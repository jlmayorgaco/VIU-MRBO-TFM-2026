"""Re-render audited SP4 tables and figures without rerunning the campaign."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.sp4.docking_game import (
    _plot_performance,
    _plot_scaling,
    _plot_scenario_matrix,
    _plot_theory,
    _plot_tradeoff,
    _plot_trajectory,
    _theory_audit,
    _write_csv,
    _write_report,
    build_docking_world,
    evaluate_hypotheses,
    simulate_docking,
    summarize_runs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    with (tables / "runs.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    summary = summarize_runs(rows)
    hypotheses = evaluate_hypotheses(rows, list(config.get("hypotheses", [])))
    _write_csv(tables / "summary.csv", summary)
    _write_csv(tables / "hypothesis_results.csv", hypotheses)
    ranking: list[dict[str, object]] = []
    ordered = sorted(
        summary,
        key=lambda row: (-float(row["safe_docking_success"]), float(row["any_collision"])),
    )
    for rank, row in enumerate(ordered, start=1):
        method = str(row["method"])
        if method in {"direct_to_slot", "apf_navigation", "rvo_proxy"}:
            family = "classic_local"
        elif method == "cbf_qp":
            family = "safety"
        elif method == "central_potential_reference":
            family = "model_based_reference"
        elif method.startswith("nash_pd"):
            family = "nash_seeking"
        else:
            family = "population"
        ranking.append(
            {
                "method": method,
                "method_variant": method,
                "method_family": family,
                "rank": rank,
                "safe_docking_success_mean": row["safe_docking_success"],
                "any_collision_mean": row["any_collision"],
                "timeout_mean": row["timeout"],
                "runtime_s_mean": row["runtime_s"],
            }
        )
    _write_csv(tables / "performance_ranking.csv", ranking)

    seed_cfg = dict(config["seeds"])
    seeds = range(int(seed_cfg["start"]), int(seed_cfg["start"]) + int(seed_cfg["count"]))
    scenarios = [str(item["id"]) for item in config["scenarios"]]
    robot_counts = [int(value) for value in config["robot_counts"]]
    worlds = [
        build_docking_world(scenario, seed, n_robots)
        for scenario in scenarios
        for n_robots in robot_counts
        for seed in seeds
    ]
    audit, trace, qp_value = _theory_audit(config, worlds, output_dir=output)

    _plot_performance(summary, figures / "fig-sp4-docking-performance.png")
    _plot_tradeoff(summary, figures / "fig-sp4-docking-tradeoff.png")
    _plot_scenario_matrix(rows, figures / "fig-sp4-scenario-matrix.png")
    _plot_scaling(rows, figures / "fig-sp4-scaling.png")
    _plot_theory(trace, qp_value, figures / "fig-sp4-kkt-potential.png")

    simulation = dict(config.get("simulation", {}))
    game = dict(config.get("game", {}))
    representative = build_docking_world(
        str(config.get("representative_scenario", "crossing")),
        int(seed_cfg["start"]),
        robot_counts[0],
    )
    selected_methods = (
        "direct_to_slot",
        "cbf_qp",
        "nash_pd_exact",
        "replicator_primitives",
    )
    selected = [
        simulate_docking(
            representative,
            method,
            dt_s=float(simulation.get("dt_s", 0.16)),
            horizon_s=float(simulation.get("horizon_s", 35.0)),
            game_steps=int(game.get("steps", 20)),
            replan_interval_steps=int(game.get("replan_interval_steps", 3)),
            central_steps=int(game.get("central_steps", 70)),
            primal_dt=float(game.get("primal_dt", 0.12)),
            dual_dt=float(game.get("dual_dt", 0.10)),
            congestion_weight=float(game.get("congestion_weight", 0.38)),
            regularization=float(game.get("regularization", 0.04)),
            consensus_rounds=int(game.get("consensus_rounds", 4)),
            barrier_gamma=float(simulation.get("barrier_gamma", 2.6)),
            barrier_iterations=int(simulation.get("barrier_iterations", 30)),
        )
        for method in selected_methods
    ]
    _plot_trajectory(representative, selected, figures / "fig-sp4-docking-trajectories.png")

    _write_report(
        output / "report.md",
        str(config["experiment_id"]),
        rows,
        summary,
        hypotheses,
        audit,
    )
    print(
        json.dumps(
            {
                "rows": len(rows),
                "audit": audit["status"],
                "initial_collisions": audit["initial_collision_count"],
                "figures": len(list(figures.glob("*.png"))),
            }
        )
    )


if __name__ == "__main__":
    main()