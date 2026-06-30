# MARL CTDE training

- Baseline: shared-parameter CTDE policy trained from full multi-robot episode returns.
- Execution: decentralized; each robot scores visible loads from local features.
- Best objective: 0.4065.
- Best capture: 0.4647.
- Runtime: 360.7 s.

| Feature | Weight |
|---|---:|
| bias | -0.168256 |
| reward | 0.693096 |
| price | -0.000676202 |
| deficit | 1.57831 |
| age | 0.275784 |
| closeness | 0.595844 |
| support | -0.134382 |
| transport | -0.534317 |
| stickiness | 0.53697 |
| quorum_pressure | 0.315334 |
| idle_score | 0.55475 |
