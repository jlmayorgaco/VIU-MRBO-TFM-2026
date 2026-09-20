# Stage 3 full-text coding QA

Run UTC: 2026-09-13T22:52:46.659645+00:00

## Inputs and codebook

- Stage 2 queue records: **1150**
- Codebook SHA-256: `3ac3f7139131ce69ccd2b142065aaf5595aadcad88ea558176dae3b903df649a`
- Coding mode: **deterministic structural first pass over extracted document text**
- Full-text policy: detailed fields require `fulltext_verified`; abstracts and metadata are never upgraded.

## Evidence strength

- `abstract_only`: **123**
- `fulltext_verified`: **244**
- `metadata_only`: **762**
- `retrieval_error`: **21**

## Coding status and role

- `coded_abstract_limited`: **123**
- `coded_fulltext_structural_pass`: **244**
- `not_codeable_without_fulltext`: **783**

- `BASELINE`: **20**
- `CONTEXT`: **796**
- `CORE`: **155**
- `ENABLING`: **155**
- `SURVEY`: **24**

## Validation

- Evidence matrix rows: **1150**, with unique candidate IDs: **1150**.
- Every `fulltext_verified` row was read from its local PDF/HTML/XML path and has a structural coding row.
- Abstract-only rows retain only abstract-limited observations; metadata-only rows have blank detailed fields.
- Extraction errors: **0**; these remain visible and are not silently treated as evidence.
- Outputs: `fulltext_evidence_matrix.csv`, `fulltext_evidence_matrix.jsonl`, and `stage3_coding_log.csv`.

## Interpretation boundary

This matrix is an auditable first-pass codebook, not a substitute for human
close reading. Terms and snippets locate candidate evidence in actual text;
they do not, by themselves, establish correctness of a method, a theorem, a
numerical result, or a limitation. The Stage 4 synthesis must use the evidence
strength and source spans explicitly and keep claims conservative.
