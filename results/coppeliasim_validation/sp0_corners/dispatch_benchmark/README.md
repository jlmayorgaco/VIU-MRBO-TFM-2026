# SP0 dispatch benchmark

Layout used: 8 Pioneer AMR, 6 simultaneous homogeneous box tasks, 3 unload targets, 2x motion speed, battery-aware assignment.

The previous balanced-only result was expected to be close because the scene is symmetric and saturated with available robots. This report adds a naive FIFO-nearest baseline and stress cases.

Fitness and objective definitions:

- Pair objective: `c_ij = d(robot_i,pickup_j) + d(pickup_j,target_j) + 0.35*d(target_j,base_i) + 0.035*(100-battery_i)`.
- Pair fitness: `f_ij = 1/(1+c_ij)` for feasible battery assignments; infeasible pairs use `f_ij=0`.
- Controller objective: `J(t)=sum(c_ij)` over assignments selected at decision time `t`.
- Hungarian optimum: `J*_H(t)` is recomputed at the same state, candidates and pending jobs. `j_regret` adds a large penalty for missed assignments.

## Summary

| Case | Policy | Delivered | Avg wait s | Energy used pct | Assignment cost | Charge cycles |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Balanced | FIFO nearest | 45.4167 | 14.4110 | 2177.6302 | 782.6749 | 43.1667 |
| Balanced | Hungarian | 46.9167 | 13.8091 | 2169.6796 | 781.4985 | 45.9167 |
| Balanced | Greedy dist. | 46.8333 | 13.7304 | 2165.9090 | 793.7428 | 45.5000 |
| Balanced | Replicator | 46.9167 | 13.7742 | 2168.9502 | 782.5690 | 46.0000 |
| Battery stress | FIFO nearest | 6.6667 | 34.2024 | 362.6211 | 108.5914 | 6.3333 |
| Battery stress | Hungarian | 6.5000 | 46.5595 | 362.9487 | 108.8923 | 6.3333 |
| Battery stress | Greedy dist. | 6.5000 | 46.5595 | 362.9487 | 108.8923 | 6.3333 |
| Battery stress | Replicator | 6.5000 | 46.5595 | 362.9487 | 108.8923 | 6.3333 |
| Scarce robots | FIFO nearest | 32.9167 | 20.9330 | 1697.5210 | 568.7566 | 31.3333 |
| Scarce robots | Hungarian | 33.4167 | 20.8344 | 1703.1686 | 581.0763 | 32.5833 |
| Scarce robots | Greedy dist. | 33.4167 | 20.6340 | 1703.5796 | 577.3228 | 32.6667 |
| Scarce robots | Replicator | 33.3333 | 20.3355 | 1691.7167 | 571.0661 | 32.4167 |
| Target skew | FIFO nearest | 36.3333 | 18.1214 | 1979.7094 | 611.0002 | 35.2500 |
| Target skew | Hungarian | 35.6667 | 16.6904 | 1949.4923 | 610.6802 | 34.9167 |
| Target skew | Greedy dist. | 34.2500 | 17.4127 | 1866.0799 | 581.9218 | 33.3333 |
| Target skew | Replicator | 35.6667 | 16.8650 | 1949.9991 | 611.1983 | 34.8333 |

## Delta vs FIFO-nearest baseline

| Case | Policy | Delivered delta % | Wait delta % | Energy delta % | Assignment cost delta % |
| --- | --- | ---: | ---: | ---: | ---: |
| Balanced | Hungarian | 3.3027 | -4.1767 | -0.3651 | -0.1503 |
| Balanced | Greedy dist. | 3.1191 | -4.7228 | -0.5383 | 1.4141 |
| Balanced | Replicator | 3.3027 | -4.4188 | -0.3986 | -0.0135 |
| Battery stress | Hungarian | -2.5005 | 36.1293 | 0.0903 | 0.2771 |
| Battery stress | Greedy dist. | -2.5005 | 36.1293 | 0.0903 | 0.2771 |
| Battery stress | Replicator | -2.5005 | 36.1293 | 0.0903 | 0.2771 |
| Scarce robots | Hungarian | 1.5190 | -0.4710 | 0.3327 | 2.1661 |
| Scarce robots | Greedy dist. | 1.5190 | -1.4284 | 0.3569 | 1.5061 |
| Scarce robots | Replicator | 1.2656 | -2.8543 | -0.3419 | 0.4061 |
| Target skew | Hungarian | -1.8347 | -7.8967 | -1.5263 | -0.0524 |
| Target skew | Greedy dist. | -5.7339 | -3.9108 | -5.7397 | -4.7591 |
| Target skew | Replicator | -1.8347 | -6.9332 | -1.5007 | 0.0324 |

