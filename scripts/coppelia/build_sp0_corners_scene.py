"""Build a minimal SP0 multi-AMR CoppeliaSim scene.

Scenario:

* 10.5 m x 10.5 m floor with crossed loading/drop platforms
* eight Pioneer P3-DX robots on individual charge pads
* homogeneous boxes that choose one of three target unload zones before assignment
* AMR dispatch by centralized Hungarian, distributed greedy, or distributed replicator proxy

The scene is intentionally plain. It is meant as an SP0 mechanics and dispatch
smoke scene, not as an AWS-style warehouse.
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

import yaml


ROOT = Path(__file__).resolve().parents[2]
COPPELIA_ROOT = Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu")
PIONEER_MODEL = COPPELIA_ROOT / "models/robots/mobile/pioneer p3dx.ttm"
CLIENT_DIR = COPPELIA_ROOT / "programming/zmqRemoteApi/clients/python/src"
COPPELIA_EXE = COPPELIA_ROOT / "coppeliaSim.exe"


@dataclass(frozen=True)
class BoxSpec:
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    color: tuple[float, float, float]
    yaw_rad: float = 0.0
    mass_kg: float = 0.1
    static: bool = True
    respondable: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=23000, help="CoppeliaSim ZMQ Remote API port.")
    parser.add_argument("--scene-dir", type=Path, default=ROOT / "coppeliasim/real_scenes")
    parser.add_argument("--out", type=Path, default=ROOT / "results/coppeliasim_validation/sp0_corners")
    parser.add_argument("--coppelia-root", type=Path, default=COPPELIA_ROOT)
    parser.add_argument("--coppelia", type=Path, default=COPPELIA_EXE)
    parser.add_argument("--no-export-ttt", action="store_true")
    parser.add_argument("--launch-coppelia", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scene_dir = args.scene_dir.resolve()
    out_dir = args.out.resolve()
    scene_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    scene = build_scene_dict(args.coppelia_root.resolve())
    validation = validate_layout(scene)
    stem = "sp0_corners_drop_suction_pioneer"
    yaml_path = scene_dir / f"{stem}.yaml"
    lua_path = scene_dir / f"{stem}.lua"
    ttt_path = scene_dir / f"{stem}.ttt"
    manifest_path = out_dir / "manifest.csv"

    yaml_path.write_text(yaml.safe_dump(scene, sort_keys=False, allow_unicode=False), encoding="utf-8")
    lua_path.write_text(render_lua_scene(scene), encoding="utf-8")
    (out_dir / "layout_validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")

    export_status = "not_requested" if args.no_export_ttt else "not_started"
    export_error = ""
    object_count = ""
    top_camera = ""
    top_camera_nonzero_ratio = ""

    if not args.no_export_ttt:
        try:
            result = export_ttt(scene, args.port, ttt_path, args.coppelia, args.launch_coppelia, out_dir)
            export_status = "exported_ttt"
            object_count = str(result["object_count"])
            top_camera = result.get("top_camera", "")
            top_camera_nonzero_ratio = result.get("top_camera_nonzero_ratio", "")
        except Exception as exc:  # noqa: BLE001
            export_status = "export_failed"
            export_error = repr(exc)

    write_manifest(
        manifest_path,
        {
            "scene": scene["scenario"],
            "yaml": rel(yaml_path),
            "lua": rel(lua_path),
            "ttt": rel(ttt_path) if ttt_path.exists() else "",
            "export_status": export_status,
            "export_error": export_error,
            "object_count": object_count,
            "top_camera": top_camera,
            "top_camera_nonzero_ratio": top_camera_nonzero_ratio,
            "robots": len(scene["robots"]),
            "boxes": len(scene["boxes"]),
            "zones": len(scene["zones"]),
            "layout_status": validation["status"],
            "layout_collisions": validation["collision_count"],
        },
    )
    return 0 if export_status != "export_failed" else 2


def build_scene_dict(coppelia_root: Path) -> dict[str, Any]:
    zones = [
        zone("carga_robot_01", "charge", (-4.35, -4.20), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_02", "charge", (-3.55, -4.20), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_03", "charge", (-4.35, -3.40), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_04", "charge", (-3.55, -3.40), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_05", "charge", (4.35, 4.20), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_06", "charge", (3.55, 4.20), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_07", "charge", (4.35, 3.40), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("carga_robot_08", "charge", (3.55, 3.40), (0.62, 0.62), (0.16, 0.34, 0.58)),
        zone("caida_cajas_nw", "drop", (-4.05, 3.75), (1.38, 1.38), (0.88, 0.64, 0.12)),
        zone("caida_cajas_se", "drop", (4.05, -3.75), (1.38, 1.38), (0.88, 0.64, 0.12)),
        zone("target_descarga_oeste", "unload", (-1.80, 0.0), (1.05, 1.05), (0.14, 0.55, 0.32)),
        zone("target_descarga_centro", "unload", (0.0, 0.0), (1.05, 1.05), (0.14, 0.55, 0.32)),
        zone("target_descarga_este", "unload", (1.80, 0.0), (1.05, 1.05), (0.14, 0.55, 0.32)),
    ]
    box_size = [0.36, 0.28, 0.18]
    robots = [
        robot("SP0_Pioneer_01", "carga_robot_01", "caida_cajas_nw", 0.00, [-4.35, -4.20, 0.18]),
        robot("SP0_Pioneer_02", "carga_robot_02", "caida_cajas_se", 0.40, [-3.55, -4.20, 0.18]),
        robot("SP0_Pioneer_03", "carga_robot_03", "caida_cajas_nw", 0.80, [-4.35, -3.40, 0.18]),
        robot("SP0_Pioneer_04", "carga_robot_04", "caida_cajas_se", 1.20, [-3.55, -3.40, 0.18]),
        robot("SP0_Pioneer_05", "carga_robot_05", "caida_cajas_se", 0.00, [4.35, 4.20, 0.18]),
        robot("SP0_Pioneer_06", "carga_robot_06", "caida_cajas_nw", 0.40, [3.55, 4.20, 0.18]),
        robot("SP0_Pioneer_07", "carga_robot_07", "caida_cajas_se", 0.80, [4.35, 3.40, 0.18]),
        robot("SP0_Pioneer_08", "carga_robot_08", "caida_cajas_nw", 1.20, [3.55, 3.40, 0.18]),
    ]
    for robot_spec, battery in zip(robots, (100.0, 92.0, 84.0, 76.0, 88.0, 80.0, 68.0, 60.0), strict=True):
        robot_spec["battery_initial_pct"] = battery
    target_names = ["target_descarga_oeste", "target_descarga_centro", "target_descarga_este"]
    slot_offsets = [(-0.32, -0.28), (0.32, -0.28), (0.0, 0.30)]
    boxes = []
    for source_name, drop_name, target_offset in (("NW", "caida_cajas_nw", 0), ("SE", "caida_cajas_se", 1)):
        for slot_index, offset in enumerate(slot_offsets, start=1):
            boxes.append(
                {
                    "name": f"SP0_box_{source_name}_{slot_index:02d}",
                    "size": box_size,
                    "mass_kg": 2.0,
                    "drop": drop_name,
                    "slot_offset": [offset[0], offset[1]],
                    "target": target_names[(slot_index - 1 + target_offset) % len(target_names)],
                }
            )
    scene = {
        "scenario": "sp0_corners_drop_suction_pioneer",
        "description": "SP0 CoppeliaSim scene: corner loads, eight Pioneer AMRs, three target unload zones and dispatch policy comparison.",
        "dimensions_m": {"width": 10.5, "depth": 10.5},
        "model_paths": {"pioneer_p3dx": str(coppelia_root / "models/robots/mobile/pioneer p3dx.ttm")},
        "zones": zones,
        "targets": target_names,
        "assignment_policy": "hungarian_centralized",
        "benchmark_policies": ["hungarian_centralized", "distributed_greedy", "replicator_distributed"],
        "robots": robots,
        "boxes": boxes,
        "box_size_m": box_size,
        "drop_height_m": 1.55,
        "carry_height_m": 0.42,
        "suction_height_m": 3.20,
        "amr": {
            "max_speed_mps": 0.55,
            "sim_speed_multiplier": 2.0,
            "arrival_radius_m": 0.20,
            "drop_alignment_radius_m": 0.07,
            "avoidance_radius_m": 1.05,
            "hard_clearance_m": 0.62,
            "footprint_radius_m": 0.46,
            "sensor_radius_m": 0.95,
            "comm_radius_m": 1.65,
            "sensor_fill_alpha": 0.70,
            "battery_low_pct": 28.0,
            "battery_resume_pct": 86.0,
            "battery_move_drain_pct_per_m": 2.2,
            "battery_load_extra_pct_per_m": 0.9,
            "battery_idle_drain_pct_per_s": 0.015,
            "battery_charge_pct_per_s": 7.5,
            "box_respawn_s": 2.0,
        },
        "metadata": {
            "purpose": "SP0 physical smoke scene for spawn/drop, carry, unload count.",
            "corner_policy": "Individual charge pads in SW/NE; crossed drop zones in NW/SE; three central target unload zones.",
            "physics_policy": "AMRs are kinematic with collidable safety footprints and local reactive collision avoidance.",
        },
    }
    return scene


def zone(name: str, kind: str, center: tuple[float, float], size: tuple[float, float], color: tuple[float, float, float]) -> dict[str, Any]:
    return {"name": name, "kind": kind, "center": [center[0], center[1], 0.02], "size": [size[0], size[1], 0.02], "color": list(color)}


def robot(name: str, base: str, drop: str, phase_offset_s: float, position: list[float]) -> dict[str, Any]:
    return {"name": name, "base": base, "drop": drop, "release_delay_s": phase_offset_s, "position": position, "heading_rad": 0.0}


def validate_layout(scene: dict[str, Any]) -> dict[str, Any]:
    width = float(scene["dimensions_m"]["width"])
    depth = float(scene["dimensions_m"]["depth"])
    collisions: list[dict[str, str]] = []
    for zone_spec in scene["zones"]:
        x, y = zone_spec["center"][0], zone_spec["center"][1]
        sx, sy = zone_spec["size"][0], zone_spec["size"][1]
        if not (-width / 2 <= x - sx / 2 and x + sx / 2 <= width / 2 and -depth / 2 <= y - sy / 2 and y + sy / 2 <= depth / 2):
            collisions.append({"a": zone_spec["name"], "b": "sp0_boundary", "reason": "zone exceeds floor"})
    zone_names = {z["name"] for z in scene["zones"]}
    for robot_spec in scene["robots"]:
        if robot_spec["base"] not in zone_names:
            collisions.append({"a": robot_spec["name"], "b": robot_spec["base"], "reason": "base zone missing"})
        if robot_spec["drop"] not in zone_names:
            collisions.append({"a": robot_spec["name"], "b": robot_spec["drop"], "reason": "drop zone missing"})
    for box_spec in scene["boxes"]:
        if box_spec["drop"] not in zone_names:
            collisions.append({"a": box_spec["name"], "b": box_spec["drop"], "reason": "drop zone missing"})
        if box_spec.get("target") not in zone_names:
            collisions.append({"a": box_spec["name"], "b": str(box_spec.get("target")), "reason": "target zone missing"})
    status = "ok" if not collisions else "invalid"
    return {"status": status, "collision_count": len(collisions), "collisions": collisions}


def export_ttt(scene: dict[str, Any], port: int, ttt_path: Path, coppelia: Path, launch_coppelia: bool, out_dir: Path) -> dict[str, Any]:
    process: subprocess.Popen[Any] | None = None
    try:
        if launch_coppelia:
            process = launch_coppelia_headless(coppelia, port, out_dir / "coppelia_export.log")
        sim = connect(port)
        stop_if_running(sim)
        clear_scene(sim)
        build_scene(sim, scene)
        write_scene_metadata(sim, scene)
        top_camera_metrics = capture_camera_snapshot(sim, "/SP0_camera_top", out_dir / "sp0_top_camera.png")
        sim.saveScene(str(ttt_path))
        object_count = len(sim.getObjectsInTree(sim.handle_scene))
        return {
            "object_count": object_count,
            "top_camera": top_camera_metrics.get("path", ""),
            "top_camera_nonzero_ratio": top_camera_metrics.get("nonzero_ratio", ""),
        }
    finally:
        if process is not None:
            stop_process(process)


def clear_scene(sim) -> None:
    for method_name in ("newScene", "createNewScene"):
        method = getattr(sim, method_name, None)
        if method is None:
            continue
        try:
            method()
            return
        except Exception:
            pass
    handles = sim.getObjectsInTree(sim.handle_scene, sim.handle_all, 0)
    preserved_types = {sim.object_camera_type, sim.object_light_type}
    removable = []
    for handle in handles:
        try:
            if sim.getObjectType(handle) in preserved_types:
                continue
        except Exception:
            pass
        removable.append(handle)
    if removable:
        sim.removeObjects(removable)


def build_scene(sim, scene: dict[str, Any]) -> None:
    configure_scene_rendering(sim)
    root = sim.createDummy(0.04)
    set_alias(sim, root, "SP0_CORNERS_DROP_SUCTION_ROOT")
    add_floor(sim, scene)
    for zone_spec in scene["zones"]:
        add_zone(sim, zone_spec)
    for zone_spec in scene["zones"]:
        if zone_spec["kind"] == "drop":
            add_drop_chute(sim, zone_spec, scene["drop_height_m"])
        elif zone_spec["kind"] == "unload":
            add_unload_zone(sim, zone_spec)
    add_counter(sim, max_ticks=48)
    for robot_spec in scene["robots"]:
        add_pioneer(sim, scene["model_paths"]["pioneer_p3dx"], robot_spec, scene)
    for box_spec in scene["boxes"]:
        add_sp0_box(sim, box_spec, scene)
    add_camera(sim, scene)
    add_demo_script(sim, scene)


def configure_scene_rendering(sim) -> None:
    for param, value in (
        ("boolparam_shape_textures_are_visible", True),
    ):
        try:
            sim.setBoolParam(getattr(sim, param), value)
        except Exception:
            pass
    try:
        sim.setArrayParam(sim.arrayparam_background_color1, [0.82, 0.86, 0.90])
        sim.setArrayParam(sim.arrayparam_background_color2, [0.72, 0.76, 0.82])
        sim.setArrayParam(sim.arrayparam_ambient_light, [0.55, 0.55, 0.55])
    except Exception:
        pass


def add_floor(sim, scene: dict[str, Any]) -> None:
    width = float(scene["dimensions_m"]["width"])
    depth = float(scene["dimensions_m"]["depth"])
    add_box(sim, BoxSpec("SP0_floor", (0.0, 0.0, -0.025), (width, depth, 0.05), (0.46, 0.47, 0.46), static=True, respondable=True))
    add_box(sim, BoxSpec("SP0_boundary_north", (0.0, depth / 2, 0.04), (width, 0.045, 0.08), (0.08, 0.08, 0.08)))
    add_box(sim, BoxSpec("SP0_boundary_south", (0.0, -depth / 2, 0.04), (width, 0.045, 0.08), (0.08, 0.08, 0.08)))
    add_box(sim, BoxSpec("SP0_boundary_east", (width / 2, 0.0, 0.04), (0.045, depth, 0.08), (0.08, 0.08, 0.08)))
    add_box(sim, BoxSpec("SP0_boundary_west", (-width / 2, 0.0, 0.04), (0.045, depth, 0.08), (0.08, 0.08, 0.08)))


def add_zone(sim, zone_spec: dict[str, Any]) -> None:
    x, y, z = zone_spec["center"]
    sx, sy, sz = zone_spec["size"]
    color = tuple(zone_spec["color"])
    add_box(sim, BoxSpec(zone_spec["name"] + "_pad", (x, y, z), (sx, sy, sz), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_north", (x, y + sy / 2, z + 0.012), (sx, 0.035, 0.035), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_south", (x, y - sy / 2, z + 0.012), (sx, 0.035, 0.035), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_east", (x + sx / 2, y, z + 0.012), (0.035, sy, 0.035), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_west", (x - sx / 2, y, z + 0.012), (0.035, sy, 0.035), color, static=True, respondable=False))


def add_drop_chute(sim, zone_spec: dict[str, Any], drop_height: float) -> None:
    x, y, _ = zone_spec["center"]
    color = (0.90, 0.63, 0.08)
    post_color = (0.12, 0.12, 0.11)
    for idx, (ox, oy) in enumerate(((-0.35, -0.35), (-0.35, 0.35), (0.35, -0.35), (0.35, 0.35)), start=1):
        add_box(sim, BoxSpec(f"{zone_spec['name']}_chute_post_{idx}", (x + ox, y + oy, drop_height / 2), (0.055, 0.055, drop_height), post_color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_chute_top", (x, y, drop_height + 0.08), (0.82, 0.82, 0.12), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone_spec["name"] + "_drop_marker", (x, y, drop_height - 0.16), (0.42, 0.42, 0.035), (0.96, 0.80, 0.16), static=True, respondable=False))


def add_unload_zone(sim, zone_spec: dict[str, Any]) -> None:
    x, y, _ = zone_spec["center"]
    add_cylinder(sim, zone_spec["name"] + "_suction_pipe", 0.16, 1.55, (x, y, 2.50), (0.20, 0.62, 0.88), respondable=False)
    add_cylinder(sim, zone_spec["name"] + "_suction_beacon", 0.28, 0.16, (x, y, 3.36), (0.32, 0.80, 1.00), respondable=False)
    for idx, radius in enumerate((0.38, 0.52, 0.66), start=1):
        add_cylinder(sim, f"{zone_spec['name']}_suction_ring_{idx}", radius, 0.025, (x, y, 0.16 + idx * 0.16), (0.16, 0.68, 0.36), respondable=False)


def add_counter(sim, max_ticks: int) -> None:
    add_box(sim, BoxSpec("SP0_counter_panel", (0.0, -4.35, 0.55), (3.0, 0.10, 1.0), (0.12, 0.13, 0.14), static=True, respondable=False))
    for idx in range(1, max_ticks + 1):
        col = (idx - 1) % 12
        row = (idx - 1) // 12
        x = -1.32 + col * 0.24
        z = 0.25 + row * 0.26
        add_box(sim, BoxSpec(f"SP0_count_tick_{idx:02d}", (x, -4.42, z), (0.16, 0.035, 0.16), (0.22, 0.24, 0.25), static=True, respondable=False))


def battery_step_color(battery_pct: float) -> tuple[tuple[float, float, float], int]:
    step = int(math.floor(max(0.0, min(100.0, battery_pct)) / 100.0 * 9.0 + 0.5)) + 1
    t = (step - 1) / 9.0
    return (
        0.90 * (1.0 - t) + 0.12 * t,
        0.10 * (1.0 - t) + 0.88 * t,
        0.08 * (1.0 - t) + 0.16 * t,
    ), step


def add_ring_segments(
    sim,
    prefix: str,
    center: tuple[float, float, float],
    radius: float,
    segment_count: int,
    color: tuple[float, float, float],
) -> list[int]:
    handles = []
    arc = max(0.16, (2.0 * math.pi * radius / segment_count) * 0.58)
    for idx in range(segment_count):
        theta = (2.0 * math.pi * idx) / segment_count
        x = center[0] + math.cos(theta) * radius
        y = center[1] + math.sin(theta) * radius
        handle = add_box(
            sim,
            BoxSpec(
                f"{prefix}_{idx + 1:02d}",
                (x, y, center[2]),
                (arc, 0.025, 0.018),
                color,
                yaw_rad=theta + math.pi / 2.0,
                static=True,
                respondable=False,
            ),
        )
        handles.append(handle)
    return handles


def add_pioneer(sim, model_path: str, robot_spec: dict[str, Any], scene: dict[str, Any]) -> None:
    handle = load_model(sim, model_path)
    if handle is None:
        handle = add_cylinder(sim, robot_spec["name"] + "_fallback", 0.26, 0.25, tuple(robot_spec["position"]), (0.12, 0.12, 0.12))
    else:
        disable_model_scripts(sim, handle)
        make_model_visual_only(sim, handle)
    set_alias(sim, handle, robot_spec["name"])
    sim.setObjectPosition(handle, -1, robot_spec["position"])
    sim.setObjectOrientation(handle, -1, [0.0, 0.0, robot_spec["heading_rad"]])
    x, y, z = robot_spec["position"]
    marker = add_box(sim, BoxSpec(robot_spec["name"] + "_cargo_plate", (x, y, z + 0.30), (0.40, 0.32, 0.035), (0.08, 0.12, 0.16), static=True, respondable=False))
    try:
        sim.setObjectParent(marker, handle, True)
    except Exception:
        pass
    footprint = add_cylinder(
        sim,
        robot_spec["name"] + "_safety_footprint",
        0.46,
        0.012,
        (x, y, 0.035),
        (0.08, 0.50, 0.88),
        static=True,
        respondable=True,
        mass_kg=0.1,
    )
    try:
        sim.setObjectParent(footprint, handle, True)
    except Exception:
        pass
    amr = scene["amr"]
    ring_color, _ = battery_step_color(float(robot_spec.get("battery_initial_pct", 100.0)))
    sensor_fill = add_cylinder(
        sim,
        robot_spec["name"] + "_sensor_fill",
        float(amr["sensor_radius_m"]),
        0.006,
        (x, y, 0.044),
        ring_color,
        static=True,
        respondable=False,
        alpha=float(amr.get("sensor_fill_alpha", 0.70)),
    )
    try:
        sim.setObjectParent(sensor_fill, handle, True)
    except Exception:
        pass
    for ring_name, radius, z in (
        ("sensor_radius", float(amr["sensor_radius_m"]), 0.052),
        ("comm_radius", float(amr["comm_radius_m"]), 0.072),
    ):
        ring_handles = add_ring_segments(
            sim,
            robot_spec["name"] + "_" + ring_name,
            (x, y, z),
            radius,
            24,
            ring_color,
        )
        for ring_handle in ring_handles:
            try:
                sim.setObjectParent(ring_handle, handle, True)
            except Exception:
                pass


def add_sp0_box(sim, box_spec: dict[str, Any], scene: dict[str, Any]) -> None:
    drop_zone = next(zone_spec for zone_spec in scene["zones"] if zone_spec["name"] == box_spec["drop"])
    x, y, _ = drop_zone["center"]
    dx, dy = box_spec.get("slot_offset", [0.0, 0.0])
    x += float(dx)
    y += float(dy)
    z = float(scene["drop_height_m"]) + 0.18
    handle = add_box(sim, BoxSpec(box_spec["name"], (x, y, z), tuple(box_spec["size"]), (0.68, 0.50, 0.28), mass_kg=float(box_spec["mass_kg"]), static=True, respondable=False))
    add_box(sim, BoxSpec(box_spec["name"] + "_label", (x, y, z + 0.02), (0.18, 0.012, 0.08), (0.90, 0.90, 0.80), static=True, respondable=False))
    try:
        label = sim.getObject("/" + box_spec["name"] + "_label")
        sim.setObjectParent(label, handle, True)
    except Exception:
        pass


def add_camera(sim, scene: dict[str, Any]) -> None:
    ortho = max(float(scene["dimensions_m"]["width"]), float(scene["dimensions_m"]["depth"])) + 1.8
    top = sim.createVisionSensor(1 + 4, [1280, 960, 0, 0], [0.05, 40.0, ortho, 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0])
    set_alias(sim, top, "SP0_camera_top")
    sim.setExplicitHandling(top, 1)
    try:
        sim.setObjectInt32Param(top, sim.visionintparam_perspective_operation, 0)
        sim.setObjectFloatParam(top, sim.visionfloatparam_ortho_size, ortho)
    except Exception:
        pass
    sim.setObjectPosition(top, -1, [0.0, 0.0, 12.5])
    sim.setObjectOrientation(top, -1, [0.0, math.pi, 0.0])
    try:
        cameras = sim.getObjectsInTree(sim.handle_scene, sim.object_camera_type, 0)
        camera = cameras[0]
        set_alias(sim, camera, "DefaultCamera")
        try:
            sim.cameraFitToView(camera + sim.handleflag_camera, None, 0, 1.20)
        except Exception:
            pass
        try:
            sim.adjustView(0, camera, 0, "SP0 default view")
            sim.cameraFitToView(0, None, 0, 1.20)
        except Exception:
            pass
    except Exception:
        pass
    try:
        lights = sim.getObjectsInTree(sim.handle_scene, sim.object_light_type, 0)
        light = lights[0]
        set_alias(sim, light, "DefaultLight")
        sim.setObjectPosition(light, -1, [1.5, -2.5, 7.0])
    except Exception:
        pass


def add_demo_script(sim, scene: dict[str, Any]) -> None:
    code = render_demo_script(scene)
    dummy = sim.createDummy(0.035)
    set_alias(sim, dummy, "SP0_demo_controller")
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


def render_demo_script(scene: dict[str, Any]) -> str:
    scene_lua = lua_table(scene)
    return """-- SP0 AMR controller: dispatch policies, battery return and local avoidance.
