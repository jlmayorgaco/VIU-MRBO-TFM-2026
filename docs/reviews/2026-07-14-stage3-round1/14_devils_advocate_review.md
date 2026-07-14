# Devil’s Advocate Review — Stage 3, Round 1

- **Role:** Devil’s Advocate reviewer
- **Frozen source commit:** `1218a064`
- **FH-v2:** `2fe960…` (identificador recibido en la asignación; la forma completa no quedó preservada tras la compactación)
- **Review date:** 2026-07-14
- **Sealed PDF:** no disponible
- **Review basis:** fuente LaTeX congelada y sus entradas/artefactos autorizados en la copia temporal de Stage 3

> **Reconstruction disclosure:** la compactación del contexto no preservó una copia literal de la respuesta completa de Phase 1. La sección siguiente fue reconstruida fielmente a partir del compromiso registrado, sin alterar sus dimensiones, pruebas ni umbrales. Phase 2 conserva los scores, condiciones y severidad emitidos.

# Phase 1 — Precommitment

**Blindness disclosure:** prior manuscript exposure; no paper access in this phase.

## Review stance

Actuaré como Devil’s Advocate. No intentaré maximizar el número de objeciones, sino construir la interpretación rival más fuerte capaz de explicar la evidencia con menos supuestos que la tesis central. Separaré errores que destruyen la base del trabajo de limitaciones reparables y no usaré `CRITICAL` salvo que exista colapso fundacional, ruptura lógica, contradicción directa con la evidencia o una contranarrativa claramente superior que invalide la contribución declarada.

## Dimension-by-dimension scoring plan

### D1 — Traceability: problem → method → result

Rastrearé preguntas, subproblemas, contribuciones e hipótesis hacia el método, artefacto, resultado y limitación correspondientes. Comprobaré especialmente la continuidad SP1–SP5 y A0–FULL.

- **Pass:** cada afirmación central puede seguirse desde el problema hasta una prueba o resultado delimitado.
- **Warn:** existen saltos, contribuciones huérfanas o resultados que no resuelven el objetivo formulado.
- **Block:** la contribución central no responde al problema o no puede reconstruirse la cadena problema–método–evidencia.

### D2 — Claim–evidence integrity

Clasificaré cada afirmación relevante según su modalidad: prueba, simulación, campaña integrada, replay histórico, propuesta o interpretación. Auditaré lenguaje causal, controles negativos, resultados nulos y límites de atribución.

- **Pass:** modalidad y alcance están rotulados de forma consistente y la evidencia sostiene la fuerza de la afirmación.
- **Warn:** hay sobreextensión reparable, causalidad no aislada o mezcla parcial de modalidades.
- **Block:** la conclusión central contradice los datos o presenta como demostrado lo que solo fue propuesto/reproducido de forma no canónica.

### D3 — Theoretical correctness

Examinaré definiciones de juego, equilibrio/Nash, KKT, dinámica primal–dual/replicador/Smith, CBF/HOCBF, mecánica, complejidad y enlace continuo–discreto. Buscaré supuestos ocultos y verificaré si las conclusiones respetan las hipótesis.

- **Pass:** las derivaciones son correctas dentro de supuestos explícitos y el enlace con el algoritmo está delimitado.
- **Warn:** lagunas o supuestos insuficientemente justificados que no destruyen el resultado condicionado.
- **Block:** teorema, equilibrio o argumento mecánico central inválido.

### D4 — Originality and positioning

Evaluaré la novedad a nivel de mecanismo frente a Quijano, Martínez y antecedentes próximos. Distinguiré una contribución de integración/diagnóstico de una nueva teoría de equilibrio o convergencia.

- **Pass:** se identifica con precisión qué es nuevo y qué se hereda.
- **Warn:** la retórica de novedad excede la aportación mecanística demostrada.
- **Block:** la contribución central ya está contenida en antecedentes o se atribuye originalidad a material heredado.

### D5 — Experimental and statistical rigor

Revisaré equidad de atribución y baselines, semillas, unidades, intervalos, tamaños de efecto, multiplicidad, ablaciones, presupuesto informacional y de cómputo. Atacaré de forma específica uniform+QR/guard, el empaquetado de FULL, la calibración y la sensibilidad.

- **Pass:** comparaciones justas y potencia/sensibilidad suficientes para el alcance declarado.
- **Warn:** evidencia condicionada a una calibración, planta o paquete no desagregado.
- **Block:** diseño incapaz de sostener la afirmación causal principal o comparación fundamentalmente injusta.

### D6 — System validity, locality and safety

Auditaré la escalera de modalidades, operaciones locales/globales, seguridad, scaling y correspondencia entre modelo planar, simulación y transporte físico. Comprobaré si existe localidad extremo a extremo y si cada garantía de seguridad corresponde a la modalidad realmente validada.

- **Pass:** dependencias centralizadas, alcance físico y límites de seguridad se declaran con claridad.
- **Warn:** la solución es solo parcialmente distribuida o físicamente parcial pese a una formulación más amplia.
- **Block:** una garantía central de localidad o seguridad es falsa dentro del sistema implementado.

### D7 — Narrative and writing

Comprobaré que exista una sola tesis progresiva, terminología estable, aportes inequívocos y ausencia de contradicciones entre texto, figuras, tablas y conclusiones.

- **Pass:** narrativa coherente y proporcional a la evidencia.
- **Warn:** figuras o secciones preservan afirmaciones más fuertes que la síntesis final.
- **Block:** contradicción narrativa central que impide determinar qué se reclama.

### D8 — Reproducibility and bibliographic integrity

Rastrearé artefactos, configuraciones, comandos, hashes, semillas y citas hasta resultados concretos. Distinguiré cierre completo de trazabilidad y disponibilidad parcial.

- **Pass:** un tercero puede reconstruir los resultados centrales y la bibliografía respalda el uso dado.
- **Warn:** trazabilidad variable o piezas no congeladas en resultados relevantes.
- **Block:** evidencia central no reproducible, artefactos ausentes o citas fabricadas/contrarias a la afirmación.

## Failure-condition commitment

- **F1:** cualquier `block` en D1–D3 activa rechazo, severidad 4.
- **F2:** dos o más `warn` o peor en D1–D3 por mayoría del panel activan `major_revision`, severidad 3.
- **F3:** cualquier `block` en D4–D8 por mayoría activa `major_revision`, severidad 3.
- **F4:** cualquier `warn` en D1–D3 activa al menos `minor_revision`, severidad 2.
- **F5:** cualquier `warn` en D4–D8 activa al menos `minor_revision`, severidad 2.
- **F0:** solo si todas las dimensiones obligatorias reciben `pass` de todos los revisores puede resultar `accept`, severidad 1.

No modificaré estos criterios después de leer el manuscrito.

[CONTRACT-ACKNOWLEDGED]

# Phase 2 — Review

**Blindness disclosure:** prior manuscript exposure; no paper access in Phase 1. Phase 2 used only the frozen checkout `C:\Users\walla\AppData\Local\Temp\VIU-MRBO-TFM-2026-stage3-1218a064`; I did not consult prior reviews, `03_consolidated_editorial_decision`, the current PDF, the main worktree, or `docs/07-tfm`.

## Dimension Scores

