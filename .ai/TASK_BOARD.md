# Task Board

| ID | Description | Status | Dependencies | Files involved | Validation method | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| P1-001 | Initialize project control files and repository state | COMPLETED | None | .ai/* | File inspection | Required project memory established |
| P1-002 | Create initial Phase 1 Next.js + TypeScript app shell | COMPLETED | P1-001 | nirman-ai-app/package.json, nirman-ai-app/app/* | npm run build | Dashboard shell preserved and functional |
| P1-003 | Add environment configuration and project docs | COMPLETED | P1-002 | .env.example, README docs, backend/README.md | File inspection and build validation | Required for setup and future integration |
| P1-004 | Define Phase 1 API contract and backend foundation | COMPLETED | P1-002 | .ai/API_CONTRACT.md, backend/app/* | Backend startup check and tests | Health endpoint and projects API wired |
| P1-005 | Create typed frontend API client and health-check connectivity flow | COMPLETED | P1-004 | nirman-ai-app/lib/api/*, nirman-ai-app/app/health-check.tsx | Frontend build and runtime fetch validation | API client extended for projects and risk |
| P1-006 | Add backend unit tests for app health and config | COMPLETED | P1-004 | backend/tests/*.py | pytest | Confirms health and config layer functions correctly |
| P1-007 | Standardize Python 3.12 and lock the development environment | COMPLETED | P1-006 | backend/.venv312, .ai/ENVIRONMENT.md, backend/README.md, .gitignore | python3.12 -m venv, pip install, pytest, python --version | Verified Python 3.12.14 in backend/.venv312 |
| P1-008 | Supabase / DB schema and repository foundation | COMPLETED | P1-007 | supabase/migrations/001_initial_schema.sql, .ai/DATABASE_SPEC.md, docs/DATABASE.md | SQL validation, RLS policies, pgvector extension | Added vector extension, RLS policies, and project ID text mapping |
| P2-001 | Locate and persist the real PAIMANA archive in the project | COMPLETED | P1-008 | data/raw/archive/zip.rar | file/hash validation | Archive preserved at canonical project path with SHA-256 verified |
| P2-002 | Extract and inventory the PAIMANA PDF corpus | COMPLETED | P2-001 | data/raw/paimana/zip/*.pdf | file enumeration, corpus count verification | Verified 21 PDFs spanning Jan 2025 through Jul 2026 |
| P2-003 | Create source manifest and inventory records | COMPLETED | P2-002 | data/manifests/paimana_source_manifest.json, data/curated/paimana/paimana_source_inventory.csv | File generation and inspection | Manifest and CSV are persisted and reusable |
| P2-004 | Validate provenance and corpus summary before downstream processing | COMPLETED | P2-003 | data/manifests/PAIMANA_CORPUS_REPORT.md | file inspection and checksum validation | Source provenance and archive hash documented |
| P2-005 | Full PAIMANA extraction, normalization, and validation pipeline | COMPLETED | P2-004 | backend/extraction/corpus_builder.py | live PDF extraction validation + dataset profile | Fixed ZIP, field alias, cost/expenditure, header, & zero-val bugs |
| P2D-001 | Audit codebase and integrations | COMPLETED | P2-005 | data/manifests/CODEBASE_AUDIT.md | source review and diagnostics | Audit completed and 30 findings cataloged |
| P2D-002 | Build leakage-safe temporal datasets & impute early NaNs | COMPLETED | P2D-001 | backend/ml/temporal.py, backend/ml/build_dataset.py | focused regression tests + Python 3.12 generation | 0 leakage, month 1-2 NaNs imputed, dataset paths dynamic |
| P2D-003 | Temporal baseline evaluation & risk API vertical slice | COMPLETED | P2D-002 | backend/ml/temporal.py, backend/app/api/v1/projects.py, nirman-ai-app/app/page.tsx | pytest, build_dataset.py, npm run build | Measured RF F1: 0.810 / PR-AUC: 0.869; Next.js frontend connected to live risk API |

## Status legend
NOT_STARTED, IN_PROGRESS, BLOCKED, TESTING, COMPLETED, DEFERRED
