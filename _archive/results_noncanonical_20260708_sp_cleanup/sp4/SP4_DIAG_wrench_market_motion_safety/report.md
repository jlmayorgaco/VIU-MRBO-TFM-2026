# SP4_DIAG_wrench_market_motion_safety

SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?
- Seeds: `5400`-`5414` (`n=15`)
- Scenario generators: `open_field_arrival, crossing_traffic, narrow_passage, cluttered_warehouse, communication_limited, long_distance_energy`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| apf_obstacle_avoidance | APF obstacle avoidance | classic | decentralized | baseline | artificial_potential_field |
| bnn_motion_field | BNN/Brown motion field | model_based | decentralized | baseline | brown_bnn_positive_excess_field |
| cbf_safety_filter | CBF safety filter | sota | centralized | baseline | cbf_velocity_projection_proxy |
| direct_to_target | Direct to target | classic | decentralized | baseline | direct_single_integrator |
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
| 1 | reference_time_expanded_cbf | model_based_reference | reference | 0.907 | 0.0093 | 0.093 | 26.56 | 923.40 | 0.000 | 99.217 |
| 2 | cbf_safety_filter | sota | baseline | 0.922 | 0.0094 | 0.078 | 27.04 | 922.32 | 0.008 | 87.699 |
| 3 | tensor_flow_motion_field | model_based | proposed | 0.854 | 0.0112 | 0.146 | 28.59 | 918.33 | 0.030 | 115.984 |
| 4 | primal_dual_motion_field | model_based | proposed | 0.873 | 0.0118 | 0.127 | 28.10 | 919.31 | 0.026 | 113.959 |
| 5 | smith_motion_field | model_based | proposed | 0.882 | 0.0125 | 0.118 | 27.33 | 936.29 | 0.028 | 111.655 |
| 6 | pid_safety_motion | model_based | proposed | 0.758 | 0.0132 | 0.242 | 30.18 | 906.05 | 0.066 | 105.607 |
| 7 | apf_obstacle_avoidance | classic | baseline | 1.000 | 0.0468 | 0.000 | 23.98 | 797.19 | 0.097 | 50.268 |
| 8 | direct_to_target | classic | baseline | 1.000 | 0.0494 | 0.000 | 21.99 | 794.47 | 0.102 | 15.418 |
| 9 | velocity_obstacle_proxy | sota | baseline | 1.000 | 0.0513 | 0.000 | 24.49 | 796.18 | 0.114 | 65.846 |
| 10 | bnn_motion_field | model_based | baseline | 0.998 | 0.0530 | 0.002 | 25.62 | 796.32 | 0.123 | 67.869 |
| 11 | replicator_motion_field | model_based | baseline | 1.000 | 0.0531 | 0.000 | 23.94 | 795.46 | 0.120 | 64.272 |
| 12 | logit_motion_field | model_based | baseline | 1.000 | 0.0536 | 0.000 | 25.05 | 795.86 | 0.124 | 65.842 |
| 13 | priority_yield | classic | baseline | 1.000 | 0.0553 | 0.000 | 24.66 | 797.40 | 0.130 | 26.937 |

## Theory Audit

- Checks: `1260`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H_DIAG_SP4_reference_collision_lower_than_direct | collision_rate | 90 | 6.85e-15 | 2.06e-14 | -0.0400 | [-0.04974, -0.0306] | True | ok |
| H_DIAG_SP4_tensor_collision_lower_than_direct | collision_rate | 90 | 6.85e-15 | 2.06e-14 | -0.0382 | [-0.04742, -0.02936] | True | ok |
| H_DIAG_SP4_primal_dual_gap_lower_than_apf | performance_gap_vs_reference | 90 | 3.43e-09 | 3.43e-09 | -0.0707 | [-0.09528, -0.04867] | True | ok |

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
