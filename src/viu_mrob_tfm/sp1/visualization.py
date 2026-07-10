"""Plots and lightweight videos for SP1 recruitment experiments."""

from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.domain import WorldState
from viu_mrob_tfm.sp1.metrics import load_diagnostics


PERFORMANCE_METRICS = [
    ("demand_satisfaction_ratio", "Demand", True),
    ("coalition_success_rate", "Coalition OK", True),
    ("served_load_rate", "Served loads", True),
    ("optimality_gap_vs_oracle", "Oracle gap", False),
    ("robots_underassigned", "Under AMRs", False),
    ("robots_overassigned", "Over AMRs", False),
    ("travel_distance_m", "Travel m", False),
    ("estimated_arrival_time_s", "Arrival s", False),
    ("energy_proxy_wh", "Energy Wh", False),
    ("communication_messages", "Messages", False),
    ("runtime_ms", "Runtime ms", False),
]


def plot_summary_bars(rows: list[dict[str, Any]], path: Path, metric: str = "demand_satisfaction_ratio") -> None:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        grouped.setdefault(str(row["method"]), []).append(float(row[metric]))
    methods = sorted(grouped)
    values = [float(np.mean(grouped[method])) for method in methods]
    figure, axis = plt.subplots(figsize=(10, 4.8))
    axis.bar(methods, values, color="#4477aa")
    axis.set_ylim(0.0, 1.05 if metric.endswith("ratio") or metric.endswith("rate") else max(values) * 1.2)
    axis.set_ylabel(metric)
    axis.set_title(f"SP1 Monte Carlo summary: {metric}")
    axis.tick_params(axis="x", rotation=28, labelsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_demand_ratio_interaction(rows: list[dict[str, Any]], path: Path) -> None:
    figure, axis = plt.subplots(figsize=(9, 5))
    methods = sorted({str(row["method"]) for row in rows})
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        xs = np.asarray([float(row["demand_ratio"]) for row in method_rows], dtype=float)
        ys = np.asarray([float(row["demand_satisfaction_ratio"]) for row in method_rows], dtype=float)
        if xs.size == 0:
            continue
        bins = np.linspace(0.45, 1.75, 6)
        centers = 0.5 * (bins[:-1] + bins[1:])
        means = []
        for left, right in zip(bins[:-1], bins[1:]):
            mask = (xs >= left) & (xs < right)
            means.append(float(np.mean(ys[mask])) if np.any(mask) else np.nan)
        axis.plot(centers, means, marker="o", linewidth=1.5, label=method)
    axis.set_xlabel("Demand ratio rho_D")
    axis.set_ylabel("Demand satisfaction ratio")
    axis.set_ylim(0.0, 1.05)
    axis.grid(True, alpha=0.2)
    axis.legend(fontsize=7, ncols=2)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_method_performance_matrix(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot mean method performance with normalized color and raw cell values."""

    if not rows:
        _draw_placeholder(path, "SP1 performance matrix", "No rows available")
        return
    methods = _ordered_methods(rows)
    raw = np.zeros((len(methods), len(PERFORMANCE_METRICS)), dtype=float)
    for method_idx, method in enumerate(methods):
        method_rows = [row for row in rows if str(row["method"]) == method]
        for metric_idx, (metric, _label, _higher_is_better) in enumerate(PERFORMANCE_METRICS):
            raw[method_idx, metric_idx] = _mean_metric(method_rows, metric)
    normalized = np.zeros_like(raw)
    for metric_idx, (_metric, _label, higher_is_better) in enumerate(PERFORMANCE_METRICS):
        values = raw[:, metric_idx]
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            continue
        low = float(np.min(finite))
        high = float(np.max(finite))
        if math.isclose(low, high):
            normalized[:, metric_idx] = 1.0
        elif higher_is_better:
            normalized[:, metric_idx] = (values - low) / (high - low)
        else:
            normalized[:, metric_idx] = (high - values) / (high - low)
    figure_height = max(5.2, 0.34 * len(methods) + 2.0)
    figure, axis = plt.subplots(figsize=(13.2, figure_height))
    image = axis.imshow(normalized, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    axis.set_xticks(np.arange(len(PERFORMANCE_METRICS)))
    axis.set_xticklabels([label for _metric, label, _higher in PERFORMANCE_METRICS], rotation=25, ha="right")
    axis.set_yticks(np.arange(len(methods)))
    axis.set_yticklabels([_method_label(rows, method) for method in methods], fontsize=8)
    for method_idx in range(len(methods)):
        for metric_idx in range(len(PERFORMANCE_METRICS)):
            value = raw[method_idx, metric_idx]
            cell = normalized[method_idx, metric_idx]
            text_color = "white" if cell < 0.45 else "black"
            axis.text(metric_idx, method_idx, _format_cell(value), ha="center", va="center", fontsize=7, color=text_color)
    axis.set_title("SP1 performance matrix by method (mean over runs)")
    axis.set_xlabel("Metric; color is normalized quality within each metric")
    figure.colorbar(image, ax=axis, fraction=0.025, pad=0.02, label="Normalized quality")
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_taxonomy_comparison(rows: list[dict[str, Any]], path: Path) -> None:
    """Compare central/decentralized, family, and ownership taxonomies."""

    if not rows:
        _draw_placeholder(path, "SP1 taxonomy comparison", "No rows available")
        return
    axes_config = [
        ("method_scope", "Centralized vs decentralized"),
        ("method_family", "Classic vs SOTA vs model/data"),
        ("method_ownership", "Ours vs baselines/reference"),
    ]
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    for axis, (key, title) in zip(axes, axes_config):
        groups = _ordered_tokens({str(row.get(key, "unknown")) for row in rows}, key)
        demand_values = [_mean_metric([row for row in rows if str(row.get(key, "unknown")) == group], "demand_satisfaction_ratio") for group in groups]
        success_values = [_mean_metric([row for row in rows if str(row.get(key, "unknown")) == group], "coalition_success_rate") for group in groups]
        gap_values = [_mean_metric([row for row in rows if str(row.get(key, "unknown")) == group], "optimality_gap_vs_oracle") for group in groups]
        x = np.arange(len(groups))
        width = 0.36
        axis.bar(x - width / 2, demand_values, width=width, label="Demand", color="#2f6fbb")
        axis.bar(x + width / 2, success_values, width=width, label="Coalition OK", color="#d08c2f")
        for idx, gap in enumerate(gap_values):
            axis.text(idx, 1.025, f"gap={gap:.2f}", ha="center", va="bottom", fontsize=7, rotation=90)
        axis.set_xticks(x)
        axis.set_xticklabels([_pretty_token(group) for group in groups], rotation=30, ha="right", fontsize=8)
        axis.set_ylim(0.0, 1.18)
        axis.grid(True, axis="y", alpha=0.2)
        axis.set_title(title)
    axes[0].set_ylabel("Mean ratio/rate")
    axes[0].legend(fontsize=8, loc="lower left")
    figure.suptitle("SP1 performance by method taxonomy", y=1.02)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_ours_vs_others(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot proposed methods against baselines and theoretical references."""

    if not rows:
        _draw_placeholder(path, "SP1 ours vs others", "No rows available")
        return
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    ownerships = _ordered_tokens({str(row.get("method_ownership", "unknown")) for row in rows}, "method_ownership")
    figure, axis = plt.subplots(figsize=(12.5, 5.2))
    x = np.arange(len(scenarios))
    width = min(0.24, 0.78 / max(len(ownerships), 1))
    colors = {"baseline": "#65789b", "proposed": "#2a9d8f", "reference": "#c44536"}
    for idx, ownership in enumerate(ownerships):
        values = []
        gaps = []
        for scenario in scenarios:
            group = [
                row
                for row in rows
                if str(row["scenario_generator"]) == scenario and str(row.get("method_ownership", "unknown")) == ownership
            ]
            values.append(_mean_metric(group, "demand_satisfaction_ratio"))
            gaps.append(_mean_metric(group, "optimality_gap_vs_oracle"))
        offsets = x + (idx - (len(ownerships) - 1) / 2) * width
        bars = axis.bar(offsets, values, width=width, label=_pretty_token(ownership), color=colors.get(ownership, None))
        for bar, gap in zip(bars, gaps):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                min(float(bar.get_height()) + 0.02, 1.08),
                f"g={gap:.2f}",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=90,
            )
    axis.set_xticks(x)
    axis.set_xticklabels([_pretty_token(scenario) for scenario in scenarios], rotation=20, ha="right")
    axis.set_ylabel("Demand satisfaction ratio")
    axis.set_ylim(0.0, 1.16)
    axis.set_title("SP1 proposed methods vs baselines and theoretical references")
    axis.grid(True, axis="y", alpha=0.2)
    axis.legend(title="Ownership", fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_reference_gap(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot proposed methods against centralized/oracle reference quality."""

    selected = [
        row
        for row in rows
        if str(row.get("method_ownership", "")) in {"proposed", "reference"}
        or str(row.get("method", "")) in {"centralized_coalition_milp", "oracle_reference"}
    ]
    if not selected:
        _draw_placeholder(path, "SP1 reference gap", "No proposed/reference rows available")
        return
    methods = _ordered_methods(selected)
    summaries = []
    for method in methods:
        group = [row for row in selected if str(row["method"]) == method]
        summaries.append(
            {
                "method": method,
                "label": _method_label(group, method),
                "ownership": str(group[0].get("method_ownership", "unknown")),
                "gap": _mean_metric(group, "optimality_gap_vs_oracle"),
                "demand": _mean_metric(group, "demand_satisfaction_ratio"),
            }
        )
    summaries.sort(key=lambda item: (item["ownership"] != "reference", item["gap"], -item["demand"], item["method"]))
    labels = [_wrap_label(item["label"], width=22) for item in summaries]
    y = np.arange(len(summaries))
    colors = [_ownership_color(str(item["ownership"])) for item in summaries]
    figure, (gap_axis, demand_axis) = plt.subplots(1, 2, figsize=(14, max(4.8, 0.4 * len(summaries) + 1.2)), sharey=True)
    gap_axis.barh(y, [item["gap"] for item in summaries], color=colors)
    demand_axis.barh(y, [item["demand"] for item in summaries], color=colors)
    gap_axis.set_yticks(y)
    gap_axis.set_yticklabels(labels, fontsize=8)
    gap_axis.invert_yaxis()
    gap_axis.set_xlabel("Optimality gap vs oracle (lower is better)")
    demand_axis.set_xlabel("Demand satisfaction ratio (higher is better)")
    demand_axis.set_xlim(0.0, 1.05)
    for axis in (gap_axis, demand_axis):
        axis.grid(True, axis="x", alpha=0.2)
    gap_axis.set_title("Distance to theoretical reference")
    demand_axis.set_title("Absolute recruitment quality")
    figure.suptitle("SP1 proposed methods vs centralized/oracle reference", y=1.01)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_communication_degradation(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot performance degradation as communication radius is reduced."""

    variable_scenarios = _scenarios_with_radius_variation(rows)
    selected = [row for row in rows if str(row.get("scenario_generator")) in variable_scenarios] if variable_scenarios else rows
    radius_labels = _ordered_radius_labels({_radius_label(row.get("communication_radius")) for row in selected})
    if len(radius_labels) < 2:
        _draw_placeholder(path, "SP1 communication-radius degradation", "Fewer than two communication radii in this run")
        return
    figure, axes = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
    _plot_radius_lines(
        axes[0],
        selected,
        radius_labels,
        group_key="method_ownership",
        title="Demand degradation by ownership",
    )
    _plot_radius_lines(
        axes[1],
        selected,
        radius_labels,
        group_key="method_scope",
        title="Demand degradation by communication scope",
    )
    axes[0].set_ylabel("Demand satisfaction ratio")
    for axis in axes:
        axis.set_ylim(0.0, 1.05)
        axis.set_xlabel("Communication radius m; inf = unconstrained")
        axis.grid(True, alpha=0.2)
    scenario_note = ", ".join(sorted(variable_scenarios)) if variable_scenarios else "all scenarios"
    figure.suptitle(f"SP1 performance degradation under reduced communication radius ({scenario_note})", y=1.02)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_best_method_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    """Render a compact ranking table: best overall, best proposed, and best baseline."""

    if not rows:
        _draw_placeholder(path, "SP1 best method by scenario", "No rows available")
        return
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    table_rows = []
    for scenario in scenarios:
        summaries = _method_summaries([row for row in rows if str(row["scenario_generator"]) == scenario])
        best_all = _best_summary(summaries)
        best_proposed = _best_summary([row for row in summaries if row["method_ownership"] == "proposed"])
        best_baseline = _best_summary([row for row in summaries if row["method_ownership"] == "baseline"])
        best_reference = _best_summary([row for row in summaries if row["method_ownership"] == "reference"])
        table_rows.append(
            [
                _pretty_token(scenario),
                _summary_cell(best_all),
                _summary_cell(best_reference),
                _summary_cell(best_proposed),
                _summary_cell(best_baseline),
            ]
        )
    figure, axis = plt.subplots(figsize=(14.5, max(3.4, 0.8 * len(table_rows) + 1.9)))
    axis.axis("off")
    table = axis.table(
        cellText=table_rows,
        colLabels=["Scenario", "Best overall", "Theoretical reference", "Best proposed", "Best baseline"],
        loc="center",
        cellLoc="left",
        colWidths=[0.15, 0.22, 0.22, 0.22, 0.22],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.9)
    for (row_idx, col_idx), cell in table.get_celld().items():
        if row_idx == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#333333")
        elif col_idx == 3:
            cell.set_facecolor("#e8f4f1")
        elif col_idx == 2:
            cell.set_facecolor("#f8ebe8")
    axis.set_title("SP1 best method by scenario using theory-aligned quality: oracle gap, coalition success, served loads, demand, under/over assignment, runtime")
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_quality_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot quality against model/training and online compute resources."""

    if not rows:
        _draw_placeholder(path, "SP1 quality-resource Pareto", "No rows available")
        return
    summaries = _method_summaries(rows)
    figure, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    for axis, x_key, xlabel in [
        (axes[0], "method_trainable_parameters", "Trainable execution parameters + 1"),
        (axes[1], "runtime_ms", "Online runtime ms + 1"),
    ]:
        points = []
        for item in summaries:
            x_value = _finite_or_floor(item.get(x_key, 0.0)) + 1.0
            y_value = _finite_or_ceiling(item["optimality_gap_vs_oracle"])
            points.append((x_value, y_value, item))
        offsets = _annotation_offsets([(x_value, y_value) for x_value, y_value, _item in points])
        for (x_value, y_value, item), offset in zip(points, offsets, strict=True):
            size = 50.0 + 0.02 * min(_finite_or_floor(item.get("communication_messages", 0.0)), 2500.0)
            axis.scatter(
                x_value,
                y_value,
                s=size,
                color=_ownership_color(str(item.get("method_ownership", "unknown"))),
                alpha=0.82,
                edgecolor="black",
                linewidth=0.5,
            )
            axis.annotate(
                _short_label(str(item["method_label"])),
                (x_value, y_value),
                xytext=offset,
                textcoords="offset points",
                fontsize=7,
            )
        axis.set_xscale("log")
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Optimality gap vs oracle (lower is better)")
        axis.margins(x=0.12, y=0.14)
        axis.grid(True, alpha=0.2)
    axes[0].set_title("Model size vs theoretical gap")
    axes[1].set_title("Online runtime vs theoretical gap")
    figure.suptitle("SP1 quality-resource Pareto: neural/data-driven methods are not free", y=1.02)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_physical_cost_tradeoff(rows: list[dict[str, Any]], path: Path) -> None:
    """Plot physical travel/energy costs against recruitment quality."""

    if not rows:
        _draw_placeholder(path, "SP1 physical cost tradeoff", "No rows available")
        return
    summaries = _method_summaries(rows)
    figure, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    travel_points = []
    message_points = []
    for item in summaries:
        travel = _finite_or_floor(item.get("travel_distance_m", 0.0))
        success = _finite_or_floor(item.get("coalition_success_rate", 0.0))
        energy = _finite_or_floor(item.get("energy_proxy_wh", 0.0))
        gap = _finite_or_ceiling(item["optimality_gap_vs_oracle"])
        messages = _finite_or_floor(item.get("communication_messages", 0.0)) + 1.0
        travel_points.append((travel, success, energy, item))
        message_points.append((messages, gap, travel, item))
    travel_offsets = _annotation_offsets([(travel, success) for travel, success, _energy, _item in travel_points])
    message_offsets = _annotation_offsets([(messages, gap) for messages, gap, _travel, _item in message_points])
    for (travel, success, energy, item), offset in zip(travel_points, travel_offsets, strict=True):
        color = _ownership_color(str(item.get("method_ownership", "unknown")))
        axes[0].scatter(travel, success, s=45.0 + min(energy, 900.0) * 0.08, color=color, alpha=0.82, edgecolor="black", linewidth=0.5)
        axes[0].annotate(
            _short_label(str(item["method_label"])),
            (travel, success),
            xytext=offset,
            textcoords="offset points",
            fontsize=7,
        )
    for (messages, gap, travel, item), offset in zip(message_points, message_offsets, strict=True):
        color = _ownership_color(str(item.get("method_ownership", "unknown")))
        axes[1].scatter(messages, gap, s=55.0 + min(travel, 250.0) * 0.4, color=color, alpha=0.82, edgecolor="black", linewidth=0.5)
        axes[1].annotate(
            _short_label(str(item["method_label"])),
            (messages, gap),
            xytext=offset,
            textcoords="offset points",
            fontsize=7,
        )
    axes[0].set_xlabel("Mean recruitment travel distance m")
    axes[0].set_ylabel("Coalition success rate")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].margins(x=0.12)
    axes[0].set_title("Travel/energy vs coalition quality")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Communication messages + 1")
    axes[1].set_ylabel("Optimality gap vs oracle")
    axes[1].margins(x=0.12, y=0.14)
    axes[1].set_title("Communication vs theoretical gap")
    for axis in axes:
        axis.grid(True, alpha=0.2)
    figure.suptitle("SP1 physical and communication cost tradeoffs", y=1.02)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_recruitment_snapshot(world: WorldState, assignment: Assignment, path: Path, title: str) -> None:
    figure, axis = plt.subplots(figsize=(7, 7))
    _draw_world(axis, world, assignment, progress=1.0, title=title)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_recruitment_video(
    world: WorldState,
    assignment: Assignment,
    path: Path,
    title: str,
    fps: int = 12,
    *,
    duration_s: float = 24.0,
    final_hold_s: float = 6.0,
) -> bool:
    figure, axis = plt.subplots(figsize=(7, 7))
    frames = max(72, int(round(max(duration_s, 1.0) * max(fps, 1))))
    hold_frames = min(frames - 1, max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1)))))
    motion_frames = max(frames - hold_frames, 2)

    def draw(frame_idx: int) -> list[object]:
        axis.clear()
        progress = min(frame_idx, motion_frames - 1) / max(motion_frames - 1, 1)
        phase = "FINAL" if frame_idx >= motion_frames else f"t={progress:.2f}"
        _draw_world(axis, world, assignment, progress=progress, title=f"{title} | {phase}")
        return []

    animation = FuncAnimation(figure, draw, frames=frames, interval=1000 / max(fps, 1), blit=False)
    try:
        writer = FFMpegWriter(fps=fps, metadata={"title": title})
        animation.save(path, writer=writer, dpi=150)
        return True
    except Exception as exc:  # pragma: no cover - backend dependent
        path.with_suffix(".warning.txt").write_text(str(exc), encoding="utf-8")
        return False
    finally:
        plt.close(figure)


def _draw_world(axis: plt.Axes, world: WorldState, assignment: Assignment, progress: float, title: str) -> None:
    half = 0.5 * world.map.size_m
    axis.set_xlim(-half, half)
    axis.set_ylim(-half, half)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.18)
    axis.set_title(title, fontsize=10)
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(world.loads), 1)))
    labels = np.asarray(assignment.labels, dtype=int)
    starts = np.vstack([robot.position for robot in world.robots])
    targets = starts.copy()
    for load_idx, load in enumerate(world.loads):
        assigned = np.flatnonzero(labels == load_idx + 1)
        for order, robot_idx in enumerate(assigned):
            angle = 2.0 * np.pi * order / max(assigned.size, 1)
            targets[int(robot_idx)] = load.pickup + 0.32 * np.array([np.cos(angle), np.sin(angle)])
    eased = progress * progress * (3.0 - 2.0 * progress)
    current = starts + eased * (targets - starts)
    diagnostics = {row["load_index"] - 1: row for row in load_diagnostics(world, assignment)}
    for load_idx, load in enumerate(world.loads):
        status = diagnostics[load_idx]["status"]
        edge = {"UNDER": "#b42318", "OK": "#1a7f37", "OVER": "#b54708"}[status]
        axis.scatter(load.pickup[0], load.pickup[1], marker="s", s=170, color=colors[load_idx], edgecolor=edge, linewidth=1.8)
        axis.annotate(
            f"L{load_idx + 1}\n{load.mass_kg:.0f} kg\nneed {load.min_coalition_size}",
            load.pickup,
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
        )
    for robot_idx, robot in enumerate(world.robots):
        label = int(labels[robot_idx])
        color = "0.7" if label == 0 else colors[label - 1]
        if label > 0:
            axis.plot([starts[robot_idx, 0], targets[robot_idx, 0]], [starts[robot_idx, 1], targets[robot_idx, 1]], "--", color=color, alpha=0.55)
        axis.scatter(current[robot_idx, 0], current[robot_idx, 1], marker="o", s=60, color=color, edgecolor="black", linewidth=0.6)
        axis.annotate(f"R{robot_idx + 1}", current[robot_idx], xytext=(4, -8), textcoords="offset points", fontsize=6)


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_as_float(row.get(metric)) for row in rows], dtype=float)
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else math.nan


def _method_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for method in _ordered_methods(rows):
        group = [row for row in rows if str(row["method"]) == method]
        first = group[0]
        summaries.append(
            {
                "method": method,
                "method_label": first.get("method_label", method),
                "method_family": str(first.get("method_family", "unknown")),
                "method_scope": str(first.get("method_scope", "unknown")),
                "method_ownership": str(first.get("method_ownership", "unknown")),
                "demand_satisfaction_ratio": _mean_metric(group, "demand_satisfaction_ratio"),
                "coalition_success_rate": _mean_metric(group, "coalition_success_rate"),
                "served_load_rate": _mean_metric(group, "served_load_rate"),
                "optimality_gap_vs_oracle": _mean_metric(group, "optimality_gap_vs_oracle"),
                "robots_underassigned": _mean_metric(group, "robots_underassigned"),
                "robots_overassigned": _mean_metric(group, "robots_overassigned"),
                "travel_distance_m": _mean_metric(group, "travel_distance_m"),
                "estimated_arrival_time_s": _mean_metric(group, "estimated_arrival_time_s"),
                "energy_proxy_wh": _mean_metric(group, "energy_proxy_wh"),
                "communication_messages": _mean_metric(group, "communication_messages"),
                "runtime_ms": _mean_metric(group, "runtime_ms"),
                "method_trainable_parameters": _as_float(first.get("method_trainable_parameters", 0.0)),
                "method_training_episodes": _as_float(first.get("method_training_episodes", 0.0)),
            }
        )
    return summaries


def _best_summary(summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not summaries:
        return None
    return max(
        summaries,
        key=lambda row: (
            -_finite_or_ceiling(row["optimality_gap_vs_oracle"]),
            _finite_or_floor(row["coalition_success_rate"]),
            _finite_or_floor(row["served_load_rate"]),
            _finite_or_floor(row["demand_satisfaction_ratio"]),
            -_finite_or_ceiling(row["robots_underassigned"]),
            -_finite_or_ceiling(row["robots_overassigned"]),
            -_finite_or_ceiling(row["travel_distance_m"]),
            -_finite_or_ceiling(row["energy_proxy_wh"]),
            -_finite_or_ceiling(row["communication_messages"]),
            -_finite_or_ceiling(row["runtime_ms"]),
        ),
    )


def _summary_cell(summary: dict[str, Any] | None) -> str:
    if summary is None:
        return "n/a"
    label = _wrap_label(str(summary.get("method_label", summary.get("method", "unknown"))), width=24)
    return (
        f"{label}\n"
        f"D={summary['demand_satisfaction_ratio']:.3f}, "
        f"S={summary['coalition_success_rate']:.3f}, "
        f"G={summary['optimality_gap_vs_oracle']:.3f}, "
        f"T={summary['travel_distance_m']:.1f}m"
    )


def _plot_radius_lines(
    axis: plt.Axes,
    rows: list[dict[str, Any]],
    radius_labels: list[str],
    *,
    group_key: str,
    title: str,
) -> None:
    groups = _ordered_tokens({str(row.get(group_key, "unknown")) for row in rows}, group_key)
    x = np.arange(len(radius_labels))
    for group in groups:
        values = []
        for radius in radius_labels:
            selected = [
                row
                for row in rows
                if str(row.get(group_key, "unknown")) == group and _radius_label(row.get("communication_radius")) == radius
            ]
            values.append(_mean_metric(selected, "demand_satisfaction_ratio"))
        axis.plot(x, values, marker="o", linewidth=1.8, label=_pretty_token(group), color=_ownership_color(group))
    axis.set_xticks(x)
    axis.set_xticklabels(radius_labels)
    axis.set_title(title)
    axis.legend(fontsize=8)


def _scenarios_with_radius_variation(rows: list[dict[str, Any]]) -> set[str]:
    radii_by_scenario: dict[str, set[str]] = {}
    for row in rows:
        scenario = str(row.get("scenario_generator", "unknown"))
        radii_by_scenario.setdefault(scenario, set()).add(_radius_label(row.get("communication_radius")))
    return {scenario for scenario, radii in radii_by_scenario.items() if len(radii) > 1}


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    first_by_method: dict[str, dict[str, Any]] = {}
    for row in rows:
        first_by_method.setdefault(str(row["method"]), row)
    return [
        method
        for method, _row in sorted(
            first_by_method.items(),
            key=lambda item: (
                _token_rank(str(item[1].get("method_ownership", "unknown")), "method_ownership"),
                _token_rank(str(item[1].get("method_family", "unknown")), "method_family"),
                _token_rank(str(item[1].get("method_scope", "unknown")), "method_scope"),
                str(item[1].get("method_label", item[0])),
                item[0],
            ),
        )
    ]


def _ordered_tokens(tokens: set[str], key: str) -> list[str]:
    return sorted(tokens, key=lambda value: (_token_rank(value, key), value))


def _token_rank(value: str, key: str) -> int:
    orders = {
        "method_ownership": ["baseline", "proposed", "reference"],
        "method_family": ["classic", "sota", "model_based", "data_driven", "model_based_oracle", "unknown"],
        "method_scope": ["centralized", "decentralized", "decentralized_local", "unknown"],
    }
    try:
        return orders.get(key, []).index(value)
    except ValueError:
        return 999


def _ordered_radius_labels(labels: set[str]) -> list[str]:
    return sorted(labels, key=lambda label: (math.inf if label == "inf" else _as_float(label)))


def _radius_label(value: Any) -> str:
    numeric = _as_float(value)
    if np.isposinf(numeric):
        return "inf"
    if not np.isfinite(numeric):
        return "unknown"
    return f"{numeric:g}"


def _method_label(rows: list[dict[str, Any]], method: str) -> str:
    for row in rows:
        if str(row["method"]) == method:
            return f"{_taxonomy_label(row)}\n{_short_label(str(row.get('method_label', method)))}"
    return method


def _taxonomy_label(row: dict[str, Any]) -> str:
    ownership = _ownership_abbrev(str(row.get("method_ownership", "unknown")))
    family = _family_abbrev(str(row.get("method_family", "unknown")))
    scope = _scope_abbrev(str(row.get("method_scope", "unknown")))
    return f"{ownership}/{family}/{scope}"


def _ownership_abbrev(value: str) -> str:
    return {"baseline": "base", "proposed": "ours", "reference": "ref"}.get(value, value.replace("_", "-"))


def _family_abbrev(value: str) -> str:
    return {"model_based": "model", "model_based_oracle": "model-oracle", "model_based_reference": "model-ref", "data_driven": "data"}.get(value, value.replace("_", "-"))


def _scope_abbrev(value: str) -> str:
    return {"centralized": "cent", "decentralized": "decent", "decentralized_local": "decent-local"}.get(value, value.replace("_", "-"))


def _format_cell(value: float) -> str:
    if not np.isfinite(value):
        return "n/a"
    if abs(value) >= 100.0:
        return f"{value:.0f}"
    if abs(value) >= 10.0:
        return f"{value:.1f}"
    return f"{value:.3f}"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _finite_or_floor(value: Any) -> float:
    numeric = _as_float(value)
    return numeric if np.isfinite(numeric) else -math.inf


def _finite_or_ceiling(value: Any) -> float:
    numeric = _as_float(value)
    return numeric if np.isfinite(numeric) else math.inf


def _pretty_token(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


def _wrap_label(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(value.replace("_", " "), width=width, break_long_words=False)) or value


def _short_label(value: str) -> str:
    aliases = {
        "Centralized coalition oracle": "Oracle",
        "Oracle reference": "Oracle ref",
        "MAPPO recruitment checkpoint": "MAPPO",
        "Data-driven imitation oracle": "Imitation",
        "Primal-dual cardinality capacity": "PD capacity",
        "Primal-dual wrench market": "PD wrench",
        "Local primal-dual wrench market": "Local PD",
        "Hungarian expanded": "Hungarian",
        "Greedy nearest": "Greedy",
        "CBBA-like auction": "CBBA",
        "Replicator cardinality": "Replicator",
        "Smith cardinality": "Smith",
        "BNN cardinality": "BNN",
    }
    if value in aliases:
        return aliases[value]
    words = value.replace("_", " ").split()
    return " ".join(words[:2]) if words else value


def _annotation_offsets(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
    if not points:
        return []
    finite_x = np.asarray([x for x, _y in points if np.isfinite(x)], dtype=float)
    finite_y = np.asarray([y for _x, y in points if np.isfinite(y)], dtype=float)
    x_span = max(float(np.ptp(finite_x)) if finite_x.size else 1.0, 1e-9)
    y_span = max(float(np.ptp(finite_y)) if finite_y.size else 1.0, 1e-9)
    placed: list[tuple[float, float]] = []
    offsets: list[tuple[int, int]] = []
    candidates = [(6, -10), (6, 8), (-34, 8), (-34, -12), (10, 18), (-48, 18), (10, -22), (-48, -24)]
    for x_value, y_value in points:
        close = sum(
            abs(x_value - other_x) / x_span < 0.08 and abs(y_value - other_y) / y_span < 0.10
            for other_x, other_y in placed
        )
        offsets.append(candidates[min(close, len(candidates) - 1)])
        placed.append((x_value, y_value))
    return offsets


def _ownership_color(value: str) -> str:
    colors = {
        "baseline": "#65789b",
        "proposed": "#2a9d8f",
        "reference": "#c44536",
        "centralized": "#c44536",
        "decentralized": "#65789b",
        "decentralized_local": "#2a9d8f",
    }
    return colors.get(value, "#6f6f6f")


def _draw_placeholder(path: Path, title: str, message: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 3.5))
    axis.axis("off")
    axis.text(0.5, 0.58, title, ha="center", va="center", fontsize=13, weight="bold")
    axis.text(0.5, 0.4, message, ha="center", va="center", fontsize=10)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)
