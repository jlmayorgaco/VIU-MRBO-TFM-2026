# Wrench-capacity gate G3

This gate tests the failure mode where a scalar quorum accepts a coalition
that cannot generate the demanded physical wrench.

- Force bound per robot: `1`
- Feasibility tolerance: `1e-08`

| Case | Contacts | Cardinality | Rank | Wrench feasible | Residual | Achieved wrench |
|---|---:|---|---:|---|---:|---:|
| cardinality_only_same_face | 3 | True | 2 | False | 1.19904 | (-0.0479, 0, 0.00192) |
| effective_wrench_distributed | 4 | True | 3 | True | 2.54384e-16 | (1.11e-16, -5.55e-17, 1.2) |

Acceptance criterion: the same-face case must be a cardinality pass and a
wrench failure; the distributed case must be feasible with full planar rank.
