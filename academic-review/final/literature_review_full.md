# Revisión de literatura: coordinación distribuida de múltiples AMR

Generada UTC: 2026-09-12T22:31:57.457080+00:00

## Resumen ejecutivo

Esta revisión organiza evidencia bibliográfica para el TFM sobre coordinación
distribuida local de múltiples AMR, formación de coaliciones, transporte
cooperativo de cargas heterogéneas y planificación/tráfico. El derivado Stage
1C contiene **2226** candidatos; la cola de texto completo contiene
**1057** registros.
Stage 2 verificó **230** objetos de texto completo
por identidad; **30** quedaron limitados al
resumen, **776** solo tienen metadatos y
**21** presentan error operativo de recuperación.

El resultado es una síntesis de revisión reproducible y una base de lectura.
No es un meta-análisis: los trabajos modelan problemas, plataformas, métricas
y niveles de evidencia heterogéneos. Tampoco establece por sí sola novedad,
optimalidad, convergencia, estabilidad, robustez o escalabilidad del TFM.

## Alcance y protocolo

La búsqueda combinó descubrimiento abierto en Crossref y OpenAlex, screening
de título/resumen, una ronda acotada de snowballing y una ronda única de
reparación con ocho familias dirigidas. Las familias de reparación cubrieron
juegos poblacionales/evolutivos/potenciales, seguridad y CBF, contexto
industrial, formación/docking, coordinación multi-agent, transporte colectivo,
fuerza/wrench y AMR/AGV logístico. La exportación de Web of Science continúa
pendiente, por lo que no se declara exhaustividad.

Stage 2 usó exclusivamente rutas públicas legales/open observadas en metadatos
o enlaces públicos de Crossref. No se usaron credenciales, proxy institucional,
bypass de paywall ni alteraciones de restricciones de acceso. Los binarios
locales se conservan fuera de Git por tamaño y condiciones de redistribución;
los manifests, URLs, hashes y estados sí quedan trazados.

## Arquitectura de evidencia

La matriz Stage 3 es un primer coding estructural de los textos extraídos. Las
señales observadas se guardan con snippets y páginas/secciones cuando existen,
pero requieren confirmación humana de lectura cercana antes de sustentar una
afirmación fuerte.

| Nivel | Registros |
|---|---:|
| Texto completo verificado | 230 |
| Solo resumen | 30 |
| Solo metadatos | 776 |
| Error de recuperación | 21 |

Roles preliminares: `BASELINE`=19, `CONTEXT`=800, `CORE`=94, `ENABLING`=123, `SURVEY`=21.
Son etiquetas de triage, no jerarquías de calidad ni de citación.

## Hallazgos organizados por SP

### SP1 — formación distribuida de coaliciones

El corpus de la cola contiene 490 registros
con señal de asignación/coalición y 100
con texto completo verificado. Los términos de coding más observados en textos
verificados para coordinación/arquitectura son: `distributed` (215), `decentralized` (148), `multi-agent` (146), `consensus` (91), `auction` (49), `decentralised` (35), `centralized` (35), `market-based` (20).
Esto identifica familias que deben leerse y compararse; no demuestra que una
dinámica de juego concreta sea nueva ni que un equilibrio sea factible.

### SP2 — ejecución y transporte cooperativo

Las etiquetas iniciales identifican 73
registros con señales físicas de transporte/contacto y 19
con texto completo verificado. En el texto completo aparecen: `object` (109), `load` (82), `payload` (35), `manipulation` (31), `pushing` (19), `caging` (11), `grasp` (10), `rigid body` (9).
La lectura del TFM debe distinguir transporte rígido/prehensil de empuje o
caging, y no transferir garantías entre modelos de contacto distintos.

### SP3 — planificación, tráfico y múltiples coaliciones

Se observan 78 señales de planificación,
seguridad o contexto industrial y 22
textos completos verificados. Los términos de ejecución más frecuentes son:
`navigation` (151), `formation` (106), `path planning` (104), `trajectory` (84), `motion planning` (63), `fault` (35), `synchronization` (31), `failure` (28).
El acoplamiento entre tráfico de varias coaliciones activas y transporte físico
debe considerarse una hipótesis de integración, no una ausencia de estado del
arte inferida por conteo de palabras.

