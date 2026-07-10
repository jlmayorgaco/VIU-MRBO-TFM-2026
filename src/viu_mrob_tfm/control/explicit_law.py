"""Closed-form AMR control law used by the executable SP experiments.

The formulas in this module implement the explicit sensor-to-actuator law
documented in the July 2026 control notes.  The implementation keeps the
project vocabulary as AMR throughout.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True, slots=True)
class ExplicitControlGains:
    """Dimensioned gains for the closed-form AMR control law."""

    load_position_bandwidth: float = 1.0
    load_orientation_bandwidth: float = 1.0
    hand_position_bandwidth: float = 5.0
    safety_k1: float = 2.8
    safety_k2: float = 2.8
    acceleration_limit_fraction: float = 0.8
    max_hand_acceleration: float = 2.5


@dataclass(frozen=True, slots=True)
class CircularHazard:
    """Circular obstacle or robot footprint for closed-form HOCBF projection."""

    center_xy: np.ndarray
    velocity_xy: np.ndarray
    radius_m: float
    cooperative: bool = False

    def __post_init__(self) -> None:
        center = np.asarray(self.center_xy, dtype=float)
        velocity = np.asarray(self.velocity_xy, dtype=float)
        if center.shape != (2,) or velocity.shape != (2,):
            raise ValueError("CircularHazard center_xy and velocity_xy must be 2D vectors.")
        object.__setattr__(self, "center_xy", center)
        object.__setattr__(self, "velocity_xy", velocity)


def unit_heading(theta: float) -> np.ndarray:
    """Return e(theta) = [cos(theta), sin(theta)]."""

    return np.array([math.cos(theta), math.sin(theta)], dtype=float)


def perp(vector: np.ndarray) -> np.ndarray:
    """Return the +90 degree planar rotation [-y, x]."""

    vec = np.asarray(vector, dtype=float)
    return np.array([-vec[1], vec[0]], dtype=float)


def rotation(theta: float) -> np.ndarray:
    """Planar rotation matrix."""

    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def wrap_angle(value: float) -> float:
    """Wrap an angle to (-pi, pi]."""

    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi


def hand_point(
    position_xy: np.ndarray,
    theta: float,
    linear_speed: float,
    angular_speed: float,
    lookahead_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the look-ahead hand point and its velocity.

    h = p + a e(theta)
    h_dot = v e(theta) + a omega e_perp(theta)
    """

    p = np.asarray(position_xy, dtype=float)
    if p.shape != (2,):
        raise ValueError("position_xy must be a 2D vector.")
    e = unit_heading(theta)
    e_perp = perp(e)
    h = p + float(lookahead_m) * e
    h_dot = float(linear_speed) * e + float(lookahead_m) * float(angular_speed) * e_perp
    return h, h_dot


