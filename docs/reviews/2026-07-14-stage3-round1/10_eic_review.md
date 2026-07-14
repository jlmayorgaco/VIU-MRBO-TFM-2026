# EIC Review — Stage 3 Round 1

- **Rol:** Editor-in-Chief simulado de *Robotics and Autonomous Systems*, experto en coordinación multi-robot, autonomía distribuida y transferencia de formulaciones algorítmicas a sistemas ejecutables.
- **Commit revisado:** `1218a064`
- **Clausura TeX FH-v2:** `2fe96009eb6dbf047bc56e86c957410c1057a68da90ee7cedc3b03cc014abee6`
- **Fecha:** 2026-07-14
- **Nota de evidencia:** el PDF sellado no estaba disponible durante la revisión; todas las ubicaciones se citan mediante ruta y línea de la clausura TeX congelada o de sus artefactos verificables.

# Phase 1 — Precommitment

## Contract Paraphrase

**D1 — Trazabilidad problema-método-resultado.** Exigiré que la tesis central, cada pregunta o subproblema y cada contribución declarada formen una cadena editorialmente reconstruible entre problema, método, hipótesis, evidencia, resultado y límite. Una ambigüedad localizada será distinta de la ausencia de trazabilidad de la tesis o de varios subproblemas.

**D2 — Integridad claim-evidencia.** Comprobaré que la fuerza y el alcance de cada claim correspondan al tipo de evidencia que lo respalda, distinguiendo claramente demostración, simulación, replay, ejecución y propuesta. Las limitaciones deberán ser visibles, y ningún claim central podrá contradecir ni exceder materialmente la evidencia disponible.

**D3 — Corrección teórica.** Verificaré, desde la supervisión editorial, que los resultados sobre juegos, equilibrios, convergencia, condiciones KKT o primal-dual, CBF, mecánica y complejidad declaren sus supuestos y mantengan un alcance compatible con el algoritmo evaluado. Diferenciaré una laguna demostrativa acotable de un resultado central falso, circular, no demostrado o basado en hipótesis incompatibles.

**D4 — Originalidad y posicionamiento.** Evaluaré si la contribución propia queda delimitada mecanismo por mecanismo y resultado por resultado frente a Quijano, Martínez y el trabajo relacionado pertinente. Una combinación útil pero posicionada de manera difusa generará advertencia; presentar como novedosa una reproducción esencial de trabajo previo sin diferencia defendible constituirá bloqueo.

**D5 — Rigor experimental y estadístico.** Exigiré que baselines, información disponible, presupuestos, semillas, unidades experimentales, intervalos, tamaños de efecto, multiplicidad, ablaciones y criterios de éxito permitan atribuir los resultados principales. Las carencias parciales de potencia, precisión o controles se distinguirán de errores de diseño que invaliden la atribución central.

**D6 — Validez de sistema y alcance físico.** Comprobaré que el nivel de validación se etiquete con precisión y que se distingan álgebra, simulación propia, ejecución dinámica en CoppeliaSim, replay y hardware. También deberán declararse la semántica de seguridad discreta, las dependencias centralizadas y los límites de escalado, sin convertir evidencia parcial en una reclamación física, distribuida o de seguridad más amplia.

**D7 — Arquitectura narrativa y escritura.** Evaluaré si el documento articula una tesis única, una jerarquía reconocible y conclusiones proporcionadas, con densidad adecuada para un TFM de aproximadamente 18.812 palabras y 80 páginas. La extensión o repetición será advertencia cuando solo dificulte identificar el aporte; será bloqueo si la estructura impide reconstruir la tesis o introduce contradicciones internas sustantivas.

**D8 — Reproducibilidad e integridad bibliográfica.** Exigiré una relación auditable entre afirmaciones, configuraciones, artefactos y resultados, además de referencias reales y contextualmente pertinentes. Distinguiré metadatos o instrucciones localmente incompletos de la imposibilidad de reproducir resultados centrales o de referencias y atribuciones fabricadas o materialmente incorrectas.

## Scoring Plan

