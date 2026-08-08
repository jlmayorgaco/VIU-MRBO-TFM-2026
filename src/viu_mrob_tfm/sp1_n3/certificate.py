"""Decomposition of the N2 feasibility certificate, and its two objectives.

The algebraic identity is exact:

    y feasible  <=>  [for all i: sum_k y_ik <= 1]  and  [for all k: Q_k(y) >= m_k]

so the predicate splits into a part each robot owns and a part each coalition
owns. That is a *decomposition*, not a claim that a robot can verify its half
at runtime: verifying ``Q_k`` locally would need a consistent, complete view of
the coalition's membership, which only a protocol that pays for it can provide.

The verdicts below are therefore computed post hoc by the observer. They are
allowed to describe the run; they are never allowed to steer, stop or repair it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


FEASIBLE = "FEASIBLE"
CAPACITY_DEFICIT = "CAPACITY_DEFICIT"
ROBOT_CONFLICT = "ROBOT_CONFLICT"
DEFICIT_AND_CONFLICT = "DEFICIT_AND_CONFLICT"

CERTIFICATE_STATUS = (
    FEASIBLE,
    CAPACITY_DEFICIT,
    ROBOT_CONFLICT,
    DEFICIT_AND_CONFLICT,
)

TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class Certificate:
    status: str
    total_deficit: float
    distance_cost: float
    conflicts: int
    unserved_loads: int
    excess_capacity: float
    assigned_robots: int
    coalition_sizes: tuple[int, ...]

    @property
    def feasible(self) -> bool:
        return self.status == FEASIBLE

    def as_dict(self) -> dict[str, object]:
        return {
            "raw_certificate": self.status,
            "total_deficit": self.total_deficit,
            "distance_cost": self.distance_cost,
            "conflicts": self.conflicts,
            "unserved_loads": self.unserved_loads,
            "excess_capacity": self.excess_capacity,
            "assigned_robots": self.assigned_robots,
            "max_coalition_size": max(self.coalition_sizes, default=0),
        }


def coverage(assignment: np.ndarray, capacities: np.ndarray, n_loads: int) -> np.ndarray:
    """``Q_k(y) = sum_i c_i y_ik`` from a one-load-per-robot assignment vector."""

    assignment = np.asarray(assignment, dtype=int)
    capacities = np.asarray(capacities, dtype=float)
    totals = np.zeros(int(n_loads), dtype=float)
    for robot, load in enumerate(assignment):
        # Out-of-range entries contribute nothing; :func:`certify` reports them
        # as ROBOT_CONFLICT rather than letting them raise here, so a buggy
        # allocator surfaces as a bad certificate instead of a traceback.
        if 0 <= load < int(n_loads):
            totals[load] += capacities[robot]
    return totals


def total_deficit(
    assignment: np.ndarray, capacities: np.ndarray, demands: np.ndarray
) -> float:
    """``D(y) = sum_k [m_k - Q_k(y)]_+``, the lexicographic first objective."""

    demands = np.asarray(demands, dtype=float)
    served = coverage(assignment, capacities, len(demands))
    return float(np.maximum(demands - served, 0.0).sum())


def distance_cost(assignment: np.ndarray, distances: np.ndarray) -> float:
    """``J(y) = sum_ik d_ik y_ik``, the frozen N2 objective."""

    assignment = np.asarray(assignment, dtype=int)
    distances = np.asarray(distances, dtype=float)
    n_loads = distances.shape[1]
    return float(
        sum(
            distances[robot, load]
            for robot, load in enumerate(assignment)
            if 0 <= load < n_loads
        )
    )


def certify(
    assignment: np.ndarray,
    capacities: np.ndarray,
    demands: np.ndarray,
    distances: np.ndarray,
) -> Certificate:
    """Post-hoc verdict on one raw allocation.

    ``assignment[i]`` is the single load robot ``i`` committed to, or ``-1``.
    That representation makes ``sum_k y_ik <= 1`` structural, so a conflict can
    only appear if an algorithm returns something outside it; the check stays
    because an implementation bug must surface as ROBOT_CONFLICT rather than be
    silently absorbed.
    """

    assignment = np.asarray(assignment, dtype=int)
    capacities = np.asarray(capacities, dtype=float)
    demands = np.asarray(demands, dtype=float)
    n_loads = len(demands)

    conflicts = int(np.sum(assignment >= n_loads) + np.sum(assignment < -1))
    served = coverage(assignment, capacities, n_loads)
    shortfall = np.maximum(demands - served, 0.0)
    deficit = float(shortfall.sum())
    unserved = int(np.sum(shortfall > TOLERANCE))
    excess = float(np.maximum(served - demands, 0.0)[served > TOLERANCE].sum())

    if conflicts and deficit > TOLERANCE:
        status = DEFICIT_AND_CONFLICT
    elif conflicts:
        status = ROBOT_CONFLICT
    elif deficit > TOLERANCE:
        status = CAPACITY_DEFICIT
    else:
        status = FEASIBLE

    sizes = tuple(int(np.sum(assignment == load)) for load in range(n_loads))
    valid = (assignment >= 0) & (assignment < n_loads)
    return Certificate(
        status=status,
        total_deficit=deficit,
        distance_cost=distance_cost(assignment, distances),
        conflicts=conflicts,
        unserved_loads=unserved,
        excess_capacity=excess,
        assigned_robots=int(np.sum(valid)),
        coalition_sizes=sizes,
    )


def lexicographic_key(
    assignment: np.ndarray,
    capacities: np.ndarray,
    demands: np.ndarray,
    distances: np.ndarray,
) -> tuple[float, float]:
    """``(D, J)``. Lower is better, compared lexicographically.

    This replaces the tuned ``lambda_d`` / ``lambda_e`` penalties: the deficit
    is reduced first, distance only at equal deficit, and once ``D = 0`` no
    move that breaks feasibility can ever look like an improvement. Nothing to
    tune, and the problem being solved stays exactly N2's.
    """

    return (
        total_deficit(assignment, capacities, demands),
        distance_cost(assignment, distances),
    )


__all__ = [
    "CAPACITY_DEFICIT",
    "CERTIFICATE_STATUS",
    "Certificate",
    "DEFICIT_AND_CONFLICT",
    "FEASIBLE",
    "ROBOT_CONFLICT",
    "TOLERANCE",
    "certify",
    "coverage",
    "distance_cost",
    "lexicographic_key",
    "total_deficit",
]
