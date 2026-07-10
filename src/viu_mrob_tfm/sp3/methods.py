"""SP3 role/slot wrench-aware allocation methods."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment, lsq_linear

from viu_mrob_tfm.sp3.scenario import SP3Problem


SP3_METHOD_LABELS = {
    "wrench_oracle": "Wrench oracle",
    "hungarian_slots": "Hungarian slots",
    "capacity_greedy_slots": "Capacity greedy slots",
    "cbba_slots": "CBBA slots",
    "replicator_wrench_deficit": "Replicator wrench deficit",
    "bnn_wrench_deficit": "BNN wrench deficit",
    "smith_wrench_deficit": "Smith-QR wrench deficit",
    "smith_wrench_marginal": "Smith-QR wrench marginal",
    "smith_wrench_marginal_guarded": "Smith-QR wrench marginal guarded",
    "support_dual_wrench_market": "Residual-support wrench market",
    "support_dual_wrench_market_guarded": "Residual-support wrench market guarded",
    "smith_wrench_pairs_guarded": "Smith-QR pair repair guarded",
    "oracle_wrench_assignment": "Oracle wrench assignment",
    "oracle_scalar_assignment": "Oracle scalar assignment",
    "greedy_cardinality": "Greedy cardinality",
    "greedy_capacity": "Greedy capacity",
    "wrench_greedy": "Wrench greedy",
    "cbba_wrench_score": "CBBA wrench score",
    "smith_qr_capacity": "Smith-QR capacity",
    "smith_qr_wrench": "Smith-QR wrench",
    "wrench_oracle_reference": "Wrench oracle reference",
}

SP3_METHOD_METADATA = {
    "wrench_oracle": ("model_based_oracle", "centralized", "reference", "exact_role_slot_wrench", "centralized_wrench_oracle_reference"),
    "oracle_wrench_assignment": ("model_based_oracle", "centralized", "reference", "exact_role_slot_wrench", "centralized_wrench_oracle_reference"),
    "wrench_oracle_reference": ("model_based_oracle", "centralized", "reference", "exact_role_slot_wrench_replay", "centralized_wrench_oracle_reference"),
    "oracle_scalar_assignment": ("model_based_oracle", "centralized", "reference", "exact_scalar_capacity_reference", "centralized_scalar_reference"),
    "hungarian_slots": ("classic", "centralized", "baseline", "hungarian_robot_slot_cost", "classic_centralized_baseline"),
    "capacity_greedy_slots": ("classic", "decentralized", "baseline", "capacity_greedy_slots", "classic_decentralized_baseline"),
    "greedy_cardinality": ("classic", "decentralized", "baseline", "nearest_cardinality_slots", "classic_decentralized_baseline"),
    "greedy_capacity": ("classic", "decentralized", "baseline", "nearest_capacity_slots", "classic_decentralized_baseline"),
    "wrench_greedy": ("model_based", "decentralized", "baseline", "marginal_residual_wrench", "model_based_wrench_baseline"),
    "cbba_slots": ("sota", "decentralized", "baseline", "cbba_slot_wrench_proxy", "sota_decentralized_baseline"),
    "cbba_wrench_score": ("sota", "decentralized", "baseline", "cbba_residual_wrench_score", "sota_decentralized_baseline"),
    "replicator_wrench_deficit": ("model_based", "decentralized", "baseline", "replicator_wrench_deficit", "wrench_dynamics_baseline"),
    "bnn_wrench_deficit": ("model_based", "decentralized", "baseline", "bnn_wrench_deficit", "wrench_dynamics_baseline"),
    "smith_wrench_deficit": ("model_based", "decentralized", "proposed", "smith_qr_wrench_deficit", "proposed_wrench_deficit"),
    "smith_wrench_marginal": ("model_based", "decentralized", "proposed", "smith_qr_delta_rho_wrench_marginal", "proposed_wrench_ablation"),
    "smith_wrench_marginal_guarded": ("model_based", "decentralized", "proposed", "smith_qr_delta_rho_guarded_local_repair", "proposed_wrench_guarded_repair"),
    "support_dual_wrench_market": ("model_based", "decentralized", "proposed", "residual_support_wrench_market", "proposed_wrench_market"),
    "support_dual_wrench_market_guarded": ("model_based", "decentralized", "proposed", "residual_support_guarded_local_repair", "proposed_wrench_guarded_repair"),
    "smith_wrench_pairs_guarded": ("model_based", "decentralized", "proposed", "pair_aware_wrench_guarded_repair", "proposed_wrench_guarded_repair"),
    "smith_qr_capacity": ("model_based", "decentralized", "proposed", "smith_qr_scalar_capacity", "proposed_scalar_variation"),
    "smith_qr_wrench": ("model_based", "decentralized", "proposed", "smith_qr_role_slot_wrench", "proposed_wrench_variation"),
}

SP3_METHOD_RESOURCE_METADATA = {
    "wrench_oracle": ("none", "centralized_exact_role_slot_search", "centralized_all_robot_slot_pairs", 0, 3, False, False),
    "oracle_wrench_assignment": ("none", "centralized_exact_role_slot_search", "centralized_all_robot_slot_pairs", 0, 3, False, False),
    "wrench_oracle_reference": ("none", "centralized_exact_reference_replay", "centralized_all_robot_slot_pairs", 0, 3, False, False),
    "oracle_scalar_assignment": ("none", "centralized_exact_scalar_search", "centralized_all_robot_slot_pairs", 0, 2, False, False),
    "hungarian_slots": ("none", "centralized_robot_slot_hungarian", "centralized_robot_slot_cost_matrix", 0, 0, False, False),
    "capacity_greedy_slots": ("none", "distributed_capacity_slot_rule", "local_robot_load_slots", 0, 0, False, False),
    "greedy_cardinality": ("none", "distributed_cardinality_slot_rule", "local_robot_load_slots", 0, 0, False, False),
    "greedy_capacity": ("none", "distributed_capacity_slot_rule", "local_robot_load_slots", 0, 0, False, False),
    "wrench_greedy": ("none", "distributed_marginal_wrench_rule", "local_robot_slot_residuals", 0, 2, False, False),
    "cbba_slots": ("none", "distributed_slot_bundle_auction_proxy", "auction_robot_slot_bids", 0, 3, False, False),
    "cbba_wrench_score": ("none", "distributed_wrench_auction_proxy", "auction_robot_slot_bids", 0, 3, False, False),
    "replicator_wrench_deficit": ("none", "distributed_replicator_wrench_deficit_rule", "local_wrench_deficit_scores", 0, 4, False, False),
    "bnn_wrench_deficit": ("none", "distributed_bnn_wrench_deficit_rule", "positive_excess_wrench_scores", 0, 4, False, False),
    "smith_wrench_deficit": ("model_based_tuning_optional", "distributed_smith_qr_wrench_deficit_rule", "local_wrench_deficit_scores", 0, 5, False, False),
    "smith_wrench_marginal": ("model_based_tuning_optional", "distributed_smith_qr_delta_rho_rule", "local_marginal_wrench_scores", 0, 5, False, False),
    "smith_wrench_marginal_guarded": ("model_based_tuning_optional", "distributed_smith_qr_delta_rho_with_certified_guard", "local_marginal_wrench_scores_plus_local_repair", 0, 7, False, False),
    "support_dual_wrench_market": ("model_based_tuning_optional", "distributed_residual_support_wrench_market", "current_residual_wrench_direction", 0, 5, False, False),
    "support_dual_wrench_market_guarded": ("model_based_tuning_optional", "distributed_residual_support_market_with_certified_guard", "current_residual_direction_plus_local_repair", 0, 7, False, False),
    "smith_wrench_pairs_guarded": ("model_based_tuning_optional", "distributed_pair_aware_smith_guarded_repair", "local_pair_complementarity_plus_wrench_guard", 0, 8, False, False),
    "smith_qr_capacity": ("model_based_tuning_optional", "distributed_smith_qr_capacity_slot_rule", "local_capacity_deficit_scores", 0, 4, False, False),
    "smith_qr_wrench": ("model_based_tuning_optional", "distributed_smith_qr_wrench_slot_rule", "local_wrench_deficit_scores", 0, 5, False, False),
}

SP3_METHOD_DESIGN = {
    "wrench_oracle": ("oracle", "strict_wrench_feasible_score", "reference", "A"),
    "oracle_wrench_assignment": ("oracle", "strict_wrench_feasible_score", "reference_legacy", "A"),
    "wrench_oracle_reference": ("oracle", "strict_wrench_feasible_score_replay", "reference", "A"),
    "oracle_scalar_assignment": ("oracle", "scalar_capacity_only", "reference_scalar_false_positive", "A"),
    "hungarian_slots": ("hungarian", "robot_slot_cost_only", "classic_baseline", "A"),
    "capacity_greedy_slots": ("greedy", "scalar_capacity_only", "classic_baseline", "A"),
    "greedy_cardinality": ("greedy", "cardinality_only", "legacy_baseline", "A"),
    "greedy_capacity": ("greedy", "scalar_capacity_only", "legacy_baseline", "A"),
    "wrench_greedy": ("greedy", "marginal_residual_wrench", "geometric_baseline", "A"),
    "cbba_slots": ("cbba", "marginal_wrench_bid", "sota_proxy", "A"),
    "cbba_wrench_score": ("cbba", "marginal_wrench_bid", "sota_proxy_legacy", "A"),
    "replicator_wrench_deficit": ("replicator", "wrench_deficit_minus_rho", "engine_ablation", "B"),
    "bnn_wrench_deficit": ("bnn", "positive_excess_wrench_deficit", "engine_ablation", "B"),
    "smith_wrench_deficit": ("smith", "wrench_deficit_minus_rho", "main_proposal", "A"),
    "smith_wrench_marginal": ("smith", "delta_rho_marginal", "proposal_ablation", "A"),
    "smith_wrench_marginal_guarded": ("smith", "delta_rho_marginal_plus_wrench_abstention_guard", "guarded_local_repair_proposal", "A"),
    "support_dual_wrench_market": ("residual_support_market", "current_residual_wrench_direction", "main_proposal", "A"),
    "support_dual_wrench_market_guarded": ("residual_support_market", "current_residual_wrench_direction_plus_abstention_guard", "guarded_local_repair_proposal", "A"),
    "smith_wrench_pairs_guarded": ("smith_pair_repair", "pairwise_delta_rho_plus_wrench_abstention_guard", "pair_complementarity_repair_proposal", "A"),
    "smith_qr_capacity": ("smith", "scalar_capacity_only", "legacy_scalar_proposal", "A"),
    "smith_qr_wrench": ("smith", "pair_lookahead_wrench_score", "legacy_pair_aware_proposal", "B"),
}


@dataclass(frozen=True, slots=True)
class SP3Assignment:
    """SP3 local assignment with robot-to-load labels and robot-to-slot labels."""

    labels: np.ndarray
    slot_labels: np.ndarray
    method: str = "unknown"
    scores: np.ndarray | None = None

    def __post_init__(self) -> None:
        labels = np.asarray(self.labels, dtype=int)
        slot_labels = np.asarray(self.slot_labels, dtype=int)
        if labels.ndim != 1 or slot_labels.ndim != 1:
            raise ValueError("SP3Assignment labels and slot_labels must be 1D arrays.")
        if labels.shape != slot_labels.shape:
            raise ValueError("SP3Assignment labels and slot_labels must have the same shape.")
        object.__setattr__(self, "labels", labels)
        object.__setattr__(self, "slot_labels", slot_labels)

    def members_for_load(self, load_index: int) -> np.ndarray:
        return np.flatnonzero(self.labels == load_index + 1)


@dataclass(frozen=True, slots=True)
class WrenchFit:
    """Bounded least-squares fit for one load wrench."""

    residual_norm: float
    force_error_n: float
    torque_error_nm: float
    achieved_wrench: np.ndarray
    demanded_wrench: np.ndarray
    lambdas: np.ndarray
    matrix: np.ndarray


class BaseSP3Allocator:
    """SP3 allocator protocol."""

    name: str = "base_sp3"

    def allocate(self, problem: SP3Problem) -> SP3Assignment:  # pragma: no cover - abstract protocol
        raise NotImplementedError


@dataclass(slots=True)
class OracleWrenchAssignmentAllocator(BaseSP3Allocator):
    """Exact bounded search over load-slot plans using strict wrench feasibility."""

    name: str = "oracle_wrench_assignment"

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _exact_search(problem, self.name, objective="wrench")


@dataclass(slots=True)
class OracleScalarAssignmentAllocator(BaseSP3Allocator):
    """Exact scalar-capacity reference that intentionally ignores wrench residuals."""

    name: str = "oracle_scalar_assignment"

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _exact_search(problem, self.name, objective="scalar")


@dataclass(slots=True)
class GreedyCardinalityAllocator(BaseSP3Allocator):
    """Classic nearest-cardinality allocator with naive slot filling."""

    name: str = "greedy_cardinality"

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        labels, slots = _empty_arrays(problem)
        available = np.ones(len(problem.world.robots), dtype=bool)
        distances = distance_matrix(problem)
        for load_idx in _load_order(problem):
            used_slots: set[int] = set()
            needed = min(problem.world.loads[load_idx].min_coalition_size, len(problem.load_slots[load_idx]))
            robot_order = np.argsort(distances[:, load_idx])
            for robot_idx in robot_order:
                if not available[int(robot_idx)]:
                    continue
                slot_idx = _nearest_free_slot(problem, int(robot_idx), load_idx, used_slots)
                if slot_idx is None:
                    break
                _assign(labels, slots, int(robot_idx), load_idx, slot_idx)
                available[int(robot_idx)] = False
                used_slots.add(slot_idx)
                if len(used_slots) >= needed:
                    break
        return SP3Assignment(labels=labels, slot_labels=slots, method=self.name)


@dataclass(slots=True)
class GreedyCapacityAllocator(BaseSP3Allocator):
    """Classic scalar-capacity allocator that ignores wrench geometry."""

    name: str = "greedy_capacity"
    distance_weight: float = 0.08

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        labels, slots = _empty_arrays(problem)
        available = np.ones(len(problem.world.robots), dtype=bool)
        distances = distance_matrix(problem)
        payloads = payload_vector(problem)
        for load_idx in _load_order(problem):
            used_slots: set[int] = set()
            assigned_payload = 0.0
            demand = float(problem.world.loads[load_idx].min_capacity_kg)
            while assigned_payload + 1e-9 < demand and np.any(available):
                best: tuple[float, int, int] | None = None
                for robot_idx in np.flatnonzero(available):
                    slot_idx = _nearest_free_slot(problem, int(robot_idx), load_idx, used_slots)
                    if slot_idx is None:
                        continue
                    utility = payloads[int(robot_idx)] - self.distance_weight * _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    if best is None or utility > best[0]:
                        best = (float(utility), int(robot_idx), slot_idx)
                if best is None:
                    break
                _utility, robot_idx, slot_idx = best
                _assign(labels, slots, robot_idx, load_idx, slot_idx)
                available[robot_idx] = False
                used_slots.add(slot_idx)
                assigned_payload += float(payloads[robot_idx])
        return SP3Assignment(labels=labels, slot_labels=slots, method=self.name)


@dataclass(slots=True)
class HungarianSlotsAllocator(BaseSP3Allocator):
    """Classic centralized robot-slot assignment using cost only, not wrench feasibility."""

    name: str = "hungarian_slots"
    distance_weight: float = 1.0
    reward_weight: float = 0.25
    force_weight: float = 0.012

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        labels, slots = _empty_arrays(problem)
        robot_count = len(problem.world.robots)
        slot_options = [(load_idx, slot_idx) for load_idx, load_slots in enumerate(problem.load_slots) for slot_idx in range(len(load_slots))]
        if robot_count == 0 or not slot_options:
            return SP3Assignment(labels=labels, slot_labels=slots, method=self.name)
        costs = np.zeros((robot_count, len(slot_options)), dtype=float)
        forces = np.asarray([robot.spec.capacity.force_limit_n for robot in problem.world.robots], dtype=float)
        for robot_idx in range(robot_count):
            for col, (load_idx, slot_idx) in enumerate(slot_options):
                costs[robot_idx, col] = (
                    self.distance_weight * _robot_slot_distance(problem, robot_idx, load_idx, slot_idx)
                    - self.reward_weight * float(problem.world.loads[load_idx].reward)
                    - self.force_weight * forces[robot_idx]
                )
        rows, cols = linear_sum_assignment(costs)
        for robot_idx, col in zip(rows, cols):
            load_idx, slot_idx = slot_options[int(col)]
            _assign(labels, slots, int(robot_idx), int(load_idx), int(slot_idx))
        return SP3Assignment(labels=labels, slot_labels=slots, method=self.name)


@dataclass(slots=True)
class WrenchGreedyAllocator(BaseSP3Allocator):
    """Greedy allocator by marginal improvement in the global wrench score."""

    name: str = "wrench_greedy"
    minimum_gain: float = 1e-6

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _marginal_wrench_allocate(problem, self.name, distance_bias=0.0, minimum_gain=self.minimum_gain)


@dataclass(slots=True)
class CbbaWrenchScoreAllocator(BaseSP3Allocator):
    """CBBA-like one-shot auction using wrench residual bids."""

    name: str = "cbba_wrench_score"
    distance_bias: float = 0.012
    minimum_gain: float = -0.02

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _marginal_wrench_allocate(problem, self.name, distance_bias=self.distance_bias, minimum_gain=self.minimum_gain)


@dataclass(slots=True)
class WrenchDeficitDynamicsAllocator(BaseSP3Allocator):
    """Population-dynamics-style allocator over the same wrench-deficit signal."""

    name: str
    engine: str = "smith"
    distance_bias: float = 0.006
    pressure_weight: float = 1.0
    improvement_weight: float = 1.0
    minimum_gain: float = -0.015

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _wrench_deficit_allocate(
            problem,
            self.name,
            engine=self.engine,
            distance_bias=self.distance_bias,
            pressure_weight=self.pressure_weight,
            improvement_weight=self.improvement_weight,
            minimum_gain=self.minimum_gain,
        )


@dataclass(slots=True)
class SmithQRCapacityAllocator(BaseSP3Allocator):
    """Smith-QR scalar carry-over: deficit/capacity pressure without wrench geometry."""

    name: str = "smith_qr_capacity"
    distance_weight: float = 0.06
    deficit_weight: float = 1.2
    reward_weight: float = 0.8

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        labels, slots = _empty_arrays(problem)
        available = np.ones(len(problem.world.robots), dtype=bool)
        payloads = payload_vector(problem)
        for _ in range(len(problem.world.robots)):
            best: tuple[float, int, int, int] | None = None
            for robot_idx in np.flatnonzero(available):
                for load_idx in range(len(problem.world.loads)):
                    used_slots = set(int(value) - 1 for value in slots[labels == load_idx + 1] if int(value) > 0)
                    slot_idx = _nearest_free_slot(problem, int(robot_idx), load_idx, used_slots)
                    if slot_idx is None:
                        continue
                    current_payload = float(np.sum(payloads[labels == load_idx + 1]))
                    demand = float(problem.world.loads[load_idx].min_capacity_kg)
                    deficit = max(demand - current_payload, 0.0) / max(demand, 1e-9)
                    if deficit <= 1e-9:
                        continue
                    utility = (
                        self.deficit_weight * deficit
                        + self.reward_weight * float(problem.world.loads[load_idx].reward)
                        + min(payloads[int(robot_idx)], max(demand - current_payload, 0.0)) / max(demand, 1e-9)
                        - self.distance_weight * _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    )
                    if best is None or utility > best[0]:
                        best = (float(utility), int(robot_idx), load_idx, slot_idx)
            if best is None:
                break
            _utility, robot_idx, load_idx, slot_idx = best
            _assign(labels, slots, robot_idx, load_idx, slot_idx)
            available[robot_idx] = False
        return SP3Assignment(labels=labels, slot_labels=slots, method=self.name)


@dataclass(slots=True)
class SmithQRWrenchAllocator(BaseSP3Allocator):
    """Smith-QR role-slot variant driven by wrench residual pressure."""

    name: str = "smith_qr_wrench"
    distance_bias: float = 0.006
    minimum_gain: float = -0.01

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _lookahead_wrench_allocate(problem, self.name, distance_bias=self.distance_bias, minimum_gain=self.minimum_gain)


@dataclass(slots=True)
class SmithWrenchMarginalAllocator(BaseSP3Allocator):
    """Smith-QR ablation where each candidate is valued by marginal improvement in rho."""

    name: str = "smith_wrench_marginal"
    distance_bias: float = 0.005
    minimum_gain: float = -0.01

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _wrench_marginal_allocate(problem, self.name, distance_bias=self.distance_bias, minimum_gain=self.minimum_gain)


@dataclass(slots=True)
class SupportDualWrenchMarketAllocator(BaseSP3Allocator):
    """Market over the current normalized residual wrench direction."""

    name: str = "support_dual_wrench_market"
    distance_bias: float = 0.004
    minimum_bid: float = -0.015

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        return _support_dual_allocate(problem, self.name, distance_bias=self.distance_bias, minimum_bid=self.minimum_bid)


@dataclass(slots=True)
class GuardedWrenchRepairAllocator(BaseSP3Allocator):
    """Wrench-aware wrapper with local exact repair and abstention guard.

    The wrapped population/market allocator proposes a role-slot assignment.
    Local repair then explores one- and two-robot slot insertions for problematic
    loads. Finally, physically infeasible loads are removed if strict score
    improves. This gives a certified local improvement layer without claiming
    global distributed optimality.
    """

    name: str = "guarded_wrench_repair"
    base_method: str = "smith_wrench_marginal"
    pair_aware: bool = False
    max_passes: int = 3

    def allocate(self, problem: SP3Problem) -> SP3Assignment:
        base = make_sp3_allocator(self.base_method).allocate(problem)
        repaired = _guarded_wrench_local_repair(problem, base, method=self.name, pair_aware=self.pair_aware, max_passes=self.max_passes)
        return SP3Assignment(repaired.labels, repaired.slot_labels, method=self.name)


def sp3_method_metadata(method_id: str) -> dict[str, Any]:
    method = method_id.lower()
    family, scope, ownership, variant, comparison_group = SP3_METHOD_METADATA.get(
        method,
        ("unknown", "unknown", "unknown", method, "unknown"),
    )
    training_type, execution_model, communication_pattern, trainable_parameters, tuned_parameters, uses_neural, uses_decoder = (
        SP3_METHOD_RESOURCE_METADATA.get(method, ("unknown", "unknown", "unknown", 0, 0, False, False))
    )
    label = SP3_METHOD_LABELS.get(method, method.replace("_", " "))
    engine, payoff_signal, method_role, recommended_phase = SP3_METHOD_DESIGN.get(method, ("unknown", "unknown", "unknown", "unknown"))
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
        "engine": engine,
        "payoff_signal": payoff_signal,
        "method_role": method_role,
        "recommended_phase": recommended_phase,
        "label": label,
        "file_tag": f"{ownership}-{family}-{scope}-{variant}-{method}".replace("_", "-"),
        "title": f"{label} [{ownership} | {family} | {scope} | {variant}]",
    }


def sp3_method_design(method_id: str) -> dict[str, str]:
    method = method_id.lower()
    engine, payoff_signal, method_role, recommended_phase = SP3_METHOD_DESIGN.get(method, ("unknown", "unknown", "unknown", "unknown"))
    return {
        "engine": engine,
        "payoff_signal": payoff_signal,
        "method_role": method_role,
        "recommended_phase": recommended_phase,
    }


def make_sp3_allocator(method_id: str, params: dict[str, Any] | None = None) -> BaseSP3Allocator:
    params = dict(params or {})
    method = method_id.lower()
    if method in {"wrench_oracle", "oracle_wrench_assignment", "wrench_oracle_reference"}:
        return OracleWrenchAssignmentAllocator(name=method)
    if method == "oracle_scalar_assignment":
        return OracleScalarAssignmentAllocator(name=method)
    if method == "hungarian_slots":
        return HungarianSlotsAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 1.0)),
            reward_weight=float(params.get("reward_weight", 0.25)),
            force_weight=float(params.get("force_weight", 0.012)),
        )
    if method == "greedy_cardinality":
        return GreedyCardinalityAllocator(name=method)
    if method in {"greedy_capacity", "capacity_greedy_slots"}:
        return GreedyCapacityAllocator(name=method, distance_weight=float(params.get("distance_weight", 0.08)))
    if method == "wrench_greedy":
        return WrenchGreedyAllocator(name=method)
    if method in {"cbba_wrench_score", "cbba_slots"}:
        return CbbaWrenchScoreAllocator(name=method, distance_bias=float(params.get("distance_bias", 0.012)))
    if method == "replicator_wrench_deficit":
        return WrenchDeficitDynamicsAllocator(
            name=method,
            engine="replicator",
            distance_bias=float(params.get("distance_bias", 0.006)),
            pressure_weight=float(params.get("pressure_weight", 0.85)),
            improvement_weight=float(params.get("improvement_weight", 0.75)),
            minimum_gain=float(params.get("minimum_gain", -0.012)),
        )
    if method == "bnn_wrench_deficit":
        return WrenchDeficitDynamicsAllocator(
            name=method,
            engine="bnn",
            distance_bias=float(params.get("distance_bias", 0.006)),
            pressure_weight=float(params.get("pressure_weight", 1.0)),
            improvement_weight=float(params.get("improvement_weight", 0.85)),
            minimum_gain=float(params.get("minimum_gain", 1e-9)),
        )
    if method == "smith_wrench_deficit":
        return WrenchDeficitDynamicsAllocator(
            name=method,
            engine="smith",
            distance_bias=float(params.get("distance_bias", 0.0045)),
            pressure_weight=float(params.get("pressure_weight", 1.15)),
            improvement_weight=float(params.get("improvement_weight", 1.05)),
            minimum_gain=float(params.get("minimum_gain", -0.015)),
        )
    if method == "smith_wrench_marginal":
        return SmithWrenchMarginalAllocator(
            name=method,
            distance_bias=float(params.get("distance_bias", 0.005)),
            minimum_gain=float(params.get("minimum_gain", -0.01)),
        )
    if method == "smith_wrench_marginal_guarded":
        return GuardedWrenchRepairAllocator(
            name=method,
            base_method=str(params.get("base_method", "smith_wrench_marginal")),
            pair_aware=bool(params.get("pair_aware", False)),
            max_passes=int(params.get("max_passes", 3)),
        )
    if method == "support_dual_wrench_market":
        return SupportDualWrenchMarketAllocator(
            name=method,
            distance_bias=float(params.get("distance_bias", 0.004)),
            minimum_bid=float(params.get("minimum_bid", -0.015)),
        )
    if method == "support_dual_wrench_market_guarded":
        return GuardedWrenchRepairAllocator(
            name=method,
            base_method=str(params.get("base_method", "support_dual_wrench_market")),
            pair_aware=bool(params.get("pair_aware", False)),
            max_passes=int(params.get("max_passes", 3)),
        )
    if method == "smith_wrench_pairs_guarded":
        return GuardedWrenchRepairAllocator(
            name=method,
            base_method=str(params.get("base_method", "smith_qr_wrench")),
            pair_aware=bool(params.get("pair_aware", True)),
            max_passes=int(params.get("max_passes", 4)),
        )
    if method == "smith_qr_capacity":
        return SmithQRCapacityAllocator(
            name=method,
            distance_weight=float(params.get("distance_weight", 0.06)),
            deficit_weight=float(params.get("deficit_weight", 1.2)),
            reward_weight=float(params.get("reward_weight", 0.8)),
        )
    if method == "smith_qr_wrench":
        return SmithQRWrenchAllocator(name=method, distance_bias=float(params.get("distance_bias", 0.006)))
    raise ValueError(f"Unknown SP3 method id: {method_id}")


def wrench_matrix(problem: SP3Problem, load_idx: int, robot_indices: list[int], slot_indices: list[int]) -> np.ndarray:
    """Return planar wrench matrix columns [Fx, Fy, tau_z] for robot-slot pairs."""

    columns = []
    for slot_idx in slot_indices:
        slot = problem.load_slots[load_idx][slot_idx]
        direction = slot.direction_xy
        offset = slot.offset_xy
        torque = float(offset[0] * direction[1] - offset[1] * direction[0])
        columns.append(np.array([direction[0], direction[1], torque], dtype=float))
    if not columns:
        return np.zeros((3, 0), dtype=float)
    return np.column_stack(columns)


def wrench_fit(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> WrenchFit:
    robot_indices, slot_indices = _assigned_pairs(problem, assignment, load_idx)
    demanded = problem.world.loads[load_idx].wrench.as_vector()
    g_matrix = wrench_matrix(problem, load_idx, robot_indices, slot_indices)
    if not robot_indices:
        achieved = np.zeros(3, dtype=float)
        error = achieved - demanded
        residual = _normalized_norm(problem, error)
        return WrenchFit(residual, float(np.linalg.norm(error[:2])), abs(float(error[2])), achieved, demanded, np.zeros(0, dtype=float), g_matrix)
    bounds_upper = np.asarray([problem.world.robots[idx].spec.capacity.force_limit_n for idx in robot_indices], dtype=float)
    q = np.diag([1.0 / max(problem.force_ref_n, 1e-9), 1.0 / max(problem.force_ref_n, 1e-9), 1.0 / max(problem.torque_ref_nm, 1e-9)])
    result = lsq_linear(q @ g_matrix, q @ demanded, bounds=(np.zeros(len(robot_indices)), bounds_upper), lsmr_tol="auto", max_iter=100)
    lambdas = np.asarray(result.x if result.success else np.zeros(len(robot_indices)), dtype=float)
    achieved = g_matrix @ lambdas
    error = achieved - demanded
    residual = _normalized_norm(problem, error)
    return WrenchFit(
        residual_norm=float(residual),
        force_error_n=float(np.linalg.norm(error[:2])),
        torque_error_nm=abs(float(error[2])),
        achieved_wrench=achieved,
        demanded_wrench=demanded,
        lambdas=lambdas,
        matrix=g_matrix,
    )


def score_assignment(problem: SP3Problem, assignment: SP3Assignment) -> float:
    """Strict SP3 physical score used by oracle, ranking gaps, and diagnostics."""

    score = sum(_load_strict_wrench_score(problem, assignment, load_idx) for load_idx in range(len(problem.world.loads)))
    score -= 0.012 * travel_distance_m(problem, assignment)
    score -= 0.0005 * energy_proxy_wh(problem, assignment)
    score -= 25.0 * len(slot_conflicts(problem, assignment))
    return float(score)


def soft_score_assignment(problem: SP3Problem, assignment: SP3Assignment) -> float:
    """Soft residual score used only by constructive heuristics before feasibility closes."""

    score = sum(_load_soft_wrench_score(problem, assignment, load_idx) for load_idx in range(len(problem.world.loads)))
    score -= 0.012 * travel_distance_m(problem, assignment)
    score -= 0.0005 * energy_proxy_wh(problem, assignment)
    score -= 25.0 * len(slot_conflicts(problem, assignment))
    return float(score)


def scalar_score_assignment(problem: SP3Problem, assignment: SP3Assignment) -> float:
    score = sum(_load_scalar_score(problem, assignment, load_idx) for load_idx in range(len(problem.world.loads)))
    score -= 0.014 * travel_distance_m(problem, assignment)
    score -= 20.0 * len(slot_conflicts(problem, assignment))
    return float(score)


def scalar_feasible(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> bool:
    load = problem.world.loads[load_idx]
    assigned_payload = _assigned_payload(problem, assignment, load_idx)
    assigned_count = int(np.sum(assignment.labels == load_idx + 1))
    return bool(assigned_count >= int(load.min_coalition_size) and assigned_payload + 1e-9 >= float(load.min_capacity_kg))


def slot_coverage_ratio(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    slot_count = len(problem.load_slots[load_idx])
    if slot_count == 0:
        return 1.0
    used = {int(value) - 1 for value in assignment.slot_labels[assignment.labels == load_idx + 1] if int(value) > 0}
    valid = {slot_idx for slot_idx in used if 0 <= slot_idx < slot_count}
    return float(len(valid) / slot_count)


def complementarity_gain(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    robot_indices, slot_indices = _assigned_pairs(problem, assignment, load_idx)
    if len(robot_indices) < 2:
        return 0.0
    demanded = problem.world.loads[load_idx].wrench.as_vector()
    best_single = math.inf
    for robot_idx, slot_idx in zip(robot_indices, slot_indices):
        partial = _assignment_for_pairs(problem, load_idx, [robot_idx], [slot_idx], method="single")
        best_single = min(best_single, wrench_fit(problem, partial, load_idx).residual_norm)
    best_pair = math.inf
    for pair in itertools.combinations(range(len(robot_indices)), 2):
        partial = _assignment_for_pairs(problem, load_idx, [robot_indices[pair[0]], robot_indices[pair[1]]], [slot_indices[pair[0]], slot_indices[pair[1]]], method="pair")
        best_pair = min(best_pair, wrench_fit(problem, partial, load_idx).residual_norm)
    full = wrench_fit(problem, assignment, load_idx).residual_norm
    reference = min(best_pair, full)
    if not np.isfinite(best_single):
        return 0.0
    # Also reward pure-torque complementarity where force cancellation matters.
    if np.linalg.norm(demanded[:2]) <= 1e-9 and abs(float(demanded[2])) > 1e-9:
        return float(max(0.0, best_single - reference))
    return float(max(0.0, best_single - reference))


def travel_distance_m(problem: SP3Problem, assignment: SP3Assignment) -> float:
    total = 0.0
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if label <= 0:
            continue
        load_idx = int(label) - 1
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if not (0 <= load_idx < len(problem.world.loads) and 0 <= slot_idx < len(problem.load_slots[load_idx])):
            continue
        total += _robot_slot_distance(problem, robot_idx, load_idx, slot_idx)
    return float(total)


def energy_proxy_wh(problem: SP3Problem, assignment: SP3Assignment) -> float:
    energy = 0.0
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if label <= 0:
            continue
        load_idx = int(label) - 1
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if not (0 <= load_idx < len(problem.world.loads) and 0 <= slot_idx < len(problem.load_slots[load_idx])):
            continue
        robot = problem.world.robots[robot_idx]
        energy += _robot_slot_distance(problem, robot_idx, load_idx, slot_idx) * float(robot.spec.battery.discharge_per_meter) * float(robot.spec.battery.capacity_wh)
    return float(energy)


def communication_messages(problem: SP3Problem, assignment: SP3Assignment, centralized: bool = False) -> int:
    if centralized or not np.isfinite(problem.communication_radius):
        return len(problem.world.robots) * sum(len(slots) for slots in problem.load_slots)
    count = 0
    for robot_idx in range(len(problem.world.robots)):
        for load_idx, slots in enumerate(problem.load_slots):
            for slot_idx in range(len(slots)):
                if _robot_slot_distance(problem, robot_idx, load_idx, slot_idx) <= problem.communication_radius:
                    count += 1
    return int(count)


def distance_matrix(problem: SP3Problem) -> np.ndarray:
    robots = problem.world.robots
    loads = problem.world.loads
    if not robots or not loads:
        return np.zeros((len(robots), len(loads)), dtype=float)
    robot_positions = np.vstack([robot.position for robot in robots])
    load_positions = np.vstack([load.pickup for load in loads])
    return np.linalg.norm(robot_positions[:, None, :] - load_positions[None, :, :], axis=2)


def payload_vector(problem: SP3Problem) -> np.ndarray:
    return np.asarray([robot.spec.capacity.payload_kg for robot in problem.world.robots], dtype=float)


def slot_conflicts(problem: SP3Problem, assignment: SP3Assignment) -> list[tuple[int, int]]:
    conflicts = []
    for load_idx, slots in enumerate(problem.load_slots):
        seen: set[int] = set()
        for value in assignment.slot_labels[assignment.labels == load_idx + 1]:
            slot_idx = int(value) - 1
            if not (0 <= slot_idx < len(slots)):
                conflicts.append((load_idx, slot_idx))
            elif slot_idx in seen:
                conflicts.append((load_idx, slot_idx))
            else:
                seen.add(slot_idx)
    return conflicts


def assignment_valid(problem: SP3Problem, assignment: SP3Assignment) -> bool:
    labels = np.asarray(assignment.labels, dtype=int)
    slots = np.asarray(assignment.slot_labels, dtype=int)
    if labels.shape != (len(problem.world.robots),) or slots.shape != labels.shape:
        return False
    if np.any(labels < 0) or np.any(labels > len(problem.world.loads)):
        return False
    for robot_idx, label in enumerate(labels):
        if label == 0 and slots[robot_idx] != 0:
            return False
        if label > 0:
            load_idx = int(label) - 1
            if slots[robot_idx] < 1 or slots[robot_idx] > len(problem.load_slots[load_idx]):
                return False
    return not slot_conflicts(problem, assignment)


def _exact_search(problem: SP3Problem, method: str, *, objective: str) -> SP3Assignment:
    load_candidates = [_plans_for_load(problem, load_idx, objective=objective) for load_idx in range(len(problem.world.loads))]
    best_score = -math.inf
    best_assignment = SP3Assignment(*_empty_arrays(problem), method=method)

    def visit(load_idx: int, labels: np.ndarray, slots: np.ndarray, used: set[int], accumulated_score: float) -> None:
        nonlocal best_score, best_assignment
        if load_idx >= len(load_candidates):
            assignment = SP3Assignment(labels=labels.copy(), slot_labels=slots.copy(), method=method)
            if accumulated_score > best_score:
                best_score = accumulated_score
                best_assignment = assignment
            return
        for plan in load_candidates[load_idx]:
            if any(robot_idx in used for robot_idx in plan["robots"]):
                continue
            next_labels = labels.copy()
            next_slots = slots.copy()
            for robot_idx, slot_idx in zip(plan["robots"], plan["slots"]):
                _assign(next_labels, next_slots, int(robot_idx), load_idx, int(slot_idx))
            visit(
                load_idx + 1,
                next_labels,
                next_slots,
                used | set(int(idx) for idx in plan["robots"]),
                accumulated_score + float(plan["score"]),
            )

    labels, slots = _empty_arrays(problem)
    visit(0, labels, slots, set(), 0.0)
    return SP3Assignment(labels=best_assignment.labels, slot_labels=best_assignment.slot_labels, method=method)


def _plans_for_load(problem: SP3Problem, load_idx: int, *, objective: str) -> list[dict[str, Any]]:
    robot_count = len(problem.world.robots)
    slot_count = len(problem.load_slots[load_idx])
    empty = SP3Assignment(*_empty_arrays(problem), method="empty")
    empty_score = _load_strict_wrench_score(problem, empty, load_idx) if objective == "wrench" else _load_scalar_score(problem, empty, load_idx)
    plans: list[dict[str, Any]] = [{"robots": (), "slots": (), "score": float(empty_score)}]
    for size in range(1, min(robot_count, slot_count) + 1):
        for robots in itertools.combinations(range(robot_count), size):
            for slot_perm in itertools.permutations(range(slot_count), size):
                partial = _assignment_for_pairs(problem, load_idx, list(robots), list(slot_perm), method="plan")
                if objective == "wrench":
                    score = _load_strict_wrench_score(problem, partial, load_idx) - 0.012 * travel_distance_m(problem, partial) - 0.0005 * energy_proxy_wh(problem, partial)
                else:
                    score = _load_scalar_score(problem, partial, load_idx) - 0.014 * travel_distance_m(problem, partial)
                plans.append({"robots": tuple(robots), "slots": tuple(slot_perm), "score": score})
    plans.sort(key=lambda row: float(row["score"]), reverse=True)
    return plans


def _load_strict_wrench_score(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    load = problem.world.loads[load_idx]
    fit = wrench_fit(problem, assignment, load_idx)
    robot_indices, _slot_indices = _assigned_pairs(problem, assignment, load_idx)
    if not robot_indices:
        return 0.0
    scalar = scalar_feasible(problem, assignment, load_idx)
    wrench_ok = fit.residual_norm <= problem.wrench_tolerance
    if not wrench_ok:
        return float(-2.0 - 10.0 * fit.residual_norm - 0.02 * fit.force_error_n - 0.01 * fit.torque_error_nm - 0.15 * len(robot_indices))
    slot_coverage = slot_coverage_ratio(problem, assignment, load_idx)
    score = 18.0 * float(load.reward)
    score += 2.5 * slot_coverage
    score += 1.25 if scalar else 0.0
    score -= 0.25 * fit.residual_norm
    score -= 0.002 * fit.force_error_n
    score -= 0.001 * fit.torque_error_nm
    return float(score)


def _load_soft_wrench_score(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    load = problem.world.loads[load_idx]
    fit = wrench_fit(problem, assignment, load_idx)
    scalar = scalar_feasible(problem, assignment, load_idx)
    wrench_ok = fit.residual_norm <= problem.wrench_tolerance
    slot_coverage = slot_coverage_ratio(problem, assignment, load_idx)
    reward = float(load.reward)
    score = 18.0 * reward if wrench_ok else 6.0 * reward * max(0.0, 1.0 - min(fit.residual_norm, 1.0))
    score += 2.5 * slot_coverage
    score += 1.25 if scalar else 0.0
    if scalar and not wrench_ok:
        score -= 4.0
    score -= 3.5 * fit.residual_norm
    score -= 0.02 * fit.force_error_n
    score -= 0.01 * fit.torque_error_nm
    return float(score)


def _load_scalar_score(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    load = problem.world.loads[load_idx]
    assigned_payload = _assigned_payload(problem, assignment, load_idx)
    assigned_count = int(np.sum(assignment.labels == load_idx + 1))
    demand = float(load.min_capacity_kg)
    coverage = min(assigned_payload, demand) / max(demand, 1e-9)
    complete = coverage >= 1.0 and assigned_count >= int(load.min_coalition_size)
    score = (10.0 if complete else 3.0) * float(load.reward) * coverage
    score += 0.4 * slot_coverage_ratio(problem, assignment, load_idx)
    return float(score)


def _marginal_wrench_allocate(problem: SP3Problem, method: str, *, distance_bias: float, minimum_gain: float) -> SP3Assignment:
    labels, slots = _empty_arrays(problem)
    available = np.ones(len(problem.world.robots), dtype=bool)
    current = SP3Assignment(labels=labels, slot_labels=slots, method=method)
    for _ in range(len(problem.world.robots)):
        base_score = soft_score_assignment(problem, current)
        best: tuple[float, int, int, int, SP3Assignment] | None = None
        for robot_idx in np.flatnonzero(available):
            for load_idx in range(len(problem.world.loads)):
                used_slots = set(int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0)
                for slot_idx in range(len(problem.load_slots[load_idx])):
                    if slot_idx in used_slots:
                        continue
                    cand_labels = current.labels.copy()
                    cand_slots = current.slot_labels.copy()
                    _assign(cand_labels, cand_slots, int(robot_idx), load_idx, slot_idx)
                    candidate = SP3Assignment(cand_labels, cand_slots, method=method)
                    gain = soft_score_assignment(problem, candidate) - base_score
                    gain -= distance_bias * _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    if best is None or gain > best[0]:
                        best = (float(gain), int(robot_idx), load_idx, slot_idx, candidate)
        if best is None or best[0] < minimum_gain:
            break
        _gain, robot_idx, _load_idx, _slot_idx, current = best
        available[robot_idx] = False
    return SP3Assignment(current.labels, current.slot_labels, method=method)


def _wrench_deficit_allocate(
    problem: SP3Problem,
    method: str,
    *,
    engine: str,
    distance_bias: float,
    pressure_weight: float,
    improvement_weight: float,
    minimum_gain: float,
) -> SP3Assignment:
    labels, slots = _empty_arrays(problem)
    current = SP3Assignment(labels=labels, slot_labels=slots, method=method)
    available = np.ones(len(problem.world.robots), dtype=bool)
    for _ in range(len(problem.world.robots)):
        candidates: list[tuple[float, int, int, int, SP3Assignment]] = []
        raw_utilities = []
        for robot_idx in np.flatnonzero(available):
            for load_idx in range(len(problem.world.loads)):
                current_fit = wrench_fit(problem, current, load_idx)
                if current_fit.residual_norm <= problem.wrench_tolerance and scalar_feasible(problem, current, load_idx):
                    continue
                used_slots = set(int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0)
                for slot_idx in range(len(problem.load_slots[load_idx])):
                    if slot_idx in used_slots:
                        continue
                    cand_labels = current.labels.copy()
                    cand_slots = current.slot_labels.copy()
                    _assign(cand_labels, cand_slots, int(robot_idx), load_idx, slot_idx)
                    candidate = SP3Assignment(cand_labels, cand_slots, method=method)
                    candidate_fit = wrench_fit(problem, candidate, load_idx)
                    rho = problem.wrench_tolerance - current_fit.residual_norm
                    pressure = math.log1p(max(0.0, -rho / max(problem.wrench_tolerance, 1e-9)))
                    improvement = max(0.0, current_fit.residual_norm - candidate_fit.residual_norm)
                    raw = float(problem.world.loads[load_idx].reward) * (pressure_weight * pressure + improvement_weight * improvement)
                    distance = _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    utility = raw - distance_bias * distance
                    raw_utilities.append(utility)
                    candidates.append((float(utility), int(robot_idx), load_idx, slot_idx, candidate))
        if not candidates:
            break
        if engine == "bnn":
            average = float(np.mean(raw_utilities)) if raw_utilities else 0.0
            candidates = [(max(0.0, utility - average), robot_idx, load_idx, slot_idx, candidate) for utility, robot_idx, load_idx, slot_idx, candidate in candidates]
        elif engine == "replicator":
            positive = [max(0.0, utility) for utility, *_rest in candidates]
            total = sum(positive)
            if total > 1e-12:
                candidates = [(max(0.0, utility) / total + 0.25 * utility, robot_idx, load_idx, slot_idx, candidate) for utility, robot_idx, load_idx, slot_idx, candidate in candidates]
        best = max(candidates, key=lambda row: row[0])
        if best[0] < minimum_gain:
            break
        _gain, robot_idx, _load_idx, _slot_idx, current = best
        available[robot_idx] = False
    return SP3Assignment(current.labels, current.slot_labels, method=method)


def _wrench_marginal_allocate(problem: SP3Problem, method: str, *, distance_bias: float, minimum_gain: float) -> SP3Assignment:
    labels, slots = _empty_arrays(problem)
    current = SP3Assignment(labels=labels, slot_labels=slots, method=method)
    available = np.ones(len(problem.world.robots), dtype=bool)
    for _ in range(len(problem.world.robots)):
        best: tuple[float, int, int, int, SP3Assignment] | None = None
        for robot_idx in np.flatnonzero(available):
            for load_idx in range(len(problem.world.loads)):
                base_fit = wrench_fit(problem, current, load_idx)
                used_slots = set(int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0)
                for slot_idx in range(len(problem.load_slots[load_idx])):
                    if slot_idx in used_slots:
                        continue
                    cand_labels = current.labels.copy()
                    cand_slots = current.slot_labels.copy()
                    _assign(cand_labels, cand_slots, int(robot_idx), load_idx, slot_idx)
                    candidate = SP3Assignment(cand_labels, cand_slots, method=method)
                    candidate_fit = wrench_fit(problem, candidate, load_idx)
                    delta_rho = base_fit.residual_norm - candidate_fit.residual_norm
                    utility = (
                        float(problem.world.loads[load_idx].reward) * delta_rho
                        - distance_bias * _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    )
                    if best is None or utility > best[0]:
                        best = (float(utility), int(robot_idx), load_idx, slot_idx, candidate)
        if best is None or best[0] < minimum_gain:
            break
        _gain, robot_idx, _load_idx, _slot_idx, current = best
        available[robot_idx] = False
    return SP3Assignment(current.labels, current.slot_labels, method=method)


def _support_dual_allocate(problem: SP3Problem, method: str, *, distance_bias: float, minimum_bid: float) -> SP3Assignment:
    labels, slots = _empty_arrays(problem)
    current = SP3Assignment(labels=labels, slot_labels=slots, method=method)
    available = np.ones(len(problem.world.robots), dtype=bool)
    for _ in range(len(problem.world.robots)):
        best: tuple[float, int, int, int, SP3Assignment] | None = None
        for robot_idx in np.flatnonzero(available):
            force_limit = float(problem.world.robots[int(robot_idx)].spec.capacity.force_limit_n)
            for load_idx in range(len(problem.world.loads)):
                fit = wrench_fit(problem, current, load_idx)
                if fit.residual_norm <= problem.wrench_tolerance and scalar_feasible(problem, current, load_idx):
                    continue
                eta = _normalized_wrench_error_direction(problem, fit.demanded_wrench - fit.achieved_wrench)
                if float(np.linalg.norm(eta)) <= 1e-12:
                    continue
                used_slots = set(int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0)
                pressure = max(fit.residual_norm, problem.wrench_tolerance)
                for slot_idx in range(len(problem.load_slots[load_idx])):
                    if slot_idx in used_slots:
                        continue
                    column = wrench_matrix(problem, load_idx, [int(robot_idx)], [slot_idx])[:, 0]
                    normalized_column = np.asarray(
                        [
                            column[0] / max(problem.force_ref_n, 1e-9),
                            column[1] / max(problem.force_ref_n, 1e-9),
                            column[2] / max(problem.torque_ref_nm, 1e-9),
                        ],
                        dtype=float,
                    )
                    support_gain = max(0.0, force_limit * float(eta @ normalized_column))
                    cand_labels = current.labels.copy()
                    cand_slots = current.slot_labels.copy()
                    _assign(cand_labels, cand_slots, int(robot_idx), load_idx, slot_idx)
                    candidate = SP3Assignment(cand_labels, cand_slots, method=method)
                    bid = (
                        float(problem.world.loads[load_idx].reward) * pressure * support_gain
                        - distance_bias * _robot_slot_distance(problem, int(robot_idx), load_idx, slot_idx)
                    )
                    if best is None or bid > best[0]:
                        best = (float(bid), int(robot_idx), load_idx, slot_idx, candidate)
        if best is None or best[0] < minimum_bid:
            break
        _bid, robot_idx, _load_idx, _slot_idx, current = best
        available[robot_idx] = False
    return SP3Assignment(current.labels, current.slot_labels, method=method)


def _lookahead_wrench_allocate(problem: SP3Problem, method: str, *, distance_bias: float, minimum_gain: float) -> SP3Assignment:
    """Pair-aware Smith-QR style heuristic for complementary wrench slots."""

    labels, slots = _empty_arrays(problem)
    current = SP3Assignment(labels=labels, slot_labels=slots, method=method)
    available: set[int] = set(range(len(problem.world.robots)))
    while available:
        base_score = soft_score_assignment(problem, current)
        best: tuple[float, tuple[int, ...], int, tuple[int, ...], SP3Assignment] | None = None
        for load_idx in range(len(problem.world.loads)):
            used_slots = set(int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0)
            free_slots = tuple(slot_idx for slot_idx in range(len(problem.load_slots[load_idx])) if slot_idx not in used_slots)
            if not free_slots:
                continue
            for add_size in (1, 2):
                if add_size > len(available) or add_size > len(free_slots):
                    continue
                for robot_group in itertools.combinations(sorted(available), add_size):
                    for slot_group in itertools.permutations(free_slots, add_size):
                        cand_labels = current.labels.copy()
                        cand_slots = current.slot_labels.copy()
                        distance = 0.0
                        for robot_idx, slot_idx in zip(robot_group, slot_group):
                            _assign(cand_labels, cand_slots, int(robot_idx), load_idx, int(slot_idx))
                            distance += _robot_slot_distance(problem, int(robot_idx), load_idx, int(slot_idx))
                        candidate = SP3Assignment(cand_labels, cand_slots, method=method)
                        gain = soft_score_assignment(problem, candidate) - base_score - distance_bias * distance
                        if best is None or gain > best[0]:
                            best = (float(gain), tuple(int(idx) for idx in robot_group), load_idx, tuple(int(idx) for idx in slot_group), candidate)
        if best is None or best[0] < minimum_gain:
            break
        _gain, robot_group, _load_idx, _slot_group, current = best
        for robot_idx in robot_group:
            available.discard(robot_idx)
    return SP3Assignment(current.labels, current.slot_labels, method=method)


def _guarded_wrench_local_repair(
    problem: SP3Problem,
    assignment: SP3Assignment,
    *,
    method: str,
    pair_aware: bool,
    max_passes: int,
) -> SP3Assignment:
    current = SP3Assignment(np.asarray(assignment.labels, dtype=int).copy(), np.asarray(assignment.slot_labels, dtype=int).copy(), method=method)
    current = _drop_infeasible_loads_if_better(problem, current, method)
    for _ in range(max(1, int(max_passes))):
        improved = False
        candidate = _best_wrench_insertion(problem, current, method=method, pair_aware=pair_aware)
        if score_assignment(problem, candidate) > score_assignment(problem, current) + 1e-9:
            current = candidate
            improved = True
        guarded = _drop_infeasible_loads_if_better(problem, current, method)
        if score_assignment(problem, guarded) > score_assignment(problem, current) + 1e-9:
            current = guarded
            improved = True
        if not improved:
            break
    return _drop_infeasible_loads_if_better(problem, current, method)


def _drop_infeasible_loads_if_better(problem: SP3Problem, assignment: SP3Assignment, method: str) -> SP3Assignment:
    current = SP3Assignment(assignment.labels.copy(), assignment.slot_labels.copy(), method=method)
    for load_idx in range(len(problem.world.loads)):
        if not np.any(current.labels == load_idx + 1):
            continue
        fit = wrench_fit(problem, current, load_idx)
        if fit.residual_norm <= problem.wrench_tolerance:
            continue
        labels = current.labels.copy()
        slots = current.slot_labels.copy()
        mask = labels == load_idx + 1
        labels[mask] = 0
        slots[mask] = 0
        candidate = SP3Assignment(labels, slots, method=method)
        if score_assignment(problem, candidate) >= score_assignment(problem, current) - 1e-9:
            current = candidate
    return current


def _best_wrench_insertion(problem: SP3Problem, assignment: SP3Assignment, *, method: str, pair_aware: bool) -> SP3Assignment:
    current = SP3Assignment(assignment.labels.copy(), assignment.slot_labels.copy(), method=method)
    best = current
    best_score = score_assignment(problem, current)
    idle = [int(idx) for idx, label in enumerate(current.labels) if int(label) == 0]
    if not idle:
        return current
    add_sizes = (1, 2) if pair_aware else (1,)
    for load_idx in range(len(problem.world.loads)):
        if _load_is_wrench_feasible(problem, current, load_idx):
            continue
        used_slots = {int(value) - 1 for value in current.slot_labels[current.labels == load_idx + 1] if int(value) > 0}
        free_slots = [slot_idx for slot_idx in range(len(problem.load_slots[load_idx])) if slot_idx not in used_slots]
        if not free_slots:
            continue
        for add_size in add_sizes:
            if add_size > len(idle) or add_size > len(free_slots):
                continue
            for robot_group in itertools.combinations(idle, add_size):
                for slot_group in itertools.permutations(free_slots, add_size):
                    labels = current.labels.copy()
                    slots = current.slot_labels.copy()
                    for robot_idx, slot_idx in zip(robot_group, slot_group):
                        _assign(labels, slots, int(robot_idx), load_idx, int(slot_idx))
                    candidate = SP3Assignment(labels, slots, method=method)
                    guarded = _drop_infeasible_loads_if_better(problem, candidate, method)
                    score = score_assignment(problem, guarded)
                    if score > best_score + 1e-9:
                        best_score = score
                        best = guarded
    return best


def _load_is_wrench_feasible(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> bool:
    return bool(np.any(assignment.labels == load_idx + 1) and wrench_fit(problem, assignment, load_idx).residual_norm <= problem.wrench_tolerance)


def _assignment_for_pairs(problem: SP3Problem, load_idx: int, robot_indices: list[int], slot_indices: list[int], *, method: str) -> SP3Assignment:
    labels, slots = _empty_arrays(problem)
    for robot_idx, slot_idx in zip(robot_indices, slot_indices):
        _assign(labels, slots, int(robot_idx), load_idx, int(slot_idx))
    return SP3Assignment(labels, slots, method=method)


def _assigned_pairs(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> tuple[list[int], list[int]]:
    robot_indices: list[int] = []
    slot_indices: list[int] = []
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if int(label) != load_idx + 1:
            continue
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if 0 <= slot_idx < len(problem.load_slots[load_idx]):
            robot_indices.append(int(robot_idx))
            slot_indices.append(slot_idx)
    return robot_indices, slot_indices


def _normalized_norm(problem: SP3Problem, error: np.ndarray) -> float:
    return float(
        np.linalg.norm(
            np.array(
                [
                    error[0] / max(problem.force_ref_n, 1e-9),
                    error[1] / max(problem.force_ref_n, 1e-9),
                    error[2] / max(problem.torque_ref_nm, 1e-9),
                ],
                dtype=float,
            )
        )
    )


def _normalized_wrench_error_direction(problem: SP3Problem, error: np.ndarray) -> np.ndarray:
    scaled = np.asarray(
        [
            error[0] / max(problem.force_ref_n, 1e-9),
            error[1] / max(problem.force_ref_n, 1e-9),
            error[2] / max(problem.torque_ref_nm, 1e-9),
        ],
        dtype=float,
    )
    norm = float(np.linalg.norm(scaled))
    if norm <= 1e-12:
        return np.zeros(3, dtype=float)
    return scaled / norm


def _empty_arrays(problem: SP3Problem) -> tuple[np.ndarray, np.ndarray]:
    count = len(problem.world.robots)
    return np.zeros(count, dtype=int), np.zeros(count, dtype=int)


def _assign(labels: np.ndarray, slots: np.ndarray, robot_idx: int, load_idx: int, slot_idx: int) -> None:
    labels[robot_idx] = load_idx + 1
    slots[robot_idx] = slot_idx + 1


def _load_order(problem: SP3Problem) -> list[int]:
    rewards = np.asarray([load.reward for load in problem.world.loads], dtype=float)
    return [int(idx) for idx in np.argsort(-rewards)]


def _nearest_free_slot(problem: SP3Problem, robot_idx: int, load_idx: int, used_slots: set[int]) -> int | None:
    candidates = [slot_idx for slot_idx in range(len(problem.load_slots[load_idx])) if slot_idx not in used_slots]
    if not candidates:
        return None
    distances = [_robot_slot_distance(problem, robot_idx, load_idx, slot_idx) for slot_idx in candidates]
    return int(candidates[int(np.argmin(distances))])


def _robot_slot_distance(problem: SP3Problem, robot_idx: int, load_idx: int, slot_idx: int) -> float:
    robot = problem.world.robots[robot_idx]
    load = problem.world.loads[load_idx]
    slot = problem.load_slots[load_idx][slot_idx]
    target = load.pickup + slot.offset_xy
    return float(np.linalg.norm(robot.position - target))


def _assigned_payload(problem: SP3Problem, assignment: SP3Assignment, load_idx: int) -> float:
    payloads = payload_vector(problem)
    return float(np.sum(payloads[assignment.labels == load_idx + 1]))
