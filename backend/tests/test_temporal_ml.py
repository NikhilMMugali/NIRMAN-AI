import pandas as pd

from ml.temporal import SAFE_FEATURES, build_targets, build_temporal_features, chronological_split
from ml.risk_scoring import RiskThresholds, build_risk_output, risk_category


def _history() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {"project_id": "P1", "reporting_period": "2025-01", "physical_progress": 10.0, "expenditure": 5.0, "original_cost": 100.0, "revised_cost": 100.0},
            {"project_id": "P1", "reporting_period": "2025-02", "physical_progress": 20.0, "expenditure": 8.0, "original_cost": 100.0, "revised_cost": 110.0},
            {"project_id": "P1", "reporting_period": "2025-03", "physical_progress": 20.0, "expenditure": 9.0, "original_cost": 100.0, "revised_cost": 120.0},
            {"project_id": "P1", "reporting_period": "2025-04", "physical_progress": 35.0, "expenditure": 12.0, "original_cost": 100.0, "revised_cost": 120.0},
            {"project_id": "P1", "reporting_period": "2025-05", "physical_progress": 40.0, "expenditure": 15.0, "original_cost": 100.0, "revised_cost": 120.0},
            {"project_id": "P1", "reporting_period": "2025-06", "physical_progress": 50.0, "expenditure": 18.0, "original_cost": 100.0, "revised_cost": 120.0},
            {"project_id": "P1", "reporting_period": "2025-07", "physical_progress": 60.0, "expenditure": 20.0, "original_cost": 100.0, "revised_cost": 120.0},
        ]
    )
    df["reporting_period"] = pd.PeriodIndex(df["reporting_period"], freq="M")
    return df


def test_feature_history_excludes_current_row_from_rolling_mean() -> None:
    features = build_temporal_features(_history())

    march = features.loc[features["reporting_period"] == pd.Period("2025-03", freq="M")].iloc[0]
    assert march["progress_mean_3m"] == 15.0
    assert march["progress_delta_1m"] == 0.0


def test_future_observation_is_target_only() -> None:
    features = build_temporal_features(_history())
    implementation, cost = build_targets(features)
    march = implementation.loc[implementation["prediction_period"] == "2025-03"].iloc[0]

    assert march["next_period"] == "2025-04"
    assert march["implementation_risk_target"] == 0
    assert "next_period" not in SAFE_FEATURES
    assert march["revised_cost"] == 120.0


def test_future_mutation_does_not_change_earlier_features() -> None:
    original = build_temporal_features(_history())
    changed_history = _history().copy()
    changed_history.loc[changed_history["reporting_period"] == pd.Period("2025-04", freq="M"), "physical_progress"] = 99.0
    changed = build_temporal_features(changed_history)

    original_march = original.loc[original["reporting_period"] == pd.Period("2025-03", freq="M"), SAFE_FEATURES].iloc[0]
    changed_march = changed.loc[changed["reporting_period"] == pd.Period("2025-03", freq="M"), SAFE_FEATURES].iloc[0]
    pd.testing.assert_series_equal(original_march, changed_march, check_names=False)


def test_chronological_split_keeps_period_order() -> None:
    features = build_temporal_features(_history())
    implementation, _ = build_targets(features)
    train, validation, test = chronological_split(implementation)

    assert max(train["prediction_period"]) < min(validation["prediction_period"])
    assert max(validation["prediction_period"]) < min(test["prediction_period"])


def test_risk_output_has_government_safe_metadata() -> None:
    output = build_risk_output("P1", 0.80, "2025-06-01", "2025-05", "model-v1", "features-v1")

    assert output["risk_category"] == "CRITICAL"
    assert output["calibration_status"] == "UNCALIBRATED"
    assert "not an official government decision" in output["disclaimer"]


def test_risk_thresholds_are_ordered_and_probabilities_bounded() -> None:
    thresholds = RiskThresholds(moderate=0.3, high=0.6, critical=0.9)

    assert risk_category(0.6, thresholds) == "HIGH"
    try:
        risk_category(1.1, thresholds)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range risk probabilities must be rejected")