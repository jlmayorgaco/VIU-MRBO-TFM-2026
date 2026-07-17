# Piloto dinámico AWS: Hungarian, greedy, random y replicator

Este artefacto compara asignación **uno-a-uno** en periodos digitales de 0.50 s. Cada carga conserva su destino propio durante toda la simulación.

| Política | Entregas | Espera [s] | Energía [%] | Distancia [m] | Regret |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hungarian | 10.00 | 6.90 | 328.11 | 378.21 | 0.00 |
| Greedy | 10.00 | 6.89 | 327.95 | 378.32 | 0.00 |
| Random factible | 8.00 | 12.87 | 314.50 | 374.26 | 0.54 |
| Replicator + consenso | 9.75 | 7.55 | 329.05 | 381.15 | 1.71 |

## Alcance de evidencia

El algoritmo húngaro es exacto aquí porque el piloto reduce cada carga activa a una tarea indivisible servida por un AMR. No es el oráculo exacto del problema posterior de coaliciones de 2--3 AMR; ese caso exige MILP/set partitioning con capacidades y restricciones mecánicas.

El movimiento es cinemático y la animación no demuestra planificación libre de colisiones, estabilidad, wrench factible ni percepción/comunicación realista.

Replicator intercambia estimaciones solo dentro del radio configurado. El consenso es por componente y el cierre entero se modela como aceptación local de una propuesta por carga; no se presupone un coordinador global. En la campaña, el grafo tuvo 3,42 componentes de media; el error medio bajó de 0,02455 a 0,000906 dentro de los componentes, con 7.612,5 escalares transmitidos por ejecución.

## Archivos

- `aws_assignment_runs.csv`: métricas por política y semilla pareada.
- `aws_robot_state_trace.csv`: `x`, `y`, batería, estado y carga asignada de cada AMR.
- `aws_load_state_trace.csv`: `x`, `y`, estado, portador y destino fijo de cada carga.
- `aws_decision_trace.csv`: pares seleccionados, coste y coordenadas en cada decisión.
- `aws_objective_trace.csv`: J(t), óptimo húngaro y regret.
- `aws_replicator_consensus_trace.csv`: componentes, aristas, desacuerdo y mensajes de la dinámica replicadora.
- `aws_assignment_comparison_seed0.mp4`: animación sincronizada de las cuatro políticas.
