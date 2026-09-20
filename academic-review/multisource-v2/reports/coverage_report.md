# Multisource V2 coverage and evidence report

Run UTC: 2026-09-13T02:50:19.307326+00:00
Campaign: `MROB-LIT-2026-09-12-V2`

## Scope

- Query executions planned: **22** across F1–F16 and configured date windows.
- V1 input candidates: **2226** (read-only input).
- V2 raw normalized records: **1225**.
- Reconciled derivative candidates: **3033**.
- Deep-evidence queue: **60**; this is not a claim that all queued works were read.
- V2 title/abstract metadata screening: **530 include**, **166 maybe**, **529 exclude**.
- Automatic repair rounds completed: **0**; maximum allowed by protocol: **1**.

## Source status

| Source | Tier | Status | Raw | Unique | New vs V1 | Errors | Credential/access note |
|---|---:|---|---:|---:|---:|---:|---|
| crossref | A | ok | 550 | 494 | 399 | 0 | public API attempted |
| openalex | A | ok | 494 | 430 | 338 | 0 | public API attempted |
| arxiv | A | network_blocked | 0 | 0 | 0 | 22 | public API attempted |
| semantic_scholar | A | partial | 50 | 48 | 26 | 20 | public API attempted |
| core | A | pending_credentials | 0 | 0 | 0 | 0 | CORE_API_KEY absent |
| openaire | A | ok | 97 | 95 | 75 | 0 | public API attempted |
| dblp | A | network_blocked | 0 | 0 | 0 | 22 | public API attempted |
| doaj | A | ok | 34 | 32 | 22 | 0 | public API attempted |
| unpaywall | B | ok_bounded | 500 | 500 | 0 | 0 | DOI enrichment; not a discovery source |
| opencitations | B | ok_bounded | 1789 | 1789 | 0 | 0 | bounded one-hop graph on V1 DOI anchors |
| google_scholar | manual | manual_pending | 0 | 0 | 0 | 0 | manual query/export pack generated; no automation |
| web_of_science | manual | manual_pending | 0 | 0 | 0 | 0 | manual query/export pack generated; no automation |
| scopus | manual | manual_pending | 0 | 0 | 0 | 0 | manual query/export pack generated; no automation |
| ieee_xplore | manual | manual_pending | 0 | 0 | 0 | 0 | manual query/export pack generated; no automation |

## Marginal yield

The sequential marginal column is descriptive: it depends on the configured source order and uses DOI when present, otherwise normalized title plus year. It is not an estimate of database recall.

| Source | Raw | Unique within source | New vs V1 | Marginal new after previous sources | Cumulative union incl. V1 |
|---|---:|---:|---:|---:|---:|
| crossref | 550 | 494 | 399 | 399 | 2625 |
| openalex | 494 | 430 | 338 | 328 | 2953 |
| arxiv | 0 | 0 | 0 | 0 | 2953 |
| semantic_scholar | 50 | 48 | 26 | 12 | 2965 |
| core | 0 | 0 | 0 | 0 | 2965 |
| openaire | 97 | 95 | 75 | 49 | 3014 |
| dblp | 0 | 0 | 0 | 0 | 3014 |
| doaj | 34 | 32 | 22 | 19 | 3033 |

## Evidence boundary

- Metadata discovery remains `evidence_status=not_evidence`; an OA URL is a retrieval lead only.
- Existing V1 full-text objects are labelled as eligible for close reading, while new V2 records remain pending legal acquisition and author verification.
- Google Scholar, WoS, Scopus and IEEE Xplore were not scraped or accessed automatically. Their packs are marked `manual_pending`.
- CORE was attempted only when `CORE_API_KEY` was available; otherwise its state is `pending_credentials`.
- A failed, empty or rate-limited API response is not interpreted as absence of literature.

## Interpretation

This campaign expands source diversity and auditability. It does not by itself establish saturation, novelty, convergence, optimality, mechanical feasibility or an integrated SP1–SP3 prior-art absence.
