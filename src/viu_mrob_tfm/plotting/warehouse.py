"""Plotting helpers for the realistic warehouse simulation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.animation import FFMpegWriter, FuncAnimation

from viu_mrob_tfm.simulations.warehouse import (
    LOAD_DELIVERED,
    LOAD_NOT_SPAWNED,
    LOAD_RECRUITING,
    LOAD_TRANSPORT,
    WarehouseResult,
)


def plot_warehouse_overview(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot robot and load trajectories over the warehouse map."""

    figure, axis = plt.subplots(figsize=(9, 9))
    _draw_warehouse_base(axis, result)
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(result.loads), 1)))

    for robot_idx in range(result.config.robot_count):
        trajectory = result.robot_positions[:, robot_idx]
        axis.plot(trajectory[:, 0], trajectory[:, 1], color="0.55", linewidth=0.7, alpha=0.35)
        axis.scatter(
            trajectory[0, 0],
            trajectory[0, 1],
            color="0.25",
            s=12,
            marker=".",
            label="robot start" if robot_idx == 0 else None,
        )
        axis.scatter(
            trajectory[-1, 0],
            trajectory[-1, 1],
            color="black",
            s=20,
            marker="o",
            label="robot final" if robot_idx == 0 else None,
        )

    for load_idx, load in enumerate(result.loads):
        active = result.load_status[:, load_idx] != LOAD_NOT_SPAWNED
        if np.any(active):
            load_path = result.load_positions[active, load_idx]
            axis.plot(
                load_path[:, 0],
                load_path[:, 1],
                color=colors[load_idx],
                linewidth=2.6,
                label=f"{load.identifier} w={load.weight}",
            )
        axis.scatter(load.source[0], load.source[1], color=colors[load_idx], s=90, marker="s")
        axis.scatter(load.target[0], load.target[1], color=colors[load_idx], s=110, marker="*", edgecolor="black")
        axis.annotate(
            f"w={load.weight}",
            xy=load.source,
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            color=colors[load_idx],
        )

    axis.set_title("Warehouse 2D: robots, dynamic loads, obstacles")
    axis.legend(loc="upper right", fontsize=8, framealpha=0.9)
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_storyboard(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot four snapshots that explain the emergent lifecycle."""

    sample_times = _storyboard_times(result)
    figure, axes = plt.subplots(2, 2, figsize=(12, 12), sharex=True, sharey=True)
    axes_flat = axes.ravel()
    for axis, sample_time in zip(axes_flat, sample_times):
        step = int(np.argmin(np.abs(result.time - sample_time)))
        _draw_warehouse_base(axis, result, include_labels=False)
        _draw_snapshot(axis, result, step)
        axis.set_title(f"t = {result.time[step]:.1f} s")
    figure.suptitle("Emergent lifecycle: recruit -> form -> transport -> release", fontsize=14)
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_timeline(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot load status over time as a compact timeline."""

    figure, axis = plt.subplots(figsize=(12, 4.8))
    status = result.load_status.T.astype(float)
    mapped = np.full_like(status, 0.0)
    mapped[status == LOAD_NOT_SPAWNED] = 0
    mapped[status == LOAD_RECRUITING] = 1
    mapped[status == LOAD_TRANSPORT] = 2
    mapped[status == LOAD_DELIVERED] = 3
    cmap = ListedColormap(["#e5e7eb", "#f59e0b", "#2563eb", "#16a34a"])
    axis.imshow(
        mapped,
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        extent=[result.time[0], result.time[-1], len(result.loads) + 0.5, 0.5],
    )
    axis.set_yticks(np.arange(1, len(result.loads) + 1))
    axis.set_yticklabels([f"{load.identifier} (w={load.weight})" for load in result.loads])
    axis.set_xlabel("Time [s]")
    axis.set_title("Load lifecycle timeline")
    legend_items = [
        ("not spawned", "#e5e7eb"),
        ("recruiting", "#f59e0b"),
        ("transport", "#2563eb"),
        ("delivered", "#16a34a"),
    ]
    for idx, (label, color) in enumerate(legend_items):
        axis.scatter([], [], color=color, marker="s", s=90, label=label)
    axis.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.32), frameon=False)
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_recruitment(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot contacts, effective occupancy, and adaptive prices."""

    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(result.loads), 1)))
    figure, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    for load_idx, load in enumerate(result.loads):
        color = colors[load_idx]
        staffing_target = load.weight + result.config.reserve_robot_slack
        axes[0].plot(result.time, result.contact_counts[:, load_idx], color=color, label=load.identifier)
        axes[0].axhline(load.weight, color=color, linestyle="--", linewidth=1.0, alpha=0.55)
        axes[0].axhline(staffing_target, color=color, linestyle=":", linewidth=1.2, alpha=0.75)
        axes[1].plot(result.time, result.effective_occupancy[:, load_idx], color=color)
        axes[1].axhline(load.weight, color=color, linestyle="--", linewidth=1.0, alpha=0.55)
        axes[1].axhline(staffing_target, color=color, linestyle=":", linewidth=1.2, alpha=0.75)
        axes[2].plot(result.time, result.prices[:, load_idx], color=color)

    axes[0].set_ylabel("Robots in contact")
    axes[0].set_title("Physical quorum: dashed = weight, dotted = efficient target")
    axes[1].set_ylabel("Effective occupancy")
    axes[1].set_title("Decision layer: proximity-weighted occupancy")
    axes[2].set_ylabel("Adaptive price")
    axes[2].set_xlabel("Time [s]")
    axes[2].set_title("Single-clock price signal")
    for axis in axes:
        axis.grid(True, alpha=0.3)
    axes[0].legend(ncol=3, fontsize=8)
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_assignments(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot the assignment chosen by each robot through time."""

    figure, axis = plt.subplots(figsize=(12, 6))
    matrix = result.assignments.T
    cmap = plt.cm.get_cmap("tab20", len(result.loads) + 1)
    image = axis.imshow(
        matrix,
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
        vmin=0,
        vmax=len(result.loads),
        extent=[result.time[0], result.time[-1], result.config.robot_count + 0.5, 0.5],
    )
    axis.set_xlabel("Time [s]")
    axis.set_ylabel("Robot")
    axis.set_title("Robot assignment heatmap (0 = idle)")
    ticks = np.arange(0, len(result.loads) + 1)
    colorbar = figure.colorbar(image, ax=axis, ticks=ticks)
    colorbar.set_label("Assigned load")
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_kinematics(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot motor limits, communication, and formation diagnostics."""

    cfg = result.config
    max_linear = np.max(np.abs(result.linear_speeds), axis=1)
    max_angular = np.max(np.abs(result.angular_speeds), axis=1)
    max_wheel = np.max(np.abs(result.wheel_speeds), axis=(1, 2))
    mean_degree = np.mean(result.communication_degrees, axis=1)
    min_degree = np.min(result.communication_degrees, axis=1)
    active_mask = result.formation_errors > 0.0
    active_sum = np.sum(np.where(active_mask, result.formation_errors, 0.0), axis=1)
    active_count = np.sum(active_mask, axis=1)
    active_form_error = np.divide(
        active_sum,
        active_count,
        out=np.zeros_like(active_sum),
        where=active_count > 0,
    )

    figure, axes = plt.subplots(4, 1, figsize=(12, 11), sharex=True)
    axes[0].plot(result.time, max_linear, color="#2563eb", label="observed")
    axes[0].axhline(min(cfg.max_speed, cfg.wheel_speed_limit), color="black", linestyle="--", label="limit")
    axes[0].set_ylabel("v [m/s]")
    axes[0].set_title("Linear speed saturation")

    axes[1].plot(result.time, max_angular, color="#7c3aed", label="observed")
    axes[1].axhline(cfg.max_angular_speed, color="black", linestyle="--", label="limit")
    axes[1].set_ylabel("omega [rad/s]")
    axes[1].set_title("Angular speed saturation")

    axes[2].plot(result.time, max_wheel, color="#dc2626", label="observed")
    axes[2].axhline(cfg.max_wheel_angular_speed, color="black", linestyle="--", label="limit")
    axes[2].set_ylabel("wheel [rad/s]")
    axes[2].set_title("Wheel motor saturation")

    axes[3].plot(result.time, mean_degree, color="#16a34a", label="mean degree")
    axes[3].plot(result.time, min_degree, color="#f97316", label="min degree")
    axes[3].plot(result.time, active_form_error, color="#0f172a", label="mean formation error")
    axes[3].set_ylabel("diagnostics")
    axes[3].set_xlabel("Time [s]")
    axes[3].set_title("Communication and formation diagnostics")

    for axis in axes:
        axis.grid(True, alpha=0.3)
        axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def plot_warehouse_formations(result: WarehouseResult, output_path: str | Path | None = None) -> Figure:
    """Plot pickup and arrival formations for each delivered load."""

    delivered_indices = [
        idx
        for idx, load in enumerate(result.loads)
        if load.status == LOAD_DELIVERED and np.any(result.load_status[:, idx] == LOAD_TRANSPORT)
    ]
    if not delivered_indices:
        delivered_indices = [
            idx for idx, _load in enumerate(result.loads) if np.any(result.load_status[:, idx] != LOAD_NOT_SPAWNED)
        ]

    rows = max(len(delivered_indices), 1)
    figure, axes = plt.subplots(rows, 2, figsize=(11, 4.2 * rows), squeeze=False)
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(result.loads), 1)))

    for row, load_idx in enumerate(delivered_indices):
        load = result.loads[load_idx]
        status = result.load_status[:, load_idx]
        transport_steps = np.flatnonzero(status == LOAD_TRANSPORT)
        if transport_steps.size:
            start_step = int(transport_steps[0])
            end_step = int(transport_steps[-1])
        else:
            active_steps = np.flatnonzero(status != LOAD_NOT_SPAWNED)
            start_step = int(active_steps[0])
            end_step = int(active_steps[-1])
        _draw_formation_panel(
            axes[row, 0],
            result=result,
            load_idx=load_idx,
            step=start_step,
            title=f"{load.identifier}: formation at pickup",
            color=colors[load_idx],
        )
        _draw_formation_panel(
            axes[row, 1],
            result=result,
            load_idx=load_idx,
            step=end_step,
            title=f"{load.identifier}: formation near delivery",
            color=colors[load_idx],
        )

    figure.suptitle("Coalition formations: source assembly vs arrival", fontsize=14)
    figure.tight_layout()
    _save_if_requested(figure, output_path)
    return figure


def save_warehouse_animation(
    result: WarehouseResult,
    output_path: str | Path,
    fps: int = 18,
    stride: int = 3,
) -> Path:
    """Save an MP4 animation of the full warehouse simulation."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_indices = list(range(0, len(result.time), max(1, stride)))
    if frame_indices[-1] != len(result.time) - 1:
        frame_indices.append(len(result.time) - 1)

    figure, axis = plt.subplots(figsize=(8, 8))

    def draw(frame_idx: int) -> list[object]:
        axis.clear()
        _draw_warehouse_base(axis, result, include_labels=False)
        _draw_motion_history(axis, result, frame_idx)
        _draw_snapshot(axis, result, frame_idx)
        axis.set_title(
            f"Warehouse AMR simulation | t={result.time[frame_idx]:.1f}s | "
            f"delivered={int(np.sum(result.load_status[frame_idx] == LOAD_DELIVERED))}/{len(result.loads)}"
        )
        return []

    animation = FuncAnimation(
        figure,
        draw,
        frames=frame_indices,
        interval=1000 / max(fps, 1),
        blit=False,
        repeat=False,
    )
    writer = FFMpegWriter(fps=fps, metadata={"title": "Warehouse realistic AMR simulation"})
    animation.save(output, writer=writer, dpi=150)
    plt.close(figure)
    return output


def save_warehouse_plot_suite(result: WarehouseResult, output_dir: str | Path) -> list[Path]:
    """Save the full PNG suite for a warehouse result."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    outputs = [
        directory / "01_warehouse_overview.png",
        directory / "02_warehouse_storyboard.png",
        directory / "03_load_timeline.png",
        directory / "04_recruitment_prices_quorum.png",
        directory / "05_robot_assignments.png",
        directory / "06_kinematics_and_safety.png",
        directory / "07_formations_pickup_vs_arrival.png",
    ]
    figures = [
        plot_warehouse_overview(result, outputs[0]),
        plot_warehouse_storyboard(result, outputs[1]),
        plot_warehouse_timeline(result, outputs[2]),
        plot_warehouse_recruitment(result, outputs[3]),
        plot_warehouse_assignments(result, outputs[4]),
        plot_warehouse_kinematics(result, outputs[5]),
        plot_warehouse_formations(result, outputs[6]),
    ]
    for figure in figures:
        plt.close(figure)
    return outputs


def _draw_warehouse_base(axis: plt.Axes, result: WarehouseResult, include_labels: bool = True) -> None:
    half = result.config.half_size
    axis.set_xlim(-half - 0.5, half + 0.5)
    axis.set_ylim(-half - 0.5, half + 0.5)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.grid(True, alpha=0.22)
    axis.add_patch(plt.Rectangle((-half, -half), 2 * half, 2 * half, fill=False, linewidth=1.8))
    for obstacle in result.obstacles:
        axis.add_patch(
            plt.Circle(obstacle.center, obstacle.influence_radius, color="#fca5a5", alpha=0.12, linewidth=0)
        )
        axis.add_patch(
            plt.Circle(obstacle.center, obstacle.radius, color="#991b1b", alpha=0.65)
        )
        if include_labels:
            axis.annotate("obs", obstacle.center, color="white", fontsize=8, ha="center", va="center")


def _draw_snapshot(axis: plt.Axes, result: WarehouseResult, step: int) -> None:
    assignments = result.assignments[step]
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(result.loads), 1)))
    for load_idx, load in enumerate(result.loads):
        status = result.load_status[step, load_idx]
        if status == LOAD_NOT_SPAWNED:
            axis.scatter(load.source[0], load.source[1], marker="s", s=50, color=colors[load_idx], alpha=0.22)
            continue
        position = result.load_positions[step, load_idx]
        marker = "P" if status == LOAD_RECRUITING else "D" if status == LOAD_TRANSPORT else "*"
        axis.scatter(position[0], position[1], marker=marker, s=140, color=colors[load_idx], edgecolor="black")
        axis.scatter(load.target[0], load.target[1], marker="*", s=90, color=colors[load_idx], alpha=0.45)
        axis.annotate(f"{load.identifier}\nw={load.weight}", position, xytext=(5, 5), textcoords="offset points", fontsize=8)

    positions = result.robot_positions[step]
    for robot_idx, position in enumerate(positions):
        assignment = assignments[robot_idx]
        if assignment == 0:
            color = "0.55"
        else:
            color = colors[assignment - 1]
            load_position = result.load_positions[step, assignment - 1]
            axis.plot([position[0], load_position[0]], [position[1], load_position[1]], color=color, alpha=0.16)
        axis.scatter(position[0], position[1], color=color, s=28, edgecolor="black", linewidth=0.3)


def _draw_motion_history(axis: plt.Axes, result: WarehouseResult, step: int) -> None:
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(result.loads), 1)))
    start = max(0, step - 90)
    for robot_idx in range(result.config.robot_count):
        trajectory = result.robot_positions[start : step + 1, robot_idx]
        axis.plot(trajectory[:, 0], trajectory[:, 1], color="0.5", linewidth=0.6, alpha=0.18)
    for load_idx, _load in enumerate(result.loads):
        active = result.load_status[: step + 1, load_idx] != LOAD_NOT_SPAWNED
        if np.any(active):
            load_path = result.load_positions[: step + 1, load_idx][active]
            axis.plot(load_path[:, 0], load_path[:, 1], color=colors[load_idx], linewidth=2.2, alpha=0.9)


def _draw_formation_panel(
    axis: plt.Axes,
    result: WarehouseResult,
    load_idx: int,
    step: int,
    title: str,
    color: np.ndarray,
) -> None:
    load = result.loads[load_idx]
    center = result.load_positions[step, load_idx]
    assignments = result.assignments[step]
    positions = result.robot_positions[step]
    members = np.flatnonzero(assignments == load_idx + 1)
    nearby_idle = np.flatnonzero(
        (assignments != load_idx + 1)
        & (np.linalg.norm(positions - center[None, :], axis=1) <= 2.6)
    )

    radius = max(
        result.config.formation_radius_base + result.config.formation_radius_per_weight * np.sqrt(load.weight),
        0.52 * max(load.weight, max(len(members), 1)) / (2.0 * np.pi),
    )
    contact = result.config.contact_radius
    theta = np.linspace(0.0, 2.0 * np.pi, 240)
    axis.plot(center[0] + contact * np.cos(theta), center[1] + contact * np.sin(theta), color="0.4", linestyle=":", label="contact radius")
    axis.plot(center[0] + radius * np.cos(theta), center[1] + radius * np.sin(theta), color=color, linestyle="--", label="formation ring")

    if nearby_idle.size:
        axis.scatter(
            positions[nearby_idle, 0],
            positions[nearby_idle, 1],
            color="0.72",
            s=26,
            label="other nearby robots",
        )
    if members.size:
        axis.scatter(
            positions[members, 0],
            positions[members, 1],
            color=color,
            s=55,
            edgecolor="black",
            linewidth=0.5,
            label="coalition robots",
        )
        for member in members:
            axis.plot([positions[member, 0], center[0]], [positions[member, 1], center[1]], color=color, alpha=0.22)

    axis.scatter(center[0], center[1], marker="D", s=130, color=color, edgecolor="black", label="load")
    axis.scatter(load.target[0], load.target[1], marker="*", s=120, color=color, edgecolor="black", alpha=0.75, label="target")
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlim(center[0] - 2.8, center[0] + 2.8)
    axis.set_ylim(center[1] - 2.8, center[1] + 2.8)
    axis.grid(True, alpha=0.25)
    axis.set_title(
        f"{title}\n"
        f"t={result.time[step]:.1f}s, assigned={members.size}, "
        f"contact={result.contact_counts[step, load_idx]:.0f}, weight={load.weight}"
    )
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.legend(loc="upper right", fontsize=7, framealpha=0.9)


def _storyboard_times(result: WarehouseResult) -> list[float]:
    delivered_times = [load.delivered_time for load in result.loads if np.isfinite(load.delivered_time)]
    interesting = [result.time[0], 0.33 * result.time[-1], 0.66 * result.time[-1], result.time[-1]]
    if delivered_times:
        interesting[2] = float(np.median(delivered_times))
    return sorted(float(np.clip(value, result.time[0], result.time[-1])) for value in interesting)


def _save_if_requested(figure: Figure, output_path: str | Path | None) -> None:
    if output_path is not None:
        figure.savefig(Path(output_path), dpi=220, bbox_inches="tight")
