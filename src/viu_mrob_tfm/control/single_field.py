"""Single-field controller for emergent coalition behavior."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from viu_mrob_tfm.allocation import Assignment
from viu_mrob_tfm.control.base import BaseContinuousController, RobotCommand
from viu_mrob_tfm.control.wrench import RigidFormation, RigidFormationSlot, VectorialWrenchGame
from viu_mrob_tfm.domain.load import LoadSpec
from viu_mrob_tfm.domain.world import WorldState


@dataclass(slots=True)
class SingleFieldController(BaseContinuousController):
    """Continuous vector field for task, rigid formation, battery, and obstacle terms."""

    name: str = "single_field"
    task_gain: float = 1.0
    formation_gain: float = 0.35
    obstacle_gain: float = 0.55
    battery_gain: float = 0.25
    wrench_gain: float = 0.08
    max_speed: float = 0.65
    formation_radius: float = 0.65
    wrench_game: VectorialWrenchGame = field(default_factory=VectorialWrenchGame)

    def compute(self, world: WorldState, assignment: Assignment) -> RobotCommand:
        commands = np.zeros((len(world.robots), 2), dtype=float)
        for idx, robot in enumerate(world.robots):
            if not robot.active:
                continue
            vector = np.zeros(2, dtype=float)
            label = int(assignment.labels[idx]) if idx < assignment.labels.size else 0
            if label > 0 and label <= len(world.loads):
                load = world.loads[label - 1]
                members = assignment.members_for_load(label - 1)
                slot = self._rigid_formation_slot(load, members, idx)
                target = load.pickup + slot.offset
                vector += self.task_gain * (load.pickup - robot.position)
                vector += self.formation_gain * (target - robot.position)
                vector += self._wrench_field(world, load, members, idx)
            vector += self._obstacle_field(world, robot.position)
            vector += self._battery_field(robot.battery_fraction, robot.position)
            commands[idx] = self._saturate(vector, robot.spec.max_speed or self.max_speed)
        return RobotCommand(commands, source=self.name)

    def _rigid_formation_slot(
        self,
        load: LoadSpec,
        members: np.ndarray,
        robot_idx: int,
    ) -> RigidFormationSlot:
        formation = RigidFormation.from_load(load)
        if members.size <= 1:
            return RigidFormationSlot(offset=np.zeros(2, dtype=float), normal=np.array([1.0, 0.0]))
        rank_matches = np.flatnonzero(members == robot_idx)
        rank = int(rank_matches[0]) if rank_matches.size else 0
        return formation.slot_for_rank(rank)

    def _wrench_field(
        self,
        world: WorldState,
        load: LoadSpec,
        members: np.ndarray,
        robot_idx: int,
    ) -> np.ndarray:
        if members.size == 0:
            return np.zeros(2, dtype=float)
        rank_matches = np.flatnonzero(members == robot_idx)
        if rank_matches.size == 0:
            return np.zeros(2, dtype=float)
        rank = int(rank_matches[0])
        formation = RigidFormation.from_load(load)
        force_limits = np.array(
            [world.robots[int(member)].spec.capacity.force_limit_n for member in members],
            dtype=float,
        )
        solution = self.wrench_game.solve(
            demand=load.wrench,
            formation=formation,
            force_limits=force_limits,
            contact_count=int(members.size),
        )
        if rank >= solution.contact_forces.size:
            return np.zeros(2, dtype=float)
        slot = formation.slot_for_rank(rank)
        return self.wrench_gain * float(solution.contact_forces[rank]) * slot.normal

    def _obstacle_field(self, world: WorldState, position: np.ndarray) -> np.ndarray:
        vector = np.zeros(2, dtype=float)
        for obstacle in world.map.obstacles:
            delta = position - obstacle.center
            distance = float(np.linalg.norm(delta))
            signed = distance - obstacle.radius
            if 1e-9 < signed < obstacle.influence_radius:
                vector += self.obstacle_gain * delta / distance * (1.0 / max(signed, 1e-3) - 1.0 / obstacle.influence_radius)
        return vector

    def _battery_field(self, battery_fraction: float, position: np.ndarray) -> np.ndarray:
        urgency = max(0.0, 0.35 - battery_fraction)
        if urgency <= 0.0:
            return np.zeros(2, dtype=float)
        home = np.zeros(2, dtype=float)
        return self.battery_gain * urgency * (home - position)

    def _saturate(self, vector: np.ndarray, limit: float) -> np.ndarray:
        norm = float(np.linalg.norm(vector))
        if norm <= limit or norm <= 1e-12:
            return vector
        return vector * (limit / norm)