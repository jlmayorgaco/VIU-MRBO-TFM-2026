# SP8_MC_fleet_ladder_extended

SP8 studies warehouse-scale intractability: many AMRs, many simultaneous payload loads, wrench/torque requirements, static/mobile obstacles and approximate transport risk.

- Runs: `600`
- Theory failed checks: `0`
- Best all-scenario method: `ours_wrench_market_hierarchical`

## Hypotheses
- `H8.1_centralized_oracle_timeout_increases_with_scale`: p=8.028e-10, Holm reject=True.
- `H8.2_ours_hierarchical_higher_completion_than_classic_local`: p=1.694e-10, Holm reject=True.
- `H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian`: p=1.346e-11, Holm reject=True.

## Primary Ranking
- ALL_SCENARIOS rank 1: `ours_wrench_market_hierarchical` completion=0.197, timeout=0.000, runtime=206.22 ms.
- ALL_SCENARIOS rank 2: `ours_tensor_quorum_flow` completion=0.197, timeout=0.000, runtime=1383.38 ms.
- ALL_SCENARIOS rank 3: `ours_primal_dual_spatial` completion=0.197, timeout=0.000, runtime=223.23 ms.
- ALL_SCENARIOS rank 4: `auction_market_local` completion=0.064, timeout=0.000, runtime=181.84 ms.
- ALL_SCENARIOS rank 5: `classic_local_greedy` completion=0.063, timeout=0.000, runtime=169.81 ms.
- ALL_SCENARIOS rank 6: `ours_mean_field_approximation` completion=0.061, timeout=0.000, runtime=174.30 ms.
- ALL_SCENARIOS rank 7: `cbba_partitioned` completion=0.055, timeout=0.000, runtime=764.12 ms.
- ALL_SCENARIOS rank 8: `centralized_hungarian_expanded` completion=0.025, timeout=0.600, runtime=36000.86 ms.
- ALL_SCENARIOS rank 9: `centralized_time_expanded_mpc` completion=0.087, timeout=0.750, runtime=45000.22 ms.
- ALL_SCENARIOS rank 10: `centralized_coalition_oracle` completion=0.078, timeout=0.800, runtime=48000.18 ms.
- fleet_ladder_extended rank 1: `ours_wrench_market_hierarchical` completion=0.197, timeout=0.000, runtime=206.22 ms.
- fleet_ladder_extended rank 2: `ours_tensor_quorum_flow` completion=0.197, timeout=0.000, runtime=1383.38 ms.