def reconstruct_load_state_from_contact(
    hand_xy: np.ndarray,
    hand_velocity_xy: np.ndarray,
    theta: float,
    angular_speed: float,
    grasp_heading_offset: float,
    slot_offset_body: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct load pose/twist from one rigid contact point."""

    hand = np.asarray(hand_xy, dtype=float)
    hand_dot = np.asarray(hand_velocity_xy, dtype=float)
    r_body = np.asarray(slot_offset_body, dtype=float)
    if hand.shape != (2,) or hand_dot.shape != (2,) or r_body.shape != (2,):
        raise ValueError("hand, hand_dot and slot_offset_body must be 2D vectors.")
    phi = wrap_angle(float(theta) - float(grasp_heading_offset))
    r_world = rotation(phi) @ r_body
    p_load = hand - r_world
    p_load_dot = hand_dot - float(angular_speed) * perp(r_world)
    return np.array([p_load[0], p_load[1], phi], dtype=float), np.array([p_load_dot[0], p_load_dot[1], float(angular_speed)], dtype=float)


def effective_health(nominal_weight: float, battery_fraction: float, *, floor_fraction: float = 0.05) -> float:
    """Battery-scaled game weight eta_i."""

    return float(nominal_weight) * max(float(battery_fraction), float(floor_fraction))


def dynamic_average_consensus_step(
    estimate_i: float,
    neighbor_estimates: Iterable[float],
    own_signal: float,
    previous_own_signal: float,
    dt_s: float,
    consensus_gain: float,
    team_size: int,
) -> tuple[float, float]:
    """One dynamic average consensus update for H or S."""

    correction = sum(float(value) - float(estimate_i) for value in neighbor_estimates)
    next_estimate = float(estimate_i) + float(dt_s) * float(consensus_gain) * correction + (float(own_signal) - float(previous_own_signal))
    return next_estimate, float(team_size) * next_estimate


def required_wrench_pd(
    *,
    mass_total_kg: float,
    inertia_total_kgm2: float,
    pose: np.ndarray,
    twist: np.ndarray,
    target_pose: np.ndarray,
    target_twist: np.ndarray | None = None,
    target_acceleration: np.ndarray | None = None,
    gains: ExplicitControlGains | None = None,
    force_limit_sum_n: float | None = None,
    linear_disturbance_n: np.ndarray | None = None,
    angular_disturbance_nm: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the closed-form load wrench with critical damping and clipping.

    The translational part is
    a_cmd = a_des + 2 sqrt(k_p) e_dot + k_p e,
    then clipped without changing direction.  The rotational part follows the
    same pattern.
    """

    cfg = gains or ExplicitControlGains()
    q = np.asarray(pose, dtype=float)
    qd = np.asarray(twist, dtype=float)
    q_ref = np.asarray(target_pose, dtype=float)
    qd_ref = np.zeros(3, dtype=float) if target_twist is None else np.asarray(target_twist, dtype=float)
    qdd_ref = np.zeros(3, dtype=float) if target_acceleration is None else np.asarray(target_acceleration, dtype=float)
    if q.shape != (3,) or qd.shape != (3,) or q_ref.shape != (3,) or qd_ref.shape != (3,) or qdd_ref.shape != (3,):
        raise ValueError("pose, twist, target_pose, target_twist and target_acceleration must be 3D vectors.")

    pos_error = q_ref[:2] - q[:2]
    vel_error = qd_ref[:2] - qd[:2]
    k_p = float(cfg.load_position_bandwidth)
    a_cmd = qdd_ref[:2] + 2.0 * math.sqrt(max(k_p, 0.0)) * vel_error + k_p * pos_error
    if force_limit_sum_n is not None and force_limit_sum_n > 0.0:
        max_accel = float(cfg.acceleration_limit_fraction) * float(force_limit_sum_n) / max(float(mass_total_kg), 1e-9)
        a_cmd = clip_vector(a_cmd, max_accel)

    theta_error = wrap_angle(float(q_ref[2] - q[2]))
    theta_dot_error = float(qd_ref[2] - qd[2])
    k_theta = float(cfg.load_orientation_bandwidth)
    alpha_cmd = float(qdd_ref[2] + 2.0 * math.sqrt(max(k_theta, 0.0)) * theta_dot_error + k_theta * theta_error)

    disturbance = np.zeros(2, dtype=float) if linear_disturbance_n is None else np.asarray(linear_disturbance_n, dtype=float)
    if disturbance.shape != (2,):
        raise ValueError("linear_disturbance_n must be a 2D vector.")
    force = float(mass_total_kg) * a_cmd + disturbance
    tau = float(inertia_total_kgm2) * alpha_cmd + float(angular_disturbance_nm)
    return np.array([force[0], force[1], tau], dtype=float), np.array([a_cmd[0], a_cmd[1], alpha_cmd], dtype=float)


def vgne_force_share(
    wrench_required: np.ndarray,
    offset_world: np.ndarray,
    eta_i: float,
    h_sum: float,
    s_sum: float,
    force_limit_n: float | None = None,
) -> np.ndarray:
    """Closed-form vGNE force share for one AMR contact."""

    wrench = np.asarray(wrench_required, dtype=float)
    r = np.asarray(offset_world, dtype=float)
    if wrench.shape != (3,) or r.shape != (2,):
        raise ValueError("wrench_required must be 3D and offset_world must be 2D.")
    force = float(eta_i) / max(float(h_sum), 1e-9) * wrench[:2]
    force += float(eta_i) / max(float(s_sum), 1e-9) * perp(r) * float(wrench[2])
    if force_limit_n is not None:
        force = clip_vector(force, float(force_limit_n))
    return force


def hand_reference(
    load_pose_ref: np.ndarray,
    load_twist_ref: np.ndarray,
    load_acceleration_ref: np.ndarray,
    slot_offset_body: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rigid reference h_des, h_dot_des, h_ddot_des for a contact slot."""

    q = np.asarray(load_pose_ref, dtype=float)
    qd = np.asarray(load_twist_ref, dtype=float)
    qdd = np.asarray(load_acceleration_ref, dtype=float)
    r_body = np.asarray(slot_offset_body, dtype=float)
    if q.shape != (3,) or qd.shape != (3,) or qdd.shape != (3,) or r_body.shape != (2,):
        raise ValueError("load references must be 3D and slot offset must be 2D.")
    r_world = rotation(float(q[2])) @ r_body
    h_des = q[:2] + r_world
    h_dot_des = qd[:2] + float(qd[2]) * perp(r_world)
    h_ddot_des = qdd[:2] + float(qdd[2]) * perp(r_world) - float(qd[2]) ** 2 * r_world
    return h_des, h_dot_des, h_ddot_des


def nominal_hand_acceleration(
    *,
    hand_xy: np.ndarray,
    hand_velocity_xy: np.ndarray,
    hand_target_xy: np.ndarray,
    hand_target_velocity_xy: np.ndarray,
    hand_target_acceleration_xy: np.ndarray,
    force_share_xy: np.ndarray,
    robot_mass_kg: float,
    gains: ExplicitControlGains | None = None,
) -> np.ndarray:
    """Step-6 hand impedance plus feedforward load-force share."""

    cfg = gains or ExplicitControlGains()
    h = np.asarray(hand_xy, dtype=float)
    h_dot = np.asarray(hand_velocity_xy, dtype=float)
    h_ref = np.asarray(hand_target_xy, dtype=float)
    h_dot_ref = np.asarray(hand_target_velocity_xy, dtype=float)
    h_ddot_ref = np.asarray(hand_target_acceleration_xy, dtype=float)
    share = np.asarray(force_share_xy, dtype=float)
    for name, value in {
        "hand_xy": h,
        "hand_velocity_xy": h_dot,
        "hand_target_xy": h_ref,
        "hand_target_velocity_xy": h_dot_ref,
        "hand_target_acceleration_xy": h_ddot_ref,
        "force_share_xy": share,
    }.items():
        if value.shape != (2,):
            raise ValueError(f"{name} must be a 2D vector.")
    k_h = float(cfg.hand_position_bandwidth)
    accel = h_ddot_ref + 2.0 * math.sqrt(max(k_h, 0.0)) * (h_dot_ref - h_dot) + k_h * (h_ref - h)
    accel += share / max(float(robot_mass_kg), 1e-9)
    return clip_vector(accel, float(cfg.max_hand_acceleration))


def closed_form_hocbf_projection(
    nominal_acceleration_xy: np.ndarray,
    hand_xy: np.ndarray,
    hand_velocity_xy: np.ndarray,
    hazards: Iterable[CircularHazard],
    safety_distance_m: float,
    *,
    gains: ExplicitControlGains | None = None,
    passes: int = 5,
    hazard_acceleration_bound: float = 0.0,
) -> np.ndarray:
    """Sequential closed-form projection over HOCBF half-spaces.

    Each hazard produces a half-space a^T w >= b for the hand acceleration.
    The update is the Euclidean projection onto violated half-spaces.
    """

    cfg = gains or ExplicitControlGains()
    w = np.asarray(nominal_acceleration_xy, dtype=float).copy()
    h_pos = np.asarray(hand_xy, dtype=float)
    h_vel = np.asarray(hand_velocity_xy, dtype=float)
    if w.shape != (2,) or h_pos.shape != (2,) or h_vel.shape != (2,):
        raise ValueError("accelerations, hand position and hand velocity must be 2D vectors.")
    for _ in range(max(int(passes), 1)):
        changed = False
        for hazard in hazards:
            delta_p = h_pos - hazard.center_xy
            delta_v = h_vel - hazard.velocity_xy
            dist = float(np.linalg.norm(delta_p))
            if dist <= 1e-9:
                delta_p = np.array([1.0, 0.0], dtype=float)
                dist = 1.0
            safe_distance = float(safety_distance_m) + float(hazard.radius_m)
            h_value = dist * dist - safe_distance * safe_distance
            h_dot = 2.0 * float(np.dot(delta_p, delta_v))
            a = 2.0 * delta_p
            b = -2.0 * float(np.dot(delta_v, delta_v)) - (float(cfg.safety_k1) + float(cfg.safety_k2)) * h_dot - float(cfg.safety_k1) * float(cfg.safety_k2) * h_value
            b += 2.0 * dist * max(float(hazard_acceleration_bound), 0.0)
            if hazard.cooperative:
                b *= 0.5
            violation = b - float(np.dot(a, w))
            if violation > 0.0:
                w += violation / max(float(np.dot(a, a)), 1e-9) * a
                changed = True
        if not changed:
            break
    return w


def inverse_unicycle_dynamics(
    safe_hand_acceleration_xy: np.ndarray,
    theta: float,
    linear_speed: float,
    angular_speed: float,
    *,
    mass_kg: float,
    inertia_kgm2: float,
    linear_friction: float,
    angular_friction: float,
    lookahead_m: float,
) -> tuple[float, float]:
    """Map hand acceleration to actuator force and yaw torque."""

    w = np.asarray(safe_hand_acceleration_xy, dtype=float)
    if w.shape != (2,):
        raise ValueError("safe_hand_acceleration_xy must be a 2D vector.")
    e = unit_heading(theta)
    e_perp = perp(e)
    w_e = float(np.dot(e, w))
    w_perp = float(np.dot(e_perp, w))
    force = float(mass_kg) * (w_e + float(lookahead_m) * float(angular_speed) ** 2) + float(linear_friction) * float(linear_speed)
    torque = float(inertia_kgm2) / max(float(lookahead_m), 1e-9) * (w_perp - float(linear_speed) * float(angular_speed)) + float(angular_friction) * float(angular_speed)
    return force, torque


def saturate_force_torque(
    force_n: float,
    torque_nm: float,
    *,
    force_limit_n: float,
    torque_limit_nm: float,
) -> tuple[float, float, float]:
    """Uniform saturation that preserves the commanded direction."""

    sigma = min(
        1.0,
        float(force_limit_n) / max(abs(float(force_n)), 1e-9),
        float(torque_limit_nm) / max(abs(float(torque_nm)), 1e-9),
    )
    return sigma * float(force_n), sigma * float(torque_nm), sigma


def clip_vector(vector: np.ndarray, limit: float) -> np.ndarray:
    """Clip vector norm while preserving direction."""

    out = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(out))
    if norm > max(float(limit), 1e-9):
        return out / norm * float(limit)
    return out.copy()
