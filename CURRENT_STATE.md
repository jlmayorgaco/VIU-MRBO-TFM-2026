# Estado actual de la revisión bibliográfica

**Etapa:** Stage 5 — paquete académico final completado  
**Fecha de ejecución:** 2026-09-12  
**Repositorio:** `VIU-MRBO-TFM-2026`  
**Rama:** `sp1-final-refactor`  
**Commits de implementación:** Stage 1A congelado en `e3bdfb553dc1f2fb32fa4a1f3c721d39200666b3`; Stage 1B en `3a99e1b8`; Stage 1C en `1ffe17e6`; Stage 2 en `f0757abd`; Stage 3 en `687d877e0`; Stage 4 en `f0ea343ad`; Stage 5 en `2d182e260`.

## Resumen ejecutivo

Stage 0 se cerró tras inspeccionar el repositorio y el bundle recibido. La
decisión de arquitectura posterior autorizó continuar bajo la estructura
canónica `academic-review/`, sin crear ni conservar un árbol paralelo
`literature_review/`. Los 32 registros legacy se incorporaron únicamente como
semillas candidatas; no se mezclaron con el ledger del TFM ni se transformaron
en evidencia.

Stage 1A se ejecutó solo para construir y auditar un corpus bibliográfico
candidato con descubrimiento abierto en Crossref y OpenAlex. Sobre esa entrada
congelada se completó Stage 1B: auditoría de identidad, recuperación
conservadora de DOI, reconciliación de las 32 semillas, matriz de conceptos,
snowballing acotado de una ronda y screening de título/resumen. No se hizo
descarga masiva de PDF, coding de texto completo, análisis de novedad ni
redacción de revisión. El diagnóstico de Stage 1B activó una única ronda Stage
1C de reparación de consultas y otra comprobación acotada de recall.

## Entradas y cobertura

| Entrada | Estado |
|---|---|
| Bundle bootstrap | SHA-256 `809ECCDDB33660B3CCAF943A01F1F9CE05E902A2F87727F7D5C4559806722A37` |
| Semillas legacy | 32 filas; preservadas en `academic-review/inputs/legacy/` |
| Exportación WoS | 0 archivos auténticos; `wos_status=pending_external_export` |
| Cobertura Stage 1A | `corpus_coverage=open_discovery_only` |
| Cobertura Stage 1B | `coverage_status=open_sources_plus_limited_snowballing` |
| Cobertura Stage 1C | `coverage_status=open_sources_plus_limited_snowballing` |
| CONTACT_EMAIL | Configurado solo en `academic-review/.env.literature`, ignorado por Git |
| Claves opcionales | No requeridas ni configuradas |
| Ledger/evidencia previos | No ingeridos, sobrescritos ni auto-fusionados |

La auditoría previa a Stage 1A registró 32 semillas, cero WoS y cero llamadas
externas. La entrada WoS futura deberá añadirse como una procedencia nueva y
reconciliarse sin sobrescribir el corpus abierto.

## Implementación entregada

La implementación se encuentra exclusivamente bajo `academic-review/` e
incluye configuración del protocolo Q1–Q7, esquema de candidatos, cliente HTTP
con caché persistente, reintentos acotados, logs de petición, normalización,
deduplicación conservadora, importación de semillas y validación de entradas.

Las expresiones Booleanas del protocolo se conservan literalmente en el log de
búsqueda. Para OpenAlex se registra además una traducción explícita a su
sintaxis `search` de texto completo; el hash y los parámetros efectivos quedan
en los logs de API.

## Resultados Stage 1A

| Métrica | Resultado |
|---|---:|
| Semillas importadas | 32 |
| Registros crudos reconciliados | 272 |
| Candidatos canónicos finales | 246 |
| DOI presente / ausente | 241 / 5 |
| Duplicados exactos fusionados | 26 |
| Probables duplicados en revisión | 9 |
| Metadatos verificados | 244 |
| Registros no resueltos o insuficientes | 2 |
| Fallos de API | 0 |
| Ejecuciones de consultas | 14 (Q1–Q7 × Crossref/OpenAlex) |
| Eventos HTTP registrados | 47 |
| Cobertura temporal no ausente | 1994–2026 |
| Años sin dato | 38 candidatos |

