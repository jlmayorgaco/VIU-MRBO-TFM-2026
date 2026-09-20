"""Shared primal--dual benchmark engine for SP1 dynamics V3.

The five fractional methods share world, mask, initialization, dual variables,
PI tracker, stopping tests and budgets.  Only ``_revision_step`` changes.  The
Replicator branch deliberately reproduces the V2 mirror--prox arithmetic; it is
kept as the frozen baseline instead of being numerically optimized here.

All quantities are dimensionless after the same cost and resource
normalizations used by V2.  A logical round is one accepted primal--dual
update.  A packet is one directed vector sent across one graph edge during one
consensus exchange.  The vector concatenates the local dual and PI tracker, so
its dimension is ``2 * K * M`` for ``M`` resource constraints.
"""

from __future__ import annotations

import math
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp1_canonical.validation.dynamics import GraphInfo, metropolis_matrix
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v2 import (
    InstancePreconditioner,
    estimate_instance_preconditioner,
)
from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld, normalized_constraints
from viu_mrob_tfm.sp1_canonical.validation.solvers import allocation_entropy, evaluate_relaxed


FRACTIONAL_METHODS = (
    "Replicator-D-preconditioned",
    "Smith-D-preconditioned",
    "BNN-D-preconditioned",
    "Logit-D-annealed",
    "BestResponse-D",
)

METHOD_KEYS = {
    "Replicator-D-preconditioned": "replicator",
    "Smith-D-preconditioned": "smith",
    "BNN-D-preconditioned": "bnn",
    "Logit-D-annealed": "logit",
    "BestResponse-D": "best_response",
}


@dataclass(frozen=True, slots=True)
class DynamicsBudgets:
    max_logical_rounds: int
    max_wall_time_s: float
    max_scalar_transmissions: int
    max_payoff_evaluations: int

    def __post_init__(self) -> None:
        if self.max_logical_rounds < 1:
            raise ValueError("max_logical_rounds must be positive")
        if self.max_wall_time_s <= 0.0:
            raise ValueError("max_wall_time_s must be positive")
        if self.max_scalar_transmissions < 0 or self.max_payoff_evaluations < 1:
            raise ValueError("communication and payoff budgets must be nonnegative")


@dataclass(slots=True)
class OperationCounts:
    logical_rounds: int = 0
    agent_updates: int = 0
    epochs: float = 0.0
    payoff_evaluations: int = 0
    pairwise_payoff_comparisons: int = 0
    projection_calls: int = 0
    softmax_calls: int = 0
    dual_updates: int = 0
    consensus_updates: int = 0
    packets_total: int = 0
    scalar_transmissions_total: int = 0

    def as_dict(self) -> dict[str, int | float]:
        payload = {name: getattr(self, name) for name in self.__dataclass_fields__}
        payload["payload_bytes_total"] = 8 * self.scalar_transmissions_total
        return payload


@dataclass(frozen=True, slots=True)
class FractionalDynamicsResult:
    method: str
    x: np.ndarray
    dual: np.ndarray
    tracker: np.ndarray
    operational_x: np.ndarray | None
    history: pd.DataFrame
    preconditioner: InstancePreconditioner
    operational_converged: bool
    refinement_converged: bool
    operational_round: int | None
    refinement_round: int | None
    stop_reason: str
    censored: bool
    censoring_reason: str
    counts: Mapping[str, int | float]
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    terminal_temperature: float
    entropy: float
    active_support: int
    concentration_round: int | None
    reactivation_round: int | None
    invariant_violations: Mapping[str, float | bool]


@dataclass(frozen=True, slots=True)
class PureBestResponseResult:
    assignment: np.ndarray
    x: np.ndarray
    dual: np.ndarray
    tracker: np.ndarray
    history: pd.DataFrame
    converged: bool
    stop_reason: str
    censored: bool
    censoring_reason: str
    counts: Mapping[str, int | float]
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    unilateral_improvement: float
    invariant_violations: Mapping[str, float | bool]


