# SP1.N4 — familia Geo-QPG distribuida

La comparación atómica contiene 1200 mundos pareados y 12000 filas.
QPG-CF se conserva como ablación con orden global; Geo-QPG-DMIS+TX es la variante distribuida principal.

## Resultados por método

| method              | label                            |   worlds |   feasibility |   feasibility_low |   feasibility_high |   gap_median |   gap_low |   gap_high |   runtime_ms_median |   bytes_per_agent_median |   rounds_median |
|:--------------------|:---------------------------------|---------:|--------------:|------------------:|-------------------:|-------------:|----------:|-----------:|--------------------:|-------------------------:|----------------:|
| capacity_cbba_rb    | CBBA-RB                          |     1160 |      0.789655 |          0.765265 |           0.812133 |    0.421554  | 0.389248  |  0.454045  |             26.5228 |                 9187.5   |              25 |
| weighted_grape      | GRAPE                            |     1160 |      0.996552 |          0.991167 |           0.998658 |    0.216206  | 0.200006  |  0.231304  |            121.536  |                20607.6   |             225 |
| weighted_pair_grape | Pair-GRAPE                       |     1160 |      1        |          0.996699 |           1        |    0.0965478 | 0.0870677 |  0.107195  |            293.112  |                25481.6   |             289 |
| geo_qpg_u           | Geo-QPG-BR                       |     1160 |      0.976724 |          0.966346 |           0.983955 |    0.556636  | 0.529727  |  0.586913  |              7.867  |                  662.25  |              39 |
| geo_qpg_smith       | Geo-ASR (revisión Smith atómica) |     1160 |      0.967241 |          0.955357 |           0.976041 |    0.683866  | 0.632808  |  0.749163  |              7.9755 |                  658.125 |              48 |
| geo_qpg_lll         | Geo-LLL atómico                  |     1160 |      0.981897 |          0.972483 |           0.988129 |    0.659292  | 0.623642  |  0.696406  |             30.5553 |                 6084     |             155 |
| geo_qpg_p           | Geo-QPG-2BR                      |     1160 |      0.999138 |          0.995133 |           0.999848 |    0.147735  | 0.137629  |  0.160082  |            142.585  |                 3323.62  |             281 |
| geo_qpg_c3          | Geo-QPG-C3                       |     1160 |      1        |          0.996699 |           1        |    0.0323348 | 0.0238124 |  0.0382929 |            250.483  |                14164     |             845 |
| geo_qpg_cf          | Geo-QPG-CF (global)              |     1160 |      1        |          0.996699 |           1        |    0.115636  | 0.106058  |  0.123408  |            185.159  |                 4080     |              16 |
| geo_qpg_d           | Geo-QPG-DMIS+TX                  |     1160 |      1        |          0.996699 |           1        |    0.115636  | 0.106058  |  0.12295   |            155.921  |                 5355.25  |              16 |

## Exactitud pequeña

DPOP y MILP coincidieron en factibilidad en 400/400 mundos. 
El error objetivo máximo fue 1.734e-12.

## Límites

- DMIS and TX are evaluated with reliable ordered delivery and no keeper crash.
- DPOP is exact only inside the explicit profile limit and is not a scalable candidate.
- Population dynamics use a different relaxed model and campaign; their numbers are contextual, not a direct ranking against atomic N4.
- No N4 result establishes transport, contact stability, collision avoidance or global optimality of the distributed heuristics.
