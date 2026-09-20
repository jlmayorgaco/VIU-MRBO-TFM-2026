# Stage 1C query-repair report

Run UTC: 2026-09-13T22:43:30.348716+00:00

## Frozen input and bounded scope

- Stage 1B CSV SHA-256: `81d81918510729460b687b72090c16b6469e8b4d6b77385f79868444687398da`
- Repair configuration SHA-256: `ee1b3a93c792ff434d77a2768bf3ed2ab649d3cf15d9a7d3a0aed9dd47d77847`
- Stage 1B input rows: **1331**
- Repair query families: **8** (maximum configured: 12)
- Provider executions: **16** (Crossref/OpenAlex per family)
- Original Q1–Q7 families were not modified.

## Query repair results

- New candidate records from repair queries: **275**
- New repair-query records classified relevant/plausible: **123**
- Additional records from the second bounded one-hop recall check: **703**
- Additional relevant/plausible records from that recall check: **296**
- Total new relevant/plausible records attributable to this repair round: **419**
- Terminal API failures: **0**

The repair round was triggered because Stage 1B showed meaningful missing
terminology and did not support a saturation claim. The targeted additions
were selected to test demonstrated gaps, not to maximize corpus size.

### Relevant repair families observed

- `amr_agv_logistics`: 24
- `collective_shared_load_transport`: 10
- `force_wrench_contact_feasibility`: 4
- `formation_docking_cooperative_motion`: 8
- `industrial_intralogistics`: 14
- `multiagent_robotic_coordination`: 30
- `population_evolutionary_potential_games`: 15
- `safety_collision_barrier_transport`: 21

## Final Stage 1C derivative

- Candidate count: **2309**
- `include_fulltext`: **613**
- `maybe_fulltext`: **537**
- `exclude`: **1159**
- Full-text queue: **1150**
- One-hop recall anchors: **20**
- Recall direction cap: 50 backward references and 25 forward citations per anchor.

## Validation

- Candidate IDs are unique; DOI values are unique after normalization.
- All records retain `evidence_status=not_evidence` and
  `screening_status=screened_title_abstract`.
- Every excluded record carries an explicit exclusion reason.
- The full-text queue equals `include_fulltext + maybe_fulltext` exactly.
- The Stage 1C regression suite is executed separately with
  `python -m pytest academic-review/tests -q`.

## Saturation decision

The repair round found additional relevant/plausible records, so it does not
support near-saturation. Query expansion stops after this single repair round,
as required by the autonomous protocol; further expansion is deferred until
full-text evidence and Web of Science availability can be assessed. This is
not a formal recall estimate or proof of exhaustiveness.

## Evidence boundary and next stage

All records remain `evidence_status=not_evidence`. Stage 1C only creates a
better acquisition candidate set. Stage 2 may attempt legal/open full-text
retrieval; paywalled or otherwise inaccessible works must be marked
`unavailable_legally` or `abstract_only` without bypassing access controls.

`coverage_status=open_sources_plus_limited_snowballing;wos_partially_reconciled`
`wos_status=present_partial`
