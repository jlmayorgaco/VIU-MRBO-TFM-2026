# SP2_MC_capacity_comparison

SP2 evaluates physical effective capacity: which heterogeneous AMRs cover heterogeneous load demand after distance and battery discounts, while communication is tracked separately as observability.
Theory note: because effective capacity is pair-dependent, the plain payoff V_k sigma(D_k-S_k)-g_ik is not generally potential-aligned. The Teorema 2 marginal payoff e_ik V_k sigma(D_k-S_k)-g_ik recovers exact potential structure for fixed E during the decision instant.
- Seeds: `3100`-`3139` (`n=40`)
- Scenario generators: `light_mixed, balanced_capacity, heavy_capacity, battery_constrained, monte_carlo`
- Training/tuning seeds must remain disjoint from this Monte Carlo evaluation.
- `oracle_reference` is the score oracle: capacity coverage plus completed-load reward and small physical-cost penalties.
- `capacity_oracle_reference` is the pure physical capacity ceiling used for `effective_feasibility_ratio` and capacity-gap analysis.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| bnn_capacity | BNN capacity | model_based | decentralized | baseline | bnn_capacity_utility | model_based_decentralized_baseline |
| capacity_oracle_reference | Pure capacity oracle reference | model_based_oracle | centralized | reference | exact_capacity_coverage_replay | centralized_capacity_ceiling_reference |
| cbba_capacity | CBBA capacity auction | sota | decentralized | baseline | cbba_payload_capacity_proxy | sota_decentralized_baseline |
| centralized_capacity_milp | Centralized capacity oracle | model_based_oracle | centralized | reference | exact_effective_capacity_milp | centralized_oracle_reference |
| greedy_capacity_nearest | Greedy capacity nearest | classic | decentralized | baseline | nearest_capacity_greedy | classic_decentralized_baseline |
| hungarian_capacity | Hungarian capacity expanded | classic | centralized | baseline | hungarian_capacity_expanded | classic_centralized_baseline |
| imitation_capacity | Data-driven capacity imitation | data_driven | decentralized | baseline | oracle_capacity_imitation_linear | data_driven_baseline |
| local_primal_dual_capacity | Local primal-dual capacity | model_based | decentralized_local | proposed | local_primal_dual_effective_capacity | proposed_local_variation |
| neural_capacity_scorer | Neural capacity scorer | data_driven | decentralized | proposed | oracle_capacity_neural_scorer | proposed_data_driven_variation |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_reference_replay | centralized_oracle_reference |
| primal_dual_capacity | Primal-dual capacity | model_based | decentralized | proposed | primal_dual_effective_capacity | proposed_model_based_variation |
| replicator_capacity | Replicator capacity | model_based | decentralized | baseline | population_game_capacity | model_based_decentralized_baseline |
| smith_capacity | Smith-QR capacity | model_based | decentralized | proposed | smith_qr_effective_capacity | proposed_model_based_variation |

## Resource Fairness

