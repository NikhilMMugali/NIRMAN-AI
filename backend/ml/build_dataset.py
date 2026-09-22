from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ml.temporal import (
    build_targets,
    build_temporal_features,
    evaluate_cost_overrun,
    evaluate_implementation_risk,
    load_canonical,
    rolling_backtest,
    write_datasets,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT_DIR / "data" / "curated" / "paimana" / "project_monthly_status.parquet"
DEFAULT_OUTPUT = ROOT_DIR / "data" / "training" / "paimana"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build leakage-safe PAIMANA temporal datasets")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    profile = write_datasets(args.source, args.output)
    frame = load_canonical(args.source)
    implementation, cost = build_targets(build_temporal_features(frame))
    implementation_results = evaluate_implementation_risk(implementation)
    cost_results = evaluate_cost_overrun(cost)
    results = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "status": "CANDIDATE",
        "feature_version": profile["feature_version"],
        "profile": profile,
        "implementation_risk": implementation_results,
        "cost_overrun": cost_results,
        "calibration": {
            "status": "NOT_RELIABLE",
            "reason": "The current corpus has only five usable report periods; calibration would overfit the small validation window.",
        },
        "temporal_backtest": {
            "implementation_risk": rolling_backtest(implementation, "implementation_risk_target"),
            "cost_overrun": rolling_backtest(cost, "cost_overrun_target"),
        },
    }
    output = Path(args.output)
    experiments = output / "experiments"
    experiments.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(results, indent=2)
    output.joinpath("baseline_results.json").write_text(encoded, encoding="utf-8")
    experiments.joinpath("baseline_results.json").write_text(encoded, encoding="utf-8")
    experiments.joinpath("temporal_backtest_results.json").write_text(json.dumps(results["temporal_backtest"], indent=2), encoding="utf-8")
    experiments.joinpath("calibration_results.json").write_text(json.dumps(results["calibration"], indent=2), encoding="utf-8")
    rows = []
    for target_name in ("implementation_risk", "cost_overrun"):
        for model_name, metrics in results[target_name]["models"].items():
            rows.append({"target": target_name, "model": model_name, **metrics})
    import pandas as pd
    pd.DataFrame(rows).to_csv(experiments / "model_comparison.csv", index=False)
    registry = []
    for target_name in ("implementation_risk", "cost_overrun"):
        for model_name in results[target_name]["models"]:
            registry.append({
                "model_name": model_name,
                "target": target_name,
                "model_version": "phase-2e-baseline-v1",
                "feature_version": profile["feature_version"],
                "status": "EXPERIMENTAL",
                "seed": 42,
                "calibration_status": results["calibration"]["status"],
                "training_period": results[target_name]["train_period"],
                "validation_period": results[target_name]["validation_period"],
                "test_period": results[target_name]["test_period"],
                "metrics": results[target_name]["models"][model_name],
            })
    experiments.joinpath("model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
