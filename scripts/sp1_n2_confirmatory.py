"""SP1.N2 confirmatory campaign: heterogeneous, atomic coalitions.

Four questions, one each:

E1  can HiGHS be trusted as the N2 ground truth, and does N2 reduce to the
    frozen N1 LSAP when every capacity is equal?
E2  what does atomicity cost, measured as the gap between the LP relaxation
    and the integral optimum of the very same model?
E3  how do capacity pressure and heterogeneity jointly shape feasibility?
E4  how far does the oracle keep certifying optimality within a budget?

The script only writes under ``n2_v1``; the frozen N1 package is read-only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

import sp1_a1_hungarian as homogeneous
import sp1_n2_oracle as oracle
from sp1_levels_common import LEVELS_OUTPUT_ROOT, REPOSITORY_ROOT


DEFAULT_CONFIG = (
    REPOSITORY_ROOT
    / "experiments"
    / "configs"
    / "sp1_n2_confirmatory_v1.yaml"
)
DEFAULT_OUTPUT = LEVELS_OUTPUT_ROOT / "n2_v1"

SCENARIO_LABELS = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}


def load_config(path: Path, *, smoke: bool) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("The N2 configuration must be a mapping.")
    if smoke:
        payload = copy.deepcopy(payload)
        payload["campaign_id"] += "_SMOKE"
        payload["oracle_validation"]["sizes"] = [[8, 2]]
        payload["oracle_validation"]["capacity_cv"] = [0.65]
        payload["oracle_validation"]["pressure"] = [0.70]
        payload["oracle_validation"]["seeds_per_cell"] = 3
        payload["homogeneous_limit"]["slots"] = [12]
        payload["homogeneous_limit"]["scenarios"] = ["uniform"]
        payload["homogeneous_limit"]["seeds_per_cell"] = 3
        payload["atomicity"]["capacity_cv"] = [0.00, 0.65]
        payload["atomicity"]["pressure"] = [0.80]
        payload["atomicity"]["scenarios"] = ["uniform"]
        payload["atomicity"]["seeds_per_cell"] = 3
        payload["phase_diagram"]["capacity_cv"] = [0.00, 0.65]
        payload["phase_diagram"]["pressure"] = [0.75, 1.02]
        payload["phase_diagram"]["scenarios"] = ["uniform"]
        payload["phase_diagram"]["seeds_per_cell"] = 3
        payload["certification"]["sizes"] = [[20, 6]]
        payload["certification"]["time_limits_s"] = [1.0]
        payload["certification"]["seeds_per_cell"] = 3
    return payload


def world_id(*parts: object) -> str:
    text = "|".join(str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def progress(label: str, index: int, total: int) -> None:
    if index == 1 or index == total or index % max(1, total // 12) == 0:
        print(f"[{label}] {index:,}/{total:,}", flush=True)


def capacity_vector(
    robot_count: int, q_bar: float, cv: float, rng: np.random.Generator
) -> np.ndarray:
    """Lognormal capacities renormalized to a fixed total supply.

    Pinning ``sum c_i`` makes CV the only thing that changes across levels, so
    a feasibility difference can never be explained by more capacity.
    """

    supply = robot_count * q_bar
    if cv <= 0.0:
        return np.full(robot_count, q_bar, dtype=float)
    sigma = math.sqrt(math.log1p(cv * cv))
    raw = rng.lognormal(mean=0.0, sigma=sigma, size=robot_count)
    return raw * (supply / float(raw.sum()))


def make_world(
    *,
    robot_count: int,
    load_count: int,
    q_bar: float,
    cv: float,
    pressure: float,
    scenario: str,
    workspace: tuple[float, float],
    seed: int,
    alpha: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Geometry and demand from the world seed; capacities from their own.

    Capacities use a separate stream keyed by CV so that the geometry and the
    masses stay byte-identical across heterogeneity levels: the design is
    paired within a world.
    """

    width, height = workspace
    spatial_rng = np.random.default_rng(seed)
    robot_positions = homogeneous.generate_positions(
        robot_count,
        role="robot",
        spatial_mode=scenario,
        workspace_width=width,
        workspace_height=height,
        rng=spatial_rng,
    )
    load_positions = homogeneous.generate_positions(
        load_count,
        role="load",
        spatial_mode=scenario,
        workspace_width=width,
        workspace_height=height,
        rng=spatial_rng,
    )
    supply = robot_count * q_bar
    masses = pressure * supply * spatial_rng.dirichlet(
        np.full(load_count, alpha)
    )
    capacity_rng = np.random.default_rng(
        homogeneous.stable_seed(seed, "n2-capacity", cv)
    )
    capacities = capacity_vector(robot_count, q_bar, cv, capacity_rng)
    distance = np.linalg.norm(
        robot_positions[:, None, :] - load_positions[None, :, :], axis=2
    )
    return capacities, masses, distance


