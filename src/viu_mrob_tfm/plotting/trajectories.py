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
    """Create a simple 2D trajectory plot for multiple AMRs."""

    data = np.asarray(trajectories, dtype=float)
    figure, axis = plt.subplots()
    for agent_index in range(data.shape[1]):
        axis.plot(data[:, agent_index, 0], data[:, agent_index, 1], label=f"AMR {agent_index + 1}")
    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title("Trayectorias cooperativas")
    axis.legend(loc="best")
    axis.grid(True, alpha=0.3)
    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure


def plot_trajectories_with_load(
    amr_trajectories: NDArray[np.float64],
    load_trajectory: NDArray[np.float64],
    load_coupled: NDArray[np.bool_] | None = None,
    output_path: str | Path | None = None,
) -> Figure:
    """Plot AMR trajectories together with the passive load trajectory.

    The load is shown as a black dashed line. When *load_coupled* is
    provided, the first coupling event is marked with a filled diamond and
    decoupling events with an open circle.
    """

    amr_data = np.asarray(amr_trajectories, dtype=float)
    load_data = np.asarray(load_trajectory, dtype=float)

    figure, axis = plt.subplots(figsize=(8, 6))

    for agent_index in range(amr_data.shape[1]):
        axis.plot(
            amr_data[:, agent_index, 0],
            amr_data[:, agent_index, 1],
            linewidth=1.2,
            label=f"AMR {agent_index + 1}",
        )

    axis.plot(
        load_data[:, 0],
        load_data[:, 1],
        color="black",
        linestyle="--",
        linewidth=1.8,
        label="Carga cinematica",
        zorder=5,
    )

    if load_coupled is not None:
        coupled = np.asarray(load_coupled, dtype=bool)
        coupling_indices = np.where(np.diff(coupled.astype(int)) > 0)[0] + 1
        for idx in coupling_indices:
            axis.scatter(
                load_data[idx, 0],
                load_data[idx, 1],
                marker="D",
                s=80,
                color="black",
                zorder=6,
                label="Acoplamiento" if idx == coupling_indices[0] else None,
            )
        decoupling_indices = np.where(np.diff(coupled.astype(int)) < 0)[0] + 1
        for idx in decoupling_indices:
            axis.scatter(
                load_data[idx, 0],
                load_data[idx, 1],
                marker="o",
                s=80,
                facecolors="white",
                edgecolors="black",
                linewidths=1.5,
                zorder=6,
                label="Desacoplamiento" if idx == decoupling_indices[0] else None,
            )

    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title("Trayectorias de AMRs y carga pasiva cinematica")
    axis.legend(loc="best", fontsize=8)
    axis.grid(True, alpha=0.3)
    figure.tight_layout()

    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure
