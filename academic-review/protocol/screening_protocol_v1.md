# Screening protocol v1 — Stage 1B

**Status:** frozen before automated screening  
**Scope:** title/abstract screening of the Stage 1A corpus plus candidates
discovered in the bounded recall audit  
**Evidence boundary:** screening is a retrieval decision, not scientific
evidence coding.

## 1. Objective

Reduce the candidate corpus to records that require legal full-text review for
at least one part of the TFM problem: multi-robot allocation or coalition/team
formation, distributed/local coordination, cooperative transport/manipulation,
heterogeneous capabilities, physical feasibility/contact/wrench, robustness or
communication constraints, or applicable game-theoretic/distributed
optimization mechanisms.

Web of Science is not available in this stage. The coverage label remains
`open_sources_plus_limited_snowballing`; the process is not exhaustive.

## 2. Evidence and missing-data rules

- Use the candidate title, abstract when present, document type, venue, authors,
  year and provenance.
- A missing abstract is not evidence of irrelevance and must not be filled by
  a model-generated guess.
- A title may justify a retrieval decision when its topical signal is explicit;
  it never proves a method, result, physical validation or guarantee.
- Citation count, venue prestige, previous-review membership and keyword
  presence alone cannot justify inclusion.
- Ambiguous records go to `maybe_fulltext` unless a clear exclusion rule applies.
- All candidates retain provenance and remain `not_evidence` at this stage.

## 3. Decisions

Each record receives exactly one `screening_decision`:

| Decision | Operational meaning |
|---|---|
| `include_fulltext` | Title/abstract metadata contains an explicit direct connection to the TFM scope, strong enough to justify retrieving the full text. |
| `maybe_fulltext` | The connection is plausible but incomplete, generic, metadata-limited or requires full-text inspection. |
| `exclude` | The available metadata gives a clear reason that the record is outside scope or is not a research item. |

An exclusion must use one approved `exclusion_reason`:

```text
out_of_domain
wrong_robotic_problem
no_multi_robot_component
no_relevant_coordination
non_research_item
duplicate
insufficient_metadata
other
```

## 4. Inclusion scope

An explicit signal in the title or abstract must connect a robotic system to at
least one of these axes:

1. multi-robot task allocation, coalition formation, team formation or MRTA;
2. distributed, decentralized, leaderless, local or neighbor-based
   coordination of multiple robots;
3. cooperative transport, object transport or cooperative manipulation by
   mobile/multiple robots;
4. heterogeneous, multi-skilled or capability-aware robot teams;
5. formation, docking, contact, grasp, force, wrench or physical feasibility
   for multiple robots or a transported object;
6. fault, failure, recovery, replacement, reconfiguration or constrained
   communication in a relevant multi-robot operation;
7. game-theoretic, population-game, evolutionary, potential-game, auction,
   consensus or distributed-optimization mechanisms applied to a relevant
   multi-robot problem.

Strong direct title signals may receive `include_fulltext` without an abstract
when the title itself identifies both the relevant robotic setting and the
problem axis. A generic title or a title whose relevance depends on an unseen
abstract receives `maybe_fulltext`.

## 5. Exclusion rules

Exclude only when the available metadata supports one of the following:

- clearly unrelated domains such as wireless sensor networks, 5G/IoT, edge
  computing, generic CPS security, missiles, traffic-only sensing or other
  non-robotic applications;
- a robotic problem with no multi-robot component and no transferable
  coordination/transport relevance;
- generic path planning, localization, tracking or control with no relevant
  multi-robot coordination axis;
- social/economic coalition theory without a transferable robotic or
  distributed-optimization method;
- generic swarm/animal/vehicular work without a relevant robot-team mechanism;
- standards, indexes, tables of contents, technical programs, tool listings,
  front matter or other non-research items;
- a duplicate removed by a documented identity merge.

Do not exclude solely because the record is a survey, is old, lacks an abstract,
has low citation count, comes from a repository, or is not published in a
preferred venue. Such records may be `include_fulltext` or `maybe_fulltext`
depending on the available topical signal.

## 6. Preliminary discovery taxonomy

For `include_fulltext` and `maybe_fulltext`, assign only tags supported by
literal title/abstract metadata. Each field may contain multiple semicolon-
separated values or `unclear`:

```text
problem_family
method_family
coordination_architecture
robot_type
heterogeneity
coalition_or_team
physical_transport
contact_or_wrench
local_communication
robustness_or_failures
industrial_context
theoretical_guarantees_claimed
experimental_platform
```

These are preliminary discovery tags. They are not final codebook values and
must not be used as verified evidence or as claims in the memory.

## 7. Identity and legacy rules

Identity resolution precedes screening. Use DOI first, then publisher or
registry metadata, normalized title, authors, year and venue. Merge only when
the identity is sufficiently supported. Preserve aliases, all provenance and
the resolution method. Distinct editions or preprint/published versions are
linked explicitly; unresolved cases retain both records and use
`duplicate_status=unresolved`.

For each legacy seed report its matched candidate, method, metadata status,
DOI, corrected bibliographic values and one of `verified`, `corrected`,
`unresolved` or `not_found`. Legacy provenance never implies inclusion.

## 8. Quality control

The screening output must satisfy:

- no `exclude` record also has `include_fulltext` or `maybe_fulltext`;
- every exclusion has an approved reason and a concise human-auditable note;
- every row has non-empty provenance;
- DOI uniqueness is checked after identity resolution;
- no legacy seed receives automatic inclusion because of its seed status;
- no abstract-derived tag is labelled verified evidence.

At least 20 included and 20 excluded records are manually audited, plus every
`maybe_fulltext` record when manageable. Manual audit results, corrections and
disagreements are recorded in the screening log. A single-reviewer audit is
reported as correction/disagreement with the deterministic pass; it is not
reported as inter-reviewer agreement.
