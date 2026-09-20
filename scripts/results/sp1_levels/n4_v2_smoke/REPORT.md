# SP1.N4 — familia Geo-QPG distribuida

La comparación atómica contiene 12 mundos pareados y 120 filas.
QPG-CF se conserva como ablación con orden global; Geo-QPG-DMIS+TX es la variante distribuida principal.

## Resultados por método

| method              | label               |   worlds |   feasibility |   feasibility_low |   feasibility_high |   gap_median |      gap_low |    gap_high |   runtime_ms_median |   bytes_per_agent_median |   rounds_median |
|:--------------------|:--------------------|---------:|--------------:|------------------:|-------------------:|-------------:|-------------:|------------:|--------------------:|-------------------------:|----------------:|
| capacity_cbba_rb    | CBBA-RB             |       12 |          0.75 |          0.467695 |           0.911058 |  0.143976    |  0.09851     | 0.748054    |             23.9756 |                 8302.34  |            24.5 |
| weighted_grape      | GRAPE               |       12 |          1    |          0.757506 |           1        |  0.039565    |  0.0329111   | 0.162203    |            131.075  |                20675.6   |           233   |
| weighted_pair_grape | Pair-GRAPE          |       12 |          1    |          0.757506 |           1        |  6.08034e-17 |  0           | 2.69147e-16 |            264.619  |                24730.5   |           289   |
| geo_qpg_u           | Geo-QPG-BR          |       12 |          1    |          0.757506 |           1        |  0.583443    |  0.464956    | 1.01719     |              8.9619 |                  517.875 |            29.5 |
| geo_qpg_smith       | Geo-Smith atómico   |       12 |          1    |          0.757506 |           1        |  1.03347     |  0.718483    | 1.20688     |              6.7787 |                  520.5   |            32   |
| geo_qpg_lll         | Geo-LLL atómico     |       12 |          1    |          0.757506 |           1        |  1.01746     |  0.65258     | 1.25514     |             26.3492 |                 4989.75  |           151.5 |
| geo_qpg_p           | Geo-QPG-2BR         |       12 |          1    |          0.757506 |           1        |  0.013672    |  1.34917e-16 | 0.136695    |            160.793  |                 3778.5   |           291.5 |
| geo_qpg_c3          | Geo-QPG-C3          |       12 |          1    |          0.757506 |           1        |  0           | -5.67471e-17 | 1.52273e-16 |           2105.11   |                13234.4   |           765.5 |
| geo_qpg_cf          | Geo-QPG-CF (global) |       12 |          1    |          0.757506 |           1        |  6.08034e-17 |  0           | 2.99813e-16 |            147.247  |                 2964.25  |            14.5 |
| geo_qpg_d           | Geo-QPG-DMIS+TX     |       12 |          1    |          0.757506 |           1        |  6.08034e-17 |  0           | 2.99813e-16 |            129.742  |                 4314.88  |            14.5 |

## Exactitud pequeña

DPOP y MILP coincidieron en factibilidad en 2/2 mundos. 
El error objetivo máximo fue 4.263e-14.

## Límites

- DMIS and TX are evaluated with reliable ordered delivery and no keeper crash.
- DPOP is exact only inside the explicit profile limit and is not a scalable candidate.
- Population dynamics use a different relaxed model and campaign; their numbers are contextual, not a direct ranking against atomic N4.
- No N4 result establishes transport, contact stability, collision avoidance or global optimality of the distributed heuristics.