local sim = require('sim')
local scene = __SCENE__
local zones = {}
local robots = {}
local robotOrder = {}
local boxes = {}
local boxOrder = {}
local ticks = {}
local deliveredCount = 0
local lastT = 0.0
local lastAssignmentT = -99.0
local globalMinDistance = 99.0
local currentPolicy = scene.assignment_policy or 'hungarian_centralized'
local amrConfig

local function getByAlias(alias)
    local ok, handle = pcall(sim.getObject, '/' .. alias)
    if ok and handle and handle >= 0 then return handle end
    return nil
end

local function clamp(v, lo, hi)
    return math.max(lo, math.min(hi, v))
end

local function atan2(y, x)
    if math.atan2 then return math.atan2(y, x) end
    return math.atan(y, x)
end

local function dist2(a, b)
    local dx = b[1] - a[1]
    local dy = b[2] - a[2]
    return math.sqrt(dx * dx + dy * dy)
end

local function yawTo(a, b)
    return atan2(b[2] - a[2], b[1] - a[1])
end

local function zoneCenter(name, z)
    local c = zones[name] and zones[name].center or {0.0, 0.0, 0.02}
    return {c[1], c[2], z or 0.18}
end

local function targetIndex(name)
    for i, targetName in ipairs(scene.targets or {}) do
        if targetName == name then return i end
    end
    return 1
