# SP2_DIAG_wrench_market_vector_potential_repair

SP2 evaluates physical effective capacity: which heterogeneous AMRs cover heterogeneous load demand after distance and battery discounts, while communication is tracked separately as observability.
Theory note: because effective capacity is pair-dependent, the plain payoff V_k sigma(D_k-S_k)-g_ik is not generally potential-aligned. The Teorema 2 marginal payoff e_ik V_k sigma(D_k-S_k)-g_ik recovers exact potential structure for fixed E during the decision instant.
- Seeds: `3400`-`3419` (`n=20`)
- Scenario generators: `light_mixed, balanced_capacity, heavy_capacity, battery_constrained, monte_carlo`
- Training/tuning seeds must remain disjoint from this Monte Carlo evaluation.
- `oracle_reference` is the score oracle: capacity coverage plus completed-load reward and small physical-cost penalties.
- `capacity_oracle_reference` is the pure physical capacity ceiling used for `effective_feasibility_ratio` and capacity-gap analysis.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| bnn_capacity_repair | Brown/BNN capacity local repair | model_based | decentralized | proposed | brown_bnn_completion_repair | proposed_local_repair_family |
| capacity_oracle_reference | Pure capacity oracle reference | model_based_oracle | centralized | reference | exact_capacity_coverage_replay | centralized_capacity_ceiling_reference |
| cbba_capacity | CBBA capacity auction | sota | decentralized | baseline | cbba_payload_capacity_proxy | sota_decentralized_baseline |
| centralized_capacity_milp | Centralized capacity oracle | model_based_oracle | centralized | reference | exact_effective_capacity_milp | centralized_oracle_reference |
| greedy_capacity_nearest | Greedy capacity nearest | classic | decentralized | baseline | nearest_capacity_greedy | classic_decentralized_baseline |
| logit_capacity_repair | Logit capacity local repair | model_based | decentralized | proposed | logit_completion_repair | proposed_local_repair_family |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_reference_replay | centralized_oracle_reference |
| pid_capacity_repair | PID capacity local repair | model_based | decentralized_local | proposed | pid_completion_error_repair | proposed_local_repair_family |
| primal_dual_capacity_repair | Primal-dual capacity local repair | model_based | decentralized | proposed | primal_dual_completion_repair | proposed_local_repair_family |
| replicator_capacity_marginal | Replicator capacity marginal payoff | model_based | decentralized | baseline | population_game_marginal_capacity_payoff | sp2_plain_vs_marginal_ablation |
| replicator_capacity_marginal_repair | Replicator marginal capacity local repair | model_based | decentralized | proposed | replicator_marginal_completion_repair | proposed_local_repair_family |
| replicator_capacity_plain | Replicator capacity plain payoff | model_based | decentralized | baseline | population_game_plain_payoff | sp2_plain_vs_marginal_ablation |
| smith_capacity_marginal | Smith-QR capacity marginal payoff | model_based | decentralized | proposed | smith_qr_marginal_capacity_payoff | sp2_plain_vs_marginal_ablation |
| smith_capacity_marginal_repair | Smith-QR marginal capacity local repair | model_based | decentralized | proposed | smith_qr_marginal_completion_repair | proposed_local_repair_family |
| smith_capacity_plain | Smith-QR capacity plain payoff | model_based | decentralized | proposed | smith_qr_plain_payoff | sp2_plain_vs_marginal_ablation |

## Resource Fairness

