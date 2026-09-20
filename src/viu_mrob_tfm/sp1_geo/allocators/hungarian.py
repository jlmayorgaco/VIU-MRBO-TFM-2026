"""Hungarian slot control restricted to separable F0 worlds."""

from __future__ import annotations

import time

import numpy as np
from scipy.optimize import linear_sum_assignment

from ..models import ActionCatalog, AllocationResult, Assignment, GeoWorld


def allocate_hungarian_slots(
    world: GeoWorld,
    catalog: ActionCatalog,
) -> AllocationResult:
    started = time.perf_counter()
    if world.family != "F0_easy_separable":
        return AllocationResult(
            method="hungarian_slots",
            engine="hungarian",
            signal="scalar_capacity",
            assignment=Assignment.empty(world.n_robots),
            status="not_applicable_nonseparable",
            runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
            diagnostics={
                "information_scope": "global_control",
                "applicability": "F0_slot_decomposable_only",
            },
        )

    virtual_slots: list[tuple[int, int]] = []
    for load_index, load in enumerate(world.loads):
        for slot_index in range(min(load.min_coalition_size, len(load.slots))):
            virtual_slots.append((load_index, slot_index))
    real_columns = len(virtual_slots)
    # Dummy idle columns make optional assignment explicit.
    matrix = np.zeros((world.n_robots, real_columns + world.n_robots), dtype=float)
    matrix[:, :real_columns] = 1e6
    for column, (load_index, slot_index) in enumerate(virtual_slots):
        value_share = (
            world.loads[load_index].priority_value
            / world.loads[load_index].min_coalition_size
        )
        for robot in range(world.n_robots):
            action = catalog.action_for(robot, load_index, slot_index)
            if action is not None and catalog.compatible[action]:
                matrix[robot, column] = catalog.costs[action] - value_share
    rows, columns = linear_sum_assignment(matrix)
    assignment = np.full(world.n_robots, -1, dtype=int)
    for robot, column in zip(rows, columns, strict=True):
        if column >= real_columns or matrix[robot, column] >= 1e5:
            continue
        load_index, slot_index = virtual_slots[column]
        action = catalog.action_for(int(robot), load_index, slot_index)
        if action is not None:
            assignment[int(robot)] = int(action)
    return AllocationResult(
        method="hungarian_slots",
        engine="hungarian",
        signal="scalar_capacity",
        assignment=Assignment(assignment),
        status="optimal_separable",
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        iterations=1,
        rounds=1,
        diagnostics={
            "information_scope": "global_control",
            "applicability": "F0_slot_decomposable_only",
        },
    )


__all__ = ["allocate_hungarian_slots"]
