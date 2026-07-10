# SP3_POSE_euler_lagrange_transport

SP3 pose transport adds a dynamic rigid-payload check after role/slot recruitment.

## Model

The payload state is `q=[x,y,theta]`. The planar Euler-Lagrange form used in the simulation is:

```math
M(q) \ddot q + D \dot q = G(q)\lambda, \quad 0 \le \lambda_i \le f_i^{max}.
```

The Hamiltonian diagnostic is:

```math
H(q,\dot q)=\frac{1}{2}\dot q^T M \dot q + V(q).
```

The vector-game signal is the residual-support payoff induced by the current generalized wrench error. It is not a full contact/friction simulator; it is a controlled planar rigid-body feasibility demonstration.

## Summary

| Metric | Value |
|---|---:|
| `final_position_error_m` | 0.3566 |
| `final_orientation_error_deg` | 0.0810 |
| `hamiltonian_drop` | 124.3519 |
| `mean_residual_norm` | 0.1714 |
| `max_torque_nm` | 42.0275 |
| `slot_coverage_ratio` | 1.0000 |
| `assigned_robots` | 4.0000 |

## Artifacts

- Snapshot: `results\sp3\SP3_POSE_euler_lagrange_transport\figures\sp3-pose-transport-pose-transport-rotate-wrench-oracle-seed5200.png`
- MP4: `results\sp3\SP3_POSE_euler_lagrange_transport\videos\sp3-pose-transport-pose-transport-rotate-wrench-oracle-seed5200.mp4` (ok)
- Trajectory CSV: `tables/pose_trajectory.csv`
