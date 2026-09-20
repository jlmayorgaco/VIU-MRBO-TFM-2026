"""Weighted-GRAPE and role/pair-GRAPE-S adaptations."""

from __future__ import annotations

import time

import numpy as np

from ..models import ActionCatalog, AllocationResult, Assignment, GeoWorld, SignalName
from ..welfare import assignment_signal_potential, marginal_payoffs


def _valid_unique(assignment: np.ndarray, catalog: ActionCatalog) -> bool:
    slots: set[tuple[int, int]] = set()
    for robot, action in enumerate(assignment):
        if action < 0:
            continue
        if (
            action >= catalog.n_actions
            or int(catalog.robot_index[action]) != robot
            or not catalog.compatible[action]
        ):
            return False
        key = (int(catalog.load_index[action]), int(catalog.slot_index[action]))
        if key in slots:
            return False
        slots.add(key)
    return True


def _initial_profile(
    world: GeoWorld,
    catalog: ActionCatalog,
    signal: SignalName,
) -> np.ndarray:
    assignment = np.full(world.n_robots, -1, dtype=int)
    occupied: set[tuple[int, int]] = set()
    payoff = marginal_payoffs(
        world, catalog, np.zeros(catalog.n_actions, dtype=float), signal
    )
    order = np.lexsort((catalog.costs, -payoff))
    for action in order:
        if payoff[action] <= 0.0 or not catalog.compatible[action]:
            continue
        robot = int(catalog.robot_index[action])
        key = (int(catalog.load_index[action]), int(catalog.slot_index[action]))
        if assignment[robot] < 0 and key not in occupied:
            assignment[robot] = int(action)
            occupied.add(key)
    return assignment


def _best_unilateral(
    world: GeoWorld,
    catalog: ActionCatalog,
    profile: np.ndarray,
    signal: SignalName,
    *,
    adjacency_restricted: bool,
) -> tuple[float, np.ndarray | None, dict[str, int | str]]:
    baseline = assignment_signal_potential(
        world, catalog, Assignment(profile), signal
    )
    best_gain = 0.0
    best: np.ndarray | None = None
    event: dict[str, int | str] = {}
    for robot in range(world.n_robots):
        candidate_actions = np.concatenate(
            [
                np.array([-1], dtype=int),
                catalog.actions_for_robot(robot, compatible_only=True),
            ]
        )
        for action in candidate_actions:
            if int(action) == int(profile[robot]):
                continue
            if action >= 0 and adjacency_restricted:
                load = int(catalog.load_index[action])
                members = [
                    other
                    for other, current in enumerate(profile)
                    if current >= 0 and int(catalog.load_index[current]) == load
                ]
                if members and not any(
                    world.communication_adjacency[robot, other] for other in members
                ):
                    continue
            proposal = profile.copy()
            proposal[robot] = int(action)
            if not _valid_unique(proposal, catalog):
                continue
            value = assignment_signal_potential(
                world, catalog, Assignment(proposal), signal
            )
            gain = value - baseline
            if gain > best_gain + 1e-12:
                best_gain = float(gain)
                best = proposal
                event = {"event": "grape_deviation", "robot": robot}
    return best_gain, best, event


def _best_pair_swap(
    world: GeoWorld,
    catalog: ActionCatalog,
    profile: np.ndarray,
    signal: SignalName,
) -> tuple[float, np.ndarray | None, dict[str, int | str]]:
    baseline = assignment_signal_potential(
        world, catalog, Assignment(profile), signal
    )
    best_gain = 0.0
    best: np.ndarray | None = None
    event: dict[str, int | str] = {}
    for left in range(world.n_robots):
        for right in np.flatnonzero(world.communication_adjacency[left]):
            right = int(right)
            if right <= left:
                continue
            left_action, right_action = int(profile[left]), int(profile[right])
            if left_action < 0 or right_action < 0:
                continue
            left_replacement = catalog.action_for(
                left,
                int(catalog.load_index[right_action]),
                int(catalog.slot_index[right_action]),
            )
            right_replacement = catalog.action_for(
                right,
                int(catalog.load_index[left_action]),
                int(catalog.slot_index[left_action]),
            )
            if (
                left_replacement is None
                or right_replacement is None
                or not catalog.compatible[left_replacement]
                or not catalog.compatible[right_replacement]
            ):
                continue
            proposal = profile.copy()
            proposal[left] = left_replacement
            proposal[right] = right_replacement
            if not _valid_unique(proposal, catalog):
                continue
            value = assignment_signal_potential(
                world, catalog, Assignment(proposal), signal
            )
            gain = value - baseline
            if gain > best_gain + 1e-12:
                best_gain = float(gain)
                best = proposal
                event = {
                    "event": "grape_pair_swap",
                    "left_robot": left,
                    "right_robot": right,
                }
    return best_gain, best, event


def allocate_grape(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    signal: SignalName,
    pair_swaps: bool = True,
    max_iterations: int = 200,
) -> AllocationResult:
    started = time.perf_counter()
    profile = _initial_profile(world, catalog, signal)
    events: list[dict[str, int | float | str]] = []
    iterations = 0
    for iteration in range(1, int(max_iterations) + 1):
        unilateral_gain, unilateral, unilateral_event = _best_unilateral(
            world,
            catalog,
            profile,
            signal,
            adjacency_restricted=True,
        )
        pair_gain, pair, pair_event = (
            _best_pair_swap(world, catalog, profile, signal)
            if pair_swaps
            else (0.0, None, {})
        )
        if unilateral is None and pair is None:
            break
        if pair is not None and pair_gain > unilateral_gain + 1e-12:
            profile = pair
            event = pair_event
            gain = pair_gain
        else:
            assert unilateral is not None
            profile = unilateral
            event = unilateral_event
            gain = unilateral_gain
        iterations = iteration
        events.append({**event, "iteration": iteration, "gain": gain})

    blocking_gain, _, _ = _best_unilateral(
        world,
        catalog,
        profile,
        signal,
        adjacency_restricted=True,
    )
    swap_gain, _, _ = _best_pair_swap(world, catalog, profile, signal)
    edges = int(np.sum(world.communication_adjacency) // 2)
    rounds = max(iterations, 1)
    messages = 2 * edges * rounds
    if signal == "scalar_capacity":
        method = "weighted_grape_scalar"
    elif pair_swaps:
        method = "pair_role_grape_s_physical"
    else:
        method = "role_grape_s_physical"
    return AllocationResult(
        method=method,
        engine="pair_grape" if pair_swaps else "role_grape",
        signal=signal,
        assignment=Assignment(profile),
        status="local_stable" if blocking_gain <= 1e-12 else "max_iterations",
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        iterations=iterations,
        rounds=rounds,
        messages=messages,
        bytes_sent=messages * 48,
        diagnostics={
            "information_scope": "neighbor_unilateral_and_pair_deviations",
            "blocking_unilateral_deviations": int(blocking_gain > 1e-12),
            "blocking_swaps": int(swap_gain > 1e-12),
            "local_core_distance": max(blocking_gain, swap_gain),
        },
        events=[dict(event) for event in events],
    )


__all__ = ["allocate_grape"]
