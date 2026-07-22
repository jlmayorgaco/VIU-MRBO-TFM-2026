"""Central references and deterministic greedy baseline for SP1 resources."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp, minimize
from scipy.sparse import lil_matrix

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld


@dataclass(frozen=True, slots=True)
class AllocationSolution:
    x: np.ndarray
    objective: float
    status: int
    message: str
    mip_gap: float = math.nan
    raw_objective: float = math.nan
    regularized_objective: float = math.nan
    entropy: float = math.nan


def _constraint_matrices(world: ResourceWorld) -> tuple[np.ndarray, np.ndarray]:
    n, k = world.n_robots, world.n_loads
    rows = n + k * world.requirements.shape[1]
    matrix = np.zeros((rows, n * k), dtype=float)
    rhs = np.empty(rows, dtype=float)
    for robot in range(n):
        matrix[robot, robot * k : (robot + 1) * k] = 1.0
        rhs[robot] = 1.0
    row = n
    for load in range(k):
        for resource in range(world.requirements.shape[1]):
            for robot in range(n):
                matrix[row, robot * k + load] = -world.resources[robot, resource]
            rhs[row] = -world.requirements[load, resource]
            row += 1
    return matrix, rhs


def solve_lp(world: ResourceWorld, costs: np.ndarray) -> AllocationSolution:
    matrix, rhs = _constraint_matrices(world)
    finite_cost = np.where(np.isfinite(costs), costs, 0.0)
    bounds = [(0.0, 1.0 if np.isfinite(costs[i, load]) else 0.0) for i in range(world.n_robots) for load in range(world.n_loads)]
    result = linprog(finite_cost.reshape(-1), A_ub=matrix, b_ub=rhs, bounds=bounds, method="highs")
    x = np.zeros_like(costs) if result.x is None else np.asarray(result.x).reshape(costs.shape)
    objective = math.inf if result.fun is None else float(result.fun)
    entropy = allocation_entropy(x)
    return AllocationSolution(
        x=x,
        objective=objective,
        status=int(result.status),
        message=str(result.message),
        raw_objective=objective,
        regularized_objective=objective,
        entropy=entropy,
    )


def solve_milp(world: ResourceWorld, costs: np.ndarray, *, time_limit_s: float = 10.0) -> AllocationSolution:
    matrix, rhs = _constraint_matrices(world)
    finite_cost = np.where(np.isfinite(costs), costs, 0.0)
    upper = np.isfinite(costs).astype(float).reshape(-1)
    result = milp(
        finite_cost.reshape(-1),
        integrality=np.ones(world.n_robots * world.n_loads, dtype=int),
        bounds=Bounds(np.zeros_like(upper), upper),
        constraints=LinearConstraint(lil_matrix(matrix).tocsr(), np.full(len(rhs), -np.inf), rhs),
        options={"time_limit": float(time_limit_s)},
    )
    x = np.zeros_like(costs) if result.x is None else (np.asarray(result.x).reshape(costs.shape) > 0.5).astype(float)
    objective = math.inf if result.fun is None else float(result.fun)
    return AllocationSolution(
        x=x,
        objective=objective,
        status=int(result.status),
        message=str(result.message),
        mip_gap=float(getattr(result, "mip_gap", math.nan)),
        raw_objective=objective,
        regularized_objective=objective,
        entropy=allocation_entropy(x),
    )


def solve_regularized_lp(
    world: ResourceWorld,
    costs: np.ndarray,
    *,
    entropy_tau: float,
    max_iterations: int = 5_000,
    tolerance: float = 1e-10,
) -> AllocationSolution:
    """Solve the same entropy-regularized relaxation used by Rep-C/Rep-D.

    The scalar objective is ``C/c_scale @ x - tau H([x,idle])``.
    ``raw_objective`` always retains the unregularized travel cost ``C @ x``.
    """

    if entropy_tau < 0.0:
        raise ValueError("entropy_tau must be nonnegative")
    n, k = world.n_robots, world.n_loads
    lp = solve_lp(world, costs)
    finite = np.isfinite(costs)
    finite_values = costs[finite]
    cost_scale = max(float(np.max(finite_values)) if finite_values.size else 1.0, 1e-12)
    normalized_cost = np.where(finite, costs / cost_scale, 0.0)
    full_initial = np.column_stack([lp.x, np.maximum(1.0 - lp.x.sum(axis=1), 0.0)])
    full_initial /= np.maximum(full_initial.sum(axis=1, keepdims=True), 1e-15)
    initial = full_initial.reshape(-1)
    bounds: list[tuple[float, float]] = []
    for robot in range(n):
        bounds.extend((0.0, 1.0) if finite[robot, load] else (0.0, 0.0) for load in range(k))
        bounds.append((0.0, 1.0))

    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)

    def unpack(vector: np.ndarray) -> np.ndarray:
        return np.asarray(vector, dtype=float).reshape(n, k + 1)

    def objective(vector: np.ndarray) -> float:
        full = unpack(vector)
        probabilities = np.clip(full, 0.0, 1.0)
        entropy_term = float(np.sum(probabilities * np.log(np.maximum(probabilities, 1e-15))))
        return float(np.sum(normalized_cost * full[:, :k]) + entropy_tau * entropy_term)

    def gradient(vector: np.ndarray) -> np.ndarray:
        full = unpack(vector)
        result = entropy_tau * (np.log(np.maximum(full, 1e-15)) + 1.0)
        result[:, :k] += normalized_cost
        result[:, :k] = np.where(finite, result[:, :k], 0.0)
        return result.reshape(-1)

    constraints = [
        {
            "type": "eq",
            "fun": lambda vector: unpack(vector).sum(axis=1) - 1.0,
        },
        {
            "type": "ineq",
            "fun": lambda vector: np.einsum("ik,ikm->km", unpack(vector)[:, :k], normalized).reshape(-1) - 1.0,
        },
    ]
    result = minimize(
        objective,
        initial,
        jac=gradient,
        bounds=bounds,
        constraints=constraints,
        method="SLSQP",
        options={"maxiter": int(max_iterations), "ftol": float(tolerance), "disp": False},
    )
    full = unpack(result.x)
    x = full[:, :k]
    raw = float(np.sum(np.where(finite, costs, 0.0) * x))
    entropy = allocation_entropy(x)
    regularized = float(raw / cost_scale - entropy_tau * entropy)
    return AllocationSolution(
        x=x,
        objective=raw,
        status=0 if result.success else int(getattr(result, "status", 1)),
        message=str(result.message),
        raw_objective=raw,
        regularized_objective=regularized,
        entropy=entropy,
    )


def allocation_entropy(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    idle = np.maximum(1.0 - x.sum(axis=1), 0.0)
    full = np.column_stack([np.clip(x, 0.0, None), idle])
    return float(-np.sum(full * np.log(np.maximum(full, 1e-15))))


def evaluate_relaxed(world: ResourceWorld, x: np.ndarray, costs: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    coverage = np.einsum("ik,im->km", x, world.resources)
    deficit = np.maximum(world.requirements - coverage, 0.0)
    excess = np.maximum(coverage - world.requirements, 0.0)
    row_excess = np.maximum(x.sum(axis=1) - 1.0, 0.0)
    invalid_mass = float(np.sum(x[~np.isfinite(costs)]))
    safe_costs = np.where(np.isfinite(costs), costs, 0.0)
    nonnegative_violation = float(np.max(np.maximum(-x, 0.0)))
    simplex_violation = max(float(np.max(row_excess)), nonnegative_violation)
    return {
        "objective": float(np.sum(safe_costs * x)),
        "primal_residual": float(np.linalg.norm(deficit) + np.linalg.norm(row_excess) + invalid_mass),
        "deficit_l1": float(np.sum(deficit)),
        "excess_l1": float(np.sum(excess)),
        "row_violation": float(np.sum(row_excess)),
        "invalid_mass": invalid_mass,
        "min_x": float(np.min(x)),
        "simplex_violation": simplex_violation,
    }


def assignment_from_matrix(x: np.ndarray) -> np.ndarray:
    assignment = np.full(x.shape[0], -1, dtype=int)
    selected = np.argwhere(x > 0.5)
    for robot, load in selected:
        if assignment[int(robot)] < 0:
            assignment[int(robot)] = int(load)
    return assignment


def matrix_from_assignment(assignment: np.ndarray, n_loads: int) -> np.ndarray:
    x = np.zeros((len(assignment), n_loads), dtype=float)
    for robot, load in enumerate(np.asarray(assignment, dtype=int)):
        if 0 <= load < n_loads:
            x[robot, load] = 1.0
    return x


def greedy_deficit(world: ResourceWorld, costs: np.ndarray) -> AllocationSolution:
    assignment = np.full(world.n_robots, -1, dtype=int)
    x = matrix_from_assignment(assignment, world.n_loads)
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)
    for _ in range(world.n_robots):
        coverage = np.einsum("ik,ikm->km", x, normalized)
        deficit = np.maximum(1.0 - coverage, 0.0)
        if np.all(deficit <= 1e-9):
            break
        candidates: list[tuple[float, float, int, int]] = []
        for robot in np.flatnonzero(assignment < 0):
            for load in range(world.n_loads):
                if not np.isfinite(costs[robot, load]):
                    continue
                gain = float(np.sum(np.minimum(deficit[load], normalized[robot, load])))
                if gain > 1e-12:
                    candidates.append((-gain / max(float(costs[robot, load]), 1e-9), float(costs[robot, load]), int(robot), load))
        if not candidates:
            break
        _, _, robot, load = min(candidates)
        assignment[robot] = load
        x[robot, load] = 1.0
    metrics = evaluate_relaxed(world, x, costs)
    return AllocationSolution(x=x, objective=metrics["objective"], status=0 if metrics["primal_residual"] <= 1e-8 else 2, message="feasible" if metrics["primal_residual"] <= 1e-8 else "greedy_infeasible")


__all__ = [
    "AllocationSolution",
    "assignment_from_matrix",
    "evaluate_relaxed",
    "greedy_deficit",
    "matrix_from_assignment",
    "allocation_entropy",
    "solve_lp",
    "solve_milp",
    "solve_regularized_lp",
]
