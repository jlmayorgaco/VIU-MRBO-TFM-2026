# Fidelidad visual Word oficial VIU -> LaTeX

## Propósito y resultado observable
Auditar la plantilla oficial `resources/VIU_MROB_TFM_TEMPLATE.docx`, comparar sus patrones con `thesis/main.pdf` y ajustar la fuente LaTeX reproducible para que el PDF final conserve la identidad visual, geometría, tipografía, preliminares y jerarquía de la plantilla VIU. El resultado se verificará mediante renderizados a imagen, medidas de página y una matriz explícita de conformidad.

## Contexto y archivos canónicos
- `resources/VIU_MROB_TFM_TEMPLATE.docx`: autoridad visual.
- `docs/01_VIU_REQUIREMENTS.md`: requisitos académicos sintetizados.
- `thesis/main.tex`, `thesis/viu-mrob-thesis.sty`: fuente de composición.
- `thesis/sections/frontmatter/`: portada y preliminares.
- `thesis/main.pdf`: salida actual y futura.

## Alcance y no alcance
Incluye geometría A4, márgenes, fuentes, interlineado, portada, encabezados/pies, numeración, índices, jerarquía de títulos, párrafos, listas, tablas, figuras y apéndices. No altera el título administrativo, el contenido científico, las afirmaciones ni los resultados experimentales salvo correcciones de maquetación imprescindibles.

## Supuestos y preguntas resueltas
- La plantilla DOCX retenida es la autoridad visual, aunque LibreOffice y Word puedan producir pequeñas diferencias de paginación.
- Se preserva Arial mediante una fuente métrica y visualmente equivalente solo si Arial no está disponible; cualquier sustitución se documentará.
- “Indistinguible” se interpreta como ausencia de diferencias visuales sistemáticas atribuibles al motor LaTeX en los patrones reutilizados, no como igualdad píxel a píxel entre documentos con contenido distinto.

## Diseño matemático/técnico
Se destilarán tokens exactos del OOXML: tamaño de página, márgenes, distancias de encabezado/pie, estilos de párrafo, fuentes, tamaños, espaciados, sangrías, alineaciones y propiedades de sección. Esos tokens se mapearán a `geometry`, `fontspec`, `setspace`, `titlesec`, `fancyhdr`, `tocloft` y componentes propios, evitando editar el PDF generado manualmente.

## Plan experimental
No aplica a resultados científicos. La validación será documental: render DOCX/PDF, extracción geométrica, auditoría de fuentes incrustadas, inspección de páginas y compilación reproducible.

## Hitos
- [x] Destilar el DOCX y documentar todos los patrones visuales relevantes.
- [x] Auditar el PDF/LaTeX actual y registrar diferencias por severidad.
- [x] Implementar el cambio mínimo en la fuente LaTeX.
- [x] Compilar, renderizar e inspeccionar todas las páginas.
- [x] Entregar matriz de conformidad, limitaciones y riesgos residuales.

## Validación
- Auditorías OOXML de secciones, estilos, campos e imágenes.
- `latexmk`/motor configurado en el repositorio sin errores fatales.
- `pdfinfo` y `pdffonts` para tamaño de página y fuentes.
- Render a PNG del DOCX oficial y del PDF final; inspección visual de todas las páginas.
- Revisión de `git diff` limitada a los archivos de maquetación, plan e informe de auditoría.

## Riesgos y mitigaciones
- Diferencias de render entre Word y LibreOffice: priorizar OOXML y, si Word está disponible, exportar también con Word para contraste.
- La plantilla puede contener texto de ejemplo y estilos no usados: separar requisitos activos de residuos de autoría.
- Cambios de tipografía pueden alterar mucho la paginación: validar el documento completo después de cada lote.
- Árbol de trabajo con cambios ajenos: no tocar ni revertir archivos fuera del alcance.

## Registro de decisiones
- 2026-07-15: la plantilla DOCX se adopta como autoridad visual y `docs/01_VIU_REQUIREMENTS.md` como autoridad de requisitos explícitos.
- 2026-07-15: los cambios se harán únicamente en fuentes reproducibles y se validarán contra renderizados.
- 2026-07-15: se conserva Abstract y nomenclatura como preliminares adicionales pertinentes, ambos dentro del sistema visual oficial; no sustituyen ni reordenan los capítulos VIU.
- 2026-07-15: la fidelidad se certifica por OOXML, hashes de activos y render completo del PDF; no se afirma igualdad píxel a píxel porque Word no respondió a la exportación automatizada.

## Progreso
Completados destilación, correcciones, compilación, inspección de 65 páginas y matriz de conformidad. Entregable final generado en `output/pdf/TFM_Jorge_Luis_Mayorga_VIU.pdf`. Riesgo residual: una última comparación manual lado a lado en Microsoft Word antes de la entrega administrativa.
