"""Smith-QR allocator facade used by the organized V6 architecture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from viu_mrob_tfm.allocation.base import Assignment, BaseAllocator, DecisionContext


@dataclass(slots=True)
class SmithQRAllocator(BaseAllocator):
    """Compact Smith-QR allocator based on deficit, distance, and stickiness."""

    name: str = "smith_qr"
    idle_score: float = 0.02
    distance_weight: float = 0.25
    deficit_weight: float = 1.0
    stickiness: float = 0.05

    def allocate(self, context: DecisionContext) -> Assignment:
        world = context.world
        robot_count = len(world.robots)
        load_count = len(world.loads)
        if load_count == 0 or robot_count == 0:
            return Assignment(labels=np.zeros(robot_count, dtype=int), method=self.name)

        scores = np.full((robot_count, load_count + 1), self.idle_score, dtype=float)
        labels = np.zeros(robot_count, dtype=int)
        previous = context.previous_assignment.labels if context.previous_assignment else None

        for robot_idx, robot in enumerate(world.robots):
            if not robot.active:
                continue
            for load_idx, load in enumerate(world.loads):
                demand = float(load.min_capacity_kg or load.mass_kg)
                effective = robot.effective_capacity(demand)
                distance = float(np.linalg.norm(robot.position - load.pickup))
                capacity_gain = min(effective / max(demand, 1e-9), 1.0)
                score = load.reward + self.deficit_weight * capacity_gain - self.distance_weight * distance
                if previous is not None and previous[robot_idx] == load_idx + 1:
                    score += self.stickiness
                scores[robot_idx, load_idx + 1] = score
            labels[robot_idx] = int(np.argmax(scores[robot_idx]))

        labels = self._close_integer_quorums(labels, scores, context)
        return Assignment(labels=labels, scores=scores, method=self.name)

    def _close_integer_quorums(
        self,
        labels: np.ndarray,
        scores: np.ndarray,
        context: DecisionContext,
    ) -> np.ndarray:
        updated = labels.copy()
        for load_idx, load in enumerate(context.world.loads):
            assigned = np.flatnonzero(updated == load_idx + 1)
            deficit = load.min_coalition_size - assigned.size
            if deficit <= 0:
                continue
            idle = np.flatnonzero(updated == 0)
            if idle.size == 0:
                continue
            ranked = idle[np.argsort(scores[idle, load_idx + 1])[::-1]]
            for robot_idx in ranked[:deficit]:
                if scores[robot_idx, load_idx + 1] > scores[robot_idx, 0]:
                    updated[robot_idx] = load_idx + 1
        return updated
