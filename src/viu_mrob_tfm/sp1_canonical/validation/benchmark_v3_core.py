"""World/scenario execution helpers for the SP1 dynamics V3 campaign."""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import replace
from typing import Any, Mapping

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import shortest_path

from viu_mrob_tfm.sp1_canonical.validation.auction import distributed_deficit_auction
from viu_mrob_tfm.sp1_canonical.validation.conference import _minimum_connected_rdisk
from viu_mrob_tfm.sp1_canonical.validation.dynamics import GraphInfo, make_graph
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v3 import (
    FRACTIONAL_METHODS,
    METHOD_KEYS,
    DynamicsBudgets,
    recompute_message_accounting,
    run_best_response_pure,
    run_fractional_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import (
    ResourceWorld,
    build_costs,
    generate_resource_world,
    normalized_constraints,
)
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    argmax_round,
    evaluate_integer,
    repair_assignment_augmenting,
)
from viu_mrob_tfm.sp1_canonical.validation.solvers import (
    allocation_entropy,
    assignment_from_matrix,
    evaluate_relaxed,
    solve_lp,
    solve_milp,
    solve_regularized_lp,
)


def deterministic_case_catalog() -> pd.DataFrame:
    """Predeclared E7.0 cases and the invariant each one isolates."""

    return pd.DataFrame(
        [
            {"case_id": "E70-01", "case": "symmetric_homogeneous", "expected": "simplex and deterministic symmetry"},
            {"case_id": "E70-02", "case": "empty_strategy_becomes_optimal", "expected": "Smith/BNN/Logit/BR reactivate admissible zero mass"},
            {"case_id": "E70-03", "case": "rare_capacity_robot", "expected": "critical resource remains available"},
            {"case_id": "E70-04", "case": "battery_incompatible_load", "expected": "masked mass remains zero"},
            {"case_id": "E70-05", "case": "two_loads_one_critical_robot", "expected": "one-robot simplex prevents double assignment"},
            {"case_id": "E70-06", "case": "payoff_tie", "expected": "BestResponse chooses lowest valid index"},
            {"case_id": "E70-07", "case": "complete_graph", "expected": "packet formula matches complete edge count"},
            {"case_id": "E70-08", "case": "connected_rdisk", "expected": "positive algebraic connectivity"},
            {"case_id": "E70-09", "case": "masked_strategies", "expected": "projection never activates invalid strategy"},
            {"case_id": "E70-10", "case": "synchronous_br_oscillation", "expected": "damped BR remains on simplex and avoids two-cycle at eta<1"},
        ]
    )


