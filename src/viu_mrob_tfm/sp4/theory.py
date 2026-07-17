"""Small, auditable mathematical core for the SP4 manuscript claims."""

from __future__ import annotations

import numpy as np


def pairwise_game_potential(
    preferences: np.ndarray,
    costs: np.ndarray,
    features: np.ndarray,
    *,
    congestion_weight: float,
    regularization: float,
) -> float:
    """Return the convex snapshot potential used by the SP4 liveness game."""

    rho = np.asarray(preferences, dtype=float)
    c = np.asarray(costs, dtype=float)
    b = np.asarray(features, dtype=float)
    occupancy = np.einsum("ia,iar->r", rho, b, optimize=True)
    return float(
        np.sum(c * rho)
        + 0.5 * congestion_weight * float(occupancy @ occupancy)
        + 0.5 * regularization * float(np.sum(rho * rho))
    )


def pairwise_player_cost(
    preferences: np.ndarray,
    costs: np.ndarray,
    features: np.ndarray,
    player: int,
    *,
    congestion_weight: float,
    regularization: float,
) -> float:
    """Return the scalar cost whose finite unilateral differences match the potential."""

    rho = np.asarray(preferences, dtype=float)
    c = np.asarray(costs, dtype=float)
    b = np.asarray(features, dtype=float)
    if not 0 <= int(player) < rho.shape[0]:
        raise IndexError("player index out of range")
    occupancy = np.einsum("ia,iar->r", rho, b, optimize=True)
    return float(
        c[int(player)] @ rho[int(player)]
        + 0.5 * congestion_weight * float(occupancy @ occupancy)
        + 0.5
        * regularization
        * float(rho[int(player)] @ rho[int(player)])
    )


def pairwise_game_gradient(
    preferences: np.ndarray,
    costs: np.ndarray,
    features: np.ndarray,
    *,
    congestion_weight: float,
    regularization: float,
) -> np.ndarray:
    """Return the gradient of :func:`pairwise_game_potential`."""

    rho = np.asarray(preferences, dtype=float)
    c = np.asarray(costs, dtype=float)
    b = np.asarray(features, dtype=float)
    occupancy = np.einsum("ia,iar->r", rho, b, optimize=True)
    return (
        c
        + congestion_weight
        * np.einsum("iar,r->ia", b, occupancy, optimize=True)
        + regularization * rho
    )


def pairwise_game_hessian(
    features: np.ndarray,
    *,
    congestion_weight: float,
    regularization: float,
) -> np.ndarray:
    """Return the constant Hessian in flattened preference coordinates."""

    b = np.asarray(features, dtype=float)
    matrix = b.reshape((-1, b.shape[-1]))
    return (
        congestion_weight * matrix @ matrix.T
        + regularization * np.eye(matrix.shape[0])
    )


def closed_loop_energy_derivative(
    velocity: np.ndarray,
    physical_damping: np.ndarray,
    derivative_gain: np.ndarray,
    wrench_residual: np.ndarray | None = None,
) -> float:
    """Evaluate the storage derivative for the local planar pose loop.

    The residual is achieved minus desired wrench.  A zero residual recovers
    the exact-wrench dissipation identity used in the SP4 proposition.
    """

    qd = np.asarray(velocity, dtype=float)
    damping = np.asarray(physical_damping, dtype=float)
    gain = np.asarray(derivative_gain, dtype=float)
    residual = (
        np.zeros_like(qd)
        if wrench_residual is None
        else np.asarray(wrench_residual, dtype=float)
    )
    return float(-qd @ (damping + gain) @ qd + qd @ residual)


def dissipation_upper_bound(
    velocity: np.ndarray,
    physical_damping: np.ndarray,
    derivative_gain: np.ndarray,
    wrench_residual: np.ndarray,
) -> float:
    """Young-inequality upper bound for the disturbed storage derivative."""

    qd = np.asarray(velocity, dtype=float)
    residual = np.asarray(wrench_residual, dtype=float)
    damping = np.asarray(physical_damping, dtype=float) + np.asarray(
        derivative_gain, dtype=float
    )
    minimum = float(np.min(np.linalg.eigvalsh(0.5 * (damping + damping.T))))
    if minimum <= 0.0:
        raise ValueError("the total damping matrix must be positive definite")
    return float(
        -0.5 * minimum * float(qd @ qd)
        + 0.5 / minimum * float(residual @ residual)
    )


__all__ = [
    "closed_loop_energy_derivative",
    "dissipation_upper_bound",
    "pairwise_game_gradient",
    "pairwise_game_hessian",
    "pairwise_game_potential",
    "pairwise_player_cost",
]
