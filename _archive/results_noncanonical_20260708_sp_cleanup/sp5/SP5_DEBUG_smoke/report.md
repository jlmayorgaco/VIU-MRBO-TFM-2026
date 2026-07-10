# SP5_DEBUG_smoke

SP5 evaluates cooperative payload transport: AMRs must recruit to payload slots, maintain formation and move a rigid load to a target pose while avoiding static obstacles and moving robot groups.
- Seeds: `6100`-`6101` (`n=2`)
- Scenario generators: `formation_corridor_push, cargo_overhead_delivery, multi_group_crossing_push`

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
| 1 | ours_hamiltonian_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.100 | 0.00 | 0.00 | 690.96 | 0.021 | 587.431 |
| 2 | reference_centralized_mpc_cbf_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.011 | 0.00 | 0.00 | 1032.68 | 0.000 | 2121.429 |
| 3 | sota_centralized_cbf_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.099 | 0.00 | 0.00 | 957.32 | 0.036 | 495.291 |
| 4 | sota_decentralized_vo_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.107 | 0.01 | 0.00 | 1016.97 | 0.046 | 507.067 |
| 5 | ours_tensor_game_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.039 | 4.81 | 0.02 | 967.91 | 1.000 | 1357.792 |
| 6 | classic_centralized_shortest_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.032 | 5.43 | 0.19 | 925.39 | 1.000 | 1148.367 |
| 7 | ours_primal_dual_wrench_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.126 | 5.45 | 1.07 | 769.93 | 1.000 | 1119.020 |
| 8 | sota_decentralized_vo_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.122 | 5.66 | 0.06 | 983.30 | 1.000 | 1203.836 |
| 9 | sota_centralized_cbf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.125 | 5.86 | 0.11 | 955.40 | 1.000 | 1197.841 |
| 10 | classic_decentralized_apf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.345 | 3.92 | 47.50 | 646.25 | 1.000 | 753.957 |

## Theory Audit

- Checks: `60`.
- Failed checks: `0`.
- Safety-margin warnings: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H5_DEBUG_reference_gap | performance_gap_vs_reference | 6 | 0.0156 | 0.0312 | -1.0000 | [-1, -1] | True | ok |
| H5_DEBUG_ours_formation | formation_broken_rate | 6 | 0.2188 | 0.2188 | -0.2442 | [-0.506, 0.01624] | False | ok |

## Scenario Videos

- `cargo_overhead_delivery` `reference_centralized_mpc_cbf_cargo` seed `6100`: `sp5_cargo-overhead-delivery_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6100.mp4`
- `cargo_overhead_delivery` `ours_hamiltonian_cargo` seed `6101`: `sp5_cargo-overhead-delivery_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6101.mp4`
- `formation_corridor_push` `sota_decentralized_vo_cargo` seed `6100`: `sp5_formation-corridor-push_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6100.mp4`
- `formation_corridor_push` `sota_centralized_cbf_cargo` seed `6100`: `sp5_formation-corridor-push_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6100.mp4`
- `multi_group_crossing_push` `ours_hamiltonian_cargo` seed `6100`: `sp5_multi-group-crossing-push_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6100.mp4`
- `multi_group_crossing_push` `reference_centralized_mpc_cbf_cargo` seed `6100`: `sp5_multi-group-crossing-push_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6100.mp4`

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
