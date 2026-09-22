from __future__ import annotations

import logging
from functools import cached_property
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SupabaseRepository:
    """
    Backend repository for Supabase operations.
    Uses the service-role key for unrestricted server-side access.
    Falls back gracefully when Supabase is not configured.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.supabase_url
            and self.settings.supabase_service_role_key
        )

    @cached_property
    def client(self) -> Any:
        """
        Lazily create and cache the Supabase client.
        Uses the service-role key so the backend can bypass RLS for reads/writes.
        Returns None if credentials are missing.
        """
        if not self.is_configured:
            logger.warning("Supabase credentials not configured — client not created.")
            return None

        try:
            from supabase import create_client, Client  # type: ignore[import]
            sb: Client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key,
            )
            logger.info("Supabase client initialised for %s", self.settings.supabase_url)
            return sb
        except Exception as exc:
            logger.error("Failed to create Supabase client: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Health / connectivity
    # ------------------------------------------------------------------

    def get_connection_status(self) -> dict[str, Any]:
        """
        Lightweight connectivity check: tries to fetch 1 row from `projects`.
        Returns a status dict compatible with the existing health endpoint.
        """
        if not self.is_configured:
            return {
                "configured": False,
                "service": "supabase",
                "status": "not-configured",
            }

        if self.client is None:
            return {
                "configured": True,
                "service": "supabase",
                "status": "client-init-failed",
            }

        try:
            resp = self.client.table("projects").select("id").limit(1).execute()
            # supabase-py v2 raises on error; reaching here means success
            return {
                "configured": True,
                "service": "supabase",
                "status": "connected",
                "url": self.settings.supabase_url,
                "tables_reachable": True,
            }
        except Exception as exc:
            return {
                "configured": True,
                "service": "supabase",
                "status": "error",
                "error": str(exc),
                "url": self.settings.supabase_url,
                "tables_reachable": False,
            }

    # ------------------------------------------------------------------
    # Data access helpers (used by other repos when Supabase is primary)
    # ------------------------------------------------------------------

    def fetch_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return up to `limit` rows from the `projects` table."""
        if self.client is None:
            return []
        try:
            resp = (
                self.client.table("projects")
                .select("*")
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.error("Supabase fetch_projects failed: %s", exc)
            return []

    def fetch_project_by_id(self, project_id: str) -> dict[str, Any] | None:
        """Return a single project row by its text `project_id` column."""
        if self.client is None:
            return None
        try:
            resp = (
                self.client.table("projects")
                .select("*")
                .eq("project_id", project_id)
                .limit(1)
                .execute()
            )
            data = resp.data or []
            return data[0] if data else None
        except Exception as exc:
            logger.error("Supabase fetch_project_by_id failed: %s", exc)
            return None

    def fetch_monthly_status(self, project_uuid: str) -> list[dict[str, Any]]:
        """Return all monthly-status rows for a given project UUID (the `id` PK)."""
        if self.client is None:
            return []
        try:
            resp = (
                self.client.table("project_monthly_status")
                .select("*")
                .eq("project_id", project_uuid)
                .order("reporting_month")
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.error("Supabase fetch_monthly_status failed: %s", exc)
            return []

    def upsert_project(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """
        Insert or update a project row. Conflicts on `project_id` are merged.
        Returns the upserted row or None on failure.
        """
        if self.client is None:
            return None
        try:
            resp = (
                self.client.table("projects")
                .upsert(record, on_conflict="project_id")
                .execute()
            )
            data = resp.data or []
            return data[0] if data else None
        except Exception as exc:
            logger.error("Supabase upsert_project failed: %s", exc)
            return None

    def upsert_monthly_status(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """
        Insert or update a project_monthly_status row.
        Conflict key is (project_id, reporting_month).
        """
        if self.client is None:
            return None
        try:
            resp = (
                self.client.table("project_monthly_status")
                .upsert(record, on_conflict="project_id,reporting_month")
                .execute()
            )
            data = resp.data or []
            return data[0] if data else None
        except Exception as exc:
            logger.error("Supabase upsert_monthly_status failed: %s", exc)
            return None
