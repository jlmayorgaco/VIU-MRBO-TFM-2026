# SP4_DOCKING_GAME_PILOT_v3

- Worlds: 18
- Runs: 198
- Theory audit: **PASS**
- Plant: dynamic unicycle with wheel-torque saturation.
- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.

## Method summary

| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Directo al contacto | 0.1667 | 0.8333 | 0.0000 | 30.127 | 0.0318 | nan | 0.0238 |
| APF | 0.1111 | 0.7778 | 0.1111 | 31.751 | 0.1207 | nan | 0.1529 |
| RVO proxy | 0.1667 | 0.8333 | 0.0000 | 30.127 | 0.0329 | nan | 0.0281 |
| Proyeccion CBF | 0.1667 | 0.0000 | 0.8333 | 30.127 | 0.2208 | nan | 1.7382 |
| PD central (70 iter.) | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.0883 | 0.00142 | 2.7530 |
| Nash-PD RAW | 0.0556 | 0.0000 | 0.9444 | 33.624 | 0.0926 | 0.03598 | 1.7916 |
| Nash-PD exacto | 0.0556 | 0.0000 | 0.9444 | 33.624 | 0.0933 | 0.00624 | 1.9683 |
| Nash-PD anillo | 0.0556 | 0.0000 | 0.9444 | 33.624 | 0.0890 | 0.40464 | 2.1973 |
| Smith + CBF | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.0967 | 0.01286 | 2.4121 |
| Replicator + CBF | 0.2778 | 0.0000 | 0.7222 | 29.091 | 0.1726 | 1.46582 | 2.3621 |
| ERV-BNN + CBF | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.0900 | 0.07348 | 2.3173 |

## Frozen hypotheses

| ID | Difference | 95% CI | p Holm | Supported |
|---|---:|---:|---:|---|
| H4_1_replicator_safe_success_above_cbf | 0.11111 | [0.00000, 0.27778] | 0.25 | no |
| H4_2_replicator_collision_below_direct | -0.83333 | [-1.00000, -0.66667] | 0.000122 | yes |
| H4_3_exact_kkt_below_ring | -0.39840 | [-0.52962, -0.26092] | 0.000527 | yes |
| H4_4_replicator_safe_success_above_nash_pd | 0.22222 | [0.05556, 0.44444] | 0.125 | no |
| H4_5_replicator_position_error_below_central | -1.09903 | [-1.43736, -0.75652] | 1.91e-05 | yes |

## Audit

- Maximum simplex error: 4.44089e-16
- Maximum capacity violation: 4.44089e-16
- Maximum QP potential gap: 4.20186e-06
- Maximum potential-gradient error: 6.21347e-09
- Initial collisions: 0
- Minimum initial clearance: 0.356114
- Position repair after integration: False

## Scope

The QP/KKT certificate applies to the convex receding primitive relaxation. It is not a global certificate for nonlinear multi-robot motion. Barrier residuals are re-evaluated after wheel-torque saturation.
