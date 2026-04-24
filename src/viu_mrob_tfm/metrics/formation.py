"""Formation tracking metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def formation_error(
    actual_offsets: NDArray[np.float64],
    desired_offsets: NDArray[np.float64],
) -> float:
    """Return the root-mean-square formation error."""

    actual_array = np.asarray(actual_offsets, dtype=float)
    desired_array = np.asarray(desired_offsets, dtype=float)
    difference = actual_array - desired_array
    return float(np.sqrt(np.mean(difference**2)))