| Method | Training type | Execution model | Trainable params | Tuned params | Decoder |
|---|---|---|---:|---:|---|
| bnn_capacity | model_based_tuning_optional | distributed_nonlinear_capacity_rule | 0 | 5 | False |
| capacity_oracle_reference | none | centralized_exact_capacity_ceiling_replay | 0 | 2 | False |
| cbba_capacity | none | distributed_payload_auction_proxy | 0 | 3 | False |
| centralized_capacity_milp | none | centralized_binary_milp_effective_capacity | 0 | 3 | False |
| greedy_capacity_nearest | none | distributed_capacity_greedy_rule | 0 | 0 | False |
| hungarian_capacity | none | centralized_capacity_slot_assignment | 0 | 0 | False |
| imitation_capacity | supervised_oracle_imitation | distributed_linear_capacity_score_policy | 8 | 1 | False |
| local_primal_dual_capacity | model_based_tuning_optional | local_primal_dual_capacity_rule | 0 | 5 | False |
| neural_capacity_scorer | supervised_oracle_imitation | distributed_neural_capacity_score_policy | 121 | 3 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 3 | False |
| primal_dual_capacity | model_based_tuning_optional | distributed_primal_dual_capacity_rule | 0 | 5 | False |
| replicator_capacity | model_based_tuning_optional | distributed_capacity_utility_rule | 0 | 4 | False |
| smith_capacity | model_based_tuning_optional | distributed_smith_qr_capacity_rule | 0 | 4 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Under kg | Over kg | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_capacity | bnn_capacity | model_based | decentralized | baseline | 640 | 0.057 | 0.346 | 0.027 | 0.501 | 0.869 | 0.127 | 200.24 | 2.07 | 64.04 | 389.14 | 0.366 |
| balanced_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 640 | 0.168 | 0.058 | 0.000 | 0.505 | 0.798 | 0.199 | 198.32 | 1.17 | 63.43 | 384.21 | 11.300 |
| balanced_capacity | cbba_capacity | sota | decentralized | baseline | 640 | 0.148 | 0.307 | 0.030 | 0.499 | 0.690 | 0.300 | 201.04 | 5.04 | 61.73 | 374.61 | 0.863 |
| balanced_capacity | centralized_capacity_milp | model_based_oracle | centralized | reference | 640 | 0.455 | 0.000 | 0.027 | 0.491 | 0.328 | 0.667 | 203.72 | 4.11 | 66.29 | 401.34 | 39.324 |
| balanced_capacity | greedy_capacity_nearest | classic | decentralized | baseline | 640 | 0.159 | 0.274 | 0.030 | 0.499 | 0.703 | 0.280 | 200.55 | 7.51 | 58.62 | 355.78 | 0.318 |
| balanced_capacity | hungarian_capacity | classic | centralized | baseline | 640 | 0.043 | 0.208 | 0.009 | 0.516 | 0.945 | 0.049 | 193.97 | 1.86 | 57.20 | 347.36 | 0.229 |
| balanced_capacity | imitation_capacity | data_driven | decentralized | baseline | 640 | 0.162 | 0.117 | 0.024 | 0.503 | 0.790 | 0.191 | 199.02 | 7.07 | 57.11 | 346.72 | 1.006 |
| balanced_capacity | local_primal_dual_capacity | model_based | decentralized_local | proposed | 640 | 0.030 | 0.370 | 0.033 | 0.498 | 0.926 | 0.073 | 201.45 | 0.89 | 66.94 | 406.41 | 1.342 |
| balanced_capacity | neural_capacity_scorer | data_driven | decentralized | proposed | 640 | 0.224 | 0.104 | 0.039 | 0.493 | 0.690 | 0.284 | 202.95 | 10.92 | 57.07 | 346.42 | 1.047 |
| balanced_capacity | oracle_reference | model_based_oracle | centralized | reference | 640 | 0.455 | 0.000 | 0.027 | 0.491 | 0.328 | 0.667 | 203.72 | 4.11 | 66.29 | 401.34 | 39.408 |
| balanced_capacity | primal_dual_capacity | model_based | decentralized | proposed | 640 | 0.031 | 0.366 | 0.032 | 0.499 | 0.925 | 0.074 | 201.04 | 0.90 | 66.47 | 403.81 | 1.296 |
| balanced_capacity | replicator_capacity | model_based | decentralized | baseline | 640 | 0.063 | 0.306 | 0.018 | 0.508 | 0.877 | 0.118 | 197.34 | 2.40 | 60.64 | 367.89 | 0.384 |
| balanced_capacity | smith_capacity | model_based | decentralized | proposed | 640 | 0.040 | 0.362 | 0.032 | 0.498 | 0.902 | 0.096 | 201.60 | 1.41 | 66.19 | 402.19 | 0.365 |
| battery_constrained | bnn_capacity | model_based | decentralized | baseline | 240 | 0.032 | 0.346 | 0.017 | 0.411 | 0.931 | 0.066 | 229.88 | 1.07 | 51.75 | 313.15 | 0.339 |
| battery_constrained | capacity_oracle_reference | model_based_oracle | centralized | reference | 240 | 0.134 | 0.051 | 0.000 | 0.402 | 0.800 | 0.197 | 233.30 | 1.04 | 57.30 | 347.24 | 9.534 |
| battery_constrained | cbba_capacity | sota | decentralized | baseline | 240 | 0.111 | 0.316 | 0.025 | 0.406 | 0.766 | 0.221 | 231.46 | 4.52 | 49.55 | 299.56 | 0.690 |
| battery_constrained | centralized_capacity_milp | model_based_oracle | centralized | reference | 240 | 0.391 | 0.000 | 0.033 | 0.388 | 0.312 | 0.682 | 238.10 | 3.50 | 59.80 | 362.15 | 35.188 |
| battery_constrained | greedy_capacity_nearest | classic | decentralized | baseline | 240 | 0.135 | 0.272 | 0.027 | 0.405 | 0.730 | 0.250 | 231.63 | 7.08 | 46.78 | 282.97 | 0.289 |
| battery_constrained | hungarian_capacity | classic | centralized | baseline | 240 | 0.043 | 0.233 | 0.010 | 0.417 | 0.932 | 0.061 | 227.26 | 2.14 | 47.32 | 285.67 | 0.212 |
| battery_constrained | imitation_capacity | data_driven | decentralized | baseline | 240 | 0.122 | 0.134 | 0.024 | 0.407 | 0.811 | 0.170 | 230.93 | 6.11 | 46.74 | 282.45 | 0.962 |
| battery_constrained | local_primal_dual_capacity | model_based | decentralized_local | proposed | 240 | 0.029 | 0.437 | 0.191 | 0.333 | 0.937 | 0.058 | 258.89 | 1.43 | 32.24 | 196.00 | 0.800 |
| battery_constrained | neural_capacity_scorer | data_driven | decentralized | proposed | 240 | 0.147 | 0.122 | 0.029 | 0.405 | 0.759 | 0.221 | 231.78 | 7.28 | 46.12 | 278.68 | 0.966 |
| battery_constrained | oracle_reference | model_based_oracle | centralized | reference | 240 | 0.391 | 0.000 | 0.033 | 0.388 | 0.312 | 0.682 | 238.10 | 3.50 | 59.80 | 362.15 | 36.038 |
| battery_constrained | primal_dual_capacity | model_based | decentralized | proposed | 240 | 0.016 | 0.371 | 0.023 | 0.408 | 0.967 | 0.032 | 231.42 | 0.46 | 55.44 | 335.93 | 1.016 |
| battery_constrained | replicator_capacity | model_based | decentralized | baseline | 240 | 0.047 | 0.304 | 0.012 | 0.415 | 0.911 | 0.084 | 228.13 | 1.88 | 48.79 | 295.23 | 0.333 |
| battery_constrained | smith_capacity | model_based | decentralized | proposed | 240 | 0.022 | 0.359 | 0.020 | 0.409 | 0.953 | 0.046 | 230.74 | 0.50 | 53.94 | 326.78 | 0.329 |
| heavy_capacity | bnn_capacity | model_based | decentralized | baseline | 320 | 0.014 | 0.524 | 0.042 | 0.370 | 0.956 | 0.043 | 351.67 | 0.91 | 65.77 | 398.73 | 0.370 |
| heavy_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.187 | 0.055 | 0.000 | 0.374 | 0.737 | 0.259 | 348.73 | 2.13 | 61.98 | 376.01 | 15.523 |
| heavy_capacity | cbba_capacity | sota | decentralized | baseline | 320 | 0.062 | 0.486 | 0.037 | 0.372 | 0.828 | 0.167 | 350.89 | 3.34 | 62.40 | 378.53 | 0.853 |
| heavy_capacity | centralized_capacity_milp | model_based_oracle | centralized | reference | 320 | 0.432 | 0.000 | 0.029 | 0.363 | 0.270 | 0.724 | 354.86 | 5.61 | 65.01 | 394.25 | 59.992 |
| heavy_capacity | greedy_capacity_nearest | classic | decentralized | baseline | 320 | 0.070 | 0.435 | 0.028 | 0.378 | 0.847 | 0.142 | 346.87 | 4.71 | 57.31 | 347.90 | 0.297 |
| heavy_capacity | hungarian_capacity | classic | centralized | baseline | 320 | 0.067 | 0.272 | 0.008 | 0.392 | 0.895 | 0.092 | 338.55 | 4.88 | 48.76 | 296.02 | 0.219 |
| heavy_capacity | imitation_capacity | data_driven | decentralized | baseline | 320 | 0.155 | 0.146 | 0.033 | 0.375 | 0.767 | 0.205 | 348.35 | 11.25 | 51.56 | 312.80 | 0.998 |
| heavy_capacity | local_primal_dual_capacity | model_based | decentralized_local | proposed | 320 | 0.010 | 0.548 | 0.053 | 0.365 | 0.966 | 0.033 | 354.71 | 0.43 | 69.80 | 424.00 | 1.309 |
| heavy_capacity | neural_capacity_scorer | data_driven | decentralized | proposed | 320 | 0.202 | 0.127 | 0.043 | 0.368 | 0.679 | 0.289 | 351.92 | 14.35 | 51.84 | 314.27 | 1.030 |
| heavy_capacity | oracle_reference | model_based_oracle | centralized | reference | 320 | 0.432 | 0.000 | 0.029 | 0.363 | 0.270 | 0.724 | 354.86 | 5.61 | 65.01 | 394.25 | 59.448 |
| heavy_capacity | primal_dual_capacity | model_based | decentralized | proposed | 320 | 0.010 | 0.542 | 0.050 | 0.366 | 0.969 | 0.030 | 354.03 | 0.48 | 69.02 | 419.09 | 1.267 |
| heavy_capacity | replicator_capacity | model_based | decentralized | baseline | 320 | 0.020 | 0.477 | 0.027 | 0.379 | 0.961 | 0.036 | 346.74 | 1.10 | 60.69 | 368.21 | 0.380 |
| heavy_capacity | smith_capacity | model_based | decentralized | proposed | 320 | 0.009 | 0.538 | 0.048 | 0.367 | 0.970 | 0.029 | 353.51 | 0.50 | 68.25 | 414.34 | 0.376 |
| light_mixed | bnn_capacity | model_based | decentralized | baseline | 320 | 0.416 | 0.115 | 0.040 | 0.788 | 0.478 | 0.490 | 40.85 | 14.23 | 48.30 | 289.51 | 0.315 |
| light_mixed | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.446 | 0.021 | 0.000 | 0.816 | 0.550 | 0.440 | 36.37 | 5.80 | 50.64 | 304.31 | 8.950 |
| light_mixed | cbba_capacity | sota | decentralized | baseline | 320 | 0.536 | 0.125 | 0.064 | 0.766 | 0.289 | 0.680 | 44.74 | 18.50 | 47.87 | 286.89 | 0.608 |
| light_mixed | centralized_capacity_milp | model_based_oracle | centralized | reference | 320 | 0.672 | 0.000 | 0.028 | 0.795 | 0.260 | 0.729 | 40.30 | 8.83 | 52.03 | 311.74 | 29.535 |
| light_mixed | greedy_capacity_nearest | classic | decentralized | baseline | 320 | 0.536 | 0.140 | 0.098 | 0.736 | 0.294 | 0.664 | 49.75 | 23.29 | 48.18 | 289.11 | 0.268 |
| light_mixed | hungarian_capacity | classic | centralized | baseline | 320 | 0.201 | 0.223 | 0.159 | 0.680 | 0.748 | 0.221 | 58.36 | 7.11 | 32.74 | 197.67 | 0.201 |
| light_mixed | imitation_capacity | data_driven | decentralized | baseline | 320 | 0.457 | 0.085 | 0.083 | 0.749 | 0.486 | 0.457 | 47.61 | 19.83 | 49.29 | 295.76 | 0.927 |
| light_mixed | local_primal_dual_capacity | model_based | decentralized_local | proposed | 320 | 0.371 | 0.104 | 0.023 | 0.804 | 0.563 | 0.413 | 38.17 | 10.27 | 49.90 | 298.86 | 0.872 |
| light_mixed | neural_capacity_scorer | data_driven | decentralized | proposed | 320 | 0.489 | 0.090 | 0.096 | 0.738 | 0.428 | 0.512 | 49.57 | 22.44 | 48.75 | 292.09 | 0.962 |
| light_mixed | oracle_reference | model_based_oracle | centralized | reference | 320 | 0.672 | 0.000 | 0.028 | 0.795 | 0.260 | 0.729 | 40.30 | 8.83 | 52.03 | 311.74 | 28.957 |
| light_mixed | primal_dual_capacity | model_based | decentralized | proposed | 320 | 0.373 | 0.105 | 0.023 | 0.803 | 0.558 | 0.418 | 38.25 | 10.53 | 49.70 | 297.49 | 0.873 |
| light_mixed | replicator_capacity | model_based | decentralized | baseline | 320 | 0.461 | 0.110 | 0.051 | 0.778 | 0.433 | 0.532 | 42.52 | 16.26 | 48.25 | 289.44 | 0.327 |
| light_mixed | smith_capacity | model_based | decentralized | proposed | 320 | 0.369 | 0.113 | 0.030 | 0.797 | 0.549 | 0.422 | 39.27 | 11.72 | 49.27 | 295.16 | 0.306 |
| monte_carlo | bnn_capacity | model_based | decentralized | baseline | 40 | 0.270 | 0.192 | 0.031 | 0.590 | 0.644 | 0.335 | 204.83 | 11.76 | 62.37 | 376.62 | 0.344 |
| monte_carlo | capacity_oracle_reference | model_based_oracle | centralized | reference | 40 | 0.283 | 0.063 | 0.000 | 0.606 | 0.700 | 0.295 | 200.92 | 5.98 | 63.82 | 380.77 | 7.500 |
| monte_carlo | cbba_capacity | sota | decentralized | baseline | 40 | 0.334 | 0.167 | 0.037 | 0.586 | 0.546 | 0.434 | 205.76 | 16.21 | 60.46 | 362.92 | 0.865 |
| monte_carlo | centralized_capacity_milp | model_based_oracle | centralized | reference | 40 | 0.528 | 0.000 | 0.023 | 0.591 | 0.317 | 0.674 | 207.50 | 9.35 | 65.98 | 393.60 | 39.989 |
| monte_carlo | greedy_capacity_nearest | classic | decentralized | baseline | 40 | 0.334 | 0.168 | 0.047 | 0.576 | 0.550 | 0.423 | 209.01 | 17.72 | 60.78 | 365.73 | 0.273 |
| monte_carlo | hungarian_capacity | classic | centralized | baseline | 40 | 0.165 | 0.189 | 0.054 | 0.572 | 0.827 | 0.151 | 207.97 | 10.09 | 55.48 | 330.62 | 0.209 |
| monte_carlo | imitation_capacity | data_driven | decentralized | baseline | 40 | 0.282 | 0.107 | 0.037 | 0.584 | 0.687 | 0.283 | 204.33 | 16.11 | 59.20 | 355.38 | 1.042 |
| monte_carlo | local_primal_dual_capacity | model_based | decentralized_local | proposed | 40 | 0.177 | 0.412 | 0.333 | 0.414 | 0.709 | 0.253 | 268.80 | 7.37 | 29.60 | 173.15 | 0.931 |
| monte_carlo | neural_capacity_scorer | data_driven | decentralized | proposed | 40 | 0.275 | 0.108 | 0.037 | 0.586 | 0.702 | 0.267 | 204.73 | 15.45 | 59.73 | 359.75 | 0.999 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 40 | 0.528 | 0.000 | 0.023 | 0.591 | 0.317 | 0.674 | 207.50 | 9.35 | 65.98 | 393.60 | 38.819 |
| monte_carlo | primal_dual_capacity | model_based | decentralized | proposed | 40 | 0.244 | 0.203 | 0.032 | 0.592 | 0.710 | 0.273 | 205.66 | 10.32 | 65.03 | 390.34 | 1.333 |
| monte_carlo | replicator_capacity | model_based | decentralized | baseline | 40 | 0.276 | 0.171 | 0.035 | 0.586 | 0.646 | 0.331 | 204.50 | 13.79 | 60.52 | 364.71 | 0.404 |
| monte_carlo | smith_capacity | model_based | decentralized | proposed | 40 | 0.233 | 0.207 | 0.033 | 0.592 | 0.725 | 0.254 | 205.82 | 10.17 | 64.53 | 387.58 | 0.355 |

