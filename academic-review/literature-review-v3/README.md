# Literatura V3: mapeo sistematizado y síntesis crítica

Este directorio es el derivado auditable para la revisión extensa del TFM. No
sobrescribe los corpus V1/V2: los conserva como descubrimiento histórico y
semillas, mientras que V3 registra de manera independiente sus consultas,
criterios, decisiones y evidencia.

Ejecutar la preparación local:

```powershell
python academic-review/scripts/prepare_v3_literature_review.py
```

El comando genera el ledger de consultas, semillas, cola priorizada de lectura,
fichas JSONL, QA y manifiesto. Una fila de la cola no puede utilizarse para una
afirmación científica hasta que la ficha tenga un localizador de pasaje
verificado y un veredicto de revisión cercana.

Después de preparar el corpus, ejecute la auditoría de accesibilidad y el
seguimiento de fichas:

```powershell
python academic-review/scripts/audit_v3_fulltexts.py --workers 12
python academic-review/scripts/build_v3_close_reading_tracker.py
```

Los resultados están en `data/fulltext_adequacy_audit_v3.csv` y
`data/close_reading_tracker_v3.csv`. Los paquetes de texto para lectura cercana
se generan de forma acotada y desplazable por prioridad:

```powershell
python academic-review/scripts/build_v3_reading_packet.py --tier P0 --offset 0 --limit 12 --output academic-review/literature-review-v3/packets/P0_batch_001.md
```

Los paquetes son un banco de pasajes, no una síntesis ni evidencia apta para
citar por sí misma.

El análisis descriptivo reproducible y el manuscrito de síntesis se generan o
consultan en:

```powershell
python academic-review/scripts/analyze_v3_literature.py
```

- `final/REVISION_SISTEMATIZADA_MRTA_COT_AMR_V3.md`: manuscrito principal.
- `reports/advanced_mapping_results_v3.md`: resumen de conteos.
- `data/analytic_corpus_v3.csv`: codificación de título/resumen.
- `data/method_lifecycle_v3.csv`: evolución temporal prudente.
- `close-read/`: 20 fichas con localizadores y límites.
- `manifests/v3_analysis_manifest.json`: hashes y base de codificación.

La búsqueda abierta separada de V3 usa únicamente APIs públicas y deja Web of
Science y Google Scholar como fuentes manuales:

```powershell
python academic-review/scripts/run_v3_open_discovery.py --sources crossref,openalex --limit-per-query 25
```

Sus respuestas quedan en `raw/`, los eventos en `logs/` y el resultado
deduplicado de descubrimiento en `data/v3_open_discovery_unique.csv`. Las
fuentes se acumulan entre ejecuciones; una fuente que no responda permanece
explícitamente con estado parcial o bloqueado en `data/query_execution_v3.csv`.

La estrategia, límites y gates están en
`plans/2026-09-13-systematic-literature-review-v3.md`.

## Dashboard completo y bibliometría

La Figura 4 recalculada y el mapa bibliométrico se generan desde el corpus
analítico congelado, sin reutilizar los conteos del corte legado de 54
documentos:

```powershell
python academic-review/scripts/build_v3_full_corpus_bibliometrics.py
python academic-review/scripts/build_full_corpus_visual_review.py
```

El primer comando produce tablas intermedias, figuras PDF/PNG y un manifiesto
en `compact-7p-full/`. El segundo ensambla el capítulo de siete páginas en
`output/pdf/MROB_literature_review_7p_full_corpus_bibliometrics.pdf`, dejando
intacta la versión aprobada de seis páginas.

La composición temática usa conteo fraccional: un documento multietiqueta
reparte un peso total de uno entre sus familias. La diversidad es Shannon
normalizado por `log(7)` en una ventana retrospectiva de tres años. La red de
coautoría conserva cadenas exactas y no resuelve identidad mediante ORCID; los
nodos no deben interpretarse como ranking de productividad o impacto.
