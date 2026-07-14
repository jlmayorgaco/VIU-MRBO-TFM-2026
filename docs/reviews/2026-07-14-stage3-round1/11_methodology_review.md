# Stage 3 — Round 1 — Methodology Review

- **Rol:** R1 — Metodología, estadística y reproducibilidad
- **Commit base:** `1218a064`
- **Fixture Harness:** `FH-v2`
- **Fecha:** 2026-07-14
- **PDF sellado:** no disponible
- **Sistema de citas:** ruta relativa del artefacto congelado + línea o intervalo de líneas

# Phase 1 — Precommitment

Blindness disclosure: prior manuscript exposure; no paper access in this phase.

## Dimension Scoring Plan

### D1 — Trazabilidad de pregunta, objetivos, hipótesis y contribuciones

Comprobaré la cadena pregunta de investigación/subproblema/contribución → hipótesis o expectativa falsable → método → resultado → limitación. Emitiré `block` si la tesis central o múltiples subproblemas no pueden trazarse hasta evidencia identificable; emitiré `warn` si existe una ambigüedad localizada que no invalida el núcleo.

### D2 — Correspondencia entre afirmaciones y evidencia

Evaluaré cada afirmación según la modalidad que realmente la sustenta: demostración, comprobación algebraica, simulación, replay, propuesta o trabajo futuro. Revisaré la preservación de resultados negativos y límites. Emitiré `block` ante una contradicción central, sobrealcance material u ocultación de evidencia adversa; emitiré `warn` ante sobreafirmaciones localizadas corregibles.

### D3 — Solidez teórica

Revisaré definiciones, supuestos, derivaciones y compatibilidad entre garantías continuas, cierres discretos y ejecución. Emitiré `block` ante un resultado falso, circular o sustentado por hipótesis incompatibles con el modelo ejecutado; emitiré `warn` ante lagunas limitadas que no destruyen la conclusión principal.

### D4 — Originalidad y separación entre herencia y aporte propio

Exigiré una matriz o trazabilidad equivalente que distinga antecedentes, mecanismos heredados, delta técnico propio y evidencia. Emitiré `block` si la contribución es esencialmente trabajo previo presentado como propia; emitiré `warn` si la frontera de originalidad es difusa pero recuperable.

### D5 — Rigor metodológico, estadístico y experimental

Examinaré unidad inferencial y anidamiento, mundos y semillas pareadas, separación desarrollo/test, reglas de parada, potencia o precisión, equidad de comparadores, endpoints, efectos, intervalos, tests, multiplicidad, ablaciones, fallos y timeouts. Emitiré `block` si pseudorreplicación, leakage, comparadores injustos o tests incompatibles invalidan el núcleo; emitiré `warn` si faltan sensibilidad, potencia o controles secundarios con un núcleo aún interpretable.

### D6 — Alcance físico, dinámico y distribuido

Comprobaré que se distingan álgebra, simulación numérica, motor dinámico, replay y hardware; revisaré centralización, seguridad discreta/continua, red, contacto y escalado. Emitiré `block` ante una afirmación física, distribuida, de seguridad o escalado sin soporte; emitiré `warn` cuando la evidencia sea parcial y el delimitador necesite mayor visibilidad.

### D7 — Narrativa científica

Evaluaré si existe una única tesis progresiva, si cada sección cumple una función y si las conclusiones responden a los resultados sin contradicciones. Emitiré `block` ante una estructura que impida reconstruir el argumento o contenga contradicciones centrales; emitiré `warn` ante repetición, densidad o transiciones localmente deficientes.

### D8 — Reproducibilidad e integridad bibliográfica

Revisaré código, configuraciones, entorno, semillas, manifiestos, hashes, tablas, datos, scripts y trazabilidad de citas. Emitiré `block` si el resultado central es irreproducible o depende de referencias fabricadas; emitiré `warn` ante metadatos, instrucciones o verificaciones bibliográficas localmente incompletas.

## Failure Condition Precommitment

- **F1:** cualquier `block` en una dimensión obligatoria activa `reject`.
- **F2:** dos o más dimensiones obligatorias con `warn` o peor, por mayoría del panel, activan `major_revision`.
- **F3:** cualquier `block` en una dimensión de prioridad alta, por mayoría del panel, activa `major_revision`.
- **F4:** cualquier `warn` en una dimensión obligatoria activa como mínimo `minor_revision`.
- **F5:** cualquier `warn` en una dimensión de prioridad alta activa como mínimo `minor_revision`.
- **F0:** solo si todas las dimensiones obligatorias están en `pass` para todo el panel puede activarse `accept`.

[CONTRACT-ACKNOWLEDGED]

# Phase 2 — Review

Disclosure de ceguera: exposición previa al manuscrito; la Phase 1 se realizó sin acceso al documento. Esta Phase 2 evalúa exclusivamente la copia congelada indicada, sin consultar dictámenes previos.

