# SP5_MC_cooperative_transport_high_power

SP5 evaluates cooperative payload transport: AMRs must recruit to payload slots, maintain formation and move a rigid load to a target pose while avoiding static obstacles and moving robot groups.
- Seeds: `6200`-`6533` (`n=334`)
- Scenario generators: `formation_corridor_push, cargo_overhead_delivery, multi_group_crossing_push, overactuated_push_drag, scarce_cargo_multi_load, monte_carlo`

## Method Taxonomy

| Method | Label | Family | Scope | Owner | Variant | Mode | Allocator |
|---|---|---|---|---|---|---|---|
| classic_centralized_shortest_push | Classic centralized shortest push | classic | centralized | baseline | shortest_path_push_drag | push_drag | hungarian_slots |
| classic_decentralized_apf_push | Classic decentralized APF push | classic | decentralized | baseline | apf_push_drag | push_drag | greedy_capacity |
| ours_hamiltonian_cargo | Ours Hamiltonian cargo | model_based | decentralized | proposed | hamiltonian_tensor_cargo | cargo | support_dual_wrench_market_guarded |
| ours_primal_dual_wrench_push | Ours primal-dual wrench push | model_based | decentralized | proposed | primal_dual_wrench_formation_push | push_drag | support_dual_wrench_market_guarded |
| ours_tensor_game_push | Ours tensor-game push | model_based | decentralized | proposed | smooth_tensor_game_wrench_push | push_drag | smith_wrench_pairs_guarded |
| reference_centralized_mpc_cbf_cargo | Reference centralized MPC-CBF cargo | model_based_reference | centralized | reference | time_expanded_mpc_cbf_cargo | cargo | wrench_oracle |
| sota_centralized_cbf_cargo | SOTA centralized CBF cargo | sota | centralized | baseline | cbf_overhead_cargo | cargo | wrench_greedy |
| sota_centralized_cbf_push | SOTA centralized CBF push | sota | centralized | baseline | cbf_payload_push_drag | push_drag | wrench_greedy |
| sota_decentralized_vo_cargo | SOTA decentralized VO cargo | sota | decentralized | baseline | velocity_obstacle_cargo | cargo | cbba_wrench_score |
| sota_decentralized_vo_push | SOTA decentralized VO push | sota | decentralized | baseline | velocity_obstacle_push_drag | push_drag | cbba_wrench_score |

## Performance Ranking

| Rank | Method | Mode | Success | Target | Collision | Formation break | Pose m | Pose deg | Energy Wh | Gap | Runtime ms |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | reference_centralized_mpc_cbf_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.014 | 0.00 | 0.00 | 891.07 | 0.000 | 3234.387 |
| 2 | sota_centralized_cbf_cargo | cargo | 0.985 | 1.000 | 0.0000 | 0.048 | 0.00 | 0.00 | 854.08 | 0.027 | 608.930 |
| 3 | sota_decentralized_vo_cargo | cargo | 0.977 | 1.000 | 0.0000 | 0.065 | 0.00 | 0.00 | 842.87 | 0.037 | 633.880 |
| 4 | ours_hamiltonian_cargo | cargo | 0.976 | 1.000 | 0.0000 | 0.057 | 0.00 | 0.00 | 739.28 | 0.031 | 663.889 |
| 5 | classic_centralized_shortest_push | push_drag | 0.035 | 0.035 | 0.0000 | 0.046 | 4.48 | 12.42 | 911.54 | 0.970 | 1140.821 |
| 6 | classic_decentralized_apf_push | push_drag | 0.001 | 0.001 | 0.0000 | 0.197 | 5.31 | 43.78 | 566.91 | 0.999 | 939.157 |
| 7 | ours_tensor_game_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.020 | 5.14 | 2.57 | 918.56 | 1.000 | 1475.002 |
| 8 | ours_primal_dual_wrench_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.065 | 5.68 | 3.23 | 760.91 | 1.000 | 1175.656 |
| 9 | sota_decentralized_vo_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.191 | 5.07 | 24.57 | 920.45 | 1.000 | 1171.974 |
| 10 | sota_centralized_cbf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.174 | 5.58 | 25.92 | 893.04 | 1.000 | 1171.172 |

## Theory Audit

- Checks: `20040`.
- Failed checks: `0`.
- Safety-margin warnings: `698`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H5_1_reference_reduces_gap_vs_classic_apf | performance_gap_vs_reference | 2004 | 0.0000 | 0.0000 | -0.9990 | [-1, -0.9975] | True | ok |
| H5_2_ours_hamiltonian_reduces_formation_break_vs_sota_vo_cargo | formation_broken_rate | 2004 | 0.1077 | 0.2153 | -0.0077 | [-0.01282, -0.00279] | False | ok |
| H5_3_ours_tensor_improves_target_reached_vs_classic_push | target_reached | 2004 | 0.5356 | 0.5356 | -0.000998 | [-0.002495, 0] | False | ok |
| H5_4_methods_differ_transport_score | score_value | 2004 | 0.0000 | 0.0000 | 0.7322 |  | True | ok |

## Scenario Videos


## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/robot_status.csv`
- `tables/trajectory_samples.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `tables/video_catalog.csv`
- `theory_audit.json`
- `figures/sp5_transport_success_by_method.png`
- `figures/sp5_final_pose_error_by_method.png`
- `figures/sp5_formation_error_by_method.png`
- `figures/sp5_collision_rate_by_scenario.png`
- `figures/sp5_quality_resource_pareto.png`
- `figures/sp5_push_drag_vs_cargo.png`
- `videos/VIDEO_INDEX.md`
- `videos/sp5_<scenario>_<owner>_<family>_<scope>_<mode>_<variant>_<method>_seed<seed>.mp4`
