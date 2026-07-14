---
document: domain_review
reviewer_role: R2 — Dominio, teoría de juegos y robótica multiagente
stage: 3
round: 1
date: 2026-07-14
frozen_commit: 1218a06451f8e6b1f2c4624e49a601e492be5feb
frozen_commit_short: 1218a064
frozen_hash_scheme: FH-v2
frozen_hash_prefix: 2fe960
sealed_pdf_available: false
citation_policy: absolute frozen-worktree path plus line or section
phase0_phase1_reconstructed_after_context_compaction: true
mutation_policy: read-only review; no manuscript edits
---

# Phase 1 — Precommitment

> Nota de persistencia: esta Phase 1 fue reconstruida fielmente después de una compactación de contexto. Conserva la identidad, el alcance, D1–D8, los disparadores de puntuación, las condiciones F0–F5 y el disclosure emitidos; no se presenta como transcripción literal.

## Reviewer identity

- **Rol:** R2 — revisor de dominio en teoría de juegos y robótica multiagente.
- **Áreas:** juegos poblacionales, dinámica de Smith, juegos potenciales, Nash, KKT/v-GNE, optimización convexa/QP, control ISS, cooperación multi-robot, contacto y wrench, localidad y cierre distribuido.
- **Objeto congelado:** commit `1218a064`, FH-v2 prefijo `2fe960`.
- **PDF sellado:** no disponible.

## Blindness disclosure

Existe exposición previa al manuscrito. Durante esta Phase 1 no se accede al paper, sus resultados ni informes de revisión. No se leerán dictámenes de otros revisores ni una decisión editorial consolidada durante Phase 2. El juicio se emitirá contra los criterios fijados aquí y con evidencia localizada.

## Precommitted scoring dimensions

### D1 — Trazabilidad — mandatory

- **pass:** afirmaciones, cifras y conclusiones centrales pueden rastrearse a una fórmula, tabla, figura, artefacto o sección identificable; las capas RAW/CLOSED/SAFE/EXEC están distinguidas.
- **warn:** hay ambigüedades localizadas de versión, etiqueta o procedencia, pero el resultado central sigue siendo auditable.
- **block:** cifras incompatibles, resultado central sin fuente o confusión sistemática entre capas que impida auditar la tesis.

### D2 — Correspondencia afirmación–evidencia — mandatory

- **pass:** la fuerza de las afirmaciones coincide con el nivel de evidencia y se distinguen prueba, validación numérica, simulación, Coppelia y hardware.
- **warn:** existe sobreextensión localizada y corregible sin rehacer el núcleo experimental.
- **block:** se presenta simulación como validación física/hardware, causalidad sin control o superioridad general que la evidencia no permite.

### D3 — Corrección teórica — mandatory

- **pass:** Nash, potencial, Smith, KKT/v-GNE, QP e ISS son matemáticamente correctos bajo hipótesis explícitas; las garantías no se transfieren a cierres, resets o dinámicas distintas.
- **warn:** existe una omisión de hipótesis o derivación localizada, reparable sin alterar el resultado principal.
- **block:** error matemático central, falsa equivalencia, afirmación de convergencia no válida o extensión indebida del caso continuo al entero.

### D4 — Originalidad y posicionamiento — high

- **pass:** la novedad propia se separa de resultados heredados y se compara con los trabajos integrados más próximos.
- **warn:** la contribución es defendible, pero su identidad queda difusa entre arquitectura, integración y mecanismos estándar, o la comparación más cercana es insuficiente.
- **block:** la contribución principal se atribuye como nueva pese a ser estándar, o no puede distinguirse del estado del arte.

### D5 — Rigor experimental — high

- **pass:** hay baselines pertinentes, ablaciones, controles negativos, repeticiones, métricas y tolerancias adecuadas para las conclusiones.
- **warn:** falta una sensibilidad o control secundario, pero las conclusiones centrales siguen soportadas.
- **block:** el diseño no permite aislar el mecanismo central, carece de baseline indispensable o no es reproducible.

### D6 — Alcance físico y de sistema — high

