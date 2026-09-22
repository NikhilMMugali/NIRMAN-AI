# NIRMAN AI ML Specification

## Phase 2D boundary

The canonical PAIMANA project-month dataset is the only source for this phase. Models are exploratory baselines and are not production-ready or official government decisions.

## Supported targets

| Target | Status | Definition |
| --- | --- | --- |
| Cost overrun | PARTIALLY_SUPPORTED | Next observed revised cost > next observed original cost by 5% |
| Time overrun | NOT_SUPPORTED | Completion-date outcomes are not populated |
| Implementation risk | SUPPORTED | Next observed physical progress is missing or does not increase |
| Early warning | PARTIALLY_SUPPORTED | One-month horizon evaluable; 3/6 month horizons not evaluable |

## Cutoff and features

Each row is a prediction at `reporting_period`. Current and prior history may be features. Future rows may only create target labels. Feature version is `paimana-temporal-v1`; see `data/manifests/ML_LEAKAGE_AUDIT.md`.

## Evaluation

Use chronological train/validation/test periods. Report precision, recall, F1, and ROC-AUC where meaningful for classification; MAE and RMSE for regression. Dummy baselines are mandatory. Weak models must remain candidates and must not be marked production-ready.
