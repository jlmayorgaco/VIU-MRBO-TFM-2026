# 02 — Matriz de investigación SP0–SP8

## 1. Bloques de la tesis

- **Bloque A — Formación de coaliciones:** SP0, SP1 y SP2.
- **Bloque B — Manipulación y transporte:** SP3 y SP4.
- **Bloque C — Seguridad y resiliencia:** SP5, SP6 y SP7.
- **Bloque D — Escalabilidad y red:** SP8.

La formulación general se presenta una sola vez. Cada SP añade restricciones o perturbaciones sobre el anterior.

## 2. Niveles de evidencia

- **Nivel A:** resultado formal completo + validación numérica.
- **Nivel B:** proposición/argumento formal parcial + validación extensa.
- **Nivel C:** evaluación experimental y análisis de sensibilidad; sin garantía general.

## 3. Matriz

| SP | Pregunta local | Cambio incremental | Método propuesto | Baseline principal candidato | Evidencia objetivo | Prioridad |
|---|---|---|---|---|---|---|
| SP0 | ¿El mecanismo reproduce factibilidad en la asignación homogénea uno-a-uno y qué calidad tiene frente al óptimo clásico? | Caso de referencia: robots intercambiables, cargas unitarias, una carga por robot y costes aditivos de distancia | Juego potencial de cobertura/exclusión y refinamiento por 2-intercambio | Hungarian como oráculo; auction, greedy, PBR y PBR-2 como referencias ejecutadas | A — alcanzada como calibración formal y numérica; red y escalabilidad se reservan para SP8 | Obligatorio |
| SP1 | ¿Se forman coaliciones de tamaños variables? | Requisito de cardinalidad distinto por carga | Payoff con déficit de coalición y penalización de sobreasignación | MILP de asignación con slots/cardinalidad; CBBA/auction distribuida verificable | A o B | Obligatorio |
| SP2 | ¿Se cubre un umbral operacional cuando la contribución depende del par robot--carga? | Índice adimensional de servicio: carga útil normalizada ponderada por disponibilidad de batería y distancia; compatibilidad universal en la campaña | Puntuación de déficit ponderada por contribución marginal; comparación separada de cobertura y completitud | MILP de puntuación y MILP de cobertura normalizada; voraz, aproximación CBBA y reglas de puntuación supervisadas | B parcial: proposición de alineación con $E$ fija + ablación extensa; estimación vecinal y factibilidad mecánica aún pendientes | Obligatorio |
| SP3 | ¿La coalición es físicamente ejecutable bajo la modalidad seleccionada? | `SP3-C`: soporte, rigidez y wrench. `SP3-E`: contacto unilateral y confinamiento de empuje/caging | Cargo: potencial de formación rígida + reparto de wrench. Empuje/caging: selección de contactos, condición de caging cuando proceda y regulación local de empuje | Cargo: QP de fuerzas y estructura virtual. Empuje: planificador/control central de empuje y referencias de caging | B para C; C para E | Cargo obligatorio; E secundaria |
| SP4 | ¿La carga llega a la pose objetivo bajo cada interfaz física? | `SP4-C`: docking dinámico y trayectoria del cuerpo compuesto. `SP4-E`: trayectorias de empuje cerradas con pose estimada de la caja | Cargo: juego de vivacidad distribuido + HOCBF para docking y servocontrol de pose mediante proyección acotada de wrench. Empuje/caging: extensión aún no ejecutada | Cargo: directo/CBF, planificador central+HOCBF, PD de pose y preview central. Empuje: planificación central de contactos/empujes y caging distribuido | B alcanzada para las garantías locales; la simulación Cargo compone uniciclos durante aproximación/reemplazo y una planta reducida de carga durante transporte, sin tracción rueda--suelo; E pendiente | Cargo obligatorio; E secundaria |
| SP5 | ¿Se mantiene seguridad con obstáculos sin perder la interfaz física? | `SP5-C`: huella rígida y soporte. `SP5-E`: caja y empujadores con contacto/confinamiento | Cargo: proyección cíclica de restricciones tipo CBF, separación RAW--SAFE--EXEC y reparto acotado de wrench. Empuje/caging: pendiente | Campo potencial y proxy VO ejecutados; CBF-QP/ORCA como referencias conceptuales; preview central con ventaja informativa | C alcanzada para C; E pendiente | Extensión prioritaria |
| SP6 | ¿Se recupera una tarea cuando falla un robot? | `SP6-C`: pérdida de soporte; fallo simple y una carga afectada. `SP6-E`: pérdida de empujador/contacto o apertura del caging | Juego potencial binario con utilidad marginal, umbral de factibilidad y re-reclutamiento asíncrono sujeto a un certificado aditivo de soporte/fuerza/torque | Oráculo exhaustivo central, subasta marginal, greedy por distancia y ablación sin reparación | B alcanzada para la reparación estratégica; la simulación integrada reemplaza el robot y reanuda 89/90 misiones con fallo, sin simular un nuevo contacto físico ni convertirlo en garantía universal; E pendiente | Cargo obligatorio; E secundaria |
| SP7 | ¿Se evitan conflictos entre varias coaliciones? | Tráfico multiagente y cargas con huella ampliada sobre un grafo de configuraciones inflado | Juego potencial finito de rutas + reserva vecinal de zona con prioridad y envejecimiento | Oráculo exhaustivo restringido y planificación priorizada ejecutados; CBS/ECBS, LA-MAPF y ORCA como contexto no reproducido | C alcanzada: potencial exacto, condición suficiente de Nash sin conflictos, invariante lógico de exclusión y 360 mundos/1.800 ejecuciones; seguridad continua y completitud MAPF pendientes | Condicionado ejecutado como exploración |
| SP8 | ¿Cómo escala y degrada la red? | Juego de rutas SP7 bajo (N=2K), radio, retardo muestreado y pérdida independiente | Juego de potencial visible + retransmisión periódica versionada | Oráculo exhaustivo restringido, mejor respuesta con información perfecta, mensajería solo por evento y perfil aleatorio ejecutados; consenso/gossip/ACBBA como contexto | C alcanzada: equilibrio visible e imposibilidad de garantizar optimalidad/detección de acoplamientos remotos no observables; 900 mundos, 4.050 ejecuciones efectivas hasta 128 robots y 450 registros del oráculo no ejecutados fuera del dominio certificado, con inferencia agrupada en 180 instancias; energía, radio real, red conmutada y planta continua pendientes | Obligatorio ejecutado |

