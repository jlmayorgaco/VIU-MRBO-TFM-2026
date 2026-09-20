"""Unique metric implementations for SP1-GEO run/load records."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .certifier import certificate_records, physical_welfare
from .models import (
    ActionCatalog,
    AllocationResult,
    Assignment,
    ClosureStage,
    GeoWorld,
    RecoveryResult,
    WorldCertificate,
)


def evaluate_stage_metrics(
    world: GeoWorld,
    catalog: ActionCatalog,
    allocation: AllocationResult,
    assignment: Assignment,
    certificate: WorldCertificate,
    stage: ClosureStage,
    *,
    runtime_certifier_ms: float,
    recovery: RecoveryResult | None = None,
    certified_before_recovery: WorldCertificate | None = None,
    oracle_welfare: float = math.nan,
    oracle_upper_bound: float = math.nan,
    oracle_certified: bool = False,
) -> dict[str, Any]:
    selected = assignment.selected_actions()
    committed = certificate.committed_loads
    served = certificate.served_loads
    value = sum(
        world.loads[item.load_index].priority_value
        for item in certificate.load_certificates
        if item.feasible
    )
    committed_invalid = sum(
        int(item.committed and not item.feasible)
        for item in certificate.load_certificates
    )
    committed_residuals = np.array(
        [
            item.wrench_residual
            for item in certificate.load_certificates
            if item.committed and np.isfinite(item.wrench_residual)
        ],
        dtype=float,
    )
    committed_margins = np.array(
        [
            item.wrench_margin
            for item in certificate.load_certificates
            if item.committed and np.isfinite(item.wrench_margin)
        ],
        dtype=float,
    )
    battery_margins = np.array(
        [
            item.battery_minimum_margin_wh
            for item in certificate.load_certificates
            if item.committed and np.isfinite(item.battery_minimum_margin_wh)
        ],
        dtype=float,
    )
    excess = sum(
        max(item.capacity_kg - world.loads[item.load_index].min_capacity_kg, 0.0)
        for item in certificate.load_certificates
        if item.feasible
    )
    welfare = physical_welfare(world, catalog, assignment, certificate)
    gap_milp = (
        max(0.0, (oracle_welfare - welfare) / max(abs(oracle_welfare), 1e-12))
        if oracle_certified
        and np.isfinite(oracle_welfare)
        and np.isfinite(welfare)
        else math.nan
    )
    gap_bound = (
        max(0.0, (oracle_upper_bound - welfare) / max(abs(oracle_upper_bound), 1e-12))
        if np.isfinite(oracle_upper_bound)
        else math.nan
    )
    runtime_recovery = recovery.runtime_ms if recovery is not None else 0.0
    runtime_total = (
        allocation.runtime_negotiation_ms + runtime_certifier_ms + runtime_recovery
    )
    served_before = (
        certified_before_recovery.served_loads
        if certified_before_recovery is not None
        else served
    )
    diagnostic = allocation.diagnostics
    return {
        "world_physical_feasible": certificate.all_committed_feasible,
        "coalition_physical_feasible_rate": served / max(committed, 1),
        "served_load_rate": served / world.n_loads,
        "served_priority_value": float(value),
        "service_value_ratio_vs_oracle": (
            value / oracle_welfare
            if np.isfinite(oracle_welfare) and oracle_welfare > 0.0
            else math.nan
        ),
        "false_positive_given_committed": committed_invalid / max(committed, 1),
        "abstention_rate": 1.0 - committed / world.n_loads,
        "physical_welfare": welfare,
        "optimality_gap_vs_certified_milp": gap_milp,
        "gap_vs_best_bound": gap_bound,
        "travel_distance_total": (
            float(np.sum(catalog.travel_distance_m[selected]))
            if selected.size
            else 0.0
        ),
        "maximum_individual_distance": (
            float(np.max(catalog.travel_distance_m[selected]))
            if selected.size
            else 0.0
        ),
        "estimated_energy": (
            float(np.sum(catalog.mission_energy_wh[selected]))
            if selected.size
            else 0.0
        ),
        "excess_capacity": float(excess),
        "robots_used": int(selected.size),
        "wrench_residual": (
            float(np.mean(committed_residuals))
            if committed_residuals.size
            else math.nan
        ),
        "wrench_residual_max": (
            float(np.max(committed_residuals))
            if committed_residuals.size
            else math.nan
        ),
        "wrench_margin": (
            float(np.min(committed_margins))
            if committed_margins.size
            else math.nan
        ),
        "slot_coverage": (
            float(
                np.mean(
                    [
                        item.slot_coverage
                        for item in certificate.load_certificates
                        if item.committed
                    ]
                )
            )
            if committed
            else 0.0
        ),
        "duplicate_slots": certificate.duplicate_slots,
        "positive_negative_torque_coverage": (
            float(
                np.mean(
                    [
                        item.positive_negative_torque_coverage
                        for item in certificate.load_certificates
                        if item.committed
                    ]
                )
            )
            if committed
            else 0.0
        ),
        "battery_minimum_margin": (
            float(np.min(battery_margins)) if battery_margins.size else math.nan
        ),
        "raw_feasible": (
            certificate.all_committed_feasible if stage == "RAW" else None
        ),
        "certified_feasible": (
            certificate.all_committed_feasible if stage == "CERTIFIED" else None
        ),
        "recovered_feasible": (
            certificate.all_committed_feasible if stage == "RECOVERED" else None
        ),
        "recovery_steps": recovery.steps if recovery is not None else 0,
        "augmenting_path_length": (
            recovery.augmenting_path_length if recovery is not None else 0
        ),
        "robots_changed_by_recovery": (
            recovery.robots_changed if recovery is not None else 0
        ),
        "recovery_dependency": max(served - served_before, 0) / world.n_loads,
        "recovery_time_after_failure": (
            runtime_recovery if world.family == "F5_network_failure" else math.nan
        ),
        "recourse_robot_changes": (
            recovery.robots_changed
            if recovery is not None and world.family == "F5_network_failure"
            else math.nan
        ),
        "lost_served_value": 0.0,
        "affected_loads_reopened": (
            max(served - served_before, 0)
            if world.family == "F5_network_failure"
            else 0
        ),
        "unnecessary_coalitions_destroyed": 0,
        "runtime_total_ms": runtime_total,
        "runtime_negotiation_ms": allocation.runtime_negotiation_ms,
        "runtime_recovery_ms": runtime_recovery,
        "runtime_certifier_ms": runtime_certifier_ms,
        "messages": allocation.messages,
        "bytes": allocation.bytes_sent,
        "rounds": allocation.rounds,
        "iterations": allocation.iterations,
        "peak_memory_mb": float(diagnostic.get("peak_memory_mb", math.nan)),
        "blocking_unilateral_deviations": diagnostic.get(
            "blocking_unilateral_deviations", math.nan
        ),
        "blocking_swaps": diagnostic.get("blocking_swaps", math.nan),
        "local_core_distance": diagnostic.get("local_core_distance", math.nan),
        "cbba_conflicts_removed": diagnostic.get(
            "cbba_conflicts_removed", math.nan
        ),
        "cbba_winner_changes": diagnostic.get("cbba_winner_changes", math.nan),
        "kkt_residual": diagnostic.get("kkt_residual", math.nan),
        "primal_residual": diagnostic.get("primal_residual", math.nan),
        "dual_stationarity_residual": diagnostic.get(
            "dual_stationarity_residual", math.nan
        ),
        "complementarity_residual": diagnostic.get(
            "complementarity_residual", math.nan
        ),
        "price_consensus_residual": diagnostic.get(
            "price_consensus_residual", math.nan
        ),
        "aggregate_estimation_error": diagnostic.get(
            "aggregate_estimation_error", math.nan
        ),
        "potential_increment": diagnostic.get("potential_increment", math.nan),
        "final_entropy": diagnostic.get("final_entropy", math.nan),
        "oracle_certified_optimal": bool(oracle_certified),
        "oracle_upper_bound": oracle_upper_bound,
        "solver_status_code": diagnostic.get("solver_status_code", math.nan),
        "solver_objective_min": diagnostic.get("objective_min", math.nan),
        "solver_objective_max": diagnostic.get("objective_max", math.nan),
        "mip_gap": diagnostic.get("mip_gap", math.nan),
        "welfare_bound": diagnostic.get("welfare_upper_bound", math.nan),
    }


def load_metric_records(
    world: GeoWorld,
    certificate: WorldCertificate,
    *,
    base: dict[str, Any],
) -> list[dict[str, Any]]:
    records = []
    for payload in certificate_records(world, certificate):
        load = world.loads[int(payload["load_index"])]
        records.append(
            {
                **base,
                **payload,
                "shape": load.shape,
                "priority_value": load.priority_value,
                "min_capacity_kg": load.min_capacity_kg,
                "max_capacity_kg": load.max_capacity_kg,
                "required_wrench_fx_n": float(load.required_wrench[0]),
                "required_wrench_fy_n": float(load.required_wrench[1]),
                "required_wrench_tau_nm": float(load.required_wrench[2]),
            }
        )
    return records


__all__ = ["evaluate_stage_metrics", "load_metric_records"]
