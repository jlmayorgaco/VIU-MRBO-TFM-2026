# SP4_DOCKING_GAME_CONFIRMATORY_v2

- Worlds: 108
- Runs: 1188
- Theory audit: **PASS**
- Plant: dynamic unicycle with wheel-torque saturation.
- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.

## Method summary

| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Directo al contacto | 0.1574 | 0.8426 | 0.0000 | 30.418 | 0.0275 | nan | 0.0227 |
| APF | 0.1111 | 0.8611 | 0.0278 | 31.782 | 0.0769 | nan | 0.0758 |
| RVO proxy | 0.1574 | 0.8426 | 0.0000 | 30.418 | 0.0277 | nan | 0.0256 |
| CBF-QP | 0.1574 | 0.1759 | 0.6667 | 30.418 | 0.1811 | nan | 1.2817 |
| Potencial central | 0.0278 | 0.1574 | 0.8148 | 34.354 | 0.0962 | 0.13435 | 2.4215 |
| Nash-PD RAW | 0.0278 | 0.1574 | 0.8148 | 34.225 | 0.1006 | 0.21825 | 1.4990 |
| Nash-PD exacto | 0.0278 | 0.1574 | 0.8148 | 34.225 | 0.1016 | 0.20961 | 1.4842 |
| Nash-PD anillo | 0.0278 | 0.1574 | 0.8148 | 34.225 | 0.0837 | 0.46257 | 1.7422 |
| Smith + CBF | 0.0278 | 0.1574 | 0.8148 | 34.371 | 0.0990 | 0.25099 | 1.8072 |
| Replicator + CBF | 0.2593 | 0.1574 | 0.5833 | 28.852 | 0.1477 | 1.48277 | 1.8390 |
| ERV-BNN + CBF | 0.0093 | 0.1574 | 0.8333 | 34.734 | 0.1019 | 0.29910 | 1.8180 |

## Frozen hypotheses

| ID | Difference | 95% CI | p Holm | Supported |
|---|---:|---:|---:|---|
| H4_1_replicator_safe_success_above_cbf | 0.10185 | [0.04630, 0.16667] | 0.000488 | yes |
| H4_2_replicator_collision_below_direct | -0.68519 | [-0.76852, -0.59259] | 2.65e-22 | yes |
| H4_3_exact_kkt_below_ring | -0.25296 | [-0.33973, -0.16023] | 8.05e-10 | yes |
| H4_4_replicator_safe_success_above_nash_pd | 0.23148 | [0.15741, 0.30579] | 5.96e-08 | yes |
| H4_5_replicator_position_error_below_central | -0.88392 | [-1.03870, -0.72939] | 2.73e-17 | yes |

## Audit

- Maximum simplex error: 2.22045e-16
- Maximum capacity violation: 2.22045e-16
- Maximum QP potential gap: 3.53103e-05
- Maximum potential-gradient error: 8.95954e-10
- Position repair after integration: False

## Scope

The QP/KKT certificate applies to the convex receding primitive relaxation. It is not a global certificate for nonlinear multi-robot motion. Barrier residuals are re-evaluated after wheel-torque saturation.
