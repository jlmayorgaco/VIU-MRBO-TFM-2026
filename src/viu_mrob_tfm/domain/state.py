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
class AMRState:
    """Kinematic state placeholder for a single autonomous mobile robot."""

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


AGVState = AMRState


@dataclass(slots=True, init=False)
class SystemState:
    """Joint state container passed to controllers and estimators."""

    amr_states: list[AMRState]
    load_state: LoadState
    time: float = 0.0

    def __init__(
        self,
        amr_states: list[AMRState] | None = None,
        load_state: LoadState | None = None,
        time: float = 0.0,
        agv_states: list[AMRState] | None = None,
    ) -> None:
        states = amr_states if amr_states is not None else agv_states
        if states is None:
            msg = "SystemState requires amr_states."
            raise TypeError(msg)
        if load_state is None:
            msg = "SystemState requires load_state."
            raise TypeError(msg)
        self.amr_states = states
        self.load_state = load_state
        self.time = time

    @property
    def agent_count(self) -> int:
        """Return the number of mobile robots in the system."""

        return len(self.amr_states)

    @property
    def agv_states(self) -> list[AMRState]:
        """Legacy alias for older code and saved notebooks."""

        return self.amr_states

    @agv_states.setter
    def agv_states(self, value: list[AMRState]) -> None:
        self.amr_states = value
