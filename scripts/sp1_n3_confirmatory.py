"""SP1.N3 confirmatory campaign: distributed baselines on the frozen N2 problem.

Three questions, one each:

E1  do the implementations respect the contract, their invariants and
    determinism? Executed as the test batteries, summarised here.
E2  what feasibility and what distance cost do the baselines reach, measured
    against the N2 oracle on the very same worlds?
E3  what does locality cost, in feasibility, rounds and bytes, as the
    communication graph thins from complete to barely connected -- and does a
    permanent partition break coordination, as it must?

The script only writes under ``n3_v1``. N1 and N2 are read-only: the world
generator is replayed from ``sp1_n2_confirmatory`` rather than reimplemented,
and the oracle is ``sp1_n2_oracle`` unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

import sp1_n2_oracle as oracle
from sp1_n3_common import N3_OUTPUT_ROOT, REPOSITORY_ROOT, write_json

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime, graph_metrics
from viu_mrob_tfm.sp1_n3.runner import METHODS, run_method
from viu_mrob_tfm.sp1_n3.worlds import make_world

import sp1_a1_hungarian as homogeneous


DEFAULT_CONFIG = (
    REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n3_confirmatory_v1.yaml"
)
DEFAULT_OUTPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n3_v1"

SCENARIO_LABELS = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}


def load_config(path: Path, *, smoke: bool) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if smoke:
        # A smoke run proves the pipeline end to end. It uses its own seed
        # base so it can never be mistaken for, or mixed with, confirmatory
        # rows.
        payload["campaign_id"] = payload["campaign_id"] + "_SMOKE"
        payload["base_seed"] = 999_000_001
        payload["e2_quality"]["capacity_cv"] = [0.00, 0.65]
        payload["e2_quality"]["pressure"] = [0.85]
        payload["e2_quality"]["scenarios"] = ["uniform", "corridor"]
        payload["e2_quality"]["seeds_per_cell"] = 3
        payload["e3_locality"]["capacity_cv"] = [0.65]
        payload["e3_locality"]["scenarios"] = ["uniform", "corridor"]
        payload["e3_locality"]["seeds_per_cell"] = 3
    return payload


def progress(label: str, index: int, total: int) -> None:
    if index == total or index % max(1, total // 20) == 0:
        print(f"  {label}: {index}/{total}", flush=True)


def world_for(
    config: Mapping[str, Any],
    section: Mapping[str, Any],
    *,
    scenario: str,
    cv: float,
    pressure: float,
    replicate: int,
):
    """One N2 world, addressed by a seed derived from the whole cell.

    The capacity stream is keyed separately by CV inside ``make_world``, so
    geometry and demand stay identical across heterogeneity levels and the
    design is paired within a world.
    """

    seed = homogeneous.stable_seed(
        int(config["base_seed"]), "n3", scenario, pressure, replicate
    )
    return make_world(
        world_id=f"{scenario}-{pressure}-{replicate}",
        robot_count=int(section["robot_count"]),
        load_count=int(section["load_count"]),
        q_bar=float(config["q_bar_kg"]),
        cv=float(cv),
        pressure=float(pressure),
        scenario=scenario,
        workspace=tuple(config["workspace_m"]),
        seed=seed,
        alpha=float(config["generator"]["demand_split_alpha"]),
    )


def solve_oracle(world, time_limit_s: float) -> dict[str, Any]:
    """The N2 MILP, unchanged. Its status is kept separate from the method's."""

    model = oracle.build_model(
        capacities=world.capacities,
        masses=world.demands,
        distance=world.distances,
    )
    result = oracle.solve(model, integral=True, time_limit_s=time_limit_s)
    return {
        "oracle_status": result.status,
        "oracle_objective": (
            float(result.distance_objective) if result.has_incumbent else float("nan")
        ),
        "oracle_runtime_s": float(result.runtime_s),
        "oracle_feasible": bool(result.has_incumbent),
        "oracle_certified": bool(result.certified_optimal),
    }


