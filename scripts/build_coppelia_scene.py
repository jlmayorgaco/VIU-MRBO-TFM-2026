"""Generate deterministic CoppeliaSim warehouse scenes from YAML/JSON.

The generated Lua files are meant to be run inside CoppeliaSim with:

```
sim.removeObjects(sim.getObjectsInTree(sim.handle_scene))
dofile("coppeliasim/scenes/nominal_smith_qr.lua")
```

The script does not require CoppeliaSim to be installed. It produces editable scene
recipes, Lua builders, a manifest and offline geometry metrics that can be versioned.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SceneSpec:
    name: str
    policy: str
    communication_radius: float
    packet_loss: float
    robots: int
    racks: int
    humans: int
    sensor_degradation: float
    robot_failure: bool = False
    playback_csv: str = ""


DEFAULT_SCENES = (
    SceneSpec("nominal_smith_qr", "smith_qr_full", 12.0, 0.0, 15, 18, 2, 0.0),
    SceneSpec("comm_r3_smith", "smith_full", 3.0, 0.0, 15, 18, 2, 0.0),
    SceneSpec("comm_r3_smith_qr", "smith_qr_full", 3.0, 0.0, 15, 18, 2, 0.0),
    SceneSpec("robot_failure_smith_qr", "smith_qr_full", 4.0, 0.0, 15, 18, 2, 0.0, robot_failure=True),
    SceneSpec("human_crossing_smith_qr", "smith_qr_full", 4.0, 0.0, 15, 18, 6, 0.0),
    SceneSpec("sensor_degraded_smith_qr", "smith_qr_full", 4.0, 0.0, 15, 18, 4, 0.55),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Optional YAML/JSON scene config.")
    parser.add_argument("--scene-dir", type=Path, default=Path("coppeliasim/scenes"))
    parser.add_argument("--out", type=Path, default=Path("results/coppeliasim_validation"))
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scene_dir = _resolve(args.scene_dir)
    out_dir = _resolve(args.out)
    scene_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = _load_specs(args.config) if args.config else DEFAULT_SCENES

    manifest_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        scenario = build_scene_dict(spec, seed=args.seed + index)
        yaml_path = scene_dir / f"{spec.name}.yaml"
        lua_path = scene_dir / f"{spec.name}.lua"
        yaml_path.write_text(yaml.safe_dump(scenario, sort_keys=False, allow_unicode=False), encoding="utf-8")
        lua_path.write_text(render_lua_scene(scenario), encoding="utf-8")
        metrics = offline_metrics(scenario)
        metric_rows.append({"scene": spec.name, **metrics})
        manifest_rows.append(
            {
                "scene": spec.name,
                "policy": spec.policy,
                "communication_radius": spec.communication_radius,
                "packet_loss": spec.packet_loss,
                "robots": spec.robots,
                "racks": spec.racks,
                "humans": spec.humans,
                "sensor_degradation": spec.sensor_degradation,
                "robot_failure": spec.robot_failure,
                "yaml": str(yaml_path.relative_to(ROOT)),
                "lua": str(lua_path.relative_to(ROOT)),
                "status": "generated_not_opened",
            }
        )

    write_csv(out_dir / "scene_manifest.csv", manifest_rows)
    write_csv(out_dir / "scene_metrics.csv", metric_rows)
    write_readme(out_dir / "README.md", scene_dir, out_dir, manifest_rows)
    return 0


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_specs(path: Path | None) -> tuple[SceneSpec, ...]:
    if path is None:
        return DEFAULT_SCENES
    resolved = _resolve(path)
    text = resolved.read_text(encoding="utf-8")
    data = json.loads(text) if resolved.suffix.lower() == ".json" else yaml.safe_load(text)
    items = data.get("scenes", data if isinstance(data, list) else [])
    return tuple(SceneSpec(**item) for item in items)


def build_scene_dict(spec: SceneSpec, seed: int) -> dict[str, Any]:
    width = 36.0
    depth = 24.0
    racks = rack_layout(spec.racks, width, depth)
    robots = robot_layout(spec.robots, width, depth)
    loads = load_layout(width, depth)
    humans = human_layout(spec.humans, width, depth)
    sensors = {
        "lidar_range_m": 6.0 * (1.0 - 0.55 * spec.sensor_degradation),
        "proximity_range_m": 2.0 * (1.0 - 0.45 * spec.sensor_degradation),
        "load_detection_range_m": 1.4 * (1.0 - 0.40 * spec.sensor_degradation),
        "blind_zones": blind_zones(width, depth) if spec.sensor_degradation > 0.0 else [],
    }
    return {
        "scenario": spec.name,
        "seed": seed,
        "warehouse": {
            "width_m": width,
            "depth_m": depth,
            "floor_thickness_m": 0.08,
            "style": "industrial fulfillment center without proprietary branding",
            "safety_markings": True,
        },
        "controller": {
            "policy": spec.policy,
            "playback_csv": spec.playback_csv,
            "closed_loop_topic": "python_policy_cmd_vel",
        },
        "communication": {
            "radius_m": spec.communication_radius,
            "packet_loss": spec.packet_loss,
            "show_links": True,
        },
        "robots": robots,
        "racks": racks,
        "loads": loads,
        "humans": humans,
        "sensors": sensors,
        "events": {
            "robot_failure": {"enabled": spec.robot_failure, "robot": "Pioneer_03", "time_s": 90.0},
            "forklift_crossing": {"enabled": spec.humans >= 4, "time_s": 120.0},
        },
    }


def rack_layout(count: int, width: float, depth: float) -> list[dict[str, Any]]:
    racks: list[dict[str, Any]] = []
    columns = 6
    rows = max(1, math.ceil(count / columns))
    x0 = -width / 2 + 5.0
    y0 = -depth / 2 + 4.5
    for idx in range(count):
        col = idx % columns
        row = idx // columns
        racks.append(
            {
                "name": f"Rack_{idx + 1:02d}",
                "position": [round(x0 + col * 5.2, 3), round(y0 + row * 6.0, 3), 1.5],
                "size": [3.8, 0.9, 3.0],
                "aisle": row,
            }
        )
    return racks


def robot_layout(count: int, width: float, depth: float) -> list[dict[str, Any]]:
    robots: list[dict[str, Any]] = []
    per_row = max(count, 1)
    start_x = -width / 2 + 3.0
    spacing = min(2.1, (width - 6.0) / max(count - 1, 1))
    start_y = -depth / 2 + 1.2
    for idx in range(count):
        robots.append(
            {
                "name": f"Pioneer_{idx + 1:02d}",
                "model": "Pioneer 3-DX",
                "position": [round(start_x + (idx % per_row) * spacing, 3), round(start_y + (idx // per_row) * 1.6, 3), 0.18],
                "heading_rad": 0.0,
                "sensors": ["front_proximity", "lidar_2d", "load_detector", "local_comm"],
            }
        )
    return robots


def load_layout(width: float, depth: float) -> list[dict[str, Any]]:
    return [
        {"name": "Load_heavy_01", "position": [-width / 2 + 2.5, -depth / 2 + 7.0, 0.35], "size": [1.0, 0.8, 0.5], "weight": 10},
        {"name": "Load_medium_01", "position": [width / 2 - 3.0, -depth / 2 + 8.0, 0.35], "size": [0.8, 0.7, 0.45], "weight": 6},
        {"name": "Load_light_01", "position": [-width / 2 + 4.0, depth / 2 - 4.0, 0.25], "size": [0.55, 0.45, 0.35], "weight": 2},
    ]


def human_layout(count: int, width: float, depth: float) -> list[dict[str, Any]]:
    humans: list[dict[str, Any]] = []
    for idx in range(count):
        y = -depth / 2 + 7.0 + (idx % 3) * 4.2
        start = [-width / 2 + 0.7, y, 0.9]
        end = [width / 2 - 1.5, y + 1.0, 0.9]
        humans.append(
            {
                "name": f"Operator_{idx + 1:02d}",
                "position": [round(start[0], 3), round(start[1], 3), start[2]],
                "route": [start, end],
                "speed_mps": 0.75,
            }
        )
    return humans


def blind_zones(width: float, depth: float) -> list[dict[str, Any]]:
    return [
        {"name": "BlindZone_RackA", "center": [-width / 4, 0.0, 0.05], "size": [4.0, 2.0, 0.05]},
        {"name": "BlindZone_RackB", "center": [width / 4, 4.0, 0.05], "size": [5.0, 2.5, 0.05]},
    ]


def render_lua_scene(scene: dict[str, Any]) -> str:
    json_blob = json.dumps(scene, indent=2)
    return f"""-- Auto-generated by scripts/build_coppelia_scene.py
