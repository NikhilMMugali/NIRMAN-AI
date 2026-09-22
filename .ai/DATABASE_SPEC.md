# NIRMAN AI Database Specification

## Database architecture
The system is designed around a layered data model:

SOURCE -> CURATED -> ANALYTICS -> AI OUTPUT

This keeps official reported data, derived metrics, analytical outputs, and AI-generated recommendations separate while preserving provenance and auditability.

## Core entities

### projects
Canonical project records representing the main PAIMANA project entity.

### project_monthly_status
Monthly project observation table keyed by project and reporting month.

### project_issues
Reported issues associated with a project and reporting month.

### project_milestones
Milestone history and state changes for a project.

### project_outcomes
Historical outcomes used for future supervised learning.

### risk_predictions
Time-bound risk predictions with model metadata.

### risk_drivers
Feature-level explanations for each risk prediction.

### alerts
Operational early-warning alerts for projects and supervision teams.

### recommendations
Actionable recommendations that are not implicitly LLM-only.

### simulation_runs
Scenario and baseline simulation outputs for reproducibility.

### data_sources
Source provenance metadata for data ingestion and extraction.

### data_quality
Quality checks and validation metadata for project and reporting fields.

### documents
Uploaded or ingested reports and source documents.

### document_chunks
Chunked document content for future retrieval-based workflows.

### chat_sessions
Conversation session metadata.

### chat_messages
User/assistant message history for operational chat contexts.

### model_versions
Model registries for analytics and prediction pipelines.

## Key rules
- Official reported data, derived data, predicted data, estimated data, and recommended data are stored separately and traced using provenance metadata.
- `project_id` is treated as the canonical external project key, but the schema keeps the database primary key as a UUID for stable relational use.
- Duplicate project-month records are prevented via a unique constraint on `(project_id, reporting_month)`.
- AI-generated outputs stay logically separate from official source records.
- The first schema is intentionally minimal and extensible without overengineering.

## Entity relationship overview

```text
projects
   |
   +-- project_monthly_status
   +-- project_issues
   +-- project_milestones
   +-- project_outcomes
   +-- risk_predictions
   +-- alerts
   +-- recommendations
   +-- simulation_runs
   +-- data_quality
   +-- documents
   +-- chat_messages

risk_predictions
   +-- risk_drivers

documents
   +-- document_chunks

chat_sessions
   +-- chat_messages
```

## Required environment variables
The backend currently expects the following keys in environment configuration:

```bash
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
```

No production credentials should be committed to this repository.

## Migration procedure
```bash
# from repository root
psql "$DATABASE_URL" -f supabase/migrations/001_initial_schema.sql
```

Or apply the migration through the Supabase SQL editor or migration tooling when using the hosted Supabase environment.

## Local/development setup
- Use the local pydantic settings environment file for configuration.
- Keep the backend on Python 3.12.
- Use the project-local venv at backend/.venv312.
- Do not hard-code production secrets in source files.

## Known limitations
- No PAIMANA data has been loaded yet.
- No extraction pipeline is active yet.
- No ML model training or RAG retrieval has been implemented.
- This schema is for the required database foundation only.
