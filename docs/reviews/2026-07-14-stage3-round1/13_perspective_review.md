# Stage 3 Round 1 — Perspective Review (R3)

- Role: R3 — Sistemas robóticos, implementación, validación física y CoppeliaSim
- Base commit: `1218a064`
- Frozen-hash reference: `FH-v2 2fe960…`
- Date: 2026-07-14
- Sealed PDF: no disponible

# Phase 1 — Precommitment

Blindness disclosure: prior manuscript exposure; no paper access in this phase

## Contract Paraphrase D1-D8

### D1: Trazabilidad problema-método-resultado

Cada pregunta, subproblema y contribución deberá poder seguirse hasta una hipótesis o criterio comprobable, un método, un artefacto ejecutado, un resultado y un límite declarado. Desde la perspectiva de implementación, la trazabilidad debe cubrir tanto los componentes SP1–SP5 como la cadena integrada A0-FULL.

### D2: Integridad claim-evidencia

La naturaleza de cada afirmación deberá corresponder al nivel real de evidencia: demostración, análisis algebraico, simulación propia, simulación dinámica en CoppeliaSim, replay, HIL, propuesta o experimento con robots físicos. Ninguna conclusión deberá atribuir a un nivel de validación propiedades demostradas únicamente en otro.

### D3: Corrección teórica

Los juegos, equilibrios, resultados de convergencia, condiciones KKT o primal-dual, CBF, modelos mecánicos y análisis de complejidad deberán especificar sus supuestos y dominio de validez. La implementación discreta, el contacto, la fricción, las dependencias centralizadas y las diferencias entre dinámica ideal y ejecutada deberán ser compatibles con las garantías invocadas.

### D4: Originalidad y posicionamiento

La contribución deberá distinguirse del trabajo previo mediante mecanismos, hipótesis, arquitectura o resultados verificables, no solo por una nueva combinación terminológica. La comparación con Quijano, Martínez y otros antecedentes deberá permitir identificar con precisión qué se reutiliza, qué se adapta y qué constituye una aportación propia.

### D5: Rigor experimental y estadístico

Las conclusiones deberán apoyarse en comparaciones controladas, baselines pertinentes, semillas, unidades experimentales, intervalos de confianza, tamaños de efecto, tratamiento de multiplicidad, ablaciones y criterios de éxito definidos. Los comparadores centralizados, greedy, MARL y distribuidos deberán operar bajo presupuestos e información comparables.

### D6: Validez de sistema y alcance físico

La cadena de validación deberá diferenciar explícitamente cálculo algebraico, simulación propia, dinámica de CoppeliaSim, replay, HIL y hardware AMR. Las afirmaciones sobre física, seguridad, escalabilidad o distribución deberán limitarse al nivel efectivamente ejecutado y declarar discretización, contacto, fricción, latencias y dependencias centralizadas relevantes.

### D7: Arquitectura narrativa y escritura

El TFM deberá desarrollar una tesis única mediante una secuencia progresiva que conecte teoría, modelo, juego, algoritmos, simulaciones, integración y alcance físico. La jerarquía y densidad del texto deberán hacer visible la contribución principal y mantener las conclusiones proporcionadas a la evidencia.

### D8: Reproducibilidad e integridad bibliográfica

Los artefactos y resultados deberán poder auditarse mediante configuraciones, versiones, escenas, modelos dinámicos, parámetros, semillas, registros y procedimientos de ejecución identificables. Las referencias deberán existir, estar correctamente atribuidas y respaldar el contexto o resultado para el que se citan.

## Scoring Plan

### D1

- `what_to_look_for`: Matrices o enlaces verificables entre preguntas, SP1–SP5, A0-FULL, hipótesis, métodos, experimentos, resultados, artefactos y límites.
- `what_triggers_block`: La tesis central o varios subproblemas carecen de una ruta verificable desde el planteamiento hasta la evidencia.
- `what_triggers_warn`: Existen enlaces ambiguos, contribuciones mezcladas o trazabilidad incompleta que puede corregirse sin experimentos sustantivos nuevos.

### D2

