# PAIMANA Data Pipeline

The source archive is preserved at `data/raw/archive/zip.rar`; extracted PDFs are under `data/raw/paimana/zip`. The canonical builder is `backend/extraction/corpus_builder.py`.

The builder emits project-month observations and project summaries as CSV and Parquet, extraction quality records, a dataset profile, and duplicate project-period rows for review. Newly generated source paths are repository-relative and each source document carries a SHA-256 hash and page number.

Canonical deduplication is deterministic by `project_id` and `reporting_period`, retaining the last sorted source row. This is a practical canonical view only; duplicate rows are preserved in `project_monthly_status_duplicates.csv` for review and should be resolved at ingestion time before production database loading.

Run from the project Python 3.12 environment:

```bash
cd backend
.venv312/bin/python -m extraction.corpus_builder
```

The ML layer consumes the resulting canonical Parquet file and writes temporal training artifacts under `data/training/paimana`.
