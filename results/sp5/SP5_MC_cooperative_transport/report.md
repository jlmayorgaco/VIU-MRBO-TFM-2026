# SP5_MC_cooperative_transport

SP5 evaluates cooperative payload transport: AMRs must recruit to payload slots, maintain formation and move a rigid load to a target pose while avoiding static obstacles and moving robot groups.
- Seeds: `6100`-`6149` (`n=50`)
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
| 1 | reference_centralized_mpc_cbf_cargo | cargo | 0.997 | 1.000 | 0.0000 | 0.010 | 0.00 | 0.00 | 893.35 | 0.000 | 3052.980 |
| 2 | sota_centralized_cbf_cargo | cargo | 0.990 | 1.000 | 0.0000 | 0.036 | 0.00 | 0.00 | 878.59 | 0.020 | 492.851 |
| 3 | sota_decentralized_vo_cargo | cargo | 0.990 | 1.000 | 0.0000 | 0.048 | 0.00 | 0.00 | 869.62 | 0.026 | 509.619 |
| 4 | ours_hamiltonian_cargo | cargo | 0.970 | 1.000 | 0.0000 | 0.052 | 0.00 | 0.00 | 741.19 | 0.031 | 511.979 |
| 5 | classic_centralized_shortest_push | push_drag | 0.010 | 0.010 | 0.0000 | 0.017 | 4.76 | 6.29 | 917.32 | 0.989 | 1001.017 |
| 6 | ours_tensor_game_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.017 | 5.36 | 2.13 | 920.33 | 0.999 | 1325.721 |
| 7 | ours_primal_dual_wrench_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.063 | 5.69 | 2.80 | 776.24 | 0.999 | 1031.006 |
| 8 | classic_decentralized_apf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.216 | 5.19 | 45.05 | 589.83 | 0.998 | 783.312 |
| 9 | sota_centralized_cbf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.153 | 5.30 | 26.09 | 913.32 | 0.999 | 1050.517 |
| 10 | sota_decentralized_vo_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.169 | 5.18 | 25.65 | 921.13 | 0.999 | 1048.477 |

## Theory Audit

- Checks: `3000`.
- Failed checks: `0`.
- Safety-margin warnings: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H5_1_reference_reduces_gap_vs_classic_apf | performance_gap_vs_reference | 300 | 2.7e-67 | 8.11e-67 | -0.9982 | [-1, -0.9946] | True | ok |
| H5_2_ours_hamiltonian_reduces_formation_break_vs_sota_vo_cargo | formation_broken_rate | 300 | 0.8552 | 1.0000 | 0.0038 | [-0.008426, 0.01516] | False | ok |
| H5_3_ours_tensor_improves_target_reached_vs_classic_push | target_reached | 300 | 0.5000 | 1.0000 | 0.0000 | [0, 0] | False | ok |
| H5_4_methods_differ_transport_score | score_value | 300 | 0.0000 | 0.0000 | 0.7230 |  | True | ok |

## Scenario Videos

- `cargo_overhead_delivery` `reference_centralized_mpc_cbf_cargo` seed `6126`: `sp5_cargo-overhead-delivery_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6126.mp4`
- `cargo_overhead_delivery` `ours_hamiltonian_cargo` seed `6133`: `sp5_cargo-overhead-delivery_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6133.mp4`
- `cargo_overhead_delivery` `sota_centralized_cbf_cargo` seed `6141`: `sp5_cargo-overhead-delivery_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6141.mp4`
- `cargo_overhead_delivery` `sota_decentralized_vo_cargo` seed `6141`: `sp5_cargo-overhead-delivery_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6141.mp4`
- `formation_corridor_push` `reference_centralized_mpc_cbf_cargo` seed `6121`: `sp5_formation-corridor-push_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6121.mp4`
- `formation_corridor_push` `sota_centralized_cbf_cargo` seed `6141`: `sp5_formation-corridor-push_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6141.mp4`
- `formation_corridor_push` `sota_decentralized_vo_cargo` seed `6141`: `sp5_formation-corridor-push_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6141.mp4`
- `formation_corridor_push` `ours_hamiltonian_cargo` seed `6136`: `sp5_formation-corridor-push_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6136.mp4`
- `monte_carlo` `reference_centralized_mpc_cbf_cargo` seed `6148`: `sp5_monte-carlo_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6148.mp4`
- `monte_carlo` `sota_centralized_cbf_cargo` seed `6108`: `sp5_monte-carlo_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6108.mp4`
- `monte_carlo` `sota_decentralized_vo_cargo` seed `6108`: `sp5_monte-carlo_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6108.mp4`
- `monte_carlo` `ours_hamiltonian_cargo` seed `6141`: `sp5_monte-carlo_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6141.mp4`
- `multi_group_crossing_push` `sota_decentralized_vo_cargo` seed `6126`: `sp5_multi-group-crossing-push_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6126.mp4`
- `multi_group_crossing_push` `ours_hamiltonian_cargo` seed `6104`: `sp5_multi-group-crossing-push_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6104.mp4`
- `multi_group_crossing_push` `reference_centralized_mpc_cbf_cargo` seed `6104`: `sp5_multi-group-crossing-push_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6104.mp4`
- `multi_group_crossing_push` `sota_centralized_cbf_cargo` seed `6104`: `sp5_multi-group-crossing-push_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6104.mp4`
- `overactuated_push_drag` `reference_centralized_mpc_cbf_cargo` seed `6125`: `sp5_overactuated-push-drag_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6125.mp4`
- `overactuated_push_drag` `sota_centralized_cbf_cargo` seed `6103`: `sp5_overactuated-push-drag_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6103.mp4`
- `overactuated_push_drag` `sota_decentralized_vo_cargo` seed `6103`: `sp5_overactuated-push-drag_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6103.mp4`
- `overactuated_push_drag` `ours_hamiltonian_cargo` seed `6141`: `sp5_overactuated-push-drag_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6141.mp4`
- `scarce_cargo_multi_load` `reference_centralized_mpc_cbf_cargo` seed `6114`: `sp5_scarce-cargo-multi-load_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6114.mp4`
- `scarce_cargo_multi_load` `ours_hamiltonian_cargo` seed `6129`: `sp5_scarce-cargo-multi-load_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6129.mp4`
- `scarce_cargo_multi_load` `sota_centralized_cbf_cargo` seed `6132`: `sp5_scarce-cargo-multi-load_baseline_sota_centralized_cargo_cbf-overhead-cargo_sota-centralized-cbf-cargo_seed6132.mp4`
- `scarce_cargo_multi_load` `sota_decentralized_vo_cargo` seed `6109`: `sp5_scarce-cargo-multi-load_baseline_sota_decentralized_cargo_velocity-obstacle-cargo_sota-decentralized-vo-cargo_seed6109.mp4`

## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/robot_status.csv`
- `tables/trajectory_samples.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `theory_audit.json`
- `figures/sp5_transport_success_by_method.png`
- `figures/sp5_final_pose_error_by_method.png`
- `figures/sp5_formation_error_by_method.png`
- `figures/sp5_collision_rate_by_scenario.png`
- `figures/sp5_quality_resource_pareto.png`
- `figures/sp5_push_drag_vs_cargo.png`
- `videos/sp5_<scenario>_<owner>_<family>_<scope>_<mode>_<variant>_<method>_seed<seed>.mp4`
