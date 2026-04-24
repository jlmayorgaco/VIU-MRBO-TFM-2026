"""State dataclasses used throughout the simulation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


def _vector2(values: list[float] | NDArray[np.float64] | tuple[float, float]) -> NDArray[np.float64]:
    """Normalize array-like inputs into a 2D float vector."""

    array = np.asarray(values, dtype=float)
    if array.shape != (2,):
        msg = f"Expected a 2D vector, received shape {array.shape!r}."
        raise ValueError(msg)
    return array


@dataclass(slots=True)
class AGVState:
    """Kinematic state placeholder for a single AGV."""

    position: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    velocity: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    heading: float = 0.0

    def __post_init__(self) -> None:
        self.position = _vector2(self.position)
        self.velocity = _vector2(self.velocity)


@dataclass(slots=True)
class LoadState:
    """Planar state placeholder for the transported load."""

    position: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    velocity: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    yaw: float = 0.0
    yaw_rate: float = 0.0

    def __post_init__(self) -> None:
        self.position = _vector2(self.position)
        self.velocity = _vector2(self.velocity)


@dataclass(slots=True)
class SystemState:
    """Joint state container passed to controllers and estimators."""

    agv_states: list[AGVState]
    load_state: LoadState
    time: float = 0.0

    @property
    def agent_count(self) -> int:
        """Return the number of AGVs in the system."""

        return len(self.agv_states)
