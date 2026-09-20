"""Exact small-instance DPOP diagnostic for the coalition assignment DCOP.

The quota constraint for each load couples every robot.  On the chain
pseudo-tree used here, that global factor gives the deepest agent a separator
containing all preceding robots.  The implementation deliberately retains the
resulting exponential utility table instead of hiding it behind a central
MILP.  It is therefore useful as an exact distributed reference on small
instances and as a direct measurement of DPOP's induced-width limitation.

The Python process simulates message construction and value propagation.  A
robot in the conceptual protocol receives only its child UTIL table and the
chosen actions of its ancestors during VALUE propagation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import time

import numpy as np

from viu_mrob_tfm.sp1_n3.certificate import certify
from viu_mrob_tfm.sp1_n3.worlds import World


FLOAT64_BYTES = 8
VALUE_MESSAGE_BYTES = 8


@dataclass(frozen=True, slots=True)
class DPOPResult:
    assignment: np.ndarray
    feasible: bool
    objective: float
    runtime_ms: float
    utility_messages: int
    value_messages: int
    utility_entries: int
    payload_bytes: int
    induced_width: int
    profiles_evaluated: int

    def as_dict(self) -> dict[str, object]:
        return {
            "method": "dpop_exact_small",
            "feasible": self.feasible,
            "distance_cost": self.objective,
            "runtime_ms": self.runtime_ms,
            "messages": self.utility_messages + self.value_messages,
            "bytes": self.payload_bytes,
            "utility_messages": self.utility_messages,
            "value_messages": self.value_messages,
            "utility_entries": self.utility_entries,
            "induced_width": self.induced_width,
            "profiles_evaluated": self.profiles_evaluated,
        }


def _profile_feasible(
    profile: tuple[int, ...], capacities: np.ndarray, demands: np.ndarray
) -> bool:
    q = np.zeros(len(demands), dtype=float)
    for robot, load in enumerate(profile):
        if load >= 0:
            q[load] += float(capacities[robot])
    return bool(np.all(q + 1e-9 >= demands))


def solve_dpop_exact_small(world: World, *, max_profiles: int = 2_000_000) -> DPOPResult:
    """Solve the atomic assignment exactly through chain-pseudo-tree DPOP.

    ``max_profiles`` is an explicit safety limit.  Exceeding it raises instead
    of silently replacing DPOP by another solver or returning a partial table.
    """

    started = time.perf_counter()
    n = int(world.n_robots)
    k = int(world.n_loads)
    domain = tuple(range(-1, k))
    profiles = len(domain) ** n
    if profiles > int(max_profiles):
        raise ValueError(
            f"DPOP diagnostic requires {profiles:,} profiles; limit is {max_profiles:,}"
        )
    if n == 0:
        feasible = bool(np.all(np.asarray(world.demands) <= 1e-9))
        return DPOPResult(
            assignment=np.empty(0, dtype=int),
            feasible=feasible,
            objective=0.0 if feasible else float("inf"),
            runtime_ms=1_000.0 * (time.perf_counter() - started),
            utility_messages=0,
            value_messages=0,
            utility_entries=0,
            payload_bytes=0,
            induced_width=0,
            profiles_evaluated=1,
        )

    # The deepest robot owns the high-arity feasibility factor.  Eliminating
    # its action creates a UTIL table indexed by every ancestor action.
    policies: dict[int, dict[tuple[int, ...], int]] = {}
    deepest = n - 1
    child_table: dict[tuple[int, ...], float] = {}
    child_policy: dict[tuple[int, ...], int] = {}
    evaluated = 0
    for prefix in product(domain, repeat=deepest):
        best_value = float("inf")
        best_action = -1
        for action in domain:
            evaluated += 1
            profile = prefix + (action,)
            if not _profile_feasible(profile, world.capacities, world.demands):
                continue
            value = 0.0 if action < 0 else float(world.distances[deepest, action])
            if value < best_value:
                best_value = value
                best_action = action
        child_table[prefix] = best_value
        child_policy[prefix] = best_action
    policies[deepest] = child_policy
    utility_entries = len(child_table)

    # Each preceding robot joins its unary distance cost with the child's UTIL
    # table and eliminates its own action.
    for robot in range(n - 2, 0, -1):
        parent_table: dict[tuple[int, ...], float] = {}
        parent_policy: dict[tuple[int, ...], int] = {}
        for prefix in product(domain, repeat=robot):
            best_value = float("inf")
            best_action = -1
            for action in domain:
                suffix_key = prefix + (action,)
                value = child_table[suffix_key]
                if action >= 0:
                    value += float(world.distances[robot, action])
                if value < best_value:
                    best_value = value
                    best_action = action
            parent_table[prefix] = best_value
            parent_policy[prefix] = best_action
        policies[robot] = parent_policy
        child_table = parent_table
        utility_entries += len(child_table)

    best_root_value = float("inf")
    best_root_action = -1
    if n == 1:
        # The deepest table has an empty separator.
        best_root_value = child_table[()]
        best_root_action = policies[0][()]
    else:
        for action in domain:
            value = child_table[(action,)]
            if action >= 0:
                value += float(world.distances[0, action])
            if value < best_root_value:
                best_root_value = value
                best_root_action = action

    feasible = bool(np.isfinite(best_root_value))
    if feasible:
        assignment = np.empty(n, dtype=int)
        assignment[0] = best_root_action
        for robot in range(1, n):
            prefix = tuple(int(value) for value in assignment[:robot])
            assignment[robot] = policies[robot][prefix]
        certificate = certify(
            assignment, world.capacities, world.demands, world.distances
        )
        if not certificate.feasible:
            raise AssertionError("DPOP VALUE propagation reconstructed an infeasible profile")
        if not np.isclose(certificate.distance_cost, best_root_value, atol=1e-9):
            raise AssertionError("DPOP UTIL value disagrees with reconstructed objective")
    else:
        assignment = np.full(n, -1, dtype=int)

    utility_messages = max(n - 1, 0)
    value_messages = max(n - 1, 0)
    payload_bytes = utility_entries * FLOAT64_BYTES + value_messages * VALUE_MESSAGE_BYTES
    return DPOPResult(
        assignment=assignment,
        feasible=feasible,
        objective=float(best_root_value),
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        utility_messages=utility_messages,
        value_messages=value_messages,
        utility_entries=utility_entries,
        payload_bytes=payload_bytes,
        induced_width=max(n - 1, 0),
        profiles_evaluated=evaluated,
    )


__all__ = ["DPOPResult", "solve_dpop_exact_small"]
