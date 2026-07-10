# SP3_MC_wrench_comparison_high_power

SP3 evaluates role/slot wrench feasibility: scalar capacity is not sufficient when the load requires a planar force-torque vector.
- Seeds: `4300`-`4633` (`n=334`)
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
| 1 | wrench_oracle | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 112.796 |
| 2 | smith_wrench_marginal | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 22.894 |
| 3 | replicator_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 25.117 |
| 4 | bnn_wrench_deficit | model_based | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 25.148 |
| 5 | smith_wrench_deficit | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.092 | 25.110 |
| 6 | cbba_slots | sota | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 22.751 |
| 7 | hungarian_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 0.072 |
| 8 | oracle_scalar_assignment | model_based_oracle | reference | 1.000 | 0.500 | 0.500 | 0.000 | 0.093 | 18.558 |
| 9 | support_dual_wrench_market | model_based | proposed | 1.000 | 0.500 | 0.500 | 0.000 | 0.094 | 7.480 |
| 10 | capacity_greedy_slots | classic | baseline | 1.000 | 0.500 | 0.500 | 0.000 | 0.100 | 0.222 |

## Theory Audit

- Checks: `38076`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H3_HP_1_scalar_false_positives_rotational_loads | false_positive_rate | 2004 | 2.12e-198 | 8.47e-198 | 0.5000 | [0.479, 0.5225] | True | ok |
| H3_HP_2_smith_wrench_lower_residual_than_capacity | wrench_residual_feasible_available | 2004 | 0.9865 | 1.0000 | -0.0001 | [-0.0002985, 3.242e-18] | False | ok |
| H3_HP_3_capacity_greedy_more_infeasible_assignments_than_support_dual | fp_given_assigned | 2004 | 0.4644 | 1.0000 | 0.000499 | [0, 0.001497] | False | ok |
| H3_HP_4_support_dual_lower_gap_than_cbba | optimality_gap_vs_wrench_oracle | 2004 | 1.0000 | 1.0000 | 0.000161 | [-0.000154, 0.0004594] | False | ok |
| H3_HP_5_methods_differ_wrench_gap | optimality_gap_vs_wrench_oracle | 2004 | 0.0000 | 0.0000 | 0.1175 |  | True | ok |

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