## Dimension Scores

### D1 — Trazabilidad

`score: warn`

La pregunta central, la hipótesis integradora y la cadena A0–FULL son trazables desde la formulación hasta los resultados y límites (`01-introduction.tex:29-46`; `03-hypothesis.tex:12-29`; `physical-coalition-integrated.tex:1-55`; `07-conclusions.tex:3-31`).

El punto débil es O5: el marco promete como mínimo MARL-CTDE y comparadores aprendidos (`05-theoretical-framework/index.tex:513-519`), y las conclusiones declaran cubierto O5 (`07-conclusions.tex:8-10`), pero el cuerpo visible no identifica el modelo entrenado, protocolo CTDE, checkpoint, presupuesto o resultado asociado. Trigger: ambigüedad localizada en la trazabilidad de un objetivo específico.

### D2 — Correspondencia claim–evidence

`score: warn`

La modalidad de evidencia está generalmente bien delimitada: simulación planar, comprobación algebraica, dinámica numérica, evidencia descriptiva y preguntas no estimables no se confunden (`04-methodology.tex:111-119`; `modular-evidence-synthesis.tex:143-151`; `07-conclusions.tex:27-31`).

No obstante, las afirmaciones sobre “métodos aprendidos” y MARL-CTDE no tienen respaldo paper-visible identificable. ERV–BNN aparece como dinámica poblacional, no como política aprendida (`sp4-motion.tex:119-131,171-188`). Trigger: sobrealcance localizado, corregible sin invalidar la tesis central.

### D3 — Solidez teórica

`score: pass`

Las definiciones, hipótesis y dominios de validez están explícitos. La memoria separa Nash poblacional, preferencia continua, cierre entero y factibilidad física (`05-theoretical-framework/index.tex:164-228`). Las derivaciones Lagrange–Hamilton, RAW/SAFE/EXEC e ISS indican exactamente qué cambia entre modelo nominal y ejecutado (`integrated-theory-core.tex:19-83,85-115`). También se evita transferir garantías convexas a cierres enteros, consenso finito o trayectorias completas (`sp4-motion.tex:93-138,301-309`).

Trigger de bloqueo no activado: no detecto circularidad ni transferencia incompatible de garantías.

### D4 — Originalidad

`score: pass`

La matriz distingue de forma convincente mecanismos heredados y delta propio. No reclama novedad sobre Nash, Smith, dinámicas poblacionales, KKT, HOCBF o herramientas primal–dual; sitúa el aporte en interfaces, semántica física, auditoría por capas y campaña integrada (`05-theoretical-framework/index.tex:449-470`). La discusión reconoce que el cierre, y no necesariamente el motor poblacional, explica parte de los resultados (`06-results-and-analysis/index.tex:41-53`).

### D5 — Rigor metodológico y estadístico

`score: warn`

La unidad experimental, el emparejamiento y la dependencia están excelentemente definidos (`04-methodology.tex:5-38`). McNemar exacto, diferencias pareadas, bootstrap y Holm son apropiados para los endpoints declarados (`04-methodology.tex:85-100`; `sp4-motion.tex:171-188`).

Persisten tres reservas:

1. La extensión 40–60–100 depende de la anchura de un IC bootstrap ordinario; como la anchura depende de los resultados observados, la cobertura nominal y el error de los contrastes finales bajo tamaño muestral aleatorio no quedan demostrados (`04-methodology.tex:102-110`; `physical-coalition-integrated.tex:4-6`).
2. Falta un análisis de sensibilidad confirmatorio para parámetros centrales como \(\rho\), HOCBF, horizonte, radio y proyección (`physical-coalition-integrated.tex:49-53`).
3. No siempre se explicita si el bootstrap estima media, mediana u otro funcional, mientras algunos tests de rangos y los IC de diferencia media pueden responder a estimandos diferentes (`04-methodology.tex:87-96`; `modular-evidence-synthesis.tex:96-104`).

Trigger: controles secundarios incompletos, con núcleo empírico todavía rescatable.

### D6 — Alcance físico, dinámico y distribuido

`score: pass`

El presupuesto de centralización expone umbrales, rankings, cierres, guardias y reemplazo globales (`04-methodology.tex:51-75`). SP4 y SP5 separan planta no holónoma, movimiento hacia contactos, transporte de carga y ejecución saturada (`sp4-motion.tex:5-42,141-168`; `modular-evidence-synthesis.tex:87-127`). La memoria no transforma cero colisiones observadas en seguridad funcional ni simulación planar en validación física (`sp4-motion.tex:292-309`; `07-conclusions.tex:27-31`).

### D7 — Narrativa científica

`score: pass`

Existe una progresión clara:

