# SP1_DEBUG_smoke

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2000`-`2002` (`n=3`)
- Scenario generators: `setup`
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
| bnn_cardinality_repair | Brown/BNN cardinality local repair | model_based | decentralized | proposed | brown_bnn_positive_excess_with_local_repair | proposed_local_repair_family |
| logit_cardinality_repair | Logit cardinality local repair | model_based | decentralized | proposed | logit_quorum_flow_with_local_repair | proposed_local_repair_family |
| primal_dual_cardinality_capacity | Primal-dual cardinality capacity | model_based | decentralized | proposed | primal_dual_capacity | proposed_model_based_variation |
| primal_dual_wrench_market | Primal-dual wrench market | model_based | decentralized | proposed | primal_dual_wrench_proxy | proposed_model_based_variation |
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
| hungarian_expanded | none | centralized_hungarian_assignment | 0 | 0 | 0 | 0 | False |
| greedy_nearest | none | distributed_greedy_rule | 0 | 0 | 0 | 0 | False |
| imitation_oracle | supervised_oracle_imitation | distributed_linear_score_policy | 7 | 1 | 0 | 1000 | False |
| bnn_cardinality | model_based_tuning_optional | distributed_nonlinear_utility_rule | 0 | 5 | 0 | 0 | False |
| replicator_cardinality | model_based_tuning_optional | distributed_utility_rule | 0 | 4 | 0 | 0 | False |
| cbba | none | distributed_auction_proxy | 0 | 2 | 0 | 0 | False |
| mappo_recruitment | ctde_ppo_with_bc_warm_start | decentralized_neural_actor_with_quorum_decoder | 4674 | 12 | 768 | 1000 | True |
| bnn_cardinality_repair | model_based_tuning_optional | distributed_brown_bnn_positive_excess_plus_local_repair | 0 | 8 | 0 | 0 | False |
| logit_cardinality_repair | model_based_tuning_optional | distributed_logit_quorum_flow_plus_local_repair | 0 | 8 | 0 | 0 | False |
| primal_dual_cardinality_capacity | model_based_tuning_optional | distributed_primal_dual_capacity_rule | 0 | 4 | 0 | 0 | False |
| primal_dual_wrench_market | model_based_tuning_optional | distributed_primal_dual_wrench_rule | 0 | 5 | 0 | 0 | False |
| replicator_cardinality_repair | model_based_tuning_optional | distributed_replicator_plus_local_exact_repair | 0 | 7 | 0 | 0 | False |
| smith_cardinality | model_based_tuning_optional | distributed_smith_qr_rule | 0 | 3 | 0 | 0 | False |
| primal_dual_local_repair | model_based_tuning_optional | distributed_primal_dual_plus_certified_local_repair | 0 | 8 | 0 | 0 | False |
| tensor_quorum_flow_repair | model_based_tuning_optional | smooth_tensor_quorum_flow_plus_certified_local_repair | 0 | 9 | 0 | 0 | False |
| centralized_coalition_milp | none | centralized_exact_subset_slot_search | 0 | 2 | 0 | 0 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 2 | 0 | 0 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| setup | bnn_cardinality | model_based | decentralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.667 | 0.137 | 11.09 | 55.47 | 0.088 |
| setup | bnn_cardinality_repair | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.444 |
| setup | cbba | sota | decentralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.126 |
| setup | centralized_coalition_milp | model_based_oracle | centralized | reference | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.147 |
| setup | greedy_nearest | classic | decentralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.088 |
| setup | hungarian_expanded | classic | centralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.049 |
| setup | imitation_oracle | data_driven | decentralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 3.349 |
| setup | logit_cardinality_repair | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.855 |
| setup | mappo_recruitment | data_driven | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 10.094 |
| setup | oracle_reference | model_based_oracle | centralized | reference | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.179 |
| setup | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.187 |
| setup | primal_dual_local_repair | model_based | decentralized_local | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.360 |
| setup | primal_dual_wrench_market | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.176 |
| setup | replicator_cardinality | model_based | decentralized | baseline | 3 | 1.000 | 1.000 | 0.000 | 0.667 | 0.137 | 11.09 | 55.47 | 0.116 |
| setup | replicator_cardinality_repair | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.718 |
| setup | smith_cardinality | model_based | decentralized | proposed | 3 | 1.000 | 1.000 | 0.000 | 2.000 | 0.567 | 22.14 | 110.72 | 0.050 |
| setup | tensor_quorum_flow_repair | model_based | decentralized_local | proposed | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 7.18 | 35.88 | 0.451 |

Best raw mean demand satisfaction: **bnn_cardinality_repair** on `setup`.

## Performance Ranking

Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.

Theory-aligned best overall: **hungarian_expanded** (`baseline`).

| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| ALL_SCENARIOS | 1 | hungarian_expanded | classic | baseline | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.049 |
| ALL_SCENARIOS | 2 | greedy_nearest | classic | baseline | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.088 |
| ALL_SCENARIOS | 3 | cbba | sota | baseline | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.126 |
| ALL_SCENARIOS | 4 | centralized_coalition_milp | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.147 |
| ALL_SCENARIOS | 5 | primal_dual_wrench_market | model_based | proposed | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.176 |
| ALL_SCENARIOS | 6 | oracle_reference | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.179 |
| ALL_SCENARIOS | 7 | primal_dual_cardinality_capacity | model_based | proposed | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.187 |
| ALL_SCENARIOS | 8 | primal_dual_local_repair | model_based | proposed | 1.000 | 1.000 | 0.000 | 7.18 | 0 | 0.360 |

## Theory Audit

- Checks: `51`.
- Failed checks: `0`.
- Strict complete-coalition failures: `0`.
- Passed: `True`.

## Scenario Videos

- `setup` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2001`: `sp1_setup_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2001.mp4`

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
