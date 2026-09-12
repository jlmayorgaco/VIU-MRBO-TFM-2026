# Stage 2 full-text acquisition QA

Run UTC: 2026-09-12T22:13:27.033800+00:00

## Frozen inputs and access policy

- Stage 1C queue SHA-256: `e61c7187d2434bbbe13599f8b6392a8693c01414b9e40f335de65685cc3e3ae8`
- Stage 1C corpus SHA-256: `02ebed7559b0749783c8610f5399ed9733aa198c213aa2a76d5748ba01adc4d8`
- Stage 2 configuration SHA-256: `9850b6104b5916eef3dca0ab3c4921a311d96d3073535113ddae2acbdcfd03a2`
- Queue records processed: **1057**
- Access policy: **legal/open public routes only**; no credentials, proxy, paywall bypass, or robots restriction override.
- Metadata routes: OpenAlex OA locations and Crossref public links; DOI landing pages are not treated as OA routes.

## Acquisition statuses

- `abstract_only`: **30**
- `acquired_html`: **86**
- `acquired_pdf`: **144**
- `acquired_xml`: **0**
- `retrieval_error`: **21**
- `unavailable_legally`: **776**

Acquired objects are retained only when the candidate DOI or title is observed
in the extracted PDF/HTML/XML. Mismatched objects and objects without
extractable identity are not promoted to the local corpus.

## Identity and sources

- Identity statuses: `identity_verified_doi`=149, `identity_verified_title`=81, `not_applicable`=827
- Verified acquired objects: **230**
- Acquired file bytes: **422,905,524**
- Top final source hosts: `link.springer.com`=88, `arxiv.org`=26, `ieeexplore.ieee.org`=19, `pmc.ncbi.nlm.nih.gov`=8, `xplorestaging.ieee.org`=7, `www.frontiersin.org`=6, `hal.science`=5, `www.cambridge.org`=5, `www.roboticsproceedings.org`=4, `ojs.aaai.org`=3, `publications.ri.cmu.edu`=3, `www.nature.com`=2
- API events: **9**; terminal API failures: **0**

## Validation

- Every queue record has exactly one status from the configured six-status vocabulary.
- Every promoted file has a SHA-256, byte size, local path and verified identity status.
- Candidate-level acquisition log and a replay-safe attempt-level log are generated; resumed candidates retain their prior details in manifests.
- Stage 1C inputs are frozen and were not overwritten.

## Limitations

Open-access discovery depends on the locations exposed by public metadata
services and on the availability of those public URLs at run time. A status of
`abstract_only` or `unavailable_legally` is not evidence that a paper has no
full text anywhere; it records only that this run did not verify a legal public
route. Retrieval errors remain operational failures and are not silently
converted into scientific evidence.