- **pass:** contacto, wrench, saturación, dinámica, comunicaciones y hardware están correctamente modelados o delimitados.
- **warn:** simplificación física importante pero declarada, con impacto limitado en la tesis explícita.
- **block:** la conclusión física depende de una inconsistencia no reconocida o afirma seguridad/robustez fuera del modelo.

### D7 — Narrativa académica — high

- **pass:** tesis, preguntas, aportes, teoría, método, resultados y límites forman una progresión coherente y legible.
- **warn:** repetición, densidad o fragmentación local que dificulta la línea argumental sin volverla indeterminada.
- **block:** estructura desconectada que impide identificar aportes o relacionar resultados con preguntas e hipótesis.

### D8 — Reproducibilidad y bibliografía — high

- **pass:** versión, artefactos, parámetros, tolerancias y bibliografía permiten auditoría; las fuentes centrales son verificables y pertinentes.
- **warn:** ambigüedad menor de versión, artefacto o referencia que no cambia la evaluación central.
- **block:** artefactos centrales ausentes, bibliografía fabricada o versión canónica imposible de determinar.

## Precommitted theory checks

1. Verificar la definición de Nash y la diferencia entre equilibrio, estacionariedad y máximo de potencial.
2. Verificar la identidad de ascenso de potencial para Smith y sus condiciones de igualdad.
3. Comprobar si la equivalencia KKT/v-GNE exige convexidad, restricciones compartidas y Slater.
4. Separar la dinámica primal-dual exacta de Smith, replicador, BNN, consenso finito, redondeo y cierre heurístico.
5. Verificar que QP centralizado, guardia y cierre global no se describan como mecanismos locales.
6. Comprobar la desigualdad ISS, sus constantes y la hipótesis de dinámica fija, perturbación acotada y ausencia de resets.
7. Separar pasividad/Hamiltoniano nominal del sistema ejecutado con filtro y saturación.
8. Evaluar si capacidad escalar/cardinalidad se distingue de factibilidad geométrica y de wrench.
9. Comprobar que el cierre entero no herede garantías del juego continuo.
10. Determinar si la contribución original es un controlador, una arquitectura de integración o una semántica auditable de coalición física.

## Precommitted failure conditions

- **F1:** cualquier dimensión mandatory en `block` → `reject`.
- **F2:** al menos dos dimensiones mandatory en `warn` o peor por la mayoría → `major_revision`.
- **F3:** cualquier dimensión high en `block` por la mayoría → `major_revision`.
- **F4:** cualquier dimensión mandatory en `warn` → como mínimo `minor_revision`.
- **F5:** cualquier dimensión high en `warn` → como mínimo `minor_revision`.
- **F0:** todas las dimensiones mandatory en `pass` para todo el panel, y ninguna condición más severa activa → `accept`.

La precedencia será por severidad y después por orden contractual. Una media numérica alta no anulará un fallo ordinal.

## Planned review form

El informe de Phase 2 incluirá D1–D8 con evidencia, F0–F5, recomendación y confianza, resumen, tres a cinco fortalezas, tres a cinco debilidades con problema–impacto–sugerencia–severidad–ubicación, evaluación de literatura/teoría/argumento/contribución, preguntas, observaciones menores, tabla 0–100 y decisión editorial.

[CONTRACT-ACKNOWLEDGED]

# Phase 2 — Review

## Dimension Scores

