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
