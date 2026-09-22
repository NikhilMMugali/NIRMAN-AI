from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from app.repositories.base_repo import BaseRepository


ROOT_DIR = Path(__file__).resolve().parents[3]
CURATED_DIR = ROOT_DIR / "data" / "curated" / "paimana"


class ProjectRepository(BaseRepository):
    def __init__(self, db_client: Any = None, use_local_fallback: bool = True) -> None:
        super().__init__(db_client)
        self.use_local_fallback = use_local_fallback

    def _load_projects_df(self) -> pd.DataFrame:
        parquet_path = CURATED_DIR / "projects.parquet"
        csv_path = CURATED_DIR / "projects.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def _load_monthly_df(self) -> pd.DataFrame:
        parquet_path = CURATED_DIR / "project_monthly_status.parquet"
        csv_path = CURATED_DIR / "project_monthly_status.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def list_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        if self.db_client:
            try:
                res = self.db_client.query("SELECT * FROM projects LIMIT %s", limit)
                if res:
                    return list(res)
            except Exception:
                pass

        if not self.is_configured() and not self.use_local_fallback:
            return []

        df = self._load_projects_df()
        if df.empty:
            return []

        monthly = self._load_monthly_df()
        if not monthly.empty:
            latest = monthly.sort_values("reporting_period").groupby("project_id", as_index=False).last()
            merged = df.merge(
                latest[["project_id", "original_cost", "expenditure", "physical_progress"]],
                on="project_id",
                how="left"
            )
            df = merged

        records = df.head(limit).to_dict(orient="records")
        try:
            from app.repositories.risk_repo import RiskRepository
            risk_repo = RiskRepository()
            for rec in records:
                pid = rec.get("project_id")
                if pid:
                    risk_data = risk_repo.get_project_risk(pid)
                    if risk_data:
                        rec["risk_probability"] = risk_data.get("risk_probability", 0.05)
                        rec["risk_category"] = risk_data.get("risk_category", "LOW")
                        rec["operational_status"] = risk_data.get("operational_status", "IN_PROGRESS")
        except Exception:
            pass
        return records


    def get_by_id(self, project_id: str) -> dict[str, Any] | None:
        return self.get_by_project_id(project_id)

    def get_by_project_id(self, project_id: str) -> dict[str, Any] | None:
        df = self._load_projects_df()
        if df.empty:
            return None
        match = df[df["project_id"] == project_id]
        if match.empty:
            # Case insensitive search fallback
            match = df[df["project_id"].astype(str).str.upper() == project_id.upper()]
        if match.empty:
            return None
        record = match.iloc[0].to_dict()
        return record

    def get_project_history(self, project_id: str) -> list[dict[str, Any]]:
        df = self._load_monthly_df()
        if df.empty:
            return []
        match = df[df["project_id"] == project_id]
        if match.empty:
            match = df[df["project_id"].astype(str).str.upper() == project_id.upper()]
        if match.empty:
            return []
        history = match.sort_values("reporting_period").to_dict(orient="records")
        return history
