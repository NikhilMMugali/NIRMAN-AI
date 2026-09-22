from __future__ import annotations

from app.repositories.risk_repo import RiskRepository
from app.services.recommendation_service import PrototypeRecommendationEngine


def test_risk_repository_loads_model_and_predicts_risk() -> None:
    repo = RiskRepository()
    # Test on a real PAIMANA project ID
    risk = repo.get_project_risk("N04000073")
    assert risk is not None
    assert "risk_probability" in risk
    assert 0.0 <= float(risk["risk_probability"]) <= 1.0
    assert risk["risk_category"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert risk["feature_version"] == "paimana-temporal-v1"


def test_risk_repository_returns_drivers() -> None:
    repo = RiskRepository()
    drivers = repo.get_project_drivers("N04000073")
    assert isinstance(drivers, list)
    if len(drivers) > 0:
        assert "feature_name" in drivers[0]
        assert "contribution" in drivers[0]


def test_recommendation_engine_generates_rules() -> None:
    engine = PrototypeRecommendationEngine()
    fake_risk_data = {
        "risk_category": "HIGH",
        "risk_probability": 0.78,
        "metrics": {
            "physical_progress_pct": 35.0,
            "cost_overrun_pct": 18.5,
            "stagnant_months_3m": 2.0,
            "reporting_gap_months": 1.0,
        },
    }

    result = engine.generate_recommendations("N24000948", fake_risk_data)
    assert result["engine"] == "PROTOTYPE_RULE_ENGINE"
    assert result["risk_category"] == "HIGH"
    assert len(result["recommendations"]) >= 2
    categories = [r["category"] for r in result["recommendations"]]
    assert "MILESTONE_RECOVERY" in categories
    assert "FINANCIAL_AUDIT" in categories
