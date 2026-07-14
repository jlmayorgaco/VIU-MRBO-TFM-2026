# SP1_PROTOCOL_v1_DRY_RUN

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `910001`-`910002` (`n=2`)
- Scenario generators: `setup, monte_carlo`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| hungarian_expanded | Hungarian expanded | classic | centralized | baseline | hungarian_expanded | classic_centralized_baseline |
| greedy_nearest | Greedy nearest | classic | decentralized | baseline | nearest_greedy | classic_decentralized_baseline |
| cbba | CBBA-like auction | sota | decentralized | baseline | cbba_like_auction | sota_decentralized_baseline |
| smith_cardinality | Smith cardinality | model_based | decentralized | proposed | smith_qr_cardinality | proposed_model_based_variation |
| primal_dual_local_repair | Primal-dual local repair | model_based | decentralized_local | proposed | primal_dual_with_certified_local_repair | proposed_local_repair_family |
| centralized_coalition_milp | Centralized coalition oracle | model_based_oracle | centralized | reference | exact_binary_quorum_capacity_milp | centralized_oracle_reference |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_feasible_reference | centralized_oracle_reference |

## Resource Fairness

Interpret neural/data-driven methods as quality-resource tradeoffs, not as free replacements for compact distributed rules.

| Method | Training type | Execution model | Trainable params | Tuned params | Train episodes | Train seeds | Decoder |
|---|---|---|---:|---:|---:|---:|---|
| hungarian_expanded | none | centralized_hungarian_assignment | 0 | 0 | 0 | 0 | False |
| greedy_nearest | none | distributed_greedy_rule | 0 | 0 | 0 | 0 | False |
| cbba | none | distributed_auction_proxy | 0 | 2 | 0 | 0 | False |
| smith_cardinality | model_based_tuning_optional | distributed_smith_qr_rule | 0 | 3 | 0 | 0 | False |
| primal_dual_local_repair | model_based_tuning_optional | distributed_primal_dual_plus_certified_local_repair | 0 | 8 | 0 | 0 | False |
| centralized_coalition_milp | none | centralized_exact_binary_milp | 0 | 3 | 0 | 0 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 2 | 0 | 0 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| monte_carlo | cbba | sota | decentralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.020 | 42.78 | 213.92 | 0.424 |
| monte_carlo | centralized_coalition_milp | model_based_oracle | centralized | reference | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 41.07 | 205.36 | 1.446 |
| monte_carlo | greedy_nearest | classic | decentralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.134 | 48.74 | 243.72 | 0.091 |
| monte_carlo | hungarian_expanded | classic | centralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 41.07 | 205.36 | 0.062 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 41.07 | 205.36 | 1.705 |
| monte_carlo | primal_dual_local_repair | model_based | decentralized_local | proposed | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.029 | 43.57 | 217.86 | 12.852 |
| monte_carlo | smith_cardinality | model_based | decentralized | proposed | 2 | 0.583 | 0.722 | 2.000 | 4.000 | 0.881 | 50.29 | 251.44 | 0.117 |
| setup | cbba | sota | decentralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 0.156 |
| setup | centralized_coalition_milp | model_based_oracle | centralized | reference | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 1.511 |
| setup | greedy_nearest | classic | decentralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 0.077 |
| setup | hungarian_expanded | classic | centralized | baseline | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 0.063 |
| setup | oracle_reference | model_based_oracle | centralized | reference | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 2.673 |
| setup | primal_dual_local_repair | model_based | decentralized_local | proposed | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 5.89 | 29.47 | 0.453 |
| setup | smith_cardinality | model_based | decentralized | proposed | 2 | 1.000 | 1.000 | 0.000 | 2.000 | 0.370 | 16.28 | 81.38 | 0.053 |

Best raw mean demand satisfaction: **centralized_coalition_milp** on `monte_carlo`.

## Performance Ranking

Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.

Theory-aligned best overall: **hungarian_expanded** (`baseline`).

| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| ALL_SCENARIOS | 1 | hungarian_expanded | classic | baseline | 1.000 | 1.000 | 0.000 | 23.48 | 0 | 0.062 |
| ALL_SCENARIOS | 2 | centralized_coalition_milp | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 23.48 | 0 | 1.478 |
| ALL_SCENARIOS | 3 | oracle_reference | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 23.48 | 0 | 2.189 |
| ALL_SCENARIOS | 4 | cbba | sota | baseline | 1.000 | 1.000 | 0.010 | 24.34 | 0 | 0.290 |
| ALL_SCENARIOS | 5 | primal_dual_local_repair | model_based | proposed | 1.000 | 1.000 | 0.015 | 24.73 | 0 | 6.653 |
| ALL_SCENARIOS | 6 | greedy_nearest | classic | baseline | 1.000 | 1.000 | 0.067 | 27.32 | 0 | 0.084 |
| ALL_SCENARIOS | 7 | smith_cardinality | model_based | proposed | 0.861 | 0.792 | 0.626 | 33.28 | 0 | 0.085 |

## Theory Audit

- Checks: `28`.
- Failed checks: `0`.
- Strict complete-coalition failures: `0`.
- Passed: `True`.

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/load_status.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `theory_audit.json`
- `figures/sp1_demand_satisfaction_by_method.png`
- `figures/sp1_demand_ratio_interaction.png`
- `figures/sp1_performance_matrix_by_method.png`
- `figures/sp1_taxonomy_scope_family_ownership.png`
- `figures/sp1_ours_vs_baselines_vs_reference.png`
- `figures/sp1_reference_gap_proposed_methods.png`
- `figures/sp1_communication_radius_degradation.png`
- `figures/sp1_best_method_by_scenario.png`
- `figures/sp1_quality_resource_pareto.png`
- `figures/sp1_physical_cost_tradeoff.png`
- `figures/sp1_<scenario>_<selection>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.png`
- `videos/sp1_<scenario>_<selection>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`
