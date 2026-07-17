# Revisión narrativa y acoplamiento físico de SP0--SP8

## Propósito y resultado observable

Reescribir el capítulo 6 como una progresión científica compacta, formal y legible. La versión final elimina etiquetas internas de gestión, explica con precisión dónde interviene el modelo del robot y presenta cada simulación mediante una comparación cuantitativa inequívoca. El resultado se verifica en el código fuente, el PDF completo y una auditoría de términos meta.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, la metodología común y la evidencia reproducible disponible para SP0--SP8. La trazabilidad técnica permanece en `docs/04_CLAIMS_EVIDENCE.md`, configuraciones, pruebas y manifiestos; no se traslada como lenguaje editorial a la memoria.

## Alcance y no alcance

Se revisan `index.tex`, `sp0.tex`--`sp8.tex`, las conclusiones y la metodología. Se compactan tablas, encabezados y párrafos redundantes; se aclaran modelos, entradas, integradores, escenarios, métricas, baselines y efectos cuantitativos. No se inventan resultados, no se simula una planta inexistente y no se convierten proxies en implementaciones completas de métodos publicados.

## Supuestos y decisiones técnicas

SP0--SP3 son capas estratégicas o cuasiestáticas: las posiciones parametrizan costes y no se afirma movimiento físico. SP4 usa uniciclos dinámicos para aproximación y una planta planar de carga para transporte; ambos experimentos se presentan por separado. SP5 extiende la planta de carga con obstáculos, reparto y saturación. SP6 usa un tiempo de llegada cinemático del reemplazo. SP7--SP8 abstraen cada coalición como cuerpo compuesto sobre rutas discretas.

La formulación común distingue decisión estratégica, aproximación de robots, dinámica de la carga y tráfico/red. Cada SP indica qué estado recibe, qué acción produce y qué modelo transforma esa acción. Los resultados formales conservan enunciado, supuestos y demostración en anexos, sin rótulos editoriales internos. Las comparaciones se articulan como protocolo, cifra principal, interpretación y límite.

## Hitos

- [x] Hito 1 — inventario de lenguaje meta, estructura, modelo físico y evidencia por SP.
- [x] Hito 2 — arquitectura narrativa común y metodología física compactadas.
- [x] Hito 3 — SP0--SP3 reescritos con resultados y fronteras precisas.
- [x] Hito 4 — SP4--SP6 reescritos con planta, control y comparaciones explícitos.
- [x] Hito 5 — SP7--SP8 reescritos con abstracción física, tráfico, red y escalabilidad claros.
- [x] Hito 6 — discusión/conclusiones, auditoría textual, pruebas y PDF revisados.

## Validación ejecutada

- Búsqueda en fuentes y PDF sin `GATE`, `MISSING`, `VALIDADO`, `RAW`, `EXEC`, `OBSERVED`, `Resultado y alcance` ni `\estadoaporte` como rótulos de la memoria.
- Suite completa: 60 pruebas superadas.
- Campañas SP1 y SP5 regeneradas desde sus configuraciones versionadas para actualizar las denominaciones de los métodos.
- Compilación completa: PDF de 109 páginas; cuerpo principal de 74 páginas y anexos de 19 páginas, dentro de los límites VIU.
- Inspección visual de metodología, apertura de resultados, SP4, SP5, SP7, SP8 y conclusiones sin recortes, solapamientos ni tablas fuera de página.

## Resultado y riesgo residual

La memoria distingue ahora con claridad qué SP integra el uniciclo, cuál integra la carga y cuáles emplean proxies cinemáticos o grafos. Los resultados cuantitativos se mantienen vinculados a sus experimentos reales. Persiste una limitación científica deliberadamente visible: no existe todavía una simulación extremo a extremo que una reclutamiento, aproximación, acoplamiento, transporte, fallo, tráfico y red imperfecta en una sola planta.

## Registro de decisiones

- 2026-07-17: retirar del texto académico las etiquetas internas de estado y conservar su función en la matriz de trazabilidad.
- 2026-07-17: no forzar el modelo de uniciclo en SP0--SP3; explicar cómo sus salidas alimentan SP4.
- 2026-07-17: describir SP7--SP8 como abstracciones de coaliciones rígidas con huella y rutas discretas.
- 2026-07-17: mantener separados el experimento de *docking* con uniciclos y el transporte de carga, porque la evidencia disponible no integra ambos procesos.
