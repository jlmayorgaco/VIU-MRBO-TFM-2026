# Candidate corpus schema

Core fields:

- `candidate_id` — immutable local ID after first normalization pass.
- `title`
- `title_original` — original seed/source title preserved verbatim where available.
- `title_norm`
- `authors`
- `authors_original`
- `authors_norm`
- `year`
- `year_original`
- `venue`
- `venue_original`
- `doi`
- `doi_original`
- `doi_norm`
- `abstract`
- `document_type`
- `source_ids` — JSON/string representation of source identifiers.
- `provenance_sources` — semicolon-separated discovery sources.
- `provenance_queries` — semicolon-separated query IDs.
- `provenance` — semicolon-separated source provenance labels.
- `verification_status`
- `metadata_verification_status`
- `evidence_status` — `not_evidence` for all Stage 1A candidates.
- `screening_status` — `pending` until a later screening stage.
- `legacy_seed_id`
- `wos_ut`
- `citation_count`
- `citation_count_source`
- `retrieved_at_utc`
- `dedup_status`
- `duplicate_status` — `unique` or `needs_review`.
- `dedup_parent_candidate_id`
- `seed_raw` — JSON representation of the original legacy seed row, when applicable.
- `notes`

Permitted verification statuses at Stage 1:

- `unverified_seed`
- `metadata_verified`
- `metadata_partial`
- `unresolved`

Later statuses must not be assigned during Stage 1:

- `abstract_screened`
- `fulltext_verified`
- `claim_coded`