def _base_row(**kwargs: Any) -> dict[str, Any]:
    return kwargs


# --------------------------------------------------------------------------
# E1.A - the oracle against exhaustive enumeration
# --------------------------------------------------------------------------
def run_oracle_validation(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["oracle_validation"]
    q_bar = float(config["q_bar_kg"])
    workspace = tuple(config["workspace_m"])
    alpha = float(config["generator"]["demand_split_alpha"])
    base_seed = int(config["base_seed"])
    rows: list[dict[str, Any]] = []
    cells = [
        (tuple(size), cv, pressure)
        for size in section["sizes"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
    ]
    for index, ((robot_count, load_count), cv, pressure) in enumerate(cells, 1):
        progress("E1.A", index, len(cells))
        for replicate in range(int(section["seeds_per_cell"])):
            seed = homogeneous.stable_seed(
                base_seed,
                "n2-oracle-validation",
                robot_count,
                load_count,
                cv,
                pressure,
                replicate,
            )
            capacities, masses, distance = make_world(
                robot_count=robot_count,
                load_count=load_count,
                q_bar=q_bar,
                cv=cv,
                pressure=pressure,
                scenario=str(section["scenario"]),
                workspace=workspace,
                seed=seed,
                alpha=alpha,
            )
            model = oracle.build_model(
                capacities=capacities, masses=masses, distance=distance
            )
            solved = oracle.solve(
                model,
                integral=True,
                time_limit_s=float(section["milp_time_limit_s"]),
            )
            brute_status, brute_value, _ = oracle.enumerate_optimum(
                model, max_states=int(section["enumeration_max_states"])
            )
            comparable = (
                solved.status == oracle.OPTIMAL
                and brute_status == oracle.OPTIMAL
            )
            rows.append(
                _base_row(
                    experiment="oracle_validation",
                    world_id=world_id("e1a", robot_count, load_count, cv, pressure, replicate),
                    world_seed=seed,
                    replicate=replicate,
                    N=robot_count,
                    K=load_count,
                    capacity_cv=cv,
                    pressure=pressure,
                    realized_cv=float(np.std(capacities) / np.mean(capacities)),
                    enumeration_states=(load_count + 1) ** robot_count,
                    milp_status=solved.status,
                    brute_status=brute_status,
                    status_agrees=solved.status == brute_status,
                    milp_objective=solved.objective,
                    brute_objective=(
                        brute_value if math.isfinite(brute_value) else math.nan
                    ),
                    absolute_error=(
                        abs(solved.objective - brute_value) if comparable else math.nan
                    ),
                    milp_runtime_s=solved.runtime_s,
                )
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# E1.B - the homogeneous limit reproduces the frozen N1 LSAP
# --------------------------------------------------------------------------
def run_homogeneous_limit(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["homogeneous_limit"]
    q_bar = float(config["q_bar_kg"])
    width, height = config["workspace_m"]
    base_seed = int(config["base_seed"])
    rows: list[dict[str, Any]] = []
    cells = [
        (int(slots), scenario)
        for slots in section["slots"]
        for scenario in section["scenarios"]
    ]
    for index, (total_slots, scenario) in enumerate(cells, 1):
        progress("E1.B", index, len(cells))
        robot_count = homogeneous.robot_count_from_delta(
            total_slots, float(section["reserve_delta"])
        )
        for replicate in range(int(section["seeds_per_cell"])):
            seed = homogeneous.stable_seed(
                base_seed, "n2-homogeneous-limit", total_slots, scenario, replicate
            )
            robots, loads, _ = homogeneous.generate_world(
                robot_count=robot_count,
                total_slots=total_slots,
                q_bar=q_bar,
                mean_quota=3.0,
                quota_mode=str(section["quota_mode"]),
                spatial_mode=scenario,
                workspace_width=float(width),
                workspace_height=float(height),
                seed=seed,
            )
            # N1 reference: the frozen slot LSAP, read but never rerun.
            lsap = homogeneous.solve_hungarian(
                robots, loads, q_bar, allow_partial=False
            )
            capacities = np.full(len(robots), q_bar, dtype=float)
            masses = np.asarray([load.mass for load in loads], dtype=float)
            distance = np.asarray(
                [
                    [math.hypot(robot.x - load.x, robot.y - load.y) for load in loads]
                    for robot in robots
                ],
                dtype=float,
            )
            model = oracle.build_model(
                capacities=capacities, masses=masses, distance=distance
            )
            solved = oracle.solve(
                model,
                integral=True,
                time_limit_s=float(section["milp_time_limit_s"]),
            )
            recruited = (
                solved.assignment.sum(axis=0)
                if solved.assignment is not None
                else np.zeros(len(loads))
            )
            required = np.asarray(
                [math.ceil(load.mass / q_bar) for load in loads], dtype=float
            )
            rows.append(
                _base_row(
                    experiment="homogeneous_limit",
                    world_id=world_id("e1b", total_slots, scenario, replicate),
                    world_seed=seed,
                    replicate=replicate,
                    scenario=scenario,
                    scenario_label=SCENARIO_LABELS[scenario],
                    N=robot_count,
                    K=len(loads),
                    M=total_slots,
                    lsap_feasible=bool(lsap.feasible),
                    lsap_cost=float(lsap.total_cost),
                    milp_status=solved.status,
                    milp_objective=solved.objective,
                    feasibility_agrees=(
                        (solved.status == oracle.OPTIMAL) == bool(lsap.feasible)
                    ),
                    distance_absolute_error=(
                        abs(solved.objective - lsap.total_cost)
                        if solved.status == oracle.OPTIMAL
                        else math.nan
                    ),
                    cardinality_matches=bool(
                        np.allclose(recruited, required, atol=1e-6)
                    ),
                    milp_runtime_s=solved.runtime_s,
                )
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# E2 - the price of atomicity
# --------------------------------------------------------------------------
def run_atomicity(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["atomicity"]
    q_bar = float(config["q_bar_kg"])
    workspace = tuple(config["workspace_m"])
    alpha = float(config["generator"]["demand_split_alpha"])
    base_seed = int(config["base_seed"])
    robot_count = int(section["robot_count"])
    load_count = int(section["load_count"])
    rows: list[dict[str, Any]] = []
    cells = [
        (scenario, pressure)
        for scenario in section["scenarios"]
        for pressure in section["pressure"]
    ]
    for index, (scenario, pressure) in enumerate(cells, 1):
        progress("E2", index, len(cells))
        for replicate in range(int(section["seeds_per_cell"])):
            seed = homogeneous.stable_seed(
                base_seed, "n2-atomicity", scenario, pressure, replicate
            )
            for cv in section["capacity_cv"]:
                capacities, masses, distance = make_world(
                    robot_count=robot_count,
                    load_count=load_count,
                    q_bar=q_bar,
                    cv=cv,
                    pressure=pressure,
                    scenario=scenario,
                    workspace=workspace,
                    seed=seed,
                    alpha=alpha,
                )
                model = oracle.build_model(
                    capacities=capacities, masses=masses, distance=distance
                )
                # Same model object for both: only integrality differs.
                relaxed = oracle.solve(model, integral=False)
                integral = oracle.solve(
                    model,
                    integral=True,
                    time_limit_s=float(section["milp_time_limit_s"]),
                )
                comparable = (
                    relaxed.status == oracle.OPTIMAL
                    and integral.status == oracle.OPTIMAL
                )
                absolute, relative = (
                    oracle.integrality_gap(integral.objective, relaxed.objective)
                    if comparable
                    else (math.nan, math.nan)
                )
                active = (
                    int(np.count_nonzero(relaxed.assignment > oracle.FRACTIONAL_EPS))
                    if relaxed.assignment is not None
                    else 0
                )
                rows.append(
                    _base_row(
                        experiment="atomicity",
                        world_id=world_id("e2", scenario, pressure, replicate),
                        world_seed=seed,
                        replicate=replicate,
                        scenario=scenario,
                        scenario_label=SCENARIO_LABELS[scenario],
                        pressure=pressure,
                        capacity_cv=cv,
                        realized_cv=float(np.std(capacities) / np.mean(capacities)),
                        N=robot_count,
                        K=load_count,
                        lp_status=relaxed.status,
                        milp_status=integral.status,
                        lp_objective=relaxed.objective,
                        milp_objective=integral.objective,
                        gap_absolute=absolute,
                        gap_relative=relative,
                        fractional_variables=relaxed.fractional_count,
                        fractional_world=bool(relaxed.fractional_count > 0),
                        fractionality_rate=(
                            relaxed.fractional_count / active if active else 0.0
                        ),
                        max_fractionality=relaxed.max_fractionality,
                        lp_runtime_s=relaxed.runtime_s,
                        milp_runtime_s=integral.runtime_s,
                    )
                )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# E3 - heterogeneity against capacity pressure
# --------------------------------------------------------------------------
def run_phase_diagram(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["phase_diagram"]
    q_bar = float(config["q_bar_kg"])
    workspace = tuple(config["workspace_m"])
    alpha = float(config["generator"]["demand_split_alpha"])
    base_seed = int(config["base_seed"])
    robot_count = int(section["robot_count"])
    load_count = int(section["load_count"])
    rows: list[dict[str, Any]] = []
    cells = [
        (scenario, pressure)
        for scenario in section["scenarios"]
        for pressure in section["pressure"]
    ]
    for index, (scenario, pressure) in enumerate(cells, 1):
        progress("E3", index, len(cells))
        for replicate in range(int(section["seeds_per_cell"])):
            seed = homogeneous.stable_seed(
                base_seed, "n2-phase", scenario, pressure, replicate
            )
            for cv in section["capacity_cv"]:
                capacities, masses, distance = make_world(
                    robot_count=robot_count,
                    load_count=load_count,
                    q_bar=q_bar,
                    cv=cv,
                    pressure=pressure,
                    scenario=scenario,
                    workspace=workspace,
                    seed=seed,
                    alpha=alpha,
                )
                model = oracle.build_model(
                    capacities=capacities, masses=masses, distance=distance
                )
                solved = oracle.solve(
                    model,
                    integral=True,
                    time_limit_s=float(section["milp_time_limit_s"]),
                )
                if solved.assignment is not None:
                    recruited = oracle.recruited_capacity(model, solved.assignment)
                    excess = float(np.sum(recruited - masses))
                    coalition = float(np.sum(solved.assignment))
                else:
                    excess = math.nan
                    coalition = math.nan
                rows.append(
                    _base_row(
                        experiment="phase_diagram",
                        world_id=world_id("e3", scenario, pressure, replicate),
                        world_seed=seed,
                        replicate=replicate,
                        scenario=scenario,
                        scenario_label=SCENARIO_LABELS[scenario],
                        pressure=pressure,
                        capacity_cv=cv,
                        realized_cv=float(np.std(capacities) / np.mean(capacities)),
                        N=robot_count,
                        K=load_count,
                        supply=float(np.sum(capacities)),
                        demand=float(np.sum(masses)),
                        realized_pressure=float(np.sum(masses) / np.sum(capacities)),
                        milp_status=solved.status,
                        certified_feasible=solved.status == oracle.OPTIMAL,
                        proven_infeasible=solved.status == oracle.INFEASIBLE,
                        censored=solved.status
                        in (oracle.FEASIBLE_TIME_LIMIT, oracle.UNKNOWN),
                        milp_objective=solved.objective,
                        excess_capacity=excess,
                        coalition_size=coalition,
                        milp_runtime_s=solved.runtime_s,
                    )
                )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# E4 - how far the oracle keeps certifying
# --------------------------------------------------------------------------
def run_certification(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["certification"]
    q_bar = float(config["q_bar_kg"])
    workspace = tuple(config["workspace_m"])
    alpha = float(config["generator"]["demand_split_alpha"])
    base_seed = int(config["base_seed"])
    cv = float(section["capacity_cv"])
    pressure = float(section["pressure"])
    rows: list[dict[str, Any]] = []
    cells = [
        (tuple(size), limit)
        for size in section["sizes"]
        for limit in section["time_limits_s"]
    ]
    for index, ((robot_count, load_count), limit) in enumerate(cells, 1):
        progress("E4", index, len(cells))
        for replicate in range(int(section["seeds_per_cell"])):
            seed = homogeneous.stable_seed(
                base_seed, "n2-certification", robot_count, load_count, replicate
            )
            capacities, masses, distance = make_world(
                robot_count=robot_count,
                load_count=load_count,
                q_bar=q_bar,
                cv=cv,
                pressure=pressure,
                scenario=str(section["scenario"]),
                workspace=workspace,
                seed=seed,
                alpha=alpha,
            )
            model = oracle.build_model(
                capacities=capacities, masses=masses, distance=distance
            )
            solved = oracle.solve(
                model, integral=True, time_limit_s=float(limit)
            )
            rows.append(
                _base_row(
                    experiment="certification",
                    world_id=world_id("e4", robot_count, load_count, replicate),
                    world_seed=seed,
                    replicate=replicate,
                    N=robot_count,
                    K=load_count,
                    binary_variables=robot_count * load_count,
                    constraints=robot_count + load_count,
                    time_limit_s=float(limit),
                    milp_status=solved.status,
                    optimal_certified=solved.status == oracle.OPTIMAL,
                    incumbent_exists=solved.has_incumbent,
                    proven_infeasible=solved.status == oracle.INFEASIBLE,
                    milp_objective=solved.objective,
                    best_bound=solved.bound,
                    mip_gap=solved.mip_gap,
                    node_count=solved.node_count,
                    runtime_s=solved.runtime_s,
                    timeout=solved.runtime_s >= 0.95 * float(limit),
                )
            )
    return pd.DataFrame(rows)


RUNNERS = {
    "oracle_validation": run_oracle_validation,
    "homogeneous_limit": run_homogeneous_limit,
    "atomicity": run_atomicity,
    "phase_diagram": run_phase_diagram,
    "certification": run_certification,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SP1.N2 confirmatory campaign."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(RUNNERS),
        help="Run a subset of the layers; repeatable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config.resolve(), smoke=bool(args.smoke))
    raw_dir = args.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    selected = args.only or list(RUNNERS)
    for name in selected:
        frame = RUNNERS[name](config)
        target = raw_dir / f"{name}_runs.csv"
        frame.to_csv(target, index=False)
        print(f"{name}: {len(frame):,} filas -> {target}", flush=True)


if __name__ == "__main__":
    main()
