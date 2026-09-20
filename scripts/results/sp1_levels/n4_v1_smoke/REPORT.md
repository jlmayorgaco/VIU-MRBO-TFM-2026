# SP1.N4 — Geo-QPG atómico

## Diseño

- Replay descriptivo: 8 mundos de N3.
- Confirmatorio: 8 mundos nuevos pareados.
- Soporte común de calidad: 4 mundos.
- El MILP conserva el papel de techo central; no interviene en las decisiones.

## Hipótesis conjunta preespecificada

- Diferencia de factibilidad QPG-CF − GRAPE: 0.00 pp (IC95 % 0.00, 0.00).
- Diferencia mediana de bytes/agente: -18654.4 (IC95 % -21901.3, -16385.9).
- Gate conjunto: PASS.

## Resumen por método

| method              | label               |   worlds |   feasible |   feasibility_rate |   feasibility_low |   feasibility_high |   common_gap_worlds |   common_gap_median |   common_gap_low |   common_gap_high |   bytes_per_agent_median |   bytes_per_agent_q25 |   bytes_per_agent_q75 |   messages_per_agent_median |   rounds_median |   runtime_ms_median |
|:--------------------|:--------------------|---------:|-----------:|-------------------:|------------------:|-------------------:|--------------------:|--------------------:|-----------------:|------------------:|-------------------------:|----------------------:|----------------------:|----------------------------:|----------------:|--------------------:|
| capacity_cbba_rb    | Capacity-CBBA-RB    |        8 |          4 |                0.5 |          0.215216 |           0.784784 |                   4 |           0.303735  |      0.071907    |          0.483523 |                 8018.41  |               6807.5  |              9466.14  |                     49.9688 |            24   |            23.1892  |
| weighted_grape      | Weighted-GRAPE      |        8 |          8 |                1   |          0.675592 |           1        |                   4 |           0.224681  |      0.0314023   |          0.462443 |                23787.2   |              22641.9  |             25125.3   |                    566.906  |           257   |           117.728   |
| weighted_pair_grape | Weighted-Pair-GRAPE |        8 |          8 |                1   |          0.675592 |           1        |                   4 |           0.0160157 |     -3.96466e-16 |          0.361549 |                28785.8   |              24513.7  |             30932.9   |                    685.844  |           337   |           295.6     |
| geo_qpg_u           | Geo-QPG-U           |        8 |          8 |                1   |          0.675592 |           1        |                   4 |           0.597895  |      0.47655     |          1.26536  |                  649.875 |                588    |               802.312 |                     19.1562 |            34.5 |             6.86855 |
| geo_qpg_p           | Geo-QPG-P           |        8 |          8 |                1   |          0.675592 |           1        |                   4 |           0.151446  |     -3.96466e-16 |          0.499276 |                 3974.12  |               3609.5  |              4043.44  |                     84.2812 |           305.5 |           138.769   |
| geo_qpg_cf          | Geo-QPG-CF          |        8 |          8 |                1   |          0.675592 |           1        |                   4 |           0.059712  |     -3.96466e-16 |          0.242317 |                 4128.25  |               3414.44 |              4683.62  |                     80.2812 |            16.5 |           158.82    |

## Alcance

- The terminal point is local to the admitted unilateral or neighbour-pair neighbourhood.
- A feasible MILP instance need not be reached by a strict-improvement path from idle.
- Atomic multi-register commit and reliable ordered broadcasts are protocol assumptions.
- No result in this campaign establishes transport, contact, physical safety or global optimality.
