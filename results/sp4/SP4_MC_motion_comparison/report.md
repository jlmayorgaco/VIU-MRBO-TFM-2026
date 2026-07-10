# SP4_MC_motion_comparison

SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?
- Seeds: `5100`-`5149` (`n=50`)
- Scenario generators: `open_field_arrival, crossing_traffic, narrow_passage, cluttered_warehouse, communication_limited, long_distance_energy`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| apf_obstacle_avoidance | APF obstacle avoidance | classic | decentralized | baseline | artificial_potential_field |
| cbf_safety_filter | CBF safety filter | sota | centralized | baseline | cbf_velocity_projection_proxy |
| direct_to_target | Direct to target | classic | decentralized | baseline | direct_single_integrator |
| energy_aware_smith_motion | Energy-aware Smith motion | model_based | decentralized | proposed | smith_qr_energy_congestion_field |
| priority_yield | Priority yield | classic | centralized | baseline | priority_release_yield |
| reference_time_expanded_cbf | Reference time-expanded CBF | model_based_reference | centralized | reference | time_expanded_safe_cbf_reference |
| smith_motion_field | Smith-QR motion field | model_based | decentralized | proposed | smith_qr_congestion_field |
| velocity_obstacle_proxy | Velocity obstacle proxy | sota | decentralized | baseline | velocity_obstacle_proxy |

## Performance Ranking

| Rank | Method | Family | Owner | Arrival | Collision | Timeout | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | reference_time_expanded_cbf | model_based_reference | reference | 0.922 | 0.0095 | 0.078 | 26.48 | 925.41 | 0.000 | 113.715 |
| 2 | cbf_safety_filter | sota | baseline | 0.921 | 0.0100 | 0.079 | 26.76 | 920.99 | 0.014 | 100.837 |
| 3 | smith_motion_field | model_based | proposed | 0.887 | 0.0107 | 0.113 | 27.14 | 938.62 | 0.027 | 126.490 |
| 4 | energy_aware_smith_motion | model_based | proposed | 0.796 | 0.0126 | 0.204 | 29.51 | 920.40 | 0.059 | 148.594 |
| 5 | apf_obstacle_avoidance | classic | baseline | 1.000 | 0.0468 | 0.000 | 23.89 | 797.56 | 0.101 | 58.147 |
| 6 | direct_to_target | classic | baseline | 1.000 | 0.0497 | 0.000 | 21.91 | 794.75 | 0.105 | 17.464 |
| 7 | velocity_obstacle_proxy | sota | baseline | 1.000 | 0.0514 | 0.000 | 24.40 | 796.57 | 0.118 | 74.428 |
| 8 | priority_yield | classic | baseline | 0.999 | 0.0566 | 0.001 | 24.57 | 797.77 | 0.136 | 31.552 |

## Theory Audit

- Checks: `2700`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H4_1_reference_reduces_collision_vs_direct | collision_rate | 300 | 2.08e-43 | 6.23e-43 | -0.0402 | [-0.04565, -0.03474] | True | ok |
| H4_2_smith_reduces_collision_vs_direct | collision_rate | 300 | 8.08e-43 | 1.62e-42 | -0.0390 | [-0.04443, -0.03357] | True | ok |
| H4_3_energy_smith_reduces_energy_vs_cbf | energy_proxy_wh | 300 | 0.9998 | 0.9998 | -0.5852 | [-5.002, 3.491] | False | ok |
| H4_4_methods_differ_gap_vs_reference | performance_gap_vs_reference | 300 | 5.98e-150 | 2.39e-149 | 0.3941 |  | True | ok |

## Scenario Videos

- `cluttered_warehouse` `reference_time_expanded_cbf` seed `5100`: `sp4_cluttered-warehouse_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5100.mp4`
- `cluttered_warehouse` `smith_motion_field` seed `5114`: `sp4_cluttered-warehouse_proposed_model-based_decentralized_smith-qr-congestion-field_smith-motion-field_seed5114.mp4`
- `cluttered_warehouse` `cbf_safety_filter` seed `5100`: `sp4_cluttered-warehouse_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5100.mp4`
- `cluttered_warehouse` `energy_aware_smith_motion` seed `5108`: `sp4_cluttered-warehouse_proposed_model-based_decentralized_smith-qr-energy-congestion-field_energy-aware-smith-motion_seed5108.mp4`
- `communication_limited` `reference_time_expanded_cbf` seed `5130`: `sp4_communication-limited_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5130.mp4`
- `communication_limited` `cbf_safety_filter` seed `5139`: `sp4_communication-limited_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5139.mp4`
- `communication_limited` `smith_motion_field` seed `5120`: `sp4_communication-limited_proposed_model-based_decentralized_smith-qr-congestion-field_smith-motion-field_seed5120.mp4`
- `communication_limited` `energy_aware_smith_motion` seed `5128`: `sp4_communication-limited_proposed_model-based_decentralized_smith-qr-energy-congestion-field_energy-aware-smith-motion_seed5128.mp4`
- `crossing_traffic` `cbf_safety_filter` seed `5100`: `sp4_crossing-traffic_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5100.mp4`
- `crossing_traffic` `energy_aware_smith_motion` seed `5107`: `sp4_crossing-traffic_proposed_model-based_decentralized_smith-qr-energy-congestion-field_energy-aware-smith-motion_seed5107.mp4`
- `crossing_traffic` `direct_to_target` seed `5100`: `sp4_crossing-traffic_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5100.mp4`
- `crossing_traffic` `velocity_obstacle_proxy` seed `5100`: `sp4_crossing-traffic_baseline_sota_decentralized_velocity-obstacle-proxy_velocity-obstacle-proxy_seed5100.mp4`
- `long_distance_energy` `direct_to_target` seed `5100`: `sp4_long-distance-energy_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5100.mp4`
- `long_distance_energy` `reference_time_expanded_cbf` seed `5100`: `sp4_long-distance-energy_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5100.mp4`
- `long_distance_energy` `apf_obstacle_avoidance` seed `5100`: `sp4_long-distance-energy_baseline_classic_decentralized_artificial-potential-field_apf-obstacle-avoidance_seed5100.mp4`
- `long_distance_energy` `priority_yield` seed `5100`: `sp4_long-distance-energy_baseline_classic_centralized_priority-release-yield_priority-yield_seed5100.mp4`
- `narrow_passage` `energy_aware_smith_motion` seed `5100`: `sp4_narrow-passage_proposed_model-based_decentralized_smith-qr-energy-congestion-field_energy-aware-smith-motion_seed5100.mp4`
- `narrow_passage` `reference_time_expanded_cbf` seed `5115`: `sp4_narrow-passage_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5115.mp4`
- `narrow_passage` `smith_motion_field` seed `5102`: `sp4_narrow-passage_proposed_model-based_decentralized_smith-qr-congestion-field_smith-motion-field_seed5102.mp4`
- `narrow_passage` `cbf_safety_filter` seed `5115`: `sp4_narrow-passage_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5115.mp4`
- `open_field_arrival` `direct_to_target` seed `5100`: `sp4_open-field-arrival_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5100.mp4`
- `open_field_arrival` `reference_time_expanded_cbf` seed `5100`: `sp4_open-field-arrival_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5100.mp4`
- `open_field_arrival` `cbf_safety_filter` seed `5100`: `sp4_open-field-arrival_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5100.mp4`
- `open_field_arrival` `smith_motion_field` seed `5100`: `sp4_open-field-arrival_proposed_model-based_decentralized_smith-qr-congestion-field_smith-motion-field_seed5100.mp4`

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
