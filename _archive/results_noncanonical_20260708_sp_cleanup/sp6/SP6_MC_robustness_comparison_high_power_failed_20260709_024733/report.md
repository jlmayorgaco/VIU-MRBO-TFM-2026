# SP6_MC_robustness_comparison_high_power

SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.
- Seeds: `7200`-`7259` (`n=60`)
- Scenario generators: `communication_radius_decay, robot_dropout_mid_task, battery_depletion_reallocation, blocked_corridor_recovery, infeasible_load_detection, delayed_information_consensus, multi_load_priority_shift, monte_carlo`

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
| 1 | ours_guarded_wrench_market_recovery | 0.556 | 0.731 | 0.269 | 0.0000 | 0.637 | 0.954 | 44.66 | 1119.50 | 0.015 | 422.887 |
| 2 | reference_resilient_oracle | 0.550 | 0.728 | 0.272 | 0.0000 | 0.623 | 0.951 | 44.86 | 1122.75 | 0.000 | 419.563 |
| 3 | primal_dual_recovery | 0.544 | 0.727 | 0.273 | 0.0000 | 0.625 | 0.957 | 44.73 | 1114.56 | 0.045 | 428.306 |
| 4 | smith_qr_recovery | 0.540 | 0.724 | 0.276 | 0.0000 | 0.605 | 0.957 | 44.87 | 1113.74 | 0.048 | 430.546 |
| 5 | replicator_repair_recovery | 0.533 | 0.719 | 0.281 | 0.0000 | 0.617 | 0.956 | 45.19 | 1120.20 | 0.049 | 432.453 |
| 6 | tensor_flow_recovery | 0.531 | 0.720 | 0.280 | 0.0000 | 0.616 | 0.952 | 45.37 | 1115.34 | 0.037 | 427.437 |
| 7 | cbba_recovery | 0.510 | 0.710 | 0.290 | 0.0000 | 0.510 | 0.928 | 45.79 | 1088.18 | 0.085 | 435.586 |
| 8 | cbf_recovery | 0.510 | 0.709 | 0.291 | 0.0000 | 0.613 | 0.956 | 45.68 | 1118.89 | 0.073 | 427.827 |
| 9 | classic_centralized_replan | 0.510 | 0.707 | 0.293 | 0.0000 | 0.510 | 0.927 | 45.87 | 1079.82 | 0.096 | 446.115 |
| 10 | classic_decentralized_greedy_recovery | 0.498 | 0.699 | 0.301 | 0.0000 | 0.482 | 0.921 | 46.17 | 1076.25 | 0.111 | 433.945 |

## Theory Audit

- Checks: `4800`.
- Failed checks: `35`.
- Passed: `False`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H6.1_ours_reduces_lost_load_rate_vs_classic_greedy | lost_load_rate | 480 | 0.0027 | 0.0054 | -0.0326 | [-0.04914, -0.01632] | True | ok |
| H6.2_ours_improves_completion_vs_smith_qr | task_completion_rate | 480 | 0.2279 | 0.2279 | 0.0073 | [-0.00625, 0.02118] | False | ok |
| H6.3_ours_reduces_reference_gap_vs_cbba | performance_gap_vs_reference | 480 | 1.3e-19 | 3.91e-19 | -0.0702 | [-0.09126, -0.04931] | True | ok |
| H6.4_recovery_family_differs_on_reference_gap | performance_gap_vs_reference | 480 | 1.12e-43 | 4.48e-43 | 0.0880 |  | True | ok |

## Scenario Videos


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
