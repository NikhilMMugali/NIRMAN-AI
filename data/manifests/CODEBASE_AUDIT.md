# NIRMAN AI Codebase Audit

## Scope and baseline

Reviewed the frontend prototype and Next.js app, FastAPI routes/configuration, repositories, both extraction implementations, Supabase migration, tests, data artifacts, documentation, and project controls. The repository is a Phase 2 extraction foundation with an unimplemented live data/API layer, not a production-connected dashboard.

The shell is outside the Live Share mount at `/home/dhruv`; `git rev-parse --show-toplevel` fails there, while the shared editor filesystem exposes the repository at `vsls:/`. This machine has Python 3.14.4, Node 24.20.0, and npm 11.19.0, but no Python 3.12 executable. Therefore baseline tests, corpus rebuild, and frontend build could not be executed from this agent context.

## Findings

| Severity | Finding | Affected files | Cause / impact | Fix or disposition | Verification |
| --- | --- | --- | --- | --- | --- |
| CRITICAL | Supabase migration assumes `pgcrypto` and `vector` extensions and has no RLS policy | `supabase/migrations/001_initial_schema.sql` | Fresh deployment can fail; exposed tables have no explicit access policy | Left for database-auth phase because no live Supabase is configured; recorded as a release blocker | Migration review |
| CRITICAL | Dashboard presents fabricated KPIs, alerts, projects, and dates as live intelligence | `nirman-ai-app/app/page.tsx` | UI constants are not backed by API data | Left intentionally for the API integration phase; must be removed before operational use | Frontend source review |
| CRITICAL | Only 5 of 21 PDFs currently yield extracted rows | `data/curated/paimana/extraction_quality.csv` | Sixteen documents are warning-only, so the current ML corpus covers only 2025-02 through 2025-06 | Blocked pending parser investigation and corpus rebuild | Persisted extraction-quality review |
| HIGH | Business API endpoints and repositories return placeholders/empty values | `backend/app/api/v1/*.py`, `backend/app/repositories/*` | No live repository contract or ingestion service exists | Left as a known integration blocker; no production claims made | Route/repository review |
| HIGH | Two competing extraction pipelines exist | `extraction/pipeline.py`, `backend/extraction/pipeline.py`, `backend/extraction/corpus_builder.py` | Different behavior and path assumptions can produce inconsistent records | Canonical ML work consumes `project_monthly_status`; consolidation remains next integration task | Import and source review |
| HIGH | Canonical builder silently drops duplicate project-month rows | `backend/extraction/corpus_builder.py` | Potential data loss and no review trail | Fixed: duplicate rows are written to `project_monthly_status_duplicates.csv` before deterministic deduplication | Regression/source inspection |
| HIGH | Curated provenance contains machine-specific absolute paths | generated CSV artifacts, `backend/extraction/corpus_builder.py` | Artifacts are not portable across CI/developers | Fixed at source for the next rebuild using repository-relative paths; existing generated files require rebuild | Source inspection |
| HIGH | Extraction dependencies were absent from requirements | `backend/requirements.txt`, `backend/extraction/corpus_builder.py` | Reprovisioned environments cannot run extraction/ML | Fixed by declaring pandas, pyarrow, pdfplumber, and scikit-learn | Editor diagnostics |
| HIGH | 404 regression test contradicted the structured error handler | `backend/tests/test_health.py`, `backend/app/core/errors.py` | Test expected FastAPI's default `detail`, while the app intentionally returns `{success,error}` | Fixed the test contract | Source review |
| HIGH | Ambiguous `N.A.` cost cells could fabricate revised-cost labels | `backend/extraction/corpus_builder.py` | A second numeric value was always interpreted as revised cost | Fixed parser to leave revised cost null and retain anticipated cost when revision is unavailable | Source inspection |
| HIGH | Empty extraction could crash project-summary generation | `backend/extraction/corpus_builder.py` | Groupby expected columns absent from an empty DataFrame | Fixed with an explicit empty summary schema | Source inspection |
| MEDIUM | Time-overrun labels cannot be supported | canonical fields and Supabase schema | No planned/actual completion dates are populated in the canonical dataset | Explicitly classified `NOT_SUPPORTED`; no time dataset/model generated | Dataset schema review |
| MEDIUM | Cost and expenditure semantics need source-level validation | builder and `.ai/DATA_DICTIONARY.md` | Numeric values exist but outcome semantics are not independently observed | Cost target is only `PARTIALLY_SUPPORTED` and uses a documented proxy | Target definition |
| MEDIUM | No typed business response schemas, auth, pagination, or rate limiting | `backend/app/api/v1`, `backend/app/schemas` | Operational API contract is incomplete | Deferred to API integration phase | Source review |
| LOW | Phase and documentation controls were stale | `.ai/*`, `docs/README.md`, `.ai/AGENT_HANDOFF.md` | Prior status did not reflect extracted artifacts | Updated for Phase 2D status below | File inspection |

## Integration audit

- Frontend -> API: only the health check is live; dashboard values are static and API base URL defaults to localhost.
- API -> service -> repository: no service layer is wired; routes return placeholders and repositories return empty values.
- Repository -> database: no Supabase client/query implementation is present; schema names broadly match intended entities but ingestion is absent.
- Extraction -> canonical dataset: files exist and counts were independently read, but the persisted profile is stale/inconsistent with the current claims and contains absolute paths until rebuilt.
- Dataset -> ML: temporal identifiers and numeric fields exist; no completion-date outcome exists, so schedule prediction is not supportable.

## Baseline status

- Backend test command: not executed; no Python 3.12 interpreter is available to this agent and the shell cannot see `vsls:/`.
- Frontend build command: not executed; the shell cannot see `nirman-ai-app`.
- No test/build pass is claimed.

## Remaining release blockers

Live Supabase ingestion, RLS/authentication, real API repositories/services, and replacing static frontend intelligence remain unresolved. They are not represented as completed by Phase 2D.
