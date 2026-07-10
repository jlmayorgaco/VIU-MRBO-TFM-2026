# SP2_MC_marginal_payoff_ablation

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
| capacity_oracle_reference | Pure capacity oracle reference | model_based_oracle | centralized | reference | exact_capacity_coverage_replay | centralized_capacity_ceiling_reference |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_reference_replay | centralized_oracle_reference |
| replicator_capacity_marginal | Replicator capacity marginal payoff | model_based | decentralized | baseline | population_game_marginal_capacity_payoff | sp2_plain_vs_marginal_ablation |
| replicator_capacity_plain | Replicator capacity plain payoff | model_based | decentralized | baseline | population_game_plain_payoff | sp2_plain_vs_marginal_ablation |
| smith_capacity_marginal | Smith-QR capacity marginal payoff | model_based | decentralized | proposed | smith_qr_marginal_capacity_payoff | sp2_plain_vs_marginal_ablation |
| smith_capacity_plain | Smith-QR capacity plain payoff | model_based | decentralized | proposed | smith_qr_plain_payoff | sp2_plain_vs_marginal_ablation |

## Resource Fairness

| Method | Training type | Execution model | Trainable params | Tuned params | Decoder |
|---|---|---|---:|---:|---|
| capacity_oracle_reference | none | centralized_exact_capacity_ceiling_replay | 0 | 2 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 3 | False |
| replicator_capacity_marginal | none | distributed_marginal_capacity_payoff_rule | 0 | 4 | False |
| replicator_capacity_plain | none | distributed_plain_capacity_payoff_rule | 0 | 4 | False |
| smith_capacity_marginal | none | distributed_smith_qr_marginal_payoff_rule | 0 | 4 | False |
| smith_capacity_plain | none | distributed_smith_qr_plain_payoff_rule | 0 | 4 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Under kg | Over kg | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 640 | 0.168 | 0.058 | 0.000 | 0.505 | 0.798 | 0.199 | 198.32 | 1.17 | 63.43 | 384.21 | 13.067 |
| balanced_capacity | oracle_reference | model_based_oracle | centralized | reference | 640 | 0.455 | 0.000 | 0.027 | 0.491 | 0.328 | 0.667 | 203.72 | 4.11 | 66.29 | 401.34 | 45.877 |
| balanced_capacity | replicator_capacity_marginal | model_based | decentralized | baseline | 640 | 0.090 | 0.160 | 0.019 | 0.505 | 0.889 | 0.102 | 198.16 | 2.89 | 61.88 | 375.72 | 0.427 |
| balanced_capacity | replicator_capacity_plain | model_based | decentralized | baseline | 640 | 0.001 | 0.365 | 0.067 | 0.474 | 0.999 | 0.001 | 210.85 | 0.05 | 77.24 | 467.85 | 0.441 |
| balanced_capacity | smith_capacity_marginal | model_based | decentralized | proposed | 640 | 0.068 | 0.166 | 0.016 | 0.506 | 0.922 | 0.072 | 197.59 | 2.02 | 61.16 | 370.82 | 0.446 |
| balanced_capacity | smith_capacity_plain | model_based | decentralized | proposed | 640 | 0.001 | 0.374 | 0.076 | 0.469 | 0.999 | 0.001 | 212.81 | 0.01 | 79.64 | 482.56 | 0.432 |
| battery_constrained | capacity_oracle_reference | model_based_oracle | centralized | reference | 240 | 0.134 | 0.051 | 0.000 | 0.402 | 0.800 | 0.197 | 233.30 | 1.04 | 57.30 | 347.24 | 10.546 |
| battery_constrained | oracle_reference | model_based_oracle | centralized | reference | 240 | 0.391 | 0.000 | 0.033 | 0.388 | 0.312 | 0.682 | 238.10 | 3.50 | 59.80 | 362.15 | 38.804 |
| battery_constrained | replicator_capacity_marginal | model_based | decentralized | baseline | 240 | 0.074 | 0.163 | 0.014 | 0.409 | 0.893 | 0.099 | 230.06 | 2.22 | 52.60 | 317.15 | 0.401 |
| battery_constrained | replicator_capacity_plain | model_based | decentralized | baseline | 240 | 0.000 | 0.415 | 0.065 | 0.380 | 1.000 | 0.000 | 241.32 | 0.00 | 67.52 | 408.87 | 0.390 |
| battery_constrained | smith_capacity_marginal | model_based | decentralized | proposed | 240 | 0.056 | 0.167 | 0.014 | 0.409 | 0.922 | 0.070 | 230.04 | 1.81 | 51.35 | 310.56 | 0.379 |
| battery_constrained | smith_capacity_plain | model_based | decentralized | proposed | 240 | 0.001 | 0.425 | 0.077 | 0.375 | 0.999 | 0.001 | 243.41 | 0.01 | 70.17 | 425.85 | 0.380 |
| heavy_capacity | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.187 | 0.055 | 0.000 | 0.374 | 0.737 | 0.259 | 348.73 | 2.13 | 61.98 | 376.01 | 17.629 |
| heavy_capacity | oracle_reference | model_based_oracle | centralized | reference | 320 | 0.432 | 0.000 | 0.029 | 0.363 | 0.270 | 0.724 | 354.86 | 5.61 | 65.01 | 394.25 | 68.826 |
| heavy_capacity | replicator_capacity_marginal | model_based | decentralized | baseline | 320 | 0.084 | 0.194 | 0.015 | 0.383 | 0.893 | 0.095 | 343.69 | 4.27 | 55.34 | 335.67 | 0.416 |
| heavy_capacity | replicator_capacity_plain | model_based | decentralized | baseline | 320 | 0.000 | 0.544 | 0.077 | 0.349 | 1.000 | 0.000 | 362.96 | 0.00 | 78.19 | 475.38 | 0.430 |
| heavy_capacity | smith_capacity_marginal | model_based | decentralized | proposed | 320 | 0.069 | 0.199 | 0.015 | 0.382 | 0.917 | 0.072 | 344.09 | 3.72 | 54.92 | 333.42 | 0.421 |
| heavy_capacity | smith_capacity_plain | model_based | decentralized | proposed | 320 | 0.000 | 0.551 | 0.087 | 0.344 | 1.000 | 0.000 | 365.24 | 0.00 | 80.48 | 489.26 | 0.413 |
| light_mixed | capacity_oracle_reference | model_based_oracle | centralized | reference | 320 | 0.446 | 0.021 | 0.000 | 0.816 | 0.550 | 0.440 | 36.37 | 5.80 | 50.64 | 304.31 | 9.865 |
| light_mixed | oracle_reference | model_based_oracle | centralized | reference | 320 | 0.672 | 0.000 | 0.028 | 0.795 | 0.260 | 0.729 | 40.30 | 8.83 | 52.03 | 311.74 | 31.325 |
| light_mixed | replicator_capacity_marginal | model_based | decentralized | baseline | 320 | 0.411 | 0.086 | 0.064 | 0.764 | 0.543 | 0.416 | 44.90 | 13.85 | 53.20 | 319.17 | 0.326 |
| light_mixed | replicator_capacity_plain | model_based | decentralized | baseline | 320 | 0.243 | 0.148 | 0.055 | 0.773 | 0.741 | 0.238 | 43.99 | 6.93 | 59.60 | 358.48 | 0.332 |
| light_mixed | smith_capacity_marginal | model_based | decentralized | proposed | 320 | 0.385 | 0.089 | 0.062 | 0.765 | 0.583 | 0.376 | 44.69 | 13.02 | 53.51 | 320.85 | 0.322 |
| light_mixed | smith_capacity_plain | model_based | decentralized | proposed | 320 | 0.229 | 0.159 | 0.063 | 0.766 | 0.759 | 0.221 | 45.27 | 6.46 | 61.71 | 370.85 | 0.312 |
| monte_carlo | capacity_oracle_reference | model_based_oracle | centralized | reference | 40 | 0.283 | 0.063 | 0.000 | 0.606 | 0.700 | 0.295 | 200.92 | 5.98 | 63.82 | 380.77 | 9.114 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 40 | 0.528 | 0.000 | 0.023 | 0.591 | 0.317 | 0.674 | 207.50 | 9.35 | 65.98 | 393.60 | 42.317 |
| monte_carlo | replicator_capacity_marginal | model_based | decentralized | baseline | 40 | 0.223 | 0.148 | 0.048 | 0.576 | 0.764 | 0.209 | 208.19 | 11.70 | 66.68 | 401.65 | 0.449 |
| monte_carlo | replicator_capacity_plain | model_based | decentralized | baseline | 40 | 0.149 | 0.268 | 0.074 | 0.563 | 0.854 | 0.132 | 220.10 | 7.15 | 79.42 | 474.89 | 0.460 |
| monte_carlo | smith_capacity_marginal | model_based | decentralized | proposed | 40 | 0.202 | 0.154 | 0.044 | 0.578 | 0.798 | 0.174 | 207.65 | 11.14 | 65.92 | 397.11 | 0.429 |
| monte_carlo | smith_capacity_plain | model_based | decentralized | proposed | 40 | 0.136 | 0.275 | 0.077 | 0.562 | 0.867 | 0.121 | 220.67 | 6.46 | 80.86 | 484.22 | 0.451 |

