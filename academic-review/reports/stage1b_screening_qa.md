# Stage 1B screening and recall QA

Run UTC: 2026-09-12T20:42:01.580852+00:00

## Frozen inputs

- Stage 1A CSV SHA-256: `41fbeaed5d49a2588955ddee5718d9ac36cd9b5a013daecdb143da3d9240ef85`
- Stage 1A JSONL SHA-256: `d169e97f710884953a09d2b6b6f83bbc32f43f4fd4d5571007fdb971bec8d6f2`
- Screening protocol SHA-256: `cbbd7c321811594f790350ab57f40ee5336058e6bce281f7dbd741d36014ccb5`
- Stage 1A inputs were not overwritten.

## Corpus and identity

- Stage 1A unique candidates: **246**
- Stage 1B candidates after identity resolution and bounded recall: **1218**
- Additional candidate records from one-hop recall: **974**
- Additional relevant/plausible records from recall: **463**
- DOI recovery attempts: **5**; recovered: **2**
- Duplicate-resolution records: **9**; decisions: `{'merge_published_preprint': 2, 'merged_alias': 2, 'retain_distinct_standard_revision': 3, 'retain_distinct_work': 2}`
- DOI present/missing after Stage 1B: **1161/57**

## Legacy seed reconciliation

- Seed records audited: **32**
- Classification: `{'corrected': 17, 'verified': 13, 'unresolved': 2}`
- No seed status was used as an automatic inclusion rule.

## Screening decisions

- `include_fulltext`: **340**
- `maybe_fulltext`: **280**
- `exclude`: **598**
- Final classifier: `deterministic_keyword_rules_v2`; semantic scope remains the frozen `screening_protocol_v1`.

### Exclusion distribution

- `no_multi_robot_component`: 89
- `no_relevant_coordination`: 9
- `non_research_item`: 25
- `out_of_domain`: 28
- `wrong_robotic_problem`: 447

## Provenance overlap

- `crossref`: 189
- `legacy_review`: 32
- `openalex`: 1038
- `openalex_snowball`: 986

## Recall audit

- Anchors selected: **20**; one hop only.
- Reference edges were bounded to at most 50 per anchor; forward citing works to 25 per anchor, sorted with the current OpenAlex `publication_date:desc` syntax.
- Citation/API retrieval events: **37** summary events; terminal API failures: **0**.
- Descriptive diagnostic: **evidence of additional relevant literature; not near saturation under the descriptive diagnostic**.
- This is not a formal saturation proof. New records were screened with the same protocol and were not included because of citation adjacency alone.

## Manual QA

- Reviewer record: `codex_agent_manual_pass` (single reviewer; not independent inter-reviewer validation).
- Randomization seed: **20260912**
- Audited include/exclude/maybe: **20/20/20**
- Corrections recorded: **0**
- Disagreement metric: **0/selected (single-reviewer correction audit; not inter-reviewer agreement)**

## Coverage boundary and deviations

`coverage_status=open_sources_plus_limited_snowballing`  
`wos_status=pending_external_export`

- Web of Science remains pending and the corpus is not represented as exhaustive.
- OpenAlex citation neighborhoods were used only for one-hop recall auditing.
- No PDF corpus was downloaded; no full-text coding, novelty claim or literature review prose was produced.

## Stop rule

Stage 1B stops after identity audit, bounded recall and title/abstract screening.
The full-text queue is an acquisition input, not scientific evidence.
