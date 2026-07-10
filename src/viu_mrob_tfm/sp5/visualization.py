"""Plots and videos for SP5 cooperative payload transport."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp5.methods import SP5TrajectoryResult, sp5_method_metadata
from viu_mrob_tfm.sp5.scenario import SP5Problem


def plot_transport_success(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8, 0.62 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["transport_success"] for row in summaries], color="#2a9d8f")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Transport success rate")
    ax.set_title("SP5 cooperative payload transport success by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_final_pose_error(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    labels = [_short(row["method"]) for row in summaries]
    x = np.arange(len(summaries))
    fig, ax1 = plt.subplots(figsize=(max(8, 0.64 * len(summaries)), 4.8))
    ax1.bar(x - 0.18, [row["final_position_error_m"] for row in summaries], width=0.36, color="#4c78a8", label="position m")
    ax1.set_ylabel("Final position error m")
    ax2 = ax1.twinx()
    ax2.bar(x + 0.18, [row["final_orientation_error_deg"] for row in summaries], width=0.36, color="#f58518", label="orientation deg")
    ax2.set_ylabel("Final orientation error deg")
    ax1.set_title("SP5 final payload pose error")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=30, ha="right")
    ax1.grid(True, axis="y", alpha=0.22)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_formation_error(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(max(8, 0.62 * len(summaries)), 4.8))
    ax.bar([_short(row["method"]) for row in summaries], [row["mean_formation_error_m"] for row in summaries], color="#72b7b2")
    ax.set_ylabel("Mean formation error m")
    ax.set_title("SP5 formation preservation by method")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_collision_rate_by_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({str(row["scenario_generator"]) for row in rows})
    methods = _ordered_methods(rows)
    if not scenarios or not methods:
        _placeholder(path, "SP5 collision rate by scenario", "No runs")
        return
    matrix = np.zeros((len(scenarios), len(methods)), dtype=float)
    for i, scenario in enumerate(scenarios):
        for j, method in enumerate(methods):
            matrix[i, j] = _mean([row for row in rows if row["scenario_generator"] == scenario and row["method"] == method], "collision_rate")
    vmax = max(0.01, float(np.nanmax(matrix)) if matrix.size else 1.0)
    fig, ax = plt.subplots(figsize=(max(8, 0.72 * len(methods)), max(4.5, 0.55 * len(scenarios))))
    image = ax.imshow(matrix, cmap="magma", vmin=0.0, vmax=vmax, aspect="auto")
    ax.set_title("SP5 collision rate by scenario")
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


def plot_quality_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    summaries = _summaries(rows)
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    for row in summaries:
        marker = "s" if row["transport_mode"] == "cargo" else "o"
        ax.scatter(row["energy_proxy_wh"], row["score_value"], s=70 + 180 * row["collision_rate"], marker=marker, alpha=0.84)
        ax.annotate(_short(row["method"]), (row["energy_proxy_wh"], row["score_value"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Energy proxy Wh")
    ax.set_ylabel("Transport score")
    ax.set_title("SP5 quality-resource Pareto\nbubble size = collision rate, square = cargo")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_push_drag_vs_cargo(rows: list[dict[str, Any]], path: Path) -> None:
    modes = ["push_drag", "cargo"]
    metrics = ["transport_success", "formation_integrity_rate", "target_reached"]
    matrix = np.zeros((len(metrics), len(modes)), dtype=float)
    for i, metric in enumerate(metrics):
        for j, mode in enumerate(modes):
            selected = [row for row in rows if str(row.get("transport_mode")) == mode]
            matrix[i, j] = _mean(selected, metric)
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    image = ax.imshow(matrix, cmap="viridis", vmin=0.0, vmax=1.0, aspect="auto")
    ax.set_title("SP5 push-drag vs cargo aggregate")
    ax.set_xticks(np.arange(len(modes)))
    ax.set_xticklabels([mode.replace("_", "/") for mode in modes])
    ax.set_yticks(np.arange(len(metrics)))
    ax.set_yticklabels([metric.replace("_", " ") for metric in metrics])
    for i in range(len(metrics)):
        for j in range(len(modes)):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=9, color="white" if matrix[i, j] < 0.45 else "black")
    fig.colorbar(image, ax=ax, shrink=0.82)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_transport_snapshot(problem: SP5Problem, result: SP5TrajectoryResult, path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 7.3))
    _draw_frame(ax, problem, result, len(result.time_s) - 1, title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_transport_video(
    problem: SP5Problem,
    result: SP5TrajectoryResult,
    path: Path,
    title: str,
    *,
    fps: int = 10,
    duration_s: float = 44.0,
    final_hold_s: float = 10.0,
) -> bool:
    fig, ax = plt.subplots(figsize=(8.0, 7.3))
    total = len(result.time_s)
    hold_frames = max(0, int(round(max(final_hold_s, 0.0) * max(fps, 1))))
    motion_budget = max(2, int(round(max(duration_s - final_hold_s, 1.0) * max(fps, 1))))
    motion_frames = min(total, max(90, motion_budget))
    indices = np.linspace(0, total - 1, motion_frames).astype(int)
    if hold_frames > 0:
        indices = np.concatenate([indices, np.full(hold_frames, total - 1, dtype=int)])

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        idx = int(indices[frame_idx])
        phase = "FINAL PAYLOAD STATE" if frame_idx >= motion_frames else ("pickup" if int(result.phase[idx]) == 0 else f"transport t={result.time_s[idx]:.1f}s")
        _draw_frame(ax, problem, result, idx, f"{title} | {phase}")
        return []

    animation = FuncAnimation(fig, draw, frames=len(indices), interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=140)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_frame(ax: plt.Axes, problem: SP5Problem, result: SP5TrajectoryResult, frame_idx: int, title: str) -> None:
    half = 0.5 * problem.world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)

    for obstacle in problem.world.map.obstacles:
        ax.add_patch(plt.Circle(obstacle.center, obstacle.influence_radius, facecolor="#f2f4f7", edgecolor="none", alpha=0.36))
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, facecolor="#8b949e", edgecolor="#344054", alpha=0.76))
    t_s = float(result.time_s[frame_idx])
    for group in problem.mobile_groups:
        center = group.center_at(t_s, problem.horizon_s)
        ax.add_patch(plt.Circle(center, group.influence_radius_m, facecolor="#fee2e2", edgecolor="none", alpha=0.26))
        ax.add_patch(plt.Circle(center, group.radius_m, facecolor="#ef4444", edgecolor="#7f1d1d", alpha=0.54))
        ax.annotate(group.identifier, center, xytext=(4, 4), textcoords="offset points", fontsize=6)

    load = problem.world.loads[result.selected_load_index]
    _draw_payload(ax, load.length_m, load.width_m, problem.task.initial_pose, edge="#64748b", face="none", linestyle="--", label="task initial")
    _draw_payload(ax, load.length_m, load.width_m, problem.task.target_pose, edge="#15803d", face="none", linestyle=":", label="task target")
    _draw_payload(ax, load.length_m, load.width_m, result.load_pose[frame_idx], edge="#1f2937", face="#8ecae6", linestyle="-", label="payload")
    ax.scatter(problem.task.target_pose[0], problem.task.target_pose[1], marker="*", s=130, color="#15803d", edgecolor="black", linewidth=0.5)

    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(problem.world.robots), 1)))
    labels = np.asarray(result.assignment.labels, dtype=int)
    slot_labels = np.asarray(result.assignment.slot_labels, dtype=int)
    assigned_selected = labels == result.selected_load_index + 1
    for idx, robot in enumerate(problem.world.robots):
        color = colors[idx % len(colors)]
        trail = result.robot_positions[: frame_idx + 1, idx]
        ax.plot(trail[:, 0], trail[:, 1], color=color, linewidth=1.0, alpha=0.55 if assigned_selected[idx] else 0.25)
        ax.scatter(result.robot_positions[0, idx, 0], result.robot_positions[0, idx, 1], marker="o", s=30, facecolor="white", edgecolor=color, linewidth=1.0)
        alpha = 0.88 if assigned_selected[idx] else 0.30
        ax.add_patch(plt.Circle(result.robot_positions[frame_idx, idx], problem.robot_radius_m, facecolor=color, edgecolor="black", linewidth=0.55, alpha=alpha))
        suffix = f"S{slot_labels[idx]}" if assigned_selected[idx] else "idle"
        ax.annotate(f"R{idx + 1}\n{suffix}", result.robot_positions[frame_idx, idx], xytext=(4, 4), textcoords="offset points", fontsize=6)

    slot_positions = _slot_positions(problem, result, frame_idx)
    for slot_idx, slot_xy in enumerate(slot_positions):
        ax.scatter(slot_xy[0], slot_xy[1], marker="x", s=65, color="#1d4ed8", linewidth=1.6, zorder=5)
        ax.annotate(f"slot {slot_idx + 1}", slot_xy, xytext=(4, -12), textcoords="offset points", fontsize=6, color="#1d4ed8")

    pos_error = float(np.linalg.norm(problem.task.target_pose[:2] - result.load_pose[frame_idx, :2]))
    theta_error = abs(_wrap_angle(float(problem.task.target_pose[2] - result.load_pose[frame_idx, 2])))
    ax.text(
        0.02,
        0.98,
        "\n".join(
            [
                f"mode={result.transport_mode} selected={result.selected_load_id} task={result.selected_task_load}",
                f"pose error={pos_error:.2f} m, {math.degrees(theta_error):.1f} deg",
                f"formation max={result.formation_errors[frame_idx]:.2f} m",
                f"wrench residual={result.wrench_residuals[frame_idx]:.3f}",
                "model: M(q) qdd + D qd = G(q) lambda + safety/game fields",
            ]
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        bbox={"facecolor": "white", "alpha": 0.84, "edgecolor": "#cbd5e1", "linewidth": 0.6},
    )
    ax.legend(loc="lower right", fontsize=7)


def _draw_payload(ax: plt.Axes, length: float, width: float, q: np.ndarray, *, edge: str, face: str, linestyle: str, label: str) -> None:
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
    ax.fill(rotated[:, 0], rotated[:, 1], facecolor=face, edgecolor=edge, linewidth=1.8, linestyle=linestyle, alpha=0.30 if face != "none" else 1.0, label=label)
    heading = _rotation(float(q[2])) @ np.array([0.75 * length, 0.0])
    ax.arrow(q[0], q[1], heading[0] * 0.28, heading[1] * 0.28, color=edge, width=0.015, head_width=0.13, alpha=0.9)


def _slot_positions(problem: SP5Problem, result: SP5TrajectoryResult, frame_idx: int) -> np.ndarray:
    rotation = _rotation(float(result.load_pose[frame_idx, 2]))
    positions = []
    for robot_idx, label in enumerate(np.asarray(result.assignment.labels, dtype=int)):
        if int(label) != result.selected_load_index + 1:
            continue
        slot_idx = int(result.assignment.slot_labels[robot_idx]) - 1
        if 0 <= slot_idx < len(problem.load_slots[result.selected_load_index]):
            slot = problem.load_slots[result.selected_load_index][slot_idx]
            positions.append(result.load_pose[frame_idx, :2] + rotation @ slot.offset_xy)
    return np.vstack(positions) if positions else np.zeros((0, 2), dtype=float)


def _summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for method in _ordered_methods(rows):
        selected = [row for row in rows if str(row["method"]) == method]
        if not selected:
            continue
        first = selected[0]
        output.append(
            {
                "method": method,
                "transport_mode": first.get("transport_mode", ""),
                "transport_success": _mean(selected, "transport_success"),
                "target_reached": _mean(selected, "target_reached"),
                "formation_integrity_rate": _mean(selected, "formation_integrity_rate"),
                "mean_formation_error_m": _mean(selected, "mean_formation_error_m"),
                "final_position_error_m": _mean(selected, "final_position_error_m"),
                "final_orientation_error_deg": _mean(selected, "final_orientation_error_deg"),
                "collision_rate": _mean(selected, "collision_rate"),
                "energy_proxy_wh": _mean(selected, "energy_proxy_wh"),
                "score_value": _mean(selected, "score_value"),
            }
        )
    return output


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    order = [
        "classic_centralized_shortest_push",
        "classic_decentralized_apf_push",
        "sota_centralized_cbf_push",
        "sota_decentralized_vo_push",
        "sota_centralized_cbf_cargo",
        "sota_decentralized_vo_cargo",
        "ours_primal_dual_wrench_push",
        "ours_tensor_game_push",
        "ours_hamiltonian_cargo",
        "reference_centralized_mpc_cbf_cargo",
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


def _short(method: str) -> str:
    meta = sp5_method_metadata(method)
    label = meta.get("label", method)
    aliases = {
        "Classic centralized shortest push": "Classic central push",
        "Classic decentralized APF push": "Classic APF push",
        "SOTA centralized CBF push": "SOTA CBF push",
        "SOTA decentralized VO push": "SOTA VO push",
        "SOTA centralized CBF cargo": "SOTA CBF cargo",
        "SOTA decentralized VO cargo": "SOTA VO cargo",
        "Ours primal-dual wrench push": "Ours PD push",
        "Ours tensor-game push": "Ours tensor push",
        "Ours Hamiltonian cargo": "Ours Ham cargo",
        "Reference centralized MPC-CBF cargo": "Reference MPC-CBF",
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
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi


def _placeholder(path: Path, title: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.55, title, ha="center", va="center", fontsize=13, weight="bold")
    ax.text(0.5, 0.42, message, ha="center", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
