# 06 — Auditoría de fidelidad a la plantilla oficial VIU

## 1. Alcance y autoridad

Esta auditoría compara la fuente LaTeX y su PDF con `resources/VIU_MROB_TFM_TEMPLATE.docx`. El DOCX oficial es la autoridad visual; `docs/01_VIU_REQUIREMENTS.md` conserva la autoridad sobre los requisitos explícitos. La auditoría no cambia contenido científico, alcance ni título administrativo.

Referencia auditada: SHA-256 `6B213806A83F7BAA1E41EB420CB12C423D4C40F90771B5E21B621148BBD33EAA`.

## 2. Evidencia extraída del DOCX

| Elemento | Valor oficial verificado |
|---|---|
| Página | A4 vertical, 21,001 × 29,700 cm |
| Márgenes | 2,499 cm superior/inferior; 3,000 cm izquierdo/derecho |
| Encabezado/pie | Distancia 1,251 cm; primera página diferenciada |
| Cuerpo | Arial 12 pt; justificado; interlineado 1,5; sin sangría inicial; 6 pt posteriores efectivos |
| Título / preliminar | Arial 18 pt, negrita, `#E65113` |
| Nivel 1 | Arial 18 pt, negrita, `#E65113`, numeración decimal |
| Nivel 2 | Arial 16 pt, regular, `#E65113`, numeración jerárquica |
| Portada | Imagen de página completa y slots Título, Alumno/a, Director/a, Edición |
| Preliminares | Resumen, Contenido, Índice de figuras e Índice de tablas |
| Numeración | Arábiga continua; portada sin folio visible y página siguiente almacenada como 2 |

La imagen de portada y el logotipo usados por LaTeX coinciden byte a byte con `word/media/image1.jpg` y `word/media/image2.png` del DOCX. Por tanto, no son recreaciones ni aproximaciones gráficas.

## 3. Diferencias encontradas y resolución

| Severidad | Diferencia previa | Resolución |
|---|---|---|
| Crítica | La plantilla oficial usa numeración arábiga continua desde la portada | Por indicación expresa del autor, los preliminares usan romanos y la Introducción reinicia la numeración arábiga en 1 |
| Crítica | `includehead` desplazaba el cuerpo aproximadamente 1,5 cm por debajo del margen superior Word | El cuerpo comienza a 2,5 cm; el encabezado ocupa únicamente la zona superior reservada |
| Alta | Encabezado aproximado: logo menor, alineado al margen de texto y tipografía reducida | Coordenadas, dimensiones y Arial 12 trasladadas desde los cuadros flotantes OOXML |
| Alta | Faltaba `Edición` en portada | Campo restaurado con el valor administrativo `2025–2026` |
| Media | El índice se titulaba `Índice de contenidos` | Se usa el rótulo exacto `Contenido` de la plantilla |
| Media | Separación anterior de títulos añadida por LaTeX | Eliminada; quedan los 6 pt posteriores efectivos del patrón Word |
| Media | Espaciado adicional antes de palabras clave | Eliminado para conservar el ritmo de párrafo oficial |

## 4. Matriz de conformidad del PDF final

| Requisito | Estado | Evidencia |
|---|---|---|
| A4 | Conforme | `pdfinfo`: 595,276 × 841,890 pt |
| Márgenes 2,5/3 cm | Conforme | Configuración reproducible y revisión visual del área de texto |
| Arial 12 | Conforme | `pdffonts`: Arial regular, negrita y cursiva incrustadas y subconjuntadas |
| Texto justificado, 1,5 | Conforme | Estilo global LaTeX y revisión visual |
| Portada VIU | Conforme | Fondo y logo idénticos al DOCX; slots oficiales presentes |
| Encabezado y folio | Conforme por medidas; numeración adaptada | Geometría OOXML trasladada; preliminares en romanos e Introducción en arábigo desde 1 por indicación del autor |
| Resumen 200–300 y palabras clave | Conforme | Resumen en español y cinco palabras clave |
| Índices | Conforme | Contenido, figuras y tablas presentes; nomenclatura añadida por aplicabilidad |
| Estructura 1–8 | Conforme | Capítulos superiores conservados |
| Figuras/tablas numeradas y con fuente | Conforme en la fuente actual | Numeración automática, captions y fuente/elaboración |
| APA 7 | Conforme por configuración | `biblatex-apa`; la veracidad bibliográfica se controla por el ledger separado |
| Render completo | Conforme | 65 páginas inspeccionadas en cinco hojas de contacto y páginas críticas al 100 % |

## 5. Validación y limitaciones

Hechos verificados:

- Compilación LuaLaTeX/Biber completada y PDF final de 65 páginas.
- Arial está incrustada; la página es A4 y no hay páginas rotadas.
- No se observaron cortes, solapes, tablas fuera de margen, imágenes rotas ni encabezados invadiendo el cuerpo.
- El pequeño aviso de caja de 1,695 pt de la tabla comparativa de familias no produce invasión visual del margen; la página se inspeccionó al 100 %.
- LuaLaTeX/newtx emite cuatro avisos de glifo de control asociados a acentos matemáticos `\dot{x}`; los cuatro puntos aparecen correctamente en el render inspeccionado.

Limitación residual: la numeración se aparta deliberadamente de la secuencia arábiga continua almacenada en el DOCX oficial para comenzar el cuerpo en la página 1, según indicación expresa del autor. Tampoco se declara igualdad píxel a píxel con una exportación de Word. Microsoft Word está instalado, pero su automatización no respondió al abrir/exportar la plantilla; LibreOffice no está disponible. La fidelidad restante queda sustentada por el OOXML, activos idénticos y revisión completa del PDF. Antes de la entrega administrativa conviene una única apertura manual del DOCX y del PDF en el mismo equipo para confirmar que no existe una diferencia específica del renderizador de Word.

## 6. Criterio operativo futuro

Todo cambio posterior en `thesis/viu-mrob-thesis.sty`, portada, preliminares o geometría debe recompilar y revisar el PDF completo. No editar `thesis/main.pdf` ni el entregable final manualmente; siempre regenerarlos desde LaTeX.

## 7. Adenda de cierre editorial de `main(14)` (2026-07-17)

Por petición expresa del autor, el encabezado vigente añade `Jorge Luis Mayorga Taborda` sobre el título corto `Coordinación distribuida AMR`. Esta decisión sustituye para la entrega actual la fidelidad literal al cuadro de encabezado del DOCX registrada en secciones anteriores. Los preliminares conservan romanos minúsculos, ahora con el punto de `i` compuesto explícitamente para evitar su confusión con `I`; la Introducción reinicia la numeración arábiga en 1.

La compilación verificada produce un A4 de 117 páginas en `thesis/build/main.pdf`, sin cajas `Overfull`. La revisión rasterizada cubrió el encabezado, el primer folio romano, las tablas 1, 2, 9, 11, 14, 16, 19 y 25, Cargo, AWS Industrial 2, Referencias y el anexo de reproducibilidad. Esta adenda es el estado operativo vigente cuando contradiga conteos o decisiones históricas anteriores del presente documento.
