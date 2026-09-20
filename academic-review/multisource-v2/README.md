# Multisource literature campaign V2

This namespace is a derivative of the frozen V1 review. It adds a versioned
F1–F16 concept lattice, modern/foundational windows, independent source logs,
raw-response hashes, conservative reconciliation, source-overlap and marginal
yield tables, bounded citation discovery, and a legal deep-evidence queue.

Run from the repository root:

```powershell
python academic-review/multisource-v2/scripts/run_multisource_v2.py --resume
```

The first run should omit `--resume` if cached V2 responses must be refreshed.
Use `--sources arxiv,semantic_scholar` for a bounded source subset and
`--skip-citations` when the OpenCitations rate limit should not be used.

## Access boundaries

The executor uses public endpoints for Crossref, OpenAlex, arXiv, Semantic
Scholar, OpenAIRE, DBLP and DOAJ. CORE is attempted only when `CORE_API_KEY`
exists in the ignored local environment. Unpaywall and OpenCitations are
bounded Tier-B enrichments.

Google Scholar, Web of Science, Scopus and IEEE Xplore are not scraped or
automated. Their query/export packs are generated under `manual-packs/` and
remain marked `manual_pending` until a human export is supplied.

## Interpretation boundary

`candidate_records_v2.csv` and `candidate_corpus_v2_reconciled.csv` contain
metadata candidates only. The `deep_evidence_queue.csv` distinguishes existing
V1 verified full text from new records awaiting legal acquisition. No row is
promoted to scientific evidence by this campaign, and no TFM experiment is
run here.
