# Recomputo de toda la inferencia con la semilla como unidad

Bootstrap percentil pareado sobre semillas, B=10000, semilla de analisis
20260919 (distinta de toda semilla de simulacion). Wilcoxon de rangos
con signo sobre las diferencias por semilla y Holm dentro de la familia
predeclarada de cada campana.

- **celdas**: el `n` impreso originalmente, una fila por
  (escenario x factor x semilla).
- **semillas**: la unidad que declara el protocolo.
- **det.**: el desenlace es identico en todas las semillas. En esos casos no
  se publica intervalo ni valor p: no hay variabilidad muestral que describir.

| Campana | Contraste | n celdas | n semillas | efecto | IC celdas (antiguo) | IC semillas (nuevo) | p Holm nuevo | p Holm antiguo | det. |
|---|---|---:|---:|---:|---|---|---|---|---|
| E2 | `H02_primal_dual_vs_greedy` | 1560 | 40 | -0.1190 | [-0.1274; -0.1106] | [-0.1271; -0.1113] | 1 | 1 |  |
| E2 | `H03_neural_vs_linear_imitation` | 1560 | 40 | -0.0097 | [-0.0118; -0.0077] | [-0.0117; -0.0079] | 3.64e-12 | --- |  |
| E2 | `H04_local_pd_vs_oracle_messages` | 1560 | 40 | -2.8385 | [-3.2250; -2.4558] | [-2.9526; -2.7321] | 3.55e-08 | --- |  |
| E2 | `H05_smith_vs_neural_runtime` | 1560 | 40 | -0.6627 | [-0.6848; -0.6438] | [-0.6871; -0.6422] | 3.64e-12 | --- |  |
| E2-abl | `H_SP2_Marginal_smith_lower_score_gap` | 1560 | 40 | -0.2145 | [-0.2230; -0.2063] | [-0.2230; -0.2065] | 4.55e-12 | --- |  |
| E2-abl | `H_SP2_Marginal_smith_higher_success` | 1560 | 40 | +0.0838 | [+0.0758; +0.0918] | [+0.0763; +0.0915] | 1.78e-08 | --- |  |
| E2-abl | `H_SP2_Marginal_replicator_lower_score_gap` | 1560 | 40 | -0.2103 | [-0.2188; -0.2018] | [-0.2192; -0.2019] | 4.55e-12 | --- |  |
| E2-abl | `H_SP2_Potential_marginal_lower_incomplete_capacity_smith` | 1560 | 40 | -0.0982 | [-0.1078; -0.0888] | [-0.1076; -0.0893] | 4.55e-12 | --- |  |
| E2-abl | `H_SP2_Potential_marginal_higher_alignment_smith` | 1560 | 40 | +0.0877 | [+0.0787; +0.0969] | [+0.0791; +0.0965] | 4.55e-12 | --- |  |
| E3 | `H-SP3-1-guard-reduces-fp` | 600 | 100 | -0.3333 | [-0.3717; -0.2950] | --- | --- | 4.27e-35 | SI |
| E3 | `H-SP3-2-vector-beats-scalar-gap` | 600 | 100 | -0.0933 | [-0.1019; -0.0849] | [-0.0936; -0.0931] | 5.84e-18 | --- |  |
| E3 | `H-SP3-3-pair-beats-cbba-gap` | 600 | 100 | -0.0933 | [-0.1018; -0.0851] | [-0.0935; -0.0931] | 5.84e-18 | --- |  |
| E3 | `H-SP3-4-exact-beats-ring-kkt` | 600 | 100 | -0.0181 | [-0.0201; -0.0161] | [-0.0191; -0.0171] | 5.84e-18 | --- |  |
| E4 | `H4_1_replicator_safe_success_above_cbf` | 108 | 6 | +0.0926 | [+0.0370; +0.1574] | [+0.0463; +0.1296] | 0.0625 | 3.17e-3 |  |
| E4 | `H4_2_replicator_collision_below_direct` | 108 | 6 | -0.8333 | [-0.8981; -0.7593] | --- | --- | --- | SI |
| E4 | `H4_3_exact_kkt_below_ring` | 108 | 6 | -0.3351 | [-0.3952; -0.2725] | [-0.3520; -0.3210] | 0.0625 | --- |  |
| E4 | `H4_4_replicator_safe_success_above_nash_pd` | 108 | 6 | +0.2407 | [+0.1574; +0.3241] | [+0.2222; +0.2593] | 0.0625 | --- |  |
| E4 | `H4_5_replicator_position_error_below_central` | 108 | 6 | -1.0436 | [-1.1869; -0.9033] | [-1.0889; -0.9889] | 0.0625 | --- |  |
| E6-C | `H6.1` | 480 | 40 | +0.7500 | [+0.7104; +0.7875] | --- | --- | 1.3e-108 | SI |
| E6-C | `H6.2` | 480 | 40 | -0.6042 | [-0.7208; -0.4938] | [-0.6979; -0.5083] | 2.54e-08 | 1.6e-21 |  |
| E6-C | `H6.3` | 480 | 40 | +0.2491 | [+0.2149; +0.2856] | [+0.2259; +0.2742] | 1.82e-12 | 1.5e-35 |  |
| E7-C | `H7.1` | 360 | 40 | +0.2611 | [+0.2167; +0.3056] | [+0.2361; +0.2833] | 1.81e-08 | 5.0e-29 |  |
| E7-C | `H7.2` | 360 | 40 | -4.0000 | [-4.3000; -3.7028] | --- | --- | 6.2e-48 | SI |
| E7-C | `H7.3` | 360 | 40 | +1.1528 | [+1.0611; +1.2444] | [+1.1222; +1.1833] | 1.81e-08 | 1.5e-45 |  |

## Lectura

Ningun contraste cambia de signo. Lo que cambia es el tamano de la
evidencia: los valores p caen de ordenes como 1e-108 a los que permiten
40, 100 o 6 semillas, y dos contrastes dejan de tener valor p porque son
deterministas dentro del banco.

## Macros reescritas

- `sp2_numbers.tex`
- `sp2_numbers.tex`
- `sp3_numbers.tex` (sin IC/p por determinismo: SPThreeGuardCIHigh, SPThreeGuardCILow, SPThreeGuardPHolm)
- `sp4_numbers.tex`
- `sp6_numbers.tex` (sin IC/p por determinismo: SPSixHOneCIHigh, SPSixHOneCILow, SPSixHOnePHolm)
- `sp7_numbers.tex` (sin IC/p por determinismo: SPSevenHTwoPHolm)
