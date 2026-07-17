# Reparación de legibilidad y trazabilidad de la Figura 2

## Propósito y resultado observable

Recomponer la Figura 2 del capítulo 5 para que sus dos paneles sean legibles en A4, no presenten solapamientos ni texto microscópico y usen la taxonomía canónica SP0--SP8. Los recuentos del panel de cobertura deben poder regenerarse desde las filas `VERIFICADA` de `references/LITERATURE_LEDGER.md`.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `docs/07_SP_SECTION_TEMPLATE.md`.
- `references/LITERATURE_LEDGER.md`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/build.ps1`.
- `plans/2026-07-16-literature-timeline-redesign.md`.

## Alcance y no alcance

Incluye el generador de recuentos, pruebas unitarias, el rediseño TikZ, la corrección de nombres y marcas de alcance, la compilación y la revisión visual. No añade fuentes, no cambia el estado bibliográfico de ninguna entrada y no convierte el recuento en una bibliometría exhaustiva.

## Supuestos y preguntas resueltas

- Solo cuentan filas con estado `VERIFICADA` y año entre 1985 y 2026.
- Una fuente etiquetada con varios SP contribuye una vez a cada SP aplicable.
- Los intervalos `SPa--SPb` se expanden de forma inclusiva.
- Los periodos son 1985--94, 1995--04, 2005--09, 2010--14, 2015--19, 2020--22 y 2023--26.
- El alcance se toma del charter: obligatorio para SP0--SP4, SP6 y SP8; extensión prioritaria para SP5; condicionado para SP7. En SP3 la marca obligatoria corresponde al modo primario Cargo.

## Diseño matemático/técnico

Un módulo estándar de Python analiza las filas Markdown del ledger, extrae año y etiquetas SP y escribe un fragmento LaTeX determinista. El TikZ consume ese fragmento y organiza la figura en dos paneles verticales a ancho nativo de texto, sin `resizebox`: cronología simplificada por carriles y matriz de cobertura con una única columna de alcance.

## Plan experimental

No aplica experimento científico. Se verifican conteos conocidos con pruebas unitarias, determinismo del fragmento generado, compilación LuaLaTeX/Biber, ausencia de errores y revisión visual de la página renderizada.

## Hitos

- [x] Hito 1 — Generador y pruebas de cobertura desde el ledger.
- [x] Hito 2 — Figura TikZ recompuesta con nombres y alcance canónicos.
- [x] Hito 3 — PDF compilado y página revisada visualmente.
- [x] Hito 4 — Diff y trazabilidad final auditados.

## Validación

- `python -m pytest tests/test_literature_coverage.py`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- Búsqueda de `undefined`, `overfull` y errores en `thesis/build/main.log`.
- Renderizado con Poppler e inspección visual de la página de la Figura 2.

## Riesgos y mitigaciones

- El ledger es Markdown semiestructurado: el parser falla de forma explícita ante filas verificadas sin año o etiquetas SP mal formadas.
- Una matriz completa puede volver a saturarse: se eliminan el panel lateral duplicado y las tarjetas con marcos redundantes; se usa texto no menor que la escala legible del documento.
- El recuento puede interpretarse como exhaustivo: el pie conserva explícitamente la limitación de corpus y alcance.

## Registro de decisiones

- 2026-07-16: se reabre el rediseño porque la versión posterior añadió un panel cuantitativo manual, contrario a la decisión de trazabilidad del plan anterior.
- 2026-07-16: se conserva el panel de cobertura solicitado, pero se sustituye su contenido por recuentos derivados del ledger y nombres SP canónicos.
- 2026-07-16: la cronología deja de usar tarjetas sobre una escala continua y adopta columnas de periodo; esta composición permite tipografía nativa sin `resizebox` y evita solapamientos.
- 2026-07-16: el alcance se integra como última columna textual para que el color no sea el único canal y para eliminar la leyenda lateral duplicada.

## Progreso

Trabajo terminado. El generador reconstruye 9 filas de cobertura desde el ledger y las cuatro pruebas unitarias pasan. La Figura 2 usa periodos comunes, nombres SP canónicos y alcance alineado con el charter; el PDF final se compiló en `thesis/build/main.pdf`. La página 41 se renderizó a 180 dpi y se revisó tras dos iteraciones: no quedan solapamientos, recortes ni desbordes atribuibles a la figura. Persisten avisos preexistentes de Arial/U+0016 y desbordes ajenos en la tabla anterior, una ecuación y la Figura 3.
