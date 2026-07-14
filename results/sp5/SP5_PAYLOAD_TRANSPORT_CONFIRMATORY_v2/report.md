# SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2

- Worlds: `108`.
- Runs: `864`.
- Execution: CPU only; GPU used: `false`.
- Theory/semantics audit: **PASS**.
- RAW, SAFE and EXEC are stored separately; only EXEC drives the plant.
- No payload or robot position is repaired after integration.

## Method summary

| Method | Safe success | Collision | Timeout | Target s | EXEC barrier | Wrench RMSE | Work J | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pose PD (RAW) | 0.259 | 0.741 | 0.000 | 40.52 | 0.2637 | 0.000 | 190.5 | 0.1303 |
| APF wrench heuristic | 0.333 | 0.333 | 0.333 | 41.00 | 0.0625 | 0.000 | 172.9 | 0.2164 |
| Velocity-obstacle proxy | 0.657 | 0.343 | 0.000 | 33.57 | 0.1170 | 8.441 | 208.8 | 0.1491 |
| Local CBF wrench filter | 0.593 | 0.000 | 0.407 | 38.94 | 0.0637 | 0.000 | 199.4 | 0.2864 |
| Damped Hamiltonian (RAW) | 0.167 | 0.833 | 0.000 | 42.93 | 0.2551 | 0.000 | 177.3 | 0.1229 |
| Damped Hamiltonian + CBF | 0.426 | 0.000 | 0.574 | 40.73 | 0.0681 | 0.000 | 188.0 | 0.2967 |
| Distributed preview-CBF | 0.398 | 0.000 | 0.602 | 40.66 | 0.0655 | 0.000 | 184.7 | 0.2980 |
| Centralized preview reference | 0.167 | 0.000 | 0.833 | 43.38 | 0.0662 | 0.000 | 206.4 | 0.3345 |

## Frozen confirmatory hypotheses

| ID | Effect | 95% CI | p Holm | Decision |
|---|---:|---:|---:|---|
| H5_1_hamiltonian_cbf_reduces_collision_vs_raw | -0.8333 | [-0.8981, -0.7593] | 4.039e-27 | supported |
| H5_2_hamiltonian_cbf_improves_safe_success_vs_raw | 0.2593 | [0.1759, 0.3426] | 1.118e-08 | supported |
| H5_3_central_preview_improves_safe_success_vs_local_cbf | -0.4259 | [-0.5185, -0.3333] | 1 | not_supported |
| H5_4_local_cbf_reduces_exec_barrier_violation_vs_apf | 0.0012 | [-0.0305, 0.0390] | 0.003764 | not_supported |
| H5_5_preview_cbf_reduces_collision_vs_vo_proxy | -0.3426 | [-0.4352, -0.2593] | 2.91e-11 | supported |

## Audit and scope

- Minimum initial clearance: `0.241667` m.
- Maximum discrete mechanics residual: `1.13912e-13`.
- Historical semantic finding: The historical SP5 projected payload and robot poses after integration; those runs remain historical and are not canonical evidence for continuous safety.
- Model scope: `reduced_order_planar_rigid_payload_bounded_planar_contact_forces_fixed_post_docking_contacts`.
- Not claimed: No frictional contact, wheel-ground dynamics, kinodynamic optimality, CoppeliaSim or hardware validation is claimed.
