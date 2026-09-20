"""Cross-layer command governor for kinematic and mechanical feasibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .dynamics import PlanarPayload, required_wrench_body
from .kinematics import DifferentialDrive, FormationCertificate, certify_formation_twist
from .mechanics import MechanicalCertificate, certify_supported_wrench
from .support import SupportContact


@dataclass(frozen=True, slots=True)
class GovernorResult:
    status: str
    scale: float
    brake_scale: float
    requested_acceleration: np.ndarray
    executed_acceleration: np.ndarray
    kinematic: FormationCertificate
    mechanical: MechanicalCertificate
    information_fresh: bool
    auxiliary_guard_feasible: bool


def govern_acceleration(
    requested_acceleration: np.ndarray,
    twist_world: np.ndarray,
    payload_yaw_rad: float,
    payload: PlanarPayload,
    drives: list[DifferentialDrive] | tuple[DifferentialDrive, ...],
    offsets_body_m: np.ndarray,
    contacts: list[SupportContact] | tuple[SupportContact, ...],
    *,
    external_wrench_world: np.ndarray | None = None,
    scale_grid: np.ndarray | None = None,
    lookahead_s: float = 0.2,
    candidate_guard: Callable[[np.ndarray], bool] | None = None,
    information_fresh: bool = True,
    brake_acceleration: np.ndarray | None = None,
    brake_gain: float = 1.8,
    hold_twist_tolerance: float = 1e-3,
) -> GovernorResult:
    """Choose an executable nominal, braking, holding, or uncontrolled action.

    N1, N2, an optional sampled safety guard, and information freshness are
    evaluated jointly. A zero nominal scale is only a hold when the load is
    already quasi-stationary; otherwise the governor attempts active braking.
    """

    requested = np.asarray(requested_acceleration, dtype=float)
    twist = np.asarray(twist_world, dtype=float)
    if requested.shape != (3,) or twist.shape != (3,):
        raise ValueError("acceleration and twist must be 3-vectors")
    if lookahead_s < 0.0:
        raise ValueError("lookahead_s must be non-negative")
    if brake_gain <= 0.0 or hold_twist_tolerance < 0.0:
        raise ValueError("brake_gain must be positive and hold tolerance non-negative")
    if brake_acceleration is not None:
        brake = np.asarray(brake_acceleration, dtype=float)
        if brake.shape != (3,) or not np.all(np.isfinite(brake)):
            raise ValueError("brake_acceleration must be a finite 3-vector")
    else:
        brake = -float(brake_gain) * twist
    grid = np.linspace(1.0, 0.0, 21) if scale_grid is None else np.asarray(scale_grid, dtype=float)
    if grid.ndim != 1 or grid.size == 0 or np.any(grid < 0.0) or np.any(grid > 1.0):
        raise ValueError("scale_grid must be a non-empty vector inside [0, 1]")
    ordered = np.unique(grid)[::-1]
    last_kinematic: FormationCertificate | None = None
    last_mechanical: MechanicalCertificate | None = None
    last_auxiliary = False

    def evaluate(candidate: np.ndarray) -> tuple[FormationCertificate, MechanicalCertificate, bool]:
        nonlocal last_kinematic, last_mechanical, last_auxiliary
        predicted_twist = twist + float(lookahead_s) * candidate
        kinematic = certify_formation_twist(
            drives,
            offsets_body_m,
            predicted_twist,
            candidate,
            payload_yaw_rad=payload_yaw_rad,
        )
        wrench = required_wrench_body(
            payload,
            candidate,
            twist,
            payload_yaw_rad,
            external_wrench_world,
        )
        mechanical = certify_supported_wrench(
            contacts,
            payload.mass_kg,
            wrench,
            diagnose_infeasible=False,
        )
        auxiliary = bool(candidate_guard(candidate)) if candidate_guard is not None else True
        last_kinematic = kinematic
        last_mechanical = mechanical
        last_auxiliary = auxiliary
        return kinematic, mechanical, auxiliary

    if information_fresh:
        for scale in ordered:
            if scale <= 1e-12:
                continue
            candidate = float(scale) * requested
            kinematic, mechanical, auxiliary = evaluate(candidate)
            if not (kinematic.feasible and mechanical.feasible and auxiliary):
                continue
            if scale >= 1.0 - 1e-12:
                status = "accepted"
            else:
                status = "scaled"
            return GovernorResult(
                status=status,
                scale=float(scale),
                brake_scale=0.0,
                requested_acceleration=requested,
                executed_acceleration=candidate,
                kinematic=kinematic,
                mechanical=mechanical,
                information_fresh=True,
                auxiliary_guard_feasible=auxiliary,
            )

    zero = np.zeros(3)
    zero_kinematic, zero_mechanical, zero_auxiliary = evaluate(zero)
    if (
        np.linalg.norm(twist) <= hold_twist_tolerance
        and zero_kinematic.feasible
        and zero_mechanical.feasible
        and zero_auxiliary
    ):
        return GovernorResult(
            status="hold",
            scale=0.0,
            brake_scale=0.0,
            requested_acceleration=requested,
            executed_acceleration=zero,
            kinematic=zero_kinematic,
            mechanical=zero_mechanical,
            information_fresh=bool(information_fresh),
            auxiliary_guard_feasible=zero_auxiliary,
        )

    if np.linalg.norm(brake) > hold_twist_tolerance:
        for brake_scale in ordered:
            if brake_scale <= 1e-12:
                continue
            candidate = float(brake_scale) * brake
            kinematic, mechanical, auxiliary = evaluate(candidate)
            if not (kinematic.feasible and mechanical.feasible and auxiliary):
                continue
            return GovernorResult(
                status="brake",
                scale=0.0,
                brake_scale=float(brake_scale),
                requested_acceleration=requested,
                executed_acceleration=candidate,
                kinematic=kinematic,
                mechanical=mechanical,
                information_fresh=bool(information_fresh),
                auxiliary_guard_feasible=auxiliary,
            )

    assert last_kinematic is not None and last_mechanical is not None
    return GovernorResult(
        status="uncontrolled_stop_required",
        scale=0.0,
        brake_scale=0.0,
        requested_acceleration=requested,
        executed_acceleration=zero,
        kinematic=last_kinematic,
        mechanical=last_mechanical,
        information_fresh=bool(information_fresh),
        auxiliary_guard_feasible=last_auxiliary,
    )


__all__ = ["GovernorResult", "govern_acceleration"]
