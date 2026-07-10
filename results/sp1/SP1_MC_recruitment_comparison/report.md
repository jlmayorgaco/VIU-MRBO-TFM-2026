# SP1_MC_recruitment_comparison

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2000`-`2099` (`n=100`)
- Scenario generators: `under_demand, balanced_demand, over_demand, monte_carlo`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| hungarian_expanded | Hungarian expanded | classic | centralized | baseline | hungarian_expanded | classic_centralized_baseline |
| greedy_nearest | Greedy nearest | classic | decentralized | baseline | nearest_greedy | classic_decentralized_baseline |
| imitation_oracle | Data-driven imitation oracle | data_driven | decentralized | baseline | oracle_imitation_linear | data_driven_baseline |
| bnn_cardinality | BNN cardinality | model_based | decentralized | baseline | bnn_cardinality | model_based_decentralized_baseline |
| replicator_cardinality | Replicator cardinality | model_based | decentralized | baseline | population_game_replicator | model_based_decentralized_baseline |
| cbba | CBBA-like auction | sota | decentralized | baseline | cbba_like_auction | sota_decentralized_baseline |
| mappo_recruitment | MAPPO recruitment checkpoint | data_driven | decentralized | proposed | mappo_ctde_quorum_decoder | proposed_data_driven_variation |
| primal_dual_cardinality_capacity | Primal-dual cardinality capacity | model_based | decentralized | proposed | primal_dual_capacity | proposed_model_based_variation |
| primal_dual_wrench_market | Primal-dual wrench market | model_based | decentralized | proposed | primal_dual_wrench_proxy | proposed_model_based_variation |
| smith_cardinality | Smith cardinality | model_based | decentralized | proposed | smith_qr_cardinality | proposed_model_based_variation |
| local_primal_dual_wrench_market | Local primal-dual wrench market | model_based | decentralized_local | proposed | local_primal_dual_wrench_proxy | proposed_local_variation |
| centralized_coalition_milp | Centralized coalition oracle | model_based_oracle | centralized | reference | exact_capacity_feasible_coalition | centralized_oracle_reference |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_feasible_reference | centralized_oracle_reference |

## Resource Fairness

Interpret neural/data-driven methods as quality-resource tradeoffs, not as free replacements for compact distributed rules.

| Method | Training type | Execution model | Trainable params | Tuned params | Train episodes | Train seeds | Decoder |
|---|---|---|---:|---:|---:|---:|---|
| hungarian_expanded | none | centralized_hungarian_assignment | 0 | 0 | 0 | 0 | False |
| greedy_nearest | none | distributed_greedy_rule | 0 | 0 | 0 | 0 | False |
| imitation_oracle | supervised_oracle_imitation | distributed_linear_score_policy | 7 | 1 | 0 | 1000 | False |
| bnn_cardinality | model_based_tuning_optional | distributed_nonlinear_utility_rule | 0 | 5 | 0 | 0 | False |
| replicator_cardinality | model_based_tuning_optional | distributed_utility_rule | 0 | 4 | 0 | 0 | False |
| cbba | none | distributed_auction_proxy | 0 | 2 | 0 | 0 | False |
| mappo_recruitment | ctde_ppo_with_bc_warm_start | decentralized_neural_actor_with_quorum_decoder | 4674 | 12 | 768 | 1000 | True |
| primal_dual_cardinality_capacity | model_based_tuning_optional | distributed_primal_dual_capacity_rule | 0 | 4 | 0 | 0 | False |
| primal_dual_wrench_market | model_based_tuning_optional | distributed_primal_dual_wrench_rule | 0 | 5 | 0 | 0 | False |
| smith_cardinality | model_based_tuning_optional | distributed_smith_qr_rule | 0 | 3 | 0 | 0 | False |
| local_primal_dual_wrench_market | model_based_tuning_optional | local_primal_dual_wrench_rule | 0 | 5 | 0 | 0 | False |
| centralized_coalition_milp | none | centralized_exact_subset_slot_search | 0 | 2 | 0 | 0 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 2 | 0 | 0 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_demand | bnn_cardinality | model_based | decentralized | baseline | 400 | 0.683 | 0.894 | 0.713 | 0.240 | 0.408 | 37.09 | 185.45 | 0.157 |
| balanced_demand | cbba | sota | decentralized | baseline | 400 | 0.873 | 1.000 | 0.000 | 0.000 | 0.185 | 42.73 | 213.65 | 0.430 |
| balanced_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 400 | 0.900 | 0.930 | 0.492 | 0.225 | 0.000 | 39.15 | 195.76 | 1.346 |
| balanced_demand | greedy_nearest | classic | decentralized | baseline | 400 | 0.877 | 1.000 | 0.000 | 0.000 | 0.182 | 43.12 | 215.58 | 0.131 |
| balanced_demand | hungarian_expanded | classic | centralized | baseline | 400 | 0.872 | 1.000 | 0.000 | 0.000 | 0.152 | 40.73 | 203.66 | 0.065 |
| balanced_demand | imitation_oracle | data_driven | decentralized | baseline | 400 | 0.724 | 0.917 | 0.560 | 0.000 | 0.319 | 34.54 | 172.69 | 0.683 |
| balanced_demand | local_primal_dual_wrench_market | model_based | decentralized_local | proposed | 400 | 0.876 | 0.999 | 0.007 | 0.007 | 0.187 | 42.82 | 214.11 | 0.640 |
| balanced_demand | mappo_recruitment | data_driven | decentralized | proposed | 400 | 0.898 | 0.929 | 0.500 | 0.225 | 0.010 | 39.18 | 195.92 | 8.066 |
| balanced_demand | oracle_reference | model_based_oracle | centralized | reference | 400 | 0.900 | 0.930 | 0.492 | 0.225 | 0.000 | 39.15 | 195.76 | 1.415 |
| balanced_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 400 | 0.869 | 0.994 | 0.040 | 0.040 | 0.190 | 42.51 | 212.53 | 0.633 |
| balanced_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 400 | 0.876 | 0.999 | 0.007 | 0.007 | 0.187 | 42.82 | 214.11 | 0.613 |
| balanced_demand | replicator_cardinality | model_based | decentralized | baseline | 400 | 0.618 | 0.859 | 0.958 | 0.312 | 0.465 | 33.51 | 167.57 | 0.160 |
| balanced_demand | smith_cardinality | model_based | decentralized | proposed | 400 | 0.545 | 0.696 | 2.090 | 1.853 | 0.601 | 32.36 | 161.81 | 0.146 |
| monte_carlo | bnn_cardinality | model_based | decentralized | baseline | 100 | 0.675 | 0.865 | 1.270 | 1.510 | 0.427 | 47.10 | 235.52 | 0.194 |
| monte_carlo | cbba | sota | decentralized | baseline | 100 | 0.771 | 0.926 | 0.800 | 0.000 | 0.233 | 37.09 | 185.43 | 0.572 |
| monte_carlo | centralized_coalition_milp | model_based_oracle | centralized | reference | 100 | 0.891 | 0.897 | 1.120 | 0.190 | 0.000 | 35.81 | 179.07 | 7.200 |
| monte_carlo | greedy_nearest | classic | decentralized | baseline | 100 | 0.796 | 0.926 | 0.800 | 0.000 | 0.208 | 37.83 | 189.16 | 0.156 |
| monte_carlo | hungarian_expanded | classic | centralized | baseline | 100 | 0.809 | 0.926 | 0.800 | 0.000 | 0.161 | 35.46 | 177.29 | 0.070 |
| monte_carlo | imitation_oracle | data_driven | decentralized | baseline | 100 | 0.722 | 0.902 | 1.000 | 0.000 | 0.292 | 34.82 | 174.10 | 0.715 |
| monte_carlo | local_primal_dual_wrench_market | model_based | decentralized_local | proposed | 100 | 0.460 | 0.683 | 2.690 | 0.570 | 0.570 | 25.71 | 128.54 | 0.755 |
| monte_carlo | mappo_recruitment | data_driven | decentralized | proposed | 100 | 0.891 | 0.897 | 1.120 | 0.190 | 0.000 | 35.79 | 178.97 | 35.256 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 100 | 0.891 | 0.897 | 1.120 | 0.190 | 0.000 | 35.81 | 179.07 | 7.073 |
| monte_carlo | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 100 | 0.738 | 0.894 | 1.030 | 0.620 | 0.275 | 40.37 | 201.83 | 0.949 |
| monte_carlo | primal_dual_wrench_market | model_based | decentralized | proposed | 100 | 0.745 | 0.899 | 0.990 | 0.560 | 0.269 | 40.64 | 203.21 | 0.923 |
| monte_carlo | replicator_cardinality | model_based | decentralized | baseline | 100 | 0.657 | 0.840 | 1.470 | 1.640 | 0.425 | 44.78 | 223.90 | 0.193 |
| monte_carlo | smith_cardinality | model_based | decentralized | proposed | 100 | 0.573 | 0.697 | 2.720 | 3.170 | 0.567 | 45.39 | 226.97 | 0.198 |
| over_demand | bnn_cardinality | model_based | decentralized | baseline | 800 | 0.290 | 0.710 | 2.840 | 0.019 | 0.957 | 38.17 | 190.83 | 0.166 |
| over_demand | cbba | sota | decentralized | baseline | 800 | 0.427 | 0.721 | 2.750 | 0.000 | 0.612 | 34.77 | 173.84 | 0.432 |
| over_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 800 | 0.663 | 0.645 | 3.553 | 0.186 | 0.000 | 33.67 | 168.33 | 2.289 |
| over_demand | greedy_nearest | classic | decentralized | baseline | 800 | 0.481 | 0.721 | 2.750 | 0.000 | 0.502 | 34.92 | 174.59 | 0.140 |
| over_demand | hungarian_expanded | classic | centralized | baseline | 800 | 0.480 | 0.721 | 2.750 | 0.000 | 0.489 | 33.71 | 168.53 | 0.067 |
| over_demand | imitation_oracle | data_driven | decentralized | baseline | 800 | 0.414 | 0.707 | 2.881 | 0.000 | 0.614 | 32.99 | 164.93 | 0.691 |
| over_demand | local_primal_dual_wrench_market | model_based | decentralized_local | proposed | 800 | 0.274 | 0.721 | 2.750 | 0.000 | 1.037 | 38.04 | 190.18 | 0.643 |
| over_demand | mappo_recruitment | data_driven | decentralized | proposed | 800 | 0.662 | 0.646 | 3.549 | 0.195 | 0.005 | 33.57 | 167.85 | 13.743 |
| over_demand | oracle_reference | model_based_oracle | centralized | reference | 800 | 0.663 | 0.645 | 3.553 | 0.186 | 0.000 | 33.67 | 168.33 | 2.347 |
| over_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 800 | 0.281 | 0.721 | 2.751 | 0.001 | 1.007 | 37.63 | 188.14 | 0.635 |
| over_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 800 | 0.274 | 0.721 | 2.750 | 0.000 | 1.037 | 38.04 | 190.18 | 0.623 |
| over_demand | replicator_cardinality | model_based | decentralized | baseline | 800 | 0.296 | 0.695 | 2.979 | 0.068 | 0.888 | 35.03 | 175.14 | 0.167 |
| over_demand | smith_cardinality | model_based | decentralized | proposed | 800 | 0.383 | 0.571 | 4.154 | 1.304 | 0.641 | 29.88 | 149.39 | 0.188 |
| under_demand | bnn_cardinality | model_based | decentralized | baseline | 800 | 0.853 | 0.958 | 0.185 | 1.097 | 0.238 | 23.98 | 119.91 | 0.155 |
| under_demand | cbba | sota | decentralized | baseline | 800 | 0.873 | 1.000 | 0.000 | 0.000 | 0.154 | 18.83 | 94.17 | 0.351 |
| under_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 800 | 0.998 | 0.999 | 0.005 | 0.374 | 0.000 | 21.11 | 105.53 | 2.964 |
| under_demand | greedy_nearest | classic | decentralized | baseline | 800 | 0.877 | 1.000 | 0.000 | 0.000 | 0.180 | 21.20 | 105.98 | 0.119 |
| under_demand | hungarian_expanded | classic | centralized | baseline | 800 | 0.876 | 1.000 | 0.000 | 0.000 | 0.141 | 18.25 | 91.25 | 0.063 |
| under_demand | imitation_oracle | data_driven | decentralized | baseline | 800 | 0.862 | 0.989 | 0.051 | 0.000 | 0.181 | 19.54 | 97.68 | 0.622 |
| under_demand | local_primal_dual_wrench_market | model_based | decentralized_local | proposed | 800 | 0.951 | 1.000 | 0.000 | 0.544 | 0.106 | 22.95 | 114.75 | 0.571 |
| under_demand | mappo_recruitment | data_driven | decentralized | proposed | 800 | 0.999 | 0.999 | 0.004 | 0.366 | 0.001 | 21.09 | 105.45 | 14.229 |
| under_demand | oracle_reference | model_based_oracle | centralized | reference | 800 | 0.998 | 0.999 | 0.005 | 0.374 | 0.000 | 21.11 | 105.53 | 2.996 |
| under_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 800 | 0.951 | 1.000 | 0.000 | 0.564 | 0.106 | 22.96 | 114.82 | 0.549 |
| under_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 800 | 0.951 | 1.000 | 0.000 | 0.544 | 0.106 | 22.95 | 114.75 | 0.541 |
| under_demand | replicator_cardinality | model_based | decentralized | baseline | 800 | 0.814 | 0.923 | 0.330 | 1.206 | 0.267 | 22.27 | 111.37 | 0.159 |
| under_demand | smith_cardinality | model_based | decentralized | proposed | 800 | 0.741 | 0.791 | 0.905 | 3.425 | 0.542 | 32.80 | 163.98 | 0.148 |

Best raw mean demand satisfaction: **local_primal_dual_wrench_market** on `under_demand`.

## Performance Ranking

Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.

Theory-aligned best overall: **centralized_coalition_milp** (`reference`).

| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| ALL_SCENARIOS | 1 | centralized_coalition_milp | model_based_oracle | reference | 0.846 | 0.847 | 0.000 | 30.03 | 0 | 2.600 |
| ALL_SCENARIOS | 2 | oracle_reference | model_based_oracle | reference | 0.846 | 0.847 | 0.000 | 30.03 | 0 | 2.642 |
| ALL_SCENARIOS | 3 | mappo_recruitment | data_driven | proposed | 0.846 | 0.846 | 0.004 | 29.99 | 4674 | 13.872 |
| ALL_SCENARIOS | 4 | hungarian_expanded | classic | baseline | 0.890 | 0.721 | 0.277 | 29.24 | 0 | 0.065 |
| ALL_SCENARIOS | 5 | greedy_nearest | classic | baseline | 0.890 | 0.722 | 0.304 | 31.39 | 0 | 0.131 |
| ALL_SCENARIOS | 6 | cbba | sota | baseline | 0.890 | 0.698 | 0.338 | 30.33 | 0 | 0.408 |
| ALL_SCENARIOS | 7 | imitation_oracle | data_driven | baseline | 0.864 | 0.658 | 0.377 | 28.24 | 7 | 0.664 |
| ALL_SCENARIOS | 8 | primal_dual_cardinality_capacity | model_based | proposed | 0.887 | 0.670 | 0.474 | 33.10 | 0 | 0.617 |

## Theory Audit

- Checks: `27300`.
- Failed checks: `0`.
- Strict complete-coalition failures: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H01_methods_differ_theoretical_gap | optimality_gap_vs_oracle | 2100 | 0 | 0 | 0.6063 |  | True | ok |
| H02_mappo_lower_gap_than_imitation | optimality_gap_vs_oracle | 2100 | 0 | 0 | -0.3731 | [-0.3903, -0.355] | True | ok |
| H03_mappo_lower_gap_than_hungarian_classic | optimality_gap_vs_oracle | 2100 | 1.558e-182 | 1.558e-182 | -0.2722 | [-0.2886, -0.2547] | True | ok |
| H04_smith_lower_runtime_than_mappo | runtime_ms | 2100 | 0 | 0 | -13.71 | [-14.27, -13.21] | True | ok |
| H05_mappo_higher_coalition_success_than_smith | coalition_success_rate | 2100 | 0 | 0 | 0.2873 | [0.2787, 0.2953] | True | ok |

## Scenario Videos

- `balanced_demand` `median` `baseline/classic/decentralized` `greedy_nearest` seed `2050`: `sp1_balanced-demand_median_baseline_classic_decentralized_nearest-greedy_greedy-nearest_seed2050.mp4`
- `balanced_demand` `median` `baseline/classic/centralized` `hungarian_expanded` seed `2050`: `sp1_balanced-demand_median_baseline_classic_centralized_hungarian-expanded_hungarian-expanded_seed2050.mp4`
- `balanced_demand` `median` `reference/model_based_oracle/centralized` `centralized_coalition_milp` seed `2028`: `sp1_balanced-demand_median_reference_model-based-oracle_centralized_exact-capacity-feasible-coalition_centralized-coalition-milp_seed2028.mp4`
- `balanced_demand` `median` `baseline/sota/decentralized` `cbba` seed `2050`: `sp1_balanced-demand_median_baseline_sota_decentralized_cbba-like-auction_cbba_seed2050.mp4`
- `balanced_demand` `median` `baseline/model_based/decentralized` `replicator_cardinality` seed `2014`: `sp1_balanced-demand_median_baseline_model-based_decentralized_population-game-replicator_replicator-cardinality_seed2014.mp4`
- `balanced_demand` `median` `proposed/model_based/decentralized` `smith_cardinality` seed `2093`: `sp1_balanced-demand_median_proposed_model-based_decentralized_smith-qr-cardinality_smith-cardinality_seed2093.mp4`
- `balanced_demand` `median` `baseline/model_based/decentralized` `bnn_cardinality` seed `2049`: `sp1_balanced-demand_median_baseline_model-based_decentralized_bnn-cardinality_bnn-cardinality_seed2049.mp4`
- `balanced_demand` `median` `proposed/model_based/decentralized` `primal_dual_cardinality_capacity` seed `2048`: `sp1_balanced-demand_median_proposed_model-based_decentralized_primal-dual-capacity_primal-dual-cardinality-capacity_seed2048.mp4`
- `balanced_demand` `median` `proposed/model_based/decentralized` `primal_dual_wrench_market` seed `2049`: `sp1_balanced-demand_median_proposed_model-based_decentralized_primal-dual-wrench-proxy_primal-dual-wrench-market_seed2049.mp4`
- `balanced_demand` `median` `proposed/model_based/decentralized_local` `local_primal_dual_wrench_market` seed `2049`: `sp1_balanced-demand_median_proposed_model-based_decentralized-local_local-primal-dual-wrench-proxy_local-primal-dual-wrench-market_seed2049.mp4`
- `balanced_demand` `median` `baseline/data_driven/decentralized` `imitation_oracle` seed `2003`: `sp1_balanced-demand_median_baseline_data-driven_decentralized_oracle-imitation-linear_imitation-oracle_seed2003.mp4`
- `balanced_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2028`: `sp1_balanced-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2028.mp4`
- `monte_carlo` `median` `baseline/classic/decentralized` `greedy_nearest` seed `2024`: `sp1_monte-carlo_median_baseline_classic_decentralized_nearest-greedy_greedy-nearest_seed2024.mp4`
- `monte_carlo` `median` `baseline/classic/centralized` `hungarian_expanded` seed `2024`: `sp1_monte-carlo_median_baseline_classic_centralized_hungarian-expanded_hungarian-expanded_seed2024.mp4`
- `monte_carlo` `median` `reference/model_based_oracle/centralized` `centralized_coalition_milp` seed `2023`: `sp1_monte-carlo_median_reference_model-based-oracle_centralized_exact-capacity-feasible-coalition_centralized-coalition-milp_seed2023.mp4`
- `monte_carlo` `median` `baseline/sota/decentralized` `cbba` seed `2024`: `sp1_monte-carlo_median_baseline_sota_decentralized_cbba-like-auction_cbba_seed2024.mp4`
- `monte_carlo` `median` `baseline/model_based/decentralized` `replicator_cardinality` seed `2010`: `sp1_monte-carlo_median_baseline_model-based_decentralized_population-game-replicator_replicator-cardinality_seed2010.mp4`
- `monte_carlo` `median` `proposed/model_based/decentralized` `smith_cardinality` seed `2087`: `sp1_monte-carlo_median_proposed_model-based_decentralized_smith-qr-cardinality_smith-cardinality_seed2087.mp4`
- `monte_carlo` `median` `baseline/model_based/decentralized` `bnn_cardinality` seed `2008`: `sp1_monte-carlo_median_baseline_model-based_decentralized_bnn-cardinality_bnn-cardinality_seed2008.mp4`
- `monte_carlo` `median` `proposed/model_based/decentralized` `primal_dual_cardinality_capacity` seed `2001`: `sp1_monte-carlo_median_proposed_model-based_decentralized_primal-dual-capacity_primal-dual-cardinality-capacity_seed2001.mp4`
- `monte_carlo` `median` `proposed/model_based/decentralized` `primal_dual_wrench_market` seed `2004`: `sp1_monte-carlo_median_proposed_model-based_decentralized_primal-dual-wrench-proxy_primal-dual-wrench-market_seed2004.mp4`
- `monte_carlo` `median` `proposed/model_based/decentralized_local` `local_primal_dual_wrench_market` seed `2054`: `sp1_monte-carlo_median_proposed_model-based_decentralized-local_local-primal-dual-wrench-proxy_local-primal-dual-wrench-market_seed2054.mp4`
- `monte_carlo` `median` `baseline/data_driven/decentralized` `imitation_oracle` seed `2011`: `sp1_monte-carlo_median_baseline_data-driven_decentralized_oracle-imitation-linear_imitation-oracle_seed2011.mp4`
- `monte_carlo` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2023`: `sp1_monte-carlo_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2023.mp4`
- `over_demand` `median` `baseline/classic/decentralized` `greedy_nearest` seed `2000`: `sp1_over-demand_median_baseline_classic_decentralized_nearest-greedy_greedy-nearest_seed2000.mp4`
- `over_demand` `median` `baseline/classic/centralized` `hungarian_expanded` seed `2000`: `sp1_over-demand_median_baseline_classic_centralized_hungarian-expanded_hungarian-expanded_seed2000.mp4`
- `over_demand` `median` `reference/model_based_oracle/centralized` `centralized_coalition_milp` seed `2040`: `sp1_over-demand_median_reference_model-based-oracle_centralized_exact-capacity-feasible-coalition_centralized-coalition-milp_seed2040.mp4`
- `over_demand` `median` `baseline/sota/decentralized` `cbba` seed `2000`: `sp1_over-demand_median_baseline_sota_decentralized_cbba-like-auction_cbba_seed2000.mp4`
- `over_demand` `median` `baseline/model_based/decentralized` `replicator_cardinality` seed `2081`: `sp1_over-demand_median_baseline_model-based_decentralized_population-game-replicator_replicator-cardinality_seed2081.mp4`
- `over_demand` `median` `proposed/model_based/decentralized` `smith_cardinality` seed `2044`: `sp1_over-demand_median_proposed_model-based_decentralized_smith-qr-cardinality_smith-cardinality_seed2044.mp4`
- `over_demand` `median` `baseline/model_based/decentralized` `bnn_cardinality` seed `2089`: `sp1_over-demand_median_baseline_model-based_decentralized_bnn-cardinality_bnn-cardinality_seed2089.mp4`
- `over_demand` `median` `proposed/model_based/decentralized` `primal_dual_cardinality_capacity` seed `2094`: `sp1_over-demand_median_proposed_model-based_decentralized_primal-dual-capacity_primal-dual-cardinality-capacity_seed2094.mp4`
- `over_demand` `median` `proposed/model_based/decentralized` `primal_dual_wrench_market` seed `2000`: `sp1_over-demand_median_proposed_model-based_decentralized_primal-dual-wrench-proxy_primal-dual-wrench-market_seed2000.mp4`
- `over_demand` `median` `proposed/model_based/decentralized_local` `local_primal_dual_wrench_market` seed `2000`: `sp1_over-demand_median_proposed_model-based_decentralized-local_local-primal-dual-wrench-proxy_local-primal-dual-wrench-market_seed2000.mp4`
- `over_demand` `median` `baseline/data_driven/decentralized` `imitation_oracle` seed `2091`: `sp1_over-demand_median_baseline_data-driven_decentralized_oracle-imitation-linear_imitation-oracle_seed2091.mp4`
- `over_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2039`: `sp1_over-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2039.mp4`
- `under_demand` `median` `baseline/classic/decentralized` `greedy_nearest` seed `2050`: `sp1_under-demand_median_baseline_classic_decentralized_nearest-greedy_greedy-nearest_seed2050.mp4`
- `under_demand` `median` `baseline/classic/centralized` `hungarian_expanded` seed `2050`: `sp1_under-demand_median_baseline_classic_centralized_hungarian-expanded_hungarian-expanded_seed2050.mp4`
- `under_demand` `median` `reference/model_based_oracle/centralized` `centralized_coalition_milp` seed `2049`: `sp1_under-demand_median_reference_model-based-oracle_centralized_exact-capacity-feasible-coalition_centralized-coalition-milp_seed2049.mp4`
- `under_demand` `median` `baseline/sota/decentralized` `cbba` seed `2050`: `sp1_under-demand_median_baseline_sota_decentralized_cbba-like-auction_cbba_seed2050.mp4`
- `under_demand` `median` `baseline/model_based/decentralized` `replicator_cardinality` seed `2028`: `sp1_under-demand_median_baseline_model-based_decentralized_population-game-replicator_replicator-cardinality_seed2028.mp4`
- `under_demand` `median` `proposed/model_based/decentralized` `smith_cardinality` seed `2086`: `sp1_under-demand_median_proposed_model-based_decentralized_smith-qr-cardinality_smith-cardinality_seed2086.mp4`
- `under_demand` `median` `baseline/model_based/decentralized` `bnn_cardinality` seed `2039`: `sp1_under-demand_median_baseline_model-based_decentralized_bnn-cardinality_bnn-cardinality_seed2039.mp4`
- `under_demand` `median` `proposed/model_based/decentralized` `primal_dual_cardinality_capacity` seed `2050`: `sp1_under-demand_median_proposed_model-based_decentralized_primal-dual-capacity_primal-dual-cardinality-capacity_seed2050.mp4`
- `under_demand` `median` `proposed/model_based/decentralized` `primal_dual_wrench_market` seed `2050`: `sp1_under-demand_median_proposed_model-based_decentralized_primal-dual-wrench-proxy_primal-dual-wrench-market_seed2050.mp4`
- `under_demand` `median` `proposed/model_based/decentralized_local` `local_primal_dual_wrench_market` seed `2050`: `sp1_under-demand_median_proposed_model-based_decentralized-local_local-primal-dual-wrench-proxy_local-primal-dual-wrench-market_seed2050.mp4`
- `under_demand` `median` `baseline/data_driven/decentralized` `imitation_oracle` seed `2047`: `sp1_under-demand_median_baseline_data-driven_decentralized_oracle-imitation-linear_imitation-oracle_seed2047.mp4`
- `under_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2049`: `sp1_under-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2049.mp4`

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