| Method | Training type | Execution model | Trainable params | Tuned params | Decoder |
|---|---|---|---:|---:|---|
| bnn_capacity_repair | model_based_tuning_optional | distributed_bnn_capacity_plus_local_repair | 0 | 8 | False |
| capacity_oracle_reference | none | centralized_exact_capacity_ceiling_replay | 0 | 2 | False |
| cbba_capacity | none | distributed_payload_auction_proxy | 0 | 3 | False |
| centralized_capacity_milp | none | centralized_binary_milp_effective_capacity | 0 | 3 | False |
| greedy_capacity_nearest | none | distributed_capacity_greedy_rule | 0 | 0 | False |
| logit_capacity_repair | model_based_tuning_optional | distributed_logit_capacity_plus_local_repair | 0 | 8 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 3 | False |
| pid_capacity_repair | model_based_tuning_optional | distributed_pid_capacity_error_plus_local_repair | 0 | 7 | False |
| primal_dual_capacity_repair | model_based_tuning_optional | distributed_primal_dual_capacity_plus_local_repair | 0 | 8 | False |
| replicator_capacity_marginal | none | distributed_marginal_capacity_payoff_rule | 0 | 4 | False |
| replicator_capacity_marginal_repair | model_based_tuning_optional | distributed_marginal_capacity_plus_local_repair | 0 | 7 | False |
| replicator_capacity_plain | none | distributed_plain_capacity_payoff_rule | 0 | 4 | False |
| smith_capacity_marginal | none | distributed_smith_qr_marginal_payoff_rule | 0 | 4 | False |
| smith_capacity_marginal_repair | model_based_tuning_optional | distributed_smith_qr_marginal_plus_local_repair | 0 | 7 | False |
| smith_capacity_plain | none | distributed_smith_qr_plain_payoff_rule | 0 | 4 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Under kg | Over kg | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_capacity | bnn_capacity_repair | model_based | decentralized | proposed | 320 | 0.399 | 0.223 | 0.195 | 0.407 | 0.120 | 0.877 | 237.56 | 7.11 | 57.13 | 344.23 | 127.481 |
| balanced_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 640 | 0.170 | 0.058 | 0.000 | 0.501 | 0.781 | 0.216 | 200.49 | 1.30 | 63.15 | 380.73 | 8.805 |
| balanced_capacity | cbba_capacity | sota | decentralized | baseline | 320 | 0.145 | 0.283 | 0.027 | 0.497 | 0.703 | 0.287 | 202.49 | 5.01 | 60.48 | 364.89 | 0.746 |
| balanced_capacity | centralized_capacity_milp | model_based_oracle | centralized | reference | 320 | 0.449 | 0.000 | 0.028 | 0.487 | 0.318 | 0.676 | 206.03 | 4.35 | 66.19 | 398.89 | 34.304 |
| balanced_capacity | greedy_capacity_nearest | classic | decentralized | baseline | 320 | 0.168 | 0.241 | 0.029 | 0.497 | 0.701 | 0.282 | 202.30 | 7.72 | 57.65 | 347.61 | 0.264 |
| balanced_capacity | logit_capacity_repair | model_based | decentralized | proposed | 320 | 0.421 | 0.192 | 0.211 | 0.399 | 0.104 | 0.893 | 240.77 | 7.53 | 57.76 | 348.69 | 108.993 |
| balanced_capacity | oracle_reference | model_based_oracle | centralized | reference | 320 | 0.449 | 0.000 | 0.028 | 0.487 | 0.318 | 0.676 | 206.03 | 4.35 | 66.19 | 398.89 | 34.395 |
| balanced_capacity | pid_capacity_repair | model_based | decentralized_local | proposed | 320 | 0.392 | 0.235 | 0.207 | 0.401 | 0.120 | 0.877 | 240.01 | 6.80 | 58.01 | 349.86 | 139.853 |
| balanced_capacity | primal_dual_capacity_repair | model_based | decentralized | proposed | 320 | 0.389 | 0.234 | 0.202 | 0.403 | 0.125 | 0.872 | 238.95 | 6.84 | 58.30 | 350.75 | 136.297 |
| balanced_capacity | replicator_capacity_marginal | model_based | decentralized | baseline | 320 | 0.085 | 0.161 | 0.018 | 0.501 | 0.890 | 0.101 | 200.54 | 2.95 | 61.94 | 373.51 | 0.328 |
| balanced_capacity | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 320 | 0.426 | 0.190 | 0.216 | 0.396 | 0.098 | 0.900 | 241.32 | 7.60 | 56.65 | 341.52 | 108.251 |
| balanced_capacity | replicator_capacity_plain | model_based | decentralized | baseline | 320 | 0.001 | 0.365 | 0.077 | 0.465 | 0.999 | 0.001 | 215.29 | 0.01 | 79.36 | 478.76 | 0.324 |
| balanced_capacity | smith_capacity_marginal | model_based | decentralized | proposed | 320 | 0.067 | 0.163 | 0.014 | 0.503 | 0.917 | 0.076 | 199.71 | 2.02 | 61.00 | 367.97 | 0.324 |
| balanced_capacity | smith_capacity_marginal_repair | model_based | decentralized | proposed | 320 | 0.425 | 0.189 | 0.223 | 0.393 | 0.101 | 0.896 | 242.41 | 7.98 | 55.55 | 335.55 | 106.288 |
| balanced_capacity | smith_capacity_plain | model_based | decentralized | proposed | 320 | 0.001 | 0.373 | 0.087 | 0.459 | 0.999 | 0.001 | 217.74 | 0.01 | 82.22 | 496.73 | 0.336 |
| battery_constrained | bnn_capacity_repair | model_based | decentralized | proposed | 120 | 0.354 | 0.257 | 0.258 | 0.306 | 0.053 | 0.936 | 264.42 | 5.77 | 42.27 | 254.18 | 62.509 |
| battery_constrained | capacity_oracle_reference | model_based_oracle | centralized | reference | 240 | 0.156 | 0.046 | 0.000 | 0.405 | 0.776 | 0.221 | 227.62 | 1.00 | 54.81 | 329.60 | 7.591 |
| battery_constrained | cbba_capacity | sota | decentralized | baseline | 120 | 0.115 | 0.311 | 0.023 | 0.404 | 0.757 | 0.234 | 227.67 | 4.08 | 49.99 | 300.68 | 0.568 |
| battery_constrained | centralized_capacity_milp | model_based_oracle | centralized | reference | 120 | 0.383 | 0.000 | 0.028 | 0.393 | 0.336 | 0.659 | 231.82 | 2.92 | 57.39 | 345.10 | 26.754 |
| battery_constrained | greedy_capacity_nearest | classic | decentralized | baseline | 120 | 0.127 | 0.281 | 0.030 | 0.401 | 0.743 | 0.239 | 228.35 | 6.08 | 47.90 | 288.72 | 0.244 |
| battery_constrained | logit_capacity_repair | model_based | decentralized | proposed | 120 | 0.365 | 0.237 | 0.275 | 0.299 | 0.052 | 0.938 | 266.97 | 6.41 | 42.37 | 252.85 | 51.751 |
| battery_constrained | oracle_reference | model_based_oracle | centralized | reference | 120 | 0.383 | 0.000 | 0.028 | 0.393 | 0.336 | 0.659 | 231.82 | 2.92 | 57.39 | 345.10 | 27.274 |
| battery_constrained | pid_capacity_repair | model_based | decentralized_local | proposed | 120 | 0.354 | 0.276 | 0.294 | 0.290 | 0.032 | 0.958 | 270.12 | 6.53 | 39.52 | 239.36 | 60.894 |
| battery_constrained | primal_dual_capacity_repair | model_based | decentralized | proposed | 120 | 0.354 | 0.250 | 0.254 | 0.307 | 0.055 | 0.943 | 263.89 | 6.09 | 43.71 | 261.66 | 65.121 |
| battery_constrained | replicator_capacity_marginal | model_based | decentralized | baseline | 120 | 0.073 | 0.154 | 0.018 | 0.406 | 0.900 | 0.092 | 226.61 | 1.89 | 53.57 | 322.44 | 0.284 |
| battery_constrained | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 120 | 0.371 | 0.231 | 0.282 | 0.297 | 0.049 | 0.940 | 268.18 | 6.52 | 42.31 | 251.92 | 50.156 |
| battery_constrained | replicator_capacity_plain | model_based | decentralized | baseline | 120 | 0.000 | 0.413 | 0.076 | 0.377 | 1.000 | 0.000 | 237.71 | 0.00 | 66.84 | 403.46 | 0.282 |
| battery_constrained | smith_capacity_marginal | model_based | decentralized | proposed | 120 | 0.069 | 0.157 | 0.019 | 0.405 | 0.904 | 0.087 | 226.89 | 2.19 | 51.75 | 311.76 | 0.281 |
| battery_constrained | smith_capacity_marginal_repair | model_based | decentralized | proposed | 120 | 0.375 | 0.220 | 0.272 | 0.300 | 0.054 | 0.936 | 267.11 | 6.70 | 42.71 | 255.35 | 48.046 |
| battery_constrained | smith_capacity_plain | model_based | decentralized | proposed | 120 | 0.000 | 0.420 | 0.081 | 0.375 | 1.000 | 0.000 | 238.65 | 0.00 | 68.39 | 413.09 | 0.285 |
| heavy_capacity | bnn_capacity_repair | model_based | decentralized | proposed | 160 | 0.375 | 0.236 | 0.233 | 0.288 | 0.076 | 0.921 | 390.02 | 9.45 | 53.05 | 321.61 | 156.126 |
| heavy_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.187 | 0.051 | 0.000 | 0.374 | 0.747 | 0.249 | 344.12 | 1.90 | 59.96 | 363.90 | 11.659 |
| heavy_capacity | cbba_capacity | sota | decentralized | baseline | 160 | 0.062 | 0.486 | 0.036 | 0.370 | 0.832 | 0.161 | 346.59 | 3.07 | 60.77 | 368.29 | 0.699 |
| heavy_capacity | centralized_capacity_milp | model_based_oracle | centralized | reference | 160 | 0.430 | 0.000 | 0.032 | 0.362 | 0.289 | 0.704 | 350.41 | 5.63 | 63.03 | 382.20 | 54.372 |
| heavy_capacity | greedy_capacity_nearest | classic | decentralized | baseline | 160 | 0.083 | 0.424 | 0.029 | 0.374 | 0.821 | 0.164 | 343.94 | 5.82 | 55.26 | 335.39 | 0.251 |
| heavy_capacity | logit_capacity_repair | model_based | decentralized | proposed | 160 | 0.394 | 0.209 | 0.250 | 0.284 | 0.067 | 0.930 | 393.14 | 10.10 | 50.23 | 303.11 | 104.995 |
| heavy_capacity | oracle_reference | model_based_oracle | centralized | reference | 160 | 0.430 | 0.000 | 0.032 | 0.362 | 0.289 | 0.704 | 350.41 | 5.63 | 63.03 | 382.20 | 54.674 |
| heavy_capacity | pid_capacity_repair | model_based | decentralized_local | proposed | 160 | 0.375 | 0.233 | 0.236 | 0.287 | 0.083 | 0.914 | 390.76 | 9.55 | 53.75 | 325.57 | 157.985 |
| heavy_capacity | primal_dual_capacity_repair | model_based | decentralized | proposed | 160 | 0.377 | 0.229 | 0.227 | 0.291 | 0.087 | 0.910 | 388.57 | 9.45 | 54.61 | 330.82 | 161.197 |
| heavy_capacity | replicator_capacity_marginal | model_based | decentralized | baseline | 160 | 0.093 | 0.186 | 0.017 | 0.380 | 0.878 | 0.108 | 340.23 | 4.41 | 54.14 | 328.62 | 0.312 |
| heavy_capacity | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 160 | 0.392 | 0.213 | 0.242 | 0.286 | 0.071 | 0.926 | 391.35 | 9.69 | 50.69 | 305.89 | 107.101 |
| heavy_capacity | replicator_capacity_plain | model_based | decentralized | baseline | 160 | 0.002 | 0.554 | 0.084 | 0.345 | 0.998 | 0.001 | 359.95 | 0.12 | 77.92 | 472.00 | 0.323 |
| heavy_capacity | smith_capacity_marginal | model_based | decentralized | proposed | 160 | 0.082 | 0.193 | 0.019 | 0.379 | 0.895 | 0.091 | 340.78 | 4.27 | 53.66 | 325.20 | 0.314 |
| heavy_capacity | smith_capacity_marginal_repair | model_based | decentralized | proposed | 160 | 0.388 | 0.226 | 0.255 | 0.281 | 0.055 | 0.943 | 393.89 | 9.97 | 49.35 | 298.24 | 101.705 |
| heavy_capacity | smith_capacity_plain | model_based | decentralized | proposed | 160 | 0.000 | 0.564 | 0.094 | 0.340 | 1.000 | 0.000 | 362.15 | 0.00 | 80.58 | 489.09 | 0.322 |
| light_mixed | bnn_capacity_repair | model_based | decentralized | proposed | 160 | 0.670 | 0.140 | 0.163 | 0.690 | 0.052 | 0.943 | 58.76 | 15.72 | 44.75 | 269.29 | 19.943 |
| light_mixed | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.446 | 0.020 | 0.000 | 0.816 | 0.559 | 0.431 | 36.92 | 5.98 | 52.10 | 314.90 | 8.670 |
| light_mixed | cbba_capacity | sota | decentralized | baseline | 160 | 0.531 | 0.123 | 0.075 | 0.757 | 0.310 | 0.653 | 46.38 | 20.23 | 48.21 | 291.37 | 0.559 |
| light_mixed | centralized_capacity_milp | model_based_oracle | centralized | reference | 160 | 0.662 | 0.000 | 0.023 | 0.799 | 0.271 | 0.716 | 40.22 | 9.13 | 51.95 | 314.07 | 30.132 |
| light_mixed | greedy_capacity_nearest | classic | decentralized | baseline | 160 | 0.540 | 0.133 | 0.105 | 0.730 | 0.294 | 0.659 | 50.79 | 23.74 | 48.54 | 293.60 | 0.242 |
| light_mixed | logit_capacity_repair | model_based | decentralized | proposed | 160 | 0.679 | 0.134 | 0.181 | 0.678 | 0.047 | 0.950 | 61.72 | 15.25 | 47.54 | 287.25 | 19.927 |
| light_mixed | oracle_reference | model_based_oracle | centralized | reference | 160 | 0.662 | 0.000 | 0.023 | 0.799 | 0.271 | 0.716 | 40.22 | 9.13 | 51.95 | 314.07 | 30.340 |
| light_mixed | pid_capacity_repair | model_based | decentralized_local | proposed | 160 | 0.670 | 0.133 | 0.151 | 0.703 | 0.061 | 0.934 | 56.96 | 14.97 | 46.50 | 279.67 | 21.881 |
| light_mixed | primal_dual_capacity_repair | model_based | decentralized | proposed | 160 | 0.671 | 0.132 | 0.150 | 0.701 | 0.063 | 0.932 | 57.08 | 15.21 | 45.83 | 275.41 | 22.938 |
| light_mixed | replicator_capacity_marginal | model_based | decentralized | baseline | 160 | 0.414 | 0.081 | 0.059 | 0.768 | 0.546 | 0.416 | 44.70 | 13.13 | 53.92 | 326.18 | 0.273 |
| light_mixed | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 160 | 0.679 | 0.133 | 0.186 | 0.674 | 0.049 | 0.947 | 62.18 | 15.39 | 47.32 | 285.93 | 18.809 |
| light_mixed | replicator_capacity_plain | model_based | decentralized | baseline | 160 | 0.233 | 0.144 | 0.058 | 0.771 | 0.748 | 0.230 | 44.38 | 6.64 | 60.66 | 368.76 | 0.293 |
| light_mixed | smith_capacity_marginal | model_based | decentralized | proposed | 160 | 0.390 | 0.085 | 0.058 | 0.768 | 0.580 | 0.382 | 44.52 | 12.30 | 54.26 | 328.95 | 0.280 |
| light_mixed | smith_capacity_marginal_repair | model_based | decentralized | proposed | 160 | 0.677 | 0.133 | 0.186 | 0.673 | 0.053 | 0.943 | 61.90 | 14.80 | 46.72 | 282.76 | 18.229 |
| light_mixed | smith_capacity_plain | model_based | decentralized | proposed | 160 | 0.227 | 0.154 | 0.069 | 0.762 | 0.757 | 0.222 | 46.08 | 6.06 | 63.62 | 386.73 | 0.289 |
| monte_carlo | bnn_capacity_repair | model_based | decentralized | proposed | 20 | 0.507 | 0.129 | 0.119 | 0.571 | 0.200 | 0.795 | 156.69 | 12.31 | 59.61 | 364.16 | 70.071 |
| monte_carlo | capacity_oracle_reference | model_based_oracle | centralized | reference | 40 | 0.350 | 0.041 | 0.000 | 0.632 | 0.628 | 0.369 | 134.83 | 5.26 | 62.36 | 383.30 | 15.767 |
| monte_carlo | cbba_capacity | sota | decentralized | baseline | 20 | 0.372 | 0.205 | 0.056 | 0.603 | 0.479 | 0.504 | 142.25 | 17.34 | 59.14 | 363.90 | 0.684 |
| monte_carlo | centralized_capacity_milp | model_based_oracle | centralized | reference | 20 | 0.578 | 0.000 | 0.033 | 0.613 | 0.253 | 0.744 | 140.66 | 7.30 | 64.76 | 393.70 | 44.156 |
| monte_carlo | greedy_capacity_nearest | classic | decentralized | baseline | 20 | 0.357 | 0.190 | 0.055 | 0.602 | 0.509 | 0.463 | 142.64 | 19.14 | 58.82 | 361.47 | 0.224 |
| monte_carlo | logit_capacity_repair | model_based | decentralized | proposed | 20 | 0.536 | 0.115 | 0.149 | 0.546 | 0.163 | 0.833 | 163.82 | 13.56 | 61.77 | 376.80 | 69.420 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 20 | 0.578 | 0.000 | 0.033 | 0.613 | 0.253 | 0.744 | 140.66 | 7.30 | 64.76 | 393.70 | 46.371 |
| monte_carlo | pid_capacity_repair | model_based | decentralized_local | proposed | 20 | 0.492 | 0.188 | 0.207 | 0.518 | 0.171 | 0.776 | 175.84 | 14.72 | 47.76 | 289.99 | 104.679 |
| monte_carlo | primal_dual_capacity_repair | model_based | decentralized | proposed | 20 | 0.517 | 0.134 | 0.112 | 0.578 | 0.214 | 0.783 | 154.40 | 12.14 | 57.09 | 353.38 | 84.696 |
| monte_carlo | replicator_capacity_marginal | model_based | decentralized | baseline | 20 | 0.259 | 0.129 | 0.042 | 0.609 | 0.715 | 0.263 | 140.49 | 10.14 | 69.26 | 427.25 | 0.280 |
| monte_carlo | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 20 | 0.536 | 0.115 | 0.149 | 0.546 | 0.163 | 0.833 | 163.82 | 13.89 | 62.10 | 377.06 | 80.618 |
| monte_carlo | replicator_capacity_plain | model_based | decentralized | baseline | 20 | 0.165 | 0.265 | 0.061 | 0.597 | 0.829 | 0.161 | 146.77 | 5.56 | 81.40 | 490.37 | 0.291 |
| monte_carlo | smith_capacity_marginal | model_based | decentralized | proposed | 20 | 0.239 | 0.136 | 0.035 | 0.614 | 0.744 | 0.235 | 139.60 | 11.53 | 65.15 | 400.50 | 0.323 |
| monte_carlo | smith_capacity_marginal_repair | model_based | decentralized | proposed | 20 | 0.536 | 0.164 | 0.191 | 0.539 | 0.113 | 0.833 | 166.14 | 15.04 | 58.32 | 352.49 | 80.574 |
| monte_carlo | smith_capacity_plain | model_based | decentralized | proposed | 20 | 0.115 | 0.281 | 0.068 | 0.592 | 0.882 | 0.106 | 148.04 | 5.18 | 83.86 | 509.62 | 0.304 |

