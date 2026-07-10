"""Plots and videos for SP6 operational robustness experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp6.methods import SP6TrajectoryResult, sp6_method_metadata
from viu_mrob_tfm.sp6.scenario import SP6Problem


def plot_recovery_success_by_method(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8.0, 0.70 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["recovery_success"] for row in summaries], color="#2a9d8f")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Recovery success rate")
    ax.set_title("SP6 robustness recovery success by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_degradation_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    methods = _ordered_methods(rows)
    if not scenarios or not methods:
        _placeholder(path, "SP6 degradation by scenario", "No runs")
        return
    matrix = np.zeros((len(scenarios), len(methods)), dtype=float)
    for i, scenario in enumerate(scenarios):
        for j, method in enumerate(methods):
            matrix[i, j] = _mean([row for row in rows if row["scenario_generator"] == scenario and row["method"] == method], "lost_load_rate")
    fig, ax = plt.subplots(figsize=(max(8.0, 0.72 * len(methods)), max(4.6, 0.55 * len(scenarios))))
    image = ax.imshow(matrix, cmap="magma", vmin=0.0, vmax=max(1.0, float(np.nanmax(matrix)) if matrix.size else 1.0), aspect="auto")
    ax.set_title("SP6 lost-load degradation by scenario")
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels([_short(method) for method in methods], rotation=30, ha="right")
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_yticklabels([scenario.replace("_", " ") for scenario in scenarios])
    for i in range(len(scenarios)):
        for j in range(len(methods)):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=7, color="white" if matrix[i, j] > 0.45 else "black")
    fig.colorbar(image, ax=ax, shrink=0.82)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_recovery_time_by_method(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8.0, 0.70 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["recovery_time_s"] for row in summaries], color="#4c78a8")
    ax.set_ylabel("Recovery time s")
    ax.set_title("SP6 recovery time by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_safety_by_method(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    labels = [_short(row["method"]) for row in summaries]
    x = np.arange(len(summaries))
    fig, ax1 = plt.subplots(figsize=(max(8.0, 0.70 * len(summaries)), 4.8))
    ax1.bar(x - 0.18, [row["collision_rate"] for row in summaries], width=0.36, color="#e45756", label="collision rate")
    ax1.set_ylabel("Collision rate")
    ax2 = ax1.twinx()
    ax2.bar(x + 0.18, [row["min_obstacle_clearance_m"] for row in summaries], width=0.36, color="#72b7b2", label="min obstacle clearance m")
    ax2.set_ylabel("Min obstacle clearance m")
    ax1.set_title("SP6 safety diagnostics by method")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha="right")
    ax1.grid(True, axis="y", alpha=0.22)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_communication_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    for row in summaries:
        meta = sp6_method_metadata(str(row["method"]))
        marker = "s" if meta["scope"] == "centralized" else "o"
        ax.scatter(row["communication_messages"], row["score_value"], s=70 + 180 * row["collision_rate"], marker=marker, alpha=0.84)
        ax.annotate(_short(row["method"]), (row["communication_messages"], row["score_value"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Communication messages")
    ax.set_ylabel("Recovery score")
    ax.set_title("SP6 quality-resource Pareto\nbubble size = collision rate, square = centralized")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_completion_vs_reassignment(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    for row in summaries:
        ax.scatter(row["reassignment_count"], row["task_completion_rate"], s=70 + 160 * row["post_event_wrench_feasible_rate"], alpha=0.84)
        ax.annotate(_short(row["method"]), (row["reassignment_count"], row["task_completion_rate"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Reassignment count")
    ax.set_ylabel("Task completion rate")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("SP6 completion versus repair activity\nbubble size = final physical feasibility")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_recovery_snapshot(problem: SP6Problem, result: SP6TrajectoryResult, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 7.5))
    _draw_frame(ax, problem, result, len(result.time_s) - 1, title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_recovery_video(
    problem: SP6Problem,
    result: SP6TrajectoryResult,
    path: Path,
    title: str,
    *,
    fps: int = 10,
    duration_s: float = 42.0,
    final_hold_s: float = 8.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(8.2, 7.5))
    total = len(result.time_s)
    hold_frames = max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1))))
    motion_budget = max(2, int(round(max(duration_s - final_hold_s, 1.0) * max(fps, 1))))
    motion_frames = min(total, max(100, motion_budget))
    indices = np.linspace(0, total - 1, motion_frames).astype(int)
    if hold_frames > 0:
        indices = np.concatenate([indices, np.full(hold_frames, total - 1, dtype=int)])

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        idx = int(indices[frame_idx])
        phase = "FINAL RECOVERY STATE" if frame_idx >= motion_frames else ("post-event" if result.time_s[idx] >= problem.event.time_s else "pre-event")
        _draw_frame(ax, problem, result, idx, f"{title} | {phase} t={result.time_s[idx]:.1f}s")
        return []

    animation = FuncAnimation(fig, draw, frames=len(indices), interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=135)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_frame(ax: plt.Axes, problem: SP6Problem, result: SP6TrajectoryResult, frame_idx: int, title: str) -> None:
    half = 0.5 * problem.world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    t_s = float(result.time_s[frame_idx])

    for obstacle in problem.active_obstacles_at(t_s):
        ax.add_patch(plt.Circle(obstacle.center, obstacle.influence_radius, facecolor="#f2f4f7", edgecolor="none", alpha=0.36))
        face = "#8b949e" if obstacle is not problem.event.blocked_obstacle else "#dc2626"
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, facecolor=face, edgecolor="#344054", alpha=0.74))

    for load_idx, load in enumerate(problem.world.loads):
        feasible = bool(result.feasible_after_event[load_idx])
        completed = bool(result.completed_loads[frame_idx, load_idx])
        color = "#15803d" if completed else ("#1d4ed8" if feasible else "#b91c1c")
        _draw_payload(ax, load.length_m, load.width_m, problem.initial_load_poses[load_idx], edge="#94a3b8", face="none", linestyle="--", label="initial" if load_idx == 0 else None)
        _draw_payload(ax, load.length_m, load.width_m, problem.target_load_poses[load_idx], edge="#15803d", face="none", linestyle=":", label="target" if load_idx == 0 else None)
        _draw_payload(ax, load.length_m, load.width_m, result.load_pose[frame_idx, load_idx], edge="#1f2937", face="#bfdbfe" if feasible else "#fecaca", linestyle="-", label="payload" if load_idx == 0 else None)
        ax.scatter(load.destination[0], load.destination[1], marker="*", s=150, color=color, edgecolor="black", linewidth=0.5, zorder=4)
        ax.scatter(load.pickup[0], load.pickup[1], marker="s", s=48, facecolor="white", edgecolor=color, linewidth=1.0)
        ax.annotate(f"L{load_idx + 1}\n{'DONE' if completed else ('OK' if feasible else 'INF')}\nwm={result.wrench_margins[frame_idx, load_idx]:.2f}", result.load_pose[frame_idx, load_idx, :2], xytext=(6, 5), textcoords="offset points", fontsize=7, color=color)
        slots = _slot_positions(problem, load_idx, result.load_pose[frame_idx, load_idx])
        if slots.size:
            ax.scatter(slots[:, 0], slots[:, 1], marker="x", s=46, color="#1d4ed8", linewidth=1.2, zorder=5)

    colors = plt.cm.tab20(np.linspace(0.0, 1.0, max(len(problem.world.robots), 1)))
    labels = np.asarray(result.labels[frame_idx], dtype=int)
    active = np.asarray(result.active_mask[frame_idx], dtype=bool)
    battery = np.asarray(result.battery_fraction[frame_idx], dtype=float)
    positions = result.robot_positions[frame_idx]
    for idx, robot in enumerate(problem.world.robots):
        color = colors[idx % len(colors)]
        trail = result.robot_positions[: frame_idx + 1, idx]
        ax.plot(trail[:, 0], trail[:, 1], color=color, linewidth=1.0, alpha=0.48)
        ax.scatter(result.robot_positions[0, idx, 0], result.robot_positions[0, idx, 1], marker="o", s=28, facecolor="white", edgecolor=color, linewidth=1.0)
        face = color if active[idx] else "#9ca3af"
        alpha = 0.88 if active[idx] else 0.45
        ax.add_patch(plt.Circle(positions[idx], problem.robot_radius_m, facecolor=face, edgecolor="black", linewidth=0.55, alpha=alpha))
        label = f"R{idx + 1}\nL{labels[idx]}" if labels[idx] > 0 else f"R{idx + 1}\nidle"
        if not active[idx]:
            label = f"R{idx + 1}\nFAIL"
        ax.annotate(label, positions[idx], xytext=(4, 4), textcoords="offset points", fontsize=6)
        if labels[idx] > 0 and active[idx]:
            dest = _target_for_robot(problem, labels, idx, result.load_pose[frame_idx])
            ax.plot([positions[idx, 0], dest[0]], [positions[idx, 1], dest[1]], color=color, alpha=0.28, linewidth=0.8, linestyle="--")
            ax.scatter(dest[0], dest[1], marker="x", s=42, color=color, linewidth=1.1)

    event_color = "#b91c1c" if t_s >= problem.event.time_s else "#475569"
    status_lines = [
        f"event={problem.event.kind} at {problem.event.time_s:.1f}s observed {result.event_observed_time_s:.1f}s",
        f"comm radius={problem.communication_radius_at(t_s):.1f} m" if np.isfinite(problem.communication_radius_at(t_s)) else "comm radius=global",
        f"completed={int(np.sum(result.completed_loads[frame_idx]))}/{len(problem.world.loads)} active={int(np.sum(active))}/{len(active)}",
        f"battery min={float(np.min(battery)):.2f} reassign={result.reassignment_count}",
        f"min wrench margin={float(np.min(result.wrench_margins[frame_idx])):.2f} paused={int(np.sum(result.load_paused_mask[frame_idx]))}",
        "model: slot handover + wrench margin + Euler-Lagrange payload transport",
    ]
    ax.text(
        0.02,
        0.98,
        "\n".join(status_lines),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        bbox={"facecolor": "white", "alpha": 0.86, "edgecolor": event_color, "linewidth": 0.8},
    )


def _summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        if not selected:
            continue
        output.append(
            {
                "method": method,
                "recovery_success": _mean(selected, "recovery_success"),
                "task_completion_rate": _mean(selected, "task_completion_rate"),
                "lost_load_rate": _mean(selected, "lost_load_rate"),
                "recovery_time_s": _mean(selected, "recovery_time_s"),
                "collision_rate": _mean(selected, "collision_rate"),
                "min_obstacle_clearance_m": _mean(selected, "min_obstacle_clearance_m"),
                "post_event_wrench_feasible_rate": _mean(selected, "post_event_wrench_feasible_rate"),
                "reassignment_count": _mean(selected, "reassignment_count"),
                "communication_messages": _mean(selected, "communication_messages"),
                "score_value": _mean(selected, "score_value"),
            }
        )
    return output


def _draw_payload(ax: plt.Axes, length: float, width: float, q: np.ndarray, *, edge: str, face: str, linestyle: str, label: str | None) -> None:
    corners = np.array(
        [
            [-0.5 * length, -0.5 * width],
            [0.5 * length, -0.5 * width],
            [0.5 * length, 0.5 * width],
            [-0.5 * length, 0.5 * width],
            [-0.5 * length, -0.5 * width],
        ],
        dtype=float,
    )
    rotated = corners @ _rotation(float(q[2])).T + q[:2]
    ax.fill(rotated[:, 0], rotated[:, 1], facecolor=face, edgecolor=edge, linewidth=1.5, linestyle=linestyle, alpha=0.32 if face != "none" else 0.95, label=label)
    heading = _rotation(float(q[2])) @ np.array([0.55 * length, 0.0])
    ax.arrow(q[0], q[1], heading[0] * 0.22, heading[1] * 0.22, color=edge, width=0.012, head_width=0.12, alpha=0.86)


def _slot_positions(problem: SP6Problem, load_idx: int, q: np.ndarray) -> np.ndarray:
    slots = problem.load_slots[load_idx]
    if not slots:
        return np.zeros((0, 2), dtype=float)
    rotation = _rotation(float(q[2]))
    return np.vstack([q[:2] + rotation @ slot.offset_xy for slot in slots])


def _target_for_robot(problem: SP6Problem, labels: np.ndarray, robot_idx: int, load_pose: np.ndarray | None = None) -> np.ndarray:
    label = int(labels[robot_idx])
    load = problem.world.loads[label - 1]
    members = np.flatnonzero(labels == label)
    rank_matches = np.flatnonzero(members == robot_idx)
    rank = int(rank_matches[0]) if rank_matches.size else 0
    slots = problem.load_slots[label - 1]
    if slots:
        pose = problem.target_load_poses[label - 1] if load_pose is None else load_pose[label - 1]
        return pose[:2] + _rotation(float(pose[2])) @ slots[rank % len(slots)].offset_xy
    count = max(int(len(members)), int(load.min_coalition_size), 1)
    angle = 2.0 * np.pi * rank / count
    radius = max(0.55 * max(float(load.length_m), float(load.width_m)), 2.0 * problem.robot_radius_m + 2.0 * problem.safety_margin_m)
    center = problem.target_load_poses[label - 1, :2] if load_pose is None else load_pose[label - 1, :2]
    return center + radius * np.array([np.cos(angle), np.sin(angle)], dtype=float)


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    order = [
        "classic_centralized_replan",
        "classic_decentralized_greedy_recovery",
        "cbba_recovery",
        "cbf_recovery",
        "replicator_repair_recovery",
        "smith_qr_recovery",
        "primal_dual_recovery",
        "tensor_flow_recovery",
        "ours_guarded_wrench_market_recovery",
        "reference_resilient_oracle",
    ]
    methods = {str(row["method"]) for row in rows}
    return [method for method in order if method in methods] + sorted(methods - set(order))


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else float("nan")


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
        return float("nan")


def _short(method: str) -> str:
    meta = sp6_method_metadata(method)
    label = meta.get("label", method)
    aliases = {
        "Classic centralized replanning": "Classic central",
        "Classic decentralized greedy recovery": "Classic greedy",
        "CBBA recovery": "CBBA",
        "CBF recovery": "CBF",
        "Replicator repair recovery": "Replicator",
        "Smith-QR recovery": "Smith-QR",
        "Primal-dual recovery": "Primal-dual",
        "Tensor-flow recovery": "Tensor-flow",
        "Ours guarded wrench-market recovery": "Ours guarded",
        "Reference centralized resilient recovery": "Reference central",
    }
    method_label = aliases.get(str(label), str(label))
    return f"{_taxonomy_label(meta)}\n{method_label}"


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


def _rotation(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.55, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
