"""Stage 5: assemble the review package without modifying the canonical thesis.

The final documents are generated from Stage 2--4 artifacts. Claims in the
package are deliberately typed as descriptive review observations, candidate
prior art, or unresolved hypotheses; the script never upgrades a structural
coding signal into a theorem, performance result, or novelty claim.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "tables"
REPORTS = BASE / "reports"
FINAL = BASE / "final"
MATRIX = PROCESSED / "fulltext_evidence_matrix.csv"
CORPUS = PROCESSED / "candidate_corpus_stage2.csv"
for directory in [FINAL]:
    directory.mkdir(parents=True, exist_ok=True)

CLAIM_SUPPORT_STATUSES = (
    "supported",
    "partially_supported",
    "contradicted",
    "unclear",
    "not_tested",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def cite(row: dict[str, Any]) -> str:
    title = clean(row.get("title")) or "Título no disponible"
    year = clean(row.get("year")) or "s.f."
    doi = clean(row.get("doi"))
    link = f"[DOI](https://doi.org/{doi})" if doi else "DOI no disponible"
    return f"{title} ({year}; {link})"


def top_terms(rows: list[dict[str, str]], field: str, limit: int = 8) -> list[tuple[str, int]]:
    counts = Counter()
    for row in rows:
        for value in clean(row.get(field)).split(";"):
            value = value.strip()
            if value and value.lower() != "unclear":
                counts[value] += 1
    return counts.most_common(limit)


def format_terms(rows: list[dict[str, str]], field: str, limit: int = 8) -> str:
    return ", ".join(f"`{term}` ({count})" for term, count in top_terms(rows, field, limit)) or "sin términos observados"


def main() -> int:
    if not MATRIX.exists() or not CORPUS.exists():
        raise FileNotFoundError("Stage 2 corpus and Stage 3 matrix are required")
    matrix = read_csv(MATRIX)
    corpus = read_csv(CORPUS)
    if len(matrix) != 1057 or len({row.get("candidate_id") for row in matrix}) != len(matrix):
        raise RuntimeError("Stage 5 invariant failure: expected 1057 unique matrix rows")
    stage4_summary = json.loads((TABLES / "stage4_analysis_summary.json").read_text(encoding="utf-8"))
    interface_rows = read_csv(TABLES / "analysis_16_tfm_interface_coverage_detail.csv")
    core = read_csv(FINAL / "core_papers.csv")
    enabling = read_csv(FINAL / "enabling_papers.csv")
    excluded = read_csv(FINAL / "excluded_papers.csv")
    evidence_counts = Counter(row.get("evidence_strength") for row in matrix)
    role_counts = Counter(row.get("scientific_role") for row in matrix)
    fulltext_rows = [row for row in matrix if row.get("evidence_strength") == "fulltext_verified"]
    ranked = sorted(fulltext_rows, key=lambda row: (row.get("scientific_role") not in {"CORE", "ENABLING", "FOUNDATIONAL"}, clean(row.get("title"))))
    prior_art = ranked[:24]
    sp = {row["subproblem"]: row for row in interface_rows}

    full = f"""# Revisión de literatura: coordinación distribuida de múltiples AMR

Generada UTC: {utc_now()}

## Resumen ejecutivo

Esta revisión organiza evidencia bibliográfica para el TFM sobre coordinación
distribuida local de múltiples AMR, formación de coaliciones, transporte
cooperativo de cargas heterogéneas y planificación/tráfico. El derivado Stage
1C contiene **{len(corpus)}** candidatos; la cola de texto completo contiene
**{sum(row.get('screening_decision') in {'include_fulltext', 'maybe_fulltext'} for row in corpus)}** registros.
Stage 2 verificó **{evidence_counts['fulltext_verified']}** objetos de texto completo
por identidad; **{evidence_counts['abstract_only']}** quedaron limitados al
resumen, **{evidence_counts['metadata_only']}** solo tienen metadatos y
**{evidence_counts['retrieval_error']}** presentan error operativo de recuperación.

El resultado es una síntesis de revisión reproducible y una base de lectura.
No es un meta-análisis: los trabajos modelan problemas, plataformas, métricas
y niveles de evidencia heterogéneos. Tampoco establece por sí sola novedad,
optimalidad, convergencia, estabilidad, robustez o escalabilidad del TFM.

