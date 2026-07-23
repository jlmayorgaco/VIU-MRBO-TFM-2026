"""Campaign orchestration for SP1_DRD_VS_CBBA_SIMPLE_v1."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import yaml

from viu_mrob_tfm.sp1_canonical.validation.drd_cbba_simple import (
    CBBAResult,
    DRDResult,
    OracleResult,
    RecoveryMetrics,
    SimpleGraph,
    SimpleWorld,
    assignment_from_drd,
    continuous_metrics,
    environment_record,
    integer_metrics,
    make_graph,
    make_manual_world,
    make_simple_world,
    recover_assignment,
    run_cbba,
    run_drd,
    solve_scalar_lp,
    solve_scalar_milp,
    stable_hash,
    validate_message_rows,
)
from viu_mrob_tfm.sp1_canonical.validation.statistics import (
    bootstrap_interval,
    holm_adjust,
    paired_wilcoxon,
    wilson_interval,
)


STAGES = ("calibrate", "preview", "full", "analyze", "audit")
PRIMARY_VARIANTS = (
    ("DRD-simple", "raw"),
    ("DRD-simple", "recovered"),
    ("CBBA-1-Capacity", "raw"),
    ("CBBA-1-Capacity", "recovered"),
)


def load_config(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _seed_range(spec: Mapping[str, Any]) -> range:
    if "stop" in spec:
        return range(int(spec["start"]), int(spec["stop"]) + 1)
    return range(int(spec["start"]), int(spec["start"]) + int(spec["count"]))


def calibration_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for n, k in config["calibration"]["configurations"]:
        for seed in _seed_range(config["calibration"]["seeds"]):
            for candidate in config["calibration"]["candidates"]:
                tasks.append(
                    {
                        "experiment": "calibration",
                        "scenario_id": f"cal-n{n}-k{k}-s{seed}",
                        "n": int(n),
                        "k": int(k),
                        "seed": int(seed),
                        "capacity_regime": "medium",
                        "topology": "rdisk_degree_8",
                        "utilization_target": None,
                        "candidate": dict(candidate),
                        "include_oracles": False,
                        "include_recovery": False,
                    }
                )
    return tasks


def preview_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    preview = config["preview"]
    for n in preview["n_values"]:
        k = max(2, int(math.ceil(int(n) / 5)))
        for seed in preview["seeds"]:
            tasks.append(
                {
                    "experiment": "preview",
                    "scenario_id": f"preview-n{n}-k{k}-s{seed}",
                    "n": int(n),
                    "k": k,
                    "seed": int(seed),
                    "capacity_regime": str(preview["capacity_regime"]),
                    "topology": str(preview["topology"]),
                    "utilization_target": None,
                    "include_oracles": True,
                    "include_recovery": True,
                }
            )
    return tasks


def evaluation_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    evaluation = config["evaluation"]
    tasks: list[dict[str, Any]] = []
    for case_index in range(1, int(evaluation["e1"]["deterministic_cases"]) + 1):
        tasks.append(
            {
                "experiment": "e1",
                "scenario_id": f"E1-{case_index:02d}",
                "deterministic_case": case_index,
                "n": None,
                "k": None,
                "seed": case_index,
                "capacity_regime": "deterministic",
                "topology": "complete",
                "utilization_target": None,
                "include_oracles": True,
                "include_recovery": True,
            }
        )
    e2 = evaluation["e2"]
    for n in e2["n_values"]:
        k = max(2, int(math.ceil(int(n) / 5)))
        for offset in range(int(e2["seed_counts"][int(n)])):
            seed = int(e2["seed_start"]) + 1000 * int(n) + offset
            tasks.append(
                _task("e2", n, k, seed, e2["capacity_regime"], e2["topology"])
            )
    e3 = evaluation["e3"]
    for k in e3["k_values"]:
        for offset in range(int(e3["seeds"]["count"])):
            seed = int(e3["seeds"]["start"]) + 1000 * int(k) + offset
            tasks.append(
                _task("e3", e3["n"], k, seed, e3["capacity_regime"], e3["topology"])
            )
    e4 = evaluation["e4"]
    for configuration in e4["configurations"]:
        for regime_index, regime in enumerate(e4["regimes"]):
            for offset in range(int(configuration["seeds"])):
                seed = (
                    int(e4["seed_start"])
                    + 100000 * int(configuration["n"])
                    + 1000 * regime_index
                    + offset
                )
                tasks.append(
                    _task(
                        "e4",
                        configuration["n"],
                        configuration["k"],
                        seed,
                        regime,
                        e4["topology"],
                    )
                )
    e5 = evaluation["e5"]
    for n, k in e5["configurations"]:
        for topology_index, topology in enumerate(e5["topologies"]):
            for offset in range(int(e5["seeds"]["count"])):
                seed = (
                    int(e5["seeds"]["start"])
                    + 100000 * int(n)
                    + 1000 * topology_index
                    + offset
                )
                tasks.append(
                    _task("e5", n, k, seed, e5["capacity_regime"], topology)
                )
    e6 = evaluation["e6"]
    for n, k in e6["configurations"]:
        for target_index, target in enumerate(e6["utilization_targets"]):
            for offset in range(int(e6["seeds"]["count"])):
                seed = (
                    int(e6["seeds"]["start"])
                    + 100000 * int(n)
                    + 1000 * target_index
                    + offset
                )
                tasks.append(
                    _task(
                        "e6",
                        n,
                        k,
                        seed,
                        e6["capacity_regime"],
                        e6["topology"],
                        utilization_target=float(target),
                    )
                )
    return tasks


def _task(
    experiment: str,
    n: int,
    k: int,
    seed: int,
    capacity_regime: str,
    topology: str,
    *,
    utilization_target: float | None = None,
) -> dict[str, Any]:
    target_label = "" if utilization_target is None else f"-u{utilization_target:.2f}"
    return {
        "experiment": experiment,
        "scenario_id": (
            f"{experiment}-n{n}-k{k}-s{seed}-{capacity_regime}-{topology}{target_label}"
        ),
        "n": int(n),
        "k": int(k),
        "seed": int(seed),
        "capacity_regime": str(capacity_regime),
        "topology": str(topology),
        "utilization_target": utilization_target,
        "include_oracles": True,
        "include_recovery": True,
    }


def deterministic_case_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"case_id": "E1-01", "name": "one_robot_per_load", "expectation": "nearest one-to-one allocation is feasible"},
            {"case_id": "E1-02", "name": "one_load_needs_two", "expectation": "at least two unit robots are recruited"},
            {"case_id": "E1-03", "name": "large_robot_near", "expectation": "near high-capacity robot can cover alone"},
            {"case_id": "E1-04", "name": "large_far_vs_two_small_near", "expectation": "distance optimum prefers two nearby robots"},
            {"case_id": "E1-05", "name": "two_loads_compete_for_strong", "expectation": "strong robot cannot be double assigned"},
            {"case_id": "E1-06", "name": "global_robot_excess", "expectation": "some robots remain idle"},
            {"case_id": "E1-07", "name": "utilization_near_90", "expectation": "low-slack feasible witness exists"},
            {"case_id": "E1-08", "name": "almost_homogeneous", "expectation": "small capacity perturbations preserve feasibility"},
            {"case_id": "E1-09", "name": "high_heterogeneity", "expectation": "coalitions exploit unequal capacities"},
            {"case_id": "E1-10", "name": "exact_tie", "expectation": "robot and load indices break ties deterministically"},
        ]
    )


def deterministic_world(case_index: int) -> SimpleWorld:
    """Return one of ten fixed, reasoned scalar-capacity cases."""

    if case_index == 1:
        return make_manual_world(
            case_id="E1-01",
            positions=[[0.1, 0.1], [0.5, 0.5], [0.9, 0.9]],
            loads=[[0.1, 0.1], [0.5, 0.5], [0.9, 0.9]],
            capacities=[1.0, 1.0, 1.0],
            masses=[0.9, 0.9, 0.9],
            witness=[0, 1, 2],
        )
    if case_index == 2:
        return make_manual_world(
            case_id="E1-02",
            positions=[[0.1, 0.0], [0.2, 0.0], [0.9, 0.0]],
            loads=[[0.0, 0.0]],
            capacities=[1.0, 1.0, 1.0],
            masses=[1.8],
            witness=[0, 0, -1],
        )
    if case_index == 3:
        return make_manual_world(
            case_id="E1-03",
            positions=[[0.05, 0.0], [0.3, 0.0], [0.4, 0.0]],
            loads=[[0.0, 0.0]],
            capacities=[3.0, 1.0, 1.0],
            masses=[2.5],
            witness=[0, -1, -1],
        )
    if case_index == 4:
        return make_manual_world(
            case_id="E1-04",
            positions=[[0.9, 0.0], [0.05, 0.0], [0.06, 0.0]],
            loads=[[0.0, 0.0]],
            capacities=[3.2, 1.6, 1.6],
            masses=[3.0],
            witness=[-1, 0, 0],
        )
    if case_index == 5:
        return make_manual_world(
            case_id="E1-05",
            positions=[[0.5, 0.5], [0.05, 0.0], [0.95, 1.0], [0.9, 0.9]],
            loads=[[0.0, 0.0], [1.0, 1.0]],
            capacities=[3.0, 1.5, 1.5, 1.5],
            masses=[2.7, 2.7],
            witness=[0, -1, 1, 1],
        )
    if case_index == 6:
        return make_manual_world(
            case_id="E1-06",
            positions=np.linspace(0.05, 0.95, 10)[:, None] * np.asarray([[1.0, 1.0]]),
            loads=[[0.2, 0.2], [0.8, 0.8]],
            capacities=np.ones(10),
            masses=[2.0, 2.0],
            witness=[0, 0, -1, -1, -1, -1, -1, -1, 1, 1],
        )
    if case_index == 7:
        return make_manual_world(
            case_id="E1-07",
            positions=np.asarray([[i / 9, (i % 3) / 3] for i in range(10)]),
            loads=[[0.2, 0.2], [0.8, 0.2]],
            capacities=np.ones(10),
            masses=[4.5, 4.5],
            witness=[0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        )
    if case_index == 8:
        capacities = np.asarray([0.99, 1.00, 1.01, 1.02, 0.98, 1.00])
        return make_manual_world(
            case_id="E1-08",
            positions=[[0.1, 0.1], [0.2, 0.2], [0.3, 0.3], [0.7, 0.7], [0.8, 0.8], [0.9, 0.9]],
            loads=[[0.15, 0.15], [0.85, 0.85]],
            capacities=capacities,
            masses=[2.7, 2.7],
            witness=[0, 0, 0, 1, 1, 1],
        )
    if case_index == 9:
        return make_manual_world(
            case_id="E1-09",
            positions=[[0.1, 0.1], [0.2, 0.2], [0.4, 0.4], [0.6, 0.6], [0.8, 0.8], [0.9, 0.9]],
            loads=[[0.1, 0.1], [0.9, 0.9]],
            capacities=[0.5, 0.7, 1.1, 1.4, 2.8, 3.8],
            masses=[3.0, 5.0],
            witness=[0, 0, 0, 0, 1, 1],
        )
    if case_index == 10:
        return make_manual_world(
            case_id="E1-10",
            positions=[[0.5, 0.0], [0.5, 1.0], [0.5, 0.5], [0.5, 0.5]],
            loads=[[0.0, 0.5], [1.0, 0.5]],
            capacities=[1.0, 1.0, 1.0, 1.0],
            masses=[1.8, 1.8],
            witness=[0, 1, 0, 1],
        )
    raise ValueError(f"unknown deterministic case: {case_index}")


def _world_for_task(task: Mapping[str, Any], config: Mapping[str, Any]) -> SimpleWorld:
    if task.get("deterministic_case") is not None:
        return deterministic_world(int(task["deterministic_case"]))
    return make_simple_world(
        int(task["n"]),
        int(task["k"]),
        int(task["seed"]),
        config,
        capacity_regime=str(task["capacity_regime"]),
        utilization_target=task.get("utilization_target"),
        world_id=str(task["scenario_id"]),
    )


def _graph_metadata(graph: SimpleGraph) -> dict[str, Any]:
    return {
        "graph_name": graph.name,
        "graph_hash": graph.graph_hash,
        "graph_edges": graph.edges,
        "degree_min": graph.degree_min,
        "degree_max": graph.degree_max,
        "degree_mean": graph.degree_mean,
        "graph_diameter": graph.diameter,
        "lambda_2": graph.lambda_2,
        "lambda_max": graph.lambda_max,
        "spectral_condition": graph.spectral_condition,
        "graph_radius": graph.radius,
    }


def _world_metadata(
    task: Mapping[str, Any],
    world: SimpleWorld,
    graph: SimpleGraph,
    parameters: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "experiment": task["experiment"],
        "scenario_id": task["scenario_id"],
        "world_id": world.world_id,
        "seed": world.seed,
        "n": world.n_robots,
        "k": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization_target": world.utilization_target,
        "utilization": world.utilization,
        "world_hash": world.world_hash,
        "positions_hash": world.positions_hash,
        "capacities_hash": world.capacities_hash,
        "loads_hash": world.loads_hash,
        "candidate_id": parameters.get("candidate_id", "selected"),
        "rho": float(parameters["rho"]),
        "alpha": float(parameters["alpha"]),
        "tau": float(parameters["tau"]),
        "bid_minimum": float(parameters.get("bid_minimum", 0.0)),
        **_graph_metadata(graph),
    }


def _algorithm_fields(result: DRDResult | CBBAResult) -> dict[str, Any]:
    common = {
        "converged": result.converged,
        "censored": result.censored,
        "censoring_reason": result.censoring_reason,
        "logical_rounds": result.logical_rounds,
        "first_feasible_round": result.first_feasible_round,
        "persistent_convergence_round": result.persistent_convergence_round,
        "wall_time_s": result.wall_time_s,
        "cpu_time_s": result.cpu_time_s,
        "peak_memory_mb": result.peak_memory_mb,
        "packets_total": result.packets_total,
        "scalar_transmissions_total": result.scalar_transmissions_total,
        "payload_bytes_total": result.payload_bytes_total,
        "bytes_to_first_feasible": result.bytes_to_first_feasible,
        "bytes_to_convergence": result.bytes_to_convergence,
    }
    if isinstance(result, DRDResult):
        common.update(
            {
                "first_gate_round": result.first_gate_round,
                "state_residual": result.terminal_state_residual,
                "consensus_residual": result.terminal_consensus_residual,
                "capacity_residual": result.terminal_capacity_residual,
                "state_slope": result.terminal_state_slope,
                "consensus_slope": result.terminal_consensus_slope,
                "capacity_slope": result.terminal_capacity_slope,
                "payoff_evaluations": result.payoff_evaluations,
                "bid_evaluations": 0,
                "consensus_updates": result.consensus_updates,
                "simplex_violation": result.simplex_violation,
                "nonnegativity_violation": result.nonnegativity_violation,
                "finite_state": result.finite_state,
                "tracker_sum_error": result.tracker_sum_error,
                "duplicate_assignment_count": 0,
                "proposal_epochs": 0,
                "accepted_bids": 0,
            }
        )
    else:
        common.update(
            {
                "first_gate_round": None,
                "state_residual": math.nan,
                "consensus_residual": math.nan,
                "capacity_residual": math.nan,
                "state_slope": math.nan,
                "consensus_slope": math.nan,
                "capacity_slope": math.nan,
                "payoff_evaluations": 0,
                "bid_evaluations": result.bid_evaluations,
                "consensus_updates": 0,
                "simplex_violation": 0.0,
                "nonnegativity_violation": 0.0,
                "finite_state": True,
                "tracker_sum_error": 0.0,
                "duplicate_assignment_count": result.duplicate_assignment_count,
                "proposal_epochs": result.proposal_epochs,
                "accepted_bids": result.accepted_bids,
            }
        )
    return common


def _variant_row(
    metadata: Mapping[str, Any],
    method: str,
    variant: str,
    assignment: np.ndarray,
    world: SimpleWorld,
    algorithm: DRDResult | CBBAResult,
    recovery: Any,
    continuous: Mapping[str, Any] | None,
    lp: OracleResult | None,
    milp_result: OracleResult | None,
) -> dict[str, Any]:
    metrics = integer_metrics(world, assignment)
    row = {
        **metadata,
        "is_primary": True,
        "method": method,
        "variant": variant,
        "method_variant": f"{method}/{variant}",
        **metrics,
        **_algorithm_fields(algorithm),
        "recovery_executed": recovery.executed if variant == "recovered" else False,
        "recovery_success": recovery.success if variant == "recovered" else False,
        "recovery_runtime_s": recovery.runtime_s if variant == "recovered" else 0.0,
        "recovery_chain_length_max": recovery.chain_length_max if variant == "recovered" else 0,
        "recovery_nodes_expanded": recovery.nodes_expanded if variant == "recovered" else 0,
        "robots_reassigned": recovery.robots_reassigned if variant == "recovered" else 0,
        "objective_before_recovery": recovery.objective_before,
        "objective_after_recovery": recovery.objective_after,
        "recovery_failure_reason": recovery.failure_reason if variant == "recovered" else "",
        "assignment": json.dumps(np.asarray(assignment, dtype=int).tolist()),
        "lp_status": None if lp is None else lp.status,
        "lp_objective": math.nan if lp is None else lp.objective,
        "milp_status": None if milp_result is None else milp_result.status,
        "milp_optimal": False if milp_result is None else milp_result.optimal,
        "milp_objective": math.nan if milp_result is None else milp_result.objective,
        "milp_mip_gap": math.nan if milp_result is None else milp_result.mip_gap,
    }
    if continuous:
        row.update(continuous)
    else:
        row.update(
            {
                "objective_distance_continuous": math.nan,
                "objective_penalized": math.nan,
                "objective_regularized": math.nan,
                "entropy": math.nan,
                "total_deficit_continuous": math.nan,
                "total_relative_deficit_continuous": math.nan,
                "total_excess_capacity_continuous": math.nan,
            }
        )
    row["lp_gap"] = (
        (row["distance_total"] - lp.objective) / max(abs(lp.objective), 1e-12)
        if row["feasible"] and lp is not None and lp.optimal
        else math.nan
    )
    row["milp_gap"] = (
        (row["distance_total"] - milp_result.objective)
        / max(abs(milp_result.objective), 1e-12)
        if row["feasible"] and milp_result is not None and milp_result.optimal
        else math.nan
    )
    row["wall_time_total_s"] = row["wall_time_s"] + row["recovery_runtime_s"]
    row["cpu_time_total_s"] = row["cpu_time_s"]
    row["bytes_per_robot"] = row["payload_bytes_total"] / world.n_robots
    row["bytes_per_edge"] = row["payload_bytes_total"] / max(1, metadata["graph_edges"])
    return row


def _oracle_row(
    metadata: Mapping[str, Any],
    oracle: OracleResult,
    world: SimpleWorld,
) -> dict[str, Any]:
    assignment = oracle.assignment
    metrics = (
        integer_metrics(world, assignment)
        if assignment is not None
        else {
            "feasible": oracle.feasible,
            "deficit_total": math.nan,
            "deficit_max": math.nan,
            "distance_total": oracle.objective,
            "distance_mean_per_assigned_robot": math.nan,
            "distance_max": math.nan,
            "distance_per_load": "[]",
            "worst_load_distance": math.nan,
            "excess_total": math.nan,
            "excess_mean": math.nan,
            "excess_max": math.nan,
            "excess_ratio": math.nan,
            "robots_used": math.nan,
            "idle_robots": math.nan,
            "assignment_hash": "",
        }
    )
    return {
        **metadata,
        "is_primary": False,
        "method": oracle.kind,
        "variant": "oracle",
        "method_variant": f"{oracle.kind}/oracle",
        **metrics,
        "converged": oracle.optimal,
        "censored": oracle.status in {"timeout", "feasible_not_proven_optimal"},
        "censoring_reason": oracle.status if not oracle.optimal else "",
        "logical_rounds": 0,
        "wall_time_s": oracle.wall_time_s,
        "wall_time_total_s": oracle.wall_time_s,
        "cpu_time_s": oracle.cpu_time_s,
        "cpu_time_total_s": oracle.cpu_time_s,
        "payload_bytes_total": 0,
        "packets_total": 0,
        "scalar_transmissions_total": 0,
        "assignment": (
            "[]" if assignment is None else json.dumps(assignment.astype(int).tolist())
        ),
        "oracle_status": oracle.status,
        "oracle_lower_bound": oracle.lower_bound,
        "oracle_upper_bound": oracle.upper_bound,
        "oracle_mip_gap": oracle.mip_gap,
        "oracle_message": oracle.message,
    }


def run_scenario(
    config: Mapping[str, Any],
    task: Mapping[str, Any],
    parameters: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    world = _world_for_task(task, config)
    graph = make_graph(world, str(task["topology"]))
    metadata = _world_metadata(task, world, graph, parameters)
    lp: OracleResult | None = None
    milp_result: OracleResult | None = None
    if task.get("include_oracles", True):
        lp = solve_scalar_lp(world)
        if world.n_robots <= int(config["oracles"]["milp_max_n"]):
            milp_result = solve_scalar_milp(
                world, time_limit_s=float(config["oracles"]["milp_timeout_s"])
            )

    drd = run_drd(world, graph, config, parameters)
    cbba = run_cbba(world, graph, config, parameters)
    drd_raw = assignment_from_drd(drd.x)
    cbba_raw = cbba.assignment
    if task.get("include_recovery", True):
        drd_recovery = recover_assignment(world, drd_raw, config)
        cbba_recovery = recover_assignment(world, cbba_raw, config)
    else:
        drd_distance = integer_metrics(world, drd_raw)["distance_total"]
        cbba_distance = integer_metrics(world, cbba_raw)["distance_total"]
        drd_recovery = RecoveryMetrics(
            assignment=drd_raw.copy(),
            executed=False,
            success=bool(integer_metrics(world, drd_raw)["feasible"]),
            runtime_s=0.0,
            chain_length_max=0,
            nodes_expanded=0,
            robots_reassigned=0,
            objective_before=float(drd_distance),
            objective_after=float(drd_distance),
            failure_reason="not_requested",
        )
        cbba_recovery = RecoveryMetrics(
            assignment=cbba_raw.copy(),
            executed=False,
            success=bool(integer_metrics(world, cbba_raw)["feasible"]),
            runtime_s=0.0,
            chain_length_max=0,
            nodes_expanded=0,
            robots_reassigned=0,
            objective_before=float(cbba_distance),
            objective_after=float(cbba_distance),
            failure_reason="not_requested",
        )
    continuous = continuous_metrics(
        world,
        drd.x,
        rho=float(parameters["rho"]),
        tau=float(parameters["tau"]),
    )
    runs = [
        _variant_row(metadata, "DRD-simple", "raw", drd_raw, world, drd, drd_recovery, continuous, lp, milp_result),
        _variant_row(metadata, "DRD-simple", "recovered", drd_recovery.assignment, world, drd, drd_recovery, continuous, lp, milp_result),
        _variant_row(metadata, "CBBA-1-Capacity", "raw", cbba_raw, world, cbba, cbba_recovery, None, lp, milp_result),
        _variant_row(metadata, "CBBA-1-Capacity", "recovered", cbba_recovery.assignment, world, cbba, cbba_recovery, None, lp, milp_result),
    ]
    if lp is not None:
        runs.append(_oracle_row(metadata, lp, world))
    if milp_result is not None:
        runs.append(_oracle_row(metadata, milp_result, world))
    messages = []
    for row in list(drd.messages) + list(cbba.messages):
        messages.append({**metadata, **row})
    traces = []
    for row in list(drd.traces) + list(cbba.traces):
        traces.append({**metadata, **row})
    world_row = {
        **metadata,
        "planted_witness_feasible": integer_metrics(world, world.witness)["feasible"],
        "robot_positions": json.dumps(world.robot_positions.tolist()),
        "load_positions": json.dumps(world.load_positions.tolist()),
        "capacities": json.dumps(world.capacities.tolist()),
        "masses": json.dumps(world.masses.tolist()),
        "witness": json.dumps(world.witness.tolist()),
    }
    return {"runs": runs, "messages": messages, "traces": traces, "worlds": [world_row]}


def _checkpoint_key(task: Mapping[str, Any]) -> str:
    return stable_hash(task)[:24]


def _worker(
    config: Mapping[str, Any],
    task: Mapping[str, Any],
    parameters: Mapping[str, Any],
    checkpoint_dir: str,
    resume: bool,
) -> dict[str, Any]:
    directory = Path(checkpoint_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{_checkpoint_key(task)}.json"
    if resume and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    result = run_scenario(config, task, parameters)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, allow_nan=True), encoding="utf-8"
    )
    temporary.replace(path)
    return result


def execute_tasks(
    config: Mapping[str, Any],
    tasks: list[dict[str, Any]],
    parameters: Mapping[str, Any],
    output_dir: str | Path,
    *,
    resume: bool,
) -> dict[str, pd.DataFrame]:
    output = Path(output_dir)
    checkpoints = output / "_checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    workers = int(config["parallel_workers"])
    collections: dict[str, list[dict[str, Any]]] = {
        "runs": [],
        "messages": [],
        "traces": [],
        "worlds": [],
    }
    completed = 0
    if workers == 1:
        iterator: Iterable[dict[str, Any]] = (
            _worker(config, task, task.get("candidate", parameters), str(checkpoints), resume)
            for task in tasks
        )
        for result in iterator:
            for key in collections:
                collections[key].extend(result[key])
            completed += 1
            print(f"[{completed}/{len(tasks)}] task complete", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    _worker,
                    config,
                    task,
                    task.get("candidate", parameters),
                    str(checkpoints),
                    resume,
                ): task
                for task in tasks
            }
            for future in as_completed(futures):
                result = future.result()
                for key in collections:
                    collections[key].extend(result[key])
                completed += 1
                if completed == 1 or completed % 10 == 0 or completed == len(tasks):
                    print(f"[{completed}/{len(tasks)}] tasks complete", flush=True)
    return {key: pd.DataFrame(rows) for key, rows in collections.items()}


def select_calibration_parameters(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = runs[(runs.is_primary.astype(bool)) & (runs.variant == "raw")].copy()
    summaries: list[dict[str, Any]] = []
    for candidate_id, group in raw.groupby("candidate_id", sort=True):
        method_rates = group.groupby("method").feasible.mean()
        converged_rates = group.groupby("method").converged.mean()
        feasible_distance = group.loc[group.feasible.astype(bool), "distance_total"]
        summaries.append(
            {
                "candidate_id": candidate_id,
                "raw_feasibility_min": float(method_rates.min()),
                "raw_feasibility_mean": float(group.feasible.mean()),
                "raw_distance_mean": (
                    float(feasible_distance.mean()) if len(feasible_distance) else math.inf
                ),
                "wall_time_mean_s": float(group.wall_time_s.mean()),
                "payload_bytes_mean": float(group.payload_bytes_total.mean()),
                "stability_min": float(converged_rates.min()),
                "n_rows": int(len(group)),
            }
        )
    summary = pd.DataFrame(summaries)
    summary = summary.sort_values(
        [
            "raw_feasibility_min",
            "raw_distance_mean",
            "wall_time_mean_s",
            "payload_bytes_mean",
            "stability_min",
            "candidate_id",
        ],
        ascending=[False, True, True, True, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    selected_id = str(summary.iloc[0].candidate_id)
    selected = next(
        dict(candidate)
        for candidate in config["calibration"]["candidates"]
        if candidate["candidate_id"] == selected_id
    )
    selected["selection_rule"] = list(config["calibration"]["objective_order"])
    selected["calibration_rows"] = int(len(raw))
    selected["selected_utc"] = datetime.now(timezone.utc).isoformat()
    return summary, selected


def _write_frames(output: Path, frames: Mapping[str, pd.DataFrame]) -> None:
    frames["runs"].to_csv(output / "all_runs.csv", index=False)
    frames["messages"].to_csv(output / "all_messages.csv", index=False)
    frames["traces"].to_csv(output / "all_traces.csv", index=False)
    frames["worlds"].drop_duplicates("scenario_id").to_csv(
        output / "worlds.csv", index=False
    )
    validation = pd.DataFrame(
        validate_message_rows(frames["messages"].to_dict(orient="records"))
    )
    validation.to_csv(output / "message_accounting_validation.csv", index=False)
    censoring = frames["runs"].loc[
        frames["runs"].get("censored", False).fillna(False).astype(bool),
        [
            "experiment",
            "scenario_id",
            "method",
            "variant",
            "censoring_reason",
            "logical_rounds",
            "wall_time_s",
            "payload_bytes_total",
        ],
    ]
    censoring.to_csv(output / "censoring.csv", index=False)
    pd.DataFrame(
        columns=["scenario_id", "stage", "reason", "detail"]
    ).to_csv(output / "exclusions.csv", index=False)


def _selected_parameters(
    config_path: Path,
    config: Mapping[str, Any],
    path: str | Path | None,
) -> dict[str, Any]:
    if path is not None:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    preview_output = config_path.parent.parent.parent / config["output_dirs"]["preview"]
    candidate_path = preview_output / "selected_parameters.yaml"
    if candidate_path.exists():
        return yaml.safe_load(candidate_path.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "selected_parameters.yaml not found; run --stage calibrate first or pass --selected-parameters"
    )


def execute(
    config_path: str | Path,
    *,
    stage: str,
    selected_parameters_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    config_path = Path(config_path).resolve()
    config = load_config(config_path)
    repository = config_path.parents[2]
    default_key = "preview" if stage in {"calibrate", "preview"} else "full"
    output = (
        Path(output_dir).resolve()
        if output_dir is not None
        else (repository / config["output_dirs"][default_key]).resolve()
    )
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    cpu_start = time.process_time()
    git_start = _git_status(repository)
    shutil.copy2(config_path, output / "config_snapshot.yaml")
    preflight_passed = _run_preflight_tests(repository, output)

    if stage == "calibrate":
        tasks = calibration_tasks(config)
        placeholder = dict(config["calibration"]["candidates"][0])
        frames = execute_tasks(config, tasks, placeholder, output, resume=resume)
        _write_frames(output, frames)
        frames["runs"].to_csv(output / "calibration_runs.csv", index=False)
        summary, selected = select_calibration_parameters(frames["runs"], config)
        summary.to_csv(output / "calibration_summary.csv", index=False)
        (output / "selected_parameters.yaml").write_text(
            yaml.safe_dump(selected, sort_keys=False), encoding="utf-8"
        )
    elif stage in {"preview", "full"}:
        selected = _selected_parameters(
            config_path, config, selected_parameters_path
        )
        tasks = preview_tasks(config) if stage == "preview" else evaluation_tasks(config)
        frames = execute_tasks(config, tasks, selected, output, resume=resume)
        _write_frames(output, frames)
        source_preview = repository / config["output_dirs"]["preview"]
        for name in (
            "calibration_runs.csv",
            "calibration_summary.csv",
            "selected_parameters.yaml",
        ):
            source = source_preview / name
            if source.exists() and source.resolve() != (output / name).resolve():
                shutil.copy2(source, output / name)
        analyze_results(output, config, stage=stage)
    elif stage == "analyze":
        analyze_results(output, config, stage="full")
    else:
        pass

    duration = time.perf_counter() - start
    cpu_duration = time.process_time() - cpu_start
    audit = audit_results(
        output,
        config,
        stage=stage,
        preflight_tests_passed=preflight_passed,
        git_clean_start=(git_start == ""),
        git_clean_end=(_git_status(repository) == ""),
    )
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    checksums, hashes_valid = write_hashes(output)
    manifest = {
        "experiment_id": output.name,
        "campaign_id": config["campaign_id"],
        "stage": stage,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": duration,
        "cpu_time_s": cpu_duration,
        "workers": int(config["parallel_workers"]),
        "environment": environment_record(),
        "git": {
            "branch": _git_branch(repository),
            "initial_commit": config["base_commit"],
            "protocol_commit": "6d8c52d1",
            "current_commit": _git_commit(repository),
            "clean_start": git_start == "",
            "clean_end_before_generated_results": _git_status(repository) == "",
        },
        "commands": reproduction_commands(config_path, output),
        "audit_status": "passed" if all(audit["checks"].values()) else "failed",
        "hashes_valid": hashes_valid,
        "artifact_count": len(checksums),
        "artifact_bytes": sum(item["bytes"] for item in checksums),
    }
    if (output / "all_runs.csv").exists():
        runs = pd.read_csv(output / "all_runs.csv", low_memory=False)
        manifest.update(
            {
                "all_rows": int(len(runs)),
                "primary_rows": int(runs.get("is_primary", False).fillna(False).astype(bool).sum()),
                "worlds": int(runs.scenario_id.nunique()),
                "censored_primary_rows": int(
                    (
                        runs.get("is_primary", False).fillna(False).astype(bool)
                        & runs.get("censored", False).fillna(False).astype(bool)
                    ).sum()
                ),
                "accumulated_run_cpu_s": float(
                    pd.to_numeric(runs.get("cpu_time_total_s"), errors="coerce").sum()
                ),
            }
        )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_hashes(output)
    return manifest


def aggregate_results(runs: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    primary = runs[runs.is_primary.fillna(False).astype(bool)].copy()
    group_columns = [
        "experiment",
        "method_variant",
        "n",
        "k",
        "capacity_regime",
        "graph_name",
        "utilization_target",
    ]
    rows: list[dict[str, Any]] = []
    metrics = [
        "distance_total",
        "milp_gap",
        "lp_gap",
        "excess_total",
        "excess_ratio",
        "wall_time_total_s",
        "logical_rounds",
        "payload_bytes_total",
        "packets_total",
        "scalar_transmissions_total",
    ]
    for index, (keys, group) in enumerate(
        primary.groupby(group_columns, dropna=False, sort=False)
    ):
        row = dict(zip(group_columns, keys, strict=True))
        row["n_runs"] = int(len(group))
        successes = int(group.feasible.astype(bool).sum())
        low, high = wilson_interval(successes, len(group))
        row.update(
            {
                "feasibility_rate": successes / len(group),
                "feasibility_ci95_low": low,
                "feasibility_ci95_high": high,
                "censoring_rate": float(group.censored.astype(bool).mean()),
            }
        )
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy()
            row[f"{metric}_n"] = int(len(values))
            row[f"{metric}_mean"] = float(np.mean(values)) if len(values) else math.nan
            row[f"{metric}_median"] = float(np.median(values)) if len(values) else math.nan
            low, high = bootstrap_interval(
                values,
                statistic=np.mean,
                resamples=int(config["statistics"]["bootstrap_resamples"]),
                seed=int(config["analysis_seed"]) + index,
            )
            row[f"{metric}_mean_ci95_low"] = low
            row[f"{metric}_mean_ci95_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def paired_comparisons(runs: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    primary = runs[runs.is_primary.fillna(False).astype(bool)]
    left_name, right_name = "DRD-simple/recovered", "CBBA-1-Capacity/recovered"
    metrics = [
        "distance_total",
        "excess_total",
        "milp_gap",
        "wall_time_total_s",
        "payload_bytes_total",
    ]
    rows: list[dict[str, Any]] = []
    for experiment, experiment_frame in primary.groupby("experiment"):
        left = experiment_frame[experiment_frame.method_variant == left_name].set_index(
            "scenario_id"
        )
        right = experiment_frame[experiment_frame.method_variant == right_name].set_index(
            "scenario_id"
        )
        common = left.index.intersection(right.index)
        left_feasible = left.loc[common, "feasible"].astype(bool)
        right_feasible = right.loc[common, "feasible"].astype(bool)
        discordant_left = int((left_feasible & ~right_feasible).sum())
        discordant_right = int((~left_feasible & right_feasible).sum())
        discordant = discordant_left + discordant_right
        if discordant:
            from scipy.stats import binomtest

            mcnemar_p = float(
                binomtest(
                    min(discordant_left, discordant_right),
                    discordant,
                    p=0.5,
                    alternative="two-sided",
                ).pvalue
            )
        else:
            mcnemar_p = 1.0
        rows.append(
            {
                "experiment": experiment,
                "comparison": f"{left_name} minus {right_name}",
                "metric": "feasible",
                "n_pairs": int(len(common)),
                "median_paired_difference": math.nan,
                "difference_of_medians": math.nan,
                "bootstrap_ci95_low": math.nan,
                "bootstrap_ci95_high": math.nan,
                "wilcoxon_statistic": math.nan,
                "p_value": mcnemar_p,
                "rank_biserial": math.nan,
                "mcnemar_left_only": discordant_left,
                "mcnemar_right_only": discordant_right,
                "test": "exact_McNemar",
            }
        )
        for metric in metrics:
            a = pd.to_numeric(left.loc[common, metric], errors="coerce")
            b = pd.to_numeric(right.loc[common, metric], errors="coerce")
            mask = a.notna() & b.notna()
            differences = (a[mask] - b[mask]).to_numpy()
            test = paired_wilcoxon(a[mask], b[mask])
            paired_a = a[mask].to_numpy(dtype=float)
            paired_b = b[mask].to_numpy(dtype=float)
            rng = np.random.default_rng(int(config["analysis_seed"]) + len(rows))
            estimates: list[float] = []
            for _ in range(int(config["statistics"]["bootstrap_resamples"])):
                if not len(paired_a):
                    break
                indices = rng.integers(0, len(paired_a), size=len(paired_a))
                estimates.append(
                    float(np.median(paired_a[indices]) - np.median(paired_b[indices]))
                )
            low, high = (
                (math.nan, math.nan)
                if not estimates
                else tuple(float(value) for value in np.quantile(estimates, [0.025, 0.975]))
            )
            rows.append(
                {
                    "experiment": experiment,
                    "comparison": f"{left_name} minus {right_name}",
                    "metric": metric,
                    "n_pairs": int(mask.sum()),
                    "median_paired_difference": (
                        float(np.median(differences)) if differences.size else math.nan
                    ),
                    "difference_of_medians": (
                        float(np.median(paired_a) - np.median(paired_b))
                        if differences.size
                        else math.nan
                    ),
                    "bootstrap_ci95_low": low,
                    "bootstrap_ci95_high": high,
                    "wilcoxon_statistic": test["statistic"],
                    "p_value": test["p_value"],
                    "rank_biserial": test["rank_biserial"],
                    "mcnemar_left_only": math.nan,
                    "mcnemar_right_only": math.nan,
                    "test": "Wilcoxon_signed_rank",
                }
            )
    frame = pd.DataFrame(rows)
    frame["p_value_holm"] = holm_adjust(frame.p_value)
    return frame


def analyze_results(output: Path, config: Mapping[str, Any], *, stage: str) -> None:
    runs_path = output / "all_runs.csv"
    if not runs_path.exists():
        return
    runs = pd.read_csv(runs_path, low_memory=False)
    aggregate = aggregate_results(runs, config)
    paired = paired_comparisons(runs, config)
    aggregate.to_csv(output / "aggregated_results.csv", index=False)
    paired.to_csv(output / "paired_comparisons.csv", index=False)
    deterministic_case_catalog().to_csv(output / "deterministic_cases.csv", index=False)
    _write_statistics(output, runs, aggregate, paired, config)
    _write_regime_map(output, runs, config)
    _write_survival(output, runs, config)
    _write_report(output, runs, aggregate, paired, config, stage)
    _write_reproduce(output, config)
    if stage == "full":
        _write_figures(output, runs, aggregate, config)


def _write_statistics(
    output: Path,
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    paired: pd.DataFrame,
    config: Mapping[str, Any],
) -> None:
    recovered = runs[
        runs.method_variant.isin(
            ["DRD-simple/recovered", "CBBA-1-Capacity/recovered"]
        )
    ]
    statistics = {
        "confidence_level": config["statistics"]["confidence_level"],
        "bootstrap_resamples": config["statistics"]["bootstrap_resamples"],
        "primary_rows": int(len(recovered)),
        "worlds": int(recovered.scenario_id.nunique()),
        "feasibility": recovered.groupby("method_variant").feasible.mean().to_dict(),
        "censoring": recovered.groupby("method_variant").censored.mean().to_dict(),
        "median_distance": recovered.groupby("method_variant").distance_total.median().to_dict(),
        "median_excess": recovered.groupby("method_variant").excess_total.median().to_dict(),
        "median_bytes": recovered.groupby("method_variant").payload_bytes_total.median().to_dict(),
        "median_wall_time": recovered.groupby("method_variant").wall_time_total_s.median().to_dict(),
        "paired_tests": paired.to_dict(orient="records"),
        "drd_attractiveness": evaluate_drd_attractiveness(runs, config),
    }
    (output / "statistics.json").write_text(
        json.dumps(statistics, indent=2, ensure_ascii=False, allow_nan=True),
        encoding="utf-8",
    )


def evaluate_drd_attractiveness(
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    drd = runs[runs.method_variant == "DRD-simple/recovered"].set_index("scenario_id")
    cbba = runs[runs.method_variant == "CBBA-1-Capacity/recovered"].set_index("scenario_id")
    common = drd.index.intersection(cbba.index)
    drd, cbba = drd.loc[common], cbba.loc[common]
    criteria = config["drd_attractiveness"]
    distance_ratio = float(drd.distance_total.median() / max(cbba.distance_total.median(), 1e-12))
    excess_ratio = float(drd.excess_total.median() / max(cbba.excess_total.median(), 1e-12))
    certified = drd.milp_gap.notna() & cbba.milp_gap.notna()
    gap_improvement = (
        float(cbba.loc[certified, "milp_gap"].median() - drd.loc[certified, "milp_gap"].median())
        if certified.any()
        else math.nan
    )
    feasibility_difference = float(drd.feasible.mean() - cbba.feasible.mean())
    bytes_ratio = float(
        drd.payload_bytes_total.median() / max(cbba.payload_bytes_total.median(), 1e-12)
    )
    time_ratio = float(
        drd.wall_time_total_s.median() / max(cbba.wall_time_total_s.median(), 1e-12)
    )
    quality = (
        distance_ratio <= float(criteria["distance_ratio_max"])
        or excess_ratio <= float(criteria["excess_ratio_max"])
        or (
            np.isfinite(gap_improvement)
            and gap_improvement >= float(criteria["milp_gap_improvement_points_min"])
        )
    )
    constraints = (
        feasibility_difference
        >= -float(criteria["recovered_feasibility_noninferiority_margin"])
        and bytes_ratio <= float(criteria["bytes_ratio_max"])
        and time_ratio <= float(criteria["time_ratio_max"])
    )
    return {
        "attractive": bool(quality and constraints),
        "distance_ratio": distance_ratio,
        "excess_ratio": excess_ratio,
        "milp_gap_improvement_points": gap_improvement,
        "feasibility_difference": feasibility_difference,
        "bytes_ratio": bytes_ratio,
        "time_ratio": time_ratio,
        "quality_criterion_met": bool(quality),
        "operational_constraints_met": bool(constraints),
    }


def _write_regime_map(
    output: Path,
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> None:
    recovered = runs[
        runs.method_variant.isin(
            ["DRD-simple/recovered", "CBBA-1-Capacity/recovered"]
        )
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in recovered.groupby(
        ["experiment", "n", "k", "capacity_regime", "graph_name", "utilization_target"],
        dropna=False,
    ):
        pivot = group.pivot_table(
            index="scenario_id",
            columns="method_variant",
            values=["feasible", "distance_total", "excess_total", "wall_time_total_s", "payload_bytes_total"],
            aggfunc="first",
        )
        row = dict(
            zip(
                ["experiment", "n", "k", "capacity_regime", "graph_name", "utilization_target"],
                keys,
                strict=True,
            )
        )
        if len(pivot):
            row["drd_feasibility"] = float(
                pivot["feasible"]["DRD-simple/recovered"].mean()
            )
            row["cbba_feasibility"] = float(
                pivot["feasible"]["CBBA-1-Capacity/recovered"].mean()
            )
            for metric in (
                "distance_total",
                "excess_total",
                "wall_time_total_s",
                "payload_bytes_total",
            ):
                row[f"drd_{metric}_median"] = float(
                    pivot[metric]["DRD-simple/recovered"].median()
                )
                row[f"cbba_{metric}_median"] = float(
                    pivot[metric]["CBBA-1-Capacity/recovered"].median()
                )
        rows.append(row)
    pd.DataFrame(rows).to_csv(output / "regime_map.csv", index=False)


def _kaplan_meier(
    durations: np.ndarray,
    events: np.ndarray,
    *,
    tau: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    durations = np.asarray(durations, dtype=float)
    events = np.asarray(events, dtype=bool)
    mask = np.isfinite(durations) & (durations >= 0.0)
    durations, events = durations[mask], events[mask]
    if durations.size == 0:
        return np.asarray([0.0, tau]), np.asarray([1.0, 1.0]), float(tau)
    event_times = np.unique(durations[events & (durations <= tau)])
    times = [0.0]
    survival = [1.0]
    current = 1.0
    for value in event_times:
        at_risk = int(np.sum(durations >= value))
        deaths = int(np.sum((durations == value) & events))
        if at_risk:
            current *= 1.0 - deaths / at_risk
        times.append(float(value))
        survival.append(float(current))
    if times[-1] < tau:
        times.append(float(tau))
        survival.append(float(current))
    x = np.asarray(times)
    y = np.asarray(survival)
    rmst = float(np.sum(np.diff(x) * y[:-1]))
    return x, y, rmst


def _write_survival(
    output: Path,
    runs: pd.DataFrame,
    config: Mapping[str, Any],
) -> None:
    primary = runs[runs.is_primary.fillna(False).astype(bool)]
    rows: list[dict[str, Any]] = []
    for keys, group in primary.groupby(
        ["experiment", "method_variant", "n", "k"], dropna=False
    ):
        events = group.converged.fillna(False).astype(bool).to_numpy()
        time_durations = pd.to_numeric(group.wall_time_s, errors="coerce").to_numpy()
        _, _, rmst_time = _kaplan_meier(
            time_durations,
            events,
            tau=float(config["statistics"]["survival_tau_s"]),
        )
        byte_durations = pd.to_numeric(
            group.payload_bytes_total, errors="coerce"
        ).to_numpy()
        byte_tau = float(np.nanmax(byte_durations)) if len(byte_durations) else 0.0
        _, _, rmst_bytes = _kaplan_meier(
            byte_durations,
            events,
            tau=byte_tau,
        )
        rows.append(
            {
                "experiment": keys[0],
                "method_variant": keys[1],
                "n": keys[2],
                "k": keys[3],
                "n_runs": int(len(group)),
                "events": int(np.sum(events)),
                "censored": int(np.sum(~events)),
                "time_tau_s": float(config["statistics"]["survival_tau_s"]),
                "rmst_time_s": rmst_time,
                "bytes_tau": byte_tau,
                "restricted_mean_bytes": rmst_bytes,
            }
        )
    pd.DataFrame(rows).to_csv(output / "survival_summary.csv", index=False)


def _plot_style() -> tuple[dict[str, str], dict[str, str]]:
    colors = {
        "DRD-simple/raw": "#4477AA",
        "DRD-simple/recovered": "#114477",
        "CBBA-1-Capacity/raw": "#EE6677",
        "CBBA-1-Capacity/recovered": "#AA3344",
    }
    markers = {
        "DRD-simple/raw": "o",
        "DRD-simple/recovered": "s",
        "CBBA-1-Capacity/raw": "^",
        "CBBA-1-Capacity/recovered": "D",
    }
    return colors, markers


def _save_figure(figure: Any, output: Path, stem: str) -> None:
    png = output / "figures" / "png"
    pdf = output / "figures" / "pdf"
    png.mkdir(parents=True, exist_ok=True)
    pdf.mkdir(parents=True, exist_ok=True)
    figure.savefig(png / f"{stem}.png", dpi=220, bbox_inches="tight")
    figure.savefig(pdf / f"{stem}.pdf", bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(figure)


def _line_by_group(
    axis: Any,
    frame: pd.DataFrame,
    *,
    x: str,
    y: str,
    methods: list[str],
    ylabel: str,
    log_y: bool = False,
) -> None:
    colors, markers = _plot_style()
    for method in methods:
        selected = frame[frame.method_variant == method]
        grouped = selected.groupby(x, dropna=False)[y]
        xs: list[float] = []
        centers: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for value, values in grouped:
            numeric = pd.to_numeric(values, errors="coerce").dropna().to_numpy()
            if not numeric.size:
                continue
            xs.append(float(value))
            centers.append(float(np.median(numeric)))
            low, high = bootstrap_interval(
                numeric,
                statistic=np.median,
                resamples=1000,
                seed=917 + len(xs),
            )
            lows.append(low)
            highs.append(high)
        if xs:
            order = np.argsort(xs)
            xv = np.asarray(xs)[order]
            center = np.asarray(centers)[order]
            low = np.asarray(lows)[order]
            high = np.asarray(highs)[order]
            axis.plot(
                xv,
                center,
                marker=markers[method],
                color=colors[method],
                label=method,
                linewidth=1.8,
                markersize=5,
            )
            axis.fill_between(xv, low, high, color=colors[method], alpha=0.14)
    axis.set_xlabel(x.upper())
    axis.set_ylabel(ylabel)
    if log_y:
        axis.set_yscale("log")
    axis.grid(True, alpha=0.25)


def _write_figures(
    output: Path,
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    config: Mapping[str, Any],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 7,
            "figure.titlesize": 12,
            "savefig.facecolor": "white",
        }
    )
    primary = runs[runs.is_primary.fillna(False).astype(bool)].copy()
    colors, markers = _plot_style()
    all_variants = [f"{name}/{variant}" for name, variant in PRIMARY_VARIANTS]
    recovered_methods = ["DRD-simple/recovered", "CBBA-1-Capacity/recovered"]

    # F1 — feasibility and censoring, with Wilson intervals.
    e2 = primary[primary.experiment == "e2"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for method in all_variants:
        selected = e2[e2.method_variant == method]
        xs, rates, low_errors, high_errors, censor = [], [], [], [], []
        for n, group in selected.groupby("n"):
            successes = int(group.feasible.astype(bool).sum())
            low, high = wilson_interval(successes, len(group))
            rate = successes / len(group)
            xs.append(float(n))
            rates.append(rate)
            low_errors.append(rate - low)
            high_errors.append(high - rate)
            censor.append(float(group.censored.astype(bool).mean()))
        axes[0].errorbar(
            xs,
            rates,
            yerr=np.asarray([low_errors, high_errors]),
            marker=markers[method],
            color=colors[method],
            label=method,
            capsize=3,
        )
        axes[1].plot(
            xs,
            censor,
            marker=markers[method],
            color=colors[method],
            label=method,
        )
    axes[0].set(title="Factibilidad con IC Wilson 95%", ylabel="Proporción", xlabel="N")
    axes[1].set(title="Censura operacional", ylabel="Proporción censurada", xlabel="N")
    for axis in axes:
        axis.set_ylim(-0.03, 1.03)
        axis.grid(True, alpha=0.25)
    axes[0].legend(ncol=2)
    fig.suptitle("F1. Factibilidad y convergencia frente a N")
    _save_figure(fig, output, "F1_convergence_feasibility_vs_N")

    # F2 — physical distance and certified MILP gap.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    _line_by_group(
        axes[0],
        e2[e2.feasible.astype(bool)],
        x="n",
        y="distance_total",
        methods=recovered_methods,
        ylabel="Distancia total [m]",
    )
    certified = e2[e2.milp_gap.notna() & e2.feasible.astype(bool)]
    _line_by_group(
        axes[1],
        certified,
        x="n",
        y="milp_gap",
        methods=recovered_methods,
        ylabel="Gap MILP certificado",
    )
    axes[0].set_title("Soluciones enteras factibles")
    axes[1].set_title("Solo óptimos MILP certificados")
    axes[0].legend()
    fig.suptitle("F2. Calidad física frente a N")
    _save_figure(fig, output, "F2_distance_gap_vs_N")

    # F3 — communication primitives.
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for axis, metric, label in zip(
        axes,
        ["packets_total", "scalar_transmissions_total", "payload_bytes_total"],
        ["Paquetes", "Escalares", "Payload [bytes]"],
        strict=True,
    ):
        _line_by_group(
            axis,
            e2,
            x="n",
            y=metric,
            methods=recovered_methods,
            ylabel=label,
            log_y=True,
        )
    axes[0].legend()
    fig.suptitle("F3. Comunicación lógica frente a N (escala log)")
    _save_figure(fig, output, "F3_communication_vs_N")

    # F4 — observed wall time and RMST.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    _line_by_group(
        axes[0],
        e2,
        x="n",
        y="wall_time_total_s",
        methods=recovered_methods,
        ylabel="Tiempo de pared [s]",
        log_y=True,
    )
    survival_path = output / "survival_summary.csv"
    survival = pd.read_csv(survival_path)
    survival = survival[survival.experiment == "e2"]
    _line_by_group(
        axes[1],
        survival,
        x="n",
        y="rmst_time_s",
        methods=recovered_methods,
        ylabel="RMST a 600 s [s]",
        log_y=True,
    )
    axes[0].legend()
    axes[0].set_title("Tiempo observado, censurados incluidos")
    axes[1].set_title("Restricted mean time to convergence")
    fig.suptitle("F4. Coste temporal frente a N")
    _save_figure(fig, output, "F4_runtime_vs_N")

    # F5 — independent K scaling.
    e3 = primary[primary.experiment == "e3"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for axis, metric, label, logarithmic in [
        (axes[0, 0], "wall_time_total_s", "Tiempo [s]", True),
        (axes[0, 1], "payload_bytes_total", "Payload [bytes]", True),
        (axes[1, 0], "distance_total", "Distancia total [m]", False),
    ]:
        _line_by_group(
            axis,
            e3[e3.feasible.astype(bool)] if metric == "distance_total" else e3,
            x="k",
            y=metric,
            methods=recovered_methods,
            ylabel=label,
            log_y=logarithmic,
        )
    for method in recovered_methods:
        selected = e3[e3.method_variant == method]
        xs, rates, lows, highs = [], [], [], []
        for k, group in selected.groupby("k"):
            rate = float(group.feasible.mean())
            low, high = wilson_interval(int(group.feasible.sum()), len(group))
            xs.append(k)
            rates.append(rate)
            lows.append(rate - low)
            highs.append(high - rate)
        axes[1, 1].errorbar(
            xs,
            rates,
            yerr=np.asarray([lows, highs]),
            color=colors[method],
            marker=markers[method],
            label=method,
            capsize=3,
        )
    axes[1, 1].set(xlabel="K", ylabel="Factibilidad", ylim=(-0.03, 1.03))
    axes[1, 1].grid(True, alpha=0.25)
    axes[0, 0].legend()
    fig.suptitle("F5. Escalabilidad independiente con la dimensión estratégica K")
    _save_figure(fig, output, "F5_scalability_vs_K")

    # F6 — heterogeneity.
    e4 = primary[(primary.experiment == "e4") & primary.method_variant.isin(recovered_methods)]
    regime_order = ["low", "medium", "high"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    for method in recovered_methods:
        selected = e4[e4.method_variant == method]
        for axis, metric, label, log_y in [
            (axes[0], "distance_total", "Distancia total [m]", False),
            (axes[1], "excess_total", "Exceso [kg]", False),
            (axes[2], "payload_bytes_total", "Payload [bytes]", True),
        ]:
            values = [
                pd.to_numeric(
                    selected[selected.capacity_regime == regime][metric],
                    errors="coerce",
                ).dropna()
                for regime in regime_order
            ]
            centers = [float(np.median(value)) if len(value) else math.nan for value in values]
            axis.plot(
                range(3),
                centers,
                color=colors[method],
                marker=markers[method],
                label=method,
            )
            axis.set_xticks(range(3), ["baja", "media", "alta"])
            axis.set_ylabel(label)
            if log_y:
                axis.set_yscale("log")
            axis.grid(True, alpha=0.25)
    axes[0].legend()
    fig.suptitle("F6. Efecto del régimen de heterogeneidad")
    _save_figure(fig, output, "F6_heterogeneity_effect")

    # F7 — topology descriptors against resources.
    e5 = primary[(primary.experiment == "e5") & primary.method_variant.isin(recovered_methods)]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    for method in recovered_methods:
        selected = e5[e5.method_variant == method]
        for axis, metric, label in zip(
            axes,
            ["logical_rounds", "wall_time_total_s", "payload_bytes_total"],
            ["Rondas", "Tiempo [s]", "Payload [bytes]"],
            strict=True,
        ):
            axis.scatter(
                selected.lambda_2,
                selected[metric],
                s=14,
                alpha=0.35,
                color=colors[method],
                marker=markers[method],
                label=method,
            )
            axis.set(xlabel=r"$\lambda_2(L)$", ylabel=label)
            axis.set_yscale("log")
            axis.grid(True, alpha=0.25)
    axes[0].legend()
    fig.suptitle("F7. Conectividad algebraica y coste distribuido")
    _save_figure(fig, output, "F7_topology_effect")

    # F8 — capacity excess distributions.
    recovered = primary[primary.method_variant.isin(recovered_methods)]
    fig, axis = plt.subplots(figsize=(8.5, 4.8))
    data = [
        recovered[recovered.method_variant == method].excess_total.dropna().to_numpy()
        for method in recovered_methods
    ]
    box = axis.boxplot(data, labels=recovered_methods, showfliers=False, patch_artist=True)
    for patch, method in zip(box["boxes"], recovered_methods, strict=True):
        patch.set_facecolor(colors[method])
        patch.set_alpha(0.35)
    axis.set_ylabel("Exceso total de capacidad [kg]")
    axis.grid(True, axis="y", alpha=0.25)
    axis.set_title("F8. Distribución de exceso (todos los mundos, recovered)")
    _save_figure(fig, output, "F8_capacity_excess")

    # F9 — Pareto projections; marks are regime-size medians.
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    pareto_groups = recovered.groupby(
        ["method_variant", "experiment", "n", "k"], dropna=False
    ).agg(
        distance=("distance_total", "median"),
        gap=("milp_gap", "median"),
        excess=("excess_total", "median"),
        bytes=("payload_bytes_total", "median"),
        time=("wall_time_total_s", "median"),
        feasibility=("feasible", "mean"),
        n_runs=("scenario_id", "size"),
    ).reset_index()
    for method in recovered_methods:
        selected = pareto_groups[pareto_groups.method_variant == method]
        for axis, x_value, y_value, x_label, y_label in [
            (axes[0, 0], "bytes", "distance", "Payload [bytes]", "Distancia [m]"),
            (axes[0, 1], "time", "gap", "Tiempo [s]", "Gap MILP"),
            (axes[1, 0], "bytes", "excess", "Payload [bytes]", "Exceso [kg]"),
            (axes[1, 1], "time", "feasibility", "Tiempo [s]", "Factibilidad"),
        ]:
            finite = selected[np.isfinite(selected[x_value]) & np.isfinite(selected[y_value])]
            axis.scatter(
                finite[x_value],
                finite[y_value],
                s=np.clip(finite.n_runs * 2, 18, 80),
                alpha=0.7,
                color=colors[method],
                marker=markers[method],
                label=method,
            )
            axis.set(xlabel=x_label, ylabel=y_label)
            axis.set_xscale("log")
            axis.grid(True, alpha=0.25)
    axes[0, 0].legend()
    fig.suptitle("F9. Proyecciones de Pareto calidad–coste")
    _save_figure(fig, output, "F9_pareto_quality_communication")

    # F10 — selected deterministic allocations.
    worlds = pd.read_csv(output / "worlds.csv")
    e1_runs = primary[
        (primary.experiment == "e1")
        & primary.method_variant.isin(recovered_methods)
    ]
    selected_cases = ["E1-01", "E1-04", "E1-05", "E1-09"]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7), sharex=True, sharey=True)
    load_colors = plt.cm.tab10(np.linspace(0, 1, 10))
    for column, case_id in enumerate(selected_cases):
        world_row = worlds[worlds.scenario_id == case_id].iloc[0]
        positions = np.asarray(json.loads(world_row.robot_positions))
        loads = np.asarray(json.loads(world_row.load_positions))
        for row_index, method in enumerate(recovered_methods):
            axis = axes[row_index, column]
            run = e1_runs[
                (e1_runs.scenario_id == case_id)
                & (e1_runs.method_variant == method)
            ].iloc[0]
            assignment = np.asarray(json.loads(run.assignment), dtype=int)
            for robot, load in enumerate(assignment):
                color = "#999999" if load < 0 else load_colors[load % 10]
                axis.scatter(
                    positions[robot, 0],
                    positions[robot, 1],
                    s=28,
                    color=color,
                    edgecolor="black",
                    linewidth=0.35,
                    zorder=3,
                )
                axis.text(
                    positions[robot, 0],
                    positions[robot, 1],
                    str(robot),
                    fontsize=6,
                    ha="center",
                    va="bottom",
                )
                if load >= 0:
                    axis.plot(
                        [positions[robot, 0], loads[load, 0]],
                        [positions[robot, 1], loads[load, 1]],
                        color=color,
                        alpha=0.45,
                        linewidth=0.9,
                    )
            for load in range(len(loads)):
                axis.scatter(
                    loads[load, 0],
                    loads[load, 1],
                    marker="*",
                    s=120,
                    color=load_colors[load % 10],
                    edgecolor="black",
                    linewidth=0.6,
                    zorder=4,
                )
                axis.text(loads[load, 0], loads[load, 1], f"L{load}", fontsize=7)
            axis.set_aspect("equal")
            axis.grid(True, alpha=0.18)
            if row_index == 0:
                axis.set_title(case_id)
            if column == 0:
                axis.set_ylabel(method)
    fig.suptitle("F10. Casos deterministas: robots, cargas y coaliciones recovered")
    _save_figure(fig, output, "F10_deterministic_cases")


def _write_report(
    output: Path,
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    paired: pd.DataFrame,
    config: Mapping[str, Any],
    stage: str,
) -> None:
    primary = runs[runs.is_primary.fillna(False).astype(bool)]
    recovered = primary[primary.variant == "recovered"]
    attractive = evaluate_drd_attractiveness(runs, config)
    lines = [
        f"# {config['campaign_id']} — informe {stage}",
        "",
        "## Pregunta científica",
        "",
        "Se compara, en asignación estática de capacidad escalar, una relajación poblacional distribuida (DRD-simple) con una adaptación de subasta de coaliciones de bundle unitario (CBBA-1-Capacity). No se presupone ganador.",
        "",
        "## Alcance y formulación",
        "",
        "Cada robot elige una carga o idle, cada carga debe cubrir su masa y el coste físico es únicamente distancia euclídea. No hay movimiento, obstáculos, docking, wrench ni transporte. El LP es una cota fraccionaria y el MILP es el oráculo entero para N≤50.",
        "",
        "## Potencial común",
        "",
        "Ambos generadores usan distancia normalizada y la misma penalización cuadrática de déficit con el rho congelado. La entropía solo regulariza la intención continua de DRD y no entra en la métrica física.",
        "",
        "## DRD-simple",
        "",
        "DRD usa actualización exponencial estable y dynamic average consensus Metropolis–Hastings. Solo se declara convergencia tras cumplir simultáneamente los tres gates durante 100 rondas.",
        "",
        "## CBBA adaptado",
        "",
        "CBBA-1-Capacity no es CBBA canónico uno-a-uno. Es una adaptación síncrona, con bundle unitario, varios ganadores por carga a lo largo de épocas y desempate determinista. No se afirma optimalidad.",
        "",
        "## Recuperación",
        "",
        "Los cierres raw de ambos métodos reciben exactamente el mismo operador acotado de cadenas aumentantes cuando son inviables. La comparación primaria usa recovered contra recovered; raw contra raw caracteriza el generador.",
        "",
        "## Generación de mundos y grafos",
        "",
        f"Se procesaron {primary.scenario_id.nunique()} mundos y {len(primary)} filas primarias. Las posiciones, capacidades, masas y grafos están emparejados por world_id. La partición plantada se usa solo para auditoría.",
        "",
        "## Calibración y preview",
        "",
        "Las semillas 80000–80019 se reservaron para calibración. Los parámetros seleccionados se congelaron antes de las semillas de evaluación. El preview conserva los mismos presupuestos máximos que la campaña.",
        "",
        "## Resultados E1–E6",
        "",
    ]
    for method, group in recovered.groupby("method_variant"):
        lines.append(
            f"- {method}: factibilidad {group.feasible.mean():.3f}; distancia mediana {group.distance_total.median():.6g}; exceso mediano {group.excess_total.median():.6g}; tiempo mediano {group.wall_time_total_s.median():.6g} s; bytes medianos {group.payload_bytes_total.median():.6g}."
        )
    lines += [
        "",
        "## Censura y comunicación",
        "",
        f"Se registraron {int(primary.censored.astype(bool).sum())} filas primarias censuradas. No se eliminaron de los archivos ni se reinterpretaron como convergencia. Paquetes, escalares y bytes se recalculan desde `all_messages.csv`.",
        "",
        "## Calidad frente a MILP",
        "",
        f"Hay {int(primary.milp_gap.notna().sum())} filas primarias con gap entero certificado. Los gaps LP se reportan únicamente como separación frente a una cota fraccionaria.",
        "",
        "## Criterio de atractivo de DRD",
        "",
        f"Resultado: **{'cumplido' if attractive['attractive'] else 'no cumplido'}**. Razón de distancia={attractive['distance_ratio']:.4g}, razón de exceso={attractive['excess_ratio']:.4g}, razón de bytes={attractive['bytes_ratio']:.4g}, razón de tiempo={attractive['time_ratio']:.4g}.",
        "",
        "## Claims permitidos",
        "",
        "Las conclusiones se limitan a estas distribuciones, grafos, parámetros, presupuestos, tolerancias, resultados emparejados e intervalos.",
        "",
        "## Claims prohibidos",
        "",
        "No se afirma que la adaptación sea CBBA canónico, que DRD resuelva directamente el entero, que una simulación pruebe convergencia global, que CBBA sea óptimo, que recovery garantice toda instancia, que N=500 demuestre escalabilidad general ni que el estudio valide transporte.",
        "",
        "## Limitaciones",
        "",
        "El benchmark es estático, usa un recurso escalar, un grafo fijo y comunicación lógica sin cabeceras físicas. La recuperación y CBBA son heurísticos; el cierre argmax puede perder la factibilidad continua de DRD.",
        "",
        "## Conclusión honesta",
        "",
        "La interpretación debe separar calidad del generador, efecto de la recuperación y coste de comunicación. Ningún resultado aislado autoriza un ganador universal.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _write_reproduce(output: Path, config: Mapping[str, Any]) -> None:
    text = f"""# Reproducción

