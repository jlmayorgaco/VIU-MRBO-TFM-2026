# Revisión académica exigente y auditoría de patrones de escritura artificial

## Propósito y resultado observable

Evaluar la versión vigente de la memoria como entrega de TFM: coherencia científica, alineación entre objetivos, hipótesis, método, resultados y conclusiones, solidez matemática y experimental, trazabilidad bibliográfica, calidad editorial, cumplimiento VIU y señales estilísticas asociadas con escritura artificial. El resultado será un informe separado de la memoria, con dictamen, hallazgos localizados y hoja de ruta priorizada.

## Contexto y archivos canónicos

La revisión usa `docs/00_TFM_CHARTER.md` a `docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, la memoria en `thesis/`, la bibliografía, el ledger, el código, las configuraciones y los artefactos de resultados. El PDF vigente se recompilará y revisará visualmente.

## Alcance y no alcance

Incluye la memoria completa, anexos, coherencia con la evidencia disponible, reproducibilidad declarada y presentación visual. No modifica el manuscrito, no inventa nuevas referencias ni repite campañas experimentales completas salvo que una comprobación puntual sea imprescindible.

## Supuestos y preguntas resueltas

Se toma `thesis/build/main.pdf` recompilado desde el árbol de trabajo actual como versión objeto de revisión. Los cambios sin confirmar del árbol pertenecen al autor y se preservan. La auditoría de patrones de IA identifica señales estilísticas, no determina autoría ni usa un detector probabilístico como prueba.

## Diseño matemático/técnico

La revisión separa: validez interna, validez externa, contribución, corrección formal, semántica de la ejecución distribuida y calidad editorial. Cada hallazgo debe incluir localización, evidencia, severidad, consecuencia y corrección verificable. Las afirmaciones se contrastan contra `docs/04_CLAIMS_EVIDENCE.md` y la notación contra `docs/05_NOTATION.md`.

## Plan experimental

No se ejecuta una campaña nueva. Se validan compilación, pruebas pertinentes disponibles, estructura del PDF, referencias cruzadas, citas, cifras, tablas, figuras, advertencias LaTeX y correspondencia entre resultados publicados y artefactos procesados mediante comprobaciones automatizadas y muestreo dirigido.

## Hitos

- [x] Reunir la versión exacta, compilar y extraer métricas estructurales.
- [x] Ejecutar panel académico independiente y revisión adversarial.
- [x] Auditar patrones de escritura artificial en modo detección.
- [x] Verificar PDF, bibliografía, trazabilidad y reproducibilidad.
- [x] Sintetizar dictamen y hoja de ruta priorizada en un informe separado.

## Validación

Compilación mediante `thesis/build.ps1`; inspección de `main.log`; extracción y renderizado del PDF; pruebas automatizadas disponibles y búsquedas estáticas de referencias rotas, marcadores, sobreafirmaciones, meta-prosa y patrones estilísticos. El informe será aceptable si todos los hallazgos mayores tienen ubicación y criterio de cierre.

## Riesgos y mitigaciones

El tamaño del manuscrito puede ocultar defectos locales; se combina lectura completa, búsquedas sistemáticas y muestreo visual. Los detectores de IA producen falsos positivos; se reportan patrones concretos y densidades, no porcentajes de “texto generado”. La evidencia puede estar desincronizada con cambios locales; se registrará la versión y se contrastará con artefactos existentes.

## Registro de decisiones

- 2026-07-18: revisión en modo solo lectura sobre el manuscrito; el informe se genera aparte.
- 2026-07-18: se adopta auditoría de IA en modo `detect`, perfil académico-técnico y criterio conservador.
- 2026-07-18: el panel queda formado por presidencia, metodología, dominio, perspectiva industrial y Devil's Advocate; Cargo se evalúa como implementación híbrida y no se presupone equivalencia con SP2--SP6.
- 2026-07-18: se conserva el título oficial; cualquier reconsideración administrativa se remite al autor y al director.

## Progreso

Compilación completada en 135 páginas, con cuerpo principal de 95 páginas, resultados de 69 páginas y anexos de 19. La suite registra 75 pruebas superadas. No hay citas ni referencias indefinidas; las 76 claves citadas aparecen en BibLaTeX y en el ledger. El panel, la auditoría estilística y la síntesis editorial están completados. El dictamen final se conserva en `docs/14_FULL_THESIS_RIGOROUS_REVIEW_2026-07-18.md` y los informes independientes en `docs/reviews/2026-07-18/`.