## Alcance y protocolo

La búsqueda combinó descubrimiento abierto en Crossref y OpenAlex, screening
de título/resumen, una ronda acotada de snowballing y una ronda única de
reparación con ocho familias dirigidas. Las familias de reparación cubrieron
juegos poblacionales/evolutivos/potenciales, seguridad y CBF, contexto
industrial, formación/docking, coordinación multi-agent, transporte colectivo,
fuerza/wrench y AMR/AGV logístico. La exportación de Web of Science continúa
pendiente, por lo que no se declara exhaustividad.

Stage 2 usó exclusivamente rutas públicas legales/open observadas en metadatos
o enlaces públicos de Crossref. No se usaron credenciales, proxy institucional,
bypass de paywall ni alteraciones de restricciones de acceso. Los binarios
locales se conservan fuera de Git por tamaño y condiciones de redistribución;
los manifests, URLs, hashes y estados sí quedan trazados.

## Arquitectura de evidencia

La matriz Stage 3 es un primer coding estructural de los textos extraídos. Las
señales observadas se guardan con snippets y páginas/secciones cuando existen,
pero requieren confirmación humana de lectura cercana antes de sustentar una
afirmación fuerte.

| Nivel | Registros |
|---|---:|
| Texto completo verificado | {evidence_counts['fulltext_verified']} |
| Solo resumen | {evidence_counts['abstract_only']} |
| Solo metadatos | {evidence_counts['metadata_only']} |
| Error de recuperación | {evidence_counts['retrieval_error']} |

Roles preliminares: {', '.join(f'`{key}`={role_counts[key]}' for key in sorted(role_counts))}.
Son etiquetas de triage, no jerarquías de calidad ni de citación.

## Hallazgos organizados por SP

### SP1 — formación distribuida de coaliciones

El corpus de la cola contiene {sp.get('SP1', {}).get('all_queue_records', 0)} registros
con señal de asignación/coalición y {sp.get('SP1', {}).get('verified_fulltext_records', 0)}
con texto completo verificado. Los términos de coding más observados en textos
verificados para coordinación/arquitectura son: {format_terms(fulltext_rows, 'coordination_architecture')}.
Esto identifica familias que deben leerse y compararse; no demuestra que una
dinámica de juego concreta sea nueva ni que un equilibrio sea factible.

### SP2 — ejecución y transporte cooperativo

Las etiquetas iniciales identifican {sp.get('SP2', {}).get('all_queue_records', 0)}
registros con señales físicas de transporte/contacto y {sp.get('SP2', {}).get('verified_fulltext_records', 0)}
con texto completo verificado. En el texto completo aparecen: {format_terms(fulltext_rows, 'physical_layer')}.
La lectura del TFM debe distinguir transporte rígido/prehensil de empuje o
caging, y no transferir garantías entre modelos de contacto distintos.

### SP3 — planificación, tráfico y múltiples coaliciones

Se observan {sp.get('SP3', {}).get('all_queue_records', 0)} señales de planificación,
seguridad o contexto industrial y {sp.get('SP3', {}).get('verified_fulltext_records', 0)}
textos completos verificados. Los términos de ejecución más frecuentes son:
{format_terms(fulltext_rows, 'execution')}.
El acoplamiento entre tráfico de varias coaliciones activas y transporte físico
debe considerarse una hipótesis de integración, no una ausencia de estado del
arte inferida por conteo de palabras.

## Familias de método y validación

Las familias observadas en textos completos incluyen: {format_terms(fulltext_rows, 'method')}.
Los términos experimentales incluyen: {format_terms(fulltext_rows, 'experiments')}.
La presencia de `theorem`, `convergence`, `stability` o `complexity` solo indica
que el vocabulario aparece; la afirmación matemática requiere leer supuestos,
prueba, dominio y conjunto invariante. Del mismo modo, una palabra como
`performance` no autoriza a copiar una mejora numérica sin extraer tabla,
baseline, semillas, intervalo y protocolo.

## Auditoría adversarial de novedad

La auditoría Stage 4 conserva explícitamente prior art candidato y niega una
conclusión final de novedad. La revisión no identifica base suficiente para
afirmar que el TFM sea el primero en combinar SP1-SP3. La integración de un
juego potencial/poblacional white-box, ejecución física de transporte rígido
con reparto de wrench y planificación de tráfico local aparece aquí como
**hipótesis de posicionamiento a contrastar**, no como contribución ya
demostrada.

