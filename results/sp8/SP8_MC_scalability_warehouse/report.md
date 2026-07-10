# SP8_MC_scalability_warehouse

SP8 studies warehouse-scale intractability: many AMRs, many simultaneous payload loads, wrench/torque requirements, static/mobile obstacles and approximate transport risk.

- Runs: `150`
- Theory failed checks: `0`
- Best all-scenario method: `ours_tensor_quorum_flow`

## Hypotheses
- `H8.1_centralized_oracle_timeout_increases_with_scale`: p=0.002205, Holm reject=True.
- `H8.2_ours_hierarchical_higher_completion_than_classic_local`: p=0.0004374, Holm reject=True.
- `H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian`: p=0.0003242, Holm reject=True.

## Primary Ranking
- ALL_SCENARIOS rank 1: `ours_tensor_quorum_flow` completion=0.153, timeout=0.000, runtime=32.62 ms.
- ALL_SCENARIOS rank 2: `ours_primal_dual_spatial` completion=0.151, timeout=0.000, runtime=3.31 ms.
- ALL_SCENARIOS rank 3: `ours_wrench_market_hierarchical` completion=0.142, timeout=0.000, runtime=3.28 ms.
- ALL_SCENARIOS rank 4: `auction_market_local` completion=0.056, timeout=0.000, runtime=2.53 ms.
- ALL_SCENARIOS rank 5: `classic_local_greedy` completion=0.054, timeout=0.000, runtime=3.00 ms.
- ALL_SCENARIOS rank 6: `cbba_partitioned` completion=0.047, timeout=0.000, runtime=16.62 ms.
- ALL_SCENARIOS rank 7: `centralized_hungarian_expanded` completion=0.042, timeout=0.000, runtime=1.48 ms.
- ALL_SCENARIOS rank 8: `ours_mean_field_approximation` completion=0.040, timeout=0.000, runtime=4.35 ms.
- ALL_SCENARIOS rank 9: `centralized_time_expanded_mpc` completion=0.060, timeout=0.600, runtime=36000.53 ms.
- ALL_SCENARIOS rank 10: `centralized_coalition_oracle` completion=0.025, timeout=0.800, runtime=48000.16 ms.
- obstacle_monte_carlo rank 1: `ours_tensor_quorum_flow` completion=0.164, timeout=0.000, runtime=42.57 ms.
- obstacle_monte_carlo rank 2: `ours_wrench_market_hierarchical` completion=0.161, timeout=0.000, runtime=3.98 ms.
