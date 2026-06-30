"""Continuous control contracts for V6."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.domain.world import WorldState


Array = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class RobotCommand:
    """Planar velocity commands for all robots."""

    velocity_xy: Array
    source: str = "unknown"

    def __post_init__(self) -> None:
        velocity = np.asarray(self.velocity_xy, dtype=float)
        if velocity.ndim != 2 or velocity.shape[1] != 2:
            raise ValueError("RobotCommand.velocity_xy must have shape (N, 2).")
        object.__setattr__(self, "velocity_xy", velocity)


class BaseContinuousController(ABC):
    """Interface for controllers consuming an assignment and world state."""

    name: str = "base"

    @abstractmethod
    def compute(self, world: WorldState, assignment: Assignment) -> RobotCommand:
        """Compute one command per robot."""
