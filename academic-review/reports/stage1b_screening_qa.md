# Stage 1B screening and recall QA

Run UTC: 2026-09-13T22:43:18.132377+00:00

## Frozen inputs

- Stage 1A CSV SHA-256: `3e5c589af0cf149c1a12384c69fbdb6eeb8692fb058c43c5f3880c185c1ef99f`
- Stage 1A JSONL SHA-256: `f1174a84643ad346cc54896fb499b74829c5e0a194cce1f4d39af618f881ac7e`
- Screening protocol SHA-256: `cbbd7c321811594f790350ab57f40ee5336058e6bce281f7dbd741d36014ccb5`
- Stage 1A inputs were not overwritten.

## Corpus and identity

- Stage 1A unique candidates: **376**
- Stage 1B candidates after identity resolution and bounded recall: **1331**
- Additional candidate records from one-hop recall: **957**
- Additional relevant/plausible records from recall: **447**
- DOI recovery attempts: **33**; recovered: **25**
- Duplicate-resolution records: **11**; decisions: `{'merge_published_preprint': 2, 'merged_alias': 2, 'retain_unresolved': 2, 'retain_distinct_standard_revision': 3, 'retain_distinct_work': 2}`
- DOI present/missing after Stage 1B: **1269/62**

## Legacy seed reconciliation

- Seed records audited: **32**
- Classification: `{'corrected': 17, 'verified': 13, 'unresolved': 2}`
- No seed status was used as an automatic inclusion rule.

## Screening decisions

- `include_fulltext`: **448**
- `maybe_fulltext`: **283**
- `exclude`: **600**
- Final classifier: `deterministic_keyword_rules_v2`; semantic scope remains the frozen `screening_protocol_v1`.

### Exclusion distribution

- `no_multi_robot_component`: 89
- `no_relevant_coordination`: 9
- `non_research_item`: 26
- `out_of_domain`: 30
- `wrong_robotic_problem`: 446

## Provenance overlap

- `crossref`: 189
- `legacy_review`: 32
- `openalex`: 1021
- `openalex_snowball`: 986
- `wos:F01_primary_wos_plaintext_full_record_cited_references.txt`: 50
- `wos:F02_primary_wos_plaintext_full_record_cited_references.txt`: 50
- `wos:F03_primary_wos_plaintext_full_record_cited_references.txt`: 14
- `wos:F04_primary_wos_plaintext_full_record_cited_references.txt`: 13
- `wos:F05_primary_wos_plaintext_full_record_cited_references.txt`: 23
- `wos:F06_primary_wos_plaintext_full_record_cited_references.txt`: 3
- `wos:F07_primary_wos_plaintext_full_record_cited_references.txt`: 1

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

`coverage_status=open_sources_plus_limited_snowballing;wos_partially_reconciled`
`wos_status=present_partial`

- Web of Science is partially reconciled from the declared manual exports; F01 and F02 remain incomplete, so the corpus is not represented as exhaustive.
- OpenAlex citation neighborhoods were used only for one-hop recall auditing.
- No PDF corpus was downloaded; no full-text coding, novelty claim or literature review prose was produced.

## Stop rule

Stage 1B stops after identity audit, bounded recall and title/abstract screening.
The full-text queue is an acquisition input, not scientific evidence.
