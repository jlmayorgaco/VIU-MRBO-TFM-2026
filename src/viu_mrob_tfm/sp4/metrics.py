"""Metrics for SP4 post-allocation AMR motion experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp4.methods import SP4TrajectoryResult
from viu_mrob_tfm.sp4.scenario import SP4Problem


@dataclass(frozen=True, slots=True)
class SP4Metrics:
    arrival_success_rate: float
    all_arrived: bool
    timeout_rate: float
    mean_arrival_time_s: float
    max_arrival_time_s: float
    travel_distance_m: float
    mean_path_length_m: float
    path_efficiency_ratio: float
    energy_proxy_wh: float
    collision_count: int
    collision_rate: float
    safety_violation_count: int
    min_robot_clearance_m: float
    min_obstacle_clearance_m: float
    mean_clearance_m: float
    mean_speed_mps: float
    max_speed_mps: float
    max_speed_violation_mps: float
    congestion_delay_s: float
    communication_messages: int
    runtime_ms: float
    score_value: float
    reference_score_value: float
    signed_score_delta_vs_reference: float
    performance_gap_vs_reference: float
    optimality_gap_vs_reference: float
    arrived_robots: int
    timed_out_robots: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_motion(
    problem: SP4Problem,
    result: SP4TrajectoryResult,
    *,
    runtime_ms: float | None = None,
    reference_result: SP4TrajectoryResult | None = None,
    centralized: bool = False,
) -> SP4Metrics:
    """Evaluate one SP4 trajectory rollout."""

    n = len(problem.world.robots)
    reached = np.asarray(result.reached, dtype=bool)
    arrived_count = int(np.sum(reached))
    timeout_count = int(n - arrived_count)
    arrivals = np.asarray(result.arrival_times_s, dtype=float)
    finite_arrivals = arrivals[np.isfinite(arrivals)]
    path_lengths = robot_path_lengths(result)
    direct_lengths = np.linalg.norm(problem.target_xy - result.positions[0], axis=1)
    travel_distance = float(np.sum(path_lengths))
    direct_total = float(np.sum(direct_lengths))
    path_efficiency = float(direct_total / max(travel_distance, 1e-9)) if direct_total > 0.0 else 1.0
    robot_clearance, obstacle_clearance, collision_count, safety_count = clearance_diagnostics(problem, result)
    speeds = np.linalg.norm(result.velocities, axis=2)
    max_limits = np.asarray([robot.spec.max_speed for robot in problem.world.robots], dtype=float)
    max_violation = float(np.max(np.maximum(speeds - max_limits[None, :], 0.0))) if speeds.size else 0.0
    direct_time = direct_lengths / np.maximum(max_limits, 1e-9)
    completed_arrival = np.where(np.isfinite(arrivals), arrivals, problem.horizon_s)
    congestion_delay = float(np.mean(np.maximum(completed_arrival - direct_time, 0.0)))
    messages = communication_messages(problem, result, centralized=centralized)
    energy = energy_proxy_wh(problem, path_lengths, speeds)
    score = motion_score(
        arrival_success_rate=float(arrived_count / max(n, 1)),
        collision_rate=float(collision_count / max(n * max(len(result.time_s), 1), 1)),
        timeout_rate=float(timeout_count / max(n, 1)),
        mean_arrival_time_s=float(np.mean(completed_arrival)) if completed_arrival.size else 0.0,
        travel_distance_m=travel_distance,
        energy_proxy_wh=energy,
    )
    reference_score = score
    if reference_result is not None:
        reference_metrics = evaluate_motion(problem, reference_result, runtime_ms=reference_result.runtime_ms, centralized=True)
        reference_score = reference_metrics.score_value
    signed_delta = float(score - reference_score)
    score_scale = max(abs(reference_score), 100.0 * max(n, 1), 1.0)
    gap = max(0.0, float((reference_score - score) / score_scale))
    return SP4Metrics(
        arrival_success_rate=float(arrived_count / max(n, 1)),
        all_arrived=bool(arrived_count == n),
        timeout_rate=float(timeout_count / max(n, 1)),
        mean_arrival_time_s=float(np.mean(finite_arrivals)) if finite_arrivals.size else float(problem.horizon_s),
        max_arrival_time_s=float(np.max(finite_arrivals)) if finite_arrivals.size else float(problem.horizon_s),
        travel_distance_m=travel_distance,
        mean_path_length_m=float(np.mean(path_lengths)) if path_lengths.size else 0.0,
        path_efficiency_ratio=float(np.clip(path_efficiency, 0.0, 1.5)),
        energy_proxy_wh=energy,
        collision_count=int(collision_count),
        collision_rate=float(collision_count / max(n * max(len(result.time_s), 1), 1)),
        safety_violation_count=int(safety_count),
        min_robot_clearance_m=float(robot_clearance[0]),
        min_obstacle_clearance_m=float(obstacle_clearance[0]),
        mean_clearance_m=float(np.mean([robot_clearance[1], obstacle_clearance[1]])),
        mean_speed_mps=float(np.mean(speeds)) if speeds.size else 0.0,
        max_speed_mps=float(np.max(speeds)) if speeds.size else 0.0,
        max_speed_violation_mps=max_violation,
        congestion_delay_s=congestion_delay,
        communication_messages=messages,
        runtime_ms=float(result.runtime_ms if runtime_ms is None else runtime_ms),
        score_value=score,
        reference_score_value=reference_score,
        signed_score_delta_vs_reference=signed_delta,
        performance_gap_vs_reference=gap,
        optimality_gap_vs_reference=gap,
        arrived_robots=arrived_count,
        timed_out_robots=timeout_count,
    )


def robot_status_rows(problem: SP4Problem, result: SP4TrajectoryResult) -> list[dict[str, Any]]:
    """Return one diagnostic row per robot."""

    path_lengths = robot_path_lengths(result)
    direct_lengths = np.linalg.norm(problem.target_xy - result.positions[0], axis=1)
    rows: list[dict[str, Any]] = []
    for idx, robot in enumerate(problem.world.robots):
        final_distance = float(np.linalg.norm(problem.target_xy[idx] - result.positions[-1, idx]))
        arrived = bool(result.reached[idx])
        rows.append(
            {
                "robot_id": robot.identifier,
                "robot_index": idx + 1,
                "target_label": problem.target_labels[idx],
                "start_x": float(result.positions[0, idx, 0]),
                "start_y": float(result.positions[0, idx, 1]),
                "target_x": float(problem.target_xy[idx, 0]),
                "target_y": float(problem.target_xy[idx, 1]),
                "final_x": float(result.positions[-1, idx, 0]),
                "final_y": float(result.positions[-1, idx, 1]),
                "arrived": arrived,
                "arrival_time_s": float(result.arrival_times_s[idx]) if np.isfinite(result.arrival_times_s[idx]) else "",
                "final_target_error_m": final_distance,
                "path_length_m": float(path_lengths[idx]),
                "direct_distance_m": float(direct_lengths[idx]),
                "path_efficiency_ratio": float(direct_lengths[idx] / max(path_lengths[idx], 1e-9)),
                "battery_fraction": float(robot.battery_fraction),
                "max_speed_mps": float(robot.spec.max_speed),
            }
        )
    return rows


def trajectory_sample_rows(problem: SP4Problem, result: SP4TrajectoryResult, *, max_frames: int = 80) -> list[dict[str, Any]]:
    """Return a compact long-form trajectory table for debugging and plots."""

    total = len(result.time_s)
    stride = max(1, int(np.ceil(total / max(max_frames, 1))))
    rows: list[dict[str, Any]] = []
    for t_idx in range(0, total, stride):
        for robot_idx, robot in enumerate(problem.world.robots):
            rows.append(
                {
                    "time_s": float(result.time_s[t_idx]),
                    "robot_id": robot.identifier,
                    "robot_index": robot_idx + 1,
                    "x": float(result.positions[t_idx, robot_idx, 0]),
                    "y": float(result.positions[t_idx, robot_idx, 1]),
                    "vx": float(result.velocities[t_idx, robot_idx, 0]),
                    "vy": float(result.velocities[t_idx, robot_idx, 1]),
                    "target_x": float(problem.target_xy[robot_idx, 0]),
                    "target_y": float(problem.target_xy[robot_idx, 1]),
                }
            )
    return rows


def robot_path_lengths(result: SP4TrajectoryResult) -> np.ndarray:
    deltas = np.diff(result.positions, axis=0)
    return np.sum(np.linalg.norm(deltas, axis=2), axis=0)


def clearance_diagnostics(problem: SP4Problem, result: SP4TrajectoryResult) -> tuple[tuple[float, float], tuple[float, float], int, int]:
    robot_clearances: list[float] = []
    obstacle_clearances: list[float] = []
    robot_collision_steps = 0
    obstacle_collision_steps = 0
    safe_robot = 2.0 * problem.robot_radius_m
    for frame in result.positions:
        for i in range(frame.shape[0]):
            for j in range(i + 1, frame.shape[0]):
                clearance = float(np.linalg.norm(frame[i] - frame[j]) - safe_robot)
                robot_clearances.append(clearance)
                if clearance < 0.0:
                    robot_collision_steps += 1
        for pos in frame:
            for obstacle in problem.world.map.obstacles:
                clearance = float(np.linalg.norm(pos - obstacle.center) - obstacle.radius - problem.robot_radius_m)
                obstacle_clearances.append(clearance)
                if clearance < 0.0:
                    obstacle_collision_steps += 1
    if not robot_clearances:
        robot_clearances = [float(problem.world.map.size_m)]
    if not obstacle_clearances:
        obstacle_clearances = [float(problem.world.map.size_m)]
    finite_robot = np.asarray([value for value in robot_clearances if np.isfinite(value)], dtype=float)
    finite_obstacle = np.asarray([value for value in obstacle_clearances if np.isfinite(value)], dtype=float)
    robot_tuple = (float(np.min(finite_robot)) if finite_robot.size else float("inf"), float(np.mean(finite_robot)) if finite_robot.size else float("inf"))
    obstacle_tuple = (float(np.min(finite_obstacle)) if finite_obstacle.size else float("inf"), float(np.mean(finite_obstacle)) if finite_obstacle.size else float("inf"))
    safety_count = sum(1 for value in robot_clearances + obstacle_clearances if value < problem.safety_margin_m)
    return robot_tuple, obstacle_tuple, int(robot_collision_steps + obstacle_collision_steps), int(safety_count)


def communication_messages(problem: SP4Problem, result: SP4TrajectoryResult, *, centralized: bool) -> int:
    n = len(problem.world.robots)
    frames = max(len(result.time_s) - 1, 1)
    if centralized:
        return int(frames * n * max(n - 1, 0))
    radius = float(problem.communication_radius)
    if not np.isfinite(radius):
        return int(frames * n * max(n - 1, 0))
    total = 0
    for frame in result.positions[:-1]:
        distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
        total += int(np.sum((distances <= radius) & (distances > 0.0)))
    return total


def energy_proxy_wh(problem: SP4Problem, path_lengths: np.ndarray, speeds: np.ndarray) -> float:
    per_meter = np.asarray([robot.spec.battery.discharge_per_meter * robot.spec.battery.capacity_wh for robot in problem.world.robots], dtype=float)
    travel_energy = float(np.sum(path_lengths * per_meter))
    speed_penalty = 0.03 * float(np.sum(speeds**2)) * problem.dt_s
    return travel_energy + speed_penalty


def motion_score(
    *,
    arrival_success_rate: float,
    collision_rate: float,
    timeout_rate: float,
    mean_arrival_time_s: float,
    travel_distance_m: float,
    energy_proxy_wh: float,
) -> float:
    return float(
        120.0 * arrival_success_rate
        - 2400.0 * collision_rate
        - 55.0 * timeout_rate
        - 1.6 * mean_arrival_time_s
        - 0.22 * travel_distance_m
        - 0.010 * energy_proxy_wh
    )