### Candidatos prioritarios para lectura cercana

""" 
    for index, row in enumerate(prior_art, start=1):
        full += f"\n{index}. {cite(row)} — rol `{clean(row.get('scientific_role'))}`, evidencia `{clean(row.get('evidence_strength'))}`."
    full += """

## Recomendaciones de uso en el TFM

1. Usar las entradas CORE/ENABLING como cola priorizada de lectura cercana y
   registrar en el ledger qué afirmación concreta respalda cada fuente.
2. Comparar SP1 con baselines de coalición/asignación apropiados (MILP,
   generalized assignment, set partitioning, subastas o consenso según el
   caso), no con Hungarian salvo reducción demostrada uno-a-uno.
3. Para SP2 separar explícitamente cinemática/dinámica, contacto, wrench,
   seguridad y comunicación; no presentar equilibrio de Nash como garantía
   mecánica o de colisión.
4. Para SP3 comparar planificación/tráfico con el baseline que corresponda al
   escenario y medir bloqueos, colisiones, makespan, throughput y recuperación.
5. Completar la exportación WoS y una lectura humana de los candidatos
   prioritarios antes de redactar novelty claims o afirmar estado del arte.

## Respuestas explícitas a las preguntas del TFM

1. **Asignación multi-robot:** la literatura ya ofrece familias maduras de
   subastas, consenso, optimización y aprendizaje para asignación; la matriz
   documenta su presencia, pero no compara sus resultados como un benchmark
   homogéneo.
2. **Coaliciones/equipos:** existen trabajos de formación de equipos y
   coaliciones; la pregunta pendiente es su factibilidad simultánea bajo
   capacidades heterogéneas y restricciones físicas.
3. **Tareas multi-robot heterogéneas:** exigen requisitos colectivos,
   cardinalidad/capacidad y compatibilidad de roles; no basta la asignación
   independiente robot-tarea.
4. **Coalición local/distribuida:** aparecen señales de consenso, subastas,
   coordinación distribuida e información local; cada candidato debe
   confirmarse en texto completo para saber si la ejecución sigue siendo local.
5. **Coalición más transporte físico:** el corpus contiene candidatos con ambas
   familias de señales; la combinación exacta no se declara resuelta sin leer
   ecuaciones, contacto y protocolo experimental.
6. **Factibilidad mecánica:** contar robots o capacidad nominal no certifica
   factibilidad mecánica; la matriz separa esos indicios de contacto/wrench y
   no los convierte en certificados.
7. **Geometría, fuerza y wrench:** dichos términos aparecen en textos
   verificados, pero la existencia de la palabra no prueba force closure,
   reparto de wrench ni estabilidad.
8. **Sustitución tras fallo:** la señal de recuperación/reemplazo es reducida
   frente a asignación y coordinación; debe auditarse con lectura cercana y
   pruebas específicas de reconfiguración.
9. **Distribución durante ejecución:** `distributed` en la descripción de
   asignación no demuestra ejecución distribuida; se deben separar mensajes,
   control, navegación y transporte durante la operación.
10. **Radio, pérdida, retardo y topología:** el coding localiza supuestos de
    información y comunicación cuando están escritos; su tratamiento
    cuantitativo aún requiere extracción manual de cada fuente.
11. **Baselines:** usar MILP/set partitioning/generalized assignment o
    subastas/consenso para SP1; leader-follower, virtual structure,
    formación/consenso o reparto centralizado de fuerzas para SP2; y
    A*/Dijkstra, CBS/ECBS, planificación priorizada, ORCA/RVO o CBF-QP para
    SP3 según el escenario.
12. **Partes estándar:** asignación, subastas, consenso, control de formación,
    evitación y planificación son familias establecidas; el TFM debe
    posicionarse sobre interfaces y supuestos concretos.
13. **Adaptaciones:** la adaptación de una familia conocida a AMR
    heterogéneos, carga rígida, información local y fallos debe nombrarse como
    adaptación hasta demostrar qué componente cambia y qué evidencia aporta.
