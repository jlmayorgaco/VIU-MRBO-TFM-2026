# SP6_DEBUG_smoke

SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.
- Seeds: `7100`-`7100` (`n=1`)
- Scenario generators: `communication_radius_decay, robot_dropout_mid_task, battery_depletion_reallocation, blocked_corridor_recovery, infeasible_load_detection, delayed_information_consensus, multi_load_priority_shift`

## Method Taxonomy

| Method | Label | Family | Scope | Owner | Variant |
|---|---|---|---|---|---|
| cbba_recovery | CBBA recovery | sota | decentralized | baseline | cbba_recovery_auction |
| cbf_recovery | CBF recovery | sota | centralized | baseline | centralized_cbf_recovery |
| classic_centralized_replan | Classic centralized replanning | classic | centralized | baseline | periodic_global_replan |
| classic_decentralized_greedy_recovery | Classic decentralized greedy recovery | classic | decentralized | baseline | local_greedy_recovery |
| ours_guarded_wrench_market_recovery | Ours guarded wrench-market recovery | model_based | decentralized | proposed | guarded_wrench_market_recovery |
| primal_dual_recovery | Primal-dual recovery | model_based | decentralized | proposed | primal_dual_recovery |
| reference_resilient_oracle | Reference centralized resilient recovery | model_based_reference | centralized | reference | centralized_resilient_recovery |
| replicator_repair_recovery | Replicator repair recovery | model_based | decentralized | proposed | replicator_integer_repair |
| smith_qr_recovery | Smith-QR recovery | model_based | decentralized | proposed | smith_qr_recovery |
| tensor_flow_recovery | Tensor-flow recovery | model_based | decentralized | proposed | tensor_flow_recovery |

## Performance Ranking

| Rank | Method | Success | Completion | Lost | Collision | Infeasible detection | Wrench feasible | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | reference_resilient_oracle | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.954 | 52.68 | 1144.96 | 0.000 | 487.209 |
| 2 | ours_guarded_wrench_market_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.959 | 52.44 | 1145.30 | 0.000 | 471.426 |
| 3 | tensor_flow_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.951 | 53.40 | 1172.63 | 0.001 | 448.655 |
| 4 | replicator_repair_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.714 | 0.892 | 52.50 | 1232.31 | 0.003 | 492.404 |
| 5 | primal_dual_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.714 | 0.889 | 52.04 | 1204.62 | 0.004 | 547.234 |
| 6 | smith_qr_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.896 | 52.50 | 1215.69 | 0.021 | 568.267 |
| 7 | cbf_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.892 | 52.68 | 1235.67 | 0.024 | 477.916 |
| 8 | classic_centralized_replan | 0.429 | 0.667 | 0.333 | 0.0000 | 0.571 | 0.822 | 52.90 | 1222.34 | 0.048 | 556.884 |
| 9 | classic_decentralized_greedy_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.429 | 0.812 | 53.18 | 1199.22 | 0.060 | 533.254 |
| 10 | cbba_recovery | 0.429 | 0.667 | 0.333 | 0.0000 | 0.429 | 0.818 | 53.00 | 1207.41 | 0.062 | 536.161 |

## Theory Audit

- Checks: `70`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H6_DEBUG_ours_reduces_lost_load_vs_classic_greedy | lost_load_rate | 7 | 1.0000 | 1.0000 | 0.0000 | [0, 0] | False | ok |
| H6_DEBUG_ours_improves_completion_vs_smith_qr | task_completion_rate | 7 | 1.0000 | 1.0000 | 0.0000 | [0, 0] | False | ok |
| H6_DEBUG_recovery_family_differs_reference_gap | performance_gap_vs_reference | 7 | 0.0965 | 0.2894 | 0.3016 |  | False | ok |

## Scenario Videos

- `battery_depletion_reallocation` `smith_qr_recovery` seed `7100`: `sp6_battery-depletion-reallocation_proposed_model-based_decentralized_smith-qr-recovery_smith-qr-recovery_seed7100.mp4`
- `blocked_corridor_recovery` `classic_centralized_replan` seed `7100`: `sp6_blocked-corridor-recovery_baseline_classic_centralized_periodic-global-replan_classic-centralized-replan_seed7100.mp4`
- `communication_radius_decay` `primal_dual_recovery` seed `7100`: `sp6_communication-radius-decay_proposed_model-based_decentralized_primal-dual-recovery_primal-dual-recovery_seed7100.mp4`
- `delayed_information_consensus` `ours_guarded_wrench_market_recovery` seed `7100`: `sp6_delayed-information-consensus_proposed_model-based_decentralized_guarded-wrench-market-recovery_ours-guarded-wrench-market-recovery_seed7100.mp4`
- `infeasible_load_detection` `tensor_flow_recovery` seed `7100`: `sp6_infeasible-load-detection_proposed_model-based_decentralized_tensor-flow-recovery_tensor-flow-recovery_seed7100.mp4`
- `multi_load_priority_shift` `reference_resilient_oracle` seed `7100`: `sp6_multi-load-priority-shift_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7100.mp4`
- `robot_dropout_mid_task` `classic_centralized_replan` seed `7100`: `sp6_robot-dropout-mid-task_baseline_classic_centralized_periodic-global-replan_classic-centralized-replan_seed7100.mp4`

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/robot_status.csv`
- `tables/load_status.csv`
- `tables/trajectory_samples.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `tables/video_catalog.csv`
- `theory_audit.json`
- `figures/sp6_recovery_success_by_method.png`
- `figures/sp6_lost_load_degradation_by_scenario.png`
- `figures/sp6_recovery_time_by_method.png`
- `figures/sp6_safety_by_method.png`
- `figures/sp6_communication_resource_pareto.png`
- `figures/sp6_completion_vs_reassignment.png`
- `videos/VIDEO_INDEX.md`
- `videos/sp6_<scenario>_<owner>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`
