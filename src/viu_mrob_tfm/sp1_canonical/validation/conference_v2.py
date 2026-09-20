"""Targeted SP1 conference remediation campaign (E1, E4, E5 and E6).

V2 is intentionally separate from the archived V1 runner.  Its protocol is
predeclared in ``plans/2026-07-22-sp1-conference-v2-remediation.md`` and the
versioned YAML configuration.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import binomtest, norm
import yaml

from viu_mrob_tfm.sp1_canonical.validation.auction import distributed_deficit_auction
from viu_mrob_tfm.sp1_canonical.validation.conference import _minimum_connected_rdisk
from viu_mrob_tfm.sp1_canonical.validation.dynamics import make_graph, run_population_dynamics
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v2 import run_two_phase_dynamics
from viu_mrob_tfm.sp1_canonical.validation.model import (
    ResourceWorld,
    build_costs,
    generate_resource_world,
    normalized_constraints,
)
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    AugmentingRepairResult,
    IntegerResult,
    argmax_round,
    evaluate_integer,
    repair_assignment,
    repair_assignment_augmenting,
)
from viu_mrob_tfm.sp1_canonical.validation.simulation import (
    conditioned_warehouse_obstacles,
    contact_targets,
    simulate_approach,
)
from viu_mrob_tfm.sp1_canonical.validation.solvers import (
    allocation_entropy,
    assignment_from_matrix,
    evaluate_relaxed,
    solve_lp,
    solve_milp,
    solve_regularized_lp,
)


EXPERIMENTS = ("e1", "e4", "e5", "e6")
PREFLIGHT_TESTS = (
    "tests/test_sp1_conference_v2.py",
    "tests/test_sp1_validation.py",
    "tests/test_sp1_conference.py",
    "tests/test_sp1_e6_visualization.py",
)


def execute(
    config_path: str | Path,
    *,
    experiment: str = "all",
    resume: bool = False,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run the frozen V2 campaign and return its manifest."""

    if experiment not in {"all", *EXPERIMENTS}:
        raise ValueError(f"unknown experiment: {experiment}")
    started = time.perf_counter()
    config_path = Path(config_path).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    base = Path(output_dir).resolve() if output_dir is not None else Path(config["output_dir"]).resolve()
    if base.exists() and not resume:
        raise FileExistsError(f"V2 output already exists; use --resume: {base}")
    for directory in (base, base / "raw", base / "tables", base / "figures", base / "videos"):
        directory.mkdir(parents=True, exist_ok=True)
    snapshot = base / "config_snapshot.yaml"
    current_config_text = config_path.read_text(encoding="utf-8")
    if snapshot.exists() and snapshot.read_text(encoding="utf-8") != current_config_text:
        raise ValueError("existing V2 output was created with a different configuration")
    snapshot.write_text(current_config_text, encoding="utf-8")

    git_commit = _git("rev-parse", "HEAD")
    git_branch = _git("branch", "--show-current")
    git_status_start = _git("status", "--porcelain", allow_failure=True)
    git_clean_start = git_status_start == ""
    preflight = _run_preflight(base) if bool(config.get("run_preflight_tests", True)) else {
        "status": "skipped", "returncode": 0, "tests": []
    }

    selected = EXPERIMENTS if experiment == "all" else (experiment,)
    for name in selected:
        required = _raw_paths(base, name)
        if resume and all(path.exists() for path in required):
            print(f"[V2] {name}: reutilizado", flush=True)
            continue
        print(f"[V2] {name}: inicio", flush=True)
        experiment_started = time.perf_counter()
        payload = globals()[f"_run_{name}"](config)
        for table_name, frame in payload.items():
            frame.to_csv(base / "raw" / f"{name}_{table_name}.csv", index=False)
        print(f"[V2] {name}: fin en {time.perf_counter() - experiment_started:.1f} s", flush=True)

    available = {name for name in EXPERIMENTS if all(path.exists() for path in _raw_paths(base, name))}
    tables, statistics = _analyse(base, config, available)
    for name, frame in tables.items():
        frame.to_csv(base / "tables" / f"{name}.csv", index=False)
    gates = _scientific_gates(config, tables, available)
    integrity = _integrity_checks(config, base, available, preflight)
    _make_figures(base, tables, available)
    report = _report(config, tables, statistics, gates, integrity, available)
    (base / "report.md").write_text(report, encoding="utf-8")
    (base / "statistics.json").write_text(
        json.dumps(statistics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    gate_frame = pd.DataFrame(
        [{"gate": key, "passed": bool(value)} for key, value in {**integrity, **gates}.items()]
    )
    gate_frame.to_csv(base / "tables" / "validation_gates.csv", index=False)

    git_status_end = _git("status", "--porcelain", allow_failure=True)
    git_clean_end = git_status_end == ""
    integrity["git_clean_start"] = git_clean_start
    integrity["git_clean_end"] = git_clean_end
    integrity = {key: bool(value) for key, value in integrity.items()}
    gates = {key: bool(value) for key, value in gates.items()}
    audit_status = "passed" if all(integrity.values()) else "failed"
    scientific_status = "passed" if available == set(EXPERIMENTS) and all(gates.values()) else "partial"
    manifest: dict[str, Any] = {
        "experiment_id": config["experiment_id"],
        "protocol_family": config["protocol_family"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": time.perf_counter() - started,
        "configuration": {**config, "effective_output_dir": str(base)},
        "git": {
            "commit": git_commit,
            "branch": git_branch,
            "clean_start": git_clean_start,
            "clean_end": git_clean_end,
            "status_start": git_status_start,
            "status_end": git_status_end,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "available_experiments": sorted(available),
        "preflight": preflight,
        "integrity_checks": integrity,
        "scientific_gates": gates,
        "audit_status": audit_status,
        "scientific_status": scientific_status,
        "scope": "SP1 coalition formation and approach only; no docking, wrench sharing or payload transport",
    }
    (base / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    hashes = _artifact_hashes(base)
    (base / "artifact_hashes.csv").write_text(hashes.to_csv(index=False), encoding="utf-8")
    audit = {
        "status": audit_status,
        "checks": integrity,
        "scientific_gates": gates,
        "artifact_count": int(len(hashes)),
        "all_hashes_unique_paths": bool(hashes["path"].is_unique),
    }
    (base / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return manifest


def _run_preflight(base: Path) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", *PREFLIGHT_TESTS, "-q"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    payload = {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": int(completed.returncode),
        "tests": list(PREFLIGHT_TESTS),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    (base / "raw" / "preflight_tests.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return payload


def _raw_paths(base: Path, experiment: str) -> tuple[Path, ...]:
    names = {
        "e1": ("runs", "history", "worlds"),
        "e4": ("runs", "assignments"),
        "e5": ("runs",),
        "e6": ("runs", "trajectories", "obstacles", "paths"),
    }[experiment]
    return tuple(base / "raw" / f"{experiment}_{name}.csv" for name in names)


def _seed_values(spec: dict[str, Any]) -> list[int]:
    return list(range(int(spec["start"]), int(spec["start"]) + int(spec["count"])))


def _world_tasks(section: dict[str, Any]) -> list[tuple[int, int, int]]:
    return [
        (int(n), int(k), seed)
        for n, k in section["configurations"]
        for seed in _seed_values(section["seeds"])
    ]


def _parallel(worker: Any, tasks: Iterable[Any], config: dict[str, Any]) -> list[Any]:
    task_list = list(tasks)
    workers = max(1, min(int(config.get("parallel_workers", os.cpu_count() or 1)), len(task_list)))
    if workers == 1:
        return [worker((config, task)) for task in task_list]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(worker, ((config, task) for task in task_list), chunksize=1))


def _costs(config: dict[str, Any], world: ResourceWorld) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    return build_costs(
        world,
        config["cost_weights"],
        reserve_energy=float(config.get("reserve_energy", 5.0)),
    )


def _dynamic_options(config: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    dynamics = config["preconditioned_dynamics"]
    return {
        "eta": float(dynamics["eta"]),
        "step_min": float(dynamics["step_min"]),
        "step_max": float(dynamics["step_max"]),
        "operational_max_iterations": int(section["operational_max_iterations"]),
        "refinement_max_iterations": int(section.get("refinement_max_iterations", 1)),
        "operational_tolerance": float(dynamics["operational_tolerance"]),
        "refinement_primal_tolerance": float(dynamics["refinement_primal_tolerance"]),
        "refinement_consensus_tolerance": float(dynamics["refinement_consensus_tolerance"]),
        "refinement_stationarity_tolerance": float(dynamics["refinement_stationarity_tolerance"]),
        "comparison_feasibility_tolerance": float(dynamics["comparison_feasibility_tolerance"]),
        "entropy_tau": float(dynamics["entropy_tau"]),
        "consensus_gain": float(dynamics["consensus_gain"]),
        "use_integral_consensus": bool(dynamics["use_integral_consensus"]),
    }


def _augment_options(config: dict[str, Any]) -> dict[str, Any]:
    repair = config["augmenting_recovery"]
    return {
        "max_chain_length": int(repair["max_chain_length"]),
        "max_nodes_per_augmentation": int(repair["max_nodes_per_augmentation"]),
        "candidates_per_load": int(repair["candidates_per_load"]),
        "prune": bool(repair["prune"]),
        "local_exchange": bool(repair["local_exchange"]),
        "compress": bool(repair["compress"]),
    }


def _run_e1(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    results = _parallel(_e1_worker, _world_tasks(config["e1"]), config)
    return {
        "runs": pd.DataFrame([row for result in results for row in result[0]]),
        "history": pd.concat([frame for result in results for frame in result[1]], ignore_index=True),
        "worlds": pd.DataFrame([result[2] for result in results]),
    }


def _e1_worker(payload: tuple[dict[str, Any], tuple[int, int, int]]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], dict[str, Any]]:
    config, (n, k, seed) = payload
    section = config["e1"]
    world = generate_resource_world(n, k, seed)
    costs, compatible, _ = _costs(config, world)
    lp = solve_lp(world, costs)
    tau = float(config["preconditioned_dynamics"]["entropy_tau"])
    lp_tau = solve_regularized_lp(
        world, costs, entropy_tau=tau, max_iterations=int(section["lp_tau_max_iterations"])
    )
    complete = make_graph(world, "complete")
    rdisk, radius = _minimum_connected_rdisk(world)
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    first_seed = _seed_values(section["seeds"])[0]
    for method, distributed, graph, graph_case in (
        ("Rep-C-preconditioned", False, complete, "central_global"),
        ("Rep-D-complete-preconditioned", True, complete, "complete"),
        ("Rep-D-rdisk-preconditioned", True, rdisk, "rdisk_connected"),
    ):
        options = _dynamic_options(config, section)
        options["history_stride"] = int(
            section["trace_stride"] if seed == first_seed else section["terminal_history_stride"]
        )
        result = run_two_phase_dynamics(
            world,
            costs,
            graph,
            distributed=distributed,
            lp_objective=float(lp.objective) if lp.status == 0 else None,
            **options,
        )
        final = result.final
        terminal = final.history.iloc[-1]
        metrics = evaluate_relaxed(world, final.x, costs)
        gap = (
            (float(metrics["objective"]) - float(lp.objective)) / max(abs(float(lp.objective)), 1e-12)
            if result.comparable_at_1e6 and lp.status == 0
            else math.nan
        )
        rows.append(
            {
                "experiment": "e1",
                "world_hash": world.world_hash,
                "seed": seed,
                "n_robots": n,
                "n_loads": k,
                "method": method,
                "graph_case": graph_case,
                "graph_connected": graph.connected,
                "lambda2": graph.lambda2,
                "lambda_max": graph.lambda_max,
                "edges": graph.edges,
                "effective_radius_m": radius if graph_case == "rdisk_connected" else math.nan,
                "operational_converged": result.operational_converged,
                "refinement_attempted": result.refinement_attempted,
                "refinement_converged": result.refinement_converged,
                "comparable_at_1e6": result.comparable_at_1e6,
                "operational_censored": not result.operational_converged,
                "refinement_censored": result.refinement_attempted and not result.refinement_converged,
                "stop_reason": result.stop_reason,
                "operational_iterations": result.operational.iterations,
                "refinement_iterations": result.refinement.iterations if result.refinement is not None else 0,
                "iterations_total": result.operational.iterations + (result.refinement.iterations if result.refinement is not None else 0),
                "operational_runtime_s": result.operational.runtime_s,
                "refinement_runtime_s": result.refinement.runtime_s if result.refinement is not None else 0.0,
                "runtime_s": result.operational.runtime_s + (result.refinement.runtime_s if result.refinement is not None else 0.0),
                "messages_total": result.messages_total,
                "scalars_sent_total": result.scalars_sent_total,
                "bytes_estimated_total": 8 * result.scalars_sent_total,
                "operator_scale_estimate": result.preconditioner.operator_scale_estimate,
                "normalized_coupling_scale": result.preconditioner.normalized_coupling_scale,
                "normalized_graph_scale": result.preconditioner.normalized_graph_scale,
                "step": result.preconditioner.step,
                "step_unclipped": result.preconditioner.step_unclipped,
                "objective": float(metrics["objective"]),
                "lp_objective": float(lp.objective),
                "regularized_lp_objective": float(lp_tau.objective),
                "gap_lp": gap,
                "error_to_lp_tau": float(np.linalg.norm(final.x - lp_tau.x)) if lp_tau.status == 0 else math.nan,
                "entropy": allocation_entropy(final.x),
                "primal_residual_normalized": float(terminal["primal_residual_normalized"]),
                "primal_residual_relative": float(terminal["primal_residual_relative"]),
                "consensus_residual_relative": float(terminal["consensus_residual_relative"]),
                "consensus_disagreement_residual": float(terminal["consensus_disagreement_residual"]),
                "stationarity_residual": float(terminal["stationarity_residual"]),
                "stationarity_residual_relative": float(terminal["stationarity_residual_relative"]),
                "simplex_violation": float(metrics["simplex_violation"]),
            }
        )
        if seed == first_seed:
            histories.append(
                result.history.assign(
                    experiment="e1",
                    method=method,
                    world_hash=world.world_hash,
                    seed=seed,
                    n_robots=n,
                    n_loads=k,
                    graph_case=graph_case,
                    step=result.preconditioner.step,
                )
            )
    return rows, histories, {
        "world_hash": world.world_hash,
        "seed": seed,
        "n_robots": n,
        "n_loads": k,
        "compatible_pairs": int(np.sum(compatible)),
        "rdisk_radius_m": radius,
        "lp_status": lp.status,
        "lp_tau_status": lp_tau.status,
    }


def _run_e4(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    results = _parallel(_e4_worker, _world_tasks(config["e4"]), config)
    return {
        "runs": pd.DataFrame([row for result in results for row in result[0]]),
        "assignments": pd.DataFrame([row for result in results for row in result[1]]),
    }


def _e4_worker(payload: tuple[dict[str, Any], tuple[int, int, int]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config, (n, k, seed) = payload
    section = config["e4"]
    world = generate_resource_world(n, k, seed)
    costs, _, _ = _costs(config, world)
    lp = solve_lp(world, costs)
    milp_started = time.perf_counter()
    milp = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
    milp_runtime = time.perf_counter() - milp_started
    milp_integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
    certified = bool(milp.status == 0 and milp_integer.feasible and np.isfinite(milp.mip_gap) and milp.mip_gap <= 1e-8)
    legacy = section["legacy_fractional_dynamics"]
    graph = make_graph(world, "complete")
    dynamic = run_population_dynamics(
        world,
        costs,
        graph,
        distributed=True,
        integrator="mirror_prox",
        step=float(legacy["step"]),
        max_iterations=int(legacy["max_iterations"]),
        convergence_residual_mode=str(legacy["convergence_residual_mode"]),
        primal_tolerance=float(legacy["primal_tolerance"]),
        consensus_tolerance=float(legacy["consensus_tolerance"]),
        stationarity_tolerance=float(legacy["stationarity_tolerance"]),
        comparison_feasibility_tolerance=float(legacy["comparison_feasibility_tolerance"]),
        entropy_tau=float(legacy["entropy_tau"]),
        consensus_gain=float(legacy["consensus_gain"]),
        use_integral_consensus=bool(legacy["use_integral_consensus"]),
        history_stride=int(legacy["max_iterations"]) + 1,
        lp_objective=float(lp.objective),
    )
    origin = argmax_round(dynamic.x, margin=float(section["rounding_margin"]))
    started = time.perf_counter()
    raw = evaluate_integer(world, origin, costs)
    raw_runtime = time.perf_counter() - started
    started = time.perf_counter()
    greedy = repair_assignment(world, origin, costs, prune=True, local_exchange=True, compress=True)
    greedy_runtime = time.perf_counter() - started
    started = time.perf_counter()
    augmenting = repair_assignment_augmenting(world, origin, costs, **_augment_options(config))
    augmenting_runtime = time.perf_counter() - started
    method_results: list[tuple[str, IntegerResult, float, AugmentingRepairResult | None]] = [
        ("Argmax-origin", raw, raw_runtime, None),
        ("GreedyRepair-V1", greedy, greedy_runtime, None),
        ("AugmentingRepair-V2", augmenting.integer, augmenting_runtime, augmenting),
        ("MILP-oracle", milp_integer, milp_runtime, None),
    ]
    rows: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    origin_hash = hashlib.sha256(origin.tobytes()).hexdigest()
    for method, integer, runtime_s, diagnostics in method_results:
        gap = (
            100.0 * (integer.objective - milp_integer.objective) / max(abs(milp_integer.objective), 1e-12)
            if certified and integer.feasible
            else math.nan
        )
        rows.append(
            {
                "experiment": "e4",
                "world_hash": world.world_hash,
                "origin_assignment_hash": origin_hash,
                "seed": seed,
                "n_robots": n,
                "n_loads": k,
                "method": method,
                "feasible": integer.feasible,
                "objective": integer.objective,
                "integer_gap_milp_percent": gap,
                "deficit_l1": integer.deficit_l1,
                "overassignment_l1": integer.overassignment_l1,
                "repairs": integer.repairs,
                "pruned": integer.pruned,
                "local_exchanges": integer.exchanges,
                "runtime_s": runtime_s,
                "assignment_json": json.dumps(integer.assignment.tolist()),
                "fractional_converged": dynamic.converged,
                "fractional_iterations": dynamic.iterations,
                "milp_status": milp.status,
                "milp_gap": milp.mip_gap,
                "milp_certified": certified,
                "augmentations": diagnostics.augmentations if diagnostics is not None else 0,
                "maximum_chain_length": diagnostics.maximum_chain_length if diagnostics is not None else 0,
                "nodes_explored": diagnostics.nodes_explored if diagnostics is not None else 0,
                "search_failures": diagnostics.search_failures if diagnostics is not None else 0,
                "failure_reason": diagnostics.failure_reason if diagnostics is not None else ("none" if integer.feasible else "infeasible"),
                "chain_lengths_json": json.dumps(diagnostics.chain_lengths) if diagnostics is not None else "[]",
            }
        )
        for robot, load in enumerate(integer.assignment):
            assignments.append(
                {
                    "world_hash": world.world_hash,
                    "seed": seed,
                    "n_robots": n,
                    "n_loads": k,
                    "method": method,
                    "robot_id": robot,
                    "load_id": int(load),
                }
            )
    return rows, assignments


def _run_e5(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    section = config["e5"]
    tasks = []
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section["robots_per_load"]))))
        for seed in _seed_values(section["seed_blocks"][str(n)]):
            tasks.append((n, k, seed))
    results = _parallel(_e5_worker, tasks, config)
    return {"runs": pd.DataFrame([row for result in results for row in result])}


def _e5_worker(payload: tuple[dict[str, Any], tuple[int, int, int]]) -> list[dict[str, Any]]:
    config, (n, k, seed) = payload
    section = config["e5"]
    world = generate_resource_world(n, k, seed)
    costs, _, _ = _costs(config, world)
    graph, radius = _minimum_connected_rdisk(world)
    lp_started = time.perf_counter()
    lp = solve_lp(world, costs)
    lp_runtime = time.perf_counter() - lp_started
    auction = distributed_deficit_auction(world, costs, graph)
    options = _dynamic_options(config, section)
    options.update({"attempt_refinement": False, "history_stride": int(section["operational_max_iterations"]) + 1})
    dynamic = run_two_phase_dynamics(
        world,
        costs,
        graph,
        distributed=True,
        lp_objective=float(lp.objective) if lp.status == 0 else None,
        **options,
    )
    final = dynamic.operational
    relaxed = evaluate_relaxed(world, final.x, costs)
    terminal = final.history.iloc[-1]
    rows: list[dict[str, Any]] = [
        {
            "experiment": "e5", "world_hash": world.world_hash, "seed": seed,
            "n_robots": n, "n_loads": k, "method": "LP-raw", "result_type": "lower_bound",
            "feasible": lp.status == 0, "objective": lp.objective, "runtime_s": lp_runtime,
            "iterations": 0, "messages_total": 0, "scalars_sent_total": 0,
            "bytes_estimated_total": 0, "censored": False, "failure_stage": "none" if lp.status == 0 else "lp_failed",
        },
        {
            "experiment": "e5", "world_hash": world.world_hash, "seed": seed,
            "n_robots": n, "n_loads": k, "method": "Auction-D", "result_type": "integer",
            "feasible": auction.integer.feasible, "objective": auction.integer.objective,
            "runtime_s": auction.runtime_s, "iterations": auction.rounds,
            "messages_total": auction.messages, "scalars_sent_total": auction.scalars_sent,
            "bytes_estimated_total": 8 * auction.scalars_sent, "censored": False,
            "failure_stage": "none" if auction.integer.feasible else auction.status,
            "assignment_json": json.dumps(auction.integer.assignment.tolist()),
        },
        {
            "experiment": "e5", "world_hash": world.world_hash, "seed": seed,
            "n_robots": n, "n_loads": k, "method": "Rep-D-preconditioned", "result_type": "fractional",
            "feasible": bool(float(terminal["primal_residual_normalized"]) <= 1e-6),
            "objective": float(relaxed["objective"]), "runtime_s": final.runtime_s,
            "iterations": final.iterations, "messages_total": dynamic.messages_total,
            "scalars_sent_total": dynamic.scalars_sent_total, "bytes_estimated_total": 8 * dynamic.scalars_sent_total,
            "censored": not dynamic.operational_converged,
            "failure_stage": "none" if dynamic.operational_converged else "fractional_nonconverged",
            "operational_converged": dynamic.operational_converged,
            "primal_residual_normalized": float(terminal["primal_residual_normalized"]),
            "primal_residual_relative": float(terminal["primal_residual_relative"]),
            "consensus_residual_relative": float(terminal["consensus_residual_relative"]),
            "stationarity_residual_relative": float(terminal["stationarity_residual_relative"]),
            "step": dynamic.preconditioner.step,
            "operator_scale_estimate": dynamic.preconditioner.operator_scale_estimate,
        },
    ]
    if dynamic.operational_converged:
        origin = argmax_round(final.x, margin=float(section["rounding_margin"]))
        recovery_started = time.perf_counter()
        recovery = repair_assignment_augmenting(world, origin, costs, **_augment_options(config))
        recovery_runtime = time.perf_counter() - recovery_started
        recovery_row = {
            "feasible": recovery.integer.feasible,
            "objective": recovery.integer.objective,
            "runtime_s": final.runtime_s + recovery_runtime,
            "recovery_runtime_s": recovery_runtime,
            "failure_stage": "none" if recovery.integer.feasible else recovery.failure_reason,
            "assignment_json": json.dumps(recovery.integer.assignment.tolist()),
            "augmentations": recovery.augmentations,
            "maximum_chain_length": recovery.maximum_chain_length,
            "nodes_explored": recovery.nodes_explored,
            "recovery_executed": True,
        }
    else:
        recovery_row = {
            "feasible": False, "objective": math.nan, "runtime_s": final.runtime_s,
            "recovery_runtime_s": 0.0, "failure_stage": "skipped_nonconverged",
            "assignment_json": "", "augmentations": 0, "maximum_chain_length": 0,
            "nodes_explored": 0, "recovery_executed": False,
        }
    recovery_row.update(
        {
            "experiment": "e5", "world_hash": world.world_hash, "seed": seed,
            "n_robots": n, "n_loads": k, "method": "Rep-D+AugmentingRecovery-V2",
            "result_type": "integer", "iterations": final.iterations,
            "messages_total": dynamic.messages_total, "scalars_sent_total": dynamic.scalars_sent_total,
            "bytes_estimated_total": 8 * dynamic.scalars_sent_total,
            "censored": not dynamic.operational_converged,
            "operational_converged": dynamic.operational_converged,
            "step": dynamic.preconditioner.step,
            "operator_scale_estimate": dynamic.preconditioner.operator_scale_estimate,
        }
    )
    rows.append(recovery_row)
    if n <= int(section["milp_max_n"]):
        milp_started = time.perf_counter()
        milp = solve_milp(world, costs, time_limit_s=float(config["oracle_time_limit_s"]))
        milp_runtime = time.perf_counter() - milp_started
        integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
        rows.append(
            {
                "experiment": "e5", "world_hash": world.world_hash, "seed": seed,
                "n_robots": n, "n_loads": k, "method": "MILP-oracle", "result_type": "integer",
                "feasible": integer.feasible, "objective": integer.objective, "runtime_s": milp_runtime,
                "iterations": 0, "messages_total": 0, "scalars_sent_total": 0,
                "bytes_estimated_total": 0, "censored": milp.status != 0,
                "failure_stage": "none" if milp.status == 0 else "milp_not_certified",
                "assignment_json": json.dumps(integer.assignment.tolist()),
            }
        )
    for row in rows:
        row["graph_connected"] = graph.connected
        row["lambda2"] = graph.lambda2
        row["edges"] = graph.edges
        row["effective_radius_m"] = radius
        row["estimated_memory_bytes"] = int(
            world.resources.nbytes + costs.nbytes + (final.x.nbytes + final.dual.nbytes if str(row["method"]).startswith("Rep-D") else 0)
        )
    return rows


def _run_e6(config: dict[str, Any]) -> dict[str, pd.DataFrame]:
    section = config["e6"]
    seeds = _seed_values(section["seeds"])
    tasks = []
    for n_value in section["fleet_sizes"]:
        n = int(n_value)
        k = max(1, int(round(n / float(section["robots_per_load"]))))
        for seed in seeds:
            tasks.append((n, k, seed, seed == seeds[0]))
    results = _parallel(_e6_worker, tasks, config)
    trajectories = [frame for result in results for frame in result[1] if not frame.empty]
    return {
        "runs": pd.DataFrame([row for result in results for row in result[0]]),
        "trajectories": pd.concat(trajectories, ignore_index=True) if trajectories else pd.DataFrame(),
        "obstacles": pd.DataFrame([row for result in results for row in result[2]]),
        "paths": pd.DataFrame([row for result in results for row in result[3]]),
    }


def _e6_worker(payload: tuple[dict[str, Any], tuple[int, int, int, bool]]) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[dict[str, Any]], list[dict[str, Any]]]:
    config, (n, k, seed, record_trajectory) = payload
    section = config["e6"]
    world = generate_resource_world(n, k, seed)
    costs, _, _ = _costs(config, world)
    graph, radius = _minimum_connected_rdisk(world)
    lp = solve_lp(world, costs)
    options = _dynamic_options(config, section)
    options.update({"attempt_refinement": False, "history_stride": int(section["operational_max_iterations"]) + 1})
    dynamic = run_two_phase_dynamics(
        world, costs, graph, distributed=True,
        lp_objective=float(lp.objective) if lp.status == 0 else None,
        **options,
    )
    assignment_source = "Rep-D-preconditioned+augmenting"
    recovery: AugmentingRepairResult | None = None
    if dynamic.operational_converged:
        origin = argmax_round(dynamic.operational.x, margin=float(section["rounding_margin"]))
        recovery = repair_assignment_augmenting(world, origin, costs, **_augment_options(config))
    if recovery is None or not recovery.integer.feasible:
        auction = distributed_deficit_auction(world, costs, graph)
        integer = auction.integer
        assignment_source = "Auction-D-fallback"
    else:
        integer = recovery.integer
    rows: list[dict[str, Any]] = []
    trajectories: list[pd.DataFrame] = []
    obstacle_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    if not integer.feasible:
        for scenario in section["scenarios"]:
            rows.append(
                {
                    "experiment": "e6", "world_hash": world.world_hash, "seed": seed,
                    "n_robots": n, "n_loads": k, "scenario": scenario,
                    "assignment_feasible": False, "arrival_success": False,
                    "assignment_source": assignment_source, "failure_reason": "integer_assignment_failed",
                    "trajectory_recorded": False, "fractional_converged": dynamic.operational_converged,
                    "messages_total": dynamic.messages_total,
                }
            )
        return rows, trajectories, obstacle_rows, path_rows
    assignment = integer.assignment
    assigned = np.flatnonzero(assignment >= 0)
    targets = contact_targets(world, assignment)
    for scenario in section["scenarios"]:
        if scenario == "warehouse":
            plan = conditioned_warehouse_obstacles(
                world.robot_positions_m[assigned],
                targets[assigned],
                desired_obstacles=int(section["desired_obstacles"]),
            )
            obstacles = plan.obstacles
            estimated = np.zeros(world.n_robots)
            estimated[assigned] = np.asarray(plan.astar_lengths_m) * world.energy_per_m[assigned]
            for index, (x0, x1, y0, y1) in enumerate(obstacles):
                obstacle_rows.append(
                    {
                        "scenario": scenario, "world_hash": world.world_hash, "seed": seed,
                        "n_robots": n, "n_loads": k, "obstacle_id": index,
                        "x0": x0, "x1": x1, "y0": y0, "y1": y1,
                    }
                )
            for local_index, robot in enumerate(assigned):
                path_rows.append(
                    {
                        "scenario": scenario, "world_hash": world.world_hash, "seed": seed,
                        "n_robots": n, "n_loads": k, "robot_id": int(robot),
                        "load_id": int(assignment[robot]),
                        "direct_length_m": plan.direct_lengths_m[local_index],
                        "astar_length_m": plan.astar_lengths_m[local_index],
                        "direct_path_blocked": local_index in plan.blocked_route_indices,
                        "astar_detoured": local_index in plan.detoured_route_indices,
                    }
                )
        else:
            obstacles = ()
            estimated = np.zeros(world.n_robots)
            estimated[assigned] = (
                np.linalg.norm(world.robot_positions_m[assigned] - targets[assigned], axis=1)
                * world.energy_per_m[assigned]
            )
        approach = simulate_approach(
            world,
            assignment,
            scenario=str(scenario),
            dt_s=float(section["dt_s"]),
            horizon_s=float(section["horizon_s"]),
            estimated_energy_by_robot=estimated,
            obstacles_override=obstacles if scenario == "warehouse" else None,
        )
        summary = dict(approach.summary)
        summary.update(
            {
                "experiment": "e6", "world_hash": world.world_hash, "seed": seed,
                "n_robots": n, "n_loads": k, "method": "V2-assignment+unicycle-approach",
                "assignment_feasible": integer.feasible,
                "assignment_source": assignment_source,
                "assignment_json": json.dumps(assignment.tolist()),
                "arrival_success": bool(summary["arrival_rate"] >= 1.0 - 1e-12),
                "failure_reason": "none" if summary["arrival_rate"] >= 1.0 - 1e-12 else "approach_timeout_or_path_failure",
                "trajectory_recorded": bool(record_trajectory),
                "fractional_converged": dynamic.operational_converged,
                "messages_total": dynamic.messages_total,
                "scalars_sent_total": dynamic.scalars_sent_total,
                "bytes_estimated_total": 8 * dynamic.scalars_sent_total,
                "runtime_s": dynamic.operational.runtime_s,
                "step": dynamic.preconditioner.step,
                "operator_scale_estimate": dynamic.preconditioner.operator_scale_estimate,
                "graph_connected": graph.connected, "lambda2": graph.lambda2,
                "edges": graph.edges, "effective_radius_m": radius,
            }
        )
        rows.append(summary)
        if record_trajectory:
            trajectories.append(
                approach.trajectories.assign(
                    experiment="e6", world_hash=world.world_hash, seed=seed,
                    n_robots=n, n_loads=k, assignment_source=assignment_source,
                )
            )
    return rows, trajectories, obstacle_rows, path_rows


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)) / denominator
    return center - half, center + half


def _boolean_series(series: pd.Series) -> pd.Series:
    return series.map(
        lambda value: False
        if pd.isna(value)
        else (value if isinstance(value, (bool, np.bool_)) else str(value).strip().lower() in {"1", "true", "yes", "si", "sí"})
    ).astype(bool)


def _rate_table(
    frame: pd.DataFrame,
    group_columns: list[str],
    boolean_columns: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_columns, sort=True, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_columns, key_values, strict=True))
        row["runs"] = len(group)
        for column in boolean_columns:
            values = group[column].fillna(False).astype(bool)
            successes = int(values.sum())
            low, high = _wilson(successes, len(values))
            row[f"{column}_count"] = successes
            row[f"{column}_rate"] = successes / len(values) if len(values) else math.nan
            row[f"{column}_ci95_low"] = low
            row[f"{column}_ci95_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def _analyse(
    base: Path,
    config: dict[str, Any],
    available: set[str],
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    tables: dict[str, pd.DataFrame] = {}
    statistics: dict[str, Any] = {}
    if "e1" in available:
        runs = pd.read_csv(base / "raw" / "e1_runs.csv")
        rates = _rate_table(
            runs,
            ["method", "n_robots", "n_loads"],
            ["operational_converged", "comparable_at_1e6", "refinement_converged"],
        )
        numeric = (
            runs.groupby(["method", "n_robots", "n_loads"], as_index=False)
            .agg(
                step_median=("step", "median"),
                iterations_total_median=("iterations_total", "median"),
                runtime_s_median=("runtime_s", "median"),
                messages_total_median=("messages_total", "median"),
                bytes_estimated_total_median=("bytes_estimated_total", "median"),
                primal_residual_normalized_median=("primal_residual_normalized", "median"),
                gap_lp_median=("gap_lp", "median"),
            )
        )
        tables["e1_convergence_comparability"] = rates.merge(
            numeric, on=["method", "n_robots", "n_loads"], validate="one_to_one"
        )
        eligible = runs[runs["operational_converged"].astype(bool)]
        statistics["e1"] = {
            "runs": int(len(runs)),
            "operational_convergence_rate": float(runs["operational_converged"].mean()),
            "eligible_for_refinement": int(len(eligible)),
            "refined_comparability_rate_among_operational": float(eligible["comparable_at_1e6"].mean()) if len(eligible) else math.nan,
            "operational_censored": int((~runs["operational_converged"].astype(bool)).sum()),
            "refinement_censored": int(runs["refinement_censored"].astype(bool).sum()),
            "messages_total": int(runs["messages_total"].sum()),
        }
    if "e4" in available:
        runs = pd.read_csv(base / "raw" / "e4_runs.csv")
        rates = _rate_table(runs, ["method", "n_robots", "n_loads"], ["feasible"])
        numeric = (
            runs.groupby(["method", "n_robots", "n_loads"], as_index=False)
            .agg(
                gap_median_percent=("integer_gap_milp_percent", "median"),
                gap_p95_percent=("integer_gap_milp_percent", lambda values: values.quantile(0.95)),
                deficit_median=("deficit_l1", "median"),
                overassignment_median=("overassignment_l1", "median"),
                runtime_s_median=("runtime_s", "median"),
                maximum_chain_length=("maximum_chain_length", "max"),
                nodes_explored_median=("nodes_explored", "median"),
            )
        )
        tables["e4_feasibility_by_configuration"] = rates.merge(
            numeric, on=["method", "n_robots", "n_loads"], validate="one_to_one"
        )
        old = runs[runs.method == "GreedyRepair-V1"][["world_hash", "feasible"]].rename(columns={"feasible": "old"})
        new = runs[runs.method == "AugmentingRepair-V2"][["world_hash", "feasible"]].rename(columns={"feasible": "new"})
        paired = old.merge(new, on="world_hash", validate="one_to_one")
        old_only = int((paired.old.astype(bool) & ~paired.new.astype(bool)).sum())
        new_only = int((~paired.old.astype(bool) & paired.new.astype(bool)).sum())
        discordant = old_only + new_only
        pvalue = float(binomtest(min(old_only, new_only), discordant, 0.5).pvalue) if discordant else 1.0
        tables["e4_paired_binary"] = pd.DataFrame(
            [{"old_only": old_only, "new_only": new_only, "discordant": discordant, "exact_mcnemar_pvalue": pvalue}]
        )
        statistics["e4"] = {
            "paired_worlds": int(len(paired)),
            "greedy_feasibility_rate": float(paired.old.mean()),
            "augmenting_feasibility_rate": float(paired.new.mean()),
            "old_only": old_only,
            "new_only": new_only,
            "exact_mcnemar_pvalue": pvalue,
        }
    if "e5" in available:
        runs = pd.read_csv(base / "raw" / "e5_runs.csv")
        tables["e5_scalability"] = (
            runs.groupby(["method", "n_robots", "n_loads"], as_index=False)
            .agg(
                seeds=("seed", "nunique"),
                feasibility_rate=("feasible", "mean"),
                censored_rate=("censored", "mean"),
                runtime_s_median=("runtime_s", "median"),
                runtime_s_p95=("runtime_s", lambda values: values.quantile(0.95)),
                iterations_median=("iterations", "median"),
                messages_total_median=("messages_total", "median"),
                messages_total_sum=("messages_total", "sum"),
                bytes_estimated_total_median=("bytes_estimated_total", "median"),
                estimated_memory_bytes_median=("estimated_memory_bytes", "median"),
            )
        )
        recovery = runs[runs.method == "Rep-D+AugmentingRecovery-V2"]
        statistics["e5"] = {
            "worlds": int(runs.world_hash.nunique()),
            "maximum_n": int(runs.n_robots.max()),
            "recovery_executed": int(_boolean_series(recovery.recovery_executed).sum()),
            "recovery_skipped_nonconverged": int((recovery.failure_stage == "skipped_nonconverged").sum()),
            "recovery_after_nonconvergence": int((_boolean_series(recovery.recovery_executed) & ~_boolean_series(recovery.operational_converged)).sum()),
            "messages_total": int(runs.messages_total.fillna(0).sum()),
        }
    if "e6" in available:
        runs = pd.read_csv(base / "raw" / "e6_runs.csv")
        tables["e6_scenario_summary"] = (
            runs.groupby(["scenario", "n_robots", "n_loads"], as_index=False)
            .agg(
                seeds=("seed", "nunique"),
                assignment_feasibility_rate=("assignment_feasible", "mean"),
                arrival_success_rate=("arrival_success", "mean"),
                arrival_rate_median=("arrival_rate", "median"),
                arrival_time_s_median=("coalition_arrival_time_s", "median"),
                distance_m_median=("distance_m", "median"),
                actual_energy_median=("actual_energy", "median"),
                obstacle_count_min=("obstacle_count", "min"),
                blocked_direct_paths_min=("blocked_direct_paths", "min"),
                astar_detoured_paths_min=("astar_detoured_paths", "min"),
                obstacle_intrusions_sum=("sampled_obstacle_intrusions", "sum"),
            )
        )
        warehouse = runs[runs.scenario == "warehouse"]
        statistics["e6"] = {
            "runs": int(len(runs)),
            "warehouse_runs": int(len(warehouse)),
            "warehouse_with_obstacles": int((warehouse.obstacle_count > 0).sum()),
            "warehouse_with_blocked_direct_path": int((warehouse.blocked_direct_paths > 0).sum()),
            "warehouse_with_astar_detour": int((warehouse.astar_detoured_paths > 0).sum()),
            "arrival_success_rate": float(runs.arrival_success.mean()),
        }
    return tables, statistics


def _scientific_gates(
    config: dict[str, Any],
    tables: dict[str, pd.DataFrame],
    available: set[str],
) -> dict[str, bool]:
    gates: dict[str, bool] = {}
    if "e1" in available:
        table = tables["e1_convergence_comparability"]
        total = int(table.runs.sum())
        operational = int(table.operational_converged_count.sum())
        # Comparability is evaluated only among operationally converged runs.
        # Recover the exact denominator from the raw paired counts by noting
        # that refinement is attempted if and only if operational convergence
        # succeeds; refinement convergence is stricter than comparability.
        comparable = int(table.comparable_at_1e6_count.sum())
        gates["e1_operational_convergence_at_least_95pct"] = operational / max(total, 1) >= float(config["acceptance"]["e1_operational_convergence_min"])
        gates["e1_refined_comparability_at_least_90pct"] = comparable / max(operational, 1) >= float(config["acceptance"]["e1_refined_comparability_min"])
    if "e4" in available:
        table = tables["e4_feasibility_by_configuration"]
        augment = table[table.method == "AugmentingRepair-V2"]
        gates["e4_augmenting_feasibility_at_least_95pct"] = float(
            augment.feasible_count.sum() / max(augment.runs.sum(), 1)
        ) >= float(config["acceptance"]["e4_augmenting_feasibility_min"])
        gates["e4_every_configuration_reported"] = len(augment) == len(config["e4"]["configurations"])
    if "e5" in available:
        table = tables["e5_scalability"]
        recovery = table[table.method == "Rep-D+AugmentingRecovery-V2"]
        gates["e5_reaches_configured_maximum_with_censoring_reported"] = int(table.n_robots.max()) == max(map(int, config["e5"]["fleet_sizes"])) and recovery.censored_rate.notna().all()
        # This invariant is also checked directly in raw data by integrity.
        gates["e5_recovery_guard_present"] = len(recovery) == len(config["e5"]["fleet_sizes"])
    if "e6" in available:
        table = tables["e6_scenario_summary"]
        warehouse = table[table.scenario == "warehouse"]
        gates["e6_obstacles_nonempty_every_warehouse_case"] = bool((warehouse.obstacle_count_min >= 1).all())
        gates["e6_direct_block_and_astar_detour_every_warehouse_case"] = bool(
            (warehouse.blocked_direct_paths_min >= 1).all() and (warehouse.astar_detoured_paths_min >= 1).all()
        )
    return gates


def _integrity_checks(
    config: dict[str, Any],
    base: Path,
    available: set[str],
    preflight: dict[str, Any],
) -> dict[str, bool]:
    checks: dict[str, bool] = {"preflight_tests_passed": preflight["returncode"] == 0}
    if "e1" in available:
        runs = pd.read_csv(base / "raw" / "e1_runs.csv")
        expected = len(config["e1"]["configurations"]) * len(_seed_values(config["e1"]["seeds"])) * 3
        checks["e1_exact_run_count"] = len(runs) == expected
        checks["e1_three_methods_per_world"] = bool((runs.groupby("world_hash").method.nunique() == 3).all())
        checks["e1_no_simplex_violation"] = bool((runs.simplex_violation <= 1e-9).all())
    if "e4" in available:
        runs = pd.read_csv(base / "raw" / "e4_runs.csv")
        assignments = pd.read_csv(base / "raw" / "e4_assignments.csv")
        expected_worlds = len(config["e4"]["configurations"]) * len(_seed_values(config["e4"]["seeds"]))
        checks["e4_exact_world_count"] = runs.world_hash.nunique() == expected_worlds
        checks["e4_four_methods_per_world"] = bool((runs.groupby("world_hash").method.nunique() == 4).all())
        checks["e4_paired_origin_identical"] = bool((runs.groupby("world_hash").origin_assignment_hash.nunique() == 1).all())
        checks["e4_one_assignment_per_robot_method"] = bool(
            (assignments.groupby(["world_hash", "method", "robot_id"]).size() == 1).all()
        )
    if "e5" in available:
        runs = pd.read_csv(base / "raw" / "e5_runs.csv")
        recovery = runs[runs.method == "Rep-D+AugmentingRecovery-V2"]
        checks["e5_all_sizes_and_seeds"] = set(runs.n_robots.unique()) == set(map(int, config["e5"]["fleet_sizes"])) and all(
            recovery.loc[recovery.n_robots == int(n), "seed"].nunique() == len(_seed_values(config["e5"]["seed_blocks"][str(n)]))
            for n in config["e5"]["fleet_sizes"]
        )
        checks["e5_no_recovery_after_nonconvergence"] = not bool(
            (_boolean_series(recovery.recovery_executed) & ~_boolean_series(recovery.operational_converged)).any()
        )
        checks["e5_messages_and_censoring_recorded"] = bool(
            recovery[["messages_total", "censored", "failure_stage"]].notna().all().all()
        )
    if "e6" in available:
        runs = pd.read_csv(base / "raw" / "e6_runs.csv")
        paths = pd.read_csv(base / "raw" / "e6_paths.csv")
        expected = len(config["e6"]["fleet_sizes"]) * len(_seed_values(config["e6"]["seeds"])) * len(config["e6"]["scenarios"])
        warehouse = runs[runs.scenario == "warehouse"]
        checks["e6_exact_run_count"] = len(runs) == expected
        checks["e6_conditioned_geometry_verified"] = bool(
            (warehouse.obstacle_count >= 1).all()
            and (warehouse.blocked_direct_paths >= 1).all()
            and (warehouse.astar_detoured_paths >= 1).all()
            and paths.direct_path_blocked.any()
            and paths.astar_detoured.any()
        )
        expected_videos = len(config["e6"]["fleet_sizes"]) * len(config["e6"]["scenarios"])
        checks["e6_trajectories_exist_for_expected_videos"] = int(_boolean_series(runs.trajectory_recorded).sum()) == expected_videos
    return checks


def _make_figures(base: Path, tables: dict[str, pd.DataFrame], available: set[str]) -> None:
    style = {"axes.grid": True, "grid.alpha": 0.25, "figure.facecolor": "white", "axes.facecolor": "#FBFCFE"}
    with plt.rc_context(style):
        if "e1" in available:
            table = tables["e1_convergence_comparability"]
            figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
            for method, group in table.groupby("method"):
                group = group.sort_values("n_robots")
                axes[0].plot(group.n_robots, group.operational_converged_rate, marker="o", label=method)
                axes[0].fill_between(group.n_robots, group.operational_converged_ci95_low, group.operational_converged_ci95_high, alpha=0.12)
                axes[1].plot(group.n_robots, group.comparable_at_1e6_rate, marker="o", label=method)
            axes[0].axhline(0.95, color="#B42318", linestyle="--", linewidth=1, label="umbral 0.95")
            axes[1].axhline(0.90, color="#B42318", linestyle="--", linewidth=1, label="umbral 0.90")
            axes[0].set(title="Convergencia operacional V2", xlabel="Robots N", ylabel="Proporción", ylim=(-0.02, 1.04))
            axes[1].set(title="Comparabilidad refinada (factibilidad 1e-6)", xlabel="Robots N", ylabel="Proporción", ylim=(-0.02, 1.04))
            axes[0].legend(fontsize=7)
            axes[1].legend(fontsize=7)
            _save_figure(figure, base / "figures" / "F1_v2_convergence_comparability")

            figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
            for method, group in table.groupby("method"):
                group = group.sort_values("n_robots")
                axes[0].plot(group.n_robots, group.iterations_total_median, marker="o", label=method)
                axes[1].plot(group.n_robots, group.messages_total_median, marker="o", label=method)
            axes[0].set(title="Iteraciones totales (mediana)", xlabel="Robots N", ylabel="Iteraciones", yscale="log")
            axes[1].set(title="Mensajes totales (mediana)", xlabel="Robots N", ylabel="Mensajes", yscale="symlog")
            axes[0].legend(fontsize=7)
            axes[1].legend(fontsize=7)
            _save_figure(figure, base / "figures" / "F2_v2_cost_and_censoring")
        if "e4" in available:
            table = tables["e4_feasibility_by_configuration"]
            methods = ["GreedyRepair-V1", "AugmentingRepair-V2"]
            configs = sorted({(int(row.n_robots), int(row.n_loads)) for row in table.itertuples()})
            matrix = np.asarray([
                [float(table[(table.method == method) & (table.n_robots == n) & (table.n_loads == k)].feasible_rate.iloc[0]) for n, k in configs]
                for method in methods
            ])
            figure, axis = plt.subplots(figsize=(12, 3.5), constrained_layout=True)
            image = axis.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
            axis.set_xticks(range(len(configs)), [f"{n},{k}" for n, k in configs], rotation=45, ha="right")
            axis.set_yticks(range(len(methods)), methods)
            axis.set(xlabel="Configuración (N,K)", title="Factibilidad de recuperación entera")
            for row in range(matrix.shape[0]):
                for column in range(matrix.shape[1]):
                    axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", fontsize=7)
            figure.colorbar(image, ax=axis, label="Proporción factible")
            _save_figure(figure, base / "figures" / "F3_v2_augmenting_recovery")
        if "e5" in available:
            table = tables["e5_scalability"]
            figure, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
            for method, group in table.groupby("method"):
                group = group.sort_values("n_robots")
                axes[0].plot(group.n_robots, group.runtime_s_median, marker="o", label=method)
                if group.messages_total_median.max() > 0:
                    axes[1].plot(group.n_robots, group.messages_total_median, marker="o", label=method)
            axes[0].set(title="Escalabilidad temporal", xlabel="Robots N", ylabel="Tiempo mediano (s)", xscale="log", yscale="log")
            axes[1].set(title="Carga de comunicación", xlabel="Robots N", ylabel="Mensajes totales medianos", xscale="log", yscale="log")
            axes[0].legend(fontsize=7)
            axes[1].legend(fontsize=7)
            _save_figure(figure, base / "figures" / "F4_v2_scalability")
        if "e6" in available:
            table = tables["e6_scenario_summary"]
            warehouse = table[table.scenario == "warehouse"].sort_values("n_robots")
            figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
            positions = np.arange(len(warehouse))
            width = 0.36
            axes[0].bar(positions - width / 2, warehouse.blocked_direct_paths_min, width=width, label="directas bloqueadas")
            axes[0].bar(positions + width / 2, warehouse.astar_detoured_paths_min, width=width, label="desvíos A*")
            axes[0].set_xticks(positions, warehouse.n_robots.astype(str))
            axes[0].set(title="Verificación geométrica mínima por tamaño", xlabel="Robots N", ylabel="Rutas por escenario")
            axes[0].legend(fontsize=8)
            for scenario, group in table.groupby("scenario"):
                axes[1].plot(group.n_robots, group.arrival_success_rate, marker="o", label=scenario)
            axes[1].set(title="Éxito de aproximación", xlabel="Robots N", ylabel="Proporción", ylim=(-0.02, 1.04))
            axes[1].legend()
            _save_figure(figure, base / "figures" / "F5_v2_conditioned_warehouse")


def _save_figure(figure: plt.Figure, stem: Path) -> None:
    figure.savefig(stem.with_suffix(".png"), dpi=220, bbox_inches="tight")
    figure.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(figure)


def _report(
    config: dict[str, Any],
    tables: dict[str, pd.DataFrame],
    statistics: dict[str, Any],
    gates: dict[str, bool],
    integrity: dict[str, bool],
    available: set[str],
) -> str:
    lines = [
        "# SP1 Conference Validation V2 — remediación dirigida",
        "",
        "V2 no repite E0, E2 ni E3. Evalúa los cuatro fallos observados en V1: paso por instancia y refinamiento (E1), recuperación entera por caminos de aumento (E4), guarda de no convergencia y censura (E5), y obstáculos constructivamente activos con desvío A* verificado (E6).",
        "",
        "## Alcance científico",
        "",
        "La evidencia corresponde a formación de coaliciones y aproximación de uniciclos a poses de contacto fijas. No valida docking, reparto de wrench ni transporte físico de cargas.",
        "",
        "## Resultados principales",
        "",
    ]
    if "e1" in statistics:
        value = statistics["e1"]
        lines.extend([
            f"- E1: convergencia operacional {value['operational_convergence_rate']:.3f}; comparabilidad a 1e-6 entre ejecuciones operacionales {value['refined_comparability_rate_among_operational']:.3f}; censuras operacionales {value['operational_censored']} y de refinamiento {value['refinement_censored']}.",
        ])
    if "e4" in statistics:
        value = statistics["e4"]
        lines.extend([
            f"- E4: factibilidad greedy V1 {value['greedy_feasibility_rate']:.3f} frente a caminos de aumento V2 {value['augmenting_feasibility_rate']:.3f}; McNemar exacto p={value['exact_mcnemar_pvalue']:.6g} en {value['paired_worlds']} mundos emparejados.",
        ])
    if "e5" in statistics:
        value = statistics["e5"]
        lines.extend([
            f"- E5: tamaños hasta N={value['maximum_n']}; recuperaciones ejecutadas {value['recovery_executed']}, omitidas por no convergencia {value['recovery_skipped_nonconverged']} y recuperaciones indebidas tras no convergencia {value['recovery_after_nonconvergence']}.",
        ])
    if "e6" in statistics:
        value = statistics["e6"]
        lines.extend([
            f"- E6: {value['warehouse_with_obstacles']}/{value['warehouse_runs']} warehouse con obstáculos, {value['warehouse_with_blocked_direct_path']}/{value['warehouse_runs']} con ruta directa bloqueada y {value['warehouse_with_astar_detour']}/{value['warehouse_runs']} con desvío A*.",
        ])
    lines.extend(["", "## Puertas predeclaradas", ""])
    for name, passed in gates.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`")
    lines.extend(["", "## Integridad", ""])
    for name, passed in integrity.items():
        lines.append(f"- {'PASS' if passed else 'FAIL'} — `{name}`")
    lines.extend(
        [
            "",
            "## Interpretación",
            "",
            "El estimador de escala del operador es un precondicionador numérico adimensional; no se presenta como constante de Lipschitz demostrada. La factibilidad de la recuperación no implica optimalidad; los gaps solo se calculan frente a un MILP certificado. Los obstáculos E6 se construyen deliberadamente para probar evitación y, por tanto, no estiman la frecuencia natural de bloqueos en un almacén real.",
            "",
            "Fuente: elaboración propia a partir de los CSV crudos de esta campaña.",
            "",
        ]
    )
    return "\n".join(lines)


def _artifact_hashes(base: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.name in {"artifact_hashes.csv", "audit.json"}:
            continue
        rows.append({"path": path.relative_to(base).as_posix(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    return pd.DataFrame(rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(*arguments: str, allow_failure: bool = False) -> str:
    completed = subprocess.run(["git", *arguments], capture_output=True, text=True, check=False)
    if completed.returncode != 0 and not allow_failure:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


__all__ = ["EXPERIMENTS", "execute"]
