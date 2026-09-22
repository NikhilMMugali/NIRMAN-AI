from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ml.temporal import SAFE_FEATURES, FEATURE_VERSION

ROOT_DIR = Path(__file__).resolve().parents[2]
TRAINING_DATA_PATH = ROOT_DIR / "data" / "training" / "paimana" / "implementation_risk_dataset.parquet"
MODEL_DIR = ROOT_DIR / "backend" / "ml" / "saved_models"


def train_and_save_model() -> dict[str, Any]:
    if not TRAINING_DATA_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found at {TRAINING_DATA_PATH}")

    df = pd.read_parquet(TRAINING_DATA_PATH)
    
    # Fill any remaining NaNs in features
    X = df[SAFE_FEATURES].fillna(0.0)
    y = df["implementation_risk_target"].astype(int)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "implementation_risk_rf.joblib"
    joblib.dump(model, model_path)

    metadata = {
        "model_id": "implementation_risk_rf_v1",
        "model_name": "RandomForestClassifier",
        "target": "implementation_risk_target",
        "feature_version": FEATURE_VERSION,
        "features": SAFE_FEATURES,
        "n_samples": int(len(df)),
        "n_estimators": 200,
        "max_depth": 6,
        "artifact_path": str(model_path.relative_to(ROOT_DIR)),
        "status": "VALIDATED_PROTOTYPE",
    }

    metadata_path = MODEL_DIR / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model successfully saved to {model_path}")
    return metadata


if __name__ == "__main__":
    train_and_save_model()