## Performance Ranking

Ranking rule: minimize score-oracle gap; then maximize completed-load capacity success; then minimize capacity-ceiling gap, incomplete capacity, under/over capacity, travel, energy, communication, and runtime. Capacity satisfaction is reported as secondary coverage.

Theory-aligned best overall: **oracle_reference** (`reference`).

| Rank | Method | Family | Owner | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Under kg | Over kg | Travel m | Params | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | oracle_reference | model_based_oracle | reference | 0.487 | 0.000 | 0.029 | 0.514 | 0.299 | 206.59 | 5.43 | 62.10 | 0 | 46.420 |
| 2 | capacity_oracle_reference | model_based_oracle | reference | 0.227 | 0.049 | 0.000 | 0.529 | 0.733 | 201.40 | 2.42 | 59.58 | 0 | 12.857 |
| 3 | replicator_capacity_marginal | model_based | baseline | 0.156 | 0.152 | 0.027 | 0.520 | 0.816 | 201.74 | 5.54 | 57.46 | 0 | 0.401 |
| 4 | smith_capacity_marginal | model_based | proposed | 0.135 | 0.157 | 0.026 | 0.521 | 0.848 | 201.53 | 4.83 | 56.93 | 0 | 0.405 |
| 5 | replicator_capacity_plain | model_based | baseline | 0.054 | 0.362 | 0.066 | 0.497 | 0.943 | 212.75 | 1.63 | 72.38 | 0 | 0.409 |
| 6 | smith_capacity_plain | model_based | proposed | 0.051 | 0.372 | 0.076 | 0.492 | 0.946 | 214.62 | 1.50 | 74.71 | 0 | 0.396 |

