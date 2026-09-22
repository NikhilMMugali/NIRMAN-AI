from __future__ import annotations

from typing import Any

from app.repositories.base_repo import BaseRepository


class ProjectStatusRepository(BaseRepository):
    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        if not self.is_configured():
            return []
        return []

    def unique_project_month_key(self, project_id: str, reporting_month: str) -> str:
        return f"{project_id}|{reporting_month}"