### D1: Trazabilidad problema-metodo-resultado

what_to_look_for: Correspondencia explícita entre objetivos, preguntas, contribuciones, métodos, hipótesis, resultados y límites; consistencia entre título, resumen, introducción, estructura de capítulos y conclusiones; localización concreta mediante secciones, páginas, tablas, figuras o artefactos.

what_triggers_block: La tesis central o varios subproblemas carecen de una cadena verificable hasta métodos y evidencia, o las conclusiones principales no pueden vincularse con resultados identificables.

what_triggers_warn: Uno o más enlaces están mezclados o formulados ambiguamente, pero la cadena principal puede recuperarse y corregirse mediante reorganización, tablas de trazabilidad o aclaraciones sin experimentos sustantivos nuevos.

### D2: Integridad claim-evidencia

what_to_look_for: Inventario de claims centrales y secundarios contrastado con su evidencia concreta; lenguaje que diferencie demostración, simulación, replay, ejecución y propuesta; correspondencia entre magnitud del claim, alcance empírico y limitaciones declaradas.

what_triggers_block: Un claim central contradice resultados identificables, omite evidencia adversa material o generaliza desde un tipo de evidencia que no puede sostener la validación reclamada.

what_triggers_warn: Existen sobreafirmaciones localizadas, etiquetas de evidencia ambiguas o límites poco visibles, pero pueden corregirse acotando el lenguaje y haciendo explícita la frontera de validez.

### D3: Correccion teorica

what_to_look_for: Definiciones consistentes; supuestos enumerados antes de resultados; alineación entre teoremas, pruebas y algoritmo ejecutado; alcance preciso de convergencia, equilibrio, KKT o primal-dual, CBF, mecánica y complejidad; tratamiento explícito de transiciones continuo-discreto y distribuido-centralizado.

what_triggers_block: Un resultado teórico central resulta falso, circular o no demostrado, o depende de supuestos incompatibles con el algoritmo o sistema al que se transfiere la garantía.

what_triggers_warn: Hay pasos demostrativos incompletos, condiciones omitidas o terminología imprecisa, pero el resultado puede acotarse o reformularse sin alterar la contribución principal.

### D4: Originalidad y posicionamiento

what_to_look_for: Declaración concisa del delta de conocimiento; comparación mecanismo por mecanismo y resultado por resultado con Quijano, Martínez y literatura pertinente; separación entre elementos heredados, combinaciones nuevas e interfaces o resultados propios.

what_triggers_block: La novedad central atribuida al trabajo reproduce esencialmente antecedentes identificables y no presenta una diferencia técnica, empírica o conceptual defendible.

what_triggers_warn: La combinación parece potencialmente valiosa, pero la contribución propia, su prioridad o la comparación con el estado del arte permanecen difusas y requieren reposicionamiento bibliográfico y conceptual.

### D5: Rigor experimental y estadistico

what_to_look_for: Equidad de baselines en información y presupuesto; definición de semillas y unidades experimentales; estructura de emparejamiento o anidamiento; intervalos, efectos y multiplicidad; ablaciones; criterios de éxito; timeouts; congelación del protocolo; sensibilidad y trazabilidad de resultados.

what_triggers_block: El diseño no permite atribuir las mejoras reclamadas, un comparador es materialmente inequitativo o existe un error estadístico o experimental que invalida los resultados principales.

what_triggers_warn: La evidencia conserva utilidad, pero faltan controles, comparaciones, sensibilidad, potencia, precisión o justificaciones estadísticas que pueden añadirse sin reconstruir toda la campaña.

### D6: Validez de sistema y alcance fisico

what_to_look_for: Etiquetado inequívoco de cada nivel de evidencia; separación entre simulación, replay, ejecución dinámica y hardware; correspondencia entre comandos y realización física; semántica de seguridad discreta; dependencias globales o centralizadas; condiciones de escalado y despliegue.

what_triggers_block: Se reclama como demostrada una validación física, distribuida o de seguridad central que el artefacto ejecutado no establece, o se atribuyen garantías de ejecución a evidencia puramente algebraica o simulada.