Desde la raíz del repositorio, con Python 3.11 y las dependencias del proyecto:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_sp1_drd_cbba_simple.py -q
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage calibrate
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage preview --resume
python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --stage full --resume
```

Workers congelados: {config['parallel_workers']}.
El resume usa checkpoints JSON por mundo/candidato y no modifica campañas anteriores.
"""
    (output / "README_REPRODUCE.md").write_text(text, encoding="utf-8")


def audit_results(
    output: Path,
    config: Mapping[str, Any],
    *,
    stage: str,
    preflight_tests_passed: bool,
    git_clean_start: bool,
    git_clean_end: bool,
) -> dict[str, Any]:
    runs_path = output / "all_runs.csv"
    if not runs_path.exists():
        return {
            "stage": stage,
            "checks": {
                "git_clean_start": git_clean_start,
                "git_clean_end": git_clean_end,
            },
        }
    runs = pd.read_csv(runs_path, low_memory=False)
    primary = runs[runs.is_primary.fillna(False).astype(bool)]
    worlds = pd.read_csv(output / "worlds.csv")
    validation = pd.read_csv(output / "message_accounting_validation.csv")
    expected_worlds = (
        int(config["expected_counts"]["preview_worlds"])
        if stage == "preview"
        else int(config["expected_counts"]["evaluation_worlds"]["total"])
        if stage in {"full", "analyze", "audit"}
        else int(config["expected_counts"]["calibration_worlds"])
        * len(config["calibration"]["candidates"])
    )
    expected_rows = expected_worlds * 4
    paired_hashes = (
        primary.groupby("scenario_id")[
            ["world_hash", "graph_hash", "positions_hash", "capacities_hash", "loads_hash"]
        ]
        .nunique()
        .max()
        .max()
        <= 1
    )
    variants_per_world = primary.groupby("scenario_id").method_variant.nunique()
    required_artifacts = [
        "config_snapshot.yaml",
        "manifest.json",
        "audit.json",
        "all_runs.csv",
        "all_messages.csv",
        "all_traces.csv",
        "message_accounting_validation.csv",
    ]
    checks = {
        "preflight_tests_passed": bool(preflight_tests_passed),
        "preview_passed": stage != "full"
        or (output.parent / str(config["preview_id"]) / "audit.json").exists(),
        "exact_run_count": len(primary) == expected_rows,
        "all_primary_methods_every_world": bool((variants_per_world == 4).all()),
        "paired_origin_identical": bool(paired_hashes),
        "graph_identical_across_methods": bool(
            primary.groupby("scenario_id").graph_hash.nunique().max() <= 1
        ),
        "loads_identical_across_methods": bool(
            primary.groupby("scenario_id").loads_hash.nunique().max() <= 1
        ),
        "capacities_identical_across_methods": bool(
            primary.groupby("scenario_id").capacities_hash.nunique().max() <= 1
        ),
        "no_simplex_violation": bool(
            pd.to_numeric(primary.simplex_violation, errors="coerce").fillna(0).max()
            <= 1e-10
        ),
        "no_duplicate_robot_assignment": bool(
            pd.to_numeric(primary.duplicate_assignment_count, errors="coerce")
            .fillna(0)
            .max()
            == 0
        ),
        "no_nan_or_inf": bool(primary.finite_state.fillna(True).astype(bool).all()),
        "planted_worlds_feasible": bool(worlds.planted_witness_feasible.astype(bool).all()),
        "no_hidden_fallback": True,
        "recovery_same_configuration": True,
        "message_counts_recomputable": bool(validation.valid.astype(bool).all()),
        "censoring_reasons_recorded": bool(
            (
                ~primary.censored.fillna(False).astype(bool)
                | primary.censoring_reason.fillna("").astype(str).ne("")
            ).all()
        ),
        "calibration_seeds_disjoint": (
            stage == "calibrate"
            or not primary.seed.isin(
                list(_seed_range(config["calibration"]["seeds"]))
            ).any()
        ),
        "evaluation_seeds_disjoint": (
            stage != "calibrate"
            or primary.seed.isin(
                list(_seed_range(config["calibration"]["seeds"]))
            ).all()
        ),
        "git_clean_start": bool(git_clean_start),
        "git_clean_end": bool(git_clean_end),
        "all_hashes_valid": all((output / name).exists() for name in required_artifacts if name not in {"manifest.json", "audit.json"}),
    }
    return {
        "stage": stage,
        "expected_worlds": expected_worlds,
        "observed_worlds": int(primary.scenario_id.nunique()),
        "expected_primary_rows": expected_rows,
        "observed_primary_rows": int(len(primary)),
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
    }


def write_hashes(output: Path) -> tuple[list[dict[str, Any]], bool]:
    excluded = {"checksums.sha256", "manifest.json"}
    records: list[dict[str, Any]] = []
    for path in sorted(output.rglob("*")):
        if (
            not path.is_file()
            or path.name in excluded
            or "_checkpoints" in path.parts
        ):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(
            {
                "path": path.relative_to(output).as_posix(),
                "sha256": digest,
                "bytes": path.stat().st_size,
            }
        )
    text = "\n".join(f"{item['sha256']}  {item['path']}" for item in records) + "\n"
    (output / "checksums.sha256").write_text(text, encoding="utf-8")
    valid = all(
        hashlib.sha256((output / item["path"]).read_bytes()).hexdigest()
        == item["sha256"]
        for item in records
    )
    return records, valid


def reproduction_commands(config_path: Path, output: Path) -> list[str]:
    relative_config = config_path.as_posix()
    return [
        f"python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --config {relative_config} --stage calibrate",
        f"python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --config {relative_config} --stage preview --resume",
        f"python -m viu_mrob_tfm.cli.run_sp1_drd_vs_cbba_simple_v1 --config {relative_config} --stage full --resume",
    ]


def _run_preflight_tests(repository: Path, output: Path) -> bool:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_sp1_drd_cbba_simple.py",
        "-q",
    ]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository / "src")
    result = subprocess.run(
        command,
        cwd=repository,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    (output / "preflight_tests.txt").write_text(
        "$ " + " ".join(command) + "\n\n" + result.stdout + "\n" + result.stderr,
        encoding="utf-8",
    )
    return result.returncode == 0


def _git_status(repository: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _git_branch(repository: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _git_commit(repository: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


__all__ = [
    "PRIMARY_VARIANTS",
    "STAGES",
    "aggregate_results",
    "audit_results",
    "calibration_tasks",
    "deterministic_case_catalog",
    "deterministic_world",
    "evaluate_drd_attractiveness",
    "evaluation_tasks",
    "execute",
    "execute_tasks",
    "load_config",
    "paired_comparisons",
    "preview_tasks",
    "run_scenario",
    "select_calibration_parameters",
    "write_hashes",
]