RQ → definición de coalición física → teoría continua → cierres discretos → escalera modular → campaña integrada → límites.

La jerarquía impide sumar plantas diferentes como si fueran una sola evidencia (`06-results-and-analysis/index.tex:1-14`). La discusión y las conclusiones conservan resultados negativos y no sostienen superioridad universal (`06-results-and-analysis/index.tex:38-53`; `07-conclusions.tex:16-25`).

### D8 — Reproducibilidad e integridad bibliográfica

`score: warn`

El protocolo exige configuraciones congeladas, semillas, mundos, hashes, esquemas y manifiestos (`04-methodology.tex:110-115`). A0–FULL informa freeze, dry-run independiente, CPU, software, número de workers, 2.160 ejecuciones únicas y cero errores (`04-methodology.tex:102-110`; `physical-coalition-integrated.tex:4-6`).

Sin embargo, la síntesis modular remite genéricamente a los artefactos sin proporcionar junto a cada claim un identificador uniforme de configuración, tabla, manifiesto y hash (`modular-evidence-synthesis.tex:1-4`). Trigger: metadatos localizados insuficientes para reconstruir rápidamente toda la cadena claim→resultado→configuración, no irreproducibilidad del núcleo.

## Failure Condition Checks

- `F1 fired: false` — No hay bloques en D1–D3. Acción individual: no rechazar.
- `F2 fired: false` — Requiere mayoría del panel; este dictamen individual no puede activar el cuantificador colectivo. Acción individual: elevar D1–D2 al editor.
- `F3 fired: false` — No hay bloque en dimensiones de prioridad alta. Acción individual: ninguna.
- `F4 fired: true` — D1 y D2 tienen `warn`. Acción individual: `minor_revision`.
- `F5 fired: true` — D5 y D8 tienen `warn`. Acción individual: `minor_revision`.
- `F0 fired: false` — No todas las dimensiones obligatorias están en `pass`. Acción individual: no aceptar todavía.

## Review Body

### Recomendación y confianza

Recomendación: **revisión menor**.

Confianza: **alta, 0,90**.

El núcleo metodológico es sólido: diseño pareado, unidad inferencial correcta, freeze explícito, preservación de fallos y timeouts, multiplicidad controlada y separación excepcionalmente clara entre preferencia, cierre, seguridad comandada y ejecución física. Las correcciones pendientes afectan principalmente a la trazabilidad de comparadores aprendidos, la justificación secuencial de la extensión por precisión, la alineación estimando–test–IC, la sensibilidad y el registro reproducible paper-visible.

### Fortalezas

1. Excelente prevención de pseudorreplicación: robots, contactos, frames y métodos están anidados en el mundo, no contados como réplicas (`04-methodology.tex:18-43`).
2. Freeze y semillas confirmatorias correctamente separados del dry-run y del desarrollo (`04-methodology.tex:45-49,102-110`).
3. McNemar exacto y bootstrap pareado respetan el emparejamiento; Holm se aplica por familias preespecificadas (`04-methodology.tex:85-100`; `physical-coalition-integrated.tex:37-39`).
4. Ablaciones particularmente informativas: RAW/CLOSED y RAW/SAFE/EXEC impiden atribuir al juego lo producido por el cierre o el filtro (`modular-evidence-synthesis.tex:8-81,87-127`).
5. Tratamiento ejemplar de resultados negativos, no estimables y timeouts (`06-results-and-analysis/index.tex:38-53`; `modular-evidence-synthesis.tex:143-151`).

### Debilidades principales

1. **Comparador aprendido no trazado.**
   Problema: se promete MARL-CTDE, pero no se presenta una campaña o checkpoint identificable.
   Impacto: O5 y la comparación frente a métodos aprendidos quedan parcialmente sin demostrar.
   Sugerencia: añadir una tabla que identifique algoritmo, observaciones, entrenamiento, semillas, checkpoint, presupuesto, resultado y artefacto; o retirar MARL/aprendidos del conjunto ejecutado.
   Severidad: moderada.
   Ubicación: `05-theoretical-framework/index.tex:513-519`; `07-conclusions.tex:8-10`.

2. **Inferencia convencional después de extensión por anchura.**
   Problema: detener o extender según la anchura bootstrap produce tamaño muestral aleatorio; ignorar signo y \(p\) no demuestra por sí solo cobertura nominal ni control del error.
   Impacto: IC95 % y McNemar/Holm finales podrían no conservar exactamente sus propiedades nominales.
   Sugerencia: fijar \(n\) definitivamente, emplear inferencia secuencial válida o demostrar cobertura y error familiar mediante simulación bajo el stopping rule completo.
   Severidad: moderada.
   Ubicación: `04-methodology.tex:102-110`; `physical-coalition-integrated.tex:4-6`.

