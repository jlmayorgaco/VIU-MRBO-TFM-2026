"""Run the independent SP4 v4 development or confirmatory campaign."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.sp4.docking_game_v4 import (  # noqa: E402
    V4_METHOD_LABELS,
    build_docking_world_v4,
    minimum_goal_clearance,
    simulate_docking_v4,
)


def _row(result: Any) -> dict[str, Any]:
    row = asdict(result)
    row.pop("positions")
    row.pop("potential_trace")
    row.pop("kkt_trace")
    for key in ("safe_docking_success", "arrival_success", "any_collision", "timeout"):
        row[key] = int(bool(row[key]))
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = (
        "safe_docking_success", "any_collision", "timeout", "docking_time_s",
        "min_clearance_m", "final_position_error_m", "energy_wh", "path_length_m",
        "exec_barrier_violations", "max_exec_barrier_residual",
        "torque_saturation_events", "final_kkt_residual", "max_capacity_violation",
        "messages", "runtime_s",
    )
    output: list[dict[str, Any]] = []
    for method in dict.fromkeys(str(row["method"]) for row in rows):
        subset = [row for row in rows if row["method"] == method]
        record: dict[str, Any] = {
            "method": method,
            "label": V4_METHOD_LABELS.get(method, method),
            "n": len(subset),
        }
        for metric in metrics:
            values = np.asarray([float(row[metric]) for row in subset], dtype=float)
            finite = values[np.isfinite(values)]
            record[metric] = float(np.mean(finite)) if finite.size else float("nan")
        output.append(record)
    return output


def _plot_performance(summary: list[dict[str, Any]], path: Path) -> None:
    labels = [str(row["label"]) for row in summary]
    y = np.arange(len(labels))
    success = [float(row["safe_docking_success"]) for row in summary]
    collision = [float(row["any_collision"]) for row in summary]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), sharey=True)
    axes[0].barh(y, success, color="#0072B2")
    axes[1].barh(y, collision, color="#D55E00")
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Fracción de acoplamientos seguros")
    axes[1].set_xlabel("Fracción con colisión")
    for ax in axes:
        ax.set_xlim(0.0, 1.02)
        ax.grid(axis="x", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def _plot_matrix(rows: list[dict[str, Any]], path: Path) -> None:
    methods = list(dict.fromkeys(str(row["method"]) for row in rows))
    scenarios = list(dict.fromkeys(str(row["scenario"]) for row in rows))
    matrix = np.zeros((len(methods), len(scenarios)), dtype=float)
    for i, method in enumerate(methods):
        for j, scenario in enumerate(scenarios):
            subset = [row for row in rows if row["method"] == method and row["scenario"] == scenario]
            matrix[i, j] = np.mean([float(row["safe_docking_success"]) for row in subset])
    fig, ax = plt.subplots(figsize=(10.5, max(4.2, 0.55 * len(methods))))
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(len(scenarios)), scenarios, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(methods)), [V4_METHOD_LABELS.get(m, m) for m in methods])
    for i in range(len(methods)):
        for j in range(len(scenarios)):
            ax.text(j, i, f"{matrix[i,j]:.2f}", ha="center", va="center", color="white" if matrix[i,j] < 0.75 else "black")
    fig.colorbar(image, ax=ax, label="Éxito seguro")
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def _plot_scaling(rows: list[dict[str, Any]], path: Path) -> None:
    counts = sorted({int(row["n_robots"]) for row in rows})
    methods = list(dict.fromkeys(str(row["method"]) for row in rows))
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.8))
    for method in methods:
        runtime, messages, success = [], [], []
        for count in counts:
            subset = [row for row in rows if row["method"] == method and int(row["n_robots"]) == count]
            runtime.append(np.mean([float(row["runtime_s"]) for row in subset]))
            messages.append(np.mean([float(row["messages"]) for row in subset]))
            success.append(np.mean([float(row["safe_docking_success"]) for row in subset]))
        label = V4_METHOD_LABELS.get(method, method)
        axes[0].plot(counts, runtime, "o-", label=label)
        axes[1].plot(counts, messages, "o-")
        axes[2].plot(counts, success, "o-")
    axes[0].set_ylabel("CPU por ejecución (s)")
    axes[1].set_ylabel("Mensajes")
    axes[2].set_ylabel("Éxito seguro")
    for ax in axes:
        ax.set_xlabel("Robots")
        ax.grid(alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(fontsize=6, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def _plot_trajectories(world: Any, results: list[Any], path: Path) -> None:
    fig, axes = plt.subplots(1, len(results), figsize=(4.0 * len(results), 4.0), squeeze=False)
    for ax, result in zip(axes[0], results):
        trace = result.positions
        for i in range(world.n_robots):
            ax.plot(trace[:, i, 0], trace[:, i, 1], lw=1.1)
            ax.scatter(*world.target_pose[i, :2], marker="x", s=24, color="black")
        load = plt.Circle((0, 0), world.load_radius_m, color="#999999", alpha=0.35)
        ax.add_patch(load)
        for obstacle in world.obstacles:
            ax.add_patch(plt.Circle(obstacle[:2], obstacle[2], color="#D55E00", alpha=0.28))
        ax.set_title(V4_METHOD_LABELS.get(result.method, result.method), fontsize=8)
        ax.set_aspect("equal")
        ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def run(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    output = ROOT / str(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    seed_start = int(config["seeds"]["start"])
    seed_count = int(config["seeds"]["count"])
    methods = [str(item["id"]) for item in config["methods"]]
    scenarios = [str(item["id"]) for item in config["scenarios"]]
    sim = dict(config.get("simulation", {}))
    rows: list[dict[str, Any]] = []
    representative: tuple[Any, list[Any]] | None = None
    goal_clearances: list[float] = []
    for seed in range(seed_start, seed_start + seed_count):
        for scenario in scenarios:
            for n_robots in [int(value) for value in config["robot_counts"]]:
                world = build_docking_world_v4(scenario, seed, n_robots)
                goal_clearances.append(minimum_goal_clearance(world))
                world_results = []
                for method in methods:
                    result = simulate_docking_v4(world, method, **sim)
                    rows.append(_row(result))
                    world_results.append(result)
                if representative is None and scenario == str(config.get("representative_scenario", scenarios[0])):
                    representative = (world, world_results)
    summary = _summary(rows)
    _write_csv(tables / "runs.csv", rows)
    _write_csv(tables / "summary.csv", summary)
    _plot_performance(summary, figures / "fig-sp4-v4-performance.png")
    _plot_matrix(rows, figures / "fig-sp4-v4-scenario-matrix.png")
    _plot_scaling(rows, figures / "fig-sp4-v4-scaling.png")
    if representative is not None:
        _plot_trajectories(representative[0], representative[1], figures / "fig-sp4-v4-trajectories.png")
    gates = dict(config.get("audit_gates", {}))
    audit = {
        "protocol_version": "SP4-v4",
        "campaign_mode": str(config.get("mode", "development")),
        "positions_repaired_after_integration": False,
        "minimum_goal_clearance_m": float(min(goal_clearances)),
        "total_exec_barrier_violations": int(sum(int(row["exec_barrier_violations"]) for row in rows)),
        "maximum_exec_barrier_residual": float(max(float(row["max_exec_barrier_residual"]) for row in rows)),
        "total_physical_torque_saturations": int(sum(int(row["torque_saturation_events"]) for row in rows)),
        "maximum_capacity_violation": float(max(float(row["max_capacity_violation"]) for row in rows)),
    }
    audit["gates_pass"] = bool(
        audit["minimum_goal_clearance_m"] >= float(gates.get("min_goal_clearance_m", 0.0))
        and audit["total_exec_barrier_violations"] <= int(gates.get("max_exec_barrier_violations", 0))
        and audit["total_physical_torque_saturations"] <= int(gates.get("max_physical_torque_saturations", 0))
        and audit["maximum_capacity_violation"] <= float(gates.get("max_capacity_violation", 0.01))
    )
    (output / "theory_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    report = [
        f"# {config['experiment_id']}", "",
        f"Mode: **{config.get('mode', 'development')}**", "",
        f"Runs: **{len(rows)}**", "",
        f"Theory gates: **{'PASS' if audit['gates_pass'] else 'FAIL'}**", "",
        "| Method | n | Safe success | Collision | Docking time (s) | CPU (s) | Max capacity |", "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        report.append(f"| {item['label']} | {item['n']} | {item['safe_docking_success']:.3f} | {item['any_collision']:.3f} | {item['docking_time_s']:.2f} | {item['runtime_s']:.2f} | {item['max_capacity_violation']:.4g} |")
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest = {"experiment_id": config["experiment_id"], "output_dir": str(output), "runs": len(rows), "audit": audit}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config), indent=2))


if __name__ == "__main__":
    main()