| Dimensión | Score | Evidencia |
|---|---|---|
| D1. Trazabilidad | **pass** | La jerarquía epistémica separa algebra, simulación modular, campaña integrada y Coppelia; además, la metodología declara explícitamente qué mecanismos son locales y cuáles requieren información global en [methodology.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:53>) y [methodology.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:67>). |
| D2. Correspondencia afirmación–evidencia | **pass** | Las conclusiones reconocen que O3 solo se satisface parcialmente y no convierten las simulaciones en evidencia de hardware en [07-conclusions.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:10>) y [07-conclusions.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:29>). |
| D3. Corrección teórica | **pass** | La proposición de ascenso del potencial bajo dinámica de Smith es correcta y está acotada por sus hipótesis en [05-theoretical-framework/index.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:189>) y [05-theoretical-framework/index.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:226>). La derivación ISS y el alcance con dinámica fija están correctamente formulados en [integrated-theory-core.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:87>) y [integrated-theory-core.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:113>). La equivalencia KKT/v-GNE del SP4 se restringe correctamente al problema convexo, con Slater y dinámica primal-dual exacta en [sp4-motion.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:102>) y [sp4-motion.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:130>). |
| D4. Originalidad y posicionamiento | **warn** | El texto delimita honestamente que Smith, Nash, KKT, HOCBF y las restricciones compartidas no son novedosos en [01-introduction.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:46>). Sin embargo, la aportación game-theoretic queda dispersa: la campaña central A0–FULL no integra un buscador de Nash, y algunos baselines uniformes con cierre o guardia igualan o superan a variantes de juego en [modular-evidence-synthesis.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:60>) y [modular-evidence-synthesis.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:81>). |
| D5. Rigor experimental | **pass** | El diseño presenta ablaciones pareadas, controles negativos y desagrega efectos no monótonos. El propio texto evita atribuir a un único mecanismo el incremento del paquete FULL y documenta que A3 empeora el caso de escasez. |
| D6. Alcance físico y de sistema | **pass** | El alcance está bien delimitado: calibración integrada en un solo punto, modelo planar, contactos idealizados, sin robustez completa a saturación ni validación funcional de hardware. La limitación de calibración aparece en [physical-coalition-integrated.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:53>) y la ausencia de saturación de par en [sp4-motion.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:292>). |
| D7. Narrativa académica | **pass** | La progresión problema → semántica de coalición física → certificados → evidencia modular → campaña integrada → límites resulta coherente. La densidad es alta, pero las conclusiones no exceden la evidencia. |
| D8. Reproducibilidad y bibliografía | **pass** | Los informes técnicos contienen tolerancias, auditorías KKT/QP, semillas y resultados RAW/CLOSED/SAFE/EXEC. La validación algebraica documenta errores numéricos muy bajos en [report.md](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/results/theory_validation/report.md:5>). Persiste una ambigüedad menor entre SP4 v3 canónico y artefactos v4 confirmatorios. |

## Failure Condition Checks

- **F1 — Mandatory block:** no se activa.
- **F2 — Dos o más mandatory warn/block:** no se activa; D1–D3 son `pass`.
- **F3 — High block:** no se activa.
- **F4 — Mandatory warn:** no se activa.
- **F5 — High warn:** **se activa por D4**.
- **F0 — Todos los mandatory pass:** satisfecho para R2; la condición global queda pendiente de la agregación del panel. F5 tiene mayor severidad y determina la recomendación individual.

## Review Body

### Identidad y evaluación general

- **Revisor:** R2, teoría de juegos y robótica multiagente.
- **Recomendación:** **Minor Revision**.
- **Confianza:** **4/5**.
- **Disclosure:** existió exposición previa al manuscrito; esta evaluación siguió el compromiso de Phase 1. Se releyó íntegramente el cierre congelado y se inspeccionaron sus artefactos técnicos sin consultar informes de otros revisores ni la decisión editorial consolidada.

### Resumen

La TFM construye una tesis sólida: una coalición multi-robot no debe considerarse físicamente válida solo porque exista una asignación, un equilibrio o un número suficiente de agentes. Debe superar una cadena explícita de certificados de capacidad, contacto, wrench, seguridad dinámica, degradación de red y reemplazo. La campaña A0–FULL aporta un resultado particularmente valioso: añadir restricciones físicamente razonables puede reducir el éxito si elimina reserva de tracción, mientras mejora otros regímenes. Este resultado no monótono es más informativo que una simple comparación de rendimiento.

Las formulaciones de Smith, potencial, KKT/v-GNE, QP e ISS son técnicamente correctas y están delimitadas con una prudencia poco habitual. El manuscrito distingue correctamente la implementación centralizada de diagnóstico de los componentes potencialmente distribuibles y no presenta Coppelia como validación física independiente.

