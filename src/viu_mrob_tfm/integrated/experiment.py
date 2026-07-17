"""Reproducible end-to-end Cargo campaign.

The simulator composes one deliberately narrow path through SP2--SP6:
heterogeneous recruitment, local versioned communication, dynamic-unicycle
docking, a planar rigid-payload plant, obstacle avoidance, a single robot
failure, local replacement and mission resumption.  It does not model 3-D
support, frictional contact, perception, a radio stack or hardware.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import yaml


METHODS = (
    "distributed_full",
    "perfect_information",
    "decoupled_local",
    "no_physical_guard",
    "no_repair",
    "central_reference",
)

METHOD_LABELS = {
    "distributed_full": "Vecinal completo",
    "perfect_information": "Información perfecta",
    "decoupled_local": "Vecinal sin acoplamiento espacial",
    "no_physical_guard": "Vecinal sin guardia física",
    "no_repair": "Vecinal sin reparación",
    "central_reference": "Referencia central",
}

SCENARIOS = (
    "open_nominal",
    "static_obstacle",
    "degraded_network",
    "failure_during_transport",
)

SCENARIO_LABELS = {
    "open_nominal": "Abierto nominal",
    "static_obstacle": "Obstáculo estático",
    "degraded_network": "Red degradada",
    "failure_during_transport": "Fallo durante transporte",
}

# Unit reference scales keep the archived Cargo ranking numerically unchanged
# while making every term in the empirical score dimensionless.
CARGO_DISTANCE_REFERENCE_M = 1.0
CARGO_PAYLOAD_REFERENCE_KG = 1.0
CARGO_FORCE_REFERENCE_N = 1.0


@dataclass(frozen=True, slots=True)
class CargoWorld:
    """One immutable world shared by every treatment."""

    scenario: str
    seed: int
    n_robots: int
    robot_positions: np.ndarray
    robot_headings: np.ndarray
    capacities_kg: np.ndarray
    force_limits_n: np.ndarray
    wheel_torque_limits_nm: np.ndarray
    communication_adjacency: np.ndarray
    communication_rounds: int
    max_delay_rounds: int
    packet_loss: float
    load_initial_pose: np.ndarray
    load_target_pose: np.ndarray
    load_mass_kg: float
    load_inertia_kgm2: float
    load_length_m: float
    load_width_m: float
    obstacle_center: np.ndarray | None
    obstacle_radius_m: float
    failure_enabled: bool
    failure_time_s: float
    world_hash: str

    @property
    def required_force_n(self) -> float:
        return 2.15 * self.load_mass_kg


@dataclass(frozen=True, slots=True)
class LocalSnapshot:
    known_indices: tuple[int, ...]
    messages: int
    bytes_sent: int
    connected_component_size: int


@dataclass(frozen=True, slots=True)
class RunResult:
    world_hash: str
    scenario: str
    seed: int
    n_robots: int
    method: str
    selected_initial: tuple[int, ...]
    selected_final: tuple[int, ...]
    mission_success: bool
    docking_success: bool
    mechanical_certificate_initial: bool
    failure_triggered: bool
    recovery_success: bool
    collision: bool
    timeout: bool
    numerical_failure: bool
    termination_reason: str
    mission_time_s: float
    docking_time_s: float
    recovery_time_s: float
    final_position_error_m: float
    final_orientation_error_rad: float
    min_clearance_m: float
    max_wrench_residual_n: float
    saturation_fraction: float
    max_wheel_torque_nm: float
    wheel_torque_saturations: int
    mechanical_work_j: float
    wheel_energy_j: float
    messages: int
    bytes_sent: int
    runtime_ms: float
    phase_trace: tuple[str, ...]
    load_trace: np.ndarray


def _wrap_angle(value: float | np.ndarray) -> float | np.ndarray:
    return (np.asarray(value) + np.pi) % (2.0 * np.pi) - np.pi


def _rotation(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _graph_connected(adjacency: np.ndarray, root: int = 0) -> tuple[bool, int]:
    visited = {int(root)}
    stack = [int(root)]
    while stack:
        node = stack.pop()
        for neighbor in np.flatnonzero(adjacency[node]):
            neighbor = int(neighbor)
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    return len(visited) == len(adjacency), len(visited)


def build_world(scenario: str, seed: int, n_robots: int) -> CargoWorld:
    """Generate one deterministic holdout world without method information."""

    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown integrated Cargo scenario: {scenario}")
    if n_robots not in {4, 8, 12}:
        raise ValueError("The preregistered robot counts are {4, 8, 12}.")
    rng = np.random.default_rng(int(seed) + 7919 * int(n_robots))
    load_pose = np.array([-3.0, -0.15 + rng.uniform(-0.12, 0.12), 0.0], dtype=float)
    target = np.array([3.1, 0.10 + rng.uniform(-0.12, 0.12), 0.0], dtype=float)
    angles = np.linspace(0.0, 2.0 * np.pi, n_robots, endpoint=False)
    angles += rng.uniform(-0.10, 0.10, size=n_robots)
    radii = rng.uniform(2.25, 2.75, size=n_robots)
    positions = load_pose[:2] + np.column_stack([np.cos(angles), np.sin(angles)]) * radii[:, None]
    headings = np.asarray([math.atan2(load_pose[1] - p[1], load_pose[0] - p[0]) for p in positions])

    capacities = rng.uniform(8.8, 10.8, size=n_robots)
    # Negative correlation makes the mechanical guard non-redundant.
    normalized = (capacities - capacities.min()) / max(float(np.ptp(capacities)), 1e-12)
    forces = 29.0 - 12.0 * normalized + rng.uniform(-1.2, 1.2, size=n_robots)
    forces = np.clip(forces, 15.0, 29.0)
    torque_limits = rng.uniform(3.2, 4.2, size=n_robots)

    network_radius = 3.25 if scenario == "degraded_network" else 4.25
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    adjacency = (distances <= network_radius) & (~np.eye(n_robots, dtype=bool))
    if not _graph_connected(adjacency, int(np.argmin(np.linalg.norm(positions - load_pose[:2], axis=1))))[0]:
        # Add only the minimum ring edges needed to avoid conflating packet loss with a permanent partition.
        order = np.argsort(angles)
        for a, b in zip(order, np.roll(order, -1)):
            adjacency[int(a), int(b)] = True
            adjacency[int(b), int(a)] = True

    mass = float(rng.uniform(23.0, 25.0))
    length, width = 1.25, 0.78
    inertia = mass * (length**2 + width**2) / 12.0
    obstacle = (
        np.array([0.05 + rng.uniform(-0.12, 0.12), rng.uniform(-0.08, 0.08)], dtype=float)
        if scenario != "open_nominal"
        else None
    )
    payload = {
        "scenario": scenario,
        "seed": int(seed),
        "n_robots": int(n_robots),
        "positions": positions.round(12).tolist(),
        "capacities": capacities.round(12).tolist(),
        "forces": forces.round(12).tolist(),
        "adjacency": adjacency.astype(int).tolist(),
        "load_pose": load_pose.round(12).tolist(),
        "target": target.round(12).tolist(),
        "mass": mass,
        "obstacle": None if obstacle is None else obstacle.round(12).tolist(),
    }
    return CargoWorld(
        scenario=scenario,
        seed=int(seed),
        n_robots=int(n_robots),
        robot_positions=positions,
        robot_headings=headings,
        capacities_kg=capacities,
        force_limits_n=forces,
        wheel_torque_limits_nm=torque_limits,
        communication_adjacency=adjacency,
        communication_rounds=10 if scenario == "degraded_network" else 7,
        max_delay_rounds=2 if scenario == "degraded_network" else 0,
        packet_loss=0.25 if scenario == "degraded_network" else 0.02,
        load_initial_pose=load_pose,
        load_target_pose=target,
        load_mass_kg=mass,
        load_inertia_kgm2=inertia,
        load_length_m=length,
        load_width_m=width,
        obstacle_center=obstacle,
        obstacle_radius_m=0.68,
        failure_enabled=scenario == "failure_during_transport",
        failure_time_s=9.0,
        world_hash=_hash_payload(payload),
    )


def _gossip_snapshot(
    world: CargoWorld,
    active: np.ndarray,
    *,
    event_seed: int,
) -> LocalSnapshot:
    """Exchange versioned robot records using delayed lossy neighbor messages."""

    n = world.n_robots
    # np.argmin resolves equal distances with the lowest robot identifier.
    leader = int(np.argmin(np.where(active, np.linalg.norm(world.robot_positions - world.load_initial_pose[:2], axis=1), np.inf)))
    views = [set([i]) if active[i] else set() for i in range(n)]
    queue: list[tuple[int, int, frozenset[int]]] = []
    rng = np.random.default_rng(int(world.seed) + int(event_seed))
    messages = 0
    bytes_sent = 0
    for round_index in range(world.communication_rounds):
        pending: list[tuple[int, int, frozenset[int]]] = []
        for arrival, receiver, records in queue:
            if arrival <= round_index:
                views[receiver].update(records)
            else:
                pending.append((arrival, receiver, records))
        queue = pending
        for sender in range(n):
            if not active[sender]:
                continue
            records = frozenset(index for index in views[sender] if active[index])
            for receiver in np.flatnonzero(world.communication_adjacency[sender]):
                receiver = int(receiver)
                if not active[receiver]:
                    continue
                messages += 1
                bytes_sent += 16 + 32 * len(records)
                if rng.random() < world.packet_loss:
                    continue
                delay = int(rng.integers(0, world.max_delay_rounds + 1))
                queue.append((round_index + delay + 1, receiver, records))
    for arrival, receiver, records in queue:
        if arrival <= world.communication_rounds:
            views[receiver].update(records)
    _, component_size = _graph_connected(world.communication_adjacency, leader)
    return LocalSnapshot(
        known_indices=tuple(sorted(index for index in views[leader] if active[index])),
        messages=messages,
        bytes_sent=bytes_sent,
        connected_component_size=component_size,
    )


def _certificate(world: CargoWorld, members: tuple[int, ...]) -> bool:
    if len(members) < 3:
        return False
    indices = np.asarray(members, dtype=int)
    return bool(
        np.sum(world.capacities_kg[indices]) >= world.load_mass_kg
        and np.sum(world.force_limits_n[indices]) >= world.required_force_n
    )


def _capacity_only(world: CargoWorld, members: tuple[int, ...]) -> bool:
    return bool(len(members) >= 3 and np.sum(world.capacities_kg[np.asarray(members, dtype=int)]) >= world.load_mass_kg)


def _cargo_spatial_score(world: CargoWorld, index: int, distance_m: float) -> float:
    """Return the dimensionless empirical Cargo recruitment score."""

    normalized_distance = float(distance_m) / CARGO_DISTANCE_REFERENCE_M
    normalized_payload = float(world.capacities_kg[index]) / CARGO_PAYLOAD_REFERENCE_KG
    normalized_force = float(world.force_limits_n[index]) / CARGO_FORCE_REFERENCE_N
    return normalized_distance - 0.08 * normalized_payload - 0.025 * normalized_force


def _greedy_select(
    world: CargoWorld,
    candidates: tuple[int, ...],
    *,
    spatial: bool,
    mechanical_guard: bool,
    fixed_members: tuple[int, ...] = (),
) -> tuple[int, ...]:
    members = list(fixed_members)
    candidates = tuple(index for index in candidates if index not in members)
    distance = np.linalg.norm(world.robot_positions - world.load_initial_pose[:2], axis=1)
    if spatial:
        key = lambda i: (_cargo_spatial_score(world, i, float(distance[i])), i)
    else:
        key = lambda i: (-world.capacities_kg[i], i)
    predicate = _certificate if mechanical_guard else _capacity_only
    for index in sorted(candidates, key=key):
        if not predicate(world, tuple(members)):
            members.append(int(index))
    return tuple(sorted(members)) if predicate(world, tuple(members)) else tuple(sorted(members))


def _central_select(
    world: CargoWorld,
    candidates: tuple[int, ...],
    *,
    fixed_members: tuple[int, ...] = (),
) -> tuple[int, ...]:
    remaining = tuple(index for index in candidates if index not in fixed_members)
    distance = np.linalg.norm(world.robot_positions - world.load_initial_pose[:2], axis=1)
    best: tuple[float, tuple[int, ...]] | None = None
    for size in range(0, len(remaining) + 1):
        for addition in itertools.combinations(remaining, size):
            members = tuple(sorted((*fixed_members, *addition)))
            if not _certificate(world, members):
                continue
            cost = float(np.sum(distance[np.asarray(addition, dtype=int)]) + 0.20 * len(members))
            if best is None or (cost, members) < best:
                best = (cost, members)
        if best is not None:
            break
    return best[1] if best is not None else tuple(sorted(fixed_members))


def _contact_offsets(world: CargoWorld, count: int) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    return np.column_stack(
        [0.52 * world.load_length_m * np.cos(angles), 0.52 * world.load_width_m * np.sin(angles)]
    )


def _unicycle_step(
    position: np.ndarray,
    heading: float,
    speed: float,
    yaw_rate: float,
    target: np.ndarray,
    *,
    torque_limit: float,
    dt: float,
) -> tuple[np.ndarray, float, float, float, float, int, float]:
    delta = target - position
    rho = float(np.linalg.norm(delta))
    desired_heading = math.atan2(delta[1], delta[0]) if rho > 1e-9 else heading
    alpha = float(_wrap_angle(desired_heading - heading))
    desired_speed = float(np.clip(1.15 * rho * max(math.cos(alpha), 0.0), 0.0, 0.75))
    desired_yaw = float(np.clip(3.2 * alpha, -2.5, 2.5))
    accel = float(np.clip((desired_speed - speed) / dt, -1.4, 1.4))
    yaw_accel = float(np.clip((desired_yaw - yaw_rate) / dt, -5.0, 5.0))
    robot_mass = 18.0
    robot_inertia = 1.6
    wheel_radius = 0.0975
    half_track = 0.165
    tau_r = 0.5 * wheel_radius * (robot_mass * accel + robot_inertia * yaw_accel / half_track)
    tau_l = 0.5 * wheel_radius * (robot_mass * accel - robot_inertia * yaw_accel / half_track)
    peak = max(abs(tau_r), abs(tau_l))
    saturated = int(peak > torque_limit)
    if saturated:
        scale = torque_limit / max(peak, 1e-12)
        accel *= scale
        yaw_accel *= scale
        tau_r *= scale
        tau_l *= scale
    speed = float(np.clip(speed + dt * accel, 0.0, 0.75))
    yaw_rate = float(np.clip(yaw_rate + dt * yaw_accel, -2.5, 2.5))
    heading = float(_wrap_angle(heading + dt * yaw_rate))
    position = position + dt * speed * np.array([math.cos(heading), math.sin(heading)])
    wheel_omega_r = speed / wheel_radius + half_track * yaw_rate / wheel_radius
    wheel_omega_l = speed / wheel_radius - half_track * yaw_rate / wheel_radius
    energy = dt * (abs(tau_r * wheel_omega_r) + abs(tau_l * wheel_omega_l))
    return position, heading, speed, yaw_rate, max(abs(tau_r), abs(tau_l)), saturated, float(energy)


def _dock(
    world: CargoWorld,
    members: tuple[int, ...],
    positions: np.ndarray,
    headings: np.ndarray,
    speeds: np.ndarray,
    yaw_rates: np.ndarray,
    *,
    load_pose: np.ndarray,
    offsets: np.ndarray,
    dt: float,
    horizon_s: float,
) -> tuple[bool, float, float, int, float]:
    stable = 0
    max_torque = 0.0
    saturations = 0
    energy = 0.0
    for step in range(int(horizon_s / dt)):
        targets = load_pose[:2] + offsets @ _rotation(float(load_pose[2])).T
        for slot, member in enumerate(members):
            result = _unicycle_step(
                positions[member],
                float(headings[member]),
                float(speeds[member]),
                float(yaw_rates[member]),
                targets[slot],
                torque_limit=float(world.wheel_torque_limits_nm[member]),
                dt=dt,
            )
            positions[member], headings[member], speeds[member], yaw_rates[member] = result[:4]
            max_torque = max(max_torque, float(result[4]))
            saturations += int(result[5])
            energy += float(result[6])
        errors = np.linalg.norm(positions[np.asarray(members)] - targets, axis=1)
        if bool(np.all(errors <= 0.12) and np.all(speeds[np.asarray(members)] <= 0.08)):
            stable += 1
        else:
            stable = 0
        if stable >= 5:
            return True, (step + 1) * dt, max_torque, saturations, energy
    return False, horizon_s, max_torque, saturations, energy


def _grasp_matrix(offsets: np.ndarray, theta: float) -> np.ndarray:
    rotated = offsets @ _rotation(theta).T
    matrix = np.zeros((3, 2 * len(offsets)), dtype=float)
    for index, offset in enumerate(rotated):
        matrix[:, 2 * index : 2 * index + 2] = np.array(
            [[1.0, 0.0], [0.0, 1.0], [-offset[1], offset[0]]], dtype=float
        )
    return matrix


def _allocate_wrench(
    desired: np.ndarray,
    offsets: np.ndarray,
    force_limits: np.ndarray,
    theta: float,
) -> tuple[np.ndarray, np.ndarray, int]:
    grasp = _grasp_matrix(offsets, theta)
    forces = np.linalg.lstsq(grasp, desired, rcond=None)[0]
    saturations = 0
    for _ in range(4):
        for index, limit in enumerate(force_limits):
            block = forces[2 * index : 2 * index + 2]
            norm = float(np.linalg.norm(block))
            if norm > float(limit):
                forces[2 * index : 2 * index + 2] = block * float(limit / norm)
                saturations += 1
        residual = desired - grasp @ forces
        forces += np.linalg.lstsq(grasp, residual, rcond=None)[0]
    for index, limit in enumerate(force_limits):
        block = forces[2 * index : 2 * index + 2]
        norm = float(np.linalg.norm(block))
        if norm > float(limit):
            forces[2 * index : 2 * index + 2] = block * float(limit / norm)
            saturations += 1
    return grasp @ forces, forces.reshape(len(offsets), 2), saturations


def _clearance(world: CargoWorld, q: np.ndarray) -> float:
    if world.obstacle_center is None:
        return 10.0
    compound_radius = 0.5 * math.hypot(world.load_length_m, world.load_width_m) + 0.27
    return float(np.linalg.norm(q[:2] - world.obstacle_center) - compound_radius - world.obstacle_radius_m)


def _waypoint(world: CargoWorld, q: np.ndarray, *, guard: bool) -> np.ndarray:
    if world.obstacle_center is None or not guard:
        return world.load_target_pose.copy()
    center = world.obstacle_center
    if q[0] < center[0] - 0.65:
        return np.array([center[0] - 0.45, center[1] + 1.62, 0.0])
    if q[0] < center[0] + 0.95:
        return np.array([center[0] + 1.18, center[1] + 1.62, 0.0])
    return world.load_target_pose.copy()


def _filter_velocity(world: CargoWorld, q: np.ndarray, proposed: np.ndarray) -> np.ndarray:
    if world.obstacle_center is None:
        return proposed
    delta = q[:2] - world.obstacle_center
    distance = float(np.linalg.norm(delta))
    normal = delta / max(distance, 1e-12)
    h = _clearance(world, q) - 0.08
    lower = -1.8 * h
    normal_speed = float(np.dot(normal, proposed))
    if normal_speed < lower:
        proposed = proposed + (lower - normal_speed) * normal
    return proposed


def _method_flags(method: str) -> dict[str, bool]:
    if method not in METHODS:
        raise ValueError(f"Unknown integrated Cargo method: {method}")
    return {
        "local": method not in {"perfect_information", "central_reference"},
        "spatial": method != "decoupled_local",
        "mechanical_guard": method != "no_physical_guard",
        "safety_guard": method != "no_physical_guard",
        "repair": method != "no_repair",
        "central": method == "central_reference",
    }


def simulate_method(
    world: CargoWorld,
    method: str,
    *,
    dt: float = 0.10,
    docking_horizon_s: float = 16.0,
    transport_horizon_s: float = 50.0,
) -> RunResult:
    """Run one treatment on one paired immutable world."""

    started = perf_counter()
    flags = _method_flags(method)
    active = np.ones(world.n_robots, dtype=bool)
    messages = bytes_sent = 0
    if flags["local"]:
        snapshot = _gossip_snapshot(world, active, event_seed=1701 + METHODS.index(method))
        candidates = snapshot.known_indices
        messages += snapshot.messages
        bytes_sent += snapshot.bytes_sent
    else:
        candidates = tuple(range(world.n_robots))
    if flags["central"]:
        members = _central_select(world, candidates)
    else:
        members = _greedy_select(
            world,
            candidates,
            spatial=flags["spatial"],
            mechanical_guard=flags["mechanical_guard"],
        )
    initial_members = members
    initial_certificate = _certificate(world, members)
    selection_ok = initial_certificate if flags["mechanical_guard"] else _capacity_only(world, members)

    positions = world.robot_positions.copy()
    headings = world.robot_headings.copy()
    speeds = np.zeros(world.n_robots, dtype=float)
    yaw_rates = np.zeros(world.n_robots, dtype=float)
    q = world.load_initial_pose.copy()
    velocity = np.zeros(3, dtype=float)
    phase_trace: list[str] = ["RECRUIT"]
    load_trace = [q.copy()]
    max_torque = 0.0
    torque_saturations = 0
    wheel_energy = 0.0
    mechanical_work = 0.0
    max_residual = 0.0
    allocation_saturations = allocation_steps = 0
    min_clearance = _clearance(world, q)
    recovery_time = 0.0
    failure_triggered = False
    recovery_success = not world.failure_enabled
    collision = False
    numerical_failure = False

    if not selection_ok:
        return _finalize_result(
            world, method, initial_members, members, False, False, initial_certificate,
            failure_triggered, False, collision, True, numerical_failure,
            "coalition_not_closed", 0.0, 0.0, recovery_time, q, min_clearance,
            max_residual, 0.0, max_torque, torque_saturations, mechanical_work,
            wheel_energy, messages, bytes_sent, phase_trace, load_trace, started,
        )

    offsets = _contact_offsets(world, len(members))
    phase_trace.append("DOCK")
    docked, docking_time, dock_torque, dock_saturations, dock_energy = _dock(
        world,
        members,
        positions,
        headings,
        speeds,
        yaw_rates,
        load_pose=q,
        offsets=offsets,
        dt=dt,
        horizon_s=docking_horizon_s,
    )
    max_torque = max(max_torque, dock_torque)
    torque_saturations += dock_saturations
    wheel_energy += dock_energy
    if not docked:
        return _finalize_result(
            world, method, initial_members, members, False, False, initial_certificate,
            failure_triggered, False, collision, True, numerical_failure,
            "docking_timeout", docking_time, docking_time, recovery_time, q,
            min_clearance, max_residual, 0.0, max_torque, torque_saturations,
            mechanical_work, wheel_energy, messages, bytes_sent, phase_trace,
            load_trace, started,
        )

    phase_trace.append("TRANSPORT")
    transport_elapsed = 0.0
    stable = 0
    failed_slot: int | None = None
    failed_robot: int | None = None
    mass_matrix = np.diag([world.load_mass_kg, world.load_mass_kg, world.load_inertia_kgm2])
    damping = np.diag([12.0, 12.0, 8.0])
    members_list = list(members)
    while transport_elapsed < transport_horizon_s:
        transport_elapsed += dt
        if world.failure_enabled and not failure_triggered and transport_elapsed >= world.failure_time_s:
            failed_slot = int(np.argmin(world.force_limits_n[np.asarray(members_list)]))
            failed_robot = int(members_list.pop(failed_slot))
            active[failed_robot] = False
            failure_triggered = True
            recovery_success = False
            phase_trace.append("RECOVER")
            velocity[:] = 0.0
            if not flags["repair"]:
                break
            remaining = tuple(sorted(members_list))
            reserve_mask = active.copy()
            reserve_mask[np.asarray(remaining, dtype=int)] = False
            if flags["local"]:
                snapshot = _gossip_snapshot(world, active, event_seed=2903 + METHODS.index(method))
                candidates = tuple(index for index in snapshot.known_indices if reserve_mask[index])
                messages += snapshot.messages
                bytes_sent += snapshot.bytes_sent
            else:
                candidates = tuple(int(index) for index in np.flatnonzero(reserve_mask))
            if flags["central"]:
                repaired = _central_select(world, candidates, fixed_members=remaining)
            else:
                repaired = _greedy_select(
                    world,
                    candidates,
                    spatial=flags["spatial"],
                    mechanical_guard=flags["mechanical_guard"],
                    fixed_members=remaining,
                )
            additions = [index for index in repaired if index not in remaining]
            if not additions:
                break
            replacement = int(additions[0])
            target_offset = offsets[failed_slot]
            recovery_started = transport_elapsed
            recovered = False
            for _ in range(int(16.0 / dt)):
                target_position = q[:2] + target_offset @ _rotation(float(q[2])).T
                result = _unicycle_step(
                    positions[replacement],
                    float(headings[replacement]),
                    float(speeds[replacement]),
                    float(yaw_rates[replacement]),
                    target_position,
                    torque_limit=float(world.wheel_torque_limits_nm[replacement]),
                    dt=dt,
                )
                positions[replacement], headings[replacement], speeds[replacement], yaw_rates[replacement] = result[:4]
                max_torque = max(max_torque, float(result[4]))
                torque_saturations += int(result[5])
                wheel_energy += float(result[6])
                recovery_time += dt
                if np.linalg.norm(positions[replacement] - target_position) <= 0.12 and speeds[replacement] <= 0.08:
                    recovered = True
                    break
            members_list.insert(failed_slot, replacement)
            members = tuple(sorted(members_list))
            recovery_success = bool(recovered and _certificate(world, members))
            if not recovery_success:
                break
            transport_elapsed = recovery_started + recovery_time
            phase_trace.append("TRANSPORT")

        current_members = tuple(members_list)
        if not _certificate(world, current_members):
            velocity[:] = 0.0
            if failure_triggered:
                break
        reference = _waypoint(world, q, guard=flags["safety_guard"])
        error = reference[:2] - q[:2]
        theta_error = float(_wrap_angle(reference[2] - q[2]))
        nominal = np.array(
            [4.2 * error[0] - 10.0 * velocity[0], 4.2 * error[1] - 10.0 * velocity[1], 7.0 * theta_error - 7.0 * velocity[2]],
            dtype=float,
        )
        raw_acceleration = np.linalg.solve(mass_matrix, nominal - damping @ velocity)
        proposed_velocity = velocity[:2] + dt * raw_acceleration[:2]
        if flags["safety_guard"]:
            safe_velocity = _filter_velocity(world, q, proposed_velocity.copy())
            raw_acceleration[:2] = (safe_velocity - velocity[:2]) / dt
            nominal = mass_matrix @ raw_acceleration + damping @ velocity
        member_indices = np.asarray(current_members, dtype=int)
        actual, forces, saturated = _allocate_wrench(
            nominal,
            offsets[: len(current_members)],
            world.force_limits_n[member_indices],
            float(q[2]),
        )
        allocation_saturations += int(saturated)
        allocation_steps += max(len(current_members), 1)
        max_residual = max(max_residual, float(np.linalg.norm(nominal - actual)))
        acceleration = np.linalg.solve(mass_matrix, actual - damping @ velocity)
        velocity = velocity + dt * acceleration
        velocity[:2] = np.clip(velocity[:2], -0.85, 0.85)
        velocity[2] = float(np.clip(velocity[2], -1.2, 1.2))
        q = q + dt * velocity
        q[2] = float(_wrap_angle(q[2]))
        mechanical_work += dt * max(0.0, float(np.dot(actual, velocity)))
        for slot, member in enumerate(current_members):
            positions[member] = q[:2] + offsets[slot] @ _rotation(float(q[2])).T
            headings[member] = float(q[2])
            speeds[member] = float(np.linalg.norm(velocity[:2]))
            yaw_rates[member] = float(velocity[2])
        clearance = _clearance(world, q)
        min_clearance = min(min_clearance, clearance)
        load_trace.append(q.copy())
        if not np.isfinite(q).all() or not np.isfinite(velocity).all():
            numerical_failure = True
            break
        if clearance < 0.0:
            collision = True
            break
        position_error = float(np.linalg.norm(q[:2] - world.load_target_pose[:2]))
        orientation_error = abs(float(_wrap_angle(q[2] - world.load_target_pose[2])))
        if position_error <= 0.18 and orientation_error <= 0.15 and np.linalg.norm(velocity) <= 0.16:
            stable += 1
        else:
            stable = 0
        if stable >= 5:
            phase_trace.append("DONE")
            break

    mission_success = bool(
        docked
        and not collision
        and not numerical_failure
        and stable >= 5
        and (not world.failure_enabled or recovery_success)
    )
    timeout = not mission_success and not collision and not numerical_failure
    if mission_success:
        reason = "target_reached"
    elif collision:
        reason = "collision"
    elif numerical_failure:
        reason = "numerical_failure"
    elif failure_triggered and not flags["repair"]:
        reason = "repair_disabled"
    elif failure_triggered and not recovery_success:
        reason = "recovery_failed"
    else:
        reason = "timeout"
    if not mission_success:
        phase_trace.append("FAILED")
    saturation_fraction = allocation_saturations / max(allocation_steps, 1)
    return _finalize_result(
        world, method, initial_members, tuple(sorted(members_list)), mission_success,
        docked, initial_certificate, failure_triggered, recovery_success, collision,
        timeout, numerical_failure, reason, docking_time + transport_elapsed,
        docking_time, recovery_time, q, min_clearance, max_residual,
        saturation_fraction, max_torque, torque_saturations, mechanical_work,
        wheel_energy, messages, bytes_sent, phase_trace, load_trace, started,
    )


def _finalize_result(
    world: CargoWorld,
    method: str,
    initial_members: tuple[int, ...],
    final_members: tuple[int, ...],
    mission_success: bool,
    docking_success: bool,
    initial_certificate: bool,
    failure_triggered: bool,
    recovery_success: bool,
    collision: bool,
    timeout: bool,
    numerical_failure: bool,
    reason: str,
    mission_time: float,
    docking_time: float,
    recovery_time: float,
    q: np.ndarray,
    min_clearance: float,
    max_residual: float,
    saturation_fraction: float,
    max_torque: float,
    torque_saturations: int,
    mechanical_work: float,
    wheel_energy: float,
    messages: int,
    bytes_sent: int,
    phase_trace: list[str],
    load_trace: list[np.ndarray],
    started: float,
) -> RunResult:
    return RunResult(
        world_hash=world.world_hash,
        scenario=world.scenario,
        seed=world.seed,
        n_robots=world.n_robots,
        method=method,
        selected_initial=tuple(initial_members),
        selected_final=tuple(final_members),
        mission_success=bool(mission_success),
        docking_success=bool(docking_success),
        mechanical_certificate_initial=bool(initial_certificate),
        failure_triggered=bool(failure_triggered),
        recovery_success=bool(recovery_success),
        collision=bool(collision),
        timeout=bool(timeout),
        numerical_failure=bool(numerical_failure),
        termination_reason=reason,
        mission_time_s=float(mission_time),
        docking_time_s=float(docking_time),
        recovery_time_s=float(recovery_time),
        final_position_error_m=float(np.linalg.norm(q[:2] - world.load_target_pose[:2])),
        final_orientation_error_rad=abs(float(_wrap_angle(q[2] - world.load_target_pose[2]))),
        min_clearance_m=float(min_clearance),
        max_wrench_residual_n=float(max_residual),
        saturation_fraction=float(saturation_fraction),
        max_wheel_torque_nm=float(max_torque),
        wheel_torque_saturations=int(torque_saturations),
        mechanical_work_j=float(mechanical_work),
        wheel_energy_j=float(wheel_energy),
        messages=int(messages),
        bytes_sent=int(bytes_sent),
        runtime_ms=1000.0 * (perf_counter() - started),
        phase_trace=tuple(phase_trace),
        load_trace=np.asarray(load_trace, dtype=float),
    )


def _row(result: RunResult) -> dict[str, Any]:
    row = asdict(result)
    row["selected_initial"] = ";".join(map(str, result.selected_initial))
    row["selected_final"] = ";".join(map(str, result.selected_final))
    row["phase_trace"] = ">".join(result.phase_trace)
    row.pop("load_trace")
    for key in (
        "mission_success", "docking_success", "mechanical_certificate_initial",
        "failure_triggered", "recovery_success", "collision", "timeout", "numerical_failure",
    ):
        row[key] = int(row[key])
    row["method_label"] = METHOD_LABELS[result.method]
    row["scenario_label"] = SCENARIO_LABELS[result.scenario]
    return row


def summarize(runs: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        "mission_success", "docking_success", "recovery_success", "collision",
        "timeout", "mission_time_s", "recovery_time_s", "final_position_error_m",
        "min_clearance_m", "max_wrench_residual_n", "saturation_fraction",
        "mechanical_work_j", "wheel_energy_j", "messages", "bytes_sent", "runtime_ms",
    )
    rows: list[dict[str, Any]] = []
    for method, group in runs.groupby("method", sort=False):
        row: dict[str, Any] = {"method": method, "method_label": METHOD_LABELS[str(method)], "n": len(group)}
        for metric in metrics:
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            row[f"{metric}_median"] = float(np.median(values))
            row[f"{metric}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def _paired_frame(
    runs: pd.DataFrame,
    a: str,
    b: str,
    metric: str,
    scenarios: tuple[str, ...],
) -> pd.DataFrame:
    selected = runs[runs["scenario"].isin(scenarios) & runs["method"].isin([a, b])]
    pivot = selected.pivot(index=["world_hash", "scenario", "n_robots", "seed"], columns="method", values=metric)
    pivot = pivot.dropna(subset=[a, b])
    paired = pivot.reset_index()
    paired["difference"] = paired[a] - paired[b]
    return paired


def _bootstrap_ci(values: np.ndarray, seed: int, resamples: int = 3000) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    for index in range(resamples):
        means[index] = float(np.mean(rng.choice(data, size=data.size, replace=True)))
    low, high = np.quantile(means, (0.025, 0.975))
    return float(low), float(high)


def _rank_biserial(differences: np.ndarray) -> float:
    data = np.asarray(differences, dtype=float)
    data = data[data != 0.0]
    if data.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(data))
    positive = float(np.sum(ranks[data > 0]))
    negative = float(np.sum(ranks[data < 0]))
    return (positive - negative) / max(positive + negative, 1e-12)


def evaluate_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("E2E-H1", "distributed_full", "decoupled_local", "mission_time_s", ("degraded_network",), "less"),
        ("E2E-H2", "distributed_full", "no_physical_guard", "mission_success", ("static_obstacle", "degraded_network", "failure_during_transport"), "greater"),
        ("E2E-H3", "distributed_full", "no_repair", "mission_success", ("failure_during_transport",), "greater"),
        ("E2E-H4", "distributed_full", "perfect_information", "mission_success", ("degraded_network",), "two-sided"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (identifier, a, b, metric, scenarios, alternative) in enumerate(specs):
        paired = _paired_frame(runs, a, b, metric, scenarios)
        pair_diffs = paired["difference"].to_numpy(dtype=float)
        cluster_diffs = (
            paired.groupby(["n_robots", "seed"], sort=True)["difference"]
            .mean()
            .to_numpy(dtype=float)
        )
        low, high = _bootstrap_ci(cluster_diffs, 77100 + index)
        if metric == "mission_success":
            favorable = int(np.sum(pair_diffs > 0))
            adverse = int(np.sum(pair_diffs < 0))
            if len(scenarios) == 1:
                if favorable + adverse:
                    if alternative == "greater":
                        p_value = float(stats.binomtest(favorable, favorable + adverse, 0.5, alternative="greater").pvalue)
                    else:
                        p_value = float(stats.binomtest(favorable, favorable + adverse, 0.5).pvalue)
                else:
                    p_value = 1.0
                test = "McNemar exacto"
            else:
                nonzero = cluster_diffs[np.abs(cluster_diffs) > 1e-12]
                p_value = (
                    float(stats.wilcoxon(nonzero, alternative="greater").pvalue)
                    if nonzero.size
                    else 1.0
                )
                test = "Wilcoxon sobre medias por instancia"
            effect_size = float(np.mean(cluster_diffs))
        else:
            nonzero = cluster_diffs[np.abs(cluster_diffs) > 1e-12]
            if nonzero.size:
                wilcoxon_alternative = "less" if alternative == "less" else "two-sided"
                p_value = float(stats.wilcoxon(nonzero, alternative=wilcoxon_alternative).pvalue)
            else:
                p_value = 1.0
            favorable = adverse = 0
            effect_size = _rank_biserial(cluster_diffs)
            test = "Wilcoxon por instancia"
        rows.append({
            "id": identifier,
            "method_a": a,
            "method_b": b,
            "metric": metric,
            "scenarios": ";".join(scenarios),
            "n_pairs": len(pair_diffs),
            "n_independent_instances": len(cluster_diffs),
            "effect_a_minus_b": float(np.mean(cluster_diffs)),
            "ci95_low": low,
            "ci95_high": high,
            "effect_size": effect_size,
            "effect_size_type": "diferencia de riesgos" if metric == "mission_success" else "biserial por rangos",
            "p_raw": p_value,
            "test": test,
            "favorable_discordances": favorable,
            "adverse_discordances": adverse,
        })
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p_raw"])
    running = 0.0
    for rank, index in enumerate(order):
        adjusted = min(1.0, (len(rows) - rank) * rows[index]["p_raw"])
        running = max(running, adjusted)
        rows[index]["p_holm"] = running
        rows[index]["reject_holm"] = int(running < 0.05)
    return pd.DataFrame(rows)


def build_audit(worlds: list[CargoWorld], results: list[RunResult], methods: tuple[str, ...]) -> dict[str, Any]:
    rows = pd.DataFrame([_row(result) for result in results])
    counts = rows.groupby("world_hash")["method"].nunique()
    checks = {
        "all_worlds_paired": bool((counts == len(methods)).all()),
        "world_hashes_unique": len({world.world_hash for world in worlds}) == len(worlds),
        "finite_metrics": bool(np.isfinite(rows[["mission_time_s", "final_position_error_m", "max_wrench_residual_n", "runtime_ms"]].to_numpy()).all()),
        "wheel_torque_limits": all(result.max_wheel_torque_nm <= float(np.max(world.wheel_torque_limits_nm)) + 1e-9 for world in worlds for result in results if result.world_hash == world.world_hash),
        "no_load_motion_before_docking": all(result.load_trace.shape[0] >= 1 and np.allclose(result.load_trace[0], world.load_initial_pose) for world in worlds for result in results if result.world_hash == world.world_hash),
        "failure_cases_preserved": bool(
            (
                (rows["scenario"] != "failure_during_transport")
                | (rows["failure_triggered"] == 0)
                | (rows["docking_success"] == 1)
            ).all()
        ),
        "termination_classified": set(rows["termination_reason"]).issubset({"target_reached", "collision", "numerical_failure", "repair_disabled", "recovery_failed", "timeout", "docking_timeout", "coalition_not_closed"}),
        "message_accounting_nonnegative": bool((rows[["messages", "bytes_sent"]].to_numpy() >= 0).all()),
        "global_methods_send_no_messages": bool((rows[rows["method"].isin(["perfect_information", "central_reference"])]["messages"] == 0).all()),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "worlds": len(worlds),
        "runs": len(results),
        "model_scope": "dynamic unicycle docking and replacement plus reduced-order planar rigid Cargo payload with fixed contacts",
        "information_scope": "versioned neighbor gossip with sampled bounded delay and independent packet loss; perfect/global methods declared separately",
        "not_claimed": "No global hybrid convergence, 3-D support, frictional contact, perception, middleware, hardware or pushing/caging validation.",
    }


def _write_tables(output: Path, runs: pd.DataFrame, summary: pd.DataFrame, hypotheses: pd.DataFrame) -> None:
    tables = output / "tables"
    result_lines = [
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Método & $n$ & Misión & \\shortstack{Intersección\\\\huella--obstáculo} & Tiempo [s] & Recuperación [s] & Mensajes \\\\",
        "\\midrule",
    ]
    for method in METHODS:
        row = summary[summary["method"] == method].iloc[0]
        result_lines.append(
            f"{METHOD_LABELS[method]} & {int(row['n'])} & {row['mission_success_mean']:.3f} & "
            f"{row['collision_mean']:.3f} & {row['mission_time_s_mean']:.2f} & "
            f"{row['recovery_time_s_mean']:.2f} & {row['messages_mean']:.1f} \\\\"
        )
    result_lines.extend(["\\bottomrule", "\\end{tabular}"])
    (tables / "cargo_e2e_results.tex").write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    distributed = runs[runs["method"] == "distributed_full"]
    failure = distributed[distributed["scenario"] == "failure_during_transport"]
    degraded = distributed[distributed["scenario"] == "degraded_network"]
    macros = {
        "CargoEtwoEWorlds": int(runs["world_hash"].nunique()),
        "CargoEtwoERuns": len(runs),
        "CargoEtwoESuccess": f"{distributed['mission_success'].mean():.3f}",
        "CargoEtwoEFailureSuccess": f"{failure['mission_success'].mean():.3f}",
        "CargoEtwoEDegradedSuccess": f"{degraded['mission_success'].mean():.3f}",
        "CargoEtwoEMessages": f"{distributed['messages'].mean():.1f}",
    }
    (tables / "cargo_e2e_numbers.tex").write_text(
        "\n".join(f"\\newcommand{{\\{key}}}{{{value}}}" for key, value in macros.items()) + "\n",
        encoding="utf-8",
    )
    hypothesis_lines = [
        "\\begin{tabular}{llrrrr}", "\\toprule",
        "ID & Métrica & $n$ & Efecto & IC 95\\% & $p_{Holm}$ \\\\", "\\midrule",
    ]
    for row in hypotheses.itertuples(index=False):
        hypothesis_lines.append(
            f"{row.id} & {str(row.metric).replace('_', ' ')} & {int(row.n_pairs)} & {row.effect_a_minus_b:.3f} & "
            f"[{row.ci95_low:.3f}; {row.ci95_high:.3f}] & {row.p_holm:.2e} \\\\"
        )
    hypothesis_lines.extend(["\\bottomrule", "\\end{tabular}"])
    (tables / "cargo_e2e_hypotheses.tex").write_text("\n".join(hypothesis_lines) + "\n", encoding="utf-8")


def _plot_results(output: Path, runs: pd.DataFrame, results: list[RunResult]) -> None:
    figures = output / "figures"
    matrix = runs.pivot_table(index="method", columns="scenario", values="mission_success", aggfunc="mean").reindex(index=METHODS, columns=SCENARIOS)
    fig, ax = plt.subplots(figsize=(8.7, 5.2))
    image = ax.imshow(matrix.to_numpy(), vmin=0.0, vmax=1.0, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(SCENARIOS)), [SCENARIO_LABELS[s] for s in SCENARIOS], rotation=20, ha="right")
    ax.set_yticks(range(len(METHODS)), [METHOD_LABELS[m] for m in METHODS])
    for i in range(len(METHODS)):
        for j in range(len(SCENARIOS)):
            value = float(matrix.iloc[i, j])
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="white" if value < 0.55 else "black")
    fig.colorbar(image, ax=ax, label="Tasa de misión extremo a extremo")
    fig.tight_layout()
    fig.savefig(figures / "fig-cargo-e2e-success.pdf", bbox_inches="tight")
    plt.close(fig)

    representative_world = sorted(set(runs["world_hash"]))[0]
    selected = [result for result in results if result.world_hash == representative_world]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for result in selected:
        trace = result.load_trace
        ax.plot(trace[:, 0], trace[:, 1], label=METHOD_LABELS[result.method], linewidth=1.5)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.22)
    ax.legend(fontsize=7, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(figures / "fig-cargo-e2e-trajectories.pdf", bbox_inches="tight")
    plt.close(fig)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unavailable"


def _freeze_protocol(config_path: Path, config: dict[str, Any], output: Path) -> dict[str, Any]:
    protocol = output / "protocol"
    protocol.mkdir(parents=True, exist_ok=True)
    frozen = protocol / "frozen_protocol.yaml"
    manifest_path = protocol / "freeze_manifest.json"
    pilot_audit = Path(str(config["pilot_evidence"])) / "audit.json"
    if not pilot_audit.exists() or json.loads(pilot_audit.read_text(encoding="utf-8")).get("status") != "passed":
        raise RuntimeError("The confirmatory Cargo campaign requires a passed pilot audit.")
    candidate = yaml.safe_dump(config, sort_keys=False)
    if frozen.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if _sha256(frozen) != existing.get("config_sha256") or frozen.read_text(encoding="utf-8") != candidate:
            raise RuntimeError("Frozen Cargo protocol mismatch; use a new experiment identifier.")
        return existing
    frozen.write_text(candidate, encoding="utf-8")
    seed_spec = dict(config["seeds"])
    (protocol / "seed_registry.yaml").write_text(
        yaml.safe_dump(
            {
                "pilot_seed_range": [9600, 9602],
                "confirmatory_seed_range": [
                    int(seed_spec["start"]),
                    int(seed_spec["start"]) + int(seed_spec["count"]) - 1,
                ],
                "disjoint": int(seed_spec["start"]) > 9602,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest = {
        "status": "frozen_before_execution",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_sha256": _sha256(frozen),
        "pilot_audit_sha256": _sha256(pilot_audit),
        "seed_registry_sha256": _sha256(protocol / "seed_registry.yaml"),
        "source_config": str(config_path),
        "git_sha_at_freeze": _git_sha(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def run_config(config_path: str | Path) -> dict[str, Any]:
    """Run a smoke or frozen confirmatory campaign and generate all artifacts."""

    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if str(config.get("protocol_family")) != "cargo_e2e_v1":
        raise ValueError("Only protocol_family=cargo_e2e_v1 is supported.")
    output = Path(str(config["output_dir"]))
    for child in ("tables", "figures", "traces", "protocol"):
        (output / child).mkdir(parents=True, exist_ok=True)
    mode = str(config.get("mode", "smoke"))
    freeze = _freeze_protocol(path, config, output) if mode == "confirmatory" else None
    scenarios = tuple(str(value) for value in config.get("scenarios", SCENARIOS))
    counts = tuple(int(value) for value in config.get("robot_counts", [4, 8, 12]))
    methods = tuple(str(value) for value in config.get("methods", METHODS))
    if methods != METHODS:
        raise ValueError(f"Canonical method order is {METHODS}")
    seeds_spec = config["seeds"]
    seeds = tuple(range(int(seeds_spec["start"]), int(seeds_spec["start"]) + int(seeds_spec["count"])))
    simulation = dict(config.get("simulation", {}))
    worlds = [build_world(scenario, seed, count) for scenario in scenarios for count in counts for seed in seeds]
    results: list[RunResult] = []
    for world in worlds:
        for method in methods:
            results.append(
                simulate_method(
                    world,
                    method,
                    dt=float(simulation.get("dt_s", 0.10)),
                    docking_horizon_s=float(simulation.get("docking_horizon_s", 16.0)),
                    transport_horizon_s=float(simulation.get("transport_horizon_s", 50.0)),
                )
            )
    runs = pd.DataFrame([_row(result) for result in results])
    summary = summarize(runs)
    hypotheses = evaluate_hypotheses(runs)
    audit = build_audit(worlds, results, methods)
    runs.to_csv(output / "tables" / "runs.csv", index=False)
    summary.to_csv(output / "tables" / "summary.csv", index=False)
    hypotheses.to_csv(output / "tables" / "hypotheses.csv", index=False)
    _write_tables(output, runs, summary, hypotheses)
    _plot_results(output, runs, results)
    representative = results[0]
    np.savez_compressed(output / "traces" / "representative_trace.npz", load_pose=representative.load_trace)
    (output / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    report = [
        f"# {config['experiment_id']}", "",
        f"- Worlds: `{len(worlds)}`", f"- Runs: `{len(results)}`",
        f"- Audit: `{audit['status']}`", "", "## Scope", "", audit["not_claimed"],
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    artifacts = sorted(file for file in output.rglob("*") if file.is_file() and file.name != "manifest.json")
    manifest = {
        "experiment_id": str(config["experiment_id"]),
        "protocol_family": "cargo_e2e_v1",
        "mode": mode,
        "status": "complete" if audit["status"] == "passed" else "failed_audit",
        "worlds": len(worlds),
        "runs": len(results),
        "methods": list(methods),
        "scenarios": list(scenarios),
        "robot_counts": list(counts),
        "seeds": list(seeds),
        "freeze": freeze,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "git_sha": _git_sha(),
        "artifacts": {str(file.relative_to(output)).replace("\\", "/"): _sha256(file) for file in artifacts},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if audit["status"] != "passed":
        raise RuntimeError(f"Integrated Cargo audit failed: {audit['checks']}")
    return manifest


__all__ = [
    "METHODS", "CargoWorld", "RunResult", "build_audit", "build_world",
    "evaluate_hypotheses", "run_config", "simulate_method", "summarize",
]
