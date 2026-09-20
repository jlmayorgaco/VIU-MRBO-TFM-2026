# Resultados preliminares de la revisión V3

**Fecha de corte:** 13 de septiembre de 2026  
**Estado:** lectura y síntesis iniciales; **no** es aún la revisión extensa
terminada ni la versión compacta de cinco páginas para la memoria.

## Resultado principal, en lenguaje directo

La evidencia revisada hasta ahora apunta a que el TFM debe tratar el problema
como una cadena de tres niveles conectados, pero no intercambiables:

1. **SP1 — decisión:** formar una coalición factible de robots heterogéneos,
   considerando capacidades, recursos, costes, plazos e interferencias.
2. **SP2 — ejecución física:** hacer que la coalición se aproxime, mantenga el
   tipo de contacto elegido y transporte la carga con restricciones mecánicas y
   de seguridad explícitas.
3. **SP3 — operación conjunta:** coordinar rutas, prioridades y congestión de
   varias coaliciones y robots libres.

Una buena asignación de SP1 no demuestra por sí misma que SP2 sea físicamente
factible. Tampoco una buena ley de transporte resuelve el tráfico de SP3. Esta
separación será la columna vertebral de la revisión extensa y del diseño
experimental del TFM.

## Qué se ha encontrado y qué significa

| Eje | Resultado localizado | Consecuencia para el TFM | Estado de evidencia |
| --- | --- | --- | --- |
| SP2 físico | La revisión de Tuci, Alkilabi y Akanyeti separa empuje, agarre/prehensión y caging; caging exige preservar un cierre geométrico. | Declarar un modo físico primario. No reutilizar pruebas de agarre rígido para caging o empuje sin un modelo de contacto nuevo. | Revisión ancla; taxonomía, no prueba de un controlador. |
| SP1 / optimización | Chakraa et al. diferencian métodos exactos y aproximados de MRTA, y muestran que asignación, complejidad y restricciones físicas son capas distintas. | Usar ILP/MILP o formulación central equivalente como oráculo en instancias pequeñas, solo si representa las mismas restricciones del caso distribuido. | Revisión ancla; marco y baseline. |
| SP1 / coaliciones con plazos | Guerrero, Oliver y Valero formalizan coaliciones con plazos e interferencia; comparan una referencia entera condicionada con una subasta. | Medir factibilidad, utilidad, tiempo de cómputo e interferencia. Presentar el oráculo central como techo de información global, no como rival arquitectónicamente simétrico. | Artículo primario; evidencia formal y experimental limitada a sus supuestos. |
| Comunicación | Mazdin y Rinner estudian formación/asignación distribuida bajo comunicación imperfecta y comparan políticas temporales, por evento e híbridas. | Incluir mensajes/bytes, regla de disparo, pérdida de mensajes y topología como métricas o factores experimentales. | Artículo primario de simulación; no prueba transporte físico. |
| Integración y plataforma | An et al. sitúan transporte cooperativo, comunicación, coordinación, asignación y plataforma como dimensiones acopladas. | No evaluar el método solo por la asignación final: declarar comunicación, modelo de movimiento/contacto, plataforma y métricas. | Revisión transversal; orienta preguntas y vacíos, no demuestra rendimiento. |

## Implicaciones concretas para la propuesta técnica

La revisión inicial no justifica todavía una afirmación de novedad. Sí define
un diseño defendible para contrastar la propuesta:

- **SP1:** mecanismo distribuido, explicable y basado en juego/potencial o
  dinámica poblacional; comparar contra una formulación central de coaliciones
  con información global y contra un baseline distribuido pertinente.
- **SP2:** seleccionar y declarar un único modo primario de transporte. La
  asignación deberá incluir requisitos que correspondan con capacidades y
  contactos que el controlador pueda realizar.
- **SP3:** no puede quedar implícito: rutas, pasos estrechos, reservas,
  prioridades y congestión necesitan su propio baseline y sus propias métricas.
- **Validación transversal:** reportar factibilidad, utilidad/gap frente al
  oráculo cuando aplique, tiempo de formación, makespan, distancia mínima,
  estado de contacto, mensajes/bytes, CPU y recuperación ante fallo. Las
  garantías solo se declararán si existen supuestos y prueba o evidencia
  experimental específica.

## Cobertura real a este corte

| Elemento | Conteo / estado | Interpretación correcta |
| --- | --- | --- |
| Registro V3 deduplicado | 3.014 identidades bibliográficas | Inventario de descubrimiento, no conjunto final incluido. |
| Nuevos hallazgos por APIs abiertas | 898 identidades DOI/título únicas | Requieren cribado V3; no son evidencia científica. |
| Textos adquiridos históricamente | 244 | No todos contienen texto completo legible. |
| Textos aptos para lectura cercana | 168 | Cola real de lectura y extracción de evidencia. |
| Fichas con pasajes localizados | 5 | Únicas fuentes que sustentan las conclusiones de este informe. |
| Acceso parcial o vista previa | 76 | No puede respaldar claims fuertes hasta obtener una copia legal o revisar manualmente. |
| Web of Science | 154 registros reconciliados; 255 pendientes de exportación | Cobertura parcial: no se puede llamar búsqueda WoS completa. |
| arXiv | API no disponible en esta ejecución | No significa que no haya preprints; la fuente queda pendiente de reintento o consulta manual. |

## Fuentes ya leídas con ficha verificable

1. [Tuci, Alkilabi y Akanyeti (2018)](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/academic-review/literature-review-v3/close-read/C5423D5A19BA0_tuci_2018.md)
2. [Mazdin y Rinner (2021)](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/academic-review/literature-review-v3/close-read/CC1697E0C2E40_mazdin_rinner_2021.md)
3. [An et al. (2023)](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/academic-review/literature-review-v3/close-read/C4F0B5BB85F46_an_2023.md)
4. [Chakraa et al. (2023)](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/academic-review/literature-review-v3/close-read/C1E34C4925F5C_chakraa_2023.md)
5. [Guerrero, Oliver y Valero (2017)](/C:/Users/walla/Documents/Github/VIU-MRBO-TFM-2026/academic-review/literature-review-v3/close-read/C0BBF943B50C0_guerrero_oliver_valero_2017.md)

## Lo que todavía no se puede concluir

- No hay base para afirmar que el método del TFM sea novedoso, óptimo,
  convergente, estable, robusto o escalable.
- No se ha terminado la lectura sistemática de los 168 textos accesibles ni el
  cribado de las 3.014 identidades.
- No procede hacer un meta-análisis: los escenarios, robots, contactos,
  métricas y comparadores son heterogéneos.
- La revisión compacta de cinco páginas se redactará **después** de completar
  la matriz crítica de métodos, baselines, resultados y limitaciones, no antes.

## Dónde seguir el trabajo

- Progreso de lectura: `reports/v3_close_reading_progress.md`.
- Inventario y deduplicación: `data/discovery_registry_v3.csv`.
- Cobertura de consultas abiertas: `reports/v3_open_discovery_coverage.md`.
- Protocolo de inclusión/exclusión: `SCREENING_PROTOCOL.md`.

El siguiente resultado sustantivo será una tabla crítica completa por SP1, SP2
y SP3 —método, supuestos, arquitectura, baseline, métricas, garantías y
limitaciones— y, a partir de ella, la síntesis narrativa extensa.
