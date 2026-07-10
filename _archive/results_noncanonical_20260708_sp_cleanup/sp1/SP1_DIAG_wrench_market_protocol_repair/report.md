# SP1_DIAG_wrench_market_protocol_repair

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2400`-`2419` (`n=20`)
- Scenario generators: `under_demand, balanced_demand, over_demand, monte_carlo`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| greedy_nearest | Greedy nearest | classic | decentralized | baseline | nearest_greedy | classic_decentralized_baseline |
| bnn_cardinality | BNN cardinality | model_based | decentralized | baseline | bnn_cardinality | model_based_decentralized_baseline |
| replicator_cardinality | Replicator cardinality | model_based | decentralized | baseline | population_game_replicator | model_based_decentralized_baseline |
| cbba | CBBA-like auction | sota | decentralized | baseline | cbba_like_auction | sota_decentralized_baseline |
| bnn_cardinality_repair | Brown/BNN cardinality local repair | model_based | decentralized | proposed | brown_bnn_positive_excess_with_local_repair | proposed_local_repair_family |
| logit_cardinality_repair | Logit cardinality local repair | model_based | decentralized | proposed | logit_quorum_flow_with_local_repair | proposed_local_repair_family |
| replicator_cardinality_repair | Replicator cardinality local repair | model_based | decentralized | proposed | replicator_with_certified_local_repair | proposed_local_repair_family |
| smith_cardinality | Smith cardinality | model_based | decentralized | proposed | smith_qr_cardinality | proposed_model_based_variation |
| primal_dual_local_repair | Primal-dual local repair | model_based | decentralized_local | proposed | primal_dual_with_certified_local_repair | proposed_local_repair_family |
| tensor_quorum_flow_repair | Smooth tensor quorum-flow repair | model_based | decentralized_local | proposed | smooth_tensor_quorum_flow_with_repair | proposed_local_repair_family |
| centralized_coalition_milp | Centralized coalition oracle | model_based_oracle | centralized | reference | exact_capacity_feasible_coalition | centralized_oracle_reference |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_feasible_reference | centralized_oracle_reference |

## Resource Fairness

Interpret neural/data-driven methods as quality-resource tradeoffs, not as free replacements for compact distributed rules.

| Method | Training type | Execution model | Trainable params | Tuned params | Train episodes | Train seeds | Decoder |
|---|---|---|---:|---:|---:|---:|---|
| greedy_nearest | none | distributed_greedy_rule | 0 | 0 | 0 | 0 | False |
| bnn_cardinality | model_based_tuning_optional | distributed_nonlinear_utility_rule | 0 | 5 | 0 | 0 | False |
| replicator_cardinality | model_based_tuning_optional | distributed_utility_rule | 0 | 4 | 0 | 0 | False |
| cbba | none | distributed_auction_proxy | 0 | 2 | 0 | 0 | False |
| bnn_cardinality_repair | model_based_tuning_optional | distributed_brown_bnn_positive_excess_plus_local_repair | 0 | 8 | 0 | 0 | False |
| logit_cardinality_repair | model_based_tuning_optional | distributed_logit_quorum_flow_plus_local_repair | 0 | 8 | 0 | 0 | False |
| replicator_cardinality_repair | model_based_tuning_optional | distributed_replicator_plus_local_exact_repair | 0 | 7 | 0 | 0 | False |
| smith_cardinality | model_based_tuning_optional | distributed_smith_qr_rule | 0 | 3 | 0 | 0 | False |
| primal_dual_local_repair | model_based_tuning_optional | distributed_primal_dual_plus_certified_local_repair | 0 | 8 | 0 | 0 | False |
| tensor_quorum_flow_repair | model_based_tuning_optional | smooth_tensor_quorum_flow_plus_certified_local_repair | 0 | 9 | 0 | 0 | False |
| centralized_coalition_milp | none | centralized_exact_subset_slot_search | 0 | 2 | 0 | 0 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 2 | 0 | 0 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_demand | bnn_cardinality | model_based | decentralized | baseline | 80 | 0.671 | 0.896 | 0.713 | 0.275 | 0.419 | 37.95 | 189.74 | 0.133 |
| balanced_demand | bnn_cardinality_repair | model_based | decentralized | proposed | 80 | 0.908 | 0.915 | 0.600 | 0.025 | 0.051 | 41.11 | 205.53 | 2.226 |
| balanced_demand | cbba | sota | decentralized | baseline | 80 | 0.850 | 1.000 | 0.000 | 0.000 | 0.199 | 43.48 | 217.38 | 0.346 |
| balanced_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 80 | 0.887 | 0.919 | 0.562 | 0.263 | 0.000 | 39.86 | 199.29 | 1.081 |
| balanced_demand | greedy_nearest | classic | decentralized | baseline | 80 | 0.850 | 1.000 | 0.000 | 0.000 | 0.225 | 43.99 | 219.95 | 0.107 |
| balanced_demand | logit_cardinality_repair | model_based | decentralized | proposed | 80 | 0.900 | 0.900 | 0.700 | 0.025 | 0.067 | 41.07 | 205.37 | 1.875 |
| balanced_demand | oracle_reference | model_based_oracle | centralized | reference | 80 | 0.887 | 0.919 | 0.562 | 0.263 | 0.000 | 39.86 | 199.29 | 1.148 |
| balanced_demand | primal_dual_local_repair | model_based | decentralized_local | proposed | 80 | 0.896 | 0.901 | 0.688 | 0.037 | 0.048 | 40.28 | 201.38 | 1.835 |
| balanced_demand | replicator_cardinality | model_based | decentralized | baseline | 80 | 0.588 | 0.849 | 1.038 | 0.338 | 0.509 | 33.54 | 167.68 | 0.138 |
| balanced_demand | replicator_cardinality_repair | model_based | decentralized | proposed | 80 | 0.908 | 0.912 | 0.613 | 0.037 | 0.047 | 40.71 | 203.56 | 2.756 |
| balanced_demand | smith_cardinality | model_based | decentralized | proposed | 80 | 0.529 | 0.678 | 2.225 | 1.950 | 0.597 | 32.86 | 164.28 | 0.126 |
| balanced_demand | tensor_quorum_flow_repair | model_based | decentralized_local | proposed | 80 | 0.892 | 0.901 | 0.688 | 0.037 | 0.050 | 39.91 | 199.56 | 1.717 |
| monte_carlo | bnn_cardinality | model_based | decentralized | baseline | 20 | 0.552 | 0.799 | 1.800 | 1.800 | 0.654 | 46.81 | 234.03 | 0.137 |
| monte_carlo | bnn_cardinality_repair | model_based | decentralized | proposed | 20 | 0.845 | 0.825 | 1.750 | 0.150 | 0.050 | 35.35 | 176.74 | 7.750 |
| monte_carlo | cbba | sota | decentralized | baseline | 20 | 0.727 | 0.892 | 1.100 | 0.000 | 0.282 | 37.41 | 187.05 | 0.439 |
| monte_carlo | centralized_coalition_milp | model_based_oracle | centralized | reference | 20 | 0.878 | 0.868 | 1.350 | 0.250 | 0.000 | 37.32 | 186.62 | 6.545 |
| monte_carlo | greedy_nearest | classic | decentralized | baseline | 20 | 0.757 | 0.892 | 1.100 | 0.000 | 0.229 | 38.47 | 192.36 | 0.108 |
| monte_carlo | logit_cardinality_repair | model_based | decentralized | proposed | 20 | 0.845 | 0.825 | 1.750 | 0.150 | 0.051 | 35.57 | 177.86 | 7.392 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 20 | 0.878 | 0.868 | 1.350 | 0.250 | 0.000 | 37.32 | 186.62 | 6.617 |
| monte_carlo | primal_dual_local_repair | model_based | decentralized_local | proposed | 20 | 0.845 | 0.829 | 1.700 | 0.050 | 0.048 | 35.78 | 178.90 | 9.503 |
| monte_carlo | replicator_cardinality | model_based | decentralized | baseline | 20 | 0.537 | 0.775 | 2.050 | 1.900 | 0.614 | 44.45 | 222.23 | 0.145 |
| monte_carlo | replicator_cardinality_repair | model_based | decentralized | proposed | 20 | 0.845 | 0.830 | 1.700 | 0.150 | 0.056 | 36.60 | 182.99 | 7.751 |
| monte_carlo | smith_cardinality | model_based | decentralized | proposed | 20 | 0.557 | 0.655 | 3.050 | 3.550 | 0.642 | 48.40 | 242.00 | 0.140 |
| monte_carlo | tensor_quorum_flow_repair | model_based | decentralized_local | proposed | 20 | 0.845 | 0.829 | 1.700 | 0.050 | 0.049 | 35.91 | 179.54 | 9.143 |
| over_demand | bnn_cardinality | model_based | decentralized | baseline | 160 | 0.281 | 0.706 | 2.875 | 0.050 | 0.956 | 37.87 | 189.36 | 0.122 |
| over_demand | bnn_cardinality_repair | model_based | decentralized | proposed | 160 | 0.637 | 0.623 | 3.756 | 0.087 | 0.117 | 35.87 | 179.33 | 4.922 |
| over_demand | cbba | sota | decentralized | baseline | 160 | 0.423 | 0.721 | 2.750 | 0.000 | 0.599 | 34.72 | 173.59 | 0.344 |
| over_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 160 | 0.659 | 0.638 | 3.625 | 0.175 | 0.000 | 33.06 | 165.32 | 1.879 |
| over_demand | greedy_nearest | classic | decentralized | baseline | 160 | 0.478 | 0.721 | 2.750 | 0.000 | 0.496 | 34.80 | 173.99 | 0.110 |
| over_demand | logit_cardinality_repair | model_based | decentralized | proposed | 160 | 0.631 | 0.627 | 3.719 | 0.081 | 0.126 | 36.44 | 182.22 | 4.772 |
| over_demand | oracle_reference | model_based_oracle | centralized | reference | 160 | 0.659 | 0.638 | 3.625 | 0.175 | 0.000 | 33.06 | 165.32 | 1.984 |
| over_demand | primal_dual_local_repair | model_based | decentralized_local | proposed | 160 | 0.641 | 0.618 | 3.794 | 0.069 | 0.102 | 34.13 | 170.63 | 6.027 |
| over_demand | replicator_cardinality | model_based | decentralized | baseline | 160 | 0.291 | 0.689 | 3.031 | 0.094 | 0.886 | 34.73 | 173.63 | 0.135 |
| over_demand | replicator_cardinality_repair | model_based | decentralized | proposed | 160 | 0.642 | 0.618 | 3.794 | 0.075 | 0.099 | 34.43 | 172.15 | 4.336 |
| over_demand | smith_cardinality | model_based | decentralized | proposed | 160 | 0.398 | 0.570 | 4.150 | 1.300 | 0.597 | 29.59 | 147.95 | 0.141 |
| over_demand | tensor_quorum_flow_repair | model_based | decentralized_local | proposed | 160 | 0.648 | 0.623 | 3.750 | 0.062 | 0.095 | 34.72 | 173.60 | 6.231 |
| under_demand | bnn_cardinality | model_based | decentralized | baseline | 160 | 0.856 | 0.967 | 0.150 | 1.094 | 0.234 | 24.60 | 123.02 | 0.129 |
| under_demand | bnn_cardinality_repair | model_based | decentralized | proposed | 160 | 1.000 | 1.000 | 0.000 | 0.056 | 0.022 | 21.98 | 109.92 | 2.662 |
| under_demand | cbba | sota | decentralized | baseline | 160 | 0.856 | 1.000 | 0.000 | 0.000 | 0.163 | 19.00 | 94.99 | 0.295 |
| under_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 160 | 1.000 | 1.000 | 0.000 | 0.419 | 0.000 | 21.51 | 107.54 | 2.600 |
| under_demand | greedy_nearest | classic | decentralized | baseline | 160 | 0.852 | 1.000 | 0.000 | 0.000 | 0.199 | 20.93 | 104.63 | 0.104 |
| under_demand | logit_cardinality_repair | model_based | decentralized | proposed | 160 | 1.000 | 1.000 | 0.000 | 0.069 | 0.023 | 22.20 | 111.00 | 3.238 |
| under_demand | oracle_reference | model_based_oracle | centralized | reference | 160 | 1.000 | 1.000 | 0.000 | 0.419 | 0.000 | 21.51 | 107.54 | 2.613 |
| under_demand | primal_dual_local_repair | model_based | decentralized_local | proposed | 160 | 1.000 | 1.000 | 0.000 | 0.100 | 0.011 | 21.17 | 105.87 | 2.200 |
| under_demand | replicator_cardinality | model_based | decentralized | baseline | 160 | 0.812 | 0.930 | 0.300 | 1.206 | 0.270 | 23.08 | 115.40 | 0.139 |
| under_demand | replicator_cardinality_repair | model_based | decentralized | proposed | 160 | 1.000 | 1.000 | 0.000 | 0.069 | 0.018 | 21.66 | 108.30 | 2.853 |
| under_demand | smith_cardinality | model_based | decentralized | proposed | 160 | 0.756 | 0.815 | 0.812 | 3.294 | 0.515 | 33.04 | 165.18 | 0.121 |
| under_demand | tensor_quorum_flow_repair | model_based | decentralized_local | proposed | 160 | 1.000 | 1.000 | 0.000 | 0.106 | 0.012 | 21.23 | 106.17 | 2.119 |

Best raw mean demand satisfaction: **centralized_coalition_milp** on `under_demand`.

## Performance Ranking

Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.

Theory-aligned best overall: **centralized_coalition_milp** (`reference`).

| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| ALL_SCENARIOS | 1 | centralized_coalition_milp | model_based_oracle | reference | 0.840 | 0.843 | 0.000 | 30.16 | 0 | 2.224 |
| ALL_SCENARIOS | 2 | oracle_reference | model_based_oracle | reference | 0.840 | 0.843 | 0.000 | 30.16 | 0 | 2.285 |
| ALL_SCENARIOS | 3 | tensor_quorum_flow_repair | model_based | proposed | 0.829 | 0.838 | 0.052 | 30.63 | 0 | 3.943 |
| ALL_SCENARIOS | 4 | primal_dual_local_repair | model_based | proposed | 0.828 | 0.836 | 0.054 | 30.44 | 0 | 3.936 |
| ALL_SCENARIOS | 5 | replicator_cardinality_repair | model_based | proposed | 0.830 | 0.839 | 0.056 | 30.86 | 0 | 3.633 |
| ALL_SCENARIOS | 6 | bnn_cardinality_repair | model_based | proposed | 0.832 | 0.837 | 0.065 | 31.55 | 0 | 3.682 |
| ALL_SCENARIOS | 7 | logit_cardinality_repair | model_based | proposed | 0.830 | 0.833 | 0.072 | 31.86 | 0 | 3.761 |
| ALL_SCENARIOS | 8 | greedy_nearest | classic | baseline | 0.889 | 0.705 | 0.319 | 31.44 | 0 | 0.107 |

## Theory Audit

- Checks: `5040`.
- Failed checks: `0`.
- Strict complete-coalition failures: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H_DIAG_SP1_repair_lower_gap_than_replicator | optimality_gap_vs_oracle | 420 | 1.322e-69 | 2.645e-69 | -0.5103 | [-0.5513, -0.4693] | True | ok |
| H_DIAG_SP1_tensor_repair_lower_gap_than_cbba | optimality_gap_vs_oracle | 420 | 4.288e-38 | 4.288e-38 | -0.2893 | [-0.3267, -0.2526] | True | ok |

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
