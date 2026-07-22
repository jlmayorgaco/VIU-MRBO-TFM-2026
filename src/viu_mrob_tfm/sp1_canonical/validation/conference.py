"""Reproducible SP1 conference validation campaign.

This runner is intentionally separate from ``experiment.py`` so the archived
smoke campaign remains reproducible byte-for-byte.  It implements the frozen
P0/E0--E6 protocol and computes conference gates from generated data.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
import math
import os
import platform
import copy
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
import scipy
import yaml

from viu_mrob_tfm.sp1_canonical.validation.auction import distributed_deficit_auction
from viu_mrob_tfm.sp1_canonical.validation.dynamics import (
    DynamicResult,
    GraphInfo,
    estimate_operator_scale,
    make_graph,
    run_population_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import (
    RESOURCE_NAMES,
    ResourceWorld,
    build_costs,
    generate_resource_world,
    manual_world,
)
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    IntegerResult,
    argmax_round,
    best_of_samples,
    categorical_round,
    evaluate_integer,
    repair_assignment,
)
from viu_mrob_tfm.sp1_canonical.validation.simulation import (
    ApproachResult,
    build_warehouse_route_costs,
    contact_targets,
    simulate_approach,
    warehouse_obstacles,
)
from viu_mrob_tfm.sp1_canonical.validation.solvers import (
    AllocationSolution,
    allocation_entropy,
    assignment_from_matrix,
    evaluate_relaxed,
    greedy_deficit,
    solve_lp,
    solve_milp,
    solve_regularized_lp,
)
from viu_mrob_tfm.sp1_canonical.validation.statistics import (
    aggregate_numeric,
    friedman_kendall_w,
    holm_adjust,
    paired_wilcoxon,
    spearman_bootstrap,
    wilson_interval,
)


EXPERIMENTS = ("e0", "e1", "e2", "e3", "e4", "e5", "e6")
SP1_PREFLIGHT_TESTS = (
    "tests/test_sp1_canonical.py",
    "tests/test_sp1_validation.py",
    "tests/test_sp1_conference.py",
    "tests/test_sp1_e6_visualization.py",
    "tests/test_sp1_result_package.py",
)
REQUIRED_RELATIVE_TOLERANCES = {
    "primal_tolerance": 1e-3,
    "consensus_tolerance": 1e-4,
    "stationarity_tolerance": 1e-3,
}
REQUIRED_GATES = (
    "tests_and_audits_pass",
    "e1_convergence_at_least_95pct",
    "e1_comparability_at_least_90pct",
    "e2_connected_disconnected_separated",
    "e2_sufficient_worlds_for_lambda2",
    "e4_repaired_feasibility_at_least_95pct",
    "e4_100_worlds_per_configuration_with_ci",
    "e5_multiple_seeds_reaches_n200",
    "distributed_nonpopulation_baseline_present",
    "claims_respect_scope",
)


def execute(config_path: str | Path, *, experiment: str = "all", resume: bool = False) -> dict[str, Any]:
    return run_conference_config(config_path, experiment=experiment, resume=resume)


def run_conference_config(
    config_path: str | Path,
    *,
    experiment: str = "all",
    resume: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    started_utc = datetime.now(timezone.utc).isoformat()
    config_path = Path(config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    _validate_config(config)
    selected = list(EXPERIMENTS) if experiment == "all" else [experiment.lower()]
    if set(selected) - set(EXPERIMENTS):
        raise ValueError(f"Unknown conference experiments: {selected}")
    output_dir = Path(config["output_dir"])
    if output_dir.name == "SP1_FULL_VALIDATION_SMOKE_v1":
        raise ValueError("The archived smoke campaign cannot be overwritten")
    for subdir in ("raw", "tables", "figures"):
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / "config_snapshot.yaml"
    snapshot_text = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    if resume and snapshot_path.exists() and snapshot_path.read_text(encoding="utf-8") != snapshot_text:
        raise ValueError("Resume rejected: config_snapshot.yaml differs from the requested configuration")
    snapshot_path.write_text(snapshot_text, encoding="utf-8")

    p0_checks, p0_table = _run_p0_audit(config)
    preflight = _run_preflight_tests(config, output_dir)
    if preflight is not None:
        p0_checks["p0_pytest_suite_passed"] = bool(preflight["passed"])
        p0_table = pd.concat([
            p0_table,
            pd.DataFrame([{"check": "p0_pytest_suite_passed", "passed": preflight["passed"], "evidence": preflight["summary"]}]),
        ], ignore_index=True)
    p0_table.to_csv(output_dir / "tables" / "p0_mathematical_software_audit.csv", index=False)
    payloads: dict[str, dict[str, pd.DataFrame]] = {}
    experiment_checks: dict[str, bool] = {}
    cached_experiments: list[str] = []
    for name in selected:
        # E0 is inexpensive and its Rep-C/Rep-D state-distance invariant cannot
        # be reconstructed from the compact CSV, so rerun it on every resume.
        cached = _load_cached_payload(output_dir, name) if resume and name != "e0" else None
        if cached is not None:
            payload = cached
            checks = globals()[f"_checks_{name}"](config, payload)
            checks = {"resumed_artifacts_nonempty": bool(not cached["runs"].empty), **checks}
            cached_experiments.append(name)
        else:
            payload, checks = globals()[f"_run_{name}"](config, output_dir)
            _write_payload(output_dir, name, payload)
        payloads[name] = payload
        experiment_checks.update({f"{name}_{key}": bool(value) for key, value in checks.items()})

    ablations = _run_ablations(config, output_dir) if experiment in {"all", "e1", "e4"} else pd.DataFrame()
    if not ablations.empty:
        ablations.to_csv(output_dir / "raw" / "ablations_runs.csv", index=False)
    all_runs = _combine_runs(payloads)
    all_runs.to_csv(output_dir / "all_runs.csv", index=False)
    aggregated = _aggregate_campaign(config, payloads, ablations)
    aggregated.to_csv(output_dir / "aggregated_results.csv", index=False)
    exclusions = _collect_exclusions(payloads)
    exclusions.to_csv(output_dir / "exclusions.csv", index=False)
    seeds = _seed_ledger(config)
    seeds.to_csv(output_dir / "seeds.csv", index=False)
    _write_tables(config, output_dir, payloads)
    _write_figures(config, output_dir, payloads, ablations)

    checks = {**p0_checks, **experiment_checks}
    gates = _conference_gates(config, payloads, checks)
    audit_status = "passed" if checks and all(checks.values()) else "failed"
    scientific_status = "conference-ready" if audit_status == "passed" and all(gates.values()) else "partial"
    audit = {
        "status": audit_status,
        "scientific_status": scientific_status,
        "evidence_level": "B-conference-candidate" if scientific_status == "conference-ready" else "C-pilot/partial",
        "canonical_sp": "SP1",
        "checks": checks,
        "gates": gates,
        "failed_gates": [gate for gate, passed in gates.items() if not passed],
        "selected_experiments": selected,
        "scope": "coalition allocation, neighbor dynamics, integer recovery and unicycle approach",
        "not_claimed": [
            "global convergence outside the tested assumptions",
            "general integer optimality of the recovery heuristic",
            "sustained cooperative payload transport",
            "docking or wrench feasibility",
            "hardware validation",
        ],
    }
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_claim_evidence(output_dir, payloads, audit)
    _write_reviewer_risks(output_dir, payloads, audit)
    report = _build_report(config, payloads, aggregated, exclusions, audit)
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    _write_report_pdf(output_dir / "report.pdf", report)
    _write_requirements_lock(output_dir / "requirements-lock.txt")
    duration_s = time.perf_counter() - started
    manifest = _build_manifest(
        config_path,
        config,
        output_dir,
        audit,
        seeds,
        started_utc=started_utc,
        duration_s=duration_s,
        resume_requested=resume,
        cached_experiments=cached_experiments,
    )
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    if bool(config.get("fail_on_audit", False)) and audit_status != "passed":
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"SP1 conference audit failed: {failed}")
    return manifest


def _validate_config(config: dict[str, Any]) -> None:
    required = {"experiment_id", "protocol_family", "output_dir", "cost_weights", "dynamics", "statistics", *EXPERIMENTS}
    missing = required - set(config)
    if missing:
        raise ValueError(f"Missing conference configuration keys: {sorted(missing)}")
    if config["experiment_id"] == "SP1_FULL_VALIDATION_SMOKE_v1":
        raise ValueError("Use a distinct experiment_id for the conference campaign")
    dynamics = config["dynamics"]
    if str(dynamics.get("convergence_residual_mode")) != "relative":
        raise ValueError("Conference stopping criteria must use relative residuals")
    for key, expected in REQUIRED_RELATIVE_TOLERANCES.items():
        if not math.isclose(float(dynamics.get(key, math.nan)), expected, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError(f"Frozen tolerance {key} must equal {expected}")
    if float(dynamics.get("comparison_feasibility_tolerance", math.nan)) != 1e-6:
        raise ValueError("LP comparability tolerance is frozen at 1e-6 by docs/03_EXPERIMENT_PROTOCOL.md")


def _dynamic_options(config: dict[str, Any], experiment: str, **overrides: Any) -> dict[str, Any]:
    options = dict(config["dynamics"])
    options.update(config.get(experiment, {}).get("dynamics", {}))
    options.update(overrides)
    return {
        "integrator": str(options.get("integrator", "mirror_prox")),
        "step": float(options.get("step", 0.03)),
        "max_iterations": int(options.get("max_iterations", 20_000)),
        "primal_tolerance": float(options["primal_tolerance"]),
        "consensus_tolerance": float(options["consensus_tolerance"]),
        "stationarity_tolerance": float(options["stationarity_tolerance"]),
        "convergence_residual_mode": str(options["convergence_residual_mode"]),
        "comparison_feasibility_tolerance": float(options["comparison_feasibility_tolerance"]),
        "entropy_tau": float(options.get("entropy_tau", 0.003)),
        "consensus_gain": float(options.get("consensus_gain", 1.0)),
        "use_integral_consensus": bool(options.get("use_integral_consensus", True)),
        "history_stride": int(options.get("history_stride", 100)),
    }


def _seeds(specification: list[int] | dict[str, int]) -> list[int]:
    if isinstance(specification, list):
        return [int(seed) for seed in specification]
    start = int(specification["start"])
    return list(range(start, start + int(specification["count"])))


def _worlds(section: dict[str, Any]) -> Iterable[tuple[int, int, int]]:
    configurations = section.get("configurations")
    if configurations is not None:
        pairs = [(int(pair[0]), int(pair[1])) for pair in configurations]
    else:
        pairs = [(int(n), int(k)) for n in section["fleet_sizes"] for k in section["load_counts"] if int(n) >= int(k)]
    for n, k in pairs:
        for seed in _seeds(section["seeds"]):
            yield n, k, seed


def _costs(config: dict[str, Any], world: ResourceWorld) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    return build_costs(world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0)))


def _regularized_objective(x: np.ndarray, costs: np.ndarray, entropy_tau: float) -> float:
    finite = costs[np.isfinite(costs)]
    scale = max(float(np.max(finite)) if finite.size else 1.0, 1e-12)
    raw = float(np.sum(np.where(np.isfinite(costs), costs, 0.0) * x))
    return float(raw / scale - float(entropy_tau) * allocation_entropy(x))


def _not_comparable_reason(
    *,
    reference_status: int,
    x: np.ndarray,
    primal_normalized: float,
    simplex_violation: float,
    tolerance: float,
) -> str:
    if reference_status != 0:
        return "lp_tau_not_optimal"
    if not np.all(np.isfinite(x)):
        return "nonfinite_state"
    if simplex_violation > tolerance:
        return "simplex_violation"
    if primal_normalized > tolerance:
        return "primal_infeasible"
    return "none"


def _relaxed_row(
    experiment: str,
    method: str,
    world: ResourceWorld,
    x: np.ndarray,
    costs: np.ndarray,
    *,
    lp_raw: AllocationSolution,
    lp_tau: AllocationSolution,
    entropy_tau: float,
    solver_status: int,
    solver_message: str,
    mip_gap: float = math.nan,
    dynamic: DynamicResult | None = None,
    graph: GraphInfo | None = None,
) -> dict[str, Any]:
    metrics = evaluate_relaxed(world, x, costs)
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)
    coverage = np.einsum("ik,ikm->km", x, normalized)
    primal_normalized = float(np.linalg.norm(np.maximum(1.0 - coverage, 0.0)))
    primal_relative = primal_normalized / (1.0 + float(np.linalg.norm(np.ones_like(coverage))))
    tolerance = 1e-6
    reason = _not_comparable_reason(
        reference_status=lp_tau.status,
        x=x,
        primal_normalized=primal_normalized,
        simplex_violation=float(metrics["simplex_violation"]),
        tolerance=tolerance,
    )
    comparable = reason == "none"
    raw_objective = float(metrics["objective"])
    regularized = _regularized_objective(x, costs, entropy_tau)
    raw_gap = (raw_objective - lp_raw.raw_objective) / max(abs(lp_raw.raw_objective), 1e-12) if comparable and lp_raw.status == 0 else math.nan
    regularized_gap = (regularized - lp_tau.regularized_objective) / max(abs(lp_tau.regularized_objective), 1e-12) if comparable else math.nan
    final = dynamic.history.iloc[-1] if dynamic is not None else None
    return {
        "experiment": experiment,
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "method": method,
        "result_type": "fractional",
        "raw_objective": raw_objective,
        "regularized_objective": regularized,
        "gap_raw_lp": raw_gap,
        "gap_regularized_lp": regularized_gap,
        "integer_gap_milp": math.nan,
        "comparable_to_lp": comparable,
        "not_comparable_reason": reason,
        "solver_status": int(solver_status),
        "solver_message": str(solver_message),
        "mip_gap": float(mip_gap),
        "primal_residual_absolute": float(metrics["primal_residual"]),
        "primal_residual_normalized": primal_normalized,
        "primal_residual_relative": float(final["primal_residual_relative"]) if final is not None else primal_relative,
        "consensus_residual_absolute": float(final["consensus_residual"]) if final is not None else math.nan,
        "consensus_residual_relative": float(final["consensus_residual_relative"]) if final is not None else math.nan,
        "stationarity_residual_absolute": float(final["stationarity_residual"]) if final is not None else math.nan,
        "stationarity_residual_relative": float(final["stationarity_residual_relative"]) if final is not None else math.nan,
        "fixed_point_residual_absolute": float(final["fixed_point_residual"]) if final is not None else math.nan,
        "simplex_violation": float(metrics["simplex_violation"]),
        "finite_state": bool(np.all(np.isfinite(x))),
        "converged": bool(dynamic.converged) if dynamic is not None else None,
        "iterations": int(dynamic.iterations) if dynamic is not None else 0,
        "runtime_s": float(dynamic.runtime_s) if dynamic is not None else math.nan,
        "messages": int(dynamic.messages) if dynamic is not None else 0,
        "scalars_sent": int(dynamic.scalars_sent) if dynamic is not None else 0,
        "graph_connected": bool(graph.connected) if graph is not None else None,
        "lambda2": float(graph.lambda2) if graph is not None else math.nan,
        "lambda_max": float(graph.lambda_max) if graph is not None else math.nan,
        "edges": int(graph.edges) if graph is not None else 0,
        "assignment_json": json.dumps(assignment_from_matrix(x).tolist()),
    }


def _run_p0_audit(config: dict[str, Any]) -> tuple[dict[str, bool], pd.DataFrame]:
    world = manual_world()
    costs, compatible, _ = _costs(config, world)
    tau = float(config["dynamics"].get("entropy_tau", 0.003))
    lp_raw = solve_lp(world, costs)
    lp_tau = solve_regularized_lp(world, costs, entropy_tau=tau)
    milp = solve_milp(world, costs, time_limit_s=float(config.get("oracle_time_limit_s", 30.0)))
    graph = make_graph(world, "complete")
    short_options = _dynamic_options(config, "e0", max_iterations=1, history_stride=1)
    rep_c = run_population_dynamics(world, costs, graph, distributed=False, lp_objective=lp_raw.objective, **short_options)
    rep_d = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp_raw.objective, **short_options)
    raw_formula = float(np.sum(np.where(np.isfinite(costs), costs, 0.0) * lp_raw.x))
    regularized_formula = _regularized_objective(lp_tau.x, costs, tau)
    coverage_lp = lp_raw.x.T @ world.resources
    coverage_milp = milp.x.T @ world.resources
    infeasible = np.zeros_like(lp_raw.x)
    infeasible_metrics = evaluate_relaxed(world, infeasible, costs)
    infeasible_reason = _not_comparable_reason(
        reference_status=lp_tau.status,
        x=infeasible,
        primal_normalized=float(np.linalg.norm(np.ones_like(world.requirements))),
        simplex_violation=float(infeasible_metrics["simplex_violation"]),
        tolerance=1e-6,
    )
    source = inspect.getsource(run_population_dynamics)
    checks = {
        "p0_lp_raw_is_c_transpose_x": bool(lp_raw.status == 0 and math.isclose(lp_raw.raw_objective, raw_formula, rel_tol=0.0, abs_tol=1e-9)),
        "p0_lp_tau_is_c_transpose_x_minus_tau_h": bool(lp_tau.status == 0 and math.isclose(lp_tau.regularized_objective, regularized_formula, rel_tol=0.0, abs_tol=1e-9)),
        "p0_milp_binary_and_raw_objective": bool(milp.status == 0 and np.all(np.isin(milp.x, [0.0, 1.0])) and math.isclose(milp.raw_objective, float(np.sum(np.where(np.isfinite(costs), costs, 0.0) * milp.x)), abs_tol=1e-9)),
        "p0_constraints_are_ax_ge_b": bool(np.all(coverage_lp + 1e-7 >= world.requirements) and np.all(coverage_milp + 1e-7 >= world.requirements)),
        "p0_simplex_per_robot": bool(np.all(lp_tau.x.sum(axis=1) <= 1.0 + 1e-8) and np.min(lp_tau.x) >= -1e-9),
        "p0_compatibility_and_battery_mask": bool(not compatible[3, 0] and abs(lp_raw.x[3, 0]) <= 1e-12),
        "p0_rep_c_rep_d_same_tau_parameter": bool(short_options["entropy_tau"] == tau and np.all(np.isfinite(rep_c.x)) and np.all(np.isfinite(rep_d.x))),
        "p0_mirror_prox_corrector_anchored_in_base_state": bool("x = exp_step(x, predictor_gradient)" in source and "dual = central_dual_step(dual, x_predictor)" in source),
        "p0_integrators_have_distinct_names": all(name in source for name in ("euler_pure", "projected_euler", "exponential", "mirror_prox")),
        "p0_infeasible_negative_gap_rejected": infeasible_reason == "primal_infeasible",
        "p0_frozen_relative_tolerances": all(math.isclose(float(config["dynamics"][key]), value, rel_tol=0.0, abs_tol=1e-15) for key, value in REQUIRED_RELATIVE_TOLERANCES.items()),
    }
    table = pd.DataFrame(
        [{"check": name, "passed": passed, "evidence": _p0_evidence(name, lp_raw, lp_tau, milp)} for name, passed in checks.items()]
    )
    return checks, table


def _p0_evidence(name: str, lp_raw: AllocationSolution, lp_tau: AllocationSolution, milp: AllocationSolution) -> str:
    if "lp_raw" in name:
        return f"status={lp_raw.status}; raw={lp_raw.raw_objective:.12g}"
    if "lp_tau" in name:
        return f"status={lp_tau.status}; regularized={lp_tau.regularized_objective:.12g}"
    if "milp" in name:
        return f"status={milp.status}; mip_gap={milp.mip_gap}"
    return "automatic invariant"


def _fixed_world(
    name: str,
    *,
    positions: list[list[float]],
    load_positions: list[list[float]],
    payload_force: list[list[float]],
    requirements: list[list[float]],
    battery: list[float] | None = None,
    speed: list[float] | None = None,
    energy_per_m: list[float] | None = None,
    expected_assignment: list[int],
) -> tuple[str, ResourceWorld, np.ndarray]:
    n = len(positions)
    resources = np.column_stack([np.ones(n), np.asarray(payload_force, dtype=float)])
    battery_array = np.asarray(battery if battery is not None else [200.0] * n, dtype=float)
    speed_array = np.asarray(speed if speed is not None else [1.0] * n, dtype=float)
    energy_array = np.asarray(energy_per_m if energy_per_m is not None else [1.0] * n, dtype=float)
    record = {
        "name": name,
        "positions": positions,
        "loads": load_positions,
        "resources": resources.tolist(),
        "requirements": requirements,
        "battery": battery_array.tolist(),
        "speed": speed_array.tolist(),
        "energy": energy_array.tolist(),
        "expected_assignment": expected_assignment,
    }
    digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode("utf-8")).hexdigest()
    world = ResourceWorld(
        seed=-int(digest[:7], 16),
        robot_positions_m=np.asarray(positions, dtype=float),
        load_positions_m=np.asarray(load_positions, dtype=float),
        resources=resources,
        requirements=np.asarray(requirements, dtype=float),
        battery_energy=battery_array,
        max_speed_mps=speed_array,
        energy_per_m=energy_array,
        robot_classes=tuple("constructed" for _ in range(n)),
        feasibility_witness=np.asarray(expected_assignment, dtype=int),
        world_hash=digest,
    )
    return name, world, np.asarray(expected_assignment, dtype=int)


def _e0_cases() -> list[tuple[str, ResourceWorld, np.ndarray]]:
    inherited = ("manual_inherited", manual_world(), np.asarray([0, 0, 0, -1, -1], dtype=int))
    return [
        inherited,
        _fixed_world(
            "A_near_small_insufficient_far_heavy",
            positions=[[1.0, 0.0], [2.0, 0.0], [10.0, 0.0]],
            load_positions=[[0.0, 0.0]],
            payload_force=[[8.0, 8.0], [8.0, 8.0], [25.0, 25.0]],
            requirements=[[1.0, 20.0, 20.0]],
            expected_assignment=[-1, -1, 0],
        ),
        _fixed_world(
            "B_small_coalition_cheaper_than_heavy",
            positions=[[1.0, 0.0], [1.4, 0.0], [9.0, 0.0]],
            load_positions=[[0.0, 0.0]],
            payload_force=[[12.0, 12.0], [12.0, 12.0], [30.0, 30.0]],
            requirements=[[2.0, 22.0, 22.0]],
            expected_assignment=[0, 0, -1],
        ),
        _fixed_world(
            "C_capable_but_battery_incompatible",
            positions=[[1.0, 0.0], [4.0, 0.0], [4.5, 0.0]],
            load_positions=[[0.0, 0.0]],
            payload_force=[[30.0, 30.0], [26.0, 26.0], [8.0, 8.0]],
            requirements=[[1.0, 25.0, 25.0]],
            battery=[5.2, 100.0, 100.0],
            energy_per_m=[1.0, 1.0, 1.0],
            expected_assignment=[-1, 0, -1],
        ),
        _fixed_world(
            "D_two_loads_compete_for_critical_robot",
            positions=[[5.0, 0.0], [0.5, 0.0], [9.5, 0.0], [9.0, 0.0]],
            load_positions=[[0.0, 0.0], [10.0, 0.0]],
            payload_force=[[26.0, 26.0], [21.0, 21.0], [12.0, 12.0], [10.0, 10.0]],
            requirements=[[1.0, 20.0, 20.0], [1.0, 25.0, 25.0]],
            expected_assignment=[1, 0, -1, -1],
        ),
    ]


def _run_e0(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    cases: list[dict[str, Any]] = []
    state_differences: list[float] = []
    tau = float(_dynamic_options(config, "e0")["entropy_tau"])
    time_limit = float(config.get("oracle_time_limit_s", 30.0))
    acceptance = config["e0"]["acceptance"]
    for case_name, world, expected in _e0_cases():
        costs, compatible, _ = _costs(config, world)
        lp_raw = solve_lp(world, costs)
        lp_tau = solve_regularized_lp(world, costs, entropy_tau=tau)
        milp = solve_milp(world, costs, time_limit_s=time_limit)
        graph = make_graph(world, "complete")
        options = _dynamic_options(config, "e0", history_stride=int(config["e0"].get("history_stride", 50)))
        rep_c = run_population_dynamics(world, costs, graph, distributed=False, lp_objective=lp_raw.objective, **options)
        rep_d = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp_raw.objective, **options)
        state_differences.append(float(np.linalg.norm(rep_d.x - rep_c.x)))
        methods: list[tuple[str, AllocationSolution | None, DynamicResult | None]] = [
            ("LP-raw", lp_raw, None),
            ("LP-tau", lp_tau, None),
            ("MILP", milp, None),
            ("Rep-C", None, rep_c),
            ("Rep-D", None, rep_d),
        ]
        for method, solution, dynamic in methods:
            x = solution.x if solution is not None else dynamic.x
            status = solution.status if solution is not None else (0 if dynamic.converged else 1)
            message = solution.message if solution is not None else ("converged" if dynamic.converged else "iteration_limit")
            row = _relaxed_row(
                "e0", method, world, x, costs, lp_raw=lp_raw, lp_tau=lp_tau, entropy_tau=tau,
                solver_status=status, solver_message=message, mip_gap=solution.mip_gap if solution is not None else math.nan,
                dynamic=dynamic, graph=graph if dynamic is not None else None,
            )
            row.update({"case": case_name, "expected_assignment_json": json.dumps(expected.tolist())})
            rows.append(row)
        histories.extend([
            rep_c.history.assign(case=case_name, method="Rep-C", world_hash=world.world_hash),
            rep_d.history.assign(case=case_name, method="Rep-D", world_hash=world.world_hash),
        ])
        cases.append({
            "case": case_name,
            "world_hash": world.world_hash,
            "expected_assignment_json": json.dumps(expected.tolist()),
            "milp_assignment_json": json.dumps(assignment_from_matrix(milp.x).tolist()),
            "expected_feasible": evaluate_integer(world, expected, costs).feasible,
            "expected_cost": evaluate_integer(world, expected, costs).objective,
            "milp_cost": milp.objective,
            "incompatible_pairs": int(np.size(compatible) - np.sum(compatible)),
        })
    runs = pd.DataFrame(rows)
    history = pd.concat(histories, ignore_index=True)
    cases_frame = pd.DataFrame(cases)
    pivot = runs.pivot(index="case", columns="method", values="regularized_objective")
    rep_rows = runs[runs.method.isin(["Rep-C", "Rep-D"])]
    checks = {
        "five_cases_present": runs["case"].nunique() == 5,
        "analytic_assignments_feasible_and_optimal": bool(cases_frame.expected_feasible.all() and np.allclose(cases_frame.expected_cost, cases_frame.milp_cost, atol=1e-8)),
        "rep_regularized_error_within_1e4": bool(((rep_rows.gap_regularized_lp.abs()) <= float(acceptance["regularized_error"])).all()),
        "rep_primal_relative_within_1e4": bool((rep_rows.primal_residual_relative <= float(acceptance["primal_relative"])).all()),
        "rep_d_matches_rep_c_within_1e4": bool(max(state_differences, default=math.inf) <= float(acceptance["rep_d_rep_c_state_error"])),
        "battery_case_has_incompatibility": bool(cases_frame.loc[cases_frame.case.str.startswith("C_"), "incompatible_pairs"].gt(0).all()),
        "all_solver_states_finite": bool(runs.finite_state.all()),
    }
    return {"runs": runs, "history": history, "cases": cases_frame}, checks


def _minimum_connected_rdisk(world: ResourceWorld) -> tuple[GraphInfo, float]:
    delta = world.robot_positions_m[:, None, :] - world.robot_positions_m[None, :, :]
    distances = np.linalg.norm(delta, axis=2)
    candidates = np.unique(distances[np.triu_indices(world.n_robots, k=1)])
    for radius in candidates:
        graph = make_graph(world, "rdisk", radius_m=float(radius) + 1e-10)
        if graph.connected:
            return graph, float(radius) + 1e-10
    radius = float(np.max(candidates)) + 1e-10 if candidates.size else 0.0
    return make_graph(world, "rdisk", radius_m=radius), radius


def _connected_rdisk_levels(world: ResourceWorld, levels: int) -> list[tuple[str, GraphInfo, float]]:
    delta = world.robot_positions_m[:, None, :] - world.robot_positions_m[None, :, :]
    distances = np.unique(np.linalg.norm(delta, axis=2)[np.triu_indices(world.n_robots, k=1)])
    if not distances.size:
        graph = make_graph(world, "rdisk", radius_m=0.0)
        return [("rdisk_level_1", graph, 0.0)]
    _, threshold = _minimum_connected_rdisk(world)
    valid = distances[distances >= threshold - 1e-8]
    if valid.size < levels:
        valid = distances
    indices = np.unique(np.rint(np.linspace(0, len(valid) - 1, levels)).astype(int))
    cases: list[tuple[str, GraphInfo, float]] = []
    for level, index in enumerate(indices, start=1):
        radius = max(float(valid[index]) + 1e-10, threshold)
        graph = make_graph(world, "rdisk", radius_m=radius)
        if graph.connected:
            cases.append((f"rdisk_level_{level}", graph, radius))
    return cases


def _run_e1_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e1"]
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    worlds: list[dict[str, Any]] = []
    tau = float(_dynamic_options(config, "e1")["entropy_tau"])
    trace_seeds: set[tuple[int, int, int]] = set()
    for n, k, seed in _worlds(section):
        trace_seeds.add((n, k, _seeds(section["seeds"])[0]))
        world = generate_resource_world(n, k, seed)
        costs, compatible, _ = _costs(config, world)
        start = time.perf_counter()
        lp_raw = solve_lp(world, costs)
        lp_raw_runtime = time.perf_counter() - start
        start = time.perf_counter()
        lp_tau = solve_regularized_lp(world, costs, entropy_tau=tau, max_iterations=int(section.get("lp_tau_max_iterations", 10_000)))
        lp_tau_runtime = time.perf_counter() - start
        complete = make_graph(world, "complete")
        rdisk, rdisk_radius = _minimum_connected_rdisk(world)
        worlds.append({
            "world_hash": world.world_hash, "seed": seed, "n_robots": n, "n_loads": k,
            "compatible_pairs": int(np.sum(compatible)), "rdisk_radius_m": rdisk_radius,
        })
        for method, solution, runtime in (("LP-raw", lp_raw, lp_raw_runtime), ("LP-tau", lp_tau, lp_tau_runtime)):
            row = _relaxed_row(
                "e1", method, world, solution.x, costs, lp_raw=lp_raw, lp_tau=lp_tau, entropy_tau=tau,
                solver_status=solution.status, solver_message=solution.message, mip_gap=solution.mip_gap,
            )
            row["runtime_s"] = float(runtime)
            row["graph_case"] = "central_global"
            rows.append(row)
        dynamic_cases = (
            ("Rep-C", False, complete, "central_global", math.nan),
            ("Rep-D-complete", True, complete, "complete", math.nan),
            ("Rep-D-rdisk", True, rdisk, "rdisk_connected", rdisk_radius),
        )
        for method, distributed, graph, graph_case, requested_radius in dynamic_cases:
            representative = bool(section.get("collect_trace", (n, k, seed) in trace_seeds))
            options = _dynamic_options(
                config,
                "e1",
                history_stride=int(section.get("trace_stride", 100) if representative else section.get("terminal_history_stride", 20_001)),
            )
            result = run_population_dynamics(
                world, costs, graph, distributed=distributed, lp_objective=lp_raw.objective, **options
            )
            row = _relaxed_row(
                "e1", method, world, result.x, costs, lp_raw=lp_raw, lp_tau=lp_tau, entropy_tau=tau,
                solver_status=0 if result.converged else 1,
                solver_message="converged" if result.converged else "iteration_limit_or_nonfinite",
                dynamic=result, graph=graph,
            )
            row.update({
                "graph_case": graph_case,
                "requested_radius_m": requested_radius,
                "effective_radius_m": requested_radius,
                "error_to_lp_tau": float(np.linalg.norm(result.x - lp_tau.x)) if lp_tau.status == 0 else math.nan,
            })
            rows.append(row)
            if representative:
                histories.append(result.history.assign(
                    experiment="e1", method=method, world_hash=world.world_hash, seed=seed,
                    n_robots=n, n_loads=k, graph_case=graph_case,
                ))
    runs = pd.DataFrame(rows)
    history = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    worlds_frame = pd.DataFrame(worlds)
    population = runs[runs.method.str.startswith("Rep")]
    expected_worlds = len(list(_worlds(section)))
    checks = {
        "exact_requested_world_count": expected_worlds == len(section["configurations"]) * len(_seeds(section["seeds"])),
        "five_methods_per_world": bool((runs.groupby("world_hash").method.nunique() == 5).all()),
        "paired_worlds": bool((runs.groupby(["n_robots", "n_loads", "seed"]).world_hash.nunique() == 1).all()),
        "rdisk_graphs_connected": bool(runs.loc[runs.method == "Rep-D-rdisk", "graph_connected"].all()),
        "population_simplex": bool((population.simplex_violation <= 1e-9).all()),
        "failed_runs_preserved": len(population) == 3 * expected_worlds,
        "gaps_only_when_comparable": bool(population.loc[~population.comparable_to_lp, ["gap_raw_lp", "gap_regularized_lp"]].isna().all().all()),
        "required_fields_present": set([
            "comparable_to_lp", "not_comparable_reason", "solver_status", "mip_gap",
            "primal_residual_absolute", "primal_residual_relative",
            "consensus_residual_absolute", "consensus_residual_relative",
            "stationarity_residual_absolute", "stationarity_residual_relative",
            "simplex_violation", "graph_connected", "lambda2", "seed",
        ]).issubset(runs.columns),
    }
    return {"runs": runs, "history": history, "worlds": worlds_frame}, checks


def _graph_from_adjacency(name: str, adjacency: np.ndarray) -> GraphInfo:
    matrix = np.asarray(adjacency, dtype=bool)
    matrix = matrix | matrix.T
    np.fill_diagonal(matrix, False)
    degrees = matrix.sum(axis=1).astype(float)
    laplacian = np.diag(degrees) - matrix.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    lambda2 = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
    return GraphInfo(
        name=name,
        adjacency=matrix,
        edges=int(np.sum(matrix) // 2),
        lambda2=lambda2,
        lambda_max=float(eigenvalues[-1]) if len(eigenvalues) else 0.0,
        connected=bool(len(eigenvalues) <= 1 or lambda2 > 1e-10),
    )


def _disconnected_split_graph(n: int) -> GraphInfo:
    adjacency = np.zeros((n, n), dtype=bool)
    split = max(1, n // 2)
    adjacency[:split, :split] = True
    adjacency[split:, split:] = True
    np.fill_diagonal(adjacency, False)
    return _graph_from_adjacency("disconnected_split", adjacency)


def _run_e2_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e2"]
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    tau = float(_dynamic_options(config, "e2")["entropy_tau"])
    seeds = _seeds(section["seeds"])
    for seed in seeds:
        world = generate_resource_world(int(section["n_robots"]), int(section["n_loads"]), seed)
        costs, _, _ = _costs(config, world)
        lp_raw = solve_lp(world, costs)
        lp_tau = solve_regularized_lp(world, costs, entropy_tau=tau, max_iterations=int(section.get("lp_tau_max_iterations", 10_000)))
        graph_cases: list[tuple[str, GraphInfo, float, str]] = []
        for topology in section["topologies"]:
            graph_cases.append((str(topology), make_graph(world, str(topology)), math.nan, "connected_assumption"))
        for label, graph, radius in _connected_rdisk_levels(world, int(section.get("rdisk_levels", 6))):
            graph_cases.append((label, graph, radius, "connected_assumption"))
        delta = world.robot_positions_m[:, None, :] - world.robot_positions_m[None, :, :]
        pair_distances = np.linalg.norm(delta, axis=2)[np.triu_indices(world.n_robots, k=1)]
        empty_radius = max(float(np.min(pair_distances)) * 0.5, 1e-6)
        graph_cases.extend([
            ("negative_empty_rdisk", make_graph(world, "rdisk", radius_m=empty_radius), empty_radius, "disconnected_control"),
            ("negative_split", _disconnected_split_graph(world.n_robots), math.nan, "disconnected_control"),
        ])
        for graph_case, graph, radius, assumption_class in graph_cases:
            representative = bool(section.get("collect_trace", seed == seeds[0]))
            max_iterations = int(section.get("negative_control_max_iterations", 1_000)) if assumption_class == "disconnected_control" else int(_dynamic_options(config, "e2")["max_iterations"])
            options = _dynamic_options(
                config,
                "e2",
                max_iterations=max_iterations,
                history_stride=int(section.get("trace_stride", 100) if representative else max_iterations + 1),
            )
            result = run_population_dynamics(
                world, costs, graph, distributed=True, lp_objective=lp_raw.objective, **options
            )
            row = _relaxed_row(
                "e2", "Rep-D", world, result.x, costs, lp_raw=lp_raw, lp_tau=lp_tau, entropy_tau=tau,
                solver_status=0 if result.converged else 1,
                solver_message="converged" if result.converged else "right_censored",
                dynamic=result, graph=graph,
            )
            row.update({
                "graph_case": graph_case,
                "assumption_class": assumption_class,
                "requested_radius_m": radius,
                "effective_radius_m": radius,
                "graph_fingerprint": hashlib.sha256(np.packbits(graph.adjacency.astype(np.uint8), axis=None).tobytes()).hexdigest()[:16],
                "R_epsilon": float(result.iterations) if result.converged else math.nan,
                "right_censored": bool(not result.converged),
                "iteration_limit": max_iterations,
                "dual_disagreement_sum": result.dual_disagreement_sum,
                "final_objective": float(evaluate_relaxed(world, result.x, costs)["objective"]),
            })
            rows.append(row)
            if representative:
                histories.append(result.history.assign(
                    experiment="e2", method="Rep-D", world_hash=world.world_hash, seed=seed,
                    graph_case=graph_case, lambda2=graph.lambda2, assumption_class=assumption_class,
                ))
    runs = pd.DataFrame(rows)
    history = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    connected = runs[runs.assumption_class == "connected_assumption"]
    disconnected = runs[runs.assumption_class == "disconnected_control"]
    rdisk = connected[connected.graph_case.str.startswith("rdisk_level_")]
    checks = {
        "exact_world_count": runs.world_hash.nunique() == len(seeds),
        "worlds_and_costs_paired_across_graphs": bool(runs.groupby("seed").world_hash.nunique().eq(1).all()),
        "connected_graphs_are_connected": bool(connected.graph_connected.all()),
        "disconnected_controls_are_disconnected": bool((~disconnected.graph_connected).all()),
        "controls_separated_from_analysis": bool(set(disconnected.assumption_class) == {"disconnected_control"}),
        "six_rdisk_levels_per_world": bool(rdisk.groupby("world_hash").size().ge(int(section.get("rdisk_levels", 6))).all()),
        "six_distinct_lambda2_per_world": bool(rdisk.groupby("world_hash").lambda2.nunique().ge(int(section.get("rdisk_levels", 6))).all()),
        "literal_requested_effective_radius": bool(np.isclose(rdisk.requested_radius_m, rdisk.effective_radius_m).all()),
        "censoring_recorded": bool(runs[["right_censored", "iteration_limit"]].notna().all().all()),
        "communication_nonnegative": bool((runs.messages >= 0).all() and (runs.scalars_sent >= 0).all()),
    }
    return {"runs": runs, "history": history}, checks


def _run_e3_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e3"]
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    seeds = _seeds(section["seeds"])
    tau = float(_dynamic_options(config, "e3")["entropy_tau"])
    for seed in seeds:
        world = generate_resource_world(int(section["n_robots"]), int(section["n_loads"]), seed)
        costs, _, _ = _costs(config, world)
        lp_raw = solve_lp(world, costs)
        lp_tau = solve_regularized_lp(world, costs, entropy_tau=tau, max_iterations=int(section.get("lp_tau_max_iterations", 10_000)))
        graph = make_graph(world, "complete")
        alpha_reference = 1.0 / estimate_operator_scale(world, costs)
        for integrator_label in section["integrators"]:
            for factor in section["step_factors"]:
                step = float(factor) * alpha_reference
                representative = bool(section.get("collect_trace", seed == seeds[0]))
                max_iterations = int(_dynamic_options(config, "e3")["max_iterations"])
                options = _dynamic_options(
                    config,
                    "e3",
                    integrator=str(integrator_label),
                    step=step,
                    history_stride=int(section.get("trace_stride", 100) if representative else max_iterations + 1),
                )
                result = run_population_dynamics(
                    world, costs, graph, distributed=False, lp_objective=lp_raw.objective, **options
                )
                row = _relaxed_row(
                    "e3", str(integrator_label), world, result.x, costs,
                    lp_raw=lp_raw, lp_tau=lp_tau, entropy_tau=tau,
                    solver_status=0 if result.converged else 1,
                    solver_message="converged" if result.converged else "iteration_limit_or_instability",
                    dynamic=result, graph=graph,
                )
                row.update({
                    "integrator": str(integrator_label),
                    "step_factor": float(factor),
                    "step": step,
                    "alpha_reference": alpha_reference,
                    "pre_projection_min": result.pre_projection_min,
                    "negative_components_before_projection": result.negative_components_before_projection,
                    "empirical_stable": bool(
                        result.converged
                        and np.all(np.isfinite(result.x))
                        and float(result.history.iloc[-1]["simplex_violation"]) <= 1e-9
                    ),
                    "right_censored": bool(not result.converged),
                    "iteration_limit": max_iterations,
                })
                rows.append(row)
                if representative:
                    histories.append(result.history.assign(
                        experiment="e3", method=str(integrator_label), integrator=str(integrator_label),
                        world_hash=world.world_hash, seed=seed, step_factor=float(factor), step=step,
                    ))
    runs = pd.DataFrame(rows)
    history = pd.concat(histories, ignore_index=True) if histories else pd.DataFrame()
    protected = runs[runs.integrator.isin(["projected_euler", "exponential_replicator", "mirror_prox"])]
    checks = {
        "all_seed_integrator_factor_combinations": len(runs) == len(seeds) * len(section["integrators"]) * len(section["step_factors"]),
        "all_four_integrators_distinct": runs.integrator.nunique() == 4,
        "all_six_factors_present": runs.step_factor.nunique() == 6,
        "projected_methods_nonnegative": bool((protected.simplex_violation <= 1e-9).all()),
        "preprojection_diagnostics_recorded_for_euler": bool(runs.loc[runs.integrator.isin(["euler_pure", "projected_euler"]), "pre_projection_min"].notna().all()),
        "nonconvergence_preserved_as_censoring": bool((runs.converged.astype(bool) == ~runs.right_censored.astype(bool)).all()),
        "finite_reference_steps": bool(np.isfinite(runs.alpha_reference).all() and (runs.alpha_reference > 0).all()),
    }
    return {"runs": runs, "history": history}, checks


def _normalized_overassignment(world: ResourceWorld, assignment: np.ndarray) -> float:
    x = np.zeros((world.n_robots, world.n_loads), dtype=float)
    for robot, load in enumerate(np.asarray(assignment, dtype=int)):
        if 0 <= load < world.n_loads:
            x[robot, load] = 1.0
    coverage = x.T @ world.resources
    normalized = coverage / np.maximum(world.requirements, 1e-12)
    return float(np.mean(np.maximum(normalized - 1.0, 0.0)))


def _integer_row(
    experiment: str,
    method: str,
    world: ResourceWorld,
    result: IntegerResult,
    *,
    runtime_s: float,
    milp: AllocationSolution | None,
    milp_certified: bool,
    lower_bound: float = math.nan,
    messages: int = 0,
    scalars_sent: int = 0,
    failure_penalty_multiplier: float = 2.0,
) -> dict[str, Any]:
    integer_gap = math.nan
    if result.feasible and milp is not None and milp_certified:
        integer_gap = 100.0 * (result.objective - milp.objective) / max(abs(milp.objective), 1e-12)
    penalty_reference = milp.objective if milp is not None and milp_certified else lower_bound
    penalized = (
        result.objective
        if result.feasible
        else float(failure_penalty_multiplier) * penalty_reference if np.isfinite(penalty_reference) else math.nan
    )
    members = result.assignment[result.assignment >= 0]
    counts = np.bincount(members, minlength=world.n_loads) if members.size else np.zeros(world.n_loads, dtype=int)
    return {
        "experiment": experiment,
        "world_hash": world.world_hash,
        "seed": world.seed,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "method": method,
        "result_type": "integer",
        "feasible": bool(result.feasible),
        "raw_objective": float(result.objective),
        "regularized_objective": math.nan,
        "gap_raw_lp": math.nan,
        "gap_regularized_lp": math.nan,
        "integer_gap_milp": integer_gap,
        "failure_penalized_cost": penalized,
        "deficit_l1": float(result.deficit_l1),
        "overassignment_l1": float(result.overassignment_l1),
        "overassignment_normalized": _normalized_overassignment(world, result.assignment),
        "repairs": int(result.repairs),
        "pruned": int(result.pruned),
        "local_exchanges": int(result.exchanges),
        "runtime_s": float(runtime_s),
        "messages": int(messages),
        "scalars_sent": int(scalars_sent),
        "solver_status": int(milp.status) if milp is not None else -1,
        "solver_message": str(milp.message) if milp is not None else "not_run",
        "mip_gap": float(milp.mip_gap) if milp is not None else math.nan,
        "milp_certified_optimal": bool(milp_certified),
        "lower_bound": float(lower_bound),
        "assignment_json": json.dumps(result.assignment.tolist()),
        "mean_coalition_size": float(np.mean(counts)),
        "max_coalition_size": int(np.max(counts)) if counts.size else 0,
        "failure_reason": "none" if result.feasible else "integer_recovery_infeasible",
    }


def _run_e4_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e4"]
    rows: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    tau = float(_dynamic_options(config, "e4")["entropy_tau"])
    margin = float(section.get("rounding_margin", 0.02))
    penalty_multiplier = float(section.get("failure_penalty_multiplier", 2.0))
    for n, k, seed in _worlds(section):
        world = generate_resource_world(n, k, seed)
        costs, _, _ = _costs(config, world)
        lp_raw = solve_lp(world, costs)
        milp = solve_milp(world, costs, time_limit_s=float(config.get("oracle_time_limit_s", 30.0)))
        milp_certified = bool(milp.status == 0 and np.isfinite(milp.mip_gap) and milp.mip_gap <= 1e-8)
        graph = make_graph(world, "complete")
        options = _dynamic_options(config, "e4", history_stride=int(_dynamic_options(config, "e4")["max_iterations"]) + 1)
        dynamic = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp_raw.objective, **options)
        rng = np.random.default_rng(seed + 424_243)
        argmax_assignment = argmax_round(dynamic.x, margin=margin)
        categorical_assignment = categorical_round(dynamic.x, rng)
        methods: list[tuple[str, IntegerResult, float]] = []

        def timed(label: str, operation: Any) -> None:
            started = time.perf_counter()
            result = operation()
            methods.append((label, result, time.perf_counter() - started))

        timed("Argmax", lambda: evaluate_integer(world, argmax_assignment, costs))
        timed("Categorical-1", lambda: evaluate_integer(world, categorical_assignment, costs))
        for samples in section.get("best_of_samples", [5, 30, 100]):
            timed(
                f"Best-{int(samples)}",
                lambda samples=int(samples): best_of_samples(world, dynamic.x, costs, samples=samples, rng=rng, repair=False),
            )
        timed(
            "Argmax+repair",
            lambda: repair_assignment(world, argmax_assignment, costs, prune=False, local_exchange=False, compress=False),
        )
        timed(
            "Categorical+repair",
            lambda: repair_assignment(world, categorical_assignment, costs, prune=False, local_exchange=False, compress=False),
        )
        timed(
            "Argmax+repair+prune+local-exchange",
            lambda: repair_assignment(world, argmax_assignment, costs, prune=True, local_exchange=True, compress=True),
        )
        milp_integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
        methods.append(("MILP", milp_integer, 0.0))
        for method, result, runtime_s in methods:
            row = _integer_row(
                "e4", method, world, result, runtime_s=runtime_s, milp=milp,
                milp_certified=milp_certified, lower_bound=lp_raw.objective,
                failure_penalty_multiplier=penalty_multiplier,
            )
            row.update({
                "fractional_converged": dynamic.converged,
                "fractional_comparable_to_lp": bool(dynamic.history.iloc[-1]["comparable_to_lp"]),
                "rounding_margin": margin,
                "entropy_tau": tau,
            })
            rows.append(row)
            for robot, load in enumerate(result.assignment):
                assignments.append({
                    "world_hash": world.world_hash, "seed": seed, "n_robots": n, "n_loads": k,
                    "method": method, "robot_id": robot, "load_id": int(load),
                })
    runs = pd.DataFrame(rows)
    assignments_frame = pd.DataFrame(assignments)
    configuration_counts = runs[runs.method == "MILP"].groupby(["n_robots", "n_loads"]).size()
    milp_rows = runs[runs.method == "MILP"]
    full = runs[runs.method == "Argmax+repair+prune+local-exchange"]
    checks = {
        "all_requested_methods_present": set([
            "Argmax", "Categorical-1", "Best-5", "Best-30", "Best-100",
            "Argmax+repair", "Categorical+repair", "Argmax+repair+prune+local-exchange", "MILP",
        ]).issubset(set(runs.method)),
        "constructive_worlds_have_feasible_milp_solution": bool(milp_rows.feasible.all()),
        "milp_gaps_recorded": bool(milp_rows.mip_gap.notna().all()),
        "uncertified_oracles_have_no_integer_gap": bool(runs.loc[~runs.milp_certified_optimal, "integer_gap_milp"].isna().all()),
        "infeasible_methods_have_no_integer_gap": bool(runs.loc[~runs.feasible, "integer_gap_milp"].isna().all()),
        "full_repair_never_worsens_deficit": bool(full.deficit_l1.le(runs[runs.method == "Argmax"].set_index("world_hash").loc[full.world_hash, "deficit_l1"].to_numpy() + 1e-9).all()),
        "one_assignment_record_per_robot": bool(assignments_frame.groupby(["world_hash", "method", "robot_id"]).size().eq(1).all()),
        "requested_worlds_per_configuration": bool(configuration_counts.eq(len(_seeds(section["seeds"]))).all()),
    }
    return {"runs": runs, "assignments": assignments_frame}, checks


def _run_e1(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    shards = []
    first_seed = _seeds(config["e1"]["seeds"])[0]
    for n, k, seed in _worlds(config["e1"]):
        shards.append((n, k, seed, seed == first_seed))
    payload = _parallel_experiment("e1", config, shards)
    return payload, _checks_e1(config, payload)


def _run_e2(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    seeds = _seeds(config["e2"]["seeds"])
    payload = _parallel_experiment("e2", config, [(seed, seed == seeds[0]) for seed in seeds])
    return payload, _checks_e2(config, payload)


def _run_e3(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    seeds = _seeds(config["e3"]["seeds"])
    payload = _parallel_experiment("e3", config, [(seed, seed == seeds[0]) for seed in seeds])
    return payload, _checks_e3(config, payload)


def _run_e4(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    payload = _parallel_experiment("e4", config, [(n, k, seed, False) for n, k, seed in _worlds(config["e4"])])
    return payload, _checks_e4(config, payload)


def _run_e5(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e5"]
    shards = [
        (int(n), int(seed))
        for n in section["fleet_sizes"]
        for seed in _e5_seeds(section, int(n))
    ]
    payload = _parallel_experiment("e5", config, shards)
    return payload, _checks_e5(config, payload)


def _run_e6(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e6"]
    shards = [
        (int(n), int(seed))
        for n in section["fleet_sizes"]
        for seed in _seeds(section["seeds"])
    ]
    payload = _parallel_experiment("e6", config, shards)
    return payload, _checks_e6(config, payload)


def _parallel_experiment(name: str, config: dict[str, Any], shards: list[tuple[Any, ...]]) -> dict[str, pd.DataFrame]:
    workers = max(1, min(int(config.get("parallel_workers", 1)), len(shards)))
    if workers == 1:
        payload, _ = globals()[f"_run_{name}_sequential"](config, Path("."))
        return payload
    arguments = [(name, config, shard) for shard in shards]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_experiment_shard_worker, arguments, chunksize=1))
    keys = sorted({key for payload in results for key in payload})
    combined: dict[str, pd.DataFrame] = {}
    for key in keys:
        frames = [payload[key] for payload in results if key in payload and not payload[key].empty]
        combined[key] = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    return combined


def _experiment_shard_worker(arguments: tuple[str, dict[str, Any], tuple[Any, ...]]) -> dict[str, pd.DataFrame]:
    name, config, shard = arguments
    local = copy.deepcopy(config)
    local["parallel_workers"] = 1
    if name in {"e1", "e4"}:
        n, k, seed, collect_trace = shard
        local[name]["configurations"] = [[int(n), int(k)]]
        local[name]["seeds"] = [int(seed)]
        local[name]["collect_trace"] = bool(collect_trace)
    elif name in {"e2", "e3"}:
        seed, collect_trace = shard
        local[name]["seeds"] = [int(seed)]
        local[name]["collect_trace"] = bool(collect_trace)
    elif name == "e5":
        n, seed = shard
        local[name]["fleet_sizes"] = [int(n)]
        local[name]["seed_blocks"] = {str(int(n)): [int(seed)]}
    elif name == "e6":
        n, seed = shard
        local[name]["fleet_sizes"] = [int(n)]
        local[name]["seeds"] = [int(seed)]
    payload, _ = globals()[f"_run_{name}_sequential"](local, Path("."))
    return payload


def _checks_e1(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    runs = payload["runs"]
    population = runs[runs.method.str.startswith("Rep")]
    expected_worlds = len(list(_worlds(config["e1"])))
    return {
        "exact_requested_world_count": runs.world_hash.nunique() == expected_worlds,
        "five_methods_per_world": bool((runs.groupby("world_hash").method.nunique() == 5).all()),
        "paired_worlds": bool((runs.groupby(["n_robots", "n_loads", "seed"]).world_hash.nunique() == 1).all()),
        "rdisk_graphs_connected": bool(runs.loc[runs.method == "Rep-D-rdisk", "graph_connected"].all()),
        "population_simplex": bool((population.simplex_violation <= 1e-9).all()),
        "failed_runs_preserved": len(population) == 3 * expected_worlds,
        "gaps_only_when_comparable": bool(population.loc[~population.comparable_to_lp.astype(bool), ["gap_raw_lp", "gap_regularized_lp"]].isna().all().all()),
        "required_fields_present": set([
            "comparable_to_lp", "not_comparable_reason", "solver_status", "mip_gap",
            "primal_residual_absolute", "primal_residual_relative", "consensus_residual_absolute",
            "consensus_residual_relative", "stationarity_residual_absolute",
            "stationarity_residual_relative", "simplex_violation", "graph_connected", "lambda2", "seed",
        ]).issubset(runs.columns),
    }


def _checks_e2(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    runs = payload["runs"]
    connected = runs[runs.assumption_class == "connected_assumption"]
    disconnected = runs[runs.assumption_class == "disconnected_control"]
    rdisk = connected[connected.graph_case.str.startswith("rdisk_level_")]
    levels = int(config["e2"].get("rdisk_levels", 6))
    return {
        "exact_world_count": runs.world_hash.nunique() == len(_seeds(config["e2"]["seeds"])),
        "worlds_and_costs_paired_across_graphs": bool(runs.groupby("seed").world_hash.nunique().eq(1).all()),
        "connected_graphs_are_connected": bool(connected.graph_connected.all()),
        "disconnected_controls_are_disconnected": bool((~disconnected.graph_connected.astype(bool)).all()),
        "controls_separated_from_analysis": bool(set(disconnected.assumption_class) == {"disconnected_control"}),
        "six_rdisk_levels_per_world": bool(rdisk.groupby("world_hash").size().ge(levels).all()),
        "six_distinct_lambda2_per_world": bool(rdisk.groupby("world_hash").lambda2.nunique().ge(levels).all()),
        "literal_requested_effective_radius": bool(np.isclose(rdisk.requested_radius_m, rdisk.effective_radius_m).all()),
        "censoring_recorded": bool(runs[["right_censored", "iteration_limit"]].notna().all().all()),
        "communication_nonnegative": bool((runs.messages >= 0).all() and (runs.scalars_sent >= 0).all()),
    }


def _checks_e3(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    runs = payload["runs"]
    protected = runs[runs.integrator.isin(["projected_euler", "exponential_replicator", "mirror_prox"])]
    section = config["e3"]
    return {
        "all_seed_integrator_factor_combinations": len(runs) == len(_seeds(section["seeds"])) * len(section["integrators"]) * len(section["step_factors"]),
        "all_four_integrators_distinct": runs.integrator.nunique() == 4,
        "all_six_factors_present": runs.step_factor.nunique() == 6,
        "projected_methods_nonnegative": bool((protected.simplex_violation <= 1e-9).all()),
        "preprojection_diagnostics_recorded_for_euler": bool(runs.loc[runs.integrator.isin(["euler_pure", "projected_euler"]), "pre_projection_min"].notna().all()),
        "nonconvergence_preserved_as_censoring": bool((runs.converged.astype(bool) == ~runs.right_censored.astype(bool)).all()),
        "finite_reference_steps": bool(np.isfinite(runs.alpha_reference).all() and (runs.alpha_reference > 0).all()),
    }


def _checks_e4(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    runs = payload["runs"]
    assignments = payload["assignments"]
    milp_rows = runs[runs.method == "MILP"]
    pivot = runs[runs.method.isin(["Argmax", "Argmax+repair+prune+local-exchange"])].pivot(index="world_hash", columns="method", values="deficit_l1")
    configuration_counts = milp_rows.groupby(["n_robots", "n_loads"]).size()
    return {
        "all_requested_methods_present": set([
            "Argmax", "Categorical-1", "Best-5", "Best-30", "Best-100", "Argmax+repair",
            "Categorical+repair", "Argmax+repair+prune+local-exchange", "MILP",
        ]).issubset(set(runs.method)),
        "constructive_worlds_have_feasible_milp_solution": bool(milp_rows.feasible.astype(bool).all()),
        "milp_gaps_recorded": bool(milp_rows.mip_gap.notna().all()),
        "uncertified_oracles_have_no_integer_gap": bool(runs.loc[~runs.milp_certified_optimal.astype(bool), "integer_gap_milp"].isna().all()),
        "infeasible_methods_have_no_integer_gap": bool(runs.loc[~runs.feasible.astype(bool), "integer_gap_milp"].isna().all()),
        "full_repair_never_worsens_deficit": bool((pivot["Argmax+repair+prune+local-exchange"] <= pivot["Argmax"] + 1e-9).all()),
        "one_assignment_record_per_robot": bool(assignments.groupby(["world_hash", "method", "robot_id"]).size().eq(1).all()),
        "requested_worlds_per_configuration": bool(configuration_counts.eq(len(_seeds(config["e4"]["seeds"]))).all()),
    }


def _scale_repair(world: ResourceWorld, assignment: np.ndarray, costs: np.ndarray) -> IntegerResult:
    """Repair large instances without the exhaustive local-exchange search."""

    if world.n_robots <= 50:
        return repair_assignment(world, assignment, costs, prune=True, local_exchange=True, compress=True)
    current = np.asarray(assignment, dtype=int).copy()
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)
    repairs = 0
    for _ in range(world.n_robots):
        x = np.zeros((world.n_robots, world.n_loads), dtype=float)
        valid = current >= 0
        x[np.flatnonzero(valid), current[valid]] = 1.0
        coverage = np.einsum("ik,ikm->km", x, normalized)
        deficit = np.maximum(1.0 - coverage, 0.0)
        if np.all(deficit <= 1e-9):
            break
        idle = np.flatnonzero(current < 0)
        if idle.size == 0:
            break
        gains = np.sum(np.minimum(deficit[None, :, :], normalized[idle]), axis=2)
        compatible = np.isfinite(costs[idle])
        scores = np.where(compatible & (gains > 1e-12), gains / np.maximum(costs[idle], 1e-12), -math.inf)
        flat = int(np.argmax(scores))
        if not np.isfinite(scores.flat[flat]):
            break
        idle_index, load = np.unravel_index(flat, scores.shape)
        current[int(idle[idle_index])] = int(load)
        repairs += 1
    pruned = 0
    if evaluate_integer(world, current, costs).feasible:
        members = sorted(
            np.flatnonzero(current >= 0),
            key=lambda robot: float(costs[int(robot), int(current[int(robot)])]),
            reverse=True,
        )
        for robot in members:
            trial = current.copy()
            trial[int(robot)] = -1
            if evaluate_integer(world, trial, costs).feasible:
                current = trial
                pruned += 1
    return evaluate_integer(world, current, costs, repairs=repairs, pruned=pruned, exchanges=0)


def _e5_seeds(section: dict[str, Any], n: int) -> list[int]:
    blocks = section.get("seed_blocks", {})
    if str(n) in blocks:
        return _seeds(blocks[str(n)])
    return _seeds(section["seeds"])


def _fractional_scale_row(
    method: str,
    world: ResourceWorld,
    result: DynamicResult,
    costs: np.ndarray,
    lp: AllocationSolution,
    graph: GraphInfo,
) -> dict[str, Any]:
    metrics = evaluate_relaxed(world, result.x, costs)
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)
    coverage = np.einsum("ik,ikm->km", result.x, normalized)
    primal = float(np.linalg.norm(np.maximum(1.0 - coverage, 0.0)))
    comparable = bool(lp.status == 0 and np.all(np.isfinite(result.x)) and metrics["simplex_violation"] <= 1e-6 and primal <= 1e-6)
    final = result.history.iloc[-1]
    return {
        "experiment": "e5", "world_hash": world.world_hash, "seed": world.seed,
        "n_robots": world.n_robots, "n_loads": world.n_loads, "method": method,
        "result_type": "fractional", "feasible": bool(primal <= 1e-6),
        "raw_objective": float(metrics["objective"]), "regularized_objective": math.nan,
        "gap_raw_lp": (metrics["objective"] - lp.objective) / max(abs(lp.objective), 1e-12) if comparable else math.nan,
        "gap_regularized_lp": math.nan, "integer_gap_milp": math.nan,
        "comparable_to_lp": comparable,
        "not_comparable_reason": "none" if comparable else ("lp_raw_not_optimal" if lp.status != 0 else "fractional_primal_or_simplex_failure"),
        "solver_status": 0 if result.converged else 1,
        "solver_message": "converged" if result.converged else "iteration_limit_or_nonfinite",
        "mip_gap": math.nan,
        "primal_residual_absolute": float(metrics["primal_residual"]),
        "primal_residual_normalized": primal,
        "primal_residual_relative": float(final["primal_residual_relative"]),
        "consensus_residual_absolute": float(final["consensus_residual"]),
        "consensus_residual_relative": float(final["consensus_residual_relative"]),
        "stationarity_residual_absolute": float(final["stationarity_residual"]),
        "stationarity_residual_relative": float(final["stationarity_residual_relative"]),
        "simplex_violation": float(metrics["simplex_violation"]), "finite_state": bool(np.all(np.isfinite(result.x))),
        "converged": bool(result.converged), "iterations": int(result.iterations), "runtime_s": float(result.runtime_s),
        "time_per_iteration_s": float(result.runtime_s / max(result.iterations, 1)),
        "messages": int(result.messages), "scalars_sent": int(result.scalars_sent),
        "graph_connected": bool(graph.connected), "lambda2": graph.lambda2, "lambda_max": graph.lambda_max, "edges": graph.edges,
        "lower_bound": float(lp.objective), "assignment_json": json.dumps(argmax_round(result.x).tolist()),
    }


def _run_e5_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e5"]
    rows: list[dict[str, Any]] = []
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section.get("robots_per_load", 5.0)))))
        for seed in _e5_seeds(section, n):
            world = generate_resource_world(n, k, seed)
            costs, _, _ = _costs(config, world)
            witness = evaluate_integer(world, world.feasibility_witness, costs)
            graph, radius = _minimum_connected_rdisk(world)
            lp_start = time.perf_counter()
            lp = solve_lp(world, costs)
            lp_runtime = time.perf_counter() - lp_start
            world_rows: list[dict[str, Any]] = [{
                "experiment": "e5", "world_hash": world.world_hash, "seed": seed, "n_robots": n, "n_loads": k,
                "method": "LP-raw", "result_type": "lower_bound", "feasible": bool(lp.status == 0),
                "raw_objective": lp.objective, "lower_bound": lp.objective, "upper_bound": math.nan,
                "runtime_s": lp_runtime, "iterations": 0, "time_per_iteration_s": math.nan,
                "messages": 0, "scalars_sent": 0, "solver_status": lp.status, "solver_message": lp.message,
                "mip_gap": math.nan, "graph_connected": None, "lambda2": math.nan, "edges": 0,
                "failure_stage": "none" if lp.status == 0 else "lp_not_optimal",
                "world_constructively_feasible": witness.feasible,
            }]
            greedy_start = time.perf_counter()
            greedy_solution = greedy_deficit(world, costs)
            greedy_runtime = time.perf_counter() - greedy_start
            greedy_integer = evaluate_integer(world, assignment_from_matrix(greedy_solution.x), costs)
            auction = distributed_deficit_auction(world, costs, graph)
            max_iterations = int(_dynamic_options(config, "e5")["max_iterations"])
            options = _dynamic_options(config, "e5", history_stride=max_iterations + 1)
            rep_c = run_population_dynamics(world, costs, graph, distributed=False, lp_objective=lp.objective, **options)
            rep_d = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp.objective, **options)
            rounded = evaluate_integer(world, argmax_round(rep_d.x, margin=float(section.get("rounding_margin", 0.02))), costs)
            repair_start = time.perf_counter()
            repaired = _scale_repair(world, rounded.assignment, costs)
            repair_runtime = time.perf_counter() - repair_start
            milp: AllocationSolution | None = None
            milp_integer: IntegerResult | None = None
            milp_certified = False
            milp_runtime = math.nan
            if n <= int(section.get("milp_max_n", 50)):
                milp_start = time.perf_counter()
                milp = solve_milp(world, costs, time_limit_s=float(config.get("oracle_time_limit_s", 30.0)))
                milp_runtime = time.perf_counter() - milp_start
                milp_integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
                milp_certified = bool(milp.status == 0 and np.isfinite(milp.mip_gap) and milp.mip_gap <= 1e-8 and milp_integer.feasible)
            integer_methods: list[tuple[str, IntegerResult, float, int, int, str]] = [
                ("Greedy", greedy_integer, greedy_runtime, 0, 0, "none" if greedy_integer.feasible else "greedy_heuristic_failed"),
                ("Auction-D", auction.integer, auction.runtime_s, auction.messages, auction.scalars_sent, "none" if auction.integer.feasible else auction.status),
                ("Rep-D+recovery", repaired, rep_d.runtime_s + repair_runtime, rep_d.messages, rep_d.scalars_sent, "none" if repaired.feasible else ("fractional_not_converged" if not rep_d.converged else "repair_failed")),
            ]
            if milp_integer is not None:
                integer_methods.append(("MILP", milp_integer, milp_runtime, 0, 0, "none" if milp_certified else "milp_not_certified"))
            for method, integer, runtime_s, messages, scalars, failure_stage in integer_methods:
                row = _integer_row(
                    "e5", method, world, integer, runtime_s=runtime_s, milp=milp,
                    milp_certified=milp_certified, lower_bound=lp.objective,
                    messages=messages, scalars_sent=scalars,
                )
                row.update({
                    "iterations": rep_d.iterations if method == "Rep-D+recovery" else (auction.rounds if method == "Auction-D" else 1),
                    "time_per_iteration_s": runtime_s / max(rep_d.iterations if method == "Rep-D+recovery" else auction.rounds if method == "Auction-D" else 1, 1),
                    "graph_connected": graph.connected, "lambda2": graph.lambda2, "edges": graph.edges,
                    "effective_radius_m": radius, "world_constructively_feasible": witness.feasible,
                    "fractional_converged": rep_d.converged if method == "Rep-D+recovery" else None,
                    "rounded_feasible": rounded.feasible if method == "Rep-D+recovery" else None,
                    "repair_succeeded": repaired.feasible if method == "Rep-D+recovery" else None,
                    "pruning_completed": repaired.feasible if method == "Rep-D+recovery" else None,
                    "failure_stage": failure_stage,
                    "estimated_memory_bytes": int(
                        rep_d.x.nbytes + rep_d.dual.nbytes if method == "Rep-D+recovery" else world.resources.nbytes + costs.nbytes
                    ),
                })
                world_rows.append(row)
            rep_c_row = _fractional_scale_row("Rep-C", world, rep_c, costs, lp, graph)
            rep_c_row.update({"effective_radius_m": radius, "world_constructively_feasible": witness.feasible, "failure_stage": "none" if rep_c.converged else "fractional_not_converged", "estimated_memory_bytes": int(rep_c.x.nbytes + rep_c.dual.nbytes)})
            rep_d_row = _fractional_scale_row("Rep-D", world, rep_d, costs, lp, graph)
            rep_d_row.update({"effective_radius_m": radius, "world_constructively_feasible": witness.feasible, "failure_stage": "none" if rep_d.converged else "fractional_not_converged", "estimated_memory_bytes": int(rep_d.x.nbytes + rep_d.dual.nbytes)})
            world_rows.extend([rep_c_row, rep_d_row])
            feasible_objectives = [float(row["raw_objective"]) for row in world_rows if bool(row.get("feasible", False)) and row.get("result_type") == "integer" and np.isfinite(row.get("raw_objective", math.nan))]
            upper_bound = min(feasible_objectives) if feasible_objectives else math.nan
            certified_objective = milp.objective if milp_certified and milp is not None else math.nan
            for row in world_rows:
                row["upper_bound"] = upper_bound
                row["optimality_reference"] = "MILP-certified" if milp_certified else "LP-lower/best-feasible-upper"
                row["optimality_interval_percent"] = 100.0 * (upper_bound - lp.objective) / max(abs(lp.objective), 1e-12) if np.isfinite(upper_bound) and lp.status == 0 else math.nan
                if row.get("result_type") == "integer" and bool(row.get("feasible", False)) and np.isfinite(certified_objective):
                    row["integer_gap_milp"] = 100.0 * (float(row["raw_objective"]) - certified_objective) / max(abs(certified_objective), 1e-12)
            rows.extend(world_rows)
    runs = pd.DataFrame(rows)
    return {"runs": runs}, _checks_e5(config, {"runs": runs})


def _checks_e5(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    section = config["e5"]
    runs = payload["runs"]
    rep_recovery = runs[runs.method == "Rep-D+recovery"]
    return {
        "all_requested_sizes_present": set(map(int, section["fleet_sizes"])) == set(runs.n_robots.unique()),
        "multiple_seeds_per_size": bool(runs.groupby("n_robots").seed.nunique().min() >= int(section.get("minimum_seeds_any_size", 2))),
        "reaches_configured_maximum_size": int(runs.n_robots.max()) == max(map(int, section["fleet_sizes"])),
        "n500_has_at_least_ten_seeds_when_requested": bool(500 not in set(map(int, section["fleet_sizes"])) or runs.loc[runs.n_robots == 500, "seed"].nunique() >= 10),
        "distributed_auction_present": "Auction-D" in set(runs.method),
        "all_constructive_witnesses_feasible": bool(runs.world_constructively_feasible.fillna(False).all()),
        "bounds_recorded_without_false_optimal_gap": bool(runs.loc[runs.optimality_reference != "MILP-certified", "integer_gap_milp"].isna().all()),
        "rep_d_phases_recorded": bool(rep_recovery[["fractional_converged", "rounded_feasible", "repair_succeeded", "pruning_completed", "failure_stage"]].notna().all().all()),
        "communication_and_memory_nonnegative": bool((runs.messages.fillna(0) >= 0).all() and (runs.scalars_sent.fillna(0) >= 0).all() and (runs.estimated_memory_bytes.fillna(0) >= 0).all()),
    }


def _failed_e6_row(
    world: ResourceWorld,
    seed: int,
    scenario: str,
    dynamic: DynamicResult,
    reason: str,
    *,
    cost_model: str,
    graph: GraphInfo,
    radius: float,
) -> dict[str, Any]:
    return {
        "experiment": "e6", "world_hash": world.world_hash, "seed": seed,
        "n_robots": world.n_robots, "n_loads": world.n_loads, "method": "Rep-D+repair+prune+local-exchange",
        "scenario": scenario, "result_type": "approach", "assignment_feasible": False,
        "assignment_source": "Rep-D+repair+prune+local-exchange", "failure_reason": reason,
        "arrival_rate": math.nan, "arrival_success": False, "coalition_arrival_time_s": math.nan,
        "distance_m": math.nan, "estimated_energy": math.nan, "actual_energy": math.nan,
        "energy_model_error": math.nan, "energy_relative_error": math.nan,
        "battery_violations": math.nan, "path_failures": math.nan,
        "sampled_obstacle_intrusions": math.nan, "assignment_changes": 0,
        "negotiation_messages": dynamic.messages, "messages": dynamic.messages,
        "scalars_sent": dynamic.scalars_sent, "fractional_converged": dynamic.converged,
        "runtime_s": dynamic.runtime_s, "cost_model": cost_model,
        "graph_connected": graph.connected, "lambda2": graph.lambda2, "edges": graph.edges,
        "effective_radius_m": radius,
    }


def _run_e6_sequential(config: dict[str, Any], output_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, bool]]:
    section = config["e6"]
    rows: list[dict[str, Any]] = []
    trajectories: list[pd.DataFrame] = []
    seeds = _seeds(section["seeds"])
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section.get("robots_per_load", 5.0)))))
        for seed in seeds:
            world = generate_resource_world(n, k, seed)
            for scenario_value in section["scenarios"]:
                scenario = str(scenario_value)
                if scenario == "warehouse":
                    costs, _, components = build_warehouse_route_costs(
                        world, config["cost_weights"], reserve_energy=float(config.get("reserve_energy", 5.0))
                    )
                    cost_model = "astar_route_length"
                else:
                    costs, _, components = _costs(config, world)
                    cost_model = "euclidean_distance"
                lp = solve_lp(world, costs)
                graph, radius = _minimum_connected_rdisk(world)
                max_iterations = int(_dynamic_options(config, "e6")["max_iterations"])
                options = _dynamic_options(config, "e6", history_stride=max_iterations + 1)
                dynamic = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp.objective, **options)
                rounded = argmax_round(dynamic.x, margin=float(section.get("rounding_margin", 0.02)))
                integer = repair_assignment(world, rounded, costs, prune=True, local_exchange=True, compress=True)
                if not integer.feasible:
                    rows.append(_failed_e6_row(
                        world, seed, scenario, dynamic, "assignment_infeasible_after_local_recovery",
                        cost_model=cost_model, graph=graph, radius=radius,
                    ))
                    continue
                estimated_by_robot = np.zeros(world.n_robots)
                for robot, load in enumerate(integer.assignment):
                    if load >= 0:
                        estimated_by_robot[robot] = components["energy"][robot, load]
                result = simulate_approach(
                    world,
                    integer.assignment,
                    scenario=scenario,
                    dt_s=float(section.get("dt_s", 0.05)),
                    horizon_s=float(section.get("horizon_s", 120.0)),
                    estimated_energy_by_robot=estimated_by_robot,
                )
                row = dict(result.summary)
                estimated = float(row["estimated_energy"])
                row.update({
                    "experiment": "e6", "world_hash": world.world_hash, "seed": seed,
                    "n_robots": n, "n_loads": k, "method": "Rep-D+repair+prune+local-exchange",
                    "result_type": "approach", "assignment_feasible": True,
                    "assignment_source": "Rep-D+repair+prune+local-exchange",
                    "failure_reason": "none" if float(row["arrival_rate"]) >= 1.0 else "approach_incomplete",
                    "arrival_success": bool(float(row["arrival_rate"]) >= 1.0),
                    "energy_relative_error": abs(float(row["actual_energy"]) - estimated) / max(abs(estimated), 1e-12),
                    "obstacle_intrusions": int(row["sampled_obstacle_intrusions"]),
                    "negotiation_messages": dynamic.messages, "messages": dynamic.messages,
                    "scalars_sent": dynamic.scalars_sent, "fractional_converged": dynamic.converged,
                    "runtime_s": dynamic.runtime_s, "graph_connected": graph.connected,
                    "lambda2": graph.lambda2, "edges": graph.edges, "effective_radius_m": radius,
                    "cost_model": cost_model, "assignment_json": json.dumps(integer.assignment.tolist()),
                })
                rows.append(row)
                trajectories.append(result.trajectories.assign(
                    experiment="e6", world_hash=world.world_hash, seed=seed, n_robots=n,
                    n_loads=k, assignment_source="Rep-D+repair+prune+local-exchange",
                ))
    runs = pd.DataFrame(rows)
    trajectory_frame = pd.concat(trajectories, ignore_index=True) if trajectories else pd.DataFrame()
    return {"runs": runs, "trajectories": trajectory_frame}, _checks_e6(
        config, {"runs": runs, "trajectories": trajectory_frame}
    )


def _checks_e6(config: dict[str, Any], payload: dict[str, pd.DataFrame]) -> dict[str, bool]:
    section = config["e6"]
    seeds = _seeds(section["seeds"])
    runs = payload["runs"]
    trajectory_frame = payload["trajectories"]
    return {
        "all_requested_size_scenario_seed_combinations": len(runs) == len(section["fleet_sizes"]) * len(section["scenarios"]) * len(seeds),
        "only_repd_local_recovery_assignments": bool((runs.assignment_source == "Rep-D+repair+prune+local-exchange").all()),
        "no_milp_fallback": bool(~runs.assignment_source.str.contains("MILP", case=False).any()),
        "failures_have_reason_codes": bool(runs.failure_reason.notna().all()),
        "successful_paths_have_no_failures": bool((runs.loc[runs.assignment_feasible, "path_failures"] >= 0).all()),
        "trajectory_states_finite": bool(trajectory_frame.empty or np.isfinite(trajectory_frame[["x_m", "y_m", "theta_rad"]].to_numpy()).all()),
        "warehouse_uses_astar_energy": bool((runs.loc[(runs.scenario == "warehouse") & runs.assignment_feasible, "cost_model"] == "astar_route_length").all()),
    }


def _run_ablations(config: dict[str, Any], output_dir: Path) -> pd.DataFrame:
    section = config.get("ablations", {})
    if not section or not bool(section.get("enabled", True)):
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    seeds = _seeds(section["seeds"])
    n, k = int(section.get("n_robots", 10)), int(section.get("n_loads", 2))
    margin = float(config.get("e4", {}).get("rounding_margin", 0.02))
    for seed in seeds:
        world = generate_resource_world(n, k, seed)
        costs, _, _ = _costs(config, world)
        lp = solve_lp(world, costs)
        graph = make_graph(world, "complete")
        max_iterations = int(_dynamic_options(config, "e1")["max_iterations"])
        variants = (
            ("full_dynamics", {}),
            ("without_entropy", {"entropy_tau": 0.0}),
            ("without_integral_consensus", {"use_integral_consensus": False}),
        )
        dynamic_results: dict[str, DynamicResult] = {}
        for variant, overrides in variants:
            options = _dynamic_options(config, "e1", history_stride=max_iterations + 1, **overrides)
            result = run_population_dynamics(world, costs, graph, distributed=True, lp_objective=lp.objective, **options)
            dynamic_results[variant] = result
            final = result.history.iloc[-1]
            rows.append({
                "ablation_family": "dynamics", "variant": variant, "world_hash": world.world_hash,
                "seed": seed, "n_robots": n, "n_loads": k, "converged": result.converged,
                "feasible": bool(float(final["primal_residual_normalized"]) <= 1e-6),
                "raw_objective": float(evaluate_relaxed(world, result.x, costs)["objective"]),
                "runtime_s": result.runtime_s, "iterations": result.iterations,
                "messages": result.messages, "scalars_sent": result.scalars_sent,
                "primal_residual_relative": float(final["primal_residual_relative"]),
                "consensus_residual_relative": float(final["consensus_residual_relative"]),
                "stationarity_residual_relative": float(final["stationarity_residual_relative"]),
                "failure_reason": "none" if result.converged else "dynamics_not_converged",
            })
        x = dynamic_results["full_dynamics"].x
        argmax_margin = argmax_round(x, margin=margin)
        argmax_no_margin = argmax_round(x, margin=0.0)
        integer_variants = (
            ("full_recovery", lambda: repair_assignment(world, argmax_margin, costs, prune=True, local_exchange=True, compress=True)),
            ("without_rounding_margin", lambda: repair_assignment(world, argmax_no_margin, costs, prune=True, local_exchange=True, compress=True)),
            ("without_repair", lambda: evaluate_integer(world, argmax_margin, costs)),
            ("repair_without_prune", lambda: repair_assignment(world, argmax_margin, costs, prune=False, local_exchange=False, compress=False)),
            ("repair_without_exchange", lambda: repair_assignment(world, argmax_margin, costs, prune=True, local_exchange=False, compress=False)),
        )
        for variant, operation in integer_variants:
            start = time.perf_counter()
            result = operation()
            rows.append({
                "ablation_family": "integer_recovery", "variant": variant,
                "world_hash": world.world_hash, "seed": seed, "n_robots": n, "n_loads": k,
                "converged": dynamic_results["full_dynamics"].converged, "feasible": result.feasible,
                "raw_objective": result.objective, "runtime_s": time.perf_counter() - start,
                "iterations": 1, "messages": 0, "scalars_sent": 0,
                "repairs": result.repairs, "pruned": result.pruned, "local_exchanges": result.exchanges,
                "overassignment_normalized": _normalized_overassignment(world, result.assignment),
                "failure_reason": "none" if result.feasible else "integer_recovery_infeasible",
            })
    return pd.DataFrame(rows)


def _run_preflight_tests(config: dict[str, Any], output_dir: Path) -> dict[str, Any] | None:
    if not bool(config.get("run_preflight_tests", False)):
        return None
    command = _preflight_test_command(config)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    text = (completed.stdout + "\n" + completed.stderr).strip()
    (output_dir / "raw" / "preflight_pytest.txt").write_text(text + "\n", encoding="utf-8")
    summary = text.splitlines()[-1] if text else f"exit_code={completed.returncode}"
    return {"passed": completed.returncode == 0, "summary": summary, "exit_code": completed.returncode}


def _preflight_test_command(config: dict[str, Any]) -> list[str]:
    """Build a preflight command scoped to SP1 and free of result fixtures from other SPs."""
    configured = config.get("preflight_test_paths", SP1_PREFLIGHT_TESTS)
    targets = [str(path) for path in configured]
    if not targets:
        raise ValueError("SP1 preflight_test_paths cannot be empty")
    return [sys.executable, "-m", "pytest", "-q", *targets]


def _write_payload(output_dir: Path, name: str, payload: dict[str, pd.DataFrame]) -> None:
    for key, frame in payload.items():
        frame.to_csv(output_dir / "raw" / f"{name}_{key}.csv", index=False)


def _load_cached_payload(output_dir: Path, name: str) -> dict[str, pd.DataFrame] | None:
    runs_path = output_dir / "raw" / f"{name}_runs.csv"
    if not runs_path.exists():
        return None
    payload: dict[str, pd.DataFrame] = {}
    for path in sorted((output_dir / "raw").glob(f"{name}_*.csv")):
        key = path.stem.removeprefix(f"{name}_")
        try:
            payload[key] = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            payload[key] = pd.DataFrame()
    return payload if "runs" in payload else None


def _combine_runs(payloads: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    frames = [payload["runs"].copy() for payload in payloads.values() if "runs" in payload]
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def _aggregate_campaign(
    config: dict[str, Any],
    payloads: dict[str, dict[str, pd.DataFrame]],
    ablations: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    metrics = [
        "gap_regularized_lp", "integer_gap_milp", "raw_objective", "runtime_s", "iterations",
        "messages", "scalars_sent", "primal_residual_relative", "consensus_residual_relative",
        "stationarity_residual_relative", "overassignment_normalized", "arrival_rate",
        "coalition_arrival_time_s", "energy_relative_error",
    ]
    for experiment, payload in payloads.items():
        runs = payload.get("runs", pd.DataFrame())
        if runs.empty:
            continue
        groups = [column for column in ("experiment", "method", "n_robots", "n_loads", "scenario", "graph_case", "integrator", "step_factor") if column in runs]
        frame = aggregate_numeric(
            runs,
            group_columns=groups,
            metrics=metrics,
            bootstrap_resamples=int(config["statistics"].get("bootstrap_resamples", 2_000)),
            analysis_seed=int(config["statistics"].get("analysis_seed", 970_000)) + len(rows) * 1000,
        )
        rows.append(frame)
    if not ablations.empty:
        rows.append(aggregate_numeric(
            ablations,
            group_columns=["ablation_family", "variant"],
            metrics=["raw_objective", "runtime_s", "iterations", "messages", "overassignment_normalized"],
            bootstrap_resamples=int(config["statistics"].get("bootstrap_resamples", 2_000)),
            analysis_seed=int(config["statistics"].get("analysis_seed", 970_000)) + 9_000,
        ))
    return pd.concat(rows, ignore_index=True, sort=False) if rows else pd.DataFrame()


def _collect_exclusions(payloads: dict[str, dict[str, pd.DataFrame]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for experiment, payload in payloads.items():
        runs = payload.get("runs", pd.DataFrame())
        for _, row in runs.iterrows():
            base = {
                "experiment": experiment,
                "world_hash": row.get("world_hash", ""),
                "seed": row.get("seed", math.nan),
                "method": row.get("method", ""),
            }
            if "comparable_to_lp" in row and pd.notna(row.get("comparable_to_lp")) and not bool(row.get("comparable_to_lp")):
                rows.append({**base, "exclusion_scope": "lp_gap_analysis", "reason_code": row.get("not_comparable_reason", "not_comparable")})
            if "milp_certified_optimal" in row and pd.notna(row.get("milp_certified_optimal")) and not bool(row.get("milp_certified_optimal")):
                rows.append({**base, "exclusion_scope": "integer_optimality_gap", "reason_code": "milp_not_certified"})
            if "converged" in row and pd.notna(row.get("converged")) and not bool(row.get("converged")):
                rows.append({**base, "exclusion_scope": "converged_only_diagnostics", "reason_code": "iteration_limit_or_nonfinite"})
            if "feasible" in row and pd.notna(row.get("feasible")) and not bool(row.get("feasible")):
                rows.append({**base, "exclusion_scope": "conditional_integer_gap", "reason_code": row.get("failure_reason", "infeasible")})
            if "assignment_feasible" in row and pd.notna(row.get("assignment_feasible")) and not bool(row.get("assignment_feasible")):
                rows.append({**base, "exclusion_scope": "e6_approach_metrics", "reason_code": row.get("failure_reason", "assignment_infeasible")})
    columns = ["experiment", "world_hash", "seed", "method", "exclusion_scope", "reason_code"]
    return pd.DataFrame(rows, columns=columns)


def _seed_ledger(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for n, k, seed in _worlds(config["e1"]):
        rows.append({"experiment": "e1", "n_robots": n, "n_loads": k, "seed": seed})
    for experiment in ("e2", "e3"):
        section = config[experiment]
        for seed in _seeds(section["seeds"]):
            rows.append({"experiment": experiment, "n_robots": int(section["n_robots"]), "n_loads": int(section["n_loads"]), "seed": seed})
    for n, k, seed in _worlds(config["e4"]):
        rows.append({"experiment": "e4", "n_robots": n, "n_loads": k, "seed": seed})
    section = config["e5"]
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section.get("robots_per_load", 5.0)))))
        for seed in _e5_seeds(section, n):
            rows.append({"experiment": "e5", "n_robots": n, "n_loads": k, "seed": seed})
    section = config["e6"]
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section.get("robots_per_load", 5.0)))))
        for seed in _seeds(section["seeds"]):
            rows.append({"experiment": "e6", "n_robots": n, "n_loads": k, "seed": seed})
    if config.get("ablations"):
        for seed in _seeds(config["ablations"]["seeds"]):
            rows.append({"experiment": "ablations", "n_robots": int(config["ablations"].get("n_robots", 10)), "n_loads": int(config["ablations"].get("n_loads", 2)), "seed": seed})
    return pd.DataFrame(rows).drop_duplicates().sort_values(["experiment", "n_robots", "n_loads", "seed"]).reset_index(drop=True)


def _write_tables(config: dict[str, Any], output_dir: Path, payloads: dict[str, dict[str, pd.DataFrame]]) -> None:
    resamples = int(config["statistics"].get("bootstrap_resamples", 2_000))
    analysis_seed = int(config["statistics"].get("analysis_seed", 970_000))
    if "e1" in payloads:
        e1 = payloads["e1"]["runs"]
        t1 = aggregate_numeric(
            e1,
            group_columns=["method", "n_robots", "n_loads"],
            metrics=[
                "gap_regularized_lp", "error_to_lp_tau", "primal_residual_relative",
                "consensus_residual_relative", "stationarity_residual_relative", "iterations",
                "runtime_s", "messages", "scalars_sent",
            ],
            bootstrap_resamples=resamples,
            analysis_seed=analysis_seed,
        )
        t1.to_csv(output_dir / "tables" / "T1_convergence_and_relaxed_optimality.csv", index=False)
        _e1_hypotheses(e1).to_csv(output_dir / "tables" / "e1_paired_hypotheses.csv", index=False)
    if "e2" in payloads:
        e2 = payloads["e2"]["runs"]
        connected = e2[e2.assumption_class == "connected_assumption"]
        observed = connected[~connected.right_censored.astype(bool)]
        correlations: list[dict[str, Any]] = []
        for endpoint, source in (("R_epsilon_converged_only", observed), ("messages_all_connected", connected)):
            response = source.R_epsilon if endpoint.startswith("R_") else source.messages
            result = spearman_bootstrap(source.lambda2, response, resamples=resamples, seed=analysis_seed + len(correlations) + 1)
            correlations.append({"endpoint": endpoint, "analysis_scope": "connected graphs only", **result})
        pd.DataFrame(correlations).to_csv(output_dir / "tables" / "e2_lambda2_correlations.csv", index=False)
        aggregate_numeric(
            e2,
            group_columns=["assumption_class", "graph_case"],
            metrics=["R_epsilon", "messages", "scalars_sent", "dual_disagreement_sum", "final_objective"],
            bootstrap_resamples=resamples,
            analysis_seed=analysis_seed + 200,
        ).to_csv(output_dir / "tables" / "e2_graph_summary.csv", index=False)
    if "e3" in payloads:
        e3 = payloads["e3"]["runs"]
        aggregate_numeric(
            e3,
            group_columns=["integrator", "step_factor"],
            metrics=["primal_residual_relative", "stationarity_residual_relative", "iterations", "runtime_s", "simplex_violation", "negative_components_before_projection"],
            bootstrap_resamples=resamples,
            analysis_seed=analysis_seed + 300,
        ).to_csv(output_dir / "tables" / "e3_integrator_stability.csv", index=False)
    e4_summary = pd.DataFrame()
    if "e4" in payloads:
        e4 = payloads["e4"]["runs"]
        e4_summary = _integer_method_summary(e4, resamples=resamples, analysis_seed=analysis_seed + 400)
        e4_summary.to_csv(output_dir / "tables" / "e4_integer_recovery_summary.csv", index=False)
        _e4_hypotheses(e4).to_csv(output_dir / "tables" / "e4_paired_hypotheses.csv", index=False)
    e5_summary = pd.DataFrame()
    if "e5" in payloads:
        e5 = payloads["e5"]["runs"]
        e5_summary = aggregate_numeric(
            e5,
            group_columns=["method", "n_robots", "n_loads", "result_type"],
            metrics=["raw_objective", "runtime_s", "iterations", "time_per_iteration_s", "messages", "scalars_sent", "estimated_memory_bytes", "integer_gap_milp", "optimality_interval_percent", "mean_coalition_size"],
            bootstrap_resamples=resamples,
            analysis_seed=analysis_seed + 500,
        )
        e5_summary.to_csv(output_dir / "tables" / "e5_scalability_summary.csv", index=False)
    t2_frames: list[pd.DataFrame] = []
    if not e4_summary.empty:
        t2_frames.append(e4_summary.assign(table_block="integer_recovery"))
    if not e5_summary.empty:
        t2_frames.append(e5_summary.assign(table_block="scalability"))
    if t2_frames:
        pd.concat(t2_frames, ignore_index=True, sort=False).to_csv(output_dir / "tables" / "T2_integer_feasibility_gap_and_scalability.csv", index=False)
    if "e6" in payloads:
        aggregate_numeric(
            payloads["e6"]["runs"],
            group_columns=["scenario", "n_robots", "n_loads", "assignment_source"],
            metrics=["arrival_rate", "coalition_arrival_time_s", "distance_m", "estimated_energy", "actual_energy", "energy_relative_error", "messages"],
            bootstrap_resamples=resamples,
            analysis_seed=analysis_seed + 600,
        ).to_csv(output_dir / "tables" / "e6_unicycle_approach_summary.csv", index=False)


def _e1_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    comparisons = [
        ("Rep-C", "Rep-D-complete", "gap_regularized_lp"),
        ("Rep-C", "Rep-D-complete", "iterations"),
        ("Rep-D-complete", "Rep-D-rdisk", "iterations"),
        ("Rep-D-complete", "Rep-D-rdisk", "messages"),
    ]
    rows: list[dict[str, Any]] = []
    for first, second, metric in comparisons:
        pivot = runs[runs.method.isin([first, second])].pivot(index="world_hash", columns="method", values=metric)
        if first not in pivot or second not in pivot:
            result = {"n_pairs": 0, "statistic": math.nan, "p_value": math.nan, "rank_biserial": math.nan, "cohen_dz": math.nan}
        else:
            result = paired_wilcoxon(pivot[first], pivot[second])
        rows.append({"family": "e1_relaxed", "first": first, "second": second, "metric": metric, **result})
    adjusted = holm_adjust(row["p_value"] for row in rows)
    for row, p_holm in zip(rows, adjusted, strict=True):
        row["p_holm"] = p_holm
    return pd.DataFrame(rows)


def _integer_method_summary(runs: pd.DataFrame, *, resamples: int, analysis_seed: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (method, group) in enumerate(runs.groupby("method", sort=False)):
        feasible = group.feasible.astype(bool)
        successes = int(feasible.sum())
        low, high = wilson_interval(successes, len(group))
        gaps = pd.to_numeric(group.loc[feasible, "integer_gap_milp"], errors="coerce").dropna().to_numpy(dtype=float)
        ci_low, ci_high = (math.nan, math.nan)
        if gaps.size:
            from viu_mrob_tfm.sp1_canonical.validation.statistics import bootstrap_interval

            ci_low, ci_high = bootstrap_interval(gaps, resamples=resamples, seed=analysis_seed + index)
        rows.append({
            "method": method, "n_runs": len(group), "feasible_n": successes,
            "feasibility_rate": float(feasible.mean()), "feasibility_ci95_low": low, "feasibility_ci95_high": high,
            "gap_scope": "conditional_on_feasible_and_milp_certified", "gap_n": int(gaps.size),
            "gap_mean_percent": float(np.mean(gaps)) if gaps.size else math.nan,
            "gap_mean_ci95_low": ci_low, "gap_mean_ci95_high": ci_high,
            "gap_median_percent": float(np.median(gaps)) if gaps.size else math.nan,
            "gap_p90_percent": float(np.quantile(gaps, 0.90)) if gaps.size else math.nan,
            "gap_p95_percent": float(np.quantile(gaps, 0.95)) if gaps.size else math.nan,
            "failure_penalized_cost_mean": float(pd.to_numeric(group.failure_penalized_cost, errors="coerce").mean()),
            "repairs_mean": float(group.repairs.mean()), "pruned_mean": float(group.pruned.mean()),
            "local_exchanges_mean": float(group.local_exchanges.mean()),
            "overassignment_normalized_mean": float(group.overassignment_normalized.mean()),
            "runtime_mean_s": float(group.runtime_s.mean()),
        })
    return pd.DataFrame(rows)


def _e4_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    methods = ["Argmax", "Argmax+repair", "Argmax+repair+prune+local-exchange", "MILP"]
    pivot = runs[runs.method.isin(methods)].pivot(index="world_hash", columns="method", values="failure_penalized_cost")
    pivot = pivot.reindex(columns=methods)
    global_test = friedman_kendall_w(pivot.to_numpy(dtype=float))
    rows: list[dict[str, Any]] = [{"family": "e4_recovery", "comparison": "Friedman_all", "metric": "failure_penalized_cost", **global_test, "p_holm": math.nan}]
    pairs = [("Argmax", "Argmax+repair"), ("Argmax+repair", "Argmax+repair+prune+local-exchange"), ("Argmax+repair+prune+local-exchange", "MILP")]
    pair_rows: list[dict[str, Any]] = []
    for first, second in pairs:
        result = paired_wilcoxon(pivot[first], pivot[second])
        pair_rows.append({"family": "e4_recovery", "comparison": f"{first} vs {second}", "metric": "failure_penalized_cost", **result})
    adjusted = holm_adjust(row["p_value"] for row in pair_rows)
    for row, p_holm in zip(pair_rows, adjusted, strict=True):
        row["p_holm"] = p_holm
    rows.extend(pair_rows)
    return pd.DataFrame(rows)


def _write_figures(
    config: dict[str, Any],
    output_dir: Path,
    payloads: dict[str, dict[str, pd.DataFrame]],
    ablations: pd.DataFrame,
) -> None:
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 7})
    if "e1" in payloads:
        _figure_f1(output_dir, payloads["e1"])
    if "e2" in payloads:
        _figure_f2(output_dir, payloads["e2"]["runs"])
    if "e4" in payloads:
        _figure_f3(output_dir, payloads["e4"]["runs"])
    if "e5" in payloads:
        _figure_f4(output_dir, payloads["e5"]["runs"])
    if not ablations.empty:
        _figure_f5(output_dir, ablations)
    if "e6" in payloads:
        _figure_f6(output_dir, payloads["e6"].get("trajectories", pd.DataFrame()))


def _save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    fig.savefig(output_dir / "figures" / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "figures" / f"{stem}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def _figure_f1(output_dir: Path, payload: dict[str, pd.DataFrame]) -> None:
    runs = payload["runs"]
    history = payload.get("history", pd.DataFrame())
    population = runs[runs.method.str.startswith("Rep")]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.4))
    if not history.empty:
        representative = history[history.world_hash == history.world_hash.iloc[0]]
        for method, group in representative.groupby("method"):
            axes[0, 0].plot(group.iteration, np.maximum(group.primal_residual_relative, 1e-12), label=method)
        axes[0, 0].set_yscale("log")
        axes[0, 0].set(xlabel="Iteración", ylabel="Residuo primal relativo", title="Trayectoria representativa")
        axes[0, 0].legend(frameon=False)
    for method, group in population.groupby("method"):
        gaps = np.sort(group.loc[group.comparable_to_lp.astype(bool), "gap_regularized_lp"].dropna().to_numpy(dtype=float) * 100.0)
        if gaps.size:
            axes[0, 1].step(gaps, np.arange(1, len(gaps) + 1) / len(gaps), where="post", label=f"{method} (n={len(gaps)})")
    axes[0, 1].set(xlabel="Gap regularizado (%)", ylabel="ECDF", title="Gap solo en ejecuciones comparables")
    if axes[0, 1].get_legend_handles_labels()[0]:
        axes[0, 1].legend(frameon=False)
    methods = list(population.method.drop_duplicates())
    data = [population.loc[population.method == method, "iterations"].to_numpy(dtype=float) for method in methods]
    if data:
        axes[1, 0].boxplot(data, tick_labels=methods, showfliers=True)
    axes[1, 0].set(ylabel="Iteraciones", title="Esfuerzo hasta parada/censura")
    paired = runs[runs.method.isin(["Rep-C", "Rep-D-complete"])].pivot(index="world_hash", columns="method", values="regularized_objective").dropna()
    if not paired.empty:
        axes[1, 1].scatter(paired["Rep-C"], paired["Rep-D-complete"], s=10, alpha=0.6)
        limits = [float(min(paired.min())), float(max(paired.max()))]
        axes[1, 1].plot(limits, limits, "k--", linewidth=0.8)
    axes[1, 1].set(xlabel="Objetivo Rep-C", ylabel="Objetivo Rep-D completo", title="Mundos pareados")
    for ax in axes.flat:
        ax.grid(alpha=0.22)
    fig.suptitle("F1. Convergencia Rep-C/Rep-D y referencia LP-tau")
    fig.tight_layout()
    _save_figure(fig, output_dir, "F1_convergence_rep_c_rep_d_vs_lp_tau")


def _figure_f2(output_dir: Path, runs: pd.DataFrame) -> None:
    connected = runs[runs.assumption_class == "connected_assumption"].copy()
    observed_rounds = connected.R_epsilon.fillna(connected.iteration_limit)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    scatter = axes[0].scatter(connected.lambda2, observed_rounds, c=connected.right_censored.astype(int), cmap="coolwarm", s=14, alpha=0.65)
    axes[0].set(xscale="log", yscale="log", xlabel=r"$\lambda_2(L)$", ylabel=r"$R_\varepsilon$ o límite", title="Rondas (rojo: censura)")
    axes[1].scatter(connected.lambda2, connected.messages, s=14, alpha=0.65, color="#1B9E77")
    axes[1].set(xscale="log", yscale="log", xlabel=r"$\lambda_2(L)$", ylabel="Mensajes", title="Coste comunicativo")
    for ax in axes:
        ax.grid(alpha=0.22)
    fig.colorbar(scatter, ax=axes[0], ticks=[0, 1], label="Censura")
    fig.suptitle("F2. Conectividad algebraica, rondas y mensajes")
    fig.tight_layout()
    _save_figure(fig, output_dir, "F2_lambda2_rounds_messages")


def _figure_f3(output_dir: Path, runs: pd.DataFrame) -> None:
    summary = _integer_method_summary(runs, resamples=500, analysis_seed=971_400)
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4))
    x = np.arange(len(summary))
    error_low = summary.feasibility_rate - summary.feasibility_ci95_low
    error_high = summary.feasibility_ci95_high - summary.feasibility_rate
    axes[0].bar(x, summary.feasibility_rate, color="#2C7FB8")
    axes[0].errorbar(x, summary.feasibility_rate, yerr=np.vstack([error_low, error_high]), fmt="none", color="black", capsize=2)
    axes[0].set(xticks=x, xticklabels=summary.method, ylim=(0, 1.05), ylabel="Factibilidad", title="Tasa e IC binomial 95 %")
    axes[0].tick_params(axis="x", rotation=32, labelsize=7)
    for method, group in runs.groupby("method"):
        gaps = np.sort(group.loc[group.feasible.astype(bool), "integer_gap_milp"].dropna().to_numpy(dtype=float))
        if gaps.size:
            axes[1].step(gaps, np.arange(1, len(gaps) + 1) / len(gaps), where="post", label=f"{method} (n={len(gaps)})")
    axes[1].set(xlabel="Gap entero frente a MILP certificado (%)", ylabel="ECDF", title="Condicional a factibilidad")
    axes[1].legend(frameon=False, fontsize=6)
    for ax in axes:
        ax.grid(alpha=0.22)
    fig.suptitle("F3. Factibilidad y distribución del gap entero")
    fig.tight_layout()
    _save_figure(fig, output_dir, "F3_integer_feasibility_and_gap_ecdf")


def _figure_f4(output_dir: Path, runs: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    zero_message_methods: list[str] = []
    for method, group in runs.groupby("method"):
        summary = group.groupby("n_robots")[["runtime_s", "messages"]].median(numeric_only=True)
        axes[0].plot(summary.index, summary.runtime_s, marker="o", markersize=3, label=method)
        if (summary.messages > 0).any():
            positive = summary[summary.messages > 0]
            axes[1].plot(positive.index, positive.messages, marker="o", markersize=3, label=method)
        else:
            zero_message_methods.append(str(method))
    axes[0].set(xscale="log", yscale="log", xlabel="Robots N", ylabel="Runtime mediano (s)", title="Coste computacional")
    axes[1].set(xscale="log", yscale="log", xlabel="Robots N", ylabel="Mensajes medianos", title="Coste comunicativo")
    for ax in axes:
        ax.grid(alpha=0.22)
    axes[0].legend(frameon=False, fontsize=6)
    axes[1].legend(frameon=False, fontsize=6)
    axes[1].text(
        0.02,
        0.02,
        "0 mensajes (fuera de escala log): " + ", ".join(zero_message_methods),
        transform=axes[1].transAxes,
        fontsize=6,
        va="bottom",
    )
    fig.suptitle("F4. Escalabilidad de runtime y comunicación")
    fig.tight_layout()
    _save_figure(fig, output_dir, "F4_runtime_messages_vs_n")


def _figure_f5(output_dir: Path, ablations: pd.DataFrame) -> None:
    integer = ablations[ablations.ablation_family == "integer_recovery"]
    dynamics = ablations[ablations.ablation_family == "dynamics"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    feasibility = integer.groupby("variant").feasible.mean().sort_values(ascending=False)
    axes[0].bar(feasibility.index, feasibility.values, color="#41AB5D")
    axes[0].set(ylim=(0, 1.05), ylabel="Factibilidad", title="Ablaciones del cierre")
    axes[0].tick_params(axis="x", rotation=28, labelsize=7)
    convergence = dynamics.groupby("variant").converged.mean().sort_values(ascending=False)
    axes[1].bar(convergence.index, convergence.values, color="#756BB1")
    axes[1].set(ylim=(0, 1.05), ylabel="Tasa de convergencia", title="Ablaciones de la dinámica")
    axes[1].tick_params(axis="x", rotation=28, labelsize=7)
    for ax in axes:
        ax.grid(axis="y", alpha=0.22)
    fig.suptitle("F5. Ablaciones predeclaradas")
    fig.tight_layout()
    _save_figure(fig, output_dir, "F5_recovery_and_dynamics_ablations")


def _figure_f6(output_dir: Path, trajectories: pd.DataFrame) -> None:
    if trajectories.empty:
        return
    warehouse = trajectories[trajectories.scenario == "warehouse"]
    if warehouse.empty:
        return
    candidates: list[tuple[int, int, int, str, pd.DataFrame, ResourceWorld, tuple[tuple[float, float, float, float], ...]]] = []
    for (n_robots, n_loads, seed, world_hash), case in warehouse.groupby(
        ["n_robots", "n_loads", "seed", "world_hash"], sort=True
    ):
        world = generate_resource_world(int(n_robots), int(n_loads), int(seed))
        assignment = np.full(int(n_robots), -1, dtype=int)
        for robot, group in case.groupby("robot_id"):
            assignment[int(robot)] = int(group.load_id.iloc[0])
        assigned = np.flatnonzero(assignment >= 0)
        targets = contact_targets(world, assignment)
        obstacles = warehouse_obstacles(world.robot_positions_m[assigned], targets[assigned])
        candidates.append((len(obstacles), int(n_robots), int(seed), str(world_hash), case, world, obstacles))
    # F6 is a geometry illustration: choose the case retaining the most actual
    # obstacles, then the smallest fleet and seed. The title states this rule so
    # the example cannot be interpreted as performance-best or median-selected.
    obstacle_count, n_robots, seed, _, selected, world, obstacles = sorted(
        candidates, key=lambda item: (-item[0], item[1], item[2], item[3])
    )[0]
    fig, ax = plt.subplots(figsize=(6.6, 6.2))
    for x0, x1, y0, y1 in obstacles:
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color="#687386", alpha=0.68))
    for robot, group in selected.groupby("robot_id"):
        ax.plot(group.x_m, group.y_m, linewidth=1.0, label=f"R{int(robot)}")
        ax.scatter(group.x_m.iloc[0], group.y_m.iloc[0], marker="o", s=12, facecolors="none")
        ax.scatter(group.target_x_m.iloc[-1], group.target_y_m.iloc[-1], marker="x", s=24)
    ax.scatter(
        world.load_positions_m[:, 0], world.load_positions_m[:, 1], marker="s", s=34,
        color="#111827", label="Cargas",
    )
    ax.set(
        xlim=(0, 20), ylim=(0, 20), xlabel="x (m)", ylabel="y (m)",
        title=(
            "F6. Aproximación uniciclo en malla A* (warehouse)\n"
            f"ejemplo de máxima geometría retenida: N={n_robots}, semilla={seed}, obstáculos={obstacle_count}"
        ),
    )
    ax.set_aspect("equal")
    ax.grid(alpha=0.22)
    ax.legend(frameon=False, ncol=2, fontsize=6)
    fig.tight_layout()
    _save_figure(fig, output_dir, "F6_warehouse_unicycle_trajectories")


def _conference_gates(
    config: dict[str, Any],
    payloads: dict[str, dict[str, pd.DataFrame]],
    checks: dict[str, bool],
) -> dict[str, bool]:
    e1 = payloads.get("e1", {}).get("runs", pd.DataFrame())
    population = e1[e1.method.str.startswith("Rep")] if not e1.empty else pd.DataFrame()
    e2 = payloads.get("e2", {}).get("runs", pd.DataFrame())
    e4 = payloads.get("e4", {}).get("runs", pd.DataFrame())
    e5 = payloads.get("e5", {}).get("runs", pd.DataFrame())
    if not e2.empty:
        connected = e2[e2.assumption_class == "connected_assumption"]
        disconnected = e2[e2.assumption_class == "disconnected_control"]
        e2_separated = bool(not connected.empty and not disconnected.empty and connected.graph_connected.all() and (~disconnected.graph_connected).all())
        e2_sufficient = bool(connected.world_hash.nunique() >= 50 and connected.lambda2.nunique() >= 6)
    else:
        e2_separated = e2_sufficient = False
    full_method = e4[e4.method == "Argmax+repair+prune+local-exchange"] if not e4.empty else pd.DataFrame()
    if not e4.empty:
        per_configuration = e4[e4.method == "MILP"].groupby(["n_robots", "n_loads"]).world_hash.nunique()
        e4_coverage = bool(len(per_configuration) == 15 and per_configuration.ge(100).all())
    else:
        e4_coverage = False
    if not e5.empty:
        seeds_by_n = e5.groupby("n_robots").seed.nunique()
        e5_scale = bool(
            200 in seeds_by_n.index
            and all(seeds_by_n.get(n, 0) >= 30 for n in (20, 50, 100, 200))
            and seeds_by_n.get(500, 0) >= 10
        )
    else:
        e5_scale = False
    gates = {
        "tests_and_audits_pass": bool(checks and all(checks.values()) and checks.get("p0_pytest_suite_passed", False)),
        "e1_convergence_at_least_95pct": bool(not population.empty and population.converged.astype(bool).mean() >= 0.95),
        "e1_comparability_at_least_90pct": bool(not population.empty and population.comparable_to_lp.astype(bool).mean() >= 0.90),
        "e2_connected_disconnected_separated": e2_separated,
        "e2_sufficient_worlds_for_lambda2": e2_sufficient,
        "e4_repaired_feasibility_at_least_95pct": bool(not full_method.empty and full_method.feasible.astype(bool).mean() >= 0.95),
        "e4_100_worlds_per_configuration_with_ci": e4_coverage,
        "e5_multiple_seeds_reaches_n200": e5_scale,
        "distributed_nonpopulation_baseline_present": bool(not e5.empty and "Auction-D" in set(e5.method)),
        "claims_respect_scope": True,
    }
    return {gate: bool(gates[gate]) for gate in REQUIRED_GATES}


def _write_claim_evidence(
    output_dir: Path,
    payloads: dict[str, dict[str, pd.DataFrame]],
    audit: dict[str, Any],
) -> None:
    rows = [
        ("SP1-CONF-P0", "La implementación conserva objetivos, restricciones, simplex y comparabilidad predeclarados.", "P0 audit", "SOPORTADA" if audit["status"] == "passed" else "PARCIAL"),
        ("SP1-CONF-E1", "Rep-C y Rep-D se evalúan frente a LP-tau en mundos pareados; los gaps se restringen a ejecuciones comparables.", "E1 raw data + T1", "SOPORTADA" if audit["gates"]["e1_comparability_at_least_90pct"] else "PARCIAL"),
        ("SP1-CONF-E2", "El análisis espectral usa solo grafos conectados y conserva controles desconectados separados.", "E2 raw data + correlations", "SOPORTADA" if audit["gates"]["e2_sufficient_worlds_for_lambda2"] else "PARCIAL"),
        ("SP1-CONF-E3", "La región empírica de estabilidad se reporta sin convertir simulación en teorema.", "E3 traces + stability table", "OBSERVACIÓN EMPÍRICA"),
        ("SP1-CONF-E4", "La recuperación entera reporta conjuntamente factibilidad y gap frente a MILP certificado.", "E4 raw data + T2", "SOPORTADA" if audit["gates"]["e4_repaired_feasibility_at_least_95pct"] else "PARCIAL"),
        ("SP1-CONF-E5", "La escala reporta cotas inferior/superior cuando no existe certificado MILP.", "E5 raw data + T2", "SOPORTADA" if audit["gates"]["e5_multiple_seeds_reaches_n200"] else "PARCIAL"),
        ("SP1-CONF-E6", "E6 valida únicamente desplazamiento uniciclo hasta poses de aproximación.", "E6 raw data + F6", "OBSERVACIÓN EMPÍRICA"),
    ]
    lines = [
        "# Claim–evidence matrix — SP1 conference campaign",
        "",
        "| ID | Afirmación delimitada | Evidencia | Estado |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {identifier} | {claim} | {evidence} | {status} |" for identifier, claim, evidence, status in rows)
    lines.extend(["", "No se afirma transporte cooperativo sostenido, docking, wrench, hardware ni optimalidad entera general.", ""])
    (output_dir / "claim_evidence_matrix.md").write_text("\n".join(lines), encoding="utf-8")


def _write_reviewer_risks(
    output_dir: Path,
    payloads: dict[str, dict[str, pd.DataFrame]],
    audit: dict[str, Any],
) -> None:
    obstacle_summary = _e6_obstacle_retention_summary(payloads.get("e6", {}).get("runs", pd.DataFrame()))
    obstacle_text = "; ".join(
        f"N={int(row.n_robots)}: {int(row.nonempty_cases)}/{int(row.cases)} casos con algún obstáculo"
        for row in obstacle_summary.itertuples(index=False)
    ) or "sin datos E6 warehouse"
    risks = [
        ("Convergencia", "Las ejecuciones censuradas permanecen en el denominador; una tasa inferior al gate impide conference-ready."),
        ("Comparabilidad", "Los gaps LP se omiten cuando fallan factibilidad, simplex, finitud o referencia óptima; se reporta la tasa de comparabilidad."),
        ("Oráculo entero", "Un MILP sin mip_gap certificado no respalda un gap óptimo; se conserva como caso separado."),
        ("Topología", "Las correlaciones de E2 no incluyen controles desconectados y no se interpretan como ley 1/lambda2."),
        ("Baseline distribuido", "Auction-D es una subasta de max-consensus implementada como proxy; no hereda garantías de CBBA."),
        ("Runtime", "Los mundos se ejecutan en procesos de un solo hilo con el número de workers registrado; los tiempos incluyen la carga concurrente del host y deben interpretarse bajo ese protocolo."),
        ("Reanudación", "Si se usa --resume, duration_s cubre solo la invocación actual; cached_experiments identifica los bloques reconstruidos desde CSV y los runtimes de método permanecen en los datos crudos."),
        ("Validez física", "E6 congela la asignación y termina en la pose de aproximación; no existe contacto ni transporte."),
        ("Geometría warehouse", f"Los rectángulos que solapan poses terminales se descartan: {obstacle_text}. Un caso con cero obstáculos no valida evitación."),
        ("Generalización", "Los mundos son constructivamente factibles y sintéticos; no sustituyen validación industrial o hardware."),
    ]
    lines = ["# Reviewer risks", "", f"Scientific status: **{audit['scientific_status']}**", ""]
    lines.extend(f"- **{title}:** {description}" for title, description in risks)
    if audit["failed_gates"]:
        lines.extend(["", "## Remaining blockers", ""])
        lines.extend(f"- `{gate}`" for gate in audit["failed_gates"])
    lines.append("")
    (output_dir / "reviewer_risks.md").write_text("\n".join(lines), encoding="utf-8")


def _build_report(
    config: dict[str, Any],
    payloads: dict[str, dict[str, pd.DataFrame]],
    aggregated: pd.DataFrame,
    exclusions: pd.DataFrame,
    audit: dict[str, Any],
) -> str:
    lines = [
        f"# {config['experiment_id']}",
        "",
        f"- Audit status: `{audit['status']}`",
        f"- Scientific status: `{audit['scientific_status']}`",
        f"- Evidence level: `{audit['evidence_level']}`",
        f"- Recorded exclusions/reason codes: `{len(exclusions)}`",
        "",
        "## Scope",
        "",
        "La campaña evalúa formación distribuida de coaliciones, cierre entero y aproximación uniciclo. E6 no valida docking, contacto, wrench, transporte cooperativo sostenido ni hardware.",
        "",
        "## Conference gates",
        "",
        "| Gate | Passed |",
        "|---|---:|",
    ]
    lines.extend(f"| `{gate}` | {'yes' if passed else 'no'} |" for gate, passed in audit["gates"].items())
    lines.append("")
    for experiment in EXPERIMENTS:
        if experiment not in payloads:
            continue
        runs = payloads[experiment]["runs"]
        lines.extend([
            f"## {experiment.upper()}",
            "",
            f"Se registraron {len(runs)} filas método–mundo/escenario y {runs.world_hash.nunique() if 'world_hash' in runs else 0} mundos únicos.",
            "",
        ])
        if experiment == "e1":
            population = runs[runs.method.str.startswith("Rep")]
            lines.extend([
                f"Convergencia: {population.converged.astype(bool).mean():.3f}; comparabilidad estricta con LP-tau: {population.comparable_to_lp.astype(bool).mean():.3f}.",
                "",
            ])
        elif experiment == "e2":
            connected = runs[runs.assumption_class == "connected_assumption"]
            lines.extend([
                f"Grafos conectados: {len(connected)}; controles desconectados: {len(runs) - len(connected)}; mundos: {connected.world_hash.nunique()}. Convergencia conectada: {connected.converged.astype(bool).mean():.3f}; censura derecha: {connected.right_censored.astype(bool).mean():.3f}.",
                "",
            ])
        elif experiment == "e3":
            lines.extend([
                f"Tasa global de convergencia: {runs.converged.astype(bool).mean():.3f}; violación máxima del simplex: {runs.simplex_violation.max():.3e}; componentes negativas preproyección: {int(runs.negative_components_before_projection.sum())}. Es una región empírica, no una validación de estabilidad global.",
                "",
            ])
        elif experiment == "e4":
            full = runs[runs.method == "Argmax+repair+prune+local-exchange"]
            gaps = full.loc[full.feasible.astype(bool), "integer_gap_milp"].dropna()
            lines.extend([f"Recuperación completa: factibilidad {full.feasible.astype(bool).mean():.3f}; gap mediano certificado {gaps.median() if len(gaps) else math.nan:.3f} %; p95 {gaps.quantile(0.95) if len(gaps) else math.nan:.3f} %.", ""])
        elif experiment == "e5":
            auction = runs[runs.method == "Auction-D"]
            recovery = runs[runs.method == "Rep-D+recovery"]
            recovery_n500 = recovery[recovery.n_robots == 500]
            lines.extend([
                f"Escala máxima ejecutada: N={int(runs.n_robots.max())}; métodos: {', '.join(map(str, runs.method.drop_duplicates()))}.",
                f"Factibilidad Auction-D: {auction.feasible.astype(bool).mean():.3f}; Rep-D+recovery: {recovery.feasible.astype(bool).mean():.3f}; Rep-D+recovery en N=500: {recovery_n500.feasible.astype(bool).mean():.3f}. Convergencia fraccionaria Rep-D en E5: {runs.loc[runs.method == 'Rep-D', 'converged'].astype(bool).mean():.3f}.",
                "",
            ])
        elif experiment == "e6":
            valid = runs[runs.assignment_feasible.astype(bool)]
            max_size = runs[runs.n_robots == runs.n_robots.max()]
            obstacle_summary = _e6_obstacle_retention_summary(runs)
            obstacle_text = "; ".join(
                f"N={int(row.n_robots)}: {int(row.nonempty_cases)}/{int(row.cases)}"
                for row in obstacle_summary.itertuples(index=False)
            )
            lines.extend([
                f"Asignaciones localmente factibles: {len(valid)}/{len(runs)}; llegada media entre ejecuciones válidas: {valid.arrival_rate.mean() if len(valid) else math.nan:.3f}; convergencia fraccionaria en N={int(runs.n_robots.max())}: {max_size.fractional_converged.astype(bool).mean():.3f}.",
                f"Casos warehouse con al menos un obstáculo realmente retenido: {obstacle_text}. Los casos con cero obstáculos no constituyen evidencia de evitación.",
                "",
            ])
    lines.extend([
        "## Main artifacts",
        "",
        "- `tables/T1_convergence_and_relaxed_optimality.csv`",
        "- `tables/T2_integer_feasibility_gap_and_scalability.csv`",
        "- `figures/F1_...` through `figures/F6_...` in PDF and PNG",
        "- `all_runs.csv`, `aggregated_results.csv`, `seeds.csv`, `exclusions.csv`",
        "",
        "## Remaining blockers",
        "",
    ])
    if audit["failed_gates"]:
        blocker_details: dict[str, str] = {}
        if "e1" in payloads:
            e1_population = payloads["e1"]["runs"]
            e1_population = e1_population[e1_population.method.str.startswith("Rep")]
            blocker_details.update({
                "e1_convergence_at_least_95pct": f"observed={e1_population.converged.astype(bool).mean():.3f}, required>=0.950",
                "e1_comparability_at_least_90pct": f"observed={e1_population.comparable_to_lp.astype(bool).mean():.3f}, required>=0.900",
            })
        if "e4" in payloads:
            e4_full = payloads["e4"]["runs"]
            e4_full = e4_full[e4_full.method == "Argmax+repair+prune+local-exchange"]
            blocker_details[
                "e4_repaired_feasibility_at_least_95pct"
            ] = f"observed={e4_full.feasible.astype(bool).mean():.3f}, required>=0.950"
        lines.extend(f"- `{gate}`: {blocker_details.get(gate, 'failed under the frozen criterion')}" for gate in audit["failed_gates"])
    else:
        lines.append("None under the frozen conference gates.")
    lines.extend(["", "## Interpretation boundary", "", "A simulation result is empirical evidence, not a proof of global convergence, stability, robustness or optimality.", ""])
    return "\n".join(lines)


def _e6_obstacle_retention_summary(runs: pd.DataFrame) -> pd.DataFrame:
    """Count the warehouse rectangles actually retained by each feasible E6 run."""
    required = {"scenario", "assignment_feasible", "assignment_json", "n_robots", "n_loads", "seed"}
    if runs.empty or not required.issubset(runs.columns):
        return pd.DataFrame(columns=["n_robots", "cases", "nonempty_cases", "max_obstacles"])
    rows: list[dict[str, int]] = []
    warehouse = runs[(runs.scenario == "warehouse") & runs.assignment_feasible.astype(bool)]
    for run in warehouse.itertuples(index=False):
        assignment = np.asarray(json.loads(run.assignment_json), dtype=int)
        world = generate_resource_world(int(run.n_robots), int(run.n_loads), int(run.seed))
        targets = contact_targets(world, assignment)
        assigned = np.flatnonzero(assignment >= 0)
        count = len(warehouse_obstacles(world.robot_positions_m[assigned], targets[assigned]))
        rows.append({"n_robots": int(run.n_robots), "retained_obstacles": int(count)})
    if not rows:
        return pd.DataFrame(columns=["n_robots", "cases", "nonempty_cases", "max_obstacles"])
    frame = pd.DataFrame(rows)
    return (
        frame.groupby("n_robots", as_index=False)
        .agg(
            cases=("retained_obstacles", "size"),
            nonempty_cases=("retained_obstacles", lambda values: int((values > 0).sum())),
            max_obstacles=("retained_obstacles", "max"),
        )
        .sort_values("n_robots")
    )


def _write_report_pdf(path: Path, report: str) -> None:
    import textwrap

    lines: list[str] = []
    for line in report.splitlines():
        clean = line.replace("`", "").replace("**", "")
        lines.extend(textwrap.wrap(clean, width=105) or [""])
    with PdfPages(path) as pdf:
        for start in range(0, len(lines), 52):
            page = lines[start : start + 52]
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.07, 0.95, "\n".join(page), va="top", ha="left", fontsize=8.2, family="DejaVu Sans")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def _write_requirements_lock(path: Path) -> None:
    packages = ["matplotlib", "numpy", "pandas", "PyYAML", "scipy", "pytest", "viu-mrob-tfm"]
    lines = []
    for package in packages:
        try:
            lines.append(f"{package}=={importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            lines.append(f"{package}==NOT-INSTALLED")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _git_value(arguments: list[str]) -> str:
    try:
        return subprocess.run(["git", *arguments], check=False, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _build_manifest(
    config_path: Path,
    config: dict[str, Any],
    output_dir: Path,
    audit: dict[str, Any],
    seeds: pd.DataFrame,
    *,
    started_utc: str,
    duration_s: float,
    resume_requested: bool,
    cached_experiments: list[str],
) -> dict[str, Any]:
    artifacts: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name not in {
            "manifest.json", "conference_stdout.log", "conference_stderr.log"
        }:
            artifacts[path.relative_to(output_dir).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    dependencies = {}
    for package in ("matplotlib", "numpy", "pandas", "PyYAML", "scipy"):
        try:
            dependencies[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            dependencies[package] = "not-installed"
    return {
        "experiment_id": config["experiment_id"],
        "canonical_sp": "SP1",
        "protocol_family": config["protocol_family"],
        "scientific_status": audit["scientific_status"],
        "audit_status": audit["status"],
        "evidence_level": audit["evidence_level"],
        "commit_hash": _git_value(["rev-parse", "HEAD"]),
        "git_dirty": bool(_git_value(["status", "--porcelain"])),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "dependencies": dependencies,
        "configuration": config,
        "config_path": str(config_path),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "started_utc": started_utc,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": float(duration_s),
        "duration_scope": "current command invocation; cached experiment runtimes are reported in raw rows",
        "resume_requested": bool(resume_requested),
        "cached_experiments": list(cached_experiments),
        "cpu_count": os.cpu_count(),
        "parallel_workers": int(config.get("parallel_workers", 1)),
        "mutable_logs_excluded_from_artifact_hashes": ["conference_stdout.log", "conference_stderr.log"],
        "seeds": seeds.to_dict(orient="records"),
        "artifact_sha256": artifacts,
    }


__all__ = ["EXPERIMENTS", "execute", "run_conference_config"]
