# Editorial Decision Letter y Revision Roadmap — Stage 3, Round 1

## Información del expediente

- **Objeto revisado por el panel:** TFM congelado en el commit `1218a064`.
- **Clausura TeX:** FH-v2 `2fe96009eb6dbf047bc56e86c957410c1057a68da90ee7cedc3b03cc014abee6`.
- **Fecha de decisión:** 2026-07-14.
- **Panel:** EIC, R1 Metodología, R2 Dominio, R3 Perspectiva de sistemas y Devil's Advocate (DA).
- **Contrato vinculante:** `tfm-reviewer-full-bulletproof-v1`, `panel_size = 5`.
- **Alcance de esta síntesis:** exclusivamente los cinco informes de Stage 3 Round 1. No se introducen hallazgos nuevos. Las ubicaciones temporales o abreviadas de los informes se normalizan a rutas committed.

## Decisión

### `minor_revision`

Estimado autor:

El panel considera que el TFM posee una tesis reconstruible, teoría correctamente condicionada, una campaña integrada valiosa y una delimitación inusualmente explícita entre demostración, simulación, replay, ejecución y propuesta. Los cuatro revisores no adversariales recomiendan **Minor Revision** y ninguno de los cinco asigna `block` a dimensión alguna.

La revisión es necesaria porque persisten advertencias localizadas en integridad claim–evidencia, atribución del efecto al componente game-theoretic, sensibilidad paramétrica, alcance físico y uniformidad de la trazabilidad reproducible. El DA no identifica hallazgos `CRITICAL`; sus cinco objeciones `MAJOR` reducen el alcance defendible de la contribución, pero no invalidan la campaña ni activan por sí solas una acción más severa. Se conservan abajo como revisiones P1/P2 cuando están corroboradas.

La acción editorial no procede de una media ni de una impresión global. F4 y F5 se activan con severidad 2; al empatar, F4 prevalece por aparecer antes en el contrato. F1, F2 y F3 no se activan, y F0 no se cumple. Por ello la decisión mecánica vinculante es `minor_revision`.

## Matriz contractual D1–D8

| Dimensión | EIC | R1 | R2 | R3 | DA |
|---|---|---|---|---|---|
| D1 Trazabilidad problema–método–resultado | pass | warn | pass | pass | pass |
| D2 Integridad claim–evidencia | warn | warn | pass | pass | warn |
| D3 Corrección teórica | pass | pass | pass | pass | pass |
| D4 Originalidad y posicionamiento | pass | pass | warn | pass | warn |
| D5 Rigor experimental y estadístico | warn | warn | pass | warn | warn |
| D6 Validez de sistema y alcance físico | warn | pass | pass | warn | warn |
| D7 Arquitectura narrativa y escritura | pass | pass | pass | pass | warn |
| D8 Reproducibilidad e integridad bibliográfica | warn | warn | pass | warn | pass |

Para `N = 5`, el contrato fija: `any ≥ 1`, `majority ≥ ceil(5/2)+1 = 4` y `all = 5`.

## Evaluación mecánica F1–F5 y F0

| Condición | Predicado por revisor | Cuantificador | Resultado | Severidad | Acción |
|---|---|---|---|---:|---|
| F1: alguna mandatory en `block` | 0/5 | any ≥ 1 | **false** | 4 | reject |
| F2: dos o más mandatory en `warn` o peor | R1; 1/5 | majority ≥ 4 | **false** | 3 | major_revision |
| F3: alguna high-priority en `block` | 0/5 | majority ≥ 4 | **false** | 3 | major_revision |
| F4: alguna mandatory en `warn` | EIC, R1, DA; 3/5 | any ≥ 1 | **true** | 2 | minor_revision |
| F5: alguna high-priority en `warn` | EIC, R1, R2, R3, DA; 5/5 | any ≥ 1 | **true** | 2 | minor_revision |
| F0: todas las mandatory en `pass` | R2, R3; 2/5 | all = 5 | **false** | 1 | accept |

**Resolución de precedencia:** las condiciones activadas de mayor severidad son F4 y F5, ambas con severidad 2. El desempate ordinal favorece F4. **Decisión editorial: `minor_revision`.**

## Resumen de revisores

