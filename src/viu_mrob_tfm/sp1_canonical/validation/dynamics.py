"""Graph-coupled primal--dual population dynamics for canonical SP1."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld, normalized_constraints
from viu_mrob_tfm.sp1_canonical.validation.solvers import evaluate_relaxed


@dataclass(frozen=True, slots=True)
class GraphInfo:
    name: str
    adjacency: np.ndarray
    edges: int
    lambda2: float
    lambda_max: float
    connected: bool


@dataclass(frozen=True, slots=True)
class DynamicResult:
    x: np.ndarray
    dual: np.ndarray
    history: pd.DataFrame
    iterations: int
    converged: bool
    runtime_s: float
    messages: int
    scalars_sent: int
    graph: GraphInfo
    integrator: str
    dual_disagreement_sum: float
    pre_projection_min: float
    negative_components_before_projection: int


def make_graph(world: ResourceWorld, topology: str, *, radius_m: float = 6.0) -> GraphInfo:
    n = world.n_robots
    adjacency = np.zeros((n, n), dtype=bool)
    if topology == "complete":
        adjacency[:] = True
        np.fill_diagonal(adjacency, False)
    elif topology == "star":
        adjacency[0, 1:] = True
        adjacency[1:, 0] = True
    elif topology == "ring":
        for i in range(n):
            adjacency[i, (i + 1) % n] = True
            adjacency[(i + 1) % n, i] = True
    elif topology == "path":
        for i in range(n - 1):
            adjacency[i, i + 1] = True
            adjacency[i + 1, i] = True
    elif topology == "grid":
        columns = max(1, int(math.ceil(math.sqrt(n))))
        for i in range(n):
            row_i, col_i = divmod(i, columns)
            for j in range(i + 1, n):
                row_j, col_j = divmod(j, columns)
                if abs(row_i - row_j) + abs(col_i - col_j) == 1:
                    adjacency[i, j] = adjacency[j, i] = True
    elif topology in {"rdisk", "near_disconnect"}:
        delta = world.robot_positions_m[:, None, :] - world.robot_positions_m[None, :, :]
        distances = np.linalg.norm(delta, axis=2)
        adjacency = (distances <= float(radius_m)) & (~np.eye(n, dtype=bool))
        if topology == "near_disconnect":
            adjacency[:] = False
            split = max(1, n // 2)
            adjacency[:split, :split] = True
            adjacency[split:, split:] = True
            np.fill_diagonal(adjacency, False)
            if split < n:
                adjacency[split - 1, split] = adjacency[split, split - 1] = True
    else:
        raise ValueError(f"Unknown graph topology: {topology}")
    adjacency = adjacency | adjacency.T
    np.fill_diagonal(adjacency, False)
    degrees = adjacency.sum(axis=1).astype(float)
    laplacian = np.diag(degrees) - adjacency.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    lambda2 = float(eigenvalues[1]) if n > 1 else 0.0
    return GraphInfo(
        name=topology,
        adjacency=adjacency,
        edges=int(np.sum(adjacency) // 2),
        lambda2=lambda2,
        lambda_max=float(eigenvalues[-1]) if eigenvalues.size else 0.0,
        connected=bool(n <= 1 or lambda2 > 1e-10),
    )


def metropolis_matrix(graph: GraphInfo) -> np.ndarray:
    adjacency = graph.adjacency
    degrees = adjacency.sum(axis=1)
    n = len(degrees)
    weights = np.zeros((n, n), dtype=float)
    for i, j in np.argwhere(adjacency):
        weights[i, j] = 1.0 / (1.0 + max(int(degrees[i]), int(degrees[j])))
    weights[np.diag_indices(n)] = 1.0 - weights.sum(axis=1)
    return weights


def estimate_operator_scale(world: ResourceWorld, costs: np.ndarray) -> float:
    finite = costs[np.isfinite(costs)]
    cost_scale = float(np.max(np.abs(finite))) if finite.size else 1.0
    normalized = normalized_constraints(world)
    return max(1.0, cost_scale + float(np.linalg.norm(normalized.reshape(world.n_robots, -1), ord=2)))


def run_population_dynamics(
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    *,
    distributed: bool,
    integrator: str = "mirror_prox",
    step: float = 0.08,
    max_iterations: int = 500,
    tolerance: float = 1e-3,
    primal_tolerance: float | None = None,
    consensus_tolerance: float | None = None,
    stationarity_tolerance: float | None = None,
    convergence_residual_mode: str = "absolute",
    comparison_feasibility_tolerance: float = 1e-6,
    entropy_tau: float = 0.01,
    consensus_gain: float = 1.0,
    lp_objective: float | None = None,
    use_integral_consensus: bool = True,
    history_stride: int = 1,
    initial_x: np.ndarray | None = None,
    initial_dual: np.ndarray | None = None,
) -> DynamicResult:
    """Execute a sampled primal--dual population dynamic.

    ``mirror_prox``, ``exponential`` and ``projected_euler`` preserve every
    robot simplex by construction. ``euler_pure`` deliberately exposes
    discretization violations and is used only by E3. ``explicit_euler`` is
    retained as a backwards-compatible alias for ``euler_pure``.
    """

    if integrator == "explicit_euler":
        integrator = "euler_pure"
    if integrator == "exponential_replicator":
        integrator = "exponential"
    if integrator not in {"euler_pure", "projected_euler", "exponential", "mirror_prox"}:
        raise ValueError(f"Unknown integrator: {integrator}")
    if convergence_residual_mode not in {"absolute", "relative"}:
        raise ValueError("convergence_residual_mode must be 'absolute' or 'relative'")
    if step <= 0.0 or max_iterations < 1:
        raise ValueError("step and max_iterations must be positive")
    if history_stride < 1:
        raise ValueError("history_stride must be positive")
    tolerance_primal = float(tolerance if primal_tolerance is None else primal_tolerance)
    tolerance_consensus = float(tolerance if consensus_tolerance is None else consensus_tolerance)
    tolerance_stationarity = float(tolerance if stationarity_tolerance is None else stationarity_tolerance)

    n, k = world.n_robots, world.n_loads
    q = k * world.requirements.shape[1]
    feasible = np.isfinite(costs)
    x = np.zeros((n, k + 1), dtype=float)
    if initial_x is None:
        for robot in range(n):
            strategies = np.flatnonzero(np.r_[feasible[robot], True])
            x[robot, strategies] = 1.0 / len(strategies)
    else:
        load_state = np.asarray(initial_x, dtype=float)
        if load_state.shape != (n, k):
            raise ValueError(f"initial_x must have shape {(n, k)}, got {load_state.shape}")
        if not np.all(np.isfinite(load_state)) or np.any(load_state < -1e-12):
            raise ValueError("initial_x must be finite and nonnegative")
        load_state = np.maximum(load_state, 0.0)
        load_state = np.where(feasible, load_state, 0.0)
        load_totals = load_state.sum(axis=1)
        if np.any(load_totals > 1.0 + 1e-8):
            raise ValueError("each initial_x row must sum to at most one")
        x[:, :k] = load_state
        x[:, k] = np.maximum(1.0 - load_totals, 0.0)
        x /= np.maximum(x.sum(axis=1, keepdims=True), 1e-15)
    dual_shape = (n, k, world.requirements.shape[1]) if distributed else (k, world.requirements.shape[1])
    if initial_dual is None:
        dual = np.zeros(dual_shape, dtype=float)
    else:
        dual = np.asarray(initial_dual, dtype=float).copy()
        if dual.shape != dual_shape:
            raise ValueError(f"initial_dual must have shape {dual_shape}, got {dual.shape}")
        if not np.all(np.isfinite(dual)) or np.any(dual < -1e-12):
            raise ValueError("initial_dual must be finite and nonnegative")
        dual = np.maximum(dual, 0.0)
    weights = metropolis_matrix(graph)
    if not 0.0 < consensus_gain <= 1.0:
        raise ValueError("consensus_gain must belong to (0, 1]")
    consensus_matrix = (1.0 - consensus_gain) * np.eye(n) + consensus_gain * weights
    degrees = graph.adjacency.sum(axis=1).astype(float)
    graph_laplacian = np.diag(degrees) - graph.adjacency.astype(float)
    normalized = normalized_constraints(world)
    finite_cost = costs[np.isfinite(costs)]
    cost_scale = max(float(np.max(finite_cost)) if finite_cost.size else 1.0, 1e-9)
    normalized_costs = np.where(feasible, costs / cost_scale, 0.0)
    history: list[dict[str, float | int | bool | str]] = []
    converged = False
    dual_disagreement_sum = 0.0
    pre_projection_global_min = math.inf
    negative_components_total = 0
    start = time.perf_counter()

    def local_residual(x_state: np.ndarray) -> np.ndarray:
        return 1.0 / n - normalized * x_state[:, :k, None]

    tracker = local_residual(x) if distributed else np.empty((0, k, world.requirements.shape[1]))

    def gradients(x_state: np.ndarray, dual_state: np.ndarray) -> np.ndarray:
        if distributed:
            load_gradient = normalized_costs - np.einsum("ikm,ikm->ik", dual_state, normalized)
        else:
            load_gradient = normalized_costs - np.einsum("km,ikm->ik", dual_state, normalized)
        full = np.column_stack([load_gradient, np.zeros(n)])
        entropy = entropy_tau * (np.log(np.maximum(x_state, 1e-15)) + 1.0)
        full += entropy
        full[:, :k] = np.where(feasible, full[:, :k], 0.0)
        return full

    def exp_step(x_state: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        exponent = np.clip(-step * gradient, -60.0, 60.0)
        candidate = x_state * np.exp(exponent)
        candidate[:, :k] = np.where(feasible, candidate[:, :k], 0.0)
        totals = candidate.sum(axis=1, keepdims=True)
        return candidate / np.maximum(totals, 1e-15)

    def euler_step(x_state: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        mean_gradient = np.sum(x_state * gradient, axis=1, keepdims=True)
        return x_state + step * x_state * (mean_gradient - gradient)

    def project_simplex(vector: np.ndarray) -> np.ndarray:
        ordered = np.sort(vector)[::-1]
        cumulative = np.cumsum(ordered) - 1.0
        indices = np.arange(1, len(vector) + 1)
        positive = np.flatnonzero(ordered - cumulative / indices > 0.0)
        if positive.size == 0:
            return np.full_like(vector, 1.0 / len(vector))
        rho = int(positive[-1])
        theta = cumulative[rho] / float(rho + 1)
        return np.maximum(vector - theta, 0.0)

    def projected_euler_step(x_state: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        raw = euler_step(x_state, gradient)
        candidate = np.zeros_like(raw)
        for robot in range(n):
            valid = np.r_[feasible[robot], True]
            candidate[robot, valid] = project_simplex(raw[robot, valid])
        return candidate

    def primal_step(x_state: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        if integrator == "euler_pure":
            return euler_step(x_state, gradient)
        if integrator == "projected_euler":
            return projected_euler_step(x_state, gradient)
        return exp_step(x_state, gradient)

    def pre_projection_diagnostics(x_state: np.ndarray, gradient: np.ndarray) -> tuple[float, int]:
        if integrator not in {"euler_pure", "projected_euler"}:
            return math.nan, 0
        raw = euler_step(x_state, gradient)
        valid = np.column_stack([feasible, np.ones(n, dtype=bool)])
        values = raw[valid]
        return float(np.min(values)), int(np.sum(values < 0.0))

    def central_dual_step(base_dual: np.ndarray, x_state: np.ndarray) -> np.ndarray:
        coverage = np.einsum("ik,ikm->km", x_state[:, :k], normalized)
        return np.maximum(base_dual + step * (1.0 - coverage), 0.0)

    for iteration in range(max_iterations + 1):
        metrics = evaluate_relaxed(world, x[:, :k], costs)
        normalized_coverage = np.einsum("ik,ikm->km", x[:, :k], normalized)
        normalized_primal = float(np.linalg.norm(np.maximum(1.0 - normalized_coverage, 0.0)))
        relative_primal = normalized_primal / (1.0 + float(np.linalg.norm(np.ones_like(normalized_coverage))))
        if distributed:
            mean_dual = np.mean(dual, axis=0)
            disagreement = dual - mean_dual[None, :, :]
            consensus_disagreement = float(np.linalg.norm(disagreement))
            laplacian_dual = np.einsum("ij,jkm->ikm", graph_laplacian, dual)
            consensus_residual = float(np.linalg.norm(laplacian_dual))
            relative_consensus = consensus_residual / (1.0 + float(np.linalg.norm(dual)))
        else:
            consensus_disagreement = 0.0
            consensus_residual = 0.0
            relative_consensus = 0.0
        gradient = gradients(x, dual)
        primal_candidate = primal_step(x, gradient)
        primal_fixed_point = float(np.linalg.norm(primal_candidate - x))
        primal_stationarity = primal_fixed_point / max(step, 1e-12)
        if distributed:
            static_tracker = np.einsum("ij,jkm->ikm", consensus_matrix, tracker)
            dual_candidate = np.maximum(
                np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * static_tracker,
                0.0,
            )
        else:
            dual_candidate = central_dual_step(dual, x)
        dual_fixed_point = float(np.linalg.norm(dual_candidate - dual))
        dual_stationarity = dual_fixed_point / max(step, 1e-12)
        stationarity = float(math.hypot(primal_stationarity, dual_stationarity))
        fixed_point_residual = float(math.hypot(primal_fixed_point, dual_fixed_point))
        state_norm = float(math.hypot(np.linalg.norm(x), np.linalg.norm(dual)))
        relative_stationarity = fixed_point_residual / (1.0 + state_norm)
        if convergence_residual_mode == "relative":
            stopping_primal = relative_primal
            stopping_consensus = relative_consensus
            stopping_stationarity = relative_stationarity
        else:
            stopping_primal = normalized_primal
            stopping_consensus = consensus_disagreement
            stopping_stationarity = stationarity
        gap = math.nan
        comparable_to_lp = bool(normalized_primal <= comparison_feasibility_tolerance)
        raw_gap = math.nan
        if lp_objective is not None and np.isfinite(lp_objective):
            raw_gap = float((metrics["objective"] - lp_objective) / max(abs(lp_objective), 1e-12))
        if comparable_to_lp and np.isfinite(raw_gap):
            gap = raw_gap
        pre_projection_min, negative_before_projection = pre_projection_diagnostics(x, gradient)
        dual_disagreement_sum += consensus_disagreement
        if np.isfinite(pre_projection_min):
            pre_projection_global_min = min(pre_projection_global_min, pre_projection_min)
        negative_components_total += negative_before_projection
        trace_row = {
                "iteration": iteration,
                "objective": metrics["objective"],
                "gap_lp": gap,
                "gap_lp_unfiltered": raw_gap,
                "comparable_to_lp": comparable_to_lp,
                "primal_residual": metrics["primal_residual"],
                "primal_residual_normalized": normalized_primal,
                "primal_residual_relative": relative_primal,
                "consensus_residual": consensus_residual,
                "consensus_disagreement_residual": consensus_disagreement,
                "consensus_residual_relative": relative_consensus,
                "stationarity_residual": stationarity,
                "fixed_point_residual": fixed_point_residual,
                "stationarity_residual_relative": relative_stationarity,
                "primal_stationarity_residual": primal_stationarity,
                "dual_stationarity_residual": dual_stationarity,
                "stopping_primal_residual": stopping_primal,
                "stopping_consensus_residual": stopping_consensus,
                "stopping_stationarity_residual": stopping_stationarity,
                "convergence_residual_mode": convergence_residual_mode,
                "min_x": metrics["min_x"],
                "simplex_violation": metrics["simplex_violation"],
                "pre_projection_min": pre_projection_min,
                "negative_components_before_projection": negative_before_projection,
            }
        should_record = bool(iteration % history_stride == 0 or iteration == max_iterations)
        if (
            stopping_primal <= tolerance_primal
            and stopping_consensus <= tolerance_consensus
            and stopping_stationarity <= tolerance_stationarity
        ):
            converged = True
            should_record = True
        if should_record:
            history.append(trace_row)
        if converged:
            break
        if iteration == max_iterations:
            break

        if integrator in {"euler_pure", "projected_euler"}:
            previous_x = x
            x = primal_step(x, gradient)
            if distributed:
                tracker = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker) + local_residual(x) - local_residual(previous_x)
                    if use_integral_consensus
                    else local_residual(x)
                )
                dual = np.maximum(np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker, 0.0)
            else:
                dual = central_dual_step(dual, x)
        elif integrator == "exponential":
            previous_x = x
            x = exp_step(x, gradient)
            if distributed:
                tracker = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker) + local_residual(x) - local_residual(previous_x)
                    if use_integral_consensus
                    else local_residual(x)
                )
                dual = np.maximum(np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker, 0.0)
            else:
                dual = central_dual_step(dual, x)
        else:
            x_predictor = exp_step(x, gradient)
            if distributed:
                tracker_predictor = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker) + local_residual(x_predictor) - local_residual(x)
                    if use_integral_consensus
                    else local_residual(x_predictor)
                )
                dual_predictor = np.maximum(
                    np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker_predictor,
                    0.0,
                )
            else:
                tracker_predictor = tracker
                dual_predictor = central_dual_step(dual, x)
            predictor_gradient = gradients(x_predictor, dual_predictor)
            previous_x = x
            x = exp_step(x, predictor_gradient)
            if distributed:
                tracker = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker) + local_residual(x) - local_residual(previous_x)
                    if use_integral_consensus
                    else local_residual(x)
                )
                dual = np.maximum(
                    np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker_predictor,
                    0.0,
                )
            else:
                dual = central_dual_step(dual, x_predictor)

        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(dual)):
            break

    runtime = time.perf_counter() - start
    # ``iteration`` is zero based.  Count evaluated states independently of
    # history thinning so communication accounting remains invariant.
    iterations = int(iteration + 1)
    exchanges = 2 if integrator == "mirror_prox" else 1
    messages = int(2 * graph.edges * exchanges * iterations) if distributed else 0
    scalars = int(messages * q)
    return DynamicResult(
        x=x[:, :k],
        dual=dual,
        history=pd.DataFrame(history),
        iterations=iterations,
        converged=converged,
        runtime_s=float(runtime),
        messages=messages,
        scalars_sent=scalars,
        graph=graph,
        integrator=integrator,
        dual_disagreement_sum=float(dual_disagreement_sum),
        pre_projection_min=float(pre_projection_global_min) if np.isfinite(pre_projection_global_min) else math.nan,
        negative_components_before_projection=int(negative_components_total),
    )


__all__ = [
    "DynamicResult",
    "GraphInfo",
    "estimate_operator_scale",
    "make_graph",
    "metropolis_matrix",
    "run_population_dynamics",
]
