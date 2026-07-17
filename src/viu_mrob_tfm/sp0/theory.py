"""Formal objects and algorithms for the SP0 assignment game.

Actions use zero for the idle strategy and integers 1..K for real tasks.
Costs are dimensionless and non-negative.  The functions intentionally keep
the finite game separate from the auction price game: their equilibrium
notions have different efficiency guarantees.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from math import factorial
from time import perf_counter

import numpy as np
from scipy.optimize import linear_sum_assignment


@dataclass(frozen=True)
class AllocationResult:
    """One algorithm outcome with auditable logical work counters."""

    assignment: np.ndarray
    iterations: int
    evaluations: int
    runtime_s: float
    converged: bool = True
    prices: np.ndarray | None = None
    epsilon_cs_violation: float | None = None
    history: tuple[np.ndarray, ...] | None = None


def _validate_costs(costs: np.ndarray) -> np.ndarray:
    array = np.asarray(costs, dtype=float)
    if array.ndim != 2 or array.shape[0] < array.shape[1] or array.shape[1] < 1:
        raise ValueError("costs must have shape (N, K) with N >= K >= 1")
    if not np.all(np.isfinite(array)) or np.any(array < 0.0):
        raise ValueError("costs must be finite and non-negative")
    return array


def profile_metrics(
    costs: np.ndarray,
    assignment: np.ndarray,
    penalty: float,
) -> dict[str, float | int | bool]:
    """Evaluate cost, deficit, excess and the penalized potential objective."""

    costs = _validate_costs(costs)
    assignment = np.asarray(assignment, dtype=int)
    n_robots, n_tasks = costs.shape
    if assignment.shape != (n_robots,):
        raise ValueError("assignment must have shape (N,)")
    if np.any(assignment < 0) or np.any(assignment > n_tasks):
        raise ValueError("actions must belong to {0, ..., K}")
    active = assignment > 0
    rows = np.flatnonzero(active)
    social_cost = float(costs[rows, assignment[active] - 1].sum())
    counts = np.bincount(assignment[active], minlength=n_tasks + 1)[1:]
    deficit = int(np.maximum(1 - counts, 0).sum())
    excess = int(np.maximum(counts - 1, 0).sum())
    penalized_cost = social_cost + float(penalty) * (deficit + excess)
    return {
        "social_cost": social_cost,
        "deficit": deficit,
        "excess": excess,
        "feasible": deficit == 0 and excess == 0,
        "penalized_cost": penalized_cost,
        "potential": -penalized_cost,
    }


def action_fitness(
    costs: np.ndarray,
    assignment: np.ndarray,
    robot: int,
    action: int,
    penalty: float,
) -> float:
    """Candidate-action fitness relative to the robot being idle.

    This implements f_ik(a_-i) = Phi(k, a_-i) - Phi(0, a_-i), so it
    remains meaningful both for the current action and for unilateral
    alternatives evaluated by an asynchronous revision protocol.
    """

    costs = _validate_costs(costs)
    assignment = np.asarray(assignment, dtype=int)
    n_robots, n_tasks = costs.shape
    if assignment.shape != (n_robots,):
        raise ValueError("assignment must have shape (N,)")
    if robot < 0 or robot >= n_robots:
        raise IndexError("robot index out of range")
    if action < 0 or action > n_tasks:
        raise ValueError("action must belong to {0, ..., K}")
    baseline = assignment.copy()
    baseline[robot] = 0
    candidate = baseline.copy()
    candidate[robot] = action
    candidate_potential = profile_metrics(costs, candidate, penalty)["potential"]
    baseline_potential = profile_metrics(costs, baseline, penalty)["potential"]
    return float(candidate_potential) - float(baseline_potential)


def marginal_payoff(
    costs: np.ndarray,
    assignment: np.ndarray,
    robot: int,
    penalty: float,
) -> float:
    """Marginal-contribution payoff u_i(a)=Phi(a)-Phi(0,a_-i)."""

    assignment = np.asarray(assignment, dtype=int)
    return action_fitness(costs, assignment, robot, int(assignment[robot]), penalty)


def is_pure_nash(
    costs: np.ndarray,
    assignment: np.ndarray,
    penalty: float,
    tolerance: float = 1e-12,
) -> bool:
    """Check unilateral Nash equilibrium using the exact potential identity."""

    costs = _validate_costs(costs)
    assignment = np.asarray(assignment, dtype=int)
    current = float(profile_metrics(costs, assignment, penalty)["penalized_cost"])
    for robot in range(costs.shape[0]):
        for action in range(costs.shape[1] + 1):
            if action == assignment[robot]:
                continue
            candidate = assignment.copy()
            candidate[robot] = action
            value = float(profile_metrics(costs, candidate, penalty)["penalized_cost"])
            if value < current - tolerance:
                return False
    return True


def enumerate_pure_nash(costs: np.ndarray, penalty: float) -> dict[str, object]:
    """Enumerate every action profile; intended only for N <= 5 audits."""

    costs = _validate_costs(costs)
    n_robots, n_tasks = costs.shape
    profiles = 0
    feasible_profiles = 0
    nash_profiles: list[np.ndarray] = []
    nash_costs: list[float] = []
    for actions in product(range(n_tasks + 1), repeat=n_robots):
        profiles += 1
        assignment = np.asarray(actions, dtype=int)
        metrics = profile_metrics(costs, assignment, penalty)
        feasible_profiles += int(metrics["feasible"])
        if is_pure_nash(costs, assignment, penalty):
            nash_profiles.append(assignment)
            nash_costs.append(float(metrics["social_cost"]))
    optimum = hungarian_assignment(costs)
    optimum_cost = float(profile_metrics(costs, optimum.assignment, penalty)["social_cost"])
    optimal_nash = sum(abs(value - optimum_cost) <= 1e-10 for value in nash_costs)
    return {
        "profiles": profiles,
        "feasible_profiles": feasible_profiles,
        "expected_feasible_profiles": factorial(n_robots) // factorial(n_robots - n_tasks),
        "nash_profiles": nash_profiles,
        "nash_count": len(nash_profiles),
        "optimal_nash_count": optimal_nash,
        "optimum_cost": optimum_cost,
        "worst_nash_cost": max(nash_costs) if nash_costs else np.nan,
    }


def hungarian_assignment(costs: np.ndarray) -> AllocationResult:
    """Exact rectangular assignment oracle using SciPy's LAP solver."""

    costs = _validate_costs(costs)
    start = perf_counter()
    rows, cols = linear_sum_assignment(costs)
    initial = np.zeros(costs.shape[0], dtype=int)
    assignment = initial.copy()
    assignment[rows] = cols + 1
    return AllocationResult(
        assignment=assignment,
        iterations=1,
        evaluations=int(costs.size),
        runtime_s=perf_counter() - start,
        history=(initial, assignment.copy()),
    )


