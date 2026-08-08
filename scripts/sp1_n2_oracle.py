"""Centralized exact oracle for SP1.N2: heterogeneous, atomic coalitions.

N2 changes exactly one hypothesis of N1. Robots keep an individual payload
capacity ``c_i`` instead of a common ``c``, so a load is no longer covered by
*counting* robots but by *summing* their capacities:

    min   sum_ik d_ik y_ik  (+ lambda_n sum_ik y_ik + lambda_e sum_k e_k)
    s.t.  sum_k y_ik <= 1                    every robot serves at most one load
          sum_i c_i y_ik >= m_k              every load is covered
          y_ik in {0,1}                      robots are atomic

The module deliberately builds the LP relaxation and the MILP from the *same*
constructor: the only difference is the integrality vector. Any comparison of
their optima would be meaningless if the two models could drift apart.

Two design decisions are recorded here rather than buried in a campaign:

1. The primary oracle minimizes distance only. The N1 LSAP minimizes distance,
   so a secondary penalty would confound "the model changed" with "the
   objective changed" in every N1-N2 comparison.
2. ``lambda_e`` is *not* a slack penalty. Because ``e_k`` is bounded below by
   the recruited surplus and carries a positive cost, it saturates at the
   optimum, and ``lambda_e * sum_k e_k`` collapses to ``lambda_e * sum_ik c_i
   y_ik`` up to a constant: a linear price on recruited kilograms. It is kept
   available as a declared sensitivity, never as the default.
"""

from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import LinearConstraint, milp
from scipy.sparse import coo_matrix

FloatArray = NDArray[np.float64]

# Frozen solver-status semantics, reused unchanged by later levels.
OPTIMAL = "OPTIMAL"
FEASIBLE_TIME_LIMIT = "FEASIBLE_TIME_LIMIT"
INFEASIBLE = "INFEASIBLE"
UNKNOWN = "UNKNOWN"
STATUS_CLASSES = (OPTIMAL, FEASIBLE_TIME_LIMIT, INFEASIBLE, UNKNOWN)

# Anything strictly inside this band counts as a fractional decision.
FRACTIONAL_EPS = 1e-6


@dataclass(frozen=True)
class CoalitionModel:
    """The shared LP/MILP data. Integrality is applied at solve time."""

    objective: FloatArray
    constraint_matrix: Any
    lower_bounds: FloatArray
    upper_bounds: FloatArray
    variable_lower: FloatArray
    variable_upper: FloatArray
    robot_count: int
    load_count: int
    capacities: FloatArray
    masses: FloatArray
    distance: FloatArray
    excess_variables: bool

    @property
    def assignment_count(self) -> int:
        return self.robot_count * self.load_count


@dataclass(frozen=True)
class OracleResult:
    """One solve, with feasibility and certification kept separate."""

    status: str
    integral: bool
    objective: float
    distance_objective: float
    bound: float
    mip_gap: float
    node_count: int
    runtime_s: float
    assignment: FloatArray | None
    fractional_count: int
    max_fractionality: float

    @property
    def has_incumbent(self) -> bool:
        return self.assignment is not None

    @property
    def certified_optimal(self) -> bool:
        return self.status == OPTIMAL