Provenance cruda: Crossref 175, OpenAlex 65 y `legacy_review` 32. En el
corpus final, la procedencia registrada es Crossref 190, OpenAlex 65 y
`legacy_review` 32; un candidato puede contar en varias procedencias.

Las 32 filas con `legacy_seed_id` mantienen:

```text
verification_status=unverified_seed
evidence_status=not_evidence
screening_status=pending
```

De ellas, 30 tienen `metadata_verification_status=metadata_verified` y 2
quedan `unresolved`. El enriquecimiento de metadatos no cambia la frontera de
evidencia ni constituye una decisión de screening.

## Resultados Stage 1B

| Métrica | Resultado |
|---|---:|
| Candidatos Stage 1B | 1218 |
| Registros nuevos por snowballing acotado | 974 |
| Nuevos relevantes/plausibles | 463 |
| Duplicados probables auditados | 9; 4 alias fusionados y 5 retenidos como distintos |
| DOI recuperados por metadatos | 2 de 5 intentos |
| Semillas legacy | 13 verificadas, 17 corregidas, 2 no resueltas |
| `include_fulltext` / `maybe_fulltext` / `exclude` | 340 / 280 / 598 |
| QA manual | 20 / 20 / 20; 0 correcciones; auditoría de un revisor |
| Fallos terminales de API en la corrida final | 0 |

La expansión por una ronda no constituye una estimación formal de recall ni
una prueba de saturación; el diagnóstico observó literatura adicional y no
permite declarar exhaustividad. Todos los registros siguen con
`evidence_status=not_evidence`; la cola de texto completo es solo una entrada
de adquisición y verificación posterior.

## Resultados Stage 1C

| Métrica | Resultado |
|---|---:|
| Familias de consulta de reparación | 8 (16 ejecuciones Crossref/OpenAlex) |
| Candidatos Stage 1C | 2226 |
| Nuevos por consultas de reparación | 278 |
| Nuevos relevantes/plausibles por consultas | 126 |
| Nuevos por segunda comprobación one-hop | 730 |
| Relevantes/plausibles de la comprobación | 311 |
| `include_fulltext` / `maybe_fulltext` / `exclude` | 515 / 542 / 1169 |
| Cola Stage 1C | 1057 |
| Fallos terminales de API | 0 |

La reparación confirmó cobertura adicional en juegos poblacionales/evolutivos,
seguridad/CBF, contexto industrial, formación/docking, terminología
multi-agent, transporte colectivo y factibilidad de fuerza/wrench. No se
ejecutarán más consultas de reparación en esta ronda; la siguiente compuerta
es la adquisición legal de texto completo.

## Resultados Stage 2

| Métrica | Resultado |
|---|---:|
| Cola procesada | 1057 |
| Texto completo verificado | 230 (144 PDF, 86 HTML, 0 XML) |
| `abstract_only` | 30 |
| `unavailable_legally` | 776 |
| `retrieval_error` | 21 |
| Fallos terminales de API | 0 |
| Política de acceso | legal/open sin autenticación ni bypass |

Cada objeto promovido conserva URL final, timestamp, SHA-256, MIME, tamaño,
ruta local y estado de identidad DOI/título. Los binarios permanecen locales y
fuera de Git por tamaño y condiciones de redistribución; los manifests y logs
son versionados.

## Resultados Stage 3

| Métrica | Resultado |
|---|---:|
| Filas de la matriz de evidencia | 1057; IDs únicos |
| Coding de texto completo verificado | 230 |
| Coding limitado a resumen | 30 |
| No codificable sin texto completo | 797 |
| Errores de extracción | 0 |
| Modo | primer pase estructural determinista con páginas/snippets |
| Roles CORE / ENABLING / CONTEXT / BASELINE / SURVEY | 94 / 123 / 800 / 19 / 21 |

La matriz no convierte vocabulario observado en resultados, teoremas,
garantías o claims de novedad. Los campos detallados de filas
`metadata_only`/`retrieval_error` permanecen vacíos.