def greedy_assignment(costs: np.ndarray) -> AllocationResult:
    """Central greedy edge selection; feasible but not generally optimal."""

    costs = _validate_costs(costs)
    start = perf_counter()
    n_robots, n_tasks = costs.shape
    assignment = np.zeros(n_robots, dtype=int)
    history = [assignment.copy()]
    task_used = np.zeros(n_tasks, dtype=bool)
    edges = sorted(
        ((float(costs[i, k]), i, k) for i in range(n_robots) for k in range(n_tasks)),
        key=lambda item: (item[0], item[1], item[2]),
    )
    accepted = 0
    for _, robot, task in edges:
        if assignment[robot] == 0 and not task_used[task]:
            assignment[robot] = task + 1
            task_used[task] = True
            accepted += 1
            history.append(assignment.copy())
            if accepted == n_tasks:
                break
    return AllocationResult(
        assignment=assignment,
        iterations=accepted,
        evaluations=len(edges),
        runtime_s=perf_counter() - start,
        history=tuple(history),
    )


def potential_best_response(
    costs: np.ndarray,
    penalty: float,
    rng: np.random.Generator,
    initial: np.ndarray | None = None,
    max_sweeps: int = 100,
) -> AllocationResult:
    """Asynchronous strict better response in the finite exact-potential game."""

    costs = _validate_costs(costs)
    n_robots, n_tasks = costs.shape
    assignment = (
        np.zeros(n_robots, dtype=int)
        if initial is None
        else np.asarray(initial, dtype=int).copy()
    )
    history = [assignment.copy()]
    start = perf_counter()
    revisions = 0
    evaluations = 0
    converged = False
    for sweep in range(1, max_sweeps + 1):
        changed = False
        for robot in rng.permutation(n_robots):
            current_action = int(assignment[robot])
            current_value = float(profile_metrics(costs, assignment, penalty)["penalized_cost"])
            best_action = current_action
            best_value = current_value
            for action in range(n_tasks + 1):
                evaluations += 1
                if action == current_action:
                    continue
                candidate = assignment.copy()
                candidate[robot] = action
                value = float(profile_metrics(costs, candidate, penalty)["penalized_cost"])
                if value < best_value - 1e-12:
                    best_action, best_value = action, value
            if best_action != current_action:
                assignment[robot] = best_action
                revisions += 1
                changed = True
                history.append(assignment.copy())
        if not changed:
            converged = True
            break
    return AllocationResult(
        assignment=assignment,
        iterations=revisions,
        evaluations=evaluations,
        runtime_s=perf_counter() - start,
        converged=converged,
        history=tuple(history),
    )


