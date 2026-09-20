"""Static 2.5-D support equilibrium for the supported-load branch."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True, slots=True)
class SupportContact:
    robot_id: str
    offset_body_m: tuple[float, float]
    friction_coefficient: float
    max_normal_force_n: float
    max_drive_force_n: float
    min_normal_force_n: float = 0.0

    def __post_init__(self) -> None:
        if self.friction_coefficient <= 0.0:
            raise ValueError("friction coefficient must be strictly positive")
        if self.max_normal_force_n <= self.min_normal_force_n or self.min_normal_force_n < 0.0:
            raise ValueError("normal-force interval is invalid")
        if self.max_drive_force_n <= 0.0:
            raise ValueError("drive-force limit must be strictly positive")


@dataclass(frozen=True, slots=True)
class SupportCertificate:
    feasible: bool
    normal_forces_n: np.ndarray
    equilibrium_residual: np.ndarray
    normalized_equilibrium_residual: np.ndarray
    residual_norm: float
    utilization: float
    margin: float
    limiting_robot_id: str
    status: str


def solve_vertical_support(
    contacts: list[SupportContact] | tuple[SupportContact, ...],
    payload_mass_kg: float,
    *,
    com_offset_body_m: np.ndarray | tuple[float, float] = (0.0, 0.0),
    gravity_m_s2: float = 9.81,
    tolerance: float = 1e-7,
) -> SupportCertificate:
    """Find normal forces satisfying weight and the two tipping moments."""

    return _solve_vertical_support_cached(
        tuple(contacts),
        float(payload_mass_kg),
        tuple(np.asarray(com_offset_body_m, dtype=float).tolist()),
        float(gravity_m_s2),
        float(tolerance),
    )


@lru_cache(maxsize=256)
def _solve_vertical_support_cached(
    contacts: tuple[SupportContact, ...],
    payload_mass_kg: float,
    com_offset_body_m: tuple[float, float],
    gravity_m_s2: float,
    tolerance: float,
) -> SupportCertificate:

    if not contacts:
        raise ValueError("at least one support contact is required")
    if payload_mass_kg <= 0.0 or gravity_m_s2 <= 0.0:
        raise ValueError("mass and gravity must be strictly positive")
    com = np.asarray(com_offset_body_m, dtype=float)
    if com.shape != (2,) or not np.all(np.isfinite(com)):
        raise ValueError("com_offset_body_m must be a finite 2-vector")
    offsets = np.asarray([contact.offset_body_m for contact in contacts], dtype=float)
    weight = float(payload_mass_kg * gravity_m_s2)
    matrix = np.vstack(
        [
            np.ones(len(contacts)),
            offsets[:, 1] - com[1],
            offsets[:, 0] - com[0],
        ]
    )
    target = np.asarray([weight, 0.0, 0.0])
    lower = np.asarray([contact.min_normal_force_n for contact in contacts])
    upper = np.asarray([contact.max_normal_force_n for contact in contacts])
    nominal = np.clip(np.full(len(contacts), weight / len(contacts)), lower, upper)
    scale = max(weight, 1.0)
    result = minimize(
        lambda normal: float(np.sum(((normal - nominal) / scale) ** 2)),
        nominal,
        method="SLSQP",
        bounds=list(zip(lower, upper, strict=True)),
        constraints={"type": "eq", "fun": lambda normal: matrix @ normal - target},
        options={"ftol": 1e-12, "maxiter": 500},
    )
    normal = np.asarray(result.x if result.success else nominal, dtype=float)
    residual = matrix @ normal - target
    length_scale = max(
        float(np.max(np.linalg.norm(offsets - com[None, :], axis=1))),
        0.1,
    )
    residual_scale = np.asarray([weight, weight * length_scale, weight * length_scale])
    normalized_residual = residual / residual_scale
    utilization_by_contact = normal / upper
    limiting = int(np.argmax(utilization_by_contact))
    utilization = float(utilization_by_contact[limiting])
    residual_norm = float(np.linalg.norm(normalized_residual, ord=np.inf))
    feasible = bool(result.success and residual_norm <= tolerance)
    return SupportCertificate(
        feasible=feasible,
        normal_forces_n=normal,
        equilibrium_residual=residual,
        normalized_equilibrium_residual=normalized_residual,
        residual_norm=residual_norm,
        utilization=utilization,
        margin=float(1.0 - utilization),
        limiting_robot_id=contacts[limiting].robot_id,
        status="feasible" if feasible else f"infeasible:{result.message}",
    )


__all__ = ["SupportCertificate", "SupportContact", "solve_vertical_support"]
