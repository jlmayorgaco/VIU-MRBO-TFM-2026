# Cierre P0/P1 del dictamen de `main(14)`

## Propósito y resultado observable

Corregir las contradicciones y defectos editoriales identificados en el dictamen de `main(14)` sin crear otra variante del PDF. El resultado observable será `thesis/build/main.pdf`, con título AMR, OE5 trazado, regla Cargo dimensionalmente coherente, metadatos completos y revisión visual de paginación, encabezado, tablas y referencias.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, las fuentes LaTeX de `thesis/`, el ejecutor Cargo y sus pruebas. El dictamen se conserva en el adjunto `pasted-text.txt`. El árbol de trabajo ya contiene cambios extensos del autor; este pase no restaura ni revierte modificaciones ajenas.

## Alcance y no alcance

Incluye OE5 y su fila metodológica, una síntesis reproducible de una página, normalización de la regla Cargo sin alterar su orden numérico, delimitación de batería, atribución AWS, encabezado, folios romanos, tablas críticas, párrafos telegráficos, terminología AMR, limpieza bibliográfica visible y metadatos PDF.

No incluye cambiar AMR por AGV, inventar DOI/release, crear una etiqueta o commit, repetir campañas cuyos valores no cambian, ni producir `main(15)` u otra copia numerada. La interpretación administrativa de si las referencias cuentan dentro de las 80 páginas requiere confirmación de VIU/tutor; la memoria mantendrá separadas las referencias como capítulo obligatorio posterior al cuerpo.

## Supuestos y preguntas resueltas

- AMR prevalece por instrucción expresa del autor y por el título administrativo canónico de la carta.
- Las escalas Cargo se fijan en 1 m, 1 kg y 1 N. La expresión queda adimensional y numéricamente idéntica a la campaña archivada, por lo que no cambia coaliciones ni resultados.
- Los empates de líder y candidato se resuelven por identificador ascendente.
- La versión de depósito no tiene aún etiqueta; se declarará el SHA base y el estado no consolidado sin presentarlos como release inmutable.
- La escena AWS se atribuye al repositorio oficial y su licencia MIT-0; la composición y modificaciones del TFM siguen rotuladas como propias.

## Diseño matemático/técnico

La puntuación Cargo será
`s_i=delta_i/delta_ref-0.08 c_i^pay/c_ref-0.025 f_i^max/f_ref`, con orden ascendente. El certificado declarará cardinalidad, carga útil y fuerza mediante tres desigualdades. El código expondrá las tres escalas y una función de puntuación probada, conservando exactamente los valores históricos para referencias unitarias.

OE5 distinguirá campañas regenerables de reanálisis archivados. El anexo incluirá repositorio, estado de versión, SHA base, entorno, clasificación de campañas y responsabilidad del autor, sin afirmar una instantánea inmutable inexistente.

## Plan experimental

No se generan datos científicos nuevos. Se ejecutarán pruebas focalizadas del ranking Cargo y la suite pertinente; la igualdad numérica del ranking anterior y normalizado se comprobará automáticamente. La compilación regenerará únicamente `thesis/build/main.pdf`.

## Hitos

- [x] Hito 1 — P0: OE5, trazabilidad y Cargo quedan consistentes en texto, código, notación y pruebas.
- [x] Hito 2 — P1: batería, AWS, encabezado, folios, tablas, prosa, APA y metadatos quedan corregidos.
- [x] Hito 3 — No quedan usos de AGV en la tesis y `main.pdf` conserva AMR en portada y metadatos.
- [x] Hito 4 — Pruebas, compilación, auditoría de log, paginación y revisión visual pasan.

## Validación

- búsqueda de `AGV`, `OE5`, `pendientes`, metadatos y escalas Cargo;
- `python -m pytest -q tests/test_cargo_e2e.py` y suite disponible;
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`;
- inspección de citas/referencias indefinidas, `Overfull`, fuentes, metadatos y número de páginas;
- render PNG de portada, preliminares, tablas críticas, Cargo, conclusiones, referencias y anexo de reproducibilidad.

## Riesgos y mitigaciones

- **Desbordar 80 páginas de cuerpo:** usar 9 pt solo en las tablas señaladas, compactar prosa adyacente y verificar la última página narrativa.
- **Atribuir una release inexistente:** declarar expresamente que la etiqueta está pendiente y que el SHA corresponde a la base Git, no al árbol modificado.
- **Cambiar resultados Cargo:** referencias unitarias y prueba de equivalencia exacta.
- **Romper cambios previos:** parches focalizados y revisión del diff por archivo.
- **Licencia AWS incierta:** citar la fuente oficial y registrar su licencia verificada, sin atribuir al TFM los activos de base.

## Registro de decisiones

- 2026-07-17 — Mantener AMR en toda la tesis por decisión expresa del autor y precedencia de `docs/00_TFM_CHARTER.md`.
- 2026-07-17 — Recompilar solo `thesis/build/main.pdf`; no crear una versión numerada paralela.
- 2026-07-17 — Conservar la semántica y resultados de Cargo mediante referencias unitarias explícitas.
- 2026-07-17 — Tratar la cuenta de referencias como cuestión administrativa no resoluble por inferencia local.

## Progreso

Cierre completado. OE5 queda definido, operacionalizado y evaluado; Cargo usa una puntuación adimensional con equivalencia numérica probada; batería y AWS están delimitados; encabezado, folios, tablas, prosa, bibliografía y metadatos fueron corregidos. Pasan 75 pruebas, el PDF final tiene 117 páginas y el log no contiene errores, referencias indefinidas ni cajas `Overfull`. La revisión visual cubrió todas las páginas sensibles. Permanece fuera de este cambio la creación de una etiqueta/release inmutable y la interpretación administrativa de si Referencias cuenta dentro del máximo de 80 páginas.