## Performance Ranking

Ranking rule: minimize score-oracle gap; then maximize completed-load capacity success; then minimize capacity-ceiling gap, incomplete capacity, under/over capacity, travel, energy, communication, and runtime. Capacity satisfaction is reported as secondary coverage.

Theory-aligned best overall: **oracle_reference** (`reference`).

| Rank | Method | Family | Owner | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Under kg | Over kg | Travel m | Params | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | oracle_reference | model_based_oracle | reference | 0.487 | 0.000 | 0.029 | 0.514 | 0.299 | 206.59 | 5.43 | 62.10 | 0 | 40.842 |
| 2 | centralized_capacity_milp | model_based_oracle | reference | 0.487 | 0.000 | 0.029 | 0.514 | 0.299 | 206.59 | 5.43 | 62.10 | 0 | 40.937 |
| 3 | capacity_oracle_reference | model_based_oracle | reference | 0.227 | 0.049 | 0.000 | 0.529 | 0.733 | 201.40 | 2.42 | 59.58 | 0 | 11.315 |
| 4 | neural_capacity_scorer | data_driven | proposed | 0.263 | 0.109 | 0.050 | 0.507 | 0.645 | 206.52 | 13.54 | 52.67 | 121 | 1.012 |
| 5 | imitation_capacity | data_driven | baseline | 0.218 | 0.118 | 0.038 | 0.514 | 0.724 | 203.64 | 10.63 | 52.83 | 8 | 0.982 |
| 6 | hungarian_capacity | classic | baseline | 0.083 | 0.228 | 0.041 | 0.510 | 0.889 | 201.29 | 3.81 | 48.89 | 0 | 0.218 |
| 7 | greedy_capacity_nearest | classic | baseline | 0.219 | 0.276 | 0.044 | 0.510 | 0.649 | 204.63 | 10.37 | 54.44 | 0 | 0.298 |
| 8 | replicator_capacity | model_based | baseline | 0.139 | 0.297 | 0.026 | 0.525 | 0.802 | 201.15 | 5.18 | 56.28 | 0 | 0.364 |
| 9 | cbba_capacity | sota | baseline | 0.209 | 0.304 | 0.038 | 0.516 | 0.644 | 204.52 | 7.66 | 57.12 | 0 | 0.782 |
| 10 | bnn_capacity | model_based | baseline | 0.124 | 0.331 | 0.031 | 0.522 | 0.811 | 203.29 | 4.42 | 59.23 | 0 | 0.351 |
| 11 | smith_capacity | model_based | proposed | 0.103 | 0.343 | 0.033 | 0.521 | 0.847 | 204.05 | 3.42 | 61.21 | 0 | 0.349 |
| 12 | primal_dual_capacity | model_based | proposed | 0.100 | 0.345 | 0.032 | 0.523 | 0.859 | 203.82 | 2.96 | 61.82 | 0 | 1.161 |
| 13 | local_primal_dual_capacity | model_based | proposed | 0.100 | 0.363 | 0.067 | 0.506 | 0.856 | 209.96 | 2.97 | 57.74 | 0 | 1.145 |

