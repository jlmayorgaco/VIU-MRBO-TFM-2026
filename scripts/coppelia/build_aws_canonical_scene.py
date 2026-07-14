"""Build the canonical cooperative-transport warehouse scene on top of AWS.

The script keeps the AWS RoboMaker warehouse as the base scene, then adds a
small 12 m x 10 m canonical overlay for the TFM scenario:

* initial AGV zone
* pickup zones A/B with conveyor + manipulator models
* delivery zones 1/2
* recharge zone
* central obstacle, narrow corridors and suggested routes
* Pioneer P3-DX robots loaded from CoppeliaSim's model library

It always writes auditable YAML/Lua recipes. When a CoppeliaSim ZMQ server is
available, it also exports a real .ttt file.
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
AWS_SCENE = COPPELIA_ROOT / "scenes/awsRobomaker/aws_robomaker_warehouse.ttt"
PIONEER_MODEL = COPPELIA_ROOT / "models/robots/mobile/pioneer p3dx.ttm"
CONVEYOR_MODEL = COPPELIA_ROOT / "models/equipment/conveyors/generic conveyor (rollers).ttm"
MANIPULATOR_MODEL = COPPELIA_ROOT / "models/robots/non-mobile/ABB IRB 140.ttm"
RACK_MODEL = COPPELIA_ROOT / "models/furniture/shelves-cupboards-racks/rack.ttm"
CLIENT_DIR = COPPELIA_ROOT / "programming/zmqRemoteApi/clients/python/src"
COPPELIA_EXE = COPPELIA_ROOT / "coppeliaSim.exe"


@dataclass(frozen=True)
class Zone:
    name: str
    center: tuple[float, float]
    size: tuple[float, float]
    color: tuple[float, float, float]
    kind: str


@dataclass(frozen=True)
class BoxSpec:
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    color: tuple[float, float, float]
    mass_kg: float = 0.1
    yaw_rad: float = 0.0
    static: bool = True
    respondable: bool = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=23000, help="CoppeliaSim ZMQ Remote API port.")
    parser.add_argument("--scene-dir", type=Path, default=ROOT / "coppeliasim/real_scenes")
    parser.add_argument("--out", type=Path, default=ROOT / "results/coppeliasim_validation/aws_canonical")
    parser.add_argument("--aws-scene", type=Path, default=AWS_SCENE)
    parser.add_argument("--coppelia-root", type=Path, default=COPPELIA_ROOT)
    parser.add_argument("--coppelia", type=Path, default=COPPELIA_EXE)
    parser.add_argument("--no-export-ttt", action="store_true")
    parser.add_argument("--launch-coppelia", action="store_true", help="Launch headless CoppeliaSim for the export if no server is already running.")
    parser.add_argument("--restore-previous", action="store_true", help="Reload the pre-existing CoppeliaSim scene after export.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scene_dir = args.scene_dir.resolve()
    out_dir = args.out.resolve()
    scene_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    scene = build_scene_dict(args.aws_scene.resolve(), args.coppelia_root.resolve())
    validation = validate_layout(scene)
    yaml_path = scene_dir / "aws_canonical_coop_transport_pioneer_p3dx.yaml"
    lua_path = scene_dir / "aws_canonical_coop_transport_pioneer_p3dx.lua"
    ttt_path = scene_dir / "aws_canonical_coop_transport_pioneer_p3dx.ttt"
    manifest_path = out_dir / "manifest.csv"

    yaml_path.write_text(yaml.safe_dump(scene, sort_keys=False, allow_unicode=False), encoding="utf-8")
    lua_path.write_text(render_lua_scene(scene), encoding="utf-8")
    (out_dir / "layout_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )

    export_status = "not_requested" if args.no_export_ttt else "not_started"
    export_error = ""
    object_count = ""
    backup_path = ""
    top_camera = ""
    top_camera_nonzero_ratio = ""
    oblique_camera = ""
    oblique_camera_nonzero_ratio = ""

    if not args.no_export_ttt:
        try:
            result = export_ttt(scene, args.port, ttt_path, args.restore_previous, args.coppelia, args.launch_coppelia)
            export_status = "exported_ttt"
            object_count = str(result["object_count"])
            backup_path = result["backup_path"]
            top_camera = result.get("top_camera", "")
            top_camera_nonzero_ratio = result.get("top_camera_nonzero_ratio", "")
            oblique_camera = result.get("oblique_camera", "")
            oblique_camera_nonzero_ratio = result.get("oblique_camera_nonzero_ratio", "")
        except Exception as exc:  # noqa: BLE001 - manifest should retain actionable failure.
            export_status = "export_failed"
            export_error = repr(exc)

    write_manifest(
        manifest_path,
        {
            "scene": scene["scenario"],
            "base_scene": str(scene["base_scene"]),
            "yaml": rel(yaml_path),
            "lua": rel(lua_path),
            "ttt": rel(ttt_path) if ttt_path.exists() else "",
            "export_status": export_status,
            "export_error": export_error,
            "object_count": object_count,
            "backup_path": backup_path,
            "top_camera": top_camera,
            "top_camera_nonzero_ratio": top_camera_nonzero_ratio,
            "oblique_camera": oblique_camera,
            "oblique_camera_nonzero_ratio": oblique_camera_nonzero_ratio,
            "robots": len(scene["robots"]),
            "zones": len(scene["zones"]),
            "racks": len(scene["racks"]),
            "loads": len(scene["loads"]),
            "layout_status": validation["status"],
            "layout_collisions": validation["collision_count"],
        },
    )
    return 0 if export_status != "export_failed" else 2


def build_scene_dict(aws_scene: Path, coppelia_root: Path) -> dict[str, Any]:
    zones = [
        Zone("zona_inicial_agvs", (-4.55, 3.85), (2.35, 1.55), (0.10, 0.38, 0.82), "initial"),
        Zone("zona_recogida_a", (-4.25, -1.55), (2.50, 1.70), (0.95, 0.70, 0.05), "pickup"),
        Zone("zona_recogida_b", (4.15, 1.45), (2.50, 1.70), (0.48, 0.18, 0.78), "pickup"),
        Zone("zona_entrega_1", (4.25, 3.75), (1.70, 1.20), (0.10, 0.62, 0.30), "delivery"),
        Zone("zona_entrega_2", (4.45, -3.55), (1.70, 1.25), (0.10, 0.62, 0.30), "delivery"),
        Zone("zona_recarga", (-4.55, -3.95), (2.35, 1.25), (0.90, 0.10, 0.10), "recharge"),
    ]
    narrow_corridors = [
        Zone("corredor_estrecho_oeste", (-2.05, -0.55), (1.00, 1.25), (0.95, 0.72, 0.10), "narrow_corridor"),
        Zone("corredor_estrecho_este", (1.95, -0.55), (1.00, 1.25), (0.95, 0.72, 0.10), "narrow_corridor"),
    ]
    robots = [
        {"name": "Pioneer_01_ligero", "position": [-5.15, 4.08, 0.18], "heading_rad": -math.pi / 2, "class": "ligero"},
        {"name": "Pioneer_02_medio", "position": [-4.55, 4.08, 0.18], "heading_rad": -math.pi / 2, "class": "medio"},
        {"name": "Pioneer_03_alta_capacidad", "position": [-3.95, 4.08, 0.18], "heading_rad": -math.pi / 2, "class": "alta_capacidad"},
        {"name": "Pioneer_04_ligero", "position": [-5.15, 3.48, 0.18], "heading_rad": -math.pi / 2, "class": "ligero"},
        {"name": "Pioneer_05_medio", "position": [-4.55, 3.48, 0.18], "heading_rad": -math.pi / 2, "class": "medio"},
        {"name": "Pioneer_06_alta_capacidad", "position": [-3.95, 3.48, 0.18], "heading_rad": -math.pi / 2, "class": "alta_capacidad"},
    ]
    klt_size = [0.40, 0.30, 0.22]
    loads = [
        {
            "name": "klt_a_01_3kg",
            "position": [-4.45, -1.78, 0.84],
            "size": klt_size,
            "weight_kg": 3.0,
            "required_agvs": 1,
            "zone": "A",
            "station": "pickup_a",
            "assigned_amr": "Pioneer_01_ligero",
            "phase_offset_s": 0.0,
            "workflow_load": True,
        },
        {
            "name": "klt_a_02_5kg",
            "position": [-4.00, -1.78, 0.84],
            "size": klt_size,
            "weight_kg": 5.0,
            "required_agvs": 1,
            "zone": "A",
            "station": "pickup_a",
            "assigned_amr": "Pioneer_04_ligero",
            "phase_offset_s": 9.0,
            "workflow_load": True,
        },
        {
            "name": "klt_a_03_2_5kg",
            "position": [-3.55, -1.78, 0.84],
            "size": klt_size,
            "weight_kg": 2.5,
            "required_agvs": 1,
            "zone": "A",
            "station": "pickup_a",
            "assigned_amr": "Pioneer_02_medio",
            "phase_offset_s": 18.0,
            "workflow_load": True,
        },
        {
            "name": "klt_b_01_3kg",
            "position": [4.45, 1.78, 0.84],
            "size": klt_size,
            "weight_kg": 3.0,
            "required_agvs": 1,
            "zone": "B",
            "station": "pickup_b",
            "assigned_amr": "Pioneer_03_alta_capacidad",
            "phase_offset_s": 4.5,
            "workflow_load": True,
        },
        {
            "name": "klt_b_02_4kg",
            "position": [4.00, 1.78, 0.84],
            "size": klt_size,
            "weight_kg": 4.0,
            "required_agvs": 1,
            "zone": "B",
            "station": "pickup_b",
            "assigned_amr": "Pioneer_05_medio",
            "phase_offset_s": 13.5,
            "workflow_load": True,
        },
        {
            "name": "klt_b_03_5kg",
            "position": [3.55, 1.78, 0.84],
            "size": klt_size,
            "weight_kg": 5.0,
            "required_agvs": 1,
            "zone": "B",
            "station": "pickup_b",
            "assigned_amr": "Pioneer_06_alta_capacidad",
            "phase_offset_s": 22.5,
            "workflow_load": True,
        },
    ]
    racks = canonical_racks()
    routes = [
        {"name": "ruta_inicial_a_recogida_a", "points": [(-3.35, 3.05), (-3.00, 2.50), (-3.00, -1.35), (-3.95, -1.05)]},
        {"name": "ruta_inicial_a_recogida_b", "points": [(-3.35, 3.55), (0.00, 3.55), (2.50, 2.45), (2.90, 1.45)]},
        {"name": "ruta_a_interseccion", "points": [(-3.95, -1.05), (-2.05, -0.55), (0.00, -0.55), (1.95, -0.55)]},
        {"name": "ruta_b_entrega_1", "points": [(4.00, 2.35), (4.00, 2.85), (4.25, 3.25)]},
        {"name": "ruta_interseccion_entrega_2", "points": [(1.95, -0.55), (3.00, -0.55), (3.00, -2.30), (4.45, -2.90)]},
        {"name": "ruta_retorno_recarga", "points": [(-2.05, -0.55), (-3.00, -2.65), (-3.40, -3.30), (-4.55, -3.30)]},
    ]
    scene = {
        "scenario": "aws_canonical_coop_transport_pioneer_p3dx",
        "description": "Canonical 12x10 m cooperative multi-AGV transport overlay on AWS RoboMaker warehouse.",
        "base_scene": str(aws_scene),
        "dimensions_m": {"width": 12.0, "depth": 10.0},
        "model_paths": {
            "pioneer_p3dx": str(coppelia_root / "models/robots/mobile/pioneer p3dx.ttm"),
            "conveyor": str(coppelia_root / "models/equipment/conveyors/generic conveyor (rollers).ttm"),
            "table": str(coppelia_root / "models/furniture/tables/high table.ttm"),
            "manipulator": str(coppelia_root / "models/robots/non-mobile/ABB IRB 140.ttm"),
            "rack": str(coppelia_root / "models/furniture/shelves-cupboards-racks/rack.ttm"),
        },
        "zones": [zone_to_dict(z) for z in [*zones, *narrow_corridors]],
        "racks": racks,
        "robots": robots,
        "loads": loads,
        "central_obstacle": {
            "name": "obstaculo_central",
            "position": [0.00, 1.25, 0.35],
            "size": [2.40, 0.80, 0.70],
        },
        "routes": routes,
        "stations": {
            "pickup_a": {
                "conveyor_position": [-4.05, -1.78, 0.0],
                "source_platform_position": [-4.55, -1.78, 0.0],
                "manipulator_position": [-4.65, -1.10, 0.20],
                "pick_position": [-4.20, -1.78, 0.84],
                "handoff_position": [-3.95, -1.05, 0.48],
            },
            "pickup_b": {
                "conveyor_position": [4.05, 1.78, 0.0],
                "source_platform_position": [4.55, 1.78, 0.0],
                "manipulator_position": [4.65, 1.10, 0.20],
                "pick_position": [4.20, 1.78, 0.84],
                "handoff_position": [3.95, 1.05, 0.48],
            },
            "delivery_1_marker": [4.25, 3.75, 0.04],
            "delivery_2_marker": [4.45, -3.55, 0.04],
            "recharge_marker": [-4.55, -3.95, 0.04],
            "footprints": {
                "conveyor": [1.55, 0.55],
                "manipulator": [0.65, 0.65],
            },
        },
        "metadata": {
            "communication": "local radio; heterogeneous transport requests by weight",
            "real_scale_assumptions": {
                "abb_irb_140": {"payload_kg": 6.0, "reach_m": 0.81},
                "pioneer_p3dx": {"length_m": 0.455, "width_m": 0.381, "height_m": 0.237, "payload_kg": 17.0},
                "klt_box": {"length_m": 0.40, "width_m": 0.30, "height_m": 0.22, "max_pick_mass_kg": 5.0},
            },
            "robot_classes": {
                "ligero": {"capacity_kg": 17, "radius_m": 0.27, "max_speed_mps": 1.0},
                "medio": {"capacity_kg": 17, "radius_m": 0.27, "max_speed_mps": 1.0},
                "alta_capacidad": {"capacity_kg": 17, "radius_m": 0.27, "max_speed_mps": 0.8},
            },
            "narrow_corridor_width_m": 1.0,
            "standard_corridor_width_m": 1.5,
            "base_scene_policy": "AWS /warehouse is loaded as provenance but hidden and made non-collidable; the MRBO overlay provides the visible AWS-like warehouse finish on the canonical layout.",
            "visual_quality": "restrained industrial palette, procedural concrete panels, lane markings, detailed rack frames, KLT totes, real CoppeliaSim conveyor models, safety hardware and animated pick-handoff-transport demo script",
        },
        "animation": canonical_animation(),
    }
    return scene


def canonical_animation() -> dict[str, Any]:
    """Small deterministic playback loop embedded in the exported scene."""
    return {
        "cycle_s": 36.0,
        "box_cycle_s": 27.0,
        "manipulator_cycle_s": 9.0,
        "robots": {
            "Pioneer_01_ligero": [
                [-5.15, 4.08, 0.18],
                [-3.35, 3.05, 0.18],
                [-3.95, -1.05, 0.18],
                [-3.95, -1.05, 0.18],
                [-1.20, -0.55, 0.18],
                [3.20, -0.55, 0.18],
                [4.45, -3.00, 0.18],
                [4.45, -3.55, 0.18],
            ],
            "Pioneer_02_medio": [
                [-4.55, 4.08, 0.18],
                [-3.00, 2.50, 0.18],
                [-3.95, -1.05, 0.18],
                [-3.95, -1.05, 0.18],
                [-0.35, -0.55, 0.18],
                [3.00, -0.55, 0.18],
                [4.25, 3.25, 0.18],
                [4.25, 3.75, 0.18],
            ],
            "Pioneer_03_alta_capacidad": [
                [-3.95, 4.08, 0.18],
                [0.00, 3.55, 0.18],
                [2.50, 2.45, 0.18],
                [3.95, 1.05, 0.18],
                [3.95, 1.05, 0.18],
                [4.00, 2.35, 0.18],
                [4.25, 3.75, 0.18],
            ],
            "Pioneer_04_ligero": [
                [-5.15, 3.48, 0.18],
                [-3.00, 2.20, 0.18],
                [-3.95, -1.05, 0.18],
                [-3.95, -1.05, 0.18],
                [-3.00, -2.65, 0.18],
                [-4.55, -3.30, 0.18],
                [-4.55, -3.95, 0.18],
            ],
            "Pioneer_05_medio": [
                [-4.55, 3.48, 0.18],
                [-3.35, 3.55, 0.18],
                [0.00, 3.55, 0.18],
                [3.95, 1.05, 0.18],
                [3.95, 1.05, 0.18],
                [4.15, 1.45, 0.18],
            ],
            "Pioneer_06_alta_capacidad": [
                [-3.95, 3.48, 0.18],
                [3.95, 1.05, 0.18],
                [3.95, 1.05, 0.18],
                [0.00, -0.55, 0.18],
                [1.95, -0.55, 0.18],
                [4.45, -3.55, 0.18],
            ],
        },
        "manipulators": [
            "zona_recogida_a_manipulador_model",
            "zona_recogida_b_manipulador_model",
        ],
    }


def orient_for_landscape_top_camera(scene: dict[str, Any]) -> dict[str, Any]:
    """Mirror the logical Y axis so the 90-degree top camera matches the plan."""

    def flip_point(point: list[float] | tuple[float, ...]) -> list[float]:
        if not isinstance(point, list):
            point = list(point)
        if len(point) >= 2:
            point[1] = -point[1]
        return point

    for zone in scene["zones"]:
        zone["center"] = flip_point(zone["center"])
    for rack in scene["racks"]:
        rack["position"] = flip_point(rack["position"])
        rack["yaw_rad"] = -rack["yaw_rad"]
    for robot in scene["robots"]:
        robot["position"] = flip_point(robot["position"])
        robot["heading_rad"] = -robot["heading_rad"]
    for load in scene["loads"]:
        load["position"] = flip_point(load["position"])
    scene["central_obstacle"]["position"] = flip_point(scene["central_obstacle"]["position"])
    for route in scene["routes"]:
        route["points"] = [flip_point(point) for point in route["points"]]
    for station in ("pickup_a", "pickup_b"):
        scene["stations"][station]["conveyor_position"] = flip_point(scene["stations"][station]["conveyor_position"])
        scene["stations"][station]["source_platform_position"] = flip_point(scene["stations"][station]["source_platform_position"])
        scene["stations"][station]["manipulator_position"] = flip_point(scene["stations"][station]["manipulator_position"])
        scene["stations"][station]["pick_position"] = flip_point(scene["stations"][station]["pick_position"])
        scene["stations"][station]["handoff_position"] = flip_point(scene["stations"][station]["handoff_position"])
    scene["stations"]["delivery_1_marker"] = flip_point(scene["stations"]["delivery_1_marker"])
    scene["stations"]["delivery_2_marker"] = flip_point(scene["stations"]["delivery_2_marker"])
    scene["stations"]["recharge_marker"] = flip_point(scene["stations"]["recharge_marker"])
    return scene


def canonical_racks() -> list[dict[str, Any]]:
    """Rack blocks laid out with explicit gaps around zones and aisles."""
    specs = [
        ("rack_norte_01", -2.70, 4.25, 1.15, 0.46, 0.0),
        ("rack_norte_02", -1.30, 4.25, 1.15, 0.46, 0.0),
        ("rack_norte_03", 0.10, 4.25, 1.15, 0.46, 0.0),
        ("rack_norte_04", 1.50, 4.25, 1.15, 0.46, 0.0),
        ("rack_muro_oeste_sup", -5.65, 2.25, 1.35, 0.46, math.pi / 2),
        ("rack_muro_oeste_med", -5.65, 0.35, 1.35, 0.46, math.pi / 2),
        ("rack_muro_este_sup", 5.72, 2.75, 1.35, 0.46, math.pi / 2),
        ("rack_muro_este_med", 5.72, 0.75, 1.35, 0.46, math.pi / 2),
        ("rack_oeste_centro", -4.05, 0.15, 1.10, 0.46, 0.0),
        ("rack_este_superior", 2.60, 2.80, 1.00, 0.46, 0.0),
        ("rack_sur_centro_01", -1.75, -2.65, 1.25, 0.46, 0.0),
        ("rack_sur_centro_02", 0.00, -2.65, 1.25, 0.46, 0.0),
        ("rack_sur_centro_03", 1.75, -2.65, 1.25, 0.46, 0.0),
        ("rack_sur_centro_04", -1.75, -3.75, 1.25, 0.46, 0.0),
        ("rack_sur_centro_05", 0.00, -3.75, 1.25, 0.46, 0.0),
        ("rack_sur_centro_06", 1.75, -3.75, 1.25, 0.46, 0.0),
        ("rack_este_bajo", 3.00, -3.20, 1.00, 0.46, 0.0),
        ("rack_oeste_bajo", -2.90, -3.65, 0.90, 0.46, 0.0),
    ]
    return [
        {
            "name": name,
            "position": [round(x, 3), round(y, 3), 0.06],
            "size": [round(sx, 3), round(sy, 3), 1.95],
            "yaw_rad": yaw,
        }
        for name, x, y, sx, sy, yaw in specs
    ]


def zone_to_dict(zone: Zone) -> dict[str, Any]:
    visual_colors = {
        "initial": (0.16, 0.34, 0.54),
        "pickup": (0.86, 0.62, 0.12),
        "delivery": (0.16, 0.46, 0.26),
        "recharge": (0.58, 0.16, 0.13),
        "narrow_corridor": (0.88, 0.68, 0.12),
    }
    color = visual_colors.get(zone.kind, zone.color)
    return {
        "name": zone.name,
        "center": [zone.center[0], zone.center[1], 0.018],
        "size": [zone.size[0], zone.size[1], 0.018],
        "color": list(color),
        "kind": zone.kind,
    }


def validate_layout(scene: dict[str, Any]) -> dict[str, Any]:
    """Validate the 2-D occupancy plan before anything is exported to CoppeliaSim."""

    def rect(center: list[float] | tuple[float, ...], size: list[float] | tuple[float, ...], yaw: float = 0.0) -> tuple[float, float, float, float]:
        sx, sy = float(size[0]), float(size[1])
        c, s = abs(math.cos(yaw)), abs(math.sin(yaw))
        hx = (sx * c + sy * s) / 2.0
        hy = (sx * s + sy * c) / 2.0
        return (float(center[0]) - hx, float(center[0]) + hx, float(center[1]) - hy, float(center[1]) + hy)

    def overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float], clearance: float = 0.0) -> bool:
        return not (
            a[1] <= b[0] + clearance
            or b[1] <= a[0] + clearance
            or a[3] <= b[2] + clearance
            or b[3] <= a[2] + clearance
        )

    def inside(inner: tuple[float, float, float, float], outer: tuple[float, float, float, float], margin: float = 0.0) -> bool:
        return (
            inner[0] >= outer[0] + margin
            and inner[1] <= outer[1] - margin
            and inner[2] >= outer[2] + margin
            and inner[3] <= outer[3] - margin
        )

    zones = {z["name"]: rect(z["center"], z["size"]) for z in scene["zones"]}
    static_items: list[tuple[str, tuple[float, float, float, float]]] = []
    for rack in scene["racks"]:
        static_items.append((rack["name"], rect(rack["position"], rack["size"], rack["yaw_rad"])))
    obstacle = scene["central_obstacle"]
    obstacle_rect = rect(obstacle["position"], obstacle["size"])
    static_items.append((obstacle["name"], obstacle_rect))

    collisions: list[dict[str, str]] = []
    for idx, (name_a, rect_a) in enumerate(static_items):
        for name_b, rect_b in static_items[idx + 1 :]:
            if overlaps(rect_a, rect_b, clearance=0.02):
                collisions.append({"a": name_a, "b": name_b, "reason": "static footprints overlap"})

    for zone_name in ("zona_inicial_agvs", "zona_recogida_a", "zona_recogida_b", "zona_entrega_1", "zona_entrega_2", "zona_recarga"):
        for rack_name, rack_rect in static_items:
            if overlaps(zones[zone_name], rack_rect, clearance=0.02):
                collisions.append({"a": zone_name, "b": rack_name, "reason": "rack intrudes into operational zone"})

    for zone_name in ("zona_inicial_agvs", "zona_recogida_a", "zona_recogida_b", "zona_entrega_1", "zona_entrega_2", "zona_recarga"):
        if not (-6.0 <= zones[zone_name][0] and zones[zone_name][1] <= 6.0 and -5.0 <= zones[zone_name][2] and zones[zone_name][3] <= 5.0):
            collisions.append({"a": zone_name, "b": "canonical_boundary", "reason": "zone exceeds 12x10 m boundary"})

    footprint = scene["stations"]["footprints"]
    for station_name in ("pickup_a", "pickup_b"):
        station = scene["stations"][station_name]
        pickup_zone = zones["zona_recogida_a" if station_name == "pickup_a" else "zona_recogida_b"]
        conveyor_rect = rect(station["conveyor_position"], footprint["conveyor"])
        manipulator_rect = rect(station["manipulator_position"], footprint["manipulator"])
        for label, item_rect in ((f"{station_name}_conveyor", conveyor_rect), (f"{station_name}_manipulator", manipulator_rect)):
            if not inside(item_rect, pickup_zone, margin=0.04):
                collisions.append({"a": label, "b": station_name, "reason": "station is outside pickup zone"})
            for rack_name, rack_rect in static_items:
                if overlaps(item_rect, rack_rect, clearance=0.02):
                    collisions.append({"a": label, "b": rack_name, "reason": "station overlaps static footprint"})
        if overlaps(conveyor_rect, manipulator_rect, clearance=0.02):
            collisions.append({"a": f"{station_name}_conveyor", "b": f"{station_name}_manipulator", "reason": "station components overlap"})

    load_rects: list[tuple[str, tuple[float, float, float, float]]] = []
    for load in scene["loads"]:
        load_rect = rect(load["position"], load["size"])
        load_rects.append((load["name"], load_rect))
        zone_name = "zona_recogida_a" if load["zone"] == "A" else "zona_recogida_b"
        if not inside(load_rect, zones[zone_name], margin=0.02):
            collisions.append({"a": load["name"], "b": zone_name, "reason": "load is outside pickup zone"})
        for other_name, other_rect in static_items:
            if overlaps(load_rect, other_rect, clearance=0.02):
                collisions.append({"a": load["name"], "b": other_name, "reason": "load overlaps static footprint"})
        if load.get("workflow_load"):
            continue
        station_name = "pickup_a" if load["zone"] == "A" else "pickup_b"
        for label, pos, size in (
            (f"{station_name}_conveyor", scene["stations"][station_name]["conveyor_position"], footprint["conveyor"]),
            (f"{station_name}_manipulator", scene["stations"][station_name]["manipulator_position"], footprint["manipulator"]),
        ):
            if overlaps(load_rect, rect(pos, size), clearance=0.02):
                collisions.append({"a": load["name"], "b": label, "reason": "load overlaps station"})
    for idx, (name_a, rect_a) in enumerate(load_rects):
        for name_b, rect_b in load_rects[idx + 1 :]:
            if overlaps(rect_a, rect_b, clearance=0.02):
                collisions.append({"a": name_a, "b": name_b, "reason": "loads overlap"})

    initial_zone = zones["zona_inicial_agvs"]
    for robot in scene["robots"]:
        robot_rect = rect(robot["position"], (0.485, 0.381), robot["heading_rad"])
        if not inside(robot_rect, initial_zone, margin=0.02):
            collisions.append({"a": robot["name"], "b": "zona_inicial_agvs", "reason": "robot is outside initial zone"})
        for rack_name, rack_rect in static_items:
            if overlaps(robot_rect, rack_rect, clearance=0.04):
                collisions.append({"a": robot["name"], "b": rack_name, "reason": "robot overlaps static footprint"})

    status = "ok" if not collisions else "invalid"
    return {"status": status, "collision_count": len(collisions), "collisions": collisions}


def export_ttt(
    scene: dict[str, Any],
    port: int,
    ttt_path: Path,
    restore_previous: bool,
    coppelia: Path,
    launch_coppelia: bool,
) -> dict[str, Any]:
    process: subprocess.Popen[Any] | None = None
    try:
        if launch_coppelia:
            process = launch_coppelia_headless(coppelia, port, ROOT / "results/coppeliasim_validation/aws_canonical/coppelia_export.log")
        sim = connect(port)
        stop_if_running(sim)
        backup_dir = ROOT / "tmp/coppelia_scene_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = unique_backup_path(backup_dir / f"{ttt_path.stem}_pre_export.ttt")
        try:
            sim.saveScene(str(backup_path))
        except Exception:
            backup_path = Path("")

        sim.loadScene(scene["base_scene"])
        configure_scene_rendering(sim)
        prepare_aws_warehouse_reference(sim)
        add_canonical_overlay(sim, scene)
        write_scene_metadata(sim, scene)
        top_camera_metrics = capture_camera_snapshot(
            sim,
            "/MRBO_camera_top_canonical",
            ROOT / "results/coppeliasim_validation/aws_canonical/aws_canonical_top_camera.png",
        )
        oblique_camera_metrics = capture_camera_snapshot(
            sim,
            "/MRBO_camera_oblique_canonical",
            ROOT / "results/coppeliasim_validation/aws_canonical/aws_canonical_oblique_camera.png",
        )
        sim.saveScene(str(ttt_path))
        object_count = len(sim.getObjectsInTree(sim.handle_scene))

        if restore_previous and backup_path:
            sim.loadScene(str(backup_path))

        return {
            "object_count": object_count,
            "backup_path": str(backup_path) if backup_path else "",
            "top_camera": top_camera_metrics.get("path", ""),
            "top_camera_nonzero_ratio": top_camera_metrics.get("nonzero_ratio", ""),
            "oblique_camera": oblique_camera_metrics.get("path", ""),
            "oblique_camera_nonzero_ratio": oblique_camera_metrics.get("nonzero_ratio", ""),
        }
    finally:
        if process is not None:
            stop_process(process)


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
        (path.with_suffix(".json")).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return {"path": metrics["path"], "nonzero_ratio": metrics["nonzero_ratio"]}
    except Exception:
        return {"path": "", "nonzero_ratio": ""}


def connect(port: int):
    if not CLIENT_DIR.exists():
        raise FileNotFoundError(f"CoppeliaSim ZMQ client not found: {CLIENT_DIR}")
    sys.path.insert(0, str(CLIENT_DIR))
    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    deadline = time.time() + 10.0
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


def add_canonical_overlay(sim, scene: dict[str, Any]) -> None:
    root = sim.createDummy(0.05)
    set_alias(sim, root, "MRBO_AWS_CANONICAL_OVERLAY")
    configure_scene_rendering(sim)
    add_floor_and_walls(sim, scene)
    add_light_rig(sim, scene)
    add_bounding_frame(sim, scene)
    for zone in scene["zones"]:
        if zone["kind"] == "narrow_corridor":
            add_hatched_zone(sim, zone)
        else:
            add_zone(sim, zone)
    for rack in scene["racks"]:
        add_rack(sim, scene["model_paths"]["rack"], rack)
    add_box(
        sim,
        BoxSpec(
            scene["central_obstacle"]["name"],
            tuple(scene["central_obstacle"]["position"]),
            tuple(scene["central_obstacle"]["size"]),
            (0.44, 0.44, 0.44),
            mass_kg=0.1,
        ),
    )
    add_safety_hardware(sim, scene)
    add_station_models(sim, scene)
    for load in scene["loads"]:
        add_load(sim, load)
    for route in scene["routes"]:
        add_route(sim, route["name"], route["points"])
    for robot in scene["robots"]:
        add_pioneer(sim, scene["model_paths"]["pioneer_p3dx"], robot)
    add_camera_pair(sim)
    add_demo_script(sim, scene)


def add_safety_hardware(sim, scene: dict[str, Any]) -> None:
    obstacle = scene["central_obstacle"]
    x, y, _ = obstacle["position"]
    sx, sy, _ = obstacle["size"]
    for idx, (bx, by) in enumerate(
        [
            (x - sx / 2 - 0.18, y - sy / 2 - 0.18),
            (x + sx / 2 + 0.18, y - sy / 2 - 0.18),
            (x - sx / 2 - 0.18, y + sy / 2 + 0.18),
            (x + sx / 2 + 0.18, y + sy / 2 + 0.18),
        ],
        start=1,
    ):
        add_bollard(sim, f"obstaculo_central_bollard_{idx}", bx, by)
    for zone in scene["zones"]:
        if zone["kind"] != "pickup":
            continue
        zx, zy, _ = zone["center"]
        zs = zone["size"]
        add_guardrail(sim, f"{zone['name']}_rear_guardrail", zx, zy - zs[1] / 2 - 0.16, zs[0] * 0.72, 0.0)


def add_bollard(sim, name: str, x: float, y: float) -> None:
    post = add_cylinder(sim, name, 0.055, 0.55, (x, y, 0.275), (0.94, 0.67, 0.08))
    add_box(sim, BoxSpec(name + "_black_band_1", (x, y, 0.23), (0.13, 0.018, 0.045), (0.04, 0.04, 0.04), static=True, respondable=False))
    add_box(sim, BoxSpec(name + "_black_band_2", (x, y, 0.39), (0.13, 0.018, 0.045), (0.04, 0.04, 0.04), static=True, respondable=False))
    try:
        sim.setObjectInt32Param(post, sim.shapeintparam_respondable, 1)
    except Exception:
        pass


def add_guardrail(sim, name: str, x: float, y: float, length: float, yaw: float) -> None:
    rail_color = (0.94, 0.67, 0.08)
    post_color = (0.08, 0.08, 0.07)
    add_box(sim, BoxSpec(name + "_rail_top", (x, y, 0.52), (length, 0.055, 0.070), rail_color, yaw_rad=yaw, static=True, respondable=False))
    add_box(sim, BoxSpec(name + "_rail_mid", (x, y, 0.34), (length, 0.050, 0.060), rail_color, yaw_rad=yaw, static=True, respondable=False))
    for idx, offset in enumerate([-length / 2, 0.0, length / 2], start=1):
        px, py = rotate_offset(offset, 0.0, yaw)
        add_box(sim, BoxSpec(f"{name}_post_{idx}", (x + px, y + py, 0.28), (0.065, 0.065, 0.50), post_color, yaw_rad=yaw, static=True, respondable=False))


def configure_scene_rendering(sim) -> None:
    try:
        sim.setBoolParam(sim.boolparam_shape_textures_are_visible, True)
    except Exception:
        pass
    for param, value in (
        ("arrayparam_background_color1", [0.82, 0.86, 0.90]),
        ("arrayparam_background_color2", [0.72, 0.76, 0.82]),
        ("arrayparam_ambient_light", [0.55, 0.55, 0.55]),
    ):
        try:
            sim.setArrayParam(getattr(sim, param), value)
        except Exception:
            pass


def prepare_aws_warehouse_reference(sim) -> None:
    """Keep AWS visual context visible while removing it from active collisions."""
    try:
        warehouse = sim.getObject("/warehouse")
    except Exception:
        return
    for handle in sim.getObjectsInTree(warehouse, sim.handle_all, 0):
        try:
            sim.setObjectInt32Param(handle, sim.objintparam_visibility_layer, 0)
        except Exception:
            pass
        try:
            if sim.getObjectType(handle) == sim.object_shape_type:
                props = sim.getObjectSpecialProperty(handle)
                renderable = getattr(sim, "objectspecialproperty_renderable", 0x0200)
                sim.setObjectSpecialProperty(handle, (props | renderable) & ~sim.objectspecialproperty_collidable)
                sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1)
                sim.setObjectInt32Param(handle, sim.shapeintparam_respondable, 0)
        except Exception:
            pass


def add_floor_and_walls(sim, scene: dict[str, Any]) -> None:
    width = scene["dimensions_m"]["width"]
    depth = scene["dimensions_m"]["depth"]
    add_box(sim, BoxSpec("canonical_concrete_floor_12x10", (0, 0, -0.025), (width, depth, 0.05), (0.42, 0.43, 0.42)))
    for ix in range(12):
        for iy in range(10):
            x = -5.5 + ix
            y = -4.5 + iy
            shade = 0.44 + 0.018 * (((ix * 17 + iy * 11) % 5) - 2)
            add_box(
                sim,
                BoxSpec(
                    f"floor_concrete_panel_{ix:02d}_{iy:02d}",
                    (x, y, 0.006),
                    (0.96, 0.96, 0.010),
                    (shade, shade + 0.008, shade + 0.010),
                    static=True,
                    respondable=False,
                ),
            )
    seam_color = (0.30, 0.31, 0.31)
    for idx, x in enumerate([v * 1.0 for v in range(-5, 6)], start=1):
        add_box(sim, BoxSpec(f"floor_tile_seam_x_{idx:02d}", (x, 0, 0.012), (0.018, depth, 0.012), seam_color, static=True, respondable=False))
    for idx, y in enumerate([v * 1.0 for v in range(-4, 5)], start=1):
        add_box(sim, BoxSpec(f"floor_tile_seam_y_{idx:02d}", (0, y, 0.014), (width, 0.018, 0.012), seam_color, static=True, respondable=False))
    lane_color = (0.92, 0.78, 0.18)
    add_box(sim, BoxSpec("aisle_main_lane_yellow_left", (0.0, -0.95, 0.035), (9.8, 0.045, 0.018), lane_color, static=True, respondable=False))
    add_box(sim, BoxSpec("aisle_main_lane_yellow_right", (0.0, 0.95, 0.035), (9.8, 0.045, 0.018), lane_color, static=True, respondable=False))
    add_box(sim, BoxSpec("aisle_cross_lane_yellow_north", (-3.0, 1.55, 0.035), (0.045, 6.2, 0.018), lane_color, static=True, respondable=False))
    add_box(sim, BoxSpec("aisle_cross_lane_yellow_south", (3.0, -1.55, 0.035), (0.045, 6.2, 0.018), lane_color, static=True, respondable=False))
    wall_color = (0.62, 0.64, 0.64)
    add_box(sim, BoxSpec("canonical_wall_north", (0, depth / 2 + 0.06, 0.62), (width + 0.25, 0.12, 1.24), wall_color))
    add_box(sim, BoxSpec("canonical_wall_south", (0, -depth / 2 - 0.06, 0.62), (width + 0.25, 0.12, 1.24), wall_color))
    add_box(sim, BoxSpec("canonical_wall_east", (width / 2 + 0.06, 0, 0.62), (0.12, depth + 0.25, 1.24), wall_color))
    add_box(sim, BoxSpec("canonical_wall_west", (-width / 2 - 0.06, 0, 0.62), (0.12, depth + 0.25, 1.24), wall_color))
    add_dock_doors(sim, width, depth)


def add_dock_doors(sim, width: float, depth: float) -> None:
    door_color = (0.18, 0.22, 0.24)
    trim_color = (0.88, 0.55, 0.12)
    for idx, x in enumerate([-3.5, 0.0, 3.5], start=1):
        add_box(sim, BoxSpec(f"dock_door_north_{idx}", (x, depth / 2 - 0.012, 0.48), (1.35, 0.035, 0.82), door_color, static=True, respondable=False))
        add_box(sim, BoxSpec(f"dock_header_north_{idx}", (x, depth / 2 - 0.030, 0.93), (1.47, 0.045, 0.08), trim_color, static=True, respondable=False))
    for idx, y in enumerate([-3.0, 0.0, 3.0], start=1):
        add_box(sim, BoxSpec(f"east_service_panel_{idx}", (width / 2 - 0.012, y, 0.55), (0.035, 1.15, 0.70), door_color, yaw_rad=0.0, static=True, respondable=False))


def add_light_rig(sim, scene: dict[str, Any]) -> None:
    width = scene["dimensions_m"]["width"]
    depth = scene["dimensions_m"]["depth"]
    for idx, (x, y) in enumerate([(-3.6, -3.0), (0.0, -3.0), (3.6, -3.0), (-3.6, 1.2), (0.0, 1.2), (3.6, 1.2)], start=1):
        add_box(sim, BoxSpec(f"overhead_light_panel_{idx:02d}", (x, y, 2.85), (1.05, 0.26, 0.035), (0.96, 0.96, 0.82), static=True, respondable=False))
    for idx, x in enumerate([-width / 2 + 0.8, width / 2 - 0.8], start=1):
        add_box(sim, BoxSpec(f"wall_safety_column_{idx:02d}_north", (x, depth / 2 - 0.35, 0.75), (0.18, 0.18, 1.45), (0.95, 0.74, 0.12)))
        add_box(sim, BoxSpec(f"wall_safety_column_{idx:02d}_south", (x, -depth / 2 + 0.35, 0.75), (0.18, 0.18, 1.45), (0.95, 0.74, 0.12)))


def add_bounding_frame(sim, scene: dict[str, Any]) -> None:
    width = scene["dimensions_m"]["width"]
    depth = scene["dimensions_m"]["depth"]
    color = (0.08, 0.08, 0.08)
    z = 0.08
    add_box(sim, BoxSpec("canonical_12m_frame_north", (0, depth / 2, z), (width, 0.05, 0.08), color))
    add_box(sim, BoxSpec("canonical_12m_frame_south", (0, -depth / 2, z), (width, 0.05, 0.08), color))
    add_box(sim, BoxSpec("canonical_10m_frame_east", (width / 2, 0, z), (0.05, depth, 0.08), color))
    add_box(sim, BoxSpec("canonical_10m_frame_west", (-width / 2, 0, z), (0.05, depth, 0.08), color))


def add_rack(sim, model_path: str, rack: dict[str, Any]) -> None:
    x, y, z = rack["position"]
    sx, sy, sz = rack["size"]
    yaw = float(rack["yaw_rad"])
    footprint = add_box(
        sim,
        BoxSpec(
            rack["name"] + "_footprint",
            (x, y, 0.14),
            (sx, sy, 0.12),
            (0.08, 0.11, 0.13),
            yaw_rad=yaw,
            static=True,
            respondable=True,
        ),
    )
    upright_color = (0.04, 0.17, 0.27)
    beam_color = (0.94, 0.56, 0.10)
    shelf_color = (0.27, 0.30, 0.32)
    pallet_color = (0.60, 0.40, 0.22)
    carton_colors = [(0.72, 0.52, 0.30), (0.62, 0.46, 0.28), (0.80, 0.62, 0.38)]

    for corner_idx, (ox, oy) in enumerate([(-sx / 2, -sy / 2), (-sx / 2, sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2)], start=1):
        px, py = rotate_offset(ox, oy, yaw)
        add_box(sim, BoxSpec(f"{rack['name']}_upright_{corner_idx}", (x + px, y + py, sz / 2), (0.055, 0.055, sz), upright_color, yaw_rad=yaw))

    rack_levels = [0.42, 0.86, 1.30, 1.74]
    for level_idx, level_z in enumerate(rack_levels, start=1):
        for side_idx, oy in enumerate([-sy / 2, sy / 2], start=1):
            px, py = rotate_offset(0.0, oy, yaw)
            add_box(sim, BoxSpec(f"{rack['name']}_beam_L{level_idx}_{side_idx}", (x + px, y + py, level_z), (sx + 0.08, 0.05, 0.07), beam_color, yaw_rad=yaw, static=True, respondable=False))
        add_box(sim, BoxSpec(f"{rack['name']}_shelf_deck_L{level_idx}", (x, y, level_z - 0.06), (sx * 0.96, sy * 0.82, 0.035), shelf_color, yaw_rad=yaw, static=True, respondable=False))

    local_slots = [-0.30, 0.0, 0.30]
    for level_slot, carton_z in enumerate([0.62, 1.06, 1.50], start=1):
        for idx, offset in enumerate(local_slots, start=1):
            px, py = rotate_offset(offset * sx, 0.0, yaw)
            if level_slot == 1:
                add_box(sim, BoxSpec(f"{rack['name']}_pallet_{idx}", (x + px, y + py, 0.49), (min(0.36, sx / 3.5), sy * 0.70, 0.12), pallet_color, yaw_rad=yaw, static=True, respondable=False))
            add_box(
                sim,
                BoxSpec(
                    f"{rack['name']}_carton_L{level_slot}_{idx}",
                    (x + px, y + py, carton_z),
                    (min(0.32, sx / 3.8), sy * 0.62, 0.24),
                    carton_colors[(idx + level_slot - 2) % len(carton_colors)],
                    yaw_rad=yaw,
                    static=True,
                    respondable=False,
                ),
            )
    label_px, label_py = rotate_offset(-sx / 2 + 0.12, -sy / 2 - 0.028, yaw)
    add_box(sim, BoxSpec(f"{rack['name']}_barcode_label", (x + label_px, y + label_py, 1.88), (0.20, 0.012, 0.09), (0.92, 0.92, 0.86), yaw_rad=yaw, static=True, respondable=False))
    return footprint


def rotate_offset(x: float, y: float, yaw: float) -> tuple[float, float]:
    return (
        x * math.cos(yaw) - y * math.sin(yaw),
        x * math.sin(yaw) + y * math.cos(yaw),
    )


def add_zone(sim, zone: dict[str, Any]) -> None:
    color = tuple(zone["color"])
    sx, sy, _ = zone["size"]
    x, y, _ = zone["center"]
    z = 0.052
    border = 0.045
    add_box(sim, BoxSpec(zone["name"] + "_north_line", (x, y + sy / 2, z), (sx, border, 0.018), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone["name"] + "_south_line", (x, y - sy / 2, z), (sx, border, 0.018), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone["name"] + "_east_line", (x + sx / 2, y, z), (border, sy, 0.018), color, static=True, respondable=False))
    add_box(sim, BoxSpec(zone["name"] + "_west_line", (x - sx / 2, y, z), (border, sy, 0.018), color, static=True, respondable=False))
    corner = min(0.34, sx * 0.18, sy * 0.26)
    for idx, (cx, cy, yaw) in enumerate(
        [
            (x - sx / 2 + corner / 2, y + sy / 2 - corner / 2, 0.0),
            (x + sx / 2 - corner / 2, y + sy / 2 - corner / 2, math.pi / 2),
            (x + sx / 2 - corner / 2, y - sy / 2 + corner / 2, math.pi),
            (x - sx / 2 + corner / 2, y - sy / 2 + corner / 2, -math.pi / 2),
        ],
        start=1,
    ):
        add_box(sim, BoxSpec(f"{zone['name']}_corner_{idx}_a", (cx, cy, z + 0.006), (corner, border * 1.15, 0.018), color, yaw_rad=yaw, static=True, respondable=False))
        add_box(sim, BoxSpec(f"{zone['name']}_corner_{idx}_b", (cx, cy, z + 0.007), (border * 1.15, corner, 0.018), color, yaw_rad=yaw, static=True, respondable=False))
    if zone["kind"] in {"delivery", "recharge"}:
        add_box(sim, BoxSpec(zone["name"] + "_subtle_pad", (x, y, 0.035), (sx * 0.64, sy * 0.50, 0.010), tuple(v * 0.78 for v in color), static=True, respondable=False))


def add_hatched_zone(sim, zone: dict[str, Any]) -> None:
    add_zone(sim, zone)
    color = tuple(zone["color"])
    x, y, _ = zone["center"]
    sx, sy, _ = zone["size"]
    for idx, offset in enumerate([-0.45, -0.15, 0.15, 0.45], start=1):
        add_box(
            sim,
            BoxSpec(
                f"{zone['name']}_hatch_pos_{idx}",
                (x + offset, y, 0.085),
                (0.035, sy * 1.25, 0.025),
                color,
                yaw_rad=math.radians(36),
                static=True,
                respondable=False,
            ),
        )
        add_box(
            sim,
            BoxSpec(
                f"{zone['name']}_hatch_neg_{idx}",
                (x + offset, y, 0.09),
                (0.035, sy * 1.25, 0.025),
                color,
                yaw_rad=math.radians(-36),
                static=True,
                respondable=False,
            ),
        )


def add_station_models(sim, scene: dict[str, Any]) -> None:
    stations = scene["stations"]
    for label, station in (("a", stations["pickup_a"]), ("b", stations["pickup_b"])):
        px, py, _ = station["conveyor_position"]
        source_x, source_y, _ = station["source_platform_position"]
        handoff_x, handoff_y, handoff_z = station["handoff_position"]
        add_box(sim, BoxSpec(f"zona_recogida_{label}_source_table", (source_x, source_y, 0.39), (0.72, 0.52, 0.78), (0.20, 0.22, 0.22), static=True, respondable=True))
        add_box(sim, BoxSpec(f"zona_recogida_{label}_source_table_top", (source_x, source_y, 0.79), (0.76, 0.56, 0.055), (0.66, 0.67, 0.64), static=True, respondable=True))
        add_box(sim, BoxSpec(f"zona_recogida_{label}_handoff_table", (handoff_x, handoff_y, handoff_z / 2.0), (0.62, 0.52, max(handoff_z, 0.08)), (0.18, 0.21, 0.23), static=True, respondable=True))
        add_box(sim, BoxSpec(f"zona_recogida_{label}_handoff_table_top", (handoff_x, handoff_y, handoff_z + 0.025), (0.66, 0.56, 0.05), (0.62, 0.64, 0.62), static=True, respondable=True))
        add_box(sim, BoxSpec(f"zona_recogida_{label}_conveyor_guard_left", (px, py - 0.31, 0.50), (1.48, 0.035, 0.26), (0.92, 0.70, 0.10), static=True, respondable=False))
        add_box(sim, BoxSpec(f"zona_recogida_{label}_conveyor_guard_right", (px, py + 0.31, 0.50), (1.48, 0.035, 0.26), (0.92, 0.70, 0.10), static=True, respondable=False))
        mx, my, _ = station["manipulator_position"]
        add_box(sim, BoxSpec(f"zona_recogida_{label}_robot_pedestal", (mx, my, 0.10), (0.68, 0.68, 0.20), (0.18, 0.20, 0.22), static=True, respondable=True))
    add_conveyor(sim, scene["model_paths"]["conveyor"], "zona_recogida_a_conveyor_model", tuple(stations["pickup_a"]["conveyor_position"]), yaw_rad=0.0)
    add_conveyor(sim, scene["model_paths"]["conveyor"], "zona_recogida_b_conveyor_model", tuple(stations["pickup_b"]["conveyor_position"]), yaw_rad=0.0)
    load_model_or_box(
        sim,
        scene["model_paths"]["manipulator"],
        "zona_recogida_a_manipulador_model",
        stations["pickup_a"]["manipulator_position"],
        yaw_rad=0.0,
        scale=(1.0, 1.0, 1.0),
        fallback=BoxSpec("zona_recogida_a_manipulador_base", tuple(stations["pickup_a"]["manipulator_position"]), (0.35, 0.35, 0.12), (0.95, 0.65, 0.05)),
    )
    load_model_or_box(
        sim,
        scene["model_paths"]["manipulator"],
        "zona_recogida_b_manipulador_model",
        stations["pickup_b"]["manipulator_position"],
        yaw_rad=math.pi,
        scale=(1.0, 1.0, 1.0),
        fallback=BoxSpec("zona_recogida_b_manipulador_base", tuple(stations["pickup_b"]["manipulator_position"]), (0.35, 0.35, 0.12), (0.95, 0.65, 0.05)),
    )
    add_box(sim, BoxSpec("zona_entrega_1_plataforma_verde", tuple(stations["delivery_1_marker"]), (0.72, 0.52, 0.08), (0.08, 0.62, 0.28)))
    add_box(sim, BoxSpec("zona_entrega_2_plataforma_verde", tuple(stations["delivery_2_marker"]), (0.72, 0.52, 0.08), (0.08, 0.62, 0.28)))
    add_box(sim, BoxSpec("zona_recarga_pad_rojo", tuple(stations["recharge_marker"]), (0.80, 0.62, 0.08), (0.90, 0.12, 0.08)))


def add_conveyor(sim, model_path: str, name: str, position: tuple[float, float, float], yaw_rad: float) -> int:
    x, y, z = position
    handle = load_model(sim, model_path)
    if handle is not None:
        set_alias(sim, handle, name)
        disable_model_scripts(sim, handle)
        make_model_visual_only(sim, handle)
        sim.setObjectPosition(handle, -1, [x, y, z])
        sim.setObjectOrientation(handle, -1, [0.0, 0.0, yaw_rad])
        return handle
    base = add_box(sim, BoxSpec(name, (x, y, z), (1.30, 0.45, 0.16), (0.13, 0.14, 0.14), yaw_rad=yaw_rad, static=True, respondable=True))
    add_box(sim, BoxSpec(name + "_belt", (x, y, z + 0.095), (1.20, 0.36, 0.035), (0.03, 0.03, 0.03), yaw_rad=yaw_rad, static=True, respondable=False))
    for idx, offset in enumerate([-0.48, 0.0, 0.48], start=1):
        px, py = rotate_offset(offset, 0.0, yaw_rad)
        roller = add_cylinder(sim, f"{name}_roller_{idx}", 0.055, 0.40, (x + px, y + py, z + 0.13), (0.46, 0.48, 0.50))
        try:
            sim.setObjectOrientation(roller, -1, [math.pi / 2, 0.0, yaw_rad])
        except Exception:
            pass
    return base


def add_load(sim, load: dict[str, Any]) -> None:
    color = (0.62, 0.64, 0.60)
    if load.get("station") == "pickup_a":
        color = (0.55, 0.61, 0.64)
    elif load.get("station") == "pickup_b":
        color = (0.60, 0.60, 0.54)
    handle = add_box(
        sim,
        BoxSpec(
            load["name"],
            tuple(load["position"]),
            tuple(load["size"]),
            color,
            mass_kg=max(float(load["weight_kg"]), 0.1),
            static=True,
            respondable=False,
        ),
    )
    sx, sy, sz = (float(v) for v in load["size"])
    x, y, z = (float(v) for v in load["position"])
    for idx, (dy, dz) in enumerate(((-sy / 2 - 0.006, 0.02), (sy / 2 + 0.006, 0.02)), start=1):
        detail = add_box(
            sim,
            BoxSpec(
                f"{load['name']}_handle_{idx}",
                (x, y + dy, z + dz),
                (sx * 0.42, 0.010, sz * 0.28),
                (0.08, 0.09, 0.09),
                static=True,
                respondable=False,
            ),
        )
        try:
            sim.setObjectParent(detail, handle, True)
        except Exception:
            pass
    label = add_box(
        sim,
        BoxSpec(
            f"{load['name']}_label",
            (x + sx / 2 + 0.006, y, z + 0.02),
            (0.010, sy * 0.46, sz * 0.34),
            (0.92, 0.92, 0.84),
            static=True,
            respondable=False,
        ),
    )
    try:
        sim.setObjectParent(label, handle, True)
    except Exception:
        pass
    marker_pos = [load["position"][0], load["position"][1], load["position"][2] + load["size"][2] / 2 + 0.08]
    dummy = sim.createDummy(0.06)
    set_alias(sim, dummy, f"{load['name']}_requires_{load['required_agvs']}_agv")
    sim.setObjectPosition(dummy, -1, marker_pos)
    try:
        sim.setObjectParent(dummy, handle, True)
    except Exception:
        pass


def add_route(sim, name: str, points: list[list[float] | tuple[float, float]]) -> None:
    color = (0.92, 0.92, 0.86)
    for segment_idx, (a, b) in enumerate(zip(points, points[1:]), start=1):
        ax, ay = float(a[0]), float(a[1])
        bx, by = float(b[0]), float(b[1])
        dx = bx - ax
        dy = by - ay
        length = math.hypot(dx, dy)
        if length <= 0.01:
            continue
        yaw = math.atan2(dy, dx)
        dash_len = 0.38
        step = 0.70
        count = max(1, int(length / step))
        ux, uy = dx / length, dy / length
        for dash_idx in range(count):
            dist = min(length - dash_len / 2, dash_idx * step + dash_len / 2)
            if dist < dash_len / 2:
                continue
            cx = ax + ux * dist
            cy = ay + uy * dist
            add_box(
                sim,
                BoxSpec(
                    f"{name}_dash_{segment_idx:02d}_{dash_idx + 1:02d}",
                    (cx, cy, 0.065),
                    (dash_len, 0.035, 0.025),
                    color,
                    yaw_rad=yaw,
                    static=True,
                    respondable=False,
                ),
            )


def add_pioneer(sim, model_path: str, robot: dict[str, Any]) -> None:
    class_colors = {
        "ligero": (0.92, 0.72, 0.05),
        "medio": (0.90, 0.22, 0.08),
        "alta_capacidad": (0.15, 0.55, 0.22),
    }
    handle = load_model(sim, model_path)
    if handle is None:
        handle = add_cylinder(sim, robot["name"] + "_fallback_base", 0.28, 0.30, tuple(robot["position"]), (0.12, 0.12, 0.12))
    else:
        disable_model_scripts(sim, handle)
        make_model_visual_only(sim, handle)
    set_alias(sim, handle, robot["name"])
    sim.setObjectPosition(handle, -1, robot["position"])
    sim.setObjectOrientation(handle, -1, [0.0, 0.0, robot["heading_rad"]])
    x, y, z = robot["position"]
    marker = add_cylinder(
        sim,
        robot["name"] + "_tipo_" + robot["class"],
        0.12,
        0.035,
        (x, y, z + 0.22),
        class_colors.get(robot["class"], (0.2, 0.2, 0.2)),
    )
    try:
        sim.setObjectParent(marker, handle, True)
    except Exception:
        pass
    comm = sim.createDummy(0.08)
    set_alias(sim, comm, robot["name"] + "_radio_local_R")
    sim.setObjectPosition(comm, -1, [x, y, z + 0.34])
    try:
        sim.setObjectParent(comm, handle, True)
    except Exception:
        pass


def add_camera_pair(sim) -> None:
    top = sim.createVisionSensor(1 + 4, [1280, 960, 0, 0], [0.05, 40.0, 11.2, 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0])
    set_alias(sim, top, "MRBO_camera_top_canonical")
    sim.setExplicitHandling(top, 1)
    sim.setObjectInt32Param(top, sim.visionintparam_perspective_operation, 0)
    sim.setObjectFloatParam(top, sim.visionfloatparam_ortho_size, 11.0)
    sim.setObjectPosition(top, -1, [0.0, 0.0, 12.5])
    sim.setObjectOrientation(top, -1, [0.0, math.pi, 0.0])
    oblique = sim.createVisionSensor(1 + 4, [1280, 960, 0, 0], [0.05, 40.0, math.radians(86), 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0])
    set_alias(sim, oblique, "MRBO_camera_oblique_canonical")
    sim.setExplicitHandling(oblique, 1)
    oblique_position = [0.0, 0.0, 12.4]
    oblique_orientation = [0.0, math.pi, 0.0]
    sim.setObjectPosition(oblique, -1, oblique_position)
    sim.setObjectOrientation(oblique, -1, oblique_orientation)
    try:
        camera = sim.createObject(sim.object_camera_type, 0)
        set_alias(sim, camera, "MRBO_camera_oblique_view")
        sim.setObjectPosition(camera, -1, oblique_position)
        sim.setObjectOrientation(camera, -1, oblique_orientation)
    except Exception:
        pass


def add_demo_script(sim, scene: dict[str, Any]) -> None:
    code = render_demo_script(scene)
    try:
        dummy = sim.createDummy(0.03)
        set_alias(sim, dummy, "MRBO_demo_controller")
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
    except Exception:
        pass


def render_demo_script(scene: dict[str, Any]) -> str:
    playback = lua_table(scene["animation"])
    stations = lua_table(scene["stations"])
    loads = lua_table(scene["loads"])
    return """-- Embedded deterministic motion preview for the MRBO AWS canonical scene.
