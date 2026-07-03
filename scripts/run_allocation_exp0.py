"""Run EXP0: one-shot AMR allocation for homogeneous robots and heterogeneous loads."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.allocation import (
    Assignment,
    CentralizedClassicAllocator,
    CentralizedUtilityAllocator,
    DecisionContext,
    DecentralizedAuctionAllocator,
    DecentralizedClassicGreedyAllocator,
    SmithQRAllocator,
    timed_allocate,
)
from viu_mrob_tfm.domain import CapacityModel, LoadSpec, RobotRuntimeState, RobotSpec, WarehouseMap, WorldState


METHODS = [
    ("A", "Centralized classic min-cost", CentralizedClassicAllocator()),
    ("B", "Decentralized classic greedy", DecentralizedClassicGreedyAllocator()),
    ("C", "Centralized SOTA proxy", CentralizedUtilityAllocator()),
    ("D", "Decentralized SOTA auction", DecentralizedAuctionAllocator()),
    (
        "E",
        "Our basic Smith-QR",
        SmithQRAllocator(
            name="our_basic_smith_qr",
            idle_score=0.05,
            distance_weight=0.22,
            deficit_weight=1.2,
            stickiness=0.0,
        ),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robots", type=int, default=10, help="Number of homogeneous AMRs.")
    parser.add_argument("--loads", type=int, default=4, help="Number of heterogeneous loads.")
    parser.add_argument("--seed", type=int, default=20260703)
    parser.add_argument("--size", type=float, default=10.0, help="Square world size in meters.")
    parser.add_argument("--output", type=Path, default=Path("results/allocation_exp0"))
    parser.add_argument("--fps", type=int, default=12)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = ROOT / args.output
    figures_dir = output_dir / "figures"
    videos_dir = output_dir / "videos"
    tables_dir = output_dir / "tables"
    for directory in (figures_dir, videos_dir, tables_dir):
        directory.mkdir(parents=True, exist_ok=True)

    world = build_world(robot_count=args.robots, load_count=args.loads, seed=args.seed, size=args.size)
    context = DecisionContext(world=world)

    results: list[dict[str, Any]] = []
    assignments: dict[str, Assignment] = {}
    for code, label, allocator in METHODS:
        assignment, runtime_ms = timed_allocate(allocator, context)
        method_id = f"{code}_{allocator.name}"
        assignments[method_id] = assignment
        metrics = summarize_assignment(world, assignment, runtime_ms)
        metrics.update({"method_code": code, "method_label": label, "method_id": method_id})
        results.append(metrics)

    save_summary_csv(tables_dir / "summary.csv", results)
    save_assignments_csv(tables_dir / "assignments.csv", world, assignments)
    save_manifest(output_dir / "manifest.json", args, world, results)

    plot_initial_state(world, figures_dir / "initial_state.png")
    plot_final_grid(world, assignments, results, figures_dir / "final_allocations.png")
    for row in results:
        assignment = assignments[row["method_id"]]
        plot_single_final(world, assignment, row, figures_dir / f"final_{row['method_id']}.png")

    video_path = videos_dir / "allocation_transition.mp4"
    video_status = save_transition_video(world, assignments, results, video_path, fps=args.fps)
    report_path = output_dir / "report.md"
    save_report(report_path, args, results, video_path if video_status else None)

    print(json.dumps({"output_dir": str(output_dir), "report": str(report_path), "video": str(video_path)}, indent=2))
    return 0


def build_world(robot_count: int, load_count: int, seed: int, size: float) -> WorldState:
    if robot_count < 1:
        raise ValueError("--robots must be positive.")
    if load_count < 1:
        raise ValueError("--loads must be positive.")

    rng = np.random.default_rng(seed)
    half = 0.5 * size
    robots: list[RobotRuntimeState] = []
    for idx in range(robot_count):
        spec = RobotSpec(
            identifier=f"amr-{idx + 1:02d}",
            capacity=CapacityModel(payload_kg=1.0, force_limit_n=10.0, torque_limit_nm=2.0),
        )
        robots.append(
            RobotRuntimeState(
                spec=spec,
                position=rng.uniform(-0.82 * half, 0.82 * half, size=2),
                heading=float(rng.uniform(-np.pi, np.pi)),
                battery_fraction=1.0,
            )
        )

    demand_template = np.array([1, 2, 3, 5, 4, 6, 2, 5], dtype=int)
    if load_count <= demand_template.size:
        demands = demand_template[:load_count]
    else:
        extra = rng.integers(2, 7, size=load_count - demand_template.size)
        demands = np.concatenate([demand_template, extra])

    loads: list[LoadSpec] = []
    for idx, demand in enumerate(demands):
        pickup = rng.uniform(-0.72 * half, 0.72 * half, size=2)
        destination = rng.uniform(-0.72 * half, 0.72 * half, size=2)
        reward = float(0.8 + 0.42 * demand + 0.08 * idx)
        loads.append(
            LoadSpec(
                identifier=f"load-{idx + 1:02d}",
                pickup=pickup,
                destination=destination,
                mass_kg=float(demand),
                min_capacity_kg=float(demand),
                min_coalition_size=int(demand),
                reward=reward,
            )
        )
    return WorldState(robots=robots, loads=loads, map=WarehouseMap(size_m=size))


def summarize_assignment(world: WorldState, assignment: Assignment, runtime_ms: float) -> dict[str, Any]:
    labels = np.asarray(assignment.labels, dtype=int)
    counts = np.array([int(np.sum(labels == idx + 1)) for idx in range(len(world.loads))], dtype=int)
    demands = np.array([load.min_coalition_size for load in world.loads], dtype=int)
    rewards = np.array([load.reward for load in world.loads], dtype=float)
    satisfied = counts >= demands
    distances = []
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        load = world.loads[label - 1]
        distances.append(float(np.linalg.norm(world.robots[robot_idx].position - load.pickup)))

    return {
        "runtime_ms": runtime_ms,
        "allocated_robots": int(np.sum(labels > 0)),
        "idle_robots": int(np.sum(labels == 0)),
        "satisfied_loads": int(np.sum(satisfied)),
        "load_count": len(world.loads),
        "total_deficit": int(np.sum(np.maximum(demands - counts, 0))),
        "total_overassignment": int(np.sum(np.maximum(counts - demands, 0))),
        "captured_reward": float(np.sum(rewards[satisfied])),
        "total_distance_m": float(np.sum(distances)) if distances else 0.0,
        "mean_distance_m": float(np.mean(distances)) if distances else 0.0,
        "load_counts": " ".join(str(value) for value in counts.tolist()),
        "load_demands": " ".join(str(value) for value in demands.tolist()),
        "idle_robot_ids": " ".join(
            world.robots[idx].identifier for idx, label in enumerate(labels) if label == 0
        ),
        "allocated_robot_ids": " ".join(
            world.robots[idx].identifier for idx, label in enumerate(labels) if label > 0
        ),
    }


def save_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "method_code",
        "method_label",
        "method_id",
        "allocated_robots",
        "idle_robots",
        "satisfied_loads",
        "load_count",
        "total_deficit",
        "total_overassignment",
        "captured_reward",
        "total_distance_m",
        "mean_distance_m",
        "runtime_ms",
        "load_demands",
        "load_counts",
        "idle_robot_ids",
        "allocated_robot_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def save_assignments_csv(path: Path, world: WorldState, assignments: dict[str, Assignment]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["method_id", "robot_id", "load_id", "load_index", "distance_m"],
        )
        writer.writeheader()
        for method_id, assignment in assignments.items():
            for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
                load_id = "idle"
                distance = 0.0
                if label > 0:
                    load = world.loads[label - 1]
                    load_id = load.identifier
                    distance = float(np.linalg.norm(world.robots[robot_idx].position - load.pickup))
                writer.writerow(
                    {
                        "method_id": method_id,
                        "robot_id": world.robots[robot_idx].identifier,
                        "load_id": load_id,
                        "load_index": int(label),
                        "distance_m": f"{distance:.6f}",
                    }
                )


def save_manifest(path: Path, args: argparse.Namespace, world: WorldState, rows: list[dict[str, Any]]) -> None:
    manifest = {
        "experiment_id": "EXP0_static_allocation",
        "seed": args.seed,
        "robot_count": len(world.robots),
        "load_count": len(world.loads),
        "loads": [
            {
                "id": load.identifier,
                "demand": load.min_coalition_size,
                "reward": load.reward,
                "pickup": load.pickup.tolist(),
            }
            for load in world.loads
        ],
        "methods": rows,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def plot_initial_state(world: WorldState, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 8))
    draw_scene(axis, world, None, "EXP0 initial state: all AMRs idle", progress=0.0)
    figure.tight_layout()
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def plot_single_final(world: WorldState, assignment: Assignment, row: dict[str, Any], path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 8))
    title = f"{row['method_code']}. {row['method_label']}"
    draw_scene(axis, world, assignment, title, row=row, progress=1.0)
    figure.tight_layout()
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def plot_final_grid(
    world: WorldState,
    assignments: dict[str, Assignment],
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(16, 10), sharex=True, sharey=True)
    axes_flat = axes.ravel()
    draw_scene(axes_flat[0], world, None, "Initial idle state", progress=0.0)
    for axis, row in zip(axes_flat[1:], rows):
        draw_scene(
            axis,
            world,
            assignments[row["method_id"]],
            f"{row['method_code']}. {row['method_label']}",
            row=row,
            progress=1.0,
        )
    for axis in axes_flat[len(rows) + 1 :]:
        axis.axis("off")
    figure.suptitle("EXP0 static allocation: homogeneous AMRs, heterogeneous loads", fontsize=15)
    figure.tight_layout()
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def draw_scene(
    axis: plt.Axes,
    world: WorldState,
    assignment: Assignment | None,
    title: str,
    row: dict[str, Any] | None = None,
    progress: float = 1.0,
) -> None:
    half = 0.5 * world.map.size_m
    axis.set_xlim(-half, half)
    axis.set_ylim(-half, half)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(True, alpha=0.18)
    axis.set_title(title, fontsize=10)
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")

    load_colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(world.loads), 1)))
    labels = np.zeros(len(world.robots), dtype=int) if assignment is None else np.asarray(assignment.labels, dtype=int)

    for load_idx, load in enumerate(world.loads):
        color = load_colors[load_idx]
        axis.scatter(load.pickup[0], load.pickup[1], marker="s", s=150, color=color, edgecolor="black", zorder=5)
        axis.annotate(
            f"L{load_idx + 1}\nd={load.min_coalition_size}\nr={load.reward:.1f}",
            xy=load.pickup,
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=7,
            color="black",
            zorder=6,
        )

    for robot_idx, robot in enumerate(world.robots):
        label = int(labels[robot_idx])
        color = "0.70" if label == 0 else load_colors[label - 1]
        if label > 0:
            load_position = world.loads[label - 1].pickup
            axis.plot(
                [robot.position[0], load_position[0]],
                [robot.position[1], load_position[1]],
                color=color,
                alpha=0.12 + 0.55 * progress,
                linewidth=1.2,
                zorder=2,
            )
        axis.scatter(
            robot.position[0],
            robot.position[1],
            marker="o",
            s=58,
            color=color,
            edgecolor="black",
            linewidth=0.6,
            zorder=7,
        )
        axis.annotate(
            f"R{robot_idx + 1}",
            xy=robot.position,
            xytext=(4, -9),
            textcoords="offset points",
            fontsize=6,
            color="black",
            zorder=8,
        )

    if row is not None:
        axis.text(
            0.02,
            0.02,
            (
                f"satisfied {row['satisfied_loads']}/{row['load_count']} | "
                f"deficit {row['total_deficit']} | idle {row['idle_robots']}\n"
                f"counts [{row['load_counts']}] vs demand [{row['load_demands']}]"
            ),
            transform=axis.transAxes,
            fontsize=7,
            va="bottom",
            ha="left",
            bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "0.85", "linewidth": 0.6},
        )


def save_transition_video(
    world: WorldState,
    assignments: dict[str, Assignment],
    rows: list[dict[str, Any]],
    path: Path,
    fps: int,
) -> bool:
    figure, axes = plt.subplots(2, 3, figsize=(16, 10), sharex=True, sharey=True)
    axes_flat = axes.ravel()
    frame_count = max(24, fps * 3)

    def draw(frame_idx: int) -> list[object]:
        progress = frame_idx / max(frame_count - 1, 1)
        for axis in axes_flat:
            axis.clear()
        draw_scene(axes_flat[0], world, None, "Initial idle state", progress=0.0)
        for axis, row in zip(axes_flat[1:], rows):
            draw_scene(
                axis,
                world,
                assignments[row["method_id"]],
                f"{row['method_code']}. {row['method_label']}",
                row=row,
                progress=progress,
            )
        figure.suptitle(f"EXP0 allocation transition | t={progress:.2f}", fontsize=15)
        return []

    animation = FuncAnimation(figure, draw, frames=frame_count, interval=1000 / max(fps, 1), blit=False)
    try:
        writer = FFMpegWriter(fps=fps, metadata={"title": "EXP0 static AMR allocation"})
        animation.save(path, writer=writer, dpi=150)
        ok = True
    except Exception as exc:  # pragma: no cover - backend dependent
        (path.parent / "allocation_transition.warning.txt").write_text(str(exc), encoding="utf-8")
        ok = False
    finally:
        plt.close(figure)
    return ok


def save_report(path: Path, args: argparse.Namespace, rows: list[dict[str, Any]], video_path: Path | None) -> None:
    best = max(rows, key=lambda row: (row["satisfied_loads"], row["captured_reward"], -row["total_distance_m"]))
    lines = [
        "# EXP0 static allocation",
        "",
        f"- Seed: `{args.seed}`",
        f"- Robots: `{args.robots}` homogeneous AMRs",
        f"- Loads: `{args.loads}` heterogeneous load demands",
        "- Scope: allocation only; no transport dynamics or collision avoidance.",
        "",
        "## Methods",
        "",
        "| Code | Method | Interpretation |",
        "|---|---|---|",
        "| A | Centralized classic min-cost | Hungarian assignment over replicated load slots. |",
        "| B | Decentralized classic greedy | Sequential nearest-load local rule. |",
        "| C | Centralized SOTA proxy | Reward-aware centralized assignment under scarcity. |",
        "| D | Decentralized SOTA auction | CBBA-like local auction with deficit prices. |",
        "| E | Our basic Smith-QR | Existing Smith-QR allocator facade, no tuning. |",
        "",
        "## Summary",
        "",
        "| Method | Satisfied loads | Deficit | Overassignment | Idle | Reward | Distance [m] |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {method} | {sat}/{loads} | {deficit} | {over} | {idle} | {reward:.3f} | {dist:.3f} |".format(
                method=row["method_label"],
                sat=row["satisfied_loads"],
                loads=row["load_count"],
                deficit=row["total_deficit"],
                over=row["total_overassignment"],
                idle=row["idle_robots"],
                reward=row["captured_reward"],
                dist=row["total_distance_m"],
            )
        )
    lines.extend(
        [
            "",
            f"Best by satisfied loads, reward, then distance: **{best['method_label']}**.",
            "",
            "## Artifacts",
            "",
            "- `figures/initial_state.png`",
            "- `figures/final_allocations.png`",
            "- `tables/summary.csv`",
            "- `tables/assignments.csv`",
        ]
    )
    if video_path is not None:
        lines.append("- `videos/allocation_transition.mp4`")
    else:
        lines.append("- MP4 video was requested but the local ffmpeg backend was unavailable; see `videos/allocation_transition.warning.txt`.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