what_triggers_warn: La cadena es auditable y reproducible, pero la evidencia física, la independencia de validación, la localidad o el escalado son parciales y necesitan límites más visibles o validación adicional.

### D7: Arquitectura narrativa y escritura

what_to_look_for: Una tesis central formulable en una frase; jerarquía clara entre contribución principal y evidencia auxiliar; continuidad problema-contribución-resultados-conclusión; densidad, repetición y proporcionalidad; coherencia terminológica y ausencia de contradicciones internas.

what_triggers_block: La organización impide identificar o reconstruir la tesis central, secciones esenciales sostienen narrativas incompatibles o las conclusiones contradicen sustantivamente el cuerpo del trabajo.

what_triggers_warn: La acumulación de capas, extensión, repetición o cambios terminológicos oscurecen el aporte principal, aunque una reestructuración editorial pueda recuperar una narrativa coherente.

### D8: Reproducibilidad e integridad bibliografica

what_to_look_for: Correspondencia entre resultados, configuraciones, semillas, código, manifiestos y artefactos; instrucciones suficientes para repetir análisis; referencias verificables; atribuciones correctas y apoyo contextual efectivo de las citas.

what_triggers_block: Los resultados centrales no pueden reconstruirse desde los artefactos disponibles, o aparecen referencias fabricadas, inexistentes o atribuciones materialmente incorrectas que sostienen claims relevantes.

what_triggers_warn: Faltan metadatos, instrucciones, versiones, enlaces o verificaciones bibliográficas localizadas, pero los resultados y la base intelectual principal siguen siendo auditables.

[CONTRACT-ACKNOWLEDGED]

# Phase 2 — Review

## Dimension Scores

### D1: Trazabilidad problema-metodo-resultado

score: pass

La pregunta de investigación, las cuatro contribuciones, los objetivos, la jerarquía de hipótesis y la evidencia integrada/modular forman una cadena reconstruible. HC se decide con A0–FULL; H1–H6 explican etapas; H7–H8 quedan explícitamente fuera del plano confirmatorio. Las conclusiones responden objetivo por objetivo y declaran O3 como cumplimiento parcial. Evidencia: `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:27-47`, `docs/doc-05-final-report/sections/mainmatter/03-hypothesis.tex:12-29`, `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:102-119`, `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:3-15`.

No se activa mi trigger de `warn`: los enlaces no dependen de reconstrucción implícita ni requieren nuevos experimentos para entenderse. Tampoco se activa `block`: la tesis central y los subproblemas conducen a evidencia identificable.

### D2: Integridad claim-evidencia

score: warn

La prosa distingue con disciplina demostración, simulación, replay, ejecución y propuesta. El resumen limita el resultado a simulación planar y niega validación física, seguridad funcional o superioridad universal; la discusión conserva resultados positivos, negativos y no estimables. Además, la auditoría local verificó 142/142 claims internos y no encontró `MISMATCH`. Evidencia: `docs/doc-05-final-report/sections/frontmatter/01-summary.tex:2-10`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:38-53`, `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:18-31`, `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/empirical_claim_audit.md:15-27`.

El `warn` se activa por una sobreafirmación localizada y corregible: el título presenta “coordinación distribuida”, mientras la implementación integrada se define como instrumento centralizado con componentes distribuibles, cierres globales y reemplazo global. El resumen corrige esa lectura, pero el título sigue admitiendo una interpretación extremo a extremo que la evidencia no sostiene. Ubicaciones: `docs/doc-05-final-report/main.tex:21-26`, `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`. No es `block` porque la limitación aparece repetidamente y no oculta la naturaleza del artefacto.

### D3: Correccion teorica

score: pass

El manuscrito delimita las garantías por capa: ascenso de potencial para Smith con ocupación exacta, KKT/v-GNE solo para relajaciones convexas bajo Slater, seguridad condicionada a estado inicial seguro y autoridad realizable, e ISS práctica únicamente con matriz cerrada común, entrada acotada y ausencia de resets. Las verificaciones V1–V3 usan solucionadores o cálculos independientes y reportan errores numéricos. Evidencia: `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:164-228`, `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:19-83`, `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:85-115`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:75-138`, `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/empirical_claim_audit.md:110-117`.

