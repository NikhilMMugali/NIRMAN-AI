# NIRMAN AI Environment

## Required runtime
- Python: 3.12
- Backend virtual environment: backend/.venv312
- Package manager: pip
- Frontend package manager: npm

## Live Share note
- Repository files are shared through the Live Share workspace, but Python, Node, virtual environments, `node_modules`, PATH, credentials, and IDE interpreter selection are machine-local.
- The current audit machine exposes Python 3.14.4 but no Python 3.12 executable, so it cannot validate the declared backend environment.
- Do not commit local virtual environments or machine-specific paths.

## Why Python 3.12
The current pinned backend dependency set has been verified with Python 3.12. The system Python 3.14 is not used for this project because it is not compatible with the current dependency set.

## Backend setup
```bash
cd backend
python3.12 -m venv .venv312
source .venv312/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
```

## Backend startup
```bash
cd backend
source .venv312/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend build
```bash
cd nirman-ai-app
npm install
npm run build
```

## Notes
- Do not use /usr/local/bin/python3 for backend development work.
- The project-local environment is the source of truth for backend validation and execution.
- Do not install project dependencies globally.
