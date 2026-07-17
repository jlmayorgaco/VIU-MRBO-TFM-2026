# AWS Industrial 2 — comparación multiescenario

Campaña piloto pareada. Dos semillas permiten depurar integración y medir señales; no permiten declarar un ganador.

| Escenario | Método | Entregas | Deadlock | Energía [%] | CPU [s] |
| --- | --- | ---: | ---: | ---: | ---: |
| open_center | Central MILP + preview | 0.00 | 0.103 | 47.79 | 16.29 |
| open_center | Auction + reciprocal proxy | 0.00 | 0.000 | 64.00 | 3.28 |
| open_center | Auction + predictive CBF proxy | 0.00 | 0.000 | 61.46 | 4.04 |
| open_center | Replicator + CBF (TFM) | 0.00 | 0.117 | 44.59 | 1.51 |
| industrial_bottleneck | Central MILP + preview | 0.00 | 0.103 | 47.79 | 18.56 |
| industrial_bottleneck | Auction + reciprocal proxy | 0.00 | 0.000 | 62.62 | 3.10 |
| industrial_bottleneck | Auction + predictive CBF proxy | 0.00 | 0.000 | 61.46 | 3.87 |
| industrial_bottleneck | Replicator + CBF (TFM) | 0.00 | 0.117 | 43.06 | 1.74 |
| controlled_cross_traffic | Central MILP + preview | 0.00 | 0.103 | 48.29 | 19.19 |
| controlled_cross_traffic | Auction + reciprocal proxy | 0.00 | 0.000 | 62.28 | 3.33 |
| controlled_cross_traffic | Auction + predictive CBF proxy | 0.00 | 0.000 | 61.21 | 4.39 |
| controlled_cross_traffic | Replicator + CBF (TFM) | 0.00 | 0.117 | 43.07 | 2.09 |
| backlog_and_low_battery | Central MILP + preview | 0.00 | 0.103 | 47.79 | 17.79 |
| backlog_and_low_battery | Auction + reciprocal proxy | 0.00 | 0.000 | 62.62 | 3.26 |
| backlog_and_low_battery | Auction + predictive CBF proxy | 0.00 | 0.000 | 61.46 | 4.20 |
| backlog_and_low_battery | Replicator + CBF (TFM) | 0.00 | 0.080 | 50.79 | 1.73 |

## Interpretación permitida

El método central tiene información global y funciona como referencia superior de arquitectura, no como comparación justa de información. La subasta y los dos controles predictivos conservan `proxy` en su nombre porque no reproducen CBBA, ORCA o DMPC completos. Replicator–CBF es el método TFM muestreado.

Deadlock es la fracción de muestras activas con velocidad ejecutada menor de 0,02 m/s a más de 0,25 m del objetivo. Es un indicador operacional, no una prueba formal de ausencia de vivacidad.

Los actores de tráfico siguen rutas deterministas y no reaccionan. Las colisiones y CBF se auditan en muestras de 0,05 s; la manipulación de carga sigue siendo cinemática.
