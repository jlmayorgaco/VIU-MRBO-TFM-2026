"""Central MILP/LP/entropy references for SP1-GEO."""

from __future__ import annotations

import math
import time
import tracemalloc
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp, minimize
from scipy.sparse import lil_matrix

from ..models import ActionCatalog, AllocationResult, Assignment, GeoWorld, SignalName
from ..welfare import (
    independent_argmax_closure,
    marginal_payoffs,
    projected_kkt_residual,
    signal_potential,
)


def _linear_model(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    relax: bool,
    time_limit_s: float,
) -> tuple[Any, np.ndarray]:
    actions, loads = catalog.n_actions, world.n_loads
    variables = actions + loads
    objective = np.zeros(variables, dtype=float)
    objective[:actions] = catalog.costs
    objective[actions:] = -np.array(
        [load.priority_value for load in world.loads], dtype=float
    )
    rows: list[tuple[dict[int, float], float, float]] = []

    for robot in range(world.n_robots):
        coefficients = {
            int(action): 1.0
            for action in catalog.actions_for_robot(robot, compatible_only=False)
        }
        rows.append((coefficients, -np.inf, 1.0))
    for load_index, load in enumerate(world.loads):
        for slot_index in range(len(load.slots)):
            action_indices = np.flatnonzero(
                (catalog.load_index == load_index)
                & (catalog.slot_index == slot_index)
            )
            rows.append(
                ({int(action): 1.0 for action in action_indices}, -np.inf, 1.0)
            )
        actions_for_load = np.flatnonzero(catalog.load_index == load_index)
        y = actions + load_index
        link = {int(action): 1.0 for action in actions_for_load}
        link[y] = -float(len(load.slots))
        rows.append((link, -np.inf, 0.0))

        capacity = {
            int(action): -float(catalog.physical_contributions[action, 0])
            for action in actions_for_load
        }
        capacity[y] = load.min_capacity_kg
        rows.append((capacity, -np.inf, 0.0))
        upper = {
            int(action): float(catalog.physical_contributions[action, 0])
            for action in actions_for_load
        }
        upper[y] = -load.max_capacity_kg
        rows.append((upper, -np.inf, 0.0))
        cardinality = {int(action): -1.0 for action in actions_for_load}
        cardinality[y] = float(load.min_coalition_size)
        rows.append((cardinality, -np.inf, 0.0))

        for resource, demand in enumerate(catalog.physical_demands[load_index]):
            if resource == 0 or demand <= 1e-12:
                continue
            coefficients = {
                int(action): -float(
                    catalog.physical_contributions[action, resource]
                )
                for action in actions_for_load
            }
            coefficients[y] = float(demand)
            rows.append((coefficients, -np.inf, 0.0))

    matrix = lil_matrix((len(rows), variables), dtype=float)
    lower = np.empty(len(rows), dtype=float)
    upper = np.empty(len(rows), dtype=float)
    for row_index, (coefficients, low, high) in enumerate(rows):
        for column, value in coefficients.items():
            matrix[row_index, column] = value
        lower[row_index] = low
        upper[row_index] = high
    variable_upper = np.ones(variables, dtype=float)
    variable_upper[:actions] = catalog.compatible.astype(float)
    result = milp(
        objective,
        integrality=np.zeros(variables, dtype=int)
        if relax
        else np.ones(variables, dtype=int),
        bounds=Bounds(np.zeros(variables), variable_upper),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": float(time_limit_s)},
    )
    values = (
        np.zeros(variables, dtype=float)
        if result.x is None
        else np.asarray(result.x, dtype=float)
    )
    return result, values


def _solver_status(result: Any) -> str:
    return {
        0: "optimal",
        1: "timeout_or_limit",
        2: "infeasible",
        3: "unbounded",
        4: "solver_error",
    }.get(int(result.status), "solver_error")


