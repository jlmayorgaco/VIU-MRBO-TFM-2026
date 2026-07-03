"""Plots and lightweight videos for SP1 recruitment experiments."""

from __future__ import annotations

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


def save_recruitment_snapshot(world: WorldState, assignment: Assignment, path: Path, title: str) -> None:
    figure, axis = plt.subplots(figsize=(7, 7))
    _draw_world(axis, world, assignment, progress=1.0, title=title)
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def save_recruitment_video(world: WorldState, assignment: Assignment, path: Path, title: str, fps: int = 12) -> bool:
    figure, axis = plt.subplots(figsize=(7, 7))
    frames = max(48, fps * 4)

    def draw(frame_idx: int) -> list[object]:
        axis.clear()
        progress = frame_idx / max(frames - 1, 1)
        _draw_world(axis, world, assignment, progress=progress, title=f"{title} | t={progress:.2f}")
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
