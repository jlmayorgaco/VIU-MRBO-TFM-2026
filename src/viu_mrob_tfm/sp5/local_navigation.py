"""Local continuous navigation law used by the AWS TFM demonstrator.

The mathematical command is a continuous goal field combined with a small
replicator population over left/right/wait motion primitives.  A SP5-style
cyclic projection filters the resulting velocity through locally observed
CBF half-spaces.  The returned ``EXEC`` velocity additionally includes the
sampled acceleration bound, so callers can audit RAW--SAFE--EXEC separately.

This module deliberately does not claim that forward-Euler execution inherits
continuous-time CBF invariance.  That property must be checked on the sampled
trajectory produced by an experiment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class BarrierConstraint:
    """Velocity half-space ``normal @ velocity + gamma * h >= 0``."""

    normal: np.ndarray
    h: float
    label: str


@dataclass(frozen=True)
class ContinuousNavigationStep:
    position: np.ndarray
    preference: np.ndarray
    raw_velocity: np.ndarray
    safe_velocity: np.ndarray
    exec_velocity: np.ndarray
    raw_residual: float
    safe_residual: float
    exec_residual: float
    projection_interventions: int
    active_constraints: int


def _signed_aabb_constraint(
    position: np.ndarray,
    center: np.ndarray,
    obstacle_half_extent: np.ndarray,
    body_half_extent: np.ndarray,
    clearance_m: float,
    label: str,
) -> BarrierConstraint:
    """Return signed clearance and an outward normal for a Minkowski AABB."""

    expanded = obstacle_half_extent + body_half_extent + float(clearance_m)
    local = position - center
    outside = np.maximum(np.abs(local) - expanded, 0.0)
    outside_distance = float(np.linalg.norm(outside))
    if outside_distance > 1.0e-12:
        closest = np.clip(local, -expanded, expanded)
        delta = local - closest
        normal = delta / outside_distance
        return BarrierConstraint(normal=normal, h=outside_distance, label=label)

    # The point is inside the expanded obstacle.  Choose the nearest exit face
    # and retain a negative signed clearance so the projection points outward.
    face_clearance = expanded - np.abs(local)
    axis = int(np.argmin(face_clearance))
    normal = np.zeros(2, dtype=float)
    normal[axis] = 1.0 if local[axis] >= 0.0 else -1.0
    return BarrierConstraint(normal=normal, h=-float(face_clearance[axis]), label=label)


def local_barrier_constraints(
    position: Sequence[float],
    body_half_extent: Sequence[float],
    static_rectangles: Iterable[tuple[float, float, float, float, str]],
    dynamic_obstacles: Iterable[tuple[Sequence[float], Sequence[float], str]],
    world_half_extent: Sequence[float],
    *,
    sensing_radius_m: float,
    static_clearance_m: float,
    dynamic_clearance_m: float,
) -> list[BarrierConstraint]:
    """Build locally sensed obstacle constraints plus always-known map bounds."""

    q = np.asarray(position, dtype=float)
    body = np.asarray(body_half_extent, dtype=float)
    world_half = np.asarray(world_half_extent, dtype=float)
    if q.shape != (2,) or body.shape != (2,) or world_half.shape != (2,):
        raise ValueError("position and half extents must be planar vectors")
    if not np.isfinite(q).all() or not np.isfinite(body).all() or np.any(body <= 0.0):
        raise ValueError("navigation geometry must be finite with positive body extent")

    constraints: list[BarrierConstraint] = []
    for xmin, xmax, ymin, ymax, label in static_rectangles:
        center = np.asarray([(xmin + xmax) / 2.0, (ymin + ymax) / 2.0], dtype=float)
        half = np.asarray([(xmax - xmin) / 2.0, (ymax - ymin) / 2.0], dtype=float)
        constraint = _signed_aabb_constraint(q, center, half, body, static_clearance_m, str(label))
        if constraint.h <= sensing_radius_m:
            constraints.append(constraint)
    for center, half, label in dynamic_obstacles:
        constraint = _signed_aabb_constraint(
            q,
            np.asarray(center, dtype=float),
            np.asarray(half, dtype=float),
            body,
            dynamic_clearance_m,
            str(label),
        )
        if constraint.h <= sensing_radius_m:
            constraints.append(constraint)

    usable = world_half - body - float(static_clearance_m)
    constraints.extend(
        [
            BarrierConstraint(np.asarray([1.0, 0.0]), float(usable[0] + q[0]), "wall_xmin"),
            BarrierConstraint(np.asarray([-1.0, 0.0]), float(usable[0] - q[0]), "wall_xmax"),
            BarrierConstraint(np.asarray([0.0, 1.0]), float(usable[1] + q[1]), "wall_ymin"),
            BarrierConstraint(np.asarray([0.0, -1.0]), float(usable[1] - q[1]), "wall_ymax"),
        ]
    )
    return constraints


def barrier_residual(
    constraints: Iterable[BarrierConstraint], velocity: Sequence[float], *, gamma: float
) -> float:
    v = np.asarray(velocity, dtype=float)
    values = [-float(constraint.normal @ v) - float(gamma) * constraint.h for constraint in constraints]
    return max([0.0, *values])


def _project_simplex(values: np.ndarray) -> np.ndarray:
    clipped = np.maximum(np.asarray(values, dtype=float), 1.0e-12)
    return clipped / float(np.sum(clipped))


def continuous_navigation_step(
    position: Sequence[float],
    goal: Sequence[float],
    current_velocity: Sequence[float],
    preference: Sequence[float],
    constraints: Sequence[BarrierConstraint],
    *,
    dt_s: float,
    max_speed_mps: float,
    max_accel_mps2: float,
    goal_gain: float,
    barrier_gamma: float,
    projection_sweeps: int,
    replicator_gain: float,
    mutation_rate: float,
    tangent_gain: float,
    activation_clearance_m: float,
    preview_s: float,
) -> ContinuousNavigationStep:
    """Advance one sampled execution of the continuous TFM navigation law."""

    q = np.asarray(position, dtype=float)
    target = np.asarray(goal, dtype=float)
    previous_velocity = np.asarray(current_velocity, dtype=float)
    rho = _project_simplex(np.asarray(preference, dtype=float))
    if q.shape != (2,) or target.shape != (2,) or previous_velocity.shape != (2,) or rho.shape != (3,):
        raise ValueError("expected planar state and a three-action population")
    scalars = (dt_s, max_speed_mps, max_accel_mps2, goal_gain, barrier_gamma, preview_s)
    if not all(np.isfinite(value) and value > 0.0 for value in scalars):
        raise ValueError("navigation time, gains and bounds must be finite and positive")

    error = target - q
    goal_distance = float(np.linalg.norm(error))
    if goal_distance <= 1.0e-12:
        nominal = np.zeros(2, dtype=float)
    else:
        nominal_speed = max_speed_mps * np.tanh(goal_gain * goal_distance / max(max_speed_mps, 1.0e-12))
        nominal = nominal_speed * error / goal_distance

    nearest = min(constraints, key=lambda row: row.h, default=None)
    tangent = np.zeros(2, dtype=float)
    influence = 0.0
    if nearest is not None and nearest.h < activation_clearance_m:
        tangent = np.asarray([-nearest.normal[1], nearest.normal[0]], dtype=float)
        influence = float(np.clip((activation_clearance_m - nearest.h) / activation_clearance_m, 0.0, 2.0))
    candidates = np.vstack(
        [
            nominal + tangent_gain * max_speed_mps * influence * tangent,
            nominal - tangent_gain * max_speed_mps * influence * tangent,
            np.zeros(2, dtype=float),
        ]
    )
    for index in range(2):
        norm = float(np.linalg.norm(candidates[index]))
        if norm > max_speed_mps:
            candidates[index] *= max_speed_mps / norm

    costs = np.zeros(3, dtype=float)
    for index, candidate in enumerate(candidates):
        predicted = q + preview_s * candidate
        costs[index] = float(np.linalg.norm(target - predicted)) + 0.025 * float(candidate @ candidate)
        for constraint in constraints:
            predicted_h = constraint.h + preview_s * float(constraint.normal @ candidate)
            costs[index] += 2.4 * max(0.0, activation_clearance_m - predicted_h) ** 2
        if index == 2 and goal_distance > 0.10:
            # SP4 liveness cost: waiting remains available for negotiation but
            # becomes increasingly unattractive while the goal is still far.
            costs[index] += 0.65 * min(goal_distance, 3.0)

    payoffs = -costs
    mean_payoff = float(rho @ payoffs)
    rho_dot = replicator_gain * rho * (payoffs - mean_payoff) + mutation_rate * (1.0 / 3.0 - rho)
    next_rho = _project_simplex(rho + dt_s * rho_dot)
    raw_velocity = next_rho @ candidates
    raw_residual = barrier_residual(constraints, raw_velocity, gamma=barrier_gamma)

    safe_velocity = raw_velocity.copy()
    interventions = 0
    for _ in range(max(int(projection_sweeps), 1)):
        changed = False
        for constraint in constraints:
            deficit = -float(constraint.normal @ safe_velocity) - barrier_gamma * constraint.h
            if deficit > 0.0:
                safe_velocity += deficit * constraint.normal / max(
                    float(constraint.normal @ constraint.normal), 1.0e-12
                )
                changed = True
                interventions += 1
        norm = float(np.linalg.norm(safe_velocity))
        if norm > max_speed_mps:
            safe_velocity *= max_speed_mps / norm
        if not changed:
            break
    safe_residual = barrier_residual(constraints, safe_velocity, gamma=barrier_gamma)

    delta_velocity = safe_velocity - previous_velocity
    delta_norm = float(np.linalg.norm(delta_velocity))
    max_delta = max_accel_mps2 * dt_s
    if delta_norm > max_delta:
        exec_velocity = previous_velocity + delta_velocity * (max_delta / delta_norm)
    else:
        exec_velocity = safe_velocity.copy()
    exec_norm = float(np.linalg.norm(exec_velocity))
    if exec_norm > max_speed_mps:
        exec_velocity *= max_speed_mps / exec_norm
    exec_residual = barrier_residual(constraints, exec_velocity, gamma=barrier_gamma)

    return ContinuousNavigationStep(
        position=q + dt_s * exec_velocity,
        preference=next_rho,
        raw_velocity=raw_velocity,
        safe_velocity=safe_velocity,
        exec_velocity=exec_velocity,
        raw_residual=raw_residual,
        safe_residual=safe_residual,
        exec_residual=exec_residual,
        projection_interventions=interventions,
        active_constraints=sum(constraint.h < activation_clearance_m for constraint in constraints),
    )


def predictive_navigation_step(
    position: Sequence[float],
    goal: Sequence[float],
    current_velocity: Sequence[float],
    preference: Sequence[float],
    constraints: Sequence[BarrierConstraint],
    *,
    dt_s: float,
    max_speed_mps: float,
    max_accel_mps2: float,
    goal_gain: float,
    barrier_gamma: float,
    projection_sweeps: int,
    horizon_s: float,
    heading_samples: int,
    clearance_weight: float,
    effort_weight: float,
    wait_cost: float,
    lateral_bias: float = 0.0,
) -> ContinuousNavigationStep:
    """Velocity-sampling predictive proxy followed by the common CBF filter.

    This is deliberately named a proxy: it does not solve a nonlinear MPC
    program and does not reproduce ORCA velocity obstacles.  It provides a
    finite-horizon, auditable comparator while those baselines are integrated.
    """

    q = np.asarray(position, dtype=float)
    target = np.asarray(goal, dtype=float)
    previous_velocity = np.asarray(current_velocity, dtype=float)
    rho = _project_simplex(np.asarray(preference, dtype=float))
    if q.shape != (2,) or target.shape != (2,) or previous_velocity.shape != (2,) or rho.shape != (3,):
        raise ValueError("expected planar state and a three-action diagnostic population")
    scalars = (
        dt_s,
        max_speed_mps,
        max_accel_mps2,
        goal_gain,
        barrier_gamma,
        horizon_s,
        clearance_weight,
        effort_weight,
        wait_cost,
    )
    if not all(np.isfinite(value) and value >= 0.0 for value in scalars):
        raise ValueError("predictive navigation parameters must be finite and nonnegative")
    if min(dt_s, max_speed_mps, max_accel_mps2, goal_gain, barrier_gamma, horizon_s) <= 0.0:
        raise ValueError("time, bounds and control gains must be strictly positive")
    error = target - q
    distance = float(np.linalg.norm(error))
    if distance <= 1.0e-12:
        goal_heading = 0.0
        nominal_speed = 0.0
    else:
        goal_heading = float(np.arctan2(error[1], error[0]))
        nominal_speed = max_speed_mps * np.tanh(goal_gain * distance / max(max_speed_mps, 1.0e-12))
    samples = max(3, int(heading_samples))
    offsets = np.linspace(-0.75 * np.pi, 0.75 * np.pi, samples)
    speeds = (nominal_speed, 0.72 * nominal_speed)
    candidates = [
        speed * np.asarray([np.cos(goal_heading + offset), np.sin(goal_heading + offset)], dtype=float)
        for speed in speeds
        for offset in offsets
    ]
    candidates.append(np.zeros(2, dtype=float))
    costs = []
    for candidate in candidates:
        predicted = q + horizon_s * candidate
        cost = float(np.linalg.norm(target - predicted)) + effort_weight * float(candidate @ candidate)
        for constraint in constraints:
            predicted_h = constraint.h + horizon_s * float(constraint.normal @ candidate)
            cost += clearance_weight * max(0.0, 0.55 - predicted_h) ** 2
            tangent = np.asarray([-constraint.normal[1], constraint.normal[0]], dtype=float)
            cost -= lateral_bias * float(tangent @ candidate) * np.exp(-max(constraint.h, 0.0))
        if float(np.linalg.norm(candidate)) <= 1.0e-12 and distance > 0.10:
            cost += wait_cost * min(distance, 3.0)
        costs.append(cost)
    selected = int(np.argmin(np.asarray(costs, dtype=float)))
    raw_velocity = np.asarray(candidates[selected], dtype=float)
    raw_residual = barrier_residual(constraints, raw_velocity, gamma=barrier_gamma)

    safe_velocity = raw_velocity.copy()
    interventions = 0
    for _ in range(max(int(projection_sweeps), 1)):
        changed = False
        for constraint in constraints:
            deficit = -float(constraint.normal @ safe_velocity) - barrier_gamma * constraint.h
            if deficit > 0.0:
                safe_velocity += deficit * constraint.normal / max(
                    float(constraint.normal @ constraint.normal), 1.0e-12
                )
                changed = True
                interventions += 1
        norm = float(np.linalg.norm(safe_velocity))
        if norm > max_speed_mps:
            safe_velocity *= max_speed_mps / norm
        if not changed:
            break
    safe_residual = barrier_residual(constraints, safe_velocity, gamma=barrier_gamma)

    delta = safe_velocity - previous_velocity
    delta_norm = float(np.linalg.norm(delta))
    max_delta = max_accel_mps2 * dt_s
    exec_velocity = (
        previous_velocity + delta * (max_delta / delta_norm)
        if delta_norm > max_delta
        else safe_velocity.copy()
    )
    exec_norm = float(np.linalg.norm(exec_velocity))
    if exec_norm > max_speed_mps:
        exec_velocity *= max_speed_mps / exec_norm
    exec_residual = barrier_residual(constraints, exec_velocity, gamma=barrier_gamma)
    diagnostic_preference = np.zeros(3, dtype=float)
    diagnostic_preference[0 if selected < samples else 1 if selected < 2 * samples else 2] = 1.0
    return ContinuousNavigationStep(
        position=q + dt_s * exec_velocity,
        preference=diagnostic_preference,
        raw_velocity=raw_velocity,
        safe_velocity=safe_velocity,
        exec_velocity=exec_velocity,
        raw_residual=raw_residual,
        safe_residual=safe_residual,
        exec_residual=exec_residual,
        projection_interventions=interventions,
        active_constraints=sum(constraint.h < 0.75 for constraint in constraints),
    )


__all__ = [
    "BarrierConstraint",
    "ContinuousNavigationStep",
    "barrier_residual",
    "continuous_navigation_step",
    "local_barrier_constraints",
    "predictive_navigation_step",
]
