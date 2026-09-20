"""Typed data contracts for the SP1-GEO benchmark."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

SignalName = Literal["scalar_capacity", "marginal_physical"]
ClosureStage = Literal["RAW", "CERTIFIED", "RECOVERED"]

PHYSICAL_RESOURCE_NAMES = (
    "effective_payload",
    "aligned_force_x",
    "aligned_force_y",
    "positive_torque",
    "negative_torque",
    "battery_return_margin",
    "reliability",
)


def _vector(value: Any, length: int, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (length,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite vector with shape ({length},).")
    return array


@dataclass(frozen=True, slots=True)
class ContactSlot:
    """One planar, unilateral contact role attached to a load."""

    identifier: str
    offset_xy_m: np.ndarray
    direction_xy: np.ndarray
    role: str
    max_force_n: float

    def __post_init__(self) -> None:
        offset = _vector(self.offset_xy_m, 2, "offset_xy_m")
        direction = _vector(self.direction_xy, 2, "direction_xy")
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-12:
            raise ValueError("direction_xy must be nonzero.")
        if not math.isfinite(self.max_force_n) or self.max_force_n <= 0.0:
            raise ValueError("max_force_n must be positive.")
        object.__setattr__(self, "offset_xy_m", offset)
        object.__setattr__(self, "direction_xy", direction / norm)


@dataclass(frozen=True, slots=True)
class GeoRobot:
    """Robot state available to SP1 while the physical world is frozen."""

    identifier: str
    pose_xytheta: np.ndarray
    payload_kg: float
    force_limit_n: float
    torque_limit_nm: float
    battery_wh: float
    safe_battery_wh: float
    max_speed_mps: float
    reliability: float
    compatible_loads: tuple[int, ...]
    compatible_roles: tuple[str, ...]
    failed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "pose_xytheta", _vector(self.pose_xytheta, 3, "pose_xytheta"))
        positives = {
            "payload_kg": self.payload_kg,
            "force_limit_n": self.force_limit_n,
            "torque_limit_nm": self.torque_limit_nm,
            "battery_wh": self.battery_wh,
            "max_speed_mps": self.max_speed_mps,
        }
        if any(not math.isfinite(v) or v <= 0.0 for v in positives.values()):
            raise ValueError(f"Robot positive fields are invalid: {positives}")
        if not 0.0 <= self.safe_battery_wh < self.battery_wh:
            raise ValueError("safe_battery_wh must be in [0, battery_wh).")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be in [0, 1].")


@dataclass(frozen=True, slots=True)
class GeoLoad:
    """Frozen load/task model used by coalition formation."""

    identifier: str
    origin_xy_m: np.ndarray
    destination_xy_m: np.ndarray
    mass_kg: float
    shape: str
    dimensions_m: np.ndarray
    com_offset_xy_m: np.ndarray
    priority_value: float
    deadline_s: float
    min_capacity_kg: float
    max_capacity_kg: float
    min_coalition_size: int
    required_wrench: np.ndarray
    wrench_tolerance: float
    route_turn_rad: float
    slots: tuple[ContactSlot, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "origin_xy_m", _vector(self.origin_xy_m, 2, "origin_xy_m"))
        object.__setattr__(
            self, "destination_xy_m", _vector(self.destination_xy_m, 2, "destination_xy_m")
        )
        object.__setattr__(self, "dimensions_m", _vector(self.dimensions_m, 2, "dimensions_m"))
        object.__setattr__(
            self, "com_offset_xy_m", _vector(self.com_offset_xy_m, 2, "com_offset_xy_m")
        )
        object.__setattr__(
            self, "required_wrench", _vector(self.required_wrench, 3, "required_wrench")
        )
        positives = (
            self.mass_kg,
            self.priority_value,
            self.deadline_s,
            self.min_capacity_kg,
            self.max_capacity_kg,
            self.wrench_tolerance,
        )
        if any(not math.isfinite(v) or v <= 0.0 for v in positives):
            raise ValueError("Load scalar fields must be finite and positive.")
        if self.max_capacity_kg < self.min_capacity_kg:
            raise ValueError("max_capacity_kg cannot be below min_capacity_kg.")
        if self.min_coalition_size < 1:
            raise ValueError("min_coalition_size must be positive.")
        if not self.slots:
            raise ValueError("Every load requires at least one slot.")
        slot_ids = [slot.identifier for slot in self.slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("Slot identifiers must be unique within a load.")


@dataclass(frozen=True, slots=True)
class GeoWorld:
    """Paired experimental unit shared unchanged by every method."""

    family: str
    seed: int
    robots: tuple[GeoRobot, ...]
    loads: tuple[GeoLoad, ...]
    communication_adjacency: np.ndarray
    map_size_m: np.ndarray
    demand_pressure: float
    scenario_parameters: dict[str, Any] = field(default_factory=dict)
    world_hash: str = ""

    def __post_init__(self) -> None:
        if not self.robots or not self.loads:
            raise ValueError("A world needs at least one robot and one load.")
        adjacency = np.asarray(self.communication_adjacency, dtype=bool)
        n = len(self.robots)
        if adjacency.shape != (n, n):
            raise ValueError("communication_adjacency has the wrong shape.")
        if not np.array_equal(adjacency, adjacency.T):
            raise ValueError("The communication graph must be undirected.")
        np.fill_diagonal(adjacency, False)
        object.__setattr__(self, "communication_adjacency", adjacency)
        object.__setattr__(self, "map_size_m", _vector(self.map_size_m, 2, "map_size_m"))
        if not math.isfinite(self.demand_pressure) or self.demand_pressure <= 0.0:
            raise ValueError("demand_pressure must be positive.")
        if not self.world_hash:
            payload = {
                "family": self.family,
                "seed": int(self.seed),
                "robots": [
                    {
                        "id": robot.identifier,
                        "pose": robot.pose_xytheta.tolist(),
                        "payload": robot.payload_kg,
                        "force": robot.force_limit_n,
                        "torque": robot.torque_limit_nm,
                        "battery": robot.battery_wh,
                        "safe": robot.safe_battery_wh,
                        "speed": robot.max_speed_mps,
                        "reliability": robot.reliability,
                        "loads": robot.compatible_loads,
                        "roles": robot.compatible_roles,
                        "failed": robot.failed,
                    }
                    for robot in self.robots
                ],
                "loads": [
                    {
                        "id": load.identifier,
                        "origin": load.origin_xy_m.tolist(),
                        "destination": load.destination_xy_m.tolist(),
                        "mass": load.mass_kg,
                        "shape": load.shape,
                        "dimensions": load.dimensions_m.tolist(),
                        "com": load.com_offset_xy_m.tolist(),
                        "value": load.priority_value,
                        "deadline": load.deadline_s,
                        "lower": load.min_capacity_kg,
                        "upper": load.max_capacity_kg,
                        "minimum": load.min_coalition_size,
                        "wrench": load.required_wrench.tolist(),
                        "tol": load.wrench_tolerance,
                        "turn": load.route_turn_rad,
                        "slots": [
                            {
                                "id": slot.identifier,
                                "offset": slot.offset_xy_m.tolist(),
                                "direction": slot.direction_xy.tolist(),
                                "role": slot.role,
                                "max_force": slot.max_force_n,
                            }
                            for slot in load.slots
                        ],
                    }
                    for load in self.loads
                ],
                "adjacency": adjacency.astype(int).tolist(),
                "map_size": self.map_size_m.tolist(),
                "pressure": self.demand_pressure,
                "parameters": self.scenario_parameters,
            }
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            object.__setattr__(self, "world_hash", digest)

    @property
    def n_robots(self) -> int:
        return len(self.robots)

    @property
    def n_loads(self) -> int:
        return len(self.loads)

    @property
    def world_id(self) -> str:
        return f"{self.family}-N{self.n_robots}-K{self.n_loads}-S{self.seed}"


@dataclass(frozen=True, slots=True)
class ActionCatalog:
    """Flat robot--load--slot action table and both signal treatments."""

    robot_index: np.ndarray
    load_index: np.ndarray
    slot_index: np.ndarray
    compatible: np.ndarray
    costs: np.ndarray
    travel_distance_m: np.ndarray
    mission_energy_wh: np.ndarray
    force_upper_n: np.ndarray
    wrench_columns_per_n: np.ndarray
    scalar_contributions: np.ndarray
    physical_contributions: np.ndarray
    scalar_demands: np.ndarray
    physical_demands: np.ndarray

    def __post_init__(self) -> None:
        count = len(np.asarray(self.robot_index))
        one_dimensional = (
            "robot_index",
            "load_index",
            "slot_index",
            "compatible",
            "costs",
            "travel_distance_m",
            "mission_energy_wh",
            "force_upper_n",
        )
        for name in one_dimensional:
            array = np.asarray(getattr(self, name))
            if array.shape != (count,):
                raise ValueError(f"{name} must have shape ({count},).")
            object.__setattr__(self, name, array)
        wrench = np.asarray(self.wrench_columns_per_n, dtype=float)
        scalar = np.asarray(self.scalar_contributions, dtype=float)
        physical = np.asarray(self.physical_contributions, dtype=float)
        if wrench.shape != (count, 3):
            raise ValueError("wrench_columns_per_n must have shape (actions, 3).")
        if scalar.shape != (count, 1):
            raise ValueError("scalar_contributions must have shape (actions, 1).")
        if physical.shape != (count, len(PHYSICAL_RESOURCE_NAMES)):
            raise ValueError("physical_contributions has the wrong resource dimension.")
        if not (
            np.isfinite(wrench).all()
            and np.isfinite(scalar).all()
            and np.isfinite(physical).all()
            and np.isfinite(self.costs).all()
        ):
            raise ValueError("ActionCatalog contains NaN or Inf.")
        if np.any(scalar < 0.0) or np.any(physical < 0.0):
            raise ValueError("Decision-signal contributions must be nonnegative.")
        object.__setattr__(self, "wrench_columns_per_n", wrench)
        object.__setattr__(self, "scalar_contributions", scalar)
        object.__setattr__(self, "physical_contributions", physical)
        object.__setattr__(self, "scalar_demands", np.asarray(self.scalar_demands, dtype=float))
        object.__setattr__(self, "physical_demands", np.asarray(self.physical_demands, dtype=float))

    @property
    def n_actions(self) -> int:
        return len(self.robot_index)

    def contributions(self, signal: SignalName) -> np.ndarray:
        if signal == "scalar_capacity":
            return self.scalar_contributions
        if signal == "marginal_physical":
            return self.physical_contributions
        raise ValueError(f"Unknown signal: {signal}")

    def demands(self, signal: SignalName) -> np.ndarray:
        if signal == "scalar_capacity":
            return self.scalar_demands
        if signal == "marginal_physical":
            return self.physical_demands
        raise ValueError(f"Unknown signal: {signal}")

    def actions_for_robot(self, robot: int, *, compatible_only: bool = True) -> np.ndarray:
        mask = self.robot_index == int(robot)
        if compatible_only:
            mask &= self.compatible
        return np.flatnonzero(mask)

    def action_for(self, robot: int, load: int, slot: int) -> int | None:
        matches = np.flatnonzero(
            (self.robot_index == int(robot))
            & (self.load_index == int(load))
            & (self.slot_index == int(slot))
        )
        return None if matches.size == 0 else int(matches[0])


@dataclass(frozen=True, slots=True)
class Assignment:
    """One native integer action per robot, with -1 denoting inactivity."""

    action_by_robot: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.action_by_robot, dtype=int)
        if values.ndim != 1:
            raise ValueError("action_by_robot must be one-dimensional.")
        object.__setattr__(self, "action_by_robot", values)

    @classmethod
    def empty(cls, n_robots: int) -> "Assignment":
        return cls(np.full(int(n_robots), -1, dtype=int))

    def selected_actions(self) -> np.ndarray:
        return self.action_by_robot[self.action_by_robot >= 0]

    def with_action(self, robot: int, action: int) -> "Assignment":
        updated = self.action_by_robot.copy()
        updated[int(robot)] = int(action)
        return Assignment(updated)


@dataclass(slots=True)
class AllocationResult:
    """Native output plus diagnostic/resource metadata from one allocator."""

    method: str
    engine: str
    signal: SignalName
    assignment: Assignment
    status: str
    runtime_negotiation_ms: float
    preferences: np.ndarray | None = None
    iterations: int = 0
    rounds: int = 0
    messages: int = 0
    bytes_sent: int = 0
    diagnostics: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class LoadCertificate:
    load_index: int
    committed: bool
    feasible: bool
    reasons: tuple[str, ...]
    capacity_kg: float
    capacity_lower_margin_kg: float
    capacity_upper_margin_kg: float
    battery_minimum_margin_wh: float
    wrench_residual: float
    wrench_residual_si: float
    wrench_margin: float
    slot_coverage: float
    positive_negative_torque_coverage: bool
    selected_robots: tuple[int, ...]
    selected_slots: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class WorldCertificate:
    load_certificates: tuple[LoadCertificate, ...]
    duplicate_slots: int
    incompatible_actions: int
    assignment_valid: bool
    committed_loads: int
    served_loads: int

    @property
    def all_committed_feasible(self) -> bool:
        return self.committed_loads > 0 and all(
            (not item.committed) or item.feasible for item in self.load_certificates
        )


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    assignment: Assignment
    certificate: WorldCertificate
    potential_trajectory: tuple[float, ...]
    steps: int
    augmenting_path_length: int
    robots_changed: int
    visited_states: int
    terminated: bool
    cycle_detected: bool
    runtime_ms: float
    events: tuple[dict[str, Any], ...]


__all__ = [
    "ActionCatalog",
    "AllocationResult",
    "Assignment",
    "ClosureStage",
    "ContactSlot",
    "GeoLoad",
    "GeoRobot",
    "GeoWorld",
    "LoadCertificate",
    "PHYSICAL_RESOURCE_NAMES",
    "RecoveryResult",
    "SignalName",
    "WorldCertificate",
]