## Familias de método y validación

Las familias observadas en textos completos incluyen: `auction` (105), `reinforcement learning` (65), `consensus-based` (52), `formation control` (40), `genetic algorithm` (35), `fuzzy` (35), `integer programming` (24), `milp` (24).
Los términos experimentales incluyen: `simulation` (168), `experimental` (128), `simulated` (90), `experiment` (76), `hardware` (46), `benchmark` (20), `warehouse` (18), `ros` (15).
La presencia de `theorem`, `convergence`, `stability` o `complexity` solo indica
que el vocabulario aparece; la afirmación matemática requiere leer supuestos,
prueba, dominio y conjunto invariante. Del mismo modo, una palabra como
`performance` no autoriza a copiar una mejora numérica sin extraer tabla,
baseline, semillas, intervalo y protocolo.

## Auditoría adversarial de novedad

La auditoría Stage 4 conserva explícitamente prior art candidato y niega una
conclusión final de novedad. La revisión no identifica base suficiente para
afirmar que el TFM sea el primero en combinar SP1-SP3. La integración de un
juego potencial/poblacional white-box, ejecución física de transporte rígido
con reparto de wrench y planificación de tráfico local aparece aquí como
**hipótesis de posicionamiento a contrastar**, no como contribución ya
demostrada.

### Candidatos prioritarios para lectura cercana


