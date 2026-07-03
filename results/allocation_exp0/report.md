# EXP0 static allocation

- Seed: `20260703`
- Robots: `10` homogeneous AMRs, `25.0 kg` payload each
- Loads: `4` heterogeneous loads with explicit mass and minimum AMR demand
- Scope: allocation only; the MP4 animates assignment-to-load relocation, not full path planning or collision avoidance.

## Physical scenario

| Load | Mass [kg] | Required capacity [kg] | Min AMRs | Reward |
|---|---:|---:|---:|---:|
| L1 | 20.0 | 20.0 | 1 | 1.220 |
| L2 | 48.0 | 48.0 | 2 | 1.720 |
| L3 | 73.0 | 73.0 | 3 | 2.220 |
| L4 | 118.0 | 118.0 | 5 | 3.140 |

A load is **UNDER** when assigned capacity is below its mass or assigned AMRs are fewer than the minimum. It is **OVER** when more AMRs than the minimum are allocated. Remaining AMRs are reported as idle.

## Methods

| Code | Method | Interpretation |
|---|---|---|
| A | Centralized classic min-cost | Hungarian assignment over replicated load slots. |
| B | Decentralized classic greedy | Sequential nearest-load local rule. |
| C | Centralized SOTA proxy | Reward-aware centralized assignment under scarcity. |
| D | Decentralized SOTA auction | CBBA-like local auction with deficit prices. |
| E | Our basic Smith-QR | Existing Smith-QR allocator facade, no tuning. |

## Summary

| Method | Satisfied loads | Under loads | Over loads | Capacity deficit [kg] | Capacity headroom [kg] | Idle | Reward | Distance [m] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Centralized classic min-cost | 3/4 | 1 | 0 | 18.0 | 9.0 | 0 | 5.160 | 23.612 |
| Decentralized classic greedy | 3/4 | 1 | 0 | 18.0 | 9.0 | 0 | 5.160 | 23.612 |
| Centralized SOTA proxy | 3/4 | 1 | 0 | 20.0 | 11.0 | 0 | 7.080 | 25.214 |
| Decentralized SOTA auction | 3/4 | 1 | 0 | 23.0 | 14.0 | 0 | 6.580 | 24.864 |
| Our basic Smith-QR | 2/4 | 2 | 1 | 68.0 | 59.0 | 0 | 5.360 | 28.433 |

## Load status by method

| Method | Load | Assigned AMRs | Assigned capacity [kg] | Required [kg] | Status | Robots |
|---|---|---:|---:|---:|---|---|
| Centralized classic min-cost | L1 | 1/1 | 25.0 | 20.0 | OK | amr-03 |
| Centralized classic min-cost | L2 | 2/2 | 50.0 | 48.0 | OK | amr-02 amr-05 |
| Centralized classic min-cost | L3 | 3/3 | 75.0 | 73.0 | OK | amr-06 amr-09 amr-10 |
| Centralized classic min-cost | L4 | 4/5 | 100.0 | 118.0 | UNDER | amr-01 amr-04 amr-07 amr-08 |
| Decentralized classic greedy | L1 | 1/1 | 25.0 | 20.0 | OK | amr-03 |
| Decentralized classic greedy | L2 | 2/2 | 50.0 | 48.0 | OK | amr-02 amr-05 |
| Decentralized classic greedy | L3 | 3/3 | 75.0 | 73.0 | OK | amr-06 amr-09 amr-10 |
| Decentralized classic greedy | L4 | 4/5 | 100.0 | 118.0 | UNDER | amr-01 amr-04 amr-07 amr-08 |
| Centralized SOTA proxy | L1 | 0/1 | 0.0 | 20.0 | UNDER | - |
| Centralized SOTA proxy | L2 | 2/2 | 50.0 | 48.0 | OK | amr-02 amr-05 |
| Centralized SOTA proxy | L3 | 3/3 | 75.0 | 73.0 | OK | amr-06 amr-09 amr-10 |
| Centralized SOTA proxy | L4 | 5/5 | 125.0 | 118.0 | OK | amr-01 amr-03 amr-04 amr-07 amr-08 |
| Decentralized SOTA auction | L1 | 1/1 | 25.0 | 20.0 | OK | amr-03 |
| Decentralized SOTA auction | L2 | 1/2 | 25.0 | 48.0 | UNDER | amr-05 |
| Decentralized SOTA auction | L3 | 3/3 | 75.0 | 73.0 | OK | amr-06 amr-09 amr-10 |
| Decentralized SOTA auction | L4 | 5/5 | 125.0 | 118.0 | OK | amr-01 amr-02 amr-04 amr-07 amr-08 |
| Our basic Smith-QR | L1 | 0/1 | 0.0 | 20.0 | UNDER | - |
| Our basic Smith-QR | L2 | 0/2 | 0.0 | 48.0 | UNDER | - |
| Our basic Smith-QR | L3 | 3/3 | 75.0 | 73.0 | OK | amr-06 amr-09 amr-10 |
| Our basic Smith-QR | L4 | 7/5 | 175.0 | 118.0 | OVER | amr-01 amr-02 amr-03 amr-04 amr-05 amr-07 amr-08 |

## Idle robots

| Method | Idle AMRs |
|---|---|
| Centralized classic min-cost | - |
| Decentralized classic greedy | - |
| Centralized SOTA proxy | - |
| Decentralized SOTA auction | - |
| Our basic Smith-QR | - |

Best by satisfied loads, reward, then distance: **Centralized SOTA proxy**.

## Artifacts

- `figures/initial_state.png`
- `figures/final_allocations.png`
- `tables/summary.csv`
- `tables/assignments.csv`
- `tables/load_status.csv`
- `videos/allocation_transition.mp4`
