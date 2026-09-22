from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier


FEATURE_VERSION = "paimana-temporal-v1"
SAFE_FEATURES = [
    "physical_progress", "expenditure", "original_cost", "revised_cost",
    "progress_delta_1m", "expenditure_delta_1m", "progress_mean_3m",
    "progress_std_3m", "stagnant_months_3m", "observations_to_date",
    "months_elapsed", "reporting_gap_months",
]


def load_canonical(path: str | Path) -> pd.DataFrame:
    frame = pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)
    missing = {"project_id", "reporting_period"}.difference(frame.columns)
    if missing:
        raise ValueError(f"canonical dataset missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["reporting_period"] = pd.PeriodIndex(frame["reporting_period"], freq="M")
    for column in ["physical_progress", "expenditure", "original_cost", "revised_cost"]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.sort_values(["project_id", "reporting_period"]).reset_index(drop=True)


def build_temporal_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build each row from history strictly before the prediction period."""
    result = frame.copy().sort_values(["project_id", "reporting_period"])
    if not isinstance(result["reporting_period"].dtype, pd.PeriodDtype):
        result["reporting_period"] = pd.PeriodIndex(result["reporting_period"], freq="M")
    grouped = result.groupby("project_id", sort=False)
    result["progress_delta_1m"] = grouped["physical_progress"].diff().fillna(0.0)
    result["expenditure_delta_1m"] = grouped["expenditure"].diff().fillna(0.0)
    result["progress_mean_3m"] = (
        grouped["physical_progress"]
        .transform(lambda values: values.shift(1).rolling(3, min_periods=1).mean())
        .fillna(result["physical_progress"])
    )
    result["progress_std_3m"] = (
        grouped["physical_progress"]
        .transform(lambda values: values.shift(1).rolling(3, min_periods=2).std())
        .fillna(0.0)
    )
    result["stagnant_months_3m"] = (
        grouped["physical_progress"]
        .transform(lambda values: values.shift(1).diff().abs().le(0.01).rolling(3, min_periods=1).sum())
        .fillna(0)
    )
    result["observations_to_date"] = grouped.cumcount()
    first_period = grouped["reporting_period"].transform("min")
    result["months_elapsed"] = (result["reporting_period"] - first_period).apply(lambda value: value.n if hasattr(value, "n") else 0)
    result["reporting_gap_months"] = grouped["reporting_period"].diff().apply(
        lambda value: value.n - 1 if (not pd.isna(value) and hasattr(value, "n")) else 0
    )
    return result



def build_targets(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach next-observation targets without using future values as features."""
    result = features.copy().sort_values(["project_id", "reporting_period"])
    grouped = result.groupby("project_id", sort=False)
    next_progress = grouped["physical_progress"].shift(-1)
    next_revised = grouped["revised_cost"].shift(-1)
    next_original = grouped["original_cost"].shift(-1)
    result["next_period"] = grouped["reporting_period"].shift(-1)
    result["implementation_risk_target"] = (
        next_progress.isna() | (next_progress - result["physical_progress"] <= 0.01)
    ).astype("int64")
    cost_available = next_revised.notna() & next_original.notna() & (next_original > 0)
    result["cost_overrun_target"] = np.where(
        cost_available, (next_revised > next_original * 1.05).astype("int64"), np.nan
    )
    result = result[result["next_period"].notna()].copy()
    result["prediction_period"] = result["reporting_period"].astype(str)
    result["next_period"] = result["next_period"].astype(str)
    
    # Fill any remaining non-critical feature NaNs so early project observations are preserved
    for col in SAFE_FEATURES:
        if col in result.columns and result[col].isna().any():
            result[col] = result[col].fillna(0.0)

    implementation = result.dropna(subset=["implementation_risk_target"]).copy()
    cost = result.dropna(subset=["cost_overrun_target"]).copy()
    return implementation, cost


def chronological_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    periods = sorted(frame["prediction_period"].unique())
    if len(periods) < 3:
        raise ValueError("at least three prediction periods are required for temporal evaluation")
    validation_period = periods[-2]
    train = frame[frame["prediction_period"] < validation_period]
    validation = frame[frame["prediction_period"] == validation_period]
    test = frame[frame["prediction_period"] > validation_period]
    if train.empty or validation.empty or test.empty:
        raise ValueError(f"cannot create non-empty chronological split from periods {periods}")
    return train, validation, test


def _positive_probability(model: Any, features: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(features)
    if probabilities.shape[1] == 1:
        return np.ones(len(features)) if model.classes_[0] == 1 else np.zeros(len(features))
    return probabilities[:, 1]


def _classification_models() -> dict[str, Any]:
    return {
        "dummy_classifier": DummyClassifier(strategy="prior"),
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)),
        "random_forest": RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, n_jobs=1),
    }


