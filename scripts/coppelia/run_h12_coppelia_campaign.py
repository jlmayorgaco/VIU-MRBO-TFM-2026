"""Build H12 CoppeliaSim validation scenes with synthetic fallback renders."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_coppelia_scene import SceneSpec, build_scene_dict, render_lua_scene, write_csv  # noqa: E402


OUT_DEFAULT = ROOT / "results/campaigns/H12_coppelia_closed_loop"
SCENE_DIR_DEFAULT = ROOT / "coppeliasim/campaign_scenes"
COPPELIA_DEFAULT = Path(r"C:\Program Files\CoppeliaRobotics\CoppeliaSimEdu\coppeliaSim.exe")


@dataclass(frozen=True)
class H12Scene:
    name: str
    policy: str
    communication_radius: float
    packet_loss: float
    robots: int
    racks: int
    humans: int
    sensor_degradation: float
    robot_failure: bool = False
    description: str = ""


SCENES = (
    H12Scene("h12_nominal_smith_qr", "smith_qr_full", 12.0, 0.0, 15, 18, 2, 0.0, description="Nominal Smith-QR."),
    H12Scene("h12_r3_smith", "smith_full", 3.0, 0.0, 15, 18, 2, 0.0, description="R3 degraded communication Smith."),
    H12Scene("h12_r3_smith_qr", "smith_qr_full", 3.0, 0.0, 15, 18, 2, 0.0, description="R3 degraded communication Smith-QR."),
    H12Scene("h12_robot_failure", "smith_qr_full", 4.0, 0.0, 15, 18, 2, 0.0, robot_failure=True, description="Robot failure and recovery."),
    H12Scene("h12_human_crossing", "smith_qr_full", 4.0, 0.0, 15, 18, 6, 0.0, description="Human crossing safety."),
    H12Scene("h12_sensor_degraded", "smith_qr_full", 4.0, 0.0, 15, 18, 4, 0.55, description="Sensor degraded blind zones."),
    H12Scene("h12_predictive_density_bottleneck", "smith_qr_predictive_density", 4.0, 0.0, 46, 18, 4, 0.0, description="Predictive density bottleneck."),
    H12Scene("h12_rectangular_wrench", "wrench_capacity", 5.0, 0.0, 18, 16, 2, 0.0, description="Rectangular load wrench/caging."),
    H12Scene("h12_battery_return", "smith_qr_battery", 5.0, 0.0, 15, 18, 2, 0.0, description="Battery returnability."),
    H12Scene("h12_integrated_full", "smith_qr_integrated", 5.0, 0.05, 24, 20, 6, 0.25, robot_failure=True, description="Integrated stress scenario."),
)


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    scene_dir = args.scene_dir.resolve()
    prepare_dirs(out_dir, scene_dir)
    coppelia_path = args.coppelia.resolve() if args.coppelia else COPPELIA_DEFAULT
    coppelia_available = coppelia_path.exists()
    manifest_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(SCENES):
        base = SceneSpec(
            name=spec.name,
            policy=spec.policy,
            communication_radius=spec.communication_radius,
            packet_loss=spec.packet_loss,
            robots=spec.robots,
            racks=spec.racks,
            humans=spec.humans,
            sensor_degradation=spec.sensor_degradation,
            robot_failure=spec.robot_failure,
            playback_csv=str((out_dir / f"data/{spec.name}_playback.csv").relative_to(ROOT)),
        )
        scene = build_scene_dict(base, seed=7200 + index)
        scene = enrich_scene(scene, spec)
        yaml_path = scene_dir / f"{spec.name}.json"
        lua_path = scene_dir / f"{spec.name}.lua"
        yaml_path.write_text(json.dumps(scene, indent=2), encoding="utf-8")
        lua_path.write_text(render_lua_scene_with_cameras(scene), encoding="utf-8")
        playback_path = out_dir / f"data/{spec.name}_playback.csv"
        playback_rows = make_playback(scene, spec)
        write_csv(playback_path, playback_rows)
        screenshot = out_dir / f"plots/{spec.name}_top_view.png"
        video = out_dir / f"animations/{spec.name}.mp4"
        render_fallback(scene, playback_rows, screenshot, video)
        metrics = offline_metrics(scene, playback_rows)
        metric_rows.append({"scene": spec.name, **metrics})
        manifest_rows.append(
            {
                "scene": spec.name,
                "description": spec.description,
                "policy": spec.policy,
                "lua": str(lua_path.relative_to(ROOT)),
                "scene_json": str(yaml_path.relative_to(ROOT)),
                "playback_csv": str(playback_path.relative_to(ROOT)),
                "screenshot": str(screenshot.relative_to(ROOT)),
                "video": str(video.relative_to(ROOT)),
                "coppelia_executable": str(coppelia_path),
                "coppelia_available": coppelia_available,
                "status": "fallback_synthetic_render",
            }
        )
    write_csv(out_dir / "manifest.csv", manifest_rows)
    write_csv(out_dir / "data/scene_metrics.csv", metric_rows)
    summary = {
        "campaign": "H12_coppelia_closed_loop",
        "coppelia_executable": str(coppelia_path),
        "coppelia_available": coppelia_available,
        "status": "fallback_synthetic_render",
        "scene_count": len(manifest_rows),
        "scenes": [row["scene"] for row in manifest_rows],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_readme(out_dir, summary)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--scene-dir", type=Path, default=SCENE_DIR_DEFAULT)
    parser.add_argument("--coppelia", type=Path, default=COPPELIA_DEFAULT)
    return parser.parse_args()


def prepare_dirs(out_dir: Path, scene_dir: Path) -> None:
    scene_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("data", "plots", "frames", "animations", "reports"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def enrich_scene(scene: dict[str, Any], spec: H12Scene) -> dict[str, Any]:
    scene["validation"] = {
        "hypothesis": spec.description,
        "expected_artifacts": ["playback_csv", "top_view_png", "mp4", "metrics_csv"],
    }
    scene["cameras"] = [
        {
            "name": "Camera_top_validation",
            "position": [0.0, 0.0, 34.0],
            "orientation_euler": [0.0, math.radians(90.0), 0.0],
            "resolution": [1920, 1080],
        },
        {
            "name": "Camera_oblique_validation",
            "position": [18.0, -20.0, 18.0],
            "orientation_euler": [math.radians(58.0), 0.0, math.radians(42.0)],
            "resolution": [1920, 1080],
        },
    ]
    if "density" in spec.name:
        scene["density_bottleneck"] = {"center": [0.0, 0.0], "radius": 1.6, "rho_max": 1.0}
    if "battery" in spec.name:
        scene["battery"] = {"low_battery_robot": "Pioneer_02", "initial_soc": 0.18, "charger": [-15.0, 10.0, 0.05]}
    if "wrench" in spec.name or "integrated" in spec.name:
        scene["loads"][0]["size"] = [2.6, 1.1, 0.55]
        scene["loads"][0]["name"] = "Load_rectangular_wrench"
        scene["wrench_validation"] = {"required_tau": 1.2, "shape": "rectangle_superellipse"}
    return scene


def render_lua_scene_with_cameras(scene: dict[str, Any]) -> str:
    base = render_lua_scene(scene)
    camera_lines = [
        "",
        "-- Validation cameras",
        "for _, cam in ipairs(scene.cameras or {}) do",
        "    local h = sim.createObject(sim.object_camera_type, 0)",
        "    setName(h, cam.name)",
        "    sim.setObjectPosition(h, -1, cam.position)",
        "    sim.setObjectOrientation(h, -1, cam.orientation_euler)",
        "end",
        "sim.setNamedStringParam('mrbo_validation_cameras', 'top_and_oblique')",
        "",
    ]
    return base + "\n" + "\n".join(camera_lines)


def make_playback(scene: dict[str, Any], spec: H12Scene) -> list[dict[str, Any]]:
    rng = np.random.default_rng(scene["seed"])
    robots = scene["robots"]
    steps = 90
    rows: list[dict[str, Any]] = []
    for frame in range(steps):
        t = frame * 0.5
        for idx, robot in enumerate(robots):
            start = np.array(robot["position"][:2], dtype=float)
            phase = min(1.0, max(0.0, (t - idx * 0.72) / 42.0))
            lane_offset = ((idx % 7) - 3) * 0.56
            longitudinal_offset = (idx // 7) * 0.34
            if "density" in spec.name:
                lane = lane_offset if idx % 3 else 4.6 + lane_offset
                goal = np.array([9.0 - longitudinal_offset, lane])
                mid = np.array([0.0 - longitudinal_offset, lane])
            elif "wrench" in spec.name or "integrated" in spec.name:
                angle = 2.0 * math.pi * (idx % 12) / 12.0
                ring = 2.2 + 0.22 * (idx // 12)
                goal = np.array([3.0 + ring * math.cos(angle), 0.5 + 1.25 * math.sin(angle)])
                mid = 0.5 * (start + goal)
            elif "battery" in spec.name and idx == 1:
                goal = np.array([-15.0, 10.0 + lane_offset])
                mid = np.array([-10.0, 6.0 + lane_offset])
            else:
                goal = np.array([8.0 - longitudinal_offset, 6.6 + lane_offset])
                mid = np.array([0.0 - longitudinal_offset, 2.2 * math.sin(idx * 0.7) + lane_offset])
            point = bezier(start, mid, goal, phase)
            point += rng.normal(0.0, 0.025, size=2)
            rows.append(
                {
                    "t": round(t, 3),
                    "robot": robot["name"],
                    "x": round(float(point[0]), 4),
                    "y": round(float(point[1]), 4),
                    "theta": round(float(math.atan2(goal[1] - start[1], goal[0] - start[0])), 4),
                    "policy": spec.policy,
                }
            )
    return rows


def bezier(a: np.ndarray, b: np.ndarray, c: np.ndarray, s: float) -> np.ndarray:
    return (1.0 - s) ** 2 * a + 2.0 * (1.0 - s) * s * b + s**2 * c


def render_fallback(scene: dict[str, Any], playback_rows: list[dict[str, Any]], screenshot: Path, video: Path) -> None:
    frames = sorted({float(row["t"]) for row in playback_rows})
    fig, ax = plt.subplots(figsize=(8.0, 5.4))

    def draw(frame_idx: int) -> list[Any]:
        ax.clear()
        t = frames[frame_idx]
        rows = [row for row in playback_rows if float(row["t"]) == t]
        draw_scene_base(ax, scene)
        xs = [float(row["x"]) for row in rows]
        ys = [float(row["y"]) for row in rows]
        ax.scatter(xs, ys, s=26, color="#2563eb", label="AMR playback")
        if "density_bottleneck" in scene:
            b = scene["density_bottleneck"]
            circle = plt.Circle(b["center"], b["radius"], color="#dc2626", fill=False, linestyle="--", linewidth=1.5)
            ax.add_patch(circle)
        ax.set_title(f"{scene['scenario']} fallback render t={t:.1f}s")
        ax.legend(loc="upper right", fontsize=7)
        return []

    draw(min(24, len(frames) - 1))
    fig.savefig(screenshot, dpi=180)
    ani = animation.FuncAnimation(fig, draw, frames=len(frames), interval=80, blit=False)
    ani.save(video, writer="ffmpeg", dpi=125, fps=12)
    plt.close(fig)


def draw_scene_base(ax: plt.Axes, scene: dict[str, Any]) -> None:
    w = scene["warehouse"]["width_m"]
    d = scene["warehouse"]["depth_m"]
    ax.set_xlim(-w / 2 - 1.0, w / 2 + 1.0)
    ax.set_ylim(-d / 2 - 1.0, d / 2 + 1.0)
    ax.set_aspect("equal", adjustable="box")
    ax.add_patch(plt.Rectangle((-w / 2, -d / 2), w, d, facecolor="#e5e7eb", edgecolor="#374151", linewidth=1.0))
    for rack in scene["racks"]:
        x, y, _ = rack["position"]
        sx, sy, _ = rack["size"]
        ax.add_patch(plt.Rectangle((x - sx / 2, y - sy / 2), sx, sy, facecolor="#9ca3af", edgecolor="#4b5563", alpha=0.9))
    for load in scene["loads"]:
        x, y, _ = load["position"]
        sx, sy, _ = load["size"]
        ax.add_patch(plt.Rectangle((x - sx / 2, y - sy / 2), sx, sy, facecolor="#f59e0b", edgecolor="#92400e"))
    for human in scene["humans"]:
        x, y, _ = human["position"]
        ax.scatter([x], [y], marker="x", color="#dc2626", s=36)
    ax.grid(alpha=0.18)


def offline_metrics(scene: dict[str, Any], playback_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_t: dict[float, list[tuple[float, float]]] = {}
    for row in playback_rows:
        by_t.setdefault(float(row["t"]), []).append((float(row["x"]), float(row["y"])))
    min_pair = math.inf
    for points in by_t.values():
        for i, p in enumerate(points):
            for q in points[i + 1 :]:
                min_pair = min(min_pair, math.dist(p, q))
    return {
        "robots": len(scene["robots"]),
        "racks": len(scene["racks"]),
        "humans": len(scene["humans"]),
        "loads": len(scene["loads"]),
        "frames": len(by_t),
        "min_playback_pair_distance": float(min_pair),
        "has_top_camera": any(cam["name"] == "Camera_top_validation" for cam in scene["cameras"]),
        "has_oblique_camera": any(cam["name"] == "Camera_oblique_validation" for cam in scene["cameras"]),
    }


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H12 CoppeliaSim closed-loop campaign",
        "",
        "Generates CoppeliaSim Lua scenes, playback CSVs, validation cameras and synthetic fallback videos.",
        "",
        f"- Status: `{summary['status']}`",
        f"- Coppelia available: `{summary['coppelia_available']}`",
        f"- Scene count: `{summary['scene_count']}`",
        "",
        "Regenerate:",
        "",
        "```powershell",
        "python scripts\\coppelia\\run_h12_coppelia_campaign.py",
        "```",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
