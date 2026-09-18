"""Backend contract and an explicitly non-evidentiary deterministic double."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .config import CampaignConfig
from .controller import Observation, WheelCommand
from .design import WorldSpec


@dataclass(frozen=True, slots=True)
class BackendMetadata:
    backend_kind: str
    evidence_class: str
    engine: str
    simulator_version: str
    synchronous_stepping: bool
    actuator_contract: str
    wrench_realization: str


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    sensor_static_relative_error: float
    force_transmission_relative_error: float
    wheel_twist_relative_error: float
    scene_no_pose_actuation_audited: bool
    configuration_acknowledged: bool
    readback_max_abs_error: float
    raw: dict[str, object]


class CargoBackend(Protocol):
    @property
    def metadata(self) -> BackendMetadata: ...

    @property
    def calibration(self) -> CalibrationReport: ...

    def start(self) -> None: ...

    def reset(self, world: WorldSpec, dt_s: float) -> Observation: ...

    def apply(self, command: WheelCommand) -> None: ...

    def step(self) -> Observation: ...

    def close(self) -> None: ...


class DeterministicCargoBackend:
    """Reduced deterministic plant for tests only, never physical evidence."""

    def __init__(self, config: CampaignConfig) -> None:
        self.config = config
        self._world: WorldSpec | None = None
        self._dt = 0.0
        self._time = 0.0
        self._pose = np.zeros(3)
        self._twist = np.zeros(3)
        self._robot_pose = np.zeros((config.robot.count, 3))
        self._wheels = np.zeros((config.robot.count, 2))
        self._wheel_drive_force = np.zeros((config.robot.count, 2))
        self._measured_wrench = np.zeros(3)
        self._normal = np.zeros(config.robot.count)
        self._contact = np.ones(config.robot.count, dtype=bool)
        self._active_mask = np.zeros(config.robot.count, dtype=bool)
        self._slip = np.zeros(config.robot.count)
        self._collisions = 0
        self._rng = np.random.default_rng(0)
        self._started = False

    @property
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(
            backend_kind="deterministic_contract",
            evidence_class="synthetic_contract_test_only",
            engine="reduced_deterministic_plant",
            simulator_version="not_coppeliasim",
            synchronous_stepping=True,
            actuator_contract="wheel_velocity_commands",
            wrench_realization="bounded_contact_setpoints_indirectly_realized_by_wheel_velocity",
        )

    @property
    def calibration(self) -> CalibrationReport:
        return CalibrationReport(
            sensor_static_relative_error=0.0,
            force_transmission_relative_error=0.0,
            wheel_twist_relative_error=0.0,
            scene_no_pose_actuation_audited=True,
            configuration_acknowledged=True,
            readback_max_abs_error=0.0,
            raw={"synthetic": True, "evidence_eligible": False},
        )

    def start(self) -> None:
        self._started = True

    def reset(self, world: WorldSpec, dt_s: float) -> Observation:
        if not self._started:
            raise RuntimeError("backend must be started before reset")
        self._world = world
        self._dt = float(dt_s)
        self._time = 0.0
        self._pose = np.asarray(world.initial_pose_m_rad, dtype=float).copy()
        self._twist = np.zeros(3)
        self._robot_pose = np.zeros((self.config.robot.count, 3))
        travel = np.asarray(world.target_pose_m_rad[:2]) - self._pose[:2]
        initial_heading = float(np.arctan2(travel[1], travel[0])) if np.linalg.norm(travel) > 1e-12 else self._pose[2]
        self._robot_pose[:, 2] = initial_heading
        self._wheels = np.zeros((self.config.robot.count, 2))
        self._wheel_drive_force = np.zeros((self.config.robot.count, 2))
        self._measured_wrench = np.zeros(3)
        self._normal = np.full(
            self.config.robot.count, 0.0,
        )
        self._active_mask = np.arange(self.config.robot.count) < world.active_robot_count
        self._normal[self._active_mask] = (
            world.actual_payload_mass_kg * 9.81 / world.active_robot_count
        )
        self._contact = self._active_mask.copy()
        self._slip = np.zeros(self.config.robot.count)
        self._collisions = 0
        seed_material = int(world.world_hash[:16], 16) ^ int(round(dt_s * 1e9))
        self._rng = np.random.default_rng(seed_material)
        self._update_robot_pose(np.zeros(self.config.robot.count))
        return self._observation()

    def apply(self, command: WheelCommand) -> None:
        wheels = np.asarray(command.wheel_speed_rad_s, dtype=float)
        if wheels.shape != (self.config.robot.count, 2) or not np.isfinite(wheels).all():
            raise ValueError("wheel command is not finite or has the wrong shape")
        if self._world is not None and np.any(
            wheels[self._world.active_robot_count :] != 0.0
        ):
            raise ValueError("inactive coalition members must receive zero wheel velocity")
        self._wheels = wheels.copy()

    def _update_robot_pose(self, heading_rate: np.ndarray) -> None:
        if self._world is None:
            return
        c, s = np.cos(self._pose[2]), np.sin(self._pose[2])
        rotation = np.asarray([[c, -s], [s, c]])
        for index, offset in enumerate(self._world.contact_offsets_body_m):
            self._robot_pose[index, :2] = self._pose[:2] + rotation @ np.asarray(offset)
            self._robot_pose[index, 2] += heading_rate[index] * self._dt
        for index in range(self._world.active_robot_count, self.config.robot.count):
            self._robot_pose[index] = [-2.0 - index, -2.0, 0.0]

    def step(self) -> Observation:
        if self._world is None:
            raise RuntimeError("backend has not been reset")
        radius = self.config.robot.wheel_radius_m
        track = self.config.robot.track_width_m
        active = self._world.active_robot_count
        active_wheels = self._wheels[:active]
        forward = radius * np.mean(active_wheels, axis=1)
        yaw_rate = radius * (active_wheels[:, 1] - active_wheels[:, 0]) / track
        headings = self._robot_pose[:active, 2]
        robot_velocity = np.column_stack((forward * np.cos(headings), forward * np.sin(headings)))
        requested = np.asarray([*np.mean(robot_velocity, axis=0), float(np.mean(yaw_rate))])

        max_linear_acceleration = min(
            self._world.actual_friction_coefficient * 9.81,
            active * self.config.robot.max_drive_force_n / self._world.actual_payload_mass_kg,
        )
        delta = requested - self._twist
        linear_delta = delta[:2]
        norm = float(np.linalg.norm(linear_delta))
        max_delta = max_linear_acceleration * self._dt
        if norm > max_delta > 0.0:
            linear_delta *= max_delta / norm
        yaw_delta = float(np.clip(delta[2], -2.0 * self._dt, 2.0 * self._dt))
        previous = self._twist.copy()
        self._twist[:2] += linear_delta
        self._twist[2] += yaw_delta
        self._pose += self._twist * self._dt
        self._pose[2] = (self._pose[2] + np.pi) % (2.0 * np.pi) - np.pi
        full_heading_rate = np.zeros(self.config.robot.count)
        full_heading_rate[:active] = yaw_rate
        self._update_robot_pose(full_heading_rate)
        acceleration = (self._twist - previous) / self._dt
        # Synthetic-only actuator diagnostic.  Split each robot's projected
        # payload force equally across its two driven wheels and cap the
        # aggregate pair at the configured per-robot traction limit.
        self._wheel_drive_force.fill(0.0)
        planar_force = self._world.actual_payload_mass_kg * acceleration[:2]
        for index, heading in enumerate(headings):
            longitudinal = abs(
                float(planar_force @ np.asarray([np.cos(heading), np.sin(heading)]))
            ) / active
            per_wheel = min(
                0.5 * longitudinal,
                0.5 * self.config.robot.max_drive_force_n,
            )
            self._wheel_drive_force[index] = per_wheel
        self._measured_wrench = np.asarray(
            [
                self._world.actual_payload_mass_kg * acceleration[0],
                self._world.actual_payload_mass_kg * acceleration[1],
                self._world.yaw_inertia_kg_m2 * acceleration[2],
            ]
        )
        noise = self.config.design.perturbations.sensor_noise_std_n
        if noise:
            self._measured_wrench[:2] += self._rng.normal(0.0, noise, size=2)
        anchor_speed_error = np.linalg.norm(robot_velocity - self._twist[:2], axis=1)
        self._slip = np.zeros(self.config.robot.count)
        self._slip[:active] = anchor_speed_error * self._dt
        self._time += self._dt
        return self._observation()

    def _observation(self) -> Observation:
        return Observation(
            time_s=float(self._time),
            payload_pose_m_rad=self._pose.copy(),
            payload_twist_m_s_rad_s=self._twist.copy(),
            robot_pose_m_rad=self._robot_pose.copy(),
            wheel_speed_rad_s=self._wheels.copy(),
            wheel_drive_force_n=self._wheel_drive_force.copy(),
            measured_wrench_body=self._measured_wrench.copy(),
            normal_force_n=self._normal.copy(),
            contact_active=self._contact.copy(),
            active_robot_mask=self._active_mask.copy(),
            relative_slip_m=self._slip.copy(),
            collision_count=self._collisions,
        )

    def close(self) -> None:
        self._started = False
        self._world = None


__all__ = [
    "BackendMetadata",
    "CalibrationReport",
    "CargoBackend",
    "DeterministicCargoBackend",
]
