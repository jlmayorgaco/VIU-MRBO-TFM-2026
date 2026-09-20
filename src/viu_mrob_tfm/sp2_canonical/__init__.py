"""Executable models for SP2 cooperative transport.

The primary branch is a supported planar load with 2.5-D contact checks. The
caging branch remains a resolution-dependent extension. Neither substitutes
for hardware validation.
"""

from .caging import CagingResult, verify_grid_caging
from .kinematics import (
    DifferentialDrive,
    FormationCertificate,
    RobotKinematicCertificate,
    anchor_kinematics,
    certify_formation_twist,
)
from .mechanics import MechanicalCertificate, certify_planar_wrench, grasp_matrix_2d
from .dynamics import PlanarPayload, required_wrench_body, required_wrench_world
from .mechanics import certify_supported_wrench
from .support import SupportCertificate, SupportContact, solve_vertical_support

__all__ = [
    "CagingResult",
    "DifferentialDrive",
    "FormationCertificate",
    "MechanicalCertificate",
    "PlanarPayload",
    "RobotKinematicCertificate",
    "SupportCertificate",
    "SupportContact",
    "anchor_kinematics",
    "certify_formation_twist",
    "certify_planar_wrench",
    "certify_supported_wrench",
    "grasp_matrix_2d",
    "required_wrench_body",
    "required_wrench_world",
    "solve_vertical_support",
    "verify_grid_caging",
]
