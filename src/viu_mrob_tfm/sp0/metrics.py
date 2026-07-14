"""Metrics for SP0 homogeneous one-to-one assignment."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp0.methods import (
    SP0MethodResult,
    assignment_objective,
    assignment_social_cost,
    assignment_valid,
    swap_epsilon,
    unilateral_epsilon,
)
from viu_mrob_tfm.sp0.scenario import SP0World


@dataclass(frozen=True, slots=True)
class SP0Metrics:
    """Scalar metrics for one SP0 run.

    v1.1 keeps legacy aliases such as ``success`` and ``timeout`` but also
    exposes the corrected semantics explicitly.
    """

    matching_valid: bool | None
    success: bool | None
    continuous_converged: bool | None
    continuous_timeout: bool | None
    continuous_equilibrium_reached: bool | None
    closure_applied: bool | None
    closure_type: str | None
    closure_success: bool | None
    maximum_cardinality: bool | None
    final_success: bool | None
    coverage: float
    assigned_count: int | None
    social_cost: float
    social_regret: float
    normalized_regret: float
    continuous_objective: float
    continuous_normalized_regret: float
    preclosure_matching_valid: bool | None
    preclosure_coverage: float
    preclosure_objective: float
    preclosure_normalized_regret: float
    closure_regret_delta: float
    closure_vs_preclosure_regret_delta: float
    final_vs_continuous_regret_delta: float
    cost_gap: float
    makespan_proxy: float
    p95_individual_cost: float
    convergence_time: float
    time_to_epsilon_solution: float
    time_to_epsilon_duration_s: float
    time_to_epsilon_observed: bool
    messages_to_epsilon_solution: float
    bytes_to_epsilon_solution: float
    timeout: bool
    messages: int
    bytes_sent: int
    runtime_cpu_s: float
    runtime_wall_s: float
    oracle_solve_time_s: float
    oracle_lookup_time_s: float
    method_online_time_s: float
    closure_runtime_s: float
    memory_peak: float
    epsilon_ne_1: float
    epsilon_ne_2: float
    fractionality: float
    switches: int
    potential_violations: int
    occupancy_error: float
    state_change: float | None
    equilibrium_residual: float | None
    equilibrium_residual_id: str | None
    simulation_end_time_s: float | None
    closure_messages: int
    global_strong_closure: bool
    largest_negative_delta: float
    median_potential_delta: float
    p01_potential_delta: float
    observed_poa_ratio: float
    price_of_integrality: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "matching_valid": self.matching_valid,
            "success": self.success,
            "continuous_converged": self.continuous_converged,
            "continuous_timeout": self.continuous_timeout,
            "continuous_equilibrium_reached": self.continuous_equilibrium_reached,
            "closure_applied": self.closure_applied,
            "closure_type": self.closure_type,
            "closure_success": self.closure_success,
            "maximum_cardinality": self.maximum_cardinality,
            "final_success": self.final_success,
            "coverage": self.coverage,
            "assigned_count": self.assigned_count,
            "social_cost": self.social_cost,
            "social_regret": self.social_regret,
            "normalized_regret": self.normalized_regret,
            "continuous_objective": self.continuous_objective,
            "continuous_normalized_regret": self.continuous_normalized_regret,
            "preclosure_matching_valid": self.preclosure_matching_valid,
            "preclosure_coverage": self.preclosure_coverage,
            "preclosure_objective": self.preclosure_objective,
            "preclosure_normalized_regret": self.preclosure_normalized_regret,
            "closure_regret_delta": self.closure_regret_delta,
            "closure_vs_preclosure_regret_delta": self.closure_vs_preclosure_regret_delta,
            "final_vs_continuous_regret_delta": self.final_vs_continuous_regret_delta,
            "cost_gap": self.cost_gap,
            "makespan_proxy": self.makespan_proxy,
            "p95_individual_cost": self.p95_individual_cost,
            "convergence_time": self.convergence_time,
            "time_to_epsilon_solution": self.time_to_epsilon_solution,
            "time_to_epsilon_duration_s": self.time_to_epsilon_duration_s,
            "time_to_epsilon_observed": self.time_to_epsilon_observed,
            "messages_to_epsilon_solution": self.messages_to_epsilon_solution,
            "bytes_to_epsilon_solution": self.bytes_to_epsilon_solution,
            "timeout": self.timeout,
            "messages": self.messages,
            "bytes": self.bytes_sent,
            "runtime_cpu_s": self.runtime_cpu_s,
            "runtime_wall_s": self.runtime_wall_s,
            "oracle_solve_time_s": self.oracle_solve_time_s,
            "oracle_lookup_time_s": self.oracle_lookup_time_s,
            "method_online_time_s": self.method_online_time_s,
            "closure_runtime_s": self.closure_runtime_s,
            "memory_peak": self.memory_peak,
            "epsilon_ne_1": self.epsilon_ne_1,
            "epsilon_ne_2": self.epsilon_ne_2,
            "fractionality": self.fractionality,
            "switches": self.switches,
            "potential_violations": self.potential_violations,
            "occupancy_error": self.occupancy_error,
            "state_change": self.state_change,
            "equilibrium_residual": self.equilibrium_residual,
            "equilibrium_residual_id": self.equilibrium_residual_id,
            "simulation_end_time_s": self.simulation_end_time_s,
            "closure_messages": self.closure_messages,
            "global_strong_closure": self.global_strong_closure,
            "largest_negative_delta": self.largest_negative_delta,
            "median_potential_delta": self.median_potential_delta,
            "p01_potential_delta": self.p01_potential_delta,
            "observed_poa_ratio": self.observed_poa_ratio,
            "price_of_integrality": self.price_of_integrality,
        }


def evaluate_sp0_result(world: SP0World, result: SP0MethodResult) -> SP0Metrics:
    labels = np.asarray(result.labels, dtype=int)
    raw_only = (result.rounding_id or "").upper() == "RAW"
    denominator = float((world.s_star + 1.0) * world.s_star + world.s_star)
    continuous_objective = _continuous_objective(world, result)
    continuous_regret = (
        float((continuous_objective - world.oracle_j) / max(denominator, 1.0e-12))
        if np.isfinite(continuous_objective)
        else math.nan
    )
    preclosure_matching_valid: bool | None = None
    preclosure_coverage = math.nan
    preclosure_objective = math.nan
    preclosure_normalized_regret = math.nan
    if result.preclosure_labels is not None:
        preclosure_labels = np.asarray(result.preclosure_labels, dtype=int)
        preclosure_matching_valid = assignment_valid(preclosure_labels, world.n_loads)
        positive = preclosure_labels[preclosure_labels > 0]
        preclosure_coverage = float(np.unique(positive).size / max(world.s_star, 1))
        preclosure_objective = assignment_objective(world, preclosure_labels)
        preclosure_normalized_regret = float(
            max(preclosure_objective - world.oracle_j, 0.0) / max(denominator, 1.0e-12)
        )

    if raw_only:
        valid: bool | None = None
        assigned_count: int | None = None
        maximum_cardinality: bool | None | None = None
        final_success: bool | None | None = None
        social_cost = math.nan
        j_value = math.nan
        social_regret = math.nan
        normalized_regret = continuous_regret
        active_costs = np.asarray([], dtype=float)
        coverage = math.nan
        cost_gap = math.nan
        epsilon1 = math.nan
        epsilon2 = math.nan
        observed_poa = math.nan
        price_integrality = math.nan
        closure_regret_delta = math.nan
        final_vs_continuous_regret_delta = math.nan
    else:
        valid = assignment_valid(labels, world.n_loads)
        assigned_count = int(np.sum(labels > 0)) if valid else int(np.unique(labels[labels > 0]).size)
        maximum_cardinality = bool(valid and assigned_count == world.s_star)
        final_success = bool(result.final_success if result.final_success is not None else maximum_cardinality)
        social_cost = assignment_social_cost(world, labels)
        j_value = assignment_objective(world, labels)
        social_regret = float(j_value - world.oracle_j)
        normalized_regret = float(max(social_regret, 0.0) / max(denominator, 1.0e-12))
        active_costs = _active_costs(world, labels)
        coverage = float(assigned_count / max(world.s_star, 1))
        cost_gap = float(social_cost - world.oracle_social_cost) if final_success else math.nan
        epsilon1 = unilateral_epsilon(world, labels) if valid else math.nan
        epsilon2 = swap_epsilon(world, labels) if valid else math.nan
        observed_poa = float((1.0 + j_value) / (1.0 + world.oracle_j))
        price_integrality = (
            float((1.0 + j_value) / (1.0 + continuous_objective))
            if np.isfinite(continuous_objective)
            else math.nan
        )
        closure_baseline = (
            preclosure_normalized_regret
            if np.isfinite(preclosure_normalized_regret)
            else continuous_regret
        )
        closure_regret_delta = (
            float(normalized_regret - closure_baseline)
            if np.isfinite(closure_baseline)
            else math.nan
        )
        final_vs_continuous_regret_delta = (
            float(normalized_regret - continuous_regret)
            if np.isfinite(continuous_regret)
            else math.nan
        )

    (
        time_to_epsilon,
        time_to_epsilon_duration,
        time_to_epsilon_observed,
        messages_to_epsilon,
        bytes_to_epsilon,
    ) = _useful_solution_metrics(world, result, epsilon=0.05)
    makespan = float(np.max(active_costs)) if active_costs.size else math.nan
    p95 = float(np.quantile(active_costs, 0.95)) if active_costs.size else math.nan
    measured_runtime_ms = float(result.method_online_time_ms or result.runtime_ms)
    runtime_s = measured_runtime_ms / 1000.0
    return SP0Metrics(
        matching_valid=valid,
        success=final_success,
        continuous_converged=result.continuous_converged,
        continuous_timeout=result.continuous_timeout,
        continuous_equilibrium_reached=result.continuous_equilibrium_reached,
        closure_applied=result.closure_applied,
        closure_type=result.closure_type or result.rounding_id,
        closure_success=result.closure_success,
        maximum_cardinality=maximum_cardinality,
        final_success=final_success,
        coverage=coverage,
        assigned_count=assigned_count,
        social_cost=social_cost,
        social_regret=social_regret,
        normalized_regret=normalized_regret,
        continuous_objective=continuous_objective,
        continuous_normalized_regret=continuous_regret,
        preclosure_matching_valid=preclosure_matching_valid,
        preclosure_coverage=preclosure_coverage,
        preclosure_objective=preclosure_objective,
        preclosure_normalized_regret=preclosure_normalized_regret,
        closure_regret_delta=closure_regret_delta,
        closure_vs_preclosure_regret_delta=closure_regret_delta,
        final_vs_continuous_regret_delta=final_vs_continuous_regret_delta,
        cost_gap=cost_gap,
        makespan_proxy=makespan,
        p95_individual_cost=p95,
        convergence_time=math.nan if result.continuous_timeout is True else float(result.convergence_time),
        time_to_epsilon_solution=time_to_epsilon,
        time_to_epsilon_duration_s=time_to_epsilon_duration,
        time_to_epsilon_observed=time_to_epsilon_observed,
        messages_to_epsilon_solution=messages_to_epsilon,
        bytes_to_epsilon_solution=bytes_to_epsilon,
        timeout=bool(result.continuous_timeout if result.continuous_timeout is not None else result.timeout),
        messages=int(result.messages),
        bytes_sent=int(result.bytes_sent),
        runtime_cpu_s=runtime_s,
        runtime_wall_s=runtime_s,
        oracle_solve_time_s=float(result.oracle_solve_time_ms) / 1000.0,
        oracle_lookup_time_s=float(result.oracle_lookup_time_ms) / 1000.0,
        method_online_time_s=float(result.method_online_time_ms or result.runtime_ms) / 1000.0,
        closure_runtime_s=float(result.closure_runtime_ms) / 1000.0,
        memory_peak=float(_memory_proxy(world, result)),
        epsilon_ne_1=epsilon1,
        epsilon_ne_2=epsilon2,
        fractionality=float(result.fractionality),
        switches=int(result.switches),
        potential_violations=int(result.potential_violations),
        occupancy_error=float(result.occupancy_error),
        state_change=result.state_change,
        equilibrium_residual=result.equilibrium_residual,
        equilibrium_residual_id=result.equilibrium_residual_id,
        simulation_end_time_s=result.simulation_end_time_s,
        closure_messages=int(result.closure_messages),
        global_strong_closure=bool(result.global_strong_closure),
        largest_negative_delta=float(result.largest_negative_delta),
        median_potential_delta=float(result.median_potential_delta),
        p01_potential_delta=float(result.p01_potential_delta),
        observed_poa_ratio=observed_poa,
        price_of_integrality=price_integrality,
    )

def _useful_solution_metrics(
    world: SP0World,
    result: SP0MethodResult,
    *,
    epsilon: float,
) -> tuple[float, float, bool, float, float]:
    denominator = float((world.s_star + 1.0) * world.s_star + world.s_star)

    def useful(labels: np.ndarray) -> bool:
        labels = np.asarray(labels, dtype=int)
        if not assignment_valid(labels, world.n_loads) or int(np.sum(labels > 0)) != world.s_star:
            return False
        regret = max(assignment_objective(world, labels) - world.oracle_j, 0.0) / max(denominator, 1.0e-12)
        return bool(regret <= epsilon)

    trajectory = result.trajectory or {}
    times = np.asarray(trajectory.get("time_s", []), dtype=float)
    labels_by_time = np.asarray(trajectory.get("argmax_labels", []), dtype=int)
    continuous_messages = max(int(result.messages) - int(result.closure_messages), 0)
    total_iterations = max(int(result.iterations), 1)
    for index, labels in enumerate(labels_by_time):
        if useful(labels):
            time_value = float(times[index]) if index < times.size else float(index + 1)
            rounds = min(index + 1, total_iterations)
            message_value = int(math.ceil(continuous_messages * rounds / total_iterations))
            byte_ratio = float(result.bytes_sent / result.messages) if result.messages else 0.0
            return time_value, time_value, True, float(message_value), float(math.ceil(message_value * byte_ratio))

    end_time = result.simulation_end_time_s
    if end_time is None or not np.isfinite(float(end_time)):
        end_time = float(result.convergence_time) if np.isfinite(float(result.convergence_time)) else 0.0
    end_time = max(float(end_time), 0.0)
    if (result.rounding_id or "").upper() != "RAW" and useful(result.labels):
        return end_time, end_time, True, float(result.messages), float(result.bytes_sent)
    return math.nan, max(end_time, 1.0e-12), False, math.nan, math.nan

def theory_check_row(world: SP0World, result: SP0MethodResult, metrics: SP0Metrics) -> dict[str, Any]:
    x = result.continuous_x
    simplex_ok = True
    nonnegative_ok = True
    if x is not None:
        simplex_ok = bool(np.allclose(np.sum(x, axis=1), 1.0, atol=1.0e-6))
        nonnegative_ok = bool(np.min(x) >= -1.0e-9)
    raw_only = (result.rounding_id or "").upper() == "RAW"
    finite_values = [metrics.normalized_regret, metrics.runtime_wall_s]
    if not raw_only:
        finite_values.extend([metrics.coverage, metrics.social_cost])
    finite_metrics = all(np.isfinite(float(value)) for value in finite_values)
    matching_required = (result.rounding_id or "").upper() not in {"RAW", "ARG"}
    matching_ok = bool(metrics.matching_valid or not matching_required)
    passed = bool(simplex_ok and nonnegative_ok and matching_ok and finite_metrics)
    return {
        "world_hash": world.world_hash,
        "method": result.method_id,
        "dynamic_id": result.dynamic_id or "",
        "fitness_id": result.fitness_id or "",
        "rounding_id": result.rounding_id or "",
        "simplex_ok": simplex_ok,
        "nonnegative_ok": nonnegative_ok,
        "matching_required": matching_required,
        "matching_valid": metrics.matching_valid,
        "finite_metrics": finite_metrics,
        "continuous_converged": metrics.continuous_converged,
        "continuous_timeout": metrics.continuous_timeout,
        "closure_success": metrics.closure_success,
        "final_success": metrics.final_success,
        "passed": passed,
    }


def _active_costs(world: SP0World, labels: np.ndarray) -> np.ndarray:
    values: list[float] = []
    for robot_idx, label in enumerate(labels):
        if 1 <= int(label) <= world.n_loads:
            values.append(float(world.cost[robot_idx, int(label) - 1]))
    return np.asarray(values, dtype=float)


def _memory_proxy(world: SP0World, result: SP0MethodResult) -> float:
    x_size = 0 if result.continuous_x is None else result.continuous_x.size
    cells = world.cost.size + world.adjacency.size + x_size
    return float(cells * 8 / (1024.0 * 1024.0))


def _continuous_objective(world: SP0World, result: SP0MethodResult) -> float:
    if result.continuous_x is None:
        return world.oracle_j
    x = result.continuous_x
    assigned_mass = float(np.sum(x[:, 1:]))
    coverage = min(float(world.s_star), assigned_mass)
    cost = float(np.sum(world.cost * x[:, 1:]))
    return float((world.s_star + 1.0) * (world.s_star - coverage) + cost)