14. **Combinaciones insuficientemente cubiertas:** el mapa identifica señales
    escasas para algunas intersecciones, pero esto es un indicador de cobertura
    y no una prueba de ausencia o de gap universal.
15. **Novedad segura:** es seguro afirmar que la revisión construye una base
    trazable y que la integración SP1-SP3 es una hipótesis de posicionamiento
    que debe contrastarse con prior art.
16. **Claims prohibidos:** no afirmar primero, único, SOTA, optimalidad,
    convergencia, estabilidad, robustez, escalabilidad, seguridad garantizada
    ni ausencia de trabajo previo sin evidencia formal y comparación completa.

## Conclusión acotada

La evidencia reunida es suficiente para estructurar el marco de comparación y
para identificar interfaces de investigación entre coaliciones, transporte
físico y tráfico. No es suficiente para una declaración de novedad ni para
garantías matemáticas o experimentales del método del TFM. El siguiente paso
científico es close reading verificable y luego validación experimental bajo el
protocolo del repositorio.
"""
    (FINAL / "literature_review_full.md").write_text(full, encoding="utf-8")

    compact = f"""# Revisión compacta para integración en el TFM

- Corpus Stage 1C: **{len(corpus)}** candidatos; cola Stage 2: **{len(matrix)}**.
- Texto completo verificado: **{evidence_counts['fulltext_verified']}**; solo resumen: **{evidence_counts['abstract_only']}**; solo metadatos: **{evidence_counts['metadata_only']}**; errores de recuperación: **{evidence_counts['retrieval_error']}**.
- SP1: {sp.get('SP1', {}).get('all_queue_records', 0)} señales de asignación/coalición en cola, {sp.get('SP1', {}).get('verified_fulltext_records', 0)} con texto verificado.
- SP2: {sp.get('SP2', {}).get('all_queue_records', 0)} señales físicas en cola, {sp.get('SP2', {}).get('verified_fulltext_records', 0)} con texto verificado.
- SP3: {sp.get('SP3', {}).get('all_queue_records', 0)} señales de planificación/seguridad/industria en cola, {sp.get('SP3', {}).get('verified_fulltext_records', 0)} con texto verificado.

La revisión soporta una base comparativa y una agenda de lectura, pero no
demuestra novedad, optimalidad, convergencia, estabilidad, robustez ni
escalabilidad. La auditoría adversarial y la ausencia de exportación WoS
obligan a tratar la combinación SP1-SP3 como hipótesis de posicionamiento.
"""
    (FINAL / "literature_review_compact.md").write_text(compact, encoding="utf-8")

    integration = """# Plan de integración de la revisión en el TFM

## Principio

Integrar la revisión como evidencia trazable dentro del capítulo de marco
teórico/estado del arte y como base de los baselines del capítulo de
resultados. No copiar afirmaciones del coding estructural sin lectura cercana,
registro en `references/LITERATURE_LEDGER.md` y mapeo a `docs/04_CLAIMS_EVIDENCE.md`.

## SP1 — coaliciones

- Núcleo de lectura: `final/core_papers.csv`.
- Comparar formalizaciones de capacidades, requisitos de tarea, formación y
  reasignación; separar métodos centralizados de distribuidos.
- Baselines candidatos: MILP/set partitioning, generalized assignment,
  subastas/consenso y formación de coaliciones, elegidos por modelo.
- Evidencia que falta: close reading de payoff, información local, factibilidad,
  dinámica de actualización y garantías reales.

## SP2 — transporte físico

- Núcleo de lectura: `final/core_papers.csv` y `final/enabling_papers.csv` con
  términos de `physical_layer`/`execution`.
- Declarar el modo primario del TFM como transporte rígido/prehensil si se
  mantiene el charter; no mezclarlo con caging/empuje sin restricciones de
  contacto propias.
- Extraer pose, wrench, fuerzas internas, límites de actuador, estabilidad,
  seguridad y reconfiguración. Un equilibrio estratégico no sustituye estas
  pruebas.

## SP3 — tráfico y planificación

- Usar candidatos con señales de planificación, seguridad, warehouse/logistics
  y comunicación local.
- Elegir A*/Dijkstra, CBS/ECBS, planificación priorizada, ORCA/RVO o CBF-QP
  solo cuando el escenario y la información disponible sean comparables.