def budgets_from_mapping(values: Mapping[str, Any]) -> DynamicsBudgets:
    return DynamicsBudgets(
        max_logical_rounds=int(values["max_logical_rounds"]),
        max_wall_time_s=float(values["max_wall_time_s"]),
        max_scalar_transmissions=int(values["max_scalar_transmissions"]),
        max_payoff_evaluations=int(values["max_payoff_evaluations"]),
    )


def initial_fractional_state(costs: np.ndarray) -> np.ndarray:
    """Return the frozen V2 uniform-interior state including idle."""

    feasible = np.isfinite(costs)
    n, k = costs.shape
    x = np.zeros((n, k + 1), dtype=float)
    for robot in range(n):
        valid = np.flatnonzero(np.r_[feasible[robot], True])
        x[robot, valid] = 1.0 / len(valid)
    return x


def _masked_project_simplex(vector: np.ndarray, valid: np.ndarray) -> np.ndarray:
    result = np.zeros_like(vector, dtype=float)
    values = np.asarray(vector[valid], dtype=float)
    ordered = np.sort(values)[::-1]
    cumulative = np.cumsum(ordered) - 1.0
    indices = np.arange(1, len(values) + 1)
    positive = np.flatnonzero(ordered - cumulative / indices > 0.0)
    if positive.size == 0:
        result[valid] = 1.0 / int(np.sum(valid))
        return result
    rho = int(positive[-1])
    theta = cumulative[rho] / float(rho + 1)
    result[valid] = np.maximum(values - theta, 0.0)
    return result


def _masked_softmax(fitness: np.ndarray, valid: np.ndarray, temperature: float) -> np.ndarray:
    result = np.zeros_like(fitness, dtype=float)
    values = fitness[valid] / max(float(temperature), 1e-12)
    values = values - float(np.max(values))
    exponent = np.exp(np.clip(values, -700.0, 0.0))
    result[valid] = exponent / max(float(np.sum(exponent)), 1e-300)
    return result