| Revisor | Recomendación | Confianza declarada | Punto rector |
|---|---|---|---|
| EIC | Minor Revision | 4/5 | Contribución sólida; cualificar localidad, sensibilidad, alcance físico y cierre reproducible. |
| R1 Metodología | Minor Revision | 0,90 (alta) | Resolver MARL/O5, stopping rule, alineación estimando–prueba–IC y registro de artefactos. |
| R2 Dominio | Minor Revision | 4/5 | Presentar el aporte como arquitectura auditable, no como controlador game-theoretic novedoso. |
| R3 Sistemas | Minor Revision | 4/5 | Delimitar el puente Python–Coppelia–HIL–hardware, contacto y sensibilidad. |
| DA | Minor Revision | severidad 2 | La explicación rival atribuye el rendimiento a cierres y salvaguardas globales más que al juego. |

## Consenso, desacuerdos y arbitraje

### Consenso de los cuatro revisores no adversariales

- **[CONSENSUS-4] Decisión:** EIC, R1, R2 y R3 recomiendan Minor Revision; ninguno observa un defecto fundacional.
- **[CONSENSUS-4] D3:** los cuatro califican la corrección teórica como `pass`; Nash/Smith, KKT/v-GNE, HOCBF e ISS están condicionados por sus supuestos.
- **[CONSENSUS-4] D7:** los cuatro califican la arquitectura narrativa como `pass`; la jerarquía A0–FULL/SP1–SP8 permite reconstruir la tesis.
- **[CONSENSUS-3] D1:** EIC, R2 y R3 califican `pass`; R1 disiente por la trazabilidad incompleta de O5/MARL-CTDE. **Arbitraje:** conservar la valoración global positiva, pero exigir R2 antes del cierre.
- **[CONSENSUS-3] D4:** EIC, R1 y R3 califican `pass`; R2 advierte que la identidad game-theoretic no queda integrada en A0–FULL. **Arbitraje:** la originalidad es defendible como integración/diagnóstico, condicionada a R1.
- **[CONSENSUS-3] D5:** EIC, R1 y R3 califican `warn`; R2 califica `pass`. **Arbitraje:** prevalece la pericia metodológica y de sistemas; se exige delimitar robustez y resolver la inferencia en R3–R5.
- **[CONSENSUS-3] D8:** EIC, R1 y R3 califican `warn`; R2 califica `pass` con una ambigüedad canónica menor. **Arbitraje:** exigir un registro único y marcar ausencias, sin declarar irreproducible el núcleo.

### Desacuerdos

1. **D2, existencia de sobrealcance (2–2).** EIC y R1 asignan `warn` por “distribuida” y MARL/O5; R2 y R3 asignan `pass` porque los límites aparecen explícitos. **Tipo:** existencia/severidad. **Arbitraje:** corrección documental obligatoria en R1–R2; no se requieren experimentos para este punto.
2. **D6, suficiencia del alcance físico (2–2).** EIC y R3 asignan `warn`; R1 y R2 asignan `pass` por la delimitación honesta. **Tipo:** severidad/perspectiva. **Arbitraje:** exigir matriz de modalidades y claims en R6; mantener Coppelia/HIL/hardware como P2, no como condición de aceptación menor.

### Hallazgos del Devil's Advocate

- **DA-CRITICAL:** ninguno.
- **DA-MAJOR 1, atribución causal al juego:** corroborado por R2 y por las reservas EIC/R1/R3 sobre FULL empaquetado. Se resuelve en R1 y R4.
- **DA-MAJOR 2, ausencia de localidad extremo a extremo:** corroborado en existencia por EIC, R2 y R3, aunque difieren en severidad. Se resuelve documentalmente en R1; implementación distribuida queda en R9.
- **DA-MAJOR 3, sensibilidad y diversidad de plantas:** corroborado por EIC, R1 y R3. Se resuelve como límite obligatorio en R5 y experimento recomendado en R8.
- **DA-MAJOR 4, garantía física inferior a la retórica de seguridad:** corroborado por EIC y R3; R1/R2 consideran suficientes los límites actuales. Se resuelve en R6 y R9.
- **DA-MAJOR 5, equilibrio como lente diagnóstica:** corroborado por R2 y por los controles negativos citados por el panel. Se resuelve en R1.

## Required Revisions — P1

### R1 — Reposicionar contribución, causalidad y localidad

