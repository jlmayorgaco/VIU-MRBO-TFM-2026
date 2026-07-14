# SP4_DOCKING_GAME_CONFIRMATORY_v3

- Worlds: 108
- Runs: 1188
- Theory audit: **PASS**
- Plant: dynamic unicycle with wheel-torque saturation.
- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.

## Method summary

| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Directo al contacto | 0.1667 | 0.8333 | 0.0000 | 30.128 | 0.0326 | nan | 0.0252 |
| APF | 0.1111 | 0.7593 | 0.1296 | 31.757 | 0.1230 | nan | 0.1365 |
| RVO proxy | 0.1667 | 0.8333 | 0.0000 | 30.128 | 0.0347 | nan | 0.0281 |
| Proyeccion CBF | 0.1759 | 0.0000 | 0.8241 | 29.921 | 0.2243 | nan | 1.5984 |
| PD central (70 iter.) | 0.0370 | 0.0000 | 0.9630 | 33.941 | 0.1180 | 0.06611 | 2.9393 |
| Nash-PD RAW | 0.0278 | 0.0000 | 0.9722 | 34.210 | 0.1180 | 0.05756 | 1.8428 |
| Nash-PD exacto | 0.0278 | 0.0000 | 0.9722 | 34.210 | 0.1203 | 0.08920 | 1.7667 |
| Nash-PD anillo | 0.0093 | 0.0000 | 0.9907 | 34.734 | 0.0798 | 0.42435 | 2.0380 |
| Smith + CBF | 0.0093 | 0.0000 | 0.9907 | 34.789 | 0.1154 | 0.12860 | 2.1641 |
| Replicator + CBF | 0.2685 | 0.0000 | 0.7315 | 28.789 | 0.1778 | 1.70355 | 2.2505 |
| ERV-BNN + CBF | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.1166 | 0.18841 | 2.1573 |

## Frozen hypotheses

| ID | Difference | 95% CI | p Holm | Supported |
|---|---:|---:|---:|---|
| H4_1_replicator_safe_success_above_cbf | 0.09259 | [0.03704, 0.15741] | 0.00317 | yes |
| H4_2_replicator_collision_below_direct | -0.83333 | [-0.89815, -0.75926] | 4.04e-27 | yes |
| H4_3_exact_kkt_below_ring | -0.33515 | [-0.39517, -0.27601] | 1.81e-14 | yes |
| H4_4_replicator_safe_success_above_nash_pd | 0.24074 | [0.15741, 0.32407] | 2.98e-08 | yes |
| H4_5_replicator_position_error_below_central | -1.04355 | [-1.18813, -0.90669] | 3.74e-19 | yes |

## Audit

- Maximum simplex error: 2.22045e-16
- Maximum capacity violation: 0
- Maximum QP potential gap: 0.000113904
- Maximum potential-gradient error: 8.07025e-10
- Initial collisions: 0
- Minimum initial clearance: 0.272366
- Position repair after integration: False

## Scope

The QP/KKT certificate applies to the convex receding primitive relaxation. It is not a global certificate for nonlinear multi-robot motion. Barrier residuals are re-evaluated after wheel-torque saturation.
