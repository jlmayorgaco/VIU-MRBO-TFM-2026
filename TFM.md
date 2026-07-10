# TFM.md - Mapa maestro cientifico del proyecto

**Proyecto:** Coordinacion distribuida de coaliciones multi-AMR para transporte cooperativo de cargas heterogeneas.  
**Repositorio:** `VIU-MRBO-TFM-2026`.  
**Autor:** Jorge Luis Mayorga Taborda.  
**Programa:** Master Universitario en Robotica y Automatizacion de Procesos, VIU.  
**Estado de este documento:** borrador estrategico vivo para entender, criticar, refinar y convertir el TFM en una memoria sobresaliente con ruta doctoral.

Este documento no sustituye la memoria final en LaTeX. Su funcion es mas dura: explicar el contexto completo, ordenar la metodologia, separar lo demostrado de lo aspiracional, y abrir una agenda teorica mas potente para que otra persona o sistema, por ejemplo Fable, pueda criticar la tesis, detectar debilidades y proponer mejoras.

## 0. Actualizacion canonica SP1-SP8

La arquitectura del proyecto queda organizada como una secuencia de subproblemas verificables, no como una coleccion de demos. La evidencia canonica vive en `docs/CANONICAL_RESULTS.md`; los limites de claims viven en `docs/CLAIM_LEDGER.md`; las instrucciones reproducibles viven en `docs/REPRODUCIBILITY.md`.

| SP | Pregunta | Estado | Evidencia principal |
|---|---|---|---|
| SP1 | Que AMR se reclutan para cargas heterogeneas? | Implementado | `results/sp1/`, tests, videos, rankings |
| SP2 | La coalicion satisface capacidad heterogenea? | Implementado | `results/sp2/`, tests, rankings |
| SP3 | La coalicion genera el wrench requerido? | Implementado | `results/sp3/`, wrench residual, false positives, videos de pose |
| SP4 | La coalicion se coordina en movimiento/control? | Implementado | `results/sp4/`, trayectorias, seguridad, videos |
| SP5 | Puede transportar evitando obstaculos/trafico sin romper formacion? | Implementado high-power | `results/sp5/SP5_MC_cooperative_transport_high_power/`, videos en la corrida compacta |
| SP6 | Puede recuperarse ante fallo/bateria/reemplazo mientras transporta? | Implementado high-power | `results/sp6/SP6_MC_robustness_comparison_high_power/`, videos en la corrida compacta |
| SP7 | Como degradan comunicacion/sensores el transporte cooperativo multi-grupo? | Implementado high-power como benchmark de conectividad temporal | `results/sp7/SP7_MC_communication_robustness_high_power/` |
| SP8 | Escala warehouse, intratabilidad y comparacion distribuida | Implementado high-power con escalera 5-50k AMR | `results/sp8/SP8_MC_fleet_ladder_high_power/` |

SP7 ya no es el benchmark MAPPO/OOD. Ahora es el subproblema de comunicacion y sensado: durante transporte cooperativo de cargas, mide radios de comunicacion, packet loss, burst drops, delays, jitter, caidas intermitentes, alcance de sensores, falsos negativos y ruido. La corrida canonica actual es `SP7_MC_communication_robustness_high_power`: 20.176 evaluaciones, 6 familias de escenarios, perfiles nominales/estresados y MC aleatorios de comunicacion/sensado, 97 seeds, 8 metodos y `failed_theory_checks = 0`. El resultado defendible por ahora es que la arquitectura ya mide conectividad directa, conectividad por relay, conectividad temporal, deteccion de obstaculos/grupos moviles y exito de transporte en mundos compartidos, sin permitir que los videos o tablas oculten colisiones o penetraciones carga-carga.

SP8 ya no queda como cajon de sastre final. Ahora es el estudio de escala: muchos AMR, muchas cargas simultaneas, rutas pickup-target, checks wrench/torque, obstaculos fijos y moviles, timeouts declarados de metodos centralizados, runtime, memoria, mensajes, throughput y Pareto calidad-complejidad. La corrida compacta contiene 150 evaluaciones, 10 metodos, 0 fallos de auditoria y dos MP4 mesoscopicos representativos. La corrida high-power `SP8_MC_fleet_ladder_high_power` usa una escalera densa de 20 tamanos unicos de flota, desde 5 hasta 50.000 AMR y hasta 12.500 cargas, con 20.000 evaluaciones, 10 metodos, 100 seeds por escala, figuras de escala mas legibles y 0 fallos de auditoria. El `10000` duplicado pedido para la escalera se conserva una sola vez para no sesgar las curvas.

La contribucion no es "Smith-QR solamente". Smith-QR es una instancia dentro de una familia de dinamicas y controles: replicator, logit, Brown/BNN, primal-dual, local repair, tensor/quorum flow, wrench-market y MAPPO/data-driven con decoders de factibilidad. La defensa debe vender esta familia y su evaluacion honesta, no un unico algoritmo aislado.

La ley de control explicita incorporada desde los documentos tecnicos de julio de 2026 queda ahora como puente ejecutable entre teoria y simulacion: punto de mano de uniciclo, wrench requerido PD con feedforward, reparto vGNE por salud/brazo, filtro HOCBF cerrado, inversion de dinamica y saturacion uniforme. Vive en `src/viu_mrob_tfm/control/explicit_law.py`, se valida en `tests/test_explicit_amr_control_law.py` y se evalua como suplemento en SP4, SP5 y SP6. El resumen tecnico esta en `docs/EXPLICIT_AMR_CONTROL_LAW.md`.

Regla de escritura: toda afirmacion fuerte de la memoria debe apuntar a uno de estos sitios: tabla/resultados canonicos, test, teoria formal, cita bibliografica o claim marcado como trabajo futuro. Si no se puede mapear, no se presenta como resultado.

## 1. Tesis central en una frase

El problema no es solo asignar robots a tareas, sino formar coaliciones fisicamente utiles de AMR para cargas heterogeneas bajo comunicacion limitada, coste energetico, geometria de contacto y demanda de fuerza/torque. La contribucion defendible es una arquitectura interpretable que conecta deficit de carga, juego poblacional, quorum entero, capacidad efectiva y validacion reproducible.

La version mas fuerte de la tesis es:

> Un sistema de transporte cooperativo multi-AMR puede formularse como un juego fisico-economico distribuido donde cada carga emite una presion de deficit, cada robot responde mediante dinamicas poblacionales y el cierre de coalicion se valida no solo por cardinalidad, sino por capacidad efectiva en espacio wrench, coste fisico y robustez bajo comunicacion local.

La version mas prudente para defensa VIU es:

> Se disena, implementa y valida por simulacion una arquitectura reproducible para reclutamiento y comparacion de coaliciones multi-AMR, con baselines clasicos, SOTA, model-based, data-driven y variantes propuestas, midiendo calidad de coalicion, gap frente a oraculo, coste fisico, coste computacional y degradacion por comunicacion.

## 2. Por que el tema importa

La automatizacion intralogistica madura ha resuelto muy bien el movimiento de unidades de carga estandarizadas con AMR individuales y gestores de flota. Esa solucion industrial deja una brecha relevante: muchas cargas reales son pesadas, largas, fragiles, voluminosas, desbalanceadas o requieren varios puntos de apoyo. En esos casos, comprar robots mas grandes para todo el flujo es caro e ineficiente, y dejar tareas al operador humano reduce continuidad operacional.

El transporte cooperativo por coaliciones temporales ofrece una alternativa: la capacidad no vive solo en el robot individual, sino en la combinacion de robots, posiciones, contactos, bateria, comunicacion y fuerza disponible. La dificultad es que la coalicion correcta no es simplemente "los tres robots mas cercanos". Debe ser factible como asignacion, ejecutable como movimiento, valida como contacto fisico y razonable como coste.

La originalidad potencial del TFM esta en no tratar esas capas como modulos aislados. El proyecto debe venderse como una arquitectura de acoplamiento:

```text
deficit de carga
  -> payoff local
  -> dinamica poblacional
  -> coalicion entera
  -> posicion/slot de contacto
  -> capacidad wrench
  -> coste fisico, energia y comunicacion
  -> validacion estadistica y visual
```

## 3. Requisitos VIU y como cumplirlos

Las guias publicas de VIU consultadas describen el TFM como un trabajo individual, original, supervisado, con memoria, anexos, defensa publica y evaluacion por tribunal. Tambien insisten en planificacion, resolucion de problemas, analisis de resultados y comunicacion clara. En guias de TFM/TFT recientes se exige depositar la memoria en PDF y, segun la guia, incluir declaracion de uso de IA generativa y autorizacion del director. Fuentes consultadas:

