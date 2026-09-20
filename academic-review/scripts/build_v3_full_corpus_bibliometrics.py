"""Build the full-corpus temporal dashboard and bibliometric map.

The input is the frozen 244-record V3 analytical corpus.  All thematic
quantities are descriptive title/abstract signals.  Multi-label papers are
fractionally counted in the seven-family dashboard so every paper contributes
exactly one unit to annual and period totals.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
CORPUS_PATH = V3 / "data" / "analytic_corpus_v3.csv"
OUT = V3 / "compact-7p-full"
DATA_OUT = OUT / "data"
FIGURES = OUT / "figures"

ORANGE = "#E95824"
BLUE = "#2D6CC0"
TRANSPORT = "#E76F2E"
YELLOW = "#F3C43C"
PEACH = "#F29A76"
GREEN = "#55A868"
PURPLE = "#7B4DBA"
GRAY = "#8A919B"
TEAL = "#278A8A"
INK = "#111936"
MUTED = "#59627A"
GRID = "#CBD2DF"
PANEL = "#F7F8FA"

FAMILY_ORDER = [
    "Coalition / MRTA",
    "Transport / control",
    "Planning / routing",
    "Feasibility / contact",
    "Recovery / replacement",
    "Learning / RL",
    "Foundational / survey",
]
FAMILY_COLORS = {
    "Coalition / MRTA": BLUE,
    "Transport / control": TRANSPORT,
    "Planning / routing": YELLOW,
    "Feasibility / contact": PEACH,
    "Recovery / replacement": GREEN,
    "Learning / RL": PURPLE,
    "Foundational / survey": GRAY,
}
PERIOD_ORDER = ["<=2010", "2011-2016", "2017-2021", "2022-2026"]
PERIOD_LABELS = ["≤2010", "2011–2016", "2017–2021", "2022–2026"]

FEASIBILITY_RE = re.compile(
    r"\b(?:feasib\w*|contact\w*|wrench\w*|caging|grasp\w*|friction\w*|"
    r"force closure|actuator\w*|payload capacit\w*)\b",
    flags=re.I,
)
RECOVERY_RE = re.compile(
    r"\b(?:fault\w*|failure\w*|recover\w*|resilien\w*|replacement\w*|"
    r"reconfigur\w*|reallocat\w*|repair\w*|breakdown\w*)\b",
    flags=re.I,
)

TOPIC_LABELS = {
    "SP1_coalition_allocation": "SP1 · coalición",
    "SP2_physical_transport": "SP2 · transporte",
    "SP3_planning_traffic": "SP3 · tráfico",
    "TRANSVERSAL_resilience_communication": "red / resiliencia",
    "auction_market": "mercado",
    "exact_optimization": "exacta",
    "game_theoretic": "teoría de juegos",
    "evolutionary_metaheuristic": "metaheurística",
    "learning_based": "aprendizaje",
    "behavior_swarm": "enjambre",
    "consensus_distributed": "consenso",
    "model_predictive_control": "MPC",
    "formation_control": "formación",
    "force_impedance_control": "fuerza / imp.",
    "safety_reactive": "seguridad",
    "graph_search_mapf": "MAPF",
    "warehouse_logistics": "almacén",
    "cooperative_transport_manipulation": "COT físico",
    "aerial_uav": "UAV",
    "underwater_marine": "submarino",
    "search_rescue_exploration": "rescate",
    "construction_agriculture": "agro",
}


def configure_plotting() -> None:
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
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Noto Sans", "Arial", "DejaVu Sans"],
            "axes.titlesize": 8.4,
            "axes.titleweight": "bold",
            "axes.labelsize": 6.8,
            "xtick.labelsize": 6.1,
            "ytick.labelsize": 6.1,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "xtick.color": INK,
            "ytick.color": INK,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signals(row: dict[str, str], field: str) -> set[str]:
    return {item for item in row.get(field, "").split(";") if item}


def parse_authors(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def family_memberships(row: dict[str, str]) -> tuple[str, ...]:
    """Map a paper to transparent dashboard families without forcing primacy."""
    themes = signals(row, "theme_signals_title_abstract")
    methods = signals(row, "method_focus_title_abstract")
    text = f"{row.get('title', '')} {row.get('abstract_extracted', '')}".lower()
    memberships: list[str] = []
    if "SP1_coalition_allocation" in themes:
        memberships.append("Coalition / MRTA")
    if "SP2_physical_transport" in themes or methods & {
        "formation_control",
        "force_impedance_control",
        "model_predictive_control",
    }:
        memberships.append("Transport / control")
    if "SP3_planning_traffic" in themes or "graph_search_mapf" in methods:
        memberships.append("Planning / routing")
    if FEASIBILITY_RE.search(text):
        memberships.append("Feasibility / contact")
    if RECOVERY_RE.search(text):
        memberships.append("Recovery / replacement")
    if "learning_based" in methods:
        memberships.append("Learning / RL")
    if (
        row.get("scientific_role_structural") == "SURVEY"
        or "CONTEXT_other" in themes
    ):
        memberships.append("Foundational / survey")
    return tuple(dict.fromkeys(memberships or ["Foundational / survey"]))


def family_weights(row: dict[str, str]) -> dict[str, float]:
    memberships = family_memberships(row)
    weight = 1.0 / len(memberships)
    return {family: weight for family in memberships}


def display_year_bin(row: dict[str, str]) -> str | None:
    year = row.get("year", "")
    if not year.isdigit():
        return None
    return "≤1999" if int(year) <= 1999 else year


def build_temporal_tables(rows: list[dict[str, str]]) -> dict[str, Any]:
    year_bins = ["≤1999"] + [str(year) for year in range(2000, 2027)]
    annual_total = Counter(display_year_bin(row) for row in rows if display_year_bin(row))
    annual_family: defaultdict[str, Counter[str]] = defaultdict(Counter)
    annual_distributed: Counter[str] = Counter()
    annual_architecture_known: Counter[str] = Counter()
    for row in rows:
        year_bin = display_year_bin(row)
        if year_bin is None:
            continue
        for family, weight in family_weights(row).items():
            annual_family[year_bin][family] += weight
        architecture = signals(row, "architecture_signals_title_abstract")
        if "distributed_decentralized" in architecture:
            annual_distributed[year_bin] += 1
        if architecture:
            annual_architecture_known[year_bin] += 1

    annual_rows: list[dict[str, Any]] = []
    for year_bin in year_bins:
        total = annual_total[year_bin]
        record: dict[str, Any] = {
            "year_bin": year_bin,
            "paper_count": total,
            "distributed_signal_count": annual_distributed[year_bin],
            "distributed_signal_share": (
                f"{annual_distributed[year_bin] / total:.6f}" if total else ""
            ),
            "architecture_signal_count": annual_architecture_known[year_bin],
        }
        record.update(
            {family: f"{annual_family[year_bin][family]:.6f}" for family in FAMILY_ORDER}
        )
        annual_rows.append(record)

    period_denominators = Counter(
        row["period"] for row in rows if row.get("period") in PERIOD_ORDER
    )
    period_family: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        period = row.get("period", "")
        if period not in PERIOD_ORDER:
            continue
        for family, weight in family_weights(row).items():
            period_family[period][family] += weight

    period_rows: list[dict[str, Any]] = []
    for period in PERIOD_ORDER:
        denominator = period_denominators[period]
        for family in FAMILY_ORDER:
            weighted_count = period_family[period][family]
            period_rows.append(
                {
                    "period": period,
                    "family": family,
                    "weighted_paper_count": f"{weighted_count:.6f}",
                    "period_denominator": denominator,
                    "period_share": f"{weighted_count / denominator:.6f}",
                }
            )

    first_period = period_family[PERIOD_ORDER[0]]
    last_period = period_family[PERIOD_ORDER[-1]]
    first_denominator = period_denominators[PERIOD_ORDER[0]]
    last_denominator = period_denominators[PERIOD_ORDER[-1]]
    change_rows = []
    for family in FAMILY_ORDER:
        initial = first_period[family] / first_denominator
        recent = last_period[family] / last_denominator
        change_rows.append(
            {
                "family": family,
                "initial_period": PERIOD_ORDER[0],
                "recent_period": PERIOD_ORDER[-1],
                "initial_share": f"{initial:.6f}",
                "recent_share": f"{recent:.6f}",
                "change_percentage_points": f"{100 * (recent - initial):.6f}",
            }
        )

    diversity_rows = []
    for year in range(1979, 2027):
        window = [
            row
            for row in rows
            if row.get("year", "").isdigit()
            and year - 2 <= int(row["year"]) <= year
        ]
        counts = Counter()
        for row in window:
            counts.update(family_weights(row))
        total = sum(counts.values())
        if total:
            probabilities = np.array([counts[family] / total for family in FAMILY_ORDER])
            positive = probabilities[probabilities > 0]
            diversity = float(-(positive * np.log(positive)).sum() / math.log(len(FAMILY_ORDER)))
        else:
            diversity = float("nan")
        diversity_rows.append(
            {
                "year": year,
                "window_start": year - 2,
                "window_end": year,
                "documents_in_window": len(window),
                "normalized_shannon_diversity": (
                    f"{diversity:.6f}" if math.isfinite(diversity) else ""
                ),
            }
        )

    emergence_rows = []
    for family in FAMILY_ORDER:
        years = [
            int(row["year"])
            for row in rows
            if row.get("year", "").isdigit() and family in family_memberships(row)
        ]
        emergence_rows.append(
            {
                "family": family,
                "first_observed_year": min(years) if years else "",
                "last_observed_year": max(years) if years else "",
                "raw_signal_documents": sum(
                    family in family_memberships(row) for row in rows
                ),
                "interpretation_limit": "First signal in the acquired corpus; not field-wide historical emergence.",
            }
        )

    write_csv(DATA_OUT / "figure4_annual_family_v3.csv", annual_rows, list(annual_rows[0]))
    write_csv(
        DATA_OUT / "figure4_period_share_v3.csv",
        period_rows,
        ["period", "family", "weighted_paper_count", "period_denominator", "period_share"],
    )
    write_csv(
        DATA_OUT / "figure4_quota_change_v3.csv",
        change_rows,
        [
            "family",
            "initial_period",
            "recent_period",
            "initial_share",
            "recent_share",
            "change_percentage_points",
        ],
    )
    write_csv(
        DATA_OUT / "figure4_moving_diversity_v3.csv",
        diversity_rows,
        [
            "year",
            "window_start",
            "window_end",
            "documents_in_window",
            "normalized_shannon_diversity",
        ],
    )
    write_csv(
        DATA_OUT / "figure4_emergence_v3.csv",
        emergence_rows,
        [
            "family",
            "first_observed_year",
            "last_observed_year",
            "raw_signal_documents",
            "interpretation_limit",
        ],
    )
    return {
        "year_bins": year_bins,
        "annual_total": annual_total,
        "annual_family": annual_family,
        "annual_distributed": annual_distributed,
        "period_denominators": period_denominators,
        "period_family": period_family,
        "change_rows": change_rows,
        "diversity_rows": diversity_rows,
        "emergence_rows": emergence_rows,
    }


def style_panel(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.set_facecolor(PANEL)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.45, zorder=0)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.55)


def canonical_venue(value: str) -> str:
    aliases = {
        "ieee access": "IEEE Access",
        "journal of intelligent & robotic systems": "Journal of Intelligent & Robotic Systems",
        "journal of intelligent and robotic systems": "Journal of Intelligent & Robotic Systems",
        "lecture notes in computer science": "Lecture Notes in Computer Science",
        "frontiers in robotics and ai": "Frontiers in Robotics and AI",
        "robotics and autonomous systems": "Robotics and Autonomous Systems",
        "autonomous robots": "Autonomous Robots",
        "sensors": "Sensors",
        "arxiv (cornell university)": "arXiv",
        "arxiv": "arXiv",
    }
    cleaned = re.sub(r"\s+", " ", html.unescape(value or "")).strip()
    return aliases.get(cleaned.casefold(), cleaned)


def top_venues(rows: list[dict[str, str]], limit: int = 7) -> list[tuple[str, int]]:
    counts = Counter(
        canonical_venue(row.get("venue", ""))
        for row in rows
        if row.get("venue", "").strip()
    )
    return counts.most_common(limit)


def build_figure4(rows: list[dict[str, str]], temporal: dict[str, Any]) -> Path:
    configure_plotting()
    fig = plt.figure(figsize=(7.25, 6.50), facecolor="white")
    gs = fig.add_gridspec(
        3,
        6,
        left=0.065,
        right=0.965,
        bottom=0.122,
        top=0.765,
        height_ratios=[1.72, 1.08, 0.98],
        hspace=0.47,
        wspace=0.52,
    )
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0:2])
    ax_c = fig.add_subplot(gs[1, 2:4])
    ax_d = fig.add_subplot(gs[1, 4:6])
    ax_e = fig.add_subplot(gs[2, 0:4])
    ax_f = fig.add_subplot(gs[2, 4:6])

    fig.text(
        0.022,
        0.972,
        "Actividad académica y evolución temática del corpus (1979–2026)",
        fontsize=13.7,
        weight="bold",
        color=ORANGE,
        va="top",
    )
    fig.text(
        0.022,
        0.927,
        "Seis lecturas complementarias sobre volumen, composición, transición temática, diversidad y venues recurrentes",
        fontsize=8.0,
        color=INK,
        va="top",
    )
    legend_handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=FAMILY_COLORS[family],
               markeredgecolor="none", markersize=7, label=family)
        for family in FAMILY_ORDER
    ]
    legend_handles.append(
        Line2D([0], [0], color=ORANGE, marker="o", markersize=4.5, linewidth=1.5,
               label="Distribuido / descentralizado (%)")
    )
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.895),
        ncol=4,
        frameon=False,
        fontsize=6.15,
        handlelength=1.0,
        handletextpad=0.35,
        columnspacing=1.0,
    )

    # (a) Annual activity, fractional thematic composition, distributed signal.
    year_bins = temporal["year_bins"]
    x = np.arange(len(year_bins))
    bottom = np.zeros(len(year_bins))
    for family in FAMILY_ORDER:
        values = np.array([temporal["annual_family"][year][family] for year in year_bins])
        ax_a.bar(x, values, bottom=bottom, color=FAMILY_COLORS[family], width=0.78, zorder=2)
        bottom += values
    totals = np.array([temporal["annual_total"][year] for year in year_bins])
    for xi, total in zip(x, totals):
        if total:
            ax_a.text(xi, total + 0.65, str(total), ha="center", va="bottom", fontsize=5.5,
                      weight="bold", color=INK)
    ax_a.set_xlim(-0.7, len(year_bins) - 0.3)
    ax_a.set_ylim(0, max(totals) * 1.17)
    tick_indices = [0] + [i for i, label in enumerate(year_bins) if label.isdigit() and int(label) % 2 == 0]
    if len(year_bins) - 1 not in tick_indices:
        tick_indices.append(len(year_bins) - 1)
    ax_a.set_xticks(tick_indices, [year_bins[i] for i in tick_indices], rotation=0)
    ax_a.set_ylabel("Trabajos/año")
    ax_a.set_title("(a) Actividad anual y desplazamiento del foco temático", loc="left", pad=-13)
    style_panel(ax_a, "y")
    ax_a_r = ax_a.twinx()
    distributed_share = [
        100 * temporal["annual_distributed"][year] / temporal["annual_total"][year]
        if temporal["annual_total"][year]
        else np.nan
        for year in year_bins
    ]
    ax_a_r.plot(x, distributed_share, color=ORANGE, marker="o", markersize=2.8,
                linewidth=1.35, zorder=5)
    ax_a_r.set_ylim(0, 105)
    ax_a_r.set_ylabel("Señal distribuida (%)", color=ORANGE, labelpad=5)
    ax_a_r.tick_params(axis="y", colors=ORANGE, labelsize=5.8, length=0)
    for spine in ax_a_r.spines.values():
        spine.set_visible(False)

    # (b) Period shares; all rows sum to 100 by construction.
    y = np.arange(len(PERIOD_ORDER))
    left = np.zeros(len(PERIOD_ORDER))
    for family in FAMILY_ORDER:
        values = np.array(
            [
                100 * temporal["period_family"][period][family]
                / temporal["period_denominators"][period]
                for period in PERIOD_ORDER
            ]
        )
        ax_b.barh(y, values, left=left, color=FAMILY_COLORS[family], height=0.46,
                  edgecolor="white", linewidth=0.35, zorder=2)
        for yi, value, start in zip(y, values, left):
            if value >= 10:
                ax_b.text(start + value / 2, yi, f"{value:.0f}%", ha="center", va="center",
                          fontsize=5.2, weight="bold",
                          color="white" if family not in {"Planning / routing", "Feasibility / contact"} else INK)
        left += values
    ax_b.set_yticks(y, [f"{label}" for label in PERIOD_LABELS])
    ax_b.set_xlim(0, 100)
    ax_b.set_xlabel("% del periodo")
    ax_b.invert_yaxis()
    ax_b.set_title("(b) Cambio temático por periodos", loc="left", pad=-10)
    style_panel(ax_b, "x")

    # (c) Change in share from the first to the most recent period.
    changes = [float(row["change_percentage_points"]) for row in temporal["change_rows"]]
    labels = [
        "Coal.", "Transp.", "Planif.", "Factib.", "Recov.", "Learning", "Fund."
    ]
    yc = np.arange(len(labels))
    ax_c.axvline(0, color=INK, linewidth=0.65, zorder=3)
    for yi, value, family in zip(yc, changes, FAMILY_ORDER):
        ax_c.barh(yi, value, color=FAMILY_COLORS[family], height=0.42, zorder=2)
        ax_c.text(
            value + (0.32 if value >= 0 else -0.32),
            yi,
            f"{value:+.1f}",
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=5.4,
            weight="bold",
        )
    bound = max(8.0, math.ceil(max(abs(v) for v in changes) + 2))
    ax_c.set_xlim(-bound, bound)
    ax_c.set_yticks(yc, labels)
    ax_c.invert_yaxis()
    ax_c.set_xlabel("Cambio en cuota (p.p.)")
    ax_c.set_title("(c) Cambio de cuota", loc="left", pad=-10)
    ax_c.text(0.5, 0.995, "≤2010 → 2022–2026", transform=ax_c.transAxes,
              ha="center", va="top", fontsize=5.7, color=MUTED)
    style_panel(ax_c, "x")

    # (d) Three-year trailing thematic diversity.
    diversity_rows = temporal["diversity_rows"]
    years = np.array([int(row["year"]) for row in diversity_rows])
    diversity = np.array(
        [float(row["normalized_shannon_diversity"]) if row["normalized_shannon_diversity"] else np.nan
         for row in diversity_rows]
    )
    ax_d.plot(years, diversity, color=ORANGE, marker="o", markersize=2.2,
              linewidth=1.35, zorder=3)
    ax_d.fill_between(years, diversity, color=ORANGE, alpha=0.09, zorder=1)
    ax_d.set_xlim(1978, 2027)
    ax_d.set_ylim(0, 1.02)
    ax_d.set_xticks([1980, 1990, 2000, 2010, 2020, 2026])
    ax_d.set_ylabel("H* normalizado")
    ax_d.set_xlabel("Año")
    ax_d.set_title("(d) Diversidad temática móvil", loc="left", pad=-10)
    ax_d.text(0.02, 0.91, "ventana retrospectiva de 3 años", transform=ax_d.transAxes,
              fontsize=5.5, color=MUTED)
    style_panel(ax_d, "y")

    # (e) First and last observed family signal.
    first_years = [int(row["first_observed_year"]) for row in temporal["emergence_rows"]]
    ye = np.arange(len(FAMILY_ORDER))
    short_labels = ["Coalition", "Transport", "Planning", "Feasibility", "Recovery", "Learning / RL", "Foundational"]
    for yi, family, first in zip(ye, FAMILY_ORDER, first_years):
        ax_e.hlines(yi, first, 2026, color=FAMILY_COLORS[family], linewidth=2.0)
        ax_e.scatter([first, 2026], [yi, yi], s=15, color=FAMILY_COLORS[family], zorder=3,
                     edgecolor="white", linewidth=0.35)
        ax_e.text(first, yi + 0.30, str(first), ha="center", fontsize=5.2)
    ax_e.text(2026.2, -0.45, "→ 2026", ha="left", fontsize=5.5, color=MUTED)
    ax_e.set_xlim(1978, 2030)
    ax_e.set_xticks([1980, 1990, 2000, 2010, 2020])
    ax_e.set_yticks(ye, short_labels)
    ax_e.invert_yaxis()
    ax_e.set_xlabel("Año")
    ax_e.set_title("(e) Timeline de primera señal temática", loc="left", pad=-10)
    style_panel(ax_e, "x")

    # (f) Recurrent venues.
    venues = top_venues(rows, 7)[::-1]
    venue_abbrev = {
        "Journal of Intelligent & Robotic Systems": "JINT",
        "Frontiers in Robotics and AI": "Frontiers RAI",
        "Lecture Notes in Computer Science": "LNCS",
        "Autonomous Robots": "Autonomous Robots",
    }
    labels_f = [venue_abbrev.get(name, name) for name, _ in venues]
    values_f = [count for _, count in venues]
    yf = np.arange(len(venues))
    ax_f.hlines(yf, 0, values_f, color="#AEB8C9", linewidth=0.75, zorder=1)
    ax_f.scatter(values_f, yf, color=INK, s=25, zorder=3)
    for yi, value in zip(yf, values_f):
        ax_f.text(value + 0.35, yi, str(value), va="center", fontsize=5.3, weight="bold")
    ax_f.set_yticks(yf, labels_f)
    ax_f.set_xlim(0, max(values_f) + 3)
    ax_f.set_xlabel("Número de trabajos")
    ax_f.set_title("(f) Venues recurrentes", loc="left", pad=-10)
    style_panel(ax_f, "x")

    fig.text(
        0.065,
        0.055,
        "Fuente: elaboración propia a partir del corpus analítico consolidado (n=244; 243 fechados; observación parcial de 2026).",
        fontsize=5.5,
        color=INK,
    )
    fig.text(
        0.065,
        0.031,
        "Nota: conteo fraccional multietiqueta (peso total 1 por documento); H*=Shannon/log(7), ventana retrospectiva de 3 años. Gris incluye revisiones y contexto sin señal SP específica; las primeras señales y cuotas describen el corpus adquirido.",
        fontsize=5.05,
        color=MUTED,
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    pdf = FIGURES / "fig04_academic_trends_full_corpus.pdf"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025)
    fig.savefig(FIGURES / "fig04_academic_trends_full_corpus.png", dpi=240,
                bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)
    return pdf


def author_graph(rows: list[dict[str, str]]) -> tuple[nx.Graph, nx.Graph, list[set[str]], Counter[str]]:
    author_counts: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        authors = sorted(set(parse_authors(row.get("authors", ""))))
        author_counts.update(authors)
        edge_counts.update(combinations(authors, 2))

    full = nx.Graph()
    for author, count in author_counts.items():
        full.add_node(author, paper_count=count)
    for (left, right), count in edge_counts.items():
        full.add_edge(left, right, paper_count=count, weight=count)

    recurrent = {author for author, count in author_counts.items() if count >= 2}
    induced = full.subgraph(recurrent).copy()
    induced.remove_nodes_from(list(nx.isolates(induced)))
    components = [
        set(component)
        for component in nx.connected_components(induced)
        if len(component) >= 3
    ]

    papers_by_author: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        for author in parse_authors(row.get("authors", "")):
            papers_by_author[author].add(row["candidate_id"])
    components.sort(
        key=lambda component: (
            -len(set().union(*(papers_by_author[author] for author in component))),
            -len(component),
            sorted(component),
        )
    )
    core_nodes = set().union(*components) if components else set()
    core = induced.subgraph(core_nodes).copy()
    for index, component in enumerate(components, start=1):
        for node in component:
            core.nodes[node]["component"] = index
    return full, core, components, author_counts


def topic_graph(rows: list[dict[str, str]]) -> tuple[nx.Graph, nx.Graph, list[set[str]], float]:
    fields = [
        "theme_signals_title_abstract",
        "method_focus_title_abstract",
        "application_signals_title_abstract",
    ]
    node_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        labels: set[str] = set()
        for field in fields:
            labels.update(signals(row, field))
        labels.discard("CONTEXT_other")
        node_counts.update(labels)
        pair_counts.update(combinations(sorted(labels), 2))

    graph = nx.Graph()
    for node, count in node_counts.items():
        graph.add_node(node, paper_count=count)
    for (left, right), count in pair_counts.items():
        if count < 2:
            continue
        association = count / math.sqrt(node_counts[left] * node_counts[right])
        graph.add_edge(left, right, paper_count=count, weight=association)
    graph.remove_nodes_from(list(nx.isolates(graph)))
    communities = [
        set(community)
        for community in nx.community.louvain_communities(
            graph, weight="weight", resolution=1.0, seed=20260914
        )
    ]
    communities.sort(key=lambda community: (-len(community), sorted(community)))
    for index, community in enumerate(communities, start=1):
        for node in community:
            graph.nodes[node]["community"] = index
    modularity = nx.community.modularity(graph, communities, weight="weight")

    # Readable association backbone: retain each node's three strongest ties,
    # plus every high-frequency co-occurrence.
    keep: set[tuple[str, str]] = set()
    for node in graph.nodes:
        ranked = sorted(
            graph.edges(node, data=True),
            key=lambda edge: (-edge[2]["weight"], -edge[2]["paper_count"], edge[1]),
        )
        for left, right, _ in ranked[:3]:
            keep.add(tuple(sorted((left, right))))
    keep.update(
        tuple(sorted((left, right)))
        for left, right, data in graph.edges(data=True)
        if data["paper_count"] >= 8
    )
    backbone = nx.Graph()
    backbone.add_nodes_from(graph.nodes(data=True))
    for left, right in sorted(keep):
        backbone.add_edge(left, right, **graph.edges[left, right])
    return graph, backbone, communities, modularity


def surname(author: str) -> str:
    if "," in author:
        return author.split(",", 1)[0].strip()
    tokens = author.split()
    return tokens[-1] if tokens else author


def author_component_tables(
    rows: list[dict[str, str]],
    core: nx.Graph,
    components: list[set[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], np.ndarray]:
    node_rows = [
        {
            "author": node,
            "paper_count": core.nodes[node]["paper_count"],
            "component": core.nodes[node]["component"],
        }
        for node in sorted(core.nodes)
    ]
    edge_rows = [
        {
            "author_left": min(left, right),
            "author_right": max(left, right),
            "coauthored_paper_count": data["paper_count"],
        }
        for left, right, data in sorted(core.edges(data=True))
    ]
    component_rows: list[dict[str, Any]] = []
    matrix = np.zeros((len(components), len(FAMILY_ORDER)))
    for index, component in enumerate(components, start=1):
        selected = [
            row
            for row in rows
            if component.intersection(parse_authors(row.get("authors", "")))
        ]
        totals = Counter()
        for row in selected:
            totals.update(family_weights(row))
        total = sum(totals.values())
        matrix[index - 1] = [100 * totals[family] / total if total else 0 for family in FAMILY_ORDER]
        ranked_authors = sorted(
            component,
            key=lambda author: (-core.nodes[author]["paper_count"], author),
        )
        component_rows.append(
            {
                "component": index,
                "author_count": len(component),
                "distinct_papers": len(selected),
                "representative_authors": "; ".join(ranked_authors[:4]),
                "all_exact_author_strings": "; ".join(sorted(component)),
            }
        )
    return node_rows, edge_rows, component_rows, matrix


def topic_tables(
    graph: nx.Graph,
    communities: list[set[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    node_rows = [
        {
            "topic": node,
            "display_label": TOPIC_LABELS.get(node, node.replace("_", " ")),
            "paper_count": graph.nodes[node]["paper_count"],
            "community": graph.nodes[node]["community"],
        }
        for node in sorted(graph.nodes)
    ]
    edge_rows = [
        {
            "topic_left": min(left, right),
            "topic_right": max(left, right),
            "cooccurring_paper_count": data["paper_count"],
            "association_strength": f"{data['weight']:.6f}",
        }
        for left, right, data in sorted(graph.edges(data=True))
    ]
    community_rows = []
    for index, community in enumerate(communities, start=1):
        community_rows.append(
            {
                "community": index,
                "topic_count": len(community),
                "topics": "; ".join(sorted(community)),
            }
        )
    return node_rows, edge_rows, community_rows


def component_layout(core: nx.Graph, components: list[set[str]]) -> dict[str, np.ndarray]:
    centers = [
        (-0.78, 0.68), (-0.25, 0.72), (0.33, 0.69), (0.80, 0.60),
        (-0.72, 0.04), (-0.20, 0.12), (0.37, 0.07), (0.79, -0.02),
        (-0.55, -0.61), (0.02, -0.57), (0.61, -0.60),
    ]
    output: dict[str, np.ndarray] = {}
    for index, component in enumerate(components):
        subgraph = core.subgraph(component)
        if len(component) == 3:
            local = nx.circular_layout(subgraph)
        else:
            local = nx.spring_layout(
                subgraph,
                weight="weight",
                seed=20260914 + index,
                iterations=300,
            )
        center = np.array(centers[index])
        scale = 0.19 if len(component) >= 5 else 0.14
        for node, position in local.items():
            output[node] = center + scale * np.asarray(position)
    return output


def topic_cluster_layout(
    graph: nx.Graph, communities: list[set[str]]
) -> tuple[dict[str, np.ndarray], dict[int, np.ndarray]]:
    """Place the three detected topic communities without a central hairball."""
    centers = {
        1: np.array([0.0, -0.34]),
        2: np.array([-0.62, 0.68]),
        3: np.array([0.62, 0.68]),
    }
    positions: dict[str, np.ndarray] = {}
    for index, community in enumerate(communities, start=1):
        center = centers[index]
        if index == 1:
            anchors = {
                "SP1_coalition_allocation": center + np.array([0.0, 0.12]),
                "consensus_distributed": center + np.array([-0.24, -0.08]),
                "auction_market": center + np.array([0.24, -0.08]),
                "TRANSVERSAL_resilience_communication": center + np.array([0.0, -0.30]),
            }
            positions.update({node: point for node, point in anchors.items() if node in community})
            remaining = sorted(community - set(anchors))
            angles = np.linspace(0.05 * math.pi, 1.95 * math.pi, len(remaining), endpoint=False)
            for node, angle in zip(remaining, angles):
                positions[node] = center + np.array([0.73 * math.cos(angle), 0.50 * math.sin(angle)])
        else:
            ordered = sorted(community)
            angles = np.linspace(0, 2 * math.pi, len(ordered), endpoint=False) + math.pi / 4
            for node, angle in zip(ordered, angles):
                positions[node] = center + np.array([0.28 * math.cos(angle), 0.22 * math.sin(angle)])
    for node in graph.nodes:
        positions.setdefault(node, np.zeros(2))
    return positions, centers


def build_bibliometric_figure(
    rows: list[dict[str, str]],
    full_author_graph: nx.Graph,
    core: nx.Graph,
    components: list[set[str]],
    author_counts: Counter[str],
    topic_full: nx.Graph,
    topic_backbone: nx.Graph,
    topic_communities: list[set[str]],
    topic_modularity: float,
    component_rows: list[dict[str, Any]],
    component_matrix: np.ndarray,
) -> Path:
    configure_plotting()
    palette = [BLUE, ORANGE, GREEN, PURPLE, TEAL, YELLOW, PEACH, "#B45373", "#4B7F52", "#5369A5", GRAY]
    topic_palette = [BLUE, ORANGE, GREEN, PURPLE, TEAL]
    fig = plt.figure(figsize=(7.25, 5.75), facecolor="white")
    outer = fig.add_gridspec(
        2,
        1,
        left=0.045,
        right=0.975,
        bottom=0.045,
        top=0.965,
        height_ratios=[1.38, 1.0],
        hspace=0.29,
    )
    top = outer[0].subgridspec(1, 2, width_ratios=[1.18, 0.82], wspace=0.17)
    bottom = outer[1].subgridspec(1, 2, width_ratios=[1.57, 0.63], wspace=0.08)
    ax_author = fig.add_subplot(top[0, 0])
    ax_topic = fig.add_subplot(top[0, 1])
    ax_heat = fig.add_subplot(bottom[0, 0])
    ax_key = fig.add_subplot(bottom[0, 1])

    # (a) Recurrent co-authorship components.
    positions = component_layout(core, components)
    for index, component in enumerate(components, start=1):
        color = palette[(index - 1) % len(palette)]
        subgraph = core.subgraph(component)
        nx.draw_networkx_edges(
            subgraph,
            positions,
            ax=ax_author,
            width=[0.35 + 0.42 * subgraph.edges[edge]["paper_count"] for edge in subgraph.edges],
            edge_color=color,
            alpha=0.48,
        )
        nx.draw_networkx_nodes(
            subgraph,
            positions,
            ax=ax_author,
            node_size=[26 + 17 * core.nodes[node]["paper_count"] for node in subgraph.nodes],
            node_color=color,
            edgecolors="white",
            linewidths=0.55,
        )
        center = np.mean([positions[node] for node in component], axis=0)
        ax_author.text(center[0], center[1] + 0.215, f"A{index}", ha="center", va="bottom",
                       fontsize=6.2, weight="bold", color=color)
        ranked = sorted(
            component,
            key=lambda author: (-core.nodes[author]["paper_count"], -core.degree(author), author),
        )
        labels = {
            node: surname(node)
            for node in ranked
            if core.nodes[node]["paper_count"] >= 3 or node == ranked[0]
        }
        nx.draw_networkx_labels(
            subgraph,
            positions,
            labels=labels,
            ax=ax_author,
            font_size=5.15,
            font_color=INK,
            verticalalignment="top",
        )
    ax_author.set_title("(a) Núcleos recurrentes de coautoría", loc="left", pad=2)
    ax_author.text(
        0.0,
        -0.03,
        "Autores: ≥2 documentos; componentes: ≥3 autores.\n"
        "Grosor = coautorías; tamaño = recurrencia.",
        transform=ax_author.transAxes,
        fontsize=5.55,
        color=MUTED,
        va="top",
    )
    ax_author.set_xlim(-1.05, 1.05)
    ax_author.set_ylim(-0.92, 1.0)
    ax_author.axis("off")

    # (b) Topic-method-application co-occurrence backbone.
    topic_positions, topic_centers = topic_cluster_layout(topic_backbone, topic_communities)
    edge_widths = [0.4 + 4.6 * topic_backbone.edges[edge]["weight"] for edge in topic_backbone.edges]
    nx.draw_networkx_edges(
        topic_backbone,
        topic_positions,
        ax=ax_topic,
        width=edge_widths,
        edge_color="#AAB3C4",
        alpha=0.54,
    )
    node_colors = [
        topic_palette[(topic_backbone.nodes[node]["community"] - 1) % len(topic_palette)]
        for node in topic_backbone.nodes
    ]
    nx.draw_networkx_nodes(
        topic_backbone,
        topic_positions,
        ax=ax_topic,
        node_size=[24 + 2.4 * topic_backbone.nodes[node]["paper_count"] for node in topic_backbone.nodes],
        node_color=node_colors,
        edgecolors="white",
        linewidths=0.55,
    )
    for node, position in topic_positions.items():
        community = topic_backbone.nodes[node]["community"]
        vector = position - topic_centers[community]
        norm = float(np.linalg.norm(vector))
        if norm < 0.14:
            offset = np.array([0.0, 7.0])
        else:
            offset = vector / norm * 8.5
        ax_topic.annotate(
            TOPIC_LABELS.get(node, node.replace("_", " ")),
            xy=position,
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=4.8,
            color=INK,
            bbox={"boxstyle": "round,pad=0.10", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
            zorder=5,
        )
    ax_topic.set_title("(b) Comunidades temático-metodológicas", loc="left", pad=2)
    ax_topic.text(
        0.0,
        -0.03,
        f"Coocurrencias ≥2; Louvain: {len(topic_communities)} comunidades, Q={topic_modularity:.2f}.\n"
        "Grosor = asociación normalizada.",
        transform=ax_topic.transAxes,
        fontsize=5.55,
        color=MUTED,
        va="top",
    )
    ax_topic.set_xlim(-1.18, 1.18)
    ax_topic.set_ylim(-1.02, 1.10)
    ax_topic.axis("off")

    # (c) Author-component thematic profile.
    display_count = min(8, len(components))
    heat = component_matrix[:display_count]
    cmap = LinearSegmentedColormap.from_list("mrob_heat", ["#F7F8FA", "#F8C9B7", ORANGE])
    image = ax_heat.imshow(heat, aspect="auto", cmap=cmap, vmin=0, vmax=max(45, float(heat.max())))
    short_columns = ["MRTA", "Transp.", "Ruta", "Contacto", "Recup.", "Aprend.", "Base"]
    row_labels = [f"A{row['component']}" for row in component_rows[:display_count]]
    ax_heat.set_xticks(np.arange(len(short_columns)), short_columns)
    ax_heat.set_yticks(np.arange(display_count), row_labels)
    ax_heat.tick_params(axis="x", labelsize=7.0, length=0, pad=3)
    ax_heat.tick_params(axis="y", labelsize=7.3, length=0, pad=4)
    for i in range(display_count):
        for j in range(len(FAMILY_ORDER)):
            value = heat[i, j]
            if value >= 7:
                ax_heat.text(j, i, f"{value:.0f}", ha="center", va="center",
                             fontsize=6.35, weight="bold",
                             color="white" if value >= 33 else INK)
    ax_heat.set_title("(c) Perfil temático por núcleo (%)", loc="left", pad=6)
    for spine in ax_heat.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.55)

    # Keep the matrix readable at print size: codes stay on the axis and the
    # author names move to a separate key instead of becoming long tick labels.
    ax_key.set_xlim(0, 1)
    ax_key.set_ylim(0, 1)
    ax_key.axis("off")
    ax_key.text(0.02, 0.985, "Clave de núcleos", fontsize=8.4, weight="bold",
                color=INK, va="top")
    y = 0.875
    for index, row in enumerate(component_rows[:display_count]):
        representatives = row["representative_authors"].split("; ")[:3]
        names = " · ".join(surname(author) for author in representatives)
        if len(names) > 42:
            names = f"{surname(representatives[0])} et al."
        color = palette[index % len(palette)]
        ax_key.text(0.02, y, f"A{row['component']}", fontsize=6.8, weight="bold",
                    color=color, va="top")
        ax_key.text(
            0.16,
            y,
            f"{names}\n{row['distinct_papers']} documentos",
            fontsize=5.75,
            color=INK,
            linespacing=1.08,
            va="top",
        )
        y -= 0.105
    ax_key.text(0.02, 0.025, "Los porcentajes se calculan dentro de cada núcleo.",
                fontsize=5.35, color=MUTED, va="bottom")
    FIGURES.mkdir(parents=True, exist_ok=True)
    pdf = FIGURES / "fig08_bibliometric_clusters_full_corpus.pdf"
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.025)
    fig.savefig(FIGURES / "fig08_bibliometric_clusters_full_corpus.png", dpi=240,
                bbox_inches="tight", pad_inches=0.025)
    plt.close(fig)
    return pdf


def main() -> None:
    rows = read_csv(CORPUS_PATH)
    if len(rows) != 244:
        raise RuntimeError(f"Expected frozen 244-record V3 corpus, found {len(rows)}")
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    temporal = build_temporal_tables(rows)
    figure4 = build_figure4(rows, temporal)

    full_author_graph, core, components, author_counts = author_graph(rows)
    node_rows, edge_rows, component_rows, component_matrix = author_component_tables(
        rows, core, components
    )
    write_csv(DATA_OUT / "bibliometric_author_nodes_v3.csv", node_rows,
              ["author", "paper_count", "component"])
    write_csv(DATA_OUT / "bibliometric_author_edges_v3.csv", edge_rows,
              ["author_left", "author_right", "coauthored_paper_count"])
    write_csv(DATA_OUT / "bibliometric_author_components_v3.csv", component_rows,
              ["component", "author_count", "distinct_papers", "representative_authors", "all_exact_author_strings"])

    topic_full, topic_backbone, topic_communities, topic_modularity = topic_graph(rows)
    topic_node_rows, topic_edge_rows, topic_community_rows = topic_tables(
        topic_full, topic_communities
    )
    write_csv(DATA_OUT / "bibliometric_topic_nodes_v3.csv", topic_node_rows,
              ["topic", "display_label", "paper_count", "community"])
    write_csv(DATA_OUT / "bibliometric_topic_edges_v3.csv", topic_edge_rows,
              ["topic_left", "topic_right", "cooccurring_paper_count", "association_strength"])
    write_csv(DATA_OUT / "bibliometric_topic_communities_v3.csv", topic_community_rows,
              ["community", "topic_count", "topics"])

    figure8 = build_bibliometric_figure(
        rows,
        full_author_graph,
        core,
        components,
        author_counts,
        topic_full,
        topic_backbone,
        topic_communities,
        topic_modularity,
        component_rows,
        component_matrix,
    )

    venues = top_venues(rows, 7)
    change = {
        row["family"]: float(row["change_percentage_points"])
        for row in temporal["change_rows"]
    }
    latest_diversity = next(
        float(row["normalized_shannon_diversity"])
        for row in reversed(temporal["diversity_rows"])
        if row["normalized_shannon_diversity"]
    )
    all_edges = Counter(
        {
            tuple(sorted((left, right))): data["paper_count"]
            for left, right, data in full_author_graph.edges(data=True)
        }
    )
    top_pair, top_pair_count = all_edges.most_common(1)[0]
    metrics = {
        "records": len(rows),
        "dated_records": sum(row.get("year", "").isdigit() for row in rows),
        "unknown_year_records": sum(not row.get("year", "").isdigit() for row in rows),
        "date_range": [
            min(int(row["year"]) for row in rows if row.get("year", "").isdigit()),
            max(int(row["year"]) for row in rows if row.get("year", "").isdigit()),
        ],
        "exact_author_strings": len(author_counts),
        "recurrent_author_strings_ge_2": sum(count >= 2 for count in author_counts.values()),
        "coauthor_edges_full": full_author_graph.number_of_edges(),
        "displayed_author_core_nodes": core.number_of_nodes(),
        "displayed_author_core_edges": core.number_of_edges(),
        "displayed_author_components_ge_3": len(components),
        "top_coauthor_pair": list(top_pair),
        "top_coauthor_pair_papers": top_pair_count,
        "distinct_venues": len(
            {canonical_venue(row.get("venue", "")) for row in rows if row.get("venue", "").strip()}
        ),
        "top_venues": [{"venue": venue, "papers": count} for venue, count in venues],
        "topic_nodes": topic_full.number_of_nodes(),
        "topic_edges_ge_2": topic_full.number_of_edges(),
        "topic_backbone_edges": topic_backbone.number_of_edges(),
        "topic_communities": len(topic_communities),
        "topic_modularity": round(topic_modularity, 6),
        "quota_change_percentage_points": change,
        "latest_three_year_diversity": round(latest_diversity, 6),
        "counting_rule": "Fractional multi-label: each document contributes total weight 1 across dashboard families.",
        "interpretation_limit": "Describes the acquired V3 corpus and title/abstract signals; not field-wide prevalence, impact, or implementation evidence.",
    }
    metrics_path = DATA_OUT / "full_corpus_bibliometric_metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": "academic-review/scripts/build_v3_full_corpus_bibliometrics.py",
        "input": str(CORPUS_PATH.relative_to(BASE)).replace("\\", "/"),
        "input_sha256": sha256(CORPUS_PATH),
        "outputs": {
            str(figure4.relative_to(BASE)).replace("\\", "/"): sha256(figure4),
            str(figure8.relative_to(BASE)).replace("\\", "/"): sha256(figure8),
            str(metrics_path.relative_to(BASE)).replace("\\", "/"): sha256(metrics_path),
        },
        "parameters": {
            "diversity_window_years": 3,
            "diversity_normalizer": "log(7)",
            "author_recurrence_threshold": 2,
            "author_component_minimum_size": 3,
            "topic_edge_minimum_cooccurrence": 2,
            "topic_community_algorithm": "networkx.louvain_communities",
            "topic_community_seed": 20260914,
            "topic_community_resolution": 1.0,
        },
    }
    manifest_path = OUT / "analysis_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
