"""Demonstrative unicycle approach layer for SP1 E6.

This module stops when recruited robots reach fixed contact-approach poses. It
does not simulate docking, force exchange or payload transport.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld


@dataclass(frozen=True, slots=True)
class ApproachResult:
    summary: dict[str, float | int | bool | str]
    trajectories: pd.DataFrame
    obstacles: tuple[tuple[float, float, float, float], ...]
    contact_targets: np.ndarray


@dataclass(frozen=True, slots=True)
class ConditionedObstaclePlan:
    obstacles: tuple[tuple[float, float, float, float], ...]
    blocked_route_indices: tuple[int, ...]
    detoured_route_indices: tuple[int, ...]
    direct_lengths_m: tuple[float, ...]
    astar_lengths_m: tuple[float, ...]


def contact_targets(world: ResourceWorld, assignment: np.ndarray, radius_m: float = 0.65) -> np.ndarray:
    targets = world.robot_positions_m.copy()
    for load in range(world.n_loads):
        members = np.flatnonzero(assignment == load)
        for rank, robot in enumerate(members):
            angle = 2.0 * math.pi * rank / max(len(members), 1)
            targets[robot] = world.load_positions_m[load] + radius_m * np.asarray([math.cos(angle), math.sin(angle)])
    return np.clip(targets, 0.2, 19.8)


def warehouse_obstacles(starts: np.ndarray, targets: np.ndarray) -> tuple[tuple[float, float, float, float], ...]:
    candidates = ((6.0, 7.6, 2.0, 15.5), (12.4, 14.0, 4.5, 18.0))
    endpoints = np.vstack([starts, targets])
    retained: list[tuple[float, float, float, float]] = []
    for rectangle in candidates:
        if not any(_inside(point, rectangle, margin=0.45) for point in endpoints):
            retained.append(rectangle)
    return tuple(retained)


def segment_intersects_rectangle(
    start: np.ndarray,
    target: np.ndarray,
    rectangle: tuple[float, float, float, float],
    *,
    margin: float = 0.0,
) -> bool:
    """Return whether a closed line segment intersects an axis-aligned box."""

    x0, x1, y0, y1 = rectangle
    bounds = (x0 - margin, x1 + margin, y0 - margin, y1 + margin)
    start = np.asarray(start, dtype=float)
    delta = np.asarray(target, dtype=float) - start
    lower, upper = 0.0, 1.0
    for coordinate, direction, minimum, maximum in (
        (start[0], delta[0], bounds[0], bounds[1]),
        (start[1], delta[1], bounds[2], bounds[3]),
    ):
        if abs(float(direction)) <= 1e-15:
            if coordinate < minimum or coordinate > maximum:
                return False
            continue
        first = (minimum - coordinate) / direction
        second = (maximum - coordinate) / direction
        entry, exit_ = min(first, second), max(first, second)
        lower = max(lower, float(entry))
        upper = min(upper, float(exit_))
        if lower > upper:
            return False
    return True


def _waypoint_path_length(start: np.ndarray, waypoints: list[np.ndarray]) -> float:
    previous = np.asarray(start, dtype=float)
    total = 0.0
    for waypoint in waypoints:
        total += float(np.linalg.norm(np.asarray(waypoint, dtype=float) - previous))
        previous = np.asarray(waypoint, dtype=float)
    return total


def conditioned_warehouse_obstacles(
    starts: np.ndarray,
    targets: np.ndarray,
    *,
    desired_obstacles: int = 2,
    endpoint_clearance_m: float = 0.80,
    detour_tolerance_m: float = 0.20,
) -> ConditionedObstaclePlan:
    """Construct warehouse barriers that block and measurably detour routes.

    Candidates are generated on the direct assigned segments, rejected if they
    cover any start/target pose, and accepted only when A* still finds a path
    whose length exceeds the corresponding direct distance.
    """

    starts = np.asarray(starts, dtype=float)
    targets = np.asarray(targets, dtype=float)
    if starts.shape != targets.shape or starts.ndim != 2 or starts.shape[1] != 2:
        raise ValueError("starts and targets must have matching shape (R, 2)")
    if desired_obstacles < 1:
        raise ValueError("desired_obstacles must be positive")
    endpoints = np.vstack([starts, targets]) if starts.size else np.empty((0, 2))
    direct = np.linalg.norm(targets - starts, axis=1) if starts.size else np.asarray([], dtype=float)
    obstacles: list[tuple[float, float, float, float]] = []
    source_routes: list[int] = []
    # Long paths offer enough clearance for a barrier and are tested first.
    for route in np.argsort(-direct):
        if direct[route] < 2.5:
            continue
        start, target = starts[route], targets[route]
        delta = target - start
        horizontal = abs(float(delta[0])) >= abs(float(delta[1]))
        accepted = False
        for fraction in (0.50, 0.40, 0.60, 0.30, 0.70, 0.22, 0.78):
            center = start + fraction * delta
            for thickness, span in ((0.60, 2.40), (0.50, 1.80), (0.40, 1.20)):
                if horizontal:
                    candidate = (
                        float(center[0] - thickness / 2),
                        float(center[0] + thickness / 2),
                        float(center[1] - span / 2),
                        float(center[1] + span / 2),
                    )
                else:
                    candidate = (
                        float(center[0] - span / 2),
                        float(center[0] + span / 2),
                        float(center[1] - thickness / 2),
                        float(center[1] + thickness / 2),
                    )
                if candidate[0] < 0.9 or candidate[1] > 19.1 or candidate[2] < 0.9 or candidate[3] > 19.1:
                    continue
                if any(_inside(point, candidate, margin=endpoint_clearance_m) for point in endpoints):
                    continue
                if any(
                    _rectangles_overlap(candidate, existing, margin=0.60)
                    for existing in obstacles
                ):
                    continue
                if not segment_intersects_rectangle(start, target, candidate):
                    continue
                trial_obstacles = tuple((*obstacles, candidate))
                waypoints = astar_waypoints(start, target, trial_obstacles)
                if not waypoints:
                    continue
                astar_length = _waypoint_path_length(start, waypoints)
                if astar_length <= float(direct[route]) + detour_tolerance_m:
                    continue
                obstacles.append(candidate)
                source_routes.append(int(route))
                accepted = True
                break
            if accepted:
                break
        if len(obstacles) >= desired_obstacles:
            break

    obstacle_tuple = tuple(obstacles)
    blocked: list[int] = []
    detoured: list[int] = []
    astar_lengths: list[float] = []
    for route, (start, target) in enumerate(zip(starts, targets, strict=True)):
        is_blocked = any(segment_intersects_rectangle(start, target, rectangle) for rectangle in obstacle_tuple)
        if is_blocked:
            blocked.append(route)
        waypoints = astar_waypoints(start, target, obstacle_tuple)
        length = _waypoint_path_length(start, waypoints) if waypoints else math.inf
        astar_lengths.append(length)
        if is_blocked and np.isfinite(length) and length > float(direct[route]) + detour_tolerance_m:
            detoured.append(route)
    # Every accepted obstacle was validated on its source route.  Keeping this
    # assertion close to construction prevents a later geometry change from
    # silently producing decorative obstacles.
    if obstacles and not set(source_routes).issubset(set(detoured)):
        raise RuntimeError("conditioned obstacle failed its A* detour invariant")
    return ConditionedObstaclePlan(
        obstacles=obstacle_tuple,
        blocked_route_indices=tuple(blocked),
        detoured_route_indices=tuple(detoured),
        direct_lengths_m=tuple(float(value) for value in direct),
        astar_lengths_m=tuple(float(value) for value in astar_lengths),
    )


def astar_waypoints(
    start: np.ndarray,
    goal: np.ndarray,
    obstacles: tuple[tuple[float, float, float, float], ...],
    *,
    resolution_m: float = 0.5,
    robot_radius_m: float = 0.75,
) -> list[np.ndarray]:
    size = int(round(20.0 / resolution_m))

    def to_cell(point: np.ndarray) -> tuple[int, int]:
        return tuple(np.clip(np.rint(point / resolution_m).astype(int), 0, size).tolist())

    def to_point(cell: tuple[int, int]) -> np.ndarray:
        return np.asarray(cell, dtype=float) * resolution_m

    start_cell, goal_cell = to_cell(start), to_cell(goal)
    blocked: set[tuple[int, int]] = set()
    for x in range(size + 1):
        for y in range(size + 1):
            point = to_point((x, y))
            if any(_inside(point, rectangle, margin=robot_radius_m) for rectangle in obstacles):
                blocked.add((x, y))
    blocked.discard(start_cell)
    blocked.discard(goal_cell)
    frontier: list[tuple[float, float, tuple[int, int]]] = [(0.0, 0.0, start_cell)]
    previous: dict[tuple[int, int], tuple[int, int]] = {}
    distance = {start_cell: 0.0}
    while frontier:
        _, current_cost, current = heapq.heappop(frontier)
        if current == goal_cell:
            break
        if current_cost > distance.get(current, math.inf) + 1e-12:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (current[0] + dx, current[1] + dy)
            if not (0 <= neighbour[0] <= size and 0 <= neighbour[1] <= size) or neighbour in blocked:
                continue
            candidate = current_cost + resolution_m
            if candidate + 1e-12 < distance.get(neighbour, math.inf):
                distance[neighbour] = candidate
                previous[neighbour] = current
                heuristic = resolution_m * (abs(goal_cell[0] - neighbour[0]) + abs(goal_cell[1] - neighbour[1]))
                heapq.heappush(frontier, (candidate + heuristic, candidate, neighbour))
    if goal_cell not in distance:
        return []
    cells = [goal_cell]
    while cells[-1] != start_cell:
        cells.append(previous[cells[-1]])
    cells.reverse()
    points = [to_point(cell) for cell in cells[1:]]
    if not points or np.linalg.norm(points[-1] - goal) > 1e-9:
        points.append(np.asarray(goal, dtype=float))
    return _compress_collinear(points)


def simulate_approach(
    world: ResourceWorld,
    assignment: np.ndarray,
    *,
    scenario: str,
    dt_s: float = 0.10,
    horizon_s: float = 80.0,
    k_rho: float = 1.25,
    k_alpha: float = 2.5,
    max_omega_rps: float = 2.0,
    estimated_energy_by_robot: np.ndarray | None = None,
    obstacles_override: tuple[tuple[float, float, float, float], ...] | None = None,
) -> ApproachResult:
    if scenario not in {"open", "warehouse"}:
        raise ValueError(f"Unknown E6 scenario: {scenario}")
    assignment = np.asarray(assignment, dtype=int)
    targets = contact_targets(world, assignment)
    assigned = np.flatnonzero(assignment >= 0)
    obstacles = (
        (
            tuple(obstacles_override)
            if obstacles_override is not None
            else warehouse_obstacles(world.robot_positions_m[assigned], targets[assigned])
        )
        if scenario == "warehouse"
        else ()
    )
    paths: dict[int, list[np.ndarray]] = {}
    for robot in assigned:
        paths[int(robot)] = (
            [targets[robot].copy()]
            if scenario == "open"
            else astar_waypoints(world.robot_positions_m[robot], targets[robot], obstacles)
        )

    positions = world.robot_positions_m.copy()
    rng = np.random.default_rng(world.seed + (0 if scenario == "open" else 1_000_003))
    headings = rng.uniform(-math.pi, math.pi, size=world.n_robots)
    indices = {int(robot): 0 for robot in assigned}
    arrived = np.zeros(world.n_robots, dtype=bool)
    arrival_time = np.full(world.n_robots, math.nan)
    travelled = np.zeros(world.n_robots)
    collision_samples = 0
    rows: list[dict[str, float | int | bool | str]] = []
    steps = int(math.ceil(horizon_s / dt_s))
    for step_index in range(steps + 1):
        time_s = step_index * dt_s
        for robot in assigned:
            robot = int(robot)
            path = paths[robot]
            if not path:
                continue
            while indices[robot] < len(path) - 1 and np.linalg.norm(path[indices[robot]] - positions[robot]) <= 0.18:
                indices[robot] += 1
            target = path[indices[robot]]
            rho = float(np.linalg.norm(target - positions[robot]))
            if indices[robot] == len(path) - 1 and rho <= 0.22:
                if not arrived[robot]:
                    arrived[robot] = True
                    arrival_time[robot] = time_s
            if not arrived[robot] and step_index < steps:
                bearing = math.atan2(target[1] - positions[robot, 1], target[0] - positions[robot, 0])
                alpha = _wrap_angle(bearing - headings[robot])
                velocity = min(world.max_speed_mps[robot], k_rho * rho * max(0.0, math.cos(alpha)))
                omega = float(np.clip(k_alpha * alpha, -max_omega_rps, max_omega_rps))
                previous_position = positions[robot].copy()
                positions[robot, 0] += dt_s * velocity * math.cos(headings[robot])
                positions[robot, 1] += dt_s * velocity * math.sin(headings[robot])
                headings[robot] = _wrap_angle(headings[robot] + dt_s * omega)
                positions[robot] = np.clip(positions[robot], 0.0, 20.0)
                travelled[robot] += float(np.linalg.norm(positions[robot] - previous_position))
            if any(_inside(positions[robot], rectangle) for rectangle in obstacles):
                collision_samples += 1
            rows.append(
                {
                    "scenario": scenario,
                    "time_s": time_s,
                    "robot_id": robot,
                    "load_id": int(assignment[robot]),
                    "x_m": float(positions[robot, 0]),
                    "y_m": float(positions[robot, 1]),
                    "theta_rad": float(headings[robot]),
                    "target_x_m": float(targets[robot, 0]),
                    "target_y_m": float(targets[robot, 1]),
                    "arrived": bool(arrived[robot]),
                }
            )
        if assigned.size and np.all(arrived[assigned]):
            break

    direct_distance = np.linalg.norm(world.robot_positions_m[assigned] - targets[assigned], axis=1) if assigned.size else np.asarray([])
    estimated_energy = (
        direct_distance * world.energy_per_m[assigned]
        if estimated_energy_by_robot is None
        else np.asarray(estimated_energy_by_robot, dtype=float)[assigned]
    )
    actual_energy = travelled[assigned] * world.energy_per_m[assigned]
    battery_violations = int(np.sum(actual_energy > world.battery_energy[assigned] + 1e-9))
    complete_loads = 0
    coalition_arrival_times: list[float] = []
    for load in range(world.n_loads):
        members = np.flatnonzero(assignment == load)
        if members.size and np.all(arrived[members]):
            complete_loads += 1
            coalition_arrival_times.append(float(np.nanmax(arrival_time[members])))
    summary: dict[str, float | int | bool | str] = {
        "scenario": scenario,
        "assigned_robots": int(assigned.size),
        "arrived_robots": int(np.sum(arrived[assigned])) if assigned.size else 0,
        "arrival_rate": float(np.mean(arrived[assigned])) if assigned.size else 0.0,
        "complete_coalitions": complete_loads,
        "coalition_arrival_time_s": float(max(coalition_arrival_times)) if coalition_arrival_times else math.nan,
        "distance_m": float(np.sum(travelled[assigned])),
        "estimated_energy": float(np.sum(estimated_energy)),
        "actual_energy": float(np.sum(actual_energy)),
        "energy_model_error": float(np.sum(actual_energy) - np.sum(estimated_energy)),
        "battery_violations": battery_violations,
        "path_failures": int(sum(not paths[int(robot)] for robot in assigned)),
        "sampled_obstacle_intrusions": collision_samples,
        "assignment_changes": 0,
        "target_changed": False,
        "obstacle_count": len(obstacles),
        "blocked_direct_paths": int(
            sum(
                any(
                    segment_intersects_rectangle(world.robot_positions_m[robot], targets[robot], rectangle)
                    for rectangle in obstacles
                )
                for robot in assigned
            )
        ),
        "astar_detoured_paths": int(
            sum(
                bool(paths[int(robot)])
                and _waypoint_path_length(world.robot_positions_m[robot], paths[int(robot)])
                > float(np.linalg.norm(world.robot_positions_m[robot] - targets[robot])) + 0.20
                for robot in assigned
            )
        ),
    }
    return ApproachResult(summary=summary, trajectories=pd.DataFrame(rows), obstacles=obstacles, contact_targets=targets)


def build_warehouse_route_costs(
    world: ResourceWorld,
    weights: Mapping[str, float],
    *,
    reserve_energy: float = 5.0,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Estimate recruitment cost with A* path length instead of Euclidean range."""

    obstacles = warehouse_obstacles(world.robot_positions_m, world.load_positions_m)
    distance = np.full((world.n_robots, world.n_loads), math.inf)
    for robot in range(world.n_robots):
        for load in range(world.n_loads):
            waypoints = astar_waypoints(world.robot_positions_m[robot], world.load_positions_m[load], obstacles)
            if not waypoints:
                continue
            previous = world.robot_positions_m[robot]
            total = 0.0
            for waypoint in waypoints:
                total += float(np.linalg.norm(waypoint - previous))
                previous = waypoint
            distance[robot, load] = total
    travel_time = distance / np.maximum(world.max_speed_mps[:, None], 1e-9)
    energy = distance * world.energy_per_m[:, None]
    compatible = np.isfinite(distance) & (energy + float(reserve_energy) <= world.battery_energy[:, None])
    costs = (
        float(weights.get("distance", 0.45)) * distance
        + float(weights.get("time", 0.25)) * travel_time
        + float(weights.get("energy", 0.30)) * energy
    )
    costs = np.where(compatible, costs, np.inf)
    return costs, compatible, {"distance": distance, "time": travel_time, "energy": energy}


def _inside(point: np.ndarray, rectangle: tuple[float, float, float, float], margin: float = 0.0) -> bool:
    x0, x1, y0, y1 = rectangle
    return bool(x0 - margin <= point[0] <= x1 + margin and y0 - margin <= point[1] <= y1 + margin)


def _rectangles_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    *,
    margin: float = 0.0,
) -> bool:
    return not (
        left[1] + margin < right[0]
        or right[1] + margin < left[0]
        or left[3] + margin < right[2]
        or right[3] + margin < left[2]
    )


def _wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def _compress_collinear(points: list[np.ndarray]) -> list[np.ndarray]:
    if len(points) < 3:
        return points
    result = [points[0]]
    for index in range(1, len(points) - 1):
        before = points[index] - result[-1]
        after = points[index + 1] - points[index]
        if abs(float(before[0] * after[1] - before[1] * after[0])) > 1e-12:
            result.append(points[index])
    result.append(points[-1])
    return result


__all__ = [
    "ApproachResult",
    "ConditionedObstaclePlan",
    "astar_waypoints",
    "build_warehouse_route_costs",
    "contact_targets",
    "conditioned_warehouse_obstacles",
    "segment_intersects_rectangle",
    "simulate_approach",
    "warehouse_obstacles",
]
