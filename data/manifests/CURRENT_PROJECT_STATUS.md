# Current Project Status — NIRMAN AI

## Phase Readiness Gate: VERIFIED & RECONCILED

### Environment & Tools
- OS: macOS (Darwin arm64/x86_64)
- Python Environment: Python 3.12.14 (`backend/.venv312`)
- Node / npm: Node v24.13.0 / npm 11.6.2
- Test Suite: 21 passed (0 failed, 1 warning)
- Next.js Build: `npm run build` compiled successfully in 4.9s

### Audit & Defect Reconciliation

| Category | Finding | Status | Verification |
|---|---|---|---|
| Extraction | ZIP input handled safely | FIXED | Safe extraction to tempdir before passing PDFs |
| Extraction | `_extract_field()` returns values | FIXED | Parsed value string returned instead of alias label |
| Extraction | Original vs Revised cost separation | FIXED | Multi-cost values parsed independently |
| Extraction | Expenditure currency parsing | FIXED | Monetary amounts parsed as ₹ Cr instead of percentage |
| Extraction | PDF table header matching | FIXED | Flexible header matching across all 21 PDFs |
| Extraction | Reporting period fallback | FIXED | Missing periods set to `None` without corrupting history |
| Extraction | Validator zero-progress handling | FIXED | Valid `0.0` progress preserved |
| Extraction | PDFReader file check order | FIXED | `file_path.exists()` checked before hashing |
| Extraction | Competing extraction trees | FIXED | Single canonical pipeline in `backend/extraction/` |
| ML | Early observation droppage | FIXED | Month 1 & 2 rolling feature NaNs imputed |
| ML | Temporal split robustness | FIXED | Structured `LIMITED_TEMPORAL_DATA` fallback |
| ML | Dataset path resolution | FIXED | Dynamic resolution relative to `ROOT_DIR` |
| Backend | Validation error 422 handler | FIXED | Explicit `RequestValidationError` handler registered |
| Backend | Generic 500 traceback logging | FIXED | Server-side `logger.exception()` added |
| Backend | Missing dependencies | FIXED | Added `pydantic-settings`, `httpx`, `supabase`, `xgboost`, `shap` |
| Backend | CORS security | FIXED | Configured CORS allowlist without wildcard credentials |
| Backend | Repository & service wiring | FIXED | `ProjectRepository` and `RiskRepository` connected |
| Database | pgvector extension in migration | FIXED | Added `CREATE EXTENSION IF NOT EXISTS vector;` |
| Database | Project ID TEXT schema mapping | FIXED | Supported PAIMANA TEXT IDs (e.g. `N04000073`) |
| Database | Row Level Security (RLS) | FIXED | Added RLS enablement and read policies |
| Frontend | API client method expansion | FIXED | Added `getProjects`, `getProjectRisk`, `getProjectDrivers` |
| Frontend | Sidebar navigation | FIXED | Interactive navigation handlers added |
| Frontend | Risk detail selection | FIXED | Click project row to view live risk & SHAP drivers |

### Reconciled Metrics & Performance

- **PAIMANA Corpus**: 21 PDF reports, 8,180 canonical project-month rows, 1,723 unique projects.
- **Implementation Risk Target (Random Forest)**:
  - Precision: 0.791
  - Recall: 0.830
  - F1 Score: 0.810
  - ROC-AUC: 0.859
  - PR-AUC: 0.869
- **Cost Overrun Target (Random Forest)**:
  - Precision: 0.864
  - Recall: 0.240
  - F1 Score: 0.375
  - ROC-AUC: 0.889
  - PR-AUC: 0.708

### End-to-End Prototype Flow
Verified real vertical slice:
`PAIMANA 21 PDFs → Canonical Parquet Dataset → Temporal Features → Random Forest ML Model → FastAPI Risk Endpoints → Next.js Project Detail View`.
Tested project: `N04000073` (HUNLI-ANINI ROAD) & `N24000948` (Delhi-Mumbai Expressway).
