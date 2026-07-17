"""Formal and executable objects for SP1.

Actions use ``0`` for inactivity and ``1..K`` for loads.  Costs and values are
dimensionless.  The finite exact-potential game, the continuous Smith
relaxation, and the integer closure are deliberately separate objects: a
successful closure is not evidence that the continuous relaxation reached an
integer equilibrium.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import exp
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True, slots=True)
class AllocationResult:
    assignment: np.ndarray
    runtime_s: float
    iterations: int = 1
    evaluations: int = 0
    converged: bool = True
    preferences: np.ndarray | None = None
    residual: float | None = None


def _validate_instance(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    costs = np.asarray(costs, dtype=float)
    quotas = np.asarray(quotas, dtype=int)
    if costs.ndim != 2 or costs.shape[0] < 1 or costs.shape[1] < 1:
        raise ValueError("costs must have shape (N, K)")
    if quotas.shape != (costs.shape[1],) or np.any(quotas < 1):
        raise ValueError("quotas must have shape (K,) and be positive integers")
    if not np.all(np.isfinite(costs)) or np.any(costs < 0.0):
        raise ValueError("costs must be finite and non-negative")
    if values is None:
        values = np.ones(costs.shape[1], dtype=float)
    values = np.asarray(values, dtype=float)
    if values.shape != quotas.shape or not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("values must have shape (K,) and be finite and non-negative")
    return costs, quotas, values


def _validate_assignment(assignment: np.ndarray, n_robots: int, n_loads: int) -> np.ndarray:
    assignment = np.asarray(assignment, dtype=int)
    if assignment.shape != (n_robots,):
        raise ValueError("assignment must have shape (N,)")
    if np.any(assignment < 0) or np.any(assignment > n_loads):
        raise ValueError("actions must belong to {0, ..., K}")
    return assignment


def linear_profile_metrics(
    costs: np.ndarray,
    quotas: np.ndarray,
    assignment: np.ndarray,
    lambda_deficit: float,
    lambda_excess: float,
) -> dict[str, float | int | bool | np.ndarray]:
    """Metrics and potential of the mandatory-load linear penalty game."""

    costs, quotas, _ = _validate_instance(costs, quotas)
    assignment = _validate_assignment(assignment, costs.shape[0], costs.shape[1])
    active = assignment > 0
    rows = np.flatnonzero(active)
    counts = np.bincount(assignment[active], minlength=costs.shape[1] + 1)[1:]
    social_cost = float(costs[rows, assignment[active] - 1].sum())
    deficit = int(np.maximum(quotas - counts, 0).sum())
    excess = int(np.maximum(counts - quotas, 0).sum())
    penalized = social_cost + lambda_deficit * deficit + lambda_excess * excess
    return {
        "counts": counts,
        "social_cost": social_cost,
        "deficit": deficit,
        "excess": excess,
        "exact": bool(np.array_equal(counts, quotas)),
        "penalized_cost": float(penalized),
        "potential": float(-penalized),
    }


def marginal_payoff(
    costs: np.ndarray,
    quotas: np.ndarray,
    assignment: np.ndarray,
    robot: int,
    lambda_deficit: float,
    lambda_excess: float,
) -> float:
    assignment = np.asarray(assignment, dtype=int)
    baseline = assignment.copy()
    baseline[robot] = 0
    return float(
        linear_profile_metrics(
            costs, quotas, assignment, lambda_deficit, lambda_excess
        )["potential"]
    ) - float(
        linear_profile_metrics(
            costs, quotas, baseline, lambda_deficit, lambda_excess
        )["potential"]
    )


def is_pure_nash(
    costs: np.ndarray,
    quotas: np.ndarray,
    assignment: np.ndarray,
    penalty: float,
    tolerance: float = 1e-12,
) -> bool:
    costs, quotas, _ = _validate_instance(costs, quotas)
    assignment = _validate_assignment(assignment, costs.shape[0], costs.shape[1])
    current = float(linear_profile_metrics(costs, quotas, assignment, penalty, penalty)["potential"])
    for robot in range(costs.shape[0]):
        for action in range(costs.shape[1] + 1):
            if action == assignment[robot]:
                continue
            candidate = assignment.copy()
            candidate[robot] = action
            value = float(linear_profile_metrics(costs, quotas, candidate, penalty, penalty)["potential"])
            if value > current + tolerance:
                return False
    return True


def enumerate_base_game(costs: np.ndarray, quotas: np.ndarray, penalty: float) -> dict[str, object]:
    """Enumerate small games and audit the Nash/exact-assignment identity."""

    costs, quotas, _ = _validate_instance(costs, quotas)
    n_robots, n_loads = costs.shape
    nash: list[np.ndarray] = []
    exact_count = 0
    profiles = 0
    for actions in product(range(n_loads + 1), repeat=n_robots):
        profiles += 1
        assignment = np.asarray(actions, dtype=int)
        metrics = linear_profile_metrics(costs, quotas, assignment, penalty, penalty)
        exact_count += int(metrics["exact"])
        if is_pure_nash(costs, quotas, assignment, penalty):
            nash.append(assignment)
    return {
        "profiles": profiles,
        "exact_profiles": exact_count,
        "nash_count": len(nash),
        "nash_profiles": nash,
        "identity_holds": len(nash) == exact_count
        and all(linear_profile_metrics(costs, quotas, a, penalty, penalty)["exact"] for a in nash),
    }


def quorum_benefit(q: float | np.ndarray, quota: int, beta: float) -> float | np.ndarray:
    """Normalized exponential quorum benefit, saturated after ``quota``.

    For beta>0 the discrete increments are strictly increasing before the
    quorum.  The beta=0 branch is its continuous linear limit.
    """

    if quota < 1 or beta < 0.0:
        raise ValueError("quota must be positive and beta non-negative")
    clipped = np.minimum(np.maximum(np.asarray(q, dtype=float), 0.0), float(quota))
    if beta <= 1e-12:
        result = clipped / float(quota)
    else:
        result = np.expm1(beta * clipped / float(quota)) / np.expm1(beta)
    if np.ndim(q) == 0:
        return float(result)
    return result


def quorum_potential(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    assignment: np.ndarray,
    beta: float,
    cost_weight: float,
    excess_penalty: float,
) -> float:
    costs, quotas, values = _validate_instance(costs, quotas, values)
    assignment = _validate_assignment(assignment, costs.shape[0], costs.shape[1])
    active = assignment > 0
    rows = np.flatnonzero(active)
    counts = np.bincount(assignment[active], minlength=costs.shape[1] + 1)[1:]
    benefit = sum(
        values[k] * float(quorum_benefit(counts[k], int(quotas[k]), beta))
        for k in range(costs.shape[1])
    )
    social_cost = float(costs[rows, assignment[active] - 1].sum())
    excess = int(np.maximum(counts - quotas, 0).sum())
    return float(benefit - cost_weight * social_cost - excess_penalty * excess)


def exact_coalition_oracle(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    cost_weight: float,
    time_limit_s: float = 5.0,
) -> AllocationResult:
    """MILP-Q oracle with exact all-or-nothing load activation."""

    costs, quotas, values = _validate_instance(costs, quotas, values)
    n_robots, n_loads = costs.shape
    n_x = n_robots * n_loads
    objective = np.concatenate([cost_weight * costs.ravel(), -values])
    rows: list[np.ndarray] = []
    lower: list[float] = []
    upper: list[float] = []
    for robot in range(n_robots):
        row = np.zeros(n_x + n_loads)
        row[robot * n_loads : (robot + 1) * n_loads] = 1.0
        rows.append(row)
        lower.append(-np.inf)
        upper.append(1.0)
    for load in range(n_loads):
        row = np.zeros(n_x + n_loads)
        row[load:n_x:n_loads] = 1.0
        row[n_x + load] = -float(quotas[load])
        rows.append(row)
        lower.append(0.0)
        upper.append(0.0)
    start = perf_counter()
    result = milp(
        c=objective,
        integrality=np.ones(n_x + n_loads),
        bounds=Bounds(np.zeros(n_x + n_loads), np.ones(n_x + n_loads)),
        constraints=LinearConstraint(np.vstack(rows), np.asarray(lower), np.asarray(upper)),
        options={"time_limit": float(time_limit_s)},
    )
    runtime = perf_counter() - start
    if result.x is None or int(result.status) not in {0, 1}:
        raise RuntimeError(f"MILP-Q failed with status={result.status}: {result.message}")
    matrix = np.asarray(result.x[:n_x]).reshape(n_robots, n_loads)
    assignment = np.zeros(n_robots, dtype=int)
    selected = np.argwhere(matrix > 0.5)
    assignment[selected[:, 0]] = selected[:, 1] + 1
    return AllocationResult(
        assignment=assignment,
        runtime_s=runtime,
        evaluations=n_x + n_loads,
        converged=int(result.status) == 0,
    )


def greedy_quorum(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    cost_weight: float,
) -> AllocationResult:
    """Central greedy baseline that accepts complete positive-value groups."""

    costs, quotas, values = _validate_instance(costs, quotas, values)
    start = perf_counter()
    assignment = np.zeros(costs.shape[0], dtype=int)
    free = np.ones(costs.shape[0], dtype=bool)
    iterations = 0
    evaluations = 0
    while True:
        candidates: list[tuple[float, int, np.ndarray]] = []
        for load, quota in enumerate(quotas):
            if np.any(assignment == load + 1) or int(free.sum()) < int(quota):
                continue
            robots = np.flatnonzero(free)
            order = robots[np.argsort(costs[robots, load], kind="stable")[: int(quota)]]
            score = float(values[load] - cost_weight * costs[order, load].sum())
            candidates.append((score, load, order))
            evaluations += len(robots)
        if not candidates:
            break
        score, load, robots = max(candidates, key=lambda item: (item[0], -item[1]))
        if score <= 0.0:
            break
        assignment[robots] = load + 1
        free[robots] = False
        iterations += 1
    return AllocationResult(assignment, perf_counter() - start, iterations, evaluations)


def project_simplex(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    order = np.sort(vector)[::-1]
    cumulative = np.cumsum(order)
    active = order * np.arange(1, vector.size + 1) > cumulative - 1.0
    rho = int(np.flatnonzero(active)[-1])
    theta = (cumulative[rho] - 1.0) / float(rho + 1)
    return np.maximum(vector - theta, 0.0)


def smith_preferences(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    *,
    beta: float,
    cost_weight: float,
    excess_penalty: float,
    seed: int,
    time_step: float,
    max_steps: int,
    tolerance: float,
) -> AllocationResult:
    """Sampled Smith relaxation over idle plus K load preferences.

    The action fitness uses the marginal quorum benefit evaluated at the
    aggregate continuous occupancy.  This is an executable relaxation, not a
    theorem that the sampled system inherits the finite-game Nash result.
    """

    costs, quotas, values = _validate_instance(costs, quotas, values)
    if time_step <= 0.0 or max_steps < 1 or tolerance <= 0.0:
        raise ValueError("invalid integration parameters")
    rng = np.random.default_rng(seed)
    n_robots, n_loads = costs.shape
    state = np.full((n_robots, n_loads + 1), 1.0 / (n_loads + 1))
    state = np.vstack(
        [project_simplex(row + rng.normal(0.0, 0.01, n_loads + 1)) for row in state]
    )
    start = perf_counter()
    residual = np.inf
    evaluations = 0
    for step in range(1, max_steps + 1):
        occupancy = state[:, 1:].sum(axis=0)
        fitness = np.zeros_like(state)
        for load in range(n_loads):
            q = float(occupancy[load])
            marginal = float(quorum_benefit(q + 1.0, int(quotas[load]), beta)) - float(
                quorum_benefit(q, int(quotas[load]), beta)
            )
            over = excess_penalty if q >= float(quotas[load]) else 0.0
            fitness[:, load + 1] = values[load] * marginal - cost_weight * costs[:, load] - over
        difference = fitness[:, :, None] - fitness[:, None, :]
        positive = np.maximum(difference, 0.0)
        inflow = np.sum(state[:, None, :] * positive, axis=2)
        outflow = state * np.sum(np.maximum(-difference, 0.0), axis=2)
        field = inflow - outflow
        residual = float(np.max(np.abs(field)))
        scale = np.maximum(1.0, np.max(np.abs(field), axis=1, keepdims=True))
        state = np.vstack([project_simplex(row) for row in state + time_step * field / scale])
        evaluations += n_robots * (n_loads + 1) ** 2
        if residual <= tolerance:
            break
    return AllocationResult(
        assignment=np.argmax(state, axis=1).astype(int),
        runtime_s=perf_counter() - start,
        iterations=step,
        evaluations=evaluations,
        converged=residual <= tolerance,
        preferences=state,
        residual=residual,
    )


def quorum_closure(
    preferences: np.ndarray,
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    cost_weight: float,
) -> AllocationResult:
    """Deterministic ranking-and-quorum closure.

    At each event the operator compares every still feasible complete group,
    commits the best positive group, and removes its robots.  Consequently
    every load receives either zero robots or exactly its integer quota and a
    robot can belong to at most one load.
    """

    costs, quotas, values = _validate_instance(costs, quotas, values)
    preferences = np.asarray(preferences, dtype=float)
    if preferences.shape == (costs.shape[0], costs.shape[1] + 1):
        preferences = preferences[:, 1:]
    if preferences.shape != costs.shape or not np.all(np.isfinite(preferences)):
        raise ValueError("preferences must have shape (N,K) or (N,K+1)")
    start = perf_counter()
    free = np.ones(costs.shape[0], dtype=bool)
    assignment = np.zeros(costs.shape[0], dtype=int)
    open_loads = set(range(costs.shape[1]))
    events = 0
    evaluations = 0
    while open_loads:
        candidates: list[tuple[float, int, np.ndarray]] = []
        robots = np.flatnonzero(free)
        for load in sorted(open_loads):
            quota = int(quotas[load])
            if robots.size < quota:
                continue
            individual = preferences[robots, load] - cost_weight * costs[robots, load]
            chosen_local = np.argsort(individual, kind="stable")[-quota:]
            chosen = robots[chosen_local]
            group_score = float(values[load] + individual[chosen_local].sum())
            candidates.append((group_score, load, chosen))
            evaluations += robots.size
        if not candidates:
            break
        score, load, chosen = max(candidates, key=lambda item: (item[0], -item[1]))
        if score <= 0.0:
            break
        assignment[chosen] = load + 1
        free[chosen] = False
        open_loads.remove(load)
        events += 1
    return AllocationResult(assignment, perf_counter() - start, events, evaluations)


def allocation_metrics(
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    assignment: np.ndarray,
    cost_weight: float,
) -> dict[str, float | int | bool | np.ndarray]:
    costs, quotas, values = _validate_instance(costs, quotas, values)
    assignment = _validate_assignment(assignment, costs.shape[0], costs.shape[1])
    active = assignment > 0
    rows = np.flatnonzero(active)
    counts = np.bincount(assignment[active], minlength=costs.shape[1] + 1)[1:]
    completed = counts == quotas
    partial = (counts > 0) & (counts < quotas)
    excess = np.maximum(counts - quotas, 0)
    deficit = np.maximum(quotas - counts, 0)
    social_cost = float(costs[rows, assignment[active] - 1].sum())
    completed_value = float(values[completed].sum())
    objective = completed_value - cost_weight * social_cost
    return {
        "counts": counts,
        "closed": bool(np.all((counts == 0) | completed)),
        "completed_loads": int(completed.sum()),
        "completed_value": completed_value,
        "deficit": int(deficit.sum()),
        "normalized_deficit": float(deficit.sum() / max(int(quotas.sum()), 1)),
        "excess": int(excess.sum()),
        "normalized_excess": float(excess.sum() / max(costs.shape[0], 1)),
        "partial_robots": int(counts[partial].sum()),
        "partial_robot_fraction": float(counts[partial].sum() / max(costs.shape[0], 1)),
        "idle_robots": int(np.sum(~active)),
        "social_cost": social_cost,
        "objective": objective,
    }


__all__ = [
    "AllocationResult",
    "allocation_metrics",
    "enumerate_base_game",
    "exact_coalition_oracle",
    "greedy_quorum",
    "is_pure_nash",
    "linear_profile_metrics",
    "marginal_payoff",
    "project_simplex",
    "quorum_benefit",
    "quorum_closure",
    "quorum_potential",
    "smith_preferences",
]
