# NIRMAN AI — Local Development & Demo Run Guide

Official operational run guide for running the NIRMAN AI platform locally on macOS / Linux.

---

## FASTEST WAY TO RUN THE DEMO (ALREADY BUILT & VERIFIED)

If dependencies and model artifacts are already present, run the demo immediately using two terminal windows:

### TERMINAL 1 — BACKEND
```bash
cd backend
.venv312/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### TERMINAL 2 — FRONTEND
```bash
cd nirman-ai-app
npm run dev
```

Keep both terminals running.

Then open:
- 🚀 **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- ⚙️ **Backend API**: [http://localhost:8000](http://localhost:8000)
- 📚 **Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 1. Prerequisites

- **Python**: `Python 3.12.14` (located in `backend/.venv312`)
- **Node.js**: `Node.js v24.13.0`
- **npm**: `npm 11.6.2`
- **OS**: macOS / Linux (Darwin arm64/x86_64)

---

## 2. Project Structure

```text
/Users/nikhil/Desktop/SIH/NIRMAN AI/
├── backend/
│   ├── app/                 # FastAPI application routes, repositories, services
│   ├── extraction/          # PDF extraction pipeline for 21 PAIMANA reports
│   ├── ml/                  # Temporal ML pipeline & trained model artifacts
│   │   └── saved_models/    # Persisted implementation_risk_rf.joblib
│   ├── tests/               # Pytest verification suite (24 passing tests)
│   └── requirements.txt     # Python requirements
├── nirman-ai-app/           # Next.js 16 App Router UI dashboard
│   ├── app/                 # Command Center, Risk Radar, Projects Detail UI
│   └── lib/api/client.ts    # Typed API client
├── data/
│   ├── raw/paimana/zip/     # 21 source PAIMANA PDFs
│   └── curated/paimana/     # 8,180 canonical project-month observations
├── RUN_NIRMAN_AI.md         # THIS ROOT RUN GUIDE
└── README.md
```

---

## 3. FIRST-TIME SETUP

### Step 3.1: Python Virtual Environment
```bash
cd backend
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
```

### Step 3.2: Frontend Node Modules
```bash
cd nirman-ai-app
npm install
```

---

## 4. VERIFY PYTHON ENVIRONMENT

```bash
cd backend
.venv312/bin/python --version
```
*Expected output*: `Python 3.12.14`

---

## 5. VERIFY CANONICAL DATASET

```bash
cd backend
.venv312/bin/python -c "import pandas as pd; df=pd.read_parquet('../data/curated/paimana/project_monthly_status.parquet'); print(f'Rows: {len(df)}, Projects: {df[\"project_id\"].nunique()}')"
```
*Expected output*: `Rows: 8180, Projects: 1723`

---

## 6. ML MODEL ARTIFACT

The candidate RandomForest implementation risk model is persisted at:
`backend/ml/saved_models/implementation_risk_rf.joblib`

To retrain and save the artifact if needed:
```bash
cd backend
.venv312/bin/python -m ml.train_and_save
```

---

## 7. BACKEND TEST SUITE

Run all 24 pytest verification suites:
```bash
cd backend
.venv312/bin/python -m pytest -v
```
*Expected output*: `24 passed, 3 warnings in ~99s`

---

## 8. FRONTEND PRODUCTION BUILD VERIFICATION

```bash
cd nirman-ai-app
npm run build
```
*Expected output*: `✓ Compiled successfully in ~4.4s`

---

## 9. DAILY / DEMO RUN SEQUENCE

### Terminal 1 — Start Backend Server
```bash
cd backend
.venv312/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2 — Start Frontend Development Server
```bash
cd nirman-ai-app
npm run dev
```

---

## 10. REAL PROJECT DIRECT API CHECKS (CURL)

With backend running on `http://127.0.0.1:8000`:

### Health Check
```bash
curl http://127.0.0.1:8000/api/v1/health
```

### Monitored Projects List
```bash
curl http://127.0.0.1:8000/api/v1/projects?limit=5
```

### Verified Real Project Detail — HUNLI-ANINI ROAD (`N04000073`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N04000073
```

### Real Model Risk Score — HUNLI-ANINI ROAD (`N04000073`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N04000073/risk
```

