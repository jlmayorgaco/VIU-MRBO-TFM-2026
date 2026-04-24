"""Error plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.typing import NDArray


def plot_error_series(
    time: NDArray[np.float64],
    errors: NDArray[np.float64],
    output_path: str | Path | None = None,
) -> Figure:
    """Plot a scalar error trace against time."""

    figure, axis = plt.subplots()
    axis.plot(np.asarray(time, dtype=float), np.asarray(errors, dtype=float), color="tab:orange")
    axis.set_xlabel("Tiempo [s]")
    axis.set_ylabel("Error")
    axis.set_title("Serie temporal del error")
    axis.grid(True, alpha=0.3)
    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure
