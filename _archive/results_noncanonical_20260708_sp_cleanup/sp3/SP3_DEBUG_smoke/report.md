# SP3_DEBUG_smoke

SP3 evaluates role/slot wrench feasibility: scalar capacity is not sufficient when the load requires a planar force-torque vector.
- Seeds: `4100`-`4101` (`n=2`)
- Scenario generators: `setup, point_load_degenerate, slot_saturation`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| capacity_greedy_slots | Capacity greedy slots | classic | decentralized | baseline | capacity_greedy_slots |
| cbba_slots | CBBA slots | sota | decentralized | baseline | cbba_slot_wrench_proxy |
| oracle_scalar_assignment | Oracle scalar assignment | model_based_oracle | centralized | reference | exact_scalar_capacity_reference |
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
| capacity_greedy_slots | greedy | scalar_capacity_only | classic_baseline | A |
| cbba_slots | cbba | marginal_wrench_bid | sota_proxy | A |
| oracle_scalar_assignment | oracle | scalar_capacity_only | reference_scalar_false_positive | A |
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
| 1 | wrench_oracle | model_based_oracle | reference | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 16.503 |
| 2 | smith_wrench_pairs_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 45.930 |
| 3 | smith_wrench_marginal_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 15.239 |
| 4 | support_dual_wrench_market_guarded | model_based | proposed | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 8.228 |
| 5 | support_dual_wrench_market | model_based | proposed | 1.000 | 0.667 | 0.333 | 0.000 | 0.074 | 2.949 |
| 6 | capacity_greedy_slots | classic | baseline | 1.000 | 0.667 | 0.333 | 0.000 | 0.074 | 0.171 |
| 7 | oracle_scalar_assignment | model_based_oracle | reference | 1.000 | 0.667 | 0.333 | 0.000 | 0.074 | 0.881 |
| 8 | smith_wrench_deficit | model_based | proposed | 1.000 | 0.667 | 0.333 | 0.000 | 0.075 | 9.707 |
| 9 | smith_wrench_marginal | model_based | proposed | 1.000 | 0.667 | 0.333 | 0.000 | 0.075 | 10.063 |
| 10 | cbba_slots | sota | baseline | 1.000 | 0.667 | 0.333 | 0.000 | 0.075 | 8.261 |

## Theory Audit

- Checks: `114`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H3_DEBUG_scalar_false_positive_positive | false_positive_rate | 6 | 0.2500 | 1.0000 | 0.3333 | [0, 0.6667] | False | ok |
| H3_DEBUG_smith_wrench_lower_residual | wrench_residual_norm | 6 | 1.0000 | 1.0000 | 0.0060 | [0, 0.01803] | False | ok |
| H3_DEBUG_support_dual_lower_residual | wrench_residual_norm | 6 | 1.0000 | 1.0000 | 0.0000 | [0, 0] | False | ok |
| H3_DEBUG_guarded_false_positive_not_worse | false_positive_rate | 6 | 0.2500 | 1.0000 | -0.3333 | [-0.6667, 0] | False | ok |

## Scenario Videos

- `point_load_degenerate` `oracle_scalar_assignment` seed `4100`: `sp3_point-load-degenerate_reference_model-based-oracle_centralized_exact-scalar-capacity-reference_oracle-scalar-assignment_seed4100.mp4`
- `point_load_degenerate` `wrench_oracle` seed `4100`: `sp3_point-load-degenerate_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`
- `point_load_degenerate` `smith_wrench_pairs_guarded` seed `4100`: `sp3_point-load-degenerate_proposed_model-based_decentralized_pair-aware-wrench-guarded-repair_smith-wrench-pairs-guarded_seed4100.mp4`
- `setup` `oracle_scalar_assignment` seed `4100`: `sp3_setup_reference_model-based-oracle_centralized_exact-scalar-capacity-reference_oracle-scalar-assignment_seed4100.mp4`
- `setup` `smith_wrench_marginal` seed `4100`: `sp3_setup_proposed_model-based_decentralized_smith-qr-delta-rho-wrench-marginal_smith-wrench-marginal_seed4100.mp4`
- `setup` `cbba_slots` seed `4100`: `sp3_setup_baseline_sota_decentralized_cbba-slot-wrench-proxy_cbba-slots_seed4100.mp4`
- `slot_saturation` `support_dual_wrench_market_guarded` seed `4100`: `sp3_slot-saturation_proposed_model-based_decentralized_residual-support-guarded-local-repair_support-dual-wrench-market-guarded_seed4100.mp4`
- `slot_saturation` `smith_wrench_marginal_guarded` seed `4100`: `sp3_slot-saturation_proposed_model-based_decentralized_smith-qr-delta-rho-guarded-local-repair_smith-wrench-marginal-guarded_seed4100.mp4`
- `slot_saturation` `wrench_oracle` seed `4100`: `sp3_slot-saturation_reference_model-based-oracle_centralized_exact-role-slot-wrench_wrench-oracle_seed4100.mp4`

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
