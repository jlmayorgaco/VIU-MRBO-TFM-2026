# SP1_TFM_VALIDATION_CLOSURE_v1_1

## Resultado

La auditoría independiente del commit V1 aprobó todos los gates post-commit. El manifiesto precommit se conserva sin editar.

## Atribución semilla–recovery

| seed_method             |   before_feasibility |   after_feasibility |   distance_m |   recourse |   chains_gt2 |
|:------------------------|---------------------:|--------------------:|-------------:|-----------:|-------------:|
| Atomic-Quota-LogitSeed  |               0.1806 |              0.9722 |     1305.53  |        8   |       0      |
| Capacity-CBBASeed       |               0.125  |              0.6111 |     1291.19  |        6   |       0.2083 |
| GreedyDeficitSeed       |               0.9722 |              0.9861 |     1082.32  |        3   |       0.0139 |
| LPSeed                  |               0.8472 |              0.9167 |      829.081 |        5   |       0      |
| NearestCompatibleSeed   |               0.0417 |              0.5694 |      832.197 |       21   |       0.25   |
| QPG-LogitSeed           |               0.8333 |              0.9444 |      818.162 |        7   |       0      |
| QPG-ReplicatorSeed      |               0.8611 |              0.9306 |      856.886 |        7.5 |       0      |
| RandomSeed              |               0      |              0.4583 |     1664.57  |       18   |       0.375  |
| Weighted-GRAPESeed      |               0.0417 |              0.8333 |     1965.65  |        6   |       0      |
| Weighted-Pair-GRAPESeed |               0.2083 |              0.8194 |     1663.16  |        6   |       0      |

La pregunta causal se responde separando la factibilidad de la semilla y la ganancia posterior del mismo recovery; no se atribuye al generador una factibilidad creada por AR.

## Convergencia real

| method                  |   persistent |   transient |   censored |
|:------------------------|-------------:|------------:|-----------:|
| Atomic-Quota-Logit      |         0.35 |      0.2167 |       0.65 |
| DRD-simple-Logit        |         0    |      0      |       1    |
| DRD-simple-Replicator   |         0    |      0      |       1    |
| QPG-BNN                 |         0    |      0      |       1    |
| QPG-Damped-BestResponse |         0    |      0      |       1    |
| QPG-Logit               |         0    |      0      |       1    |
| QPG-Projection          |         0    |      0      |       1    |
| QPG-Replicator          |         1    |      0      |       0    |
| QPG-Smith               |         0    |      0      |       1    |

Los tiempos censurados son tiempos terminales presupuestados, no tiempos de convergencia. Recovery no participa en A3.

## Bernstein

Se evaluaron 400 estados y 200000 redondeos. La fracción de violaciones empíricas fue 0.0000; las bandas cubren deliberadamente cotas no vacuas y vacuas.

## Gap homogéneo

Filas comparables: 2506/2506. Los tres componentes se expresan en metros y se normalizan por `J_ref`; el delta firmado se mantiene separado.

## Dinámica y localidad

| recovery_variant   |   post_event_feasible |   recourse |   unaffected_coalition_integrity |   locality_respected |
|:-------------------|----------------------:|-----------:|---------------------------------:|---------------------:|
| global             |                     1 |          0 |                                1 |                    1 |
| local              |                     1 |          0 |                                1 |                    1 |
| local_recourse     |                     1 |          0 |                                1 |                    1 |

## Limitaciones

- A3 prueba convergencia operacional bajo 12.000 rondas/240 s; no demuestra convergencia global.
- La recuperación local es incompleta fuera de su universo residual.
- A5 regenera cada mundo desde la configuración V1 congelada; una discrepancia de hash invalida la campaña.
- La mensajería es payload lógico, no tráfico de middleware.

Runtime de cierre: 227.196 s.
