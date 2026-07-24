# Preview — SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1_preview

## Alcance y lectura correcta

La campaña evalúa exclusivamente reclutamiento SP1. Las posiciones solo parametrizan coste de llegada; no se simulan docking, contacto, wrench, transporte, MPC ni tráfico. `rho` es intención continua y `x` es la asignación atómica, conforme a la notación canónica del repositorio.

Los resultados `raw`, `seeded` y `recovered` se conservan por separado. El LP es una cota/referencia fraccionaria, nunca una ejecución física. Capacity-CBBA y Weighted-GRAPE son adaptaciones declaradas. GRAPE-S aparece solo en E10, su dominio discreto de servicios.

## Resultado descriptivo agregado

| method                |   runs |   feasibility |   distance_median_m |   excess_median |   time_median_s |    bytes_median |
|:----------------------|-------:|--------------:|--------------------:|----------------:|----------------:|----------------:|
| QPG-Replicator-AR     |     15 |      1        |             811.148 |         6.23724 |        0.214009 |     6.67648e+06 |
| QPG-Logit-AR          |     15 |      1        |             814.145 |         4.73461 |        0.197599 |     6.67648e+06 |
| Atomic-Quota-Logit    |     15 |      1        |             989.643 |         4.20664 |        5.03408  | 53824           |
| Capacity-CBBA         |     15 |      1        |            1307.61  |         5.40155 |        0.886444 | 40544           |
| Weighted-GRAPE        |     15 |      1        |            1401.6   |         4.1618  |        0.172501 | 99960           |
| DRD-simple-Logit      |     15 |      1        |            1895.45  |         5.85689 |        0.254385 |     5.632e+06   |
| DRD-simple-Replicator |     15 |      0.933333 |            1920.44  |         5.26969 |        0.255088 |     5.632e+06   |

## Servicios discretos E10

No aplica al preview.

## Certificados

Se verificaron 30 certificados válidos de 30 diagnósticos aplicables.

## Censura y límites

El guard de rondas es censura computacional explícita y nunca se interpreta como convergencia. Las simulaciones no demuestran estabilidad global, optimalidad distribuida, transporte físico ni tasa asintótica.

## Ejecución

- Tasks completadas: 15/15.
- Workers: 6.
- Wall time primario del driver: 310.763 s.
- CPU algorítmica acumulada sin triplicar cierres: 877.578 s.
- Figuras PNG/PDF: 7.

## Conclusión científica

La interpretación final se basa en el mapa de regímenes y en pruebas emparejadas; no se presupone un ganador. Cuando QPG no satisface un gate, se registra como resultado negativo. La contribución defendible es el pipeline trazable continuo→semilla→recovery con precios comunes por mercado local y certificados computables, no una afirmación de optimalidad entera distribuida general.
