# Alineación final de resumen, objetivos, hipótesis y metodología

## Propósito y resultado observable
Actualizar la apertura de la memoria y su cierre metodológico para que resumen, abstract, introducción, objetivos, hipótesis, metodología y conclusiones describan únicamente el sistema implementado y la evidencia registrada. El resultado será verificable mediante una matriz objetivo--hipótesis--método--resultado--conclusión, compilación de la memoria y una auditoría de afirmaciones contra `docs/04_CLAIMS_EVIDENCE.md`.

## Contexto y archivos canónicos
Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, la matriz de evidencia, los artefactos procesados y el código actual. Los archivos principales a revisar son `thesis/sections/frontmatter/01-summary.tex`, `02-abstract.tex`, `mainmatter/01-introduction.tex`, `02-objectives.tex`, `03-hypotheses.tex`, `04-methodology.tex`, `06-results-and-analysis/index.tex` y `07-conclusions.tex`.

## Alcance y no alcance
Incluye auditoría y corrección de coherencia vertical y horizontal, lenguaje de evidencia, diseño metodológico, criterios de contraste y trazabilidad. No cambia el título administrativo, no añade experimentos, no presenta la rama empuje/caging como ejecutada y no eleva resultados parciales a garantías generales.

## Supuestos y preguntas resueltas
Se toma Cargo soportado como modalidad primaria ejecutada. La rama empuje/caging se mantiene como extensión pendiente. SP7 se conserva como estudio discreto exploratorio ejecutado. Las hipótesis se juzgan por el conjunto de resultados y pueden quedar sustentadas, parcialmente sustentadas, no sustentadas o refutadas; no se fuerza su aceptación.

## Diseño matemático/técnico
La auditoría enlaza cada objetivo específico con preguntas RQ, hipótesis contrastables, variables/factores, método de análisis, SP que aporta evidencia, resultado y limitación. Se separan asignación estratégica, estimación vecinal, cierre entero, certificado mecánico, control físico, seguridad y red. Los términos `demuestra`, `garantiza`, `óptimo`, `robusto` y `escalable` se restringen al alcance de filas `SOPORTADA`.

## Plan experimental
No se ejecutan campañas nuevas. Se verifican tamaños de muestra, tratamientos, baselines, estadística, criterios de éxito y resultados mediante configuraciones versionadas, tablas procesadas y manifiestos ya existentes. Se emplean pruebas de regresión de texto/trazabilidad y compilación LaTeX.

## Hitos
- [ ] Hito 1 — Inventario del contenido actual y matriz de coherencia con brechas clasificadas.
- [ ] Hito 2 — Resumen/abstract, introducción, objetivos e hipótesis alineados con evidencia real.
- [ ] Hito 3 — Metodología y conclusiones sincronizadas con objetivos e hipótesis.
- [ ] Hito 4 — Matriz de trazabilidad y registro de revisión actualizados.
- [ ] Hito 5 — Pruebas, compilación, revisión visual y diff final completados.

## Validación
Ejecutar búsquedas de términos fuertes y estados pendientes; verificar referencias cruzadas y etiquetas; compilar con `thesis/build.ps1`; ejecutar las pruebas pertinentes existentes; revisar el PDF renderizado, el log de LaTeX y el diff limitado a los archivos de esta tarea.

## Riesgos y mitigaciones
El árbol de trabajo contiene numerosos cambios previos: se editarán solo archivos en alcance y se preservará contenido ajeno. La memoria puede contener resultados posteriores a documentos narrativos antiguos: la matriz de evidencia tiene precedencia. Si una afirmación no tiene artefacto verificable, se rebaja o elimina. La extensión VIU se controla para no convertir los capítulos iniciales en otra sección de resultados.

## Registro de decisiones
- 2026-07-17 — Adoptar una revisión de coherencia completa y no una corrección aislada del resumen, porque el usuario solicita resistencia a una evaluación metodológica de tesis.
- 2026-07-17 — Mantener Cargo como único modo físico validado y empuje/caging como trabajo pendiente.

## Progreso
Leídas las fuentes de verdad y el protocolo de revisión académica. Pendiente inventariar la memoria, construir la matriz de alineación, editar y validar.
