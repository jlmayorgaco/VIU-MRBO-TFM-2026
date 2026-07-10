# SP5_MC_explicit_control_law

SP5 evaluates cooperative payload transport: AMRs must recruit to payload slots, maintain formation and move a rigid load to a target pose while avoiding static obstacles and moving robot groups.
- Seeds: `6650`-`6661` (`n=12`)
- Scenario generators: `formation_corridor_push, multi_group_crossing_push, overactuated_push_drag, monte_carlo`

## Method Taxonomy

| Method | Label | Family | Scope | Owner | Variant | Mode | Allocator |
|---|---|---|---|---|---|---|---|
| classic_decentralized_apf_push | Classic decentralized APF push | classic | decentralized | baseline | apf_push_drag | push_drag | greedy_capacity |
| ours_explicit_vgne_cbf_cargo | Ours explicit vGNE-CBF cargo | model_based | decentralized | proposed | closed_form_explicit_vgne_cbf_cargo | cargo | support_dual_wrench_market_guarded |
| ours_explicit_vgne_cbf_push | Ours explicit vGNE-CBF push | model_based | decentralized | proposed | closed_form_explicit_vgne_cbf_push | push_drag | support_dual_wrench_market_guarded |
| ours_hamiltonian_cargo | Ours Hamiltonian cargo | model_based | decentralized | proposed | hamiltonian_tensor_cargo | cargo | support_dual_wrench_market_guarded |
| ours_tensor_game_push | Ours tensor-game push | model_based | decentralized | proposed | smooth_tensor_game_wrench_push | push_drag | smith_wrench_pairs_guarded |
| reference_centralized_mpc_cbf_cargo | Reference centralized MPC-CBF cargo | model_based_reference | centralized | reference | time_expanded_mpc_cbf_cargo | cargo | wrench_oracle |
| sota_centralized_cbf_push | SOTA centralized CBF push | sota | centralized | baseline | cbf_payload_push_drag | push_drag | wrench_greedy |
| sota_decentralized_vo_cargo | SOTA decentralized VO cargo | sota | decentralized | baseline | velocity_obstacle_cargo | cargo | cbba_wrench_score |
| sota_decentralized_vo_push | SOTA decentralized VO push | sota | decentralized | baseline | velocity_obstacle_push_drag | push_drag | cbba_wrench_score |

## Performance Ranking

| Rank | Method | Mode | Success | Target | Collision | Formation break | Pose m | Pose deg | Energy Wh | Gap | Runtime ms |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | reference_centralized_mpc_cbf_cargo | cargo | 1.000 | 1.000 | 0.0000 | 0.006 | 0.00 | 0.00 | 931.53 | 0.000 | 4528.716 |
| 2 | sota_decentralized_vo_cargo | cargo | 0.979 | 1.000 | 0.0000 | 0.038 | 0.00 | 0.00 | 890.59 | 0.024 | 594.970 |
| 3 | ours_explicit_vgne_cbf_cargo | cargo | 0.896 | 1.000 | 0.0000 | 0.098 | 0.00 | 0.00 | 678.74 | 0.098 | 726.778 |
| 4 | ours_hamiltonian_cargo | cargo | 0.896 | 1.000 | 0.0000 | 0.102 | 0.00 | 0.00 | 729.84 | 0.099 | 636.406 |
| 5 | ours_explicit_vgne_cbf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.104 | 4.91 | 0.23 | 767.24 | 1.000 | 1120.958 |
| 6 | ours_tensor_game_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.018 | 5.53 | 0.00 | 886.67 | 1.000 | 1513.667 |
| 7 | sota_decentralized_vo_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.082 | 5.18 | 1.27 | 920.65 | 1.000 | 1181.584 |
| 8 | sota_centralized_cbf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.060 | 6.14 | 3.79 | 823.62 | 1.000 | 1182.083 |
| 9 | classic_decentralized_apf_push | push_drag | 0.000 | 0.000 | 0.0000 | 0.332 | 5.67 | 67.46 | 550.26 | 1.000 | 951.455 |

## Theory Audit

- Checks: `432`.
- Failed checks: `0`.
- Safety-margin warnings: `10`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H5E_1_explicit_cargo_improves_target_reached_vs_classic_apf | target_reached | 48 | 2.13e-12 | 4.26e-12 | 1.0000 | [1, 1] | True | ok |
| H5E_2_explicit_cargo_reduces_position_error_vs_sota_vo_cargo | final_position_error_m | 48 | 3.55e-15 | 1.07e-14 | -0.000753 | [-0.0009367, -0.0005757] | True | ok |
| H5E_3_explicit_push_reduces_wrench_residual_vs_tensor | mean_wrench_residual_norm | 48 | 1.0000 | 1.0000 | 0.2485 | [0.2175, 0.2789] | False | ok |
| H5E_4_explicit_family_differs | score_value | 48 | 1.06e-52 | 4.25e-52 | 0.7778 |  | True | ok |

## Scenario Videos

- `formation_corridor_push` `reference_centralized_mpc_cbf_cargo` seed `6651`: `sp5_formation-corridor-push_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6651.mp4`
- `monte_carlo` `reference_centralized_mpc_cbf_cargo` seed `6661`: `sp5_monte-carlo_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6661.mp4`
- `multi_group_crossing_push` `reference_centralized_mpc_cbf_cargo` seed `6661`: `sp5_multi-group-crossing-push_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6661.mp4`
- `overactuated_push_drag` `reference_centralized_mpc_cbf_cargo` seed `6655`: `sp5_overactuated-push-drag_reference_model-based-reference_centralized_cargo_time-expanded-mpc-cbf-cargo_reference-centralized-mpc-cbf-cargo_seed6655.mp4`

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
