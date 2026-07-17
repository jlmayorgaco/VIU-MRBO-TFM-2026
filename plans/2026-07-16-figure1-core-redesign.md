# Rediseño de la Figura 1: arquitectura nuclear del TFM

## Propósito y resultado observable

Actualizar la primera figura de la memoria para que sintetice con claridad la contribución nuclear vigente y sea legible en una página A4. El resultado observable será una figura TikZ compilable que muestre la cadena de información y ejecución, las dos modalidades físicas con distinta prioridad, la realimentación local y la correspondencia con SP0--SP8, sin atribuir como demostrados resultados pendientes.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md`: contribución nuclear, modo Cargo primario y rama empuje/caging secundaria.
- `docs/02_RESEARCH_MATRIX.md`: bloques A--D y dependencia incremental SP0--SP8.
- `docs/04_CLAIMS_EVIDENCE.md`: SP0--SP3 cuentan con evidencia delimitada; SP4--SP8 permanecen parcial o totalmente pendientes.
- `docs/05_NOTATION.md`: cadena `OBSERVED--ESTIMATED--RAW--CLOSED--GUARDED--EXECUTED` y símbolos canónicos.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`: fuente de la Figura 1 y texto que la introduce.
- `thesis/viu-mrob-thesis.sty`: paleta y convenciones visuales comunes.
- `thesis/build/main.pdf`: artefacto para revisión visual.

## Alcance y no alcance

Incluye la revisión conceptual, el rediseño TikZ, la actualización del párrafo introductorio y la leyenda, la compilación y la inspección visual. No modifica formulaciones, resultados, citas, el orden de capítulos ni el estado de las afirmaciones.

## Supuestos y preguntas resueltas

- “Fig. 1 core” se interpreta como la Figura 1 global, rotulada `fig:tf-problem-gap`.
- La figura debe describir la arquitectura y sus contratos, no afirmar que la cadena distribuida completa ya está validada.
- Cargo se representa como vía primaria; empuje/caging se mantiene como extensión y solo usa el término caging cuando existe certificado geométrico.
- SP8 es transversal porque red, escala y coste afectan estimación, decisión y ejecución.

## Diseño matemático/técnico

La composición tendrá tres bandas:

1. información disponible: estado propio, percepción local y mensajes vecinales;
2. flujo nuclear: `OBSERVED/ESTIMATED -> RAW -> CLOSED -> GUARDED -> EXECUTED`;
3. validación incremental: SP0--SP2, SP3, SP4--SP7 y SP8 transversal.

La jerarquía se construye con un flujo horizontal dominante, tipografía de dos niveles, colores ya definidos en la plantilla y una realimentación inferior que vuelve desde la ejecución a la estimación/decisión. Las modalidades físicas aparecen dentro del contrato `GUARDED`, con Cargo destacado y empuje/caging como rama secundaria.

## Plan experimental

No aplica una campaña numérica. La validación es editorial y de composición: compilación reproducible de la memoria, ausencia de errores LaTeX, revisión de referencias y renderizado de la página a PNG para inspeccionar legibilidad, alineación y desbordamientos.

## Hitos

- [x] Hito 1 — identificar la Figura 1 global y auditar sus omisiones frente a los documentos canónicos.
- [x] Hito 2 — sustituir el diagrama por la arquitectura nuclear actualizada y sincronizar el texto asociado.
- [x] Hito 3 — compilar la memoria sin errores y estabilizar las referencias.
- [x] Hito 4 — renderizar la página final, corregir composición y revisar el diff.

## Validación

- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- búsqueda de errores y desbordamientos en `thesis/build/main.log`.
- renderizado de la página con `pdftoppm` y revisión visual a resolución suficiente.
- `git diff -- thesis/sections/mainmatter/05-theoretical-framework.tex plans/2026-07-16-figure1-core-redesign.md`

## Riesgos y mitigaciones

- Sobrecarga de texto: limitar cada contrato a una acción y un criterio verificable.
- Confusión entre arquitectura propuesta y evidencia alcanzada: usar lenguaje de contrato y una nota explícita de que la figura no acredita por sí misma el estado `EXECUTED`.
- Pérdida de legibilidad por `\resizebox`: diseñar directamente dentro del ancho de texto y comprobar el tamaño aparente en el PDF.
- Inflación de alcance: conservar Cargo como modo primario, empuje/caging como extensión y SP7 como condicionado.

## Registro de decisiones

- 2026-07-16: se conserva la figura en el marco teórico porque sintetiza la brecha entre familias; no se traslada a la introducción.
- 2026-07-16: la antigua caja aislada “Brecha de integración” se reemplaza por interfaces explícitas entre estados de información y ejecución.

## Progreso

Trabajo completado. La Figura 1 incorpora la cadena de información y ejecución, diferencia la modalidad Cargo primaria de la extensión empuje/caging, muestra la realimentación local y sitúa SP8 como eje transversal. La memoria completa compila en 128 páginas; la figura se inspeccionó en la página 33 del PDF sin solapamientos ni desbordamientos propios. Persisten avisos preexistentes en otras partes de la memoria, no causados por este cambio.
