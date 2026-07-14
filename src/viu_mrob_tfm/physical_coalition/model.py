"""Typed contracts for the integrated physical-coalition campaign."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

import numpy as np


PROTOCOL_VERSION = "PHYSICAL_COALITION_CERTIFICATE_v1"


class CertificateStage(StrEnum):
    RAW_PREF = "A0_RAW_PREF"
    INTEGER_QR = "A1_INTEGER_QR"
    CAPACITY = "A2_CAPACITY"
    WRENCH_PAIR = "A3_WRENCH_PAIR"
    MECHANICS_SAFE = "A4_MECHANICS_SAFE"
    ROBUST_LOCAL = "FULL_ROBUST_LOCAL"


class FailureCode(StrEnum):
    NONE = "none"
    INCOMPLETE_QUORUM = "incomplete_quorum"
    CAPACITY_DEFICIT = "capacity_deficit"
    WRENCH_INFEASIBLE = "wrench_infeasible"
    COLLISION = "collision"
    TARGET_NOT_REACHED = "target_not_reached"
    POSE_INVALID = "pose_invalid"
    NETWORK_STALE = "network_stale"
    DROPOUT_UNRECOVERED = "dropout_unrecovered"
    NUMERICAL_ERROR = "numerical_error"


@dataclass(frozen=True, slots=True)
class PhysicalWorld:
    world_id: str
    seed: int
    family: str
    robot_positions: np.ndarray
    robot_capacity: np.ndarray
    robot_force_limit: np.ndarray
    robot_health: np.ndarray
    load_start: np.ndarray
    load_target: np.ndarray
    quorum: int
    capacity_demand: float
    wrench_demand: np.ndarray
    slot_offsets: np.ndarray
    slot_normals: np.ndarray
    obstacle_center: np.ndarray
    obstacle_radius: float
    dropout_robot: int
    dropout_time_s: float
    packet_loss: float
    delay_steps: int

    @property
    def n_robots(self) -> int:
        return int(self.robot_positions.shape[0])

    def payload(self) -> dict[str, Any]:
        raw = asdict(self)
        return {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in raw.items()
        }

    @property
    def world_hash(self) -> str:
        encoded = json.dumps(
            self.payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class CoalitionDecision:
    selected: tuple[int, ...]
    slot_by_robot: tuple[int, ...]
    messages: int = 0
    recovered_robot: int = -1

    def slot_map(self) -> dict[int, int]:
        return dict(zip(self.selected, self.slot_by_robot, strict=True))


def stable_token(*parts: object) -> str:
    encoded = "|".join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
