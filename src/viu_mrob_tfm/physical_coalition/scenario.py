"""Deterministic paired worlds for the physical-coalition certificate ladder."""

from __future__ import annotations

import math

import numpy as np

from .model import PhysicalWorld


SCENARIO_FAMILIES = (
    "nominal_rotation",
    "scarcity_capacity",
    "torque_complementarity",
    "obstacle_network_dropout",
)


def make_world(*, family: str, seed: int, ordinal: int = 0) -> PhysicalWorld:
    if family not in SCENARIO_FAMILIES:
        raise ValueError(f"unknown physical-coalition family: {family}")
    rng = np.random.default_rng(int(seed))
    if family == "scarcity_capacity":
        n_robots = int(rng.integers(5, 7))
        quorum = 4
    elif family == "obstacle_network_dropout":
        n_robots = int(rng.integers(7, 10))
        quorum = 4
    else:
        n_robots = int(rng.integers(6, 9))
        quorum = 3

    load_start = np.array([-4.2, rng.uniform(-0.35, 0.35), rng.uniform(-0.08, 0.08)])
    load_target = np.array([4.2, rng.uniform(-0.25, 0.25), rng.uniform(0.28, 0.62)])
    robot_positions = load_start[:2] + rng.normal(0.0, [1.5, 1.0], size=(n_robots, 2))
    robot_capacity = rng.uniform(6.0, 12.0, size=n_robots)
    robot_force_limit = rng.uniform(4.5, 8.5, size=n_robots)
    robot_health = rng.uniform(0.62, 1.0, size=n_robots)

    if family == "scarcity_capacity":
        capacity_demand = float(np.quantile(robot_capacity * robot_health, 0.55) * quorum * 0.98)
        wrench_demand = np.array([13.0, 0.8, 1.6])
    elif family == "torque_complementarity":
        capacity_demand = float(np.mean(robot_capacity * robot_health) * 2.45)
        wrench_demand = np.array([10.0, 0.0, rng.choice([-1.0, 1.0]) * 5.2])
    elif family == "obstacle_network_dropout":
        capacity_demand = float(np.mean(robot_capacity * robot_health) * 3.0)
        wrench_demand = np.array([12.0, 1.0, 2.4])
    else:
        capacity_demand = float(np.mean(robot_capacity * robot_health) * 2.35)
        wrench_demand = np.array([11.0, 0.4, 1.8])

    slot_offsets, slot_normals = _contact_slots()
    if family == "obstacle_network_dropout":
        obstacle_center = np.array([0.0, rng.uniform(-0.15, 0.15)])
        obstacle_radius = 0.72
        packet_loss = 0.22
        delay_steps = 3
        dropout_time_s = 7.5
    else:
        obstacle_center = np.array([0.0, 2.8])
        obstacle_radius = 0.55
        packet_loss = 0.02
        delay_steps = 1
        dropout_time_s = math.inf

    return PhysicalWorld(
        world_id=f"pcert-{family}-{ordinal:03d}",
        seed=int(seed),
        family=family,
        robot_positions=robot_positions,
        robot_capacity=robot_capacity,
        robot_force_limit=robot_force_limit,
        robot_health=robot_health,
        load_start=load_start,
        load_target=load_target,
        quorum=quorum,
        capacity_demand=capacity_demand,
        wrench_demand=wrench_demand,
        slot_offsets=slot_offsets,
        slot_normals=slot_normals,
        obstacle_center=obstacle_center,
        obstacle_radius=float(obstacle_radius),
        dropout_robot=int(rng.integers(0, n_robots)),
        dropout_time_s=float(dropout_time_s),
        packet_loss=float(packet_loss),
        delay_steps=int(delay_steps),
    )


def _contact_slots() -> tuple[np.ndarray, np.ndarray]:
    offsets = np.array(
        [
            [-1.15, -0.58],
            [-1.15, 0.58],
            [-0.25, -0.72],
            [-0.25, 0.72],
            [0.55, -0.72],
            [0.55, 0.72],
            [1.15, -0.50],
            [1.15, 0.50],
        ],
        dtype=float,
    )
    directions = np.array(
        [
            [1.0, -0.30],
            [1.0, 0.30],
            [0.92, -0.55],
            [0.92, 0.55],
            [0.92, 0.55],
            [0.92, -0.55],
            [1.0, 0.38],
            [1.0, -0.38],
        ],
        dtype=float,
    )
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    return offsets, directions