## Performance Ranking

Ranking rule: minimize score-oracle gap; then maximize completed-load capacity success; then minimize capacity-ceiling gap, incomplete capacity, under/over capacity, travel, energy, communication, and runtime. Capacity satisfaction is reported as secondary coverage.

Theory-aligned best overall: **centralized_capacity_milp** (`reference`).

| Rank | Method | Family | Owner | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Under kg | Over kg | Travel m | Params | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | centralized_capacity_milp | model_based_oracle | reference | 0.482 | 0.000 | 0.028 | 0.514 | 0.303 | 203.93 | 5.45 | 61.23 | 0 | 36.656 |
| 2 | oracle_reference | model_based_oracle | reference | 0.482 | 0.000 | 0.028 | 0.514 | 0.303 | 203.93 | 5.45 | 61.23 | 0 | 36.934 |
| 3 | capacity_oracle_reference | model_based_oracle | reference | 0.233 | 0.047 | 0.000 | 0.528 | 0.724 | 198.89 | 2.44 | 58.93 | 0 | 9.354 |
| 4 | replicator_capacity_marginal | model_based | baseline | 0.156 | 0.148 | 0.027 | 0.519 | 0.814 | 199.70 | 5.36 | 57.60 | 0 | 0.305 |
| 5 | smith_capacity_marginal | model_based | proposed | 0.141 | 0.151 | 0.026 | 0.520 | 0.837 | 199.45 | 4.86 | 56.79 | 0 | 0.306 |
| 6 | replicator_capacity_marginal_repair | model_based | proposed | 0.465 | 0.187 | 0.223 | 0.419 | 0.076 | 237.49 | 9.62 | 51.45 | 0 | 80.022 |
| 7 | logit_capacity_repair | model_based | proposed | 0.463 | 0.188 | 0.221 | 0.421 | 0.078 | 237.35 | 9.62 | 51.85 | 0 | 80.082 |
| 8 | smith_capacity_marginal_repair | model_based | proposed | 0.464 | 0.189 | 0.229 | 0.417 | 0.075 | 238.30 | 9.77 | 50.56 | 0 | 77.665 |
| 9 | bnn_capacity_repair | model_based | proposed | 0.445 | 0.212 | 0.204 | 0.429 | 0.089 | 234.22 | 9.28 | 51.53 | 0 | 99.830 |
| 10 | primal_dual_capacity_repair | model_based | proposed | 0.442 | 0.212 | 0.202 | 0.431 | 0.096 | 234.00 | 9.12 | 52.71 | 0 | 105.878 |
| 11 | pid_capacity_repair | model_based | proposed | 0.442 | 0.219 | 0.215 | 0.425 | 0.088 | 236.37 | 9.20 | 51.67 | 0 | 106.324 |
| 12 | greedy_capacity_nearest | classic | baseline | 0.226 | 0.261 | 0.046 | 0.508 | 0.644 | 202.75 | 10.66 | 53.82 | 0 | 0.253 |
| 13 | cbba_capacity | sota | baseline | 0.208 | 0.294 | 0.039 | 0.513 | 0.651 | 202.35 | 7.91 | 56.37 | 0 | 0.669 |
| 14 | replicator_capacity_plain | model_based | baseline | 0.053 | 0.363 | 0.074 | 0.493 | 0.943 | 211.60 | 1.53 | 73.35 | 0 | 0.310 |
| 15 | smith_capacity_plain | model_based | proposed | 0.050 | 0.372 | 0.083 | 0.487 | 0.947 | 213.58 | 1.38 | 75.98 | 0 | 0.314 |

## Theory Audit

- Checks: `12480`.
- Failed checks: `0`.
- Passed: `True`.
- Potential theorem: `Teorema 2`.
- Potential structure in this experiment: `mixed`.
- Marginal payoff methods: `centralized_capacity_milp, capacity_oracle_reference, replicator_capacity_marginal, replicator_capacity_marginal_repair, smith_capacity_marginal, smith_capacity_marginal_repair, oracle_reference`.
- Distance interpretation: `deliverable_capacity_within_finite_operational_horizon`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H_DIAG_SP2_marginal_smith_lower_score_gap | optimality_gap_vs_oracle | 780 | 2.57e-124 | 7.7e-124 | -0.2207 | [-0.2325, -0.2089] | True | ok |
| H_DIAG_SP2_smith_repair_lower_score_gap_than_marginal | optimality_gap_vs_oracle | 780 | 1.0000 | 1.0000 | 0.0378 | [0.02724, 0.04833] | False | ok |
| H_DIAG_SP2_repair_methods_differ | optimality_gap_vs_oracle | 780 | 0.0057 | 0.0113 | 0.0042 |  | True | ok |

## Scenario Videos


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
