# Stage 1A provenance summary

Coverage: `wos_partially_reconciled`
WoS status: `present_partial`

## Source provenance counts

- `crossref`: 190
- `legacy_review`: 32
- `openalex`: 65
- `wos:F01_primary_wos_plaintext_full_record_cited_references.txt`: 50
- `wos:F02_primary_wos_plaintext_full_record_cited_references.txt`: 50
- `wos:F03_primary_wos_plaintext_full_record_cited_references.txt`: 14
- `wos:F04_primary_wos_plaintext_full_record_cited_references.txt`: 13
- `wos:F05_primary_wos_plaintext_full_record_cited_references.txt`: 23
- `wos:F06_primary_wos_plaintext_full_record_cited_references.txt`: 3
- `wos:F07_primary_wos_plaintext_full_record_cited_references.txt`: 1

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
