# SP7_MC_communication_robustness_high_power

SP7 evaluates cooperative transport under time-varying communication and sensing stress: radio radius, packet loss, burst drops, delay, jitter, intermittent outages and sensor degradation.

## Scope

- Uses SP5 payload transport worlds with static obstacles and moving robot groups.
- Adds temporal robot-robot communication graphs and sensor-detection metrics.
- Measures direct connectivity, multi-hop relay connectivity and temporal connectivity.
- Does not claim RF propagation fidelity or hardware-network validation.

## Summary

- Runs: `20176`
- Theory failed checks: `0`
- Best all-scenario method: `ours_connectivity_wrench_game`
- Videos generated: `0`

## Hypotheses
- `H7.1_radius_improves_coalition_connectivity`: p=0, Holm reject=True.
- `H7.2_ours_connectivity_beats_classic_under_harsh_profiles`: p=6.812e-81, Holm reject=True.
- `H7.3_methods_differ_under_intermittent_communication`: p=1, Holm reject=False.

## Primary Ranking
- ALL_SCENARIOS rank 1: `ours_connectivity_wrench_game` score=0.436, connectivity=0.684.
- ALL_SCENARIOS rank 2: `ours_delay_robust_repair` score=0.419, connectivity=0.641.
- ALL_SCENARIOS rank 3: `reference_full_communication` score=0.356, connectivity=0.676.
- ALL_SCENARIOS rank 4: `classic_decentralized_sensor_apf` score=0.333, connectivity=0.631.
- ALL_SCENARIOS rank 5: `sota_delay_tolerant_consensus` score=0.314, connectivity=0.665.
- ALL_SCENARIOS rank 6: `sota_centralized_cbf_networked` score=0.302, connectivity=0.661.
- ALL_SCENARIOS rank 7: `sota_decentralized_cbba_relay` score=0.301, connectivity=0.663.
- ALL_SCENARIOS rank 8: `classic_centralized_global_mpc` score=0.293, connectivity=0.673.
- cargo_sensor_degradation rank 1: `ours_connectivity_wrench_game` score=0.625, connectivity=0.661.
- cargo_sensor_degradation rank 2: `ours_delay_robust_repair` score=0.625, connectivity=0.660.
- cargo_sensor_degradation rank 3: `reference_full_communication` score=0.477, connectivity=0.696.
- cargo_sensor_degradation rank 4: `classic_decentralized_sensor_apf` score=0.438, connectivity=0.645.