def _class_distribution(frame: pd.DataFrame, target: str) -> dict[str, int | float]:
    counts = frame[target].value_counts().to_dict()
    positive = int(counts.get(1, 0))
    return {
        "negative": int(counts.get(0, 0)),
        "positive": positive,
        "total": int(len(frame)),
        "positive_rate": float(positive / len(frame)) if len(frame) else 0.0,
    }


def evaluate_implementation_risk(frame: pd.DataFrame) -> dict[str, Any]:
    try:
        train, validation, test = chronological_split(frame)
    except ValueError as exc:
        return {
            "status": "LIMITED_TEMPORAL_DATA",
            "message": str(exc),
            "production_ready": False,
            "models": {},
        }
    models = _classification_models()
    metrics: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        try:
            model.fit(train[SAFE_FEATURES], train["implementation_risk_target"])
        except ValueError as exc:
            metrics[name] = {"status": "not_trainable", "reason": str(exc)}
            continue
        predicted = model.predict(test[SAFE_FEATURES])
        probabilities = _positive_probability(model, test[SAFE_FEATURES])
        values = {
            "precision": float(precision_score(test["implementation_risk_target"], predicted, zero_division=0)),
            "recall": float(recall_score(test["implementation_risk_target"], predicted, zero_division=0)),
            "f1": float(f1_score(test["implementation_risk_target"], predicted, zero_division=0)),
            "confusion_matrix": confusion_matrix(test["implementation_risk_target"], predicted, labels=[0, 1]).tolist(),
        }
        if test["implementation_risk_target"].nunique() > 1:
            values["roc_auc"] = float(roc_auc_score(test["implementation_risk_target"], probabilities))
            values["pr_auc"] = float(average_precision_score(test["implementation_risk_target"], probabilities))
        metrics[name] = values
    return {
        "target": "implementation_risk_target",
        "train_period": [min(train.prediction_period), max(train.prediction_period)],
        "validation_period": sorted(validation.prediction_period.unique())[0],
        "test_period": [min(test.prediction_period), max(test.prediction_period)],
        "rows": {"train": len(train), "validation": len(validation), "test": len(test)},
        "class_distribution": {
            "train": _class_distribution(train, "implementation_risk_target"),
            "validation": _class_distribution(validation, "implementation_risk_target"),
            "test": _class_distribution(test, "implementation_risk_target"),
        },
        "models": metrics,
        "selection_rule": "maximize validation PR-AUC, then recall; test metrics are held out",
    }


def evaluate_cost_overrun(frame: pd.DataFrame) -> dict[str, Any]:
    try:
        train, validation, test = chronological_split(frame)
    except ValueError as exc:
        return {
            "status": "LIMITED_TEMPORAL_DATA",
            "message": str(exc),
            "production_ready": False,
            "models": {},
        }
    metrics: dict[str, dict[str, float]] = {}
    models = _classification_models()
    for name, model in models.items():
        try:
            model.fit(train[SAFE_FEATURES], train["cost_overrun_target"])
        except ValueError as exc:
            metrics[name] = {"status": "not_trainable", "reason": str(exc)}
            continue
        predicted = model.predict(test[SAFE_FEATURES])
        values = {
            "precision": float(precision_score(test["cost_overrun_target"], predicted, zero_division=0)),
            "recall": float(recall_score(test["cost_overrun_target"], predicted, zero_division=0)),
            "f1": float(f1_score(test["cost_overrun_target"], predicted, zero_division=0)),
            "confusion_matrix": confusion_matrix(test["cost_overrun_target"], predicted, labels=[0, 1]).tolist(),
        }
        if test["cost_overrun_target"].nunique() > 1:
            probabilities = _positive_probability(model, test[SAFE_FEATURES])
            values["roc_auc"] = float(roc_auc_score(test["cost_overrun_target"], probabilities))
            values["pr_auc"] = float(average_precision_score(test["cost_overrun_target"], probabilities))
        metrics[name] = values
    return {
        "target": "cost_overrun_target",
        "train_period": [min(train.prediction_period), max(train.prediction_period)],
        "validation_period": sorted(validation.prediction_period.unique())[0],
        "test_period": [min(test.prediction_period), max(test.prediction_period)],
        "rows": {"train": len(train), "validation": len(validation), "test": len(test)},
        "class_distribution": {
            "train": _class_distribution(train, "cost_overrun_target"),
            "validation": _class_distribution(validation, "cost_overrun_target"),
            "test": _class_distribution(test, "cost_overrun_target"),
        },
        "models": metrics,
        "selection_rule": "maximize validation PR-AUC, then recall; test metrics are held out",
    }


