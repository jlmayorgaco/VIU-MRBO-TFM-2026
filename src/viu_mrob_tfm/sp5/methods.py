"""Methods and dynamics for SP5 cooperative payload transport."""

from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace
from time import perf_counter
from typing import Any

import numpy as np
from scipy.optimize import lsq_linear

from viu_mrob_tfm.control.explicit_law import ExplicitControlGains, required_wrench_pd
from viu_mrob_tfm.sp3.methods import SP3Assignment, make_sp3_allocator
from viu_mrob_tfm.sp5.scenario import SP5Problem


SP5_METHOD_LABELS = {
    "classic_centralized_shortest_push": "Classic centralized shortest push",
    "classic_decentralized_apf_push": "Classic decentralized APF push",
    "sota_centralized_cbf_push": "SOTA centralized CBF push",
    "sota_decentralized_vo_push": "SOTA decentralized VO push",
    "sota_centralized_cbf_cargo": "SOTA centralized CBF cargo",
    "sota_decentralized_vo_cargo": "SOTA decentralized VO cargo",
    "ours_primal_dual_wrench_push": "Ours primal-dual wrench push",
    "ours_tensor_game_push": "Ours tensor-game push",
    "ours_explicit_vgne_cbf_push": "Ours explicit vGNE-CBF push",
    "ours_explicit_vgne_cbf_cargo": "Ours explicit vGNE-CBF cargo",
    "ours_hamiltonian_cargo": "Ours Hamiltonian cargo",
    "reference_centralized_mpc_cbf_cargo": "Reference centralized MPC-CBF cargo",
}


METHOD_META = {
    "classic_centralized_shortest_push": ("classic", "centralized", "baseline", "shortest_path_push_drag", "push_drag"),
    "classic_decentralized_apf_push": ("classic", "decentralized", "baseline", "apf_push_drag", "push_drag"),
    "sota_centralized_cbf_push": ("sota", "centralized", "baseline", "cbf_payload_push_drag", "push_drag"),
    "sota_decentralized_vo_push": ("sota", "decentralized", "baseline", "velocity_obstacle_push_drag", "push_drag"),
    "sota_centralized_cbf_cargo": ("sota", "centralized", "baseline", "cbf_overhead_cargo", "cargo"),
    "sota_decentralized_vo_cargo": ("sota", "decentralized", "baseline", "velocity_obstacle_cargo", "cargo"),
    "ours_primal_dual_wrench_push": ("model_based", "decentralized", "proposed", "primal_dual_wrench_formation_push", "push_drag"),
    "ours_tensor_game_push": ("model_based", "decentralized", "proposed", "smooth_tensor_game_wrench_push", "push_drag"),
    "ours_explicit_vgne_cbf_push": ("model_based", "decentralized", "proposed", "closed_form_explicit_vgne_cbf_push", "push_drag"),
    "ours_explicit_vgne_cbf_cargo": ("model_based", "decentralized", "proposed", "closed_form_explicit_vgne_cbf_cargo", "cargo"),
    "ours_hamiltonian_cargo": ("model_based", "decentralized", "proposed", "hamiltonian_tensor_cargo", "cargo"),
    "reference_centralized_mpc_cbf_cargo": ("model_based_reference", "centralized", "reference", "time_expanded_mpc_cbf_cargo", "cargo"),
}


METHOD_RESOURCES = {
    "classic_centralized_shortest_push": ("none", "centralized_slot_assignment_plus_direct_payload_tracking", "global_robot_slot_cost", 0, 2, False, False),
    "classic_decentralized_apf_push": ("none", "distributed_apf_payload_tracking", "local_obstacle_and_slot_state", 0, 3, False, False),
    "sota_centralized_cbf_push": ("none", "centralized_cbf_payload_velocity_projection", "global_payload_robot_traffic_state", 0, 6, False, False),
    "sota_decentralized_vo_push": ("none", "distributed_velocity_obstacle_payload_tracking", "local_relative_traffic_state", 0, 6, False, False),
    "sota_centralized_cbf_cargo": ("none", "centralized_cbf_cargo_transport", "global_payload_robot_traffic_state", 0, 6, False, False),
    "sota_decentralized_vo_cargo": ("none", "distributed_velocity_obstacle_cargo_transport", "local_relative_traffic_state", 0, 6, False, False),
    "ours_primal_dual_wrench_push": ("model_based_tuning_optional", "distributed_primal_dual_wrench_formation_transport", "local_wrench_residual_dual_prices", 0, 8, False, False),
    "ours_tensor_game_push": ("model_based_tuning_optional", "distributed_tensor_game_wrench_transport", "local_tensor_field_and_wrench_residual", 0, 9, False, False),
    "ours_explicit_vgne_cbf_push": ("closed_form_model_based", "distributed_explicit_vgne_cbf_transport", "local_contact_geometry_consensus_scalars_and_wrench_residual", 0, 10, False, False),
    "ours_explicit_vgne_cbf_cargo": ("closed_form_model_based", "distributed_explicit_vgne_cbf_caging_transport", "local_contact_geometry_consensus_scalars_and_wrench_residual", 0, 10, False, False),
    "ours_hamiltonian_cargo": ("model_based_tuning_optional", "distributed_hamiltonian_cargo_transport", "local_energy_wrench_formation_game", 0, 9, False, False),
    "reference_centralized_mpc_cbf_cargo": ("none", "centralized_reference_mpc_cbf_cargo", "global_state_and_time_expanded_constraints", 0, 10, False, False),
}


METHOD_ALLOCATOR = {
    "classic_centralized_shortest_push": "hungarian_slots",
    "classic_decentralized_apf_push": "greedy_capacity",
    "sota_centralized_cbf_push": "wrench_greedy",
    "sota_decentralized_vo_push": "cbba_wrench_score",
    "sota_centralized_cbf_cargo": "wrench_greedy",
    "sota_decentralized_vo_cargo": "cbba_wrench_score",
    "ours_primal_dual_wrench_push": "support_dual_wrench_market_guarded",
    "ours_tensor_game_push": "smith_wrench_pairs_guarded",
    "ours_explicit_vgne_cbf_push": "support_dual_wrench_market_guarded",
    "ours_explicit_vgne_cbf_cargo": "support_dual_wrench_market_guarded",
    "ours_hamiltonian_cargo": "support_dual_wrench_market_guarded",
    "reference_centralized_mpc_cbf_cargo": "wrench_oracle",
}


