# ML Pipeline

## Scope

Phase 2D uses `data/curated/paimana/project_monthly_status.parquet` as the canonical source. The generator is `backend/ml/build_dataset.py` and the feature/target implementation is `backend/ml/temporal.py`.

## Targets

- Implementation risk: supported as a one-month-ahead proxy. A row is positive when the next observed physical progress is missing or does not increase by more than 0.01 percentage points.
- Cost overrun: partially supported as a one-month-ahead observed revision proxy. A row is positive when next-period revised cost exceeds next-period original cost by more than 5%.
- Time overrun: not supported. Planned and actual completion dates are not populated.

These labels are not official government decisions and must not be presented as such.

## Features and cutoff

Features contain current fields and history-derived changes, rolling statistics, stagnation, observation count, elapsed months, and reporting gaps. Rolling values are shifted before aggregation. Future observations are used only to form labels. Feature version: `paimana-temporal-v1`.

## Evaluation

The primary split is chronological: older prediction periods for training, the penultimate period for validation, and the latest period for test. The pipeline reports dummy and simple baseline models. Entity-aware generalization and calibration remain follow-up work because the current corpus has only five observed reporting periods.

## Reproducible command

```bash
cd backend
.venv312/bin/python -m ml.build_dataset
```

The command writes CSV/Parquet datasets and JSON profiles/results under `data/training/paimana`. No production model is registered or marked ready by this phase.
