"""Common planar payload dynamics used between N1 and N2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _vector3(values: np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be a finite 3-vector")
    return vector


@dataclass(frozen=True, slots=True)
class PlanarPayload:
    """Rigid planar payload model in SI units."""

    mass_kg: float
    yaw_inertia_kg_m2: float
    linear_damping_n_s_m: float = 0.0
    yaw_damping_n_m_s_rad: float = 0.0
    gravity_m_s2: float = 9.81

    def __post_init__(self) -> None:
        if self.mass_kg <= 0.0 or self.yaw_inertia_kg_m2 <= 0.0:
            raise ValueError("mass and yaw inertia must be strictly positive")
        if min(self.linear_damping_n_s_m, self.yaw_damping_n_m_s_rad) < 0.0:
            raise ValueError("damping must be non-negative")
        if self.gravity_m_s2 <= 0.0:
            raise ValueError("gravity must be strictly positive")

    @property
    def mass_matrix(self) -> np.ndarray:
        return np.diag([self.mass_kg, self.mass_kg, self.yaw_inertia_kg_m2])

    @property
    def damping_matrix(self) -> np.ndarray:
        return np.diag(
            [
                self.linear_damping_n_s_m,
                self.linear_damping_n_s_m,
                self.yaw_damping_n_m_s_rad,
            ]
        )


def required_wrench_world(
    payload: PlanarPayload,
    acceleration_world: np.ndarray,
    twist_world: np.ndarray,
    external_wrench_world: np.ndarray | None = None,
) -> np.ndarray:
    """Return the contact wrench required by ``M a + D nu - w_ext``."""

    acceleration = _vector3(acceleration_world, "acceleration_world")
    twist = _vector3(twist_world, "twist_world")
    external = (
        np.zeros(3)
        if external_wrench_world is None
        else _vector3(external_wrench_world, "external_wrench_world")
    )
    return payload.mass_matrix @ acceleration + payload.damping_matrix @ twist - external


def wrench_world_to_body(wrench_world: np.ndarray, payload_yaw_rad: float) -> np.ndarray:
    """Express a planar world-frame wrench in the payload frame."""

    wrench = _vector3(wrench_world, "wrench_world")
    c, s = np.cos(float(payload_yaw_rad)), np.sin(float(payload_yaw_rad))
    rotation_world_from_body = np.asarray([[c, -s], [s, c]])
    transformed = np.empty(3, dtype=float)
    transformed[:2] = rotation_world_from_body.T @ wrench[:2]
    transformed[2] = wrench[2]
    return transformed


def required_wrench_body(
    payload: PlanarPayload,
    acceleration_world: np.ndarray,
    twist_world: np.ndarray,
    payload_yaw_rad: float,
    external_wrench_world: np.ndarray | None = None,
) -> np.ndarray:
    """Compute the required contact wrench and express it in body coordinates."""

    return wrench_world_to_body(
        required_wrench_world(
            payload,
            acceleration_world,
            twist_world,
            external_wrench_world,
        ),
        payload_yaw_rad,
    )


__all__ = [
    "PlanarPayload",
    "required_wrench_body",
    "required_wrench_world",
    "wrench_world_to_body",
]
