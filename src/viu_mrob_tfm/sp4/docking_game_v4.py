"""SP4 v4: distributed liveness game with torque-feasible HOCBF execution.

This module intentionally lives beside ``docking_game.py``.  The v3 campaign is
immutable evidence; v4 is a new protocol and must earn its own confirmatory run.
"""

from __future__ import annotations


import heapq
import math
import time
from dataclasses import dataclass, replace

import numpy as np

from .docking_game import (
    DockingRunResult,
    DockingWorld,
    _segment_point_distance,
    _swept_clearance,
    build_docking_world,
    evaluate_hypotheses,
    project_simplex,
    summarize_runs,
    wrap_angle,
)


V4_METHOD_LABELS: dict[str, str] = {
    "direct_hocbf": "Directo + HOCBF",
    "priority_hocbf": "Prioridad local + HOCBF",
    "central_hocbf": "Planificador central + HOCBF",
    "distributed_pd_hocbf": "Juego PD distribuido + HOCBF",
    "distributed_replicator_hocbf": "Replicator distribuido + HOCBF",
}

V4_GAME_METHODS = {"distributed_pd_hocbf", "distributed_replicator_hocbf"}


@dataclass(slots=True)
class PairwiseGameState:
    """Persistent local state for the three-action liveness game."""

    preferences: np.ndarray
    dual_prices: np.ndarray
    wait_age: np.ndarray
    potential_trace: list[float]
    kkt_trace: list[float]
    capacity_trace: list[float]
    pair_owner: np.ndarray
    messages: int = 0


@dataclass(slots=True)
class HOCBFResult:
    acceleration: np.ndarray
    residual: float
    interventions: int
    intervention_norm: float
    torque_active: int


def _pair_index(n: int, i: int, j: int) -> int:
    if i > j:
        i, j = j, i
    return i * (2 * n - i - 1) // 2 + (j - i - 1)


def _grid_point(index: tuple[int, int], half: float, resolution: float) -> np.ndarray:
    return np.asarray([-half + index[0] * resolution, -half + index[1] * resolution])


def _grid_index(point: np.ndarray, half: float, resolution: float) -> tuple[int, int]:
    value = np.rint((np.asarray(point) + half) / resolution).astype(int)
    return int(value[0]), int(value[1])


def _static_clearance(world: DockingWorld, point: np.ndarray) -> float:
    clearance = float(np.linalg.norm(point) - world.load_radius_m - world.robot_radius_m)
    for obstacle in world.obstacles:
        clearance = min(
            clearance,
            float(np.linalg.norm(point - obstacle[:2]) - obstacle[2] - world.robot_radius_m),
        )
    boundary = world.map_half_extent_m - world.robot_radius_m - float(np.max(np.abs(point)))
    return min(clearance, boundary)


def _segment_is_free(
    world: DockingWorld,
    start: np.ndarray,
    end: np.ndarray,
    *,
    margin_m: float = 0.025,
) -> bool:
    length = float(np.linalg.norm(end - start))
    samples = max(2, int(math.ceil(length / 0.055)) + 1)
    for fraction in np.linspace(0.0, 1.0, samples):
        point = start + fraction * (end - start)
        if _static_clearance(world, point) < margin_m:
            return False
    return True




def build_docking_world_v4(
    scenario: str,
    seed: int,
    n_robots: int,
) -> DockingWorld:
    """Build a v4 world and repair only the infeasible v3 actuator geometry."""

    world = build_docking_world(scenario, seed, n_robots)
    if scenario == "actuator_limited":
        obstacles = np.asarray(
            [
                [-1.92, 0.0, 0.40],
                [1.92, 0.0, 0.40],
                [0.0, 2.60, 0.34],
            ],
            dtype=float,
        )
        return replace(world, obstacles=obstacles)
    if scenario == "narrow_passage":
        # Preserve the 0.66 m bottlenecks while keeping every N<=12
        # contact slot physically attainable by a 0.22 m-radius robot.
        obstacles = np.asarray(
            [
                [-1.90, 1.05, 0.72],
                [-1.90, -1.05, 0.72],
                [1.90, 1.05, 0.72],
                [1.90, -1.05, 0.72],
            ],
            dtype=float,
        )
        return replace(world, obstacles=obstacles)
    return world


def minimum_goal_clearance(world: DockingWorld) -> float:
    """Audit every target disk against load, obstacles, peers and boundary."""

    minimum = float("inf")
    targets = world.target_pose[:, :2]
    for i, point in enumerate(targets):
        minimum = min(
            minimum,
            float(np.linalg.norm(point) - world.load_radius_m - world.robot_radius_m),
        )
        for obstacle in world.obstacles:
            minimum = min(
                minimum,
                float(
                    np.linalg.norm(point - obstacle[:2])
                    - obstacle[2]
                    - world.robot_radius_m
                ),
            )
        minimum = min(
            minimum,
            world.map_half_extent_m
            - world.robot_radius_m
            - float(np.max(np.abs(point))),
        )
        for j in range(i + 1, world.n_robots):
            minimum = min(
                minimum,
                float(np.linalg.norm(point - targets[j]) - 2.0 * world.robot_radius_m),
            )
    return float(minimum)