- VIU, Guia de Asignatura TFT 09MIAR, que define el TFM como planificacion, realizacion, presentacion y defensa de un proyecto original relacionado con el master, con aplicacion de conocimientos y competencias. Fuente: [VIU 09MIAR TFT](https://www.universidadviu.com/sites/universidadviu.com/files/media_files/Gui%CC%81a%20Asignatura%20TFT_09MIAR_V03.pdf).
- VIU, Guia de TFM que estructura la memoria en portada, resumen, tabla de contenido, glosario opcional, introduccion/estado del arte, desarrollo, resultados, conclusiones, bibliografia y apendices. Fuente: [VIU 21MIBI TFM](https://www.universidadviu.com/sites/universidadviu.com/files/media_files/21MIBI_GuiaDidactica_Trabajo_Fin_M%C3%A1ster.pdf).
- VIU, Guia de TFM Industria/Digitalizacion que menciona introduccion, objetivos, planificacion, desarrollo, resultados y conclusiones, ademas de estilo formal, extension aproximada, figuras y repositorio publico para codigo. Fuente: [VIU 09MIND TFM](https://www.universidadviu.com/sites/universidadviu.com/files/media_files/09MIND_10_A_Trabajo%20Fin%20de%20%20Master.pdf).
- VIU, Guia 15MUIN que explicita deposito en PDF, declaracion de uso de IA generativa, solicitud de defensa, autorizacion del director y defensa por videoconferencia ante tribunal. Fuente: [VIU 15MUIN TFT](https://www.universidadviu.com/sites/universidadviu.com/files/media_files/GUIA%20DE%20ASIGNATURA%2015MUIN.pdf).

El repositorio ya mantiene una alineacion interna en `docs/VIU_GUIDELINES_ALIGNMENT.md`. La memoria canonica esta en `docs/doc-05-final-report/main.tex`. Este `TFM.md` debe servir para revisar si esa memoria final cumple:

| Requisito VIU | Evidencia esperada en este proyecto | Riesgo |
|---|---|---|
| Trabajo original | Smith-QR, quorum, capacidad efectiva, comparacion SP1 y validacion reproducible | Sobrevender como teoria completa si solo hay simulacion |
| Introduccion y estado del arte | `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex` y `05-theoretical-framework` | Estado del arte debe conectar con cargas fisicas, no solo MRTA generico |
| Objetivos | `02-objectives.tex` | Deben ser falsables y medibles |
| Metodologia | `04-methodology.tex`, configs, scripts, tests | No basta narrar: hay que mapear metodo, escenario, metrica, seed |
| Desarrollo del proyecto | `src/viu_mrob_tfm`, `configs`, `scripts`, `results` | Evitar meter codigo largo en memoria; referenciar repo |
| Resultados y conclusiones | `results/validation_suite_v1`, `results/sp1/...`, `results/sp2/...`, `results/sp3/...`, `results/sp4/...`, `results/sp5/...`, `results/sp6/...` | Separar resultado principal, smoke, gate matematico y visualizacion |
| Bibliografia | `docs/doc-05-final-report/references.bib` | Verificar que cada claim fuerte tenga fuente real |
| Anexos | matematico, reproducibilidad, validacion | Deben contener detalles, no repetir narrativa |
| Defensa | figuras, videos, resumen ejecutivo | En 20 min hay que contar solo la historia ganadora |

## 4. Posicionamiento cientifico

El proyecto debe posicionarse en la interseccion de:

- MRTA y asignacion multi-robot.
- Formacion de coaliciones.
- Transporte cooperativo de objetos.
- Control distribuido y consenso.
- Teoria de juegos poblacionales.
- Juegos potenciales y busqueda de Nash.
- Capacidad efectiva en espacio wrench.
- Aprendizaje multiagente como comparador y posible acelerador.
- Validacion reproducible por simulacion.

La tesis no debe presentarse como "otro algoritmo de asignacion". La lectura potente es:

> Convertimos el reclutamiento de robots en una dinamica de escasez fisica, donde las cargas compiten por capacidad efectiva y los robots responden localmente a senales interpretables.

La frase anterior protege la novedad. No dice que se haya cerrado toda la teoria de control, ni que se domine universalmente a MARL, ni que se haya hecho despliegue industrial. Dice algo original y defendible: la capa discreta de coalicion se conecta con fisica y costes.

## 5. Subproblemas de investigacion

El TFM debe organizarse como una escalera de 8 subproblemas tecnicos. SP1, SP2, SP3, SP4, SP5 y SP6 ya existen como pipelines ejecutables y forman la prueba de concepto metodologica: comparan familias de metodos de forma justa, generan figuras, tablas, videos, tests e hipotesis, y separan la calidad de la solucion de su coste fisico, computacional y de entrenamiento. Los otros SP deben seguir el mismo patron para que el trabajo no parezca una coleccion dispersa de scripts.

Si se desea conservar la arquitectura del repositorio como objeto evaluable, puede llamarse SP0 de soporte transversal. Pero la narrativa cientifica principal debe ser SP1-SP8:

| SP | Nombre | Pregunta central | Estado actual | Resultado esperado |
|---|---|---|---|---|
| SP1 | Reclutamiento de coaliciones | Que robots deben asignarse a que cargas? | Implementado y validado | Ranking justo classic/SOTA/model-based/data-driven/ours/oracle |
| SP2 | Capacidad efectiva y heterogeneidad | Que significa que una carga quede realmente cubierta? | Implementado y validado | Pasar de cardinalidad a capacidad efectiva, masa, bateria, distancia y observabilidad |
| SP3 | Roles, slots y wrench | La coalicion puede producir fuerza/torque utiles? | Implementado y validado v3 + experimento dinamico | Asignacion carga-slot-robot, residual wrench, falsos positivos escalares y validacion Euler-Lagrange/Hamiltoniana |
| SP4 | Movimiento y llegada | Los robots llegan desde posiciones iniciales con coste razonable? | Implementado v1 y validado | Trayectorias, arrival time, energia, colisiones, comunicacion y congestion |
| SP5 | Transporte cooperativo de carga | Pueden los AMR recoger una carga, mantener formacion y llevarla a pose objetivo evitando obstaculos y otros grupos? | Implementado high-power y videos compactos | Movimiento rigido de payload, pickup, push/drag vs cargo, formacion, colisiones, pose final y videos |
| SP6 | Robustez operativa | Que pasa cuando falla un robot/bateria o cambia el entorno durante el transporte? | Implementado high-power y videos compactos | Recovery, fallos, bateria, cargas inviables y recuperacion |
| SP7 | Comunicacion, sensores y conectividad temporal | La coalicion sigue conectada y percibe obstaculos mientras transporta? | Implementado high-power | Radio, packet loss, delay, jitter, relay, sensores y transporte multi-grupo |
| SP8 | Escalabilidad warehouse e intratabilidad | Que pasa cuando el numero de AMR/cargas vuelve impracticables el oracle, MPC o asignaciones globales? | Implementado high-power + videos compactos | Benchmark mesoscopico con wrench/torque, cargas moviles, obstaculos fijos/moviles, timeouts, complejidad y metodos distribuidos/hierarquicos hasta 50.000 AMR |

**Evidencia ejecutada actual:**

| SP | Artefacto principal | Escenarios/seeds/metodos | Runs/checks | Auditoria | Lectura |
|---|---|---|---:|---|---|
| SP1 | `results/sp1/SP1_MC_recruitment_comparison` | 4 generadores, 100 seeds, 13 metodos | 27.300 checks | 0 fallos | MAPPO se acerca al oraculo; reglas clasicas son baratas pero con mayor gap |
| SP2 | `results/sp2/SP2_MC_capacity_comparison` | 5 generadores, 40 seeds, 13 metodos | 20.280 checks | 0 fallos | capacidad efectiva cambia el ranking; neural scorer gana entre no-oraculos por gap |
| SP3 | `results/sp3/SP3_MC_wrench_comparison_high_power` | 6 generadores, 334 seeds, 10 metodos | 20.040 runs / 38.076 checks | 0 fallos | criterio escalar produce falsos positivos; wrench oracle define el benchmark fisico; videos se conservan en el run compacto |
| SP4 | `results/sp4/SP4_MC_motion_comparison_high_power` | 6 generadores, 223 seeds, 15 metodos | 20.070 rollouts / 21.408 checks | 0 fallos | trade-off llegada-seguridad con familia completa: classic, SOTA, replicator/logit/BNN/primal-dual/PID/tensor/Smith/ley explicita |
| SP4-explicit | `results/sp4/SP4_MC_explicit_control_law` | 6 generadores, 12 seeds, 6 metodos | 432 rollouts / 504 checks | 0 fallos | ley explicita AMR llega, pero no reduce colision ni gap frente a direct/CBF; resultado negativo util |
| SP5 | `results/sp5/SP5_MC_cooperative_transport_high_power` | 6 generadores, 334 seeds, 10 metodos | 20.040 rollouts / 20.040 checks | 0 fallos | payload rigido con clearance duro; los near-misses de margen quedan penalizados y reportados, videos en `SP5_MC_cooperative_transport` |
| SP5-explicit | `results/sp5/SP5_MC_explicit_control_law` | 4 generadores, 12 seeds, 9 metodos | 432 rollouts / 432 checks | 0 fallos | `ours_explicit_vgne_cbf_cargo` llega al target en 100%, rank 3; `push` no confirma mejora de residual |
| SP6 | `results/sp6/SP6_MC_robustness_comparison_high_power` | 8 generadores, 250 seeds, 10 metodos | 20.000 rollouts / 20.000 checks | 0 fallos | recovery con no-colision dura AMR-AMR, AMR-obstaculo, carga-obstaculo y carga-carga; videos en `SP6_MC_robustness_comparison` |
| SP6-explicit | `results/sp6/SP6_MC_explicit_control_law` | 5 generadores, 12 seeds, 6 metodos | 360 rollouts / 360 checks | 0 fallos | ley explicita mejora trazabilidad de wrench requerido; no prueba superioridad en lost-load/completion |
| SP7 | `results/sp7/SP7_MC_communication_robustness_high_power` | 6 generadores, perfiles nominales/estresados + MC, 97 seeds, 8 metodos | 20.176 runs / 20.176 checks | 0 fallos | mide radio, relay, packet loss, delay, jitter, sensores, exito de transporte y clearances heredados de SP5 |
| SP8 | `results/sp8/SP8_MC_fleet_ladder_high_power` | 20 tamanos de flota, 100 seeds por tamano, 10 metodos | 20.000 runs / 20.000 checks | 0 fallos | escalera 5-50.000 AMR y 1-12.500 cargas; centralizados/time-expanded declaran timeout, mientras propuestas distribuidas/hierarquicas conservan completion/wrench por recurso |

### 5.1 Integracion Wrench-Market Games

El PDF `wrench_market_games_paper (1).pdf` debe incorporarse como marco teorico transversal, no como apendice decorativo. La tesis fuerte que aporta es:

```text
contribucion vectorial E_ik
  -> agregado de carga S_k
  -> precio marginal / shadow price
  -> motor de revision positiva
  -> clearing entero con guardia
  -> certificado fisico wrench/movimiento
```

La consecuencia metodologica es importante: Smith-QR no es la contribucion completa. Smith es un motor de revision dentro de una clase mas amplia que incluye Replicator, Brown/BNN, Logit, primal-dual, PID y tensor-flow. Lo defendible como arquitectura propia es el acoplamiento entre senal fisica correcta, precio marginal, clearing entero y certificado de factibilidad.

El documento tecnico de trazabilidad queda en `docs/WRENCH_MARKET_GAMES_INTEGRATION.md`. La integracion practica anade cuatro configs nuevas:

| SP | Config nueva | Prediccion que prueba |
|---|---|---|
| SP1 | `SP1_MC_wrench_market_protocol_repair.yaml` | motores poblacionales + repair local para clearing entero |
| SP2 | `SP2_MC_wrench_market_vector_potential_repair.yaml` | payoff marginal frente a payoff plano y factorization obstruction |
| SP3 | `SP3_MC_wrench_market_protocol_invariance.yaml` | falsos positivos escalares, complementariedad wrench, senal continua e invariancia de motor |
| SP4 | `SP4_MC_wrench_market_motion_safety.yaml` | campos de movimiento seguros: replicator/logit/BNN/Smith/primal-dual/PID/tensor-flow |

Estas configs no sustituyen los resultados Monte Carlo ya citados; son la siguiente campana congelada si se quiere elevar la memoria hacia la teoria Wrench-Market Games. Hasta ejecutarlas no debe afirmarse superioridad estadistica de la nueva familia; si debe afirmarse que la arquitectura y las hipotesis ya estan codificadas y son reproducibles.

**Diagnostico rapido ejecutado:** se corrieron configs `DIAG` sin video para verificar si la familia nueva mejora antes de lanzar la campana final pesada. Resultado:

| SP | Resultado diagnostico | Lectura honesta |
|---|---|---|
| SP1 | `replicator_cardinality_repair` baja el gap vs `replicator_cardinality` en `-0.510` (`p_Holm=2.64e-69`); `tensor_quorum_flow_repair` baja gap vs `cbba` en `-0.289` (`p_Holm=4.29e-38`) | mejora clara de calidad de reclutamiento con repair local |
| SP2 | `smith_capacity_marginal` confirma mejora vs `smith_capacity_plain` (`-0.221`, `p_Holm=7.70e-124`), pero `smith_capacity_marginal_repair` empeora gap vs marginal aunque sube success e incomplete-capacity | marginal pricing si mejora; completion repair necesita retuning |
| SP3 | `smith_wrench_pairs_guarded` logra precision `1.0`, `fp_given_assigned=0.0`, gap `0.000012`; baja gap vs `smith_wrench_marginal` en `-0.0923` (`p_Holm=1.36e-25`) | mejora fuerte: corrige falsos positivos fisicos |
| SP4 | `tensor_flow_motion_field` baja collision vs direct en `-0.0382` (`p_Holm=2.06e-14`); `primal_dual_motion_field` baja gap vs APF en `-0.0707` (`p_Holm=3.43e-09`) | mejora seguridad/Pareto, pero paga timeout/llegada |

Las cuatro auditorias teoricas del diagnostico pasaron con `failed_checks=0`. Estos resultados justifican ejecutar los Monte Carlo finales con video; no deben mezclarse con los rankings historicos como si fueran la misma campana.

### 5.2 Ley de control explicita AMR

Los PDFs tecnicos de julio de 2026 se incorporan como una ley cerrada ejecutable, no como texto decorativo. La version implementada se normaliza a nomenclatura AMR y consta de nueve bloques:

```text
punto de mano h_i = p_i + a_i e(theta_i)
  -> salud eta_i por bateria
  -> consenso dinamico de H=sum eta_i y S=sum eta_i||r_i||^2
  -> reconstruccion local de pose de carga desde contacto rigido
  -> wrench requerido PD critico-amortiguado con feedforward
  -> reparto vGNE f_i* = eta_i/H w_p + eta_i/S perp(Rr_i) tau
  -> impedancia rigida del punto de mano
  -> proyeccion HOCBF cerrada sobre semiespacios
  -> inversion exacta uniciclo + saturacion uniforme fuerza/par
```

La implementacion vive en `src/viu_mrob_tfm/control/explicit_law.py`. Las pruebas `tests/test_explicit_amr_control_law.py` validan el punto de mano, el ejemplo numerico de wrench requerido (`78.5 N`, `47.1 N`, `5.70 N m`), el cierre de fuerza/torque del vGNE, la proyeccion HOCBF y la saturacion uniforme. Los entry points no cambian: la ley aparece como metodo o bloque interno en los pipelines existentes.

| SP | Integracion | Config/resultados | Lectura |
|---|---|---|---|
| SP4 | `explicit_vgne_cbf_motion` | `SP4_MC_explicit_control_law`, 432 rollouts | llega al target, pero no reduce colision ni gap frente a direct/CBF; no vender como superioridad |
| SP5 | `ours_explicit_vgne_cbf_push` y `ours_explicit_vgne_cbf_cargo` | `SP5_MC_explicit_control_law`, 432 rollouts | la variante cargo alcanza `target_reached=1.0`, rank 3, y mejora posicion final frente a VO cargo; push no confirma mejora de residual |
| SP6 | generacion de wrench requerido explicita en tensor/ours/reference | `SP6_MC_explicit_control_law`, 360 rollouts | mayor trazabilidad fisica; no confirma mejora en lost-load ni completion frente a greedy/Smith |

Se generaron MP4 manuales especificos porque los selectores automaticos tienden a escoger la referencia centralizada: `sp4_crossing_traffic_explicit-vgne-cbf-motion_manual_seed5400.mp4`, `sp5_overactuated_push_drag_explicit-vgne-cbf-cargo_manual_seed6655.mp4` y `sp6_robot_dropout_mid_task_ours-guarded-explicit-control_manual_seed7656.mp4`.

Esta seccion es metodologicamente importante: la ley explicita fortalece el puente teoria-control, pero no permite declarar que todo metodo nuestro domina. La tesis debe presentar el resultado como maduracion fisica del framework y como base doctoral para CBF certificados, implementacion embebida y contacto real.

El contrato comun de todos los SP debe ser:

```text
escenario reproducible
  -> familia de metodos comparables
  -> metricas primarias y de coste
  -> hipotesis falsable
  -> tabla + figura + video si aplica
  -> audit trail en results/
```

### SP1 - Reclutamiento y asignacion de coaliciones

**Pregunta:** Que robots deben reclutarse para que cargas heterogeneas reciban coaliciones utiles?

**Estado actual:** SP1 esta implementado. El pipeline compara metodos clasicos, SOTA, model-based, data-driven, variantes propuestas y referencias oraculares. Genera tablas, reportes, figuras, videos, tests e hipotesis estadisticas.

**Implementacion trazable:** SP1 vive en `src/viu_mrob_tfm/sp1`. El escenario se define en `scenario.py` con `SP1RecruitmentScenarioParams`, `SP1RecruitmentScenario` e `iter_sp1_worlds`. La fabrica `make_sp1_allocator` de `methods.py` instancia los metodos a partir de ids estables. Las metricas se calculan en `metrics.py` mediante `SP1Metrics`, `evaluate_assignment` y `load_diagnostics`. El runner `runner.py` expone `run_sp1_config`, ejecuta entrenamiento, tuning o Monte Carlo segun YAML, escribe `runs.csv`, `summary.csv`, `performance_ranking.csv`, `hypothesis_results.csv`, `theory_checks.csv`, `theory_audit.json`, figuras y MP4. Las visualizaciones estan en `visualization.py`. Los entry points son `viu-run-sp1` y `scripts/run_sp1_experiment.py`.

**Arquitectura SP1:** el contrato central sigue siendo `Assignment` global, con `labels` robot->carga. SP1 no introduce slots fisicos; interpreta una carga como una demanda de quorum/capacidad escalar. El pipeline separa cinco capas: generacion de mundo, allocator, evaluacion, auditoria teorica y artefactos visuales. La capa de fairness anade metadatos por metodo (`method_family`, `method_scope`, `method_ownership`, parametros, entrenamiento, comunicacion) para que un MAPPO entrenado no se compare como si costara lo mismo que una regla Smith de pocos parametros.

**Simulacion SP1:** Cada corrida genera un mundo sintetico con AMR homogeneos o heterogeneos en capacidad, cargas con demanda entera de coalicion, posiciones iniciales, bateria, coste de viaje y radio de comunicacion. Todos los metodos reciben exactamente el mismo `WorldState` para cada par `(scenario_generator, seed)`. El resultado de cada metodo es un vector discreto `labels_i in {0,...,M}`, donde `0` significa robot no asignado y `k` significa robot asignado a la carga `k`. La evaluacion comprueba si cada carga recibe al menos el quorum requerido, si la capacidad de payload es suficiente, cuanto recorrido exige la asignacion y cuanto se separa de la referencia oracular.

**Metodos SP1 comparados:**

| Grupo | Ids principales | Clase/implementacion | Lectura metodologica |
|---|---|---|---|
| Classic centralized | `hungarian_expanded` | `CentralizedClassicAllocator` | Baseline centralizado de asignacion expandida por slots |
| Classic decentralized | `greedy_nearest` | `DecentralizedClassicGreedyAllocator` | Regla local barata por cercania |
| Reference/oracle | `centralized_coalition_milp`, `oracle_reference` | `CentralizedCoalitionOracleAllocator` | Cota no desplegable para score/gap |
| SOTA decentralized proxy | `cbba` | `DecentralizedAuctionAllocator` | Subasta tipo CBBA, interpretable y distribuida |
| Model-based baselines | `replicator_cardinality`, `bnn_cardinality` | `UtilityGreedyAllocator` | Utilidades poblacionales compactas |
| Proposed model-based | `smith_cardinality`, `primal_dual_cardinality_capacity`, `primal_dual_wrench_market`, `local_primal_dual_wrench_market` | `SmithQRAllocator`, `PrimalDualRecruitmentAllocator` | Variaciones interpretables con deficit, capacidad y proxy wrench |
| Proposed hybrid repair | `replicator_cardinality_repair`, `logit_cardinality_repair`, `bnn_cardinality_repair`, `primal_dual_local_repair`, `tensor_quorum_flow_repair` | `LocalRepairRecruitmentAllocator` sobre motores poblacionales/primal-dual | Familia no-Smith: dinamica barata + reparacion local monotona para cerrar coaliciones incompletas |
| Data-driven baseline | `imitation_oracle` | `ImitationRecruitmentAllocator` | Scorer lineal supervisado por oraculo, 7 parametros |
| Data-driven proposed | `mappo_recruitment` | `MAPPORecruitmentAllocator` | MAPPO-style CTDE con actor descentralizado y decoder de quorum |

**Metricas SP1:** `coalition_success_rate`, `served_load_rate`, `demand_satisfaction_ratio`, `robots_underassigned`, `robots_overassigned`, `assignment_cost`, `travel_distance_m`, `estimated_arrival_time_s`, `energy_proxy_wh`, `priority_regret`, `optimality_gap_vs_oracle`, `strategy_switches`, `communication_messages` y `runtime_ms`. La metrica primaria no es solo satisfaccion de demanda: el ranking prioriza gap teorico, exito de coalicion, cargas servidas y despues costes fisicos/computacionales.

**Revision metodologica SP1 no-Smith:** el codigo ya no presenta Smith-QR como unica contribucion. La nueva familia proposed hybrid repair separa tres componentes: motor de preferencia (`replicator`, `logit`, `BNN/Brown`, `primal-dual`, `tensor_quorum_flow`), clearing entero `Assignment`, y reparacion local finita que solo acepta cambios con mejora de score. Esto permite defender que la contribucion es una arquitectura de dinamicas + certificacion local, no un unico algoritmo.

**Resultado principal reciente:** En `results/sp1/SP1_MC_recruitment_comparison` hay 27.300 evaluaciones/checks, 13 ids de metodo si se incluye `oracle_reference`, 100 seeds, 4 generadores de escenarios y MP4 representativos por escenario/metodo. El ranking theory-aligned ubica:

| Rank | Metodo | Familia | Gap vs oracle | Success | Travel | Runtime | Params |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | centralized_coalition_milp | oracle | 0.000 | 0.847 | 30.03 m | 2.60 ms | 0 |
| 2 | oracle_reference | oracle | 0.000 | 0.847 | 30.03 m | 2.64 ms | 0 |
| 3 | mappo_recruitment | data-driven proposed | 0.004 | 0.846 | 29.99 m | 13.87 ms | 4674 |
| 4 | hungarian_expanded | classic centralized | 0.277 | 0.721 | 29.24 m | 0.065 ms | 0 |
| 5 | greedy_nearest | classic decentralized | 0.304 | 0.722 | 31.39 m | 0.131 ms | 0 |
| 6 | cbba | SOTA proxy decentralized | 0.338 | 0.698 | 30.33 m | 0.408 ms | 0 |
| 7 | imitation_oracle | data-driven baseline | 0.377 | 0.658 | 28.24 m | 0.664 ms | 7 |

**Lectura critica:** MAPPO se acerca mucho al oraculo, pero no es gratis. Tiene miles de parametros, entrenamiento y mayor runtime. Smith es mucho mas barato pero actualmente paga en gap y success. Esta comparacion de calidad contra recursos es cientificamente mejor que declarar un ganador unico.

**Entrenamiento data-driven SP1:** MAPPO usa actor compartido descentralizado, critic centralizado, warm start por behavior cloning y PPO con `rollout_action_mode: sampled_policy`. El checkpoint reporta 4674 parametros en actor, 9411 parametros actor+critic, 768 episodios, 1000 seeds de entrenamiento, 200 seeds de validacion y 200 de test. En test obtiene `demand_satisfaction_ratio_mean = 0.890`, `coalition_success_rate_mean = 0.884` y `optimality_gap_vs_oracle_mean = 0.0010`. Esto permite afirmar que SP1 tiene RL real, pero no que MAPPO sea una garantia general fuera de los generadores evaluados.

**Hipotesis SP1:** El Monte Carlo rechaza que todos los metodos tengan el mismo gap (`p_Holm = 0`, Kendall W `0.606`). MAPPO reduce gap frente a imitation (`effect=-0.373`, IC95 `[-0.390,-0.355]`, `p_Holm=0`) y frente a Hungarian (`effect=-0.272`, IC95 `[-0.289,-0.255]`, `p_Holm=1.56e-182`). Smith es mas rapido que MAPPO (`effect=-13.71 ms`, IC95 `[-14.27,-13.21]`, `p_Holm=0`) y MAPPO logra mayor success que Smith (`effect=0.287`, IC95 `[0.279,0.295]`, `p_Holm=0`). La auditoria teorica tiene 27.300 checks y 0 fallos. La conclusion defendible es que MAPPO se acerca al oraculo bajo este protocolo, pagando entrenamiento y runtime; no que domine universalmente.

**Artefactos SP1 existentes:** `results/sp1/SP1_MC_recruitment_comparison/report.md`, `tables/performance_ranking.csv`, `tables/hypothesis_results.csv`, `figures/sp1_quality_resource_pareto.png`, `figures/sp1_physical_cost_tradeoff.png`, videos por escenario/metodo y `theory_audit.json`.

### SP2 - Capacidad efectiva y cargas heterogeneas

**Pregunta:** Cuando una carga tiene masa, demanda de capacidad, bateria disponible en los robots y coste de llegar, como decide el sistema si una coalicion realmente cubre la carga?

**Criterio:** No basta con `|C_k| >= n_k`. Se requiere:

```math
S_k(C_k,q,b,G) >= D_k
```

y, si hay contacto fisico:

```math
\min_{0 \le \lambda \le \bar f}
  \|G_{C_k}\lambda - w_k^{dem}\|_2 \le \epsilon_k.
```

**Estado:** SP2 ya esta implementado como pipeline Monte Carlo. Es deliberadamente mas fisico que SP1: separa capacidad efectiva fisica de visibilidad por comunicacion. La capacidad efectiva de robot `i` sobre carga `k` combina payload nominal, factor de bateria y decaimiento por distancia. La comunicacion se registra como observabilidad (`communication_coverage_ratio`) y coste (`communication_messages`), no como descuento fisico escondido.

**Implementacion trazable:** SP2 vive en `src/viu_mrob_tfm/sp2`. El escenario se define en `scenario.py` con `SP2CapacityScenarioParams`, `SP2CapacityScenario` e `iter_sp2_worlds`. Los metodos se instancian en `methods.py` con `make_sp2_allocator`. Las funciones clave son `physical_effective_capacity_matrix`, `communication_visibility_matrix`, `effective_capacity_matrix`, `feature_tensor`, `SP2Metrics`, `evaluate_assignment` y `load_diagnostics`. El runner `runner.py` ejecuta entrenamiento supervisado, tuning model-based o Monte Carlo con `run_sp2_config`; tambien escribe `performance_ranking.csv`, `hypothesis_results.csv`, `theory_checks.csv` y `theory_audit.json`. Las visualizaciones viven en `visualization.py`. Los entry points son `viu-run-sp2` y `scripts/run_sp2_experiment.py`.

**Arquitectura SP2:** SP2 conserva el contrato `Assignment`, pero cambia la semantica de la demanda: una etiqueta robot->carga ya no significa "un robot mas", sino contribucion de capacidad efectiva `e_ik`. La arquitectura separa capacidad fisica entregable, visibilidad por comunicacion, score operativo y techo fisico de capacidad. Por eso hay dos referencias: `oracle_reference` para score operativo y `capacity_oracle_reference` para techo fisico. El tuning model-based y el entrenamiento data-driven usan seeds separadas del Monte Carlo final.

**Simulacion SP2:** Cada mundo sintetico contiene AMR con payload, bateria y consumo, cargas con masa/demanda de capacidad, recompensas y posiciones. La capacidad efectiva usada por los metodos es:

```math
e_{ik}
=
c_i
\cdot
\max\left(0,\frac{b_i-b_i^{res}}{1-b_i^{res}}\right)
\cdot
\exp\left(-\frac{\|q_i-p_k\|}{\ell_d}\right).
```

La demanda de una carga queda cubierta cuando la suma de capacidad efectiva asignada alcanza `D_k`. Este criterio evita que un robot nominalmente fuerte pero lejos o con poca bateria cuente igual que uno disponible fisicamente. El cierre wrench completo, con `G_C lambda`, queda como SP3, no como resultado cerrado de SP2.

**Interpretacion fisica del descuento por distancia:** `e_ik` no se interpreta como payload mecanico estatico. Un AMR lejano no pierde kg nominales por estar lejos. En SP2, `e_ik` representa capacidad entregable dentro de un horizonte operativo finito: payload nominal corregido por bateria, tiempo/coste de llegada y oportunidad operacional. La capacidad estatica se recupera con `ell_d -> infinity` o moviendo toda la distancia al coste separable `g_ik`.

**Teorema 2 - payoff marginal de capacidad efectiva:** como `e_ik` depende del par robot-carga, el agregado:

```math
S_k(x)=\sum_i e_{ik}x_{ik}
```

no preserva en general la estructura potencial si el payoff mantiene la forma plana:

```math
p_{ik}=V_k\sigma(D_k-S_k)-g_{ik}.
```

La razon es que las derivadas cruzadas escalan con `e_jk` y `e_ik`; solo coinciden si la matriz de capacidad efectiva factoriza de forma especial. El payoff corregido por el teorema es:

```math
p_{ik}=e_{ik}V_k\sigma(D_k-S_k)-g_{ik},
```

que recupera una estructura de potencial exacto para `E=[e_ik]` fija durante el instante de decision. En el codigo esto queda como ablacion explicita entre `smith_capacity_plain`, `smith_capacity_marginal`, `replicator_capacity_plain` y `replicator_capacity_marginal`.

**Metodos SP2 comparados:**

| Grupo | Ids principales | Clase/implementacion | Lectura metodologica |
|---|---|---|---|
| Classic centralized | `hungarian_capacity` | `HungarianCapacityAllocator` | Asignacion centralizada por slots de capacidad |
| Classic decentralized | `greedy_capacity_nearest` | `GreedyCapacityAllocator` | Regla local por capacidad efectiva y distancia |
| Reference/oracle score | `centralized_capacity_milp`, `oracle_reference` | `CentralizedCapacityMILPAllocator` | MILP que optimiza cobertura, cargas completas y costes pequenos |
| Reference/oracle capacidad | `capacity_oracle_reference` | `CentralizedCapacityCoverageMILPAllocator` | Cota pura de capacidad fisica, sin priorizar score de tarea |
| SOTA decentralized proxy | `cbba_capacity` | `CapacityAuctionAllocator` | Subasta payload-aware tipo CBBA |
| Model-based baselines | `replicator_capacity`, `bnn_capacity` | `UtilityCapacityAllocator` | Utilidades de deficit/capacidad compactas |
| Model-based ablation | `replicator_capacity_plain`, `replicator_capacity_marginal` | `UtilityCapacityAllocator` | Contraste Teorema 2: payoff plano vs marginal |
| Proposed model-based | `smith_capacity`, `primal_dual_capacity`, `local_primal_dual_capacity` | `UtilityCapacityAllocator`, `PrimalDualCapacityAllocator` | Smith-QR y primal-dual adaptados a capacidad efectiva |
| Proposed ablation | `smith_capacity_plain`, `smith_capacity_marginal` | `UtilityCapacityAllocator` | Smith-QR con payoff plano vs payoff marginal `e_ik V sigma` |
| Proposed hybrid repair | `replicator_capacity_marginal_repair`, `logit_capacity_repair`, `bnn_capacity_repair`, `smith_capacity_marginal_repair`, `primal_dual_capacity_repair`, `pid_capacity_repair` | `LocalRepairCapacityAllocator` sobre `UtilityCapacityAllocator` o `PrimalDualCapacityAllocator` | Familia de completion repair: penaliza capacidad atrapada en cargas incompletas y acepta solo mejoras finitas de score |
| Data-driven baseline | `imitation_capacity` | `ImitationCapacityAllocator` | Scorer lineal supervisado por oraculo, 8 parametros |
| Data-driven proposed | `neural_capacity_scorer` | `NeuralCapacityScorerAllocator` | MLP compacto de una capa oculta supervisado por oraculo, 121 parametros |

**Metricas SP2:** las metricas primarias son `capacity_success_rate`, `optimality_gap_vs_oracle` y `capacity_gap_vs_capacity_oracle`. `capacity_satisfaction_ratio` queda como cobertura secundaria porque puede subir aunque no se completen cargas. Tambien se reportan `incomplete_capacity_ratio`, `served_capacity_alignment`, `effective_feasibility_ratio`, `under_capacity_kg`, `over_capacity_kg`, `capacity_waste_ratio`, `travel_distance_m`, `estimated_arrival_time_s`, `energy_proxy_wh`, `communication_coverage_ratio`, `communication_messages`, `runtime_ms`, `score_value`, `oracle_score_value` y `oracle_dominance_violation`. SP2 usa dos referencias porque hay dos preguntas distintas: score operativo y techo fisico de capacidad.

**Revision metodologica SP2 no-Smith:** la mejora actual introduce completion repair para motores replicator, logit, BNN/Brown, primal-dual, PID y Smith marginal. La auditoria `sp2_potential_alignment` distingue dos casos: `*_marginal_repair` conserva el payoff marginal del Teorema 2 y anade reparacion local monotona; los otros `*_repair` son heuristicas fisicamente honestas, no teoremas de potencial exacto. Este matiz es importante para defensa: la reparacion mejora coherencia operativa, pero no debe venderse como garantia global de optimalidad.

**Resultado principal reciente:** En `results/sp2/SP2_MC_capacity_comparison` hay 20.280 checks, 13 metodos, 40 seeds, 5 generadores de escenarios y MP4 representativos por escenario/metodo. El ranking theory-aligned ubica:

| Rank | Metodo | Familia | Capacity | Success | Score gap | Capacity gap | Travel | Runtime | Params |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | oracle_reference | oracle score | 0.514 | 0.487 | 0.000 | 0.029 | 62.10 m | 40.84 ms | 0 |
| 2 | centralized_capacity_milp | oracle score | 0.514 | 0.487 | 0.000 | 0.029 | 62.10 m | 40.94 ms | 0 |
| 3 | capacity_oracle_reference | oracle capacidad | 0.529 | 0.227 | 0.049 | 0.000 | 59.58 m | 11.32 ms | 0 |
| 4 | neural_capacity_scorer | data-driven proposed | 0.507 | 0.263 | 0.109 | 0.050 | 52.67 m | 1.01 ms | 121 |
| 5 | imitation_capacity | data-driven baseline | 0.514 | 0.218 | 0.118 | 0.038 | 52.83 m | 0.98 ms | 8 |
| 6 | hungarian_capacity | classic centralized | 0.510 | 0.083 | 0.228 | 0.041 | 48.89 m | 0.22 ms | 0 |
| 7 | greedy_capacity_nearest | classic decentralized | 0.510 | 0.219 | 0.276 | 0.044 | 54.44 m | 0.30 ms | 0 |
| 8 | replicator_capacity | model-based baseline | 0.525 | 0.139 | 0.297 | 0.026 | 56.28 m | 0.36 ms | 0 |
| 11 | smith_capacity | proposed model-based | 0.521 | 0.103 | 0.343 | 0.033 | 61.21 m | 0.35 ms | 0 |

**Lectura critica:** SP2 no demuestra que los metodos model-based propuestos ganen en success. Muestra algo mas util: cuando se juzga capacidad parcial, reglas compactas como Smith/replicator tienen buena cobertura cercana al techo de capacidad, pero fallan en completar cargas frente al oraculo de score. El mejor metodo propuesto por score es `neural_capacity_scorer`; aun asi, es supervised distillation, no MARL. Esto debe decirse claramente en defensa.

**Ablacion Teorema 2:** se ejecuto `configs/experiments/sp2/SP2_MC_marginal_payoff_ablation.yaml` con las mismas seeds finales `3100`-`3139` y los mismos cinco generadores. La auditoria produjo 9.360 checks, 0 fallos y `theory_audit.json` con `potential_alignment`: capacidad efectiva par-dependiente, estructura mixta en el experimento, y potencial exacto para `replicator_capacity_marginal` y `smith_capacity_marginal`.

| Rank | Metodo | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Runtime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | oracle_reference | 0.487 | 0.000 | 0.029 | 0.514 | 0.299 | 0.694 | 46.42 ms |
| 2 | capacity_oracle_reference | 0.227 | 0.049 | 0.000 | 0.529 | 0.733 | 0.263 | 12.86 ms |
| 3 | replicator_capacity_marginal | 0.156 | 0.152 | 0.027 | 0.520 | 0.816 | 0.167 | 0.401 ms |
| 4 | smith_capacity_marginal | 0.135 | 0.157 | 0.026 | 0.521 | 0.848 | 0.137 | 0.405 ms |
| 5 | replicator_capacity_plain | 0.054 | 0.362 | 0.066 | 0.497 | 0.943 | 0.053 | 0.409 ms |
| 6 | smith_capacity_plain | 0.051 | 0.372 | 0.076 | 0.492 | 0.946 | 0.049 | 0.396 ms |

Resultado: el payoff marginal no convierte a Smith en ganador global, pero si valida la prediccion teorica. Para Smith reduce el score gap en `0.2145`, sube success en `0.0838`, reduce la capacidad asignada a cargas incompletas en `0.0982` y mejora `served_capacity_alignment` en `0.0877`; todos con `p << 0.001` sobre 1.560 pares. La lectura fuerte es: la alineacion potencial es necesaria para no dispersar capacidad, pero aun no suficiente para igualar al oraculo de score.

**Entrenamiento y tuning SP2:** Los metodos data-driven se entrenan con `configs/training/sp2/SP2_capacity_data_driven.yaml`, usando 24 seeds de train, 10 de validation y 10 de test, separados del Monte Carlo final. `imitation_capacity` usa 936 contextos y 8 parametros; en test obtiene capacity satisfaction 0.511, success 0.226 y score gap 0.115. `neural_capacity_scorer` usa 121 parametros, 220 epocas supervisadas y baja el score gap de test a 0.103, con success 0.272. Los model-based se ajustan con `SP2_model_based_tuning.yaml` sobre seeds separados y guardan `outputs/tuning/SP2/model_based/v1/best_params.yaml`.

**Hipotesis SP2:** El Monte Carlo general rechaza diferencias nulas entre metodos en score gap (`p_Holm=0`, Kendall W `0.710`) y capacity-ceiling gap (`p_Holm=5.68e-10`). Tambien confirma que la red neural reduce score gap frente a imitation lineal (`effect=-0.0097`, IC95 `[-0.0118,-0.0076]`, `p_Holm=1.17e-26`), que el local primal-dual usa menos mensajes que el oraculo (`effect=-2.84`, IC95 `[-3.23,-2.46]`, `p_Holm=6.85e-18`) y que Smith es mas rapido que la red neural (`effect=-0.663 ms`, IC95 `[-0.686,-0.644]`, `p_Holm=8.71e-256`). No confirma que `primal_dual_capacity` tenga mayor success que `greedy_capacity_nearest` (`effect=-0.119`, `p_Holm=1.0`); ese resultado negativo debe quedar como hallazgo, no esconderse. La ablacion confirma `H-SP2-Marginal` y `H-SP2-Potential`: para Smith marginal baja score gap (`effect=-0.2145`, `p_Holm=2.23e-242`), sube success (`effect=0.0838`, `p_Holm=8.43e-59`), baja capacidad incompleta (`effect=-0.0982`, `p_Holm=9.97e-62`) y sube alignment (`effect=0.0877`, `p_Holm=7.11e-59`). La auditoria teorica del experimento general tiene 20.280 checks, 0 fallos y 0 violaciones de dominancia del oraculo; la ablacion marginal suma 9.360 checks adicionales con 0 fallos.

**Artefactos SP2 existentes:** `results/sp2/SP2_MC_capacity_comparison/report.md`, `tables/performance_ranking.csv`, `tables/hypothesis_results.csv`, `tables/load_status.csv`, `figures/sp2_quality_resource_pareto.png`, `figures/sp2_capacity_cost_tradeoff.png`, `figures/sp2_communication_radius_degradation.png`, videos por escenario/metodo, `theory_audit.json`, checkpoints data-driven y tuning model-based. La ablacion del Teorema 2 esta en `results/sp2/SP2_MC_marginal_payoff_ablation/report.md` e incluye `figures/sp2_capacity_coverage_vs_completion.png`, `tables/hypothesis_results.csv`, videos plain/marginal y `theory_audit.json` con `potential_alignment`.

### SP3 - Roles, slots y capacidad wrench

**Pregunta:** La coalicion asignada puede generar la fuerza y el torque que la carga necesita?

**Criterio:** Cardinalidad y capacidad escalar no bastan. Para cada carga:

```math
r_k(C_k)
=
\min_{0 \le \lambda \le \bar f}
\|G_{C_k}\lambda - w_k^{dem}\|_2
\le \epsilon_k.
```

**Estado:** SP3 ya existe como pipeline v1 en `src/viu_mrob_tfm/sp3`. Define escenarios con slots de contacto, matriz wrench planar, ajuste least-squares acotado, metricas de falsos positivos escalares, residual wrench, complementariedad, plots, snapshots y MP4. La revision metodologica nueva corrige la lista de metodos: Replicator, Smith, BNN, CBBA y primal-dual son motores dinamicos, no propuestas por si solos. La contribucion SP3 esta en la senal wrench, el margen `rho`, el clearing por slots y el mercado de wrenches.

**Principio de diseno SP3:** la carga no pide robots ni kg; pide reduccion de deficit wrench. La condicion relevante es:

```math
w_k^{dem}\in W(C_k),
\qquad
W(C_k)=\bigoplus_{i@h\in C_k} A_{kh}U_i.
```

Por eso SP3 separa:

| Capa | Ejemplos | Lectura |
|---|---|---|
| Motor dinamico | Replicator, Smith, BNN, CBBA | Como se actualizan preferencias o bids |
| Senal fisica | `wrench_deficit`, `delta_rho`, `support_dual` | Que compra la carga |
| Clearing | slots, conflictos, pares complementarios | Como se vuelve asignacion entera |
| Referencia | `wrench_oracle` | Cota superior combinatoria |

**Metodos SP3 recomendados:**

| ID | Familia | Rol metodologico |
|---|---|
| `wrench_oracle` | reference | Busqueda exacta por slots/subconjuntos con factibilidad wrench estricta; no es propuesta |
| `oracle_scalar_assignment` | reference | Referencia escalar para medir falsos positivos |
| `hungarian_slots` | classic centralized | Coste robot-slot, ciego a wrench |
| `capacity_greedy_slots` | classic decentralized | Capacidad escalar, ignora geometria |
| `cbba_slots` | SOTA proxy | Subasta por bids wrench/slot |
| `replicator_wrench_deficit` | model-based baseline | Mismo payoff wrench con motor replicator |
| `bnn_wrench_deficit` | model-based baseline | Mismo payoff wrench con exceso BNN |
| `smith_wrench_deficit` | proposed | Propuesta principal Smith-QR-WD: deficit `-rho`/residual wrench |
| `smith_wrench_marginal` | proposed ablation | Valora `Delta rho`; prueba si el marginal basta bajo complementariedad |
| `support_dual_wrench_market` | proposed | Heuristica residual-support: precio por direccion de residual wrench normalizado |
| `smith_wrench_marginal_guarded` | proposed repair | Marginal wrench + guardia local que elimina falsos positivos si mejora el score |
| `support_dual_wrench_market_guarded` | proposed repair | Mercado dual wrench + guardia local anti-asignacion fisicamente invalida |
| `smith_wrench_pairs_guarded` | proposed repair | Repair por pares complementarios para capturar torque que un robot aislado no puede producir |

**Implementacion trazable:** SP3 vive en `src/viu_mrob_tfm/sp3/`. `scenario.py` define robots, cargas, slots de contacto, offsets, direcciones admisibles y demandas `w_dem=[F_x,F_y,\tau_z]`. `methods.py` contiene `SP3Assignment`, `labels`, `slot_labels`, oraculos, greedy, CBBA, Smith, Replicator, BNN y mercado dual. `metrics.py` evalua factibilidad escalar, factibilidad wrench, falsos positivos, precision, cobertura y residuales. `visualization.py` genera snapshots/MP4 con slots, flechas de fuerza y torque. `pose_dynamics.py` implementa la validacion Euler-Lagrange/Hamiltoniana. `runner.py` ensambla Monte Carlo, hipotesis, tablas, ranking y auditoria teorica.

El contrato global `Assignment` no se modifica: SP3 usa un contrato local porque necesita representar `robot -> carga -> slot`. Cada columna wrench se calcula como:

```math
g_{ih} = [d_x,\ d_y,\ r_x d_y-r_y d_x]^T,
\qquad
\min_{0 \le \lambda \le f^{max}}\|Q(G_C\lambda-w^{dem})\|_2.
```

Los IDs nuevos conviven con los legacy (`oracle_wrench_assignment`, `greedy_capacity`, `cbba_wrench_score`, `smith_qr_wrench`) para no romper comparabilidad historica. Los smoke/diag antiguos quedaron archivados fuera de `results/sp*`; el Monte Carlo estadistico defendible es `results/sp3/SP3_MC_wrench_comparison_high_power`, mientras `SP3_MC_wrench_comparison_methodology_v3` queda como corrida compacta con videos y trazabilidad de la revision metodologica D1.

**Metricas SP3 corregidas:** ademas de `wrench_feasible_rate`, `false_positive_rate`, `false_positive_given_scalar_rate`, `wrench_residual_norm`, `max_wrench_residual_norm`, `wrench_margin`, `torque_error_nm`, `force_error_n`, `slot_coverage_ratio`, `complementarity_gain`, `travel_distance_m`, `energy_proxy_wh`, `communication_messages`, `runtime_ms` y `optimality_gap_vs_wrench_oracle`, SP3 v3 reporta metricas anti-sesgo:

| Metrica | Lectura |
|---|---|
| `feasible_available_loads` | cargas fisicamente servibles por el oracle wrench estricto |
| `feasible_coverage` / `relative_feasibility` | cargas fisicamente servidas por el metodo divididas por las servibles por el oracle |
| `precision_given_assigned` | proporcion de cargas asignadas que son wrench-feasible |
| `fp_given_assigned` | proporcion de cargas asignadas que son fisicamente invalidas |
| `wrench_residual_feasible_available` | residual medio solo sobre cargas que el oracle puede servir |

Esta separacion evita dos errores: premiar un metodo por abstenerse y comparar residual bruto en mundos donde parte de la demanda es fisicamente imposible.

**Revision metodologica SP3 guarded:** la mejora actual anade reparacion local en espacio wrench sin tocar el contrato global `Assignment`. `smith_wrench_marginal_guarded` y `support_dual_wrench_market_guarded` solo mantienen cargas si el residual wrench cumple tolerancia o si conservarlas mejora el score honesto; `smith_wrench_pairs_guarded` prueba pares de AMR para capturar complementariedad de torque. Esto ataca el punto cientificamente peligroso de SP3: una asignacion puede ser escalarmente suficiente y fisicamente falsa.

**Hipotesis SP3 revisadas:**

| ID | Hipotesis |
|---|---|
| H3.1 | Los criterios escalares producen falsos positivos cuando hay demanda rotacional/direccional |
| H3.2 | `smith_wrench_deficit` reduce residual condicionado a cargas factibles frente a `capacity_greedy_slots` |
| H3.3 | `support_dual_wrench_market` reduce asignaciones fisicamente invalidas frente a baselines de slots |
| H3.4 | `support_dual_wrench_market` reduce gap frente a CBBA |
| H3.5 | Cambiar motor con el mismo payoff wrench separa aporte del payoff y aporte de Smith |

**Resultado SP3 high-power:** `SP3_MC_wrench_comparison_high_power` ejecuta 6 escenarios, 334 seeds, 10 metodos y 20.040 runs; produce figuras principales y `theory_audit.json` con 38.076 checks, 0 fallos. El grid queda ligeramente por encima de 20.000 porque mantener los 6 escenarios y 10 metodos exige un producto entero escenario-seed-metodo. El gate `G3_no_abstention_gaming` hace 18.036 comparaciones por mundo contra el oracle y pasa sin violaciones. Los MP4 representativos siguen en el run compacto `SP3_MC_wrench_comparison_methodology_v3` y en la suite pose-dinamica.

| Rank | Metodo | Coverage | Precision | FP assigned | Gap | Runtime |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `wrench_oracle` | 1.000 | 1.000 | 0.000 | 0.000 | 112.80 ms |
| 2 | `smith_wrench_marginal` | 1.000 | 0.500 | 0.500 | 0.092 | 22.89 ms |
| 3 | `replicator_wrench_deficit` | 1.000 | 0.500 | 0.500 | 0.092 | 25.12 ms |
| 4 | `bnn_wrench_deficit` | 1.000 | 0.500 | 0.500 | 0.092 | 25.15 ms |
| 5 | `smith_wrench_deficit` | 1.000 | 0.500 | 0.500 | 0.092 | 25.11 ms |
| 6 | `cbba_slots` | 1.000 | 0.500 | 0.500 | 0.093 | 22.75 ms |
| 7 | `hungarian_slots` | 1.000 | 0.500 | 0.500 | 0.093 | 0.07 ms |
| 8 | `oracle_scalar_assignment` | 1.000 | 0.500 | 0.500 | 0.093 | 18.56 ms |
| 9 | `support_dual_wrench_market` | 1.000 | 0.500 | 0.500 | 0.094 | 7.48 ms |
| 10 | `capacity_greedy_slots` | 1.000 | 0.500 | 0.500 | 0.100 | 0.22 ms |

La lectura corregida es mas estricta: `wrench_oracle` sirve todas las cargas fisicamente servibles y se abstiene correctamente en las no factibles; por eso queda con precision 1.0 y `fp_given_assigned=0.0`. Los demas metodos cubren las cargas posibles, pero todavia asignan tambien cargas fisicamente imposibles en la mitad de los mundos, lo que aparece como `fp_given_assigned=0.5`. H3_HP_1 se confirma con mucha potencia: el criterio escalar genera falsos positivos bajo demanda rotacional/direccional (`effect=0.500`, `p_Holm=8.47e-198`). H3_HP_2, H3_HP_3 y H3_HP_4 no se confirman: las mejoras de residual, falsos positivos asignados y gap de las variantes propuestas frente a los baselines comparados no son estadisticamente defendibles en esta matriz. H3_HP_5 si se sostiene: existen diferencias globales entre metodos en gap wrench (`effect=0.117`, `p_Holm=0`). Esto es cientificamente mejor: SP3 demuestra la necesidad del criterio wrench, pero no sobrevende todavia una variante propuesta como dominante.

**Artefactos SP3 existentes:** el Monte Carlo estadistico principal esta en `results/sp3/SP3_MC_wrench_comparison_high_power/report.md`, `tables/runs.csv`, `tables/summary.csv`, `tables/performance_ranking.csv`, `tables/load_status.csv`, `tables/hypothesis_results.csv`, figuras y `theory_audit.json`. Los videos representativos y figuras de inspeccion visual se conservan en `results/sp3/SP3_MC_wrench_comparison_methodology_v3` y la validacion dinamica multi-caso/multi-metodo esta en `results/sp3/SP3_POSE_suite_euler_lagrange_transport`, con tablas estandarizadas `runs.csv`, `summary.csv`, `performance_ranking.csv`, `hypothesis_results.csv` y `theory_checks.csv`.

**Experimento dinamico SP3 Euler-Lagrange / Hamiltoniano:** se usa `configs/experiments/sp3/SP3_POSE_suite_euler_lagrange_transport.yaml` como validacion visual y fisica complementaria. Primero se reclutan AMR a slots, luego se simula una carga rigida planar con:

```math
q=[x,y,\theta], \quad M\ddot q + D\dot q = G(q)\lambda,\quad 0 \le \lambda_i \le f_i^{max}.
```

El control vectorial usa un wrench deseado de pose y proyecta fuerzas acotadas por robot sobre `G(q)`. El diagnostico Hamiltoniano es:

```math
H(q,\dot q)=\frac{1}{2}\dot q^T M\dot q + V(q).
```

Resultado reproducible en `results/sp3/SP3_POSE_suite_euler_lagrange_transport`: 18 casos metodo-escenario, 18 MP4, tablas estandarizadas, cobertura de slots, error final de pose, torque, caida Hamiltoniana y `failed_checks=0`. Los MP4 muestran reclutamiento, contacto, flechas de fuerza, arco de torque, movimiento y giro desde pose inicial hasta pose objetivo.

**Suite dinamica SP3 multi-metodo:** se anade `configs/experiments/sp3/SP3_POSE_suite_euler_lagrange_transport.yaml` para generar ejemplos comparables de movimiento/giro de carga en tres regimenes:

| Caso | Regimen | Movimiento | Objetivo |
|---|---|---|---|
| `overactuated_push_more_robots_than_loads` | mas AMR que cargas | push con slot frontal de drag/freno | demostrar movimiento y orientacion alcanzable con redundancia |
| `balanced_push_drag_equal_robots_loads` | AMR y cargas balanceados | push/drag | mostrar sensibilidad a cobertura de slots |
| `scarce_heavy_cargo_fewer_robots_than_loads` | menos AMR que cargas | cargo pesado push/drag | exponer degradacion por escasez |

La suite compara `wrench_oracle`, `hungarian_slots`, `capacity_greedy_slots`, `cbba_slots`, `smith_wrench_deficit` y `support_dual_wrench_market`. Produce 18 corridas, 18 MP4, 18 snapshots, `tables/pose_runs.csv`, trayectorias por corrida, `figures/sp3_pose_transport_suite_performance.png` y `theory_audit.json` con 18 checks y 0 fallos. La tasa de llegada pose es `0.611`: no se interpreta como ranking estadistico, sino como evidencia visual/controlada de que el modelo `M qdd + D qd = G(q)lambda` distingue asignaciones con slots suficientes de asignaciones incompletas o mal orientadas.

La suite usa `complete_uncovered_slots=True` para ejemplos dinamicos: si el allocator deja slots objetivo sin cubrir, el demo puede llenar slots con AMR idle para visualizar el transporte fisico. Esto debe declararse claramente: el benchmark honesto de asignacion sigue siendo `SP3_MC_wrench_comparison_high_power`; la suite pose es una prueba visual/fisica complementaria, no una prueba de superioridad de asignacion.

### SP4 - Movimiento, llegada y coste fisico

**Pregunta:** Una vez asignados a una carga o slot, los AMR pueden llegar a posiciones fisicas utiles con coste razonable y sin colisiones?

**Estado:** SP4 ya existe como pipeline v1 en `src/viu_mrob_tfm/sp4`. Es deliberadamente post-asignacion: no reabre la pregunta de que robot va a que carga, sino que recibe un target por AMR y evalua el movimiento planar hasta ese target. El modelo es cinematica single-integrator saturada con radio de robot, obstaculos circulares, horizonte finito y comunicacion local. No se presenta como MAPF optimo, ni como control de contacto/manipulacion.

**Implementacion trazable:** entry point `viu-run-sp4`, script `scripts/run_sp4_experiment.py`, configs `configs/experiments/sp4/SP4_DEBUG_smoke.yaml`, `configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml` y `configs/experiments/sp4/SP4_MC_motion_comparison.yaml` para videos compactos, tests en `tests/test_sp4_pipeline.py`.

El flujo SP4 es:

```text
SP4MotionScenarioParams
  -> SP4MotionScenario
  -> iter_sp4_problems
  -> make_sp4_policy(method_id)
  -> simulate_motion
  -> evaluate_motion / SP4Metrics
  -> report + figures + MP4 + theory_audit
```

**Escenarios SP4:**

| Escenario | Que mide |
|---|---|
| `open_field_arrival` | caso degenerado sin obstaculos; llegada simple |
| `crossing_traffic` | conflictos entre AMR con trayectorias cruzadas |
| `narrow_passage` | cuello de botella y congestion |
| `cluttered_warehouse` | obstaculos tipo almacen |
| `communication_limited` | politica local con radio finito |
| `long_distance_energy` | coste de trayecto largo y energia |

**Metodos SP4 comparados:**

| ID | Familia | Rol |
|---|---|---|
| `direct_to_target` | classic decentralized | baseline directo, rapido pero inseguro |
| `priority_yield` | classic centralized | prioridad/espera, baseline clasico |
| `apf_obstacle_avoidance` | classic decentralized | campo potencial clasico |
| `velocity_obstacle_proxy` | SOTA proxy decentralized | aproximacion de obstacle velocity |
| `cbf_safety_filter` | SOTA/model-based centralized | filtro CBF-QP proxy sobre velocidad |
| `smith_motion_field` | proposed decentralized | campo Smith-QR con precio de congestion |
| `replicator_motion_field` | proposed decentralized | campo poblacional replicator con presion de objetivo/congestion |
| `logit_motion_field` | proposed decentralized | seleccion suave tipo logit para evitar cambios bruscos de preferencia |
| `bnn_motion_field` | proposed decentralized | Brown/BNN con exceso positivo y respuesta mas conservadora ante congestion |
| `primal_dual_motion_field` | proposed decentralized | campo primal-dual con precios de seguridad/distancia |
| `pid_safety_motion` | proposed decentralized_local | regulador PID de error de llegada con filtro local de seguridad |
| `tensor_flow_motion_field` | proposed decentralized | flujo vectorial suave con acoplamiento tensorial de objetivo, obstaculos y vecinos |
| `explicit_vgne_cbf_motion` | proposed decentralized | ley explicita AMR con punto de mano, CBF cerrado y tracking de velocidad en SP4 |
| `energy_aware_smith_motion` | proposed decentralized | variante Smith con modulacion energetica |
| `reference_time_expanded_cbf` | reference centralized | referencia segura heuristica; no es oracle MAPF exacto |

**Metricas SP4:** `arrival_success_rate`, `timeout_rate`, `mean_arrival_time_s`, `max_arrival_time_s`, `travel_distance_m`, `path_efficiency_ratio`, `energy_proxy_wh`, `collision_count`, `collision_rate`, `safety_violation_count`, `min_robot_clearance_m`, `min_obstacle_clearance_m`, `congestion_delay_s`, `communication_messages`, `runtime_ms`, `score_value` y `performance_gap_vs_reference`. La columna legacy `optimality_gap_vs_reference` se conserva solo como alias de compatibilidad; no debe leerse como prueba de optimalidad global.

**Revision metodologica SP4 no-Smith:** el smoke y la fabrica de politicas ya incluyen replicator, logit, BNN/Brown, primal-dual, PID y tensor-flow. En SP4 estas politicas se leen como campos de movimiento distribuidos comparables, no como solucion MAPF optima. El objetivo cientifico es aislar trade-offs entre llegada, seguridad, energia, mensajes y suavidad de trayectoria.

**Resultado SP4 high-power:** `results/sp4/SP4_MC_motion_comparison_high_power` ejecuta 6 escenarios, 223 seeds, 15 metodos y 20.070 rollouts; genera figuras principales, tablas y `theory_audit.json` con 21.408 checks, 0 fallos. El grid queda ligeramente por encima de 20.000 porque mantener 6 escenarios y 15 metodos exige un producto entero escenario-seed-metodo. El gate principal verifica que la referencia CBF segura reduce la tasa de colision pareada frente a `direct_to_target` en agregado (`mean_reference_minus_direct_collision_rate = -0.03925`). Hay 9 outliers individuales documentados en el audit, coherentes con una referencia heuristica y no un oracle exacto. El run compacto `SP4_MC_motion_comparison` se conserva para MP4 representativos.

Ranking global SP4:

| Rank | Metodo | Arrival | Collision | Timeout | Time | Energy | Gap |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `apf_obstacle_avoidance` | 1.000 | 0.0468 | 0.000 | 23.85 s | 791.57 Wh | 0.097 |
| 2 | `direct_to_target` | 1.000 | 0.0496 | 0.000 | 21.86 s | 788.78 Wh | 0.101 |
| 3 | `velocity_obstacle_proxy` | 1.000 | 0.0514 | 0.000 | 24.35 s | 790.58 Wh | 0.115 |
| 4 | `replicator_motion_field` | 1.000 | 0.0535 | 0.000 | 23.80 s | 789.81 Wh | 0.121 |
| 5 | `logit_motion_field` | 1.000 | 0.0539 | 0.000 | 24.90 s | 790.16 Wh | 0.125 |
| 6 | `explicit_vgne_cbf_motion` | 1.000 | 0.0546 | 0.000 | 24.30 s | 789.94 Wh | 0.126 |
| 7 | `reference_time_expanded_cbf` | 0.921 | 0.0104 | 0.079 | 26.49 s | 918.80 Wh | 0.000 |
| 8 | `cbf_safety_filter` | 0.918 | 0.0115 | 0.082 | 26.80 s | 915.12 Wh | 0.015 |
| 9 | `smith_motion_field` | 0.887 | 0.0124 | 0.113 | 27.14 s | 930.83 Wh | 0.028 |

La lectura correcta no es "el metodo mas rapido gana". SP4 muestra el trade-off central: los metodos directos llegan siempre y consumen menos, pero chocan mucho mas; los metodos CBF/Smith/tensor/primal-dual reducen colisiones a costa de tiempo, timeout y coste computacional. Las hipotesis high-power H4_HP_1, H4_HP_2 y H4_HP_3 se sostienen: referencia, CBF y tensor reducen colision frente a direct (`p_Holm=2.52e-183`, `8.88e-183` y `1.41e-183`). La hipotesis energetica H4_HP_4 no se confirma (`p_Holm=0.9999998`): la variante energy-aware no demuestra ahorro estadistico frente a CBF bajo este proxy. Las diferencias globales entre metodos en gap si son fuertes (`p_Holm=0`, efecto `0.369`). El runner actualizado reporta, para SP1-SP5, `p_value_raw`, `p_value_holm`, decision `reject_holm`, IC bootstrap 95% y tamano de efecto; la defensa debe citar la decision corregida por Holm.

**Suplemento SP4 de ley explicita:** `results/sp4/SP4_MC_explicit_control_law` ejecuta 432 rollouts y 504 checks, con 0 fallos. Se corrigio la regla de ranking SP4 para no premiar politicas inmoviles: ahora maximiza llegada, minimiza timeout y luego evalua colision/gap/coste. `explicit_vgne_cbf_motion` llega en `1.0` de los casos, pero no reduce colision frente a `direct_to_target` (`p_Holm=1.0`) ni gap frente a `cbf_safety_filter` (`p_Holm=1.0`). Por tanto, en SP4 esta ley se reporta como integracion fisica y resultado negativo de tuning, no como metodo ganador.

### SP5 - Transporte cooperativo de carga con formacion

**Pregunta:** una vez reclutada la coalicion, pueden varios AMR recoger una carga, mantenerse en slots/roles, moverla como cuerpo rigido y llevarla a una pose objetivo evitando obstaculos estaticos y otros grupos de robots sin romper formacion?

**Estado:** implementado como pipeline nuevo en `src/viu_mrob_tfm/sp5/`, con entry point `viu-run-sp5`, wrapper `scripts/run_sp5_experiment.py`, configs en `configs/experiments/sp5/` y tests en `tests/test_sp5_pipeline.py`. SP5 no reemplaza SP4: SP4 mide llegada individual post-asignacion; SP5 acopla asignacion de slots, pickup, dinamica Euler-Lagrange reducida del payload, formacion y transporte de pose.

**Modelo:** el payload se representa en plano con

```text
q = [x, y, theta],     M(q) qdd + D qd = G(q) lambda + campos de seguridad/juego
```

Los robots asignados primero se reclutan hacia slots de contacto o anclaje. Despues el payload avanza hacia `target_pose`; la velocidad de la carga se limita por los robots asignados para no crear una ruptura artificial de formacion. Hay dos modos fisicos:

- `push_drag`: contactos unidireccionales en slots de periferia, con fuerzas acotadas y torque por brazo.
- `cargo`: robots tipo carrier bajo/sobre la carga, con fuerza planar equivalente bidireccional y mayor exigencia de formacion.

**Escenarios SP5 v1:**

| Escenario | Que evalua |
|---|---|
| `formation_corridor_push` | Carga rigida con obstaculos de pasillo y necesidad de mantener slots. |
| `cargo_overhead_delivery` | Transporte tipo cargo con anclajes y target pose. |
| `multi_group_crossing_push` | Interferencia de otros grupos de robots moviles. |
| `overactuated_push_drag` | Mas robots que los estrictamente necesarios. |
| `scarce_cargo_multi_load` | Menos robots que cargas, seleccion y escasez. |
| `monte_carlo` | Mezcla aleatoria de los escenarios anteriores. |

**Metodos implementados:**

| Familia | Metodos SP5 |
|---|---|
| Classic centralized | `classic_centralized_shortest_push` |
| Classic decentralized | `classic_decentralized_apf_push` |
| SOTA centralized | `sota_centralized_cbf_push`, `sota_centralized_cbf_cargo` |
| SOTA decentralized | `sota_decentralized_vo_push`, `sota_decentralized_vo_cargo` |
| Ours model-based | `ours_primal_dual_wrench_push`, `ours_tensor_game_push`, `ours_explicit_vgne_cbf_push`, `ours_explicit_vgne_cbf_cargo`, `ours_hamiltonian_cargo` |
| Reference | `reference_centralized_mpc_cbf_cargo` |

SP5 reutiliza los allocators SP3 (`hungarian_slots`, `greedy_capacity`, `cbba_wrench_score`, `support_dual_wrench_market_guarded`, `smith_wrench_pairs_guarded`, `wrench_oracle`) para que la seleccion robot-slot no sea ad hoc.

**Metricas principales:** `selected_task_load`, `pickup_success`, `target_reached`, `transport_success`, error final de posicion/orientacion, `formation_integrity_rate`, `formation_broken_rate`, residual wrench, colisiones normalizadas por oportunidad, clearances, energia, distancia, mensajes, runtime y gap frente a referencia. La tasa de colision se normaliza por oportunidades de choque, no por frame, para que sea interpretable en `[0,1]`.

**Resultado high-power actual:** `results/sp5/SP5_MC_cooperative_transport_high_power` ejecuta 6 generadores, 334 seeds, 10 metodos y 20.040 rollouts. Genera tablas MC, ranking, hipotesis, `report.md`, `theory_audit.json` y 6 figuras principales; la corrida compacta `results/sp5/SP5_MC_cooperative_transport` conserva los MP4 largos para inspeccion visual. La auditoria teorica reporta 20.040 checks y 0 fallos. La version corregida trata obstaculos, trafico movil y otras cargas como cuerpos solidos comunes a todos los metodos: AMR y payload se proyectan fuera de discos estaticos/moviles y fuera de otros payloads despues de cada paso de integracion, y tambien se repara la factibilidad inicial. El fix mas reciente reemplaza la proyeccion radial aproximada por una proyeccion rectangulo-circulo consistente con la metrica de auditoria y una recuperacion local determinista cuando dos restricciones ciclan. La tolerancia de pose se mantiene estricta (`0.20 m` y `5 deg`). En high-power no hay colisiones duras (`failed_checks = 0`); hay 698 warnings de margen de seguridad, todos con `hard_clearance_valid=True`, que se mantienen como `safety_violation_count` y penalizacion de score, no se esconden como exito perfecto. La lectura metodologica importante es que ningun metodo gana atravesando trafico ni atravesando otras cargas: si no rodea, no conserva formacion o no llega, pierde llegada/score.

Ranking high-power SP5: `reference_centralized_mpc_cbf_cargo` logra `transport_success=1.000` y gap `0.000`; `sota_centralized_cbf_cargo` queda en `0.985`; `sota_decentralized_vo_cargo` en `0.977`; `ours_hamiltonian_cargo` en `0.976` con `target_reached=1.000`, colision `0.0` y gap `0.031`. Los metodos push/drag quedan muy por debajo en exito de transporte, lo que refuerza la lectura de que el modo de manipulacion y la factibilidad de slots importan mas que solo llegar al entorno de la carga. H5_1 y H5_4 se confirman (`p_Holm=0`), mientras H5_2 y H5_3 no se confirman; por tanto no se debe vender la variante tensor-push como superior en esta configuracion.

**Suplemento SP5 de ley explicita:** `results/sp5/SP5_MC_explicit_control_law` ejecuta 4 generadores, 12 seeds, 9 metodos, 432 rollouts y 0 fallos de auditoria. `ours_explicit_vgne_cbf_cargo` queda rank 3 tras `reference_centralized_mpc_cbf_cargo` y `sota_decentralized_vo_cargo`: alcanza `target_reached=1.0`, `transport_success=0.896`, error final medio `5.5e-09 m`, colision `0.0` y runtime medio `726.8 ms`. Las hipotesis H5E.1 y H5E.2 se confirman: mejora target frente a `classic_decentralized_apf_push` (`p_Holm=4.26e-12`) y reduce error final frente a `sota_decentralized_vo_cargo` (`p_Holm=1.07e-14`). La hipotesis H5E.3 no se confirma: `ours_explicit_vgne_cbf_push` no reduce residual wrench frente a `ours_tensor_game_push` (`p_Holm=1.0`). Lectura: la ley explicita encaja mejor con cargo/caging rigido que con push/drag unidireccional en esta implementacion.

**Lectura correcta:** SP5 v1 no prueba control industrial completo ni contacto/friccion real. Si demuestra algo defendible: al pasar de llegada individual a transporte cooperativo de payload, el ranking cambia; no basta evadir obstaculos con robots individuales, hay que medir pose del objeto, formacion, slots, wrench residual, colisiones con otros grupos y coste de recursos. La ruta port-Hamiltonian + CBF-QP + Coppelia/ROS queda como extension doctoral, no como evidencia actual de SP5.

### SP6 - Robustez operativa: fallos, bateria, obstaculos e inviabilidad

**Pregunta:** que ocurre cuando cambia el sistema durante la ejecucion: cae el radio de comunicacion, falla un AMR, se agota una bateria, aparece un obstaculo, una carga se vuelve inviable o la informacion llega con retraso?

**Estado:** implementado como pipeline nuevo en `src/viu_mrob_tfm/sp6/`, con entry point `viu-run-sp6`, wrapper `scripts/run_sp6_experiment.py`, configs en `configs/experiments/sp6/`, tests en `tests/test_sp6_pipeline.py` y artefactos high-power en `results/sp6/SP6_MC_robustness_comparison_high_power`. SP6 no sustituye SP4/SP5: toma asignacion y movimiento simplificado con slots destino para medir recuperacion operativa post-evento.

**Escenarios SP6 v1:**

| Escenario | Que evalua |
|---|---|
| `communication_radius_decay` | Degradacion de radio y coste de comunicacion local. |
| `robot_dropout_mid_task` | Fallo fisico de AMR y reconfiguracion de coalicion. |
| `battery_depletion_reallocation` | Robot que queda por debajo de reserva y debe ser retirado. |
| `blocked_corridor_recovery` | Obstaculo dinamico que bloquea una zona durante la ejecucion. |
| `infeasible_load_detection` | Carga que despues del evento requiere mas capacidad que la flota disponible. |
| `delayed_information_consensus` | Evento real con observacion retardada para metodos descentralizados. |
| `multi_load_priority_shift` | Cambio de prioridad entre multiples cargas factibles. |

**Metodos implementados SP6:**

| Familia | Metodos |
|---|---|
| Classic centralized | `classic_centralized_replan` |
| Classic decentralized | `classic_decentralized_greedy_recovery` |
| SOTA/proxy | `cbba_recovery`, `cbf_recovery` |
| Ours/model-based | `replicator_repair_recovery`, `smith_qr_recovery`, `primal_dual_recovery`, `tensor_flow_recovery`, `ours_guarded_wrench_market_recovery` |
| Reference | `reference_resilient_oracle` como recuperacion centralizada resiliente, no como oracle combinatorio exacto |

**Metricas principales:** `recovery_success`, `task_completion_rate`, `lost_load_rate`, `recovery_time_s`, `infeasible_load_detection_rate`, `post_event_wrench_feasible_rate`, `reassignment_count`, `final_active_robot_rate`, `battery_margin_final`, `communication_coverage_ratio`, `communication_messages`, `collision_rate`, clearances, energia, runtime y `performance_gap_vs_reference`.

**Resultado high-power actual:** `results/sp6/SP6_MC_robustness_comparison_high_power` ejecuta 8 generadores, 250 seeds, 10 metodos y 20.000 rollouts. Genera tablas por corrida/robot/carga/trayectoria, ranking, hipotesis, `report.md`, `theory_audit.json` y 6 figuras agregadas; la corrida compacta `results/sp6/SP6_MC_robustness_comparison` conserva los MP4 largos de recuperacion. La auditoria reporta 20.000 checks y 0 fallos. La revision visual y la corrida grande detectaron fallos metodologicos previos: coaliciones reasignadas sin memoria, snaps artificiales de carga completada al target, y una proyeccion de payload distinta a la metrica de clearance. La version corregida introduce persistencia de coalicion durante la entrega, evalua factibilidad justo tras el evento, proyecta AMR-AMR desde el estado inicial y en cada paso, proyecta carga-carga/carga-obstaculo con la misma geometria que audita, y cuando una carga se completa congela/proyecta la pose fisica alcanzada en vez de teletransportarla al target. La lectura metodologica importante es que SP6 puede mostrar near-misses y perdida de completion bajo eventos duros, pero no debe mostrar cargas atravesandose ni atravesando obstaculos.

Ranking high-power SP6: `ours_guarded_wrench_market_recovery` queda primero por `task_completion_rate=0.712`, `lost_load_rate=0.288` y gap `0.0108`; `primal_dual_recovery` queda en `0.710`; `reference_resilient_oracle` en `0.709`; `smith_qr_recovery` en `0.707`. H6.1 se confirma: nuestra recuperacion reduce perdida de carga frente a greedy (`effect=-0.0227`, `p_Holm=2.55e-05`). H6.2 no se confirma frente a Smith en completion (`p_Holm=0.196`). H6.3 y H6.4 se confirman con margen fuerte: reduce gap frente a CBBA (`effect=-0.0658`, `p_Holm=2.06e-92`) y hay diferencias globales entre familias (`p_Holm=7.19e-160`).

**Suplemento SP6 de ley explicita:** `results/sp6/SP6_MC_explicit_control_law` ejecuta 5 generadores, 12 seeds, 6 metodos, 360 rollouts y 0 fallos de auditoria. La ley explicita se usa para generar el wrench requerido en `tensor_flow_recovery`, `ours_guarded_wrench_market_recovery` y `reference_resilient_oracle`. `ours_guarded_wrench_market_recovery` queda con `task_completion_rate=0.572`, `lost_load_rate=0.428`, residual medio `0.903` y colision `0.0`. Las hipotesis H6E.1 y H6E.2 no se confirman: no hay mejora estadisticamente significativa en lost-load frente a greedy (`p_Holm=0.639`) ni en completion frente a Smith (`p_Holm=0.639`). H6E.3 si detecta diferencias familiares de score (`p_Holm=0.00199`). Lectura: la ley explicita mejora la trazabilidad fisica del recovery, pero SP6 exige mas tuning/reasignacion para demostrar superioridad operacional.

**Lectura correcta:** SP6 muestra robustez operacional de asignacion/reparacion y movimiento a slots, no una prueba de control industrial bajo POMDP completo. La contribucion defendible es la metodologia: separar evento fisico, observacion retrasada, carga inviable, recuperacion de coalicion, coste de comunicacion y seguridad, con el mismo mundo para todos los metodos.

### SP7 - Comunicacion, sensores y conectividad temporal

**Pregunta:** La coalicion sigue conectada y percibe obstaculos mientras varios AMR transportan cargas entre otros grupos de robots?

**Estado actual:** SP7 esta implementado como benchmark temporal de red sobre mundos SP5. Cada frame construye un grafo robot-robot por radio de comunicacion, aplica packet loss, burst drops, delays, jitter y caidas intermitentes, y mide si la coalicion queda conectada directamente, por relay multi-hop o por conectividad temporal en una ventana reciente. En paralelo mide deteccion de obstaculos estaticos y grupos moviles con alcance, falsos negativos y ruido de sensor.

**Escenarios:** `radius_sweep_balanced_push`, `multi_group_obstacle_crossing`, `cargo_sensor_degradation`, `over_robot_relay`, `under_robot_multi_load` y `monte_carlo`.

**Metodos:** `classic_centralized_global_mpc`, `classic_decentralized_sensor_apf`, `sota_centralized_cbf_networked`, `sota_decentralized_cbba_relay`, `sota_delay_tolerant_consensus`, `ours_connectivity_wrench_game`, `ours_delay_robust_repair` y `reference_full_communication`.

**Metricas:** `packet_delivery_ratio`, `control_packet_ratio`, `mean_link_delay_s`, `delay_violation_rate`, `coalition_connected_time_ratio`, `temporal_coalition_connected_rate`, `relay_success_rate`, `direct_clique_time_ratio`, `base_connected_time_ratio`, `communication_outage_count`, `longest_outage_s`, `obstacle_detection_rate`, `mobile_group_detection_rate`, `sensor_coverage_rate`, `network_quality_score`, `transport_network_score`, ademas de `transport_success`, `target_reached`, `formation_integrity_rate`, `collision_rate`, energia y runtime heredados de SP5.

**Resultado actual:** `results/sp7/SP7_MC_communication_robustness_high_power` ejecuta 20.176 runs con 6 generadores de escenario, perfiles nominales/estresados mas MC aleatorios, 97 seeds y 8 metodos. La auditoria reporta 20.176 checks y 0 fallos. El MC actual hereda el contrato fisico SP5 y ya no acepta penetraciones entre cargas solidas: el fallo detectado en `under_robot_multi_load_radius_4m_loss_delay_seed9000` se corrigio haciendo que la proyeccion de payload use la misma geometria rectangulo-circulo que la auditoria. Genera figuras de conectividad vs radio, exito bajo estres de red, heatmap packet-loss/delay, relay temporal, sensado vs colision, Pareto calidad-recurso y `paper_figures/` con PDF vectorial.

Ranking high-power SP7: `ours_connectivity_wrench_game` queda primero con `transport_network_score=0.436`, conectividad de coalicion `0.684`, packet delivery `0.825` y transport success `0.142`. `ours_delay_robust_repair` queda segundo con score `0.419` y menor runtime medio. La referencia full-communication queda tercera (`score=0.356`) porque elimina degradacion de comunicacion, pero no resuelve por si sola los cuellos de transporte y formacion. H7.1 confirma que aumentar radio mejora conectividad de coalicion (`effect=0.893`, `p_Holm=0`); H7.2 confirma que nuestra variante de conectividad supera al clasico bajo perfiles severos (`effect=0.189`, `p_Holm=1.36e-80`). H7.3 no se confirma en esta configuracion (`p_Holm=1.0`), por lo que no debe usarse como claim fuerte.

**Lectura correcta:** SP7 no pretende ser un simulador RF industrial. Su valor metodologico es separar comunicacion directa, relay y conectividad temporal, y juzgar si esa red cambiante permite transportar cargas sin romper formacion, sin ignorar obstaculos y sin esconder penetraciones fisicas.

### SP8 - Escalabilidad warehouse e intratabilidad

**Pregunta:** Que ocurre cuando el problema deja de ser pequeno y aparecen cientos o miles de AMR, decenas o cientos de cargas simultaneas, obstaculos fijos/moviles y requisitos wrench/torque? En ese regimen, que metodos centralizados dejan de ser utiles por tiempo/memoria, y que metodos distribuidos o jerarquicos conservan calidad razonable?

**Estado actual:** SP8 esta implementado como pipeline mesoscopico vectorizado en `src/viu_mrob_tfm/sp8`. No simula contacto rigido completo ni RF industrial. Su objetivo es otro: estudiar escala e intratabilidad manteniendo suficientes restricciones fisicas para que la comparacion no sea una asignacion abstracta. Cada mundo tiene AMR, cargas pickup-target, masa, longitud, demanda `[Fx,Fy,tau_z]`, obstaculos estaticos, obstaculos moviles, radio de comunicacion, horizonte, rutas y coste de recursos.

**Implementacion trazable:** `scenario.py` genera `debug`, `scale_ladder`, `fleet_ladder_extended`, `warehouse_large`, `mega_peak` y `obstacle_monte_carlo`. `methods.py` compara `centralized_hungarian_expanded`, `centralized_coalition_oracle`, `centralized_time_expanded_mpc`, `classic_local_greedy`, `cbba_partitioned`, `auction_market_local`, `ours_primal_dual_spatial`, `ours_tensor_quorum_flow`, `ours_wrench_market_hierarchical` y `ours_mean_field_approximation`. Para las escalas grandes, los metodos locales/hierarquicos usan busqueda espacial `cKDTree` y pools candidatos por carga, no una matriz densa AMR-carga que seria inviable en 50k. `metrics.py` evalua factibilidad escalar y wrench con least-squares acotado en mundos pequenos/medios y usa una aproximacion bounded-LS vectorizada en escenarios con miles de cargas para mantener el coste de auditoria bajo control. Evalua completion, throughput, colisiones/riesgo por obstaculos, rutas cruzadas, runtime, memoria, mensajes y gap frente a referencia. `runner.py` escribe reportes, CSVs, hipotesis, auditoria, figuras y MP4 representativos, con muestreo configurable de `load_status.csv` para no crear artefactos inmanejables. Los entry points son `viu-run-sp8` y `scripts/run_sp8_experiment.py`.

**Escenarios SP8:**

| Generador | Escala | Uso |
|---|---:|---|
| `debug` | 64 AMR / 16 cargas | smoke reproducible rapido |
| `scale_ladder` | 64/16, 128/32, 256/64, 512/128 | frontera de crecimiento y timeouts |
| `fleet_ladder_extended` | 5, 10, 25, 50, 100, 250, 500, 1000, 1250, 1500, 2000, 2500, 5000, 7500, 10000, 12500, 15000, 20000, 25000 y 50000 AMR | plot denso de escalabilidad; la carga escala a 25% de la flota, hasta 12.500 cargas |
| `warehouse_large` | 1000/250 y 1200/320 | analogia con warehouse robotizado grande |
| `mega_peak` | 2000/600 y 3000/900 | regimen extremo para estudiar intractabilidad |
| `obstacle_monte_carlo` | 128-512 AMR, obstaculos aleatorios | variacion de posiciones, tamanos y obstaculos moviles |

**Metodos SP8:** Los metodos centralizados sirven como referencias o baselines, pero SP8 declara timeout de forma explicita cuando el tamano vuelve impracticable el oracle de coaliciones o el MPC time-expanded. Esto es metodologicamente importante: no se penaliza a un metodo centralizado por no haber sido optimizado infinitamente; se registra que su complejidad teorica lo saca del regimen operativo. Las propuestas distribuidas/hierarquicas se juzgan por completion, wrench feasibility, throughput, runtime, mensajes y memoria, no solo por score.

**Metricas SP8:** `solved_rate`, `timeout_rate`, `scalar_feasible_rate`, `wrench_feasible_rate`, `false_positive_rate`, `force_error_n_mean`, `torque_error_nm_mean`, `transport_success_rate`, `task_completion_rate`, `throughput_tasks_per_min`, `collision_risk_rate`, `obstacle_intersection_rate`, `mobile_conflict_rate`, `route_crossing_rate`, `mean_travel_distance_m`, `energy_proxy_wh`, `communication_messages`, `messages_per_robot`, `runtime_ms`, `estimated_memory_mb`, `complexity_score` y `performance_gap_vs_reference`.

**Resultado compacto:** `results/sp8/SP8_MC_scalability_warehouse` ejecuta 150 evaluaciones, 10 metodos, 2 generadores, 3 seeds y reporta 0 fallos de auditoria. La mejor posicion global queda para `ours_tensor_quorum_flow` (`task_completion_rate_mean=0.153`, `wrench_feasible_rate_mean=0.189`, runtime medio `32.62 ms`, `timeout_rate=0`). `ours_primal_dual_spatial` (`completion=0.151`, runtime `3.31 ms`) y `ours_wrench_market_hierarchical` (`completion=0.142`, runtime `3.28 ms`) quedan muy cerca. Los baselines `classic_local_greedy`, `auction_market_local`, `cbba_partitioned` y `centralized_hungarian_expanded` quedan por debajo en completion/wrench. `centralized_time_expanded_mpc` declara timeout en `0.600` de las corridas y `centralized_coalition_oracle` en `0.800`.

**Resultado high-power de escala:** `results/sp8/SP8_MC_fleet_ladder_high_power` ejecuta 20.000 evaluaciones: 20 tamanos de flota unicos, 100 seeds por tamano y 10 metodos. La escalera cubre 5, 10, 25, 50, 100, 250, 500, 1000, 1250, 1500, 2000, 2500, 5000, 7500, 10000, 12500, 15000, 20000, 25000 y 50000 AMR, con cargas entre 1 y 12.500. La auditoria reporta 20.000 checks y 0 fallos. La lectura principal ya no depende de un unico mundo por escala: las curvas incluyen bandas IC95 en `paper_figures/paper_sp8_scale_completion_ci.pdf`, y los metodos centralizados exactos/time-expanded quedan penalizados por timeout declarado al crecer mientras las variantes propuestas mantienen completion/wrench por recurso.

**Hipotesis SP8:** En la corrida high-power, H8.1 confirma que el timeout del oracle centralizado aumenta con escala (`effect=0.694`, `p_Holm=4.93e-287`), H8.2 confirma que `ours_wrench_market_hierarchical` supera a `classic_local_greedy` en completion (`effect=0.1008`, `p_Holm=4.18e-300`) y H8.3 confirma que `ours_wrench_market_hierarchical` supera a `centralized_hungarian_expanded` en wrench feasibility (`effect=0.1628`, `p_Holm=6.45e-299`). El ranking global por score queda liderado por `ours_tensor_quorum_flow` (`completion=0.156`, `wrench=0.194`), seguido de `ours_primal_dual_spatial` y `ours_wrench_market_hierarchical`; los centralizados exactos/time-expanded aparecen con timeout alto (`0.60` a `0.80`) y runtime declarado de decenas de segundos por corrida.

**Figuras y videos:** SP8 genera `sp8_runtime_scaling_loglog.png`, `sp8_solved_rate_by_scale.png`, `sp8_throughput_by_scale.png`, `sp8_wrench_success_by_scale.png`, `sp8_quality_complexity_pareto.png` y `sp8_timeout_boundary.png`. Los MP4 no son prueba de exactitud fisica; son inspecciones mesoscopicas que muestran carga pickup-target, AMR asignados, flechas de wrench/torque, obstaculos estaticos y obstaculos moviles para comparar `classic_local_greedy` contra `ours_wrench_market_hierarchical` en el mismo mundo.

**Lectura correcta:** SP8 permite decir que, bajo este modelo mesoscopico, las referencias centralizadas exactas o time-expanded dejan de ser operativas al crecer y que las propuestas distribuidas/hierarquicas son mas competitivas en completion/wrench por recurso. No permite decir que el sistema este listo para Amazon, Cainiao o hardware real. La ruta doctoral queda abierta: mean-field games con error finito-N, GNEP con restricciones wrench/collision, CBF/HOCBF en espacio wrench, port-Hamiltonian contact y GNN/MARL con decoders fisicos.

## 6. Metodologia experimental detallada de SP1 a SP8

La metodologia debe ser incremental, reproducible y falsable. La regla central es que todos los metodos se ejecutan sobre los mismos mundos sinteticos, con seeds congeladas y con separacion estricta entre entrenamiento/tuning y evaluacion final. El resultado de una comparacion no es una sola media, sino un conjunto de CSV, figuras, videos, hipotesis y auditorias que permiten reconstruir que ocurrio en cada corrida.

### 6.1 Pipeline comun

1. Definir generadores de escenarios con seeds fijas.
2. Construir el estado del mundo con AMR, cargas, mapa, baterias, capacidades, posiciones y, si aplica, slots/wrenches.
3. Ejecutar todos los metodos sobre el mismo mundo y registrar `Assignment` o `SP3Assignment`.
4. Evaluar la asignacion con metricas del SP correspondiente.
5. Comparar cada metodo contra referencia oracular o referencia heuristica declarada, segun el SP.
6. Agregar por escenario, metodo, familia, alcance y ownership.
7. Evaluar hipotesis estadisticas pareadas por escenario/seed.
8. Generar tablas, plots de performance, Pareto calidad-recursos y degradacion por radio.
9. Guardar snapshots y videos MP4 con nombres que incluyan SP, escenario, familia, alcance, variante, metodo y seed.
10. Ejecutar auditoria teorica para detectar dominancia imposible, coaliciones invalidas, falsos positivos fisicos o resultados incoherentes.
11. Reportar tambien resultados negativos y limitaciones cuando una hipotesis no se confirma.

Las hipotesis se reportan de forma homogenea: test pareado por bloque comun (`scenario_generator`, `scenario_variant_id`, `seed`), Wilcoxon signed-rank para comparaciones A-vs-B, Friedman/Kendall W para diferencias globales entre varios metodos, `p_value_raw`, correccion Holm-Bonferroni (`p_value_holm`, `reject_holm`), IC bootstrap 95% del efecto medio y tamano de efecto (`cohens_dz` o `kendall_w`). La decision que se defiende es siempre la corregida, no el p-value crudo.

La unidad de evidencia minima para cada SP es:

```text
config YAML
  -> runner reproducible
  -> runs.csv por corrida
  -> summary/performance_ranking/hypothesis_results
  -> figures + videos
  -> theory_audit.json
  -> tests unitarios del pipeline
```

La capa comun de estadistica esta en `src/viu_mrob_tfm/experiment_stats.py` y se valida con `tests/test_experiment_stats.py`. SP1, SP2, SP3, SP4, SP5 y SP6 usan el mismo formato de hipotesis: `p_value_raw`, `p_value_holm`, `reject_holm`, IC95 bootstrap y tamano de efecto cuando aplica. La regeneracion final produjo auditorias limpias en los artefactos oficiales: SP1 con 27.300 checks, SP2 con 20.280 checks, la ablacion SP2 con 9.360 checks, SP3 high-power con 38.076 checks, SP4 high-power con 21.408 checks, SP5 high-power con 20.040 checks, SP6 high-power con 20.000 checks, SP7 high-power con 20.176 checks y SP8 high-power con 20.000 checks, todos con 0 fallos. En SP4 se corrigio el audit para acotar solo tasas/probabilidades y validar `performance_gap_vs_reference` como brecha finita no negativa. Para SP5-SP7, las auditorias actuales incluyen clearances fisicos duros: no se acepta interpenetracion AMR-AMR, AMR-obstaculo, payload-obstaculo, payload-trafico ni payload-payload cuando el escenario lo contiene.

### 6.2 Protocolo SP1

SP1 evalua reclutamiento: decidir que AMR se asignan a que cargas heterogeneas. El experimento final es `configs/experiments/sp1/SP1_MC_recruitment_comparison.yaml`. Usa 100 seeds finales (`2000`-`2099`) y cuatro generadores: `under_demand`, `balanced_demand`, `over_demand` y `monte_carlo`. Los checkpoints data-driven y parametros model-based se congelan antes del Monte Carlo.

El flujo SP1 es:

```text
SP1RecruitmentScenarioParams
  -> SP1RecruitmentScenario
  -> iter_sp1_worlds
  -> make_sp1_allocator(method_id)
  -> evaluate_assignment / SP1Metrics
  -> write_report + figures + videos + theory_audit
```

SP1 compara 13 ids en el reporte final si se cuenta `oracle_reference`, agrupados como:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| classic | centralized | baseline | `hungarian_expanded` |
| classic | decentralized | baseline | `greedy_nearest` |
| sota | decentralized | baseline | `cbba` |
| model_based | decentralized | baseline | `replicator_cardinality`, `bnn_cardinality` |
| model_based | decentralized/decentralized_local | proposed | `smith_cardinality`, `primal_dual_cardinality_capacity`, `primal_dual_wrench_market`, `local_primal_dual_wrench_market` |
| model_based | decentralized/decentralized_local | proposed repair | `replicator_cardinality_repair`, `logit_cardinality_repair`, `bnn_cardinality_repair`, `primal_dual_local_repair`, `tensor_quorum_flow_repair` |
| data_driven | decentralized | baseline | `imitation_oracle` |
| data_driven | decentralized | proposed | `mappo_recruitment` |
| model_based_oracle | centralized | reference | `centralized_coalition_milp`, `oracle_reference` |

La evaluacion SP1 debe responder cuatro preguntas:

| Pregunta | Metricas |
|---|---|
| Se reclutan suficientes robots? | `coalition_success_rate`, `served_load_rate`, `demand_satisfaction_ratio` |
| Se evita desperdicio o falta de robots? | `robots_underassigned`, `robots_overassigned`, `priority_regret` |
| Es fisicamente barato llegar a las cargas? | `travel_distance_m`, `estimated_arrival_time_s`, `energy_proxy_wh` |
| Es justo frente a metodos complejos? | `optimality_gap_vs_oracle`, `runtime_ms`, `communication_messages`, parametros y episodios de entrenamiento |

Las hipotesis SP1 no intentan probar que un metodo domina universalmente. Prueban diferencias en gap, ventaja de MAPPO sobre imitation/Hungarian en gap, ventaja de Smith en runtime y ventaja de MAPPO sobre Smith en success. Esta separacion evita mezclar calidad de solucion y coste de recursos.

### 6.3 Protocolo SP2

SP2 evalua capacidad efectiva: decidir que AMR cubren la demanda fisica de cargas con masa/capacidad bajo descuentos por bateria y distancia. El experimento final general es `configs/experiments/sp2/SP2_MC_capacity_comparison.yaml`. Usa 40 seeds finales (`3100`-`3139`) y cinco generadores: `light_mixed`, `balanced_capacity`, `heavy_capacity`, `battery_constrained` y `monte_carlo`. Los data-driven se entrenan con seeds `1200`-`1223`, validan en `2200`-`2209` y testean en `3200`-`3209`; el Monte Carlo final usa seeds disjuntas `3100`-`3139`. Los model-based se tunean con seeds `1300`-`1307` y validan en `2300`-`2305`. La ablacion teorica del payoff marginal usa `configs/experiments/sp2/SP2_MC_marginal_payoff_ablation.yaml`, con las mismas seeds finales y los mismos generadores.

El flujo SP2 es:

```text
SP2CapacityScenarioParams
  -> SP2CapacityScenario
  -> iter_sp2_worlds
  -> physical_effective_capacity_matrix + communication_visibility_matrix
  -> make_sp2_allocator(method_id)
  -> evaluate_assignment / SP2Metrics
  -> write_report + figures + videos + theory_audit
```

SP2 compara 13 ids en el benchmark general y 4 ids adicionales en la ablacion del Teorema 2:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| classic | centralized | baseline | `hungarian_capacity` |
| classic | decentralized | baseline | `greedy_capacity_nearest` |
| sota | decentralized | baseline | `cbba_capacity` |
| model_based | decentralized | baseline | `replicator_capacity`, `bnn_capacity` |
| model_based ablation | decentralized | baseline | `replicator_capacity_plain`, `replicator_capacity_marginal` |
| model_based | decentralized/decentralized_local | proposed | `smith_capacity`, `primal_dual_capacity`, `local_primal_dual_capacity` |
| model_based ablation | decentralized | proposed | `smith_capacity_plain`, `smith_capacity_marginal` |
| model_based | decentralized/decentralized_local | proposed repair | `replicator_capacity_marginal_repair`, `logit_capacity_repair`, `bnn_capacity_repair`, `smith_capacity_marginal_repair`, `primal_dual_capacity_repair`, `pid_capacity_repair` |
| data_driven | decentralized | baseline | `imitation_capacity` |
| data_driven | decentralized | proposed | `neural_capacity_scorer` |
| model_based_oracle | centralized | reference | `centralized_capacity_milp`, `oracle_reference`, `capacity_oracle_reference` |

La evaluacion SP2 debe responder cinco preguntas:

| Pregunta | Metricas |
|---|---|
| Cuantas cargas quedan completamente cubiertas? | `capacity_success_rate` |
| Cuanto se aleja del score oracle y del techo fisico? | `optimality_gap_vs_oracle`, `capacity_gap_vs_capacity_oracle`, `signed_score_delta_vs_oracle` |
| Cuanta capacidad fisica queda cubierta? | `capacity_satisfaction_ratio`, `effective_feasibility_ratio` |
| Cuanto falta, sobra o se dispersa en cargas incompletas? | `under_capacity_kg`, `over_capacity_kg`, `capacity_waste_ratio`, `incomplete_capacity_ratio`, `served_capacity_alignment` |
| Que coste paga el metodo? | `travel_distance_m`, `energy_proxy_wh`, `communication_coverage_ratio`, `communication_messages`, `runtime_ms`, parametros |

SP2 usa dos oraculos porque una sola referencia seria ambigua. `centralized_capacity_milp` optimiza el score operativo: cobertura parcial, carga completa, reward y costes. `capacity_oracle_reference` maximiza el techo de capacidad fisica. Por eso un metodo puede estar cerca del techo de capacidad y aun asi tener peor score si no completa cargas valiosas.

La ablacion plain/marginal congela la matriz `E=[e_ik]` en cada instante de decision. Asi el experimento contrasta exactamente la prediccion del Teorema 2: si se usa `V_k sigma(D_k-S_k)-g_ik`, la estructura potencial no esta garantizada; si se usa `e_ik V_k sigma(D_k-S_k)-g_ik`, el payoff queda alineado con el potencial. El runner escribe esta auditoria en `theory_audit.json` bajo `potential_alignment`.

### 6.4 Protocolo SP3

SP3 evalua factibilidad fisica planar: decidir no solo que AMR se asignan a una carga, sino en que slot/contacto actuan y si la coalicion puede producir el wrench requerido. El experimento estadistico final es `configs/experiments/sp3/SP3_MC_wrench_comparison_high_power.yaml`. Usa seis escenarios deterministas/Monte Carlo (`point_load_degenerate`, `bar_torque_pure`, `one_sided_push`, `off_center_com`, `long_payload_slots`, `slot_saturation`), 334 seeds por escenario y 10 metodos sobre los mismos mundos, para 20.040 corridas. `SP3_MC_wrench_comparison_methodology_v3.yaml` se conserva como corrida compacta con videos.

El flujo SP3 es:

```text
SP3ScenarioParams
  -> SP3Scenario
  -> iter_sp3_worlds
  -> build_wrench_matrix + bounded least-squares
  -> make_sp3_allocator(method_id)
  -> SP3Assignment(labels, slot_labels)
  -> evaluate_sp3_assignment / SP3Metrics
  -> report + figures + videos + theory_audit
```

SP3 compara:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| reference | centralized | reference | `wrench_oracle`, `oracle_scalar_assignment` |
| classic | centralized | baseline | `hungarian_slots` |
| classic | decentralized | baseline | `capacity_greedy_slots` |
| sota proxy | decentralized | baseline | `cbba_slots` |
| model_based | decentralized | baseline | `replicator_wrench_deficit`, `bnn_wrench_deficit` |
| proposed | decentralized | proposed | `smith_wrench_deficit`, `smith_wrench_marginal`, `support_dual_wrench_market` |
| proposed/supplement | decentralized | proposed guarded repair | `smith_wrench_marginal_guarded`, `support_dual_wrench_market_guarded`, `smith_wrench_pairs_guarded` en corridas metodologicas compactas; no forman parte del high-power de 20.040 |

La evaluacion SP3 debe responder cinco preguntas:

| Pregunta | Metricas |
|---|---|
| La asignacion escalar parece suficiente? | `scalar_feasible_rate`, `false_positive_rate`, `false_positive_given_scalar_rate` |
| La coalicion puede producir el wrench? | `wrench_feasible_rate`, `wrench_residual_norm`, `max_wrench_residual_norm`, `wrench_margin` |
| Que parte del error es fuerza y que parte torque? | `force_error_n`, `torque_error_nm`, residual normalizado por `Q` |
| Se ocupan slots fisicamente utiles? | `slot_coverage_ratio`, `precision_given_assigned`, `fp_given_assigned`, `feasible_coverage` |
| Que coste operativo paga el metodo? | `travel_distance_m`, `energy_proxy_wh`, `communication_messages`, `runtime_ms`, `optimality_gap_vs_wrench_oracle` |

La referencia `wrench_oracle` es una cota combinatoria para tamanos pequenos: enumera planes por carga, resuelve least-squares acotado `0 <= lambda_i <= f_i^{max}`, conserva planes no conflictivos por robot/slot y combina planes disjuntos. No es un metodo desplegable. Su funcion es definir que cargas son fisicamente servibles y evitar dos trampas: premiar abstencion y premiar capacidad escalar cuando el torque es imposible.

SP3 incluye un gate metodologico nuevo, `G3_no_abstention_gaming`: un metodo no debe parecer mejor que otro solo por no asignar cargas dificiles. Por eso el reporte separa cobertura de cargas factibles, precision condicionada a cargas asignadas y falsos positivos condicionados. La conclusion actual es deliberadamente sobria: el criterio wrench es necesario y el escalar falla, pero las variantes propuestas todavia no dominan al oracle ni muestran una mejora estadistica fuerte sobre todos los baselines.

El experimento dinamico `configs/experiments/sp3/SP3_POSE_suite_euler_lagrange_transport.yaml` no reemplaza el benchmark de asignacion; lo complementa. Simula reclutamiento a slots, contacto, giro y desplazamiento de una carga rigida planar usando dinamica Euler-Lagrange y diagnostico Hamiltoniano. Sus MP4 sirven para defensa visual y control fisico cualitativo: se observa la masa pasar de pose inicial a pose objetivo con flechas de fuerza y arco de torque.

La extension `configs/experiments/sp3/SP3_POSE_suite_euler_lagrange_transport.yaml` generaliza ese demo a varios metodos y regimenes. El flujo es:

```text
pose case + method id
  -> SP3Problem with target load slots
  -> allocator assignment
  -> optional target-slot completion for visual demo
  -> simulate_pose_transport
  -> pose_runs.csv + per-run trajectory + MP4 + pose_theory_checks
```

Sus metricas son `pose_success`, `final_position_error_m`, `final_orientation_error_deg`, `slot_coverage_ratio`, `hamiltonian_drop`, `mean_residual_norm`, `max_torque_nm`, `assigned_robots`, `video_ok` y `complete_uncovered_slots`. La suite debe citarse como demostracion de dinamica y visualizacion, no como Monte Carlo inferencial.

### 6.5 Protocolo SP4

SP4 evalua movimiento post-asignacion: una vez decidido el target de cada AMR, mide si los robots llegan con seguridad, coste fisico razonable y comunicacion local. El experimento estadistico final es `configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml`. Usa 223 seeds (`5600`-`5822`), seis generadores (`open_field_arrival`, `crossing_traffic`, `narrow_passage`, `cluttered_warehouse`, `communication_limited`, `long_distance_energy`) y 15 metodos sobre los mismos mundos, para 20.070 rollouts. `SP4_MC_motion_comparison.yaml` queda como corrida compacta con videos.

El flujo SP4 es:

```text
SP4MotionScenarioParams
  -> SP4MotionScenario
  -> iter_sp4_problems
  -> make_sp4_policy(method_id)
  -> simulate_motion
  -> evaluate_motion / SP4Metrics
  -> report + figures + videos + theory_audit
```

SP4 compara:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| classic | decentralized | baseline | `direct_to_target`, `apf_obstacle_avoidance` |
| classic | centralized | baseline | `priority_yield` |
| sota | centralized/decentralized | baseline | `cbf_safety_filter`, `velocity_obstacle_proxy` |
| model_based | decentralized | proposed | `smith_motion_field`, `energy_aware_smith_motion` |
| model_based_reference | centralized | reference | `reference_time_expanded_cbf` |

La evaluacion SP4 responde:

| Pregunta | Metricas |
|---|---|
| Llegan los AMR a sus targets? | `arrival_success_rate`, `timeout_rate`, `mean_arrival_time_s`, `max_arrival_time_s` |
| Son trayectorias seguras? | `collision_count`, `collision_rate`, `safety_violation_count`, `min_robot_clearance_m`, `min_obstacle_clearance_m` |
| Que coste fisico pagan? | `travel_distance_m`, `path_efficiency_ratio`, `energy_proxy_wh`, `mean_speed_mps` |
| Que coste operativo/computacional pagan? | `communication_messages`, `congestion_delay_s`, `runtime_ms`, `performance_gap_vs_reference` |

SP4 no se vende como MAPF optimo. La referencia `reference_time_expanded_cbf` es una referencia segura heuristica, no un oracle exacto. Por eso la conclusion correcta es de trade-off: los metodos directos llegan rapido y barato, pero chocan mas; los metodos CBF/Smith reducen colisiones a cambio de tiempo, timeout y coste computacional.

### 6.6 Protocolo SP5

SP5 evalua transporte cooperativo de payload: los AMR deben reclutarse a slots de una carga, completar pickup, mantener formacion y mover una carga rigida planar hasta una pose objetivo evitando obstaculos estaticos, grupos moviles y otras cargas solidas del mundo. El experimento estadistico oficial actual es `configs/experiments/sp5/SP5_MC_cooperative_transport_high_power.yaml`: 6 generadores, 334 seeds (`6200`-`6533`), 10 metodos y 20.040 rollouts con 0 fallos de auditoria. La corrida `configs/experiments/sp5/SP5_MC_cooperative_transport.yaml` queda como run compacto con videos largos.

El flujo SP5 es:

```text
SP5TransportScenarioParams
  -> SP5TransportScenario
  -> SP3 allocator for robot-slot assignment
  -> simulate_transport
  -> Euler-Lagrange reduced payload dynamics
  -> hard clearance projection for AMR, payload, traffic and solid loads
  -> evaluate_transport / SP5Metrics
  -> report + figures + videos + theory_audit
```

SP5 compara:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| classic | centralized/decentralized | baseline | `classic_centralized_shortest_push`, `classic_decentralized_apf_push` |
| sota | centralized/decentralized | baseline | `sota_centralized_cbf_push`, `sota_decentralized_vo_push`, `sota_centralized_cbf_cargo`, `sota_decentralized_vo_cargo` |
| model_based | decentralized | proposed | `ours_primal_dual_wrench_push`, `ours_tensor_game_push`, `ours_hamiltonian_cargo` |
| model_based_reference | centralized | reference | `reference_centralized_mpc_cbf_cargo` |

La evaluacion SP5 responde:

| Pregunta | Metricas |
|---|---|
| Se selecciona la carga correcta y se completa pickup? | `selected_task_load`, `pickup_success`, `pickup_complete_time_s` |
| La carga llega a pose final estricta? | `target_reached`, `transport_success`, `final_position_error_m`, `final_orientation_error_deg`, `completion_time_s` |
| Se preserva formacion y wrench? | `formation_integrity_rate`, `formation_broken_rate`, `mean_wrench_residual_norm`, `max_wrench_residual_norm` |
| Se evita trafico/obstaculos/cargas solidas sin atravesarlos? | `collision_count`, `collision_rate`, `min_mobile_group_clearance_m`, `min_obstacle_clearance_m`, `min_load_clearance_m` |
| Que coste paga el metodo? | `travel_distance_m`, `load_travel_distance_m`, `energy_proxy_wh`, `communication_messages`, `runtime_ms`, `score_value` |

Cambios metodologicos recientes de SP5 que deben quedar declarados:

1. La tolerancia de pose se endurece a `0.20 m` y `5 deg`; antes era visualmente laxa.
2. Los videos duran 44 s y mantienen 10 s de estado final para ver el docking.
3. El trafico movil se modela como barrera geometrica dura: ningun metodo puede atravesar `traffic-a/b`.
4. El horizonte de movimiento del trafico se desacopla del horizonte de simulacion, para que alargar el experimento permita asentamiento sin ralentizar artificialmente los grupos moviles.
5. La proyeccion de clearance se aplica a AMR, payload, obstaculos, trafico movil y otras cargas despues de cada paso de integracion y tambien repara factibilidad inicial.
6. `min_load_clearance_m` significa ahora clearance minimo de la carga transportada frente a cualquier solido relevante de tipo payload/obstaculo/trafico, no solo distancia a obstaculos.
7. La auditoria distingue `hard_clearance_valid` de `safety_margin_valid`: cruzar o colisionar falla; rozar unos milimetros el margen se reporta como seguridad, no como interpenetracion.
8. El ranking SP5 se corrige para ordenar por exito, llegada, colision, `score_value`, formacion, pose, gap, energia, mensajes y runtime.

SP5 no prueba contacto/friccion industrial completo. Su valor es cerrar el salto de SP3/SP4: ya no basta asignar robots ni llegar individualmente; hay que mover el objeto como cuerpo rigido, preservar slots/formacion y respetar barreras.

### 6.7 Protocolo SP6

SP6 evalua robustez operativa: ante un evento exogeno, la coalicion debe reparar asignaciones, retirar AMR no disponibles, detectar cargas inviables y completar las cargas factibles sin esconder costes de comunicacion, bateria, seguridad o runtime. El experimento estadistico oficial actual es `configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml`: 8 generadores, 250 seeds (`7200`-`7449`), 10 metodos y 20.000 rollouts con 0 fallos de auditoria. La corrida `configs/experiments/sp6/SP6_MC_robustness_comparison.yaml` queda como run compacto con videos largos.

El flujo SP6 es:

```text
SP6RobustnessScenarioParams
  -> SP6RobustnessScenario
  -> SP6Problem(world, event, active_obstacles_at, demand_at, communication_radius_at)
  -> make_sp6_policy(method_id)
  -> simulate_recovery
  -> slot targets around each load destination
  -> hard projection for AMR-AMR, AMR-obstacle, load-obstacle and load-load
  -> evaluate_recovery / SP6Metrics
  -> report + figures + videos + theory_audit
```

SP6 compara:

| Familia | Scope | Ownership | Metodos |
|---|---|---|---|
| classic | centralized | baseline | `classic_centralized_replan` |
| classic | decentralized | baseline | `classic_decentralized_greedy_recovery` |
| sota | centralized/decentralized | baseline | `cbf_recovery`, `cbba_recovery` |
| model_based | decentralized | proposed | `replicator_repair_recovery`, `smith_qr_recovery`, `primal_dual_recovery`, `tensor_flow_recovery`, `ours_guarded_wrench_market_recovery` |
| model_based_reference | centralized | reference | `reference_resilient_oracle` como recuperacion centralizada resiliente |

La evaluacion SP6 responde:

| Pregunta | Metricas |
|---|---|
| Se completan las cargas que siguen siendo factibles tras el evento? | `task_completion_rate`, `completed_load_count`, `lost_load_rate`, `recovery_success` |
| Se detectan cargas imposibles en lugar de gastar robots en ellas? | `infeasible_load_count`, `infeasible_load_detection_rate`, `final_unassigned_infeasible` en `load_status.csv` |
| La coalicion final sigue siendo fisicamente plausible? | `post_event_wrench_feasible_rate`, capacidad/fuerza/torque asignados por carga |
| Que paga la recuperacion? | `reassignment_count`, `recovery_time_s`, `travel_distance_m`, `energy_proxy_wh`, `runtime_ms` |
| Que pasa con comunicacion y seguridad? | `communication_coverage_ratio`, `communication_messages`, `collision_rate`, `min_robot_clearance_m`, `min_obstacle_clearance_m`, `min_load_clearance_m` |

Cambios metodologicos importantes de SP6:

1. El evento tiene tiempo fisico y tiempo observado; los metodos descentralizados pueden recibir informacion retrasada.
2. La carga infeasible se evalua como caso negativo correcto: no asignarla puede ser una decision buena si la flota no puede servirla.
3. Los robots asignados no convergen al centro de la carga, sino a slots alrededor del destino; esto evita colisiones artificiales y hace visible la formacion final.
4. La referencia centralizada se etiqueta honestamente como recuperacion resiliente, no como oracle combinatorio exacto.
5. El ranking prioriza exito, completitud, cargas perdidas y gap frente a referencia antes que pequenos cambios de energia o runtime; la colision fisica es una restriccion dura auditada.
6. La asignacion ahora es sticky mientras una carga factible esta en transporte: un replan puede reemplazar robots fallidos o baterias agotadas, pero no debe hacer que toda la coalicion salte de carga en carga antes de entregar.
7. Las cargas se tratan como solidos: no pueden atravesar obstaculos ni otras cargas; los AMR tampoco pueden solaparse entre ellos ni con obstaculos.
8. El `theory_audit` no falla porque un baseline sea malo; falla por estados no finitos, shapes invalidos, rates fuera de rango, velocidad fuera de contrato, bateria invalida o cualquier penetracion fisica detectada por `collision_count`, `min_robot_clearance_m`, `min_obstacle_clearance_m` o `min_load_clearance_m`.

SP6 no prueba robustez industrial completa bajo incertidumbre parcial general. Su valor es cerrar una capa necesaria entre transporte nominal y despliegue: cuando algo falla, el benchmark mide si el sistema repara, comunica, detecta imposibilidad, evita penetraciones fisicas y completa solo aquello que puede completar bajo las restricciones activas.

### 6.8 Fairness de comparacion

La comparacion debe conservar familias, pero no debe fingir que todos los metodos cuestan lo mismo:

| Tipo de coste | SP1 | SP2 | SP3 | SP4 | SP5 | SP6 | SP7 | SP8 |
|---|---|---|---|---|---|---|---|---|
| Coste offline | MAPPO: 768 episodios, 1000 train seeds; imitation: entrenamiento supervisado | Imitation/neural: distillation supervisada; model-based: tuning por YAML | sin aprendizaje en v3; MAPPO/GNN-wrench futuro | sin aprendizaje en v1 | sin aprendizaje en v1; allocators vienen de SP3 | sin aprendizaje en v1; politicas analiticas de recuperacion | sin aprendizaje en v1; perfiles de red/sensado | sin aprendizaje en v1; benchmark de escala y timeouts |
| Parametros | MAPPO actor 4674, imitation 7, model-based 0 | neural 121, imitation 8, model-based 0 | oraculo combinatorio y metodos analiticos; 0 parametros aprendidos | politicas analiticas; 0 parametros aprendidos | politicas analiticas; 0 parametros aprendidos | politicas analiticas; 0 parametros aprendidos | politicas analiticas de comunicacion; 0 parametros aprendidos | reglas/modelos analiticos; 0 parametros aprendidos |
| Coste online | runtime, mensajes, distancia, energia | runtime, mensajes, cobertura de comunicacion, distancia, energia | runtime, mensajes, distancia, energia, conflictos de slot y residual wrench | runtime, mensajes, distancia, energia, colisiones | runtime, mensajes, distancia, energia, formacion, residual wrench, docking | runtime, mensajes, cobertura de comunicacion, reasignaciones, recovery time, energia | paquetes, delay, jitter, outages, sensores, transporte | runtime, memoria, complejidad, mensajes, throughput, energia y timeouts |
| Validez teorica | gap vs oracle de coalicion | gap vs score oracle y gap vs capacity oracle | gap vs wrench oracle, falsos positivos escalares y gate anti-abstencion | gap vs referencia CBF segura, no oracle global | docking estricto, hard clearance con trafico/obstaculos/cargas solidas, comparacion cargo vs push/drag | gap vs referencia resiliente, deteccion de inviabilidad, slots de recuperacion y no-colision dura entre AMR/cargas/obstaculos | conectividad temporal vs directa/relay con transporte SP5 y clearances heredados; no RF industrial | intratabilidad declarada, wrench checks y gap vs referencia; no contacto/hardware |

La frase metodologica correcta es:

> Comparamos calidad de asignacion y coste de obtencion de esa calidad. Un metodo aprendido puede ganar en gap o success, pero debe pagar explicitamente sus parametros, entrenamiento, runtime y dependencia de un decoder o de un oraculo de entrenamiento.

En SP3 v3, SP4 v1, SP5 v1, SP6 v1, SP7 v1 y SP8 v1 no se introduce data-driven training a proposito: primero se aislan la fisica de wrench, movimiento, transporte cooperativo, recuperacion operativa, comunicacion temporal y escalabilidad. Cualquier MAPPO/GNN-wrench futuro debe entrenarse con train/validation/test disjuntos y compararse contra estas bases wrench/motion/transport/recovery/network/scale-aware, no contra un baseline escalar debil.

### 6.9 Artefactos y entry points

Los entry points instalables son `viu-run-sp1`, `viu-run-sp2`, `viu-run-sp3`, `viu-run-sp4`, `viu-run-sp5`, `viu-run-sp6`, `viu-run-sp7` y `viu-run-sp8`, definidos en `pyproject.toml`. Los scripts equivalentes son `scripts/run_sp1_experiment.py` ... `scripts/run_sp8_experiment.py`. Los artefactos principales son:

| SP | Config final | Reporte | Modelos/tuning | Tests |
|---|---|---|---|---|
| SP1 | `configs/experiments/sp1/SP1_MC_recruitment_comparison.yaml` | `results/sp1/SP1_MC_recruitment_comparison/report.md` | `outputs/trained_models/SP1`, `outputs/tuning/SP1` | `tests/test_sp1_pipeline.py` |
| SP2 | `configs/experiments/sp2/SP2_MC_capacity_comparison.yaml` | `results/sp2/SP2_MC_capacity_comparison/report.md` | `outputs/trained_models/SP2`, `outputs/tuning/SP2` | `tests/test_sp2_pipeline.py` |
| SP3 | `configs/experiments/sp3/SP3_MC_wrench_comparison_high_power.yaml`; videos compactos en `SP3_MC_wrench_comparison_methodology_v3.yaml`; pose suite `SP3_POSE_suite_euler_lagrange_transport.yaml` | `results/sp3/SP3_MC_wrench_comparison_high_power/report.md`; videos en `results/sp3/SP3_MC_wrench_comparison_methodology_v3/`; `results/sp3/SP3_POSE_suite_euler_lagrange_transport/report.md` | no aplica en v3/high-power; MAPPO/GNN-wrench queda para anexo/futuro doctoral | `tests/test_sp3_pipeline.py` |
| SP4 | `configs/experiments/sp4/SP4_MC_motion_comparison_high_power.yaml`; videos compactos en `SP4_MC_motion_comparison.yaml`; suplemento `SP4_MC_explicit_control_law.yaml` | `results/sp4/SP4_MC_motion_comparison_high_power/report.md`; videos en `results/sp4/SP4_MC_motion_comparison/`; `results/sp4/SP4_MC_explicit_control_law/report.md` | no aplica en v1/high-power; ley explicita AMR como suplemento model-based cerrado | `tests/test_sp4_pipeline.py`; `tests/test_explicit_amr_control_law.py` |
| SP5 | `configs/experiments/sp5/SP5_MC_cooperative_transport_high_power.yaml`; videos en `SP5_MC_cooperative_transport.yaml`; suplemento `SP5_MC_explicit_control_law.yaml` | `results/sp5/SP5_MC_cooperative_transport_high_power/report.md`; videos en `results/sp5/SP5_MC_cooperative_transport/`; `results/sp5/SP5_MC_explicit_control_law/report.md` | no aplica en v1; usa allocators SP3 y controladores analiticos/ley explicita AMR | `tests/test_sp5_pipeline.py`; `tests/test_explicit_amr_control_law.py` |
| SP6 | `configs/experiments/sp6/SP6_MC_robustness_comparison_high_power.yaml`; videos en `SP6_MC_robustness_comparison.yaml`; suplemento `SP6_MC_explicit_control_law.yaml` | `results/sp6/SP6_MC_robustness_comparison_high_power/report.md`; videos en `results/sp6/SP6_MC_robustness_comparison/`; `results/sp6/SP6_MC_explicit_control_law/report.md` | no aplica en v1; aprendizaje reactivo queda para anexo/futuro doctoral; recovery con wrench requerido explicito | `tests/test_sp6_pipeline.py`; `tests/test_explicit_amr_control_law.py` |
| SP7 | `configs/experiments/sp7/SP7_MC_communication_robustness_high_power.yaml`; stress preparado en `SP7_MC_communication_robustness_full.yaml` | `results/sp7/SP7_MC_communication_robustness_high_power/report.md` | no aplica en v1; comunicacion/sensado analitico | `tests/test_sp7_pipeline.py` |
| SP8 | `configs/experiments/sp8/SP8_MC_fleet_ladder_high_power.yaml`; videos en `SP8_MC_scalability_warehouse.yaml`; full preparado en `SP8_MC_scalability_warehouse_full.yaml` | `results/sp8/SP8_MC_fleet_ladder_high_power/report.md`; videos en `results/sp8/SP8_MC_scalability_warehouse/` | no aplica en v1; escalabilidad/model-based sin entrenamiento | `tests/test_sp8_pipeline.py` |

Configs de extension Wrench-Market Games, todavia pendientes de ejecucion Monte Carlo final:

| SP | Config extension | Uso |
|---|---|---|
| SP1 | `configs/experiments/sp1/SP1_MC_wrench_market_protocol_repair.yaml` | protocol engines + repair entero |
| SP2 | `configs/experiments/sp2/SP2_MC_wrench_market_vector_potential_repair.yaml` | payoff marginal + factorization obstruction + repair |
| SP3 | `configs/experiments/sp3/SP3_MC_wrench_market_protocol_invariance.yaml` | wrench signal + complementarity + engine invariance |
| SP4 | `configs/experiments/sp4/SP4_MC_wrench_market_motion_safety.yaml` | campos seguros post-asignacion |

Para la defensa, los CSV no deben mostrarse completos. Deben convertirse en cuatro figuras: ranking, Pareto calidad-recursos, coste fisico y degradacion por radio de comunicacion.

## 7. Teoria matematica de fondo

### 7.1 Notacion minima

Sea:

- `R = {1,...,N}` el conjunto de AMR.
- `L = {1,...,M}` el conjunto de cargas.
- `q_i in R^2` la posicion del robot `i`.
- `b_i in [0,1]` la bateria normalizada.
- `c_i` la capacidad nominal del robot.
- `D_k` la demanda efectiva de la carga `k`.
- `w_k^{dem} in R^3` el wrench planar requerido por la carga.
- `G(t)` el grafo de comunicacion.
- `C_k subset R` la coalicion asignada a la carga `k`.
- `y_{ik}` la preferencia continua del robot `i` por la carga `k`.
- `z_{ikh}` la decision discreta de robot `i`, carga `k`, slot `h`.

Una asignacion es admisible si:

```math
C_k \cap C_l = \emptyset \quad (k \ne l),
\qquad
\bigcup_k C_k \subseteq R.
```

Una carga queda servida por cardinalidad si:

```math
|C_k| \ge n_k.
```

Pero una carga queda servida fisicamente solo si:

```math
S_k(C_k,q,b,G) \ge D_k
```

y, para transporte con contacto:

```math
r_k(C_k) =
\min_{0 \le \lambda \le \bar f}
\|G_{C_k}\lambda - w_k^{dem}\|_2
\le \epsilon_k.
```

### 7.2 Estructura vector-agregativa Wrench-Market

El marco Wrench-Market Games generaliza SP1-SP6 con un mismo objeto conceptual, aunque su uso formal mas cerrado esta en SP1-SP3 y su extension de movimiento/transporte/recuperacion aparece como campo vectorial en SP4-SP6. Cada AMR `i` aporta a cada carga `k` un vector fijo durante el instante de decision:

```math
E_{ik}\in\mathbb{R}^{d_k},
\qquad
S_k(x)=\sum_i E_{ik}x_{ik}.
```

La carga tiene una utilidad concava `F_k(S_k)`. El payoff correcto no es necesariamente un deficit escalar plano, sino el precio marginal de la contribucion:

```math
p_{ik}(x)
=
\nabla F_k(S_k(x))^T E_{ik}
- g_{ik}.
```

La funcion potencial queda:

```math
\Phi(x)=
\sum_k F_k(S_k(x))
-
\sum_{i,k} g_{ik}x_{ik}.
```

Esta forma explica por que los SP no son problemas separados:

| SP | `E_ik` | `F_k` / precio | Consecuencia |
|---|---|---|---|
| SP1 | capacidad/quorum escalar | deficit de coalicion | reclutamiento por demanda y coste |
| SP2 | capacidad efectiva par-dependiente `e_ik` | precio marginal `e_ik V_k sigma(D_k-S_k)` | el payoff plano falla si `e_ik` no factoriza |
| SP3 | columna wrench esperada | precio vectorial residual `mu_k = V_k(w_k^{dem}-S_k)` | la carga compra fuerza/torque, no robots |
| SP4 | campo vectorial/velocidad deseada | potencial mecanico de llegada/seguridad | movimiento como continuacion del juego |

El resultado conceptual que debe quedar en la memoria: si la senal `p_ik` esta alineada con el potencial, Smith, Brown/BNN y Replicator pertenecen a la misma familia de dinamicas de correlacion positiva. Entonces la calidad de solucion deberia depender mas de la senal fisica que del motor. Esto se prueba empiricamente con la nueva config SP3 de invariancia; antes de ejecutarla debe presentarse como hipotesis falsable, no como resultado cerrado.

### 7.3 Payoff de deficit fisico-economico

La carga debe atraer robots cuando esta subatendida y dejar de atraerlos cuando su coalicion ya es suficiente. Un payoff razonable es:

```math
p_{ik}
=
V_k \sigma(D_k - S_k)
- \alpha d(q_i,q_k)
- \beta E_{ik}
- \gamma \rho_k
- \eta O_k
- \chi B_i.
```

Donde:

- `sigma` suaviza el umbral de demanda.
- `d(q_i,q_k)` penaliza distancia.
- `E_ik` penaliza energia esperada.
- `rho_k` mide congestion local.
- `O_k` mide sobreasignacion.
- `B_i` penaliza bajo margen de bateria.

La idea elegante es que la carga "compra" capacidad marginal, no robots. Un robot lejos, mal orientado o sin bateria tiene menor contribucion efectiva aunque tenga la misma capacidad nominal.

### 7.4 Dinamica de Smith

Smith mueve preferencia desde estrategias de menor payoff a estrategias de mayor payoff:

```math
\dot y_{ik}
=
\sum_{\ell} y_{i\ell}[p_{ik}-p_{i\ell}]_+
-
y_{ik}\sum_{\ell}[p_{i\ell}-p_{ik}]_+.
```

En juegos potenciales, esta dinamica tiende a conjuntos de equilibrio bajo condiciones regulares. En el TFM, Smith se usa como motor interpretable de decision distribuida.

**Punto critico:** Smith puro produce preferencias continuas. El transporte requiere coaliciones enteras. Por eso aparece QR/quorum:

```text
Smith continuo -> ranking local -> clearing entero -> guardias de quorum -> coalicion ejecutable
```

### 7.5 Juegos potenciales

Un juego es potencial si existe `Phi(y)` tal que el incentivo individual coincide con el cambio del potencial:

```math
p_{ik}(y) - p_{i\ell}(y)
=
\Phi(y_{i->k}) - \Phi(y_{i->\ell}).
```

La utilidad de esta lectura es doble:

1. Da una funcion global interpretable aunque las decisiones sean locales.
2. Permite discutir estabilidad y equilibrio sin convertir cada corrida en heuristica.

El TFM debe apoyarse en Monderer y Shapley para juegos potenciales, Sandholm para dinamicas poblacionales, Quijano y Barreiro-Gomez para control distribuido via juegos poblacionales, y Martinez-Piazuelo para dinamicas poblacionales en tiempo discreto.

### 7.6 Generalized Nash seeking

El problema real no es Nash simple, porque los robots comparten restricciones:

```math
\sum_k x_{ik} \le 1,
\qquad
\sum_i c_i x_{ik} \ge D_k,
\qquad
0 \le \lambda_i \le \bar f_i,
\qquad
h_{safe}(q) \ge 0.
```

Esto sugiere un GNEP, generalized Nash equilibrium problem, donde el conjunto factible de un robot depende de las decisiones de los demas. La version doctoral puede formular:

```math
\min_{x_i,u_i,\lambda_i} J_i(x_i,x_{-i},u_i)
\quad
s.t. \quad
g_i(x_i,x_{-i}) \le 0.
```

La solucion moderna podria usar:

- variational inequalities;
- primal-dual dynamics;
- projected gradient;
- operator splitting;
- augmented Lagrangian;
- ADMM distribuido;
- CBF-QP para seguridad.

### 7.7 Mean Field Games (MFG)

Cuando `N` crece, modelar cada robot individual puede volverse caro. MFG reemplaza muchos agentes por una densidad `m(q,t)`. La pregunta doctoral seria:

> Puede el reclutamiento de coaliciones multi-AMR verse como control de una densidad de capacidad que fluye hacia cargas con deficit?

Una formulacion continua ideal tendria:

```math
\partial_t m + \nabla \cdot (m v) = 0,
```

con una funcion de valor `V(q,t)` que satisface una ecuacion Hamilton-Jacobi-Bellman:

```math
-\partial_t V
=
\min_u
\left[
L(q,u,m,D)
+ \nabla V \cdot f(q,u)
\right],
```

y una velocidad inducida:

```math
v(q,t) = f(q,u^*(q,t)).
```

La carga `k` aparece como demanda localizada:

```math
D(q,t) = \sum_k D_k(t)\delta(q-q_k).
```

El acoplamiento MFG ocurre porque el coste de ir a una carga depende de la densidad de otros robots, congestion, ocupacion de la coalicion y deficit residual:

```math
L(q,u,m,D)
=
\frac{1}{2}\|u\|^2
+ c_{cong} m(q,t)
+ c_{def} \sum_k \psi_k(q)(D_k - S_k[m])_+
+ c_{bat}(q,b).
```

Esta extension es potente, pero no debe venderse como resultado cerrado del TFM. Es ruta PhD:

- TFM: finito, discreto, reproducible.
- PhD: limite de campo medio, MFG con cargas puntuales, congestion y capacidad.

### 7.8 Euler-Lagrange y mecanica del robot

Para conectar con robotica fisica, cada AMR puede modelarse por Euler-Lagrange:

```math
M_i(q_i)\ddot q_i + C_i(q_i,\dot q_i)\dot q_i + D_i\dot q_i + g_i(q_i)
=
B_i(q_i)\tau_i + J_i(q_i)^\top f_i.
```

En un AMR diferencial simplificado, la capa cinematica puede bastar:

```math
\dot x_i = v_i \cos\theta_i,
\quad
\dot y_i = v_i \sin\theta_i,
\quad
\dot\theta_i = \omega_i.
```

Pero para cargas fisicas, la capa dinamica importa porque los contactos transfieren fuerza:

```math
w = G_C \lambda.
```

La memoria puede usar cinematica para simulacion principal y dejar Euler-Lagrange como extension de realismo. Lo importante es que el modelo declare la frontera.

### 7.9 Hamiltoniano, pasividad y energia positiva

Una lectura mas elegante para PhD es port-Hamiltonian. Definir energia:

```math
H(q,p) =
\frac{1}{2}p^\top M(q)^{-1}p + U(q).
```

Con `H >= 0`, el sistema se puede expresar como:

```math
\begin{bmatrix}\dot q \\ \dot p\end{bmatrix}
=
\left[
J(q,p)-R(q,p)
\right]\nabla H(q,p)
+ G(q)u,
```

donde:

- `J = -J^T` conserva energia;
- `R = R^T >= 0` disipa energia;
- `G(q)u` inyecta potencia/control.

La tesis doctoral podria decir:

> El reclutamiento decide quien debe aportar potencia, el juego wrench decide como repartirla, y el control port-Hamiltonian garantiza que la interaccion carga-robot no cree energia espuria.

Esto conectaria teoria de juegos con pasividad:

```math
deficit -> payoff -> coalicion -> puerto de potencia -> energia de carga
```

### 7.10 CBF-QP para seguridad

La seguridad no debe quedar como "evitamos colisiones en simulacion". Una extension fuerte usa Control Barrier Functions:

```math
h_{ij}(q) = \|q_i-q_j\|^2 - d_{safe}^2.
```

La condicion:

```math
\dot h_{ij}(q,u) + \alpha h_{ij}(q) \ge 0
```

se impone en un QP:

```math
u_i^*
=
\arg\min_u \|u-u_i^{nom}\|^2
\quad
s.t. \quad
\dot h(q,u)+\alpha h(q) \ge 0.
```

El `u_i^{nom}` vendria de Smith-QR/campo unico, y el QP actuaria como filtro de seguridad. Esto es un puente claro hacia investigacion doctoral.

## 8. Data-driven y MARL: como hacerlo riguroso

### 8.1 Lo que si se puede afirmar ahora

MAPPO en SP1 usa rollout muestreado de politica y PPO estilo CTDE con warm start. El checkpoint reporta:

- actor ejecutable: 4674 parametros;
- entrenamiento actor+critic: 9411 parametros;
- training episodes: 768;
- train seeds: 1000;
- validation seeds: 200;
- test seeds: 200;
- decoder de quorum: true;
- rollout action mode: sampled_policy.

Eso permite decir que hay entrenamiento RL real, no solo una heuristica congelada.

SP2, en cambio, no debe presentarse como MARL. Sus metodos data-driven actuales son scorers supervisados por oraculo:

- `imitation_capacity`: modelo lineal con 8 parametros, entrenado por distillation de `centralized_capacity_milp`.
- `neural_capacity_scorer`: MLP compacto de una capa oculta, 121 parametros, 220 epocas supervisadas, tambien entrenado contra el oraculo.
- Train/validation/test usan seeds disjuntas, y el Monte Carlo final usa otros seeds.

Esto permite decir que SP2 tiene data-driven bien controlado, no que tenga RL multiagente completo. La ruta correcta es usar SP2 como base para un futuro MAPPO/GNN capacity-aware, no inflar el claim actual.

### 8.2 Lo que no se debe afirmar

No decir:

- "MAPPO resuelve el problema general".
- "MARL domina a Smith-QR".
- "La politica aprendida tiene garantias teoricas".
- "Generaliza a cualquier numero de robots/cargas".
- "El decoder no influye".

Decir:

- "MAPPO aporta una politica aprendida competitiva para SP1 bajo escenarios sinteticos definidos".
- "SP2 usa distillation supervisada de oraculo para capacity scoring; no es aun MARL".
- "La comparacion incluye coste de entrenamiento, parametros, runtime y comunicacion".
- "El decoder se declara como capa de factibilidad, no como parte invisible de la politica".

### 8.3 Mejor giro cientifico

El giro elegante no es "model-based vs MARL". Es:

> Model-based da estructura, interpretabilidad y seguridad; MARL aprende correcciones, prioridades y parametros de payoff que son dificiles de calibrar a mano.

Rutas:

1. **Policy distillation:** entrenar MAPPO y destilarlo a payoff Smith-QR interpretable.
2. **Neural payoff shaping:** red pequena predice pesos `alpha,beta,gamma` del payoff, no la asignacion completa.
3. **GNN critic, symbolic actor:** critic con message passing, actor Smith-QR.
4. **Amortized optimizer:** la red aproxima solucion primal-dual, pero se proyecta a restricciones fisicas.
5. **Offline-to-online:** aprender en simulacion, ejecutar con guardias model-based.

Esta narrativa es mas PhD que decir "usamos MARL".

## 9. Resultados: como leerlos sin autoengano

### 9.1 SP1

SP1 produce una historia fuerte y defendible porque el oraculo, MAPPO, reglas clasicas, CBBA, model-based y propuestas se juzgan sobre los mismos mundos. El experimento final `SP1_MC_recruitment_comparison` ejecuta 27.300 evaluaciones, 100 seeds, 4 generadores, 13 ids de metodo si se incluye `oracle_reference`, 0 fallos en auditoria teorica y MP4 representativos.

- El oraculo centralizado da la cota teorica.
- MAPPO se acerca mucho al oraculo en gap y success.
- Greedy/Hungarian/CBBA pueden tener alta demand satisfaction, pero peor success/gap por criterios de coalicion.
- Smith es muy barato y rapido, pero en la version actual no gana en calidad global.
- El reporte ahora mide coste fisico y coste de recursos, lo cual hace la comparacion mas honesta.

Ranking global SP1:

| Rank | Metodo | Lectura | Gap | Success | Runtime |
|---:|---|---|---:|---:|---:|
| 1 | `centralized_coalition_milp` | referencia oracular | 0.000 | 0.847 | 2.60 ms |
| 2 | `oracle_reference` | replay referencia | 0.000 | 0.847 | 2.64 ms |
| 3 | `mappo_recruitment` | propuesto data-driven | 0.004 | 0.846 | 13.87 ms |
| 4 | `hungarian_expanded` | classic centralized | 0.277 | 0.721 | 0.065 ms |
| 5 | `greedy_nearest` | classic decentralized | 0.304 | 0.722 | 0.131 ms |
| 6 | `cbba` | SOTA proxy decentralized | 0.338 | 0.698 | 0.408 ms |

La evidencia estadistica respalda la narrativa: los metodos difieren en gap, MAPPO baja el gap frente a imitation y Hungarian, Smith es mucho mas rapido que MAPPO, y MAPPO obtiene mayor success que Smith. La conclusion no es que MAPPO sea siempre mejor, sino que en SP1 la politica aprendida se acerca al oraculo cuando se le permite pagar entrenamiento, parametros y decoder.

La frase para defensa:

> El resultado importante no es que un metodo gane en todas las metricas. El resultado importante es que la evaluacion distingue calidad teorica, coste fisico, coste computacional y coste de entrenamiento, mostrando donde una politica aprendida justifica su complejidad y donde una regla distribuida barata sigue siendo preferible.

### 9.2 SP2

SP2 ya no es un plan: es el segundo pipeline ejecutado. El experimento final `SP2_MC_capacity_comparison` ejecuta 20.280 checks, 40 seeds, 5 generadores, 13 ids de metodo, 0 fallos de auditoria y MP4 representativos. Su objetivo es distinto al de SP1: no pregunta solo "a que carga va cada robot", sino "cuanta capacidad efectiva, descontada por bateria y distancia, queda cubriendo cada carga".

El refinamiento teorico clave de SP2 es el Teorema 2: si la capacidad efectiva depende del par robot-carga, el payoff plano pierde la garantia potencial salvo casos factorizables. La forma marginal `e_ik V_k sigma(D_k-S_k)-g_ik` recupera potencial exacto para `E` fija. Esto se implemento como ablacion reproducible en `SP2_MC_marginal_payoff_ablation`.

Ranking global SP2:

| Rank | Metodo | Lectura | Capacity | Success | Score gap | Capacity gap | Runtime |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `centralized_capacity_milp` | score oracle | 0.514 | 0.487 | 0.000 | 0.029 | 40.94 ms |
| 2 | `oracle_reference` | replay score oracle | 0.514 | 0.487 | 0.000 | 0.029 | 40.84 ms |
| 3 | `capacity_oracle_reference` | techo fisico capacidad | 0.529 | 0.227 | 0.049 | 0.000 | 11.32 ms |
| 4 | `neural_capacity_scorer` | propuesto data-driven | 0.507 | 0.263 | 0.109 | 0.050 | 1.01 ms |
| 5 | `imitation_capacity` | baseline data-driven | 0.514 | 0.218 | 0.118 | 0.038 | 0.98 ms |
| 6 | `hungarian_capacity` | classic centralized | 0.510 | 0.083 | 0.228 | 0.041 | 0.22 ms |
| 7 | `greedy_capacity_nearest` | classic decentralized | 0.510 | 0.219 | 0.276 | 0.044 | 0.30 ms |
| 8 | `replicator_capacity` | model-based baseline | 0.525 | 0.139 | 0.297 | 0.026 | 0.36 ms |
| 11 | `smith_capacity` | proposed model-based | 0.521 | 0.103 | 0.343 | 0.033 | 0.35 ms |

La lectura correcta de SP2 es mas sutil que SP1:

- El oraculo de score gana porque puede balancear capacidad parcial, cargas completas y costes.
- El oraculo de capacidad logra el techo de cobertura fisica, pero no maximiza el score operativo.
- El neural scorer es el mejor metodo propuesto por score gap, pero es supervised distillation, no MAPPO.
- Los metodos model-based propuestos son baratos y cubren capacidad parcial razonable, pero no completan suficientes cargas bajo el score actual.
- `primal_dual_capacity` no supera a `greedy_capacity_nearest` en success; esta hipotesis no se rechaza a favor del propuesto y debe quedar como limitacion experimental.
- Smith es rapido y compacto, pero en SP2 no puede venderse como ganador global.
- La ablacion marginal si valida la prediccion formal: `smith_capacity_marginal` reduce el score gap de 0.372 a 0.157 frente a `smith_capacity_plain`, sube success de 0.051 a 0.135, reduce `incomplete_capacity_ratio` de 0.946 a 0.848 y mejora `served_capacity_alignment` de 0.049 a 0.137.
- El resultado no dice que Smith marginal gane al oraculo; dice algo mas fuerte para la metodologia: la teoria detecta una desalineacion, prescribe el payoff corregido, y el experimento confirma que esa correccion cambia el comportamiento en la direccion esperada.

La frase para defensa:

> SP2 demuestra que pasar de cardinalidad a capacidad cambia el ranking: cubrir kg parcialmente no equivale a completar cargas. Por eso usamos dos referencias, una de score operativo y otra de techo fisico, y reportamos tanto gap teorico como kg faltantes/sobrantes, distancia, energia, comunicacion y runtime.

La frase refinada tras el Teorema 2:

> En SP2, las cargas no compran robots: compran capacidad efectiva marginal. Cuando el payoff ignora `e_ik`, la dinamica puede cubrir kg de forma dispersa; cuando el payoff se corrige por capacidad marginal, baja el gap, sube la completitud y se reduce la capacidad atrapada en cargas incompletas.

### 9.3 SP3

SP3 ya no es un plan: es el tercer pipeline ejecutado. El experimento estadistico final `SP3_MC_wrench_comparison_high_power` ejecuta 20.040 corridas, 6 escenarios, 334 seeds por escenario, 10 metodos, figuras principales y 38.076 checks de auditoria con 0 fallos. El experimento compacto `SP3_MC_wrench_comparison_methodology_v3` retiene MP4 representativos. Su pregunta es distinta de SP1 y SP2: no basta sumar robots o kg; la coalicion debe poder generar el wrench demandado por la carga.

Ademas, `SP3_POSE_suite_euler_lagrange_transport` genera 18 ejemplos dinamicos con Euler-Lagrange/Hamiltoniano para casos con mas AMR que cargas, AMR-cargas balanceados y menos AMR que cargas. Compara referencia centralizada, clasicos, SOTA proxy y propuestas, y produce MP4 donde los AMR se reclutan a slots, aplican fuerzas vectoriales, generan torque y desplazan/giran la carga. Su `theory_audit.json` tiene 18 checks y 0 fallos; la tasa `pose_success=0.611` se interpreta como resultado visual/controlado, no como inferencia estadistica principal.

Ranking global SP3:

| Rank | Metodo | Lectura | Coverage | Precision | FP assigned | Gap | Runtime |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `wrench_oracle` | referencia fisica | 1.000 | 1.000 | 0.000 | 0.000 | 112.80 ms |
| 2 | `smith_wrench_marginal` | propuesta marginal | 1.000 | 0.500 | 0.500 | 0.092 | 22.89 ms |
| 3 | `replicator_wrench_deficit` | model-based baseline | 1.000 | 0.500 | 0.500 | 0.092 | 25.12 ms |
| 4 | `bnn_wrench_deficit` | model-based baseline | 1.000 | 0.500 | 0.500 | 0.092 | 25.15 ms |
| 5 | `smith_wrench_deficit` | propuesta Smith | 1.000 | 0.500 | 0.500 | 0.092 | 25.11 ms |
| 6 | `cbba_slots` | SOTA proxy | 1.000 | 0.500 | 0.500 | 0.093 | 22.75 ms |
| 7 | `hungarian_slots` | classic centralized | 1.000 | 0.500 | 0.500 | 0.093 | 0.07 ms |
| 8 | `oracle_scalar_assignment` | referencia escalar | 1.000 | 0.500 | 0.500 | 0.093 | 18.56 ms |

La frase para defensa:

> SP3 muestra por que el criterio escalar es metodologicamente peligroso: puede declarar una carga cubierta aunque la coalicion no pueda producir el torque o la direccion de fuerza requerida. El resultado fuerte no es que nuestra heuristica gane ya al oracle; el resultado fuerte es que el protocolo detecta falsos positivos fisicos, separa coverage de precision y obliga a evaluar roles/slots en espacio wrench.

El experimento pose-dinamico complementario muestra el paso de asignacion a movimiento de una masa rigida: los AMR se posicionan en slots, aplican fuerzas acotadas, generan torque y desplazan/giran la carga hasta una pose objetivo. Esto no convierte SP3 en control industrial completo, pero si da una demostracion visual y matematica de la ruta hacia SP8.

### 9.4 SP4

SP4 convierte la comparacion en movimiento post-asignacion. El experimento estadistico final `SP4_MC_motion_comparison_high_power` ejecuta 20.070 rollouts, 6 escenarios, 223 seeds, 15 metodos y 21.408 checks de auditoria con 0 fallos. El experimento compacto `SP4_MC_motion_comparison` retiene MP4 representativos. La pregunta ya no es que robot se asigna, sino si llega con seguridad y coste razonable.

Ranking global SP4:

| Rank | Metodo | Lectura | Arrival | Collision | Timeout | Time | Energy | Gap |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `apf_obstacle_avoidance` | classic decentralized | 1.000 | 0.0468 | 0.000 | 23.85 s | 791.57 Wh | 0.097 |
| 2 | `direct_to_target` | classic directo | 1.000 | 0.0496 | 0.000 | 21.86 s | 788.78 Wh | 0.101 |
| 3 | `velocity_obstacle_proxy` | SOTA decentralized | 1.000 | 0.0514 | 0.000 | 24.35 s | 790.58 Wh | 0.115 |
| 4 | `replicator_motion_field` | model-based decentralized | 1.000 | 0.0535 | 0.000 | 23.80 s | 789.81 Wh | 0.121 |
| 5 | `logit_motion_field` | model-based decentralized | 1.000 | 0.0539 | 0.000 | 24.90 s | 790.16 Wh | 0.125 |
| 6 | `explicit_vgne_cbf_motion` | propuesta explicita | 1.000 | 0.0546 | 0.000 | 24.30 s | 789.94 Wh | 0.126 |
| 7 | `reference_time_expanded_cbf` | referencia segura | 0.921 | 0.0104 | 0.079 | 26.49 s | 918.80 Wh | 0.000 |
| 8 | `cbf_safety_filter` | SOTA centralized | 0.918 | 0.0115 | 0.082 | 26.80 s | 915.12 Wh | 0.015 |
| 9 | `smith_motion_field` | propuesta Smith motion | 0.887 | 0.0124 | 0.113 | 27.14 s | 930.83 Wh | 0.028 |

La evidencia estadistica sostiene dos claims fuertes y un resultado negativo:

- La referencia CBF reduce colisiones frente a `direct_to_target` (`p_Holm=2.52e-183`, efecto medio `-0.03925`).
- `cbf_safety_filter` reduce colisiones frente a `direct_to_target` (`p_Holm=8.88e-183`, efecto medio `-0.03814`).
- `tensor_flow_motion_field` reduce colisiones frente a `direct_to_target` (`p_Holm=1.41e-183`, efecto medio `-0.03744`).
- `energy_aware_smith_motion` no demuestra ahorro energetico estadisticamente significativo frente a CBF (`p_Holm=0.9999998`).

La lectura correcta es de Pareto, no de ganador universal. Los metodos directos llegan siempre y son baratos, pero chocan mas. CBF y Smith sacrifican rapidez y algunos timeouts para ganar seguridad. Esa tension es exactamente lo que SP4 debe mostrar antes de pasar a transporte de payload.

### 9.5 SP5

SP5 cierra el salto hacia transporte cooperativo del objeto. El experimento estadistico oficial actual `SP5_MC_cooperative_transport_high_power` ejecuta 20.040 rollouts, 6 escenarios, 334 seeds, 10 metodos, 6 figuras principales y 20.040 checks de auditoria con 0 fallos. La corrida compacta `SP5_MC_cooperative_transport` conserva los MP4 largos de 44 s para inspeccion visual. SP5 ya es una campana Monte Carlo con dinamica de payload, slots, pickup, formacion, obstaculos, trafico movil, otras cargas solidas y docking estricto.

Ranking global SP5 debe citarse desde `results/sp5/SP5_MC_cooperative_transport_high_power/tables/performance_ranking.csv`. En el high-power actual:

| Rank | Metodo | Lectura | Transport | Target | Formation broken | Pose error | Gap |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `reference_centralized_mpc_cbf_cargo` | referencia centralizada | 1.000 | 1.000 | 0.014 | 0.0003 m | 0.000 |
| 2 | `sota_centralized_cbf_cargo` | SOTA cargo centralizado | 0.985 | 1.000 | 0.048 | 0.0016 m | 0.027 |
| 3 | `sota_decentralized_vo_cargo` | SOTA cargo descentralizado | 0.977 | 1.000 | 0.065 | 0.0023 m | 0.037 |
| 4 | `ours_hamiltonian_cargo` | propuesta cargo Hamiltoniana | 0.976 | 1.000 | 0.057 | 0.0012 m | 0.031 |
| 5+ | push/drag variants | fallan al exigir pose/formacion | <= 0.035 | <= 0.035 | variable | >= 4.479 m | >= 0.970 |

La correccion reciente de SP5 es importante para honestidad academica:

- La tolerancia de pose se endurece a `0.20 m` y `5 deg`.
- El trafico movil y las otras cargas ya no son campos blandos atravesables: la corrida high-power tiene `failed_checks=0`; los near-misses de margen quedan como `safety_violation_count`, no como colision escondida.
- Los videos duran 44 s con 10 s de estado final, por lo que el docking se observa claramente.
- El video diagnostico `sp5_multi-group-crossing-push_proposed_model-based_decentralized_cargo_hamiltonian-tensor-cargo_ours-hamiltonian-cargo_seed6100.mp4` muestra carga, trafico `traffic-a/b`, docking preciso y ausencia de cruce.

La conclusion SP5 es fuerte pero acotada: al exigir pose final de carga, formacion y cuerpos solidos, el ranking deja de depender solo de asignacion o llegada individual. H5_1 confirma que la referencia reduce gap frente a APF (`p_Holm=0`), H5_4 confirma diferencias globales de score (`p_Holm=0`), pero H5_2 y H5_3 no se confirman; por tanto la tesis no debe vender superioridad universal de nuestras variantes push. No debe afirmarse validacion industrial de contacto/friccion; debe afirmarse que el benchmark ya obliga a mover el objeto como cuerpo rigido y no permite ganar atravesando trafico, obstaculos ni otras cargas.

### 9.6 SP6

SP6 anade robustez operativa: no mide solo si una politica funciona en condiciones nominales, sino si repara coaliciones cuando cambia el sistema. El experimento estadistico oficial actual `SP6_MC_robustness_comparison_high_power` ejecuta 20.000 rollouts, 8 escenarios, 250 seeds, 10 metodos, 6 figuras principales, tablas por corrida/robot/carga/trayectoria y 20.000 checks de auditoria con 0 fallos. La corrida compacta `SP6_MC_robustness_comparison` conserva 7 MP4 largos. La version actual exige no-colision dura; near-misses positivos de margen se penalizan como seguridad, pero no invalidan una corrida fisicamente no penetrante.

Ranking global SP6 debe citarse desde `results/sp6/SP6_MC_robustness_comparison_high_power/tables/performance_ranking.csv`. En el high-power actual:

| Rank | Metodo | Lectura | Completion | Lost | Gap ref | Collision |
|---:|---|---|---:|---:|---:|---:|
| 1 | `ours_guarded_wrench_market_recovery` | propuesta guardada wrench-market | 0.712 | 0.288 | 0.0108 | 0.0000 |
| 2 | `primal_dual_recovery` | propuesta primal-dual | 0.710 | 0.291 | 0.0447 | 0.0000 |
| 3 | `reference_resilient_oracle` | referencia centralizada resiliente | 0.709 | 0.291 | 0.0000 | 0.0000 |
| 4 | `smith_qr_recovery` | propuesta Smith-QR recovery | 0.707 | 0.293 | 0.0480 | 0.0000 |
| 5 | `tensor_flow_recovery` | propuesta tensor-flow | 0.703 | 0.297 | 0.0315 | 0.0000 |
| 10 | `classic_decentralized_greedy_recovery` | baseline clasico descentralizado | 0.689 | 0.311 | 0.0924 | 0.0000 |

La lectura importante cambio despues de imponer no-colision dura y subir la potencia estadistica. La familia model-based con repair ya no puede prometer que recupera todas las cargas factibles en todos los escenarios; eso seria una lectura demasiado optimista de una simulacion laxa. La lectura defendible es mas seria: bajo fallos, escasez, bloqueos y cargas inviables, todos los metodos quedan sujetos a la misma geometria fisica, no atraviesan AMR/cargas/obstaculos, y las diferencias se leen en gap, deteccion de inviabilidad, energia, comunicacion, reasignaciones y completion. En el high-power, `ours_guarded_wrench_market_recovery` queda primero por completion y reduce lost-load frente a greedy (`p_Holm=2.55e-05`), aunque H6.2 no confirma mejora significativa de completion frente a Smith (`p_Holm=0.196`).

Correcciones metodologicas de SP6 que deben citarse:

- Los eventos separan ocurrencia fisica de observacion por los metodos descentralizados.
- Los AMR asignados se posicionan en slots alrededor del destino de carga, no todos en el centro.
- La carga inviable se trata como caso negativo correcto; detectarla evita desperdicio de robots.
- Las coaliciones tienen persistencia durante una entrega: los robots pueden ser reemplazados por fallos/bateria, pero no deben saltar de carga en carga sin completar.
- La referencia se etiqueta como recuperacion centralizada resiliente, no como oracle exacto.
- Las cargas no pueden atravesarse entre ellas ni atravesar obstaculos; los AMR tampoco pueden solaparse entre si.
- El ranking prioriza exito/completion/gap, pero `collision_count=0` queda como contrato fisico duro antes de interpretar recursos.

### 9.7 Estado de ejecucion SP7-SP8

SP1, SP2, SP3, SP4, SP5 y SP6 quedaron como plantilla operativa. SP7 y SP8 ya siguen el mismo contrato minimo:

```text
configs/scenarios/sp<k>/
configs/experiments/sp<k>/
src/viu_mrob_tfm/sp<k>/
tests/test_sp<k>_pipeline.py
results/sp<k>/<experiment_id>/
```

El estado actual es:

| Orden | SP | Por que va ahi | Entregable actual |
|---:|---|---|---|
| 1 | SP7 comunicacion | Evalua radio, relay, packet loss, delay, jitter y sensores durante transporte | Conectividad temporal + transporte multi-grupo, 20.176 runs, 0 fallos y paper figures |
| 2 | SP8 escala warehouse | Evalua intratabilidad centralizada, cargas moviles, wrench/torque, obstaculos y metodos distribuidos | compacto: 150 runs y MP4; high-power: 20.000 runs, 5-50.000 AMR, 0 fallos y figuras de scaling/timeout/Pareto mas densas |

La comparacion de metodos debe repetirse en todos los SP, pero con oraculos y metricas adaptadas. El esqueleto comun es:

| Familia | SP1 | SP2-SP3 | SP4-SP6 | SP7 | SP8 |
|---|---|---|---|---|---|
| Classic centralized | Hungarian/MILP | capacity/wrench MILP | shortest payload push / min-cost replanner | global comm controller | expanded Hungarian / time-expanded MPC |
| Classic decentralized | greedy nearest | greedy capacity/wrench | APF push / local replanning | local sensor APF | local greedy |
| SOTA decentralized | CBBA-like | CBBA payload-aware | VO/CBBA payload-aware | relay/CBBA or delay consensus | CBBA partitioned / local auction |
| Model-based ours | replicator/logit/BNN/Smith/primal-dual + repair | marginal capacity/wrench + guarded repair | primal-dual/tensor-flow/Hamiltonian cargo | connectivity wrench game + delay repair | primal-dual spatial, tensor quorum flow, wrench-market hierarchical, MFG approx |
| Data-driven | imitation/MAPPO | supervised scorer ahora; MAPPO/GNN futuro | MAPPO reactive futuro | no neuronal en v1 | no neuronal en v1; GNN/MARL queda futuro |
| Reference | oracle coalition | oracle capacity/wrench | safe reference replanner | full communication reference | coalition oracle con timeout declarado |

### 9.8 Que falta para que el resultado sea "wow"

Para que la memoria sea mas novedosa, conviene anadir al menos una de estas piezas:

1. **Re-ejecutar Monte Carlo final con la familia hybrid repair.** El codigo y los smoke ya incluyen repair/guarded/tensor-flow; falta congelar un benchmark final que actualice rankings y tablas historicas.
2. **Ablacion de arquitectura, no solo de Smith-QR.** Motor puro vs motor+quorum vs motor+repair vs motor+wrench vs motor+energy para replicator, logit, BNN, Smith y primal-dual.
3. **Ablaciones OOD de MAPPO/GNN.** Quedan como anexo/futuro doctoral; falta separar causalmente decoder, warm start, politica pura y repair aprendido.
4. **Pareto de calidad-recursos.** Ya existe, pero debe aparecer en memoria como argumento central.
5. **Degradacion por radio.** Convertirlo en figura principal.
6. **Counterexample matematico.** Convertir el caso cardinalidad suficiente/torque imposible en figura principal de introduccion y anexo.

## 10. Originalidad: claim ledger

| Claim | Estado | Como defenderlo | Que no decir |
|---|---|---|---|
| Arquitectura distribuida para coaliciones multi-AMR | Implementada y evaluada en SP1-SP8 | Modulos, configs, tests, resultados, videos SP1-SP8, auditorias, benchmark de comunicacion SP7 y escalabilidad SP8 | No decir despliegue industrial |
| Smith-QR como extension interpretable | Implementado como propuesta SP1/SP2/SP3, con resultados mixtos | Dinamica Smith + quorum/capacidad/wrench + costes | No decir teorema global ni ganador universal |
| Familia no-Smith de dinamicas + repair | Implementada en codigo y evaluada en SP1-SP8 segun alcance de cada SP | Replicator, Logit, BNN/Brown, primal-dual, PID, tensor-flow, Hamiltonian cargo, recovery repair/guard monotono y scale-aware quorum flow | No afirmar superioridad estadistica universal |
| Cargas heterogeneas | Validado en SP1 por quorum/payload, SP2 por capacidad efectiva y SP3 por slots/wrench | Peso/capacidad, bateria, distancia, kg under/over, slots, torque, oraculos de score/capacidad/wrench | No decir que friccion/contacto real 3D ya esta cerrado |
| Evaluacion justa model-based vs data-driven | Implementada en SP1/SP2; SP7 evalua comunicacion/sensores sin aprendizaje | parametros, episodes, runtime, communication, energy, train/test seeds, costo de oraculo y metricas anti-abstencion | No comparar solo demand/capacity/wrench satisfaction |
| MAPPO real | Implementado para SP1 | sampled_policy, PPO, validation/test | No ocultar decoder |
| SP2 data-driven | Implementado como distillation supervisada | modelo lineal 8 params, MLP 121 params, seeds disjuntas | No llamarlo MARL |
| Capacidad wrench | Implementada en SP3 v3 + experimento pose-dinamico | Anexo matematico, slots, residual wrench, false positives, MP4 Euler-Lagrange/Hamiltoniano | No afirmar validacion fisica completa ni contacto/friccion 3D |
| Transporte cooperativo de payload | Implementado en SP5 high-power + videos compactos | Pickup, slots, formacion, push/drag vs cargo, obstaculos, grupos moviles, cargas solidas, pose final, hard clearances, MC de 20.040 y MP4 | No decir que es simulacion de contacto/friccion industrial completa |
| Robustez operativa | Implementada en SP6 high-power + videos compactos | Fallos, bateria, radio, obstaculo dinamico, retraso de observacion, carga inviable, slots de recuperacion, no-colision dura, MC de 20.000 y MP4 con exitos/fallos validos | No decir POMDP industrial completo, garantia hardware ni recuperacion universal |
| Comunicacion y sensado | Implementada en SP7 high-power | Radio, relay, packet loss, delays, jitter, sensores, obstaculos, grupos moviles y clearances heredados de SP5 en 20.176 corridas | No decir RF industrial |
| Escalabilidad warehouse | Implementada en SP8 high-power + videos compactos | Timeouts centralizados, complejidad, memoria, throughput, wrench/torque y obstaculos en 150 corridas compactas con videos y 20.000 corridas 5-50.000 AMR | No decir despliegue Amazon/Cainiao ni contacto fisico completo |
| CoppeliaSim | Visual/plausibility | Videos y escenas | No decir hardware |
| Ruta PhD | Conceptual | MFG, GNEP, port-Hamiltonian, CBF-QP | No mezclar con resultados ya probados |

## 11. Lo que Fable debe criticar

Pedir a Fable que responda estas preguntas:

1. La contribucion central esta formulada como problema nuevo o como mezcla de tecnicas?
2. El termino "cargas heterogeneas" esta probado con suficiente riqueza fisica?
3. SP1 evalua reclutamiento o transporte cooperativo completo?
4. MAPPO es comparado de forma justa frente a reglas baratas?
5. El oraculo usado es una cota teorica adecuada?
6. Las metricas favorecen algun metodo por construccion?
7. Hay leakage entre seeds de entrenamiento/tuning y evaluacion?
8. La seccion matematica prueba algo o solo motiva?
9. Donde esta el primer resultado verdaderamente original?
10. Cual seria el giro mas elegante para convertirlo en paper?
11. Que claim deberia eliminarse para evitar rechazo?
12. Que figura debe abrir la defensa?

## 12. Riesgos conceptuales y mitigaciones

| Riesgo | Por que es peligroso | Mitigacion |
|---|---|---|
| Confundir demand satisfaction con calidad | Puede premiar llenar cargas sin factibilidad teorica | Ranking por gap, success, under/over, coste |
| Decir que MAPPO es SOTA general | Puede parecer exagerado | "MAPPO-style CTDE for SP1" |
| Llamar MARL a SP2 | SP2 usa supervision de oraculo, no PPO multiagente | "data-driven supervised capacity scorer" |
| Vender CoppeliaSim como validacion fisica | Simulacion no es hardware | "plausibilidad visual e integracion" |
| Usar cardinalidad como capacidad | Falla con torque/geometria | Wrench residual y slots |
| Comparar red grande contra regla barata sin recursos | Injusto | Pareto calidad-recursos |
| Inflar MFG/Hamiltoniano como resultado | Aun no esta implementado | Ruta doctoral, no claim TFM |
| Usar demasiados subproblemas | Diluir contribucion | SP1-SP8 como evidencia ejecutable, con SP8 acotado a escala/intratabilidad mesoscopica |
| Falta de citas reales | Vulnerable en tribunal | Auditar `references.bib` y claims |

## 13. Giro "wow" recomendado

La tesis podria titularse conceptualmente:

> De coaliciones numericas a coaliciones fisicas: reclutamiento distribuido de AMR mediante deficit, quorum y capacidad wrench.

O mas academico:

> Smith-QR: una arquitectura fisico-economica para reclutamiento distribuido de coaliciones multi-AMR bajo cargas heterogeneas.

El giro novedoso:

```text
Las cargas no piden robots.
Las cargas piden capacidad fisica.
Los robots no reciben tareas.
Los robots responden a deficit local bajo coste, energia y comunicacion.
La coalicion no se acepta por numero.
La coalicion se acepta por capacidad efectiva y residual wrench.
```

Esta narrativa es simple, original y defendible.

## 14. Ruta PhD

### Fase doctoral 1 - Teoria discreta finita

- Formalizar Smith-QR como juego potencial con clearing entero.
- Probar bound de perdida por discretizacion.
- Probar convergencia practica bajo grafo conexo a trozos.
- Conectar primal-dual y Smith como dinamicas de equilibrio.

### Fase doctoral 2 - Wrench y roles

- Resolver `z_{ikh}` explicitamente.
- Integrar contact wrench cone.
- Medir residual wrench por carga.
- Incorporar friccion, torque y saturaciones.

### Fase doctoral 3 - Seguridad

- Campo unico nominal.
- CBF-QP como filtro.
- Garantias de no colision y mantenimiento de conectividad.
- Seguridad bajo cargas rigidas.

### Fase doctoral 4 - MFG y limite de gran poblacion

- Modelar densidad de capacidad `m(q,t)`.
- Definir HJB + Fokker-Planck con cargas puntuales.
- Analizar Wardrop/Nash en limite continuo.
- Relacionar solucion MFG con Smith discreto.

### Fase doctoral 5 - Hamiltoniano y pasividad

- Carga como sistema port-Hamiltonian.
- Robots como puertos de potencia.
- Reparto de potencia por juego wrench.
- Pasividad para interaccion robot-carga.

### Fase doctoral 6 - MARL estructurado

- GNN critic.
- Actor Smith-QR parametrico.
- Aprendizaje de pesos de payoff.
- Proyeccion fisica.
- Generalizacion OOD.

### Fase doctoral 7 - Hardware o gemelo digital fuerte

- ROS 2.
- AMR reales o simulacion fisica validada.
- Cargas modulares.
- Medicion de energia y fuerza.
- Protocolos reproducibles.

## 15. Estructura recomendada de memoria final

1. **Resumen.** Problema, metodo, validacion, resultado principal.
2. **Introduccion.** Industria, AMR, limite de un robot por carga, necesidad de coaliciones.
3. **Objetivos e hipotesis.** Objetivo general, especificos, SPs y claims falsables.
4. **Estado del arte.** MRTA, coaliciones, CBBA, juegos poblacionales, MARL, transporte cooperativo, AMR comerciales.
5. **Modelo.** Robots, cargas, grafo, demanda, coste, energia, capacity/wrench.
6. **Metodo.** Smith-QR, quorum, clearing, MAPPO baseline, oraculo.
7. **Metodologia experimental.** Seeds, escenarios, metricas, fairness, tests.
8. **Resultados SP1.** Ranking, Pareto, degradacion, videos, hipotesis.
9. **Discusion.** Que aprendimos, tradeoffs, por que no hay ganador universal.
10. **Limitaciones.** Simulacion, contacto, hardware, MFG no cerrado, MARL OOD.
11. **Conclusiones.** Contribucion defendible y ruta futura.
12. **Anexos.** Matematica, reproducibilidad, tablas grandes, configuraciones, declaracion de IA.

## 16. Figuras que deberian existir en la defensa

1. **Figura de problema.** Cargas de distinto peso/geometria y AMR con capacidades.
2. **Pipeline.** Escenario -> metodo -> metrics -> hypothesis -> report/video.
3. **Arquitectura.** Deficit -> Smith -> quorum -> wrench -> control.
4. **Taxonomia de metodos.** Classic/SOTA/model-based/data-driven/ours/oracle.
5. **Ranking SP1.** Gap vs oracle y success.
6. **Pareto calidad-recursos.** MAPPO cerca del oraculo pero no gratis.
7. **Coste fisico.** Travel/energy vs success.
8. **Degradacion comunicacion.** Radio vs performance.
9. **Video snapshot.** Robots, cargas, pesos/capacidades, asignaciones.
10. **Roadmap PhD.** GNEP, MFG, Hamiltonian, CBF-QP.

## 17. Checklist de cierre antes de entregar

### Cientifico

- [ ] Cada objetivo tiene resultado o limitacion explicita.
- [ ] Cada hipotesis tiene metrica y archivo de salida.
- [ ] El oraculo no se presenta como metodo desplegable.
- [ ] MARL tiene coste de entrenamiento y parametros reportados.
- [ ] Smith/Smith-QR no se vende como dominante universal.
- [ ] Heterogeneidad de carga no se reduce a un slogan.
- [ ] Las figuras principales cuentan una historia unica.

### Reproducibilidad

- [ ] `python -m pytest -q` pasa o se reportan fallos.
- [ ] Entry points documentados funcionan.
- [ ] Seeds de entrenamiento y evaluacion estan separados.
- [ ] Resultados pesados tienen manifest.
- [ ] Videos y figuras tienen nombres con metodo, familia y escenario.
- [ ] GitHub contiene codigo, configs y resultados esenciales.

### VIU

- [ ] Portada institucional.
- [ ] Resumen y palabras clave.
- [ ] Indice.
- [ ] Introduccion y estado del arte.
- [ ] Objetivos.
- [ ] Metodologia.
- [ ] Desarrollo y resultados.
- [ ] Conclusiones.
- [ ] Bibliografia.
- [ ] Anexos.
- [ ] Declaracion de uso de IA si la convocatoria la exige.
- [ ] Defensa de 20 minutos con diapositivas limpias.

## 18. Bibliografia base que debe sostener la memoria

La memoria ya incluye muchas entradas en `docs/doc-05-final-report/references.bib`. Las claves minimas para sostener el argumento son:

- MRTA: `gerkey2004formal`, `korsah2013taxonomy`.
- Mercados multi-robot: `dias2006market`.
- CBBA: `choi2009consensus`.
- Coaliciones: `sandholm1999coalition`, `rahwan2015coalition`.
- Juegos potenciales: `monderer1996potential`.
- Juegos poblacionales: `sandholm2010population`, `quijano2017population`.
- Control distribuido con dinamicas poblacionales: `barreiro2017distributed`, `martinezpiazuelo2022tcss`, `martinezpiazuelo2022automatica`.
- Consenso y redes roboticas: `bullo2009distributed`, `ren2008distributed`, `kia2019tutorial`.
- MFG: `lasry2007mfg`, `huang2006large`.
- Pasividad y Hamiltoniano: `vanderschraft2017l2gain`, `ortega2002interconnection`.
- Seguridad CBF: `ames2017cbf`.
- Transporte cooperativo y payload: revisar las claves focales del capitulo de estado del arte y asegurar DOI/URL.

## 19. Abstract estrategico propuesto

Este trabajo estudia el reclutamiento distribuido de coaliciones multi-AMR para transportar cargas heterogeneas en entornos intralogisticos. A diferencia de la asignacion clasica un robot-una tarea, el problema exige decidir que robots cooperan sobre una misma carga, con que coste fisico y bajo que restricciones de comunicacion, energia, bateria, capacidad efectiva, wrench, no-colision y robustez operativa. Se propone una arquitectura fisico-economica basada en deficit de carga, dinamicas poblacionales y de control (replicator, logit, BNN/Brown, Smith, primal-dual, PID y tensor-flow), cierre entero de quorum y reparacion local monotona. La validacion se realiza mediante simulacion reproducible en SP1-SP8: reclutamiento de coaliciones, capacidad efectiva, slots/wrench, movimiento post-asignacion, transporte cooperativo de payload rigido, recuperacion ante eventos, conectividad temporal bajo degradacion de comunicacion/sensores y escalabilidad warehouse bajo intratabilidad centralizada. Los pipelines comparan metodos centralizados, descentralizados, clasicos, SOTA, model-based, data-driven y variantes propuestas frente a referencias declaradas. Los resultados existentes muestran que MAPPO-style CTDE se acerca al oraculo en SP1 pagando parametros/runtime, que SP2 cambia el ranking al pasar de cardinalidad a capacidad efectiva, que SP3 expone falsos positivos escalares frente a factibilidad wrench, que SP4 revela el trade-off llegada-seguridad, que SP5 cambia de nuevo el ranking cuando se exige mover la carga a una pose objetivo manteniendo formacion frente a obstaculos, trafico robotico y otras cargas solidas, que SP6 separa recuperacion, carga inviable, comunicacion, coste de reasignacion y fallos validos bajo no-colision dura, que SP7 mide radio, packet loss, delay, jitter, relay multi-hop, conectividad temporal y sensado durante transporte cooperativo sin ocultar clearances fisicos, y que SP8 muestra como los metodos centralizados exactos/time-expanded dejan de ser operativos al crecer mientras las variantes distribuidas/hierarquicas mantienen mejor completion/wrench por recurso bajo un modelo mesoscopico. La contribucion principal no es un ganador universal, sino una metodologia rigurosa para juzgar calidad, coste fisico, conectividad, recursos computacionales, coste de entrenamiento, seguridad geometrica y escalabilidad en coaliciones multi-AMR, abriendo una extension natural hacia juegos generalizados, mean field games, control port-Hamiltoniano, CBF y aprendizaje multiagente seguro.

## 20. Cierre

El proyecto tiene potencial de TFM sobresaliente si se mantiene una disciplina: separar evidencia de ambicion. La evidencia fuerte actual esta en SP1-SP8, la arquitectura reproducible y la comparacion justa de metodos. La ambicion doctoral esta en convertir capacidad escalar en capacidad wrench, Smith-QR y las demas dinamicas poblacionales en juego generalizado con restricciones, el reclutamiento finito en MFG con error finito-N, y el control de contacto en un sistema port-Hamiltonian seguro.

La defensa debe sonar asi:

> No resolvemos todo el transporte cooperativo multi-robot. Resolvemos y medimos rigurosamente una cadena de cuellos de botella: a quien reclutar, cuanta capacidad efectiva aporta cada coalicion, si puede producir wrench, si los AMR llegan, si la carga se mueve como cuerpo rigido, si el sistema recupera ante eventos y si la coalicion permanece conectada/sensada bajo comunicacion degradada. Desde ahi, mostramos la ruta matematica natural hacia coaliciones fisicas con slots, capacidad wrench, robustez, conectividad temporal y control seguro.
