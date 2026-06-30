"""Simulation result models for V6 OOP workflows."""

from __future__ import annotations

from dataclasses import dataclass

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.control import RobotCommand
from viu_mrob_tfm.domain.world import WorldState


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Small result object returned by the OOP simulation facade."""

    world: WorldState
    assignment: Assignment
    command: RobotCommand
    steps: int
    metadata: dict[str, str]
