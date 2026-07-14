"""Metrics for SP1 recruitment and coalition experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.domain import WorldState


@dataclass(frozen=True, slots=True)
class SP1Metrics:
    """Flat SP1 metric bundle written to CSV and reports."""

    coalition_success_rate: float
    served_load_rate: float
    demand_satisfaction_ratio: float
    coalition_time: float
    robots_underassigned: int
    robots_overassigned: int
    assignment_cost: float
    travel_distance_m: float
    mean_assigned_travel_distance_m: float
    max_assigned_travel_distance_m: float
    estimated_arrival_time_s: float
    energy_proxy_wh: float
    priority_regret: float
    optimality_gap_vs_oracle: float
    strategy_switches: int
    communication_messages: int
    runtime_ms: float
    captured_reward: float
    oracle_reward: float
    assigned_robots: int
    idle_robots: int
    fully_served_load_fraction: float
    robot_demand_satisfaction_ratio: float
    unmet_quorum: int
    robots_in_incomplete_coalitions: int
    robots_overallocated: int
    regret_vs_coalition_oracle: float
    time_to_close_quorums_s: float
    messages_to_close_quorums: int
    timeout_rate: float
    failure_rate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_diagnostics(world: WorldState, assignment: Assignment) -> list[dict[str, Any]]:
    """Return per-load SP1 feasibility diagnostics."""

    labels = np.asarray(assignment.labels, dtype=int)
    payloads = np.asarray([robot.spec.capacity.payload_kg for robot in world.robots], dtype=float)
    rows = []
    for load_idx, load in enumerate(world.loads):
        assigned = np.flatnonzero(labels == load_idx + 1)
        assigned_capacity = float(np.sum(payloads[assigned]))
        required_capacity = float(load.min_capacity_kg)
        assigned_robots = int(assigned.size)
        required_robots = int(load.min_coalition_size)
        robot_deficit = max(required_robots - assigned_robots, 0)
        robot_surplus = max(assigned_robots - required_robots, 0)
        capacity_deficit = max(required_capacity - assigned_capacity, 0.0)
        status = "OK"
        if robot_deficit > 0 or capacity_deficit > 1e-9:
            status = "UNDER"
        elif robot_surplus > 0:
            status = "OVER"
        rows.append(
            {
                "load_id": load.identifier,
                "load_index": load_idx + 1,
                "required_robots": required_robots,
                "assigned_robots": assigned_robots,
                "robot_deficit": robot_deficit,
                "robot_surplus": robot_surplus,
                "mass_kg": float(load.mass_kg),
                "required_capacity_kg": required_capacity,
                "assigned_capacity_kg": assigned_capacity,
                "capacity_deficit_kg": capacity_deficit,
                "status": status,
                "reward": float(load.reward),
                "assigned_robot_ids": " ".join(world.robots[idx].identifier for idx in assigned),
            }
        )
    return rows


def evaluate_assignment(
    world: WorldState,
    assignment: Assignment,
    *,
    runtime_ms: float,
    oracle_assignment: Assignment | None = None,
    communication_radius: float = float("inf"),
    centralized: bool = False,
) -> SP1Metrics:
    """Compute SP1 one-shot recruitment metrics."""

    labels = np.asarray(assignment.labels, dtype=int)
    diagnostics = load_diagnostics(world, assignment)
    served = [row for row in diagnostics if row["status"] in {"OK", "OVER"}]
    demand_total = sum(row["required_robots"] for row in diagnostics)
    demand_met = sum(min(row["assigned_robots"], row["required_robots"]) for row in diagnostics)
    underassigned = int(sum(row["robot_deficit"] for row in diagnostics))
    overassigned = int(sum(row["robot_surplus"] for row in diagnostics))
    incomplete_labels = {int(row["load_index"]) for row in diagnostics if row["status"] == "UNDER"}
    robots_in_incomplete = int(sum(int(label) in incomplete_labels for label in labels if int(label) > 0))
    captured_reward = float(sum(row["reward"] for row in served))
    travel_stats = _assignment_travel_stats(world, assignment)
    assignment_cost = travel_stats["travel_distance_m"]

    oracle_reward = captured_reward
    oracle_cost = assignment_cost
    if oracle_assignment is not None:
        oracle_diagnostics = load_diagnostics(world, oracle_assignment)
        oracle_reward = float(sum(row["reward"] for row in oracle_diagnostics if row["status"] in {"OK", "OVER"}))
        oracle_cost = _assignment_distance(world, oracle_assignment)

    score = captured_reward - 0.05 * assignment_cost
    oracle_score = oracle_reward - 0.05 * oracle_cost
    if abs(oracle_score) < 1e-9:
        gap = 0.0
    else:
        gap = max(0.0, float((oracle_score - score) / abs(oracle_score)))

    return SP1Metrics(
        coalition_success_rate=float(len(served) / max(len(world.loads), 1)),
        served_load_rate=float(len(served) / max(len(world.loads), 1)),
        demand_satisfaction_ratio=float(demand_met / max(demand_total, 1)),
        coalition_time=1.0 if underassigned == 0 else float("nan"),
        robots_underassigned=underassigned,
        robots_overassigned=overassigned,
        assignment_cost=assignment_cost,
        travel_distance_m=travel_stats["travel_distance_m"],
        mean_assigned_travel_distance_m=travel_stats["mean_assigned_travel_distance_m"],
        max_assigned_travel_distance_m=travel_stats["max_assigned_travel_distance_m"],
        estimated_arrival_time_s=travel_stats["estimated_arrival_time_s"],
        energy_proxy_wh=travel_stats["energy_proxy_wh"],
        priority_regret=max(0.0, oracle_reward - captured_reward),
        optimality_gap_vs_oracle=gap,
        strategy_switches=0,
        communication_messages=_communication_messages(world, communication_radius, centralized),
        runtime_ms=float(runtime_ms),
        captured_reward=captured_reward,
        oracle_reward=oracle_reward,
        assigned_robots=int(np.sum(labels > 0)),
        idle_robots=int(np.sum(labels == 0)),
        fully_served_load_fraction=float(len(served) / max(len(world.loads), 1)),
        robot_demand_satisfaction_ratio=float(demand_met / max(demand_total, 1)),
        unmet_quorum=underassigned,
        robots_in_incomplete_coalitions=robots_in_incomplete,
        robots_overallocated=overassigned,
        regret_vs_coalition_oracle=max(0.0, oracle_reward - captured_reward),
        time_to_close_quorums_s=1.0 if underassigned == 0 else float("nan"),
        messages_to_close_quorums=_communication_messages(world, communication_radius, centralized),
        timeout_rate=0.0,
        failure_rate=float(not np.all((labels >= 0) & (labels <= len(world.loads)))),
    )


def _assignment_travel_stats(world: WorldState, assignment: Assignment) -> dict[str, float]:
    labels = np.asarray(assignment.labels, dtype=int)
    distances = []
    arrival_times = []
    energy_proxy = 0.0
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        robot = world.robots[robot_idx]
        load = world.loads[int(label) - 1]
        distance = float(np.linalg.norm(robot.position - load.pickup))
        speed = max(float(robot.spec.max_speed), 1.0e-9)
        distances.append(distance)
        arrival_times.append(distance / speed)
        energy_proxy += distance * float(robot.spec.battery.discharge_per_meter) * float(robot.spec.battery.capacity_wh)
    if not distances:
        return {
            "travel_distance_m": 0.0,
            "mean_assigned_travel_distance_m": 0.0,
            "max_assigned_travel_distance_m": 0.0,
            "estimated_arrival_time_s": 0.0,
            "energy_proxy_wh": 0.0,
        }
    distance_array = np.asarray(distances, dtype=float)
    return {
        "travel_distance_m": float(np.sum(distance_array)),
        "mean_assigned_travel_distance_m": float(np.mean(distance_array)),
        "max_assigned_travel_distance_m": float(np.max(distance_array)),
        "estimated_arrival_time_s": float(np.max(arrival_times)),
        "energy_proxy_wh": float(energy_proxy),
    }


def _assignment_distance(world: WorldState, assignment: Assignment) -> float:
    labels = np.asarray(assignment.labels, dtype=int)
    total = 0.0
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        total += float(np.linalg.norm(world.robots[robot_idx].position - world.loads[int(label) - 1].pickup))
    return total


def _communication_messages(world: WorldState, radius: float, centralized: bool) -> int:
    if centralized or not np.isfinite(radius):
        return len(world.robots) * len(world.loads)
    count = 0
    for robot in world.robots:
        for load in world.loads:
            if float(np.linalg.norm(robot.position - load.pickup)) <= radius:
                count += 1
    return count