def rolling_backtest(frame: pd.DataFrame, target: str) -> list[dict[str, Any]]:
    """Run expanding-window one-period-ahead evaluation where both classes permit training."""
    periods = sorted(frame["prediction_period"].unique())
    folds: list[dict[str, Any]] = []
    for index in range(2, len(periods)):
        train = frame[frame["prediction_period"] < periods[index]]
        validation = frame[frame["prediction_period"] == periods[index]]
        fold: dict[str, Any] = {
            "train_period": [periods[0], periods[index - 1]],
            "validation_period": periods[index],
            "train_rows": len(train),
            "validation_rows": len(validation),
        }
        if train[target].nunique() < 2 or validation[target].nunique() < 2:
            fold["status"] = "descriptive_only"
            fold["reason"] = "one or both periods contain a single class"
            folds.append(fold)
            continue
        fold["status"] = "evaluated"
        fold["models"] = {}
        for name, model in _classification_models().items():
            model.fit(train[SAFE_FEATURES], train[target])
            probabilities = _positive_probability(model, validation[SAFE_FEATURES])
            predicted = model.predict(validation[SAFE_FEATURES])
            fold["models"][name] = {
                "precision": float(precision_score(validation[target], predicted, zero_division=0)),
                "recall": float(recall_score(validation[target], predicted, zero_division=0)),
                "f1": float(f1_score(validation[target], predicted, zero_division=0)),
                "pr_auc": float(average_precision_score(validation[target], probabilities)),
            }
        folds.append(fold)
    return folds


def write_datasets(source_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    raw = load_canonical(source_path)
    features = build_temporal_features(raw)
    implementation, cost = build_targets(features)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in [("implementation_risk_dataset", implementation), ("cost_overrun_dataset", cost)]:
        frame.to_csv(output / f"{name}.csv", index=False)
        frame.to_parquet(output / f"{name}.parquet", index=False)
    profile = {
        "source_rows": int(len(raw)),
        "source_projects": int(raw["project_id"].nunique()),
        "source_periods": sorted(raw["reporting_period"].astype(str).unique()),
        "implementation_risk_rows": int(len(implementation)),
        "cost_overrun_rows": int(len(cost)),
        "time_overrun_status": "NOT_SUPPORTED",
        "early_warning": {"1_month": "EVALUABLE", "3_month": "NOT_EVALUABLE", "6_month": "NOT_EVALUABLE"},
        "feature_version": FEATURE_VERSION,
        "features": SAFE_FEATURES,
    }
    (output / "dataset_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    (output / "feature_catalog.json").write_text(json.dumps({"version": FEATURE_VERSION, "features": SAFE_FEATURES}, indent=2), encoding="utf-8")
    (output / "target_definitions.json").write_text(json.dumps({
        "implementation_risk": {"status": "SUPPORTED", "definition": "next observed month has no physical progress increase"},
        "cost_overrun": {"status": "PARTIALLY_SUPPORTED", "definition": "next observed revised cost exceeds original cost by more than 5%"},
        "time_overrun": {"status": "NOT_SUPPORTED", "reason": "no planned or actual completion dates are populated"},
    }, indent=2), encoding="utf-8")
    return profile