@dataclass(frozen=True, slots=True)
class SP5PolicyConfig:
    pose_gain: float = 18.0
    pose_damping: float = 14.0
    theta_gain: float = 18.0
    theta_damping: float = 28.0
    load_linear_damping: float = 7.0
    load_angular_damping: float = 18.0
    pickup_gain: float = 1.4
    formation_gain: float = 2.6
    obstacle_gain: float = 0.0
    mobile_gain: float = 0.0
    robot_gain: float = 0.0
    velocity_obstacle_gain: float = 0.0
    cbf_gain: float = 0.0
    tensor_gain: float = 0.0
    energy_shaping_gain: float = 0.0
    force_limit_n: float = 210.0
    torque_limit_nm: float = 130.0
    speed_scale: float = 1.0
    use_global_traffic: bool = False
    explicit_control_law: bool = False
    explicit_pose_bandwidth: float = 1.05
    explicit_theta_bandwidth: float = 1.05
    explicit_accel_fraction: float = 0.80


@dataclass(frozen=True, slots=True)
class SP5TrajectoryResult:
    method: str
    method_label: str
    selected_load_index: int
    selected_load_id: str
    selected_task_load: bool
    transport_mode: str
    assignment: SP3Assignment
    time_s: np.ndarray
    load_pose: np.ndarray
    load_velocity: np.ndarray
    robot_positions: np.ndarray
    robot_velocities: np.ndarray
    formation_errors: np.ndarray
    wrench_residuals: np.ndarray
    phase: np.ndarray
    pickup_complete_time_s: float
    runtime_ms: float


class SP5TransportPolicy:
    """Assignment plus cooperative transport controller."""

    def __init__(self, method_id: str, config: SP5PolicyConfig | None = None, allocator_params: dict[str, Any] | None = None) -> None:
        self.method_id = _canonical_method(method_id)
        self.config = config or _default_config(self.method_id)
        self.allocator_params = dict(allocator_params or {})

    def allocate(self, problem: SP5Problem) -> SP3Assignment:
        allocator = make_sp3_allocator(METHOD_ALLOCATOR[self.method_id], self.allocator_params)
        assignment = allocator.allocate(problem.to_sp3_problem())
        return SP3Assignment(assignment.labels, assignment.slot_labels, method=self.method_id)


def make_sp5_policy(method_id: str, params: dict[str, Any] | None = None) -> SP5TransportPolicy:
    """Create an SP5 policy by stable method id."""

    params = dict(params or {})
    method = _canonical_method(method_id)
    cfg = _default_config(method)
    policy_params = dict(params.get("policy", params))
    if policy_params:
        allowed = {field.name for field in fields(SP5PolicyConfig)}
        cfg = replace(cfg, **{key: value for key, value in policy_params.items() if key in allowed})
    allocator_params = dict(params.get("allocator", {}))
    return SP5TransportPolicy(method, cfg, allocator_params)


def simulate_transport(policy: SP5TransportPolicy, problem: SP5Problem) -> SP5TrajectoryResult:
    """Roll out one SP5 cooperative payload transport policy."""

    start = perf_counter()
    assignment = policy.allocate(problem)
    method = policy.method_id
    selected_load_idx = _selected_load_index(problem, assignment)
    load = problem.world.loads[selected_load_idx]
    selected_task = selected_load_idx == problem.task.load_index
    initial_pose, target_pose = _pose_pair(problem, selected_load_idx)
    transport_mode = _transport_mode_for_method(method)
    steps = int(np.ceil(problem.horizon_s / problem.dt_s))
    pickup_steps = min(steps, int(np.ceil(problem.pickup_horizon_s / problem.dt_s)))
    n = len(problem.world.robots)
    robot_positions = np.zeros((steps + 1, n, 2), dtype=float)
    robot_velocities = np.zeros((steps + 1, n, 2), dtype=float)
    load_pose = np.zeros((steps + 1, 3), dtype=float)
    load_velocity = np.zeros((steps + 1, 3), dtype=float)
    formation_errors = np.zeros(steps + 1, dtype=float)
    wrench_residuals = np.zeros(steps + 1, dtype=float)
    phase = np.zeros(steps + 1, dtype=int)
    robot_positions[0] = _project_robot_clearance(problem, np.vstack([robot.position for robot in problem.world.robots]), 0.0)
    load_pose[0] = _project_load_clearance(problem, selected_load_idx, initial_pose, 0.0)
    qd = np.zeros(3, dtype=float)
    pickup_complete_time = math.nan

    assigned = _assigned_pairs(problem, assignment, selected_load_idx)
    load_speed_limit = _load_speed_limit(problem, assigned, transport_mode)
    mass = max(float(load.mass_kg), 1e-6)
    inertia = max(float(mass * (load.length_m**2 + load.width_m**2) / 12.0), 1e-6)
    mass_matrix = np.diag([mass, mass, inertia])
    damping = np.diag([policy.config.load_linear_damping, policy.config.load_linear_damping, policy.config.load_angular_damping])

    for step in range(steps):
        t_s = step * problem.dt_s
        current_q = load_pose[step].copy()
        current_robots = robot_positions[step].copy()
        slot_positions, slot_directions, slot_offsets = _slot_geometry(problem, selected_load_idx, assignment, current_q)
        formation_error = _formation_error(current_robots, assigned, slot_positions)
        formation_errors[step] = formation_error
        in_pickup = step < pickup_steps and formation_error > problem.formation_tolerance_m
        if in_pickup:
            commanded = _pickup_robot_velocities(problem, policy.config, current_robots, assigned, slot_positions, t_s)
            robot_velocities[step] = commanded
            next_robots = _clip_positions(problem, current_robots + problem.dt_s * commanded)
            robot_positions[step + 1] = _project_robot_clearance(problem, next_robots, t_s + problem.dt_s)
            load_pose[step + 1] = current_q
            load_velocity[step + 1] = qd
            phase[step + 1] = 0
            wrench_residuals[step] = 1.0 if assigned else 0.0
            continue

        if not np.isfinite(pickup_complete_time):
            pickup_complete_time = t_s
        phase[step + 1] = 1
        desired = _desired_wrench(problem, policy.config, assignment, selected_load_idx, current_q, qd, target_pose, t_s)
        achieved, residual = _achieved_wrench(problem, policy.config, assignment, selected_load_idx, current_q, desired, transport_mode, formation_error)
        wrench_residuals[step] = residual
        qdd = np.linalg.solve(mass_matrix, achieved - damping @ qd)
        qd = qd + problem.dt_s * qdd
        qd[:2] = _clip_vector(qd[:2], load_speed_limit)
        qd[2] = float(np.clip(qd[2], -0.95, 0.95))
        next_q = current_q + problem.dt_s * qd
        next_q[2] = _wrap_angle(float(next_q[2]))
        projected_q = _project_load_clearance(problem, selected_load_idx, next_q, t_s + problem.dt_s)
        load_pose[step + 1] = projected_q
        corrected_qd = qd.copy()
        corrected_qd[:2] = (projected_q[:2] - current_q[:2]) / problem.dt_s
        corrected_qd[2] = _wrap_angle(float(projected_q[2] - current_q[2])) / problem.dt_s
        load_velocity[step + 1] = corrected_qd
        qd = corrected_qd
        next_slots, _next_dirs, next_offsets = _slot_geometry(problem, selected_load_idx, assignment, load_pose[step + 1])
        commanded = _transport_robot_velocities(problem, policy.config, current_robots, assigned, next_slots, next_offsets, qd, load_pose[step + 1], t_s, transport_mode)
        robot_velocities[step] = commanded
        next_robots = _clip_positions(problem, current_robots + problem.dt_s * commanded)
        robot_positions[step + 1] = _project_robot_clearance(problem, next_robots, t_s + problem.dt_s)

    final_slots, _final_dirs, _final_offsets = _slot_geometry(problem, selected_load_idx, assignment, load_pose[-1])
    formation_errors[-1] = _formation_error(robot_positions[-1], assigned, final_slots)
    wrench_residuals[-1] = wrench_residuals[-2] if len(wrench_residuals) > 1 else 0.0
    runtime_ms = 1000.0 * (perf_counter() - start)
    return SP5TrajectoryResult(
        method=method,
        method_label=SP5_METHOD_LABELS[method],
        selected_load_index=selected_load_idx,
        selected_load_id=load.identifier,
        selected_task_load=selected_task,
        transport_mode=transport_mode,
        assignment=assignment,
        time_s=np.arange(steps + 1, dtype=float) * problem.dt_s,
        load_pose=load_pose,
        load_velocity=load_velocity,
        robot_positions=robot_positions,
        robot_velocities=robot_velocities,
        formation_errors=formation_errors,
        wrench_residuals=wrench_residuals,
        phase=phase,
        pickup_complete_time_s=float(pickup_complete_time) if np.isfinite(pickup_complete_time) else math.nan,
        runtime_ms=runtime_ms,
    )