- `what_to_look_for`: Etiquetado inequívoco del origen de cada evidencia y correspondencia entre el alcance de los claims y el nivel de validación realmente alcanzado.
- `what_triggers_block`: Una afirmación central contradice la evidencia o presenta como demostrada, física, segura o distribuida una propiedad que el soporte disponible no establece.
- `what_triggers_warn`: Hay sobreafirmaciones localizadas, límites poco visibles o confusión puntual entre prueba, simulación, replay y propuesta.

### D3

- `what_to_look_for`: Definiciones, supuestos, dominios, condiciones de existencia o convergencia y compatibilidad entre teoría, algoritmo e implementación; atención especial a extrapolaciones de tiempo continuo a discreto.
- `what_triggers_block`: Un resultado teórico central es falso, circular, no está demostrado o depende de supuestos incompatibles con el algoritmo o sistema ejecutado.
- `what_triggers_warn`: Faltan condiciones, pasos demostrativos o precisión terminológica, pero el alcance puede acotarse sin modificar la contribución principal.

### D4

- `what_to_look_for`: Comparación mecanismo por mecanismo con antecedentes, atribución de elementos reutilizados y delimitación verificable de la novedad teórica, algorítmica o de integración.
- `what_triggers_block`: Se presenta como original una contribución que reproduce esencialmente trabajo previo sin diferencia técnica o empírica defendible.
- `what_triggers_warn`: La combinación parece potencialmente valiosa, pero la aportación propia o la comparación con el estado del arte permanece difusa.

### D5

- `what_to_look_for`: Baselines, semillas, unidades experimentales, controles, intervalos de confianza, efectos, multiplicidad, ablaciones y criterios de éxito; igualdad de información y presupuesto entre comparadores.
- `what_triggers_block`: El diseño impide atribuir las mejoras al método propuesto o contiene errores que invalidan los resultados principales.
- `what_triggers_warn`: La evidencia es informativa, pero presenta controles, comparaciones, potencia, precisión estadística o ablaciones incompletas.

### D6

- `what_to_look_for`: Separación auditable entre simulación cinemática, dinámica de CoppeliaSim, replay, HIL y hardware; parámetros de contacto y fricción, paso discreto, latencias, seguridad ejecutada, escalabilidad y centralización.
- `what_triggers_block`: Se reclama validación física, distribuida, dinámica independiente o de seguridad sin que el artefacto ejecutado la demuestre.
- `what_triggers_warn`: La cadena es reproducible, pero la validación física, el escalado, la sensibilidad dinámica o la transición a AMR reales sigue siendo parcial y está correctamente limitada.

### D7

- `what_to_look_for`: Una línea argumental progresiva desde el problema hasta las conclusiones, jerarquía clara de contribuciones y conexión legible entre teoría, modelo, juego, experimentos e integración.
- `what_triggers_block`: La estructura impide reconstruir la tesis central o contiene contradicciones internas sustantivas.
- `what_triggers_warn`: La repetición, extensión o acumulación de capas dificulta identificar el aporte principal, aunque la reorganización editorial puede resolverlo.

### D8

- `what_to_look_for`: Repositorio y artefactos auditables, instrucciones de ejecución, versiones, configuraciones, escenas, parámetros, semillas, resultados intermedios y referencias verificables.
- `what_triggers_block`: Los resultados centrales no pueden reproducirse o existen referencias o atribuciones fabricadas o materialmente incorrectas.
- `what_triggers_warn`: Faltan metadatos, instrucciones, versiones o comprobaciones bibliográficas localizadas que pueden incorporarse sin rehacer la investigación.

[CONTRACT-ACKNOWLEDGED]

# Phase 2 — Review

Blindness disclosure: prior manuscript exposure; no paper access in Phase 1; paper-visible Phase 2 completed independently without consulting other reviewers or the consolidated decision.

Evidence root: `C:\Users\walla\AppData\Local\Temp\VIU-MRBO-TFM-2026-stage3-1218a064`

## Dimension Scores

