# SP5_PAYLOAD_TRANSPORT_PILOT_v2

- Worlds: `36`.
- Runs: `288`.
- Execution: CPU only; GPU used: `false`.
- Theory/semantics audit: **PASS**.
- RAW, SAFE and EXEC are stored separately; only EXEC drives the plant.
- No payload or robot position is repaired after integration.

## Method summary

| Method | Safe success | Collision | Timeout | Target s | EXEC barrier | Wrench RMSE | Work J | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Pose PD (RAW) | 0.222 | 0.778 | 0.000 | 41.27 | 0.2677 | 0.000 | 189.2 | 0.1268 |
| APF wrench heuristic | 0.333 | 0.333 | 0.333 | 41.00 | 0.0687 | 0.000 | 171.1 | 0.2191 |
| Velocity-obstacle proxy | 0.667 | 0.333 | 0.000 | 34.43 | 0.1245 | 36.469 | 206.5 | 0.1585 |
| Local CBF wrench filter | 0.667 | 0.000 | 0.333 | 38.20 | 0.0644 | 0.000 | 196.7 | 0.2802 |
| Damped Hamiltonian (RAW) | 0.167 | 0.833 | 0.000 | 42.93 | 0.2575 | 0.000 | 176.0 | 0.1214 |
| Damped Hamiltonian + CBF | 0.611 | 0.000 | 0.389 | 40.60 | 0.0685 | 0.000 | 185.6 | 0.3054 |
| Distributed preview-CBF | 0.417 | 0.000 | 0.583 | 40.62 | 0.0655 | 0.000 | 182.8 | 0.2994 |
| Centralized preview reference | 0.167 | 0.000 | 0.833 | 43.38 | 0.0663 | 0.000 | 203.6 | 0.3331 |

## Frozen confirmatory hypotheses

| ID | Effect | 95% CI | p Holm | Decision |
|---|---:|---:|---:|---|

## Audit and scope

- Minimum initial clearance: `0.241667` m.
- Maximum discrete mechanics residual: `1.13695e-13`.
- Historical semantic finding: The historical SP5 projected payload and robot poses after integration; those runs remain historical and are not canonical evidence for continuous safety.
- Model scope: `reduced_order_planar_rigid_payload_bounded_planar_contact_forces_fixed_post_docking_contacts`.
- Not claimed: No frictional contact, wheel-ground dynamics, kinodynamic optimality, CoppeliaSim or hardware validation is claimed.
