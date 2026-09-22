from __future__ import annotations

from app.services.assessment_service import ProjectAssessmentService


def test_assessment_service_returns_full_payload_for_real_project() -> None:
    service = ProjectAssessmentService()
    payload = service.get_full_assessment("N04000073")
    assert payload is not None
    assert payload["project_id"] == "N04000073"
    assert "financials" in payload
    assert "risk_assessment" in payload
    assert "model_drivers" in payload
    assert "decision_interventions" in payload
    assert isinstance(payload["decision_interventions"], list)
