"""Plots and videos for SP3 wrench-feasibility experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp3.methods import SP3Assignment, sp3_method_metadata
from viu_mrob_tfm.sp3.metrics import load_diagnostics
from viu_mrob_tfm.sp3.scenario import SP3Problem


def plot_scalar_vs_wrench_success(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    methods = [row["method"] for row in summaries]
    x = np.arange(len(methods))
    fig, ax = plt.subplots(figsize=(max(11, 0.95 * len(methods)), 4.8))
    ax.bar(x - 0.18, [row["scalar_feasible_rate"] for row in summaries], width=0.36, label="scalar feasible", color="#4c78a8")
    ax.bar(x + 0.18, [row["wrench_feasible_rate"] for row in summaries], width=0.36, label="wrench feasible", color="#54a24b")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title("SP3 scalar feasibility vs wrench feasibility")
    ax.set_xticks(x)
    ax.set_xticklabels([_short(method) for method in methods], rotation=30, ha="right", fontsize=7)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_false_positive_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    methods = _ordered_methods(rows)
    matrix = np.zeros((len(scenarios), len(methods)), dtype=float)
    for i, scenario in enumerate(scenarios):
        for j, method in enumerate(methods):
            matrix[i, j] = _mean([row for row in rows if row["scenario_generator"] == scenario and row["method"] == method], "false_positive_rate")
    fig, ax = plt.subplots(figsize=(max(11, 0.95 * len(methods)), max(4.5, 0.55 * len(scenarios))))
    image = ax.imshow(matrix, cmap="magma", vmin=0.0, vmax=max(1.0, float(np.nanmax(matrix)) if matrix.size else 1.0), aspect="auto")
    ax.set_title("SP3 false positive rate: scalar feasible but wrench infeasible")
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels([_short(method) for method in methods], rotation=30, ha="right", fontsize=7)
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_yticklabels([scenario.replace("_", " ") for scenario in scenarios])
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=7, color="white" if matrix[i, j] > 0.45 else "black")
    fig.colorbar(image, ax=ax, shrink=0.82)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_residual_wrench_by_method(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(11, 0.95 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["wrench_residual_norm"] for row in summaries], color="#e45756")
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1.0, label="feasibility tolerance")
    ax.set_ylabel("Mean normalized residual")
    ax.set_title("SP3 residual wrench by method")
    ax.tick_params(axis="x", rotation=30, labelsize=7)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_wrench_set_valid_vs_invalid(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for row in summaries:
        ax.scatter(
            row["fp_given_assigned"],
            row["wrench_residual_feasible_available"],
            s=80 + 80 * row["slot_coverage_ratio"],
            label=_short(row["method"]),
            alpha=0.82,
        )
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1.0)
    ax.set_xlabel("Infeasible assigned load rate")
    ax.set_ylabel("Residual on oracle-feasible loads")
    ax.set_title("SP3 invalid scalar coalitions vs valid wrench coalitions")
    ax.grid(True, alpha=0.22)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_precision_coverage(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    residuals = np.asarray([row["wrench_residual_feasible_available"] for row in summaries], dtype=float)
    finite_residuals = residuals[np.isfinite(residuals)]
    residual_scale = float(np.max(finite_residuals)) if finite_residuals.size else 1.0
    residual_scale = max(residual_scale, 1e-9)
    for row in summaries:
        residual = float(row["wrench_residual_feasible_available"])
        size = 70.0 + 180.0 * min(max(residual / residual_scale, 0.0), 1.0)
        ax.scatter(row["feasible_coverage"], row["precision_given_assigned"], s=size, alpha=0.82)
        ax.annotate(_short(row["method"]), (row["feasible_coverage"], row["precision_given_assigned"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.0, alpha=0.55)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.0, alpha=0.55)
    ax.set_xlim(-0.03, 1.08)
    ax.set_ylim(-0.03, 1.08)
    ax.set_xlabel("Feasible coverage vs strict wrench oracle")
    ax.set_ylabel("Precision among assigned loads")
    ax.set_title("SP3 precision-coverage: avoid abstention and scalar false positives")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_complementarity_gain(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    values = [_mean([row for row in rows if row["scenario_generator"] == scenario], "complementarity_gain") for scenario in scenarios]
    ax.bar([scenario.replace("_", " ") for scenario in scenarios], values, color="#72b7b2")
    ax.set_ylabel("Residual reduction")
    ax.set_title("SP3 complementarity: marginal value of multi-slot coalitions")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_quality_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    for row in summaries:
        ax.scatter(row["runtime_ms"], row["feasible_coverage"], s=80, alpha=0.82)
        ax.annotate(_short(row["method"]), (row["runtime_ms"], row["feasible_coverage"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Runtime ms")
    ax.set_ylabel("Feasible coverage vs oracle")
    ax.set_title("SP3 quality-resource Pareto")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_wrench_snapshot(problem: SP3Problem, assignment: SP3Assignment, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    _draw_problem(ax, problem, assignment, 1.0, title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_wrench_video(
    problem: SP3Problem,
    assignment: SP3Assignment,
    path: Path,
    title: str,
    *,
    fps: int = 10,
    duration_s: float = 28.0,
    final_hold_s: float = 8.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    frames = max(90, int(round(max(duration_s, 1.0) * max(fps, 1))))
    hold_frames = min(frames - 1, max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1)))))
    motion_frames = max(frames - hold_frames, 2)

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        progress = min(frame_idx, motion_frames - 1) / max(motion_frames - 1, 1)
        phase = "FINAL WRENCH STATE" if frame_idx >= motion_frames else f"t={progress:.2f}"
        _draw_problem(ax, problem, assignment, progress, f"{title} | {phase}")
        return []

    animation = FuncAnimation(fig, draw, frames=frames, interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=145)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_problem(ax: plt.Axes, problem: SP3Problem, assignment: SP3Assignment, progress: float, title: str) -> None:
    half = 0.5 * problem.world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(problem.world.loads), 1)))
    starts = np.vstack([robot.position for robot in problem.world.robots])
    targets = starts.copy()
    labels = np.asarray(assignment.labels, dtype=int)
    slot_labels = np.asarray(assignment.slot_labels, dtype=int)
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        load_idx = int(label) - 1
        slot_idx = int(slot_labels[robot_idx]) - 1
        if 0 <= load_idx < len(problem.world.loads) and 0 <= slot_idx < len(problem.load_slots[load_idx]):
            targets[robot_idx] = problem.world.loads[load_idx].pickup + problem.load_slots[load_idx][slot_idx].offset_xy
    smooth = progress * progress * (3.0 - 2.0 * progress)
    current = starts + smooth * (targets - starts)
    diagnostics = {row["load_index"] - 1: row for row in load_diagnostics(problem, assignment)}

    for load_idx, load in enumerate(problem.world.loads):
        color = colors[load_idx]
        diag = diagnostics[load_idx]
        load_xy = load.pickup
        ax.add_patch(
            plt.Rectangle(
                (load_xy[0] - 0.5 * load.length_m, load_xy[1] - 0.5 * load.width_m),
                load.length_m,
                load.width_m,
                facecolor=color,
                edgecolor="#1f2937" if diag["wrench_feasible"] else "#b42318",
                linewidth=1.8,
                alpha=0.22,
            )
        )
        ax.scatter(load_xy[0], load_xy[1], marker="s", s=60, color=color, edgecolor="black", linewidth=0.8)
        force = load.wrench.as_vector()[:2]
        tau = float(load.wrench.as_vector()[2])
        if np.linalg.norm(force) > 1e-9:
            ax.arrow(load_xy[0], load_xy[1], 0.025 * force[0], 0.025 * force[1], color="#111827", width=0.018, head_width=0.18, alpha=0.85)
        ax.annotate(
            f"L{load_idx + 1}\nscalar {'OK' if diag['scalar_feasible'] else 'NO'} | wrench {'OK' if diag['wrench_feasible'] else 'NO'}\nr={diag['wrench_residual_norm']:.3f}\ntau {tau:.0f}",
            load_xy,
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=7,
        )
        for slot_idx, slot in enumerate(problem.load_slots[load_idx]):
            slot_xy = load_xy + slot.offset_xy
            ax.scatter(slot_xy[0], slot_xy[1], marker="x", s=64, color=color, linewidth=1.7)
            ax.arrow(slot_xy[0], slot_xy[1], 0.55 * slot.direction_xy[0], 0.55 * slot.direction_xy[1], color=color, width=0.012, head_width=0.12, alpha=0.85)
            ax.annotate(f"S{slot_idx + 1}\n{slot.role}", slot_xy, xytext=(3, -14), textcoords="offset points", fontsize=5.8)
        if abs(tau) > 1e-9:
            theta = np.linspace(0.0, np.sign(tau) * 1.3 * np.pi, 45)
            radius = 0.52
            ax.plot(load_xy[0] + radius * np.cos(theta), load_xy[1] + radius * np.sin(theta), color="#7c2d12", linewidth=1.4)

    for robot_idx, robot in enumerate(problem.world.robots):
        label = int(labels[robot_idx])
        color = "0.72" if label == 0 else colors[label - 1]
        if label > 0:
            ax.plot([starts[robot_idx, 0], targets[robot_idx, 0]], [starts[robot_idx, 1], targets[robot_idx, 1]], "--", color=color, alpha=0.5)
        ax.scatter(current[robot_idx, 0], current[robot_idx, 1], marker="o", s=64, color=color, edgecolor="black", linewidth=0.6)
        ax.annotate(f"R{robot_idx + 1}\nF{robot.spec.capacity.force_limit_n:.0f}", current[robot_idx], xytext=(4, -13), textcoords="offset points", fontsize=6)


def _summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        output.append(
            {
                "method": method,
                "scalar_feasible_rate": _mean(selected, "scalar_feasible_rate"),
                "wrench_feasible_rate": _mean(selected, "wrench_feasible_rate"),
                "false_positive_rate": _mean(selected, "false_positive_rate"),
                "fp_given_assigned": _mean(selected, "fp_given_assigned"),
                "feasible_coverage": _mean(selected, "feasible_coverage"),
                "precision_given_assigned": _mean(selected, "precision_given_assigned"),
                "wrench_residual_norm": _mean(selected, "wrench_residual_norm"),
                "wrench_residual_feasible_available": _mean(selected, "wrench_residual_feasible_available"),
                "slot_coverage_ratio": _mean(selected, "slot_coverage_ratio"),
                "complementarity_gain": _mean(selected, "complementarity_gain"),
                "runtime_ms": _mean(selected, "runtime_ms"),
            }
        )
    return output


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    order = [
        "oracle_wrench_assignment",
        "wrench_oracle_reference",
        "oracle_scalar_assignment",
        "greedy_cardinality",
        "greedy_capacity",
        "wrench_greedy",
        "cbba_wrench_score",
        "smith_qr_capacity",
        "smith_qr_wrench",
    ]
    methods = {str(row["method"]) for row in rows}
    return [method for method in order if method in methods] + sorted(methods - set(order))


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else 0.0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _short(value: str) -> str:
    meta = sp3_method_metadata(value)
    aliases = {
        "oracle_wrench_assignment": "Wrench oracle",
        "wrench_oracle_reference": "Wrench ref",
        "oracle_scalar_assignment": "Scalar oracle",
        "greedy_cardinality": "Greedy cardinal",
        "greedy_capacity": "Greedy capacity",
        "wrench_greedy": "Wrench greedy",
        "cbba_wrench_score": "CBBA wrench",
        "smith_qr_capacity": "Smith capacity",
        "smith_qr_wrench": "Smith wrench",
    }
    method_label = aliases.get(value, value.replace("_assignment", "").replace("_", " "))
    return f"{_taxonomy_label(meta)}\n{method_label}"


def _taxonomy_label(meta: dict[str, Any]) -> str:
    ownership = _ownership_label(str(meta.get("ownership", "unknown")))
    family = _family_label(str(meta.get("family", "unknown")))
    scope = _scope_label(str(meta.get("scope", "unknown")))
    return f"{ownership}/{family}/{scope}"


def _ownership_label(value: str) -> str:
    return {"baseline": "base", "proposed": "ours", "reference": "ref"}.get(value, value.replace("_", "-"))


def _family_label(value: str) -> str:
    return {"model_based": "model", "model_based_reference": "model-ref", "model_based_oracle": "model-oracle", "data_driven": "data"}.get(value, value.replace("_", "-"))


def _scope_label(value: str) -> str:
    return {"centralized": "cent", "decentralized": "decent", "decentralized_local": "decent-local"}.get(value, value.replace("_", "-"))