def sp5_method_metadata(method_id: str) -> dict[str, Any]:
    method = _canonical_method(method_id)
    family, scope, ownership, variant, transport_mode = METHOD_META[method]
    training_type, execution_model, communication_pattern, trainable, tuned, uses_neural, uses_decoder = METHOD_RESOURCES[method]
    return {
        "label": SP5_METHOD_LABELS[method],
        "title": f"{SP5_METHOD_LABELS[method]} [{ownership} | {family} | {scope} | {transport_mode}]",
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "transport_mode": transport_mode,
        "comparison_group": f"{ownership}_{family}_{scope}_{transport_mode}",
        "training_type": training_type,
        "execution_model": execution_model,
        "communication_pattern": communication_pattern,
        "trainable_parameters": trainable,
        "tuned_parameters": tuned,
        "uses_neural_policy": uses_neural,
        "uses_decoder": uses_decoder,
        "allocator": METHOD_ALLOCATOR[method],
    }


def communication_messages(problem: SP5Problem, result: SP5TrajectoryResult, *, centralized: bool) -> int:
    n = len(problem.world.robots)
    frames = max(len(result.time_s) - 1, 1)
    if centralized or not np.isfinite(problem.communication_radius):
        return int(frames * n * max(n - 1, 0))
    radius = float(problem.communication_radius)
    total = 0
    for frame in result.robot_positions[:-1]:
        distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
        total += int(np.sum((distances <= radius) & (distances > 0.0)))
    return total


def assignment_member_count(result: SP5TrajectoryResult) -> int:
    return int(np.sum(result.assignment.labels == result.selected_load_index + 1))


def _canonical_method(method_id: str) -> str:
    method = method_id.lower()
    aliases = {
        "classic_push": "classic_decentralized_apf_push",
        "centralized_classic": "classic_centralized_shortest_push",
        "apf_push": "classic_decentralized_apf_push",
        "cbf_push": "sota_centralized_cbf_push",
        "vo_push": "sota_decentralized_vo_push",
        "cbf_cargo": "sota_centralized_cbf_cargo",
        "vo_cargo": "sota_decentralized_vo_cargo",
        "primal_dual_push": "ours_primal_dual_wrench_push",
        "tensor_push": "ours_tensor_game_push",
        "explicit_push": "ours_explicit_vgne_cbf_push",
        "explicit_cargo": "ours_explicit_vgne_cbf_cargo",
        "explicit_vgne_cbf": "ours_explicit_vgne_cbf_push",
        "hamiltonian_cargo": "ours_hamiltonian_cargo",
        "reference": "reference_centralized_mpc_cbf_cargo",
    }
    method = aliases.get(method, method)
    if method not in METHOD_META:
        raise ValueError(f"Unknown SP5 method: {method_id}")
    return method


