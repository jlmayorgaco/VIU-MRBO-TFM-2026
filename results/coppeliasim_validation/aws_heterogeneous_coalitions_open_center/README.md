# Piloto AWS de cargas heterogéneas y coaliciones

Cargas: **5 kg/R1**, **14 kg/R2**, **28 kg/R3** y **18 kg/R2**. Una carga solo se mueve cuando su coalición está completa.

| Política | Entregas | Formación [s] | Espera [s] | Energía [%] | Regret |
| --- | ---: | ---: | ---: | ---: | ---: |
| MILP-Q | 0.75 | 11.64 | 11.65 | 220.40 | 0.00 |
| Greedy-Q | 1.25 | 11.78 | 11.81 | 253.89 | 0.07 |
| Random-Q | 0.88 | 9.76 | 9.80 | 138.05 | 31.25 |
| Replicator-Q | 1.38 | 12.93 | 13.14 | 158.77 | 344.83 |

## Contrastes pareados de entregas

| A − B | Diferencia | IC95 % | p Holm | Decisión |
| --- | ---: | ---: | ---: | --- |
| MILP-Q − Greedy-Q | -0.500 | [-1.375, 0.250] | 1.0000 | no concluyente |
| MILP-Q − Random-Q | -0.125 | [-1.000, 0.625] | 1.0000 | no concluyente |
| MILP-Q − Replicator-Q | -0.625 | [-1.625, 0.375] | 1.0000 | no concluyente |
| Greedy-Q − Random-Q | 0.375 | [-0.375, 1.125] | 1.0000 | no concluyente |
| Greedy-Q − Replicator-Q | -0.125 | [-1.125, 0.750] | 1.0000 | no concluyente |
| Random-Q − Replicator-Q | -0.500 | [-1.500, 0.375] | 1.0000 | no concluyente |

## Límite de evidencia

El MILP-Q es el oráculo central apropiado para cuotas variables; Hungarian no se usa porque no resuelve selección todo-o-nada de coaliciones.

Cada caja recibe un destino pseudoaleatorio reproducible al generarse; el destino permanece fijo durante ese ciclo de tarea y cambia entre ciclos.

La variante mantiene las estanterías pero retira el puesto y las barreras centrales. A* de cuatro vecinos planifica sobre huellas infladas: el interior de las rutas es discreto y ortogonal, con conectores cortos desde y hacia la pose real; no son curvas continuas. Una reserva local detiene movimientos que solaparían robots o cargas.

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
