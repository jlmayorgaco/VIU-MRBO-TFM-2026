# SP6_MC_explicit_control_law

SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.
- Seeds: `7650`-`7661` (`n=12`)
- Scenario generators: `robot_dropout_mid_task, battery_depletion_reallocation, blocked_corridor_recovery, multi_load_priority_shift, monte_carlo`

## Method Taxonomy

| Method | Label | Family | Scope | Owner | Variant |
|---|---|---|---|---|---|
| cbf_recovery | CBF recovery | sota | centralized | baseline | centralized_cbf_recovery |
| classic_decentralized_greedy_recovery | Classic decentralized greedy recovery | classic | decentralized | baseline | local_greedy_recovery |
| ours_guarded_wrench_market_recovery | Ours guarded wrench-market recovery | model_based | decentralized | proposed | guarded_wrench_market_recovery |
| reference_resilient_oracle | Reference centralized resilient recovery | model_based_reference | centralized | reference | centralized_resilient_recovery |
| smith_qr_recovery | Smith-QR recovery | model_based | decentralized | proposed | smith_qr_recovery |
| tensor_flow_recovery | Tensor-flow recovery | model_based | decentralized | proposed | tensor_flow_recovery |

## Performance Ranking

| Rank | Method | Success | Completion | Lost | Collision | Infeasible detection | Wrench feasible | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | reference_resilient_oracle | 0.317 | 0.589 | 0.411 | 0.0000 | 0.442 | 0.954 | 51.84 | 1062.92 | 0.000 | 553.896 |
| 2 | classic_decentralized_greedy_recovery | 0.300 | 0.581 | 0.419 | 0.0000 | 0.450 | 0.939 | 51.82 | 1071.65 | 0.053 | 550.481 |
| 3 | ours_guarded_wrench_market_recovery | 0.300 | 0.572 | 0.428 | 0.0000 | 0.508 | 0.953 | 52.06 | 1059.05 | 0.017 | 557.654 |
| 4 | smith_qr_recovery | 0.300 | 0.567 | 0.433 | 0.0000 | 0.492 | 0.948 | 51.34 | 1051.52 | 0.041 | 534.031 |
| 5 | cbf_recovery | 0.300 | 0.561 | 0.439 | 0.0000 | 0.442 | 0.954 | 51.61 | 1060.74 | 0.045 | 538.895 |
| 6 | tensor_flow_recovery | 0.267 | 0.567 | 0.433 | 0.0000 | 0.408 | 0.952 | 52.83 | 1056.63 | 0.058 | 552.767 |

## Theory Audit

- Checks: `360`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H6E_1_explicit_ours_reduces_lost_load_vs_classic | lost_load_rate | 60 | 0.5066 | 0.6393 | 0.0083 | [-0.02222, 0.04167] | False | ok |
| H6E_2_explicit_ours_improves_completion_vs_smith | task_completion_rate | 60 | 0.3197 | 0.6393 | 0.0056 | [-0.02236, 0.03333] | False | ok |
| H6E_3_explicit_family_differs | score_value | 60 | 0.000664 | 0.0020 | 0.0807 |  | True | ok |

## Scenario Videos

- `battery_depletion_reallocation` `reference_resilient_oracle` seed `7658`: `sp6_battery-depletion-reallocation_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7658.mp4`
- `blocked_corridor_recovery` `classic_decentralized_greedy_recovery` seed `7652`: `sp6_blocked-corridor-recovery_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7652.mp4`
- `monte_carlo` `cbf_recovery` seed `7661`: `sp6_monte-carlo_baseline_sota_centralized_centralized-cbf-recovery_cbf-recovery_seed7661.mp4`
- `multi_load_priority_shift` `smith_qr_recovery` seed `7652`: `sp6_multi-load-priority-shift_proposed_model-based_decentralized_smith-qr-recovery_smith-qr-recovery_seed7652.mp4`
- `robot_dropout_mid_task` `reference_resilient_oracle` seed `7656`: `sp6_robot-dropout-mid-task_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7656.mp4`

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
