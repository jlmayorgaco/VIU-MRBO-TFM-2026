# Rediseño de la línea temporal del marco teórico

## Propósito y resultado observable

Reformular la línea temporal del capítulo 5 como una cronología por carriles temáticos, inspirada en la referencia visual aportada por el autor. La figura debe permitir leer simultáneamente año, familia metodológica, aporte conceptual y relación con SP0--SP8, sin introducir recuentos bibliométricos no auditados.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/references.bib`.
- `references/LITERATURE_LEDGER.md`.
- `plans/2026-07-15-theoretical-framework.md`.

## Alcance y no alcance

Incluye únicamente el rediseño del TikZ y el ajuste de su introducción y pie. No añade publicaciones, no estima acumulados del corpus y no crea una matriz de cobertura cuantitativa, porque esos valores exigirían un análisis bibliométrico reproducible separado.

## Supuestos y preguntas resueltas

- Los cuatro carriles canónicos son coordinación, MRTA/coaliciones, transporte/contacto y seguridad/red.
- Las etiquetas SP indican pertinencia temática según el ledger, no evidencia experimental del TFM ni cobertura exhaustiva del artículo.
- Se conservan solo trabajos ya citados y verificados en el ledger.

## Diseño matemático/técnico

La escala temporal es única y horizontal. Cada hito se representa mediante una tarjeta del color del carril, un conector vertical al eje y una etiqueta SP textual como canal redundante al color. La jerarquía visual es: título interno, carriles, tarjetas, etiquetas SP y eje temporal.

## Plan experimental

No aplica un experimento científico. La validación consiste en compilar con LuaLaTeX/Biber, comprobar citas y referencias, buscar desbordes y revisar visualmente la página renderizada.

## Hitos

- [x] Hito 1 — TikZ por carriles implementado con fuentes verificadas.
- [x] Hito 2 — memoria compilada sin errores ni referencias indefinidas.
- [x] Hito 3 — página revisada visualmente y ajustada para A4.

## Validación

- `thesis/build.ps1`.
- Búsqueda de `undefined`, `overfull` y errores BibLaTeX en `thesis/build/main.log`.
- Renderizado de la página correspondiente y revisión de legibilidad, solapamientos y recortes.

## Riesgos y mitigaciones

- Densidad excesiva: agrupar hitos recientes y limitar cada tarjeta a autor/año, concepto y etiqueta SP.
- Confusión entre color y significado: repetir el nombre del carril y la etiqueta SP en texto.
- Sobreinterpretación bibliométrica: explicitar que la selección es representativa y no cuantitativa.

## Registro de decisiones

- 2026-07-16: se adopta la composición por carriles de la referencia, pero se excluyen sus paneles de acumulados y cobertura porque el repositorio no contiene todavía un conteo bibliométrico reproducible equivalente.
- 2026-07-16: tras la primera renderización se amplió la separación vertical y se desplazó el origen temporal para eliminar solapamientos entre tarjetas y etiquetas de carril.

## Progreso

Trabajo terminado. Todos los hitos seleccionados existen en el ledger con estado `VERIFICADA`. La memoria se compiló con LuaLaTeX/Biber en `thesis/build/main.pdf` (123 páginas), sin errores, citas indefinidas ni desbordes atribuibles al nuevo timeline. La página 41 se renderizó a 180 dpi y la revisión visual confirmó ausencia de solapamientos, recortes y texto ilegible. Permanece un desborde previo de 1,70 pt en la tabla que antecede al timeline y los avisos U+0016 de Arial ya documentados; ninguno pertenece a esta figura.
