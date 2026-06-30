"""World-level domain models for V6 scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.domain.robot import RobotRuntimeState
from viu_mrob_tfm.domain.load import LoadSpec


Array = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class Obstacle:
    """Circular obstacle used by navigation and safety fields."""

    center: Array
    radius: float = 0.35
    influence_radius: float = 1.25

    def __post_init__(self) -> None:
        center = np.asarray(self.center, dtype=float)
        if center.shape != (2,):
            raise ValueError("Obstacle.center must be a 2D vector.")
        object.__setattr__(self, "center", center)


@dataclass(frozen=True, slots=True)
class WarehouseMap:
    """Static map definition for warehouse-like scenarios."""

    size_m: float = 12.0
    obstacles: tuple[Obstacle, ...] = ()


@dataclass(slots=True)
class WorldState:
    """Simulation state consumed by allocators and controllers."""

    robots: list[RobotRuntimeState]
    loads: list[LoadSpec]
    map: WarehouseMap = field(default_factory=WarehouseMap)
    time_s: float = 0.0

    @property
    def robot_positions(self) -> Array:
        if not self.robots:
            return np.zeros((0, 2), dtype=float)
        return np.vstack([robot.position for robot in self.robots])

    @property
    def active_robot_count(self) -> int:
        return sum(1 for robot in self.robots if robot.active)