-- Scenario: {scene['scenario']}
local scene = {lua_table(scene)}

local function setName(handle, name)
    if handle and handle >= 0 then sim.setObjectAlias(handle, name, 1) end
    return handle
end

local function cuboid(name, size, pos, color)
    local h = sim.createPureShape(0, 8, size, 0.1, nil)
    setName(h, name)
    sim.setObjectPosition(h, -1, pos)
    if color then sim.setShapeColor(h, nil, sim.colorcomponent_ambient_diffuse, color) end
    return h
end

local function cylinder(name, radius, height, pos, color)
    local h = sim.createPureShape(2, 8, {{radius * 2.0, radius * 2.0, height}}, 0.1, nil)
    setName(h, name)
    sim.setObjectPosition(h, -1, pos)
    if color then sim.setShapeColor(h, nil, sim.colorcomponent_ambient_diffuse, color) end
    return h
end

local function tryLoadPioneer(robot)
    local candidates = {{
        sim.getStringParam(sim.stringparam_systemdir) .. '/models/robots/mobile/Pioneer p3dx.ttm',
        sim.getStringParam(sim.stringparam_systemdir) .. '/models/robots/mobile/Pioneer P3-DX.ttm',
        sim.getStringParam(sim.stringparam_systemdir) .. '/models/robots/mobile/Pioneer 3-DX.ttm'
    }}
    for _, path in ipairs(candidates) do
        local ok, handle = pcall(sim.loadModel, path)
        if ok and handle and handle >= 0 then
            setName(handle, robot.name)
            sim.setObjectPosition(handle, -1, robot.position)
            sim.setObjectOrientation(handle, -1, {{0, 0, robot.heading_rad}})
            return handle
        end
    end
    local base = cylinder(robot.name .. '_Pioneer3DX_fallback', 0.28, 0.32, robot.position, {{0.10, 0.22, 0.34}})
    cuboid(robot.name .. '_sensor_bar', {{0.48, 0.06, 0.06}}, {{robot.position[1], robot.position[2] + 0.22, robot.position[3] + 0.23}}, {{0.03, 0.10, 0.16}})
    return base