def _initialize_state(
    world: ResourceWorld,
    costs: np.ndarray,
    *,
    distributed: bool,
    initial_x: np.ndarray | None,
    initial_dual: np.ndarray | None,
    initial_tracker: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n, k = costs.shape
    m = world.requirements.shape[1]
    feasible = np.isfinite(costs)
    if initial_x is None:
        x = initial_fractional_state(costs)
    else:
        candidate = np.asarray(initial_x, dtype=float)
        if candidate.shape == (n, k):
            candidate = np.column_stack([candidate, np.maximum(1.0 - candidate.sum(axis=1), 0.0)])
        if candidate.shape != (n, k + 1):
            raise ValueError(f"initial_x must have shape {(n, k)} or {(n, k + 1)}")
        x = np.zeros_like(candidate)
        for robot in range(n):
            valid = np.r_[feasible[robot], True]
            x[robot] = _masked_project_simplex(candidate[robot], valid)
    dual_shape = (n, k, m) if distributed else (k, m)
    if initial_dual is None:
        dual = np.zeros(dual_shape, dtype=float)
    else:
        dual = np.asarray(initial_dual, dtype=float).copy()
        if dual.shape != dual_shape or not np.all(np.isfinite(dual)):
            raise ValueError(f"initial_dual must be finite with shape {dual_shape}")
        dual = np.maximum(dual, 0.0)
    normalized = normalized_constraints(world)

    def local_residual(state: np.ndarray) -> np.ndarray:
        return 1.0 / n - normalized * state[:, :k, None]

    if distributed:
        tracker = local_residual(x) if initial_tracker is None else np.asarray(initial_tracker, dtype=float).copy()
        if tracker.shape != (n, k, m) or not np.all(np.isfinite(tracker)):
            raise ValueError(f"initial_tracker must be finite with shape {(n, k, m)}")
    else:
        tracker = np.empty((0, k, m), dtype=float)
    return x, dual, tracker


def _method_temperature(method_key: str, parameters: Mapping[str, Any], round_index: int) -> float:
    if method_key != "logit":
        return math.nan
    return max(
        float(parameters.get("T_min", 0.005)),
        float(parameters.get("T_0", 0.15)) * float(parameters.get("gamma", 0.995)) ** round_index,
    )


def _revision_step(
    method_key: str,
    x: np.ndarray,
    fitness: np.ndarray,
    feasible: np.ndarray,
    *,
    step: float,
    parameters: Mapping[str, Any],
    round_index: int,
    counts: OperationCounts,
) -> np.ndarray:
    """Apply only the method-specific strategic revision map."""

    n, strategies = x.shape
    valid_mask = np.column_stack([feasible, np.ones(n, dtype=bool)])
    if method_key == "replicator":
        exponent = np.clip(step * fitness, -60.0, 60.0)
        candidate = x * np.exp(exponent)
        candidate[:, :-1] = np.where(feasible, candidate[:, :-1], 0.0)
        candidate /= np.maximum(candidate.sum(axis=1, keepdims=True), 1e-15)
        return candidate

    result = np.zeros_like(x)
    damping = float(parameters.get("damping", 1.0))
    if method_key == "smith":
        for robot in range(n):
            valid = valid_mask[robot]
            xv = x[robot, valid]
            fv = fitness[robot, valid]
            difference = fv[:, None] - fv[None, :]
            positive = np.maximum(difference, 0.0)
            derivative = positive @ xv - xv * np.sum(positive.T, axis=1)
            raw = xv + damping * step * derivative
            embedded = np.zeros(strategies, dtype=float)
            embedded[valid] = raw
            result[robot] = _masked_project_simplex(embedded, valid)
            counts.projection_calls += 1
            counts.pairwise_payoff_comparisons += int(len(fv) * max(len(fv) - 1, 0))
        return result

    if method_key == "bnn":
        for robot in range(n):
            valid = valid_mask[robot]
            xv = x[robot, valid]
            fv = fitness[robot, valid]
            excess = fv - float(np.dot(xv, fv))
            positive = np.maximum(excess, 0.0)
            derivative = positive - xv * float(np.sum(positive))
            raw = xv + damping * step * derivative
            embedded = np.zeros(strategies, dtype=float)
            embedded[valid] = raw
            result[robot] = _masked_project_simplex(embedded, valid)
            counts.projection_calls += 1
        return result

    if method_key == "logit":
        temperature = _method_temperature(method_key, parameters, round_index)
        integration = float(np.clip(damping * step, 0.0, 1.0))
        for robot in range(n):
            target = _masked_softmax(fitness[robot], valid_mask[robot], temperature)
            result[robot] = (1.0 - integration) * x[robot] + integration * target
            counts.softmax_calls += 1
        return result

    if method_key == "best_response":
        eta_br = float(parameters.get("eta_br", 0.25))
        if not 0.0 < eta_br <= 1.0:
            raise ValueError("eta_br must belong to (0,1]")
        for robot in range(n):
            valid_indices = np.flatnonzero(valid_mask[robot])
            best = int(valid_indices[int(np.argmax(fitness[robot, valid_indices]))])
            target = np.zeros(strategies, dtype=float)
            target[best] = 1.0
            result[robot] = (1.0 - eta_br) * x[robot] + eta_br * target
            counts.pairwise_payoff_comparisons += max(len(valid_indices) - 1, 0)
        return result
    raise ValueError(f"unknown method key: {method_key}")


def _invariants(x: np.ndarray, feasible: np.ndarray) -> dict[str, float | bool]:
    simplex = float(np.max(np.abs(x.sum(axis=1) - 1.0)))
    minimum = float(np.min(x))
    mask = float(np.sum(np.abs(x[:, :-1][~feasible])))
    finite = bool(np.all(np.isfinite(x)))
    return {
        "simplex_violation": simplex,
        "nonnegativity_violation": max(-minimum, 0.0),
        "mask_violation": mask,
        "finite": finite,
    }


def run_fractional_dynamics(
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    method: str,
    *,
    distributed: bool,
    parameters: Mapping[str, Any],
    budgets: DynamicsBudgets,
    operational_tolerances: Mapping[str, float],
    refinement_tolerances: Mapping[str, float],
    entropy_tau: float = 0.003,
    consensus_gain: float = 1.0,
    use_integral_consensus: bool = True,
    history_stride: int = 25,
    initial_x: np.ndarray | None = None,
    initial_dual: np.ndarray | None = None,
    initial_tracker: np.ndarray | None = None,
    attempt_refinement: bool = True,
) -> FractionalDynamicsResult:
    """Run one fractional method under common dual, PI and budget rules."""

    if method not in METHOD_KEYS:
        raise ValueError(f"unknown fractional method: {method}")
    if history_stride < 1:
        raise ValueError("history_stride must be positive")
    method_key = METHOD_KEYS[method]
    n, k = costs.shape
    m = world.requirements.shape[1]
    feasible = np.isfinite(costs)
    x, dual, tracker = _initialize_state(
        world,
        costs,
        distributed=distributed,
        initial_x=initial_x,
        initial_dual=initial_dual,
        initial_tracker=initial_tracker,
    )
    initial_zero = (x <= 1e-12) & np.column_stack([feasible, np.ones(n, dtype=bool)])
    weights = metropolis_matrix(graph)
    consensus_matrix = (1.0 - consensus_gain) * np.eye(n) + consensus_gain * weights
    degrees = graph.adjacency.sum(axis=1).astype(float)
    graph_laplacian = np.diag(degrees) - graph.adjacency.astype(float)
    normalized = normalized_constraints(world)
    finite_values = costs[feasible]
    cost_scale = max(float(np.max(finite_values)) if finite_values.size else 1.0, 1e-9)
    normalized_costs = np.where(feasible, costs / cost_scale, 0.0)
    preconditioner = estimate_instance_preconditioner(
        world,
        graph,
        distributed=distributed,
        eta=float(parameters.get("eta", 0.22)),
        step_min=float(parameters.get("step_min", 0.005)),
        step_max=float(parameters.get("step_max", 0.10)),
    )
    step = preconditioner.step
    counts = OperationCounts()
    history: list[dict[str, Any]] = []
    operational_converged = False
    refinement_converged = False
    operational_round: int | None = None
    refinement_round: int | None = None
    operational_x: np.ndarray | None = None
    concentration_round: int | None = None
    reactivation_round: int | None = None
    stop_reason = "max_rounds"
    censoring_reason = "max_rounds"

    def local_residual(state: np.ndarray) -> np.ndarray:
        return 1.0 / n - normalized * state[:, :k, None]

    def fitness(state: np.ndarray, dual_state: np.ndarray) -> np.ndarray:
        counts.payoff_evaluations += n
        if distributed:
            load_fitness = -normalized_costs + np.einsum("ikm,ikm->ik", dual_state, normalized)
        else:
            load_fitness = -normalized_costs + np.einsum("km,ikm->ik", dual_state, normalized)
        result = np.column_stack([load_fitness, np.zeros(n)])
        # Shared objective regularization.  Logit temperature below is a
        # revision mechanism and is not folded into this term.
        result -= entropy_tau * (np.log(np.maximum(state, 1e-15)) + 1.0)
        result[:, :k] = np.where(feasible, result[:, :k], -np.inf)
        return result

    def central_dual_step(base_dual: np.ndarray, state: np.ndarray) -> np.ndarray:
        coverage = np.einsum("ik,ikm->km", state[:, :k], normalized)
        counts.dual_updates += 1
        return np.maximum(base_dual + step * (1.0 - coverage), 0.0)

    def distributed_candidate(
        base_dual: np.ndarray, base_tracker: np.ndarray, state: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        mixed_tracker = np.einsum("ij,jkm->ikm", consensus_matrix, base_tracker)
        mixed_dual = np.einsum("ij,jkm->ikm", consensus_matrix, base_dual)
        candidate_dual = np.maximum(mixed_dual + step * n * mixed_tracker, 0.0)
        return candidate_dual, mixed_tracker

    exchanges = 2 if method_key == "replicator" else 1
    packet_increment = 2 * graph.edges * exchanges if distributed else 0
    scalar_increment = packet_increment * 2 * k * m
    payoff_increment_upper = n * exchanges
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0

    for round_index in range(budgets.max_logical_rounds + 1):
        elapsed = time.perf_counter() - started_wall
        if elapsed >= budgets.max_wall_time_s:
            stop_reason = censoring_reason = "wall_time"
            break
        if counts.scalar_transmissions_total + scalar_increment > budgets.max_scalar_transmissions:
            stop_reason = censoring_reason = "communication_budget"
            break
        if counts.payoff_evaluations + payoff_increment_upper > budgets.max_payoff_evaluations:
            stop_reason = censoring_reason = "payoff_budget"
            break

        current_fitness = fitness(x, dual)
        candidate_x = _revision_step(
            method_key,
            x,
            current_fitness,
            feasible,
            step=step,
            parameters=parameters,
            round_index=round_index,
            counts=counts,
        )
        if distributed:
            dual_candidate, _ = distributed_candidate(dual, tracker, x)
            mean_dual = np.mean(dual, axis=0)
            disagreement = float(np.linalg.norm(dual - mean_dual[None, :, :]))
            laplacian_dual = np.einsum("ij,jkm->ikm", graph_laplacian, dual)
            consensus_absolute = float(np.linalg.norm(laplacian_dual))
            consensus_residual = consensus_absolute / (1.0 + float(np.linalg.norm(dual)))
        else:
            dual_candidate = central_dual_step(dual, x)
            disagreement = consensus_absolute = consensus_residual = 0.0
        coverage = np.einsum("ik,ikm->km", x[:, :k], normalized)
        primal_absolute = float(np.linalg.norm(np.maximum(1.0 - coverage, 0.0)))
        primal_residual = primal_absolute / (1.0 + math.sqrt(k * m))
        primal_fixed = float(np.linalg.norm(candidate_x - x))
        dual_fixed = float(np.linalg.norm(dual_candidate - dual))
        fixed_absolute = float(math.hypot(primal_fixed, dual_fixed))
        state_norm = float(math.hypot(np.linalg.norm(x), np.linalg.norm(dual)))
        fixed_residual = fixed_absolute / (1.0 + state_norm)
        metrics = evaluate_relaxed(world, x[:, :k], costs)
        phase = "refinement" if operational_converged else "operational"
        tolerances = refinement_tolerances if operational_converged else operational_tolerances
        meets = bool(
            primal_residual <= float(tolerances["primal"])
            and consensus_residual <= float(tolerances["consensus"])
            and fixed_residual <= float(tolerances["fixed_point"])
        )
        invariants = _invariants(x, feasible)
        temperature = _method_temperature(method_key, parameters, round_index)
        active_support = int(np.sum(x > 1e-8))
        entropy = allocation_entropy(x[:, :k])
        if concentration_round is None and np.all(np.max(x, axis=1) >= 0.95):
            concentration_round = counts.logical_rounds
        if reactivation_round is None and np.any(initial_zero & (x > 1e-6)):
            reactivation_round = counts.logical_rounds
        should_record = bool(
            counts.logical_rounds % history_stride == 0
            or meets
            or counts.logical_rounds == budgets.max_logical_rounds
        )
        if should_record:
            history.append(
                {
                    "logical_round": counts.logical_rounds,
                    "phase": phase,
                    "primal_residual": primal_residual,
                    "primal_residual_absolute": primal_absolute,
                    "consensus_residual": consensus_residual,
                    "consensus_residual_absolute": consensus_absolute,
                    "consensus_disagreement": disagreement,
                    "fixed_point_residual": fixed_residual,
                    "fixed_point_residual_absolute": fixed_absolute,
                    "objective_raw": metrics["objective"],
                    "entropy": entropy,
                    "active_support": active_support,
                    "temperature": temperature,
                    "simplex_violation": invariants["simplex_violation"],
                    "mask_violation": invariants["mask_violation"],
                    "packets_total": counts.packets_total,
                    "scalar_transmissions_total": counts.scalar_transmissions_total,
                    "payoff_evaluations": counts.payoff_evaluations,
                    "wall_time_s": elapsed,
                }
            )
        if not bool(invariants["finite"]):
            stop_reason = censoring_reason = "numerical_failure"
            break
        if (
            float(invariants["simplex_violation"]) > 1e-8
            or float(invariants["nonnegativity_violation"]) > 1e-10
            or float(invariants["mask_violation"]) > 1e-10
        ):
            stop_reason = censoring_reason = "invalid_state"
            break
        if meets and not operational_converged:
            operational_converged = True
            operational_round = counts.logical_rounds
            operational_x = x[:, :k].copy()
            if not attempt_refinement:
                stop_reason = "operational_converged"
                censoring_reason = "none"
                break
            # Evaluate the strict gate from the same state on the next loop.
            continue
        if meets and operational_converged:
            refinement_converged = True
            refinement_round = counts.logical_rounds
            stop_reason = "refinement_converged"
            censoring_reason = "none"
            break
        if counts.logical_rounds >= budgets.max_logical_rounds:
            stop_reason = censoring_reason = "max_rounds"
            break

        previous_x = x
        if method_key == "replicator":
            # Frozen V2 mirror--prox arithmetic, including the same tracker and
            # corrector dual ordering.
            x_predictor = candidate_x
            if distributed:
                mixed_tracker = np.einsum("ij,jkm->ikm", consensus_matrix, tracker)
                tracker_predictor = (
                    mixed_tracker + local_residual(x_predictor) - local_residual(x)
                    if use_integral_consensus
                    else local_residual(x_predictor)
                )
                dual_predictor = np.maximum(
                    np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker_predictor,
                    0.0,
                )
            else:
                tracker_predictor = tracker
                dual_predictor = central_dual_step(dual, x)
            predictor_fitness = fitness(x_predictor, dual_predictor)
            x = _revision_step(
                method_key,
                x,
                predictor_fitness,
                feasible,
                step=step,
                parameters=parameters,
                round_index=round_index,
                counts=counts,
            )
            if distributed:
                tracker = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker)
                    + local_residual(x)
                    - local_residual(previous_x)
                    if use_integral_consensus
                    else local_residual(x)
                )
                dual = np.maximum(
                    np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker_predictor,
                    0.0,
                )
                counts.dual_updates += 2 * n
                counts.consensus_updates += 2 * n
            else:
                dual = central_dual_step(dual, x_predictor)
        else:
            x = candidate_x
            if distributed:
                tracker = (
                    np.einsum("ij,jkm->ikm", consensus_matrix, tracker)
                    + local_residual(x)
                    - local_residual(previous_x)
                    if use_integral_consensus
                    else local_residual(x)
                )
                dual = np.maximum(
                    np.einsum("ij,jkm->ikm", consensus_matrix, dual) + step * n * tracker,
                    0.0,
                )
                counts.dual_updates += n
                counts.consensus_updates += n
            else:
                dual = central_dual_step(dual, x)
        counts.logical_rounds += 1
        counts.agent_updates += n
        counts.epochs = float(counts.logical_rounds)
        counts.packets_total += packet_increment
        counts.scalar_transmissions_total += scalar_increment
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(dual)):
            stop_reason = censoring_reason = "numerical_failure"
            break

    wall_time = time.perf_counter() - started_wall
    cpu_time = time.process_time() - started_cpu
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    final_invariants = _invariants(x, feasible)
    censored = not operational_converged
    if operational_converged and censoring_reason != "none":
        # Refinement may be censored, but the operational endpoint was observed.
        censoring_reason = "none"
        censored = False
    return FractionalDynamicsResult(
        method=method,
        x=x[:, :k].copy(),
        dual=dual.copy(),
        tracker=tracker.copy(),
        operational_x=operational_x,
        history=pd.DataFrame(history),
        preconditioner=preconditioner,
        operational_converged=operational_converged,
        refinement_converged=refinement_converged,
        operational_round=operational_round,
        refinement_round=refinement_round,
        stop_reason=stop_reason,
        censored=censored,
        censoring_reason=censoring_reason,
        counts=counts.as_dict(),
        wall_time_s=float(wall_time),
        cpu_time_s=float(cpu_time),
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0 * 1024.0)),
        terminal_temperature=_method_temperature(method_key, parameters, counts.logical_rounds),
        entropy=allocation_entropy(x[:, :k]),
        active_support=int(np.sum(x > 1e-8)),
        concentration_round=concentration_round,
        reactivation_round=reactivation_round,
        invariant_violations=final_invariants,
    )


