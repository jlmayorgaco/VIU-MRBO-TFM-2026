"""Tracking error metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def tracking_error_series(
    actual: NDArray[np.float64],
    reference: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Return the Euclidean tracking error at each sample."""

    actual_array = np.asarray(actual, dtype=float)
    reference_array = np.asarray(reference, dtype=float)
    return np.linalg.norm(actual_array - reference_array, axis=-1)


def trajectory_tracking_error(
    actual: NDArray[np.float64],
    reference: NDArray[np.float64],
) -> float:
    """Return the mean tracking error across all samples."""

    return float(np.mean(tracking_error_series(actual, reference)))
