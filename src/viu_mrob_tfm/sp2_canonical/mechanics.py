"""Planar and supported-load mechanical oracles for SP2.N2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

from .support import SupportCertificate, SupportContact, solve_vertical_support


@dataclass(frozen=True, slots=True)
class MechanicalCertificate:
    feasible: bool
    utilization: float
    forces_n: np.ndarray
    achieved_wrench: np.ndarray
    residual_norm: float
    status: str
    internal_force_ratio: float = float("nan")
    limiting_robot_id: str = "unknown"
    friction_margin: float = float("nan")
    support: SupportCertificate | None = None
    diagnostic_forces_n: np.ndarray | None = None
    diagnostic_achieved_wrench: np.ndarray | None = None
    diagnostic_residual_norm: float = float("nan")


def grasp_matrix_2d(offsets_body_m: np.ndarray) -> np.ndarray:
    """Build the planar grasp matrix mapping contact forces to [Fx,Fy,tau]."""

    offsets = np.asarray(offsets_body_m, dtype=float)
    if (
        offsets.ndim != 2
        or offsets.shape[1] != 2
        or not np.all(np.isfinite(offsets))
    ):
        raise ValueError("offsets_body_m must have shape (n_contacts, 2)")
    matrix = np.zeros((3, 2 * len(offsets)), dtype=float)
    for index, (rx, ry) in enumerate(offsets):
        matrix[0, 2 * index] = 1.0
        matrix[1, 2 * index + 1] = 1.0
        matrix[2, 2 * index] = -ry
        matrix[2, 2 * index + 1] = rx
    return matrix


def certify_planar_wrench(
    offsets_body_m: np.ndarray,
    force_limits_n: np.ndarray,
    desired_wrench: np.ndarray,
    *,
    tolerance: float = 1e-8,
) -> MechanicalCertificate:
    """Minimize maximum component utilization subject to exact wrench balance."""

    limits = np.asarray(force_limits_n, dtype=float)
    wrench = np.asarray(desired_wrench, dtype=float)
    offsets = np.asarray(offsets_body_m, dtype=float)
    if limits.shape != (len(offsets),) or np.any(limits <= 0.0):
        raise ValueError("force_limits_n must be positive with one value per contact")
    if wrench.shape != (3,) or not np.all(np.isfinite(wrench)):
        raise ValueError("desired_wrench must be a finite 3-vector")

    grasp = grasp_matrix_2d(offsets)
    n_force = 2 * len(offsets)
    objective = np.zeros(n_force + 1)
    objective[-1] = 1.0
    equalities = np.zeros((3, n_force + 1))
    equalities[:, :n_force] = grasp

    inequalities: list[np.ndarray] = []
    upper_bounds: list[float] = []
    component_limits = np.repeat(limits, 2)
    for component, limit in enumerate(component_limits):
        positive = np.zeros(n_force + 1)
        positive[component] = 1.0
        positive[-1] = -limit
        negative = np.zeros(n_force + 1)
        negative[component] = -1.0
        negative[-1] = -limit
        inequalities.extend((positive, negative))
        upper_bounds.extend((0.0, 0.0))

    result = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.asarray(upper_bounds),
        A_eq=equalities,
        b_eq=wrench,
        bounds=[(None, None)] * n_force + [(0.0, None)],
        method="highs",
    )
    if not result.success:
        return MechanicalCertificate(
            feasible=False,
            utilization=float("inf"),
            forces_n=np.full((len(offsets), 2), np.nan),
            achieved_wrench=np.full(3, np.nan),
            residual_norm=float("inf"),
            status=f"infeasible:{result.status}",
        )

    forces = np.asarray(result.x[:n_force]).reshape((-1, 2))
    achieved = grasp @ forces.reshape(-1)
    residual = float(np.linalg.norm(achieved - wrench))
    utilization = float(result.x[-1])
    feasible = residual <= tolerance and utilization <= 1.0 + tolerance
    return MechanicalCertificate(
        feasible=feasible,
        utilization=utilization,
        forces_n=forces,
        achieved_wrench=achieved,
        residual_norm=residual,
        status="feasible" if feasible else "force_limit_exceeded",
        internal_force_ratio=float(
            np.linalg.norm(forces.reshape(-1) - np.linalg.pinv(grasp) @ achieved)
            / max(np.linalg.norm(forces), tolerance)
        ),
        limiting_robot_id=f"contact-{int(np.argmax(np.linalg.norm(forces, axis=1))) + 1}",
        friction_margin=float("nan"),
    )


def certify_supported_wrench(
    contacts: list[SupportContact] | tuple[SupportContact, ...],
    payload_mass_kg: float,
    desired_wrench_body: np.ndarray,
    *,
    com_offset_body_m: np.ndarray | tuple[float, float] = (0.0, 0.0),
    friction_faces: int = 16,
    residual_penalty: float = 1_000.0,
    tolerance: float = 1e-7,
    diagnose_infeasible: bool = True,
) -> MechanicalCertificate:
    """Allocate a planar wrench after checking vertical support equilibrium.

    The tangential Coulomb disks are conservatively approximated by an
    inscribed regular polygon. Feasibility and diagnosis are deliberately
    separated: the first LP minimizes utilization under exact wrench balance;
    if the request lies outside the physical set, a second LP minimizes a
    normalized L1 residual with utilization fixed at one.
    """

    if friction_faces < 4 or friction_faces % 2:
        raise ValueError("friction_faces must be an even integer of at least four")
    if residual_penalty <= 0.0:
        raise ValueError("residual_penalty must be strictly positive")
    wrench = np.asarray(desired_wrench_body, dtype=float)
    if wrench.shape != (3,) or not np.all(np.isfinite(wrench)):
        raise ValueError("desired_wrench_body must be a finite 3-vector")
    support = solve_vertical_support(
        contacts,
        payload_mass_kg,
        com_offset_body_m=com_offset_body_m,
        tolerance=tolerance,
    )
    offsets = np.asarray([contact.offset_body_m for contact in contacts], dtype=float)
    if not support.feasible:
        return MechanicalCertificate(
            feasible=False,
            utilization=float("inf"),
            forces_n=np.full((len(contacts), 2), np.nan),
            achieved_wrench=np.full(3, np.nan),
            residual_norm=float("inf"),
            status="support_infeasible",
            limiting_robot_id=support.limiting_robot_id,
            support=support,
        )

    grasp = grasp_matrix_2d(offsets)
    n_force = 2 * len(contacts)
    rho_index = n_force
    n_variables = n_force + 1
    objective = np.zeros(n_variables)
    objective[rho_index] = 1.0
    force_scale = max(float(np.sum([c.max_drive_force_n for c in contacts])), 1.0)
    torque_scale = max(force_scale * max(float(np.max(np.linalg.norm(offsets, axis=1))), 0.1), 1.0)
    wrench_scale = np.asarray([force_scale, force_scale, torque_scale])

    equalities = np.zeros((3, n_variables))
    equalities[:, :n_force] = grasp

    rows: list[np.ndarray] = []
    limits: list[float] = []
    polygon_factor = float(np.cos(np.pi / friction_faces))
    tangential_limits = np.minimum(
        np.asarray([c.max_drive_force_n for c in contacts], dtype=float),
        np.asarray([c.friction_coefficient for c in contacts], dtype=float)
        * support.normal_forces_n,
    )
    for contact_index, limit in enumerate(tangential_limits):
        for angle in np.linspace(0.0, 2.0 * np.pi, friction_faces, endpoint=False):
            row = np.zeros(n_variables)
            row[2 * contact_index : 2 * contact_index + 2] = [np.cos(angle), np.sin(angle)]
            row[rho_index] = -float(limit * polygon_factor)
            rows.append(row)
            limits.append(0.0)

    exact = linprog(
        objective,
        A_ub=np.asarray(rows),
        b_ub=np.asarray(limits),
        A_eq=equalities,
        b_eq=wrench,
        bounds=[(None, None)] * n_force + [(0.0, None)],
        method="highs",
    )

    diagnostic_forces: np.ndarray | None = None
    diagnostic_achieved: np.ndarray | None = None
    diagnostic_residual_norm = float("nan")

    if exact.success:
        forces = np.asarray(exact.x[:n_force]).reshape((-1, 2))
        achieved = grasp @ forces.reshape(-1)
        residual = wrench - achieved
        residual_norm = float(np.linalg.norm(residual / wrench_scale, ord=np.inf))
        norms = np.linalg.norm(forces, axis=1)
        utilization_by_contact = norms / np.maximum(tangential_limits, tolerance)
        limiting = int(np.argmax(utilization_by_contact))
        utilization = float(max(exact.x[rho_index], utilization_by_contact[limiting]))
        projector = np.eye(n_force) - np.linalg.pinv(grasp) @ grasp
        internal = projector @ forces.reshape(-1)
        internal_ratio = float(
            np.linalg.norm(internal) / max(np.linalg.norm(forces), tolerance)
        )
        feasible = bool(utilization <= 1.0 + tolerance and residual_norm <= tolerance)
    else:
        forces = np.full((len(contacts), 2), np.nan)
        achieved = np.full(3, np.nan)
        residual_norm = float("inf")
        limiting = 0
        utilization = float("inf")
        internal_ratio = float("nan")
        feasible = False

    if not feasible and diagnose_infeasible:
        slack_positive = n_force
        slack_negative = n_force + 3
        diagnostic_variables = n_force + 6
        diagnostic_objective = np.zeros(diagnostic_variables)
        diagnostic_objective[slack_positive:slack_negative] = residual_penalty / wrench_scale
        diagnostic_objective[slack_negative:] = residual_penalty / wrench_scale
        diagnostic_equalities = np.zeros((3, diagnostic_variables))
        diagnostic_equalities[:, :n_force] = grasp
        diagnostic_equalities[:, slack_positive:slack_negative] = np.eye(3)
        diagnostic_equalities[:, slack_negative:] = -np.eye(3)
        diagnostic_rows: list[np.ndarray] = []
        for contact_index, limit in enumerate(tangential_limits):
            for angle in np.linspace(0.0, 2.0 * np.pi, friction_faces, endpoint=False):
                row = np.zeros(diagnostic_variables)
                row[2 * contact_index : 2 * contact_index + 2] = [
                    np.cos(angle),
                    np.sin(angle),
                ]
                diagnostic_rows.append(row)
        diagnostic = linprog(
            diagnostic_objective,
            A_ub=np.asarray(diagnostic_rows),
            b_ub=np.repeat(tangential_limits * polygon_factor, friction_faces),
            A_eq=diagnostic_equalities,
            b_eq=wrench,
            bounds=[(None, None)] * n_force + [(0.0, None)] * 6,
            method="highs",
        )
        if diagnostic.success:
            diagnostic_forces = np.asarray(diagnostic.x[:n_force]).reshape((-1, 2))
            diagnostic_achieved = grasp @ diagnostic_forces.reshape(-1)
            diagnostic_residual_norm = float(
                np.linalg.norm((wrench - diagnostic_achieved) / wrench_scale, ord=1)
            )

    if exact.success:
        status = "feasible" if feasible else "wrench_outside_supported_set"
    else:
        status = f"wrench_balance_infeasible:{exact.status}"
    return MechanicalCertificate(
        feasible=feasible,
        utilization=utilization,
        forces_n=forces,
        achieved_wrench=achieved,
        residual_norm=residual_norm,
        status=status,
        internal_force_ratio=internal_ratio,
        limiting_robot_id=contacts[limiting].robot_id,
        friction_margin=float(1.0 - utilization),
        support=support,
        diagnostic_forces_n=diagnostic_forces,
        diagnostic_achieved_wrench=diagnostic_achieved,
        diagnostic_residual_norm=diagnostic_residual_norm,
    )


def aggregate_force_only_feasible(
    force_limits_n: np.ndarray,
    desired_wrench: np.ndarray,
    *,
    tolerance: float = 1e-9,
) -> bool:
    """Necessary-only baseline that discards torque and contact geometry."""

    limits = np.asarray(force_limits_n, dtype=float)
    wrench = np.asarray(desired_wrench, dtype=float)
    if limits.ndim != 1 or wrench.shape != (3,):
        raise ValueError("invalid force limits or wrench")
    return bool(np.linalg.norm(wrench[:2]) <= float(np.sum(limits)) + tolerance)


__all__ = [
    "MechanicalCertificate",
    "aggregate_force_only_feasible",
    "certify_planar_wrench",
    "certify_supported_wrench",
    "grasp_matrix_2d",
]
