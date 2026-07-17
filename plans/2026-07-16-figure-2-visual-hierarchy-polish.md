# Pulido de jerarquía visual de la Figura 2

## Propósito y resultado observable

Mejorar la lectura de la Figura 2 del capítulo 5 en una página A4 sin alterar el corpus ni los recuentos: los dos paneles usarán los mismos periodos, la cronología reducirá densidad textual, la escala cromática quedará descrita con precisión y el pie será autosuficiente y más conciso.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`.
- `docs/07_SP_SECTION_TEMPLATE.md`.
- `references/LITERATURE_LEDGER.md`.
- `src/viu_mrob_tfm/literature_coverage.py`.
- `tests/test_literature_coverage.py`.
- `thesis/sections/mainmatter/05-theoretical-framework.tex`.
- `thesis/generated/literature-coverage.tex`.
- `thesis/build.ps1`.

## Alcance y no alcance

Incluye únicamente composición, tipografía, rotulación y semántica visual de la Figura 2, además de pruebas de coherencia entre periodos. No añade referencias, no cambia estados del ledger, no modifica la taxonomía SP0--SP8 y no presenta los recuentos como bibliometría exhaustiva.

## Supuestos y preguntas resueltas

- Se conserva la Figura 2 como una figura TikZ reproducible de dos paneles.
- Los siete intervalos canónicos son 1985--94, 1995--04, 2005--09, 2010--14, 2015--19, 2020--22 y 2023--26.
- La intensidad azul usa una escala común basada en el recuento absoluto; no es una normalización por fila.
- Los trabajos del panel (a) siguen siendo hitos representativos verificados y no una genealogía completa.

## Diseño matemático/técnico

El panel (a) adopta la misma retícula temporal de siete columnas que el generador de cobertura. Los textos de celda se reducen a autor/año, mecanismo breve y SP cubiertos, con jerarquía tipográfica estable. El panel (b) conserva cifras exactas, totales y alcance; su nota explicita la escala cromática común. El pie sustituye detalles internos del repositorio por una descripción académica del registro bibliográfico verificable.

## Plan experimental

No aplica experimento científico. Se verifican constantes temporales y salida determinista mediante pruebas unitarias, se compila el PDF, se renderiza la página de la figura con Poppler y se inspeccionan tamaño de texto, alineación, contraste, recortes y solapamientos.

## Hitos

- [x] Hito 1 — Periodos y semántica de escala coherentes entre generador y TikZ.
- [x] Hito 2 — Cronología simplificada con jerarquía visual mejorada.
- [x] Hito 3 — Pruebas, compilación y revisión visual A4 completadas.
- [x] Hito 4 — Diff y trazabilidad final auditados.

## Validación

- `python -m pytest tests/test_literature_coverage.py`
- `powershell -ExecutionPolicy Bypass -File thesis/build.ps1`
- búsqueda focalizada de errores, referencias indefinidas y desbordes en `thesis/build/main.log`;
- renderizado de la página de la Figura 2 a 180--220 dpi e inspección visual.

## Riesgos y mitigaciones

- Siete columnas pueden estrechar la cronología: se acortan las descripciones antes de reducir tipografía.
- Simplificar hitos puede ocultar matices: se mantienen mecanismo y SP, mientras el párrafo previo y las citas conservan el contexto.
- El estado actual del repositorio contiene muchos cambios ajenos: el trabajo se limita a los archivos objetivo y no restaura ni modifica cambios no relacionados.

## Registro de decisiones

- 2026-07-16: se crea un plan separado porque el plan previo de reparación de legibilidad ya estaba cerrado.
- 2026-07-16: se corrige la discrepancia entre seis periodos en el panel (a) y siete en el panel (b).
- 2026-07-16: se conserva una escala cromática absoluta y común, por ser comparable entre filas, y se corrige su nota explicativa.
- 2026-07-16: los años exactos se eliminan de las celdas de hitos porque ya están codificados por la cabecera de periodo; se conservan autores, mecanismo breve y SP para aumentar el tamaño de letra y evitar cruces entre carriles.

## Progreso

Trabajo terminado. Los dos paneles consumen la misma lista de siete periodos y una prueba impide reintroducir la discrepancia. La cronología conserva autores, mecanismo y SP con menor densidad, la matriz usa una escala azul común correctamente descrita y el pie distingue corpus, alcance y evidencia. Las cinco pruebas focalizadas pasan; LuaLaTeX genera 128 páginas y la página 41 se revisó a 220 dpi sin solapamientos, recortes, referencias indefinidas ni desbordes atribuibles a la figura. Se conservan advertencias preexistentes: caracteres U+0016/Arial, sustituciones de fuente y un desborde de 1,695 pt en la tabla anterior (línea 249), todos fuera de la Figura 2.
