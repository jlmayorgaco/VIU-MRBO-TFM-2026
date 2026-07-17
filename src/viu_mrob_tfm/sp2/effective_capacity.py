"""Formal and executable objects for SP2.

The module keeps four objects separate:

* physical payload is a nominal robot property;
* operational availability discounts service by battery state and arrival cost;
* service contribution is a dimensionless campaign index, not payload capacity;
* assignment oracles optimize either normalized coverage or an operational score.

The potential result concerns a continuous preference matrix with a fixed
effective-capacity matrix.  It does not establish convergence of a sampled
revision protocol or integer optimality after decoding.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True, slots=True)
class OracleResult:
    assignment: np.ndarray
    completed: np.ndarray
    covered_capacity: np.ndarray
    objective: float
    runtime_s: float
    optimal: bool


def operational_availability(
    battery_fraction: np.ndarray,
    reserve_fraction: np.ndarray,
    distance_m: np.ndarray,
    distance_scale_m: float,
    compatibility: np.ndarray | None = None,
) -> np.ndarray:
    """Return the dimensionless pair-dependent operational availability.

    Battery and distance describe whether a robot is attractive and available
    within the campaign horizon.  They do not change its mechanical payload.
    """

    battery = np.asarray(battery_fraction, dtype=float)
    reserve = np.asarray(reserve_fraction, dtype=float)
    distance = np.asarray(distance_m, dtype=float)
    if battery.ndim != 1 or reserve.shape != battery.shape:
        raise ValueError("battery and reserve must have shape (N,)")
    if distance.ndim != 2 or distance.shape[0] != battery.size:
        raise ValueError("distance must have shape (N, K)")
    if distance_scale_m <= 0.0:
        raise ValueError("distance_scale_m must be positive")
    if (
        np.any(~np.isfinite(battery))
        or np.any(~np.isfinite(reserve))
        or np.any(~np.isfinite(distance))
        or np.any(distance < 0.0)
        or np.any((battery < 0.0) | (battery > 1.0))
        or np.any((reserve < 0.0) | (reserve >= 1.0))
    ):
        raise ValueError("invalid operational parameters")
    battery_factor = np.clip(
        (battery - reserve) / np.maximum(1.0 - reserve, np.finfo(float).eps),
        0.0,
        1.0,
    )
    availability = battery_factor[:, None] * np.exp(
        -distance / float(distance_scale_m)
    )
    if compatibility is not None:
        compatibility = np.asarray(compatibility, dtype=float)
        if compatibility.shape != distance.shape or np.any(
            ~np.isin(compatibility, [0.0, 1.0])
        ):
            raise ValueError("compatibility must be binary with shape (N, K)")
        availability *= compatibility
    return availability


def service_contribution(
    nominal_payload_kg: np.ndarray,
    battery_fraction: np.ndarray,
    reserve_fraction: np.ndarray,
    distance_m: np.ndarray,
    distance_scale_m: float,
    compatibility: np.ndarray | None = None,
    service_reference_kg: float = 1.0,
) -> np.ndarray:
    """Return the dimensionless operational service contribution.

    The nominal payload is divided by an explicit reference scale before it is
    weighted by operational availability.  With the campaign convention
    ``service_reference_kg=1``, values are numerically identical to the legacy
    ``kg-equivalent`` column while no longer being interpreted as kilograms.
    """

    payload = np.asarray(nominal_payload_kg, dtype=float)
    if (
        payload.ndim != 1
        or np.any(~np.isfinite(payload))
        or np.any(payload < 0.0)
        or not np.isfinite(service_reference_kg)
        or service_reference_kg <= 0.0
    ):
        raise ValueError("payload and service_reference_kg must be finite and non-negative")
    availability = operational_availability(
        battery_fraction=battery_fraction,
        reserve_fraction=reserve_fraction,
        distance_m=distance_m,
        distance_scale_m=distance_scale_m,
        compatibility=compatibility,
    )
    if availability.shape[0] != payload.size:
        raise ValueError("payload, battery, reserve, and distance must share N")
    return payload[:, None] / float(service_reference_kg) * availability


def effective_capacity(
    nominal_payload_kg: np.ndarray,
    battery_fraction: np.ndarray,
    reserve_fraction: np.ndarray,
    distance_m: np.ndarray,
    distance_scale_m: float,
    compatibility: np.ndarray | None = None,
    service_reference_kg: float = 1.0,
) -> np.ndarray:
    """Backward-compatible alias for :func:`service_contribution`.

    The historical function name is retained for archived processors.  Its
    output must be interpreted as normalized service units, not mechanical
    payload or deliverable mass.
    """

    return service_contribution(
        nominal_payload_kg=nominal_payload_kg,
        battery_fraction=battery_fraction,
        reserve_fraction=reserve_fraction,
        distance_m=distance_m,
        distance_scale_m=distance_scale_m,
        compatibility=compatibility,
        service_reference_kg=service_reference_kg,
    )


def _validate_assignment_inputs(
    capacity: np.ndarray,
    demand: np.ndarray,
    min_cardinality: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    capacity = np.asarray(capacity, dtype=float)
    demand = np.asarray(demand, dtype=float)
    if capacity.ndim != 2 or capacity.shape[0] < 1 or capacity.shape[1] < 1:
        raise ValueError("capacity must have shape (N, K)")
    if demand.shape != (capacity.shape[1],) or np.any(demand <= 0.0):
        raise ValueError("demand must have shape (K,) and be positive")
    if np.any(~np.isfinite(capacity)) or np.any(capacity < 0.0):
        raise ValueError("capacity must be finite and non-negative")
    if min_cardinality is None:
        min_cardinality = np.ones(capacity.shape[1], dtype=int)
    min_cardinality = np.asarray(min_cardinality, dtype=int)
    if min_cardinality.shape != demand.shape or np.any(min_cardinality < 1):
        raise ValueError("min_cardinality must have shape (K,) and be positive")
    return capacity, demand, min_cardinality


def aggregate_capacity(capacity: np.ndarray, assignment: np.ndarray) -> np.ndarray:
    capacity = np.asarray(capacity, dtype=float)
    assignment = np.asarray(assignment, dtype=float)
    if assignment.shape != capacity.shape:
        raise ValueError("assignment must have the same shape as capacity")
    return np.sum(capacity * assignment, axis=0)


def _decode_oracle(
    solution: np.ndarray,
    capacity: np.ndarray,
    demand: np.ndarray,
    min_cardinality: np.ndarray,
    objective: float,
    runtime_s: float,
    optimal: bool,
) -> OracleResult:
    n_robots, n_loads = capacity.shape
    assignment = (solution[: n_robots * n_loads].reshape(n_robots, n_loads) > 0.5).astype(int)
    supplied = aggregate_capacity(capacity, assignment)
    counts = assignment.sum(axis=0)
    completed = (supplied + 1e-9 >= demand) & (counts >= min_cardinality)
    return OracleResult(
        assignment=assignment,
        completed=completed,
        covered_capacity=np.minimum(supplied, demand),
        objective=float(objective),
        runtime_s=float(runtime_s),
        optimal=bool(optimal),
    )


def coverage_reference(
    capacity: np.ndarray,
    demand: np.ndarray,
    *,
    distance_m: np.ndarray | None = None,
    distance_weight: float = 1e-5,
    time_limit_s: float = 8.0,
) -> OracleResult:
    """MILP reference that maximizes the sum of per-load coverage ratios."""

    capacity, demand, min_cardinality = _validate_assignment_inputs(capacity, demand)
    n_robots, n_loads = capacity.shape
    n_x = n_robots * n_loads
    if distance_m is None:
        distance_m = np.zeros_like(capacity)
    distance_m = np.asarray(distance_m, dtype=float)
    if distance_m.shape != capacity.shape or np.any(distance_m < 0.0):
        raise ValueError("distance_m must be non-negative with shape (N, K)")
    objective = np.concatenate(
        [distance_weight * distance_m.ravel(), -1.0 / demand]
    )
    integrality = np.concatenate([np.ones(n_x), np.zeros(n_loads)])
    lower = np.zeros(n_x + n_loads)
    upper = np.concatenate([np.ones(n_x), demand])
    rows: list[np.ndarray] = []
    lower_constraints: list[float] = []
    upper_constraints: list[float] = []
    for robot in range(n_robots):
        row = np.zeros(n_x + n_loads)
        row[robot * n_loads : (robot + 1) * n_loads] = 1.0
        rows.append(row)
        lower_constraints.append(-np.inf)
        upper_constraints.append(1.0)
    for load in range(n_loads):
        row = np.zeros(n_x + n_loads)
        row[load:n_x:n_loads] = -capacity[:, load]
        row[n_x + load] = 1.0
        rows.append(row)
        lower_constraints.append(-np.inf)
        upper_constraints.append(0.0)
    start = perf_counter()
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(
            np.vstack(rows), np.asarray(lower_constraints), np.asarray(upper_constraints)
        ),
        options={"time_limit": float(time_limit_s)},
    )
    runtime = perf_counter() - start
    if result.x is None or int(result.status) not in {0, 1}:
        raise RuntimeError(f"coverage MILP failed: {result.message}")
    return _decode_oracle(
        result.x,
        capacity,
        demand,
        min_cardinality,
        -float(result.fun),
        runtime,
        int(result.status) == 0,
    )


def score_reference(
    capacity: np.ndarray,
    demand: np.ndarray,
    values: np.ndarray,
    min_cardinality: np.ndarray,
    distance_m: np.ndarray,
    travel_energy_wh: np.ndarray,
    *,
    completion_weight: float = 5.0,
    partial_weight: float = 100.0,
    distance_weight: float = 5e-4,
    energy_weight: float = 1e-5,
    time_limit_s: float = 8.0,
) -> OracleResult:
    """MILP reference matching the operational score used by the campaign."""

    capacity, demand, min_cardinality = _validate_assignment_inputs(
        capacity, demand, min_cardinality
    )
    values = np.asarray(values, dtype=float)
    distance_m = np.asarray(distance_m, dtype=float)
    travel_energy_wh = np.asarray(travel_energy_wh, dtype=float)
    if values.shape != demand.shape or np.any(values < 0.0):
        raise ValueError("values must be non-negative with shape (K,)")
    if distance_m.shape != capacity.shape or travel_energy_wh.shape != capacity.shape:
        raise ValueError("cost matrices must have shape (N, K)")
    n_robots, n_loads = capacity.shape
    n_x = n_robots * n_loads
    n_variables = n_x + 2 * n_loads
    objective = np.zeros(n_variables)
    objective[:n_x] = (
        distance_weight * distance_m.ravel()
        + energy_weight * travel_energy_wh.ravel()
    )
    objective[n_x : n_x + n_loads] = -completion_weight * values
    objective[n_x + n_loads :] = -partial_weight / demand
    integrality = np.concatenate(
        [np.ones(n_x + n_loads), np.zeros(n_loads)]
    )
    lower = np.zeros(n_variables)
    upper = np.concatenate([np.ones(n_x + n_loads), demand])
    rows: list[np.ndarray] = []
    lows: list[float] = []
    highs: list[float] = []
    for robot in range(n_robots):
        row = np.zeros(n_variables)
        row[robot * n_loads : (robot + 1) * n_loads] = 1.0
        rows.append(row)
        lows.append(-np.inf)
        highs.append(1.0)
    for load in range(n_loads):
        full = np.zeros(n_variables)
        full[load:n_x:n_loads] = capacity[:, load]
        full[n_x + load] = -demand[load]
        rows.append(full)
        lows.append(0.0)
        highs.append(np.inf)
        card = np.zeros(n_variables)
        card[load:n_x:n_loads] = 1.0
        card[n_x + load] = -min_cardinality[load]
        rows.append(card)
        lows.append(0.0)
        highs.append(np.inf)
        partial = np.zeros(n_variables)
        partial[load:n_x:n_loads] = -capacity[:, load]
        partial[n_x + n_loads + load] = 1.0
        rows.append(partial)
        lows.append(-np.inf)
        highs.append(0.0)
    start = perf_counter()
    result = milp(
        c=objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(np.vstack(rows), np.asarray(lows), np.asarray(highs)),
        options={"time_limit": float(time_limit_s)},
    )
    runtime = perf_counter() - start
    if result.x is None or int(result.status) not in {0, 1}:
        raise RuntimeError(f"score MILP failed: {result.message}")
    return _decode_oracle(
        result.x,
        capacity,
        demand,
        min_cardinality,
        -float(result.fun),
        runtime,
        int(result.status) == 0,
    )


def _validate_game(
    preferences: np.ndarray,
    capacity: np.ndarray,
    demand: np.ndarray,
    values: np.ndarray,
    costs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    preferences = np.asarray(preferences, dtype=float)
    capacity, demand, _ = _validate_assignment_inputs(capacity, demand)
    values = np.asarray(values, dtype=float)
    costs = np.asarray(costs, dtype=float)
    if preferences.shape != capacity.shape or costs.shape != capacity.shape:
        raise ValueError("preferences and costs must have shape (N, K)")
    if values.shape != demand.shape:
        raise ValueError("values must have shape (K,)")
    if np.any(preferences < 0.0) or np.any(preferences.sum(axis=1) > 1.0 + 1e-9):
        raise ValueError("preferences must be non-negative with row sums at most one")
    return preferences, capacity, demand, values, costs


def marginal_potential(
    preferences: np.ndarray,
    capacity: np.ndarray,
    demand: np.ndarray,
    values: np.ndarray,
    costs: np.ndarray,
) -> float:
    """Potential for the clipped linear deficit pressure ``sigma(r)=[1-r]+``."""

    preferences, capacity, demand, values, costs = _validate_game(
        preferences, capacity, demand, values, costs
    )
    ratio = aggregate_capacity(capacity, preferences) / demand
    utility = np.where(ratio <= 1.0, ratio - 0.5 * ratio**2, 0.5)
    return float(np.sum(values * utility) - np.sum(costs * preferences))


def marginal_payoff(
    preferences: np.ndarray,
    capacity: np.ndarray,
    demand: np.ndarray,
    values: np.ndarray,
    costs: np.ndarray,
) -> np.ndarray:
    preferences, capacity, demand, values, costs = _validate_game(
        preferences, capacity, demand, values, costs
    )
    ratio = aggregate_capacity(capacity, preferences) / demand
    pressure = np.maximum(1.0 - ratio, 0.0)
    return capacity / demand[None, :] * values[None, :] * pressure[None, :] - costs


def plain_payoff(
    preferences: np.ndarray,
    capacity: np.ndarray,
    demand: np.ndarray,
    values: np.ndarray,
    costs: np.ndarray,
) -> np.ndarray:
    preferences, capacity, demand, values, costs = _validate_game(
        preferences, capacity, demand, values, costs
    )
    ratio = aggregate_capacity(capacity, preferences) / demand
    pressure = np.maximum(1.0 - ratio, 0.0)
    return values[None, :] * pressure[None, :] - costs