No aparece un resultado central falso, circular o transferido a un algoritmo incompatible, ni una laguna demostrativa que exija `warn`.

### D4: Originalidad y posicionamiento

score: pass

La novedad no se atribuye a Smith, Nash, KKT, HOCBF ni a las dinámicas distribuidas heredadas. Se define como interfaz entre déficit, capacidad, contacto, `wrench` y ejecución; semántica de coalición física; y campaña acumulativa que revela interacciones no monótonas. La matriz de originalidad separa antecedente, delta, evidencia y límite frente a Quijano, Martínez y literatura contemporánea. Evidencia: `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:37-46`, `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:449-469`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:41-53`.

La auditoría de originalidad no encontró coincidencias pertinentes en 82 consultas ni copia textual del trabajo previo localizado: `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/originality_ai_modes.md:8-19`, `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/originality_ai_modes.md:404-416`. El delta es incremental-integrador, pero está suficientemente delimitado para no activar `warn`.

### D5: Rigor experimental y estadistico

score: warn

La unidad inferencial es el mundo; tratamientos, robots, cargas, contactos y frames se modelan como repetidos o anidados. A0–FULL usa mundos y `world_hash` compartidos, McNemar exacto, bootstrap pareado, Holm y extensión exclusivamente por precisión. Sus 20 contrastes se publican sin selección. Evidencia: `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:18-43`, `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:85-110`, `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/FINAL_RUN_MANIFEST.json:2-25`, `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/statistics/paired_contrasts_holm.csv:1-21`.

Se activa `warn`, no `block`, por controles todavía incompletos: no hay sensibilidad confirmatoria de los umbrales y ganancias de A0–FULL; el efecto A4–FULL empaqueta mensajes, memoria y reemplazo; SP7 no inyecta la red dentro del lazo y SP8 no mide recursos mediante watchdog común. Evidencia: `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:37-53`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:143-151`. Los resultados principales siguen siendo atribuibles dentro de la planta y calibración declaradas.

### D6: Validez de sistema y alcance fisico

score: warn

RAW, SAFE y EXEC están separados; la colisión se decide sobre la trayectoria ejecutada; CoppeliaSim no se presenta como hardware ni como validación dinámica independiente; y el presupuesto de centralización identifica cada operación global. Evidencia: `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-83`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:140-168`, `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:27-31`.

Se activa exactamente el trigger de `warn`: la cadena es reproducible, pero la validez física y de escalado sigue siendo parcial. Hay una única planta integrada planar, agarre rígido, red sintética, calibración puntual, ausencia de sensibilidad y ninguna validación independiente o hardware. FULL conserva además 14 % de colisiones en el régimen adverso. No se activa `block` porque el manuscrito no reclama que esas fronteras estén resueltas.

### D7: Arquitectura narrativa y escritura

score: pass

El documento mantiene una tesis reconocible —una asignación estratégica no equivale a coalición física— y jerarquiza A0–FULL como evidencia central frente a SP1–SP8 como explicación modular. La discusión crítica y la conclusión conservan la misma lectura sin convertir la extensión en una colección de campañas independientes. Evidencia: `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:27-47`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:1-14`, `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:3-43`.

Existen repeticiones entre resumen, validación, discusión, conclusiones y anexos, pero sirven principalmente a la trazabilidad de un TFM de 80 páginas y no impiden identificar el aporte. No alcanzan mi trigger de `warn`.

### D8: Reproducibilidad e integridad bibliografica

score: warn

A0–FULL y SP5 conservan freeze, apertura de semillas, manifiestos y hashes; la clausura TeX está ligada a FH-v2 `2fe96009…`; las 107 entradas bibliográficas existen, las 55 claves citadas aparecen en 97 usos y no quedan claves o contextos incorrectos. Evidencia: `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/protocol/frozen_manifest.json:2-18`, `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/audit/seed_opening.json:2-5`, `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/STAGE2_5_INTEGRITY_REPORT.md:14-28`.

