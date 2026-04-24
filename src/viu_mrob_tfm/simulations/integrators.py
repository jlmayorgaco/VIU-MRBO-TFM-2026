"""Numerical integration helpers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def euler_step(
    value: NDArray[np.float64],
    derivative: NDArray[np.float64],
    dt: float,
) -> NDArray[np.float64]:
    """Apply a single explicit Euler integration step."""

    return np.asarray(value, dtype=float) + dt * np.asarray(derivative, dtype=float)
