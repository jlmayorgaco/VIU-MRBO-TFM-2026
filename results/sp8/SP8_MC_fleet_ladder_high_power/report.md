# SP8_MC_fleet_ladder_high_power

SP8 studies warehouse-scale intractability: many AMRs, many simultaneous payload loads, wrench/torque requirements, static/mobile obstacles and approximate transport risk.

- Runs: `20000`
- Theory failed checks: `0`
- Best all-scenario method: `ours_tensor_quorum_flow`

## Hypotheses
- `H8.1_centralized_oracle_timeout_increases_with_scale`: p=4.928e-287, Holm reject=True.
- `H8.2_ours_hierarchical_higher_completion_than_classic_local`: p=1.394e-300, Holm reject=True.
- `H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian`: p=3.223e-299, Holm reject=True.

## Primary Ranking
- ALL_SCENARIOS rank 1: `ours_tensor_quorum_flow` completion=0.156, timeout=0.000, runtime=1385.50 ms.
- ALL_SCENARIOS rank 2: `ours_primal_dual_spatial` completion=0.154, timeout=0.000, runtime=212.83 ms.
- ALL_SCENARIOS rank 3: `ours_wrench_market_hierarchical` completion=0.153, timeout=0.000, runtime=206.96 ms.
- ALL_SCENARIOS rank 4: `classic_local_greedy` completion=0.052, timeout=0.000, runtime=167.55 ms.
- ALL_SCENARIOS rank 5: `auction_market_local` completion=0.052, timeout=0.000, runtime=179.14 ms.
- ALL_SCENARIOS rank 6: `ours_mean_field_approximation` completion=0.044, timeout=0.000, runtime=174.26 ms.
- ALL_SCENARIOS rank 7: `cbba_partitioned` completion=0.043, timeout=0.000, runtime=759.67 ms.
- ALL_SCENARIOS rank 8: `centralized_hungarian_expanded` completion=0.024, timeout=0.600, runtime=36000.87 ms.
- ALL_SCENARIOS rank 9: `centralized_time_expanded_mpc` completion=0.043, timeout=0.750, runtime=45000.25 ms.
- ALL_SCENARIOS rank 10: `centralized_coalition_oracle` completion=0.033, timeout=0.800, runtime=48000.13 ms.
- fleet_ladder_extended rank 1: `ours_tensor_quorum_flow` completion=0.156, timeout=0.000, runtime=1385.50 ms.
- fleet_ladder_extended rank 2: `ours_primal_dual_spatial` completion=0.154, timeout=0.000, runtime=212.83 ms.