Se activa `warn` por asimetrías localizadas: SP1–SP4 tienen trazabilidad variable; SP6–SP8 no satisfacen el cierre íntegro de A0–FULL/SP5; falta revisión citacional externa de otra familia y el informe institucional de similitud. Evidencia: `docs/doc-05-final-report/sections/anexo-e-declaraciones.tex:4-6`, `docs/doc-05-final-report/.aris/traces/integrity/2026-07-14_stage2_5/STAGE2_5_INTEGRITY_REPORT.md:42-48`. No hay trigger de `block`: los resultados centrales son reproducibles y no se encontraron referencias fabricadas o atribuciones materialmente erróneas.

## Failure Condition Checks

### F1: any mandatory dimension scores 'block'

fired: false

D1=`pass`, D2=`warn`, D3=`pass`; ninguna dimensión obligatoria tiene `block`.

### F2: two or more mandatory dimensions score 'warn' or worse

fired: false

Solo D2 tiene `warn`; D1 y D3 tienen `pass`.

### F3: any high-priority dimension scores 'block'

fired: false

D4–D8 no contienen ningún `block`.

### F4: any mandatory dimension scores 'warn'

fired: true

D2=`warn`. Acción asociada: `minor_revision`.

### F5: any high-priority dimension scores 'warn'

fired: true

D5, D6 y D8 tienen `warn`. Acción asociada: `minor_revision`.

### F0: every mandatory dimension scores 'pass'

fired: false

D2 no tiene `pass`.

La condición de mayor precedencia activada es F4 —empata en severidad 2 con F5 y aparece antes en el contrato—, por lo que la acción individual derivada es `minor_revision`.

## Review Body

### EIC Review Report

#### Reviewer Identity

Editor-in-Chief simulado de *Robotics and Autonomous Systems*, especialista en coordinación multi-robot, autonomía distribuida y transferencia de formulaciones algorítmicas a sistemas ejecutables.

#### Overall Recommendation

Minor Revision

#### Confidence Score

4/5 — alta confianza editorial tras revisar la clausura TeX completa y los artefactos centrales; la confianza no es 5 porque la validación física externa, el informe institucional de similitud y una auditoría citacional de otra familia no están disponibles.

#### Summary Assessment

El TFM propone una arquitectura escalonada para convertir preferencias multiagente en coaliciones capaces de transportar cargas heterogéneas, distinguiendo cardinalidad, capacidad, geometría de contacto, `wrench`, autoridad dinámica, seguridad y recuperación. Su contribución más convincente no es una nueva dinámica de juego aislada, sino la definición operacional de coalición física y la campaña A0–FULL, que ejecuta seis prefijos sobre una planta común y muestra que añadir una comprobación estática puede empeorar el transporte al retirar reserva dinámica. Esta interacción no monótona es relevante para lectores de coordinación multi-robot.

La memoria presenta una disciplina poco habitual en la separación entre teoría, simulación, ejecución y propuesta. Conserva resultados negativos, controles uniformes, timeouts y falsos positivos, y reconoce que sus cierres y reemplazos canónicos utilizan información global. La trazabilidad local de claims, contrastes y referencias es sólida.

Las reservas son acotadas pero importantes para aspirar a máxima calificación: el título puede sugerir distribución extremo a extremo; A0–FULL carece de sensibilidad confirmatoria y desagregación del paquete FULL; la evidencia física sigue limitada a simulación planar; y la profundidad reproducible es desigual fuera de A0–FULL/SP5. Son correcciones de posicionamiento, análisis y empaquetado, no una invalidación de la tesis.

#### Strengths

1. **Contribución central identificable y falsable.** La coalición física se define mediante etapas que separan aceptación y éxito ejecutado; A0–FULL es la evidencia principal, no una suma artificial de SP. Ubicación: `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:27-46`, `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:1-14`.

