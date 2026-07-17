# Reorganización de la introducción

## Propósito y resultado observable

Reemplazar el andamiaje provisional de `thesis/sections/mainmatter/01-introduction.tex` por una introducción sustantiva que conserve el tono del borrador histórico aportado por el autor y lo alinee con el alcance, la estructura VIU y el estado de evidencia canónicos.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`, `docs/01_VIU_REQUIREMENTS.md`, `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md`, `docs/04_CLAIMS_EVIDENCE.md` y `docs/05_NOTATION.md`. El borrador histórico sirve como referencia de estilo, no como fuente de verdad. Las citas deben existir en `thesis/references.bib` y constar como `VERIFICADA` en `references/LITERATURE_LEDGER.md`.

## Alcance y no alcance

Incluye contexto y motivación, planteamiento y brecha, contribución y límites, preguntas RQ1--RQ6 y mapa de la memoria. No modifica objetivos, hipótesis, formulaciones, resultados ni el alcance administrativo. Tampoco reincorpora campañas históricas o afirmaciones de resultado que no estén trazadas en la matriz de evidencia.

## Supuestos y preguntas resueltas

- El nuevo esquema es el esqueleto VIU ya presente en `thesis/sections/mainmatter/01-introduction.tex`.
- Se mantiene el estilo argumentativo del borrador: contexto industrial concreto, transición hacia la dificultad científica y delimitación honesta.
- La contribución se presenta como una única formulación distribuida acoplada; SP0--SP8 son una escalera de validación.
- Como el modo físico primario aún no está fijado en los documentos canónicos, la introducción declara la obligación de elegir y modelar uno, pero no adopta una modalidad sin autorización científica suficiente.
- Todos los resultados de `docs/04_CLAIMS_EVIDENCE.md` siguen pendientes; por ello, la introducción formula objetivos de validación y no conclusiones.

## Diseño matemático/técnico

La introducción define en prosa la entrada, la salida y las capas del problema, sin anticipar notación que corresponde al capítulo 6. Se distinguen asignación estratégica, estimación/comunicación, movimiento, interacción física y seguridad. La ejecución digital se describe como muestreada y asíncrona localmente, sin afirmar ausencia de reloj.

## Plan experimental

No se ejecutan experimentos. Las afirmaciones empíricas C1--C7 se mantienen como preguntas o resultados por contrastar y se remiten al protocolo común del capítulo 6.

## Hitos

- [x] Auditar el borrador histórico frente a las fuentes canónicas.
- [x] Diseñar el esquema argumental y seleccionar citas verificadas.
- [x] Redactar la introducción completa.
- [x] Compilar y auditar referencias, cajas y caracteres.
- [x] Revisar el diff y cerrar la matriz de afirmaciones de la sección.

## Validación

Ejecutar `thesis/build.ps1`. El cambio se acepta si el PDF se genera sin citas o referencias indefinidas, no aparecen cajas desbordadas y la introducción mantiene coherencia terminológica con los capítulos 2--6.

## Riesgos y mitigaciones

El principal riesgo es arrastrar resultados del borrador histórico que contradicen el reinicio canónico; se mitiga eliminando A0--FULL y cualquier conclusión no trazada. Otro riesgo es duplicar el marco teórico; la introducción solo sintetiza las familias necesarias para formular la brecha y reserva la revisión detallada al capítulo 5.

## Registro de decisiones

- 2026-07-15: se preserva la frase guía según la cual la unidad científica no es la asignación aislada, sino su transición a ejecución física.
- 2026-07-15: la lista histórica de cuatro aportaciones se sustituye por una contribución nuclear y capacidades complementarias.
- 2026-07-15: se usan solo referencias previamente verificadas en el ledger.
- 2026-07-15: se elimina el párrafo metadiscursivo inicial y se conserva una única frase sustantiva para cumplir la regla VIU de no dejar dos encabezados consecutivos.

## Progreso

Trabajo completado. La introducción prescinde del anuncio «Este capítulo...» y entra al contexto mediante una sola frase sustantiva antes de 1.1. Sus 15 claves bibliográficas están presentes en BibLaTeX y marcadas como `VERIFICADA` en el ledger. `thesis/build.ps1` genera un PDF A4 sin citas o referencias indefinidas, cajas desbordadas ni cajas subocupadas registradas. La lista RQ1--RQ6 se ajustó para impedir que una pregunta se partiera entre páginas. No se actualizó `docs/04_CLAIMS_EVIDENCE.md` porque C1--C7 se mantienen como cuestiones por contrastar y la sección no presenta ningún resultado pendiente como hecho.