def plan_static_path(
    world: DockingWorld,
    start: np.ndarray,
    goal: np.ndarray,
    *,
    resolution_m: float = 0.14,
    margin_m: float = 0.025,
    narrow_margin_override_m: float | None = None,
) -> np.ndarray:
    """Plan a collision-free grid path and preserve the exact docking goal."""

    start = np.asarray(start, dtype=float)
    goal = np.asarray(goal, dtype=float)
    if world.scenario == "narrow_passage" and resolution_m >= 0.10:
        resolution_m = 0.03 if world.n_robots >= 10 else 0.05
        margin_m = (
            float(narrow_margin_override_m)
            if narrow_margin_override_m is not None
            else max(margin_m, 0.070)
        )
    if _segment_is_free(world, start, goal, margin_m=margin_m):
        return np.vstack([start, goal])

    half = world.map_half_extent_m - world.robot_radius_m - 0.04
    limit = int(math.floor(2.0 * half / resolution_m))
    start_idx = _grid_index(start, half, resolution_m)
    goal_idx = _grid_index(goal, half, resolution_m)

    def valid(index: tuple[int, int]) -> bool:
        if index[0] < 0 or index[1] < 0 or index[0] > limit or index[1] > limit:
            return False
        return _static_clearance(world, _grid_point(index, half, resolution_m)) >= margin_m

    if not valid(goal_idx):
        candidates: list[tuple[float, tuple[int, int]]] = []
        for radius in range(1, 8):
            for dx in range(-radius, radius + 1):
                for dy in (-radius, radius):
                    idx = (goal_idx[0] + dx, goal_idx[1] + dy)
                    if valid(idx):
                        candidates.append(
                            (float(np.linalg.norm(_grid_point(idx, half, resolution_m) - goal)), idx)
                        )
            for dy in range(-radius + 1, radius):
                for dx in (-radius, radius):
                    idx = (goal_idx[0] + dx, goal_idx[1] + dy)
                    if valid(idx):
                        candidates.append(
                            (float(np.linalg.norm(_grid_point(idx, half, resolution_m) - goal)), idx)
                        )
            if candidates:
                goal_idx = min(candidates)[1]
                break

    moves = (
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)),
        (-1, 1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)),
        (1, 1, math.sqrt(2.0)),
    )
    frontier: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start_idx)]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start_idx: None}
    cost_so_far: dict[tuple[int, int], float] = {start_idx: 0.0}
    reached = False
    while frontier:
        _score, current_cost, current = heapq.heappop(frontier)
        if current == goal_idx:
            reached = True
            break
        if current_cost > cost_so_far.get(current, float("inf")) + 1e-12:
            continue
        for dx, dy, step_cost in moves:
            neighbour = (current[0] + dx, current[1] + dy)
            if not valid(neighbour):
                continue
            point = _grid_point(neighbour, half, resolution_m)
            clearance = max(_static_clearance(world, point) - margin_m, 0.015)
            penalty = 0.018 / min(clearance, 0.60)
            new_cost = current_cost + step_cost + penalty
            if new_cost + 1e-12 < cost_so_far.get(neighbour, float("inf")):
                cost_so_far[neighbour] = new_cost
                parent[neighbour] = current
                heuristic = float(np.linalg.norm(np.asarray(neighbour) - np.asarray(goal_idx)))
                heapq.heappush(frontier, (new_cost + heuristic, new_cost, neighbour))
    if not reached:
        raise RuntimeError(f"No static path for {world.scenario} seed={world.seed}")

    indices: list[tuple[int, int]] = []
    cursor: tuple[int, int] | None = goal_idx
    while cursor is not None:
        indices.append(cursor)
        cursor = parent[cursor]
    indices.reverse()
    dense = np.vstack([_grid_point(index, half, resolution_m) for index in indices])
    dense[0] = start
    dense[-1] = _grid_point(goal_idx, half, resolution_m)

    simplified = [dense[0]]
    anchor = 0
    while anchor < len(dense) - 1:
        candidate = len(dense) - 1
        while candidate > anchor + 1 and not _segment_is_free(
            world, dense[anchor], dense[candidate], margin_m=margin_m
        ):
            candidate -= 1
        simplified.append(dense[candidate])
        anchor = candidate
    path = np.vstack(simplified)
    if (
        _static_clearance(world, goal) >= 0.001
        and _segment_is_free(world, path[-1], goal, margin_m=0.001)
    ):
        path = np.vstack([path, goal])
    return path





def _world_with_reserved_targets(
    world: DockingWorld,
    reserved_robot_indices: np.ndarray | list[int] | tuple[int, ...],
) -> DockingWorld:
    indices = np.asarray(reserved_robot_indices, dtype=int)
    if indices.size == 0:
        return world
    other = world.target_pose[indices, :2]
    reservation_buffer = 0.05 if world.scenario == "narrow_passage" else 0.12
    reserved = np.column_stack(
        [
            other,
            np.full(
                other.shape[0],
                world.robot_radius_m + reservation_buffer,
            ),
        ]
    )
    obstacles = (
        reserved
        if world.obstacles.size == 0
        else np.vstack([world.obstacles, reserved])
    )
    return replace(world, obstacles=obstacles)

def _shortest_route_side(world: DockingWorld, robot_index: int) -> int:
    start = world.initial_state[robot_index, :2]
    goal = world.target_pose[robot_index, :2]
    start_angle = math.atan2(start[1], start[0])
    target_angle = math.atan2(goal[1], goal[0])
    positive_delta = (target_angle - start_angle) % (2.0 * math.pi)
    return 1 if positive_delta <= math.pi else -1


def _phase_consistent_route_sides(
    world: DockingWorld,
    phase_of_robot: np.ndarray,
) -> np.ndarray:
    sides = np.ones(world.n_robots, dtype=int)
    for phase in np.unique(phase_of_robot):
        members = np.flatnonzero(phase_of_robot == phase)
        positive: list[float] = []
        for robot in members:
            start = world.initial_state[robot, :2]
            goal = world.target_pose[robot, :2]
            start_angle = math.atan2(start[1], start[0])
            target_angle = math.atan2(goal[1], goal[0])
            positive.append((target_angle - start_angle) % (2.0 * math.pi))
        positive_cost = float(np.sum(positive))
        negative_cost = float(np.sum([2.0 * math.pi - value for value in positive]))
        sides[members] = 1 if positive_cost <= negative_cost else -1
    return sides


def _docking_staging_point(
    world: DockingWorld,
    target_angle: float,
    goal: np.ndarray,
) -> np.ndarray:
    required = 0.070 if world.scenario == "narrow_passage" else 0.025
    for radius in np.linspace(1.30, 1.08, 12):
        candidate = radius * np.asarray(
            [math.cos(target_angle), math.sin(target_angle)]
        )
        if (
            _static_clearance(world, candidate) >= required
            and _segment_is_free(world, candidate, goal, margin_m=0.001)
        ):
            return candidate
    return np.asarray(goal, dtype=float).copy()