## Theory Audit

- Checks: `20280`.
- Failed checks: `0`.
- Passed: `True`.
- Potential theorem: `Teorema 2`.
- Potential structure in this experiment: `mixed`.
- Marginal payoff methods: `centralized_capacity_milp, oracle_reference, capacity_oracle_reference`.
- Distance interpretation: `deliverable_capacity_within_finite_operational_horizon`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H01_methods_differ_capacity_gap | optimality_gap_vs_oracle | 1560 | 0.0000 | 0.0000 | 0.7100 |  | True | ok |
| H01b_methods_differ_capacity_ceiling_gap | capacity_gap_vs_capacity_oracle | 1560 | 2.84e-10 | 5.68e-10 | 0.0081 |  | True | ok |
| H02_primal_dual_higher_capacity_success_than_greedy | capacity_success_rate | 1560 | 1.0000 | 1.0000 | -0.1190 | [-0.1278, -0.1108] | False | ok |
| H03_neural_lower_gap_than_linear_imitation | optimality_gap_vs_oracle | 1560 | 2.94e-27 | 1.17e-26 | -0.0097 | [-0.01176, -0.007593] | True | ok |
| H04_local_primal_dual_lower_messages_than_oracle | communication_messages | 1560 | 2.28e-18 | 6.85e-18 | -2.8385 | [-3.231, -2.457] | True | ok |
| H05_smith_lower_runtime_than_neural | runtime_ms | 1560 | 1.74e-256 | 8.71e-256 | -0.6627 | [-0.6859, -0.6439] | True | ok |