| Dimensión | Score | 0–100 | Justificación |
|---|---:|---:|---|
| D1 Trazabilidad problema–método–resultado | pass | 92 | La pregunta, HC/H1–H8, la jerarquía A0–FULL/SP1–SP8 y los límites están conectados explícitamente. Véanse `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:27`, `03-hypothesis.tex:3` y `04-methodology.tex:102`. |
| D2 Integridad claim–evidencia | pass | 94 | Se distinguen prueba algebraica, simulación Python, evidencia modular, inspección visual y ausencia de hardware. RAW–SAFE–EXEC y los falsos positivos físicos evitan convertir una orden o cierre estático en éxito. Evidencia: `04-methodology.tex:77-96`, `integrated-theory-core.tex:40-68` y `07-conclusions.tex:27-31`. |
| D3 Corrección teórica | pass | 86 | El resultado ISS explicita matriz común, carga y ganancias fijas, ausencia de resets y perturbación acotada; la seguridad distingue HOCBF continua, proyección discreta y realizabilidad. Evidencia: `integrated-theory-core.tex:44-115` y `sp4-motion.tex:141-168`. |
| D4 Originalidad y posicionamiento | pass | 88 | La matriz de originalidad separa mecanismos heredados y delta propio; no reclama Nash, Smith, KKT, HOCBF o dinámica poblacional como novedades. Evidencia: `01-introduction.tex:37-46` y `05-theoretical-framework/index.tex:449-469`. |
| D5 Rigor experimental y estadístico | warn | 76 | El diseño emparejado, freeze, McNemar, bootstrap y Holm es sólido, pero faltan sensibilidad confirmatoria de parámetros físicos críticos y excitación real de saturación de par. Evidencia: `04-methodology.tex:85-110`, `physical-coalition-integrated.tex:53` y `sp4-motion.tex:292-298`. |
| D6 Validez de sistema y alcance físico | warn | 70 | El alcance está descrito honestamente, pero la cadena física termina en simulación planar Python; el contacto con fricción, HIL y AMR físicos siguen pendientes. CoppeliaSim no forma parte de la evidencia canónica SP5. Evidencia: `02-objectives.tex:18-22`, `anexo-b-reproducibilidad.tex:41-45` y `07-conclusions.tex:27-41`. |
| D7 Arquitectura narrativa y escritura | pass | 89 | La progresión problema → coalición física → teoría → A0–FULL → mecanismos SP → límites es legible y las conclusiones responden a los objetivos. Evidencia: `06-results-and-analysis/index.tex:1-14` y `07-conclusions.tex:3-25`. |
| D8 Reproducibilidad e integridad bibliográfica | warn | 74 | A0–FULL y SP5 tienen cierre hashado y rutas reproducibles; el propio documento reconoce trazabilidad variable en SP1–SP4 y contrato incompleto en SP6–SP8. Existen trazas Stage 2.5, pero no toda la escalera alcanza el mismo nivel de cierre. Evidencia: `anexo-b-reproducibilidad.tex:18-49`, `anexo-e-declaraciones.tex:4-6` y `.aris/traces/integrity/2026-07-14_stage2_5/stage2_5_final_manifest.json`. |

Promedio simple: **83,6/100**. Los valores son ordinales; la decisión contractual deriva de `pass|warn|block`, no del promedio.

## Failure Condition Checks

| Condición | Resultado R3 | Razón |
|---|---|---|
| F1: cualquier dimensión mandatory en `block` | No activada | D1–D3 son `pass`. |
| F2: dos o más mandatory en `warn` o peor, con mayoría del panel | No activada por R3 | Este informe no tiene dimensiones mandatory en `warn`; la mayoría corresponde al sintetizador. |
| F3: dimensión high-priority en `block`, con mayoría | No activada | No hay `block`. |
| F4: cualquier mandatory en `warn` | No activada | D1–D3 son `pass`. |
| F5: cualquier high-priority en `warn` | **Activada** | D5, D6 y D8 son `warn`. |
| F0: todas las mandatory en `pass` | Activada | D1–D3 pasan, pero F5 tiene mayor severidad que F0. |

## Review Body

### Reviewer Identity

Revisor R3 desde sistemas robóticos, contacto/fricción, simulación dinámica, CoppeliaSim, HIL y transición a AMR físicos. La revisión se concentra en implementabilidad y validez externa, sin sustituir la auditoría estadística de R1 ni la revisión bibliográfica de R2.

### Overall Recommendation

**Minor Revision**

### Confidence Score

**4/5.** Se leyó íntegramente `main.tex` y sus 27 entradas alcanzables y se inspeccionó la presencia de escenas y resultados relevantes en la copia ESA. No se ejecutaron campañas ni se consideraron informes de otros revisores.

