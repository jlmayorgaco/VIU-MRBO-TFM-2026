# SP1_MC_smoke

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2000`-`2002` (`n=3`)
- Scenario generators: `under_demand, balanced_demand, over_demand, monte_carlo`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Summary

| Scenario | Method | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Runtime ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| balanced_demand | centralized_coalition_milp | 12 | 0.889 | 1.000 | 0.000 | 0.000 | 0.000 | 0.185 |
| balanced_demand | greedy_nearest | 12 | 0.889 | 1.000 | 0.000 | 0.000 | 0.048 | 0.096 |
| balanced_demand | imitation_oracle | 12 | 0.750 | 0.938 | 0.417 | 0.000 | 0.223 | 0.604 |
| balanced_demand | mappo_recruitment | 12 | 0.889 | 1.000 | 0.000 | 0.000 | 0.001 | 2.782 |
| balanced_demand | oracle_reference | 12 | 0.889 | 1.000 | 0.000 | 0.000 | 0.000 | 0.178 |
| balanced_demand | primal_dual_cardinality_capacity | 12 | 0.861 | 1.000 | 0.000 | 0.000 | 0.158 | 0.542 |
| balanced_demand | primal_dual_wrench_market | 12 | 0.861 | 1.000 | 0.000 | 0.000 | 0.166 | 0.490 |
| monte_carlo | centralized_coalition_milp | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.000 | 0.281 |
| monte_carlo | greedy_nearest | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.005 | 0.101 |
| monte_carlo | imitation_oracle | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.004 | 0.582 |
| monte_carlo | mappo_recruitment | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.032 | 3.334 |
| monte_carlo | oracle_reference | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.000 | 0.332 |
| monte_carlo | primal_dual_cardinality_capacity | 3 | 0.800 | 0.933 | 1.000 | 0.000 | 0.194 | 0.583 |
| monte_carlo | primal_dual_wrench_market | 3 | 0.800 | 0.933 | 1.000 | 0.000 | 0.194 | 0.765 |
| over_demand | centralized_coalition_milp | 24 | 0.615 | 0.657 | 3.458 | 0.000 | 0.000 | 0.242 |
| over_demand | greedy_nearest | 24 | 0.469 | 0.721 | 2.750 | 0.000 | 0.443 | 0.093 |
| over_demand | imitation_oracle | 24 | 0.417 | 0.704 | 2.917 | 0.000 | 0.519 | 0.551 |
| over_demand | mappo_recruitment | 24 | 0.646 | 0.657 | 3.458 | 0.000 | 0.009 | 3.065 |
| over_demand | oracle_reference | 24 | 0.615 | 0.657 | 3.458 | 0.000 | 0.000 | 0.263 |
| over_demand | primal_dual_cardinality_capacity | 24 | 0.281 | 0.721 | 2.750 | 0.000 | 0.965 | 0.449 |
| over_demand | primal_dual_wrench_market | 24 | 0.271 | 0.721 | 2.750 | 0.000 | 1.005 | 0.435 |
| under_demand | centralized_coalition_milp | 24 | 0.903 | 1.000 | 0.000 | 0.000 | 0.000 | 0.167 |
| under_demand | greedy_nearest | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.057 | 0.086 |
| under_demand | imitation_oracle | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.052 | 0.500 |
| under_demand | mappo_recruitment | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.000 | 2.866 |
| under_demand | oracle_reference | 24 | 0.903 | 1.000 | 0.000 | 0.000 | 0.000 | 0.184 |
| under_demand | primal_dual_cardinality_capacity | 24 | 1.000 | 1.000 | 0.000 | 0.250 | 0.003 | 0.453 |
| under_demand | primal_dual_wrench_market | 24 | 1.000 | 1.000 | 0.000 | 0.250 | 0.003 | 0.439 |

Best mean demand satisfaction: **centralized_coalition_milp** on `balanced_demand`.

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/load_status.csv`
- `figures/sp1_demand_satisfaction_by_method.png`
- `figures/sp1_demand_ratio_interaction.png`
- `figures/sp1_representative_snapshot.png`
- `videos/sp1_representative_recruitment.mp4`
