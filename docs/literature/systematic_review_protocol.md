# Systematic literature review protocol draft

Version: 0.1  
Status: planning protocol, not yet registered  
Corpus source at this stage: local arXiv PDF corpus under `output/literature/arxiv_full`

## Working title

Distributed coordination, coalition formation, and cooperative transport in multi-robot systems: a systematic mapping review and focused systematic literature review.

## Review design

This project should use a two-layer design:

1. Systematic mapping review across the broad corpus.
2. Focused systematic literature review over papers that directly address the TFM problem.

The mapping review classifies the research landscape. The focused review supports the thesis argument and should only include papers that pass explicit eligibility criteria.

## Primary research questions

RQ1. What technical approaches have been proposed for distributed coordination and task allocation in multi-agent or multi-robot systems?

RQ2. Which approaches specifically support cooperative transport, payload manipulation, rigid formation, or coalition-based mobile robotics?

RQ3. How are graph theory, game theory, distributed optimization, networked control, and geometry/topology used as theoretical foundations for these systems?

RQ4. What evidence is reported for robustness, scalability, communication efficiency, real-world validity, and reproducibility?

## Focused TFM review question

For heterogeneous multi-AGV or mobile-robot teams performing cooperative transport under communication and resource constraints, what distributed coordination mechanisms combine allocation, coalition formation, formation/control geometry, and robustness guarantees?

## Eligibility criteria

In-scope papers should satisfy at least one core relevance condition:

- Multi-robot or multi-agent coordination with a robotics, control, planning, or networked-systems setting.
- Cooperative transport, cooperative manipulation, formation control, task allocation, coalition formation, MAPF, coverage, exploration, or warehouse/AGV fleet coordination.
- Mathematical foundation directly usable for the thesis: graph-theoretic consensus/connectivity, game theory, distributed optimization, distributed MPC, control barrier functions, rigid formation, topology, or networked control.

Out-of-scope papers:

- Pure biological, social, wireless, power-grid, or generic network papers with no transferable control/coordination method.
- Single-robot perception papers unless they materially support multi-robot coordination or transport.
- Papers without enough methodological detail to extract mechanism, assumptions, and validation.
- Non-English papers unless metadata clearly indicates high relevance and translation is feasible.

## Study types

Include:

- theoretical papers
- simulation studies
- real-robot experiments
- benchmarks
- surveys and tutorials, flagged separately from primary studies

Do not mix surveys with primary evidence during claims about performance. Use surveys for taxonomy and citation chasing.

## Information sources

Initial source:

- arXiv API corpus, downloaded locally with reproducible query topics.

Additional sources required before claiming PRISMA-grade systematic coverage:

- IEEE Xplore
- ACM Digital Library
- Scopus or Web of Science
- Google Scholar citation chasing
- key venue proceedings for ICRA, IROS, RSS, CDC, ACC, TAC, TRO, T-RO, RA-L

## Screening procedure

Stage 1. Automated deduplication by arXiv ID and title.

Stage 2. Title/abstract screening using the criteria in `screening_criteria.yaml`.

Stage 3. Full-text screening for borderline and high-priority papers.

Stage 4. Data extraction using `extraction_schema.yaml`.

Stage 5. Quality assessment using an engineering-oriented evidence rubric.

All exclusions after Stage 2 must keep a reason code.

## Synthesis plan

The main synthesis should be narrative and taxonomic, not a classical meta-analysis, unless a narrow subset shares comparable outcomes.

Planned outputs:

- PRISMA-style flow counts.
- Study characteristic matrix.
- Taxonomy of problem type, method family, theoretical foundation, and validation type.
- Evidence gap map.
- Tables for thesis LaTeX.
- Candidate bibliography with verification status.

## Quality assessment rubric

Assess each included paper on:

- relevance to the focused TFM question
- mathematical clarity
- distributed/decentralized validity
- realism of assumptions
- validation quality
- baseline comparisons
- reproducibility and code/data availability
- robustness/scalability evidence
- communication model clarity
- hardware or real-world evidence

## Registration note

If this review is submitted as a standalone systematic review, register the protocol in OSF before final screening. For the TFM, keep this protocol versioned in the repository and report deviations transparently.