| Dimensión | Resultado | Fundamento |
|---|---|---|
| D1 Traceabilidad problema–método–resultado | **pass** | Objetivos, hipótesis, escalera SP y campaña A0–FULL forman una cadena explícita; además, SP7–SP8 se distinguen como evidencia descriptiva/exploratoria (`docs/doc-05-final-report/sections/mainmatter/03-hypothesis.tex:3-29`; `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:85-110`). |
| D2 Integridad afirmación–evidencia | **warn** | La tesis reconoce que uniform+QR/guard iguala o supera variantes de juego y que FULL empaqueta varios mecanismos, pero conserva formulaciones que atribuyen demasiado a la arquitectura “basada en juegos” (`docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:17-34,60,69-81`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/index.tex:44-53`). |
| D3 Corrección teórica | **pass** | Los resultados de equilibrio, KKT, CBF e ISS están acotados por supuestos explícitos. El teorema ISS declara matriz común, perturbación acotada y ausencia de resets; SP4 reconoce que residuo KKT no predice por sí solo éxito dinámico (`docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:85-113`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:269-275,292-309`). |
| D4 Originalidad y posicionamiento | **warn** | La aportación sólida es la integración diagnóstica y la escalera de evidencia, no un nuevo principio general de equilibrio. Algunas frases aún sugieren una familia distribuida y unificada más amplia que lo implementado (`docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:451-464,521-527`). |
| D5 Rigor experimental/estadístico | **warn** | La campaña integrada es amplia y emparejada, pero usa una sola planta/calibración, carece de sensibilidad confirmatoria y contiene tratamientos acumulativos o empaquetados que impiden atribución fina (`docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:102-110`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39,53`). |
| D6 Validez sistémica, localidad y seguridad | **warn** | La dependencia global está declarada honestamente, pero no existe localidad extremo a extremo; tampoco validación de saturación de par, seguridad continua, fricción, ruedas o hardware (`docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:292-309`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:123-127`). |
| D7 Narrativa y escritura | **warn** | El cuerpo principal es progresivo y autocrítico, pero algunas figuras mantienen una tesis más fuerte —“una misma ley”, juego que incorpora seguridad y wrench— que el texto final ya no sostiene (`docs/doc-05-final-report/figures/fig-gap-literatura.tex:24-42`; `docs/doc-05-final-report/figures/fig-equilibrio-nash-smith.tex:42-44`; `docs/doc-05-final-report/figures/fig-sota-transporte-cooperativo.tex:33-43`). |
| D8 Reproducibilidad e integridad bibliográfica | **pass** | Se ofrecen configuraciones, comandos, semillas y hashes, junto con una declaración explícita sobre el alcance desigual de la trazabilidad entre bloques (`docs/doc-05-final-report/sections/anexo-b-reproducibilidad.tex:18-45`; `docs/doc-05-final-report/sections/anexo-e-declaraciones.tex:6`). |

## Failure Condition Checks

| Condición | Resultado |
|---|---|
| F1 — algún `block` obligatorio | **No**: D1–D3 no contienen bloqueos. |
| F2 — dos dimensiones obligatorias `warn` o peor por mayoría | **No activada por este voto**: solo D2 queda en `warn`; además, la mayoría exige agregación del panel. |
| F3 — dimensión de alta prioridad `block` por mayoría | **No**: no asigno ningún `block`. |
| F4 — cualquier dimensión obligatoria `warn` | **Sí**: D2 activa `minor_revision`, severidad 2. |
| F5 — cualquier dimensión de alta prioridad `warn` | **Sí**: D4–D7 activan `minor_revision`, severidad 2. |
| F0 — todas las obligatorias `pass` por unanimidad | **No**: D2 es `warn`. |

## Review Body — Devil’s Advocate

### Fortalezas breves

- La tesis convierte controles negativos incómodos en resultados centrales: uniform+QR/guard revela que gran parte del rendimiento procede del cierre de factibilidad, no del motor poblacional.
- La dependencia global, el empaquetado de FULL, la falta de sensibilidad y las limitaciones físicas se declaran de manera poco habitual y científicamente valiosa.
- La separación entre prueba, simulación canónica, replay histórico y propuesta está generalmente bien ejecutada.
- El resultado ISS no se presenta como una garantía universal: sus hipótesis excluyen precisamente varios cambios que una sustitución física real podría introducir.
- La campaña integrada aporta una lectura mecanicista más fuerte que una simple tabla de rankings.

### Strongest Counter-Argument

La interpretación adversa más fuerte es que la tesis no demuestra que un juego distribuido sea la causa de la mejora observada. Los propios controles indican que uniform+QR puede superar a Smith+QR y que uniform+guard alcanza cobertura completa; por tanto, el componente decisivo parece ser el cierre global de factibilidad, no la dinámica poblacional (`docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:17-34,60,69-81`). En la campaña A0–FULL, las operaciones que materialmente determinan quién entra, quién sale y si la coalición es válida incluyen cuantiles, rankings, sumas, ordenaciones, uniones y reemplazo globales (`docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`). FULL agrega comunicación, memoria expirable y reemplazo en un único incremento de \(+0.62\), de modo que tampoco identifica cuál de esos mecanismos produce la recuperación (`docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39`).

