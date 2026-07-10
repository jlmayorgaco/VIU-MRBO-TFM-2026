"""SP8 scalability plots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp8.methods import SP8Assignment
from viu_mrob_tfm.sp8.scenario import SP8Problem


def plot_runtime_scaling(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_loglog(rows, path, y="runtime_ms", title="SP8 runtime scaling", ylabel="Runtime [ms]")


def plot_solved_rate_by_scale(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_line(rows, path, y="solved_rate", title="SP8 solved rate by scale", ylabel="Solved rate")


def plot_throughput_by_scale(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_line(rows, path, y="throughput_tasks_per_min", title="SP8 throughput by scale", ylabel="Tasks/min")


def plot_wrench_success(rows: list[dict[str, Any]], path: Path) -> None:
    _plot_line(rows, path, y="wrench_feasible_rate", title="SP8 wrench feasibility by scale", ylabel="Wrench feasible rate")


def plot_quality_complexity_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    groups = _group(rows)
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    for method, selected in groups.items():
        complexity = _mean(selected, "complexity_score")
        score = _mean(selected, "score_value")
        ax.scatter(complexity + 1.0, score, s=70, edgecolors="black", linewidths=0.45)
        ax.annotate(_short(method), (complexity + 1.0, score), xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_title("SP8 quality-complexity Pareto")
    ax.set_xlabel("Complexity proxy + 1 (log)")
    ax.set_ylabel("Mean score")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_timeout_boundary(rows: list[dict[str, Any]], path: Path) -> None:
    groups = _group(rows)
    methods = list(groups)
    timeout = [_mean(groups[method], "timeout_rate") for method in methods]
    fig, ax = plt.subplots(figsize=(max(8.0, 0.75 * len(methods)), 4.5))
    ax.bar(np.arange(len(methods)), timeout, color="#8b3a3a")
    ax.set_title("SP8 centralized timeout/intractability boundary")
    ax.set_ylabel("Timeout rate")
    ax.set_xticks(np.arange(len(methods)))
    ax.set_xticklabels([_short(method) for method in methods], fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_scale_transport_video(problem: SP8Problem, assignment: SP8Assignment, path: Path, title: str, *, fps: int = 6, duration_s: float = 16.0) -> bool:
    fig, ax = plt.subplots(figsize=(8.2, 7.4))
    frames = max(80, int(round(duration_s * fps)))
    sample_loads = _sample_loads(problem)
    sample_robots = _sample_robots(problem, assignment, sample_loads)

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        alpha = min(1.0, frame_idx / max(frames - int(4 * fps), 1))
        _draw_scale_frame(ax, problem, assignment, sample_loads, sample_robots, alpha, f"{title} | t={alpha * problem.params.horizon_s:.0f}s")
        return []

    animation = FuncAnimation(fig, draw, frames=frames, interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=128)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _draw_scale_frame(ax: plt.Axes, problem: SP8Problem, assignment: SP8Assignment, load_indices: np.ndarray, robot_indices: np.ndarray, alpha: float, title: str) -> None:
    half = 0.5 * problem.params.world_size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.16)
    ax.set_title(title, fontsize=9)
    for xy, radius in zip(problem.obstacle_xy, problem.obstacle_radius_m):
        ax.add_patch(plt.Circle(xy, radius + 1.25, facecolor="#e5e7eb", edgecolor="none", alpha=0.28))
        ax.add_patch(plt.Circle(xy, radius, facecolor="#6b7280", edgecolor="#111827", linewidth=0.55, alpha=0.72))
    mobile_xy = (1.0 - alpha) * problem.mobile_start_xy + alpha * problem.mobile_end_xy
    for xy, radius in zip(mobile_xy, problem.mobile_radius_m):
        ax.add_patch(plt.Circle(xy, radius + 1.5, facecolor="#fee2e2", edgecolor="none", alpha=0.22))
        ax.add_patch(plt.Circle(xy, radius, facecolor="#ef4444", edgecolor="#7f1d1d", linewidth=0.55, alpha=0.58))
    load_xy = (1.0 - alpha) * problem.load_pickup_xy + alpha * problem.load_target_xy
    for load_idx in load_indices:
        start = problem.load_pickup_xy[load_idx]
        target = problem.load_target_xy[load_idx]
        pos = load_xy[load_idx]
        ax.plot([start[0], target[0]], [start[1], target[1]], color="#64748b", linewidth=0.8, alpha=0.42)
        ax.scatter(target[0], target[1], marker="*", s=62, color="#15803d", edgecolor="black", linewidth=0.35)
        ax.add_patch(_payload_patch(pos, problem.load_length_m[load_idx], problem.load_width_m[load_idx], angle=float(np.arctan2(*(target - start)[::-1])), face="#8ecae6", edge="#1f2937"))
        demand = problem.wrench_demands[load_idx]
        force = demand[:2]
        norm = float(np.linalg.norm(force))
        if norm > 1e-9:
            vec = force / norm * min(4.0, 0.04 * problem.params.world_size_m)
            ax.arrow(pos[0], pos[1], vec[0], vec[1], width=0.04, color="#2563eb", alpha=0.72, length_includes_head=True)
        ax.annotate(f"L{load_idx + 1}\n{problem.load_mass_kg[load_idx]:.0f}kg\n{demand[2]:.0f}Nm", pos, xytext=(4, 4), textcoords="offset points", fontsize=6)
    colors = plt.cm.tab20(np.linspace(0.0, 1.0, max(robot_indices.size, 1)))
    for color_idx, robot_idx in enumerate(robot_indices):
        label = int(assignment.labels[robot_idx])
        if label > 0:
            load_idx = label - 1
            load_pos = load_xy[load_idx]
            angle = assignment.slot_angles[robot_idx]
            if not np.isfinite(angle):
                angle = 0.0
            slot_offset = np.array([0.5 * problem.load_length_m[load_idx] * np.cos(angle), 0.5 * problem.load_width_m[load_idx] * np.sin(angle)])
            pickup_slot = problem.load_pickup_xy[load_idx] + slot_offset
            carried_slot = load_pos + slot_offset
            approach = min(1.0, alpha / 0.30)
            if alpha < 0.30:
                pos = (1.0 - approach) * problem.robot_xy[robot_idx] + approach * pickup_slot
            else:
                pos = carried_slot
            edge = "#111827"
            face = colors[color_idx % len(colors)]
            ax.plot([problem.robot_xy[robot_idx, 0], pickup_slot[0]], [problem.robot_xy[robot_idx, 1], pickup_slot[1]], color=face, linewidth=0.7, alpha=0.25)
            ax.add_patch(plt.Circle(pos, 0.7, facecolor=face, edgecolor=edge, linewidth=0.45, alpha=0.82))
            if load_idx in load_indices:
                ax.plot([pos[0], load_pos[0]], [pos[1], load_pos[1]], color="#2563eb", linewidth=0.65, alpha=0.34)
        else:
            pos = problem.robot_xy[robot_idx]
            ax.add_patch(plt.Circle(pos, 0.55, facecolor="#94a3b8", edgecolor="#334155", linewidth=0.35, alpha=0.30))
    assigned = int(np.sum(assignment.labels > 0))
    ax.text(
        0.02,
        0.98,
        "\n".join(
            [
                f"method={assignment.method} status={assignment.status}",
                f"scale={problem.params.n_robots} AMR / {problem.params.n_loads} loads",
                f"shown={robot_indices.size} robots / {load_indices.size} loads, assigned={assigned}",
                "mesoscopic model: pickup -> transport -> target with wrench/torque checks",
                "obstacles: gray static, red mobile",
            ]
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        bbox={"facecolor": "white", "alpha": 0.84, "edgecolor": "#cbd5e1", "linewidth": 0.6},
    )


def _plot_line(rows: list[dict[str, Any]], path: Path, *, y: str, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    for method, selected in _group(rows).items():
        by_scale: dict[int, list[float]] = {}
        for row in selected:
            by_scale.setdefault(int(row["n_robots"]), []).append(float(row[y]))
        xs = sorted(by_scale)
        ys = [float(np.mean(by_scale[x])) for x in xs]
        ax.plot(xs, ys, marker="o", linewidth=1.8, label=_short(method))
    ax.set_title(title)
    ax.set_xscale("log")
    ax.set_xlabel("AMR count (log)")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_loglog(rows: list[dict[str, Any]], path: Path, *, y: str, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    for method, selected in _group(rows).items():
        by_scale: dict[int, list[float]] = {}
        for row in selected:
            by_scale.setdefault(int(row["n_robots"]), []).append(max(float(row[y]), 1e-6))
        xs = np.asarray(sorted(by_scale), dtype=float)
        ys = np.asarray([float(np.mean(by_scale[int(x)])) for x in xs], dtype=float)
        ax.plot(xs, ys, marker="o", linewidth=1.8, label=_short(method))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(title)
    ax.set_xlabel("AMR count (log)")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _group(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["method"]), []).append(row)
    return grouped


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = np.asarray([float(row.get(key, np.nan)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else np.nan


def _short(method: str) -> str:
    return {
        "centralized_hungarian_expanded": "Hungarian\nexpanded",
        "centralized_coalition_oracle": "Coalition\noracle",
        "centralized_time_expanded_mpc": "Central\nMPC",
        "classic_local_greedy": "Classic\nlocal",
        "cbba_partitioned": "CBBA\npartitioned",
        "auction_market_local": "Auction\nlocal",
        "ours_primal_dual_spatial": "Ours\nPD spatial",
        "ours_tensor_quorum_flow": "Ours\ntensor flow",
        "ours_wrench_market_hierarchical": "Ours\nwrench hier.",
        "ours_mean_field_approximation": "Ours\nMFG approx.",
    }.get(method, method)


def _sample_loads(problem: SP8Problem, limit: int = 18) -> np.ndarray:
    if problem.params.n_loads <= limit:
        return np.arange(problem.params.n_loads, dtype=int)
    score = problem.load_reward + 0.004 * np.abs(problem.wrench_demands[:, 2])
    return np.sort(np.argsort(-score)[:limit])


def _sample_robots(problem: SP8Problem, assignment: SP8Assignment, load_indices: np.ndarray, limit: int = 180) -> np.ndarray:
    assigned_to_shown = np.flatnonzero(np.isin(assignment.labels - 1, load_indices))
    if assigned_to_shown.size >= limit:
        return np.sort(assigned_to_shown[:limit])
    unassigned = np.flatnonzero(assignment.labels == 0)
    remaining = limit - assigned_to_shown.size
    if unassigned.size > remaining:
        unassigned = unassigned[:remaining]
    return np.sort(np.concatenate([assigned_to_shown, unassigned]))


def _payload_patch(center: np.ndarray, length: float, width: float, *, angle: float, face: str, edge: str) -> plt.Polygon:
    corners = np.array([[-0.5 * length, -0.5 * width], [0.5 * length, -0.5 * width], [0.5 * length, 0.5 * width], [-0.5 * length, 0.5 * width]], dtype=float)
    rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]], dtype=float)
    xy = corners @ rot.T + center
    return plt.Polygon(xy, closed=True, facecolor=face, edgecolor=edge, linewidth=1.1, alpha=0.55)
