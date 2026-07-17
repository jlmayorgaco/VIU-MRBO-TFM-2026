"""Reproducible SP7 traffic experiment for rigid payload coalitions."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import stats
import yaml

from viu_mrob_tfm.sp7.theory import (
    RouteResources,
    all_profiles,
    asynchronous_better_response,
    base_cost,
    conflict_free_penalty_threshold,
    conflict_pairs,
    is_pure_nash,
    potential,
    pure_nash_profiles,
    verify_exact_potential_identity,
)


METHODS = (
    "local_potential_reservation",
    "no_congestion_penalty",
    "no_zone_reservation",
    "prioritized_planning",
    "central_restricted_oracle",
)

METHOD_LABELS = {
    "local_potential_reservation": "Juego + reserva local",
    "no_congestion_penalty": "Sin penalización de congestión",
    "no_zone_reservation": "Sin reserva de zona",
    "prioritized_planning": "Planificación priorizada",
    "central_restricted_oracle": "Oráculo restringido",
}

SCENARIO_LABELS = {
    "crossing": "Cruce",
    "bidirectional_corridor": "Pasillo bidireccional",
    "dynamic_bottleneck": "Cuello dinámico",
}


@dataclass(frozen=True, slots=True)
class TrafficWorld:
    scenario: str
    n_coalitions: int
    seed: int
    paths: tuple[tuple[tuple[str, ...], ...], ...]
    base_costs: np.ndarray
    route_resources: RouteResources
    node_zones: dict[str, str]
    priorities: np.ndarray
    penalty: float
    horizon_steps: int
    deadlock_window: int
    clearance_steps: int
    dynamic_blocks: tuple[tuple[int, str], ...]
    compound_radius_m: float
    cell_size_m: float
    world_hash: str

    def blocked_nodes(self, step: int) -> set[str]:
        return {node for blocked_step, node in self.dynamic_blocks if blocked_step == int(step)}


@dataclass(frozen=True, slots=True)
class ScheduleOutcome:
    delivered_count: int
    delivery_success: bool
    deadlock: bool
    timeout: bool
    makespan_steps: int
    sum_arrival_steps: int
    total_wait_steps: int
    conflict_denials: int
    zone_denials: int
    messages: int
    collision_violations: int
    min_logical_separation_cells: int


def run_sp7_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    experiment_id = str(config["experiment_id"])
    output_dir = Path(config.get("output_dir", f"results/processed/sp7/{experiment_id}"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "tables").mkdir(exist_ok=True)
    (output_dir / "figures").mkdir(exist_ok=True)

    scenarios = [str(value) for value in config["scenarios"]]
    coalition_counts = [int(value) for value in config["coalition_counts"]]
    seeds = _expand_seeds(config["seeds"])
    methods = [str(value) for value in config.get("methods", METHODS)]
    if set(methods) != set(METHODS):
        raise ValueError(f"Canonical SP7 requires exactly these methods: {METHODS}")

    rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        if scenario not in SCENARIO_LABELS:
            raise ValueError(f"Unknown SP7 scenario: {scenario}")
        for n_coalitions in coalition_counts:
            for seed in seeds:
                world = generate_world(scenario, n_coalitions, seed)
                theory = audit_world_theory(world)
                theory_rows.append(theory)
                oracle_started = perf_counter()
                oracle_cache = restricted_schedule_oracle(world)
                oracle_runtime_ms = 1000.0 * (perf_counter() - oracle_started)
                for method in methods:
                    rows.append(simulate_method(world, method, theory, oracle_cache, oracle_runtime_ms))

    runs = pd.DataFrame(rows)
    theory_df = pd.DataFrame(theory_rows)
    summary = summarize_runs(runs)
    hypotheses = evaluate_hypotheses(runs)
    audit = build_audit(config, runs, theory_df, scenarios, coalition_counts, seeds, methods)

    runs.to_csv(output_dir / "tables" / "runs.csv", index=False)
    theory_df.to_csv(output_dir / "tables" / "theory_checks.csv", index=False)
    summary.to_csv(output_dir / "tables" / "summary.csv", index=False)
    hypotheses.to_csv(output_dir / "tables" / "hypotheses.csv", index=False)
    _write_latex_tables(output_dir, runs, summary, hypotheses)
    _plot_results(output_dir, runs)
    (output_dir / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "report.md").write_text(_report(experiment_id, runs, summary, hypotheses, audit), encoding="utf-8")
    manifest = {
        "experiment_id": experiment_id,
        "config_path": str(path),
        "output_dir": str(output_dir),
        "scenarios": scenarios,
        "coalition_counts": coalition_counts,
        "seeds": seeds,
        "methods": methods,
        "worlds": int(len(theory_df)),
        "runs": int(len(runs)),
        "evidence_level": "C",
        "audit": str(output_dir / "audit.json"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "gpu_used": False,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def generate_world(scenario: str, n_coalitions: int, seed: int) -> TrafficWorld:
    if scenario not in SCENARIO_LABELS:
        raise ValueError(f"Unknown SP7 scenario: {scenario}")
    if not 2 <= int(n_coalitions) <= 4:
        raise ValueError("The canonical SP7 campaign supports two to four coalitions.")
    stable_offset = int.from_bytes(hashlib.sha256(scenario.encode("utf-8")).digest()[:4], "little")
    rng = np.random.default_rng(int(seed) + stable_offset + 1013 * int(n_coalitions))
    paths: list[tuple[tuple[str, ...], ...]] = []
    node_zones: dict[str, str] = {}
    for agent in range(int(n_coalitions)):
        start, pre, post, goal = f"S{agent}", f"P{agent}", f"Q{agent}", f"G{agent}"
        if scenario == "crossing":
            direct = (start, pre, "C", post, goal)
            detour = (start, f"D{agent}a", f"D{agent}b", f"D{agent}c", post, goal)
            node_zones["C"] = "core"
        elif scenario == "bidirectional_corridor":
            core = ("C1", "C2") if agent % 2 == 0 else ("C2", "C1")
            direct = (start, pre, *core, post, goal)
            detour = (
                start,
                f"D{agent}a",
                f"D{agent}b",
                f"D{agent}c",
                f"D{agent}d",
                f"D{agent}e",
                post,
                goal,
            )
            node_zones.update({"C1": "core", "C2": "core"})
        else:
            direct = (start, pre, "B", post, goal)
            detour = (start, f"D{agent}a", f"D{agent}b", f"D{agent}c", f"D{agent}d", f"D{agent}e", post, goal)
            node_zones["B"] = "core"
        paths.append((direct, detour))

    base_costs = np.asarray(
        [
            [len(agent_paths[0]) - 1 + rng.uniform(0.0, 0.12), len(agent_paths[1]) - 1 + rng.uniform(0.0, 0.12)]
            for agent_paths in paths
        ],
        dtype=float,
    )
    route_resources: RouteResources = tuple(
        tuple(frozenset({"core"}) if any(node in node_zones for node in path) else frozenset() for path in agent_paths)
        for agent_paths in paths
    )
    priorities = rng.uniform(0.0, 1.0, size=int(n_coalitions))
    dynamic_blocks: tuple[tuple[int, str], ...] = ()
    if scenario == "dynamic_bottleneck":
        start_step = 2 + int(rng.integers(0, 2))
        dynamic_blocks = tuple((step, "B") for step in range(start_step, start_step + 3))
    compound_radius_m = float(rng.uniform(0.52, 0.68))
    payload = {
        "scenario": scenario,
        "n_coalitions": int(n_coalitions),
        "seed": int(seed),
        "paths": paths,
        "base_costs": base_costs.round(12).tolist(),
        "priorities": priorities.round(12).tolist(),
        "dynamic_blocks": dynamic_blocks,
        "compound_radius_m": round(compound_radius_m, 12),
    }
    world_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return TrafficWorld(
        scenario=scenario,
        n_coalitions=int(n_coalitions),
        seed=int(seed),
        paths=tuple(paths),
        base_costs=base_costs,
        route_resources=route_resources,
        node_zones=node_zones,
        priorities=priorities,
        penalty=1.6,
        horizon_steps=48,
        deadlock_window=8,
        clearance_steps=1,
        dynamic_blocks=dynamic_blocks,
        compound_radius_m=compound_radius_m,
        cell_size_m=1.0,
        world_hash=world_hash,
    )


def audit_world_theory(world: TrafficWorld) -> dict[str, Any]:
    result = asynchronous_better_response(
        world.base_costs,
        world.route_resources,
        world.penalty,
        seed=world.seed + 17,
    )
    threshold = conflict_free_penalty_threshold(world.base_costs, world.route_resources)
    equilibria = pure_nash_profiles(world.base_costs, world.route_resources, world.penalty)
    condition_met = bool(np.isfinite(threshold) and world.penalty > threshold + 1e-10)
    return {
        "world_hash": world.world_hash,
        "scenario": world.scenario,
        "n_coalitions": world.n_coalitions,
        "seed": world.seed,
        "penalty": world.penalty,
        "conflict_free_threshold": threshold,
        "threshold_condition_met": condition_met,
        "exact_potential_verified": verify_exact_potential_identity(
            world.base_costs, world.route_resources, world.penalty
        ),
        "potential_monotone": bool(np.all(np.diff(result.potential_trace) > 0.0)),
        "better_response_ends_at_nash": is_pure_nash(
            result.profile, world.base_costs, world.route_resources, world.penalty
        ),
        "strict_moves": result.strict_moves,
        "finite_profile_bound": int(np.prod([len(routes) for routes in world.route_resources])) - 1,
        "final_conflict_pairs": conflict_pairs(result.profile, world.route_resources),
        "pure_nash_count": len(equilibria),
        "conditional_all_nash_conflict_free": bool(
            (not condition_met) or all(conflict_pairs(profile, world.route_resources) == 0 for profile in equilibria)
        ),
    }


def simulate_schedule(
    world: TrafficWorld,
    profile: np.ndarray,
    *,
    use_zone_reservation: bool,
    priority_mode: str,
    fixed_order: tuple[int, ...] | None = None,
) -> ScheduleOutcome:
    routes = [world.paths[agent][int(route)] for agent, route in enumerate(np.asarray(profile, dtype=int))]
    positions = np.zeros(world.n_coalitions, dtype=int)
    delivered = np.zeros(world.n_coalitions, dtype=bool)
    arrivals = np.full(world.n_coalitions, world.horizon_steps, dtype=int)
    waiting = np.zeros(world.n_coalitions, dtype=int)
    token_owner: dict[str, int] = {}
    release_at: dict[str, int] = {}
    messages = 0
    conflict_denials = 0
    zone_denials = 0
    collision_violations = 0
    stagnant = 0
    deadlock = False
    rank = {agent: index for index, agent in enumerate(fixed_order or tuple(range(world.n_coalitions)))}

    def key(agent: int) -> tuple[float, float, int]:
        if priority_mode == "fixed":
            return (-float(rank[agent]), float(world.priorities[agent]), -agent)
        return (float(waiting[agent]), float(world.priorities[agent]), -agent)

    last_step = 0
    for step in range(world.horizon_steps):
        last_step = step
        for zone in list(token_owner):
            if release_at.get(zone, world.horizon_steps + 1) <= step:
                token_owner.pop(zone, None)
                release_at.pop(zone, None)

        active = [agent for agent in range(world.n_coalitions) if not delivered[agent]]
        if not active:
            break
        current = {agent: routes[agent][int(positions[agent])] for agent in active}
        target = {agent: routes[agent][int(positions[agent]) + 1] for agent in active}
        blocked = world.blocked_nodes(step)
        allowed = {agent for agent in active if target[agent] not in blocked}
        conflict_denials += len(active) - len(allowed)

        if use_zone_reservation:
            contenders: dict[str, list[int]] = {}
            for agent in active:
                next_zone = world.node_zones.get(target[agent])
                current_zone = world.node_zones.get(current[agent])
                if next_zone is not None and current_zone != next_zone:
                    contenders.setdefault(next_zone, []).append(agent)
            for zone, agents in contenders.items():
                owner = token_owner.get(zone)
                if owner is None:
                    owner = max(agents, key=key)
                    token_owner[zone] = owner
                    release_at.pop(zone, None)
                    messages += 2 * len(agents)
                for agent in agents:
                    if agent != owner and agent in allowed:
                        allowed.remove(agent)
                        zone_denials += 1
            for agent in active:
                next_zone = world.node_zones.get(target[agent])
                if next_zone is not None and token_owner.get(next_zone) not in (None, agent) and agent in allowed:
                    allowed.remove(agent)
                    zone_denials += 1

        by_target: dict[str, list[int]] = {}
        for agent in allowed:
            by_target.setdefault(target[agent], []).append(agent)
        for agents in by_target.values():
            if len(agents) <= 1:
                continue
            winner = max(agents, key=key)
            for agent in agents:
                if agent != winner:
                    allowed.remove(agent)
                    conflict_denials += 1
            messages += 2 * len(agents)

        for agent in list(allowed):
            for other in list(allowed):
                if agent < other and target[agent] == current[other] and target[other] == current[agent]:
                    allowed.discard(agent)
                    allowed.discard(other)
                    conflict_denials += 2

        changed = True
        while changed:
            changed = False
            stationary_nodes = {current[agent] for agent in active if agent not in allowed}
            for agent in list(allowed):
                if target[agent] in stationary_nodes:
                    allowed.remove(agent)
                    conflict_denials += 1
                    changed = True

        moved = 0
        for agent in active:
            if agent in allowed:
                old_node = current[agent]
                positions[agent] += 1
                new_node = routes[agent][int(positions[agent])]
                moved += 1
                old_zone = world.node_zones.get(old_node)
                new_zone = world.node_zones.get(new_node)
                if use_zone_reservation and old_zone is not None and old_zone != new_zone and token_owner.get(old_zone) == agent:
                    release_at[old_zone] = step + world.clearance_steps + 1
                if positions[agent] == len(routes[agent]) - 1:
                    delivered[agent] = True
                    arrivals[agent] = step + 1
            else:
                waiting[agent] += 1

        occupied = [routes[agent][int(positions[agent])] for agent in range(world.n_coalitions) if not delivered[agent]]
        collision_violations += len(occupied) - len(set(occupied))
        stagnant = stagnant + 1 if moved == 0 else 0
        dynamic_still_active = any(block_step >= step for block_step, _ in world.dynamic_blocks)
        if stagnant >= world.deadlock_window and not dynamic_still_active:
            deadlock = True
            break

    delivered_count = int(np.sum(delivered))
    success = delivered_count == world.n_coalitions
    makespan = int(np.max(arrivals)) if success else world.horizon_steps
    sum_arrival = int(np.sum(arrivals))
    return ScheduleOutcome(
        delivered_count=delivered_count,
        delivery_success=success,
        deadlock=deadlock,
        timeout=bool(not success and not deadlock and last_step >= world.horizon_steps - 1),
        makespan_steps=makespan,
        sum_arrival_steps=sum_arrival,
        total_wait_steps=int(np.sum(waiting)),
        conflict_denials=conflict_denials,
        zone_denials=zone_denials,
        messages=messages,
        collision_violations=collision_violations,
        min_logical_separation_cells=0 if collision_violations else 1,
    )


def restricted_schedule_oracle(world: TrafficWorld) -> tuple[ScheduleOutcome, np.ndarray, tuple[int, ...], int]:
    best: tuple[tuple[float, ...], ScheduleOutcome, np.ndarray, tuple[int, ...]] | None = None
    evaluated = 0
    for profile in all_profiles(world.route_resources):
        for order in permutations(range(world.n_coalitions)):
            evaluated += 1
            outcome = simulate_schedule(
                world,
                profile,
                use_zone_reservation=True,
                priority_mode="fixed",
                fixed_order=tuple(order),
            )
            score = (
                float(world.n_coalitions - outcome.delivered_count),
                float(outcome.makespan_steps),
                float(outcome.sum_arrival_steps),
                base_cost(profile, world.base_costs),
                *[float(value) for value in profile],
                *[float(value) for value in order],
            )
            if best is None or score < best[0]:
                best = (score, outcome, profile.copy(), tuple(order))
    if best is None:
        raise RuntimeError("The restricted SP7 oracle evaluated no schedule.")
    return best[1], best[2], best[3], evaluated


def simulate_method(
    world: TrafficWorld,
    method: str,
    theory: dict[str, Any],
    oracle_cache: tuple[ScheduleOutcome, np.ndarray, tuple[int, ...], int],
    oracle_runtime_ms: float,
) -> dict[str, Any]:
    started = perf_counter()
    response = asynchronous_better_response(
        world.base_costs,
        world.route_resources,
        world.penalty,
        seed=world.seed + 17,
    )
    oracle_outcome, oracle_profile, oracle_order, oracle_evaluations = oracle_cache
    if method == "local_potential_reservation":
        profile = response.profile
        outcome = simulate_schedule(world, profile, use_zone_reservation=True, priority_mode="aging")
        strategic_messages = 2 * response.activations
        revisions = response.strict_moves
    elif method == "no_congestion_penalty":
        profile = np.zeros(world.n_coalitions, dtype=int)
        outcome = simulate_schedule(world, profile, use_zone_reservation=True, priority_mode="aging")
        strategic_messages = 0
        revisions = 0
    elif method == "no_zone_reservation":
        profile = response.profile
        outcome = simulate_schedule(world, profile, use_zone_reservation=False, priority_mode="aging")
        strategic_messages = 2 * response.activations
        revisions = response.strict_moves
    elif method == "prioritized_planning":
        profile = np.zeros(world.n_coalitions, dtype=int)
        order = tuple(int(agent) for agent in np.argsort(-world.priorities))
        outcome = simulate_schedule(
            world, profile, use_zone_reservation=True, priority_mode="fixed", fixed_order=order
        )
        strategic_messages = world.n_coalitions * max(world.n_coalitions - 1, 0)
        revisions = 0
    elif method == "central_restricted_oracle":
        profile = oracle_profile
        outcome = oracle_outcome
        strategic_messages = world.n_coalitions * 3
        revisions = int(np.sum(profile != 0))
    else:
        raise ValueError(f"Unknown SP7 method: {method}")

    route_cost_value = base_cost(profile, world.base_costs)
    oracle_route_cost = base_cost(oracle_profile, world.base_costs)
    return {
        "scenario": world.scenario,
        "scenario_label": SCENARIO_LABELS[world.scenario],
        "n_coalitions": world.n_coalitions,
        "seed": world.seed,
        "world_hash": world.world_hash,
        "method": method,
        "method_label": METHOD_LABELS[method],
        "delivery_success": outcome.delivery_success,
        "delivered_fraction": outcome.delivered_count / world.n_coalitions,
        "deadlock": outcome.deadlock,
        "timeout": outcome.timeout,
        "makespan_steps": outcome.makespan_steps,
        "sum_arrival_steps": outcome.sum_arrival_steps,
        "total_wait_steps": outcome.total_wait_steps,
        "conflict_denials": outcome.conflict_denials,
        "zone_denials": outcome.zone_denials,
        "messages": outcome.messages + strategic_messages,
        "collision_violations": outcome.collision_violations,
        "min_logical_separation_cells": outcome.min_logical_separation_cells,
        "route_revisions": revisions,
        "route_conflict_pairs": conflict_pairs(profile, world.route_resources),
        "route_base_cost": route_cost_value,
        "route_potential": potential(profile, world.base_costs, world.route_resources, world.penalty),
        "makespan_gap_vs_restricted_oracle": (
            (outcome.makespan_steps - oracle_outcome.makespan_steps) / max(oracle_outcome.makespan_steps, 1)
        ),
        "route_cost_gap_vs_restricted_oracle": (
            (route_cost_value - oracle_route_cost) / max(oracle_route_cost, 1e-12)
        ),
        "oracle_candidates_evaluated": oracle_evaluations,
        "compound_radius_m": world.compound_radius_m,
        "cell_size_m": world.cell_size_m,
        "clearance_steps": world.clearance_steps,
        "potential_monotone": theory["potential_monotone"],
        "final_pure_nash": theory["better_response_ends_at_nash"],
        "runtime_ms": (
            float(oracle_runtime_ms)
            if method == "central_restricted_oracle"
            else 1000.0 * (perf_counter() - started)
        ),
    }


def summarize_runs(runs: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "delivery_success",
        "delivered_fraction",
        "deadlock",
        "makespan_steps",
        "total_wait_steps",
        "messages",
        "route_conflict_pairs",
        "makespan_gap_vs_restricted_oracle",
        "runtime_ms",
    ]
    rows: list[dict[str, Any]] = []
    for method, group in runs.groupby("method", sort=False):
        row: dict[str, Any] = {"method": method, "method_label": METHOD_LABELS[str(method)], "n": len(group)}
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if values.size else math.nan
            low, high = _bootstrap_mean_ci(values, seed=20260718)
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_hypotheses(runs: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("H7.1", "delivery_success", "local_potential_reservation", "no_zone_reservation", "greater", "mcnemar", False),
        ("H7.2", "makespan_steps", "local_potential_reservation", "no_congestion_penalty", "less", "wilcoxon", True),
        ("H7.3", "makespan_steps", "local_potential_reservation", "central_restricted_oracle", "greater", "wilcoxon", True),
    ]
    rows: list[dict[str, Any]] = []
    for hid, metric, method_a, method_b, direction, test, successful_only in specs:
        paired = _paired(runs, metric, method_a, method_b, successful_only=successful_only)
        a = paired[method_a].to_numpy(dtype=float)
        b = paired[method_b].to_numpy(dtype=float)
        diff = a - b
        if test == "mcnemar":
            favorable = int(np.sum((a == 1) & (b == 0)))
            adverse = int(np.sum((a == 0) & (b == 1)))
            p_value = (
                float(stats.binomtest(favorable, favorable + adverse, 0.5, alternative="greater").pvalue)
                if favorable + adverse
                else 1.0
            )
        else:
            nonzero = diff[np.abs(diff) > 1e-12]
            p_value = (
                float(stats.wilcoxon(nonzero, alternative=direction, zero_method="wilcox").pvalue)
                if nonzero.size
                else 1.0
            )
        low, high = _bootstrap_mean_ci(diff, seed=20260719)
        rows.append(
            {
                "id": hid,
                "metric": metric,
                "method_a": method_a,
                "method_b": method_b,
                "direction": direction,
                "test": test,
                "successful_pairs_only": successful_only,
                "n_pairs": len(diff),
                "effect_a_minus_b": float(np.mean(diff)) if diff.size else math.nan,
                "ci95_low": low,
                "ci95_high": high,
                "p_raw": p_value,
            }
        )
    adjusted = _holm([float(row["p_raw"]) for row in rows])
    for row, p_holm in zip(rows, adjusted, strict=True):
        row["p_holm"] = p_holm
        row["reject_holm"] = bool(p_holm < 0.05)
    return pd.DataFrame(rows)


def build_audit(
    config: dict[str, Any],
    runs: pd.DataFrame,
    theory: pd.DataFrame,
    scenarios: list[str],
    coalition_counts: list[int],
    seeds: list[int],
    methods: list[str],
) -> dict[str, Any]:
    expected_worlds = len(scenarios) * len(coalition_counts) * len(seeds)
    expected_runs = expected_worlds * len(methods)
    paired_counts = runs.groupby("world_hash")["method"].nunique()
    numeric = runs[
        ["delivered_fraction", "makespan_steps", "total_wait_steps", "messages", "route_conflict_pairs", "runtime_ms"]
    ].to_numpy(dtype=float)
    checks = {
        "world_count": len(theory) == expected_worlds,
        "run_count": len(runs) == expected_runs,
        "paired_methods": bool((paired_counts == len(methods)).all()),
        "world_hash_unique": theory["world_hash"].nunique() == expected_worlds,
        "finite_primary_metrics": bool(np.isfinite(numeric).all()),
        "exact_potential_identity": bool(theory["exact_potential_verified"].all()),
        "strict_potential_monotonicity": bool(theory["potential_monotone"].all()),
        "better_response_ends_at_nash": bool(theory["better_response_ends_at_nash"].all()),
        "finite_profile_move_bound": bool((theory["strict_moves"] <= theory["finite_profile_bound"]).all()),
        "conditional_conflict_free_result": bool(theory["conditional_all_nash_conflict_free"].all()),
        "logical_collision_exclusion": bool((runs["collision_violations"] == 0).all()),
        "restricted_oracle_delivers": bool(
            runs[runs["method"] == "central_restricted_oracle"]["delivery_success"].all()
        ),
        "no_pose_repair": True,
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "evidence_level": "C",
        "primary_branch": "SP7-C rigid compound bodies on an inflated configuration graph",
        "worlds": expected_worlds,
        "runs": expected_runs,
        "model_scope": "finite route game plus sampled exclusive-resource traffic abstraction",
        "not_claimed": (
            "No CBS/ECBS or ORCA reproduction, continuous collision-avoidance proof, contact dynamics, "
            "hardware validation, packet-loss robustness, global MAPF optimality or industrial deadlock freedom is claimed."
        ),
        "historical_campaign_used": False,
        "config_protocol": config.get("protocol_family", "sp7_route_reservation_v1"),
    }


def _paired(
    runs: pd.DataFrame,
    metric: str,
    method_a: str,
    method_b: str,
    *,
    successful_only: bool,
) -> pd.DataFrame:
    selected = runs[runs["method"].isin([method_a, method_b])].copy()
    values = selected.pivot(index="world_hash", columns="method", values=metric)
    if successful_only:
        success = selected.pivot(index="world_hash", columns="method", values="delivery_success")
        valid = success[method_a].astype(bool) & success[method_b].astype(bool)
        values = values.loc[valid]
    return values[[method_a, method_b]].dropna()


def _bootstrap_mean_ci(values: np.ndarray, *, seed: int, reps: int = 2000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return math.nan, math.nan
    if values.size == 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(values, size=(reps, values.size), replace=True), axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.ones(len(p_values), dtype=float)
    running = 0.0
    for rank_index, index in enumerate(order):
        value = min(1.0, (len(p_values) - rank_index) * p_values[int(index)])
        running = max(running, value)
        adjusted[int(index)] = running
    return adjusted.tolist()


def _write_latex_tables(output_dir: Path, runs: pd.DataFrame, summary: pd.DataFrame, hypotheses: pd.DataFrame) -> None:
    tables = output_dir / "tables"
    proposed = runs[runs["method"] == "local_potential_reservation"]
    no_reservation = runs[runs["method"] == "no_zone_reservation"]
    oracle = runs[runs["method"] == "central_restricted_oracle"]
    corridor_no_reservation = no_reservation[no_reservation["scenario"] == "bidirectional_corridor"]
    h1, h2, h3 = (hypotheses[hypotheses["id"] == hid].iloc[0] for hid in ("H7.1", "H7.2", "H7.3"))
    numbers = (
        f"\\newcommand{{\\SPSevenWorlds}}{{{runs['world_hash'].nunique()}}}\n"
        f"\\newcommand{{\\SPSevenRuns}}{{{len(runs)}}}\n"
        f"\\newcommand{{\\SPSevenProposedSuccess}}{{{proposed['delivery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenNoReservationSuccess}}{{{no_reservation['delivery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenOracleSuccess}}{{{oracle['delivery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenOracleMakespan}}{{{oracle['makespan_steps'].mean():.2f}}}\n"
        f"\\newcommand{{\\SPSevenProposedMakespan}}{{{proposed['makespan_steps'].mean():.2f}}}\n"
        f"\\newcommand{{\\SPSevenProposedMessages}}{{{proposed['messages'].mean():.1f}}}\n"
        f"\\newcommand{{\\SPSevenProposedRuntime}}{{{proposed['runtime_ms'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenOracleRuntime}}{{{oracle['runtime_ms'].mean():.2f}}}\n"
        f"\\newcommand{{\\SPSevenProposedRoutePairs}}{{{proposed['route_conflict_pairs'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenCorridorNoReservationSuccess}}{{{corridor_no_reservation['delivery_success'].mean():.3f}}}\n"
        f"\\newcommand{{\\SPSevenHOneEffect}}{{{h1['effect_a_minus_b']:.3f}}}\n"
        f"\\newcommand{{\\SPSevenHOneEffectPP}}{{{100.0 * h1['effect_a_minus_b']:.1f}}}\n"
        f"\\newcommand{{\\SPSevenHOneCI}}{{[{h1['ci95_low']:.3f}; {h1['ci95_high']:.3f}]}}\n"
        f"\\newcommand{{\\SPSevenHOnePHolm}}{{{_latex_scientific(float(h1['p_holm']))}}}\n"
        f"\\newcommand{{\\SPSevenHTwoEffect}}{{{h2['effect_a_minus_b']:.2f}}}\n"
        f"\\newcommand{{\\SPSevenHTwoPHolm}}{{{_latex_scientific(float(h2['p_holm']))}}}\n"
        f"\\newcommand{{\\SPSevenHThreeEffect}}{{{h3['effect_a_minus_b']:.2f}}}\n"
        f"\\newcommand{{\\SPSevenHThreePHolm}}{{{_latex_scientific(float(h3['p_holm']))}}}\n"
    )
    (tables / "sp7_numbers.tex").write_text(numbers, encoding="utf-8")

    lines = [
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Método & Entrega & Interbloqueo & Terminación & Espera & Mensajes \\\\",
        "\\midrule",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"{row['method_label']} & {row['delivery_success_mean']:.3f} & {row['deadlock_mean']:.3f} & "
            f"{row['makespan_steps_mean']:.2f} & {row['total_wait_steps_mean']:.2f} & {row['messages_mean']:.1f} \\\\"
        )
    lines += ["\\bottomrule", "\\end{tabular}"]
    (tables / "sp7_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    hlines = [
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "ID & Métrica & $n$ & Efecto $A-B$ & IC 95\\% & $p_{Holm}$ \\\\",
        "\\midrule",
    ]
    labels = {"delivery_success": "entrega", "makespan_steps": "tiempo de terminación"}
    for _, row in hypotheses.iterrows():
        hlines.append(
            f"{row['id']} & {labels[str(row['metric'])]} & {int(row['n_pairs'])} & {row['effect_a_minus_b']:.3f} & "
            f"[{row['ci95_low']:.3f}; {row['ci95_high']:.3f}] & \\({_latex_scientific(float(row['p_holm']))}\\) \\\\"
        )
    hlines += ["\\bottomrule", "\\end{tabular}"]
    (tables / "sp7_hypotheses.tex").write_text("\n".join(hlines) + "\n", encoding="utf-8")


def _plot_results(output_dir: Path, runs: pd.DataFrame) -> None:
    figures = output_dir / "figures"
    method_order = list(METHODS)
    scenario_order = list(SCENARIO_LABELS)
    matrix = np.zeros((len(scenario_order), len(method_order)), dtype=float)
    for row_index, scenario in enumerate(scenario_order):
        for column_index, method in enumerate(method_order):
            values = runs[(runs["scenario"] == scenario) & (runs["method"] == method)]["delivery_success"]
            matrix[row_index, column_index] = float(values.mean())
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(method_order)), [METHOD_LABELS[value] for value in method_order], rotation=24, ha="right", fontsize=8)
    ax.set_yticks(range(len(scenario_order)), [SCENARIO_LABELS[value] for value in scenario_order], fontsize=8)
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            ax.text(column_index, row_index, f"{matrix[row_index, column_index]:.2f}", ha="center", va="center", color="white" if matrix[row_index, column_index] < 0.55 else "black", fontsize=8)
    fig.colorbar(image, ax=ax, label="Tasa de entrega")
    fig.tight_layout()
    fig.savefig(figures / "fig-sp7-delivery-matrix.pdf", bbox_inches="tight")
    plt.close(fig)

    grouped = runs.groupby("method", sort=False).agg(makespan=("makespan_steps", "mean"), messages=("messages", "mean"), deadlock=("deadlock", "mean"))
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    for method, row in grouped.iterrows():
        ax.scatter(row["messages"], row["makespan"], s=45 + 260 * row["deadlock"], label=METHOD_LABELS[str(method)])
    ax.set_xlabel("Mensajes contabilizados por mundo")
    ax.set_ylabel("Tiempo de terminación truncado [pasos]")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(figures / "fig-sp7-traffic-tradeoff.pdf", bbox_inches="tight")
    plt.close(fig)


def _report(experiment_id: str, runs: pd.DataFrame, summary: pd.DataFrame, hypotheses: pd.DataFrame, audit: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {experiment_id}",
            "",
            f"- Worlds: `{runs['world_hash'].nunique()}`",
            f"- Runs: `{len(runs)}`",
            f"- Audit: `{audit['status']}`",
            f"- Evidence: `{audit['evidence_level']}`",
            "",
            "## Method summary",
            "",
            summary.to_markdown(index=False),
            "",
            "## Hypotheses",
            "",
            hypotheses.to_markdown(index=False),
            "",
            "## Scope",
            "",
            audit["not_claimed"],
            "",
        ]
    )


def _expand_seeds(spec: Any) -> list[int]:
    if isinstance(spec, list):
        return [int(value) for value in spec]
    return list(range(int(spec["start"]), int(spec["start"]) + int(spec["count"])))


def _latex_scientific(value: float) -> str:
    if value == 0.0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10.0**exponent)
    return f"{mantissa:.2g}\\times10^{{{exponent}}}"


__all__ = [
    "METHODS",
    "ScheduleOutcome",
    "TrafficWorld",
    "audit_world_theory",
    "generate_world",
    "restricted_schedule_oracle",
    "run_sp7_config",
    "simulate_method",
    "simulate_schedule",
]
