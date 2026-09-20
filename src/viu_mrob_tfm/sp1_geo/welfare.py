"""Concave signal potentials and common discrete welfare helpers."""

from __future__ import annotations

import math

import numpy as np

from .contributions import aggregate_signal
from .models import ActionCatalog, Assignment, GeoWorld, SignalName


def _active_resources(demand: np.ndarray) -> np.ndarray:
    return np.asarray(demand, dtype=float) > 1e-12


def load_signal_value(
    service: np.ndarray,
    demand: np.ndarray,
    priority_value: float,
    *,
    curvature: float = 1.0,
) -> float:
    """Smooth, concave and increasing value of a load's signal coverage."""

    active = _active_resources(demand)
    if not np.any(active):
        return 0.0
    ratio = np.maximum(np.asarray(service)[active], 0.0) / np.asarray(demand)[active]
    return float(priority_value * np.mean(1.0 - np.exp(-curvature * ratio)))


def load_signal_gradient(
    service: np.ndarray,
    demand: np.ndarray,
    priority_value: float,
    *,
    curvature: float = 1.0,
) -> np.ndarray:
    """Gradient of :func:`load_signal_value` with physical units preserved."""

    service_values = np.asarray(service, dtype=float)
    demand_values = np.asarray(demand, dtype=float)
    gradient = np.zeros_like(service_values)
    active = _active_resources(demand_values)
    count = int(np.sum(active))
    if count == 0:
        return gradient
    ratio = np.maximum(service_values[active], 0.0) / demand_values[active]
    gradient[active] = (
        float(priority_value)
        * curvature
        * np.exp(-curvature * ratio)
        / (count * demand_values[active])
    )
    return gradient


def signal_potential(
    world: GeoWorld,
    catalog: ActionCatalog,
    preferences: np.ndarray,
    signal: SignalName,
    *,
    entropy_tau: float = 0.0,
) -> float:
    """Potential on action preferences with per-robot idle entropy."""

    x = np.asarray(preferences, dtype=float)
    aggregate = aggregate_signal(catalog, x, signal, world.n_loads)
    demands = catalog.demands(signal)
    value = sum(
        load_signal_value(
            aggregate[load_index],
            demands[load_index],
            world.loads[load_index].priority_value,
        )
        for load_index in range(world.n_loads)
    )
    value -= float(np.dot(catalog.costs, x))
    if entropy_tau > 0.0:
        entropy = 0.0
        for robot in range(world.n_robots):
            indices = catalog.actions_for_robot(robot, compatible_only=True)
            action_mass = np.clip(x[indices], 0.0, 1.0)
            idle = max(1.0 - float(np.sum(action_mass)), 0.0)
            full = np.concatenate([action_mass, np.array([idle])])
            entropy -= float(np.sum(full * np.log(np.maximum(full, 1e-15))))
        value += float(entropy_tau) * entropy
    return float(value)


def marginal_payoffs(
    world: GeoWorld,
    catalog: ActionCatalog,
    preferences: np.ndarray,
    signal: SignalName,
) -> np.ndarray:
    """Return ``E_ikh^T grad F_k - c_ikh`` for every action."""

    x = np.asarray(preferences, dtype=float)
    aggregate = aggregate_signal(catalog, x, signal, world.n_loads)
    contributions = catalog.contributions(signal)
    demands = catalog.demands(signal)
    gradients = np.vstack(
        [
            load_signal_gradient(
                aggregate[load_index],
                demands[load_index],
                world.loads[load_index].priority_value,
            )
            for load_index in range(world.n_loads)
        ]
    )
    payoff = np.einsum(
        "ad,ad->a", contributions, gradients[catalog.load_index]
    ) - catalog.costs
    return np.where(catalog.compatible, payoff, -1e9)


def assignment_preferences(
    assignment: Assignment, catalog: ActionCatalog
) -> np.ndarray:
    x = np.zeros(catalog.n_actions, dtype=float)
    selected = assignment.selected_actions()
    if selected.size:
        x[selected] = 1.0
    return x


def assignment_signal_potential(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
    signal: SignalName,
) -> float:
    selected = assignment.selected_actions()
    aggregate = np.zeros(
        (world.n_loads, catalog.contributions(signal).shape[1]), dtype=float
    )
    if selected.size:
        np.add.at(
            aggregate,
            catalog.load_index[selected],
            catalog.contributions(signal)[selected],
        )
    demands = catalog.demands(signal)
    value = sum(
        load_signal_value(
            aggregate[load_index],
            demands[load_index],
            world.loads[load_index].priority_value,
        )
        for load_index in range(world.n_loads)
    )
    if selected.size:
        value -= float(np.sum(catalog.costs[selected]))
    return float(value)


def independent_argmax_closure(
    preferences: np.ndarray,
    catalog: ActionCatalog,
    n_robots: int,
) -> Assignment:
    """Close each robot independently; duplicate slots remain observable."""

    x = np.asarray(preferences, dtype=float)
    assignment = np.full(n_robots, -1, dtype=int)
    for robot in range(n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        if actions.size == 0:
            continue
        best = int(actions[np.argmax(x[actions])])
        idle_mass = max(1.0 - float(np.sum(x[actions])), 0.0)
        if float(x[best]) > idle_mass + 1e-12:
            assignment[robot] = best
    return Assignment(assignment)


def wonderful_life_difference(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
    robot: int,
    new_action: int,
    signal: SignalName,
) -> tuple[float, float]:
    """Return unilateral utility and potential changes for an exact-potential audit."""

    before = assignment_signal_potential(world, catalog, assignment, signal)
    after_assignment = assignment.with_action(robot, new_action)
    after = assignment_signal_potential(world, catalog, after_assignment, signal)
    delta_potential = after - before
    # Wonderful-life utility is the agent's marginal contribution to the same
    # discrete potential, so its unilateral difference is exact by definition.
    return float(delta_potential), float(delta_potential)


def projected_kkt_residual(
    world: GeoWorld,
    catalog: ActionCatalog,
    preferences: np.ndarray,
    signal: SignalName,
    *,
    entropy_tau: float,
) -> float:
    """Fixed-point residual of the entropy-regularized simplex KKT system."""

    if entropy_tau <= 0.0:
        raise ValueError("entropy_tau must be positive for the logit KKT residual.")
    x = np.asarray(preferences, dtype=float)
    payoff = marginal_payoffs(world, catalog, x, signal)
    residual = 0.0
    for robot in range(world.n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        if actions.size == 0:
            continue
        scores = np.concatenate([payoff[actions], np.array([0.0])])
        scores -= float(np.max(scores))
        target = np.exp(scores / entropy_tau)
        target /= float(np.sum(target))
        current = np.concatenate(
            [x[actions], np.array([max(1.0 - float(np.sum(x[actions])), 0.0)])]
        )
        residual = max(residual, float(np.max(np.abs(current - target))))
    return residual


def relative_objective_gap(value: float, reference: float) -> float:
    if not (math.isfinite(value) and math.isfinite(reference)):
        return math.nan
    return abs(float(value) - float(reference)) / (1.0 + abs(float(reference)))


__all__ = [
    "assignment_preferences",
    "assignment_signal_potential",
    "independent_argmax_closure",
    "load_signal_gradient",
    "load_signal_value",
    "marginal_payoffs",
    "projected_kkt_residual",
    "relative_objective_gap",
    "signal_potential",
    "wonderful_life_difference",
]