- **Fuentes:** EIC W1/W3; R2 D4 y debilidades 1/3; R3 minor issues; DA MAJOR 1/2/5 y MINOR 1–3.
- **Ubicación:** `docs/doc-05-final-report/main.tex:21-26`; `docs/doc-05-final-report/sections/mainmatter/01-introduction.tex:37-46`; `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`; `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:449-469,521-527`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:17-34,60,69-81`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:29-31`.
- **Problema:** la evidencia sostiene una arquitectura híbrida auditable, pero no causalidad aislada del juego ni localidad extremo a extremo; FULL agrupa mensajes, memoria y reemplazo.
- **Acción:** cualificar título y claims; declarar si A0 es juego formal o política diagnóstica; incorporar tabla por experimento con generador, jugadores/acciones, cierre, guardia, recuperación, localidad y claim autorizado; describir incrementos acumulativos como efectos del paquete.
- **Acceptance criteria:** título, resumen, introducción y conclusiones usan una terminología consistente (`híbrida`, `semi-distribuida` o equivalente justificado); ningún claim atribuye a un mecanismo individual un efecto del paquete; la tabla permite distinguir juego, cierre y salvaguarda; el resultado uniforme/QR/guard aparece como límite central.

### R2 — Cerrar la trazabilidad de O5 y MARL-CTDE

- **Fuente:** R1 D1/D2, debilidad 1 y preguntas 1.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:513-519`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:8-10`.
- **Problema:** el texto promete comparadores aprendidos/MARL-CTDE y declara O5 cubierto sin identificar modelo, entrenamiento, checkpoint, presupuesto o resultado.
- **Acción:** aportar una tabla completa algoritmo–observaciones–entrenamiento–semillas–checkpoint–presupuesto–resultado–artefacto, o retirar MARL/aprendidos del conjunto ejecutado y ajustar O5.
- **Acceptance criteria:** cada mención a MARL o método aprendido enlaza a evidencia reproducible, o queda rotulada como propuesta/no ejecutada; la conclusión sobre O5 coincide exactamente con ese estado.

### R3 — Justificar la regla de extensión 40–60–100

- **Fuente:** R1 D5, debilidad 2 y pregunta 2.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:102-110`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:4-6`.
- **Problema:** el tamaño final depende de la anchura bootstrap observada; la cobertura y el FWER bajo esa regla no están demostrados.
- **Acción:** adoptar `n` fijo, inferencia secuencial válida o simulación que evalúe cobertura y error familiar bajo la regla completa.
- **Acceptance criteria:** la opción elegida está especificada antes de interpretar resultados; existe artefacto o derivación verificable; todos los IC, `p` y ajustes Holm finales usan la misma regla justificada.

### R4 — Alinear estimando, prueba e intervalo

- **Fuente:** R1 D5, debilidad 3, preguntas 3–4 y comentario menor sobre SP4.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:85-96`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:96-104`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:249-258`.
- **Problema:** Wilcoxon unilateral e IC bootstrap de diferencia media pueden responder a parámetros distintos.
- **Acción:** añadir tabla por contraste con estimando, dirección, estadístico, IC, remuestreos, semillas y regla decisoria; explicar cualquier divergencia entre `p` e IC.
- **Acceptance criteria:** cada contraste tiene una fila completa y reproducible; la prosa no interpreta `p` e IC como si midieran el mismo parámetro cuando no lo hacen.

### R5 — Delimitar sensibilidad y robustez paramétrica

- **Fuentes:** EIC D5/W3; R1 D5/W4; R3 D5/W3; DA MAJOR 3.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:102-110`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:49-53`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:27-31`.
- **Problema:** los efectos se obtienen en una planta y calibración puntuales sin sensibilidad confirmatoria.
- **Acción:** incorporar una tabla de parámetros críticos, intervalo plausible, mecanismo afectado y riesgo de inversión; condicionar explícitamente los claims a la calibración. Si se ejecuta el barrido de R8, enlazar sus artefactos.
- **Acceptance criteria:** ningún resultado se presenta como robusto fuera de la calibración evaluada sin evidencia; la tabla cubre al menos fricción, masa/inercia, `dt`, horizonte, radio, HOCBF, fuerza/par y retardos o explica por qué alguno no aplica.

### R6 — Matriz de modalidad, evidencia física y seguridad

- **Fuentes:** EIC D6/W2; R3 D6/W1–W4; DA MAJOR 4; R1/R2 como posiciones favorables a la delimitación existente.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/02-objectives.tex:18-22`; `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:77-119`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:292-309`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:87-127`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:27-41`; `docs/doc-05-final-report/sections/anexo-b-reproducibilidad.tex:41-45`.
- **Problema:** Python, CoppeliaSim, replay, HIL y hardware no autorizan los mismos claims; la saturación, contacto y seguridad continua no están validados de forma equivalente.
- **Acción:** añadir matriz modalidad–motor–dinámica–controlador–sensores–entradas–outputs–hash–claim autorizado; clasificar expresamente el resultado Coppelia SP4 V4.
- **Acceptance criteria:** cada modalidad tiene claim y límite inequívocos; Coppelia queda identificado como replay, controller-in-the-loop o dinámica cerrada; cero colisiones discretas no se equipara a seguridad funcional o invariancia continua; hardware/HIL permanecen no realizados si no hay evidencia nueva.