### Summary Assessment

El TFM presenta una arquitectura técnicamente madura y, sobre todo, muy honesta respecto de lo que sus simulaciones demuestran. Su mejor contribución de implementación no es una promesa de despliegue distribuido, sino la semántica de auditoría que separa preferencia, cierre, factibilidad estática, orden segura y acción físicamente realizada. La distinción RAW–SAFE–EXEC, la conservación de colisiones y timeouts, y el resultado no monótono A2–A3 son particularmente valiosos para ingeniería robótica.

La principal frontera pendiente es sim-to-real. SP3 representa factibilidad wrench cuasiestática; SP4 mueve robots hacia contactos todavía sin acoplamiento físico; SP5 comienza con un agarre rígido ya establecido. Entre esas tres capas no se ejecuta todavía una secuencia física continua con impacto de docking, fricción, deslizamiento, compliance, límites de rueda y pérdida de contacto. CoppeliaSim aparece como evidencia separada o artefacto adicional, no como validación dinámica canónica del resultado central. Esto no invalida las conclusiones porque el manuscrito lo declara repetidamente, pero sí limita una aspiración de máxima calificación si no se convierte en una matriz de transferencia explícita y verificable.

### Strengths

1. **[S1] Semántica física excepcionalmente clara.** `accepted_by_stage`, `final_physical_success` y `physical_false_positive` impiden que una asignación o QP resuelto se confunda con transporte exitoso (`04-methodology.tex:102-110`; `physical-coalition-integrated.tex:8-10`).

2. **[S2] RAW–SAFE–EXEC está correctamente orientado a implementación.** Solo EXEC mueve la carga; la saturación y el error de realización pueden destruir la seguridad de SAFE, y no hay proyección posterior de poses (`integrated-theory-core.tex:40-68`; `modular-evidence-synthesis.tex:87-127`).

3. **[S3] La interacción estática–dinámica produce un hallazgo útil.** A3 mejora torque, pero puede retirar reserva de tracción y empeorar escasez. Esta no monotonía es más informativa para un integrador que un ranking agregado (`physical-coalition-integrated.tex:37-55`).

4. **[S4] Centralización declarada por etapa.** El presupuesto distingue utilidad local, umbral global, ranking, búsqueda de contactos, unión de coaliciones y selector global de reemplazo (`04-methodology.tex:51-74`). Esto evita una falsa afirmación de ejecución distribuida.

5. **[S5] Los resultados negativos se conservan.** Uniforme+closure y uniforme+guardia limitan la atribución al motor de juego; SP4 reconoce timeouts elevados y ausencia de saturación; SP7–SP8 permanecen descriptivos o exploratorios (`06-results-and-analysis/index.tex:38-53`).

### Weaknesses accionables

1. **[W1 — Alta, D6] Falta un puente dinámico independiente hacia hardware.**
   **Ubicación:** `02-objectives.tex:18-22`; `04-methodology.tex:111-119`; `anexo-b-reproducibilidad.tex:41-45`.
   La evidencia canónica SP4–SP5 es CPU/Python. La copia contiene `coppeliasim/real_scenes/sp4_v4_paired_narrow_passage.ttt` y `results/sp4/SP4_V4_COPPELIA_PAIRED_NARROW/`, pero el cuerpo no los integra como validación canónica ni define si son replay, controller-in-the-loop o simulación dinámica cerrada.
   **Acción:** añadir una matriz de evidencia con motor, dinámica activa, controlador, sensores, entradas, outputs, hashes y claim autorizado. Validar una muestra congelada en CoppeliaSim con física activa y después mediante HIL o 2–3 AMR instrumentados.

2. **[W2 — Alta para transferencia, D6] La interfaz SP3–SP5 presupone el fenómeno físico más difícil.**
   **Ubicación:** `sp4-motion.tex:5-12`; `modular-evidence-synthesis.tex:87-94`; `07-conclusions.tex:27-31`.
   SP3 asigna contactos; SP4 termina al alcanzar pose y velocidad; SP5 empieza con contactos fijos y agarre rígido. No se modelan impacto de docking, establecimiento de normal, cono de fricción, deslizamiento, compliance, pérdida o recuperación del contacto. Además, la comprobación estática usa fuerzas unilaterales mientras el seguimiento supone tracción acotada de ambos signos.
   **Acción:** introducir un modelo de contacto con normal unilateral, cono/pirámide de fricción, slip, detachment y límites rueda–suelo; ensayar explícitamente la transición docking→grasp→transporte.