def _default_config(method: str) -> SP5PolicyConfig:
    if method == "classic_centralized_shortest_push":
        return SP5PolicyConfig(pose_gain=15.0, pose_damping=12.0, theta_gain=12.0, theta_damping=22.0, pickup_gain=1.30, formation_gain=2.25, speed_scale=0.92)
    if method == "classic_decentralized_apf_push":
        return SP5PolicyConfig(pose_gain=15.5, pose_damping=12.0, theta_gain=13.0, theta_damping=23.0, pickup_gain=1.25, formation_gain=2.15, obstacle_gain=0.55, mobile_gain=0.35, robot_gain=0.18, speed_scale=0.88)
    if method == "sota_centralized_cbf_push":
        return SP5PolicyConfig(pose_gain=17.0, pose_damping=13.5, theta_gain=15.5, theta_damping=26.0, pickup_gain=1.35, formation_gain=2.65, obstacle_gain=0.45, mobile_gain=0.58, robot_gain=0.20, cbf_gain=0.75, speed_scale=0.92, use_global_traffic=True)
    if method == "sota_decentralized_vo_push":
        return SP5PolicyConfig(pose_gain=16.0, pose_damping=13.0, theta_gain=15.0, theta_damping=25.0, pickup_gain=1.28, formation_gain=2.45, obstacle_gain=0.40, mobile_gain=0.46, robot_gain=0.22, velocity_obstacle_gain=0.42, speed_scale=0.88)
    if method == "sota_centralized_cbf_cargo":
        return SP5PolicyConfig(pose_gain=18.0, pose_damping=14.5, theta_gain=17.0, theta_damping=28.0, pickup_gain=1.45, formation_gain=3.20, obstacle_gain=0.42, mobile_gain=0.58, robot_gain=0.16, cbf_gain=0.78, speed_scale=0.94, use_global_traffic=True)
    if method == "sota_decentralized_vo_cargo":
        return SP5PolicyConfig(pose_gain=17.0, pose_damping=14.0, theta_gain=16.0, theta_damping=27.0, pickup_gain=1.40, formation_gain=3.00, obstacle_gain=0.38, mobile_gain=0.48, robot_gain=0.18, velocity_obstacle_gain=0.36, speed_scale=0.90)
    if method == "ours_primal_dual_wrench_push":
        return SP5PolicyConfig(pose_gain=18.5, pose_damping=15.0, theta_gain=18.0, theta_damping=30.0, pickup_gain=1.42, formation_gain=3.05, obstacle_gain=0.50, mobile_gain=0.64, robot_gain=0.22, cbf_gain=0.66, energy_shaping_gain=0.18, speed_scale=0.92)
    if method == "ours_tensor_game_push":
        return SP5PolicyConfig(pose_gain=19.2, pose_damping=15.0, theta_gain=19.0, theta_damping=31.0, pickup_gain=1.45, formation_gain=3.25, obstacle_gain=0.54, mobile_gain=0.70, robot_gain=0.24, cbf_gain=0.70, tensor_gain=0.40, energy_shaping_gain=0.20, speed_scale=0.92)
    if method == "ours_explicit_vgne_cbf_push":
        return SP5PolicyConfig(pose_gain=18.0, pose_damping=14.0, theta_gain=18.0, theta_damping=28.0, pickup_gain=1.48, formation_gain=3.35, obstacle_gain=0.52, mobile_gain=0.72, robot_gain=0.24, cbf_gain=0.74, tensor_gain=0.30, energy_shaping_gain=0.18, speed_scale=0.92, explicit_control_law=True, explicit_pose_bandwidth=1.18, explicit_theta_bandwidth=1.10, explicit_accel_fraction=0.80)
    if method == "ours_explicit_vgne_cbf_cargo":
        return SP5PolicyConfig(pose_gain=20.0, pose_damping=16.0, theta_gain=20.0, theta_damping=32.0, pickup_gain=1.58, formation_gain=3.75, obstacle_gain=0.50, mobile_gain=0.72, robot_gain=0.18, cbf_gain=0.78, tensor_gain=0.34, energy_shaping_gain=0.24, speed_scale=0.94, explicit_control_law=True, explicit_pose_bandwidth=1.28, explicit_theta_bandwidth=1.18, explicit_accel_fraction=0.86)
    if method == "ours_hamiltonian_cargo":
        return SP5PolicyConfig(pose_gain=20.0, pose_damping=16.5, theta_gain=20.0, theta_damping=34.0, pickup_gain=1.55, formation_gain=3.65, obstacle_gain=0.48, mobile_gain=0.68, robot_gain=0.18, cbf_gain=0.72, tensor_gain=0.34, energy_shaping_gain=0.28, speed_scale=0.94)
    if method == "reference_centralized_mpc_cbf_cargo":
        return SP5PolicyConfig(pose_gain=21.0, pose_damping=17.0, theta_gain=21.0, theta_damping=36.0, pickup_gain=1.65, formation_gain=3.90, obstacle_gain=0.52, mobile_gain=0.78, robot_gain=0.18, cbf_gain=0.92, tensor_gain=0.30, energy_shaping_gain=0.22, speed_scale=0.96, use_global_traffic=True)
    raise ValueError(f"Unknown SP5 method: {method}")


def _transport_mode_for_method(method: str) -> str:
    return str(METHOD_META[method][4])


def _selected_load_index(problem: SP5Problem, assignment: SP3Assignment) -> int:
    labels = np.asarray(assignment.labels, dtype=int)
    candidates = []
    for load_idx, load in enumerate(problem.world.loads):
        members = int(np.sum(labels == load_idx + 1))
        if members <= 0:
            continue
        candidates.append((float(load.reward), members, -abs(load_idx - problem.task.load_index), load_idx))
    if not candidates:
        return int(problem.task.load_index)
    candidates.sort(reverse=True)
    return int(candidates[0][3])


def _pose_pair(problem: SP5Problem, load_idx: int) -> tuple[np.ndarray, np.ndarray]:
    if load_idx == problem.task.load_index:
        return problem.task.initial_pose.copy(), problem.task.target_pose.copy()
    load = problem.world.loads[load_idx]
    return np.array([load.pickup[0], load.pickup[1], 0.0], dtype=float), np.array([load.destination[0], load.destination[1], 0.0], dtype=float)


def _assigned_pairs(problem: SP5Problem, assignment: SP3Assignment, load_idx: int) -> list[tuple[int, int]]:
    pairs = []
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if int(label) != load_idx + 1:
            continue
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if 0 <= slot_idx < len(problem.load_slots[load_idx]):
            pairs.append((int(robot_idx), slot_idx))
    return pairs


def _load_speed_limit(problem: SP5Problem, pairs: list[tuple[int, int]], transport_mode: str) -> float:
    if not pairs:
        return 0.35
    speeds = [float(problem.world.robots[robot_idx].spec.max_speed) for robot_idx, _slot_idx in pairs]
    factor = 0.82 if transport_mode == "cargo" else 0.74
    return float(np.clip(factor * min(speeds), 0.38, 0.72))