### R7 — Registro único claim–artefacto y estado canónico

- **Fuentes:** EIC D8/W4; R1 D8/W5; R2 D8/debilidad 5; R3 D8; DA MINOR 4.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:111-119`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:1-4`; `docs/doc-05-final-report/sections/anexo-b-reproducibilidad.tex:18-49`; `docs/doc-05-final-report/sections/anexo-e-declaraciones.tex:4-6`; `results/sp4/STATUS.md:3`.
- **Problema:** A0–FULL/SP5 tienen cierre fuerte, pero la escalera modular presenta metadatos y versiones desiguales, incluida la ambigüedad SP4 v3/v4.
- **Acción:** publicar un registro único para A0–FULL y SP1–SP8: claim, tabla/figura, configuración, semillas, comando, manifiesto, hash, versión y estado canónico; usar `no disponible` cuando corresponda.
- **Acceptance criteria:** todo claim cuantitativo central resuelve a una única versión y artefacto; SP4 v3/v4 queda inequívocamente clasificado; no hay celdas vacías silenciosas.

## Suggested Revisions — P2/P3

### R8 — Sensibilidad confirmatoria acotada (P2)

- **Fuentes:** EIC W3; R1 W4; R3 W3; DA MAJOR 3.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:49-53`.
- **Problema:** R5 delimita el alcance, pero no prueba estabilidad paramétrica.
- **Acción:** ejecutar un barrido congelado, pareado y pequeño sobre los parámetros de mayor riesgo, reportando efectos e interacciones.
- **Acceptance criteria:** protocolo, mundos, semillas, matriz paramétrica y outputs están congelados y enlazados; se informa región de factibilidad y cualquier inversión de efecto. Si no se adopta, responder con justificación y conservar los límites de R5.

### R9 — Puente dinámico, contacto y despliegue (P2)

- **Fuentes:** R3 W1/W2/W4/W5; EIC W2; DA MAJOR 2/4.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:5-42,292-309`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:87-127`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:32-41`.
- **Problema:** la cadena SP3–SP5 presupone docking, agarre, fricción y transferencia que aún no se ejecutan como secuencia física continua.
- **Acción:** proponer o ejecutar gate progresivo Coppelia dinámico → HIL → AMR, con contacto unilateral, fricción/slip, saturación, abstención segura y hazards/stakeholders.
- **Acceptance criteria:** si se adopta, cada gate tiene criterio de entrada/salida y artefacto; si queda como futuro, el texto no lo presenta como validado y explicita caída de carga, atrapamiento, pérdida de red, E-stop y recuperación manual.

### R10 — Derivación, figuras, referencias y edición final (P3)

- **Fuentes:** R2 debilidades 2/4 y observaciones; EIC W5/minor issues; R3 minor issues; DA MINOR 1–3.
- **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp3-wrench.tex:105`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:81,103`; `docs/doc-05-final-report/figures/fig-gap-literatura.tex:24-42`; `docs/doc-05-final-report/figures/fig-equilibrio-nash-smith.tex:42-44`; `docs/doc-05-final-report/figures/fig-sota-transporte-cooperativo.tex:33-43`.
- **Problema:** la derivación SP3 no está plenamente visible en el compilado; algunas figuras y términos son más fuertes que la síntesis; faltan apoyos fundacionales y queda redundancia editorial.
- **Acción:** incorporar una proposición SP3 breve; armonizar figuras y nomenclatura; añadir referencias fundacionales propuestas por R2; corregir redundancias y erratas.
- **Acceptance criteria:** el PDF compilado permite auditar SP3 sin archivo excluido; figuras representan generador–cierre–guardia–recuperación; Smith/BNN/KKT/CBF/HOCBF/RAW/SAFE/EXEC se usan consistentemente; se corrige “Tampoco” en `modular-evidence-synthesis.tex:103`.

## Revision Roadmap verificable

### P1 — Obligatorio para cerrar Minor Revision

