# NIRMAN AI Extraction Specification

## Scope
This document defines the PAIMANA extraction foundation. It is intentionally limited to source intake, table parsing, normalization, validation, provenance, and batch resilience. It does not include ML, RAG, or LLM integration.

## Supported input
- single PDF
- batch directory of PDFs
- ZIP archive if provided to the CLI wrapper

## Directory layout
```text
data/
  raw/paimana/
  staging/paimana/
  curated/paimana/
  training/paimana/
  manifests/
```

## Extraction flow
1. Detect document type and file hash.
2. Read source text from the PDF.
3. Extract candidate project fields based on configured aliases.
4. Normalize numeric, percentage, and date values.
5. Validate core fields and data quality checks.
6. Resolve project identity.
7. Attach provenance metadata.
8. Record success/failure in the manifest.
9. Write staging output for downstream validation.

## Field mapping strategy
The field mapping is config-driven via [extraction/config/paimana_schema.yaml](../extraction/config/paimana_schema.yaml). Aliases are provided for the main PAIMANA fields encountered in the project reports.

## Provenance model
Every extraction result records:
- source document
- source file hash
- source page
- reporting month
- extraction method
- extraction confidence

## Validation rules
- missing project_id is rejected
- missing project_name is rejected
- physical progress must be between 0 and 100
- risk percentage fields must be between 0 and 100 when present
- duplicate file hash is treated as a duplicate candidate
- invalid values are preserved as raw but flagged rather than silently converted to zero

## Duplicate handling
- file hash detection prevents repeated ingestion of the same document
- project-hour/month duplicates are tracked as review cases in staging

## Batch behavior
- one document failure does not stop the batch
- partial success is recorded in the extraction manifest
- processing summary is emitted at the end of the run

## Confidence scoring
- extraction confidence is a decimal between 0 and 1
- low-confidence fields are flagged for review

## Command-line usage
```bash
cd backend
source .venv312/bin/activate
python -m extraction.pipeline --input data/raw/paimana
```

## Known limitations
- This is a foundational parser, not a full OCR and table extraction engine.
- Actual PAIMANA PDFs must be reviewed against the field aliases and normalization rules during Phase 2 ingest work.
- No ML, recommendation, or RAG features are included here.
