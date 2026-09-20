"""Common finite augmenting recovery applied to every allocator."""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

import numpy as np

from .certifier import (
    bounded_wrench_residual,
    certify_assignment,
    filter_certified_assignment,
    physical_welfare,
)
from .models import ActionCatalog, Assignment, GeoWorld, RecoveryResult


def _state_key(assignment: Assignment) -> tuple[int, ...]:
    return tuple(int(value) for value in assignment.action_by_robot)


def _occupied_slots(assignment: Assignment, catalog: ActionCatalog) -> set[tuple[int, int]]:
    return {
        (int(catalog.load_index[action]), int(catalog.slot_index[action]))
        for action in assignment.selected_actions()
    }


def _rank_actions(
    world: GeoWorld,
    catalog: ActionCatalog,
    load_index: int,
    available_robots: set[int],
) -> np.ndarray:
    actions = np.flatnonzero(
        catalog.compatible
        & (catalog.load_index == int(load_index))
        & np.isin(catalog.robot_index, np.fromiter(available_robots, dtype=int))
    )
    if actions.size == 0:
        return actions
    demand = np.maximum(catalog.physical_demands[load_index], 1e-12)
    normalized_gain = np.sum(
        np.minimum(catalog.physical_contributions[actions] / demand, 1.0), axis=1
    )
    score = normalized_gain - 0.20 * catalog.costs[actions]
    order = np.lexsort(
        (
            catalog.slot_index[actions],
            catalog.robot_index[actions],
            catalog.costs[actions],
            -score,
        )
    )
    return actions[order]


def _load_feasible(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
    load_index: int,
) -> bool:
    """Cheap exact prefilter for one candidate load.

    Recovery constructs robot-valid, slot-unique proposals and never changes
    previously certified loads. Therefore only the candidate load needs to be
    rechecked during chain construction. A full world certificate is still
    computed before any proposal can be accepted.
    """

    actions = np.array(
        [
            int(action)
            for action in assignment.selected_actions()
            if int(catalog.load_index[action]) == int(load_index)
        ],
        dtype=int,
    )
    if actions.size == 0 or np.any(~catalog.compatible[actions]):
        return False
    slots = catalog.slot_index[actions]
    if len(set(slots.tolist())) != len(slots):
        return False
    load = world.loads[load_index]
    capacity = float(np.sum(catalog.physical_contributions[actions, 0]))
    if (
        capacity < load.min_capacity_kg - 1e-9
        or capacity > load.max_capacity_kg + 1e-9
        or actions.size < load.min_coalition_size
    ):
        return False
    for action in actions:
        robot = world.robots[int(catalog.robot_index[action])]
        battery_margin = (
            robot.battery_wh
            - robot.safe_battery_wh
            - catalog.mission_energy_wh[action]
        )
        if battery_margin < -1e-9:
            return False
    _, residual, _ = bounded_wrench_residual(
        catalog.wrench_columns_per_n[actions],
        catalog.force_upper_n[actions],
        load.required_wrench,
    )
    if residual > load.wrench_tolerance + 1e-12:
        return False
    torque_columns = catalog.wrench_columns_per_n[actions, 2]
    if load.required_wrench[2] > 1e-12:
        return bool(np.any(torque_columns > 1e-12))
    if load.required_wrench[2] < -1e-12:
        return bool(np.any(torque_columns < -1e-12))
    return True


def _candidate_for_load(
    world: GeoWorld,
    catalog: ActionCatalog,
    base: Assignment,
    load_index: int,
    *,
    max_chain_length: int,
    candidates_per_load: int,
) -> list[tuple[Assignment, int]]:
    assigned_robots = {
        robot for robot, action in enumerate(base.action_by_robot) if action >= 0
    }
    available = set(range(world.n_robots)) - assigned_robots
    ranked = _rank_actions(world, catalog, load_index, available)
    if ranked.size == 0:
        return []
    starts = ranked[: min(int(candidates_per_load), len(ranked))]
    candidates: list[tuple[Assignment, int]] = []
    for first in starts:
        proposal = base.action_by_robot.copy()
        used_slots = _occupied_slots(base, catalog)
        ordered = np.concatenate(
            [np.array([first], dtype=int), ranked[ranked != first]]
        )
        changes = 0
        for action in ordered:
            robot = int(catalog.robot_index[action])
            slot_key = (load_index, int(catalog.slot_index[action]))
            if proposal[robot] >= 0 or slot_key in used_slots:
                continue
            proposal[robot] = int(action)
            used_slots.add(slot_key)
            changes += 1
            if changes > max_chain_length:
                break
            candidate = Assignment(proposal.copy())
            if _load_feasible(world, catalog, candidate, load_index):
                candidates.append((candidate, changes))
                break
    unique: dict[tuple[int, ...], tuple[Assignment, int]] = {}
    for candidate, length in candidates:
        unique.setdefault(_state_key(candidate), (candidate, length))
    return list(unique.values())


def _cost_reducing_swaps(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
) -> Iterable[tuple[Assignment, int, dict[str, Any]]]:
    free = set(np.flatnonzero(assignment.action_by_robot < 0).tolist())
    if not free:
        return []
    proposals: list[tuple[Assignment, int, dict[str, Any]]] = []
    for old_robot, old_action in enumerate(assignment.action_by_robot):
        if old_action < 0:
            continue
        load = int(catalog.load_index[old_action])
        slot = int(catalog.slot_index[old_action])
        for new_robot in sorted(free):
            replacement = catalog.action_for(new_robot, load, slot)
            if replacement is None or not bool(catalog.compatible[replacement]):
                continue
            if catalog.costs[replacement] >= catalog.costs[old_action] - 1e-12:
                continue
            values = assignment.action_by_robot.copy()
            values[old_robot] = -1
            values[new_robot] = replacement
            proposals.append(
                (
                    Assignment(values),
                    2,
                    {
                        "event": "swap",
                        "load_index": load,
                        "old_robot": old_robot,
                        "new_robot": new_robot,
                    },
                )
            )
    return proposals


