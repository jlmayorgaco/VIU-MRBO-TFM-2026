"""SP2 capacity-aware allocation methods."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp

from viu_mrob_tfm.allocation import Assignment, BaseAllocator, DecisionContext


SP2_METHOD_LABELS = {
    "greedy_capacity_nearest": "Greedy capacity nearest",
    "hungarian_capacity": "Hungarian capacity expanded",
    "centralized_capacity_milp": "Centralized capacity oracle",
    "cbba_capacity": "CBBA capacity auction",
    "replicator_capacity": "Replicator capacity",
    "replicator_capacity_plain": "Replicator capacity plain payoff",
    "replicator_capacity_marginal": "Replicator capacity marginal payoff",
    "replicator_capacity_marginal_repair": "Replicator marginal capacity local repair",
    "bnn_capacity": "BNN capacity",
    "bnn_capacity_repair": "Brown/BNN capacity local repair",
    "logit_capacity_repair": "Logit capacity local repair",
    "smith_capacity": "Smith-QR capacity",
    "smith_capacity_plain": "Smith-QR capacity plain payoff",
    "smith_capacity_marginal": "Smith-QR capacity marginal payoff",
    "smith_capacity_marginal_repair": "Smith-QR marginal capacity local repair",
    "primal_dual_capacity": "Primal-dual capacity",
    "primal_dual_capacity_repair": "Primal-dual capacity local repair",
    "local_primal_dual_capacity": "Local primal-dual capacity",
    "pid_capacity_repair": "PID capacity local repair",
    "imitation_capacity": "Data-driven capacity imitation",
    "neural_capacity_scorer": "Neural capacity scorer",
    "oracle_reference": "Oracle reference",
    "capacity_oracle_reference": "Pure capacity oracle reference",
}

SP2_METHOD_METADATA = {
    "greedy_capacity_nearest": ("classic", "decentralized", "baseline", "nearest_capacity_greedy", "classic_decentralized_baseline"),
    "hungarian_capacity": ("classic", "centralized", "baseline", "hungarian_capacity_expanded", "classic_centralized_baseline"),
    "centralized_capacity_milp": ("model_based_oracle", "centralized", "reference", "exact_effective_capacity_milp", "centralized_oracle_reference"),
    "cbba_capacity": ("sota", "decentralized", "baseline", "cbba_payload_capacity_proxy", "sota_decentralized_baseline"),
    "replicator_capacity": ("model_based", "decentralized", "baseline", "population_game_capacity", "model_based_decentralized_baseline"),
    "replicator_capacity_plain": ("model_based", "decentralized", "baseline", "population_game_plain_payoff", "sp2_plain_vs_marginal_ablation"),
    "replicator_capacity_marginal": ("model_based", "decentralized", "baseline", "population_game_marginal_capacity_payoff", "sp2_plain_vs_marginal_ablation"),
    "replicator_capacity_marginal_repair": ("model_based", "decentralized", "proposed", "replicator_marginal_completion_repair", "proposed_local_repair_family"),
    "bnn_capacity": ("model_based", "decentralized", "baseline", "bnn_capacity_utility", "model_based_decentralized_baseline"),
    "bnn_capacity_repair": ("model_based", "decentralized", "proposed", "brown_bnn_completion_repair", "proposed_local_repair_family"),
    "logit_capacity_repair": ("model_based", "decentralized", "proposed", "logit_completion_repair", "proposed_local_repair_family"),
    "smith_capacity": ("model_based", "decentralized", "proposed", "smith_qr_effective_capacity", "proposed_model_based_variation"),
    "smith_capacity_plain": ("model_based", "decentralized", "proposed", "smith_qr_plain_payoff", "sp2_plain_vs_marginal_ablation"),
    "smith_capacity_marginal": ("model_based", "decentralized", "proposed", "smith_qr_marginal_capacity_payoff", "sp2_plain_vs_marginal_ablation"),
    "smith_capacity_marginal_repair": ("model_based", "decentralized", "proposed", "smith_qr_marginal_completion_repair", "proposed_local_repair_family"),
    "primal_dual_capacity": ("model_based", "decentralized", "proposed", "primal_dual_effective_capacity", "proposed_model_based_variation"),
    "primal_dual_capacity_repair": ("model_based", "decentralized", "proposed", "primal_dual_completion_repair", "proposed_local_repair_family"),
    "local_primal_dual_capacity": ("model_based", "decentralized_local", "proposed", "local_primal_dual_effective_capacity", "proposed_local_variation"),
    "pid_capacity_repair": ("model_based", "decentralized_local", "proposed", "pid_completion_error_repair", "proposed_local_repair_family"),
    "imitation_capacity": ("data_driven", "decentralized", "baseline", "oracle_capacity_imitation_linear", "data_driven_baseline"),
    "neural_capacity_scorer": ("data_driven", "decentralized", "proposed", "oracle_capacity_neural_scorer", "proposed_data_driven_variation"),
    "oracle_reference": ("model_based_oracle", "centralized", "reference", "exact_capacity_reference_replay", "centralized_oracle_reference"),
    "capacity_oracle_reference": ("model_based_oracle", "centralized", "reference", "exact_capacity_coverage_replay", "centralized_capacity_ceiling_reference"),
}

SP2_METHOD_RESOURCE_METADATA = {
    "greedy_capacity_nearest": ("none", "distributed_capacity_greedy_rule", "local_robot_load_distance_capacity", 0, 0, False, False),
    "hungarian_capacity": ("none", "centralized_capacity_slot_assignment", "centralized_all_robot_load_pairs", 0, 0, False, False),
    "centralized_capacity_milp": ("none", "centralized_binary_milp_effective_capacity", "centralized_all_robot_load_pairs", 0, 3, False, False),
    "cbba_capacity": ("none", "distributed_payload_auction_proxy", "auction_bids_capacity_deficit", 0, 3, False, False),
    "replicator_capacity": ("model_based_tuning_optional", "distributed_capacity_utility_rule", "local_capacity_deficit_scores", 0, 4, False, False),
    "replicator_capacity_plain": ("none", "distributed_plain_capacity_payoff_rule", "local_deficit_pressure_scores", 0, 4, False, False),
    "replicator_capacity_marginal": ("none", "distributed_marginal_capacity_payoff_rule", "local_effective_capacity_marginal_scores", 0, 4, False, False),
    "replicator_capacity_marginal_repair": ("model_based_tuning_optional", "distributed_marginal_capacity_plus_local_repair", "local_effective_capacity_scores_plus_small_repair_neighborhood", 0, 7, False, False),
    "bnn_capacity": ("model_based_tuning_optional", "distributed_nonlinear_capacity_rule", "local_capacity_deficit_scores", 0, 5, False, False),
    "bnn_capacity_repair": ("model_based_tuning_optional", "distributed_bnn_capacity_plus_local_repair", "positive_excess_scores_plus_small_repair_neighborhood", 0, 8, False, False),
    "logit_capacity_repair": ("model_based_tuning_optional", "distributed_logit_capacity_plus_local_repair", "softmax_capacity_scores_plus_small_repair_neighborhood", 0, 8, False, False),
    "smith_capacity": ("model_based_tuning_optional", "distributed_smith_qr_capacity_rule", "local_effective_capacity_scores", 0, 4, False, False),
    "smith_capacity_plain": ("none", "distributed_smith_qr_plain_payoff_rule", "local_deficit_pressure_scores", 0, 4, False, False),
    "smith_capacity_marginal": ("none", "distributed_smith_qr_marginal_payoff_rule", "local_effective_capacity_marginal_scores", 0, 4, False, False),
    "smith_capacity_marginal_repair": ("model_based_tuning_optional", "distributed_smith_qr_marginal_plus_local_repair", "local_effective_capacity_marginal_scores_plus_small_repair_neighborhood", 0, 7, False, False),
    "primal_dual_capacity": ("model_based_tuning_optional", "distributed_primal_dual_capacity_rule", "local_capacity_prices", 0, 5, False, False),
    "primal_dual_capacity_repair": ("model_based_tuning_optional", "distributed_primal_dual_capacity_plus_local_repair", "local_capacity_prices_plus_small_repair_neighborhood", 0, 8, False, False),
    "local_primal_dual_capacity": ("model_based_tuning_optional", "local_primal_dual_capacity_rule", "radius_limited_capacity_scores", 0, 5, False, False),
    "pid_capacity_repair": ("model_based_tuning_optional", "distributed_pid_capacity_error_plus_local_repair", "local_integral_deficit_error_plus_small_repair_neighborhood", 0, 7, False, False),
    "imitation_capacity": ("supervised_oracle_imitation", "distributed_linear_capacity_score_policy", "local_robot_load_capacity_features", 8, 1, False, False),
    "neural_capacity_scorer": ("supervised_oracle_imitation", "distributed_neural_capacity_score_policy", "local_robot_load_capacity_features", 97, 3, True, False),
    "oracle_reference": ("none", "centralized_exact_reference_replay", "centralized_all_robot_load_pairs", 0, 3, False, False),
    "capacity_oracle_reference": ("none", "centralized_exact_capacity_ceiling_replay", "centralized_all_robot_load_pairs", 0, 2, False, False),
}


def sp2_method_metadata(method_id: str) -> dict[str, Any]:
    method = method_id.lower()
    family, scope, ownership, variant, comparison_group = SP2_METHOD_METADATA.get(
        method,
        ("unknown", "unknown", "unknown", method, "unknown"),
    )
    training_type, execution_model, communication_pattern, trainable_parameters, tuned_parameters, uses_neural, uses_decoder = (
        SP2_METHOD_RESOURCE_METADATA.get(method, ("unknown", "unknown", "unknown", 0, 0, False, False))
    )
    label = SP2_METHOD_LABELS.get(method, method.replace("_", " "))
    return {
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "comparison_group": comparison_group,
        "training_type": training_type,
        "execution_model": execution_model,
        "communication_pattern": communication_pattern,
        "trainable_parameters": trainable_parameters,
        "tuned_parameters": tuned_parameters,
        "uses_neural_policy": uses_neural,
        "uses_decoder": uses_decoder,
        "label": label,
        "file_tag": f"{ownership}-{family}-{scope}-{variant}-{method}".replace("_", "-"),
        "title": f"{label} [{ownership} | {family} | {scope} | {variant}]",
    }


def make_sp2_allocator(method_id: str, params: dict[str, Any] | None = None) -> BaseAllocator:
    params = dict(params or {})
    method = method_id.lower()
    if method == "greedy_capacity_nearest":
        return GreedyCapacityAllocator(name=method, distance_weight=float(params.get("distance_weight", 0.45)))
    if method == "hungarian_capacity":
        return HungarianCapacityAllocator(name=method, distance_weight=float(params.get("distance_weight", 0.5)))
    if method == "centralized_capacity_milp":
        return CentralizedCapacityMILPAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.0005)),
            energy_weight=float(params.get("energy_weight", 0.00001)),
            partial_capacity_weight=float(params.get("partial_capacity_weight", 100.0)),
            reward_weight=float(params.get("reward_weight", 5.0)),
        )
    if method == "cbba_capacity":
        return CapacityAuctionAllocator(name=method, distance_weight=float(params.get("distance_weight", 0.32)), deficit_weight=1.1)
    if method == "replicator_capacity":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.28)),
            deficit_weight=float(params.get("deficit_weight", 1.0)),
            reward_weight=float(params.get("reward_weight", 0.85)),
            capacity_weight=float(params.get("capacity_weight", 0.8)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.0)),
        )
    if method == "replicator_capacity_plain":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.04)),
            deficit_weight=float(params.get("deficit_weight", 1.0)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            capacity_weight=float(params.get("capacity_weight", 1.0)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.0)),
            payoff_mode="plain",
        )
    if method == "replicator_capacity_marginal":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.04)),
            deficit_weight=float(params.get("deficit_weight", 1.0)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            capacity_weight=float(params.get("capacity_weight", 1.0)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.0)),
            payoff_mode="marginal",
        )
    if method == "replicator_capacity_marginal_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=UtilityCapacityAllocator(
                name="replicator_capacity_marginal",
                distance_weight=float(params.get("distance_weight", 0.04)),
                deficit_weight=float(params.get("deficit_weight", 1.0)),
                reward_weight=float(params.get("reward_weight", 1.0)),
                capacity_weight=float(params.get("capacity_weight", 1.0)),
                completion_weight=float(params.get("completion_weight", 0.25)),
                exponent=float(params.get("exponent", 1.0)),
                payoff_mode="marginal",
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "bnn_capacity":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.22)),
            deficit_weight=float(params.get("deficit_weight", 1.15)),
            reward_weight=float(params.get("reward_weight", 0.95)),
            capacity_weight=float(params.get("capacity_weight", 0.8)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 2.0)),
        )
    if method == "bnn_capacity_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=UtilityCapacityAllocator(
                name="bnn_capacity",
                distance_weight=float(params.get("distance_weight", 0.22)),
                deficit_weight=float(params.get("deficit_weight", 1.15)),
                reward_weight=float(params.get("reward_weight", 0.95)),
                capacity_weight=float(params.get("capacity_weight", 0.8)),
                completion_weight=float(params.get("completion_weight", 0.25)),
                exponent=float(params.get("exponent", 2.0)),
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "logit_capacity_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=UtilityCapacityAllocator(
                name="logit_capacity",
                distance_weight=float(params.get("distance_weight", 0.08)),
                deficit_weight=float(params.get("deficit_weight", 1.25)),
                reward_weight=float(params.get("reward_weight", 1.05)),
                capacity_weight=float(params.get("capacity_weight", 1.15)),
                completion_weight=float(params.get("completion_weight", 0.35)),
                exponent=float(params.get("inverse_temperature", 1.45)),
                payoff_mode="marginal",
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "smith_capacity":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.18)),
            deficit_weight=float(params.get("deficit_weight", 1.45)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            capacity_weight=float(params.get("capacity_weight", 1.2)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.15)),
        )
    if method == "smith_capacity_plain":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.035)),
            deficit_weight=float(params.get("deficit_weight", 1.35)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            capacity_weight=float(params.get("capacity_weight", 1.0)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.15)),
            payoff_mode="plain",
        )
    if method == "smith_capacity_marginal":
        return UtilityCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.035)),
            deficit_weight=float(params.get("deficit_weight", 1.35)),
            reward_weight=float(params.get("reward_weight", 1.0)),
            capacity_weight=float(params.get("capacity_weight", 1.0)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            exponent=float(params.get("exponent", 1.15)),
            payoff_mode="marginal",
        )
    if method == "smith_capacity_marginal_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=UtilityCapacityAllocator(
                name="smith_capacity_marginal",
                distance_weight=float(params.get("distance_weight", 0.035)),
                deficit_weight=float(params.get("deficit_weight", 1.35)),
                reward_weight=float(params.get("reward_weight", 1.0)),
                capacity_weight=float(params.get("capacity_weight", 1.0)),
                completion_weight=float(params.get("completion_weight", 0.35)),
                exponent=float(params.get("exponent", 1.15)),
                payoff_mode="marginal",
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "primal_dual_capacity":
        return PrimalDualCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.15)),
            deficit_weight=float(params.get("deficit_weight", 1.55)),
            capacity_weight=float(params.get("capacity_weight", 1.35)),
            reward_weight=float(params.get("reward_weight", 1.1)),
            completion_weight=float(params.get("completion_weight", 0.0)),
        )
    if method == "primal_dual_capacity_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=PrimalDualCapacityAllocator(
                name="primal_dual_capacity",
                distance_weight=float(params.get("distance_weight", 0.15)),
                deficit_weight=float(params.get("deficit_weight", 1.55)),
                capacity_weight=float(params.get("capacity_weight", 1.35)),
                reward_weight=float(params.get("reward_weight", 1.1)),
                completion_weight=float(params.get("completion_weight", 0.4)),
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "local_primal_dual_capacity":
        return PrimalDualCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.14)),
            deficit_weight=float(params.get("deficit_weight", 1.55)),
            capacity_weight=float(params.get("capacity_weight", 1.35)),
            reward_weight=float(params.get("reward_weight", 1.1)),
            completion_weight=float(params.get("completion_weight", 0.0)),
            local_only=True,
        )
    if method == "pid_capacity_repair":
        return LocalRepairCapacityAllocator(
            name=method,
            base_allocator=PrimalDualCapacityAllocator(
                name="pid_capacity",
                distance_weight=float(params.get("distance_weight", 0.12)),
                deficit_weight=float(params.get("deficit_weight", 1.75)),
                capacity_weight=float(params.get("capacity_weight", 1.15)),
                reward_weight=float(params.get("reward_weight", 1.0)),
                completion_weight=float(params.get("completion_weight", 0.65)),
                local_only=bool(params.get("local_only", True)),
            ),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "capacity_oracle_reference":
        return CentralizedCapacityCoverageMILPAllocator()
    if method == "imitation_capacity":
        return ImitationCapacityAllocator(
            name=method,
            model_path=None if params.get("checkpoint") is None else Path(str(params["checkpoint"])),
        )
    if method == "neural_capacity_scorer":
        return NeuralCapacityScorerAllocator(
            name=method,
            model_path=None if params.get("checkpoint") is None else Path(str(params["checkpoint"])),
        )
    raise ValueError(f"Unknown SP2 method id: {method_id}")


def sp2_potential_alignment(method_id: str) -> dict[str, Any]:
    """Audit whether an SP2 payoff matches the marginal-capacity potential theorem."""

    method = method_id.lower()
    if method in {"oracle_reference", "capacity_oracle_reference", "centralized_capacity_milp"}:
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": True,
            "potential_structure": "centralized_reference_not_population_payoff",
            "theorem": "Teorema 2",
        }
    if method.endswith("_marginal"):
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": True,
            "potential_structure": "exact",
            "theorem": "Teorema 2",
        }
    if method.endswith("_marginal_repair"):
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": True,
            "potential_structure": "marginal_payoff_plus_monotone_finite_local_repair",
            "theorem": "Teorema 2 + local repair monotonicity lemma",
        }
    if method.endswith("_plain"):
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": False,
            "potential_structure": "not_guaranteed_unless_eik_factorizes",
            "theorem": "Teorema 2",
        }
    if method.endswith("_repair"):
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": False,
            "potential_structure": "heuristic_payoff_plus_monotone_finite_local_repair",
            "theorem": "local repair monotonicity lemma",
        }
    if method in {"replicator_capacity", "bnn_capacity", "smith_capacity", "primal_dual_capacity", "local_primal_dual_capacity"}:
        return {
            "uses_effective_capacity_in_state": True,
            "payoff_uses_marginal_capacity": False,
            "potential_structure": "heuristic_hybrid_not_theorem_exact",
            "theorem": "Teorema 2",
        }
    return {
        "uses_effective_capacity_in_state": True,
        "payoff_uses_marginal_capacity": False,
        "potential_structure": "not_a_population_payoff_or_not_audited",
        "theorem": "Teorema 2",
    }


@dataclass(slots=True)
class CentralizedCapacityMILPAllocator(BaseAllocator):
    """Binary MILP oracle for effective-capacity coverage."""

    name: str = "centralized_capacity_milp"
    distance_weight: float = 0.0005
    energy_weight: float = 0.00001
    partial_capacity_weight: float = 100.0
    reward_weight: float = 5.0

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        rewards = load_rewards(context)
        demands = load_capacity_demands(context)
        energy = energy_matrix(context)
        x_count = robot_count * load_count
        y_count = load_count
        s_count = load_count
        variable_count = x_count + y_count + s_count
        c = np.zeros(variable_count, dtype=float)
        c[:x_count] = self.distance_weight * distances.ravel() + self.energy_weight * energy.ravel()
        c[x_count : x_count + y_count] = -self.reward_weight * rewards
        c[x_count + y_count :] = -self.partial_capacity_weight / np.maximum(demands, 1e-9)
        integrality = np.zeros(variable_count, dtype=int)
        integrality[: x_count + y_count] = 1
        lower_bounds = np.zeros(variable_count, dtype=float)
        upper_bounds = np.ones(variable_count, dtype=float)
        upper_bounds[x_count + y_count :] = demands
        bounds = Bounds(lower_bounds, upper_bounds)
        constraints = []

        for robot_idx in range(robot_count):
            row = np.zeros(variable_count, dtype=float)
            for load_idx in range(load_count):
                row[_x_index(robot_idx, load_idx, load_count)] = 1.0
            constraints.append(LinearConstraint(row, -np.inf, 1.0))

        for load_idx in range(load_count):
            # Mark a load as fully served only when effective capacity covers
            # the required demand. This keeps the binary success metric honest.
            full_capacity = np.zeros(variable_count, dtype=float)
            for robot_idx in range(robot_count):
                full_capacity[_x_index(robot_idx, load_idx, load_count)] = eff[robot_idx, load_idx]
            full_capacity[_y_index(robot_count, load_count, load_idx)] = -demands[load_idx]
            constraints.append(LinearConstraint(full_capacity, 0.0, np.inf))

            card = np.zeros(variable_count, dtype=float)
            for robot_idx in range(robot_count):
                card[_x_index(robot_idx, load_idx, load_count)] = 1.0
            card[_y_index(robot_count, load_count, load_idx)] = -float(context.world.loads[load_idx].min_coalition_size)
            constraints.append(LinearConstraint(card, 0.0, np.inf))

            # Continuous coverage variable: s_k <= sum_i effective_capacity_ik x_ik.
            # This allows the oracle to value partial coverage in overloaded
            # regimes instead of discarding under-capacity assignments.
            partial_capacity = np.zeros(variable_count, dtype=float)
            for robot_idx in range(robot_count):
                partial_capacity[_x_index(robot_idx, load_idx, load_count)] = -eff[robot_idx, load_idx]
            partial_capacity[_s_index(robot_count, load_count, load_idx)] = 1.0
            constraints.append(LinearConstraint(partial_capacity, -np.inf, 0.0))

        result = milp(c=c, integrality=integrality, bounds=bounds, constraints=constraints, options={"time_limit": 8.0})
        if not result.success or result.x is None:
            return _fallback_capacity_oracle(context, self.name)
        x = np.asarray(result.x[:x_count]).reshape(robot_count, load_count)
        for robot_idx in range(robot_count):
            if float(np.max(x[robot_idx])) > 0.5:
                labels[robot_idx] = int(np.argmax(x[robot_idx])) + 1
        return Assignment(labels=labels, scores=-distances, method=self.name)


@dataclass(slots=True)
class CentralizedCapacityCoverageMILPAllocator(CentralizedCapacityMILPAllocator):
    """Pure capacity-ceiling MILP with only physical-capacity coverage as primary objective."""

    name: str = "capacity_oracle_reference"
    distance_weight: float = 0.00001
    energy_weight: float = 0.0
    partial_capacity_weight: float = 1000.0
    reward_weight: float = 0.0


@dataclass(slots=True)
class GreedyCapacityAllocator(BaseAllocator):
    """Local greedy capacity allocator."""

    name: str = "greedy_capacity_nearest"
    distance_weight: float = 0.45

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.zeros((robot_count, load_count), dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        deficits = load_capacity_demands(context).copy()
        rewards = load_rewards(context)
        for robot_idx in np.argsort(np.min(distances, axis=1)):
            open_loads = np.flatnonzero(deficits > 1e-9)
            if open_loads.size == 0:
                break
            utility = rewards[open_loads] + eff[int(robot_idx), open_loads] / np.maximum(deficits[open_loads], 1.0) - self.distance_weight * distances[int(robot_idx), open_loads]
            load_idx = int(open_loads[int(np.argmax(utility))])
            labels[int(robot_idx)] = load_idx + 1
            scores[int(robot_idx), load_idx] = float(np.max(utility))
            deficits[load_idx] = max(0.0, deficits[load_idx] - eff[int(robot_idx), load_idx])
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class HungarianCapacityAllocator(BaseAllocator):
    """Centralized classic capacity baseline using expanded capacity slots."""

    name: str = "hungarian_capacity"
    distance_weight: float = 0.5

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        demands = load_capacity_demands(context)
        median_payload = max(float(np.median([robot.spec.capacity.payload_kg for robot in context.world.robots])), 1.0)
        slot_loads = []
        for load_idx, demand in enumerate(demands):
            slots = max(context.world.loads[load_idx].min_coalition_size, int(math.ceil(float(demand) / median_payload)))
            slot_loads.extend([load_idx] * slots)
        if not slot_loads:
            return Assignment(labels=labels, method=self.name)
        slot_array = np.asarray(slot_loads, dtype=int)
        rewards = load_rewards(context)
        cost = self.distance_weight * distances[:, slot_array] - 0.018 * eff[:, slot_array] - 0.15 * rewards[slot_array][None, :]
        rows, cols = linear_sum_assignment(cost)
        for row, col in zip(rows, cols):
            labels[int(row)] = int(slot_array[int(col)]) + 1
        return Assignment(labels=labels, scores=-cost, method=self.name)


@dataclass(slots=True)
class CapacityAuctionAllocator(BaseAllocator):
    """CBBA-like payload/capacity auction proxy."""

    name: str = "cbba_capacity"
    distance_weight: float = 0.32
    deficit_weight: float = 1.1
    max_rounds: int = 64

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.zeros((robot_count, load_count), dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        deficits = load_capacity_demands(context).copy()
        rewards = load_rewards(context)
        available = np.ones(robot_count, dtype=bool)
        for _ in range(min(self.max_rounds, robot_count)):
            open_loads = np.flatnonzero(deficits > 1e-9)
            if open_loads.size == 0 or not np.any(available):
                break
            best: tuple[float, int, int] | None = None
            for robot_idx in np.flatnonzero(available):
                gain = np.minimum(eff[int(robot_idx), open_loads], deficits[open_loads]) / np.maximum(deficits[open_loads], 1.0)
                utility = rewards[open_loads] + self.deficit_weight * gain - self.distance_weight * distances[int(robot_idx), open_loads]
                load_idx = int(open_loads[int(np.argmax(utility))])
                score = float(np.max(utility))
                scores[int(robot_idx), load_idx] = score
                if best is None or score > best[0]:
                    best = (score, int(robot_idx), load_idx)
            if best is None:
                break
            _score, robot_idx, load_idx = best
            labels[robot_idx] = load_idx + 1
            deficits[load_idx] = max(0.0, deficits[load_idx] - eff[robot_idx, load_idx])
            available[robot_idx] = False
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class UtilityCapacityAllocator(BaseAllocator):
    """Population-game-style capacity utility allocator."""

    name: str
    distance_weight: float = 0.2
    deficit_weight: float = 1.0
    reward_weight: float = 1.0
    capacity_weight: float = 0.8
    completion_weight: float = 0.0
    exponent: float = 1.0
    payoff_mode: str = "hybrid"

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.zeros((robot_count, load_count), dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        deficits = load_capacity_demands(context).copy()
        rewards = load_rewards(context)
        demands = load_capacity_demands(context)
        for robot_idx in np.argsort(np.min(distances, axis=1)):
            deficit_ratio = deficits / np.maximum(demands, 1.0)
            capacity_gain = np.minimum(eff[int(robot_idx)], deficits) / np.maximum(demands, 1.0)
            capacity_ratio = eff[int(robot_idx)] / np.maximum(demands, 1.0)
            completion = (eff[int(robot_idx)] + 1e-9 >= deficits).astype(float)
            if self.payoff_mode == "plain":
                deficit_pressure = self.reward_weight * rewards * deficit_ratio
                utility = (
                    self.deficit_weight * deficit_pressure
                    + self.completion_weight * completion
                    - self.distance_weight * distances[int(robot_idx)]
                )
            elif self.payoff_mode == "marginal":
                deficit_pressure = self.reward_weight * rewards * deficit_ratio
                utility = (
                    self.deficit_weight * self.capacity_weight * capacity_ratio * deficit_pressure
                    + self.completion_weight * completion
                    - self.distance_weight * distances[int(robot_idx)]
                )
            else:
                utility = (
                    self.reward_weight * rewards
                    + self.deficit_weight * deficit_ratio
                    + self.capacity_weight * capacity_gain
                    + self.completion_weight * completion
                    - self.distance_weight * distances[int(robot_idx)]
                )
            utility = np.maximum(utility, 0.0) ** self.exponent
            utility = np.where(deficits > 1e-9, utility, -np.inf)
            scores[int(robot_idx)] = utility
            if not np.isfinite(np.max(utility)):
                continue
            load_idx = int(np.argmax(utility))
            labels[int(robot_idx)] = load_idx + 1
            deficits[load_idx] = max(0.0, deficits[load_idx] - eff[int(robot_idx), load_idx])
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class PrimalDualCapacityAllocator(BaseAllocator):
    """Primal-dual capacity allocator with optional radius-limited visibility."""

    name: str
    distance_weight: float = 0.15
    deficit_weight: float = 1.55
    capacity_weight: float = 1.35
    reward_weight: float = 1.1
    completion_weight: float = 0.0
    local_only: bool = False

    def allocate(self, context: DecisionContext) -> Assignment:
        distances = distance_matrix(context)
        eff = effective_capacity_matrix(context)
        robot_count, load_count = distances.shape
        labels = np.zeros(robot_count, dtype=int)
        scores = np.full((robot_count, load_count), -np.inf, dtype=float)
        if robot_count == 0 or load_count == 0:
            return Assignment(labels=labels, method=self.name)
        demands = load_capacity_demands(context)
        deficits = demands.copy()
        rewards = load_rewards(context)
        available = np.ones(robot_count, dtype=bool)
        radius = float(context.metadata.get("communication_radius", np.inf))
        for _ in range(robot_count):
            best: tuple[float, int, int] | None = None
            for robot_idx in np.flatnonzero(available):
                visible = np.arange(load_count)
                if self.local_only and np.isfinite(radius):
                    visible = visible[distances[int(robot_idx)] <= radius]
                visible = visible[deficits[visible] > 1e-9]
                if visible.size == 0:
                    continue
                dual_price = deficits[visible] / np.maximum(demands[visible], 1.0)
                cap_gain = np.minimum(eff[int(robot_idx), visible], deficits[visible]) / np.maximum(demands[visible], 1.0)
                completion = (eff[int(robot_idx), visible] + 1e-9 >= deficits[visible]).astype(float)
                utility = (
                    self.reward_weight * rewards[visible]
                    + self.deficit_weight * dual_price
                    + self.capacity_weight * cap_gain
                    + self.completion_weight * completion
                    - self.distance_weight * distances[int(robot_idx), visible]
                )
                load_idx = int(visible[int(np.argmax(utility))])
                score = float(np.max(utility))
                scores[int(robot_idx), load_idx] = score
                if best is None or score > best[0]:
                    best = (score, int(robot_idx), load_idx)
            if best is None:
                break
            _score, robot_idx, load_idx = best
            labels[robot_idx] = load_idx + 1
            deficits[load_idx] = max(0.0, deficits[load_idx] - eff[robot_idx, load_idx])
            available[robot_idx] = False
        return Assignment(labels=labels, scores=scores, method=self.name)


@dataclass(slots=True)
class LocalRepairCapacityAllocator(BaseAllocator):
    """Finite monotone local repair wrapper for SP2 capacity allocators."""

    name: str = "local_repair_capacity"
    base_allocator: BaseAllocator | None = None
    max_passes: int = 4

    def allocate(self, context: DecisionContext) -> Assignment:
        if self.base_allocator is None:
            raise ValueError("LocalRepairCapacityAllocator requires a base allocator.")
        base = self.base_allocator.allocate(context)
        return _sp2_completion_repair(context, base, method=self.name, max_passes=self.max_passes)


@dataclass(slots=True)
class ImitationCapacityAllocator(BaseAllocator):
    """Frozen linear scorer trained from the SP2 capacity oracle."""

    name: str = "imitation_capacity"
    model_path: Path | None = None

    def allocate(self, context: DecisionContext) -> Assignment:
        model = _load_linear_model(self.model_path)
        weights = np.asarray(model["weights"], dtype=float)
        return _score_decode(context, self.name, lambda features: features @ weights)


@dataclass(slots=True)
class NeuralCapacityScorerAllocator(BaseAllocator):
    """Small neural-style nonlinear capacity scorer.

    The default weights are deterministic and compact. If a JSON checkpoint is
    provided, it is used as a one-hidden-layer MLP scorer.
    """

    name: str = "neural_capacity_scorer"
    model_path: Path | None = None

    def allocate(self, context: DecisionContext) -> Assignment:
        model = _load_neural_model(self.model_path)
        w1 = np.asarray(model["w1"], dtype=float)
        b1 = np.asarray(model["b1"], dtype=float)
        w2 = np.asarray(model["w2"], dtype=float)
        b2 = float(model["b2"])

        def scorer(features: np.ndarray) -> np.ndarray:
            hidden = np.tanh(features @ w1 + b1)
            return hidden @ w2 + b2

        return _score_decode(context, self.name, scorer)


FEATURE_NAMES = [
    "bias",
    "reward",
    "capacity_deficit_ratio",
    "effective_capacity_ratio",
    "distance_norm",
    "battery",
    "visibility",
    "mass_norm",
]


def fit_imitation_model(contexts: list[DecisionContext], oracle: BaseAllocator) -> dict[str, Any]:
    x, y = _imitation_dataset(contexts, oracle, shaped=True)
    ridge = 1e-5 * np.eye(x.shape[1], dtype=float)
    weights = np.linalg.solve(x.T @ x + ridge, x.T @ y)
    return {
        "model_version": "sp2-imitation-capacity-linear-v2",
        "feature_names": FEATURE_NAMES,
        "weights": [float(value) for value in weights],
        "target": "oracle_assignment_plus_capacity_utility",
    }


def fit_neural_imitation_model(
    contexts: list[DecisionContext],
    oracle: BaseAllocator,
    *,
    hidden_dim: int = 8,
    epochs: int = 180,
    learning_rate: float = 0.015,
    random_seed: int = 2026,
) -> dict[str, Any]:
    """Train a compact one-hidden-layer scorer by oracle imitation."""

    import torch

    x_np, y_np = _imitation_dataset(contexts, oracle, shaped=True)
    torch.manual_seed(int(random_seed))
    x = torch.as_tensor(x_np, dtype=torch.float32)
    y = torch.as_tensor(y_np[:, None], dtype=torch.float32)
    model = torch.nn.Sequential(
        torch.nn.Linear(x.shape[1], int(hidden_dim)),
        torch.nn.Tanh(),
        torch.nn.Linear(int(hidden_dim), 1),
    )
    loss_fn = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate), weight_decay=1e-4)
    history = []
    for _epoch in range(int(epochs)):
        optimizer.zero_grad(set_to_none=True)
        prediction = model(x)
        loss = loss_fn(prediction, y)
        loss.backward()
        optimizer.step()
        history.append(float(loss.detach().item()))
    first = model[0]
    second = model[2]
    w1 = first.weight.detach().cpu().numpy().T
    b1 = first.bias.detach().cpu().numpy()
    w2 = second.weight.detach().cpu().numpy().reshape(-1)
    b2 = float(second.bias.detach().cpu().numpy().reshape(-1)[0])
    return {
        "model_version": "sp2-neural-capacity-imitation-v2",
        "feature_names": FEATURE_NAMES,
        "w1": w1.astype(float).tolist(),
        "b1": b1.astype(float).tolist(),
        "w2": w2.astype(float).tolist(),
        "b2": b2,
        "target": "oracle_assignment_plus_capacity_utility",
        "hidden_dim": int(hidden_dim),
        "training_episodes": int(epochs),
        "training_loss_initial": history[0] if history else math.nan,
        "training_loss_final": history[-1] if history else math.nan,
    }


def _imitation_dataset(contexts: list[DecisionContext], oracle: BaseAllocator, *, shaped: bool) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    targets = []
    for context in contexts:
        assignment = oracle.allocate(context)
        features = feature_tensor(context)
        rewards = load_rewards(context)
        reward_norm = rewards / max(float(np.max(rewards)) if rewards.size else 1.0, 1.0)
        for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
            for load_idx in range(len(context.world.loads)):
                pair = features[robot_idx, load_idx]
                rows.append(pair)
                assigned = 1.0 if label == load_idx + 1 else 0.0
                if shaped:
                    effective_capacity_ratio = min(float(pair[3]), 1.6)
                    distance_norm = float(pair[4])
                    battery = float(pair[5])
                    visible = float(pair[6])
                    target = (
                        2.1 * assigned
                        + 1.35 * effective_capacity_ratio
                        + 0.35 * float(reward_norm[load_idx])
                        + 0.2 * battery
                        + 0.2 * visible
                        - 1.05 * distance_norm
                    )
                    targets.append(target)
                else:
                    targets.append(assigned)
    x = np.asarray(rows, dtype=float)
    y = np.asarray(targets, dtype=float)
    if x.size == 0:
        raise ValueError("SP2 imitation training requires at least one robot-load pair.")
    return x, y


def _sp2_completion_repair(context: DecisionContext, assignment: Assignment, *, method: str, max_passes: int) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int).copy()
    current = Assignment(labels=labels, method=method)
    current = _sp2_drop_incomplete_if_better(context, current, method)
    for _ in range(max(1, int(max_passes))):
        improved = False
        candidate = _sp2_best_completion_repair(context, current, method)
        if _sp2_completion_score(context, candidate) > _sp2_completion_score(context, current) + 1e-9:
            current = candidate
            improved = True
        candidate = _sp2_best_single_move(context, current, method)
        if _sp2_completion_score(context, candidate) > _sp2_completion_score(context, current) + 1e-9:
            current = candidate
            improved = True
        candidate = _sp2_drop_incomplete_if_better(context, current, method)
        if _sp2_completion_score(context, candidate) > _sp2_completion_score(context, current) + 1e-9:
            current = candidate
            improved = True
        if not improved:
            break
    return Assignment(labels=np.asarray(current.labels, dtype=int).copy(), method=method)


def _sp2_best_completion_repair(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int)
    best = Assignment(labels=labels.copy(), method=method)
    best_score = _sp2_completion_score(context, best)
    distances = distance_matrix(context)
    load_count = len(context.world.loads)
    for load_idx in range(load_count):
        if _sp2_load_complete(context, best.labels, load_idx):
            continue
        current_members = set(int(idx) for idx in np.flatnonzero(best.labels == load_idx + 1))
        candidate_pool = []
        for robot_idx in range(len(context.world.robots)):
            label = int(best.labels[robot_idx])
            if robot_idx in current_members or label == 0:
                candidate_pool.append(int(robot_idx))
            elif 1 <= label <= load_count and not _sp2_load_complete(context, best.labels, label - 1):
                candidate_pool.append(int(robot_idx))
        candidate_pool = sorted(set(candidate_pool), key=lambda idx: float(distances[idx, load_idx]))[: min(10, len(candidate_pool))]
        for size in range(1, min(6, len(candidate_pool)) + 1):
            for group in combinations(candidate_pool, size):
                next_labels = best.labels.copy()
                for robot_idx in group:
                    next_labels[int(robot_idx)] = load_idx + 1
                if not _sp2_load_complete(context, next_labels, load_idx):
                    continue
                candidate = Assignment(labels=next_labels, method=method)
                score = _sp2_completion_score(context, candidate)
                if score > best_score + 1e-9:
                    best_score = score
                    best = candidate
    return best


def _sp2_best_single_move(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    labels = np.asarray(assignment.labels, dtype=int)
    best = Assignment(labels=labels.copy(), method=method)
    best_score = _sp2_completion_score(context, best)
    for robot_idx in range(len(context.world.robots)):
        original = int(labels[robot_idx])
        for label in range(len(context.world.loads) + 1):
            if label == original:
                continue
            next_labels = labels.copy()
            next_labels[robot_idx] = label
            candidate = Assignment(labels=next_labels, method=method)
            score = _sp2_completion_score(context, candidate)
            if score > best_score + 1e-9:
                best_score = score
                best = candidate
    return best


def _sp2_drop_incomplete_if_better(context: DecisionContext, assignment: Assignment, method: str) -> Assignment:
    current = Assignment(labels=np.asarray(assignment.labels, dtype=int).copy(), method=method)
    for load_idx in range(len(context.world.loads)):
        if _sp2_load_complete(context, current.labels, load_idx):
            continue
        if not np.any(current.labels == load_idx + 1):
            continue
        next_labels = np.asarray(current.labels, dtype=int).copy()
        next_labels[next_labels == load_idx + 1] = 0
        candidate = Assignment(labels=next_labels, method=method)
        if _sp2_completion_score(context, candidate) >= _sp2_completion_score(context, current) - 1e-9:
            current = candidate
    return current


def _sp2_completion_score(context: DecisionContext, assignment: Assignment) -> float:
    labels = np.asarray(assignment.labels, dtype=int)
    eff = effective_capacity_matrix(context)
    demands = load_capacity_demands(context)
    rewards = load_rewards(context)
    distances = distance_matrix(context)
    score = 0.0
    for load_idx, load in enumerate(context.world.loads):
        members = np.flatnonzero(labels == load_idx + 1)
        if members.size == 0:
            continue
        capacity = float(np.sum(eff[members, load_idx]))
        demand = max(float(demands[load_idx]), 1e-9)
        ratio = min(capacity / demand, 1.0)
        score += 4.0 * float(rewards[load_idx]) * ratio
        if capacity + 1e-9 >= demand and members.size >= int(load.min_coalition_size):
            score += 80.0 + 10.0 * float(rewards[load_idx])
        else:
            score -= 8.0 * (1.0 - ratio) + 0.25 * float(members.size) + 0.02 * min(capacity, demand)
        if capacity > demand:
            score -= 0.01 * (capacity - demand)
    for robot_idx, label in enumerate(labels):
        if int(label) <= 0:
            continue
        load_idx = int(label) - 1
        if 0 <= load_idx < len(context.world.loads):
            score -= 0.03 * float(distances[robot_idx, load_idx])
    return float(score)


def _sp2_load_complete(context: DecisionContext, labels: np.ndarray, load_idx: int) -> bool:
    members = np.flatnonzero(np.asarray(labels, dtype=int) == load_idx + 1)
    if members.size < int(context.world.loads[load_idx].min_coalition_size):
        return False
    eff = effective_capacity_matrix(context)
    demand = float(context.world.loads[load_idx].min_capacity_kg)
    return bool(float(np.sum(eff[members, load_idx])) + 1e-9 >= demand)


def distance_matrix(context: DecisionContext) -> np.ndarray:
    robots = context.world.robots
    loads = context.world.loads
    if not robots or not loads:
        return np.zeros((len(robots), len(loads)), dtype=float)
    robot_positions = np.vstack([robot.position for robot in robots])
    load_positions = np.vstack([load.pickup for load in loads])
    return np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)


def energy_matrix(context: DecisionContext) -> np.ndarray:
    distances = distance_matrix(context)
    energy = np.zeros_like(distances)
    for robot_idx, robot in enumerate(context.world.robots):
        energy[robot_idx] = distances[robot_idx] * robot.spec.battery.discharge_per_meter * robot.spec.battery.capacity_wh
    return energy


def physical_effective_capacity_matrix(context: DecisionContext) -> np.ndarray:
    distances = distance_matrix(context)
    decay = float(context.metadata.get("distance_decay_m", 22.0))
    eff = np.zeros_like(distances)
    for robot_idx, robot in enumerate(context.world.robots):
        payload = float(robot.spec.capacity.payload_kg)
        battery = float(robot.battery_fraction)
        battery_factor = float(np.clip((battery - robot.spec.battery.reserve_fraction) / max(1.0 - robot.spec.battery.reserve_fraction, 1e-9), 0.0, 1.0))
        distance_factor = np.exp(-distances[robot_idx] / max(decay, 1e-9))
        eff[robot_idx] = payload * battery_factor * distance_factor
    return eff


def communication_visibility_matrix(context: DecisionContext) -> np.ndarray:
    distances = distance_matrix(context)
    radius = float(context.metadata.get("communication_radius", np.inf))
    if not np.isfinite(radius):
        return np.ones_like(distances)
    return (distances <= radius).astype(float)


def effective_capacity_matrix(context: DecisionContext) -> np.ndarray:
    """Physical effective capacity; communication is tracked separately as observability."""

    return physical_effective_capacity_matrix(context)


def load_capacity_demands(context: DecisionContext) -> np.ndarray:
    return np.asarray([float(load.min_capacity_kg) for load in context.world.loads], dtype=float)


def load_rewards(context: DecisionContext) -> np.ndarray:
    return np.asarray([float(load.reward) for load in context.world.loads], dtype=float)


def feature_tensor(context: DecisionContext) -> np.ndarray:
    distances = distance_matrix(context)
    eff = effective_capacity_matrix(context)
    demands = load_capacity_demands(context)
    rewards = load_rewards(context)
    max_distance = max(float(context.world.map.size_m), 1.0)
    max_mass = max(float(np.max(demands)) if demands.size else 1.0, 1.0)
    radius = float(context.metadata.get("communication_radius", np.inf))
    visibility_matrix = communication_visibility_matrix(context)
    robot_count, load_count = distances.shape
    features = np.zeros((robot_count, load_count, len(FEATURE_NAMES)), dtype=float)
    for robot_idx, robot in enumerate(context.world.robots):
        for load_idx in range(load_count):
            features[robot_idx, load_idx] = np.asarray(
                [
                    1.0,
                    rewards[load_idx],
                    1.0,
                    eff[robot_idx, load_idx] / max(demands[load_idx], 1e-9),
                    distances[robot_idx, load_idx] / max_distance,
                    float(robot.battery_fraction),
                    visibility_matrix[robot_idx, load_idx] if np.isfinite(radius) else 1.0,
                    demands[load_idx] / max_mass,
                ],
                dtype=float,
            )
    return features


def _score_decode(context: DecisionContext, method: str, scorer: Any) -> Assignment:
    distances = distance_matrix(context)
    eff = effective_capacity_matrix(context)
    robot_count, load_count = distances.shape
    labels = np.zeros(robot_count, dtype=int)
    scores = np.zeros((robot_count, load_count), dtype=float)
    if robot_count == 0 or load_count == 0:
        return Assignment(labels=labels, method=method)
    demands = load_capacity_demands(context)
    deficits = demands.copy()
    base_features = feature_tensor(context)
    for robot_idx in np.argsort(np.min(distances, axis=1)):
        if np.all(deficits <= 1e-9):
            break
        features = base_features[int(robot_idx)].copy()
        features[:, 2] = deficits / np.maximum(demands, 1.0)
        utility = np.asarray(scorer(features), dtype=float)
        utility = np.where(deficits > 1e-9, utility, -np.inf)
        scores[int(robot_idx)] = utility
        if not np.isfinite(np.max(utility)):
            continue
        load_idx = int(np.argmax(utility))
        labels[int(robot_idx)] = load_idx + 1
        deficits[load_idx] = max(0.0, deficits[load_idx] - eff[int(robot_idx), load_idx])
    return Assignment(labels=labels, scores=scores, method=method)


def _fallback_capacity_oracle(context: DecisionContext, method: str) -> Assignment:
    allocator = PrimalDualCapacityAllocator(name=method, distance_weight=0.04, deficit_weight=1.8, capacity_weight=1.6, reward_weight=1.3)
    return allocator.allocate(context)


def _x_index(robot_idx: int, load_idx: int, load_count: int) -> int:
    return robot_idx * load_count + load_idx


def _y_index(robot_count: int, load_count: int, load_idx: int) -> int:
    return robot_count * load_count + load_idx


def _s_index(robot_count: int, load_count: int, load_idx: int) -> int:
    return robot_count * load_count + load_count + load_idx


def _load_linear_model(path: Path | None) -> dict[str, Any]:
    if path is not None and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "model_version": "sp2-imitation-capacity-default",
        "feature_names": FEATURE_NAMES,
        "weights": [0.05, 0.55, 1.45, 1.35, -1.8, 0.35, 0.65, 0.12],
    }


def _load_neural_model(path: Path | None) -> dict[str, Any]:
    if path is not None and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "model_version": "sp2-neural-capacity-default",
        "feature_names": FEATURE_NAMES,
        "w1": [
            [0.2, -0.1, 0.3, 0.2, -0.4, 0.1, 0.2, 0.1],
            [0.5, 0.4, -0.2, 0.3, 0.2, 0.1, 0.1, -0.1],
            [0.7, 0.9, 0.8, -0.3, 0.4, 0.2, 0.4, 0.0],
            [0.8, 0.7, 0.9, 0.1, 0.2, 0.3, 0.5, 0.1],
            [-1.3, -1.0, -0.9, -1.1, -0.8, -0.7, -0.9, -0.6],
            [0.3, 0.1, 0.5, 0.4, 0.8, 0.6, 0.4, 0.2],
            [0.5, 0.4, 0.6, 0.5, 0.2, 0.5, 0.8, 0.2],
            [0.2, 0.3, 0.1, 0.2, 0.0, 0.1, 0.1, 0.3],
        ],
        "b1": [0.0, 0.05, 0.1, -0.05, 0.0, 0.02, 0.04, 0.01],
        "w2": [0.25, 0.35, 0.85, 0.95, -0.75, 0.25, 0.3, 0.15],
        "b2": 0.0,
    }
