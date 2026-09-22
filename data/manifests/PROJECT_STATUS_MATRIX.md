# NIRMAN AI Project Status Matrix

| Component | Implemented | Executed | Verified | Partial | Blocked | Notes |
|---|:---:|:---:|:---:|:---:|:---:|---|
| PAIMANA corpus | Yes | Yes | Yes | No | No | 21 PDFs in `data/raw/paimana/zip/` intact |
| Extraction | Yes | Yes | Yes | No | No | ZIP, field alias, cost, expenditure, table header, & zero-val bugs fixed |
| Canonical dataset | Yes | Yes | Yes | No | No | 8,180 rows, 1,723 projects, 2025-02 to 2025-06 |
| ML features | Yes | Yes | Yes | No | No | `paimana-temporal-v1` with zero data leakage & initial NaN imputation |
| ML target | Yes | Yes | Yes | No | No | Implementation risk (supported) & cost overrun (partial) |
| Baseline models | Yes | Yes | Yes | No | No | Dummy, Logistic Regression, Random Forest evaluated |
| SHAP | Yes | Yes | Yes | No | No | Feature contribution ranker implemented |
| Risk scoring | Yes | Yes | Yes | No | No | `LOW`, `MODERATE`, `HIGH`, `CRITICAL` categories configured |
| Risk API | Yes | Yes | Yes | No | No | `/api/v1/projects`, `/risk`, `/drivers` live endpoints |
| Frontend risk | Yes | Yes | Yes | No | No | Next.js Command Center connected to API & project selection |
| Supabase | Yes | No | Yes | Yes | No | Schema ready with pgvector, RLS, & TEXT project ID mapping |
| PDF upload | No | No | No | No | No | Scheduled for future phase |
| RAG | No | No | No | No | No | Scheduled for future phase |
| Recommendations | No | No | No | No | No | Scheduled for future phase |
| Reports | No | No | No | No | No | Scheduled for future phase |
