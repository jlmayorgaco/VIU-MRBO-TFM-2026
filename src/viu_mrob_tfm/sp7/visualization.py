"""SP7 communication figures and videos."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from viu_mrob_tfm.sp5.visualization import save_transport_snapshot
from viu_mrob_tfm.sp7.scenario import CommunicationProfile
from viu_mrob_tfm.utils.io import ensure_directory


def plot_connectivity_vs_radius(rows: list[dict[str, Any]], path: Path) -> None:
    _line_by_method(rows, path, x="communication_radius_m", y="coalition_connected_time_ratio", title="SP7 coalition connectivity vs communication radius", ylabel="Coalition connected time ratio")


def plot_transport_success_under_stress(rows: list[dict[str, Any]], path: Path) -> None:
    _line_by_method(rows, path, x="network_severity", y="transport_success", title="SP7 transport success under communication stress", ylabel="Transport success")


def plot_packet_loss_delay_heatmap(rows: list[dict[str, Any]], path: Path) -> None:
    x_vals = sorted({_bucket(float(row["packet_loss_probability"]), 0.05) for row in rows})
    y_vals = sorted({_bucket(float(row["delay_mean_s"]), 0.05) for row in rows})
    grid = np.full((len(y_vals), len(x_vals)), np.nan, dtype=float)
    for yi, delay in enumerate(y_vals):
        for xi, loss in enumerate(x_vals):
            selected = [row for row in rows if _bucket(float(row["packet_loss_probability"]), 0.05) == loss and _bucket(float(row["delay_mean_s"]), 0.05) == delay]
            if selected:
                grid[yi, xi] = float(np.mean([float(row["transport_network_score"]) for row in selected]))
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    image = ax.imshow(grid, origin="lower", aspect="auto", vmin=0.0, vmax=1.0, cmap="viridis")
    ax.set_title("SP7 transport-network score by packet loss and delay")
    ax.set_xlabel("Packet loss probability")
    ax.set_ylabel("Mean delay [s]")
    ax.set_xticks(range(len(x_vals)))
    ax.set_xticklabels([f"{value:.2f}" for value in x_vals], rotation=45)
    ax.set_yticks(range(len(y_vals)))
    ax.set_yticklabels([f"{value:.2f}" for value in y_vals])
    fig.colorbar(image, ax=ax, label="Transport-network score")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_relay_temporal_connectivity(rows: list[dict[str, Any]], path: Path) -> None:
    methods = _ordered_methods(rows)
    direct = [_mean([row for row in rows if row["method"] == method], "direct_clique_time_ratio") for method in methods]
    relay = [_mean([row for row in rows if row["method"] == method], "relay_success_rate") for method in methods]
    temporal = [_mean([row for row in rows if row["method"] == method], "temporal_coalition_connected_rate") for method in methods]
    x = np.arange(len(methods))
    fig, ax = plt.subplots(figsize=(max(8.5, 0.9 * len(methods)), 4.8))
    ax.bar(x - 0.25, direct, width=0.25, label="Direct clique")
    ax.bar(x, relay, width=0.25, label="Relay-only connected")
    ax.bar(x + 0.25, temporal, width=0.25, label="Temporal connected")
    ax.set_title("SP7 direct vs relay vs temporal connectivity")
    ax.set_ylabel("Mean rate")
    ax.set_xticks(x)
    ax.set_xticklabels([_short(row_method) for row_method in methods], fontsize=8)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_sensing_vs_collision(rows: list[dict[str, Any]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for method in _ordered_methods(rows):
        selected = [row for row in rows if row["method"] == method]
        x = [float(row["sensor_coverage_rate"]) for row in selected]
        y = [float(row["collision_rate"]) for row in selected]
        ax.scatter(x, y, s=26, alpha=0.62, label=_short(method))
    ax.set_title("SP7 sensing coverage vs collision rate")
    ax.set_xlabel("Sensor coverage rate")
    ax.set_ylabel("Collision rate")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_quality_resource_pareto(rows: list[dict[str, Any]], path: Path) -> None:
    methods = _ordered_methods(rows)
    fig, ax = plt.subplots(figsize=(7.5, 4.9))
    for method in methods:
        selected = [row for row in rows if row["method"] == method]
        score = _mean(selected, "transport_network_score")
        messages = _mean(selected, "attempted_messages")
        ax.scatter(messages + 1.0, score, s=68, edgecolors="black", linewidths=0.45)
        ax.annotate(_short(method), (messages + 1.0, score), xytext=(4, 3), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_title("SP7 quality-resource Pareto")
    ax.set_xlabel("Attempted messages + 1 (log)")
    ax.set_ylabel("Mean transport-network score")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_communication_video(problem: Any, result: Any, profile: CommunicationProfile, path: Path, title: str, *, fps: int = 10, duration_s: float = 48.0) -> bool:
    fig, ax = plt.subplots(figsize=(8.0, 7.3))
    total = len(result.time_s)
    frames = max(90, int(round(duration_s * fps)))
    indices = np.linspace(0, total - 1, min(total, frames)).astype(int)
    hold = np.full(max(10, int(3 * fps)), total - 1, dtype=int)
    indices = np.concatenate([indices, hold])

    def draw(frame_idx: int) -> list[object]:
        ax.clear()
        idx = int(indices[frame_idx])
        _draw_comm_frame(ax, problem, result, profile, idx, f"{title} | t={result.time_s[idx]:.1f}s")
        return []

    animation = FuncAnimation(fig, draw, frames=len(indices), interval=1000 / max(fps, 1), blit=False)
    try:
        animation.save(path, fps=fps, dpi=130)
        ok = True
    except Exception:
        ok = False
    finally:
        plt.close(fig)
    return ok


def _line_by_method(rows: list[dict[str, Any]], path: Path, *, x: str, y: str, title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    for method in _ordered_methods(rows):
        selected = [row for row in rows if row["method"] == method]
        groups: dict[float, list[float]] = {}
        for row in selected:
            x_value = float(row[x])
            if not np.isfinite(x_value):
                x_value = 12.5
            groups.setdefault(x_value, []).append(float(row[y]))
        xs = sorted(groups)
        ys = [float(np.mean(groups[value])) for value in xs]
        ax.plot(xs, ys, marker="o", linewidth=1.8, label=_short(method))
    ax.set_title(title)
    ax.set_xlabel(x.replace("_", " "))
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _draw_comm_frame(ax: plt.Axes, problem: Any, result: Any, profile: CommunicationProfile, idx: int, title: str) -> None:
    half = 0.5 * problem.world.map.size_m
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.18)
    ax.set_title(title, fontsize=9)
    for obstacle in problem.world.map.obstacles:
        ax.add_patch(plt.Circle(obstacle.center, obstacle.influence_radius, facecolor="#e5e7eb", edgecolor="none", alpha=0.35))
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, facecolor="#6b7280", edgecolor="#111827", alpha=0.7))
    t_s = float(result.time_s[idx])
    for group in problem.mobile_groups:
        center = group.center_at(t_s, problem.horizon_s)
        ax.add_patch(plt.Circle(center, group.influence_radius_m, facecolor="#fee2e2", edgecolor="none", alpha=0.25))
        ax.add_patch(plt.Circle(center, group.radius_m, facecolor="#ef4444", edgecolor="#7f1d1d", alpha=0.5))
    q = result.load_pose[idx]
    ax.scatter(problem.task.target_pose[0], problem.task.target_pose[1], marker="*", s=120, color="#15803d", edgecolor="black")
    ax.scatter(q[0], q[1], marker="s", s=140, color="#8ecae6", edgecolor="#1f2937")
    positions = result.robot_positions[idx]
    links = _geometric_links(positions, profile.communication_radius_m)
    for i in range(positions.shape[0]):
        for j in range(i + 1, positions.shape[0]):
            if links[i, j]:
                ax.plot([positions[i, 0], positions[j, 0]], [positions[i, 1], positions[j, 1]], color="#2563eb", linewidth=1.0, alpha=0.35)
    labels = np.asarray(result.assignment.labels, dtype=int)
    selected = labels == result.selected_load_index + 1
    for robot_idx, xy in enumerate(positions):
        color = "#16a34a" if selected[robot_idx] else "#64748b"
        ax.add_patch(plt.Circle(xy, problem.robot_radius_m, facecolor=color, edgecolor="black", alpha=0.88 if selected[robot_idx] else 0.35))
        ax.annotate(f"R{robot_idx + 1}", xy, xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.text(
        0.02,
        0.98,
        "\n".join(
            [
                f"profile={profile.profile_id}",
                f"radius={_radius(profile.communication_radius_m)} loss={profile.packet_loss_probability:.2f}",
                f"delay={profile.delay_mean_s:.2f}s jitter={profile.delay_jitter_s:.2f}s",
                f"sensor range={profile.sensor_range_m:.1f}m fn={profile.sensor_false_negative_probability:.2f}",
            ]
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        bbox={"facecolor": "white", "alpha": 0.84, "edgecolor": "#cbd5e1", "linewidth": 0.6},
    )


def _geometric_links(frame: np.ndarray, radius: float) -> np.ndarray:
    n = frame.shape[0]
    if n <= 1:
        return np.zeros((n, n), dtype=bool)
    distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
    links = distances <= radius if np.isfinite(radius) else np.ones((n, n), dtype=bool)
    np.fill_diagonal(links, False)
    return links


def _bucket(value: float, step: float) -> float:
    return float(step * round(value / step))


def _ordered_methods(rows: list[dict[str, Any]]) -> list[str]:
    order = [
        "classic_centralized_global_mpc",
        "classic_decentralized_sensor_apf",
        "sota_centralized_cbf_networked",
        "sota_decentralized_cbba_relay",
        "sota_delay_tolerant_consensus",
        "ours_connectivity_wrench_game",
        "ours_delay_robust_repair",
        "reference_full_communication",
    ]
    methods = {str(row["method"]) for row in rows}
    return [method for method in order if method in methods] + sorted(methods - set(order))


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = np.asarray([float(row.get(key, math.nan)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else math.nan


def _short(method: str) -> str:
    return {
        "classic_centralized_global_mpc": "Classic\ncentral",
        "classic_decentralized_sensor_apf": "Classic\nsensor",
        "sota_centralized_cbf_networked": "SOTA\ncentral CBF",
        "sota_decentralized_cbba_relay": "SOTA\nrelay",
        "sota_delay_tolerant_consensus": "SOTA\ndelay cons.",
        "ours_connectivity_wrench_game": "Ours\nconn-wrench",
        "ours_delay_robust_repair": "Ours\ndelay repair",
        "reference_full_communication": "Reference\nfull comm",
    }.get(method, method)


def _radius(value: float) -> str:
    return "inf" if not np.isfinite(value) else f"{value:.1f}m"
