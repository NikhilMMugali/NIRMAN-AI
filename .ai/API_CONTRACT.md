# API Contract

This is the current Phase 1 contract for the NIRMAN AI foundation. Only the health endpoint is implemented.

## Health
- GET /api/v1/health
  Response:
  {
    "status": "ok",
    "service": "nirman-ai-api"
  }

## Projects (database-ready, data not yet loaded)
- GET /api/v1/projects
  Response: empty dataset with the correct schema shape when no PAIMANA data has been loaded yet
- GET /api/v1/projects/{project_id}
- GET /api/v1/projects/{project_id}/history
- GET /api/v1/projects/{project_id}/risk
- GET /api/v1/projects/{project_id}/drivers

## Alerts and intelligence (database-ready, data not yet loaded)
- GET /api/v1/alerts
- GET /api/v1/sectors
- GET /api/v1/states

## Database-backed behavior
- Repositories are prepared to handle persistence and future project queries.
- Empty list responses are valid when no operational data has been imported yet.
- No fabricated project statistics or production dataset values are included in API responses.

## Contract design principles
- Typed payloads
- Structured error responses
- Versioned endpoints
- Explicit empty/not-implemented responses for future endpoints without live data
- No fabricated project statistics or production dataset values
- No ML, document extraction, or chatbot endpoints are active yet

## Error handling
- 400: validation error
- 404: resource not found
- 500: internal server error
- 503: unavailable dependency

## Notes
The current backend implementation is intentionally minimal to satisfy the Phase 1 foundation requirement and keep the architecture ready for future ingestion, ML, and document intelligence work.
