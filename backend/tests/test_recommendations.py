from __future__ import annotations

import pytest
from app.services.recommendation_service import PrototypeRecommendationEngine


@pytest.fixture
def engine() -> PrototypeRecommendationEngine:
    return PrototypeRecommendationEngine()


def test_completed_project_with_cost_overrun(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "LOW",
        "risk_probability": 0.05,
        "operational_status": "COMPLETED",
        "metrics": {
            "physical_progress_pct": 100.0,
            "cost_overrun_pct": 12.5,
            "stagnant_months_3m": 0,
            "reporting_gap_months": 0,
        },
    }
    res = engine.generate_recommendations("TEST-001", risk_data)
    assert res["operational_status"] == "COMPLETED"
    recs = res["recommendations"]
    assert len(recs) == 1
    assert recs[0]["category"] == "POST_COMPLETION_AUDIT"
    assert recs[0]["priority"] == "HIGH"


def test_completed_project_on_budget(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "LOW",
        "risk_probability": 0.05,
        "operational_status": "COMPLETED",
        "metrics": {
            "physical_progress_pct": 100.0,
            "cost_overrun_pct": 0.0,
            "stagnant_months_3m": 0,
            "reporting_gap_months": 0,
        },
    }
    res = engine.generate_recommendations("TEST-002", risk_data)
    assert res["operational_status"] == "COMPLETED"
    recs = res["recommendations"]
    assert len(recs) == 1
    assert recs[0]["category"] == "ROUTINE_CLOSURE"
    assert recs[0]["priority"] == "LOW"


def test_active_project_milestone_recovery(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "HIGH",
        "risk_probability": 0.65,
        "operational_status": "STAGNANT",
        "metrics": {
            "physical_progress_pct": 45.0,
            "cost_overrun_pct": 0.0,
            "stagnant_months_3m": 3,
            "reporting_gap_months": 0,
        },
    }
    res = engine.generate_recommendations("TEST-003", risk_data)
    categories = [r["category"] for r in res["recommendations"]]
    assert "MILESTONE_RECOVERY" in categories


def test_active_project_financial_audit(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "HIGH",
        "risk_probability": 0.55,
        "operational_status": "IN_PROGRESS",
        "metrics": {
            "physical_progress_pct": 70.0,
            "cost_overrun_pct": 15.0,
            "stagnant_months_3m": 0,
            "reporting_gap_months": 0,
        },
    }
    res = engine.generate_recommendations("TEST-004", risk_data)
    categories = [r["category"] for r in res["recommendations"]]
    assert "FINANCIAL_AUDIT" in categories


def test_active_project_reporting_compliance(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "LOW",
        "risk_probability": 0.15,
        "operational_status": "IN_PROGRESS",
        "metrics": {
            "physical_progress_pct": 80.0,
            "cost_overrun_pct": 0.0,
            "stagnant_months_3m": 0,
            "reporting_gap_months": 2,
        },
    }
    res = engine.generate_recommendations("TEST-005", risk_data)
    categories = [r["category"] for r in res["recommendations"]]
    assert "REPORTING_COMPLIANCE" in categories


def test_active_project_routine_monitoring(engine: PrototypeRecommendationEngine) -> None:
    risk_data = {
        "risk_category": "LOW",
        "risk_probability": 0.10,
        "operational_status": "IN_PROGRESS",
        "metrics": {
            "physical_progress_pct": 85.0,
            "cost_overrun_pct": 0.0,
            "stagnant_months_3m": 0,
            "reporting_gap_months": 0,
        },
    }
    res = engine.generate_recommendations("TEST-006", risk_data)
    recs = res["recommendations"]
    assert len(recs) == 1
    assert recs[0]["category"] == "ROUTINE_MONITORING"
    assert recs[0]["priority"] == "LOW"
