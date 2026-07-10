# SP2_DEBUG_smoke

SP2 evaluates physical effective capacity: which heterogeneous AMRs cover heterogeneous load demand after distance and battery discounts, while communication is tracked separately as observability.
Theory note: because effective capacity is pair-dependent, the plain payoff V_k sigma(D_k-S_k)-g_ik is not generally potential-aligned. The Teorema 2 marginal payoff e_ik V_k sigma(D_k-S_k)-g_ik recovers exact potential structure for fixed E during the decision instant.
- Seeds: `3100`-`3101` (`n=2`)
- Scenario generators: `setup`
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
| hungarian_capacity | Hungarian capacity expanded | classic | centralized | baseline | hungarian_capacity_expanded | classic_centralized_baseline |
| imitation_capacity | Data-driven capacity imitation | data_driven | decentralized | baseline | oracle_capacity_imitation_linear | data_driven_baseline |
| logit_capacity_repair | Logit capacity local repair | model_based | decentralized | proposed | logit_completion_repair | proposed_local_repair_family |
| neural_capacity_scorer | Neural capacity scorer | data_driven | decentralized | proposed | oracle_capacity_neural_scorer | proposed_data_driven_variation |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_reference_replay | centralized_oracle_reference |
| pid_capacity_repair | PID capacity local repair | model_based | decentralized_local | proposed | pid_completion_error_repair | proposed_local_repair_family |
| primal_dual_capacity | Primal-dual capacity | model_based | decentralized | proposed | primal_dual_effective_capacity | proposed_model_based_variation |
| primal_dual_capacity_repair | Primal-dual capacity local repair | model_based | decentralized | proposed | primal_dual_completion_repair | proposed_local_repair_family |
| replicator_capacity_marginal | Replicator capacity marginal payoff | model_based | decentralized | baseline | population_game_marginal_capacity_payoff | sp2_plain_vs_marginal_ablation |
| replicator_capacity_marginal_repair | Replicator marginal capacity local repair | model_based | decentralized | proposed | replicator_marginal_completion_repair | proposed_local_repair_family |
| smith_capacity | Smith-QR capacity | model_based | decentralized | proposed | smith_qr_effective_capacity | proposed_model_based_variation |
| smith_capacity_marginal_repair | Smith-QR marginal capacity local repair | model_based | decentralized | proposed | smith_qr_marginal_completion_repair | proposed_local_repair_family |

## Resource Fairness

