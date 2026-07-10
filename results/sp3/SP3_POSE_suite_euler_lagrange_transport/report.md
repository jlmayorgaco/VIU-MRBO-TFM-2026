# SP3_POSE_suite_euler_lagrange_transport

SP3 dynamic pose-transport suite compares centralized, decentralized, classic, SOTA-proxy and proposed role/slot methods after wrench-aware recruitment.

## Model

```math
M(q) \ddot q + D \dot q = G(q)\lambda, \quad 0 \le \lambda_i \le f_i^{max}
```

The payload state is `q=[x,y,theta]`. Each AMR contact contributes a planar wrench column `[d_x,d_y,r_x d_y-r_y d_x]^T`; the controller projects a desired generalized wrench onto bounded slot forces. The Hamiltonian diagnostic is `H=0.5 qd^T M qd + V(q)`.

When `complete_uncovered_slots=True`, the dynamic demo fills uncovered target-load slots with nearest idle AMR after the selected allocator. That option is for visual/physical pose transport examples; the assignment benchmark remains the strict SP3 Monte Carlo v3.

## Summary

- Runs: `18`.
- Cases: `3`.
- Methods: `6`.
- Pose success rate: `0.611`.
- Theory failed checks: `0`.

## Runs

| Case | Regime | Movement | Method | Family | Scope | Owner | Success | Slots | Pos err m | Ori err deg | H drop | Video |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | wrench_oracle | model_based_oracle | centralized | reference | True | 1.00 | 0.301 | 3.25 | 669.33 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-wrench-oracle-seed5300.mp4 |
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | hungarian_slots | classic | centralized | baseline | True | 1.00 | 0.301 | 3.25 | 669.33 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-hungarian-slots-seed5300.mp4 |
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | capacity_greedy_slots | classic | decentralized | baseline | True | 1.00 | 0.301 | 3.25 | 669.33 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-capacity-greedy-slots-seed5300.mp4 |
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | cbba_slots | sota | decentralized | baseline | True | 1.00 | 0.301 | 3.25 | 669.33 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-cbba-slots-seed5300.mp4 |
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | smith_wrench_deficit | model_based | decentralized | proposed | True | 1.00 | 0.301 | 3.25 | 669.33 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-smith-wrench-deficit-seed5300.mp4 |
| overactuated_push_more_robots_than_loads | more_robots_than_loads | push | support_dual_wrench_market | model_based | decentralized | proposed | True | 1.00 | 0.314 | 3.40 | 669.23 | sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-support-dual-wrench-market-seed5300.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | wrench_oracle | model_based_oracle | centralized | reference | False | 0.25 | 2.805 | 58.96 | 194.92 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-wrench-oracle-seed5301.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | hungarian_slots | classic | centralized | baseline | True | 1.00 | 0.039 | 14.98 | 301.98 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-hungarian-slots-seed5301.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | capacity_greedy_slots | classic | decentralized | baseline | False | 0.50 | 2.805 | 58.96 | 194.92 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-capacity-greedy-slots-seed5301.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | cbba_slots | sota | decentralized | baseline | False | 0.25 | 3.633 | 17.47 | 141.27 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-cbba-slots-seed5301.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | smith_wrench_deficit | model_based | decentralized | proposed | True | 1.00 | 0.040 | 14.82 | 302.00 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-smith-wrench-deficit-seed5301.mp4 |
| balanced_push_drag_equal_robots_loads | equal_robots_loads | push_drag | support_dual_wrench_market | model_based | decentralized | proposed | True | 0.75 | 0.391 | 14.89 | 299.66 | sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-support-dual-wrench-market-seed5301.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | wrench_oracle | model_based_oracle | centralized | reference | False | 0.75 | 1.502 | 17.97 | 254.08 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-wrench-oracle-seed5302.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | hungarian_slots | classic | centralized | baseline | True | 0.75 | 0.641 | 9.70 | 281.94 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-hungarian-slots-seed5302.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | capacity_greedy_slots | classic | decentralized | baseline | True | 0.75 | 0.641 | 9.70 | 281.94 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-capacity-greedy-slots-seed5302.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | cbba_slots | sota | decentralized | baseline | False | 0.00 | 4.778 | 74.00 | 0.00 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-cbba-slots-seed5302.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | smith_wrench_deficit | model_based | decentralized | proposed | False | 0.75 | 1.502 | 17.97 | 254.08 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-smith-wrench-deficit-seed5302.mp4 |
| scarce_heavy_cargo_fewer_robots_than_loads | fewer_robots_than_loads | cargo_push_drag | support_dual_wrench_market | model_based | decentralized | proposed | False | 0.75 | 1.502 | 17.97 | 254.08 | sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-support-dual-wrench-market-seed5302.mp4 |

## Videos

- `overactuated_push_more_robots_than_loads` `wrench_oracle` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-wrench-oracle-seed5300.mp4`
- `overactuated_push_more_robots_than_loads` `hungarian_slots` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-hungarian-slots-seed5300.mp4`
- `overactuated_push_more_robots_than_loads` `capacity_greedy_slots` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-capacity-greedy-slots-seed5300.mp4`
- `overactuated_push_more_robots_than_loads` `cbba_slots` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-cbba-slots-seed5300.mp4`
- `overactuated_push_more_robots_than_loads` `smith_wrench_deficit` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-smith-wrench-deficit-seed5300.mp4`
- `overactuated_push_more_robots_than_loads` `support_dual_wrench_market` seed `5300`: `sp3-pose-overactuated-push-more-robots-than-loads-pose-push-overactuated-support-dual-wrench-market-seed5300.mp4`
- `balanced_push_drag_equal_robots_loads` `wrench_oracle` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-wrench-oracle-seed5301.mp4`
- `balanced_push_drag_equal_robots_loads` `hungarian_slots` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-hungarian-slots-seed5301.mp4`
- `balanced_push_drag_equal_robots_loads` `capacity_greedy_slots` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-capacity-greedy-slots-seed5301.mp4`
- `balanced_push_drag_equal_robots_loads` `cbba_slots` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-cbba-slots-seed5301.mp4`
- `balanced_push_drag_equal_robots_loads` `smith_wrench_deficit` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-smith-wrench-deficit-seed5301.mp4`
- `balanced_push_drag_equal_robots_loads` `support_dual_wrench_market` seed `5301`: `sp3-pose-balanced-push-drag-equal-robots-loads-pose-push-drag-balanced-support-dual-wrench-market-seed5301.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `wrench_oracle` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-wrench-oracle-seed5302.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `hungarian_slots` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-hungarian-slots-seed5302.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `capacity_greedy_slots` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-capacity-greedy-slots-seed5302.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `cbba_slots` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-cbba-slots-seed5302.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `smith_wrench_deficit` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-smith-wrench-deficit-seed5302.mp4`
- `scarce_heavy_cargo_fewer_robots_than_loads` `support_dual_wrench_market` seed `5302`: `sp3-pose-scarce-heavy-cargo-fewer-robots-than-loads-pose-cargo-scarce-support-dual-wrench-market-seed5302.mp4`

## Artifacts

- `tables/pose_runs.csv`
- `tables/pose_theory_checks.csv`
- `tables/trajectories/*.csv`
- `figures/sp3_pose_transport_suite_performance.png`
- `videos/*.mp4`
- `theory_audit.json`
