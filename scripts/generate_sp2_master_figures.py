"""Generate the SP2 master figures and evidence table from archived results.

The script is intentionally post-processing only: it never simulates new worlds and
never reconstructs robot poses that were not stored by the Cargo campaign.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd



def _spanish_decimals(fig) -> None:
    """Sustituye el punto decimal por coma en todo el texto de la figura.

    Se ejecuta con el dibujo ya resuelto, de modo que las marcas automaticas de
    matplotlib ya tienen su texto definitivo. El documento esta en castellano y
    el separador decimal es la coma, tambien en los ejes.
    """

    import re as _re

    between_digits = _re.compile(r"(?<=\d)\.(?=\d)")
    identifier = _re.compile(r"[A-Za-z]\w*\.\d")

    def fix(text):
        if not text or "." not in text or identifier.search(text):
            return text
        return between_digits.sub(",", text)

    fig.canvas.draw()
    for ax in fig.get_axes():
        for axis in (ax.xaxis, ax.yaxis):
            labels = [t.get_text() for t in axis.get_ticklabels()]
            if any(fix(t) != t for t in labels):
                axis.set_ticks(axis.get_ticklocs())
                axis.set_ticklabels([fix(t) for t in labels])
        for loc in ("left", "center", "right"):
            current = ax.get_title(loc=loc)
            if current:
                ax.set_title(fix(current), loc=loc)
        ax.set_xlabel(fix(ax.get_xlabel()))
        ax.set_ylabel(fix(ax.get_ylabel()))
        for text in list(ax.texts):
            text.set_text(fix(text.get_text()))
        legend = ax.get_legend()
        if legend is not None:
            for item in legend.get_texts():
                item.set_text(fix(item.get_text()))
    for text in list(fig.texts):
        text.set_text(fix(text.get_text()))


INK = "#172033"
MUTED = "#5f6b7a"
GRID = "#d8dee8"
BLUE = "#2166ac"
ORANGE = "#d97706"
GREEN = "#16836b"
RED = "#c43d4b"
PURPLE = "#7251b5"
PALE = "#f6f8fb"
PDF_METADATA = {
    "Creator": "VIU-MRBO-TFM-2026 SP2 post-processing",
    "CreationDate": None,
    "ModDate": None,
}

METHOD_ORDER = ["pd", "pid", "lqr", "lqi", "port_hamiltonian", "mpc_central"]
METHOD_SHORT = {
    "pd": "PD",
    "pid": "PID",
    "lqr": "LQR",
    "lqi": "LQI",
    "port_hamiltonian": "Amort.",
    "mpc_central": "MPC",
}
SCENARIO_ORDER = [f"S{i}" for i in range(7)]

CARGO_METHOD_ORDER = [
    "distributed_full",
    "perfect_information",
    "decoupled_local",
    "no_physical_guard",
    "no_repair",
    "central_reference",
]
CARGO_METHOD_SHORT = {
    "distributed_full": "Vecinal completo",
    "perfect_information": "Info. perfecta",
    "decoupled_local": "Sin acop. espacial",
    "no_physical_guard": "Sin guarda física",
    "no_repair": "Sin reparación",
    "central_reference": "Ref. central",
}
CARGO_SCENARIO_ORDER = [
    "open_nominal",
    "static_obstacle",
    "degraded_network",
    "failure_during_transport",
]
CARGO_SCENARIO_SHORT = {
    "open_nominal": "Nominal",
    "static_obstacle": "Obstáculo",
    "degraded_network": "Red degrad.",
    "failure_during_transport": "Fallo",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _panel_title(axis: plt.Axes, letter: str, title: str) -> None:
    axis.set_title(f"{letter}  {title}", loc="left", color=INK, fontweight="bold", pad=7)


def _finish_axis(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(colors=INK)
    axis.xaxis.label.set_color(INK)
    axis.yaxis.label.set_color(INK)


def _annotated_heatmap(
    axis: plt.Axes,
    values: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    *,
    fmt: str = ".2f",
    cmap: str | colors.Colormap = "viridis",
    vmin: float = 0.0,
    vmax: float = 1.0,
    fontsize: float = 8.2,
) -> matplotlib.image.AxesImage:
    image = axis.imshow(values, aspect="auto", vmin=vmin, vmax=vmax, cmap=cmap)
    axis.set_xticks(np.arange(len(col_labels)), col_labels)
    axis.set_yticks(np.arange(len(row_labels)), row_labels)
    axis.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    axis.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=1.05)
    axis.tick_params(which="minor", bottom=False, left=False)
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = float(values[row, col])
            text = format(value, fmt)
            axis.text(
                col,
                row,
                text,
                ha="center",
                va="center",
                fontsize=fontsize,
                fontweight="semibold",
                color="white" if value < 0.53 else INK,
            )
    return image


def _figure_n1_n2(n1: pd.DataFrame, n2: pd.DataFrame, output: Path) -> dict[str, float]:
    false_accepts = int(((n1["naive_feasible"] == 1) & (n1["feasible"] == 0)).sum())
    total_n1 = int(len(n1))
    if total_n1 != 36_600 or false_accepts != 4_536:
        raise ValueError(f"Unexpected N1 archive: rows={total_n1}, false accepts={false_accepts}")
    if len(n2) != 720:
        raise ValueError(f"Unexpected N2 archive: rows={len(n2)}")

    per_seed = (
        n1.assign(feasible_omega=n1["omega_rad_s"].where(n1["feasible"] == 1))
        .groupby(["seed", "radius_m", "speed_mps"], as_index=False)["feasible_omega"]
        .max()
        .fillna({"feasible_omega": 0.0})
    )

    plt.rcParams.update({"font.size": 9.4, "axes.titlesize": 10.2, "axes.labelsize": 9.4})
    fig = plt.figure(figsize=(7.35, 7.65), layout="constrained")
    grid = fig.add_gridspec(3, 2, height_ratios=(1.35, 1.12, 1.02), width_ratios=(1.75, 1.0))

    # A — kinematic envelope.
    ax_a = fig.add_subplot(grid[0, 0])
    radii = sorted(per_seed["radius_m"].unique())
    palette = plt.cm.viridis(np.linspace(0.10, 0.88, len(radii)))
    for radius, color in zip(radii, palette, strict=True):
        subset = per_seed[per_seed["radius_m"] == radius]
        summary = (
            subset.groupby("speed_mps")["feasible_omega"]
            .agg(
                median="median",
                q05=lambda value: float(np.quantile(value, 0.05)),
                q95=lambda value: float(np.quantile(value, 0.95)),
            )
            .reset_index()
        )
        speed = summary["speed_mps"].to_numpy(float)
        ax_a.plot(speed, summary["median"], marker="o", markersize=3.2, linewidth=1.55, color=color, label=f"{radius:.1f}")
        ax_a.fill_between(speed, summary["q05"], summary["q95"], color=color, alpha=0.13)
    _panel_title(ax_a, "A", "Envolvente cinemática N1")
    ax_a.set(xlabel="velocidad longitudinal [m/s]", ylabel=r"$\omega_{\max}$ factible [rad/s]")
    ax_a.grid(alpha=0.23)
    ax_a.legend(title="radio R [m]", frameon=False, ncol=3, fontsize=8.1, title_fontsize=8.4, loc="upper right")
    ax_a.text(0.01, 0.02, "mediana y P5–P95 · 30 semillas", transform=ax_a.transAxes, fontsize=8.0, color=MUTED)
    _finish_axis(ax_a)

    # B — false-positive funnel without a decorative Sankey.
    ax_b = fig.add_subplot(grid[0, 1])
    ax_b.set_xlim(0, 1)
    ax_b.set_ylim(0, 1)
    ax_b.axis("off")
    _panel_title(ax_b, "B", "Falsa aceptación N1")
    cards = [
        (0.10, 0.57, 0.80, 0.25, BLUE, f"{total_n1:,}".replace(",", " "), "órdenes evaluadas"),
        (0.18, 0.17, 0.64, 0.25, RED, f"{false_accepts:,}".replace(",", " "), "aceptadas por el criterio simple\ny rechazadas por N1"),
    ]
    for x, y, width, height, color, number, label in cards:
        ax_b.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.02,rounding_size=0.03", facecolor=f"{color}12", edgecolor=color, linewidth=1.4))
        ax_b.text(x + width / 2, y + height * 0.64, number, ha="center", va="center", fontsize=16, color=color, fontweight="bold")
        ax_b.text(x + width / 2, y + height * 0.25, label, ha="center", va="center", fontsize=8.5, color=INK)
    ax_b.annotate("", xy=(0.5, 0.44), xytext=(0.5, 0.55), arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.2})
    ax_b.text(0.5, 0.04, f"{100 * false_accepts / total_n1:.1f}% del barrido", ha="center", fontsize=10.2, fontweight="bold", color=RED)

    # C — three nested mechanical models.
    nested_outer = grid[1, :].subgridspec(2, 1, height_ratios=(0.13, 0.87), hspace=0.02)
    holder = fig.add_subplot(nested_outer[0, 0])
    holder.axis("off")
    holder.text(0, 0.55, "C  Escalera mecánica N2 · misma cuadrícula", transform=holder.transAxes, color=INK, fontweight="bold", fontsize=10.2, va="center")
    nested = nested_outer[1, 0].subgridspec(1, 3, wspace=0.12)
    n2_grouped = n2.groupby(["dispersion_m", "pressure"])[["scalar_feasible", "bilateral_feasible", "supported_feasible"]].mean().reset_index()
    mechanical = [
        ("scalar_feasible", "Capacidad escalar"),
        ("bilateral_feasible", "LP bilateral"),
        ("supported_feasible", "Soporte + fricción"),
    ]
    for index, (column, label) in enumerate(mechanical):
        axis = fig.add_subplot(nested[0, index])
        pivot = n2_grouped.pivot(index="pressure", columns="dispersion_m", values=column)
        accepted = int(n2[column].sum())
        _annotated_heatmap(
            axis,
            pivot.to_numpy(),
            [f"{value:.1f}" for value in pivot.index],
            [f"{value:.1f}" for value in pivot.columns],
            fmt=".0%",
            fontsize=6.9,
        )
        axis.set_title(f"{label}\n{accepted}/720 aceptadas", fontsize=9.0, color=INK, pad=3)
        axis.set_xlabel("dispersión d [m]", fontsize=8.2)
        if index == 0:
            axis.set_ylabel(r"demanda $\pi^{N2}$", fontsize=8.2)
        else:
            axis.set_yticklabels([])
        axis.tick_params(labelsize=7.6)

    # D — direct summaries of the two geometry sweeps.
    ax_d = fig.add_subplot(grid[2, :])
    common_scale = [0.2, 0.4, 0.6, 0.8]
    n1_fraction = n1[n1["radius_m"].isin(common_scale)].groupby("radius_m")["feasible"].mean().reindex(common_scale)
    n2_fraction = n2[n2["dispersion_m"].isin(common_scale)].groupby("dispersion_m")["supported_feasible"].mean().reindex(common_scale)
    ax_d.plot(common_scale, n1_fraction, marker="o", linewidth=2.0, color=BLUE, label="N1 · órdenes cinemáticamente factibles")
    ax_d.plot(common_scale, n2_fraction, marker="s", linewidth=2.0, color=ORANGE, label="N2 · demandas factibles con soporte")
    _panel_title(ax_d, "D", "La geometría ayuda y limita por vías distintas")
    ax_d.set(xlabel="escala geométrica [m] · R en N1; d en N2", ylabel="fracción factible del barrido", ylim=(0, 1.04), xticks=common_scale)
    ax_d.grid(alpha=0.23)
    ax_d.legend(frameon=False, fontsize=8.6, ncol=2, loc="lower center")
    ax_d.text(0.99, 0.96, "dos barridos distintos; lectura conjunta, no efecto causal", transform=ax_d.transAxes, ha="right", va="top", fontsize=7.8, color=MUTED)
    _finish_axis(ax_d)

    _spanish_decimals(fig)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.035, dpi=300, metadata=PDF_METADATA)
    plt.close(fig)
    return {
        "n1_rows": total_n1,
        "n1_false_accepts": false_accepts,
        "n1_false_acceptance_rate": false_accepts / total_n1,
        "n2_rows": int(len(n2)),
        "n2_supported_accepts": int(n2["supported_feasible"].sum()),
    }


def _dominant_failure(n4: pd.DataFrame) -> tuple[np.ndarray, list[list[str]]]:
    governed = n4[n4["mode"] == "governed"]
    code = {
        "timeout": "TO",
        "communication_timeout": "COM",
        "governor_limited_timeout": "GOV",
        "barrier_limited_timeout": "BAR",
        "stale_information_braking": "AGE",
        "uncontrolled_stop_required": "AUT",
        "support_unavailable": "SUP",
        "collision": "COL",
        "kinematic_limit": "KIN",
        "wrench_limit": "W",
        "numerical_failure": "NUM",
    }
    categories = list(code)
    dominant = np.zeros((len(METHOD_ORDER), len(SCENARIO_ORDER)), dtype=float)
    annotations: list[list[str]] = []
    for row, method in enumerate(METHOD_ORDER):
        labels: list[str] = []
        for col, scenario in enumerate(SCENARIO_ORDER):
            cell = governed[(governed["method"] == method) & (governed["scenario"] == scenario)]
            failures = cell.loc[cell["failure_mode"] != "none", "failure_mode"]
            if failures.empty:
                labels.append("—")
                continue
            counts = failures.value_counts()
            category = str(counts.index[0])
            dominant[row, col] = categories.index(category) + 1
            labels.append(f"{code[category]}\n{counts.iloc[0] / len(cell):.0%}")
        annotations.append(labels)
    return dominant, annotations


def _forest(axis: plt.Axes, paired: pd.DataFrame, endpoint: pd.DataFrame, metric: str) -> None:
    paired_order = ["pd", "lqi", "port_hamiltonian", "mpc_central"]
    indexed = paired.assign(method=paired["comparison"].str.split(":").str[0]).set_index("method").reindex(paired_order)
    if metric == "success":
        value_col, low_col, high_col = "success_risk_difference", "success_difference_ci95_low", "success_difference_ci95_high"
        title, color = "Δ éxito · positivo favorece", BLUE
    else:
        value_col, low_col, high_col = "collision_risk_difference", "collision_difference_ci95_low", "collision_difference_ci95_high"
        title, color = "Δ colisión · positivo perjudica", ORANGE
    values = indexed[value_col].to_numpy(float)
    lows = indexed[low_col].to_numpy(float)
    highs = indexed[high_col].to_numpy(float)
    labels = [METHOD_SHORT[item] for item in paired_order]
    if metric == "collision":
        aggregate = endpoint.set_index("endpoint").loc["collision"]
        values = np.append(values, float(aggregate["difference_governed_minus_raw"]))
        lows = np.append(lows, float(aggregate["difference_ci95_low"]))
        highs = np.append(highs, float(aggregate["difference_ci95_high"]))
        labels.append("Agregado H6")
    y = np.arange(len(values))
    axis.errorbar(values, y, xerr=np.vstack([values - lows, highs - values]), fmt="o", color=color, ecolor=color, capsize=3, linewidth=1.15)
    if metric == "collision":
        axis.plot(values[-1], y[-1], marker="D", color=INK, markersize=5)
    axis.axvline(0, color=INK, linewidth=0.9)
    axis.set_yticks(y, labels)
    axis.invert_yaxis()
    axis.set_xlabel("guarda − crudo")
    axis.set_title(title, fontsize=9.2, color=INK)
    axis.grid(axis="x", alpha=0.22)
    _finish_axis(axis)


def _figure_n4(n4: pd.DataFrame, paired: pd.DataFrame, endpoint: pd.DataFrame, output: Path) -> dict[str, float]:
    if len(n4) != 2_100:
        raise ValueError(f"Unexpected N4 archive: rows={len(n4)}")
    governed = n4[n4["mode"] == "governed"]
    pivot = governed.pivot_table(index="method", columns="scenario", values="success", aggfunc="mean").reindex(index=METHOD_ORDER, columns=SCENARIO_ORDER)

    plt.rcParams.update({"font.size": 9.1, "axes.titlesize": 10.0, "axes.labelsize": 9.0})
    fig = plt.figure(figsize=(7.35, 7.85), layout="constrained")
    grid = fig.add_gridspec(3, 2, height_ratios=(1.18, 1.05, 0.66), hspace=0.13)

    ax_a = fig.add_subplot(grid[0, 0])
    _annotated_heatmap(ax_a, pivot.to_numpy(), [METHOD_SHORT[item] for item in METHOD_ORDER], SCENARIO_ORDER, fontsize=7.9)
    _panel_title(ax_a, "A", "Éxito con guarda")
    ax_a.set_xlabel("escenario · 30 mundos por celda")

    ax_b = fig.add_subplot(grid[0, 1])
    dominant, annotations = _dominant_failure(n4)
    failure_colors = [PALE, "#aab2bd", "#79a7d8", "#e5a84b", "#a58ad7", "#55aa8b", "#d45b73", "#cb4b48", "#384152", "#26857b", "#b36b33", "#a95588"]
    ax_b.imshow(dominant, vmin=0, vmax=len(failure_colors) - 1, cmap=colors.ListedColormap(failure_colors), aspect="auto")
    ax_b.set_xticks(np.arange(7), SCENARIO_ORDER)
    ax_b.set_yticks(np.arange(6), [METHOD_SHORT[item] for item in METHOD_ORDER])
    ax_b.set_xticks(np.arange(-0.5, 7, 1), minor=True)
    ax_b.set_yticks(np.arange(-0.5, 6, 1), minor=True)
    ax_b.grid(which="minor", color="white", linewidth=1.05)
    ax_b.tick_params(which="minor", bottom=False, left=False)
    for row, values in enumerate(annotations):
        for col, value in enumerate(values):
            ax_b.text(col, row, value, ha="center", va="center", fontsize=7.4, fontweight="semibold", color="white" if value.startswith(("AUT", "COL", "SUP")) else INK)
    _panel_title(ax_b, "B", "Terminal dominante")
    ax_b.set_xlabel("AGE: edad · KIN: ruedas · SUP: soporte · COL: col.")

    nested_outer = grid[1, :].subgridspec(2, 1, height_ratios=(0.13, 0.87), hspace=0.02)
    holder = fig.add_subplot(nested_outer[0, 0])
    holder.axis("off")
    holder.text(0, 0.55, "C  Efecto pareado de la guarda · IC 95%, 30 bloques de semilla", transform=holder.transAxes, color=INK, fontweight="bold", fontsize=10.0, va="center")
    nested = nested_outer[1, 0].subgridspec(1, 2, wspace=0.34)
    _forest(fig.add_subplot(nested[0, 0]), paired, endpoint, "success")
    _forest(fig.add_subplot(nested[0, 1]), paired, endpoint, "collision")

    holder_d = fig.add_subplot(grid[2, :])
    holder_d.axis("off")
    _panel_title(holder_d, "D", "Admisibilidad realizada · cuatro leyes pareadas")
    endpoints = endpoint.set_index("endpoint")
    metrics = [
        ("realized_violation_fraction", "fracción temporal fuera del modelo", 1.0, ""),
        ("realized_violation_max_duration_s", "episodio continuo más largo", 4.0, " s"),
    ]
    for index, (metric, label, maximum, suffix) in enumerate(metrics):
        row = endpoints.loc[metric]
        x0 = 0.05 + index * 0.52
        width = 0.36
        holder_d.text(x0, 0.66, label, transform=holder_d.transAxes, fontsize=8.8, color=INK, fontweight="semibold")
        raw = float(row["raw_mean"])
        governed_value = float(row["governed_mean"])
        for offset, value, color, name in [(0.36, raw, RED, "crudo"), (0.14, governed_value, GREEN, "guarda")]:
            holder_d.add_patch(Rectangle((x0, offset), width, 0.12, transform=holder_d.transAxes, facecolor=PALE, edgecolor=GRID, linewidth=0.6))
            holder_d.add_patch(Rectangle((x0, offset), width * value / maximum, 0.12, transform=holder_d.transAxes, facecolor=color, edgecolor="none"))
            holder_d.text(x0 - 0.008, offset + 0.06, name, transform=holder_d.transAxes, ha="right", va="center", fontsize=7.8, color=MUTED)
            holder_d.text(x0 + width + 0.008, offset + 0.06, f"{value:.3f}{suffix}", transform=holder_d.transAxes, ha="left", va="center", fontsize=8.4, color=color, fontweight="bold")
        holder_d.annotate("", xy=(x0 + 0.28, 0.20), xytext=(x0 + 0.28, 0.38), xycoords=holder_d.transAxes, arrowprops={"arrowstyle": "-|>", "color": GREEN, "lw": 1.0})

    _spanish_decimals(fig)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.035, dpi=300, metadata=PDF_METADATA)
    plt.close(fig)
    return {
        "n4_rows": int(len(n4)),
        "n4_worlds": int(n4[["scenario", "seed"]].drop_duplicates().shape[0]),
        "n4_seed_blocks": int(n4["seed"].nunique()),
        "paired_success_difference": float(endpoints.loc["success", "difference_governed_minus_raw"]),
        "paired_collision_difference": float(endpoints.loc["collision", "difference_governed_minus_raw"]),
    }


def _load_rectangle(axis: plt.Axes, pose: np.ndarray, *, color: str, alpha: float, label: str | None = None) -> None:
    x, y, theta = [float(value) for value in pose]
    width, height = 0.76, 0.48
    corners = np.array([[-width / 2, -height / 2], [width / 2, -height / 2], [width / 2, height / 2], [-width / 2, height / 2]])
    rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    rotated = corners @ rotation.T + np.array([x, y])
    patch = plt.Polygon(rotated, facecolor=color, edgecolor=color, alpha=alpha, linewidth=1.0, label=label)
    axis.add_patch(patch)


def _draw_phase_lane(axis: plt.Axes, y: float, phases: list[str], colors_: list[str], note: str) -> None:
    start, end = 0.02, 0.98
    gap = 0.018
    width = (end - start - gap * (len(phases) - 1)) / len(phases)
    for index, (phase, color) in enumerate(zip(phases, colors_, strict=True)):
        x = start + index * (width + gap)
        axis.add_patch(FancyBboxPatch((x, y), width, 0.20, boxstyle="round,pad=0.008,rounding_size=0.012", transform=axis.transAxes, facecolor=f"{color}18", edgecolor=color, linewidth=1.0))
        axis.text(x + width / 2, y + 0.10, phase, transform=axis.transAxes, ha="center", va="center", fontsize=7.2, fontweight="bold", color=INK)
        if index < len(phases) - 1:
            axis.annotate("", xy=(x + width + gap * 0.86, y + 0.10), xytext=(x + width + gap * 0.14, y + 0.10), xycoords=axis.transAxes, arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 0.8})
    axis.text(start, y - 0.055, note, transform=axis.transAxes, ha="left", va="top", fontsize=8.2, color=MUTED)


def _figure_cargo(cargo: pd.DataFrame, trace: np.ndarray, output: Path) -> dict[str, float]:
    worlds = int(cargo[["world_hash"]].drop_duplicates().shape[0])
    if worlds != 360 or len(cargo) != 2_160:
        raise ValueError(f"Unexpected Cargo archive: worlds={worlds}, rows={len(cargo)}")
    full = cargo[cargo["method"] == "distributed_full"]
    full_success = int(full["mission_success"].sum())
    failure = full[full["scenario"] == "failure_during_transport"]
    failure_success = int(failure["mission_success"].sum())

    plt.rcParams.update({"font.size": 9.2, "axes.titlesize": 10.0, "axes.labelsize": 9.0})
    fig = plt.figure(figsize=(7.35, 6.05))
    fig.subplots_adjust(left=0.17, right=0.98, top=0.95, bottom=0.12, hspace=0.36, wspace=0.43)
    grid = fig.add_gridspec(2, 2, height_ratios=(0.76, 1.12), width_ratios=(1.05, 1.15))

    # A — the only stored physical trace: load pose in a representative nominal world.
    ax_a = fig.add_subplot(grid[0, 0])
    ax_a.plot(trace[:, 0], trace[:, 1], color=BLUE, linewidth=2.2, zorder=1)
    snapshot_indices = np.linspace(0, len(trace) - 1, 4, dtype=int)
    snapshot_colors = [MUTED, "#5d85bd", "#4b9d90", GREEN]
    for number, (index, color) in enumerate(zip(snapshot_indices, snapshot_colors, strict=True)):
        _load_rectangle(ax_a, trace[index], color=color, alpha=0.22 if number not in (0, 3) else 0.34)
        ax_a.text(trace[index, 0], trace[index, 1] + 0.37, f"t{number}", ha="center", fontsize=9.2, color=color, fontweight="bold")
    ax_a.scatter(trace[0, 0], trace[0, 1], color=MUTED, marker="o", s=22, zorder=3)
    ax_a.scatter(trace[-1, 0], trace[-1, 1], color=GREEN, marker="*", s=75, zorder=3)
    _panel_title(ax_a, "A", "Trayectoria de carga registrada")
    ax_a.set(xlabel="x [m]", ylabel="y [m]")
    ax_a.set_xlim(float(trace[:, 0].min()) - 0.45, float(trace[:, 0].max()) + 0.45)
    ax_a.set_ylim(-1.05, 1.05)
    ax_a.set_aspect("equal", adjustable="box")
    ax_a.grid(alpha=0.22)
    _finish_axis(ax_a)

    # B — exact categorical traces; deliberately not drawn against a time axis.
    ax_b = fig.add_subplot(grid[0, 1])
    ax_b.axis("off")
    _panel_title(ax_b, "B", "Fases observadas")
    _draw_phase_lane(ax_b, 0.57, ["RECL.", "DOCK", "TRANS.", "META"], [BLUE, BLUE, GREEN, GREEN], "270/270 mundos sin fallo · vecinal completo")
    _draw_phase_lane(ax_b, 0.21, ["FALLO", "RECUP.", "REAN.", "META"], [RED, ORANGE, GREEN, GREEN], f"{failure_success}/90 sustituciones llegan; 1 falla en RECUPERAR")

    # C — architecture ablation.
    ax_c = fig.add_subplot(grid[1, :])
    matrix = cargo.pivot_table(index="method", columns="scenario", values="mission_success", aggfunc="mean").reindex(index=CARGO_METHOD_ORDER, columns=CARGO_SCENARIO_ORDER)
    _annotated_heatmap(
        ax_c,
        matrix.to_numpy(),
        [CARGO_METHOD_SHORT[item] for item in CARGO_METHOD_ORDER],
        [CARGO_SCENARIO_SHORT[item] for item in CARGO_SCENARIO_ORDER],
        fontsize=8.8,
    )
    _panel_title(ax_c, "C", "Misión por tratamiento y régimen · 90 mundos por celda")
    ax_c.set_xlabel("éxito de misión")
    ax_c.text(0.99, -0.24, f"Vecinal completo: {full_success}/360 · fallo y sustitución: {failure_success}/90", transform=ax_c.transAxes, ha="right", fontsize=9.0, color=GREEN, fontweight="bold")

    _spanish_decimals(fig)
    fig.savefig(output, bbox_inches="tight", pad_inches=0.035, dpi=300, metadata=PDF_METADATA)
    plt.close(fig)
    return {
        "cargo_worlds": worlds,
        "cargo_runs": int(len(cargo)),
        "cargo_distributed_success": full_success,
        "cargo_failure_success": failure_success,
        "cargo_docking_success": int(full["docking_success"].sum()),
    }


def _latex_decimal(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", "{,}")


def _latex_integer(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _write_evidence_table(
    path: Path,
    n1: pd.DataFrame,
    n2: pd.DataFrame,
    n3: pd.DataFrame,
    n3_stats: pd.DataFrame,
    n4: pd.DataFrame,
    endpoint: pd.DataFrame,
    cargo: pd.DataFrame,
) -> None:
    n3_degraded = n3_stats.set_index("network").loc["degraded"]
    endpoints = endpoint.set_index("endpoint")
    full = cargo[cargo["method"] == "distributed_full"]
    failure = full[full["scenario"] == "failure_during_transport"]
    content = rf"""\begin{{tabularx}}{{\textwidth}}{{p{{0.90cm}} p{{2.45cm}} p{{5.20cm}} X}}