def recompute_message_accounting(
    *,
    logical_rounds: int,
    graph_edges: int,
    n_loads: int,
    n_resources: int,
    consensus_exchanges_per_round: int,
    distributed: bool,
) -> dict[str, int]:
    packets = (
        2 * int(graph_edges) * int(consensus_exchanges_per_round) * int(logical_rounds)
        if distributed
        else 0
    )
    scalars = packets * 2 * int(n_loads) * int(n_resources)
    return {"packets_total": packets, "scalar_transmissions_total": scalars, "payload_bytes_total": 8 * scalars}


def run_best_response_pure(
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    *,
    parameters: Mapping[str, Any],
    budgets: DynamicsBudgets,
    consensus_tolerance: float,
    epsilon_br: float = 1e-6,
    seed: int = 0,
    initial_assignment: np.ndarray | None = None,
) -> PureBestResponseResult:
    """Asynchronous pure-strategy comparator with event-level messages.

    One activation selects one robot.  The activated robot sends its dual and
    tracker vector to every neighbor; only these actual event transmissions are
    counted.  A pure equilibrium is reported after one complete epoch without
    accepted changes, no unilateral gain above ``epsilon_br`` and consensus
    below tolerance.
    """

    n, k = costs.shape
    m = world.requirements.shape[1]
    feasible = np.isfinite(costs)
    rng = np.random.default_rng(int(seed))
    if initial_assignment is None:
        assignment = np.full(n, k, dtype=int)
    else:
        assignment = np.asarray(initial_assignment, dtype=int).copy()
        if assignment.shape != (n,):
            raise ValueError(f"initial_assignment must have shape {(n,)}")
    x = np.zeros((n, k + 1), dtype=float)
    x[np.arange(n), assignment] = 1.0
    normalized = normalized_constraints(world)
    dual = np.zeros((n, k, m), dtype=float)
    tracker = 1.0 / n - normalized * x[:, :k, None]
    weights = metropolis_matrix(graph)
    preconditioner = estimate_instance_preconditioner(
        world,
        graph,
        distributed=True,
        eta=float(parameters.get("eta", 0.16)),
        step_min=float(parameters.get("step_min", 0.005)),
        step_max=float(parameters.get("step_max", 0.10)),
    )
    step = preconditioner.step
    finite_values = costs[feasible]
    cost_scale = max(float(np.max(finite_values)) if finite_values.size else 1.0, 1e-9)
    normalized_costs = np.where(feasible, costs / cost_scale, 0.0)
    counts = OperationCounts()
    history: list[dict[str, Any]] = []
    changes_in_epoch = 0
    converged = False
    stop_reason = censoring_reason = "max_rounds"
    max_activations = budgets.max_logical_rounds * n
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    last_max_gain = math.inf

    for activation in range(max_activations):
        if time.perf_counter() - started_wall >= budgets.max_wall_time_s:
            stop_reason = censoring_reason = "wall_time"
            break
        robot = int(rng.integers(0, n))
        degree = int(np.sum(graph.adjacency[robot]))
        next_packets = degree
        next_scalars = next_packets * 2 * k * m
        if counts.scalar_transmissions_total + next_scalars > budgets.max_scalar_transmissions:
            stop_reason = censoring_reason = "communication_budget"
            break
        if counts.payoff_evaluations + 1 > budgets.max_payoff_evaluations:
            stop_reason = censoring_reason = "payoff_budget"
            break
        load_fitness = -normalized_costs[robot] + np.einsum("km,km->k", dual[robot], normalized[robot])
        fitness = np.r_[load_fitness, 0.0]
        fitness[:k] = np.where(feasible[robot], fitness[:k], -np.inf)
        valid = np.flatnonzero(np.r_[feasible[robot], True])
        best = int(valid[int(np.argmax(fitness[valid]))])
        current = int(assignment[robot])
        gain = float(fitness[best] - fitness[current])
        counts.payoff_evaluations += 1
        counts.pairwise_payoff_comparisons += max(len(valid) - 1, 0)
        previous_x = x.copy()
        if best != current and gain > epsilon_br:
            assignment[robot] = best
            x[robot] = 0.0
            x[robot, best] = 1.0
            changes_in_epoch += 1
        mixed_dual = weights[robot] @ dual.reshape(n, -1)
        mixed_tracker = weights[robot] @ tracker.reshape(n, -1)
        new_local = (1.0 / n - normalized[robot] * x[robot, :k, None]).reshape(-1)
        old_local = (1.0 / n - normalized[robot] * previous_x[robot, :k, None]).reshape(-1)
        tracker[robot] = (mixed_tracker + new_local - old_local).reshape(k, m)
        dual[robot] = np.maximum((mixed_dual + step * n * tracker[robot].reshape(-1)).reshape(k, m), 0.0)
        counts.agent_updates += 1
        counts.dual_updates += 1
        counts.consensus_updates += 1
        counts.packets_total += next_packets
        counts.scalar_transmissions_total += next_scalars
        if (activation + 1) % n == 0:
            counts.logical_rounds += 1
            counts.epochs = float(counts.logical_rounds)
            mean_dual = np.mean(dual, axis=0)
            consensus = float(np.linalg.norm(dual - mean_dual[None])) / (1.0 + float(np.linalg.norm(dual)))
            gains = []
            for other in range(n):
                lf = -normalized_costs[other] + np.einsum("km,km->k", dual[other], normalized[other])
                ff = np.r_[lf, 0.0]
                ff[:k] = np.where(feasible[other], ff[:k], -np.inf)
                gains.append(float(np.max(ff) - ff[int(assignment[other])]))
            last_max_gain = max(gains, default=0.0)
            history.append(
                {
                    "epoch": counts.logical_rounds,
                    "accepted_changes": changes_in_epoch,
                    "max_unilateral_improvement": last_max_gain,
                    "consensus_residual": consensus,
                    "packets_total": counts.packets_total,
                    "scalar_transmissions_total": counts.scalar_transmissions_total,
                }
            )
            if changes_in_epoch == 0 and last_max_gain <= epsilon_br and consensus <= consensus_tolerance:
                converged = True
                stop_reason = "pure_equilibrium"
                censoring_reason = "none"
                break
            changes_in_epoch = 0
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(dual)):
            stop_reason = censoring_reason = "numerical_failure"
            break
    wall_time = time.perf_counter() - started_wall
    cpu_time = time.process_time() - started_cpu
    peak = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else baseline_peak
    if owned_trace:
        tracemalloc.stop()
    invariants = _invariants(x, feasible)
    return PureBestResponseResult(
        assignment=np.where(assignment == k, -1, assignment).astype(int),
        x=x[:, :k],
        dual=dual,
        tracker=tracker,
        history=pd.DataFrame(history),
        converged=converged,
        stop_reason=stop_reason,
        censored=not converged,
        censoring_reason=censoring_reason,
        counts=counts.as_dict(),
        wall_time_s=float(wall_time),
        cpu_time_s=float(cpu_time),
        peak_memory_mb=float(max(peak - baseline_peak, 0) / (1024.0 * 1024.0)),
        unilateral_improvement=float(last_max_gain),
        invariant_violations=invariants,
    )


__all__ = [
    "DynamicsBudgets",
    "FRACTIONAL_METHODS",
    "FractionalDynamicsResult",
    "METHOD_KEYS",
    "OperationCounts",
    "PureBestResponseResult",
    "budgets_from_mapping",
    "initial_fractional_state",
    "recompute_message_accounting",
    "run_best_response_pure",
    "run_fractional_dynamics",
]
