# Planes activos

## Stage 1A — corpus candidato de revisión bibliográfica

**Estado:** completado el 2026-09-12  
**Ruta canónica:** `academic-review/`

### Entregable

Construir un corpus candidato reproducible a partir de 32 semillas legacy y
descubrimiento abierto Crossref/OpenAlex, preservando provenance, metadatos
originales, estados de evidencia y logs de API. Detenerse antes de screening,
texto completo, snowballing y análisis de novedad.

### Criterios de aceptación

- [x] 32 semillas importadas como `unverified_seed`.
- [x] `evidence_status=not_evidence` y `screening_status=pending` para todas
  las semillas y candidatos Stage 1A.
- [x] Caché persistente, timeout, límites, reintentos y fallos explícitos.
- [x] Consultas Q1–Q7 ejecutadas en ambos proveedores abiertos.
- [x] DOI/título/autores/año reconciliados conservadoramente.
- [x] Duplicados ambiguos retenidos para revisión.
- [x] CSV, JSONL, logs de API/búsqueda/dedupe y QA generados.
- [x] Sin WoS: cobertura etiquetada `open_discovery_only` y pendiente
  `wos_status=pending_external_export`.
- [x] Pruebas unitarias, compilación Python y auditoría de consistencia
  ejecutadas.

### Resultado

246 candidatos canónicos; 241 con DOI y 5 sin DOI; 26 fusiones exactas; 9
probables duplicados en revisión; 244 metadatos verificados; 2 no resueltos; 0
fallos terminales de API. El detalle está en
`academic-review/reports/stage1a_qa.md`.

### Siguiente tarea autorizable

Stage 2 queda pendiente de la disponibilidad de exportaciones WoS manuales
y/o semillas originales. No avanzar automáticamente a screening ni a la
redacción de conclusiones.

## Stage 1B — auditoría de cobertura y screening bibliográfico

**Estado:** completado y validado el 2026-09-12  
**Entrada congelada:** `academic-review/data/processed/candidate_corpus_stage1a.csv` y `.jsonl`

### Alcance

Auditar identidad bibliográfica, recuperar DOI solo mediante metadatos
observables, reconciliar las 32 semillas, construir la matriz de conceptos,
hacer snowballing limitado de una ronda sobre 15–25 anclas y aplicar screening
reproducible de título/resumen. No descargar masivamente PDFs, no hacer coding
de texto completo y no redactar el estado del arte.

### Compuertas

- [x] Hashes de Stage 1A registrados y verificados como inmutables.
- [x] Protocolo de screening v1 congelado antes de clasificar candidatos.
- [x] Resolución de los 9 registros probables y auditoría de los 5 sin DOI.
- [x] Recall audit de una sola ronda con anclas trazables.
- [x] Screening completo, taxonomía preliminar y QA de invariantes.
- [x] Muestras auditadas manualmente; desacuerdos y correcciones registrados.
- [x] Informe Stage 1B generado y etapa detenida.

### Resultado

1218 candidatos; 340 `include_fulltext`, 280 `maybe_fulltext` y 598
`exclude`; 974 registros nuevos por una ronda de snowballing, de los cuales
463 fueron relevantes o plausibles; 2 DOI recuperados de 5 intentos; 32
semillas reconciliadas (13 verificadas, 17 corregidas y 2 no resueltas); 0
fallos terminales en la corrida final. La auditoría manual cubrió 20
incluidos, 20 excluidos y 20 `maybe`, con 0 correcciones en revisión de un
único auditor. El diagnóstico no demuestra saturación. Stage 1B se detiene
antes de descarga masiva, coding de texto completo y redacción del estado del
arte.

### Siguiente compuerta

Esperar exportaciones WoS/semillas originales si están disponibles y, en una
etapa separada, adquirir legalmente los textos completos de la cola. Ningún
registro Stage 1B es evidencia científica todavía.

### Stage 1C — reparación acotada de consultas

**Estado: completado y validado el 2026-09-12.**

- [x] Congelar el hash del derivado Stage 1B antes de crear el derivado de
  reparación.
- [x] Ejecutar una única ronda de reparación con ocho familias nuevas, sin
  modificar Q1–Q7 y respetando el máximo de 12 familias.
- [x] Ejecutar una segunda comprobación one-hop acotada sobre las 20 anclas
  seleccionadas.
- [x] Reconciliar conservadoramente los nuevos registros y volver a aplicar el
  screening determinista v1 sin promover ningún registro a evidencia.
- [x] Validar unicidad, ausencia de duplicados DOI, estados de evidencia y
  correspondencia exacta de la cola de texto completo.
- [x] Generar el informe, logs, manifest y pruebas de regresión de Stage 1C.

