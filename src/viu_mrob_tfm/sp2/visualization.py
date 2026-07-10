"""Plots and videos for SP2 capacity-aware experiments."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.domain import WorldState
from viu_mrob_tfm.sp2.methods import sp2_method_metadata
from viu_mrob_tfm.sp2.metrics import load_diagnostics


PERFORMANCE_METRICS = [
    ("capacity_satisfaction_ratio", "Capacity", True),
    ("capacity_success_rate", "Loads OK", True),
    ("effective_feasibility_ratio", "Ceiling", True),
    ("optimality_gap_vs_oracle", "Score gap", False),
    ("capacity_gap_vs_capacity_oracle", "Capacity gap", False),
    ("signed_score_delta_vs_oracle", "Score delta", True),
    ("under_capacity_kg", "Under kg", False),
    ("over_capacity_kg", "Over kg", False),
    ("capacity_waste_ratio", "Waste", False),
    ("incomplete_capacity_ratio", "Incomplete cap.", False),
    ("served_capacity_alignment", "Served cap. align.", True),
    ("travel_distance_m", "Travel m", False),
    ("estimated_arrival_time_s", "Arrival s", False),
    ("energy_proxy_wh", "Energy Wh", False),
    ("communication_messages", "Messages", False),
    ("communication_coverage_ratio", "Comm cover", True),
    ("runtime_ms", "Runtime ms", False),
]


def plot_summary_bars(rows: list[dict[str, Any]], path: Path, metric: str = "capacity_satisfaction_ratio") -> None:
    if not rows:
        _placeholder(path, "SP2 summary", "No rows available")
        return
    grouped = {method: [float(row[metric]) for row in rows if str(row["method"]) == method] for method in _ordered_methods(rows)}
    labels = [_method_label(rows, method) for method in grouped]
    values = [float(np.mean(values)) if values else math.nan for values in grouped.values()]
    fig, ax = plt.subplots(figsize=(11, 5.0))
    ax.bar(labels, values, color="#2a9d8f")
    ax.set_ylabel(metric)
    ax.set_title(f"SP2 capacity-aware Monte Carlo: {metric}")
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    if metric.endswith("ratio") or metric.endswith("rate"):
        ax.set_ylim(0.0, 1.05)
    ax.grid(True, axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_capacity_regime_interaction(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 capacity regime", "No rows available")
        return
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        xs = np.asarray([float(row["capacity_ratio"]) for row in selected], dtype=float)
        ys = np.asarray([float(row["capacity_satisfaction_ratio"]) for row in selected], dtype=float)
        bins = np.linspace(0.4, 1.5, 6)
        centers = 0.5 * (bins[:-1] + bins[1:])
        means = []
        for left, right in zip(bins[:-1], bins[1:]):
            mask = (xs >= left) & (xs < right)
            means.append(float(np.mean(ys[mask])) if np.any(mask) else np.nan)
        ax.plot(centers, means, marker="o", linewidth=1.4, label=_short_label(_method_label(rows, method)))
    ax.set_xlabel("Capacity demand ratio")
    ax.set_ylabel("Capacity satisfaction ratio")
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=7, ncols=2)
    ax.set_title("SP2 degradation as aggregate load capacity demand rises")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_method_performance_matrix(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 performance matrix", "No rows available")
        return
    methods = _ordered_methods(rows)
    raw = np.zeros((len(methods), len(PERFORMANCE_METRICS)), dtype=float)
    for i, method in enumerate(methods):
        selected = [row for row in rows if str(row["method"]) == method]
        for j, (metric, _label, _hib) in enumerate(PERFORMANCE_METRICS):
            raw[i, j] = _mean(selected, metric)
    norm = np.zeros_like(raw)
    for j, (_metric, _label, higher) in enumerate(PERFORMANCE_METRICS):
        values = raw[:, j]
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            continue
        low, high = float(np.min(finite)), float(np.max(finite))
        if math.isclose(low, high):
            norm[:, j] = 1.0
        elif higher:
            norm[:, j] = (values - low) / (high - low)
        else:
            norm[:, j] = (high - values) / (high - low)
    fig, ax = plt.subplots(figsize=(13.6, max(5.2, 0.36 * len(methods) + 2.0)))
    image = ax.imshow(norm, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xticks(np.arange(len(PERFORMANCE_METRICS)))
    ax.set_xticklabels([label for _m, label, _h in PERFORMANCE_METRICS], rotation=25, ha="right")
    ax.set_yticks(np.arange(len(methods)))
    ax.set_yticklabels([_method_label(rows, method) for method in methods], fontsize=8)
    for i in range(len(methods)):
        for j in range(len(PERFORMANCE_METRICS)):
            color = "white" if norm[i, j] < 0.45 else "black"
            ax.text(j, i, _format(raw[i, j]), ha="center", va="center", fontsize=7, color=color)
    ax.set_title("SP2 performance matrix by method (mean over runs)")
    ax.set_xlabel("Metric; color normalized within metric")
    fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02, label="Normalized quality")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_quality_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 quality-resource Pareto", "No rows available")
        return
    summaries = _summaries(rows)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    for ax, x_key, xlabel in [
        (axes[0], "method_trainable_parameters", "Trainable execution parameters + 1"),
        (axes[1], "runtime_ms", "Online runtime ms + 1"),
    ]:
        points = []
        for item in summaries:
            points.append((_finite(item.get(x_key, 0.0)) + 1.0, _finite(item["optimality_gap_vs_oracle"]), item))
        offsets = _annotation_offsets([(x, y) for x, y, _ in points])
        for (x, y, item), offset in zip(points, offsets, strict=True):
            ax.scatter(x, y, s=60, color=_ownership_color(str(item["method_ownership"])), edgecolor="black", linewidth=0.5, alpha=0.85)
            ax.annotate(_short_label(str(item["method_label"])), (x, y), xytext=offset, textcoords="offset points", fontsize=7)
        ax.set_xscale("log")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Optimality gap vs capacity oracle")
        ax.margins(x=0.12, y=0.14)
        ax.grid(True, alpha=0.2)
    axes[0].set_title("Model size vs capacity gap")
    axes[1].set_title("Online runtime vs capacity gap")
    fig.suptitle("SP2 capacity quality-resource Pareto", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_capacity_cost_tradeoff(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 capacity-cost tradeoff", "No rows available")
        return
    summaries = _summaries(rows)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    p0 = [(_finite(s["travel_distance_m"]), _finite(s["capacity_success_rate"]), _finite(s["energy_proxy_wh"]), s) for s in summaries]
    p1 = [(_finite(s["under_capacity_kg"]), _finite(s["over_capacity_kg"]), s) for s in summaries]
    for (x, y, energy, item), offset in zip(p0, _annotation_offsets([(x, y) for x, y, _e, _i in p0]), strict=True):
        axes[0].scatter(x, y, s=55 + min(energy, 900.0) * 0.08, color=_ownership_color(str(item["method_ownership"])), edgecolor="black", alpha=0.85)
        axes[0].annotate(_short_label(str(item["method_label"])), (x, y), xytext=offset, textcoords="offset points", fontsize=7)
    for (x, y, item), offset in zip(p1, _annotation_offsets([(x, y) for x, y, _i in p1]), strict=True):
        axes[1].scatter(x, y, s=70, color=_ownership_color(str(item["method_ownership"])), edgecolor="black", alpha=0.85)
        axes[1].annotate(_short_label(str(item["method_label"])), (x, y), xytext=offset, textcoords="offset points", fontsize=7)
    axes[0].set_xlabel("Mean recruitment travel distance m")
    axes[0].set_ylabel("Capacity success rate")
    axes[0].set_ylim(0.0, 1.05)
    axes[0].set_title("Travel/energy vs capacity success")
    axes[1].set_xlabel("Under-capacity kg")
    axes[1].set_ylabel("Over-capacity kg")
    axes[1].set_title("Shortage vs wasted effective capacity")
    for ax in axes:
        ax.grid(True, alpha=0.2)
        ax.margins(x=0.12, y=0.14)
    fig.suptitle("SP2 physical capacity and cost tradeoffs", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_capacity_coverage_vs_completion(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 coverage-completion", "No rows available")
        return
    summaries = _summaries(rows)
    points = [
        (
            _finite(item["capacity_satisfaction_ratio"]),
            _finite(item["capacity_success_rate"]),
            _finite(item.get("incomplete_capacity_ratio", 0.0)),
            item,
        )
        for item in summaries
    ]
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    offsets = _annotation_offsets([(x, y) for x, y, _z, _item in points])
    for (x, y, incomplete_ratio, item), offset in zip(points, offsets, strict=True):
        offset = {
            "oracle_reference": (12, -10),
            "capacity_oracle_reference": (12, -12),
            "replicator_capacity_marginal": (12, -18),
            "smith_capacity_marginal": (12, 8),
            "replicator_capacity_plain": (12, -28),
            "smith_capacity_plain": (-72, -10),
        }.get(str(item["method"]), offset)
        size = 70.0 + 260.0 * max(0.0, min(float(incomplete_ratio), 1.0))
        ax.scatter(
            x,
            y,
            s=size,
            color=_ownership_color(str(item["method_ownership"])),
            edgecolor="black",
            linewidth=0.6,
            alpha=0.86,
        )
        ax.annotate(_short_label(str(item["method_label"])), (x, y), xytext=offset, textcoords="offset points", fontsize=7)
    ax.set_xlabel("Capacity satisfaction ratio")
    ax.set_ylabel("Capacity success rate")
    ax.set_xlim(0.0, 1.05)
    ax.set_ylim(0.0, 1.05)
    ax.grid(True, alpha=0.2)
    ax.set_title("SP2 coverage-completion trade-off\nbubble size = capacity assigned to incomplete loads")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_communication_degradation(rows: list[dict[str, Any]], path: Path) -> None:
    labels = _ordered_radius_labels({_radius_label(row.get("communication_radius")) for row in rows})
    if len(labels) < 2:
        _placeholder(path, "SP2 communication degradation", "Fewer than two radii")
        return
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
    for ax, key, title in [(axes[0], "method_ownership", "By ownership"), (axes[1], "method_scope", "By scope")]:
        groups = sorted({str(row.get(key, "unknown")) for row in rows})
        for group in groups:
            values = []
            for label in labels:
                selected = [row for row in rows if str(row.get(key, "unknown")) == group and _radius_label(row.get("communication_radius")) == label]
                values.append(_mean(selected, "capacity_satisfaction_ratio"))
            ax.plot(np.arange(len(labels)), values, marker="o", label=group, color=_ownership_color(group))
        ax.set_xticks(np.arange(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_title(title)
        ax.grid(True, alpha=0.2)
        ax.set_xlabel("Communication radius m")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Capacity satisfaction ratio")
    axes[0].set_ylim(0.0, 1.05)
    fig.suptitle("SP2 degradation under reduced communication radius", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_best_method_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        _placeholder(path, "SP2 best method", "No rows available")
        return
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    table_rows = []
    for scenario in scenarios:
        summaries = _summaries([row for row in rows if str(row["scenario_generator"]) == scenario])
        table_rows.append(
            [
                scenario.replace("_", " ").title(),
                _summary_cell(_best(summaries)),
                _summary_cell(_best([s for s in summaries if s["method_ownership"] == "reference"])),
                _summary_cell(_best([s for s in summaries if s["method_ownership"] == "proposed"])),
                _summary_cell(_best([s for s in summaries if s["method_ownership"] == "baseline"])),
            ]
        )
    fig, ax = plt.subplots(figsize=(14.5, max(3.4, 0.8 * len(table_rows) + 1.9)))
    ax.axis("off")
    table = ax.table(
        cellText=table_rows,
        colLabels=["Scenario", "Best overall", "Reference", "Best proposed", "Best baseline"],
        loc="center",
        cellLoc="left",
        colWidths=[0.16, 0.22, 0.22, 0.22, 0.22],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.9)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#333333")
        elif c == 3:
            cell.set_facecolor("#e8f4f1")
        elif c == 2:
            cell.set_facecolor("#f8ebe8")
    ax.set_title("SP2 best method by scenario: capacity gap, success, shortage, waste, cost")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_capacity_snapshot(world: WorldState, assignment: Assignment, path: Path, title: str, *, communication_radius: float = float("inf"), distance_decay_m: float = 22.0) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    _draw_world(ax, world, assignment, 1.0, title, communication_radius=communication_radius, distance_decay_m=distance_decay_m)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_capacity_video(
    world: WorldState,
    assignment: Assignment,
    path: Path,
    title: str,
    *,
    communication_radius: float = float("inf"),
    distance_decay_m: float = 22.0,
    fps: int = 12,
    duration_s: float = 24.0,
    final_hold_s: float = 6.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(7, 7))
    frames = max(72, int(round(max(duration_s, 1.0) * max(fps, 1))))
    hold_frames = min(frames - 1, max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1)))))
    motion_frames = max(frames - hold_frames, 2)

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        progress = min(frame_idx, motion_frames - 1) / max(motion_frames - 1, 1)
        phase = "FINAL" if frame_idx >= motion_frames else f"t={progress:.2f}"
        _draw_world(ax, world, assignment, progress, f"{title} | {phase}", communication_radius=communication_radius, distance_decay_m=distance_decay_m)
        return []

    animation = FuncAnimation(fig, draw, frames=frames, interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=150)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_world(ax: plt.Axes, world: WorldState, assignment: Assignment, progress: float, title: str, *, communication_radius: float, distance_decay_m: float) -> None:
    half = 0.5 * world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    labels = np.asarray(assignment.labels, dtype=int)
    starts = np.vstack([robot.position for robot in world.robots])
    targets = starts.copy()
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(world.loads), 1)))
    diagnostics = {row["load_index"] - 1: row for row in load_diagnostics(world, assignment, communication_radius=communication_radius, distance_decay_m=distance_decay_m)}
    for load_idx, load in enumerate(world.loads):
        assigned = np.flatnonzero(labels == load_idx + 1)
        for order, robot_idx in enumerate(assigned):
            angle = 2.0 * np.pi * order / max(assigned.size, 1)
            targets[int(robot_idx)] = load.pickup + 0.38 * np.array([np.cos(angle), np.sin(angle)])
    smooth = progress * progress * (3.0 - 2.0 * progress)
    current = starts + smooth * (targets - starts)
    for load_idx, load in enumerate(world.loads):
        diag = diagnostics[load_idx]
        status = str(diag["status"])
        edge = {"UNDER": "#b42318", "OK": "#1a7f37", "OVER": "#b54708"}[status]
        ax.scatter(load.pickup[0], load.pickup[1], marker="s", s=190, color=colors[load_idx], edgecolor=edge, linewidth=1.9)
        ax.annotate(
            f"L{load_idx + 1}\n{load.mass_kg:.0f} kg\nreq {diag['required_capacity_kg']:.0f}\neff {diag['assigned_effective_capacity_kg']:.0f}",
            load.pickup,
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
        )
    for robot_idx, robot in enumerate(world.robots):
        label = int(labels[robot_idx])
        color = "0.72" if label == 0 else colors[label - 1]
        if label > 0:
            ax.plot([starts[robot_idx, 0], targets[robot_idx, 0]], [starts[robot_idx, 1], targets[robot_idx, 1]], "--", color=color, alpha=0.55)
        ax.scatter(current[robot_idx, 0], current[robot_idx, 1], marker="o", s=62, color=color, edgecolor="black", linewidth=0.6)
        ax.annotate(
            f"R{robot_idx + 1}\n{robot.spec.capacity.payload_kg:.0f}kg\nb{robot.battery_fraction:.2f}",
            current[robot_idx],
            xytext=(4, -13),
            textcoords="offset points",
            fontsize=6,
        )


def _summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        first = selected[0]
        summaries.append(
            {
                "method": method,
                "method_label": first.get("method_label", method),
                "method_ownership": str(first.get("method_ownership", "unknown")),
                "capacity_satisfaction_ratio": _mean(selected, "capacity_satisfaction_ratio"),
                "capacity_success_rate": _mean(selected, "capacity_success_rate"),
                "optimality_gap_vs_oracle": _mean(selected, "optimality_gap_vs_oracle"),
                "under_capacity_kg": _mean(selected, "under_capacity_kg"),
                "over_capacity_kg": _mean(selected, "over_capacity_kg"),
                "incomplete_capacity_ratio": _mean(selected, "incomplete_capacity_ratio"),
                "served_capacity_alignment": _mean(selected, "served_capacity_alignment"),
                "travel_distance_m": _mean(selected, "travel_distance_m"),
                "energy_proxy_wh": _mean(selected, "energy_proxy_wh"),
                "runtime_ms": _mean(selected, "runtime_ms"),
                "method_trainable_parameters": _float(first.get("method_trainable_parameters", 0.0)),
            }
        )
    return summaries


def _best(summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not summaries:
        return None
    return max(
        summaries,
        key=lambda row: (
            -_finite(row["optimality_gap_vs_oracle"]),
            _finite(row["capacity_success_rate"]),
            _finite(row["capacity_satisfaction_ratio"]),
            -_finite(row["under_capacity_kg"]),
            -_finite(row["over_capacity_kg"]),
            -_finite(row["travel_distance_m"]),
            -_finite(row["runtime_ms"]),
        ),
    )


def _summary_cell(row: dict[str, Any] | None) -> str:
    if row is None:
        return "n/a"
    return (
        f"{str(row['method_label']).replace('_', ' ')}\n"
        f"C={row['capacity_satisfaction_ratio']:.3f}, "
        f"S={row['capacity_success_rate']:.3f}, "
        f"G={row['optimality_gap_vs_oracle']:.3f}, "
        f"U={row['under_capacity_kg']:.1f}kg"
    )


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    first = {}
    for row in rows:
        first.setdefault(str(row["method"]), row)
    return [
        method
        for method, row in sorted(
            first.items(),
            key=lambda item: (
                _rank(str(item[1].get("method_ownership", "unknown")), ["baseline", "proposed", "reference"]),
                _rank(str(item[1].get("method_family", "unknown")), ["classic", "sota", "model_based", "data_driven", "model_based_oracle"]),
                str(item[1].get("method_label", item[0])),
            ),
        )
    ]


def _method_label(rows: list[dict[str, Any]], method: str) -> str:
    for row in rows:
        if str(row["method"]) == method:
            label = _short_label(str(row.get("method_label", method)))
            return f"{_taxonomy_label(row, method)}\n{label}"
    return f"{_taxonomy_label({}, method)}\n{_short_label(method)}"


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    vals = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    vals = vals[np.isfinite(vals)]
    return float(np.mean(vals)) if vals.size else math.nan


def _format(value: float) -> str:
    if not np.isfinite(value):
        return "n/a"
    if abs(value) >= 100.0:
        return f"{value:.0f}"
    if abs(value) >= 10.0:
        return f"{value:.1f}"
    return f"{value:.3f}"


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _finite(value: Any) -> float:
    numeric = _float(value)
    return numeric if np.isfinite(numeric) else math.inf


def _rank(value: str, order: list[str]) -> int:
    try:
        return order.index(value)
    except ValueError:
        return 999


def _ownership_color(value: str) -> str:
    return {"baseline": "#65789b", "proposed": "#2a9d8f", "reference": "#c44536", "centralized": "#c44536", "decentralized": "#65789b", "decentralized_local": "#2a9d8f"}.get(value, "#777777")


def _taxonomy_label(row: dict[str, Any], method: str) -> str:
    meta = sp2_method_metadata(method)
    ownership = _ownership_label(str(row.get("method_ownership", meta.get("ownership", "unknown"))))
    family = _family_label(str(row.get("method_family", meta.get("family", "unknown"))))
    scope = _scope_label(str(row.get("method_scope", meta.get("scope", "unknown"))))
    return f"{ownership}/{family}/{scope}"


def _ownership_label(value: str) -> str:
    return {"baseline": "base", "proposed": "ours", "reference": "ref"}.get(value, value.replace("_", "-"))


def _family_label(value: str) -> str:
    return {"model_based": "model", "model_based_reference": "model-ref", "model_based_oracle": "model-oracle", "data_driven": "data"}.get(value, value.replace("_", "-"))


def _scope_label(value: str) -> str:
    return {"centralized": "cent", "decentralized": "decent", "decentralized_local": "decent-local"}.get(value, value.replace("_", "-"))


def _short_label(value: str) -> str:
    aliases = {
        "Centralized capacity oracle": "Oracle",
        "Oracle reference": "Oracle ref",
        "Greedy capacity nearest": "Greedy",
        "Hungarian capacity expanded": "Hungarian",
        "CBBA capacity auction": "CBBA",
        "Replicator capacity": "Replicator",
        "Replicator capacity plain payoff": "Repl plain",
        "Replicator capacity marginal payoff": "Repl marginal",
        "BNN capacity": "BNN",
        "Smith-QR capacity": "Smith-QR",
        "Smith-QR capacity plain payoff": "Smith plain",
        "Smith-QR capacity marginal payoff": "Smith marginal",
        "Primal-dual capacity": "PD",
        "Local primal-dual capacity": "Local PD",
        "Data-driven capacity imitation": "Imitation",
        "Neural capacity scorer": "Neural",
    }
    return aliases.get(value, " ".join(value.replace("_", " ").split()[:2]))


def _radius_label(value: Any) -> str:
    val = _float(value)
    if np.isposinf(val):
        return "inf"
    return "unknown" if not np.isfinite(val) else f"{val:g}"


def _ordered_radius_labels(labels: set[str]) -> list[str]:
    return sorted(labels, key=lambda label: (math.inf if label == "inf" else _float(label)))


def _annotation_offsets(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
    if not points:
        return []
    finite_x = np.asarray([x for x, _y in points if np.isfinite(x)], dtype=float)
    finite_y = np.asarray([y for _x, y in points if np.isfinite(y)], dtype=float)
    x_span = max(float(np.ptp(finite_x)) if finite_x.size else 1.0, 1e-9)
    y_span = max(float(np.ptp(finite_y)) if finite_y.size else 1.0, 1e-9)
    offsets = []
    placed = []
    candidates = [(6, -10), (6, 8), (-36, 8), (-36, -12), (12, 18), (-52, 18), (12, -22), (-52, -24)]
    for x, y in points:
        close = sum(abs(x - px) / x_span < 0.08 and abs(y - py) / y_span < 0.10 for px, py in placed)
        offsets.append(candidates[min(close, len(candidates) - 1)])
        placed.append((x, y))
    return offsets


def _placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.55, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
