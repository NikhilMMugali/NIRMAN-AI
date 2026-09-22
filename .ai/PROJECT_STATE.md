# NIRMAN AI — PROJECT STATE

## Current Phase: Master SIH Prototype Integration — VERIFIED & LIVE
- Status: PRODUCTION PROTOTYPE READY
- Date: 2026-09-11

## Architecture & Foundation
- **Frontend**: Next.js 16 (App Router) + TypeScript + Vanilla CSS running at `http://localhost:3000`. Connected live to FastAPI backend with interactive view switcher (`Command Center`, `Risk Radar`, `Projects`, `State Intelligence`, `Sector Intelligence`, `AI Insights`). Features global search filtering, restored `NIRMAN AI ASSISTANT` chat interface (`NirmanAiChat`), and structured recommendation cards.
- **Backend**: FastAPI 0.115 server running at `http://127.0.0.1:8000` with versioned routes (`/api/v1`), explicit RequestValidationError handler (422), structured traceback logging (500), CORS allowlist, and repository/service architecture.
- **Python Environment**: Python 3.12.14 in `backend/.venv312`.
- **Extraction Engine**: Single canonical pipeline in `backend/extraction/` processing 21 PAIMANA report PDFs into 8,180 project-month rows.
- **ML Engine**: `paimana-temporal-v1` feature engineering, trained candidate RandomForest model artifact (`implementation_risk_rf.joblib`), SHAP model drivers, explicit operational status separation (`COMPLETED`, `IN_PROGRESS`, `STAGNANT`), and prototype rule engine (`PROTOTYPE_RULE_ENGINE`).
- **Database Schema**: PostgreSQL / Supabase migration ready with `pgvector` (`VECTOR(1536)`), RLS enablement, and TEXT `project_id` support. Local Parquet fallback active.

## Verified ML Performance
- **Implementation Risk** (RandomForest Candidate Model):
  - Precision: 0.791
  - Recall: 0.830
  - F1 Score: 0.810
  - ROC-AUC: 0.859
  - PR-AUC: 0.869

## Test & Build Results
- **Backend Pytest**: 31 passed out of 31 tests (0 failed, 1 warning) including `test_recommendations.py`
- **Frontend Production Build**: `npm run build` compiled successfully in 2.9s (0 errors)
- **Root Operational Guide**: Verified at `RUN_NIRMAN_AI.md`
