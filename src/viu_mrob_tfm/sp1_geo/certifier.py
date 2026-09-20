"""Common physical certifier for every integer allocator output."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import lsq_linear

from .models import (
    ActionCatalog,
    Assignment,
    GeoWorld,
    LoadCertificate,
    WorldCertificate,
)


def bounded_wrench_residual(
    columns_per_n: np.ndarray,
    force_upper_n: np.ndarray,
    demand: np.ndarray,
) -> tuple[float, float, np.ndarray]:
    """Solve bounded convex least squares and return SI/normalized residuals.

    The Euclidean residual requested by the protocol is a bounded
    least-squares problem, not a linear program. The implementation and report
    use the mathematically correct solver class.
    """

    matrix = np.asarray(columns_per_n, dtype=float).T
    upper = np.asarray(force_upper_n, dtype=float)
    target = np.asarray(demand, dtype=float)
    if matrix.shape[0] != 3 or matrix.shape[1] != len(upper):
        raise ValueError("The wrench matrix or force bounds have invalid dimensions.")
    if matrix.shape[1] == 0:
        residual_si = float(np.linalg.norm(target))
        return residual_si, residual_si / max(float(np.linalg.norm(target)), 1.0), np.zeros(0)
    if np.any(upper < 0.0) or not np.isfinite(matrix).all() or not np.isfinite(upper).all():
        raise ValueError("Wrench columns and force bounds must be finite and nonnegative.")
    result = lsq_linear(
        matrix,
        target,
        bounds=(np.zeros_like(upper), upper),
        method="trf",
        tol=1e-12,
        lsmr_tol=1e-12,
        max_iter=2_000,
    )
    efforts = np.asarray(result.x, dtype=float)
    residual_si = float(np.linalg.norm(matrix @ efforts - target))
    residual = residual_si / max(float(np.linalg.norm(target)), 1.0)
    return residual_si, residual, efforts


def certify_assignment(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
) -> WorldCertificate:
    """Apply exclusivity, energy, slot, quota, and wrench checks."""

    if assignment.action_by_robot.shape != (world.n_robots,):
        raise ValueError("Assignment size does not match the world.")
    invalid_action_count = 0
    selected_by_load: list[list[int]] = [[] for _ in range(world.n_loads)]
    seen_actions: set[int] = set()
    for robot, action in enumerate(assignment.action_by_robot):
        if action < 0:
            continue
        if action >= catalog.n_actions:
            invalid_action_count += 1
            continue
        if int(catalog.robot_index[action]) != robot:
            invalid_action_count += 1
            continue
        if action in seen_actions:
            invalid_action_count += 1
            continue
        seen_actions.add(int(action))
        selected_by_load[int(catalog.load_index[action])].append(int(action))

    duplicate_slots = 0
    load_certificates: list[LoadCertificate] = []
    for load_index, actions_list in enumerate(selected_by_load):
        load = world.loads[load_index]
        actions = np.asarray(actions_list, dtype=int)
        committed = actions.size > 0
        reasons: list[str] = []
        if not committed:
            load_certificates.append(
                LoadCertificate(
                    load_index=load_index,
                    committed=False,
                    feasible=False,
                    reasons=(),
                    capacity_kg=0.0,
                    capacity_lower_margin_kg=-load.min_capacity_kg,
                    capacity_upper_margin_kg=load.max_capacity_kg,
                    battery_minimum_margin_wh=math.nan,
                    wrench_residual=math.nan,
                    wrench_residual_si=math.nan,
                    wrench_margin=math.nan,
                    slot_coverage=0.0,
                    positive_negative_torque_coverage=False,
                    selected_robots=(),
                    selected_slots=(),
                )
            )
            continue

        robots = catalog.robot_index[actions].astype(int)
        slots = catalog.slot_index[actions].astype(int)
        unique_slots = len(set(slots.tolist()))
        duplicates = int(len(slots) - unique_slots)
        duplicate_slots += duplicates
        if duplicates:
            reasons.append("duplicate_slot")
        if np.any(~catalog.compatible[actions]):
            reasons.append("incompatible_action")
        if len(set(robots.tolist())) != len(robots):
            reasons.append("duplicate_robot")

        capacity = float(np.sum(catalog.physical_contributions[actions, 0]))
        lower_margin = capacity - load.min_capacity_kg
        upper_margin = load.max_capacity_kg - capacity
        if lower_margin < -1e-9:
            reasons.append("capacity_below_lower")
        if upper_margin < -1e-9:
            reasons.append("capacity_above_upper")
        if len(robots) < load.min_coalition_size:
            reasons.append("coalition_below_minimum")

        battery_margins = np.array(
            [
                world.robots[int(robot)].battery_wh
                - world.robots[int(robot)].safe_battery_wh
                - catalog.mission_energy_wh[int(action)]
                for robot, action in zip(robots, actions, strict=True)
            ],
            dtype=float,
        )
        minimum_battery_margin = float(np.min(battery_margins))
        if minimum_battery_margin < -1e-9:
            reasons.append("battery_return_unsafe")

        residual_si, residual, _ = bounded_wrench_residual(
            catalog.wrench_columns_per_n[actions],
            catalog.force_upper_n[actions],
            load.required_wrench,
        )
        wrench_margin = float(load.wrench_tolerance - residual)
        if residual > load.wrench_tolerance + 1e-12:
            reasons.append("wrench_residual")

        torque_columns = catalog.wrench_columns_per_n[actions, 2]
        if load.required_wrench[2] > 1e-12:
            torque_coverage = bool(np.any(torque_columns > 1e-12))
        elif load.required_wrench[2] < -1e-12:
            torque_coverage = bool(np.any(torque_columns < -1e-12))
        else:
            torque_coverage = True
        if not torque_coverage:
            reasons.append("torque_direction_missing")

        load_certificates.append(
            LoadCertificate(
                load_index=load_index,
                committed=True,
                feasible=len(reasons) == 0,
                reasons=tuple(sorted(set(reasons))),
                capacity_kg=capacity,
                capacity_lower_margin_kg=lower_margin,
                capacity_upper_margin_kg=upper_margin,
                battery_minimum_margin_wh=minimum_battery_margin,
                wrench_residual=residual,
                wrench_residual_si=residual_si,
                wrench_margin=wrench_margin,
                slot_coverage=unique_slots / max(len(load.slots), 1),
                positive_negative_torque_coverage=torque_coverage,
                selected_robots=tuple(int(value) for value in robots),
                selected_slots=tuple(int(value) for value in slots),
            )
        )

    committed = sum(int(item.committed) for item in load_certificates)
    served = sum(int(item.feasible) for item in load_certificates)
    assignment_valid = invalid_action_count == 0 and duplicate_slots == 0
    return WorldCertificate(
        load_certificates=tuple(load_certificates),
        duplicate_slots=duplicate_slots,
        incompatible_actions=invalid_action_count,
        assignment_valid=assignment_valid,
        committed_loads=committed,
        served_loads=served,
    )


def filter_certified_assignment(
    assignment: Assignment,
    catalog: ActionCatalog,
    certificate: WorldCertificate,
) -> Assignment:
    """Keep only complete loads that pass the common physical certificate."""

    valid_loads = {
        item.load_index for item in certificate.load_certificates if item.feasible
    }
    filtered = assignment.action_by_robot.copy()
    for robot, action in enumerate(filtered):
        if action < 0:
            continue
        if action >= catalog.n_actions or int(catalog.load_index[action]) not in valid_loads:
            filtered[robot] = -1
    return Assignment(filtered)


def physical_welfare(
    world: GeoWorld,
    catalog: ActionCatalog,
    assignment: Assignment,
    certificate: WorldCertificate | None = None,
) -> float:
    """Common physical endpoint: certified value minus committed action costs."""

    audit = certificate or certify_assignment(world, catalog, assignment)
    value = sum(
        world.loads[item.load_index].priority_value
        for item in audit.load_certificates
        if item.feasible
    )
    selected = assignment.selected_actions()
    cost = float(np.sum(catalog.costs[selected])) if selected.size else 0.0
    return float(value - cost)


def certificate_records(
    world: GeoWorld,
    certificate: WorldCertificate,
) -> list[dict[str, Any]]:
    records = []
    for item in certificate.load_certificates:
        records.append(
            {
                "load_index": item.load_index,
                "load_id": world.loads[item.load_index].identifier,
                "committed": item.committed,
                "physical_feasible": item.feasible,
                "failure_reasons": "|".join(item.reasons) if item.reasons else "none",
                "capacity_kg": item.capacity_kg,
                "capacity_lower_margin_kg": item.capacity_lower_margin_kg,
                "capacity_upper_margin_kg": item.capacity_upper_margin_kg,
                "battery_minimum_margin_wh": item.battery_minimum_margin_wh,
                "wrench_residual": item.wrench_residual,
                "wrench_residual_si": item.wrench_residual_si,
                "wrench_margin": item.wrench_margin,
                "slot_coverage": item.slot_coverage,
                "positive_negative_torque_coverage": item.positive_negative_torque_coverage,
                "selected_robots": jsonable_tuple(item.selected_robots),
                "selected_slots": jsonable_tuple(item.selected_slots),
            }
        )
    return records


def jsonable_tuple(values: tuple[int, ...]) -> str:
    return "[" + ",".join(str(int(value)) for value in values) + "]"


__all__ = [
    "bounded_wrench_residual",
    "certificate_records",
    "certify_assignment",
    "filter_certified_assignment",
    "physical_welfare",
]