La reparación produjo 278 registros nuevos por consulta y 730 por la
comprobación de recall; 437 fueron relevantes o plausibles. El corpus derivado
contiene 2226 registros: 515 `include_fulltext`, 542 `maybe_fulltext` y 1169
`exclude`; la cola de adquisición contiene 1057 registros. Persistió evidencia
de terminología relevante no cubierta, por lo que no se declara saturación; la
expansión automática queda detenida tras esta ronda.

### Siguiente compuerta

Pasar a Stage 2 con la cola Stage 1C para intentar adquisición legal/open de
texto completo. Los trabajos inaccesibles se conservarán como
`abstract_only` o `unavailable_legally`; no se usarán para afirmaciones
detalladas de método, resultados o garantías.

### Stage 2 — adquisición legal de texto completo

**Estado: completado y validado el 2026-09-12.**

- [x] Congelar los CSV Stage 1C y registrar sus hashes.
- [x] Consultar ubicaciones OA de OpenAlex por lotes y enlaces públicos de
  Crossref, sin autenticación ni bypass.
- [x] Descargar/cachear rutas públicas y guardar cada objeto bajo
  `academic-review/data/fulltext/<candidate_id>/`.
- [x] Verificar identidad por DOI/título; rechazar contenido incompatible,
  paywalled o solo landing page.
- [x] Registrar los seis estados permitidos, URL, timestamp, hash, MIME, tamaño,
  nota de acceso y error.
- [x] Ejecutar QA, tests y manifest de adquisición.

Resultado: 1057 registros procesados; 230 objetos verificados (144 PDF y 86
HTML), 30 `abstract_only`, 776 `unavailable_legally` y 21
`retrieval_error`. Los binarios se mantienen locales y fuera de Git; los
manifests y hashes permiten reproducir la adquisición.

### Stage 3 — coding científico de texto completo

**Estado: completado y validado el 2026-09-12.**

- [x] Leer los 230 objetos verificados desde sus rutas locales.
- [x] Generar matriz CSV/JSONL con problema, arquitectura, información,
  método, capa física, ejecución, teoría, experimentos, resultados,
  limitaciones, rol y localización de snippets.
- [x] Mantener `abstract_only`, `metadata_only` y `retrieval_error` separados
  de la evidencia de texto completo.
- [x] Generar QA, log de coding y pruebas.

El resultado es un primer pase estructural determinista: localiza evidencia en
texto real, pero requiere lectura humana cercana para confirmar ecuaciones,
tablas, figuras, supuestos, garantías y resultados antes de usarlos como
claims fuertes.

### Siguiente compuerta

Fijar Stage 4 con las 16 analíticas requeridas, tablas/figuras reproducibles y
auditoría adversarial de solapamiento por ejes SP1–SP3.

### Stage 4 — síntesis, taxonomía, figuras y auditoría de novedad

**Estado: completado y validado el 2026-09-12.**

- [x] Generar las 16 analíticas requeridas desde la matriz y el corpus Stage 2.
- [x] Producir tablas/figuras para selección, temporalidad, métodos,
  arquitectura, robots/aplicaciones, heterogeneidad, coaliciones, física,
  contacto/wrench, comunicación, fallos, validación, heatmaps, mapa de
  evidencia y gaps.
- [x] Separar conteos descriptivos de impacto científico y conservar el nivel
  de evidencia en la interpretación.
- [x] Generar la auditoría adversarial con prior art candidato y estados de
  novedad prudentes.
- [x] Inspeccionar figuras representativas y ejecutar pruebas de análisis.

Resultado: 20 análisis totales (16 requeridos), 23 tablas CSV, 20 PNG, triage
de 94 CORE y 123 ENABLING, y auditoría de novedad sin conclusión final.

### Stage 5 — paquete académico final

**Estado: completado y validado el 2026-09-12.**

- [x] Generar revisión completa y compacta de carácter analítico, no
  narración paper-by-paper.
- [x] Responder explícitamente las 16 preguntas TFM sobre asignación,
  coaliciones, transporte físico, comunicación, fallos, baselines y claims.
- [x] Generar plan de integración SP1–SP3 y matriz claim-source con
  `candidate_id`, DOI, localización, estado de soporte y uso permitido.
- [x] Generar triage CORE/ENABLING, exclusiones, limitaciones y manifest de
  reproducción.
- [x] Verificar que la tesis canónica y las figuras TikZ protegidas no fueron
  modificadas.
- [x] Ejecutar QA final, tests, parsing de CSV/JSONL y búsqueda de límites de
  novedad.

El paquete contiene 10 archivos finales, 5 filas de trazabilidad de claims y
mantiene la conclusión de novedad retenida por ausencia de WoS y por el
carácter estructural del coding.

### Estado final y riesgos abiertos

El pipeline autónomo queda completado bajo `academic-review/`. Permanecen como
trabajo científico posterior la exportación WoS, la lectura humana cercana de
prior art, la confirmación de ecuaciones/tablas/figuras y la validación
experimental del método del TFM.