Bajo esta lectura, “juego” funciona como generador candidato de asignaciones, mientras que la arquitectura efectiva es un pipeline híbrido de selección más reparación centralizada. El equilibrio tampoco explica el rendimiento dinámico: en SP4, el residuo KKT y la tasa de éxito pueden divergir, y el Nash exacto sufre timeouts (`docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:269-275`). La campaña integrada, además, se apoya en una sola planta planar y una calibración sin análisis confirmatorio de sensibilidad (`docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:53`). En consecuencia, una narrativa igualmente compatible —y más parsimoniosa— sería: “los cierres globales y las salvaguardas físicas dominan; el juego aporta una parametrización interpretable, pero no una ventaja causal demostrada”. Esta alternativa no invalida los datos, pero sí reduce la novedad desde “control distribuido basado en juegos” a “arquitectura diagnóstica híbrida con heurísticas de factibilidad”.

### Issue List

#### CRITICAL

Ninguno. No encuentro colapso fundacional, contradicción probatoria ni error matemático que invalide todo el estudio. La interpretación alternativa reduce el alcance de la contribución, pero deja en pie la campaña empírica dentro de su simulador congelado.

#### MAJOR

1. **Atribución causal insuficiente al juego — D2/D4/D5.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:17-34,60,69-81`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:39`; `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:521-527`.
   El control uniforme demuestra que cierre y guard pueden explicar una porción dominante del resultado. FULL y A4 también agregan mecanismos simultáneamente.
   **Alternativa:** ejecutar un factorial común en la planta integrada: motor `{uniforme, Smith, greedy, subasta}` × cierre `{sin QR, QR}` × guard `{off,on}` × recuperación `{off,on}`, con igual presupuesto informacional, semillas emparejadas e interacciones. Si no se amplía el experimento, redefinir la contribución como arquitectura híbrida de factibilidad y presentar el juego como generador interpretable, no como causa establecida.

2. **No existe localidad extremo a extremo — D2/D6.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:51-74`; `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/index.tex:521-527`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:29-31`.
   La decisión local convive con cuantiles, rankings, quórum, QR, unión y reemplazo globales. La etiqueta “distribuido” resulta válida solo a nivel parcial.
   **Alternativa:** implementar consenso/gossip, max-consensus y QR distribuido o aproximado, medir mensajes, rondas, sensibilidad a topología y fallos; o usar de forma consistente “arquitectura híbrida/semi-distribuida”.

3. **Ausencia de sensibilidad confirmatoria y diversidad de plantas — D5/D6.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/04-methodology.tex:102-110`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:53`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:31`.
   Una campaña extensa sobre una única planta no determina si los saltos A2–A4/FULL son estructurales o producto de umbrales, horizonte, ganancias, masa e inercia concretos.
   **Alternativa:** matriz preregistrada de sensibilidad sobre carga, geometría, fricción, ruido, latencia, pérdidas, densidad de obstáculos, horizonte y umbrales; informar efectos e interacciones, no solo tasas agregadas.

4. **La garantía física queda por debajo de la retórica de seguridad — D3/D6.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:292-309`; `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:123-127`; `docs/doc-05-final-report/sections/mainmatter/07-conclusions.tex:29-31`.
   Cero colisiones discretas no prueba invariancia continua; faltan saturación de actuadores, fricción/ruedas y validación funcional de seguridad. El agarre rígido permite autoridad que el modelo estático unilateral no representa.
   **Alternativa:** integrar límites de par y fricción, detección continua o paso adaptativo, barrera robusta con error de discretización y al menos una planta 3D o ensayo hardware-in-the-loop.