2. **Resultado negativo científicamente valioso.** A3 mejora torque en 0,60 pero reduce éxito en escasez en 0,18, mostrando que factibilidad estática y autoridad dinámica no son intercambiables. Ubicación: `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:37-55`; contraste canónico: `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/statistics/paired_contrasts_holm.csv:7-15`.

3. **Integridad inferencial y semántica.** La unidad experimental, emparejamiento, multiplicidad, timeouts y endpoints no estimables están definidos antes de interpretar resultados. Ubicación: `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:18-24`, `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:85-108`.

4. **Delimitación honesta de localidad y ejecución.** El presupuesto de centralización y la separación RAW–SAFE–EXEC evitan atribuir al algoritmo garantías que pertenecen a un cierre global o a una orden no realizable. Ubicación: `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-83`.

5. **Posicionamiento de novedad explícito.** La matriz de originalidad reconoce mecanismos heredados y sitúa el delta en interfaces, semántica y auditoría integrada. Ubicación: `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:449-469`.

#### Weaknesses

1. **Título más fuerte que la localidad demostrada.**
   **Problema:** “coordinación distribuida” puede leerse como arquitectura local extremo a extremo, aunque el artefacto integrado usa umbral, ranking, cierres y reemplazo globales.
   **Impacto:** crea una expectativa editorial que el resumen debe corregir inmediatamente.
   **Sugerencia:** cualificar el título —por ejemplo, “con componentes distribuidos y cierres globales auditados”— o incorporar esa delimitación en el subtítulo oficial.
   **Severidad:** moderada, requerida; `warn` D2.
   **Ubicación:** `docs/doc-05-final-report/main.tex:21-26`, `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`.

2. **Validez física externa todavía limitada.**
   **Problema:** una sola planta planar, agarre rígido, red sintética y ausencia de motor dinámico independiente o hardware.
   **Impacto:** impide traducir las tasas a seguridad funcional, prevalencia industrial o robustez física general.
   **Sugerencia:** convertir las limitaciones en una tabla compacta “claim–evidencia–frontera” y, si el calendario lo permite, añadir una validación congelada pequeña en motor independiente; no es necesario hardware para cerrar el TFM.
   **Severidad:** moderada; `warn` D6.
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:27-31`.

3. **Sensibilidad y atribución causal incompletas en A0–FULL.**
   **Problema:** los umbrales y ganancias están congelados, pero no se evalúa sensibilidad; A4–FULL empaqueta red, memoria y reemplazo.
   **Impacto:** se conoce el efecto del paquete, no su mecanismo individual ni estabilidad paramétrica.
   **Sugerencia:** añadir una sensibilidad predefinida de bajo coste o, como mínimo, una tabla de parámetros críticos y escenarios donde podría cambiar la conclusión; separar mensajes/memoria/reemplazo como futura ablación obligatoria.
   **Severidad:** moderada; `warn` D5.
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39-53`.

4. **Reproducibilidad desigual entre campañas.**
   **Problema:** A0–FULL y SP5 tienen cierre hashado completo, pero SP1–SP4 presentan trazabilidad variable y SP6–SP8 no satisfacen el mismo contrato.
   **Impacto:** la fuerza de auditoría de los resultados modulares no es uniforme.
   **Sugerencia:** entregar un índice único de campaña con versión, configuración, manifiesto, tabla canónica, hash y estado inferencial; marcar “no disponible” cuando corresponda.
   **Severidad:** moderada-baja; `warn` D8.
   **Ubicación:** `docs/doc-05-final-report/sections/anexo-e-declaraciones.tex:4-6`.