def plan_coordinated_path(
    world: DockingWorld,
    robot_index: int,
    *,
    side: int = 1,
    reserved_robot_indices: np.ndarray | list[int] | tuple[int, ...] = (),
) -> np.ndarray:
    """Force a shared circulation convention before the radial docking tail."""

    planning_world = _world_with_reserved_targets(world, reserved_robot_indices)
    start = world.initial_state[robot_index, :2]
    goal = world.target_pose[robot_index, :2]
    start_angle = math.atan2(start[1], start[0])
    target_angle = math.atan2(goal[1], goal[0])
    shortest_delta = abs(float(wrap_angle(target_angle - start_angle)))
    if world.scenario == "narrow_passage":
        staging = _docking_staging_point(planning_world, target_angle, goal)

        try:
            prefix = plan_static_path(planning_world, start, staging)
        except RuntimeError:
            prefix = plan_static_path(
                planning_world,
                start,
                staging,
                narrow_margin_override_m=0.040,
            )
        if (
            float(np.linalg.norm(prefix[-1] - staging)) > 1e-8
            and _segment_is_free(planning_world, prefix[-1], staging, margin_m=0.001)
        ):
            prefix = np.vstack([prefix, staging])
        if _segment_is_free(planning_world, prefix[-1], goal, margin_m=0.001):
            return np.vstack([prefix, goal])
        return plan_static_path(planning_world, start, goal)
    if shortest_delta < 0.32:
        staging = _docking_staging_point(planning_world, target_angle, goal)

        prefix = plan_static_path(planning_world, start, staging)
        if (
            float(np.linalg.norm(prefix[-1] - staging)) > 1e-8
            and _segment_is_free(planning_world, prefix[-1], staging, margin_m=0.001)
        ):
            prefix = np.vstack([prefix, staging])
        if _segment_is_free(planning_world, prefix[-1], goal, margin_m=0.001):
            return np.vstack([prefix, goal])
        return plan_static_path(planning_world, start, goal)
    if (
        world.scenario not in {"crossing", "symmetric_deadlock", "narrow_passage", "cluttered_docking"}
        and _segment_is_free(planning_world, start, goal)
    ):
        return np.vstack([start, goal])
    positive_delta = (target_angle - start_angle) % (2.0 * math.pi)
    negative_delta = positive_delta - 2.0 * math.pi
    angular_delta = positive_delta if side >= 0 else negative_delta
    route_radius = 2.85 if world.scenario == "narrow_passage" else 1.48

    entry = route_radius * np.asarray([math.cos(start_angle), math.sin(start_angle)])
    first = plan_static_path(planning_world, start, entry)
    points: list[np.ndarray] = [point.copy() for point in first]
    arc_steps = max(2, int(math.ceil(abs(angular_delta) / 0.18)))
    arc_angles = np.linspace(start_angle, start_angle + angular_delta, arc_steps + 1)[1:]
    current = points[-1]
    for angle in arc_angles:
        waypoint = route_radius * np.asarray([math.cos(angle), math.sin(angle)])
        if _segment_is_free(planning_world, current, waypoint):
            points.append(waypoint)
        else:
            detour = plan_static_path(planning_world, current, waypoint)
            points.extend(point.copy() for point in detour[1:])
        current = points[-1]
    staging = _docking_staging_point(planning_world, target_angle, goal)

    for waypoint in (staging, goal):
        segment = plan_static_path(planning_world, current, waypoint)
        points.extend(point.copy() for point in segment[1:])
        current = points[-1]
    return np.vstack(points)

def _path_lookahead(
    world: DockingWorld,
    path: np.ndarray,
    position: np.ndarray,
    cursor: int,
    distance_m: float,
) -> tuple[np.ndarray, int]:
    next_index = max(int(cursor), 1)
    capture_radius = max(0.16, 0.52 * distance_m)
    while (
        next_index < len(path) - 1
        and float(np.linalg.norm(path[next_index] - position)) <= capture_radius
        and _segment_is_free(
            world,
            position,
            path[next_index + 1],
            margin_m=0.006,
        )
    ):
        next_index += 1
    return path[next_index], next_index


