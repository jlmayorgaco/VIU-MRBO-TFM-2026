# SP3_MC_wrench_comparison_methodology_v2

SP3 evaluates role/slot wrench feasibility: scalar capacity is not sufficient when the load requires a planar force-torque vector.
- Seeds: `4100`-`4199` (`n=100`)
- Scenario generators: `point_load_degenerate, bar_torque_pure, one_sided_push, off_center_com, long_payload_slots, slot_saturation`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| bnn_wrench_deficit | BNN wrench deficit | model_based | decentralized | baseline | bnn_wrench_deficit |
| capacity_greedy_slots | Capacity greedy slots | classic | decentralized | baseline | capacity_greedy_slots |
| cbba_slots | CBBA slots | sota | decentralized | baseline | cbba_slot_wrench_proxy |
| hungarian_slots | Hungarian slots | classic | centralized | baseline | hungarian_robot_slot_cost |
| oracle_scalar_assignment | Oracle scalar assignment | model_based_oracle | centralized | reference | exact_scalar_capacity_reference |
| replicator_wrench_deficit | Replicator wrench deficit | model_based | decentralized | baseline | replicator_wrench_deficit |
| smith_wrench_deficit | Smith-QR wrench deficit | model_based | decentralized | proposed | smith_qr_wrench_deficit |
| smith_wrench_marginal | Smith-QR wrench marginal | model_based | decentralized | proposed | smith_qr_delta_rho_wrench_marginal |
| support_dual_wrench_market | Residual-support wrench market | model_based | decentralized | proposed | residual_support_wrench_market |
| wrench_oracle | Wrench oracle | model_based_oracle | centralized | reference | exact_role_slot_wrench |

## Method Design

SP3 separates the dynamic engine from the wrench signal. Replicator, Smith, BNN and CBBA are engines; the contribution is the strict wrench feasibility reference plus wrench-deficit, marginal-rho and residual-support signals.

| Method | Engine | Payoff/signal | Role | Phase |
|---|---|---|---|---|
| bnn_wrench_deficit | bnn | positive_excess_wrench_deficit | engine_ablation | B |
| capacity_greedy_slots | greedy | scalar_capacity_only | classic_baseline | A |
| cbba_slots | cbba | marginal_wrench_bid | sota_proxy | A |
| hungarian_slots | hungarian | robot_slot_cost_only | classic_baseline | A |
| oracle_scalar_assignment | oracle | scalar_capacity_only | reference_scalar_false_positive | A |
| replicator_wrench_deficit | replicator | wrench_deficit_minus_rho | engine_ablation | B |
| smith_wrench_deficit | smith | wrench_deficit_minus_rho | main_proposal | A |
| smith_wrench_marginal | smith | delta_rho_marginal | proposal_ablation | A |
| support_dual_wrench_market | residual_support_market | current_residual_wrench_direction | main_proposal | A |
| wrench_oracle | oracle | strict_wrench_feasible_score | reference | A |

## Performance Ranking

| Rank | Method | Family | Owner | Coverage | Precision | FP assigned | Feasible residual | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | wrench_oracle | model_based_oracle | reference | 1.000 | 0.500 | 0.000 | 0.000 | 0.000 | 137.803 |
| 2 | smith_wrench_marginal | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 27.934 |
| 3 | bnn_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 30.442 |
| 4 | replicator_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 30.487 |
| 5 | smith_wrench_deficit | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 30.567 |
| 6 | oracle_scalar_assignment | model_based_oracle | reference | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 22.023 |
| 7 | hungarian_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 0.087 |
| 8 | cbba_slots | sota | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 27.720 |
| 9 | support_dual_wrench_market | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 9.128 |
| 10 | capacity_greedy_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.101 | 0.273 |

## Theory Audit

- Checks: `11400`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p-value | Effect | Reject | Status |
|---|---|---:|---:|---:|---|---|
| H3_1_scalar_false_positives_rotational_loads | false_positive_rate | 600 | 6.03e-61 | 0.5000 | True | ok |
| H3_2_smith_wrench_lower_residual_than_smith_capacity | wrench_residual_feasible_available | 600 | 0.6435 | 4.01e-19 | False | ok |
| H3_3_capacity_greedy_more_infeasible_assignments_than_support_dual | fp_given_assigned | 600 | 0.5000 | 0.0000 | False | ok |
| H3_4_support_dual_lower_gap_than_cbba | optimality_gap_vs_wrench_oracle | 600 | 0.9942 | 4.52e-05 | False | ok |
| H3_5_methods_differ_wrench_gap | optimality_gap_vs_wrench_oracle | 600 | 2.58e-95 | 0.1096 | True | ok |

## Scenario Videos