- Medir bloqueos, colisiones/distancia mínima, makespan, throughput y tiempo de
  recuperación con semillas pareadas.

## Redacción y claims

- Toda cifra debe venir de tablas/figuras derivadas, no de esta prosa escrita a
  mano.
- Etiquetar observaciones del dataset, evidencia bibliográfica y resultados
  propios con niveles distintos.
- Sustituir `first/novel/SOTA` por una formulación prudente hasta cerrar la
  auditoría de prior art y WoS.
"""
    (FINAL / "tfm_integration_plan.md").write_text(integration, encoding="utf-8")

    fulltext_ids = ";".join(row.get("candidate_id", "") for row in fulltext_rows)
    fulltext_dois = ";".join(row.get("doi", "") for row in fulltext_rows if clean(row.get("doi")))
    prior_ids = ";".join(row.get("candidate_id", "") for row in prior_art)
    prior_dois = ";".join(row.get("doi", "") for row in prior_art if clean(row.get("doi")))
    claims = [
        {"claim_id": "C01", "claim_text": f"El derivado Stage 1C contiene {len(corpus)} candidatos y la cola Stage 2 contiene {len(matrix)} registros.", "claim_type": "review_descriptive", "support_status": "supported", "candidate_id": "", "DOI": "", "evidence_location": "data/processed/candidate_corpus_stage2.csv;data/processed/fulltext_evidence_matrix.csv", "source_artifacts": "data/processed/candidate_corpus_stage2.csv;data/processed/fulltext_evidence_matrix.csv", "source_candidate_ids": "", "allowed_use": "metodología de revisión", "notes": "Cifra derivada directamente de artefactos congelados del pipeline; no es una afirmación sobre impacto científico."},
        {"claim_id": "C02", "claim_text": f"Se verificaron {evidence_counts['fulltext_verified']} objetos de texto completo mediante identidad DOI/título.", "claim_type": "acquisition_descriptive", "support_status": "supported", "candidate_id": fulltext_ids, "DOI": fulltext_dois, "evidence_location": "logs/stage2_fulltext_acquisition.csv;reports/stage2_acquisition_qa.md", "source_artifacts": "logs/stage2_fulltext_acquisition.csv;reports/stage2_acquisition_qa.md", "source_candidate_ids": fulltext_ids, "allowed_use": "describir cobertura de evidencia", "notes": "El soporte es operativo y de identidad; no convierte el coding estructural en validación científica de resultados."},
        {"claim_id": "C03", "claim_text": "Las señales de método, teoría, física y experimentación son indicadores de coding estructural, no verificación de resultados.", "claim_type": "evidence_boundary", "support_status": "supported", "candidate_id": "", "DOI": "", "evidence_location": "reports/stage3_fulltext_qa.md;config/stage3_codebook.yaml", "source_artifacts": "reports/stage3_fulltext_qa.md;config/stage3_codebook.yaml", "source_candidate_ids": "", "allowed_use": "limitación metodológica", "notes": "Límite explícito del protocolo de extracción y del primer pase automatizado."},
        {"claim_id": "C04", "claim_text": "La combinación completa SP1-SP3 no puede declararse ausente ni novedosa con el corpus actual.", "claim_type": "novelty_boundary", "support_status": "unclear", "candidate_id": prior_ids, "DOI": prior_dois, "evidence_location": "reports/adversarial_novelty_audit.md;tables/stage4_analysis_summary.json", "source_artifacts": "reports/adversarial_novelty_audit.md;tables/stage4_analysis_summary.json", "source_candidate_ids": prior_ids, "allowed_use": "auditoría de novedad, no claim final", "notes": "Hipótesis de gap retenida: requiere exportación WoS y lectura cercana antes de cualquier conclusión de novedad."},
        {"claim_id": "C05", "claim_text": "El siguiente paso requerido es lectura cercana de prior art, exportación WoS y validación experimental según el protocolo del repositorio.", "claim_type": "research_action", "support_status": "supported", "candidate_id": "", "DOI": "", "evidence_location": "final/tfm_integration_plan.md;reports/stage4_synthesis_qa.md", "source_artifacts": "final/tfm_integration_plan.md;reports/stage4_synthesis_qa.md", "source_candidate_ids": "", "allowed_use": "plan de trabajo", "notes": "Acción derivada de las limitaciones registradas; no es un resultado bibliográfico."},
    ]
    write_csv(FINAL / "claim_source_matrix.csv", claims)
    (FINAL / "review_limitations.md").write_text(f"""# Limitaciones de la revisión