def nominal_path_acceleration(
    world: DockingWorld,
    state: np.ndarray,
    paths: list[np.ndarray],
    cursors: np.ndarray,
    docked: np.ndarray,
    speed_scale: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Track the static paths with a dynamic-unicycle acceleration command."""

    control = np.zeros((world.n_robots, 2), dtype=float)
    next_cursors = cursors.copy()
    for i in range(world.n_robots):
        if docked[i]:
            continue
        target = world.target_pose[i]
        distance = float(np.linalg.norm(state[i, :2] - target[:2]))
        lookahead = 0.25 if distance < 0.70 else 0.46
        waypoint, next_cursors[i] = _path_lookahead(
            world,
            paths[i],
            state[i, :2],
            int(cursors[i]),
            lookahead,
        )
        delta = waypoint - state[i, :2]
        desired_heading = (
            math.atan2(delta[1], delta[0])
            if np.linalg.norm(delta) > 1e-9
            else float(target[2])
        )
        if distance < 0.36:
            blend = float(np.clip((0.36 - distance) / 0.24, 0.0, 1.0))
            heading_delta = float(wrap_angle(float(target[2]) - desired_heading))
            desired_heading = float(wrap_angle(desired_heading + blend * heading_delta))
        if distance <= 0.11:
            desired_heading = float(target[2])
        heading_error = float(wrap_angle(desired_heading - state[i, 2]))
        turn_factor = max(0.0, math.cos(heading_error)) ** 2
        desired_speed = min(world.max_speed_mps[i] * 0.88, 1.20 * distance)
        desired_speed *= float(speed_scale[i]) * turn_factor
        if distance <= 0.11 or abs(heading_error) > 1.00:
            desired_speed = 0.0
        desired_omega = np.clip(
            2.45 * heading_error,
            -world.max_omega_rps[i],
            world.max_omega_rps[i],
        )
        control[i, 0] = 2.35 * (desired_speed - state[i, 3])
        control[i, 1] = 3.20 * (desired_omega - state[i, 4])
    return control, next_cursors


def predicted_conflicts(
    world: DockingWorld,
    state: np.ndarray,
    nominal_acceleration: np.ndarray,
    *,
    horizon_s: float = 1.05,
) -> np.ndarray:
    """Build the local conflict graph from exchanged one-step predictions."""

    n = world.n_robots
    predicted = np.zeros((n, 2), dtype=float)
    for i in range(n):
        e = np.asarray([math.cos(state[i, 2]), math.sin(state[i, 2])])
        ep = np.asarray([-e[1], e[0]])
        velocity = state[i, 3] * e
        acceleration = nominal_acceleration[i, 0] * e + state[i, 3] * state[i, 4] * ep
        predicted[i] = (
            state[i, :2]
            + horizon_s * velocity
            + 0.5 * horizon_s**2 * acceleration
        )
    conflict = np.zeros((n, n), dtype=bool)
    threshold = 2.0 * world.robot_radius_m + 0.14
    for i in range(n):
        for j in range(i + 1, n):
            separation = _segment_point_distance(
                state[i, :2] - state[j, :2],
                predicted[i] - predicted[j],
                np.zeros(2),
            )
            close = float(np.linalg.norm(state[i, :2] - state[j, :2])) < 0.72
            conflict[i, j] = conflict[j, i] = separation < threshold or close
    return conflict


def build_pairwise_game_features(conflict: np.ndarray) -> np.ndarray:
    """Return local occupancy shares for every potential pair resource."""

    n = int(conflict.shape[0])
    resources = n * (n - 1) // 2
    features = np.zeros((n, 3, resources), dtype=float)
    intensity = np.asarray([1.0, 0.42, 0.0])
    for i in range(n):
        for j in range(i + 1, n):
            if not conflict[i, j]:
                continue
            resource = _pair_index(n, i, j)
            features[i, :, resource] = intensity
            features[j, :, resource] = intensity
    return features


def pairwise_game_potential(
    preferences: np.ndarray,
    costs: np.ndarray,
    features: np.ndarray,
    *,
    congestion_weight: float = 0.52,
    regularization: float = 0.08,
) -> float:
    occupancy = np.einsum("ia,iar->r", preferences, features, optimize=True)
    return float(
        np.sum(costs * preferences)
        + 0.5 * congestion_weight * float(occupancy @ occupancy)
        + 0.5 * regularization * float(np.sum(preferences * preferences))
    )


def pairwise_game_gradient(
    preferences: np.ndarray,
    costs: np.ndarray,
    features: np.ndarray,
    *,
    congestion_weight: float = 0.52,
    regularization: float = 0.08,
) -> np.ndarray:
    occupancy = np.einsum("ia,iar->r", preferences, features, optimize=True)
    return (
        costs
        + congestion_weight
        * np.einsum("iar,r->ia", features, occupancy, optimize=True)
        + regularization * preferences
    )


def project_pair_capacities(
    preferences: np.ndarray,
    conflict: np.ndarray,
) -> np.ndarray:
    """Distributed feasibility map for unit-capacity pair resources."""

    projected = np.asarray(preferences, dtype=float).copy()
    intensity = np.asarray([1.0, 0.42])
    n = projected.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            if not conflict[i, j]:
                continue
            occupancy = float(intensity @ projected[i, :2] + intensity @ projected[j, :2])
            if occupancy <= 1.0 + 1e-12:
                continue
            scale = 1.0 / occupancy
            for robot in (i, j):
                projected[robot, :2] *= scale
                projected[robot, 2] = 1.0 - float(np.sum(projected[robot, :2]))
    return projected


def initialise_pairwise_game(n_robots: int) -> PairwiseGameState:
    resources = n_robots * (n_robots - 1) // 2
    preferences = np.zeros((n_robots, 3), dtype=float)
    preferences[:, 0] = 0.72
    preferences[:, 1] = 0.18
    preferences[:, 2] = 0.10
    return PairwiseGameState(
        preferences=preferences,
        dual_prices=np.zeros(resources, dtype=float),
        wait_age=np.zeros(n_robots, dtype=float),
        potential_trace=[],
        kkt_trace=[],
        capacity_trace=[],
        pair_owner=np.full(resources, -1, dtype=int),
    )


def solve_pairwise_game(
    game: PairwiseGameState,
    conflict: np.ndarray,
    priority: np.ndarray,
    docked: np.ndarray,
    *,
    protocol: str = "projected_pd",
    iterations: int = 16,
    primal_dt: float = 0.18,
    dual_dt: float = 0.14,
    congestion_weight: float = 0.52,
    regularization: float = 0.08,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Update a convex pair-resource game using only conflict-neighbour data."""

    features = build_pairwise_game_features(conflict)
    utility = 1.0 + 0.025 * game.wait_age + 0.10 * np.asarray(priority)
    costs = np.column_stack(
        [
            -utility,
            -0.46 * utility + 0.03,
            0.10 + 0.005 * game.wait_age,
        ]
    )
    costs[docked, :] = (8.0, 8.0, 0.0)
    game.preferences[docked, :] = (0.0, 0.0, 1.0)
    active = np.any(features > 0.0, axis=(0, 1))
    game.dual_prices[~active] *= 0.75
    if not np.any(active):
        game.preferences[~docked, :] = (1.0, 0.0, 0.0)
        game.preferences[docked, :] = (0.0, 0.0, 1.0)
        game.potential_trace.append(
            pairwise_game_potential(
                game.preferences,
                costs,
                features,
                congestion_weight=congestion_weight,
                regularization=regularization,
            )
        )
        game.kkt_trace.append(0.0)
        game.capacity_trace.append(0.0)
        actions = np.zeros(game.preferences.shape[0], dtype=int)
        actions[docked] = 2
        return actions, costs, 0.0
    last_gradient = np.zeros_like(game.preferences)
    for _ in range(max(int(iterations), 1)):
        occupancy = np.einsum("ia,iar->r", game.preferences, features, optimize=True)
        last_gradient = (
            pairwise_game_gradient(
                game.preferences,
                costs,
                features,
                congestion_weight=congestion_weight,
                regularization=regularization,
            )
            + np.einsum(
                "iar,r->ia",
                features,
                game.dual_prices,
                optimize=True,
            )
        )
        if protocol == "replicator":
            # Entropic mirror step: the exact multiplicative discretisation of
            # replicator dynamics is positivity preserving and avoids the
            # boundary cycles produced by forward Euler.
            centred = last_gradient - np.min(last_gradient, axis=1, keepdims=True)
            weights = np.maximum(game.preferences, 1e-12) * np.exp(
                -0.10 * centred
            )
            candidate = weights / np.sum(weights, axis=1, keepdims=True)
        elif protocol == "projected_pd":
            candidate = game.preferences - primal_dt * last_gradient
        else:
            raise ValueError(f"Unknown v4 protocol: {protocol}")
        game.preferences = np.vstack([project_simplex(row) for row in candidate])
        game.preferences[docked, :] = (0.0, 0.0, 1.0)
        game.preferences = project_pair_capacities(game.preferences, conflict)
        occupancy = np.einsum("ia,iar->r", game.preferences, features, optimize=True)
        game.dual_prices = np.maximum(
            game.dual_prices + dual_dt * (occupancy - 1.0) * active,
            0.0,
        )
        game.messages += int(2 * np.count_nonzero(np.triu(conflict, 1)))
    projected = np.vstack(
        [
            project_simplex(game.preferences[i] - last_gradient[i])
            for i in range(game.preferences.shape[0])
        ]
    )
    occupancy = np.einsum("ia,iar->r", game.preferences, features, optimize=True)
    residual = max(
        float(np.max(np.linalg.norm(game.preferences - projected, axis=1))),
        float(np.max(np.maximum(occupancy - 1.0, 0.0))) if occupancy.size else 0.0,
    )
    game.potential_trace.append(
        pairwise_game_potential(
            game.preferences,
            costs,
            features,
            congestion_weight=congestion_weight,
            regularization=regularization,
        )
    )
    game.kkt_trace.append(residual)
    game.capacity_trace.append(
        float(np.max(np.maximum(occupancy - 1.0, 0.0)))
        if occupancy.size
        else 0.0
    )
    actions = np.argmax(game.preferences, axis=1)
    actions[docked] = 2
    return actions, costs, residual


def _distributed_independent_set(
    actions: np.ndarray,
    conflict: np.ndarray,
    bid: np.ndarray,
    docked: np.ndarray,
) -> tuple[np.ndarray, int, int]:
    """Resolve conflicts through repeated neighbour-only maximal-priority rounds."""

    selected = np.asarray(actions, dtype=int).copy()
    selected[docked] = 2
    candidates = set(np.flatnonzero((selected < 2) & (~docked)).tolist())
    winners: set[int] = set()
    blocked: set[int] = set()
    messages = 0
    rounds = 0
    while candidates:
        rounds += 1
        local_winners: set[int] = set()
        for i in candidates:
            neighbours = [j for j in candidates if conflict[i, j]]
            messages += len(neighbours)
            if all((bid[i], -i) > (bid[j], -j) for j in neighbours):
                local_winners.add(i)
        if not local_winners:
            local_winners.add(max(candidates, key=lambda i: (bid[i], -i)))
        winners.update(local_winners)
        newly_blocked = {
            j
            for i in local_winners
            for j in candidates
            if j != i and conflict[i, j]
        }
        blocked.update(newly_blocked)
        candidates.difference_update(local_winners | newly_blocked)
    for i in blocked:
        selected[i] = 2
    return selected, messages, rounds


def _central_independent_set(
    actions: np.ndarray,
    conflict: np.ndarray,
    bid: np.ndarray,
    docked: np.ndarray,
) -> np.ndarray:
    """Exact maximum-weight independent set for the small confirmatory fleets."""

    candidates = np.flatnonzero((actions < 2) & (~docked))
    best_score = -float("inf")
    best_mask = 0
    for mask in range(1 << len(candidates)):
        chosen = [int(candidates[k]) for k in range(len(candidates)) if mask & (1 << k)]
        if any(conflict[i, j] for position, i in enumerate(chosen) for j in chosen[position + 1 :]):
            continue
        score = float(np.sum(bid[chosen])) if chosen else 0.0
        if score > best_score:
            best_score = score
            best_mask = mask
    selected = np.full_like(actions, 2)
    for k, robot in enumerate(candidates):
        if best_mask & (1 << k):
            selected[robot] = actions[robot]
    selected[docked] = 2
    return selected



def _apply_pair_ownership(
    game: PairwiseGameState,
    conflict: np.ndarray,
    bid: np.ndarray,
    state: np.ndarray,
    paths: list[np.ndarray],
    cursors: np.ndarray,
    docked: np.ndarray,
) -> np.ndarray:
    """Hold local right-of-way until a predicted pair conflict clears."""

    owned_bid = np.asarray(bid, dtype=float).copy()
    n = conflict.shape[0]
    progress = np.zeros(n, dtype=float)
    for i in range(n):
        next_index = min(max(int(cursors[i]), 1), len(paths[i]) - 1)
        progress[i] = (
            next_index / max(len(paths[i]) - 1, 1)
            - 0.08 * float(np.linalg.norm(paths[i][next_index] - state[i, :2]))
        )
    for i in range(n):
        for j in range(i + 1, n):
            resource = _pair_index(n, i, j)
            if not conflict[i, j]:
                game.pair_owner[resource] = -1
                continue
            owner = int(game.pair_owner[resource])
            if owner not in (i, j) or docked[owner]:
                owner = max((i, j), key=lambda robot: (progress[robot], bid[robot], -robot))
                game.pair_owner[resource] = owner
            owned_bid[owner] += 100.0
    return owned_bid

def _body_kinematics(state: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    theta = state[:, 2]
    e = np.column_stack([np.cos(theta), np.sin(theta)])
    ep = np.column_stack([-np.sin(theta), np.cos(theta)])
    velocity = state[:, 3, None] * e
    drift = (state[:, 3] * state[:, 4])[:, None] * ep
    return e, ep, velocity, drift


def _input_bounds(world: DockingWorld, state: np.ndarray, dt_s: float) -> tuple[np.ndarray, np.ndarray]:
    lower = np.column_stack(
        [
            np.maximum(-world.max_accel_mps2, -state[:, 3] / dt_s),
            np.maximum(-world.max_alpha_rps2, (-world.max_omega_rps - state[:, 4]) / dt_s),
        ]
    )
    upper = np.column_stack(
        [
            np.minimum(world.max_accel_mps2, (world.max_speed_mps - state[:, 3]) / dt_s),
            np.minimum(world.max_alpha_rps2, (world.max_omega_rps - state[:, 4]) / dt_s),
        ]
    )
    return lower, upper


def _project_upper_halfspace(value: np.ndarray, normal: np.ndarray, upper: float) -> tuple[np.ndarray, bool]:
    excess = float(normal @ value - upper)
    norm2 = float(normal @ normal)
    if excess <= 0.0 or norm2 <= 1e-14:
        return value, False
    return value - excess * normal / norm2, True


def _project_input_constraints(
    world: DockingWorld,
    state: np.ndarray,
    acceleration: np.ndarray,
    docked: np.ndarray,
    *,
    dt_s: float,
    sweeps: int = 3,
) -> tuple[np.ndarray, int]:
    projected = np.asarray(acceleration, dtype=float).copy()
    lower, upper = _input_bounds(world, state, dt_s)
    torque_active = 0
    for _ in range(max(sweeps, 1)):
        projected = np.minimum(np.maximum(projected, lower), upper)
        for i in range(world.n_robots):
            if docked[i]:
                projected[i] = 0.0
                continue
            right = world.wheel_radius_m * np.asarray(
                [0.5 * world.mass_kg[i], world.inertia_kgm2[i] / world.axle_length_m]
            )
            left = world.wheel_radius_m * np.asarray(
                [0.5 * world.mass_kg[i], -world.inertia_kgm2[i] / world.axle_length_m]
            )
            for normal in (right, -right, left, -left):
                projected[i], changed = _project_upper_halfspace(
                    projected[i], normal, float(world.max_wheel_torque_nm[i])
                )
                torque_active += int(changed)
        projected = np.minimum(np.maximum(projected, lower), upper)
    projected[docked] = 0.0
    return projected, torque_active


def _hocbf_pair_terms(
    world: DockingWorld,
    state: np.ndarray,
    i: int,
    j: int,
    *,
    margin_m: float,
    rate_1: float,
    rate_2: float,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    e, _ep, velocity, drift = _body_kinematics(state)
    delta = state[i, :2] - state[j, :2]
    relative_velocity = velocity[i] - velocity[j]
    safe = 2.0 * world.robot_radius_m + margin_m
    h = float(delta @ delta - safe * safe)
    h_dot = float(2.0 * delta @ relative_velocity)
    constant = float(
        2.0 * relative_velocity @ relative_velocity
        + 2.0 * delta @ (drift[i] - drift[j])
        + (rate_1 + rate_2) * h_dot
        + rate_1 * rate_2 * h
    )
    normal_i = np.asarray([2.0 * float(delta @ e[i]), 0.0])
    normal_j = np.asarray([-2.0 * float(delta @ e[j]), 0.0])
    return normal_i, normal_j, -constant, h


def _hocbf_obstacle_terms(
    world: DockingWorld,
    state: np.ndarray,
    i: int,
    obstacle: np.ndarray,
    *,
    margin_m: float,
    rate_1: float,
    rate_2: float,
) -> tuple[np.ndarray, float, float]:
    e, _ep, velocity, drift = _body_kinematics(state)
    delta = state[i, :2] - obstacle[:2]
    radius = float(obstacle[2] + world.robot_radius_m + margin_m)
    h = float(delta @ delta - radius * radius)
    h_dot = float(2.0 * delta @ velocity[i])
    constant = float(
        2.0 * velocity[i] @ velocity[i]
        + 2.0 * delta @ drift[i]
        + (rate_1 + rate_2) * h_dot
        + rate_1 * rate_2 * h
    )
    normal = np.asarray([2.0 * float(delta @ e[i]), 0.0])
    return normal, -constant, h


def hocbf_residual(
    world: DockingWorld,
    state: np.ndarray,
    acceleration: np.ndarray,
    *,
    margin_m: float = 0.015,
    rate_1: float = 2.8,
    rate_2: float = 2.8,
) -> float:
    """Return the largest violation of the executed second-order barriers."""

    violation = 0.0
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            normal_i, normal_j, rhs, _h = _hocbf_pair_terms(
                world,
                state,
                i,
                j,
                margin_m=margin_m,
                rate_1=rate_1,
                rate_2=rate_2,
            )
            lhs = float(normal_i @ acceleration[i] + normal_j @ acceleration[j])
            violation = max(violation, rhs - lhs)
        obstacle_set = list(world.obstacles)
        obstacle_set.append(np.asarray([0.0, 0.0, world.load_radius_m]))
        for obstacle in obstacle_set:
            normal, rhs, _h = _hocbf_obstacle_terms(
                world,
                state,
                i,
                obstacle,
                margin_m=margin_m,
                rate_1=rate_1,
                rate_2=rate_2,
            )
            violation = max(violation, rhs - float(normal @ acceleration[i]))
    return float(max(violation, 0.0))


def project_hocbf_acceleration(
    world: DockingWorld,
    state: np.ndarray,
    nominal_acceleration: np.ndarray,
    docked: np.ndarray,
    *,
    dt_s: float = 0.12,
    iterations: int = 140,
    margin_m: float = 0.015,
    rate_1: float = 2.8,
    rate_2: float = 2.8,
) -> HOCBFResult:
    """Distributed alternating projection in acceleration/torque space.

    Pair constraints update only the two robots that share the constraint.
    Obstacle and actuator constraints are local.  No central QP or positional
    repair is used by the proposed distributed methods.
    """

    nominal = np.asarray(nominal_acceleration, dtype=float)
    acceleration, torque_active = _project_input_constraints(
        world, state, nominal, docked, dt_s=dt_s
    )
    interventions = 0
    obstacle_set = list(world.obstacles)
    obstacle_set.append(np.asarray([0.0, 0.0, world.load_radius_m]))
    for _ in range(max(int(iterations), 1)):
        changed = False
        for i in range(world.n_robots):
            for j in range(i + 1, world.n_robots):
                normal_i, normal_j, rhs, _h = _hocbf_pair_terms(
                    world,
                    state,
                    i,
                    j,
                    margin_m=margin_m,
                    rate_1=rate_1,
                    rate_2=rate_2,
                )
                lhs = float(normal_i @ acceleration[i] + normal_j @ acceleration[j])
                deficit = rhs - lhs
                if deficit <= 1e-10:
                    continue
                norm2 = 0.0
                if not docked[i]:
                    norm2 += float(normal_i @ normal_i)
                if not docked[j]:
                    norm2 += float(normal_j @ normal_j)
                if norm2 <= 1e-14:
                    continue
                if not docked[i]:
                    acceleration[i] += deficit * normal_i / norm2
                if not docked[j]:
                    acceleration[j] += deficit * normal_j / norm2
                interventions += 1
                changed = True
        for i in range(world.n_robots):
            if docked[i]:
                acceleration[i] = 0.0
                continue
            for obstacle in obstacle_set:
                normal, rhs, _h = _hocbf_obstacle_terms(
                    world,
                    state,
                    i,
                    obstacle,
                    margin_m=margin_m,
                    rate_1=rate_1,
                    rate_2=rate_2,
                )
                deficit = rhs - float(normal @ acceleration[i])
                norm2 = float(normal @ normal)
                if deficit <= 1e-10 or norm2 <= 1e-14:
                    continue
                acceleration[i] += deficit * normal / norm2
                interventions += 1
                changed = True
        acceleration, active = _project_input_constraints(
            world,
            state,
            acceleration,
            docked,
            dt_s=dt_s,
            sweeps=2,
        )
        torque_active += active
        if not changed:
            break
    residual = hocbf_residual(
        world,
        state,
        acceleration,
        margin_m=margin_m,
        rate_1=rate_1,
        rate_2=rate_2,
    )
    return HOCBFResult(
        acceleration=acceleration,
        residual=residual,
        interventions=interventions,
        intervention_norm=float(np.linalg.norm(acceleration - nominal)),
        torque_active=torque_active,
    )


def execute_acceleration(
    world: DockingWorld,
    state: np.ndarray,
    acceleration: np.ndarray,
    docked: np.ndarray,
    *,
    dt_s: float,
) -> tuple[np.ndarray, np.ndarray, float, int]:
    """Apply wheel-torque saturation and integrate without state repair."""

    control = np.asarray(acceleration, dtype=float)
    force = world.mass_kg * control[:, 0]
    yaw_moment = world.inertia_kgm2 * control[:, 1]
    right_force = 0.5 * force + yaw_moment / world.axle_length_m
    left_force = 0.5 * force - yaw_moment / world.axle_length_m
    raw_right = world.wheel_radius_m * right_force
    raw_left = world.wheel_radius_m * left_force
    torque_right = np.clip(raw_right, -world.max_wheel_torque_nm, world.max_wheel_torque_nm)
    torque_left = np.clip(raw_left, -world.max_wheel_torque_nm, world.max_wheel_torque_nm)
    saturated = int(
        np.count_nonzero(np.abs(raw_right - torque_right) > 1e-9)
        + np.count_nonzero(np.abs(raw_left - torque_left) > 1e-9)
    )
    actual_force = (torque_right + torque_left) / world.wheel_radius_m
    actual_moment = (
        (torque_right - torque_left)
        / world.wheel_radius_m
        * world.axle_length_m
        / 2.0
    )
    actual = np.column_stack(
        [actual_force / world.mass_kg, actual_moment / world.inertia_kgm2]
    )
    actual[docked] = 0.0
    next_state = state.copy()
    v_new = np.clip(
        state[:, 3] + dt_s * actual[:, 0],
        0.0,
        world.max_speed_mps,
    )
    omega_new = np.clip(
        state[:, 4] + dt_s * actual[:, 1],
        -world.max_omega_rps,
        world.max_omega_rps,
    )
    v_new[docked] = 0.0
    omega_new[docked] = 0.0
    theta_mid = state[:, 2] + 0.5 * dt_s * omega_new
    next_state[:, 0] = state[:, 0] + dt_s * v_new * np.cos(theta_mid)
    next_state[:, 1] = state[:, 1] + dt_s * v_new * np.sin(theta_mid)
    next_state[:, 2] = wrap_angle(state[:, 2] + dt_s * omega_new)
    next_state[:, 3] = v_new
    next_state[:, 4] = omega_new
    wheel_speed_right = (
        v_new + 0.5 * world.axle_length_m * omega_new
    ) / world.wheel_radius_m
    wheel_speed_left = (
        v_new - 0.5 * world.axle_length_m * omega_new
    ) / world.wheel_radius_m
    energy = float(
        np.sum(
            np.abs(torque_right * wheel_speed_right)
            + np.abs(torque_left * wheel_speed_left)
        )
        * dt_s
        / 3600.0
    )
    return next_state, actual, energy, saturated

def simulate_docking_v4(
    world: DockingWorld,
    method: str,
    *,
    dt_s: float = 0.12,
    horizon_s: float = 55.0,
    game_iterations: int = 64,
    hocbf_iterations: int = 140,
    hocbf_margin_m: float = 0.005,
    hocbf_rate: float = 2.8,
    docking_position_tolerance_m: float = 0.12,
    docking_orientation_tolerance_rad: float = 0.24,
    docking_speed_tolerance_mps: float = 0.16,
) -> DockingRunResult:
    """Execute one v4 method on a paired SP4 world."""

    if method not in V4_METHOD_LABELS:
        raise ValueError(f"Unknown SP4 v4 method: {method}")
    started = time.perf_counter()
    phase_capacity = (
        1
        if world.scenario in {"cluttered_docking", "narrow_passage"}
        else 4
    )
    phase_count = max(
        1,
        int(math.ceil(world.n_robots / float(phase_capacity))),
    )
    phase_of_robot = np.arange(world.n_robots) % phase_count
    if world.scenario == "narrow_passage" and phase_capacity == 1:
        slot_clearance = np.full(world.n_robots, float("inf"), dtype=float)
        for robot, goal in enumerate(world.target_pose[:, :2]):
            if world.obstacles.size:
                slot_clearance[robot] = min(
                    float(
                        np.linalg.norm(goal - obstacle[:2])
                        - obstacle[2]
                        - world.robot_radius_m
                    )
                    for obstacle in world.obstacles
                )
        order = np.lexsort((np.arange(world.n_robots), slot_clearance))
        phase_of_robot = np.empty(world.n_robots, dtype=int)
        phase_of_robot[order] = np.arange(world.n_robots)
    route_sides = _phase_consistent_route_sides(world, phase_of_robot)
    if method in V4_GAME_METHODS:
        if world.scenario in {"cluttered_docking", "narrow_passage"}:
            paths = [
                np.vstack(
                    [world.initial_state[i, :2], world.target_pose[i, :2]]
                )
                for i in range(world.n_robots)
            ]
        else:
            paths = [
                plan_coordinated_path(
                    world,
                    i,
                    side=1,
                    reserved_robot_indices=np.flatnonzero(
                        phase_of_robot < phase_of_robot[i]
                    ),
                )
                for i in range(world.n_robots)
            ]
    elif method == "central_hocbf":
        paths = [
            plan_coordinated_path(world, i, side=1)
            for i in range(world.n_robots)
        ]
    else:
        paths = [
            plan_static_path(
                world,
                world.initial_state[i, :2],
                world.target_pose[i, :2],
            )
            for i in range(world.n_robots)
        ]
    state = world.initial_state.copy()
    docked = np.zeros(world.n_robots, dtype=bool)
    cursors = np.zeros(world.n_robots, dtype=int)
    arrival_times = np.full(world.n_robots, np.nan, dtype=float)
    game = initialise_pairwise_game(world.n_robots)
    positions = [state[:, :2].copy()]
    max_steps = int(math.ceil(horizon_s / dt_s))
    guard_interventions = 0
    closure_interventions = 0
    guard_intervention_norm = 0.0
    raw_barrier_violations = 0
    exec_barrier_violations = 0
    max_exec_residual = 0.0
    torque_saturation_events = 0
    min_clearance = float("inf")
    energy_wh = 0.0
    path_length_m = 0.0
    any_collision = False
    time_to_wrench_feasible = math.nan
    priority_threshold = 0.80 * float(np.sum(world.wrench_priority))
    extra_messages = 0
    final_residual = math.nan
    planned_phase = -1

    for step in range(max_steps):
        admission = np.ones(world.n_robots, dtype=float)
        if method in V4_GAME_METHODS:
            pending_phases = [
                phase
                for phase in range(phase_count)
                if np.any((phase_of_robot == phase) & (~docked))
            ]
            active_phase = pending_phases[0] if pending_phases else 0
            admission = (phase_of_robot == active_phase).astype(float)
            admission[docked] = 0.0
            extra_messages += int(world.n_robots)
            if (
                world.scenario in {"cluttered_docking", "narrow_passage"}
                and active_phase != planned_phase
            ):
                parked = np.column_stack(
                    [
                        state[docked, :2],
                        np.full(int(np.count_nonzero(docked)), world.robot_radius_m),
                    ]
                )
                planning_obstacles = (
                    world.obstacles.copy()
                    if parked.size == 0
                    else np.vstack([world.obstacles, parked])
                )
                planning_world = replace(world, obstacles=planning_obstacles)
                for robot in np.flatnonzero(phase_of_robot == active_phase):
                    side = (
                        int(route_sides[robot])
                        if world.scenario == "narrow_passage"
                        else _shortest_route_side(world, int(robot))
                    )
                    paths[robot] = plan_coordinated_path(
                        planning_world,
                        int(robot),
                        side=side,
                    )
                    cursors[robot] = 0
                planned_phase = active_phase
        all_go = admission.copy()
        nominal_go, _ = nominal_path_acceleration(
            world,
            state,
            paths,
            cursors,
            docked,
            all_go,
        )
        conflict = predicted_conflicts(world, state, nominal_go)
        if method in V4_GAME_METHODS:
            game_active = (admission > 0.5) & (~docked)
            conflict = (
                conflict
                & game_active[:, None]
                & game_active[None, :]
            )
        continuous_scale: np.ndarray | None = None
        if method == "direct_hocbf":
            raw_actions = np.zeros(world.n_robots, dtype=int)
            actions = raw_actions.copy()
        elif method == "priority_hocbf":
            raw_actions = np.zeros(world.n_robots, dtype=int)
            bid = (
                world.wrench_priority
                + 0.035 * game.wait_age
                - 1e-6 * np.arange(world.n_robots)
            )
            bid = _apply_pair_ownership(
                game,
                conflict,
                bid,
                state,
                paths,
                cursors,
                docked,
            )
            actions, messages, _rounds = _distributed_independent_set(
                raw_actions,
                conflict,
                bid,
                docked,
            )
            extra_messages += messages
        elif method == "central_hocbf":
            raw_actions = np.zeros(world.n_robots, dtype=int)
            bid = world.wrench_priority + 0.035 * game.wait_age
            actions = _central_independent_set(
                raw_actions,
                conflict,
                bid,
                docked,
            )
        else:
            protocol = (
                "replicator"
                if method == "distributed_replicator_hocbf"
                else "projected_pd"
            )
            raw_actions, _costs, final_residual = solve_pairwise_game(
                game,
                conflict,
                world.wrench_priority,
                docked,
                protocol=protocol,
                iterations=game_iterations,
            )
            actions = raw_actions.copy()
            continuous_scale = game.preferences @ np.asarray([1.0, 0.42, 0.0])
            ownership_bid = (
                world.wrench_priority
                + 0.035 * game.wait_age
                - 1e-6 * np.arange(world.n_robots)
            )
            _apply_pair_ownership(
                game,
                conflict,
                ownership_bid,
                state,
                paths,
                cursors,
                docked,
            )
            for i in range(world.n_robots):
                for j in range(i + 1, world.n_robots):
                    if not conflict[i, j]:
                        continue
                    owner = int(game.pair_owner[_pair_index(world.n_robots, i, j)])
                    loser = j if owner == i else i
                    continuous_scale[owner] = max(continuous_scale[owner], 0.80)
                    continuous_scale[loser] = 0.0
                    extra_messages += 2
                    closure_interventions += 1
            continuous_scale *= admission
            continuous_scale[docked] = 0.0
        actions[docked] = 2
        closure_interventions += int(np.count_nonzero(actions != raw_actions))
        speed_scale = (
            continuous_scale
            if continuous_scale is not None
            else np.asarray([1.0, 0.44, 0.0])[actions]
        )
        admitted = (admission > 0.5) & (~docked)
        game.wait_age = np.where(
            admitted & (speed_scale < 0.12),
            np.minimum(game.wait_age + 1.0, 40.0),
            np.where(
                admitted,
                np.maximum(game.wait_age - 0.55, 0.0),
                game.wait_age,
            ),
        )
        game.wait_age[docked] = 0.0
        nominal, cursors = nominal_path_acceleration(
            world,
            state,
            paths,
            cursors,
            docked,
            speed_scale,
        )
        raw_residual = hocbf_residual(
            world,
            state,
            nominal,
            margin_m=hocbf_margin_m,
            rate_1=hocbf_rate,
            rate_2=hocbf_rate,
        )
        raw_barrier_violations += int(raw_residual > 1e-7)
        safe = project_hocbf_acceleration(
            world,
            state,
            nominal,
            docked,
            dt_s=dt_s,
            iterations=hocbf_iterations,
            margin_m=hocbf_margin_m,
            rate_1=hocbf_rate,
            rate_2=hocbf_rate,
        )
        guard_interventions += safe.interventions
        guard_intervention_norm += safe.intervention_norm
        before = state.copy()
        state, actual_acceleration, step_energy, saturated = execute_acceleration(
            world,
            state,
            safe.acceleration,
            docked,
            dt_s=dt_s,
        )
        energy_wh += step_energy
        torque_saturation_events += saturated
        exec_residual = hocbf_residual(
            world,
            before,
            actual_acceleration,
            margin_m=hocbf_margin_m,
            rate_1=hocbf_rate,
            rate_2=hocbf_rate,
        )
        exec_barrier_violations += int(exec_residual > 1e-6)
        max_exec_residual = max(max_exec_residual, exec_residual)
        path_length_m += float(
            np.sum(np.linalg.norm(state[:, :2] - before[:, :2], axis=1))
        )
        step_clearance, collided = _swept_clearance(world, before, state)
        min_clearance = min(min_clearance, step_clearance)
        any_collision = any_collision or collided
        positions.append(state[:, :2].copy())

        position_error = np.linalg.norm(
            state[:, :2] - world.target_pose[:, :2],
            axis=1,
        )
        orientation_error = np.abs(
            wrap_angle(state[:, 2] - world.target_pose[:, 2])
        )
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
        if (
            math.isnan(time_to_wrench_feasible)
            and float(np.sum(world.wrench_priority[docked])) >= priority_threshold
        ):
            time_to_wrench_feasible = (step + 1) * dt_s
        if np.all(docked) or any_collision:
            break

    position_error = np.linalg.norm(
        state[:, :2] - world.target_pose[:, :2],
        axis=1,
    )
    orientation_error = np.abs(
        wrap_angle(state[:, 2] - world.target_pose[:, 2])
    )
    arrival_success = bool(np.all(docked))
    safe_success = bool(arrival_success and not any_collision)
    docking_time = (
        float(np.nanmax(arrival_times))
        if arrival_success
        else float(horizon_s)
    )
    if math.isnan(time_to_wrench_feasible):
        time_to_wrench_feasible = float(horizon_s)
    kkt = np.asarray(game.kkt_trace, dtype=float)
    potential = np.asarray(game.potential_trace, dtype=float)
    runtime = time.perf_counter() - started
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
        max_exec_barrier_residual=float(max_exec_residual),
        torque_saturation_events=int(torque_saturation_events),
        mean_kkt_residual=float(np.mean(kkt)) if kkt.size else math.nan,
        final_kkt_residual=(
            float(kkt[-1])
            if kkt.size
            else float(final_residual)
        ),
        max_simplex_error=float(
            np.max(np.abs(np.sum(game.preferences, axis=1) - 1.0))
        ),
        max_capacity_violation=(
            float(max(game.capacity_trace))
            if game.capacity_trace
            else 0.0
        ),
        consensus_error=0.0,
        messages=int(game.messages + extra_messages),
        runtime_s=float(runtime),
        steps=len(positions) - 1,
        positions=np.asarray(positions),
        potential_trace=potential,
        kkt_trace=kkt,
    )