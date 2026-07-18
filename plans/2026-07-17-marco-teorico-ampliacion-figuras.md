# Ampliación del marco teórico y mejora de figuras

## Propósito y resultado observable

Mejorar el capítulo 5 de la memoria mediante una ampliación crítica de sus fundamentos y del estado del arte, sin eliminar ninguna figura o diagrama existente. El resultado verificable será un capítulo compilado con una extensión compatible con el presupuesto VIU vigente, figuras más grandes y legibles, citas resueltas y ausencia de recortes o solapes en el PDF.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/references.bib` y `references/LITERATURE_LEDGER.md`.
- `docs/04_CLAIMS_EVIDENCE.md`, especialmente la afirmación C8 sobre la brecha bibliográfica.
- Texto editorial adjunto por el autor sobre el presupuesto y los contenidos faltantes.
- `thesis/build/main.pdf` como salida reproducible para la revisión visual.

## Alcance y no alcance

Incluye la ampliación de transporte cooperativo, MRTA y coaliciones, información local y juegos, factibilidad mecánica, control de pose, seguridad, recuperación, tráfico y red imperfecta. También incluye la comparación crítica final y el aumento de tamaño de las tres figuras existentes. No se eliminan figuras, no se incorporan resultados numéricos propios al capítulo 5, no se formulan teoremas nuevos y no se amplía la rama secundaria de empuje/caging más allá de su delimitación conceptual.

## Supuestos y preguntas resueltas

- Se conserva Cargo soportado como modalidad física primaria; empuje/caging permanece como contraste conceptual y extensión secundaria.
- El presupuesto canónico del repositorio, 11--13 páginas para el capítulo 5, tiene precedencia sobre la recomendación adjunta de 9--11 páginas; se buscará el extremo inferior del intervalo canónico para no restar espacio al capítulo 6.
- Las citas añadidas se limitan a entradas ya verificadas o explícitamente clasificadas en el ledger.
- Los cambios previos sin confirmar del archivo se consideran trabajo del autor y se preservan.

## Diseño matemático/técnico

La revisión mantendrá cuatro fronteras como hilo argumental: asignación frente a coalición ejecutable; cobertura de recursos frente a factibilidad de wrench; seguridad frente a vivacidad; y equilibrio visible frente a consistencia global. Las ecuaciones existentes se mantienen como fundamentos mínimos. La ampliación se concentra en supuestos, interfaces y límites de cada familia metodológica, no en reproducir las formulaciones de SP0--SP8.

Las figuras TikZ se escalarán hasta el ancho útil de la página o el mayor ancho compatible con márgenes y legibilidad. La figura compuesta de literatura conservará ambos paneles y el mapa metodológico, pero dejará de usar el escalado reducido al 75 % del ancho de texto.

## Plan experimental

No se generan datos científicos. La validación comprende compilación LuaLaTeX/Biber, búsqueda de citas o referencias indefinidas, auditoría de cajas desbordadas, medición de la extensión real del capítulo y renderizado PNG de todas sus páginas. Se inspeccionarán especialmente las páginas con el diagrama de contratos, el símplex, la tabla comparativa y la figura compuesta del corpus.

## Hitos

- [ ] Hito 1 — línea base de contenido, paginación y figuras auditada.
- [ ] Hito 2 — narrativa teórica y comparación crítica ampliadas con fuentes verificadas.
- [ ] Hito 3 — todas las figuras existentes conservadas y ampliadas.
- [ ] Hito 4 — PDF compilado, capítulo medido y páginas revisadas visualmente.
- [ ] Hito 5 — diff final y trazabilidad editorial revisados.

## Validación

- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1` desde el repositorio o `./build.ps1` desde `thesis/`.
- Búsqueda en `thesis/build/main.log` de errores, referencias/citas indefinidas y `Overfull`.
- `pdfinfo thesis/build/main.pdf` y extracción del índice para delimitar el capítulo.
- `pdftoppm -png -f <inicio> -l <fin> -r 160 thesis/build/main.pdf tmp/pdfs/marco-teorico/page`.
- Inspección visual de todos los PNG del intervalo.

## Riesgos y mitigaciones

- Exceso de extensión: priorizar explicaciones que aclaren interfaces y mantener el capítulo en el extremo inferior del intervalo 11--13.
- Figuras ampliadas que fuercen páginas vacías: ajustar flotantes y espaciado sin reducir la legibilidad ni eliminar contenido.
- Afirmaciones bibliográficas excesivas: formular la brecha solo respecto del corpus verificado y conservar la salvedad de no universalidad.
- Confusión entre fundamentos y contribución: reservar payoffs, pruebas y resultados específicos para el capítulo 6 y anexos.

## Registro de decisiones

- 2026-07-17 — Se conservan las tres figuras existentes y la tabla comparativa; la solicitud explícita del autor prevalece sobre la sugerencia adjunta de seleccionar una sola figura de estado del arte.
- 2026-07-17 — Se adopta 11--13 páginas como restricción canónica del repositorio y 11 páginas como objetivo editorial inicial.

## Progreso

Se completó la lectura de las fuentes canónicas, del texto adjunto, del capítulo vigente, del plan anterior y del ledger bibliográfico. La línea base contiene tres figuras: contratos entre capas, retratos de dinámicas poblacionales y una figura compuesta de cronología/cobertura más mapa metodológico. Las dos mitades de la figura compuesta están reducidas al 75 % del ancho de texto y son el principal objetivo de ampliación visual.
