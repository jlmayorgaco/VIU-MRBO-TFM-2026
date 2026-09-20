"""Paired scenario generation for the six SP1-GEO regime families."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .geometry import circle_slots, planar_wrench_column, rectangular_slots
from .models import GeoLoad, GeoRobot, GeoWorld

FAMILY_DEFAULTS: dict[str, dict[str, Any]] = {
    "F0_easy_separable": {
        "demand_pressure": 0.70,
        "heterogeneity": 0.03,
        "compatibility_probability": 1.0,
        "communication_degree": 6,
        "shapes": ["circle"],
        "route_turns": [0.0],
    },
    "F1_heterogeneous_critical": {
        "demand_pressure": 0.95,
        "heterogeneity": 0.28,
        "compatibility_probability": 0.82,
        "communication_degree": 5,
        "shapes": ["rectangle", "square"],
        "route_turns": [0.0, math.pi / 4.0],
    },
    "F2_scarce_priority": {
        "demand_pressure": 1.20,
        "heterogeneity": 0.22,
        "compatibility_probability": 0.86,
        "communication_degree": 5,
        "shapes": ["circle", "rectangle"],
        "route_turns": [0.0, math.pi / 2.0],
    },
    "F3_torque_complementarity": {
        "demand_pressure": 0.95,
        "heterogeneity": 0.20,
        "compatibility_probability": 0.88,
        "communication_degree": 5,
        "shapes": ["rectangle"],
        "route_turns": [math.pi / 2.0],
    },
    "F4_mixed_geometry_route": {
        "demand_pressure": 0.95,
        "heterogeneity": 0.25,
        "compatibility_probability": 0.84,
        "communication_degree": 5,
        "shapes": ["circle", "square", "rectangle", "superellipse"],
        "route_turns": [0.0, math.pi / 2.0],
    },
    "F5_network_failure": {
        "demand_pressure": 0.95,
        "heterogeneity": 0.24,
        "compatibility_probability": 0.84,
        "communication_degree": 2,
        "packet_loss_probability": 0.15,
        "shapes": ["rectangle", "superellipse"],
        "route_turns": [0.0, math.pi / 2.0],
    },
}


def load_scenario_parameters(path: str | Path) -> dict[str, Any]:
    """Load one versioned family parameter file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Scenario file {path} must contain a mapping.")
    return payload


def _stable_family_offset(family: str) -> int:
    return int(hashlib.sha256(family.encode("utf-8")).hexdigest()[:8], 16)


def _connected_knn_graph(positions: np.ndarray, degree: int) -> np.ndarray:
    n = len(positions)
    adjacency = np.zeros((n, n), dtype=bool)
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    for robot in range(n):
        nearest = np.argsort(distances[robot])[: min(max(int(degree), 1), n - 1)]
        adjacency[robot, nearest] = True
    adjacency |= adjacency.T
    # A deterministic minimum spanning chain prevents accidental isolated
    # components while preserving sparse/local communication.
    visited = {0}
    while len(visited) < n:
        best: tuple[float, int, int] | None = None
        for left in visited:
            for right in range(n):
                if right in visited:
                    continue
                candidate = (float(distances[left, right]), left, right)
                if best is None or candidate < best:
                    best = candidate
        assert best is not None
        _, left, right = best
        adjacency[left, right] = adjacency[right, left] = True
        visited.add(right)
    np.fill_diagonal(adjacency, False)
    return adjacency


def _is_connected(adjacency: np.ndarray) -> bool:
    if len(adjacency) == 0:
        return True
    visited = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for neighbor in np.flatnonzero(adjacency[node]):
            value = int(neighbor)
            if value not in visited:
                visited.add(value)
                frontier.append(value)
    return len(visited) == len(adjacency)


def _slot_count(
    demand_kg: float,
    median_payload_kg: float,
    n_robots: int,
    n_loads: int,
) -> int:
    nominal = int(math.ceil(demand_kg / max(median_payload_kg, 1e-9)))
    per_load_cap = max(2, int(math.ceil(n_robots / n_loads)) + 2)
    return int(np.clip(nominal + 1, 2, per_load_cap))


