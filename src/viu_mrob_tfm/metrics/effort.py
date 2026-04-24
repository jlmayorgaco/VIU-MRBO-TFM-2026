"""Control effort metrics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def control_effort(control_signal: NDArray[np.float64]) -> float:
    """Return an aggregate effort value for a control signal."""

    signal = np.asarray(control_signal, dtype=float)
    return float(np.sum(np.linalg.norm(signal, axis=-1)))
