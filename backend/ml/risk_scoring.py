from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskThresholds:
    moderate: float = 0.25
    high: float = 0.50
    critical: float = 0.75

    def __post_init__(self) -> None:
        values = (self.moderate, self.high, self.critical)
        if any(value < 0 or value > 1 for value in values) or not (self.moderate < self.high < self.critical):
            raise ValueError("risk thresholds must be ordered values between 0 and 1")


def risk_category(probability: float, thresholds: RiskThresholds = RiskThresholds()) -> str:
    if not 0 <= probability <= 1:
        raise ValueError("risk probability must be between 0 and 1")
    if probability >= thresholds.critical:
        return "CRITICAL"
    if probability >= thresholds.high:
        return "HIGH"
    if probability >= thresholds.moderate:
        return "MODERATE"
    return "LOW"


def build_risk_output(
    project_id: str,
    probability: float,
    prediction_date: str,
    data_cutoff: str,
    model_version: str,
    feature_version: str,
    calibrated: bool = False,
    thresholds: RiskThresholds = RiskThresholds(),
) -> dict[str, object]:
    return {
        "project_id": project_id,
        "prediction_date": prediction_date,
        "data_cutoff": data_cutoff,
        "risk_probability": probability,
        "risk_category": risk_category(probability, thresholds),
        "model_version": model_version,
        "feature_version": feature_version,
        "calibration_status": "CALIBRATED" if calibrated else "UNCALIBRATED",
        "disclaimer": "Model-generated estimate; not an official government decision.",
    }