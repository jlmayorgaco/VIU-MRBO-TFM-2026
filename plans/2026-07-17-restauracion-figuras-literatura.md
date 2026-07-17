# Restauración literal de las figuras bibliográficas

## Propósito y resultado observable

Restaurar en el capítulo 5 la cronología bibliográfica y el mapa metodológico XY exactamente como estaban antes de su retirada del 17 de julio de 2026. El PDF deberá volver a mostrar ambas figuras, con sus textos, etiquetas, citas y fuentes originales.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `references/METHODOLOGICAL_MAP_RUBRIC.md`.
- `references/LITERATURE_LEDGER.md`.
- Planes del 16 de julio sobre la cronología y el mapa metodológico.
- Objetos e historial local de Git anteriores a la reducción editorial.

## Alcance y no alcance

Se recuperan literalmente las dos figuras y el texto inmediato necesario para presentarlas. No se rediseñan, no se cambian sus coordenadas, no se añaden papers y no se modifica evidencia experimental.

## Supuestos y preguntas resueltas

La versión correcta es la última versión validada visualmente antes de la retirada. Si existen varias copias, se elegirá la que coincida con los planes cerrados del 16 de julio y con la rúbrica de la Figura 3.

## Diseño matemático/técnico

La recuperación se hará desde contenido local previo, preservando el eje distribuido--centralizado, el eje white-box--data-driven, la agrupación reproducible del mapa y los carriles temáticos de la cronología.

## Plan experimental

No aplica experimento científico. La validación consiste en compilación LaTeX/Biber, comprobación de referencias y revisión visual de las páginas afectadas.

## Hitos

- [x] Localizar la versión literal anterior a la retirada.
- [x] Restaurar ambos bloques sin alterar cambios ajenos.
- [x] Compilar la memoria y comprobar referencias/citas.
- [x] Renderizar e inspeccionar visualmente las páginas afectadas.
- [x] Revisar el diff y actualizar este plan.

## Validación

- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`.
- Búsqueda de errores, referencias indefinidas y desbordes nuevos en el log.
- Renderizado de las páginas del capítulo 5 y revisión visual.

## Riesgos y mitigaciones

- Pérdida de la copia en el worktree: recuperar desde objetos locales de Git y contrastar con planes y rúbrica.
- Colisión con cambios actuales: aplicar solo los bloques recuperados y revisar el diff contextual.
- Aumento de páginas: aceptado por petición expresa del autor; se reportará el nuevo total.

## Registro de decisiones

- 2026-07-17: el autor solicita restauración literal; la reducción de páginas deja de tener precedencia para estas dos figuras.
- 2026-07-17: la fuente literal se recupera del registro local de la última sesión que mostró el capítulo 5 completo antes de la retirada, no de una reconstrucción manual.
- 2026-07-17: se añaden captions cortos literales a tres tablas existentes para evitar que macros numéricas aún no definidas corrompan la segunda pasada del auxiliar; el texto visible no cambia.

## Progreso

Restauración completada. La cronología vuelve como Figura 3 y el mapa metodológico como Figura 4 en las páginas impresas 18--19. La compilación completa genera 122 páginas; las páginas físicas 31--32 se renderizaron a 180 dpi y se revisaron sin cortes, solapes ni texto ilegible. Las cinco pruebas de cobertura bibliográfica pasan y `git diff --check` no detecta errores. El log conserva advertencias bibliográficas preexistentes en otras secciones, pero ninguna referencia o cita de las dos figuras queda indefinida.
