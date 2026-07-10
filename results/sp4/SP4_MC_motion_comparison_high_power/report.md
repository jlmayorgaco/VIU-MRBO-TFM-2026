# SP4_MC_motion_comparison_high_power

SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?
- Seeds: `5600`-`5822` (`n=223`)
- Scenario generators: `open_field_arrival, crossing_traffic, narrow_passage, cluttered_warehouse, communication_limited, long_distance_energy`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| apf_obstacle_avoidance | APF obstacle avoidance | classic | decentralized | baseline | artificial_potential_field |
| bnn_motion_field | BNN/Brown motion field | model_based | decentralized | baseline | brown_bnn_positive_excess_field |
| cbf_safety_filter | CBF safety filter | sota | centralized | baseline | cbf_velocity_projection_proxy |
| direct_to_target | Direct to target | classic | decentralized | baseline | direct_single_integrator |
| energy_aware_smith_motion | Energy-aware Smith motion | model_based | decentralized | proposed | smith_qr_energy_congestion_field |
| explicit_vgne_cbf_motion | Ours explicit vGNE-CBF motion | model_based | decentralized | proposed | closed_form_explicit_amr_vgne_cbf |
| logit_motion_field | Logit motion field | model_based | decentralized | baseline | logit_softmax_motion_field |
| pid_safety_motion | PID safety motion | model_based | decentralized | proposed | pid_damped_safety_motion |
| primal_dual_motion_field | Primal-dual motion field | model_based | decentralized | proposed | primal_dual_barrier_motion_field |
| priority_yield | Priority yield | classic | centralized | baseline | priority_release_yield |
| reference_time_expanded_cbf | Reference time-expanded CBF | model_based_reference | centralized | reference | time_expanded_safe_cbf_reference |
| replicator_motion_field | Replicator motion field | model_based | decentralized | baseline | replicator_target_congestion_field |
| smith_motion_field | Smith-QR motion field | model_based | decentralized | proposed | smith_qr_congestion_field |
| tensor_flow_motion_field | Smooth tensor-flow motion | model_based | decentralized | proposed | smooth_tensor_flow_barrier_motion |
| velocity_obstacle_proxy | Velocity obstacle proxy | sota | decentralized | baseline | velocity_obstacle_proxy |

## Performance Ranking

| Rank | Method | Family | Owner | Arrival | Collision | Timeout | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | apf_obstacle_avoidance | classic | baseline | 1.000 | 0.0468 | 0.000 | 23.85 | 791.57 | 0.097 | 47.081 |
| 2 | direct_to_target | classic | baseline | 1.000 | 0.0496 | 0.000 | 21.86 | 788.78 | 0.101 | 14.093 |
| 3 | velocity_obstacle_proxy | sota | baseline | 1.000 | 0.0514 | 0.000 | 24.35 | 790.58 | 0.115 | 61.101 |
| 4 | replicator_motion_field | model_based | baseline | 1.000 | 0.0535 | 0.000 | 23.80 | 789.81 | 0.121 | 59.834 |
| 5 | logit_motion_field | model_based | baseline | 1.000 | 0.0539 | 0.000 | 24.90 | 790.16 | 0.125 | 62.352 |
| 6 | explicit_vgne_cbf_motion | model_based | proposed | 1.000 | 0.0546 | 0.000 | 24.30 | 789.94 | 0.126 | 222.201 |
| 7 | priority_yield | classic | baseline | 1.000 | 0.0574 | 0.000 | 24.54 | 792.12 | 0.135 | 25.257 |
| 8 | bnn_motion_field | model_based | baseline | 1.000 | 0.0531 | 0.000 | 25.48 | 790.64 | 0.124 | 63.626 |
| 9 | reference_time_expanded_cbf | model_based_reference | reference | 0.921 | 0.0104 | 0.079 | 26.49 | 918.80 | 0.000 | 93.253 |
| 10 | cbf_safety_filter | sota | baseline | 0.918 | 0.0115 | 0.082 | 26.80 | 915.12 | 0.015 | 83.156 |
| 11 | smith_motion_field | model_based | proposed | 0.887 | 0.0124 | 0.113 | 27.14 | 930.83 | 0.028 | 104.663 |
| 12 | primal_dual_motion_field | model_based | proposed | 0.883 | 0.0122 | 0.117 | 27.97 | 916.64 | 0.027 | 107.189 |
| 13 | tensor_flow_motion_field | model_based | proposed | 0.867 | 0.0122 | 0.133 | 28.42 | 914.29 | 0.032 | 109.293 |
| 14 | energy_aware_smith_motion | model_based | proposed | 0.804 | 0.0136 | 0.196 | 29.58 | 912.85 | 0.056 | 123.405 |
| 15 | pid_safety_motion | model_based | proposed | 0.776 | 0.0139 | 0.224 | 30.07 | 903.43 | 0.065 | 99.181 |

## Theory Audit

- Checks: `21408`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H4_HP_1_reference_reduces_collision_vs_direct | collision_rate | 1338 | 8.4e-184 | 2.52e-183 | -0.0392 | [-0.04164, -0.0368] | True | ok |
| H4_HP_2_cbf_reduces_collision_vs_direct | collision_rate | 1338 | 4.44e-183 | 8.88e-183 | -0.0381 | [-0.0406, -0.03578] | True | ok |
| H4_HP_3_tensor_reduces_collision_vs_direct | collision_rate | 1338 | 3.52e-184 | 1.41e-183 | -0.0374 | [-0.03983, -0.03511] | True | ok |
| H4_HP_4_energy_smith_reduces_energy_vs_cbf | energy_proxy_wh | 1338 | 1.0000 | 1.0000 | -2.2656 | [-4.243, -0.2836] | False | ok |
| H4_HP_5_methods_differ_gap_vs_reference | performance_gap_vs_reference | 1338 | 0.0000 | 0.0000 | 0.3687 |  | True | ok |

## Scenario Videos


## Artifacts

- `tables/runs.csv`
- `tables/summary.csv`
- `tables/performance_ranking.csv`
- `tables/robot_status.csv`
- `tables/trajectory_samples.csv`
- `tables/theory_checks.csv`
- `tables/hypothesis_results.csv`
- `theory_audit.json`
- `figures/sp4_arrival_success_by_method.png`
- `figures/sp4_collision_rate_by_scenario.png`
- `figures/sp4_time_energy_pareto.png`
- `figures/sp4_clearance_by_method.png`
- `figures/sp4_path_efficiency_by_method.png`
- `figures/sp4_communication_radius_degradation.png`
- `videos/sp4_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`