end

local function targetNameFromIndex(index)
    local targets = scene.targets or {}
    if #targets == 0 then return 'target_descarga_centro' end
    return targets[((index - 1) % #targets) + 1]
end

local function pickupCenter(boxEntry, z)
    local base = zoneCenter(boxEntry.spec.drop, z or 0.18)
    local offset = boxEntry.spec.slot_offset or {0.0, 0.0}
    return {base[1] + (offset[1] or 0.0), base[2] + (offset[2] or 0.0), z or 0.18}
end

local function targetCenter(boxEntry, z)
    return zoneCenter(boxEntry.target or boxEntry.spec.target or targetNameFromIndex(1), z or 0.18)
end

local function simScale()
    return math.max(0.1, amrConfig('sim_speed_multiplier', 1.0))
end

local function scaledDuration(seconds)
    return seconds / simScale()
end

local function setBoxVisible(handle, visible)
    local layer = visible and 1 or 0
    pcall(sim.setObjectInt32Param, handle, sim.objintparam_visibility_layer, layer)
    local ok, children = pcall(sim.getObjectsInTree, handle, sim.handle_all, 0)
    if ok and children then
        for _, child in ipairs(children) do
            pcall(sim.setObjectInt32Param, child, sim.objintparam_visibility_layer, layer)
        end
    end
end

function amrConfig(name, fallback)
    if scene.amr and scene.amr[name] then return scene.amr[name] end
    return fallback
end

local function collectRing(prefix)
    local handles = {}
    for i = 1, 24 do
        local h = getByAlias(string.format('%s_%02d', prefix, i))
        if h then handles[#handles + 1] = h end
    end
    return handles
end

local function batteryColor(batteryPct)
    local step = math.floor(clamp(batteryPct, 0.0, 100.0) / 100.0 * 9.0 + 0.5) + 1
    local t = (step - 1) / 9.0
    return {
        0.90 * (1.0 - t) + 0.12 * t,
        0.10 * (1.0 - t) + 0.88 * t,
        0.08 * (1.0 - t) + 0.16 * t
    }, step
end

local function setManyColor(handles, color)
    for _, h in ipairs(handles or {}) do
        pcall(sim.setShapeColor, h, nil, sim.colorcomponent_ambient_diffuse, color)
    end
end

local function setAlpha(handle, alpha)
    if not handle then return end
    local transparency = 1.0 - clamp(alpha or 1.0, 0.0, 1.0)
    if sim.colorcomponent_transparency then
        pcall(sim.setShapeColor, handle, nil, sim.colorcomponent_transparency, {transparency})
    end
    if sim.shapefloatparam_transparency then
        pcall(sim.setObjectFloatParam, handle, sim.shapefloatparam_transparency, transparency)
    end
end

local function targetColor(targetName)
    local palette = {
        {0.30, 0.85, 1.00},
        {0.24, 0.82, 0.34},
        {0.96, 0.66, 0.16},
        {0.90, 0.22, 0.18}
    }
    return palette[((targetIndex(targetName) - 1) % #palette) + 1]
end

local function updateBoxTargetVisual(boxEntry)
    if boxEntry.label then
        pcall(sim.setShapeColor, boxEntry.label, nil, sim.colorcomponent_ambient_diffuse, targetColor(boxEntry.target))
    end
    pcall(sim.setNamedStringParam, 'sp0_target_' .. boxEntry.spec.name, boxEntry.target or '')
end

local function advanceBoxTarget(boxEntry)
    boxEntry.targetIndex = (boxEntry.targetIndex or targetIndex(boxEntry.spec.target)) + 1
    boxEntry.target = targetNameFromIndex(boxEntry.targetIndex)
    updateBoxTargetVisual(boxEntry)
end

local function readPolicy()
    local ok, value = pcall(sim.getNamedStringParam, 'sp0_assignment_policy')
    if ok and value and value ~= '' then
        currentPolicy = value
    end
    pcall(sim.setNamedStringParam, 'sp0_assignment_policy_active', currentPolicy)
    return currentPolicy
end

local function updateCounter()
    for i, tick in ipairs(ticks) do
        if tick then
            if i <= deliveredCount then
                pcall(sim.setShapeColor, tick, nil, sim.colorcomponent_ambient_diffuse, {0.18, 0.78, 0.30})
            else
                pcall(sim.setShapeColor, tick, nil, sim.colorcomponent_ambient_diffuse, {0.22, 0.24, 0.25})
            end
        end
    end
    pcall(sim.setNamedInt32Param, 'sp0_delivered_count', deliveredCount)
end

local function updateBatteryVisual(entry)
    local color, step = batteryColor(entry.battery)
    if entry.sensorFill then
        pcall(sim.setShapeColor, entry.sensorFill, nil, sim.colorcomponent_ambient_diffuse, color)
        setAlpha(entry.sensorFill, amrConfig('sensor_fill_alpha', 0.70))
    end
    setManyColor(entry.sensorRing, color)
    setManyColor(entry.commRing, color)
    pcall(sim.setNamedFloatParam, 'sp0_battery_' .. entry.spec.name, entry.battery)
    pcall(sim.setNamedInt32Param, 'sp0_battery_step_' .. entry.spec.name, step)
end

function sysCall_init()
    for _, z in ipairs(scene.zones) do zones[z.name] = z end
    for index, r in ipairs(scene.robots) do
        local handle = getByAlias(r.name)
        if handle then
            local p = sim.getObjectPosition(handle, -1)
            robots[r.name] = {
                handle = handle,
                spec = r,
                index = index,
                pos = {p[1], p[2], 0.18},
                yaw = r.heading_rad or 0.0,
                state = 'idle',
                stateStart = 0.0,
                waitUntil = 0.0,
                carrying = false,
                assignedBox = nil,
                releaseDelay = r.release_delay_s or 0.0,
                battery = r.battery_initial_pct or 100.0,
                footprint = getByAlias(r.name .. '_safety_footprint'),
                sensorFill = getByAlias(r.name .. '_sensor_fill'),
                sensorRing = collectRing(r.name .. '_sensor_radius'),
                commRing = collectRing(r.name .. '_comm_radius'),
                minDistance = 99.0
            }
            robotOrder[#robotOrder + 1] = r.name
            updateBatteryVisual(robots[r.name])
        end
    end
    for _, b in ipairs(scene.boxes) do
        local handle = getByAlias(b.name)
        if handle then
            local index = targetIndex(b.target)
            boxes[b.name] = {
                handle = handle,
                label = getByAlias(b.name .. '_label'),
                spec = b,
                state = 'waiting',
                assignedRobot = nil,
                carrier = nil,
                target = b.target,
                targetIndex = index,
                stateStart = 0.0,
                waitUntil = 0.0,
                respawnAt = 0.0
            }
            boxOrder[#boxOrder + 1] = b.name
            updateBoxTargetVisual(boxes[b.name])
        end
    end
    for i = 1, 48 do
        ticks[i] = getByAlias(string.format('SP0_count_tick_%02d', i))
    end
    pcall(sim.setNamedStringParam, 'sp0_assignment_policy', currentPolicy)
    updateCounter()
end

local function targetFor(entry)
    local assigned = entry.assignedBox and boxes[entry.assignedBox]
    if (entry.state == 'to_box' or entry.state == 'pickup_wait') and assigned then
        return pickupCenter(assigned, 0.18)
    elseif entry.state == 'to_unload' or entry.state == 'unload_wait' then
        if assigned then return targetCenter(assigned, 0.18) end
        return zoneCenter(targetNameFromIndex(1), 0.18)
    elseif entry.state == 'to_charge' or entry.state == 'charging' then
        return zoneCenter(entry.spec.base, 0.18)
    end
    return entry.pos
end

local function progress(entry, t)
    local duration = math.max(0.001, entry.waitUntil - entry.stateStart)
    return clamp((t - entry.stateStart) / duration, 0.0, 1.0)
end

local function releaseAssignedBox(entry)
    if entry.assignedBox and boxes[entry.assignedBox] then
        local b = boxes[entry.assignedBox]
        if b.state == 'assigned' then
            b.state = 'waiting'
            b.assignedRobot = nil
        end
    end
    entry.assignedBox = nil
end

local function updateMission(entry, t)
    local low = amrConfig('battery_low_pct', 28.0)
    local resume = amrConfig('battery_resume_pct', 86.0)
    local arrival = amrConfig('arrival_radius_m', 0.24)
    local dropArrival = amrConfig('drop_alignment_radius_m', 0.12)
    if entry.state == 'charging' then
        if entry.battery >= resume then
            entry.state = 'idle'
            entry.stateStart = t
        end
        return
    end
    if entry.state == 'to_charge' then
        if dist2(entry.pos, zoneCenter(entry.spec.base, 0.18)) <= arrival then
            entry.state = 'charging'
            entry.stateStart = t
        end
        return
    end
    if entry.battery <= low and not entry.carrying then
        releaseAssignedBox(entry)
        entry.state = 'to_charge'
        entry.stateStart = t
        return
    end
    if entry.state == 'idle' or t < entry.releaseDelay then return end
    local target = targetFor(entry)
    local d = dist2(entry.pos, target)
    if entry.state == 'to_box' and d <= dropArrival then
        local b = boxes[entry.assignedBox]
        if b then
            local pickup = pickupCenter(b, 0.18)
            entry.pos[1] = pickup[1]
            entry.pos[2] = pickup[2]
            entry.yaw = yawTo(entry.pos, targetCenter(b, 0.18))
            pcall(sim.setObjectPosition, entry.handle, -1, {entry.pos[1], entry.pos[2], entry.pos[3]})
            pcall(sim.setObjectOrientation, entry.handle, -1, {0, 0, entry.yaw})
            b.state = 'pickup_wait'
            b.carrier = entry.spec.name
            b.stateStart = t
            b.waitUntil = t + scaledDuration(1.20)
        end
        entry.state = 'pickup_wait'
        entry.stateStart = t
        entry.waitUntil = t + scaledDuration(1.20)
        entry.carrying = false
    elseif entry.state == 'pickup_wait' and t >= entry.waitUntil then
        local b = boxes[entry.assignedBox]
        if b then b.state = 'carrying' end
        entry.state = 'to_unload'
        entry.stateStart = t
        entry.carrying = true
    elseif entry.state == 'to_unload' and d <= arrival then
        local b = boxes[entry.assignedBox]
        if b then
            b.state = 'unload_wait'
            b.stateStart = t
            b.waitUntil = t + scaledDuration(1.25)
        end
        entry.state = 'unload_wait'
        entry.stateStart = t
        entry.waitUntil = t + scaledDuration(1.25)
    elseif entry.state == 'unload_wait' and t >= entry.waitUntil then
        if entry.carrying then
            deliveredCount = deliveredCount + 1
            updateCounter()
        end
        local b = boxes[entry.assignedBox]
        if b then
            b.state = 'cooldown'
            b.assignedRobot = nil
            b.carrier = nil
            b.respawnAt = t + scaledDuration(amrConfig('box_respawn_s', 2.0))
        end
        entry.assignedBox = nil
        entry.stateStart = t
        entry.carrying = false
        if entry.battery <= resume then
            entry.state = 'to_charge'
        else
            entry.state = 'idle'
        end
    end
end

local function assignmentEnergy(entry, boxEntry)
    local drop = pickupCenter(boxEntry, 0.18)
    local unload = targetCenter(boxEntry, 0.18)
    local base = zoneCenter(entry.spec.base, 0.18)
    local unloaded = dist2(entry.pos, drop)
    local loaded = dist2(drop, unload)
    local returnHome = dist2(unload, base)
    local moveDrain = amrConfig('battery_move_drain_pct_per_m', 2.2)
    local loadDrain = amrConfig('battery_load_extra_pct_per_m', 0.9)
    return (unloaded + loaded + returnHome) * moveDrain + loaded * loadDrain
end

local function assignmentCost(entry, boxEntry)
    local low = amrConfig('battery_low_pct', 28.0)
    local drop = pickupCenter(boxEntry, 0.18)
    local unload = targetCenter(boxEntry, 0.18)
    local base = zoneCenter(entry.spec.base, 0.18)
    local travel = dist2(entry.pos, drop) + dist2(drop, unload)
    local home = dist2(unload, base)
    local energy = assignmentEnergy(entry, boxEntry)
    if entry.battery - energy < low then return 1.0e9 end
    return travel + home * 0.35 + (100.0 - entry.battery) * 0.035
end

local function publishAssignmentStats(assignments, policy)
    local totalCost = 0.0
    for _, item in ipairs(assignments or {}) do
        local entry = robots[item[1]]
        local boxEntry = boxes[item[2]]
        if entry and boxEntry then totalCost = totalCost + assignmentCost(entry, boxEntry) end
    end
    pcall(sim.setNamedStringParam, 'sp0_dispatch_policy', policy)
    pcall(sim.setNamedFloatParam, 'sp0_dispatch_cost', totalCost)
    pcall(sim.setNamedInt32Param, 'sp0_dispatch_assignments', #(assignments or {}))
end

local function hungarianAssign(candidateNames, jobNames)
    local best = {}
    local bestCount = -1
    local bestCost = 1.0e18
    local used = {}
    local current = {}
    local function copyCurrent()
        local out = {}
        for i, item in ipairs(current) do out[i] = {item[1], item[2]} end
        return out
    end
    local function rec(jobIndex, assignedCount, cost)
        if jobIndex > #jobNames or assignedCount == #candidateNames then
            if assignedCount > bestCount or (assignedCount == bestCount and cost < bestCost) then
                bestCount = assignedCount
                bestCost = cost
                best = copyCurrent()
            end
            return
        end
        rec(jobIndex + 1, assignedCount, cost)
        local boxEntry = boxes[jobNames[jobIndex]]
        for _, robotName in ipairs(candidateNames) do
            if not used[robotName] then
                local entry = robots[robotName]
                local c = assignmentCost(entry, boxEntry)
                if c < 1.0e8 then
                    used[robotName] = true
                    current[#current + 1] = {robotName, jobNames[jobIndex]}
                    rec(jobIndex + 1, assignedCount + 1, cost + c)
                    current[#current] = nil
                    used[robotName] = false
                end
            end
        end
    end
    rec(1, 0, 0.0)
    pcall(sim.setNamedFloatParam, 'sp0_hungarian_cost', bestCost < 1.0e17 and bestCost or -1.0)
    pcall(sim.setNamedInt32Param, 'sp0_hungarian_assignments', bestCount)
    return best
end

local function greedyAssign(candidateNames, jobNames)
    local pairs = {}
    for _, robotName in ipairs(candidateNames) do
        for _, boxName in ipairs(jobNames) do
            local c = assignmentCost(robots[robotName], boxes[boxName])
            if c < 1.0e8 then
                pairs[#pairs + 1] = {robotName, boxName, c}
            end
        end
    end
    table.sort(pairs, function(a, b) return a[3] < b[3] end)
    local usedRobots = {}
    local usedJobs = {}
    local out = {}
    for _, item in ipairs(pairs) do
        if not usedRobots[item[1]] and not usedJobs[item[2]] then
            usedRobots[item[1]] = true
            usedJobs[item[2]] = true
            out[#out + 1] = {item[1], item[2]}
        end
    end
    return out
end

local function replicatorAssign(candidateNames, jobNames)
    local weights = {}
    local utilities = {}
    for _, robotName in ipairs(candidateNames) do
        weights[robotName] = {}
        utilities[robotName] = {}
        local feasible = 0
        for _, boxName in ipairs(jobNames) do
            local c = assignmentCost(robots[robotName], boxes[boxName])
            local u = c < 1.0e8 and 1.0 / (1.0 + c) or 0.0
            utilities[robotName][boxName] = u
            if u > 0.0 then feasible = feasible + 1 end
        end
        for _, boxName in ipairs(jobNames) do
            weights[robotName][boxName] = feasible > 0 and utilities[robotName][boxName] > 0.0 and 1.0 / feasible or 0.0
        end
    end
    for _ = 1, 18 do
        local demand = {}
        for _, boxName in ipairs(jobNames) do demand[boxName] = 0.0 end
        for _, robotName in ipairs(candidateNames) do
            for _, boxName in ipairs(jobNames) do
                demand[boxName] = demand[boxName] + (weights[robotName][boxName] or 0.0)
            end
        end
        for _, robotName in ipairs(candidateNames) do
            local avg = 0.0
            for _, boxName in ipairs(jobNames) do
                local pressure = 1.0 / (1.0 + math.max(0.0, demand[boxName] - 1.0))
                avg = avg + (weights[robotName][boxName] or 0.0) * (utilities[robotName][boxName] or 0.0) * pressure
            end
            local denom = 0.0
            local nextWeights = {}
            for _, boxName in ipairs(jobNames) do
                local pressure = 1.0 / (1.0 + math.max(0.0, demand[boxName] - 1.0))
                local fitness = (utilities[robotName][boxName] or 0.0) * pressure
                local w = math.max(0.0, (weights[robotName][boxName] or 0.0) * (1.0 + 1.15 * (fitness - avg)))
                nextWeights[boxName] = w
                denom = denom + w
            end
            if denom > 0.0 then
                for _, boxName in ipairs(jobNames) do weights[robotName][boxName] = nextWeights[boxName] / denom end
            end
        end
    end
    local pairs = {}
    for _, robotName in ipairs(candidateNames) do
        for _, boxName in ipairs(jobNames) do
            local score = (weights[robotName][boxName] or 0.0) * (utilities[robotName][boxName] or 0.0)
            if score > 0.0 then pairs[#pairs + 1] = {robotName, boxName, score} end
        end
    end
    table.sort(pairs, function(a, b) return a[3] > b[3] end)
    local usedRobots = {}
    local usedJobs = {}
    local out = {}
    for _, item in ipairs(pairs) do
        if not usedRobots[item[1]] and not usedJobs[item[2]] then
            usedRobots[item[1]] = true
            usedJobs[item[2]] = true
            out[#out + 1] = {item[1], item[2]}
        end
    end
    return out
end

local function assignJobs(t)
    if t - lastAssignmentT < scaledDuration(0.75) then return end
    lastAssignmentT = t
    local candidateNames = {}
    local low = amrConfig('battery_low_pct', 28.0)
    for _, name in ipairs(robotOrder) do
        local entry = robots[name]
        if entry and entry.state == 'idle' and t >= entry.releaseDelay and entry.battery > low then
            candidateNames[#candidateNames + 1] = name
        end
    end
    local jobNames = {}
    for _, boxName in ipairs(boxOrder) do
        local b = boxes[boxName]
        if b and b.state == 'cooldown' and t >= b.respawnAt then
            b.state = 'waiting'
            advanceBoxTarget(b)
        end
        if b and b.state == 'waiting' and not b.assignedRobot and t >= b.respawnAt then
            jobNames[#jobNames + 1] = boxName
        end
    end
    local policy = readPolicy()
    local assignments = {}
    if policy == 'distributed_greedy' then
        assignments = greedyAssign(candidateNames, jobNames)
    elseif policy == 'replicator_distributed' then
        assignments = replicatorAssign(candidateNames, jobNames)
    else
        policy = 'hungarian_centralized'
        assignments = hungarianAssign(candidateNames, jobNames)
    end
    publishAssignmentStats(assignments, policy)
    for _, item in ipairs(assignments) do
        local robotName, boxName = item[1], item[2]
        local entry = robots[robotName]
        local b = boxes[boxName]
        if entry and b and entry.state == 'idle' and b.state == 'waiting' then
            entry.assignedBox = boxName
            entry.state = 'to_box'
            entry.stateStart = t
            b.state = 'assigned'
            b.assignedRobot = robotName
        end
    end
end

local function updateSafetyFootprint(entry)
    if not entry.footprint then return end
    local hard = amrConfig('hard_clearance_m', 0.62)
    local avoid = amrConfig('avoidance_radius_m', 1.05)
    local color = {0.08, 0.50, 0.88}
    if entry.minDistance < hard then
        color = {0.90, 0.12, 0.10}
    elseif entry.minDistance < avoid then
        color = {0.95, 0.70, 0.12}
    end
    pcall(sim.setShapeColor, entry.footprint, nil, sim.colorcomponent_ambient_diffuse, color)
end

local function computeVelocity(name, entry)
    local maxSpeed = amrConfig('max_speed_mps', 0.55) * simScale()
    local avoid = amrConfig('avoidance_radius_m', 1.05)
    local hard = amrConfig('hard_clearance_m', 0.62)
    entry.minDistance = 99.0
    if entry.state == 'idle' or entry.state == 'pickup_wait' or entry.state == 'unload_wait' or entry.state == 'charging' then
        return 0.0, 0.0
    end
    local t = sim.getSimulationTime()
    if t < entry.releaseDelay then return 0.0, 0.0 end
    local target = targetFor(entry)
    local dx = target[1] - entry.pos[1]
    local dy = target[2] - entry.pos[2]
    local d = math.sqrt(dx * dx + dy * dy)
    local vx = 0.0
    local vy = 0.0
    if d > 0.001 then
        local speed = maxSpeed * clamp(d / 0.90, 0.20, 1.0)
        vx = dx / d * speed
        vy = dy / d * speed
    end
    for _, otherName in ipairs(robotOrder) do
        if otherName ~= name then
            local other = robots[otherName]
            if other then
                local ox = entry.pos[1] - other.pos[1]
                local oy = entry.pos[2] - other.pos[2]
                local od = math.sqrt(ox * ox + oy * oy)
                if od > 0.001 then
                    entry.minDistance = math.min(entry.minDistance, od)
                    if od < avoid then
                        local strength = ((avoid - od) / avoid) ^ 2 * maxSpeed * 1.65
                        vx = vx + ox / od * strength
                        vy = vy + oy / od * strength
                    end
                    if od < hard and name > otherName then
                        vx = vx * 0.10
                        vy = vy * 0.10
                    end
                end
            end
        end
    end
    local speed = math.sqrt(vx * vx + vy * vy)
    if speed > maxSpeed then
        vx = vx / speed * maxSpeed
        vy = vy / speed * maxSpeed
    end
    return vx, vy
end

local function moveEntry(entry, vx, vy, dt)
    local oldX, oldY = entry.pos[1], entry.pos[2]
    local hx = scene.dimensions_m.width / 2.0 - 0.55
    local hy = scene.dimensions_m.depth / 2.0 - 0.55
    entry.pos[1] = clamp(entry.pos[1] + vx * dt, -hx, hx)
    entry.pos[2] = clamp(entry.pos[2] + vy * dt, -hy, hy)
    local speed = math.sqrt(vx * vx + vy * vy)
    if speed > 0.015 then
        entry.yaw = atan2(vy, vx)
    else
        local target = targetFor(entry)
        if dist2(entry.pos, target) > 0.05 then
            entry.yaw = yawTo(entry.pos, target)
        end
    end
    pcall(sim.setObjectPosition, entry.handle, -1, {entry.pos[1], entry.pos[2], entry.pos[3]})
    pcall(sim.setObjectOrientation, entry.handle, -1, {0, 0, entry.yaw})
    return math.sqrt((entry.pos[1] - oldX) * (entry.pos[1] - oldX) + (entry.pos[2] - oldY) * (entry.pos[2] - oldY))
end

local function updateBattery(entry, distance, dt)
    if entry.state == 'charging' then
        entry.battery = clamp(entry.battery + amrConfig('battery_charge_pct_per_s', 7.5) * dt, 0.0, 100.0)
    else
        local drain = amrConfig('battery_idle_drain_pct_per_s', 0.015) * dt
        drain = drain + distance * amrConfig('battery_move_drain_pct_per_m', 2.2)
        if entry.carrying then
            drain = drain + distance * amrConfig('battery_load_extra_pct_per_m', 0.9)
        end
        entry.battery = clamp(entry.battery - drain, 0.0, 100.0)
    end
    updateBatteryVisual(entry)
end

local function updateBox(boxEntry, t)
    local box = boxEntry.handle
    local boxHeight = boxEntry.spec.size[3]
    local drop = pickupCenter(boxEntry, 0.18)
    local unload = targetCenter(boxEntry, 0.18)
    local pos = {drop[1], drop[2], scene.drop_height_m + boxHeight}
    local yaw = 0.0
    local visible = boxEntry.state ~= 'cooldown'
    if boxEntry.state == 'pickup_wait' then
        visible = true
        local u = progress(boxEntry, t)
        pos = {drop[1], drop[2], scene.drop_height_m + (scene.carry_height_m - scene.drop_height_m) * u}
    elseif boxEntry.state == 'carrying' and boxEntry.carrier and robots[boxEntry.carrier] then
        visible = true
        local carrier = robots[boxEntry.carrier]
        pos = {carrier.pos[1], carrier.pos[2], scene.carry_height_m}
        yaw = carrier.yaw
    elseif boxEntry.state == 'unload_wait' then
        visible = true
        local u = progress(boxEntry, t)
        pos = {unload[1], unload[2], scene.carry_height_m + (scene.suction_height_m - scene.carry_height_m) * u}
    end
    setBoxVisible(box, visible)
    pcall(sim.setObjectPosition, box, -1, pos)
    pcall(sim.setObjectOrientation, box, -1, {0, 0, yaw})
    updateBoxTargetVisual(boxEntry)
end

function sysCall_actuation()
    local t = sim.getSimulationTime()
    local dt = t - lastT
    if dt <= 0.0 then dt = 0.05 end
    dt = clamp(dt, 0.01, 0.12)
    lastT = t
    for _, name in ipairs(robotOrder) do
        local entry = robots[name]
        if entry then updateMission(entry, t) end
    end
    assignJobs(t)
    local velocities = {}
    globalMinDistance = 99.0
    for _, name in ipairs(robotOrder) do
        local entry = robots[name]
        if entry then
            local vx, vy = computeVelocity(name, entry)
            velocities[name] = {vx, vy}
            globalMinDistance = math.min(globalMinDistance, entry.minDistance)
        end
    end
    for _, name in ipairs(robotOrder) do
        local entry = robots[name]
        if entry then
            local v = velocities[name] or {0.0, 0.0}
            local distance = moveEntry(entry, v[1], v[2], dt)
            updateBattery(entry, distance, dt)
            updateSafetyFootprint(entry)
        end
    end
    for _, boxName in ipairs(boxOrder) do
        local boxEntry = boxes[boxName]
        if boxEntry then updateBox(boxEntry, t) end
    end
    pcall(sim.setNamedFloatParam, 'sp0_min_robot_distance_m', globalMinDistance)
    pcall(sim.setNamedInt32Param, 'sp0_collision_warning', globalMinDistance < amrConfig('hard_clearance_m', 0.62) and 1 or 0)
end
""".replace("__SCENE__", scene_lua)


def render_lua_scene(scene: dict[str, Any]) -> str:
    json_blob = json.dumps(scene, indent=2)
    lua_scene = lua_table(scene)
    demo_script = render_demo_script(scene)
    template = """-- Auto-generated by scripts/coppelia/build_sp0_corners_scene.py
-- Scenario: __SCENARIO__
-- Usage:
--   1. Open CoppeliaSim.
--   2. Run: dofile([[__LUA_PATH__]])

local scene = __SCENE__

local function setAlias(handle, name)
    if handle and handle >= 0 then pcall(sim.setObjectAlias, handle, name, 1) end
    return handle
end

local function setPhysics(handle, static, respondable, mass)
    pcall(sim.setObjectInt32Param, handle, sim.shapeintparam_static, static and 1 or 0)
    pcall(sim.setObjectInt32Param, handle, sim.shapeintparam_respondable, respondable and 1 or 0)
    pcall(sim.setObjectFloatParam, handle, sim.shapefloatparam_mass, mass or 0.001)
    pcall(sim.setObjectInt32Param, handle, sim.shapeintparam_edge_visibility, 1)
end

local function setAlpha(handle, alpha)
    local transparency = 1.0 - math.max(0.0, math.min(1.0, alpha or 1.0))
    if sim.colorcomponent_transparency then
        pcall(sim.setShapeColor, handle, nil, sim.colorcomponent_transparency, {transparency})
    end
    if sim.shapefloatparam_transparency then
        pcall(sim.setObjectFloatParam, handle, sim.shapefloatparam_transparency, transparency)
    end
end

local function box(name, size, pos, color, yaw, static, respondable, mass)
    local h = sim.createPrimitiveShape(sim.primitiveshape_cuboid, size, 0)
    setAlias(h, name)
    sim.setObjectPosition(h, -1, pos)
    sim.setObjectOrientation(h, -1, {0, 0, yaw or 0})
    sim.setShapeColor(h, nil, sim.colorcomponent_ambient_diffuse, color)
    setPhysics(h, static ~= false, respondable ~= false, mass or 0.001)
    return h
end

local function cylinder(name, radius, height, pos, color, static, respondable, mass, alpha)
    local h = sim.createPrimitiveShape(sim.primitiveshape_cylinder, {radius * 2, radius * 2, height}, 0)
    setAlias(h, name)
    sim.setObjectPosition(h, -1, pos)
    sim.setShapeColor(h, nil, sim.colorcomponent_ambient_diffuse, color)
    setAlpha(h, alpha or 1.0)
    setPhysics(h, static ~= false, respondable == true, mass or 0.001)
    return h
end

local function clamp(value, low, high)
    if value < low then return low end
    if value > high then return high end
    return value
end

local function batteryColor(batteryPct)
    local step = math.floor(clamp(batteryPct, 0.0, 100.0) / 100.0 * 9.0 + 0.5) + 1
    local t = (step - 1) / 9.0
    return {
        0.90 * (1.0 - t) + 0.12 * t,
        0.10 * (1.0 - t) + 0.88 * t,
        0.08 * (1.0 - t) + 0.16 * t
    }
end

local function addRingSegments(prefix, center, radius, segmentCount, color)
    local handles = {}
    local arc = math.max(0.16, (2.0 * math.pi * radius / segmentCount) * 0.58)
    for i = 1, segmentCount do
        local theta = (2.0 * math.pi * (i - 1)) / segmentCount
        local x = center[1] + math.cos(theta) * radius
        local y = center[2] + math.sin(theta) * radius
        handles[#handles + 1] = box(string.format('%s_%02d', prefix, i), {arc, 0.025, 0.018}, {x, y, center[3]}, color, theta + math.pi / 2.0, true, false)
    end
    return handles
end

local function disableModelScripts(handle)
    local scriptTypes = {sim.scripttype_simulation, sim.scripttype_customization, sim.scripttype_childscript, sim.scripttype_customizationscript}
    for _, obj in ipairs(sim.getObjectsInTree(handle, sim.handle_all, 0)) do
        for _, scriptType in ipairs(scriptTypes) do
            if scriptType then
                local ok, script = pcall(sim.getScript, scriptType, obj)
                if ok and script and script >= 0 then pcall(sim.removeObjects, {script}) end
            end
        end
    end
end

local function makeModelVisualOnly(handle)
    for _, child in ipairs(sim.getObjectsInTree(handle, sim.handle_all, 0)) do
        if sim.getObjectType(child) == sim.object_shape_type then
            pcall(sim.setObjectInt32Param, child, sim.shapeintparam_static, 1)
            pcall(sim.setObjectInt32Param, child, sim.shapeintparam_respondable, 0)
        end
    end
end

local function addPioneer(spec)
    local ok, handle = pcall(sim.loadModel, scene.model_paths.pioneer_p3dx)
    if ok and handle and handle >= 0 then
        disableModelScripts(handle)
        makeModelVisualOnly(handle)
    else
        handle = cylinder(spec.name .. '_fallback', 0.26, 0.25, spec.position, {0.12, 0.12, 0.12})
    end
    setAlias(handle, spec.name)
    sim.setObjectPosition(handle, -1, spec.position)
    sim.setObjectOrientation(handle, -1, {0, 0, spec.heading_rad})
    local plate = box(spec.name .. '_cargo_plate', {0.40, 0.32, 0.035}, {spec.position[1], spec.position[2], spec.position[3] + 0.30}, {0.08, 0.12, 0.16}, 0, true, false)
    pcall(sim.setObjectParent, plate, handle, true)
    local footprint = cylinder(spec.name .. '_safety_footprint', 0.46, 0.012, {spec.position[1], spec.position[2], 0.035}, {0.08, 0.50, 0.88}, true, true, 0.1)
    pcall(sim.setObjectParent, footprint, handle, true)
    local ringColor = batteryColor(spec.battery_initial_pct or 100.0)
    local sensorFill = cylinder(spec.name .. '_sensor_fill', scene.amr.sensor_radius_m, 0.006, {spec.position[1], spec.position[2], 0.044}, ringColor, true, false, 0.001, scene.amr.sensor_fill_alpha or 0.70)
    pcall(sim.setObjectParent, sensorFill, handle, true)
    local sensorRing = addRingSegments(spec.name .. '_sensor_radius', {spec.position[1], spec.position[2], 0.052}, scene.amr.sensor_radius_m, 24, ringColor)
    for _, ring in ipairs(sensorRing) do pcall(sim.setObjectParent, ring, handle, true) end
    local commRing = addRingSegments(spec.name .. '_comm_radius', {spec.position[1], spec.position[2], 0.072}, scene.amr.comm_radius_m, 24, ringColor)
    for _, ring in ipairs(commRing) do pcall(sim.setObjectParent, ring, handle, true) end
end

local function clearScene()
    local ok, didCreateNew = pcall(function()
        if sim.newScene then
            sim.newScene()
            return true
        end
        if sim.createNewScene then
            sim.createNewScene()
            return true
        end
        return false
    end)
    if ok and didCreateNew then return end
    local objects = sim.getObjectsInTree(sim.handle_scene, sim.handle_all, 0)
    local removable = {}
    for _, object in ipairs(objects) do
        local okType, objectType = pcall(sim.getObjectType, object)
        if not (okType and (objectType == sim.object_camera_type or objectType == sim.object_light_type)) then
            removable[#removable + 1] = object
        end
    end
    if #removable > 0 then sim.removeObjects(removable) end
end

clearScene()
setAlias(sim.createDummy(0.04), 'SP0_CORNERS_DROP_SUCTION_ROOT')
local floorW = scene.dimensions_m.width
local floorD = scene.dimensions_m.depth
box('SP0_floor', {floorW, floorD, 0.05}, {0, 0, -0.025}, {0.46, 0.47, 0.46}, 0, true, true)
box('SP0_boundary_north', {floorW, 0.045, 0.08}, {0, floorD / 2, 0.04}, {0.08, 0.08, 0.08}, 0, true, true)
box('SP0_boundary_south', {floorW, 0.045, 0.08}, {0, -floorD / 2, 0.04}, {0.08, 0.08, 0.08}, 0, true, true)
box('SP0_boundary_east', {0.045, floorD, 0.08}, {floorW / 2, 0, 0.04}, {0.08, 0.08, 0.08}, 0, true, true)
box('SP0_boundary_west', {0.045, floorD, 0.08}, {-floorW / 2, 0, 0.04}, {0.08, 0.08, 0.08}, 0, true, true)

for _, z in ipairs(scene.zones) do
    local x, y, zz = z.center[1], z.center[2], z.center[3]
    local sx, sy, sz = z.size[1], z.size[2], z.size[3]
    box(z.name .. '_pad', z.size, z.center, z.color, 0, true, false)
    box(z.name .. '_north', {sx, 0.035, 0.035}, {x, y + sy / 2, zz + 0.012}, z.color, 0, true, false)
    box(z.name .. '_south', {sx, 0.035, 0.035}, {x, y - sy / 2, zz + 0.012}, z.color, 0, true, false)
    box(z.name .. '_east', {0.035, sy, 0.035}, {x + sx / 2, y, zz + 0.012}, z.color, 0, true, false)
    box(z.name .. '_west', {0.035, sy, 0.035}, {x - sx / 2, y, zz + 0.012}, z.color, 0, true, false)
    if z.kind == 'drop' then
        for idx, p in ipairs({{-0.35, -0.35}, {-0.35, 0.35}, {0.35, -0.35}, {0.35, 0.35}}) do
            box(z.name .. '_chute_post_' .. idx, {0.055, 0.055, scene.drop_height_m}, {x + p[1], y + p[2], scene.drop_height_m / 2}, {0.12, 0.12, 0.11}, 0, true, false)
        end
        box(z.name .. '_chute_top', {0.82, 0.82, 0.12}, {x, y, scene.drop_height_m + 0.08}, {0.90, 0.63, 0.08}, 0, true, false)
    elseif z.kind == 'unload' then
        cylinder(z.name .. '_suction_pipe', 0.16, 1.55, {x, y, 2.50}, {0.20, 0.62, 0.88}, true, false)
        cylinder(z.name .. '_suction_beacon', 0.28, 0.16, {x, y, 3.36}, {0.32, 0.80, 1.00}, true, false)
        for idx, radius in ipairs({0.38, 0.52, 0.66}) do
            cylinder(string.format('%s_suction_ring_%d', z.name, idx), radius, 0.025, {x, y, 0.16 + idx * 0.16}, {0.16, 0.68, 0.36}, true, false)
        end
    end
end

box('SP0_counter_panel', {3.0, 0.10, 1.0}, {0.0, -4.35, 0.55}, {0.12, 0.13, 0.14}, 0, true, false)
for i = 1, 48 do
    local col = (i - 1) % 12
    local row = math.floor((i - 1) / 12)
    box(string.format('SP0_count_tick_%02d', i), {0.16, 0.035, 0.16}, {-1.32 + col * 0.24, -4.42, 0.25 + row * 0.26}, {0.22, 0.24, 0.25}, 0, true, false)
end

for _, r in ipairs(scene.robots) do addPioneer(r) end
local zoneMap = {}
for _, z in ipairs(scene.zones) do zoneMap[z.name] = z end
for _, b in ipairs(scene.boxes) do
    local z = zoneMap[b.drop]
    local offset = b.slot_offset or {0.0, 0.0}
    local px = z.center[1] + offset[1]
    local py = z.center[2] + offset[2]
    local h = box(b.name, b.size, {px, py, scene.drop_height_m + b.size[3]}, {0.68, 0.50, 0.28}, 0, true, false, b.mass_kg)
    local label = box(b.name .. '_label', {0.18, 0.012, 0.08}, {px, py, scene.drop_height_m + b.size[3] + 0.02}, {0.90, 0.90, 0.80}, 0, true, false)
    pcall(sim.setObjectParent, label, h, true)
end

local ortho = math.max(scene.dimensions_m.width, scene.dimensions_m.depth) + 1.8
local top = sim.createVisionSensor(1 + 4, {1280, 960, 0, 0}, {0.05, 40.0, ortho, 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0})
setAlias(top, 'SP0_camera_top')
sim.setExplicitHandling(top, 1)
pcall(sim.setObjectInt32Param, top, sim.visionintparam_perspective_operation, 0)
pcall(sim.setObjectFloatParam, top, sim.visionfloatparam_ortho_size, ortho)
sim.setObjectPosition(top, -1, {0, 0, 12.5})
sim.setObjectOrientation(top, -1, {0, math.pi, 0})
pcall(function()
    local cameras = sim.getObjectsInTree(sim.handle_scene, sim.object_camera_type, 0)
    local camera = cameras[1]
    setAlias(camera, 'DefaultCamera')
    pcall(sim.cameraFitToView, camera + sim.handleflag_camera, nil, 0, 1.20)
    pcall(sim.adjustView, 0, camera, 0, 'SP0 default view')
    pcall(sim.cameraFitToView, 0, nil, 0, 1.20)
end)
pcall(function()
    local lights = sim.getObjectsInTree(sim.handle_scene, sim.object_light_type, 0)
    local light = lights[1]
    setAlias(light, 'DefaultLight')
    sim.setObjectPosition(light, -1, {1.5, -2.5, 7.0})
end)

local scriptText = [==[__DEMO_SCRIPT__]==]
local dummy = setAlias(sim.createDummy(0.035), 'SP0_demo_controller')
if sim.getBoolParam(sim.boolparam_usingscriptobjects) then
    local s = sim.createScript(sim.scripttype_simulation, scriptText, 0, 'lua')
    sim.setObjectParent(s, dummy)
else
    local s = sim.addScript(sim.scripttype_simulation)
    sim.associateScriptWithObject(s, dummy)
    sim.setScriptText(s, scriptText)
end
sim.setNamedStringParam('sp0_corners_scene_json', [==[__JSON__]==])
"""
    return (
        template.replace("__SCENARIO__", scene["scenario"])
        .replace("__LUA_PATH__", str((ROOT / "coppeliasim/real_scenes/sp0_corners_drop_suction_pioneer.lua").resolve()))
        .replace("__SCENE__", lua_scene)
        .replace("__DEMO_SCRIPT__", demo_script)
        .replace("__JSON__", json_blob)
    )


def load_model(sim, model_path: str) -> int | None:
    path = Path(model_path)
    if not path.exists():
        return None
    try:
        handle = sim.loadModel(str(path))
    except Exception:
        return None
    return handle if isinstance(handle, int) and handle >= 0 else None


def disable_model_scripts(sim, handle: int) -> None:
    script_types = []
    for attr in ("scripttype_simulation", "scripttype_customization", "scripttype_childscript", "scripttype_customizationscript"):
        try:
            script_types.append(getattr(sim, attr))
        except Exception:
            pass
    for obj in sim.getObjectsInTree(handle, sim.handle_all, 0):
        for script_type in script_types:
            try:
                script = sim.getScript(script_type, obj)
                if isinstance(script, int) and script >= 0:
                    sim.removeObjects([script])
            except Exception:
                pass


def make_model_visual_only(sim, handle: int) -> None:
    for child in sim.getObjectsInTree(handle, sim.handle_all, 0):
        try:
            if sim.getObjectType(child) != sim.object_shape_type:
                continue
            props = sim.getObjectSpecialProperty(child)
            renderable = getattr(sim, "objectspecialproperty_renderable", 0x0200)
            collidable = getattr(sim, "objectspecialproperty_collidable", 0x0001)
            sim.setObjectSpecialProperty(child, (props | renderable) & ~collidable)
            sim.setObjectInt32Param(child, sim.shapeintparam_static, 1)
            sim.setObjectInt32Param(child, sim.shapeintparam_respondable, 0)
        except Exception:
            pass


def add_box(sim, spec: BoxSpec) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cuboid, list(spec.size), 0)
    set_alias(sim, handle, spec.name)
    sim.setObjectPosition(handle, -1, list(spec.center))
    sim.setObjectOrientation(handle, -1, [0.0, 0.0, spec.yaw_rad])
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, list(spec.color))
    set_shape_physics(sim, handle, spec.static, spec.respondable, spec.mass_kg)
    set_shape_render_props(sim, handle)
    return handle


def add_cylinder(
    sim,
    name: str,
    radius: float,
    height: float,
    position: tuple[float, float, float],
    color: tuple[float, float, float],
    static: bool = True,
    respondable: bool = False,
    mass_kg: float = 0.001,
    alpha: float = 1.0,
) -> int:
    handle = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [radius * 2.0, radius * 2.0, height], 0)
    set_alias(sim, handle, name)
    sim.setObjectPosition(handle, -1, list(position))
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, list(color))
    set_shape_alpha(sim, handle, alpha)
    set_shape_physics(sim, handle, static, respondable, mass_kg)
    set_shape_render_props(sim, handle)
    return handle


def set_shape_alpha(sim, handle: int, alpha: float) -> None:
    alpha = max(0.0, min(1.0, float(alpha)))
    transparency = 1.0 - alpha
    try:
        component = getattr(sim, "colorcomponent_transparency")
        sim.setShapeColor(handle, None, component, [transparency])
    except Exception:
        pass
    try:
        param = getattr(sim, "shapefloatparam_transparency")
        sim.setObjectFloatParam(handle, param, transparency)
    except Exception:
        pass


def set_shape_physics(sim, handle: int, static: bool, respondable: bool, mass_kg: float) -> None:
    for param, value in (
        ("shapeintparam_static", 1 if static else 0),
        ("shapeintparam_respondable", 1 if respondable else 0),
    ):
        try:
            sim.setObjectInt32Param(handle, getattr(sim, param), value)
        except Exception:
            pass
    try:
        sim.setObjectFloatParam(handle, sim.shapefloatparam_mass, max(float(mass_kg), 0.0))
    except Exception:
        pass


def set_shape_render_props(sim, handle: int) -> None:
    try:
        sim.setObjectInt32Param(handle, sim.shapeintparam_edge_visibility, 1)
    except Exception:
        pass


def set_alias(sim, handle: int, name: str) -> None:
    try:
        sim.setObjectAlias(handle, name, 1)
    except Exception:
        pass


def write_scene_metadata(sim, scene: dict[str, Any]) -> None:
    payload = json.dumps(scene, indent=2)
    try:
        sim.setNamedStringParam("sp0_corners_scene_json", payload)
    except Exception:
        pass
    try:
        sim.writeCustomStringData(sim.handle_scene, "SP0_CORNERS_DROP_SUCTION", payload)
    except Exception:
        pass


def capture_camera_snapshot(sim, sensor_alias: str, path: Path) -> dict[str, str]:
    try:
        import imageio.v2 as imageio
        import numpy as np

        sensor = sim.getObject(sensor_alias)
        sim.handleVisionSensor(sensor)
        img, resolution = sim.getVisionSensorImg(sensor)
        data = np.frombuffer(img, dtype=np.uint8)
        width, height = int(resolution[0]), int(resolution[1])
        if data.size != width * height * 3:
            return {"path": "", "nonzero_ratio": ""}
        frame = np.flipud(data.reshape((height, width, 3)))
        path.parent.mkdir(parents=True, exist_ok=True)
        imageio.imwrite(path, frame)
        metrics = {
            "path": rel(path),
            "sensor": sensor_alias,
            "resolution": f"{width}x{height}",
            "mean_rgb": [round(float(v), 3) for v in frame.mean(axis=(0, 1))],
            "nonzero_ratio": f"{float(np.count_nonzero(frame) / frame.size):.6f}",
        }
        path.with_suffix(".json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return {"path": metrics["path"], "nonzero_ratio": metrics["nonzero_ratio"]}
    except Exception:
        return {"path": "", "nonzero_ratio": ""}


def launch_coppelia_headless(coppelia: Path, port: int, log_path: Path) -> subprocess.Popen[Any]:
    if not coppelia.exists():
        raise FileNotFoundError(f"CoppeliaSim executable not found: {coppelia}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8", errors="replace")
    args = [
        str(coppelia),
        "-h",
        f"-GzmqRemoteApi.rpcPort={port}",
    ]
    return subprocess.Popen(
        args,
        cwd=str(coppelia.parent),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )


def stop_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


def connect(port: int):
    if not CLIENT_DIR.exists():
        raise FileNotFoundError(f"CoppeliaSim ZMQ client not found: {CLIENT_DIR}")
    sys.path.insert(0, str(CLIENT_DIR))
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    deadline = time.time() + 12.0
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            client = RemoteAPIClient(port=port)
            client.initialTimeout = 1
            sim = client.require("sim")
            sim.getSimulationState()
            return sim
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"Could not connect to CoppeliaSim ZMQ on port {port}: {last_error!r}")


def stop_if_running(sim) -> None:
    if sim.getSimulationState() != sim.simulation_stopped:
        sim.stopSimulation()
        deadline = time.time() + 10.0
        while sim.getSimulationState() != sim.simulation_stopped and time.time() < deadline:
            time.sleep(0.1)


def lua_table(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{key} = {lua_table(item)}" for key, item in value.items()]
        return "{\n" + ",\n".join(parts) + "\n}"
    if isinstance(value, list):
        return "{" + ", ".join(lua_table(item) for item in value) + "}"
    if isinstance(value, tuple):
        return "{" + ", ".join(lua_table(item) for item in value) + "}"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "nil"
    return repr(value)


def write_manifest(path: Path, row: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