La revisión solicitada es principalmente de posicionamiento. La contribución más fuerte es una arquitectura auditable y una semántica operacional de “coalición física”, no un controlador game-theoretic integrado novedoso. Esa identidad debe aparecer todavía más nítida en el resumen, la introducción, la matriz de contribuciones y la síntesis final.

### Fortalezas

1. **Delimitación epistémica rigurosa.** Se diferencia entre prueba algebraica, evidencia numérica, simulación dinámica y reproducción cinemática.

2. **Teoría correctamente condicionada.** Nash, potencial exacto, dinámica de Smith, KKT/v-GNE e ISS no se extrapolan fuera de sus hipótesis.

3. **Resultado central no trivial.** La escalera A0–FULL muestra que “más física” no implica automáticamente “mejor desempeño”; revela conflictos entre factibilidad geométrica y reserva dinámica.

4. **Controles negativos útiles.** Los resultados donde uniform+closure o uniform+guard compiten con variantes de juego ayudan a separar el valor del mecanismo estratégico del valor del reparador global.

5. **Honestidad sobre localidad y hardware.** Los cierres globales, el reemplazo y las limitaciones del playback en Coppelia están declarados explícitamente.

### Debilidades y revisiones requeridas

#### 1. Identidad game-theoretic insuficientemente integrada

- **Problema:** la campaña física central A0–FULL utiliza utilidad, cuantiles, quórum, cierres y guardias, pero no incorpora un proceso de búsqueda de Nash claramente definido.
- **Impacto:** el lector puede interpretar que la evidencia física valida un controlador basado en juegos, cuando valida principalmente una arquitectura de certificados y reparación.
- **Sugerencia:** añadir una tabla sintética que indique, para cada experimento, jugadores, acciones, utilidad/potencial, dinámica de revisión, noción de equilibrio, mecanismo de cierre y grado de localidad. Si A0 no es un juego formal, declararlo de manera inequívoca.
- **Severidad:** moderada; revisión conceptual obligatoria, sin requerir nuevos experimentos.
- **Ubicación:** introducción, contribuciones, metodología A0–FULL y síntesis de resultados.

#### 2. La derivación completa de SP3 no forma parte del documento compilado

- **Problema:** el manuscrito afirma la correspondencia KKT/v-GNE, pero la formulación completa de jugadores, función potencial, multiplicadores y dinámica proyectada permanece en `sp3-wrench.tex`, fuera del cierre compilado.
- **Impacto:** un lector no puede auditar la afirmación central del SP3 únicamente desde la TFM.
- **Sugerencia:** incorporar en el marco teórico o en un anexo una proposición breve con problema primal, potencial, restricciones compartidas, KKT, hipótesis de Slater y alcance exclusivamente continuo.
- **Severidad:** moderada.
- **Ubicación:** síntesis SP3 en [modular-evidence-synthesis.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:81>) y derivación fuente en [sp3-wrench.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp3-wrench.tex:105>).

#### 3. La matriz de originalidad necesita comparación mecanismo por mecanismo

- **Problema:** existe una buena declaración de herencia teórica, pero la novedad respecto de los trabajos integrados más cercanos queda descrita principalmente en prosa.
- **Impacto:** dificulta identificar qué es exactamente nuevo: semántica de coalición, cadena de certificados, auditoría RAW/CLOSED, integración o controlador.
- **Sugerencia:** añadir una matriz comparativa con ejes de localidad, cierre entero, wrench/contacto, seguridad dinámica, reemplazo, validación física y trazabilidad RAW/SAFE/EXEC.
- **Severidad:** moderada.
- **Ubicación:** matriz de herencia en [05-theoretical-framework/index.tex](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:453>).

#### 4. Faltan algunas referencias fundacionales en el recorrido compilado

