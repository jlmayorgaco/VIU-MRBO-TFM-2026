# SP1_MC_smoke

SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.
- Seeds: `2000`-`2002` (`n=3`)
- Scenario generators: `under_demand, balanced_demand, over_demand, monte_carlo`
- Tuning/training must use disjoint seeds from this Monte Carlo config.

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant | Comparison group |
|---|---|---|---|---|---|---|
| greedy_nearest | Greedy nearest | classic | decentralized | baseline | nearest_greedy | classic_decentralized_baseline |
| imitation_oracle | Data-driven imitation oracle | data_driven | decentralized | baseline | oracle_imitation_linear | data_driven_baseline |
| mappo_recruitment | MAPPO recruitment checkpoint | data_driven | decentralized | proposed | mappo_ctde_quorum_decoder | proposed_data_driven_variation |
| primal_dual_cardinality_capacity | Primal-dual cardinality capacity | model_based | decentralized | proposed | primal_dual_capacity | proposed_model_based_variation |
| primal_dual_wrench_market | Primal-dual wrench market | model_based | decentralized | proposed | primal_dual_wrench_proxy | proposed_model_based_variation |
| centralized_coalition_milp | Centralized coalition oracle | model_based_oracle | centralized | reference | exact_capacity_feasible_coalition | centralized_oracle_reference |
| oracle_reference | Oracle reference | model_based_oracle | centralized | reference | exact_capacity_feasible_reference | centralized_oracle_reference |

## Resource Fairness

Interpret neural/data-driven methods as quality-resource tradeoffs, not as free replacements for compact distributed rules.

| Method | Training type | Execution model | Trainable params | Tuned params | Train episodes | Train seeds | Decoder |
|---|---|---|---:|---:|---:|---:|---|
| greedy_nearest | none | distributed_greedy_rule | 0 | 0 | 0 | 0 | False |
| imitation_oracle | supervised_oracle_imitation | distributed_linear_score_policy | 7 | 1 | 0 | 1000 | False |
| mappo_recruitment | ctde_ppo_with_bc_warm_start | decentralized_neural_actor_with_quorum_decoder | 4674 | 12 | 768 | 1000 | True |
| primal_dual_cardinality_capacity | model_based_tuning_optional | distributed_primal_dual_capacity_rule | 0 | 4 | 0 | 0 | False |
| primal_dual_wrench_market | model_based_tuning_optional | distributed_primal_dual_wrench_rule | 0 | 5 | 0 | 0 | False |
| centralized_coalition_milp | none | centralized_exact_subset_slot_search | 0 | 2 | 0 | 0 | False |
| oracle_reference | none | centralized_exact_reference_replay | 0 | 2 | 0 | 0 | False |

## Summary

| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| balanced_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 12 | 0.889 | 0.938 | 0.417 | 0.333 | 0.000 | 38.68 | 193.41 | 1.435 |
| balanced_demand | greedy_nearest | classic | decentralized | baseline | 12 | 0.889 | 1.000 | 0.000 | 0.000 | 0.082 | 40.47 | 202.36 | 0.147 |
| balanced_demand | imitation_oracle | data_driven | decentralized | baseline | 12 | 0.750 | 0.938 | 0.417 | 0.000 | 0.256 | 34.08 | 170.39 | 0.712 |
| balanced_demand | mappo_recruitment | data_driven | decentralized | proposed | 12 | 0.889 | 0.938 | 0.417 | 0.333 | 0.001 | 38.74 | 193.72 | 8.521 |
| balanced_demand | oracle_reference | model_based_oracle | centralized | reference | 12 | 0.889 | 0.938 | 0.417 | 0.333 | 0.000 | 38.68 | 193.41 | 1.522 |
| balanced_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 12 | 0.861 | 1.000 | 0.000 | 0.000 | 0.169 | 40.92 | 204.62 | 0.702 |
| balanced_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 12 | 0.861 | 1.000 | 0.000 | 0.000 | 0.176 | 41.43 | 207.15 | 0.623 |
| monte_carlo | centralized_coalition_milp | model_based_oracle | centralized | reference | 3 | 0.867 | 0.867 | 2.000 | 0.333 | 0.000 | 35.02 | 175.11 | 9.403 |
| monte_carlo | greedy_nearest | classic | decentralized | baseline | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.059 | 41.39 | 206.93 | 0.351 |
| monte_carlo | imitation_oracle | data_driven | decentralized | baseline | 3 | 0.867 | 0.933 | 1.000 | 0.000 | 0.058 | 41.33 | 206.65 | 0.955 |
| monte_carlo | mappo_recruitment | data_driven | decentralized | proposed | 3 | 0.867 | 0.867 | 2.000 | 0.333 | 0.001 | 35.14 | 175.70 | 38.871 |
| monte_carlo | oracle_reference | model_based_oracle | centralized | reference | 3 | 0.867 | 0.867 | 2.000 | 0.333 | 0.000 | 35.02 | 175.11 | 10.001 |
| monte_carlo | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 3 | 0.800 | 0.933 | 1.000 | 0.000 | 0.217 | 42.79 | 213.97 | 1.031 |
| monte_carlo | primal_dual_wrench_market | model_based | decentralized | proposed | 3 | 0.800 | 0.933 | 1.000 | 0.000 | 0.217 | 42.79 | 213.97 | 1.017 |
| over_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 24 | 0.667 | 0.647 | 3.542 | 0.125 | 0.000 | 36.23 | 181.15 | 2.440 |
| over_demand | greedy_nearest | classic | decentralized | baseline | 24 | 0.469 | 0.721 | 2.750 | 0.000 | 0.536 | 36.57 | 182.84 | 0.142 |
| over_demand | imitation_oracle | data_driven | decentralized | baseline | 24 | 0.406 | 0.704 | 2.917 | 0.000 | 0.623 | 34.07 | 170.37 | 0.768 |
| over_demand | mappo_recruitment | data_driven | decentralized | proposed | 24 | 0.667 | 0.647 | 3.542 | 0.208 | 0.003 | 35.59 | 177.97 | 14.881 |
| over_demand | oracle_reference | model_based_oracle | centralized | reference | 24 | 0.667 | 0.647 | 3.542 | 0.125 | 0.000 | 36.23 | 181.15 | 2.693 |
| over_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 24 | 0.281 | 0.721 | 2.750 | 0.000 | 1.034 | 39.66 | 198.31 | 0.656 |
| over_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 24 | 0.271 | 0.721 | 2.750 | 0.000 | 1.072 | 40.17 | 200.87 | 0.645 |
| under_demand | centralized_coalition_milp | model_based_oracle | centralized | reference | 24 | 1.000 | 1.000 | 0.000 | 0.292 | 0.000 | 21.53 | 107.67 | 2.923 |
| under_demand | greedy_nearest | classic | decentralized | baseline | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.124 | 21.98 | 109.88 | 0.117 |
| under_demand | imitation_oracle | data_driven | decentralized | baseline | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.117 | 21.18 | 105.88 | 0.622 |
| under_demand | mappo_recruitment | data_driven | decentralized | proposed | 24 | 1.000 | 1.000 | 0.000 | 0.250 | 0.000 | 21.22 | 106.08 | 13.144 |
| under_demand | oracle_reference | model_based_oracle | centralized | reference | 24 | 1.000 | 1.000 | 0.000 | 0.292 | 0.000 | 21.53 | 107.67 | 2.822 |
| under_demand | primal_dual_cardinality_capacity | model_based | decentralized | proposed | 24 | 1.000 | 1.000 | 0.000 | 0.250 | 0.010 | 21.53 | 107.67 | 0.497 |
| under_demand | primal_dual_wrench_market | model_based | decentralized | proposed | 24 | 1.000 | 1.000 | 0.000 | 0.250 | 0.010 | 21.53 | 107.67 | 0.406 |

Best raw mean demand satisfaction: **centralized_coalition_milp** on `under_demand`.

## Performance Ranking

Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.

Theory-aligned best overall: **centralized_coalition_milp** (`reference`).

| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| ALL_SCENARIOS | 1 | centralized_coalition_milp | model_based_oracle | reference | 0.847 | 0.846 | 0.000 | 31.04 | 0 | 2.764 |
| ALL_SCENARIOS | 2 | oracle_reference | model_based_oracle | reference | 0.847 | 0.846 | 0.000 | 31.04 | 0 | 2.867 |
| ALL_SCENARIOS | 3 | mappo_recruitment | data_driven | proposed | 0.847 | 0.846 | 0.001 | 30.69 | 4674 | 14.150 |
| ALL_SCENARIOS | 4 | greedy_nearest | classic | baseline | 0.890 | 0.738 | 0.270 | 31.98 | 0 | 0.143 |
| ALL_SCENARIOS | 5 | imitation_oracle | data_driven | baseline | 0.872 | 0.688 | 0.333 | 29.51 | 7 | 0.711 |
| ALL_SCENARIOS | 6 | primal_dual_cardinality_capacity | model_based | proposed | 0.890 | 0.690 | 0.440 | 33.15 | 0 | 0.622 |
| ALL_SCENARIOS | 7 | primal_dual_wrench_market | model_based | proposed | 0.890 | 0.686 | 0.456 | 33.44 | 0 | 0.568 |

## Theory Audit

- Checks: `441`.
- Failed checks: `0`.
- Strict complete-coalition failures: `0`.
- Passed: `True`.

## Scenario Videos

- `balanced_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2001`: `sp1_balanced-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2001.mp4`
- `monte_carlo` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2000`: `sp1_monte-carlo_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2000.mp4`
- `over_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2002`: `sp1_over-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2002.mp4`
- `under_demand` `median` `proposed/data_driven/decentralized` `mappo_recruitment` seed `2001`: `sp1_under-demand_median_proposed_data-driven_decentralized_mappo-ctde-quorum-decoder_mappo-recruitment_seed2001.mp4`

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
