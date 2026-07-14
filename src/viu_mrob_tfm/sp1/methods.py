"""SP1 recruitment methods: baselines, model-based policies, and data-driven methods."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp

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
    "replicator_cardinality_repair": "Replicator cardinality local repair",
    "logit_cardinality_repair": "Logit cardinality local repair",
    "smith_cardinality": "Smith cardinality",
    "bnn_cardinality": "BNN cardinality",
    "bnn_cardinality_repair": "Brown/BNN cardinality local repair",
    "primal_dual_cardinality_capacity": "Primal-dual cardinality capacity",
    "primal_dual_local_repair": "Primal-dual local repair",
    "primal_dual_wrench_market": "Primal-dual wrench market",
    "local_primal_dual_wrench_market": "Local primal-dual wrench market",
    "tensor_quorum_flow_repair": "Smooth tensor quorum-flow repair",
    "imitation_oracle": "Data-driven imitation oracle",
    "mappo_recruitment": "MAPPO recruitment checkpoint",
}

SP1_METHOD_METADATA = {
    "greedy_nearest": {
        "family": "classic",
        "scope": "decentralized",
        "ownership": "baseline",
        "variant": "nearest_greedy",
        "comparison_group": "classic_decentralized_baseline",
    },
    "hungarian_expanded": {
        "family": "classic",
        "scope": "centralized",
        "ownership": "baseline",
        "variant": "hungarian_expanded",
        "comparison_group": "classic_centralized_baseline",
    },
    "centralized_coalition_milp": {
        "family": "model_based_oracle",
        "scope": "centralized",
        "ownership": "reference",
        "variant": "exact_binary_quorum_capacity_milp",
        "comparison_group": "centralized_oracle_reference",
    },
    "cbba": {
        "family": "sota",
        "scope": "decentralized",
        "ownership": "baseline",
        "variant": "cbba_like_auction",
        "comparison_group": "sota_decentralized_baseline",
    },
    "replicator_cardinality": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "baseline",
        "variant": "population_game_replicator",
        "comparison_group": "model_based_decentralized_baseline",
    },
    "replicator_cardinality_repair": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "replicator_with_certified_local_repair",
        "comparison_group": "proposed_local_repair_family",
    },
    "logit_cardinality_repair": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "logit_quorum_flow_with_local_repair",
        "comparison_group": "proposed_local_repair_family",
    },
    "smith_cardinality": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "smith_qr_cardinality",
        "comparison_group": "proposed_model_based_variation",
    },
    "bnn_cardinality": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "baseline",
        "variant": "bnn_cardinality",
        "comparison_group": "model_based_decentralized_baseline",
    },
    "bnn_cardinality_repair": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "brown_bnn_positive_excess_with_local_repair",
        "comparison_group": "proposed_local_repair_family",
    },
    "primal_dual_cardinality_capacity": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "primal_dual_capacity",
        "comparison_group": "proposed_model_based_variation",
    },
    "primal_dual_local_repair": {
        "family": "model_based",
        "scope": "decentralized_local",
        "ownership": "proposed",
        "variant": "primal_dual_with_certified_local_repair",
        "comparison_group": "proposed_local_repair_family",
    },
    "primal_dual_wrench_market": {
        "family": "model_based",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "primal_dual_wrench_proxy",
        "comparison_group": "proposed_model_based_variation",
    },
    "local_primal_dual_wrench_market": {
        "family": "model_based",
        "scope": "decentralized_local",
        "ownership": "proposed",
        "variant": "local_primal_dual_wrench_proxy",
        "comparison_group": "proposed_local_variation",
    },
    "tensor_quorum_flow_repair": {
        "family": "model_based",
        "scope": "decentralized_local",
        "ownership": "proposed",
        "variant": "smooth_tensor_quorum_flow_with_repair",
        "comparison_group": "proposed_local_repair_family",
    },
    "imitation_oracle": {
        "family": "data_driven",
        "scope": "decentralized",
        "ownership": "baseline",
        "variant": "oracle_imitation_linear",
        "comparison_group": "data_driven_baseline",
    },
    "mappo_recruitment": {
        "family": "data_driven",
        "scope": "decentralized",
        "ownership": "proposed",
        "variant": "mappo_ctde_quorum_decoder",
        "comparison_group": "proposed_data_driven_variation",
    },
    "oracle_reference": {
        "family": "model_based_oracle",
        "scope": "centralized",
        "ownership": "reference",
        "variant": "exact_capacity_feasible_reference",
        "comparison_group": "centralized_oracle_reference",
    },
}

SP1_METHOD_RESOURCE_METADATA = {
    "greedy_nearest": {
        "training_type": "none",
        "execution_model": "distributed_greedy_rule",
        "communication_pattern": "local_robot_load_distances",
        "trainable_parameters": 0,
        "tuned_parameters": 0,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "hungarian_expanded": {
        "training_type": "none",
        "execution_model": "centralized_hungarian_assignment",
        "communication_pattern": "centralized_all_robot_load_pairs",
        "trainable_parameters": 0,
        "tuned_parameters": 0,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "centralized_coalition_milp": {
        "training_type": "none",
        "execution_model": "centralized_exact_binary_milp",
        "communication_pattern": "centralized_all_robot_load_pairs",
        "trainable_parameters": 0,
        "tuned_parameters": 3,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "cbba": {
        "training_type": "none",
        "execution_model": "distributed_auction_proxy",
        "communication_pattern": "auction_bids",
        "trainable_parameters": 0,
        "tuned_parameters": 2,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "replicator_cardinality": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_utility_rule",
        "communication_pattern": "local_deficit_scores",
        "trainable_parameters": 0,
        "tuned_parameters": 4,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "replicator_cardinality_repair": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_replicator_plus_local_exact_repair",
        "communication_pattern": "local_deficit_scores_plus_small_repair_neighborhood",
        "trainable_parameters": 0,
        "tuned_parameters": 7,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "logit_cardinality_repair": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_logit_quorum_flow_plus_local_repair",
        "communication_pattern": "softmax_local_deficit_scores_plus_small_repair_neighborhood",
        "trainable_parameters": 0,
        "tuned_parameters": 8,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "smith_cardinality": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_smith_qr_rule",
        "communication_pattern": "local_capacity_scores",
        "trainable_parameters": 0,
        "tuned_parameters": 3,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "bnn_cardinality": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_nonlinear_utility_rule",
        "communication_pattern": "local_deficit_scores",
        "trainable_parameters": 0,
        "tuned_parameters": 5,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "bnn_cardinality_repair": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_brown_bnn_positive_excess_plus_local_repair",
        "communication_pattern": "positive_excess_scores_plus_small_repair_neighborhood",
        "trainable_parameters": 0,
        "tuned_parameters": 8,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "primal_dual_cardinality_capacity": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_primal_dual_capacity_rule",
        "communication_pattern": "local_deficit_capacity_prices",
        "trainable_parameters": 0,
        "tuned_parameters": 4,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "primal_dual_local_repair": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_primal_dual_plus_certified_local_repair",
        "communication_pattern": "local_deficit_capacity_prices_plus_small_repair_neighborhood",
        "trainable_parameters": 0,
        "tuned_parameters": 8,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "primal_dual_wrench_market": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "distributed_primal_dual_wrench_rule",
        "communication_pattern": "local_deficit_capacity_wrench_prices",
        "trainable_parameters": 0,
        "tuned_parameters": 5,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "local_primal_dual_wrench_market": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "local_primal_dual_wrench_rule",
        "communication_pattern": "radius_limited_local_scores",
        "trainable_parameters": 0,
        "tuned_parameters": 5,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "tensor_quorum_flow_repair": {
        "training_type": "model_based_tuning_optional",
        "execution_model": "smooth_tensor_quorum_flow_plus_certified_local_repair",
        "communication_pattern": "radius_limited_tensorized_deficit_capacity_scores",
        "trainable_parameters": 0,
        "tuned_parameters": 9,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "imitation_oracle": {
        "training_type": "supervised_oracle_imitation",
        "execution_model": "distributed_linear_score_policy",
        "communication_pattern": "local_robot_load_features",
        "trainable_parameters": 7,
        "tuned_parameters": 1,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
    "mappo_recruitment": {
        "training_type": "ctde_ppo_with_bc_warm_start",
        "execution_model": "decentralized_neural_actor_with_quorum_decoder",
        "communication_pattern": "local_features_plus_centralized_training",
        "trainable_parameters": 0,
        "tuned_parameters": 12,
        "uses_neural_policy": True,
        "uses_decoder": True,
    },
    "oracle_reference": {
        "training_type": "none",
        "execution_model": "centralized_exact_reference_replay",
        "communication_pattern": "centralized_all_robot_load_pairs",
        "trainable_parameters": 0,
        "tuned_parameters": 2,
        "uses_neural_policy": False,
        "uses_decoder": False,
    },
}


def sp1_method_metadata(method_id: str) -> dict[str, Any]:
    """Return stable taxonomy fields used by reports, tables, and filenames."""

    method = method_id.lower()
    metadata = dict(
        SP1_METHOD_METADATA.get(
            method,
            {
                "family": "unknown",
                "scope": "unknown",
                "ownership": "unknown",
                "variant": method,
                "comparison_group": "unknown",
            },
        )
    )
    metadata.update(
        SP1_METHOD_RESOURCE_METADATA.get(
            method,
            {
                "training_type": "unknown",
                "execution_model": "unknown",
                "communication_pattern": "unknown",
                "trainable_parameters": 0,
                "tuned_parameters": 0,
                "uses_neural_policy": False,
                "uses_decoder": False,
            },
        )
    )
    label = SP1_METHOD_LABELS.get(method, method.replace("_", " "))
    metadata["label"] = label
    metadata["file_tag"] = (
        f"{metadata['ownership']}-{metadata['family']}-{metadata['scope']}-{method}"
    ).replace("_", "-")
    metadata["title"] = (
        f"{label} [{metadata['ownership']} | {metadata['family']} | "
        f"{metadata['scope']} | {metadata['variant']}]"
    )
    return metadata


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
    if method == "replicator_cardinality_repair":
        return LocalRepairRecruitmentAllocator(
            name=method,
            base_allocator=UtilityGreedyAllocator(
                name="replicator_cardinality",
                distance_weight=float(params.get("distance_weight", 0.25)),
                deficit_weight=float(params.get("deficit_weight", 0.8)),
                reward_weight=float(params.get("reward_weight", 1.0)),
                idle_score=float(params.get("idle_score", 0.02)),
                exponent=1.0,
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "logit_cardinality_repair":
        return LocalRepairRecruitmentAllocator(
            name=method,
            base_allocator=UtilityGreedyAllocator(
                name="logit_cardinality",
                distance_weight=float(params.get("distance_weight", 0.20)),
                deficit_weight=float(params.get("deficit_weight", 1.05)),
                reward_weight=float(params.get("reward_weight", 1.10)),
                idle_score=float(params.get("idle_score", 0.01)),
                exponent=float(params.get("inverse_temperature", 1.35)),
            ),
            max_passes=int(params.get("max_passes", 4)),
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
    if method == "bnn_cardinality_repair":
        return LocalRepairRecruitmentAllocator(
            name=method,
            base_allocator=UtilityGreedyAllocator(
                name="bnn_cardinality",
                distance_weight=float(params.get("distance_weight", 0.22)),
                deficit_weight=float(params.get("deficit_weight", 1.0)),
                reward_weight=float(params.get("reward_weight", 1.0)),
                idle_score=float(params.get("idle_score", 0.04)),
                exponent=2.0,
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "primal_dual_cardinality_capacity":
        return PrimalDualRecruitmentAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.16)),
            deficit_weight=float(params.get("deficit_weight", 1.25)),
            capacity_weight=float(params.get("capacity_weight", 0.75)),
            reward_weight=float(params.get("reward_weight", 1.15)),
        )
    if method == "primal_dual_local_repair":
        return LocalRepairRecruitmentAllocator(
            name=method,
            base_allocator=PrimalDualRecruitmentAllocator(
                name="primal_dual_cardinality_capacity",
                distance_weight=float(params.get("distance_weight", 0.16)),
                deficit_weight=float(params.get("deficit_weight", 1.25)),
                capacity_weight=float(params.get("capacity_weight", 0.75)),
                reward_weight=float(params.get("reward_weight", 1.15)),
                local_only=bool(params.get("local_only", True)),
            ),
            max_passes=int(params.get("max_passes", 5)),
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
    if method == "tensor_quorum_flow_repair":
        return LocalRepairRecruitmentAllocator(
            name=method,
            base_allocator=PrimalDualRecruitmentAllocator(
                name="tensor_quorum_flow",
                distance_weight=float(params.get("distance_weight", 0.11)),
                deficit_weight=float(params.get("deficit_weight", 1.45)),
                capacity_weight=float(params.get("capacity_weight", 1.05)),
                reward_weight=float(params.get("reward_weight", 1.30)),
                wrench_weight=float(params.get("wrench_weight", 0.20)),
                local_only=True,
            ),
            max_passes=int(params.get("max_passes", 5)),
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
    """Exact binary MILP reference for complete SP1 coalitions.

    Binary ``x[i,k]`` assigns robot ``i`` to load ``k`` and ``y[k]`` activates
    a served load.  The model enforces one load per robot, quorum, payload
    capacity, and zero assignments to inactive loads.  Unassigned robots are
    the explicit idle state represented by label 0.
    """

    name: str = "centralized_coalition_milp"
    distance_weight: float = 0.01
    overassignment_weight: float = 0.03
    timeout_s: float = 5.0
    last_solve_status: str = "not_run"
    last_mip_gap: float = math.nan

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = _distance_matrix(context)
        robot_count, load_count = distances.shape
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=np.zeros(robot_count, dtype=int), method=self.name)
        demands = _load_demands(context).astype(float)
        rewards = np.array([load.reward for load in context.world.loads], dtype=float)
        payloads = np.array([robot.spec.capacity.payload_kg for robot in context.world.robots], dtype=float)
        required_capacity = np.array([load.min_capacity_kg for load in context.world.loads], dtype=float)
        x_count = robot_count * load_count
        variable_count = x_count + load_count
        objective = np.zeros(variable_count, dtype=float)
        for robot_idx in range(robot_count):
            for load_idx in range(load_count):
                variable_idx = robot_idx * load_count + load_idx
                objective[variable_idx] = (
                    self.distance_weight * distances[robot_idx, load_idx]
                    + self.overassignment_weight
                    + 1.0e-10 * (variable_idx + 1)
                )
        for load_idx in range(load_count):
            objective[x_count + load_idx] = (
                -rewards[load_idx]
                - self.overassignment_weight * demands[load_idx]
                + 1.0e-12 * (load_idx + 1)
            )

        rows: list[np.ndarray] = []
        lower: list[float] = []
        upper: list[float] = []
        for robot_idx in range(robot_count):
            row = np.zeros(variable_count, dtype=float)
            start = robot_idx * load_count
            row[start : start + load_count] = 1.0
            rows.append(row)
            lower.append(-np.inf)
            upper.append(1.0)
        for load_idx in range(load_count):
            assigned = np.zeros(variable_count, dtype=float)
            assigned[load_idx:x_count:load_count] = 1.0
            quorum = -assigned
            quorum[x_count + load_idx] = demands[load_idx]
            rows.append(quorum)
            lower.append(-np.inf)
            upper.append(0.0)

            activation = assigned.copy()
            activation[x_count + load_idx] = -float(robot_count)
            rows.append(activation)
            lower.append(-np.inf)
            upper.append(0.0)

            capacity = np.zeros(variable_count, dtype=float)
            capacity[load_idx:x_count:load_count] = -payloads
            capacity[x_count + load_idx] = required_capacity[load_idx]
            rows.append(capacity)
            lower.append(-np.inf)
            upper.append(0.0)

        result = milp(
            c=objective,
            integrality=np.ones(variable_count, dtype=int),
            bounds=Bounds(np.zeros(variable_count), np.ones(variable_count)),
            constraints=LinearConstraint(np.vstack(rows), np.asarray(lower), np.asarray(upper)),
            options={"time_limit": float(self.timeout_s), "mip_rel_gap": 0.0, "presolve": True},
        )
        status_names = {0: "optimal", 1: "timeout_or_limit", 2: "infeasible", 3: "unbounded", 4: "solver_error"}
        self.last_solve_status = status_names.get(int(result.status), f"unknown_{result.status}")
        self.last_mip_gap = float(getattr(result, "mip_gap", math.nan))
        if result.x is None:
            return Assignment(labels=np.zeros(robot_count, dtype=int), scores=-distances, method=self.name)
        x = np.asarray(result.x[:x_count], dtype=float).reshape(robot_count, load_count)
        labels = np.zeros(robot_count, dtype=int)
        active = np.max(x, axis=1) > 0.5
        labels[active] = np.argmax(x[active], axis=1) + 1
        return Assignment(labels=labels, scores=-distances, method=self.name)


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
class LocalRepairRecruitmentAllocator(BaseAllocator):
    """Monotone local repair wrapper for SP1 population/primal-dual allocators."""

    name: str = "local_repair_recruitment"
    base_allocator: BaseAllocator | None = None
    max_passes: int = 4

    def allocate(self, context: DecisionContext) -> Assignment:
        if self.base_allocator is None:
            raise ValueError("LocalRepairRecruitmentAllocator requires a base allocator.")
        base = self.base_allocator.allocate(context)
        repaired = _sp1_local_repair(context, base, method=self.name, max_passes=self.max_passes)
        return repaired


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


def _sp1_local_repair(context: DecisionContext, assignment: Assignment, *, method: str, max_passes: int) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int).copy()
    current = Assignment(labels=labels, method=method)
    current = _sp1_drop_incomplete_if_better(context, current, method)
    for _ in range(max(1, int(max_passes))):
        improved = False
        candidate = _sp1_best_completion_repair(context, current, method)
        if _sp1_score(context, candidate) > _sp1_score(context, current) + 1e-9:
            current = candidate
            improved = True
        candidate = _sp1_best_single_move(context, current, method)
        if _sp1_score(context, candidate) > _sp1_score(context, current) + 1e-9:
            current = candidate
            improved = True
        candidate = _sp1_drop_incomplete_if_better(context, current, method)
        if _sp1_score(context, candidate) > _sp1_score(context, current) + 1e-9:
            current = candidate
            improved = True
        if not improved:
            break
    return Assignment(labels=current.labels.copy(), method=method)


def _sp1_best_completion_repair(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int)
    best = Assignment(labels=labels.copy(), method=method)
    best_score = _sp1_score(context, best)
    distances = _distance_matrix(context)
    payloads = np.asarray([robot.spec.capacity.payload_kg for robot in context.world.robots], dtype=float)
    for load_idx in range(len(context.world.loads)):
        if _sp1_load_complete(context, best.labels, load_idx):
            continue
        current_members = set(int(idx) for idx in np.flatnonzero(best.labels == load_idx + 1))
        candidate_pool = [
            int(idx)
            for idx in range(len(context.world.robots))
            if idx in current_members or best.labels[idx] == 0 or not _sp1_load_complete(context, best.labels, int(best.labels[idx]) - 1)
        ]
        candidate_pool = sorted(set(candidate_pool), key=lambda idx: float(distances[idx, load_idx]))[: min(10, len(candidate_pool))]
        for size in range(1, min(6, len(candidate_pool)) + 1):
            for group in combinations(candidate_pool, size):
                next_labels = best.labels.copy()
                for robot_idx in group:
                    next_labels[int(robot_idx)] = load_idx + 1
                if not _sp1_load_complete(context, next_labels, load_idx):
                    continue
                candidate = Assignment(labels=next_labels, method=method)
                score = _sp1_score(context, candidate)
                if score > best_score + 1e-9:
                    best_score = score
                    best = candidate
    return best


def _sp1_best_single_move(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int)
    best = Assignment(labels=labels.copy(), method=method)
    best_score = _sp1_score(context, best)
    for robot_idx in range(len(context.world.robots)):
        original = int(labels[robot_idx])
        for label in range(len(context.world.loads) + 1):
            if label == original:
                continue
            next_labels = labels.copy()
            next_labels[robot_idx] = label
            candidate = Assignment(labels=next_labels, method=method)
            score = _sp1_score(context, candidate)
            if score > best_score + 1e-9:
                best_score = score
                best = candidate
    return best


def _sp1_drop_incomplete_if_better(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    current = Assignment(labels=np.asarray(assignment.labels, dtype=int).copy(), method=method)
    for load_idx in range(len(context.world.loads)):
        if _sp1_load_complete(context, current.labels, load_idx):
            continue
        if not np.any(current.labels == load_idx + 1):
            continue
        next_labels = current.labels.copy()
        next_labels[next_labels == load_idx + 1] = 0
        candidate = Assignment(labels=next_labels, method=method)
        if _sp1_score(context, candidate) >= _sp1_score(context, current) - 1e-9:
            current = candidate
    return current


def _sp1_score(context: DecisionContext, assignment: Assignment) -> float:
    labels = np.asarray(assignment.labels, dtype=int)
    reward = 0.0
    for load_idx, load in enumerate(context.world.loads):
        if _sp1_load_complete(context, labels, load_idx):
            reward += float(load.reward)
    distance = 0.0
    for robot_idx, label in enumerate(labels):
        if label <= 0:
            continue
        distance += float(np.linalg.norm(context.world.robots[robot_idx].position - context.world.loads[int(label) - 1].pickup))
    return float(reward - 0.05 * distance)


def _sp1_load_complete(context: DecisionContext, labels: np.ndarray, load_idx: int) -> bool:
    members = np.flatnonzero(labels == load_idx + 1)
    if members.size < int(context.world.loads[load_idx].min_coalition_size):
        return False
    payload = float(sum(context.world.robots[int(idx)].spec.capacity.payload_kg for idx in members))
    return bool(payload + 1e-9 >= float(context.world.loads[load_idx].min_capacity_kg))


def iter_complete_slot_plans(
    demands: np.ndarray,
    subset: tuple[int, ...],
    robot_count: int,
) -> list[tuple[tuple[int, ...], int]]:
    """Return feasible complete-coalition slot plans for a selected load subset.

    A load's SP1 cardinality is a lower bound. Extra AMR slots are enumerated so
    heterogeneous low-payload robots can be supplemented when capacity requires
    it. The returned integer is the number of extra robots beyond the minimum
    cardinality demand.
    """

    if not subset:
        return [((), 0)]
    base_counts = [int(demands[load_idx]) for load_idx in subset]
    required = int(sum(base_counts))
    if required > robot_count:
        return []
    plans: list[tuple[tuple[int, ...], int]] = []
    max_extra = robot_count - required
    for extras in _extra_robot_distributions(len(subset), max_extra):
        slot_loads: list[int] = []
        for load_idx, base, extra in zip(subset, base_counts, extras):
            slot_loads.extend([int(load_idx)] * (base + int(extra)))
        plans.append((tuple(slot_loads), int(sum(extras))))
    return plans


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


def _assign_capacity_feasible_plan(
    distances: np.ndarray,
    payloads: np.ndarray,
    required_capacity: np.ndarray,
    slot_loads: tuple[int, ...],
) -> tuple[np.ndarray | None, float]:
    labels = np.zeros(distances.shape[0], dtype=int)
    if not slot_loads:
        return labels, 0.0
    cost = distances[:, list(slot_loads)]
    rows, cols = linear_sum_assignment(cost)
    if rows.size < len(slot_loads):
        return None, math.inf
    total = 0.0
    for row, col in zip(rows, cols):
        labels[int(row)] = int(slot_loads[int(col)]) + 1
        total += float(cost[int(row), int(col)])
    for load_idx in set(slot_loads):
        assigned = np.flatnonzero(labels == int(load_idx) + 1)
        assigned_capacity = float(np.sum(payloads[assigned]))
        if assigned_capacity + 1e-9 < float(required_capacity[int(load_idx)]):
            return None, math.inf
    return labels, total


def _extra_robot_distributions(size: int, max_extra: int) -> list[tuple[int, ...]]:
    if size <= 0:
        return [()]
    output: list[tuple[int, ...]] = []

    def visit(index: int, remaining: int, prefix: list[int]) -> None:
        if index == size - 1:
            for value in range(remaining + 1):
                output.append(tuple(prefix + [value]))
            return
        for value in range(remaining + 1):
            visit(index + 1, remaining - value, prefix + [value])

    visit(0, max_extra, [])
    return output


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
