# EXP0 static allocation

- Seed: `20260703`
- Robots: `10` homogeneous AMRs
- Loads: `4` heterogeneous load demands
- Scope: allocation only; no transport dynamics or collision avoidance.

## Methods

| Code | Method | Interpretation |
|---|---|---|
| A | Centralized classic min-cost | Hungarian assignment over replicated load slots. |
| B | Decentralized classic greedy | Sequential nearest-load local rule. |
| C | Centralized SOTA proxy | Reward-aware centralized assignment under scarcity. |
| D | Decentralized SOTA auction | CBBA-like local auction with deficit prices. |
| E | Our basic Smith-QR | Existing Smith-QR allocator facade, no tuning. |

## Summary

| Method | Satisfied loads | Deficit | Overassignment | Idle | Reward | Distance [m] |
|---|---:|---:|---:|---:|---:|---:|
| Centralized classic min-cost | 3/4 | 1 | 0 | 0 | 5.160 | 23.612 |
| Decentralized classic greedy | 3/4 | 1 | 0 | 0 | 5.160 | 23.612 |
| Centralized SOTA proxy | 3/4 | 1 | 0 | 0 | 7.080 | 25.214 |
| Decentralized SOTA auction | 3/4 | 1 | 0 | 0 | 6.580 | 24.864 |
| Our basic Smith-QR | 2/4 | 3 | 2 | 0 | 5.360 | 28.433 |

Best by satisfied loads, reward, then distance: **Centralized SOTA proxy**.

## Artifacts

- `figures/initial_state.png`
- `figures/final_allocations.png`
- `tables/summary.csv`
- `tables/assignments.csv`
- `videos/allocation_transition.mp4`
