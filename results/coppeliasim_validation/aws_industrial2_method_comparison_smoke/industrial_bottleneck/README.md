# Piloto AWS de cargas heterogéneas y coaliciones

Cargas: **5 kg/R1**, **14 kg/R2**, **28 kg/R3** y **18 kg/R2**. Una carga solo se mueve cuando su coalición está completa.

| Política | Entregas | Formación [s] | Espera [s] | Energía [%] | Regret |
| --- | ---: | ---: | ---: | ---: | ---: |
| Central MILP + preview | 0.00 | 10.45 | 10.45 | 47.79 | 0.00 |
| Auction + reciprocal proxy | 0.00 | 5.17 | 5.17 | 62.62 | 13.97 |
| Auction + predictive CBF proxy | 0.00 | 5.78 | 5.78 | 61.46 | 13.97 |
| Replicator + CBF (TFM) | 0.00 | 0.00 | 0.00 | 43.06 | 1005.27 |

## Contrastes pareados de entregas

| A − B | Diferencia | IC95 % | p Holm | Decisión |
| --- | ---: | ---: | ---: | --- |
| Central MILP + preview − Auction + reciprocal proxy | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |
| Central MILP + preview − Auction + predictive CBF proxy | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |
| Central MILP + preview − Replicator + CBF (TFM) | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |
| Auction + reciprocal proxy − Auction + predictive CBF proxy | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |
| Auction + reciprocal proxy − Replicator + CBF (TFM) | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |
| Auction + predictive CBF proxy − Replicator + CBF (TFM) | 0.000 | [0.000, 0.000] | 1.0000 | no concluyente |

## Límite de evidencia

El MILP-Q es el oráculo central apropiado para cuotas variables; Hungarian no se usa porque no resuelve selección todo-o-nada de coaliciones.

Cada caja recibe un destino pseudoaleatorio reproducible al generarse; el destino permanece fijo durante ese ciclo de tarea y cambia entre ciclos.

La variante mantiene estanterías, barreras y obstáculo central. El método propuesto usa un campo de objetivo continuo, un juego Replicator local sobre primitivas izquierda/derecha/espera y proyección cíclica CBF; Euler lo ejecuta con el paso declarado. A* queda fuera de esta variante y se conserva como baseline independiente.

Cada AMR tiene un radio de sensado de **1,8 m** y un radio de comunicación de **3,2 m**. Las trazas distinguen objetos observados de vecinos comunicantes; el modelo de enlace es perfecto dentro del radio y nulo fuera de él.

La masa determina una cuota nominal mediante 10 kg por AMR, pero esto no certifica soporte, rigidez, reparto de fuerza o torque. El acoplamiento es cinemático y no demuestra factibilidad física.

MILP-Q optimiza cada instantánea de asignación, no el throughput del horizonte completo. Por ello, una diferencia descriptiva pequeña de entregas a favor de greedy no implica que greedy supere el óptimo del mismo problema estático ni que MILP sea un oráculo temporal global.

## Auditoría geométrica muestreada

En las 4 ejecuciones se registraron **0** solapamientos estáticos, **0** solapamientos dinámicos y **0** fallos reales de A*. Las esperas y rutas temporalmente no disponibles se conservan aparte como reservas y aplazamientos de planificación.
La variante continua registró **0** intervenciones del guard de último recurso y un residual EXEC máximo de **7.104e-02**. RAW, SAFE y EXEC se conservan por separado; estos datos muestreados no constituyen una prueba de invariancia continua.

## Artefactos

- `coalition_runs.csv`: métricas por política y semilla.
- `coalition_robot_trace.csv` y `coalition_load_trace.csv`: estado completo `x,y`, batería, masa, tamaño, cuota, coalición, vecinos y objetos sensados.
- `coalition_decision_trace.csv`: composición y coste de cada coalición aceptada.
- `coalition_delivery_trace.csv`: entregas por carga y tiempos de formación.
- `coalition_replicator_trace.csv`: consenso y mensajes.
- `coalition_motion_trace.csv`: preferencias de primitivas y velocidades RAW--SAFE--EXEC del controlador continuo.
- `paired_policy_contrasts.csv`: bootstrap pareado, Wilcoxon y corrección de Holm por métrica.
- `aws_heterogeneous_coalitions_seed0.mp4`: comparación visual sincronizada.
