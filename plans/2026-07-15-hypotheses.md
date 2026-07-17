# Hipótesis y preguntas de investigación en dos páginas

## Propósito y resultado observable

Sustituir los marcadores provisionales del capítulo 3 por una formulación contrastable de dos páginas: una hipótesis principal, cinco preguntas de investigación y cinco subhipótesis con métricas, contraste y regla de decisión previa.

## Contexto y archivos canónicos

- `docs/00_TFM_CHARTER.md` y `docs/01_VIU_REQUIREMENTS.md`.
- `docs/02_RESEARCH_MATRIX.md`, `docs/03_EXPERIMENT_PROTOCOL.md` y `docs/04_CLAIMS_EVIDENCE.md`.
- `thesis/sections/mainmatter/03-hypotheses.tex`.
- Capítulos 4 y 5 para conservar la frontera entre hipótesis, metodología y resultados.

## Alcance y no alcance

Incluye preguntas, hipótesis, supuestos mínimos, variables de respuesta, comparadores y criterios de refutación. No fija umbrales arbitrarios antes de los pilotos, no presenta resultados y no traslada demostraciones o algoritmos del capítulo 6.

## Supuestos y preguntas resueltas

- Las cinco RQ condensan las seis RQ previas sin eliminar heterogeneidad, acoplamiento, manipulación, resiliencia o escala.
- El modo físico primario sigue siendo transporte rígido/prehensil planar.
- “Apoyo” significa evidencia compatible dentro del dominio ensayado; no equivale a aceptación universal.
- Toda comparación estocástica usa escenarios y semillas pareadas e intervalos de confianza.

## Diseño matemático/técnico

Cada subhipótesis se expresa mediante cuatro elementos: enunciado direccional, métrica canónica, contraste o ablación y criterio de apoyo/refutación. H1 cubre reclutamiento; H2, certificado de `wrench`; H3, conectividad y red; H4, fallos; H5, coste y calidad frente a referentes.

## Plan experimental

Se enlazan SP0--SP8 con las métricas canónicas ya definidas: factibilidad, sobreasignación, falsos positivos mecánicos, tiempo de recuperación, entrega, gap, CPU, memoria, mensajes y bytes. Los umbrales cuantitativos solo se fijarán tras piloto o justificación industrial.

## Hitos

- [x] Hito 1 — capítulo 3 redactado con H principal, RQ1--RQ5 y H1--H5 contrastables.
- [x] Hito 2 — `charter` y matriz de afirmaciones alineados con la nueva numeración.
- [x] Hito 3 — memoria compilada y capítulo 3 verificado visualmente en exactamente dos páginas.

## Validación

- Compilar con LuaLaTeX/Biber y pasadas de estabilización.
- Comprobar que el capítulo 3 ocupa dos páginas numeradas consecutivas.
- Renderizar ambas páginas con Poppler y revisar legibilidad, cortes y transiciones.
- Verificar que cada H contiene métrica, contraste y criterio de refutación.

## Riesgos y mitigaciones

- Hipótesis demasiado fuertes: limitar cada resultado al dominio, supuestos y tipo de evidencia.
- Umbrales arbitrarios: emplear dirección del efecto e intervalos de confianza hasta disponer de piloto.
- Tabla ilegible: preferir una matriz compacta con texto breve y cuerpo mínimo legible.
- Duplicación con metodología: declarar el contraste, pero reservar ejecución y estadística detallada al capítulo 4.

## Registro de decisiones

- 2026-07-15: RQ1 absorbe heterogeneidad y RQ2 reúne acoplamiento con comunicación local para pasar de seis a cinco preguntas sin reducir el alcance científico.
- 2026-07-15: se reemplaza el umbral fijo del 80 % por criterios direccionales, intervalos de confianza y regiones de validez justificadas.

## Progreso

Capítulo final redactado y alineado con el `charter`, la matriz SP0--SP8 y C1--C7. Con la plantilla vigente al cierre, la memoria compila en 65 páginas y el capítulo 3 ocupa exactamente dos páginas físicas consecutivas (17--18 del PDF). La inspección PNG confirma que HP, RQ1--RQ5 y la matriz H1--H5 son legibles y no presentan recortes ni solapamientos. Durante la validación cambió de forma concurrente la numeración y el encabezado de la plantilla; esos cambios ajenos se preservaron.