def _slot_geometry(problem: SP5Problem, load_idx: int, assignment: SP3Assignment, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rotation = _rotation(float(q[2]))
    positions = []
    directions = []
    offsets = []
    for _robot_idx, slot_idx in _assigned_pairs(problem, assignment, load_idx):
        slot = problem.load_slots[load_idx][slot_idx]
        offset = rotation @ slot.offset_xy
        positions.append(q[:2] + offset)
        directions.append(rotation @ slot.direction_xy)
        offsets.append(offset)
    if not positions:
        return np.zeros((0, 2), dtype=float), np.zeros((0, 2), dtype=float), np.zeros((0, 2), dtype=float)
    return np.vstack(positions), np.vstack(directions), np.vstack(offsets)


def _formation_error(robot_positions: np.ndarray, pairs: list[tuple[int, int]], slot_positions: np.ndarray) -> float:
    if not pairs or slot_positions.size == 0:
        return 99.0
    errors = []
    for local_idx, (robot_idx, _slot_idx) in enumerate(pairs[: len(slot_positions)]):
        errors.append(float(np.linalg.norm(robot_positions[robot_idx] - slot_positions[local_idx])))
    return float(np.max(errors)) if errors else 99.0


def _pickup_robot_velocities(problem: SP5Problem, cfg: SP5PolicyConfig, positions: np.ndarray, pairs: list[tuple[int, int]], slot_positions: np.ndarray, t_s: float) -> np.ndarray:
    velocities = np.zeros_like(positions)
    for local_idx, (robot_idx, _slot_idx) in enumerate(pairs[: len(slot_positions)]):
        desired = cfg.pickup_gain * (slot_positions[local_idx] - positions[robot_idx])
        desired += _safety_term(problem, positions[robot_idx], t_s, cfg, include_tensor=False)
        desired += _robot_repulsion(problem, positions, robot_idx, cfg)
        velocities[robot_idx] = desired
    return _saturate_robot_velocities(problem, velocities, cfg.speed_scale)


def _transport_robot_velocities(
    problem: SP5Problem,
    cfg: SP5PolicyConfig,
    positions: np.ndarray,
    pairs: list[tuple[int, int]],
    slot_positions: np.ndarray,
    slot_offsets: np.ndarray,
    qd: np.ndarray,
    q: np.ndarray,
    t_s: float,
    transport_mode: str,
) -> np.ndarray:
    velocities = np.zeros_like(positions)
    for local_idx, (robot_idx, _slot_idx) in enumerate(pairs[: len(slot_positions)]):
        offset = slot_offsets[local_idx]
        point_velocity = qd[:2] + qd[2] * np.array([-offset[1], offset[0]], dtype=float)
        gain = cfg.formation_gain * (1.15 if transport_mode == "cargo" else 1.0)
        desired = point_velocity + gain * (slot_positions[local_idx] - positions[robot_idx])
        desired += 0.65 * _safety_term(
            problem,
            positions[robot_idx],
            t_s,
            cfg,
            include_tensor=cfg.tensor_gain > 0.0,
            tangent_goal=slot_positions[local_idx] - positions[robot_idx],
        )
        desired += _robot_repulsion(problem, positions, robot_idx, cfg)
        velocities[robot_idx] = desired
    return _saturate_robot_velocities(problem, velocities, cfg.speed_scale)


def _desired_wrench(problem: SP5Problem, cfg: SP5PolicyConfig, assignment: SP3Assignment, load_idx: int, q: np.ndarray, qd: np.ndarray, target: np.ndarray, t_s: float) -> np.ndarray:
    pos_error = target[:2] - q[:2]
    theta_error = _wrap_angle(float(target[2] - q[2]))
    load = problem.world.loads[load_idx]
    if cfg.explicit_control_law:
        force_limit_sum = _assigned_force_limit_sum(problem, assignment, load_idx)
        inertia = max(float(load.mass_kg * (load.length_m**2 + load.width_m**2) / 12.0), 1e-6)
        gains = ExplicitControlGains(
            load_position_bandwidth=float(cfg.explicit_pose_bandwidth),
            load_orientation_bandwidth=float(cfg.explicit_theta_bandwidth),
            acceleration_limit_fraction=float(cfg.explicit_accel_fraction),
        )
        wrench, _accel = required_wrench_pd(
            mass_total_kg=float(load.mass_kg),
            inertia_total_kgm2=inertia,
            pose=q,
            twist=qd,
            target_pose=target,
            target_twist=np.zeros(3, dtype=float),
            target_acceleration=np.zeros(3, dtype=float),
            gains=gains,
            force_limit_sum_n=force_limit_sum,
        )
        force = wrench[:2]
        tau = float(wrench[2])
    else:
        force = cfg.pose_gain * pos_error - cfg.pose_damping * qd[:2]
        tau = cfg.theta_gain * theta_error - cfg.theta_damping * float(qd[2])
    payload_radius = 0.5 * float(np.hypot(load.length_m, load.width_m))
    safety = _safety_term(
        problem,
        q[:2],
        t_s,
        cfg,
        include_tensor=True,
        body_radius_m=payload_radius,
        tangent_goal=pos_error,
        safety_scale=0.62,
    )
    force += cfg.force_limit_n * safety
    if cfg.energy_shaping_gain > 0.0:
        force -= cfg.energy_shaping_gain * float(np.dot(force, qd[:2])) * qd[:2]
    force = _clip_vector(force, cfg.force_limit_n)
    tau = float(np.clip(tau, -cfg.torque_limit_nm, cfg.torque_limit_nm))
    return np.array([force[0], force[1], tau], dtype=float)


def _assigned_force_limit_sum(problem: SP5Problem, assignment: SP3Assignment, load_idx: int) -> float:
    labels = np.asarray(assignment.labels, dtype=int)
    members = np.flatnonzero(labels == int(load_idx) + 1)
    if members.size == 0:
        return float(problem.force_ref_n)
    return float(sum(problem.world.robots[int(idx)].spec.capacity.force_limit_n for idx in members))


def _achieved_wrench(
    problem: SP5Problem,
    cfg: SP5PolicyConfig,
    assignment: SP3Assignment,
    load_idx: int,
    q: np.ndarray,
    desired: np.ndarray,
    transport_mode: str,
    formation_error: float,
) -> tuple[np.ndarray, float]:
    pairs = _assigned_pairs(problem, assignment, load_idx)
    if not pairs:
        return np.zeros(3, dtype=float), 1.0
    if transport_mode == "cargo":
        achieved = _cargo_wrench(problem, cfg, pairs, load_idx, q, desired)
    else:
        achieved = _push_drag_wrench(problem, cfg, pairs, load_idx, q, desired)
    formation_factor = float(np.clip(1.0 - max(0.0, formation_error - problem.formation_tolerance_m) / max(1.8 * problem.formation_tolerance_m, 1e-9), 0.0, 1.0))
    achieved = achieved * formation_factor
    residual = _normalized_residual(problem, cfg, achieved - desired)
    return achieved, residual


def _push_drag_wrench(problem: SP5Problem, cfg: SP5PolicyConfig, pairs: list[tuple[int, int]], load_idx: int, q: np.ndarray, desired: np.ndarray) -> np.ndarray:
    rotation = _rotation(float(q[2]))
    columns = []
    limits = []
    for robot_idx, slot_idx in pairs:
        slot = problem.load_slots[load_idx][slot_idx]
        offset = rotation @ slot.offset_xy
        direction = rotation @ slot.direction_xy
        torque = float(offset[0] * direction[1] - offset[1] * direction[0])
        columns.append(np.array([direction[0], direction[1], torque], dtype=float))
        limits.append(float(problem.world.robots[robot_idx].spec.capacity.force_limit_n))
    if not columns:
        return np.zeros(3, dtype=float)
    g_matrix = np.column_stack(columns)
    scale = np.diag([1.0 / max(cfg.force_limit_n, 1e-9), 1.0 / max(cfg.force_limit_n, 1e-9), 1.0 / max(cfg.torque_limit_nm, 1e-9)])
    result = lsq_linear(scale @ g_matrix, scale @ desired, bounds=(np.zeros(len(columns)), np.asarray(limits, dtype=float)), lsmr_tol="auto", max_iter=80)
    lambdas = np.asarray(result.x if result.success else np.zeros(len(columns)), dtype=float)
    return g_matrix @ lambdas


def _cargo_wrench(problem: SP5Problem, cfg: SP5PolicyConfig, pairs: list[tuple[int, int]], load_idx: int, q: np.ndarray, desired: np.ndarray) -> np.ndarray:
    rotation = _rotation(float(q[2]))
    columns = []
    lower = []
    upper = []
    for robot_idx, slot_idx in pairs:
        slot = problem.load_slots[load_idx][slot_idx]
        offset = rotation @ slot.offset_xy
        limit = float(problem.world.robots[robot_idx].spec.capacity.force_limit_n) / math.sqrt(2.0)
        columns.append(np.array([1.0, 0.0, -offset[1]], dtype=float))
        columns.append(np.array([0.0, 1.0, offset[0]], dtype=float))
        lower.extend([-limit, -limit])
        upper.extend([limit, limit])
    if not columns:
        return np.zeros(3, dtype=float)
    g_matrix = np.column_stack(columns)
    cargo_force = desired * np.array([1.10, 1.10, 1.05], dtype=float)
    scale = np.diag([1.0 / max(cfg.force_limit_n, 1e-9), 1.0 / max(cfg.force_limit_n, 1e-9), 1.0 / max(cfg.torque_limit_nm, 1e-9)])
    result = lsq_linear(scale @ g_matrix, scale @ cargo_force, bounds=(np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)), lsmr_tol="auto", max_iter=80)
    forces = np.asarray(result.x if result.success else np.zeros(len(columns)), dtype=float)
    return g_matrix @ forces


