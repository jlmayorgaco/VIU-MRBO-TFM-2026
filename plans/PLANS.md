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
