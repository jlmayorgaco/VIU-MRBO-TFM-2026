"""Metrics for SP5 cooperative payload transport experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp5.methods import SP5TrajectoryResult, assignment_member_count, communication_messages, sp5_method_metadata
from viu_mrob_tfm.sp5.scenario import SP5Problem


@dataclass(frozen=True, slots=True)
class SP5Metrics:
    selected_task_load: bool
    pickup_success: bool
    target_reached: bool
    transport_success: bool
    final_position_error_m: float
    final_orientation_error_rad: float
    final_orientation_error_deg: float
    mean_position_error_m: float
    formation_integrity_rate: float
    formation_broken_rate: float
    max_formation_error_m: float
    mean_formation_error_m: float
    mean_wrench_residual_norm: float
    max_wrench_residual_norm: float
    collision_count: int
    collision_rate: float
    safety_violation_count: int
    min_robot_clearance_m: float
    min_obstacle_clearance_m: float
    min_mobile_group_clearance_m: float
    min_load_clearance_m: float
    travel_distance_m: float
    load_travel_distance_m: float
    path_efficiency_ratio: float
    energy_proxy_wh: float
    mean_speed_mps: float
    max_speed_mps: float
    max_speed_violation_mps: float
    pickup_complete_time_s: float
    completion_time_s: float
    assigned_robots: int
    idle_robots: int
    communication_messages: int
    runtime_ms: float
    score_value: float
    reference_score_value: float
    signed_score_delta_vs_reference: float
    performance_gap_vs_reference: float
    optimality_gap_vs_reference: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_transport(
    problem: SP5Problem,
    result: SP5TrajectoryResult,
    *,
    reference_result: SP5TrajectoryResult | None = None,
    centralized: bool = False,
) -> SP5Metrics:
    """Evaluate one SP5 rollout against the requested payload task."""

    target = problem.task.target_pose
    position_errors = np.linalg.norm(target[:2] - result.load_pose[:, :2], axis=1)
    final_position_error = float(position_errors[-1])
    theta_errors = np.asarray([abs(_wrap_angle(float(target[2] - theta))) for theta in result.load_pose[:, 2]], dtype=float)
    final_theta_error = float(theta_errors[-1])
    target_reached = bool(result.selected_task_load and final_position_error <= problem.pose_tolerance_m and final_theta_error <= problem.orientation_tolerance_rad)
    transport_frames = result.phase.astype(int) == 1
    if np.any(transport_frames):
        formation_values = result.formation_errors[transport_frames]
    else:
        formation_values = result.formation_errors
    formation_integrity_rate = float(np.mean(formation_values <= problem.formation_tolerance_m)) if formation_values.size else 0.0
    formation_broken_rate = 1.0 - formation_integrity_rate
    pickup_success = bool(np.isfinite(result.pickup_complete_time_s) and result.pickup_complete_time_s <= problem.pickup_horizon_s + problem.dt_s)
    clearance = clearance_diagnostics(problem, result)
    path_lengths = robot_path_lengths(result)
    load_path = load_path_length(result)
    direct = float(np.linalg.norm(problem.task.target_pose[:2] - problem.task.initial_pose[:2]))
    path_efficiency = float(direct / max(load_path, direct, 1e-9))
    speeds = np.linalg.norm(result.robot_velocities, axis=2)
    limits = np.asarray([robot.spec.max_speed for robot in problem.world.robots], dtype=float)
    max_violation = float(np.max(np.maximum(speeds - limits[None, :], 0.0))) if speeds.size else 0.0
    assigned = assignment_member_count(result)
    messages = communication_messages(problem, result, centralized=centralized)
    energy = energy_proxy_wh(problem, result, path_lengths)
    collision_rate = float(clearance["collision_count"] / max(_collision_opportunities(problem, result), 1))
    completion_time = completion_time_s(problem, result)
    success = bool(target_reached and pickup_success and formation_integrity_rate >= 0.75 and collision_rate <= 0.03)
    score = transport_score(
        transport_success=success,
        target_reached=target_reached,
        pickup_success=pickup_success,
        selected_task_load=result.selected_task_load,
        collision_rate=collision_rate,
        formation_broken_rate=formation_broken_rate,
        final_position_error_m=final_position_error,
        final_orientation_error_rad=final_theta_error,
        travel_distance_m=float(np.sum(path_lengths)),
        energy_proxy_wh=energy,
        completion_time_s=completion_time,
    )
    reference_score = score
    if reference_result is not None:
        reference_score = evaluate_transport(problem, reference_result, centralized=True).score_value
    signed_delta = float(score - reference_score)
    score_scale = max(abs(reference_score), 220.0, 1.0)
    gap = float(np.clip((reference_score - score) / score_scale, 0.0, 1.0))
    return SP5Metrics(
        selected_task_load=bool(result.selected_task_load),
        pickup_success=pickup_success,
        target_reached=target_reached,
        transport_success=success,
        final_position_error_m=final_position_error,
        final_orientation_error_rad=final_theta_error,
        final_orientation_error_deg=float(np.degrees(final_theta_error)),
        mean_position_error_m=float(np.mean(position_errors)),
        formation_integrity_rate=formation_integrity_rate,
        formation_broken_rate=formation_broken_rate,
        max_formation_error_m=float(np.max(result.formation_errors)) if result.formation_errors.size else 0.0,
        mean_formation_error_m=float(np.mean(result.formation_errors)) if result.formation_errors.size else 0.0,
        mean_wrench_residual_norm=float(np.mean(result.wrench_residuals)) if result.wrench_residuals.size else 0.0,
        max_wrench_residual_norm=float(np.max(result.wrench_residuals)) if result.wrench_residuals.size else 0.0,
        collision_count=int(clearance["collision_count"]),
        collision_rate=collision_rate,
        safety_violation_count=int(clearance["safety_violation_count"]),
        min_robot_clearance_m=float(clearance["min_robot_clearance_m"]),
        min_obstacle_clearance_m=float(clearance["min_obstacle_clearance_m"]),
        min_mobile_group_clearance_m=float(clearance["min_mobile_group_clearance_m"]),
        min_load_clearance_m=float(clearance["min_load_clearance_m"]),
        travel_distance_m=float(np.sum(path_lengths)),
        load_travel_distance_m=load_path,
        path_efficiency_ratio=float(np.clip(path_efficiency, 0.0, 1.0)),
        energy_proxy_wh=energy,
        mean_speed_mps=float(np.mean(speeds)) if speeds.size else 0.0,
        max_speed_mps=float(np.max(speeds)) if speeds.size else 0.0,
        max_speed_violation_mps=max_violation,
        pickup_complete_time_s=float(result.pickup_complete_time_s) if np.isfinite(result.pickup_complete_time_s) else float(problem.horizon_s),
        completion_time_s=completion_time,
        assigned_robots=int(assigned),
        idle_robots=int(len(problem.world.robots) - assigned),
        communication_messages=messages,
        runtime_ms=float(result.runtime_ms),
        score_value=score,
        reference_score_value=reference_score,
        signed_score_delta_vs_reference=signed_delta,
        performance_gap_vs_reference=gap,
        optimality_gap_vs_reference=gap,
    )


def robot_status_rows(problem: SP5Problem, result: SP5TrajectoryResult) -> list[dict[str, Any]]:
    """Return one diagnostic row per robot."""

    path_lengths = robot_path_lengths(result)
    rows = []
    labels = np.asarray(result.assignment.labels, dtype=int)
    slots = np.asarray(result.assignment.slot_labels, dtype=int)
    for idx, robot in enumerate(problem.world.robots):
        assigned = bool(labels[idx] == result.selected_load_index + 1)
        rows.append(
            {
                "robot_id": robot.identifier,
                "robot_index": idx + 1,
                "assigned_to_selected_load": assigned,
                "assigned_load_label": int(labels[idx]),
                "assigned_slot_label": int(slots[idx]),
                "start_x": float(result.robot_positions[0, idx, 0]),
                "start_y": float(result.robot_positions[0, idx, 1]),
                "final_x": float(result.robot_positions[-1, idx, 0]),
                "final_y": float(result.robot_positions[-1, idx, 1]),
                "path_length_m": float(path_lengths[idx]),
                "battery_fraction": float(robot.battery_fraction),
                "max_speed_mps": float(robot.spec.max_speed),
                "force_limit_n": float(robot.spec.capacity.force_limit_n),
                "payload_kg": float(robot.spec.capacity.payload_kg),
            }
        )
    return rows


def trajectory_sample_rows(problem: SP5Problem, result: SP5TrajectoryResult, *, max_frames: int = 80) -> list[dict[str, Any]]:
    """Return compact long-form trajectory samples for debugging and videos."""

    total = len(result.time_s)
    stride = max(1, int(np.ceil(total / max(max_frames, 1))))
    rows: list[dict[str, Any]] = []
    for t_idx in range(0, total, stride):
        rows.append(
            {
                "time_s": float(result.time_s[t_idx]),
                "entity": "payload",
                "entity_id": result.selected_load_id,
                "x": float(result.load_pose[t_idx, 0]),
                "y": float(result.load_pose[t_idx, 1]),
                "theta_rad": float(result.load_pose[t_idx, 2]),
                "phase": int(result.phase[t_idx]),
                "formation_error_m": float(result.formation_errors[t_idx]),
                "wrench_residual_norm": float(result.wrench_residuals[t_idx]),
            }
        )
        for robot_idx, robot in enumerate(problem.world.robots):
            rows.append(
                {
                    "time_s": float(result.time_s[t_idx]),
                    "entity": "robot",
                    "entity_id": robot.identifier,
                    "x": float(result.robot_positions[t_idx, robot_idx, 0]),
                    "y": float(result.robot_positions[t_idx, robot_idx, 1]),
                    "theta_rad": "",
                    "phase": int(result.phase[t_idx]),
                    "formation_error_m": float(result.formation_errors[t_idx]),
                    "wrench_residual_norm": float(result.wrench_residuals[t_idx]),
                }
            )
    return rows


def robot_path_lengths(result: SP5TrajectoryResult) -> np.ndarray:
    deltas = np.diff(result.robot_positions, axis=0)
    return np.sum(np.linalg.norm(deltas, axis=2), axis=0)


def load_path_length(result: SP5TrajectoryResult) -> float:
    deltas = np.diff(result.load_pose[:, :2], axis=0)
    return float(np.sum(np.linalg.norm(deltas, axis=1)))


def completion_time_s(problem: SP5Problem, result: SP5TrajectoryResult) -> float:
    target = problem.task.target_pose
    pos = np.linalg.norm(target[:2] - result.load_pose[:, :2], axis=1)
    theta = np.asarray([abs(_wrap_angle(float(target[2] - value))) for value in result.load_pose[:, 2]], dtype=float)
    mask = (pos <= problem.pose_tolerance_m) & (theta <= problem.orientation_tolerance_rad) & (result.phase.astype(int) == 1)
    if result.selected_task_load and np.any(mask):
        return float(result.time_s[int(np.flatnonzero(mask)[0])])
    return float(problem.horizon_s)


def clearance_diagnostics(problem: SP5Problem, result: SP5TrajectoryResult) -> dict[str, float | int]:
    """Compute robot, obstacle, traffic and solid payload clearances."""

    robot_clearances: list[float] = []
    obstacle_clearances: list[float] = []
    mobile_clearances: list[float] = []
    load_clearances: list[float] = []
    collision_count = 0
    safety_count = 0
    load = problem.world.loads[result.selected_load_index]
    safe_robot = 2.0 * problem.robot_radius_m
    for frame_idx, frame in enumerate(result.robot_positions):
        t_s = float(result.time_s[frame_idx])
        load_q = result.load_pose[frame_idx]
        for i in range(frame.shape[0]):
            for j in range(i + 1, frame.shape[0]):
                clearance = float(np.linalg.norm(frame[i] - frame[j]) - safe_robot)
                robot_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
        for pos in frame:
            for obstacle in problem.world.map.obstacles:
                clearance = float(np.linalg.norm(pos - obstacle.center) - obstacle.radius - problem.robot_radius_m)
                obstacle_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
            for group in problem.mobile_groups:
                clearance = float(np.linalg.norm(pos - group.center_at(t_s, problem.horizon_s)) - group.radius_m - problem.robot_radius_m)
                mobile_clearances.append(clearance)
                if clearance < 0.0:
                    collision_count += 1
                if clearance < problem.safety_margin_m:
                    safety_count += 1
        for obstacle in problem.world.map.obstacles:
            clearance = _payload_rectangle_circle_clearance(load_q, float(load.length_m), float(load.width_m), obstacle.center, float(obstacle.radius))
            load_clearances.append(clearance)
            if clearance < 0.0:
                collision_count += 1
            if clearance < problem.safety_margin_m:
                safety_count += 1
        for group in problem.mobile_groups:
            clearance = _payload_rectangle_circle_clearance(load_q, float(load.length_m), float(load.width_m), group.center_at(t_s, problem.horizon_s), float(group.radius_m))
            load_clearances.append(clearance)
            mobile_clearances.append(clearance)
            if clearance < 0.0:
                collision_count += 1
            if clearance < problem.safety_margin_m:
                safety_count += 1
        for other_idx, other_load in enumerate(problem.world.loads):
            if other_idx == result.selected_load_index:
                continue
            clearance = _payload_rectangle_rectangle_clearance(
                load_q,
                float(load.length_m),
                float(load.width_m),
                _static_load_pose(problem, other_idx),
                float(other_load.length_m),
                float(other_load.width_m),
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
        "min_mobile_group_clearance_m": _min_or_inf(mobile_clearances),
        "min_load_clearance_m": _min_or_inf(load_clearances),
    }


def _collision_opportunities(problem: SP5Problem, result: SP5TrajectoryResult) -> int:
    n = len(problem.world.robots)
    pair_checks = n * max(n - 1, 0) // 2
    robot_static = n * len(problem.world.map.obstacles)
    robot_mobile = n * len(problem.mobile_groups)
    load_static = len(problem.world.map.obstacles)
    load_mobile = len(problem.mobile_groups)
    load_load = max(len(problem.world.loads) - 1, 0)
    per_frame = pair_checks + robot_static + robot_mobile + load_static + load_mobile + load_load
    return int(max(len(result.time_s), 1) * max(per_frame, 1))


def _payload_rectangle_circle_clearance(q: np.ndarray, length_m: float, width_m: float, center: np.ndarray, radius_m: float) -> float:
    """Signed clearance between an oriented rectangular payload and a circular obstacle."""

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


def _static_load_pose(problem: SP5Problem, load_idx: int) -> np.ndarray:
    load = problem.world.loads[load_idx]
    if load_idx == problem.task.load_index:
        return problem.task.initial_pose.copy()
    return np.array([float(load.pickup[0]), float(load.pickup[1]), 0.0], dtype=float)


def energy_proxy_wh(problem: SP5Problem, result: SP5TrajectoryResult, path_lengths: np.ndarray) -> float:
    per_meter = np.asarray([robot.spec.battery.discharge_per_meter * robot.spec.battery.capacity_wh for robot in problem.world.robots], dtype=float)
    robot_energy = float(np.sum(path_lengths * per_meter))
    speeds = np.linalg.norm(result.robot_velocities, axis=2)
    speed_penalty = 0.035 * float(np.sum(speeds**2)) * problem.dt_s
    load_work = 0.12 * load_path_length(result) * float(problem.world.loads[result.selected_load_index].mass_kg)
    return robot_energy + speed_penalty + load_work


def transport_score(
    *,
    transport_success: bool,
    target_reached: bool,
    pickup_success: bool,
    selected_task_load: bool,
    collision_rate: float,
    formation_broken_rate: float,
    final_position_error_m: float,
    final_orientation_error_rad: float,
    travel_distance_m: float,
    energy_proxy_wh: float,
    completion_time_s: float,
) -> float:
    return float(
        210.0 * float(transport_success)
        + 80.0 * float(target_reached)
        + 35.0 * float(pickup_success)
        + 35.0 * float(selected_task_load)
        - 700.0 * collision_rate
        - 95.0 * formation_broken_rate
        - 9.0 * final_position_error_m
        - 18.0 * final_orientation_error_rad
        - 0.18 * travel_distance_m
        - 0.012 * energy_proxy_wh
        - 0.75 * completion_time_s
    )


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp5_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": meta["trainable_parameters"],
        "method_tuned_parameters": meta["tuned_parameters"],
        "method_uses_neural_policy": meta["uses_neural_policy"],
        "method_uses_decoder": meta["uses_decoder"],
        "method_allocator": meta["allocator"],
    }


def _min_or_inf(values: list[float]) -> float:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    return float(np.min(finite)) if finite.size else float("inf")


def _rotation(theta: float) -> np.ndarray:
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + np.pi) % (2.0 * np.pi) - np.pi