3. **[W3 — Alta, D5] Los parámetros que gobiernan seguridad y éxito no tienen sensibilidad confirmatoria.**
   **Ubicación:** `physical-coalition-integrated.tex:49-53`; `07-conclusions.tex:29-31`.
   El umbral $\rho\leq0{,}16$, masa, inercia, paso de 0,1 s, horizonte, radio, ganancias HOCBF y número de proyecciones se congelaron, pero no se sometieron a sensibilidad.
   **Acción:** preespecificar un barrido pequeño sobre fricción, masa/inercia, `dt`, $k_1,k_2$, fuerza máxima y retardo. Reportar región de factibilidad, tasa de abstención y degradación del margen EXEC.

4. **[W4 — Media, D5/D6] La saturación está implementada, pero no validada experimentalmente.**
   **Ubicación:** `sp4-motion.tex:23-42` y `292-298`.
   Ninguna de las 1.188 ejecuciones SP4 saturó el par. Por tanto, la planta “saturada” no sustenta todavía robustez frente a saturación. Al mismo tiempo aparecen residuos CBF EXEC positivos sin colisión barrida.
   **Acción:** añadir escenarios de baja tensión, carga elevada, rueda pequeña, pendiente o menor límite de par; registrar torque/corriente, slip, residual SAFE/EXEC y distancia barrida.

5. **[W5 — Media, D8/impacto] Falta traducir la seguridad simulada a responsabilidades de despliegue.**
   **Ubicación:** `anexo-e-declaraciones.tex:8-10`; `07-conclusions.tex:32-41`.
   La ética está correctamente limitada a ausencia de humanos y datos, pero un despliegue AMR involucra operarios, integradores, mantenimiento y responsables de seguridad funcional.
   **Acción:** añadir una subsección de stakeholders y hazards: caída de carga, atrapamiento, pérdida de comunicación, parada segura, recuperación manual, override, logging, ciberseguridad y autoridad para reanudar la misión.

### Auditoría SP3–SP4–SP5

| Interfaz | Qué demuestra | Qué todavía no demuestra |
|---|---|---|
| SP3: contacto/wrench | El residual basado en $G_S$ distingue capacidad escalar y fuerza/torque; la guardia global elimina falsos positivos condicionados (`modular-evidence-synthesis.tex:62-81`). | Fricción de Coulomb, normal de contacto medida, slip, compliance o cierre distribuido. Uniforme+guardia también alcanza cobertura completa. |
| SP4: aproximación y docking | Uniciclo dinámico, conversión a pares, saturación, CBF, integración sin teleportación y monitor barrido (`sp4-motion.tex:14-42`, `141-168`). | El contacto físico durante docking. Hay 73,15% de timeout para el mejor método y ningún caso excita saturación (`sp4-motion.tex:225-230`, `292-298`). |
| SP5: transporte | Planta Euler–Lagrange y separación RAW–SAFE–EXEC; colisión se decide sobre trayectoria ejecutada, sin reparar poses (`modular-evidence-synthesis.tex:87-127`). | Dinámica de rueda, agarre real, fricción, deformación, contacto 3D o pérdida de contacto. |
| A0–FULL | Ejecuta selección, mecánica, HOCBF y recuperación sobre una planta común; conserva fallos residuales (`physical-coalition-integrated.tex:1-10`, `49-55`). | Una ejecución física continua de SP3→SP4→SP5 ni reemplazo exclusivamente vecino. |

La semántica RAW–SAFE–EXEC es correcta y debería preservarse en hardware:

- RAW: orden nominal del controlador.
- SAFE: orden filtrada bajo el modelo de barrera.
- EXEC: wrench reconstruido a partir de actuadores/contactos realmente realizados.
- MEASURED, recomendable para HIL/hardware: wrench o aceleración estimados mediante encoders, IMU, corrientes y sensores de fuerza. Esta cuarta capa permitiría cuantificar la brecha EXEC-modelo frente a ejecución física.