## Gap vs instantaneous Hungarian optimum

| Case | Policy | J mean | J*_H mean | J gap mean | Regret mean | Assignment count gap | Hungarian pair match |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced | Greedy dist. | 17.7043 | 17.6565 | 0.0478 | 0.0478 | 0.0000 | 0.8918 |
| Balanced | Replicator | 17.1365 | 17.1362 | 0.0003 | 0.0003 | 0.0000 | 0.9934 |
| Battery stress | Greedy dist. | 15.5560 | 15.5560 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| Battery stress | Replicator | 15.5560 | 15.5560 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| Scarce robots | Greedy dist. | 17.4067 | 17.5845 | 0.0021 | 10.0523 | 0.0100 | 0.9644 |
| Scarce robots | Replicator | 17.5713 | 17.5205 | 0.0508 | 0.0508 | 0.0000 | 0.9091 |
| Target skew | Greedy dist. | 16.6263 | 17.2140 | 0.0020 | 35.7163 | 0.0357 | 0.9310 |
| Target skew | Replicator | 16.9385 | 16.9382 | 0.0003 | 0.0003 | 0.0000 | 0.9957 |

Interpretation: when the case is balanced, all cost-aware policies remain close. The useful comparison is against `FIFO nearest`, which ignores target and return-energy cost. Stress cases expose whether the cost-aware dispatchers reduce assignment cost, energy, or wait.

Files:

- `dispatch_policy_runs.csv`: per-seed raw runs.
- `dispatch_policy_summary.csv`: mean/std by case and policy.
- `dispatch_policy_baseline_delta.csv`: percentage deltas vs FIFO-nearest baseline.
- `dispatch_policy_ci.csv`: mean, standard error and 95% confidence intervals by metric.
- `dispatch_seed_hungarian_gap.csv`: per-seed distance to the instantaneous Hungarian optimum.
- `dispatch_statistical_tests.csv`: paired per-seed deltas, 95% CI, Cohen dz and better-rate tests.
- `dispatch_time_integrals.csv`: time-weighted battery, objective and regret integrals.
- `dispatch_robot_trace.csv`: sampled robot `x_m`, `y_m`, state and battery life over time.
- `dispatch_objective_trace.csv`: `J(t)`, `J*_H(t)`, gap/regret and fitness stats per decision event.
- `dispatch_assignment_trace.csv`: selected robot-box pairs with cost, fitness and battery at assignment time.
- `dispatch_hungarian_gap_summary.csv`: aggregate distance to instantaneous Hungarian optimum.
- `dispatch_policy_comparison.png`: grouped comparison by case.
- `dispatch_policy_baseline_delta.png`: deltas vs baseline.
- `dispatch_policy_scatter.png`: delivery vs cumulative energy scatter.
- `dispatch_objective_j_vs_t.png`: objective function over time for the three controllers.
- `dispatch_hungarian_regret_vs_t.png`: greedy/replicator regret against Hungarian over time.
- `dispatch_battery_life_vs_t.png`: average battery life over time.
- `dispatch_xy_trajectories_seed0_balanced.png`: sampled XY trajectories for the three controllers.
- `dispatch_ieee_metric_ci.png/.pdf`: publication-style metric panel with 95% CI.
- `dispatch_pareto_energy_wait.png/.pdf`: energy-wait Pareto map with callout arrows.
- `dispatch_optimality_heatmap.png/.pdf`: Hungarian match-rate heatmap with regret annotations.
- `dispatch_regret_boxplot.png/.pdf`: per-seed regret distribution.
- `dispatch_battery_quantile_bands.png/.pdf`: median and IQR battery traces.
- `dispatch_regret_ecdf.png/.pdf`: empirical regret distribution with right-tail callouts.
- `dispatch_robot_state_timeline_seed0_target_skew.png/.pdf`: robot state timeline sample.
