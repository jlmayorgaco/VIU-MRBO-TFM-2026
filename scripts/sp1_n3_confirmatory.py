"""SP1.N3 confirmatory campaign: distributed baselines on the frozen N2 problem.

Three questions, one each:

E1  do the implementations respect the contract, their invariants and
    determinism? Executed as the test batteries, summarised, and a gate: if it
    fails, this campaign must not run.
E2  what feasibility and what distance cost do the baselines reach, measured
    against the N2 oracle on the very same worlds?
E3  what does locality cost, in feasibility, rounds and bytes, as the graph
    thins from complete to barely connected -- and does a permanent partition
    break coordination, as it must?

The script only writes under ``n3_v1``. N1 and N2 are read-only: the world
generator is replayed from ``sp1_n2_confirmatory`` rather than reimplemented,
and the oracle is ``sp1_n2_oracle`` unchanged.

Packet loss, delay and scale are deliberately absent. They will be a stress
campaign shared with N4, under paired channel realizations, so that every
method meets the same network rather than N3's being repeated later.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml

import sp1_a1_hungarian as homogeneous
import sp1_n2_oracle as oracle
from sp1_n3_common import REPOSITORY_ROOT, write_json

from viu_mrob_tfm.sp1_n3 import PROTOCOL_VERSION
from viu_mrob_tfm.sp1_n3.graph import (
    REGIME_MULTIPLIERS,
    adjacency_for_regime,
    critical_radius,
    graph_metrics,
)
from viu_mrob_tfm.sp1_n3.runner import METHODS, run_method
from viu_mrob_tfm.sp1_n3.worlds import make_world


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
        # Its own seed base, so smoke rows can never be mistaken for, or mixed
        # with, confirmatory ones.
        payload["campaign_id"] += "_SMOKE"
        payload["base_seed"] = 999_000_001
        payload["e2_quality"].update(
            capacity_cv=[0.00, 0.65], pressure=[0.85],
            scenarios=["uniform", "corridor"], seeds_per_cell=2,
        )
        payload["e3_locality"].update(
            capacity_cv=[0.65], scenarios=["uniform"], seeds_per_cell=2,
        )
    return payload


def progress(label: str, index: int, total: int) -> None:
    if index == total or index % max(1, total // 20) == 0:
        print(f"  {label}: {index}/{total}", flush=True)


# ------------------------------------------------------------------- worlds
def world_for(config, section, *, scenario, cv, pressure, replicate):
    """One N2 world, addressed by a seed derived from the whole cell.

    The capacity stream is keyed separately by CV inside ``make_world``, so
    geometry and demand stay identical across heterogeneity levels: within a
    world the design is paired.
    """

    seed = homogeneous.stable_seed(
        int(config["base_seed"]), "n3", scenario, pressure, replicate
    )
    return make_world(
        world_id=f"{scenario}-p{pressure}-r{replicate}",
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


def world_row(world, cv, key) -> dict[str, Any]:
    return {
        "world_key": key,
        "world_id": world.world_id,
        "world_seed": world.seed,
        "world_digest": world.digest(),
        "scenario": world.scenario,
        "scenario_label": SCENARIO_LABELS.get(world.scenario, world.scenario),
        "capacity_cv": cv,
        "realized_cv": world.realized_cv,
        "pressure": world.pressure,
        "N": world.n_robots,
        "K": world.n_loads,
        "total_capacity": float(world.capacities.sum()),
        "total_demand": float(world.demands.sum()),
        "critical_radius_m": critical_radius(world.robot_positions),
    }


# ------------------------------------------------------------------- oracle
def solve_oracle(world, time_limit_s: float) -> dict[str, Any]:
    """The frozen N2 MILP. Its status stays separate from the method's."""

    model = oracle.build_model(
        capacities=world.capacities, masses=world.demands, distance=world.distances
    )
    result = oracle.solve(model, integral=True, time_limit_s=time_limit_s)
    return {
        "oracle_status": result.status,
        "oracle_objective": (
            float(result.distance_objective) if result.has_incumbent else float("nan")
        ),
        "oracle_bound": float(result.bound),
        "oracle_gap": float(result.mip_gap),
        "oracle_runtime_s": float(result.runtime_s),
        # An incumbent proves a solution exists, so it counts as feasible even
        # when optimality was not certified.
        "oracle_feasible": bool(result.has_incumbent),
        "oracle_certified": bool(result.certified_optimal),
    }


