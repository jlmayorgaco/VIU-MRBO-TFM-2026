# Modularización SP0--SP8 del capítulo de resultados

## Propósito y resultado observable

Sustituir el archivo monolítico del capítulo 6 por un índice común y nueve archivos LaTeX, uno por SP0--SP8. Cada archivo debe compilar como una subsección de «Resultados y análisis» y contener planteamiento incremental, diagrama TikZ, formulación formal de referencia, tabla de métodos, protocolo de simulación, contribución esperada y cierre.

## Contexto y archivos canónicos

El alcance procede de `docs/00_TFM_CHARTER.md`; la extensión y jerarquía, de `docs/01_VIU_REQUIREMENTS.md`; la pregunta, método, baseline y nivel de evidencia de cada SP, de `docs/02_RESEARCH_MATRIX.md`; el diseño de simulación, de `docs/03_EXPERIMENT_PROTOCOL.md`; y la fuerza admisible de las afirmaciones, de `docs/04_CLAIMS_EVIDENCE.md`. La notación sigue `docs/05_NOTATION.md`.

## Alcance y no alcance

Incluye estructura y contenido técnico de andamiaje, ecuaciones de referencia, diagramas conceptuales y tablas de comparación candidatas. No incorpora resultados numéricos, citas no verificadas, pruebas de convergencia ni conclusiones empíricas. SP7 permanece condicionado y los niveles de evidencia se declaran de forma explícita.

## Supuestos y preguntas resueltas

- La formulación común y el protocolo se presentan una sola vez en `index.tex` para evitar nueve miniartículos repetitivos.
- Cada `spX.tex` representa una subsección; sus componentes internos son subsubsecciones.
- Los problemas de optimización se etiquetan como referencias centralizadas o problemas de evaluación cuando no representan el mecanismo distribuido propuesto.
- Los términos de coste se normalizan antes de combinar magnitudes con unidades distintas; los pesos definitivos no se fijan en este andamiaje.
- El título administrativo se sincroniza con la versión vigente del TFM Charter, que usa AMR.

## Diseño matemático/técnico

`sections/mainmatter/06-results-and-analysis/index.tex` contiene la sección, la formulación común, el protocolo y las entradas a `sp0.tex`--`sp8.tex`. Cada módulo emplea `x_{ik}` como asignación binaria cuando formula un oráculo estático; cualquier interpretación poblacional o continua deberá declararse por separado en la redacción definitiva. Los diagramas comparten estilos TikZ definidos en `viu-mrob-thesis.sty`.

## Plan experimental

Cada SP conserva los escenarios mínimos y las métricas prescritas en `docs/03_EXPERIMENT_PROTOCOL.md`. Las tablas distinguen método propuesto, oráculo/referencia central, baseline distribuido y ablación. No se etiqueta ningún baseline como estado del arte sin verificación bibliográfica.

## Hitos

- [x] Respaldar la versión compilable previa.
- [x] Crear el índice y los nueve módulos SP.
- [x] Compilar sin errores ni referencias indefinidas.
- [x] Revisar visualmente las nueve figuras y tablas.
- [x] Auditar archivos incluidos, notación y afirmaciones.

## Validación

Desde `thesis/`: `.\build.ps1`. Se aceptará el cambio si `build/main.pdf` se genera, todas las figuras y tablas aparecen numeradas, no hay cajas desbordadas ni archivos `.tex` huérfanos, y la revisión visual confirma que diagramas, ecuaciones y tablas son legibles.

## Riesgos y mitigaciones

La repetición puede inflar el capítulo y superar el presupuesto de páginas; se mitiga centralizando definiciones y usando módulos breves. Las formulaciones pueden confundirse con el algoritmo propuesto; cada una se clasifica explícitamente como oráculo, referencia o problema de evaluación. La ausencia de resultados se mantiene visible mediante redacción prospectiva y estados de evidencia.

## Registro de decisiones

- 2026-07-14: un archivo por SP, con `index.tex` como único punto de entrada del capítulo.
- 2026-07-14: diagramas TikZ específicos por SP y estilo visual común.
- 2026-07-14: no se añaden citas ni cifras hasta verificar literatura y resultados.

## Progreso

Trabajo completado. El capítulo 6 contiene `index.tex` y `sp0.tex`--`sp8.tex`, con nueve figuras TikZ, nueve tablas y nueve formulaciones numeradas. `thesis/build/main.pdf` compila en A4 con 37 páginas; el log no contiene cajas desbordadas, referencias indefinidas, caracteres ausentes ni errores de LaTeX. Se inspeccionaron visualmente todas las páginas del capítulo. La bibliografía permanece vacía de forma intencional hasta incorporar fuentes verificadas.