## 4. Dependencias

```text
SP0 -> SP1 -> SP2 -> SP3-C -> SP4-C
                    |           |
                    |           +-> SP5-C -> SP7
                    +--------------> SP6-C
                    |
                    +-> SP3-E -> SP4-E -> SP5-E
                                    +----> SP6-E
SP0..SP7 ----------------------> SP8
```

No implementar SP7 antes de disponer de un SP4 estable y métricas verificadas. SP8 debe ejecutarse progresivamente desde SP0, no solo al final.

## 5. Capítulos dentro de Resultados y análisis

### 6.1 Formulación general y arquitectura

- conjuntos y grafos;
- modelos de robot, carga y comunicación;
- variables estratégicas y físicas;
- función objetivo social de referencia;
- arquitectura distribuida propuesta.

### 6.2 Protocolo, baselines y reproducibilidad

- escenarios comunes;
- métricas;
- oráculo central;
- baselines distribuidos;
- diseño estadístico.

### 6.3 Bloque A — SP0–SP2

Asignación, cardinalidad y heterogeneidad. Aquí debe concentrarse la aportación teórica principal.

### 6.4 Bloque B — SP3–SP4

Factibilidad mecánica y transporte de pose mediante dos subramas. Cargo (`C`) es el modo primario: caja soportada, formación rígida y wrench. Empuje/caging (`E`) es la extensión secundaria: contacto unilateral, trayectorias de empuje y realimentación local de pose. Las ramas comparten asignación estratégica, pero no modelo de contacto ni prueba de estabilidad.

### 6.5 Bloque C — SP5–SP7

Seguridad, recuperación y tráfico, con profundidad acorde al nivel de evidencia.

### 6.6 Bloque D — SP8

Curvas de escala, gap de optimalidad en tamaños pequeños, comunicación, fallos de red y coste computacional.

### 6.7 Discusión transversal

- respuesta a RQ1–RQ5;
- comparación entre garantías y resultados;
- regiones de fallo;
- amenazas a la validez;
- límites de generalización.