def _safety_term(
    problem: SP5Problem,
    position: np.ndarray,
    t_s: float,
    cfg: SP5PolicyConfig,
    *,
    include_tensor: bool,
    body_radius_m: float | None = None,
    tangent_goal: np.ndarray | None = None,
    safety_scale: float = 1.0,
) -> np.ndarray:
    term = np.zeros(2, dtype=float)
    body_radius = float(problem.robot_radius_m if body_radius_m is None else body_radius_m)
    for obstacle in problem.world.map.obstacles:
        vec = position - obstacle.center
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        clearance = dist - obstacle.radius - body_radius
        if clearance < obstacle.influence_radius:
            normal = vec / dist
            pressure = max(0.0, 1.0 / max(clearance + 0.15, 0.15) - 1.0 / (obstacle.influence_radius + 0.15))
            term += safety_scale * cfg.obstacle_gain * pressure * normal
            if include_tensor:
                tangent = _tangent_toward_goal(normal, tangent_goal)
                term += safety_scale * max(cfg.tensor_gain, 0.35) * pressure * tangent
            if cfg.cbf_gain > 0.0 and clearance < 0.85:
                term += safety_scale * cfg.cbf_gain * (0.85 - clearance) * normal
    for group in problem.mobile_groups:
        center = group.center_at(t_s, problem.horizon_s)
        vec = position - center
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        clearance = dist - group.radius_m - body_radius
        if clearance < group.influence_radius_m:
            normal = vec / dist
            pressure = max(0.0, 1.0 / max(clearance + 0.18, 0.18) - 1.0 / (group.influence_radius_m + 0.18))
            term += safety_scale * cfg.mobile_gain * pressure * normal
            if cfg.velocity_obstacle_gain > 0.0:
                group_velocity = (group.end_xy - group.start_xy) / max(problem.horizon_s, 1e-9)
                closing = max(0.0, -float(np.dot(group_velocity, normal)))
                term += safety_scale * cfg.velocity_obstacle_gain * closing * normal
            if include_tensor:
                tangent = _tangent_toward_goal(normal, tangent_goal)
                term += safety_scale * max(cfg.tensor_gain, 0.45) * pressure * tangent
    return _clip_vector(term, 1.25)


def _tangent_toward_goal(normal: np.ndarray, tangent_goal: np.ndarray | None) -> np.ndarray:
    tangent = np.array([-normal[1], normal[0]], dtype=float)
    if tangent_goal is None:
        return tangent
    goal = np.asarray(tangent_goal, dtype=float)
    norm = float(np.linalg.norm(goal))
    if norm <= 1e-9:
        return tangent
    goal = goal / norm
    return tangent if float(np.dot(tangent, goal)) >= 0.0 else -tangent


def _robot_repulsion(problem: SP5Problem, positions: np.ndarray, idx: int, cfg: SP5PolicyConfig) -> np.ndarray:
    if cfg.robot_gain <= 0.0:
        return np.zeros(2, dtype=float)
    term = np.zeros(2, dtype=float)
    safe = 2.0 * problem.robot_radius_m + problem.safety_margin_m
    for j in range(positions.shape[0]):
        if j == idx:
            continue
        vec = positions[idx] - positions[j]
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        if not cfg.use_global_traffic and np.isfinite(problem.communication_radius) and dist > problem.communication_radius:
            continue
        influence = max(1.5, 3.0 * safe)
        if dist < influence:
            pressure = (influence - dist) / max(influence - safe, 1e-9)
            term += cfg.robot_gain * max(pressure, 0.0) * vec / dist
    return term


