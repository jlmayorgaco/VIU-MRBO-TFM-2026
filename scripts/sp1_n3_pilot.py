"""Technical pilots for N3: graph radii and runtime. No confirmatory seeds.

Two questions, both about sizing the campaign rather than answering it:

* do the five graph regimes separate on *graph* metrics alone, at every size
  and spatial scenario we intend to use? The regimes must be chosen without
  ever looking at how a method scores on them;
* what does a run cost in rounds, bytes and wall clock, so E2--E4 can be
  budgeted honestly instead of discovered mid-campaign?

Everything here draws from ``PILOT_SEED_BASE``. The confirmatory seed base is
still closed.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from sp1_n3_common import (
    DEMAND_ALPHA,
    N3_OUTPUT_ROOT,
    PILOT_SEED_BASE,
    Q_BAR_KG,
    SCENARIOS,
    WORKSPACE_M,
    write_json,
)

from viu_mrob_tfm.sp1_n3.graph import (
    REGIME_MULTIPLIERS,
    adjacency_for_regime,
    critical_radius,
    graph_metrics,
)
from viu_mrob_tfm.sp1_n3.runner import METHODS, run_method
from viu_mrob_tfm.sp1_n3.worlds import load_count_for, make_world

REGIMES = tuple(REGIME_MULTIPLIERS)


def _world(size: int, scenario: str, replicate: int, *, cv: float, pressure: float):
    seed = PILOT_SEED_BASE + 1013 * replicate + 17 * size + hash(scenario) % 997
    return make_world(
        world_id=f"pilot-{size}-{scenario}-{replicate}",
        robot_count=size,
        load_count=load_count_for(size),
        q_bar=Q_BAR_KG,
        cv=cv,
        pressure=pressure,
        scenario=scenario,
        workspace=WORKSPACE_M,
        seed=seed,
        alpha=DEMAND_ALPHA,
    )


def radius_pilot(sizes, replicates: int, cv: float, pressure: float) -> pd.DataFrame:
    """Graph metrics per regime. Method outcomes are deliberately absent."""

    rows = []
    for size in sizes:
        for scenario in SCENARIOS:
            for replicate in range(replicates):
                world = _world(size, scenario, replicate, cv=cv, pressure=pressure)
                r_c = critical_radius(world.robot_positions)
                for regime in REGIMES:
                    adjacency = adjacency_for_regime(world.robot_positions, regime)
                    metrics = graph_metrics(adjacency)
                    rows.append(
                        {
                            "n_robots": size,
                            "scenario": scenario,
                            "replicate": replicate,
                            "regime": regime,
                            "critical_radius_m": r_c,
                            "multiplier": REGIME_MULTIPLIERS[regime],
                            **metrics.as_dict(),
                        }
                    )
    return pd.DataFrame(rows)


def runtime_pilot(sizes, replicates: int, cv: float, pressure: float) -> pd.DataFrame:
    """Rounds, bytes and wall clock per method, on connected regimes only."""

    rows = []
    for size in sizes:
        for replicate in range(replicates):
            world = _world(size, "uniform", replicate, cv=cv, pressure=pressure)
            for regime in ("complete", "medium", "threshold"):
                adjacency = adjacency_for_regime(world.robot_positions, regime)
                for method in METHODS:
                    started = time.perf_counter()
                    record = run_method(world, adjacency, method, regime=regime)
                    elapsed = 1_000.0 * (time.perf_counter() - started)
                    rows.append(
                        {
                            "n_robots": size,
                            "n_loads": world.n_loads,
                            "replicate": replicate,
                            "regime": regime,
                            "method": method,
                            "wall_ms": elapsed,
                            "rounds": record.observation.rounds,
                            "messages": record.observation.messages,
                            "bytes": record.observation.bytes_sent,
                            "bytes_per_robot": record.observation.bytes_sent / size,
                            "algorithm_status": record.observation.algorithm_status,
                            "consistent": record.observation.consistent,
                            "cycle_detected": record.observation.cycle_detected,
                            "raw_certificate": record.certificate.status,
                            "total_deficit": record.certificate.total_deficit,
                            "distance_cost": record.certificate.distance_cost,
                        }
                    )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[16, 24, 32])
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--capacity-cv", type=float, default=0.65)
    parser.add_argument("--pressure", type=float, default=0.85)
    parser.add_argument("--output-dir", type=Path, default=N3_OUTPUT_ROOT)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    radii = radius_pilot(args.sizes, args.replicates, args.capacity_cv, args.pressure)
    radii.to_csv(args.output_dir / "radius_pilot.csv", index=False)

    timings = runtime_pilot(
        args.sizes, args.replicates, args.capacity_cv, args.pressure
    )
    timings.to_csv(args.output_dir / "runtime_pilot.csv", index=False)

    summary = {
        "seed_base": PILOT_SEED_BASE,
        "confirmatory_seed_opened": False,
        "sizes": list(args.sizes),
        "replicates": args.replicates,
        "capacity_cv": args.capacity_cv,
        "pressure": args.pressure,
        "regimes": list(REGIMES),
        "radius_rows": int(len(radii)),
        "runtime_rows": int(len(timings)),
    }
    write_json(args.output_dir / "pilot_manifest.json", summary)

    print("\n== graph regimes (median over scenarios and replicates) ==")
    grouped = radii.groupby(["n_robots", "regime"], sort=False).median(
        numeric_only=True
    )
    print(
        grouped[["mean_degree", "diameter", "lambda_2", "components"]].round(3).to_string()
    )

    print("\n== runtime and communication (median) ==")
    view = timings.groupby(["n_robots", "regime", "method"], sort=False).median(
        numeric_only=True
    )
    print(
        view[["rounds", "messages", "bytes_per_robot", "wall_ms"]]
        .round(1)
        .to_string()
    )

    print("\n== raw feasibility by method (pilot only, not a result) ==")
    rates = (
        timings.assign(feasible=timings["raw_certificate"] == "FEASIBLE")
        .groupby(["method", "regime"], sort=False)["feasible"]
        .mean()
        .round(3)
    )
    print(rates.to_string())
    print(f"\nwrote {args.output_dir}")


if __name__ == "__main__":
    main()
