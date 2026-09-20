"""Build reproducible figures and LaTeX metrics for the four-page V3 review.

All plotted values are read from the frozen V3 analytical derivatives.  The
script intentionally distinguishes descriptive title/abstract signals from
close-read evidence; it does not infer implementation or field prevalence.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
DATA = V3 / "data"
OUT = V3 / "compact-4p"
FIGURES = OUT / "figures"

ORANGE = "#E36A2E"
BLUE = "#2D6CC0"
GREEN = "#2E9B5F"
PURPLE = "#7B4DBA"
YELLOW = "#FCD757"
INK = "#0C0C0C"
MUTED = "#5F6670"
GRID = "#D9DEE5"
SOFT = "#F5F7FA"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def index_counts(name: str) -> dict[str, int]:
    return {row["category"]: int(row["paper_count"]) for row in read_csv(name)}


def tex_number(value: int) -> str:
    return f"{value:,}".replace(",", r"\,")


def setup_style() -> None:
    font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for filename in (
        "NotoSans-Regular.ttf",
        "NotoSans-Bold.ttf",
        "NotoSans-Italic.ttf",
        "NotoSans-BoldItalic.ttf",
    ):
        font_path = font_dir / filename
        if not font_path.exists():
            raise RuntimeError(f"Required figure font not found: {font_path}")
        font_manager.fontManager.addfont(str(font_path))
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans", "Arial", "DejaVu Sans"],
            "font.size": 8.3,
            "axes.titlesize": 9.5,
            "axes.titleweight": "bold",
            "axes.labelcolor": INK,
            "text.color": INK,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
        }
    )


def collect_metrics() -> dict[str, int]:
    discovery = read_csv("discovery_registry_v3.csv")
    corpus = read_csv("analytic_corpus_v3.csv")
    audit = read_csv("fulltext_adequacy_audit_v3.csv")
    tracker = read_csv("close_reading_tracker_v3.csv")
    adequate = sum(row.get("close_reading_eligibility") == "eligible" for row in audit)
    completed_cards = sum(
        row.get("close_reading_status") == "completed_passage_localized_card"
        for row in tracker
    )
    if completed_cards == 0:
        completed_cards = len(
            [path for path in (V3 / "close-read").glob("*.md") if path.name != "README.md"]
        )

    themes = index_counts("theme_counts_v3.csv")
    methods = index_counts("method_counts_v3.csv")
    validation = index_counts("validation_counts_v3.csv")
    architecture = index_counts("architecture_counts_v3.csv")
    applications = index_counts("application_counts_v3.csv")
    combination_rows = read_csv("theme_combinations_v3.csv")
    combinations = {
        row["theme_combination"]: int(row["paper_count"])
        for row in combination_rows
    }
    sp12 = combinations.get(
        "SP1_coalition_allocation;SP2_physical_transport;TRANSVERSAL_resilience_communication",
        0,
    )
    sp13 = combinations.get("SP1_coalition_allocation;SP3_planning_traffic", 0) + combinations.get(
        "SP1_coalition_allocation;SP3_planning_traffic;TRANSVERSAL_resilience_communication",
        0,
    )
    sp23 = combinations.get("SP2_physical_transport;SP3_planning_traffic", 0) + combinations.get(
        "SP2_physical_transport;SP3_planning_traffic;TRANSVERSAL_resilience_communication",
        0,
    )
    triple = sum(
        value
        for key, value in combinations.items()
        if all(prefix in key for prefix in ("SP1_", "SP2_", "SP3_"))
    )

    metrics = {
        "discovery": len(discovery),
        "corpus": len(corpus),
        "adequate": adequate,
        "close_read": completed_cards,
        "sp1": themes["SP1_coalition_allocation"],
        "sp2": themes["SP2_physical_transport"],
        "sp3": themes["SP3_planning_traffic"],
        "sp12": sp12,
        "sp13": sp13,
        "sp23": sp23,
        "sp123": triple,
        "transversal": themes["TRANSVERSAL_resilience_communication"],
        "context": themes["CONTEXT_other"],
        "distributed": architecture["distributed_decentralized"],
        "centralized": architecture["centralized"],
        "simulation": validation["simulation"],
        "industrial": validation["industrial_case"],
        "physical": validation["physical_experiment"],
        "formal": validation["formal_analysis"],
        "warehouse": applications["warehouse_logistics"],
        "transport_app": applications["cooperative_transport_manipulation"],
        "auction": methods["auction_market"],
        "game": methods["game_theoretic"],
        "learning": methods["learning_based"],
        "consensus": methods["consensus_distributed"],
    }
    expected = {
        "discovery": 3014,
        "corpus": 244,
        "adequate": 168,
        "close_read": 20,
        "sp1": 115,
        "sp2": 15,
        "sp3": 20,
        "sp12": 2,
        "sp13": 10,
        "sp23": 0,
        "sp123": 0,
        "simulation": 99,
        "physical": 12,
        "formal": 7,
    }
    for key, value in expected.items():
        if metrics[key] != value:
            raise RuntimeError(f"V3 invariant changed: {key}={metrics[key]}, expected {value}")
    return metrics


def write_metrics(metrics: dict[str, int]) -> None:
    names = {
        "discovery": "NDiscovery",
        "corpus": "NCorpus",
        "adequate": "NAdequate",
        "close_read": "NCloseRead",
        "sp1": "NSpOne",
        "sp2": "NSpTwo",
        "sp3": "NSpThree",
        "sp12": "NSpOneTwo",
        "sp13": "NSpOneThree",
        "sp23": "NSpTwoThree",
        "sp123": "NSpAll",
        "transversal": "NTransversal",
        "context": "NContext",
        "distributed": "NDistributed",
        "centralized": "NCentralized",
        "simulation": "NSimulation",
        "industrial": "NIndustrial",
        "physical": "NPhysical",
        "formal": "NFormal",
        "warehouse": "NWarehouse",
        "transport_app": "NTransportApp",
        "auction": "NAuction",
        "game": "NGame",
        "learning": "NLearning",
        "consensus": "NConsensus",
    }
    lines = ["% Generated by academic-review/scripts/build_v3_compact_review.py"]
    lines.extend(f"\\newcommand{{\\{names[key]}}}{{{tex_number(value)}}}" for key, value in metrics.items())
    (OUT / "compact_metrics.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def corpus_flow(metrics: dict[str, int]) -> None:
    labels = [
        ("Descubrimiento", metrics["discovery"], "IDs deduplicados"),
        ("Corpus analítico", metrics["corpus"], "objetos adquiridos"),
        ("Texto adecuado", metrics["adequate"], "145 PDF + 23 HTML"),
        ("Lectura cercana", metrics["close_read"], "fichas con localizador"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 1.55))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 28)
    ax.axis("off")
    xs = [2, 27, 52, 77]
    colors = [BLUE, ORANGE, GREEN, PURPLE]
    for i, ((title, number, note), x, color) in enumerate(zip(labels, xs, colors)):
        ax.add_patch(
            plt.Rectangle((x, 8), 20.5, 14, facecolor=SOFT, edgecolor=color, linewidth=1.4)
        )
        ax.text(x + 10.25, 18.6, title, ha="center", va="center", weight="bold", color=color, fontsize=9)
        ax.text(x + 10.25, 14.0, f"{number:,}".replace(",", "\u202f"), ha="center", va="center", weight="bold", fontsize=17)
        ax.text(x + 10.25, 10.1, note, ha="center", va="center", color=MUTED, fontsize=7.2)
        if i < len(xs) - 1:
            ax.annotate("", xy=(xs[i + 1] - 1.0, 15), xytext=(x + 21.4, 15), arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.0})
    ax.text(2, 3.5, "Cobertura: WoS reconciliado parcialmente (154 registros; 255 faltantes en F01/F02) · descubrimiento abierto: 898 identidades únicas · arXiv: 10 registros en el corpus.", fontsize=7.0, color=MUTED)
    ax.text(2, 0.4, "Los niveles describen adquisición y profundidad de verificación; no son un diagrama PRISMA de exclusiones.", fontsize=6.8, color=MUTED, style="italic")
    fig.savefig(FIGURES / "fig01_corpus_flow.pdf", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def method_evolution() -> None:
    rows = read_csv("method_period_v3.csv")
    periods = ["<=2010", "2011-2016", "2017-2021", "2022-2026"]
    order = [
        "consensus_distributed",
        "auction_market",
        "learning_based",
        "evolutionary_metaheuristic",
        "formation_control",
        "behavior_swarm",
        "game_theoretic",
        "safety_reactive",
        "exact_optimization",
    ]
    labels = [
        "Consenso/distribución",
        "Subasta/mercado",
        "Aprendizaje",
        "Metaheurística evolutiva",
        "Control de formación",
        "Comportamiento/enjambre",
        "Teoría de juegos",
        "Seguridad reactiva/CBF",
        "Optimización exacta",
    ]
    values = {(r["category"], r["period"]): float(r["period_share"]) * 100 for r in rows}
    matrix = np.array([[values[(method, period)] for period in periods] for method in order])
    delta = matrix[:, -1] - matrix[:, 0]
    cmap = LinearSegmentedColormap.from_list("method", ["#FFFFFF", "#DCE8F8", BLUE])
    fig = plt.figure(figsize=(7.2, 3.1))
    gs = fig.add_gridspec(1, 2, width_ratios=[4.4, 1.25], wspace=0.27)
    ax = fig.add_subplot(gs[0, 0])
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=32, aspect="auto")
    ax.set_xticks(range(4), ["≤2010\n(n=35)", "2011–16\n(n=40)", "2017–21\n(n=79)", "2022–26\n(n=89)"])
    ax.set_yticks(range(len(labels)), labels)
    ax.set_title("(a) Cuota de documentos del periodo", loc="left", pad=7, fontsize=9.0)
    ax.tick_params(axis="both", length=0)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            color = "white" if matrix[i, j] >= 19 else INK
            ax.text(j, i, f"{matrix[i, j]:.1f}%", ha="center", va="center", fontsize=7.4, color=color, weight="bold" if matrix[i, j] >= 13 else "normal")
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax2 = fig.add_subplot(gs[0, 1])
    colors = [GREEN if value > 0.2 else ORANGE if value < -0.2 else MUTED for value in delta]
    ax2.barh(range(len(labels)), delta, color=colors, height=0.58)
    ax2.axvline(0, color=INK, linewidth=0.7)
    ax2.set_ylim(len(labels) - 0.5, -0.5)
    ax2.set_yticks([])
    ax2.set_title("(b) Δ temprano→reciente\n(puntos porcentuales)", loc="left", pad=7, fontsize=7.8)
    for i, value in enumerate(delta):
        ax2.text(value + (0.45 if value >= 0 else -0.45), i, f"{value:+.1f}", va="center", ha="left" if value >= 0 else "right", fontsize=7.0)
    ax2.set_xlim(-13, 15)
    ax2.grid(axis="x", color=GRID, linewidth=0.5)
    ax2.tick_params(axis="x", labelsize=6.8, length=0)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    fig.text(0.012, -0.012, "Señales nuevas en 2022–26: MPC 2.2%, fuerza/impedancia 2.2% y MAPF/búsqueda 2.2%. Clasificación multietiqueta de título/resumen; 2026 es un año incompleto.", fontsize=6.8, color=MUTED)
    fig.savefig(FIGURES / "fig02_method_evolution.pdf", bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)


def interface_and_evidence(metrics: dict[str, int]) -> None:
    combination_rows = read_csv("theme_combinations_v3.csv")
    combos = {row["theme_combination"]: int(row["paper_count"]) for row in combination_rows}
    sp12 = combos.get("SP1_coalition_allocation;SP2_physical_transport;TRANSVERSAL_resilience_communication", 0)
    sp13 = combos.get("SP1_coalition_allocation;SP3_planning_traffic", 0) + combos.get("SP1_coalition_allocation;SP3_planning_traffic;TRANSVERSAL_resilience_communication", 0)
    sp23 = combos.get("SP2_physical_transport;SP3_planning_traffic", 0) + combos.get("SP2_physical_transport;SP3_planning_traffic;TRANSVERSAL_resilience_communication", 0)
    triple = sum(v for k, v in combos.items() if all(x in k for x in ("SP1_", "SP2_", "SP3_")))
    assert (sp12, sp13, sp23, triple) == (2, 10, 0, 0)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.55), gridspec_kw={"width_ratios": [1.35, 1]})
    labels = ["SP1: coalición/asignación", "SP2: transporte físico", "SP3: planificación/tráfico", "SP1 ∩ SP2", "SP1 ∩ SP3", "SP2 ∩ SP3", "SP1 ∩ SP2 ∩ SP3"]
    values = [metrics["sp1"], metrics["sp2"], metrics["sp3"], sp12, sp13, sp23, triple]
    colors = [BLUE, ORANGE, GREEN, "#7EA5D8", "#67B485", "#C8CDD3", "#C8CDD3"]
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors, height=0.58)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 126)
    ax.set_title("Cobertura temática y de interfaces", loc="left", pad=7)
    ax.grid(axis="x", color=GRID, linewidth=0.5)
    ax.tick_params(axis="x", labelsize=6.8, length=0)
    ax.tick_params(axis="y", labelsize=7.3, length=0)
    for yi, value in zip(y, values):
        ax.text(value + 2.0, yi, str(value), va="center", weight="bold", fontsize=8.0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ev_labels = ["Simulación", "Señal de caso industrial", "Experimento físico", "Análisis formal"]
    ev_values = [metrics["simulation"], metrics["industrial"], metrics["physical"], metrics["formal"]]
    ev_colors = [PURPLE, YELLOW, ORANGE, GREEN]
    y2 = np.arange(len(ev_labels))
    ax2.barh(y2, ev_values, color=ev_colors, height=0.58)
    ax2.set_yticks(y2, ev_labels)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 108)
    ax2.set_title("Madurez de validación observada", loc="left", pad=7)
    ax2.grid(axis="x", color=GRID, linewidth=0.5)
    ax2.tick_params(axis="x", labelsize=6.8, length=0)
    ax2.tick_params(axis="y", labelsize=7.3, length=0)
    for yi, value in zip(y2, ev_values):
        ax2.text(value + 1.7, yi, f"{value} ({value / metrics['corpus'] * 100:.1f}%)", va="center", weight="bold", fontsize=7.6)
    for spine in ax2.spines.values():
        spine.set_visible(False)
    fig.text(0.012, -0.018, "Conteos multietiqueta sobre n=244. ‘Caso industrial’ puede describir un escenario simulado; no equivale a despliegue real.", fontsize=6.8, color=MUTED)
    fig.savefig(FIGURES / "fig03_interfaces_evidence.pdf", bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)


def write_manifest(metrics: dict[str, int]) -> None:
    manifest = {
        "script": "academic-review/scripts/build_v3_compact_review.py",
        "inputs": [
            "analytic_corpus_v3.csv",
            "discovery_registry_v3.csv",
            "fulltext_adequacy_audit_v3.csv",
            "close_reading_tracker_v3.csv",
            "theme_counts_v3.csv",
            "theme_combinations_v3.csv",
            "method_counts_v3.csv",
            "method_period_v3.csv",
            "architecture_counts_v3.csv",
            "validation_counts_v3.csv",
            "application_counts_v3.csv",
        ],
        "outputs": [
            "compact_metrics.tex",
            "figures/fig01_corpus_flow.pdf",
            "figures/fig02_method_evolution.pdf",
            "figures/fig03_interfaces_evidence.pdf",
        ],
        "metrics": metrics,
        "interpretation_rule": "Counts are descriptive title/abstract signals unless explicitly identified as close-read evidence.",
    }
    (OUT / "build_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    setup_style()
    metrics = collect_metrics()
    write_metrics(metrics)
    corpus_flow(metrics)
    method_evolution()
    interface_and_evidence(metrics)
    write_manifest(metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