\toprule
Nivel & Unidad y tamaño & Resultado observado & Alcance acreditado \\
\midrule
N1 & {_latex_integer(len(n1))} órdenes & {_latex_integer(int(((n1['naive_feasible'] == 1) & (n1['feasible'] == 0)).sum()))} falsos positivos del criterio simple (12{{,}}4\,\%) & Cinemática de pivote y ruedas; sin par ni contacto \\
N2 & {len(n2)} demandas & {int(n2['supported_feasible'].sum())}/{len(n2)} factibles con soporte y fricción & Sustituto 2.5D con contactos fijos \\
N3 & {len(n3)} ejecuciones; 30 semillas & En red degradada, $\Delta\mathrm{{RMSE}}={_latex_decimal(float(n3_degraded['difference_virtual_minus_leader_rmse_position_m']))}$ m, IC [{_latex_decimal(float(n3_degraded['difference_ci95_low_rmse_position_m']))}; {_latex_decimal(float(n3_degraded['difference_ci95_high_rmse_position_m']))}] & Cuatro AMR en anillo; canal abstracto, no SLAM ejecutado \\
N4 & {n4[['scenario', 'seed']].drop_duplicates().shape[0]} mundos; 30 bloques & Guarda: $\Delta P_{{\rm éxito}}=+{_latex_decimal(float(endpoints.loc['success', 'difference_governed_minus_raw']))}$; $\Delta P_{{\rm col}}=+{_latex_decimal(float(endpoints.loc['collision', 'difference_governed_minus_raw']))}$ & Planta reducida; H6 de colisión refutada \\
Cargo & {cargo[['world_hash']].drop_duplicates().shape[0]} mundos; {_latex_integer(len(cargo))} ejecuciones & Vecinal completo {int(full['mission_success'].sum())}/360; sustitución {int(failure['mission_success'].sum())}/90 & Hasta pose de entrega; arquitectura híbrida y acoplamiento posicional \\
Caging & verificador $21\!\times\!21$ & Cierre o ruta de escape por BFS de cuatro vecinos & Certificado geométrico traslacional; sin orientación, fuerza ni dinámica \\
\bottomrule
\end{{tabularx}}
"""
    path.write_text(content, encoding="utf-8")


def generate(repository_root: Path, output_dir: Path, generated_dir: Path) -> dict[str, object]:
    # Archived campaign data: moved to legacy/ in the 2026-09-02 repository cleanup.
    archive = repository_root / "legacy" / "results"
    sp2 = archive / "sp2_canonical" / "SP2_HONORS_v3"
    cargo_dir = archive / "processed" / "integrated" / "CARGO_E2E_CONFIRMATORY_v1"
    inputs = {
        "n1": sp2 / "raw" / "n1_kinematic_grid.csv",
        "n2": sp2 / "raw" / "n2_mechanical_grid.csv",
        "n3": sp2 / "raw" / "n3_network_runs.csv",
        "n3_stats": sp2 / "processed" / "n3_architecture_statistics.csv",
        "n4": sp2 / "raw" / "n4_runs.csv",
        "paired": sp2 / "processed" / "paired_governor_statistics.csv",
        "endpoints": sp2 / "processed" / "paired_endpoint_statistics.csv",
        "cargo": cargo_dir / "tables" / "runs.csv",
        "cargo_trace": cargo_dir / "traces" / "representative_trace.npz",
    }
    missing = [str(path) for path in inputs.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing SP2 inputs: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    n1 = pd.read_csv(inputs["n1"])
    n2 = pd.read_csv(inputs["n2"])
    n3 = pd.read_csv(inputs["n3"])
    n3_stats = pd.read_csv(inputs["n3_stats"])
    n4 = pd.read_csv(inputs["n4"])
    paired = pd.read_csv(inputs["paired"])
    endpoint = pd.read_csv(inputs["endpoints"])
    cargo = pd.read_csv(inputs["cargo"])
    with np.load(inputs["cargo_trace"]) as archive:
        trace = archive["load_pose"]

    outputs = {
        "n1_n2": output_dir / "fig-sp2-master-n1-n2.pdf",
        "n4": output_dir / "fig-sp2-master-n4.pdf",
        "cargo": output_dir / "fig-sp2-master-cargo.pdf",
        "table": generated_dir / "sp2_evidence_summary.tex",
    }
    metrics: dict[str, float] = {}
    metrics.update(_figure_n1_n2(n1, n2, outputs["n1_n2"]))
    metrics.update(_figure_n4(n4, paired, endpoint, outputs["n4"]))
    metrics.update(_figure_cargo(cargo, trace, outputs["cargo"]))
    _write_evidence_table(outputs["table"], n1, n2, n3, n3_stats, n4, endpoint, cargo)

    manifest = {
        "generator": str(Path(__file__).resolve()),
        "scope": "post-processing only; no new simulations",
        "cargo_trace_limit": "load_pose only; robot poses and phase timestamps were not archived",
        "inputs": {name: {"path": str(path), "sha256": _sha256(path)} for name, path in inputs.items()},
        "outputs": {name: {"path": str(path), "sha256": _sha256(path)} for name, path in outputs.items()},
        "metrics": metrics,
    }
    manifest_path = generated_dir / "sp2_master_figures_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--generated-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = generate(args.repo_root.resolve(), args.output_dir.resolve(), args.generated_dir.resolve())
    print(json.dumps({"outputs": manifest["outputs"], "metrics": manifest["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
