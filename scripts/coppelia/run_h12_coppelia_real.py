"""Run a real CoppeliaSim H12 validation campaign.

This runner is intentionally separate from ``run_h12_coppelia_campaign.py``:
that older campaign creates editable scene recipes and synthetic fallback
renders. This file launches CoppeliaSim through the ZMQ Remote API, builds a
physical scene, advances the simulator step by step, exports measured states,
and marks the campaign as validated only when the real simulator completed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "results/campaigns/H12_coppelia_real"
SCENE_DIR_DEFAULT = ROOT / "coppeliasim/real_scenes"
COPPELIA_DEFAULT = Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe")
ADDON_REL = Path("programming/zmqRemoteApi/addOns/ZMQ remote API server.lua")
CLIENT_REL = Path("programming/zmqRemoteApi/clients/python/src")


@dataclass(frozen=True)
class CampaignConfig:
    duration_s: float = 18.0
    dt_s: float = 0.05
    warehouse_width_m: float = 24.0
    warehouse_depth_m: float = 14.0
    load_start: tuple[float, float] = (-7.6, 0.0)
    load_goal: tuple[float, float] = (6.4, 0.0)
    load_size: tuple[float, float, float] = (2.4, 1.15, 0.55)
    robot_size: tuple[float, float, float] = (0.72, 0.52, 0.34)
    load_mass_kg: float = 18.0
    robot_mass_kg: float = 8.0
    push_force_n: float = 34.0
    lateral_gain: float = 30.0
    longitudinal_gain: float = 22.0
    damping_gain: float = 12.0
    max_robot_force_n: float = 70.0
    max_load_force_n: float = 42.0
    corridor_half_width_m: float = 2.15
    safety_margin_m: float = 0.18
    frame_every_steps: int = 8


def main() -> int:
    args = parse_args()
    cfg = CampaignConfig(duration_s=args.duration, dt_s=args.dt)
    out_dir = args.out.resolve()
    scene_dir = args.scene_dir.resolve()
    prepare_dirs(out_dir, scene_dir)

    summary: dict[str, Any] = {
        "campaign": "H12_coppelia_real",
        "status": "not_started",
        "coppelia_executable": str(args.coppelia),
        "scene": "h12_real_rectangular_transport_physics",
        "real_coppelia": True,
        "synthetic_fallback": False,
    }

    process: subprocess.Popen[Any] | None = None
    log_path = out_dir / "reports/coppelia_process.log"
    try:
        client_cls = load_remote_client(args.coppelia)
        process = None if args.no_launch else launch_coppelia(args.coppelia, args.port, log_path)
        sim = connect(client_cls, args.port, timeout_s=args.connect_timeout)
        handles = build_scene(sim, cfg)
        scene_path = scene_dir / "h12_real_rectangular_transport_physics.ttt"
        save_scene(sim, scene_path)
        rows, frame_paths, runtime_s = run_closed_loop(sim, handles, cfg, out_dir)
        metrics = compute_metrics(rows, handles["rack_names"], cfg)

        data_csv = out_dir / "data/h12_real_rectangular_transport_physics.csv"
        write_csv(data_csv, rows)
        metrics_csv = out_dir / "data/h12_real_metrics.csv"
        write_csv(metrics_csv, [metrics])
        plot_path = out_dir / "plots/h12_real_transport_trace.png"
        video_path = out_dir / "animations/h12_real_transport_trace.mp4"
        render_trace(rows, cfg, plot_path, video_path)
        camera_video = make_camera_video(frame_paths, out_dir / "animations/h12_real_coppelia_camera.mp4")

        status = "coppelia_real_pass" if metrics["passed"] else "coppelia_real_failed_gate"
        summary.update(
            {
                "status": status,
                "runtime_s": runtime_s,
                "scene_file": rel(scene_path),
                "csv": rel(data_csv),
                "metrics_csv": rel(metrics_csv),
                "plot": rel(plot_path),
                "trace_video": rel(video_path),
                "camera_video": rel(camera_video) if camera_video else "",
                "frames": len(frame_paths),
                "metrics": metrics,
            }
        )
        write_manifest(out_dir, summary)
        write_readme(out_dir, summary)
        return 0 if metrics["passed"] else 2
    except Exception as exc:  # noqa: BLE001 - campaign must leave an auditable status.
        summary.update({"status": "coppelia_real_error", "error": repr(exc)})
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        write_manifest(out_dir, summary)
        write_readme(out_dir, summary)
        return 1
    finally:
        if process is not None:
            stop_process(process)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--scene-dir", type=Path, default=SCENE_DIR_DEFAULT)
    parser.add_argument("--coppelia", type=Path, default=COPPELIA_DEFAULT)
    parser.add_argument("--port", type=int, default=23000)
    parser.add_argument("--duration", type=float, default=18.0)
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--connect-timeout", type=float, default=45.0)
    parser.add_argument("--no-launch", action="store_true", help="Connect to an already running CoppeliaSim ZMQ server.")
    return parser.parse_args()


def prepare_dirs(out_dir: Path, scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("data", "plots", "frames", "animations", "reports"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def load_remote_client(coppelia: Path):
    client_dir = coppelia.parent / CLIENT_REL
    if not client_dir.exists():
        raise FileNotFoundError(f"Coppelia ZMQ client not found: {client_dir}")
    sys.path.insert(0, str(client_dir))
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    return RemoteAPIClient


def launch_coppelia(coppelia: Path, port: int, log_path: Path) -> subprocess.Popen[Any]:
    if not coppelia.exists():
        raise FileNotFoundError(f"CoppeliaSim executable not found: {coppelia}")
    addon = coppelia.parent / ADDON_REL
    if not addon.exists():
        raise FileNotFoundError(f"ZMQ add-on not found: {addon}")
    log_handle = log_path.open("w", encoding="utf-8", errors="replace")
    args = [
        str(coppelia),
        "-h",
        f"-a{addon}",
        f"-GzmqRemoteApi.rpcPort={port}",
    ]
    return subprocess.Popen(
        args,
        cwd=str(coppelia.parent),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def connect(client_cls, port: int, timeout_s: float):
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            client = client_cls(port=port)
            sim = client.require("sim")
            sim.getSimulationState()
            return sim
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.75)
    raise TimeoutError(f"Could not connect to CoppeliaSim ZMQ on port {port}: {last_error!r}")


def build_scene(sim, cfg: CampaignConfig) -> dict[str, Any]:
    stop_if_running(sim)
    clear_scene(sim)
    sim.setStepping(True)

    handles: dict[str, Any] = {"robots": [], "robot_names": [], "racks": [], "rack_names": []}
    handles["floor"] = create_box(
        sim,
        "Warehouse_floor_static",
        [cfg.warehouse_width_m, cfg.warehouse_depth_m, 0.10],
        [0.0, 0.0, -0.05],
        mass_kg=0.0,
        color=[0.48, 0.50, 0.52],
        static=True,
    )
    handles["inbound"] = create_box(
        sim,
        "Inbound_station",
        [2.8, 1.4, 0.05],
        [cfg.load_start[0] - 0.8, -2.9, 0.025],
        mass_kg=0.0,
        color=[0.10, 0.35, 0.70],
        static=True,
    )
    handles["outbound"] = create_box(
        sim,
        "Outbound_station",
        [2.8, 1.4, 0.05],
        [cfg.load_goal[0] + 0.4, 2.9, 0.025],
        mass_kg=0.0,
        color=[0.10, 0.48, 0.24],
        static=True,
    )

    for i, (x, y, sx, sy) in enumerate(rack_layout(cfg), start=1):
        rack = create_box(
            sim,
            f"Rack_static_{i:02d}",
            [sx, sy, 1.35],
            [x, y, 0.675],
            mass_kg=0.0,
            color=[0.36, 0.38, 0.40],
            static=True,
        )
        handles["racks"].append(rack)
        handles["rack_names"].append(f"Rack_static_{i:02d}")

    load_z = 0.10 + cfg.load_size[2] / 2
    handles["load"] = create_box(
        sim,
        "Load_rectangular_dynamic",
        list(cfg.load_size),
        [cfg.load_start[0], cfg.load_start[1], load_z],
        mass_kg=cfg.load_mass_kg,
        color=[0.86, 0.56, 0.18],
        static=False,
    )
    set_planar_initial_pose(sim, handles["load"])

    robot_offsets = [
        (-cfg.load_size[0] / 2 - 0.50, -0.38),
        (-cfg.load_size[0] / 2 - 0.50, 0.38),
        (-cfg.load_size[0] / 2 - 1.12, -0.04),
        (-0.10, -cfg.load_size[1] / 2 - 0.44),
        (-0.10, cfg.load_size[1] / 2 + 0.44),
        (-cfg.load_size[0] / 2 - 1.56, 0.72),
    ]
    robot_z = 0.10 + cfg.robot_size[2] / 2
    for i, offset in enumerate(robot_offsets, start=1):
        x = cfg.load_start[0] + offset[0]
        y = cfg.load_start[1] + offset[1]
        robot = create_box(
            sim,
            f"AMR_dynamic_{i:02d}",
            list(cfg.robot_size),
            [x, y, robot_z],
            mass_kg=cfg.robot_mass_kg,
            color=[0.08, 0.18, 0.32],
            static=False,
        )
        create_box(
            sim,
            f"AMR_top_marker_{i:02d}",
            [0.35, 0.08, 0.04],
            [x + 0.16, y, robot_z + cfg.robot_size[2] / 2 + 0.03],
            mass_kg=0.0,
            color=[0.12, 0.55, 0.95],
            static=True,
            respondable=False,
        )
        handles["robots"].append(robot)
        handles["robot_names"].append(f"AMR_dynamic_{i:02d}")

    handles["human"] = create_cylinder(
        sim,
        "Human_crossing_static_exclusion",
        radius=0.18,
        height=1.70,
        position=[0.5, cfg.corridor_half_width_m + 0.85, 0.85],
        mass_kg=0.0,
        color=[0.78, 0.12, 0.12],
        static=True,
    )
    handles["top_sensor"] = create_top_vision_sensor(sim, cfg)
    handles["oblique_camera"] = create_oblique_camera(sim)

    sim.setNamedStringParam(
        "mrbo_h12_real_scene",
        json.dumps(
            {
                "scenario": "h12_real_rectangular_transport_physics",
                "robots": handles["robot_names"],
                "load": "Load_rectangular_dynamic",
                "racks": handles["rack_names"],
                "physics": "CoppeliaSim dynamic shapes; forces applied through Remote API stepping",
            }
        ),
    )
    return handles


def stop_if_running(sim) -> None:
    try:
        state = sim.getSimulationState()
        if state != sim.simulation_stopped:
            sim.stopSimulation()
            for _ in range(200):
                if sim.getSimulationState() == sim.simulation_stopped:
                    break
                time.sleep(0.05)
    except Exception:
        pass


def clear_scene(sim) -> None:
    try:
        objects = sim.getObjectsInTree(sim.handle_scene)
        if objects:
            sim.removeObjects(objects)
    except Exception:
        sim.closeScene()


def create_box(
    sim,
    name: str,
    size: list[float],
    position: list[float],
    mass_kg: float,
    color: list[float],
    static: bool,
    respondable: bool = True,
) -> int:
    handle = sim.createPureShape(0, 8, size, max(mass_kg, 0.001), [])
    sim.setObjectAlias(handle, name, 1)
    sim.setObjectPosition(handle, -1, position)
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, color)
    sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1 if static else 0)
    sim.setObjectInt32Param(handle, sim.shapeintparam_respondable, 1 if respondable else 0)
    sim.setObjectFloatParam(handle, sim.shapefloatparam_mass, mass_kg)
    return handle


def create_cylinder(
    sim,
    name: str,
    radius: float,
    height: float,
    position: list[float],
    mass_kg: float,
    color: list[float],
    static: bool,
) -> int:
    handle = sim.createPureShape(2, 8, [radius * 2.0, radius * 2.0, height], max(mass_kg, 0.001), [])
    sim.setObjectAlias(handle, name, 1)
    sim.setObjectPosition(handle, -1, position)
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, color)
    sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1 if static else 0)
    sim.setObjectInt32Param(handle, sim.shapeintparam_respondable, 1)
    sim.setObjectFloatParam(handle, sim.shapefloatparam_mass, mass_kg)
    return handle


def set_planar_initial_pose(sim, handle: int) -> None:
    sim.setObjectOrientation(handle, -1, [0.0, 0.0, 0.0])
    sim.resetDynamicObject(handle)


def rack_layout(cfg: CampaignConfig) -> list[tuple[float, float, float, float]]:
    xs = [-5.0, -1.4, 2.2, 5.8]
    racks: list[tuple[float, float, float, float]] = []
    for x in xs:
        racks.append((x, cfg.corridor_half_width_m + 1.45, 2.0, 0.75))
        racks.append((x, -cfg.corridor_half_width_m - 1.45, 2.0, 0.75))
    racks.append((-0.2, cfg.corridor_half_width_m + 0.42, 0.9, 0.55))
    racks.append((2.7, -cfg.corridor_half_width_m - 0.42, 0.9, 0.55))
    return racks


def create_top_vision_sensor(sim, cfg: CampaignConfig) -> int:
    sensor = sim.createVisionSensor(
        1 + 4,
        [960, 540, 0, 0],
        [0.2, 40.0, max(cfg.warehouse_width_m, cfg.warehouse_depth_m) + 2.0, 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0],
    )
    sim.setObjectAlias(sensor, "Camera_top_validation_sensor", 1)
    sim.setObjectPosition(sensor, -1, [0.0, 0.0, 18.0])
    sim.setObjectOrientation(sensor, -1, [0.0, math.radians(180.0), 0.0])
    return sensor


def create_oblique_camera(sim) -> int:
    camera = sim.createObject(sim.object_camera_type, 0)
    sim.setObjectAlias(camera, "Camera_oblique_validation", 1)
    sim.setObjectPosition(camera, -1, [8.0, -9.5, 7.0])
    sim.setObjectOrientation(camera, -1, [math.radians(60.0), 0.0, math.radians(42.0)])
    return camera


def save_scene(sim, scene_path: Path) -> None:
    scene_path.parent.mkdir(parents=True, exist_ok=True)
    sim.saveScene(str(scene_path))


def run_closed_loop(
    sim,
    handles: dict[str, Any],
    cfg: CampaignConfig,
    out_dir: Path,
) -> tuple[list[dict[str, Any]], list[Path], float]:
    steps = int(round(cfg.duration_s / cfg.dt_s))
    rows: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    target_offsets = [
        (-cfg.load_size[0] / 2 - 0.50, -0.38),
        (-cfg.load_size[0] / 2 - 0.50, 0.38),
        (-cfg.load_size[0] / 2 - 1.10, -0.04),
        (-0.10, -cfg.load_size[1] / 2 - 0.43),
        (-0.10, cfg.load_size[1] / 2 + 0.43),
        (-cfg.load_size[0] / 2 - 1.52, 0.72),
    ]

    start = time.perf_counter()
    sim.startSimulation()
    try:
        for step in range(steps + 1):
            t = step * cfg.dt_s
            load_pos = np.array(sim.getObjectPosition(handles["load"], -1), dtype=float)
            load_vel = np.array(sim.getObjectVelocity(handles["load"])[0], dtype=float)
            progress = min(1.0, t / max(cfg.duration_s - 1.0, 1.0))
            load_target = np.array(
                [
                    cfg.load_start[0] + progress * (cfg.load_goal[0] - cfg.load_start[0]),
                    0.0,
                    load_pos[2],
                ],
                dtype=float,
            )
            load_error = load_target - load_pos
            load_force = np.array([cfg.max_load_force_n * 0.45, -18.0 * load_pos[1], 0.0]) + 4.5 * load_error - 4.0 * load_vel
            load_force[0] = float(np.clip(load_force[0], 0.0, cfg.max_load_force_n))
            load_force[1] = float(np.clip(load_force[1], -cfg.max_load_force_n * 0.35, cfg.max_load_force_n * 0.35))
            sim.addForceAndTorque(handles["load"], load_force.tolist(), [0.0, 0.0, -5.0 * get_yaw(sim, handles["load"])])

            robot_states: list[dict[str, float]] = []
            for idx, robot in enumerate(handles["robots"]):
                robot_pos = np.array(sim.getObjectPosition(robot, -1), dtype=float)
                robot_vel = np.array(sim.getObjectVelocity(robot)[0], dtype=float)
                target = load_pos + np.array([target_offsets[idx][0], target_offsets[idx][1], 0.0], dtype=float)
                error = target - robot_pos
                force = np.array(
                    [
                        cfg.push_force_n + cfg.longitudinal_gain * error[0] - cfg.damping_gain * robot_vel[0],
                        cfg.lateral_gain * error[1] - cfg.damping_gain * robot_vel[1],
                        0.0,
                    ],
                    dtype=float,
                )
                force_norm = float(np.linalg.norm(force[:2]))
                if force_norm > cfg.max_robot_force_n:
                    force[:2] *= cfg.max_robot_force_n / force_norm
                sim.addForceAndTorque(robot, force.tolist(), [0.0, 0.0, -4.0 * get_yaw(sim, robot)])
                robot_states.append(
                    {
                        "robot": handles["robot_names"][idx],
                        "x": robot_pos[0],
                        "y": robot_pos[1],
                        "z": robot_pos[2],
                        "vx": robot_vel[0],
                        "vy": robot_vel[1],
                        "force_x": force[0],
                        "force_y": force[1],
                    }
                )

            collisions = count_collisions(sim, [handles["load"], *handles["robots"]], handles["racks"])
            min_rack_distance = min_distance_to_racks(sim, [handles["load"], *handles["robots"]], handles["racks"])
            rows.append(
                {
                    "t": round(t, 4),
                    "object": "Load_rectangular_dynamic",
                    "x": load_pos[0],
                    "y": load_pos[1],
                    "z": load_pos[2],
                    "vx": load_vel[0],
                    "vy": load_vel[1],
                    "yaw": get_yaw(sim, handles["load"]),
                    "force_x": load_force[0],
                    "force_y": load_force[1],
                    "rack_collisions": collisions,
                    "min_rack_distance": min_rack_distance,
                }
            )
            for state in robot_states:
                rows.append(
                    {
                        "t": round(t, 4),
                        "object": state["robot"],
                        "x": state["x"],
                        "y": state["y"],
                        "z": state["z"],
                        "vx": state["vx"],
                        "vy": state["vy"],
                        "yaw": 0.0,
                        "force_x": state["force_x"],
                        "force_y": state["force_y"],
                        "rack_collisions": collisions,
                        "min_rack_distance": min_rack_distance,
                    }
                )

            if step % cfg.frame_every_steps == 0:
                frame = capture_sensor_frame(sim, handles["top_sensor"], out_dir / f"frames/coppelia_top_{step:04d}.png")
                if frame is not None:
                    frame_paths.append(frame)
            sim.step()
    finally:
        try:
            sim.stopSimulation()
        except Exception:
            pass
    return rows, frame_paths, time.perf_counter() - start


def get_yaw(sim, handle: int) -> float:
    return float(sim.getObjectOrientation(handle, -1)[2])


def count_collisions(sim, moving: list[int], racks: list[int]) -> int:
    count = 0
    for item in moving:
        for rack in racks:
            try:
                result = sim.checkCollision(item, rack)
                if isinstance(result, (list, tuple)):
                    collides = bool(result[0])
                else:
                    collides = bool(result)
                count += int(collides)
            except Exception:
                continue
    return count


def min_distance_to_racks(sim, moving: list[int], racks: list[int]) -> float:
    best = math.inf
    for item in moving:
        p = np.array(sim.getObjectPosition(item, -1), dtype=float)
        for rack in racks:
            q = np.array(sim.getObjectPosition(rack, -1), dtype=float)
            best = min(best, float(np.linalg.norm((p - q)[:2])))
    return best


def capture_sensor_frame(sim, sensor: int, path: Path) -> Path | None:
    try:
        sim.handleVisionSensor(sensor)
        img, resolution = sim.getVisionSensorImg(sensor)
        data = np.frombuffer(img, dtype=np.uint8)
        if data.size != int(resolution[0]) * int(resolution[1]) * 3:
            return None
        frame = data.reshape((int(resolution[1]), int(resolution[0]), 3))
        frame = np.flipud(frame)
        imageio.imwrite(path, frame)
        return path
    except Exception:
        return None


def compute_metrics(rows: list[dict[str, Any]], rack_names: list[str], cfg: CampaignConfig) -> dict[str, Any]:
    load_rows = [row for row in rows if row["object"] == "Load_rectangular_dynamic"]
    if not load_rows:
        return {"passed": False, "reason": "no_load_rows"}
    start_x = float(load_rows[0]["x"])
    end_x = float(load_rows[-1]["x"])
    displacement = end_x - start_x
    max_abs_y = max(abs(float(row["y"])) for row in load_rows)
    max_abs_yaw = max(abs(float(row["yaw"])) for row in load_rows)
    total_collisions = sum(int(row["rack_collisions"]) for row in load_rows)
    min_rack_distance = min(float(row["min_rack_distance"]) for row in load_rows)
    mean_speed = float(np.mean([math.hypot(float(row["vx"]), float(row["vy"])) for row in load_rows]))
    passed = (
        displacement >= 4.0
        and total_collisions == 0
        and max_abs_y <= cfg.corridor_half_width_m
        and max_abs_yaw <= 0.75
        and min_rack_distance >= 0.75
    )
    return {
        "passed": bool(passed),
        "load_displacement_m": displacement,
        "load_start_x_m": start_x,
        "load_end_x_m": end_x,
        "max_abs_load_y_m": max_abs_y,
        "max_abs_load_yaw_rad": max_abs_yaw,
        "rack_collision_count": int(total_collisions),
        "min_rack_center_distance_m": min_rack_distance,
        "mean_load_speed_mps": mean_speed,
        "rack_count": len(rack_names),
        "gate": "displacement>=4m, rack_collisions=0, |y| within corridor, yaw bounded",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def render_trace(rows: list[dict[str, Any]], cfg: CampaignConfig, plot_path: Path, video_path: Path) -> None:
    times = sorted({float(row["t"]) for row in rows})
    fig, ax = plt.subplots(figsize=(9.0, 5.4))

    def draw_base() -> None:
        ax.set_xlim(-cfg.warehouse_width_m / 2, cfg.warehouse_width_m / 2)
        ax.set_ylim(-cfg.warehouse_depth_m / 2, cfg.warehouse_depth_m / 2)
        ax.set_aspect("equal", adjustable="box")
        ax.add_patch(
            plt.Rectangle(
                (-cfg.warehouse_width_m / 2, -cfg.warehouse_depth_m / 2),
                cfg.warehouse_width_m,
                cfg.warehouse_depth_m,
                facecolor="#e5e7eb",
                edgecolor="#374151",
                linewidth=1.0,
            )
        )
        for x, y, sx, sy in rack_layout(cfg):
            ax.add_patch(plt.Rectangle((x - sx / 2, y - sy / 2), sx, sy, facecolor="#6b7280", edgecolor="#374151"))
        ax.axhline(cfg.corridor_half_width_m, color="#dc2626", linestyle="--", linewidth=0.9, alpha=0.55)
        ax.axhline(-cfg.corridor_half_width_m, color="#dc2626", linestyle="--", linewidth=0.9, alpha=0.55)
        ax.scatter([cfg.load_start[0]], [cfg.load_start[1]], marker="s", color="#1d4ed8", s=50, label="inicio")
        ax.scatter([cfg.load_goal[0]], [cfg.load_goal[1]], marker="*", color="#15803d", s=90, label="meta")
        ax.grid(alpha=0.16)

    def draw(frame_idx: int) -> list[Any]:
        ax.clear()
        draw_base()
        t = times[frame_idx]
        frame = [row for row in rows if float(row["t"]) == t]
        for row in frame:
            if row["object"] == "Load_rectangular_dynamic":
                ax.add_patch(
                    plt.Rectangle(
                        (float(row["x"]) - cfg.load_size[0] / 2, float(row["y"]) - cfg.load_size[1] / 2),
                        cfg.load_size[0],
                        cfg.load_size[1],
                        facecolor="#f59e0b",
                        edgecolor="#92400e",
                        alpha=0.92,
                    )
                )
            else:
                ax.scatter([float(row["x"])], [float(row["y"])], color="#0f172a", s=24)
        ax.set_title(f"H12 CoppeliaSim real physics t={t:.2f}s")
        ax.legend(loc="upper left", fontsize=7)
        return []

    draw(len(times) - 1)
    fig.savefig(plot_path, dpi=180)
    ani = animation.FuncAnimation(fig, draw, frames=len(times), interval=60, blit=False)
    ani.save(video_path, writer="ffmpeg", dpi=130, fps=18)
    plt.close(fig)


def make_camera_video(frame_paths: list[Path], out_path: Path) -> Path | None:
    if not frame_paths:
        return None
    images = [imageio.imread(path) for path in frame_paths]
    imageio.mimsave(out_path, images, fps=8)
    return out_path


def write_manifest(out_dir: Path, summary: dict[str, Any]) -> None:
    row = {
        "campaign": summary["campaign"],
        "scene": summary["scene"],
        "status": summary["status"],
        "real_coppelia": summary["real_coppelia"],
        "synthetic_fallback": summary["synthetic_fallback"],
        "scene_file": summary.get("scene_file", ""),
        "csv": summary.get("csv", ""),
        "plot": summary.get("plot", ""),
        "trace_video": summary.get("trace_video", ""),
        "camera_video": summary.get("camera_video", ""),
    }
    write_csv(out_dir / "manifest.csv", [row])
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H12 CoppeliaSim real physics campaign",
        "",
        "This campaign is the real CoppeliaSim route. It is not a synthetic fallback render.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Coppelia executable: `{summary['coppelia_executable']}`",
        f"- Scene: `{summary['scene']}`",
        "",
        "Regenerate:",
        "",
        "```powershell",
        "python scripts\\coppelia\\run_h12_coppelia_real.py",
        "```",
    ]
    if "metrics" in summary:
        metrics = summary["metrics"]
        lines.extend(
            [
                "",
                "Gate summary:",
                "",
                f"- Load displacement: `{metrics['load_displacement_m']:.3f} m`",
                f"- Rack collision count: `{metrics['rack_collision_count']}`",
                f"- Minimum rack center distance: `{metrics['min_rack_center_distance_m']:.3f} m`",
                f"- Maximum absolute load lateral offset: `{metrics['max_abs_load_y_m']:.3f} m`",
            ]
        )
    if "error" in summary:
        lines.extend(["", "Error:", "", f"`{summary['error']}`"])
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def stop_process(process: subprocess.Popen[Any]) -> None:
    try:
        process.terminate()
        process.wait(timeout=8)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
