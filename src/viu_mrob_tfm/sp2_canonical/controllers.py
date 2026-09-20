"""Controller baselines with a common acceleration interface for SP2.N4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from scipy.linalg import solve_continuous_are
from scipy.optimize import lsq_linear


def wrap_angle(value: float) -> float:
    return float((value + np.pi) % (2.0 * np.pi) - np.pi)


def pose_error(target: np.ndarray, pose: np.ndarray) -> np.ndarray:
    error = np.asarray(target, dtype=float) - np.asarray(pose, dtype=float)
    if error.shape != (3,):
        raise ValueError("target and pose must be 3-vectors")
    error[2] = wrap_angle(float(error[2]))
    return error


class AccelerationController(Protocol):
    method: str
    centralized: bool

    def command(
        self,
        pose: np.ndarray,
        twist: np.ndarray,
        target: np.ndarray,
        dt_s: float,
        *,
        governor_scale: float = 1.0,
    ) -> np.ndarray: ...


@dataclass(slots=True)
class PDController:
    kp: np.ndarray = field(default_factory=lambda: np.asarray([1.6, 1.6, 2.2]))
    kd: np.ndarray = field(default_factory=lambda: np.asarray([2.4, 2.4, 2.2]))
    method: str = "pd"
    centralized: bool = False

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        del dt_s, governor_scale
        return self.kp * pose_error(target, pose) - self.kd * np.asarray(twist, dtype=float)


@dataclass(slots=True)
class PIDController:
    kp: np.ndarray = field(default_factory=lambda: np.asarray([1.45, 1.45, 2.0]))
    kd: np.ndarray = field(default_factory=lambda: np.asarray([2.3, 2.3, 2.1]))
    ki: np.ndarray = field(default_factory=lambda: np.asarray([0.12, 0.12, 0.08]))
    integral_limit: np.ndarray = field(default_factory=lambda: np.asarray([1.5, 1.5, 1.0]))
    integral: np.ndarray = field(default_factory=lambda: np.zeros(3))
    method: str = "pid"
    centralized: bool = False

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        error = pose_error(target, pose)
        if governor_scale >= 1.0 - 1e-9:
            self.integral = np.clip(
                self.integral + float(dt_s) * error,
                -self.integral_limit,
                self.integral_limit,
            )
        return self.kp * error - self.kd * np.asarray(twist, dtype=float) + self.ki * self.integral


def _double_integrator_gain(q_position: np.ndarray, q_velocity: np.ndarray, r: np.ndarray) -> np.ndarray:
    zeros = np.zeros((3, 3))
    identity = np.eye(3)
    a = np.block([[zeros, identity], [zeros, zeros]])
    b = np.vstack([zeros, identity])
    q = np.diag(np.concatenate([q_position, q_velocity]))
    solution = solve_continuous_are(a, b, q, np.diag(r))
    return np.linalg.solve(np.diag(r), b.T @ solution)


@dataclass(slots=True)
class LQRController:
    method: str = "lqr"
    centralized: bool = False
    gain: np.ndarray = field(
        default_factory=lambda: _double_integrator_gain(
            np.asarray([8.0, 8.0, 10.0]),
            np.asarray([3.0, 3.0, 3.0]),
            np.asarray([1.0, 1.0, 1.0]),
        )
    )

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        del dt_s, governor_scale
        state = np.concatenate([-pose_error(target, pose), np.asarray(twist, dtype=float)])
        return -self.gain @ state


def _lqi_gain() -> np.ndarray:
    zeros = np.zeros((3, 3))
    identity = np.eye(3)
    a = np.block(
        [
            [zeros, identity, zeros],
            [zeros, zeros, zeros],
            [identity, zeros, zeros],
        ]
    )
    b = np.vstack([zeros, identity, zeros])
    q = np.diag([10.0, 10.0, 12.0, 3.0, 3.0, 3.5, 0.7, 0.7, 0.5])
    r = np.eye(3)
    solution = solve_continuous_are(a, b, q, r)
    return b.T @ solution


@dataclass(slots=True)
class LQIController:
    integral_state: np.ndarray = field(default_factory=lambda: np.zeros(3))
    integral_limit: np.ndarray = field(default_factory=lambda: np.asarray([1.5, 1.5, 1.0]))
    method: str = "lqi"
    centralized: bool = False
    gain: np.ndarray = field(default_factory=_lqi_gain)

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        position_state = -pose_error(target, pose)
        if governor_scale >= 1.0 - 1e-9:
            self.integral_state = np.clip(
                self.integral_state + float(dt_s) * position_state,
                -self.integral_limit,
                self.integral_limit,
            )
        state = np.concatenate([position_state, np.asarray(twist, dtype=float), self.integral_state])
        return -self.gain @ state


@dataclass(slots=True)
class PortHamiltonianController:
    shaped_stiffness: np.ndarray = field(default_factory=lambda: np.asarray([1.9, 1.9, 2.7]))
    damping_injection: np.ndarray = field(default_factory=lambda: np.asarray([2.8, 2.8, 2.6]))
    method: str = "port_hamiltonian"
    centralized: bool = False

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        del dt_s, governor_scale
        gradient_potential = -self.shaped_stiffness * pose_error(target, pose)
        return -gradient_potential - self.damping_injection * np.asarray(twist, dtype=float)


@dataclass(slots=True)
class CentralMPCController:
    horizon_steps: int = 8
    max_acceleration: np.ndarray = field(default_factory=lambda: np.asarray([1.2, 1.2, 1.0]))
    method: str = "mpc_central"
    centralized: bool = True

    def command(self, pose: np.ndarray, twist: np.ndarray, target: np.ndarray, dt_s: float, *, governor_scale: float = 1.0) -> np.ndarray:
        del governor_scale
        dt = float(dt_s)
        position_state = -pose_error(target, pose)
        velocity_state = np.asarray(twist, dtype=float)
        a_axis = np.asarray([[1.0, dt], [0.0, 1.0]])
        b_axis = np.asarray([[0.5 * dt * dt], [dt]])
        a = np.kron(a_axis, np.eye(3))
        b = np.kron(b_axis, np.eye(3))
        state = np.concatenate([position_state, velocity_state])
        state_transition = np.zeros((6 * self.horizon_steps, 6))
        control_transition = np.zeros((6 * self.horizon_steps, 3 * self.horizon_steps))
        for row in range(self.horizon_steps):
            state_transition[6 * row : 6 * (row + 1)] = np.linalg.matrix_power(a, row + 1)
            for column in range(row + 1):
                control_transition[
                    6 * row : 6 * (row + 1), 3 * column : 3 * (column + 1)
                ] = np.linalg.matrix_power(a, row - column) @ b
        q_state = np.diag([8.0, 8.0, 10.0, 2.2, 2.2, 2.6])
        sqrt_q = np.kron(np.eye(self.horizon_steps), np.sqrt(q_state))
        sqrt_r = np.kron(np.eye(self.horizon_steps), np.diag(np.sqrt([0.35, 0.35, 0.4])))
        least_squares_matrix = np.vstack([sqrt_q @ control_transition, sqrt_r])
        least_squares_target = np.concatenate(
            [-sqrt_q @ state_transition @ state, np.zeros(3 * self.horizon_steps)]
        )
        limits = np.tile(self.max_acceleration, self.horizon_steps)
        result = lsq_linear(
            least_squares_matrix,
            least_squares_target,
            bounds=(-limits, limits),
            tol=1e-7,
            lsmr_tol=1e-7,
            max_iter=40,
        )
        return np.asarray(result.x[:3])


def make_controller(method: str) -> AccelerationController:
    constructors = {
        "pd": PDController,
        "pid": PIDController,
        "lqr": LQRController,
        "lqi": LQIController,
        "port_hamiltonian": PortHamiltonianController,
        "mpc_central": CentralMPCController,
    }
    if method not in constructors:
        raise ValueError(f"unknown controller: {method}")
    return constructors[method]()


def cbf_acceleration_filter(
    pose: np.ndarray,
    twist: np.ndarray,
    acceleration: np.ndarray,
    obstacles: list[tuple[np.ndarray, float]],
    *,
    body_radius_m: float,
    safety_margin_m: float,
    alpha0: float = 2.0,
    alpha1: float = 2.5,
) -> tuple[np.ndarray, float]:
    """Project translational acceleration onto sampled relative-degree-two CBF halfspaces."""

    filtered = np.asarray(acceleration, dtype=float).copy()
    maximum_intervention = 0.0
    for center, radius in obstacles:
        delta = np.asarray(pose[:2], dtype=float) - np.asarray(center, dtype=float)
        distance = float(np.linalg.norm(delta))
        normal = delta / max(distance, 1e-9)
        h = distance - body_radius_m - float(radius) - safety_margin_m
        radial_velocity = float(np.dot(normal, np.asarray(twist[:2], dtype=float)))
        lower_bound = -alpha1 * radial_velocity - alpha0 * h
        achieved = float(np.dot(normal, filtered[:2]))
        if achieved < lower_bound:
            correction = (lower_bound - achieved) * normal
            filtered[:2] += correction
            maximum_intervention = max(maximum_intervention, float(np.linalg.norm(correction)))
    return filtered, maximum_intervention


__all__ = [
    "AccelerationController",
    "CentralMPCController",
    "LQIController",
    "LQRController",
    "PDController",
    "PIDController",
    "PortHamiltonianController",
    "cbf_acceleration_filter",
    "make_controller",
    "pose_error",
    "wrap_angle",
]