## Theory Audit

- Checks: `9360`.
- Failed checks: `0`.
- Passed: `True`.
- Potential theorem: `Teorema 2`.
- Potential structure in this experiment: `mixed`.
- Marginal payoff methods: `replicator_capacity_marginal, smith_capacity_marginal, oracle_reference, capacity_oracle_reference`.
- Distance interpretation: `deliverable_capacity_within_finite_operational_horizon`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H_SP2_Marginal_smith_lower_score_gap | optimality_gap_vs_oracle | 1560 | 4.46e-243 | 2.23e-242 | -0.2145 | [-0.2225, -0.2057] | True | ok |
| H_SP2_Marginal_smith_higher_success | capacity_success_rate | 1560 | 8.43e-59 | 8.43e-59 | 0.0838 | [0.07586, 0.09201] | True | ok |
| H_SP2_Marginal_replicator_lower_score_gap | optimality_gap_vs_oracle | 1560 | 2.08e-240 | 8.33e-240 | -0.2103 | [-0.2187, -0.2017] | True | ok |
| H_SP2_Potential_marginal_lower_incomplete_capacity_smith | incomplete_capacity_ratio | 1560 | 3.32e-62 | 9.97e-62 | -0.0982 | [-0.1081, -0.08903] | True | ok |
| H_SP2_Potential_marginal_higher_alignment_smith | served_capacity_alignment | 1560 | 3.56e-59 | 7.11e-59 | 0.0877 | [0.07894, 0.09716] | True | ok |
| H_SP2_Potential_methods_differ | optimality_gap_vs_oracle | 1560 | 0.0000 | 0.0000 | 0.6871 |  | True | ok |

## Scenario Videos

