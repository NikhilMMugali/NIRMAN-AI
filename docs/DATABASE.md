# NIRMAN AI Database Foundation

## Scope
This database layer is a schema foundation for PAIMANA ingestion, prediction workflows, and RAG-based intelligence. It is not yet a live operational database.

## Architecture

```text
SOURCE
  |
  v
CURATED
  |
  v
ANALYTICS
  |
  v
AI OUTPUT
```

## Core tables
- projects
- project_monthly_status
- project_issues
- project_milestones
- project_outcomes
- risk_predictions
- risk_drivers
- alerts
- recommendations
- simulation_runs
- data_sources
- data_quality
- documents
- document_chunks
- chat_sessions
- chat_messages
- model_versions

## Primary relationships

```text
projects
   ├── project_monthly_status
   ├── project_issues
   ├── project_milestones
   ├── project_outcomes
   ├── risk_predictions
   ├── alerts
   ├── recommendations
   ├── simulation_runs
   ├── data_quality
   ├── documents
   └── chat_messages

risk_predictions
   └── risk_drivers

documents
   └── document_chunks

chat_sessions
   └── chat_messages
```

## Important design principles
- Official and derived data are separated by table semantics and metadata.
- Provenance is recorded in `data_sources` and by source metadata columns.
- Historical predictions are stored immutably where practical.
- Recommendations are not assumed to be only LLM-generated.
- Documents are stored by metadata and file reference, not as large binary blobs in standard app rows.

## Migration location
- [supabase/migrations/001_initial_schema.sql](../supabase/migrations/001_initial_schema.sql)

## Repository layer
The backend repository pattern is intentionally minimal:

- A base repository abstraction provides the common database client contract.
- Feature-specific repositories manage project, status, alert, and risk persistence logic.

This keeps business logic separate from data access and avoids direct SQL in route handlers.

## Known limitations
- Canonical PAIMANA files exist locally, but no records are loaded into Supabase.
- The persisted extraction-quality artifact has rows from 5 of 21 PDFs; the remaining corpus requires parser investigation.
- No live Supabase connection, RLS policy, or repository query implementation is configured.
- Supabase credentials and direct database connection usage are intentionally not included in docs.
- This is a schema and repository foundation only, not a production operational database.
