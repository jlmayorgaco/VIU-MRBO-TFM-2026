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


def plot_trajectories_with_load(
    agv_trajectories: NDArray[np.float64],
    load_trajectory: NDArray[np.float64],
    load_coupled: NDArray[np.bool_] | None = None,
    output_path: str | Path | None = None,
) -> Figure:
    """Plot AGV trajectories together with the passive load trajectory.

    The load is shown as a black dashed line.  When *load_coupled* is
    provided, the first coupling event is marked with a filled diamond (◆)
    and any decoupling events with an open circle (○), illustrating that
    the load only moves once the coalition is formed.

    Parameters
    ----------
    agv_trajectories:
        Array of shape (steps, n_agents, 2).
    load_trajectory:
        Array of shape (steps, 2).
    load_coupled:
        Boolean array of shape (steps,) indicating coupling state per step.
    output_path:
        If provided, save the figure to this path (PNG, PDF, …).
    """

    agv_data = np.asarray(agv_trajectories, dtype=float)
    load_data = np.asarray(load_trajectory, dtype=float)

    figure, axis = plt.subplots(figsize=(8, 6))

    # AGV trajectories
    for agent_index in range(agv_data.shape[1]):
        axis.plot(
            agv_data[:, agent_index, 0],
            agv_data[:, agent_index, 1],
            linewidth=1.2,
            label=f"AGV {agent_index + 1}",
        )

    # Load trajectory
    axis.plot(
        load_data[:, 0],
        load_data[:, 1],
        color="black",
        linestyle="--",
        linewidth=1.8,
        label="Carga (cinemática)",
        zorder=5,
    )

    # Coupling / decoupling events
    if load_coupled is not None:
        coupled = np.asarray(load_coupled, dtype=bool)
        # First coupling event
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
        # Decoupling events
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
    axis.set_title("Trayectorias de AGVs y carga pasiva cinemática")
    axis.legend(loc="best", fontsize=8)
    axis.grid(True, alpha=0.3)
    figure.tight_layout()

    if output_path is not None:
        figure.savefig(Path(output_path), dpi=200, bbox_inches="tight")
    return figure
