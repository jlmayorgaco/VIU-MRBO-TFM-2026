"""Build and execute one real CoppeliaSim scene that explains SP4 v4.

The scene contains two copies of the same frozen narrow-passage world:

* left: direct nominal motion followed by the common HOCBF filter;
* right: distributed primal-dual liveness game followed by the same HOCBF.

The Python SP4 controller is executed first.  Its trajectories are embedded in
the saved ``.ttt`` as a Lua playback script and replayed in a real CoppeliaSim
process.  This is a geometry and visual-plausibility validation, not a hardware
or independent closed-loop dynamics validation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
HERE = Path(__file__).resolve().parent
for entry in (SRC, HERE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import build_sp0_corners_scene as scene_utils  # noqa: E402
import run_h12_coppelia_real as coppelia_utils  # noqa: E402
from viu_mrob_tfm.sp4.docking_game import _swept_clearance  # noqa: E402
from viu_mrob_tfm.sp4.docking_game_v4 import (  # noqa: E402
    V4_METHOD_LABELS,
    build_docking_world_v4,
    simulate_docking_v4,
)


SCENARIO = "narrow_passage"
SEED = 886001
N_ROBOTS = 4
DT_S = 0.12
DIRECT = "direct_hocbf"
PROPOSED = "distributed_pd_hocbf"
OUT_DEFAULT = ROOT / "results/sp4/SP4_V4_COPPELIA_PAIRED_NARROW"
SCENE_DEFAULT = ROOT / "coppeliasim/real_scenes/sp4_v4_paired_narrow_passage.ttt"
COPPELIA_DEFAULT = Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe")
PIONEER_DEFAULT = Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\models\robots\mobile\pioneer p3dx.ttm")
METHODS = (DIRECT, PROPOSED)
OFFSETS = {DIRECT: np.asarray([-6.55, 0.0]), PROPOSED: np.asarray([6.55, 0.0])}
COLORS = {DIRECT: (0.84, 0.16, 0.16), PROPOSED: (0.05, 0.58, 0.34)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--scene", type=Path, default=SCENE_DEFAULT)
    parser.add_argument("--coppelia", type=Path, default=COPPELIA_DEFAULT)
    parser.add_argument("--pioneer", type=Path, default=PIONEER_DEFAULT)
    parser.add_argument("--port", type=int, default=23001)
    parser.add_argument("--connect-timeout", type=float, default=50.0)
    parser.add_argument("--frame-every", type=int, default=12)
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--skip-video", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    scene_path = args.scene.resolve()
    prepare_dirs(out_dir, scene_path.parent)

    world = build_docking_world_v4(SCENARIO, SEED, N_ROBOTS)
    results = {
        method: simulate_docking_v4(
            world,
            method,
            dt_s=DT_S,
            horizon_s=120.0,
            game_iterations=64,
            hocbf_iterations=140,
            hocbf_margin_m=0.005,
            hocbf_rate=2.8,
            docking_position_tolerance_m=0.12,
            docking_orientation_tolerance_rad=0.24,
            docking_speed_tolerance_mps=0.16,
        )
        for method in METHODS
    }
    numerical = numerical_summary(results)
    render_trajectory_figure(world, results, out_dir / "plots/sp4_v4_paired_trajectories.png")

    summary: dict[str, Any] = {
        "campaign": "SP4_V4_COPPELIA_PAIRED_NARROW",
        "status": "not_started",
        "scenario": SCENARIO,
        "seed": SEED,
        "n_robots_per_arena": N_ROBOTS,
        "real_coppelia": True,
        "kinematic_playback": True,
        "independent_physics_validation": False,
        "hardware_validation": False,
        "synthetic_fallback": False,
        "coppelia_executable": str(args.coppelia),
        "scene_file": relative(scene_path),
        "numerical": numerical,
    }
    process = None
    try:
        client_cls = coppelia_utils.load_remote_client(args.coppelia)
        process = None if args.no_launch else coppelia_utils.launch_coppelia(
            args.coppelia,
            args.port,
            out_dir / "reports/coppelia_process.log",
        )
        sim = coppelia_utils.connect(client_cls, args.port, args.connect_timeout)
        handles = build_scene(sim, world, results, args.pioneer)
        sim.saveScene(str(scene_path))
        rows, frame_paths, runtime_s = execute_playback(
            sim,
            handles,
            world,
            results,
            out_dir,
            frame_every=max(1, args.frame_every),
        )
        csv_path = out_dir / "data/coppelia_measured_poses.csv"
        write_csv(csv_path, rows)
        measured = measured_summary(world, results, rows)
        montage = render_montage(frame_paths, out_dir / "plots/sp4_v4_coppelia_montage.png")
        camera_video = None
        if frame_paths and not args.skip_video:
            camera_video = coppelia_utils.make_camera_video(
                frame_paths,
                out_dir / "animations/sp4_v4_coppelia_paired.mp4",
            )
        object_count = len(sim.getObjectsInTree(sim.handle_scene))
        gates = {
            "scene_saved": scene_path.exists() and scene_path.stat().st_size > 0,
            "real_frames_captured": len(frame_paths) >= 3,
            "object_count_at_least_30": object_count >= 30,
            "replay_tracking_error_below_1mm": measured["max_replay_error_m"] <= 0.001,
            "direct_counterexample_reproduced": measured[DIRECT]["any_collision"],
            "proposed_safe_success_reproduced": measured[PROPOSED]["safe_success"],
        }
        passed = all(bool(value) for value in gates.values())
        summary.update(
            {
                "status": "coppelia_real_kinematic_replay_pass" if passed else "coppelia_real_kinematic_replay_failed_gate",
                "runtime_s": runtime_s,
                "object_count": object_count,
                "frames": len(frame_paths),
                "measured_csv": relative(csv_path),
                "camera_montage": relative(montage) if montage else "",
                "camera_video": relative(camera_video) if camera_video else "",
                "trajectory_plot": relative(out_dir / "plots/sp4_v4_paired_trajectories.png"),
                "measured": measured,
                "gates": gates,
                "gates_pass": passed,
            }
        )
        write_artifacts(out_dir, summary)
        return 0 if passed else 2
    except Exception as exc:  # noqa: BLE001 - leave an auditable failure artifact.
        summary.update({"status": "coppelia_real_error", "error": repr(exc), "gates_pass": False})
        write_artifacts(out_dir, summary)
        return 1
    finally:
        if process is not None:
            coppelia_utils.stop_process(process)


def prepare_dirs(out_dir: Path, scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("data", "plots", "frames", "animations", "reports"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def numerical_summary(results: dict[str, Any]) -> dict[str, Any]:
    return {
        method: {
            "label": V4_METHOD_LABELS[method],
            "safe_success": bool(result.safe_docking_success),
            "arrival_success": bool(result.arrival_success),
            "any_collision": bool(result.any_collision),
            "docking_time_s": float(result.docking_time_s),
            "minimum_swept_clearance_m": float(result.min_clearance_m),
            "exec_barrier_violations": int(result.exec_barrier_violations),
            "max_exec_barrier_residual": float(result.max_exec_barrier_residual),
            "steps": int(result.steps),
        }
        for method, result in results.items()
    }


def build_scene(sim, world, results: dict[str, Any], pioneer_path: Path) -> dict[str, Any]:
    coppelia_utils.stop_if_running(sim)
    # Preserve Coppelia's default camera/light rig so the validation sensor
    # records the actual method and obstacle colours instead of a dark scene.
    scene_utils.clear_scene(sim)
    sim.setStepping(True)
    try:
        sim.setFloatParam(sim.floatparam_simulation_time_step, DT_S)
    except Exception:
        pass
    scene_utils.configure_scene_rendering(sim)

    handles: dict[str, Any] = {"robots": {}, "sensor": None}
    scene_utils.add_box(
        sim,
        scene_utils.BoxSpec(
            "SP4_floor",
            (0.0, 0.0, -0.035),
            (25.8, 12.4, 0.07),
            (0.58, 0.60, 0.62),
            static=True,
            respondable=True,
        ),
    )
    scene_utils.add_box(
        sim,
        scene_utils.BoxSpec(
            "SP4_divider",
            (0.0, 0.0, 0.12),
            (0.10, 12.1, 0.24),
            (0.10, 0.10, 0.12),
            static=True,
            respondable=False,
        ),
    )

    for method in METHODS:
        offset = OFFSETS[method]
        color = COLORS[method]
        prefix = "DIRECT" if method == DIRECT else "PD"
        scene_utils.add_box(
            sim,
            scene_utils.BoxSpec(
                f"{prefix}_header",
                (float(offset[0]), 5.72, 0.035),
                (11.8, 0.28, 0.07),
                color,
                static=True,
                respondable=False,
            ),
        )
        scene_utils.add_cylinder(
            sim,
            f"{prefix}_payload",
            world.load_radius_m,
            0.42,
            (float(offset[0]), 0.0, 0.21),
            (0.38, 0.40, 0.43),
            static=True,
            respondable=True,
        )
        for idx, obstacle in enumerate(world.obstacles, start=1):
            scene_utils.add_cylinder(
                sim,
                f"{prefix}_obstacle_{idx:02d}",
                float(obstacle[2]),
                0.78,
                (float(obstacle[0] + offset[0]), float(obstacle[1]), 0.39),
                (0.93, 0.48, 0.12),
                static=True,
                respondable=True,
            )
        for idx, goal in enumerate(world.target_pose, start=1):
            scene_utils.add_cylinder(
                sim,
                f"{prefix}_port_{idx:02d}",
                world.robot_radius_m + 0.04,
                0.022,
                (float(goal[0] + offset[0]), float(goal[1]), 0.018),
                (0.12, 0.78, 0.32),
                static=True,
                respondable=False,
                alpha=0.72,
            )
        path = results[method].positions
        stride = max(1, len(path) // 28)
        for robot in range(world.n_robots):
            for sample_index in range(0, len(path), stride):
                point = path[sample_index, robot] + offset
                scene_utils.add_cylinder(
                    sim,
                    f"{prefix}_path_r{robot + 1:02d}_{sample_index:04d}",
                    0.035,
                    0.012,
                    (float(point[0]), float(point[1]), 0.026),
                    color,
                    static=True,
                    respondable=False,
                    alpha=0.62,
                )
        handles["robots"][method] = []
        for robot in range(world.n_robots):
            alias = f"SP4_{prefix}_Pioneer_{robot + 1:02d}"
            point = results[method].positions[0, robot] + offset
            handle = add_pioneer(sim, pioneer_path, alias, point, color, world.robot_radius_m)
            handles["robots"][method].append(handle)

    collision_result = results[DIRECT]
    collision_point = collision_result.positions[-1, 0] + OFFSETS[DIRECT]
    scene_utils.add_cylinder(
        sim,
        "DIRECT_collision_marker",
        0.32,
        0.018,
        (float(collision_point[0]), float(collision_point[1]), 0.045),
        (0.95, 0.02, 0.02),
        static=True,
        respondable=False,
        alpha=0.58,
    )
    handles["sensor"] = create_top_sensor(sim)
    add_playback_script(sim, results)
    sim.setNamedStringParam(
        "sp4_v4_paired_scene_metadata",
        json.dumps(
            {
                "scenario": SCENARIO,
                "seed": SEED,
                "methods": list(METHODS),
                "scope": "real CoppeliaSim kinematic playback; not hardware or independent dynamics validation",
            }
        ),
    )
    return handles


def add_pioneer(sim, model_path: Path, alias: str, point: np.ndarray, color, radius: float) -> int:
    handle = scene_utils.load_model(sim, str(model_path))
    if handle is None:
        handle = scene_utils.add_cylinder(
            sim,
            alias,
            radius,
            0.28,
            (float(point[0]), float(point[1]), 0.14),
            color,
            static=True,
            respondable=False,
        )
    else:
        scene_utils.disable_model_scripts(sim, handle)
        scene_utils.make_model_visual_only(sim, handle)
        scene_utils.set_alias(sim, handle, alias)
        sim.setObjectPosition(handle, -1, [float(point[0]), float(point[1]), 0.14])
        sim.setObjectOrientation(handle, -1, [0.0, 0.0, 0.0])
    marker = scene_utils.add_box(
        sim,
        scene_utils.BoxSpec(
            alias + "_method_marker",
            (float(point[0]), float(point[1]), 0.42),
            (0.30, 0.16, 0.035),
            color,
            static=True,
            respondable=False,
        ),
    )
    footprint = scene_utils.add_cylinder(
        sim,
        alias + "_footprint",
        radius,
        0.012,
        (float(point[0]), float(point[1]), 0.028),
        color,
        static=True,
        respondable=False,
        alpha=0.45,
    )
    for child in (marker, footprint):
        try:
            sim.setObjectParent(child, handle, True)
        except Exception:
            pass
    return handle


def create_top_sensor(sim) -> int:
    sensor = sim.createVisionSensor(
        1 + 4,
        [1280, 720, 0, 0],
        [0.2, 50.0, 27.5, 0.5, 0.0, 0.0, 0.92, 0.93, 0.94, 0.0, 0.0],
    )
    scene_utils.set_alias(sim, sensor, "SP4_camera_top")
    sim.setExplicitHandling(sensor, 1)
    try:
        sim.setObjectInt32Param(sensor, sim.visionintparam_perspective_operation, 0)
        sim.setObjectFloatParam(sensor, sim.visionfloatparam_ortho_size, 27.5)
    except Exception:
        pass
    sim.setObjectPosition(sensor, -1, [0.0, 0.0, 20.0])
    sim.setObjectOrientation(sensor, -1, [0.0, math.pi, 0.0])
    return sensor


def add_playback_script(sim, results: dict[str, Any]) -> None:
    code = render_lua_playback(results)
    dummy = sim.createDummy(0.035)
    scene_utils.set_alias(sim, dummy, "SP4_v4_playback_controller")
    try:
        if sim.getBoolParam(sim.boolparam_usingscriptobjects):
            script = sim.createScript(sim.scripttype_simulation, code, 0, "lua")
            sim.setObjectParent(script, dummy)
        else:
            script = sim.addScript(sim.scripttype_simulation)
            sim.associateScriptWithObject(script, dummy)
            sim.setScriptText(script, code)
    except Exception:
        script = sim.addScript(sim.scripttype_simulation)
        sim.associateScriptWithObject(script, dummy)
        sim.setScriptText(script, code)


def render_lua_playback(results: dict[str, Any]) -> str:
    method_tables = []
    for method in METHODS:
        prefix = "DIRECT" if method == DIRECT else "PD"
        aliases = ",".join(f"'{f'SP4_{prefix}_Pioneer_{i + 1:02d}'}'" for i in range(N_ROBOTS))
        trajectories = lua_positions(results[method].positions, OFFSETS[method])
        method_tables.append(
            "{aliases={" + aliases + "},trajectory=" + trajectories + "}"
        )
    return f"""-- Embedded SP4 v4 paired-world playback.
