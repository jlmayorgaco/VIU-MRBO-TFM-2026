"""Resource-allocation model and constructive worlds for SP1 validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

import numpy as np


RESOURCE_NAMES = ("cardinality", "payload", "force")
ROBOT_CLASSES = ("small", "medium", "heavy")


@dataclass(frozen=True, slots=True)
class ResourceWorld:
    seed: int
    robot_positions_m: np.ndarray
    load_positions_m: np.ndarray
    resources: np.ndarray
    requirements: np.ndarray
    battery_energy: np.ndarray
    max_speed_mps: np.ndarray
    energy_per_m: np.ndarray
    robot_classes: tuple[str, ...]
    feasibility_witness: np.ndarray
    world_hash: str

    @property
    def n_robots(self) -> int:
        return int(self.resources.shape[0])

    @property
    def n_loads(self) -> int:
        return int(self.requirements.shape[0])


def generate_resource_world(n_robots: int, n_loads: int, seed: int) -> ResourceWorld:
    """Generate a heterogeneous feasible instance, then leave certification to MILP."""

    if n_robots < n_loads:
        raise ValueError("A constructive SP1 world needs at least one robot per load")
    if n_loads < 1:
        raise ValueError("SP1 needs at least one load")
    rng = np.random.default_rng(int(seed) + 7919 * n_robots + 104729 * n_loads)
    positions = rng.uniform(0.5, 19.5, size=(n_robots, 2))
    load_positions = rng.uniform(2.0, 18.0, size=(n_loads, 2))

    class_ids = rng.integers(0, len(ROBOT_CLASSES), size=n_robots)
    payload_ranges = ((6.0, 12.0), (13.0, 23.0), (25.0, 42.0))
    force_ranges = ((7.0, 14.0), (14.0, 25.0), (22.0, 38.0))
    speed_ranges = ((1.15, 1.65), (0.80, 1.20), (0.48, 0.88))
    battery_ranges = ((45.0, 75.0), (65.0, 100.0), (95.0, 145.0))
    consumption_ranges = ((0.55, 0.85), (0.75, 1.05), (1.00, 1.40))

    payload = np.empty(n_robots)
    force = np.empty(n_robots)
    speed = np.empty(n_robots)
    battery = np.empty(n_robots)
    consumption = np.empty(n_robots)
    classes: list[str] = []
    for robot, class_id in enumerate(class_ids):
        idx = int(class_id)
        payload[robot] = rng.uniform(*payload_ranges[idx])
        force[robot] = rng.uniform(*force_ranges[idx])
        speed[robot] = rng.uniform(*speed_ranges[idx])
        battery[robot] = rng.uniform(*battery_ranges[idx])
        consumption[robot] = rng.uniform(*consumption_ranges[idx])
        classes.append(ROBOT_CLASSES[idx])
    resources = np.column_stack([np.ones(n_robots), payload, force])

    # Disjoint provisional coalitions make feasibility constructive without
    # leaking the provisional assignment to any solver.
    permutation = rng.permutation(n_robots)
    base_size = max(1, min(5, n_robots // n_loads))
    cursor = 0
    requirements = np.zeros((n_loads, len(RESOURCE_NAMES)), dtype=float)
    witness = np.full(n_robots, -1, dtype=int)
    for load in range(n_loads):
        remaining_loads = n_loads - load
        remaining_robots = n_robots - cursor
        size = min(base_size, remaining_robots - (remaining_loads - 1))
        coalition = permutation[cursor : cursor + size]
        witness[coalition] = load
        cursor += size
        fraction = rng.uniform(0.72, 0.88, size=2)
        requirements[load, 0] = max(1, int(np.ceil(0.72 * size)))
        requirements[load, 1:] = resources[coalition, 1:].sum(axis=0) * fraction
        distance = np.linalg.norm(positions[coalition] - load_positions[load], axis=1)
        battery[coalition] = np.maximum(battery[coalition], 1.5 * distance * consumption[coalition] + 8.0)

    payload_record = {
        "seed": int(seed),
        "positions": positions.round(12).tolist(),
        "load_positions": load_positions.round(12).tolist(),
        "resources": resources.round(12).tolist(),
        "requirements": requirements.round(12).tolist(),
        "battery": battery.round(12).tolist(),
        "speed": speed.round(12).tolist(),
        "consumption": consumption.round(12).tolist(),
        "classes": classes,
        "feasibility_witness": witness.tolist(),
    }
    digest = hashlib.sha256(json.dumps(payload_record, sort_keys=True).encode("utf-8")).hexdigest()
    return ResourceWorld(
        seed=int(seed),
        robot_positions_m=positions,
        load_positions_m=load_positions,
        resources=resources,
        requirements=requirements,
        battery_energy=battery,
        max_speed_mps=speed,
        energy_per_m=consumption,
        robot_classes=tuple(classes),
        feasibility_witness=witness,
        world_hash=digest,
    )


def manual_world() -> ResourceWorld:
    """Return the fixed five-robot diagnostic instance described by the author."""

    positions = np.asarray([[2.0, 0.0], [3.0, 0.0], [8.0, 0.0], [15.0, 0.0], [5.0, 0.0]])
    load_positions = np.asarray([[0.0, 0.0]])
    resources = np.asarray(
        [[1.0, 10.0, 8.0], [1.0, 10.0, 10.0], [1.0, 20.0, 18.0], [1.0, 40.0, 30.0], [1.0, 15.0, 12.0]]
    )
    battery = np.asarray([80.0, 75.0, 90.0, 35.0, 60.0])
    speed = np.asarray([1.3, 1.2, 0.9, 0.6, 1.0])
    consumption = np.full(5, 3.0)
    requirements = np.asarray([[2.0, 40.0, 35.0]])
    record = {
        "positions": positions.tolist(),
        "loads": load_positions.tolist(),
        "resources": resources.tolist(),
        "requirements": requirements.tolist(),
        "battery": battery.tolist(),
        "speed": speed.tolist(),
        "consumption": consumption.tolist(),
        "feasibility_witness": [0, 0, 0, -1, -1],
    }
    digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest()
    return ResourceWorld(
        seed=0,
        robot_positions_m=positions,
        load_positions_m=load_positions,
        resources=resources,
        requirements=requirements,
        battery_energy=battery,
        max_speed_mps=speed,
        energy_per_m=consumption,
        robot_classes=("small", "small", "medium", "heavy", "medium"),
        feasibility_witness=np.asarray([0, 0, 0, -1, -1], dtype=int),
        world_hash=digest,
    )


def build_costs(
    world: ResourceWorld,
    weights: Mapping[str, float],
    *,
    reserve_energy: float = 5.0,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Return C_ik, battery mask and its distance/time/energy components."""

    delta = world.robot_positions_m[:, None, :] - world.load_positions_m[None, :, :]
    distance = np.linalg.norm(delta, axis=2)
    travel_time = distance / np.maximum(world.max_speed_mps[:, None], 1e-9)
    energy = distance * world.energy_per_m[:, None]
    compatible = energy + float(reserve_energy) <= world.battery_energy[:, None]
    costs = (
        float(weights.get("distance", 0.45)) * distance
        + float(weights.get("time", 0.25)) * travel_time
        + float(weights.get("energy", 0.30)) * energy
    )
    costs = np.where(compatible, costs, np.inf)
    return costs, compatible, {"distance": distance, "time": travel_time, "energy": energy}


def normalized_constraints(world: ResourceWorld) -> np.ndarray:
    """Return a[i,m]/b[k,m] as tensor (i,k,m)."""

    return world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)


def world_record(world: ResourceWorld) -> dict[str, object]:
    return {
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "mean_payload": float(np.mean(world.resources[:, 1])),
        "mean_force": float(np.mean(world.resources[:, 2])),
        "mean_battery": float(np.mean(world.battery_energy)),
        "constructive_witness_assigned": int(np.sum(world.feasibility_witness >= 0)),
        "requirements": json.dumps(world.requirements.tolist()),
    }


__all__ = [
    "RESOURCE_NAMES",
    "ROBOT_CLASSES",
    "ResourceWorld",
    "build_costs",
    "generate_resource_world",
    "manual_world",
    "normalized_constraints",
    "world_record",
]
