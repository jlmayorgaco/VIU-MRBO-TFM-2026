"""Auditable N1 kinematics for a supported load on passive-yaw pivots."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


_J = np.asarray([[0.0, -1.0], [1.0, 0.0]])


@dataclass(frozen=True, slots=True)
class DifferentialDrive:
    """Differential-drive geometry and actuator limits in SI units."""

    robot_id: str
    wheel_radius_m: float
    track_width_m: float
    max_wheel_speed_rad_s: float

    def __post_init__(self) -> None:
        if min(
            self.wheel_radius_m,
            self.track_width_m,
            self.max_wheel_speed_rad_s,
        ) <= 0.0:
            raise ValueError("drive parameters must be strictly positive")


@dataclass(frozen=True, slots=True)
class RobotKinematicCertificate:
    robot_id: str
    feasible: bool
    mode: str
    anchor_speed_mps: float
    aligned_heading_rad: float | None
    heading_rate_rad_s: float | None
    left_wheel_speed_rad_s: float
    right_wheel_speed_rad_s: float
    utilization: float
    margin: float
    limiting_wheel: str
    reason: str


@dataclass(frozen=True, slots=True)
class FormationCertificate:
    feasible: bool
    robots: tuple[RobotKinematicCertificate, ...]
    limiting_robot_id: str
    limiting_wheel: str
    max_utilization: float
    margin: float
    reason: str


def _as_vector(values: np.ndarray, size: int, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (size,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be a finite vector with shape ({size},)")
    return vector


def anchor_kinematics(
    twist: np.ndarray,
    twist_rate: np.ndarray,
    offset_body_m: np.ndarray,
    *,
    payload_yaw_rad: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return pivot velocity and acceleration in the world frame.

    The load twist is [vx, vy, omega] and its derivative is [ax, ay, alpha].
    The offset is fixed in the load frame, so acceleration includes the
    centripetal term -omega squared times r.
    """

    xi = _as_vector(twist, 3, "twist")
    xidot = _as_vector(twist_rate, 3, "twist_rate")
    offset = _as_vector(offset_body_m, 2, "offset_body_m")
    c, s = np.cos(float(payload_yaw_rad)), np.sin(float(payload_yaw_rad))
    rotation = np.asarray([[c, -s], [s, c]])
    radius_world = rotation @ offset
    velocity = xi[:2] + xi[2] * (_J @ radius_world)
    acceleration = (
        xidot[:2]
        + xidot[2] * (_J @ radius_world)
        - xi[2] ** 2 * radius_world
    )
    return velocity, acceleration


def _certify_robot(
    drive: DifferentialDrive,
    velocity: np.ndarray,
    acceleration: np.ndarray,
    *,
    speed_guard_mps: float,
    tolerance: float,
) -> RobotKinematicCertificate:
    speed = float(np.linalg.norm(velocity))
    if speed < speed_guard_mps:
        stationary = float(np.linalg.norm(acceleration)) <= tolerance
        if stationary:
            heading = None
            mode = "hold"
            reason = "stationary pivot"
        else:
            heading = float(np.arctan2(acceleration[1], acceleration[0]))
            mode = "reorient_then_track"
            reason = "heading selected from the nonzero acceleration before departure"
        return RobotKinematicCertificate(
            robot_id=drive.robot_id,
            feasible=True,
            mode=mode,
            anchor_speed_mps=speed,
            aligned_heading_rad=heading,
            heading_rate_rad_s=0.0,
            left_wheel_speed_rad_s=0.0,
            right_wheel_speed_rad_s=0.0,
            utilization=0.0,
            margin=1.0,
            limiting_wheel="none",
            reason=reason,
        )

    heading = float(np.arctan2(velocity[1], velocity[0]))
    heading_rate = float(
        (velocity[0] * acceleration[1] - velocity[1] * acceleration[0])
        / (speed * speed)
    )
    left = (
        speed - 0.5 * drive.track_width_m * heading_rate
    ) / drive.wheel_radius_m
    right = (
        speed + 0.5 * drive.track_width_m * heading_rate
    ) / drive.wheel_radius_m
    utilization = max(abs(left), abs(right)) / drive.max_wheel_speed_rad_s
    limiting_wheel = "left" if abs(left) >= abs(right) else "right"
    feasible = utilization <= 1.0 + tolerance
    return RobotKinematicCertificate(
        robot_id=drive.robot_id,
        feasible=feasible,
        mode="track",
        anchor_speed_mps=speed,
        aligned_heading_rad=heading,
        heading_rate_rad_s=heading_rate,
        left_wheel_speed_rad_s=float(left),
        right_wheel_speed_rad_s=float(right),
        utilization=float(utilization),
        margin=float(1.0 - utilization),
        limiting_wheel=limiting_wheel,
        reason="within wheel limits" if feasible else "wheel-speed limit exceeded",
    )


def certify_formation_twist(
    drives: list[DifferentialDrive] | tuple[DifferentialDrive, ...],
    offsets_body_m: np.ndarray,
    twist: np.ndarray,
    twist_rate: np.ndarray | None = None,
    *,
    payload_yaw_rad: float = 0.0,
    speed_guard_mps: float = 1e-3,
    tolerance: float = 1e-9,
) -> FormationCertificate:
    """Certify the aligned tracking branch for every robot in a formation."""

    offsets = np.asarray(offsets_body_m, dtype=float)
    if offsets.shape != (len(drives), 2):
        raise ValueError("offsets_body_m must have shape (n_robots, 2)")
    rate = (
        np.zeros(3)
        if twist_rate is None
        else _as_vector(twist_rate, 3, "twist_rate")
    )
    certificates: list[RobotKinematicCertificate] = []
    for drive, offset in zip(drives, offsets, strict=True):
        velocity, acceleration = anchor_kinematics(
            twist,
            rate,
            offset,
            payload_yaw_rad=payload_yaw_rad,
        )
        certificates.append(
            _certify_robot(
                drive,
                velocity,
                acceleration,
                speed_guard_mps=speed_guard_mps,
                tolerance=tolerance,
            )
        )
    limiting = max(certificates, key=lambda item: item.utilization)
    feasible = all(item.feasible for item in certificates)
    reason = (
        "joint aligned certificate passed"
        if feasible
        else f"{limiting.robot_id}: {limiting.reason}"
    )
    return FormationCertificate(
        feasible=feasible,
        robots=tuple(certificates),
        limiting_robot_id=limiting.robot_id,
        limiting_wheel=limiting.limiting_wheel,
        max_utilization=float(limiting.utilization),
        margin=float(1.0 - limiting.utilization),
        reason=reason,
    )


def independent_speed_only_feasible(
    drives: list[DifferentialDrive] | tuple[DifferentialDrive, ...],
    offsets_body_m: np.ndarray,
    twist: np.ndarray,
    *,
    payload_yaw_rad: float = 0.0,
    tolerance: float = 1e-9,
) -> bool:
    """Naive baseline that ignores heading rate and the wheel-speed split."""

    offsets = np.asarray(offsets_body_m, dtype=float)
    for drive, offset in zip(drives, offsets, strict=True):
        velocity, _ = anchor_kinematics(
            twist,
            np.zeros(3),
            offset,
            payload_yaw_rad=payload_yaw_rad,
        )
        speed_limit = drive.wheel_radius_m * drive.max_wheel_speed_rad_s
        if float(np.linalg.norm(velocity)) > speed_limit + tolerance:
            return False
    return True


__all__ = [
    "DifferentialDrive",
    "FormationCertificate",
    "RobotKinematicCertificate",
    "anchor_kinematics",
    "certify_formation_twist",
    "independent_speed_only_feasible",
]
