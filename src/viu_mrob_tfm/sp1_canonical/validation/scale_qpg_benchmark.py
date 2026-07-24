"""Reproducible SCALE-QPG V2 benchmark and blocking preview."""

from __future__ import annotations

import itertools
import json
import math
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.stats import binomtest, norm, rankdata, wilcoxon

from .campaign_io import (
    git_metadata,
    load_resolved_config,
    sha256_file,
    write_checksums,
    write_json,
    write_parquet_or_empty,
    write_shard,
    write_yaml,
)
from .quota_game_benchmark import _dynamic_pair
from .quota_game_cases import (
    evaluate_service_assignment,
    make_chain_world,
    make_service_world,
    run_grape_s,
    run_service_greedy,
    service_world_hash,
)
from .quota_game_core import (
    AlgorithmResult,
    QuotaWorld,
    environment_record,
    evaluate_assignment,
    make_quota_graph,
    make_quota_world,
    quota_aware_seed,
    recover_assignment,
    run_primary_method,
    solve_milp_repair,
    solve_quota_lp,
    solve_quota_milp,
    stable_hash,
)
from .scale_qpg import (
    SCALE_METHODS,
    all_world_cost,
    nearest_compatible_seed,
    random_seed_assignment,
    run_local_recovery,
    run_scale_qpg,
)


CAMPAIGN = "SP1_SCALE_QPG_BENCHMARK_v2"
PREVIEW = f"{CAMPAIGN}_preview"


def _seed_range(spec: Mapping[str, Any]) -> range:
    return range(int(spec["start"]), int(spec["start"]) + int(spec["count"]))


def _scalar_task(
    experiment: str,
    n: int,
    k: int,
    seed: int,
    spec: Mapping[str, Any],
    *,
    suffix: str = "",
    active_set_override: int | None = None,
) -> dict[str, Any]:
    return {
        "kind": "scalar",
        "experiment": experiment,
        "n": int(n),
        "k": int(k),
        "seed": int(seed),
        "capacity_regime": str(spec["capacity_regime"]),
        "utilization": float(spec["utilization"]),
        "quota_band": str(spec["quota_band"]),
        "compatibility": str(spec.get("compatibility", "arrival_radius")),
        "topology": str(spec.get("topology", "rdisk_degree_8")),
        "suffix": suffix,
        "active_set_override": active_set_override,
    }


def build_preview_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    spec = config["preview"]
    revision = str(spec["protocol_revision"])
    tasks: list[dict[str, Any]] = []
    for n, regime, seed in itertools.product(
        spec["n_values"],
        spec["capacity_regimes"],
        spec["seeds"],
    ):
        task = _scalar_task(
            "PREVIEW",
            int(n),
            int(math.ceil(int(n) / 5)),
            int(seed),
            {
                **spec,
                "capacity_regime": regime,
            },
            suffix=str(regime),
        )
        task["protocol_revision"] = revision
        tasks.append(task)
    dynamic = spec["dynamic"]
    event_map = {"robot_failure": "committed_robot_failure"}
    for event, seed in itertools.product(
        dynamic["events"],
        dynamic["seeds"],
    ):
        task = _scalar_task(
            "PREVIEW-DYNAMIC",
            int(dynamic["n"]),
            int(dynamic["k"]),
            int(seed),
            dynamic,
            suffix=str(event),
        )
        task.update(
            {
                "kind": "dynamic",
                "event": event_map.get(str(event), str(event)),
                "reported_event": str(event),
                "protocol_revision": revision,
            }
        )
        tasks.append(task)
    return tasks


def build_full_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    ev = config["evaluation"]
    tasks: list[dict[str, Any]] = []
    c1 = ev["c1"]
    cursor = int(c1["seed_start"])
    for n in c1["n_values"]:
        count = int(c1["seed_counts"][int(n)])
        for seed in range(cursor, cursor + count):
            tasks.append(
                _scalar_task(
                    "C1",
                    int(n),
                    int(math.ceil(int(n) / 5)),
                    seed,
                    c1,
                )
            )
        cursor += 100
    c2 = ev["c2"]
    for k, active_size, seed in itertools.product(
        c2["k_values"],
        c2["active_set_sizes"],
        _seed_range(c2["seeds"]),
    ):
        tasks.append(
            _scalar_task(
                "C2",
                int(c2["n"]),
                int(k),
                int(seed),
                c2,
                suffix=f"k{k}_L{active_size}",
                active_set_override=int(active_size),
            )
        )
    c3 = ev["c3"]
    cursor = int(c3["seed_start"])
    for n, k in c3["configurations"]:
        count = int(c3["seed_counts"][int(n)])
        seeds = range(cursor, cursor + count)
        for utilization, band, seed in itertools.product(
            c3["utilizations"],
            c3["quota_bands"],
            seeds,
        ):
            spec = {
                **c3,
                "utilization": utilization,
                "quota_band": band,
            }
            tasks.append(
                _scalar_task(
                    "C3",
                    n,
                    k,
                    seed,
                    spec,
                    suffix=f"u{float(utilization):.2f}_{band}",
                )
            )
        cursor += 100
    c4 = ev["c4"]
    for (n, k), utilization, seed in itertools.product(
        c4["configurations"],
        c4["utilizations"],
        _seed_range(c4["seeds"]),
    ):
        spec = {**c4, "utilization": utilization}
        tasks.append(
            _scalar_task(
                "C4",
                n,
                k,
                seed,
                spec,
                suffix=f"u{float(utilization):.2f}",
            )
        )
    c5 = ev["c5"]
    for topology, seed in itertools.product(
        c5["topologies"],
        _seed_range(c5["seeds"]),
    ):
        spec = {**c5, "topology": topology}
        tasks.append(
            _scalar_task(
                "C5",
                c5["n"],
                c5["k"],
                seed,
                spec,
                suffix=str(topology),
            )
        )
    c6 = ev["c6"]
    for event, seed in itertools.product(
        c6["events"],
        _seed_range(c6["seeds"]),
    ):
        event_name = (
            "committed_robot_failure"
            if event == "robot_failure"
            else str(event)
        )
        tasks.append(
            {
                **_scalar_task(
                    "C6",
                    c6["n"],
                    c6["k"],
                    seed,
                    c6,
                    suffix=str(event),
                ),
                "kind": "dynamic",
                "event": event_name,
                "reported_event": str(event),
            }
        )
    c7 = ev["c7"]
    cursor = int(c7["seed_start"])
    for n, k in c7["configurations"]:
        count = int(c7["seed_counts"][int(n)])
        for seed in range(cursor, cursor + count):
            tasks.append(_scalar_task("C7", n, k, seed, c7))
        cursor += 100
    c8 = ev["c8"]
    for length in c8["chain_lengths"]:
        for index in range(int(c8["instances_per_length"])):
            tasks.append(
                {
                    "kind": "chain",
                    "experiment": "C8",
                    "length": int(length),
                    "seed": int(c8["seed_start"])
                    + 100 * int(length)
                    + index,
                    "index": index,
                }
            )
    c9 = ev["c9"]
    for n, services, per_robot, seed in itertools.product(
        c9["n_values"],
        c9["service_types"],
        c9["services_per_robot"],
        _seed_range(c9["seeds"]),
    ):
        tasks.append(
            {
                "kind": "service",
                "experiment": "C9",
                "n": int(n),
                "service_types": int(services),
                "services_per_robot": int(per_robot),
                "task_fraction": float(c9["task_fraction"]),
                "seed": int(seed),
            }
        )
    return tasks