end

local function addDummy(name, pos)
    local h = sim.createDummy(0.08)
    setName(h, name)
    sim.setObjectPosition(h, -1, pos)
    return h
end

sim.setNamedStringParam('mrbo_scene_json', [==[{json_blob}]==])

cuboid('Warehouse_floor', {{scene.warehouse.width_m, scene.warehouse.depth_m, scene.warehouse.floor_thickness_m}}, {{0, 0, -scene.warehouse.floor_thickness_m / 2}}, {{0.46, 0.48, 0.49}})
cuboid('Inbound_station', {{3.0, 2.0, 0.08}}, {{-scene.warehouse.width_m / 2 + 2.0, -scene.warehouse.depth_m / 2 + 2.0, 0.03}}, {{0.10, 0.40, 0.70}})
cuboid('Outbound_station', {{3.0, 2.0, 0.08}}, {{scene.warehouse.width_m / 2 - 2.0, scene.warehouse.depth_m / 2 - 2.0, 0.03}}, {{0.10, 0.55, 0.25}})

for _, rack in ipairs(scene.racks) do
    cuboid(rack.name, rack.size, rack.position, {{0.42, 0.44, 0.46}})
end

for _, load in ipairs(scene.loads) do
    cuboid(load.name .. '_w' .. tostring(load.weight), load.size, load.position, {{0.85, 0.58, 0.20}})
end

for _, robot in ipairs(scene.robots) do
    local handle = tryLoadPioneer(robot)
    addDummy(robot.name .. '_lidar_2d_range_' .. tostring(scene.sensors.lidar_range_m), {{robot.position[1], robot.position[2], robot.position[3] + 0.35}})
    addDummy(robot.name .. '_local_comm_R' .. tostring(scene.communication.radius_m), {{robot.position[1], robot.position[2], robot.position[3] + 0.55}})
end

for _, human in ipairs(scene.humans) do
    cylinder(human.name, 0.22, 1.8, human.position, {{0.78, 0.20, 0.18}})
    addDummy(human.name .. '_route_start', human.route[1])
    addDummy(human.name .. '_route_end', human.route[2])
end

for _, zone in ipairs(scene.sensors.blind_zones) do
    cuboid(zone.name, zone.size, zone.center, {{0.80, 0.10, 0.10}})
end

if scene.events.robot_failure.enabled then
    addDummy('Robot_failure_event_' .. scene.events.robot_failure.robot .. '_t' .. tostring(scene.events.robot_failure.time_s), {{0, 0, 1.2}})
end

sim.addLog(sim.verbosity_scriptinfos, 'MRBO warehouse scene generated: ' .. scene.scenario .. ' policy=' .. scene.controller.policy)
"""


def lua_table(value: Any) -> str:
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.append(f"{key} = {lua_table(item)}")
        return "{\n" + ",\n".join(parts) + "\n}"
    if isinstance(value, list):
        return "{" + ", ".join(lua_table(item) for item in value) + "}"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "nil"
    return repr(value)


def offline_metrics(scene: dict[str, Any]) -> dict[str, Any]:
    robot_positions = [item["position"] for item in scene["robots"]]
    human_positions = [item["position"] for item in scene["humans"]]
    min_robot_human = min_distance(robot_positions, human_positions)
    rack_positions = [item["position"] for item in scene["racks"]]
    min_robot_rack = min_distance(robot_positions, rack_positions)
    return {
        "robots": len(scene["robots"]),
        "racks": len(scene["racks"]),
        "humans": len(scene["humans"]),
        "loads": len(scene["loads"]),
        "communication_radius": scene["communication"]["radius_m"],
        "packet_loss": scene["communication"]["packet_loss"],
        "sensor_lidar_range": scene["sensors"]["lidar_range_m"],
        "blind_zones": len(scene["sensors"]["blind_zones"]),
        "min_initial_robot_human_distance": min_robot_human,
        "min_initial_robot_rack_distance": min_robot_rack,
    }


def min_distance(a: list[list[float]], b: list[list[float]]) -> float:
    if not a or not b:
        return math.nan
    best = math.inf
    for pa in a:
        for pb in b:
            dist = math.dist(pa[:2], pb[:2])
            best = min(best, dist)
    return float(best)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(
    path: Path,
    scene_dir: Path,
    out_dir: Path,
    manifest_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# CoppeliaSim validation scenes",
        "",
        "Generated deterministic warehouse scenes for the MRBO TFM validation package.",
        "Status is `generated_not_opened`: this machine did not launch CoppeliaSim in this run.",
        "",
        "| Scene | Policy | Robots | Racks | Humans | Lua |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in manifest_rows:
        lines.append(
            f"| {row['scene']} | {row['policy']} | {row['robots']} | {row['racks']} | {row['humans']} | `{row['lua']}` |"
        )
    lines.extend(
        [
            "",
            "Expected Coppelia smoke:",
            "",
            "1. Open CoppeliaSim.",
            "2. Run one generated Lua file from `coppeliasim/scenes`.",
            "3. Confirm Pioneer 3-DX models load, or fallback bases appear with the same names.",
            "4. Export MP4/captures and update `scene_manifest.csv` status from `generated_not_opened` to `opened_pass`.",
            "",
            "Regenerate:",
            "",
            "```powershell",
            "python scripts\\build_coppelia_scene.py --scene-dir coppeliasim\\scenes --out results\\coppeliasim_validation",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