local playback = __PLAYBACK__
local stations = __STATIONS__
local loads = __LOADS__
local robotHandles = {}
local robotPaths = {}
local robotByName = {}
local armStations = {}
local loadHandles = {}

local function getByAlias(alias)
    local ok, handle = pcall(sim.getObject, '/' .. alias)
    if ok and handle and handle >= 0 then return handle end
    return nil
end

local function clamp(v, lo, hi)
    return math.max(lo, math.min(hi, v))
end

local function lerp(a, b, u)
    return a + (b - a) * u
end

local function smooth(u)
    u = clamp(u, 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)
end

local function mix3(a, b, u)
    return {
        lerp(a[1], b[1], u),
        lerp(a[2], b[2], u),
        lerp(a[3], b[3], u)
    }
end

local function yawTo(a, b)
    return math.atan2(b[2] - a[2], b[1] - a[1])
end

local function samplePath(path, t, cycle)
    if #path < 2 then return path[1], 0 end
    local segCount = #path - 1
    local phase = (t % cycle) / cycle
    local scaled = phase * segCount
    local idx = math.min(segCount, math.floor(scaled) + 1)
    local u = scaled - (idx - 1)
    local a, b = path[idx], path[idx + 1]
    return {
        a[1] + (b[1] - a[1]) * u,
        a[2] + (b[2] - a[2]) * u,
        a[3] + (b[3] - a[3]) * u,
    }, yawTo(a, b)
