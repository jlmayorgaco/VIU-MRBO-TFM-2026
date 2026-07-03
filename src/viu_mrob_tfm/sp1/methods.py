"""SP1 recruitment methods: baselines, model-based policies, and data-driven methods."""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from viu_mrob_tfm.allocation import (
    Assignment,
    BaseAllocator,
    CentralizedClassicAllocator,
    DecisionContext,
    DecentralizedAuctionAllocator,
    DecentralizedClassicGreedyAllocator,
    SmithQRAllocator,
)


SP1_METHOD_LABELS = {
    "greedy_nearest": "Greedy nearest",
    "hungarian_expanded": "Hungarian expanded",
    "centralized_coalition_milp": "Centralized coalition oracle",
    "cbba": "CBBA-like auction",
    "replicator_cardinality": "Replicator cardinality",
    "smith_cardinality": "Smith cardinality",
    "bnn_cardinality": "BNN cardinality",
    "primal_dual_cardinality_capacity": "Primal-dual cardinality capacity",
    "primal_dual_wrench_market": "Primal-dual wrench market",
    "local_primal_dual_wrench_market": "Local primal-dual wrench market",
    "imitation_oracle": "Data-driven imitation oracle",
    "mappo_recruitment": "MAPPO recruitment checkpoint",
}


def make_sp1_allocator(method_id: str, params: dict[str, Any] | None = None) -> BaseAllocator:
    """Instantiate an SP1 allocator by stable method id."""

    params = dict(params or {})
    method = method_id.lower()
    if method == "greedy_nearest":
        return DecentralizedClassicGreedyAllocator(name=method)
    if method == "hungarian_expanded":
        return CentralizedClassicAllocator(name=method)
    if method == "centralized_coalition_milp":
        return CentralizedCoalitionOracleAllocator(name=method, **_filter_params(params, {"distance_weight"}))
    if method == "cbba":
        return DecentralizedAuctionAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.65)),
            deficit_weight=float(params.get("deficit_weight", 0.45)),
        )
    if method == "replicator_cardinality":
        return UtilityGreedyAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.25)),
            deficit_weight=float(params.get("deficit_weight", 0.8)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            idle_score=float(params.get("idle_score", 0.02)),
            exponent=1.0,
        )
    if method == "smith_cardinality":
        return SmithQRAllocator(
            name=method,
            idle_score=float(params.get("idle_score", 0.02)),
            distance_weight=float(params.get("distance_weight", 0.22)),
            deficit_weight=float(params.get("deficit_weight", 1.15)),
            stickiness=float(params.get("stickiness", 0.0)),
        )
    if method == "bnn_cardinality":
        return UtilityGreedyAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.22)),
            deficit_weight=float(params.get("deficit_weight", 1.0)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            idle_score=float(params.get("idle_score", 0.04)),
            exponent=2.0,
        )
    if method == "primal_dual_cardinality_capacity":
        return PrimalDualRecruitmentAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.16)),
            deficit_weight=float(params.get("deficit_weight", 1.25)),
            capacity_weight=float(params.get("capacity_weight", 0.75)),
            reward_weight=float(params.get("reward_weight", 1.15)),
        )
    if method == "primal_dual_wrench_market":
        return PrimalDualRecruitmentAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.14)),
            deficit_weight=float(params.get("deficit_weight", 1.35)),
            capacity_weight=float(params.get("capacity_weight", 0.85)),
            reward_weight=float(params.get("reward_weight", 1.25)),
            wrench_weight=float(params.get("wrench_weight", 0.15)),
        )
    if method == "local_primal_dual_wrench_market":
        return PrimalDualRecruitmentAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.14)),
            deficit_weight=float(params.get("deficit_weight", 1.35)),
            capacity_weight=float(params.get("capacity_weight", 0.85)),
            reward_weight=float(params.get("reward_weight", 1.25)),
            wrench_weight=float(params.get("wrench_weight", 0.15)),
            local_only=True,
        )
    if method == "mappo_recruitment":
        from viu_mrob_tfm.sp1.mappo import MAPPORecruitmentAllocator

        checkpoint = params.get("checkpoint") or params.get("model_path")
        return MAPPORecruitmentAllocator(
            name=method,
            checkpoint=None if checkpoint is None else Path(checkpoint),
            deterministic=bool(params.get("deterministic", True)),
        )
    if method == "imitation_oracle":
        checkpoint = params.get("checkpoint") or params.get("model_path")
        return ImitationRecruitmentAllocator(name=method, model_path=None if checkpoint is None else Path(checkpoint))
    raise ValueError(f"Unknown SP1 method id: {method_id}")


