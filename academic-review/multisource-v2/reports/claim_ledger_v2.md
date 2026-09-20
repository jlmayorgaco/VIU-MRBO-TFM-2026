# V2 claim ledger

Ledger reconstruido desde los artefactos de la campaña. Los claims son descriptivos del proceso y conservan una frontera explícita contra claims científicos fuertes.

## V2-C01

**Claim:** La campaña V2 produjo 1225 registros normalizados y un derivado reconciliado de 3033 candidatos a partir de 2226 candidatos V1.
**Estado:** `supported`; nivel `artifact_derived`.
**Artefactos:** `data/processed/candidate_records_v2.csv;data/processed/candidate_corpus_v2_reconciled.csv`
**Uso permitido:** describir el flujo y el tamaño del derivado
**Límite:** No es una afirmación de recall, saturación ni impacto científico.

## V2-C02

**Claim:** Las fuentes producen rendimientos marginales y solapamientos distintos bajo la celosía F1–F16.
**Estado:** `supported`; nivel `artifact_derived`.
**Artefactos:** `data/processed/source_marginal_yield.csv;data/processed/source_overlap_matrix.csv;logs/search_events.csv`
**Uso permitido:** comparar descriptivamente proveedores y priorizar revisión
**Límite:** El rendimiento depende del orden de fuentes y no estima cobertura total.

## V2-C03

**Claim:** Se registraron 1789 aristas de una comprobación one-hop acotada sobre anclas DOI V1 mediante OpenCitations.
**Estado:** `supported`; nivel `artifact_derived`.
**Artefactos:** `data/processed/one_hop_citation_edges.csv;logs/api_events.csv`
**Uso permitido:** descubrimiento y priorización de lectura
**Límite:** Una arista de citación no demuestra relevancia, soporte de claim ni novedad.

## V2-C04

**Claim:** Unpaywall devolvió 500 respuestas de enriquecimiento DOI dentro del límite configurado.
**Estado:** `supported`; nivel `artifact_derived`.
**Artefactos:** `data/processed/unpaywall_enrichment.csv;logs/api_events.csv`
**Uso permitido:** priorizar adquisición OA legal
**Límite:** Una ubicación OA requiere verificación de identidad, licencia, versión y contenido.

## V2-C05

**Claim:** Google Scholar, WoS, Scopus e IEEE Xplore no fueron automatizados; se generaron paquetes manuales de consulta/exportación.
**Estado:** `supported`; nivel `protocol_and_artifact`.
**Artefactos:** `manual-packs/;reports/manual_access_boundary.md`
**Uso permitido:** declarar una limitación de cobertura
**Límite:** La no automatización no equivale a ausencia de registros en esas bases.
