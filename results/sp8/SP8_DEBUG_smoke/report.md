# SP8_DEBUG_smoke

SP8 studies warehouse-scale intractability: many AMRs, many simultaneous payload loads, wrench/torque requirements, static/mobile obstacles and approximate transport risk.

- Runs: `6`
- Theory failed checks: `0`
- Best all-scenario method: `ours_wrench_market_hierarchical`

## Hypotheses
- `H8.1_centralized_oracle_timeout_increases_with_scale`: p=1, Holm reject=False.
- `H8.2_ours_hierarchical_higher_completion_than_classic_local`: p=1, Holm reject=False.
- `H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian`: p=1, Holm reject=False.

## Primary Ranking
- ALL_SCENARIOS rank 1: `ours_wrench_market_hierarchical` completion=0.250, timeout=0.000, runtime=1.51 ms.
- ALL_SCENARIOS rank 2: `centralized_coalition_oracle` completion=0.250, timeout=0.000, runtime=1.51 ms.
- ALL_SCENARIOS rank 3: `ours_mean_field_approximation` completion=0.188, timeout=0.000, runtime=1.46 ms.
- ALL_SCENARIOS rank 4: `cbba_partitioned` completion=0.188, timeout=0.000, runtime=3.57 ms.
- ALL_SCENARIOS rank 5: `classic_local_greedy` completion=0.188, timeout=0.000, runtime=1.25 ms.
- ALL_SCENARIOS rank 6: `centralized_hungarian_expanded` completion=0.125, timeout=0.000, runtime=0.11 ms.
- debug rank 1: `ours_wrench_market_hierarchical` completion=0.250, timeout=0.000, runtime=1.51 ms.
- debug rank 2: `centralized_coalition_oracle` completion=0.250, timeout=0.000, runtime=1.51 ms.
- debug rank 3: `ours_mean_field_approximation` completion=0.188, timeout=0.000, runtime=1.46 ms.
- debug rank 4: `cbba_partitioned` completion=0.188, timeout=0.000, runtime=3.57 ms.
- debug rank 5: `classic_local_greedy` completion=0.188, timeout=0.000, runtime=1.25 ms.
- debug rank 6: `centralized_hungarian_expanded` completion=0.125, timeout=0.000, runtime=0.11 ms.