@dataclass(slots=True)
class CentralizedCoalitionOracleAllocator(BaseAllocator):
    """Exact complete-coalition oracle over load subsets plus Hungarian assignment.

    It is small but exact for SP1-scale load counts: each candidate subset of
    loads is accepted only if its full cardinality demand fits the fleet.
    """

    name: str = "centralized_coalition_milp"
    distance_weight: float = 0.01

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=np.zeros(robot_count, dtype=int), method=self.name)
        demands = _load_demands(context)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)

        best_score = -np.inf
        best_labels = np.zeros(robot_count, dtype=int)
        load_indices = range(load_count)
        for size in range(load_count + 1):
            for subset in combinations(load_indices, size):
                required = int(np.sum(demands[list(subset)])) if subset else 0
                if required > robot_count:
                    continue
                labels, assignment_distance = _assign_complete_subset(distances, demands, subset)
                score = float(np.sum(rewards[list(subset)])) - self.distance_weight * assignment_distance
                if score > best_score:
                    best_score = score
                    best_labels = labels
        return Assignment(labels=best_labels, scores=-distances, method=self.name)


@dataclass(slots=True)
class UtilityGreedyAllocator(BaseAllocator):
    """Decentralized utility rule used for replicator and BNN SP1 approximations."""

    name: str
    distance_weight: float = 0.25
    deficit_weight: float = 1.0
    reward_weight: float = 1.0
    idle_score: float = 0.02
    exponent: float = 1.0

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        demands = _load_demands(context).astype(float)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        counts = np.zeros(load_count, dtype=float)
        scores = np.zeros((robot_count, load_count), dtype=float)

        for robot_idx in np.argsort(np.min(distances, axis=1)):
            deficits = np.maximum(demands - counts, 0.0)
            utility = self.reward_weight * rewards + self.deficit_weight * deficits - self.distance_weight * distances[int(robot_idx)]
            utility = np.maximum(utility, 0.0) ** self.exponent
            scores[int(robot_idx)] = utility
            if float(np.max(utility)) <= self.idle_score:
                continue
            load_idx = int(np.argmax(utility))
            labels[int(robot_idx)] = load_idx + 1
            counts[load_idx] += 1.0
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class PrimalDualRecruitmentAllocator(BaseAllocator):
    """Primal-dual-style SP1 allocator with capacity and optional local communication."""

    name: str
    distance_weight: float = 0.14
    deficit_weight: float = 1.35
    capacity_weight: float = 0.85
    reward_weight: float = 1.25
    wrench_weight: float = 0.0
    local_only: bool = False

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.full((robot_count, load_count), -np.inf, dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)

        demands = _load_demands(context).astype(float)
        required_capacity = np.array([load.min_capacity_kg for load in context.world.loads], dtype=float)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        capacities = np.array([robot.spec.capacity.payload_kg for robot in context.world.robots], dtype=float)
        assigned_counts = np.zeros(load_count, dtype=float)
        assigned_capacity = np.zeros(load_count, dtype=float)
        available = np.ones(robot_count, dtype=bool)
        radius = float(context.metadata.get("communication_radius", np.inf))

        for _ in range(robot_count):
            best: tuple[float, int, int] | None = None
            deficits = np.maximum(demands - assigned_counts, 0.0)
            capacity_deficits = np.maximum(required_capacity - assigned_capacity, 0.0)
            if np.all(deficits <= 0.0) and np.all(capacity_deficits <= 1e-9):
                break
            for robot_idx in np.flatnonzero(available):
                visible = np.arange(load_count)
                if self.local_only and np.isfinite(radius):
                    visible = visible[distances[int(robot_idx)] <= radius]
                    if visible.size == 0:
                        continue
                capacity_gain = np.minimum(capacities[int(robot_idx)], capacity_deficits[visible]) / np.maximum(
                    required_capacity[visible],
                    1e-9,
                )
                geometric_term = self.wrench_weight / np.sqrt(np.maximum(demands[visible], 1.0))
                utility = (
                    self.reward_weight * rewards[visible]
                    + self.deficit_weight * deficits[visible]
                    + self.capacity_weight * capacity_gain
                    + geometric_term
                    - self.distance_weight * distances[int(robot_idx), visible]
                )
                local_choice = int(np.argmax(utility))
                load_idx = int(visible[local_choice])
                score = float(utility[local_choice])
                scores[int(robot_idx), load_idx] = score
                if best is None or score > best[0]:
                    best = (score, int(robot_idx), load_idx)
            if best is None:
                break
            _score, robot_idx, load_idx = best
            labels[robot_idx] = load_idx + 1
            assigned_counts[load_idx] += 1.0
            assigned_capacity[load_idx] += capacities[robot_idx]
            available[robot_idx] = False
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class ImitationRecruitmentAllocator(BaseAllocator):
    """Frozen linear data-driven SP1 policy trained from oracle demonstrations."""

    name: str = "imitation_oracle"
    model_path: Path | None = None

    def allocate(self, context: DecisionContext) -> Assignment:
        model = self._load_model()
        weights = np.asarray(model["weights"], dtype=float)
        idle_score = float(model.get("idle_score", -0.05))
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.zeros((robot_count, load_count), dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)

        demands = _load_demands(context).astype(float)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        capacities = np.array([robot.spec.capacity.payload_kg for robot in context.world.robots], dtype=float)
        required_capacity = np.array([load.min_capacity_kg for load in context.world.loads], dtype=float)
        counts = np.zeros(load_count, dtype=float)

        for robot_idx in np.argsort(np.min(distances, axis=1)):
            open_loads = counts < demands
            if not np.any(open_loads):
                break
            features = _imitation_features(
                rewards=rewards,
                demands=demands,
                counts=counts,
                distances=distances[int(robot_idx)],
                capacity=capacities[int(robot_idx)],
                required_capacity=required_capacity,
            )
            utility = features @ weights
            utility = np.where(open_loads, utility, -np.inf)
            scores[int(robot_idx)] = utility
            if float(np.max(utility)) <= idle_score:
                continue
            load_idx = int(np.argmax(utility))
            labels[int(robot_idx)] = load_idx + 1
            counts[load_idx] += 1.0
        return Assignment(labels=labels, scores=scores, method=self.name)

    def _load_model(self) -> dict[str, Any]:
        if self.model_path is not None and self.model_path.exists():
            return json.loads(self.model_path.read_text(encoding="utf-8"))
        return {
            "model_version": "sp1-imitation-default-linear",
            "feature_names": IMITATION_FEATURE_NAMES,
            "weights": [0.15, 1.05, 0.8, 0.65, -0.22, 0.2],
            "idle_score": -0.05,
        }