## Resultados Stage 4

| Métrica | Resultado |
|---|---:|
| Analíticas requeridas | 16 |
| Analíticas totales | 20 |
| Tablas CSV de análisis | 23 |
| Figuras PNG | 20 |
| Filas CORE / ENABLING triage | 94 / 123 |
| Auditoría adversarial | generada; novedad final retenida |

Las salidas incluyen selección, temporalidad, familias de método,
arquitectura, robots/aplicaciones, heterogeneidad, coaliciones, factibilidad
física, contacto/wrench, comunicación, fallos/recuperación, validación,
heatmaps de método-capacidad y problema-familia, mapa de evidencia SP1–SP3 y
mapa explícito de gaps. Se inspeccionaron visualmente figuras representativas
sin clipping ni solapamientos. Los conteos son descriptivos y no impacto
científico.

## Resultados Stage 5

| Métrica | Resultado |
|---|---:|
| Archivos finales | 10 |
| Filas de claim-source matrix | 5 |
| CORE / ENABLING triage | 94 / 123 |
| Excluidos preservados | 1169 |
| Preguntas TFM respondidas explícitamente | 16 |
| Tesis canónica modificada | no |
| Claim final de novedad | retenido/no emitido |

El paquete final es integración-ready en Markdown/CSV/JSON, con revisión
analítica completa y compacta, plan SP1–SP3, matriz de trazabilidad, triage,
limitaciones y reproducción. No se generó una variante LaTeX no compilada ni
se alteró el manuscrito oficial.

## Artefactos verificables

- `academic-review/data/processed/candidate_corpus_stage1a.csv`
- `academic-review/data/processed/candidate_corpus_stage1a.jsonl`
- `academic-review/logs/stage1a_api_log.csv`
- `academic-review/logs/stage1a_search_log.csv`
- `academic-review/logs/stage1a_dedup_log.csv`
- `academic-review/reports/stage1a_qa.md`
- `academic-review/reports/stage1a_provenance_summary.md`
- `academic-review/reports/WOS_PENDING.md`
- `academic-review/data/processed/candidate_corpus_stage1b.csv`
- `academic-review/data/processed/fulltext_queue_stage1b.csv`
- `academic-review/logs/stage1b_duplicate_resolution.csv`
- `academic-review/logs/stage1b_doi_recovery.csv`
- `academic-review/logs/stage1b_legacy_reconciliation.csv`
- `academic-review/logs/stage1b_screening_log.csv`
- `academic-review/logs/stage1b_snowball_log.csv`
- `academic-review/logs/stage1b_api_log.csv`
- `academic-review/reports/search_concept_matrix.md`
- `academic-review/reports/stage1b_recall_audit.md`
- `academic-review/reports/stage1b_screening_qa.md`
- `academic-review/protocol/screening_protocol_v1.md`
- `academic-review/manifests/stage1a_freeze_manifest.json`
- `academic-review/data/processed/candidate_corpus_stage1c.csv`
- `academic-review/data/processed/candidate_corpus_stage1c.jsonl`
- `academic-review/data/processed/fulltext_queue_stage1c.csv`
- `academic-review/logs/stage1c_query_repair_log.csv`
- `academic-review/logs/stage1c_recall_log.csv`
- `academic-review/logs/stage1c_anchor_manifest.csv`
- `academic-review/logs/stage1c_api_log.csv`
- `academic-review/manifests/stage1b_freeze_manifest.json`
- `academic-review/config/stage1c_query_repair.yaml`
- `academic-review/reports/stage1c_query_repair_report.md`
- `academic-review/config/stage2_acquisition.yaml`
- `academic-review/data/processed/candidate_corpus_stage2.csv`
- `academic-review/data/processed/fulltext_queue_stage2.csv`
- `academic-review/logs/stage2_fulltext_acquisition.csv`
- `academic-review/logs/stage2_fulltext_attempts.csv`
- `academic-review/logs/stage2_api_log.csv`
- `academic-review/manifests/stage1c_freeze_manifest.json`
- `academic-review/reports/stage2_acquisition_qa.md`
- `academic-review/config/stage3_codebook.yaml`
- `academic-review/data/processed/fulltext_evidence_matrix.csv`
- `academic-review/data/processed/fulltext_evidence_matrix.jsonl`
- `academic-review/logs/stage3_coding_log.csv`
- `academic-review/reports/stage3_fulltext_qa.md`
- `academic-review/scripts/stage4_synthesize.py`
- `academic-review/tests/test_stage4.py`
- `academic-review/tables/stage4_analysis_summary.json`
- `academic-review/tables/stage4_analysis_index.csv`
- `academic-review/figures/analysis_01_selection_flow.png` … `analysis_20_execution_terms.png`
- `academic-review/reports/stage4_synthesis_qa.md`
- `academic-review/reports/adversarial_novelty_audit.md`
- `academic-review/scripts/stage5_finalize.py`
- `academic-review/tests/test_stage5.py`
- `academic-review/final/literature_review_full.md`
- `academic-review/final/literature_review_compact.md`
- `academic-review/final/tfm_integration_plan.md`
- `academic-review/final/claim_source_matrix.csv`
- `academic-review/final/core_papers.csv`
- `academic-review/final/enabling_papers.csv`
- `academic-review/final/excluded_papers.csv`
- `academic-review/final/review_limitations.md`
- `academic-review/final/reproducibility_manifest.md`
- `academic-review/final/reproducibility_manifest.json`
- `academic-review/reports/stage5_final_package_qa.md`

