"""Deterministic greedy controls for SP1-GEO."""

from __future__ import annotations

import time

import numpy as np

from ..models import ActionCatalog, AllocationResult, Assignment, GeoWorld, SignalName
from ..welfare import marginal_payoffs


def allocate_greedy(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    signal: SignalName = "marginal_physical",
    nearest_only: bool = True,
) -> AllocationResult:
    started = time.perf_counter()
    assignment = np.full(world.n_robots, -1, dtype=int)
    occupied: set[tuple[int, int]] = set()
    zero = np.zeros(catalog.n_actions, dtype=float)
    payoff = marginal_payoffs(world, catalog, zero, signal)
    if nearest_only:
        order = np.lexsort(
            (
                catalog.slot_index,
                catalog.load_index,
                catalog.travel_distance_m,
            )
        )
    else:
        order = np.lexsort(
            (
                catalog.costs,
                -payoff,
            )
        )
    for action in order:
        if not catalog.compatible[action]:
            continue
        robot = int(catalog.robot_index[action])
        key = (int(catalog.load_index[action]), int(catalog.slot_index[action]))
        if assignment[robot] >= 0 or key in occupied:
            continue
        if not nearest_only and payoff[action] <= 0.0:
            continue
        assignment[robot] = int(action)
        occupied.add(key)
    runtime = 1_000.0 * (time.perf_counter() - started)
    return AllocationResult(
        method="greedy_nearest" if nearest_only else "greedy_marginal",
        engine="greedy",
        signal=signal,
        assignment=Assignment(assignment),
        status="success",
        runtime_negotiation_ms=runtime,
        iterations=1,
        rounds=1,
        diagnostics={"information_scope": "global_control"},
    )


__all__ = ["allocate_greedy"]
