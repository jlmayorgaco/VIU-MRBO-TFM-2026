# Stage 1A provenance summary

Coverage: `open_discovery_only`  
WoS status: `pending_external_export`

## Source provenance counts

- `crossref`: 190
- `legacy_review`: 32
- `openalex`: 65

## API events

- Total events: 47
- Failures (`failed`, `forbidden`, `auth_required`, `parse_error`): 0
- Cache hits: 46

## Search protocol

- Query families executed: 14 source-query executions.
- Queries are preserved in `logs/stage1a_search_log.csv` with exact text,
  request hash, result count and returned count.

## Interpretation boundary

The 32 legacy rows remain seeds with `verification_status=unverified_seed`,
`evidence_status=not_evidence` and `screening_status=pending`. Metadata
enrichment does not promote them to evidence. No screening, full-text review,
deep reading, snowballing or novelty analysis was performed.