Además se conservaron la semilla legacy, el contrato de alcance, el protocolo
de búsqueda, el esquema y el validador dentro de `academic-review/`.

## Validaciones ejecutadas

- `python academic-review/scripts/validate_inputs.py` — correcto: 4 entradas,
  32 semillas y 0 WoS.
- `python -m pytest academic-review/tests -q` — 30 pruebas correctas.
- `python -m py_compile academic-review/scripts/bootstrap_literature.py academic-review/scripts/validate_inputs.py` — correcto.
- CSV y JSONL — 246 filas/líneas y 246 `candidate_id` únicos.
- Campos obligatorios — sin valores ausentes.
- Log de búsqueda — 14/14 estados `ok`; log API sin fallos terminales.
- Stage 1B — 1218 IDs únicos, 0 DOI duplicados, decisiones y razones válidas,
  cola igual a `include_fulltext + maybe_fulltext`, provenance presente y
  exclusiones sin etiquetas temáticas.
- Stage 1C — 2226 IDs únicos, 0 DOI duplicados, cola igual a
  `include_fulltext + maybe_fulltext`, provenance presente y 8/8 familias de
  reparación procesadas.
- Stage 2 — 1057 filas con estados válidos, 230 objetos adquiridos con
  identidad verificada, hashes/rutas presentes y entradas fuera de Git
  excluidas por la política de binarios.
- Stage 3 — 1057 filas únicas, 230 textos completos leídos, filas limitadas
  por nivel de evidencia y JSONL/CSV generados.
- Stage 4 — 16 analíticas requeridas, 20 análisis totales, tablas/figuras
  generadas desde CSV/JSONL y auditoría adversarial sin claim final de novedad.
- Stage 5 — paquete final, 5 claims trazables, 16 preguntas TFM contestadas,
  limitaciones y reproducción generadas sin modificar el manuscrito.

La advertencia de `requests` sobre versiones de `urllib3`/`charset_normalizer`
no impidió la ejecución ni produjo fallos HTTP; queda como nota de entorno para
una futura fijación reproducible de dependencias.

## Estado del árbol y siguiente compuerta

El árbol de trabajo contiene numerosos cambios preexistentes del TFM, que se
han preservado sin limpieza ni reset. Los cambios de esta tarea están aislados
en `academic-review/`, `CURRENT_STATE.md`, `IMPLEMENTATION_PLAN.md` y el plan
operativo correspondiente.

Stage 5 queda completado como paquete de revisión independiente. WoS continúa
pendiente y la lectura humana cercana/validación experimental siguen siendo
riesgos científicos abiertos; no se emite afirmación de inclusión definitiva,
estado del arte, novedad o hueco universal.
