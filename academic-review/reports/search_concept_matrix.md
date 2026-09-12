# Stage 1B search-concept matrix

This matrix audits the 14 canonical executions (Q1–Q7 × Crossref/OpenAlex). It does not claim that an absent query term proves absent literature.

| Concept axis | Protocol terms/synonyms | Canonical query families | Candidate title/abstract signal | Coverage assessment |
|---|---|---|---:|---|
| multi-robot / multi-agent robotic systems | `multi-robot`, `multi robot`, `multi-agent`, `multi agent` | Q1_coalition_transport, Q2_sharedload_distributed, Q3_physical_certificate, Q4_recovery_replacement, Q5_heterogeneous_local, Q6_network_imperfect, Q7_counterexample_full_conjunction | 373 | Multi-robot is present; multi-agent is only partially represented. |
| AMR / AGV / mobile robots | `AMR`, `AGV`, `mobile robot` | Q1_coalition_transport, Q2_sharedload_distributed, Q3_physical_certificate, Q4_recovery_replacement, Q6_network_imperfect | 66 | AMR/AGV is concentrated in Q1; mobile robot appears more broadly. |
| cooperative transport / manipulation / object transport | `cooperative transport`, `object transport`, `payload`, `manipulation` | Q2_sharedload_distributed, Q3_physical_certificate, Q4_recovery_replacement, Q6_network_imperfect, Q7_counterexample_full_conjunction | 41 | Covered directly, with terminology variants requiring audit. |
| coalition formation / team formation / task allocation / MRTA | `coalition formation`, `team formation`, `task allocation`, `MRTA` | Q1_coalition_transport, Q5_heterogeneous_local, Q7_counterexample_full_conjunction | 214 | Covered directly; matching, assignment and service-composition synonyms are partial. |
| heterogeneous capabilities | `heterogeneous`, `multi-skilled`, `multi skilled` | Q5_heterogeneous_local, Q7_counterexample_full_conjunction | 73 | Covered in two conjunctions; skill/capability synonyms should be checked. |
| distributed / decentralized / local coordination | `distributed`, `decentralized`, `local`, `leaderless` | Q2_sharedload_distributed, Q4_recovery_replacement, Q5_heterogeneous_local, Q6_network_imperfect, Q7_counterexample_full_conjunction | 215 | Well represented in query families. |
| population / evolutionary / potential games | `population game`, `evolutionary game`, `potential game`, `replicator`, `logit` | none | 2 | Missing from canonical query text; only indirect game terminology is present in the seed/discovery corpus. |
| consensus / distributed optimization | `consensus`, `distributed optimization`, `decentralized optimization` | Q2_sharedload_distributed, Q6_network_imperfect | 65 | Consensus is present; distributed-optimization wording is incomplete. |
| physical feasibility | `wrench`, `force allocation`, `contact feasibility`, `grasp matrix`, `force closure`, `caging` | Q3_physical_certificate | 7 | Concentrated in Q3; support, rigidity and actuator synonyms are partial. |
| formation / docking / cooperative motion | `formation`, `docking`, `cooperative motion` | Q1_coalition_transport, Q2_sharedload_distributed | 99 | Formation is partial; docking is absent from canonical query text. |
| collision avoidance / safety / CBF | `collision avoidance`, `control barrier function`, `CBF`, `safety` | none | 11 | Missing from canonical query text; important for SP2/SP3 interface audit. |
| failures / replacement / reconfiguration | `fault`, `failure`, `recovery`, `replacement`, `reconfiguration` | Q4_recovery_replacement, Q7_counterexample_full_conjunction | 31 | Covered directly. |
| communication delay / packet loss / switching topology | `packet loss`, `delay`, `switching topology`, `event-triggered`, `communication constraints` | Q6_network_imperfect, Q7_counterexample_full_conjunction | 49 | Covered directly, including network variants. |
| warehouse / intralogistics / industrial logistics | `warehouse`, `intralogistics`, `industrial logistics`, `factory` | none | 11 | Missing from canonical query text; add as context terms rather than assume every Cartesian combination. |

## Candidate follow-up query families (not executed in Stage 1B)

The following bounded additions are justified as gap checks, not as an assumption that every combination is relevant:

- `Q8_game_dynamics`: `(population game OR evolutionary game OR potential game OR replicator OR logit) AND (multi-robot OR MRTA OR coalition)`.
- `Q9_safety_transport`: `(multi-robot OR mobile robot) AND (cooperative transport OR payload) AND (collision avoidance OR control barrier function OR CBF OR safety)`.
- `Q10_industrial_context`: `(multi-robot OR AMR OR AGV) AND (warehouse OR intralogistics OR industrial logistics OR factory) AND (transport OR task allocation OR coalition)`.
- `Q11_formation_docking`: `(multi-robot OR mobile robot) AND (formation OR docking OR cooperative motion) AND (transport OR payload)`.

These suggestions require review after the one-hop recall audit. They are not included in the Stage 1B search count.
