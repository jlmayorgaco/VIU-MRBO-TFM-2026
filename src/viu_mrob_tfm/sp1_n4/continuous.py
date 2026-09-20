"""Continuous N4 families and their common atomic closure.

This module deliberately keeps two mathematical objects separate:

* F-II is an unconstrained population game with a differentiable deficit
  penalty.  Replicator, Smith, BNN and Logit use exactly the same fitness.
* F-III is a convex shared-constraint game.  Capacity requirements are handled
  by dual prices and a projected primal--dual iteration.

Both objects end in :func:`atomic_closure`.  The closure is deterministic and
does not depend on the continuous method that produced the intention matrix.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, minimize

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    argmax_round,
    repair_assignment_augmenting,
)
from viu_mrob_tfm.sp1_n3.worlds import World


POPULATION_METHODS = ("replicator", "smith", "bnn", "logit")


@dataclass(frozen=True, slots=True)
class PopulationResult:
    method: str
    x: np.ndarray
    history: pd.DataFrame
    converged: bool
    stop_reason: str
    iterations: int
    runtime_ms: float
    potential: float
    continuous_deficit: float
    continuous_distance: float
    fixed_point_residual: float
    potential_monotone: bool
    minimum_positive_correlation: float
    simplex_violation: float
    support_reactivated: bool
    consensus_residual: float
    messages: int
    bytes_sent: int
    information_mode: str


@dataclass(frozen=True, slots=True)
class AtomicClosureResult:
    assignment: np.ndarray
    feasible: bool
    deficit: float
    distance: float
    excess_capacity: float
    initial_assignment: np.ndarray
    robots_changed: int
    recovery_operations: int
    augmentations: int
    maximum_chain_length: int
    nodes_explored: int
    failure_reason: str


@dataclass(frozen=True, slots=True)
class VGNESolution:
    method: str
    x: np.ndarray
    dual: np.ndarray
    history: pd.DataFrame
    converged: bool
    stop_reason: str
    iterations: int
    runtime_ms: float
    objective: float
    primal_residual: float
    dual_residual: float
    complementarity_residual: float
    stationarity_residual: float
    consensus_residual: float
    kkt_residual: float
    messages: int
    bytes_sent: int
    simplex_violation: float


def _validate_world(world: World) -> None:
    if world.n_robots < 1 or world.n_loads < 1:
        raise ValueError("N4 requires at least one robot and one load")
    if np.any(world.capacities < 0.0) or np.any(world.demands <= 0.0):
        raise ValueError("capacities must be nonnegative and demands positive")
    if world.distances.shape != (world.n_robots, world.n_loads):
        raise ValueError("distance matrix has an invalid shape")


def initial_simplex(world: World) -> np.ndarray:
    """Uniform interior intention over every load plus the idle strategy."""

    _validate_world(world)
    return np.full(
        (world.n_robots, world.n_loads + 1),
        1.0 / (world.n_loads + 1),
        dtype=float,
    )


def project_simplex(vector: np.ndarray) -> np.ndarray:
    """Euclidean projection of one vector onto the probability simplex."""

    values = np.asarray(vector, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("simplex projection expects a nonempty vector")
    ordered = np.sort(values)[::-1]
    cumulative = np.cumsum(ordered) - 1.0
    positive = np.flatnonzero(
        ordered - cumulative / np.arange(1, len(values) + 1) > 0.0
    )
    if positive.size == 0:
        return np.full_like(values, 1.0 / len(values))
    rho = int(positive[-1])
    theta = cumulative[rho] / float(rho + 1)
    return np.maximum(values - theta, 0.0)


def project_simplex_rows(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("row projection expects a matrix")
    if values.shape[1] == 0:
        raise ValueError("simplex rows cannot be empty")
    ordered = np.sort(values, axis=1)[:, ::-1]
    cumulative = np.cumsum(ordered, axis=1) - 1.0
    divisors = np.arange(1, values.shape[1] + 1, dtype=float)[None, :]
    positive = ordered - cumulative / divisors > 0.0
    rho = np.maximum(np.sum(positive, axis=1) - 1, 0)
    theta = cumulative[np.arange(values.shape[0]), rho] / (rho + 1.0)
    return np.maximum(values - theta[:, None], 0.0)


def _normalized_problem(world: World) -> tuple[np.ndarray, np.ndarray]:
    capacity_ratio = world.capacities[:, None] / np.maximum(
        world.demands[None, :], 1e-12
    )
    distance_scale = max(float(np.max(world.distances)), 1e-12)
    normalized_distance = world.distances / distance_scale
    return capacity_ratio, normalized_distance


def population_potential_and_fitness(
    world: World,
    x: np.ndarray,
    *,
    deficit_penalty: float = 24.0,
    distance_weight: float = 1.0,
) -> tuple[float, np.ndarray, Mapping[str, float]]:
    """Return the common F-II potential, its gradient and diagnostics.

    The normalized residual is ``r_k=[1-Q_k/m_k]_+`` and

    ``Phi=-alpha/2 ||r||^2 - beta/N sum(dbar_ik x_ik)``.

    The squared hinge is continuously differentiable and has exactly zero
    derivative once a load is covered.  It is a penalty relaxation, not an
    exact representation of the lexicographic atomic objective.
    """

    _validate_world(world)
    state = np.asarray(x, dtype=float)
    expected = (world.n_robots, world.n_loads + 1)
    if state.shape != expected:
        raise ValueError(f"x must have shape {expected}")
    if deficit_penalty <= 0.0 or distance_weight < 0.0:
        raise ValueError("potential weights must be nonnegative")
    ratio, normalized_distance = _normalized_problem(world)
    coverage_ratio = np.sum(ratio * state[:, : world.n_loads], axis=0)
    residual = np.maximum(1.0 - coverage_ratio, 0.0)
    normalized_travel = float(
        np.sum(normalized_distance * state[:, : world.n_loads]) / world.n_robots
    )
    potential = float(
        -0.5 * deficit_penalty * np.dot(residual, residual)
        - distance_weight * normalized_travel
    )
    fitness = np.zeros_like(state)
    fitness[:, : world.n_loads] = (
        deficit_penalty * ratio * residual[None, :]
        - distance_weight * normalized_distance / world.n_robots
    )
    coverage = np.sum(
        world.capacities[:, None] * state[:, : world.n_loads], axis=0
    )
    diagnostics = {
        "continuous_deficit": float(
            np.sum(np.maximum(world.demands - coverage, 0.0))
        ),
        "normalized_deficit": float(np.sum(residual)),
        "continuous_distance": float(
            np.sum(world.distances * state[:, : world.n_loads])
        ),
    }
    return potential, fitness, diagnostics


def population_direction(
    method: str,
    x: np.ndarray,
    fitness: np.ndarray,
    *,
    temperature: float,
) -> np.ndarray:
    """Continuous-time revision field used by one F-II method."""

    if method not in POPULATION_METHODS:
        raise KeyError(f"unknown F-II method: {method}")
    state = np.asarray(x, dtype=float)
    payoff = np.asarray(fitness, dtype=float)
    if state.shape != payoff.shape:
        raise ValueError("state and fitness must have the same shape")
    if method == "replicator":
        mean = np.sum(state * payoff, axis=1, keepdims=True)
        return state * (payoff - mean)
    if method == "smith":
        result = np.zeros_like(state)
        for robot in range(state.shape[0]):
            difference = payoff[robot, :, None] - payoff[robot, None, :]
            positive = np.maximum(difference, 0.0)
            inbound = positive @ state[robot]
            outbound = state[robot] * np.sum(positive, axis=0)
            result[robot] = inbound - outbound
        return result
    if method == "bnn":
        mean = np.sum(state * payoff, axis=1, keepdims=True)
        excess = np.maximum(payoff - mean, 0.0)
        return excess - state * np.sum(excess, axis=1, keepdims=True)
    if temperature <= 0.0:
        raise ValueError("Logit temperature must be positive")
    scaled = payoff / temperature
    scaled -= np.max(scaled, axis=1, keepdims=True)
    target = np.exp(np.clip(scaled, -700.0, 0.0))
    target /= np.maximum(np.sum(target, axis=1, keepdims=True), 1e-300)
    return target - state


def _simplex_violation(x: np.ndarray) -> float:
    return float(
        max(
            np.max(np.abs(np.sum(x, axis=1) - 1.0)),
            np.max(np.maximum(-x, 0.0)),
        )
    )


def run_population_game(
    world: World,
    method: str,
    *,
    initial_x: np.ndarray | None = None,
    deficit_penalty: float = 24.0,
    distance_weight: float = 1.0,
    step: float = 0.08,
    temperature: float = 0.08,
    max_iterations: int = 4_000,
    tolerance: float = 1e-7,
    history_stride: int = 20,
) -> PopulationResult:
    """Integrate one F-II revision field under common numerical rules."""

    if method not in POPULATION_METHODS:
        raise KeyError(f"unknown F-II method: {method}")
    if step <= 0.0 or max_iterations < 1 or tolerance <= 0.0:
        raise ValueError("invalid integration parameters")
    x = initial_simplex(world) if initial_x is None else project_simplex_rows(initial_x)
    initial_support = x > 1e-14
    history: list[dict[str, float | int]] = []
    converged = False
    stop_reason = "max_iterations"
    started = time.perf_counter()
    minimum_correlation = math.inf
    potentials: list[float] = []
    fixed_residual = math.inf

    for iteration in range(max_iterations + 1):
        potential, fitness, diagnostics = population_potential_and_fitness(
            world,
            x,
            deficit_penalty=deficit_penalty,
            distance_weight=distance_weight,
        )
        direction = population_direction(
            method, x, fitness, temperature=temperature
        )
        fixed_residual = float(np.linalg.norm(direction) / math.sqrt(x.size))
        correlation = float(np.sum(fitness * direction))
        minimum_correlation = min(minimum_correlation, correlation)
        potentials.append(potential)
        if iteration % history_stride == 0 or fixed_residual <= tolerance:
            history.append(
                {
                    "iteration": iteration,
                    "potential": potential,
                    "continuous_deficit": diagnostics["continuous_deficit"],
                    "normalized_deficit": diagnostics["normalized_deficit"],
                    "continuous_distance": diagnostics["continuous_distance"],
                    "fixed_point_residual": fixed_residual,
                    "positive_correlation": correlation,
                    "simplex_violation": _simplex_violation(x),
                }
            )
        if fixed_residual <= tolerance:
            converged = True
            stop_reason = "fixed_point"
            break
        if iteration >= max_iterations:
            break

        if method == "replicator":
            local_step = step
            candidate = x * np.exp(np.clip(local_step * fitness, -60.0, 60.0))
            candidate /= np.maximum(np.sum(candidate, axis=1, keepdims=True), 1e-15)
        else:
            local_step = min(step, 1.0) if method == "logit" else step
            candidate = project_simplex_rows(x + local_step * direction)

        # Positive-correlation dynamics should not lose the potential merely
        # because Euler used a step that is too large.  Logit targets a
        # perturbed equilibrium and is therefore audited without this guard.
        if method != "logit":
            candidate_potential, _, _ = population_potential_and_fitness(
                world,
                candidate,
                deficit_penalty=deficit_penalty,
                distance_weight=distance_weight,
            )
            backtracks = 0
            while candidate_potential < potential - 1e-12 and backtracks < 20:
                local_step *= 0.5
                if method == "replicator":
                    candidate = x * np.exp(
                        np.clip(local_step * fitness, -60.0, 60.0)
                    )
                    candidate /= np.maximum(
                        np.sum(candidate, axis=1, keepdims=True), 1e-15
                    )
                else:
                    candidate = project_simplex_rows(x + local_step * direction)
                candidate_potential, _, _ = population_potential_and_fitness(
                    world,
                    candidate,
                    deficit_penalty=deficit_penalty,
                    distance_weight=distance_weight,
                )
                backtracks += 1
        x = candidate
        if not np.all(np.isfinite(x)) or _simplex_violation(x) > 1e-8:
            stop_reason = "invalid_state"
            break

    final_potential, _, diagnostics = population_potential_and_fitness(
        world,
        x,
        deficit_penalty=deficit_penalty,
        distance_weight=distance_weight,
    )
    monotone = bool(
        all(later >= earlier - 1e-10 for earlier, later in zip(potentials, potentials[1:]))
    )
    support_reactivated = bool(np.any((~initial_support) & (x > 1e-10)))
    return PopulationResult(
        method=method,
        x=x.copy(),
        history=pd.DataFrame(history),
        converged=converged,
        stop_reason=stop_reason,
        iterations=int(history[-1]["iteration"] if history else 0),
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        potential=final_potential,
        continuous_deficit=diagnostics["continuous_deficit"],
        continuous_distance=diagnostics["continuous_distance"],
        fixed_point_residual=fixed_residual,
        potential_monotone=monotone,
        minimum_positive_correlation=float(minimum_correlation),
        simplex_violation=_simplex_violation(x),
        support_reactivated=support_reactivated,
        consensus_residual=0.0,
        messages=0,
        bytes_sent=0,
        information_mode="exact_aggregate_reference",
    )


def run_distributed_population_game(
    world: World,
    adjacency: np.ndarray,
    method: str,
    *,
    initial_x: np.ndarray | None = None,
    deficit_penalty: float = 24.0,
    distance_weight: float = 1.0,
    step: float = 0.04,
    temperature: float = 0.15,
    max_iterations: int = 4_000,
    tolerance: float = 2e-4,
    consensus_tolerance: float = 2e-4,
    history_stride: int = 20,
) -> PopulationResult:
    """Run F-II with a dynamic-average-consensus estimate of ``Q_k(x)``.

    Each robot tracks its own normalized contribution and sends one ``K``
    vector to every neighbour per digital iteration.  The theoretical
    positive-correlation statements still refer to the exact aggregate field;
    this routine records the mismatch introduced by the information layer.
    """

    if method not in POPULATION_METHODS:
        raise KeyError(f"unknown F-II method: {method}")
    weights = metropolis_weights(adjacency)
    n, k = world.n_robots, world.n_loads
    ratio, normalized_distance = _normalized_problem(world)
    x = initial_simplex(world) if initial_x is None else project_simplex_rows(initial_x)
    initial_support = x > 1e-14

    def contribution(state: np.ndarray) -> np.ndarray:
        return ratio * state[:, :k]

    tracker = contribution(x)
    history: list[dict[str, float | int]] = []
    started = time.perf_counter()
    converged = False
    stop_reason = "max_iterations"
    minimum_correlation = math.inf
    potentials: list[float] = []
    fixed_residual = math.inf
    consensus_residual = math.inf
    iterations = 0

    for iteration in range(max_iterations + 1):
        exact_potential, exact_fitness, diagnostics = population_potential_and_fitness(
            world,
            x,
            deficit_penalty=deficit_penalty,
            distance_weight=distance_weight,
        )
        true_coverage = np.sum(contribution(x), axis=0)
        estimated_coverage = n * tracker
        consensus_residual = float(
            np.linalg.norm(estimated_coverage - true_coverage[None, :])
            / (1.0 + np.linalg.norm(true_coverage))
        )
        local_residual = np.maximum(1.0 - estimated_coverage, 0.0)
        local_fitness = np.zeros_like(x)
        local_fitness[:, :k] = (
            deficit_penalty * ratio * local_residual
            - distance_weight * normalized_distance / n
        )
        direction = population_direction(
            method, x, local_fitness, temperature=temperature
        )
        fixed_residual = float(np.linalg.norm(direction) / math.sqrt(x.size))
        correlation = float(np.sum(exact_fitness * direction))
        minimum_correlation = min(minimum_correlation, correlation)
        potentials.append(exact_potential)
        if (
            iteration % history_stride == 0
            or (fixed_residual <= tolerance and consensus_residual <= consensus_tolerance)
        ):
            history.append(
                {
                    "iteration": iteration,
                    "potential": exact_potential,
                    "continuous_deficit": diagnostics["continuous_deficit"],
                    "normalized_deficit": diagnostics["normalized_deficit"],
                    "continuous_distance": diagnostics["continuous_distance"],
                    "fixed_point_residual": fixed_residual,
                    "positive_correlation": correlation,
                    "consensus_residual": consensus_residual,
                    "simplex_violation": _simplex_violation(x),
                }
            )
        if fixed_residual <= tolerance and consensus_residual <= consensus_tolerance:
            converged = True
            stop_reason = "fixed_point_and_consensus"
            iterations = iteration
            break
        if iteration >= max_iterations:
            iterations = iteration
            break

        if method == "replicator":
            candidate = x * np.exp(np.clip(step * local_fitness, -60.0, 60.0))
            candidate /= np.maximum(candidate.sum(axis=1, keepdims=True), 1e-15)
        else:
            integration = min(step, 1.0) if method == "logit" else step
            candidate = project_simplex_rows(x + integration * direction)
        previous_contribution = contribution(x)
        new_contribution = contribution(candidate)
        tracker = weights @ tracker + new_contribution - previous_contribution
        x = candidate
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(tracker)):
            stop_reason = "numerical_failure"
            iterations = iteration + 1
            break

    final_potential, _, diagnostics = population_potential_and_fitness(
        world,
        x,
        deficit_penalty=deficit_penalty,
        distance_weight=distance_weight,
    )
    undirected_edges = int(np.sum(np.asarray(adjacency, dtype=bool)) // 2)
    messages = 2 * undirected_edges * iterations
    bytes_sent = messages * k * 8
    return PopulationResult(
        method=method,
        x=x.copy(),
        history=pd.DataFrame(history),
        converged=converged,
        stop_reason=stop_reason,
        iterations=iterations,
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        potential=final_potential,
        continuous_deficit=diagnostics["continuous_deficit"],
        continuous_distance=diagnostics["continuous_distance"],
        fixed_point_residual=fixed_residual,
        potential_monotone=bool(
            all(
                later >= earlier - 1e-10
                for earlier, later in zip(potentials, potentials[1:])
            )
        ),
        minimum_positive_correlation=float(minimum_correlation),
        simplex_violation=_simplex_violation(x),
        support_reactivated=bool(np.any((~initial_support) & (x > 1e-10))),
        consensus_residual=consensus_residual,
        messages=messages,
        bytes_sent=bytes_sent,
        information_mode="dynamic_average_consensus",
    )


def as_scalar_resource_world(world: World) -> ResourceWorld:
    """Represent the scalar N4 world for the common integer recovery code."""

    _validate_world(world)
    n = world.n_robots
    return ResourceWorld(
        seed=world.seed,
        robot_positions_m=world.robot_positions.copy(),
        load_positions_m=world.load_positions.copy(),
        resources=world.capacities[:, None].copy(),
        requirements=world.demands[:, None].copy(),
        battery_energy=np.full(n, 1e9, dtype=float),
        max_speed_mps=np.ones(n, dtype=float),
        energy_per_m=np.zeros(n, dtype=float),
        robot_classes=tuple("scalar" for _ in range(n)),
        feasibility_witness=np.full(n, -1, dtype=int),
        world_hash=world.digest(),
    )


def _assignment_metrics(world: World, assignment: np.ndarray) -> tuple[bool, float, float, float]:
    coverage = np.zeros(world.n_loads, dtype=float)
    distance = 0.0
    for robot, load in enumerate(np.asarray(assignment, dtype=int)):
        if load >= 0:
            coverage[load] += world.capacities[robot]
            distance += world.distances[robot, load]
    deficit = float(np.sum(np.maximum(world.demands - coverage, 0.0)))
    excess = float(np.sum(np.maximum(coverage - world.demands, 0.0)))
    return deficit <= 1e-8, deficit, float(distance), excess


def atomic_closure(
    world: World,
    x: np.ndarray,
    *,
    max_chain_length: int = 8,
    max_nodes_per_augmentation: int = 5_000,
    candidates_per_load: int = 16,
) -> AtomicClosureResult:
    """Apply the one deterministic atomic closure shared by F-II and F-III."""

    state = np.asarray(x, dtype=float)
    if state.shape == (world.n_robots, world.n_loads + 1):
        load_mass = state[:, : world.n_loads]
    elif state.shape == (world.n_robots, world.n_loads):
        load_mass = state
    else:
        raise ValueError("continuous state has an invalid shape")
    initial = argmax_round(load_mass)
    resource_world = as_scalar_resource_world(world)
    recovered = repair_assignment_augmenting(
        resource_world,
        initial,
        world.distances,
        max_chain_length=max_chain_length,
        max_nodes_per_augmentation=max_nodes_per_augmentation,
        candidates_per_load=candidates_per_load,
    )
    final = recovered.integer.assignment.copy()
    feasible, deficit, distance, excess = _assignment_metrics(world, final)
    operations = (
        recovered.augmentations
        + recovered.integer.pruned
        + recovered.integer.exchanges
    )
    return AtomicClosureResult(
        assignment=final,
        feasible=feasible,
        deficit=deficit,
        distance=distance,
        excess_capacity=excess,
        initial_assignment=initial,
        robots_changed=int(np.sum(initial != final)),
        recovery_operations=int(operations),
        augmentations=int(recovered.augmentations),
        maximum_chain_length=int(recovered.maximum_chain_length),
        nodes_explored=int(recovered.nodes_explored),
        failure_reason=str(recovered.failure_reason),
    )


def _vgne_objective(
    world: World, x: np.ndarray, regularization: float
) -> float:
    _, normalized_distance = _normalized_problem(world)
    return float(
        np.sum(normalized_distance * x[:, : world.n_loads]) / world.n_robots
        + 0.5 * regularization * np.sum(x * x)
    )


def _vgne_gradient(
    world: World,
    x: np.ndarray,
    dual: np.ndarray,
    regularization: float,
) -> np.ndarray:
    ratio, normalized_distance = _normalized_problem(world)
    gradient = regularization * np.asarray(x, dtype=float)
    gradient[:, : world.n_loads] += normalized_distance / world.n_robots
    gradient[:, : world.n_loads] -= ratio * dual[None, :]
    return gradient


def vgnekkt_residuals(
    world: World,
    x: np.ndarray,
    dual: np.ndarray,
    *,
    regularization: float,
    consensus_residual: float = 0.0,
) -> dict[str, float]:
    """Projected KKT residuals for the regularized shared-constraint game."""

    state = np.asarray(x, dtype=float)
    price = np.asarray(dual, dtype=float)
    ratio, normalized_distance = _normalized_problem(world)
    g = 1.0 - np.sum(ratio * state[:, : world.n_loads], axis=0)
    primal = float(np.linalg.norm(np.maximum(g, 0.0)))
    dual_feasibility = float(np.linalg.norm(np.minimum(price, 0.0)))
    complementarity = float(np.linalg.norm(price * g))
    gradient = _vgne_gradient(world, state, price, regularization)
    projected = project_simplex_rows(state - gradient)
    stationarity = float(np.linalg.norm(state - projected) / math.sqrt(state.size))
    total = float(
        math.sqrt(
            primal * primal
            + dual_feasibility * dual_feasibility
            + complementarity * complementarity
            + stationarity * stationarity
            + consensus_residual * consensus_residual
        )
    )
    return {
        "primal": primal,
        "dual": dual_feasibility,
        "complementarity": complementarity,
        "stationarity": stationarity,
        "consensus": float(consensus_residual),
        "kkt": total,
    }


def _estimate_dual(
    world: World,
    x: np.ndarray,
    regularization: float,
) -> np.ndarray:
    k = world.n_loads

    def objective(vector: np.ndarray) -> float:
        residuals = vgnekkt_residuals(
            world, x, vector, regularization=regularization
        )
        return float(
            residuals["stationarity"] ** 2
            + residuals["complementarity"] ** 2
            + residuals["dual"] ** 2
        )

    estimate = minimize(
        objective,
        np.zeros(k, dtype=float),
        method="L-BFGS-B",
        bounds=[(0.0, None)] * k,
        options={"maxiter": 2_000, "ftol": 1e-15},
    )
    return np.maximum(np.asarray(estimate.x, dtype=float), 0.0)


def solve_central_vgne(
    world: World,
    *,
    regularization: float = 0.02,
    max_iterations: int = 4_000,
    tolerance: float = 1e-10,
    kkt_tolerance: float = 1e-4,
) -> VGNESolution:
    """Solve the convex regularized F-III reference and audit its KKT point."""

    if regularization <= 0.0:
        raise ValueError("regularization must be positive")
    _validate_world(world)
    n, k = world.n_robots, world.n_loads
    ratio, normalized_distance = _normalized_problem(world)
    size = n * (k + 1)
    initial = initial_simplex(world).reshape(-1)
    row_matrix = np.zeros((n, size), dtype=float)
    for robot in range(n):
        row_matrix[robot, robot * (k + 1) : (robot + 1) * (k + 1)] = 1.0
    coverage_matrix = np.zeros((k, size), dtype=float)
    for load in range(k):
        for robot in range(n):
            coverage_matrix[load, robot * (k + 1) + load] = ratio[robot, load]
    constraints = [
        LinearConstraint(row_matrix, np.ones(n), np.ones(n)),
        LinearConstraint(coverage_matrix, np.ones(k), np.full(k, np.inf)),
    ]

    def unpack(vector: np.ndarray) -> np.ndarray:
        return np.asarray(vector, dtype=float).reshape(n, k + 1)

    def objective(vector: np.ndarray) -> float:
        return _vgne_objective(world, unpack(vector), regularization)

    def gradient(vector: np.ndarray) -> np.ndarray:
        state = unpack(vector)
        result = regularization * state
        result[:, :k] += normalized_distance / n
        return result.reshape(-1)

    started = time.perf_counter()
    solution = minimize(
        objective,
        initial,
        jac=gradient,
        method="SLSQP",
        bounds=Bounds(np.zeros(size), np.ones(size)),
        constraints=constraints,
        options={
            "maxiter": int(max_iterations),
            "ftol": float(tolerance),
            "disp": False,
        },
    )
    x = project_simplex_rows(unpack(solution.x))
    dual = _estimate_dual(world, x, regularization)
    residuals = vgnekkt_residuals(
        world, x, dual, regularization=regularization
    )
    success = bool(solution.success and residuals["kkt"] <= kkt_tolerance)
    history = pd.DataFrame(
        [
            {
                "iteration": int(getattr(solution, "nit", 0)),
                "objective": objective(x.reshape(-1)),
                **residuals,
            }
        ]
    )
    return VGNESolution(
        method="central_vgne_reference",
        x=x,
        dual=dual,
        history=history,
        converged=success,
        stop_reason="kkt_tolerance" if success else str(solution.message),
        iterations=int(getattr(solution, "nit", 0)),
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        objective=_vgne_objective(world, x, regularization),
        primal_residual=residuals["primal"],
        dual_residual=residuals["dual"],
        complementarity_residual=residuals["complementarity"],
        stationarity_residual=residuals["stationarity"],
        consensus_residual=0.0,
        kkt_residual=residuals["kkt"],
        messages=0,
        bytes_sent=0,
        simplex_violation=_simplex_violation(x),
    )


def metropolis_weights(adjacency: np.ndarray) -> np.ndarray:
    graph = np.asarray(adjacency, dtype=bool)
    if graph.ndim != 2 or graph.shape[0] != graph.shape[1]:
        raise ValueError("adjacency must be square")
    if not np.array_equal(graph, graph.T) or np.any(np.diag(graph)):
        raise ValueError("adjacency must be undirected without self loops")
    degrees = np.sum(graph, axis=1)
    weights = np.zeros(graph.shape, dtype=float)
    for left in range(len(graph)):
        for right in np.flatnonzero(graph[left]):
            weights[left, right] = 1.0 / (1.0 + max(degrees[left], degrees[right]))
        weights[left, left] = 1.0 - np.sum(weights[left])
    return weights


def run_distributed_vgne(
    world: World,
    adjacency: np.ndarray,
    *,
    regularization: float = 0.02,
    primal_step: float = 0.08,
    dual_step: float = 0.025,
    max_iterations: int = 8_000,
    tolerance: float = 2e-4,
    history_stride: int = 25,
) -> VGNESolution:
    """Projected distributed primal--dual pilot with dual consensus and DAC.

    The routine is an auditable implementation candidate.  Its ``converged``
    flag means that the five recorded residuals crossed the configured
    tolerance; it is not a theorem of convergence for arbitrary graphs.
    """

    if regularization <= 0.0 or primal_step <= 0.0 or dual_step <= 0.0:
        raise ValueError("regularization and steps must be positive")
    n, k = world.n_robots, world.n_loads
    weights = metropolis_weights(adjacency)
    ratio, normalized_distance = _normalized_problem(world)
    x = initial_simplex(world)
    dual = np.zeros((n, k), dtype=float)

    def local_residual(state: np.ndarray) -> np.ndarray:
        return 1.0 / n - ratio * state[:, :k]

    tracker = local_residual(x)
    history: list[dict[str, float | int]] = []
    converged = False
    stop_reason = "max_iterations"
    started = time.perf_counter()
    residuals = {
        "primal": math.inf,
        "dual": math.inf,
        "complementarity": math.inf,
        "stationarity": math.inf,
        "consensus": math.inf,
        "kkt": math.inf,
    }
    rounds = 0

    for iteration in range(max_iterations + 1):
        mean_dual = np.mean(dual, axis=0)
        consensus = float(
            np.linalg.norm(dual - mean_dual[None, :])
            / (1.0 + np.linalg.norm(dual))
        )
        residuals = vgnekkt_residuals(
            world,
            x,
            mean_dual,
            regularization=regularization,
            consensus_residual=consensus,
        )
        if iteration % history_stride == 0 or residuals["kkt"] <= tolerance:
            history.append(
                {
                    "iteration": iteration,
                    "objective": _vgne_objective(world, x, regularization),
                    **residuals,
                    "simplex_violation": _simplex_violation(x),
                }
            )
        if residuals["kkt"] <= tolerance:
            converged = True
            stop_reason = "kkt_tolerance"
            rounds = iteration
            break
        if iteration >= max_iterations:
            rounds = iteration
            break

        mixed_dual = weights @ dual
        mixed_tracker = weights @ tracker
        gradient = np.empty_like(x)
        gradient[:] = regularization * x
        gradient[:, :k] += normalized_distance / n - ratio * mixed_dual
        predictor_x = project_simplex_rows(x - primal_step * gradient)
        predictor_local = local_residual(predictor_x)
        predictor_tracker = mixed_tracker + predictor_local - local_residual(x)
        predictor_dual = np.maximum(
            mixed_dual + dual_step * n * predictor_tracker, 0.0
        )

        predictor_gradient = regularization * predictor_x
        predictor_gradient[:, :k] += (
            normalized_distance / n - ratio * predictor_dual
        )
        new_x = project_simplex_rows(x - primal_step * predictor_gradient)
        new_local = local_residual(new_x)
        tracker = mixed_tracker + new_local - local_residual(x)
        dual = np.maximum(
            mixed_dual + dual_step * n * predictor_tracker, 0.0
        )
        x = new_x
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(dual)):
            stop_reason = "numerical_failure"
            rounds = iteration + 1
            break

    undirected_edges = int(np.sum(np.asarray(adjacency, dtype=bool)) // 2)
    directed_packets_per_round = 4 * undirected_edges  # predictor + corrector
    messages = directed_packets_per_round * rounds
    bytes_sent = messages * (2 * k) * 8
    mean_dual = np.mean(dual, axis=0)
    return VGNESolution(
        method="distributed_pd_vgne",
        x=x.copy(),
        dual=mean_dual.copy(),
        history=pd.DataFrame(history),
        converged=converged,
        stop_reason=stop_reason,
        iterations=rounds,
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        objective=_vgne_objective(world, x, regularization),
        primal_residual=residuals["primal"],
        dual_residual=residuals["dual"],
        complementarity_residual=residuals["complementarity"],
        stationarity_residual=residuals["stationarity"],
        consensus_residual=residuals["consensus"],
        kkt_residual=residuals["kkt"],
        messages=messages,
        bytes_sent=bytes_sent,
        simplex_violation=_simplex_violation(x),
    )


__all__ = [
    "POPULATION_METHODS",
    "AtomicClosureResult",
    "PopulationResult",
    "VGNESolution",
    "as_scalar_resource_world",
    "atomic_closure",
    "initial_simplex",
    "metropolis_weights",
    "population_direction",
    "population_potential_and_fitness",
    "project_simplex",
    "project_simplex_rows",
    "run_distributed_vgne",
    "run_distributed_population_game",
    "run_population_game",
    "solve_central_vgne",
    "vgnekkt_residuals",
]
