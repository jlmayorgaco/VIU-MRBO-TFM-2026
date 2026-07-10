"""Metrics for SP2 effective-capacity experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.allocation import Assignment, DecisionContext
from viu_mrob_tfm.domain import WorldState
from viu_mrob_tfm.sp2.methods import communication_visibility_matrix, effective_capacity_matrix, energy_matrix, load_capacity_demands


@dataclass(frozen=True, slots=True)
class SP2Metrics:
    capacity_success_rate: float
    served_load_rate: float
    capacity_satisfaction_ratio: float
    demand_satisfaction_ratio: float
    coalition_success_rate: float
    under_capacity_kg: float
    over_capacity_kg: float
    capacity_waste_ratio: float
    mean_capacity_margin_kg: float
    nominal_payload_assigned_kg: float
    effective_capacity_assigned_kg: float
    incomplete_capacity_kg: float
    incomplete_capacity_ratio: float
    served_capacity_alignment: float
    robots_underassigned: int
    robots_overassigned: int
    assignment_cost: float
    travel_distance_m: float
    mean_assigned_travel_distance_m: float
    max_assigned_travel_distance_m: float
    estimated_arrival_time_s: float
    energy_proxy_wh: float
    score_value: float
    oracle_score_value: float
    signed_score_delta_vs_oracle: float
    oracle_dominance_violation: bool
    optimality_gap_vs_oracle: float
    capacity_oracle_satisfaction_ratio: float
    capacity_oracle_success_rate: float
    effective_feasibility_ratio: float
    capacity_gap_vs_capacity_oracle: float
    signed_capacity_delta_vs_capacity_oracle: float
    priority_regret: float
    strategy_switches: int
    communication_messages: int
    communication_coverage_ratio: float
    runtime_ms: float
    captured_reward: float
    oracle_reward: float
    assigned_robots: int
    idle_robots: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_diagnostics(world: WorldState, assignment: Assignment, *, communication_radius: float = float("inf"), distance_decay_m: float = 22.0) -> list[dict[str, Any]]:
    context = DecisionContext(world=world, metadata={"communication_radius": communication_radius, "distance_decay_m": distance_decay_m})
    labels = np.asarray(assignment.labels, dtype=int)
    eff = effective_capacity_matrix(context)
    visibility = communication_visibility_matrix(context)
    demands = load_capacity_demands(context)
    payloads = np.asarray([robot.spec.capacity.payload_kg for robot in world.robots], dtype=float)
    rows = []
    for load_idx, load in enumerate(world.loads):
        assigned = np.flatnonzero(labels == load_idx + 1)
        nominal = float(np.sum(payloads[assigned]))
        effective = float(np.sum(eff[assigned, load_idx])) if assigned.size else 0.0
        visible_assigned = int(np.sum(visibility[assigned, load_idx] > 0.5)) if assigned.size else 0
        required = float(demands[load_idx])
        deficit = max(required - effective, 0.0)
        surplus = max(effective - required, 0.0)
        assigned_robots = int(assigned.size)
        required_robots = int(load.min_coalition_size)
        robot_deficit = max(required_robots - assigned_robots, 0)
        robot_surplus = max(assigned_robots - required_robots, 0)
        status = "OK" if deficit <= 1e-9 and assigned_robots >= required_robots else "UNDER"
        if status == "OK" and surplus > 0.2 * required:
            status = "OVER"
        rows.append(
            {
                "load_id": load.identifier,
                "load_index": load_idx + 1,
                "mass_kg": float(load.mass_kg),
                "length_m": float(load.length_m),
                "width_m": float(load.width_m),
                "required_robots": required_robots,
                "assigned_robots": assigned_robots,
                "robot_deficit": robot_deficit,
                "robot_surplus": robot_surplus,
                "required_capacity_kg": required,
                "assigned_nominal_capacity_kg": nominal,
                "assigned_effective_capacity_kg": effective,
                "assigned_visible_robots": visible_assigned,
                "assigned_out_of_radius_robots": int(max(assigned_robots - visible_assigned, 0)),
                "capacity_deficit_kg": deficit,
                "capacity_surplus_kg": surplus,
                "capacity_margin_kg": effective - required,
                "capacity_satisfaction_ratio": min(effective, required) / max(required, 1e-9),
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
    capacity_oracle_assignment: Assignment | None = None,
    communication_radius: float = float("inf"),
    distance_decay_m: float = 22.0,
    centralized: bool = False,
) -> SP2Metrics:
    labels = np.asarray(assignment.labels, dtype=int)
    diagnostics = load_diagnostics(
        world,
        assignment,
        communication_radius=communication_radius,
        distance_decay_m=distance_decay_m,
    )
    served = [row for row in diagnostics if row["status"] in {"OK", "OVER"}]
    required_total = float(sum(row["required_capacity_kg"] for row in diagnostics))
    satisfied_total = float(sum(min(row["assigned_effective_capacity_kg"], row["required_capacity_kg"]) for row in diagnostics))
    under_capacity = float(sum(row["capacity_deficit_kg"] for row in diagnostics))
    over_capacity = float(sum(row["capacity_surplus_kg"] for row in diagnostics))
    effective_total = float(sum(row["assigned_effective_capacity_kg"] for row in diagnostics))
    nominal_total = float(sum(row["assigned_nominal_capacity_kg"] for row in diagnostics))
    incomplete_capacity = float(sum(row["assigned_effective_capacity_kg"] for row in diagnostics if row["status"] not in {"OK", "OVER"}))
    completed_satisfied_capacity = float(sum(min(row["assigned_effective_capacity_kg"], row["required_capacity_kg"]) for row in served))
    robot_underassigned = int(sum(row["robot_deficit"] for row in diagnostics))
    robot_overassigned = int(sum(row["robot_surplus"] for row in diagnostics))
    captured_reward = float(sum(row["reward"] for row in served))
    travel_stats = _assignment_travel_stats(world, assignment)
    assignment_cost = travel_stats["travel_distance_m"]

    oracle_reward = captured_reward
    oracle_score = _capacity_score(world, assignment, communication_radius, distance_decay_m)
    capacity_oracle_satisfaction = float(satisfied_total / max(required_total, 1e-9))
    capacity_oracle_success = float(len(served) / max(len(world.loads), 1))
    if oracle_assignment is not None:
        oracle_diag = load_diagnostics(world, oracle_assignment, communication_radius=communication_radius, distance_decay_m=distance_decay_m)
        oracle_reward = float(sum(row["reward"] for row in oracle_diag if row["status"] in {"OK", "OVER"}))
        oracle_score = _capacity_score(world, oracle_assignment, communication_radius, distance_decay_m)
    if capacity_oracle_assignment is not None:
        capacity_oracle_diag = load_diagnostics(world, capacity_oracle_assignment, communication_radius=communication_radius, distance_decay_m=distance_decay_m)
        capacity_oracle_satisfaction = _satisfaction_ratio(capacity_oracle_diag)
        capacity_oracle_success = _success_rate(capacity_oracle_diag, world)
    score = _capacity_score(world, assignment, communication_radius, distance_decay_m)
    signed_score_delta = float(score - oracle_score)
    dominance_tolerance = max(1e-6, 1e-4 * abs(oracle_score))
    gap = 0.0 if abs(oracle_score) < 1e-9 else max(0.0, float((oracle_score - score) / abs(oracle_score)))
    signed_capacity_delta = float((satisfied_total / max(required_total, 1e-9)) - capacity_oracle_satisfaction)
    capacity_gap = 0.0 if abs(capacity_oracle_satisfaction) < 1e-9 else max(0.0, float((capacity_oracle_satisfaction - satisfied_total / max(required_total, 1e-9)) / abs(capacity_oracle_satisfaction)))
    communication_coverage = _communication_coverage_ratio(world, assignment, communication_radius)

    return SP2Metrics(
        capacity_success_rate=float(len(served) / max(len(world.loads), 1)),
        served_load_rate=float(len(served) / max(len(world.loads), 1)),
        capacity_satisfaction_ratio=float(satisfied_total / max(required_total, 1e-9)),
        demand_satisfaction_ratio=float(satisfied_total / max(required_total, 1e-9)),
        coalition_success_rate=float(len(served) / max(len(world.loads), 1)),
        under_capacity_kg=under_capacity,
        over_capacity_kg=over_capacity,
        capacity_waste_ratio=float(over_capacity / max(effective_total, 1e-9)),
        mean_capacity_margin_kg=float(np.mean([row["capacity_margin_kg"] for row in diagnostics])) if diagnostics else 0.0,
        nominal_payload_assigned_kg=nominal_total,
        effective_capacity_assigned_kg=effective_total,
        incomplete_capacity_kg=incomplete_capacity,
        incomplete_capacity_ratio=float(incomplete_capacity / max(effective_total, 1e-9)),
        served_capacity_alignment=float(completed_satisfied_capacity / max(satisfied_total, 1e-9)),
        robots_underassigned=robot_underassigned,
        robots_overassigned=robot_overassigned,
        assignment_cost=assignment_cost,
        travel_distance_m=travel_stats["travel_distance_m"],
        mean_assigned_travel_distance_m=travel_stats["mean_assigned_travel_distance_m"],
        max_assigned_travel_distance_m=travel_stats["max_assigned_travel_distance_m"],
        estimated_arrival_time_s=travel_stats["estimated_arrival_time_s"],
        energy_proxy_wh=travel_stats["energy_proxy_wh"],
        score_value=score,
        oracle_score_value=oracle_score,
        signed_score_delta_vs_oracle=signed_score_delta,
        oracle_dominance_violation=bool(signed_score_delta > dominance_tolerance),
        optimality_gap_vs_oracle=gap,
        capacity_oracle_satisfaction_ratio=capacity_oracle_satisfaction,
        capacity_oracle_success_rate=capacity_oracle_success,
        effective_feasibility_ratio=capacity_oracle_satisfaction,
        capacity_gap_vs_capacity_oracle=capacity_gap,
        signed_capacity_delta_vs_capacity_oracle=signed_capacity_delta,
        priority_regret=max(0.0, oracle_reward - captured_reward),
        strategy_switches=0,
        communication_messages=_communication_messages(world, communication_radius, centralized),
        communication_coverage_ratio=communication_coverage,
        runtime_ms=float(runtime_ms),
        captured_reward=captured_reward,
        oracle_reward=oracle_reward,
        assigned_robots=int(np.sum(labels > 0)),
        idle_robots=int(np.sum(labels == 0)),
    )


def _capacity_score(world: WorldState, assignment: Assignment, communication_radius: float, distance_decay_m: float) -> float:
    diagnostics = load_diagnostics(world, assignment, communication_radius=communication_radius, distance_decay_m=distance_decay_m)
    capacity_term = sum(row["capacity_satisfaction_ratio"] for row in diagnostics)
    reward_term = sum(row["reward"] for row in diagnostics if row["status"] in {"OK", "OVER"})
    under_penalty = 0.001 * sum(row["capacity_deficit_kg"] for row in diagnostics)
    over_penalty = 0.0005 * sum(row["capacity_surplus_kg"] for row in diagnostics)
    travel_stats = _assignment_travel_stats(world, assignment)
    travel_penalty = 0.0005 * travel_stats["travel_distance_m"]
    energy_penalty = 0.00001 * travel_stats["energy_proxy_wh"]
    return float(100.0 * capacity_term + 5.0 * reward_term - under_penalty - over_penalty - travel_penalty - energy_penalty)


def _satisfaction_ratio(diagnostics: list[dict[str, Any]]) -> float:
    required_total = float(sum(row["required_capacity_kg"] for row in diagnostics))
    satisfied_total = float(sum(min(row["assigned_effective_capacity_kg"], row["required_capacity_kg"]) for row in diagnostics))
    return float(satisfied_total / max(required_total, 1e-9))


def _success_rate(diagnostics: list[dict[str, Any]], world: WorldState) -> float:
    served = [row for row in diagnostics if row["status"] in {"OK", "OVER"}]
    return float(len(served) / max(len(world.loads), 1))


def _assignment_travel_stats(world: WorldState, assignment: Assignment) -> dict[str, float]:
    labels = np.asarray(assignment.labels, dtype=int)
    distances = []
    arrivals = []
    energy = 0.0
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        robot = world.robots[robot_idx]
        load = world.loads[int(label) - 1]
        distance = float(np.linalg.norm(robot.position - load.pickup))
        distances.append(distance)
        arrivals.append(distance / max(float(robot.spec.max_speed), 1e-9))
        energy += distance * float(robot.spec.battery.discharge_per_meter) * float(robot.spec.battery.capacity_wh)
    if not distances:
        return {
            "travel_distance_m": 0.0,
            "mean_assigned_travel_distance_m": 0.0,
            "max_assigned_travel_distance_m": 0.0,
            "estimated_arrival_time_s": 0.0,
            "energy_proxy_wh": 0.0,
        }
    values = np.asarray(distances, dtype=float)
    return {
        "travel_distance_m": float(np.sum(values)),
        "mean_assigned_travel_distance_m": float(np.mean(values)),
        "max_assigned_travel_distance_m": float(np.max(values)),
        "estimated_arrival_time_s": float(np.max(arrivals)),
        "energy_proxy_wh": float(energy),
    }


def _communication_messages(world: WorldState, radius: float, centralized: bool) -> int:
    if centralized or not np.isfinite(radius):
        return len(world.robots) * len(world.loads)
    count = 0
    for robot in world.robots:
        for load in world.loads:
            if float(np.linalg.norm(robot.position - load.pickup)) <= radius:
                count += 1
    return count


def _communication_coverage_ratio(world: WorldState, assignment: Assignment, radius: float) -> float:
    labels = np.asarray(assignment.labels, dtype=int)
    assigned = np.flatnonzero(labels > 0)
    if assigned.size == 0 or not np.isfinite(radius):
        return 1.0
    visible = 0
    for robot_idx in assigned:
        robot = world.robots[int(robot_idx)]
        load = world.loads[int(labels[int(robot_idx)]) - 1]
        if float(np.linalg.norm(robot.position - load.pickup)) <= radius:
            visible += 1
    return float(visible / max(int(assigned.size), 1))