def generate_world(
    family: str,
    n_robots: int,
    n_loads: int,
    seed: int,
    *,
    parameters: dict[str, Any] | None = None,
) -> GeoWorld:
    """Generate one frozen, reproducible world shared by all treatments."""

    if family not in FAMILY_DEFAULTS:
        raise ValueError(f"Unknown SP1-GEO family: {family}")
    if n_robots < n_loads or n_loads < 1:
        raise ValueError("SP1-GEO requires n_robots >= n_loads >= 1.")
    config = {**FAMILY_DEFAULTS[family], **(parameters or {})}
    mixed_seed = (int(seed) + _stable_family_offset(family)) % (2**32)
    rng = np.random.default_rng(mixed_seed)
    map_size = np.array(
        [max(18.0, 2.2 * math.sqrt(n_robots) + 12.0), max(14.0, 1.8 * math.sqrt(n_robots) + 10.0)],
        dtype=float,
    )
    robot_positions = rng.uniform(-0.45 * map_size, 0.45 * map_size, size=(n_robots, 2))
    heterogeneity = float(config["heterogeneity"])

    if family == "F0_easy_separable":
        payload = np.full(n_robots, 20.0)
        force = np.full(n_robots, 45.0)
        torque = np.full(n_robots, 55.0)
        battery = np.full(n_robots, 560.0)
        speed = np.full(n_robots, 0.70)
        reliability = np.full(n_robots, 0.98)
    else:
        payload = np.clip(rng.lognormal(np.log(20.0), heterogeneity, n_robots), 9.0, 38.0)
        force = np.clip(rng.lognormal(np.log(44.0), heterogeneity, n_robots), 20.0, 78.0)
        torque = np.clip(
            force * rng.uniform(0.9, 1.7, n_robots), 24.0, 105.0
        )
        battery = rng.uniform(390.0, 690.0, n_robots)
        speed = rng.uniform(0.48, 0.82, n_robots)
        reliability = rng.uniform(0.80, 0.995, n_robots)

    failed_index: int | None = None
    if family == "F5_network_failure":
        failed_index = int(rng.integers(0, n_robots))
        reliability[failed_index] = 0.0

    demand_pressure = float(config["demand_pressure"])
    active_payload = float(np.sum(payload[reliability > 0.0]))
    weights = (
        np.full(n_loads, 1.0 / n_loads)
        if family == "F0_easy_separable"
        else rng.dirichlet(np.full(n_loads, 1.5))
    )
    total_demand = demand_pressure * active_payload
    capacity_demands = np.maximum(total_demand * weights, 0.75 * float(np.median(payload)))
    capacity_demands *= total_demand / float(np.sum(capacity_demands))
    priority = rng.uniform(1.0, 3.0, n_loads)
    if family == "F2_scarce_priority":
        priority *= np.linspace(0.75, 2.25, n_loads)

    load_origins = rng.uniform(-0.30 * map_size, 0.30 * map_size, size=(n_loads, 2))
    load_destinations = np.clip(
        load_origins + rng.uniform(-0.35 * map_size, 0.35 * map_size, size=(n_loads, 2)),
        -0.45 * map_size,
        0.45 * map_size,
    )
    shapes = list(config["shapes"])
    route_turns = list(config["route_turns"])
    median_payload = float(np.median(payload))
    median_force = float(np.median(force))
    loads: list[GeoLoad] = []

    for load_index in range(n_loads):
        shape = str(shapes[load_index % len(shapes)])
        demand = float(capacity_demands[load_index])
        count = _slot_count(demand, median_payload, n_robots, n_loads)
        minimum = max(1, int(math.ceil(demand / max(float(np.quantile(payload, 0.65)), 1e-9))))
        if family == "F0_easy_separable":
            minimum = max(
                minimum, int(math.ceil(demand / max(0.82 * median_payload, 1e-9)))
            )
        minimum = min(minimum, count)
        length = float(rng.uniform(1.2, 3.5))
        width = float(rng.uniform(0.7, min(1.8, length)))
        if shape == "square":
            width = length = float(rng.uniform(1.1, 2.0))
        if shape == "circle":
            length = width = float(rng.uniform(1.0, 1.8))
        if family == "F3_torque_complementarity":
            length = float(rng.uniform(2.8, 4.2))
            width = float(rng.uniform(0.8, 1.3))
            count = max(count, 4)

        max_slot_force = float(np.quantile(force, 0.70))
        if shape == "circle" and family != "F0_easy_separable":
            slots = circle_slots(
                count,
                radius_m=0.5 * length,
                force_limit_n=max_slot_force,
                prefix=f"L{load_index:02d}-circle",
            )
        else:
            slots = rectangular_slots(
                count,
                length,
                width,
                force_limit_n=max_slot_force,
                mixed_directions=family != "F0_easy_separable",
                prefix=f"L{load_index:02d}-{shape}",
            )

        nominal_force = max(
            18.0, 0.42 * minimum * median_force * rng.uniform(0.75, 1.0)
        )
        if family == "F0_easy_separable":
            wrench = np.array([nominal_force, 0.0, 0.0])
        elif family == "F3_torque_complementarity":
            signs = np.array(
                [np.sign(planar_wrench_column(slot)[2]) for slot in slots], dtype=float
            )
            preferred_sign = -1.0 if np.sum(signs < 0.0) >= np.sum(signs > 0.0) else 1.0
            torque_demand = preferred_sign * 0.52 * minimum * median_force * max(width, 0.5)
            wrench = np.array([0.0, 0.0, torque_demand])
        elif family == "F4_mixed_geometry_route":
            torque_sign = -1.0 if load_index % 2 else 1.0
            wrench = np.array(
                [0.65 * nominal_force, (-1.0) ** load_index * 0.25 * nominal_force, torque_sign * 0.30 * nominal_force]
            )
        else:
            torque_sign = -1.0 if load_index % 2 else 1.0
            wrench = np.array(
                [nominal_force, 0.12 * nominal_force * ((load_index % 3) - 1), torque_sign * 0.12 * nominal_force]
            )

        com_offset = (
            rng.uniform([-0.25 * length, -0.20 * width], [0.25 * length, 0.20 * width])
            if family in {"F1_heterogeneous_critical", "F4_mixed_geometry_route"}
            else np.zeros(2)
        )
        route_turn = float(route_turns[load_index % len(route_turns)])
        loads.append(
            GeoLoad(
                identifier=f"load-{load_index:03d}",
                origin_xy_m=load_origins[load_index],
                destination_xy_m=load_destinations[load_index],
                mass_kg=0.90 * demand,
                shape=shape,
                dimensions_m=np.array([length, width]),
                com_offset_xy_m=com_offset,
                priority_value=float(priority[load_index]),
                deadline_s=float(rng.uniform(70.0, 160.0)),
                min_capacity_kg=demand,
                max_capacity_kg=float(1.75 * demand),
                min_coalition_size=minimum,
                required_wrench=wrench,
                wrench_tolerance=float(config.get("wrench_tolerance", 0.08)),
                route_turn_rad=route_turn,
                slots=slots,
            )
        )

    all_roles = sorted({slot.role for load in loads for slot in load.slots})
    compatibility_probability = float(config["compatibility_probability"])
    robot_load_mask = rng.random((n_robots, n_loads)) < compatibility_probability
    # Ensure each load has at least its minimum number of compatible robots.
    for load_index, load in enumerate(loads):
        candidates = np.argsort(
            np.linalg.norm(robot_positions - load.origin_xy_m[None, :], axis=1)
        )[: max(load.min_coalition_size + 1, 2)]
        robot_load_mask[candidates, load_index] = True

    robots: list[GeoRobot] = []
    for robot_index in range(n_robots):
        if family == "F0_easy_separable":
            roles = tuple(all_roles)
        else:
            selected_roles = [
                role for role in all_roles if rng.random() < 0.82
            ]
            if not selected_roles:
                selected_roles = [all_roles[robot_index % len(all_roles)]]
            # A deterministic versatile subset prevents accidental generator
            # infeasibility while retaining role heterogeneity.
            if robot_index < max(2, n_loads):
                selected_roles = list(all_roles)
            roles = tuple(sorted(set(selected_roles)))
        robots.append(
            GeoRobot(
                identifier=f"amr-{robot_index:03d}",
                pose_xytheta=np.array(
                    [
                        robot_positions[robot_index, 0],
                        robot_positions[robot_index, 1],
                        rng.uniform(-math.pi, math.pi),
                    ]
                ),
                payload_kg=float(payload[robot_index]),
                force_limit_n=float(force[robot_index]),
                torque_limit_nm=float(torque[robot_index]),
                battery_wh=float(battery[robot_index]),
                safe_battery_wh=float(0.18 * battery[robot_index]),
                max_speed_mps=float(speed[robot_index]),
                reliability=float(reliability[robot_index]),
                compatible_loads=tuple(np.flatnonzero(robot_load_mask[robot_index]).tolist()),
                compatible_roles=roles,
                failed=robot_index == failed_index,
            )
        )

    adjacency = _connected_knn_graph(
        robot_positions, degree=int(config["communication_degree"])
    )
    dropped_edges = 0
    if family == "F5_network_failure":
        loss_probability = float(config.get("packet_loss_probability", 0.0))
        for left in range(n_robots):
            for right in range(left + 1, n_robots):
                if adjacency[left, right] and rng.random() < loss_probability:
                    adjacency[left, right] = adjacency[right, left] = False
                    if _is_connected(adjacency):
                        dropped_edges += 1
                    else:
                        adjacency[left, right] = adjacency[right, left] = True
    parameters_for_hash = {
        key: value
        for key, value in config.items()
        if isinstance(value, (str, int, float, bool, list, tuple, type(None)))
    }
    parameters_for_hash["failed_robot_index"] = failed_index
    parameters_for_hash["packet_loss_realization"] = (
        "frozen_nonbridge_edge_dropout"
    )
    parameters_for_hash["dropped_communication_edges"] = dropped_edges
    return GeoWorld(
        family=family,
        seed=int(seed),
        robots=tuple(robots),
        loads=tuple(loads),
        communication_adjacency=adjacency,
        map_size_m=map_size,
        demand_pressure=demand_pressure,
        scenario_parameters=parameters_for_hash,
    )


