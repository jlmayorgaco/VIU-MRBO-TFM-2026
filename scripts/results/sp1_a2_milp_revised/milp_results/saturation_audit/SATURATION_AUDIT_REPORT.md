# SP1.A2 — auditoría de la aparente saturación temporal

## Veredicto metodológico

Una línea temporal plana al nivel del timeout no demuestra coste constante: es una observación censurada. La saturación solo sería compatible con los datos si el tiempo se estabilizara lejos del límite, manteniendo factibilidad y optimalidad certificada.

Además, el modelo explícito contiene `N*K` costes y variables. Con `K` fijo, leer y construir la instancia cuesta al menos `Omega(N)`; cuando `K` crece proporcionalmente con `N`, cuesta al menos `Omega(N^2)`. Por tanto, esta formulación no puede resolver `N -> infinito` con coste total fijo.

## Ejecución

- Casos completados: 105 de 105.
- Réplicas por celda: 3.
- Soluciones incumbent devueltas: 83 (79.0%).
- Optimalidad certificada: 19 (18.1%).
- Ejecuciones censuradas: 86 (81.9%).
- Mayor razón tiempo observado/timeout nominal: 15.40.

## Extremos de los dos brazos

| Brazo | N máximo | M | K mediana | P50 tiempo [s] | Óptimos | Censura |
|---|---:|---:|---:|---:|---:|---:|
| Demanda fija | 4800 | 120 | 40 | 16.599 | 0.0% | 100.0% |
| Crecimiento conjunto | 1800 | 1200 | 400 | 76.635 | 0.0% | 100.0% |

## Crecimiento mínimo de la representación explícita

| Brazo | Exponente de `N*K` | Exponente de memoria |
|---|---:|---:|
| Demanda fija | 1.000 | 0.999 |
| Crecimiento conjunto | 2.004 | 2.001 |

Estos exponentes describen el tamaño determinista de la representación, no una regresión de tiempo. No se ajusta una ley temporal sobre la cola porque está censurada.

## Sonda completa de timeout

| N | Timeout [s] | P50 observado [s] | Incumbent | Optimalidad | Censura |
|---:|---:|---:|---:|---:|---:|
| 400 | 2 | 2.111 | 100.0% | 0.0% | 100.0% |
| 400 | 5 | 5.064 | 100.0% | 33.3% | 66.7% |
| 400 | 20 | 11.187 | 100.0% | 66.7% | 33.3% |
| 800 | 2 | 2.145 | 100.0% | 0.0% | 100.0% |
| 800 | 5 | 5.264 | 100.0% | 0.0% | 100.0% |
| 800 | 20 | 7.554 | 100.0% | 100.0% | 0.0% |
| 1600 | 2 | 2.308 | 100.0% | 0.0% | 100.0% |
| 1600 | 5 | 5.297 | 100.0% | 0.0% | 100.0% |
| 1600 | 20 | 20.325 | 100.0% | 33.3% | 66.7% |
| 3200 | 2 | 3.928 | 0.0% | 0.0% | 100.0% |
| 3200 | 5 | 6.592 | 0.0% | 0.0% | 100.0% |
| 3200 | 20 | 21.204 | 100.0% | 0.0% | 100.0% |

Al aumentar el presupuesto de 5 a 20 s, `N=400` pasa de 33.3% a 66.7% de optimalidad certificada y `N=800` pasa de 0.0% a 100.0% de optimalidad certificada y `N=1600` pasa de 0.0% a 33.3% de optimalidad certificada. El cambio de régimen con el timeout demuestra que la meseta de 5 s no es coste fijo. En `N=3200`, el límite de 20 s eleva la tasa de incumbent de 0.0% a 100.0%, aunque la optimalidad permanece en 0.0%.

## Cómo interpretar las figuras

- `saturation_runtime_and_certification`: tiempo, optimalidad y censura deben leerse conjuntamente.
- `saturation_timeout_probe`: si la meseta se desplaza al cambiar 2/5/20 s, es una frontera impuesta por el presupuesto.
- `saturation_model_growth`: muestra que variables y memoria siguen creciendo aunque el solver parezca plano.
- `saturation_phase_costs`: separa distancias, ensamblaje, solver y tiempo total en casos con incumbente.

## Limitaciones

Esta es una auditoría piloto con tres semillas. Los tiempos dependen de hardware, carga del sistema, SciPy/HiGHS, presolve y timeout. No constituyen una prueba asintótica.
