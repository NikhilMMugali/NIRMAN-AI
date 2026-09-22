# Development Guide

## Frontend

From the app root:

```bash
cd /Users/nikhil/Desktop/SIH/NIRMAN AI/nirman-ai-app
npm install
npm run dev
```

The frontend is intentionally kept close to the original government dashboard design while the backend API foundation is added.

## Backend

From the repository root:

```bash
cd /Users/nikhil/Desktop/SIH/NIRMAN AI/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "nirman-ai-api"
}
```

## Current scope
This repository is intentionally limited to Phase 1 integration and foundation work.
