# SP1.N4 — Geo-QPG atómico

## Diseño

- Replay descriptivo: 1,200 mundos de N3.
- Confirmatorio: 1,200 mundos nuevos pareados.
- Oráculo: 1,160 mundos con solución y 40 infactibles.
- Soporte común de calidad: 898 mundos.
- El MILP conserva el papel de techo central; no interviene en las decisiones.

## Hipótesis conjunta preespecificada

- Diferencia de factibilidad QPG-CF − GRAPE: 0.34 pp (IC95 % 0.09, 0.69).
- Diferencia mediana de bytes/agente: -16388.0 (IC95 % -16695.8, -16083.5).
- Reducción relativa de bytes: 80.2 %; ratio de tiempo CPU: 1.52.
- Diferencia mediana de gap QPG-CF − GRAPE: -7.16 pp (IC95 % -8.42, -5.77).
- Gate conjunto: PASS.

## Resumen por método

| method              | label               |   worlds |   feasible |   feasibility_rate |   feasibility_low |   feasibility_high |   common_gap_worlds |   common_gap_median |   common_gap_low |   common_gap_high |   bytes_per_agent_median |   bytes_per_agent_q25 |   bytes_per_agent_q75 |   messages_per_agent_median |   rounds_median |   runtime_ms_median |
|:--------------------|:--------------------|---------:|-----------:|-------------------:|------------------:|-------------------:|--------------------:|--------------------:|-----------------:|------------------:|-------------------------:|----------------------:|----------------------:|----------------------------:|----------------:|--------------------:|
| capacity_cbba_rb    | Capacity-CBBA-RB    |     1160 |        916 |           0.789655 |          0.765265 |           0.812133 |                 898 |           0.419701  |        0.387949  |          0.451175 |                  9187.5  |               7706.73 |             10908.7   |                     57.5    |              25 |             26.5228 |
| weighted_grape      | Weighted-GRAPE      |     1160 |       1156 |           0.996552 |          0.991167 |           0.998658 |                 898 |           0.205512  |        0.191182  |          0.225119 |                 20607.6  |              17340.9  |             24265.1   |                    491.094  |             225 |            121.536  |
| weighted_pair_grape | Weighted-Pair-GRAPE |     1160 |       1160 |           1        |          0.996699 |           1        |                 898 |           0.0899509 |        0.0824867 |          0.101994 |                 25481.6  |              20171.6  |             31832.1   |                    607.281  |             289 |            293.112  |
| geo_qpg_u           | Geo-QPG-BR          |     1160 |       1133 |           0.976724 |          0.966346 |           0.983955 |                 898 |           0.570479  |        0.539598  |          0.626616 |                   662.25 |                581.25 |               774.938 |                     19.625  |              39 |              7.867  |
| geo_qpg_p           | Geo-QPG-2BR         |     1160 |       1159 |           0.999138 |          0.995133 |           0.999848 |                 898 |           0.14449   |        0.13174   |          0.157865 |                  3323.62 |               2766.44 |              3987.06  |                     70.4688 |             281 |            142.585  |
| geo_qpg_cf          | Geo-QPG-CF (global) |     1160 |       1160 |           1        |          0.996699 |           1        |                 898 |           0.111743  |        0.100686  |          0.120794 |                  4080    |               3182.56 |              5209.19  |                     79.1562 |              16 |            185.159  |

## Alcance

- The terminal point is local to the admitted unilateral or neighbour-pair neighbourhood.
- A feasible MILP instance need not be reached by a strict-improvement path from idle.
- Atomic multi-register commit and reliable ordered broadcasts are protocol assumptions.
- No result in this campaign establishes transport, contact, physical safety or global optimality.
