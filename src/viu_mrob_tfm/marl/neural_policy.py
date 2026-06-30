"""Neural shared-actor policy used by the CTDE MARL baseline.

The actor is deliberately small so that it remains reproducible inside the TFM
repository: a shared linear term plus a one-hidden-layer residual MLP. Training
can use centralized episode returns, but execution only needs local pair
features.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .shared_policy import DEFAULT_MARL_CTDE_WEIGHTS, MARL_CTDE_FEATURE_NAMES


FEATURE_DIM = len(MARL_CTDE_FEATURE_NAMES)
DEFAULT_HIDDEN_DIM = 8


@dataclass(frozen=True)
class NeuralPolicyParams:
    """Unpacked parameters for the shared residual actor."""

    linear: np.ndarray
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: float
    idle_score: float


def neural_param_size(hidden_dim: int = DEFAULT_HIDDEN_DIM) -> int:
    """Return flattened parameter count, including the idle score."""

    return FEATURE_DIM + hidden_dim * FEATURE_DIM + hidden_dim + hidden_dim + 1 + 1


def initial_neural_vector(
    linear_weights: Sequence[float] | None = None,
    *,
    hidden_dim: int = DEFAULT_HIDDEN_DIM,
    idle_score: float = 0.0,
) -> np.ndarray:
    """Create an actor initialized as the linear CTDE policy plus zero residual."""

    linear = np.asarray(linear_weights or DEFAULT_MARL_CTDE_WEIGHTS, dtype=float)
    if linear.shape != (FEATURE_DIM,):
        msg = f"Expected {FEATURE_DIM} linear weights, got {linear.shape}."
        raise ValueError(msg)
    vector = np.zeros(neural_param_size(hidden_dim), dtype=float)
    vector[:FEATURE_DIM] = linear
    vector[-1] = float(idle_score)
    return vector


def unpack_neural_vector(raw: Sequence[float] | np.ndarray, hidden_dim: int = DEFAULT_HIDDEN_DIM) -> NeuralPolicyParams:
    """Validate and unpack a flat actor vector."""

    vector = np.asarray(raw, dtype=float)
    expected = neural_param_size(hidden_dim)
    if vector.shape != (expected,):
        msg = f"Neural CTDE policy expects {expected} parameters, got {vector.shape}."
        raise ValueError(msg)
    if not np.all(np.isfinite(vector)):
        msg = "Neural CTDE policy parameters must be finite."
        raise ValueError(msg)
    cursor = 0
    linear = vector[cursor : cursor + FEATURE_DIM]
    cursor += FEATURE_DIM
    w1 = vector[cursor : cursor + hidden_dim * FEATURE_DIM].reshape(hidden_dim, FEATURE_DIM)
    cursor += hidden_dim * FEATURE_DIM
    b1 = vector[cursor : cursor + hidden_dim]
    cursor += hidden_dim
    w2 = vector[cursor : cursor + hidden_dim]
    cursor += hidden_dim
    b2 = float(vector[cursor])
    cursor += 1
    idle_score = float(vector[cursor])
    return NeuralPolicyParams(linear=linear, w1=w1, b1=b1, w2=w2, b2=b2, idle_score=idle_score)


def score_neural_features(features: np.ndarray, params: NeuralPolicyParams) -> float:
    """Evaluate the residual shared actor on one robot-load feature vector."""

    hidden = np.tanh(params.w1 @ features + params.b1)
    residual = float(params.w2 @ hidden + params.b2)
    return float(params.linear @ features + residual)
