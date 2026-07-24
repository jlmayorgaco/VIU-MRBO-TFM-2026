"""Core algorithms for SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1.

The module is intentionally limited to strategic recruitment with one
indivisible scalar capacity per robot.  Robot positions parameterize travel
cost only: there is no docking, contact, transport, path planning or physical
controller in this campaign.

Notation follows ``docs/05_NOTATION.md``: ``rho`` denotes continuous
intention, while an integer ``assignment`` represents the executable decision.
The prompt's ``x``/``y`` notation is mapped in the frozen configuration.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import platform
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import (
    Bounds,
    LinearConstraint,
    linear_sum_assignment,
    linprog,
    milp,
    minimize,
)
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree, shortest_path


FLOAT64_BYTES = 8
INT64_BYTES = 8
BOOL_BYTES = 1

PRIMARY_METHODS = (
    "Capacity-CBBA",
    "Weighted-GRAPE",
    "Weighted-Pair-GRAPE",
    "DRD-simple-Replicator",
    "DRD-simple-Logit",
    "QPG-Replicator-AR",
    "QPG-Logit-AR",
    "Atomic-Quota-Logit",
)

QPG_REVIEW_METHODS = (
    "QPG-Replicator",
    "QPG-Smith",
    "QPG-BNN",
    "QPG-Logit",
    "QPG-Projection",
    "QPG-Damped-BestResponse",
)


def stable_hash(value: Any) -> str:
    """Return a stable SHA-256 for JSON-compatible values and arrays."""

    if isinstance(value, np.ndarray):
        payload = np.ascontiguousarray(value).tobytes()
    else:
        payload = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _readonly(array: np.ndarray, dtype: Any | None = None) -> np.ndarray:
    result = np.asarray(array, dtype=dtype).copy()
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class QuotaWorld:
    """Paired scalar-capacity recruitment instance."""

    seed: int
    world_id: str
    robot_positions: np.ndarray
    load_positions: np.ndarray
    capacities: np.ndarray
    lower_quotas: np.ndarray
    upper_quotas: np.ndarray
    compatibility: np.ndarray
    witness_assignment: np.ndarray
    distances_m: np.ndarray
    normalized_costs: np.ndarray
    normalization_scale_m: float
    capacity_regime: str
    utilization_target: float
    quota_band: str
    compatibility_regime: str
    world_hash: str
    service_durations_s: np.ndarray
    arrival_deadlines_s: np.ndarray

    def __post_init__(self) -> None:
        n = int(np.asarray(self.capacities).size)
        k = int(np.asarray(self.lower_quotas).size)
        if n < 1 or k < 1:
            raise ValueError("a quota world requires at least one robot and load")
        expected_nk = (n, k)
        for name, array, shape in (
            ("robot_positions", self.robot_positions, (n, 2)),
            ("load_positions", self.load_positions, (k, 2)),
            ("compatibility", self.compatibility, expected_nk),
            ("distances_m", self.distances_m, expected_nk),
            ("normalized_costs", self.normalized_costs, expected_nk),
        ):
            if np.asarray(array).shape != shape:
                raise ValueError(f"{name} must have shape {shape}")
        if np.asarray(self.upper_quotas).shape != (k,):
            raise ValueError("upper_quotas has invalid shape")
        if np.asarray(self.witness_assignment).shape != (n,):
            raise ValueError("witness_assignment has invalid shape")
        if np.any(np.asarray(self.capacities) <= 0.0):
            raise ValueError("capacities must be strictly positive")
        if np.any(np.asarray(self.lower_quotas) < 0.0):
            raise ValueError("lower quotas must be nonnegative")
        if np.any(np.asarray(self.upper_quotas) < np.asarray(self.lower_quotas)):
            raise ValueError("upper quotas must dominate lower quotas")
        if not np.all(np.isfinite(np.asarray(self.distances_m))):
            raise ValueError("physical distances must be finite")
        if self.normalization_scale_m <= 0.0:
            raise ValueError("normalization scale must be positive")

    @property
    def n_robots(self) -> int:
        return int(self.capacities.size)

    @property
    def n_loads(self) -> int:
        return int(self.lower_quotas.size)

    @property
    def idle_index(self) -> int:
        return self.n_loads

    @property
    def quota_widths(self) -> np.ndarray:
        return self.upper_quotas - self.lower_quotas


@dataclass(frozen=True, slots=True)
class QuotaGraph:
    """Connected robot communication graph and routed market metadata."""

    name: str
    adjacency: np.ndarray
    edges: int
    degree_min: int
    degree_max: int
    degree_mean: float
    diameter: int
    lambda_2: float
    lambda_max: float
    radius_m: float
    shortest_hops: np.ndarray
    market_hosts: np.ndarray
    market_route_hops: np.ndarray
    graph_hash: str

    @property
    def n_nodes(self) -> int:
        return int(self.adjacency.shape[0])


@dataclass(frozen=True, slots=True)
class OracleResult:
    method: str
    status: str
    status_code: int
    feasible: bool
    optimal: bool
    objective_m: float
    lower_bound_m: float
    upper_bound_m: float
    mip_gap: float
    assignment: np.ndarray | None
    rho: np.ndarray | None
    wall_time_s: float
    cpu_time_s: float
    message: str


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    assignment: np.ndarray
    success: bool
    failure_reason: str
    runtime_s: float
    chain_lengths: tuple[int, ...]
    nodes_expanded: int
    robots_reassigned: int
    cost_before_m: float
    cost_after_m: float
    loads_repaired: int
    residual_deficit_loads: int
    residual_excess_loads: int
    residual_no_path: bool

    @property
    def maximum_chain_length(self) -> int:
        return max(self.chain_lengths, default=0)

    @property
    def mean_chain_length(self) -> float:
        return float(np.mean(self.chain_lengths)) if self.chain_lengths else 0.0


@dataclass(frozen=True, slots=True)
class AlgorithmResult:
    method: str
    result_family: str
    rho: np.ndarray | None
    assignment: np.ndarray | None
    lambda_minus: np.ndarray
    lambda_plus: np.ndarray
    converged: bool
    censored: bool
    censoring_reason: str
    logical_rounds: int
    agent_updates: int
    payoff_evaluations: int
    pairwise_evaluations: int
    swaps: int
    accepted_moves: int
    packets_total: int
    scalar_transmissions_total: int
    payload_bytes_total: int
    bytes_to_first_feasible: int | None
    bytes_to_convergence: int | None
    first_feasible_round: int | None
    convergence_round: int | None
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    terminal_state_residual: float
    terminal_quota_residual: float
    terminal_price_residual: float
    terminal_consensus_residual: float
    simplex_violation: float
    mask_violation: float
    finite_state: bool
    traces: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    message_rows: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ServiceWorld:
    """Discrete-service instance used only by the faithful E10 benchmark."""

    seed: int
    world_id: str
    robot_services: np.ndarray
    task_requirements: np.ndarray
    task_service_utilities: np.ndarray
    graph: QuotaGraph

    @property
    def n_robots(self) -> int:
        return int(self.robot_services.shape[0])

    @property
    def n_services(self) -> int:
        return int(self.robot_services.shape[1])

    @property
    def n_tasks(self) -> int:
        return int(self.task_requirements.shape[0])


def _sample_capacities(
    rng: np.random.Generator,
    n: int,
    regime: str,
    config: Mapping[str, Any],
) -> np.ndarray:
    spec = config["capacity_regimes"][regime]
    if spec["kind"] == "uniform":
        return rng.uniform(float(spec["low"]), float(spec["high"]), size=n)
    if spec["kind"] != "mixture":
        raise ValueError(f"unknown capacity regime: {spec['kind']}")
    components = list(spec["components"])
    weights = np.asarray([float(item["weight"]) for item in components], dtype=float)
    weights /= weights.sum()
    labels = rng.choice(len(components), size=n, p=weights)
    capacities = np.empty(n, dtype=float)
    for component_index, component in enumerate(components):
        selected = labels == component_index
        capacities[selected] = rng.uniform(
            float(component["low"]),
            float(component["high"]),
            size=int(np.sum(selected)),
        )
    return capacities


def _compatibility_mask(
    rng: np.random.Generator,
    regime: str,
    distances: np.ndarray,
    capacities: np.ndarray,
    witness: np.ndarray,
    config: Mapping[str, Any],
) -> np.ndarray:
    n, k = distances.shape
    spec = config["compatibility"][regime]
    kind = str(spec["kind"])
    if kind == "full":
        mask = np.ones((n, k), dtype=bool)
    elif kind == "radius_with_witness":
        threshold = float(np.quantile(distances, float(spec["nonwitness_quantile"])))
        mask = distances <= threshold
    elif kind == "critical_sparse":
        mask = rng.random((n, k)) < float(spec["other_robot_probability"])
        critical_threshold = float(np.quantile(capacities, 0.90))
        maximum_extra = int(spec["large_robot_max_extra_loads"])
        for robot in np.flatnonzero(capacities >= critical_threshold):
            allowed = {int(witness[robot])}
            extras = [load for load in np.argsort(distances[robot]) if load not in allowed]
            allowed.update(map(int, extras[:maximum_extra]))
            mask[robot] = False
            mask[robot, list(allowed)] = True
    else:
        raise ValueError(f"unsupported compatibility kind: {kind}")
    mask[np.arange(n), witness] = True
    for robot in range(n):
        if not np.any(mask[robot]):
            mask[robot, int(witness[robot])] = True
    return mask


def make_quota_world(
    n: int,
    k: int,
    seed: int,
    config: Mapping[str, Any],
    *,
    capacity_regime: str = "medium",
    utilization: float = 0.8,
    quota_band: str = "medium",
    compatibility_regime: str = "arrival_radius",
    world_id: str | None = None,
) -> QuotaWorld:
    """Generate a paired feasible world from an audit-only hidden witness."""

    if n < k or k < 1:
        raise ValueError("world generation requires n >= k >= 1")
    if not 0.0 < utilization <= 1.0:
        raise ValueError("utilization must lie in (0, 1]")
    side = float(config["problem"]["workspace_side_m"])
    max_attempts = int(config["problem"]["max_world_generation_attempts"])
    headroom = float(config["quota_bands"][quota_band]["headroom_fraction_of_witness"])
    duration_range = config["evaluation"]["e7"]["service_duration_range"]
    deadline_range = config["evaluation"]["e7"]["arrival_deadline_range"]

    for attempt in range(max_attempts):
        mixed_seed = (
            int(seed)
            + 104729 * int(n)
            + 130363 * int(k)
            + 15485863 * int(attempt)
            + int(round(1000 * utilization))
        )
        rng = np.random.default_rng(mixed_seed)
        robot_positions = rng.uniform(0.0, side, size=(n, 2))
        load_positions = rng.uniform(0.0, side, size=(k, 2))
        capacities = _sample_capacities(rng, n, capacity_regime, config)
        permutation = rng.permutation(n)
        groups = np.array_split(permutation, k)
        if any(len(group) == 0 for group in groups):
            continue
        witness = np.full(n, -1, dtype=int)
        witness_capacity = np.zeros(k, dtype=float)
        for load, members in enumerate(groups):
            witness[members] = load
            witness_capacity[load] = float(np.sum(capacities[members]))
        lower = utilization * witness_capacity
        slack_upper = (1.0 - utilization + headroom) * witness_capacity
        upper = lower + slack_upper
        distances = np.linalg.norm(
            robot_positions[:, None, :] - load_positions[None, :, :],
            axis=2,
        )
        scale = max(float(np.max(distances)), 1.0e-12)
        normalized = distances / scale
        compatibility = _compatibility_mask(
            rng,
            compatibility_regime,
            distances,
            capacities,
            witness,
            config,
        )
        witness_metrics = capacities_by_load(witness, capacities, k)
        tolerance = float(config["problem"]["numerical_tolerance"])
        if np.any(witness_metrics < lower - tolerance) or np.any(
            witness_metrics > upper + tolerance
        ):
            continue
        identifier = world_id or (
            f"n{n}_k{k}_s{seed}_{capacity_regime}_u{utilization:.2f}_"
            f"{quota_band}_{compatibility_regime}"
        )
        payload = {
            "seed": int(seed),
            "n": n,
            "k": k,
            "robot_positions": robot_positions.round(12).tolist(),
            "load_positions": load_positions.round(12).tolist(),
            "capacities": capacities.round(12).tolist(),
            "lower": lower.round(12).tolist(),
            "upper": upper.round(12).tolist(),
            "compatibility": compatibility.astype(int).tolist(),
            "witness": witness.tolist(),
        }
        return QuotaWorld(
            seed=int(seed),
            world_id=identifier,
            robot_positions=_readonly(robot_positions, float),
            load_positions=_readonly(load_positions, float),
            capacities=_readonly(capacities, float),
            lower_quotas=_readonly(lower, float),
            upper_quotas=_readonly(upper, float),
            compatibility=_readonly(compatibility, bool),
            witness_assignment=_readonly(witness, int),
            distances_m=_readonly(distances, float),
            normalized_costs=_readonly(normalized, float),
            normalization_scale_m=scale,
            capacity_regime=capacity_regime,
            utilization_target=float(utilization),
            quota_band=quota_band,
            compatibility_regime=compatibility_regime,
            world_hash=stable_hash(payload),
            service_durations_s=_readonly(
                rng.uniform(float(duration_range[0]), float(duration_range[1]), size=k),
                float,
            ),
            arrival_deadlines_s=_readonly(
                rng.uniform(float(deadline_range[0]), float(deadline_range[1]), size=k),
                float,
            ),
        )
    raise RuntimeError(f"could not generate a feasible quota world after {max_attempts} attempts")


def make_manual_quota_world(
    *,
    case_id: str,
    robot_positions: np.ndarray,
    load_positions: np.ndarray,
    capacities: np.ndarray,
    lower_quotas: np.ndarray,
    upper_quotas: np.ndarray,
    compatibility: np.ndarray,
    witness_assignment: np.ndarray,
) -> QuotaWorld:
    """Construct a deterministic world used by E0/E9 and unit tests."""

    robot_positions = np.asarray(robot_positions, dtype=float)
    load_positions = np.asarray(load_positions, dtype=float)
    capacities = np.asarray(capacities, dtype=float)
    lower = np.asarray(lower_quotas, dtype=float)
    upper = np.asarray(upper_quotas, dtype=float)
    mask = np.asarray(compatibility, dtype=bool)
    witness = np.asarray(witness_assignment, dtype=int)
    distances = np.linalg.norm(
        robot_positions[:, None, :] - load_positions[None, :, :],
        axis=2,
    )
    scale = max(float(np.max(distances)), 1.0e-12)
    payload = {
        "case_id": case_id,
        "positions": robot_positions.tolist(),
        "loads": load_positions.tolist(),
        "capacities": capacities.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "compatibility": mask.astype(int).tolist(),
        "witness": witness.tolist(),
    }
    return QuotaWorld(
        seed=0,
        world_id=case_id,
        robot_positions=_readonly(robot_positions),
        load_positions=_readonly(load_positions),
        capacities=_readonly(capacities),
        lower_quotas=_readonly(lower),
        upper_quotas=_readonly(upper),
        compatibility=_readonly(mask, bool),
        witness_assignment=_readonly(witness, int),
        distances_m=_readonly(distances),
        normalized_costs=_readonly(distances / scale),
        normalization_scale_m=scale,
        capacity_regime="deterministic",
        utilization_target=float(np.sum(lower) / np.sum(capacities)),
        quota_band="deterministic",
        compatibility_regime="deterministic",
        world_hash=stable_hash(payload),
        service_durations_s=_readonly(np.ones(lower.size)),
        arrival_deadlines_s=_readonly(np.ones(lower.size)),
    )


def _connected_adjacency(
    positions: np.ndarray,
    target_degree: float,
) -> tuple[np.ndarray, float]:
    """Return a literal connected random-geometric graph.

    The radius is the larger of the target-degree radius and the longest edge
    in the Euclidean minimum spanning tree.  Consequently every returned edge
    satisfies the reported disk radius.
    """

    n = int(positions.shape[0])
    if n == 1:
        return np.zeros((1, 1), dtype=np.int8), 0.0
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    finite = np.sort(distances[np.isfinite(distances)])
    target_edges = int(math.ceil(n * min(float(target_degree), n - 1) / 2.0))
    target_edges = min(max(target_edges, n - 1), n * (n - 1) // 2)
    upper_values = np.sort(distances[np.triu_indices(n, k=1)])
    target_radius = float(upper_values[min(target_edges - 1, upper_values.size - 1)])
    mst = minimum_spanning_tree(csr_matrix(np.where(np.isfinite(distances), distances, 0.0)))
    mst_radius = float(np.max(mst.data)) if mst.nnz else 0.0
    radius = max(target_radius, mst_radius) + 1.0e-12
    adjacency = ((distances <= radius) & np.isfinite(distances)).astype(np.int8)
    np.fill_diagonal(adjacency, 0)
    return adjacency, radius


def make_quota_graph(
    world: QuotaWorld,
    topology: str,
    config: Mapping[str, Any],
) -> QuotaGraph:
    n = world.n_robots
    if topology == "complete":
        adjacency = np.ones((n, n), dtype=np.int8) - np.eye(n, dtype=np.int8)
        radius = math.inf
    elif topology.startswith("rdisk_degree_"):
        target = float(topology.rsplit("_", 1)[-1])
        adjacency, radius = _connected_adjacency(world.robot_positions, target)
    else:
        raise ValueError(f"unsupported topology: {topology}")
    components = connected_components(csr_matrix(adjacency), directed=False, return_labels=False)
    if int(components) != 1:
        raise RuntimeError("graph construction did not produce a connected graph")
    degrees = adjacency.sum(axis=1).astype(int)
    laplacian = np.diag(degrees.astype(float)) - adjacency.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    hops = shortest_path(csr_matrix(adjacency), directed=False, unweighted=True)
    finite_hops = hops[np.isfinite(hops)]
    diameter = int(np.max(finite_hops)) if finite_hops.size else 0
    market_hosts = np.empty(world.n_loads, dtype=int)
    market_route_hops = np.zeros((world.n_loads, n), dtype=int)
    for load in range(world.n_loads):
        candidates = np.flatnonzero(world.compatibility[:, load])
        host = int(candidates[np.argmin(world.distances_m[candidates, load])])
        market_hosts[load] = host
        market_route_hops[load] = hops[host].astype(int)
    edges = int(np.sum(adjacency) // 2)
    payload = {
        "topology": topology,
        "adjacency": adjacency.tolist(),
        "hosts": market_hosts.tolist(),
    }
    return QuotaGraph(
        name=topology,
        adjacency=_readonly(adjacency, np.int8),
        edges=edges,
        degree_min=int(np.min(degrees)),
        degree_max=int(np.max(degrees)),
        degree_mean=float(np.mean(degrees)),
        diameter=diameter,
        lambda_2=float(eigenvalues[1]) if n > 1 else 0.0,
        lambda_max=float(eigenvalues[-1]) if eigenvalues.size else 0.0,
        radius_m=float(radius),
        shortest_hops=_readonly(hops, float),
        market_hosts=_readonly(market_hosts, int),
        market_route_hops=_readonly(market_route_hops, int),
        graph_hash=stable_hash(payload),
    )


def graph_metadata(graph: QuotaGraph) -> dict[str, Any]:
    return {
        "topology": graph.name,
        "graph_hash": graph.graph_hash,
        "graph_edges": graph.edges,
        "degree_min": graph.degree_min,
        "degree_max": graph.degree_max,
        "degree_mean": graph.degree_mean,
        "diameter": graph.diameter,
        "lambda_2": graph.lambda_2,
        "lambda_max": graph.lambda_max,
        "radius_m": graph.radius_m,
    }


def world_metadata(world: QuotaWorld) -> dict[str, Any]:
    witness_capacity = capacities_by_load(
        world.witness_assignment,
        world.capacities,
        world.n_loads,
    )
    return {
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization_target": world.utilization_target,
        "realized_lower_utilization": float(
            np.sum(world.lower_quotas) / np.sum(world.capacities)
        ),
        "quota_band": world.quota_band,
        "compatibility_regime": world.compatibility_regime,
        "compatible_pairs": int(np.sum(world.compatibility)),
        "compatibility_density": float(np.mean(world.compatibility)),
        "witness_feasible": bool(
            np.all(witness_capacity >= world.lower_quotas - 1.0e-9)
            and np.all(witness_capacity <= world.upper_quotas + 1.0e-9)
        ),
        "normalization_scale_m": world.normalization_scale_m,
    }


def capacities_by_load(
    assignment: np.ndarray,
    capacities: np.ndarray,
    n_loads: int,
) -> np.ndarray:
    assignment = np.asarray(assignment, dtype=int)
    capacities = np.asarray(capacities, dtype=float)
    valid = (assignment >= 0) & (assignment < int(n_loads))
    return np.bincount(
        assignment[valid],
        weights=capacities[valid],
        minlength=int(n_loads),
    ).astype(float)


def assignment_matrix(assignment: np.ndarray, n_loads: int) -> np.ndarray:
    assignment = np.asarray(assignment, dtype=int)
    matrix = np.zeros((assignment.size, int(n_loads)), dtype=float)
    valid = (assignment >= 0) & (assignment < int(n_loads))
    matrix[np.flatnonzero(valid), assignment[valid]] = 1.0
    return matrix


def assignment_distance(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    normalized: bool = False,
) -> float:
    assignment = np.asarray(assignment, dtype=int)
    valid = (assignment >= 0) & (assignment < world.n_loads)
    costs = world.normalized_costs if normalized else world.distances_m
    return float(np.sum(costs[np.flatnonzero(valid), assignment[valid]]))


def assignment_is_compatible(world: QuotaWorld, assignment: np.ndarray) -> bool:
    assignment = np.asarray(assignment, dtype=int)
    valid = (assignment >= 0) & (assignment < world.n_loads)
    return bool(
        np.all(world.compatibility[np.flatnonzero(valid), assignment[valid]])
        and np.all((assignment >= 0) & (assignment <= world.idle_index))
    )


def evaluate_assignment(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    previous_assignment: np.ndarray | None = None,
    tolerance: float = 1.0e-9,
) -> dict[str, Any]:
    assignment = np.asarray(assignment, dtype=int)
    capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
    deficit = np.maximum(world.lower_quotas - capacity, 0.0)
    excess_upper = np.maximum(capacity - world.upper_quotas, 0.0)
    over_lower = np.maximum(capacity - world.lower_quotas, 0.0)
    compatibility = assignment_is_compatible(world, assignment)
    exclusivity = bool(assignment.shape == (world.n_robots,))
    recourse = (
        int(np.sum(assignment != np.asarray(previous_assignment, dtype=int)))
        if previous_assignment is not None
        else 0
    )
    used = assignment < world.n_loads
    distances = (
        world.distances_m[np.flatnonzero(used), assignment[used]]
        if np.any(used)
        else np.asarray([], dtype=float)
    )
    feasible = bool(
        exclusivity
        and compatibility
        and np.max(deficit, initial=0.0) <= tolerance
        and np.max(excess_upper, initial=0.0) <= tolerance
    )
    return {
        "feasible": feasible,
        "compatible": compatibility,
        "exclusive": exclusivity,
        "capacity": capacity,
        "deficit_total": float(np.sum(deficit)),
        "deficit_ratio": float(np.sum(deficit) / max(np.sum(world.lower_quotas), 1.0e-12)),
        "excess_upper_total": float(np.sum(excess_upper)),
        "overcapacity_total": float(np.sum(over_lower)),
        "overcapacity_ratio": float(
            np.sum(over_lower) / max(np.sum(world.lower_quotas), 1.0e-12)
        ),
        "robots_used": int(np.sum(used)),
        "distance_total_m": float(np.sum(distances)),
        "maximum_distance_m": float(np.max(distances, initial=0.0)),
        "recourse_hamming": recourse,
        "duplicate_assignment_count": 0,
    }


def social_potential(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    rho_minus: float,
    rho_plus: float,
    gamma_switch: float = 0.0,
    previous_assignment: np.ndarray | None = None,
) -> float:
    assignment = np.asarray(assignment, dtype=int)
    capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
    deficit = np.maximum(world.lower_quotas - capacity, 0.0)
    excess = np.maximum(capacity - world.upper_quotas, 0.0)
    recourse = (
        int(np.sum(assignment != np.asarray(previous_assignment, dtype=int)))
        if previous_assignment is not None
        else 0
    )
    return float(
        -assignment_distance(world, assignment, normalized=True)
        - 0.5 * float(rho_minus) * np.dot(deficit, deficit)
        - 0.5 * float(rho_plus) * np.dot(excess, excess)
        - float(gamma_switch) * recourse
    )


def marginal_move_value(
    world: QuotaWorld,
    assignment: np.ndarray,
    robot: int,
    destination: int,
    *,
    rho_minus: float,
    rho_plus: float,
    gamma_switch: float = 0.0,
    previous_assignment: np.ndarray | None = None,
) -> float:
    assignment = np.asarray(assignment, dtype=int)
    source = int(assignment[robot])
    if destination == source:
        return 0.0
    if destination < world.n_loads and not world.compatibility[robot, destination]:
        return -math.inf
    if destination < 0 or destination > world.idle_index:
        return -math.inf
    candidate = assignment.copy()
    candidate[robot] = int(destination)
    return social_potential(
        world,
        candidate,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
        gamma_switch=gamma_switch,
        previous_assignment=previous_assignment,
    ) - social_potential(
        world,
        assignment,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
        gamma_switch=gamma_switch,
        previous_assignment=previous_assignment,
    )


def _linear_constraint_matrix(world: QuotaWorld) -> csr_matrix:
    n, k = world.n_robots, world.n_loads
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for robot in range(n):
        for load in range(k):
            column = robot * k + load
            rows.append(robot)
            cols.append(column)
            data.append(1.0)
            rows.append(n + load)
            cols.append(column)
            data.append(float(world.capacities[robot]))
    return coo_matrix((data, (rows, cols)), shape=(n + k, n * k)).tocsr()


def _variable_bounds(world: QuotaWorld) -> Bounds:
    upper = world.compatibility.astype(float).ravel()
    return Bounds(np.zeros(world.n_robots * world.n_loads), upper)


def solve_quota_lp(world: QuotaWorld) -> OracleResult:
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    n, k = world.n_robots, world.n_loads
    costs = world.distances_m.ravel()
    rows = _linear_constraint_matrix(world)
    a_ub = csr_matrix(
        np.vstack(
            [
                rows[:n].toarray(),
                rows[n:].toarray(),
                -rows[n:].toarray(),
            ]
        )
    )
    b_ub = np.r_[
        np.ones(n),
        world.upper_quotas,
        -world.lower_quotas,
    ]
    bounds = [
        (0.0, 1.0 if world.compatibility[robot, load] else 0.0)
        for robot in range(n)
        for load in range(k)
    ]
    try:
        result = linprog(costs, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
        feasible = bool(result.success and result.x is not None)
        rho = np.asarray(result.x, dtype=float).reshape(n, k) if feasible else None
        objective = float(result.fun) if feasible else math.nan
        status = "optimal" if result.success else (
            "infeasible" if int(result.status) == 2 else "solver_error"
        )
        return OracleResult(
            method="LP-raw",
            status=status,
            status_code=int(result.status),
            feasible=feasible,
            optimal=bool(result.success),
            objective_m=objective,
            lower_bound_m=objective,
            upper_bound_m=objective,
            mip_gap=0.0 if result.success else math.nan,
            assignment=None,
            rho=rho,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=str(result.message),
        )
    except Exception as exc:  # pragma: no cover - defensive solver boundary
        return OracleResult(
            method="LP-raw",
            status="solver_error",
            status_code=-1,
            feasible=False,
            optimal=False,
            objective_m=math.nan,
            lower_bound_m=math.nan,
            upper_bound_m=math.nan,
            mip_gap=math.nan,
            assignment=None,
            rho=None,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=repr(exc),
        )


def solve_quota_milp(world: QuotaWorld, *, time_limit_s: float = 60.0) -> OracleResult:
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    n, k = world.n_robots, world.n_loads
    matrix = _linear_constraint_matrix(world)
    lower = np.r_[np.full(n, -np.inf), world.lower_quotas]
    upper = np.r_[np.ones(n), world.upper_quotas]
    try:
        result = milp(
            c=world.distances_m.ravel(),
            integrality=np.ones(n * k, dtype=np.int8),
            bounds=_variable_bounds(world),
            constraints=LinearConstraint(matrix, lower, upper),
            options={"time_limit": float(time_limit_s), "mip_rel_gap": 0.0},
        )
        has_incumbent = result.x is not None and np.all(np.isfinite(result.x))
        assignment = None
        if has_incumbent:
            matrix_x = np.asarray(result.x, dtype=float).reshape(n, k)
            assignment = np.full(n, k, dtype=int)
            selected = np.max(matrix_x, axis=1) > 0.5
            assignment[selected] = np.argmax(matrix_x[selected], axis=1)
        objective = float(result.fun) if has_incumbent and result.fun is not None else math.nan
        lower_bound = float(getattr(result, "mip_dual_bound", math.nan))
        gap = float(getattr(result, "mip_gap", math.nan))
        optimal = bool(result.success and int(result.status) == 0 and gap <= 1.0e-8)
        feasible = bool(
            assignment is not None
            and evaluate_assignment(world, assignment)["feasible"]
        )
        if optimal:
            status = "optimal"
        elif int(result.status) == 1 and feasible:
            status = "timeout_incumbent"
        elif int(result.status) == 1:
            status = "timeout_no_incumbent"
        elif int(result.status) == 2:
            status = "infeasible"
        else:
            status = "solver_error"
        return OracleResult(
            method="MILP-oracle",
            status=status,
            status_code=int(result.status),
            feasible=feasible,
            optimal=optimal,
            objective_m=objective,
            lower_bound_m=lower_bound,
            upper_bound_m=objective,
            mip_gap=gap,
            assignment=assignment,
            rho=None,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=str(result.message),
        )
    except Exception as exc:  # pragma: no cover - defensive solver boundary
        return OracleResult(
            method="MILP-oracle",
            status="solver_error",
            status_code=-1,
            feasible=False,
            optimal=False,
            objective_m=math.nan,
            lower_bound_m=math.nan,
            upper_bound_m=math.nan,
            mip_gap=math.nan,
            assignment=None,
            rho=None,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=repr(exc),
        )


def solve_quota_entropy_reference(
    world: QuotaWorld,
    *,
    tau: float,
    max_iterations: int = 2000,
) -> OracleResult:
    """Solve the convex entropy-regularized relaxation with SLSQP.

    The returned point is a numerical reference, not a physical assignment.
    """

    if tau <= 0.0:
        raise ValueError("tau must be positive")
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    n, k = world.n_robots, world.n_loads
    initial = assignment_matrix(world.witness_assignment, k).ravel()
    matrix = _linear_constraint_matrix(world)
    constraint = LinearConstraint(
        matrix,
        np.r_[np.full(n, -np.inf), world.lower_quotas],
        np.r_[np.ones(n), world.upper_quotas],
    )
    epsilon = 1.0e-15
    costs = world.normalized_costs.ravel()

    def objective(vector: np.ndarray) -> float:
        clipped = np.maximum(vector, epsilon)
        return float(np.dot(costs, vector) + tau * np.dot(vector, np.log(clipped)))

    def jacobian(vector: np.ndarray) -> np.ndarray:
        return costs + tau * (np.log(np.maximum(vector, epsilon)) + 1.0)

    try:
        result = minimize(
            objective,
            initial,
            jac=jacobian,
            method="SLSQP",
            bounds=_variable_bounds(world),
            constraints=[constraint],
            options={"maxiter": int(max_iterations), "ftol": 1.0e-11},
        )
        rho = np.asarray(result.x, dtype=float).reshape(n, k) if result.x is not None else None
        feasible = False
        if rho is not None and np.all(np.isfinite(rho)):
            row_sums = rho.sum(axis=1)
            capacity = np.einsum("i,ik->k", world.capacities, rho)
            feasible = bool(
                np.max(row_sums - 1.0, initial=0.0) <= 1.0e-7
                and np.max(world.lower_quotas - capacity, initial=0.0) <= 1.0e-7
                and np.max(capacity - world.upper_quotas, initial=0.0) <= 1.0e-7
                and np.max(rho[~world.compatibility], initial=0.0) <= 1.0e-9
            )
        objective_m = (
            float(np.sum(world.distances_m * rho)) if rho is not None else math.nan
        )
        return OracleResult(
            method="LP-entropy",
            status="optimal_numerical" if result.success and feasible else "solver_error",
            status_code=int(result.status),
            feasible=feasible,
            optimal=bool(result.success and feasible),
            objective_m=objective_m,
            lower_bound_m=math.nan,
            upper_bound_m=math.nan,
            mip_gap=math.nan,
            assignment=None,
            rho=rho,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=str(result.message),
        )
    except Exception as exc:  # pragma: no cover
        return OracleResult(
            method="LP-entropy",
            status="solver_error",
            status_code=-1,
            feasible=False,
            optimal=False,
            objective_m=math.nan,
            lower_bound_m=math.nan,
            upper_bound_m=math.nan,
            mip_gap=math.nan,
            assignment=None,
            rho=None,
            wall_time_s=float(time.perf_counter() - started_wall),
            cpu_time_s=float(time.process_time() - started_cpu),
            message=repr(exc),
        )


def solve_hungarian_slots(
    distances: np.ndarray,
    slot_loads: Sequence[int],
) -> tuple[np.ndarray, float]:
    """Polynomial control for unit capacities and nonrestrictive upper quotas."""

    distances = np.asarray(distances, dtype=float)
    slots = np.asarray(slot_loads, dtype=int)
    if distances.shape[0] < slots.size:
        raise ValueError("there must be at least as many robots as slots")
    expanded = distances[:, slots]
    rows, columns = linear_sum_assignment(expanded)
    assignment = np.full(distances.shape[0], distances.shape[1], dtype=int)
    assignment[rows] = slots[columns]
    return assignment, float(expanded[rows, columns].sum())


def continuous_metrics(world: QuotaWorld, rho: np.ndarray) -> dict[str, Any]:
    rho = np.asarray(rho, dtype=float)
    if rho.shape == (world.n_robots, world.n_loads + 1):
        load_rho = rho[:, : world.n_loads]
        row_sums = rho.sum(axis=1)
    elif rho.shape == (world.n_robots, world.n_loads):
        load_rho = rho
        row_sums = rho.sum(axis=1)
    else:
        raise ValueError("rho has invalid shape")
    capacity = np.einsum("i,ik->k", world.capacities, load_rho)
    deficit = np.maximum(world.lower_quotas - capacity, 0.0)
    excess = np.maximum(capacity - world.upper_quotas, 0.0)
    return {
        "capacity": capacity,
        "deficit_total": float(np.sum(deficit)),
        "excess_upper_total": float(np.sum(excess)),
        "quota_residual": float(
            math.hypot(np.linalg.norm(deficit), np.linalg.norm(excess))
            / (1.0 + np.linalg.norm(world.lower_quotas))
        ),
        "simplex_violation": float(np.max(np.abs(row_sums - 1.0), initial=0.0)),
        "nonnegativity_violation": float(max(0.0, -np.min(rho, initial=0.0))),
        "mask_violation": float(np.max(load_rho[~world.compatibility], initial=0.0)),
        "finite": bool(np.all(np.isfinite(rho))),
        "objective_m": float(np.sum(world.distances_m * load_rho)),
        "objective_normalized": float(np.sum(world.normalized_costs * load_rho)),
    }


def nonregularized_dual_lower_bound(
    world: QuotaWorld,
    lambda_minus: np.ndarray,
    lambda_plus: np.ndarray,
) -> float:
    """Compute the valid LP/MILP lower bound d0(lambda) in metres."""

    lambda_minus = np.maximum(np.asarray(lambda_minus, dtype=float), 0.0)
    lambda_plus = np.maximum(np.asarray(lambda_plus, dtype=float), 0.0)
    reduced = (
        world.distances_m
        - world.capacities[:, None] * lambda_minus[None, :]
        + world.capacities[:, None] * lambda_plus[None, :]
    )
    reduced = np.where(world.compatibility, reduced, np.inf)
    robot_terms = np.minimum(0.0, np.min(reduced, axis=1))
    return float(
        np.dot(lambda_minus, world.lower_quotas)
        - np.dot(lambda_plus, world.upper_quotas)
        + np.sum(robot_terms)
    )


def entropy_dual_lower_bound(
    world: QuotaWorld,
    lambda_minus: np.ndarray,
    lambda_plus: np.ndarray,
    *,
    tau: float,
) -> float:
    """Dual function of the entropy-regularized normalized relaxation."""

    if tau <= 0.0:
        raise ValueError("tau must be positive")
    lm = np.maximum(np.asarray(lambda_minus, dtype=float), 0.0)
    lp = np.maximum(np.asarray(lambda_plus, dtype=float), 0.0)
    reduced = (
        world.normalized_costs
        - world.capacities[:, None] * lm[None, :]
        + world.capacities[:, None] * lp[None, :]
    )
    reduced = np.where(world.compatibility, reduced, np.inf)
    minimum = np.minimum(0.0, np.min(reduced, axis=1))
    shifted = np.exp(-(reduced - minimum[:, None]) / tau)
    shifted[~np.isfinite(shifted)] = 0.0
    idle = np.exp(minimum / tau)
    robot_terms = minimum - tau * np.log(idle + np.sum(shifted, axis=1))
    return float(
        np.dot(lm, world.lower_quotas)
        - np.dot(lp, world.upper_quotas)
        + np.sum(robot_terms)
    )


def certificate_diagnostics(
    world: QuotaWorld,
    rho: np.ndarray,
    atomic_assignment: np.ndarray,
    lambda_minus_normalized: np.ndarray,
    lambda_plus_normalized: np.ndarray,
    *,
    tau: float,
    lp_reference: OracleResult | None = None,
    milp_reference: OracleResult | None = None,
    tolerance: float = 1.0e-7,
) -> dict[str, Any]:
    """Return online and decomposition diagnostics without overclaiming."""

    atomic = evaluate_assignment(world, atomic_assignment, tolerance=tolerance)
    scale = world.normalization_scale_m
    lm_m = np.asarray(lambda_minus_normalized, dtype=float) / scale
    lp_m = np.asarray(lambda_plus_normalized, dtype=float) / scale
    lower_bound_m = nonregularized_dual_lower_bound(world, lm_m, lp_m)
    upper_bound_m = float(atomic["distance_total_m"]) if atomic["feasible"] else math.nan
    gap = (
        (upper_bound_m - lower_bound_m) / max(1.0, abs(lower_bound_m))
        if np.isfinite(upper_bound_m) and np.isfinite(lower_bound_m)
        else math.nan
    )
    load_rho = np.asarray(rho, dtype=float)[:, : world.n_loads]
    continuous_cost_m = float(np.sum(world.distances_m * load_rho))
    entropy = float(
        -np.sum(
            np.where(
                np.asarray(rho) > 0.0,
                np.asarray(rho) * np.log(np.maximum(np.asarray(rho), 1.0e-300)),
                0.0,
            )
        )
    )
    action_counts = np.sum(world.compatibility, axis=1) + 1
    entropy_bias_normalized = float(tau * np.sum(np.log(action_counts)))
    regularized_primal = float(
        np.sum(world.normalized_costs * load_rho) - tau * entropy
    )
    entropic_dual = entropy_dual_lower_bound(
        world,
        lambda_minus_normalized,
        lambda_plus_normalized,
        tau=tau,
    )
    regularized_gap = regularized_primal - entropic_dual
    valid = bool(
        np.isfinite(lower_bound_m)
        and (lp_reference is None or not lp_reference.optimal or lower_bound_m <= lp_reference.objective_m + tolerance)
        and (
            milp_reference is None
            or not milp_reference.optimal
            or lower_bound_m <= milp_reference.objective_m + tolerance
        )
        and (not atomic["feasible"] or lower_bound_m <= upper_bound_m + tolerance)
    )
    return {
        "dual_lower_bound_m": lower_bound_m,
        "integer_upper_bound_m": upper_bound_m,
        "gap_cert": gap,
        "certificate_valid": valid,
        "regularized_primal_normalized": regularized_primal,
        "regularized_dual_normalized": entropic_dual,
        "optimization_error_normalized": regularized_gap,
        "entropy_bias_bound_normalized": entropy_bias_normalized,
        "atomicity_cost_m": upper_bound_m - continuous_cost_m
        if np.isfinite(upper_bound_m)
        else math.nan,
        "continuous_cost_m": continuous_cost_m,
        "entropy": entropy,
    }


def bernstein_rounding_bound(world: QuotaWorld, rho: np.ndarray) -> dict[str, Any]:
    """Union bound for independent categorical rounding of one state."""

    rho = np.asarray(rho, dtype=float)
    probabilities = rho[:, : world.n_loads]
    means = np.einsum("i,ik->k", world.capacities, probabilities)
    variances = np.einsum(
        "i,ik->k",
        world.capacities**2,
        probabilities * (1.0 - probabilities),
    )
    maximum = float(np.max(world.capacities))
    lower_margin = means - world.lower_quotas
    upper_margin = world.upper_quotas - means

    def one_sided(margin: np.ndarray) -> np.ndarray:
        result = np.ones_like(margin, dtype=float)
        deterministic_safe = (variances <= 1.0e-15) & (margin >= 0.0)
        result[deterministic_safe] = 0.0
        positive = margin > 0.0
        positive &= ~deterministic_safe
        result[positive] = np.exp(
            -(margin[positive] ** 2)
            / (2.0 * (variances[positive] + maximum * margin[positive] / 3.0))
        )
        return np.clip(result, 0.0, 1.0)

    lower_bounds = one_sided(lower_margin)
    upper_bounds = one_sided(upper_margin)
    union = float(min(1.0, np.sum(lower_bounds) + np.sum(upper_bounds)))
    return {
        "capacity_mean": means,
        "capacity_variance": variances,
        "lower_margin": lower_margin,
        "upper_margin": upper_margin,
        "lower_failure_bound": lower_bounds,
        "upper_failure_bound": upper_bounds,
        "union_failure_bound": union,
    }


def categorical_round(
    world: QuotaWorld,
    rho: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    rho = np.asarray(rho, dtype=float)
    if rho.shape != (world.n_robots, world.n_loads + 1):
        raise ValueError("rho must include the idle strategy")
    assignment = np.empty(world.n_robots, dtype=int)
    for robot in range(world.n_robots):
        probabilities = np.maximum(rho[robot], 0.0)
        probabilities[: world.n_loads] = np.where(
            world.compatibility[robot],
            probabilities[: world.n_loads],
            0.0,
        )
        total = float(np.sum(probabilities))
        if total <= 0.0:
            assignment[robot] = world.idle_index
        else:
            assignment[robot] = int(rng.choice(world.n_loads + 1, p=probabilities / total))
    return assignment


def raw_assignment_from_rho(world: QuotaWorld, rho: np.ndarray) -> np.ndarray:
    """Independent argmax closure with deterministic idle-aware tie breaking."""

    rho = np.asarray(rho, dtype=float)
    if rho.shape == (world.n_robots, world.n_loads):
        idle = np.maximum(1.0 - np.sum(rho, axis=1, keepdims=True), 0.0)
        rho = np.column_stack([rho, idle])
    if rho.shape != (world.n_robots, world.n_loads + 1):
        raise ValueError("rho has invalid shape")
    masked = rho.copy()
    masked[:, : world.n_loads] = np.where(
        world.compatibility,
        masked[:, : world.n_loads],
        -np.inf,
    )
    return np.argmax(masked, axis=1).astype(int)


def quota_aware_seed(
    world: QuotaWorld,
    rho: np.ndarray | None,
    *,
    base_assignment: np.ndarray | None = None,
    tolerance: float = 1.0e-9,
) -> np.ndarray:
    """Create the common atomic seed without using the hidden witness."""

    n, k = world.n_robots, world.n_loads
    if rho is None:
        scores = -world.normalized_costs
    else:
        array = np.asarray(rho, dtype=float)
        if array.shape == (n, k + 1):
            array = array[:, :k]
        if array.shape != (n, k):
            raise ValueError("rho has invalid shape")
        scores = array - 1.0e-6 * world.normalized_costs
    if base_assignment is None:
        assignment = np.full(n, k, dtype=int)
    else:
        assignment = np.asarray(base_assignment, dtype=int).copy()
        invalid = (assignment < 0) | (assignment > k)
        assignment[invalid] = k
        assigned = assignment < k
        incompatible = assigned & ~world.compatibility[np.arange(n), np.minimum(assignment, k - 1)]
        assignment[incompatible] = k
    capacity = capacities_by_load(assignment, world.capacities, k)

    # First enforce upper quotas by evicting expensive or weakly supported robots.
    for load in range(k):
        while capacity[load] > world.upper_quotas[load] + tolerance:
            members = np.flatnonzero(assignment == load)
            if members.size == 0:
                break
            removable = sorted(
                map(int, members),
                key=lambda robot: (
                    scores[robot, load],
                    -world.distances_m[robot, load],
                    robot,
                ),
            )
            robot = removable[0]
            assignment[robot] = k
            capacity[load] -= world.capacities[robot]

    # Fill the most severe normalized deficit first.
    for _ in range(k * max(n, 1)):
        deficit = np.maximum(world.lower_quotas - capacity, 0.0)
        if np.max(deficit, initial=0.0) <= tolerance:
            break
        ratios = deficit / np.maximum(world.lower_quotas, tolerance)
        load = int(np.argmax(ratios))
        candidates = [
            int(robot)
            for robot in np.flatnonzero(assignment == k)
            if world.compatibility[robot, load]
            and capacity[load] + world.capacities[robot]
            <= world.upper_quotas[load] + tolerance
        ]
        if not candidates:
            # Recovery may need a chain through another load.
            break
        candidates.sort(
            key=lambda robot: (
                -scores[robot, load],
                world.distances_m[robot, load],
                robot,
            )
        )
        robot = candidates[0]
        assignment[robot] = load
        capacity[load] += world.capacities[robot]
    return assignment


def _prune_upper_excess(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    tolerance: float,
) -> np.ndarray:
    result = np.asarray(assignment, dtype=int).copy()
    k = world.n_loads
    capacity = capacities_by_load(result, world.capacities, k)
    for load in range(k):
        safety = 0
        while capacity[load] > world.upper_quotas[load] + tolerance:
            safety += 1
            if safety > world.n_robots:
                break
            members = list(map(int, np.flatnonzero(result == load)))
            if not members:
                break
            members.sort(
                key=lambda robot: (
                    # Prefer an eviction that preserves the lower quota.
                    capacity[load] - world.capacities[robot]
                    < world.lower_quotas[load] - tolerance,
                    -world.distances_m[robot, load],
                    world.capacities[robot],
                    robot,
                )
            )
            robot = members[0]
            result[robot] = k
            capacity[load] -= world.capacities[robot]
    return result


def _augmentation_for_target(
    world: QuotaWorld,
    assignment: np.ndarray,
    target: int,
    *,
    max_chain_length: int,
    max_nodes: int,
    candidates_per_load: int,
    tolerance: float,
    deadline: float | None = None,
) -> tuple[np.ndarray | None, tuple[tuple[int, int, int], ...], int, bool]:
    """Find one shortest augmenting chain that repairs ``target``.

    A state may move a deficit through previously feasible loads, but the
    terminal state must restore every load that was feasible at the root.
    Other pre-existing deficits are left for subsequent augmentations.
    """

    root = np.asarray(assignment, dtype=int)
    k = world.n_loads
    root_capacity = capacities_by_load(root, world.capacities, k)
    protected = {
        load
        for load in range(k)
        if root_capacity[load] >= world.lower_quotas[load] - tolerance
        and root_capacity[load] <= world.upper_quotas[load] + tolerance
    }
    counter = 0
    heap: list[
        tuple[
            int,
            float,
            int,
            tuple[int, ...],
            tuple[tuple[int, int, int], ...],
            frozenset[int],
        ]
    ] = []
    root_tuple = tuple(map(int, root))
    heapq.heappush(heap, (0, 0.0, counter, root_tuple, tuple(), frozenset()))
    best_depth: dict[tuple[int, ...], int] = {root_tuple: 0}
    nodes = 0

    while heap and nodes < max_nodes:
        if deadline is not None and time.perf_counter() >= deadline:
            return None, tuple(), nodes, True
        depth, delta_cost, _, state_tuple, path, moved = heapq.heappop(heap)
        nodes += 1
        state = np.asarray(state_tuple, dtype=int)
        capacity = capacities_by_load(state, world.capacities, k)
        target_fixed = capacity[target] >= world.lower_quotas[target] - tolerance
        protected_fixed = all(
            capacity[load] >= world.lower_quotas[load] - tolerance
            and capacity[load] <= world.upper_quotas[load] + tolerance
            for load in protected
        )
        if target_fixed and protected_fixed:
            return state, path, nodes, False
        if depth >= max_chain_length:
            continue

        deficits = [
            load
            for load in ({target} | protected)
            if capacity[load] < world.lower_quotas[load] - tolerance
        ]
        if not deficits:
            continue
        deficits.sort(
            key=lambda load: (
                -(world.lower_quotas[load] - capacity[load])
                / max(world.lower_quotas[load], tolerance),
                load,
            )
        )
        destination = int(deficits[0])
        candidate_robots: list[tuple[float, int]] = []
        for robot in range(world.n_robots):
            if robot in moved or state[robot] == destination:
                continue
            if not world.compatibility[robot, destination]:
                continue
            if (
                capacity[destination] + world.capacities[robot]
                > world.upper_quotas[destination] + tolerance
            ):
                continue
            source = int(state[robot])
            old_cost = (
                world.distances_m[robot, source] if source < k else 0.0
            )
            increment = float(world.distances_m[robot, destination] - old_cost)
            candidate_robots.append((increment, robot))
        candidate_robots.sort(key=lambda item: (item[0], item[1]))
        for increment, robot in candidate_robots[:candidates_per_load]:
            candidate = state.copy()
            source = int(candidate[robot])
            candidate[robot] = destination
            key = tuple(map(int, candidate))
            next_depth = depth + 1
            if best_depth.get(key, max_chain_length + 1) <= next_depth:
                continue
            best_depth[key] = next_depth
            counter += 1
            heapq.heappush(
                heap,
                (
                    next_depth,
                    delta_cost + increment,
                    counter,
                    key,
                    path + ((robot, source, destination),),
                    moved | {robot},
                ),
            )
    return None, tuple(), nodes, False


def _compress_feasible_assignment(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    tolerance: float,
) -> np.ndarray:
    result = np.asarray(assignment, dtype=int).copy()
    capacity = capacities_by_load(result, world.capacities, world.n_loads)
    for load in range(world.n_loads):
        members = sorted(
            map(int, np.flatnonzero(result == load)),
            key=lambda robot: (-world.distances_m[robot, load], robot),
        )
        for robot in members:
            if (
                capacity[load] - world.capacities[robot]
                >= world.lower_quotas[load] - tolerance
            ):
                result[robot] = world.idle_index
                capacity[load] -= world.capacities[robot]
    return result


def _local_exchange(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    tolerance: float,
    max_passes: int = 2,
) -> np.ndarray:
    """Bounded deterministic distance-improving 1-for-1 exchange."""

    result = np.asarray(assignment, dtype=int).copy()
    for _ in range(max(0, int(max_passes))):
        improved = False
        base_cost = assignment_distance(world, result)
        for left in range(world.n_robots):
            for right in range(left + 1, world.n_robots):
                left_load, right_load = int(result[left]), int(result[right])
                if left_load == right_load:
                    continue
                if right_load < world.n_loads and not world.compatibility[left, right_load]:
                    continue
                if left_load < world.n_loads and not world.compatibility[right, left_load]:
                    continue
                candidate = result.copy()
                candidate[left], candidate[right] = right_load, left_load
                if not evaluate_assignment(world, candidate, tolerance=tolerance)["feasible"]:
                    continue
                candidate_cost = assignment_distance(world, candidate)
                if candidate_cost < base_cost - tolerance:
                    result = candidate
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return result


def recover_assignment(
    world: QuotaWorld,
    initial_assignment: np.ndarray,
    options: Mapping[str, Any],
    *,
    previous_assignment: np.ndarray | None = None,
    max_chain_length_override: int | None = None,
) -> RecoveryResult:
    """Common bounded augmenting recovery for lower and upper quotas."""

    started = time.perf_counter()
    tolerance = 1.0e-9
    original = np.asarray(initial_assignment, dtype=int).copy()
    if original.shape != (world.n_robots,):
        raise ValueError("initial_assignment has invalid shape")
    assignment = original.copy()
    invalid = (assignment < 0) | (assignment > world.idle_index)
    assignment[invalid] = world.idle_index
    active = assignment < world.n_loads
    incompatible = active & ~world.compatibility[
        np.arange(world.n_robots),
        np.minimum(assignment, world.n_loads - 1),
    ]
    assignment[incompatible] = world.idle_index
    cost_before = assignment_distance(world, assignment)
    assignment = _prune_upper_excess(world, assignment, tolerance=tolerance)
    max_chain_length = (
        int(max_chain_length_override)
        if max_chain_length_override is not None
        else int(options["max_chain_length"])
    )
    maximum_nodes = int(options["max_nodes_per_augmentation"])
    deadline = started + float(options.get("max_wall_time_s", math.inf))
    candidates = int(options["candidates_per_load"])
    nodes = 0
    chain_lengths: list[int] = []
    repaired_loads = 0
    failure_reason = "none"

    for _ in range(world.n_loads * 2):
        capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
        deficits = np.maximum(world.lower_quotas - capacity, 0.0)
        if np.max(deficits, initial=0.0) <= tolerance:
            break
        target = int(np.argmax(deficits / np.maximum(world.lower_quotas, tolerance)))
        candidate, path, expanded, timed_out = _augmentation_for_target(
            world,
            assignment,
            target,
            max_chain_length=max_chain_length,
            max_nodes=maximum_nodes,
            candidates_per_load=candidates,
            tolerance=tolerance,
            deadline=deadline,
        )
        nodes += expanded
        if candidate is None:
            failure_reason = (
                "wall_time_limit"
                if timed_out
                else "no_augmenting_path_within_limits"
            )
            break
        assignment = candidate
        chain_lengths.append(len(path))
        repaired_loads += 1

    if bool(options.get("compress", True)):
        assignment = _compress_feasible_assignment(
            world,
            assignment,
            tolerance=tolerance,
        )
    metrics = evaluate_assignment(
        world,
        assignment,
        previous_assignment=previous_assignment,
        tolerance=tolerance,
    )
    if metrics["feasible"] and bool(options.get("local_exchange", True)):
        assignment = _local_exchange(
            world,
            assignment,
            tolerance=tolerance,
            max_passes=int(options.get("local_exchange_max_passes", 2)),
        )
        metrics = evaluate_assignment(
            world,
            assignment,
            previous_assignment=previous_assignment,
            tolerance=tolerance,
        )
    capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
    residual_deficits = int(np.sum(capacity < world.lower_quotas - tolerance))
    residual_excess = int(np.sum(capacity > world.upper_quotas + tolerance))
    success = bool(metrics["feasible"])
    if success:
        failure_reason = "none"
    elif failure_reason == "none":
        failure_reason = "residual_quota_violation"
    return RecoveryResult(
        assignment=assignment,
        success=success,
        failure_reason=failure_reason,
        runtime_s=float(time.perf_counter() - started),
        chain_lengths=tuple(chain_lengths),
        nodes_expanded=nodes,
        robots_reassigned=int(np.sum(assignment != original)),
        cost_before_m=cost_before,
        cost_after_m=assignment_distance(world, assignment),
        loads_repaired=repaired_loads,
        residual_deficit_loads=residual_deficits,
        residual_excess_loads=residual_excess,
        residual_no_path=bool(not success and failure_reason.startswith("no_augmenting")),
    )


def solve_milp_repair(
    world: QuotaWorld,
    initial_assignment: np.ndarray,
    *,
    recourse_weight: float = 1.0e-6,
    time_limit_s: float = 60.0,
) -> RecoveryResult:
    """Central repair oracle with lexicographic-like distance/recourse cost."""

    started = time.perf_counter()
    initial = np.asarray(initial_assignment, dtype=int)
    n, k = world.n_robots, world.n_loads
    recourse = np.ones((n, k), dtype=float)
    valid = initial < k
    recourse[np.flatnonzero(valid), initial[valid]] = 0.0
    objective = world.distances_m + recourse_weight * recourse
    matrix = _linear_constraint_matrix(world)
    try:
        result = milp(
            c=objective.ravel(),
            integrality=np.ones(n * k, dtype=np.int8),
            bounds=_variable_bounds(world),
            constraints=LinearConstraint(
                matrix,
                np.r_[np.full(n, -np.inf), world.lower_quotas],
                np.r_[np.ones(n), world.upper_quotas],
            ),
            options={"time_limit": float(time_limit_s), "mip_rel_gap": 0.0},
        )
        if result.x is None:
            raise RuntimeError(str(result.message))
        values = np.asarray(result.x, dtype=float).reshape(n, k)
        assignment = np.full(n, k, dtype=int)
        selected = np.max(values, axis=1) > 0.5
        assignment[selected] = np.argmax(values[selected], axis=1)
        metrics = evaluate_assignment(world, assignment)
        return RecoveryResult(
            assignment=assignment,
            success=bool(metrics["feasible"]),
            failure_reason="none" if metrics["feasible"] else "milp_invalid_incumbent",
            runtime_s=float(time.perf_counter() - started),
            chain_lengths=tuple(),
            nodes_expanded=int(getattr(result, "mip_node_count", 0) or 0),
            robots_reassigned=int(np.sum(assignment != initial)),
            cost_before_m=assignment_distance(world, initial),
            cost_after_m=assignment_distance(world, assignment),
            loads_repaired=int(
                np.sum(
                    capacities_by_load(initial, world.capacities, k)
                    < world.lower_quotas - 1.0e-9
                )
            ),
            residual_deficit_loads=0 if metrics["feasible"] else world.n_loads,
            residual_excess_loads=0 if metrics["feasible"] else world.n_loads,
            residual_no_path=False,
        )
    except Exception as exc:
        return RecoveryResult(
            assignment=initial.copy(),
            success=False,
            failure_reason=f"milp_repair_error:{exc!r}",
            runtime_s=float(time.perf_counter() - started),
            chain_lengths=tuple(),
            nodes_expanded=0,
            robots_reassigned=0,
            cost_before_m=assignment_distance(world, initial),
            cost_after_m=assignment_distance(world, initial),
            loads_repaired=0,
            residual_deficit_loads=int(
                np.sum(
                    capacities_by_load(initial, world.capacities, k)
                    < world.lower_quotas - 1.0e-9
                )
            ),
            residual_excess_loads=int(
                np.sum(
                    capacities_by_load(initial, world.capacities, k)
                    > world.upper_quotas + 1.0e-9
                )
            ),
            residual_no_path=False,
        )


def _metropolis_matrix(graph: QuotaGraph) -> np.ndarray:
    adjacency = graph.adjacency.astype(float)
    degrees = adjacency.sum(axis=1)
    weights = np.zeros_like(adjacency)
    rows, columns = np.nonzero(adjacency)
    for row, column in zip(rows, columns, strict=True):
        weights[row, column] = 1.0 / (1.0 + max(degrees[row], degrees[column]))
    weights[np.diag_indices_from(weights)] = 1.0 - weights.sum(axis=1)
    return weights


def _initial_rho(world: QuotaWorld) -> np.ndarray:
    rho = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    valid = np.column_stack(
        [world.compatibility, np.ones(world.n_robots, dtype=bool)]
    )
    rho[valid] = 1.0
    rho /= rho.sum(axis=1, keepdims=True)
    return rho


def _masked_softmax(values: np.ndarray, valid: np.ndarray, temperature: float) -> np.ndarray:
    temperature = max(float(temperature), 1.0e-9)
    masked = np.where(valid, values, -np.inf)
    maximum = np.max(masked, axis=1, keepdims=True)
    exponential = np.exp(np.clip((masked - maximum) / temperature, -745.0, 0.0))
    exponential = np.where(valid, exponential, 0.0)
    return exponential / np.maximum(exponential.sum(axis=1, keepdims=True), 1.0e-300)


def _project_simplex(vector: np.ndarray) -> np.ndarray:
    """Euclidean projection onto the probability simplex."""

    values = np.asarray(vector, dtype=float)
    if values.size == 1:
        return np.ones(1, dtype=float)
    ordered = np.sort(values)[::-1]
    cumulative = np.cumsum(ordered)
    indexes = np.arange(1, values.size + 1)
    positive = ordered - (cumulative - 1.0) / indexes > 0.0
    rho = int(np.flatnonzero(positive)[-1])
    threshold = (cumulative[rho] - 1.0) / float(rho + 1)
    return np.maximum(values - threshold, 0.0)


def _revision_update(
    protocol: str,
    rho: np.ndarray,
    utilities: np.ndarray,
    valid: np.ndarray,
    *,
    eta: float,
    temperature: float,
) -> np.ndarray:
    n = rho.shape[0]
    result = np.zeros_like(rho)
    key = protocol.lower()
    if key in {"replicator", "qpg-replicator"}:
        centered = utilities - np.max(np.where(valid, utilities, -np.inf), axis=1, keepdims=True)
        weights = rho * np.exp(np.clip(float(eta) * centered, -100.0, 0.0))
        weights = np.where(valid, weights, 0.0)
        result = weights / np.maximum(weights.sum(axis=1, keepdims=True), 1.0e-300)
    elif key in {"logit", "qpg-logit"}:
        target = _masked_softmax(utilities, valid, temperature)
        result = (1.0 - float(eta)) * rho + float(eta) * target
    elif key in {"smith", "qpg-smith"}:
        for robot in range(n):
            indexes = np.flatnonzero(valid[robot])
            state = rho[robot, indexes]
            payoff = utilities[robot, indexes]
            flow = np.zeros(indexes.size, dtype=float)
            for origin in range(indexes.size):
                gains = np.maximum(payoff - payoff[origin], 0.0)
                flow += state[origin] * gains
                flow[origin] -= state[origin] * float(np.sum(gains))
            result[robot, indexes] = _project_simplex(state + float(eta) * flow)
    elif key in {"bnn", "qpg-bnn"}:
        mean = np.sum(rho * np.where(valid, utilities, 0.0), axis=1, keepdims=True)
        excess = np.maximum(np.where(valid, utilities - mean, -np.inf), 0.0)
        target = excess / np.maximum(excess.sum(axis=1, keepdims=True), 1.0e-300)
        no_excess = np.sum(excess, axis=1) <= 1.0e-15
        target[no_excess] = rho[no_excess]
        result = (1.0 - float(eta)) * rho + float(eta) * target
    elif key in {"projection", "qpg-projection"}:
        for robot in range(n):
            indexes = np.flatnonzero(valid[robot])
            payoff = utilities[robot, indexes]
            centered = payoff - float(np.mean(payoff))
            result[robot, indexes] = _project_simplex(
                rho[robot, indexes] + float(eta) * centered
            )
    elif key in {"best_response", "qpg-damped-bestresponse"}:
        target = np.zeros_like(rho)
        masked = np.where(valid, utilities, -np.inf)
        best = np.argmax(masked, axis=1)
        target[np.arange(n), best] = 1.0
        result = (1.0 - float(eta)) * rho + float(eta) * target
    else:
        raise ValueError(f"unknown revision protocol: {protocol}")
    result = np.where(valid, np.maximum(result, 0.0), 0.0)
    result /= np.maximum(result.sum(axis=1, keepdims=True), 1.0e-300)
    return result


def _market_message_increment(
    world: QuotaWorld,
    graph: QuotaGraph,
    message_config: Mapping[str, Any],
) -> tuple[int, int, int, int]:
    route_hops = int(np.sum(graph.market_route_hops[world.compatibility.T]))
    packets = 2 * route_hops
    spec = message_config["routed_market"]
    price_scalars = int(spec["price_float64"])
    intention_scalars = int(spec["intention_float64"])
    metadata = int(spec["metadata_int64"])
    scalars = route_hops * (price_scalars + intention_scalars)
    bytes_total = route_hops * (
        (price_scalars + intention_scalars) * FLOAT64_BYTES
        + 2 * metadata * INT64_BYTES
    )
    return packets, scalars, bytes_total, route_hops


def run_continuous_method(
    world: QuotaWorld,
    graph: QuotaGraph,
    method: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    initial_rho: np.ndarray | None = None,
) -> AlgorithmResult:
    """Run DRD-simple or local-market QPG under common stopping rules."""

    method_map = {
        "DRD-simple-Replicator": ("drd", "replicator"),
        "DRD-simple-Logit": ("drd", "logit"),
        "QPG-Replicator-AR": ("qpg", "replicator"),
        "QPG-Logit-AR": ("qpg", "logit"),
        "QPG-Replicator": ("qpg", "replicator"),
        "QPG-Smith": ("qpg", "smith"),
        "QPG-BNN": ("qpg", "bnn"),
        "QPG-Logit": ("qpg", "logit"),
        "QPG-Projection": ("qpg", "projection"),
        "QPG-Damped-BestResponse": ("qpg", "best_response"),
    }
    if method not in method_map:
        raise ValueError(f"unsupported continuous method: {method}")
    architecture, protocol = method_map[method]
    budget = config["budgets"][stage]
    hard_maximum_rounds = int(budget["max_rounds"])
    guard = int(
        config["budgets"].get("evaluation_round_guard", {}).get(
            stage,
            hard_maximum_rounds,
        )
    )
    maximum_rounds = min(hard_maximum_rounds, guard)
    maximum_wall = min(
        float(budget["max_wall_time_s"]),
        float(
            config["budgets"].get("evaluation_wall_guard_s", {}).get(
                stage,
                budget["max_wall_time_s"],
            )
        ),
    )
    maximum_payoffs = int(budget["max_payoff_evaluations"])
    dwell_required = int(config["budgets"]["dwell_rounds"])
    trace_stride = int(config["budgets"]["trace_stride"])
    eta = float(parameters.get("eta", 0.15))
    alpha_price = float(parameters.get("alpha_price", 0.08))
    temperature_initial = float(parameters.get("temperature_initial", 0.15))
    temperature_minimum = float(parameters.get("temperature_min", 0.005))
    annealing = float(parameters.get("annealing", 0.995))
    tau = float(config["potential"]["entropy_tau"])
    state_tolerance = float(parameters.get("state_tolerance", 1.0e-5))
    quota_tolerance = float(parameters.get("quota_tolerance", 1.0e-5))
    price_tolerance = float(parameters.get("price_tolerance", 1.0e-5))
    consensus_tolerance = float(parameters.get("consensus_tolerance", 1.0e-4))
    valid = np.column_stack(
        [world.compatibility, np.ones(world.n_robots, dtype=bool)]
    )
    rho = _initial_rho(world) if initial_rho is None else np.asarray(initial_rho, dtype=float).copy()
    if rho.shape != (world.n_robots, world.n_loads + 1):
        raise ValueError("initial_rho has invalid shape")
    rho = np.where(valid, np.maximum(rho, 0.0), 0.0)
    rho /= np.maximum(rho.sum(axis=1, keepdims=True), 1.0e-300)
    lambda_minus = np.zeros(world.n_loads, dtype=float)
    lambda_plus = np.zeros(world.n_loads, dtype=float)
    tracker = world.capacities[:, None] * rho[:, : world.n_loads]
    weights = _metropolis_matrix(graph)
    traces: list[dict[str, Any]] = []
    message_rows: list[dict[str, Any]] = []
    logical_rounds = 0
    agent_updates = 0
    payoff_evaluations = 0
    packets = scalars = payload_bytes = 0
    first_feasible_round: int | None = None
    bytes_to_first_feasible: int | None = None
    convergence_round: int | None = None
    bytes_to_convergence: int | None = None
    dwell = 0
    converged = False
    censoring_reason = (
        "evaluation_round_guard"
        if maximum_rounds < hard_maximum_rounds
        else "max_rounds"
    )
    terminal_state = terminal_quota = terminal_price = terminal_consensus = math.inf
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0

    for round_index in range(maximum_rounds):
        if time.perf_counter() - started_wall >= maximum_wall:
            censoring_reason = "wall_time"
            break
        if payoff_evaluations + world.n_robots > maximum_payoffs:
            censoring_reason = "payoff_budget"
            break
        temperature = max(
            temperature_minimum,
            temperature_initial * (annealing**round_index),
        )
        actual_capacity = np.einsum(
            "i,ik->k",
            world.capacities,
            rho[:, : world.n_loads],
        )
        if architecture == "drd":
            local_capacity = world.n_robots * tracker
            deficit_pressure = float(config["potential"]["rho_minus"]) * np.maximum(
                world.lower_quotas[None, :] - local_capacity,
                0.0,
            )
            excess_pressure = float(config["potential"]["rho_plus"]) * np.maximum(
                local_capacity - world.upper_quotas[None, :],
                0.0,
            )
            load_utilities = (
                -world.normalized_costs
                + world.capacities[:, None] * (deficit_pressure - excess_pressure)
            )
        else:
            load_utilities = (
                -world.normalized_costs
                + world.capacities[:, None]
                * (lambda_minus[None, :] - lambda_plus[None, :])
            )
        utilities = np.column_stack([load_utilities, np.zeros(world.n_robots)])
        if protocol == "replicator":
            # The entropy term belongs to the continuous optimizer.
            utilities -= tau * (1.0 + np.log(np.maximum(rho, 1.0e-300)))
        candidate = _revision_update(
            protocol,
            rho,
            utilities,
            valid,
            eta=eta,
            temperature=temperature,
        )
        candidate_capacity = np.einsum(
            "i,ik->k",
            world.capacities,
            candidate[:, : world.n_loads],
        )
        previous_minus = lambda_minus.copy()
        previous_plus = lambda_plus.copy()
        if architecture == "qpg":
            lambda_minus = np.maximum(
                lambda_minus + alpha_price * (world.lower_quotas - candidate_capacity),
                0.0,
            )
            lambda_plus = np.maximum(
                lambda_plus + alpha_price * (candidate_capacity - world.upper_quotas),
                0.0,
            )
            packet_increment, scalar_increment, byte_increment, route_hops = (
                _market_message_increment(world, graph, config["messages"])
            )
            consensus_residual = 0.0
            message_rows.append(
                {
                    "logical_round": round_index + 1,
                    "message_kind": "routed_market_roundtrip",
                    "route_hops": route_hops,
                    "packets": packet_increment,
                    "scalars": scalar_increment,
                    "bytes": byte_increment,
                }
            )
        else:
            signal = world.capacities[:, None] * candidate[:, : world.n_loads]
            mixed = weights @ tracker
            next_tracker = mixed + signal - (
                world.capacities[:, None] * rho[:, : world.n_loads]
            )
            tracker = next_tracker
            estimates = world.n_robots * tracker
            consensus_residual = float(
                np.linalg.norm(estimates - candidate_capacity[None, :])
                / (1.0 + np.linalg.norm(candidate_capacity))
            )
            packet_increment = 2 * graph.edges
            scalar_increment = packet_increment * world.n_loads
            byte_increment = (
                scalar_increment * FLOAT64_BYTES + packet_increment * INT64_BYTES
            )
            message_rows.append(
                {
                    "logical_round": round_index + 1,
                    "message_kind": "dynamic_average_consensus",
                    "route_hops": graph.edges,
                    "packets": packet_increment,
                    "scalars": scalar_increment,
                    "bytes": byte_increment,
                }
            )
        packets += packet_increment
        scalars += scalar_increment
        payload_bytes += byte_increment
        payoff_evaluations += world.n_robots
        agent_updates += world.n_robots
        logical_rounds = round_index + 1
        terminal_state = float(
            np.linalg.norm(candidate - rho) / (1.0 + np.linalg.norm(rho))
        )
        deficit = np.maximum(world.lower_quotas - candidate_capacity, 0.0)
        excess = np.maximum(candidate_capacity - world.upper_quotas, 0.0)
        terminal_quota = float(
            math.hypot(np.linalg.norm(deficit), np.linalg.norm(excess))
            / (1.0 + np.linalg.norm(world.lower_quotas))
        )
        terminal_price = (
            float(
                math.hypot(
                    np.linalg.norm(lambda_minus - previous_minus),
                    np.linalg.norm(lambda_plus - previous_plus),
                )
                / (
                    1.0
                    + math.hypot(
                        np.linalg.norm(previous_minus),
                        np.linalg.norm(previous_plus),
                    )
                )
            )
            if architecture == "qpg"
            else 0.0
        )
        terminal_consensus = consensus_residual
        continuous_feasible = bool(
            np.max(deficit, initial=0.0) <= quota_tolerance
            and np.max(excess, initial=0.0) <= quota_tolerance
        )
        if continuous_feasible and first_feasible_round is None:
            first_feasible_round = logical_rounds
            bytes_to_first_feasible = payload_bytes
        meets = bool(
            terminal_state <= state_tolerance
            and terminal_quota <= quota_tolerance
            and terminal_price <= price_tolerance
            and terminal_consensus <= consensus_tolerance
        )
        dwell = dwell + 1 if meets else 0
        if (
            round_index % trace_stride == 0
            or meets
            or round_index + 1 == maximum_rounds
        ):
            traces.append(
                {
                    "logical_round": logical_rounds,
                    "temperature": temperature,
                    "state_residual": terminal_state,
                    "quota_residual": terminal_quota,
                    "price_residual": terminal_price,
                    "consensus_residual": terminal_consensus,
                    "lower_violation": float(np.sum(deficit)),
                    "upper_violation": float(np.sum(excess)),
                    "packets_total": packets,
                    "payload_bytes_total": payload_bytes,
                    "dwell": dwell,
                }
            )
        rho = candidate
        invariants = continuous_metrics(world, rho)
        if not invariants["finite"]:
            censoring_reason = "numerical_failure"
            break
        if (
            invariants["simplex_violation"] > 1.0e-8
            or invariants["nonnegativity_violation"] > 1.0e-10
            or invariants["mask_violation"] > 1.0e-10
        ):
            censoring_reason = "invalid_state"
            break
        if dwell >= dwell_required:
            converged = True
            censoring_reason = "none"
            convergence_round = logical_rounds - dwell_required + 1
            bytes_to_convergence = payload_bytes
            break

    wall_time = float(time.perf_counter() - started_wall)
    cpu_time = float(time.process_time() - started_cpu)
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    invariants = continuous_metrics(world, rho)
    return AlgorithmResult(
        method=method,
        result_family="continuous_intention",
        rho=rho,
        assignment=None,
        lambda_minus=lambda_minus,
        lambda_plus=lambda_plus,
        converged=converged,
        censored=not converged,
        censoring_reason=censoring_reason,
        logical_rounds=logical_rounds,
        agent_updates=agent_updates,
        payoff_evaluations=payoff_evaluations,
        pairwise_evaluations=0,
        swaps=0,
        accepted_moves=0,
        packets_total=packets,
        scalar_transmissions_total=scalars,
        payload_bytes_total=payload_bytes,
        bytes_to_first_feasible=bytes_to_first_feasible,
        bytes_to_convergence=bytes_to_convergence,
        first_feasible_round=first_feasible_round,
        convergence_round=convergence_round,
        wall_time_s=wall_time,
        cpu_time_s=cpu_time,
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0**2)),
        terminal_state_residual=terminal_state,
        terminal_quota_residual=terminal_quota,
        terminal_price_residual=terminal_price,
        terminal_consensus_residual=terminal_consensus,
        simplex_violation=float(invariants["simplex_violation"]),
        mask_violation=float(invariants["mask_violation"]),
        finite_state=bool(invariants["finite"]),
        traces=tuple(traces),
        message_rows=tuple(message_rows),
    )


def _atomic_result(
    *,
    method: str,
    assignment: np.ndarray,
    world: QuotaWorld,
    lambda_minus: np.ndarray | None,
    lambda_plus: np.ndarray | None,
    converged: bool,
    censoring_reason: str,
    logical_rounds: int,
    agent_updates: int,
    payoff_evaluations: int,
    pairwise_evaluations: int,
    swaps: int,
    accepted_moves: int,
    packets: int,
    scalars: int,
    payload_bytes: int,
    bytes_to_first_feasible: int | None,
    bytes_to_convergence: int | None,
    first_feasible_round: int | None,
    convergence_round: int | None,
    wall_time: float,
    cpu_time: float,
    peak_memory_mb: float,
    traces: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> AlgorithmResult:
    metrics = evaluate_assignment(world, assignment)
    return AlgorithmResult(
        method=method,
        result_family="atomic",
        rho=None,
        assignment=assignment,
        lambda_minus=np.zeros(world.n_loads)
        if lambda_minus is None
        else np.asarray(lambda_minus, dtype=float),
        lambda_plus=np.zeros(world.n_loads)
        if lambda_plus is None
        else np.asarray(lambda_plus, dtype=float),
        converged=converged,
        censored=not converged,
        censoring_reason=censoring_reason,
        logical_rounds=logical_rounds,
        agent_updates=agent_updates,
        payoff_evaluations=payoff_evaluations,
        pairwise_evaluations=pairwise_evaluations,
        swaps=swaps,
        accepted_moves=accepted_moves,
        packets_total=packets,
        scalar_transmissions_total=scalars,
        payload_bytes_total=payload_bytes,
        bytes_to_first_feasible=bytes_to_first_feasible,
        bytes_to_convergence=bytes_to_convergence,
        first_feasible_round=first_feasible_round,
        convergence_round=convergence_round,
        wall_time_s=wall_time,
        cpu_time_s=cpu_time,
        peak_memory_mb=peak_memory_mb,
        terminal_state_residual=0.0 if converged else 1.0,
        terminal_quota_residual=float(
            math.hypot(metrics["deficit_total"], metrics["excess_upper_total"])
            / (1.0 + np.linalg.norm(world.lower_quotas))
        ),
        terminal_price_residual=0.0,
        terminal_consensus_residual=0.0,
        simplex_violation=0.0,
        mask_violation=0.0 if metrics["compatible"] else 1.0,
        finite_state=True,
        traces=tuple(traces),
        message_rows=tuple(messages),
    )


def run_capacity_cbba(
    world: QuotaWorld,
    graph: QuotaGraph,
    config: Mapping[str, Any],
    *,
    stage: str,
    initial_assignment: np.ndarray | None = None,
    previous_assignment: np.ndarray | None = None,
) -> AlgorithmResult:
    """Bundle-one, multi-winner Capacity-CBBA adaptation.

    Bids are exact marginal improvements of the common social potential.
    They are routed to load markets; at most one winner per load is committed
    per epoch.  This is not canonical one-winner CBBA.
    """

    budget = config["budgets"][stage]
    maximum_rounds = int(budget["max_rounds"])
    maximum_wall = min(
        float(budget["max_wall_time_s"]),
        float(
            config["budgets"].get("evaluation_wall_guard_s", {}).get(
                stage,
                budget["max_wall_time_s"],
            )
        ),
    )
    improvement = float(config["potential"]["improvement_epsilon"])
    rho_minus = float(config["potential"]["rho_minus"])
    rho_plus = float(config["potential"]["rho_plus"])
    gamma_switch = float(config["potential"]["gamma_switch"])
    assignment = (
        np.full(world.n_robots, world.idle_index, dtype=int)
        if initial_assignment is None
        else np.asarray(initial_assignment, dtype=int).copy()
    )
    packets = scalars = payload_bytes = 0
    payoff_evaluations = accepted_moves = 0
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    first_feasible_round = bytes_to_first_feasible = None
    converged = False
    censoring_reason = "max_rounds"
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    logical_rounds = 0

    for epoch in range(maximum_rounds):
        if time.perf_counter() - started_wall >= maximum_wall:
            censoring_reason = "wall_time"
            break
        proposals: list[tuple[float, int, int]] = []
        for robot in range(world.n_robots):
            best_value = improvement
            best_load = int(assignment[robot])
            for load in range(world.n_loads):
                if not world.compatibility[robot, load] or load == assignment[robot]:
                    continue
                value = marginal_move_value(
                    world,
                    assignment,
                    robot,
                    load,
                    rho_minus=rho_minus,
                    rho_plus=rho_plus,
                    gamma_switch=gamma_switch,
                    previous_assignment=previous_assignment,
                )
                payoff_evaluations += 1
                if value > best_value + improvement or (
                    abs(value - best_value) <= improvement and load < best_load
                ):
                    best_value, best_load = value, load
            if best_load != assignment[robot]:
                proposals.append((best_value, robot, best_load))
                hops = int(graph.market_route_hops[best_load, robot])
                proposal_packets = 2 * hops
                spec = config["messages"]["bid_record"]
                proposal_scalars = hops * int(spec["float64"])
                proposal_bytes = hops * (
                    int(spec["float64"]) * FLOAT64_BYTES
                    + int(spec["int64"]) * INT64_BYTES
                )
                packets += proposal_packets
                scalars += proposal_scalars
                payload_bytes += proposal_bytes
                messages.append(
                    {
                        "logical_round": epoch + 1,
                        "message_kind": "capacity_cbba_bid_roundtrip",
                        "robot": robot,
                        "load": best_load,
                        "route_hops": hops,
                        "packets": proposal_packets,
                        "scalars": proposal_scalars,
                        "bytes": proposal_bytes,
                    }
                )
        proposals.sort(key=lambda item: (-item[0], item[1], item[2]))
        winners: set[int] = set()
        changes = 0
        for _, robot, load in proposals:
            if load in winners:
                continue
            capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
            source = int(assignment[robot])
            destination_capacity = capacity[load] + world.capacities[robot]
            if source == load:
                continue
            if destination_capacity > world.upper_quotas[load] + 1.0e-9:
                continue
            value = marginal_move_value(
                world,
                assignment,
                robot,
                load,
                rho_minus=rho_minus,
                rho_plus=rho_plus,
                gamma_switch=gamma_switch,
                previous_assignment=previous_assignment,
            )
            payoff_evaluations += 1
            if value <= improvement:
                continue
            assignment[robot] = load
            winners.add(load)
            changes += 1
            accepted_moves += 1
        logical_rounds = epoch + 1
        metrics = evaluate_assignment(
            world,
            assignment,
            previous_assignment=previous_assignment,
        )
        if metrics["feasible"] and first_feasible_round is None:
            first_feasible_round = logical_rounds
            bytes_to_first_feasible = payload_bytes
        traces.append(
            {
                "logical_round": logical_rounds,
                "accepted_moves": changes,
                "feasible": metrics["feasible"],
                "deficit_total": metrics["deficit_total"],
                "excess_upper_total": metrics["excess_upper_total"],
                "distance_total_m": metrics["distance_total_m"],
                "payload_bytes_total": payload_bytes,
            }
        )
        if changes == 0:
            if metrics["feasible"]:
                converged = True
                censoring_reason = "none"
            else:
                censoring_reason = "no_positive_bid"
            break

    wall = float(time.perf_counter() - started_wall)
    cpu = float(time.process_time() - started_cpu)
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    return _atomic_result(
        method="Capacity-CBBA",
        assignment=assignment,
        world=world,
        lambda_minus=None,
        lambda_plus=None,
        converged=converged,
        censoring_reason=censoring_reason,
        logical_rounds=logical_rounds,
        agent_updates=logical_rounds * world.n_robots,
        payoff_evaluations=payoff_evaluations,
        pairwise_evaluations=0,
        swaps=0,
        accepted_moves=accepted_moves,
        packets=packets,
        scalars=scalars,
        payload_bytes=payload_bytes,
        bytes_to_first_feasible=bytes_to_first_feasible,
        bytes_to_convergence=payload_bytes if converged else None,
        first_feasible_round=first_feasible_round,
        convergence_round=logical_rounds if converged else None,
        wall_time=wall,
        cpu_time=cpu,
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0**2)),
        traces=traces,
        messages=messages,
    )


def run_weighted_grape(
    world: QuotaWorld,
    graph: QuotaGraph,
    config: Mapping[str, Any],
    *,
    stage: str,
    pairwise: bool,
    seed: int,
    initial_assignment: np.ndarray | None = None,
    previous_assignment: np.ndarray | None = None,
) -> AlgorithmResult:
    """Weighted scalar-capacity hedonic adaptation inspired by GRAPE."""

    method = "Weighted-Pair-GRAPE" if pairwise else "Weighted-GRAPE"
    budget = config["budgets"][stage]
    maximum_rounds = int(budget["max_rounds"])
    maximum_wall = min(
        float(budget["max_wall_time_s"]),
        float(
            config["budgets"].get("evaluation_wall_guard_s", {}).get(
                stage,
                budget["max_wall_time_s"],
            )
        ),
    )
    epsilon = float(config["potential"]["improvement_epsilon"])
    rho_minus = float(config["potential"]["rho_minus"])
    rho_plus = float(config["potential"]["rho_plus"])
    gamma_switch = float(config["potential"]["gamma_switch"])
    assignment = (
        np.full(world.n_robots, world.idle_index, dtype=int)
        if initial_assignment is None
        else np.asarray(initial_assignment, dtype=int).copy()
    )
    rng = np.random.default_rng(int(seed))
    accepted_moves = swaps = payoff_evaluations = pairwise_evaluations = 0
    packets = scalars = payload_bytes = 0
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    first_feasible_round = bytes_to_first_feasible = None
    converged = False
    censoring_reason = "max_rounds"
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    logical_rounds = 0

    for epoch in range(maximum_rounds):
        if time.perf_counter() - started_wall >= maximum_wall:
            censoring_reason = "wall_time"
            break
        changes = 0
        for robot in rng.permutation(world.n_robots):
            robot = int(robot)
            current = int(assignment[robot])
            best = current
            best_gain = epsilon
            for destination in range(world.n_loads + 1):
                if destination == current:
                    continue
                gain = marginal_move_value(
                    world,
                    assignment,
                    robot,
                    destination,
                    rho_minus=rho_minus,
                    rho_plus=rho_plus,
                    gamma_switch=gamma_switch,
                    previous_assignment=previous_assignment,
                )
                payoff_evaluations += 1
                if gain > best_gain + epsilon or (
                    abs(gain - best_gain) <= epsilon and destination < best
                ):
                    best_gain, best = gain, destination
            if best != current:
                assignment[robot] = best
                accepted_moves += 1
                changes += 1
                update_packets = max(world.n_robots - 1, 0)
                spec = config["messages"]["partition_update"]
                update_scalars = update_packets * int(spec["float64"])
                update_bytes = update_packets * (
                    int(spec["float64"]) * FLOAT64_BYTES
                    + int(spec["int64"]) * INT64_BYTES
                )
                packets += update_packets
                scalars += update_scalars
                payload_bytes += update_bytes
                messages.append(
                    {
                        "logical_round": epoch + 1,
                        "message_kind": "grape_partition_broadcast",
                        "robot": robot,
                        "load": best,
                        "route_hops": update_packets,
                        "packets": update_packets,
                        "scalars": update_scalars,
                        "bytes": update_bytes,
                    }
                )
        logical_rounds = epoch + 1
        metrics = evaluate_assignment(
            world,
            assignment,
            previous_assignment=previous_assignment,
        )
        if metrics["feasible"] and first_feasible_round is None:
            first_feasible_round = logical_rounds
            bytes_to_first_feasible = payload_bytes
        traces.append(
            {
                "logical_round": logical_rounds,
                "phase": "unilateral",
                "accepted_moves": changes,
                "feasible": metrics["feasible"],
                "deficit_total": metrics["deficit_total"],
                "excess_upper_total": metrics["excess_upper_total"],
                "distance_total_m": metrics["distance_total_m"],
                "payload_bytes_total": payload_bytes,
            }
        )
        if changes == 0:
            break

    if pairwise and time.perf_counter() - started_wall < maximum_wall:
        for pair_epoch in range(maximum_rounds):
            best_gain = epsilon
            best_pair: tuple[int, int] | None = None
            pair_timeout = False
            base = social_potential(
                world,
                assignment,
                rho_minus=rho_minus,
                rho_plus=rho_plus,
                gamma_switch=gamma_switch,
                previous_assignment=previous_assignment,
            )
            for left in range(world.n_robots):
                if time.perf_counter() - started_wall >= maximum_wall:
                    pair_timeout = True
                    break
                for right in range(left + 1, world.n_robots):
                    if assignment[left] == assignment[right]:
                        continue
                    candidate = assignment.copy()
                    candidate[left], candidate[right] = candidate[right], candidate[left]
                    if not assignment_is_compatible(world, candidate):
                        continue
                    gain = social_potential(
                        world,
                        candidate,
                        rho_minus=rho_minus,
                        rho_plus=rho_plus,
                        gamma_switch=gamma_switch,
                        previous_assignment=previous_assignment,
                    ) - base
                    pairwise_evaluations += 1
                    if gain > best_gain + epsilon:
                        best_gain = gain
                        best_pair = (left, right)
            if pair_timeout:
                censoring_reason = "wall_time"
                break
            if best_pair is None:
                break
            left, right = best_pair
            assignment[left], assignment[right] = assignment[right], assignment[left]
            swaps += 1
            accepted_moves += 2
            update_packets = 2 * max(world.n_robots - 1, 0)
            packets += update_packets
            spec = config["messages"]["partition_update"]
            update_scalars = update_packets * int(spec["float64"])
            update_bytes = update_packets * (
                int(spec["float64"]) * FLOAT64_BYTES
                + int(spec["int64"]) * INT64_BYTES
            )
            scalars += update_scalars
            payload_bytes += update_bytes
            logical_rounds += 1
            messages.append(
                {
                    "logical_round": logical_rounds,
                    "message_kind": "pair_grape_swap_broadcast",
                    "robot": left,
                    "load": int(assignment[left]),
                    "route_hops": update_packets,
                    "packets": update_packets,
                    "scalars": update_scalars,
                    "bytes": update_bytes,
                }
            )
            if time.perf_counter() - started_wall >= maximum_wall:
                censoring_reason = "wall_time"
                break

    final_metrics = evaluate_assignment(
        world,
        assignment,
        previous_assignment=previous_assignment,
    )
    if final_metrics["feasible"] and censoring_reason != "wall_time":
        converged = True
        censoring_reason = "none"
    elif censoring_reason != "wall_time":
        censoring_reason = "stable_infeasible"
    wall = float(time.perf_counter() - started_wall)
    cpu = float(time.process_time() - started_cpu)
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    return _atomic_result(
        method=method,
        assignment=assignment,
        world=world,
        lambda_minus=None,
        lambda_plus=None,
        converged=converged,
        censoring_reason=censoring_reason,
        logical_rounds=logical_rounds,
        agent_updates=logical_rounds * world.n_robots,
        payoff_evaluations=payoff_evaluations,
        pairwise_evaluations=pairwise_evaluations,
        swaps=swaps,
        accepted_moves=accepted_moves,
        packets=packets,
        scalars=scalars,
        payload_bytes=payload_bytes,
        bytes_to_first_feasible=bytes_to_first_feasible,
        bytes_to_convergence=payload_bytes if converged else None,
        first_feasible_round=first_feasible_round,
        convergence_round=logical_rounds if converged else None,
        wall_time=wall,
        cpu_time=cpu,
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0**2)),
        traces=traces,
        messages=messages,
    )


def run_atomic_quota_logit(
    world: QuotaWorld,
    graph: QuotaGraph,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    seed: int,
    initial_assignment: np.ndarray | None = None,
    previous_assignment: np.ndarray | None = None,
) -> AlgorithmResult:
    """Finite tentative/committed Logit process with local load prices."""

    budget = config["budgets"][stage]
    hard_maximum_epochs = int(budget["max_rounds"])
    maximum_epochs = min(
        hard_maximum_epochs,
        int(
            config["budgets"].get("evaluation_round_guard", {}).get(
                stage,
                hard_maximum_epochs,
            )
        ),
    )
    maximum_wall = min(
        float(budget["max_wall_time_s"]),
        float(
            config["budgets"].get("evaluation_wall_guard_s", {}).get(
                stage,
                budget["max_wall_time_s"],
            )
        ),
    )
    maximum_payoffs = int(budget["max_payoff_evaluations"])
    dwell_required = int(config["budgets"]["dwell_rounds"])
    rho_minus = float(config["potential"]["rho_minus"])
    rho_plus = float(config["potential"]["rho_plus"])
    gamma_switch = float(config["potential"]["gamma_switch"])
    eta_price = float(parameters.get("alpha_price", 0.08))
    initial_temperature = float(parameters.get("temperature_initial", 0.15))
    minimum_temperature = float(parameters.get("temperature_min", 0.005))
    annealing = float(parameters.get("annealing", 0.995))
    assignment = (
        np.full(world.n_robots, world.idle_index, dtype=int)
        if initial_assignment is None
        else np.asarray(initial_assignment, dtype=int).copy()
    )
    rng = np.random.default_rng(int(seed))
    lambda_minus = np.zeros(world.n_loads, dtype=float)
    lambda_plus = np.zeros(world.n_loads, dtype=float)
    packets = scalars = payload_bytes = 0
    payoff_evaluations = accepted_moves = 0
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    first_feasible_round = bytes_to_first_feasible = None
    convergence_round = bytes_to_convergence = None
    dwell = 0
    converged = False
    censoring_reason = (
        "evaluation_round_guard"
        if maximum_epochs < hard_maximum_epochs
        else "max_rounds"
    )
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    logical_rounds = 0

    for epoch in range(maximum_epochs):
        if time.perf_counter() - started_wall >= maximum_wall:
            censoring_reason = "wall_time"
            break
        temperature = max(minimum_temperature, initial_temperature * annealing**epoch)
        changes = 0
        for robot in rng.permutation(world.n_robots):
            if payoff_evaluations + world.n_loads + 1 > maximum_payoffs:
                censoring_reason = "payoff_budget"
                break
            robot = int(robot)
            source = int(assignment[robot])
            utilities = np.full(world.n_loads + 1, -np.inf, dtype=float)
            for destination in range(world.n_loads + 1):
                if destination < world.n_loads and not world.compatibility[robot, destination]:
                    continue
                gain = marginal_move_value(
                    world,
                    assignment,
                    robot,
                    destination,
                    rho_minus=rho_minus,
                    rho_plus=rho_plus,
                    gamma_switch=gamma_switch,
                    previous_assignment=previous_assignment,
                )
                price_adjustment = 0.0
                if destination < world.n_loads:
                    price_adjustment += world.capacities[robot] * (
                        lambda_minus[destination] - lambda_plus[destination]
                    )
                if source < world.n_loads:
                    price_adjustment -= world.capacities[robot] * (
                        lambda_minus[source] - lambda_plus[source]
                    )
                utilities[destination] = gain + price_adjustment
                payoff_evaluations += 1
            finite = np.isfinite(utilities)
            maximum = float(np.max(utilities[finite]))
            probabilities = np.zeros_like(utilities)
            probabilities[finite] = np.exp(
                np.clip((utilities[finite] - maximum) / temperature, -745.0, 0.0)
            )
            probabilities /= probabilities.sum()
            tentative = int(rng.choice(world.n_loads + 1, p=probabilities))
            if tentative == source:
                continue
            capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
            if (
                tentative < world.n_loads
                and capacity[tentative] + world.capacities[robot]
                > world.upper_quotas[tentative] + 1.0e-9
            ):
                # Tentative move is explicitly rejected; committed state is unchanged.
                continue
            assignment[robot] = tentative
            accepted_moves += 1
            changes += 1
            host_load = tentative if tentative < world.n_loads else source
            if host_load < world.n_loads:
                hops = int(graph.market_route_hops[host_load, robot])
                event_packets = 2 * hops
                event_scalars = 4 * hops
                event_bytes = event_scalars * FLOAT64_BYTES + 4 * hops * INT64_BYTES
                packets += event_packets
                scalars += event_scalars
                payload_bytes += event_bytes
                messages.append(
                    {
                        "logical_round": epoch + 1,
                        "message_kind": "atomic_logit_tentative_commit",
                        "robot": robot,
                        "load": tentative,
                        "route_hops": hops,
                        "packets": event_packets,
                        "scalars": event_scalars,
                        "bytes": event_bytes,
                    }
                )
        if censoring_reason == "payoff_budget":
            break
        capacity = capacities_by_load(assignment, world.capacities, world.n_loads)
        lambda_minus = np.maximum(
            lambda_minus + eta_price * (world.lower_quotas - capacity),
            0.0,
        )
        lambda_plus = np.maximum(
            lambda_plus + eta_price * (capacity - world.upper_quotas),
            0.0,
        )
        logical_rounds = epoch + 1
        metrics = evaluate_assignment(
            world,
            assignment,
            previous_assignment=previous_assignment,
        )
        if metrics["feasible"] and first_feasible_round is None:
            first_feasible_round = logical_rounds
            bytes_to_first_feasible = payload_bytes
        dwell = dwell + 1 if changes == 0 and metrics["feasible"] else 0
        traces.append(
            {
                "logical_round": logical_rounds,
                "temperature": temperature,
                "accepted_moves": changes,
                "dwell": dwell,
                "feasible": metrics["feasible"],
                "deficit_total": metrics["deficit_total"],
                "excess_upper_total": metrics["excess_upper_total"],
                "payload_bytes_total": payload_bytes,
            }
        )
        if dwell >= dwell_required:
            converged = True
            censoring_reason = "none"
            convergence_round = logical_rounds - dwell_required + 1
            bytes_to_convergence = payload_bytes
            break

    wall = float(time.perf_counter() - started_wall)
    cpu = float(time.process_time() - started_cpu)
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    return _atomic_result(
        method="Atomic-Quota-Logit",
        assignment=assignment,
        world=world,
        lambda_minus=lambda_minus,
        lambda_plus=lambda_plus,
        converged=converged,
        censoring_reason=censoring_reason,
        logical_rounds=logical_rounds,
        agent_updates=logical_rounds * world.n_robots,
        payoff_evaluations=payoff_evaluations,
        pairwise_evaluations=0,
        swaps=0,
        accepted_moves=accepted_moves,
        packets=packets,
        scalars=scalars,
        payload_bytes=payload_bytes,
        bytes_to_first_feasible=bytes_to_first_feasible,
        bytes_to_convergence=bytes_to_convergence,
        first_feasible_round=first_feasible_round,
        convergence_round=convergence_round,
        wall_time=wall,
        cpu_time=cpu,
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0**2)),
        traces=traces,
        messages=messages,
    )


def run_primary_method(
    world: QuotaWorld,
    graph: QuotaGraph,
    method: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    seed: int,
    initial_assignment: np.ndarray | None = None,
    initial_rho: np.ndarray | None = None,
    previous_assignment: np.ndarray | None = None,
) -> AlgorithmResult:
    if method == "Capacity-CBBA":
        return run_capacity_cbba(
            world,
            graph,
            config,
            stage=stage,
            initial_assignment=initial_assignment,
            previous_assignment=previous_assignment,
        )
    if method == "Weighted-GRAPE":
        return run_weighted_grape(
            world,
            graph,
            config,
            stage=stage,
            pairwise=False,
            seed=seed,
            initial_assignment=initial_assignment,
            previous_assignment=previous_assignment,
        )
    if method == "Weighted-Pair-GRAPE":
        return run_weighted_grape(
            world,
            graph,
            config,
            stage=stage,
            pairwise=True,
            seed=seed,
            initial_assignment=initial_assignment,
            previous_assignment=previous_assignment,
        )
    if method == "Atomic-Quota-Logit":
        return run_atomic_quota_logit(
            world,
            graph,
            config,
            parameters,
            stage=stage,
            seed=seed,
            initial_assignment=initial_assignment,
            previous_assignment=previous_assignment,
        )
    return run_continuous_method(
        world,
        graph,
        method,
        config,
        parameters,
        stage=stage,
        initial_rho=initial_rho,
    )


def environment_record() -> dict[str, Any]:
    import scipy

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
    }
