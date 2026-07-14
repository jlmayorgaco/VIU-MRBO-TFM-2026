# SP4_DOCKING_GAME_PILOT

- Worlds: 12
- Runs: 120
- Theory audit: **PASS**
- Plant: dynamic unicycle with wheel-torque saturation.
- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.

## Method summary

| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Directo al contacto | 0.1667 | 0.8333 | 0.0000 | 19.307 | 0.0151 | nan | 0.0125 |
| APF | 0.0000 | 0.1667 | 0.8333 | 22.000 | 0.0425 | nan | 0.1004 |
| RVO proxy | 0.1667 | 0.8333 | 0.0000 | 19.307 | 0.0156 | nan | 0.0141 |
| CBF-QP | 0.0000 | 0.5000 | 0.5000 | 22.000 | 0.0361 | nan | 0.2082 |
| Potencial central | 0.0000 | 0.2500 | 0.7500 | 22.000 | 0.0617 | 0.00534 | 3.0162 |
| Nash-PD exacto | 0.0000 | 0.2500 | 0.7500 | 22.000 | 0.0599 | 0.03370 | 1.3471 |
| Nash-PD anillo | 0.0000 | 0.1667 | 0.8333 | 22.000 | 0.0603 | 0.08954 | 2.1755 |
| Smith + CBF | 0.0000 | 0.2500 | 0.7500 | 22.000 | 0.0618 | 0.05637 | 1.9816 |
| Replicator + CBF | 0.0000 | 0.3333 | 0.6667 | 22.000 | 0.0456 | 1.29690 | 1.7670 |
| ERV-BNN + CBF | 0.0000 | 0.1667 | 0.8333 | 22.000 | 0.0610 | 0.13543 | 1.9505 |

## Frozen hypotheses

| ID | Difference | 95% CI | p Holm | Supported |
|---|---:|---:|---:|---|
| H4P_1_nash_safe_success_above_direct | -0.16667 | [-0.41667, 0.00000] | 1 | no |
| H4P_2_nash_collision_below_apf | 0.08333 | [-0.25000, 0.41667] | 1 | no |
| H4P_3_exact_kkt_below_ring | -0.05585 | [-0.11134, -0.02194] | 0.000732 | yes |

## Audit

- Maximum simplex error: 1.11022e-16
- Maximum capacity violation: 0
- Maximum QP potential gap: 2.43463e-06
- Maximum potential-gradient error: 2.29393e-09
- Position repair after integration: False

## Scope

The QP/KKT certificate applies to the convex receding primitive relaxation. It is not a global certificate for nonlinear multi-robot motion. Barrier residuals are re-evaluated after wheel-torque saturation.
