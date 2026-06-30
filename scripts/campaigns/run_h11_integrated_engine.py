"""Run H11: integrated wrench, battery, CBF and port-Hamiltonian gate.

This campaign is a compact dynamic simulation for the extended framework. It
compares scalar cardinality against wrench-aware contact placement for a
rectangular load that must translate and rotate near an obstacle.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import lsq_linear


ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "results/campaigns/H11_integrated_engine"
DOC_FIG = ROOT / "docs/doc-06-explanatory-report/figures/fig-h11-integrated-engine.png"


POLICIES = ("cardinality_only", "wrench_capacity")


@dataclass(frozen=True)
class Config:
    seeds: tuple[int, ...] = tuple(range(6126, 6156))
    duration: float = 45.0
    dt: float = 0.1
    a: float = 1.7
    b: float = 0.75
    p: float = 5.0
    fmax: float = 1.0
    mass: float = 7.5
    inertia: float = 3.4
    damping: float = 0.28
    torque_limit: float = 0.85
    battery_initial: float = 1.0
    obstacle: tuple[float, float] = (4.2, 0.0)
    obstacle_radius: float = 0.85
    safe_radius: float = 1.25


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    prepare_dirs(out_dir)
    cfg = Config()
    rows: list[dict[str, Any]] = []
    time_rows: list[dict[str, Any]] = []
    representative: dict[str, Any] = {}
    for seed in cfg.seeds:
        for policy in POLICIES:
            result = simulate(seed, policy, cfg)
            rows.append(result["summary"])
            if seed == cfg.seeds[0]:
                representative[policy] = result
                time_rows.extend(result["time_rows"])
    write_csv(out_dir / "data/runs.csv", rows)
    write_csv(out_dir / "data/time_series_seed6126.csv", time_rows)
    stats = paired_stats(rows)
    write_csv(out_dir / "data/hypothesis_tests.csv", stats)
    summary = build_summary(rows, stats)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    make_plots(out_dir, rows, representative, cfg)
    make_animation(out_dir, representative, cfg)
    write_manifest(out_dir)
    write_readme(out_dir, summary)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    return parser.parse_args()


def prepare_dirs(out_dir: Path) -> None:
    for sub in ("data", "plots", "frames", "animations", "reports"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def simulate(seed: int, policy: str, cfg: Config) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    steps = int(cfg.duration / cfg.dt) + 1
    q = np.array([-7.5, 0.0, 0.0], dtype=float)
    xi = np.array([0.0, 0.0, 0.0], dtype=float)
    battery = np.full(4 if policy == "wrench_capacity" else 3, cfg.battery_initial, dtype=float)
    phases = contact_phases(policy, rng)
    desired_dist = pairwise_phase_distances(phases, cfg)
    hamiltonian_prev = hamiltonian(q, xi, cfg)
    delivered = False
    time_rows: list[dict[str, Any]] = []
    pos_history: list[np.ndarray] = []
    contact_history: list[np.ndarray] = []
    q_history: list[np.ndarray] = []

    for step in range(steps):
        t = step * cfg.dt
        demand = demanded_wrench(t, q, cfg)
        contacts = contact_points(phases, q, cfg)
        signatures = wrench_signatures(phases, cfg)
        forces, achieved, residual = solve_wrench(signatures, demand, cfg.fmax)
        force_vec = achieved[:2]
        torque = achieved[2]
        cbf_active = 0
        if np.linalg.norm(q[:2] - np.array(cfg.obstacle)) < cfg.safe_radius + cfg.obstacle_radius:
            cbf_active = 1
            force_vec += cbf_correction(q, cfg)
            torque += 0.18 if policy == "wrench_capacity" else -0.04
        accel = np.array([force_vec[0] / cfg.mass, force_vec[1] / cfg.mass, torque / cfg.inertia])
        xi += cfg.dt * (accel - cfg.damping * xi)
        xi[0] = float(np.clip(xi[0], -1.2, 1.2))
        xi[1] = float(np.clip(xi[1], -0.75, 0.75))
        xi[2] = float(np.clip(xi[2], -0.9, 0.9))
        q += cfg.dt * xi
        battery -= cfg.dt * (0.0008 + 0.0045 * forces**2)
        formation_error = formation_error_value(contacts, desired_dist)
        h = hamiltonian(q, xi, cfg)
        delta_h = max(h - hamiltonian_prev, 0.0)
        hamiltonian_prev = h
        torque_saturation = abs(torque) / cfg.torque_limit
        if q[0] >= 4.5 and not delivered:
            delivered = True
        time_rows.append(
            {
                "seed": seed,
                "policy": policy,
                "t": t,
                "x_load": q[0],
                "y_load": q[1],
                "theta_load": q[2],
                "wrench_residual": float(np.linalg.norm(residual)),
                "torque_saturation": float(torque_saturation),
                "hamiltonian": h,
                "delta_hamiltonian": delta_h,
                "formation_error": formation_error,
                "cbf_active": cbf_active,
                "battery_min": float(np.min(battery)),
                "delivered": int(delivered),
            }
        )
        if seed == 6126 and step % 4 == 0:
            pos_history.append(contacts.copy())
            contact_history.append(forces.copy())
            q_history.append(q.copy())

    summary = summarize(seed, policy, time_rows, cfg)
    return {
        "summary": summary,
        "time_rows": time_rows,
        "pos_history": pos_history,
        "contact_history": contact_history,
        "q_history": q_history,
    }


def contact_phases(policy: str, rng: np.random.Generator) -> np.ndarray:
    if policy == "cardinality_only":
        base = np.array([math.pi, math.pi + 0.16, math.pi - 0.16])
    else:
        base = np.array([math.pi, math.pi / 2, -math.pi / 2, 0.0])
    return base + rng.normal(0.0, 0.015, size=base.shape)


def superellipse_point(gamma: float, cfg: Config) -> np.ndarray:
    c = math.cos(gamma)
    s = math.sin(gamma)
    eps = 1.0e-5
    x = cfg.a * c * (c * c + eps) ** (1.0 / cfg.p - 0.5)
    y = cfg.b * s * (s * s + eps) ** (1.0 / cfg.p - 0.5)
    return np.array([x, y], dtype=float)


def superellipse_normal(point: np.ndarray, cfg: Config) -> np.ndarray:
    x, y = point
    gx = cfg.p * abs(x / cfg.a) ** (cfg.p - 1.0) * math.copysign(1.0, x) / cfg.a
    gy = cfg.p * abs(y / cfg.b) ** (cfg.p - 1.0) * math.copysign(1.0, y) / cfg.b
    g = np.array([gx, gy], dtype=float)
    return g / max(float(np.linalg.norm(g)), 1.0e-9)


def contact_points(phases: np.ndarray, q: np.ndarray, cfg: Config) -> np.ndarray:
    rot = rotation(q[2])
    return np.array([q[:2] + rot @ superellipse_point(g, cfg) for g in phases])


def wrench_signatures(phases: np.ndarray, cfg: Config) -> np.ndarray:
    rows = []
    for gamma in phases:
        r = superellipse_point(gamma, cfg)
        n = superellipse_normal(r, cfg)
        torque = r[0] * n[1] - r[1] * n[0]
        rows.append([n[0], n[1], torque])
    return np.array(rows, dtype=float).T


def solve_wrench(signatures: np.ndarray, demand: np.ndarray, fmax: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    result = lsq_linear(signatures, demand, bounds=(0.0, fmax), lsmr_tol="auto")
    forces = np.asarray(result.x, dtype=float)
    achieved = signatures @ forces
    residual = demand - achieved
    return forces, achieved, residual


def demanded_wrench(t: float, q: np.ndarray, cfg: Config) -> np.ndarray:
    target_x = 7.4
    force_x = np.clip(0.32 + 0.065 * (target_x - q[0]), 0.12, 0.72)
    force_y = -0.08 * q[1]
    torque = 0.0
    if 12.0 <= t <= 29.0:
        torque = 0.78 * math.sin((t - 12.0) / 17.0 * math.pi)
    return np.array([force_x, force_y, torque], dtype=float)


def cbf_correction(q: np.ndarray, cfg: Config) -> np.ndarray:
    diff = q[:2] - np.array(cfg.obstacle)
    norm = max(float(np.linalg.norm(diff)), 1.0e-6)
    return 0.26 * diff / norm


def hamiltonian(q: np.ndarray, xi: np.ndarray, cfg: Config) -> float:
    obstacle_dist = max(float(np.linalg.norm(q[:2] - np.array(cfg.obstacle))) - cfg.obstacle_radius, 0.05)
    potential = 0.045 / obstacle_dist
    kinetic = 0.5 * cfg.mass * float(np.dot(xi[:2], xi[:2])) + 0.5 * cfg.inertia * xi[2] ** 2
    return float(kinetic + potential)


def pairwise_phase_distances(phases: np.ndarray, cfg: Config) -> np.ndarray:
    points = np.array([superellipse_point(g, cfg) for g in phases])
    return pairwise_distances(points)


def formation_error_value(points: np.ndarray, desired: np.ndarray) -> float:
    if len(points) < 2:
        return 0.0
    observed = pairwise_distances(points)
    mask = desired > 0.0
    return float(np.mean(np.abs(observed[mask] - desired[mask])))


def pairwise_distances(points: np.ndarray) -> np.ndarray:
    n = len(points)
    out = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            out[i, j] = out[j, i] = float(np.linalg.norm(points[i] - points[j]))
    return out


def rotation(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def summarize(seed: int, policy: str, rows: list[dict[str, Any]], cfg: Config) -> dict[str, Any]:
    delivered_time = next((row["t"] for row in rows if row["delivered"]), math.nan)
    return {
        "seed": seed,
        "policy": policy,
        "mean_wrench_residual": float(np.mean([row["wrench_residual"] for row in rows])),
        "max_wrench_residual": float(np.max([row["wrench_residual"] for row in rows])),
        "max_torque_saturation": float(np.max([row["torque_saturation"] for row in rows])),
        "max_delta_hamiltonian": float(np.max([row["delta_hamiltonian"] for row in rows])),
        "mean_formation_error": float(np.mean([row["formation_error"] for row in rows])),
        "cbf_active_steps": int(np.sum([row["cbf_active"] for row in rows])),
        "min_battery": float(np.min([row["battery_min"] for row in rows])),
        "throughput": 1.0 if any(row["delivered"] for row in rows) else 0.0,
        "delivery_time": float(delivered_time),
    }


def paired_stats(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_seed_policy = {(int(row["seed"]), row["policy"]): row for row in rows}
    seeds = sorted({int(row["seed"]) for row in rows})
    specs = [
        ("mean_wrench_residual", "less_than_cardinality", 0.0),
        ("max_torque_saturation", "bounded_candidate", 0.85),
        ("max_delta_hamiltonian", "bounded_candidate", 0.35),
        ("min_battery", "lower_bounded_candidate", 0.75),
        ("throughput", "greater_than_cardinality", 0.0),
    ]
    out: list[dict[str, Any]] = []
    for metric, alternative, threshold in specs:
        deltas = np.array(
            [
                float(by_seed_policy[(seed, "wrench_capacity")][metric])
                - float(by_seed_policy[(seed, "cardinality_only")][metric])
                for seed in seeds
            ],
            dtype=float,
        )
        candidate_values = np.array([float(by_seed_policy[(seed, "wrench_capacity")][metric]) for seed in seeds], dtype=float)
        mean = float(np.mean(deltas))
        low, high = ci95(deltas)
        candidate_low, candidate_high = ci95(candidate_values)
        candidate_mean = float(np.mean(candidate_values))
        if alternative == "less_than_cardinality":
            passed = high < 0.0
        elif alternative == "greater_than_cardinality":
            passed = low > 0.0
        elif alternative == "bounded_candidate":
            passed = candidate_high <= threshold
        elif alternative == "lower_bounded_candidate":
            passed = candidate_low >= threshold
        else:
            passed = False
        out.append(
            {
                "hypothesis": f"wrench_capacity_vs_cardinality_{metric}",
                "candidate": "wrench_capacity",
                "baseline": "cardinality_only",
                "metric": metric,
                "n": len(seeds),
                "mean_delta": mean,
                "ci95_low": low,
                "ci95_high": high,
                "candidate_mean": candidate_mean,
                "candidate_ci95_low": candidate_low,
                "candidate_ci95_high": candidate_high,
                "threshold": threshold,
                "alternative": alternative,
                "passed": passed,
            }
        )
    return out


def ci95(values: np.ndarray) -> tuple[float, float]:
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1) / math.sqrt(values.size))
    return mean - 1.96 * se, mean + 1.96 * se


def build_summary(rows: list[dict[str, Any]], stats: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"campaign": "H11_integrated_engine", "paired_tests": stats}
    for policy in POLICIES:
        policy_rows = [row for row in rows if row["policy"] == policy]
        summary[policy] = {}
        for metric in (
            "mean_wrench_residual",
            "max_torque_saturation",
            "max_delta_hamiltonian",
            "mean_formation_error",
            "cbf_active_steps",
            "min_battery",
            "throughput",
            "delivery_time",
        ):
            values = np.array([float(row[metric]) for row in policy_rows], dtype=float)
            summary[policy][metric] = float(np.nanmean(values)) if np.any(np.isfinite(values)) else math.nan
    summary["h11_pass"] = bool(all(row["passed"] for row in stats[:4]))
    return summary


def make_plots(out_dir: Path, rows: list[dict[str, Any]], representative: dict[str, Any], cfg: Config) -> None:
    plots = out_dir / "plots"
    metrics = ["mean_wrench_residual", "max_torque_saturation", "max_delta_hamiltonian", "min_battery"]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2))
    colors = ["#b45309", "#2563eb"]
    for ax, metric in zip(axes, metrics):
        vals = [np.mean([float(row[metric]) for row in rows if row["policy"] == policy]) for policy in POLICIES]
        ax.bar(POLICIES, vals, color=colors)
        ax.set_title(metric.replace("_", " "))
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(plots / "h11_policy_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    for policy, color in zip(POLICIES, colors):
        rows_ts = representative[policy]["time_rows"]
        ax.plot([r["t"] for r in rows_ts], [r["wrench_residual"] for r in rows_ts], label=policy, color=color)
    ax.set_xlabel("t [s]")
    ax.set_ylabel("||W_dem - W_act||")
    ax.set_title("H11 wrench residual during rectangular-load transport")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plots / "h11_wrench_residual_timeseries.png", dpi=180)
    plt.close(fig)

    combined_doc_figure(plots)


def combined_doc_figure(plots: Path) -> None:
    comp = plt.imread(plots / "h11_policy_comparison.png")
    ts = plt.imread(plots / "h11_wrench_residual_timeseries.png")
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 7.0))
    axes[0].imshow(ts)
    axes[0].axis("off")
    axes[1].imshow(comp)
    axes[1].axis("off")
    fig.tight_layout(pad=0.4)
    fig.savefig(DOC_FIG, dpi=180)
    fig.savefig(plots / "h11_doc_figure.png", dpi=180)
    plt.close(fig)


def make_animation(out_dir: Path, representative: dict[str, Any], cfg: Config) -> None:
    result = representative["wrench_capacity"]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    anim_path = out_dir / "animations/h11_integrated_engine.mp4"
    frames_dir = out_dir / "frames"

    def draw(frame: int) -> list[Any]:
        ax.clear()
        q = result["q_history"][frame]
        pts = result["pos_history"][frame]
        rot = rotation(q[2])
        rect = np.array([[-cfg.a, -cfg.b], [cfg.a, -cfg.b], [cfg.a, cfg.b], [-cfg.a, cfg.b], [-cfg.a, -cfg.b]])
        rect_world = np.array([q[:2] + rot @ p for p in rect])
        ax.plot(rect_world[:, 0], rect_world[:, 1], color="#1f2937", linewidth=2.0)
        ax.scatter(pts[:, 0], pts[:, 1], color="#2563eb", s=42, label="contacts")
        obstacle = plt.Circle(cfg.obstacle, cfg.obstacle_radius, color="#dc2626", alpha=0.25)
        safe = plt.Circle(cfg.obstacle, cfg.safe_radius + cfg.obstacle_radius, color="#dc2626", fill=False, linestyle="--")
        ax.add_patch(obstacle)
        ax.add_patch(safe)
        ax.set_xlim(-8.5, 8.5)
        ax.set_ylim(-4.0, 4.0)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title("H11 wrench-aware rectangular load transport")
        ax.grid(alpha=0.25)
        return []

    ani = animation.FuncAnimation(fig, draw, frames=len(result["q_history"]), interval=80, blit=False)
    ani.save(anim_path, writer="ffmpeg", dpi=130, fps=12)
    draw(min(45, len(result["q_history"]) - 1))
    fig.savefig(frames_dir / "h11_integrated_engine_representative.png", dpi=180)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(out_dir: Path) -> None:
    rels = [
        "data/runs.csv",
        "data/time_series_seed6126.csv",
        "data/hypothesis_tests.csv",
        "plots/h11_policy_comparison.png",
        "plots/h11_wrench_residual_timeseries.png",
        "plots/h11_doc_figure.png",
        "frames/h11_integrated_engine_representative.png",
        "animations/h11_integrated_engine.mp4",
        "summary.json",
        "README.md",
    ]
    write_csv(
        out_dir / "manifest.csv",
        [{"artifact": rel, "exists": (out_dir / rel).exists(), "bytes": (out_dir / rel).stat().st_size if (out_dir / rel).exists() else 0} for rel in rels],
    )


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H11 integrated engine campaign",
        "",
        "Dynamic rectangular-load simulation with wrench, CBF, battery and port-Hamiltonian metrics.",
        "",
        f"- H11 pass: `{summary['h11_pass']}`",
        f"- Cardinality residual mean: `{summary['cardinality_only']['mean_wrench_residual']:.4f}`",
        f"- Wrench-aware residual mean: `{summary['wrench_capacity']['mean_wrench_residual']:.4f}`",
        "",
        "Regenerate:",
        "",
        "```powershell",
        "python scripts\\campaigns\\run_h11_integrated_engine.py",
        "```",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
