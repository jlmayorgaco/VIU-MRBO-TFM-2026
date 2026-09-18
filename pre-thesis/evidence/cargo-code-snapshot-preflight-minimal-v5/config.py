"""Typed SI configuration for the primary CoppeliaSim Cargo campaign.

The confirmatory contract is deliberately strict: four binary factors produce
sixteen cells, thirty perturbation seeds are paired across all guards, and the
only evidence-eligible backend is the synchronous MuJoCo adapter.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


GUARDS = (
    "scalar_capacity",
    "planar_lsq",
    "supported_wrench_wheels",
)


def _positive(value: Any, name: str, *, allow_zero: bool = False) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0.0 or (number == 0.0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "strictly positive"
        raise ValueError(f"{name} must be {qualifier}")
    return number


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _vector(value: Any, size: int, name: str) -> tuple[float, ...]:
    try:
        vector = tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a numeric vector") from exc
    if len(vector) != size:
        raise ValueError(f"{name} must contain {size} values")
    if not all(abs(item) < float("inf") for item in vector):
        raise ValueError(f"{name} must contain finite values")
    return vector


@dataclass(frozen=True, slots=True)
class SeedConfig:
    start: int
    count: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.count <= 0:
            raise ValueError("seed start must be non-negative and count positive")

    @property
    def values(self) -> tuple[int, ...]:
        return tuple(range(self.start, self.start + self.count))


@dataclass(frozen=True, slots=True)
class AccelerationProfile:
    name: str
    peak_acceleration_world_m_s2_rad_s2: tuple[float, float, float]
    peak_twist_world_m_s_rad_s: tuple[float, float, float]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("acceleration profile name cannot be empty")
        for field_name in (
            "peak_acceleration_world_m_s2_rad_s2",
            "peak_twist_world_m_s_rad_s",
        ):
            values = getattr(self, field_name)
            if len(values) != 3 or not all(math.isfinite(value) and value >= 0.0 for value in values):
                raise ValueError(f"profile.{field_name} must be a finite non-negative 3-vector")


@dataclass(frozen=True, slots=True)
class MotionEnvelope:
    peak_lateral_acceleration_m_s2: float
    peak_yaw_acceleration_rad_s2: float
    peak_twist_world_m_s_rad_s: tuple[float, float, float]

    def __post_init__(self) -> None:
        _positive(
            self.peak_lateral_acceleration_m_s2,
            "design.motion_envelope.peak_lateral_acceleration_m_s2",
            allow_zero=True,
        )
        _positive(
            self.peak_yaw_acceleration_rad_s2,
            "design.motion_envelope.peak_yaw_acceleration_rad_s2",
            allow_zero=True,
        )
        if not all(math.isfinite(value) and value >= 0.0 for value in self.peak_twist_world_m_s_rad_s):
            raise ValueError("design.motion_envelope peak twist must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class PerturbationConfig:
    mass_relative_half_range: float
    friction_absolute_half_range: float
    com_jitter_m: float
    initial_pose_jitter_m: float
    initial_yaw_jitter_rad: float
    sensor_noise_std_n: float

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            _positive(value, f"perturbations.{name}", allow_zero=True)


@dataclass(frozen=True, slots=True)
class SensitivityConfig:
    dt_values_s: tuple[float, ...]
    cell_indices: tuple[int, ...]
    seeds_per_cell: int

    def __post_init__(self) -> None:
        if len(set(self.dt_values_s)) != len(self.dt_values_s):
            raise ValueError("dt sensitivity values must be unique")
        if not self.dt_values_s or any(value <= 0.0 for value in self.dt_values_s):
            raise ValueError("dt sensitivity values must be positive")
        if not self.cell_indices or len(set(self.cell_indices)) != len(self.cell_indices):
            raise ValueError("dt sensitivity cell indices must be non-empty and unique")
        if self.seeds_per_cell <= 0:
            raise ValueError("dt sensitivity seeds_per_cell must be positive")


@dataclass(frozen=True, slots=True)
class FactorialConfig:
    payload_mass_kg: tuple[float, ...]
    friction_regime: tuple[str, ...]
    friction_coefficients: Mapping[str, float]
    coalition: tuple[str, ...]
    longitudinal_acceleration_m_s2: tuple[float, ...]
    coalitions_m: Mapping[str, tuple[tuple[float, float], ...]]
    motion_envelope: MotionEnvelope
    perturbations: PerturbationConfig
    seeds: SeedConfig
    primary_dt_s: float
    sensitivity: SensitivityConfig

    def __post_init__(self) -> None:
        factor_levels = (
            self.payload_mass_kg,
            self.friction_regime,
            self.coalition,
            self.longitudinal_acceleration_m_s2,
        )
        if any(not levels or len(set(levels)) != len(levels) for levels in factor_levels):
            raise ValueError("factor levels must be non-empty and unique")
        if any(value <= 0.0 for value in self.payload_mass_kg):
            raise ValueError("payload masses must be positive")
        if any(name not in self.friction_coefficients for name in self.friction_regime):
            raise ValueError("every friction regime must define a coefficient")
        if any(self.friction_coefficients[name] <= 0.0 for name in self.friction_regime):
            raise ValueError("friction coefficients must be positive")
        if any(value <= 0.0 for value in self.longitudinal_acceleration_m_s2):
            raise ValueError("longitudinal acceleration levels must be positive")
        if not self.coalition or any(name not in self.coalitions_m for name in self.coalition):
            raise ValueError("every coalition factor level must define contact offsets")
        _positive(self.primary_dt_s, "design.primary_dt_s")
        if self.primary_dt_s not in self.sensitivity.dt_values_s:
            raise ValueError("dt sensitivity must include the primary timestep")
        if any(index < 0 or index >= self.cell_count for index in self.sensitivity.cell_indices):
            raise ValueError("dt sensitivity references a nonexistent factorial cell")
        if self.sensitivity.seeds_per_cell > self.seeds.count:
            raise ValueError("dt sensitivity cannot use more seeds than the primary design")

    @property
    def cell_count(self) -> int:
        return (
            len(self.payload_mass_kg)
            * len(self.friction_regime)
            * len(self.coalition)
            * len(self.longitudinal_acceleration_m_s2)
        )


@dataclass(frozen=True, slots=True)
class InferenceConfig:
    analysis_seed: int
    confidence_level: float
    bootstrap_resamples: int
    holm_family: str

    def __post_init__(self) -> None:
        if self.analysis_seed < 0:
            raise ValueError("inference.analysis_seed must be non-negative")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("inference.confidence_level must lie in (0, 1)")
        if self.bootstrap_resamples < 1_000:
            raise ValueError("inference.bootstrap_resamples must be at least 1000")
        if self.holm_family != "within_cell_and_endpoint":
            raise ValueError("inference.holm_family must be within_cell_and_endpoint")


@dataclass(frozen=True, slots=True)
class PayloadConfig:
    length_m: float
    width_m: float
    height_m: float
    linear_damping_n_s_m: float
    yaw_damping_n_m_s_rad: float
    initial_pose_m_rad: tuple[float, float, float]
    target_pose_m_rad: tuple[float, float, float]

    def __post_init__(self) -> None:
        for name in ("length_m", "width_m", "height_m"):
            _positive(getattr(self, name), f"payload.{name}")
        _positive(self.linear_damping_n_s_m, "payload.linear_damping_n_s_m", allow_zero=True)
        _positive(self.yaw_damping_n_m_s_rad, "payload.yaw_damping_n_m_s_rad", allow_zero=True)


@dataclass(frozen=True, slots=True)
class RobotConfig:
    count: int
    payload_capacity_kg: float
    wheel_radius_m: float
    track_width_m: float
    max_wheel_speed_rad_s: float
    max_drive_force_n: float
    max_normal_force_n: float

    def __post_init__(self) -> None:
        if self.count <= 0:
            raise ValueError("robot.count must be positive")
        for name, value in asdict(self).items():
            if name != "count":
                _positive(value, f"robot.{name}")


@dataclass(frozen=True, slots=True)
class ControlConfig:
    controller_id: str
    position_gain_s2: float
    velocity_gain_s: float
    yaw_gain_s2: float
    yaw_rate_gain_s: float
    heading_gain_s: float
    allocation_regularization: float
    contact_force_admittance_m_s_per_n: float
    wrench_force_admittance_m_s_per_n: float
    wrench_torque_admittance_rad_s_per_n_m: float
    admittance_twist_limit_fraction: float
    horizon_s: float
    series_stride: int

    def __post_init__(self) -> None:
        if not self.controller_id:
            raise ValueError("control.controller_id cannot be empty")
        for name, value in asdict(self).items():
            if name == "series_stride":
                if value <= 0:
                    raise ValueError("control.series_stride must be positive")
            elif name != "controller_id":
                _positive(value, f"control.{name}")
        if self.admittance_twist_limit_fraction > 1.0:
            raise ValueError(
                "control.admittance_twist_limit_fraction must lie in (0, 1]"
            )


@dataclass(frozen=True, slots=True)
class GateConfig:
    lsq_residual_max: float
    sensor_static_relative_error_max: float
    force_transmission_relative_error_max: float
    wheel_twist_relative_error_max: float
    contact_duty_min: float
    max_relative_slip_m: float
    final_position_error_m: float
    final_yaw_error_rad: float
    final_linear_speed_m_s: float
    final_angular_speed_rad_s: float
    dwell_time_s: float
    collision_count_max: int
    config_readback_abs_tolerance: float
    dt_final_position_spread_max_m: float
    dt_final_yaw_spread_max_rad: float
    dt_success_disagreement_max: int
    paired_repeat_position_spread_max_m: float
    paired_repeat_yaw_spread_max_rad: float
    paired_success_disagreement_max: int

    def __post_init__(self) -> None:
        bounded = (
            "lsq_residual_max",
            "sensor_static_relative_error_max",
            "force_transmission_relative_error_max",
            "wheel_twist_relative_error_max",
            "contact_duty_min",
        )
        for name in bounded:
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"gates.{name} must lie in [0, 1]")
        for name in (
            "max_relative_slip_m",
            "final_position_error_m",
            "final_yaw_error_rad",
            "final_linear_speed_m_s",
            "final_angular_speed_rad_s",
            "dwell_time_s",
            "config_readback_abs_tolerance",
            "dt_final_position_spread_max_m",
            "dt_final_yaw_spread_max_rad",
            "paired_repeat_position_spread_max_m",
            "paired_repeat_yaw_spread_max_rad",
        ):
            _positive(getattr(self, name), f"gates.{name}")
        if (
            self.collision_count_max < 0
            or self.dt_success_disagreement_max < 0
            or self.paired_success_disagreement_max < 0
        ):
            raise ValueError("integer gate limits must be non-negative")


@dataclass(frozen=True, slots=True)
class RobotAliases:
    robot_id: str
    base: str
    left_wheel_joint: str
    right_wheel_joint: str
    force_sensor: str

    def __post_init__(self) -> None:
        if not all((self.robot_id, self.base, self.left_wheel_joint, self.right_wheel_joint, self.force_sensor)):
            raise ValueError("robot aliases cannot be empty")


@dataclass(frozen=True, slots=True)
class BackendConfig:
    kind: str
    scene_path: str | None
    host: str
    port: int
    headless: bool
    startup_timeout_s: float
    payload_alias: str | None
    robots: tuple[RobotAliases, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"deterministic_contract", "coppeliasim_mujoco"}:
            raise ValueError("backend.kind must be deterministic_contract or coppeliasim_mujoco")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("backend.port is invalid")
        _positive(self.startup_timeout_s, "backend.startup_timeout_s")
        if self.kind == "coppeliasim_mujoco":
            if not self.scene_path or not self.payload_alias or not self.robots:
                raise ValueError("the Coppelia backend requires a scene, payload and robot aliases")


@dataclass(frozen=True, slots=True)
class CampaignConfig:
    experiment_id: str
    protocol_family: str
    mode: str
    output_dir: str
    guards: tuple[str, ...]
    backend: BackendConfig
    design: FactorialConfig
    payload: PayloadConfig
    robot: RobotConfig
    control: ControlConfig
    gates: GateConfig
    inference: InferenceConfig

    def __post_init__(self) -> None:
        if self.protocol_family != "coppelia_cargo_v1":
            raise ValueError("protocol_family must be coppelia_cargo_v1")
        if self.mode not in {"smoke", "confirmatory"}:
            raise ValueError("mode must be smoke or confirmatory")
        if self.guards != GUARDS:
            raise ValueError(f"guards must use the canonical order {GUARDS}")
        if not self.experiment_id or not self.output_dir:
            raise ValueError("experiment_id and output_dir are required")
        coalition_sizes = {
            name: len(self.design.coalitions_m[name]) for name in self.design.coalition
        }
        if any(size < 2 or size > self.robot.count for size in coalition_sizes.values()):
            raise ValueError("coalition layouts must contain between two and robot.count offsets")
        if self.backend.kind == "coppeliasim_mujoco" and len(self.backend.robots) != self.robot.count:
            raise ValueError("the Coppelia scene contract needs one alias set per robot")
        if self.mode == "confirmatory":
            if self.backend.kind != "coppeliasim_mujoco":
                raise ValueError("synthetic backends can never run a confirmatory protocol")
            if self.design.cell_count != 16:
                raise ValueError("the confirmatory factorial must contain exactly 16 cells")
            factor_lengths = (
                len(self.design.payload_mass_kg),
                len(self.design.friction_regime),
                len(self.design.coalition),
                len(self.design.longitudinal_acceleration_m_s2),
            )
            if factor_lengths != (2, 2, 2, 2):
                raise ValueError("the confirmatory design must be a 2x2x2x2 factorial")
            if self.design.seeds.count != 30:
                raise ValueError("the confirmatory design requires exactly 30 paired seeds")
            if self.design.payload_mass_kg != (14.0, 28.0):
                raise ValueError("confirmatory payload masses must be 14 and 28 kg")
            if self.design.friction_regime != ("low", "nominal"):
                raise ValueError("confirmatory friction regimes must be low and nominal")
            if self.design.coalition != ("minimal", "redundant") or tuple(coalition_sizes.values()) != (3, 4):
                raise ValueError("confirmatory coalitions must be minimal=3 and redundant=4")
            if self.design.longitudinal_acceleration_m_s2 != (0.10, 0.25):
                raise ValueError("confirmatory longitudinal accelerations must be 0.10 and 0.25 m/s^2")
            if self.inference.confidence_level != 0.95:
                raise ValueError("confirmatory inference requires 95% confidence intervals")

    @property
    def canonical_hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_config(path: str | Path) -> CampaignConfig:
    """Load and validate a Cargo campaign YAML without touching output state."""

    source = Path(path)
    raw = _mapping(yaml.safe_load(source.read_text(encoding="utf-8")), "configuration")
    design_raw = _mapping(raw["design"], "design")
    factors = _mapping(design_raw["factors"], "design.factors")
    coalitions_raw = _mapping(design_raw["coalitions_m"], "design.coalitions_m")
    coalitions = {
        str(name): tuple(
            _vector(offset, 2, f"design.coalitions_m.{name}") for offset in offsets
        )
        for name, offsets in coalitions_raw.items()
    }
    motion = _mapping(design_raw["motion_envelope"], "design.motion_envelope")
    perturb = _mapping(design_raw["perturbations"], "design.perturbations")
    seeds = _mapping(design_raw["seeds"], "design.seeds")
    sensitivity = _mapping(design_raw["dt_sensitivity"], "design.dt_sensitivity")
    design = FactorialConfig(
        payload_mass_kg=tuple(float(value) for value in factors["payload_mass_kg"]),
        friction_regime=tuple(str(value) for value in factors["friction_regime"]),
        friction_coefficients={
            str(name): float(value)
            for name, value in _mapping(
                design_raw["friction_coefficients"], "design.friction_coefficients"
            ).items()
        },
        coalition=tuple(str(value) for value in factors["coalition"]),
        longitudinal_acceleration_m_s2=tuple(
            float(value) for value in factors["longitudinal_acceleration_m_s2"]
        ),
        coalitions_m=coalitions,
        motion_envelope=MotionEnvelope(
            peak_lateral_acceleration_m_s2=float(
                motion["peak_lateral_acceleration_m_s2"]
            ),
            peak_yaw_acceleration_rad_s2=float(
                motion["peak_yaw_acceleration_rad_s2"]
            ),
            peak_twist_world_m_s_rad_s=_vector(
                motion["peak_twist_world_m_s_rad_s"],
                3,
                "design.motion_envelope.peak_twist_world_m_s_rad_s",
            ),
        ),
        perturbations=PerturbationConfig(
            mass_relative_half_range=float(perturb["mass_relative_half_range"]),
            friction_absolute_half_range=float(perturb["friction_absolute_half_range"]),
            com_jitter_m=float(perturb["com_jitter_m"]),
            initial_pose_jitter_m=float(perturb["initial_pose_jitter_m"]),
            initial_yaw_jitter_rad=float(perturb["initial_yaw_jitter_rad"]),
            sensor_noise_std_n=float(perturb["sensor_noise_std_n"]),
        ),
        seeds=SeedConfig(start=int(seeds["start"]), count=int(seeds["count"])),
        primary_dt_s=float(design_raw["primary_dt_s"]),
        sensitivity=SensitivityConfig(
            dt_values_s=tuple(float(value) for value in sensitivity["values_s"]),
            cell_indices=tuple(int(value) for value in sensitivity["cell_indices"]),
            seeds_per_cell=int(sensitivity["seeds_per_cell"]),
        ),
    )

    payload_raw = _mapping(raw["payload"], "payload")
    robot_raw = _mapping(raw["robot"], "robot")
    control_raw = _mapping(raw["control"], "control")
    gates_raw = _mapping(raw["gates"], "gates")
    backend_raw = _mapping(raw["backend"], "backend")
    inference_raw = _mapping(raw["inference"], "inference")
    aliases_raw = backend_raw.get("aliases", {})
    aliases = _mapping(aliases_raw, "backend.aliases") if aliases_raw else {}
    robot_aliases = tuple(
        RobotAliases(
            robot_id=str(item["robot_id"]),
            base=str(item["base"]),
            left_wheel_joint=str(item["left_wheel_joint"]),
            right_wheel_joint=str(item["right_wheel_joint"]),
            force_sensor=str(item["force_sensor"]),
        )
        for item in aliases.get("robots", ())
    )
    return CampaignConfig(
        experiment_id=str(raw["experiment_id"]),
        protocol_family=str(raw["protocol_family"]),
        mode=str(raw["mode"]),
        output_dir=str(raw["output_dir"]),
        guards=tuple(str(value) for value in raw["guards"]),
        backend=BackendConfig(
            kind=str(backend_raw["kind"]),
            scene_path=(None if backend_raw.get("scene_path") is None else str(backend_raw["scene_path"])),
            host=str(backend_raw.get("host", "127.0.0.1")),
            port=int(backend_raw.get("port", 23000)),
            headless=bool(backend_raw.get("headless", True)),
            startup_timeout_s=float(backend_raw.get("startup_timeout_s", 120.0)),
            payload_alias=(None if not aliases else str(aliases["payload"])),
            robots=robot_aliases,
        ),
        design=design,
        payload=PayloadConfig(
            length_m=float(payload_raw["length_m"]),
            width_m=float(payload_raw["width_m"]),
            height_m=float(payload_raw["height_m"]),
            linear_damping_n_s_m=float(payload_raw["linear_damping_n_s_m"]),
            yaw_damping_n_m_s_rad=float(payload_raw["yaw_damping_n_m_s_rad"]),
            initial_pose_m_rad=_vector(payload_raw["initial_pose_m_rad"], 3, "payload.initial_pose_m_rad"),
            target_pose_m_rad=_vector(payload_raw["target_pose_m_rad"], 3, "payload.target_pose_m_rad"),
        ),
        robot=RobotConfig(
            count=int(robot_raw["count"]),
            payload_capacity_kg=float(robot_raw["payload_capacity_kg"]),
            wheel_radius_m=float(robot_raw["wheel_radius_m"]),
            track_width_m=float(robot_raw["track_width_m"]),
            max_wheel_speed_rad_s=float(robot_raw["max_wheel_speed_rad_s"]),
            max_drive_force_n=float(robot_raw["max_drive_force_n"]),
            max_normal_force_n=float(robot_raw["max_normal_force_n"]),
        ),
        control=ControlConfig(
            controller_id=str(control_raw["controller_id"]),
            position_gain_s2=float(control_raw["position_gain_s2"]),
            velocity_gain_s=float(control_raw["velocity_gain_s"]),
            yaw_gain_s2=float(control_raw["yaw_gain_s2"]),
            yaw_rate_gain_s=float(control_raw["yaw_rate_gain_s"]),
            heading_gain_s=float(control_raw["heading_gain_s"]),
            allocation_regularization=float(
                control_raw["allocation_regularization"]
            ),
            contact_force_admittance_m_s_per_n=float(
                control_raw["contact_force_admittance_m_s_per_n"]
            ),
            wrench_force_admittance_m_s_per_n=float(
                control_raw["wrench_force_admittance_m_s_per_n"]
            ),
            wrench_torque_admittance_rad_s_per_n_m=float(
                control_raw["wrench_torque_admittance_rad_s_per_n_m"]
            ),
            admittance_twist_limit_fraction=float(
                control_raw["admittance_twist_limit_fraction"]
            ),
            horizon_s=float(control_raw["horizon_s"]),
            series_stride=int(control_raw.get("series_stride", 1)),
        ),
        gates=GateConfig(
            lsq_residual_max=float(gates_raw["lsq_residual_max"]),
            sensor_static_relative_error_max=float(gates_raw["sensor_static_relative_error_max"]),
            force_transmission_relative_error_max=float(gates_raw["force_transmission_relative_error_max"]),
            wheel_twist_relative_error_max=float(gates_raw["wheel_twist_relative_error_max"]),
            contact_duty_min=float(gates_raw["contact_duty_min"]),
            max_relative_slip_m=float(gates_raw["max_relative_slip_m"]),
            final_position_error_m=float(gates_raw["final_position_error_m"]),
            final_yaw_error_rad=float(gates_raw["final_yaw_error_rad"]),
            final_linear_speed_m_s=float(gates_raw["final_linear_speed_m_s"]),
            final_angular_speed_rad_s=float(gates_raw["final_angular_speed_rad_s"]),
            dwell_time_s=float(gates_raw["dwell_time_s"]),
            collision_count_max=int(gates_raw["collision_count_max"]),
            config_readback_abs_tolerance=float(gates_raw["config_readback_abs_tolerance"]),
            dt_final_position_spread_max_m=float(gates_raw["dt_final_position_spread_max_m"]),
            dt_final_yaw_spread_max_rad=float(gates_raw["dt_final_yaw_spread_max_rad"]),
            dt_success_disagreement_max=int(gates_raw["dt_success_disagreement_max"]),
            paired_repeat_position_spread_max_m=float(
                gates_raw["paired_repeat_position_spread_max_m"]
            ),
            paired_repeat_yaw_spread_max_rad=float(
                gates_raw["paired_repeat_yaw_spread_max_rad"]
            ),
            paired_success_disagreement_max=int(
                gates_raw["paired_success_disagreement_max"]
            ),
        ),
        inference=InferenceConfig(
            analysis_seed=int(inference_raw["analysis_seed"]),
            confidence_level=float(inference_raw["confidence_level"]),
            bootstrap_resamples=int(inference_raw["bootstrap_resamples"]),
            holm_family=str(inference_raw["holm_family"]),
        ),
    )


__all__ = [
    "GUARDS",
    "AccelerationProfile",
    "BackendConfig",
    "CampaignConfig",
    "ControlConfig",
    "FactorialConfig",
    "GateConfig",
    "InferenceConfig",
    "MotionEnvelope",
    "PayloadConfig",
    "RobotAliases",
    "RobotConfig",
    "SeedConfig",
    "SensitivityConfig",
    "load_config",
]