5. **El equilibrio es una lente diagnóstica, no una explicación completa del desempeño — D2/D3/D4.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/sp4-motion.tex:269-275`; `docs/doc-05-final-report/sections/mainmatter/05-theoretical-framework/integrated-theory-core.tex:85-113`.
   La divergencia KKT–éxito demuestra que transitorios, saturación y horizonte dominan ciertos regímenes. El resultado ISS depende de una matriz común y entradas acotadas, condiciones no verificadas para toda sustitución física.
   **Alternativa:** demostrar el enlace entre actualización implementada, juego/potencial y dinámica física bajo switching; o rebajar explícitamente Nash/KKT a criterio de consistencia estacionaria.

#### MINOR

1. **Figuras con afirmaciones más fuertes que el texto — D7.**
   **Ubicación:** `docs/doc-05-final-report/figures/fig-gap-literatura.tex:24-42`; `docs/doc-05-final-report/figures/fig-equilibrio-nash-smith.tex:42-44`; `docs/doc-05-final-report/figures/fig-sota-transporte-cooperativo.tex:33-43`.
   Sustituir “una misma ley” y la incorporación implícita de seguridad/wrench al equilibrio por una representación de capas: generador, cierre, guard y recuperación.

2. **Uso de lenguaje causal en ablations acumulativas — D2/D7.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/physical-coalition-integrated.tex:4-6,39`.
   Preferir “incremento observado al añadir el paquete” frente a atribuirlo al mecanismo individual cuando el escalón introduce más de un cambio.

3. **Resultado negativo uniforme insuficientemente elevado en la síntesis — D4/D7.**
   **Ubicación:** `docs/doc-05-final-report/sections/mainmatter/06-results-and-analysis/modular-evidence-synthesis.tex:17-34,60,69-81`.
   Conviene convertirlo en una proposición empírica central: el valor del juego es condicional al cierre y no domina universalmente.

4. **Matriz de reproducibilidad por afirmación — D8.**
   **Ubicación:** `docs/doc-05-final-report/sections/anexo-b-reproducibilidad.tex:18-45`.
   Añadir una tabla claim → figura/tabla → configuración → semillas → archivo → hash → estatus canónico reduciría el coste de auditoría.

### Alternativas interpretativas

- **Narrativa de factibilidad:** el aporte principal es descubrir que la selección por utilidad no basta; QR, guardas y reemplazo explican el cierre.
- **Narrativa híbrida:** la solución efectiva es una arquitectura jerárquica con preferencias locales y reparación global, no un algoritmo completamente distribuido.
- **Narrativa de transitorios:** Nash/KKT caracterizan estados candidatos, pero el éxito depende más de tiempos de convergencia, saturaciones y horizonte.
- **Narrativa de ingeniería:** la contribución más defendible es la escalera experimental reproducible que localiza fallos entre selección, wrench, movimiento, seguridad y recuperación.

### Blind spots

- No se cuantifica cuánto rendimiento se conserva al reemplazar cada primitiva global por una aproximación local.
- Falta análisis de equivalencia frente al uniforme: “no significativo” no demuestra desempeño equivalente.
- No se estudia robustez a comportamiento estratégico, información falsa o agentes bizantinos, pese al encuadre de teoría de juegos.
- La red sintética no cubre correlación temporal realista, interferencia ni congestión inducida por el propio protocolo.
- Una planta planar con agarre rígido no revela redistribución 3D, torsión, compliance ni pérdida de contacto.
- Los veinte contrastes de precisión mejoran resolución, pero no sustituyen una política confirmatoria de multiplicidad y sensibilidad.

### Unexamined Premise

La premisa insuficientemente examinada es que una arquitectura puede calificarse como “distribuida basada en juegos” cuando las decisiones que finalmente certifican factibilidad y corrigen la coalición son globales. La tesis reconoce la deuda, pero no prueba que la capa local conserve utilidad al retirar el oráculo global. La prueba decisiva sería sustituir cada primitiva centralizada por una versión local bajo el mismo presupuesto de comunicación y medir la degradación.

### Observations

- La autocrítica del manuscrito es una fortaleza real: varias objeciones adversariales ya aparecen en resultados y conclusiones.
- La tesis es más convincente como mapa causal de fallos que como demostración de superioridad de un juego específico.
- El teorema ISS es correcto dentro de sus supuestos, pero debe permanecer presentado como resultado condicionado, no como certificación de FULL.
- “Sin colisiones observadas”, “seguridad funcional” e “invariancia continua” deben conservarse como tres niveles distintos.
- Alcanzar un nivel 10/10 exige resolver principalmente atribución, localidad y sensibilidad; no añadir más amplitud teórica desconectada.

## Editorial Decision

**minor_revision — severity 2.** Decisión mecánica: F4 se activa por `D2=warn` y F5 por `D4–D7=warn`; F1, F2 y F3 no se activan en este voto, y F0 no se cumple.
