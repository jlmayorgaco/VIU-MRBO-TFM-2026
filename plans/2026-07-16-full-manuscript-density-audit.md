# Auditoría integral de contribución, rigor y densidad de la memoria

## Propósito y resultado observable

Evaluar la memoria completa como manuscrito académico y como artefacto científico reproducible. El resultado será un informe separado que determine qué aportes están realmente acreditados, qué resultados formales y capas distribuidas existen, dónde se sobreafirma, qué patrones de escritura artificial o metatexto degradan la prosa y qué contenido debe compactarse, fusionarse o retirarse.

## Contexto y archivos canónicos

- Contrato científico: `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`.
- Microestructura SP: `docs/07_SP_SECTION_TEMPLATE.md`.
- Fuente de la memoria: `thesis/main.tex`, preliminares, capítulos 1--7, SP0--SP8 y anexos.
- Evidencia: `results/`, `experiments/configs/`, `tests/` y `docs/04_CLAIMS_EVIDENCE.md`.
- Bibliografía: `thesis/references.bib` y `references/LITERATURE_LEDGER.md`.

## Alcance y no alcance

Incluye lectura completa, auditoría formal y empírica, revisión de coherencia, densidad, metarreferencias, patrones de escritura artificial, consistencia terminológica y revisión visual del PDF compilado. No incluye reescribir la memoria ni generar evidencia experimental nueva; cualquier corrección se propondrá en un mapa de revisión posterior.

## Supuestos y preguntas resueltas

- Se audita el estado actual del repositorio, incluso si contiene trabajo sin confirmar.
- Una caja de contribución o un enunciado formal no cuenta como aporte fuerte sin prueba, artefacto y alcance coherentes.
- "Distribuido" se evalúa sobre toda la cadena `OBSERVED--ESTIMATED--RAW--CLOSED--GUARDED--EXECUTED`, no solo sobre el payoff.
- La densificación prioriza eliminar repetición y metatexto, no comprimir pruebas hasta volverlas inverificables.

## Diseño matemático/técnico

Se construirá una matriz por SP con problema, juego, potencial/equilibrio, garantía, control, implementación distribuida, evidencia y brecha. Los resultados se contrastarán con la matriz de afirmaciones. La auditoría de escritura clasificará patrones P0--P2 y distinguirá tecnicismo legítimo de prosa genérica.

## Plan experimental

No se ejecutará una campaña nueva. Se verificarán compilación, pruebas existentes, manifiestos, recuentos de páginas/palabras, referencias cruzadas y presencia de artefactos citados. Las comprobaciones cuantitativas usarán scripts de lectura, no cambios en resultados.

## Hitos

- [x] Inventario completo de la memoria, PDF y evidencia disponible.
- [x] Matriz de aportes formales, estratégicos, distribuidos y de control por SP.
- [x] Auditoría de metodología, estadística, reproducibilidad y bibliografía.
- [x] Auditoría de escritura artificial, carreta, metatexto, redundancia y terminología.
- [x] Revisión visual y estructural del PDF.
- [x] Informe editorial con decisión, prioridades y plan de compactación verificable.

## Validación

- Compilar `thesis/main.tex` con el flujo versionado.
- Ejecutar la suite de pruebas pertinente o, si su coste es excesivo, las pruebas de teoría y evidencia de SP0--SP6 más controles de literatura.
- Extraer texto y metadatos del PDF; renderizar una muestra estratificada y todas las páginas con alertas de maquetación.
- Comprobar que cada hallazgo del informe cite archivo, sección o página.

## Riesgos y mitigaciones

- La memoria puede exceder el contexto: se usará inventario automático y lectura por capítulos, manteniendo matrices intermedias.
- El PDF puede estar desactualizado: se recompilará antes de juzgar la maquetación.
- Una cita puede existir sin respaldar la afirmación: se separará presencia bibliográfica de verificación contextual.
- Los resultados pueden proceder de campañas de desarrollo: se conservará la clasificación de evidencia y no se promoverán a confirmatorios.

## Registro de decisiones

- 2026-07-16: auditoría en modo de solo lectura sobre la memoria; los únicos archivos nuevos serán este plan y el informe separado.
- 2026-07-16: el criterio principal de aporte fuerte será la cadena formulación--prueba--implementación--evidencia--límite.

## Progreso

Auditoría terminada. Se compiló un PDF de 139 páginas, se inspeccionaron visualmente todas sus páginas, se ejecutaron 50 pruebas con resultado satisfactorio y se verificó la consistencia local de 83 claves citadas frente a 90 entradas bibliográficas y 90 registros del ledger. El dictamen, la matriz por SP, el diagnóstico de escritura y el plan de compactación quedaron en `docs/11_FULL_MANUSCRIPT_REVIEW.md`.