def _transition_welfare(
    catalog: ActionCatalog,
    current: Assignment,
    proposal: Assignment,
    current_value: float,
    *,
    added_service_value: float = 0.0,
) -> float:
    changed = current.action_by_robot != proposal.action_by_robot
    old_actions = current.action_by_robot[
        changed & (current.action_by_robot >= 0)
    ]
    new_actions = proposal.action_by_robot[
        changed & (proposal.action_by_robot >= 0)
    ]
    removed_cost = (
        float(np.sum(catalog.costs[old_actions]))
        if old_actions.size
        else 0.0
    )
    added_cost = (
        float(np.sum(catalog.costs[new_actions]))
        if new_actions.size
        else 0.0
    )
    return float(
        current_value + added_service_value + removed_cost - added_cost
    )


def recover_assignment(
    world: GeoWorld,
    catalog: ActionCatalog,
    raw_assignment: Assignment,
    *,
    delta: float = 1e-9,
    max_chain_length: int = 12,
    candidates_per_load: int = 30,
    enable_swaps: bool = True,
) -> RecoveryResult:
    """Repair a native intention with finite, strictly improving changes."""

    started = time.perf_counter()
    raw_certificate = certify_assignment(world, catalog, raw_assignment)
    current = filter_certified_assignment(raw_assignment, catalog, raw_certificate)
    certificate = certify_assignment(world, catalog, current)
    current_value = physical_welfare(world, catalog, current, certificate)
    trajectory = [current_value]
    visited = {_state_key(current)}
    events: list[dict[str, Any]] = []
    maximum_chain = 0
    cycle_detected = False

    while True:
        served = {
            item.load_index
            for item in certificate.load_certificates
            if item.feasible
        }
        candidates: list[tuple[float, Assignment, int, dict[str, Any]]] = []
        for load_index in range(world.n_loads):
            if load_index in served:
                continue
            for proposal, chain_length in _candidate_for_load(
                world,
                catalog,
                current,
                load_index,
                max_chain_length=max_chain_length,
                candidates_per_load=candidates_per_load,
            ):
                key = _state_key(proposal)
                if key in visited:
                    cycle_detected = True
                    continue
                value = _transition_welfare(
                    catalog,
                    current,
                    proposal,
                    current_value,
                    added_service_value=world.loads[
                        load_index
                    ].priority_value,
                )
                if value >= current_value + float(delta):
                    candidates.append(
                        (
                            value,
                            proposal,
                            chain_length,
                            {
                                "event": "augment",
                                "load_index": load_index,
                                "chain_length": chain_length,
                            },
                        )
                    )
        if enable_swaps:
            for proposal, chain_length, event in _cost_reducing_swaps(
                world, catalog, current
            ):
                key = _state_key(proposal)
                if key in visited:
                    cycle_detected = True
                    continue
                load_index = int(event["load_index"])
                if not _load_feasible(
                    world, catalog, proposal, load_index
                ):
                    continue
                value = _transition_welfare(
                    catalog,
                    current,
                    proposal,
                    current_value,
                )
                if value >= current_value + float(delta):
                    candidates.append((value, proposal, chain_length, event))
        if not candidates:
            break
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[2],
                _state_key(item[1]),
            )
        )
        value, proposal, chain_length, event = candidates[0]
        previous = current
        current = proposal
        certificate = certify_assignment(world, catalog, current)
        certified_served = {
            item.load_index
            for item in certificate.load_certificates
            if item.feasible
        }
        if not served.issubset(certified_served):
            raise RuntimeError(
                "Recovery transition invalidated a previously certified load."
            )
        if event["event"] == "augment" and int(
            event["load_index"]
        ) not in certified_served:
            raise RuntimeError(
                "Recovery local prefilter disagreed with the global certifier."
            )
        certified_value = physical_welfare(
            world, catalog, current, certificate
        )
        if not np.isclose(certified_value, value, atol=1e-10, rtol=1e-10):
            raise RuntimeError(
                "Incremental and globally certified welfare disagree."
            )
        current_value = float(value)
        visited.add(_state_key(current))
        maximum_chain = max(maximum_chain, int(chain_length))
        changed = int(np.sum(previous.action_by_robot != current.action_by_robot))
        events.append(
            {
                **event,
                "step": len(events) + 1,
                "accepted": True,
                "welfare": current_value,
                "robots_changed": changed,
            }
        )
        trajectory.append(current_value)

    total_changed = int(
        np.sum(raw_assignment.action_by_robot != current.action_by_robot)
    )
    runtime_ms = 1_000.0 * (time.perf_counter() - started)
    monotone = all(
        later >= earlier + float(delta) - 1e-12
        for earlier, later in zip(trajectory, trajectory[1:])
    )
    return RecoveryResult(
        assignment=current,
        certificate=certificate,
        potential_trajectory=tuple(float(value) for value in trajectory),
        steps=len(events),
        augmenting_path_length=maximum_chain,
        robots_changed=total_changed,
        visited_states=len(visited),
        terminated=True,
        cycle_detected=cycle_detected and not monotone,
        runtime_ms=runtime_ms,
        events=tuple(events),
    )


__all__ = ["recover_assignment"]