### Python, CoppeliaSim, replay y hardware

| Canal | Estado defendible |
|---|---|
| Python numérico | Evidencia canónica de A0–FULL, SP4 y SP5. Incluye dinámica reducida, colisiones geométricas y campañas estadísticas. |
| CoppeliaSim | El manuscrito lo clasifica como inspección cualitativa separada (`04-methodology.tex:111-115`) y declara que SP5 v2 no lo usa (`anexo-b-reproducibilidad.tex:43-45`). La copia contiene escenas `.ttt` y un resultado SP4 V4, pero el cuerpo no establece su semántica ni su papel inferencial. |
| Replay/visualización | Válido para inspección de formación y trayectorias, no como validación dinámica independiente (`anexo-b-reproducibilidad.tex:12-16`). |
| HIL/hardware | No realizado y correctamente excluido del alcance. Debe ser el siguiente gate de validez, no una extrapolación verbal. |

### Factibilidad de transferencia

La transferencia es plausible como arquitectura de supervisión y auditoría, pero todavía no como controlador listo para planta. El orden recomendable es:

1. congelar 12–20 mundos representativos y reproducirlos en un motor dinámico independiente;
2. identificar masa, inercia, fricción rueda–suelo, latencia y saturación a partir de un AMR real;
3. ejecutar HIL con el mismo logging RAW–SAFE–EXEC;
4. realizar pruebas de docking y transporte con carga instrumentada;
5. incorporar abstención segura cuando SAFE no sea realizable;
6. solo después evaluar cierre vecinal y sustitución distribuida.

### Stakeholders, ética y futuro

Los stakeholders omitidos en la simulación —operario cercano, integrador WMS/MES, responsable de seguridad, mantenimiento y propietario de la carga— necesitan métricas distintas del éxito medio. Para ellos importan peor caso, distancia de parada, energía de impacto, probabilidad de caída, recuperación manual, tiempo fuera de servicio y trazabilidad de quién autorizó una sustitución.

El trabajo no presenta un problema de ética con participantes, pero sí un problema prospectivo de seguridad y responsabilidad. La futura prueba física debería utilizar un procedimiento de hazard analysis, límites de energía, zona segregada, E-stop independiente y criterios de suspensión. También conviene tratar pérdida o falsificación de mensajes como riesgo de ciberseguridad, no solo como dropout aleatorio.

### Questions for Authors

1. ¿El resultado `SP4_V4_COPPELIA_PAIRED_NARROW` es replay de trayectorias Python, controller-in-the-loop o una ejecución con dinámica/contacto activos? ¿Qué claim adicional autoriza?
2. ¿Cómo se transforma el contacto unilateral de SP3 en el agarre rígido bidireccional supuesto por SP5?
3. ¿Qué mecanismo obliga a abstenerse cuando el wrench SAFE no es realizable y EXEC volvería negativa la barrera?
4. ¿Cuál es el margen mínimo de fricción rueda–suelo y contacto–carga necesario para sostener las tasas A0–FULL?
5. ¿Qué sensores reales permitirían reconstruir EXEC y detectar slip, pérdida de agarre o saturación antes de una colisión?
6. ¿Cómo cambiaría el selector FULL si solo pudiera elegir reemplazos entre vecinos conectados y con información caducable?

### Minor Issues

- La Figura `fig-gap-literatura.tex:24-36` sugiere que “una misma ley” cierra quórum, capacidad, wrench y movimiento; el cuerpo demuestra una arquitectura por capas con cierres globales. Conviene armonizar la leyenda.
- Debe uniformarse “CBF”, “HOCBF” y “proyección discreta de barrera”; no son certificados intercambiables.
- La matriz de validación llama a SP4 “uniciclo dinámico” (`anexo-c-validacion.tex:42-47`); sería más preciso “modelo cinemático extendido con dinámica longitudinal/angular y saturación de par”.
- Añadir a la nomenclatura RAW, SAFE, EXEC, HIL y RSS.
- El paquete FULL combina mensajes, memoria y reemplazo; mantener visible que el efecto $+0,62$ no identifica contribuciones individuales (`physical-coalition-integrated.tex:39`).

## Editorial Decision

minor_revision
