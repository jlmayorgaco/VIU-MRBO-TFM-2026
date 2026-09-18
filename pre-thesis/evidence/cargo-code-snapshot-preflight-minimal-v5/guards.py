"""Three preregistered feasibility guards for the same physical trials."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import lsq_linear

from viu_mrob_tfm.sp2_canonical.dynamics import PlanarPayload, required_wrench_body
from viu_mrob_tfm.sp2_canonical.kinematics import DifferentialDrive, certify_formation_twist
from viu_mrob_tfm.sp2_canonical.mechanics import certify_supported_wrench, grasp_matrix_2d
from viu_mrob_tfm.sp2_canonical.support import SupportContact

from .config import CampaignConfig
from .design import WorldSpec


@dataclass(frozen=True, slots=True)
class GuardDecision:
    guard: str
    accepted: bool
    reason: str
    capacity_margin_kg: float
    wrench_residual_normalized: float
    wrench_utilization: float
    support_margin: float
    wheel_margin: float

    def as_record(self) -> dict[str, object]:
        return {
            "guard_accepted": self.accepted,
            "guard_reason": self.reason,
            "capacity_margin_kg": self.capacity_margin_kg,
            "guard_wrench_residual_normalized": self.wrench_residual_normalized,
            "guard_wrench_utilization": self.wrench_utilization,
            "guard_support_margin": self.support_margin,
            "guard_wheel_margin": self.wheel_margin,
        }


def required_peak_wrench(config: CampaignConfig, world: WorldSpec) -> np.ndarray:
    payload = PlanarPayload(
        mass_kg=world.actual_payload_mass_kg,
        yaw_inertia_kg_m2=world.yaw_inertia_kg_m2,
        linear_damping_n_s_m=config.payload.linear_damping_n_s_m,
        yaw_damping_n_m_s_rad=config.payload.yaw_damping_n_m_s_rad,
    )
    return required_wrench_body(
        payload,
        np.asarray(world.profile.peak_acceleration_world_m_s2_rad_s2),
        np.asarray(world.profile.peak_twist_world_m_s_rad_s),
        payload_yaw_rad=0.0,
    )


def _base(config: CampaignConfig, world: WorldSpec, guard: str) -> dict[str, float | str | bool]:
    margin = (
        world.active_robot_count * config.robot.payload_capacity_kg
        - world.actual_payload_mass_kg
    )
    return {
        "guard": guard,
        "accepted": margin >= 0.0,
        "reason": "capacity_pass" if margin >= 0.0 else "capacity_fail",
        "capacity_margin_kg": float(margin),
        "wrench_residual_normalized": float("nan"),
        "wrench_utilization": float("nan"),
        "support_margin": float("nan"),
        "wheel_margin": float("nan"),
    }


def evaluate_guard(config: CampaignConfig, world: WorldSpec, guard: str) -> GuardDecision:
    """Predict feasibility; this decision never changes the executed controller."""

    values = _base(config, world, guard)
    if guard == "scalar_capacity":
        return GuardDecision(**values)

    wrench = required_peak_wrench(config, world)
    offsets = np.asarray(world.contact_offsets_body_m, dtype=float)
    grasp = grasp_matrix_2d(offsets)
    n_components = 2 * world.active_robot_count
    upper = np.repeat(config.robot.max_drive_force_n, n_components)
    # Signed planar force components are represented directly by symmetric bounds.
    result = lsq_linear(grasp, wrench, bounds=(-upper, upper), tol=1e-12, max_iter=2_000)
    residual_si = float(np.linalg.norm(grasp @ result.x - wrench))
    residual = residual_si / max(float(np.linalg.norm(wrench)), 1.0)
    utilization = float(np.max(np.abs(result.x) / upper))
    planar_ok = bool(result.success and residual <= config.gates.lsq_residual_max and utilization <= 1.0 + 1e-9)
    planar_reason = "planar_lsq_pass" if planar_ok else "planar_lsq_fail"
    if float(values["capacity_margin_kg"]) < 0.0:
        planar_reason = f"capacity_fail|{planar_reason}"
    values.update(
        accepted=bool(values["accepted"] and planar_ok),
        reason=planar_reason,
        wrench_residual_normalized=residual,
        wrench_utilization=utilization,
    )
    if guard == "planar_lsq":
        return GuardDecision(**values)
    if guard != "supported_wrench_wheels":
        raise ValueError(f"unknown guard: {guard}")

    contacts = tuple(
        SupportContact(
            robot_id=f"R{index + 1}",
            offset_body_m=tuple(offset),
            friction_coefficient=world.actual_friction_coefficient,
            max_normal_force_n=config.robot.max_normal_force_n,
            max_drive_force_n=config.robot.max_drive_force_n,
        )
        for index, offset in enumerate(world.contact_offsets_body_m)
    )
    mechanical = certify_supported_wrench(
        contacts,
        world.actual_payload_mass_kg,
        wrench,
        com_offset_body_m=world.com_offset_body_m,
    )
    drives = tuple(
        DifferentialDrive(
            robot_id=f"R{index + 1}",
            wheel_radius_m=config.robot.wheel_radius_m,
            track_width_m=config.robot.track_width_m,
            max_wheel_speed_rad_s=config.robot.max_wheel_speed_rad_s,
        )
        for index in range(world.active_robot_count)
    )
    wheel = certify_formation_twist(
        drives,
        offsets,
        np.asarray(world.profile.peak_twist_world_m_s_rad_s),
        np.asarray(world.profile.peak_acceleration_world_m_s2_rad_s2),
    )
    accepted = bool(values["accepted"] and planar_ok and mechanical.feasible and wheel.feasible)
    reasons = []
    if float(values["capacity_margin_kg"]) < 0.0:
        reasons.append("capacity")
    if not planar_ok:
        reasons.append("planar_lsq")
    if not mechanical.feasible:
        reasons.append(f"mechanics:{mechanical.status}")
    if not wheel.feasible:
        reasons.append(f"wheels:{wheel.reason}")
    values.update(
        accepted=accepted,
        reason="supported_wrench_wheels_pass" if accepted else "|".join(reasons),
        wrench_residual_normalized=float(mechanical.residual_norm),
        wrench_utilization=float(mechanical.utilization),
        support_margin=(float(mechanical.support.margin) if mechanical.support else float("nan")),
        wheel_margin=float(wheel.margin),
    )
    return GuardDecision(**values)


__all__ = ["GuardDecision", "evaluate_guard", "required_peak_wrench"]