1. 1P2-S-030 Designing An Algorithm for Testing Object Caging Condition by Multiple Mobile Robots(Cooperation Control of Multi Robot,Mega-Integration in Robotics and Mechatronics to Assist Our Daily Lives) (2005; [DOI](https://doi.org/10.1299/jsmermd.2005.124_4)) — rol `CORE`, evidencia `fulltext_verified`.
2. 3D camera augmented Autonomous Mobile Robot for intralogistics
						purposes (2023; [DOI](https://doi.org/10.14232/analecta.2023.1.10-15)) — rol `ENABLING`, evidencia `fulltext_verified`.
3. A Centralized Task Allocation Algorithm for a Multi-Robot Inspection Mission With Sensing Specifications (2023; [DOI](https://doi.org/10.1109/access.2023.3315130)) — rol `CORE`, evidencia `fulltext_verified`.
4. A Comparative Study of Task Assignment and Path Planning Methods for Multi-UGV Missions (2008; [DOI](https://doi.org/10.1007/978-3-540-88063-9_10)) — rol `ENABLING`, evidencia `fulltext_verified`.
5. A Digital Twin Approach for the Improvement of an Autonomous Mobile Robots (AMR’s) Operating Environment—A Case Study (2021; [DOI](https://doi.org/10.3390/s21237830)) — rol `ENABLING`, evidencia `fulltext_verified`.
6. A Distributed Approach to the Multi-Robot Task Allocation Problem Using the Consensus-Based Bundle Algorithm and Ant Colony System (2020; [DOI](https://doi.org/10.1109/access.2020.2971585)) — rol `CORE`, evidencia `fulltext_verified`.
7. A Distributed Solution to the Multi-robot Task Allocation Problem Using Ant Colony Optimization and Bat Algorithm (2020; [DOI](https://doi.org/10.1007/978-981-15-5243-4_44)) — rol `CORE`, evidencia `fulltext_verified`.
8. A Distributed Task Allocation Algorithm for a Multi-Robot System in Healthcare Facilities (2014; [DOI](https://doi.org/10.1007/s10846-014-0154-2)) — rol `CORE`, evidencia `fulltext_verified`.
9. A Faithful Mechanism for Incremental Multi-Agent Agreement Problems with Self-Interested and Privacy-Preserving Agents (2021; [DOI](https://doi.org/10.1007/s42979-021-00650-4)) — rol `ENABLING`, evidencia `fulltext_verified`.
10. A Multi-Agent Reinforcement Learning-Based Data-Driven Method for Home Energy Management (2020; [DOI](https://doi.org/10.1109/tsg.2020.2971427)) — rol `ENABLING`, evidencia `fulltext_verified`.
11. A Multi-Robots Task Allocation Algorithm Based on Relevance and Ability With Group Collaboration (2010; [DOI](https://doi.org/10.22266/ijies2010.0630.05)) — rol `CORE`, evidencia `fulltext_verified`.
12. A Novel Hybrid Auction Algorithm for Multi-UAVs Dynamic Task Assignment (2019; [DOI](https://doi.org/10.1109/access.2019.2959327)) — rol `ENABLING`, evidencia `fulltext_verified`.
13. A Secure Decentralized Event-Triggered Cooperative Localization in Multi-Robot Systems Under Cyber Attack (2022; [DOI](https://doi.org/10.1109/access.2022.3227076)) — rol `ENABLING`, evidencia `fulltext_verified`.
14. A Stochastic Clustering Auction (SCA) for Centralized and Distributed Task Allocation in Multi-agent Teams (2009; [DOI](https://doi.org/10.1007/978-3-642-00644-9_31)) — rol `CORE`, evidencia `fulltext_verified`.
15. A Two-Level Clustered Consensus-Based Bundle Algorithm for Dynamic Heterogeneous Multi-UAV Multi-Task Allocation (2025; [DOI](https://doi.org/10.3390/s25216738)) — rol `ENABLING`, evidencia `fulltext_verified`.
16. A decentralized multi-agent unmanned aerial system to search, pick up, and relocate objects (2017; [DOI](https://doi.org/10.1109/ssrr.2017.8088150)) — rol `ENABLING`, evidencia `fulltext_verified`.
17. A distributed PI-based dynamic task allocation method for multi-AUV systems (2026; [DOI](https://doi.org/10.1007/s00500-025-10894-4)) — rol `CORE`, evidencia `fulltext_verified`.
18. A kinematically compatible framework for cooperative payload transport by nonholonomic mobile manipulators (2006; [DOI](https://doi.org/10.1007/s10514-005-9717-9)) — rol `CORE`, evidencia `fulltext_verified`.
19. A novel approach to task assignment in a cooperative multi-agent design system (2015; [DOI](https://doi.org/10.1007/s10489-014-0640-z)) — rol `ENABLING`, evidencia `fulltext_verified`.
20. A novel marine predator algorithm for robot task allocation problem (2026; [DOI](https://doi.org/10.1017/s0263574726103531)) — rol `CORE`, evidencia `fulltext_verified`.
21. A semantically-informed multirobot system for exploration of relevant areas in search and rescue settings (2015; [DOI](https://doi.org/10.1007/s10514-015-9480-x)) — rol `ENABLING`, evidencia `fulltext_verified`.
22. A taxonomy for multi-agent robotics (1996; [DOI](https://doi.org/10.1007/bf00240651)) — rol `ENABLING`, evidencia `fulltext_verified`.
23. Adaptable and stable decentralized task allocation for hierarchical domains (2020; [DOI](https://doi.org/10.1017/s0269888920000235)) — rol `CORE`, evidencia `fulltext_verified`.
24. Affection Based Multi-robot Team Work (2008; [DOI](https://doi.org/10.1007/978-3-540-69033-7_17)) — rol `CORE`, evidencia `fulltext_verified`.

## Recomendaciones de uso en el TFM

1. Usar las entradas CORE/ENABLING como cola priorizada de lectura cercana y
   registrar en el ledger qué afirmación concreta respalda cada fuente.
2. Comparar SP1 con baselines de coalición/asignación apropiados (MILP,
   generalized assignment, set partitioning, subastas o consenso según el
   caso), no con Hungarian salvo reducción demostrada uno-a-uno.
3. Para SP2 separar explícitamente cinemática/dinámica, contacto, wrench,
   seguridad y comunicación; no presentar equilibrio de Nash como garantía
   mecánica o de colisión.
4. Para SP3 comparar planificación/tráfico con el baseline que corresponda al
   escenario y medir bloqueos, colisiones, makespan, throughput y recuperación.
5. Completar la exportación WoS y una lectura humana de los candidatos
   prioritarios antes de redactar novelty claims o afirmar estado del arte.

## Respuestas explícitas a las preguntas del TFM

1. **Asignación multi-robot:** la literatura ya ofrece familias maduras de
   subastas, consenso, optimización y aprendizaje para asignación; la matriz
   documenta su presencia, pero no compara sus resultados como un benchmark
   homogéneo.
2. **Coaliciones/equipos:** existen trabajos de formación de equipos y
   coaliciones; la pregunta pendiente es su factibilidad simultánea bajo
   capacidades heterogéneas y restricciones físicas.
3. **Tareas multi-robot heterogéneas:** exigen requisitos colectivos,
   cardinalidad/capacidad y compatibilidad de roles; no basta la asignación
   independiente robot-tarea.
4. **Coalición local/distribuida:** aparecen señales de consenso, subastas,
   coordinación distribuida e información local; cada candidato debe
   confirmarse en texto completo para saber si la ejecución sigue siendo local.
5. **Coalición más transporte físico:** el corpus contiene candidatos con ambas
   familias de señales; la combinación exacta no se declara resuelta sin leer
   ecuaciones, contacto y protocolo experimental.
6. **Factibilidad mecánica:** contar robots o capacidad nominal no certifica
   factibilidad mecánica; la matriz separa esos indicios de contacto/wrench y
   no los convierte en certificados.
7. **Geometría, fuerza y wrench:** dichos términos aparecen en textos
   verificados, pero la existencia de la palabra no prueba force closure,
   reparto de wrench ni estabilidad.
8. **Sustitución tras fallo:** la señal de recuperación/reemplazo es reducida
   frente a asignación y coordinación; debe auditarse con lectura cercana y
   pruebas específicas de reconfiguración.
9. **Distribución durante ejecución:** `distributed` en la descripción de
   asignación no demuestra ejecución distribuida; se deben separar mensajes,
   control, navegación y transporte durante la operación.
10. **Radio, pérdida, retardo y topología:** el coding localiza supuestos de
    información y comunicación cuando están escritos; su tratamiento
    cuantitativo aún requiere extracción manual de cada fuente.
11. **Baselines:** usar MILP/set partitioning/generalized assignment o
    subastas/consenso para SP1; leader-follower, virtual structure,
    formación/consenso o reparto centralizado de fuerzas para SP2; y
    A*/Dijkstra, CBS/ECBS, planificación priorizada, ORCA/RVO o CBF-QP para
    SP3 según el escenario.
12. **Partes estándar:** asignación, subastas, consenso, control de formación,
    evitación y planificación son familias establecidas; el TFM debe
    posicionarse sobre interfaces y supuestos concretos.
13. **Adaptaciones:** la adaptación de una familia conocida a AMR
    heterogéneos, carga rígida, información local y fallos debe nombrarse como
    adaptación hasta demostrar qué componente cambia y qué evidencia aporta.
14. **Combinaciones insuficientemente cubiertas:** el mapa identifica señales
    escasas para algunas intersecciones, pero esto es un indicador de cobertura
    y no una prueba de ausencia o de gap universal.
15. **Novedad segura:** es seguro afirmar que la revisión construye una base
    trazable y que la integración SP1-SP3 es una hipótesis de posicionamiento
    que debe contrastarse con prior art.
16. **Claims prohibidos:** no afirmar primero, único, SOTA, optimalidad,
    convergencia, estabilidad, robustez, escalabilidad, seguridad garantizada
    ni ausencia de trabajo previo sin evidencia formal y comparación completa.

## Conclusión acotada

La evidencia reunida es suficiente para estructurar el marco de comparación y
para identificar interfaces de investigación entre coaliciones, transporte
físico y tráfico. No es suficiente para una declaración de novedad ni para
garantías matemáticas o experimentales del método del TFM. El siguiente paso
científico es close reading verificable y luego validación experimental bajo el
protocolo del repositorio.
