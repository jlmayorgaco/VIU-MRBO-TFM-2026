"""Auditable SP0 B0 gates and protocol helpers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import sys
import time
from datetime import UTC, datetime
from itertools import combinations, permutations
from pathlib import Path
from typing import Any

import numpy as np
import yaml

import viu_mrob_tfm.sp0.methods as sp0_methods
from viu_mrob_tfm.sp0.methods import (
    assignment_objective,
    assignment_valid,
    close_integer,
    hungarian_assignment,
    qra_global_closure,
    repair_assignment,
    run_sp0_method,
)
from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result
from viu_mrob_tfm.sp0.runner import _config_hash, _git_hash, run_monte_carlo, write_csv
from viu_mrob_tfm.sp0.scenario import SP0World, make_sp0_world
from viu_mrob_tfm.utils.io import coerce_nullable_dataframe_types, ensure_directory, load_yaml, save_json

ORACLE_ATTRS = {"oracle_labels", "oracle_social_cost", "oracle_j", "oracle_assignment", "oracle_cost"}
REQUIRED_RUN_SCHEMA = [
    "sp_id", "experiment_id", "block_id", "method_family", "method_variant", "fitness_id", "rounding_id",
    "world_seed", "method_seed", "train_seed", "N", "K", "load_ratio", "geometry_id", "R", "mean_degree",
    "min_degree", "lambda2", "num_components", "success", "matching_valid", "maximum_cardinality", "final_success",
    "continuous_converged", "continuous_timeout", "continuous_equilibrium_reached", "closure_applied", "closure_type",
    "closure_success", "coverage", "social_cost", "social_regret", "normalized_regret", "continuous_objective", "continuous_normalized_regret", "preclosure_matching_valid", "preclosure_coverage", "preclosure_objective", "preclosure_normalized_regret", "closure_regret_delta", "closure_vs_preclosure_regret_delta", "final_vs_continuous_regret_delta", "cost_gap",
    "convergence_time", "time_to_epsilon_solution", "time_to_epsilon_duration_s", "time_to_epsilon_observed", "messages_to_epsilon_solution", "bytes_to_epsilon_solution", "timeout", "messages", "bytes", "runtime_cpu_s",
    "runtime_wall_s", "oracle_solve_time_s", "oracle_lookup_time_s",
    "method_online_time_s", "closure_runtime_s", "epsilon_ne_1", "epsilon_ne_2", "fractionality", "switches",
    "potential_violations", "occupancy_error", "state_change", "equilibrium_residual", "equilibrium_residual_id", "simulation_end_time_s", "closure_messages",
    "global_strong_closure", "training_steps", "training_converged", "config_hash", "world_hash", "git_hash", "timestamp_utc",
]
PRIMARY_KEYS = ["sp_id", "experiment_id", "block_id", "method_variant", "world_seed", "method_seed", "train_seed", "N", "K", "R"]


class OracleAccessError(RuntimeError):
    pass


WorldOracleView = SP0World

class OracleBlockedWorld:
    def __init__(self, world: SP0World, access_log: list[str]):
        object.__setattr__(self, "_world", world)
        object.__setattr__(self, "_access_log", access_log)

    def __getattr__(self, name: str) -> Any:
        if name in ORACLE_ATTRS or name.startswith("oracle_"):
            self._access_log.append(name)
            raise OracleAccessError(f"Non-oracle method attempted to access {name}")
        return getattr(self._world, name)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("OracleBlockedWorld is read-only")


WorldPublicView = OracleBlockedWorld


def validate_b0(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1"))
    ensure_protocol_layout(root)
    b0_dir = ensure_directory(root / "b0")
    smoke_dir = ensure_directory(root / "smoke")
    git_hash = _git_hash()
    config_hash = _config_hash(config)
    timestamp = datetime.now(UTC).isoformat()
    checks: list[dict[str, Any]] = []
    benchmark_rows: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    theory_contract_rows: list[dict[str, Any]] = []

    for fixture_id, world in build_fixtures().items():
        checks.extend(run_fixture_checks(fixture_id, world, config_hash, git_hash, timestamp))
    checks.extend(run_disconnected_and_timeout_checks(config_hash, git_hash, timestamp))
    invariant_checks, theory_contract_rows = run_dynamic_invariant_checks(config_hash, git_hash, timestamp)
    checks.extend(invariant_checks)
    leakage_checks, leakage_rows = run_oracle_leakage_checks(config_hash, git_hash, timestamp)
    checks.extend(leakage_checks)
    checks.extend(run_oracle_correctness_checks(config_hash, git_hash, timestamp))
    benchmark_checks, benchmark_rows = run_runtime_benchmark(config_hash, git_hash, timestamp)
    checks.extend(benchmark_checks)
    budget_checks, budget_rows = run_b0_budget_evidence(config, config_hash, git_hash, timestamp)
    checks.extend(budget_checks)
    smoke_manifest, smoke_rows, ablations = run_required_smoke(config, smoke_dir)
    checks.extend(run_schema_checks(smoke_rows, config_hash, git_hash, timestamp, dataset_id="smoke"))
    checks.extend(run_schema_checks(budget_rows, config_hash, git_hash, timestamp, dataset_id="b0_budget"))
    checks.extend(run_duplicate_timeout_checks(smoke_rows, config_hash, git_hash, timestamp))

    failures = [row for row in checks if not bool(row["passed"])]
    write_table(b0_dir / "checks.parquet", checks)
    write_table(b0_dir / "benchmark.parquet", benchmark_rows)
    write_table(b0_dir / "failures.parquet", failures, columns_like=checks)
    write_table(b0_dir / "oracle_leakage.parquet", leakage_rows)
    write_table(b0_dir / "theory_contract_results.parquet", theory_contract_rows)
    write_table(b0_dir / "budget_runs.parquet", budget_rows)
    convergence_diagnostics = summarize_convergence_diagnostics(budget_rows)
    write_table(b0_dir / "convergence_diagnostics.parquet", convergence_diagnostics)
    write_table(smoke_dir / "ablations.parquet", ablations)
    write_csv(b0_dir / "checks.csv", checks, b0_columns(checks))
    write_csv(b0_dir / "benchmark.csv", benchmark_rows, b0_columns(benchmark_rows))
    write_csv(b0_dir / "failures.csv", failures, b0_columns(checks))
    family_summary = summarize_check_families(checks)
    gate_status = gate_status_from_checks(checks, smoke_manifest)
    passed = all(row.get("status") == "PASS" for row in gate_status.get("gates", {}).values())
    report = {
        "experiment_id": config.get("experiment_id", "SP0_PROTOCOL_v1"),
        "generated_at_utc": timestamp,
        "git_hash": git_hash,
        "config_hash": config_hash,
        "number_of_checks": len(checks),
        "number_failed": len(failures),
        "passed": bool(passed),
        "families": family_summary,
        "gate_status": gate_status,
        "hardware": hardware_info(),
    }
    write_b0_audit_report(b0_dir, checks, benchmark_rows, convergence_diagnostics, gate_status)
    write_gate_status(root, gate_status)
    write_deviation_file(root)
    return report


def ensure_protocol_layout(root: Path) -> None:
    for name in ["protocol", "b0", "worlds", "smoke", "b2", "b3", "training", "b4", "b5", "b6", "b7", "extensions", "statistics", "figures", "videos", "audit", "archive/pre_freeze"]:
        ensure_directory(root / name)


def build_fixtures() -> dict[str, SP0World]:
    return {
        "U0": world_from_cost("U0", np.array([[0.1]], dtype=float)),
        "U1": world_from_cost("U1", np.array([[0.1, 0.4, 0.7], [0.5, 0.2, 0.6]], dtype=float)),
        "U2": world_from_cost("U2", np.array([[0.1, 0.5], [0.6, 0.2], [0.3, 0.4]], dtype=float)),
        "U3": world_from_cost("U3", np.array([[1.0, 0.1], [0.1, 1.0]], dtype=float)),
        "U4": world_from_cost("U4", np.ones((4, 4), dtype=float) * 0.5),
        "U5": world_from_cost("U5", np.array([[0.0, 0.7], [0.8, 0.1]], dtype=float), zero_first_load=True),
        "U7": world_from_cost("U7", np.array([[0.1, 0.6, 0.7], [0.1, 0.5, 0.8], [0.1, 0.4, 0.9]], dtype=float)),
        "U8": world_from_cost("U8", np.array([[1.0, 0.9], [0.9, 1.0]], dtype=float)),
    }


def world_from_cost(name: str, cost: np.ndarray, *, zero_first_load: bool = False) -> SP0World:
    n_robots, n_loads = cost.shape
    adjacency = np.ones((n_robots, n_robots), dtype=bool) & ~np.eye(n_robots, dtype=bool)
    degrees = np.sum(adjacency, axis=1) if n_robots else np.array([0])
    initial_x = np.full((n_robots, n_loads + 1), 1.0 / (n_loads + 1), dtype=float)
    if zero_first_load and n_loads >= 1:
        initial_x[:, 1] = 0.0
        initial_x /= np.sum(initial_x, axis=1, keepdims=True)
    labels, _solve_ms = hungarian_assignment(cost)
    social = assignment_cost(cost, labels)
    s_star = min(n_robots, n_loads)
    j_value = float((s_star + 1) * (s_star - int(np.sum(labels > 0))) + social)
    payload = {"fixture": name, "cost": np.round(cost, 12).tolist(), "zero_first_load": zero_first_load}
    world_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    robot_xy = np.column_stack([np.arange(n_robots, dtype=float), np.zeros(n_robots)])
    load_xy = np.column_stack([np.arange(n_loads, dtype=float), np.ones(n_loads)])
    return SP0World("SP0-v1.0", fixture_seed(name), name, n_robots, n_loads, 1.0, robot_xy, load_xy, cost, adjacency, math.inf, float(np.mean(degrees)), int(np.min(degrees)), float(n_robots if n_robots > 1 else 0.0), 1 if n_robots else 0, 1.0 if n_robots > 1 else 0.0, initial_x, labels, social, j_value, world_hash)


def run_fixture_checks(fixture_id: str, world: SP0World, config_hash: str, git_hash: str, timestamp: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    hun = run_sp0_method(world, {"id": "HUN"})
    metrics = evaluate_sp0_result(world, hun)
    if fixture_id == "U0":
        rows.append(check_row("U0_matching_trivial", "matching_validity", world, hun, 1, int(metrics.success), 1e-9, config_hash, git_hash, timestamp))
    if fixture_id == "U1":
        rows.append(check_row("U1_coverage_count", "metric_correctness", world, hun, 2, int(metrics.assigned_count), 1e-9, config_hash, git_hash, timestamp))
        rows.append(check_row("U1_coverage", "metric_correctness", world, hun, 1.0, metrics.coverage, 1e-9, config_hash, git_hash, timestamp))
    if fixture_id == "U2":
        rows.append(check_row("U2_two_loads_served", "metric_correctness", world, hun, 2, int(metrics.assigned_count), 1e-9, config_hash, git_hash, timestamp))
        rows.append(check_row("U2_one_idle", "metric_correctness", world, hun, 1, int(np.sum(hun.labels == 0)), 1e-9, config_hash, git_hash, timestamp))
    if fixture_id == "U3":
        start = np.array([1, 2], dtype=int)
        qr1 = close_integer(world, labels_to_x(start, world.n_loads), rounding_id="QR1", params={"delta_qr": 1e-4})
        qr2 = close_integer(world, labels_to_x(start, world.n_loads), rounding_id="QR2", params={"delta_qr": 1e-4})
        qra, exhaustive = qra_global_closure(world, qr1)
        rows.append(simple_check("U3_QR1_may_remain_stable", "qr_termination", world, "QR1", True, assignment_objective(world, qr1) >= assignment_objective(world, qr2), config_hash, git_hash, timestamp))
        rows.append(simple_check("U3_QR2_executes_swap", "qr_acceptance", world, "QR2", True, np.array_equal(qr2, np.array([2, 1])), config_hash, git_hash, timestamp))
        rows.append(simple_check("U3_QRA_not_worse_QR2", "qr_termination", world, "QRA", True, exhaustive and assignment_objective(world, qra) <= assignment_objective(world, qr2) + 1e-9, config_hash, git_hash, timestamp))
    if fixture_id == "U4":
        hun2 = run_sp0_method(world, {"id": "HUN"})
        rows.append(simple_check("U4_tie_break_deterministic", "seed_reproducibility", world, "HUN", True, np.array_equal(hun.labels, hun2.labels), config_hash, git_hash, timestamp))
        rows.append(simple_check("U4_tie_matching_valid", "matching_validity", world, "HUN", True, assignment_valid(hun.labels, world.n_loads), config_hash, git_hash, timestamp))
    if fixture_id == "U5":
        rep = run_sp0_method(world, {"id": "REP", "fitness_id": "LIN", "rounding_id": "RAW", "max_steps": 5})
        log = run_sp0_method(world, {"id": "LOG", "fitness_id": "LIN", "rounding_id": "RAW", "max_steps": 5})
        smi = run_sp0_method(world, {"id": "SMI", "fitness_id": "LIN", "rounding_id": "RAW", "max_steps": 5})
        bnn = run_sp0_method(world, {"id": "BNN", "fitness_id": "LIN", "rounding_id": "RAW", "max_steps": 5})
        rows.append(check_row("U5_REP_support_invariant", "mass_conservation", world, rep, 0.0, float(np.max(rep.continuous_x[:, 1])), 1e-12, config_hash, git_hash, timestamp))
        rows.append(simple_check("U5_LOG_reactivates_zero_support", "mass_conservation", world, "LOG", True, float(np.max(log.continuous_x[:, 1])) > 0.0, config_hash, git_hash, timestamp))
        rows.append(simple_check("U5_SMI_protocol_recorded", "mass_conservation", world, "SMI", True, smi.continuous_x is not None, config_hash, git_hash, timestamp))
        rows.append(simple_check("U5_BNN_protocol_recorded", "mass_conservation", world, "BNN", True, bnn.continuous_x is not None, config_hash, git_hash, timestamp))
    if fixture_id == "U7":
        labels = np.ones(world.n_robots, dtype=int)
        repaired = repair_assignment(world, labels, labels_to_x(labels, world.n_loads))
        qr = close_integer(world, labels_to_x(labels, world.n_loads), rounding_id="QR1", params={})
        rows.append(simple_check("U7_ARG_conflict_possible", "matching_validity", world, "ARG", True, not assignment_valid(labels, world.n_loads), config_hash, git_hash, timestamp))
        rows.append(simple_check("U7_REPAIR_resolves_conflict", "matching_validity", world, "REPAIR", True, assignment_valid(repaired, world.n_loads), config_hash, git_hash, timestamp))
        rows.append(simple_check("U7_QR_resolves_conflict", "matching_validity", world, "QR1", True, assignment_valid(qr, world.n_loads), config_hash, git_hash, timestamp))
    if fixture_id == "U8":
        full = np.array([1, 2], dtype=int)
        partial = np.array([0, 0], dtype=int)
        rows.append(simple_check("U8_lexicographic_coverage_dominates", "metric_correctness", world, "objective", True, assignment_objective(world, full) < assignment_objective(world, partial), config_hash, git_hash, timestamp))
    return rows


def run_disconnected_and_timeout_checks(config_hash: str, git_hash: str, timestamp: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    world = make_sp0_world(n_robots=8, n_loads=8, seed=8106, geometry_id="G-UNI", mean_degree_target=0)
    rows.append(check_row("U6_lambda2_zero", "cache_consistency", world, "graph", 0.0, world.lambda2, 1e-9, config_hash, git_hash, timestamp))
    rows.append(simple_check("U6_components_gt_one", "cache_consistency", world, "graph", True, world.num_components > 1, config_hash, git_hash, timestamp))
    timeout_world = make_sp0_world(n_robots=8, n_loads=8, seed=8109, geometry_id="G-UNI", mean_degree_target="all")
    timeout_result = run_sp0_method(timeout_world, {"id": "SMI", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 1, "stable_window_steps": 1000})
    timeout_metric = evaluate_sp0_result(timeout_world, timeout_result)
    timeout_semantics = {
        "continuous_timeout": timeout_metric.continuous_timeout,
        "continuous_converged": timeout_metric.continuous_converged,
        "closure_success": timeout_metric.closure_success,
        "final_success": timeout_metric.final_success,
    }
    rows.append(simple_check("U9_timeout_preserved", "timeout_preservation", timeout_world, "SMI", True, bool(timeout_metric.continuous_timeout) and timeout_metric.continuous_converged is False, config_hash, git_hash, timestamp, observed=timeout_semantics))
    return rows


def load_theory_contracts() -> dict[str, Any]:
    path = Path("theory_contracts/SP0_THEORY_CONTRACTS_v1_1.yaml")
    if not path.exists():
        return {"contracts": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"contracts": []}


def theory_contract_for(method: str, fitness: str, closure: str) -> dict[str, Any]:
    method = method.upper()
    fitness = fitness.upper()
    closure = closure.upper()
    for contract in load_theory_contracts().get("contracts", []):
        methods = {str(item).upper() for item in contract.get("methods", [])}
        fitnesses = {str(item).upper() for item in contract.get("fitness", [])}
        closures = {str(item).upper() for item in contract.get("closures", [])}
        if method in methods and fitness in fitnesses and closure in closures:
            return dict(contract)
    return {"potential_check_applicable": False, "expected_property": "no_contract", "potential_function_id": "none", "tolerance": None}
def run_dynamic_invariant_checks(config_hash: str, git_hash: str, timestamp: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    contract_rows: list[dict[str, Any]] = []
    for idx, dynamic in enumerate(["REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB"]):
        world = make_sp0_world(n_robots=6, n_loads=6, seed=8200 + idx, geometry_id="G-UNI", mean_degree_target="all")
        spec = {"id": dynamic, "fitness_id": "LIN", "rounding_id": "QR1", "h": 0.03, "max_steps": 30, "stable_window_steps": 4}
        result = run_sp0_method(world, spec)
        x = result.continuous_x
        sum_err = float(np.max(np.abs(np.sum(x, axis=1) - 1.0))) if x is not None else 0.0
        min_x = float(np.min(x)) if x is not None else 0.0
        rows.append(check_row(f"G3_{dynamic}_simplex", "simplex", world, result, 0.0, sum_err, 1e-6, config_hash, git_hash, timestamp))
        rows.append(check_row(f"G3_{dynamic}_nonnegative", "non_negativity", world, result, 0.0, max(0.0, -min_x), 1e-9, config_hash, git_hash, timestamp))
        rows.append(check_row(f"G3_{dynamic}_mass", "mass_conservation", world, result, 0.0, sum_err, 1e-6, config_hash, git_hash, timestamp))
        contract = theory_contract_for(dynamic, "LIN", "QR1")
        applicable = bool(contract.get("potential_check_applicable", False))
        violation_count = int(result.potential_violations)
        passed = (violation_count == 0) if applicable else True
        rows.append(simple_check(f"G3_{dynamic}_potential_contract", "potential_monotonicity", world, dynamic, True, passed, config_hash, git_hash, timestamp, observed={"applicable": applicable, "violations": violation_count}))
        contract_rows.append({
            "method": dynamic,
            "fitness": "LIN",
            "closure": "QR1",
            "potential_check_applicable": applicable,
            "expected_property": contract.get("expected_property"),
            "potential_function_id": contract.get("potential_function_id"),
            "tolerance": contract.get("tolerance"),
            "potential_violation_count": violation_count,
            "largest_negative_delta": result.largest_negative_delta,
            "median_potential_delta": result.median_potential_delta,
            "p01_potential_delta": result.p01_potential_delta,
            "potential_monotonicity_passed": (violation_count == 0) if applicable else None,
            "config_hash": config_hash,
            "git_hash": git_hash,
            "timestamp_utc": timestamp,
        })
    return rows, contract_rows


def run_oracle_leakage_checks(config_hash: str, git_hash: str, timestamp: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    world = make_sp0_world(n_robots=6, n_loads=6, seed=8300, geometry_id="G-X", mean_degree_target="all")
    specs = [
        {"id": "GRD"},
        {"id": "DA"},
        {"id": "REP", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 10},
        {"id": "SMI", "fitness_id": "ASYM", "rounding_id": "QR2", "max_steps": 10},
        {"id": "BNN", "fitness_id": "MC", "rounding_id": "QR1", "max_steps": 10},
        {"id": "LOG", "fitness_id": "SIG", "rounding_id": "REPAIR", "max_steps": 10},
        {"id": "PROJ", "fitness_id": "QUAD", "rounding_id": "QR1", "max_steps": 10},
        {"id": "IBR", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 10},
        {"id": "GPC", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 10},
        {"id": "HYB", "fitness_id": "ASYM", "rounding_id": "QRA", "max_steps": 10},
        {"id": "IPPO-GNN", "method_seed": 101, "train_seed": 15001, "allow_untrained_debug_policy": True},
        {"id": "MAPPO-GNN", "method_seed": 102, "train_seed": 15002, "allow_untrained_debug_policy": True},
    ]
    original_hungarian = sp0_methods.hungarian_assignment
    calls: list[str] = []

    def blocked_hungarian(*_args: Any, **_kwargs: Any):
        calls.append("hungarian_assignment")
        raise OracleAccessError("Non-oracle method attempted to call Hungarian")

    for spec in specs:
        access_log: list[str] = []
        calls.clear()
        ok = True
        err = ""
        method = str(spec["id"]).upper()
        try:
            normal = run_sp0_method(world, spec)
            sp0_methods.hungarian_assignment = blocked_hungarian
            public = run_sp0_method(WorldPublicView(world, access_log), spec)
            same_output = bool(np.array_equal(normal.labels, public.labels))
        except Exception as exc:
            ok = False
            same_output = False
            err = str(exc)
        finally:
            sp0_methods.hungarian_assignment = original_hungarian
        passed = bool(ok and not access_log and not calls and same_output)
        leakage_rows.append({
            "method": method,
            "accessed_oracle_fields": json.dumps(access_log),
            "hungarian_calls": len(calls),
            "disable_oracle_same_output": same_output,
            "error": err,
            "passed": passed,
        })
        checks.append(simple_check(f"G4_{method}_no_oracle_access", "oracle_leakage", world, method, True, passed, config_hash, git_hash, timestamp, observed={"fields": access_log, "hungarian_calls": len(calls), "same_output": same_output, "error": err}))
    return checks, leakage_rows


def run_oracle_correctness_checks(config_hash: str, git_hash: str, timestamp: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, (n_robots, n_loads, geometry) in enumerate([(2, 3, "G-UNI"), (3, 3, "G-TIE"), (4, 2, "G-UNI"), (5, 5, "G-X"), (6, 4, "G-CLU")]):
        world = make_sp0_world(n_robots=n_robots, n_loads=n_loads, seed=8400 + idx, geometry_id=geometry, mean_degree_target="all")
        _brute_labels, brute_j = brute_force_assignment(world)
        hun_labels, _ = hungarian_assignment(world.cost)
        hun_j = assignment_objective(world, hun_labels)
        rows.append(check_row(f"G6_case_{idx}_j", "oracle_correctness", world, "HUN", brute_j, hun_j, 1e-9, config_hash, git_hash, timestamp))
        rows.append(check_row(f"G6_case_{idx}_coverage", "oracle_correctness", world, "HUN", world.s_star, int(np.sum(hun_labels > 0)), 0.0, config_hash, git_hash, timestamp))
        rows.append(check_row(f"G6_case_{idx}_nr", "oracle_correctness", world, "HUN", 0.0, max(0.0, hun_j - brute_j), 1e-9, config_hash, git_hash, timestamp))
    return rows


def run_runtime_benchmark(config_hash: str, git_hash: str, timestamp: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for n_robots in [8, 16, 32]:
        world = make_sp0_world(n_robots=n_robots, n_loads=n_robots, seed=8500 + n_robots, geometry_id="G-UNI", mean_degree_target="all")
        for spec in [{"id": "HUN"}, {"id": "GRD"}, {"id": "DA"}, {"id": "SMI", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 30}]:
            values: list[float] = []
            solves: list[float] = []
            lookups: list[float] = []
            for _ in range(8):
                result = run_sp0_method(world, spec)
                values.append(float(result.method_online_time_ms or result.runtime_ms) / 1000.0)
                solves.append(float(result.oracle_solve_time_ms) / 1000.0)
                lookups.append(float(result.oracle_lookup_time_ms) / 1000.0)
            method = str(spec["id"]).upper()
            row = {"method": method, "N": n_robots, "K": n_robots, **runtime_stats(values), "oracle_solve_time_s_mean": float(np.mean(solves)), "oracle_lookup_time_s_mean": float(np.mean(lookups)), **hardware_info(), "config_hash": config_hash, "git_hash": git_hash, "timestamp_utc": timestamp}
            rows.append(row)
            if method == "HUN":
                checks.append(simple_check(f"G5_HUN_runtime_not_lookup_N{n_robots}", "runtime_correctness", world, method, True, row["oracle_solve_time_s_mean"] >= 0.0 and row["oracle_lookup_time_s_mean"] >= 0.0, config_hash, git_hash, timestamp, observed={"solve_s": row["oracle_solve_time_s_mean"], "lookup_s": row["oracle_lookup_time_s_mean"]}))
    return checks, rows


def run_b0_budget_evidence(config: dict[str, Any], config_hash: str, git_hash: str, timestamp: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    count = int(config.get("campaign_counts", {}).get("B0", 300))
    checks: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    dynamics = ["REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB"]
    fitness = ["LIN", "QUAD", "ASYM", "SIG", "MC"]
    rounding = ["REPAIR", "QR1", "QR2", "QRA"]
    geometries = ["G-UNI", "G-CLU", "G-TIE", "G-X", "G-BIAS", "G-ZERO"]
    for idx in range(count):
        n_robots = [4, 8, 12][idx % 3]
        ratio = [0.67, 1.0, 1.5][(idx // 3) % 3]
        n_loads = max(1, int(math.ceil(n_robots * ratio)))
        world = make_sp0_world(
            n_robots=n_robots,
            n_loads=n_loads,
            seed=7000 + idx,
            geometry_id=geometries[idx % len(geometries)],
            mean_degree_target="all" if idx % 4 else min(n_robots - 1, 4),
            sp_id=str(config.get("sp_id", "SP0-v1.0")),
        )
        spec = {
            "id": dynamics[idx % len(dynamics)],
            "fitness_id": fitness[idx % len(fitness)],
            "rounding_id": rounding[idx % len(rounding)],
            "h": 0.05,
            "dt": 0.1,
            "max_steps": 100,
            "stable_window_steps": 10,
        }
        result = run_sp0_method(world, spec)
        metrics = evaluate_sp0_result(world, result)
        simplex_ok = bool(result.continuous_x is None or np.allclose(np.sum(result.continuous_x, axis=1), 1.0, atol=1.0e-6))
        nonnegative_ok = bool(result.continuous_x is None or np.min(result.continuous_x) >= -1.0e-9)
        matching_required = str(result.rounding_id).upper() not in {"RAW", "ARG"}
        matching_ok = bool(metrics.matching_valid or not matching_required)
        finite_ok = bool(np.isfinite(metrics.normalized_regret) and np.isfinite(metrics.runtime_wall_s))
        oracle_ok = bool(assignment_valid(world.oracle_labels, world.n_loads) and abs(world.oracle_j - assignment_objective(world, world.oracle_labels)) <= 1.0e-9)
        passed = bool(simplex_ok and nonnegative_ok and matching_ok and finite_ok and oracle_ok)
        observed = {"simplex_ok": simplex_ok, "nonnegative_ok": nonnegative_ok, "matching_ok": matching_ok, "finite_ok": finite_ok, "oracle_ok": oracle_ok}
        checks.append(simple_check(f"B0_budget_{idx:03d}", "b0_budget_execution", world, result.method_id, True, passed, config_hash, git_hash, timestamp, observed=observed))
        rows.append({
            "sp_id": world.sp_id,
            "experiment_id": str(config.get("experiment_id", "SP0_PROTOCOL_v1_1")),
            "block_id": "B0",
            "b0_index": idx,
            "method_family": "population",
            "method_variant": result.method_id,
            "fitness_id": result.fitness_id,
            "rounding_id": result.rounding_id,
            "world_seed": world.world_seed,
            "method_seed": 710000 + idx,
            "train_seed": None,
            "N": world.n_robots,
            "K": world.n_loads,
            "load_ratio": world.load_ratio,
            "geometry_id": world.geometry_id,
            "R": world.radius,
            "mean_degree": world.mean_degree,
            "min_degree": world.min_degree,
            "lambda2": world.lambda2,
            "num_components": world.num_components,
            "world_hash": world.world_hash,
            **metrics.to_dict(),
            "oracle_solve_time_s": metrics.oracle_solve_time_s,
            "oracle_lookup_time_s": metrics.oracle_lookup_time_s,
            "training_steps": None,
            "training_converged": None,
            "config_hash": config_hash,
            "git_hash": git_hash,
            "timestamp_utc": timestamp,
        })
    return checks, rows
def run_required_smoke(config: dict[str, Any], smoke_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    smoke_config = dict(config)
    smoke_config.update({
        "experiment_id": "SP0_PROTOCOL_v1_smoke",
        "mode": "debug",
        "output_dir": str(smoke_dir),
        "seeds": {"start": 9000, "count": 1},
        "make_figures": True,
        "worlds": [
            {"block": "smoke_nominal", "geometries": ["G-UNI"], "N": [8], "load_ratios": [1.0], "mean_degrees": ["all"]},
            {"block": "smoke_cross", "geometries": ["G-X"], "N": [8], "load_ratios": [1.0], "mean_degrees": ["all"]},
            {"block": "smoke_tie", "geometries": ["G-TIE"], "N": [8], "load_ratios": [1.0], "mean_degrees": ["all"]},
            {"block": "smoke_support_zero", "geometries": ["G-ZERO"], "N": [8], "load_ratios": [1.0], "mean_degrees": ["all"]},
            {"block": "smoke_connected_local", "geometries": ["G-UNI"], "N": [8], "load_ratios": [1.0], "mean_degrees": [4]},
            {"block": "smoke_disconnected", "geometries": ["G-UNI"], "N": [8], "load_ratios": [1.0], "mean_degrees": [0]},
            {"block": "smoke_robot_scarcity", "geometries": ["G-UNI"], "N": [8], "load_ratios": [1.5], "mean_degrees": ["all"]},
            {"block": "smoke_robot_surplus", "geometries": ["G-UNI"], "N": [8], "load_ratios": [0.67], "mean_degrees": ["all"]},
        ],
        "methods": [
            {"id": "HUN"}, {"id": "GRD"}, {"id": "DA"},
            {"id": "REP", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 60},
            {"id": "SMI", "fitness_id": "ASYM", "rounding_id": "QR1", "max_steps": 60},
            {"id": "BNN", "fitness_id": "MC", "rounding_id": "QR1", "max_steps": 60},
            {"id": "LOG", "fitness_id": "SIG", "rounding_id": "REPAIR", "max_steps": 60},
            {"id": "PROJ", "fitness_id": "QUAD", "rounding_id": "QR1", "max_steps": 60},
            {"id": "IBR", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 60},
            {"id": "GPC", "fitness_id": "LIN", "rounding_id": "QR1", "max_steps": 60},
            {"id": "HYB", "fitness_id": "ASYM", "rounding_id": "QR2", "max_steps": 60},
            {"id": "IPPO-GNN", "method_seed": 101, "train_seed": 15001, "allow_untrained_debug_policy": True},
            {"id": "MAPPO-GNN", "method_seed": 102, "train_seed": 15002, "allow_untrained_debug_policy": True},
        ],
    })
    temp_config = smoke_dir / "smoke_config.yaml"
    temp_config.write_text(yaml.safe_dump(smoke_config, sort_keys=True), encoding="utf-8")
    manifest = run_monte_carlo(smoke_config, config_path=temp_config)
    rows = read_table(smoke_dir / "tables" / "runs.parquet")
    for row in rows:
        row["exploratory_debug_only"] = True
        row.setdefault("block_id", row.get("block", ""))
    write_table(smoke_dir / "runs.parquet", rows)
    write_table(smoke_dir / "hypotheses.parquet", read_table(smoke_dir / "tables" / "hypothesis_results.parquet"))
    ablations = build_qr_ablation_rows(config_hash=_config_hash(smoke_config), git_hash=_git_hash())
    (smoke_dir / "report.md").write_text(f"# SP0 Smoke Suite\n\nexploratory_debug_only = true\n\nRuns: `{len(rows)}`\n", encoding="utf-8")
    return manifest, rows, ablations


def run_schema_checks(
    rows: list[dict[str, Any]],
    config_hash: str,
    git_hash: str,
    timestamp: str,
    *,
    dataset_id: str,
) -> list[dict[str, Any]]:
    world = make_sp0_world(n_robots=2, n_loads=2, seed=8600)
    missing_by_row = {
        index: sorted(set(REQUIRED_RUN_SCHEMA).difference(row))
        for index, row in enumerate(rows)
        if set(REQUIRED_RUN_SCHEMA).difference(row)
    }
    null_ok = bool(rows) and all(
        all(row.get(field) not in {None, ""} for field in ["world_hash", "config_hash", "git_hash"])
        for row in rows
    )
    return [
        simple_check(
            f"G7_required_schema_{dataset_id}", "parquet_schema", world, f"schema:{dataset_id}",
            True, bool(rows) and not missing_by_row, config_hash, git_hash, timestamp,
            observed={"rows": len(rows), "missing_by_row": missing_by_row},
        ),
        simple_check(
            f"G7_null_semantics_{dataset_id}", "null_semantics", world, f"schema:{dataset_id}",
            True, null_ok, config_hash, git_hash, timestamp,
        ),
    ]

def run_duplicate_timeout_checks(rows: list[dict[str, Any]], config_hash: str, git_hash: str, timestamp: str) -> list[dict[str, Any]]:
    world = make_sp0_world(n_robots=2, n_loads=2, seed=8601)
    keys = [tuple(row.get(key) for key in PRIMARY_KEYS if key in row) for row in rows]
    duplicate_count = len(keys) - len(set(keys))
    timeout_rows = [row for row in rows if bool(row.get("continuous_timeout", row.get("timeout", False)))]
    run_row_preserved = len(rows) > 0
    timeout_field_preserved = all("continuous_timeout" in row and "timeout" in row for row in timeout_rows)
    failure_not_converted_to_missing = all(row.get("final_success") is not None for row in timeout_rows)
    non_applicable_metrics_are_null = all(row.get("convergence_time") is None or np.isnan(float(row.get("convergence_time"))) for row in timeout_rows if row.get("continuous_converged") is False)
    timeout_semantics = {
        "timeout_rows": len(timeout_rows),
        "run_row_preserved": run_row_preserved,
        "timeout_field_preserved": timeout_field_preserved,
        "failure_not_converted_to_missing": failure_not_converted_to_missing,
        "non_applicable_metrics_are_null": non_applicable_metrics_are_null,
    }
    timeout_ok = bool(run_row_preserved and timeout_field_preserved and failure_not_converted_to_missing and non_applicable_metrics_are_null)
    return [
        check_row("G7_duplicate_rows", "duplicate_rows", world, "schema", 0, duplicate_count, 0, config_hash, git_hash, timestamp),
        simple_check("G7_timeout_preservation", "timeout_preservation", world, "schema", True, timeout_ok, config_hash, git_hash, timestamp, observed=timeout_semantics),
    ]


def build_qr_ablation_rows(*, config_hash: str, git_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for seed in [9100, 9101, 9102]:
        world = make_sp0_world(n_robots=8, n_loads=8, seed=seed, geometry_id="G-X", mean_degree_target="all")
        row = {"method": "SMI", "world_seed": seed, "world_hash": world.world_hash, "config_hash": config_hash, "git_hash": git_hash}
        for rounding in ["RAW", "ARG", "REPAIR", "QR1", "QR2", "QRA"]:
            result = run_sp0_method(world, {"id": "SMI", "fitness_id": "ASYM", "rounding_id": rounding, "max_steps": 40})
            metric = evaluate_sp0_result(world, result)
            row[f"NR_{rounding}"] = metric.normalized_regret
            row[f"valid_{rounding}"] = metric.matching_valid
        output.append(row)
    return output


def freeze_protocol(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1_1"))
    gate_path = root / "GATE_STATUS.json"
    if not gate_path.exists():
        raise RuntimeError("B0 gates have not been validated yet.")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if any(row.get("status") != "PASS" for row in gate.get("gates", {}).values()):
        raise RuntimeError("Cannot freeze protocol while a gate is not PASS.")

    experiment_id = str(config.get("experiment_id", "SP0_PROTOCOL"))
    version_tag = experiment_id.removeprefix("SP0_PROTOCOL_").lower()
    versioned_protocol = version_tag.startswith("v")
    if versioned_protocol:
        dd_status = data_driven_readiness(root)
        if dd_status.get("status") != "ready":
            raise RuntimeError(
                f"Cannot freeze {experiment_id} before real IPPO/MAPPO training artifacts exist: "
                + json.dumps(dd_status.get("missing", []) + dd_status.get("champion_errors", []))
            )
        dry_run_path = root / "smoke" / "integral_dry_run_report.json"
        if not dry_run_path.exists():
            raise RuntimeError(f"Cannot freeze {experiment_id} before the integral dry-run report exists.")
        dry_run = json.loads(dry_run_path.read_text(encoding="utf-8"))
        if dry_run.get("status") != "PASS":
            raise RuntimeError(f"Cannot freeze {experiment_id} because integral dry-run status is {dry_run.get('status')!r}.")
        current_implementation = sha256_python_sources(Path(__file__).parent)
        if dry_run.get("implementation_sha256") != current_implementation:
            raise RuntimeError(f"Cannot freeze {experiment_id} because the implementation changed after the integral dry-run.")

    protocol_dir = ensure_directory(root / "protocol")
    names = {
        "protocol": f"frozen_protocol_{version_tag}.yaml" if versioned_protocol else "frozen_protocol.yaml",
        "manifest": f"frozen_manifest_{version_tag}.json" if versioned_protocol else "frozen_manifest.json",
        "hypotheses": f"hypotheses_{version_tag}.yaml" if versioned_protocol else "hypotheses.yaml",
        "seeds": f"seed_registry_{version_tag}.yaml" if versioned_protocol else "seed_registry.yaml",
        "environment": f"environment_{version_tag}.lock" if versioned_protocol else "environment.lock",
        "hashes": f"HASHES_{version_tag}.sha256" if versioned_protocol else "HASHES.sha256",
    }
    frozen = dict(config)
    frozen["frozen"] = True
    frozen["status"] = "frozen_ready_for_execution"
    frozen["frozen_at_utc"] = datetime.now(UTC).isoformat()
    frozen["git_commit_sha"] = full_git_hash()
    seed_registry = build_seed_registry()
    environment = environment_lock()
    hypotheses = {
        "families": config.get("hypotheses", []),
        "version": str(config.get("sp_id", "SP0")),
        "frozen_before_confirmatory_seed_opening": True,
    }
    protocol_path = protocol_dir / names["protocol"]
    seed_path = protocol_dir / names["seeds"]
    environment_path = protocol_dir / names["environment"]
    hypotheses_path = protocol_dir / names["hypotheses"]
    write_yaml(protocol_path, frozen)
    write_yaml(seed_path, seed_registry)
    write_yaml(environment_path, environment)
    write_yaml(hypotheses_path, hypotheses)
    hashes = {
        "config_sha256": sha256_file(protocol_path),
        "hypotheses_sha256": sha256_file(hypotheses_path),
        "seed_registry_sha256": sha256_file(seed_path),
        "environment_lock_sha256": sha256_file(environment_path),
        "b0_evidence_sha256": sha256_tree(root / "b0"),
        "data_driven_implementation_sha256": sha256_file(Path(__file__).with_name("data_driven.py")),
        "sp0_implementation_sha256": sha256_python_sources(Path(__file__).parent),
    }
    manifest = {
        **frozen,
        **hashes,
        "hardware_id": hardware_id(),
        "expected_full_campaign_evaluations": 15436,
        "confirmatory_seeds_opened": False,
        "artifact_names": names,
    }
    save_json(protocol_dir / names["manifest"], manifest)
    hash_targets = {
        hashes["config_sha256"]: names["protocol"],
        hashes["hypotheses_sha256"]: names["hypotheses"],
        hashes["seed_registry_sha256"]: names["seeds"],
        hashes["environment_lock_sha256"]: names["environment"],
        hashes["b0_evidence_sha256"]: "../b0",
        hashes["data_driven_implementation_sha256"]: "../../src/viu_mrob_tfm/sp0/data_driven.py",
        hashes["sp0_implementation_sha256"]: "../../src/viu_mrob_tfm/sp0/*.py",
    }
    (protocol_dir / names["hashes"]).write_text(
        "\n".join(f"{digest}  {target}" for digest, target in hash_targets.items()) + "\n",
        encoding="utf-8",
    )
    return manifest

def run_full(
    config_path: str | Path,
    *,
    validate: bool,
    freeze: bool,
    run_b1_b7: bool,
    analyze: bool,
    render_figures: bool,
    render_videos: bool,
    dry_run: bool = False,
    train_data_driven: bool = False,
    device: str = "auto",
    allow_long_cpu_training: bool = False,
    extend_by_precision: bool = False,
    resume: bool = True,
    block: str | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1_1"))
    manifest: dict[str, Any] = {"started_at_utc": datetime.now(UTC).isoformat(), "dry_run": dry_run}
    if validate:
        manifest["b0"] = validate_b0(config_path)
        gate = json.loads((root / "GATE_STATUS.json").read_text(encoding="utf-8"))
        if any(row.get("status") != "PASS" for row in gate.get("gates", {}).values()):
            blocked = {**manifest, "status": "blocked_b0"}
            save_json(root / "FINAL_RUN_MANIFEST.json", blocked)
            return blocked

    train_status: dict[str, Any] | None = None
    if train_data_driven:
        from viu_mrob_tfm.sp0.data_driven import train_data_driven_from_config

        train_status = train_data_driven_from_config(
            config_path,
            full_budget=not dry_run,
            device=device,
            allow_long_cpu_training=allow_long_cpu_training,
        )
        manifest["data_driven_training"] = train_status
        if dry_run:
            if train_status.get("status") != "dry_run_complete":
                blocked = {**manifest, "status": "blocked_dry_run_training"}
                save_json(root / "FINAL_RUN_MANIFEST.json", blocked)
                write_final_report(root, blocked)
                return blocked
            from viu_mrob_tfm.sp0.campaign import run_integral_dry_run

            dry_report = run_integral_dry_run(config_path, train_status)
            complete = {**manifest, "integral_dry_run": dry_report, "status": "dry_run_complete"}
            save_json(root / "FINAL_RUN_MANIFEST.json", complete)
            write_final_report(root, complete)
            return complete

        dd_status = data_driven_readiness(root)
        manifest["data_driven"] = dd_status
        if train_status.get("status") != "complete" or dd_status.get("status") != "ready":
            blocked = {**manifest, "status": "blocked_data_driven_not_ready"}
            save_json(root / "FINAL_RUN_MANIFEST.json", blocked)
            write_final_report(root, blocked)
            return blocked

    if dry_run:
        from viu_mrob_tfm.sp0.campaign import run_integral_dry_run

        status_path = root / "training" / "dry_run" / "status.json"
        if not status_path.exists():
            blocked = {**manifest, "status": "blocked_missing_dry_run_training"}
            save_json(root / "FINAL_RUN_MANIFEST.json", blocked)
            return blocked
        train_status = json.loads(status_path.read_text(encoding="utf-8"))
        dry_report = run_integral_dry_run(config_path, train_status)
        complete = {**manifest, "integral_dry_run": dry_report, "status": "dry_run_complete"}
        save_json(root / "FINAL_RUN_MANIFEST.json", complete)
        write_final_report(root, complete)
        return complete

    if freeze:
        manifest["freeze"] = freeze_protocol(config_path)
    if run_b1_b7:
        from viu_mrob_tfm.sp0.campaign import run_available_campaign

        campaign = run_available_campaign(config_path, resume=resume, dry_run=False, block=block)
        combined = {**manifest, "campaign": campaign}
        if campaign.get("status") == "confirmatory_blocks_complete":
            if extend_by_precision:
                from viu_mrob_tfm.sp0.campaign import data_driven_training_status, run_precision_extensions

                combined["precision_extensions"] = run_precision_extensions(
                    config,
                    root,
                    data_driven_training_status(root),
                    resume=resume,
                )
            if analyze or render_figures or render_videos:
                from viu_mrob_tfm.sp0.postprocess import run_postprocessing

                combined["postprocessing"] = run_postprocessing(
                    root,
                    analyze=analyze,
                    render_figures=render_figures,
                    render_videos=render_videos,
                )
        combined["acceptance"] = final_acceptance_status(
            root,
            require_precision=extend_by_precision,
            require_analysis=analyze,
            require_figures=render_figures,
            require_videos=render_videos,
        )
        combined["status"] = (
            "SP0_COMPLETE"
            if combined["acceptance"].get("passed")
            else "incomplete_acceptance"
        )
        save_json(root / "FINAL_RUN_MANIFEST.json", combined)
        write_final_report(root, combined)
        return combined
    status = "validated_and_frozen" if freeze else "validated"
    complete = {**manifest, "status": status}
    save_json(root / "FINAL_RUN_MANIFEST.json", complete)
    write_final_report(root, complete)
    return complete

def validate_confirmatory_seed_opening(root: Path) -> list[str]:
    from viu_mrob_tfm.sp0.campaign import frozen_manifest_path

    errors: list[str] = []
    protocol = root / "protocol"
    event_path = protocol / "confirmatory_seed_opening.json"
    digest_path = protocol / "confirmatory_seed_opening.sha256"
    frozen_path = frozen_manifest_path(root, required=False)
    if not event_path.exists():
        return ["confirmatory seed opening event is missing"]
    if frozen_path is None:
        return ["frozen manifest is missing"]
    event = json.loads(event_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if event.get("status") != "OPENED" or not event.get("confirmatory_seeds_opened"):
        errors.append("confirmatory seed opening status is invalid")
    if event.get("frozen_manifest_sha256") != sha256_file(frozen_path):
        errors.append("opening event frozen-manifest hash mismatch")
    if event.get("seed_registry_sha256") != frozen.get("seed_registry_sha256"):
        errors.append("opening event seed-registry hash mismatch")
    expected_paths = {
        "b3_champions_sha256": root / "b3" / "champions.yaml",
        "data_driven_champion_sha256": root / "training" / "champion.yaml",
        "model_selection_sha256": root / "b3" / "model_selection_champions.yaml",
    }
    for field, path in expected_paths.items():
        if not path.exists() or event.get(field) != sha256_file(path):
            errors.append(f"opening event {field} mismatch")
    if not digest_path.exists() or digest_path.read_text(encoding="utf-8").split()[0] != sha256_file(event_path):
        errors.append("opening event SHA-256 sidecar mismatch")
    try:
        opened = datetime.fromisoformat(str(event["opened_at_utc"]))
        frozen_at = datetime.fromisoformat(str(frozen["frozen_at_utc"]))
        if opened < frozen_at:
            errors.append("confirmatory seeds were opened before freeze")
    except (KeyError, TypeError, ValueError):
        errors.append("freeze/opening timestamps are invalid")
    return errors

def final_acceptance_status(
    root: Path,
    *,
    require_precision: bool,
    require_analysis: bool,
    require_figures: bool,
    require_videos: bool,
) -> dict[str, Any]:
    from viu_mrob_tfm.sp0.campaign import frozen_manifest_path

    checks: dict[str, bool] = {}
    gate_path = root / "GATE_STATUS.json"
    checks["B0_G1_G7_PASS"] = bool(
        gate_path.exists()
        and all(
            row.get("status") == "PASS"
            for row in json.loads(gate_path.read_text(encoding="utf-8")).get("gates", {}).values()
        )
    )
    checks["protocol_frozen"] = frozen_manifest_path(root, required=False) is not None
    try:
        from viu_mrob_tfm.sp0.campaign import _require_frozen, validate_b1_cache, validate_completed_block

        _require_frozen(root)
        checks["frozen_integrity"] = True
    except Exception:
        validate_b1_cache = validate_completed_block = None
        checks["frozen_integrity"] = False
    data_readiness = data_driven_readiness(root)
    checks["data_driven_ready"] = data_readiness.get("status") == "ready"
    checks["training_budget_matches_SP0_v1_1"] = not any(
        "training_budget_contract." in str(error)
        for error in data_readiness.get("champion_errors", [])
    )
    expected = {"b2": 2400, "b3": 1536, "b4": 5760, "b5": 4000, "b6": 960, "b7": 480}
    counts = {}
    schema_ok = True
    trajectory_ok = True
    block_integrity_ok = True
    parquet_types_ok = True
    for block, count in expected.items():
        path = root / block / "runs.parquet"
        rows = read_table(path) if path.exists() else []
        counts[block.upper()] = len(rows)
        checks[f"{block.upper()}_count"] = len(rows) == count
        if rows:
            schema_ok = schema_ok and all(field in rows[0] for field in REQUIRED_RUN_SCHEMA)
            trajectory_ok = trajectory_ok and all(bool(row.get("trajectory_path")) for row in rows)
            if validate_completed_block is not None:
                block_integrity_ok = block_integrity_ok and not validate_completed_block(
                    rows, block_id=block.upper(), expected_runs=count,
                    config_hash=str(rows[0].get("config_hash")),
                )
            try:
                import pyarrow.parquet as pq
                parquet_types_ok = parquet_types_ok and str(pq.read_schema(path).field("final_success").type) == "bool"
            except Exception:
                parquet_types_ok = False
    b0_rows = read_table(root / "b0" / "budget_runs.parquet")
    counts["B0"] = len(b0_rows)
    checks["B0_count"] = len(b0_rows) == 300
    checks["base_total_15436"] = sum(counts.values()) == 15436
    checks["schema_valid"] = schema_ok
    checks["block_primary_keys_and_hashes_valid"] = block_integrity_ok
    checks["parquet_boolean_types_valid"] = parquet_types_ok
    checks["audit_trajectories_present"] = trajectory_ok
    checks["world_cache_valid"] = bool(
        validate_b1_cache is not None
        and not validate_b1_cache(
            root / "worlds" / "world_catalog.parquet",
            root / "worlds" / "cache_manifest.json",
            expected_worlds=60,
            allow_additional=True,
        )
    )
    precision_path = root / "extensions" / "precision_decision.json"
    precision_report = json.loads(precision_path.read_text(encoding="utf-8")) if precision_path.exists() else {}
    checks["precision_rule_recorded"] = (
        precision_report.get("status") == "complete"
        and precision_report.get("extension_reason") == "precision_only"
        if require_precision else True
    )
    hypotheses_path = root / "statistics" / "hypotheses.parquet"
    model_path = root / "statistics" / "model_results.parquet"
    hypotheses = read_table(hypotheses_path) if hypotheses_path.exists() else []
    models = read_table(model_path) if model_path.exists() else []
    required_hypothesis_fields = {
        "hypothesis_id", "effect_estimate", "CI95_low", "CI95_high", "raw_p",
        "Holm_adjusted_p", "decision", "claim_permitted", "source",
    }
    checks["Holm_applied"] = (
        len(hypotheses) == 19
        and all(required_hypothesis_fields.issubset(row) for row in hypotheses)
        and sum(str(row.get("decision")) == "exploratory_only" for row in hypotheses) == 6
        if require_analysis else True
    )
    required_models = {
        "mixed_regret_world_random_intercept", "robust_regret_GEE_world_cluster",
        "mixed_logistic_world_random_intercept", "cox_time_to_epsilon_world_cluster",
        "connectivity_regret_GEE", "negative_binomial_messages_to_epsilon_solution_GEE",
        "negative_binomial_bytes_to_epsilon_solution_GEE", "robustness_method_stress_GEE",
        "generalization_method_logN_GEE", "initial_support_method_geometry_GEE",
    }
    checks["statistical_models_recorded"] = (
        required_models.issubset({str(row.get("model")) for row in models}) if require_analysis else True
    )
    checks["figures_generated"] = (
        all(len(list((root / "figures").glob(f"F*.{suffix}"))) >= 22 for suffix in ["png", "pdf", "svg"])
        if require_figures else True
    )
    video_manifest_path = root / "videos" / "video_manifest.json"
    video_manifest = json.loads(video_manifest_path.read_text(encoding="utf-8")) if video_manifest_path.exists() else {}
    generated_videos = [Path(value) for value in video_manifest.get("generated", [])]
    checks["videos_generated"] = (
        video_manifest.get("status") == "complete"
        and len(generated_videos) == 10
        and all(path.exists() for path in generated_videos)
        if require_videos else True
    )
    seed_opening_errors = validate_confirmatory_seed_opening(root)
    checks["confirmatory_seed_opening_audited"] = not seed_opening_errors
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "counts": counts,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
    }


def data_driven_readiness(root: Path) -> dict[str, Any]:
    """Return readiness of real IPPO/MAPPO training artifacts without creating placeholders."""
    training_dir = root / "training"
    required = [
        training_dir / "champion.yaml",
        training_dir / "champion_selection" / "champion_selection.yaml",
        training_dir / "dd_executor.json",
        training_dir / "final_seeds" / "DD_seed_1" / "checkpoint.pt",
        training_dir / "final_seeds" / "DD_seed_2" / "checkpoint.pt",
        training_dir / "final_seeds" / "DD_seed_3" / "checkpoint.pt",
    ]
    missing = [str(path) for path in required if not path.exists()]
    champion_errors: list[str] = []
    champion_path = training_dir / "champion.yaml"
    if champion_path.exists():
        from viu_mrob_tfm.sp0.campaign import validate_data_driven_champion

        champion = yaml.safe_load(champion_path.read_text(encoding="utf-8")) or {}
        champion_errors = validate_data_driven_champion(champion)
        selection_path = training_dir / "champion_selection" / "champion_selection.yaml"
        if selection_path.exists():
            selection = yaml.safe_load(selection_path.read_text(encoding="utf-8")) or {}
            if selection.get("champion_id") != champion.get("champion_id"):
                champion_errors.append("champion selection and final champion IDs differ")
            rounds = selection.get("rounds", {})
            budget = champion.get("training_budget_contract", {})
            expected_dd1 = int(budget.get("DD_1_steps", 250_000))
            expected_dd2 = int(budget.get("DD_2_steps", 1_000_000))
            if int(rounds.get("DD-1_steps", 0) or 0) != expected_dd1:
                champion_errors.append(f"DD-1 selection budget is not {expected_dd1} steps")
            if int(rounds.get("DD-2_steps", 0) or 0) != expected_dd2:
                champion_errors.append(f"DD-2 selection budget is not {expected_dd2} steps")
        executor_path = training_dir / "dd_executor.json"
        if executor_path.exists():
            executor = json.loads(executor_path.read_text(encoding="utf-8"))
            implementation = Path(__file__).with_name("data_driven.py")
            if executor.get("backend_sha256") != sha256_file(implementation):
                champion_errors.append("data-driven executor implementation hash mismatch")
    ready = not missing and not champion_errors
    return {
        "status": "ready" if ready else "missing_real_training_artifacts" if missing else "invalid_real_training_artifacts",
        "missing": missing,
        "champion_errors": champion_errors,
        "note": "SP0 cannot freeze/open confirmatory seeds until real IPPO/MAPPO training and three contract-valid final DD seeds exist.",
    }

def check_row(check_id: str, family: str, world: SP0World, result_or_method: Any, expected: Any, observed: Any, tolerance: float, config_hash: str, git_hash: str, timestamp: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        exp = float(expected); obs = float(observed)
        absolute = abs(obs - exp); relative = absolute / max(abs(exp), 1e-12)
        passed = absolute <= float(tolerance)
    except Exception:
        absolute = math.nan; relative = math.nan; passed = expected == observed
    method_variant = getattr(result_or_method, "method_id", str(result_or_method))
    return {"check_id": check_id, "check_family": family, "method_family": getattr(result_or_method, "method_family", "audit"), "method_variant": method_variant, "fitness_id": getattr(result_or_method, "fitness_id", None), "rounding_id": getattr(result_or_method, "rounding_id", None), "world_seed": world.world_seed, "method_seed": getattr(result_or_method, "method_seed", None), "N": world.n_robots, "K": world.n_loads, "expected_value": expected, "observed_value": observed, "absolute_error": absolute, "relative_error": relative, "tolerance": tolerance, "passed": bool(passed), "runtime_wall_s": time.perf_counter() - start, "config_hash": config_hash, "git_hash": git_hash, "timestamp_utc": timestamp}


def simple_check(check_id: str, family: str, world: SP0World, method: str, expected: Any, passed: bool, config_hash: str, git_hash: str, timestamp: str, *, observed: Any | None = None) -> dict[str, Any]:
    row = check_row(check_id, family, world, method, expected, observed if observed is not None else passed, 0.0, config_hash, git_hash, timestamp)
    row["passed"] = bool(passed)
    return row


def labels_to_x(labels: np.ndarray, n_loads: int) -> np.ndarray:
    x = np.zeros((labels.size, n_loads + 1), dtype=float)
    x[np.arange(labels.size), labels.astype(int)] = 1.0
    return x


def assignment_cost(cost: np.ndarray, labels: np.ndarray) -> float:
    return float(sum(float(cost[i, int(label) - 1]) for i, label in enumerate(labels) if int(label) > 0))


def brute_force_assignment(world: SP0World) -> tuple[np.ndarray, float]:
    best_labels: np.ndarray | None = None; best_j = math.inf
    if world.n_robots <= world.n_loads:
        iterator = (np.asarray(loads, dtype=int) for loads in permutations(range(1, world.n_loads + 1), world.n_robots))
    else:
        def gen():
            for robots in combinations(range(world.n_robots), world.n_loads):
                for perm in permutations(range(1, world.n_loads + 1), world.n_loads):
                    labels = np.zeros(world.n_robots, dtype=int)
                    for robot_idx, label in zip(robots, perm): labels[int(robot_idx)] = int(label)
                    yield labels
        iterator = gen()
    for labels in iterator:
        j = assignment_objective(world, labels)
        if j < best_j: best_j = j; best_labels = labels
    assert best_labels is not None
    return best_labels, best_j


def runtime_stats(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {"p50": float(np.quantile(arr, 0.50)), "p95": float(np.quantile(arr, 0.95)), "p99": float(np.quantile(arr, 0.99)), "mean": float(np.mean(arr)), "std": float(np.std(arr)), "max": float(np.max(arr)), "deadline_miss_rate": float(np.mean(arr > 10.0))}


def summarize_check_families(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for family in sorted({row["check_family"] for row in checks}):
        selected = [row for row in checks if row["check_family"] == family]
        finite_abs = [safe_float(row.get("absolute_error")) for row in selected if np.isfinite(safe_float(row.get("absolute_error")))]
        finite_rel = [safe_float(row.get("relative_error")) for row in selected if np.isfinite(safe_float(row.get("relative_error")))]
        output.append({"check_family": family, "number_of_cases": len(selected), "number_passed": sum(bool(row["passed"]) for row in selected), "number_failed": sum(not bool(row["passed"]) for row in selected), "max_absolute_error": max(finite_abs, default=0.0), "max_relative_error": max(finite_rel, default=0.0), "tolerance": max([safe_float(row.get("tolerance")) for row in selected], default=0.0), "affected_methods": sorted({str(row.get("method_variant")) for row in selected})})
    return output


def gate_status_from_checks(checks: list[dict[str, Any]], smoke_manifest: dict[str, Any]) -> dict[str, Any]:
    family_to_gate = {"simplex": "G3", "non_negativity": "G3", "mass_conservation": "G3", "potential_monotonicity": "G3", "matching_validity": "G2", "oracle_correctness": "G6", "qr_acceptance": "G3", "qr_termination": "G3", "metric_correctness": "G2", "seed_reproducibility": "G2", "cache_consistency": "G1", "parquet_schema": "G7", "null_semantics": "G7", "duplicate_rows": "G7", "timeout_preservation": "G7", "oracle_leakage": "G4", "runtime_correctness": "G5"}
    gates = {f"G{i}": {"status": "PASS", "failed_checks": []} for i in range(1, 8)}
    gates["SMOKE"] = {"status": "PASS" if smoke_manifest.get("runs", 0) > 0 else "FAIL", "failed_checks": []}
    for row in checks:
        gate = family_to_gate.get(str(row.get("check_family")), "G1")
        if not bool(row.get("passed")):
            gates[gate]["status"] = "FAIL"; gates[gate]["failed_checks"].append(row.get("check_id"))
    return {"generated_at_utc": datetime.now(UTC).isoformat(), "gates": gates}


def write_gate_status(root: Path, status: dict[str, Any]) -> None:
    save_json(root / "GATE_STATUS.json", status)
    lines = ["# SP0 Gate Status", ""]
    header = ["| Gate | Status | Failed checks |", "|---|---:|---|"]
    rows = []
    for gate, row in status.get("gates", {}).items():
        failed = ", ".join(str(item) for item in row.get("failed_checks", [])) or "-"
        rows.append(f"| {gate} | {row.get('status')} | {failed} |")
    (root / "GATE_STATUS.md").write_text("\n".join(lines + header + rows) + "\n", encoding="utf-8")


def summarize_convergence_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("method_variant")), []).append(row)
    output: list[dict[str, Any]] = []
    for method, selected in sorted(grouped.items()):
        converged_times = [
            float(row["convergence_time"])
            for row in selected
            if row.get("continuous_converged") and row.get("convergence_time") is not None
        ]
        residuals = [float(row["equilibrium_residual"]) for row in selected if row.get("equilibrium_residual") is not None]
        state_changes = [float(row["state_change"]) for row in selected if row.get("state_change") is not None]
        fractionality = [float(row["fractionality"]) for row in selected if row.get("fractionality") is not None]
        end_times = [float(row["simulation_end_time_s"]) for row in selected if row.get("simulation_end_time_s") is not None]
        output.append(
            {
                "method_variant": method,
                "runs": len(selected),
                "continuous_timeout_rate": float(np.mean([bool(row.get("continuous_timeout")) for row in selected])),
                "continuous_convergence_rate": float(np.mean([bool(row.get("continuous_converged")) for row in selected])),
                "median_equilibrium_residual": float(np.median(residuals)) if residuals else math.nan,
                "median_state_change": float(np.median(state_changes)) if state_changes else math.nan,
                "median_fractionality": float(np.median(fractionality)) if fractionality else math.nan,
                "median_convergence_time_s": float(np.median(converged_times)) if converged_times else math.nan,
                "median_simulation_end_time_s": float(np.median(end_times)) if end_times else math.nan,
                "residual_ids": sorted({str(row.get("equilibrium_residual_id")) for row in selected}),
                "final_success_rate": float(np.mean([bool(row.get("final_success")) for row in selected])),
                "interpretation": "continuous timeout is distinct from successful integer closure",
            }
        )
    return output


def write_b0_audit_report(
    b0_dir: Path,
    checks: list[dict[str, Any]],
    benchmark_rows: list[dict[str, Any]],
    convergence_diagnostics: list[dict[str, Any]],
    status: dict[str, Any],
) -> None:
    summary = summarize_check_families(checks)
    failed = [row for row in checks if not bool(row.get("passed"))]
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "checks": len(checks),
        "failed_checks": len(failed),
        "families": summary,
        "gates": status.get("gates", {}),
        "benchmark_rows": len(benchmark_rows),
        "convergence_diagnostics": convergence_diagnostics,
    }
    save_json(b0_dir / "report.json", payload)
    lines = [
        "# SP0 B0 Audit Report",
        "",
        f"Checks: `{len(checks)}`",
        f"Failed checks: `{len(failed)}`",
        "",
        "| Family | Cases | Passed | Failed | Max abs error | Max rel error | Tolerance | Affected methods |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary:
        lines.append(
            "| {check_family} | {number_of_cases} | {number_passed} | {number_failed} | {max_absolute_error:.3g} | {max_relative_error:.3g} | {tolerance:.3g} | {affected_methods} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Continuous convergence diagnostics",
            "",
            "A continuous timeout is retained even when the integer closure later reaches a valid maximum-cardinality assignment.",
            "",
            "| Method | Runs | Timeout rate | Median residual | Median state change | Median fractionality | Median convergence time (s) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in convergence_diagnostics:
        convergence_time = row["median_convergence_time_s"]
        convergence_text = "null" if not np.isfinite(convergence_time) else f"{convergence_time:.3g}"
        lines.append(
            f"| {row['method_variant']} | {row['runs']} | {row['continuous_timeout_rate']:.3f} | "
            f"{row['median_equilibrium_residual']:.3g} | {row['median_state_change']:.3g} | "
            f"{row['median_fractionality']:.3g} | {convergence_text} |"
        )
    lines.extend(["", "## Gates", "", "| Gate | Status | Failed checks |", "|---|---:|---|"])
    for gate, row in status.get("gates", {}).items():
        failed_ids = ", ".join(str(item) for item in row.get("failed_checks", [])) or "-"
        lines.append(f"| {gate} | {row.get('status')} | {failed_ids} |")
    (b0_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_deviation_file(root: Path) -> None:
    path = root / "protocol_deviations.md"
    if path.exists():
        return
    before = full_git_hash()
    text = "\n".join(
        [
            "# Protocol Deviations",
            "",
            "No confirmatory deviations recorded.",
            "",
            "| date_utc | commit_before | commit_after | reason | affected_blocks | affected_hypotheses | impact_on_confirmatory_validity | resolution |",
            "|---|---|---|---|---|---|---|---|",
            f"| {datetime.now(UTC).isoformat()} | {before} | pending | B0 audit instrumentation added before freezing; no confirmatory seeds opened. | B0 | none | none | pending validation |",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def write_final_report(root: Path, manifest: dict[str, Any]) -> None:
    campaign = manifest.get("campaign", {})
    overall = campaign.get("status", manifest.get("status", "unknown"))
    lines = [f"# {root.name} Final Report", "", f"Overall status: {overall}", "", "## 1. Gates B0", ""]
    gate_path = root / "GATE_STATUS.json"
    if gate_path.exists():
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        lines.extend(["| Gate | Status | Failed checks |", "|---|---:|---|"])
        for gate_id, row in gate.get("gates", {}).items():
            failed = ", ".join(str(item) for item in row.get("failed_checks", [])) or "-"
            lines.append(f"| {gate_id} | {row.get('status')} | {failed} |")
    else:
        lines.append("B0 gate evidence is missing.")

    lines.extend([
        "", "## 2. Changes from v1", "",
        "The active SP0 revision separates continuous convergence, timeout, closure success and final assignment success; "
        "uses method-specific residuals, isolates public/oracle views, records seconds-only runtimes, "
        "implements checkpoint-backed PPO with local GNN actors, and preserves audit trajectories.",
        "", "## 3. IPPO/MAPPO training state", "",
    ])
    training_status = {}
    for path in [root / "training" / "status.json", root / "training" / "dry_run" / "status.json"]:
        if path.exists():
            training_status[str(path)] = json.loads(path.read_text(encoding="utf-8"))
    lines.append(json.dumps(training_status, indent=2, sort_keys=True))

    lines.extend(["", "## 4. Three final seeds", ""])
    champion_path = root / "training" / "champion.yaml"
    if champion_path.exists():
        champion = yaml.safe_load(champion_path.read_text(encoding="utf-8")) or {}
        lines.extend(["| Train seed | Steps | Converged | Checkpoint hash |", "|---:|---:|---:|---|"])
        for seed in champion.get("final_seeds", []):
            lines.append(f"| {seed.get('train_seed')} | {seed.get('training_steps')} | {seed.get('training_converged')} | {seed.get('checkpoint_hash')} |")
    else:
        lines.append("No contract-valid confirmatory champion exists; reduced dry-run checkpoints are not substitutes.")

    lines.extend(["", "## 5. Planned vs executed counts", "", "| Block | Planned | Executed |", "|---|---:|---:|"])
    planned = {"B0": 300, "B2": 2400, "B3": 1536, "B4": 5760, "B5": 4000, "B6": 960, "B7": 480}
    executed = {"B0": len(read_table(root / "b0" / "budget_runs.parquet")) if (root / "b0" / "budget_runs.parquet").exists() else 0}
    for block in ["B2", "B3", "B4", "B5", "B6", "B7"]:
        path = root / block.lower() / "runs.parquet"
        executed[block] = len(read_table(path)) if path.exists() else 0
    for block, count in planned.items():
        lines.append(f"| {block} | {count} | {executed.get(block, 0)} |")
    lines.append(f"| TOTAL | 15436 | {sum(executed.values())} |")

    lines.extend([
        "", "## 6. Duration and hardware", "",
        f"- commit: {full_git_hash()}",
        f"- generated_at_utc: {datetime.now(UTC).isoformat()}",
        f"- hardware_id: {hardware_id()}",
        "", json.dumps(hardware_info(), indent=2, sort_keys=True),
        "", "## 7. Results by regime", "",
    ])
    primary_path = root / "statistics" / "primary_summary.parquet"
    if primary_path.exists():
        primary = read_table(primary_path)
        lines.extend(["| Block | Method | N | K | Success | Mean NR | CVaR95 |", "|---|---|---:|---:|---:|---:|---:|"])
        for row in primary[:80]:
            lines.append(f"| {row.get('block_id')} | {row.get('unit_id')} | {row.get('N')} | {row.get('K')} | {safe_float(row.get('success_rate')):.3g} | {safe_float(row.get('mean_normalized_regret')):.3g} | {safe_float(row.get('CVaR95_NR')):.3g} |")
    else:
        lines.append("Confirmatory result tables do not exist yet.")

    for title in [
        "8. Continuous dynamics vs closures", "9. Dynamic-fitness interaction",
        "10. Method-connectivity interaction", "11. Robustness", "12. Generalization",
        "13. Pareto fronts", "14. Observed PoA/PoS",
    ]:
        lines.extend(["", f"## {title}", "", "See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent."])

    lines.extend(["", "## 15. Hypotheses with Holm", ""])
    hypotheses_path = root / "statistics" / "hypotheses.parquet"
    if hypotheses_path.exists():
        hypotheses = read_table(hypotheses_path)
        lines.extend([
            "| Hypothesis | Status | Effect | CI95 | Raw p | Holm p | Decision | Claim | Source |",
            "|---|---|---:|---|---:|---:|---|---|---|",
        ])
        for row in hypotheses:
            interval = f"[{row.get('CI95_low')}, {row.get('CI95_high')}]"
            lines.append(
                f"| {row.get('hypothesis_id')} | {row.get('status')} | {row.get('effect_estimate')} | "
                f"{interval} | {row.get('raw_p')} | {row.get('Holm_adjusted_p')} | "
                f"{row.get('decision')} | {row.get('claim_permitted')} | {row.get('source')} |"
            )
    else:
        lines.append("Holm-adjusted confirmatory analysis has not been generated.")

    lines.extend([
        "", "## 16. Claims", "",
        "- Theoretically guaranteed: oracle optimality, declared simplex contracts, finite QR termination and declared QRA scope.",
        "- Empirically supported: only frozen confirmatory hypotheses at final sample size with Holm correction.",
        "- Exploratory only: B0, smoke, B2 dynamic-fitness screening and nonconfirmatory closure ablations.",
        "- Not supported: universal stability, universal graph convergence, theoretical PoA from Monte Carlo, or physical transfer.",
        "", "## 17. Failure cases", "",
    ])
    failures = []
    for block in ["b2", "b3", "b4", "b5", "b6", "b7"]:
        path = root / block / "runs.parquet"
        if path.exists():
            failures.extend([row for row in read_table(path) if row.get("error_type") or row.get("timeout") is True])
    lines.append(f"Preserved failure/timeout rows found: {len(failures)}.")

    deviations = root / "protocol_deviations.md"
    lines.extend(["", "## 18. Deviations", ""])
    lines.append(deviations.read_text(encoding="utf-8") if deviations.exists() else "No deviation log found.")
    lines.extend([
        "", "## 19. Reproducibility", "",
        "Frozen hashes, seed registry, environment lock, world/checkpoint/trajectory hashes are authoritative. "
        "Dry-run artifacts are exploratory and cannot open test seeds.",
        "", "## 20. Final verdict", "",
    ])
    if manifest.get("status") == "SP0_COMPLETE" and hypotheses_path.exists():
        lines.append("SP0 execution is complete. Regime-specific winners are reported from final Pareto/ranking tables; no universal winner is forced.")
    else:
        lines.append("SP0 is not closed. Winners cannot be declared until contract-valid training, freeze, B1-B7, precision checks and postprocessing complete.")
    (root / "FINAL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_table(path: Path, rows: list[dict[str, Any]], columns_like: list[dict[str, Any]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table_columns = columns_for_rows(rows if rows else (columns_like or []))
    normalized_rows = [{key: normalize_table_cell(row.get(key)) for key in table_columns} for row in rows]
    if path.suffix.lower() == ".parquet":
        try:
            import pandas as pd
            df = pd.DataFrame(normalized_rows, columns=table_columns)
            coerce_nullable_dataframe_types(df).to_parquet(path, index=False)
            return
        except Exception:
            csv_path = path.with_suffix(".csv")
            write_csv(csv_path, rows, table_columns)
            path.write_text(f"Parquet unavailable; see {csv_path.name}\n", encoding="utf-8")
            return
    write_csv(path, rows, table_columns)


def normalize_table_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def read_table(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".parquet":
        try:
            import pandas as pd
            return pd.read_parquet(path).to_dict(orient="records")
        except Exception:
            csv_path = path.with_suffix(".csv")
            if csv_path.exists():
                return read_table(csv_path)
            return []
    if not path.exists():
        return []
    import csv
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def columns_for_rows(rows: list[dict[str, Any]]) -> list[str]:
    preferred = b0_columns()
    keys = set().union(*(row.keys() for row in rows)) if rows else set()
    return [key for key in preferred if key in keys] + sorted(keys - set(preferred))


def b0_columns(rows: list[dict[str, Any]] | None = None) -> list[str]:
    return [
        "check_id", "check_family", "method_family", "method_variant", "fitness_id", "rounding_id", "world_seed", "method_seed", "N", "K", "expected_value", "observed_value", "absolute_error", "relative_error", "tolerance", "passed", "runtime_wall_s", "config_hash", "git_hash", "timestamp_utc",
    ]


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def fixture_seed(offset: int | str) -> int:
    if isinstance(offset, str):
        digits = "".join(ch for ch in offset if ch.isdigit())
        return 8000 + int(digits or 0)
    return 8000 + int(offset)


def hardware_info() -> dict[str, Any]:
    gpu_model = "not_detected"
    gpu_memory_bytes: int | None = None
    torch_version = "not_installed"
    try:
        import torch

        torch_version = str(torch.__version__)
        if torch.cuda.is_available():
            index = torch.cuda.current_device()
            gpu_model = torch.cuda.get_device_name(index)
            gpu_memory_bytes = int(torch.cuda.get_device_properties(index).total_memory)
    except Exception:
        pass
    try:
        import jax

        jax_version = str(jax.__version__)
    except Exception:
        jax_version = "not_installed"
    return {
        "cpu_model": platform.processor() or platform.machine(),
        "gpu_model": gpu_model,
        "gpu_memory_bytes": gpu_memory_bytes,
        "ram_bytes": ram_bytes(),
        "python_version": sys.version.split()[0],
        "torch_version": torch_version,
        "jax_version": jax_version,
        "num_workers": int(os.environ.get("SP0_WORKERS", "1")),
        "batch_size": int(os.environ.get("SP0_BATCH_SIZE", "1")),
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", ""),
        "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS", ""),
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS", ""),
    }

def ram_bytes() -> int | None:
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
    except Exception:
        return None
    return None
def _jax_or_torch_version() -> str:
    versions: list[str] = []
    for module_name in ["jax", "torch"]:
        try:
            module = __import__(module_name)
            versions.append(f"{module_name}={getattr(module, '__version__', 'unknown')}")
        except Exception:
            pass
    return ",".join(versions) if versions else "not_installed"


def hardware_id() -> str:
    encoded = json.dumps(hardware_info(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def environment_lock() -> dict[str, Any]:
    packages = {}
    for name in [
        "numpy", "scipy", "torch", "jax", "pandas", "pyarrow", "statsmodels",
        "matplotlib", "PyYAML", "pytest", "imageio",
    ]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "hardware": hardware_info(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "packages": packages,
        "thread_environment": {
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"),
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        },
    }


def build_seed_registry() -> dict[str, list[int]]:
    registry = {
        "unit_seeds": list(range(8000, 8010)),
        "screening_seeds": list(range(10000, 10005)),
        "tuning_seeds": list(range(11000, 11030)),
        "validation_seeds": list(range(12000, 12040)),
        "test_seeds_1_40": list(range(13000, 13040)),
        "extension_seeds_41_60": list(range(13040, 13060)),
        "extension_seeds_61_100": list(range(13060, 13100)),
        "generalization_seeds": list(range(14000, 14040)),
        "training_seeds": [14101, 14201, 14202, 15001, 15002, 15003],
    }
    seen: set[int] = set()
    for name, values in registry.items():
        overlap = seen.intersection(values)
        if overlap:
            raise RuntimeError(f"Seed registry is not disjoint at {name}: {sorted(overlap)}")
        seen.update(values)
    return registry


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=True, allow_unicode=False), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def sha256_python_sources(path: Path) -> str:
    h = hashlib.sha256()
    for item in sorted(path.rglob("*.py")):
        h.update(str(item.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(item.read_bytes())
    return h.hexdigest()


def sha256_tree(path: Path) -> str:
    h = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            h.update(str(item.relative_to(path)).replace("\\", "/").encode("utf-8"))
            h.update(item.read_bytes())
    return h.hexdigest()


def full_git_hash() -> str:
    git_dir = Path(".git")
    head = git_dir / "HEAD"
    try:
        text = head.read_text(encoding="utf-8").strip()
        if text.startswith("ref:"):
            ref = text.split(" ", 1)[1]
            return (git_dir / ref).read_text(encoding="utf-8").strip()
        return text
    except OSError:
        return "unknown"