- `balanced_capacity` `replicator_capacity_marginal` seed `3100`: `sp2_balanced-capacity_baseline_model-based_decentralized_population-game-marginal-capacity-payoff_replicator-capacity-marginal_seed3100.mp4`
- `balanced_capacity` `replicator_capacity_plain` seed `3100`: `sp2_balanced-capacity_baseline_model-based_decentralized_population-game-plain-payoff_replicator-capacity-plain_seed3100.mp4`
- `balanced_capacity` `smith_capacity_marginal` seed `3100`: `sp2_balanced-capacity_proposed_model-based_decentralized_smith-qr-marginal-capacity-payoff_smith-capacity-marginal_seed3100.mp4`
- `balanced_capacity` `smith_capacity_plain` seed `3100`: `sp2_balanced-capacity_proposed_model-based_decentralized_smith-qr-plain-payoff_smith-capacity-plain_seed3100.mp4`
- `battery_constrained` `replicator_capacity_marginal` seed `3100`: `sp2_battery-constrained_baseline_model-based_decentralized_population-game-marginal-capacity-payoff_replicator-capacity-marginal_seed3100.mp4`
- `battery_constrained` `replicator_capacity_plain` seed `3100`: `sp2_battery-constrained_baseline_model-based_decentralized_population-game-plain-payoff_replicator-capacity-plain_seed3100.mp4`
- `battery_constrained` `smith_capacity_marginal` seed `3100`: `sp2_battery-constrained_proposed_model-based_decentralized_smith-qr-marginal-capacity-payoff_smith-capacity-marginal_seed3100.mp4`
- `battery_constrained` `smith_capacity_plain` seed `3100`: `sp2_battery-constrained_proposed_model-based_decentralized_smith-qr-plain-payoff_smith-capacity-plain_seed3100.mp4`
- `heavy_capacity` `replicator_capacity_marginal` seed `3100`: `sp2_heavy-capacity_baseline_model-based_decentralized_population-game-marginal-capacity-payoff_replicator-capacity-marginal_seed3100.mp4`
- `heavy_capacity` `replicator_capacity_plain` seed `3100`: `sp2_heavy-capacity_baseline_model-based_decentralized_population-game-plain-payoff_replicator-capacity-plain_seed3100.mp4`
- `heavy_capacity` `smith_capacity_marginal` seed `3100`: `sp2_heavy-capacity_proposed_model-based_decentralized_smith-qr-marginal-capacity-payoff_smith-capacity-marginal_seed3100.mp4`
- `heavy_capacity` `smith_capacity_plain` seed `3100`: `sp2_heavy-capacity_proposed_model-based_decentralized_smith-qr-plain-payoff_smith-capacity-plain_seed3100.mp4`
- `light_mixed` `replicator_capacity_marginal` seed `3100`: `sp2_light-mixed_baseline_model-based_decentralized_population-game-marginal-capacity-payoff_replicator-capacity-marginal_seed3100.mp4`
- `light_mixed` `replicator_capacity_plain` seed `3100`: `sp2_light-mixed_baseline_model-based_decentralized_population-game-plain-payoff_replicator-capacity-plain_seed3100.mp4`
- `light_mixed` `smith_capacity_marginal` seed `3100`: `sp2_light-mixed_proposed_model-based_decentralized_smith-qr-marginal-capacity-payoff_smith-capacity-marginal_seed3100.mp4`
- `light_mixed` `smith_capacity_plain` seed `3100`: `sp2_light-mixed_proposed_model-based_decentralized_smith-qr-plain-payoff_smith-capacity-plain_seed3100.mp4`
- `monte_carlo` `replicator_capacity_marginal` seed `3102`: `sp2_monte-carlo_baseline_model-based_decentralized_population-game-marginal-capacity-payoff_replicator-capacity-marginal_seed3102.mp4`
- `monte_carlo` `replicator_capacity_plain` seed `3100`: `sp2_monte-carlo_baseline_model-based_decentralized_population-game-plain-payoff_replicator-capacity-plain_seed3100.mp4`
- `monte_carlo` `smith_capacity_marginal` seed `3102`: `sp2_monte-carlo_proposed_model-based_decentralized_smith-qr-marginal-capacity-payoff_smith-capacity-marginal_seed3102.mp4`
- `monte_carlo` `smith_capacity_plain` seed `3100`: `sp2_monte-carlo_proposed_model-based_decentralized_smith-qr-plain-payoff_smith-capacity-plain_seed3100.mp4`

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
