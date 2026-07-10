# SP4_DEBUG_smoke

SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?
- Seeds: `5100`-`5101` (`n=2`)
- Scenario generators: `open_field_arrival, crossing_traffic, narrow_passage`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
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

## Performance Ranking

| Rank | Method | Family | Owner | Arrival | Collision | Timeout | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | smith_motion_field | model_based | proposed | 0.778 | 0.0041 | 0.222 | 25.21 | 801.35 | 0.021 | 82.413 |
| 2 | primal_dual_motion_field | model_based | proposed | 0.806 | 0.0054 | 0.194 | 26.06 | 786.10 | 0.023 | 90.779 |
| 3 | tensor_flow_motion_field | model_based | proposed | 0.806 | 0.0057 | 0.194 | 26.54 | 783.76 | 0.021 | 99.675 |
| 4 | pid_safety_motion | model_based | proposed | 0.556 | 0.0081 | 0.444 | 27.94 | 760.19 | 0.070 | 77.271 |
| 5 | cbf_safety_filter | sota | baseline | 0.833 | 0.0103 | 0.167 | 24.96 | 789.06 | 0.020 | 63.886 |
| 6 | reference_time_expanded_cbf | model_based_reference | reference | 0.861 | 0.0168 | 0.139 | 25.77 | 804.48 | 0.000 | 76.351 |
| 7 | direct_to_target | classic | baseline | 1.000 | 0.0508 | 0.000 | 20.35 | 669.11 | 0.073 | 12.378 |
| 8 | priority_yield | classic | baseline | 1.000 | 0.0577 | 0.000 | 22.77 | 670.59 | 0.106 | 20.896 |
| 9 | bnn_motion_field | model_based | baseline | 0.972 | 0.0611 | 0.028 | 23.60 | 670.40 | 0.130 | 56.007 |
| 10 | replicator_motion_field | model_based | baseline | 1.000 | 0.0624 | 0.000 | 22.14 | 669.45 | 0.123 | 49.852 |
| 11 | logit_motion_field | model_based | baseline | 1.000 | 0.0626 | 0.000 | 23.18 | 670.04 | 0.127 | 51.145 |

## Theory Audit

- Checks: `72`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H4_DEBUG_reference_collision_not_worse_than_direct | collision_rate | 6 | 0.0625 | 0.0625 | -0.0340 | [-0.06886, -0.002632] | False | ok |

## Scenario Videos

- `crossing_traffic` `reference_time_expanded_cbf` seed `5100`: `sp4_crossing-traffic_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5100.mp4`
- `crossing_traffic` `cbf_safety_filter` seed `5100`: `sp4_crossing-traffic_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5100.mp4`
- `narrow_passage` `tensor_flow_motion_field` seed `5100`: `sp4_narrow-passage_proposed_model-based_decentralized_smooth-tensor-flow-barrier-motion_tensor-flow-motion-field_seed5100.mp4`
- `narrow_passage` `primal_dual_motion_field` seed `5100`: `sp4_narrow-passage_proposed_model-based_decentralized_primal-dual-barrier-motion-field_primal-dual-motion-field_seed5100.mp4`
- `open_field_arrival` `direct_to_target` seed `5100`: `sp4_open-field-arrival_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5100.mp4`
- `open_field_arrival` `reference_time_expanded_cbf` seed `5100`: `sp4_open-field-arrival_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5100.mp4`

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
