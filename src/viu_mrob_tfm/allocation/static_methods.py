"""Static allocation baselines for one-shot AMR-to-load assignment experiments."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import linear_sum_assignment

from viu_mrob_tfm.allocation.base import Assignment, BaseAllocator, DecisionContext


def _distance_matrix(context: DecisionContext) -> np.ndarray:
    robots = context.world.robots
    loads = context.world.loads
    if not robots or not loads:
        return np.zeros((len(robots), len(loads)), dtype=float)
    robot_positions = np.vstack([robot.position for robot in robots])
    load_positions = np.vstack([load.pickup for load in loads])
    return np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)


def _load_demands(context: DecisionContext) -> np.ndarray:
    return np.array([load.min_coalition_size for load in context.world.loads], dtype=int)


def _assignment_with_diagnostics(labels: np.ndarray, method: str, scores: np.ndarray | None = None) -> Assignment:
    return Assignment(labels=np.asarray(labels, dtype=int), scores=scores, method=method)


@dataclass(slots=True)
class CentralizedClassicAllocator(BaseAllocator):
    """Classic centralized min-cost assignment over replicated load slots."""

    name: str = "centralized_classic_mincost"

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        if robot_count == 0 or load_count == 0:
            return _assignment_with_diagnostics(np.zeros(robot_count, dtype=int), self.name)

        demands = _load_demands(context)
        slot_loads = [load_idx for load_idx, demand in enumerate(demands) for _ in range(int(demand))]
        if not slot_loads:
            return _assignment_with_diagnostics(np.zeros(robot_count, dtype=int), self.name)

        cost = distances[:, slot_loads]
        row_ind, col_ind = linear_sum_assignment(cost)
        labels = np.zeros(robot_count, dtype=int)
        for row, col in zip(row_ind, col_ind):
            labels[int(row)] = int(slot_loads[int(col)]) + 1
        return _assignment_with_diagnostics(labels, self.name, scores=-distances)


@dataclass(slots=True)
class DecentralizedClassicGreedyAllocator(BaseAllocator):
    """Classic local greedy allocator: each AMR takes nearest load with open demand."""

    name: str = "decentralized_classic_greedy"

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        if robot_count == 0 or load_count == 0:
            return _assignment_with_diagnostics(labels, self.name)

        remaining = _load_demands(context).astype(int)
        order = np.argsort(np.min(distances, axis=1))
        for robot_idx in order:
            available = np.flatnonzero(remaining > 0)
            if available.size == 0:
                break
            selected = int(available[np.argmin(distances[int(robot_idx), available])])
            labels[int(robot_idx)] = selected + 1
            remaining[selected] -= 1
        return _assignment_with_diagnostics(labels, self.name, scores=-distances)


@dataclass(slots=True)
class CentralizedUtilityAllocator(BaseAllocator):
    """Centralized SOTA proxy: reward-aware min-cost assignment under scarcity."""

    name: str = "centralized_sota_reward_aware"
    reward_weight: float = 2.4
    demand_weight: float = 0.15

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        if robot_count == 0 or load_count == 0:
            return _assignment_with_diagnostics(np.zeros(robot_count, dtype=int), self.name)

        demands = _load_demands(context)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        slot_loads = [load_idx for load_idx, demand in enumerate(demands) for _ in range(int(demand))]
        if not slot_loads:
            return _assignment_with_diagnostics(np.zeros(robot_count, dtype=int), self.name)

        slot_loads_array = np.asarray(slot_loads, dtype=int)
        value = self.reward_weight * rewards[slot_loads_array] + self.demand_weight * demands[slot_loads_array]
        cost = distances[:, slot_loads_array] - value[None, :]
        row_ind, col_ind = linear_sum_assignment(cost)
        labels = np.zeros(robot_count, dtype=int)
        for row, col in zip(row_ind, col_ind):
            labels[int(row)] = int(slot_loads_array[int(col)]) + 1
        return _assignment_with_diagnostics(labels, self.name, scores=-cost)


@dataclass(slots=True)
class DecentralizedAuctionAllocator(BaseAllocator):
    """Decentralized SOTA proxy: CBBA-like local auction with deficit prices."""

    name: str = "decentralized_sota_auction"
    distance_weight: float = 0.65
    deficit_weight: float = 0.45
    max_rounds: int = 32

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        if robot_count == 0 or load_count == 0:
            return _assignment_with_diagnostics(labels, self.name)

        demands = _load_demands(context).astype(int)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        assigned_counts = np.zeros(load_count, dtype=int)
        available = np.ones(robot_count, dtype=bool)
        scores = np.zeros((robot_count, load_count), dtype=float)

        for _ in range(self.max_rounds):
            if not np.any(available) or np.all(assigned_counts >= demands):
                break
            deficits = np.maximum(demands - assigned_counts, 0)
            open_loads = np.flatnonzero(deficits > 0)
            if open_loads.size == 0:
                break

            best: tuple[float, int, int] | None = None
            for robot_idx in np.flatnonzero(available):
                utility = (
                    rewards[open_loads]
                    + self.deficit_weight * deficits[open_loads]
                    - self.distance_weight * distances[int(robot_idx), open_loads]
                )
                local_best_idx = int(np.argmax(utility))
                load_idx = int(open_loads[local_best_idx])
                bid = float(utility[local_best_idx])
                scores[int(robot_idx), load_idx] = bid
                if best is None or bid > best[0]:
                    best = (bid, int(robot_idx), load_idx)
            if best is None:
                break
            _bid, robot_idx, load_idx = best
            labels[robot_idx] = load_idx + 1
            assigned_counts[load_idx] += 1
            available[robot_idx] = False
        return _assignment_with_diagnostics(labels, self.name, scores=scores)


def timed_allocate(allocator: BaseAllocator, context: DecisionContext) -> tuple[Assignment, float]:
    """Run an allocator and return wall-clock runtime in milliseconds."""

    start = perf_counter()
    assignment = allocator.allocate(context)
    runtime_ms = 1000.0 * (perf_counter() - start)
    return assignment, runtime_ms
