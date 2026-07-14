# Citation Audit Report

**Current refresh:** 2026-07-14<br>
**Bibliography:** `references.bib`<br>
**Scope:** 107 entries; 53 cited keys in 75 included-source uses
**Machine verdict:** `WARN`

## Outcome

- The recursive 27-file LaTeX inclusion graph was rebuilt from `main.tex`.
- Every cited key resolves in the bibliography; unresolved cited keys: **0**.
- The prior 99-entry ledger was retained and its use locations were reindexed against the current source.
- Eight later bibliography entries were checked against publisher, DOI, DBLP or institutional-repository records: `garey1978strong`, `shmoys1993generalized`, `yi2019operator`, `cherukuri2016primaldual`, `koshal2016aggregative`, `franci2022stochasticgne`, `bicchi1995closure` and `ferrari1992grasps`.
- All 107 ledger entries are `KEEP`; none is marked `FIX`, `REPLACE` or `REMOVE`.

## Current cited delta

Only `yi2019operator` and `cherukuri2016primaldual` from the eight-entry delta are cited by the included manuscript. Their separate roles in SP4 are supported by the Automatica publisher record and the University of Groningen institutional record. The other six entries occur only in retained supplementary source or remain uncited in the compiled manuscript; their metadata were nevertheless verified because they remain in `references.bib`.

## Earlier repairs retained

The earlier audit corrected 18 metadata records and rewrote or removed eight weak citation contexts. Those corrections remain present. The current refresh did not silently restore any rejected context.

## Residual limitation

A fresh external reviewer from a different model family and the institutional similarity service are not available in this workspace. Primary-source verification and local resolution therefore support the bibliography, but they do not justify an unconditional `PASS`. The verdict remains `WARN` until those two external checks are supplied.

## Artifacts

- `.aris/citation-audit/contexts.txt`: current 75 use locations and source lines.
- `CITATION_AUDIT.json`: 107-entry ledger, current source hashes and per-entry verdicts.
- `CITATION_AUDIT_FRESHNESS.json`: final PDF/bibliography freshness binding, regenerated after compilation.