def torque_complementarity_world() -> GeoWorld:
    """Return the deterministic two-robot T8 counterexample."""

    slots = rectangular_slots(
        2,
        length_m=2.0,
        width_m=2.0,
        force_limit_n=10.0,
        mixed_directions=True,
        prefix="torque",
    )
    load = GeoLoad(
        identifier="torque-load",
        origin_xy_m=np.zeros(2),
        destination_xy_m=np.array([1.0, 0.0]),
        mass_kg=10.0,
        shape="rectangle",
        dimensions_m=np.array([2.0, 2.0]),
        com_offset_xy_m=np.zeros(2),
        priority_value=50.0,
        deadline_s=60.0,
        min_capacity_kg=10.0,
        max_capacity_kg=30.0,
        min_coalition_size=2,
        required_wrench=np.array([0.0, 0.0, -16.0]),
        wrench_tolerance=1e-8,
        route_turn_rad=math.pi / 2.0,
        slots=slots,
    )
    roles = tuple(slot.role for slot in slots)
    robots = tuple(
        GeoRobot(
            identifier=f"torque-amr-{index}",
            pose_xytheta=np.array([float(index), -2.0, 0.0]),
            payload_kg=10.0,
            force_limit_n=10.0,
            torque_limit_nm=12.0,
            battery_wh=100.0,
            safe_battery_wh=10.0,
            max_speed_mps=1.0,
            reliability=1.0,
            compatible_loads=(0,),
            compatible_roles=roles,
        )
        for index in range(2)
    )
    return GeoWorld(
        family="T8_torque_complementarity",
        seed=0,
        robots=robots,
        loads=(load,),
        communication_adjacency=np.array([[False, True], [True, False]]),
        map_size_m=np.array([8.0, 8.0]),
        demand_pressure=1.0,
        scenario_parameters={"deterministic": True},
    )


__all__ = [
    "FAMILY_DEFAULTS",
    "generate_world",
    "load_scenario_parameters",
    "torque_complementarity_world",
]
