from __future__ import annotations

from typing import Any
from app.repositories.projects_repo import ProjectRepository
from app.repositories.risk_repo import RiskRepository
from app.services.recommendation_service import recommendation_engine


class ProjectAssessmentService:
    """Unified service combining project metadata, monthly status, ML risk probability, SHAP drivers, and rule engine recommendations."""

    def __init__(
        self,
        projects_repo: ProjectRepository | None = None,
        risk_repo: RiskRepository | None = None,
    ) -> None:
        self.projects_repo = projects_repo or ProjectRepository()
        self.risk_repo = risk_repo or RiskRepository()

    def get_full_assessment(self, project_id: str) -> dict[str, Any] | None:
        project = self.projects_repo.get_by_project_id(project_id)
        if not project:
            return None

        history = self.projects_repo.get_project_history(project_id)
        risk = self.risk_repo.get_project_risk(project_id)
        drivers = self.risk_repo.get_project_drivers(project_id)

        if risk:
            recommendations = recommendation_engine.generate_recommendations(project_id, risk)
        else:
            recommendations = {
                "project_id": project_id,
                "engine": "PROTOTYPE_RULE_ENGINE",
                "risk_category": "LOW",
                "recommendations": [],
            }

        return {
            "project_id": project_id,
            "project_name": project.get("project_name") or project_id,
            "ministry": project.get("ministry") or "Ministry of Road Transport and Highways",
            "state": project.get("state") or "India",
            "sector": project.get("sector") or "Infrastructure",
            "operational_status": risk.get("operational_status", "IN_PROGRESS") if risk else "IN_PROGRESS",
            "financials": {
                "original_cost_cr": float(project.get("original_cost") or 0.0),
                "revised_cost_cr": float(project.get("revised_cost") or project.get("original_cost") or 0.0),
                "expenditure_cr": float(project.get("expenditure") or 0.0),
            },
            "status_history_count": len(history),
            "latest_status": history[-1] if history else {},
            "risk_assessment": risk or {},
            "model_drivers": drivers,
            "decision_interventions": recommendations.get("recommendations", []),
        }


assessment_service = ProjectAssessmentService()
