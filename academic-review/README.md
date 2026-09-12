# Academic review bootstrap

This directory contains the Stage 1A candidate-corpus pipeline for the MROB
TFM. It is deliberately separate from the thesis literature ledger and from
all previous TFM datasets.

Stage 1A produces a provenance-preserving bibliographic candidate corpus from
the 32 reconstructed legacy seeds plus open Crossref/OpenAlex discovery. The
legacy rows remain `unverified_seed`, carry `evidence_status=not_evidence`, and
are not screening decisions or included papers.

Web of Science exports are not present in this run. The resulting coverage is
therefore `open_discovery_only`, with `wos_status=pending_external_export`.
Authentic exports can later be placed under `inputs/wos/` and reconciled as a
new provenance without overwriting the open corpus.

## Run

From the repository root:

```powershell
python academic-review/scripts/validate_inputs.py
python academic-review/scripts/bootstrap_literature.py --mode open --resume
```

Use `--force` only when an explicit refresh of cached HTTP responses is
required. Stage 1A stops at candidate metadata and QA; it does not perform
screening, full-text acquisition, snowballing, or novelty analysis.

The contact email is stored only in the local `.env.literature` file and is
ignored by Git. Optional API keys are not required for this stage.