| Method | Training type | Execution model | Trainable params | Tuned params | Decoder |
|---|---|---|---:|---:|---|
| bnn_capacity_repair | model_based_tuning_optional | distributed_bnn_capacity_plus_local_repair | 0 | 8 | False |
| capacity_oracle_reference | none | centralized_exact_capacity_ceiling_replay | 0 | 2 | False |
| cbba_capacity | none | distributed_payload_auction_proxy | 0 | 3 | False |
| centralized_capacity_milp | none | centralized_binary_milp_effective_capacity | 0 | 3 | False |
| greedy_capacity_nearest | none | distributed_capacity_greedy_rule | 0 | 0 | False |
| hungarian_capacity | none | centralized_capacity_slot_assignment | 0 | 0 | False |
| imitation_capacity | supervised_oracle_imitation | distributed_linear_capacity_score_policy | 8 | 1 | False |
| logit_capacity_repair | model_based_tuning_optional | distributed_logit_capacity_plus_local_repair | 0 | 8 | False |
| neural_capacity_scorer | supervised_oracle_imitation | distributed_neural_capacity_score_policy | 121 | 3 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 3 | False |
| pid_capacity_repair | model_based_tuning_optional | distributed_pid_capacity_error_plus_local_repair | 0 | 7 | False |
| primal_dual_capacity | model_based_tuning_optional | distributed_primal_dual_capacity_rule | 0 | 5 | False |
| primal_dual_capacity_repair | model_based_tuning_optional | distributed_primal_dual_capacity_plus_local_repair | 0 | 8 | False |
| replicator_capacity_marginal | none | distributed_marginal_capacity_payoff_rule | 0 | 4 | False |
| replicator_capacity_marginal_repair | model_based_tuning_optional | distributed_marginal_capacity_plus_local_repair | 0 | 7 | False |
| smith_capacity | model_based_tuning_optional | distributed_smith_qr_capacity_rule | 0 | 4 | False |
| smith_capacity_marginal_repair | model_based_tuning_optional | distributed_smith_qr_marginal_plus_local_repair | 0 | 7 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Under kg | Over kg | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| setup | bnn_capacity_repair | model_based | decentralized | proposed | 2 | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 0.820 | 7.27 | 7.61 | 32.11 | 205.17 | 3.297 |
| setup | capacity_oracle_reference | model_based_oracle | centralized | reference | 2 | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 0.797 | 2.54 | 5.51 | 30.30 | 191.97 | 3.020 |
| setup | cbba_capacity | sota | decentralized | baseline | 2 | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 0.820 | 7.27 | 7.61 | 32.11 | 205.17 | 0.326 |
| setup | centralized_capacity_milp | model_based_oracle | centralized | reference | 2 | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 0.797 | 2.54 | 5.51 | 30.30 | 191.97 | 5.157 |
| setup | greedy_capacity_nearest | classic | decentralized | baseline | 2 | 0.500 | 0.107 | 0.124 | 0.864 | 0.633 | 0.250 | 24.34 | 28.47 | 30.73 | 196.34 | 0.183 |
| setup | hungarian_capacity | classic | centralized | baseline | 2 | 0.250 | 0.134 | 0.105 | 0.882 | 0.838 | 0.110 | 21.04 | 12.17 | 24.05 | 154.31 | 0.271 |
| setup | imitation_capacity | data_driven | decentralized | baseline | 2 | 0.500 | 0.089 | 0.095 | 0.893 | 0.645 | 0.240 | 19.15 | 28.46 | 27.74 | 179.79 | 5.963 |
| setup | logit_capacity_repair | model_based | decentralized | proposed | 2 | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 0.797 | 2.54 | 5.51 | 30.30 | 191.97 | 6.817 |
| setup | neural_capacity_scorer | data_driven | decentralized | proposed | 2 | 0.500 | 0.089 | 0.095 | 0.893 | 0.645 | 0.240 | 19.15 | 28.46 | 27.74 | 179.79 | 5.427 |
| setup | oracle_reference | model_based_oracle | centralized | reference | 2 | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 0.797 | 2.54 | 5.51 | 30.30 | 191.97 | 9.563 |
| setup | pid_capacity_repair | model_based | decentralized_local | proposed | 2 | 0.500 | 0.001 | 0.000 | 0.985 | 0.198 | 0.797 | 2.61 | 4.49 | 31.05 | 196.44 | 6.694 |
| setup | primal_dual_capacity | model_based | decentralized | proposed | 2 | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 0.797 | 2.54 | 5.51 | 30.30 | 191.97 | 0.418 |
| setup | primal_dual_capacity_repair | model_based | decentralized | proposed | 2 | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 0.820 | 7.27 | 7.61 | 32.11 | 205.17 | 2.944 |
| setup | replicator_capacity_marginal | model_based | decentralized | baseline | 2 | 0.500 | 0.105 | 0.122 | 0.866 | 0.646 | 0.249 | 23.96 | 25.01 | 32.90 | 212.38 | 0.228 |
| setup | replicator_capacity_marginal_repair | model_based | decentralized | proposed | 2 | 0.500 | 0.010 | 0.005 | 0.981 | 0.194 | 0.801 | 3.44 | 4.57 | 31.49 | 201.06 | 7.517 |
| setup | smith_capacity | model_based | decentralized | proposed | 2 | 0.500 | 0.001 | 0.000 | 0.985 | 0.198 | 0.797 | 2.61 | 4.49 | 31.05 | 196.44 | 0.211 |
| setup | smith_capacity_marginal_repair | model_based | decentralized | proposed | 2 | 0.500 | 0.010 | 0.005 | 0.981 | 0.194 | 0.801 | 3.44 | 4.57 | 31.49 | 201.06 | 7.088 |

## Performance Ranking

Ranking rule: minimize score-oracle gap; then maximize completed-load capacity success; then minimize capacity-ceiling gap, incomplete capacity, under/over capacity, travel, energy, communication, and runtime. Capacity satisfaction is reported as secondary coverage.

Theory-aligned best overall: **primal_dual_capacity** (`proposed`).