end

function sysCall_init()
    local idx = 1
    for name, path in pairs(playback.robots) do
        local handle = getByAlias(name)
        if handle then
            robotHandles[idx] = handle
            robotPaths[idx] = path
            robotByName[name] = handle
            idx = idx + 1
        end
    end
    local stationArmAliases = {
        pickup_a = 'zona_recogida_a_manipulador_model',
        pickup_b = 'zona_recogida_b_manipulador_model'
    }
    for stationName, alias in pairs(stationArmAliases) do
        local handle = getByAlias(alias)
        if handle then
            local joints = sim.getObjectsInTree(handle, sim.object_joint_type, 0)
            if #joints > 0 then armStations[#armStations + 1] = {station = stationName, joints = joints} end
        end
    end
    for _, load in ipairs(loads) do
        local handle = getByAlias(load.name)
        if handle then loadHandles[load.name] = handle end
    end
end

local function setArmPose(stationName, joints, t)
    local offset = stationName == 'pickup_b' and 4.5 or 0.0
    local phase = ((t + offset) % playback.manipulator_cycle_s) / playback.manipulator_cycle_s
    local side = stationName == 'pickup_b' and -1.0 or 1.0
    local home = {0.0, -0.55, 0.95, 0.0, 0.72, 0.0}
    local pick = {side * 0.35, -0.82, 1.22, 0.0, 0.56, side * 0.18}
    local place = {side * -0.48, -0.70, 1.05, 0.0, 0.62, side * -0.18}
    local fromPose, toPose, u
    if phase < 0.22 then
        fromPose, toPose, u = home, pick, phase / 0.22
    elseif phase < 0.38 then
        fromPose, toPose, u = pick, pick, (phase - 0.22) / 0.16
    elseif phase < 0.68 then
        fromPose, toPose, u = pick, place, (phase - 0.38) / 0.30
    elseif phase < 0.82 then
        fromPose, toPose, u = place, place, (phase - 0.68) / 0.14
    else
        fromPose, toPose, u = place, home, (phase - 0.82) / 0.18
    end
    u = smooth(u)
    for jointIdx, joint in ipairs(joints) do
        local a = fromPose[((jointIdx - 1) % #fromPose) + 1]
        local b = toPose[((jointIdx - 1) % #toPose) + 1]
        local q = lerp(a, b, u)
        pcall(sim.setJointTargetPosition, joint, q)
        pcall(sim.setJointPosition, joint, q)
    end
end

local function setLoadPose(load, t)
    local handle = loadHandles[load.name]
    local station = stations[load.station]
    if not handle or not station then return end
    local cycle = playback.box_cycle_s or playback.cycle_s
    local phase = ((t + (load.phase_offset_s or 0.0)) % cycle) / cycle
    local halfHeight = load.size[3] / 2.0
    local spawn = load.position
    local pick = station.pick_position
    local handoff = {
        station.handoff_position[1],
        station.handoff_position[2],
        station.handoff_position[3] + halfHeight + 0.04
    }
    local pos = spawn
    local yaw = 0.0
    if phase < 0.18 then
        pos = mix3(spawn, pick, smooth(phase / 0.18))
    elseif phase < 0.44 then
        local u = smooth((phase - 0.18) / 0.26)
        pos = mix3(pick, handoff, u)
        pos[3] = pos[3] + 0.28 * math.sin(math.pi * u)
    elseif phase < 0.58 then
        pos = handoff
    else
        local robot = robotByName[load.assigned_amr]
        if robot then
            local ok, robotPos = pcall(sim.getObjectPosition, robot, -1)
            if ok and robotPos then
                pos = {robotPos[1], robotPos[2], robotPos[3] + 0.34}
                local okOri, robotOri = pcall(sim.getObjectOrientation, robot, -1)
                if okOri and robotOri then yaw = robotOri[3] end
            end
        end
    end
    pcall(sim.setObjectPosition, handle, -1, pos)
    pcall(sim.setObjectOrientation, handle, -1, {0, 0, yaw})
end

function sysCall_actuation()
    local t = sim.getSimulationTime()
    for i, handle in ipairs(robotHandles) do
        local pos, yaw = samplePath(robotPaths[i], t + (i - 1) * 1.7, playback.cycle_s)
        pcall(sim.setObjectPosition, handle, -1, pos)
        pcall(sim.setObjectOrientation, handle, -1, {0, 0, yaw})
    end
    for _, arm in ipairs(armStations) do
        setArmPose(arm.station, arm.joints, t)
    end
    for _, load in ipairs(loads) do setLoadPose(load, t) end
end
""".replace("__PLAYBACK__", playback).replace("__STATIONS__", stations).replace("__LOADS__", loads)


def load_model_or_box(
    sim,
    model_path: str,
    alias: str,
    position: list[float],
    yaw_rad: float,
    fallback: BoxSpec,
    orientation: tuple[float, float, float] | None = None,
    scale: tuple[float, float, float] | None = None,
) -> int:
    handle = load_model(sim, model_path)
    if handle is None:
        return add_box(sim, fallback)
    set_alias(sim, handle, alias)
    if scale is not None:
        scale_model(sim, handle, scale)
    disable_model_scripts(sim, handle)
    make_model_visual_only(sim, handle)
    sim.setObjectPosition(handle, -1, position)
    sim.setObjectOrientation(handle, -1, list(orientation or (0.0, 0.0, yaw_rad)))
    return handle


def load_model(sim, model_path: str) -> int | None:
    path = Path(model_path)
    if not path.exists():
        return None
    try:
        handle = sim.loadModel(str(path))
    except Exception:
        return None
    return handle if isinstance(handle, int) and handle >= 0 else None


def scale_model(sim, handle: int, scale: tuple[float, float, float]) -> None:
    try:
        sim.scaleModelNonIsometrically(handle, float(scale[0]), float(scale[1]), float(scale[2]))
    except Exception as exc:
        raise RuntimeError(f"Could not scale model {handle} with {scale!r}") from exc


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
    """Keep imported visual geometry while using explicit overlay footprints for collision."""
    for child in sim.getObjectsInTree(handle, sim.handle_all, 0):
        try:
            if sim.getObjectType(child) != sim.object_shape_type:
                continue
            props = sim.getObjectSpecialProperty(child)
            renderable = getattr(sim, "objectspecialproperty_renderable", 0x0200)
            sim.setObjectSpecialProperty(child, (props | renderable) & ~sim.objectspecialproperty_collidable)
            sim.setObjectInt32Param(child, sim.shapeintparam_static, 1)
            sim.setObjectInt32Param(child, sim.shapeintparam_respondable, 0)
        except Exception:
            pass


def add_box(sim, spec: BoxSpec) -> int:
    try:
        handle = sim.createPrimitiveShape(sim.primitiveshape_cuboid, list(spec.size), 0)
    except Exception as exc:
        try:
            handle = sim.createPureShape(0, 8, list(spec.size), max(float(spec.mass_kg), 0.001), [])
        except Exception as pure_exc:
            raise RuntimeError(f"Failed to create box {spec.name} with size={spec.size!r}") from pure_exc
    set_alias(sim, handle, spec.name)
    sim.setObjectPosition(handle, -1, list(spec.center))
    sim.setObjectOrientation(handle, -1, [0.0, 0.0, spec.yaw_rad])
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, list(spec.color))
    set_shape_physics(sim, handle, static=spec.static, respondable=spec.respondable, mass_kg=spec.mass_kg)
    set_shape_render_props(sim, handle)
    return handle


def add_cylinder(
    sim,
    name: str,
    radius: float,
    height: float,
    position: tuple[float, float, float],
    color: tuple[float, float, float],
) -> int:
    try:
        handle = sim.createPrimitiveShape(sim.primitiveshape_cylinder, [radius * 2.0, radius * 2.0, height], 0)
    except Exception as exc:
        try:
            handle = sim.createPureShape(2, 8, [radius * 2.0, radius * 2.0, height], 0.001, [])
        except Exception as pure_exc:
            raise RuntimeError(f"Failed to create cylinder {name} radius={radius!r} height={height!r}") from pure_exc
    set_alias(sim, handle, name)
    sim.setObjectPosition(handle, -1, list(position))
    sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, list(color))
    set_shape_physics(sim, handle, static=True, respondable=False, mass_kg=0.001)
    set_shape_render_props(sim, handle)
    return handle


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
    try:
        props = sim.getObjectSpecialProperty(handle)
        renderable = getattr(sim, "objectspecialproperty_renderable", 0x0200)
        sim.setObjectSpecialProperty(handle, props | renderable)
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
        sim.setNamedStringParam("mrbo_aws_canonical_scene_json", payload)
    except Exception:
        pass
    try:
        sim.writeCustomStringData(sim.handle_scene, "MRBO_AWS_CANONICAL", payload)
    except Exception:
        pass


def render_lua_scene(scene: dict[str, Any]) -> str:
    json_blob = json.dumps(scene, indent=2)
    lua_scene = lua_table(scene)
    demo_script = render_demo_script(scene)
    template = """-- Auto-generated by scripts/coppelia/build_aws_canonical_scene.py
-- Scenario: __SCENARIO__
-- Usage:
--   1. Open CoppeliaSim.
--   2. Open __BASE_SCENE__
--   3. Run: dofile([[__LUA_PATH__]])
-- The Python generator can also export a .ttt file directly through ZMQ.

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

local function configureRendering()
    pcall(sim.setBoolParam, sim.boolparam_shape_textures_are_visible, true)
    pcall(sim.setArrayParam, sim.arrayparam_background_color1, {0.82, 0.86, 0.90})
    pcall(sim.setArrayParam, sim.arrayparam_background_color2, {0.72, 0.76, 0.82})
    pcall(sim.setArrayParam, sim.arrayparam_ambient_light, {0.55, 0.55, 0.55})
end

local function prepareAwsReference()
    local ok, warehouse = pcall(sim.getObject, '/warehouse')
    if not ok or not warehouse then return end
    for _, handle in ipairs(sim.getObjectsInTree(warehouse, sim.handle_all, 0)) do
        pcall(sim.setObjectInt32Param, handle, sim.objintparam_visibility_layer, 0)
        if sim.getObjectType(handle) == sim.object_shape_type then
            local props = sim.getObjectSpecialProperty(handle)
            local renderable = sim.objectspecialproperty_renderable or 0x0200
            pcall(sim.setObjectSpecialProperty, handle, bit32.band(bit32.bor(props, renderable), bit32.bnot(sim.objectspecialproperty_collidable)))
            pcall(sim.setObjectInt32Param, handle, sim.shapeintparam_static, 1)
            pcall(sim.setObjectInt32Param, handle, sim.shapeintparam_respondable, 0)
        end
    end
end

local function makeModelVisualOnly(handle)
    for _, child in ipairs(sim.getObjectsInTree(handle, sim.handle_all, 0)) do
        if sim.getObjectType(child) == sim.object_shape_type then
            local props = sim.getObjectSpecialProperty(child)
            local renderable = sim.objectspecialproperty_renderable or 0x0200
            pcall(sim.setObjectSpecialProperty, child, bit32.band(bit32.bor(props, renderable), bit32.bnot(sim.objectspecialproperty_collidable)))
            pcall(sim.setObjectInt32Param, child, sim.shapeintparam_static, 1)
            pcall(sim.setObjectInt32Param, child, sim.shapeintparam_respondable, 0)
        end
    end
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

local function scaleModel(handle, scale)
    pcall(sim.scaleModelNonIsometrically, handle, scale[1], scale[2], scale[3])
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

local function cylinder(name, radius, height, pos, color)
    local h = sim.createPrimitiveShape(sim.primitiveshape_cylinder, {radius * 2, radius * 2, height}, 0)
    setAlias(h, name)
    sim.setObjectPosition(h, -1, pos)
    sim.setShapeColor(h, nil, sim.colorcomponent_ambient_diffuse, color)
    setPhysics(h, true, false, 0.001)
    return h
end

local function modelOrFallback(path, name, pos, yaw, fallbackSize, fallbackColor, orientation, scale, keepScripts)
    local ok, handle = pcall(sim.loadModel, path)
    if ok and handle and handle >= 0 then
        setAlias(handle, name)
        if scale then scaleModel(handle, scale) end
        if not keepScripts then
            disableModelScripts(handle)
            makeModelVisualOnly(handle)
        end
        sim.setObjectPosition(handle, -1, pos)
        sim.setObjectOrientation(handle, -1, orientation or {0, 0, yaw or 0})
        return handle
    end
    return box(name .. '_fallback', fallbackSize, pos, fallbackColor, yaw or 0, true, true, 0.001)
end

local function zone(z)
    local sx, sy = z.size[1], z.size[2]
    local x, y = z.center[1], z.center[2]
    local z0 = 0.052
    local border = 0.045
    box(z.name .. '_north_line', {sx, border, 0.018}, {x, y + sy / 2, z0}, z.color, 0, true, false)
    box(z.name .. '_south_line', {sx, border, 0.018}, {x, y - sy / 2, z0}, z.color, 0, true, false)
    box(z.name .. '_east_line', {border, sy, 0.018}, {x + sx / 2, y, z0}, z.color, 0, true, false)
    box(z.name .. '_west_line', {border, sy, 0.018}, {x - sx / 2, y, z0}, z.color, 0, true, false)
    local corner = math.min(0.34, sx * 0.18, sy * 0.26)
    local corners = {
        {x - sx / 2 + corner / 2, y + sy / 2 - corner / 2, 0},
        {x + sx / 2 - corner / 2, y + sy / 2 - corner / 2, math.pi / 2},
        {x + sx / 2 - corner / 2, y - sy / 2 + corner / 2, math.pi},
        {x - sx / 2 + corner / 2, y - sy / 2 + corner / 2, -math.pi / 2},
    }
    for idx, c in ipairs(corners) do
        box(z.name .. '_corner_' .. idx .. '_a', {corner, border * 1.15, 0.018}, {c[1], c[2], z0 + 0.006}, z.color, c[3], true, false)
        box(z.name .. '_corner_' .. idx .. '_b', {border * 1.15, corner, 0.018}, {c[1], c[2], z0 + 0.007}, z.color, c[3], true, false)
    end
    if z.kind == 'delivery' or z.kind == 'recharge' then
        box(z.name .. '_subtle_pad', {sx * 0.64, sy * 0.50, 0.010}, {x, y, 0.035}, {z.color[1] * 0.78, z.color[2] * 0.78, z.color[3] * 0.78}, 0, true, false)
    end
end

local function route(name, pts)
    for i = 1, #pts - 1 do
        local ax, ay = pts[i][1], pts[i][2]
        local bx, by = pts[i + 1][1], pts[i + 1][2]
        local dx, dy = bx - ax, by - ay
        local len = math.sqrt(dx * dx + dy * dy)
        if len > 0.01 then
            local yaw = math.atan2(dy, dx)
            local ux, uy = dx / len, dy / len
            local count = math.max(1, math.floor(len / 0.70))
            for j = 1, count do
                local dist = math.min(len - 0.19, (j - 1) * 0.70 + 0.19)
                if dist > 0.18 then
                    box(name .. '_dash_' .. i .. '_' .. j, {0.38, 0.035, 0.025}, {ax + ux * dist, ay + uy * dist, 0.065}, {0.92, 0.92, 0.86}, yaw, true, false)
                end
            end
        end
    end
end

local function rotateOffset(x, y, yaw)
    return x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
end

local function conveyor(name, pos, yaw)
    modelOrFallback(scene.model_paths.conveyor, name, pos, yaw, {1.30, 0.45, 0.16}, {0.13, 0.14, 0.14})
end

local function bollard(name, x, y)
    cylinder(name, 0.055, 0.55, {x, y, 0.275}, {0.94, 0.67, 0.08})
    box(name .. '_black_band_1', {0.13, 0.018, 0.045}, {x, y, 0.23}, {0.04, 0.04, 0.04}, 0, true, false)
    box(name .. '_black_band_2', {0.13, 0.018, 0.045}, {x, y, 0.39}, {0.04, 0.04, 0.04}, 0, true, false)
end

local function guardrail(name, x, y, length, yaw)
    box(name .. '_rail_top', {length, 0.055, 0.070}, {x, y, 0.52}, {0.94, 0.67, 0.08}, yaw, true, false)
    box(name .. '_rail_mid', {length, 0.050, 0.060}, {x, y, 0.34}, {0.94, 0.67, 0.08}, yaw, true, false)
    for idx, offset in ipairs({-length / 2, 0.0, length / 2}) do
        local px, py = rotateOffset(offset, 0.0, yaw)
        box(name .. '_post_' .. idx, {0.065, 0.065, 0.50}, {x + px, y + py, 0.28}, {0.08, 0.08, 0.07}, yaw, true, false)
    end
end

local function safetyHardware()
    local o = scene.central_obstacle
    local x, y = o.position[1], o.position[2]
    local sx, sy = o.size[1], o.size[2]
    local points = {
        {x - sx / 2 - 0.18, y - sy / 2 - 0.18},
        {x + sx / 2 + 0.18, y - sy / 2 - 0.18},
        {x - sx / 2 - 0.18, y + sy / 2 + 0.18},
        {x + sx / 2 + 0.18, y + sy / 2 + 0.18},
    }
    for idx, p in ipairs(points) do bollard('obstaculo_central_bollard_' .. idx, p[1], p[2]) end
    for _, z in ipairs(scene.zones) do
        if z.kind == 'pickup' then
            guardrail(z.name .. '_rear_guardrail', z.center[1], z.center[2] - z.size[2] / 2 - 0.16, z.size[1] * 0.72, 0)
        end
    end
end

local function rackBlock(r)
    local x, y, yaw = r.position[1], r.position[2], r.yaw_rad
    local sx, sy, sz = r.size[1], r.size[2], r.size[3]
    box(r.name .. '_footprint', {sx, sy, 0.12}, {x, y, 0.14}, {0.08, 0.11, 0.13}, yaw, true, true)
    local uprightColor = {0.04, 0.17, 0.27}
    local beamColor = {0.94, 0.56, 0.10}
    local shelfColor = {0.27, 0.30, 0.32}
    local palletColor = {0.60, 0.40, 0.22}
    for idx, p in ipairs({{-sx / 2, -sy / 2}, {-sx / 2, sy / 2}, {sx / 2, -sy / 2}, {sx / 2, sy / 2}}) do
        local px, py = rotateOffset(p[1], p[2], yaw)
        box(r.name .. '_upright_' .. idx, {0.055, 0.055, sz}, {x + px, y + py, sz / 2}, uprightColor, yaw, true, false)
    end
    for levelIdx, levelZ in ipairs({0.42, 0.86, 1.30, 1.74}) do
        for sideIdx, oy in ipairs({-sy / 2, sy / 2}) do
            local px, py = rotateOffset(0, oy, yaw)
            box(r.name .. '_beam_L' .. levelIdx .. '_' .. sideIdx, {sx + 0.08, 0.05, 0.07}, {x + px, y + py, levelZ}, beamColor, yaw, true, false)
        end
        box(r.name .. '_shelf_deck_L' .. levelIdx, {sx * 0.96, sy * 0.82, 0.035}, {x, y, levelZ - 0.06}, shelfColor, yaw, true, false)
    end
    local cartonColors = {{0.72, 0.52, 0.30}, {0.62, 0.46, 0.28}, {0.80, 0.62, 0.38}}
    for levelSlot, cartonZ in ipairs({0.62, 1.06, 1.50}) do
        for idx, offset in ipairs({-0.30, 0.0, 0.30}) do
            local px, py = rotateOffset(offset * sx, 0, yaw)
            if levelSlot == 1 then
                box(r.name .. '_pallet_' .. idx, {math.min(0.36, sx / 3.5), sy * 0.70, 0.12}, {x + px, y + py, 0.49}, palletColor, yaw, true, false)
            end
            local c = cartonColors[((idx + levelSlot - 2) % #cartonColors) + 1]
            box(r.name .. '_carton_L' .. levelSlot .. '_' .. idx, {math.min(0.32, sx / 3.8), sy * 0.62, 0.24}, {x + px, y + py, cartonZ}, c, yaw, true, false)
        end
    end
    local lx, ly = rotateOffset(-sx / 2 + 0.12, -sy / 2 - 0.028, yaw)
    box(r.name .. '_barcode_label', {0.20, 0.012, 0.09}, {x + lx, y + ly, 1.88}, {0.92, 0.92, 0.86}, yaw, true, false)
end

local function installDemoScript()
    local scriptText = [==[__DEMO_SCRIPT__]==]
    local dummy = setAlias(sim.createDummy(0.03), 'MRBO_demo_controller')
    if sim.getBoolParam(sim.boolparam_usingscriptobjects) then
        local s = sim.createScript(sim.scripttype_simulation, scriptText, 0, 'lua')
        sim.setObjectParent(s, dummy)
    else
        local s = sim.addScript(sim.scripttype_simulation)
        sim.associateScriptWithObject(s, dummy)
        sim.setScriptText(s, scriptText)
    end
end

sim.setNamedStringParam('mrbo_aws_canonical_scene_json', [==[__JSON__]==])
configureRendering()
prepareAwsReference()
setAlias(sim.createDummy(0.05), 'MRBO_AWS_CANONICAL_OVERLAY')

box('canonical_concrete_floor_12x10', {12.0, 10.0, 0.05}, {0, 0, -0.025}, {0.42, 0.43, 0.42}, 0, true, true)
for ix = 0, 11 do
    for iy = 0, 9 do
        local shade = 0.44 + 0.018 * (((ix * 17 + iy * 11) % 5) - 2)
        box('floor_concrete_panel_' .. ix .. '_' .. iy, {0.96, 0.96, 0.010}, {-5.5 + ix, -4.5 + iy, 0.006}, {shade, shade + 0.008, shade + 0.010}, 0, true, false)
    end
end
for i = -5, 5 do box('floor_tile_seam_x_' .. i, {0.018, 10.0, 0.012}, {i, 0, 0.012}, {0.30, 0.31, 0.31}, 0, true, false) end
for i = -4, 4 do box('floor_tile_seam_y_' .. i, {12.0, 0.018, 0.012}, {0, i, 0.014}, {0.30, 0.31, 0.31}, 0, true, false) end
box('aisle_main_lane_yellow_left', {9.8, 0.045, 0.018}, {0, -0.95, 0.035}, {0.92, 0.78, 0.18}, 0, true, false)
box('aisle_main_lane_yellow_right', {9.8, 0.045, 0.018}, {0, 0.95, 0.035}, {0.92, 0.78, 0.18}, 0, true, false)
box('aisle_cross_lane_yellow_north', {0.045, 6.2, 0.018}, {-3.0, 1.55, 0.035}, {0.92, 0.78, 0.18}, 0, true, false)
box('aisle_cross_lane_yellow_south', {0.045, 6.2, 0.018}, {3.0, -1.55, 0.035}, {0.92, 0.78, 0.18}, 0, true, false)
box('canonical_wall_north', {12.25, 0.12, 1.24}, {0, 5.06, 0.62}, {0.62, 0.64, 0.64}, 0, true, true)
box('canonical_wall_south', {12.25, 0.12, 1.24}, {0, -5.06, 0.62}, {0.62, 0.64, 0.64}, 0, true, true)
box('canonical_wall_east', {0.12, 10.25, 1.24}, {6.06, 0, 0.62}, {0.62, 0.64, 0.64}, 0, true, true)
box('canonical_wall_west', {0.12, 10.25, 1.24}, {-6.06, 0, 0.62}, {0.62, 0.64, 0.64}, 0, true, true)
for idx, x in ipairs({-3.5, 0.0, 3.5}) do
    box('dock_door_north_' .. idx, {1.35, 0.035, 0.82}, {x, 4.988, 0.48}, {0.18, 0.22, 0.24}, 0, true, false)
    box('dock_header_north_' .. idx, {1.47, 0.045, 0.08}, {x, 4.970, 0.93}, {0.88, 0.55, 0.12}, 0, true, false)
end
for idx, y in ipairs({-3.0, 0.0, 3.0}) do
    box('east_service_panel_' .. idx, {0.035, 1.15, 0.70}, {5.988, y, 0.55}, {0.18, 0.22, 0.24}, 0, true, false)
end
for _, p in ipairs({{-3.6, -3.0}, {0, -3.0}, {3.6, -3.0}, {-3.6, 1.2}, {0, 1.2}, {3.6, 1.2}}) do
    box('overhead_light_panel_' .. tostring(_), {1.05, 0.26, 0.035}, {p[1], p[2], 2.85}, {0.96, 0.96, 0.82}, 0, true, false)
end
box('canonical_12m_frame_north', {12.0, 0.05, 0.08}, {0, 5.0, 0.08}, {0.08, 0.08, 0.08}, 0, true, true)
box('canonical_12m_frame_south', {12.0, 0.05, 0.08}, {0, -5.0, 0.08}, {0.08, 0.08, 0.08}, 0, true, true)
box('canonical_10m_frame_east', {0.05, 10.0, 0.08}, {6.0, 0, 0.08}, {0.08, 0.08, 0.08}, 0, true, true)
box('canonical_10m_frame_west', {0.05, 10.0, 0.08}, {-6.0, 0, 0.08}, {0.08, 0.08, 0.08}, 0, true, true)

for _, z in ipairs(scene.zones) do zone(z) end
for _, r in ipairs(scene.racks) do rackBlock(r) end
box(scene.central_obstacle.name, scene.central_obstacle.size, scene.central_obstacle.position, {0.44, 0.44, 0.44}, 0, true, true)
safetyHardware()

for label, station in pairs({a = scene.stations.pickup_a, b = scene.stations.pickup_b}) do
    local px, py = station.conveyor_position[1], station.conveyor_position[2]
    local sx, sy = station.source_platform_position[1], station.source_platform_position[2]
    local hx, hy, hz = station.handoff_position[1], station.handoff_position[2], station.handoff_position[3]
    box('zona_recogida_' .. label .. '_source_table', {0.72, 0.52, 0.78}, {sx, sy, 0.39}, {0.20, 0.22, 0.22}, 0, true, true)
    box('zona_recogida_' .. label .. '_source_table_top', {0.76, 0.56, 0.055}, {sx, sy, 0.79}, {0.66, 0.67, 0.64}, 0, true, true)
    box('zona_recogida_' .. label .. '_handoff_table', {0.62, 0.52, math.max(hz, 0.08)}, {hx, hy, hz / 2}, {0.18, 0.21, 0.23}, 0, true, true)
    box('zona_recogida_' .. label .. '_handoff_table_top', {0.66, 0.56, 0.05}, {hx, hy, hz + 0.025}, {0.62, 0.64, 0.62}, 0, true, true)
    box('zona_recogida_' .. label .. '_conveyor_guard_left', {1.48, 0.035, 0.26}, {px, py - 0.31, 0.50}, {0.92, 0.70, 0.10}, 0, true, false)
    box('zona_recogida_' .. label .. '_conveyor_guard_right', {1.48, 0.035, 0.26}, {px, py + 0.31, 0.50}, {0.92, 0.70, 0.10}, 0, true, false)
    local mx, my = station.manipulator_position[1], station.manipulator_position[2]
    box('zona_recogida_' .. label .. '_robot_pedestal', {0.68, 0.68, 0.20}, {mx, my, 0.10}, {0.18, 0.20, 0.22}, 0, true, true)
end
conveyor('zona_recogida_a_conveyor_model', scene.stations.pickup_a.conveyor_position, 0)
conveyor('zona_recogida_b_conveyor_model', scene.stations.pickup_b.conveyor_position, 0)
modelOrFallback(scene.model_paths.manipulator, 'zona_recogida_a_manipulador_model', scene.stations.pickup_a.manipulator_position, 0, {0.35, 0.35, 0.12}, {0.95, 0.65, 0.05})
modelOrFallback(scene.model_paths.manipulator, 'zona_recogida_b_manipulador_model', scene.stations.pickup_b.manipulator_position, math.pi, {0.35, 0.35, 0.12}, {0.95, 0.65, 0.05})
box('zona_entrega_1_plataforma_verde', {0.72, 0.52, 0.08}, scene.stations.delivery_1_marker, {0.08, 0.62, 0.28}, 0, true, true)
box('zona_entrega_2_plataforma_verde', {0.72, 0.52, 0.08}, scene.stations.delivery_2_marker, {0.08, 0.62, 0.28}, 0, true, true)
box('zona_recarga_pad_rojo', {0.80, 0.62, 0.08}, scene.stations.recharge_marker, {0.90, 0.12, 0.08}, 0, true, true)

for _, load in ipairs(scene.loads) do
    local color = {0.62, 0.64, 0.60}
    if load.station == 'pickup_a' then color = {0.55, 0.61, 0.64} end
    if load.station == 'pickup_b' then color = {0.60, 0.60, 0.54} end
    local h = box(load.name, load.size, load.position, color, 0, true, false, math.max(load.weight_kg, 0.001))
    local sx, sy, sz = load.size[1], load.size[2], load.size[3]
    for idx, dy in ipairs({-sy / 2 - 0.006, sy / 2 + 0.006}) do
        local detail = box(load.name .. '_handle_' .. idx, {sx * 0.42, 0.010, sz * 0.28}, {load.position[1], load.position[2] + dy, load.position[3] + 0.02}, {0.08, 0.09, 0.09}, 0, true, false)
        pcall(sim.setObjectParent, detail, h, true)
    end
    local label = box(load.name .. '_label', {0.010, sy * 0.46, sz * 0.34}, {load.position[1] + sx / 2 + 0.006, load.position[2], load.position[3] + 0.02}, {0.92, 0.92, 0.84}, 0, true, false)
    pcall(sim.setObjectParent, label, h, true)
    local marker = sim.createDummy(0.06)
    setAlias(marker, load.name .. '_requires_' .. load.required_agvs .. '_agv')
    sim.setObjectPosition(marker, -1, {load.position[1], load.position[2], load.position[3] + load.size[3] / 2 + 0.08})
    pcall(sim.setObjectParent, marker, h, true)
end
for _, r in ipairs(scene.routes) do route(r.name, r.points) end
for _, robot in ipairs(scene.robots) do
    local ok, handle = pcall(sim.loadModel, scene.model_paths.pioneer_p3dx)
    if ok and handle and handle >= 0 then
        disableModelScripts(handle)
        makeModelVisualOnly(handle)
    else
        handle = cylinder(robot.name .. '_fallback_base', 0.28, 0.30, robot.position, {0.12, 0.12, 0.12})
    end
    setAlias(handle, robot.name)
    sim.setObjectPosition(handle, -1, robot.position)
    sim.setObjectOrientation(handle, -1, {0, 0, robot.heading_rad})
    local marker = cylinder(robot.name .. '_tipo_' .. robot.class, 0.12, 0.035, {robot.position[1], robot.position[2], robot.position[3] + 0.22}, {0.92, 0.72, 0.05})
    pcall(sim.setObjectParent, marker, handle, true)
    local comm = sim.createDummy(0.08)
    setAlias(comm, robot.name .. '_radio_local_R')
    sim.setObjectPosition(comm, -1, {robot.position[1], robot.position[2], robot.position[3] + 0.34})
    pcall(sim.setObjectParent, comm, handle, true)
end

local top = sim.createVisionSensor(1 + 4, {1280, 960, 0, 0}, {0.05, 40.0, 11.2, 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0})
setAlias(top, 'MRBO_camera_top_canonical')
sim.setExplicitHandling(top, 1)
sim.setObjectInt32Param(top, sim.visionintparam_perspective_operation, 0)
sim.setObjectFloatParam(top, sim.visionfloatparam_ortho_size, 11.0)
sim.setObjectPosition(top, -1, {0.0, 0.0, 12.5})
sim.setObjectOrientation(top, -1, {0.0, math.pi, 0.0})
local oblique = sim.createVisionSensor(1 + 4, {1280, 960, 0, 0}, {0.05, 40.0, math.rad(86), 0.5, 0.0, 0.0, 0.88, 0.90, 0.93, 0.0, 0.0})
setAlias(oblique, 'MRBO_camera_oblique_canonical')
sim.setExplicitHandling(oblique, 1)
sim.setObjectPosition(oblique, -1, {0.0, 0.0, 12.4})
sim.setObjectOrientation(oblique, -1, {0.0, math.pi, 0.0})
installDemoScript()
sim.addLog(sim.verbosity_scriptinfos, 'MRBO AWS canonical cooperative transport scene generated with visible AWS reference, stable physics and embedded motion.')
"""
    return (
        template.replace("__SCENARIO__", scene["scenario"])
        .replace("__BASE_SCENE__", str(scene["base_scene"]))
        .replace("__LUA_PATH__", str((ROOT / "coppeliasim/real_scenes/aws_canonical_coop_transport_pioneer_p3dx.lua").resolve()))
        .replace("__SCENE__", lua_scene)
        .replace("__JSON__", json_blob)
        .replace("__DEMO_SCRIPT__", demo_script)
    )


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


def unique_backup_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for idx in range(1, 1000):
        candidate = path.with_name(f"{stem}_{idx:03d}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not allocate a unique backup path for {path}")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
