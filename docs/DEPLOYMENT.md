# Deployment Guide

## Local development
- Frontend runs on port 3000
- Backend runs on port 8000
- Use environment variables from .env.example

## Production expectations
- Protect all server-side keys and never expose them to the Next.js client bundle.
- Keep the API on a separate host or service boundary from the frontend.
- Configure CORS to allow the exact frontend origin.

## Current deployment state
This project is still in the Phase 1 foundation stage. Production database, LLM, and document pipelines are not yet live.
