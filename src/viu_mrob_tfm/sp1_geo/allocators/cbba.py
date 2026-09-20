"""Capacity-CBBA adaptation with local max-consensus over slot bids."""

from __future__ import annotations

import time

import numpy as np

from ..contributions import aggregate_signal
from ..models import ActionCatalog, AllocationResult, Assignment, GeoWorld, SignalName
from ..welfare import marginal_payoffs


def _graph_diameter(adjacency: np.ndarray) -> int:
    n = len(adjacency)
    maximum = 0
    for source in range(n):
        distances = np.full(n, -1, dtype=int)
        distances[source] = 0
        queue = [source]
        while queue:
            node = queue.pop(0)
            for neighbor in np.flatnonzero(adjacency[node]):
                if distances[neighbor] < 0:
                    distances[neighbor] = distances[node] + 1
                    queue.append(int(neighbor))
        if np.any(distances < 0):
            return n
        maximum = max(maximum, int(np.max(distances)))
    return maximum


def allocate_capacity_cbba(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    signal: SignalName,
    max_bundle_rounds: int | None = None,
) -> AllocationResult:
    """Multi-winner CBBA-style adaptation; it is not canonical one-winner CBBA."""

    started = time.perf_counter()
    assignment = np.full(world.n_robots, -1, dtype=int)
    occupied: set[tuple[int, int]] = set()
    zero = np.zeros(catalog.n_actions, dtype=float)
    base_bids = marginal_payoffs(world, catalog, zero, signal)
    diameter = max(_graph_diameter(world.communication_adjacency), 1)
    bundle_limit = max_bundle_rounds or world.n_robots
    conflicts_removed = 0
    winner_changes = 0
    consensus_rounds = 0
    edges = int(np.sum(world.communication_adjacency) // 2)
    events: list[dict[str, int | float | str]] = []

    for bundle_round in range(1, int(bundle_limit) + 1):
        current_x = np.zeros(catalog.n_actions, dtype=float)
        selected = assignment[assignment >= 0]
        current_x[selected] = 1.0
        service = aggregate_signal(catalog, current_x, signal, world.n_loads)
        demands = catalog.demands(signal)
        closed_loads = np.all(service >= demands - 1e-12, axis=1)

        # Each free robot submits one locally computed bid.
        proposals: list[tuple[int, float, int, int]] = []
        for robot in np.flatnonzero(assignment < 0):
            actions = catalog.actions_for_robot(int(robot), compatible_only=True)
            candidates = [
                int(action)
                for action in actions
                if (
                    int(catalog.load_index[action]),
                    int(catalog.slot_index[action]),
                )
                not in occupied
                and not closed_loads[int(catalog.load_index[action])]
                and base_bids[action] > 0.0
            ]
            if not candidates:
                continue
            candidates.sort(
                key=lambda action: (
                    -float(base_bids[action]),
                    float(catalog.costs[action]),
                    int(catalog.load_index[action]),
                    int(catalog.slot_index[action]),
                )
            )
            action = candidates[0]
            global_slot = sum(
                len(world.loads[index].slots)
                for index in range(int(catalog.load_index[action]))
            ) + int(catalog.slot_index[action])
            proposals.append(
                (global_slot, float(base_bids[action]), int(robot), action)
            )
        if not proposals:
            break

        # Simulate diameter rounds of max-consensus. The deterministic final
        # lexicographic maximum is the value every node obtains on a connected
        # graph; resource counts record the actual neighbor exchanges.
        winners: dict[int, tuple[float, int, int]] = {}
        for slot, bid, robot, action in proposals:
            candidate = (bid, -robot, action)
            if slot in winners:
                conflicts_removed += 1
            if slot not in winners or candidate > winners[slot]:
                winners[slot] = candidate
        consensus_rounds += diameter
        accepted = 0
        for slot, (bid, negative_robot, action) in sorted(winners.items()):
            robot = -negative_robot
            if assignment[robot] >= 0:
                continue
            key = (int(catalog.load_index[action]), int(catalog.slot_index[action]))
            if key in occupied:
                conflicts_removed += 1
                continue
            assignment[robot] = action
            occupied.add(key)
            winner_changes += 1
            accepted += 1
            events.append(
                {
                    "event": "cbba_winner",
                    "bundle_round": bundle_round,
                    "slot": slot,
                    "robot": robot,
                    "action": action,
                    "bid": bid,
                }
            )
        if accepted == 0:
            break

    messages = 2 * edges * consensus_rounds
    bytes_sent = messages * 40
    name = (
        "physical_cbba_marginal"
        if signal == "marginal_physical"
        else "capacity_cbba_scalar"
    )
    return AllocationResult(
        method=name,
        engine="capacity_cbba",
        signal=signal,
        assignment=Assignment(assignment),
        status="success",
        runtime_negotiation_ms=1_000.0 * (time.perf_counter() - started),
        iterations=winner_changes,
        rounds=consensus_rounds,
        messages=messages,
        bytes_sent=bytes_sent,
        diagnostics={
            "information_scope": "neighbor_max_consensus",
            "cbba_conflicts_removed": conflicts_removed,
            "cbba_winner_changes": winner_changes,
            "consensus_diameter": diameter,
        },
        events=[dict(event) for event in events],
    )


__all__ = ["allocate_capacity_cbba"]