| Rank | Method | Family | Owner | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Under kg | Over kg | Travel m | Params | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | primal_dual_capacity | model_based | proposed | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 2.54 | 5.51 | 30.30 | 0 | 0.418 |
| 2 | capacity_oracle_reference | model_based_oracle | reference | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 2.54 | 5.51 | 30.30 | 0 | 3.020 |
| 3 | centralized_capacity_milp | model_based_oracle | reference | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 2.54 | 5.51 | 30.30 | 0 | 5.157 |
| 4 | logit_capacity_repair | model_based | proposed | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 2.54 | 5.51 | 30.30 | 0 | 6.817 |
| 5 | oracle_reference | model_based_oracle | reference | 0.500 | 0.000 | 0.000 | 0.986 | 0.197 | 2.54 | 5.51 | 30.30 | 0 | 9.563 |
| 6 | smith_capacity | model_based | proposed | 0.500 | 0.001 | 0.000 | 0.985 | 0.198 | 2.61 | 4.49 | 31.05 | 0 | 0.211 |
| 7 | pid_capacity_repair | model_based | proposed | 0.500 | 0.001 | 0.000 | 0.985 | 0.198 | 2.61 | 4.49 | 31.05 | 0 | 6.694 |
| 8 | smith_capacity_marginal_repair | model_based | proposed | 0.500 | 0.010 | 0.005 | 0.981 | 0.194 | 3.44 | 4.57 | 31.49 | 0 | 7.088 |
| 9 | replicator_capacity_marginal_repair | model_based | proposed | 0.500 | 0.010 | 0.005 | 0.981 | 0.194 | 3.44 | 4.57 | 31.49 | 0 | 7.517 |
| 10 | cbba_capacity | sota | baseline | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 7.27 | 7.61 | 32.11 | 0 | 0.326 |
| 11 | primal_dual_capacity_repair | model_based | proposed | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 7.27 | 7.61 | 32.11 | 0 | 2.944 |
| 12 | bnn_capacity_repair | model_based | proposed | 0.500 | 0.063 | 0.028 | 0.958 | 0.172 | 7.27 | 7.61 | 32.11 | 0 | 3.297 |
| 13 | neural_capacity_scorer | data_driven | proposed | 0.500 | 0.089 | 0.095 | 0.893 | 0.645 | 19.15 | 28.46 | 27.74 | 121 | 5.427 |
| 14 | imitation_capacity | data_driven | baseline | 0.500 | 0.089 | 0.095 | 0.893 | 0.645 | 19.15 | 28.46 | 27.74 | 8 | 5.963 |
| 15 | replicator_capacity_marginal | model_based | baseline | 0.500 | 0.105 | 0.122 | 0.866 | 0.646 | 23.96 | 25.01 | 32.90 | 0 | 0.228 |
| 16 | greedy_capacity_nearest | classic | baseline | 0.500 | 0.107 | 0.124 | 0.864 | 0.633 | 24.34 | 28.47 | 30.73 | 0 | 0.183 |
| 17 | hungarian_capacity | classic | baseline | 0.250 | 0.134 | 0.105 | 0.882 | 0.838 | 21.04 | 12.17 | 24.05 | 0 | 0.271 |

## Theory Audit

- Checks: `34`.
- Failed checks: `0`.
- Passed: `True`.
- Potential theorem: `Teorema 2`.
- Potential structure in this experiment: `mixed`.
- Marginal payoff methods: `centralized_capacity_milp, replicator_capacity_marginal, replicator_capacity_marginal_repair, smith_capacity_marginal_repair, oracle_reference, capacity_oracle_reference`.
- Distance interpretation: `deliverable_capacity_within_finite_operational_horizon`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H01_methods_differ_capacity_gap | optimality_gap_vs_oracle | 2 | 0.1104 | 0.2208 | 0.9412 |  | False | ok |
| H02_primal_dual_capacity_higher_success_than_greedy | capacity_success_rate | 2 | 1.0000 | 1.0000 | 0.0000 | [0, 0] | False | ok |

## Scenario Videos

- `setup` `bnn_capacity_repair` seed `3100`: `sp2_setup_proposed_model-based_decentralized_brown-bnn-completion-repair_bnn-capacity-repair_seed3100.mp4`
- `setup` `cbba_capacity` seed `3100`: `sp2_setup_baseline_sota_decentralized_cbba-payload-capacity-proxy_cbba-capacity_seed3100.mp4`
- `setup` `centralized_capacity_milp` seed `3100`: `sp2_setup_reference_model-based-oracle_centralized_exact-effective-capacity-milp_centralized-capacity-milp_seed3100.mp4`
- `setup` `greedy_capacity_nearest` seed `3100`: `sp2_setup_baseline_classic_decentralized_nearest-capacity-greedy_greedy-capacity-nearest_seed3100.mp4`
- `setup` `hungarian_capacity` seed `3100`: `sp2_setup_baseline_classic_centralized_hungarian-capacity-expanded_hungarian-capacity_seed3100.mp4`
- `setup` `imitation_capacity` seed `3100`: `sp2_setup_baseline_data-driven_decentralized_oracle-capacity-imitation-linear_imitation-capacity_seed3100.mp4`
- `setup` `logit_capacity_repair` seed `3100`: `sp2_setup_proposed_model-based_decentralized_logit-completion-repair_logit-capacity-repair_seed3100.mp4`
- `setup` `neural_capacity_scorer` seed `3100`: `sp2_setup_proposed_data-driven_decentralized_oracle-capacity-neural-scorer_neural-capacity-scorer_seed3100.mp4`

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