5. **Redundancia editorial residual.**
   **Problema:** algunos resultados y límites reaparecen en resumen, validación transversal, discusión, conclusiones y anexos.
   **Impacto:** aumenta densidad y dificulta convertir el TFM en artículo.
   **Sugerencia:** mantener en el cuerpo una sola tabla transversal y reservar el registro exhaustivo para anexos; para artículo, centrar el texto en A0–FULL y usar SP1–SP8 como ablaciones seleccionadas.
   **Severidad:** menor.
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:12-38`, `docs/doc-05-final-report/sections/anexo-c-validacion.tex:5-90`.

#### Journal / TFM Fit

Como TFM de ingeniería con aspiración a máxima calificación, el trabajo encaja muy bien: combina formulación, implementación, teoría, experimentación reproducible, resultados negativos y límites explícitos. Para *Robotics and Autonomous Systems*, el tema encaja plenamente, pero el manuscrito no es todavía un artículo directamente sometible: debería concentrarse en la coalición física y A0–FULL, reducir la escalera modular y reforzar validación independiente o sensibilidad.

#### Originalidad

La novedad es una integración metodológica y semántica defendible, no una teoría de juegos nueva. El delta más claro es demostrar, sobre la misma planta, que cerrar `wrench` estático puede reducir éxito al eliminar margen dinámico. Esa conclusión es específica, verificable y relevante.

#### Significancia

El trabajo ofrece un criterio útil para evitar falsos positivos entre MRTA y ejecución física. Su impacto inmediato es metodológico y diagnóstico para simulación multi-robot; su transferencia industrial permanece futura.

#### Structural Coherence

La jerarquía A0–FULL principal / SP1–SP8 modular funciona y las conclusiones regresan a objetivos e hipótesis. La densidad es alta, pero no destruye la tesis única.

#### Title & Abstract

El resumen y el abstract son informativos, cuantitativos y conservadores. El único desajuste editorial relevante es el uso no cualificado de “distribuida” en el título frente a los cierres globales declarados.

#### Conclusion

La conclusión responde a objetivos, distingue cumplimiento parcial y conserva resultados inconcluyentes. Es proporcional a la evidencia y no promete validación física, seguridad funcional ni superioridad universal.

#### Puntuación descriptiva 0–100

| Dimensión | Puntuación | Lectura |
|---|---:|---|
| Originalidad | 82 | Integración y resultado diagnóstico fuertes |
| Metodología | 75 | Diseño sólido; sensibilidad y controles externos incompletos |
| Evidencia | 75 | Amplia y trazable dentro del simulador; validez externa limitada |
| Coherencia | 86 | Tesis y jerarquía reconocibles |
| Escritura | 84 | Precisa y profesional, con redundancia residual |
| **Promedio ponderado** | **79,4** | Frontera superior de Minor Revision |

El promedio usa pesos 20/25/25/15/15 y es descriptivo; la decisión vinculante procede de las condiciones del contrato.

#### Questions for Authors

1. ¿Aceptaría el autor cualificar el título para que la deuda de localidad sea visible antes del resumen?
2. ¿Qué parámetros de A0–FULL considera capaces de invertir los efectos A2–A3 o A3–A4, y cuáles podrían someterse a una sensibilidad mínima congelada?
3. ¿Puede separar conceptualmente —o mediante una ablación adicional— los efectos de mensajes, memoria y reemplazo dentro de FULL?
4. ¿Puede consolidar en un único índice de entrega la trazabilidad exacta de SP1–SP8 y marcar explícitamente qué campañas no poseen cierre hashado completo?

#### Minor Issues

- Capitalizar “Tampoco” al iniciar la oración en `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:103`.
- Explicar una vez que el identificador técnico `FULL_ROBUST_LOCAL` conserva “LOCAL” por nomenclatura histórica aunque el selector use candidatos globales.
- Mantener junto al paquete de entrega el addendum de freeze, pues el YAML congelado conserva una bandera obsoleta: `results/physical_coalition/PHYSICAL_COALITION_CERTIFICATE_v1/INTEGRITY_ADDENDUM_2026-07-14.md:5-31`.
- No presentar el PASS local de citas como sustituto del informe institucional de similitud o de una revisión externa independiente.

## Editorial Decision

minor_revision

La decisión deriva mecánicamente de F4 y F5. No existen bloqueos en dimensiones obligatorias ni de alta prioridad, pero debe corregirse la ambigüedad localizada del claim “distribuida” y cerrarse documentalmente la sensibilidad, el alcance físico y la asimetría de reproducibilidad antes de considerar el TFM completamente listo.