def build_model(
    *,
    capacities: Sequence[float],
    masses: Sequence[float],
    distance: FloatArray,
    lambda_excess: float = 0.0,
    lambda_robot: float = 0.0,
) -> CoalitionModel:
    """Assemble the N2 coalition model once for both relaxations.

    ``lambda_excess`` introduces the surplus variables ``e_k``; with the
    default of zero they are omitted entirely, because an unpriced ``e_k``
    would be a free variable that only widens the search space.
    """

    capacity_array = np.asarray(capacities, dtype=float)
    mass_array = np.asarray(masses, dtype=float)
    distance_array = np.asarray(distance, dtype=float)
    robot_count = capacity_array.size
    load_count = mass_array.size
    if distance_array.shape != (robot_count, load_count):
        raise ValueError(
            "distance must be shaped (robots, loads); got "
            f"{distance_array.shape}"
        )
    if np.any(capacity_array <= 0.0) or np.any(mass_array <= 0.0):
        raise ValueError("capacities and masses must be strictly positive.")
    if lambda_excess < 0.0 or lambda_robot < 0.0:
        raise ValueError("objective weights must be non-negative.")

    use_excess = lambda_excess > 0.0
    assignment_count = robot_count * load_count
    variable_count = assignment_count + (load_count if use_excess else 0)

    objective = np.empty(variable_count, dtype=float)
    objective[:assignment_count] = distance_array.reshape(-1) + lambda_robot
    if use_excess:
        objective[assignment_count:] = lambda_excess

    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    row = 0

    # Each robot serves at most one load.
    for i in range(robot_count):
        for k in range(load_count):
            rows.append(row)
            columns.append(i * load_count + k)
            values.append(1.0)
        lower.append(-np.inf)
        upper.append(1.0)
        row += 1

    # Each load receives at least its demanded capacity.
    for k in range(load_count):
        for i in range(robot_count):
            rows.append(row)
            columns.append(i * load_count + k)
            values.append(float(capacity_array[i]))
        lower.append(float(mass_array[k]))
        upper.append(np.inf)
        row += 1

    if use_excess:
        # e_k >= recruited_k - m_k, priced so it saturates at the optimum.
        for k in range(load_count):
            for i in range(robot_count):
                rows.append(row)
                columns.append(i * load_count + k)
                values.append(float(capacity_array[i]))
            rows.append(row)
            columns.append(assignment_count + k)
            values.append(-1.0)
            lower.append(-np.inf)
            upper.append(float(mass_array[k]))
            row += 1

    matrix = coo_matrix(
        (values, (rows, columns)), shape=(row, variable_count)
    ).tocsr()
    variable_lower = np.zeros(variable_count, dtype=float)
    variable_upper = np.full(variable_count, np.inf, dtype=float)
    variable_upper[:assignment_count] = 1.0

    return CoalitionModel(
        objective=objective,
        constraint_matrix=matrix,
        lower_bounds=np.asarray(lower, dtype=float),
        upper_bounds=np.asarray(upper, dtype=float),
        variable_lower=variable_lower,
        variable_upper=variable_upper,
        robot_count=robot_count,
        load_count=load_count,
        capacities=capacity_array,
        masses=mass_array,
        distance=distance_array,
        excess_variables=use_excess,
    )


def _classify(status: int, has_incumbent: bool) -> str:
    """Map a SciPy/HiGHS status onto the frozen four-way semantics."""

    if status == 0:
        return OPTIMAL
    if status == 2:
        return INFEASIBLE
    if status == 1:
        # Time or iteration limit: an incumbent may or may not exist.
        return FEASIBLE_TIME_LIMIT if has_incumbent else UNKNOWN
    return UNKNOWN


def solve(
    model: CoalitionModel,
    *,
    integral: bool,
    time_limit_s: float | None = None,
    mip_rel_gap: float = 0.0,
) -> OracleResult:
    """Solve the model as a MILP (``integral``) or as its LP relaxation."""

    integrality = np.zeros(model.objective.size, dtype=np.int32)
    if integral:
        integrality[: model.assignment_count] = 1

    options: dict[str, Any] = {"mip_rel_gap": mip_rel_gap}
    if time_limit_s is not None:
        options["time_limit"] = float(time_limit_s)

    started = time.perf_counter()
    result = milp(
        c=model.objective,
        constraints=LinearConstraint(
            model.constraint_matrix, model.lower_bounds, model.upper_bounds
        ),
        bounds=(model.variable_lower, model.variable_upper),
        integrality=integrality,
        options=options,
    )
    runtime = time.perf_counter() - started

    solution = None if result.x is None else np.asarray(result.x, dtype=float)
    status = _classify(int(result.status), solution is not None)

    if solution is None:
        assignment = None
        distance_objective = math.nan
        fractional_count = 0
        max_fractionality = 0.0
    else:
        assignment = solution[: model.assignment_count].reshape(
            model.robot_count, model.load_count
        )
        distance_objective = float(np.sum(model.distance * assignment))
        interior = (assignment > FRACTIONAL_EPS) & (
            assignment < 1.0 - FRACTIONAL_EPS
        )
        fractional_count = int(np.count_nonzero(interior))
        max_fractionality = (
            float(np.max(np.minimum(assignment, 1.0 - assignment)))
            if assignment.size
            else 0.0
        )

    return OracleResult(
        status=status,
        integral=integral,
        objective=(
            float(result.fun) if result.fun is not None else math.nan
        ),
        distance_objective=distance_objective,
        bound=float(getattr(result, "mip_dual_bound", math.nan) or math.nan),
        mip_gap=float(getattr(result, "mip_gap", math.nan) or 0.0),
        node_count=int(getattr(result, "mip_node_count", 0) or 0),
        runtime_s=runtime,
        assignment=assignment,
        fractional_count=fractional_count,
        max_fractionality=max_fractionality,
    )


