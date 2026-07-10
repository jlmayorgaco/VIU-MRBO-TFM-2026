"""Plots and videos for SP4 AMR motion and arrival experiments."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp4.methods import METHOD_META, SP4TrajectoryResult, sp4_method_metadata
from viu_mrob_tfm.sp4.scenario import SP4Problem


def plot_arrival_success(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8, 0.58 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["arrival_success_rate"] for row in summaries], color="#2a9d8f")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Arrival success rate")
    ax.set_title("SP4 AMR arrival success by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_collision_rate_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    methods = _ordered_methods(rows)
    matrix = np.zeros((len(scenarios), len(methods)), dtype=float)
    for i, scenario in enumerate(scenarios):
        for j, method in enumerate(methods):
            matrix[i, j] = _mean([row for row in rows if row["scenario_generator"] == scenario and row["method"] == method], "collision_rate")
    vmax = max(0.01, float(np.nanmax(matrix)) if matrix.size else 1.0)
    fig, ax = plt.subplots(figsize=(max(8, 0.72 * len(methods)), max(4.5, 0.55 * len(scenarios))))
    image = ax.imshow(matrix, cmap="magma", vmin=0.0, vmax=vmax, aspect="auto")
    ax.set_title("SP4 collision rate by scenario")
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels([_short(method) for method in methods], rotation=30, ha="right")
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_yticklabels([scenario.replace("_", " ") for scenario in scenarios])
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=7, color="white" if matrix[i, j] > 0.5 * vmax else "black")
    fig.colorbar(image, ax=ax, shrink=0.82)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_time_energy_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(7.8, 5.6))
    for row in summaries:
        ax.scatter(row["mean_arrival_time_s"], row["energy_proxy_wh"], s=70 + 150 * row["collision_rate"], alpha=0.84)
        ax.annotate(_short(row["method"]), (row["mean_arrival_time_s"], row["energy_proxy_wh"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Mean arrival time s")
    ax.set_ylabel("Energy proxy Wh")
    ax.set_title("SP4 time-energy-safety trade-off\nbubble size = collision rate")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_clearance_by_method(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    labels = [_short(row["method"]) for row in summaries]
    x = np.arange(len(summaries))
    fig, ax = plt.subplots(figsize=(max(8, 0.58 * len(summaries)), 4.8))
    ax.bar(x - 0.18, [row["min_robot_clearance_m"] for row in summaries], width=0.36, label="robot clearance", color="#4c78a8")
    ax.bar(x + 0.18, [row["min_obstacle_clearance_m"] for row in summaries], width=0.36, label="obstacle clearance", color="#f58518")
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_ylabel("Minimum clearance m")
    ax.set_title("SP4 minimum safety clearance by method")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_path_efficiency(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8, 0.58 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["path_efficiency_ratio"] for row in summaries], color="#72b7b2")
    ax.set_ylim(0.0, 1.08)
    ax.set_ylabel("Direct distance / path length")
    ax.set_title("SP4 path efficiency by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_communication_degradation(rows: list[dict[str, Any]], path: Path) -> None:
    labels = _ordered_radius_labels({_radius_label(row.get("communication_radius")) for row in rows})
    if len(labels) < 2:
        _placeholder(path, "SP4 communication degradation", "Fewer than two communication radii")
        return
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    for ownership in sorted({str(row.get("method_ownership", "unknown")) for row in rows}):
        values = []
        for label in labels:
            selected = [row for row in rows if str(row.get("method_ownership", "unknown")) == ownership and _radius_label(row.get("communication_radius")) == label]
            values.append(_mean(selected, "arrival_success_rate"))
        ax.plot(np.arange(len(labels)), values, marker="o", label=ownership)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel("Communication radius m")
    ax.set_ylabel("Arrival success rate")
    ax.set_title("SP4 degradation under reduced communication radius")
    ax.grid(True, alpha=0.22)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_motion_snapshot(problem: SP4Problem, result: SP4TrajectoryResult, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    _draw_frame(ax, problem, result, len(result.time_s) - 1, title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_motion_video(
    problem: SP4Problem,
    result: SP4TrajectoryResult,
    path: Path,
    title: str,
    *,
    fps: int = 12,
    duration_s: float = 26.0,
    final_hold_s: float = 6.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(7.4, 7.4))
    total = len(result.time_s)
    hold_frames = max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1))))
    motion_budget = max(2, int(round(max(duration_s - final_hold_s, 1.0) * max(fps, 1))))
    motion_frames = min(total, max(72, motion_budget))
    indices = np.linspace(0, total - 1, motion_frames).astype(int)
    if hold_frames > 0:
        indices = np.concatenate([indices, np.full(hold_frames, total - 1, dtype=int)])

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        idx = int(indices[frame_idx])
        phase = "FINAL" if frame_idx >= motion_frames else f"t={result.time_s[idx]:.1f}s"
        _draw_frame(ax, problem, result, idx, f"{title} | {phase}")
        return []

    animation = FuncAnimation(fig, draw, frames=len(indices), interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=145)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_frame(ax: plt.Axes, problem: SP4Problem, result: SP4TrajectoryResult, frame_idx: int, title: str) -> None:
    half = 0.5 * problem.world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(problem.world.robots), 1)))
    for obstacle in problem.world.map.obstacles:
        ax.add_patch(plt.Circle(obstacle.center, obstacle.influence_radius, facecolor="#f2f4f7", edgecolor="none", alpha=0.42))
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, facecolor="#8b949e", edgecolor="#344054", alpha=0.75))
    for idx, robot in enumerate(problem.world.robots):
        color = colors[idx % len(colors)]
        trail = result.positions[: frame_idx + 1, idx]
        ax.plot(trail[:, 0], trail[:, 1], color=color, linewidth=1.2, alpha=0.72)
        ax.scatter(result.positions[0, idx, 0], result.positions[0, idx, 1], marker="o", s=36, facecolor="white", edgecolor=color, linewidth=1.1)
        ax.scatter(problem.target_xy[idx, 0], problem.target_xy[idx, 1], marker="x", s=70, color=color, linewidth=1.7)
        reached = bool(result.reached[idx] and np.isfinite(result.arrival_times_s[idx]) and result.time_s[frame_idx] >= result.arrival_times_s[idx])
        ax.add_patch(plt.Circle(result.positions[frame_idx, idx], problem.robot_radius_m, facecolor=color, edgecolor="black", linewidth=0.6, alpha=0.86 if not reached else 0.48))
        ax.annotate(f"R{idx + 1}", result.positions[frame_idx, idx], xytext=(4, 4), textcoords="offset points", fontsize=6)
    arrived = int(np.sum(np.isfinite(result.arrival_times_s) & (result.arrival_times_s <= result.time_s[frame_idx])))
    ax.text(0.02, 0.98, f"arrived {arrived}/{len(problem.world.robots)}", transform=ax.transAxes, ha="left", va="top", fontsize=8, bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none"})


def _summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        first = selected[0]
        output.append(
            {
                "method": method,
                "method_label": first.get("method_label", method),
                "arrival_success_rate": _mean(selected, "arrival_success_rate"),
                "collision_rate": _mean(selected, "collision_rate"),
                "mean_arrival_time_s": _mean(selected, "mean_arrival_time_s"),
                "energy_proxy_wh": _mean(selected, "energy_proxy_wh"),
                "min_robot_clearance_m": _mean(selected, "min_robot_clearance_m"),
                "min_obstacle_clearance_m": _mean(selected, "min_obstacle_clearance_m"),
                "path_efficiency_ratio": _mean(selected, "path_efficiency_ratio"),
            }
        )
    return output


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    order = [
        "direct_to_target",
        "priority_yield",
        "apf_obstacle_avoidance",
        "velocity_obstacle_proxy",
        "cbf_safety_filter",
        "smith_motion_field",
        "energy_aware_smith_motion",
        "reference_time_expanded_cbf",
    ]
    methods = {str(row["method"]) for row in rows}
    return [method for method in order if method in methods] + sorted(methods - set(order))


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else math.nan


def _float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower == "true":
            return 1.0
        if lower == "false":
            return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _short(value: str) -> str:
    meta = sp4_method_metadata(value) if value in METHOD_META else {}
    label = meta.get("label", value)
    aliases = {
        "Direct to target": "Direct",
        "Priority yield": "Priority",
        "APF obstacle avoidance": "APF",
        "Velocity obstacle proxy": "VO",
        "CBF safety filter": "CBF",
        "Smith-QR motion field": "Smith",
        "Energy-aware Smith motion": "Energy Smith",
        "Reference time-expanded CBF": "Reference",
    }
    method_label = aliases.get(str(label), str(label))
    taxonomy = _taxonomy_label(meta)
    return f"{taxonomy}\n{method_label}"


def _taxonomy_label(meta: dict[str, Any]) -> str:
    ownership = _ownership_label(str(meta.get("ownership", "unknown")))
    family = _family_label(str(meta.get("family", "unknown")))
    scope = _scope_label(str(meta.get("scope", "unknown")))
    return f"{ownership}/{family}/{scope}"


def _ownership_label(value: str) -> str:
    return {"baseline": "base", "proposed": "ours", "reference": "ref"}.get(value, value.replace("_", "-"))


def _family_label(value: str) -> str:
    return {"model_based": "model", "model_based_reference": "model-ref", "data_driven": "data"}.get(value, value.replace("_", "-"))


def _scope_label(value: str) -> str:
    return {"centralized": "cent", "decentralized": "decent", "decentralized_local": "decent-local"}.get(value, value.replace("_", "-"))


def _radius_label(value: Any) -> str:
    val = _float(value)
    if np.isposinf(val):
        return "inf"
    return "unknown" if not np.isfinite(val) else f"{val:g}"


def _ordered_radius_labels(labels: set[str]) -> list[str]:
    return sorted(labels, key=lambda label: (math.inf if label == "inf" else _float(label)))


def _placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.55, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