# -------------------------------------------------------------------- graph
def graph_row(world, regime: str, key: str) -> tuple[np.ndarray, dict[str, Any]]:
    adjacency = adjacency_for_regime(world.robot_positions, regime)
    metrics = graph_metrics(adjacency)
    r_c = critical_radius(world.robot_positions)
    multiplier = REGIME_MULTIPLIERS[regime]
    row = {
        "world_key": key,
        "graph_regime": regime,
        "radius": float("nan") if multiplier is None else multiplier * r_c,
        "radius_over_rc": float("nan") if multiplier is None else float(multiplier),
        "graph_seed": world.seed,  # the graph is a function of the world geometry
        **{f"graph_{k}": v for k, v in metrics.as_dict().items()},
    }
    return adjacency, row


# --------------------------------------------------------------------- rows
def method_row(config, world_key, world, cv, graph, record, oracle_row, experiment):
    row: dict[str, Any] = {
        "campaign_id": config["campaign_id"],
        "experiment": experiment,
        "world_key": world_key,
        "world_id": world.world_id,
        "world_seed": world.seed,
        "scenario": world.scenario,
        "N": world.n_robots,
        "K": world.n_loads,
        "capacity_cv": cv,
        "pressure": world.pressure,
        "implementation_version": PROTOCOL_VERSION,
    }
    row.update({k: v for k, v in graph.items() if k != "world_key"})
    observed = record.observation
    certificate = record.certificate
    row.update(
        {
            "method": record.method,
            "algorithm_status": observed.algorithm_status,
            "cycle_observed": observed.cycle_detected,
            "consistent": observed.consistent,
            "raw_certificate": certificate.status,
            "distance_cost": certificate.distance_cost,
            "capacity_deficit": certificate.total_deficit,
            "robot_conflict": certificate.conflicts,
            "excess_capacity": certificate.excess_capacity,
            "assigned_robots": certificate.assigned_robots,
            "max_coalition_size": max(certificate.coalition_sizes, default=0),
            "unserved_loads": certificate.unserved_loads,
            "rounds": observed.rounds,
            "messages": observed.messages,
            "bytes": observed.bytes_sent,
            "messages_per_agent": observed.messages / world.n_robots,
            "bytes_per_agent": observed.bytes_sent / world.n_robots,
            "runtime_ms": record.runtime_ms,
        }
    )
    row.update(oracle_row)
    # A gap exists only where the oracle certified the optimum and the method
    # produced something feasible. Never against an uncertified incumbent, and
    # never imputed.
    gap = float("nan")
    if (
        oracle_row["oracle_status"] == oracle.OPTIMAL
        and certificate.feasible
        and oracle_row["oracle_objective"] > 0.0
    ):
        gap = (
            certificate.distance_cost - oracle_row["oracle_objective"]
        ) / oracle_row["oracle_objective"]
    row["optimality_gap"] = gap
    return row


