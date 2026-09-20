# Stage 2 full-text acquisition QA

Run UTC: 2026-09-13T22:46:57.596799+00:00

## Frozen inputs and access policy

- Stage 1C queue SHA-256: `37e6700972c0f625a8dc8bbea58914073d4031d27158cec495bf2ffb4c4146d4`
- Stage 1C corpus SHA-256: `2296f21702b01e20cb9e5fedccc744bc497f18a4e2c215060f542b6dc7ca783d`
- Stage 2 configuration SHA-256: `9850b6104b5916eef3dca0ab3c4921a311d96d3073535113ddae2acbdcfd03a2`
- Queue records processed: **1150**
- Access policy: **legal/open public routes only**; no credentials, proxy, paywall bypass, or robots restriction override.
- Metadata routes: OpenAlex OA locations and Crossref public links; DOI landing pages are not treated as OA routes.

## Acquisition statuses

- `abstract_only`: **123**
- `acquired_html`: **96**
- `acquired_pdf`: **148**
- `acquired_xml`: **0**
- `retrieval_error`: **21**
- `unavailable_legally`: **762**

Acquired objects are retained only when the candidate DOI or title is observed
in the extracted PDF/HTML/XML. Mismatched objects and objects without
extractable identity are not promoted to the local corpus.

## Identity and sources

- Identity statuses: `identity_verified_doi`=161, `identity_verified_title`=83, `not_applicable`=906
- Verified acquired objects: **244**
- Acquired file bytes: **444,582,094**
- Top final source hosts: `link.springer.com`=97, `arxiv.org`=26, `ieeexplore.ieee.org`=18, `xplorestaging.ieee.org`=10, `pmc.ncbi.nlm.nih.gov`=8, `www.frontiersin.org`=7, `hal.science`=5, `www.cambridge.org`=5, `www.roboticsproceedings.org`=4, `ojs.aaai.org`=3, `publications.ri.cmu.edu`=3, `journals.plos.org`=2
- API events: **112**; terminal API failures: **0**

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