3. **Estimando, prueba e intervalo no siempre alineados.**
   Problema: Wilcoxon unilateral y un IC bootstrap de diferencia media pueden responder a parámetros distintos.
   Impacto: puede aparecer un \(p_{\rm Holm}\) significativo junto a un IC que incluye cero, como reconoce correctamente SP5.
   Sugerencia: tabla por contraste con estimando, dirección, estadístico, método de IC, número de remuestreos y regla decisoria.
   Severidad: moderada.
   Ubicación: `04-methodology.tex:85-96`; `modular-evidence-synthesis.tex:96-104`.

4. **Sensibilidad paramétrica insuficiente.**
   Problema: los resultados integrados dependen de una calibración puntual no sometida a sensibilidad confirmatoria.
   Impacto: limita robustez paramétrica y transportabilidad incluso dentro del simulador planar.
   Sugerencia: análisis factorial o barrido congelado sobre \(\rho\), ganancias HOCBF, horizonte, radio y número de proyecciones, manteniendo mundos pareados.
   Severidad: moderada.
   Ubicación: `physical-coalition-integrated.tex:49-53`; `07-conclusions.tex:27-31`.

5. **Registro claim–artifact incompleto en el cuerpo.**
   Problema: varias campañas se identifican narrativamente, pero sin una clave uniforme que enlace claim, configuración, manifiesto, tabla y hash.
   Impacto: aumenta el coste de auditoría y el riesgo de enlazar una cifra con una versión histórica.
   Sugerencia: incorporar un registro machine-readable y una tabla breve en el anexo.
   Severidad: menor.
   Ubicación: `04-methodology.tex:111-119`; `modular-evidence-synthesis.tex:1-4`.

### Auditoría metodológica focal

- **RQ:** definida y operacionalizada mediante estados falsables (`01-introduction.tex:29-33`).
- **Diseño:** cuantitativo, comparativo, pareado y por simulación (`04-methodology.tex:3-16`).
- **Unidad inferencial:** mundo experimental; tratamientos repetidos dentro del mundo (`04-methodology.tex:18-43`).
- **Semillas y freeze:** disjuntas y abiertas después de congelar el protocolo (`04-methodology.tex:45-49,102-110`).
- **Extensión precision-only:** transparente, aunque requiere validación secuencial (`04-methodology.tex:104-106`).
- **McNemar:** adecuado para pares binarios discordantes (`04-methodology.tex:87-90`).
- **Bootstrap:** correctamente pareado; falta especificar estimando y validez bajo stopping (`04-methodology.tex:89-96`).
- **Holm:** apropiado y aplicado al tamaño final (`04-methodology.tex:98-106`).
- **Baselines:** incluyen controles uniformes, greedy, subastas, referencias centralizadas y modelos físicos; los proxies se declaran (`04-methodology.tex:45-49`; `modular-evidence-synthesis.tex:17-81`).
- **Ablaciones:** fuertes y causalmente informativas (`06-results-and-analysis/index.tex:38-53`).
- **Timeouts:** permanecen en denominador y no se convierten en missing o éxito (`04-methodology.tex:33-38,85-96`).
- **Sensibilidad:** insuficiente para parámetros centrales (`physical-coalition-integrated.tex:49-53`).
- **Reproducibilidad:** fuerte para A0–FULL; mejorable en el enlace uniforme de campañas modulares.
- **Falacias evitadas:** pseudorreplicación, \(p=1\) para no estimable, significación como relevancia práctica, suma de simuladores heterogéneos, cero colisiones como prueba de seguridad y centralización encubierta como distribución.

### Preguntas para el autor

1. ¿Qué campaña y artefacto corresponden exactamente al comparador MARL-CTDE?
2. ¿Se evaluó mediante simulación la cobertura de los IC y el FWER bajo la regla 40–60–100?
3. ¿Qué estimando exacto acompaña a cada Wilcoxon y a cada IC bootstrap?
4. ¿Cuántas réplicas bootstrap se usaron y cómo se fijaron sus semillas?
5. ¿Puede publicarse un registro único claim→tabla→configuración→manifiesto→hash?

### Comentarios menores

- Sustituir “los cinco contrastes sobrevivieron Holm” por una tabla compacta que incluya estimando, dirección y margen práctico (`sp4-motion.tex:249-258`).
- Mantener de forma uniforme “proxy”, “referencia interna” y “no desplegable” en todas las tablas de comparadores.
- Hacer visible en la tabla principal que FULL combina comunicación, memoria y reemplazo, por lo que su efecto no admite atribución individual (`physical-coalition-integrated.tex:37-39`).

### Puntuación global

- Originalidad: **88/100**
- Rigor metodológico: **82/100**
- Suficiencia de evidencia: **86/100**
- Coherencia: **87/100**
- Escritura científica: **86/100**
- Promedio: **85,8/100**

## Editorial Decision

minor_revision