- **Problema:** las referencias de cierre de agarre aparecen en la bibliografía o en el material SP3, pero no respaldan directamente la sección compilada; la noción de ISS tampoco dispone de una referencia fundacional.
- **Impacto:** reduce la profundidad histórica de dos puentes teóricos importantes.
- **Sugerencia:** citar explícitamente [Ferrari y Canny, “Planning Optimal Grasps”](https://doi.org/10.1109/ROBOT.1992.219918), [Bicchi, “On the Closure Properties of Robotic Grasping”](https://journals.sagepub.com/doi/abs/10.1177/027836499501400402) y [Sontag, “Input to State Stability: Basic Concepts and Results”](https://link.springer.com/book/10.1007/978-3-540-77653-6).
- **Severidad:** menor.
- **Ubicación:** contacto/wrench, cierre de agarre y proposición ISS.

#### 5. Etiquetado canónico de SP4

- **Problema:** `STATUS.md` identifica v3 como canónico, mientras el repositorio contiene resultados v4 confirmatorios.
- **Impacto:** un auditor puede no saber qué conjunto sustenta exactamente las cifras de la TFM.
- **Sugerencia:** marcar los experimentos v4 como suplementarios/no canónicos en el manifiesto o promoverlos formalmente con una justificación y actualización completa de trazabilidad.
- **Severidad:** menor.
- **Ubicación:** [STATUS.md](<C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/results/sp4/STATUS.md:3>).

### Evaluación teórica específica

- **Nash y potencial:** correctos. La condición estacionaria de Smith se vincula adecuadamente con estrategias soportadas de pago máximo; no se afirma convergencia universal del estado.
- **KKT/v-GNE:** válida para los juegos convexos continuos con restricciones compartidas y regularidad indicada. No debe extenderse al redondeo entero, guardias o cierres heurísticos.
- **QP:** la equivalencia potencial–QP y las verificaciones numéricas son consistentes; el QP centralizado debe seguir presentado como benchmark o cierre global.
- **ISS:** la desigualdad es correcta para matriz y ganancias fijas con perturbación acotada. Los cambios de masa, topología, reset o modo híbrido requieren resultados adicionales y el texto ya lo reconoce.
- **Localidad:** la distinción es correcta. En particular, cierre, guardia, cuantiles globales y reemplazo global impiden caracterizar la cadena completa como plenamente distribuida.
- **Wrench y contacto:** la tesis acierta al mostrar que capacidad escalar y cardinalidad no garantizan factibilidad geométrica ni equilibrio de wrench.
- **Contribución:** el aporte principal defendible es metodológico y de integración auditable; la novedad de cada dinámica de juego por separado es deliberadamente limitada.

### Preguntas para los autores

1. ¿A0 pretende representar un juego discretizado o una política diagnóstica de asignación? Si es juego, faltan jugadores, acciones, utilidad y noción de equilibrio; si no, conviene decirlo expresamente.
2. ¿Por qué la derivación formal de SP3 permanece fuera del documento compilado?
3. ¿Cuál es el criterio verificable para mantener SP4 v3 como canónico frente a los experimentos v4 confirmatorios?

### Observaciones menores

- Diferenciar de forma consistente “potencial de utilidad” y “función de coste” en SP4.
- Reservar “convergencia” para la dinámica primal-dual exacta; para Smith, BNN o consenso finito hablar de dinámica evaluada o evidencia empírica.
- No denominar “precio” a todo residual de fuerza/par: los precios formales son multiplicadores duales.
- Definir inmediatamente “QR” como redondeo de quórum para evitar confusión con factorización QR.

### Evaluación cuantitativa

| Criterio | Peso | Nota /100 |
|---|---:|---:|
| Originalidad | 15 % | 72 |
| Rigor metodológico | 25 % | 90 |
| Suficiencia de evidencia | 20 % | 91 |
| Coherencia argumental | 15 % | 88 |
| Calidad de escritura | 10 % | 86 |
| Integración bibliográfica | 10 % | 84 |
| Importancia e impacto | 5 % | 86 |
| **Promedio ponderado** | **100 %** | **86.0** |

La nota cuantitativa refleja una TFM fuerte. La recomendación ordinal queda determinada por el `warn` de D4 conforme al contrato.

## Editorial Decision

**minor_revision**
