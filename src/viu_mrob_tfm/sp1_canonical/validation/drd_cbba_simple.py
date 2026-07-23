"""Core models and algorithms for SP1_DRD_VS_CBBA_SIMPLE_v1.

The module deliberately implements a scalar-capacity, static allocation
problem.  It does not reuse the multi-resource primal-dual dynamics from the
other SP1 campaigns.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import time
import tracemalloc
from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix, csr_matrix, diags
from scipy.sparse.csgraph import connected_components, shortest_path
from scipy.sparse.linalg import eigsh

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    AugmentingRepairResult,
    repair_assignment_augmenting,
)


FLOAT64_BYTES = 8
INT64_BYTES = 8
BOOL_BYTES = 1


def stable_hash(value: Any) -> str:
    """Return a deterministic SHA-256 for arrays or JSON-compatible objects."""

    if isinstance(value, np.ndarray):
        return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SimpleWorld:
    seed: int
    world_id: str
    robot_positions: np.ndarray
    load_positions: np.ndarray
    capacities: np.ndarray
    masses: np.ndarray
    witness: np.ndarray
    capacity_regime: str
    utilization_target: float | None
    utilization: float
    distances: np.ndarray
    normalized_distances: np.ndarray
    normalization_scale: float
    world_hash: str
    positions_hash: str
    capacities_hash: str
    loads_hash: str

    @property
    def n_robots(self) -> int:
        return int(self.capacities.size)

    @property
    def n_loads(self) -> int:
        return int(self.masses.size)


@dataclass(frozen=True, slots=True)
class SimpleGraph:
    name: str
    adjacency: csr_matrix
    edges: int
    degree_min: int
    degree_max: int
    degree_mean: float
    diameter: int
    lambda_2: float
    lambda_max: float
    spectral_condition: float
    radius: float
    graph_hash: str

    @property
    def n_nodes(self) -> int:
        return int(self.adjacency.shape[0])


@dataclass(frozen=True, slots=True)
class DRDResult:
    x: np.ndarray
    converged: bool
    censored: bool
    censoring_reason: str
    logical_rounds: int
    first_gate_round: int | None
    first_feasible_round: int | None
    persistent_convergence_round: int | None
    terminal_state_residual: float
    terminal_consensus_residual: float
    terminal_capacity_residual: float
    terminal_state_slope: float
    terminal_consensus_slope: float
    terminal_capacity_slope: float
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    payoff_evaluations: int
    consensus_updates: int
    packets_total: int
    scalar_transmissions_total: int
    payload_bytes_total: int
    bytes_to_first_feasible: int | None
    bytes_to_convergence: int | None
    simplex_violation: float
    nonnegativity_violation: float
    finite_state: bool
    tracker_sum_error: float
    traces: tuple[dict[str, Any], ...]
    messages: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class CBBAResult:
    assignment: np.ndarray
    converged: bool
    censored: bool
    censoring_reason: str
    logical_rounds: int
    first_feasible_round: int | None
    persistent_convergence_round: int | None
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    bid_evaluations: int
    packets_total: int
    scalar_transmissions_total: int
    payload_bytes_total: int
    bytes_to_first_feasible: int | None
    bytes_to_convergence: int | None
    duplicate_assignment_count: int
    proposal_epochs: int
    accepted_bids: int
    traces: tuple[dict[str, Any], ...]
    messages: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class OracleResult:
    kind: str
    status: str
    status_code: int
    objective: float
    lower_bound: float
    upper_bound: float
    mip_gap: float
    optimal: bool
    feasible: bool
    assignment: np.ndarray | None
    x: np.ndarray
    wall_time_s: float
    cpu_time_s: float
    message: str


@dataclass(frozen=True, slots=True)
class RecoveryMetrics:
    assignment: np.ndarray
    executed: bool
    success: bool
    runtime_s: float
    chain_length_max: int
    nodes_expanded: int
    robots_reassigned: int
    objective_before: float
    objective_after: float
    failure_reason: str


def _world_hash(
    seed: int,
    positions: np.ndarray,
    loads: np.ndarray,
    capacities: np.ndarray,
    masses: np.ndarray,
) -> str:
    return stable_hash(
        {
            "seed": int(seed),
            "positions": np.asarray(positions).round(15).tolist(),
            "loads": np.asarray(loads).round(15).tolist(),
            "capacities": np.asarray(capacities).round(15).tolist(),
            "masses": np.asarray(masses).round(15).tolist(),
        }
    )


def _sample_capacities(
    rng: np.random.Generator,
    n: int,
    regime: str,
    regimes: Mapping[str, Any],
) -> np.ndarray:
    spec = regimes[regime]
    if spec["kind"] == "uniform":
        return rng.uniform(float(spec["low"]), float(spec["high"]), size=n)
    if spec["kind"] != "mixture":
        raise ValueError(f"unknown capacity regime kind: {spec['kind']}")
    components = list(spec["components"])
    weights = np.asarray([float(item["weight"]) for item in components], dtype=float)
    weights /= weights.sum()
    labels = rng.choice(len(components), size=n, p=weights)
    capacities = np.empty(n, dtype=float)
    for index, component in enumerate(components):
        selected = labels == index
        capacities[selected] = rng.uniform(
            float(component["low"]),
            float(component["high"]),
            size=int(np.sum(selected)),
        )
    return capacities


def make_simple_world(
    n: int,
    k: int,
    seed: int,
    config: Mapping[str, Any],
    *,
    capacity_regime: str = "medium",
    utilization_target: float | None = None,
    world_id: str | None = None,
) -> SimpleWorld:
    """Generate a feasible planted scalar-capacity world.

    The witness is retained only for audits and is never passed to either
    distributed method.
    """

    if n < k or k < 1:
        raise ValueError("world requires n >= k >= 1")
    problem = config["problem"]
    regimes = config["capacity_regimes"]
    max_attempts = int(problem["max_world_generation_attempts"])
    eta_low, eta_high = map(float, problem["planted_eta_range"])
    utilization_low, utilization_high = map(float, problem["utilization_range"])
    tolerance = float(problem["position_tolerance"])
    epsilon = float(problem["normalization_epsilon"])
    side = float(problem["workspace_side_m"])

    for attempt in range(max_attempts):
        mixed_seed = int(seed) + 104729 * n + 130363 * k + 15485863 * attempt
        rng = np.random.default_rng(mixed_seed)
        positions = rng.uniform(0.0, side, size=(n, 2))
        loads = rng.uniform(0.0, side, size=(k, 2))
        all_positions = np.vstack([positions, loads])
        pairwise = np.linalg.norm(
            all_positions[:, None, :] - all_positions[None, :, :], axis=2
        )
        pairwise += np.eye(n + k)
        if float(np.min(pairwise)) <= tolerance:
            continue
        capacities = _sample_capacities(rng, n, capacity_regime, regimes)
        groups = np.array_split(rng.permutation(n), k)
        witness = np.full(n, -1, dtype=int)
        masses = np.empty(k, dtype=float)
        target = None if utilization_target is None else float(utilization_target)
        for load, coalition in enumerate(groups):
            witness[coalition] = load
            eta = rng.uniform(eta_low, eta_high) if target is None else target
            masses[load] = float(eta * np.sum(capacities[coalition]))
        utilization = float(np.sum(masses) / np.sum(capacities))
        if target is None and not (utilization_low <= utilization <= utilization_high):
            continue
        distances = np.linalg.norm(positions[:, None, :] - loads[None, :, :], axis=2)
        scale = max(float(np.max(distances)), epsilon)
        normalized = distances / scale
        identifier = world_id or f"n{n}_k{k}_s{seed}_{capacity_regime}"
        digest = _world_hash(seed, positions, loads, capacities, masses)
        return SimpleWorld(
            seed=int(seed),
            world_id=identifier,
            robot_positions=positions,
            load_positions=loads,
            capacities=capacities,
            masses=masses,
            witness=witness,
            capacity_regime=capacity_regime,
            utilization_target=target,
            utilization=utilization,
            distances=distances,
            normalized_distances=normalized,
            normalization_scale=scale,
            world_hash=digest,
            positions_hash=stable_hash(np.vstack([positions, loads])),
            capacities_hash=stable_hash(capacities),
            loads_hash=stable_hash(np.column_stack([loads, masses])),
        )
    raise RuntimeError(f"could not generate {n}x{k} world after {max_attempts} attempts")


def make_manual_world(
    *,
    case_id: str,
    positions: np.ndarray,
    loads: np.ndarray,
    capacities: np.ndarray,
    masses: np.ndarray,
    witness: np.ndarray,
) -> SimpleWorld:
    positions = np.asarray(positions, dtype=float)
    loads = np.asarray(loads, dtype=float)
    capacities = np.asarray(capacities, dtype=float)
    masses = np.asarray(masses, dtype=float)
    witness = np.asarray(witness, dtype=int)
    distances = np.linalg.norm(positions[:, None, :] - loads[None, :, :], axis=2)
    scale = max(float(np.max(distances)), 1e-12)
    digest = _world_hash(0, positions, loads, capacities, masses)
    return SimpleWorld(
        seed=0,
        world_id=case_id,
        robot_positions=positions,
        load_positions=loads,
        capacities=capacities,
        masses=masses,
        witness=witness,
        capacity_regime="deterministic",
        utilization_target=None,
        utilization=float(masses.sum() / capacities.sum()),
        distances=distances,
        normalized_distances=distances / scale,
        normalization_scale=scale,
        world_hash=digest,
        positions_hash=stable_hash(np.vstack([positions, loads])),
        capacities_hash=stable_hash(capacities),
        loads_hash=stable_hash(np.column_stack([loads, masses])),
    )


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = np.arange(n)
        self.rank = np.zeros(n, dtype=np.int8)
        self.components = n

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = int(self.parent[item])
        return item

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a == b:
            return
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1
        self.components -= 1


def _graph_diameter(adjacency: csr_matrix) -> int:
    n = adjacency.shape[0]
    maximum = 0
    indptr, indices = adjacency.indptr, adjacency.indices
    for origin in range(n):
        distances = np.full(n, -1, dtype=np.int32)
        distances[origin] = 0
        queue = deque([origin])
        while queue:
            node = queue.popleft()
            for neighbor in indices[indptr[node] : indptr[node + 1]]:
                if distances[neighbor] < 0:
                    distances[neighbor] = distances[node] + 1
                    queue.append(int(neighbor))
        if np.any(distances < 0):
            raise ValueError("diameter requested for disconnected graph")
        maximum = max(maximum, int(np.max(distances)))
    return maximum


def graph_from_adjacency(
    name: str,
    adjacency: csr_matrix | np.ndarray,
    *,
    radius: float = math.inf,
) -> SimpleGraph:
    matrix = csr_matrix(adjacency, dtype=np.int8)
    matrix = ((matrix + matrix.T) > 0).astype(np.int8).tocsr()
    matrix.setdiag(0)
    matrix.eliminate_zeros()
    n = matrix.shape[0]
    components, _ = connected_components(matrix, directed=False)
    if components != 1:
        raise ValueError("SP1-simple graph must be connected")
    degrees = np.asarray(matrix.sum(axis=1)).ravel().astype(int)
    laplacian = diags(degrees.astype(float)) - matrix.astype(float)
    if n == 1:
        lambda_2 = lambda_max = 0.0
    elif n <= 120:
        eigenvalues = np.linalg.eigvalsh(laplacian.toarray())
        lambda_2 = float(eigenvalues[1])
        lambda_max = float(eigenvalues[-1])
    else:
        small = np.sort(eigsh(laplacian, k=2, which="SM", return_eigenvectors=False))
        lambda_2 = float(max(small[1], 0.0))
        lambda_max = float(
            eigsh(laplacian, k=1, which="LA", return_eigenvectors=False)[0]
        )
    digest = stable_hash(matrix.toarray().astype(np.uint8))
    return SimpleGraph(
        name=name,
        adjacency=matrix,
        edges=int(matrix.nnz // 2),
        degree_min=int(np.min(degrees)) if degrees.size else 0,
        degree_max=int(np.max(degrees)) if degrees.size else 0,
        degree_mean=float(np.mean(degrees)),
        diameter=_graph_diameter(matrix),
        lambda_2=lambda_2,
        lambda_max=lambda_max,
        spectral_condition=(
            float(lambda_max / lambda_2) if lambda_2 > 1e-12 else math.inf
        ),
        radius=float(radius),
        graph_hash=digest,
    )


def make_graph(world: SimpleWorld, topology: str) -> SimpleGraph:
    """Build a complete or connected target-degree geometric graph."""

    n = world.n_robots
    if topology == "complete":
        adjacency = np.ones((n, n), dtype=np.int8) - np.eye(n, dtype=np.int8)
        return graph_from_adjacency("complete", adjacency)
    if not topology.startswith("rdisk_degree_"):
        raise ValueError(f"unknown topology: {topology}")
    target = float(topology.rsplit("_", 1)[-1])
    delta = world.robot_positions[:, None, :] - world.robot_positions[None, :, :]
    distances = np.linalg.norm(delta, axis=2)
    upper_i, upper_j = np.triu_indices(n, 1)
    order = np.argsort(distances[upper_i, upper_j], kind="mergesort")
    edges_i = upper_i[order]
    edges_j = upper_j[order]
    edge_distances = distances[edges_i, edges_j]
    union = _UnionFind(n)
    connected_edge_count = len(order)
    for index, (left, right) in enumerate(zip(edges_i, edges_j, strict=True), start=1):
        union.union(int(left), int(right))
        if union.components == 1:
            connected_edge_count = index
            break
    target_edges = int(round(n * target / 2.0))
    selected_count = min(len(order), max(connected_edge_count, target_edges))
    radius = float(edge_distances[selected_count - 1]) + 1e-12
    mask = distances <= radius
    np.fill_diagonal(mask, False)
    return graph_from_adjacency(topology, mask.astype(np.int8), radius=radius)


def metropolis_hastings_matrix(
    graph: SimpleGraph,
    *,
    tolerance: float = 1e-12,
) -> csr_matrix:
    """Construct a symmetric doubly stochastic Metropolis matrix."""

    adjacency = graph.adjacency
    degrees = np.asarray(adjacency.sum(axis=1)).ravel().astype(int)
    rows: list[int] = []
    columns: list[int] = []
    data: list[float] = []
    diagonal = np.ones(graph.n_nodes, dtype=float)
    upper_rows, upper_columns = adjacency.nonzero()
    for left, right in zip(upper_rows, upper_columns, strict=True):
        if left >= right:
            continue
        weight = 1.0 / (1.0 + max(degrees[left], degrees[right]))
        rows.extend([int(left), int(right)])
        columns.extend([int(right), int(left)])
        data.extend([weight, weight])
        diagonal[left] -= weight
        diagonal[right] -= weight
    rows.extend(range(graph.n_nodes))
    columns.extend(range(graph.n_nodes))
    data.extend(diagonal.tolist())
    matrix = csr_matrix((data, (rows, columns)), shape=adjacency.shape)
    row_error = float(np.max(np.abs(np.asarray(matrix.sum(axis=1)).ravel() - 1.0)))
    column_error = float(np.max(np.abs(np.asarray(matrix.sum(axis=0)).ravel() - 1.0)))
    forbidden = matrix.copy()
    forbidden.setdiag(0.0)
    forbidden.eliminate_zeros()
    support_error = int(
        np.any(
            (forbidden.toarray() != 0.0)
            & (adjacency.toarray().astype(bool) == 0)
        )
    )
    if row_error > tolerance or column_error > tolerance or support_error:
        raise ValueError("invalid Metropolis-Hastings matrix")
    eigenvalues = np.linalg.eigvalsh(matrix.toarray()) if graph.n_nodes <= 120 else None
    if eigenvalues is not None and float(np.max(np.abs(eigenvalues))) > 1.0 + tolerance:
        raise ValueError("unstable Metropolis-Hastings matrix")
    return matrix


def initial_drd_state(
    world: SimpleWorld,
    mode: str = "uniform",
) -> np.ndarray:
    if mode == "uniform":
        return np.full(
            (world.n_robots, world.n_loads + 1),
            1.0 / (world.n_loads + 1),
            dtype=float,
        )
    if mode != "distance_biased":
        raise ValueError(f"unknown DRD initialization: {mode}")
    weights = np.column_stack(
        [np.ones(world.n_robots), np.exp(-world.normalized_distances)]
    )
    return weights / weights.sum(axis=1, keepdims=True)


def exponential_replicator_step(
    x: np.ndarray,
    fitness: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """Stable exponentiated replicator/multiplicative-weights update."""

    log_weights = np.log(np.maximum(np.asarray(x, dtype=float), 1e-300))
    log_weights += float(alpha) * np.asarray(fitness, dtype=float)
    log_weights -= np.max(log_weights, axis=1, keepdims=True)
    weights = np.exp(log_weights)
    return weights / weights.sum(axis=1, keepdims=True)


def _terminal_slope(values: deque[float]) -> float:
    data = np.asarray(values, dtype=float)
    if data.size < 2 or not np.all(np.isfinite(data)):
        return math.nan
    return float(np.polyfit(np.arange(data.size, dtype=float), data, 1)[0])


def run_drd(
    world: SimpleWorld,
    graph: SimpleGraph,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    initialization: str | None = None,
    max_rounds_override: int | None = None,
    max_wall_time_override: float | None = None,
) -> DRDResult:
    """Run DRD-simple using only local tracker estimates in its update."""

    drd = config["drd"]
    mode = initialization or str(drd["initialization"])
    max_rounds = int(max_rounds_override or drd["max_rounds"])
    max_wall = float(max_wall_time_override or drd["max_wall_time_s"])
    dwell_rounds = int(drd["dwell_rounds"])
    state_tolerance = float(drd["state_tolerance"])
    consensus_tolerance = float(drd["consensus_tolerance"])
    capacity_tolerance = float(drd["capacity_tolerance"])
    trace_stride = int(drd["trace_stride"])
    alpha = float(parameters["alpha"])
    rho = float(parameters["rho"])
    tau = float(parameters["tau"])
    idle_bias = float(config["potential"]["idle_bias"])
    log_epsilon = float(config["problem"]["log_epsilon"])
    n, k = world.n_robots, world.n_loads
    matrix = metropolis_hastings_matrix(
        graph, tolerance=float(config["graph"]["stochastic_tolerance"])
    )
    x = initial_drd_state(world, mode)
    z = world.capacities[:, None] * x[:, 1:]
    tracker_initial_sum = np.sum(z, axis=0).copy()
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    recent_state: deque[float] = deque(maxlen=101)
    recent_consensus: deque[float] = deque(maxlen=101)
    recent_capacity: deque[float] = deque(maxlen=101)
    gate_streak = 0
    first_gate: int | None = None
    first_feasible: int | None = None
    persistent: int | None = None
    reason = "max_rounds"
    terminal_state = terminal_consensus = terminal_capacity = math.inf

    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    rounds = 0
    for round_index in range(1, max_rounds + 1):
        if time.perf_counter() - wall_start >= max_wall:
            reason = "max_wall_time"
            break
        qhat = n * z
        delta_hat = np.maximum(
            0.0, 1.0 - qhat / np.maximum(world.masses[None, :], 1e-15)
        )
        fitness = np.empty_like(x)
        fitness[:, 0] = (
            -tau * (1.0 + np.log(np.maximum(x[:, 0], log_epsilon))) + idle_bias
        )
        fitness[:, 1:] = (
            -world.normalized_distances
            + rho
            * (world.capacities[:, None] / world.masses[None, :])
            * delta_hat
            - tau * (1.0 + np.log(np.maximum(x[:, 1:], log_epsilon)))
        )
        x_new = exponential_replicator_step(x, fitness, alpha)
        z_new = matrix.dot(z) + world.capacities[:, None] * (
            x_new[:, 1:] - x[:, 1:]
        )
        q_true = np.sum(world.capacities[:, None] * x_new[:, 1:], axis=0)
        qhat_new = n * z_new
        terminal_state = float(np.max(np.abs(x_new - x)))
        terminal_consensus = float(
            np.max(np.abs(qhat_new - q_true[None, :]))
            / max(1.0, float(np.max(q_true)))
        )
        terminal_capacity = float(
            np.max(np.maximum(world.masses - q_true, 0.0))
            / max(1.0, float(np.max(world.masses)))
        )
        rounds = round_index
        recent_state.append(terminal_state)
        recent_consensus.append(terminal_consensus)
        recent_capacity.append(terminal_capacity)
        capacity_ok = terminal_capacity <= capacity_tolerance
        if capacity_ok and first_feasible is None:
            first_feasible = round_index
        gate = (
            terminal_state <= state_tolerance
            and terminal_consensus <= consensus_tolerance
            and capacity_ok
        )
        if gate:
            gate_streak += 1
            if first_gate is None:
                first_gate = round_index
        else:
            gate_streak = 0
        if (
            round_index == 1
            or round_index % trace_stride == 0
            or gate
            or round_index == max_rounds
        ):
            traces.append(
                {
                    "method": "DRD-simple",
                    "round": round_index,
                    "state_residual": terminal_state,
                    "consensus_residual": terminal_consensus,
                    "capacity_residual": terminal_capacity,
                    "gate_streak": gate_streak,
                    "continuous_feasible": capacity_ok,
                }
            )
        x, z = x_new, z_new
        if gate_streak >= dwell_rounds:
            persistent = round_index
            reason = ""
            break
    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    directed_edges = 2 * graph.edges
    packets = directed_edges * rounds
    scalars = packets * (k + 1)
    bytes_total = scalars * FLOAT64_BYTES
    bytes_per_round = directed_edges * (k + 1) * FLOAT64_BYTES
    messages.append(
        {
            "method": "DRD-simple",
            "phase": "tracker",
            "logical_rounds": rounds,
            "directed_edges": directed_edges,
            "packets_per_round": directed_edges,
            "float64_per_packet": k,
            "int64_per_packet": 1,
            "bool_per_packet": 0,
            "records": rounds * directed_edges,
            "packets_total": packets,
            "scalar_transmissions_total": scalars,
            "payload_bytes_total": bytes_total,
        }
    )
    finite = bool(np.all(np.isfinite(x)) and np.all(np.isfinite(z)))
    simplex_violation = float(np.max(np.abs(x.sum(axis=1) - 1.0)))
    nonnegative_violation = float(np.max(np.maximum(-x, 0.0)))
    tracker_sum_error = float(
        np.max(
            np.abs(
                np.sum(z, axis=0)
                - (
                    tracker_initial_sum
                    + np.sum(
                        world.capacities[:, None]
                        * (x[:, 1:] - initial_drd_state(world, mode)[:, 1:]),
                        axis=0,
                    )
                )
            )
        )
    )
    converged = persistent is not None
    return DRDResult(
        x=x,
        converged=converged,
        censored=not converged,
        censoring_reason=reason if not converged else "",
        logical_rounds=rounds,
        first_gate_round=first_gate,
        first_feasible_round=first_feasible,
        persistent_convergence_round=persistent,
        terminal_state_residual=terminal_state,
        terminal_consensus_residual=terminal_consensus,
        terminal_capacity_residual=terminal_capacity,
        terminal_state_slope=_terminal_slope(recent_state),
        terminal_consensus_slope=_terminal_slope(recent_consensus),
        terminal_capacity_slope=_terminal_slope(recent_capacity),
        wall_time_s=wall_time,
        cpu_time_s=cpu_time,
        peak_memory_mb=peak_bytes / 1024**2,
        payoff_evaluations=rounds * n * (k + 1),
        consensus_updates=rounds * n * k,
        packets_total=packets,
        scalar_transmissions_total=scalars,
        payload_bytes_total=bytes_total,
        bytes_to_first_feasible=(
            None if first_feasible is None else first_feasible * bytes_per_round
        ),
        bytes_to_convergence=(None if persistent is None else persistent * bytes_per_round),
        simplex_violation=simplex_violation,
        nonnegativity_violation=nonnegative_violation,
        finite_state=finite,
        tracker_sum_error=tracker_sum_error,
        traces=tuple(traces),
        messages=tuple(messages),
    )


def marginal_bid(
    normalized_distance: float,
    capacity: float,
    mass: float,
    recruited_capacity: float,
    rho: float,
) -> float:
    delta = max(0.0, 1.0 - recruited_capacity / mass)
    after = max(0.0, 1.0 - (recruited_capacity + capacity) / mass)
    return float(-normalized_distance + 0.5 * rho * (delta * delta - after * after))


def _flood_delta_counts(
    graph: SimpleGraph,
    sources: np.ndarray,
    fields_per_record: int,
    distances: np.ndarray | None = None,
) -> tuple[int, int, int, int]:
    """Count deterministic frontier flooding with delta-record packets.

    A node sends one packet per neighbor when its frontier is non-empty.  The
    packet contains every record learned in the preceding hop.  Duplicate
    arrivals are counted because they consume payload.
    """

    sources = np.asarray(sources, dtype=int)
    if sources.size == 0:
        return 0, 0, 0, 0
    hops = (
        np.asarray(distances, dtype=np.int16)
        if distances is not None
        else shortest_path(
            graph.adjacency, directed=False, unweighted=True
        ).astype(np.int16)
    )
    source_hops = hops[sources]
    degrees = np.asarray(graph.adjacency.sum(axis=1)).ravel().astype(np.int64)
    packets = scalars = 0
    maximum_hop = int(np.max(source_hops))
    # A record learned at hop h is forwarded once by that frontier. Packets
    # bundle every record in the sender's frontier; payload still counts each
    # record separately. This is exactly equivalent to explicit set flooding.
    for hop in range(maximum_hop + 1):
        record_counts = np.sum(source_hops == hop, axis=0, dtype=np.int64)
        packets += int(np.sum(degrees[record_counts > 0]))
        scalars += int(np.dot(record_counts, degrees)) * int(fields_per_record)
    rounds = maximum_hop + 1
    bytes_total = scalars * 8
    return rounds, packets, scalars, bytes_total


def run_cbba(
    world: SimpleWorld,
    graph: SimpleGraph,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    candidates_per_load: int | str | None = None,
    max_rounds_override: int | None = None,
    max_wall_time_override: float | None = None,
) -> CBBAResult:
    """Run the explicit unit-bundle, multi-winner CBBA adaptation."""

    cbba = config["cbba"]
    max_rounds = int(max_rounds_override or cbba["max_rounds"])
    max_wall = float(max_wall_time_override or cbba["max_wall_time_s"])
    stable_rounds = int(cbba["stable_rounds_multiplier"]) * graph.diameter
    accepted_per_load = (
        candidates_per_load
        if candidates_per_load is not None
        else cbba["candidates_per_load_per_epoch"]
    )
    rho = float(parameters["rho"])
    bid_minimum = float(parameters.get("bid_minimum", 0.0))
    n, k = world.n_robots, world.n_loads
    assignment = np.full(n, -1, dtype=int)
    bid_evaluations = 0
    packets = scalars = bytes_total = rounds = 0
    first_feasible: int | None = None
    persistent: int | None = None
    proposal_epochs = accepted_bids = 0
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    reason = "max_rounds"
    graph_hops = shortest_path(
        graph.adjacency, directed=False, unweighted=True
    ).astype(np.int16)

    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    while rounds < max_rounds:
        if time.perf_counter() - wall_start >= max_wall:
            reason = "max_wall_time"
            break
        coverage = np.bincount(
            assignment[assignment >= 0],
            weights=world.capacities[assignment >= 0],
            minlength=k,
        )
        deficient = coverage < world.masses - 1e-12
        if not np.any(deficient):
            first_feasible = rounds if first_feasible is None else first_feasible
            directed_edges = 2 * graph.edges
            state_records = n
            per_round_scalars = directed_edges * state_records * 4
            possible = min(stable_rounds, max_rounds - rounds)
            packets_added = directed_edges * possible
            scalars_added = per_round_scalars * possible
            bytes_added = scalars_added * 8
            packets += packets_added
            scalars += scalars_added
            bytes_total += bytes_added
            messages.append(
                {
                    "method": "CBBA-1-Capacity",
                    "phase": "stable_full_state",
                    "logical_rounds": possible,
                    "directed_edges": directed_edges,
                    "packets_per_round": directed_edges,
                    "records": state_records * possible * directed_edges,
                    "float64_per_record": 1,
                    "int64_per_record": 3,
                    "bool_per_record": 0,
                    "packets_total": packets_added,
                    "scalar_transmissions_total": scalars_added,
                    "payload_bytes_total": bytes_added,
                }
            )
            rounds += possible
            if possible == stable_rounds:
                persistent = rounds
                reason = ""
            break

        free = np.flatnonzero(assignment < 0)
        proposals: list[tuple[int, int, float, float]] = []
        for robot in free:
            candidates: list[tuple[float, int, float]] = []
            for load in np.flatnonzero(deficient):
                bid_evaluations += 1
                bid = marginal_bid(
                    world.normalized_distances[robot, load],
                    world.capacities[robot],
                    world.masses[load],
                    coverage[load],
                    rho,
                )
                useful = min(
                    world.capacities[robot],
                    max(world.masses[load] - coverage[load], 0.0),
                )
                if bid > bid_minimum:
                    candidates.append((bid, int(load), float(useful)))
            if candidates:
                bid, load, useful = min(
                    candidates,
                    key=lambda item: (-item[0], item[1]),
                )
                proposals.append((int(robot), load, float(bid), useful))
        if not proposals:
            reason = "no_positive_bid"
            break
        proposal_epochs += 1
        proposal_sources = np.asarray([item[0] for item in proposals], dtype=int)
        flood_rounds, p, s, b = _flood_delta_counts(
            graph, proposal_sources, 5, graph_hops
        )
        if rounds + flood_rounds > max_rounds:
            reason = "max_rounds"
            break
        rounds += flood_rounds
        packets += p
        scalars += s
        bytes_total += b
        messages.append(
            {
                "method": "CBBA-1-Capacity",
                "phase": "bid_delta_flood",
                "logical_rounds": flood_rounds,
                "directed_edges": 2 * graph.edges,
                "packets_per_round": math.nan,
                "records": int(s // 5),
                "float64_per_record": 2,
                "int64_per_record": 3,
                "bool_per_record": 0,
                "packets_total": p,
                "scalar_transmissions_total": s,
                "payload_bytes_total": b,
            }
        )
        winners: list[int] = []
        for load in range(k):
            load_proposals = [item for item in proposals if item[1] == load]
            ranked = sorted(
                load_proposals,
                key=lambda item: (
                    -item[2],
                    world.distances[item[0], load],
                    -item[3],
                    item[0],
                ),
            )
            limit = len(ranked) if accepted_per_load == "all" else int(accepted_per_load)
            remaining = max(world.masses[load] - coverage[load], 0.0)
            for candidate in ranked[:limit]:
                if remaining <= 1e-12:
                    break
                winners.append(candidate[0])
                remaining -= world.capacities[candidate[0]]
        if not winners:
            reason = "conflict_without_winner"
            break
        winner_load = {item[0]: item[1] for item in proposals if item[0] in winners}
        for robot in winners:
            assignment[robot] = winner_load[robot]
        accepted_bids += len(winners)
        state_sources = np.asarray(winners, dtype=int)
        state_rounds, p, s, b = _flood_delta_counts(
            graph, state_sources, 4, graph_hops
        )
        if rounds + state_rounds > max_rounds:
            reason = "max_rounds"
            break
        rounds += state_rounds
        packets += p
        scalars += s
        bytes_total += b
        messages.append(
            {
                "method": "CBBA-1-Capacity",
                "phase": "coalition_delta_flood",
                "logical_rounds": state_rounds,
                "directed_edges": 2 * graph.edges,
                "packets_per_round": math.nan,
                "records": int(s // 4),
                "float64_per_record": 1,
                "int64_per_record": 3,
                "bool_per_record": 0,
                "packets_total": p,
                "scalar_transmissions_total": s,
                "payload_bytes_total": b,
            }
        )
        coverage_after = np.bincount(
            assignment[assignment >= 0],
            weights=world.capacities[assignment >= 0],
            minlength=k,
        )
        feasible_after = bool(np.all(coverage_after >= world.masses - 1e-12))
        if feasible_after and first_feasible is None:
            first_feasible = rounds
        traces.append(
            {
                "method": "CBBA-1-Capacity",
                "round": rounds,
                "proposal_epoch": proposal_epochs,
                "proposals": len(proposals),
                "accepted": len(winners),
                "assigned_robots": int(np.sum(assignment >= 0)),
                "deficit_total": float(
                    np.sum(np.maximum(world.masses - coverage_after, 0.0))
                ),
                "feasible": feasible_after,
            }
        )
    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    converged = persistent is not None
    bytes_to_first = None
    if first_feasible is not None:
        # The cumulative count at first feasibility is exactly the total
        # before stable-state verification; stable exchange is added later.
        stable_bytes = 0
        for row in messages:
            if row["phase"] == "stable_full_state":
                stable_bytes += int(row["payload_bytes_total"])
        bytes_to_first = bytes_total - stable_bytes
    # A single integer vector is the canonical reconstruction; it cannot
    # encode the same robot in two coalitions.
    duplicate_count = 0
    return CBBAResult(
        assignment=assignment,
        converged=converged,
        censored=not converged,
        censoring_reason=reason if not converged else "",
        logical_rounds=rounds,
        first_feasible_round=first_feasible,
        persistent_convergence_round=persistent,
        wall_time_s=wall_time,
        cpu_time_s=cpu_time,
        peak_memory_mb=peak_bytes / 1024**2,
        bid_evaluations=bid_evaluations,
        packets_total=packets,
        scalar_transmissions_total=scalars,
        payload_bytes_total=bytes_total,
        bytes_to_first_feasible=bytes_to_first,
        bytes_to_convergence=(bytes_total if converged else None),
        duplicate_assignment_count=duplicate_count,
        proposal_epochs=proposal_epochs,
        accepted_bids=accepted_bids,
        traces=tuple(traces),
        messages=tuple(messages),
    )


def assignment_from_drd(x: np.ndarray) -> np.ndarray:
    choices = np.argmax(np.asarray(x, dtype=float), axis=1)
    return np.where(choices == 0, -1, choices - 1).astype(int)


def integer_metrics(
    world: SimpleWorld,
    assignment: np.ndarray,
) -> dict[str, Any]:
    assignment = np.asarray(assignment, dtype=int)
    if assignment.shape != (world.n_robots,):
        raise ValueError("assignment shape mismatch")
    if np.any((assignment < -1) | (assignment >= world.n_loads)):
        raise ValueError("assignment contains invalid load")
    coverage = np.bincount(
        assignment[assignment >= 0],
        weights=world.capacities[assignment >= 0],
        minlength=world.n_loads,
    )
    deficit = np.maximum(world.masses - coverage, 0.0)
    excess = np.maximum(coverage - world.masses, 0.0)
    assigned = np.flatnonzero(assignment >= 0)
    selected_distances = (
        world.distances[assigned, assignment[assigned]]
        if assigned.size
        else np.asarray([], dtype=float)
    )
    per_load = np.zeros(world.n_loads, dtype=float)
    for load in range(world.n_loads):
        robots = np.flatnonzero(assignment == load)
        per_load[load] = float(np.sum(world.distances[robots, load]))
    return {
        "feasible": bool(np.all(deficit <= 1e-9)),
        "deficit_total": float(np.sum(deficit)),
        "deficit_max": float(np.max(deficit, initial=0.0)),
        "distance_total": float(np.sum(selected_distances)),
        "distance_mean_per_assigned_robot": (
            float(np.mean(selected_distances)) if assigned.size else 0.0
        ),
        "distance_max": float(np.max(selected_distances, initial=0.0)),
        "distance_per_load": json.dumps(per_load.tolist()),
        "worst_load_distance": float(np.max(per_load, initial=0.0)),
        "excess_total": float(np.sum(excess)),
        "excess_mean": float(np.mean(excess)),
        "excess_max": float(np.max(excess, initial=0.0)),
        "excess_ratio": float(np.sum(excess) / max(float(np.sum(world.masses)), 1e-12)),
        "robots_used": int(assigned.size),
        "idle_robots": int(world.n_robots - assigned.size),
        "assignment_hash": stable_hash(assignment),
    }


def continuous_metrics(
    world: SimpleWorld,
    x: np.ndarray,
    *,
    rho: float,
    tau: float,
) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    load_x = x[:, 1:]
    q = np.sum(world.capacities[:, None] * load_x, axis=0)
    relative_deficit = np.maximum(0.0, 1.0 - q / world.masses)
    excess = np.maximum(q - world.masses, 0.0)
    normalized_distance = float(np.sum(world.normalized_distances * load_x))
    physical_distance = float(np.sum(world.distances * load_x))
    entropy = float(-np.sum(x * np.log(np.maximum(x, 1e-300))))
    penalized = normalized_distance + 0.5 * rho * float(
        np.sum(relative_deficit**2)
    )
    regularized = penalized - tau * entropy
    return {
        "objective_distance_continuous": physical_distance,
        "objective_penalized": penalized,
        "objective_regularized": regularized,
        "entropy": entropy,
        "total_deficit_continuous": float(np.sum(np.maximum(world.masses - q, 0.0))),
        "total_relative_deficit_continuous": float(np.sum(relative_deficit)),
        "total_excess_capacity_continuous": float(np.sum(excess)),
    }


def _as_resource_world(world: SimpleWorld) -> ResourceWorld:
    return ResourceWorld(
        seed=world.seed,
        robot_positions_m=world.robot_positions.copy(),
        load_positions_m=world.load_positions.copy(),
        resources=world.capacities[:, None].copy(),
        requirements=world.masses[:, None].copy(),
        battery_energy=np.ones(world.n_robots),
        max_speed_mps=np.ones(world.n_robots),
        energy_per_m=np.ones(world.n_robots),
        robot_classes=tuple("scalar" for _ in range(world.n_robots)),
        feasibility_witness=world.witness.copy(),
        world_hash=world.world_hash,
    )


def recover_assignment(
    world: SimpleWorld,
    assignment: np.ndarray,
    config: Mapping[str, Any],
) -> RecoveryMetrics:
    """Apply the exact same bounded augmenting recovery to either generator."""

    before = integer_metrics(world, assignment)
    if before["feasible"]:
        return RecoveryMetrics(
            assignment=np.asarray(assignment, dtype=int).copy(),
            executed=False,
            success=True,
            runtime_s=0.0,
            chain_length_max=0,
            nodes_expanded=0,
            robots_reassigned=0,
            objective_before=float(before["distance_total"]),
            objective_after=float(before["distance_total"]),
            failure_reason="",
        )
    recovery = config["recovery"]
    resource_world = _as_resource_world(world)
    start = time.perf_counter()
    result: AugmentingRepairResult = repair_assignment_augmenting(
        resource_world,
        np.asarray(assignment, dtype=int),
        world.distances,
        max_chain_length=int(recovery["max_chain_length"]),
        max_nodes_per_augmentation=int(recovery["max_nodes_per_augmentation"]),
        candidates_per_load=int(recovery["candidates_per_load"]),
        prune=bool(recovery["prune"]),
        local_exchange=bool(recovery["local_exchange"]),
        compress=bool(recovery["compress"]),
    )
    runtime = time.perf_counter() - start
    after_assignment = result.integer.assignment
    after = integer_metrics(world, after_assignment)
    return RecoveryMetrics(
        assignment=after_assignment,
        executed=True,
        success=bool(after["feasible"]),
        runtime_s=runtime,
        chain_length_max=result.maximum_chain_length,
        nodes_expanded=result.nodes_explored,
        robots_reassigned=int(np.sum(after_assignment != np.asarray(assignment))),
        objective_before=float(before["distance_total"]),
        objective_after=float(after["distance_total"]),
        failure_reason=result.failure_reason,
    )


def _scalar_constraint_matrix(world: SimpleWorld) -> csr_matrix:
    n, k = world.n_robots, world.n_loads
    variables = n * k
    robot_rows = np.repeat(np.arange(n), k)
    variable_indices = np.arange(variables)
    load_rows = n + np.tile(np.arange(k), n)
    data = np.concatenate(
        [np.ones(variables), -np.repeat(world.capacities, k)]
    )
    rows = np.concatenate([robot_rows, load_rows])
    columns = np.concatenate([variable_indices, variable_indices])
    return coo_matrix((data, (rows, columns)), shape=(n + k, variables)).tocsr()


def solve_scalar_lp(world: SimpleWorld) -> OracleResult:
    matrix = _scalar_constraint_matrix(world)
    rhs = np.r_[np.ones(world.n_robots), -world.masses]
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    result = linprog(
        world.distances.reshape(-1),
        A_ub=matrix,
        b_ub=rhs,
        bounds=(0.0, 1.0),
        method="highs",
    )
    wall, cpu = time.perf_counter() - wall_start, time.process_time() - cpu_start
    x = (
        np.zeros_like(world.distances)
        if result.x is None
        else np.asarray(result.x).reshape(world.distances.shape)
    )
    objective = math.inf if result.fun is None else float(result.fun)
    feasible = bool(result.success)
    return OracleResult(
        kind="LP",
        status="optimal" if result.success else "solver_error",
        status_code=int(result.status),
        objective=objective,
        lower_bound=objective,
        upper_bound=objective,
        mip_gap=0.0 if result.success else math.nan,
        optimal=bool(result.success),
        feasible=feasible,
        assignment=None,
        x=x,
        wall_time_s=wall,
        cpu_time_s=cpu,
        message=str(result.message),
    )


def solve_scalar_milp(
    world: SimpleWorld,
    *,
    time_limit_s: float,
) -> OracleResult:
    matrix = _scalar_constraint_matrix(world)
    rhs = np.r_[np.ones(world.n_robots), -world.masses]
    variables = world.n_robots * world.n_loads
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    try:
        result = milp(
            world.distances.reshape(-1),
            integrality=np.ones(variables, dtype=np.int8),
            bounds=Bounds(np.zeros(variables), np.ones(variables)),
            constraints=LinearConstraint(
                matrix, np.full(matrix.shape[0], -np.inf), rhs
            ),
            options={"time_limit": float(time_limit_s)},
        )
    except Exception as error:  # pragma: no cover - defensive solver boundary
        wall = time.perf_counter() - wall_start
        cpu = time.process_time() - cpu_start
        return OracleResult(
            kind="MILP",
            status="solver_error",
            status_code=-1,
            objective=math.inf,
            lower_bound=math.nan,
            upper_bound=math.inf,
            mip_gap=math.nan,
            optimal=False,
            feasible=False,
            assignment=None,
            x=np.zeros_like(world.distances),
            wall_time_s=wall,
            cpu_time_s=cpu,
            message=repr(error),
        )
    wall, cpu = time.perf_counter() - wall_start, time.process_time() - cpu_start
    x = (
        np.zeros_like(world.distances)
        if result.x is None
        else (np.asarray(result.x).reshape(world.distances.shape) > 0.5).astype(float)
    )
    objective = math.inf if result.fun is None else float(result.fun)
    feasible = result.x is not None and np.all(
        np.sum(world.capacities[:, None] * x, axis=0) >= world.masses - 1e-7
    )
    assignment = None
    if feasible:
        assignment = np.full(world.n_robots, -1, dtype=int)
        selected = np.argwhere(x > 0.5)
        for robot, load in selected:
            assignment[int(robot)] = int(load)
    if result.status == 0 and feasible:
        status = "optimal"
    elif result.status == 1 and feasible:
        status = "feasible_not_proven_optimal"
    elif result.status == 1:
        status = "timeout"
    elif result.status == 2:
        status = "infeasible"
    else:
        status = "solver_error"
    lower = float(getattr(result, "mip_dual_bound", math.nan))
    gap = float(getattr(result, "mip_gap", math.nan))
    return OracleResult(
        kind="MILP",
        status=status,
        status_code=int(result.status),
        objective=objective,
        lower_bound=lower,
        upper_bound=objective,
        mip_gap=gap,
        optimal=status == "optimal",
        feasible=bool(feasible),
        assignment=assignment,
        x=x,
        wall_time_s=wall,
        cpu_time_s=cpu,
        message=str(result.message),
    )


def validate_message_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Independently recompute payload totals from message-log primitives."""

    validation: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        packets = int(row["packets_total"])
        if row["phase"] == "tracker":
            expected_packets = int(row["logical_rounds"]) * int(
                row["packets_per_round"]
            )
            expected_scalars = expected_packets * (
                int(row["float64_per_packet"]) + int(row["int64_per_packet"])
            )
            expected_bytes = expected_scalars * 8
        else:
            expected_packets = packets
            records = int(row["records"])
            float_fields = int(row.get("float64_per_record", 0))
            int_fields = int(row.get("int64_per_record", 0))
            bool_fields = int(row.get("bool_per_record", 0))
            expected_scalars = records * (float_fields + int_fields + bool_fields)
            expected_bytes = records * (
                float_fields * FLOAT64_BYTES
                + int_fields * INT64_BYTES
                + bool_fields * BOOL_BYTES
            )
        validation.append(
            {
                "row_index": index,
                "method": row["method"],
                "phase": row["phase"],
                "declared_packets": packets,
                "recomputed_packets": expected_packets,
                "declared_scalars": int(row["scalar_transmissions_total"]),
                "recomputed_scalars": expected_scalars,
                "declared_bytes": int(row["payload_bytes_total"]),
                "recomputed_bytes": expected_bytes,
                "valid": bool(
                    packets == expected_packets
                    and int(row["scalar_transmissions_total"]) == expected_scalars
                    and int(row["payload_bytes_total"]) == expected_bytes
                ),
            }
        )
    return validation


def environment_record() -> dict[str, Any]:
    import scipy

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "os": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
    }


__all__ = [
    "BOOL_BYTES",
    "CBBAResult",
    "DRDResult",
    "FLOAT64_BYTES",
    "INT64_BYTES",
    "OracleResult",
    "RecoveryMetrics",
    "SimpleGraph",
    "SimpleWorld",
    "assignment_from_drd",
    "continuous_metrics",
    "environment_record",
    "exponential_replicator_step",
    "graph_from_adjacency",
    "initial_drd_state",
    "integer_metrics",
    "make_graph",
    "make_manual_world",
    "make_simple_world",
    "marginal_bid",
    "metropolis_hastings_matrix",
    "recover_assignment",
    "run_cbba",
    "run_drd",
    "solve_scalar_lp",
    "solve_scalar_milp",
    "stable_hash",
    "validate_message_rows",
]
