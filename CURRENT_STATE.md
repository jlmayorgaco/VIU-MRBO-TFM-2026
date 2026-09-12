# Estado actual de la revisión bibliográfica

**Etapa:** Stage 1A — corpus candidato y QA completados  
**Fecha de ejecución:** 2026-09-12  
**Repositorio:** `VIU-MRBO-TFM-2026`  
**Rama:** `sp1-final-refactor`  
**HEAD observado:** `307683ea2eac7d7e5a2dc54190bd22b6d8589b7e`

## Resumen ejecutivo

Stage 0 se cerró tras inspeccionar el repositorio y el bundle recibido. La
decisión de arquitectura posterior autorizó continuar bajo la estructura
canónica `academic-review/`, sin crear ni conservar un árbol paralelo
`literature_review/`. Los 32 registros legacy se incorporaron únicamente como
semillas candidatas; no se mezclaron con el ledger del TFM ni se transformaron
en evidencia.

Stage 1A se ejecutó solo para construir y auditar un corpus bibliográfico
candidato con descubrimiento abierto en Crossref y OpenAlex. No se hizo
screening, adquisición de texto completo, lectura profunda, snowballing,
análisis de novedad ni redacción de revisión.

## Entradas y cobertura

| Entrada | Estado |
|---|---|
| Bundle bootstrap | SHA-256 `809ECCDDB33660B3CCAF943A01F1F9CE05E902A2F87727F7D5C4559806722A37` |
| Semillas legacy | 32 filas; preservadas en `academic-review/inputs/legacy/` |
| Exportación WoS | 0 archivos auténticos; `wos_status=pending_external_export` |
| Cobertura declarada | `corpus_coverage=open_discovery_only` |
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

## Artefactos verificables

- `academic-review/data/processed/candidate_corpus_stage1a.csv`
- `academic-review/data/processed/candidate_corpus_stage1a.jsonl`
- `academic-review/logs/stage1a_api_log.csv`
- `academic-review/logs/stage1a_search_log.csv`
- `academic-review/logs/stage1a_dedup_log.csv`
- `academic-review/reports/stage1a_qa.md`
- `academic-review/reports/stage1a_provenance_summary.md`
- `academic-review/reports/WOS_PENDING.md`

Además se conservaron la semilla legacy, el contrato de alcance, el protocolo
de búsqueda, el esquema y el validador dentro de `academic-review/`.

## Validaciones ejecutadas

- `python academic-review/scripts/validate_inputs.py` — correcto: 4 entradas,
  32 semillas y 0 WoS.
- `python -m pytest academic-review/tests -q` — 5 pruebas correctas.
- `python -m py_compile academic-review/scripts/bootstrap_literature.py academic-review/scripts/validate_inputs.py` — correcto.
- CSV y JSONL — 246 filas/líneas y 246 `candidate_id` únicos.
- Campos obligatorios — sin valores ausentes.
- Log de búsqueda — 14/14 estados `ok`; log API sin fallos terminales.

La advertencia de `requests` sobre versiones de `urllib3`/`charset_normalizer`
no impidió la ejecución ni produjo fallos HTTP; queda como nota de entorno para
una futura fijación reproducible de dependencias.

## Estado del árbol y siguiente compuerta

El árbol de trabajo contiene numerosos cambios preexistentes del TFM, que se
han preservado sin limpieza ni reset. Los cambios de esta tarea están aislados
en `academic-review/`, `CURRENT_STATE.md`, `IMPLEMENTATION_PLAN.md` y el plan
operativo correspondiente.

Stage 1A queda detenido aquí, conforme a la autorización. La siguiente
compuerta es Stage 2: incorporar, si el autor lo proporciona, el export WoS
manual y/o semillas originales, calcular hashes de lineage y probar la ingesta
sin pérdida silenciosa. Ningún resultado actual autoriza afirmaciones de
inclusión, estado del arte, novedad o hueco científico.
