# Plantilla canónica para las secciones SP0--SP8

## Propósito y resultado observable

Consolidar una microestructura reutilizable para `sp0.tex`--`sp8.tex` que preserve la plantilla VIU y haga explícitos el diagrama TikZ, el oráculo de optimización, la revisión comparada de métodos, el juego distribuido, el problema de control, las simulaciones, las comparaciones y el cierre de evidencia.

## Contexto y archivos canónicos

La estructura debe respetar `AGENTS.md`, `docs/01_VIU_REQUIREMENTS.md`, la matriz de investigación y el protocolo experimental. El contrato especializado se ubicará en `docs/07_SP_SECTION_TEMPLATE.md`; `AGENTS.md` actuará como punto de descubrimiento, sin duplicar su contenido.

## Alcance y no alcance

Incluye la estructura académica, un esqueleto LaTeX y listas de comprobación. No reescribe ahora los nueve SP ni impone la misma extensión a todos. SP0--SP2 pueden declarar que el control físico queda fuera de su alcance en vez de inventar una ley de control.

## Supuestos y preguntas resueltas

Cada SP es una `\subsection` dentro del capítulo 6 y comienza con texto introductorio. La formulación de optimización se clasifica como oráculo, baseline o problema de evaluación; no se confunde con el mecanismo distribuido. Las fuentes de la tabla de literatura deben estar verificadas en el ledger.

## Diseño matemático/técnico

La plantilla separará decisión estratégica, control físico, comunicación y evaluación. Exigirá dominios y unidades, relación payoff--potencial, garantía formal honesta, ejecución digital, complejidad computacional y comunicativa, y trazabilidad entre código, configuración, datos y texto.

## Plan experimental

La plantilla exigirá hipótesis local, factores, semillas pareadas, oráculo/baselines, ablación, métricas, intervalos de confianza, resultados negativos y artefactos generados automáticamente.

## Hitos

- [x] Hito 1 — contrato especializado y esqueleto LaTeX creados.
- [x] Hito 2 — referencias desde `AGENTS.md` y `README.md` añadidas.
- [x] Hito 3 — enlaces y consistencia terminológica auditados.

## Validación

Comprobar con búsquedas locales que los enlaces existen, que la secuencia solicitada aparece completa y que no se altera ningún archivo fuente de la memoria.

## Riesgos y mitigaciones

El riesgo principal es convertir nueve SP en miniartículos repetitivos. La plantilla marca componentes obligatorios, pero permite profundidad desigual, reutilización del contenido común de `index.tex` y agrupación cuando la matriz de evidencia lo aconseje.

## Registro de decisiones

- 2026-07-15 — Se usa un documento especializado en `docs/` y referencias ligeras desde los archivos de instrucciones.
- 2026-07-15 — El bloque de control es obligatorio como delimitación; cuando no aplique, debe justificarse explícitamente y no fabricarse una dinámica física.

## Progreso

Contrato terminado. `docs/07_SP_SECTION_TEMPLATE.md` contiene nueve bloques canónicos, reglas detalladas, un esqueleto LaTeX, adaptación SP0--SP8 y lista de cierre. Los tres puntos de entrada enlazan al documento; las rutas citadas existen y el bloque de código Markdown está balanceado. No se modificaron los archivos `spX.tex`, por lo que no fue necesaria una recompilación de la memoria.
