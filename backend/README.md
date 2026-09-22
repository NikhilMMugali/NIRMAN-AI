# NIRMAN AI Backend

This backend provides the Phase 1 application foundation for the NIRMAN AI platform.

## Required runtime

Python 3.12 is required for the current dependency set.

The project must use the local virtual environment at:

backend/.venv312/

Do not rely on the system Python at /usr/local/bin/python3 for backend work.

## Setup

From the repository root:

```bash
cd backend
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run tests

```bash
cd backend
source .venv312/bin/activate
python -m pytest -q
```

## Start the backend

```bash
cd backend
source .venv312/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Current status

Implemented:
- FastAPI application skeleton
- Versioned API router
- Health endpoint at /api/v1/health
- Configuration management
- CORS support
- Structured error handling
- Request logging foundation

Planned:
- Supabase/PostgreSQL integration
- PAIMANA ingestion and data validation
- Risk prediction service
- Document extraction and analysis
- Recommendation engine
- RAG and grounded LLM orchestration

Not yet implemented:
- ML model training or inference
- PDF extraction workflows
- Real project data ingestion
- Recommendation or chatbot workflows