def run_experiment(config, section, *, experiment, regimes):
    cells = [
        (scenario, cv, pressure, replicate)
        for scenario in section["scenarios"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    runs, worlds, graphs, oracles = [], [], [], []
    limit = float(section.get("oracle_time_limit_s", 30.0))
    for index, (scenario, cv, pressure, replicate) in enumerate(cells, 1):
        world = world_for(
            config, section, scenario=scenario, cv=cv, pressure=pressure,
            replicate=replicate,
        )
        key = f"{experiment}:{scenario}:p{pressure}:cv{cv}:r{replicate}"
        worlds.append(world_row(world, cv, key))
        oracle_row = solve_oracle(world, limit)
        oracles.append({"world_key": key, **oracle_row})
        for regime in regimes:
            adjacency, grow = graph_row(world, regime, key)
            graphs.append(grow)
            for method in METHODS:
                record = run_method(world, adjacency, method, regime=regime)
                runs.append(
                    method_row(
                        config, key, world, cv, grow, record, oracle_row, experiment
                    )
                )
        progress(experiment, index, len(cells))
    return (
        pd.DataFrame(runs),
        pd.DataFrame(worlds),
        pd.DataFrame(graphs),
        pd.DataFrame(oracles),
    )


# ---------------------------------------------------------------- integrity
def check_integrity(frames: Mapping[str, pd.DataFrame], expected: Mapping[str, int]):
    """Fail loudly rather than write a campaign nobody can trust."""

    problems: list[str] = []
    for name, count in expected.items():
        got = len(frames[name])
        if got != count:
            problems.append(f"{name}: expected {count} rows, got {got}")
    for name in ("e2_runs", "e3_runs"):
        frame = frames[name]
        if frame.empty:
            continue
        duplicated = frame.duplicated(["world_key", "graph_regime", "method"]).sum()
        if duplicated:
            problems.append(f"{name}: {duplicated} duplicate (world, graph, method)")
        missing = frame[["distance_cost", "rounds", "bytes"]].isna().sum().sum()
        if missing:
            problems.append(f"{name}: {missing} missing primary metrics")
        per_cell = frame.groupby(["world_key", "graph_regime"]).method.nunique()
        if not (per_cell == len(METHODS)).all():
            problems.append(f"{name}: some cells lack all {len(METHODS)} methods")
        if not frame["bytes"].ge(7 * frame["messages"]).all():
            problems.append(f"{name}: bytes below envelope floor for some rows")
        if not frame["rounds"].ge(1).all():
            problems.append(f"{name}: non-positive round counts")
        bad = set(frame["raw_certificate"]) - {
            "FEASIBLE", "CAPACITY_DEFICIT", "ROBOT_CONFLICT", "DEFICIT_AND_CONFLICT"
        }
        if bad:
            problems.append(f"{name}: unknown certificate values {bad}")
    return problems


def environment_lock() -> dict[str, Any]:
    import scipy

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "protocol": PROTOCOL_VERSION,
    }


def git_state() -> dict[str, Any]:
    def run(*args):
        return subprocess.run(
            args, cwd=REPOSITORY_ROOT, capture_output=True, text=True
        ).stdout.strip()

    return {
        "commit": run("git", "rev-parse", "HEAD") or "unknown",
        "tree_dirty": bool(run("git", "status", "--porcelain")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config, smoke=args.smoke)
    output = (
        args.output_dir
        if not args.smoke
        else args.output_dir.with_name(args.output_dir.name + "_smoke")
    )
    raw = output / "raw"
    if not args.smoke and raw.exists() and any(raw.glob("*.csv")):
        raise SystemExit(
            f"{raw} already holds RAW. A confirmatory campaign is never "
            "overwritten; start a v2 config and campaign_id instead."
        )
    raw.mkdir(parents=True, exist_ok=True)

    config_sha = hashlib.sha256(args.config.read_bytes()).hexdigest()
    git = git_state()
    print(f"campaign   {config['campaign_id']}")
    print(f"base_seed  {config['base_seed']}")
    print(f"config     {config_sha}")
    print(f"commit     {git['commit']}  dirty={git['tree_dirty']}")
    print(f"protocol   {PROTOCOL_VERSION}")

    e2 = run_experiment(
        config, config["e2_quality"], experiment="E2",
        regimes=[str(config["e2_quality"]["graph_regime"])],
    )
    e3 = run_experiment(
        config, config["e3_locality"], experiment="E3",
        regimes=list(config["e3_locality"]["regimes"]),
    )

    frames = {
        "e2_runs": e2[0],
        "e3_runs": e3[0],
        "worlds": pd.concat([e2[1], e3[1]], ignore_index=True),
        "graph_instances": pd.concat([e2[2], e3[2]], ignore_index=True),
        "oracle_runs": pd.concat([e2[3], e3[3]], ignore_index=True),
    }
    expected = {
        "e2_runs": len(e2[1]) * 1 * len(METHODS),
        "e3_runs": len(e3[1]) * len(config["e3_locality"]["regimes"]) * len(METHODS),
    }
    problems = check_integrity(frames, expected)
    if problems:
        for line in problems:
            print(f"INTEGRITY: {line}")
        raise SystemExit("integrity checks failed; RAW not written")

    frozen: dict[str, Any] = {}
    for name, frame in frames.items():
        path = raw / f"{name}.csv"
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
            "config_sha256": config_sha,
            "frozen_raw": frozen,
            "environment": environment_lock(),
            "git": git,
            "contract": config["contract"],
            "runs_solvers": True,
            "note": (
                "The oracle is the frozen N2 MILP; the methods are the N3 "
                "baselines. No recovery, no packet loss, no delay."
            ),
        },
    )
    for name, frame in frames.items():
        print(f"{name}: {len(frame)} filas")
    print(f"escrito en {output}")


if __name__ == "__main__":
    main()
