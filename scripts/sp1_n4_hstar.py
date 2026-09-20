"""Measure the bounded minimum coordination order after Geo-QPG-BR.

The confirmatory block replays the 1,200 frozen N4 worlds.  A separate
sensitivity block varies N/K.  The reported category ``>3`` means only that no
connected strict improvement of order one, two or three was found.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable, Mapping

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.ticker import FuncFormatter


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import World, make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import (  # noqa: E402
    minimum_improving_coalition_order,
    run_geo_qpg,
)

import sp1_n4_cross_family as cross  # noqa: E402


DEFAULT_CONFIG = REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n4_hstar_v4.yaml"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n4_v4"
CATEGORIES = ("2", "3", ">3")
CATEGORY_COLORS = {"2": "#2F6FB0", "3": "#D64B3C", ">3": "#6C727A"}
CATEGORY_LABELS = {
    "2": r"$h_c^\star=2$",
    "3": r"$h_c^\star=3$",
    ">3": "sin escape detectado\nhasta $h=3$",
}
METHOD_LABELS = {
    "geo_qpg_u": "BR (h=1)",
    "geo_qpg_p": "2BR (h<=2)",
    "geo_qpg_c3": "C3 (h<=3)",
    "geo_qpg_d": "DMIS+TX",
}
METHOD_COLORS = {
    "geo_qpg_u": "#6C727A",
    "geo_qpg_p": "#2F6FB0",
    "geo_qpg_c3": "#D64B3C",
    "geo_qpg_d": "#16825D",
}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def load_config(path: Path, smoke: bool) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if smoke:
        config["campaign_id"] += "_SMOKE"
        config["main"]["max_worlds"] = 24
        config["ratio_sweep"]["robot_load_pairs"] = [[8, 4], [12, 4]]
        config["ratio_sweep"]["scenarios"] = ["uniform", "corridor"]
        config["ratio_sweep"]["capacity_cv"] = [0.0, 1.0]
        config["ratio_sweep"]["pressure"] = [0.85]
        config["ratio_sweep"]["seeds_per_cell"] = 1
    return config


def world_from_source(row: Mapping[str, Any], section: Mapping[str, Any]) -> World:
    world = make_world(
        world_id=str(row["world_id"]),
        robot_count=int(row["N"]),
        load_count=int(row["K"]),
        q_bar=float(section["q_bar_kg"]),
        cv=float(row["capacity_cv"]),
        pressure=float(row["pressure"]),
        scenario=str(row["scenario"]),
        workspace=tuple(float(value) for value in section["workspace_m"]),
        seed=int(row["world_seed"]),
        alpha=float(section["demand_split_alpha"]),
    )
    expected = row.get("world_digest")
    if expected is not None and str(expected) != "nan" and world.digest() != str(expected):
        raise RuntimeError(f"world digest mismatch: {row['world_key']}")
    return world


def _audit_world(
    world: World,
    *,
    world_key: str,
    block: str,
    graph_regime: str,
    max_order: int,
    expected_br: Mapping[str, Any] | None = None,
    source_gaps: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    adjacency = adjacency_for_regime(world.robot_positions, graph_regime)
    terminal = run_geo_qpg(world, adjacency, "geo_qpg_u")
    if not terminal.unilateral_local_minimum:
        raise AssertionError(f"BR did not terminate at a unilateral minimum: {world_key}")
    if expected_br:
        expected_distance = float(expected_br["distance_cost"])
        if not np.isclose(terminal.certificate.distance_cost, expected_distance, rtol=0.0, atol=1e-8):
            raise AssertionError(
                f"BR replay drift in {world_key}: "
                f"{terminal.certificate.distance_cost} != {expected_distance}"
            )

    started = time.perf_counter()
    audit = minimum_improving_coalition_order(
        world,
        terminal.assignment,
        adjacency,
        max_order=max_order,
        connected_only=True,
    )
    search_ms = 1_000.0 * (time.perf_counter() - started)
    if audit.order == 1:
        raise AssertionError(f"h*=1 contradicts BR termination in {world_key}")
    source_gaps = source_gaps or {}
    return {
        "campaign_id": "SP1_N4_HSTAR_v4",
        "experiment": "E9_HSTAR_BARRIERS",
        "block": block,
        "world_key": world_key,
        "world_id": world.world_id,
        "world_seed": int(world.seed),
        "scenario": world.scenario,
        "N": world.n_robots,
        "K": world.n_loads,
        "robots_per_load": world.n_robots / world.n_loads,
        "capacity_cv": world.capacity_cv,
        "realized_cv": world.realized_cv,
        "pressure": world.pressure,
        "graph_regime": graph_regime,
        "graph_edges": int(np.count_nonzero(adjacency) // 2),
        "graph_connected": bool(terminal.graph["connected"]),
        "br_status": terminal.algorithm_status,
        "br_phase": terminal.terminal_phase,
        "br_feasible": bool(terminal.certificate.feasible),
        "br_distance": float(terminal.certificate.distance_cost),
        "br_deficit": float(terminal.certificate.total_deficit),
        "br_rounds": int(terminal.rounds),
        "br_bytes_per_agent": float(terminal.bytes_sent / world.n_robots),
        "hstar_order": audit.order if audit.order is not None else math.nan,
        "hstar_category": audit.category,
        "searched_through": audit.searched_through,
        "phase": audit.phase,
        "witness_robots": ";".join(map(str, audit.robot_ids)),
        "witness_old_actions": ";".join(map(str, audit.old_actions)),
        "witness_new_actions": ";".join(map(str, audit.new_actions)),
        "witness_delta_deficit": audit.delta_deficit,
        "witness_delta_distance": audit.delta_distance,
        "search_runtime_ms": search_ms,
        "br_assignment": ";".join(map(str, terminal.assignment.tolist())),
        "gap_br": float(source_gaps.get("geo_qpg_u", math.nan)),
        "gap_2br": float(source_gaps.get("geo_qpg_p", math.nan)),
        "gap_c3": float(source_gaps.get("geo_qpg_c3", math.nan)),
    }


def run_main_world(payload: tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, float]]):
    row, section, expected, gaps = payload
    world = world_from_source(row, section)
    return _audit_world(
        world,
        world_key=str(row["world_key"]),
        block="frozen_main",
        graph_regime=str(section["graph_regime"]),
        max_order=int(section["max_order"]),
        expected_br=expected,
        source_gaps=gaps,
    )


def run_ratio_world(payload: tuple[dict[str, Any], dict[str, Any]]):
    cell, section = payload
    world = make_world(
        world_id=str(cell["world_id"]),
        robot_count=int(cell["N"]),
        load_count=int(cell["K"]),
        q_bar=float(section["q_bar_kg"]),
        cv=float(cell["capacity_cv"]),
        pressure=float(cell["pressure"]),
        scenario=str(cell["scenario"]),
        workspace=tuple(float(value) for value in section["workspace_m"]),
        seed=int(cell["world_seed"]),
        alpha=float(section["demand_split_alpha"]),
    )
    return _audit_world(
        world,
        world_key=str(cell["world_key"]),
        block="ratio_sensitivity",
        graph_regime=str(section["graph_regime"]),
        max_order=int(section["max_order"]),
    )


def _execute(payloads: Iterable[Any], worker: Any, *, workers: int, label: str) -> list[dict[str, Any]]:
    payloads = list(payloads)
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(worker, payload) for payload in payloads]
        for index, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if index == len(futures) or index % max(1, len(futures) // 50) == 0:
                print(f"  {label}: {index}/{len(futures)}", flush=True)
    return rows


def run_campaign(config: Mapping[str, Any], *, workers: int) -> pd.DataFrame:
    objective = config["objective"]
    main = dict(config["main"])
    main["max_order"] = int(objective["max_order"])
    worlds = pd.read_csv(REPOSITORY_ROOT / str(main["source_worlds"]))
    max_worlds = main.get("max_worlds")
    if max_worlds is not None:
        indices = np.linspace(0, len(worlds) - 1, int(max_worlds), dtype=int)
        worlds = worlds.iloc[indices].copy()
    runs = pd.read_csv(REPOSITORY_ROOT / str(main["source_runs"]))
    runs = runs[runs["world_key"].isin(worlds["world_key"])].copy()
    br_lookup = (
        runs[runs["method"] == "geo_qpg_u"]
        .drop_duplicates("world_key")
        .set_index("world_key")
    )
    gap_lookup = (
        runs[runs["method"].isin(["geo_qpg_u", "geo_qpg_p", "geo_qpg_c3"])]
        .pivot_table(index="world_key", columns="method", values="optimality_gap", aggfunc="first")
        .reindex(worlds["world_key"].astype(str))
    )
    main_payloads = []
    for _, row in worlds.iterrows():
        key = str(row["world_key"])
        main_payloads.append(
            (
                row.to_dict(),
                main,
                br_lookup.loc[key].to_dict(),
                gap_lookup.loc[key].to_dict(),
            )
        )
    rows = _execute(main_payloads, run_main_world, workers=workers, label="main h*")

    ratio = dict(config["ratio_sweep"])
    ratio["max_order"] = int(objective["max_order"])
    ratio_payloads = []
    for n, k in ratio["robot_load_pairs"]:
        for scenario in ratio["scenarios"]:
            for cv in ratio["capacity_cv"]:
                for pressure in ratio["pressure"]:
                    for replicate in range(int(ratio["seeds_per_cell"])):
                        seed = cross.stable_seed(
                            int(ratio["base_seed"]), n, k, scenario, cv, pressure, replicate
                        )
                        key = (
                            f"E9R:N{n}:K{k}:{scenario}:p{float(pressure):.2f}:"
                            f"cv{float(cv):.2f}:r{replicate}"
                        )
                        ratio_payloads.append(
                            (
                                {
                                    "world_key": key,
                                    "world_id": key,
                                    "world_seed": seed,
                                    "N": int(n),
                                    "K": int(k),
                                    "scenario": str(scenario),
                                    "capacity_cv": float(cv),
                                    "pressure": float(pressure),
                                },
                                ratio,
                            )
                        )
    rows.extend(
        _execute(ratio_payloads, run_ratio_world, workers=workers, label="ratio h*")
    )
    frame = pd.DataFrame(rows).sort_values(["block", "world_key"]).reset_index(drop=True)
    frame["campaign_id"] = str(config["campaign_id"])
    if set(frame["hstar_category"]) - set(CATEGORIES):
        raise AssertionError(f"unexpected h* categories: {sorted(set(frame['hstar_category']))}")
    return frame


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def category_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    specifications = [
        ("overall", []),
        ("capacity_cv", ["capacity_cv"]),
        ("pressure", ["pressure"]),
        ("scenario", ["scenario"]),
        ("robots_per_load", ["robots_per_load"]),
        ("cv_pressure", ["capacity_cv", "pressure"]),
        ("ratio_pressure", ["robots_per_load", "pressure"]),
    ]
    for block, block_frame in frame.groupby("block", sort=False):
        for factor, keys in specifications:
            if factor == "robots_per_load" or factor == "ratio_pressure":
                if block != "ratio_sensitivity":
                    continue
            if not keys:
                groups = [((), block_frame)]
            elif all(key in block_frame for key in keys):
                groups = block_frame.groupby(keys, dropna=False, sort=True)
            else:
                continue
            for values, group in groups:
                if not isinstance(values, tuple):
                    values = (values,)
                factor_value = " | ".join(
                    f"{key}={value}" for key, value in zip(keys, values, strict=True)
                ) or "all"
                for category in CATEGORIES:
                    count = int((group["hstar_category"] == category).sum())
                    total = int(len(group))
                    low, high = wilson_interval(count, total)
                    rows.append(
                        {
                            "block": block,
                            "factor": factor,
                            "factor_value": factor_value,
                            "category": category,
                            "count": count,
                            "total": total,
                            "proportion": count / total,
                            "ci95_low": low,
                            "ci95_high": high,
                        }
                    )
    return pd.DataFrame(rows)


def configure_plots() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 8.5,
            "axes.edgecolor": "#56616D",
            "axes.linewidth": 0.7,
            "axes.facecolor": "#FBFCFD",
            "figure.facecolor": "white",
            "grid.color": "#DCE2E8",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.75,
            "legend.frameon": False,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"), dpi=300)
    fig.savefig(path.with_suffix(".png"), dpi=300)
    plt.close(fig)


def _stacked_bars(
    ax: plt.Axes,
    frame: pd.DataFrame,
    keys: list[str],
    labels: list[str],
) -> None:
    grouped = (
        frame.groupby(keys + ["hstar_category"]).size().unstack(fill_value=0).reindex(columns=CATEGORIES, fill_value=0)
    )
    proportions = grouped.div(grouped.sum(axis=1), axis=0)
    x = np.arange(len(grouped))
    bottom = np.zeros(len(grouped))
    for category in CATEGORIES:
        values = proportions[category].to_numpy(float)
        ax.bar(
            x,
            values,
            bottom=bottom,
            width=0.72,
            color=CATEGORY_COLORS[category],
            edgecolor="white",
            linewidth=0.5,
            label=CATEGORY_LABELS[category],
        )
        for index, (value, base) in enumerate(zip(values, bottom, strict=True)):
            if value >= 0.10:
                ax.text(index, base + value / 2.0, f"{100*value:.0f} %", ha="center", va="center", color="white", fontsize=7, fontweight="bold")
        bottom += values
    ax.set_xticks(x, labels)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Proporción de terminales BR")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))


def plot_hstar_distribution(frame: pd.DataFrame, output: Path) -> None:
    main = frame[frame["block"] == "frozen_main"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 5.2), constrained_layout=True)
    cv_pressure = (
        main[["capacity_cv", "pressure"]]
        .drop_duplicates()
        .sort_values(["capacity_cv", "pressure"])
    )
    labels = [
        f"CV={cross.spanish_number(row.capacity_cv)}\n"
        f"ρ={cross.spanish_number(row.pressure)}"
        for row in cv_pressure.itertuples()
    ]
    _stacked_bars(axes[0], main, ["capacity_cv", "pressure"], labels)
    axes[0].set_title("A. Por heterogeneidad y presión")
    scenario_order = ["uniform", "clustered", "separated", "ring", "corridor"]
    _stacked_bars(axes[1], main, ["scenario"], ["Aleatorio", "Agrupado", "Separado", "Anillo", "Pasillo"])
    axes[1].set_title("B. Por geometría")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="outside lower center", ncol=3, frameon=False)
    fig.suptitle(
        "Orden mínimo conectado tras agotar BR unilateral",
        fontsize=11.5,
        fontweight="bold",
        y=1.025,
    )
    save_figure(fig, output / "n4_hstar_distribution")


def plot_hstar_ratio(frame: pd.DataFrame, output: Path) -> None:
    ratio = frame[frame["block"] == "ratio_sensitivity"].copy()
    ratios = sorted(ratio["robots_per_load"].unique())
    cvs = sorted(ratio["capacity_cv"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 4.6), constrained_layout=True, gridspec_kw={"width_ratios": [1.0, 1.0, 1.08]})
    pressure_axes: list[plt.Axes] = []
    for ax in axes[:2]:
        ax.set_visible(False)
    for ax, pressure in zip(axes[:2], sorted(ratio["pressure"].unique())):
        ax.set_visible(True)
        pressure_axes.append(ax)
        subset = ratio[ratio["pressure"] == pressure]
        matrix = np.zeros((len(cvs), len(ratios)))
        for row_index, cv in enumerate(cvs):
            for column_index, value in enumerate(ratios):
                cell = subset[(subset["capacity_cv"] == cv) & (subset["robots_per_load"] == value)]
                matrix[row_index, column_index] = (cell["hstar_category"] == ">3").mean()
        image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlOrRd", aspect="auto")
        for row_index in range(len(cvs)):
            for column_index in range(len(ratios)):
                value = matrix[row_index, column_index]
                ax.text(column_index, row_index, f"{100*value:.0f} %", ha="center", va="center", color="white" if value > 0.55 else "#202124", fontweight="bold", fontsize=8)
        ax.set_xticks(range(len(ratios)), [cross.spanish_number(value) for value in ratios])
        ax.set_yticks(range(len(cvs)), [cross.spanish_number(value) for value in cvs])
        ax.set_xlabel("AMR por carga N/K")
        ax.set_ylabel("CV de capacidad")
        ax.set_title(f"ρ={cross.spanish_number(pressure)}: sin escape hasta $h=3$")
    overall = ratio.groupby(["robots_per_load", "hstar_category"]).size().unstack(fill_value=0).reindex(columns=CATEGORIES, fill_value=0)
    proportions = overall.div(overall.sum(axis=1), axis=0)
    bottom = np.zeros(len(overall))
    x = np.arange(len(overall))
    for category in CATEGORIES:
        values = proportions[category].to_numpy(float)
        label = CATEGORY_LABELS[category]
        axes[2].bar(x, values, bottom=bottom, width=0.64, color=CATEGORY_COLORS[category], edgecolor="white", label=label)
        bottom += values
    axes[2].set_xticks(x, [cross.spanish_number(value) for value in overall.index])
    axes[2].set_xlabel("AMR por carga N/K")
    axes[2].set_ylabel("Proporción")
    axes[2].set_ylim(0.0, 1.0)
    axes[2].grid(axis="y")
    axes[2].yaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))
    axes[2].set_title("Distribución marginal")
    axes[2].legend(loc="lower right")
    colorbar = fig.colorbar(
        image,
        ax=pressure_axes,
        shrink=0.78,
        label="Proporción sin mejora hasta h=3",
    )
    colorbar.ax.yaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))
    fig.suptitle("Sensibilidad separada a N/K: búsqueda truncada en h=3", fontsize=11.5, fontweight="bold")
    save_figure(fig, output / "n4_hstar_ratio_sensitivity")


def plot_hstar_gap_link(frame: pd.DataFrame, output: Path) -> None:
    main = frame[frame["block"] == "frozen_main"].dropna(subset=["gap_br", "gap_2br", "gap_c3"]).copy()
    main["gain_2br"] = 100.0 * (main["gap_br"] - main["gap_2br"])
    main["gain_c3"] = 100.0 * (main["gap_2br"] - main["gap_c3"])
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.8), constrained_layout=True)
    positions = np.arange(len(CATEGORIES))
    rng = np.random.default_rng(2026081517)
    for ax, metric, title, color in (
        (axes[0], "gain_2br", "A. Reducción de brecha al pasar BR → 2BR", "#2F6FB0"),
        (axes[1], "gain_c3", "B. Reducción adicional al pasar 2BR → C3", "#D64B3C"),
    ):
        values = [main.loc[main["hstar_category"] == category, metric].to_numpy(float) for category in CATEGORIES]
        # A density estimate is not informative for tiny categories (notably
        # the four h_c*=3 worlds).  Draw a violin only when the sample can
        # support it; all small-category observations remain visible.
        valid = [
            (position, data)
            for position, data in zip(positions, values, strict=True)
            if len(data) >= 20
        ]
        if valid:
            violin = ax.violinplot(
                [data for _, data in valid],
                positions=[position for position, _ in valid],
                widths=0.78,
                showmeans=False,
                showmedians=False,
                showextrema=False,
            )
            for body in violin["bodies"]:
                body.set_facecolor(color)
                body.set_edgecolor(color)
                body.set_alpha(0.22)
        for index, data in enumerate(values):
            n_obs = len(data)
            if not n_obs:
                continue
            if n_obs >= 20:
                # Muestra grande: nube con jitter y resumen por la mediana.
                sample_size = min(n_obs, 130)
                jitter = rng.normal(index, 0.045, size=sample_size)
                sample = data[
                    rng.choice(n_obs, size=sample_size, replace=False)
                ]
                ax.scatter(jitter, sample, s=8, color=color, alpha=0.25, linewidth=0)
                median = float(np.median(data))
                ax.plot([index - 0.22, index + 0.22], [median, median], color="#202124", linewidth=2.0)
                ax.text(index, median, f"  {cross.spanish_number(median, 1)}", va="center", ha="left", fontsize=7.5, fontweight="bold")
            else:
                # Con cuatro o con una observacion no hay densidad que estimar
                # ni mediana que resuma nada: se dibujan los puntos crudos, sin
                # jitter aleatorio, y se rotula su valor.
                offsets = (
                    np.linspace(-0.12, 0.12, n_obs) if n_obs > 1 else np.zeros(1)
                )
                ax.scatter(index + offsets, data, s=30, color=color, alpha=0.95,
                           edgecolor="white", linewidth=0.6, zorder=4)
                for off, value in zip(offsets, data, strict=True):
                    ax.text(index + off, float(value),
                            f"  {cross.spanish_number(float(value), 1)}",
                            va="center", ha="left", fontsize=6.4, color="#3A3A3A")
        ax.axhline(0.0, color="#56616D", linewidth=0.8)
        ax.set_xticks(
            positions,
            [
                (
                    f"sin escape\n(n={len(data)})"
                    if category.startswith(">")
                    else CATEGORY_LABELS[category] + f"\n(n={len(data)})"
                )
                for category, data in zip(CATEGORIES, values, strict=True)
            ],
        )
        ax.set_ylabel("Cambio de brecha (puntos porcentuales)")
        ax.set_title(title)
        ax.grid(axis="y")
        ax.yaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))
    fig.suptitle("")
    save_figure(fig, output / "n4_hstar_gap_link")


def representative_trace(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    main = frame[frame["block"] == "frozen_main"].copy()
    candidates = main[
        (main["hstar_category"] == "3")
        & (main["capacity_cv"] >= 0.65)
        & (main["pressure"] == main["pressure"].max())
    ]
    selected = (candidates if len(candidates) else main).sort_values("world_key").iloc[0]
    worlds = pd.read_csv(REPOSITORY_ROOT / str(config["main"]["source_worlds"]))
    source = worlds[worlds["world_key"] == selected["world_key"]].iloc[0]
    world = world_from_source(source.to_dict(), config["main"])
    adjacency = adjacency_for_regime(world.robot_positions, str(config["main"]["graph_regime"]))
    rows: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    for method in METHOD_LABELS:
        result = run_geo_qpg(world, adjacency, method)
        rows.append(
            {
                "world_key": selected["world_key"],
                "method": method,
                "commit": 0,
                "deficit": float(world.demands.sum()),
                "distance": 0.0,
                "move_order": 0,
                "phase": "Q",
            }
        )
        commit = 0
        for event in result.event_history:
            if not event.accepted:
                continue
            commit += 1
            rows.append(
                {
                    "world_key": selected["world_key"],
                    "method": method,
                    "commit": commit,
                    "deficit": event.deficit_after,
                    "distance": event.distance_after,
                    "move_order": len(event.robot_ids),
                    "phase": event.phase,
                }
            )
        endpoints.append(
            {
                "world_key": selected["world_key"],
                "method": method,
                "bytes_per_agent": result.bytes_sent / world.n_robots,
                "rounds": result.rounds,
                "distance": result.certificate.distance_cost,
                "feasible": result.certificate.feasible,
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(endpoints), str(selected["world_key"])


def plot_fi_trace(trace: pd.DataFrame, endpoints: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 6.25), constrained_layout=True)
    for method, group in trace.groupby("method", sort=False):
        label = METHOD_LABELS[method]
        color = METHOD_COLORS[method]
        axes[0, 0].step(group["commit"], group["deficit"], where="post", label=label, color=color, linewidth=1.7)
        axes[0, 1].step(group["commit"], group["distance"], where="post", label=label, color=color, linewidth=1.7)
        accepted = group[group["commit"] > 0]
        axes[1, 0].scatter(accepted["commit"], accepted["move_order"], s=22, color=color, alpha=0.75, label=label)
    axes[0, 0].set_title("A. Déficit después de cada commit")
    axes[0, 0].set_ylabel("D(a) [capacidad]")
    axes[0, 1].set_title("B. Coste geométrico durante la ejecución")
    axes[0, 1].set_ylabel("J(a) [m]")
    axes[1, 0].set_title("C. Orden de la desviación aceptada")
    axes[1, 0].set_ylabel("AMR que cambian")
    axes[1, 0].set_yticks([1, 2, 3])
    order = list(METHOD_LABELS)
    endpoint = endpoints.set_index("method").loc[order]
    bars = axes[1, 1].bar(
        np.arange(len(order)),
        endpoint["bytes_per_agent"],
        color=[METHOD_COLORS[method] for method in order],
        width=0.68,
    )
    axes[1, 1].bar_label(bars, fmt="%.0f", padding=2, fontsize=7.5)
    axes[1, 1].set_xticks(np.arange(len(order)), [METHOD_LABELS[method].replace(" ", "\n", 1) for method in order])
    axes[1, 1].set_ylabel("Bytes por AMR")
    axes[1, 1].set_title("D. Coste de comunicación al terminar")
    for ax in axes.flat:
        ax.grid(True)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))
    for ax in (axes[0, 0], axes[0, 1], axes[1, 0]):
        ax.xaxis.set_major_formatter(FuncFormatter(cross.spanish_tick))
    axes[1, 0].set_xlabel("Commit aceptado")
    axes[0, 0].set_xlabel("Commit aceptado")
    axes[0, 1].set_xlabel("Commit aceptado")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.015), ncol=4)
    fig.suptitle(
        "F-I: mejora lexicográfica y tráfico en una ejecución",
        fontsize=11.5,
        fontweight="bold",
        y=1.095,
    )
    save_figure(fig, output / "n4_fi_representative_trace")


def write_macros(path: Path, frame: pd.DataFrame) -> None:
    main = frame[frame["block"] == "frozen_main"]
    ratio = frame[frame["block"] == "ratio_sensitivity"]
    proportions = main["hstar_category"].value_counts(normalize=True)
    low_cv = main[main["capacity_cv"] == main["capacity_cv"].min()]
    high_cv = main[main["capacity_cv"] == main["capacity_cv"].max()]
    hard = lambda data: 100.0 * data["hstar_category"].isin(["3", ">3"]).mean()
    pair_gain = 100.0 * (
        main.loc[main["hstar_category"] == "2", "gap_br"]
        - main.loc[main["hstar_category"] == "2", "gap_2br"]
    )
    triple_gain = 100.0 * (
        main.loc[main["hstar_category"] == "3", "gap_2br"]
        - main.loc[main["hstar_category"] == "3", "gap_c3"]
    )
    ratio_low = ratio[ratio["robots_per_load"] == ratio["robots_per_load"].min()]
    ratio_high = ratio[ratio["robots_per_load"] == ratio["robots_per_load"].max()]
    lines = [
        f"\\newcommand{{\\NFourHStarWorlds}}{{{len(main):,}}}".replace(",", r"\,"),
        f"\\newcommand{{\\NFourHStarRatioWorlds}}{{{len(ratio):,}}}".replace(",", r"\,"),
        f"\\newcommand{{\\NFourHStarTwoPct}}{{{cross.latex_decimal(100.0 * proportions.get('2', 0.0), 1)}}}",
        f"\\newcommand{{\\NFourHStarThreePct}}{{{cross.latex_decimal(100.0 * proportions.get('3', 0.0), 1)}}}",
        f"\\newcommand{{\\NFourHStarGtThreePct}}{{{cross.latex_decimal(100.0 * proportions.get('>3', 0.0), 1)}}}",
        f"\\newcommand{{\\NFourHStarHardLowCvPct}}{{{cross.latex_decimal(hard(low_cv), 1)}}}",
        f"\\newcommand{{\\NFourHStarHardHighCvPct}}{{{cross.latex_decimal(hard(high_cv), 1)}}}",
        f"\\newcommand{{\\NFourHStarSearchMedianMs}}{{{cross.latex_decimal(main['search_runtime_ms'].median(), 1)}}}",
        f"\\newcommand{{\\NFourHStarPairGainPct}}{{{cross.latex_decimal(pair_gain.dropna().median(), 1)}}}",
        f"\\newcommand{{\\NFourHStarTripleGainPct}}{{{cross.latex_decimal(triple_gain.dropna().median(), 1)}}}",
        f"\\newcommand{{\\NFourHStarGtThreeLowRatioPct}}{{{cross.latex_decimal(100.0 * (ratio_low['hstar_category'] == '>3').mean(), 1)}}}",
        f"\\newcommand{{\\NFourHStarGtThreeHighRatioPct}}{{{cross.latex_decimal(100.0 * (ratio_high['hstar_category'] == '>3').mean(), 1)}}}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(args, cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=False).stdout.strip()

    return {
        "commit": run("git", "rev-parse", "HEAD") or "unknown",
        "branch": run("git", "branch", "--show-current") or "unknown",
        "tree_dirty": bool(run("git", "status", "--porcelain")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--analysis-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config, args.smoke)
    output = args.output
    if args.smoke and args.output == DEFAULT_OUTPUT:
        output = DEFAULT_OUTPUT.with_name("n4_v4_smoke")
    for folder in ("raw", "processed", "figures"):
        (output / folder).mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    raw_path = output / "raw" / "e9_hstar_runs.csv"
    if args.analysis_only:
        if not raw_path.exists():
            raise FileNotFoundError(f"analysis-only requires {raw_path}")
        frame = pd.read_csv(raw_path)
    else:
        frame = run_campaign(config, workers=args.workers)
        frame.to_csv(raw_path, index=False)

    summary = category_summary(frame)
    summary.to_csv(output / "processed" / "hstar_category_summary.csv", index=False)
    trace, endpoints, trace_world = representative_trace(frame, config)
    trace.to_csv(output / "raw" / "e9_fi_representative_trace.csv", index=False)
    endpoints.to_csv(output / "processed" / "e9_fi_trace_endpoints.csv", index=False)
    write_macros(output / "processed" / "n4_v4_results_macros.tex", frame)

    configure_plots()
    plot_hstar_distribution(frame, output / "figures")
    plot_hstar_ratio(frame, output / "figures")
    plot_hstar_gap_link(frame, output / "figures")
    plot_fi_trace(trace, endpoints, output / "figures")

    main_frame = frame[frame["block"] == "frozen_main"]
    metrics = {
        "main_worlds": int(len(main_frame)),
        "ratio_worlds": int((frame["block"] == "ratio_sensitivity").sum()),
        "categories": main_frame["hstar_category"].value_counts(normalize=True).sort_index().to_dict(),
        "search_runtime_ms_median": float(main_frame["search_runtime_ms"].median()),
        "representative_trace_world": trace_world,
        "elapsed_s": time.perf_counter() - started,
    }
    write_json(output / "key_metrics.json", metrics)
    (output / "config_frozen.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    report = (
        "# SP1.N4 minimum coordination-order audit v4\n\n"
        f"- Frozen worlds: {metrics['main_worlds']}\n"
        f"- Independent N/K sensitivity worlds: {metrics['ratio_worlds']}\n"
        f"- h*=2: {100.0 * metrics['categories'].get('2', 0.0):.1f}%\n"
        f"- h*=3: {100.0 * metrics['categories'].get('3', 0.0):.1f}%\n"
        f"- no connected improvement through h=3: {100.0 * metrics['categories'].get('>3', 0.0):.1f}%\n"
        f"- representative trace: {trace_world}\n\n"
        "The audited state is the unilateral BR terminal reached from idle. "
        "The >3 category is a bounded-search result, not a certificate of global "
        "optimality or of the absence of larger deviations.\n"
    )
    (output / "REPORT.md").write_text(report, encoding="utf-8")

    artifact_files = sorted(
        path for path in output.rglob("*") if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "campaign_id": config["campaign_id"],
        "status": "smoke" if args.smoke else "executed",
        "git": git_state(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "workers": args.workers,
        },
        "artifacts": {
            path.relative_to(output).as_posix(): {
                "sha256": cross.sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in artifact_files
        },
        "limitations": config["limitations"],
    }
    write_json(output / "manifest.json", manifest)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
