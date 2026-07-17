# Piloto AWS de cargas heterogéneas y coaliciones

Cargas: **5 kg/R1**, **14 kg/R2**, **28 kg/R3** y **18 kg/R2**. Una carga solo se mueve cuando su coalición está completa.

| Política | Entregas | Formación [s] | Espera [s] | Energía [%] | Regret |
| --- | ---: | ---: | ---: | ---: | ---: |
| MILP-Q | 3.12 | 15.71 | 15.78 | 363.74 | 0.00 |
| Greedy-Q | 3.25 | 15.30 | 15.36 | 377.01 | 0.03 |
| Random-Q | 0.50 | 7.65 | 7.67 | 119.17 | 32.11 |
| Replicator-Q | 1.38 | 14.99 | 15.22 | 200.89 | 360.38 |

## Contrastes pareados de entregas

| A − B | Diferencia | IC95 % | p Holm | Decisión |
| --- | ---: | ---: | ---: | --- |
| MILP-Q − Greedy-Q | -0.125 | [-0.500, 0.250] | 1.0000 | no concluyente |
| MILP-Q − Random-Q | 2.625 | [1.625, 3.500] | 0.0781 | no concluyente |
| MILP-Q − Replicator-Q | 1.750 | [0.625, 2.875] | 0.1875 | no concluyente |
| Greedy-Q − Random-Q | 2.750 | [2.125, 3.375] | 0.0469 | diferencia detectada |
| Greedy-Q − Replicator-Q | 1.875 | [1.000, 2.750] | 0.0781 | no concluyente |
| Random-Q − Replicator-Q | -0.875 | [-1.750, -0.125] | 0.3125 | no concluyente |

## Límite de evidencia

El MILP-Q es el oráculo central apropiado para cuotas variables; Hungarian no se usa porque no resuelve selección todo-o-nada de coaliciones.

Cada caja recibe un destino pseudoaleatorio reproducible al generarse; el destino permanece fijo durante ese ciclo de tarea y cambia entre ciclos.

La variante mantiene estanterías, barreras y obstáculo central. A* de cuatro vecinos planifica sobre huellas infladas: el interior de las rutas es discreto y ortogonal, con conectores cortos desde y hacia la pose real; no son curvas continuas. Una reserva local detiene movimientos que solaparían robots o cargas.

Cada AMR tiene un radio de sensado de **1,8 m** y un radio de comunicación de **3,2 m**. Las trazas distinguen objetos observados de vecinos comunicantes; el modelo de enlace es perfecto dentro del radio y nulo fuera de él.

La masa determina una cuota nominal mediante 10 kg por AMR, pero esto no certifica soporte, rigidez, reparto de fuerza o torque. El acoplamiento es cinemático y no demuestra factibilidad física.

MILP-Q optimiza cada instantánea de asignación, no el throughput del horizonte completo. Por ello, una diferencia descriptiva pequeña de entregas a favor de greedy no implica que greedy supere el óptimo del mismo problema estático ni que MILP sea un oráculo temporal global.

## Auditoría geométrica muestreada

En las 32 ejecuciones se registraron **0** solapamientos estáticos, **0** solapamientos dinámicos y **0** fallos reales de A*. Las esperas y rutas temporalmente no disponibles se conservan aparte como reservas y aplazamientos de planificación.

## Artefactos

- `coalition_runs.csv`: métricas por política y semilla.
- `coalition_robot_trace.csv` y `coalition_load_trace.csv`: estado completo `x,y`, batería, masa, tamaño, cuota, coalición, vecinos y objetos sensados.
- `coalition_decision_trace.csv`: composición y coste de cada coalición aceptada.
- `coalition_delivery_trace.csv`: entregas por carga y tiempos de formación.
- `coalition_replicator_trace.csv`: consenso y mensajes.
- `paired_policy_contrasts.csv`: bootstrap pareado, Wilcoxon y corrección de Holm por métrica.
- `aws_heterogeneous_coalitions_seed0.mp4`: comparación visual sincronizada.
