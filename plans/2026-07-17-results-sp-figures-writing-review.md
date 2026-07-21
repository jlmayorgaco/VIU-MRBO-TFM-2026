# Revisión experimental y de redacción de Resultados SP0--SP8

## Propósito y resultado observable

Revisar el capítulo 6 y los nueve SP para que cada resultado principal tenga una visualización cuantitativa trazable y para reducir patrones de redacción mecánica sin alterar afirmaciones, cifras ni alcance. El resultado se verificará en los `sp0.tex`--`sp8.tex`, en las figuras generadas desde datos existentes y en el PDF compilado.

## Contexto y archivos canónicos

Rigen `docs/00_TFM_CHARTER.md`--`docs/05_NOTATION.md`, `docs/07_SP_SECTION_TEMPLATE.md`, los datos de `results/`, las configuraciones de `experiments/configs/` y las secciones de `thesis/sections/mainmatter/06-results-and-analysis/`. La matriz `docs/04_CLAIMS_EVIDENCE.md` fija la fuerza máxima de cada conclusión.

## Alcance y no alcance

Se auditan `index.tex` y `sp0.tex`--`sp8.tex`; se incorporan figuras ausentes cuando ya existe evidencia canónica y se reescribe la prosa experimental prioritaria. No se inventan datos, no se elevan resultados piloto a confirmatorios, no se ejecutan campañas nuevas costosas y no se modifican los cambios locales preexistentes del capítulo 5.

## Supuestos y preguntas resueltas

Se interpreta la petición como autorización para revisar e implementar mejoras en el capítulo 6. Una figura debe responder a una hipótesis o limitación concreta; no se añadirá por simetría editorial. Los datos procesados y campañas congeladas tienen precedencia sobre figuras exploratorias de campañas no canónicas.

## Diseño matemático/técnico

La unidad de revisión es la cadena afirmación--métrica--dato--figura--interpretación. Cada SP debe mostrar, como mínimo, el resultado principal y una segunda dimensión necesaria para interpretarlo: dinámica/escala, ablación, coste, comunicación o región de fallo. La reescritura conserva términos canónicos y distingue resultado formal, observación empírica y limitación.

## Plan experimental

No se crean mundos nuevos. Se reutilizan las unidades independientes, contrastes pareados e intervalos ya registrados. Cuando una figura adicional no exista, se generará desde tablas procesadas mediante código versionado, manteniendo semillas de análisis y denominadores. Las figuras mostrarán unidades, tamaño muestral o IC cuando corresponda.

## Hitos

- [x] Inventario SP por SP de figuras usadas, figuras disponibles y huecos de evidencia.
- [x] Auditoría de patrones de redacción y de alineación afirmación--evidencia.
- [x] Incorporación de visualizaciones prioritarias con texto de lectura y limitación.
- [x] Reescritura del bloque experimental y síntesis de cada SP.
- [x] Compilación, revisión visual y pruebas de trazabilidad.

## Validación

Se comprobarán rutas y etiquetas con `rg`, se ejecutarán las pruebas de generación afectadas y se compilará la memoria con el flujo disponible en `thesis/`. La aceptación exige ausencia de referencias rotas, figuras citadas antes de aparecer, captions interpretables, cifras coherentes con tablas y ningún cambio en resultados numéricos.

## Riesgos y mitigaciones

El principal riesgo es reutilizar una figura de una campaña no canónica. Se mitigará contrastando cada ruta con `docs/04_CLAIMS_EVIDENCE.md` y los manifiestos. El segundo riesgo es aumentar demasiado la extensión; se priorizarán paneles complementarios y se recortará prosa redundante. El tercero es homogeneizar aún más la voz; la reescritura variará ritmo y estructura, pero mantendrá precisión académica.

## Registro de decisiones

- 2026-07-17: usar solo datos existentes y campañas canónicas en esta pasada; una nueva campaña requeriría protocolo y coste separados.
- 2026-07-17: preservar sin tocar los cambios locales preexistentes en `05-theoretical-framework.tex` y su plan.
- 2026-07-18: reactivar los gráficos experimentales ocultos en SP0 y SP2--SP8; SP1 ya tenía su gráfico principal activo.
- 2026-07-18: añadir una segunda lectura solo cuando separa métricas no intercambiables: escala/bienestar, dinámica KKT, escenarios, seguridad, recuperación, tráfico o coste de red.
- 2026-07-18: registrar la extensión del capítulo 6 como riesgo editorial y posponer el traslado de tablas a una pasada de compresión con criterio de evidencia.

## Progreso

Revisión completada. Cada SP contiene al menos una figura experimental visible y las secciones con compromisos multidimensionales muestran una segunda lectura pertinente. Se reescribieron introducciones, diseño experimental y síntesis con el patrón fallo heredado--medición--límite. La auditoría queda en `docs/11_RESULTS_SP_FIGURE_WRITING_AUDIT.md`. Pasaron 55 pruebas dirigidas de SP0--SP8 y la memoria se compiló y revisó visualmente. El riesgo pendiente es de extensión: el capítulo 6 ocupa unas 70 páginas y requiere una pasada posterior de compresión selectiva.