def task_id(task: Mapping[str, Any]) -> str:
    prefix = "_".join(
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
    return f"{prefix}_{stable_hash(task)[:16]}".replace("/", "_")


def _world_from_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[QuotaWorld, Any]:
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


def _world_row(
    world: QuotaWorld,
    graph: Any,
    task: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "experiment": str(task["experiment"]),
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "graph_hash": graph.graph_hash,
        "seed": world.seed,
        "n": world.n_robots,
        "k": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization": world.utilization_target,
        "quota_band": world.quota_band,
        "topology": graph.name,
        "edges": graph.edges,
        "degree_min": graph.degree_min,
        "degree_max": graph.degree_max,
        "degree_mean": graph.degree_mean,
        "diameter": graph.diameter,
        "lambda_2": graph.lambda_2,
        "lambda_max": graph.lambda_max,
        "compatibility_density": float(np.mean(world.compatibility)),
    }


def _recovery_message_bytes(
    world: QuotaWorld,
    graph: Any,
    before: np.ndarray,
    after: np.ndarray,
) -> tuple[int, int]:
    changed = np.flatnonzero(
        np.asarray(before, dtype=int) != np.asarray(after, dtype=int)
    )
    hops = 0
    for robot in changed:
        destination = int(after[robot])
        source = int(before[robot])
        load = destination if destination < world.n_loads else source
        if load < world.n_loads:
            hops += int(graph.market_route_hops[load, robot])
    return int(2 * hops), int(hops * (2 * 8 + 5 * 8))


def _result_row(
    *,
    task: Mapping[str, Any],
    world: QuotaWorld,
    method: str,
    assignment_before: np.ndarray,
    assignment_after: np.ndarray,
    previous_assignment: np.ndarray,
    wall_time_s: float,
    cpu_time_s: float,
    first_atomic_time_s: float | None,
    first_feasible_time_s: float | None,
    first_persistent_time_s: float | None,
    final_termination_time_s: float,
    converged: bool,
    censored: bool,
    censoring_reason: str,
    payload_bytes: int,
    packets: int,
    scalar_transmissions: int,
    recovery: Any,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    before = evaluate_assignment(
        world,
        assignment_before,
        previous_assignment=previous_assignment,
    )
    after = evaluate_assignment(
        world,
        assignment_after,
        previous_assignment=previous_assignment,
    )
    row = {
        "experiment": str(task["experiment"]),
        "domain": "scalar_quotas",
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "method": method,
        "seed": int(task["seed"]),
        "n": world.n_robots,
        "k": world.n_loads,
        "capacity_regime": world.capacity_regime,
        "utilization": world.utilization_target,
        "quota_band": world.quota_band,
        "topology": str(task["topology"]),
        "regime": (
            "target"
            if str(task["experiment"]) in {"C1", "C2", "C3", "C5", "C7"}
            and world.capacity_regime == "high"
            and world.utilization_target >= 0.85
            else "easy"
            if str(task["experiment"]) == "C4"
            else "other"
        ),
        "raw_feasible": bool(before["feasible"]),
        "feasible": bool(after["feasible"]),
        "distance_total_m": float(after["distance_total_m"]),
        "all_world_cost": all_world_cost(world, assignment_after),
        "deficit_total": float(after["deficit_total"]),
        "excess_upper_total": float(after["excess_upper_total"]),
        "overcapacity_total": float(after["overcapacity_total"]),
        "recourse": int(after["recourse_hamming"]),
        "robots_used": int(after["robots_used"]),
        "atomicity_violations": int(
            not bool(after["exclusive"] and after["compatible"])
        ),
        "duplicate_assignment_count": int(after["duplicate_assignment_count"]),
        "assignment_hash": stable_hash(np.asarray(assignment_after, dtype=int)),
        "converged": bool(converged),
        "censored": bool(censored),
        "censoring_reason": str(censoring_reason),
        "wall_time_s": float(wall_time_s),
        "cpu_time_s": float(cpu_time_s),
        "first_atomic_assignment_time_s": first_atomic_time_s,
        "first_feasible_time_s": first_feasible_time_s,
        "first_persistent_feasible_time_s": first_persistent_time_s,
        "final_termination_time_s": float(final_termination_time_s),
        "packets_total": int(packets),
        "scalar_transmissions_total": int(scalar_transmissions),
        "payload_bytes_total": int(payload_bytes),
        "recovery_success": bool(recovery.success),
        "recovery_runtime_s": float(recovery.runtime_s),
        "recovery_robots_reassigned": int(recovery.robots_reassigned),
        "maximum_chain_length": int(recovery.maximum_chain_length),
        "nodes_expanded": int(recovery.nodes_expanded),
        "fallback_global_used": False,
    }
    if extra:
        row.update(extra)
    return row


def _common_baseline(
    world: QuotaWorld,
    graph: Any,
    task: Mapping[str, Any],
    method: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    previous_assignment: np.ndarray,
    initial_assignment: np.ndarray | None = None,
    affected_loads: Sequence[int] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    started = time.perf_counter()
    started_cpu = time.process_time()
    algorithm: AlgorithmResult | None = None
    if method == "RandomSeed-AR":
        seed_assignment = random_seed_assignment(
            world,
            int(task["seed"]) + 500003,
        )
    elif method == "NearestCompatibleSeed-AR":
        seed_assignment = nearest_compatible_seed(world)
    elif method == "LPSeed-AR":
        lp = solve_quota_lp(world)
        seed_assignment = quota_aware_seed(world, lp.rho)
    else:
        algorithm = run_primary_method(
            world,
            graph,
            method,
            config,
            parameters,
            stage=stage,
            seed=int(task["seed"]) + int(stable_hash(method)[:8], 16),
            initial_assignment=initial_assignment,
            initial_rho=(
                None
                if initial_assignment is None
                else np.eye(world.n_loads + 1, dtype=float)[
                    np.asarray(initial_assignment, dtype=int)
                ]
            ),
            previous_assignment=previous_assignment,
        )
        if algorithm.rho is not None:
            seed_assignment = quota_aware_seed(world, algorithm.rho)
        elif algorithm.assignment is not None:
            seed_assignment = np.asarray(algorithm.assignment, dtype=int).copy()
        else:
            raise RuntimeError(f"{method} produced no atomic seed")
    atomic_time = float(time.perf_counter() - started)
    raw = evaluate_assignment(
        world,
        seed_assignment,
        previous_assignment=previous_assignment,
    )
    first_feasible = atomic_time if raw["feasible"] else None
    recovery = recover_assignment(
        world,
        seed_assignment,
        config["recovery"],
        previous_assignment=previous_assignment,
    )
    final_time = float(time.perf_counter() - started)
    if first_feasible is None and recovery.success:
        first_feasible = final_time
    recovery_packets, recovery_bytes = _recovery_message_bytes(
        world,
        graph,
        seed_assignment,
        recovery.assignment,
    )
    algorithm_bytes = algorithm.payload_bytes_total if algorithm else 0
    algorithm_packets = algorithm.packets_total if algorithm else 0
    algorithm_scalars = (
        algorithm.scalar_transmissions_total if algorithm else 0
    )
    changed_robots = np.flatnonzero(recovery.assignment != previous_assignment)
    changed_loads = set()
    for robot in changed_robots:
        for load in (
            int(previous_assignment[robot]),
            int(recovery.assignment[robot]),
        ):
            if load < world.n_loads:
                changed_loads.add(load)
    row = _result_row(
        task=task,
        world=world,
        method=method,
        assignment_before=seed_assignment,
        assignment_after=recovery.assignment,
        previous_assignment=previous_assignment,
        wall_time_s=final_time,
        cpu_time_s=float(time.process_time() - started_cpu),
        first_atomic_time_s=atomic_time,
        first_feasible_time_s=first_feasible,
        first_persistent_time_s=(
            algorithm.first_persistent_feasible_time_s if algorithm else None
        ),
        final_termination_time_s=final_time,
        converged=algorithm.converged if algorithm else True,
        censored=algorithm.censored if algorithm else False,
        censoring_reason=algorithm.censoring_reason if algorithm else "none",
        payload_bytes=int(algorithm_bytes + recovery_bytes),
        packets=int(algorithm_packets + recovery_packets),
        scalar_transmissions=int(algorithm_scalars),
        recovery=recovery,
        extra={
            "logical_rounds": algorithm.logical_rounds if algorithm else 0,
            "accepted_moves": algorithm.accepted_moves if algorithm else 0,
            "maximum_active_set_size": math.nan,
            "mean_active_set_size": math.nan,
            "strict_potential_monotone": None,
            "cycles_detected": None,
            "accepted_version_violations": 0,
            "locality_respected": None,
            "local_universe_robot_fraction": math.nan,
            "local_universe_load_fraction": math.nan,
            "indices_bytes_total": math.nan,
            "versions_bytes_total": math.nan,
            "reservation_bytes_total": math.nan,
            "recovery_bytes_total": recovery_bytes,
            "proposals": math.nan,
            "rejected_proposals": math.nan,
            "rollbacks": math.nan,
            "loads_touched_count": len(changed_loads),
            "robots_touched_count": len(changed_robots),
            "unaffected_coalition_integrity": _unaffected_integrity(
                previous_assignment,
                recovery.assignment,
                n_initial_loads=world.n_loads,
                affected_loads=affected_loads or (),
            ),
        },
    )
    traces = (
        [
            {
                "experiment": task["experiment"],
                "world_id": world.world_id,
                "method": method,
                **trace,
            }
            for trace in algorithm.traces
        ]
        if algorithm
        else []
    )
    messages = (
        [
            {
                "experiment": task["experiment"],
                "world_id": world.world_id,
                "method": method,
                **message,
            }
            for message in algorithm.message_rows
        ]
        if algorithm
        else []
    )
    if recovery_bytes:
        messages.append(
            {
                "experiment": task["experiment"],
                "world_id": world.world_id,
                "method": method,
                "message_kind": "common_augmenting_recovery",
                "packets": recovery_packets,
                "bytes": recovery_bytes,
                "payload_bytes": recovery_bytes,
                "route_hops": recovery_packets // 2,
            }
        )
    return row, traces, messages


def _scale_method(
    world: QuotaWorld,
    graph: Any,
    task: Mapping[str, Any],
    method: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    previous_assignment: np.ndarray,
    initial_assignment: np.ndarray | None,
    affected_loads: Sequence[int] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    result = run_scale_qpg(
        world,
        graph,
        method,
        config,
        parameters,
        stage=stage,
        seed=int(task["seed"]) + int(stable_hash(method)[:8], 16),
        initial_assignment=initial_assignment,
        previous_assignment=previous_assignment,
        affected_loads=affected_loads,
    )
    universe = result.recovery.universe
    changed_robots = np.flatnonzero(result.assignment != previous_assignment)
    changed_loads = set()
    for robot in changed_robots:
        for load in (
            int(previous_assignment[robot]),
            int(result.assignment[robot]),
        ):
            if load < world.n_loads:
                changed_loads.add(load)
    row = _result_row(
        task=task,
        world=world,
        method=method,
        assignment_before=result.assignment_before_recovery,
        assignment_after=result.assignment,
        previous_assignment=previous_assignment,
        wall_time_s=result.wall_time_s,
        cpu_time_s=result.cpu_time_s,
        first_atomic_time_s=result.first_atomic_assignment_time_s,
        first_feasible_time_s=result.first_feasible_time_s,
        first_persistent_time_s=result.first_persistent_feasible_time_s,
        final_termination_time_s=result.final_termination_time_s,
        converged=result.converged,
        censored=result.censored,
        censoring_reason=result.censoring_reason,
        payload_bytes=result.payload_bytes_total,
        packets=result.packets_total,
        scalar_transmissions=result.scalar_transmissions_total,
        recovery=result.recovery.recovery,
        extra={
            "logical_rounds": result.logical_epochs,
            "accepted_moves": result.accepted_moves,
            "maximum_active_set_size": result.maximum_active_set_size,
            "mean_active_set_size": result.mean_active_set_size,
            "strict_potential_monotone": result.strict_potential_monotone,
            "cycles_detected": result.cycles_detected,
            "accepted_version_violations": 0,
            "potential_decreasing_accepted_moves": int(
                sum(
                    delta <= float(parameters["epsilon_improvement"])
                    for delta in result.potential_increments
                )
            ),
            "minimum_accepted_delta_phi": (
                min(result.potential_increments)
                if result.potential_increments
                else math.nan
            ),
            "strict_br_finite_termination": bool(
                result.converged and result.censoring_reason == "none"
            ),
            "version_conflicts_rejected": result.version_conflicts,
            "locality_respected": result.recovery.locality_respected,
            "local_universe_robot_fraction": (
                len(universe.robots) / world.n_robots
                if universe.robots
                else 0.0
            ),
            "local_universe_load_fraction": (
                len(universe.loads) / world.n_loads if universe.loads else 0.0
            ),
            "indices_bytes_total": result.indices_bytes_total,
            "versions_bytes_total": result.versions_bytes_total,
            "reservation_bytes_total": result.reservation_bytes_total,
            "recovery_bytes_total": result.recovery_bytes_total,
            "proposals": result.proposals,
            "rejected_proposals": result.rejected_proposals,
            "rollbacks": result.rollbacks,
            "fallback_global_used": result.recovery.fallback_used,
            "message_accounting_recomputable": (
                result.payload_bytes_total
                == sum(
                    int(message["payload_bytes"])
                    for message in result.message_rows
                )
            ),
            "loads_touched_count": len(changed_loads),
            "robots_touched_count": len(changed_robots),
            "unaffected_coalition_integrity": _unaffected_integrity(
                previous_assignment,
                result.assignment,
                n_initial_loads=world.n_loads,
                affected_loads=affected_loads or (),
            ),
        },
    )
    traces = [
        {
            "experiment": task["experiment"],
            "world_id": world.world_id,
            "method": method,
            **trace,
        }
        for trace in result.traces
    ]
    messages = [
        {
            "experiment": task["experiment"],
            "world_id": world.world_id,
            "method": method,
            **message,
        }
        for message in result.message_rows
    ]
    return row, traces, messages


def _oracle_rows(
    world: QuotaWorld,
    task: Mapping[str, Any],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    lp = solve_quota_lp(world)
    rows.append(
        {
            "experiment": str(task["experiment"]),
            "domain": "scalar_quotas",
            "world_id": world.world_id,
            "world_hash": world.world_hash,
            "method": "LP-oracle",
            "seed": int(task["seed"]),
            "n": world.n_robots,
            "k": world.n_loads,
            "capacity_regime": world.capacity_regime,
            "utilization": world.utilization_target,
            "quota_band": world.quota_band,
            "topology": str(task["topology"]),
            "regime": "oracle",
            "feasible": bool(lp.feasible),
            "optimal": bool(lp.optimal),
            "solver_status": lp.status,
            "distance_total_m": float(lp.objective_m),
            "lower_bound_m": float(lp.lower_bound_m),
            "all_world_cost": math.nan,
            "censored": not bool(lp.optimal),
            "censoring_reason": "none" if lp.optimal else lp.status,
            "wall_time_s": lp.wall_time_s,
            "cpu_time_s": lp.cpu_time_s,
            "payload_bytes_total": 0,
            "atomicity_violations": math.nan,
        }
    )
    if world.n_robots <= int(config["oracles"]["milp_max_n"]):
        milp = solve_quota_milp(
            world,
            time_limit_s=float(config["oracles"]["milp_timeout_s"]),
        )
        rows.append(
            {
                "experiment": str(task["experiment"]),
                "domain": "scalar_quotas",
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "method": "MILP-oracle",
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_loads,
                "capacity_regime": world.capacity_regime,
                "utilization": world.utilization_target,
                "quota_band": world.quota_band,
                "topology": str(task["topology"]),
                "regime": "oracle",
                "feasible": bool(milp.feasible),
                "optimal": bool(milp.optimal),
                "solver_status": milp.status,
                "distance_total_m": float(milp.objective_m),
                "lower_bound_m": float(milp.lower_bound_m),
                "all_world_cost": (
                    all_world_cost(world, milp.assignment)
                    if milp.assignment is not None
                    else math.nan
                ),
                "censored": not bool(milp.optimal),
                "censoring_reason": "none" if milp.optimal else milp.status,
                "wall_time_s": milp.wall_time_s,
                "cpu_time_s": milp.cpu_time_s,
                "payload_bytes_total": 0,
                "atomicity_violations": 0
                if milp.assignment is not None
                else math.nan,
            }
        )
    return rows


def _run_methods_on_world(
    *,
    world: QuotaWorld,
    graph: Any,
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    stage: str,
    previous_assignment: np.ndarray,
    initial_assignment: np.ndarray | None,
    affected_loads: Sequence[int] | None,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    for method in config["methods"]["scalar"]:
        if method in SCALE_METHODS:
            row, method_traces, method_messages = _scale_method(
                world,
                graph,
                task,
                str(method),
                config,
                parameters,
                stage=stage,
                previous_assignment=previous_assignment,
                initial_assignment=initial_assignment,
                affected_loads=affected_loads,
            )
        else:
            row, method_traces, method_messages = _common_baseline(
                world,
                graph,
                task,
                str(method),
                config,
                parameters,
                stage=stage,
                previous_assignment=previous_assignment,
                initial_assignment=initial_assignment,
                affected_loads=affected_loads,
            )
        rows.append(row)
        traces.extend(method_traces)
        messages.extend(method_messages)
    rows.extend(_oracle_rows(world, task, config))
    return rows, traces, messages


def run_scalar_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    world, graph = _world_from_task(task, config)
    effective = dict(parameters)
    if task.get("active_set_override") is not None:
        effective["L"] = int(task["active_set_override"])
    previous = np.full(world.n_robots, world.idle_index, dtype=int)
    rows, traces, messages = _run_methods_on_world(
        world=world,
        graph=graph,
        task=task,
        config=config,
        parameters=effective,
        stage=stage,
        previous_assignment=previous,
        initial_assignment=None,
        affected_loads=None,
    )
    return {
        "runs": rows,
        "traces": traces,
        "messages": messages,
        "worlds": [_world_row(world, graph, task)],
        "dynamic": [],
        "chains": [],
        "services": [],
    }


def _unaffected_integrity(
    before: np.ndarray,
    after: np.ndarray,
    *,
    n_initial_loads: int,
    affected_loads: Sequence[int],
) -> float:
    loads = set(map(int, before[before < int(n_initial_loads)]))
    loads -= set(map(int, affected_loads))
    if not loads:
        return 1.0
    unchanged = 0
    for load in loads:
        before_members = set(map(int, np.flatnonzero(before == load)))
        after_members = set(map(int, np.flatnonzero(after == load)))
        unchanged += int(before_members == after_members)
    return unchanged / len(loads)


def run_dynamic_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    initial_world, world, graph, commitment, detail = _dynamic_pair(task, config)
    previous = commitment.copy()
    warm = commitment.copy()
    affected_loads: list[int] = []
    if detail.get("affected_load") is not None:
        affected_loads.append(int(detail["affected_load"]))
    if detail.get("affected_robot") is not None:
        robot = int(detail["affected_robot"])
        old_load = int(previous[robot])
        if old_load < world.n_loads:
            affected_loads.append(old_load)
        if task["reported_event"] == "robot_failure":
            warm[robot] = world.idle_index
    if not evaluate_assignment(initial_world, previous)["feasible"]:
        raise RuntimeError("C6 event lacks an integer-feasible pre-event state")
    rows, traces, messages = _run_methods_on_world(
        world=world,
        graph=graph,
        task=task,
        config=config,
        parameters=parameters,
        stage=stage,
        previous_assignment=previous,
        initial_assignment=warm,
        affected_loads=affected_loads,
    )
    dynamic_rows = []
    for row in rows:
        if row["method"] in {"LP-oracle", "MILP-oracle"}:
            continue
        assignment_hash = row.get("assignment_hash")
        # Membership sets are not persisted; integrity is recomputed inside a
        # deterministic rerun only for the operational methods below.
        dynamic_rows.append(
            {
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "method": row["method"],
                "event": task["reported_event"],
                "pre_event_integer_feasible": True,
                "post_event_feasible": row["feasible"],
                "time_to_feasibility_s": row["first_feasible_time_s"],
                "recourse": row["recourse"],
                "loads_touched": row.get("loads_touched_count", 0),
                "robots_touched": row.get("robots_touched_count", 0),
                "unaffected_coalition_integrity": row[
                    "unaffected_coalition_integrity"
                ],
                "distance_after_m": row["distance_total_m"],
                "bytes": row["payload_bytes_total"],
                "fallback_global_used": row.get("fallback_global_used", False),
                "locality_respected": row.get("locality_respected"),
                "assignment_hash": assignment_hash,
                "affected_load_count": len(set(affected_loads)),
            }
        )
    return {
        "runs": rows,
        "traces": traces,
        "messages": messages,
        "worlds": [_world_row(world, graph, task)],
        "dynamic": dynamic_rows,
        "chains": [],
        "services": [],
    }


def run_chain_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
) -> dict[str, Any]:
    world, initial = make_chain_world(
        int(task["length"]),
        adversarial=True,
        seed=int(task["seed"]),
    )
    active_sets = [
        tuple(
            list(map(int, np.flatnonzero(world.compatibility[robot])))
            + [world.idle_index]
        )
        for robot in range(world.n_robots)
    ]
    rows = []
    for method in config["evaluation"]["c8"]["methods"]:
        owned = not tracemalloc.is_tracing()
        if owned:
            tracemalloc.start()
        baseline = (
            tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
        )
        started = time.perf_counter()
        if method == "milp_repair":
            recovery = solve_milp_repair(
                world,
                initial,
                time_limit_s=float(config["oracles"]["milp_timeout_s"]),
            )
            success = recovery.success
            failure_reason = recovery.failure_reason
            assignment = recovery.assignment
            nodes = recovery.nodes_expanded
            maximum_chain = math.nan
            local_fraction = 1.0
        elif method in {"local_augmenting", "global_augmenting"}:
            local = run_local_recovery(
                world,
                initial,
                active_sets,
                config["scale"]["local_recovery"],
                affected_loads=[0],
                radius=int(parameters["h"]),
                maximum_chain_length=(
                    int(parameters["H"])
                    if method == "local_augmenting"
                    else 20
                ),
                previous_assignment=initial,
                global_scope=method == "global_augmenting",
            )
            recovery = local.recovery
            success = recovery.success
            failure_reason = recovery.failure_reason
            assignment = recovery.assignment
            nodes = recovery.nodes_expanded
            maximum_chain = recovery.maximum_chain_length
            local_fraction = len(local.universe.robots) / world.n_robots
        else:
            options = dict(config["scale"]["local_recovery"])
            limit = 1 if method == "greedy" else 2
            recovery = recover_assignment(
                world,
                initial,
                options,
                max_chain_length_override=limit,
            )
            success = recovery.success
            failure_reason = recovery.failure_reason
            assignment = recovery.assignment
            nodes = recovery.nodes_expanded
            maximum_chain = recovery.maximum_chain_length
            local_fraction = 1.0
        elapsed = float(time.perf_counter() - started)
        peak = (
            tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
        )
        if owned:
            tracemalloc.stop()
        metrics = evaluate_assignment(world, assignment)
        rows.append(
            {
                "experiment": "C8",
                "world_id": f"c8_l{task['length']}_s{task['seed']}",
                "seed": int(task["seed"]),
                "required_chain_length": int(task["length"]),
                "repair_method": str(method),
                "success": bool(success and metrics["feasible"]),
                "failure_reason": str(failure_reason),
                "runtime_s": elapsed,
                "nodes_expanded": int(nodes),
                "peak_memory_mb": float(
                    max(0, peak - baseline) / (1024.0**2)
                ),
                "robots_reassigned": int(recovery.robots_reassigned),
                "maximum_chain_length": maximum_chain,
                "local_universe_robot_fraction": local_fraction,
            }
        )
    return {
        "runs": [],
        "traces": [],
        "messages": [],
        "worlds": [],
        "dynamic": [],
        "chains": rows,
        "services": [],
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
    rows = []
    for method in config["methods"]["services"]:
        if method in {"GRAPE-S", "Pair-GRAPE-S"}:
            result = run_grape_s(
                world,
                pairwise=method == "Pair-GRAPE-S",
                seed=int(task["seed"]),
            )
        else:
            result = run_service_greedy(
                world,
                method=str(method),
                seed=int(task["seed"]),
            )
        metrics = evaluate_service_assignment(
            world,
            result.tasks,
            result.services,
        )
        rows.append(
            {
                "experiment": "C9",
                "domain": "discrete_services",
                "world_id": world.world_id,
                "world_hash": service_world_hash(world),
                "method": str(method),
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_tasks,
                "service_types": world.n_services,
                "services_per_robot": int(task["services_per_robot"]),
                "feasible": bool(metrics["feasible"]),
                "deficit_total": int(metrics["deficit"]),
                "excess_upper_total": int(metrics["excess"]),
                "logical_rounds": result.logical_rounds,
                "accepted_moves": result.unilateral_moves,
                "swaps": result.swaps,
                "packets_total": result.packets,
                "payload_bytes_total": result.bytes_total,
                "converged": result.converged,
                "deviation": result.deviation,
            }
        )
    return {
        "runs": rows,
        "traces": [],
        "messages": [],
        "worlds": [
            {
                "experiment": "C9",
                "domain": "discrete_services",
                "world_id": world.world_id,
                "world_hash": service_world_hash(world),
                "seed": world.seed,
                "n": world.n_robots,
                "k": world.n_tasks,
                "service_types": world.n_services,
                "services_per_robot": int(task["services_per_robot"]),
            }
        ],
        "dynamic": [],
        "chains": [],
        "services": rows,
    }


def run_task(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
) -> dict[str, Any]:
    if task["kind"] == "scalar":
        return run_scalar_task(task, config, parameters, stage=stage)
    if task["kind"] == "dynamic":
        return run_dynamic_task(task, config, parameters, stage=stage)
    if task["kind"] == "chain":
        return run_chain_task(task, config, parameters)
    if task["kind"] == "service":
        return run_service_task(task, config)
    raise ValueError(f"unknown task kind: {task['kind']}")


def _task_worker(
    task: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    stage: str,
    shard_path: str,
) -> str:
    payload = run_task(task, config, parameters, stage=stage)
    payload["task"] = dict(task)
    write_shard(Path(shard_path), payload)
    return shard_path


def run_task_set(
    *,
    tasks: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    output_dir: Path,
    stage: str,
    workers: int,
    force: bool,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    checkpoint = output_dir / "checkpoints" / "tasks"
    shards, pending = [], []
    for task in tasks:
        path = checkpoint / f"{task_id(task)}.json"
        shards.append(path)
        if force or not path.exists():
            pending.append((task, path))
    started = time.perf_counter()
    failures = []
    if pending:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            future_map = {
                pool.submit(
                    _task_worker,
                    task,
                    config,
                    parameters,
                    stage,
                    str(path),
                ): task
                for task, path in pending
            }
            for future in as_completed(future_map):
                try:
                    future.result()
                except Exception as error:
                    failures.append(
                        {
                            "task": dict(future_map[future]),
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
    if failures:
        raise RuntimeError(f"task failures: {failures[:5]}")
    buckets = {
        "runs": [],
        "traces": [],
        "messages": [],
        "worlds": [],
        "dynamic": [],
        "chains": [],
        "services": [],
    }
    for path in shards:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in buckets:
            buckets[key].extend(payload.get(key, []))
    frames = {key: pd.DataFrame(value) for key, value in buckets.items()}
    runtime = {
        "wall_time_s": float(time.perf_counter() - started),
        "workers": int(workers),
        "tasks_expected": len(tasks),
        "tasks_completed": len(shards),
        "tasks_reused": len(tasks) - len(pending),
        "tasks_executed": len(pending),
        "task_failures": failures,
    }
    return frames, runtime


def _calibration_worker(
    seed: int,
    profile_name: str,
    profile: Mapping[str, Any],
    config: Mapping[str, Any],
    shard_path: str,
) -> str:
    configurations = config["calibration"]["configurations"]
    n, k = configurations[int(seed) % len(configurations)]
    task = _scalar_task(
        "CALIBRATION",
        int(n),
        int(k),
        int(seed),
        config["calibration"],
        suffix=profile_name,
    )
    world, graph = _world_from_task(task, config)
    previous = np.full(world.n_robots, world.idle_index, dtype=int)
    result = run_scale_qpg(
        world,
        graph,
        "SCALE-QPG-LogitBR-LocalAR",
        config,
        profile,
        stage="calibration",
        seed=int(seed) + int(stable_hash(profile_name)[:8], 16),
        previous_assignment=previous,
    )
    metrics = evaluate_assignment(
        world,
        result.assignment,
        previous_assignment=previous,
    )
    row = {
        "profile": profile_name,
        "world_id": world.world_id,
        "seed": int(seed),
        "n": int(n),
        "k": int(k),
        "feasible": bool(metrics["feasible"]),
        "all_world_cost": all_world_cost(world, result.assignment),
        "recourse": int(metrics["recourse_hamming"]),
        "distance_m": float(metrics["distance_total_m"]),
        "payload_bytes": result.payload_bytes_total,
        "wall_time_s": result.wall_time_s,
    }
    write_shard(Path(shard_path), {"row": row})
    return shard_path


def run_calibration(
    config: Mapping[str, Any],
    output_dir: Path,
    *,
    workers: int,
    force: bool,
) -> dict[str, Any]:
    checkpoint = output_dir / "checkpoints" / "calibration"
    shards, pending = [], []
    for profile_name, profile in config["calibration"]["candidate_profiles"].items():
        for seed in config["calibration"]["seeds"]:
            key = {"profile": profile_name, "seed": int(seed)}
            path = checkpoint / f"{stable_hash(key)}.json"
            shards.append(path)
            if force or not path.exists():
                pending.append((int(seed), str(profile_name), profile, path))
    if pending:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            futures = [
                pool.submit(
                    _calibration_worker,
                    seed,
                    name,
                    profile,
                    config,
                    str(path),
                )
                for seed, name, profile, path in pending
            ]
            for future in as_completed(futures):
                future.result()
    frame = pd.DataFrame(
        [
            json.loads(path.read_text(encoding="utf-8"))["row"]
            for path in shards
        ]
    )
    frame.to_csv(output_dir / "calibration_runs.csv", index=False)
    summary = (
        frame.groupby("profile")
        .agg(
            feasibility=("feasible", "mean"),
            all_world_cost=("all_world_cost", "median"),
            recourse=("recourse", "median"),
            distance=("distance_m", "median"),
            bytes=("payload_bytes", "median"),
            time=("wall_time_s", "median"),
        )
        .reset_index()
        .sort_values(
            [
                "feasibility",
                "all_world_cost",
                "recourse",
                "distance",
                "bytes",
                "time",
            ],
            ascending=[False, True, True, True, True, True],
            kind="mergesort",
        )
    )
    summary.to_csv(output_dir / "calibration_summary.csv", index=False)
    selected_name = str(summary.iloc[0]["profile"])
    selected = {
        "profile": selected_name,
        **dict(config["calibration"]["candidate_profiles"][selected_name]),
        "selection_rule": list(config["calibration"]["objective_order"]),
        "calibration_seeds": list(config["calibration"]["seeds"]),
    }
    write_yaml(output_dir / "selected_parameters.yaml", selected)
    return selected


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1.0 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    half = (
        z
        * math.sqrt(p * (1.0 - p) / total + z**2 / (4 * total**2))
        / denominator
    )
    return center - half, center + half


def aggregate_results(runs: pd.DataFrame) -> pd.DataFrame:
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ].copy()
    rows = []
    for (experiment, method), group in operational.groupby(
        ["experiment", "method"]
    ):
        successes = int(group["feasible"].astype(bool).sum())
        lower, upper = _wilson(successes, len(group))
        feasible = group[group["feasible"].astype(bool)]
        rows.append(
            {
                "experiment": experiment,
                "method": method,
                "worlds": len(group),
                "feasibility": successes / len(group),
                "feasibility_ci_lower": lower,
                "feasibility_ci_upper": upper,
                "median_all_world_cost": float(
                    group["all_world_cost"].median()
                ),
                "median_common_candidate_distance_m": float(
                    feasible["distance_total_m"].median()
                )
                if len(feasible)
                else math.nan,
                "median_payload_bytes": float(
                    group["payload_bytes_total"].median()
                ),
                "median_time_to_first_feasible_s": float(
                    group["first_feasible_time_s"].median()
                ),
                "median_wall_time_s": float(group["wall_time_s"].median()),
                "censoring_rate": float(group["censored"].fillna(False).mean()),
            }
        )
    return pd.DataFrame(rows)


def _rank_biserial(differences: np.ndarray) -> float:
    differences = np.asarray(differences, dtype=float)
    differences = differences[np.isfinite(differences) & (differences != 0.0)]
    if differences.size == 0:
        return 0.0
    ranks = rankdata(np.abs(differences))
    positive = float(np.sum(ranks[differences > 0]))
    negative = float(np.sum(ranks[differences < 0]))
    return (positive - negative) / max(positive + negative, 1.0)


def _paired_bootstrap(
    differences: np.ndarray,
    *,
    resamples: int,
    seed: int,
) -> tuple[float, float]:
    values = np.asarray(differences, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(int(seed))
    medians = np.empty(int(resamples), dtype=float)
    for index in range(int(resamples)):
        medians[index] = float(
            np.median(rng.choice(values, size=values.size, replace=True))
        )
    return (
        float(np.quantile(medians, 0.025)),
        float(np.quantile(medians, 0.975)),
    )


def _holm_adjust(p_values: Sequence[float]) -> list[float]:
    values = np.asarray(p_values, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    finite = np.flatnonzero(np.isfinite(values))
    if not finite.size:
        return result.tolist()
    ordered = finite[np.argsort(values[finite])]
    running = 0.0
    m = len(ordered)
    for rank, index in enumerate(ordered):
        adjusted = min(1.0, (m - rank) * values[index])
        running = max(running, adjusted)
        result[index] = running
    return result.tolist()


def paired_comparisons(
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    is_preview = bool(runs["experiment"].eq("PREVIEW").any())
    primaries = (
        list(SCALE_METHODS)
        if is_preview
        else ["SCALE-QPG-LogitBR-LocalAR"]
    )
    baselines = (
        list(config["win_gates"]["distributed_baselines"])
        if is_preview
        else ["Capacity-CBBA", "Weighted-Pair-GRAPE"]
    )
    target_experiment = "PREVIEW" if is_preview else "C3"
    target = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & (runs["experiment"] == target_experiment)
        & runs["method"].isin([*primaries, *baselines])
    ].copy()
    rows = []
    metrics = [
        ("all_world_cost", False),
        ("distance_total_m", True),
        ("payload_bytes_total", False),
        ("first_feasible_time_s", False),
    ]
    resamples = int(config["statistics"]["bootstrap_resamples"])
    analysis_seed = int(config["statistics"]["analysis_seed"])
    for primary in primaries:
        for baseline in baselines:
            for metric, common_feasible in metrics:
                left = target[target["method"] == primary][
                    ["world_id", metric, "feasible"]
                ].rename(
                    columns={metric: "left", "feasible": "left_feasible"}
                )
                right = target[target["method"] == baseline][
                    ["world_id", metric, "feasible"]
                ].rename(
                    columns={metric: "right", "feasible": "right_feasible"}
                )
                paired = left.merge(right, on="world_id", how="inner")
                if common_feasible:
                    paired = paired[
                        paired["left_feasible"].astype(bool)
                        & paired["right_feasible"].astype(bool)
                    ]
                paired = paired.dropna(subset=["left", "right"])
                differences = (
                    paired["left"].to_numpy(float)
                    - paired["right"].to_numpy(float)
                )
                if differences.size and np.any(differences != 0.0):
                    p_value = float(
                        wilcoxon(differences, zero_method="wilcox").pvalue
                    )
                else:
                    p_value = 1.0
                lower, upper = _paired_bootstrap(
                    differences,
                    resamples=resamples,
                    seed=analysis_seed
                    + int(
                        stable_hash((primary, baseline, metric))[:8],
                        16,
                    ),
                )
                rows.append(
                    {
                        "comparison": f"{primary} vs {baseline}",
                        "metric": metric,
                        "common_feasible_only": common_feasible,
                        "pairs": len(paired),
                        "median_paired_difference": float(
                            np.median(differences)
                        )
                        if differences.size
                        else math.nan,
                        "bootstrap_ci_lower": lower,
                        "bootstrap_ci_upper": upper,
                        "p_raw": p_value,
                        "rank_biserial": _rank_biserial(differences),
                    }
                )
            left_feasible = target[target["method"] == primary][
                ["world_id", "feasible"]
            ].rename(columns={"feasible": "left"})
            right_feasible = target[target["method"] == baseline][
                ["world_id", "feasible"]
            ].rename(columns={"feasible": "right"})
            binary = left_feasible.merge(right_feasible, on="world_id")
            discordant_left = int(
                (
                    binary["left"].astype(bool)
                    & ~binary["right"].astype(bool)
                ).sum()
            )
            discordant_right = int(
                (
                    ~binary["left"].astype(bool)
                    & binary["right"].astype(bool)
                ).sum()
            )
            discordant = discordant_left + discordant_right
            p_value = (
                float(
                    binomtest(
                        min(discordant_left, discordant_right),
                        discordant,
                        0.5,
                        alternative="two-sided",
                    ).pvalue
                )
                if discordant
                else 1.0
            )
            rows.append(
                {
                    "comparison": f"{primary} vs {baseline}",
                    "metric": "feasibility",
                    "common_feasible_only": False,
                    "pairs": len(binary),
                    "median_paired_difference": float(
                        binary["left"].astype(float).mean()
                        - binary["right"].astype(float).mean()
                    ),
                    "bootstrap_ci_lower": math.nan,
                    "bootstrap_ci_upper": math.nan,
                    "p_raw": p_value,
                    "rank_biserial": math.nan,
                }
            )
    if not dynamic.empty:
        subset = dynamic[
            dynamic["method"].isin([*primaries, *baselines])
        ]
        for primary in primaries:
            for baseline in baselines:
                left = subset[subset["method"] == primary][
                    ["world_id", "recourse"]
                ].rename(columns={"recourse": "left"})
                right = subset[subset["method"] == baseline][
                    ["world_id", "recourse"]
                ].rename(columns={"recourse": "right"})
                paired = left.merge(right, on="world_id").dropna()
                differences = paired["left"].to_numpy(float) - paired[
                    "right"
                ].to_numpy(float)
                p_value = (
                    float(wilcoxon(differences).pvalue)
                    if differences.size and np.any(differences != 0)
                    else 1.0
                )
                lower, upper = _paired_bootstrap(
                    differences,
                    resamples=resamples,
                    seed=analysis_seed
                    + int(
                        stable_hash((primary, baseline, "recourse"))[:8],
                        16,
                    ),
                )
                rows.append(
                    {
                        "comparison": f"{primary} vs {baseline}",
                        "metric": "dynamic_recourse",
                        "common_feasible_only": False,
                        "pairs": len(paired),
                        "median_paired_difference": float(
                            np.median(differences)
                        )
                        if differences.size
                        else math.nan,
                        "bootstrap_ci_lower": lower,
                        "bootstrap_ci_upper": upper,
                        "p_raw": p_value,
                        "rank_biserial": _rank_biserial(differences),
                    }
                )
    frame = pd.DataFrame(rows)
    frame["p_holm"] = _holm_adjust(frame["p_raw"].to_numpy(float))
    return frame


def _km_rmst(
    durations: np.ndarray,
    events: np.ndarray,
    tau: float,
) -> float:
    order = np.argsort(durations)
    times = durations[order]
    observed = events[order]
    survival = 1.0
    previous = 0.0
    area = 0.0
    for current in np.unique(times[times <= tau]):
        area += survival * (float(current) - previous)
        at_risk = int(np.sum(times >= current))
        deaths = int(np.sum((times == current) & observed))
        if at_risk:
            survival *= 1.0 - deaths / at_risk
        previous = float(current)
    area += survival * max(0.0, float(tau) - previous)
    return float(area)


def survival_summary(runs: pd.DataFrame) -> pd.DataFrame:
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ].copy()
    rows = []
    for method, group in operational.groupby("method"):
        durations = group["final_termination_time_s"].fillna(
            group["wall_time_s"]
        ).to_numpy(float)
        events = group["first_feasible_time_s"].notna().to_numpy(bool)
        observed_duration = group["first_feasible_time_s"].fillna(
            group["final_termination_time_s"]
        ).to_numpy(float)
        tau = float(np.max(durations)) if durations.size else 0.0
        bytes_values = group["payload_bytes_total"].to_numpy(float)
        bytes_events = group["feasible"].fillna(False).to_numpy(bool)
        bytes_tau = float(np.max(bytes_values)) if bytes_values.size else 0.0
        rows.append(
            {
                "method": method,
                "runs": len(group),
                "tau_time_s": tau,
                "rmst_time_to_feasible_s": _km_rmst(
                    observed_duration,
                    events,
                    tau,
                ),
                "tau_bytes": bytes_tau,
                "restricted_mean_bytes": _km_rmst(
                    bytes_values,
                    bytes_events,
                    bytes_tau,
                ),
            }
        )
    return pd.DataFrame(rows)


def _message_validation(
    runs: pd.DataFrame,
    messages: pd.DataFrame,
) -> pd.DataFrame:
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"]),
        ["world_id", "method", "payload_bytes_total"],
    ].copy()
    if messages.empty:
        message_sum = pd.DataFrame(
            columns=["world_id", "method", "recomputed_payload_bytes"]
        )
    else:
        data = messages.copy()
        if "payload_bytes" not in data:
            data["payload_bytes"] = np.nan
        if "bytes" not in data:
            data["bytes"] = np.nan
        data["effective_bytes"] = data["payload_bytes"].fillna(data["bytes"]).fillna(0)
        message_sum = (
            data.groupby(["world_id", "method"])["effective_bytes"]
            .sum()
            .reset_index(name="recomputed_payload_bytes")
        )
    validation = operational.merge(
        message_sum,
        on=["world_id", "method"],
        how="left",
    )
    validation["recomputed_payload_bytes"] = validation[
        "recomputed_payload_bytes"
    ].fillna(0)
    validation["difference"] = (
        validation["payload_bytes_total"]
        - validation["recomputed_payload_bytes"]
    )
    validation["valid"] = validation["difference"].abs() <= 1.0e-9
    return validation


def _regime_map(runs: pd.DataFrame) -> pd.DataFrame:
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ]
    if operational.empty:
        return pd.DataFrame()
    return (
        operational.groupby(
            [
                "experiment",
                "regime",
                "n",
                "k",
                "capacity_regime",
                "utilization",
                "quota_band",
                "topology",
            ],
            dropna=False,
        )
        .agg(worlds=("world_id", "nunique"), runs=("method", "size"))
        .reset_index()
    )


def _win_gates(
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    comparisons: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    primary = "SCALE-QPG-LogitBR-LocalAR"
    baselines = ["Capacity-CBBA", "Weighted-Pair-GRAPE"]
    target = runs.loc[
        (runs["experiment"] == "C3")
        & runs["method"].isin([primary, *baselines])
    ]
    scale = target[target["method"] == primary]
    pivot_feasible = target.pivot_table(
        index="world_id",
        columns="method",
        values="feasible",
        aggfunc="first",
    ).dropna()
    common_ids = pivot_feasible.index[pivot_feasible.astype(bool).all(axis=1)]
    common = target[target["world_id"].isin(common_ids)]

    def median(method: str, metric: str, frame: pd.DataFrame = target) -> float:
        values = frame.loc[frame["method"] == method, metric].dropna()
        return float(values.median()) if len(values) else math.inf

    best_distance = min(median(method, "distance_total_m", common) for method in baselines)
    scale_distance = median(primary, "distance_total_m", common)
    best_all_world = min(median(method, "all_world_cost") for method in baselines)
    scale_all_world = median(primary, "all_world_cost")
    best_bytes = min(median(method, "payload_bytes_total") for method in baselines)
    scale_bytes = median(primary, "payload_bytes_total")
    best_time = min(
        median(method, "first_feasible_time_s") for method in baselines
    )
    scale_time = median(primary, "first_feasible_time_s")
    dynamic_subset = dynamic[dynamic["method"].isin([primary, *baselines])]
    scale_recourse = float(
        dynamic_subset.loc[
            dynamic_subset["method"] == primary,
            "recourse",
        ].median()
    ) if not dynamic_subset.empty else math.inf
    best_recourse = min(
        float(
            dynamic_subset.loc[
                dynamic_subset["method"] == method,
                "recourse",
            ].median()
        )
        for method in baselines
    ) if not dynamic_subset.empty else math.inf
    integrity = float(
        dynamic_subset.loc[
            dynamic_subset["method"] == primary,
            "unaffected_coalition_integrity",
        ].median()
    ) if not dynamic_subset.empty else 0.0
    fallback_rate = float(scale["fallback_global_used"].fillna(False).mean())
    atomicity = int(scale["atomicity_violations"].fillna(0).sum())
    significant = comparisons.loc[
        (comparisons["metric"] == "all_world_cost")
        & comparisons["comparison"].str.startswith(primary),
    ]
    significant_advantage = bool(
        len(significant) == len(baselines)
        and (significant["p_holm"] < 0.05).all()
        and (significant["median_paired_difference"] < 0.0).all()
    )
    thresholds = config["win_gates"]
    observed = {
        "recovered_feasibility": float(scale["feasible"].mean()),
        "distance_ratio_to_best_baseline": scale_distance
        / max(best_distance, 1.0e-12),
        "all_world_cost_ratio_to_best_baseline": scale_all_world
        / max(best_all_world, 1.0e-12),
        "bytes_ratio_to_best_baseline": scale_bytes
        / max(best_bytes, 1.0e-12),
        "time_to_first_feasible_ratio": scale_time
        / max(best_time, 1.0e-12),
        "recourse_ratio_to_best_dynamic_baseline": scale_recourse
        / max(best_recourse, 1.0e-12),
        "unaffected_coalition_integrity": integrity,
        "global_fallback_rate": fallback_rate,
        "atomicity_violations": atomicity,
        "holm_significant_advantage": significant_advantage,
        "common_feasible_worlds": len(common_ids),
    }
    passed = {
        "recovered_feasibility": observed["recovered_feasibility"]
        >= float(thresholds["recovered_feasibility_min"]),
        "common_feasible_distance": observed[
            "distance_ratio_to_best_baseline"
        ]
        <= float(thresholds["distance_ratio_to_best_baseline_max"]),
        "all_world_cost": observed["all_world_cost_ratio_to_best_baseline"]
        <= float(thresholds["all_world_cost_ratio_to_best_baseline_max"]),
        "payload_bytes": observed["bytes_ratio_to_best_baseline"]
        <= float(thresholds["bytes_ratio_to_best_baseline_max"]),
        "time_to_first_feasible": observed["time_to_first_feasible_ratio"]
        <= float(thresholds["time_to_first_feasible_ratio_max"]),
        "dynamic_recourse": observed[
            "recourse_ratio_to_best_dynamic_baseline"
        ]
        <= float(thresholds["recourse_ratio_to_best_dynamic_baseline_max"]),
        "unaffected_coalition_integrity": observed[
            "unaffected_coalition_integrity"
        ]
        >= float(thresholds["unaffected_coalition_integrity_min"]),
        "global_fallback_rate": observed["global_fallback_rate"]
        <= float(thresholds["global_fallback_rate_max"]),
        "atomicity": atomicity <= int(thresholds["atomicity_violations_max"]),
        "holm_significance": significant_advantage,
    }
    return {
        "observed": observed,
        "passed": passed,
        "all_passed": all(passed.values()),
    }


def _finite_ratio(numerator: float, denominator: float) -> float:
    if not np.isfinite(numerator) or not np.isfinite(denominator):
        return math.inf
    if abs(float(denominator)) <= 1.0e-12:
        return 0.0 if abs(float(numerator)) <= 1.0e-12 else math.inf
    return float(numerator) / float(denominator)


def _preview_performance_gates(
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    thresholds = config["win_gates"]
    baselines = list(thresholds["distributed_baselines"])
    static = runs.loc[
        runs["experiment"].eq("PREVIEW")
        & runs["method"].isin([*SCALE_METHODS, *baselines])
    ]
    per_method: dict[str, Any] = {}
    passed_by_gate = {
        "recovered_feasibility": True,
        "common_feasible_distance": True,
        "payload_bytes": True,
        "dynamic_recourse": True,
        "unaffected_coalition_integrity": True,
        "global_fallback_rate": True,
    }

    for method in SCALE_METHODS:
        method_static = static[static["method"].eq(method)]
        method_dynamic = dynamic[dynamic["method"].eq(method)]
        static_feasibility = (
            float(method_static["feasible"].mean())
            if not method_static.empty
            else 0.0
        )
        dynamic_feasibility = (
            float(method_dynamic["post_event_feasible"].mean())
            if not method_dynamic.empty
            else 0.0
        )

        static_pivot = static.pivot_table(
            index="world_id",
            columns="method",
            values="feasible",
            aggfunc="first",
        ).reindex(columns=[method, *baselines])
        static_common_ids = static_pivot.dropna().index[
            static_pivot.dropna().astype(bool).all(axis=1)
        ]
        static_common = static[static["world_id"].isin(static_common_ids)]
        scale_distance = float(
            static_common.loc[
                static_common["method"].eq(method),
                "distance_total_m",
            ].median()
        )
        best_distance = min(
            float(
                static_common.loc[
                    static_common["method"].eq(baseline),
                    "distance_total_m",
                ].median()
            )
            for baseline in baselines
        )
        scale_bytes = float(method_static["payload_bytes_total"].median())
        best_bytes = min(
            float(
                static.loc[
                    static["method"].eq(baseline),
                    "payload_bytes_total",
                ].median()
            )
            for baseline in baselines
        )

        dynamic_subset = dynamic[
            dynamic["method"].isin([method, *baselines])
        ]
        dynamic_pivot = dynamic_subset.pivot_table(
            index="world_id",
            columns="method",
            values="post_event_feasible",
            aggfunc="first",
        ).reindex(columns=[method, *baselines])
        dynamic_common_ids = dynamic_pivot.dropna().index[
            dynamic_pivot.dropna().astype(bool).all(axis=1)
        ]
        dynamic_common = dynamic_subset[
            dynamic_subset["world_id"].isin(dynamic_common_ids)
        ]
        scale_recourse = float(
            dynamic_common.loc[
                dynamic_common["method"].eq(method),
                "recourse",
            ].median()
        )
        best_recourse = min(
            float(
                dynamic_common.loc[
                    dynamic_common["method"].eq(baseline),
                    "recourse",
                ].median()
            )
            for baseline in baselines
        )
        integrity = (
            float(method_dynamic["unaffected_coalition_integrity"].median())
            if not method_dynamic.empty
            else 0.0
        )
        fallback_rate = (
            float(method_dynamic["fallback_global_used"].fillna(False).mean())
            if not method_dynamic.empty
            else 1.0
        )
        observed = {
            "static_recovered_feasibility": static_feasibility,
            "dynamic_recovered_feasibility": dynamic_feasibility,
            "distance_ratio_to_best_baseline": _finite_ratio(
                scale_distance,
                best_distance,
            ),
            "bytes_ratio_to_best_baseline": _finite_ratio(
                scale_bytes,
                best_bytes,
            ),
            "recourse_ratio_to_best_dynamic_baseline": _finite_ratio(
                scale_recourse,
                best_recourse,
            ),
            "unaffected_coalition_integrity": integrity,
            "global_fallback_rate": fallback_rate,
            "common_feasible_static_worlds": int(len(static_common_ids)),
            "common_feasible_dynamic_worlds": int(len(dynamic_common_ids)),
        }
        passed = {
            "recovered_feasibility": min(
                static_feasibility,
                dynamic_feasibility,
            )
            >= float(thresholds["recovered_feasibility_min"]),
            "common_feasible_distance": observed[
                "distance_ratio_to_best_baseline"
            ]
            <= float(thresholds["distance_ratio_to_best_baseline_max"]),
            "payload_bytes": observed["bytes_ratio_to_best_baseline"]
            <= float(thresholds["bytes_ratio_to_best_baseline_max"]),
            "dynamic_recourse": observed[
                "recourse_ratio_to_best_dynamic_baseline"
            ]
            <= float(
                thresholds["recourse_ratio_to_best_dynamic_baseline_max"]
            ),
            "unaffected_coalition_integrity": integrity
            >= float(thresholds["unaffected_coalition_integrity_min"]),
            "global_fallback_rate": fallback_rate
            <= float(thresholds["global_fallback_rate_max"]),
        }
        for gate, value in passed.items():
            passed_by_gate[gate] = bool(passed_by_gate[gate] and value)
        per_method[method] = {
            "observed": observed,
            "passed": passed,
            "all_passed": all(passed.values()),
        }
    return {
        "baselines": baselines,
        "per_method": per_method,
        "passed": passed_by_gate,
        "all_passed": all(passed_by_gate.values()),
    }


def _preview_gates(
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    worlds: pd.DataFrame,
    messages: pd.DataFrame,
    message_validation: pd.DataFrame,
    runtime: Mapping[str, Any],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    performance: Mapping[str, Any],
    output_dir: Path,
) -> dict[str, bool]:
    scale = runs[runs["method"].isin(SCALE_METHODS)]
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ]
    local = scale
    finite_columns = [
        "distance_total_m",
        "all_world_cost",
        "wall_time_s",
        "payload_bytes_total",
    ]
    expected_worlds = int(config["preview"]["expected_worlds"])
    expected_dynamic = int(
        config["preview"]["dynamic"]["expected_worlds"]
    )
    expected_tasks = expected_worlds + expected_dynamic
    expected_operational = expected_tasks * len(config["methods"]["scalar"])
    publication_fields = [
        "load_id",
        "committed_capacity",
        "lower_quota",
        "upper_quota",
        "marginal_price",
        "version",
    ]
    message_kinds = set(messages.get("message_kind", pd.Series(dtype=str)))
    forbidden_periodic = {
        "periodic_broadcast",
        "periodic_market_update",
        "global_broadcast",
    }
    return {
        "zero_double_assignments": bool(
            (operational["duplicate_assignment_count"].fillna(0) == 0).all()
        ),
        "zero_stale_version_commits": bool(
            (scale["accepted_version_violations"].fillna(0) == 0).all()
        ),
        "zero_potential_decreasing_accepted_moves": bool(
            (
                scale["potential_decreasing_accepted_moves"].fillna(0)
                == 0
            ).all()
        ),
        "strict_br_monotonic_potential": bool(
            scale["strict_potential_monotone"].fillna(False).all()
        ),
        "zero_strict_br_cycles": bool(
            (scale["cycles_detected"].fillna(0) == 0).all()
        ),
        "strict_br_finite_termination": bool(
            scale["strict_br_finite_termination"].fillna(False).all()
        ),
        "event_triggered_message_accounting": bool(
            message_validation["valid"].all()
            and message_kinds.isdisjoint(forbidden_periodic)
        ),
        "load_publication_schema_exact": bool(
            list(config["scale"]["load_publication_fields"])
            == publication_fields
            and config["scale"]["payload_schema"]["market_update"]
            == {"float64": 4, "int64": 2}
        ),
        "active_set_size_bound": bool(
            int(parameters["L"]) in {4, 8}
            and (
                scale["maximum_active_set_size"].fillna(0)
                <= int(parameters["L"])
            ).all()
        ),
        "local_recovery_scope_enforced": bool(
            local["locality_respected"].fillna(False).all()
            and not local["fallback_global_used"].fillna(False).any()
        ),
        "same_instance_for_all_methods": bool(
            operational.groupby("world_id")["world_hash"].nunique().eq(1).all()
            and operational.groupby("world_id")["method"].nunique().eq(
                len(config["methods"]["scalar"])
            ).all()
        ),
        "no_nan_inf_core_metrics": bool(
            np.isfinite(operational[finite_columns].to_numpy(float)).all()
        ),
        "exact_static_world_count": int(
            worlds.loc[
                worlds["experiment"].eq("PREVIEW"),
                "world_id",
            ].nunique()
        )
        == expected_worlds,
        "exact_dynamic_world_count": int(
            worlds.loc[
                worlds["experiment"].eq("PREVIEW-DYNAMIC"),
                "world_id",
            ].nunique()
        )
        == expected_dynamic,
        "exact_operational_run_count": len(operational) == expected_operational,
        "checkpoint_resume_available": bool(
            (output_dir / "checkpoints" / "tasks").is_dir()
            and int(runtime["tasks_completed"]) == expected_tasks
        ),
        "task_failures_zero": not bool(runtime["task_failures"]),
        **{
            f"performance_{gate}": bool(value)
            for gate, value in performance["passed"].items()
        },
    }


def _save_figure(fig: Any, output_dir: Path, name: str) -> None:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figure_dir / f"{name}.png", dpi=180)
    fig.savefig(figure_dir / f"{name}.pdf")
    plt.close(fig)


def _not_available(ax: Any, text: str) -> None:
    ax.text(0.5, 0.5, text, ha="center", va="center", transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])


def generate_figures(
    output_dir: Path,
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    chains: pd.DataFrame,
    bernstein: pd.DataFrame,
    gap: pd.DataFrame,
) -> list[str]:
    operational = runs.loc[
        (runs["domain"] == "scalar_quotas")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ].copy()
    names = []

    def save(fig: Any, name: str) -> None:
        _save_figure(fig, output_dir, name)
        names.append(name)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    methods = list(operational["method"].drop_duplicates())
    before = operational.groupby("method")["raw_feasible"].mean().reindex(methods)
    after = operational.groupby("method")["feasible"].mean().reindex(methods)
    x = np.arange(len(methods))
    ax.bar(x - 0.2, before, width=0.4, label="semilla/raw")
    ax.bar(x + 0.2, after, width=0.4, label="salida final")
    ax.set_xticks(x, methods, rotation=40, ha="right")
    ax.set_ylabel("Factibilidad")
    ax.legend()
    save(fig, "01_seed_quality_before_after_recovery")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    convergence = operational.groupby("method")["converged"].mean()
    ax.bar(convergence.index, convergence.values)
    ax.tick_params(axis="x", rotation=40)
    ax.set_ylabel("Terminación/convergencia declarada")
    save(fig, "02_persistent_convergence")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    feasibility = operational.groupby("method")["feasible"].mean()
    costs = operational.groupby("method")["all_world_cost"].median()
    axes[0].bar(feasibility.index, feasibility.values)
    axes[0].tick_params(axis="x", rotation=70)
    axes[0].set_ylabel("Factibilidad")
    axes[1].bar(costs.index, costs.values)
    axes[1].tick_params(axis="x", rotation=70)
    axes[1].set_ylabel("All-world cost mediano [m]")
    save(fig, "03_feasibility_all_world_cost")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    feasible = operational[operational["feasible"].astype(bool)]
    distance = feasible.groupby("method")["distance_total_m"].median()
    ax.bar(distance.index, distance.values)
    ax.tick_params(axis="x", rotation=40)
    ax.set_ylabel("Distancia en mundos factibles [m]")
    save(fig, "04_common_feasible_distance")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for method, group in operational.groupby("method"):
        by_n = group.groupby("n")["payload_bytes_total"].median()
        axes[0].plot(by_n.index, by_n.values, marker="o", label=method)
        by_k = group.groupby("k")["payload_bytes_total"].median()
        axes[1].plot(by_k.index, by_k.values, marker="o", label=method)
    axes[0].set_xlabel("N")
    axes[1].set_xlabel("K")
    axes[0].set_ylabel("Payload mediano [bytes]")
    axes[1].legend(fontsize=5, ncol=2)
    save(fig, "05_bytes_vs_n_k")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    scale = operational[operational["method"].isin(SCALE_METHODS)]
    for method, group in scale.groupby("method"):
        active = group.groupby("k")["mean_active_set_size"].median()
        ax.plot(active.index, active.values, marker="o", label=method)
    ax.set_xlabel("K")
    ax.set_ylabel("Tamaño medio de A_i")
    ax.legend(fontsize=7)
    save(fig, "06_active_set_size_vs_k")

    fig, ax = plt.subplots(figsize=(9, 6))
    if dynamic.empty:
        _not_available(ax, "C6 no pertenece al preview")
    else:
        recourse = dynamic.groupby("method")["recourse"].median().sort_values()
        ax.barh(recourse.index, recourse.values)
        ax.set_xlabel("Recourse mediano")
    save(fig, "07_dynamic_recourse")

    fig, ax = plt.subplots(figsize=(9, 6))
    if dynamic.empty:
        _not_available(ax, "C6 no pertenece al preview")
    else:
        integrity = dynamic.groupby("method")[
            "unaffected_coalition_integrity"
        ].median().sort_values()
        ax.barh(integrity.index, integrity.values)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Integridad mediana")
    save(fig, "08_unaffected_coalition_integrity")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    if chains.empty:
        _not_available(ax, "C8 no pertenece al preview")
    else:
        for method, group in chains.groupby("repair_method"):
            values = group.groupby("required_chain_length")[
                "nodes_expanded"
            ].median()
            ax.plot(values.index, values.values, marker="o", label=method)
        ax.set_xlabel("Longitud requerida")
        ax.set_ylabel("Nodos expandidos")
        ax.legend(fontsize=7)
    save(fig, "09_augmenting_chain_complexity")

    fig, ax = plt.subplots(figsize=(6, 5.5))
    if bernstein.empty or "bernstein_bound" not in bernstein:
        _not_available(ax, "Validación disponible en V1.1")
    else:
        grouped = bernstein.groupby("target_band").agg(
            bound=("bernstein_bound", "mean"),
            failure=("failure_frequency", "mean"),
        )
        ax.plot([0, 1], [0, 1], "--", color="grey")
        ax.scatter(grouped["bound"], grouped["failure"])
        ax.set_xlabel("Cota Bernstein")
        ax.set_ylabel("Fallo empírico")
    save(fig, "10_bernstein_calibration")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    if gap.empty or "comparable" not in gap:
        _not_available(axes[0], "Descomposición disponible en V1.1")
        _not_available(axes[1], "Descomposición disponible en V1.1")
    else:
        comparable = gap[gap["comparable"].astype(bool)]
        medians = comparable[
            [
                "optimization_error_over_J_ref",
                "entropy_bias_bound_over_J_ref",
                "positive_atomic_delta_over_J_ref",
            ]
        ].median()
        axes[0].bar(medians.index, medians.values)
        axes[0].tick_params(axis="x", rotation=30)
        axes[1].hist(gap["signed_atomic_delta_m"].dropna(), bins=30)
        axes[1].set_xlabel("Delta firmado [m]")
    save(fig, "11_homogeneous_gap_decomposition")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    pareto = operational.groupby("method").agg(
        cost=("all_world_cost", "median"),
        bytes=("payload_bytes_total", "median"),
        recourse=("recourse", "median"),
    )
    scatter = ax.scatter(
        pareto["cost"],
        pareto["bytes"],
        c=pareto["recourse"],
        cmap="viridis",
    )
    method_key = []
    label_offsets = ((4, 4), (4, -10), (-10, 4), (-10, -10))
    for index, (method, row) in enumerate(pareto.iterrows(), start=1):
        offset = label_offsets[(index - 1) % len(label_offsets)]
        ax.annotate(
            str(index),
            (row["cost"], row["bytes"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=7,
            weight="bold",
        )
        method_key.append(f"{index:>2}  {method}")
    ax.text(
        1.20,
        0.5,
        "\n".join(method_key),
        transform=ax.transAxes,
        va="center",
        fontsize=7,
        family="monospace",
    )
    ax.set_xlabel("All-world cost [m]")
    ax.set_ylabel("Payload [bytes]")
    fig.colorbar(scatter, ax=ax, label="Recourse")
    save(fig, "12_pareto_quality_communication_recourse")
    return names


def _select_conclusion(
    win: Mapping[str, Any] | None,
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
) -> tuple[str, str]:
    if win and win["all_passed"]:
        return "A", "SCALE-QPG supera los gates en el régimen objetivo."
    if win and "per_method" in win:
        return (
            "F",
            "SCALE-QPG no supera todos los gates del preview; V2 full queda bloqueada.",
        )
    passed = win["passed"] if win else {}
    quality = all(
        passed.get(key, False)
        for key in (
            "recovered_feasibility",
            "common_feasible_distance",
            "all_world_cost",
        )
    )
    if quality and not passed.get("payload_bytes", False):
        return "B", "SCALE-QPG conserva calidad, pero no reduce comunicación."
    if passed.get("payload_bytes", False) and not quality:
        return "C", "SCALE-QPG reduce comunicación, pero pierde calidad."
    dynamic_good = passed.get("dynamic_recourse", False) and passed.get(
        "unaffected_coalition_integrity",
        False,
    )
    if dynamic_good and not quality:
        return (
            "D",
            "SCALE-QPG mejora la adaptación dinámica, pero no el caso estático.",
        )
    c7 = runs[runs["experiment"] == "C7"]
    if not c7.empty:
        nearest = c7.loc[
            c7["method"] == "NearestCompatibleSeed-AR",
            "all_world_cost",
        ].median()
        qpg = c7.loc[
            c7["method"].isin(["QPG-Logit-AR", "QPG-Replicator-AR"]),
            "all_world_cost",
        ].median()
        if np.isfinite(nearest) and np.isfinite(qpg) and qpg >= nearest:
            return (
                "E",
                "El recovery explica casi toda la ventaja y QPG no está justificado.",
            )
    return "F", "Existen regímenes distintos y no hay dominador."


def _build_report(
    output_dir: Path,
    *,
    is_preview: bool,
    runs: pd.DataFrame,
    dynamic: pd.DataFrame,
    aggregates: pd.DataFrame,
    comparisons: pd.DataFrame,
    audit: Mapping[str, Any],
    win: Mapping[str, Any] | None,
    runtime: Mapping[str, Any],
    conclusion: tuple[str, str],
) -> None:
    scale = aggregates[
        aggregates["method"].isin(
            [
                *SCALE_METHODS,
                "Capacity-CBBA",
                "Weighted-GRAPE",
                "Weighted-Pair-GRAPE",
            ]
        )
    ]
    claims_allowed = [
        "La salida física de SCALE-QPG es atómica en todos los runs auditados.",
        "La fase strict-BR solo acepta incrementos exactos positivos del potencial.",
        "El payload lógico se contabiliza por eventos y rutas del grafo.",
        "Los resultados se limitan a reclutamiento escalar SP1 en simulación.",
    ]
    claims_forbidden = [
        "Superioridad universal sobre CBBA o GRAPE.",
        "Convergencia global o optimalidad social.",
        "Equivalencia de Weighted-GRAPE con GRAPE-S canónico.",
        "Validación de transporte físico, contacto o hardware.",
    ]
    lines = [
        f"# {PREVIEW if is_preview else CAMPAIGN}",
        "",
        "## Resultado principal",
        "",
        (
            "El preview bloqueante "
            f"{'aprobó' if audit['passed'] else 'no aprobó'} los gates de "
            "integridad y rendimiento. La campaña full no se ejecuta desde "
            "este paquete."
            if is_preview
            else (
                "La campaña full se ejecutó solo después de aprobar el preview. "
                "Los gates científicos se evalúan de forma conjuntiva."
            )
        ),
        "",
        scale.to_markdown(index=False) if not scale.empty else "Sin resumen.",
        "",
        "## Comparaciones emparejadas",
        "",
        comparisons.to_markdown(index=False)
        if not comparisons.empty
        else "No aplicable en preview.",
        "",
        "## Gates",
        "",
        "```json",
        json.dumps(
            win if win is not None else audit["gates"],
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        "```",
        "",
        "## Dominio separado de servicios",
        "",
        (
            "C9 conserva GRAPE-S y Pair-GRAPE-S en servicios discretos. "
            "Weighted-GRAPE es una adaptación escalar y no se presenta como "
            "GRAPE-S canónico."
        ),
        "",
        "## Claims permitidos",
        "",
        *[f"- {claim}" for claim in claims_allowed],
        "",
        "## Claims prohibidos",
        "",
        *[f"- {claim}" for claim in claims_forbidden],
        "",
        "## Contabilidad",
        "",
        f"- Tareas: {runtime['tasks_completed']}.",
        f"- Censuras: {int(runs.get('censored', pd.Series(dtype=bool)).fillna(False).sum())}.",
        f"- Fallbacks globales: {int(runs.get('fallback_global_used', pd.Series(dtype=bool)).fillna(False).sum())}.",
        f"- Runtime del driver: {float(runtime['wall_time_s']):.3f} s.",
        "",
        f"Conclusión seleccionada: {conclusion[0]}. {conclusion[1]}",
    ]
    (output_dir / "report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _copy_closure_table(
    repo: Path,
    filename: str,
    columns: Sequence[str],
) -> pd.DataFrame:
    path = (
        repo
        / "results/sp1_validation/SP1_TFM_VALIDATION_CLOSURE_v1_1"
        / filename
    )
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=list(columns))


def _write_outputs(
    *,
    repo: Path,
    output_dir: Path,
    frames: Mapping[str, pd.DataFrame],
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    runtime: Mapping[str, Any],
    is_preview: bool,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, Any],
    dict[str, Any] | None,
    tuple[str, str],
    list[str],
]:
    runs = frames["runs"]
    traces = frames["traces"]
    messages = frames["messages"]
    worlds = frames["worlds"]
    dynamic = frames["dynamic"]
    chains = frames["chains"]
    write_parquet_or_empty(output_dir / "all_runs.parquet", runs)
    write_parquet_or_empty(output_dir / "all_traces.parquet", traces)
    write_parquet_or_empty(output_dir / "all_messages.parquet", messages)
    dynamic.to_csv(output_dir / "dynamic_events.csv", index=False)
    seed_attribution = runs.loc[
        runs["experiment"].eq("C7")
        & ~runs["method"].isin(["LP-oracle", "MILP-oracle"])
    ].copy()
    seed_attribution.to_csv(output_dir / "seed_attribution.csv", index=False)
    convergence = runs.loc[
        runs["method"].isin(SCALE_METHODS),
        [
            column
            for column in (
                "world_id",
                "method",
                "converged",
                "censored",
                "censoring_reason",
                "logical_rounds",
                "first_feasible_time_s",
                "first_persistent_feasible_time_s",
                "final_termination_time_s",
                "strict_potential_monotone",
                "cycles_detected",
            )
            if column in runs
        ],
    ]
    convergence.to_csv(output_dir / "convergence_validation.csv", index=False)
    bernstein = _copy_closure_table(
        repo,
        "bernstein_validation.csv",
        [
            "target_band",
            "bernstein_bound",
            "failure_frequency",
            "bound_violated",
        ],
    )
    bernstein.to_csv(output_dir / "bernstein_validation.csv", index=False)
    gap = _copy_closure_table(
        repo,
        "gap_decomposition.csv",
        [
            "world_id",
            "comparable",
            "optimization_error_over_J_ref",
            "entropy_bias_bound_over_J_ref",
            "positive_atomic_delta_over_J_ref",
            "signed_atomic_delta_m",
        ],
    )
    gap.to_csv(output_dir / "gap_decomposition.csv", index=False)
    comparisons = paired_comparisons(runs, dynamic, config)
    comparisons.to_csv(output_dir / "paired_comparisons.csv", index=False)
    censoring = runs.loc[
        runs.get("censored", pd.Series(False, index=runs.index))
        .fillna(False)
        .astype(bool),
        [
            column
            for column in (
                "world_id",
                "method",
                "wall_time_s",
                "final_termination_time_s",
                "censoring_reason",
            )
            if column in runs
        ],
    ]
    censoring.to_csv(output_dir / "censoring.csv", index=False)
    fallbacks = runs.loc[
        runs.get("fallback_global_used", pd.Series(False, index=runs.index))
        .fillna(False)
        .astype(bool),
        [
            column
            for column in ("world_id", "method", "experiment")
            if column in runs
        ],
    ].copy()
    if not fallbacks.empty:
        fallbacks["fallback_kind"] = "global"
    else:
        fallbacks = pd.DataFrame(
            columns=["world_id", "method", "experiment", "fallback_kind"]
        )
    fallbacks.to_csv(output_dir / "fallbacks.csv", index=False)
    regime = _regime_map(runs)
    regime.to_csv(output_dir / "regime_map.csv", index=False)
    message_validation = _message_validation(runs, messages)
    message_validation.to_csv(
        output_dir / "message_accounting_validation.csv",
        index=False,
    )
    aggregates = aggregate_results(runs)
    aggregates.to_csv(output_dir / "aggregated_results.csv", index=False)
    survival = survival_summary(runs)
    survival.to_csv(output_dir / "survival_rmst.csv", index=False)
    tables = {
        **dict(frames),
        "seed_attribution": seed_attribution,
        "convergence": convergence,
        "bernstein": bernstein,
        "gap": gap,
        "comparisons": comparisons,
        "censoring": censoring,
        "fallbacks": fallbacks,
        "regime": regime,
        "message_validation": message_validation,
        "aggregates": aggregates,
        "survival": survival,
    }
    win = (
        _preview_performance_gates(runs, dynamic, config)
        if is_preview
        else _win_gates(runs, dynamic, comparisons, config)
    )
    if is_preview:
        gates = _preview_gates(
            runs,
            dynamic,
            worlds,
            messages,
            message_validation,
            runtime,
            config,
            parameters,
            win,
            output_dir,
        )
    else:
        expected = config["expected_counts"]
        observed_task_counts = {
            experiment.lower(): int(
                sum(
                    1
                    for path in (
                        output_dir / "checkpoints" / "tasks"
                    ).glob(f"{experiment.upper()}_*")
                )
            )
            for experiment in (
                "c1",
                "c2",
                "c3",
                "c4",
                "c5",
                "c6",
                "c7",
                "c8",
                "c9",
            )
        }
        gates = {
            "preview_passed_before_full": True,
            "all_tasks_completed": int(runtime["tasks_completed"])
            == sum(int(expected[key]) for key in observed_task_counts),
            "task_failures_zero": not bool(runtime["task_failures"]),
            "message_accounting_reproducible": bool(
                message_validation["valid"].all()
            ),
            "atomicity_preserved": bool(
                runs.loc[
                    runs["domain"].eq("scalar_quotas")
                    & ~runs["method"].isin(["LP-oracle", "MILP-oracle"]),
                    "atomicity_violations",
                ]
                .fillna(0)
                .eq(0)
                .all()
            ),
            "strict_phase_monotone": bool(
                runs.loc[
                    runs["method"].isin(SCALE_METHODS),
                    "strict_potential_monotone",
                ]
                .fillna(False)
                .all()
            ),
            "zero_strict_cycles": bool(
                runs.loc[
                    runs["method"].isin(SCALE_METHODS),
                    "cycles_detected",
                ]
                .fillna(0)
                .eq(0)
                .all()
            ),
            "locality_respected": bool(
                runs.loc[
                    runs["method"].isin(
                        [
                            "SCALE-QPG-LogitBR-LocalAR",
                            "SCALE-QPG-ReplicatorBR-LocalAR",
                        ]
                    ),
                    "locality_respected",
                ]
                .fillna(False)
                .all()
            ),
            "exact_task_counts": all(
                observed_task_counts[key] == int(expected[key])
                for key in observed_task_counts
            ),
        }
    audit = {
        "campaign": PREVIEW if is_preview else CAMPAIGN,
        "gates": gates,
        "passed": all(gates.values()),
        "scientific_win_gates": win,
        "runtime": dict(runtime),
        "row_counts": {
            key: len(frame) for key, frame in tables.items()
        },
        "limitations": [
            "Finite simulation is not a global convergence proof.",
            "Local AR is bounded and incomplete.",
            "Payload is logical traffic, not middleware traffic.",
            "C9 is a separate discrete-service domain.",
            "No transport physics or hardware is evaluated.",
        ],
    }
    write_json(output_dir / "audit.json", audit)
    if is_preview:
        write_json(output_dir / "scale_qpg_preview_audit.json", audit)
    conclusion = _select_conclusion(win, runs, dynamic)
    figures = generate_figures(
        output_dir,
        runs,
        dynamic,
        chains,
        bernstein,
        gap,
    )
    statistics = {
        "aggregates": aggregates.to_dict("records"),
        "paired_comparisons": comparisons.to_dict("records"),
        "survival": survival.to_dict("records"),
        "scientific_win_gates": win,
        "conclusion": {"code": conclusion[0], "text": conclusion[1]},
        "methods": {
            "proportions": "Wilson 95%",
            "paired_binary": "exact McNemar/binomial",
            "continuous": "paired bootstrap, Wilcoxon and rank-biserial",
            "multiplicity": "Holm",
            "censoring": "Kaplan-Meier/RMST and restricted mean bytes",
        },
    }
    write_json(output_dir / "statistics.json", statistics)
    return tables, audit, win, conclusion, figures


def execute_campaign(
    *,
    repo: Path,
    config_path: Path,
    mode: str,
    workers: int | None = None,
    force: bool = False,
) -> Path:
    if mode not in {"preview", "full"}:
        raise ValueError("mode must be preview or full")
    config = load_resolved_config(repo, config_path)
    is_preview = mode == "preview"
    output_dir = repo / config["output_dirs"]["preview" if is_preview else "full"]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(output_dir / "config_snapshot.yaml", config)
    worker_count = int(workers or config["parallel_workers"])
    preview_dir = repo / config["output_dirs"]["preview"]
    if is_preview:
        selected_path = output_dir / "selected_parameters.yaml"
        if selected_path.exists() and not force:
            parameters = yaml.safe_load(selected_path.read_text(encoding="utf-8"))
        else:
            parameters = run_calibration(
                config,
                output_dir,
                workers=worker_count,
                force=force,
            )
    else:
        preview_audit_path = preview_dir / "audit.json"
        if not preview_audit_path.exists():
            raise RuntimeError("blocking preview audit does not exist")
        preview_audit = json.loads(
            preview_audit_path.read_text(encoding="utf-8")
        )
        if not bool(preview_audit["passed"]):
            raise RuntimeError("blocking preview gates did not pass")
        selected_path = preview_dir / "selected_parameters.yaml"
        if not selected_path.exists():
            raise RuntimeError("frozen preview parameters are missing")
        parameters = yaml.safe_load(selected_path.read_text(encoding="utf-8"))
        write_yaml(output_dir / "selected_parameters.yaml", parameters)
        for filename in ("calibration_runs.csv", "calibration_summary.csv"):
            source = preview_dir / filename
            if source.exists():
                (output_dir / filename).write_bytes(source.read_bytes())
    tasks = build_preview_tasks(config) if is_preview else build_full_tasks(config)
    frames, runtime = run_task_set(
        tasks=tasks,
        config=config,
        parameters=parameters,
        output_dir=output_dir,
        stage="preview" if is_preview else "full",
        workers=worker_count,
        force=force,
    )
    tables, audit, win, conclusion, figures = _write_outputs(
        repo=repo,
        output_dir=output_dir,
        frames=frames,
        config=config,
        parameters=parameters,
        runtime=runtime,
        is_preview=is_preview,
    )
    _build_report(
        output_dir,
        is_preview=is_preview,
        runs=frames["runs"],
        dynamic=frames["dynamic"],
        aggregates=tables["aggregates"],
        comparisons=tables["comparisons"],
        audit=audit,
        win=win,
        runtime=runtime,
        conclusion=conclusion,
    )
    if is_preview:
        (output_dir / "scale_qpg_preview_report.md").write_text(
            (output_dir / "report.md").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    reproduce = f"""# Reproducción de {PREVIEW if is_preview else CAMPAIGN}

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_scale_qpg_v2 --mode {mode} --workers {worker_count} --resume
```

Los parámetros se calibran únicamente con semillas 91000--91029 y se
congelan antes del preview. Full exige un `audit.json` de preview aprobado.
Los shards en `checkpoints/` son idempotentes; `--force` los recalcula.
"""
    (output_dir / "README_REPRODUCE.md").write_text(
        reproduce,
        encoding="utf-8",
    )
    manifest = {
        "campaign": PREVIEW if is_preview else CAMPAIGN,
        "schema_version": int(config["schema_version"]),
        "config_sha256": sha256_file(output_dir / "config_snapshot.yaml"),
        "selected_parameters_sha256": sha256_file(
            output_dir / "selected_parameters.yaml"
        ),
        "task_manifest_hash": stable_hash(tasks),
        "tasks": len(tasks),
        "environment": environment_record(),
        "git_at_execution": git_metadata(repo),
        "runtime": runtime,
        "audit_passed": bool(audit["passed"]),
        "scientific_win_gates": win,
        "conclusion": {"code": conclusion[0], "text": conclusion[1]},
        "censoring_count": int(
            frames["runs"]
            .get("censored", pd.Series(dtype=bool))
            .fillna(False)
            .sum()
        ),
        "fallback_count": int(
            frames["runs"]
            .get("fallback_global_used", pd.Series(dtype=bool))
            .fillna(False)
            .sum()
        ),
        "figures": figures,
    }
    write_json(output_dir / "manifest.json", manifest)
    write_checksums(output_dir)
    return output_dir
