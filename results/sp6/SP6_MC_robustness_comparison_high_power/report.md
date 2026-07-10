# SP6_MC_robustness_comparison_high_power

SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.
- Seeds: `7200`-`7449` (`n=250`)
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
| 1 | ours_guarded_wrench_market_recovery | 0.515 | 0.712 | 0.288 | 0.0000 | 0.597 | 0.967 | 45.64 | 1105.87 | 0.011 | 536.932 |
| 2 | primal_dual_recovery | 0.511 | 0.710 | 0.290 | 0.0000 | 0.598 | 0.972 | 45.76 | 1111.82 | 0.045 | 530.025 |
| 3 | reference_resilient_oracle | 0.508 | 0.709 | 0.291 | 0.0000 | 0.596 | 0.967 | 45.77 | 1108.02 | 0.000 | 532.912 |
| 4 | smith_qr_recovery | 0.506 | 0.707 | 0.293 | 0.0000 | 0.582 | 0.972 | 45.89 | 1111.33 | 0.048 | 528.280 |
| 5 | tensor_flow_recovery | 0.500 | 0.703 | 0.297 | 0.0000 | 0.584 | 0.968 | 46.40 | 1105.06 | 0.032 | 536.408 |
| 6 | replicator_repair_recovery | 0.497 | 0.701 | 0.299 | 0.0000 | 0.597 | 0.972 | 46.14 | 1111.54 | 0.052 | 530.582 |
| 7 | cbf_recovery | 0.491 | 0.700 | 0.300 | 0.0000 | 0.595 | 0.972 | 46.61 | 1110.61 | 0.061 | 526.423 |
| 8 | cbba_recovery | 0.488 | 0.696 | 0.304 | 0.0000 | 0.497 | 0.940 | 46.58 | 1080.80 | 0.077 | 534.987 |
| 9 | classic_centralized_replan | 0.486 | 0.696 | 0.304 | 0.0000 | 0.502 | 0.942 | 46.71 | 1072.66 | 0.079 | 550.855 |
| 10 | classic_decentralized_greedy_recovery | 0.473 | 0.689 | 0.311 | 0.0000 | 0.481 | 0.936 | 47.12 | 1067.56 | 0.092 | 540.508 |

## Theory Audit

- Checks: `20000`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H6.1_ours_reduces_lost_load_rate_vs_classic_greedy | lost_load_rate | 2000 | 1.28e-05 | 2.55e-05 | -0.0227 | [-0.03, -0.01546] | True | ok |
| H6.2_ours_improves_completion_vs_smith_qr | task_completion_rate | 2000 | 0.1962 | 0.1962 | 0.0044 | [-0.002, 0.01067] | False | ok |
| H6.3_ours_reduces_reference_gap_vs_cbba | performance_gap_vs_reference | 2000 | 6.86e-93 | 2.06e-92 | -0.0658 | [-0.07484, -0.05678] | True | ok |
| H6.4_recovery_family_differs_on_reference_gap | performance_gap_vs_reference | 2000 | 1.8e-160 | 7.19e-160 | 0.0753 |  | True | ok |

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
