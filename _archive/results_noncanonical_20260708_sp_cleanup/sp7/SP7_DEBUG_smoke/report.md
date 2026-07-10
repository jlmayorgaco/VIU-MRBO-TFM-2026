# SP7_DEBUG_smoke

SP7 evaluates cooperative transport under time-varying communication and sensing stress: radio radius, packet loss, burst drops, delay, jitter, intermittent outages and sensor degradation.

## Scope

- Uses SP5 payload transport worlds with static obstacles and moving robot groups.
- Adds temporal robot-robot communication graphs and sensor-detection metrics.
- Measures direct connectivity, multi-hop relay connectivity and temporal connectivity.
- Does not claim RF propagation fidelity or hardware-network validation.

## Summary

- Runs: `4`
- Theory failed checks: `0`
- Best all-scenario method: `classic_decentralized_sensor_apf`
- Videos generated: `0`

## Hypotheses
- `H7.1_radius_improves_coalition_connectivity`: p=1, Holm reject=False.
- `H7.2_ours_connectivity_beats_classic_under_harsh_profiles`: p=1, Holm reject=False.
- `H7.3_methods_differ_under_intermittent_communication`: p=1, Holm reject=False.

## Primary Ranking
- ALL_SCENARIOS rank 1: `classic_decentralized_sensor_apf` score=0.353, connectivity=0.447.
- ALL_SCENARIOS rank 2: `ours_connectivity_wrench_game` score=0.335, connectivity=0.574.
- ALL_SCENARIOS rank 3: `reference_full_communication` score=0.290, connectivity=0.451.
- ALL_SCENARIOS rank 4: `classic_centralized_global_mpc` score=0.236, connectivity=0.549.
- setup rank 1: `classic_decentralized_sensor_apf` score=0.353, connectivity=0.447.
- setup rank 2: `ours_connectivity_wrench_game` score=0.335, connectivity=0.574.
- setup rank 3: `reference_full_communication` score=0.290, connectivity=0.451.
- setup rank 4: `classic_centralized_global_mpc` score=0.236, connectivity=0.549.
