"""Homogeneous multi-AMR recruitment through distributed population games.

This module is deliberately independent from the historical SP0/SP1 result
packages.  It implements the new, versioned experiment in which the legacy
one-to-one problem is the q=1 boundary case and homogeneous cooperative
recruitment is represented by a common quorum q>=1.

The implementation keeps the continuous population state, the argmax decode,
and the integer quorum closure as separate artifacts.  This separation is a
hard methodological requirement: a successful closure must never be reported
as evidence that the underlying population dynamic converged to a valid
integer assignment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linear_sum_assignment
from scipy.stats import wilcoxon


POPULATION_METHODS = {"smith_qr": "SMITH", "replicator_qr": "REPLICATOR", "bnn_qr": "BNN"}
CONTROL_METHODS = {"uniform_qr", "random_qr"}
EXTERNAL_METHODS = {"greedy", "auction_proxy", "hungarian_exact"}
ALL_METHODS = set(POPULATION_METHODS) | CONTROL_METHODS | EXTERNAL_METHODS


@dataclass(frozen=True, slots=True)
class HomogeneousWorld:
    seed: int
    n_robots: int
    n_loads: int
    quorum: int
    geometry: str
    graph: str
    robot_positions: np.ndarray
    load_positions: np.ndarray
    cost_m: np.ndarray
    cost_normalized: np.ndarray
    adjacency: np.ndarray
    mixing: np.ndarray
    lambda2: float
    world_hash: str


@dataclass(slots=True)
class PopulationResult:
    method: str
    x: np.ndarray
    initial_x: np.ndarray
    iterations: int
    converged: bool
    residual: float
    potential_initial: float
    potential_final: float
    potential_violations: int
    simplex_error: float
    projection_corrections: int
    switches: int
    messages: int
    runtime_s: float
    potential_history: list[float]
    residual_history: list[float]


@dataclass(frozen=True, slots=True)
class AssignmentMetrics:
    valid: bool
    coverage: float
    distance_m: float
    normalized_regret: float
    unmet_quorum: int
    overallocated: int
    served_loads: int


def project_simplex(values: np.ndarray) -> np.ndarray:
    """Euclidean projection of one vector onto the probability simplex."""

    vector = np.asarray(values, dtype=float)
    order = np.sort(vector)[::-1]
    cumulative = np.cumsum(order)
    active = order * np.arange(1, vector.size + 1) > cumulative - 1.0
    if not np.any(active):
        return np.full_like(vector, 1.0 / max(vector.size, 1))
    rho = int(np.flatnonzero(active)[-1])
    theta = (cumulative[rho] - 1.0) / float(rho + 1)
    return np.maximum(vector - theta, 0.0)


def project_rows(values: np.ndarray) -> np.ndarray:
    return np.vstack([project_simplex(row) for row in np.asarray(values, dtype=float)])


def make_homogeneous_world(
    *, seed: int, n_robots: int, quorum: int, geometry: str, graph: str
) -> HomogeneousWorld:
    if n_robots <= 0 or quorum <= 0 or n_robots % quorum != 0:
        raise ValueError("The balanced SP1 design requires n_robots>0 and n_robots % quorum == 0")
    n_loads = n_robots // quorum
    rng = np.random.default_rng(seed)
    geometry_id = geometry.lower()
    if geometry_id == "uniform":
        robots = rng.uniform(0.5, 9.5, size=(n_robots, 2))
        loads = rng.uniform(0.5, 9.5, size=(n_loads, 2))
    elif geometry_id == "clustered":
        robot_centers = np.asarray([[2.0, 2.0], [8.0, 8.0]])
        load_centers = np.asarray([[2.0, 8.0], [8.0, 2.0]])
        robots = robot_centers[np.arange(n_robots) % 2] + rng.normal(0.0, 0.65, size=(n_robots, 2))
        loads = load_centers[np.arange(n_loads) % 2] + rng.normal(0.0, 0.65, size=(n_loads, 2))
        robots = np.clip(robots, 0.25, 9.75)
        loads = np.clip(loads, 0.25, 9.75)
    elif geometry_id == "crossed":
        robot_y = np.linspace(0.75, 9.25, n_robots)
        load_y = np.linspace(9.25, 0.75, n_loads)
        robots = np.column_stack([np.full(n_robots, 1.0), robot_y])
        loads = np.column_stack([np.full(n_loads, 9.0), load_y])
        robots += rng.normal(0.0, 0.04, size=robots.shape)
        loads += rng.normal(0.0, 0.04, size=loads.shape)
    else:
        raise ValueError(f"Unknown geometry: {geometry}")

    cost_m = np.linalg.norm(robots[:, None, :] - loads[None, :, :], axis=2)
    cost_normalized = cost_m / math.sqrt(200.0)
    adjacency = _adjacency(n_robots, graph)
    mixing = _metropolis_mixing(adjacency)
    laplacian = np.diag(np.sum(adjacency, axis=1)) - adjacency
    eigvals = np.linalg.eigvalsh(laplacian)
    lambda2 = float(eigvals[1]) if n_robots > 1 else 0.0
    payload = {
        "seed": seed,
        "n_robots": n_robots,
        "n_loads": n_loads,
        "quorum": quorum,
        "geometry": geometry_id,
        "graph": graph.lower(),
        "robots": np.round(robots, 10).tolist(),
        "loads": np.round(loads, 10).tolist(),
        "adjacency": adjacency.astype(int).tolist(),
    }
    world_hash = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    return HomogeneousWorld(
        seed=seed,
        n_robots=n_robots,
        n_loads=n_loads,
        quorum=quorum,
        geometry=geometry_id,
        graph=graph.lower(),
        robot_positions=robots,
        load_positions=loads,
        cost_m=cost_m,
        cost_normalized=cost_normalized,
        adjacency=adjacency,
        mixing=mixing,
        lambda2=lambda2,
        world_hash=world_hash,
    )


def _adjacency(n_robots: int, graph: str) -> np.ndarray:
    graph_id = graph.lower()
    if graph_id == "complete":
        return np.ones((n_robots, n_robots), dtype=float) - np.eye(n_robots)
    if graph_id == "ring":
        matrix = np.zeros((n_robots, n_robots), dtype=float)
        for index in range(n_robots):
            matrix[index, (index - 1) % n_robots] = 1.0
            matrix[index, (index + 1) % n_robots] = 1.0
        return matrix
    raise ValueError(f"Unknown graph: {graph}")


def _metropolis_mixing(adjacency: np.ndarray) -> np.ndarray:
    degrees = np.sum(adjacency, axis=1)
    matrix = np.zeros_like(adjacency, dtype=float)
    for i in range(adjacency.shape[0]):
        for j in range(adjacency.shape[1]):
            if adjacency[i, j] > 0:
                matrix[i, j] = 1.0 / (1.0 + max(degrees[i], degrees[j]))
        matrix[i, i] = 1.0 - np.sum(matrix[i])
    return matrix


def potential(world: HomogeneousWorld, x: np.ndarray, *, alpha: float, beta: float) -> float:
    occupancy = np.sum(x, axis=0)
    imbalance = -0.5 * alpha * float(np.sum((occupancy - world.quorum) ** 2))
    spatial = -beta * float(np.sum(world.cost_normalized * x))
    return imbalance + spatial


def fitness(
    world: HomogeneousWorld,
    x: np.ndarray,
    *,
    alpha: float,
    beta: float,
    consensus_rounds: int,
) -> tuple[np.ndarray, int]:
    estimate = np.asarray(x, dtype=float)
    rounds = 1 if world.graph == "complete" else max(int(consensus_rounds), 1)
    for _ in range(rounds):
        estimate = world.mixing @ estimate
    occupancy_estimate = world.n_robots * estimate
    edge_count = int(np.sum(world.adjacency) / 2)
    messages = rounds * 2 * edge_count * world.n_loads
    values = -alpha * (occupancy_estimate - world.quorum) - beta * world.cost_normalized
    return values, messages


def vector_field(x: np.ndarray, values: np.ndarray, protocol: str) -> np.ndarray:
    protocol_id = protocol.upper()
    if protocol_id == "SMITH":
        difference = values[:, :, None] - values[:, None, :]
        positive = np.maximum(difference, 0.0)
        inflow = np.sum(x[:, None, :] * positive, axis=2)
        outflow = x * np.sum(np.maximum(-difference, 0.0), axis=2)
        return inflow - outflow
    mean = np.sum(x * values, axis=1, keepdims=True)
    if protocol_id == "REPLICATOR":
        return x * (values - mean)
    if protocol_id == "BNN":
        excess = np.maximum(values - mean, 0.0)
        return excess - x * np.sum(excess, axis=1, keepdims=True)
    raise ValueError(f"Unknown population protocol: {protocol}")


def run_population(
    world: HomogeneousWorld,
    *,
    protocol: str,
    seed: int,
    alpha: float,
    beta: float,
    dt: float,
    max_steps: int,
    tolerance: float,
    stable_steps: int,
    consensus_rounds: int,
) -> PopulationResult:
    rng = np.random.default_rng(seed)
    initial = np.full((world.n_robots, world.n_loads), 1.0 / world.n_loads)
    initial = project_rows(initial + rng.normal(0.0, 0.01, size=initial.shape))
    x = initial.copy()
    potential_history = [potential(world, x, alpha=alpha, beta=beta)]
    residual_history: list[float] = []
    violations = 0
    projection_corrections = 0
    switches = 0
    messages = 0
    stable = 0
    converged = False
    start = perf_counter()
    previous_labels = np.argmax(x, axis=1)
    residual = math.inf
    for step in range(1, max_steps + 1):
        values, step_messages = fitness(
            world, x, alpha=alpha, beta=beta, consensus_rounds=consensus_rounds
        )
        messages += step_messages
        field = vector_field(x, values, protocol)
        residual = float(np.max(np.abs(field)))
        residual_history.append(residual)
        # Positive per-player time rescaling bounds the revision rate without
        # changing stationary points or the continuous potential-ascent sign.
        rate_scale = np.maximum(1.0, np.max(np.abs(field), axis=1, keepdims=True))
        proposal = x + dt * field / rate_scale
        corrected = project_rows(proposal)
        if float(np.max(np.abs(corrected - proposal))) > 1.0e-10:
            projection_corrections += 1
        x = corrected
        labels = np.argmax(x, axis=1)
        switches += int(np.sum(labels != previous_labels))
        previous_labels = labels
        current_potential = potential(world, x, alpha=alpha, beta=beta)
        if current_potential < potential_history[-1] - 1.0e-9:
            violations += 1
        potential_history.append(current_potential)
        if residual <= tolerance:
            stable += 1
            if stable >= stable_steps:
                converged = True
                break
        else:
            stable = 0
    runtime = perf_counter() - start
    simplex_error = float(np.max(np.abs(np.sum(x, axis=1) - 1.0)))
    return PopulationResult(
        method=protocol.upper(),
        x=x,
        initial_x=initial,
        iterations=step,
        converged=converged,
        residual=residual,
        potential_initial=potential_history[0],
        potential_final=potential_history[-1],
        potential_violations=violations,
        simplex_error=simplex_error,
        projection_corrections=projection_corrections,
        switches=switches,
        messages=messages,
        runtime_s=runtime,
        potential_history=potential_history,
        residual_history=residual_history,
    )


def hungarian_exact(world: HomogeneousWorld) -> np.ndarray:
    slots = np.repeat(np.arange(world.n_loads), world.quorum)
    rows, columns = linear_sum_assignment(world.cost_m[:, slots])
    labels = np.full(world.n_robots, -1, dtype=int)
    labels[rows] = slots[columns]
    return labels


def greedy_assignment(world: HomogeneousWorld) -> np.ndarray:
    labels = np.full(world.n_robots, -1, dtype=int)
    remaining = np.full(world.n_loads, world.quorum, dtype=int)
    for robot in range(world.n_robots):
        available = np.flatnonzero(remaining > 0)
        chosen = int(available[np.argmin(world.cost_m[robot, available])])
        labels[robot] = chosen
        remaining[chosen] -= 1
    return labels


def auction_proxy_assignment(world: HomogeneousWorld) -> np.ndarray:
    """Deterministic regret-priority auction baseline for homogeneous slots."""

    labels = np.full(world.n_robots, -1, dtype=int)
    remaining = np.full(world.n_loads, world.quorum, dtype=int)
    unassigned = set(range(world.n_robots))
    while unassigned:
        available = np.flatnonzero(remaining > 0)
        bids: list[tuple[float, float, int, int]] = []
        for robot in sorted(unassigned):
            order = available[np.argsort(world.cost_m[robot, available], kind="stable")]
            best = int(order[0])
            second_cost = (
                float(world.cost_m[robot, order[1]]) if order.size > 1 else float(world.cost_m[robot, best]) + 1.0
            )
            regret = second_cost - float(world.cost_m[robot, best])
            bids.append((regret, -float(world.cost_m[robot, best]), -robot, best))
        _, _, neg_robot, load = max(bids)
        robot = -neg_robot
        labels[robot] = load
        remaining[load] -= 1
        unassigned.remove(robot)
    return labels


def quorum_closure(world: HomogeneousWorld, preferences: np.ndarray) -> np.ndarray:
    """Finite preference-priority closure with an explicit q-slot contract."""

    labels = np.full(world.n_robots, -1, dtype=int)
    remaining = np.full(world.n_loads, world.quorum, dtype=int)
    score = np.asarray(preferences, dtype=float) - 0.05 * world.cost_normalized
    pairs = [
        (float(score[robot, load]), -float(world.cost_m[robot, load]), -robot, -load)
        for robot in range(world.n_robots)
        for load in range(world.n_loads)
    ]
    for _, _, neg_robot, neg_load in sorted(pairs, reverse=True):
        robot, load = -neg_robot, -neg_load
        if labels[robot] >= 0 or remaining[load] <= 0:
            continue
        labels[robot] = load
        remaining[load] -= 1
        if np.all(labels >= 0):
            break
    if np.any(labels < 0) or np.any(remaining != 0):
        raise RuntimeError("Quorum closure failed in a balanced homogeneous world")
    return labels


def evaluate_assignment(
    world: HomogeneousWorld, labels: np.ndarray, *, optimal_distance: float
) -> AssignmentMetrics:
    labels = np.asarray(labels, dtype=int)
    counts = np.bincount(labels[labels >= 0], minlength=world.n_loads)
    valid = bool(labels.size == world.n_robots and np.all(labels >= 0) and np.all(counts == world.quorum))
    served = int(np.sum(counts >= world.quorum))
    coverage = float(np.sum(np.minimum(counts, world.quorum)) / (world.n_loads * world.quorum))
    unmet = int(np.sum(np.maximum(world.quorum - counts, 0)))
    over = int(np.sum(np.maximum(counts - world.quorum, 0)))
    distance = float(
        sum(world.cost_m[robot, load] for robot, load in enumerate(labels) if 0 <= load < world.n_loads)
    )
    if valid:
        regret = (distance - optimal_distance) / max(optimal_distance, 1.0e-12)
    else:
        regret = 1.0 + unmet / max(world.n_robots, 1) + over / max(world.n_robots, 1)
    return AssignmentMetrics(
        valid=valid,
        coverage=coverage,
        distance_m=distance,
        normalized_regret=float(max(regret, 0.0)),
        unmet_quorum=unmet,
        overallocated=over,
        served_loads=served,
    )


def run_homogeneous_campaign(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    methods = [str(item) for item in config["methods"]]
    unknown = set(methods) - ALL_METHODS
    if unknown:
        raise ValueError(f"Unknown methods: {sorted(unknown)}")

    factors = config["factors"]
    alpha = float(config["population"]["alpha"])
    beta = float(config["population"]["beta"])
    dt = float(config["population"]["dt"])
    max_steps = int(config["population"]["max_steps"])
    tolerance = float(config["population"]["tolerance"])
    stable_steps = int(config["population"]["stable_steps"])
    consensus_rounds = int(config["population"]["consensus_rounds"])
    replicates = int(config["replicates_per_cell"])
    base_seed = int(config["base_seed"])

    rows: list[dict[str, Any]] = []
    raw_assignments: list[dict[str, Any]] = []
    closed_assignments: list[dict[str, Any]] = []
    representative_histories: list[dict[str, Any]] = []
    world_index = 0
    for n_robots in factors["n_robots"]:
        for quorum in factors["quorum"]:
            if int(n_robots) % int(quorum):
                continue
            for geometry in factors["geometry"]:
                for graph in factors["graph"]:
                    for replicate in range(replicates):
                        seed = base_seed + world_index
                        world_index += 1
                        world = make_homogeneous_world(
                            seed=seed,
                            n_robots=int(n_robots),
                            quorum=int(quorum),
                            geometry=str(geometry),
                            graph=str(graph),
                        )
                        exact = hungarian_exact(world)
                        optimal_distance = evaluate_assignment(
                            world, exact, optimal_distance=1.0
                        ).distance_m
                        common = {
                            "experiment_id": experiment_id,
                            "world_seed": seed,
                            "world_hash": world.world_hash,
                            "replicate": replicate,
                            "n_robots": world.n_robots,
                            "n_loads": world.n_loads,
                            "quorum": world.quorum,
                            "geometry": world.geometry,
                            "graph": world.graph,
                            "lambda2": world.lambda2,
                        }
                        for method_index, method in enumerate(methods):
                            native_start = perf_counter()
                            pop: PopulationResult | None = None
                            raw_labels: np.ndarray
                            if method == "hungarian_exact":
                                raw_labels = exact.copy()
                                closed_labels = exact.copy()
                            elif method == "greedy":
                                raw_labels = greedy_assignment(world)
                                closed_labels = raw_labels.copy()
                            elif method == "auction_proxy":
                                raw_labels = auction_proxy_assignment(world)
                                closed_labels = raw_labels.copy()
                            elif method in POPULATION_METHODS:
                                pop = run_population(
                                    world,
                                    protocol=POPULATION_METHODS[method],
                                    seed=seed + 100_000 * (method_index + 1),
                                    alpha=alpha,
                                    beta=beta,
                                    dt=dt,
                                    max_steps=max_steps,
                                    tolerance=tolerance,
                                    stable_steps=stable_steps,
                                    consensus_rounds=consensus_rounds,
                                )
                                raw_labels = np.argmax(pop.x, axis=1)
                                closed_labels = quorum_closure(world, pop.x)
                                if replicate == 0:
                                    for step, value in enumerate(pop.potential_history):
                                        representative_histories.append(
                                            {**common, "method": method, "step": step, "potential": value}
                                        )
                            elif method == "uniform_qr":
                                preferences = np.full(
                                    (world.n_robots, world.n_loads), 1.0 / world.n_loads
                                )
                                raw_labels = np.argmax(preferences, axis=1)
                                closed_labels = quorum_closure(world, preferences)
                            elif method == "random_qr":
                                rng = np.random.default_rng(seed + 100_000 * (method_index + 1))
                                preferences = project_rows(
                                    rng.uniform(0.0, 1.0, size=(world.n_robots, world.n_loads))
                                )
                                raw_labels = np.argmax(preferences, axis=1)
                                closed_labels = quorum_closure(world, preferences)
                            else:  # pragma: no cover - guarded above
                                raise AssertionError(method)

                            raw_metrics = evaluate_assignment(
                                world, raw_labels, optimal_distance=optimal_distance
                            )
                            final_metrics = evaluate_assignment(
                                world, closed_labels, optimal_distance=optimal_distance
                            )
                            row = {
                                **common,
                                "method": method,
                                "method_family": _method_family(method),
                                "stage": "closed" if method not in EXTERNAL_METHODS else "native",
                                "raw_valid": raw_metrics.valid,
                                "raw_coverage": raw_metrics.coverage,
                                "raw_normalized_regret": raw_metrics.normalized_regret,
                                "final_valid": final_metrics.valid,
                                "final_coverage": final_metrics.coverage,
                                "distance_m": final_metrics.distance_m,
                                "normalized_regret": final_metrics.normalized_regret,
                                "unmet_quorum": final_metrics.unmet_quorum,
                                "overallocated": final_metrics.overallocated,
                                "served_loads": final_metrics.served_loads,
                                "optimal_distance_m": optimal_distance,
                                "closure_delta_regret": final_metrics.normalized_regret
                                - raw_metrics.normalized_regret,
                                "iterations": pop.iterations if pop else 0,
                                "continuous_converged": pop.converged if pop else True,
                                "equilibrium_residual": pop.residual if pop else 0.0,
                                "potential_initial": pop.potential_initial if pop else math.nan,
                                "potential_final": pop.potential_final if pop else math.nan,
                                "potential_gain": (
                                    pop.potential_final - pop.potential_initial if pop else math.nan
                                ),
                                "potential_violations": pop.potential_violations if pop else 0,
                                "simplex_error": pop.simplex_error if pop else 0.0,
                                "projection_corrections": pop.projection_corrections if pop else 0,
                                "switches": pop.switches if pop else 0,
                                "messages": pop.messages if pop else _external_messages(world, method),
                                "runtime_s": pop.runtime_s if pop else perf_counter() - native_start,
                            }
                            rows.append(row)
                            for robot, label in enumerate(raw_labels):
                                raw_assignments.append(
                                    {**common, "method": method, "robot": robot, "load": int(label)}
                                )
                            for robot, label in enumerate(closed_labels):
                                closed_assignments.append(
                                    {**common, "method": method, "robot": robot, "load": int(label)}
                                )

    runs = pd.DataFrame(rows)
    raw_df = pd.DataFrame(raw_assignments)
    closed_df = pd.DataFrame(closed_assignments)
    history_df = pd.DataFrame(representative_histories)
    summary = _summarize(runs)
    hypotheses = _hypotheses(runs, primary="smith_qr")
    theory_audit = _theory_audit(runs)
    _write_table(runs, tables / "runs")
    _write_table(raw_df, tables / "assignments_raw")
    _write_table(closed_df, tables / "assignments_closed")
    _write_table(history_df, tables / "potential_histories")
    _write_table(summary, tables / "summary")
    _write_table(hypotheses, tables / "hypothesis_results")
    (output / "theory_audit.json").write_text(
        json.dumps(theory_audit, indent=2, sort_keys=True), encoding="utf-8"
    )
    _plot_results(runs, summary, history_df, figures)
    manifest = {
        "experiment_id": experiment_id,
        "status": "completed",
        "protocol": "SP1_HOMOGENEOUS_v1",
        "config_path": path.as_posix(),
        "config_hash": sha256(path.read_bytes()).hexdigest(),
        "worlds": int(runs["world_hash"].nunique()),
        "runs": int(len(runs)),
        "methods": methods,
        "theory_audit_passed": bool(theory_audit["passed"]),
        "confirmatory": bool(config.get("confirmatory", False)),
        "seeds_opened": [base_seed, base_seed + world_index - 1],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output / "report.md").write_text(
        _report_markdown(manifest, summary, hypotheses, theory_audit), encoding="utf-8"
    )
    return {"manifest": manifest, "summary": summary, "hypotheses": hypotheses, "theory_audit": theory_audit}


def _method_family(method: str) -> str:
    if method in POPULATION_METHODS:
        return "population_game"
    if method in CONTROL_METHODS:
        return "closure_control"
    if method == "hungarian_exact":
        return "centralized_exact"
    return "classical"


def _external_messages(world: HomogeneousWorld, method: str) -> int:
    if method == "hungarian_exact":
        return world.n_robots * world.n_loads
    if method == "auction_proxy":
        return world.n_robots * world.n_loads
    return world.n_robots


def _write_table(frame: pd.DataFrame, prefix: Path) -> None:
    frame.to_csv(prefix.with_suffix(".csv"), index=False)
    frame.to_parquet(prefix.with_suffix(".parquet"), index=False)


def _summarize(runs: pd.DataFrame) -> pd.DataFrame:
    columns = {
        "n": ("world_hash", "nunique"),
        "raw_valid_rate": ("raw_valid", "mean"),
        "raw_coverage_mean": ("raw_coverage", "mean"),
        "final_valid_rate": ("final_valid", "mean"),
        "final_coverage_mean": ("final_coverage", "mean"),
        "normalized_regret_mean": ("normalized_regret", "mean"),
        "normalized_regret_std": ("normalized_regret", "std"),
        "distance_m_mean": ("distance_m", "mean"),
        "convergence_rate": ("continuous_converged", "mean"),
        "potential_gain_mean": ("potential_gain", "mean"),
        "messages_mean": ("messages", "mean"),
        "runtime_s_mean": ("runtime_s", "mean"),
    }
    return runs.groupby("method", as_index=False).agg(**columns).sort_values(
        ["normalized_regret_mean", "method"], kind="stable"
    )


def _paired_values(runs: pd.DataFrame, left: str, right: str, metric: str) -> tuple[np.ndarray, np.ndarray]:
    lframe = runs[runs.method == left][["world_hash", metric]].rename(columns={metric: "left"})
    rframe = runs[runs.method == right][["world_hash", metric]].rename(columns={metric: "right"})
    merged = lframe.merge(rframe, on="world_hash", validate="one_to_one")
    return merged.left.to_numpy(dtype=float), merged.right.to_numpy(dtype=float)


def _bootstrap_ci(values: np.ndarray, *, seed: int = 71226, draws: int = 3000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if values.size == 0:
        return math.nan, math.nan
    indices = rng.integers(0, values.size, size=(draws, values.size))
    means = np.mean(values[indices], axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _holm(values: Iterable[float]) -> list[float]:
    raw = np.asarray(list(values), dtype=float)
    order = np.argsort(raw)
    adjusted = np.empty_like(raw)
    running = 0.0
    count = raw.size
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * raw[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def _hypotheses(runs: pd.DataFrame, *, primary: str) -> pd.DataFrame:
    comparisons = [
        method
        for method in ["greedy", "auction_proxy", "uniform_qr", "random_qr", "hungarian_exact"]
        if method in set(runs.method)
    ]
    rows: list[dict[str, Any]] = []
    for index, reference in enumerate(comparisons, start=1):
        left, right = _paired_values(runs, primary, reference, "normalized_regret")
        difference = left - right
        nonzero = difference[np.abs(difference) > 1.0e-14]
        if nonzero.size:
            p_value = float(wilcoxon(nonzero, alternative="two-sided", zero_method="wilcox").pvalue)
            p_value = max(p_value, np.finfo(float).tiny)
        else:
            p_value = 1.0
        low, high = _bootstrap_ci(difference, seed=71226 + index)
        rows.append(
            {
                "id": f"H-SP1-{index}",
                "candidate": primary,
                "reference": reference,
                "metric": "normalized_regret",
                "n_pairs": int(difference.size),
                "effect_mean_paired": float(np.mean(difference)),
                "ci95_low": low,
                "ci95_high": high,
                "p_value_raw": p_value,
                "interpretation": "candidate_better" if high < 0 else "reference_better" if low > 0 else "inconclusive",
            }
        )
    adjusted = _holm(row["p_value_raw"] for row in rows)
    for row, value in zip(rows, adjusted, strict=True):
        row["p_value_holm"] = value
        row["reject_holm_005"] = bool(value < 0.05)
    return pd.DataFrame(rows)


def _theory_audit(runs: pd.DataFrame) -> dict[str, Any]:
    population = runs[runs.method.isin(POPULATION_METHODS)]
    smith_complete = population[(population.method == "smith_qr") & (population.graph == "complete")]
    checks = {
        "simplex_invariant": bool((population.simplex_error <= 1.0e-10).all()),
        "finite_residuals": bool(np.isfinite(population.equilibrium_residual).all()),
        "closed_assignments_valid": bool(runs.final_valid.all()),
        "raw_and_closed_are_separate": bool(
            (runs[runs.method.isin(set(POPULATION_METHODS) | CONTROL_METHODS)].raw_valid
             != runs[runs.method.isin(set(POPULATION_METHODS) | CONTROL_METHODS)].final_valid).any()
        ),
        "smith_complete_graph_potential_monotone": bool((smith_complete.potential_violations == 0).all()),
        "world_pairing": bool(runs.groupby("world_hash").method.nunique().nunique() == 1),
    }
    return {
        "passed": bool(all(checks.values())),
        "checks": checks,
        "population_runs": int(len(population)),
        "smith_complete_graph_runs": int(len(smith_complete)),
        "max_simplex_error": float(population.simplex_error.max()),
        "total_potential_violations": int(population.potential_violations.sum()),
    }


def _plot_results(runs: pd.DataFrame, summary: pd.DataFrame, history: pd.DataFrame, output: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    colors = ["#004488", "#DDAA33", "#BB5566", "#228833", "#66CCEE", "#AA3377", "#999933", "#4477AA"]

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ordered = summary.sort_values("normalized_regret_mean")
    ax.bar(ordered.method, ordered.normalized_regret_mean, color=colors[: len(ordered)])
    ax.set_ylabel("Regret normalizado medio (menor es mejor)")
    ax.set_xlabel("Método")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(output / "sp1_homogeneous_regret.png", dpi=220)
    plt.close(fig)

    subset = summary[summary.method.isin(list(POPULATION_METHODS) + list(CONTROL_METHODS))]
    x = np.arange(len(subset))
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.bar(x - 0.18, subset.raw_coverage_mean, width=0.36, label="RAW", color="#BB5566")
    ax.bar(x + 0.18, subset.final_coverage_mean, width=0.36, label="Tras cierre", color="#228833")
    ax.set_xticks(x, subset.method, rotation=25, ha="right")
    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Cobertura de cuórum")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output / "sp1_homogeneous_raw_vs_closed.png", dpi=220)
    plt.close(fig)

    if not history.empty:
        selected_hash = history.world_hash.iloc[0]
        selected = history[history.world_hash == selected_hash]
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        for method, group in selected.groupby("method"):
            ax.plot(group.step, group.potential, label=method)
        ax.set_xlabel("Iteración")
        ax.set_ylabel("Potencial")
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(output / "sp1_homogeneous_potential.png", dpi=220)
        plt.close(fig)

    graph_summary = runs.groupby(["method", "graph"], as_index=False).normalized_regret.mean()
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    for graph, group in graph_summary.groupby("graph"):
        ax.plot(group.method, group.normalized_regret, marker="o", label=graph)
    ax.set_ylabel("Regret normalizado medio")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output / "sp1_homogeneous_graph_effect.png", dpi=220)
    plt.close(fig)


def _report_markdown(
    manifest: dict[str, Any], summary: pd.DataFrame, hypotheses: pd.DataFrame, theory_audit: dict[str, Any]
) -> str:
    lines = [
        f"# {manifest['experiment_id']}",
        "",
        "## Scope",
        "",
        "Homogeneous robots and loads with common quorum q. The q=1 case is the legacy one-to-one boundary; q>1 is homogeneous cooperative recruitment.",
        "",
        f"- Worlds: `{manifest['worlds']}`",
        f"- Runs: `{manifest['runs']}`",
        f"- Theory audit: `{'PASS' if theory_audit['passed'] else 'FAIL'}`",
        "",
        "## Summary",
        "",
        summary.to_markdown(index=False, floatfmt=".5g"),
        "",
        "## Paired hypotheses",
        "",
        hypotheses.to_markdown(index=False, floatfmt=".5g"),
        "",
        "## Interpretation contract",
        "",
        "- Population dynamics, argmax decoding, and integer closure are separate stages.",
        "- Hungarian is a centralized exact reference, not a deployable distributed method.",
        "- The ring graph is a fixed connected sensitivity condition; time-varying graphs are outside SP1.",
        "- A successful closure does not prove that the continuous dynamic reached an integer equilibrium.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "ALL_METHODS",
    "HomogeneousWorld",
    "PopulationResult",
    "evaluate_assignment",
    "fitness",
    "hungarian_exact",
    "make_homogeneous_world",
    "potential",
    "project_simplex",
    "quorum_closure",
    "run_homogeneous_campaign",
    "run_population",
    "vector_field",
]
