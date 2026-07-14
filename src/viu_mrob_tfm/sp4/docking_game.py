"""SP4 wrench-aware safe docking game on a non-holonomic AMR plant.

The module is independent from the legacy SP4 single-integrator campaign. It
keeps the population state, RAW primitive, SAFE velocity and EXEC wheel
torques as separate experimental objects. Positions are never repaired after
integration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
import math
from pathlib import Path
import time
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.optimize import Bounds, LinearConstraint, minimize
from scipy.stats import binomtest, wilcoxon


METHOD_LABELS = {
    "direct_to_slot": "Directo al contacto",
    "apf_navigation": "APF",
    "rvo_proxy": "RVO proxy",
    "cbf_qp": "Proyeccion CBF",
    "central_potential_reference": "PD central (70 iter.)",
    "nash_pd_exact": "Nash-PD exacto",
    "nash_pd_exact_raw": "Nash-PD RAW",
    "nash_pd_ring": "Nash-PD anillo",
    "smith_primitives": "Smith + CBF",
    "replicator_primitives": "Replicator + CBF",
    "erv_bnn_primitives": "ERV-BNN + CBF",
}

GAME_METHODS = {
    "central_potential_reference": ("projected_pd", "complete"),
    "nash_pd_exact": ("projected_pd", "complete"),
    "nash_pd_exact_raw": ("projected_pd", "complete"),
    "nash_pd_ring": ("projected_pd", "ring"),
    "smith_primitives": ("smith", "complete"),
    "replicator_primitives": ("replicator", "complete"),
    "erv_bnn_primitives": ("erv_bnn", "complete"),
}

GUARDED_METHODS = {
    "cbf_qp",
    "central_potential_reference",
    "nash_pd_exact",
    "nash_pd_exact_raw",
    "nash_pd_ring",
    "smith_primitives",
    "replicator_primitives",
    "erv_bnn_primitives",
}


@dataclass(frozen=True, slots=True)
class DockingWorld:
    scenario: str
    seed: int
    n_robots: int
    initial_state: np.ndarray
    target_pose: np.ndarray
    wrench_priority: np.ndarray
    mass_kg: np.ndarray
    inertia_kgm2: np.ndarray
    max_speed_mps: np.ndarray
    max_omega_rps: np.ndarray
    max_accel_mps2: np.ndarray
    max_alpha_rps2: np.ndarray
    max_wheel_torque_nm: np.ndarray
    obstacles: np.ndarray
    map_half_extent_m: float = 6.0
    robot_radius_m: float = 0.18
    load_radius_m: float = 0.78
    wheel_radius_m: float = 0.08
    axle_length_m: float = 0.38
    hand_point_m: float = 0.02
    safety_margin_m: float = 0.005


@dataclass(frozen=True, slots=True)
class PrimitiveSnapshot:
    controls: np.ndarray
    endpoints: np.ndarray
    occupancy_features: np.ndarray
    costs: np.ndarray
    capacity: np.ndarray
    resource_ids: tuple[tuple[int, int, int], ...]

    @property
    def n_actions(self) -> int:
        return int(self.controls.shape[1])


@dataclass(slots=True)
class GameStepResult:
    preferences: np.ndarray
    dual_prices: np.ndarray
    potential_history: list[float]
    kkt_history: list[float]
    consensus_error: float
    messages: int
    iterations: int
    simplex_error: float
    capacity_violation: float
    kkt_residual: float


@dataclass(slots=True)
class DockingRunResult:
    method: str
    scenario: str
    seed: int
    n_robots: int
    safe_docking_success: bool
    arrival_success: bool
    any_collision: bool
    timeout: bool
    docking_time_s: float
    time_to_wrench_feasible_s: float
    min_clearance_m: float
    final_position_error_m: float
    final_orientation_error_rad: float
    energy_wh: float
    path_length_m: float
    guard_interventions: int
    closure_interventions: int
    guard_intervention_norm: float
    raw_barrier_violations: int
    exec_barrier_violations: int
    max_exec_barrier_residual: float
    torque_saturation_events: int
    mean_kkt_residual: float
    final_kkt_residual: float
    max_simplex_error: float
    max_capacity_violation: float
    consensus_error: float
    messages: int
    runtime_s: float
    steps: int
    positions: np.ndarray
    potential_trace: np.ndarray
    kkt_trace: np.ndarray


def wrap_angle(angle: np.ndarray | float) -> np.ndarray | float:
    return (np.asarray(angle) + np.pi) % (2.0 * np.pi) - np.pi


def project_simplex(vector: np.ndarray) -> np.ndarray:
    """Euclidean projection onto the probability simplex."""

    v = np.asarray(vector, dtype=float)
    if v.ndim != 1:
        raise ValueError("project_simplex expects a one-dimensional vector")
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    indices = np.arange(1, v.size + 1)
    eligible = u - cssv / indices > 0.0
    if not np.any(eligible):
        return np.full_like(v, 1.0 / max(v.size, 1))
    rho = int(indices[eligible][-1])
    theta = float(cssv[rho - 1] / rho)
    return np.maximum(v - theta, 0.0)


def _scenario_obstacles(name: str, rng: np.random.Generator) -> np.ndarray:
    if name == "open_docking":
        return np.zeros((0, 3), dtype=float)
    if name == "crossing":
        return np.asarray([[0.0, 2.15, 0.42], [0.0, -2.15, 0.42]], dtype=float)
    if name == "narrow_passage":
        return np.asarray(
            [[-1.55, 0.95, 0.72], [-1.55, -0.95, 0.72], [1.55, 0.95, 0.72], [1.55, -0.95, 0.72]],
            dtype=float,
        )
    if name == "cluttered_docking":
        angles = np.linspace(0.0, 2.0 * np.pi, 7, endpoint=False) + rng.uniform(-0.18, 0.18, 7)
        radii = rng.uniform(2.0, 3.7, 7)
        return np.column_stack([radii * np.cos(angles), radii * np.sin(angles), rng.uniform(0.30, 0.48, 7)])
    if name == "symmetric_deadlock":
        return np.asarray([[0.0, 2.55, 0.38], [0.0, -2.55, 0.38]], dtype=float)
    if name == "actuator_limited":
        return np.asarray([[-1.55, 0.0, 0.48], [1.55, 0.0, 0.48], [0.0, 2.45, 0.35]], dtype=float)
    raise ValueError(f"Unknown SP4 docking scenario: {name}")


def build_docking_world(scenario: str, seed: int, n_robots: int) -> DockingWorld:
    """Generate a paired safe-docking world with fixed SP3 contact slots."""

    if n_robots < 3:
        raise ValueError("SP4 docking requires at least three robots")
    rng = np.random.default_rng(seed + 1009 * n_robots)
    slot_angles = np.linspace(0.0, 2.0 * np.pi, n_robots, endpoint=False)
    target_radius = 1.06
    target_xy = target_radius * np.column_stack([np.cos(slot_angles), np.sin(slot_angles)])
    target_theta = wrap_angle(slot_angles + np.pi)
    target_pose = np.column_stack([target_xy, target_theta])

    start_angles = slot_angles.copy()
    if scenario in {"crossing", "symmetric_deadlock"}:
        start_angles = np.roll(slot_angles, max(n_robots // 2, 1))
    elif scenario == "narrow_passage":
        # Split the fleet between two approach arcs while preserving enough
        # angular separation for every initial disk to be collision-free.
        start_angles = np.zeros(n_robots, dtype=float)
        for parity, center in ((0, np.pi), (1, 0.0)):
            indices = np.arange(parity, n_robots, 2)
            offsets = 0.20 * (
                np.arange(indices.size, dtype=float) - 0.5 * (indices.size - 1)
            )
            start_angles[indices] = center + offsets + rng.normal(0.0, 0.012, indices.size)
    elif scenario == "cluttered_docking":
        start_angles = rng.permutation(slot_angles)
    else:
        spacing = 2.0 * np.pi / n_robots
        perturbation = np.clip(
            rng.normal(0.0, min(0.10, 0.10 * spacing), n_robots),
            -0.18 * spacing,
            0.18 * spacing,
        )
        start_angles = slot_angles + perturbation

    start_radius = 4.65 if scenario != "actuator_limited" else 4.9
    initial_xy = start_radius * np.column_stack([np.cos(start_angles), np.sin(start_angles)])
    initial_xy += rng.uniform(-0.08, 0.08, initial_xy.shape)
    initial_theta = wrap_angle(
        np.arctan2(target_xy[:, 1] - initial_xy[:, 1], target_xy[:, 0] - initial_xy[:, 0])
        + rng.normal(0.0, 0.18, n_robots)
    )
    initial_state = np.column_stack([initial_xy, initial_theta, np.zeros(n_robots), np.zeros(n_robots)])

    wrench_priority = 0.75 + 0.50 * np.abs(np.sin(slot_angles + 0.37))
    mass = rng.uniform(22.0, 38.0, n_robots)
    inertia = rng.uniform(1.8, 3.2, n_robots)
    max_speed = rng.uniform(0.72, 0.92, n_robots)
    max_omega = rng.uniform(1.35, 1.75, n_robots)
    max_accel = rng.uniform(1.05, 1.45, n_robots)
    max_alpha = rng.uniform(2.1, 3.0, n_robots)
    max_torque = rng.uniform(4.2, 5.8, n_robots)
    if scenario == "actuator_limited":
        weak = np.arange(n_robots) % 3 == 0
        max_speed[weak] *= 0.62
        max_omega[weak] *= 0.60
        max_accel[weak] *= 0.58
        max_alpha[weak] *= 0.55
        max_torque[weak] *= 0.62
        mass[weak] *= 1.20

    return DockingWorld(
        scenario=scenario,
        seed=int(seed),
        n_robots=int(n_robots),
        initial_state=initial_state,
        target_pose=target_pose,
        wrench_priority=wrench_priority,
        mass_kg=mass,
        inertia_kgm2=inertia,
        max_speed_mps=max_speed,
        max_omega_rps=max_omega,
        max_accel_mps2=max_accel,
        max_alpha_rps2=max_alpha,
        max_wheel_torque_nm=max_torque,
        obstacles=_scenario_obstacles(scenario, rng),
    )


def _integrate_constant_control(
    position: np.ndarray,
    theta: float,
    v_cmd: float,
    omega_cmd: float,
    times: np.ndarray,
) -> np.ndarray:
    points = np.zeros((times.size, 2), dtype=float)
    if abs(omega_cmd) < 1e-8:
        points[:, 0] = position[0] + times * v_cmd * math.cos(theta)
        points[:, 1] = position[1] + times * v_cmd * math.sin(theta)
        return points
    points[:, 0] = position[0] + v_cmd / omega_cmd * (
        np.sin(theta + omega_cmd * times) - math.sin(theta)
    )
    points[:, 1] = position[1] - v_cmd / omega_cmd * (
        np.cos(theta + omega_cmd * times) - math.cos(theta)
    )
    return points


def _clearance_to_circles(
    point: np.ndarray,
    world: DockingWorld,
    *,
    include_load: bool = True,
) -> float:
    clearance = float("inf")
    for obstacle in world.obstacles:
        clearance = min(
            clearance,
            float(np.linalg.norm(point - obstacle[:2]) - obstacle[2] - world.robot_radius_m),
        )
    if include_load:
        clearance = min(
            clearance,
            float(np.linalg.norm(point) - world.load_radius_m - world.robot_radius_m),
        )
    return clearance


def _game_guidance_point(
    world: DockingWorld,
    position: np.ndarray,
    target: np.ndarray,
    robot_index: int,
    *,
    forced_side: float | None = None,
    radial_offset_m: float = 0.0,
) -> np.ndarray:
    """Return a local tangent waypoint when the direct chord crosses the load.

    The forced_side argument exposes the two homotopy classes around the
    payload to the game: -1 is clockwise, +1 is counter-clockwise, and None
    selects the shortest angular route.
    """

    radius = float(np.linalg.norm(position))
    chord_clearance = _segment_point_distance(position, target, np.zeros(2))
    required = (
        world.load_radius_m
        + world.robot_radius_m
        + world.safety_margin_m
        + abs(world.hand_point_m)
    )
    if chord_clearance >= required:
        return np.asarray(target, dtype=float)
    phi = math.atan2(position[1], position[0])
    target_phi = math.atan2(target[1], target[0])
    angular_error = float(wrap_angle(target_phi - phi))
    if forced_side is not None:
        side = 1.0 if forced_side >= 0.0 else -1.0
    elif abs(abs(angular_error) - np.pi) < 0.20:
        side = 1.0 if robot_index % 2 == 0 else -1.0
    else:
        side = 1.0 if angular_error >= 0.0 else -1.0
    waypoint_radius = max(1.42 + radial_offset_m, min(radius, 2.15 + radial_offset_m))
    waypoint_angle = phi + side * 0.62
    return waypoint_radius * np.asarray([math.cos(waypoint_angle), math.sin(waypoint_angle)])


def build_primitive_snapshot(
    world: DockingWorld,
    state: np.ndarray,
    docked: np.ndarray | None = None,
    *,
    route_commitment: np.ndarray | None = None,
    prediction_times_s: Iterable[float] = (0.45, 0.90, 1.35, 1.80),
    cell_size_m: float | None = None,
) -> PrimitiveSnapshot:
    """Build convex space-time occupancy features for six motion primitives."""

    n = world.n_robots
    docked_mask = np.zeros(n, dtype=bool) if docked is None else np.asarray(docked, dtype=bool)
    committed_route = (
        np.zeros(n, dtype=int)
        if route_commitment is None
        else np.asarray(route_commitment, dtype=int)
    )
    times = np.asarray(tuple(prediction_times_s), dtype=float)
    n_actions = 6
    controls = np.zeros((n, n_actions, 2), dtype=float)
    endpoints = np.zeros((n, n_actions, 2), dtype=float)
    costs = np.zeros((n, n_actions), dtype=float)
    paths: list[list[np.ndarray]] = [[np.zeros((times.size, 2)) for _ in range(n_actions)] for _ in range(n)]
    # Two clockwise arcs, the locally shortest arc, two counter-clockwise arcs,
    # and wait/rotate. The game therefore chooses route classes, not gains only.
    route_side: tuple[float | None, ...] = (-1.0, -1.0, None, 1.0, 1.0, None)
    radial_offset = np.asarray([0.28, 0.0, 0.0, 0.0, 0.28, 0.0], dtype=float)
    heading_bias = np.asarray([-0.16, -0.04, 0.0, 0.04, 0.16, 0.0], dtype=float)
    speed_scale = np.asarray([0.72, 0.88, 1.0, 0.88, 0.72, 0.0], dtype=float)

    for i in range(n):
        position = state[i, :2]
        theta = float(state[i, 2])
        distance = float(np.linalg.norm(world.target_pose[i, :2] - position))
        target_angle_error = float(wrap_angle(world.target_pose[i, 2] - theta))
        near = distance < 0.42
        for action in range(n_actions):
            guidance = _game_guidance_point(
                world,
                position,
                world.target_pose[i, :2],
                i,
                forced_side=route_side[action],
                radial_offset_m=float(radial_offset[action]),
            )
            delta = guidance - position
            desired_heading = (
                math.atan2(delta[1], delta[0])
                if np.linalg.norm(delta) > 1e-12
                else float(world.target_pose[i, 2])
            )
            heading_error = float(wrap_angle(desired_heading - theta))
            if docked_mask[i]:
                v_cmd = 0.0
                omega_cmd = 0.0
            elif distance <= world.robot_radius_m:
                v_cmd = 0.0
                omega_cmd = np.clip(
                    1.9 * target_angle_error,
                    -world.max_omega_rps[i],
                    world.max_omega_rps[i],
                )
            elif near:
                v_cmd = (
                    min(world.max_speed_mps[i] * 0.38, 1.35 * distance)
                    * max(0.08, math.cos(heading_error))
                )
                omega_cmd = np.clip(
                    1.9 * heading_error
                    + (0.30 * target_angle_error if distance < 0.24 else 0.0)
                    + heading_bias[action],
                    -world.max_omega_rps[i],
                    world.max_omega_rps[i],
                )
                if action == n_actions - 1:
                    v_cmd = 0.0
                    omega_cmd = np.clip(1.9 * target_angle_error, -world.max_omega_rps[i], world.max_omega_rps[i])
            else:
                alignment = max(0.12, math.cos(heading_error))
                v_cmd = world.max_speed_mps[i] * speed_scale[action] * alignment
                omega_cmd = np.clip(
                    1.48 * heading_error + heading_bias[action],
                    -world.max_omega_rps[i],
                    world.max_omega_rps[i],
                )
            controls[i, action] = (v_cmd, omega_cmd)
            path = _integrate_constant_control(position, theta, float(v_cmd), float(omega_cmd), times)
            paths[i][action] = path
            endpoints[i, action] = path[-1]
            endpoint_distance = float(np.linalg.norm(path[-1] - world.target_pose[i, :2]))
            endpoint_theta = float(wrap_angle(theta + omega_cmd * times[-1] - world.target_pose[i, 2]))
            obstacle_cost = 0.0
            target_slot_angle = math.atan2(world.target_pose[i, 1], world.target_pose[i, 0])
            for point in path:
                clearance = _clearance_to_circles(point, world, include_load=False)
                if clearance < 0.0:
                    obstacle_cost += 18.0 + 50.0 * abs(clearance)
                elif clearance < 0.50:
                    obstacle_cost += 0.22 / max(clearance + 0.04, 0.025)
                radial = float(np.linalg.norm(point))
                point_angle = math.atan2(point[1], point[0])
                in_assigned_corridor = abs(float(wrap_angle(point_angle - target_slot_angle))) <= 0.42
                load_clearance = radial - world.load_radius_m - world.robot_radius_m
                if not in_assigned_corridor:
                    if load_clearance < 0.0:
                        obstacle_cost += 24.0 + 60.0 * abs(load_clearance)
                    elif load_clearance < 0.55:
                        obstacle_cost += 0.30 / max(load_clearance + 0.04, 0.025)
            wait_cost = 0.65 * min(distance, 3.0) if action == n_actions - 1 and not docked_mask[i] else 0.0
            angular_error = float(
                wrap_angle(
                    math.atan2(world.target_pose[i, 1], world.target_pose[i, 0])
                    - math.atan2(position[1], position[0])
                )
            )
            auto_side = (
                (1 if i % 2 == 0 else -1)
                if abs(abs(angular_error) - np.pi) < 0.20
                else (1 if angular_error >= 0.0 else -1)
            )
            action_side = (-1, -1, auto_side, 1, 1, 0)[action]
            switching_cost = (
                2.40
                if committed_route[i] != 0
                and action_side != 0
                and action_side != committed_route[i]
                else 0.0
            )
            costs[i, action] = (
                world.wrench_priority[i] * endpoint_distance
                + 0.12 * abs(endpoint_theta)
                + 0.07 * (v_cmd * v_cmd + 0.18 * omega_cmd * omega_cmd)
                + obstacle_cost
                + wait_cost
                + switching_cost
            )
        if docked_mask[i]:
            costs[i, :] = 20.0
            costs[i, -1] = 0.0

    cell = float(cell_size_m or (2.0 * world.robot_radius_m + world.safety_margin_m))
    resource_lookup: dict[tuple[int, int, int], int] = {}
    action_resources: list[list[list[int]]] = [[[] for _ in range(n_actions)] for _ in range(n)]
    for i in range(n):
        for action in range(n_actions):
            for time_idx, point in enumerate(paths[i][action]):
                cell_x = int(math.floor((point[0] + world.map_half_extent_m) / cell))
                cell_y = int(math.floor((point[1] + world.map_half_extent_m) / cell))
                key = (time_idx, cell_x, cell_y)
                if key not in resource_lookup:
                    resource_lookup[key] = len(resource_lookup)
                action_resources[i][action].append(resource_lookup[key])

    resources = tuple(key for key, _idx in sorted(resource_lookup.items(), key=lambda item: item[1]))
    features = np.zeros((n, n_actions, len(resources)), dtype=float)
    for i in range(n):
        for action in range(n_actions):
            for resource in action_resources[i][action]:
                features[i, action, resource] = 1.0
    capacity = np.ones(len(resources), dtype=float)
    return PrimitiveSnapshot(
        controls=controls,
        endpoints=endpoints,
        occupancy_features=features,
        costs=costs,
        capacity=capacity,
        resource_ids=resources,
    )


def occupancy(preferences: np.ndarray, snapshot: PrimitiveSnapshot) -> np.ndarray:
    return np.einsum("ia,iar->r", preferences, snapshot.occupancy_features, optimize=True)


def potential_cost(
    preferences: np.ndarray,
    snapshot: PrimitiveSnapshot,
    *,
    congestion_weight: float = 0.38,
    regularization: float = 0.04,
) -> float:
    occ = occupancy(preferences, snapshot)
    return float(
        np.sum(snapshot.costs * preferences)
        + 0.5 * congestion_weight * np.sum(occ * occ)
        + 0.5 * regularization * np.sum(preferences * preferences)
    )


def potential_gradient(
    preferences: np.ndarray,
    snapshot: PrimitiveSnapshot,
    *,
    congestion_weight: float = 0.38,
    regularization: float = 0.04,
) -> np.ndarray:
    occ = occupancy(preferences, snapshot)
    return (
        snapshot.costs
        + congestion_weight * np.einsum("iar,r->ia", snapshot.occupancy_features, occ, optimize=True)
        + regularization * preferences
    )


def _ring_matrix(n_agents: int) -> tuple[np.ndarray, int]:
    if n_agents <= 2:
        return np.full((n_agents, n_agents), 1.0 / n_agents), max(n_agents - 1, 1)
    adjacency = np.zeros((n_agents, n_agents), dtype=float)
    for i in range(n_agents):
        adjacency[i, (i - 1) % n_agents] = 1.0
        adjacency[i, (i + 1) % n_agents] = 1.0
    degree = np.sum(adjacency, axis=1)
    weights = np.zeros_like(adjacency)
    for i in range(n_agents):
        for j in range(n_agents):
            if adjacency[i, j] > 0:
                weights[i, j] = 1.0 / (1.0 + max(degree[i], degree[j]))
        weights[i, i] = 1.0 - np.sum(weights[i])
    return weights, n_agents


def _occupancy_estimates(
    preferences: np.ndarray,
    snapshot: PrimitiveSnapshot,
    *,
    graph: str,
    rounds: int,
) -> tuple[np.ndarray, float, int]:
    n = preferences.shape[0]
    local = np.einsum("ia,iar->ir", preferences, snapshot.occupancy_features, optimize=True)
    exact = np.sum(local, axis=0)
    if graph == "complete":
        return np.repeat(exact[None, :], n, axis=0), 0.0, n * max(n - 1, 0) * exact.size
    weights, edges = _ring_matrix(n)
    estimate = local.copy()
    for _ in range(max(rounds, 0)):
        estimate = weights @ estimate
    estimate *= n
    error = float(np.max(np.linalg.norm(estimate - exact[None, :], axis=1))) if exact.size else 0.0
    messages = int(max(rounds, 0) * 2 * edges * exact.size)
    return estimate, error, messages


def _revision_field(preferences: np.ndarray, payoffs: np.ndarray, protocol: str) -> np.ndarray:
    if protocol == "projected_pd":
        return payoffs
    field = np.zeros_like(preferences)
    for i in range(preferences.shape[0]):
        x = preferences[i]
        f = payoffs[i]
        mean = float(x @ f)
        if protocol == "replicator":
            field[i] = x * (f - mean)
        elif protocol == "erv_bnn":
            excess = np.maximum(f - mean, 0.0)
            field[i] = excess - x * float(np.sum(excess))
        elif protocol == "smith":
            gain = np.maximum(f[:, None] - f[None, :], 0.0)
            field[i] = gain @ x - x * np.sum(gain.T, axis=1)
        else:
            raise ValueError(f"Unknown SP4 game protocol: {protocol}")
    return field


def _kkt_residual(
    preferences: np.ndarray,
    dual: np.ndarray,
    snapshot: PrimitiveSnapshot,
    *,
    congestion_weight: float,
    regularization: float,
) -> float:
    if snapshot.capacity.size == 0:
        lambda_bar = np.zeros(0, dtype=float)
    else:
        lambda_bar = np.mean(dual, axis=0) if dual.ndim == 2 else dual
    gradient = potential_gradient(
        preferences,
        snapshot,
        congestion_weight=congestion_weight,
        regularization=regularization,
    )
    if lambda_bar.size:
        gradient += np.einsum("iar,r->ia", snapshot.occupancy_features, lambda_bar, optimize=True)
    projected = np.vstack([project_simplex(preferences[i] - gradient[i]) for i in range(preferences.shape[0])])
    stationarity = float(np.max(np.linalg.norm(preferences - projected, axis=1)))
    occ = occupancy(preferences, snapshot)
    primal = float(np.max(np.maximum(occ - snapshot.capacity, 0.0))) if occ.size else 0.0
    complementarity = float(np.max(np.abs(lambda_bar * (occ - snapshot.capacity)))) if occ.size else 0.0
    return max(stationarity, primal, complementarity)


def solve_motion_game(
    snapshot: PrimitiveSnapshot,
    *,
    protocol: str = "projected_pd",
    graph: str = "complete",
    steps: int = 28,
    primal_dt: float = 0.12,
    dual_dt: float = 0.10,
    congestion_weight: float = 0.38,
    regularization: float = 0.04,
    consensus_rounds: int = 4,
    tolerance: float = 1e-3,
    initial_preferences: np.ndarray | None = None,
) -> GameStepResult:
    """Solve one convexified receding motion game."""

    n, actions = snapshot.costs.shape
    if initial_preferences is None or initial_preferences.shape != (n, actions):
        preferences = np.full((n, actions), 1.0 / actions, dtype=float)
    else:
        preferences = np.vstack([project_simplex(row) for row in initial_preferences])
    if graph == "complete":
        dual = np.zeros((1, snapshot.capacity.size), dtype=float)
    else:
        dual = np.zeros((n, snapshot.capacity.size), dtype=float)

    potential_history: list[float] = []
    kkt_history: list[float] = []
    messages = 0
    consensus_error = 0.0
    for iteration in range(max(int(steps), 1)):
        estimates, error, step_messages = _occupancy_estimates(
            preferences,
            snapshot,
            graph=graph,
            rounds=consensus_rounds,
        )
        consensus_error = max(consensus_error, error)
        messages += step_messages
        lambda_agents = np.repeat(dual, n, axis=0) if dual.shape[0] == 1 else dual
        gradient = (
            snapshot.costs
            + congestion_weight
            * np.einsum("iar,ir->ia", snapshot.occupancy_features, estimates, optimize=True)
            + regularization * preferences
            + np.einsum("iar,ir->ia", snapshot.occupancy_features, lambda_agents, optimize=True)
        )
        payoffs = -gradient
        field = _revision_field(preferences, payoffs, protocol)
        if protocol == "projected_pd":
            preferences = np.vstack(
                [project_simplex(preferences[i] + primal_dt * field[i]) for i in range(n)]
            )
        else:
            preferences = np.vstack(
                [project_simplex(preferences[i] + primal_dt * field[i]) for i in range(n)]
            )
        if dual.shape[0] == 1:
            occ = occupancy(preferences, snapshot)
            dual[0] = np.maximum(dual[0] + dual_dt * (occ - snapshot.capacity), 0.0)
        else:
            next_estimates, _error, extra_messages = _occupancy_estimates(
                preferences,
                snapshot,
                graph=graph,
                rounds=consensus_rounds,
            )
            messages += extra_messages
            dual = np.maximum(dual + dual_dt * (next_estimates - snapshot.capacity[None, :]), 0.0)

        potential_history.append(
            potential_cost(
                preferences,
                snapshot,
                congestion_weight=congestion_weight,
                regularization=regularization,
            )
        )
        residual = _kkt_residual(
            preferences,
            dual,
            snapshot,
            congestion_weight=congestion_weight,
            regularization=regularization,
        )
        kkt_history.append(residual)
        if protocol == "projected_pd" and residual <= tolerance and iteration >= 4:
            break

    simplex_error = float(np.max(np.abs(np.sum(preferences, axis=1) - 1.0)))
    occ = occupancy(preferences, snapshot)
    capacity_violation = float(np.max(np.maximum(occ - snapshot.capacity, 0.0))) if occ.size else 0.0
    return GameStepResult(
        preferences=preferences,
        dual_prices=dual,
        potential_history=potential_history,
        kkt_history=kkt_history,
        consensus_error=consensus_error,
        messages=messages,
        iterations=len(potential_history),
        simplex_error=simplex_error,
        capacity_violation=capacity_violation,
        kkt_residual=float(kkt_history[-1]),
    )


def solve_snapshot_qp(
    snapshot: PrimitiveSnapshot,
    *,
    congestion_weight: float = 0.38,
    regularization: float = 0.04,
) -> tuple[np.ndarray, float, bool]:
    """Independent SLSQP reference for the convex snapshot potential."""

    n, actions = snapshot.costs.shape
    variables = n * actions
    features = snapshot.occupancy_features.reshape(variables, -1).T
    equality = np.zeros((n, variables), dtype=float)
    for i in range(n):
        equality[i, i * actions : (i + 1) * actions] = 1.0
    constraints: list[LinearConstraint] = [
        LinearConstraint(equality, np.ones(n), np.ones(n))
    ]
    if snapshot.capacity.size:
        constraints.append(
            LinearConstraint(
                features,
                np.full(snapshot.capacity.size, -np.inf),
                snapshot.capacity,
            )
        )

    def objective(flat: np.ndarray) -> float:
        return potential_cost(
            flat.reshape(n, actions),
            snapshot,
            congestion_weight=congestion_weight,
            regularization=regularization,
        )

    def jacobian(flat: np.ndarray) -> np.ndarray:
        return potential_gradient(
            flat.reshape(n, actions),
            snapshot,
            congestion_weight=congestion_weight,
            regularization=regularization,
        ).ravel()

    initial = np.zeros((n, actions), dtype=float)
    initial[:, -1] = 1.0
    feature_matrix = snapshot.occupancy_features.reshape(variables, -1).T
    hessian_matrix = (
        congestion_weight * (feature_matrix.T @ feature_matrix)
        + regularization * np.eye(variables)
    )
    result = minimize(
        objective,
        initial.ravel(),
        jac=jacobian,
        hess=lambda _flat: hessian_matrix,
        method="trust-constr",
        bounds=Bounds(np.zeros(variables), np.ones(variables)),
        constraints=constraints,
        options={"gtol": 1e-10, "xtol": 1e-10, "maxiter": 1200, "verbose": 0},
    )
    return result.x.reshape(n, actions), float(result.fun), bool(result.success)


def decode_conflict_aware(
    preferences: np.ndarray,
    snapshot: PrimitiveSnapshot,
    priorities: np.ndarray,
    docked: np.ndarray,
) -> tuple[np.ndarray, int]:
    """Pair-aware deterministic closure of fractional primitive preferences."""

    n, actions = preferences.shape
    selected = np.full(n, actions - 1, dtype=int)
    used: set[int] = set()
    interventions = 0
    order = np.argsort(-np.asarray(priorities, dtype=float), kind="stable")
    for i in order:
        if docked[i]:
            continue
        raw = int(np.argmax(preferences[i]))
        chosen = actions - 1
        for action in np.argsort(-preferences[i], kind="stable"):
            resources = set(np.flatnonzero(snapshot.occupancy_features[i, action] > 0.0).tolist())
            if not (resources & used):
                chosen = int(action)
                used.update(resources)
                break
        selected[i] = chosen
        interventions += int(chosen != raw)
    return selected, interventions


def _nominal_direct_controls(world: DockingWorld, state: np.ndarray, docked: np.ndarray) -> np.ndarray:
    controls = np.zeros((world.n_robots, 2), dtype=float)
    for i in range(world.n_robots):
        if docked[i]:
            continue
        delta = world.target_pose[i, :2] - state[i, :2]
        distance = float(np.linalg.norm(delta))
        desired_heading = math.atan2(delta[1], delta[0]) if distance > 1e-12 else float(world.target_pose[i, 2])
        heading_error = float(wrap_angle(desired_heading - state[i, 2]))
        if distance < 0.38:
            desired_heading = float(world.target_pose[i, 2])
            heading_error = float(wrap_angle(desired_heading - state[i, 2]))
        controls[i, 0] = min(world.max_speed_mps[i], 0.95 * distance) * max(0.08, math.cos(heading_error))
        controls[i, 1] = np.clip(1.65 * heading_error, -world.max_omega_rps[i], world.max_omega_rps[i])
    return controls


def _unicycle_to_hand(world: DockingWorld, theta: np.ndarray, controls: np.ndarray) -> np.ndarray:
    v = controls[:, 0]
    omega = controls[:, 1]
    length = world.hand_point_m
    return np.column_stack(
        [
            np.cos(theta) * v - length * np.sin(theta) * omega,
            np.sin(theta) * v + length * np.cos(theta) * omega,
        ]
    )


def _hand_to_unicycle(world: DockingWorld, theta: np.ndarray, hand_velocity: np.ndarray) -> np.ndarray:
    length = world.hand_point_m
    controls = np.zeros_like(hand_velocity)
    controls[:, 0] = np.cos(theta) * hand_velocity[:, 0] + np.sin(theta) * hand_velocity[:, 1]
    controls[:, 1] = (
        -np.sin(theta) * hand_velocity[:, 0] + np.cos(theta) * hand_velocity[:, 1]
    ) / max(length, 1e-9)
    controls[:, 0] = np.clip(controls[:, 0], 0.0, world.max_speed_mps)
    controls[:, 1] = np.clip(controls[:, 1], -world.max_omega_rps, world.max_omega_rps)
    return controls


def _hand_points(world: DockingWorld, state: np.ndarray) -> np.ndarray:
    return state[:, :2] + world.hand_point_m * np.column_stack(
        [np.cos(state[:, 2]), np.sin(state[:, 2])]
    )


def _barrier_max_violation(
    world: DockingWorld,
    state: np.ndarray,
    hand_velocity: np.ndarray,
    *,
    gamma: float = 2.6,
) -> float:
    points = _hand_points(world, state)
    safe_pair = 2.0 * world.robot_radius_m + world.safety_margin_m + 2.0 * abs(world.hand_point_m)
    max_violation = 0.0
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            delta = points[i] - points[j]
            h = float(delta @ delta - safe_pair * safe_pair)
            lhs = float(2.0 * delta @ (hand_velocity[i] - hand_velocity[j]) + gamma * h)
            max_violation = max(max_violation, -lhs)
        obstacle_set = [(obstacle, False) for obstacle in world.obstacles]
        obstacle_set.append((np.asarray([0.0, 0.0, world.load_radius_m]), True))
        for obstacle, is_load in obstacle_set:
            delta = points[i] - obstacle[:2]
            radius = float(
                obstacle[2]
                + world.robot_radius_m
                + world.safety_margin_m
                + abs(world.hand_point_m)
            )
            h = float(delta @ delta - radius * radius)
            lhs = float(2.0 * delta @ hand_velocity[i] + gamma * h)
            max_violation = max(max_violation, -lhs)
    return max_violation


def barrier_project(
    world: DockingWorld,
    state: np.ndarray,
    raw_hand_velocity: np.ndarray,
    docked: np.ndarray,
    *,
    gamma: float = 2.6,
    iterations: int = 18,
    dt_s: float = 0.16,
) -> tuple[np.ndarray, float, int]:
    """Alternating projection onto pair and circular-obstacle CBF half-spaces."""

    velocity = np.asarray(raw_hand_velocity, dtype=float).copy()
    points = _hand_points(world, state)
    movable = ~np.asarray(docked, dtype=bool)
    safe_pair = 2.0 * world.robot_radius_m + world.safety_margin_m + 2.0 * abs(world.hand_point_m)
    interventions = 0
    for _ in range(max(iterations, 1)):
        changed = False
        for i in range(world.n_robots):
            for j in range(i + 1, world.n_robots):
                delta = points[i] - points[j]
                norm2 = float(delta @ delta)
                if norm2 < 1e-12:
                    continue
                h = norm2 - safe_pair * safe_pair
                lhs = float(2.0 * delta @ (velocity[i] - velocity[j]) + gamma * h)
                if lhs < 0.0:
                    deficit = -lhs
                    if movable[i] and movable[j]:
                        correction = deficit * delta / (4.0 * norm2)
                        velocity[i] += correction
                        velocity[j] -= correction
                    elif movable[i]:
                        velocity[i] += deficit * delta / (2.0 * norm2)
                    elif movable[j]:
                        velocity[j] -= deficit * delta / (2.0 * norm2)
                    changed = True
                    interventions += 1
        obstacle_set = [(obstacle, False) for obstacle in world.obstacles]
        obstacle_set.append((np.asarray([0.0, 0.0, world.load_radius_m]), True))
        for i in range(world.n_robots):
            if not movable[i]:
                velocity[i] = 0.0
                continue
            for obstacle, is_load in obstacle_set:
                delta = points[i] - obstacle[:2]
                norm2 = float(delta @ delta)
                if norm2 < 1e-12:
                    continue
                radius = float(
                    obstacle[2]
                    + world.robot_radius_m
                    + world.safety_margin_m
                    + abs(world.hand_point_m)
                )
                h = norm2 - radius * radius
                lhs = float(2.0 * delta @ velocity[i] + gamma * h)
                if lhs < 0.0:
                    velocity[i] += (-lhs) * delta / (2.0 * norm2)
                    changed = True
                    interventions += 1
        reachable_controls = _hand_to_unicycle(world, state[:, 2], velocity)
        reachable_controls[:, 0] = np.clip(
            reachable_controls[:, 0],
            np.maximum(0.0, state[:, 3] - world.max_accel_mps2 * dt_s),
            np.minimum(world.max_speed_mps, state[:, 3] + world.max_accel_mps2 * dt_s),
        )
        reachable_controls[:, 1] = np.clip(
            reachable_controls[:, 1],
            np.maximum(-world.max_omega_rps, state[:, 4] - world.max_alpha_rps2 * dt_s),
            np.minimum(world.max_omega_rps, state[:, 4] + world.max_alpha_rps2 * dt_s),
        )
        bounded = _unicycle_to_hand(world, state[:, 2], reachable_controls)
        velocity[movable] = bounded[movable]
        velocity[~movable] = 0.0
        if not changed:
            break
    residual = _barrier_max_violation(world, state, velocity, gamma=gamma)
    return velocity, residual, interventions


def _apf_hand_velocity(
    world: DockingWorld,
    state: np.ndarray,
    direct_controls: np.ndarray,
    docked: np.ndarray,
) -> np.ndarray:
    velocity = _unicycle_to_hand(world, state[:, 2], direct_controls)
    points = _hand_points(world, state)
    influence = 1.05
    for i in range(world.n_robots):
        if docked[i]:
            velocity[i] = 0.0
            continue
        for j in range(world.n_robots):
            if i == j:
                continue
            delta = points[i] - points[j]
            distance = float(np.linalg.norm(delta))
            if 1e-8 < distance < influence:
                velocity[i] += 0.18 * (1.0 / distance - 1.0 / influence) * delta / (distance**3)
        obstacle_set = list(world.obstacles)
        for obstacle in obstacle_set:
            delta = points[i] - obstacle[:2]
            center_distance = float(np.linalg.norm(delta))
            clearance = center_distance - obstacle[2] - world.robot_radius_m
            if center_distance > 1e-8 and clearance < influence:
                effective = max(clearance, 0.04)
                velocity[i] += 0.16 * (1.0 / effective - 1.0 / influence) * delta / (center_distance * effective**2)
    return _unicycle_to_hand(world, state[:, 2], _hand_to_unicycle(world, state[:, 2], velocity))


def _rvo_proxy_hand_velocity(
    world: DockingWorld,
    state: np.ndarray,
    direct_controls: np.ndarray,
    docked: np.ndarray,
    *,
    horizon_s: float = 1.25,
) -> np.ndarray:
    velocity = _unicycle_to_hand(world, state[:, 2], direct_controls)
    points = _hand_points(world, state)
    safe = 2.0 * world.robot_radius_m + world.safety_margin_m
    for i in range(world.n_robots):
        if docked[i]:
            velocity[i] = 0.0
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            future_delta = (points[i] + horizon_s * velocity[i]) - (points[j] + horizon_s * velocity[j])
            distance = float(np.linalg.norm(future_delta))
            if distance < safe * 1.10 and distance > 1e-8:
                tangent = np.asarray([-future_delta[1], future_delta[0]]) / distance
                sign = 1.0 if (i + j) % 2 == 0 else -1.0
                correction = sign * 0.24 * (safe * 1.10 - distance) / max(horizon_s, 1e-6) * tangent
                if not docked[i]:
                    velocity[i] += correction
                if not docked[j]:
                    velocity[j] -= correction
    return _unicycle_to_hand(world, state[:, 2], _hand_to_unicycle(world, state[:, 2], velocity))


def _execute_dynamics(
    world: DockingWorld,
    state: np.ndarray,
    desired_controls: np.ndarray,
    docked: np.ndarray,
    dt_s: float,
) -> tuple[np.ndarray, np.ndarray, float, int]:
    """Apply acceleration and wheel-torque bounds, then integrate the unicycle."""

    n = world.n_robots
    next_state = state.copy()
    desired_a = np.clip(
        (desired_controls[:, 0] - state[:, 3]) / dt_s,
        -world.max_accel_mps2,
        world.max_accel_mps2,
    )
    desired_alpha = np.clip(
        (desired_controls[:, 1] - state[:, 4]) / dt_s,
        -world.max_alpha_rps2,
        world.max_alpha_rps2,
    )
    force = world.mass_kg * desired_a
    yaw_moment = world.inertia_kgm2 * desired_alpha
    right_force = 0.5 * force + yaw_moment / world.axle_length_m
    left_force = 0.5 * force - yaw_moment / world.axle_length_m
    raw_torque_right = world.wheel_radius_m * right_force
    raw_torque_left = world.wheel_radius_m * left_force
    torque_right = np.clip(raw_torque_right, -world.max_wheel_torque_nm, world.max_wheel_torque_nm)
    torque_left = np.clip(raw_torque_left, -world.max_wheel_torque_nm, world.max_wheel_torque_nm)
    saturated = int(
        np.count_nonzero(np.abs(raw_torque_right - torque_right) > 1e-10)
        + np.count_nonzero(np.abs(raw_torque_left - torque_left) > 1e-10)
    )
    actual_force = (torque_right + torque_left) / world.wheel_radius_m
    actual_moment = (
        (torque_right - torque_left) / world.wheel_radius_m * world.axle_length_m / 2.0
    )
    actual_a = actual_force / world.mass_kg
    actual_alpha = actual_moment / world.inertia_kgm2
    v_new = np.clip(state[:, 3] + dt_s * actual_a, 0.0, world.max_speed_mps)
    omega_new = np.clip(state[:, 4] + dt_s * actual_alpha, -world.max_omega_rps, world.max_omega_rps)
    v_new[docked] = 0.0
    omega_new[docked] = 0.0
    theta_mid = state[:, 2] + 0.5 * dt_s * omega_new
    next_state[:, 0] = state[:, 0] + dt_s * v_new * np.cos(theta_mid)
    next_state[:, 1] = state[:, 1] + dt_s * v_new * np.sin(theta_mid)
    next_state[:, 2] = wrap_angle(state[:, 2] + dt_s * omega_new)
    next_state[:, 3] = v_new
    next_state[:, 4] = omega_new
    wheel_speed_right = (v_new + 0.5 * world.axle_length_m * omega_new) / world.wheel_radius_m
    wheel_speed_left = (v_new - 0.5 * world.axle_length_m * omega_new) / world.wheel_radius_m
    energy_wh = float(
        np.sum(np.abs(torque_right * wheel_speed_right) + np.abs(torque_left * wheel_speed_left))
        * dt_s
        / 3600.0
    )
    executed_controls = np.column_stack([v_new, omega_new])
    return next_state, executed_controls, energy_wh, saturated


def _segment_point_distance(start: np.ndarray, end: np.ndarray, point: np.ndarray) -> float:
    delta = end - start
    denom = float(delta @ delta)
    if denom <= 1e-14:
        return float(np.linalg.norm(start - point))
    fraction = float(np.clip((point - start) @ delta / denom, 0.0, 1.0))
    return float(np.linalg.norm(start + fraction * delta - point))


def _swept_clearance(world: DockingWorld, before: np.ndarray, after: np.ndarray) -> tuple[float, bool]:
    min_clearance = float("inf")
    collision = False
    safe_pair_radius = 2.0 * world.robot_radius_m
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            rel_start = before[i, :2] - before[j, :2]
            rel_end = after[i, :2] - after[j, :2]
            distance = _segment_point_distance(rel_start, rel_end, np.zeros(2))
            clearance = distance - safe_pair_radius
            min_clearance = min(min_clearance, clearance)
            collision = collision or clearance < 0.0
        obstacle_set = list(world.obstacles)
        obstacle_set.append(np.asarray([0.0, 0.0, world.load_radius_m]))
        for obstacle in obstacle_set:
            distance = _segment_point_distance(before[i, :2], after[i, :2], obstacle[:2])
            clearance = distance - obstacle[2] - world.robot_radius_m
            min_clearance = min(min_clearance, clearance)
            collision = collision or clearance < -1e-5
        boundary = world.map_half_extent_m - float(np.max(np.abs(after[i, :2]))) - world.robot_radius_m
        min_clearance = min(min_clearance, boundary)
        collision = collision or boundary < 0.0
    return min_clearance, collision


def simulate_docking(
    world: DockingWorld,
    method: str,
    *,
    dt_s: float = 0.16,
    horizon_s: float = 22.0,
    game_steps: int = 24,
    replan_interval_steps: int = 3,
    central_steps: int = 70,
    primal_dt: float = 0.12,
    dual_dt: float = 0.10,
    congestion_weight: float = 0.38,
    regularization: float = 0.04,
    consensus_rounds: int = 4,
    barrier_gamma: float = 2.6,
    barrier_iterations: int = 18,
    docking_position_tolerance_m: float = 0.18,
    docking_orientation_tolerance_rad: float = 0.24,
    docking_speed_tolerance_mps: float = 0.16,
) -> DockingRunResult:
    """Execute one method on a fixed world without post-integration repair."""

    if method not in METHOD_LABELS:
        raise ValueError(f"Unknown SP4 docking method: {method}")
    start = time.perf_counter()
    max_steps = int(math.ceil(horizon_s / dt_s))
    state = world.initial_state.copy()
    docked = np.zeros(world.n_robots, dtype=bool)
    arrival_times = np.full(world.n_robots, np.nan, dtype=float)
    preference_warm: np.ndarray | None = None
    held_raw_controls = np.zeros((world.n_robots, 2), dtype=float)
    route_commitment = np.zeros(world.n_robots, dtype=int)
    positions = [state[:, :2].copy()]
    potential_trace: list[float] = []
    kkt_trace: list[float] = []
    messages = 0
    max_simplex_error = 0.0
    max_capacity_violation = 0.0
    max_consensus_error = 0.0
    guard_interventions = 0
    closure_interventions = 0
    guard_intervention_norm = 0.0
    raw_barrier_violations = 0
    exec_barrier_violations = 0
    max_exec_barrier_residual = 0.0
    torque_saturation_events = 0
    energy_wh = 0.0
    path_length_m = 0.0
    min_clearance = float("inf")
    any_collision = False
    time_to_wrench_feasible = math.nan
    priority_threshold = 0.80 * float(np.sum(world.wrench_priority))

    for step in range(max_steps):
        direct_controls = _nominal_direct_controls(world, state, docked)
        direct_hand = _unicycle_to_hand(world, state[:, 2], direct_controls)
        if method == "direct_to_slot":
            raw_hand = direct_hand
        elif method == "apf_navigation":
            raw_hand = _apf_hand_velocity(world, state, direct_controls, docked)
        elif method == "rvo_proxy":
            raw_hand = _rvo_proxy_hand_velocity(world, state, direct_controls, docked)
        elif method == "cbf_qp":
            raw_hand = direct_hand
        else:
            if step % max(replan_interval_steps, 1) == 0 or preference_warm is None:
                required_route_clearance = (
                    world.load_radius_m
                    + world.robot_radius_m
                    + world.safety_margin_m
                    + abs(world.hand_point_m)
                )
                for i in range(world.n_robots):
                    chord_clearance = _segment_point_distance(
                        state[i, :2],
                        world.target_pose[i, :2],
                        np.zeros(2),
                    )
                    if chord_clearance >= required_route_clearance:
                        route_commitment[i] = 0
                snapshot = build_primitive_snapshot(
                    world,
                    state,
                    docked,
                    route_commitment=route_commitment,
                )
                protocol, graph = GAME_METHODS[method]
                local_steps = central_steps if method == "central_potential_reference" else game_steps
                game = solve_motion_game(
                    snapshot,
                    protocol=protocol,
                    graph=graph,
                    steps=local_steps,
                    primal_dt=primal_dt,
                    dual_dt=dual_dt,
                    congestion_weight=congestion_weight,
                    regularization=regularization,
                    consensus_rounds=consensus_rounds,
                    initial_preferences=preference_warm,
                )
                preference_warm = game.preferences
                if method == "nash_pd_exact_raw":
                    actions = np.argmax(game.preferences, axis=1)
                else:
                    actions, closure_count = decode_conflict_aware(
                        game.preferences,
                        snapshot,
                        world.wrench_priority,
                        docked,
                    )
                    closure_interventions += closure_count
                for i, action in enumerate(actions):
                    if route_commitment[i] != 0 or docked[i] or int(action) == 5:
                        continue
                    chord_clearance = _segment_point_distance(
                        state[i, :2],
                        world.target_pose[i, :2],
                        np.zeros(2),
                    )
                    if chord_clearance < required_route_clearance:
                        angular_error = float(
                            wrap_angle(
                                math.atan2(world.target_pose[i, 1], world.target_pose[i, 0])
                                - math.atan2(state[i, 1], state[i, 0])
                            )
                        )
                        auto_side = (
                            (1 if i % 2 == 0 else -1)
                            if abs(abs(angular_error) - np.pi) < 0.20
                            else (1 if angular_error >= 0.0 else -1)
                        )
                        route_commitment[i] = (-1, -1, auto_side, 1, 1, 0)[int(action)]
                held_raw_controls = snapshot.controls[np.arange(world.n_robots), actions]
                potential_trace.append(float(game.potential_history[-1]))
                kkt_trace.append(game.kkt_residual)
                messages += game.messages
                max_simplex_error = max(max_simplex_error, game.simplex_error)
                max_capacity_violation = max(max_capacity_violation, game.capacity_violation)
                max_consensus_error = max(max_consensus_error, game.consensus_error)
            raw_controls = held_raw_controls.copy()
            raw_controls[docked] = 0.0
            raw_hand = _unicycle_to_hand(world, state[:, 2], raw_controls)

        raw_residual = _barrier_max_violation(world, state, raw_hand, gamma=barrier_gamma)
        if raw_residual > 1e-7:
            raw_barrier_violations += 1

        if method in GUARDED_METHODS:
            safe_hand, safe_residual, interventions = barrier_project(
                world,
                state,
                raw_hand,
                docked,
                gamma=barrier_gamma,
                iterations=barrier_iterations,
                dt_s=dt_s,
            )
            guard_interventions += interventions
            guard_intervention_norm += float(np.linalg.norm(safe_hand - raw_hand))
        else:
            safe_hand = raw_hand
            safe_residual = raw_residual

        desired_controls = _hand_to_unicycle(world, state[:, 2], safe_hand)
        before = state.copy()
        state, executed_controls, step_energy, saturated = _execute_dynamics(
            world,
            state,
            desired_controls,
            docked,
            dt_s,
        )
        energy_wh += step_energy
        torque_saturation_events += saturated
        executed_hand = _unicycle_to_hand(world, before[:, 2], executed_controls)
        exec_residual = _barrier_max_violation(
            world,
            before,
            executed_hand,
            gamma=barrier_gamma,
        )
        max_exec_barrier_residual = max(max_exec_barrier_residual, exec_residual)
        if method in GUARDED_METHODS and exec_residual > 1e-5:
            exec_barrier_violations += 1

        path_length_m += float(np.sum(np.linalg.norm(state[:, :2] - before[:, :2], axis=1)))
        step_clearance, collided = _swept_clearance(world, before, state)
        min_clearance = min(min_clearance, step_clearance)
        any_collision = any_collision or collided
        positions.append(state[:, :2].copy())

        position_error = np.linalg.norm(state[:, :2] - world.target_pose[:, :2], axis=1)
        orientation_error = np.abs(wrap_angle(state[:, 2] - world.target_pose[:, 2]))
        newly_docked = (
            (~docked)
            & (position_error <= docking_position_tolerance_m)
            & (orientation_error <= docking_orientation_tolerance_rad)
            & (np.abs(state[:, 3]) <= docking_speed_tolerance_mps)
        )
        if np.any(newly_docked):
            arrival_times[newly_docked] = (step + 1) * dt_s
            docked[newly_docked] = True
            state[newly_docked, 3:] = 0.0

        if math.isnan(time_to_wrench_feasible) and float(np.sum(world.wrench_priority[docked])) >= priority_threshold:
            time_to_wrench_feasible = (step + 1) * dt_s
        if np.all(docked) or any_collision:
            break

    position_error = np.linalg.norm(state[:, :2] - world.target_pose[:, :2], axis=1)
    orientation_error = np.abs(wrap_angle(state[:, 2] - world.target_pose[:, 2]))
    arrival_success = bool(np.all(docked))
    safe_success = bool(arrival_success and not any_collision)
    docking_time = float(np.nanmax(arrival_times)) if arrival_success else float(horizon_s)
    if math.isnan(time_to_wrench_feasible):
        time_to_wrench_feasible = float(horizon_s)
    kkt_array = np.asarray(kkt_trace, dtype=float)
    runtime = time.perf_counter() - start
    return DockingRunResult(
        method=method,
        scenario=world.scenario,
        seed=world.seed,
        n_robots=world.n_robots,
        safe_docking_success=safe_success,
        arrival_success=arrival_success,
        any_collision=any_collision,
        timeout=not arrival_success and not any_collision,
        docking_time_s=docking_time,
        time_to_wrench_feasible_s=float(time_to_wrench_feasible),
        min_clearance_m=float(min_clearance),
        final_position_error_m=float(np.mean(position_error)),
        final_orientation_error_rad=float(np.mean(orientation_error)),
        energy_wh=float(energy_wh),
        path_length_m=float(path_length_m),
        guard_interventions=int(guard_interventions),
        closure_interventions=int(closure_interventions),
        guard_intervention_norm=float(guard_intervention_norm),
        raw_barrier_violations=int(raw_barrier_violations),
        exec_barrier_violations=int(exec_barrier_violations),
        max_exec_barrier_residual=float(max_exec_barrier_residual),
        torque_saturation_events=int(torque_saturation_events),
        mean_kkt_residual=float(np.mean(kkt_array)) if kkt_array.size else math.nan,
        final_kkt_residual=float(kkt_array[-1]) if kkt_array.size else math.nan,
        max_simplex_error=float(max_simplex_error),
        max_capacity_violation=float(max_capacity_violation),
        consensus_error=float(max_consensus_error),
        messages=int(messages),
        runtime_s=float(runtime),
        steps=len(positions) - 1,
        positions=np.asarray(positions),
        potential_trace=np.asarray(potential_trace, dtype=float),
        kkt_trace=kkt_array,
    )


def _run_row(result: DockingRunResult) -> dict[str, Any]:
    row = asdict(result)
    row.pop("positions")
    row.pop("potential_trace")
    row.pop("kkt_trace")
    for key in (
        "safe_docking_success",
        "arrival_success",
        "any_collision",
        "timeout",
    ):
        row[key] = int(bool(row[key]))
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int = 47011, draws: int = 2000) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    samples = rng.choice(data, size=(draws, data.size), replace=True)
    means = np.mean(samples, axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = [
        "safe_docking_success",
        "arrival_success",
        "any_collision",
        "timeout",
        "docking_time_s",
        "time_to_wrench_feasible_s",
        "min_clearance_m",
        "energy_wh",
        "guard_intervention_norm",
        "closure_interventions",
        "exec_barrier_violations",
        "final_kkt_residual",
        "messages",
        "runtime_s",
    ]
    summary: list[dict[str, Any]] = []
    methods = list(dict.fromkeys(str(row["method"]) for row in rows))
    for method_idx, method in enumerate(methods):
        subset = [row for row in rows if row["method"] == method]
        record: dict[str, Any] = {
            "method": method,
            "label": METHOD_LABELS.get(method, method),
            "n": len(subset),
        }
        for metric_idx, metric in enumerate(metrics):
            values = np.asarray([float(row[metric]) for row in subset], dtype=float)
            finite = values[np.isfinite(values)]
            record[metric] = float(np.mean(finite)) if finite.size else math.nan
            low, high = _bootstrap_mean_ci(
                finite,
                seed=47011 + 97 * method_idx + metric_idx,
            )
            record[f"{metric}_ci_low"] = low
            record[f"{metric}_ci_high"] = high
        summary.append(record)
    return summary


def _paired_vectors(
    rows: list[dict[str, Any]],
    method_a: str,
    method_b: str,
    metric: str,
) -> tuple[np.ndarray, np.ndarray]:
    keys = ("scenario", "seed", "n_robots")
    lookup_a = {
        tuple(row[key] for key in keys): float(row[metric])
        for row in rows
        if row["method"] == method_a
    }
    lookup_b = {
        tuple(row[key] for key in keys): float(row[metric])
        for row in rows
        if row["method"] == method_b
    }
    common = sorted(set(lookup_a) & set(lookup_b))
    return (
        np.asarray([lookup_a[key] for key in common], dtype=float),
        np.asarray([lookup_b[key] for key in common], dtype=float),
    )


def _holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.ones(len(p_values), dtype=float)
    running = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * p_values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def evaluate_hypotheses(
    rows: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    p_values: list[float] = []
    for index, hypothesis in enumerate(hypotheses):
        a, b = _paired_vectors(
            rows,
            str(hypothesis["method_a"]),
            str(hypothesis["method_b"]),
            str(hypothesis["metric"]),
        )
        difference = a - b
        rng = np.random.default_rng(49001 + index)
        if difference.size:
            samples = rng.choice(difference, size=(3000, difference.size), replace=True)
            boot = np.mean(samples, axis=1)
            ci_low, ci_high = np.quantile(boot, [0.025, 0.975])
        else:
            ci_low = ci_high = math.nan
        binary = bool(np.all(np.isin(np.unique(np.concatenate([a, b])), [0.0, 1.0]))) if a.size else False
        direction = str(hypothesis.get("direction", "different"))
        if binary and a.size:
            positive = int(np.sum((a == 1.0) & (b == 0.0)))
            negative = int(np.sum((a == 0.0) & (b == 1.0)))
            discordant = positive + negative
            if discordant:
                alternative = "greater" if direction == "greater" else "less" if direction == "less" else "two-sided"
                p_value = float(binomtest(positive, discordant, 0.5, alternative=alternative).pvalue)
            else:
                p_value = 1.0
            statistic = float(positive - negative)
        elif a.size and np.any(np.abs(difference) > 1e-12):
            alternative = "greater" if direction == "greater" else "less" if direction == "less" else "two-sided"
            test = wilcoxon(difference, alternative=alternative, zero_method="wilcox")
            statistic = float(test.statistic)
            p_value = float(test.pvalue)
        else:
            statistic = 0.0
            p_value = 1.0
        p_values.append(p_value)
        results.append(
            {
                "hypothesis": str(hypothesis["id"]),
                "metric": str(hypothesis["metric"]),
                "method_a": str(hypothesis["method_a"]),
                "method_b": str(hypothesis["method_b"]),
                "direction": direction,
                "n_pairs": int(a.size),
                "mean_a": float(np.mean(a)) if a.size else math.nan,
                "mean_b": float(np.mean(b)) if b.size else math.nan,
                "mean_difference": float(np.mean(difference)) if difference.size else math.nan,
                "ci95_low": float(ci_low),
                "ci95_high": float(ci_high),
                "statistic": statistic,
                "p_raw": p_value,
            }
        )
    adjusted = _holm_adjust(p_values)
    for result, p_holm in zip(results, adjusted):
        result["p_holm"] = p_holm
        result["supported"] = bool(p_holm < 0.05)
    return results


def _plot_performance(summary: list[dict[str, Any]], path: Path) -> None:
    labels = [str(row["label"]) for row in summary]
    success = np.asarray([row["safe_docking_success"] for row in summary], dtype=float)
    collision = np.asarray([row["any_collision"] for row in summary], dtype=float)
    success_low = np.asarray([row["safe_docking_success_ci_low"] for row in summary])
    success_high = np.asarray([row["safe_docking_success_ci_high"] for row in summary])
    collision_low = np.asarray([row["any_collision_ci_low"] for row in summary])
    collision_high = np.asarray([row["any_collision_ci_high"] for row in summary])
    y = np.arange(len(labels))
    colors = ["#EE7733" if "Nash" in label else "#0077BB" if "Potencial" in label else "#009988" if "CBF" in label else "#777777" for label in labels]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.5), sharey=True)
    axes[0].barh(y, success, color=colors, alpha=0.88)
    axes[0].errorbar(success, y, xerr=[success - success_low, success_high - success], fmt="none", ecolor="black", capsize=2, lw=0.8)
    axes[0].set_xlabel("Éxito de acoplamiento seguro")
    axes[0].set_xlim(0.0, 1.03)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[1].barh(y, collision, color=colors, alpha=0.88)
    axes[1].errorbar(collision, y, xerr=[collision - collision_low, collision_high - collision], fmt="none", ecolor="black", capsize=2, lw=0.8)
    axes[1].set_xlabel("Ejecuciones con colisión")
    axes[1].set_xlim(0.0, max(0.12, float(np.max(collision_high)) * 1.08))
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x", alpha=0.20)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_tradeoff(summary: list[dict[str, Any]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
    for row in summary:
        label = str(row["label"])
        highlight = "Nash" in label
        axes[0].scatter(
            row["docking_time_s"],
            row["energy_wh"],
            s=60 if highlight else 38,
            marker="D" if highlight else "o",
            color="#EE7733" if highlight else "#0077BB",
            edgecolor="black",
            linewidth=0.4,
        )
        axes[0].annotate(label, (row["docking_time_s"], row["energy_wh"]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        if np.isfinite(row["final_kkt_residual"]):
            axes[1].scatter(
                row["guard_intervention_norm"],
                row["final_kkt_residual"],
                s=60 if highlight else 38,
                marker="D" if highlight else "o",
                color="#EE7733" if highlight else "#009988",
                edgecolor="black",
                linewidth=0.4,
            )
            axes[1].annotate(
                label,
                (row["guard_intervention_norm"], row["final_kkt_residual"]),
                fontsize=7,
                xytext=(3, 3),
                textcoords="offset points",
            )
    axes[0].set_xlabel("Tiempo truncado de acoplamiento (s)")
    axes[0].set_ylabel("Energía de ruedas (Wh)")
    axes[1].set_xlabel("Intervención acumulada de barrera")
    axes[1].set_ylabel("Residual KKT final")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_scenario_matrix(rows: list[dict[str, Any]], path: Path) -> None:
    scenarios = list(dict.fromkeys(str(row["scenario"]) for row in rows))
    methods = list(dict.fromkeys(str(row["method"]) for row in rows))
    success = np.zeros((len(methods), len(scenarios)), dtype=float)
    collision = np.zeros_like(success)
    for i, method in enumerate(methods):
        for j, scenario in enumerate(scenarios):
            subset = [
                row for row in rows
                if row["method"] == method and row["scenario"] == scenario
            ]
            success[i, j] = np.mean([float(row["safe_docking_success"]) for row in subset])
            collision[i, j] = np.mean([float(row["any_collision"]) for row in subset])

    labels = [METHOD_LABELS.get(method, method) for method in methods]
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12.0, max(4.8, 0.43 * len(methods))),
        sharey=True,
    )
    for ax, matrix, title, cmap in (
        (axes[0], success, "Exito seguro", "Blues"),
        (axes[1], collision, "Colision barrida", "Reds"),
    ):
        image = ax.imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", cmap=cmap)
        ax.set_title(title)
        ax.set_xticks(np.arange(len(scenarios)), scenarios, rotation=35, ha="right")
        ax.set_yticks(np.arange(len(methods)), labels)
        for i in range(len(methods)):
            for j in range(len(scenarios)):
                value = matrix[i, j]
                ax.text(
                    j,
                    i,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if value >= 0.58 else "black",
                )
        fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_scaling(rows: list[dict[str, Any]], path: Path) -> None:
    counts = sorted({int(row["n_robots"]) for row in rows})
    methods = [
        method
        for method in dict.fromkeys(str(row["method"]) for row in rows)
        if method in GAME_METHODS
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.9))
    colors = plt.cm.tab10(np.linspace(0.0, 1.0, max(len(methods), 1)))
    for color, method in zip(colors, methods):
        runtime: list[float] = []
        messages: list[float] = []
        success: list[float] = []
        for count in counts:
            subset = [
                row for row in rows
                if row["method"] == method and int(row["n_robots"]) == count
            ]
            runtime.append(float(np.mean([float(row["runtime_s"]) for row in subset])))
            messages.append(float(np.mean([float(row["messages"]) for row in subset])))
            success.append(float(np.mean([float(row["safe_docking_success"]) for row in subset])))
        label = METHOD_LABELS.get(method, method)
        axes[0].plot(counts, runtime, marker="o", lw=1.4, label=label, color=color)
        axes[1].plot(counts, messages, marker="o", lw=1.4, color=color)
        axes[2].plot(counts, success, marker="o", lw=1.4, color=color)
    axes[0].set_ylabel("Tiempo por ejecucion (s)")
    axes[1].set_ylabel("Mensajes contabilizados")
    axes[1].set_yscale("log")
    axes[2].set_ylabel("Exito seguro")
    axes[2].set_ylim(-0.02, 1.02)
    for ax in axes:
        ax.set_xlabel("Numero de robots")
        ax.set_xticks(counts)
        ax.grid(alpha=0.20)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(fontsize=6.5, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)

def _plot_trajectory(world: DockingWorld, results: list[DockingRunResult], path: Path) -> None:
    selected = []
    for method in ("direct_to_slot", "cbf_qp", "nash_pd_exact", "replicator_primitives"):
        match = next((result for result in results if result.method == method), None)
        if match is not None:
            selected.append(match)
    fig, axes = plt.subplots(2, 2, figsize=(8.2, 8.0), sharex=True, sharey=True)
    for ax, result in zip(axes.ravel(), selected):
        load = plt.Circle((0.0, 0.0), world.load_radius_m, color="#999999", alpha=0.35)
        ax.add_patch(load)
        for obstacle in world.obstacles:
            ax.add_patch(plt.Circle(obstacle[:2], obstacle[2], color="#CC3311", alpha=0.25))
        for robot in range(world.n_robots):
            ax.plot(result.positions[:, robot, 0], result.positions[:, robot, 1], lw=1.1)
            ax.scatter(world.target_pose[robot, 0], world.target_pose[robot, 1], marker="x", s=22, color="black")
        ax.set_title(METHOD_LABELS[result.method], fontsize=9)
        ax.set_aspect("equal")
        ax.grid(alpha=0.16)
        ax.set_xlim(-world.map_half_extent_m, world.map_half_extent_m)
        ax.set_ylim(-world.map_half_extent_m, world.map_half_extent_m)
    for ax in axes[-1]:
        ax.set_xlabel("x (m)")
    for ax in axes[:, 0]:
        ax.set_ylabel("y (m)")
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _plot_theory(audit_trace: GameStepResult, qp_value: float, path: Path) -> None:
    iterations = np.arange(1, len(audit_trace.potential_history) + 1)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.8))
    axes[0].plot(iterations, audit_trace.potential_history, color="#0077BB", lw=1.5)
    axes[0].axhline(qp_value, color="#CC3311", ls="--", lw=1.0, label="QP independiente")
    axes[0].set_xlabel("Iteración primal-dual")
    axes[0].set_ylabel("Coste potencial")
    axes[0].legend(frameon=False, fontsize=8)
    axes[1].semilogy(iterations, np.maximum(audit_trace.kkt_history, 1e-12), color="#EE7733", lw=1.5)
    axes[1].set_xlabel("Iteración primal-dual")
    axes[1].set_ylabel("Residual KKT")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _theory_audit(
    config: dict[str, Any],
    worlds: list[DockingWorld],
    *,
    output_dir: Path,
) -> tuple[dict[str, Any], GameStepResult, float]:
    game_cfg = dict(config.get("game", {}))
    audit_worlds = max(1, min(int(config.get("audit_worlds", 8)), len(worlds)))
    max_simplex = 0.0
    max_capacity = 0.0
    max_qp_gap = 0.0
    max_potential_identity_error = 0.0
    qp_failures = 0
    representative: GameStepResult | None = None
    representative_qp = math.nan
    for world_index, world in enumerate(worlds[:audit_worlds]):
        snapshot = build_primitive_snapshot(world, world.initial_state)
        result = solve_motion_game(
            snapshot,
            protocol="projected_pd",
            graph="complete",
            steps=int(game_cfg.get("audit_steps", 260)),
            primal_dt=float(game_cfg.get("primal_dt", 0.12)),
            dual_dt=float(game_cfg.get("dual_dt", 0.10)),
            congestion_weight=float(game_cfg.get("congestion_weight", 0.38)),
            regularization=float(game_cfg.get("regularization", 0.04)),
            consensus_rounds=int(game_cfg.get("consensus_rounds", 4)),
            tolerance=float(game_cfg.get("tolerance", 1e-3)),
        )
        optimum, qp_value, success = solve_snapshot_qp(
            snapshot,
            congestion_weight=float(game_cfg.get("congestion_weight", 0.38)),
            regularization=float(game_cfg.get("regularization", 0.04)),
        )
        if not success:
            qp_failures += 1
        value = potential_cost(
            result.preferences,
            snapshot,
            congestion_weight=float(game_cfg.get("congestion_weight", 0.38)),
            regularization=float(game_cfg.get("regularization", 0.04)),
        )
        max_qp_gap = max(max_qp_gap, max(0.0, value - qp_value))
        max_simplex = max(max_simplex, result.simplex_error)
        max_capacity = max(max_capacity, result.capacity_violation)

        rng = np.random.default_rng(51000 + world_index)
        x = np.full_like(result.preferences, 1.0 / result.preferences.shape[1])
        i = world_index % world.n_robots
        candidate = project_simplex(rng.random(result.preferences.shape[1]))
        before = potential_cost(x, snapshot)
        after_x = x.copy()
        after_x[i] = candidate
        delta_potential = potential_cost(after_x, snapshot) - before
        costs_before = potential_gradient(x, snapshot)[i] @ x[i]
        costs_after = potential_gradient(x, snapshot)[i] @ candidate
        # Finite games use the common potential by construction; the gradient
        # check below is an independent unilateral directional derivative test.
        direction = candidate - x[i]
        eps = 1e-6
        plus = x.copy()
        minus = x.copy()
        plus[i] = x[i] + eps * direction
        minus[i] = x[i] - eps * direction
        numeric = (potential_cost(plus, snapshot) - potential_cost(minus, snapshot)) / (2.0 * eps)
        analytic = float(potential_gradient(x, snapshot)[i] @ direction)
        max_potential_identity_error = max(max_potential_identity_error, abs(numeric - analytic))
        _ = (delta_potential, costs_before, costs_after, optimum)
        if representative is None:
            representative = result
            representative_qp = qp_value

    initial_clearances = [
        _swept_clearance(world, world.initial_state, world.initial_state)[0]
        for world in worlds
    ]
    initial_collision_count = int(sum(clearance < 0.0 for clearance in initial_clearances))
    min_initial_clearance = float(min(initial_clearances))

    gates = dict(config.get("audit_gates", {}))
    pass_simplex = max_simplex <= float(gates.get("max_simplex_error", 1e-9))
    pass_capacity = max_capacity <= float(gates.get("max_capacity_violation", 0.08))
    pass_qp = max_qp_gap <= float(gates.get("max_qp_potential_gap", 0.025))
    pass_identity = max_potential_identity_error <= float(gates.get("max_potential_gradient_error", 1e-5))
    pass_initial = (
        initial_collision_count == 0
        and min_initial_clearance >= float(gates.get("min_initial_clearance_m", 0.0))
    )
    passed = (
        pass_simplex
        and pass_capacity
        and pass_qp
        and pass_identity
        and pass_initial
        and qp_failures == 0
    )
    audit = {
        "status": "PASS" if passed else "FAIL",
        "worlds_audited": audit_worlds,
        "max_simplex_error": max_simplex,
        "max_capacity_violation": max_capacity,
        "max_qp_potential_gap": max_qp_gap,
        "max_potential_gradient_error": max_potential_identity_error,
        "qp_failures": qp_failures,
        "initial_collision_count": initial_collision_count,
        "min_initial_clearance_m": min_initial_clearance,
        "positions_repaired_after_integration": False,
        "gates": {
            "simplex": pass_simplex,
            "capacity": pass_capacity,
            "qp_gap": pass_qp,
            "potential_gradient": pass_identity,
            "qp_success": qp_failures == 0,
            "initial_worlds": pass_initial,
        },
    }
    (output_dir / "theory_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    assert representative is not None
    return audit, representative, representative_qp


def _write_report(
    path: Path,
    experiment_id: str,
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    audit: dict[str, Any],
) -> None:
    lines = [
        f"# {experiment_id}",
        "",
        f"- Worlds: {len(rows) // max(len(summary), 1)}",
        f"- Runs: {len(rows)}",
        f"- Theory audit: **{audit['status']}**",
        "- Plant: dynamic unicycle with wheel-torque saturation.",
        "- Safety accounting: RAW, SAFE and EXEC are separate; no position repair is applied.",
        "",
        "## Method summary",
        "",
        "| Method | Safe success | Collision | Timeout | Docking s | Energy Wh | KKT | Runtime s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {label} | {safe_docking_success:.4f} | {any_collision:.4f} | {timeout:.4f} | "
            "{docking_time_s:.3f} | {energy_wh:.4f} | {final_kkt_residual:.5f} | {runtime_s:.4f} |".format(**row)
        )
    lines.extend(["", "## Frozen hypotheses", "", "| ID | Difference | 95% CI | p Holm | Supported |", "|---|---:|---:|---:|---|"])
    for row in hypotheses:
        lines.append(
            f"| {row['hypothesis']} | {row['mean_difference']:.5f} | "
            f"[{row['ci95_low']:.5f}, {row['ci95_high']:.5f}] | "
            f"{row['p_holm']:.3g} | {'yes' if row['supported'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Audit",
            "",
            f"- Maximum simplex error: {audit['max_simplex_error']:.6g}",
            f"- Maximum capacity violation: {audit['max_capacity_violation']:.6g}",
            f"- Maximum QP potential gap: {audit['max_qp_potential_gap']:.6g}",
            f"- Maximum potential-gradient error: {audit['max_potential_gradient_error']:.6g}",
            f"- Initial collisions: {audit['initial_collision_count']}",
            f"- Minimum initial clearance: {audit['min_initial_clearance_m']:.6g}",
            f"- Position repair after integration: {audit['positions_repaired_after_integration']}",
            "",
            "## Scope",
            "",
            "The QP/KKT certificate applies to the convex receding primitive relaxation. "
            "It is not a global certificate for nonlinear multi-robot motion. Barrier "
            "residuals are re-evaluated after wheel-torque saturation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sp4_docking_config(config_path: Path | str) -> dict[str, Any]:
    """Run a reproducible SP4 docking campaign and generate thesis artifacts."""

    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    traces_dir = output_dir / "traces"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    traces_dir.mkdir(parents=True, exist_ok=True)

    seed_cfg = dict(config["seeds"])
    seeds = range(int(seed_cfg["start"]), int(seed_cfg["start"]) + int(seed_cfg["count"]))
    scenarios = [str(item["id"]) for item in config["scenarios"]]
    robot_counts = [int(value) for value in config.get("robot_counts", [4, 8, 12])]
    methods = [str(item["id"]) for item in config["methods"]]
    worlds = [
        build_docking_world(scenario, seed, n_robots)
        for scenario in scenarios
        for n_robots in robot_counts
        for seed in seeds
    ]

    audit, audit_trace, audit_qp_value = _theory_audit(config, worlds, output_dir=output_dir)
    simulation_cfg = dict(config.get("simulation", {}))
    game_cfg = dict(config.get("game", {}))
    results: list[DockingRunResult] = []
    representative_results: list[DockingRunResult] = []
    representative_scenario = str(config.get("representative_scenario", "crossing" if "crossing" in scenarios else scenarios[0]))
    representative_key = (representative_scenario, robot_counts[0], int(seed_cfg["start"]))
    for world in worlds:
        for method in methods:
            result = simulate_docking(
                world,
                method,
                dt_s=float(simulation_cfg.get("dt_s", 0.16)),
                horizon_s=float(simulation_cfg.get("horizon_s", 22.0)),
                game_steps=int(game_cfg.get("steps", 24)),
                replan_interval_steps=int(game_cfg.get("replan_interval_steps", 3)),
                central_steps=int(game_cfg.get("central_steps", 70)),
                primal_dt=float(game_cfg.get("primal_dt", 0.12)),
                dual_dt=float(game_cfg.get("dual_dt", 0.10)),
                congestion_weight=float(game_cfg.get("congestion_weight", 0.38)),
                regularization=float(game_cfg.get("regularization", 0.04)),
                consensus_rounds=int(game_cfg.get("consensus_rounds", 4)),
                barrier_gamma=float(simulation_cfg.get("barrier_gamma", 2.6)),
                barrier_iterations=int(simulation_cfg.get("barrier_iterations", 18)),
            )
            results.append(result)
            if (world.scenario, world.n_robots, world.seed) == representative_key:
                representative_results.append(result)

    rows = [_run_row(result) for result in results]
    summary = summarize_runs(rows)
    hypotheses = evaluate_hypotheses(rows, list(config.get("hypotheses", [])))
    _write_csv(tables_dir / "runs.csv", rows)
    _write_csv(tables_dir / "summary.csv", summary)
    _write_csv(tables_dir / "hypothesis_results.csv", hypotheses)

    _plot_performance(summary, figures_dir / "fig-sp4-docking-performance.png")
    _plot_tradeoff(summary, figures_dir / "fig-sp4-docking-tradeoff.png")
    _plot_scenario_matrix(rows, figures_dir / "fig-sp4-scenario-matrix.png")
    if len(robot_counts) > 1:
        _plot_scaling(rows, figures_dir / "fig-sp4-scaling.png")
    _plot_theory(audit_trace, audit_qp_value, figures_dir / "fig-sp4-kkt-potential.png")
    if representative_results:
        rep_world = next(
            world
            for world in worlds
            if (world.scenario, world.n_robots, world.seed) == representative_key
        )
        _plot_trajectory(rep_world, representative_results, figures_dir / "fig-sp4-docking-trajectories.png")
        for result in representative_results:
            np.savez_compressed(
                traces_dir / f"{result.method}.npz",
                positions=result.positions,
                potential=result.potential_trace,
                kkt=result.kkt_trace,
            )

    _write_report(
        output_dir / "report.md",
        experiment_id,
        rows,
        summary,
        hypotheses,
        audit,
    )
    manifest = {
        "experiment_id": experiment_id,
        "output_dir": str(output_dir),
        "worlds": len(worlds),
        "runs": len(rows),
        "methods": len(methods),
        "scenarios": len(scenarios),
        "robot_counts": robot_counts,
        "theory_audit": audit["status"],
        "config": str(path),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


__all__ = [
    "DockingRunResult",
    "DockingWorld",
    "GameStepResult",
    "PrimitiveSnapshot",
    "barrier_project",
    "build_docking_world",
    "build_primitive_snapshot",
    "potential_cost",
    "potential_gradient",
    "project_simplex",
    "run_sp4_docking_config",
    "simulate_docking",
    "solve_motion_game",
    "solve_snapshot_qp",
]
