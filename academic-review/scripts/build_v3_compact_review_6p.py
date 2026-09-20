"""Build the restored six-page V3 literature-review figures.

The V3 panels are generated from frozen analytical CSV files.  Legacy values
are restricted to numbers explicitly printed in the author-supplied LaTeX
snapshot; the missing legacy dashboard dataset is never reconstructed.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

import build_v3_compact_review as base


BASE = Path(__file__).resolve().parents[1]
V3 = BASE / "literature-review-v3"
DATA = V3 / "data"
OUT = V3 / "compact-6p"
FIGURES = OUT / "figures"

ORANGE = base.ORANGE
BLUE = base.BLUE
GREEN = base.GREEN
PURPLE = base.PURPLE
YELLOW = base.YELLOW
INK = base.INK
MUTED = base.MUTED
GRID = base.GRID
SOFT = base.SOFT
RED = "#C9463D"
TEAL = "#278A8A"


# Only values visibly encoded in academic_literature_review (1).tex.
LEGACY = {
    "corpus": 59,
    "dated": 54,
    "families": {
        "Coalición": 18,
        "Transporte compartido": 23,
        "Red/seguridad": 15,
        "Fundacional": 6,
    },
    "coverage": {
        "Transporte compartido": 23,
        "Reclutamiento": 18,
        "Certificación física": 13,
        "Transporte + distribuido": 10,
        "Heterogéneo + coalición variable": 9,
        "Transporte + reemplazo": 2,
        "Heterogéneo + transporte": 0,
        "Físico + distribuido + reemplazo": 0,
    },
    # Original horizontal coordinates, normalized from its 28--148 axis.
    "authority_x": {
        "Reclutar": (45 - 28) / 120 * 100,
        "Certificar": (76 - 28) / 120 * 100,
        "Acoplar": (48 - 28) / 120 * 100,
        "Transportar": (44 - 28) / 120 * 100,
        "Recuperar": (79 - 28) / 120 * 100,
    },
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def signals(row: dict[str, str], field: str) -> set[str]:
    return {item for item in row.get(field, "").split(";") if item}


def save(fig: plt.Figure, name: str, pad: float = 0.035) -> None:
    fig.savefig(FIGURES / name, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)


def freeze_legacy_values() -> None:
    rows: list[dict[str, object]] = []
    for label, value in LEGACY["families"].items():
        rows.append({"group": "family", "label": label, "value": value})
    for label, value in LEGACY["coverage"].items():
        rows.append({"group": "coverage", "label": label, "value": value})
    for label, value in LEGACY["authority_x"].items():
        rows.append({"group": "authority_ordinal_0_100", "label": label, "value": f"{value:.3f}"})
    rows.extend(
        [
            {"group": "snapshot", "label": "corpus", "value": LEGACY["corpus"]},
            {"group": "snapshot", "label": "dated_window", "value": LEGACY["dated"]},
        ]
    )
    with (OUT / "legacy_snapshot_values.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["group", "label", "value"])
        writer.writeheader()
        writer.writerows(rows)


def methodological_map(corpus: list[dict[str, str]]) -> None:
    method_style = [
        ("learning_based", "Aprendizaje", PURPLE),
        ("evolutionary_metaheuristic", "Metaheurística", ORANGE),
        ("game_theoretic", "Juegos", RED),
        ("auction_market", "Mercados", YELLOW),
        ("consensus_distributed", "Consenso", BLUE),
        ("formation_control", "Control/formación", GREEN),
        ("safety_reactive", "Seguridad/CBF", TEAL),
        ("exact_optimization", "Optimización", "#6B7280"),
    ]
    close_ids = {
        path.name.split("_")[0]
        for path in (V3 / "close-read").glob("*.md")
        if path.name != "README.md"
    }
    label_ids = {
        "CFE80E994AC44": "Ramchurn 2010",
        "C60F209AB33AE": "Liu--Shell 2013",
        "C0BBF943B50C0": "Guerrero 2017",
        "C5423D5A19BA0": "Tuci 2018",
        "C20FBE73D7292": "Zitouni 2020",
        "CC1697E0C2E40": "Mazdin 2021",
        "CF7C60AFD9DE7": "De Ryck 2021",
        "C96F294D621AC": "Verma 2025",
        "C1B0A43A71755": "Muhammed 2026",
        "CF0BC51D9FA65": "Song 2026",
        "CCB936E7536AC": "Varghese 2026",
    }

    def position(row: dict[str, str]) -> tuple[float, float, str, str]:
        arch = signals(row, "architecture_signals_title_abstract")
        methods = signals(row, "method_focus_title_abstract")
        if "distributed_decentralized" in arch and "centralized" in arch:
            x = 0.0
        elif "distributed_decentralized" in arch:
            x = -0.72
        elif "centralized" in arch:
            x = 0.72
        elif "leader_follower" in arch:
            x = 0.48
        elif "hybrid" in arch:
            x = 0.18
        else:
            x = 0.20
        y_map = {
            "learning_based": 0.70,
            "evolutionary_metaheuristic": 0.30,
            "safety_reactive": 0.10,
            "formation_control": -0.22,
            "consensus_distributed": -0.40,
            "game_theoretic": -0.55,
            "auction_market": -0.67,
            "exact_optimization": -0.80,
        }
        selected = next((key for key, _, _ in method_style if key in methods), "other")
        y = y_map.get(selected, -0.02)
        color = next((c for key, _, c in method_style if key == selected), "#A8AFB8")
        digest = hashlib.sha1(row["candidate_id"].encode()).digest()
        x += (digest[0] / 255 - 0.5) * 0.25
        y += (digest[1] / 255 - 0.5) * 0.16
        return x, y, selected, color

    fig, ax = plt.subplots(figsize=(7.2, 3.58))
    ax.axvline(0, color=GRID, lw=0.8, zorder=0)
    ax.axhline(0, color=GRID, lw=0.8, zorder=0)
    positions: dict[str, tuple[float, float]] = {}
    for row in corpus:
        x, y, _, color = position(row)
        positions[row["candidate_id"]] = (x, y)
        is_close = row["candidate_id"] in close_ids
        ax.scatter(
            x,
            y,
            s=34 if is_close else 13,
            c=color,
            alpha=0.92 if is_close else 0.26,
            edgecolors=INK if is_close else "none",
            linewidths=0.45,
            zorder=3 if is_close else 1,
        )
    offsets = {
        "CFE80E994AC44": (-7, 8),
        "C60F209AB33AE": (6, -12),
        "C0BBF943B50C0": (7, 5),
        "C5423D5A19BA0": (-8, 17),
        "C48B0DC86870B": (8, -11),
        "C20FBE73D7292": (-6, 10),
        "CC1697E0C2E40": (-8, -15),
        "CF7C60AFD9DE7": (-7, -12),
        "CD01C8A55EAC3": (9, 15),
        "C4F0B5BB85F46": (9, 7),
        "C96F294D621AC": (-9, -5),
        "C1B0A43A71755": (9, -15),
        "CF0BC51D9FA65": (-6, 8),
        "CCB936E7536AC": (7, -10),
    }
    for idx, (candidate_id, label) in enumerate(label_ids.items()):
        if candidate_id not in positions:
            continue
        x, y = positions[candidate_id]
        dx, dy = offsets[candidate_id]
        ax.annotate(
            label,
            (x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="left" if dx > 0 else "right",
            va="bottom" if dy > 0 else "top",
            fontsize=5.8,
            color=INK,
            arrowprops={"arrowstyle": "-", "color": GRID, "lw": 0.45},
            zorder=4,
        )
    ax.set_xlim(-1.02, 1.02)
    ax.set_ylim(-1.02, 1.02)
    ax.set_xticks([-0.8, 0, 0.8], ["Autoridad local", "Híbrida/ambigua", "Autoridad central"])
    ax.set_yticks([-0.82, 0, 0.72], ["White-box / optimización", "Composición", "Data-driven"])
    ax.tick_params(length=0, labelsize=7.1)
    ax.set_title("Mapa metodológico recalculado · corpus V3 completo y anclas de lectura cercana", loc="left", pad=8)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [Line2D([0], [0], marker="o", color="none", markerfacecolor=c, markeredgecolor="none", markersize=5, label=label) for _, label, c in method_style]
    handles.extend(
        [
            Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor=INK, markersize=5.5, label="Lectura cercana"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#A8AFB8", alpha=0.35, markersize=4.5, label="Mapeo título/resumen"),
        ]
    )
    fig.subplots_adjust(bottom=0.29)
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.31), ncol=5, frameon=False, fontsize=6.1, handletextpad=0.25, columnspacing=0.85)
    fig.text(0.012, 0.008, "Ejes ordinales derivados de señales; la posición no representa calidad, novedad ni rendimiento. Un artículo puede activar varias familias; se muestra la de mayor prioridad gráfica.", fontsize=6.6, color=MUTED)
    save(fig, "fig01_methodological_map.pdf", 0.04)


def snapshot_summary(metrics: dict[str, int], corpus: list[dict[str, str]]) -> None:
    v3 = [metrics["sp1"], metrics["sp2"], metrics["transversal"], sum(r["scientific_role_structural"] == "SURVEY" for r in corpus)]
    old = [18, 23, 15, 6]
    titles = ["Coalición / SP1", "Transporte / SP2", "Red / transversal", "Fundacional / survey"]
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 1.22))
    colors = [BLUE, ORANGE, GREEN, PURPLE]
    for ax, title, legacy, current, color in zip(axes, titles, old, v3, colors):
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.02, 0.04), 0.96, 0.90, boxstyle="round,pad=0.02,rounding_size=0.04", facecolor=SOFT, edgecolor=color, lw=1.0, transform=ax.transAxes))
        ax.text(0.5, 0.79, title, transform=ax.transAxes, ha="center", va="center", color=color, weight="bold", fontsize=7.4)
        ax.text(0.29, 0.49, str(legacy), transform=ax.transAxes, ha="center", va="center", fontsize=14, weight="bold", color=ORANGE)
        ax.text(0.71, 0.49, str(current), transform=ax.transAxes, ha="center", va="center", fontsize=14, weight="bold", color=BLUE)
        ax.text(0.29, 0.20, "legado", transform=ax.transAxes, ha="center", fontsize=6.1, color=MUTED)
        ax.text(0.71, 0.20, "V3", transform=ax.transAxes, ha="center", fontsize=6.1, color=MUTED)
    fig.text(0.012, -0.055, "Cortes no intercambiables: legado n=59 (conteos de familia impresos) frente a V3 n=244 (señales multietiqueta; la cuarta tarjeta compara ‘fundacional’ con rol SURVEY).", fontsize=6.55, color=MUTED)
    save(fig, "fig01b_snapshot_summary.pdf", 0.035)


def capability_matrix(corpus: list[dict[str, str]]) -> None:
    rows = [
        ("Ramchurn 2010", "CFE80E994AC44", [2, 1, 2, 0, 0, 0, 1, 0]),
        ("Liu--Shell 2013", "C60F209AB33AE", [2, 0, 0, 1, 0, 0, 0, 0]),
        ("Guerrero 2017", "C0BBF943B50C0", [2, 1, 2, 1, 0, 0, 1, 0]),
        ("Mazdin 2021", "CC1697E0C2E40", [2, 1, 2, 2, 0, 0, 0, 1]),
        ("De Ryck 2021", "CF7C60AFD9DE7", [2, 1, 1, 2, 0, 0, 2, 0]),
        ("An 2023", "C4F0B5BB85F46", [1, 1, 1, 1, 2, 1, 1, 1]),
        ("Verma 2025", "C96F294D621AC", [2, 2, 2, 0, 0, 0, 0, 0]),
        ("Varghese 2026", "CCB936E7536AC", [2, 2, 1, 0, 0, 0, 1, 1]),
        ("Tuci 2018", "C5423D5A19BA0", [0, 1, 1, 1, 2, 1, 0, 1]),
        ("Pi 2021", "C5543C6C3DDAB", [0, 0, 0, 1, 2, 2, 0, 1]),
        ("Muhammed 2026", "C1B0A43A71755", [0, 0, 0, 2, 2, 2, 0, 0]),
        ("Song 2026", "CF0BC51D9FA65", [1, 0, 1, 2, 1, 0, 1, 1]),
    ]
    close_ids = {path.name.split("_")[0] for path in (V3 / "close-read").glob("*.md")}
    missing = [cid for _, cid, _ in rows if cid not in close_ids]
    if missing:
        raise RuntimeError(f"Capability matrix contains non-close-read sources: {missing}")
    coding_columns = ["recruitment", "heterogeneity", "variable_coalition", "distributed_decision", "physical_feasibility", "hardware", "traffic", "recovery"]
    with (OUT / "capability_matrix_coding.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "label", *coding_columns])
        writer.writeheader()
        for label, candidate_id, values in rows:
            writer.writerow({"candidate_id": candidate_id, "label": label, **dict(zip(coding_columns, values))})
    matrix = np.array([values for _, _, values in rows])
    labels = [label for label, _, _ in rows]
    columns = ["Recluta", "Heterog.", "Coalición\nvariable", "Decisión\ndistrib.", "Factibilidad\nfísica", "Hardware", "Tráfico", "Recupera"]
    cmap = plt.matplotlib.colors.ListedColormap(["#F1F3F5", "#F8D9C9", "#2D6CC0"])
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.imshow(matrix, cmap=cmap, vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(np.arange(len(columns)), columns)
    ax.set_yticks(np.arange(len(labels)), labels)
    ax.tick_params(axis="x", labelsize=6.9, length=0, pad=3)
    ax.tick_params(axis="y", labelsize=7.1, length=0)
    ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, ["—", "△", "●"][matrix[i, j]], ha="center", va="center", fontsize=7.0, color="white" if matrix[i, j] == 2 else INK, weight="bold")
    ax.set_title("Matriz discriminante de capacidades · 12 fuentes con lectura cercana", loc="left", pad=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#2D6CC0", markersize=7, label="explícito"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#F8D9C9", markersize=7, label="parcial/solo alcance"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="#F1F3F5", markersize=7, label="no identificado"),
    ]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False, fontsize=6.5)
    fig.text(0.012, -0.045, "Codificación conservadora desde fichas localizadas; ‘parcial’ no equivale a implementación end-to-end. La matriz sintetiza alcance, no puntúa calidad.", fontsize=6.55, color=MUTED)
    save(fig, "fig02_capability_matrix.pdf", 0.04)


def physical_modes() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 1.55))
    titles = ["Carga soportada", "Acople rígido", "Empuje / caging", "Grasping / brazos"]
    notes = ["modo primario TFM", "contacto prehensil", "modo alternativo", "manipulación articulada"]
    colors = [BLUE, GREEN, ORANGE, PURPLE]
    for ax, title, note, color in zip(axes, titles, notes, colors):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 7)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.15, 0.2), 9.7, 6.55, boxstyle="round,pad=0.02,rounding_size=0.18", facecolor=SOFT, edgecolor=color, lw=1.0))
        ax.text(5, 6.05, title, ha="center", va="center", fontsize=7.4, weight="bold", color=color)
        ax.text(5, 0.70, note, ha="center", va="center", fontsize=6.1, color=MUTED)
    # Supported payload: platform on four robots.
    ax = axes[0]
    ax.add_patch(Rectangle((2.0, 3.4), 6.0, 1.25, facecolor="#F6C7A7", edgecolor=INK, lw=0.8))
    for x in [2.4, 7.6]:
        ax.add_patch(Circle((x, 2.65), 0.72, facecolor=BLUE, edgecolor=INK, lw=0.6))
        ax.add_patch(Circle((x, 2.65), 0.18, facecolor="white", edgecolor=INK, lw=0.4))
    # Rigid attachment: cargo and two bolted robots.
    ax = axes[1]
    ax.add_patch(Rectangle((3.15, 2.75), 3.7, 2.15, facecolor="#D9EEDB", edgecolor=INK, lw=0.8))
    for x in [1.9, 8.1]:
        ax.add_patch(Circle((x, 3.8), 0.72, facecolor=GREEN, edgecolor=INK, lw=0.6))
        ax.plot([x + (0.72 if x < 5 else -0.72), 3.15 if x < 5 else 6.85], [3.8, 3.8], color=INK, lw=1.2)
    # Pushing/caging: arrows around a free object.
    ax = axes[2]
    ax.add_patch(Circle((5, 3.75), 1.25, facecolor="#F8D9C9", edgecolor=INK, lw=0.8))
    for x, y, dx, dy in [(1.7, 3.75, 1.8, 0), (8.3, 3.75, -1.8, 0), (5, 1.65, 0, 1.15)]:
        ax.add_patch(Circle((x, y), 0.55, facecolor=ORANGE, edgecolor=INK, lw=0.55))
        ax.add_patch(FancyArrowPatch((x, y), (x + dx, y + dy), arrowstyle="-|>", mutation_scale=8, color=INK, lw=0.8))
    # Manipulators.
    ax = axes[3]
    ax.add_patch(Rectangle((3.65, 3.2), 2.7, 1.55, facecolor="#E2D5F1", edgecolor=INK, lw=0.8))
    for x, side in [(1.7, 1), (8.3, -1)]:
        ax.add_patch(Circle((x, 2.0), 0.58, facecolor=PURPLE, edgecolor=INK, lw=0.55))
        ax.plot([x, x + 1.2 * side, x + 2.0 * side], [2.35, 3.3, 3.75], color=INK, lw=1.25, marker="o", markersize=2.5)
    fig.text(0.012, -0.025, "Las modalidades comparten el objetivo de transporte, pero no la misma cinemática, modelo de contacto ni prueba de estabilidad; no deben fusionarse bajo una única garantía.", fontsize=6.55, color=MUTED)
    save(fig, "fig03_physical_modes.pdf", 0.035)


def architecture_score(row: dict[str, str]) -> float | None:
    arch = signals(row, "architecture_signals_title_abstract")
    if "centralized" in arch and "distributed_decentralized" in arch:
        return 50.0
    if "distributed_decentralized" in arch:
        return 0.0
    if "centralized" in arch:
        return 100.0
    if "hybrid" in arch:
        return 50.0
    if "leader_follower" in arch:
        return 75.0
    return None


def intersections_authority(corpus: list[dict[str, str]], metrics: dict[str, int]) -> None:
    legacy_labels = list(LEGACY["coverage"].keys())
    legacy_values = np.array(list(LEGACY["coverage"].values())) / LEGACY["corpus"] * 100
    v3_labels = ["SP1", "SP2", "SP3", "SP1∩SP2", "SP1∩SP3", "SP2∩SP3", "Triple"]
    v3_values = np.array([metrics["sp1"], metrics["sp2"], metrics["sp3"], metrics["sp12"], metrics["sp13"], metrics["sp23"], metrics["sp123"]]) / metrics["corpus"] * 100

    fig = plt.figure(figsize=(7.2, 3.72))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.18, 1], wspace=0.35)
    ax = fig.add_subplot(gs[0, 0])
    gap = 1.1
    y_old = np.arange(len(legacy_labels))
    y_new = np.arange(len(v3_labels)) + len(legacy_labels) + gap
    ax.barh(y_old, legacy_values, color=ORANGE, alpha=0.82, height=0.58, label="Legado n=59")
    ax.barh(y_new, v3_values, color=BLUE, alpha=0.88, height=0.58, label="V3 n=244")
    labels = legacy_labels + v3_labels
    ticks = list(y_old) + list(y_new)
    ax.set_yticks(ticks, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 52)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.tick_params(axis="x", length=0, labelsize=6.5)
    ax.tick_params(axis="y", length=0, labelsize=6.2)
    ax.axhline(len(legacy_labels) - 0.5 + gap / 2, color=GRID, lw=0.8)
    for y, value in zip(ticks, list(legacy_values) + list(v3_values)):
        ax.text(value + 0.7, y, f"{value:.1f}%", va="center", fontsize=6.2)
    ax.set_title("(a) Coberturas en su propio denominador", loc="left", fontsize=8.8, pad=8)
    ax.legend(frameon=False, fontsize=6.4, loc="lower right")
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax2 = fig.add_subplot(gs[0, 1])
    stage_predicates = {
        "Reclutar": lambda r, text: "SP1_coalition_allocation" in signals(r, "theme_signals_title_abstract"),
        "Certificar": lambda r, text: "SP2_physical_transport" in signals(r, "theme_signals_title_abstract") and bool(signals(r, "method_focus_title_abstract") & {"force_impedance_control", "safety_reactive", "formation_control"}),
        "Acoplar": lambda r, text: "SP2_physical_transport" in signals(r, "theme_signals_title_abstract") and any(k in text for k in ("contact", "grasp", "caging", "dock", "attach", "coupl")),
        "Transportar": lambda r, text: "SP2_physical_transport" in signals(r, "theme_signals_title_abstract"),
        "Recuperar": lambda r, text: "TRANSVERSAL_resilience_communication" in signals(r, "theme_signals_title_abstract") and any(k in text for k in ("fault", "fail", "recover", "resilien", "realloc", "replacement")),
    }
    stages = list(stage_predicates)
    means: list[float] = []
    lows: list[float] = []
    highs: list[float] = []
    ns: list[int] = []
    rng = np.random.default_rng(20260914)
    for stage, predicate in stage_predicates.items():
        values = []
        for row in corpus:
            text = (row.get("title", "") + " " + row.get("abstract_extracted", "")).lower()
            score = architecture_score(row)
            if predicate(row, text) and score is not None:
                values.append(score)
        if not values:
            means.append(float("nan")); lows.append(float("nan")); highs.append(float("nan")); ns.append(0)
            continue
        arr = np.array(values, dtype=float)
        boots = np.array([rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(2000)])
        means.append(float(arr.mean()))
        lows.append(float(np.quantile(boots, 0.025)))
        highs.append(float(np.quantile(boots, 0.975)))
        ns.append(len(values))
    y = np.arange(len(stages))
    old = [LEGACY["authority_x"][stage] for stage in stages]
    ax2.hlines(y, 0, 100, color=GRID, lw=0.6)
    ax2.scatter(old, y, s=43, facecolors="white", edgecolors=ORANGE, linewidths=1.3, label="legado ordinal", zorder=3)
    errors = np.vstack([np.array(means) - np.array(lows), np.array(highs) - np.array(means)])
    ax2.errorbar(means, y, xerr=errors, fmt="o", color=BLUE, ecolor=BLUE, elinewidth=0.8, capsize=2.2, markersize=5.0, label="V3 señal léxica", zorder=4)
    for x, yi, n in zip(means, y, ns):
        ax2.text(min(x + 3, 93), yi - 0.18, f"n={n}", fontsize=6.0, color=MUTED)
    ax2.set_yticks(y, stages)
    ax2.set_xlim(-2, 102)
    ax2.set_xticks([0, 25, 50, 75, 100], ["local", "25", "híbrida", "75", "central"])
    ax2.invert_yaxis()
    ax2.tick_params(axis="both", length=0, labelsize=6.5)
    ax2.set_title("(b) Presupuesto de autoridad por etapa", loc="left", fontsize=8.8, pad=8)
    ax2.legend(frameon=False, fontsize=6.3, loc="lower right")
    for spine in ax2.spines.values():
        spine.set_visible(False)
    fig.text(0.012, -0.025, "Panel (a): las taxonomías legado y V3 no son equivalentes y se muestran separadas. Panel (b): media e IC bootstrap del score 0=distribuido, 50=híbrido/mixto, 100=central, solo entre resúmenes con señal arquitectónica; el legado era cualitativo.", fontsize=6.4, color=MUTED)
    save(fig, "fig04_intersections_authority.pdf", 0.04)


def trends_dashboard(corpus: list[dict[str, str]]) -> None:
    periods = ["<=2010", "2011-2016", "2017-2021", "2022-2026"]
    period_labels = ["≤2010", "2011–16", "2017–21", "2022–26"]
    theme_keys = ["SP1_coalition_allocation", "SP2_physical_transport", "SP3_planning_traffic", "TRANSVERSAL_resilience_communication"]
    theme_labels = ["SP1", "SP2", "SP3", "Transversal"]
    theme_colors = [BLUE, ORANGE, GREEN, PURPLE]
    method_keys = [
        "auction_market", "consensus_distributed", "learning_based", "evolutionary_metaheuristic",
        "formation_control", "behavior_swarm", "game_theoretic", "safety_reactive",
        "exact_optimization", "model_predictive_control", "force_impedance_control", "graph_search_mapf",
    ]

    fig = plt.figure(figsize=(7.2, 5.05))
    gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.30)
    axes = [fig.add_subplot(gs[i, j]) for i in range(3) for j in range(2)]

    # (a) annual activity.
    ax = axes[0]
    years = np.arange(2000, 2027)
    counts = Counter(int(r["year"]) for r in corpus if r["year"].isdigit())
    vals = np.array([counts[y] for y in years])
    ax.bar(years, vals, color=BLUE, width=0.82)
    ax.plot(years, np.convolve(vals, np.ones(3) / 3, mode="same"), color=ORANGE, lw=1.2)
    ax.set_title("(a) Actividad anual V3", loc="left", fontsize=8.2)
    ax.set_xlim(1999.2, 2026.8)
    ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2026])
    ax.set_ylabel("documentos", fontsize=6.5)

    # (b) theme shares by period.
    ax = axes[1]
    theme_rows = read_csv("theme_period_v3.csv")
    share = {(r["category"], r["period"]): float(r["period_share"]) * 100 for r in theme_rows}
    x = np.arange(len(periods))
    for key, label, color in zip(theme_keys, theme_labels, theme_colors):
        ax.plot(x, [share[(key, p)] for p in periods], marker="o", lw=1.4, ms=3.3, color=color, label=label)
    ax.set_xticks(x, period_labels)
    ax.set_ylim(0, 60)
    ax.set_title("(b) Cuota temática por periodo", loc="left", fontsize=8.2)
    ax.set_ylabel("% del periodo", fontsize=6.5)
    ax.legend(frameon=False, fontsize=5.8, ncol=2, loc="upper right")

    # (c) architecture shares by period.
    ax = axes[2]
    arch_keys = ["distributed_decentralized", "centralized", "leader_follower", "hybrid"]
    arch_labels = ["Distribuida", "Central", "Leader--follower", "Híbrida"]
    arch_colors = [BLUE, ORANGE, GREEN, PURPLE]
    for key, label, color in zip(arch_keys, arch_labels, arch_colors):
        vals = []
        for period in periods:
            subset = [r for r in corpus if r["period"] == period]
            vals.append(sum(key in signals(r, "architecture_signals_title_abstract") for r in subset) / len(subset) * 100)
        ax.plot(x, vals, marker="o", lw=1.35, ms=3.1, color=color, label=label)
    ax.set_xticks(x, period_labels)
    ax.set_ylim(0, 60)
    ax.set_title("(c) Señal arquitectónica", loc="left", fontsize=8.2)
    ax.set_ylabel("% del periodo", fontsize=6.5)
    ax.legend(frameon=False, fontsize=5.5, ncol=2, loc="upper left")

    # (d) five-year rolling method diversity.
    ax = axes[3]
    diversity_years = np.arange(2002, 2027)
    diversity = []
    for year in diversity_years:
        subset = [r for r in corpus if r["year"].isdigit() and year - 4 <= int(r["year"]) <= year]
        counts_method = Counter()
        for row in subset:
            counts_method.update(signals(row, "method_focus_title_abstract") & set(method_keys))
        total = sum(counts_method.values())
        if total == 0:
            diversity.append(float("nan"))
        else:
            probs = np.array([value / total for value in counts_method.values()])
            diversity.append(float(-(probs * np.log(probs)).sum() / math.log(len(method_keys))))
    ax.plot(diversity_years, diversity, color=PURPLE, lw=1.7)
    ax.fill_between(diversity_years, diversity, color=PURPLE, alpha=0.12)
    ax.set_ylim(0, 1)
    ax.set_xlim(2001.5, 2026.5)
    ax.set_xticks([2002, 2008, 2014, 2020, 2026])
    ax.set_title("(d) Diversidad metodológica móvil", loc="left", fontsize=8.2)
    ax.set_ylabel("Shannon normalizado", fontsize=6.5)

    # (e) first observed signal.
    ax = axes[4]
    emergence = []
    for key in method_keys:
        available = [int(r["year"]) for r in corpus if r["year"].isdigit() and key in signals(r, "method_focus_title_abstract")]
        if available:
            emergence.append((key, min(available)))
    pretty = {
        "auction_market": "Mercados", "consensus_distributed": "Consenso", "learning_based": "Aprendizaje",
        "evolutionary_metaheuristic": "Metaheurística", "formation_control": "Formación", "behavior_swarm": "Enjambre",
        "game_theoretic": "Juegos", "safety_reactive": "CBF/seguridad", "exact_optimization": "Exacta",
        "model_predictive_control": "MPC", "force_impedance_control": "Fuerza/imp.", "graph_search_mapf": "MAPF",
    }
    emergence.sort(key=lambda item: item[1])
    emergence = emergence[-8:]
    labels = [pretty[k] for k, _ in emergence]
    values = [v for _, v in emergence]
    y = np.arange(len(labels))
    ax.hlines(y, 1979, values, color=GRID, lw=1.0)
    ax.scatter(values, y, color=GREEN, s=18)
    ax.set_yticks(y, labels)
    ax.set_xlim(1978, 2027)
    ax.set_xticks([1980, 1995, 2010, 2026])
    ax.set_title("(e) Primera señal observada", loc="left", fontsize=8.2)

    # (f) recurring venues.
    ax = axes[5]
    venues = read_csv("top_venues_v3.csv")[:7]
    venue_labels = [r["venue"].replace("Journal of Intelligent & Robotic Systems", "JINT").replace("Lecture Notes in Computer Science", "LNCS").replace("Frontiers in Robotics and AI", "Frontiers RAI") for r in venues][::-1]
    venue_values = [int(r["paper_count"]) for r in venues][::-1]
    y = np.arange(len(venue_labels))
    ax.barh(y, venue_values, color=TEAL, height=0.58)
    ax.set_yticks(y, venue_labels)
    ax.set_xlim(0, 26)
    for yi, value in zip(y, venue_values):
        ax.text(value + 0.5, yi, str(value), va="center", fontsize=6.2)
    ax.set_title("(f) Venues recurrentes", loc="left", fontsize=8.2)

    for ax in axes:
        ax.grid(axis="y" if ax is axes[0] else "x", color=GRID, lw=0.45)
        ax.tick_params(axis="both", length=0, labelsize=6.0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Dashboard temporal y estructural · 243 documentos fechados de 244", x=0.012, y=1.02, ha="left", fontsize=9.6, weight="bold")
    fig.text(0.012, -0.025, "Estructura visual restaurada. El corte legado informaba n=54 fechados, pero su tabla anual no fue entregada: no se dibuja una curva histórica ficticia. Paneles (b)--(d) son multietiqueta; 2026 está incompleto.", fontsize=6.45, color=MUTED)
    save(fig, "fig05_trends_dashboard.pdf", 0.04)


def write_manifest(metrics: dict[str, int]) -> None:
    manifest = {
        "script": "academic-review/scripts/build_v3_compact_review_6p.py",
        "v3_inputs": sorted(path.name for path in DATA.glob("*_v3.csv")),
        "legacy_source": "C:/Users/walla/Downloads/academic_literature_review (1).tex",
        "legacy_scope": "Only values explicitly printed in the supplied TeX; no missing annual series was reconstructed.",
        "outputs": [
            "compact_metrics.tex",
            "legacy_snapshot_values.csv",
            "capability_matrix_coding.csv",
            "figures/fig01_methodological_map.pdf",
            "figures/fig01b_snapshot_summary.pdf",
            "figures/fig02_capability_matrix.pdf",
            "figures/fig03_physical_modes.pdf",
            "figures/fig04_intersections_authority.pdf",
            "figures/fig05_trends_dashboard.pdf",
            "figures/fig06_method_evolution.pdf",
            "figures/fig07_interfaces_evidence.pdf",
        ],
        "metrics": metrics,
        "interpretation_rule": "V3 corpus-level panels are title/abstract signals; capability claims require close-read evidence cards.",
    }
    (OUT / "build_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    base.OUT = OUT
    base.FIGURES = FIGURES
    base.setup_style()
    metrics = base.collect_metrics()
    base.write_metrics(metrics)
    freeze_legacy_values()
    corpus = read_csv("analytic_corpus_v3.csv")
    methodological_map(corpus)
    snapshot_summary(metrics, corpus)
    capability_matrix(corpus)
    physical_modes()
    intersections_authority(corpus, metrics)
    trends_dashboard(corpus)
    base.method_evolution()
    (FIGURES / "fig02_method_evolution.pdf").replace(FIGURES / "fig06_method_evolution.pdf")
    base.interface_and_evidence(metrics)
    (FIGURES / "fig03_interfaces_evidence.pdf").replace(FIGURES / "fig07_interfaces_evidence.pdf")
    write_manifest(metrics)
    print(json.dumps({"metrics": metrics, "legacy": LEGACY, "output": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