## Scenario Videos

- `balanced_capacity` `bnn_capacity` seed `3115`: `sp2_balanced-capacity_baseline_model-based_decentralized_bnn-capacity-utility_bnn-capacity_seed3115.mp4`
- `balanced_capacity` `cbba_capacity` seed `3110`: `sp2_balanced-capacity_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3110.mp4`
- `balanced_capacity` `centralized_capacity_milp` seed `3119`: `sp2_balanced-capacity_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3119.mp4`
- `balanced_capacity` `greedy_capacity_nearest` seed `3110`: `sp2_balanced-capacity_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3110.mp4`
- `balanced_capacity` `hungarian_capacity` seed `3110`: `sp2_balanced-capacity_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3110.mp4`
- `balanced_capacity` `imitation_capacity` seed `3101`: `sp2_balanced-capacity_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3101.mp4`
- `balanced_capacity` `local_primal_dual_capacity` seed `3120`: `sp2_balanced-capacity_proposed_model-based_decentralized-local_local-primal-dual-effective-capacity_local-primal-dual-capacity_seed3120.mp4`
- `balanced_capacity` `neural_capacity_scorer` seed `3104`: `sp2_balanced-capacity_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3104.mp4`
- `battery_constrained` `bnn_capacity` seed `3110`: `sp2_battery-constrained_baseline_model-based_decentralized_bnn-capacity-utility_bnn-capacity_seed3110.mp4`
- `battery_constrained` `cbba_capacity` seed `3117`: `sp2_battery-constrained_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3117.mp4`
- `battery_constrained` `centralized_capacity_milp` seed `3116`: `sp2_battery-constrained_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3116.mp4`
- `battery_constrained` `greedy_capacity_nearest` seed `3100`: `sp2_battery-constrained_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3100.mp4`
- `battery_constrained` `hungarian_capacity` seed `3114`: `sp2_battery-constrained_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3114.mp4`
- `battery_constrained` `imitation_capacity` seed `3134`: `sp2_battery-constrained_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3134.mp4`
- `battery_constrained` `local_primal_dual_capacity` seed `3112`: `sp2_battery-constrained_proposed_model-based_decentralized-local_local-primal-dual-effective-capacity_local-primal-dual-capacity_seed3112.mp4`
- `battery_constrained` `neural_capacity_scorer` seed `3110`: `sp2_battery-constrained_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3110.mp4`
- `heavy_capacity` `bnn_capacity` seed `3109`: `sp2_heavy-capacity_baseline_model-based_decentralized_bnn-capacity-utility_bnn-capacity_seed3109.mp4`
- `heavy_capacity` `cbba_capacity` seed `3101`: `sp2_heavy-capacity_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3101.mp4`
- `heavy_capacity` `centralized_capacity_milp` seed `3104`: `sp2_heavy-capacity_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3104.mp4`
- `heavy_capacity` `greedy_capacity_nearest` seed `3102`: `sp2_heavy-capacity_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3102.mp4`
- `heavy_capacity` `hungarian_capacity` seed `3112`: `sp2_heavy-capacity_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3112.mp4`
- `heavy_capacity` `imitation_capacity` seed `3109`: `sp2_heavy-capacity_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3109.mp4`
- `heavy_capacity` `local_primal_dual_capacity` seed `3134`: `sp2_heavy-capacity_proposed_model-based_decentralized-local_local-primal-dual-effective-capacity_local-primal-dual-capacity_seed3134.mp4`
- `heavy_capacity` `neural_capacity_scorer` seed `3100`: `sp2_heavy-capacity_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3100.mp4`
- `light_mixed` `bnn_capacity` seed `3104`: `sp2_light-mixed_baseline_model-based_decentralized_bnn-capacity-utility_bnn-capacity_seed3104.mp4`
- `light_mixed` `cbba_capacity` seed `3134`: `sp2_light-mixed_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3134.mp4`
- `light_mixed` `centralized_capacity_milp` seed `3100`: `sp2_light-mixed_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3100.mp4`
- `light_mixed` `greedy_capacity_nearest` seed `3138`: `sp2_light-mixed_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3138.mp4`
- `light_mixed` `hungarian_capacity` seed `3102`: `sp2_light-mixed_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3102.mp4`
- `light_mixed` `imitation_capacity` seed `3115`: `sp2_light-mixed_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3115.mp4`
- `light_mixed` `local_primal_dual_capacity` seed `3120`: `sp2_light-mixed_proposed_model-based_decentralized-local_local-primal-dual-effective-capacity_local-primal-dual-capacity_seed3120.mp4`
- `light_mixed` `neural_capacity_scorer` seed `3125`: `sp2_light-mixed_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3125.mp4`
- `monte_carlo` `bnn_capacity` seed `3133`: `sp2_monte-carlo_baseline_model-based_decentralized_bnn-capacity-utility_bnn-capacity_seed3133.mp4`
- `monte_carlo` `cbba_capacity` seed `3117`: `sp2_monte-carlo_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3117.mp4`
- `monte_carlo` `centralized_capacity_milp` seed `3107`: `sp2_monte-carlo_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3107.mp4`
- `monte_carlo` `greedy_capacity_nearest` seed `3117`: `sp2_monte-carlo_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3117.mp4`
- `monte_carlo` `hungarian_capacity` seed `3108`: `sp2_monte-carlo_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3108.mp4`
- `monte_carlo` `imitation_capacity` seed `3108`: `sp2_monte-carlo_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3108.mp4`
- `monte_carlo` `local_primal_dual_capacity` seed `3126`: `sp2_monte-carlo_proposed_model-based_decentralized-local_local-primal-dual-effective-capacity_local-primal-dual-capacity_seed3126.mp4`
- `monte_carlo` `neural_capacity_scorer` seed `3117`: `sp2_monte-carlo_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3117.mp4`

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/load_status.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `theory_audit.json`
- `figures/sp2_capacity_satisfaction_by_method.png`
- `figures/sp2_capacity_ratio_interaction.png`
- `figures/sp2_performance_matrix_by_method.png`
- `figures/sp2_quality_resource_pareto.png`
- `figures/sp2_capacity_cost_tradeoff.png`
- `figures/sp2_capacity_coverage_vs_completion.png`
- `figures/sp2_communication_radius_degradation.png`
- `figures/sp2_best_method_by_scenario.png`
- `videos/sp2_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`
