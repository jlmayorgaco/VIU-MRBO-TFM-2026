# SP4_MC_explicit_control_law

SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?
- Seeds: `5400`-`5411` (`n=12`)
- Scenario generators: `open_field_arrival, crossing_traffic, narrow_passage, cluttered_warehouse, communication_limited, long_distance_energy`

## Method Taxonomy

| Method | Label | Family | Scope | Ownership | Variant |
|---|---|---|---|---|---|
| cbf_safety_filter | CBF safety filter | sota | centralized | baseline | cbf_velocity_projection_proxy |
| direct_to_target | Direct to target | classic | decentralized | baseline | direct_single_integrator |
| explicit_vgne_cbf_motion | Ours explicit vGNE-CBF motion | model_based | decentralized | proposed | closed_form_explicit_amr_vgne_cbf |
| reference_time_expanded_cbf | Reference time-expanded CBF | model_based_reference | centralized | reference | time_expanded_safe_cbf_reference |
| smith_motion_field | Smith-QR motion field | model_based | decentralized | proposed | smith_qr_congestion_field |
| tensor_flow_motion_field | Smooth tensor-flow motion | model_based | decentralized | proposed | smooth_tensor_flow_barrier_motion |

## Performance Ranking

| Rank | Method | Family | Owner | Arrival | Collision | Timeout | Time s | Energy Wh | Gap | Runtime ms |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | direct_to_target | classic | baseline | 1.000 | 0.0505 | 0.000 | 21.93 | 798.34 | 0.100 | 14.171 |
| 2 | explicit_vgne_cbf_motion | model_based | proposed | 1.000 | 0.0554 | 0.000 | 24.38 | 799.57 | 0.122 | 222.217 |
| 3 | cbf_safety_filter | sota | baseline | 0.919 | 0.0103 | 0.081 | 27.00 | 928.76 | 0.007 | 83.905 |
| 4 | reference_time_expanded_cbf | model_based_reference | reference | 0.898 | 0.0102 | 0.102 | 26.50 | 929.99 | 0.000 | 94.105 |
| 5 | smith_motion_field | model_based | proposed | 0.880 | 0.0136 | 0.120 | 27.29 | 942.41 | 0.028 | 104.802 |
| 6 | tensor_flow_motion_field | model_based | proposed | 0.848 | 0.0124 | 0.152 | 28.60 | 924.78 | 0.031 | 110.403 |

## Theory Audit

- Checks: `504`.
- Failed checks: `0`.
- Passed: `True`.

## Hypotheses

| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |
|---|---|---:|---:|---:|---:|---|---|---|
| H4E_1_explicit_reduces_collision_vs_direct | collision_rate | 72 | 0.9946 | 1.0000 | 0.0048 | [0.001877, 0.008201] | False | ok |
| H4E_2_explicit_reduces_gap_vs_cbf | performance_gap_vs_reference | 72 | 1.0000 | 1.0000 | 0.1149 | [0.08348, 0.1477] | False | ok |
| H4E_3_explicit_family_differs | score_value | 72 | 3.81e-23 | 1.14e-22 | 0.3865 |  | True | ok |

## Scenario Videos

- `cluttered_warehouse` `cbf_safety_filter` seed `5400`: `sp4_cluttered-warehouse_baseline_sota_centralized_cbf-velocity-projection-proxy_cbf-safety-filter_seed5400.mp4`
- `communication_limited` `reference_time_expanded_cbf` seed `5400`: `sp4_communication-limited_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5400.mp4`
- `crossing_traffic` `reference_time_expanded_cbf` seed `5400`: `sp4_crossing-traffic_reference_model-based-reference_centralized_time-expanded-safe-cbf-reference_reference-time-expanded-cbf_seed5400.mp4`
- `long_distance_energy` `direct_to_target` seed `5400`: `sp4_long-distance-energy_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5400.mp4`
- `narrow_passage` `direct_to_target` seed `5400`: `sp4_narrow-passage_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5400.mp4`
- `open_field_arrival` `direct_to_target` seed `5400`: `sp4_open-field-arrival_baseline_classic_decentralized_direct-single-integrator_direct-to-target_seed5400.mp4`

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