def _saturate_robot_velocities(problem: SP5Problem, velocities: np.ndarray, speed_scale: float) -> np.ndarray:
    out = velocities.copy()
    for idx, robot in enumerate(problem.world.robots):
        limit = max(float(robot.spec.max_speed) * float(speed_scale), 1e-9)
        norm = float(np.linalg.norm(out[idx]))
        if norm > limit:
            out[idx] = out[idx] / norm * limit
    return out


def _clip_positions(problem: SP5Problem, positions: np.ndarray) -> np.ndarray:
    half = 0.5 * problem.world.map.size_m
    return np.clip(positions, -0.92 * half, 0.92 * half)


def _clip_load_pose(problem: SP5Problem, q: np.ndarray) -> np.ndarray:
    half = 0.5 * problem.world.map.size_m
    out = q.copy()
    out[:2] = np.clip(out[:2], -0.82 * half, 0.82 * half)
    out[2] = _wrap_angle(float(out[2]))
    return out


def _project_load_clearance(problem: SP5Problem, load_idx: int, q: np.ndarray, t_s: float) -> np.ndarray:
    """Project payload pose outside static obstacles, traffic groups and other solid loads."""

    desired = _clip_load_pose(problem, q)
    out = desired.copy()
    load = problem.world.loads[load_idx]
    margin = float(problem.safety_margin_m)
    best = out.copy()
    best_clearance = _minimum_load_clearance(problem, load_idx, out, t_s)
    for _pass in range(80):
        previous = out.copy()
        for obstacle in problem.world.map.obstacles:
            out = _project_payload_rectangle_outside_circle(out, load, obstacle.center, obstacle.radius, margin)
        for group in problem.mobile_groups:
            out = _project_payload_rectangle_outside_circle(out, load, group.center_at(t_s, problem.horizon_s), group.radius_m, margin)
        for other_idx, other_load in enumerate(problem.world.loads):
            if other_idx == load_idx:
                continue
            out = _project_payload_rectangle_outside_payload(out, load, _static_load_pose(problem, other_idx), other_load, margin + 0.08)
        out = _clip_load_pose(problem, out)
        clearance = _minimum_load_clearance(problem, load_idx, out, t_s)
        if clearance > best_clearance + 1e-9:
            best_clearance = clearance
            best = out.copy()
        if clearance >= margin:
            break
        if float(np.linalg.norm(out[:2] - previous[:2])) <= 1e-9:
            recovered = _search_payload_clear_pose(problem, load_idx, desired, out, t_s, margin)
            recovered_clearance = _minimum_load_clearance(problem, load_idx, recovered, t_s)
            if recovered_clearance > best_clearance + 1e-9:
                best_clearance = recovered_clearance
                best = recovered.copy()
            out = recovered
            if recovered_clearance >= margin:
                break
            if float(np.linalg.norm(out[:2] - previous[:2])) <= 1e-9:
                break
    if _minimum_load_clearance(problem, load_idx, out, t_s) + 1e-9 < best_clearance:
        out = best
    return out


def _project_robot_clearance(problem: SP5Problem, positions: np.ndarray, t_s: float) -> np.ndarray:
    """Project AMR centers outside obstacles, moving traffic groups and pairwise overlap."""

    out = _clip_positions(problem, positions)
    margin = float(problem.safety_margin_m + 0.035)
    for _pass in range(48):
        previous = out.copy()
        for idx in range(out.shape[0]):
            for obstacle in problem.world.map.obstacles:
                min_distance = float(obstacle.radius + problem.robot_radius_m + margin)
                out[idx] = _project_point_outside(out[idx], obstacle.center, min_distance)
            for group in problem.mobile_groups:
                min_distance = float(group.radius_m + problem.robot_radius_m + margin)
                out[idx] = _project_point_outside(out[idx], group.center_at(t_s, problem.horizon_s), min_distance)
        for i in range(out.shape[0]):
            for j in range(i + 1, out.shape[0]):
                vec = out[i] - out[j]
                dist = float(np.linalg.norm(vec))
                min_distance = float(2.0 * problem.robot_radius_m + margin)
                if dist >= min_distance:
                    continue
                if dist <= 1e-9:
                    vec = np.array([1.0, 0.0], dtype=float)
                    dist = 1.0
                correction = 0.5 * (min_distance - dist) * vec / dist
                out[i] += correction
                out[j] -= correction
        out = _clip_positions(problem, out)
        if float(np.linalg.norm(out - previous)) <= 1e-9:
            break
    return out


def _project_point_outside(point: np.ndarray, center: np.ndarray, min_distance: float) -> np.ndarray:
    out = np.asarray(point, dtype=float).copy()
    vec = out - np.asarray(center, dtype=float)
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        vec = np.array([1.0, 0.0], dtype=float)
        dist = 1.0
    if dist < min_distance:
        out = np.asarray(center, dtype=float) + (vec / dist) * float(min_distance)
    return out


def _project_payload_rectangle_outside_circle(q: np.ndarray, load: Any, center: np.ndarray, radius: float, margin: float) -> np.ndarray:
    out = np.asarray(q, dtype=float).copy()
    center = np.asarray(center, dtype=float)
    rotation = _rotation(float(out[2]))
    local = rotation.T @ (center - out[:2])
    half_extents = np.array([0.5 * float(load.length_m), 0.5 * float(load.width_m)], dtype=float)
    closest = np.clip(local, -half_extents, half_extents)
    delta_local = local - closest
    distance = float(np.linalg.norm(delta_local))
    if distance > 1e-9:
        clearance = distance - float(radius)
        if clearance < margin:
            normal_world = rotation @ (delta_local / distance)
            out[:2] -= normal_world * (float(margin) - clearance + 1e-6)
        return out

    inflated = half_extents + float(radius + margin)
    penetration = inflated - np.abs(local)
    axis = int(np.argmin(penetration))
    sign = math.copysign(1.0, float(local[axis]))
    if abs(float(local[axis])) <= 1e-9:
        sign = 1.0
    correction_local = np.zeros(2, dtype=float)
    correction_local[axis] = -sign * (float(penetration[axis]) + 1e-6)
    out[:2] += rotation @ correction_local
    return out


