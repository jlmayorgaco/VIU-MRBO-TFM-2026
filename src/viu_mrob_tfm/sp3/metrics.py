"""Metrics for SP3 role/slot wrench-feasibility experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp3.methods import (
    SP3Assignment,
    assignment_valid,
    communication_messages,
    complementarity_gain,
    energy_proxy_wh,
    scalar_feasible,
    score_assignment,
    slot_conflicts,
    slot_coverage_ratio,
    travel_distance_m,
    wrench_fit,
)
from viu_mrob_tfm.sp3.scenario import SP3Problem


@dataclass(frozen=True, slots=True)
class SP3Metrics:
    scalar_feasible_rate: float
    wrench_feasible_rate: float
    false_positive_rate: float
    false_positive_given_scalar_rate: float
    assigned_loads: int
    feasible_assigned_loads: int
    infeasible_assigned_loads: int
    feasible_available_loads: int
    relative_feasibility: float
    feasible_coverage: float
    precision_given_assigned: float
    fp_given_assigned: float
    wrench_residual_norm: float
    max_wrench_residual_norm: float
    wrench_residual_feasible_available: float
    max_wrench_residual_feasible_available: float
    wrench_margin: float
    torque_error_nm: float
    force_error_n: float
    slot_coverage_ratio: float
    complementarity_gain: float
    scalar_wrench_success_gap: float
    slot_conflict_count: int
    assignment_valid: bool
    travel_distance_m: float
    mean_assigned_travel_distance_m: float
    max_assigned_travel_distance_m: float
    estimated_arrival_time_s: float
    energy_proxy_wh: float
    communication_messages: int
    runtime_ms: float
    score_value: float
    oracle_score_value: float
    signed_score_delta_vs_oracle: float
    oracle_dominance_violation: bool
    optimality_gap_vs_wrench_oracle: float
    captured_reward: float
    oracle_reward: float
    assigned_robots: int
    idle_robots: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_diagnostics(problem: SP3Problem, assignment: SP3Assignment) -> list[dict[str, Any]]:
    """Return one diagnostic row per load."""

    rows: list[dict[str, Any]] = []
    for load_idx, load in enumerate(problem.world.loads):
        labels = np.asarray(assignment.labels, dtype=int)
        slot_labels = np.asarray(assignment.slot_labels, dtype=int)
        assigned = np.flatnonzero(labels == load_idx + 1)
        fit = wrench_fit(problem, assignment, load_idx)
        scalar_ok = scalar_feasible(problem, assignment, load_idx)
        wrench_ok = fit.residual_norm <= problem.wrench_tolerance
        assigned_load = bool(assigned.size > 0)
        feasible_assigned = bool(assigned_load and wrench_ok)
        infeasible_assigned = bool(assigned_load and not wrench_ok)
        false_positive = bool(scalar_ok and not wrench_ok)
        slots = [int(slot_labels[idx]) for idx in assigned]
        status = "WRENCH_OK" if wrench_ok else "SCALAR_ONLY" if false_positive else "UNDER"
        if not assignment_valid(problem, assignment):
            status = "INVALID"
        rows.append(
            {
                "load_id": load.identifier,
                "load_index": load_idx + 1,
                "mass_kg": float(load.mass_kg),
                "required_capacity_kg": float(load.min_capacity_kg),
                "required_robots": int(load.min_coalition_size),
                "wrench_fx_n": float(load.wrench.as_vector()[0]),
                "wrench_fy_n": float(load.wrench.as_vector()[1]),
                "wrench_tau_nm": float(load.wrench.as_vector()[2]),
                "assigned_robots": int(assigned.size),
                "assigned_load": assigned_load,
                "feasible_assigned": feasible_assigned,
                "infeasible_assigned": infeasible_assigned,
                "assigned_robot_ids": " ".join(problem.world.robots[idx].identifier for idx in assigned),
                "assigned_slot_labels": " ".join(str(value) for value in slots),
                "scalar_feasible": scalar_ok,
                "wrench_feasible": wrench_ok,
                "false_positive": false_positive,
                "wrench_residual_norm": float(fit.residual_norm),
                "wrench_margin": float(problem.wrench_tolerance - fit.residual_norm),
                "force_error_n": float(fit.force_error_n),
                "torque_error_nm": float(fit.torque_error_nm),
                "achieved_fx_n": float(fit.achieved_wrench[0]),
                "achieved_fy_n": float(fit.achieved_wrench[1]),
                "achieved_tau_nm": float(fit.achieved_wrench[2]),
                "slot_coverage_ratio": slot_coverage_ratio(problem, assignment, load_idx),
                "complementarity_gain": complementarity_gain(problem, assignment, load_idx),
                "reward": float(load.reward),
                "status": status,
            }
        )
    return rows


def evaluate_assignment(
    problem: SP3Problem,
    assignment: SP3Assignment,
    *,
    runtime_ms: float,
    oracle_assignment: SP3Assignment | None = None,
    centralized: bool = False,
) -> SP3Metrics:
    diagnostics = load_diagnostics(problem, assignment)
    load_count = max(len(problem.world.loads), 1)
    scalar_count = sum(1 for row in diagnostics if bool(row["scalar_feasible"]))
    wrench_count = sum(1 for row in diagnostics if bool(row["wrench_feasible"]))
    false_positive_count = sum(1 for row in diagnostics if bool(row["false_positive"]))
    assigned_load_count = sum(1 for row in diagnostics if bool(row["assigned_load"]))
    feasible_assigned_count = sum(1 for row in diagnostics if bool(row["feasible_assigned"]))
    infeasible_assigned_count = sum(1 for row in diagnostics if bool(row["infeasible_assigned"]))
    residuals = np.asarray([float(row["wrench_residual_norm"]) for row in diagnostics], dtype=float)
    margins = np.asarray([float(row["wrench_margin"]) for row in diagnostics], dtype=float)
    force_errors = np.asarray([float(row["force_error_n"]) for row in diagnostics], dtype=float)
    torque_errors = np.asarray([float(row["torque_error_nm"]) for row in diagnostics], dtype=float)
    slot_coverages = np.asarray([float(row["slot_coverage_ratio"]) for row in diagnostics], dtype=float)
    complementarity = np.asarray([float(row["complementarity_gain"]) for row in diagnostics], dtype=float)
    score = score_assignment(problem, assignment)
    oracle_score = score
    oracle_reward = float(sum(row["reward"] for row in diagnostics if bool(row["wrench_feasible"])))
    oracle_diag = diagnostics
    if oracle_assignment is not None:
        oracle_score = score_assignment(problem, oracle_assignment)
        oracle_diag = load_diagnostics(problem, oracle_assignment)
        oracle_reward = float(sum(row["reward"] for row in oracle_diag if bool(row["wrench_feasible"])))
    feasible_available_mask = [bool(row["wrench_feasible"]) for row in oracle_diag]
    feasible_available_count = sum(1 for value in feasible_available_mask if value)
    feasible_available_residuals = np.asarray(
        [float(diagnostics[idx]["wrench_residual_norm"]) for idx, feasible in enumerate(feasible_available_mask) if feasible],
        dtype=float,
    )
    reward = float(sum(row["reward"] for row in diagnostics if bool(row["wrench_feasible"])))
    if feasible_available_count:
        feasible_coverage = float(feasible_assigned_count / feasible_available_count)
    else:
        feasible_coverage = 1.0 if feasible_assigned_count == 0 else 0.0
    if assigned_load_count:
        precision_given_assigned = float(feasible_assigned_count / assigned_load_count)
    else:
        precision_given_assigned = 1.0 if feasible_available_count == 0 else 0.0
    fp_given_assigned = float(infeasible_assigned_count / assigned_load_count) if assigned_load_count else 0.0
    signed_delta = float(score - oracle_score)
    dominance_tolerance = max(1e-6, 1e-4 * abs(oracle_score))
    physical_score_scale = 18.0 * sum(float(load.reward) for load in problem.world.loads) + 2.5 * len(problem.world.loads)
    gap_denominator = max(abs(oracle_score), physical_score_scale, 1.0)
    gap = max(0.0, float((oracle_score - score) / gap_denominator))
    travel_stats = _assignment_travel_stats(problem, assignment)
    labels = np.asarray(assignment.labels, dtype=int)
    return SP3Metrics(
        scalar_feasible_rate=float(scalar_count / load_count),
        wrench_feasible_rate=float(wrench_count / load_count),
        false_positive_rate=float(false_positive_count / load_count),
        false_positive_given_scalar_rate=float(false_positive_count / max(scalar_count, 1)),
        assigned_loads=assigned_load_count,
        feasible_assigned_loads=feasible_assigned_count,
        infeasible_assigned_loads=infeasible_assigned_count,
        feasible_available_loads=feasible_available_count,
        relative_feasibility=feasible_coverage,
        feasible_coverage=feasible_coverage,
        precision_given_assigned=precision_given_assigned,
        fp_given_assigned=fp_given_assigned,
        wrench_residual_norm=float(np.mean(residuals)) if residuals.size else 0.0,
        max_wrench_residual_norm=float(np.max(residuals)) if residuals.size else 0.0,
        wrench_residual_feasible_available=float(np.mean(feasible_available_residuals)) if feasible_available_residuals.size else 0.0,
        max_wrench_residual_feasible_available=float(np.max(feasible_available_residuals)) if feasible_available_residuals.size else 0.0,
        wrench_margin=float(np.mean(margins)) if margins.size else 0.0,
        torque_error_nm=float(np.mean(torque_errors)) if torque_errors.size else 0.0,
        force_error_n=float(np.mean(force_errors)) if force_errors.size else 0.0,
        slot_coverage_ratio=float(np.mean(slot_coverages)) if slot_coverages.size else 0.0,
        complementarity_gain=float(np.mean(complementarity)) if complementarity.size else 0.0,
        scalar_wrench_success_gap=float((scalar_count - wrench_count) / load_count),
        slot_conflict_count=len(slot_conflicts(problem, assignment)),
        assignment_valid=assignment_valid(problem, assignment),
        travel_distance_m=travel_stats["travel_distance_m"],
        mean_assigned_travel_distance_m=travel_stats["mean_assigned_travel_distance_m"],
        max_assigned_travel_distance_m=travel_stats["max_assigned_travel_distance_m"],
        estimated_arrival_time_s=travel_stats["estimated_arrival_time_s"],
        energy_proxy_wh=energy_proxy_wh(problem, assignment),
        communication_messages=communication_messages(problem, assignment, centralized=centralized),
        runtime_ms=float(runtime_ms),
        score_value=score,
        oracle_score_value=oracle_score,
        signed_score_delta_vs_oracle=signed_delta,
        oracle_dominance_violation=bool(signed_delta > dominance_tolerance),
        optimality_gap_vs_wrench_oracle=gap,
        captured_reward=reward,
        oracle_reward=oracle_reward,
        assigned_robots=int(np.sum(labels > 0)),
        idle_robots=int(np.sum(labels == 0)),
    )


def _assignment_travel_stats(problem: SP3Problem, assignment: SP3Assignment) -> dict[str, float]:
    distances = []
    arrivals = []
    for robot_idx, label in enumerate(np.asarray(assignment.labels, dtype=int)):
        if label <= 0:
            continue
        load_idx = int(label) - 1
        slot_idx = int(assignment.slot_labels[robot_idx]) - 1
        if not (0 <= load_idx < len(problem.world.loads) and 0 <= slot_idx < len(problem.load_slots[load_idx])):
            continue
        robot = problem.world.robots[robot_idx]
        load = problem.world.loads[load_idx]
        slot = problem.load_slots[load_idx][slot_idx]
        distance = float(np.linalg.norm(robot.position - (load.pickup + slot.offset_xy)))
        distances.append(distance)
        arrivals.append(distance / max(float(robot.spec.max_speed), 1e-9))
    if not distances:
        return {
            "travel_distance_m": 0.0,
            "mean_assigned_travel_distance_m": 0.0,
            "max_assigned_travel_distance_m": 0.0,
            "estimated_arrival_time_s": 0.0,
        }
    values = np.asarray(distances, dtype=float)
    return {
        "travel_distance_m": travel_distance_m(problem, assignment),
        "mean_assigned_travel_distance_m": float(np.mean(values)),
        "max_assigned_travel_distance_m": float(np.max(values)),
        "estimated_arrival_time_s": float(np.max(arrivals)),
    }
