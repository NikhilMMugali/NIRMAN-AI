# NIRMAN AI Data Dictionary

## Overview
This dictionary defines the current Phase 2 extraction foundation fields. It intentionally marks future fields as `FUTURE_TARGET` when they are not yet being populated.

## Field catalog

### project_id
- Type: string
- Meaning: canonical PAIMANA project identifier
- Source: PAIMANA report / project registry
- Nullable: false for usable records
- Unit: N/A
- Raw representation: original source text
- Normalized representation: trimmed identifier string
- Status: OBSERVED

### project_name
- Type: string
- Meaning: PAIMANA project name
- Source: PAIMANA report / project registry
- Nullable: false for usable records
- Unit: N/A
- Raw representation: original source text
- Normalized representation: trimmed title string
- Status: OBSERVED

### original_cost
- Type: numeric
- Meaning: original sanctioned cost
- Source: PAIMANA report
- Nullable: true
- Unit: currency value
- Raw representation: rupee value with labels and commas
- Normalized representation: numeric value
- Status: OBSERVED

### revised_cost
- Type: numeric
- Meaning: revised cost estimate if available
- Source: PAIMANA report
- Nullable: true
- Unit: currency value
- Raw representation: rupee value with labels and commas
- Normalized representation: numeric value
- Status: OBSERVED

### expenditure
- Type: numeric
- Meaning: cumulative expenditure
- Source: PAIMANA report
- Nullable: true
- Unit: currency value
- Raw representation: rupee value with labels and commas
- Normalized representation: numeric value
- Status: OBSERVED

### physical_progress
- Type: numeric
- Meaning: percentage physical progress
- Source: PAIMANA report
- Nullable: true
- Unit: percentage
- Raw representation: value with or without % sign
- Normalized representation: numeric percentage
- Status: OBSERVED

### reporting_month
- Type: string
- Meaning: reporting period for the observed record
- Source: PAIMANA report metadata
- Nullable: true
- Unit: YYYY-MM or month label
- Raw representation: original source label
- Normalized representation: canonical month string
- Status: OBSERVED

### source_file
- Type: string
- Meaning: input document path
- Source: extraction metadata
- Nullable: false
- Unit: N/A
- Raw representation: file path
- Normalized representation: repo-relative or absolute path
- Status: OBSERVED

### file_hash
- Type: string
- Meaning: source file fingerprint for duplicate detection
- Source: extraction metadata
- Nullable: false
- Unit: SHA-256 hex string
- Raw representation: file bytes
- Normalized representation: digest text
- Status: OBSERVED

### extraction_confidence
- Type: numeric
- Meaning: confidence in extracted field or record
- Source: extraction pipeline
- Nullable: true
- Unit: 0.0 to 1.0
- Raw representation: pipeline estimate
- Normalized representation: float in [0,1]
- Status: DERIVED

## Future target fields
These fields are intentionally not treated as available yet and remain future targets:
- risk score
- cost overrun label
- time overrun label
- recommendation text
- chunk embeddings
- model predictions
- LLM explanations

Status: FUTURE_TARGET

## Phase 2D derived fields

### temporal features
- Type: numeric
- Meaning: current and history-derived features used at prediction cutoff
- Status: DERIVED
- Leakage rule: rolling features use only rows before the prediction period; future rows are label-only

### implementation_risk_target
- Type: integer label
- Meaning: next observed month has missing or non-increasing physical progress
- Status: SUPPORTED_PROXY

### cost_overrun_target
- Type: integer label
- Meaning: next observed revised cost exceeds next observed original cost by more than 5 percent
- Status: PARTIALLY_SUPPORTED_PROXY
