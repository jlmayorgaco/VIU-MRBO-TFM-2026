"""Trajectory plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from numpy.typing import NDArray


def plot_trajectories(
    trajectories: NDArray[np.float64],
    output_path: str | Path | None = None,
) -> Figure:
    """Create a simple 2D trajectory plot for multiple AGVs."""

    data = np.asarray(trajectories, dtype=float)
    figure, axis = plt.subplots()
    for agent_index in range(data.shape[1]):
        axis.plot(data[:, agent_index, 0], data[:, agent_index, 1], label=f"AGV {agent_index + 1}")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title("Trayectorias cooperativas")
    axis.legend(loc="best")
    axis.grid(True, alpha=0.3)
    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure
