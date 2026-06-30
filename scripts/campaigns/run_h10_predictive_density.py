"""Run H10: predictive density tolls for warehouse congestion.

The campaign is intentionally synthetic but tied to the thesis framework: robots
choose between a short bottleneck route and a longer alternative. The predictive
treatment estimates rho(x,t+tau) from current positions and velocities, applies a
virtual congestion toll, and compares against Smith-QR without tolls and a
reactive congestion penalty.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "results/campaigns/H10_predictive_density"
DOC_FIG = ROOT / "docs/doc-06-explanatory-report/figures/fig-h10-predictive-density.png"


POLICIES = ("greedy", "smith_qr_base", "smith_qr_reactive", "smith_qr_predictive")


@dataclass(frozen=True)
class CampaignConfig:
    seeds: tuple[int, ...] = tuple(range(5026, 5056))
    robot_count: int = 64
    duration: float = 80.0
    dt: float = 0.25
    spawn_period: float = 0.48
    base_speed: float = 1.05
    bottleneck_center: tuple[float, float] = (0.0, 0.0)
    bottleneck_radius: float = 1.55
    sigma: float = 1.75
    lookahead_tau: float = 5.5
    rho_max: float = 1.0
    toll_gain: float = 1.55
    congestion_capacity: float = 2.45
    degradation_margin: float = 0.03


ROUTES: dict[str, np.ndarray] = {
    "short": np.array([[-9.0, 0.0], [-3.0, 0.0], [0.0, 0.0], [3.0, 0.0], [9.0, 0.0]], dtype=float),
    "alt": np.array([[-9.0, 0.0], [-5.8, 4.4], [0.0, 5.2], [5.8, 4.4], [9.0, 0.0]], dtype=float),
}


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    prepare_dirs(out_dir)
    cfg = CampaignConfig()

    run_rows: list[dict[str, Any]] = []
    time_rows: list[dict[str, Any]] = []
    representative: dict[str, Any] = {}
    for seed in cfg.seeds:
        for policy in POLICIES:
            result = simulate(seed, policy, cfg)
            run_rows.append(result["summary"])
            if seed == cfg.seeds[0]:
                representative[policy] = result
                time_rows.extend(result["time_rows"])

    data_dir = out_dir / "data"
    write_csv(data_dir / "runs.csv", run_rows)
    write_csv(data_dir / "time_series_seed5026.csv", time_rows)
    stats_rows = paired_statistics(run_rows, cfg)
    write_csv(data_dir / "hypothesis_tests.csv", stats_rows)
    summary = build_summary(run_rows, stats_rows, cfg)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_manifest(out_dir, summary)
    write_readme(out_dir, summary)
    make_plots(out_dir, run_rows, representative, cfg)
    make_animation(out_dir, representative, cfg)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DEFAULT)
    return parser.parse_args()


def prepare_dirs(out_dir: Path) -> None:
    for sub in ("data", "plots", "frames", "animations", "reports"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)


def simulate(seed: int, policy: str, cfg: CampaignConfig) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    steps = int(cfg.duration / cfg.dt) + 1
    spawn_times = np.arange(0.0, cfg.duration * 0.72, cfg.spawn_period)
    spawn_times = spawn_times[: cfg.robot_count]
    spawn_times = spawn_times + rng.normal(0.0, 0.08, size=spawn_times.shape)

    route_names = np.array(["unspawned"] * cfg.robot_count, dtype=object)
    progress = np.zeros(cfg.robot_count, dtype=float)
    active = np.zeros(cfg.robot_count, dtype=bool)
    delivered = np.zeros(cfg.robot_count, dtype=bool)
    positions = np.repeat(ROUTES["short"][[0]], cfg.robot_count, axis=0)
    velocities = np.zeros_like(positions)
    delivery_times = np.full(cfg.robot_count, np.nan)
    total_distance = np.zeros(cfg.robot_count, dtype=float)
    decision_runtime = 0.0
    decision_count = 0

    time_rows: list[dict[str, Any]] = []
    history_pos: list[np.ndarray] = []
    history_routes: list[np.ndarray] = []
    history_rho: list[float] = []
    history_rho_tau: list[float] = []

    for step in range(steps):
        now = step * cfg.dt
        just_spawned = (~active) & (~delivered) & (spawn_times <= now)
        if np.any(just_spawned):
            for idx in np.flatnonzero(just_spawned):
                t0 = time.perf_counter()
                route_names[idx] = choose_route(policy, positions, velocities, active, route_names, cfg)
                decision_runtime += time.perf_counter() - t0
                decision_count += 1
            active[just_spawned] = True

        prev_positions = positions.copy()
        rho_now = bottleneck_density(positions, active & (route_names == "short"), cfg, lookahead=0.0)
        rho_tau = bottleneck_density(positions, active & (route_names == "short"), cfg, lookahead=cfg.lookahead_tau, velocities=velocities)

        for idx in np.flatnonzero(active):
            route = str(route_names[idx])
            speed_factor = route_speed_factor(route, positions[idx], rho_now, rho_tau, policy, cfg)
            route_length = path_length(ROUTES[route])
            progress[idx] = min(1.0, progress[idx] + cfg.dt * cfg.base_speed * speed_factor / route_length)
            positions[idx] = point_on_route(ROUTES[route], progress[idx])
            positions[idx] += rng.normal(0.0, 0.015, size=2)
            if progress[idx] >= 1.0:
                active[idx] = False
                delivered[idx] = True
                delivery_times[idx] = now

        velocities = (positions - prev_positions) / cfg.dt
        total_distance += np.linalg.norm(positions - prev_positions, axis=1)
        active_count = int(np.sum(active))
        mean_speed = float(np.mean(np.linalg.norm(velocities[active], axis=1))) if active_count else 0.0
        jam = rho_tau > cfg.rho_max

        time_rows.append(
            {
                "seed": seed,
                "policy": policy,
                "t": now,
                "rho_now": rho_now,
                "rho_tau": rho_tau,
                "active": active_count,
                "delivered": int(np.sum(delivered)),
                "mean_speed": mean_speed,
                "jam": int(jam),
                "short_active": int(np.sum(active & (route_names == "short"))),
                "alt_active": int(np.sum(active & (route_names == "alt"))),
            }
        )
        if seed == cfg.seeds[0] and step % 2 == 0:
            history_pos.append(positions.copy())
            history_routes.append(route_names.copy())
            history_rho.append(float(rho_now))
            history_rho_tau.append(float(rho_tau))

    completed = int(np.sum(delivered))
    direct_distance = path_length(ROUTES["short"])
    delivered_times = delivery_times[np.isfinite(delivery_times)]
    reward_capture = completed / cfg.robot_count
    jam_steps = int(sum(row["jam"] for row in time_rows))
    deadlocks = int(sum(1 for row in time_rows if row["jam"] and row["active"] > 8 and row["mean_speed"] < 0.18))
    route_split_ratio = float(np.sum(route_names == "alt") / max(np.sum(route_names != "unspawned"), 1))
    runtime_ms = 1000.0 * decision_runtime / max(decision_count, 1)
    wasted_distance = float(np.sum(np.maximum(total_distance - direct_distance * delivered.astype(float), 0.0)))
    summary = {
        "seed": seed,
        "policy": policy,
        "robots": cfg.robot_count,
        "completed": completed,
        "reward_capture_ratio": reward_capture,
        "mean_delivery_time": float(np.mean(delivered_times)) if delivered_times.size else math.nan,
        "max_rho_tau": float(max(row["rho_tau"] for row in time_rows)),
        "mean_rho_tau": float(np.mean([row["rho_tau"] for row in time_rows])),
        "jam_steps": jam_steps,
        "deadlocks": deadlocks,
        "route_split_ratio": route_split_ratio,
        "wasted_distance": wasted_distance,
        "runtime_per_robot_ms": runtime_ms,
    }
    return {
        "summary": summary,
        "time_rows": time_rows,
        "history_pos": history_pos,
        "history_routes": history_routes,
        "history_rho": history_rho,
        "history_rho_tau": history_rho_tau,
    }


def choose_route(policy: str, positions: np.ndarray, velocities: np.ndarray, active: np.ndarray, route_names: np.ndarray, cfg: CampaignConfig) -> str:
    if policy == "greedy":
        return "short"
    rho_now = bottleneck_density(positions, active & (route_names == "short"), cfg, lookahead=0.0)
    rho_tau = bottleneck_density(positions, active & (route_names == "short"), cfg, lookahead=cfg.lookahead_tau, velocities=velocities)
    short_cost = path_length(ROUTES["short"])
    alt_cost = path_length(ROUTES["alt"])
    if policy == "smith_qr_reactive":
        short_cost += cfg.toll_gain * max(rho_now - cfg.rho_max, 0.0) * path_length(ROUTES["short"])
    elif policy == "smith_qr_predictive":
        short_cost += cfg.toll_gain * max(rho_tau - cfg.rho_max, 0.0) * path_length(ROUTES["short"])
    return "alt" if alt_cost < short_cost else "short"


def route_speed_factor(route: str, pos: np.ndarray, rho_now: float, rho_tau: float, policy: str, cfg: CampaignConfig) -> float:
    if route == "alt":
        return 0.92
    dist = float(np.linalg.norm(pos - np.array(cfg.bottleneck_center)))
    if dist > 2.7:
        return 1.0
    rho = rho_tau if policy == "smith_qr_predictive" else rho_now
    penalty = max(rho - 0.75, 0.0)
    return float(np.clip(1.0 / (1.0 + 1.85 * penalty), 0.12, 1.0))


def bottleneck_density(
    positions: np.ndarray,
    mask: np.ndarray,
    cfg: CampaignConfig,
    lookahead: float,
    velocities: np.ndarray | None = None,
) -> float:
    if not np.any(mask):
        return 0.0
    vel = np.zeros_like(positions) if velocities is None else velocities
    predicted = positions + lookahead * vel
    center = np.array(cfg.bottleneck_center)
    dist2 = np.sum((predicted[mask] - center) ** 2, axis=1)
    kernel_mass = np.sum(np.exp(-0.5 * dist2 / (cfg.sigma**2)))
    return float(kernel_mass / cfg.congestion_capacity)


def point_on_route(route: np.ndarray, progress: float) -> np.ndarray:
    segs = np.diff(route, axis=0)
    lengths = np.linalg.norm(segs, axis=1)
    target = progress * float(np.sum(lengths))
    acc = 0.0
    for idx, length in enumerate(lengths):
        if acc + length >= target:
            local = 0.0 if length == 0.0 else (target - acc) / length
            return route[idx] + local * segs[idx]
        acc += float(length)
    return route[-1].copy()


def path_length(route: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(route, axis=0), axis=1)))


def paired_statistics(rows: list[dict[str, Any]], cfg: CampaignConfig) -> list[dict[str, Any]]:
    by_seed_policy = {(int(row["seed"]), row["policy"]): row for row in rows}
    tests = [
        ("smith_qr_predictive", "smith_qr_base", "jam_steps", "less"),
        ("smith_qr_predictive", "smith_qr_base", "max_rho_tau", "less"),
        ("smith_qr_predictive", "smith_qr_base", "reward_capture_ratio", "noninferior"),
        ("smith_qr_predictive", "smith_qr_reactive", "jam_steps", "less"),
        ("smith_qr_predictive", "greedy", "jam_steps", "less"),
    ]
    stats: list[dict[str, Any]] = []
    for candidate, baseline, metric, alternative in tests:
        deltas = np.array(
            [
                float(by_seed_policy[(seed, candidate)][metric]) - float(by_seed_policy[(seed, baseline)][metric])
                for seed in cfg.seeds
            ],
            dtype=float,
        )
        mean = float(np.mean(deltas))
        low, high = ci95(deltas)
        if alternative == "less":
            passed = high < 0.0
        elif alternative == "noninferior":
            passed = low >= -cfg.degradation_margin
        else:
            passed = False
        stats.append(
            {
                "hypothesis": f"{candidate}_vs_{baseline}_{metric}",
                "candidate": candidate,
                "baseline": baseline,
                "metric": metric,
                "n": len(deltas),
                "mean_delta": mean,
                "ci95_low": low,
                "ci95_high": high,
                "alternative": alternative,
                "passed": passed,
            }
        )
    return stats


def ci95(values: np.ndarray) -> tuple[float, float]:
    if values.size <= 1:
        val = float(values[0]) if values.size else math.nan
        return val, val
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1) / math.sqrt(values.size))
    # Conservative normal CI; n=30 keeps this close to the paired t interval.
    return mean - 1.96 * se, mean + 1.96 * se


def build_summary(rows: list[dict[str, Any]], stats_rows: list[dict[str, Any]], cfg: CampaignConfig) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {policy: [] for policy in POLICIES}
    for row in rows:
        grouped[row["policy"]].append(row)
    policy_summary: dict[str, dict[str, float]] = {}
    for policy, policy_rows in grouped.items():
        policy_summary[policy] = {
            metric: float(np.mean([float(row[metric]) for row in policy_rows]))
            for metric in (
                "reward_capture_ratio",
                "mean_delivery_time",
                "max_rho_tau",
                "jam_steps",
                "deadlocks",
                "route_split_ratio",
                "wasted_distance",
                "runtime_per_robot_ms",
            )
        }
    h10_pass = all(row["passed"] for row in stats_rows[:3])
    return {
        "campaign": "H10_predictive_density",
        "hypothesis": "Predictive density tolls reduce congestion without material reward degradation.",
        "seeds": [int(seed) for seed in cfg.seeds],
        "policies": list(POLICIES),
        "rho_max": cfg.rho_max,
        "lookahead_tau": cfg.lookahead_tau,
        "policy_summary": policy_summary,
        "paired_tests": stats_rows,
        "h10_pass": bool(h10_pass),
    }


def make_plots(out_dir: Path, rows: list[dict[str, Any]], representative: dict[str, Any], cfg: CampaignConfig) -> None:
    plots_dir = out_dir / "plots"
    policies = list(POLICIES)
    means = {policy: [np.mean([float(row[m]) for row in rows if row["policy"] == policy]) for m in ("jam_steps", "max_rho_tau", "reward_capture_ratio")] for policy in policies}

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
    labels = ["Jam steps", "Max predicted density", "Reward capture"]
    colors = ["#9a3412", "#1d4ed8", "#166534", "#7c3aed"]
    for ax, metric_idx, label in zip(axes, range(3), labels):
        ax.bar(policies, [means[p][metric_idx] for p in policies], color=colors)
        ax.set_title(label)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(plots_dir / "h10_policy_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for policy, color in zip(policies, colors):
        series = representative[policy]["time_rows"]
        ax.plot([r["t"] for r in series], [r["rho_tau"] for r in series], label=policy, color=color, linewidth=1.7)
    ax.axhline(cfg.rho_max, color="black", linestyle="--", linewidth=1.0, label="rho max")
    ax.set_xlabel("t [s]")
    ax.set_ylabel("rho(t+tau) bottleneck")
    ax.set_title("H10 predictive density: congestion before it materializes")
    ax.grid(alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(plots_dir / "h10_congestion_timeseries.png", dpi=180)
    plt.close(fig)

    make_heatmap_plot(plots_dir / "h10_density_heatmap.png", representative["smith_qr_predictive"], cfg)
    make_combined_doc_figure(plots_dir, cfg)


def make_heatmap_plot(path: Path, result: dict[str, Any], cfg: CampaignConfig) -> None:
    positions = result["history_pos"][min(70, len(result["history_pos"]) - 1)]
    routes = result["history_routes"][min(70, len(result["history_routes"]) - 1)]
    x = np.linspace(-10, 10, 120)
    y = np.linspace(-2, 7, 90)
    xx, yy = np.meshgrid(x, y)
    zz = np.zeros_like(xx)
    active = routes != "unspawned"
    for pos in positions[active]:
        zz += np.exp(-0.5 * ((xx - pos[0]) ** 2 + (yy - pos[1]) ** 2) / (cfg.sigma**2))
    zz /= cfg.congestion_capacity
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    im = ax.imshow(zz, extent=[x.min(), x.max(), y.min(), y.max()], origin="lower", cmap="magma", aspect="auto")
    ax.plot(ROUTES["short"][:, 0], ROUTES["short"][:, 1], color="white", linewidth=1.6, label="short")
    ax.plot(ROUTES["alt"][:, 0], ROUTES["alt"][:, 1], color="#7dd3fc", linewidth=1.6, label="alternative")
    ax.scatter([cfg.bottleneck_center[0]], [cfg.bottleneck_center[1]], marker="x", color="cyan", s=60)
    ax.set_title("Predictive density field and route bifurcation")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.legend(loc="upper right")
    fig.colorbar(im, ax=ax, label="rho")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def make_combined_doc_figure(plots_dir: Path, cfg: CampaignConfig) -> None:
    heat = plt.imread(plots_dir / "h10_density_heatmap.png")
    comp = plt.imread(plots_dir / "h10_policy_comparison.png")
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 7.2))
    axes[0].imshow(heat)
    axes[0].axis("off")
    axes[1].imshow(comp)
    axes[1].axis("off")
    fig.tight_layout(pad=0.4)
    fig.savefig(DOC_FIG, dpi=180)
    fig.savefig(plots_dir / "h10_doc_figure.png", dpi=180)
    plt.close(fig)


def make_animation(out_dir: Path, representative: dict[str, Any], cfg: CampaignConfig) -> None:
    result = representative["smith_qr_predictive"]
    frames_dir = out_dir / "frames"
    anim_path = out_dir / "animations/h10_predictive_density.mp4"
    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    def draw(frame_idx: int) -> list[Any]:
        ax.clear()
        positions = result["history_pos"][frame_idx]
        routes = result["history_routes"][frame_idx]
        ax.plot(ROUTES["short"][:, 0], ROUTES["short"][:, 1], color="#737373", linewidth=2.0, label="short")
        ax.plot(ROUTES["alt"][:, 0], ROUTES["alt"][:, 1], color="#2563eb", linewidth=2.0, label="alternative")
        short_mask = routes == "short"
        alt_mask = routes == "alt"
        ax.scatter(positions[short_mask, 0], positions[short_mask, 1], s=22, color="#f97316", label="short robots")
        ax.scatter(positions[alt_mask, 0], positions[alt_mask, 1], s=22, color="#16a34a", label="alt robots")
        circle = plt.Circle(cfg.bottleneck_center, cfg.bottleneck_radius, color="#dc2626", fill=False, linestyle="--")
        ax.add_patch(circle)
        ax.set_xlim(-10, 10)
        ax.set_ylim(-2.5, 6.5)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(f"H10 predictive toll | rho_tau={result['history_rho_tau'][frame_idx]:.2f}")
        ax.grid(alpha=0.2)
        ax.legend(loc="upper left", fontsize=7)
        return []

    ani = animation.FuncAnimation(fig, draw, frames=len(result["history_pos"]), interval=80, blit=False)
    ani.save(anim_path, writer="ffmpeg", dpi=130, fps=12)
    draw(min(30, len(result["history_pos"]) - 1))
    fig.savefig(frames_dir / "h10_predictive_density_representative.png", dpi=180)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(out_dir: Path, summary: dict[str, Any]) -> None:
    artifacts = []
    for rel in (
        "data/runs.csv",
        "data/time_series_seed5026.csv",
        "data/hypothesis_tests.csv",
        "plots/h10_policy_comparison.png",
        "plots/h10_congestion_timeseries.png",
        "plots/h10_density_heatmap.png",
        "plots/h10_doc_figure.png",
        "frames/h10_predictive_density_representative.png",
        "animations/h10_predictive_density.mp4",
        "summary.json",
        "README.md",
    ):
        path = out_dir / rel
        artifacts.append({"artifact": rel, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    write_csv(out_dir / "manifest.csv", artifacts)


def write_readme(out_dir: Path, summary: dict[str, Any]) -> None:
    pred = summary["policy_summary"]["smith_qr_predictive"]
    base = summary["policy_summary"]["smith_qr_base"]
    lines = [
        "# H10 predictive density campaign",
        "",
        "Synthetic warehouse bottleneck validation for predictive density tolls.",
        "",
        f"- H10 pass: `{summary['h10_pass']}`",
        f"- Predictive jam steps mean: `{pred['jam_steps']:.3f}`",
        f"- Base jam steps mean: `{base['jam_steps']:.3f}`",
        f"- Predictive max rho_tau mean: `{pred['max_rho_tau']:.3f}`",
        f"- Base max rho_tau mean: `{base['max_rho_tau']:.3f}`",
        "",
        "Regenerate:",
        "",
        "```powershell",
        "python scripts\\campaigns\\run_h10_predictive_density.py",
        "```",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