local sim = require('sim')
local dt = {DT_S:.12g}
local groups = {{{','.join(method_tables)}}}

function sysCall_init()
    for _,group in ipairs(groups) do
        group.handles = {{}}
        for i,name in ipairs(group.aliases) do
            group.handles[i] = sim.getObject('/' .. name)
        end
    end
end

function sysCall_actuation()
    local index = math.floor(sim.getSimulationTime() / dt + 1.0e-7) + 1
    for _,group in ipairs(groups) do
        local k = math.min(index, #group.trajectory)
        local knext = math.min(k + 1, #group.trajectory)
        for robot,handle in ipairs(group.handles) do
            local p = group.trajectory[k][robot]
            local q = group.trajectory[knext][robot]
            local yaw = math.atan2(q[2] - p[2], q[1] - p[1])
            sim.setObjectPosition(handle, -1, {{p[1], p[2], 0.14}})
            sim.setObjectOrientation(handle, -1, {{0.0, 0.0, yaw}})
        end
    end
end
"""


def lua_positions(positions: np.ndarray, offset: np.ndarray) -> str:
    frames = []
    for frame in positions:
        robots = []
        for point in frame:
            shifted = point + offset
            robots.append(f"{{{shifted[0]:.8f},{shifted[1]:.8f}}}")
        frames.append("{" + ",".join(robots) + "}")
    return "{" + ",".join(frames) + "}"


def execute_playback(sim, handles, world, results, out_dir: Path, frame_every: int):
    total_steps = max(len(result.positions) for result in results.values())
    rows: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    started = time.perf_counter()
    sim.startSimulation()
    try:
        for step in range(total_steps):
            sim.step()
            t = step * DT_S
            for method in METHODS:
                # Coppelia executes ``sysCall_actuation`` before returning from
                # the first synchronous step, so the measured pose already
                # corresponds to trajectory sample 1 rather than sample 0.
                command_index = min(step + 1, len(results[method].positions) - 1)
                for robot, handle in enumerate(handles["robots"][method]):
                    position = sim.getObjectPosition(handle, -1)
                    commanded = results[method].positions[command_index, robot] + OFFSETS[method]
                    rows.append(
                        {
                            "t_s": round(t, 4),
                            "method": method,
                            "robot": robot,
                            "x_m": float(position[0] - OFFSETS[method][0]),
                            "y_m": float(position[1]),
                            "command_x_m": float(commanded[0] - OFFSETS[method][0]),
                            "command_y_m": float(commanded[1]),
                            "replay_error_m": float(np.linalg.norm(np.asarray(position[:2]) - commanded)),
                        }
                    )
            if step % frame_every == 0 or step == total_steps - 1:
                frame = coppelia_utils.capture_sensor_frame(
                    sim,
                    handles["sensor"],
                    out_dir / f"frames/sp4_coppelia_{step:04d}.png",
                )
                if frame is not None:
                    frame_paths.append(frame)
    finally:
        try:
            sim.stopSimulation()
            for _ in range(100):
                if sim.getSimulationState() == sim.simulation_stopped:
                    break
                time.sleep(0.03)
        except Exception:
            pass
    return rows, frame_paths, time.perf_counter() - started


def measured_summary(world, results, rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "max_replay_error_m": max(float(row["replay_error_m"]) for row in rows),
    }
    for method in METHODS:
        subset = [row for row in rows if row["method"] == method]
        times = sorted({float(row["t_s"]) for row in subset})
        measured = np.zeros((len(times), world.n_robots, 2), dtype=float)
        for ti, t in enumerate(times):
            for row in (item for item in subset if float(item["t_s"]) == t):
                measured[ti, int(row["robot"])] = [float(row["x_m"]), float(row["y_m"])]
        minimum = float("inf")
        collision = False
        for step in range(1, len(measured)):
            before = np.zeros((world.n_robots, 5), dtype=float)
            after = np.zeros_like(before)
            before[:, :2] = measured[step - 1]
            after[:, :2] = measured[step]
            clearance, collided = _swept_clearance(world, before, after)
            minimum = min(minimum, float(clearance))
            collision = collision or bool(collided)
        final_error = float(np.mean(np.linalg.norm(measured[-1] - world.target_pose[:, :2], axis=1)))
        expected = results[method]
        summary[method] = {
            "label": V4_METHOD_LABELS[method],
            "minimum_swept_clearance_m": minimum,
            "any_collision": collision,
            "final_mean_position_error_m": final_error,
            "safe_success": bool((not collision) and expected.arrival_success and final_error <= 0.12),
        }
    return summary


def render_trajectory_figure(world, results, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.2), constrained_layout=True)
    for ax, method in zip(axes, METHODS, strict=True):
        ax.add_patch(plt.Circle((0.0, 0.0), world.load_radius_m, color="#9ca3af", ec="#374151"))
        for obstacle in world.obstacles:
            ax.add_patch(plt.Circle(obstacle[:2], obstacle[2], color="#f59e0b", ec="#92400e", alpha=0.75))
        ax.scatter(world.target_pose[:, 0], world.target_pose[:, 1], marker="x", color="#111827", label="puertos")
        for robot in range(world.n_robots):
            trajectory = results[method].positions[:, robot]
            ax.plot(trajectory[:, 0], trajectory[:, 1], linewidth=1.5, label=f"R{robot + 1}")
            ax.scatter(trajectory[0, 0], trajectory[0, 1], s=18)
        ax.set_title(V4_METHOD_LABELS[method])
        ax.set_xlim(-6.0, 6.0)
        ax.set_ylim(-6.0, 6.0)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.18)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
    fig.suptitle("SP4 v4: mundo pareado narrow_passage, semilla 886001")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def render_montage(frame_paths: list[Path], path: Path) -> Path | None:
    if len(frame_paths) < 3:
        return None
    selected = [frame_paths[0], frame_paths[len(frame_paths) // 2], frame_paths[-1]]
    images = [crop_dark_border(Image.open(item).convert("RGB")) for item in selected]
    panel_width = 640
    images = [image.resize((panel_width, round(image.height * panel_width / image.width))) for image in images]
    panel_height = min(image.height for image in images)
    images = [image.crop((0, 0, panel_width, panel_height)) for image in images]
    label_height = 42
    legend_height = 34
    gap = 12
    canvas = Image.new(
        "RGB",
        (3 * panel_width + 2 * gap, label_height + panel_height + legend_height),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    labels = ("Inicio pareado", "Evolución", "Resultado final")
    for column, (label, image) in enumerate(zip(labels, images, strict=True)):
        x = column * (panel_width + gap)
        draw.text((x + 12, 13), label, fill=(20, 24, 30))
        canvas.paste(image, (x, label_height))
    legend_y = label_height + panel_height + 10
    draw.rectangle((12, legend_y, 34, legend_y + 12), fill=(238, 44, 56))
    draw.text((42, legend_y - 2), "Directo + HOCBF", fill=(20, 24, 30))
    draw.rectangle((205, legend_y, 227, legend_y + 12), fill=(36, 194, 112))
    draw.text((235, legend_y - 2), "Juego primal-dual + HOCBF", fill=(20, 24, 30))
    canvas.save(path)
    return path


def crop_dark_border(image: Image.Image) -> Image.Image:
    data = np.asarray(image)
    mask = np.max(data, axis=2) > 28
    rows = np.flatnonzero(np.any(mask, axis=1))
    cols = np.flatnonzero(np.any(mask, axis=0))
    if rows.size == 0 or cols.size == 0:
        return image
    margin = 4
    left = max(0, int(cols[0]) - margin)
    upper = max(0, int(rows[0]) - margin)
    right = min(image.width, int(cols[-1]) + margin + 1)
    lower = min(image.height, int(rows[-1]) + margin + 1)
    return image.crop((left, upper, right, lower))

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_artifacts(out_dir: Path, summary: dict[str, Any]) -> None:
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    manifest = {
        "campaign": summary["campaign"],
        "status": summary["status"],
        "scene": summary["scene_file"],
        "real_coppelia": summary["real_coppelia"],
        "kinematic_playback": summary["kinematic_playback"],
        "synthetic_fallback": summary["synthetic_fallback"],
        "gates_pass": summary.get("gates_pass", False),
        "montage": summary.get("camera_montage", ""),
        "video": summary.get("camera_video", ""),
    }
    write_csv(out_dir / "manifest.csv", [manifest])
    lines = [
        "# SP4 v4 paired CoppeliaSim scene",
        "",
        f"Status: `{summary['status']}`",
        "",
        "The scene replays two controllers in the same frozen narrow-passage world. "
        "It validates CoppeliaSim geometry, scene reproducibility and visual plausibility. "
        "It does not constitute hardware or independent dynamics validation.",
        "",
        f"- Scene: `{summary['scene_file']}`",
        f"- Real CoppeliaSim: `{summary['real_coppelia']}`",
        f"- Synthetic fallback: `{summary['synthetic_fallback']}`",
    ]
    if "measured" in summary:
        lines.extend(
            [
                f"- Maximum replay tracking error: `{summary['measured']['max_replay_error_m']:.3e} m`",
                f"- Direct minimum swept clearance: `{summary['measured'][DIRECT]['minimum_swept_clearance_m']:.4f} m`",
                f"- Proposed minimum swept clearance: `{summary['measured'][PROPOSED]['minimum_swept_clearance_m']:.4f} m`",
                f"- Captured frames: `{summary['frames']}`",
                "",
                "Interpretation: the common HOCBF is not sufficient to resolve liveness in this paired world; "
                "the distributed game and admission closure complete the docking sequence.",
            ]
        )
    if "error" in summary:
        lines.extend(["", f"Error: `{summary['error']}`"])
    lines.extend(
        [
            "",
            "Regenerate:",
            "",
            "```powershell",
            "python scripts\\coppelia\\run_sp4_v4_coppelia_paired_scene.py",
            "```",
        ]
    )
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def relative(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
