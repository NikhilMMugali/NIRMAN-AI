from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd

from app.repositories.base_repo import BaseRepository
from ml.risk_scoring import build_risk_output
from ml.temporal import SAFE_FEATURES, build_temporal_features

ROOT_DIR = Path(__file__).resolve().parents[3]
CURATED_DIR = ROOT_DIR / "data" / "curated" / "paimana"
MODEL_DIR = ROOT_DIR / "backend" / "ml" / "saved_models"
MODEL_PATH = MODEL_DIR / "implementation_risk_rf.joblib"


class RiskRepository(BaseRepository):

    def __init__(self, db_client: Any = None) -> None:
        super().__init__(db_client)
        self.model: Any = None
        self._load_model()

    def _load_model(self) -> None:
        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Warning: Could not load model from {MODEL_PATH}: {e}")
                self.model = None

    def _load_monthly_df(self) -> pd.DataFrame:
        parquet_path = CURATED_DIR / "project_monthly_status.parquet"
        csv_path = CURATED_DIR / "project_monthly_status.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    def get_project_risk(self, project_id: str) -> dict[str, Any] | None:
        df = self._load_monthly_df()
        if df.empty:
            return None

        match = df[df["project_id"] == project_id]
        if match.empty:
            match = df[df["project_id"].astype(str).str.upper() == project_id.upper()]
        if match.empty:
            return None

        # Build safe temporal features across history
        features_df = build_temporal_features(match)
        latest_features = features_df.iloc[-1]

        records = match.sort_values("reporting_period").to_dict(orient="records")
        latest = records[-1]

        progress = float(latest.get("physical_progress") or 0.0)
        orig_cost = float(latest.get("original_cost") or 1.0)
        rev_cost = float(latest.get("revised_cost") or orig_cost)
        cost_overrun_pct = ((rev_cost - orig_cost) / orig_cost * 100.0) if orig_cost > 0 else 0.0

        stagnant_months = float(latest_features.get("stagnant_months_3m", 0))
        gap_months = float(latest_features.get("reporting_gap_months", 0))

        if progress >= 100.0:
            operational_status = "COMPLETED"
            prob = 0.05  # Completed projects have zero active physical delay risk
        elif stagnant_months >= 2:
            operational_status = "STAGNANT"
        else:
            operational_status = "IN_PROGRESS"

        if self.model is not None and progress < 100.0:
            # Real model inference
            raw_features = latest_features[SAFE_FEATURES].to_dict()
            clean_features = {k: (float(v) if pd.notna(v) else 0.0) for k, v in raw_features.items()}
            feature_vector = pd.DataFrame([clean_features])
            probas = self.model.predict_proba(feature_vector)
            prob = float(probas[0][1]) if probas.shape[1] > 1 else float(probas[0][0])
            model_ver = "implementation_risk_rf_v1"
        elif self.model is None and progress < 100.0:
            # Fallback score if model is uninitialized
            risk_score = 0.2
            if progress < 30.0:
                risk_score += 0.35
            elif progress < 60.0:
                risk_score += 0.20
            if cost_overrun_pct > 20.0:
                risk_score += 0.35
            prob = min(0.99, max(0.05, round(risk_score, 2)))
            model_ver = "heuristic_fallback_v1"
        else:
            model_ver = "implementation_risk_rf_v1" if self.model is not None else "heuristic_fallback_v1"

        period = str(latest.get("reporting_period") or "2025-06")

        output = build_risk_output(
            project_id=project_id,
            probability=round(prob, 4),
            prediction_date=f"{period}-01",
            data_cutoff=f"{period}-01",
            model_version=model_ver,
            feature_version="paimana-temporal-v1",
        )
        output["operational_status"] = operational_status
        output["metrics"] = {
            "physical_progress_pct": progress,
            "original_cost_cr": orig_cost,
            "revised_cost_cr": rev_cost,
            "cost_overrun_pct": round(cost_overrun_pct, 2),
            "observations_count": len(records),
            "stagnant_months_3m": stagnant_months,
            "reporting_gap_months": gap_months,
            "operational_status": operational_status,
        }
        return output

    def get_project_drivers(self, project_id: str) -> list[dict[str, Any]]:
        risk = self.get_project_risk(project_id)
        if not risk:
            return []

        metrics = risk.get("metrics", {})
        progress = metrics.get("physical_progress_pct", 0.0)
        overrun = metrics.get("cost_overrun_pct", 0.0)
        stagnant = metrics.get("stagnant_months_3m", 0.0)
        gap = metrics.get("reporting_gap_months", 0.0)

        drivers = []
        rank = 1

        if self.model is not None and hasattr(self.model, "feature_importances_"):
            importances = dict(zip(SAFE_FEATURES, self.model.feature_importances_))
        else:
            importances = {}

        if (stagnant > 0 or progress < 70.0) and progress < 100.0:
            weight = importances.get("stagnant_months_3m", 0.25)
            drivers.append({
                "feature_name": "stagnant_months_3m",
                "feature_value": f"{int(stagnant)} stagnant months",
                "contribution": round(min(0.45, max(0.1, weight * (stagnant + 1))), 4),
                "rank": rank,
                "explanation_type": "model driver",
                "description": f"Physical progress stagnant for {int(stagnant)} of past 3 periods (current progress: {progress}%).",
            })
            rank += 1

        if overrun > 5.0:
            weight = importances.get("revised_cost", 0.20)
            drivers.append({
                "feature_name": "revised_cost_overrun",
                "feature_value": f"+{overrun}% overrun",
                "contribution": round(min(0.40, max(0.1, weight + (overrun / 100.0))), 4),
                "rank": rank,
                "explanation_type": "model driver",
                "description": f"Revised cost exceeds original budget by {overrun}%.",
            })
            rank += 1

        if gap > 0:
            weight = importances.get("reporting_gap_months", 0.15)
            drivers.append({
                "feature_name": "reporting_gap_months",
                "feature_value": f"{int(gap)} month gap",
                "contribution": round(min(0.30, max(0.1, weight * gap)), 4),
                "rank": rank,
                "explanation_type": "model driver",
                "description": f"Reporting delay of {int(gap)} month(s) detected in source submissions.",
            })
            rank += 1

        if not drivers:
            drivers.append({
                "feature_name": "physical_progress",
                "feature_value": f"{progress}%",
                "contribution": 0.10,
                "rank": 1,
                "explanation_type": "model driver",
                "description": f"Physical progress tracking at {progress}%.",
            })

        return drivers

