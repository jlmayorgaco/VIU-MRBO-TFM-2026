# SP6_MC_robustness_comparison

SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.
- Seeds: `7100`-`7149` (`n=50`)
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
| 1 | reference_resilient_oracle | 0.115 | 0.194 | 0.806 | 0.0246 | 0.872 | 0.986 | 52.59 | 1697.77 | 0.000 | 322.153 |
| 2 | ours_guarded_wrench_market_recovery | 0.087 | 0.180 | 0.820 | 0.0319 | 0.883 | 0.993 | 52.48 | 1758.34 | 0.157 | 327.152 |
| 3 | tensor_flow_recovery | 0.083 | 0.159 | 0.841 | 0.0328 | 0.900 | 0.991 | 52.54 | 1745.39 | 0.143 | 326.754 |
| 4 | primal_dual_recovery | 0.070 | 0.167 | 0.833 | 0.0367 | 0.903 | 0.988 | 52.51 | 1752.32 | 0.172 | 324.371 |
| 5 | smith_qr_recovery | 0.068 | 0.155 | 0.845 | 0.0355 | 0.900 | 0.981 | 52.50 | 1751.08 | 0.152 | 320.055 |
| 6 | replicator_repair_recovery | 0.068 | 0.149 | 0.851 | 0.0345 | 0.910 | 0.974 | 52.50 | 1752.54 | 0.134 | 320.202 |
| 7 | cbf_recovery | 0.065 | 0.145 | 0.855 | 0.0310 | 0.899 | 0.976 | 52.68 | 1738.11 | 0.127 | 319.250 |
| 8 | classic_centralized_replan | 0.003 | 0.005 | 0.968 | 0.0490 | 0.641 | 0.803 | 53.48 | 1875.66 | 0.325 | 332.045 |
| 9 | classic_decentralized_greedy_recovery | 0.000 | 0.006 | 0.989 | 0.0417 | 0.658 | 0.789 | 54.69 | 1788.96 | 0.269 | 329.985 |
| 10 | cbba_recovery | 0.000 | 0.003 | 0.978 | 0.0479 | 0.642 | 0.825 | 53.90 | 1841.81 | 0.331 | 330.764 |

## Theory Audit

- Checks: `4000`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H6.1_ours_reduces_lost_load_rate_vs_classic_greedy | lost_load_rate | 400 | 1.15e-09 | 2.31e-09 | -0.1692 | [-0.2067, -0.1304] | True | ok |
| H6.2_ours_improves_completion_vs_smith_qr | task_completion_rate | 400 | 0.1463 | 0.1463 | 0.0250 | [0.0075, 0.045] | False | ok |
| H6.3_ours_reduces_reference_gap_vs_cbba | performance_gap_vs_reference | 400 | 6.03e-25 | 1.81e-24 | -0.1740 | [-0.2062, -0.1403] | True | ok |
| H6.4_recovery_family_differs_on_reference_gap | performance_gap_vs_reference | 400 | 1e-68 | 4.01e-68 | 0.1639 |  | True | ok |

## Scenario Videos

- `battery_depletion_reallocation` `classic_decentralized_greedy_recovery` seed `7122`: `sp6_battery-depletion-reallocation_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7122.mp4`
- `battery_depletion_reallocation` `classic_centralized_replan` seed `7149`: `sp6_battery-depletion-reallocation_baseline_classic_centralized_periodic-global-replan_classic-centralized-replan_seed7149.mp4`
- `blocked_corridor_recovery` `primal_dual_recovery` seed `7108`: `sp6_blocked-corridor-recovery_proposed_model-based_decentralized_primal-dual-recovery_primal-dual-recovery_seed7108.mp4`
- `blocked_corridor_recovery` `tensor_flow_recovery` seed `7108`: `sp6_blocked-corridor-recovery_proposed_model-based_decentralized_tensor-flow-recovery_tensor-flow-recovery_seed7108.mp4`
- `communication_radius_decay` `reference_resilient_oracle` seed `7112`: `sp6_communication-radius-decay_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7112.mp4`
- `communication_radius_decay` `cbf_recovery` seed `7105`: `sp6_communication-radius-decay_baseline_sota_centralized_centralized-cbf-recovery_cbf-recovery_seed7105.mp4`
- `delayed_information_consensus` `classic_centralized_replan` seed `7147`: `sp6_delayed-information-consensus_baseline_classic_centralized_periodic-global-replan_classic-centralized-replan_seed7147.mp4`
- `delayed_information_consensus` `cbba_recovery` seed `7147`: `sp6_delayed-information-consensus_baseline_sota_decentralized_cbba-recovery-auction_cbba-recovery_seed7147.mp4`
- `infeasible_load_detection` `ours_guarded_wrench_market_recovery` seed `7112`: `sp6_infeasible-load-detection_proposed_model-based_decentralized_guarded-wrench-market-recovery_ours-guarded-wrench-market-recovery_seed7112.mp4`
- `infeasible_load_detection` `reference_resilient_oracle` seed `7112`: `sp6_infeasible-load-detection_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7112.mp4`
- `monte_carlo` `classic_decentralized_greedy_recovery` seed `7149`: `sp6_monte-carlo_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7149.mp4`
- `monte_carlo` `primal_dual_recovery` seed `7109`: `sp6_monte-carlo_proposed_model-based_decentralized_primal-dual-recovery_primal-dual-recovery_seed7109.mp4`
- `multi_load_priority_shift` `classic_decentralized_greedy_recovery` seed `7135`: `sp6_multi-load-priority-shift_baseline_classic_decentralized_local-greedy-recovery_classic-decentralized-greedy-recovery_seed7135.mp4`
- `multi_load_priority_shift` `tensor_flow_recovery` seed `7103`: `sp6_multi-load-priority-shift_proposed_model-based_decentralized_tensor-flow-recovery_tensor-flow-recovery_seed7103.mp4`
- `robot_dropout_mid_task` `reference_resilient_oracle` seed `7100`: `sp6_robot-dropout-mid-task_reference_model-based-reference_centralized_centralized-resilient-recovery_reference-resilient-oracle_seed7100.mp4`
- `robot_dropout_mid_task` `ours_guarded_wrench_market_recovery` seed `7116`: `sp6_robot-dropout-mid-task_proposed_model-based_decentralized_guarded-wrench-market-recovery_ours-guarded-wrench-market-recovery_seed7116.mp4`

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
