"""Shared-parameter CTDE policy primitives for MARL comparisons.

The thesis method remains Smith-QR. This module provides a real learned
competitor: one common action-value vector is trained from multi-robot episode
returns and is executed independently by every robot from local load features.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]

MARL_CTDE_FEATURE_NAMES: tuple[str, ...] = (
    "bias",
    "reward",
    "price",
    "deficit",
    "age",
    "closeness",
    "support",
    "transport",
    "stickiness",
    "quorum_pressure",
)

DEFAULT_MARL_CTDE_WEIGHTS: tuple[float, ...] = (
    -0.15,
    1.10,
    0.35,
    1.25,
    0.25,
    1.00,
    0.12,
    0.65,
    0.30,
    0.55,
)


def coerce_policy_weights(raw: Sequence[float] | Array | None) -> Array:
    """Return a finite weight vector with the declared CTDE feature dimension."""

    if raw is None or len(raw) == 0:
        return np.asarray(DEFAULT_MARL_CTDE_WEIGHTS, dtype=float)
    weights = np.asarray(raw, dtype=float)
    expected = len(MARL_CTDE_FEATURE_NAMES)
    if weights.shape != (expected,):
        msg = f"MARL CTDE policy expects {expected} weights, got {weights.shape}."
        raise ValueError(msg)
    if not np.all(np.isfinite(weights)):
        msg = "MARL CTDE policy weights must be finite."
        raise ValueError(msg)
    return weights


def build_pair_features(
    *,
    reward: float,
    max_price: float,
    price: float,
    target: int,
    assigned: int,
    age: float,
    duration: float,
    distance: float,
    local_support: float,
    robot_count: int,
    is_transport: bool,
    is_sticky: bool,
) -> Array:
    """Build the local robot-load feature vector used by the shared policy."""

    normalized_reward = reward / max(max_price, 1.0e-9)
    normalized_price = price / max(max_price, 1.0e-9)
    deficit = max(0.0, float(target - assigned))
    deficit_ratio = deficit / max(float(target), 1.0)
    age_ratio = min(max(age, 0.0) / max(duration, 1.0), 1.0)
    closeness = 1.0 / (1.0 + max(distance, 0.0))
    support_ratio = max(local_support, 0.0) / max(float(robot_count), 1.0)
    quorum_pressure = deficit / max(float(robot_count - assigned), 1.0)
    return np.asarray(
        [
            1.0,
            normalized_reward,
            normalized_price,
            deficit_ratio,
            age_ratio,
            closeness,
            support_ratio,
            1.0 if is_transport else 0.0,
            1.0 if is_sticky else 0.0,
            quorum_pressure,
        ],
        dtype=float,
    )


def build_global_features(
    *,
    robot_count: int,
    active_count: int,
    available_count: int,
    mean_deficit: float,
    max_deficit: float,
    mean_price: float,
    mean_age_ratio: float,
    mean_distance_ratio: float,
) -> Array:
    """Build a compact centralized critic feature vector for CTDE analyses."""

    scale = max(float(robot_count), 1.0)
    return np.asarray(
        [
            1.0,
            float(active_count) / scale,
            float(available_count) / scale,
            max(mean_deficit, 0.0),
            max(max_deficit, 0.0),
            max(mean_price, 0.0),
            min(max(mean_age_ratio, 0.0), 1.0),
            min(max(mean_distance_ratio, 0.0), 1.0),
        ],
        dtype=float,
    )
