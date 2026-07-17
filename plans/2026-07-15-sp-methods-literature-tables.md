# Tablas SP0--SP8 como mini revisión de literatura

## Propósito y resultado observable

Sustituir las nueve tablas genéricas de métodos del capítulo 6 por matrices comparativas sustentadas en literatura primaria verificada. Cada tabla deberá permitir identificar familias metodológicas, mecanismo, información o supuestos, fortaleza, limitación relevante y papel experimental dentro del SP.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`, `docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md` y `docs/05_NOTATION.md`. Se modificarán `thesis/sections/mainmatter/06-results-and-analysis/sp0.tex`--`sp8.tex`, `thesis/references.bib` y `references/LITERATURE_LEDGER.md`.

## Alcance y no alcance

Incluye búsqueda narrativa focalizada, verificación de metadatos y pertinencia, síntesis crítica y maquetación LaTeX. No constituye una revisión sistemática PRISMA ni atribuye superioridad empírica antes de ejecutar los experimentos. No se incorporarán fuentes que no puedan verificarse.

## Supuestos y preguntas resueltas

- Se usarán trabajos seminales cuando definan una familia y trabajos posteriores cuando aporten el comparador operativo.
- Una misma fuente podrá informar varios SP si el mecanismo realmente se reutiliza.
- El oráculo, la propuesta y las ablaciones se distinguirán de los métodos tomados de la literatura.
- Las tablas priorizarán diferencias de mecanismo y supuestos sobre descripciones promocionales.

## Diseño matemático/técnico

Cada tabla tendrá cinco columnas: familia y referencias representativas; mecanismo; información/supuestos; capacidad comparable; limitación y uso en el protocolo. Se usarán citas `\parencite{}` enlazadas a `thesis/references.bib`. El ledger registrará estado, DOI/URL, SP, afirmación respaldada y evidencia revisada.

## Plan experimental

Las tablas no generan resultados, pero definirán baselines verificables y condiciones de comparación justa. Se comprobará que cada comparador produce una salida alineada con las métricas canónicas y que cualquier ventaja de información global se declara explícitamente.

## Hitos

- [x] Respaldar las tablas y archivos bibliográficos actuales.
- [x] Construir y verificar un corpus de al menos 25 fuentes primarias pertinentes.
- [x] Diseñar la matriz de comparación y redactar SP0--SP2.
- [x] Redactar SP3--SP5.
- [x] Redactar SP6--SP8.
- [x] Actualizar BibLaTeX y el ledger sin referencias huérfanas.
- [x] Compilar, auditar y revisar visualmente las nueve tablas.

## Validación

Ejecutar `thesis/build.ps1`; auditar errores, referencias indefinidas, cajas desbordadas y citas no resueltas. Verificar correspondencia uno a uno entre claves citadas, `references.bib` y entradas `VERIFICADA` del ledger. Renderizar las páginas de las nueve tablas y revisar legibilidad en A4.

## Riesgos y mitigaciones

El principal riesgo es convertir las tablas en un volcado de citas o exceder el presupuesto de páginas. Se limitará cada fila a una familia metodológica con una diferencia verificable y se trasladará el detalle narrativo a un párrafo breve. Las fuentes clásicas se mantendrán por su función definitoria, no como evidencia de actualidad. Cualquier método no equivalente se marcará como referencia contextual y no como baseline justo.

## Registro de decisiones

- 2026-07-15: se adopta modo de revisión narrativa focalizada, no revisión sistemática.
- 2026-07-15: se exige literatura primaria verificada y trazabilidad simultánea en BibLaTeX y ledger.
- 2026-07-15: se consolidan cinco columnas comunes: familia/referencia, mecanismo, información/supuestos, aporte comparable y límite/papel experimental.
- 2026-07-15: el corpus final contiene 48 fuentes utilizadas; propuesta, oráculo, baseline y ablación se distinguen en la tabla o en el párrafo de decisión experimental.

## Progreso

Trabajo completado. Las nueve tablas contienen síntesis crítica sustentada en 48 fuentes primarias verificadas. La correspondencia citas--BibLaTeX--ledger es 48/48/48, sin claves huérfanas. `thesis/build.ps1` genera un PDF A4 de 49 páginas; la auditoría del log no detecta cajas desbordadas, referencias indefinidas, errores de LaTeX ni glifos ausentes. Las nueve tablas y los extremos de la bibliografía se renderizaron e inspeccionaron visualmente sin solapamientos, recortes ni texto ilegible.