### Verified Real Project Detail — Delhi-Mumbai Expressway (`N24000948`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N24000948/risk
```

### SHAP Model Feature Drivers (`N24000948`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N24000948/drivers
```

### Prototype Rule Engine Interventions (`N24000948`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N24000948/recommendations
```

### Full Unified Project Assessment (`N24000948`)
```bash
curl http://127.0.0.1:8000/api/v1/projects/N24000948/assessment
```

### Analytics Summary
```bash
curl http://127.0.0.1:8000/api/v1/analytics/summary
```

### State Intelligence Aggregates
```bash
curl http://127.0.0.1:8000/api/v1/intelligence/states
```

### Sector Intelligence Aggregates
```bash
curl http://127.0.0.1:8000/api/v1/intelligence/sectors
```

---

## 11. DEMO FLOW IN BROWSER

1. Open [http://localhost:3000](http://localhost:3000) in Chrome/Safari.
2. View **National Infrastructure Command Center** headline KPIs (`Total Projects: 1,723`, `Sanctioned Budget`, `Total Expenditure`, `At-Risk Projects`).
3. Click any row in the **PAIMANA Monitored Projects Table** (e.g. `N04000073` or `N24000948`).
4. Inspect the **AI Model Risk Evaluation** hero card for live Risk Probability, Category, SHAP Model Drivers, and Rule Engine Recommendations.
5. Use sidebar tabs to switch views:
   - **Risk Radar**: High-Risk & Critical priority filter
   - **Projects**: Side-by-side table & detail drawer
   - **State Intelligence**: State/UT aggregate analysis
   - **Sector Intelligence**: Sectoral breakdown
   - **AI Insights**: Model architecture & risk rationale inspector

---

## 12. TROUBLESHOOTING

- **Port 8000 in use**: Kill existing process using `lsof -ti:8000 | xargs kill -9`.
- **Port 3000 in use**: Kill existing process using `lsof -ti:3000 | xargs kill -9`.
- **Model artifact missing**: Run `.venv312/bin/python -m ml.train_and_save` inside `backend/`.
- **Parquet fallback active**: Normal behavior when local environment has no live cloud database URL configured.

---

## 13. VERIFIED LOCALHOST URLS

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 14. VERCEL DEPLOYMENT PREPARATION

### Current Deployment Status
- **Status**: **NOT DEPLOYED** (Preparation completed; local application fully functional).
- **No live deployment commands or accounts connected during audit.**

### Deployment Boundary Architecture
1. **Frontend (Vercel Host)**:
   - Next.js 16 App Router application (`nirman-ai-app`).
   - Builds into static assets & serverless functions (`npm run build`).
   - Set environment variable `NEXT_PUBLIC_API_BASE_URL` in Vercel project settings pointing to the deployed backend URL.

2. **Backend (Python Host / Container)**:
   - FastAPI backend (`backend/`).
   - Relies on offline-trained Scikit-Learn Random Forest model (`implementation_risk_rf.joblib`) and 8,180 canonical PAIMANA observations (`data/curated/paimana/`).
   - Recommended hosting: Render, Railway, Google Cloud Run, or AWS ECS.
   - Set environment variable `CORS_ORIGINS` to allow your Vercel frontend domain (e.g., `https://nirman-ai.vercel.app`).

### Key Environment Variables Required
- **Frontend (`nirman-ai-app/.env`)**:
  ```env
  NEXT_PUBLIC_API_BASE_URL=https://<your-backend-domain>
  ```
- **Backend (`backend/.env`)**:
  ```env
  ENVIRONMENT=production
  CORS_ORIGINS=https://<your-vercel-app-domain>
  ```

### Future Production Deployment Steps
1. Deploy FastAPI backend to Python host (e.g. Render/Cloud Run) with `gunicorn`/`uvicorn`.
2. Connect Vercel repository to `nirman-ai-app` directory.
3. Configure `NEXT_PUBLIC_API_BASE_URL` in Vercel settings.
4. Trigger Vercel build (`npm run build`).

