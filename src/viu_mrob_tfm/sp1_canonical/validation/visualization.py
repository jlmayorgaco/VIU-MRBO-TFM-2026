"""Reproducible top-down videos for the canonical SP1 E6 approach layer.

The renderer consumes the frozen E6 run and trajectory CSV files. It does not
rerun the optimizer or interpolate new physical states. E6 stops at fixed
contact-approach poses and therefore the videos must not be described as
docking or payload transport.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FFMpegWriter, FuncAnimation, writers
from matplotlib.patches import Patch, Rectangle

from viu_mrob_tfm.sp1_canonical.validation.model import generate_resource_world
from viu_mrob_tfm.sp1_canonical.validation.simulation import (
    contact_targets,
    warehouse_obstacles,
)


CASE_KEYS = ["scenario", "n_robots", "seed", "world_hash"]
SELECTION_RULE = (
    "successful run closest to the group median coalition-arrival time; "
    "otherwise highest arrival rate, then lowest seed"
)


def select_representative_runs(runs: pd.DataFrame) -> pd.DataFrame:
    """Choose one deterministic E6 run per scenario and fleet size."""

    if "trajectory_recorded" in runs.columns:
        runs = runs[runs["trajectory_recorded"].map(_as_bool)].copy()

    required = {
        *CASE_KEYS,
        "n_loads",
        "assignment_feasible",
        "arrival_success",
        "arrival_rate",
        "coalition_arrival_time_s",
    }
    missing = sorted(required.difference(runs.columns))
    if missing:
        raise ValueError(f"E6 runs are missing columns: {missing}")

    rows: list[pd.Series] = []
    for (_, _), group in runs.groupby(["scenario", "n_robots"], sort=True):
        feasible = group[group["assignment_feasible"].map(_as_bool)].copy()
        if feasible.empty:
            raise ValueError(
                "No feasible E6 run available for "
                f"scenario={group.scenario.iloc[0]!r}, n_robots={group.n_robots.iloc[0]}"
            )
        arrival_time = pd.to_numeric(feasible["coalition_arrival_time_s"], errors="coerce")
        successful = feasible[
            feasible["arrival_success"].map(_as_bool) & np.isfinite(arrival_time)
        ].copy()
        if not successful.empty:
            successful["_arrival_time"] = pd.to_numeric(
                successful["coalition_arrival_time_s"], errors="coerce"
            )
            median = float(successful["_arrival_time"].median())
            successful["_selection_distance"] = (successful["_arrival_time"] - median).abs()
            selected = successful.sort_values(
                ["_selection_distance", "seed", "world_hash"], kind="mergesort"
            ).iloc[0]
            reason = "successful_nearest_median_arrival_time"
        else:
            feasible["_arrival_rate"] = pd.to_numeric(
                feasible["arrival_rate"], errors="coerce"
            ).fillna(-math.inf)
            selected = feasible.sort_values(
                ["_arrival_rate", "seed", "world_hash"],
                ascending=[False, True, True],
                kind="mergesort",
            ).iloc[0]
            reason = "fallback_highest_arrival_rate"
        selected = selected.copy()
        selected["selection_reason"] = reason
        rows.append(selected)

    selected_frame = pd.DataFrame(rows).drop(
        columns=["_arrival_time", "_arrival_rate", "_selection_distance"],
        errors="ignore",
    )
    return selected_frame.sort_values(["scenario", "n_robots"], kind="mergesort").reset_index(
        drop=True
    )


def load_selected_trajectories(
    path: str | Path,
    selected: pd.DataFrame,
    *,
    chunksize: int = 250_000,
) -> pd.DataFrame:
    """Load only selected cases from a potentially large trajectory CSV."""

    trajectory_path = Path(path)
    key_frame = selected[CASE_KEYS].drop_duplicates().copy()
    key_frame["n_robots"] = key_frame["n_robots"].astype(int)
    key_frame["seed"] = key_frame["seed"].astype(int)
    retained: list[pd.DataFrame] = []
    for chunk in pd.read_csv(trajectory_path, chunksize=chunksize):
        chunk["n_robots"] = chunk["n_robots"].astype(int)
        chunk["seed"] = chunk["seed"].astype(int)
        match = chunk.merge(key_frame, on=CASE_KEYS, how="inner", validate="many_to_one")
        if not match.empty:
            retained.append(match)
    if not retained:
        raise ValueError(f"No selected E6 trajectories found in {trajectory_path}")
    trajectories = pd.concat(retained, ignore_index=True)
    observed = set(
        map(tuple, trajectories[CASE_KEYS].drop_duplicates().itertuples(index=False, name=None))
    )
    expected = set(map(tuple, key_frame.itertuples(index=False, name=None)))
    missing = sorted(expected.difference(observed))
    if missing:
        raise ValueError(f"Selected E6 cases without trajectory rows: {missing}")
    return trajectories


def render_e6_videos(
    run_dir: str | Path,
    *,
    fps: int = 15,
    dpi: int = 110,
    playback_duration_s: float = 18.0,
) -> dict[str, Any]:
    """Render one audited MP4 for every E6 scenario/fleet-size combination."""

    if fps < 1 or dpi < 40 or playback_duration_s <= 0:
        raise ValueError("fps, dpi and playback_duration_s must be positive")
    if not writers.is_available("ffmpeg"):
        raise RuntimeError("Matplotlib cannot locate FFmpeg; MP4 rendering is unavailable")

    base = Path(run_dir)
    runs_path = base / "raw" / "e6_runs.csv"
    trajectories_path = base / "raw" / "e6_trajectories.csv"
    if not runs_path.exists() or not trajectories_path.exists():
        raise FileNotFoundError(
            f"Expected {runs_path} and {trajectories_path}; run the complete SP1 conference campaign first"
        )

    e6_runs = pd.read_csv(runs_path)
    selected = select_representative_runs(e6_runs)
    trajectories = load_selected_trajectories(trajectories_path, selected)
    obstacles_path = base / "raw" / "e6_obstacles.csv"
    obstacle_frame = pd.read_csv(obstacles_path) if obstacles_path.exists() else pd.DataFrame()
    videos_dir = base / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    catalog_rows: list[dict[str, Any]] = []
    max_frames = max(2, int(round(fps * playback_duration_s)))
    for selected_row in selected.itertuples(index=False):
        selector = (
            (trajectories["scenario"] == selected_row.scenario)
            & (trajectories["n_robots"].astype(int) == int(selected_row.n_robots))
            & (trajectories["seed"].astype(int) == int(selected_row.seed))
            & (trajectories["world_hash"] == selected_row.world_hash)
        )
        case = trajectories.loc[selector].copy()
        stem = (
            f"sp1_e6_{selected_row.scenario}_n{int(selected_row.n_robots)}_"
            f"seed{int(selected_row.seed)}_topdown"
        )
        video_path = videos_dir / f"{stem}.mp4"
        if not obstacle_frame.empty:
            obstacle_case = obstacle_frame[
                (obstacle_frame["scenario"] == selected_row.scenario)
                & (obstacle_frame["n_robots"].astype(int) == int(selected_row.n_robots))
                & (obstacle_frame["seed"].astype(int) == int(selected_row.seed))
                & (obstacle_frame["world_hash"] == selected_row.world_hash)
            ].sort_values("obstacle_id")
            stored_obstacles = tuple(
                (float(row.x0), float(row.x1), float(row.y0), float(row.y1))
                for row in obstacle_case.itertuples(index=False)
            )
        else:
            stored_obstacles = None
        render_info = _render_case(
            case,
            selected_row._asdict(),
            video_path,
            fps=fps,
            dpi=dpi,
            max_frames=max_frames,
            obstacles_override=stored_obstacles,
        )
        relative_video = video_path.relative_to(base).as_posix()
        catalog_rows.append(
            {
                "canonical_sp": "SP1",
                "experiment": "E6",
                "scenario": str(selected_row.scenario),
                "n_robots": int(selected_row.n_robots),
                "n_loads": int(selected_row.n_loads),
                "seed": int(selected_row.seed),
                "world_hash": str(selected_row.world_hash),
                "selection_rule": SELECTION_RULE,
                "selection_reason": str(selected_row.selection_reason),
                "arrival_success": _as_bool(selected_row.arrival_success),
                "arrival_rate": float(selected_row.arrival_rate),
                "coalition_arrival_time_s": float(selected_row.coalition_arrival_time_s),
                "simulation_duration_s": render_info["simulation_duration_s"],
                "retained_obstacles": render_info["retained_obstacles"],
                "output_fps": fps,
                "frame_count": render_info["frame_count"],
                "playback_duration_s": render_info["frame_count"] / fps,
                "time_compression": render_info["time_compression"],
                "video": relative_video,
                "sha256": _sha256(video_path),
                "bytes": video_path.stat().st_size,
                "status": "ok",
                "scientific_scope": "approach_only_no_docking_no_transport",
            }
        )

    catalog = pd.DataFrame(catalog_rows).sort_values(["scenario", "n_robots"])
    catalog_path = videos_dir / "video_catalog.csv"
    catalog.to_csv(catalog_path, index=False)
    index_path = videos_dir / "VIDEO_INDEX.md"
    index_path.write_text(_video_index(catalog), encoding="utf-8")
    manifest: dict[str, Any] = {
        "experiment_id": str(_read_json(base / "manifest.json").get("experiment_id", base.name)),
        "canonical_sp": "SP1",
        "stage": "E6",
        "status": "passed",
        "scientific_scope": "unicycle approach to fixed contact poses; no docking, wrench or payload transport",
        "selection_rule": SELECTION_RULE,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_runs": runs_path.relative_to(base).as_posix(),
        "source_runs_sha256": _sha256(runs_path),
        "source_trajectories": trajectories_path.relative_to(base).as_posix(),
        "source_trajectories_sha256": _sha256(trajectories_path),
        "source_obstacles": obstacles_path.relative_to(base).as_posix() if obstacles_path.exists() else None,
        "source_obstacles_sha256": _sha256(obstacles_path) if obstacles_path.exists() else None,
        "video_count": int(len(catalog)),
        "fps": int(fps),
        "dpi": int(dpi),
        "target_playback_duration_s": float(playback_duration_s),
        "catalog": catalog_path.relative_to(base).as_posix(),
        "index": index_path.relative_to(base).as_posix(),
        "videos": catalog.to_dict(orient="records"),
    }
    (videos_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


def _render_case(
    trajectories: pd.DataFrame,
    run: dict[str, Any],
    output_path: Path,
    *,
    fps: int,
    dpi: int,
    max_frames: int,
    obstacles_override: tuple[tuple[float, float, float, float], ...] | None = None,
) -> dict[str, float | int]:
    required = {
        "time_s",
        "robot_id",
        "load_id",
        "x_m",
        "y_m",
        "theta_rad",
        "target_x_m",
        "target_y_m",
        "arrived",
    }
    missing = sorted(required.difference(trajectories.columns))
    if missing:
        raise ValueError(f"E6 trajectories are missing columns: {missing}")
    if trajectories.empty:
        raise ValueError("Cannot render an empty E6 trajectory")

    n_robots = int(run["n_robots"])
    n_loads = int(run["n_loads"])
    seed = int(run["seed"])
    world = generate_resource_world(n_robots, n_loads, seed)
    if world.world_hash != str(run["world_hash"]):
        raise ValueError(
            f"World hash mismatch for E6 seed {seed}: {world.world_hash} != {run['world_hash']}"
        )

    trajectories = trajectories.sort_values(["robot_id", "time_s"], kind="mergesort")
    assignment = np.full(n_robots, -1, dtype=int)
    tracks: dict[int, pd.DataFrame] = {}
    for robot_value, group in trajectories.groupby("robot_id", sort=True):
        robot = int(robot_value)
        loads = group["load_id"].astype(int).unique()
        if len(loads) != 1:
            raise ValueError(f"Robot {robot} changes load inside a frozen E6 approach")
        assignment[robot] = int(loads[0])
        tracks[robot] = group.sort_values("time_s", kind="mergesort").reset_index(drop=True)
    assigned = np.asarray(sorted(tracks), dtype=int)
    targets = contact_targets(world, assignment)
    observed_targets = (
        trajectories.groupby("robot_id")[["target_x_m", "target_y_m"]].first().sort_index()
    )
    if not np.allclose(observed_targets.to_numpy(), targets[assigned], atol=1e-9):
        raise ValueError("Stored E6 targets do not match the deterministically regenerated world")
    obstacles = (
        (
            tuple(obstacles_override)
            if obstacles_override is not None
            else warehouse_obstacles(world.robot_positions_m[assigned], targets[assigned])
        )
        if str(run["scenario"]) == "warehouse"
        else ()
    )

    times = np.sort(trajectories["time_s"].astype(float).unique())
    frame_indices = np.unique(
        np.linspace(0, len(times) - 1, num=min(max_frames, len(times)), dtype=int)
    )
    frame_times = times[frame_indices]
    cmap = plt.get_cmap("tab20")
    load_colors = {load: cmap(load % 20) for load in range(n_loads)}

    figure, axis = plt.subplots(figsize=(8.0, 7.6))
    figure.patch.set_facecolor("#F7F8FA")
    axis.set_facecolor("#FCFCFD")
    scenario_detail = (
        f"warehouse; obstáculos retenidos={len(obstacles)}"
        if str(run["scenario"]) == "warehouse"
        else "open"
    )
    axis.set(
        xlim=(0, 20),
        ylim=(0, 20),
        xlabel="x (m)",
        ylabel="y (m)",
        title=(
            f"SP1 · E6 · aproximación cenital ({scenario_detail})\n"
            f"N={n_robots}, K={n_loads}, semilla={seed} · sin docking ni transporte"
        ),
    )
    axis.set_aspect("equal")
    axis.grid(color="#D9DEE7", linewidth=0.6, alpha=0.75)
    axis.set_axisbelow(True)

    for x0, x1, y0, y1 in obstacles:
        axis.add_patch(
            Rectangle(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                facecolor="#687386",
                edgecolor="#313A49",
                linewidth=1.0,
                alpha=0.72,
            )
        )

    for load in range(n_loads):
        color = load_colors[load]
        axis.scatter(
            world.load_positions_m[load, 0],
            world.load_positions_m[load, 1],
            marker="s",
            s=190,
            color=color,
            edgecolor="#15191F",
            linewidth=1.0,
            zorder=4,
        )
        axis.text(
            world.load_positions_m[load, 0],
            world.load_positions_m[load, 1],
            f"L{load}",
            ha="center",
            va="center",
            color="white",
            fontsize=7,
            fontweight="bold",
            zorder=5,
        )
    axis.scatter(
        targets[assigned, 0],
        targets[assigned, 1],
        marker="x",
        s=32,
        color=[load_colors[int(assignment[robot])] for robot in assigned],
        linewidth=1.2,
        zorder=3,
    )
    axis.scatter(
        world.robot_positions_m[assigned, 0],
        world.robot_positions_m[assigned, 1],
        marker="o",
        s=20,
        facecolors="none",
        edgecolors="#AAB3C2",
        linewidth=0.7,
        zorder=2,
    )

    artists: dict[int, dict[str, Any]] = {}
    for robot in assigned:
        load = int(assignment[robot])
        color = load_colors[load]
        trail, = axis.plot([], [], color=color, linewidth=0.9, alpha=0.48, zorder=2)
        marker, = axis.plot(
            [],
            [],
            marker="o",
            markersize=6.0,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=1.5,
            linestyle="none",
            zorder=7,
        )
        heading, = axis.plot([], [], color="#111827", linewidth=1.0, zorder=8)
        label = axis.text(0, 0, f"R{robot}", fontsize=5.2, color="#111827", zorder=9)
        artists[int(robot)] = {
            "trail": trail,
            "marker": marker,
            "heading": heading,
            "label": label,
            "color": color,
        }

    legend_handles = [
        Patch(facecolor=load_colors[load], edgecolor="#15191F", label=f"Carga {load}")
        for load in range(n_loads)
    ]
    if obstacles:
        legend_handles.append(Patch(facecolor="#687386", edgecolor="#313A49", label="Obstáculo"))
    axis.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=min(5, len(legend_handles)),
        frameon=False,
        fontsize=7,
    )
    clock = axis.text(
        0.015,
        0.985,
        "",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "alpha": 0.88,
            "edgecolor": "#C7CED8",
        },
        zorder=12,
    )

    def draw(frame_number: int) -> list[Any]:
        current_time = float(frame_times[frame_number])
        arrived_count = 0
        changed: list[Any] = [clock]
        for robot in assigned:
            track = tracks[int(robot)]
            index = int(
                np.searchsorted(
                    track["time_s"].to_numpy(dtype=float), current_time, side="right"
                )
                - 1
            )
            index = max(0, min(index, len(track) - 1))
            state = track.iloc[index]
            x, y, theta = float(state.x_m), float(state.y_m), float(state.theta_rad)
            arrived = _as_bool(state.arrived)
            arrived_count += int(arrived)
            artist = artists[int(robot)]
            artist["trail"].set_data(
                track.loc[:index, "x_m"].to_numpy(dtype=float),
                track.loc[:index, "y_m"].to_numpy(dtype=float),
            )
            artist["marker"].set_data([x], [y])
            artist["marker"].set_markerfacecolor(artist["color"] if arrived else "white")
            artist["heading"].set_data(
                [x, x + 0.34 * math.cos(theta)],
                [y, y + 0.34 * math.sin(theta)],
            )
            artist["label"].set_position((x + 0.12, y + 0.12))
            changed.extend(
                [artist["trail"], artist["marker"], artist["heading"], artist["label"]]
            )
        clock.set_text(
            f"t = {current_time:5.1f} s\n"
            f"llegadas = {arrived_count}/{len(assigned)}\n"
            "trayectoria registrada · vista cenital"
        )
        return changed

    animation = FuncAnimation(
        figure,
        draw,
        frames=len(frame_times),
        interval=1000 / fps,
        blit=False,
        repeat=False,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = FFMpegWriter(
        fps=fps,
        codec="libx264",
        bitrate=2400,
        metadata={
            "title": output_path.stem,
            "comment": "SP1 E6 top-down approach only; no docking or payload transport",
        },
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    animation.save(output_path, writer=writer, dpi=dpi)
    plt.close(figure)
    simulation_duration = float(frame_times[-1] - frame_times[0])
    playback_duration = len(frame_times) / fps
    return {
        "frame_count": int(len(frame_times)),
        "simulation_duration_s": simulation_duration,
        "time_compression": simulation_duration / max(playback_duration, 1e-12),
        "retained_obstacles": int(len(obstacles)),
    }


def _video_index(catalog: pd.DataFrame) -> str:
    lines = [
        "# Catálogo de vídeos cenitales de SP1 E6",
        "",
        "Cada vídeo reproduce estados muestreados de aproximación de uniciclos a poses de contacto fijas. No representa docking, intercambio de fuerzas ni transporte de la carga.",
        "",
        f"Regla de selección: {SELECTION_RULE}.",
        "",
        "En `warehouse`, la columna de obstáculos informa cuántos rectángulos conservó realmente el simulador tras descartar los que solapaban poses iniciales o finales. Un valor cero no debe interpretarse como validación de evitación de obstáculos.",
        "",
        "| Escenario | N | K | Semilla | Obstáculos | Llegada | Duración simulada (s) | Vídeo |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in catalog.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.n_robots} | {row.n_loads} | {row.seed} | {row.retained_obstacles} | "
            f"{row.arrival_rate:.3f} | {row.simulation_duration_s:.2f} | `{row.video}` |"
        )
    lines.extend(
        ["", "Fuente: elaboración propia a partir de `raw/e6_trajectories.csv`.", ""]
    )
    return "\n".join(lines)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "sí", "si"}
    return bool(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "SELECTION_RULE",
    "load_selected_trajectories",
    "render_e6_videos",
    "select_representative_runs",
]
