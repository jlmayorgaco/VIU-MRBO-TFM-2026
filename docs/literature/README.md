# Literature PDF corpus

Use the arXiv collector to build a local PDF corpus for the literature review.
The default output goes under `output/literature/arxiv`, which is ignored by
Git and can grow without polluting the repository.

## Smoke run

```powershell
python scripts/collect_arxiv_pdfs.py --list-topics
python scripts/collect_arxiv_pdfs.py --topic multi_agent_mobile_robotics --max-results-per-topic 5 --no-download
```

## Download the configured corpus

```powershell
python scripts/collect_arxiv_pdfs.py --from-year 2010 --to-year 2026 --max-results-per-topic-year 250
```

The configured topics live in `configs/arxiv_literature_topics.yaml` and cover:

- multi-agent and multi-robot mobile robotics
- distributed and networked control
- graph theory, consensus, and network topology
- game theory, auctions, coalitions, and math foundations
- rigid formation, geometry, topology, and cooperative transportation
- AMR, warehouse, payload, swarm, and distributed optimization literature
- general robotics, SLAM, navigation, motion planning, MAPF, MARL, GNNs,
  resilient control, safety-critical CBFs, distributed MPC, temporal logic,
  cyber-physical systems, network science, and search/exploration literature

Outputs:

- `manifest.csv`: one row per unique arXiv paper, with matched topic labels.
- `manifest.jsonl`: machine-readable mirror of the manifest.
- `references_arxiv.bib`: initial BibTeX file for manual curation.
- `pdfs/by-id/<year>/`: canonical unique PDF copies.
- `pdfs/by-topic-year/<topic>/<year>/`: organized topic/year view. The
  collector uses hardlinks when possible, so the same PDF can appear in
  multiple topic folders without consuming duplicate disk space.
- `metadata/by-topic-year/<topic>/<year>/manifest.csv`: incremental metadata
  for each topic/year folder.
- `status.json`: progress file updated while the collector is running.
- `metadata/events.jsonl`: append-only progress/event log.

For a very large run, keep the default API pause or raise it. Re-running the
command skips existing PDFs unless `--overwrite` is passed.

## Monitor a running corpus download

```powershell
Get-Content output\literature\arxiv_full\status.json
Get-Content output\literature\arxiv_full\logs\collector-*.stdout.log -Tail 30
Get-ChildItem output\literature\arxiv_full\pdfs\by-id -Recurse -Filter *.pdf |
  Measure-Object Length -Sum
```

## Build the review database

The systematic review layer is defined by:

- `docs/literature/systematic_review_protocol.md`
- `docs/literature/screening_criteria.yaml`
- `docs/literature/extraction_schema.yaml`

Build the SQLite database and first screening queue from the downloaded corpus:

```powershell
python scripts/build_literature_review_db.py
```

Outputs:

- `output/literature/arxiv_full/literature.sqlite`
- `output/literature/arxiv_full/screening_candidates.csv`
- `output/literature/arxiv_full/topic_year_counts.csv`
- `output/literature/arxiv_full/review_db_summary.json`

The candidate CSV is sorted by a transparent keyword-based relevance score. It
is only a triage aid; final inclusion/exclusion decisions must keep reviewer
judgment and reason codes.

Optional text extraction for full-text screening:

```powershell
python scripts/build_literature_review_db.py --extract-text --text-max-pages 8
```

Use `--text-max-pages 0` only when full extraction is needed; it can take a long
time on a multi-GB corpus.
