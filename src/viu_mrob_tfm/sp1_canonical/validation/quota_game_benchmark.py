"""Reproducible runner for SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1.

The runner stores one checkpoint shard per paired world.  A resumed run never
recomputes a completed shard unless ``--force`` is supplied.  Scalar methods,
the discrete-service E10 benchmark and E9 repair controls remain separate
domains in the output schema.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linear_sum_assignment
from scipy.stats import binomtest, norm, wilcoxon

from .quota_game_cases import (
    deterministic_case_catalog,
    evaluate_service_assignment,
    make_chain_world,
    make_service_world,
    run_grape_s,
    run_service_greedy,
    service_world_hash,
)
from .quota_game_core import (
    PRIMARY_METHODS,
    QPG_REVIEW_METHODS,
    AlgorithmResult,
    QuotaWorld,
    bernstein_rounding_bound,
    categorical_round,
    certificate_diagnostics,
    continuous_metrics,
    environment_record,
    evaluate_assignment,
    make_manual_quota_world,
    make_quota_graph,
    make_quota_world,
    quota_aware_seed,
    raw_assignment_from_rho,
    recover_assignment,
    run_continuous_method,
    run_primary_method,
    solve_hungarian_slots,
    solve_milp_repair,
    solve_quota_entropy_reference,
    solve_quota_lp,
    solve_quota_milp,
    stable_hash,
)


CAMPAIGN = "SP1_TFM_FINAL_QUOTA_GAME_BENCHMARK_v1"
PREVIEW = f"{CAMPAIGN}_preview"
SCALAR_CLOSURES = ("raw", "seeded", "recovered")
SERVICE_METHODS = (
    "GRAPE-S",
    "Pair-GRAPE-S",
    "Capacity-CBBA-Services",
    "QPG-Multiservice-Extension",
)


def load_config(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"not JSON serializable: {type(value)!r}")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )


def _task_seed_range(spec: Mapping[str, Any]) -> range:
    return range(int(spec["start"]), int(spec["start"]) + int(spec["count"]))


def build_preview_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    spec = config["preview"]
    tasks = []
    for n, k in spec["configurations"]:
        for seed in spec["seeds"]:
            tasks.append(
                {
                    "kind": "scalar",
                    "experiment": "PREVIEW",
                    "n": int(n),
                    "k": int(k),
                    "seed": int(seed),
                    "capacity_regime": spec["capacity_regime"],
                    "utilization": float(spec["utilization"]),
                    "quota_band": spec["quota_band"],
                    "compatibility": spec["compatibility"],
                    "topology": spec["topology"],
                    "methods": [
                        method
                        for method in PRIMARY_METHODS
                        if method != "Weighted-Pair-GRAPE"
                    ],
                }
            )
    return tasks


def _scalar_task(
    experiment: str,
    n: int,
    k: int,
    seed: int,
    spec: Mapping[str, Any],
    *,
    methods: Sequence[str] = PRIMARY_METHODS,
    suffix: str = "",
) -> dict[str, Any]:
    return {
        "kind": "scalar",
        "experiment": experiment,
        "n": int(n),
        "k": int(k),
        "seed": int(seed),
        "capacity_regime": spec.get("capacity_regime", "medium"),
        "utilization": float(spec.get("utilization", 0.8)),
        "quota_band": spec.get("quota_band", "medium"),
        "compatibility": spec.get("compatibility", "arrival_radius"),
        "topology": spec.get("topology", "rdisk_degree_8"),
        "methods": list(methods),
        "suffix": suffix,
    }


def build_full_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    ev = config["evaluation"]
    tasks: list[dict[str, Any]] = []
    for n in ev["e1"]["n_values"]:
        k = max(2, math.ceil(int(n) / 5))
        for seed in _task_seed_range(ev["e1"]["seeds"]):
            tasks.append(_scalar_task("E1", n, k, seed, ev["e1"]))
    cursor = int(ev["e2"]["seed_start"])
    for n in ev["e2"]["n_values"]:
        k = math.ceil(int(n) / 5)
        count = int(ev["e2"]["seed_counts"][int(n)])
        for seed in range(cursor, cursor + count):
            tasks.append(_scalar_task("E2", n, k, seed, ev["e2"]))
        cursor += 100
    for k in ev["e3"]["k_values"]:
        for seed in _task_seed_range(ev["e3"]["seeds"]):
            tasks.append(_scalar_task("E3", ev["e3"]["n"], k, seed, ev["e3"]))
    e4 = ev["e4"]
    for (n, k), regime, util, band, seed in itertools.product(
        e4["configurations"],
        e4["capacity_regimes"],
        e4["utilizations"],
        e4["quota_bands"],
        _task_seed_range(e4["seeds"]),
    ):
        spec = dict(e4)
        spec.update(capacity_regime=regime, utilization=util, quota_band=band)
        tasks.append(
            _scalar_task(
                "E4",
                n,
                k,
                seed,
                spec,
                suffix=f"{regime}_u{float(util):.2f}_{band}",
            )
        )
    e5 = ev["e5"]
    for (n, k), topology, seed in itertools.product(
        e5["configurations"],
        e5["topologies"],
        _task_seed_range(e5["seeds"]),
    ):
        spec = dict(e5)
        spec["topology"] = topology
        tasks.append(
            _scalar_task("E5", n, k, seed, spec, suffix=str(topology))
        )
    e6 = ev["e6"]
    for n, k in e6["configurations"]:
        for seed in _task_seed_range(e6["seeds"]):
            tasks.append(
                _scalar_task(
                    "E6",
                    n,
                    k,
                    seed,
                    e6,
                    methods=QPG_REVIEW_METHODS,
                )
            )
    # E7 is one paired event world per size/event/seed.
    e7 = ev["e7"]
    for (n, k), event, seed in itertools.product(
        e7["configurations"],
        e7["events"],
        _task_seed_range(e7["seeds"]),
    ):
        tasks.append(
            {
                **_scalar_task(
                    "E7",
                    n,
                    k,
                    seed,
                    {
                        "capacity_regime": "medium",
                        "utilization": 0.6,
                        "quota_band": "wide",
                        "compatibility": "arrival_radius",
                        "topology": e7["topology"],
                    },
                ),
                "kind": "dynamic",
                "event": event,
                "suffix": event,
            }
        )
    # E8 uses QPG-Logit states and 100 independent categorical closures.
    e8 = ev["e8"]
    for n, k in e8["sizes"]:
        for index in range(int(e8["subset_worlds_per_size"])):
            tasks.append(
                {
                    **_scalar_task(
                        "E8",
                        n,
                        k,
                        int(e8["seed_start"]) + 1000 * int(n) + index,
                        {
                            "capacity_regime": "medium",
                            "utilization": 0.8,
                            "quota_band": "medium",
                            "compatibility": "arrival_radius",
                            "topology": "rdisk_degree_8",
                        },
                        methods=["QPG-Logit-AR"],
                    ),
                    "kind": "rounding",
                    "roundings": int(e8["roundings_per_state"]),
                }
            )
    e9 = ev["e9"]
    for length in e9["chain_lengths"]:
        for index in range(int(e9["instances_per_length"])):
            tasks.append(
                {
                    "kind": "recovery",
                    "experiment": "E9",
                    "length": int(length),
                    "seed": int(e9["seed_start"]) + 100 * int(length) + index,
                    "adversarial": False,
                    "suffix": f"l{length}_{index}",
                }
            )
    for index in range(int(e9["adversarial_instances"])):
        length = 3 + index % 10
        tasks.append(
            {
                "kind": "recovery",
                "experiment": "E9",
                "length": length,
                "seed": int(e9["seed_start"]) + 5000 + index,
                "adversarial": True,
                "suffix": f"adv_l{length}_{index}",
            }
        )
    e10 = ev["e10"]
    for n, service_types, per_robot, seed in itertools.product(
        e10["n_values"],
        e10["service_types"],
        e10["services_per_robot"],
        _task_seed_range(e10["seeds"]),
    ):
        tasks.append(
            {
                "kind": "service",
                "experiment": "E10",
                "n": int(n),
                "service_types": int(service_types),
                "services_per_robot": int(per_robot),
                "task_fraction": float(e10["task_fraction"]),
                "seed": int(seed),
                "suffix": f"s{service_types}_r{per_robot}",
            }
        )
    return tasks


def task_id(task: Mapping[str, Any]) -> str:
    label = "_".join(
        str(task.get(key, ""))
        for key in (
            "experiment",
            "kind",
            "n",
            "k",
            "length",
            "seed",
            "suffix",
        )
    )
    return f"{label}_{stable_hash(task)[:12]}".replace("/", "_")


def _world_record(
    world: QuotaWorld,
    graph: Any,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "experiment": task["experiment"],
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "graph_hash": graph.graph_hash,
        "seed": world.seed,
        "n": world.n_robots,
        "k": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization": world.utilization_target,
        "quota_band": world.quota_band,
        "compatibility_regime": world.compatibility_regime,
        "topology": graph.name,
        "edges": graph.edges,
        "degree_min": graph.degree_min,
        "degree_max": graph.degree_max,
        "degree_mean": graph.degree_mean,
        "diameter": graph.diameter,
        "lambda_2": graph.lambda_2,
        "lambda_max": graph.lambda_max,
        "radius_m": graph.radius_m,
        "total_lower_quota": float(np.sum(world.lower_quotas)),
        "total_upper_quota": float(np.sum(world.upper_quotas)),
        "total_capacity": float(np.sum(world.capacities)),
    }


def _algorithm_record(result: AlgorithmResult) -> dict[str, Any]:
    return {
        "result_family": result.result_family,
        "converged": result.converged,
        "censored": result.censored,
        "censoring_reason": result.censoring_reason,
        "logical_rounds": result.logical_rounds,
        "agent_updates": result.agent_updates,
        "payoff_evaluations": result.payoff_evaluations,
        "pairwise_evaluations": result.pairwise_evaluations,
        "swaps": result.swaps,
        "accepted_moves": result.accepted_moves,
        "packets_total": result.packets_total,
        "scalar_transmissions_total": result.scalar_transmissions_total,
        "payload_bytes_total": result.payload_bytes_total,
        "bytes_to_first_feasible": result.bytes_to_first_feasible,
        "bytes_to_convergence": result.bytes_to_convergence,
        "first_feasible_round": result.first_feasible_round,
        "convergence_round": result.convergence_round,
        "wall_time_s": result.wall_time_s,
        "cpu_time_s": result.cpu_time_s,
        "peak_memory_mb": result.peak_memory_mb,
        "terminal_state_residual": result.terminal_state_residual,
        "terminal_quota_residual": result.terminal_quota_residual,
        "terminal_price_residual": result.terminal_price_residual,
        "terminal_consensus_residual": result.terminal_consensus_residual,
        "simplex_violation": result.simplex_violation,
        "mask_violation": result.mask_violation,
        "finite_state": result.finite_state,
    }


def _closure_rows(
    *,
    world: QuotaWorld,
    method_result: AlgorithmResult,
    method: str,
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    lp: Any,
    milp_result: Any,
    previous_assignment: np.ndarray | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if method_result.rho is not None:
        raw = raw_assignment_from_rho(world, method_result.rho)
        seeded = quota_aware_seed(world, method_result.rho)
    else:
        raw = np.asarray(method_result.assignment, dtype=int)
        seeded = quota_aware_seed(world, None, base_assignment=raw)
    recovered_result = recover_assignment(
        world,
        seeded,
        config["recovery"],
        previous_assignment=previous_assignment,
    )
    assignments = {
        "raw": raw,
        "seeded": seeded,
        "recovered": recovered_result.assignment,
    }
    base = {
        "experiment": task["experiment"],
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "method": method,
        "seed": int(task["seed"]),
        "n": world.n_robots,
        "k": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization": world.utilization_target,
        "quota_band": world.quota_band,
        "compatibility_regime": world.compatibility_regime,
        **_algorithm_record(method_result),
    }
    rows: list[dict[str, Any]] = []
    certificate: dict[str, Any] = {}
    for closure, assignment in assignments.items():
        metrics = evaluate_assignment(
            world,
            assignment,
            previous_assignment=previous_assignment,
        )
        lp_gap = (
            (metrics["distance_total_m"] - lp.objective_m)
            / max(1.0, abs(lp.objective_m))
            if metrics["feasible"] and lp.optimal
            else math.nan
        )
        milp_gap = (
            (metrics["distance_total_m"] - milp_result.objective_m)
            / max(1.0, abs(milp_result.objective_m))
            if metrics["feasible"] and milp_result is not None and milp_result.optimal
            else math.nan
        )
        rows.append(
            {
                **base,
                "closure": closure,
                "feasible": metrics["feasible"],
                "compatible": metrics["compatible"],
                "exclusive": metrics["exclusive"],
                "deficit_total": metrics["deficit_total"],
                "deficit_ratio": metrics["deficit_ratio"],
                "excess_upper_total": metrics["excess_upper_total"],
                "overcapacity_total": metrics["overcapacity_total"],
                "overcapacity_ratio": metrics["overcapacity_ratio"],
                "robots_used": metrics["robots_used"],
                "distance_total_m": metrics["distance_total_m"],
                "maximum_distance_m": metrics["maximum_distance_m"],
                "recourse_hamming": metrics["recourse_hamming"],
                "lp_gap": lp_gap,
                "milp_certified_gap": milp_gap,
                "assignment_hash": stable_hash(np.asarray(assignment, dtype=np.int64)),
                "recovery_success": (
                    recovered_result.success if closure == "recovered" else None
                ),
                "recovery_failure_reason": (
                    recovered_result.failure_reason
                    if closure == "recovered"
                    else "not_applied"
                ),
            }
        )
    if method in {"QPG-Replicator-AR", "QPG-Logit-AR"}:
        certificate = certificate_diagnostics(
            world,
            method_result.rho,
            recovered_result.assignment,
            method_result.lambda_minus,
            method_result.lambda_plus,
            tau=float(config["potential"]["entropy_tau"]),
            lp_reference=lp,
            milp_reference=milp_result,
        )
        certificate.update(
            experiment=task["experiment"],
            world_id=world.world_id,
            method=method,
        )
        for row in rows:
            row.update(
                certificate_valid=certificate["certificate_valid"],
                dual_lower_bound_m=certificate["dual_lower_bound_m"],
                gap_cert=certificate["gap_cert"],
                atomicity_cost_m=certificate["atomicity_cost_m"],
            )
    else:
        for row in rows:
            row.update(
                certificate_valid=None,
                dual_lower_bound_m=math.nan,
                gap_cert=math.nan,
                atomicity_cost_m=math.nan,
            )
    recovery_row = {
        "experiment": task["experiment"],
        "world_id": world.world_id,
        "method": method,
        "success": recovered_result.success,
        "failure_reason": recovered_result.failure_reason,
        "maximum_chain_length": recovered_result.maximum_chain_length,
        "mean_chain_length": recovered_result.mean_chain_length,
        "nodes_expanded": recovered_result.nodes_expanded,
        "runtime_s": recovered_result.runtime_s,
        "robots_reassigned": recovered_result.robots_reassigned,
        "cost_before_m": recovered_result.cost_before_m,
        "cost_after_m": recovered_result.cost_after_m,
        "loads_repaired": recovered_result.loads_repaired,
        "residual_deficit_loads": recovered_result.residual_deficit_loads,
        "residual_excess_loads": recovered_result.residual_excess_loads,
        "residual_no_path": recovered_result.residual_no_path,
    }
    return rows, [recovery_row], certificate


def _oracle_rows(
    world: QuotaWorld,
    task: Mapping[str, Any],
    lp: Any,
    milp_result: Any,
    entropy_result: Any | None,
) -> list[dict[str, Any]]:
    rows = []
    for result in (lp, entropy_result, milp_result):
        if result is None:
            continue
        rows.append(
            {
                "experiment": task["experiment"],
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "method": result.method,
                "closure": "oracle_reference",
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_loads,
                "result_family": "centralized_reference",
                "feasible": result.feasible,
                "optimal": result.optimal,
                "solver_status": result.status,
                "distance_total_m": result.objective_m,
                "lower_bound_m": result.lower_bound_m,
                "upper_bound_m": result.upper_bound_m,
                "solver_gap": result.mip_gap,
                "wall_time_s": result.wall_time_s,
                "cpu_time_s": result.cpu_time_s,
                "censored": result.status == "limit",
                "censoring_reason": result.status,
                "finite_state": bool(np.isfinite(result.objective_m)),
            }
        )
    return rows


def _make_scalar_world(task: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[QuotaWorld, Any]:
    world = make_quota_world(
        int(task["n"]),
        int(task["k"]),
        int(task["seed"]),
        config,
        capacity_regime=str(task["capacity_regime"]),
        utilization=float(task["utilization"]),
        quota_band=str(task["quota_band"]),
        compatibility_regime=str(task["compatibility"]),
        world_id=(
            f"{task['experiment'].lower()}_n{task['n']}_k{task['k']}_"
            f"s{task['seed']}_{task.get('suffix', '')}"
        ),
    )
    graph = make_quota_graph(world, str(task["topology"]), config)
    return world, graph


def run_scalar_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    world, graph = _make_scalar_world(task, config)
    lp = solve_quota_lp(world)
    milp_result = (
        solve_quota_milp(
            world,
            time_limit_s=float(config["oracles"]["milp_timeout_s"]),
        )
        if world.n_robots <= int(config["oracles"]["milp_max_n_default"])
        else None
    )
    entropy_result = (
        solve_quota_entropy_reference(
            world,
            tau=float(config["potential"]["entropy_tau"]),
        )
        if task["experiment"] == "PREVIEW"
        and world.n_robots <= int(config["oracles"]["entropy_reference_max_n"])
        else None
    )
    runs = _oracle_rows(world, task, lp, milp_result, entropy_result)
    messages: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    recovery: list[dict[str, Any]] = []
    theorem: list[dict[str, Any]] = []
    for method in task["methods"]:
        if method in QPG_REVIEW_METHODS:
            result = run_continuous_method(
                world,
                graph,
                method,
                config,
                parameters,
                stage=stage,
            )
        else:
            result = run_primary_method(
                world,
                graph,
                method,
                config,
                parameters,
                stage=stage,
                seed=int(task["seed"]) + int(stable_hash(method)[:8], 16),
            )
        closure_rows, recovery_rows, certificate = _closure_rows(
            world=world,
            method_result=result,
            method=method,
            task=task,
            config=config,
            lp=lp,
            milp_result=milp_result,
        )
        runs.extend(closure_rows)
        recovery.extend(recovery_rows)
        if certificate:
            theorem.append(certificate)
        for row in result.message_rows:
            messages.append(
                {
                    "experiment": task["experiment"],
                    "world_id": world.world_id,
                    "method": method,
                    **row,
                }
            )
        for row in result.traces:
            traces.append(
                {
                    "experiment": task["experiment"],
                    "world_id": world.world_id,
                    "method": method,
                    **row,
                }
            )
    return {
        "runs": runs,
        "worlds": [_world_record(world, graph, task)],
        "messages": messages,
        "traces": traces,
        "recovery": recovery,
        "theorem": theorem,
        "dynamic": [],
        "exclusions": [],
    }


def run_rounding_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    payload = run_scalar_task(task, config, parameters, stage=stage)
    world, graph = _make_scalar_world(task, config)
    result = run_continuous_method(
        world,
        graph,
        "QPG-Logit-AR",
        config,
        parameters,
        stage=stage,
    )
    bound = bernstein_rounding_bound(world, result.rho)
    rng = np.random.default_rng(
        int(config["rounding_seed"]) + int(task["seed"])
    )
    failures = 0
    for _ in range(int(task["roundings"])):
        assignment = categorical_round(world, result.rho, rng)
        failures += int(not evaluate_assignment(world, assignment)["feasible"])
    frequency = failures / int(task["roundings"])
    payload["theorem"].append(
        {
            "experiment": "E8",
            "world_id": world.world_id,
            "method": "QPG-Logit-AR",
            "roundings": int(task["roundings"]),
            "rounding_failures": failures,
            "empirical_failure_frequency": frequency,
            "bernstein_union_failure_bound": bound["union_failure_bound"],
            "bernstein_valid_empirically": bool(
                frequency <= bound["union_failure_bound"] + 1.0e-12
            ),
            "minimum_lower_margin": float(np.min(bound["lower_margin"])),
            "minimum_upper_margin": float(np.min(bound["upper_margin"])),
            "total_variance": float(np.sum(bound["capacity_variance"])),
        }
    )
    return payload


def _clone_world(
    world: QuotaWorld,
    *,
    world_id: str,
    capacities: np.ndarray | None = None,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    compatibility: np.ndarray | None = None,
) -> QuotaWorld:
    return make_manual_quota_world(
        case_id=world_id,
        robot_positions=world.robot_positions,
        load_positions=world.load_positions,
        capacities=world.capacities if capacities is None else capacities,
        lower_quotas=world.lower_quotas if lower is None else lower,
        upper_quotas=world.upper_quotas if upper is None else upper,
        compatibility=world.compatibility if compatibility is None else compatibility,
        witness_assignment=world.witness_assignment,
    )


def _dynamic_pair(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[QuotaWorld, QuotaWorld, Any, np.ndarray, dict[str, Any]]:
    final, _ = _make_scalar_world(task, config)
    event = str(task["event"])
    initial = final
    detail: dict[str, Any] = {"event": event}
    if event == "new_load":
        lower = final.lower_quotas.copy()
        upper = final.upper_quotas.copy()
        lower[-1] = 0.0
        upper[-1] = 0.0
        initial = _clone_world(
            final,
            world_id=final.world_id + "_pre",
            lower=lower,
            upper=upper,
        )
        detail["affected_load"] = final.n_loads - 1
    elif event == "load_completion":
        lower = final.lower_quotas.copy()
        upper = final.upper_quotas.copy()
        lower[0] = 0.0
        upper[0] = 0.0
        post = _clone_world(
            final,
            world_id=final.world_id + "_post",
            lower=lower,
            upper=upper,
        )
        initial, final = final, post
        detail["affected_load"] = 0
    elif event in {"committed_robot_failure", "capacity_drop"}:
        witness = np.asarray(initial.witness_assignment, dtype=int)
        active = np.flatnonzero(witness < initial.n_loads)
        ordered = sorted(map(int, active), key=lambda r: (final.capacities[r], r))
        post = None
        robot = ordered[0]
        for candidate_robot in ordered:
            if event == "committed_robot_failure":
                compatibility = final.compatibility.copy()
                compatibility[candidate_robot, :] = False
                candidate_post = _clone_world(
                    final,
                    world_id=final.world_id + "_post",
                    compatibility=compatibility,
                )
            else:
                capacities = final.capacities.copy()
                capacities[candidate_robot] *= 0.5
                candidate_post = _clone_world(
                    final,
                    world_id=final.world_id + "_post",
                    capacities=capacities,
                )
            if solve_quota_lp(candidate_post).feasible:
                robot = candidate_robot
                post = candidate_post
                break
        if post is None:
            raise RuntimeError("could not construct a feasible dynamic perturbation")
        final = post
        detail["affected_robot"] = robot
    graph = make_quota_graph(
        final,
        (
            "rdisk_degree_4"
            if event == "topology_degradation"
            else str(task["topology"])
        ),
        config,
    )
    commitment = np.asarray(initial.witness_assignment, dtype=int).copy()
    if event == "new_load":
        commitment[commitment == initial.n_loads - 1] = initial.n_loads
    if not evaluate_assignment(initial, commitment)["feasible"]:
        seed_assignment = quota_aware_seed(initial, None)
        repaired = recover_assignment(initial, seed_assignment, config["recovery"])
        if not repaired.success:
            raise RuntimeError("no valid initial commitment for dynamic event")
        commitment = repaired.assignment
    return initial, final, graph, commitment, detail


def run_dynamic_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    initial, world, graph, commitment, detail = _dynamic_pair(task, config)
    lp = solve_quota_lp(world)
    milp_result = (
        solve_quota_milp(world, time_limit_s=60.0)
        if world.n_robots <= int(config["oracles"]["milp_max_n_default"])
        else None
    )
    runs = _oracle_rows(world, task, lp, milp_result, None)
    messages: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    dynamic_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    initial_rho = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    initial_rho[np.arange(world.n_robots), commitment] = 1.0
    failed_robot = detail.get("affected_robot")
    if failed_robot is not None and task["event"] == "committed_robot_failure":
        initial_rho[int(failed_robot), :] = 0.0
        initial_rho[int(failed_robot), world.idle_index] = 1.0
    for method in task["methods"]:
        warm_assignment = commitment.copy()
        affected_robot = detail.get("affected_robot")
        if affected_robot is not None and task["event"] == "committed_robot_failure":
            warm_assignment[int(affected_robot)] = world.idle_index
        try:
            result = run_primary_method(
                world,
                graph,
                method,
                config,
                parameters,
                stage=stage,
                seed=int(task["seed"]) + int(stable_hash(method)[:8], 16),
                initial_assignment=warm_assignment,
                initial_rho=initial_rho,
                previous_assignment=commitment,
            )
            closure, rec, _ = _closure_rows(
                world=world,
                method_result=result,
                method=method,
                task=task,
                config=config,
                lp=lp,
                milp_result=milp_result,
                previous_assignment=commitment,
            )
            runs.extend(closure)
            recovery_rows.extend(rec)
            recovered = next(row for row in closure if row["closure"] == "recovered")
            if result.rho is not None:
                dynamic_seed = quota_aware_seed(world, result.rho)
            else:
                dynamic_seed = quota_aware_seed(
                    world,
                    None,
                    base_assignment=result.assignment,
                )
            dynamic_recovered = recover_assignment(
                world,
                dynamic_seed,
                config["recovery"],
                previous_assignment=commitment,
            ).assignment
            old_loads = set(map(int, commitment[commitment < initial.n_loads]))
            affected_load = detail.get("affected_load")
            if affected_load is not None:
                old_loads.discard(int(affected_load))
            unchanged = 0
            for load in old_loads:
                before = set(map(int, np.flatnonzero(commitment == load)))
                after = set(map(int, np.flatnonzero(dynamic_recovered == load)))
                unchanged += int(before == after)
            dynamic_rows.append(
                {
                    "world_id": world.world_id,
                    "method": method,
                    "event": task["event"],
                    "initial_commitment_valid": evaluate_assignment(
                        initial, commitment
                    )["feasible"],
                    "post_event_feasible": recovered["feasible"],
                    "time_to_new_feasibility_s": result.wall_time_s
                    + rec[0]["runtime_s"],
                    "bytes_recovery": result.payload_bytes_total,
                    "robots_reassigned": recovered["recourse_hamming"],
                    "integrated_quota_violation": float(
                        sum(
                            trace.get("lower_violation", trace.get("deficit_total", 0.0))
                            + trace.get("upper_violation", 0.0)
                            for trace in result.traces
                        )
                    ),
                    "unaffected_coalition_intact_fraction": (
                        unchanged / len(old_loads) if old_loads else 1.0
                    ),
                    "service_duration_mean_s": float(
                        np.mean(initial.service_durations_s)
                    ),
                    "arrival_deadline_mean_s": float(
                        np.mean(initial.arrival_deadlines_s)
                    ),
                }
            )
            messages.extend(
                {
                    "experiment": "E7",
                    "world_id": world.world_id,
                    "method": method,
                    **row,
                }
                for row in result.message_rows
            )
            traces.extend(
                {
                    "experiment": "E7",
                    "world_id": world.world_id,
                    "method": method,
                    **row,
                }
                for row in result.traces
            )
        except Exception as exc:  # retained as an auditable exclusion
            exclusions.append(
                {
                    "experiment": "E7",
                    "world_id": world.world_id,
                    "method": method,
                    "reason": f"{type(exc).__name__}: {exc}",
                }
            )
    return {
        "runs": runs,
        "worlds": [_world_record(world, graph, task)],
        "messages": messages,
        "traces": traces,
        "recovery": recovery_rows,
        "theorem": [],
        "dynamic": dynamic_rows,
        "exclusions": exclusions,
    }


def run_recovery_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    world, initial = make_chain_world(
        int(task["length"]),
        adversarial=bool(task["adversarial"]),
        seed=int(task["seed"]),
    )
    world = replace(
        world,
        world_id=f"{world.world_id}_{task['seed']}",
        seed=int(task["seed"]),
    )
    rows = []
    for method, limit in (
        ("greedy", 1),
        ("swap", 2),
        ("augmenting_paths", int(config["recovery"]["max_chain_length"])),
    ):
        options = dict(config["recovery"])
        options["local_exchange"] = method != "greedy"
        result = recover_assignment(
            world,
            initial,
            options,
            max_chain_length_override=limit,
        )
        rows.append(
            {
                "experiment": "E9",
                "world_id": world.world_id,
                "seed": int(task["seed"]),
                "adversarial": bool(task["adversarial"]),
                "required_chain_length": int(task["length"]),
                "repair_method": method,
                "success": result.success,
                "failure_reason": result.failure_reason,
                "maximum_chain_length": result.maximum_chain_length,
                "mean_chain_length": result.mean_chain_length,
                "nodes_expanded": result.nodes_expanded,
                "runtime_s": result.runtime_s,
                "robots_reassigned": result.robots_reassigned,
                "cost_before_m": result.cost_before_m,
                "cost_after_m": result.cost_after_m,
                "residual_no_path": result.residual_no_path,
            }
        )
    milp_result = solve_milp_repair(world, initial)
    assignment = milp_result.assignment
    metrics = evaluate_assignment(world, assignment)
    rows.append(
        {
            "experiment": "E9",
            "world_id": world.world_id,
            "seed": int(task["seed"]),
            "adversarial": bool(task["adversarial"]),
            "required_chain_length": int(task["length"]),
            "repair_method": "milp_repair",
            "success": milp_result.success,
            "failure_reason": milp_result.failure_reason,
            "maximum_chain_length": math.nan,
            "mean_chain_length": math.nan,
            "nodes_expanded": math.nan,
            "runtime_s": milp_result.runtime_s,
            "robots_reassigned": metrics["recourse_hamming"],
            "cost_before_m": float(
                evaluate_assignment(world, initial)["distance_total_m"]
            ),
            "cost_after_m": metrics["distance_total_m"],
            "residual_no_path": False,
        }
    )
    return {
        "runs": [],
        "worlds": [
            {
                "experiment": "E9",
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_loads,
            }
        ],
        "messages": [],
        "traces": [],
        "recovery": rows,
        "theorem": [],
        "dynamic": [],
        "exclusions": [],
    }


def run_service_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    world = make_service_world(
        n=int(task["n"]),
        service_types=int(task["service_types"]),
        services_per_robot=int(task["services_per_robot"]),
        task_fraction=float(task["task_fraction"]),
        seed=int(task["seed"]),
        config=config,
    )
    runs = []
    for method in SERVICE_METHODS:
        started = time.perf_counter()
        if method == "GRAPE-S":
            result = run_grape_s(
                world,
                pairwise=False,
                seed=int(task["seed"]),
            )
        elif method == "Pair-GRAPE-S":
            result = run_grape_s(
                world,
                pairwise=True,
                seed=int(task["seed"]),
            )
        else:
            result = run_service_greedy(
                world,
                method=method,
                seed=int(task["seed"]),
            )
        metrics = evaluate_service_assignment(
            world,
            result.tasks,
            result.services,
        )
        runs.append(
            {
                "experiment": "E10",
                "domain": "discrete_services",
                "world_id": world.world_id,
                "world_hash": service_world_hash(world),
                "method": method,
                "closure": "atomic",
                "n": world.n_robots,
                "k": world.n_tasks,
                "service_types": world.n_services,
                "services_per_robot": int(task["services_per_robot"]),
                "seed": int(task["seed"]),
                "feasible": metrics["feasible"],
                "deficit_total": metrics["deficit"],
                "overcapacity_total": metrics["excess"],
                "robots_used": metrics["robots_used"],
                "logical_rounds": result.logical_rounds,
                "accepted_moves": result.unilateral_moves,
                "swaps": result.swaps,
                "packets_total": result.packets,
                "payload_bytes_total": result.bytes_total,
                "converged": result.converged,
                "censored": False,
                "censoring_reason": "none",
                "wall_time_s": time.perf_counter() - started,
                "deviation": result.deviation,
                "finite_state": True,
            }
        )
    return {
        "runs": runs,
        "worlds": [
            {
                "experiment": "E10",
                "domain": "discrete_services",
                "world_id": world.world_id,
                "world_hash": service_world_hash(world),
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_tasks,
                "service_types": world.n_services,
                "services_per_robot": int(task["services_per_robot"]),
                "graph_hash": world.graph.graph_hash,
            }
        ],
        "messages": [],
        "traces": [],
        "recovery": [],
        "theorem": [],
        "dynamic": [],
        "exclusions": [],
    }


def run_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    stage: str,
) -> dict[str, Any]:
    if task["kind"] == "scalar":
        return run_scalar_task(task, config, parameters, stage=stage)
    if task["kind"] == "rounding":
        return run_rounding_task(task, config, parameters, stage=stage)
    if task["kind"] == "dynamic":
        return run_dynamic_task(task, config, parameters, stage=stage)
    if task["kind"] == "recovery":
        return run_recovery_task(task, config)
    if task["kind"] == "service":
        return run_service_task(task, config)
    raise ValueError(f"unknown task kind: {task['kind']}")


def _checkpoint_worker(
    task: dict[str, Any],
    config: dict[str, Any],
    parameters: dict[str, Any],
    stage: str,
    path: str,
    protocol_hash: str,
) -> str:
    payload = run_task(task, config, parameters, stage)
    payload["task"] = task
    payload["protocol_hash"] = protocol_hash
    target = Path(path)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, default=_json_default, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temporary, target)
    return str(target)


def _read_shards(shards: Iterable[Path]) -> dict[str, list[dict[str, Any]]]:
    tables = {
        name: []
        for name in (
            "runs",
            "worlds",
            "messages",
            "traces",
            "recovery",
            "theorem",
            "dynamic",
            "exclusions",
        )
    }
    for shard in sorted(shards):
        payload = json.loads(shard.read_text(encoding="utf-8"))
        for name in tables:
            tables[name].extend(payload.get(name, []))
    return tables


def run_task_set(
    *,
    tasks: list[dict[str, Any]],
    config: dict[str, Any],
    parameters: dict[str, Any],
    output_dir: Path,
    stage: str,
    workers: int,
    force: bool,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    checkpoints = output_dir / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    protocol_hash = stable_hash(
        {
            "config": config,
            "parameters": parameters,
            "stage": stage,
        }
    )
    expected = {
        f"{task_id(task)}_{protocol_hash[:12]}": task
        for task in tasks
    }
    pending = []
    reused = 0
    for identifier, task in expected.items():
        path = checkpoints / f"{identifier}.json"
        if path.exists() and not force:
            reused += 1
        else:
            pending.append((task, path))
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    failures = []
    if workers <= 1:
        for task, path in pending:
            try:
                _checkpoint_worker(
                    task,
                    config,
                    parameters,
                    stage,
                    str(path),
                    protocol_hash,
                )
            except Exception as exc:
                failures.append(
                    {"task": task, "error": f"{type(exc).__name__}: {exc}"}
                )
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    _checkpoint_worker,
                    task,
                    config,
                    parameters,
                    stage,
                    str(path),
                    protocol_hash,
                ): task
                for task, path in pending
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    failures.append(
                        {
                            "task": futures[future],
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
    shards = [
        checkpoints / f"{identifier}.json"
        for identifier in expected
        if (checkpoints / f"{identifier}.json").exists()
    ]
    tables = _read_shards(shards)
    runtime = {
        "wall_time_s": time.perf_counter() - started_wall,
        "driver_cpu_time_s": time.process_time() - started_cpu,
        "algorithm_cpu_time_s": float(
            pd.to_numeric(
                pd.DataFrame(tables["runs"]).get("cpu_time_s", pd.Series(dtype=float)),
                errors="coerce",
            ).sum()
        ),
        "workers": workers,
        "tasks_expected": len(tasks),
        "tasks_completed": len(shards),
        "tasks_reused": reused,
        "task_failures": failures,
    }
    return tables, runtime


def run_calibration(
    config: dict[str, Any],
    output_dir: Path,
    *,
    workers: int,
) -> dict[str, Any]:
    rows = []
    spec = config["calibration"]
    for candidate_name, parameters in spec["candidates"].items():
        tasks = []
        for n, k in spec["configurations"]:
            for seed in spec["seeds"]:
                task = _scalar_task(
                    "CALIBRATION",
                    n,
                    k,
                    seed,
                    {
                        **spec,
                        "compatibility": "arrival_radius",
                    },
                    methods=["QPG-Replicator-AR", "QPG-Logit-AR"],
                    suffix=candidate_name,
                )
                tasks.append(task)
        # Calibration is small and intentionally independent of evaluation
        # checkpoints.
        for task in tasks:
            payload = run_scalar_task(
                task,
                config,
                parameters,
                stage="calibration",
            )
            for row in payload["runs"]:
                if row.get("closure") == "recovered" and row["method"].startswith("QPG"):
                    rows.append({"candidate": candidate_name, **row})
    frame = pd.DataFrame(rows)
    summary = (
        frame.groupby("candidate", dropna=False)
        .agg(
            recovered_feasibility=("feasible", "mean"),
            certificate_validity=("certificate_valid", "mean"),
            median_distance_m=("distance_total_m", "median"),
            median_excess=("overcapacity_total", "median"),
            median_wall_time_s=("wall_time_s", "median"),
            median_bytes=("payload_bytes_total", "median"),
        )
        .reset_index()
    )
    summary = summary.sort_values(
        [
            "recovered_feasibility",
            "certificate_validity",
            "median_distance_m",
            "median_excess",
            "median_wall_time_s",
            "median_bytes",
        ],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    )
    selected_name = str(summary.iloc[0]["candidate"])
    selected = {
        "candidate": selected_name,
        **dict(spec["candidates"][selected_name]),
        "state_tolerance": 1.0e-5,
        "quota_tolerance": 1.0e-5,
        "price_tolerance": 1.0e-5,
        "consensus_tolerance": 1.0e-4,
        "selection_rule": list(spec["objective_order"]),
        "calibration_seeds": list(spec["seeds"]),
    }
    frame.to_csv(output_dir / "calibration_runs.csv", index=False)
    summary.to_csv(output_dir / "calibration_summary.csv", index=False)
    (output_dir / "selected_parameters.yaml").write_text(
        yaml.safe_dump(selected, sort_keys=False),
        encoding="utf-8",
    )
    return selected


def run_e0(
    config: Mapping[str, Any],
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    recovery_rows = []
    for item in deterministic_case_catalog():
        world = item["world"]
        lp = solve_quota_lp(world)
        milp_result = solve_quota_milp(world, time_limit_s=60.0)
        row = {
            "experiment": "E0",
            "case": item["case"],
            "world_id": world.world_id,
            "world_hash": world.world_hash,
            "analytical_note": item["analytical_note"],
            "lp_optimal": lp.optimal,
            "milp_optimal": milp_result.optimal,
            "lp_lower_bound_m": lp.objective_m,
            "milp_objective_m": milp_result.objective_m,
            "witness_feasible": evaluate_assignment(
                world, world.witness_assignment
            )["feasible"],
        }
        if item["case"] == "hungarian_slots":
            slots = np.repeat(
                np.arange(world.n_loads),
                world.lower_quotas.astype(int),
            )
            assignment, objective = solve_hungarian_slots(
                world.distances_m,
                slots,
            )
            row.update(
                hungarian_feasible=evaluate_assignment(world, assignment)["feasible"],
                hungarian_objective_m=objective,
                hungarian_matches_milp=abs(objective - milp_result.objective_m)
                <= 1.0e-8,
            )
        initial = item.get("initial_assignment")
        if initial is not None:
            recovered = recover_assignment(world, initial, config["recovery"])
            row.update(
                initial_feasible=evaluate_assignment(world, initial)["feasible"],
                recovery_success=recovered.success,
                recovery_chain_length=recovered.maximum_chain_length,
            )
            recovery_rows.append(
                {
                    "experiment": "E0",
                    "case": item["case"],
                    "world_id": world.world_id,
                    "repair_method": "augmenting_paths",
                    "success": recovered.success,
                    "maximum_chain_length": recovered.maximum_chain_length,
                    "nodes_expanded": recovered.nodes_expanded,
                    "runtime_s": recovered.runtime_s,
                }
            )
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "e0_deterministic_cases.csv", index=False)
    return frame, pd.DataFrame(recovery_rows)


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = z / denominator * math.sqrt(
        p * (1.0 - p) / total + z * z / (4.0 * total * total)
    )
    return center - radius, center + radius


def aggregate_results(runs: pd.DataFrame) -> pd.DataFrame:
    if runs.empty:
        return pd.DataFrame()
    operational = runs[
        runs["closure"].isin(["raw", "seeded", "recovered", "atomic"])
    ].copy()
    keys = ["experiment", "method", "closure", "n", "k"]
    records = []
    for key, group in operational.groupby(keys, dropna=False):
        feasible = pd.to_numeric(group["feasible"], errors="coerce").fillna(0).astype(bool)
        lo, hi = _wilson(int(feasible.sum()), int(feasible.size))
        records.append(
            {
                **dict(zip(keys, key)),
                "runs": len(group),
                "feasibility_rate": float(feasible.mean()),
                "feasibility_wilson_low": lo,
                "feasibility_wilson_high": hi,
                "distance_median_m": float(
                    pd.to_numeric(group["distance_total_m"], errors="coerce").median()
                ),
                "overcapacity_median": float(
                    pd.to_numeric(group["overcapacity_total"], errors="coerce").median()
                ),
                "wall_time_median_s": float(
                    pd.to_numeric(group["wall_time_s"], errors="coerce").median()
                ),
                "bytes_median": float(
                    pd.to_numeric(
                        group.get("payload_bytes_total", 0), errors="coerce"
                    ).median()
                ),
                "censoring_rate": float(
                    pd.to_numeric(group.get("censored", False), errors="coerce")
                    .fillna(0)
                    .astype(bool)
                    .mean()
                ),
            }
        )
    return pd.DataFrame(records)


def _mcnemar_exact(left: np.ndarray, right: np.ndarray) -> float:
    discordant_left = int(np.sum(left & ~right))
    discordant_right = int(np.sum(~left & right))
    total = discordant_left + discordant_right
    return (
        float(binomtest(min(discordant_left, discordant_right), total, 0.5).pvalue)
        if total
        else 1.0
    )


def paired_comparisons(
    runs: pd.DataFrame,
    *,
    analysis_seed: int,
    bootstrap_resamples: int,
) -> pd.DataFrame:
    subset = runs[
        (runs["closure"] == "recovered")
        & runs["method"].isin(PRIMARY_METHODS)
    ].copy()
    if subset.empty:
        return pd.DataFrame()
    proposed = "QPG-Logit-AR"
    records = []
    rng = np.random.default_rng(analysis_seed)
    for experiment in sorted(subset["experiment"].dropna().unique()):
        exp = subset[subset["experiment"] == experiment]
        left = exp[exp["method"] == proposed].set_index("world_id")
        for baseline in [m for m in PRIMARY_METHODS if m != proposed]:
            right = exp[exp["method"] == baseline].set_index("world_id")
            common = left.index.intersection(right.index)
            if not len(common):
                continue
            left_feasible = left.loc[common, "feasible"].astype(bool).to_numpy()
            right_feasible = right.loc[common, "feasible"].astype(bool).to_numpy()
            paired = (
                left.loc[common, "distance_total_m"].to_numpy(float)
                - right.loc[common, "distance_total_m"].to_numpy(float)
            )
            finite = np.isfinite(paired)
            paired = paired[finite]
            if paired.size:
                samples = np.median(
                    paired[
                        rng.integers(
                            0,
                            paired.size,
                            size=(min(bootstrap_resamples, 2000), paired.size),
                        )
                    ],
                    axis=1,
                )
                ci_low, ci_high = np.quantile(samples, [0.025, 0.975])
                try:
                    wilcoxon_p = float(wilcoxon(paired).pvalue)
                except ValueError:
                    wilcoxon_p = 1.0
                nonzero = paired[paired != 0]
                rank_biserial = (
                    float(
                        (
                            np.sum(np.abs(nonzero)[nonzero > 0])
                            - np.sum(np.abs(nonzero)[nonzero < 0])
                        )
                        / np.sum(np.abs(nonzero))
                    )
                    if nonzero.size
                    else 0.0
                )
            else:
                ci_low = ci_high = wilcoxon_p = rank_biserial = math.nan
            records.append(
                {
                    "experiment": experiment,
                    "method": proposed,
                    "baseline": baseline,
                    "paired_worlds": len(common),
                    "mcnemar_exact_p": _mcnemar_exact(
                        left_feasible, right_feasible
                    ),
                    "distance_median_difference_m": float(np.median(paired))
                    if paired.size
                    else math.nan,
                    "distance_bootstrap_low_m": ci_low,
                    "distance_bootstrap_high_m": ci_high,
                    "wilcoxon_p": wilcoxon_p,
                    "rank_biserial": rank_biserial,
                }
            )
    frame = pd.DataFrame(records)
    if not frame.empty:
        order = np.argsort(frame["wilcoxon_p"].fillna(1.0).to_numpy())
        adjusted = np.ones(len(frame))
        raw = frame["wilcoxon_p"].fillna(1.0).to_numpy()
        running = 0.0
        for rank, index in enumerate(order):
            value = min(1.0, raw[index] * (len(frame) - rank))
            running = max(running, value)
            adjusted[index] = running
        frame["wilcoxon_holm_p"] = adjusted
    return frame


def _save_figure(fig: Any, base: Path) -> None:
    fig.tight_layout()
    fig.savefig(base.with_suffix(".png"), dpi=180, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def generate_figures(
    runs: pd.DataFrame,
    worlds: pd.DataFrame,
    theorem: pd.DataFrame,
    recovery: pd.DataFrame,
    dynamic: pd.DataFrame,
    output_dir: Path,
) -> list[str]:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(exist_ok=True)
    generated: list[str] = []

    def bar_metric(name: str, closure: str, column: str, ylabel: str) -> None:
        subset = runs[
            (runs["closure"] == closure) & runs["method"].isin(PRIMARY_METHODS)
        ]
        if subset.empty:
            return
        data = subset.groupby("method")[column].median().sort_values()
        fig, ax = plt.subplots(figsize=(9, 4.5))
        data.plot.bar(ax=ax, color="#3366aa")
        ax.set_ylabel(ylabel)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
        base = figure_dir / name
        _save_figure(fig, base)
        generated.append(name)

    # 1
    feas = runs[
        runs["closure"].isin(["raw", "recovered"])
        & runs["method"].isin(PRIMARY_METHODS)
    ]
    if not feas.empty:
        table = feas.pivot_table(
            index="method",
            columns="closure",
            values="feasible",
            aggfunc="mean",
        )
        fig, ax = plt.subplots(figsize=(9, 4.5))
        table.plot.bar(ax=ax, color=["#9ecae1", "#08519c"])
        ax.set_ylabel("Feasibility rate")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=35)
        base = figure_dir / "01_feasibility_raw_recovered"
        _save_figure(fig, base)
        generated.append(base.name)
    # 2,3,4
    bar_metric("02_distance_recovered", "recovered", "distance_total_m", "Median distance [m]")
    bar_metric("03_overcapacity_recovered", "recovered", "overcapacity_total", "Median capacity above lower quota")
    bar_metric("04_wall_time_rmst_proxy", "recovered", "wall_time_s", "Median wall time [s]")
    # 5
    bar_metric("05_bytes", "recovered", "payload_bytes_total", "Median transmitted bytes")
    # 6
    e5 = runs[(runs["experiment"] == "E5") & (runs["closure"] == "recovered")]
    if not e5.empty and not worlds.empty:
        data = e5.merge(worlds[["world_id", "lambda_2"]], on="world_id", how="left")
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for method in ["DRD-simple-Logit", "QPG-Logit-AR"]:
            part = data[data["method"] == method]
            ax.scatter(part["lambda_2"], part["payload_bytes_total"], s=10, alpha=0.5, label=method)
        ax.set_xlabel(r"Algebraic connectivity $\lambda_2$")
        ax.set_ylabel("Bytes")
        ax.legend()
        base = figure_dir / "06_lambda2_communication"
        _save_figure(fig, base)
        generated.append(base.name)
    # 7
    e6 = runs[(runs["experiment"] == "E6") & (runs["closure"] == "recovered")]
    if not e6.empty:
        data = e6.groupby("method")["feasible"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        data.plot.bar(ax=ax, color="#31a354")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Recovered feasibility")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=35)
        base = figure_dir / "07_revision_protocols"
        _save_figure(fig, base)
        generated.append(base.name)
    # 8
    e8 = theorem[theorem.get("experiment", pd.Series(dtype=str)) == "E8"]
    if not e8.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(
            e8["bernstein_union_failure_bound"],
            e8["empirical_failure_frequency"],
            color="#756bb1",
        )
        ax.plot([0, 1], [0, 1], "--", color="black")
        ax.set_xlabel("Bernstein union upper bound")
        ax.set_ylabel("Empirical failure frequency")
        base = figure_dir / "08_bernstein_validation"
        _save_figure(fig, base)
        generated.append(base.name)
    # 9
    e9 = recovery[recovery.get("experiment", pd.Series(dtype=str)) == "E9"]
    if not e9.empty:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for method, part in e9.groupby("repair_method"):
            data = part.groupby("required_chain_length")["success"].mean()
            ax.plot(data.index, data.values, marker="o", label=method)
        ax.set_xlabel("Required chain length")
        ax.set_ylabel("Success rate")
        ax.set_ylim(-0.02, 1.02)
        ax.legend()
        base = figure_dir / "09_augmenting_paths"
        _save_figure(fig, base)
        generated.append(base.name)
    # 10
    if not dynamic.empty:
        data = dynamic.groupby(["event", "method"])["robots_reassigned"].median().unstack()
        fig, ax = plt.subplots(figsize=(10, 5))
        data.plot.bar(ax=ax)
        ax.set_ylabel("Median recourse [robots]")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        ax.legend(fontsize=7, ncol=2)
        base = figure_dir / "10_dynamic_recovery"
        _save_figure(fig, base)
        generated.append(base.name)
    # 11
    rec = runs[
        (runs["closure"] == "recovered") & runs["method"].isin(PRIMARY_METHODS)
    ]
    if not rec.empty:
        data = rec.groupby("method").agg(
            distance=("distance_total_m", "median"),
            bytes=("payload_bytes_total", "median"),
        )
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(data["bytes"], data["distance"])
        for method, row in data.iterrows():
            ax.annotate(method, (row["bytes"], row["distance"]), fontsize=7)
        ax.set_xscale("symlog")
        ax.set_xlabel("Median bytes")
        ax.set_ylabel("Median distance [m]")
        base = figure_dir / "11_pareto_quality_cost"
        _save_figure(fig, base)
        generated.append(base.name)
    # 12
    cert = theorem[
        theorem.get("gap_cert", pd.Series(index=theorem.index, dtype=float)).notna()
    ]
    if not cert.empty:
        columns = [
            "optimization_error_normalized",
            "entropy_bias_bound_normalized",
            "atomicity_cost_m",
        ]
        data = cert[columns].apply(pd.to_numeric, errors="coerce").median()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        data.plot.bar(ax=ax, color=["#3182bd", "#9ecae1", "#de2d26"])
        ax.set_ylabel("Median diagnostic magnitude")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        base = figure_dir / "12_gap_decomposition"
        _save_figure(fig, base)
        generated.append(base.name)
    return generated


def _write_tables(
    tables: Mapping[str, list[dict[str, Any]]],
    output_dir: Path,
    e0: pd.DataFrame,
    e0_recovery: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, pd.DataFrame]:
    frames = {name: pd.DataFrame(rows) for name, rows in tables.items()}
    runs = frames["runs"]
    e0_worlds = e0[
        ["experiment", "world_id", "world_hash"]
    ].copy()
    worlds = (
        pd.concat([frames["worlds"], e0_worlds], ignore_index=True)
        .drop_duplicates("world_id", keep="first")
    )
    recovery = pd.concat([frames["recovery"], e0_recovery], ignore_index=True)
    aggregated = aggregate_results(runs)
    paired = paired_comparisons(
        runs,
        analysis_seed=int(config["analysis_seed"]),
        bootstrap_resamples=int(config["statistics"]["bootstrap_resamples"]),
    )
    censoring = (
        runs[runs.get("censored", False).fillna(False).astype(bool)]
        if "censored" in runs
        else pd.DataFrame()
    )
    mapping = {
        "all_runs": runs,
        "all_messages": frames["messages"],
        "all_traces": frames["traces"],
        "worlds": worlds,
        "aggregated_results": aggregated,
        "paired_comparisons": paired,
        "censoring": censoring,
        "exclusions": frames["exclusions"],
        "theorem_diagnostics": frames["theorem"],
        "recovery_paths": recovery,
        "dynamic_events": frames["dynamic"],
    }
    for name, frame in mapping.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)
        if name in {"all_runs", "all_messages", "all_traces"}:
            frame.to_parquet(output_dir / f"{name}.parquet", index=False)
    message_validation = pd.DataFrame()
    if not runs.empty:
        algorithm_totals = (
            runs[runs["closure"] == "raw"][
                ["world_id", "method", "packets_total", "scalar_transmissions_total", "payload_bytes_total"]
            ]
            .drop_duplicates(["world_id", "method"])
            .copy()
        )
        if not frames["messages"].empty:
            recomputed = (
                frames["messages"]
                .groupby(["world_id", "method"], as_index=False)
                .agg(
                    packets_recomputed=("packets", "sum"),
                    scalars_recomputed=("scalars", "sum"),
                    bytes_recomputed=("bytes", "sum"),
                )
            )
            message_validation = algorithm_totals.merge(
                recomputed, on=["world_id", "method"], how="left"
            )
            message_validation["valid"] = (
                message_validation["packets_total"].fillna(0)
                == message_validation["packets_recomputed"].fillna(0)
            ) & (
                message_validation["payload_bytes_total"].fillna(0)
                == message_validation["bytes_recomputed"].fillna(0)
            )
    message_validation.to_csv(
        output_dir / "message_accounting_validation.csv",
        index=False,
    )
    mapping["message_accounting_validation"] = message_validation
    return mapping


def _regime_map(runs: pd.DataFrame) -> pd.DataFrame:
    e4 = runs[
        (runs["experiment"] == "E4")
        & (runs["closure"] == "recovered")
        & runs["method"].isin(PRIMARY_METHODS)
    ]
    if e4.empty:
        return pd.DataFrame()
    records = []
    keys = ["capacity_regime", "utilization", "quota_band"]
    for key, group in e4.groupby(keys):
        summary = group.groupby("method").agg(
            feasibility=("feasible", "mean"),
            distance=("distance_total_m", "median"),
            excess=("overcapacity_total", "median"),
            time=("wall_time_s", "median"),
            bytes=("payload_bytes_total", "median"),
        )
        eligible = summary[summary["feasibility"] >= 0.95]
        winner = (
            str(
                (
                    eligible["distance"]
                    + 0.1 * eligible["excess"]
                ).idxmin()
            )
            if not eligible.empty
            else "none_at_95pct_feasibility"
        )
        records.append(
            {
                **dict(zip(keys, key)),
                "descriptive_winner": winner,
                "criterion": "min median distance+0.1 excess among methods with >=95% feasibility",
            }
        )
    return pd.DataFrame(records)


def create_report(
    *,
    output_dir: Path,
    frames: Mapping[str, pd.DataFrame],
    runtime: Mapping[str, Any],
    figures: Sequence[str],
    is_preview: bool,
) -> str:
    runs = frames["all_runs"]
    rec = runs[
        (runs["closure"] == "recovered") & runs["method"].isin(PRIMARY_METHODS)
    ]
    summary = (
        rec.groupby("method")
        .agg(
            runs=("world_id", "count"),
            feasibility=("feasible", "mean"),
            distance_median_m=("distance_total_m", "median"),
            excess_median=("overcapacity_total", "median"),
            time_median_s=("wall_time_s", "median"),
            bytes_median=("payload_bytes_total", "median"),
        )
        .sort_values(["feasibility", "distance_median_m"], ascending=[False, True])
        if not rec.empty
        else pd.DataFrame()
    )
    service = runs[runs["experiment"] == "E10"]
    service_summary = (
        service.groupby("method")["feasible"].mean().sort_values(ascending=False)
        if not service.empty
        else pd.Series(dtype=float)
    )
    certificate = frames["theorem_diagnostics"]
    cert_applicable = certificate[
        certificate.get(
            "certificate_valid",
            pd.Series(index=certificate.index, dtype=bool),
        ).notna()
    ]
    report = [
        f"# {'Preview' if is_preview else 'Informe'} — {PREVIEW if is_preview else CAMPAIGN}",
        "",
        "## Alcance y lectura correcta",
        "",
        "La campaña evalúa exclusivamente reclutamiento SP1. Las posiciones solo "
        "parametrizan coste de llegada; no se simulan docking, contacto, wrench, "
        "transporte, MPC ni tráfico. `rho` es intención continua y `x` es la "
        "asignación atómica, conforme a la notación canónica del repositorio.",
        "",
        "Los resultados `raw`, `seeded` y `recovered` se conservan por separado. "
        "El LP es una cota/referencia fraccionaria, nunca una ejecución física. "
        "Capacity-CBBA y Weighted-GRAPE son adaptaciones declaradas. GRAPE-S "
        "aparece solo en E10, su dominio discreto de servicios.",
        "",
        "## Resultado descriptivo agregado",
        "",
        summary.to_markdown() if not summary.empty else "Sin filas escalares.",
        "",
        "## Servicios discretos E10",
        "",
        service_summary.to_frame("feasibility_rate").to_markdown()
        if not service_summary.empty
        else "No aplica al preview.",
        "",
        "## Certificados",
        "",
        (
            f"Se verificaron {int(cert_applicable['certificate_valid'].sum())} "
            f"certificados válidos de {len(cert_applicable)} diagnósticos aplicables."
            if not cert_applicable.empty
            else "No hubo diagnósticos aplicables."
        ),
        "",
        "## Censura y límites",
        "",
        "El guard de rondas es censura computacional explícita y nunca se "
        "interpreta como convergencia. Las simulaciones no demuestran estabilidad "
        "global, optimalidad distribuida, transporte físico ni tasa asintótica.",
        "",
        "## Ejecución",
        "",
        f"- Tasks completadas: {runtime['tasks_completed']}/{runtime['tasks_expected']}.",
        f"- Workers: {runtime['workers']}.",
        f"- Wall time del driver: {runtime['wall_time_s']:.3f} s.",
        f"- CPU algorítmica acumulada: {runtime['algorithm_cpu_time_s']:.3f} s.",
        f"- Figuras PNG/PDF: {len(figures)}.",
        "",
        "## Conclusión científica",
        "",
        "La interpretación final se basa en el mapa de regímenes y en pruebas "
        "emparejadas; no se presupone un ganador. Cuando QPG no satisface un gate, "
        "se registra como resultado negativo. La contribución defendible es el "
        "pipeline trazable continuo→semilla→recovery con precios comunes por "
        "mercado local y certificados computables, no una afirmación de "
        "optimalidad entera distribuida general.",
        "",
    ]
    text = "\n".join(report)
    (output_dir / "report.md").write_text(text, encoding="utf-8")
    return text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksums(output_dir: Path) -> None:
    files = [
        path
        for path in output_dir.rglob("*")
        if path.is_file()
        and path.name != "checksums.sha256"
        and "checkpoints" not in path.parts
    ]
    lines = [
        f"{_sha256_file(path)}  {path.relative_to(output_dir).as_posix()}"
        for path in sorted(files)
    ]
    (output_dir / "checksums.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_audit(
    *,
    output_dir: Path,
    config: Mapping[str, Any],
    frames: Mapping[str, pd.DataFrame],
    runtime: Mapping[str, Any],
    expected_tasks: int,
    preview_passed: bool,
    is_preview: bool,
) -> dict[str, Any]:
    runs = frames["all_runs"]
    worlds = frames["worlds"]
    operational = runs[runs["closure"].isin(SCALAR_CLOSURES)]
    exact_worlds = {
        experiment.lower(): int(
            worlds[worlds["experiment"] == experiment]["world_id"].nunique()
        )
        for experiment in [f"E{i}" for i in range(0, 11)]
    }
    expected = config["expected_counts"]
    expected_map = {
        "e0": expected["e0_worlds"],
        "e1": expected["e1_worlds"],
        "e2": expected["e2_worlds"],
        "e3": expected["e3_worlds"],
        "e4": expected["e4_worlds"],
        "e5": expected["e5_worlds"],
        "e6": expected["e6_worlds"],
        "e7": expected["e7_event_worlds"],
        "e8": expected["e8_states"],
        "e9": expected["e9_instances"],
        "e10": expected["e10_worlds"],
    }
    method_completeness = True
    for experiment in ["E1", "E2", "E3", "E4", "E5"]:
        subset = operational[operational["experiment"] == experiment]
        if subset.empty:
            continue
        counts = subset.groupby(["world_id", "closure"])["method"].nunique()
        method_completeness &= bool((counts == len(PRIMARY_METHODS)).all())
    finite_columns = [
        column
        for column in [
            "wall_time_s",
            "logical_rounds",
            "payload_bytes_total",
            "simplex_violation",
        ]
        if column in runs
    ]
    no_inf = all(
        not np.isinf(pd.to_numeric(runs[column], errors="coerce")).any()
        for column in finite_columns
    )
    certificate = frames["theorem_diagnostics"]
    applicable_cert = certificate[
        certificate.get(
            "certificate_valid",
            pd.Series(index=certificate.index, dtype=bool),
        ).notna()
    ]
    message_validation = frames["message_accounting_validation"]
    audit = {
        "campaign": PREVIEW if is_preview else CAMPAIGN,
        "generated_at_utc": pd.Timestamp.utcnow().isoformat(),
        "runtime": runtime,
        "gates": {
            "task_count_exact": runtime["tasks_completed"] == expected_tasks,
            "task_failures_empty": not runtime["task_failures"],
            "preview_passed": preview_passed,
            "world_counts_exact": (
                True
                if is_preview
                else all(exact_worlds[key] == int(value) for key, value in expected_map.items())
            ),
            "all_primary_methods_per_world": method_completeness,
            "same_world_hash_per_world_id": bool(
                worlds.groupby("world_id")["world_hash"].nunique().max() <= 1
            )
            if not worlds.empty
            else False,
            "no_inf": no_inf,
            "simplex_valid": bool(
                (
                    pd.to_numeric(
                        operational.get("simplex_violation", 0),
                        errors="coerce",
                    ).fillna(0)
                    <= 1.0e-8
                ).all()
            ),
            "exclusive_atomic_output": bool(
                operational.get("exclusive", False).fillna(False).all()
            ),
            "certificate_valid_all_applicable": bool(
                applicable_cert["certificate_valid"].astype(bool).all()
            )
            if not applicable_cert.empty
            else True,
            "messages_recomputable": bool(
                message_validation["valid"].all()
            )
            if not message_validation.empty
            else True,
            "calibration_evaluation_seeds_disjoint": set(
                config["calibration"]["seeds"]
            ).isdisjoint(
                set(config["preview"]["seeds"])
                | set(
                    range(
                        int(config["evaluation"]["e1"]["seeds"]["start"]),
                        int(config["evaluation"]["e1"]["seeds"]["start"])
                        + int(config["evaluation"]["e1"]["seeds"]["count"]),
                    )
                )
            ),
            "checkpoint_resume_present": (output_dir / "checkpoints").is_dir(),
            "censoring_explicit": not runs.get(
                "censoring_reason", pd.Series(dtype=object)
            ).isna().any(),
            "git_clean_pending_final_commit": True,
        },
        "observed_world_counts": exact_worlds,
        "expected_world_counts": expected_map,
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "limitations": [
            "Evaluation-round guard is explicit right-censoring.",
            "AugmentingRecovery is bounded and is not complete for arbitrary weighted instances.",
            "N=500 is finite-scale evidence, not an asymptotic proof.",
            "E10 is a separate discrete-service domain.",
            "No physical transport is simulated.",
        ],
    }
    _write_json(output_dir / "audit.json", audit)
    return audit


def _copy_config_snapshot(config_path: Path, output_dir: Path) -> None:
    shutil.copy2(config_path, output_dir / "config_snapshot.yaml")


def _git_metadata(repo: Path) -> dict[str, Any]:
    def call(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo,
            text=True,
            encoding="utf-8",
        ).strip()

    return {
        "commit": call("rev-parse", "HEAD"),
        "branch": call("branch", "--show-current"),
        "status_porcelain": call("status", "--porcelain"),
    }


def execute_campaign(
    *,
    repo: Path,
    config_path: Path,
    mode: str,
    workers: int | None = None,
    force: bool = False,
) -> Path:
    config = load_config(config_path)
    is_preview = mode == "preview"
    if mode not in {"preview", "full"}:
        raise ValueError("mode must be preview or full")
    output_dir = repo / config["output_dirs"]["preview" if is_preview else "full"]
    output_dir.mkdir(parents=True, exist_ok=True)
    _copy_config_snapshot(config_path, output_dir)
    selected_path = (
        repo / config["output_dirs"]["preview"] / "selected_parameters.yaml"
    )
    if not selected_path.exists() or force:
        selected = run_calibration(
            config,
            output_dir,
            workers=workers or int(config["parallel_workers"]),
        )
    else:
        selected = yaml.safe_load(selected_path.read_text(encoding="utf-8"))
        selected_destination = output_dir / "selected_parameters.yaml"
        if selected_path.resolve() != selected_destination.resolve():
            shutil.copy2(selected_path, selected_destination)
        if not is_preview:
            preview_calibration = selected_path.parent / "calibration_runs.csv"
            preview_summary = selected_path.parent / "calibration_summary.csv"
            if preview_calibration.exists():
                shutil.copy2(preview_calibration, output_dir / "calibration_runs.csv")
            if preview_summary.exists():
                shutil.copy2(preview_summary, output_dir / "calibration_summary.csv")
    tasks = build_preview_tasks(config) if is_preview else build_full_tasks(config)
    e0, e0_recovery = run_e0(config, output_dir)
    tables, runtime = run_task_set(
        tasks=tasks,
        config=config,
        parameters=selected,
        output_dir=output_dir,
        stage="preview" if is_preview else "full",
        workers=workers or int(config["parallel_workers"]),
        force=force,
    )
    frames = _write_tables(
        tables,
        output_dir,
        e0,
        e0_recovery,
        config,
    )
    regime = _regime_map(frames["all_runs"])
    regime.to_csv(output_dir / "regime_map.csv", index=False)
    frames["regime_map"] = regime
    figures = generate_figures(
        frames["all_runs"],
        frames["worlds"],
        frames["theorem_diagnostics"],
        frames["recovery_paths"],
        frames["dynamic_events"],
        output_dir,
    )
    statistics = {
        "paired_comparisons": frames["paired_comparisons"].to_dict("records"),
        "methods": frames["aggregated_results"].to_dict("records"),
        "notes": {
            "proportions": "Wilson 95%",
            "paired_binary": "exact McNemar/binomial",
            "continuous": "paired bootstrap, Wilcoxon and rank-biserial",
            "multiplicity": "Holm",
            "survival": "right-censored runs retained; RMST proxy reported in aggregation",
            "robust_regression": "descriptive factorial regime map; no causal claim",
        },
    }
    _write_json(output_dir / "statistics.json", statistics)
    preview_audit_path = (
        repo / config["output_dirs"]["preview"] / "audit.json"
    )
    preview_passed = (
        True
        if is_preview
        else (
            preview_audit_path.exists()
            and all(
                value
                for key, value in json.loads(
                    preview_audit_path.read_text(encoding="utf-8")
                )["gates"].items()
                if key != "git_clean_pending_final_commit"
            )
        )
    )
    audit = build_audit(
        output_dir=output_dir,
        config=config,
        frames=frames,
        runtime=runtime,
        expected_tasks=len(tasks),
        preview_passed=preview_passed,
        is_preview=is_preview,
    )
    manifest = {
        "campaign": PREVIEW if is_preview else CAMPAIGN,
        "schema_version": config["schema_version"],
        "config_sha256": _sha256_file(config_path),
        "selected_parameters_sha256": _sha256_file(
            output_dir / "selected_parameters.yaml"
        ),
        "environment": environment_record(),
        "git": _git_metadata(repo),
        "runtime": runtime,
        "task_manifest_hash": stable_hash(tasks),
        "tasks": len(tasks),
        "figures": figures,
        "audit_passed_precommit": all(
            value
            for key, value in audit["gates"].items()
            if key != "git_clean_pending_final_commit"
        ),
        "grape_s": config["grape_s_source"],
    }
    _write_json(output_dir / "manifest.json", manifest)
    reproduce = f"""# Reproducción de {manifest['campaign']}

Entorno: Python 3.11+, dependencias fijadas en `pyproject.toml`.

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_tfm_final_quota_game_v1 --mode {mode} --workers {manifest['runtime']['workers']} --resume
```

Los shards se guardan en `checkpoints/`. `--resume` reutiliza shards completos;
`--force` los recalcula. Las semillas de calibración y evaluación son disjuntas.
El guard de rondas genera censura explícita; no equivale a convergencia.
"""
    (output_dir / "README_REPRODUCE.md").write_text(
        reproduce,
        encoding="utf-8",
    )
    create_report(
        output_dir=output_dir,
        frames=frames,
        runtime=runtime,
        figures=figures,
        is_preview=is_preview,
    )
    write_checksums(output_dir)
    return output_dir