def enumerate_optimum(
    model: CoalitionModel,
    *,
    max_states: int = 5_000_000,
) -> tuple[str, float, FloatArray | None]:
    """Exhaustively minimise over every atomic assignment.

    Each robot independently picks one load or stays idle, so the state space
    is ``(K+1)**N``. This exists to check the solver, so it is written to be
    obviously correct rather than fast, and refuses to run when the space is
    too large to enumerate honestly.
    """

    robot_count = model.robot_count
    load_count = model.load_count
    base = load_count + 1
    states = base**robot_count
    if states > max_states:
        raise ValueError(
            f"{states:,} states exceeds the {max_states:,} enumeration budget."
        )

    capacities = model.capacities
    masses = model.masses
    # Column 0 is the idle choice and costs nothing.
    cost_table = np.zeros((robot_count, base), dtype=float)
    cost_table[:, 1:] = model.distance
    powers = base ** np.arange(robot_count, dtype=np.int64)

    best_cost = math.inf
    best_digits: NDArray[np.int64] | None = None
    chunk = max(1, min(states, 262_144))
    robot_index = np.arange(robot_count)

    for start in range(0, states, chunk):
        stop = min(start + chunk, states)
        # digits[s, i] in {0..K}: which load robot i serves, 0 = idle.
        digits = (np.arange(start, stop)[:, None] // powers) % base
        cost = cost_table[robot_index[None, :], digits].sum(axis=1)
        admissible = np.ones(digits.shape[0], dtype=bool)
        for load in range(load_count):
            recruited = (capacities[None, :] * (digits == load + 1)).sum(axis=1)
            admissible &= recruited >= masses[load] - 1e-9
        if not admissible.any():
            continue
        cost = np.where(admissible, cost, np.inf)
        position = int(np.argmin(cost))
        if cost[position] < best_cost:
            best_cost = float(cost[position])
            best_digits = digits[position].copy()

    if best_digits is None:
        return INFEASIBLE, math.inf, None

    assignment = np.zeros((robot_count, load_count), dtype=float)
    for i in range(robot_count):
        selection = int(best_digits[i])
        if selection:
            assignment[i, selection - 1] = 1.0
    return OPTIMAL, float(best_cost), assignment


def recruited_capacity(
    model: CoalitionModel, assignment: FloatArray
) -> FloatArray:
    """Capacity actually gathered per load by a (possibly fractional) plan."""

    return model.capacities @ assignment


def capacity_pressure(
    capacities: Sequence[float], masses: Sequence[float]
) -> float:
    """Global demand-to-supply ratio ``rho = sum m_k / sum c_i``."""

    supply = float(np.sum(np.asarray(capacities, dtype=float)))
    if supply <= 0.0:
        return math.inf
    return float(np.sum(np.asarray(masses, dtype=float))) / supply


def integrality_gap(
    milp_objective: float,
    lp_objective: float,
    *,
    floor: float = 1e-9,
) -> tuple[float, float]:
    """Return the absolute and relative integrality gap.

    The relative form divides by the MILP optimum, which is a sum of positive
    distances and is therefore safely bounded away from zero here; the floor
    guards the degenerate case where every recruited robot sits on its load.
    """

    absolute = milp_objective - lp_objective
    if not math.isfinite(absolute):
        return math.nan, math.nan
    if abs(milp_objective) <= floor:
        return absolute, math.nan
    return absolute, absolute / milp_objective
