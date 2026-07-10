"""Metrics for SP6 operational robustness and recovery experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp6.methods import SP6TrajectoryResult, communication_coverage, communication_messages, sp6_method_metadata
from viu_mrob_tfm.sp6.scenario import SP6Problem


@dataclass(frozen=True, slots=True)
class SP6Metrics:
    feasible_load_count: int
    completed_load_count: int
    task_completion_rate: float
    recovery_success: bool
    recovery_time_s: float
    load_target_reached_rate: float
    mean_final_pose_error_m: float
    max_final_pose_error_m: float
    mean_final_orientation_error_deg: float
    max_final_orientation_error_deg: float
    lost_load_rate: float
    infeasible_load_count: int
    infeasible_load_detection_rate: float
    post_event_wrench_feasible_rate: float
    mean_wrench_residual_norm: float
    min_wrench_margin: float
    unsupported_time_s: float
    load_pause_time_s: float
    degraded_speed_time_s: float
    replacement_arrival_time_s: float
    final_assigned_loads: int
    final_idle_robots: int
    reassignment_count: int
    final_active_robot_rate: float
    failed_robot_count: int
    battery_margin_final: float
    min_battery_fraction: float
    communication_coverage_ratio: float
    communication_messages: int
    collision_count: int
    collision_rate: float
    safety_violation_count: int
    min_robot_clearance_m: float
    min_obstacle_clearance_m: float
    min_load_clearance_m: float
    travel_distance_m: float
    mean_path_length_m: float
    path_efficiency_ratio: float
    energy_proxy_wh: float
    mean_speed_mps: float
    max_speed_mps: float
    max_speed_violation_mps: float
    runtime_ms: float
    score_value: float
    reference_score_value: float
    signed_score_delta_vs_reference: float
    performance_gap_vs_reference: float
    optimality_gap_vs_reference: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_recovery(
    problem: SP6Problem,
    result: SP6TrajectoryResult,
    *,
    reference_result: SP6TrajectoryResult | None = None,
    centralized: bool = False,
) -> SP6Metrics:
    """Evaluate one SP6 robustness rollout."""

    feasible_after_event = np.asarray(result.feasible_after_event, dtype=bool)
    final_completed = np.asarray(result.completed_loads[-1], dtype=bool)
    feasible_count = int(np.sum(feasible_after_event))
    infeasible_count = int(len(feasible_after_event) - feasible_count)
    completed_feasible = final_completed & feasible_after_event
    completed_count = int(np.sum(completed_feasible))
    task_completion_rate = float(completed_count / max(feasible_count, 1))
    lost_load_rate = float(1.0 - task_completion_rate) if feasible_count else 0.0

    final_labels = np.asarray(result.labels[-1], dtype=int)
    final_active = np.asarray(result.active_mask[-1], dtype=bool)
    final_battery = np.asarray(result.battery_fraction[-1], dtype=float)
    event_mask = result.time_s >= problem.event.time_s
    feasible_indices = np.flatnonzero(feasible_after_event)
    post_event_margins = result.wrench_margins[np.ix_(event_mask, feasible_indices)] if feasible_indices.size else np.zeros((0, 0))
    post_event_wrench_rate = float(np.mean(post_event_margins >= -0.03)) if post_event_margins.size else 1.0
    final_wrench_ok = bool(np.all(result.wrench_margins[-1, feasible_indices] >= -0.03)) if feasible_indices.size else True
    pose_errors = np.linalg.norm(problem.target_load_poses[:, :2] - result.load_pose[-1, :, :2], axis=1)
    theta_errors = np.asarray([abs(_wrap_angle(float(problem.target_load_poses[idx, 2] - result.load_pose[-1, idx, 2]))) for idx in range(len(problem.world.loads))], dtype=float)
    target_reached_by_load = (pose_errors <= problem.pose_tolerance_m) & (theta_errors <= problem.orientation_tolerance_rad)
    target_reached_rate = float(np.mean(target_reached_by_load[feasible_after_event])) if feasible_count else 1.0
    infeasible_detection = infeasible_load_detection_rate(problem, result)
    clearance = clearance_diagnostics(problem, result)
    path_lengths = robot_path_lengths(result)
    speeds = np.linalg.norm(result.robot_velocities, axis=2)
    max_limits = np.asarray([robot.spec.max_speed for robot in problem.world.robots], dtype=float)
    max_violation = float(np.max(np.maximum(speeds - max_limits[None, :], 0.0))) if speeds.size else 0.0
    messages = communication_messages(problem, result, centralized=centralized)
    coverage = communication_coverage(problem, result, centralized=centralized)
    energy = energy_proxy_wh(problem, result, path_lengths)
    recovery_time = recovery_time_s(problem, result, feasible_after_event)
    collision_rate = float(clearance["collision_count"] / max(_collision_opportunities(problem, result), 1))
    success = bool(
        feasible_count > 0
        and completed_count == feasible_count
        and target_reached_rate >= 0.999
        and final_wrench_ok
        and collision_rate <= 0.03
        and max_violation <= 1e-6
    )
    score = recovery_score(
        recovery_success=success,
        task_completion_rate=task_completion_rate,
        lost_load_rate=lost_load_rate,
        infeasible_load_detection_rate=infeasible_detection,
        post_event_wrench_feasible_rate=post_event_wrench_rate,
        collision_rate=collision_rate,
        safety_violation_count=int(clearance["safety_violation_count"]),
        recovery_time_s=recovery_time,
        travel_distance_m=float(np.sum(path_lengths)),
        energy_proxy_wh=energy,
        communication_messages=messages,
        reassignment_count=int(result.reassignment_count),
    )
    reference_score = score
    if reference_result is not None:
        reference_score = evaluate_recovery(problem, reference_result, centralized=True).score_value
    signed_delta = float(score - reference_score)
    score_scale = max(abs(reference_score), 220.0, 1.0)
    gap = float(np.clip((reference_score - score) / score_scale, 0.0, 1.0))
    assigned_loads = {int(label) for label in final_labels if int(label) > 0}
    reserves = np.asarray([robot.spec.battery.reserve_fraction for robot in problem.world.robots], dtype=float)
    return SP6Metrics(
        feasible_load_count=feasible_count,
        completed_load_count=completed_count,
        task_completion_rate=task_completion_rate,
        recovery_success=success,
        recovery_time_s=recovery_time,
        load_target_reached_rate=target_reached_rate,
        mean_final_pose_error_m=float(np.mean(pose_errors[feasible_after_event])) if feasible_count else 0.0,
        max_final_pose_error_m=float(np.max(pose_errors[feasible_after_event])) if feasible_count else 0.0,
        mean_final_orientation_error_deg=float(np.degrees(np.mean(theta_errors[feasible_after_event]))) if feasible_count else 0.0,
        max_final_orientation_error_deg=float(np.degrees(np.max(theta_errors[feasible_after_event]))) if feasible_count else 0.0,
        lost_load_rate=lost_load_rate,
        infeasible_load_count=infeasible_count,
        infeasible_load_detection_rate=infeasible_detection,
        post_event_wrench_feasible_rate=post_event_wrench_rate,
        mean_wrench_residual_norm=float(np.mean(result.wrench_residuals[np.ix_(event_mask, feasible_indices)])) if post_event_margins.size else 0.0,
        min_wrench_margin=float(np.min(post_event_margins)) if post_event_margins.size else 0.0,
        unsupported_time_s=float(np.sum((result.support_level[event_mask] < 0.18) & feasible_after_event[None, :]) * problem.dt_s) if np.any(event_mask) else 0.0,
        load_pause_time_s=float(np.sum(result.load_paused_mask[event_mask] & feasible_after_event[None, :]) * problem.dt_s) if np.any(event_mask) else 0.0,
        degraded_speed_time_s=float(np.sum(result.degraded_speed_mask[event_mask] & feasible_after_event[None, :]) * problem.dt_s) if np.any(event_mask) else 0.0,
        replacement_arrival_time_s=replacement_arrival_time_s(problem, result, feasible_after_event),
        final_assigned_loads=len(assigned_loads),
        final_idle_robots=int(np.sum((final_labels <= 0) | (~final_active))),
        reassignment_count=int(result.reassignment_count),
        final_active_robot_rate=float(np.mean(final_active)) if final_active.size else 0.0,
        failed_robot_count=int(np.sum(~final_active)),
        battery_margin_final=float(np.min(final_battery - reserves)) if final_battery.size else 0.0,
        min_battery_fraction=float(np.min(result.battery_fraction)) if result.battery_fraction.size else 0.0,
        communication_coverage_ratio=coverage,
        communication_messages=messages,
        collision_count=int(clearance["collision_count"]),
        collision_rate=collision_rate,
        safety_violation_count=int(clearance["safety_violation_count"]),
        min_robot_clearance_m=float(clearance["min_robot_clearance_m"]),
        min_obstacle_clearance_m=float(clearance["min_obstacle_clearance_m"]),
        min_load_clearance_m=float(clearance["min_load_clearance_m"]),
        travel_distance_m=float(np.sum(path_lengths)),
        mean_path_length_m=float(np.mean(path_lengths)) if path_lengths.size else 0.0,
        path_efficiency_ratio=path_efficiency_ratio(problem, result, path_lengths),
        energy_proxy_wh=energy,
        mean_speed_mps=float(np.mean(speeds)) if speeds.size else 0.0,
        max_speed_mps=float(np.max(speeds)) if speeds.size else 0.0,
        max_speed_violation_mps=max_violation,
        runtime_ms=float(result.runtime_ms),
        score_value=score,
        reference_score_value=reference_score,
        signed_score_delta_vs_reference=signed_delta,
        performance_gap_vs_reference=gap,
        optimality_gap_vs_reference=gap,
    )


def load_status_rows(problem: SP6Problem, result: SP6TrajectoryResult) -> list[dict[str, Any]]:
    """Return one diagnostic row per load."""

    rows = []
    labels = np.asarray(result.labels[-1], dtype=int)
    active = np.asarray(result.active_mask[-1], dtype=bool)
    battery = np.asarray(result.battery_fraction[-1], dtype=float)
    for load_idx, load in enumerate(problem.world.loads):
        members = np.flatnonzero((labels == load_idx + 1) & active)
        capacity = float(sum(_effective_payload(problem, battery, int(idx)) for idx in members))
        force = float(sum(problem.world.robots[int(idx)].spec.capacity.force_limit_n for idx in members))
        torque = float(sum(problem.world.robots[int(idx)].spec.capacity.torque_limit_nm for idx in members))
        demand = float(problem.load_demand_at(load_idx, problem.event.time_s, observed=False))
        wrench_force = float(np.linalg.norm(load.wrench.force_xy))
        wrench_torque = float(abs(load.wrench.torque_z))
        completed = bool(result.completed_loads[-1, load_idx])
        feasible = bool(result.feasible_after_event[load_idx])
        pose_error = float(np.linalg.norm(problem.target_load_poses[load_idx, :2] - result.load_pose[-1, load_idx, :2]))
        theta_error = abs(_wrap_angle(float(problem.target_load_poses[load_idx, 2] - result.load_pose[-1, load_idx, 2])))
        rows.append(
            {
                "load_id": load.identifier,
                "load_index": load_idx + 1,
                "mass_kg": float(load.mass_kg),
                "post_event_demand_kg": demand,
                "min_coalition_size": int(load.min_coalition_size),
                "assigned_robots": int(len(members)),
                "assigned_capacity_kg": capacity,
                "assigned_force_n": force,
                "assigned_torque_nm": torque,
                "wrench_force_demand_n": wrench_force,
                "wrench_torque_demand_nm": wrench_torque,
                "feasible_after_event": feasible,
                "completed": completed,
                "physically_feasible_final": bool(load_physical_feasible(problem, result, load_idx)),
                "final_unassigned_infeasible": bool((not feasible) and len(members) == 0),
                "final_pose_x": float(result.load_pose[-1, load_idx, 0]),
                "final_pose_y": float(result.load_pose[-1, load_idx, 1]),
                "final_pose_theta_rad": float(result.load_pose[-1, load_idx, 2]),
                "target_pose_x": float(problem.target_load_poses[load_idx, 0]),
                "target_pose_y": float(problem.target_load_poses[load_idx, 1]),
                "target_pose_theta_rad": float(problem.target_load_poses[load_idx, 2]),
                "final_pose_error_m": pose_error,
                "final_orientation_error_deg": float(np.degrees(theta_error)),
                "final_wrench_margin": float(result.wrench_margins[-1, load_idx]),
                "unsupported_time_s": float(np.sum(result.support_level[:, load_idx] < 0.18) * problem.dt_s),
                "load_pause_time_s": float(np.sum(result.load_paused_mask[:, load_idx]) * problem.dt_s),
                "degraded_speed_time_s": float(np.sum(result.degraded_speed_mask[:, load_idx]) * problem.dt_s),
                "completion_time_s": float(result.completion_times_s[load_idx]) if np.isfinite(result.completion_times_s[load_idx]) else "",
                "destination_x": float(load.destination[0]),
                "destination_y": float(load.destination[1]),
            }
        )
    return rows


def robot_status_rows(problem: SP6Problem, result: SP6TrajectoryResult) -> list[dict[str, Any]]:
    """Return one diagnostic row per robot."""

    path_lengths = robot_path_lengths(result)
    rows = []
    for idx, robot in enumerate(problem.world.robots):
        label = int(result.labels[-1, idx])
        rows.append(
            {
                "robot_id": robot.identifier,
                "robot_index": idx + 1,
                "final_active": bool(result.active_mask[-1, idx]),
                "assigned_load_label": label,
                "start_x": float(result.robot_positions[0, idx, 0]),
                "start_y": float(result.robot_positions[0, idx, 1]),
                "final_x": float(result.robot_positions[-1, idx, 0]),
                "final_y": float(result.robot_positions[-1, idx, 1]),
                "path_length_m": float(path_lengths[idx]),
                "initial_battery_fraction": float(result.battery_fraction[0, idx]),
                "final_battery_fraction": float(result.battery_fraction[-1, idx]),
                "battery_reserve_fraction": float(robot.spec.battery.reserve_fraction),
                "max_speed_mps": float(robot.spec.max_speed),
                "force_limit_n": float(robot.spec.capacity.force_limit_n),
                "torque_limit_nm": float(robot.spec.capacity.torque_limit_nm),
                "payload_kg": float(robot.spec.capacity.payload_kg),
            }
        )
    return rows


def trajectory_sample_rows(problem: SP6Problem, result: SP6TrajectoryResult, *, max_frames: int = 90) -> list[dict[str, Any]]:
    """Return compact long-form trajectory samples for debugging."""

    total = len(result.time_s)
    stride = max(1, int(np.ceil(total / max(max_frames, 1))))
    rows: list[dict[str, Any]] = []
    for t_idx in range(0, total, stride):
        t_s = float(result.time_s[t_idx])
        for robot_idx, robot in enumerate(problem.world.robots):
            label = int(result.labels[t_idx, robot_idx])
            target = _target_for_robot(problem, result.labels[t_idx], robot_idx, result.load_pose[t_idx]) if label > 0 else result.robot_positions[t_idx, robot_idx]
            rows.append(
                {
                    "time_s": t_s,
                    "entity": "robot",
                    "entity_id": robot.identifier,
                    "robot_index": robot_idx + 1,
                    "assigned_load_label": label,
                    "active": bool(result.active_mask[t_idx, robot_idx]),
                    "battery_fraction": float(result.battery_fraction[t_idx, robot_idx]),
                    "x": float(result.robot_positions[t_idx, robot_idx, 0]),
                    "y": float(result.robot_positions[t_idx, robot_idx, 1]),
                    "vx": float(result.robot_velocities[t_idx, robot_idx, 0]),
                    "vy": float(result.robot_velocities[t_idx, robot_idx, 1]),
                    "target_x": float(target[0]),
                    "target_y": float(target[1]),
                    "event_phase": "post_event" if t_s >= problem.event.time_s else "pre_event",
                }
            )
        for load_idx, load in enumerate(problem.world.loads):
            rows.append(
                {
                    "time_s": t_s,
                    "entity": "load",
                    "entity_id": load.identifier,
                    "robot_index": "",
                    "assigned_load_label": load_idx + 1,
                    "active": "",
                    "battery_fraction": "",
                    "x": float(result.load_pose[t_idx, load_idx, 0]),
                    "y": float(result.load_pose[t_idx, load_idx, 1]),
                    "vx": float(result.load_velocity[t_idx, load_idx, 0]),
                    "vy": float(result.load_velocity[t_idx, load_idx, 1]),
                    "target_x": float(problem.target_load_poses[load_idx, 0]),
                    "target_y": float(problem.target_load_poses[load_idx, 1]),
                    "theta_rad": float(result.load_pose[t_idx, load_idx, 2]),
                    "target_theta_rad": float(problem.target_load_poses[load_idx, 2]),
                    "wrench_margin": float(result.wrench_margins[t_idx, load_idx]),
                    "wrench_residual_norm": float(result.wrench_residuals[t_idx, load_idx]),
                    "support_level": float(result.support_level[t_idx, load_idx]),
                    "paused": bool(result.load_paused_mask[t_idx, load_idx]),
                    "degraded_speed": bool(result.degraded_speed_mask[t_idx, load_idx]),
                    "event_phase": "post_event" if t_s >= problem.event.time_s else "pre_event",
                }
            )
    return rows


def robot_path_lengths(result: SP6TrajectoryResult) -> np.ndarray:
    deltas = np.diff(result.robot_positions, axis=0)
    return np.sum(np.linalg.norm(deltas, axis=2), axis=0)


def path_efficiency_ratio(problem: SP6Problem, result: SP6TrajectoryResult, path_lengths: np.ndarray) -> float:
    del problem
    direct = float(np.sum(np.linalg.norm(result.robot_positions[-1] - result.robot_positions[0], axis=1)))
    return float(np.clip(direct / max(float(np.sum(path_lengths)), direct, 1e-9), 0.0, 1.0))


def recovery_time_s(problem: SP6Problem, result: SP6TrajectoryResult, feasible_after_event: np.ndarray) -> float:
    times = []
    for load_idx, feasible in enumerate(feasible_after_event):
        if not bool(feasible):
            continue
        t_s = float(result.completion_times_s[load_idx])
        if np.isfinite(t_s):
            times.append(t_s)
    if len(times) == int(np.sum(feasible_after_event)):
        return float(max(times)) if times else 0.0
    return float(problem.horizon_s)


def replacement_arrival_time_s(problem: SP6Problem, result: SP6TrajectoryResult, feasible_after_event: np.ndarray) -> float:
    event_indices = np.flatnonzero(result.time_s >= problem.event.time_s)
    feasible_loads = np.flatnonzero(feasible_after_event)
    if event_indices.size == 0 or feasible_loads.size == 0:
        return 0.0
    for frame_idx in event_indices:
        if bool(np.all(result.wrench_margins[frame_idx, feasible_loads] >= -0.03)):
            return float(max(0.0, result.time_s[frame_idx] - problem.event.time_s))
    return float(problem.horizon_s - problem.event.time_s)


def infeasible_load_detection_rate(problem: SP6Problem, result: SP6TrajectoryResult) -> float:
    infeasible = np.flatnonzero(~np.asarray(result.feasible_after_event, dtype=bool))
    if infeasible.size == 0:
        return 1.0
    labels = np.asarray(result.labels[-1], dtype=int)
    detected = 0
    for load_idx in infeasible:
        if not np.any(labels == int(load_idx) + 1):
            detected += 1
    return float(detected / max(infeasible.size, 1))


def load_physical_feasible(problem: SP6Problem, result: SP6TrajectoryResult, load_idx: int) -> bool:
    if bool(result.feasible_after_event[load_idx]) and bool(result.completed_loads[-1, load_idx]):
        return True
    if bool(result.wrench_margins[-1, load_idx] >= -0.03):
        return True
    labels = np.asarray(result.labels[-1], dtype=int)
    active = np.asarray(result.active_mask[-1], dtype=bool)
    battery = np.asarray(result.battery_fraction[-1], dtype=float)
    members = np.flatnonzero((labels == load_idx + 1) & active)
    if len(members) < int(problem.world.loads[load_idx].min_coalition_size):
        return False
    load = problem.world.loads[load_idx]
    demand = problem.load_demand_at(load_idx, problem.event.time_s, observed=False)
    capacity = sum(_effective_payload(problem, battery, int(idx)) for idx in members)
    force = sum(problem.world.robots[int(idx)].spec.capacity.force_limit_n for idx in members)
    torque = sum(problem.world.robots[int(idx)].spec.capacity.torque_limit_nm for idx in members)
    return bool(
        capacity >= demand
        and force >= float(np.linalg.norm(load.wrench.force_xy))
        and torque >= abs(float(load.wrench.torque_z))
    )


def _target_for_robot(problem: SP6Problem, labels: np.ndarray, robot_idx: int, load_pose: np.ndarray | None = None) -> np.ndarray:
    label = int(labels[robot_idx])
    load = problem.world.loads[label - 1]
    members = np.flatnonzero(labels == label)
    rank_matches = np.flatnonzero(members == robot_idx)
    rank = int(rank_matches[0]) if rank_matches.size else 0
    slots = problem.load_slots[label - 1]
    if slots:
        pose = problem.target_load_poses[label - 1] if load_pose is None else load_pose[label - 1]
        return pose[:2] + _rotation(float(pose[2])) @ slots[rank % len(slots)].offset_xy
    count = max(int(len(members)), int(load.min_coalition_size), 1)
    angle = 2.0 * np.pi * rank / count
    radius = max(0.55 * max(float(load.length_m), float(load.width_m)), 2.0 * problem.robot_radius_m + 2.0 * problem.safety_margin_m)
    center = problem.target_load_poses[label - 1, :2] if load_pose is None else load_pose[label - 1, :2]
    return center + radius * np.array([np.cos(angle), np.sin(angle)], dtype=float)


def clearance_diagnostics(problem: SP6Problem, result: SP6TrajectoryResult) -> dict[str, float | int]:
    """Compute robot, obstacle and solid payload clearance diagnostics."""

    robot_clearances: list[float] = []
    obstacle_clearances: list[float] = []
    load_clearances: list[float] = []
    collision_count = 0
    safety_count = 0
    safe_robot = 2.0 * problem.robot_radius_m
    for frame_idx, frame in enumerate(result.robot_positions):
        t_s = float(result.time_s[frame_idx])
        for i in range(frame.shape[0]):
            for j in range(i + 1, frame.shape[0]):
                clearance = float(np.linalg.norm(frame[i] - frame[j]) - safe_robot)
                robot_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
        for pos in frame:
            for obstacle in problem.active_obstacles_at(t_s):
                clearance = float(np.linalg.norm(pos - obstacle.center) - obstacle.radius - problem.robot_radius_m)
                obstacle_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
        for load_idx, load in enumerate(problem.world.loads):
            for obstacle in problem.active_obstacles_at(t_s):
                clearance = _payload_rectangle_circle_clearance(result.load_pose[frame_idx, load_idx], float(load.length_m), float(load.width_m), obstacle.center, float(obstacle.radius))
                load_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
        for i, load_i in enumerate(problem.world.loads):
            for j in range(i + 1, len(problem.world.loads)):
                load_j = problem.world.loads[j]
                clearance = _payload_rectangle_rectangle_clearance(
                    result.load_pose[frame_idx, i],
                    float(load_i.length_m),
                    float(load_i.width_m),
                    result.load_pose[frame_idx, j],
                    float(load_j.length_m),
                    float(load_j.width_m),
                )
                load_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
    return {
        "collision_count": int(collision_count),
        "safety_violation_count": int(safety_count),
        "min_robot_clearance_m": _min_or_inf(robot_clearances),
        "min_obstacle_clearance_m": _min_or_inf(obstacle_clearances),
        "min_load_clearance_m": _min_or_inf(load_clearances),
    }


def energy_proxy_wh(problem: SP6Problem, result: SP6TrajectoryResult, path_lengths: np.ndarray) -> float:
    per_meter = np.asarray([robot.spec.battery.discharge_per_meter * robot.spec.battery.capacity_wh for robot in problem.world.robots], dtype=float)
    speeds = np.linalg.norm(result.robot_velocities, axis=2)
    travel_energy = float(np.sum(path_lengths * per_meter))
    speed_penalty = 0.035 * float(np.sum(speeds**2)) * problem.dt_s
    recovery_switching_penalty = 0.015 * float(result.reassignment_count)
    return travel_energy + speed_penalty + recovery_switching_penalty


def recovery_score(
    *,
    recovery_success: bool,
    task_completion_rate: float,
    lost_load_rate: float,
    infeasible_load_detection_rate: float,
    post_event_wrench_feasible_rate: float,
    collision_rate: float,
    safety_violation_count: int,
    recovery_time_s: float,
    travel_distance_m: float,
    energy_proxy_wh: float,
    communication_messages: int,
    reassignment_count: int,
) -> float:
    return float(
        200.0 * float(recovery_success)
        + 120.0 * task_completion_rate
        + 45.0 * infeasible_load_detection_rate
        + 45.0 * post_event_wrench_feasible_rate
        - 95.0 * lost_load_rate
        - 900.0 * collision_rate
        - 0.018 * safety_violation_count
        - 0.75 * recovery_time_s
        - 0.15 * travel_distance_m
        - 0.012 * energy_proxy_wh
        - 0.0008 * communication_messages
        - 0.35 * reassignment_count
    )


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp6_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": meta["trainable_parameters"],
        "method_tuned_parameters": meta["tuned_parameters"],
        "method_uses_neural_policy": meta["uses_neural_policy"],
        "method_uses_decoder": meta["uses_decoder"],
    }


def _collision_opportunities(problem: SP6Problem, result: SP6TrajectoryResult) -> int:
    n = len(problem.world.robots)
    m = len(problem.world.loads)
    total = 0
    for t_s in result.time_s:
        total += n * max(n - 1, 0) // 2
        total += n * len(problem.active_obstacles_at(float(t_s)))
        total += len(problem.world.loads) * len(problem.active_obstacles_at(float(t_s)))
        total += m * max(m - 1, 0) // 2
    return int(max(total, 1))


def _effective_payload(problem: SP6Problem, battery: np.ndarray, robot_idx: int) -> float:
    robot = problem.world.robots[robot_idx]
    if battery[robot_idx] <= robot.spec.battery.reserve_fraction:
        return 0.0
    scale = np.clip((battery[robot_idx] - robot.spec.battery.reserve_fraction) / max(1.0 - robot.spec.battery.reserve_fraction, 1e-9), 0.0, 1.0)
    return float(robot.spec.capacity.payload_kg * scale)


def _min_or_inf(values: list[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    return float(np.min(finite)) if finite.size else float("inf")


def _payload_rectangle_circle_clearance(q: np.ndarray, length_m: float, width_m: float, center: np.ndarray, radius_m: float) -> float:
    theta = float(q[2])
    c = np.cos(theta)
    s = np.sin(theta)
    rotation_t = np.array([[c, s], [-s, c]], dtype=float)
    local = rotation_t @ (np.asarray(center, dtype=float) - np.asarray(q[:2], dtype=float))
    half_extents = np.array([0.5 * float(length_m), 0.5 * float(width_m)], dtype=float)
    outside = np.maximum(np.abs(local) - half_extents, 0.0)
    return float(np.linalg.norm(outside) - float(radius_m))


def _payload_rectangle_rectangle_clearance(
    q_a: np.ndarray,
    length_a_m: float,
    width_a_m: float,
    q_b: np.ndarray,
    length_b_m: float,
    width_b_m: float,
) -> float:
    vec = np.asarray(q_a[:2], dtype=float) - np.asarray(q_b[:2], dtype=float)
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        normal = np.array([1.0, 0.0], dtype=float)
        dist = 0.0
    else:
        normal = vec / dist
    support_a = _payload_support_radius(q_a, length_a_m, width_a_m, normal)
    support_b = _payload_support_radius(q_b, length_b_m, width_b_m, -normal)
    return float(dist - support_a - support_b)


def _payload_support_radius(q: np.ndarray, length_m: float, width_m: float, normal: np.ndarray) -> float:
    rotation = _rotation(float(q[2]))
    return float(
        0.5 * float(length_m) * abs(float(np.dot(normal, rotation[:, 0])))
        + 0.5 * float(width_m) * abs(float(np.dot(normal, rotation[:, 1])))
    )


def _rotation(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + np.pi) % (2.0 * np.pi) - np.pi
