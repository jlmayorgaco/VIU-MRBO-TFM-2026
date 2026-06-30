"""Run canonical warehouse visualizations with coordinate trajectory export.

This script is visualization-only. It reuses the validated Python simulator and
v2.7 scenario/method configuration, records coordinate histories from
``WarehouseResult``, and renders MP4 videos plus PDF-ready static figures.

It does not run the 20-seed benchmark campaign.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_v27_daemon import build_methods, build_triage_scarcity_priority, load_params  # noqa: E402
from benchmark_warehouse_methods import ScenarioRun, _rho_config, _summary_row, scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import (  # noqa: E402
    LOAD_CANCELED,
    LOAD_DELIVERED,
    LOAD_NOT_SPAWNED,
    LOAD_RECRUITING,
    LOAD_TRANSPORT,
    WarehouseConfig,
    WarehouseResult,
    run_warehouse_simulation,
)


CANONICAL_SEED = 2026
BACKUP_SEEDS = [2027, 2028]
DEFAULT_SEEDS = [CANONICAL_SEED, *BACKUP_SEEDS]
FPS = 24
VIDEO_SECONDS = 30
LOG_HZ = 12.0

VIS_METHODS = [
    "smith_full",
    "classic_greedy_nearest",
    "classic_centralized_mincost",
    "oracle_clairvoyant",
]

METHOD_TO_V27 = {
    "smith_full": "smith",
    "classic_greedy_nearest": "classic_greedy_nearest",
    "classic_centralized_mincost": "classic_centralized_mincost",
    "oracle_clairvoyant": "oracle_clairvoyant",
}

METHOD_LABELS = {
    "smith_full": "Smith full",
    "classic_greedy_nearest": "Greedy",
    "classic_centralized_mincost": "Centralized",
    "oracle_clairvoyant": "Oracle",
}

METHOD_COLORS = {
    "smith_full": "#1b9e77",
    "classic_greedy_nearest": "#ff7f00",
    "classic_centralized_mincost": "#377eb8",
    "oracle_clairvoyant": "#4daf4a",
}

TASK_COLORS = [
    "#bdbdbd",
    "#1b9e77",
    "#377eb8",
    "#ff7f00",
    "#984ea3",
    "#e41a1c",
    "#a65628",
    "#f781bf",
    "#999999",
    "#66c2a5",
    "#fc8d62",
]

LOAD_STATUS_LABELS = {
    LOAD_NOT_SPAWNED: "announced",
    LOAD_RECRUITING: "recruiting",
    LOAD_TRANSPORT: "moving",
    LOAD_DELIVERED: "delivered",
    LOAD_CANCELED: "expired",
}


@dataclass(frozen=True)
class ScenarioSpec:
    key: str
    title: str
    run: ScenarioRun
    canonical_seed: int = CANONICAL_SEED
    reason: str = "Semilla canonica 2026 usada por v2.7; no fue elegida por rendimiento."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-trajectory", action="store_true", help="Write trajectory/load parquet logs.")
    parser.add_argument("--canonical-only", action="store_true", help="Run only the canonical seed, not backups.")
    parser.add_argument("--skip-render", action="store_true", help="Export logs but skip video/static rendering.")
    parser.add_argument("--params", type=Path, default=Path("configs/tuned_params_v26.json"))
    parser.add_argument("--out-trajectories", type=Path, default=Path("results/trajectories"))
    parser.add_argument("--out-animations", type=Path, default=Path("results/animations"))
    parser.add_argument("--figures-dir", type=Path, default=Path("results/figures_pdf/scenarios"))
    parser.add_argument("--log-hz", type=float, default=LOG_HZ)
    parser.add_argument("--fps", type=int, default=FPS)
    parser.add_argument("--video-seconds", type=float, default=VIDEO_SECONDS)
    parser.add_argument(
        "--max-sim-duration",
        type=float,
        default=180.0,
        help="Cap simulation horizon for visualization runs; v2.7 metrics remain the citable full runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.record_trajectory:
        raise SystemExit("Refusing to run visualization batch without --record-trajectory.")

    for path in [args.out_trajectories, args.out_animations, args.figures_dir, args.out_animations / "frames"]:
        path.mkdir(parents=True, exist_ok=True)

    tuned_params = load_params(args.params)
    methods = {method.key: method for method in build_methods(tuned_params)}
    scenarios = build_scenarios()
    seeds = [CANONICAL_SEED] if args.canonical_only else DEFAULT_SEEDS
    manifest_rows: list[dict[str, Any]] = []
    sanity_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    results: dict[tuple[str, str, int], WarehouseResult] = {}

    sanity_rows.extend(run_logging_sanity(scenarios[0], methods["smith"], args))

    for scenario in scenarios:
        for seed in seeds:
            for method_id in VIS_METHODS:
                method = methods[METHOD_TO_V27[method_id]]
                print(f"RUN {scenario.key}/{method_id}/seed={seed}", flush=True)
                started = time.perf_counter()
                config = config_for(scenario.run, method, seed, max_duration=args.max_sim_duration)
                result = run_warehouse_simulation(config)
                runtime = time.perf_counter() - started
                row = _summary_row(
                    result.summary,
                    scenario.run,
                    method.policy,
                    method.label,
                    method.family,
                    runtime,
                    result.time.size,
                )
                row.update({"visual_scenario": scenario.key, "visual_method": method_id})
                summary_rows.append(row)

                robot_log, load_log = export_trajectory_logs(
                    result=result,
                    scenario=scenario,
                    method_id=method_id,
                    seed=seed,
                    out_dir=args.out_trajectories,
                    log_hz=args.log_hz,
                )
                manifest_rows.append(
                    manifest_row(
                        robot_log,
                        scenario,
                        method_id,
                        seed,
                        args.fps,
                        robot_log,
                        "robot trajectory log from Python simulator",
                    )
                )
                manifest_rows.append(
                    manifest_row(
                        load_log,
                        scenario,
                        method_id,
                        seed,
                        args.fps,
                        load_log,
                        "load trajectory log from Python simulator",
                    )
                )
                if seed == scenario.canonical_seed:
                    results[(scenario.key, method_id, seed)] = result

                if seed == scenario.canonical_seed and not args.skip_render:
                    mp4 = render_individual_video(
                        result=result,
                        scenario=scenario,
                        method_id=method_id,
                        out_dir=args.out_animations,
                        fps=args.fps,
                        video_seconds=args.video_seconds,
                    )
                    manifest_rows.append(
                        manifest_row(mp4, scenario, method_id, seed, args.fps, robot_log, "individual MP4, H.264")
                    )

        if not args.skip_render:
            comparison = render_comparison_video(
                results={method_id: results[(scenario.key, method_id, scenario.canonical_seed)] for method_id in VIS_METHODS[:3]},
                scenario=scenario,
                out_dir=args.out_animations,
                fps=args.fps,
                video_seconds=args.video_seconds,
            )
            manifest_rows.append(
                manifest_row(
                    comparison,
                    scenario,
                    "smith_full|greedy|centralized",
                    scenario.canonical_seed,
                    args.fps,
                    args.out_trajectories,
                    "side-by-side MP4, H.264",
                )
            )
            for method_id in VIS_METHODS:
                result = results[(scenario.key, method_id, scenario.canonical_seed)]
                snapshots = render_snapshots(result, scenario, method_id, args.figures_dir)
                paths = render_paths(result, scenario, method_id, args.figures_dir)
                for artifact in [*snapshots, *paths]:
                    manifest_rows.append(
                        manifest_row(
                            artifact,
                            scenario,
                            method_id,
                            scenario.canonical_seed,
                            args.fps,
                            args.out_trajectories,
                            "static figure derived from trajectories",
                        )
                    )

    write_csv(args.out_animations / "manifest.csv", manifest_rows)
    write_csv(args.out_animations / "trajectory_summary.csv", summary_rows)
    write_csv(args.out_animations / "trajectory_sanity.csv", sanity_rows)
    write_readme(args.out_animations / "README.md", scenarios, seeds, args)

    print("Trajectory visualization batch complete.")
    print(f"  trajectories: {args.out_trajectories}")
    print(f"  animations:   {args.out_animations}")
    print(f"  manifest:     {args.out_animations / 'manifest.csv'}")
    return 0


def build_scenarios() -> list[ScenarioSpec]:
    nominal = scenario_runs("nominal_flow", quick=False)[0]
    failure = scenario_runs("robot_failures", quick=False)[0]
    comm = [run for run in scenario_runs("comm_degradation", quick=True) if run.case == "R3_p0"][0]
    triage = build_triage_scarcity_priority()[0]
    return [
        ScenarioSpec("abundance", "Abundancia", nominal),
        ScenarioSpec("scarcity_priority", "Escasez con prioridad", triage),
        ScenarioSpec("robot_failure", "Fallo de robot", failure),
        ScenarioSpec("comm_degradation", "Degradacion comunicacion R3", comm),
    ]


def config_for(
    scenario_run: ScenarioRun,
    method: Any,
    seed: int,
    max_duration: float | None = None,
) -> WarehouseConfig:
    overrides = dict(scenario_run.overrides)
    overrides.update(method.params)
    if max_duration is not None and math.isfinite(max_duration):
        duration = min(float(overrides.get("duration", max_duration)), float(max_duration))
        original_duration = float(overrides.get("duration", duration))
        overrides["duration"] = duration
        if scenario_run.name == "robot_failures":
            overrides["failure_time"] = duration * 0.40
            overrides["revive_time"] = duration * 0.70
        elif "failure_time" in overrides and original_duration > 0.0:
            overrides["failure_time"] = float(overrides["failure_time"]) * duration / original_duration
        if "revive_time" in overrides and scenario_run.name != "robot_failures" and original_duration > 0.0:
            overrides["revive_time"] = float(overrides["revive_time"]) * duration / original_duration
    if scenario_run.name == "nominal_flow":
        # Explicitly make the visualization scenario abundant while preserving
        # v2.7-style dynamics and duration.
        overrides["rho"] = 0.45
        overrides["offered_load"] = 0.45
        overrides["spawn_period"] = max(float(overrides.get("spawn_period", 20.0)) * 1.55, 8.0)
    if scenario_run.name == "comm_degradation" and method.family in {"classic", "oracle"}:
        if method.key in {"classic_centralized_mincost", "oracle_clairvoyant"}:
            overrides["packet_loss"] = 0.0
            overrides["r_com"] = 12.0
    overrides["seed"] = seed
    overrides["scenario_name"] = scenario_run.name
    overrides["assignment_policy"] = method.policy
    return WarehouseConfig(**overrides)


def run_logging_sanity(scenario: ScenarioSpec, method: Any, args: argparse.Namespace) -> list[dict[str, Any]]:
    config = config_for(scenario.run, method, CANONICAL_SEED, max_duration=args.max_sim_duration)
    plain = run_warehouse_simulation(config)
    recorded = run_warehouse_simulation(config)
    tmp_dir = args.out_trajectories / "_sanity"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    robot_log, load_log = export_trajectory_logs(
        result=recorded,
        scenario=scenario,
        method_id="smith_full",
        seed=CANONICAL_SEED,
        out_dir=tmp_dir,
        log_hz=args.log_hz,
    )
    plain_hash = metric_hash(plain.summary)
    recorded_hash = metric_hash(recorded.summary)
    passed = plain_hash == recorded_hash
    if not passed:
        raise RuntimeError(f"Logging sanity failed: {plain_hash} != {recorded_hash}")
    return [
        {
            "scenario": scenario.key,
            "method": "smith_full",
            "seed": CANONICAL_SEED,
            "plain_hash": plain_hash,
            "recorded_hash": recorded_hash,
            "passed": passed,
            "robot_log": rel(robot_log),
            "load_log": rel(load_log),
            "max_sim_duration": args.max_sim_duration,
        }
    ]


def metric_hash(summary: dict[str, Any]) -> str:
    ignored = {"switch_events"}
    cleaned = {key: normalize_value(value) for key, value in summary.items() if key not in ignored}
    encoded = json.dumps(cleaned, sort_keys=True, allow_nan=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def normalize_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_value(item) for key, item in value.items()}
    return value


def sample_indices(time_values: np.ndarray, log_hz: float) -> np.ndarray:
    if len(time_values) == 0:
        return np.array([], dtype=int)
    stride = max(1, int(round(1.0 / max(float(log_hz), 1e-9) / max(float(np.diff(time_values[:2])[0]) if len(time_values) > 1 else 1.0, 1e-9))))
    indices = np.arange(0, len(time_values), stride, dtype=int)
    if indices[-1] != len(time_values) - 1:
        indices = np.append(indices, len(time_values) - 1)
    return indices


def export_trajectory_logs(
    result: WarehouseResult,
    scenario: ScenarioSpec,
    method_id: str,
    seed: int,
    out_dir: Path,
    log_hz: float,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    indices = sample_indices(result.time, log_hz)
    robot_rows: list[dict[str, Any]] = []
    for idx in indices:
        t = float(result.time[idx])
        for robot_id in range(result.config.robot_count):
            assignment = int(result.assignments[idx, robot_id])
            robot_rows.append(
                {
                    "t": t,
                    "robot_id": robot_id,
                    "x": float(result.robot_positions[idx, robot_id, 0]),
                    "y": float(result.robot_positions[idx, robot_id, 1]),
                    "theta": float(result.headings[idx, robot_id]),
                    "strategy_k": assignment,
                    "committed_load_id": "" if assignment <= 0 else result.loads[assignment - 1].identifier,
                    "v_cmd": float(result.linear_speeds[idx, robot_id]),
                    "omega_cmd": float(result.angular_speeds[idx, robot_id]),
                    "battery": math.nan,
                }
            )

    load_rows: list[dict[str, Any]] = []
    for idx in indices:
        t = float(result.time[idx])
        for load_idx, load in enumerate(result.loads):
            status = int(result.load_status[idx, load_idx])
            z = float(result.contact_counts[idx, load_idx])
            load_rows.append(
                {
                    "t": t,
                    "load_id": load.identifier,
                    "x": float(result.load_positions[idx, load_idx, 0]),
                    "y": float(result.load_positions[idx, load_idx, 1]),
                    "weight_n_k": int(load.weight),
                    "reward_r_k": float(load.reward),
                    "z_occupancy": z,
                    "quorum_met": bool(z >= load.weight),
                    "state": LOAD_STATUS_LABELS.get(status, str(status)),
                    "spawn_t": float(load.spawn_time),
                    "deadline": float(load.cancel_time) if np.isfinite(load.cancel_time) else math.nan,
                    "z_theory": float(result.theory_staffing[idx, load_idx]),
                }
            )

    base = f"{scenario.key}_{method_id}_{seed}"
    robot_path = out_dir / f"trajectory_{base}.parquet"
    load_path = out_dir / f"loads_{base}.parquet"
    pd.DataFrame(robot_rows).to_parquet(robot_path, index=False)
    pd.DataFrame(load_rows).to_parquet(load_path, index=False)
    return robot_path, load_path


def render_individual_video(
    result: WarehouseResult,
    scenario: ScenarioSpec,
    method_id: str,
    out_dir: Path,
    fps: int,
    video_seconds: float,
) -> Path:
    frames = frame_indices(result.time, fps, video_seconds)
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    gs = fig.add_gridspec(2, 2, width_ratios=[2.0, 1.0], height_ratios=[1.0, 1.0])
    ax_world = fig.add_subplot(gs[:, 0])
    ax_capture = fig.add_subplot(gs[0, 1])
    ax_occ = fig.add_subplot(gs[1, 1])
    setup_world_axis(ax_world, result)
    capture_line, = ax_capture.plot([], [], color=METHOD_COLORS[method_id], lw=2)
    ax_capture.set_xlim(0, float(result.time[-1]))
    ax_capture.set_ylim(0, 1.05)
    ax_capture.set_title("capture(t)")
    ax_capture.set_xlabel("t")
    ax_capture.set_ylabel("capture")
    ax_capture.grid(alpha=0.25)
    watched = top_load_indices(result, n=2)
    occ_lines = []
    theory_lines = []
    for load_idx in watched:
        line, = ax_occ.plot([], [], lw=1.8, label=result.loads[load_idx].identifier)
        occ_lines.append(line)
        th, = ax_occ.plot([], [], lw=1.2, ls="--", alpha=0.75)
        theory_lines.append(th)
        ax_occ.axhline(result.loads[load_idx].weight, color=line.get_color(), alpha=0.25, lw=1.0)
    ax_occ.set_xlim(0, float(result.time[-1]))
    ax_occ.set_ylim(0, max(1.0, max(load.weight for load in result.loads) * 1.3))
    ax_occ.set_title("ocupacion vs quorum / z*")
    ax_occ.set_xlabel("t")
    ax_occ.set_ylabel("z_k")
    ax_occ.legend(fontsize=8)
    ax_occ.grid(alpha=0.25)

    artists: dict[str, Any] = {}

    def update(frame: int) -> list[Any]:
        idx = int(frames[frame])
        ax_world.cla()
        setup_world_axis(ax_world, result)
        draw_world(ax_world, result, idx, title=f"{scenario.title} | {METHOD_LABELS[method_id]} | t={result.time[idx]:.1f}s")
        t = result.time[: idx + 1]
        capture_line.set_data(t, capture_series(result)[: idx + 1])
        for line, th, load_idx in zip(occ_lines, theory_lines, watched, strict=True):
            line.set_data(t, result.contact_counts[: idx + 1, load_idx])
            th.set_data(t, result.theory_staffing[: idx + 1, load_idx])
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    out_path = out_dir / f"{scenario.key}_{method_id}.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out_path, writer=animation.FFMpegWriter(fps=fps, codec="libx264", bitrate=2200))
    plt.close(fig)
    return out_path


def render_comparison_video(
    results: dict[str, WarehouseResult],
    scenario: ScenarioSpec,
    out_dir: Path,
    fps: int,
    video_seconds: float,
) -> Path:
    base_result = next(iter(results.values()))
    frames = frame_indices(base_result.time, fps, video_seconds)
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.8), dpi=100)

    def update(frame: int) -> list[Any]:
        idx = int(frames[frame])
        for ax, (method_id, result) in zip(axes, results.items(), strict=True):
            idx_local = min(idx, result.time.size - 1)
            ax.cla()
            setup_world_axis(ax, result)
            draw_world(ax, result, idx_local, title=f"{METHOD_LABELS[method_id]}\nt={result.time[idx_local]:.1f}s")
        fig.suptitle(f"{scenario.title} - comparacion sincronizada", y=0.98)
        return []

    anim = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    out_path = out_dir / f"{scenario.key}_comparison.mp4"
    anim.save(out_path, writer=animation.FFMpegWriter(fps=fps, codec="libx264", bitrate=2600))
    plt.close(fig)
    return out_path


def frame_indices(time_values: np.ndarray, fps: int, video_seconds: float) -> np.ndarray:
    count = max(2, int(fps * video_seconds))
    return np.unique(np.linspace(0, len(time_values) - 1, count).astype(int))


def setup_world_axis(ax: plt.Axes, result: WarehouseResult) -> None:
    half = result.config.half_size
    ax.set_xlim(-half - 0.8, half + 0.8)
    ax.set_ylim(-half - 0.8, half + 0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.grid(alpha=0.18)
    ax.add_patch(plt.Rectangle((-half, -half), result.config.square_size, result.config.square_size, fill=False, lw=1.2, ec="#555555"))
    for obstacle in result.obstacles:
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, color="#555555", alpha=0.35))
    ax.scatter([0], [0], marker="s", s=60, color="#222222", label="station")


def draw_world(ax: plt.Axes, result: WarehouseResult, idx: int, title: str) -> None:
    positions = result.robot_positions[idx]
    headings = result.headings[idx]
    assignments = result.assignments[idx]
    colors = [TASK_COLORS[int(assign) % len(TASK_COLORS)] for assign in assignments]
    dx = 0.35 * np.cos(headings)
    dy = 0.35 * np.sin(headings)
    ax.quiver(
        positions[:, 0],
        positions[:, 1],
        dx,
        dy,
        angles="xy",
        scale_units="xy",
        scale=1,
        color=colors,
        width=0.006,
        alpha=0.9,
    )
    ax.scatter(positions[:, 0], positions[:, 1], c=colors, s=34, edgecolor="black", linewidth=0.35, zorder=3)
    for load_idx, load in enumerate(result.loads):
        status = int(result.load_status[idx, load_idx])
        if status == LOAD_NOT_SPAWNED:
            continue
        pos = result.load_positions[idx, load_idx]
        z = float(result.contact_counts[idx, load_idx])
        fill = min(1.0, z / max(load.weight, 1))
        radius = 0.11 + 0.035 * load.weight
        edge = "#2ca25f" if z >= load.weight else "#444444"
        face = (0.85 - 0.45 * fill, 0.85, 0.95 - 0.65 * fill)
        alpha = 0.25 if status in {LOAD_DELIVERED, LOAD_CANCELED} else 0.86
        ax.add_patch(plt.Circle(pos, radius, facecolor=face, edgecolor=edge, lw=1.8, alpha=alpha))
        ax.text(pos[0], pos[1], str(load.weight), ha="center", va="center", fontsize=7)
    ax.set_title(title, fontsize=10)


def capture_series(result: WarehouseResult) -> np.ndarray:
    delivered_reward = np.zeros_like(result.time, dtype=float)
    total_reward = float(sum(load.reward for load in result.loads))
    for idx in range(result.time.size):
        delivered = result.load_status[idx] == LOAD_DELIVERED
        delivered_reward[idx] = sum(load.reward for load_idx, load in enumerate(result.loads) if delivered[load_idx])
    return delivered_reward / max(total_reward, 1e-9)


def top_load_indices(result: WarehouseResult, n: int) -> list[int]:
    totals = np.nanmax(result.contact_counts, axis=0)
    return list(np.argsort(totals)[::-1][:n])


def render_snapshots(
    result: WarehouseResult,
    scenario: ScenarioSpec,
    method_id: str,
    figures_dir: Path,
) -> list[Path]:
    indices = choose_snapshot_indices(result)
    out_paths: list[Path] = []
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 4.0))
    labels = ["inicio reclutamiento", "coalicion", "entrega/final"]
    for ax, idx, label in zip(axes, indices, labels, strict=True):
        setup_world_axis(ax, result)
        draw_world(ax, result, int(idx), f"{label}\nt={result.time[int(idx)]:.1f}s")
    fig.suptitle(f"{scenario.title} - snapshots | {METHOD_LABELS[method_id]}")
    base = figures_dir / scenario.key / f"snapshots_{method_id}"
    base.parent.mkdir(parents=True, exist_ok=True)
    for suffix, kwargs in {".pdf": {}, ".png": {"dpi": 300}}.items():
        path = base.with_suffix(suffix)
        fig.savefig(path, bbox_inches="tight", **kwargs)
        out_paths.append(path)
    plt.close(fig)
    return out_paths


def choose_snapshot_indices(result: WarehouseResult) -> list[int]:
    active_counts = np.sum(result.load_status != LOAD_NOT_SPAWNED, axis=1)
    quorum_counts = np.sum(result.contact_counts >= np.array([load.weight for load in result.loads])[None, :], axis=1)
    first_active = int(np.argmax(active_counts > 0)) if np.any(active_counts > 0) else 0
    first_quorum = int(np.argmax(quorum_counts > 0)) if np.any(quorum_counts > 0) else len(result.time) // 2
    delivered_counts = np.sum(result.load_status == LOAD_DELIVERED, axis=1)
    first_delivery = int(np.argmax(delivered_counts > 0)) if np.any(delivered_counts > 0) else len(result.time) - 1
    return [first_active, max(first_active, first_quorum), max(first_quorum, first_delivery)]


def render_paths(
    result: WarehouseResult,
    scenario: ScenarioSpec,
    method_id: str,
    figures_dir: Path,
) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.3, 6.0))
    setup_world_axis(ax, result)
    steps = result.time.size
    for robot_id in range(result.config.robot_count):
        path = result.robot_positions[:, robot_id, :]
        ax.plot(path[:, 0], path[:, 1], color=METHOD_COLORS[method_id], alpha=0.18, lw=1.0)
        ax.scatter(path[0, 0], path[0, 1], color="#222222", s=10, alpha=0.5)
        ax.scatter(path[-1, 0], path[-1, 1], color=METHOD_COLORS[method_id], s=12, alpha=0.75)
    ax.set_title(f"{scenario.title} - trazas | {METHOD_LABELS[method_id]}")
    base = figures_dir / scenario.key / f"paths_{method_id}"
    base.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = base.with_suffix(".pdf")
    png_path = base.with_suffix(".png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return [pdf_path, png_path]


def manifest_row(
    artifact: Path,
    scenario: ScenarioSpec,
    method: str,
    seed: int,
    fps: int,
    source: Path | str,
    note: str,
) -> dict[str, Any]:
    return {
        "archivo": rel(artifact),
        "escenario": scenario.key,
        "metodo": method,
        "semilla": seed,
        "fps": fps,
        "fuente": rel(Path(source)) if isinstance(source, Path) else str(source),
        "nota": f"{note}; simulador Python propio, no CoppeliaSim; {scenario.reason}",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(path: Path, scenarios: list[ScenarioSpec], seeds: list[int], args: argparse.Namespace) -> None:
    lines = [
        "# Animaciones de trayectorias",
        "",
        "Artefactos generados desde el simulador Python propio. No son validacion en CoppeliaSim.",
        "",
        f"- Semillas: {', '.join(str(seed) for seed in seeds)}",
        f"- FPS: {args.fps}",
        f"- Duracion objetivo por video: {args.video_seconds:g} s",
        f"- Horizonte maximo de simulacion visual: {args.max_sim_duration:g} s",
        f"- Logging: {args.log_hz:g} Hz, Parquet",
        "",
        "## Escenarios",
        "",
    ]
    for scenario in scenarios:
        lines.append(f"- `{scenario.key}`: {scenario.title}. {scenario.reason}")
    lines.extend(
        [
            "",
            "## Sanity",
            "",
            "Ver `trajectory_sanity.csv`: el hash de metricas con exportacion de trayectoria coincide con el run sin exportacion.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