IMITATION_FEATURE_NAMES = [
    "bias",
    "reward",
    "cardinality_deficit_ratio",
    "capacity_ratio",
    "distance_m",
    "priority_density",
]


def fit_imitation_model(contexts: list[DecisionContext], oracle: BaseAllocator) -> dict[str, Any]:
    """Fit a small linear scorer from oracle robot-load choices."""

    feature_rows = []
    targets = []
    for context in contexts:
        assignment = oracle.allocate(context)
        distances = _distance_matrix(context)
        demands = _load_demands(context).astype(float)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        capacities = np.array([robot.spec.capacity.payload_kg for robot in context.world.robots], dtype=float)
        required_capacity = np.array([load.min_capacity_kg for load in context.world.loads], dtype=float)
        counts = np.zeros(len(context.world.loads), dtype=float)
        for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
            features = _imitation_features(
                rewards=rewards,
                demands=demands,
                counts=counts,
                distances=distances[int(robot_idx)],
                capacity=capacities[int(robot_idx)],
                required_capacity=required_capacity,
            )
            for load_idx in range(len(context.world.loads)):
                feature_rows.append(features[load_idx])
                targets.append(1.0 if label == load_idx + 1 else 0.0)
            if label > 0:
                counts[int(label) - 1] += 1.0

    x = np.asarray(feature_rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    ridge = 1e-6 * np.eye(x.shape[1], dtype=float)
    weights = np.linalg.solve(x.T @ x + ridge, x.T @ y)
    return {
        "model_version": "sp1-imitation-linear-v1",
        "algorithm": "ridge least-squares imitation from centralized coalition oracle",
        "feature_names": IMITATION_FEATURE_NAMES,
        "weights": [float(value) for value in weights],
        "idle_score": -0.02,
    }


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


def _assign_complete_subset(distances: np.ndarray, demands: np.ndarray, subset: tuple[int, ...]) -> tuple[np.ndarray, float]:
    labels = np.zeros(distances.shape[0], dtype=int)
    if not subset:
        return labels, 0.0
    slot_loads = [load_idx for load_idx in subset for _ in range(int(demands[load_idx]))]
    cost = distances[:, slot_loads]
    rows, cols = linear_sum_assignment(cost)
    total = 0.0
    for row, col in zip(rows, cols):
        labels[int(row)] = int(slot_loads[int(col)]) + 1
        total += float(cost[int(row), int(col)])
    return labels, total


def _imitation_features(
    *,
    rewards: np.ndarray,
    demands: np.ndarray,
    counts: np.ndarray,
    distances: np.ndarray,
    capacity: float,
    required_capacity: np.ndarray,
) -> np.ndarray:
    deficits = np.maximum(demands - counts, 0.0)
    demand_ratio = deficits / np.maximum(demands, 1.0)
    capacity_ratio = np.minimum(capacity, required_capacity) / np.maximum(required_capacity, 1e-9)
    priority_density = rewards / np.maximum(demands, 1.0)
    return np.column_stack(
        [
            np.ones_like(rewards),
            rewards,
            demand_ratio,
            capacity_ratio,
            distances,
            priority_density,
        ]
    )


def _filter_params(params: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if key in allowed}
