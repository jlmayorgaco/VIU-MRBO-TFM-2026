"""Minimal dynamic N4 pilot with exogenous events.

F-IV is modelled as a repeated atomic recruitment game driven by an exogenous
event state.  The module does not call it a Markov potential game.  It compares
two executable Geo-QPG policies with a finite-state perfect-foresight oracle on
small instances.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp1_n3.worlds import World
from viu_mrob_tfm.sp1_n4.geo_qpg import run_geo_qpg


@dataclass(frozen=True, slots=True)
class RecruitmentEvent:
    time: int
    name: str
    active_loads: tuple[int, ...]
    failed_robots: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class DynamicEpisodeResult:
    policy: str
    history: pd.DataFrame
    discounted_cost: float
    service_success_rate: float
    unmet_demand_steps: int
    coalition_switches: int
    messages: int
    bytes_sent: int
    atomic_feasible_rate: float


def canonical_event_schedule(world: World) -> tuple[RecruitmentEvent, ...]:
    """Return the same controlled arrival/failure/completion sequence per world."""

    if world.n_loads < 3:
        raise ValueError("the F-IV schedule requires at least three loads")
    failure_robot = int(
        np.lexsort((np.arange(world.n_robots), -world.capacities))[0]
    )
    return (
        RecruitmentEvent(0, "initial_job", (0,)),
        RecruitmentEvent(1, "job_1_arrival", (0, 1)),
        RecruitmentEvent(2, "robot_failure", (0, 1), (failure_robot,)),
        RecruitmentEvent(3, "job_0_completion", (1,), (failure_robot,)),
        RecruitmentEvent(4, "job_2_arrival", (1, 2), (failure_robot,)),
        RecruitmentEvent(5, "job_1_completion", (2,), (failure_robot,)),
    )


def snapshot_world(world: World, event: RecruitmentEvent) -> World:
    """Freeze one exogenous state while preserving robot and load identities."""

    capacities = world.capacities.copy()
    if event.failed_robots:
        capacities[np.asarray(event.failed_robots, dtype=int)] = 0.0
    demands = np.zeros_like(world.demands)
    active = np.asarray(event.active_loads, dtype=int)
    demands[active] = world.demands[active]
    return World(
        world_id=f"{world.world_id}:t{event.time}:{event.name}",
        seed=world.seed,
        scenario=world.scenario,
        capacity_cv=world.capacity_cv,
        pressure=world.pressure,
        robot_positions=world.robot_positions.copy(),
        load_positions=world.load_positions.copy(),
        capacities=capacities,
        demands=demands,
        distances=world.distances.copy(),
    )


def assignment_stage_metrics(
    world: World,
    event: RecruitmentEvent,
    assignment: np.ndarray,
    previous: np.ndarray,
    *,
    deficit_weight: float,
    distance_weight: float,
    switch_weight: float,
) -> dict[str, float | int | bool]:
    """Evaluate one atomic decision under a declared dynamic stage cost."""

    snapshot = snapshot_world(world, event)
    assignment = np.asarray(assignment, dtype=int)
    previous = np.asarray(previous, dtype=int)
    coverage = np.zeros(world.n_loads, dtype=float)
    distance = 0.0
    for robot, load in enumerate(assignment):
        if load >= 0:
            coverage[load] += snapshot.capacities[robot]
            distance += snapshot.distances[robot, load]
    active = np.asarray(event.active_loads, dtype=int)
    active_demands = snapshot.demands[active]
    active_deficit = np.maximum(active_demands - coverage[active], 0.0)
    normalized_deficit = float(
        np.sum(active_deficit / np.maximum(active_demands, 1e-12))
    )
    distance_scale = max(float(np.max(world.distances)), 1e-12)
    normalized_distance = float(distance / (world.n_robots * distance_scale))
    switches = int(np.sum(assignment != previous))
    normalized_switches = switches / world.n_robots
    cost = (
        deficit_weight * normalized_deficit
        + distance_weight * normalized_distance
        + switch_weight * normalized_switches
    )
    return {
        "stage_cost": float(cost),
        "deficit": float(np.sum(active_deficit)),
        "normalized_deficit": normalized_deficit,
        "distance": float(distance),
        "switches": switches,
        "feasible": bool(np.all(active_deficit <= 1e-8)),
    }


def run_event_triggered_policy(
    world: World,
    adjacency: np.ndarray,
    events: Iterable[RecruitmentEvent],
    *,
    policy: str,
    gamma: float = 0.95,
    deficit_weight: float = 20.0,
    distance_weight: float = 1.0,
    switch_weight: float = 0.75,
    max_rounds: int = 2_048,
) -> DynamicEpisodeResult:
    """Run cold myopic or event-triggered warm-start Geo-QPG."""

    if policy not in {"myopic_cold", "event_triggered_warm"}:
        raise KeyError(f"unknown F-IV policy: {policy}")
    if not 0.0 < gamma <= 1.0:
        raise ValueError("gamma must belong to (0,1]")
    previous = np.full(world.n_robots, -1, dtype=int)
    rows: list[dict[str, float | int | str | bool]] = []
    total_messages = 0
    total_bytes = 0
    discounted = 0.0
    for event in events:
        snapshot = snapshot_world(world, event)
        initial = previous if policy == "event_triggered_warm" else None
        result = run_geo_qpg(
            snapshot,
            adjacency,
            "geo_qpg_d",
            max_rounds=max_rounds,
            initial_assignment=initial,
        )
        metrics = assignment_stage_metrics(
            world,
            event,
            result.assignment,
            previous,
            deficit_weight=deficit_weight,
            distance_weight=distance_weight,
            switch_weight=switch_weight,
        )
        discounted += gamma**event.time * float(metrics["stage_cost"])
        total_messages += result.messages
        total_bytes += result.bytes_sent
        rows.append(
            {
                "time": event.time,
                "event": event.name,
                "active_loads": ";".join(map(str, event.active_loads)),
                "failed_robots": ";".join(map(str, event.failed_robots)),
                "assignment": ";".join(map(str, result.assignment.tolist())),
                "rounds": result.rounds,
                "messages": result.messages,
                "bytes": result.bytes_sent,
                **metrics,
            }
        )
        previous = result.assignment.copy()
    history = pd.DataFrame(rows)
    return DynamicEpisodeResult(
        policy=policy,
        history=history,
        discounted_cost=float(discounted),
        service_success_rate=float(history["feasible"].mean()),
        unmet_demand_steps=int((~history["feasible"].astype(bool)).sum()),
        coalition_switches=int(history["switches"].sum()),
        messages=int(total_messages),
        bytes_sent=int(total_bytes),
        atomic_feasible_rate=float(history["feasible"].mean()),
    )


def _all_assignments(n_robots: int, n_loads: int) -> np.ndarray:
    return np.asarray(
        list(itertools.product(range(-1, n_loads), repeat=n_robots)),
        dtype=np.int16,
    )


def run_perfect_foresight_oracle(
    world: World,
    events: Iterable[RecruitmentEvent],
    *,
    gamma: float = 0.95,
    deficit_weight: float = 20.0,
    distance_weight: float = 1.0,
    switch_weight: float = 0.75,
    max_states: int = 20_000,
) -> DynamicEpisodeResult:
    """Exact finite-horizon dynamic-programming oracle for small N4 worlds."""

    sequence = tuple(events)
    states = _all_assignments(world.n_robots, world.n_loads)
    if len(states) > max_states:
        raise ValueError(
            f"dynamic oracle requires {len(states)} states, above {max_states}"
        )
    idle = np.full(world.n_robots, -1, dtype=int)
    idle_index = int(np.flatnonzero(np.all(states == idle[None, :], axis=1))[0])
    hamming = np.mean(states[:, None, :] != states[None, :, :], axis=2)
    base_costs: list[np.ndarray] = []
    for event in sequence:
        metrics = [
            assignment_stage_metrics(
                world,
                event,
                state,
                idle,
                deficit_weight=deficit_weight,
                distance_weight=distance_weight,
                switch_weight=0.0,
            )
            for state in states
        ]
        base_costs.append(
            np.asarray([float(item["stage_cost"]) for item in metrics], dtype=float)
        )

    value_next = np.zeros(len(states), dtype=float)
    policies: list[np.ndarray] = []
    for event, base in reversed(list(zip(sequence, base_costs, strict=True))):
        total = (
            base[None, :]
            + switch_weight * hamming
            + gamma * value_next[None, :]
        )
        policy = np.argmin(total, axis=1)
        value_next = np.min(total, axis=1)
        policies.append(policy)
    policies.reverse()

    previous_index = idle_index
    rows: list[dict[str, float | int | str | bool]] = []
    discounted = 0.0
    for step, event in enumerate(sequence):
        action_index = int(policies[step][previous_index])
        assignment = states[action_index].astype(int)
        previous = states[previous_index].astype(int)
        metrics = assignment_stage_metrics(
            world,
            event,
            assignment,
            previous,
            deficit_weight=deficit_weight,
            distance_weight=distance_weight,
            switch_weight=switch_weight,
        )
        discounted += gamma**event.time * float(metrics["stage_cost"])
        rows.append(
            {
                "time": event.time,
                "event": event.name,
                "active_loads": ";".join(map(str, event.active_loads)),
                "failed_robots": ";".join(map(str, event.failed_robots)),
                "assignment": ";".join(map(str, assignment.tolist())),
                "rounds": 0,
                "messages": 0,
                "bytes": 0,
                **metrics,
            }
        )
        previous_index = action_index
    history = pd.DataFrame(rows)
    return DynamicEpisodeResult(
        policy="perfect_foresight_dp",
        history=history,
        discounted_cost=float(discounted),
        service_success_rate=float(history["feasible"].mean()),
        unmet_demand_steps=int((~history["feasible"].astype(bool)).sum()),
        coalition_switches=int(history["switches"].sum()),
        messages=0,
        bytes_sent=0,
        atomic_feasible_rate=float(history["feasible"].mean()),
    )


__all__ = [
    "DynamicEpisodeResult",
    "RecruitmentEvent",
    "assignment_stage_metrics",
    "canonical_event_schedule",
    "run_event_triggered_policy",
    "run_perfect_foresight_oracle",
    "snapshot_world",
]
