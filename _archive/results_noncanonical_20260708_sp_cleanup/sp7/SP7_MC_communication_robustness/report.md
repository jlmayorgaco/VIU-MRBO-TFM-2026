# SP7_MC_communication_robustness

SP7 evaluates cooperative transport under time-varying communication and sensing stress: radio radius, packet loss, burst drops, delay, jitter, intermittent outages and sensor degradation.

## Scope

- Uses SP5 payload transport worlds with static obstacles and moving robot groups.
- Adds temporal robot-robot communication graphs and sensor-detection metrics.
- Measures direct connectivity, multi-hop relay connectivity and temporal connectivity.
- Does not claim RF propagation fidelity or hardware-network validation.

## Summary

- Runs: `28`
- Theory failed checks: `0`
- Best all-scenario method: `classic_decentralized_sensor_apf`
- Videos generated: `2`

## Hypotheses
- `H7.1_radius_improves_coalition_connectivity`: p=2.114e-13, Holm reject=True.
- `H7.2_ours_connectivity_beats_classic_under_harsh_profiles`: p=0.125, Holm reject=False.
- `H7.3_methods_differ_under_intermittent_communication`: p=1, Holm reject=False.

## Primary Ranking
- ALL_SCENARIOS rank 1: `classic_decentralized_sensor_apf` score=0.401, connectivity=0.478.
- ALL_SCENARIOS rank 2: `reference_full_communication` score=0.379, connectivity=0.446.
- ALL_SCENARIOS rank 3: `ours_connectivity_wrench_game` score=0.325, connectivity=0.451.
- ALL_SCENARIOS rank 4: `classic_centralized_global_mpc` score=0.257, connectivity=0.443.
- cargo_sensor_degradation rank 1: `reference_full_communication` score=0.679, connectivity=0.502.
- cargo_sensor_degradation rank 2: `classic_decentralized_sensor_apf` score=0.622, connectivity=0.513.
- cargo_sensor_degradation rank 3: `ours_connectivity_wrench_game` score=0.318, connectivity=0.521.
- cargo_sensor_degradation rank 4: `classic_centralized_global_mpc` score=0.266, connectivity=0.513.
- monte_carlo rank 1: `ours_connectivity_wrench_game` score=0.304, connectivity=0.077.
- monte_carlo rank 2: `classic_decentralized_sensor_apf` score=0.285, connectivity=0.132.
- monte_carlo rank 3: `reference_full_communication` score=0.172, connectivity=0.094.
- monte_carlo rank 4: `classic_centralized_global_mpc` score=0.163, connectivity=0.047.
