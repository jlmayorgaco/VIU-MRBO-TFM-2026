"""Build paired scalar/physical action signals from one frozen world."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .geometry import aligned_wrench_resources, demand_resource_vector, planar_wrench_column
from .models import ActionCatalog, GeoWorld


DEFAULT_COST_WEIGHTS = {
    "distance": 0.38,
    "energy": 0.24,
    "time": 0.18,
    "turn": 0.12,
    "reliability": 0.08,
}


def _route_length(load: Any) -> float:
    straight = float(np.linalg.norm(load.destination_xy_m - load.origin_xy_m))
    return straight * (1.0 + 0.22 * abs(float(load.route_turn_rad)) / (math.pi / 2.0))


def build_action_catalog(
    world: GeoWorld,
    *,
    cost_weights: dict[str, float] | None = None,
) -> ActionCatalog:
    """Construct every robot--load--slot action exactly once."""

    weights = {**DEFAULT_COST_WEIGHTS, **(cost_weights or {})}
    robot_indices: list[int] = []
    load_indices: list[int] = []
    slot_indices: list[int] = []
    compatible_values: list[bool] = []
    costs: list[float] = []
    distances: list[float] = []
    mission_energies: list[float] = []
    force_uppers: list[float] = []
    wrench_columns: list[np.ndarray] = []
    scalar_rows: list[np.ndarray] = []
    physical_rows: list[np.ndarray] = []
    map_diagonal = max(float(np.linalg.norm(world.map_size_m)), 1e-9)

    for robot_index, robot in enumerate(world.robots):
        start = robot.pose_xytheta[:2]
        for load_index, load in enumerate(world.loads):
            route_length = _route_length(load)
            return_length = float(np.linalg.norm(load.destination_xy_m - start))
            for slot_index, slot in enumerate(load.slots):
                target = load.origin_xy_m + slot.offset_xy_m
                approach = float(np.linalg.norm(start - target))
                travel_distance = approach + route_length
                energy_per_m = 0.045 + 0.0015 * robot.payload_kg
                mission_energy = energy_per_m * (travel_distance + 0.45 * return_length)
                battery_margin = robot.battery_wh - robot.safe_battery_wh - mission_energy
                battery_factor = float(
                    np.clip(
                        battery_margin
                        / max(robot.battery_wh - robot.safe_battery_wh, 1e-9),
                        0.0,
                        1.0,
                    )
                )
                distance_factor = (
                    1.0
                    if world.family == "F0_easy_separable"
                    else math.exp(-approach / max(1.20 * map_diagonal, 1e-9))
                )
                role_compatible = slot.role in robot.compatible_roles
                load_compatible = load_index in robot.compatible_loads
                feasible_pair = bool(
                    not robot.failed
                    and robot.reliability > 0.0
                    and role_compatible
                    and load_compatible
                    and battery_margin >= 0.0
                )

                column = planar_wrench_column(
                    slot, com_offset_xy_m=load.com_offset_xy_m
                )
                moment_per_n = abs(float(column[2]))
                force_upper = min(robot.force_limit_n, slot.max_force_n)
                if moment_per_n > 1e-12:
                    force_upper = min(
                        force_upper, robot.torque_limit_nm / moment_per_n
                    )
                turn_derate = 1.0 / (
                    1.0 + 0.18 * abs(float(load.route_turn_rad)) / (math.pi / 2.0)
                )
                force_upper *= robot.reliability * turn_derate
                effective_payload = (
                    robot.payload_kg
                    * battery_factor
                    * distance_factor
                    * robot.reliability
                )
                aligned = (
                    aligned_wrench_resources(column, load.required_wrench)
                    * force_upper
                )
                physical = np.concatenate(
                    [
                        np.array([effective_payload]),
                        aligned,
                        np.array(
                            [
                                max(battery_margin / max(robot.battery_wh, 1e-9), 0.0),
                                robot.reliability,
                            ]
                        ),
                    ]
                )
                if not feasible_pair:
                    effective_payload = 0.0
                    physical = np.zeros(7, dtype=float)
                    force_upper = 0.0

                approach_time = approach / max(robot.max_speed_mps, 1e-9)
                cost = (
                    float(weights["distance"]) * approach / map_diagonal
                    + float(weights["energy"]) * mission_energy / max(robot.battery_wh, 1e-9)
                    + float(weights["time"]) * approach_time / max(load.deadline_s, 1e-9)
                    + float(weights["turn"]) * abs(load.route_turn_rad) / math.pi
                    + float(weights["reliability"]) * (1.0 - robot.reliability)
                )
                if not feasible_pair:
                    cost += 1e3

                robot_indices.append(robot_index)
                load_indices.append(load_index)
                slot_indices.append(slot_index)
                compatible_values.append(feasible_pair)
                costs.append(float(cost))
                distances.append(travel_distance)
                mission_energies.append(mission_energy)
                force_uppers.append(force_upper)
                wrench_columns.append(column)
                scalar_rows.append(np.array([effective_payload], dtype=float))
                physical_rows.append(physical)

    scalar_demands = np.array(
        [[load.min_capacity_kg] for load in world.loads], dtype=float
    )
    physical_demands = []
    for load in world.loads:
        wrench_resources = demand_resource_vector(load.required_wrench)
        physical_demands.append(
            np.concatenate(
                [
                    np.array([load.min_capacity_kg]),
                    wrench_resources,
                    np.array(
                        [
                            0.10 * load.min_coalition_size,
                            0.75 * load.min_coalition_size,
                        ]
                    ),
                ]
            )
        )
    return ActionCatalog(
        robot_index=np.asarray(robot_indices, dtype=int),
        load_index=np.asarray(load_indices, dtype=int),
        slot_index=np.asarray(slot_indices, dtype=int),
        compatible=np.asarray(compatible_values, dtype=bool),
        costs=np.asarray(costs, dtype=float),
        travel_distance_m=np.asarray(distances, dtype=float),
        mission_energy_wh=np.asarray(mission_energies, dtype=float),
        force_upper_n=np.asarray(force_uppers, dtype=float),
        wrench_columns_per_n=np.vstack(wrench_columns),
        scalar_contributions=np.vstack(scalar_rows),
        physical_contributions=np.vstack(physical_rows),
        scalar_demands=scalar_demands,
        physical_demands=np.vstack(physical_demands),
    )


def aggregate_signal(
    catalog: ActionCatalog,
    preferences: np.ndarray,
    signal: str,
    n_loads: int,
) -> np.ndarray:
    """Aggregate an action vector by load."""

    x = np.asarray(preferences, dtype=float)
    if x.shape != (catalog.n_actions,):
        raise ValueError("preferences has the wrong shape.")
    contributions = catalog.contributions(signal)  # type: ignore[arg-type]
    aggregate = np.zeros((n_loads, contributions.shape[1]), dtype=float)
    np.add.at(aggregate, catalog.load_index, x[:, None] * contributions)
    return aggregate


__all__ = [
    "DEFAULT_COST_WEIGHTS",
    "aggregate_signal",
    "build_action_catalog",
]
