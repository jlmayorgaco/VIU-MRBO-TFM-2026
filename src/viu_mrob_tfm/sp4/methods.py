"""Motion policies for SP4 post-allocation AMR arrival experiments."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from time import perf_counter
from typing import Any

import numpy as np

from viu_mrob_tfm.control.explicit_law import CircularHazard, ExplicitControlGains, closed_form_hocbf_projection
from viu_mrob_tfm.sp4.scenario import SP4Problem


SP4_METHOD_LABELS = {
    "direct_to_target": "Direct to target",
    "priority_yield": "Priority yield",
    "apf_obstacle_avoidance": "APF obstacle avoidance",
    "velocity_obstacle_proxy": "Velocity obstacle proxy",
    "cbf_safety_filter": "CBF safety filter",
    "replicator_motion_field": "Replicator motion field",
    "logit_motion_field": "Logit motion field",
    "bnn_motion_field": "BNN/Brown motion field",
    "primal_dual_motion_field": "Primal-dual motion field",
    "pid_safety_motion": "PID safety motion",
    "tensor_flow_motion_field": "Smooth tensor-flow motion",
    "explicit_vgne_cbf_motion": "Ours explicit vGNE-CBF motion",
    "smith_motion_field": "Smith-QR motion field",
    "energy_aware_smith_motion": "Energy-aware Smith motion",
    "reference_time_expanded_cbf": "Reference time-expanded CBF",
}


METHOD_META = {
    "direct_to_target": ("classic", "decentralized", "baseline", "direct_single_integrator", "sp4_motion_baseline"),
    "priority_yield": ("classic", "centralized", "baseline", "priority_release_yield", "sp4_motion_baseline"),
    "apf_obstacle_avoidance": ("classic", "decentralized", "baseline", "artificial_potential_field", "sp4_motion_baseline"),
    "velocity_obstacle_proxy": ("sota", "decentralized", "baseline", "velocity_obstacle_proxy", "sp4_motion_sota_proxy"),
    "cbf_safety_filter": ("sota", "centralized", "baseline", "cbf_velocity_projection_proxy", "sp4_motion_sota_proxy"),
    "replicator_motion_field": ("model_based", "decentralized", "baseline", "replicator_target_congestion_field", "sp4_population_motion_family"),
    "logit_motion_field": ("model_based", "decentralized", "baseline", "logit_softmax_motion_field", "sp4_population_motion_family"),
    "bnn_motion_field": ("model_based", "decentralized", "baseline", "brown_bnn_positive_excess_field", "sp4_population_motion_family"),
    "primal_dual_motion_field": ("model_based", "decentralized", "proposed", "primal_dual_barrier_motion_field", "sp4_motion_proposed"),
    "pid_safety_motion": ("model_based", "decentralized", "proposed", "pid_damped_safety_motion", "sp4_motion_proposed"),
    "tensor_flow_motion_field": ("model_based", "decentralized", "proposed", "smooth_tensor_flow_barrier_motion", "sp4_motion_proposed"),
    "explicit_vgne_cbf_motion": ("model_based", "decentralized", "proposed", "closed_form_explicit_amr_vgne_cbf", "sp4_explicit_control_law"),
    "smith_motion_field": ("model_based", "decentralized", "proposed", "smith_qr_congestion_field", "sp4_motion_proposed"),
    "energy_aware_smith_motion": ("model_based", "decentralized", "proposed", "smith_qr_energy_congestion_field", "sp4_motion_proposed"),
    "reference_time_expanded_cbf": ("model_based_reference", "centralized", "reference", "time_expanded_safe_cbf_reference", "sp4_motion_reference"),
}


METHOD_RESOURCES = {
    "direct_to_target": ("none", "local_target_feedback", "none", 0, 0, False, False),
    "priority_yield": ("none", "centralized_priority_schedule", "global_priority_order", 0, 2, False, False),
    "apf_obstacle_avoidance": ("none", "local_apf_feedback", "local_obstacle_robot_neighbors", 0, 4, False, False),
    "velocity_obstacle_proxy": ("none", "local_velocity_obstacle_proxy", "local_relative_state_neighbors", 0, 5, False, False),
    "cbf_safety_filter": ("none", "centralized_cbf_velocity_projection_proxy", "global_relative_state", 0, 6, False, False),
    "replicator_motion_field": ("none", "distributed_replicator_motion_field", "local_target_obstacle_neighbor_scores", 0, 5, False, False),
    "logit_motion_field": ("none", "distributed_logit_smoothed_motion_field", "local_softmax_flow_scores", 0, 6, False, False),
    "bnn_motion_field": ("none", "distributed_bnn_positive_excess_motion_field", "local_positive_excess_neighbor_scores", 0, 6, False, False),
    "primal_dual_motion_field": ("none", "distributed_primal_dual_barrier_motion_field", "local_barrier_dual_prices", 0, 7, False, False),
    "pid_safety_motion": ("none", "distributed_pid_damped_safety_feedback", "local_target_error_and_clearance", 0, 5, False, False),
    "tensor_flow_motion_field": ("none", "distributed_smooth_tensor_flow_motion_field", "local_anisotropic_clearance_tensor", 0, 8, False, False),
    "explicit_vgne_cbf_motion": ("closed_form_model_based", "distributed_explicit_amr_vgne_cbf_hand_point", "local_target_obstacle_neighbor_state_plus_consensus_scalars", 0, 10, False, False),
    "smith_motion_field": ("none", "distributed_smith_qr_motion_field", "local_congestion_price_neighbors", 0, 6, False, False),
    "energy_aware_smith_motion": ("none", "distributed_smith_qr_energy_motion_field", "local_congestion_energy_neighbors", 0, 7, False, False),
    "reference_time_expanded_cbf": ("none", "centralized_time_expanded_cbf_reference", "global_state_and_release_schedule", 0, 8, False, False),
}


@dataclass(frozen=True, slots=True)
class MotionPolicyConfig:
    target_gain: float = 1.25
    obstacle_gain: float = 0.0
    robot_gain: float = 0.0
    cbf_gain: float = 0.0
    velocity_obstacle_gain: float = 0.0
    speed_scale: float = 1.0
    release_interval_s: float = 0.0
    priority_yield: bool = False
    energy_aware: bool = False
    use_global_neighbors: bool = False
    explicit_control_law: bool = False
    explicit_position_bandwidth: float = 1.15
    explicit_safety_k: float = 2.8
    explicit_acceleration_limit: float = 2.0


@dataclass(frozen=True, slots=True)
class SP4TrajectoryResult:
    method: str
    time_s: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    arrival_times_s: np.ndarray
    reached: np.ndarray
    runtime_ms: float


class BaseMotionPolicy:
    method_id = "base"

    def __init__(self, config: MotionPolicyConfig | None = None) -> None:
        self.config = config or MotionPolicyConfig()

    def velocity(self, problem: SP4Problem, positions: np.ndarray, velocities: np.ndarray, reached: np.ndarray, step_idx: int) -> np.ndarray:
        raise NotImplementedError


class PotentialMotionPolicy(BaseMotionPolicy):
    """Single-integrator target tracking with optional safety and congestion terms."""

    def velocity(self, problem: SP4Problem, positions: np.ndarray, velocities: np.ndarray, reached: np.ndarray, step_idx: int) -> np.ndarray:
        cfg = self.config
        n = len(problem.world.robots)
        out = np.zeros((n, 2), dtype=float)
        time_s = step_idx * problem.dt_s
        for idx in range(n):
            if reached[idx] or time_s < cfg.release_interval_s * idx:
                continue
            if cfg.explicit_control_law:
                out[idx] = _explicit_control_velocity(problem, positions, velocities, idx, cfg)
                continue
            error = problem.target_xy[idx] - positions[idx]
            desired = cfg.target_gain * error
            desired += _obstacle_term(problem, positions[idx], cfg.obstacle_gain)
            desired += _robot_term(problem, positions, velocities, idx, cfg)
            if cfg.priority_yield:
                desired = _priority_yield(positions, idx, desired)
            if cfg.cbf_gain > 0.0:
                desired = _cbf_project(problem, positions, idx, desired, cfg.cbf_gain)
            if cfg.energy_aware:
                desired *= _energy_speed_factor(problem, idx)
            out[idx] = desired
        return _saturate(problem, out, cfg.speed_scale)


def make_sp4_policy(method_id: str, params: dict[str, Any] | None = None) -> BaseMotionPolicy:
    """Create an SP4 motion policy by stable method id."""

    params = params or {}
    method = _canonical_method(method_id)
    cfg = _default_config(method)
    if params:
        allowed = {field.name for field in fields(MotionPolicyConfig)}
        cfg = replace(cfg, **{key: value for key, value in params.items() if key in allowed})
    policy = PotentialMotionPolicy(cfg)
    policy.method_id = method
    return policy


def simulate_motion(policy: BaseMotionPolicy, problem: SP4Problem) -> SP4TrajectoryResult:
    """Roll out one SP4 motion policy on a fixed problem."""

    start = perf_counter()
    steps = int(np.ceil(problem.horizon_s / problem.dt_s))
    n = len(problem.world.robots)
    positions = np.zeros((steps + 1, n, 2), dtype=float)
    velocities = np.zeros((steps + 1, n, 2), dtype=float)
    positions[0] = np.vstack([robot.position for robot in problem.world.robots])
    arrival = np.full(n, np.nan, dtype=float)
    reached = np.zeros(n, dtype=bool)
    half = 0.5 * problem.world.map.size_m
    for step in range(steps):
        dist = np.linalg.norm(problem.target_xy - positions[step], axis=1)
        newly_reached = (~reached) & (dist <= problem.target_tolerance_m)
        arrival[newly_reached] = step * problem.dt_s
        reached = reached | newly_reached
        commanded = policy.velocity(problem, positions[step], velocities[step], reached, step)
        commanded[reached] = 0.0
        velocities[step] = commanded
        next_pos = positions[step] + problem.dt_s * commanded
        positions[step + 1] = np.clip(next_pos, -half, half)
    final_dist = np.linalg.norm(problem.target_xy - positions[-1], axis=1)
    newly_reached = (~reached) & (final_dist <= problem.target_tolerance_m)
    arrival[newly_reached] = steps * problem.dt_s
    reached = reached | newly_reached
    runtime_ms = 1000.0 * (perf_counter() - start)
    return SP4TrajectoryResult(
        method=policy.method_id if policy.method_id != "base" else "motion_policy",
        time_s=np.arange(steps + 1, dtype=float) * problem.dt_s,
        positions=positions,
        velocities=velocities,
        arrival_times_s=arrival,
        reached=reached,
        runtime_ms=runtime_ms,
    )


def sp4_method_metadata(method_id: str) -> dict[str, Any]:
    method = _canonical_method(method_id)
    family, scope, ownership, variant, group = METHOD_META[method]
    return {
        "label": SP4_METHOD_LABELS.get(method, method),
        "title": SP4_METHOD_LABELS.get(method, method),
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "comparison_group": group,
        "training_type": METHOD_RESOURCES[method][0],
        "execution_model": METHOD_RESOURCES[method][1],
        "communication_pattern": METHOD_RESOURCES[method][2],
        "trainable_parameters": METHOD_RESOURCES[method][3],
        "tuned_parameters": METHOD_RESOURCES[method][4],
        "uses_neural_policy": METHOD_RESOURCES[method][5],
        "uses_decoder": METHOD_RESOURCES[method][6],
    }


def _canonical_method(method_id: str) -> str:
    method = method_id.lower()
    aliases = {
        "direct": "direct_to_target",
        "straight_line": "direct_to_target",
        "apf": "apf_obstacle_avoidance",
        "vo": "velocity_obstacle_proxy",
        "cbf": "cbf_safety_filter",
        "replicator": "replicator_motion_field",
        "logit": "logit_motion_field",
        "brown": "bnn_motion_field",
        "bnn": "bnn_motion_field",
        "primal_dual": "primal_dual_motion_field",
        "pid": "pid_safety_motion",
        "tensor_flow": "tensor_flow_motion_field",
        "explicit": "explicit_vgne_cbf_motion",
        "explicit_vgne_cbf": "explicit_vgne_cbf_motion",
        "smith": "smith_motion_field",
        "energy_smith": "energy_aware_smith_motion",
        "reference": "reference_time_expanded_cbf",
    }
    method = aliases.get(method, method)
    if method not in METHOD_META:
        raise ValueError(f"Unknown SP4 method: {method_id}")
    return method


def _default_config(method: str) -> MotionPolicyConfig:
    if method == "direct_to_target":
        return MotionPolicyConfig(target_gain=1.35, speed_scale=1.0)
    if method == "priority_yield":
        return MotionPolicyConfig(target_gain=1.25, speed_scale=0.92, release_interval_s=0.22, priority_yield=True, use_global_neighbors=True)
    if method == "apf_obstacle_avoidance":
        return MotionPolicyConfig(target_gain=1.25, obstacle_gain=0.70, robot_gain=0.28, speed_scale=0.92)
    if method == "velocity_obstacle_proxy":
        return MotionPolicyConfig(target_gain=1.22, obstacle_gain=0.55, robot_gain=0.34, velocity_obstacle_gain=0.55, speed_scale=0.90)
    if method == "cbf_safety_filter":
        return MotionPolicyConfig(target_gain=1.32, obstacle_gain=0.38, robot_gain=0.22, cbf_gain=0.88, speed_scale=0.94, use_global_neighbors=True)
    if method == "replicator_motion_field":
        return MotionPolicyConfig(target_gain=1.22, obstacle_gain=0.42, robot_gain=0.26, velocity_obstacle_gain=0.14, speed_scale=0.92)
    if method == "logit_motion_field":
        return MotionPolicyConfig(target_gain=1.16, obstacle_gain=0.48, robot_gain=0.30, velocity_obstacle_gain=0.18, speed_scale=0.88)
    if method == "bnn_motion_field":
        return MotionPolicyConfig(target_gain=1.20, obstacle_gain=0.56, robot_gain=0.38, velocity_obstacle_gain=0.16, speed_scale=0.86)
    if method == "primal_dual_motion_field":
        return MotionPolicyConfig(target_gain=1.26, obstacle_gain=0.50, robot_gain=0.36, cbf_gain=0.70, velocity_obstacle_gain=0.18, speed_scale=0.90)
    if method == "pid_safety_motion":
        return MotionPolicyConfig(target_gain=1.05, obstacle_gain=0.46, robot_gain=0.28, cbf_gain=0.50, speed_scale=0.82)
    if method == "tensor_flow_motion_field":
        return MotionPolicyConfig(target_gain=1.30, obstacle_gain=0.62, robot_gain=0.42, cbf_gain=0.72, velocity_obstacle_gain=0.28, speed_scale=0.88)
    if method == "explicit_vgne_cbf_motion":
        return MotionPolicyConfig(target_gain=1.22, obstacle_gain=0.40, robot_gain=0.30, cbf_gain=0.68, velocity_obstacle_gain=0.18, speed_scale=0.90, explicit_control_law=True, explicit_position_bandwidth=1.20, explicit_safety_k=3.0, explicit_acceleration_limit=2.2)
    if method == "smith_motion_field":
        return MotionPolicyConfig(target_gain=1.32, obstacle_gain=0.48, robot_gain=0.34, cbf_gain=0.58, velocity_obstacle_gain=0.22, speed_scale=0.94)
    if method == "energy_aware_smith_motion":
        return MotionPolicyConfig(target_gain=1.24, obstacle_gain=0.44, robot_gain=0.32, cbf_gain=0.55, velocity_obstacle_gain=0.20, speed_scale=0.84, energy_aware=True)
    if method == "reference_time_expanded_cbf":
        return MotionPolicyConfig(target_gain=1.38, obstacle_gain=0.52, robot_gain=0.24, cbf_gain=0.95, speed_scale=0.96, release_interval_s=0.06, priority_yield=True, use_global_neighbors=True)
    raise ValueError(f"Unknown SP4 method: {method}")


def _obstacle_term(problem: SP4Problem, position: np.ndarray, gain: float) -> np.ndarray:
    if gain <= 0.0:
        return np.zeros(2, dtype=float)
    term = np.zeros(2, dtype=float)
    for obstacle in problem.world.map.obstacles:
        vec = position - obstacle.center
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        clearance = dist - obstacle.radius - problem.robot_radius_m - problem.safety_margin_m
        influence = max(obstacle.influence_radius, obstacle.radius + 0.5)
        if clearance < influence:
            pressure = (1.0 / max(clearance + 0.12, 0.12) - 1.0 / (influence + 0.12))
            term += gain * max(pressure, 0.0) * (vec / dist)
    return term


def _explicit_control_velocity(problem: SP4Problem, positions: np.ndarray, velocities: np.ndarray, idx: int, cfg: MotionPolicyConfig) -> np.ndarray:
    """Closed-form Step-6/7 motion command for the hand-point controller."""

    pos = positions[idx]
    vel = velocities[idx]
    target = problem.target_xy[idx]
    k = max(float(cfg.explicit_position_bandwidth), 0.0)
    nominal_accel = 2.0 * np.sqrt(k) * (-vel) + k * (target - pos)
    hazards = _explicit_hazards(problem, positions, velocities, idx, cfg)
    gains = ExplicitControlGains(
        load_position_bandwidth=k,
        safety_k1=float(cfg.explicit_safety_k),
        safety_k2=float(cfg.explicit_safety_k),
        max_hand_acceleration=float(cfg.explicit_acceleration_limit),
    )
    safe_accel = closed_form_hocbf_projection(
        nominal_accel,
        pos,
        vel,
        hazards,
        0.0,
        gains=gains,
        passes=5,
        hazard_acceleration_bound=0.0,
    )
    safe_accel = _clip_vector(safe_accel, float(cfg.explicit_acceleration_limit))
    desired = cfg.target_gain * (target - pos) + problem.dt_s * safe_accel
    desired += _obstacle_term(problem, pos, cfg.obstacle_gain)
    desired += _robot_term(problem, positions, velocities, idx, cfg)
    return desired


def _explicit_hazards(problem: SP4Problem, positions: np.ndarray, velocities: np.ndarray, idx: int, cfg: MotionPolicyConfig) -> list[CircularHazard]:
    hazards: list[CircularHazard] = []
    for obstacle in problem.world.map.obstacles:
        hazards.append(
            CircularHazard(
                center_xy=obstacle.center,
                velocity_xy=np.zeros(2, dtype=float),
                radius_m=float(obstacle.radius + problem.robot_radius_m + problem.safety_margin_m),
                cooperative=False,
            )
        )
    for j in range(positions.shape[0]):
        if j == idx:
            continue
        dist = float(np.linalg.norm(positions[idx] - positions[j]))
        if not cfg.use_global_neighbors and np.isfinite(problem.communication_radius) and dist > problem.communication_radius:
            continue
        hazards.append(
            CircularHazard(
                center_xy=positions[j],
                velocity_xy=velocities[j],
                radius_m=float(2.0 * problem.robot_radius_m + problem.safety_margin_m),
                cooperative=True,
            )
        )
    return hazards


def _clip_vector(vector: np.ndarray, limit: float) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm > max(float(limit), 1e-9):
        return vector / norm * float(limit)
    return np.asarray(vector, dtype=float)


def _robot_term(problem: SP4Problem, positions: np.ndarray, velocities: np.ndarray, idx: int, cfg: MotionPolicyConfig) -> np.ndarray:
    if cfg.robot_gain <= 0.0 and cfg.velocity_obstacle_gain <= 0.0:
        return np.zeros(2, dtype=float)
    term = np.zeros(2, dtype=float)
    for j in range(positions.shape[0]):
        if j == idx:
            continue
        vec = positions[idx] - positions[j]
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        if not cfg.use_global_neighbors and np.isfinite(problem.communication_radius) and dist > problem.communication_radius:
            continue
        safe = 2.0 * problem.robot_radius_m + problem.safety_margin_m
        influence = max(1.8, 3.2 * safe)
        if dist < influence:
            pressure = (influence - dist) / max(influence - safe, 1e-9)
            term += cfg.robot_gain * max(pressure, 0.0) * vec / dist
        if cfg.velocity_obstacle_gain > 0.0:
            rel_vel = velocities[idx] - velocities[j]
            closing = -float(np.dot(rel_vel, vec / dist))
            if closing > 0.0 and dist < 2.8:
                term += cfg.velocity_obstacle_gain * closing * vec / dist
    return term


def _priority_yield(positions: np.ndarray, idx: int, desired: np.ndarray) -> np.ndarray:
    adjusted = desired.copy()
    for j in range(idx):
        vec = positions[j] - positions[idx]
        dist = float(np.linalg.norm(vec))
        if dist < 1.15:
            forward = float(np.dot(adjusted, vec / max(dist, 1e-9)))
            if forward > 0.0:
                adjusted -= min(0.85, 1.15 - dist) * forward * vec / max(dist, 1e-9)
    return adjusted


def _cbf_project(problem: SP4Problem, positions: np.ndarray, idx: int, desired: np.ndarray, gain: float) -> np.ndarray:
    projected = desired.copy()
    pos = positions[idx]
    for obstacle in problem.world.map.obstacles:
        vec = pos - obstacle.center
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            continue
        normal = vec / dist
        clearance = dist - obstacle.radius - problem.robot_radius_m
        if clearance < obstacle.influence_radius:
            inward = -float(np.dot(projected, normal))
            limit = gain * max(clearance - problem.safety_margin_m, -0.2)
            if inward > limit:
                projected += (inward - limit) * normal
    for j in range(positions.shape[0]):
        if j == idx:
            continue
        vec = pos - positions[j]
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            continue
        normal = vec / dist
        clearance = dist - 2.0 * problem.robot_radius_m
        if clearance < 1.55:
            inward = -float(np.dot(projected, normal))
            limit = gain * max(clearance - problem.safety_margin_m, -0.2)
            if inward > limit:
                projected += (inward - limit) * normal
    return projected


def _energy_speed_factor(problem: SP4Problem, idx: int) -> float:
    battery = problem.world.robots[idx].battery_fraction
    return float(np.clip(0.62 + 0.45 * battery, 0.62, 1.0))


def _saturate(problem: SP4Problem, velocities: np.ndarray, speed_scale: float) -> np.ndarray:
    out = velocities.copy()
    for idx, robot in enumerate(problem.world.robots):
        limit = max(float(robot.spec.max_speed) * float(speed_scale), 1e-9)
        norm = float(np.linalg.norm(out[idx]))
        if norm > limit:
            out[idx] = out[idx] / norm * limit
    return out
