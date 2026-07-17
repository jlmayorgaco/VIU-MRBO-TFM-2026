"""Auditable SP5 cooperative payload transport protocol.

This module is intentionally separate from the historical SP5 implementation.
The historical simulator projected payload and robot poses back to collision-free
space after integration.  Here RAW wrench, SAFE wrench and physically realised
EXEC wrench are distinct objects and positions are never repaired.

The plant is a reduced-order planar rigid payload with bounded planar contact
forces.  SP5 starts after SP4: contact locations are fixed in the payload frame
and the corresponding robot centres are kinematic points of the compound body.
This is not a frictional contact or hardware model.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.stats import binomtest, wilcoxon

from viu_mrob_tfm.sp5.scenario import (
    SP5Problem,
    SP5TransportScenario,
    scenario_params_for_generator,
)


SCENARIO_GENERATORS = {
    "open_nominal": "monte_carlo",
    "static_corridor": "cargo_overhead_delivery",
    "mobile_crossing": "multi_group_crossing_push",
    "mixed_corridor": "formation_corridor_push",
    "actuator_limited": "overactuated_push_drag",
    "multi_load_clutter": "scarce_cargo_multi_load",
}

METHOD_LABELS = {
    "pose_pd_raw": "Pose PD (RAW)",
    "apf_wrench_heuristic": "APF wrench heuristic",
    "velocity_obstacle_proxy": "Velocity-obstacle proxy",
    "cbf_wrench_local": "Local CBF wrench filter",
    "damped_hamiltonian_raw": "Damped Hamiltonian (RAW)",
    "damped_hamiltonian_cbf": "Damped Hamiltonian + CBF",
    "distributed_preview_cbf": "Distributed preview-CBF",
    "centralized_preview_reference": "Centralized preview reference",
}

GUARDED_METHODS = {
    "cbf_wrench_local",
    "damped_hamiltonian_cbf",
    "distributed_preview_cbf",
    "centralized_preview_reference",
}

HAMILTONIAN_METHODS = {"damped_hamiltonian_raw", "damped_hamiltonian_cbf"}


@dataclass(frozen=True, slots=True)
class TransportWorld:
    """One fixed post-docking payload world shared by every method."""

    scenario: str
    seed: int
    n_robots: int
    problem: SP5Problem
    contact_offsets_body: np.ndarray
    robot_offsets_body: np.ndarray
    force_limits_n: np.ndarray
    mass_matrix: np.ndarray
    damping_matrix: np.ndarray
    world_hash: str

    @property
    def q0(self) -> np.ndarray:
        return self.problem.task.initial_pose.copy()

    @property
    def target(self) -> np.ndarray:
        return self.problem.task.target_pose.copy()


@dataclass(frozen=True, slots=True)
class ControllerSpec:
    kp_xy: float
    kd_xy: float
    kp_theta: float
    kd_theta: float
    apf_gain: float = 0.0
    vo_gain: float = 0.0
    barrier: bool = False
    sensor_radius_m: float = float("inf")
    preview_s: float = 0.0
    damping_injection: float = 0.0
    centralized: bool = False


@dataclass(frozen=True, slots=True)
class PayloadRunResult:
    method: str
    scenario: str
    seed: int
    n_robots: int
    world_hash: str
    time_s: np.ndarray
    load_pose: np.ndarray
    load_velocity: np.ndarray
    robot_positions: np.ndarray
    raw_wrench: np.ndarray
    safe_wrench: np.ndarray
    exec_wrench: np.ndarray
    contact_forces: np.ndarray
    hamiltonian: np.ndarray
    raw_barrier_residual: np.ndarray
    safe_barrier_residual: np.ndarray
    exec_barrier_residual: np.ndarray
    mechanics_residual: np.ndarray
    target_reached: bool
    safe_transport_success: bool
    any_collision: bool
    timeout: bool
    numerical_failure: bool
    termination_reason: str
    time_to_target_s: float
    final_position_error_m: float
    final_orientation_error_rad: float
    min_clearance_m: float
    raw_barrier_violation_rate: float
    safe_barrier_violation_rate: float
    exec_barrier_violation_rate: float
    guard_intervention_norm: float
    wrench_realization_rmse: float
    saturation_fraction: float
    positive_hamiltonian_delta_rate: float
    mechanical_work_j: float
    force_effort_n2s: float
    messages: int
    runtime_wall_s: float
    positions_repaired_after_integration: bool = False


def _controller(method: str) -> ControllerSpec:
    if method not in METHOD_LABELS:
        raise ValueError(f"Unknown SP5 v2 method: {method}")
    if method == "pose_pd_raw":
        return ControllerSpec(3.0, 12.0, 8.0, 10.0)
    if method == "apf_wrench_heuristic":
        return ControllerSpec(3.0, 12.0, 8.0, 10.0, apf_gain=15.0, sensor_radius_m=5.0)
    if method == "velocity_obstacle_proxy":
        return ControllerSpec(3.0, 12.0, 8.0, 10.0, vo_gain=15.0, sensor_radius_m=5.5, preview_s=1.2)
    if method == "cbf_wrench_local":
        return ControllerSpec(3.0, 12.0, 8.0, 10.0, barrier=True, sensor_radius_m=5.0)
    if method == "damped_hamiltonian_raw":
        return ControllerSpec(3.2, 10.0, 10.0, 8.0, damping_injection=6.0)
    if method == "damped_hamiltonian_cbf":
        return ControllerSpec(3.2, 10.0, 10.0, 8.0, barrier=True, sensor_radius_m=5.5, damping_injection=6.0)
    if method == "distributed_preview_cbf":
        return ControllerSpec(3.0, 12.0, 9.0, 10.0, barrier=True, sensor_radius_m=6.0, preview_s=0.8, damping_injection=3.0)
    return ControllerSpec(3.0, 13.0, 9.0, 11.0, barrier=True, preview_s=1.8, damping_injection=3.0, centralized=True)


def _rotation(theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float | np.ndarray) -> float | np.ndarray:
    return (np.asarray(value) + np.pi) % (2.0 * np.pi) - np.pi


def _contact_geometry(length_m: float, width_m: float, n: int, robot_radius_m: float) -> tuple[np.ndarray, np.ndarray]:
    """Evenly place contact points and robot centres around a rectangle."""

    perimeter = 2.0 * (length_m + width_m)
    samples = (np.arange(n, dtype=float) + 0.5) * perimeter / float(n)
    contacts = np.zeros((n, 2), dtype=float)
    directions = np.zeros((n, 2), dtype=float)
    for index, value in enumerate(samples):
        if value < length_m:
            contacts[index] = [-0.5 * length_m + value, 0.5 * width_m]
            directions[index] = [0.0, 1.0]
        elif value < length_m + width_m:
            offset = value - length_m
            contacts[index] = [0.5 * length_m, 0.5 * width_m - offset]
            directions[index] = [1.0, 0.0]
        elif value < 2.0 * length_m + width_m:
            offset = value - length_m - width_m
            contacts[index] = [0.5 * length_m - offset, -0.5 * width_m]
            directions[index] = [0.0, -1.0]
        else:
            offset = value - 2.0 * length_m - width_m
            contacts[index] = [-0.5 * length_m, -0.5 * width_m + offset]
            directions[index] = [-1.0, 0.0]
    centres = contacts + directions * (robot_radius_m + 0.035)
    return contacts, centres


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _world_hash(problem: SP5Problem, scenario: str, seed: int, n: int, contacts: np.ndarray, limits: np.ndarray) -> str:
    payload = {
        "scenario": scenario,
        "seed": seed,
        "n_robots": n,
        "q0": problem.task.initial_pose.tolist(),
        "target": problem.task.target_pose.tolist(),
        "contacts": np.round(contacts, 12).tolist(),
        "force_limits": np.round(limits, 12).tolist(),
        "obstacles": [
            [f"obstacle-{index:02d}", *np.round(ob.center, 12).tolist(), float(ob.radius)]
            for index, ob in enumerate(problem.world.map.obstacles)
        ],
        "mobile": [
            [group.identifier, *np.round(group.start_xy, 12).tolist(), *np.round(group.end_xy, 12).tolist(), group.radius_m]
            for group in problem.mobile_groups
        ],
    }
    return _sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))


def build_transport_world(scenario: str, seed: int, n_robots: int) -> TransportWorld:
    """Build a deterministic SP5 world without inspecting method outputs."""

    if scenario not in SCENARIO_GENERATORS:
        raise ValueError(f"Unknown SP5 v2 scenario: {scenario}")
    if n_robots not in {4, 8, 12}:
        raise ValueError("SP5 v2 preregisters N in {4, 8, 12}.")
    generator = SCENARIO_GENERATORS[scenario]
    base = scenario_params_for_generator(generator)[0]
    params = replace(
        base,
        n_robots=n_robots,
        transport_mode="cargo",
        horizon_s=45.0,
        pickup_horizon_s=0.1,
        dt_s=0.15,
    )
    problem = SP5TransportScenario(params).build(seed=seed)
    load = problem.world.loads[problem.task.load_index]
    contacts, robot_centres = _contact_geometry(
        float(load.length_m), float(load.width_m), n_robots, float(problem.robot_radius_m)
    )
    limits = np.asarray(
        [float(robot.spec.capacity.force_limit_n) for robot in problem.world.robots],
        dtype=float,
    )
    if scenario == "actuator_limited":
        limits = limits * np.linspace(0.42, 0.72, n_robots)
    mass = float(load.mass_kg) * (1.25 if scenario == "actuator_limited" else 1.0)
    inertia = mass * (float(load.length_m) ** 2 + float(load.width_m) ** 2) / 12.0
    mass_matrix = np.diag([mass, mass, inertia])
    damping_matrix = np.diag([15.0, 15.0, 13.0])
    return TransportWorld(
        scenario=scenario,
        seed=int(seed),
        n_robots=int(n_robots),
        problem=problem,
        contact_offsets_body=contacts,
        robot_offsets_body=robot_centres,
        force_limits_n=limits,
        mass_matrix=mass_matrix,
        damping_matrix=damping_matrix,
        world_hash=_world_hash(problem, scenario, seed, n_robots, contacts, limits),
    )


def _body_points(q: np.ndarray, offsets: np.ndarray) -> np.ndarray:
    return q[:2] + offsets @ _rotation(float(q[2])).T


def _compound_radius(world: TransportWorld) -> float:
    """Conservative radius covering payload and docked robot disks."""

    return float(np.max(np.linalg.norm(world.robot_offsets_body, axis=1)) + world.problem.robot_radius_m)


def _external_wrench(world: TransportWorld, t_s: float) -> np.ndarray:
    if world.scenario != "actuator_limited" or not (13.0 <= t_s < 16.0):
        return np.zeros(3, dtype=float)
    sign = -1.0 if world.seed % 2 else 1.0
    return np.array([0.0, sign * 32.0, sign * 8.0], dtype=float)


def _obstacle_states(world: TransportWorld, t_s: float, preview_s: float, sensor_radius: float, q: np.ndarray) -> list[tuple[np.ndarray, np.ndarray, float]]:
    states: list[tuple[np.ndarray, np.ndarray, float]] = []
    problem = world.problem
    for obstacle in problem.world.map.obstacles:
        center = np.asarray(obstacle.center, dtype=float)
        if np.linalg.norm(center - q[:2]) <= sensor_radius:
            states.append((center, np.zeros(2), float(obstacle.radius)))
    for group in problem.mobile_groups:
        now = group.center_at(t_s, problem.horizon_s)
        future = group.center_at(t_s + max(preview_s, problem.dt_s), problem.horizon_s)
        velocity = (future - now) / max(preview_s, problem.dt_s)
        center = now + preview_s * velocity
        if np.linalg.norm(center - q[:2]) <= sensor_radius:
            states.append((center, velocity, float(group.radius_m)))
    for index, other in enumerate(problem.world.loads):
        if index == problem.task.load_index:
            continue
        center = np.asarray(other.pickup, dtype=float)
        radius = 0.5 * float(np.hypot(other.length_m, other.width_m))
        if np.linalg.norm(center - q[:2]) <= sensor_radius:
            states.append((center, np.zeros(2), radius))
    return states


def _nominal_wrench(world: TransportWorld, spec: ControllerSpec, q: np.ndarray, velocity: np.ndarray, t_s: float) -> np.ndarray:
    error = world.target[:2] - q[:2]
    theta_error = float(_wrap_angle(world.target[2] - q[2]))
    force = spec.kp_xy * error - (spec.kd_xy + spec.damping_injection) * velocity[:2]
    torque = spec.kp_theta * theta_error - (spec.kd_theta + spec.damping_injection) * float(velocity[2])
    body_radius = _compound_radius(world)
    states = _obstacle_states(world, t_s, spec.preview_s, spec.sensor_radius_m, q)
    for center, obstacle_velocity, radius in states:
        delta = q[:2] - center
        distance = float(np.linalg.norm(delta))
        if distance <= 1e-9:
            delta = np.array([1.0, 0.0])
            distance = 1.0
        normal = delta / distance
        clearance = distance - body_radius - radius - world.problem.safety_margin_m
        if spec.apf_gain > 0.0 and clearance < 2.5:
            pressure = max(0.0, 1.0 / max(clearance + 0.18, 0.18) - 1.0 / 2.68)
            force += spec.apf_gain * pressure * normal
        if spec.vo_gain > 0.0:
            relative = velocity[:2] - obstacle_velocity
            closing = -float(np.dot(relative, normal))
            time_to_contact = clearance / max(closing, 1e-6) if closing > 0.0 else float("inf")
            if time_to_contact < max(spec.preview_s, 0.1):
                tangent = np.array([-normal[1], normal[0]])
                if float(np.dot(tangent, error)) < 0.0:
                    tangent = -tangent
                force += spec.vo_gain * (1.0 - time_to_contact / max(spec.preview_s, 0.1)) * (normal + 0.7 * tangent)
    return np.array([force[0], force[1], torque], dtype=float)


def _barrier_constraints(world: TransportWorld, spec: ControllerSpec, q: np.ndarray, t_s: float) -> list[tuple[np.ndarray, float, float]]:
    body_radius = _compound_radius(world)
    constraints: list[tuple[np.ndarray, float, float]] = []
    for center, obstacle_velocity, radius in _obstacle_states(world, t_s, spec.preview_s, spec.sensor_radius_m, q):
        delta = q[:2] - center
        distance = float(np.linalg.norm(delta))
        normal = delta / max(distance, 1e-9)
        if distance <= 1e-9:
            normal = np.array([1.0, 0.0])
        h = distance - body_radius - radius - world.problem.safety_margin_m
        constraints.append((normal, float(np.dot(normal, obstacle_velocity)), h))
    half = 0.5 * float(world.problem.world.map.size_m) - body_radius - world.problem.safety_margin_m
    constraints.extend(
        [
            (np.array([1.0, 0.0]), 0.0, half + q[0]),
            (np.array([-1.0, 0.0]), 0.0, half - q[0]),
            (np.array([0.0, 1.0]), 0.0, half + q[1]),
            (np.array([0.0, -1.0]), 0.0, half - q[1]),
        ]
    )
    return constraints


def _barrier_residual(constraints: Iterable[tuple[np.ndarray, float, float]], velocity: np.ndarray, gamma: float = 1.6) -> float:
    values = [rhs - float(np.dot(normal, velocity)) - gamma * h for normal, rhs, h in constraints]
    return max([0.0, *values])


def filtered_acceleration_from_velocity(
    current_velocity: np.ndarray,
    filtered_translational_velocity: np.ndarray,
    nominal_acceleration: np.ndarray,
    dt_s: float,
    max_translational_accel_mps2: float | None = None,
) -> np.ndarray:
    """Map the 2-D filtered velocity back to a planar acceleration.

    The translational channel is a finite difference over the controller
    sample.  The angular channel remains nominal because the SP5 barrier is
    translational.  An optional norm bound implements ``sat_A``; the archived
    campaign used ``None`` and relied on the subsequent contact-force
    allocation for physical saturation.
    """

    velocity = np.asarray(current_velocity, dtype=float)
    filtered = np.asarray(filtered_translational_velocity, dtype=float)
    nominal = np.asarray(nominal_acceleration, dtype=float)
    if velocity.shape != (3,) or filtered.shape != (2,) or nominal.shape != (3,):
        raise ValueError("planar velocity/acceleration shapes must be (3,), (2,), (3,)")
    if not np.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("dt_s must be finite and positive")
    if not np.isfinite(velocity).all() or not np.isfinite(filtered).all() or not np.isfinite(nominal).all():
        raise ValueError("velocity and acceleration inputs must be finite")
    acceleration = nominal.copy()
    acceleration[:2] = (filtered - velocity[:2]) / float(dt_s)
    if max_translational_accel_mps2 is not None:
        limit = float(max_translational_accel_mps2)
        if not np.isfinite(limit) or limit <= 0.0:
            raise ValueError("max_translational_accel_mps2 must be finite and positive")
        norm = float(np.linalg.norm(acceleration[:2]))
        if norm > limit:
            acceleration[:2] *= limit / norm
    return acceleration


def _safety_filter(world: TransportWorld, spec: ControllerSpec, q: np.ndarray, velocity: np.ndarray, raw: np.ndarray, t_s: float) -> tuple[np.ndarray, float, float, float]:
    constraints = _barrier_constraints(world, spec, q, t_s)
    raw_accel = np.linalg.solve(world.mass_matrix, raw - world.damping_matrix @ velocity)
    proposed = velocity[:2] + world.problem.dt_s * raw_accel[:2]
    raw_residual = _barrier_residual(constraints, proposed)
    if not spec.barrier:
        return raw.copy(), raw_residual, raw_residual, 0.0
    safe_velocity = proposed.copy()
    gamma = 1.6
    for _ in range(12):
        changed = False
        for normal, rhs, h in constraints:
            deficit = rhs - float(np.dot(normal, safe_velocity)) - gamma * h
            if deficit > 0.0:
                safe_velocity += deficit * normal / max(float(np.dot(normal, normal)), 1e-12)
                changed = True
        if not changed:
            break
    safe_accel = filtered_acceleration_from_velocity(
        current_velocity=velocity,
        filtered_translational_velocity=safe_velocity,
        nominal_acceleration=raw_accel,
        dt_s=world.problem.dt_s,
    )
    safe = world.mass_matrix @ safe_accel + world.damping_matrix @ velocity
    safe_residual = _barrier_residual(constraints, safe_velocity)
    return safe, raw_residual, safe_residual, float(np.linalg.norm(safe - raw))


def _grasp_matrix(world: TransportWorld, q: np.ndarray) -> np.ndarray:
    offsets = world.contact_offsets_body @ _rotation(float(q[2])).T
    matrix = np.zeros((3, 2 * world.n_robots), dtype=float)
    for i, offset in enumerate(offsets):
        matrix[:, 2 * i : 2 * i + 2] = np.array(
            [[1.0, 0.0], [0.0, 1.0], [-offset[1], offset[0]]], dtype=float
        )
    return matrix


def _allocate_wrench(world: TransportWorld, q: np.ndarray, desired: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    grasp = _grasp_matrix(world, q)
    scale = np.diag([1.0 / 250.0, 1.0 / 250.0, 1.0 / 160.0])
    scaled = scale @ grasp
    forces = np.linalg.lstsq(scaled, scale @ desired, rcond=None)[0]
    saturated = 0
    for _ in range(4):
        for i, limit in enumerate(world.force_limits_n):
            value = forces[2 * i : 2 * i + 2]
            norm = float(np.linalg.norm(value))
            if norm > limit:
                forces[2 * i : 2 * i + 2] = value * float(limit / norm)
                saturated += 1
        residual = desired - grasp @ forces
        correction = np.linalg.lstsq(scaled, scale @ residual, rcond=None)[0]
        forces += correction
    for i, limit in enumerate(world.force_limits_n):
        value = forces[2 * i : 2 * i + 2]
        norm = float(np.linalg.norm(value))
        if norm > limit:
            forces[2 * i : 2 * i + 2] = value * float(limit / norm)
            saturated += 1
    return grasp @ forces, forces.reshape(world.n_robots, 2), saturated


def _payload_circle_clearance(q: np.ndarray, length: float, width: float, center: np.ndarray, radius: float) -> float:
    local = _rotation(float(q[2])).T @ (np.asarray(center, dtype=float) - q[:2])
    outside = np.maximum(np.abs(local) - np.array([0.5 * length, 0.5 * width]), 0.0)
    return float(np.linalg.norm(outside) - radius)


def _support_radius(q: np.ndarray, length: float, width: float, normal: np.ndarray) -> float:
    rotation = _rotation(float(q[2]))
    return 0.5 * length * abs(float(np.dot(normal, rotation[:, 0]))) + 0.5 * width * abs(float(np.dot(normal, rotation[:, 1])))


def _clearance(world: TransportWorld, q: np.ndarray, t_s: float) -> float:
    problem = world.problem
    load = problem.world.loads[problem.task.load_index]
    values: list[float] = []
    for obstacle in problem.world.map.obstacles:
        values.append(_payload_circle_clearance(q, load.length_m, load.width_m, obstacle.center, obstacle.radius))
    for group in problem.mobile_groups:
        values.append(_payload_circle_clearance(q, load.length_m, load.width_m, group.center_at(t_s, problem.horizon_s), group.radius_m))
    for index, other in enumerate(problem.world.loads):
        if index == problem.task.load_index:
            continue
        other_q = np.array([other.pickup[0], other.pickup[1], 0.0], dtype=float)
        delta = q[:2] - other_q[:2]
        distance = float(np.linalg.norm(delta))
        normal = delta / max(distance, 1e-9)
        values.append(distance - _support_radius(q, load.length_m, load.width_m, normal) - _support_radius(other_q, other.length_m, other.width_m, -normal))
    robots = _body_points(q, world.robot_offsets_body)
    for position in robots:
        for obstacle in problem.world.map.obstacles:
            values.append(float(np.linalg.norm(position - obstacle.center) - obstacle.radius - problem.robot_radius_m))
        for group in problem.mobile_groups:
            values.append(float(np.linalg.norm(position - group.center_at(t_s, problem.horizon_s)) - group.radius_m - problem.robot_radius_m))
    for i in range(len(robots)):
        for j in range(i + 1, len(robots)):
            values.append(float(np.linalg.norm(robots[i] - robots[j]) - 2.0 * problem.robot_radius_m))
    return float(min(values)) if values else float("inf")


def _hamiltonian(world: TransportWorld, spec: ControllerSpec, q: np.ndarray, velocity: np.ndarray) -> float:
    error = world.target[:2] - q[:2]
    theta_error = float(_wrap_angle(world.target[2] - q[2]))
    kinetic = 0.5 * float(velocity @ world.mass_matrix @ velocity)
    potential = 0.5 * spec.kp_xy * float(error @ error) + 0.5 * spec.kp_theta * theta_error**2
    return kinetic + potential


def simulate_payload_transport(
    world: TransportWorld,
    method: str,
    *,
    dt_s: float = 0.15,
    horizon_s: float = 45.0,
    stable_steps: int = 5,
) -> PayloadRunResult:
    """Simulate one fixed world with no post-integration position repair."""

    spec = _controller(method)
    start = time.perf_counter()
    max_steps = int(math.ceil(horizon_s / dt_s))
    q = world.q0
    velocity = np.zeros(3, dtype=float)
    poses = [q.copy()]
    velocities = [velocity.copy()]
    robots = [_body_points(q, world.robot_offsets_body)]
    raw_trace: list[np.ndarray] = []
    safe_trace: list[np.ndarray] = []
    exec_trace: list[np.ndarray] = []
    force_trace: list[np.ndarray] = []
    h_trace = [_hamiltonian(world, spec, q, velocity)]
    raw_residuals: list[float] = []
    safe_residuals: list[float] = []
    exec_residuals: list[float] = []
    mechanics_residuals: list[float] = []
    min_clearance = _clearance(world, q, 0.0)
    any_collision = min_clearance < 0.0
    numerical_failure = False
    target_stable = 0
    time_to_target = math.nan
    intervention_norm = 0.0
    saturation_events = 0
    mechanical_work = 0.0
    force_effort = 0.0
    messages = 0
    reason = "initial_collision" if any_collision else "timeout"

    for step in range(max_steps):
        if any_collision:
            break
        t_s = step * dt_s
        raw = _nominal_wrench(world, spec, q, velocity, t_s)
        safe, raw_residual, safe_residual, intervention = _safety_filter(world, spec, q, velocity, raw, t_s)
        executed, contact_forces, saturated = _allocate_wrench(world, q, safe)
        disturbance = _external_wrench(world, t_s)
        acceleration = np.linalg.solve(
            world.mass_matrix,
            executed + disturbance - world.damping_matrix @ velocity,
        )
        next_velocity = velocity + dt_s * acceleration
        next_q = q + dt_s * next_velocity
        next_q[2] = float(_wrap_angle(next_q[2]))

        mechanics = world.mass_matrix @ ((next_velocity - velocity) / dt_s) + world.damping_matrix @ velocity - executed - disturbance
        constraints = _barrier_constraints(world, spec, q, t_s)
        exec_residual = _barrier_residual(constraints, next_velocity[:2])
        clearance = min(
            _clearance(world, q + 0.5 * dt_s * next_velocity, t_s + 0.5 * dt_s),
            _clearance(world, next_q, t_s + dt_s),
        )

        raw_trace.append(raw)
        safe_trace.append(safe)
        exec_trace.append(executed)
        force_trace.append(contact_forces)
        raw_residuals.append(raw_residual)
        safe_residuals.append(safe_residual)
        exec_residuals.append(exec_residual)
        mechanics_residuals.append(float(np.linalg.norm(mechanics)))
        intervention_norm += intervention
        saturation_events += saturated
        mechanical_work += max(0.0, float(np.dot(executed, velocity))) * dt_s
        force_effort += float(np.sum(contact_forces**2)) * dt_s
        messages += (world.n_robots * max(world.n_robots - 1, 0)) if spec.centralized else (2 * world.n_robots if method in GUARDED_METHODS else 0)

        q = next_q
        velocity = next_velocity
        poses.append(q.copy())
        velocities.append(velocity.copy())
        robots.append(_body_points(q, world.robot_offsets_body))
        h_trace.append(_hamiltonian(world, spec, q, velocity))
        min_clearance = min(min_clearance, clearance)
        any_collision = any_collision or clearance < 0.0
        if any_collision:
            reason = "collision"
            break
        if not np.isfinite(q).all() or not np.isfinite(velocity).all():
            numerical_failure = True
            reason = "numerical_failure"
            break
        position_error = float(np.linalg.norm(world.target[:2] - q[:2]))
        orientation_error = abs(float(_wrap_angle(world.target[2] - q[2])))
        if position_error <= 0.30 and orientation_error <= math.radians(8.0) and np.linalg.norm(velocity) <= 0.18:
            target_stable += 1
        else:
            target_stable = 0
        if target_stable >= stable_steps:
            time_to_target = (step + 1) * dt_s
            reason = "target_reached"
            break

    pose_array = np.asarray(poses, dtype=float)
    velocity_array = np.asarray(velocities, dtype=float)
    raw_array = np.asarray(raw_trace, dtype=float).reshape(-1, 3)
    safe_array = np.asarray(safe_trace, dtype=float).reshape(-1, 3)
    exec_array = np.asarray(exec_trace, dtype=float).reshape(-1, 3)
    force_array = np.asarray(force_trace, dtype=float).reshape(-1, world.n_robots, 2)
    h_array = np.asarray(h_trace, dtype=float)
    raw_residual_array = np.asarray(raw_residuals, dtype=float)
    safe_residual_array = np.asarray(safe_residuals, dtype=float)
    exec_residual_array = np.asarray(exec_residuals, dtype=float)
    mechanics_array = np.asarray(mechanics_residuals, dtype=float)
    target_reached = reason == "target_reached"
    timeout = reason == "timeout"
    positive_h = np.diff(h_array) > 1e-7
    wrench_error = safe_array - exec_array
    steps = max(len(raw_array), 1)
    return PayloadRunResult(
        method=method,
        scenario=world.scenario,
        seed=world.seed,
        n_robots=world.n_robots,
        world_hash=world.world_hash,
        time_s=np.arange(len(pose_array), dtype=float) * dt_s,
        load_pose=pose_array,
        load_velocity=velocity_array,
        robot_positions=np.asarray(robots, dtype=float),
        raw_wrench=raw_array,
        safe_wrench=safe_array,
        exec_wrench=exec_array,
        contact_forces=force_array,
        hamiltonian=h_array,
        raw_barrier_residual=raw_residual_array,
        safe_barrier_residual=safe_residual_array,
        exec_barrier_residual=exec_residual_array,
        mechanics_residual=mechanics_array,
        target_reached=target_reached,
        safe_transport_success=bool(target_reached and not any_collision and not numerical_failure),
        any_collision=bool(any_collision),
        timeout=bool(timeout),
        numerical_failure=bool(numerical_failure),
        termination_reason=reason,
        time_to_target_s=float(time_to_target) if target_reached else float(horizon_s),
        final_position_error_m=float(np.linalg.norm(world.target[:2] - pose_array[-1, :2])),
        final_orientation_error_rad=abs(float(_wrap_angle(world.target[2] - pose_array[-1, 2]))),
        min_clearance_m=float(min_clearance),
        raw_barrier_violation_rate=float(np.mean(raw_residual_array > 1e-7)) if raw_residual_array.size else 0.0,
        safe_barrier_violation_rate=float(np.mean(safe_residual_array > 1e-7)) if safe_residual_array.size else 0.0,
        exec_barrier_violation_rate=float(np.mean(exec_residual_array > 1e-7)) if exec_residual_array.size else 0.0,
        guard_intervention_norm=float(intervention_norm),
        wrench_realization_rmse=float(np.sqrt(np.mean(wrench_error**2))) if wrench_error.size else 0.0,
        saturation_fraction=float(min(1.0, saturation_events / max(steps * world.n_robots * 5, 1))),
        positive_hamiltonian_delta_rate=float(np.mean(positive_h)) if positive_h.size else 0.0,
        mechanical_work_j=float(mechanical_work),
        force_effort_n2s=float(force_effort),
        messages=int(messages),
        runtime_wall_s=float(time.perf_counter() - start),
    )


def _run_row(result: PayloadRunResult) -> dict[str, Any]:
    return {
        "method": result.method,
        "method_label": METHOD_LABELS[result.method],
        "scenario": result.scenario,
        "seed": result.seed,
        "n_robots": result.n_robots,
        "world_hash": result.world_hash,
        "target_reached": int(result.target_reached),
        "safe_transport_success": int(result.safe_transport_success),
        "any_collision": int(result.any_collision),
        "timeout": int(result.timeout),
        "numerical_failure": int(result.numerical_failure),
        "termination_reason": result.termination_reason,
        "time_to_target_s": result.time_to_target_s,
        "final_position_error_m": result.final_position_error_m,
        "final_orientation_error_rad": result.final_orientation_error_rad,
        "min_clearance_m": result.min_clearance_m,
        "raw_barrier_violation_rate": result.raw_barrier_violation_rate,
        "safe_barrier_violation_rate": result.safe_barrier_violation_rate,
        "exec_barrier_violation_rate": result.exec_barrier_violation_rate,
        "guard_intervention_norm": result.guard_intervention_norm,
        "wrench_realization_rmse": result.wrench_realization_rmse,
        "saturation_fraction": result.saturation_fraction,
        "positive_hamiltonian_delta_rate": result.positive_hamiltonian_delta_rate,
        "mechanical_work_j": result.mechanical_work_j,
        "force_effort_n2s": result.force_effort_n2s,
        "messages": result.messages,
        "runtime_wall_s": result.runtime_wall_s,
        "steps": len(result.raw_wrench),
        "max_mechanics_residual": float(np.max(result.mechanics_residual)) if result.mechanics_residual.size else 0.0,
        "positions_repaired_after_integration": int(result.positions_repaired_after_integration),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _bootstrap_ci(values: np.ndarray, seed: int, draws: int = 2000) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(finite, size=(draws, finite.size), replace=True), axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


SUMMARY_METRICS = [
    "safe_transport_success",
    "target_reached",
    "any_collision",
    "timeout",
    "time_to_target_s",
    "final_position_error_m",
    "min_clearance_m",
    "exec_barrier_violation_rate",
    "guard_intervention_norm",
    "wrench_realization_rmse",
    "saturation_fraction",
    "positive_hamiltonian_delta_rate",
    "mechanical_work_j",
    "messages",
    "runtime_wall_s",
]


def summarize_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for method_index, method in enumerate(METHOD_LABELS):
        selected = [row for row in rows if row["method"] == method]
        if not selected:
            continue
        record: dict[str, Any] = {"method": method, "method_label": METHOD_LABELS[method], "n": len(selected)}
        for metric_index, metric in enumerate(SUMMARY_METRICS):
            values = np.asarray([float(row[metric]) for row in selected], dtype=float)
            record[metric] = float(np.mean(values))
            low, high = _bootstrap_ci(values, 58100 + 97 * method_index + metric_index)
            record[f"{metric}_ci95_low"] = low
            record[f"{metric}_ci95_high"] = high
        summary.append(record)
    return summary


def _paired(rows: list[dict[str, Any]], a: str, b: str, metric: str) -> tuple[np.ndarray, np.ndarray]:
    keys = ("scenario", "seed", "n_robots")
    left = {tuple(row[key] for key in keys): float(row[metric]) for row in rows if row["method"] == a}
    right = {tuple(row[key] for key in keys): float(row[metric]) for row in rows if row["method"] == b}
    common = sorted(set(left) & set(right))
    return np.asarray([left[key] for key in common]), np.asarray([right[key] for key in common])


def _holm(values: list[float]) -> list[float]:
    order = np.argsort(values)
    adjusted = np.ones(len(values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted.tolist()


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    raw_p: list[float] = []
    for index, hypothesis in enumerate(hypotheses):
        a, b = _paired(rows, str(hypothesis["method_a"]), str(hypothesis["method_b"]), str(hypothesis["metric"]))
        difference = a - b
        direction = str(hypothesis.get("direction", "different"))
        alternative = "greater" if direction == "greater" else "less" if direction == "less" else "two-sided"
        binary = a.size > 0 and set(np.unique(np.concatenate([a, b]))).issubset({0.0, 1.0})
        if binary:
            positive = int(np.sum((a == 1.0) & (b == 0.0)))
            negative = int(np.sum((a == 0.0) & (b == 1.0)))
            discordant = positive + negative
            p_value = float(binomtest(positive, discordant, 0.5, alternative=alternative).pvalue) if discordant else 1.0
            test = "paired_McNemar_exact"
        elif difference.size and np.any(np.abs(difference) > 1e-12):
            p_value = float(wilcoxon(difference, alternative=alternative, zero_method="wilcox").pvalue)
            test = "paired_Wilcoxon"
        else:
            p_value = 1.0
            test = "all_pairs_equal"
        rng = np.random.default_rng(59000 + index)
        if difference.size:
            boot = np.mean(rng.choice(difference, size=(3000, difference.size), replace=True), axis=1)
            ci_low, ci_high = np.quantile(boot, [0.025, 0.975])
        else:
            ci_low = ci_high = math.nan
        raw_p.append(p_value)
        results.append(
            {
                "hypothesis": str(hypothesis["id"]),
                "metric": str(hypothesis["metric"]),
                "method_a": str(hypothesis["method_a"]),
                "method_b": str(hypothesis["method_b"]),
                "direction": direction,
                "test": test,
                "n_pairs": int(a.size),
                "mean_a": float(np.mean(a)) if a.size else math.nan,
                "mean_b": float(np.mean(b)) if b.size else math.nan,
                "effect_estimate": float(np.mean(difference)) if difference.size else math.nan,
                "CI95_low": float(ci_low),
                "CI95_high": float(ci_high),
                "raw_p": p_value,
                "margin": float(hypothesis.get("margin", 0.0)),
            }
        )
    for row, adjusted in zip(results, _holm(raw_p), strict=True):
        row["Holm_adjusted_p"] = adjusted
        direction = row["direction"]
        effect = row["effect_estimate"]
        margin = row["margin"]
        directional = effect > margin if direction == "greater" else effect < -margin if direction == "less" else abs(effect) > margin
        row["decision"] = "supported" if adjusted < 0.05 and directional else "not_supported"
    return results


def _stage_rows(results: list[PayloadRunResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for stage, values in (
            ("RAW", result.raw_barrier_residual),
            ("SAFE", result.safe_barrier_residual),
            ("EXEC", result.exec_barrier_residual),
        ):
            rows.append(
                {
                    "scenario": result.scenario,
                    "seed": result.seed,
                    "n_robots": result.n_robots,
                    "world_hash": result.world_hash,
                    "method": result.method,
                    "stage": stage,
                    "barrier_violation_rate": float(np.mean(values > 1e-7)) if values.size else 0.0,
                    "max_barrier_residual": float(np.max(values)) if values.size else 0.0,
                    "is_executed_trajectory": int(stage == "EXEC"),
                }
            )
    return rows


def _theory_audit(worlds: list[TransportWorld], results: list[PayloadRunResult]) -> dict[str, Any]:
    initial = [_clearance(world, world.q0, 0.0) for world in worlds]
    same_world = all(
        len({result.world_hash for result in results if result.scenario == world.scenario and result.seed == world.seed and result.n_robots == world.n_robots}) == 1
        for world in worlds
    )
    max_mechanics = max((float(np.max(result.mechanics_residual)) if result.mechanics_residual.size else 0.0) for result in results)
    finite = all(np.isfinite(result.load_pose).all() and np.isfinite(result.load_velocity).all() for result in results)
    no_repair = all(not result.positions_repaired_after_integration for result in results)
    all_failures_preserved = all(result.termination_reason in {"target_reached", "collision", "timeout", "numerical_failure", "initial_collision"} for result in results)
    gates = {
        "initial_worlds_collision_free": min(initial) >= 0.0,
        "same_world_hash_for_all_methods": same_world,
        "finite_dynamics": finite,
        "mechanics_identity": max_mechanics <= 1e-8,
        "positions_never_repaired": no_repair,
        "failures_and_timeouts_preserved": all_failures_preserved,
        "raw_safe_exec_separated": all(result.raw_wrench.shape == result.safe_wrench.shape == result.exec_wrench.shape for result in results),
    }
    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": gates,
        "worlds": len(worlds),
        "runs": len(results),
        "minimum_initial_clearance_m": float(min(initial)),
        "max_mechanics_residual": max_mechanics,
        "positions_repaired_after_integration": False,
        "legacy_semantic_finding": "The historical SP5 projected payload and robot poses after integration; those runs remain historical and are not canonical evidence for continuous safety.",
        "model_scope": "reduced_order_planar_rigid_payload_bounded_planar_contact_forces_fixed_post_docking_contacts",
        "not_claimed": "No frictional contact, wheel-ground dynamics, kinodynamic optimality, CoppeliaSim or hardware validation is claimed.",
    }


def _plot_primary(summary: list[dict[str, Any]], path: Path) -> None:
    labels = [row["method_label"] for row in summary]
    success = [row["safe_transport_success"] for row in summary]
    collision = [row["any_collision"] for row in summary]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    ax.bar(x - 0.19, success, 0.38, label="safe success", color="#2a9d8f")
    ax.bar(x + 0.19, collision, 0.38, label="collision", color="#e76f51")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("fraction of fixed worlds")
    ax.set_xticks(x, labels, rotation=28, ha="right")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_stage(stage_rows: list[dict[str, Any]], path: Path) -> None:
    methods = list(METHOD_LABELS)
    stages = ["RAW", "SAFE", "EXEC"]
    matrix = np.zeros((len(methods), len(stages)))
    for i, method in enumerate(methods):
        for j, stage in enumerate(stages):
            selected = [row["barrier_violation_rate"] for row in stage_rows if row["method"] == method and row["stage"] == stage]
            matrix[i, j] = np.mean(selected) if selected else math.nan
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    image = ax.imshow(matrix, vmin=0, vmax=max(0.01, float(np.nanmax(matrix))), cmap="magma_r", aspect="auto")
    ax.set_xticks(range(3), stages)
    ax.set_yticks(range(len(methods)), [METHOD_LABELS[m] for m in methods])
    for i in range(len(methods)):
        for j in range(3):
            ax.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="barrier violation rate")
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_scenario(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = list(SCENARIO_GENERATORS)
    methods = list(METHOD_LABELS)
    matrix = np.zeros((len(methods), len(scenarios)))
    for i, method in enumerate(methods):
        for j, scenario in enumerate(scenarios):
            selected = [float(row["safe_transport_success"]) for row in rows if row["method"] == method and row["scenario"] == scenario]
            matrix[i, j] = np.mean(selected) if selected else math.nan
    fig, ax = plt.subplots(figsize=(10.4, 6.0))
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(scenarios)), scenarios, rotation=25, ha="right")
    ax.set_yticks(range(len(methods)), [METHOD_LABELS[m] for m in methods])
    for i in range(len(methods)):
        for j in range(len(scenarios)):
            ax.text(j, i, f"{matrix[i, j]:.2f}", color="white" if matrix[i, j] < 0.55 else "black", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="safe transport success")
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_pareto(summary: list[dict[str, Any]], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    for row in summary:
        ax.scatter(row["mechanical_work_j"], row["safe_transport_success"], s=70 + 170 * row["any_collision"], alpha=0.82)
        ax.annotate(row["method"], (row["mechanical_work_j"], row["safe_transport_success"]), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("positive mechanical work [J]")
    ax.set_ylabel("safe transport success")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _plot_trajectory(world: TransportWorld, results: list[PayloadRunResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 7.0))
    for obstacle in world.problem.world.map.obstacles:
        ax.add_patch(plt.Circle(obstacle.center, obstacle.radius, color="#6b7280", alpha=0.45))
    for group in world.problem.mobile_groups:
        ax.plot([group.start_xy[0], group.end_xy[0]], [group.start_xy[1], group.end_xy[1]], "--", color="#7c3aed", alpha=0.6)
    for result in results:
        ax.plot(result.load_pose[:, 0], result.load_pose[:, 1], label=METHOD_LABELS[result.method], linewidth=1.5)
        ax.scatter(result.load_pose[-1, 0], result.load_pose[-1, 1], s=18)
    ax.scatter(world.q0[0], world.q0[1], marker="s", s=65, color="black", label="start")
    ax.scatter(world.target[0], world.target[1], marker="*", s=130, color="#f4a261", label="target")
    half = 0.5 * world.problem.world.map.size_m
    ax.set(xlim=(-half, half), ylim=(-half, half), aspect="equal", xlabel="x [m]", ylabel="y [m]")
    ax.legend(fontsize=7, ncol=2, frameon=False)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def _hardware() -> dict[str, Any]:
    return {
        "cpu_model": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "machine": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "gpu_used": False,
        "execution_device": "CPU",
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
    }


def _sha256_file(path: Path) -> str:
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


def _freeze_protocol(config: dict[str, Any], config_path: Path, output: Path) -> dict[str, Any]:
    protocol = output / "protocol"
    protocol.mkdir(parents=True, exist_ok=True)
    existing_manifest_path = protocol / "frozen_manifest_v2.json"
    if existing_manifest_path.exists():
        existing = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        required = {
            "config_sha256": protocol / "frozen_protocol_v2.yaml",
            "hypotheses_sha256": protocol / "hypotheses_v2.yaml",
            "seed_registry_sha256": protocol / "seed_registry_v2.yaml",
            "environment_lock_sha256": protocol / "environment_v2.lock.json",
        }
        if not existing.get("frozen") or existing.get("status") != "frozen_ready_for_execution":
            raise RuntimeError("Existing SP5 freeze manifest is invalid.")
        if any(not file.exists() or _sha256_file(file) != existing.get(field) for field, file in required.items()):
            raise RuntimeError("Existing SP5 frozen protocol hash mismatch.")
        return existing
    pilot_path = Path(str(config["pilot_evidence"]))
    pilot_audit = pilot_path / "theory_audit.json"
    if not pilot_audit.exists() or json.loads(pilot_audit.read_text(encoding="utf-8")).get("status") != "PASS":
        raise RuntimeError("SP5 confirmatory freeze requires a PASS pilot theory audit.")
    frozen_protocol = dict(config)
    frozen_protocol.update({"frozen": True, "status": "frozen_ready_for_execution"})
    protocol_yaml = protocol / "frozen_protocol_v2.yaml"
    hypotheses_yaml = protocol / "hypotheses_v2.yaml"
    seeds_yaml = protocol / "seed_registry_v2.yaml"
    environment_json = protocol / "environment_v2.lock.json"
    protocol_yaml.write_text(yaml.safe_dump(frozen_protocol, sort_keys=False), encoding="utf-8")
    hypotheses_yaml.write_text(yaml.safe_dump({"hypotheses": config.get("hypotheses", [])}, sort_keys=False), encoding="utf-8")
    seed_cfg = dict(config["seeds"])
    start = int(seed_cfg["start"])
    count = int(seed_cfg["count"])
    registry = {
        "pilot_seeds": list(range(573000, 573000 + 2)),
        "confirmatory_seeds": list(range(start, start + count)),
        "disjoint": not bool(set(range(573000, 573002)) & set(range(start, start + count))),
        "confirmatory_opened": False,
    }
    seeds_yaml.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    environment_json.write_text(json.dumps(_hardware(), indent=2), encoding="utf-8")
    manifest = {
        "frozen": True,
        "status": "frozen_ready_for_execution",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit_sha": _git_sha(),
        "config_source": str(config_path),
        "config_sha256": _sha256_file(protocol_yaml),
        "hypotheses_sha256": _sha256_file(hypotheses_yaml),
        "seed_registry_sha256": _sha256_file(seeds_yaml),
        "environment_lock_sha256": _sha256_file(environment_json),
        "pilot_evidence_sha256": _sha256_file(pilot_audit),
        "hardware_id": _sha256_file(environment_json)[:16],
        "confirmatory_seeds_opened": False,
    }
    manifest_path = protocol / "frozen_manifest_v2.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    hashes = [
        f"{_sha256_file(path)}  {path.name}"
        for path in (protocol_yaml, hypotheses_yaml, seeds_yaml, environment_json, manifest_path)
    ]
    (protocol / "HASHES_v2.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    return manifest


def _open_confirmatory(output: Path) -> dict[str, Any]:
    protocol = output / "protocol"
    manifest_path = protocol / "frozen_manifest_v2.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("frozen") or manifest.get("status") != "frozen_ready_for_execution":
        raise RuntimeError("SP5 confirmatory seeds cannot be opened before freeze.")
    event_path = protocol / "confirmatory_seed_opening.json"
    if event_path.exists():
        return json.loads(event_path.read_text(encoding="utf-8"))
    event = {
        "status": "OPENED",
        "confirmatory_seeds_opened": True,
        "after_freeze": True,
        "opened_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_manifest_sha256": _sha256_file(manifest_path),
        "seed_registry_sha256": manifest["seed_registry_sha256"],
    }
    event_path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    manifest["confirmatory_seeds_opened"] = True
    manifest["confirmatory_seed_opening_event_sha256"] = _sha256_file(event_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return event


def _write_report(path: Path, experiment_id: str, summary: list[dict[str, Any]], hypotheses: list[dict[str, Any]], audit: dict[str, Any], manifest: dict[str, Any]) -> None:
    lines = [
        f"# {experiment_id}",
        "",
        f"- Worlds: `{manifest['worlds']}`.",
        f"- Runs: `{manifest['runs']}`.",
        f"- Execution: CPU only; GPU used: `false`.",
        f"- Theory/semantics audit: **{audit['status']}**.",
        "- RAW, SAFE and EXEC are stored separately; only EXEC drives the plant.",
        "- No payload or robot position is repaired after integration.",
        "",
        "## Method summary",
        "",
        "| Method | Safe success | Collision | Timeout | Target s | EXEC barrier | Wrench RMSE | Work J | Runtime s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method_label']} | {row['safe_transport_success']:.3f} | {row['any_collision']:.3f} | "
            f"{row['timeout']:.3f} | {row['time_to_target_s']:.2f} | {row['exec_barrier_violation_rate']:.4f} | "
            f"{row['wrench_realization_rmse']:.3f} | {row['mechanical_work_j']:.1f} | {row['runtime_wall_s']:.4f} |"
        )
    lines.extend(["", "## Frozen confirmatory hypotheses", "", "| ID | Effect | 95% CI | p Holm | Decision |", "|---|---:|---:|---:|---|"])
    for row in hypotheses:
        lines.append(
            f"| {row['hypothesis']} | {row['effect_estimate']:.4f} | [{row['CI95_low']:.4f}, {row['CI95_high']:.4f}] | "
            f"{row['Holm_adjusted_p']:.4g} | {row['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Audit and scope",
            "",
            f"- Minimum initial clearance: `{audit['minimum_initial_clearance_m']:.6g}` m.",
            f"- Maximum discrete mechanics residual: `{audit['max_mechanics_residual']:.6g}`.",
            f"- Historical semantic finding: {audit['legacy_semantic_finding']}",
            f"- Model scope: `{audit['model_scope']}`.",
            f"- Not claimed: {audit['not_claimed']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_payload_transport_config(config_path: Path | str) -> dict[str, Any]:
    """Run pilot or frozen confirmatory SP5 v2 on CPU."""

    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output = Path(str(config["output_dir"]))
    output.mkdir(parents=True, exist_ok=True)
    for child in ("tables", "figures", "traces", "audit"):
        (output / child).mkdir(parents=True, exist_ok=True)
    mode = str(config.get("mode", "pilot"))
    frozen_manifest: dict[str, Any] | None = None
    opening: dict[str, Any] | None = None
    if mode == "confirmatory":
        frozen_manifest = _freeze_protocol(config, path, output)
        opening = _open_confirmatory(output)
    seed_cfg = dict(config["seeds"])
    seeds = range(int(seed_cfg["start"]), int(seed_cfg["start"]) + int(seed_cfg["count"]))
    scenarios = [str(item["id"]) for item in config["scenarios"]]
    robot_counts = [int(value) for value in config.get("robot_counts", [4, 8, 12])]
    methods = [str(item["id"]) for item in config["methods"]]
    worlds = [build_transport_world(scenario, seed, n) for scenario in scenarios for n in robot_counts for seed in seeds]
    results: list[PayloadRunResult] = []
    representative: list[PayloadRunResult] = []
    representative_key = (str(config.get("representative_scenario", scenarios[0])), robot_counts[0], int(seed_cfg["start"]))
    simulation = dict(config.get("simulation", {}))
    for world in worlds:
        for method in methods:
            result = simulate_payload_transport(
                world,
                method,
                dt_s=float(simulation.get("dt_s", 0.15)),
                horizon_s=float(simulation.get("horizon_s", 45.0)),
                stable_steps=int(simulation.get("stable_steps", 5)),
            )
            results.append(result)
            if (world.scenario, world.n_robots, world.seed) == representative_key:
                representative.append(result)
    rows = [_run_row(result) for result in results]
    stage_rows = _stage_rows(results)
    summary = summarize_runs(rows)
    hypotheses = evaluate_hypotheses(rows, list(config.get("hypotheses", [])))
    audit = _theory_audit(worlds, results)
    _write_csv(output / "tables" / "runs.csv", rows)
    _write_csv(output / "tables" / "summary.csv", summary)
    _write_csv(output / "tables" / "stage_ablation.csv", stage_rows)
    _write_csv(output / "tables" / "hypothesis_results.csv", hypotheses)
    (output / "theory_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    _plot_primary(summary, output / "figures" / "fig-sp5-payload-performance.png")
    _plot_stage(stage_rows, output / "figures" / "fig-sp5-raw-safe-exec.png")
    _plot_scenario(rows, output / "figures" / "fig-sp5-scenario-matrix.png")
    _plot_pareto(summary, output / "figures" / "fig-sp5-payload-pareto.png")
    if representative:
        world = next(item for item in worlds if (item.scenario, item.n_robots, item.seed) == representative_key)
        _plot_trajectory(world, representative, output / "figures" / "fig-sp5-payload-trajectories.png")
        for result in representative:
            np.savez_compressed(
                output / "traces" / f"{result.method}.npz",
                time_s=result.time_s,
                load_pose=result.load_pose,
                load_velocity=result.load_velocity,
                raw_wrench=result.raw_wrench,
                safe_wrench=result.safe_wrench,
                exec_wrench=result.exec_wrench,
                contact_forces=result.contact_forces,
                hamiltonian=result.hamiltonian,
            )
    manifest = {
        "experiment_id": experiment_id,
        "mode": mode,
        "status": "complete" if audit["status"] == "PASS" else "failed_audit",
        "worlds": len(worlds),
        "runs": len(results),
        "methods": len(methods),
        "scenarios": len(scenarios),
        "robot_counts": robot_counts,
        "expected_runs": len(worlds) * len(methods),
        "count_valid": len(results) == len(worlds) * len(methods),
        "theory_audit": audit["status"],
        "hardware": _hardware(),
        "config": str(path),
        "frozen_before_confirmatory_seed_opening": bool(mode != "confirmatory" or (frozen_manifest and opening and opening.get("after_freeze"))),
        "confirmatory_seeds_opened": bool(opening and opening.get("confirmatory_seeds_opened")),
        "confirmatory_seed_opening_event_sha256": _sha256_file(output / "protocol" / "confirmatory_seed_opening.json") if opening else None,
        "sum_method_runtime_wall_s": float(sum(result.runtime_wall_s for result in results)),
        "legacy_high_power_status": "historical_noncanonical_post_integration_projection",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_report(output / "report.md", experiment_id, summary, hypotheses, audit, manifest)
    if mode == "confirmatory" and audit["status"] != "PASS":
        raise RuntimeError("SP5 v2 confirmatory campaign failed its semantic/theory audit.")
    return manifest


__all__ = [
    "METHOD_LABELS",
    "PayloadRunResult",
    "TransportWorld",
    "build_transport_world",
    "evaluate_hypotheses",
    "run_payload_transport_config",
    "simulate_payload_transport",
    "summarize_runs",
]
