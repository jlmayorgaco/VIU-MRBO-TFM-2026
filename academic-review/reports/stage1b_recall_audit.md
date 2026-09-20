# Stage 1B bounded recall audit

## Scope

The audit used **20** anchors selected to span the
methodological families represented in Stage 1A. It inspected one-hop backward
references and forward citing works through OpenAlex, bounded to 50 references
and 25 citing works per anchor. It did not perform unrestricted snowballing.

## Observed counts

- Stage 1A unique candidates: **376**
- New unique or unresolved records observed through recall: **957**
- New records classified `include_fulltext` or `maybe_fulltext`: **447**
- New records classified `exclude`: **510**
- Anchors with citation retrieval summaries: **37**
- API failures: **0**

## Interpretation

The bounded recall result is a diagnostic of missed candidates, not a recall
estimate. The result is classified as: **evidence of additional relevant literature; not near saturation under the descriptive diagnostic**. A citation link was
never used as an inclusion criterion; each candidate received the frozen
title/abstract protocol. The canonical corpus has no WoS coverage and cannot
be described as exhaustive.

## Query families and gaps

See `reports/search_concept_matrix.md`. The clearest canonical-query gaps are
population/evolutionary/potential-game terminology, collision avoidance/CBF,
docking/formation variants, and warehouse/intralogistics context terms. The
matrix proposes bounded follow-up queries, which were not executed in Stage 1B.

## Methodological families represented by anchors

- `coalition_or_allocation`: 9
- `distributed_coordination`: 11
- `fault_recovery`: 2
- `game_or_optimization`: 4
- `heterogeneous_teams`: 2

## Limitations

OpenAlex coverage and citation metadata are source-dependent; reference lists
can be incomplete, and the one-hop cap excludes multi-hop discovery. The result
must therefore be used to decide whether an additional query pilot is justified,
not to assert saturation or absence of literature.
