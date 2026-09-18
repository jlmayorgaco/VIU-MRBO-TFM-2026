"""Deriva los datos de la Figura de actividad del corpus académico.

Lee los CSV congelados de `academic-review/literature-review-v3/data/` y escribe
`pre-thesis/shared/generated-macros/lit-corpus-activity.tex`, que la figura
consume. Ninguna cifra de esa figura se escribe a mano en el `.tex`: si el corpus
cambia, se regenera y la figura se mueve sola.

Paneles cubiertos:
  (a) volumen anual, composición fraccional por tema y señal terminológica de
      «distributed/decentralized» como porcentaje del año;
  (b) cuota temática por periodo;
  (c) cambio de cuota entre el periodo temprano y 2022-2026;
  (d) diversidad temática móvil H* normalizada, ventana retrospectiva de 3 años;
  (e) primer año con señal por familia de método;
  (f) publicaciones recurrentes.

Uso:
    python pre-thesis/scripts/build_review_figure_data.py [--check]
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "academic-review" / "literature-review-v3" / "data"
OUT = ROOT / "pre-thesis" / "shared" / "generated-macros" / "lit-corpus-activity.tex"
OUT_BIB = ROOT / "pre-thesis" / "shared" / "generated-macros" / "lit-bibliometric.tex"

# Umbral de coautoría fuerte: mismo criterio que usa "núcleos recurrentes" en
# la literatura de bibliometría descriptiva (Newman, 2004): un par cuenta como
# núcleo cuando coincide en tres o más documentos del corpus.
COAUTHOR_THRESHOLD = 3

# Orden y rótulo corto de las cinco categorías temáticas del corpus.
THEMES = [
    ("SP1_coalition_allocation", "Coalición / MRTA"),
    ("SP2_physical_transport", "Transporte / control"),
    ("SP3_planning_traffic", "Planificación / rutas"),
    ("TRANSVERSAL_resilience_communication", "Recuperación / resiliencia"),
    ("CONTEXT_other", "Contexto / otros"),
]
PERIODS = ["<=2010", "2011-2016", "2017-2021", "2022-2026"]
WINDOW = 3  # ventana retrospectiva de la diversidad móvil


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def signals(row: dict[str, str], field: str) -> list[str]:
    return [s.strip() for s in row[field].split(";") if s.strip()]


def shannon(counts: list[float]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = -sum((c / total) * math.log(c / total) for c in counts if c > 0)
    return h / math.log(len(THEMES))


def build() -> str:
    corpus = read("analytic_corpus_v3.csv")
    dated = [r for r in corpus if r["year"].strip().isdigit()]
    years = sorted({int(r["year"]) for r in dated})
    lo, hi = years[0], years[-1]

    # --- (a) volumen, composición fraccional y señal terminológica -----------
    total_by_year: Counter[int] = Counter()
    theme_by_year: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    distributed_by_year: Counter[int] = Counter()
    for row in dated:
        y = int(row["year"])
        total_by_year[y] += 1
        ts = [t for t in signals(row, "theme_signals_title_abstract") if t in dict(THEMES)]
        if ts:
            for t in ts:
                theme_by_year[y][t] += 1.0 / len(ts)
        if "distributed_decentralized" in signals(row, "architecture_signals_title_abstract"):
            distributed_by_year[y] += 1

    lines: list[str] = [
        "% Generado por pre-thesis/scripts/build_review_figure_data.py",
        "% Fuente: academic-review/literature-review-v3/data/*.csv (corpus V3 congelado).",
        "% No editar a mano: regenerar con el script.",
        f"\\def\\LitYearFirst{{{lo}}}",
        f"\\def\\LitYearLast{{{hi}}}",
        f"\\def\\LitDatedDocs{{{len(dated)}}}",
        f"\\def\\LitTotalDocs{{{len(corpus)}}}",
        f"\\def\\LitMaxYearCount{{{max(total_by_year.values())}}}",
    ]

    coords = " ".join(f"({y},{total_by_year.get(y, 0)})" for y in range(lo, hi + 1))
    lines.append(f"\\def\\LitYearTotals{{{coords}}}")

    for key, _ in THEMES:
        pts = " ".join(
            f"({y},{theme_by_year.get(y, {}).get(key, 0.0):.3f})" for y in range(lo, hi + 1)
        )
        lines.append(f"\\def\\LitYearTheme{sanitise(key)}{{{pts}}}")

    pts = " ".join(
        f"({y},{100.0 * distributed_by_year.get(y, 0) / total_by_year[y]:.1f})"
        if total_by_year.get(y)
        else f"({y},0.0)"
        for y in range(lo, hi + 1)
    )
    lines.append(f"\\def\\LitYearDistributedPct{{{pts}}}")

    # --- (b) cuota temática por periodo --------------------------------------
    period_rows = read("theme_period_v3.csv")
    share = {(r["category"], r["period"]): float(r["period_share"]) for r in period_rows}
    for key, _ in THEMES:
        vals = " ".join(f"{100.0 * share.get((key, p), 0.0):.1f}" for p in PERIODS)
        lines.append(f"\\def\\LitPeriodShare{sanitise(key)}{{{vals}}}")

    # --- (c) cambio de cuota entre el primer periodo y el último -------------
    deltas = []
    for key, label in THEMES:
        d = 100.0 * (share.get((key, PERIODS[-1]), 0.0) - share.get((key, PERIODS[0]), 0.0))
        deltas.append((label, d))
    lines.append(
        "\\def\\LitShareDelta{"
        + ",".join(f"{label}/{d:+.1f}" for label, d in deltas)
        + "}"
    )

    # --- (d) diversidad temática móvil ---------------------------------------
    div = []
    for y in range(lo, hi + 1):
        window = [r for r in dated if y - WINDOW + 1 <= int(r["year"]) <= y]
        counts = [0.0] * len(THEMES)
        for row in window:
            ts = [t for t in signals(row, "theme_signals_title_abstract") if t in dict(THEMES)]
            for t in ts:
                counts[[k for k, _ in THEMES].index(t)] += 1.0 / len(ts)
        div.append(f"({y},{shannon(counts):.3f})")
    lines.append(f"\\def\\LitDiversity{{{' '.join(div)}}}")
    lines.append(f"\\def\\LitDiversityWindow{{{WINDOW}}}")

    # --- (e) primera señal por familia de método -----------------------------
    lifecycle = read("method_lifecycle_v3.csv")
    firsts = sorted(((int(r["first_year"]), r["method"]) for r in lifecycle), reverse=True)
    lines.append(
        "\\def\\LitMethodFirstYear{"
        + ",".join(f"{pretty(m)}/{y}" for y, m in firsts)
        + "}"
    )

    # --- (f) venues recurrentes ----------------------------------------------
    venues = read("top_venues_v3.csv")[:7]
    lines.append(
        "\\def\\LitTopVenues{"
        + ",".join(f"{shorten(v['venue'])}/{v['paper_count']}" for v in venues)
        + "}"
    )
    lines.append(f"\\def\\LitTopVenueMax{{{venues[0]['paper_count']}}}")

    return "\n".join(lines) + "\n"


def sanitise(key: str) -> str:
    """Nombre de macro LaTeX válido: solo letras."""
    return "".join(part.capitalize() for part in key.replace("_", " ").split())


def pretty(method: str) -> str:
    table = {
        "consensus_distributed": "Consenso",
        "auction_market": "Subasta / mercado",
        "learning_based": "Aprendizaje",
        "evolutionary_metaheuristic": "Metaheurística",
        "formation_control": "Formación",
        "behavior_swarm": "Enjambre",
        "game_theory": "Teoría de juegos",
        "reactive_safety_cbf": "CBF / seguridad",
        "exact_optimization": "Optimización exacta",
    }
    return table.get(method, method.replace("_", " "))


def shorten(venue: str) -> str:
    table = {
        "Journal of Intelligent & Robotic Systems": "JINT",
        "Lecture Notes in Computer Science": "LNCS",
        "Frontiers in Robotics and AI": "Frontiers RAI",
    }
    return table.get(venue, venue)


def build_bibliometric() -> str:
    """Datos reales de coautoría y coocurrencia de métodos.

    No reproduce los identificadores A1-A11 del panel (a) de la Figura 8
    original: esos provienen de una ejecución de Louvain con semilla propia
    que no está guardada en ningún artefacto del repositorio. En su lugar se
    calculan aquí, de forma reproducible, las componentes conexas del grafo de
    coautoría fuerte (par con >=3 documentos compartidos) y la comunidad de
    Louvain sobre el grafo de coocurrencia de métodos, que sí tiene datos.
    """
    pairs = read("top_coauthor_pairs_v3.csv")
    g = nx.Graph()
    for r in pairs:
        w = int(r["paper_count"])
        if w >= COAUTHOR_THRESHOLD:
            g.add_edge(r["author_left"], r["author_right"], weight=w)

    components = sorted(nx.connected_components(g), key=len, reverse=True)
    lines = [
        "% Generado por pre-thesis/scripts/build_review_figure_data.py",
        "% Fuente: academic-review/literature-review-v3/data/top_coauthor_pairs_v3.csv",
        "% y method_cooccurrence_v3.csv (corpus V3 congelado). No editar a mano.",
        f"\\def\\LitCoauthorThreshold{{{COAUTHOR_THRESHOLD}}}",
        f"\\def\\LitCoauthorPairsTotal{{{len(pairs)}}}",
        f"\\def\\LitCoauthorStrongPairs{{{g.number_of_edges()}}}",
        f"\\def\\LitCoauthorClusters{{{len(components)}}}",
    ]
    comp_spec = []
    for comp in components:
        sub = g.subgraph(comp)
        edges = ";".join(f"{a}|{b}|{sub[a][b]['weight']}" for a, b in sub.edges())
        comp_spec.append(f"{len(comp)}~{edges}")
    lines.append("\\def\\LitCoauthorComponents{" + ",".join(comp_spec) + "}")

    cooc = read("method_cooccurrence_v3.csv")
    mg = nx.Graph()
    for r in cooc:
        mg.add_edge(r["left"], r["right"], weight=int(r["paper_count"]))
    communities = nx.community.greedy_modularity_communities(mg, weight="weight")
    modularity = nx.community.modularity(mg, communities, weight="weight")
    lines.append(f"\\def\\LitMethodModularity{{{modularity:.3f}}}")
    lines.append(f"\\def\\LitMethodCommunities{{{len(communities)}}}")
    comm_spec = []
    for comm in communities:
        comm_spec.append(",".join(sorted(pretty(m) for m in comm)))
    lines.append("\\def\\LitMethodCommunityLabels{" + "~".join(comm_spec) + "}")
    edge_spec = ";".join(
        f"{pretty(r['left'])}|{pretty(r['right'])}|{r['paper_count']}" for r in cooc
    )
    lines.append("\\def\\LitMethodEdges{" + edge_spec + "}")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="falla si el archivo está desactualizado")
    args = ap.parse_args()

    payload = build()
    payload_bib = build_bibliometric()

    if args.check:
        ok = True
        for path, content in ((OUT, payload), (OUT_BIB, payload_bib)):
            current = path.read_text(encoding="utf-8") if path.is_file() else ""
            if current != content:
                print(f"Desactualizado: {path}")
                ok = False
        if ok:
            print("Al día.")
        return 0 if ok else 1

    for path, content in ((OUT, payload), (OUT_BIB, payload_bib)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Escrito: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