- [ ] **R1** Posicionamiento, causalidad, localidad y tabla de mecanismos completados.
- [ ] **R2** O5/MARL respaldado por artefacto o retirado del conjunto ejecutado.
- [ ] **R3** Regla 40–60–100 validada o sustituida.
- [ ] **R4** Tabla estimando–prueba–IC completa y reproducible.
- [ ] **R5** Claims condicionados a calibración y tabla de parámetros críticos incluida.
- [ ] **R6** Matriz de modalidades y semántica Coppelia/safety incluida.
- [ ] **R7** Registro claim–artefacto y versión canónica publicado.

### P2 — Responder: adoptar o justificar

- [ ] **R8** Sensibilidad confirmatoria ejecutada, o justificación explícita con límites R5 conservados.
- [ ] **R9** Gate dinámico/contacto/despliegue ejecutado o convertido en plan futuro verificable sin sobreclaim.

### P3 — Mejora editorial

- [ ] **R10** Derivación SP3, figuras, referencias, nomenclatura y erratas revisadas.

### Entrega y plazo

- **Plazo recomendado:** cuatro semanas, hasta 2026-08-11.
- **Respuesta:** carta punto por punto con los IDs R1–R10, acción adoptada o justificación, nueva ubicación y evidencia de verificación.
- **Gate editorial:** todos los R1–R7 deben satisfacer sus acceptance criteria; R8–R9 requieren respuesta explícita; R10 se verificará en la pasada editorial.

## Preguntas para el autor

1. ¿A0 es un juego formal o una política diagnóstica de asignación?
2. ¿Qué campaña, checkpoint y presupuesto corresponden exactamente a MARL-CTDE?
3. ¿Cómo se garantiza cobertura/FWER bajo la regla 40–60–100?
4. ¿Qué estimando y semilla bootstrap corresponden a cada contraste?
5. ¿El resultado Coppelia SP4 V4 es replay, controller-in-the-loop o dinámica cerrada, y cuál versión SP4 es canónica?
6. ¿Qué parámetros podrían invertir A2–A3 o A3–A4 y cuáles se someterán a sensibilidad?
7. ¿Cómo se transforma el contacto unilateral SP3 en el agarre rígido SP5 y cuándo debe abstenerse SAFE si EXEC no es realizable?

## R&R Traceability Seed

Los IDs siguientes son estables y no deben renumerarse en la respuesta ni en la re-review.

| ID estable | Prioridad | Dimensión/Fallo | Evidencia de cierre esperada | Regla de verificación futura |
|---|---|---|---|---|
| R1 | P1 | D2/D4/D5/D6; F4/F5 | Diff de título/claims + tabla de mecanismos/localidad | Confirmar terminología consistente y ausencia de atribución causal no aislada. |
| R2 | P1 | D1/D2; F4 | Tabla y artefactos MARL, o diff de retirada/O5 | Cada claim aprendido debe resolver a evidencia o estar rotulado no ejecutado. |
| R3 | P1 | D5; F5 | Protocolo y artefacto de validación del stopping rule | Recalcular que IC y FWER corresponden a la regla usada. |
| R4 | P1 | D5; F5 | Tabla estimando–test–IC–semillas | Muestrear contrastes y verificar coherencia de estimando e interpretación. |
| R5 | P1 | D5/D6; F5 | Tabla de parámetros y diff de claims condicionados | Buscar lenguaje de robustez y comprobar que esté respaldado o acotado. |
| R6 | P1 | D2/D6; F4/F5 | Matriz de modalidades y clasificación Coppelia | Verificar un claim autorizado y un límite por modalidad. |
| R7 | P1 | D8; F5 | Registro machine-readable y tabla legible | Trazar una muestra de claims a configuración, semilla, hash y versión canónica. |
| R8 | P2 | D5/D6; F5 | Protocolo/outputs de sensibilidad o justificación | Si se adopta, reproducir matriz; si no, verificar que R5 permanezca íntegro. |
| R9 | P2 | D6; F5 | Artefactos de gate o plan futuro con hazards | Confirmar que evidencia futura no se describa como ya realizada. |
| R10 | P3 | D3/D7/D8 | PDF recompilado, figuras y bibliografía | Auditar SP3, terminología, referencias y errata señalada. |

### Plantilla mínima de respuesta R&R

| ID | Respuesta del autor | Cambio realizado | Nueva ubicación | Evidencia/artefacto | Estado solicitado |
|---|---|---|---|---|---|
| R1–R10 | Pendiente | Pendiente | Pendiente | Pendiente | `addressed` / `justified` / `not addressed` |

Atentamente,

**Editorial Synthesizer — Stage 3 Round 1**