def stable_hash(value: Any) -> str:
    if isinstance(value, np.ndarray):
        return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def graph_from_adjacency(name: str, adjacency: np.ndarray) -> GraphInfo:
    adjacency = np.asarray(adjacency, dtype=bool)
    adjacency = adjacency | adjacency.T
    np.fill_diagonal(adjacency, False)
    degrees = adjacency.sum(axis=1).astype(float)
    laplacian = np.diag(degrees) - adjacency.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    lambda2 = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
    return GraphInfo(
        name=name,
        adjacency=adjacency,
        edges=int(np.sum(adjacency) // 2),
        lambda2=lambda2,
        lambda_max=float(eigenvalues[-1]) if len(eigenvalues) else 0.0,
        connected=bool(len(adjacency) <= 1 or lambda2 > 1e-10),
    )


def graph_metrics(graph: GraphInfo) -> dict[str, Any]:
    n = len(graph.adjacency)
    average_degree = float(2 * graph.edges / n) if n else 0.0
    if graph.connected and n > 1:
        distances = shortest_path(graph.adjacency.astype(float), directed=False, unweighted=True)
        diameter = int(np.max(distances[np.isfinite(distances)]))
    else:
        diameter = math.inf
    condition = graph.lambda_max / graph.lambda2 if graph.lambda2 > 1e-12 else math.inf
    return {
        "graph_hash": stable_hash(graph.adjacency.astype(np.uint8)),
        "graph_edges": graph.edges,
        "average_degree": average_degree,
        "graph_diameter": diameter,
        "lambda_2": graph.lambda2,
        "lambda_max": graph.lambda_max,
        "laplacian_condition": condition,
        "graph_connected": graph.connected,
    }


def target_degree_rdisk(world: ResourceWorld, target_degree: float) -> tuple[GraphInfo, float]:
    """Choose the connected r-disk threshold closest to a target mean degree."""

    positions = world.robot_positions_m
    distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
    candidates = np.unique(distances[np.triu_indices(world.n_robots, 1)])
    connected: list[tuple[float, float, GraphInfo]] = []
    for radius in candidates:
        graph = make_graph(world, "rdisk", radius_m=float(radius) + 1e-10)
        if graph.connected:
            mean_degree = 2.0 * graph.edges / world.n_robots
            connected.append((abs(mean_degree - float(target_degree)), float(radius), graph))
    if not connected:
        graph, radius = _minimum_connected_rdisk(world)
        return graph, radius
    _, radius, graph = min(connected, key=lambda item: (item[0], item[1]))
    return graph_from_adjacency(f"rdisk_degree_{int(target_degree)}", graph.adjacency), radius + 1e-10


def scenario_graph(world: ResourceWorld, topology: str) -> tuple[GraphInfo, float]:
    if topology == "complete":
        return make_graph(world, "complete"), math.inf
    if topology in {"rdisk_v2", "rdisk"}:
        return _minimum_connected_rdisk(world)
    if topology.startswith("rdisk_degree_"):
        return target_degree_rdisk(world, float(topology.rsplit("_", 1)[-1]))
    if topology == "shared_dual":
        return make_graph(world, "complete"), math.inf
    raise ValueError(f"unknown V3 topology: {topology}")


def _rehash_world(world: ResourceWorld, label: str) -> ResourceWorld:
    payload = {
        "label": label,
        "seed": world.seed,
        "positions": world.robot_positions_m.round(12).tolist(),
        "loads": world.load_positions_m.round(12).tolist(),
        "resources": world.resources.round(12).tolist(),
        "requirements": world.requirements.round(12).tolist(),
        "battery": world.battery_energy.round(12).tolist(),
        "speed": world.max_speed_mps.round(12).tolist(),
        "consumption": world.energy_per_m.round(12).tolist(),
        "witness": world.feasibility_witness.tolist(),
    }
    return replace(world, world_hash=stable_hash(payload))


def controlled_utilization_world(n: int, k: int, seed: int, target: float) -> ResourceWorld:
    """Construct a feasible K-scaling world with total utilization near target."""

    if not 0.70 <= target <= 0.80:
        raise ValueError("target utilization must lie in the predeclared 70--80% interval")
    base = generate_resource_world(n, k, seed)
    rng = np.random.default_rng(int(seed) + 271828)
    groups = np.array_split(rng.permutation(n), k)
    requirements = np.zeros_like(base.requirements)
    witness = np.full(n, -1, dtype=int)
    battery = base.battery_energy.copy()
    for load, coalition in enumerate(groups):
        witness[coalition] = load
        requirements[load, 0] = max(1, int(math.ceil(target * len(coalition))))
        requirements[load, 1:] = target * base.resources[coalition, 1:].sum(axis=0)
        distance = np.linalg.norm(base.robot_positions_m[coalition] - base.load_positions_m[load], axis=1)
        battery[coalition] = np.maximum(
            battery[coalition],
            1.5 * distance * base.energy_per_m[coalition] + 8.0,
        )
    world = replace(base, requirements=requirements, feasibility_witness=witness, battery_energy=battery)
    return _rehash_world(world, f"controlled_utilization_{target:.6f}")


def event_base_and_reserve(n: int, k: int, seed: int) -> tuple[ResourceWorld, ResourceWorld]:
    """Create a K-load base and a held-out feasible (K+1)-th load."""

    full = generate_resource_world(n, k + 1, seed)
    base_witness = np.where(full.feasibility_witness < k, full.feasibility_witness, -1)
    base = replace(
        full,
        load_positions_m=full.load_positions_m[:k].copy(),
        requirements=full.requirements[:k].copy(),
        feasibility_witness=base_witness,
    )
    return _rehash_world(base, "e75_base"), _rehash_world(full, "e75_new_load")


def degraded_connected_graph(graph: GraphInfo) -> GraphInfo:
    adjacency = graph.adjacency.copy()
    edges = [(int(i), int(j)) for i, j in np.argwhere(np.triu(adjacency, 1))]
    target = max(len(adjacency) - 1, int(math.ceil(0.55 * len(edges))))
    for i, j in sorted(edges, reverse=True):
        if int(np.sum(adjacency) // 2) <= target:
            break
        candidate = adjacency.copy()
        candidate[i, j] = candidate[j, i] = False
        info = graph_from_adjacency("topology_degradation", candidate)
        if info.connected:
            adjacency = candidate
    return graph_from_adjacency("topology_degradation", adjacency)


def apply_event(
    base: ResourceWorld,
    reserve: ResourceWorld,
    graph: GraphInfo,
    event: str,
) -> tuple[ResourceWorld, GraphInfo, dict[str, Any]]:
    critical_candidates = np.flatnonzero(base.feasibility_witness == 0)
    critical = int(critical_candidates[0]) if critical_candidates.size else 0
    metadata: dict[str, Any] = {"critical_robot": critical}
    if event == "new_load":
        return reserve, graph, metadata
    if event == "robot_failure":
        resources = base.resources.copy()
        battery = base.battery_energy.copy()
        resources[critical] = 0.0
        battery[critical] = 0.0
        world = _rehash_world(replace(base, resources=resources, battery_energy=battery), event)
        return world, graph, metadata
    if event == "capacity_drop":
        resources = base.resources.copy()
        battery = base.battery_energy.copy()
        resources[critical, 1:] *= 0.35
        battery[critical] *= 0.45
        world = _rehash_world(replace(base, resources=resources, battery_energy=battery), event)
        return world, graph, metadata
    if event == "topology_degradation":
        degraded = degraded_connected_graph(graph)
        metadata["removed_edges"] = graph.edges - degraded.edges
        return _rehash_world(base, event), degraded, metadata
    raise ValueError(f"unknown event: {event}")


def _cost_hash(costs: np.ndarray) -> str:
    safe = np.where(np.isfinite(costs), costs, np.finfo(float).max)
    return stable_hash(safe)


def _regularized_objective(costs: np.ndarray, x: np.ndarray, tau: float) -> float:
    finite = np.isfinite(costs)
    scale = max(float(np.max(costs[finite])) if np.any(finite) else 1.0, 1e-12)
    raw = float(np.sum(np.where(finite, costs, 0.0) * x))
    return raw / scale - tau * allocation_entropy(x)


def solve_references(
    world: ResourceWorld,
    costs: np.ndarray,
    config: Mapping[str, Any],
    *,
    include_regularized: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    lp = solve_lp(world, costs)
    lp_time = time.perf_counter() - started
    lp_tau = None
    lp_tau_time = math.nan
    # SLSQP grows quickly; N<=50 is the predeclared computationally permitted set.
    if include_regularized and world.n_robots <= 50:
        started = time.perf_counter()
        lp_tau = solve_regularized_lp(world, costs, entropy_tau=float(config["entropy_tau"]))
        lp_tau_time = time.perf_counter() - started
    milp = None
    milp_time = math.nan
    if world.n_robots <= int(config["oracles"]["milp_max_n"]):
        started = time.perf_counter()
        milp = solve_milp(world, costs, time_limit_s=float(config["oracles"]["milp_timeout_s"]))
        milp_time = time.perf_counter() - started
    return {
        "lp": lp,
        "lp_time": lp_time,
        "lp_tau": lp_tau,
        "lp_tau_time": lp_tau_time,
        "milp": milp,
        "milp_time": milp_time,
    }


def _base_record(
    *,
    experiment: str,
    scenario_id: str,
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    topology: str,
    seed: int,
    method: str,
    method_family: str,
    is_primary: bool,
    distributed: bool,
) -> dict[str, Any]:
    graph_data = graph_metrics(graph)
    initial = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    feasible = np.isfinite(costs)
    for robot in range(world.n_robots):
        valid = np.flatnonzero(np.r_[feasible[robot], True])
        initial[robot, valid] = 1.0 / len(valid)
    return {
        "experiment": experiment,
        "scenario_id": scenario_id,
        "world_id": f"{experiment}-N{world.n_robots}-K{world.n_loads}-S{seed}",
        "world_hash": world.world_hash,
        "cost_hash": _cost_hash(costs),
        "initial_state_hash": stable_hash(initial),
        "initial_dual_hash": stable_hash(np.zeros((world.n_robots, world.n_loads, 3)) if distributed else np.zeros((world.n_loads, 3))),
        "seed": int(seed),
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "strategy_dimension": world.n_loads + 1,
        "topology": topology,
        "distributed": distributed,
        "method": method,
        "method_family": method_family,
        "is_primary": is_primary,
        **graph_data,
    }


def _reference_rows(
    base: dict[str, Any],
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    references: Mapping[str, Any],
    *,
    include_auction: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lp = references["lp"]
    rows.append(
        {
            **base,
            "method": "LP-raw",
            "method_family": "central_reference",
            "is_primary": False,
            "objective_raw": lp.raw_objective,
            "objective_regularized": lp.regularized_objective,
            "primal_feasibility": lp.status == 0,
            "operational_converged": lp.status == 0,
            "integer_feasibility": math.nan,
            "wall_time_s": references["lp_time"],
            "censored": lp.status != 0,
            "censoring_reason": "none" if lp.status == 0 else "oracle_failure",
            "oracle_certified": lp.status == 0,
        }
    )
    lp_tau = references["lp_tau"]
    if lp_tau is not None:
        rows.append(
            {
                **base,
                "method": "LP-tau",
                "method_family": "central_reference",
                "is_primary": False,
                "objective_raw": lp_tau.raw_objective,
                "objective_regularized": lp_tau.regularized_objective,
                "primal_feasibility": lp_tau.status == 0,
                "operational_converged": lp_tau.status == 0,
                "integer_feasibility": math.nan,
                "wall_time_s": references["lp_tau_time"],
                "censored": lp_tau.status != 0,
                "censoring_reason": "none" if lp_tau.status == 0 else "oracle_failure",
                "oracle_certified": lp_tau.status == 0,
            }
        )
    milp = references["milp"]
    if milp is not None:
        integer = evaluate_integer(world, assignment_from_matrix(milp.x), costs)
        certified = bool(milp.status == 0 and (not np.isfinite(milp.mip_gap) or milp.mip_gap <= 1e-9))
        rows.append(
            {
                **base,
                "method": "MILP-oracle",
                "method_family": "central_reference",
                "is_primary": False,
                "objective_raw": integer.objective,
                "objective_regularized": math.nan,
                "primal_feasibility": integer.feasible,
                "integer_feasibility": integer.feasible,
                "operational_converged": certified,
                "wall_time_s": references["milp_time"],
                "censored": not certified,
                "censoring_reason": "none" if certified else "oracle_timeout_or_gap",
                "oracle_certified": certified,
                "oracle_mip_gap": milp.mip_gap,
            }
        )
    if include_auction:
        auction = distributed_deficit_auction(world, costs, graph)
        rows.append(
            {
                **base,
                "method": "Auction-D",
                "method_family": "distributed_reference",
                "is_primary": False,
                "objective_raw": auction.integer.objective,
                "objective_regularized": math.nan,
                "primal_feasibility": auction.integer.feasible,
                "integer_feasibility": auction.integer.feasible,
                "operational_converged": auction.integer.feasible,
                "logical_rounds": auction.rounds,
                "wall_time_s": auction.runtime_s,
                "packets_total": auction.messages,
                "scalar_transmissions_total": auction.scalars_sent,
                "payload_bytes_total": 8 * auction.scalars_sent,
                "censored": False,
                "censoring_reason": "none",
                "oracle_certified": False,
                "recovery_executed": False,
                "assignment_json": json.dumps(auction.integer.assignment.tolist()),
            }
        )
    return rows


def run_fractional_scenario(
    config: Mapping[str, Any],
    selected: Mapping[str, Mapping[str, Any]],
    task: Mapping[str, Any],
    budgets: DynamicsBudgets,
    *,
    include_references: bool = True,
    include_pure: bool = False,
    include_recovery: bool = True,
    parameters_override: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    experiment = str(task["experiment"])
    n, k, seed = int(task["n"]), int(task["k"]), int(task["seed"])
    topology = str(task["topology"])
    if experiment == "e74":
        world = controlled_utilization_world(n, k, seed, float(task["target_utilization"]))
    else:
        world = generate_resource_world(n, k, seed)
    costs, compatible, _ = build_costs(
        world,
        config["cost_weights"],
        reserve_energy=float(config["reserve_energy"]),
    )
    graph, radius = scenario_graph(world, topology)
    distributed = topology != "shared_dual"
    scenario_id = str(task["scenario_id"])
    references = solve_references(world, costs, config, include_regularized=include_references)
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    common = _base_record(
        experiment=experiment,
        scenario_id=scenario_id,
        world=world,
        costs=costs,
        graph=graph,
        topology=topology,
        seed=seed,
        method="",
        method_family="fractional",
        is_primary=True,
        distributed=distributed,
    )
    common.update(
        {
            "effective_radius_m": radius,
            "compatible_pairs": int(np.sum(compatible)),
            "demand_utilization_payload": float(np.sum(world.requirements[:, 1]) / np.sum(world.resources[:, 1])),
            "demand_utilization_force": float(np.sum(world.requirements[:, 2]) / np.sum(world.resources[:, 2])),
        }
    )
    overrides = parameters_override or {}
    for method in FRACTIONAL_METHODS:
        params = dict(selected[method])
        params.update(overrides.get(method, {}))
        result = run_fractional_dynamics(
            world,
            costs,
            graph,
            method,
            distributed=distributed,
            parameters=params,
            budgets=budgets,
            operational_tolerances=config["convergence"]["operational"],
            refinement_tolerances=config["convergence"]["refinement"],
            entropy_tau=float(config["entropy_tau"]),
            consensus_gain=float(config["consensus"]["gain"]),
            use_integral_consensus=bool(config["consensus"]["integral"]),
            history_stride=int(task.get("history_stride", 50)),
            attempt_refinement=bool(task.get("attempt_refinement", True)),
        )
        terminal = result.history.iloc[-1].to_dict() if not result.history.empty else {}
        relaxed = evaluate_relaxed(world, result.x, costs)
        regularized = _regularized_objective(costs, result.x, float(config["entropy_tau"]))
        origin = argmax_round(result.x)
        native = evaluate_integer(world, origin, costs)
        recovery = None
        recovery_runtime = 0.0
        if include_recovery and result.operational_converged:
            started = time.perf_counter()
            recovery = repair_assignment_augmenting(
                world,
                origin,
                costs,
                max_chain_length=int(config["recovery"]["max_chain_length"]),
                max_nodes_per_augmentation=int(config["recovery"]["max_nodes_per_augmentation"]),
                candidates_per_load=int(config["recovery"]["candidates_per_load"]),
                prune=bool(config["recovery"]["prune"]),
                local_exchange=bool(config["recovery"]["local_exchange"]),
                compress=bool(config["recovery"]["compress"]),
            )
            recovery_runtime = time.perf_counter() - started
        integer = recovery.integer if recovery is not None else native
        lp_tau = references["lp_tau"]
        milp = references["milp"]
        lp_gap = math.nan
        if lp_tau is not None and lp_tau.status == 0 and float(terminal.get("primal_residual", math.inf)) <= 1e-6:
            lp_gap = (regularized - lp_tau.regularized_objective) / max(abs(lp_tau.regularized_objective), 1e-12)
        milp_certified = bool(
            milp is not None and milp.status == 0 and (not np.isfinite(milp.mip_gap) or milp.mip_gap <= 1e-9)
        )
        milp_gap = math.nan
        if milp_certified and integer.feasible:
            milp_gap = (integer.objective - milp.objective) / max(abs(milp.objective), 1e-12)
        exchanges = 2 if METHOD_KEYS[method] == "replicator" else 1
        recomputed = recompute_message_accounting(
            logical_rounds=int(result.counts["logical_rounds"]),
            graph_edges=graph.edges,
            n_loads=k,
            n_resources=world.requirements.shape[1],
            consensus_exchanges_per_round=exchanges,
            distributed=distributed,
        )
        accounting_ok = all(int(result.counts[key]) == int(value) for key, value in recomputed.items())
        row = {
            **common,
            "method": method,
            "parameters_json": json.dumps(params, sort_keys=True),
            "objective_raw": relaxed["objective"],
            "objective_regularized": regularized,
            "LP_tau_gap": lp_gap,
            "MILP_gap": milp_gap,
            "primal_feasibility": float(terminal.get("primal_residual", math.inf)) <= 1e-3,
            "integer_feasibility": integer.feasible if result.operational_converged else False,
            "native_integer_feasibility": native.feasible,
            "operational_converged": result.operational_converged,
            "refinement_converged": result.refinement_converged,
            "operational_round": result.operational_round,
            "refinement_round": result.refinement_round,
            "primal_residual": terminal.get("primal_residual", math.nan),
            "consensus_residual": terminal.get("consensus_residual", math.nan),
            "fixed_point_residual": terminal.get("fixed_point_residual", math.nan),
            "residual_semantics": "relative_normalized_primal|relative_laplacian_consensus|relative_method_fixed_point",
            "stop_reason": result.stop_reason,
            "censored": result.censored,
            "censoring_reason": result.censoring_reason,
            **result.counts,
            "wall_time_s": result.wall_time_s,
            "cpu_time_s": result.cpu_time_s,
            "peak_memory_mb": result.peak_memory_mb,
            "packets_per_robot": float(result.counts["packets_total"]) / n,
            "packets_per_edge": float(result.counts["packets_total"]) / max(graph.edges, 1),
            "packets_per_successful_solution": float(result.counts["packets_total"]) if integer.feasible else math.nan,
            "bytes_per_successful_solution": float(result.counts["payload_bytes_total"]) if integer.feasible else math.nan,
            "terminal_temperature": result.terminal_temperature,
            "entropy": result.entropy,
            "active_support": result.active_support,
            "concentration_round": result.concentration_round,
            "reactivation_round": result.reactivation_round,
            "simplex_violation": result.invariant_violations["simplex_violation"],
            "mask_violation": result.invariant_violations["mask_violation"],
            "nonnegativity_violation": result.invariant_violations["nonnegativity_violation"],
            "finite_state": result.invariant_violations["finite"],
            "message_accounting_recomputable": accounting_ok,
            "recovery_executed": recovery is not None,
            "recovery_skipped_nonconverged": bool(include_recovery and not result.operational_converged),
            "recovery_runtime_s": recovery_runtime,
            "recovery_chain_length": recovery.maximum_chain_length if recovery else 0,
            "recovery_nodes_expanded": recovery.nodes_explored if recovery else 0,
            "recovery_failure_reason": recovery.failure_reason if recovery else "skipped_nonconverged",
            "recovered_only_by_augmenting_path": bool(recovery and recovery.integer.feasible and not native.feasible),
            "fallback_used": False,
            "assignment_json": json.dumps(integer.assignment.tolist()) if result.operational_converged else "",
            "operator_scale_estimate": result.preconditioner.operator_scale_estimate,
            "step": result.preconditioner.step,
            "oracle_certified": milp_certified,
        }
        rows.append(row)
        for trace in result.history.to_dict(orient="records"):
            traces.append(
                {
                    "experiment": experiment,
                    "scenario_id": scenario_id,
                    "world_id": common["world_id"],
                    "world_hash": world.world_hash,
                    "seed": seed,
                    "n_robots": n,
                    "n_loads": k,
                    "topology": topology,
                    "method": method,
                    **trace,
                }
            )
        validations.append(
            {
                "experiment": experiment,
                "scenario_id": scenario_id,
                "world_id": common["world_id"],
                "method": method,
                "reported_packets": int(result.counts["packets_total"]),
                "recomputed_packets": recomputed["packets_total"],
                "reported_scalars": int(result.counts["scalar_transmissions_total"]),
                "recomputed_scalars": recomputed["scalar_transmissions_total"],
                "reported_bytes": int(result.counts["payload_bytes_total"]),
                "recomputed_bytes": recomputed["payload_bytes_total"],
                "valid": accounting_ok,
            }
        )
    if include_pure:
        pure = run_best_response_pure(
            world,
            costs,
            graph,
            parameters=selected["BestResponse-D"],
            budgets=budgets,
            consensus_tolerance=float(config["convergence"]["operational"]["consensus"]),
            seed=seed + 4049,
        )
        native = evaluate_integer(world, pure.assignment, costs)
        rows.append(
            {
                **common,
                "method": "BestResponse-pure",
                "method_family": "integer_async",
                "is_primary": False,
                "objective_raw": native.objective,
                "objective_regularized": math.nan,
                "primal_feasibility": native.feasible,
                "integer_feasibility": native.feasible,
                "operational_converged": pure.converged,
                "refinement_converged": False,
                "stop_reason": pure.stop_reason,
                "censored": pure.censored,
                "censoring_reason": pure.censoring_reason,
                **pure.counts,
                "wall_time_s": pure.wall_time_s,
                "cpu_time_s": pure.cpu_time_s,
                "peak_memory_mb": pure.peak_memory_mb,
                "simplex_violation": pure.invariant_violations["simplex_violation"],
                "mask_violation": pure.invariant_violations["mask_violation"],
                "nonnegativity_violation": pure.invariant_violations["nonnegativity_violation"],
                "finite_state": pure.invariant_violations["finite"],
                "unilateral_improvement": pure.unilateral_improvement,
                "recovery_executed": False,
                "recovery_skipped_nonconverged": False,
                "fallback_used": False,
                "assignment_json": json.dumps(pure.assignment.tolist()),
            }
        )
        for trace in pure.history.to_dict(orient="records"):
            traces.append(
                {
                    "experiment": experiment,
                    "scenario_id": scenario_id,
                    "world_id": common["world_id"],
                    "world_hash": world.world_hash,
                    "seed": seed,
                    "n_robots": n,
                    "n_loads": k,
                    "topology": topology,
                    "method": "BestResponse-pure",
                    **trace,
                }
            )
    if include_references:
        rows.extend(_reference_rows(common, world, costs, graph, references, include_auction=distributed))
    return {"runs": rows, "traces": traces, "message_validation": validations}


def _pad_warm_start(
    x: np.ndarray,
    dual: np.ndarray,
    tracker: np.ndarray,
    old_world: ResourceWorld,
    new_world: ResourceWorld,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n, old_k = x.shape
    new_k = new_world.n_loads
    if new_k == old_k:
        full = np.column_stack([x, np.maximum(1.0 - x.sum(axis=1), 0.0)])
        normalized_old = normalized_constraints(old_world)
        normalized_new = normalized_constraints(new_world)
        old_local = 1.0 / n - normalized_old * x[:, :, None]
        new_local = 1.0 / n - normalized_new * x[:, :, None]
        return full, dual.copy(), tracker + new_local - old_local
    if new_k != old_k + 1:
        raise ValueError("event warm start only supports unchanged K or one added load")
    epsilon = 1e-8
    idle = np.maximum(1.0 - x.sum(axis=1), 0.0)
    full = np.column_stack([x, np.full(n, epsilon), idle])
    full /= full.sum(axis=1, keepdims=True)
    dual_new = np.zeros((n, new_k, new_world.requirements.shape[1]), dtype=float)
    dual_new[:, :old_k] = dual
    normalized_new = normalized_constraints(new_world)
    tracker_new = 1.0 / n - normalized_new * full[:, :new_k, None]
    tracker_new[:, :old_k] = tracker
    return full, dual_new, tracker_new


def run_dynamic_event_task(
    config: Mapping[str, Any],
    selected: Mapping[str, Mapping[str, Any]],
    task: Mapping[str, Any],
    evaluation_budgets: DynamicsBudgets,
) -> dict[str, list[dict[str, Any]]]:
    n, k, seed = int(task["n"]), int(task["k"]), int(task["seed"])
    base_world, reserve_world = event_base_and_reserve(n, k, seed)
    base_costs, _, _ = build_costs(base_world, config["cost_weights"], reserve_energy=float(config["reserve_energy"]))
    base_graph, radius = scenario_graph(base_world, "rdisk_v2")
    event_round = int(round(evaluation_budgets.max_logical_rounds * float(config["evaluation"]["e75"]["event_fraction"])))
    base_budgets = DynamicsBudgets(
        max_logical_rounds=event_round,
        max_wall_time_s=evaluation_budgets.max_wall_time_s,
        max_scalar_transmissions=evaluation_budgets.max_scalar_transmissions,
        max_payoff_evaluations=evaluation_budgets.max_payoff_evaluations,
    )
    post_budgets = DynamicsBudgets(
        max_logical_rounds=evaluation_budgets.max_logical_rounds - event_round,
        max_wall_time_s=evaluation_budgets.max_wall_time_s,
        max_scalar_transmissions=evaluation_budgets.max_scalar_transmissions,
        max_payoff_evaluations=evaluation_budgets.max_payoff_evaluations,
    )
    base_results: dict[str, Any] = {}
    base_assignments: dict[str, np.ndarray] = {}
    for method in FRACTIONAL_METHODS:
        base_result = run_fractional_dynamics(
            base_world,
            base_costs,
            base_graph,
            method,
            distributed=True,
            parameters=selected[method],
            budgets=base_budgets,
            operational_tolerances=config["convergence"]["operational"],
            refinement_tolerances={"primal": 0.0, "consensus": 0.0, "fixed_point": 0.0},
            entropy_tau=float(config["entropy_tau"]),
            consensus_gain=float(config["consensus"]["gain"]),
            use_integral_consensus=bool(config["consensus"]["integral"]),
            history_stride=50,
            attempt_refinement=True,
        )
        base_results[method] = base_result
        base_assignments[method] = argmax_round(base_result.x)
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    for event in config["evaluation"]["e75"]["events"]:
        event_world, event_graph, event_meta = apply_event(base_world, reserve_world, base_graph, str(event))
        event_costs, _, _ = build_costs(event_world, config["cost_weights"], reserve_energy=float(config["reserve_energy"]))
        references = solve_references(event_world, event_costs, config, include_regularized=False)
        scenario_id = f"e75-N{n}-K{k}-S{seed}-{event}"
        common = _base_record(
            experiment="e75",
            scenario_id=scenario_id,
            world=event_world,
            costs=event_costs,
            graph=event_graph,
            topology=str(event),
            seed=seed,
            method="",
            method_family="fractional_dynamic_event",
            is_primary=True,
            distributed=True,
        )
        common.update({"event": event, "event_round": event_round, "base_world_hash": base_world.world_hash, "effective_radius_m": radius, **event_meta})
        for method in FRACTIONAL_METHODS:
            before = base_results[method]
            warm_x, warm_dual, warm_tracker = _pad_warm_start(
                before.x,
                before.dual,
                before.tracker,
                base_world,
                event_world,
            )
            result = run_fractional_dynamics(
                event_world,
                event_costs,
                event_graph,
                method,
                distributed=True,
                parameters=selected[method],
                budgets=post_budgets,
                operational_tolerances=config["convergence"]["operational"],
                refinement_tolerances=config["convergence"]["refinement"],
                entropy_tau=float(config["entropy_tau"]),
                consensus_gain=float(config["consensus"]["gain"]),
                use_integral_consensus=bool(config["consensus"]["integral"]),
                history_stride=25,
                initial_x=warm_x,
                initial_dual=warm_dual,
                initial_tracker=warm_tracker,
                attempt_refinement=True,
            )
            origin = argmax_round(result.x)
            recovery = None
            recovery_runtime = 0.0
            if result.operational_converged:
                started = time.perf_counter()
                recovery = repair_assignment_augmenting(
                    event_world,
                    origin,
                    event_costs,
                    max_chain_length=int(config["recovery"]["max_chain_length"]),
                    max_nodes_per_augmentation=int(config["recovery"]["max_nodes_per_augmentation"]),
                    candidates_per_load=int(config["recovery"]["candidates_per_load"]),
                    prune=bool(config["recovery"]["prune"]),
                    local_exchange=bool(config["recovery"]["local_exchange"]),
                    compress=bool(config["recovery"]["compress"]),
                )
                recovery_runtime = time.perf_counter() - started
            after_assignment = recovery.integer.assignment if recovery else origin
            after_integer = recovery.integer if recovery else evaluate_integer(event_world, origin, event_costs)
            before_assignment = base_assignments[method]
            before_full = np.zeros((n, event_world.n_loads + 1), dtype=float)
            after_full = np.zeros_like(before_full)
            before_index = np.where(before_assignment >= 0, before_assignment, event_world.n_loads)
            after_index = np.where(after_assignment >= 0, after_assignment, event_world.n_loads)
            before_full[np.arange(n), before_index] = 1.0
            after_full[np.arange(n), after_index] = 1.0
            recourse = 0.5 * float(np.sum(np.abs(after_full - before_full)))
            terminal = result.history.iloc[-1].to_dict() if not result.history.empty else {}
            feasible_trace = result.history[result.history["primal_residual"] <= float(config["convergence"]["operational"]["primal"])] if not result.history.empty else pd.DataFrame()
            first_feasible = int(feasible_trace.iloc[0]["logical_round"]) if not feasible_trace.empty else math.nan
            objectives = result.history.get("objective_raw", pd.Series(dtype=float)).to_numpy(dtype=float)
            rounds = result.history.get("logical_round", pd.Series(dtype=float)).to_numpy(dtype=float)
            final_objective = float(objectives[-1]) if objectives.size else math.nan
            cumulative_loss = float(np.trapz(np.maximum(objectives - final_objective, 0.0), rounds)) if objectives.size > 1 else 0.0
            exchanges = 2 if METHOD_KEYS[method] == "replicator" else 1
            recomputed = recompute_message_accounting(
                logical_rounds=int(result.counts["logical_rounds"]),
                graph_edges=event_graph.edges,
                n_loads=event_world.n_loads,
                n_resources=event_world.requirements.shape[1],
                consensus_exchanges_per_round=exchanges,
                distributed=True,
            )
            accounting_ok = all(int(result.counts[key]) == int(value) for key, value in recomputed.items())
            milp = references["milp"]
            certified = bool(milp is not None and milp.status == 0 and (not np.isfinite(milp.mip_gap) or milp.mip_gap <= 1e-9))
            milp_gap = (
                (after_integer.objective - milp.objective) / max(abs(milp.objective), 1e-12)
                if certified and after_integer.feasible
                else math.nan
            )
            rows.append(
                {
                    **common,
                    "method": method,
                    "pre_event_operational_converged": before.operational_converged,
                    "valid_event_origin": before.operational_converged,
                    "operational_converged": result.operational_converged,
                    "refinement_converged": result.refinement_converged,
                    "operational_round": result.operational_round,
                    "refinement_round": result.refinement_round,
                    "recovery_rounds": result.operational_round,
                    "recovery_wall_time": result.wall_time_s,
                    "recovery_packets": result.counts["packets_total"],
                    "recovery_bytes": result.counts["payload_bytes_total"],
                    "number_of_reassigned_robots": int(recourse),
                    "hamming_recourse": recourse,
                    "cumulative_objective_loss": cumulative_loss,
                    "transient_feasible_fraction": float(np.mean(result.history["primal_residual"] <= float(config["convergence"]["operational"]["primal"]))) if not result.history.empty else 0.0,
                    "time_to_new_feasible_solution": first_feasible,
                    "time_to_epsilon_stationary": result.operational_round,
                    "reactivation_round": result.reactivation_round,
                    "objective_raw": evaluate_relaxed(event_world, result.x, event_costs)["objective"],
                    "objective_regularized": _regularized_objective(event_costs, result.x, float(config["entropy_tau"])),
                    "MILP_gap": milp_gap,
                    "integer_feasibility": after_integer.feasible if result.operational_converged else False,
                    "primal_feasibility": float(terminal.get("primal_residual", math.inf)) <= 1e-3,
                    "primal_residual": terminal.get("primal_residual", math.nan),
                    "consensus_residual": terminal.get("consensus_residual", math.nan),
                    "fixed_point_residual": terminal.get("fixed_point_residual", math.nan),
                    "censored": result.censored,
                    "censoring_reason": result.censoring_reason,
                    "stop_reason": result.stop_reason,
                    **result.counts,
                    "wall_time_s": result.wall_time_s,
                    "cpu_time_s": result.cpu_time_s,
                    "peak_memory_mb": result.peak_memory_mb,
                    "simplex_violation": result.invariant_violations["simplex_violation"],
                    "mask_violation": result.invariant_violations["mask_violation"],
                    "nonnegativity_violation": result.invariant_violations["nonnegativity_violation"],
                    "finite_state": result.invariant_violations["finite"],
                    "message_accounting_recomputable": accounting_ok,
                    "recovery_executed": recovery is not None,
                    "recovery_skipped_nonconverged": not result.operational_converged,
                    "recovery_runtime_s": recovery_runtime,
                    "recovery_chain_length": recovery.maximum_chain_length if recovery else 0,
                    "recovery_nodes_expanded": recovery.nodes_explored if recovery else 0,
                    "recovered_only_by_augmenting_path": bool(recovery and recovery.integer.feasible and not evaluate_integer(event_world, origin, event_costs).feasible),
                    "fallback_used": False,
                    "assignment_json": json.dumps(after_assignment.tolist()) if result.operational_converged else "",
                    "oracle_certified": certified,
                }
            )
            for trace in result.history.to_dict(orient="records"):
                traces.append(
                    {
                        "experiment": "e75",
                        "scenario_id": scenario_id,
                        "world_id": common["world_id"],
                        "world_hash": event_world.world_hash,
                        "seed": seed,
                        "n_robots": n,
                        "n_loads": event_world.n_loads,
                        "topology": str(event),
                        "event": event,
                        "method": method,
                        **trace,
                    }
                )
            validations.append(
                {
                    "experiment": "e75",
                    "scenario_id": scenario_id,
                    "world_id": common["world_id"],
                    "method": method,
                    "reported_packets": int(result.counts["packets_total"]),
                    "recomputed_packets": recomputed["packets_total"],
                    "reported_scalars": int(result.counts["scalar_transmissions_total"]),
                    "recomputed_scalars": recomputed["scalar_transmissions_total"],
                    "reported_bytes": int(result.counts["payload_bytes_total"]),
                    "recomputed_bytes": recomputed["payload_bytes_total"],
                    "valid": accounting_ok,
                }
            )
    return {"runs": rows, "traces": traces, "message_validation": validations}


__all__ = [
    "apply_event",
    "controlled_utilization_world",
    "degraded_connected_graph",
    "deterministic_case_catalog",
    "event_base_and_reserve",
    "graph_from_adjacency",
    "graph_metrics",
    "run_dynamic_event_task",
    "run_fractional_scenario",
    "scenario_graph",
    "stable_hash",
    "target_degree_rdisk",
]
