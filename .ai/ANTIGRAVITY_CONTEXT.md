# NIRMAN AI Antigravity Project Context

## Current Phase & Readiness Gate
- Current Phase: GitHub Release Pass & Final Verification — COMPLETE & VERIFIED
- Status: GITHUB RELEASE READY (Frontend Next.js App Router prepared; Backend deployment boundary documented; Supabase cloud dataset seeded & verified)

## Architecture Overview
- Frontend: Next.js 16 (App Router) + TypeScript + Vanilla CSS (`nirman-ai-app/`). API requests centralized in `lib/api/client.ts` with environment variable `NEXT_PUBLIC_API_BASE_URL`.
- Views: Command Center, Risk Radar, Projects, State Intelligence, Sector Intelligence, AI Insights.
- UI Controls: 18 audited interactive controls (table row click, search bar, status filter chips, inspect buttons, quick chips, notification popover, refresh data button, sidebar tabs).
- Backend: FastAPI 0.115 with versioned routes (`/api/v1`), environment-driven CORS configuration (`CORS_ORIGINS`), Groq LLM API integration (`GROQ_API_KEY` configured in gitignored `.env`), location-agnostic relative path resolution (`Path(__file__).resolve().parents[3]`).
- Python Environment: Python 3.12.14 in `backend/.venv312`.
- Canonical Data & ML: 21 PAIMANA PDFs, 8,180 project-month observations across 1,723 unique projects. RandomForestClassifier artifact (`implementation_risk_rf.joblib`), SHAP model drivers, Groq LLM API (`openai/gpt-oss-120b`), and deterministic recommendation engine (`PROTOTYPE_RULE_ENGINE`).
- Supabase Integration: Cloud Supabase database verified with 1,723 projects and 8,180 project-month records (0 duplicates).

## Data & Extraction Status
- Source PDFs: 21 verified PAIMANA PDF reports
- Total Observations: 8,180 canonical project-month rows
- Unique Projects: 1,723 projects
- Reporting Periods: 2025-02 to 2025-06
- Model Artifact: `backend/ml/saved_models/implementation_risk_rf.joblib`
- LLM Provider: Groq (`openai/gpt-oss-120b`) active via `GROQ_API_KEY` in gitignored `.env` files.

## Test & Build Results
- Backend Pytest: 31 passed (0 failed).
- Frontend Build: `npm run build` compiled successfully in 2.1s (0 TypeScript/ESLint errors).
- Groq API Integration: Verified live completion (`HTTP 200`) using `openai/gpt-oss-120b` model.
- Localhost Demo: Verified with real projects `N04000077` (CCS Lucknow Airport), `N04000073` (VSI Port Blair Terminal), `N24000948` (Hunli-Anini Road).

## Deployment Preparation
- **Vercel Frontend**: Ready for deployment via standard Next.js build. Environment variable `NEXT_PUBLIC_API_BASE_URL` configures target API.
- **Backend Architecture Boundary**: FastAPI backend prepared for separate containerized/Python hosting (Render/Cloud Run) with `CORS_ORIGINS` setup.
- **Deployment Status**: NOT DEPLOYED (Local demo operational; cloud deployment prepared).

## Operational Run Guide
- Root Guide: [RUN_NIRMAN_AI.md](file:///Users/nikhil/Desktop/SIH/NIRMAN%20AI/RUN_NIRMAN_AI.md)