def pairwise_exchange(
    costs: np.ndarray,
    initial: np.ndarray,
    max_events: int = 100_000,
) -> AllocationResult:
    """Strictly improve a feasible matching by swaps and idle replacements.

    The terminal point is stable against exchanges involving at most two
    robots.  It is not claimed to be a global assignment optimum.
    """

    costs = _validate_costs(costs)
    assignment = np.asarray(initial, dtype=int).copy()
    if not profile_metrics(costs, assignment, penalty=0.0)["feasible"]:
        raise ValueError("pairwise exchange requires a feasible initial assignment")
    start = perf_counter()
    history = [assignment.copy()]
    n_robots = costs.shape[0]
    events = 0
    evaluations = 0
    converged = False
    for _ in range(max_events):
        best_delta = -1e-12
        best_move: tuple[str, int, int] | None = None
        assigned = np.flatnonzero(assignment > 0)
        idle = np.flatnonzero(assignment == 0)
        for left_index, robot_i in enumerate(assigned):
            task_i = assignment[robot_i] - 1
            for robot_j in assigned[left_index + 1 :]:
                task_j = assignment[robot_j] - 1
                evaluations += 1
                delta = (
                    costs[robot_i, task_j]
                    + costs[robot_j, task_i]
                    - costs[robot_i, task_i]
                    - costs[robot_j, task_j]
                )
                if delta < best_delta:
                    best_delta = float(delta)
                    best_move = ("swap", int(robot_i), int(robot_j))
            for robot_j in idle:
                evaluations += 1
                delta = costs[robot_j, task_i] - costs[robot_i, task_i]
                if delta < best_delta:
                    best_delta = float(delta)
                    best_move = ("replace", int(robot_i), int(robot_j))
        if best_move is None:
            converged = True
            break
        move, robot_i, robot_j = best_move
        if move == "swap":
            assignment[robot_i], assignment[robot_j] = assignment[robot_j], assignment[robot_i]
        else:
            assignment[robot_j] = assignment[robot_i]
            assignment[robot_i] = 0
        events += 1
        history.append(assignment.copy())
    return AllocationResult(
        assignment=assignment,
        iterations=events,
        evaluations=evaluations,
        runtime_s=perf_counter() - start,
        converged=converged,
        history=tuple(history),
    )


def auction_assignment(
    costs: np.ndarray,
    epsilon: float,
    max_bids: int = 2_000_000,
) -> AllocationResult:
    """Forward auction on a square padding of the rectangular assignment.

    The returned prices certify epsilon-complementary slackness.  Dummy items
    represent the N-K idle positions and have zero cost.
    """

    costs = _validate_costs(costs)
    if epsilon <= 0.0:
        raise ValueError("epsilon must be positive")
    n_robots, n_tasks = costs.shape
    padded = np.zeros((n_robots, n_robots), dtype=float)
    padded[:, :n_tasks] = costs
    benefits = -padded
    prices = np.zeros(n_robots, dtype=float)
    owner = np.full(n_robots, -1, dtype=int)
    item_of_robot = np.full(n_robots, -1, dtype=int)
    queue = deque(range(n_robots))
    history = [np.zeros(n_robots, dtype=int)]
    bids = 0
    start = perf_counter()
    while queue and bids < max_bids:
        robot = queue.popleft()
        values = benefits[robot] - prices
        order = np.argsort(values, kind="stable")
        best_item = int(order[-1])
        best_value = float(values[best_item])
        second_value = float(values[order[-2]]) if n_robots > 1 else best_value - epsilon
        prices[best_item] += best_value - second_value + epsilon
        displaced = int(owner[best_item])
        owner[best_item] = robot
        item_of_robot[robot] = best_item
        if displaced >= 0:
            item_of_robot[displaced] = -1
            queue.append(displaced)
        bids += 1
        transient = np.zeros(n_robots, dtype=int)
        transient_real = (item_of_robot >= 0) & (item_of_robot < n_tasks)
        transient[transient_real] = item_of_robot[transient_real] + 1
        history.append(transient)
    assignment = np.zeros(n_robots, dtype=int)
    real = (item_of_robot >= 0) & (item_of_robot < n_tasks)
    assignment[real] = item_of_robot[real] + 1
    net_values = benefits - prices[None, :]
    assigned_values = net_values[np.arange(n_robots), item_of_robot]
    violation = float(np.max(np.max(net_values, axis=1) - assigned_values)) if not queue else np.inf
    return AllocationResult(
        assignment=assignment,
        iterations=bids,
        evaluations=bids * n_robots,
        runtime_s=perf_counter() - start,
        converged=not queue,
        prices=prices,
        epsilon_cs_violation=violation,
        history=tuple(history),
    )