def solve_physical_milp(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    time_limit_s: float = 60.0,
) -> AllocationResult:
    started = time.perf_counter()
    tracemalloc.start()
    result, values = _linear_model(
        world, catalog, relax=False, time_limit_s=time_limit_s
    )
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    action_values = values[: catalog.n_actions]
    assignment = np.full(world.n_robots, -1, dtype=int)
    for action in np.flatnonzero(action_values > 0.5):
        robot = int(catalog.robot_index[action])
        if assignment[robot] < 0:
            assignment[robot] = int(action)
    status = _solver_status(result)
    dual_bound = float(getattr(result, "mip_dual_bound", math.nan))
    return AllocationResult(
        method="milp_physical_oracle",
        engine="milp",
        signal="marginal_physical",
        assignment=Assignment(assignment),
        status=status,
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        preferences=action_values,
        iterations=int(getattr(result, "mip_node_count", 0) or 0),
        diagnostics={
            "information_scope": "global_oracle",
            "solver_status_code": int(result.status),
            "solver_message": str(result.message),
            "objective_min": float(result.fun)
            if result.fun is not None
            else math.nan,
            "welfare_upper_bound": -dual_bound
            if np.isfinite(dual_bound)
            else math.nan,
            "mip_gap": float(getattr(result, "mip_gap", math.nan)),
            "optimal_certified": bool(int(result.status) == 0),
            "peak_memory_mb": peak / (1024.0**2),
        },
    )


def solve_lp_relaxation(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    time_limit_s: float = 60.0,
) -> AllocationResult:
    started = time.perf_counter()
    result, values = _linear_model(
        world, catalog, relax=True, time_limit_s=time_limit_s
    )
    preferences = np.clip(values[: catalog.n_actions], 0.0, 1.0)
    assignment = independent_argmax_closure(
        preferences, catalog, world.n_robots
    )
    status = _solver_status(result)
    objective = float(result.fun) if result.fun is not None else math.nan
    return AllocationResult(
        method="lp_relaxation_oracle",
        engine="lp_relaxation",
        signal="marginal_physical",
        assignment=assignment,
        status=status,
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        preferences=preferences,
        diagnostics={
            "information_scope": "global_oracle",
            "solver_status_code": int(result.status),
            "solver_message": str(result.message),
            "objective_min": objective,
            "welfare_upper_bound": -objective if np.isfinite(objective) else math.nan,
            "optimal_certified": bool(int(result.status) == 0),
        },
    )


def solve_entropic_convex(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    signal: SignalName = "marginal_physical",
    entropy_tau: float = 0.08,
    max_iterations: int = 2_000,
    tolerance: float = 1e-10,
) -> AllocationResult:
    """Solve the concave entropy-regularized simplex reference with SLSQP."""

    started = time.perf_counter()
    compatible = catalog.compatible
    x0 = np.zeros(catalog.n_actions, dtype=float)
    bounds: list[tuple[float, float]] = []
    for action in range(catalog.n_actions):
        bounds.append((0.0, 1.0) if compatible[action] else (0.0, 0.0))
    for robot in range(world.n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        if actions.size:
            x0[actions] = 0.50 / actions.size

    constraints = [
        {
            "type": "ineq",
            "fun": lambda x, robot=robot: 1.0
            - float(np.sum(x[catalog.actions_for_robot(robot, compatible_only=True)])),
        }
        for robot in range(world.n_robots)
    ]

    def objective(x: np.ndarray) -> float:
        return -signal_potential(
            world, catalog, x, signal, entropy_tau=entropy_tau
        )

    def gradient(x: np.ndarray) -> np.ndarray:
        values = -marginal_payoffs(world, catalog, x, signal)
        for robot in range(world.n_robots):
            actions = catalog.actions_for_robot(robot, compatible_only=True)
            if actions.size == 0:
                continue
            idle = max(1.0 - float(np.sum(x[actions])), 1e-15)
            values[actions] -= entropy_tau * np.log(
                idle / np.maximum(x[actions], 1e-15)
            )
        values[~compatible] = 0.0
        return values

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        jac=gradient,
        bounds=bounds,
        constraints=constraints,
        options={
            "maxiter": int(max_iterations),
            "ftol": float(tolerance),
            "disp": False,
        },
    )
    preferences = np.clip(np.asarray(result.x, dtype=float), 0.0, 1.0)
    assignment = independent_argmax_closure(
        preferences, catalog, world.n_robots
    )
    kkt = projected_kkt_residual(
        world,
        catalog,
        preferences,
        signal,
        entropy_tau=entropy_tau,
    )
    return AllocationResult(
        method="entropic_convex_oracle",
        engine="entropic_convex",
        signal=signal,
        assignment=assignment,
        status="optimal" if result.success else "solver_error",
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        preferences=preferences,
        iterations=int(result.nit),
        diagnostics={
            "information_scope": "global_oracle",
            "solver_status_code": int(result.status),
            "solver_message": str(result.message),
            "objective_max": -float(result.fun),
            "kkt_residual": kkt,
            "optimal_certified": bool(result.success),
        },
    )


__all__ = [
    "solve_entropic_convex",
    "solve_lp_relaxation",
    "solve_physical_milp",
]
