# SP4_DOCKING_GAME_PILOT_v2

- Worlds: 12
- Runs: 132
- Theory audit: **PASS**
- Plant: dynamic unicycle with wheel-torque saturation.
- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.

## Method summary

| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Directo al contacto | 0.1667 | 0.8333 | 0.0000 | 30.113 | 0.0151 | nan | 0.0138 |
| APF | 0.1667 | 0.6667 | 0.1667 | 30.113 | 0.0439 | nan | 0.0710 |
| RVO proxy | 0.1667 | 0.8333 | 0.0000 | 30.113 | 0.0162 | nan | 0.0141 |
| CBF-QP | 0.1667 | 0.0000 | 0.8333 | 30.113 | 0.1016 | nan | 0.6744 |
| Potencial central | 0.1667 | 0.0000 | 0.8333 | 30.193 | 0.0453 | 0.00481 | 1.2648 |
| Nash-PD RAW | 0.0833 | 0.0000 | 0.9167 | 32.857 | 0.0506 | 0.00505 | 0.8072 |
| Nash-PD exacto | 0.0833 | 0.0000 | 0.9167 | 32.857 | 0.0471 | 0.02656 | 0.8161 |
| Nash-PD anillo | 0.0833 | 0.0000 | 0.9167 | 32.857 | 0.0462 | 0.04063 | 1.2332 |
| Smith + CBF | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.0494 | 0.00120 | 1.2881 |
| Replicator + CBF | 0.5833 | 0.0000 | 0.4167 | 24.970 | 0.0813 | 1.44000 | 1.1311 |
| ERV-BNN + CBF | 0.0000 | 0.0000 | 1.0000 | 35.000 | 0.0518 | 0.09110 | 1.2625 |

## Frozen hypotheses

| ID | Difference | 95% CI | p Holm | Supported |
|---|---:|---:|---:|---|
| H4P_1_replicator_safe_success_above_cbf | 0.41667 | [0.16667, 0.66667] | 0.0625 | no |
| H4P_2_replicator_collision_below_direct | -0.83333 | [-1.00000, -0.58333] | 0.00293 | yes |
| H4P_3_exact_kkt_below_ring | -0.01408 | [-0.02030, -0.00795] | 0.000977 | yes |
| H4P_4_closure_safe_success_above_raw | 0.00000 | [0.00000, 0.00000] | 1 | no |

## Audit

- Maximum simplex error: 4.44089e-16
- Maximum capacity violation: 4.44089e-16
- Maximum QP potential gap: 5.52185e-05
- Maximum potential-gradient error: 9.27532e-10
- Position repair after integration: False

## Scope

The QP/KKT certificate applies to the convex receding primitive relaxation. It is not a global certificate for nonlinear multi-robot motion. Barrier residuals are re-evaluated after wheel-torque saturation.
