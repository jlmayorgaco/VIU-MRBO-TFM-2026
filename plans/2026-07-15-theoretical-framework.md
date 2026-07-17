# Marco teórico y estado del arte ajustado a VIU

## Propósito y resultado observable

Sustituir el esquema provisional del capítulo 5 por un marco teórico avanzado, crítico y trazable, con una extensión renderizada máxima de 12 páginas. El capítulo debe explicar el problema, los fundamentos, autores y técnicas relevantes, el estado actual del área, la brecha de investigación y el posicionamiento exacto del TFM. Incluirá al menos un diagrama TikZ legible y reproducible.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/references.bib` y `references/LITERATURE_LEDGER.md`.
- Borradores de `tmp/docs/doc-05-final-report/`, `tmp/docs/doc-06-explanatory-report/` y `tmp/docs/literature/generated/`.
- Auditoría local de citas `tmp/docs/07-tfm/CITATION_AUDIT.json`.

## Alcance y no alcance

Incluye fundamentos de MRTA y coaliciones, juegos potenciales/poblacionales, coordinación distribuida, transporte rígido prehensil, seguridad, resiliencia, comunicación imperfecta y síntesis crítica. No traslada al capítulo 5 resultados propios, comprobaciones numéricas ni demostraciones extensas que pertenecen al capítulo 6 o a anexos. No presenta MARL como método principal.

## Supuestos y preguntas resueltas

- El modo físico primario se declara como transporte rígido/prehensil planar con contactos establecidos.
- La asincronía significa ausencia de rondas globales síncronas en una implementación digital muestreada.
- Las fuentes recientes de `tmp/` solo se usarán cuando la auditoría local las marque `KEEP`; sus entradas se incorporarán también al ledger canónico.
- El estado del arte se agrupa por mecanismos y supuestos, no como cronología ni inventario de resúmenes.

## Diseño matemático/técnico

El capítulo separará cinco capas: asignación, estimación/comunicación, movimiento, interacción física y seguridad/resiliencia. Definirá con notación canónica el problema mínimo y las condiciones que distinguen una coalición lógica de una coalición físicamente ejecutable. Un TikZ mostrará la cadena problema--familias metodológicas--brecha--pregunta del TFM y otro resumirá las interfaces entre capas si el presupuesto de páginas lo permite.

## Plan experimental

No se generan resultados científicos nuevos. La validación es documental y de maquetación: resolución de claves BibLaTeX, compilación LuaLaTeX/Biber, medición de páginas del capítulo, revisión visual de las páginas renderizadas y comprobación de ausencia de errores o desbordes.

## Hitos

- [x] Hito 1 -- fuentes canónicas, borradores de `tmp/` y auditorías inspeccionados.
- [x] Hito 2 -- capítulo y diagrama TikZ redactados con citas verificadas.
- [x] Hito 3 -- bibliografía y ledger actualizados sin claves huérfanas.
- [x] Hito 4 -- PDF compilado, capítulo entre 11 y 13 páginas y revisión visual superada.
- [x] Hito 5 -- reorganización exacta 5.1--5.8 conforme al presupuesto de 12 páginas indicado por el autor.
- [x] Hito 6 -- frontera marco/resultados auditada: ningún teorema o condición original permanece en el capítulo 5.
- [x] Hito 7 -- nueva versión compilada en un máximo de 12 páginas y verificada visualmente.
- [x] Hito 8 -- revisión de densidad doctoral: jerarquía de factibilidad, contratos de garantía, síntesis deductiva de la brecha y nueva validación dentro de 12 páginas.

## Validación

- LuaLaTeX, Biber y dos pasadas adicionales de LuaLaTeX; `latexmk` no está disponible porque el entorno MiKTeX carece de Perl.
- Búsqueda de `undefined`, `overfull` y errores BibLaTeX en el log.
- Medición del intervalo de páginas del capítulo 5 mediante el PDF/TOC.
- Renderizado con Poppler y revisión de las páginas del capítulo.

## Riesgos y mitigaciones

- Exceso de extensión: priorizar comparación crítica y mover desarrollos propios al capítulo 6.
- Citas recientes preprint: etiquetar explícitamente su estado y no usarlas para afirmaciones universales.
- Diagramas densos: usar texto breve, colores VIU existentes y tamaño mínimo legible.
- Confusión entre equilibrio y ejecución: declarar en cada capa qué propiedad no se transfiere automáticamente.

## Registro de decisiones

- 2026-07-15: se adopta el documento 05 como base de densidad y el documento 06 como cantera conceptual, por ser este último demasiado extenso para VIU.
- 2026-07-15: se excluyen del capítulo 5 las validaciones V1--V3 y teoremas propios largos; pertenecen a resultados/anexos.
- 2026-07-15: se fija la tabla comparativa en posición no flotante para evitar una página aislada y mantener un cierre narrativo continuo.
- 2026-07-15: el autor fija una estructura obligatoria de ocho apartados y un máximo aconsejable de 12 páginas; se reemplaza la organización previa de siete apartados.
- 2026-07-15: ``nivel PhD'' se interpreta como rigor de argumentación y trazabilidad, no como ampliación del alcance ni de la carga oficial de 6 ECTS; la revisión sustituye prosa descriptiva por definiciones, fronteras de inferencia y comparaciones por supuestos.

## Progreso

La revisión de densidad doctoral está terminada. El capítulo conserva exactamente 5.1--5.8 y ocupa las páginas físicas 20--29 del PDF (10 páginas). Contiene 53 claves bibliográficas únicas sin claves ausentes, ocho ecuaciones de fundamentos, un diagrama TikZ y una tabla crítica de siete columnas. La introducción formula cinco niveles de factibilidad y sus inferencias no válidas; MRTA incorpora una formulación binaria mínima que delimita el alcance del algoritmo húngaro; consenso, juegos, GNE/pasividad y robustez explicitan sus contratos y fronteras de garantía; y la brecha se deriva de la falta de cierre entre capas. La auditoría no encontró resultados originales desplazados al marco. LuaLaTeX compila sin citas ni referencias indefinidas y la inspección visual confirmó diagrama, ecuaciones y tabla sin recortes. Persiste una advertencia subpíxel de 1,70 pt en el ancho natural de la tabla y cuatro avisos internos U+0016 de Arial ya presentes en la plantilla; no producen pérdida visible.