- La cobertura depende de Crossref/OpenAlex, snowballing limitado y rutas OA
  públicas; Web of Science no fue incorporado.
- La cola de 1057 registros produjo 230 textos completos verificados, por lo
  que muchas familias permanecen con evidencia de resumen/metadatos.
- El coding de Stage 3 es un primer pase estructural automatizado. No sustituye
  lectura humana de ecuaciones, tablas, figuras, supuestos y protocolos.
- `abstract_only` y `metadata_only` no respaldan detalles técnicos; `retrieval_error`
  es un estado operativo, no una ausencia científica.
- La heterogeneidad de tareas, robots, contactos, baselines y métricas impide
  un meta-análisis cuantitativo directo.
- No se evaluaron aquí estabilidad, convergencia, optimalidad, seguridad,
  robustez o escalabilidad de los métodos descritos.
- Las figuras son descriptivas y generadas de los datasets; no son resultados
  del algoritmo del TFM.
- Los binarios descargados se mantienen localmente pero fuera de Git por
  licencia/tamaño; su recuperación requiere ejecutar Stage 2 y comprobar hashes.
""", encoding="utf-8")

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE.parent, capture_output=True, text=True, check=False).stdout.strip()
    manifest = {
        "generated_at_utc": utc_now(),
        "git_head_at_generation": head,
        "canonical_thesis_modified": False,
        "stage_inputs": {
            "candidate_corpus_stage2.csv": sha256(CORPUS),
            "fulltext_evidence_matrix.csv": sha256(MATRIX),
            "stage4_analysis_summary.json": sha256(TABLES / "stage4_analysis_summary.json"),
        },
        "commands": [
            "python academic-review/scripts/stage1c.py --resume",
            "python academic-review/scripts/stage2_acquire.py --resume",
            "python academic-review/scripts/stage3_code.py",
            "python academic-review/scripts/stage4_synthesize.py",
            "python academic-review/scripts/stage5_finalize.py",
            "python -m pytest academic-review/tests -q",
        ],
        "outputs": [str(path.relative_to(BASE)) for path in sorted(FINAL.iterdir()) if path.is_file()],
        "raw_fulltext_policy": "local-only; excluded from Git; manifests and SHA-256 values are versioned",
        "wos_status": "pending_external_export",
    }
    (FINAL / "reproducibility_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (FINAL / "reproducibility_manifest.md").write_text(f"""# Manifest de reproducibilidad

- HEAD al generar Stage 5: `{head}`
- Tesis canónica modificada: **no**
- Corpus Stage 2 SHA-256: `{sha256(CORPUS)}`
- Matriz Stage 3 SHA-256: `{sha256(MATRIX)}`
- Resumen Stage 4 SHA-256: `{sha256(TABLES / 'stage4_analysis_summary.json')}`
- WoS: `pending_external_export`

Ejecutar en orden:

```powershell
python academic-review/scripts/stage2_acquire.py --resume
python academic-review/scripts/stage3_code.py
python academic-review/scripts/stage4_synthesize.py
python academic-review/scripts/stage5_finalize.py
python -m pytest academic-review/tests -q
```

Los binarios de texto completo están excluidos de Git por licencias/tamaño;
`logs/stage2_fulltext_acquisition.csv` y los manifests por candidato registran
URL, estado, identidad, tamaño y SHA-256 para regenerarlos legalmente.
""", encoding="utf-8")

    qa = f"""# Stage 5 final package QA

Run UTC: {utc_now()}

- Final files generated: **{len([path for path in FINAL.iterdir() if path.is_file()])}**
- Claim-source rows: **{len(claims)}**
- Core triage rows: **{len(core)}**
- Enabling triage rows: **{len(enabling)}**
- Excluded rows: **{len(excluded)}**
- Canonical thesis modified: **no**
- Final novelty conclusion: **withheld**

The package is integration-ready as a conservative review artifact. It does
not replace close reading, WoS reconciliation, or experimental validation.
"""
    (REPORTS / "stage5_final_package_qa.md").write_text(qa, encoding="utf-8")
    print(qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
