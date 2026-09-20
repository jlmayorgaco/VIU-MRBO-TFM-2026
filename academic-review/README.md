# Academic review bootstrap

This directory contains the Stage 1A candidate-corpus pipeline for the MROB
TFM. It is deliberately separate from the thesis literature ledger and from
all previous TFM datasets.

Stage 1A produces a provenance-preserving bibliographic candidate corpus from
the 32 reconstructed legacy seeds plus open Crossref/OpenAlex discovery. The
legacy rows remain `unverified_seed`, carry `evidence_status=not_evidence`, and
are not screening decisions or included papers.

Web of Science exports are present and are reconciled as a separate
provenance. The current manifest labels coverage
`wos_partially_reconciled`: F03–F07 are complete, while the supplied F01 and
F02 exports contain their first 50 records only. This does not support an
exhaustiveness, absence, or novelty claim. Further authentic exports can be
placed under `inputs/wos/` without overwriting the open corpus.

## Run

From the repository root:

```powershell
python academic-review/scripts/validate_inputs.py
python academic-review/scripts/bootstrap_literature.py --mode all --resume
```

Use `--force` only when an explicit refresh of cached HTTP responses is
required. Stage 1A stops at candidate metadata and QA; it does not perform
screening, full-text acquisition, snowballing, or novelty analysis.

The contact email is stored only in the local `.env.literature` file and is
ignored by Git. Optional API keys are not required for this stage.

## Multisource V2

The derivative campaign lives under `multisource-v2/` and does not overwrite
V1. It executes the F1–F16 lattice against the configured public sources,
records raw responses and provider status, and produces reconciliation,
overlap, marginal-yield, citation, access and evidence-boundary artifacts.

```powershell
python academic-review/multisource-v2/scripts/run_multisource_v2.py --resume
```

CORE requires `CORE_API_KEY`. Google Scholar, Web of Science, Scopus and IEEE
Xplore are intentionally manual-only; their reproducible query/export packs
are under `multisource-v2/manual-packs/`.