- `bar_torque_pure` `hungarian_slots` seed `4100`: `sp3_bar-torque-pure_baseline_classic_centralized_hungarian-robot-slot-cost_hungarian-slots_seed4100.mp4`
- `bar_torque_pure` `oracle_scalar_assignment` seed `4100`: `sp3_bar-torque-pure_reference_model-based-oracle_centralized_exact-scalar-capacity-reference_oracle-scalar-assignment_seed4100.mp4`
- `bar_torque_pure` `smith_wrench_deficit` seed `4100`: `sp3_bar-torque-pure_proposed_model-based_decentralized_smith-qr-wrench-deficit_smith-wrench-deficit_seed4100.mp4`
- `bar_torque_pure` `smith_wrench_marginal` seed `4100`: `sp3_bar-torque-pure_proposed_model-based_decentralized_smith-qr-delta-rho-wrench-marginal_smith-wrench-marginal_seed4100.mp4`
- `long_payload_slots` `hungarian_slots` seed `4100`: `sp3_long-payload-slots_baseline_classic_centralized_hungarian-robot-slot-cost_hungarian-slots_seed4100.mp4`
- `long_payload_slots` `oracle_scalar_assignment` seed `4100`: `sp3_long-payload-slots_reference_model-based-oracle_centralized_exact-scalar-capacity-reference_oracle-scalar-assignment_seed4100.mp4`
- `long_payload_slots` `wrench_oracle` seed `4100`: `sp3_long-payload-slots_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `long_payload_slots` `capacity_greedy_slots` seed `4100`: `sp3_long-payload-slots_baseline_classic_decentralized_capacity-greedy-slots_capacity-greedy-slots_seed4100.mp4`
- `off_center_com` `wrench_oracle` seed `4100`: `sp3_off-center-com_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `off_center_com` `replicator_wrench_deficit` seed `4100`: `sp3_off-center-com_baseline_model-based_decentralized_replicator-wrench-deficit_replicator-wrench-deficit_seed4100.mp4`
- `off_center_com` `smith_wrench_deficit` seed `4100`: `sp3_off-center-com_proposed_model-based_decentralized_smith-qr-wrench-deficit_smith-wrench-deficit_seed4100.mp4`
- `off_center_com` `bnn_wrench_deficit` seed `4100`: `sp3_off-center-com_baseline_model-based_decentralized_bnn-wrench-deficit_bnn-wrench-deficit_seed4100.mp4`
- `one_sided_push` `wrench_oracle` seed `4100`: `sp3_one-sided-push_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `one_sided_push` `cbba_slots` seed `4100`: `sp3_one-sided-push_baseline_sota_decentralized_cbba-slot-wrench-proxy_cbba-slots_seed4100.mp4`
- `one_sided_push` `smith_wrench_marginal` seed `4100`: `sp3_one-sided-push_proposed_model-based_decentralized_smith-qr-delta-rho-wrench-marginal_smith-wrench-marginal_seed4100.mp4`
- `one_sided_push` `capacity_greedy_slots` seed `4100`: `sp3_one-sided-push_baseline_classic_decentralized_capacity-greedy-slots_capacity-greedy-slots_seed4100.mp4`
- `point_load_degenerate` `hungarian_slots` seed `4100`: `sp3_point-load-degenerate_baseline_classic_centralized_hungarian-robot-slot-cost_hungarian-slots_seed4100.mp4`
- `point_load_degenerate` `oracle_scalar_assignment` seed `4100`: `sp3_point-load-degenerate_reference_model-based-oracle_centralized_exact-scalar-capacity-reference_oracle-scalar-assignment_seed4100.mp4`
- `point_load_degenerate` `wrench_oracle` seed `4100`: `sp3_point-load-degenerate_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `point_load_degenerate` `cbba_slots` seed `4100`: `sp3_point-load-degenerate_baseline_sota_decentralized_cbba-slot-wrench-proxy_cbba-slots_seed4100.mp4`
- `slot_saturation` `wrench_oracle` seed `4100`: `sp3_slot-saturation_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `slot_saturation` `capacity_greedy_slots` seed `4100`: `sp3_slot-saturation_baseline_classic_decentralized_capacity-greedy-slots_capacity-greedy-slots_seed4100.mp4`
- `slot_saturation` `support_dual_wrench_market` seed `4100`: `sp3_slot-saturation_proposed_model-based_decentralized_residual-support-wrench-market_support-dual-wrench-market_seed4100.mp4`
- `slot_saturation` `hungarian_slots` seed `4100`: `sp3_slot-saturation_baseline_classic_centralized_hungarian-robot-slot-cost_hungarian-slots_seed4100.mp4`

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/load_status.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `theory_audit.json`
- `figures/sp3_scalar_vs_wrench_success_by_method.png`
- `figures/sp3_false_positive_rate_by_scenario.png`
- `figures/sp3_residual_wrench_by_method.png`
- `figures/sp3_wrench_set_valid_vs_invalid.png`
- `figures/sp3_precision_coverage.png`
- `figures/sp3_complementarity_gain.png`
- `figures/sp3_quality_resource_pareto.png`
- `videos/sp3_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`
