"""Robot domain models for the V6 OOP architecture."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


Array = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class BatteryModel:
    """Minimal normalized battery model used by continuous field terms."""

    capacity_wh: float = 500.0
    reserve_fraction: float = 0.15
    discharge_per_meter: float = 0.01

    def is_returnable(self, charge_fraction: float, estimated_return_distance: float) -> bool:
        required = self.reserve_fraction + self.discharge_per_meter * estimated_return_distance
        return charge_fraction >= min(required, 1.0)


@dataclass(frozen=True, slots=True)
class CapacityModel:
    """Mechanical capacity limits for a heterogeneous robot."""

    payload_kg: float = 1.0
    force_limit_n: float = 10.0
    torque_limit_nm: float = 2.0

    def scalar_margin(self, demand_kg: float) -> float:
        return self.payload_kg - demand_kg


@dataclass(frozen=True, slots=True)
class RobotSpec:
    """Static robot parameters shared across scenarios and controllers."""

    identifier: str
    capacity: CapacityModel = field(default_factory=CapacityModel)
    battery: BatteryModel = field(default_factory=BatteryModel)
    max_speed: float = 0.65
    max_angular_speed: float = 2.5
    wheel_radius: float = 0.0975
    axle_length: float = 0.33


@dataclass(slots=True)
class RobotRuntimeState:
    """Mutable robot state for the OOP simulation contracts."""

    spec: RobotSpec
    position: Array = field(default_factory=lambda: np.zeros(2, dtype=float))
    heading: float = 0.0
    battery_fraction: float = 1.0
    active: bool = True

    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=float)
        if self.position.shape != (2,):
            raise ValueError("RobotRuntimeState.position must be a 2D vector.")
        self.battery_fraction = float(np.clip(self.battery_fraction, 0.0, 1.0))

    @property
    def identifier(self) -> str:
        return self.spec.identifier

    def effective_capacity(self, demand_kg: float, return_distance: float = 0.0) -> float:
        if not self.active:
            return 0.0
        if not self.spec.battery.is_returnable(self.battery_fraction, return_distance):
            return 0.0
        return max(0.0, min(self.spec.capacity.payload_kg, demand_kg))
