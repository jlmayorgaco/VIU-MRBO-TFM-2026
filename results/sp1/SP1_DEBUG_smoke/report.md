# SP1_DEBUG_smoke

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2000`-`2002` (`n=3`)
- Scenario generators: `setup`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Summary

| Scenario | Method | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Runtime ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| setup | bnn_cardinality | 3 | 1.000 | 1.000 | 0.000 | 0.667 | 0.137 | 0.109 |
| setup | cbba | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.137 |
| setup | centralized_coalition_milp | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.065 |
| setup | greedy_nearest | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.070 |
| setup | hungarian_expanded | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.040 |
| setup | imitation_oracle | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.508 |
| setup | mappo_recruitment | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 3.419 |
| setup | oracle_reference | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.088 |
| setup | primal_dual_cardinality_capacity | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.215 |
| setup | primal_dual_wrench_market | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.189 |
| setup | replicator_cardinality | 3 | 1.000 | 1.000 | 0.000 | 0.667 | 0.137 | 0.124 |
| setup | smith_cardinality | 3 | 1.000 | 1.000 | 0.000 | 2.000 | 0.567 | 0.055 |

Best mean demand satisfaction: **cbba** on `setup`.

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/load_status.csv`
- `figures/sp1_demand_satisfaction_by_method.png`
- `figures/sp1_demand_ratio_interaction.png`
- `figures/sp1_representative_snapshot.png`
- `videos/sp1_representative_recruitment.mp4`
