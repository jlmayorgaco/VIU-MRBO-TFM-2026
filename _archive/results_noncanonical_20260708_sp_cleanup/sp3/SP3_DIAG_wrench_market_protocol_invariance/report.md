# SP3_DIAG_wrench_market_protocol_invariance

SP3 evaluates role/slot wrench feasibility: scalar capacity is not sufficient when the load requires a planar force-torque vector.
- Seeds: `4400`-`4429` (`n=30`)
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
| smith_wrench_marginal_guarded | Smith-QR wrench marginal guarded | model_based | decentralized | proposed | smith_qr_delta_rho_guarded_local_repair |
| smith_wrench_pairs_guarded | Smith-QR pair repair guarded | model_based | decentralized | proposed | pair_aware_wrench_guarded_repair |
| support_dual_wrench_market | Residual-support wrench market | model_based | decentralized | proposed | residual_support_wrench_market |
| support_dual_wrench_market_guarded | Residual-support wrench market guarded | model_based | decentralized | proposed | residual_support_guarded_local_repair |
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
| smith_wrench_marginal_guarded | smith | delta_rho_marginal_plus_wrench_abstention_guard | guarded_local_repair_proposal | A |
| smith_wrench_pairs_guarded | smith_pair_repair | pairwise_delta_rho_plus_wrench_abstention_guard | pair_complementarity_repair_proposal | A |
| support_dual_wrench_market | residual_support_market | current_residual_wrench_direction | main_proposal | A |
| support_dual_wrench_market_guarded | residual_support_market | current_residual_wrench_direction_plus_abstention_guard | guarded_local_repair_proposal | A |
| wrench_oracle | oracle | strict_wrench_feasible_score | reference | A |

## Performance Ranking

| Rank | Method | Family | Owner | Coverage | Precision | FP assigned | Feasible residual | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | wrench_oracle | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 126.777 |
| 2 | smith_wrench_pairs_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 152.506 |
| 3 | smith_wrench_marginal_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 37.225 |
| 4 | support_dual_wrench_market_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.001 | 19.596 |
| 5 | smith_wrench_marginal | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 25.960 |
| 6 | bnn_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 28.891 |
| 7 | smith_wrench_deficit | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 28.426 |
| 8 | replicator_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 28.567 |
| 9 | oracle_scalar_assignment | model_based_oracle | reference | 1.000 | 0.500 | 0.500 | 0.000 | 0.094 | 20.646 |
| 10 | hungarian_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.094 | 0.080 |
| 11 | support_dual_wrench_market | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.094 | 8.624 |
| 12 | cbba_slots | sota | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.094 | 25.998 |
| 13 | capacity_greedy_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.100 | 0.244 |

## Theory Audit

- Checks: `4500`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H_DIAG_SP3_scalar_false_positive_positive | false_positive_rate | 180 | 1.2e-19 | 3.6e-19 | 0.5000 | [0.4278, 0.5722] | True | ok |
| H_DIAG_SP3_wrench_signal_lower_gap_than_scalar | optimality_gap_vs_wrench_oracle | 180 | 0.00061 | 0.00061 | -0.0076 | [-0.0119, -0.003636] | True | ok |
| H_DIAG_SP3_guarded_fp_not_worse_than_marginal | fp_given_assigned | 180 | 1.2e-19 | 3.6e-19 | -0.5000 | [-0.5722, -0.4278] | True | ok |
| H_DIAG_SP3_pair_repair_lower_gap_than_marginal | optimality_gap_vs_wrench_oracle | 180 | 3.41e-26 | 1.36e-25 | -0.0923 | [-0.1071, -0.07744] | True | ok |

## Scenario Videos


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
