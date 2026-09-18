"""White-box Cargo control from payload pose to wheel-speed commands.

The three preregistered guards predict feasibility only. Every physical run
uses this same chain: pose PD, rigid-body wrench demand, bounded contact-force
allocation, wrench-error admittance, and differential-drive inverse
kinematics. The allocation is a setpoint for the velocity-controlled contact
branches; it is never reported as an exactly realized physical wrench.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import lsq_linear

from viu_mrob_tfm.sp2_canonical.dynamics import PlanarPayload, required_wrench_body
from viu_mrob_tfm.sp2_canonical.mechanics import grasp_matrix_2d

from .config import CampaignConfig
from .design import WorldSpec


def wrap_angle(value: float) -> float:
    return float((value + np.pi) % (2.0 * np.pi) - np.pi)


def _finite_array(value: np.ndarray, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}, received {array.shape}")
    if not np.isfinite(array.astype(float, copy=False)).all():
        raise FloatingPointError(f"{name} must contain only finite values")
    return array


@dataclass(frozen=True, slots=True)
class Observation:
    """One synchronous sample; all physical quantities use SI units."""

    time_s: float
    payload_pose_m_rad: np.ndarray
    payload_twist_m_s_rad_s: np.ndarray
    robot_pose_m_rad: np.ndarray
    wheel_speed_rad_s: np.ndarray
    wheel_drive_force_n: np.ndarray
    measured_wrench_body: np.ndarray
    normal_force_n: np.ndarray
    contact_active: np.ndarray
    active_robot_mask: np.ndarray
    relative_slip_m: np.ndarray
    collision_count: int

    def __post_init__(self) -> None:
        robot_pose = np.asarray(self.robot_pose_m_rad)
        if robot_pose.ndim != 2 or robot_pose.shape[1:] != (3,):
            raise ValueError("robot_pose_m_rad must have shape (n_robots, 3)")
        robot_count = robot_pose.shape[0]
        _finite_array(self.payload_pose_m_rad, (3,), "payload_pose_m_rad")
        _finite_array(
            self.payload_twist_m_s_rad_s,
            (3,),
            "payload_twist_m_s_rad_s",
        )
        _finite_array(robot_pose, (robot_count, 3), "robot_pose_m_rad")
        _finite_array(
            self.wheel_speed_rad_s,
            (robot_count, 2),
            "wheel_speed_rad_s",
        )
        _finite_array(
            self.wheel_drive_force_n,
            (robot_count, 2),
            "wheel_drive_force_n",
        )
        _finite_array(self.measured_wrench_body, (3,), "measured_wrench_body")
        _finite_array(self.normal_force_n, (robot_count,), "normal_force_n")
        _finite_array(self.contact_active, (robot_count,), "contact_active")
        _finite_array(
            self.active_robot_mask,
            (robot_count,),
            "active_robot_mask",
        )
        _finite_array(self.relative_slip_m, (robot_count,), "relative_slip_m")
        if not np.isfinite(float(self.time_s)) or self.time_s < 0.0:
            raise ValueError("time_s must be finite and non-negative")
        if int(self.collision_count) != self.collision_count or self.collision_count < 0:
            raise ValueError("collision_count must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ContactAllocation:
    """Bounded planar contact-force setpoint and honest residual diagnostics."""

    force_setpoint_body_n: np.ndarray
    contact_force_limit_n: np.ndarray
    achieved_wrench_body: np.ndarray
    residual_body: np.ndarray
    residual_normalized: float
    utilization: float
    saturation_count: int
    solver_success: bool


@dataclass(frozen=True, slots=True)
class WheelCommand:
    wheel_speed_rad_s: np.ndarray
    desired_acceleration_world_m_s2_rad_s2: np.ndarray
    reference_wrench_body: np.ndarray
    contact_force_setpoint_body_n: np.ndarray
    contact_force_limit_n: np.ndarray
    allocated_wrench_body: np.ndarray
    allocation_residual_body: np.ndarray
    allocation_residual_normalized: float
    allocation_utilization: float
    allocation_saturation_count: int
    wheel_saturation_count: int
    admittance_twist_body_m_s_rad_s: np.ndarray
    allocation_solver_success: bool
    saturation_count: int
    controller_id: str


def _wrench_normalization(
    config: CampaignConfig, world: WorldSpec
) -> np.ndarray:
    force_scale = max(
        world.active_robot_count * config.robot.max_drive_force_n,
        1.0,
    )
    offsets = np.asarray(world.contact_offsets_body_m, dtype=float)
    radius_scale = max(float(np.max(np.linalg.norm(offsets, axis=1))), 0.1)
    torque_scale = max(force_scale * radius_scale, 1.0)
    return np.diag([1.0 / force_scale, 1.0 / force_scale, 1.0 / torque_scale])


def allocate_contact_wrench(
    config: CampaignConfig,
    world: WorldSpec,
    observation: Observation,
    desired_wrench_body: np.ndarray,
) -> ContactAllocation:
    """Solve a regularized, bounded LSQ allocation in the payload frame.

    Each contact uses an inscribed square with half-width
    ``min(F_drive, mu*N)/sqrt(2)``. Thus the Euclidean tangential-force norm
    cannot exceed either the measured Coulomb limit or the declared drive
    limit. Lost/inactive contacts receive exactly zero setpoint.
    """

    robot_count = config.robot.count
    desired = _finite_array(
        np.asarray(desired_wrench_body, dtype=float),
        (3,),
        "desired_wrench_body",
    ).astype(float, copy=False)
    if len(world.contact_offsets_body_m) != world.active_robot_count:
        raise ValueError("world contact offsets must match active_robot_count")
    expected_active = np.arange(robot_count) < world.active_robot_count
    observed_active = np.asarray(observation.active_robot_mask, dtype=bool)
    if not np.array_equal(observed_active, expected_active):
        raise ValueError("observation active mask does not match the frozen world")

    contact = np.asarray(observation.contact_active, dtype=bool)
    normal = np.maximum(np.asarray(observation.normal_force_n, dtype=float), 0.0)
    radial_limits = np.zeros(robot_count, dtype=float)
    radial_limits[expected_active] = np.minimum(
        config.robot.max_drive_force_n,
        world.actual_friction_coefficient * normal[expected_active],
    )
    eligible = expected_active & contact & (radial_limits > 1.0e-12)
    selected = np.flatnonzero(eligible)
    force_setpoint = np.zeros((robot_count, 2), dtype=float)
    normalization = _wrench_normalization(config, world)
    if not len(selected):
        residual = -desired
        return ContactAllocation(
            force_setpoint_body_n=force_setpoint,
            contact_force_limit_n=radial_limits,
            achieved_wrench_body=np.zeros(3),
            residual_body=residual,
            residual_normalized=float(np.linalg.norm(normalization @ residual)),
            utilization=0.0,
            saturation_count=0,
            solver_success=False,
        )

    offsets = np.asarray(world.contact_offsets_body_m, dtype=float)[selected]
    grasp = grasp_matrix_2d(offsets)
    component_limits = radial_limits[selected] / np.sqrt(2.0)
    repeated_limits = np.repeat(component_limits, 2)
    force_scale = max(config.robot.max_drive_force_n, 1.0)
    regularizer = (
        np.sqrt(config.control.allocation_regularization)
        / force_scale
        * np.eye(2 * len(selected))
    )
    system = np.vstack((normalization @ grasp, regularizer))
    target = np.concatenate((normalization @ desired, np.zeros(2 * len(selected))))
    result = lsq_linear(
        system,
        target,
        bounds=(-repeated_limits, repeated_limits),
        tol=1.0e-12,
        lsmr_tol="auto",
        max_iter=2_000,
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"bounded contact allocation failed: {result.message}")

    selected_forces = np.asarray(result.x, dtype=float).reshape((-1, 2))
    force_setpoint[selected] = selected_forces
    achieved = grasp @ selected_forces.reshape(-1)
    residual = achieved - desired
    utilization = float(
        np.max(
            np.linalg.norm(selected_forces, axis=1)
            / np.maximum(radial_limits[selected], 1.0e-12)
        )
    )
    at_component_bound = np.isclose(
        np.abs(selected_forces),
        component_limits[:, None],
        rtol=1.0e-7,
        atol=1.0e-9,
    )
    return ContactAllocation(
        force_setpoint_body_n=force_setpoint,
        contact_force_limit_n=radial_limits,
        achieved_wrench_body=achieved,
        residual_body=residual,
        residual_normalized=float(np.linalg.norm(normalization @ residual)),
        utilization=utilization,
        saturation_count=int(np.count_nonzero(np.any(at_component_bound, axis=1))),
        solver_success=True,
    )


class CargoPoseController:
    """Map payload pose error to bounded wheel-speed commands.

    The contact allocation influences the velocity-controlled robots through a
    force-to-velocity admittance. Because wheel velocity is the only actuator
    command, the allocated forces remain setpoints. Sensor feedback and the
    recorded residual are needed to assess physical realization.
    """

    def __init__(self, config: CampaignConfig) -> None:
        self.config = config

    def command(
        self,
        world: WorldSpec,
        observation: Observation,
        dt_s: float,
    ) -> WheelCommand:
        if not np.isfinite(float(dt_s)) or dt_s <= 0.0:
            raise ValueError("dt_s must be finite and strictly positive")
        if observation.robot_pose_m_rad.shape != (self.config.robot.count, 3):
            raise ValueError("observation robot count does not match configuration")
        control = self.config.control
        pose_error = (
            np.asarray(world.target_pose_m_rad, dtype=float)
            - np.asarray(observation.payload_pose_m_rad, dtype=float)
        )
        pose_error[2] = wrap_angle(float(pose_error[2]))
        twist = np.asarray(observation.payload_twist_m_s_rad_s, dtype=float)
        acceleration = np.asarray(
            [
                control.position_gain_s2 * pose_error[0]
                - control.velocity_gain_s * twist[0],
                control.position_gain_s2 * pose_error[1]
                - control.velocity_gain_s * twist[1],
                control.yaw_gain_s2 * pose_error[2]
                - control.yaw_rate_gain_s * twist[2],
            ],
            dtype=float,
        )
        peak_acceleration = np.abs(
            np.asarray(world.profile.peak_acceleration_world_m_s2_rad_s2)
        )
        acceleration = np.clip(acceleration, -peak_acceleration, peak_acceleration)
        nominal_twist_world = twist + acceleration * float(dt_s)
        max_twist = np.abs(
            np.asarray(world.profile.peak_twist_world_m_s_rad_s, dtype=float)
        )
        nominal_twist_world = np.clip(
            nominal_twist_world,
            -max_twist,
            max_twist,
        )

        payload = PlanarPayload(
            mass_kg=world.actual_payload_mass_kg,
            yaw_inertia_kg_m2=world.yaw_inertia_kg_m2,
            linear_damping_n_s_m=self.config.payload.linear_damping_n_s_m,
            yaw_damping_n_m_s_rad=self.config.payload.yaw_damping_n_m_s_rad,
        )
        reference_wrench = required_wrench_body(
            payload,
            acceleration,
            nominal_twist_world,
            payload_yaw_rad=float(observation.payload_pose_m_rad[2]),
        )
        allocation = allocate_contact_wrench(
            self.config,
            world,
            observation,
            reference_wrench,
        )

        yaw = float(observation.payload_pose_m_rad[2])
        cosine, sine = np.cos(yaw), np.sin(yaw)
        rotation_world_from_body = np.asarray(
            [[cosine, -sine], [sine, cosine]],
            dtype=float,
        )
        wrench_error = (
            allocation.achieved_wrench_body
            - np.asarray(observation.measured_wrench_body, dtype=float)
        )
        admittance_twist_body = np.asarray(
            [
                control.wrench_force_admittance_m_s_per_n * wrench_error[0],
                control.wrench_force_admittance_m_s_per_n * wrench_error[1],
                control.wrench_torque_admittance_rad_s_per_n_m * wrench_error[2],
            ]
        )
        correction_limit = control.admittance_twist_limit_fraction * max_twist
        admittance_twist_body = np.clip(
            admittance_twist_body,
            -correction_limit,
            correction_limit,
        )
        commanded_twist_world = nominal_twist_world.copy()
        commanded_twist_world[:2] += (
            rotation_world_from_body @ admittance_twist_body[:2]
        )
        commanded_twist_world[2] += admittance_twist_body[2]
        commanded_twist_world = np.clip(
            commanded_twist_world,
            -max_twist,
            max_twist,
        )

        wheels = np.zeros((self.config.robot.count, 2), dtype=float)
        enabled = (
            np.asarray(observation.active_robot_mask, dtype=bool)
            & np.asarray(observation.contact_active, dtype=bool)
            & (allocation.contact_force_limit_n > 1.0e-12)
        )
        max_anchor_speed = (
            self.config.robot.wheel_radius_m
            * self.config.robot.max_wheel_speed_rad_s
        )
        for index, offset_body in enumerate(world.contact_offsets_body_m):
            if not enabled[index]:
                continue
            radius_world = rotation_world_from_body @ np.asarray(offset_body)
            anchor_velocity = (
                commanded_twist_world[:2]
                + commanded_twist_world[2]
                * np.asarray([-radius_world[1], radius_world[0]])
                + rotation_world_from_body
                @ (
                    control.contact_force_admittance_m_s_per_n
                    * allocation.force_setpoint_body_n[index]
                )
            )
            anchor_speed = float(np.linalg.norm(anchor_velocity))
            if anchor_speed > max_anchor_speed:
                anchor_velocity *= max_anchor_speed / anchor_speed
            heading = float(observation.robot_pose_m_rad[index, 2])
            desired_heading = (
                float(np.arctan2(anchor_velocity[1], anchor_velocity[0]))
                if np.linalg.norm(anchor_velocity) > 1.0e-9
                else heading
            )
            forward = float(
                anchor_velocity @ np.asarray([np.cos(heading), np.sin(heading)])
            )
            omega = commanded_twist_world[2] + control.heading_gain_s * wrap_angle(
                desired_heading - heading
            )
            wheels[index, 0] = (
                forward - 0.5 * self.config.robot.track_width_m * omega
            ) / self.config.robot.wheel_radius_m
            wheels[index, 1] = (
                forward + 0.5 * self.config.robot.track_width_m * omega
            ) / self.config.robot.wheel_radius_m

        wheel_limit = self.config.robot.max_wheel_speed_rad_s
        wheel_saturation_count = int(np.count_nonzero(np.abs(wheels) > wheel_limit))
        wheels = np.clip(wheels, -wheel_limit, wheel_limit)
        return WheelCommand(
            wheel_speed_rad_s=wheels,
            desired_acceleration_world_m_s2_rad_s2=acceleration,
            reference_wrench_body=reference_wrench,
            contact_force_setpoint_body_n=allocation.force_setpoint_body_n,
            contact_force_limit_n=allocation.contact_force_limit_n,
            allocated_wrench_body=allocation.achieved_wrench_body,
            allocation_residual_body=allocation.residual_body,
            allocation_residual_normalized=allocation.residual_normalized,
            allocation_utilization=allocation.utilization,
            allocation_saturation_count=allocation.saturation_count,
            wheel_saturation_count=wheel_saturation_count,
            admittance_twist_body_m_s_rad_s=admittance_twist_body,
            allocation_solver_success=allocation.solver_success,
            saturation_count=(
                allocation.saturation_count + wheel_saturation_count
            ),
            controller_id=control.controller_id,
        )


__all__ = [
    "CargoPoseController",
    "ContactAllocation",
    "Observation",
    "WheelCommand",
    "allocate_contact_wrench",
    "wrap_angle",
]