def _search_payload_clear_pose(
    problem: SP5Problem,
    load_idx: int,
    desired_q: np.ndarray,
    current_q: np.ndarray,
    t_s: float,
    margin: float,
) -> np.ndarray:
    """Deterministic local recovery when sequential projections cycle."""

    desired = _clip_load_pose(problem, desired_q)
    current = _clip_load_pose(problem, current_q)
    candidates = [desired, current]
    load = problem.world.loads[load_idx]
    for obstacle in problem.world.map.obstacles:
        candidates.append(_project_payload_rectangle_outside_circle(desired, load, obstacle.center, obstacle.radius, margin))
        candidates.append(_project_payload_rectangle_outside_circle(current, load, obstacle.center, obstacle.radius, margin))
    for group in problem.mobile_groups:
        center = group.center_at(t_s, problem.horizon_s)
        candidates.append(_project_payload_rectangle_outside_circle(desired, load, center, group.radius_m, margin))
        candidates.append(_project_payload_rectangle_outside_circle(current, load, center, group.radius_m, margin))

    angles = np.linspace(0.0, 2.0 * math.pi, 72, endpoint=False)
    radii = np.array([0.15, 0.30, 0.50, 0.75, 1.05, 1.40, 1.80, 2.30, 2.90, 3.60, 4.50, 5.60], dtype=float)
    anchors = (desired[:2].copy(), current[:2].copy())
    for anchor in anchors:
        for radius in radii:
            offsets = np.column_stack((np.cos(angles), np.sin(angles))) * float(radius)
            for offset in offsets:
                candidate = desired.copy()
                candidate[:2] = anchor + offset
                candidates.append(_clip_load_pose(problem, candidate))

    best = current.copy()
    best_clearance = _minimum_load_clearance(problem, load_idx, best, t_s)
    best_cost = float(np.linalg.norm(best[:2] - desired[:2]))
    for candidate in candidates:
        candidate = _clip_load_pose(problem, candidate)
        clearance = _minimum_load_clearance(problem, load_idx, candidate, t_s)
        cost = float(np.linalg.norm(candidate[:2] - desired[:2]))
        if clearance >= margin:
            if best_clearance < margin or cost < best_cost - 1e-9:
                best = candidate.copy()
                best_clearance = clearance
                best_cost = cost
            continue
        if clearance > best_clearance + 1e-9 or (abs(clearance - best_clearance) <= 1e-9 and cost < best_cost):
            best = candidate.copy()
            best_clearance = clearance
            best_cost = cost
    return best


def _minimum_load_clearance(problem: SP5Problem, load_idx: int, q: np.ndarray, t_s: float) -> float:
    load = problem.world.loads[load_idx]
    values: list[float] = []
    for obstacle in problem.world.map.obstacles:
        values.append(_payload_rectangle_circle_clearance_local(q, load, obstacle.center, float(obstacle.radius)))
    for group in problem.mobile_groups:
        values.append(_payload_rectangle_circle_clearance_local(q, load, group.center_at(t_s, problem.horizon_s), float(group.radius_m)))
    for other_idx, other_load in enumerate(problem.world.loads):
        if other_idx == load_idx:
            continue
        values.append(_payload_rectangle_rectangle_clearance_local(q, load, _static_load_pose(problem, other_idx), other_load))
    return float(min(values)) if values else float("inf")


def _payload_rectangle_circle_clearance_local(q: np.ndarray, load: Any, center: np.ndarray, radius_m: float) -> float:
    rotation_t = _rotation(float(q[2])).T
    local = rotation_t @ (np.asarray(center, dtype=float) - np.asarray(q[:2], dtype=float))
    half_extents = np.array([0.5 * float(load.length_m), 0.5 * float(load.width_m)], dtype=float)
    outside = np.maximum(np.abs(local) - half_extents, 0.0)
    return float(np.linalg.norm(outside) - float(radius_m))


def _payload_rectangle_rectangle_clearance_local(q_a: np.ndarray, load_a: Any, q_b: np.ndarray, load_b: Any) -> float:
    vec = np.asarray(q_a[:2], dtype=float) - np.asarray(q_b[:2], dtype=float)
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        normal = np.array([1.0, 0.0], dtype=float)
        dist = 0.0
    else:
        normal = vec / dist
    return float(dist - _payload_support_radius(q_a, load_a, normal) - _payload_support_radius(q_b, load_b, -normal))


def _project_payload_rectangle_outside_payload(q: np.ndarray, load: Any, other_q: np.ndarray, other_load: Any, margin: float) -> np.ndarray:
    out = np.asarray(q, dtype=float).copy()
    other_q = np.asarray(other_q, dtype=float)
    vec = out[:2] - other_q[:2]
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        vec = np.array([1.0, 0.0], dtype=float)
        dist = 1.0
    normal = vec / dist
    support_radius = _payload_support_radius(out, load, normal)
    other_support_radius = _payload_support_radius(other_q, other_load, -normal)
    min_distance = float(support_radius + other_support_radius + margin)
    if dist < min_distance:
        out[:2] = other_q[:2] + normal * min_distance
    return out


def _payload_support_radius(q: np.ndarray, load: Any, normal: np.ndarray) -> float:
    rotation = _rotation(float(q[2]))
    return float(
        0.5 * float(load.length_m) * abs(float(np.dot(normal, rotation[:, 0])))
        + 0.5 * float(load.width_m) * abs(float(np.dot(normal, rotation[:, 1])))
    )


def _static_load_pose(problem: SP5Problem, load_idx: int) -> np.ndarray:
    load = problem.world.loads[load_idx]
    if load_idx == problem.task.load_index:
        return problem.task.initial_pose.copy()
    return np.array([float(load.pickup[0]), float(load.pickup[1]), 0.0], dtype=float)


def _clip_vector(vector: np.ndarray, limit: float) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm > max(limit, 1e-9):
        return vector / norm * limit
    return np.asarray(vector, dtype=float)


def _normalized_residual(problem: SP5Problem, cfg: SP5PolicyConfig, error: np.ndarray) -> float:
    return float(
        np.linalg.norm(
            np.array(
                [
                    error[0] / max(cfg.force_limit_n, problem.force_ref_n, 1e-9),
                    error[1] / max(cfg.force_limit_n, problem.force_ref_n, 1e-9),
                    error[2] / max(cfg.torque_limit_nm, problem.torque_ref_nm, 1e-9),
                ],
                dtype=float,
            )
        )
    )


def _rotation(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi
