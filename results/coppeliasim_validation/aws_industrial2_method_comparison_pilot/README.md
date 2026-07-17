# AWS Industrial 2 — comparación multiescenario

Campaña piloto pareada. Dos semillas permiten depurar integración y medir señales; no permiten declarar un ganador.

| Escenario | Método | Entregas | Deadlock | Energía [%] | CPU [s] |
| --- | --- | ---: | ---: | ---: | ---: |
| open_center | Central MILP + preview | 0.00 | 0.317 | 79.19 | 70.41 |
| open_center | Auction + reciprocal proxy | 1.00 | 0.114 | 125.62 | 13.26 |
| open_center | Auction + predictive CBF proxy | 1.00 | 0.008 | 144.32 | 13.63 |
| open_center | Replicator + CBF (TFM) | 1.00 | 0.467 | 85.52 | 6.49 |
| industrial_bottleneck | Central MILP + preview | 0.00 | 0.317 | 78.12 | 80.80 |
| industrial_bottleneck | Auction + reciprocal proxy | 0.00 | 0.011 | 108.87 | 14.69 |
| industrial_bottleneck | Auction + predictive CBF proxy | 0.00 | 0.010 | 137.75 | 16.27 |
| industrial_bottleneck | Replicator + CBF (TFM) | 0.00 | 0.633 | 52.31 | 7.80 |
| controlled_cross_traffic | Central MILP + preview | 0.00 | 0.316 | 81.09 | 83.01 |
| controlled_cross_traffic | Auction + reciprocal proxy | 0.00 | 0.021 | 118.92 | 16.97 |
| controlled_cross_traffic | Auction + predictive CBF proxy | 0.00 | 0.009 | 139.78 | 15.84 |
| controlled_cross_traffic | Replicator + CBF (TFM) | 0.00 | 0.646 | 51.17 | 7.45 |
| backlog_and_low_battery | Central MILP + preview | 0.00 | 0.317 | 78.12 | 67.62 |
| backlog_and_low_battery | Auction + reciprocal proxy | 0.00 | 0.011 | 108.87 | 12.98 |
| backlog_and_low_battery | Auction + predictive CBF proxy | 0.00 | 0.010 | 137.75 | 15.07 |
| backlog_and_low_battery | Replicator + CBF (TFM) | 0.00 | 0.611 | 60.52 | 6.69 |

## Interpretación permitida

El método central tiene información global y funciona como referencia superior de arquitectura, no como comparación justa de información. La subasta y los dos controles predictivos conservan `proxy` en su nombre porque no reproducen CBBA, ORCA o DMPC completos. Replicator–CBF es el método TFM muestreado.

Deadlock es la fracción de muestras activas con velocidad ejecutada menor de 0,02 m/s a más de 0,25 m del objetivo. Es un indicador operacional, no una prueba formal de ausencia de vivacidad.

Los actores de tráfico siguen rutas deterministas y aplican una parada de seguridad muestreada antes de invadir una huella ocupada. Las colisiones y CBF se auditan en muestras de 0,05 s; la manipulación de carga sigue siendo cinemática.