def _row(world, cv, record, oracle_row, *, experiment: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "experiment": experiment,
        "world_id": f"{experiment}:{world.world_id}:cv{cv}",
        "world_digest": world.digest(),
        "world_seed": world.seed,
        "scenario": world.scenario,
        "scenario_label": SCENARIO_LABELS.get(world.scenario, world.scenario),
        "capacity_cv": cv,
        "realized_cv": world.realized_cv,
        "pressure": world.pressure,
        "N": world.n_robots,
        "K": world.n_loads,
    }
    row.update(record.as_row())
    row.update(oracle_row)
    # A gap is only defined where the oracle certified the optimum and the
    # method produced something feasible. Everything else stays NaN rather
    # than being imputed.
    gap = float("nan")
    if (
        oracle_row["oracle_status"] == oracle.OPTIMAL
        and record.certificate.feasible
        and oracle_row["oracle_objective"] > 0.0
    ):
        gap = (
            record.certificate.distance_cost - oracle_row["oracle_objective"]
        ) / oracle_row["oracle_objective"]
    row["optimality_gap"] = gap
    return row


def run_e2(config: Mapping[str, Any]) -> pd.DataFrame:
    """Feasibility and quality against the oracle, on one fixed graph regime."""

    section = config["e2_quality"]
    regime = str(section["graph_regime"])
    cells = [
        (scenario, cv, pressure, replicate)
        for scenario in section["scenarios"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    rows: list[dict[str, Any]] = []
    for index, (scenario, cv, pressure, replicate) in enumerate(cells, 1):
        world = world_for(
            config, section, scenario=scenario, cv=cv, pressure=pressure,
            replicate=replicate,
        )
        oracle_row = solve_oracle(world, float(section["oracle_time_limit_s"]))
        adjacency = adjacency_for_regime(world.robot_positions, regime)
        for method in METHODS:
            record = run_method(world, adjacency, method, regime=regime)
            rows.append(_row(world, cv, record, oracle_row, experiment="E2"))
        progress("E2", index, len(cells))
    return pd.DataFrame(rows)


def run_e3(config: Mapping[str, Any]) -> pd.DataFrame:
    """The price of locality: the same worlds under five graph regimes."""

    section = config["e3_locality"]
    regimes = list(section["regimes"])
    cells = [
        (scenario, cv, pressure, replicate)
        for scenario in section["scenarios"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    rows: list[dict[str, Any]] = []
    for index, (scenario, cv, pressure, replicate) in enumerate(cells, 1):
        world = world_for(
            config, section, scenario=scenario, cv=cv, pressure=pressure,
            replicate=replicate,
        )
        oracle_row = solve_oracle(world, 30.0)
        for regime in regimes:
            adjacency = adjacency_for_regime(world.robot_positions, regime)
            metrics = graph_metrics(adjacency)
            for method in METHODS:
                record = run_method(world, adjacency, method, regime=regime)
                row = _row(world, cv, record, oracle_row, experiment="E3")
                row["regime_lambda_2"] = metrics.algebraic_connectivity
                row["regime_components"] = metrics.components
                rows.append(row)
        progress("E3", index, len(cells))
    return pd.DataFrame(rows)


def environment_lock() -> dict[str, Any]:
    import scipy

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
    }


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:  # pragma: no cover - only when git is unavailable
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="tiny run on a separate seed base, to prove the pipeline",
    )
    args = parser.parse_args()

    config = load_config(args.config, smoke=args.smoke)
    output = args.output_dir if not args.smoke else args.output_dir.with_name(
        args.output_dir.name + "_smoke"
    )
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    print(f"campaign {config['campaign_id']} (base_seed {config['base_seed']})")
    frames = {"e2_quality": run_e2(config), "e3_locality": run_e3(config)}

    frozen: dict[str, Any] = {}
    for name, frame in frames.items():
        path = raw / f"{name}_runs.csv"
        frame.to_csv(path, index=False)
        frozen[name] = {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "rows": int(len(frame)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    write_json(
        output / "manifest.json",
        {
            "schema_version": "sp1-n3-campaign-v1",
            "campaign_id": config["campaign_id"],
            "base_seed": config["base_seed"],
            "smoke": bool(args.smoke),
            "config_sha256": hashlib.sha256(
                args.config.read_bytes()
            ).hexdigest(),
            "frozen_raw": frozen,
            "environment": environment_lock(),
            "git_commit": git_commit(),
            "contract": config["contract"],
        },
    )
    for name, frame in frames.items():
        print(f"{name}: {len(frame)} filas")
    print(f"escrito en {output}")


if __name__ == "__main__":
    main()
