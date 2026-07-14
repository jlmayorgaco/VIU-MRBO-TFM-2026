"""Confirmatory SP3 wrench-contact game with primal-dual Nash seeking.

This module is intentionally separate from the legacy SP3 campaign.  It treats
robot--load--slot force utilisation as a convex continuous relaxation, runs
several revision protocols on the same residual-price payoff, and then keeps
RAW, slot-closed and wrench-guarded assignments as distinct experimental
objects.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
import math
from pathlib import Path
import time
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from scipy.optimize import Bounds, LinearConstraint, minimize
from scipy.stats import wilcoxon

from viu_mrob_tfm.sp3.methods import (
    SP3Assignment,
    _guarded_wrench_local_repair,
    assignment_valid,
    make_sp3_allocator,
    score_assignment,
    wrench_fit,
)
from viu_mrob_tfm.sp3.metrics import evaluate_assignment
from viu_mrob_tfm.sp3.scenario import SP3Problem, SP3WrenchScenario, scenario_params_for_generator


@dataclass(frozen=True, slots=True)
class ActionModel:
    """Common action catalogue and normalized wrench columns."""

    load_indices: np.ndarray
    slot_indices: np.ndarray
    columns: np.ndarray
    costs: np.ndarray
    demand: np.ndarray

    @property
    def n_actions(self) -> int:
        return int(self.load_indices.size)


@dataclass(slots=True)
class GameResult:
    preferences: np.ndarray
    dual_prices: np.ndarray
    potential_history: list[float]
    kkt_history: list[float]
    consensus_error_history: list[float]
    iterations: int
    converged: bool
    messages: int
    simplex_error: float
    slot_violation: float
    kkt_residual: float
    complementarity_residual: float
    consensus_error: float
    runtime_s: float


def project_simplex(vector: np.ndarray) -> np.ndarray:
    """Euclidean projection onto the probability simplex."""

    v = np.asarray(vector, dtype=float)
    if v.ndim != 1:
        raise ValueError("project_simplex expects a one-dimensional vector")
    u = np.sort(v)[::-1]
    cssv = np.cumsum(u) - 1.0
    indices = np.arange(1, v.size + 1)
    eligible = u - cssv / indices > 0.0
    if not np.any(eligible):
        return np.full_like(v, 1.0 / max(v.size, 1))
    rho = int(indices[eligible][-1])
    theta = float(cssv[rho - 1] / rho)
    return np.maximum(v - theta, 0.0)


def build_action_model(problem: SP3Problem, *, distance_weight: float = 0.012) -> ActionModel:
    load_indices: list[int] = []
    slot_indices: list[int] = []
    base_columns: list[np.ndarray] = []
    for load_idx, slots in enumerate(problem.load_slots):
        for slot_idx, slot in enumerate(slots):
            direction = np.asarray(slot.direction_xy, dtype=float)
            offset = np.asarray(slot.offset_xy, dtype=float)
            torque = float(offset[0] * direction[1] - offset[1] * direction[0])
            base_columns.append(
                np.asarray(
                    [
                        direction[0] / max(problem.force_ref_n, 1e-12),
                        direction[1] / max(problem.force_ref_n, 1e-12),
                        torque / max(problem.torque_ref_nm, 1e-12),
                    ],
                    dtype=float,
                )
            )
            load_indices.append(load_idx)
            slot_indices.append(slot_idx)

    n_robots = len(problem.world.robots)
    n_actions = len(base_columns)
    columns = np.zeros((n_robots, n_actions, 3), dtype=float)
    costs = np.zeros((n_robots, n_actions), dtype=float)
    for robot_idx, robot in enumerate(problem.world.robots):
        force_limit = float(robot.spec.capacity.force_limit_n)
        for action_idx, (load_idx, slot_idx, base) in enumerate(zip(load_indices, slot_indices, base_columns)):
            columns[robot_idx, action_idx] = force_limit * base
            load = problem.world.loads[load_idx]
            slot = problem.load_slots[load_idx][slot_idx]
            target = np.asarray(load.pickup, dtype=float) + np.asarray(slot.offset_xy, dtype=float)
            distance = float(np.linalg.norm(np.asarray(robot.position, dtype=float) - target))
            costs[robot_idx, action_idx] = distance_weight * distance

    demand = np.vstack(
        [
            np.asarray(
                [
                    load.wrench.force_xy[0] / max(problem.force_ref_n, 1e-12),
                    load.wrench.force_xy[1] / max(problem.force_ref_n, 1e-12),
                    load.wrench.torque_z / max(problem.torque_ref_nm, 1e-12),
                ],
                dtype=float,
            )
            for load in problem.world.loads
        ]
    )
    return ActionModel(
        load_indices=np.asarray(load_indices, dtype=int),
        slot_indices=np.asarray(slot_indices, dtype=int),
        columns=columns,
        costs=costs,
        demand=demand,
    )


def aggregate_wrench(preferences: np.ndarray, model: ActionModel) -> tuple[np.ndarray, np.ndarray]:
    active = np.asarray(preferences[:, 1:], dtype=float)
    aggregate = np.zeros_like(model.demand)
    for action_idx, load_idx in enumerate(model.load_indices):
        aggregate[load_idx] += np.sum(active[:, action_idx, None] * model.columns[:, action_idx, :], axis=0)
    occupancy = np.sum(active, axis=0)
    return aggregate, occupancy


def potential_value(preferences: np.ndarray, model: ActionModel, *, regularization: float = 0.025) -> float:
    aggregate, _occupancy = aggregate_wrench(preferences, model)
    residual = model.demand - aggregate
    active = np.asarray(preferences[:, 1:], dtype=float)
    return float(-0.5 * np.sum(residual * residual) - np.sum(model.costs * active) - 0.5 * regularization * np.sum(active * active))


def potential_gradient(preferences: np.ndarray, model: ActionModel, *, regularization: float = 0.025) -> np.ndarray:
    aggregate, _occupancy = aggregate_wrench(preferences, model)
    residual = model.demand - aggregate
    gradient = np.zeros_like(preferences, dtype=float)
    for action_idx, load_idx in enumerate(model.load_indices):
        gradient[:, action_idx + 1] = (
            model.columns[:, action_idx, :] @ residual[load_idx]
            - model.costs[:, action_idx]
            - regularization * preferences[:, action_idx + 1]
        )
    return gradient


def _ring_matrix(n_agents: int) -> tuple[np.ndarray, int]:
    if n_agents <= 2:
        return np.full((n_agents, n_agents), 1.0 / n_agents), max(n_agents * (n_agents - 1) // 2, 1)
    adjacency = np.zeros((n_agents, n_agents), dtype=float)
    for idx in range(n_agents):
        adjacency[idx, (idx - 1) % n_agents] = 1.0
        adjacency[idx, (idx + 1) % n_agents] = 1.0
    degrees = np.sum(adjacency, axis=1)
    weights = np.zeros_like(adjacency)
    for i in range(n_agents):
        for j in range(n_agents):
            if adjacency[i, j] > 0.0:
                weights[i, j] = 1.0 / (1.0 + max(degrees[i], degrees[j]))
        weights[i, i] = 1.0 - np.sum(weights[i])
    return weights, n_agents


def _distributed_estimates(
    preferences: np.ndarray,
    model: ActionModel,
    *,
    graph: str,
    rounds: int,
) -> tuple[np.ndarray, np.ndarray, float, int]:
    n_agents = preferences.shape[0]
    exact_aggregate, exact_occupancy = aggregate_wrench(preferences, model)
    if graph == "complete":
        return (
            np.repeat(exact_aggregate[None, :, :], n_agents, axis=0),
            np.repeat(exact_occupancy[None, :], n_agents, axis=0),
            0.0,
            0,
        )

    local = np.zeros((n_agents, model.demand.size + model.n_actions), dtype=float)
    for robot_idx in range(n_agents):
        for action_idx, load_idx in enumerate(model.load_indices):
            local[robot_idx, 3 * load_idx : 3 * load_idx + 3] += (
                preferences[robot_idx, action_idx + 1] * model.columns[robot_idx, action_idx]
            )
            local[robot_idx, model.demand.size + action_idx] = preferences[robot_idx, action_idx + 1]
    weights, edges = _ring_matrix(n_agents)
    estimate = local.copy()
    for _ in range(max(int(rounds), 0)):
        estimate = weights @ estimate
    estimate *= n_agents
    aggregate_estimate = estimate[:, : model.demand.size].reshape(n_agents, *model.demand.shape)
    occupancy_estimate = estimate[:, model.demand.size :]
    target = np.concatenate([exact_aggregate.ravel(), exact_occupancy])
    consensus_error = float(np.max(np.linalg.norm(estimate - target[None, :], axis=1)))
    dimensions = model.demand.size + model.n_actions
    messages = int(max(rounds, 0) * 2 * edges * dimensions)
    return aggregate_estimate, occupancy_estimate, consensus_error, messages


def _payoffs_from_estimates(
    preferences: np.ndarray,
    dual_prices: np.ndarray,
    aggregate_estimates: np.ndarray,
    model: ActionModel,
    *,
    regularization: float,
) -> np.ndarray:
    payoffs = np.zeros_like(preferences)
    for robot_idx in range(preferences.shape[0]):
        residual = model.demand - aggregate_estimates[robot_idx]
        for action_idx, load_idx in enumerate(model.load_indices):
            payoffs[robot_idx, action_idx + 1] = (
                float(model.columns[robot_idx, action_idx] @ residual[load_idx])
                - model.costs[robot_idx, action_idx]
                - regularization * preferences[robot_idx, action_idx + 1]
                - dual_prices[robot_idx, action_idx]
            )
    return payoffs


def _revision_field(preferences: np.ndarray, payoffs: np.ndarray, protocol: str) -> np.ndarray:
    if protocol == "projected_pd":
        return payoffs
    field = np.zeros_like(preferences)
    for robot_idx in range(preferences.shape[0]):
        x = preferences[robot_idx]
        f = payoffs[robot_idx]
        average = float(x @ f)
        if protocol == "replicator":
            field[robot_idx] = x * (f - average)
        elif protocol == "erv_bnn":
            excess = np.maximum(f - average, 0.0)
            field[robot_idx] = excess - x * float(np.sum(excess))
        elif protocol == "smith":
            for action in range(x.size):
                inbound = float(np.sum(x * np.maximum(f[action] - f, 0.0)))
                outbound = float(x[action] * np.sum(np.maximum(f - f[action], 0.0)))
                field[robot_idx, action] = inbound - outbound
        else:
            raise ValueError(f"Unknown protocol: {protocol}")
    return field


def kkt_residual(preferences: np.ndarray, dual: np.ndarray, model: ActionModel, *, regularization: float = 0.025) -> tuple[float, float, float]:
    global_dual = np.mean(dual, axis=0)
    aggregate, occupancy = aggregate_wrench(preferences, model)
    estimates = np.repeat(aggregate[None, :, :], preferences.shape[0], axis=0)
    prices = np.repeat(global_dual[None, :], preferences.shape[0], axis=0)
    payoffs = _payoffs_from_estimates(preferences, prices, estimates, model, regularization=regularization)
    projected = np.vstack([project_simplex(preferences[i] + payoffs[i]) for i in range(preferences.shape[0])])
    stationarity = float(np.max(np.linalg.norm(projected - preferences, axis=1)))
    violation = float(max(np.max(occupancy - 1.0), 0.0))
    complementarity = float(np.max(np.abs(global_dual * (occupancy - 1.0)))) if occupancy.size else 0.0
    return max(stationarity, violation, complementarity), violation, complementarity


def simulate_wrench_game(
    problem: SP3Problem,
    *,
    protocol: str,
    graph: str = "complete",
    consensus_rounds: int = 4,
    steps: int = 500,
    dt: float = 0.08,
    dual_dt: float = 0.10,
    regularization: float = 0.025,
    tolerance: float = 2e-4,
) -> GameResult:
    model = build_action_model(problem)
    n_agents = len(problem.world.robots)
    preferences = np.full((n_agents, model.n_actions + 1), 0.75 / max(model.n_actions, 1), dtype=float)
    preferences[:, 0] = 0.25
    preferences = np.vstack([project_simplex(row) for row in preferences])
    dual = np.zeros((n_agents, model.n_actions), dtype=float)
    potential_history = [potential_value(preferences, model, regularization=regularization)]
    kkt_history: list[float] = []
    consensus_history: list[float] = []
    total_messages = 0
    stable = 0
    start = time.perf_counter()
    iterations = 0
    for step in range(int(steps)):
        iterations = step + 1
        agg_est, occ_est, consensus_error, messages = _distributed_estimates(
            preferences, model, graph=graph, rounds=consensus_rounds
        )
        total_messages += messages
        payoffs = _payoffs_from_estimates(
            preferences, dual, agg_est, model, regularization=regularization
        )
        field = _revision_field(preferences, payoffs, protocol)
        previous = preferences.copy()
        preferences = np.vstack(
            [project_simplex(preferences[i] + dt * field[i]) for i in range(n_agents)]
        )
        dual = np.maximum(0.0, dual + dual_dt * (occ_est - 1.0))
        if graph == "complete":
            dual[:] = np.mean(dual, axis=0)
        else:
            weights, _edges = _ring_matrix(n_agents)
            dual = weights @ dual

        residual, _violation, _comp = kkt_residual(
            preferences, dual, model, regularization=regularization
        )
        delta = float(np.max(np.abs(preferences - previous)))
        if step % 5 == 0 or step == int(steps) - 1:
            potential_history.append(potential_value(preferences, model, regularization=regularization))
            kkt_history.append(residual)
            consensus_history.append(consensus_error)
        if delta <= tolerance and residual <= 10.0 * tolerance:
            stable += 1
        else:
            stable = 0
        if stable >= 15:
            break

    runtime = time.perf_counter() - start
    residual, slot_violation, complementarity = kkt_residual(
        preferences, dual, model, regularization=regularization
    )
    simplex_error = float(np.max(np.abs(np.sum(preferences, axis=1) - 1.0)))
    consensus_error = float(consensus_history[-1]) if consensus_history else 0.0
    return GameResult(
        preferences=preferences,
        dual_prices=dual,
        potential_history=potential_history,
        kkt_history=kkt_history,
        consensus_error_history=consensus_history,
        iterations=iterations,
        converged=bool(residual <= 0.02),
        messages=total_messages,
        simplex_error=simplex_error,
        slot_violation=slot_violation,
        kkt_residual=residual,
        complementarity_residual=complementarity,
        consensus_error=consensus_error,
        runtime_s=float(runtime),
    )


def solve_relaxed_qp(problem: SP3Problem, *, regularization: float = 0.025) -> tuple[np.ndarray, float, bool]:
    """Central SLSQP reference for the convex continuous relaxation."""

    model = build_action_model(problem)
    n_agents = len(problem.world.robots)
    n_strategies = model.n_actions + 1
    size = n_agents * n_strategies
    x0 = np.full((n_agents, n_strategies), 0.75 / max(model.n_actions, 1), dtype=float)
    x0[:, 0] = 0.25

    def objective(flat: np.ndarray) -> float:
        pref = flat.reshape(n_agents, n_strategies)
        return -potential_value(pref, model, regularization=regularization)

    def jacobian(flat: np.ndarray) -> np.ndarray:
        pref = flat.reshape(n_agents, n_strategies)
        return -potential_gradient(pref, model, regularization=regularization).ravel()

    equality = np.zeros((n_agents, size), dtype=float)
    for robot_idx in range(n_agents):
        equality[robot_idx, robot_idx * n_strategies : (robot_idx + 1) * n_strategies] = 1.0
    slot = np.zeros((model.n_actions, size), dtype=float)
    for action_idx in range(model.n_actions):
        for robot_idx in range(n_agents):
            slot[action_idx, robot_idx * n_strategies + action_idx + 1] = 1.0
    constraints = [LinearConstraint(equality, np.ones(n_agents), np.ones(n_agents))]
    if model.n_actions:
        constraints.append(LinearConstraint(slot, np.zeros(model.n_actions), np.ones(model.n_actions)))
    result = minimize(
        objective,
        x0.ravel(),
        jac=jacobian,
        method="SLSQP",
        bounds=Bounds(np.zeros(size), np.ones(size)),
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10, "disp": False},
    )
    preferences = np.asarray(result.x, dtype=float).reshape(n_agents, n_strategies)
    return preferences, float(-result.fun), bool(result.success)


def decode_preferences(problem: SP3Problem, preferences: np.ndarray, *, guarded: bool, method: str) -> tuple[SP3Assignment, SP3Assignment]:
    model = build_action_model(problem)
    raw_labels = np.zeros(preferences.shape[0], dtype=int)
    raw_slots = np.zeros(preferences.shape[0], dtype=int)
    for robot_idx in range(preferences.shape[0]):
        action = int(np.argmax(preferences[robot_idx]))
        if action > 0:
            raw_labels[robot_idx] = int(model.load_indices[action - 1]) + 1
            raw_slots[robot_idx] = int(model.slot_indices[action - 1]) + 1
    raw = SP3Assignment(raw_labels, raw_slots, method=f"{method}_raw")

    labels = np.zeros(preferences.shape[0], dtype=int)
    slots = np.zeros(preferences.shape[0], dtype=int)
    candidates: list[tuple[float, int, int]] = []
    for robot_idx in range(preferences.shape[0]):
        for action_idx in range(model.n_actions):
            candidates.append((float(preferences[robot_idx, action_idx + 1]), robot_idx, action_idx))
    used_robots: set[int] = set()
    used_slots: set[tuple[int, int]] = set()
    for preference, robot_idx, action_idx in sorted(candidates, reverse=True):
        if preference <= 1e-9 or robot_idx in used_robots:
            continue
        load_idx = int(model.load_indices[action_idx])
        slot_idx = int(model.slot_indices[action_idx])
        key = (load_idx, slot_idx)
        if key in used_slots:
            continue
        labels[robot_idx] = load_idx + 1
        slots[robot_idx] = slot_idx + 1
        used_robots.add(robot_idx)
        used_slots.add(key)
    closed = SP3Assignment(labels, slots, method=method)
    if guarded:
        closed = _guarded_wrench_local_repair(
            problem, closed, method=method, pair_aware=True, max_passes=4
        )
        closed = _strict_wrench_guard(problem, closed, method=method)
    return raw, SP3Assignment(closed.labels, closed.slot_labels, method=method)


def _strict_wrench_guard(problem: SP3Problem, assignment: SP3Assignment, *, method: str) -> SP3Assignment:
    """Unconditionally abstain from any CLOSED load that fails the wrench test."""

    labels = assignment.labels.copy()
    slots = assignment.slot_labels.copy()
    for load_idx in range(len(problem.world.loads)):
        current = SP3Assignment(labels, slots, method)
        if np.any(labels == load_idx + 1) and wrench_fit(problem, current, load_idx).residual_norm > problem.wrench_tolerance:
            mask = labels == load_idx + 1
            labels[mask] = 0
            slots[mask] = 0
    return SP3Assignment(labels, slots, method=method)


def _uniform_preferences(problem: SP3Problem) -> np.ndarray:
    model = build_action_model(problem)
    preferences = np.full((len(problem.world.robots), model.n_actions + 1), 1.0 / (model.n_actions + 1), dtype=float)
    return preferences


def _assignment_fp(problem: SP3Problem, assignment: SP3Assignment) -> tuple[float, float]:
    assigned = 0
    false = 0
    feasible = 0
    for load_idx in range(len(problem.world.loads)):
        if not np.any(assignment.labels == load_idx + 1):
            continue
        assigned += 1
        ok = wrench_fit(problem, assignment, load_idx).residual_norm <= problem.wrench_tolerance
        feasible += int(ok)
        false += int(not ok)
    return float(false / assigned) if assigned else 0.0, float(feasible / max(len(problem.world.loads), 1))


def _is_guarded_method(method: str) -> bool:
    """Return true only for strict guarded variants, never for unguarded."""

    name = str(method).lower()
    return name.endswith("_guarded") or name in {"uniform_guarded", "smith_wrench_pairs_guarded"}


def _method_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(item) for item in config.get("methods", [])]


def _row_from_assignment(
    problem: SP3Problem,
    assignment: SP3Assignment,
    oracle: SP3Assignment,
    *,
    method: str,
    world_id: str,
    seed: int,
    scenario: str,
    runtime_s: float,
    raw: SP3Assignment | None = None,
    game: GameResult | None = None,
) -> dict[str, Any]:
    metrics = evaluate_assignment(
        problem,
        assignment,
        runtime_ms=1000.0 * runtime_s,
        oracle_assignment=oracle,
        centralized=method in {"wrench_oracle", "oracle_scalar_assignment"},
    )
    row: dict[str, Any] = asdict(metrics)
    row.update(
        {
            "world_id": world_id,
            "seed": seed,
            "scenario": scenario,
            "method": method,
            "assignment_valid": assignment_valid(problem, assignment),
            "strict_score": score_assignment(problem, assignment),
            "runtime_s": runtime_s,
        }
    )
    if raw is not None:
        raw_fp, raw_feasible = _assignment_fp(problem, raw)
        row.update(
            {
                "raw_fp_given_assigned": raw_fp,
                "raw_wrench_feasible_rate": raw_feasible,
                "raw_closed_distinct": bool(np.any(raw.labels != assignment.labels) or np.any(raw.slot_labels != assignment.slot_labels)),
            }
        )
    else:
        row.update({"raw_fp_given_assigned": math.nan, "raw_wrench_feasible_rate": math.nan, "raw_closed_distinct": False})
    if game is not None:
        row.update(
            {
                "iterations": game.iterations,
                "converged": game.converged,
                "messages": game.messages,
                "simplex_error": game.simplex_error,
                "slot_violation": game.slot_violation,
                "kkt_residual": game.kkt_residual,
                "complementarity_residual": game.complementarity_residual,
                "consensus_error": game.consensus_error,
                "potential_initial": game.potential_history[0],
                "potential_final": game.potential_history[-1],
                "potential_gain": game.potential_history[-1] - game.potential_history[0],
            }
        )
    else:
        for key in ["iterations", "messages", "simplex_error", "slot_violation", "kkt_residual", "complementarity_residual", "consensus_error", "potential_initial", "potential_final", "potential_gain"]:
            row[key] = math.nan
        row["converged"] = True
    return row


def _summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metrics = [
        "wrench_feasible_rate",
        "feasible_coverage",
        "precision_given_assigned",
        "fp_given_assigned",
        "optimality_gap_vs_wrench_oracle",
        "wrench_residual_feasible_available",
        "runtime_s",
        "messages",
        "kkt_residual",
        "consensus_error",
    ]
    output: list[dict[str, Any]] = []
    for method in sorted({str(row["method"]) for row in rows}):
        group = [row for row in rows if row["method"] == method]
        item: dict[str, Any] = {"method": method, "n": len(group)}
        for metric in metrics:
            values = np.asarray([float(row.get(metric, math.nan)) for row in group], dtype=float)
            values = values[np.isfinite(values)]
            item[f"{metric}_mean"] = float(np.mean(values)) if values.size else math.nan
            item[f"{metric}_std"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0 if values.size else math.nan
        output.append(item)
    return sorted(output, key=lambda item: float(item.get("optimality_gap_vs_wrench_oracle_mean", math.inf)))


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(np.asarray(p_values, dtype=float))
    adjusted = np.ones(len(p_values), dtype=float)
    running = 0.0
    m = len(p_values)
    for rank, idx in enumerate(order):
        value = min(1.0, (m - rank) * float(p_values[int(idx)]))
        running = max(running, value)
        adjusted[int(idx)] = running
    return adjusted.tolist()


def _hypotheses(rows: list[dict[str, Any]], specs: Iterable[dict[str, Any]], *, seed: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    output: list[dict[str, Any]] = []
    for spec in specs:
        metric = str(spec["metric"])
        method_a = str(spec["method_a"])
        method_b = str(spec["method_b"])
        by_world: dict[str, dict[str, float]] = {}
        for row in rows:
            if row["method"] not in {method_a, method_b}:
                continue
            value = float(row.get(metric, math.nan))
            if np.isfinite(value):
                by_world.setdefault(str(row["world_id"]), {})[str(row["method"])] = value
        diffs = np.asarray([values[method_a] - values[method_b] for values in by_world.values() if method_a in values and method_b in values], dtype=float)
        if diffs.size < 2:
            output.append({"id": spec["id"], "metric": metric, "method_a": method_a, "method_b": method_b, "n_pairs": int(diffs.size), "effect_mean": math.nan, "ci95_low": math.nan, "ci95_high": math.nan, "p_raw": 1.0})
            continue
        boot = np.asarray([np.mean(rng.choice(diffs, size=diffs.size, replace=True)) for _ in range(2000)], dtype=float)
        try:
            alternative = "less" if str(spec.get("direction", "less")) == "less" else "greater"
            p_raw = float(wilcoxon(diffs, alternative=alternative, zero_method="zsplit").pvalue)
        except ValueError:
            p_raw = 1.0
        output.append(
            {
                "id": spec["id"],
                "metric": metric,
                "method_a": method_a,
                "method_b": method_b,
                "n_pairs": int(diffs.size),
                "effect_mean": float(np.mean(diffs)),
                "ci95_low": float(np.quantile(boot, 0.025)),
                "ci95_high": float(np.quantile(boot, 0.975)),
                "p_raw": p_raw,
            }
        )
    adjusted = _holm([float(row["p_raw"]) for row in output]) if output else []
    for row, value in zip(output, adjusted):
        row["p_holm"] = value
        row["reject_holm_005"] = bool(value < 0.05)
    return output


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0])
    for row in rows[1:]:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _plots(rows: list[dict[str, Any]], histories: dict[str, GameResult], output: Path) -> list[str]:
    output.mkdir(parents=True, exist_ok=True)
    summary = _summary(rows)
    labels = [str(row["method"]).replace("_", " ") for row in summary]
    gaps = [float(row["optimality_gap_vs_wrench_oracle_mean"]) for row in summary]
    fp = [float(row["fp_given_assigned_mean"]) for row in summary]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.2))
    axes[0].barh(labels[::-1], gaps[::-1], color="#0072B2")
    axes[0].set_xlabel("Brecha frente al oráculo (↓)")
    axes[0].grid(axis="x", alpha=0.25)
    axes[1].barh(labels[::-1], fp[::-1], color="#D55E00")
    axes[1].set_xlabel("Falsos positivos condicionados (↓)")
    axes[1].grid(axis="x", alpha=0.25)
    fig.tight_layout()
    main_path = output / "fig-sp3-wrench-game-performance.png"
    fig.savefig(main_path, dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    for label, result in histories.items():
        axes[0].plot(np.arange(len(result.kkt_history)) * 5, result.kkt_history, label=label.replace("_", " "))
        axes[1].plot(np.arange(len(result.potential_history)) * 5, result.potential_history, label=label.replace("_", " "))
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Iteración")
    axes[0].set_ylabel("Residual KKT")
    axes[1].set_xlabel("Iteración")
    axes[1].set_ylabel("Potencial primal")
    for axis in axes:
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    conv_path = output / "fig-sp3-kkt-potential.png"
    fig.savefig(conv_path, dpi=220)
    plt.close(fig)

    game_rows = [row for row in rows if str(row["method"]).startswith(("nash_pd", "smith_price", "replicator_price", "erv_bnn"))]
    methods = sorted({str(row["method"]) for row in game_rows})
    coverage = [float(np.mean([row["feasible_coverage"] for row in game_rows if row["method"] == method])) for method in methods]
    raw_fp = [float(np.mean([row["raw_fp_given_assigned"] for row in game_rows if row["method"] == method])) for method in methods]
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    x = np.arange(len(methods))
    ax.bar(x - 0.18, coverage, width=0.36, label="Cobertura CLOSED", color="#009E73")
    ax.bar(x + 0.18, raw_fp, width=0.36, label="FP RAW", color="#CC79A7")
    ax.set_xticks(x, [method.replace("_", "\n") for method in methods], fontsize=8)
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    ablation_path = output / "fig-sp3-protocol-closure.png"
    fig.savefig(ablation_path, dpi=220)
    plt.close(fig)
    return [str(main_path), str(conv_path), str(ablation_path)]


def run_sp3_wrench_nash_config(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    output.mkdir(parents=True, exist_ok=True)
    seeds_spec = dict(config["seeds"])
    seeds = list(range(int(seeds_spec["start"]), int(seeds_spec["start"]) + int(seeds_spec["count"])))
    scenarios = [str(item["param_generator"]) for item in config["scenarios"]]
    method_specs = _method_specs(config)
    game_config = dict(config.get("game", {}))
    rows: list[dict[str, Any]] = []
    histories: dict[str, GameResult] = {}
    qp_audit: list[dict[str, Any]] = []

    for scenario in scenarios:
        params = scenario_params_for_generator(scenario)[0]
        for seed in seeds:
            problem = SP3WrenchScenario(params).build(seed)
            world_id = f"{scenario}_seed{seed}"
            game_cache: dict[tuple[Any, ...], GameResult] = {}
            oracle_start = time.perf_counter()
            oracle = make_sp3_allocator("wrench_oracle").allocate(problem)
            oracle_runtime = time.perf_counter() - oracle_start
            qp_preferences, qp_potential, qp_success = solve_relaxed_qp(problem, regularization=float(game_config.get("regularization", 0.025)))
            if len(qp_audit) < int(config.get("audit_worlds", 60)):
                qp_audit.append({"world_id": world_id, "qp_success": qp_success, "qp_potential": qp_potential})

            for spec in method_specs:
                method = str(spec["id"])
                kind = str(spec.get("kind", "allocator"))
                if method == "wrench_oracle":
                    assignment = oracle
                    rows.append(_row_from_assignment(problem, assignment, oracle, method=method, world_id=world_id, seed=seed, scenario=scenario, runtime_s=oracle_runtime))
                    continue
                if kind == "allocator":
                    start = time.perf_counter()
                    assignment = make_sp3_allocator(method, dict(spec.get("params", {}))).allocate(problem)
                    if _is_guarded_method(method):
                        assignment = _strict_wrench_guard(problem, assignment, method=method)
                    runtime = time.perf_counter() - start
                    rows.append(_row_from_assignment(problem, assignment, oracle, method=method, world_id=world_id, seed=seed, scenario=scenario, runtime_s=runtime))
                    continue
                if kind == "uniform":
                    start = time.perf_counter()
                    raw, assignment = decode_preferences(problem, _uniform_preferences(problem), guarded=bool(spec.get("guarded", True)), method=method)
                    runtime = time.perf_counter() - start
                    rows.append(_row_from_assignment(problem, assignment, oracle, method=method, world_id=world_id, seed=seed, scenario=scenario, runtime_s=runtime, raw=raw))
                    continue
                protocol = str(spec["protocol"])
                graph = str(spec.get("graph", "complete"))
                simulation_args = {
                    "protocol": protocol,
                    "graph": graph,
                    "consensus_rounds": int(spec.get("consensus_rounds", game_config.get("consensus_rounds", 4))),
                    "steps": int(spec.get("steps", game_config.get("steps", 500))),
                    "dt": float(spec.get("dt", game_config.get("dt", 0.08))),
                    "dual_dt": float(spec.get("dual_dt", game_config.get("dual_dt", 0.10))),
                    "regularization": float(spec.get("regularization", game_config.get("regularization", 0.025))),
                    "tolerance": float(spec.get("tolerance", game_config.get("tolerance", 2e-4))),
                }
                cache_key = tuple(simulation_args.items())
                if cache_key not in game_cache:
                    game_cache[cache_key] = simulate_wrench_game(problem, **simulation_args)
                result = game_cache[cache_key]
                raw, assignment = decode_preferences(problem, result.preferences, guarded=bool(spec.get("guarded", True)), method=method)
                row = _row_from_assignment(problem, assignment, oracle, method=method, world_id=world_id, seed=seed, scenario=scenario, runtime_s=result.runtime_s, raw=raw, game=result)
                row["qp_potential"] = qp_potential
                row["qp_potential_gap"] = float(max(qp_potential - result.potential_history[-1], 0.0))
                row["qp_success"] = qp_success
                rows.append(row)
                if not histories and method.startswith("nash_pd"):
                    histories[method] = result
                elif method not in histories and len(histories) < 5 and seed == seeds[0] and scenario == scenarios[0]:
                    histories[method] = result

    summary = _summary(rows)
    hypotheses = _hypotheses(rows, config.get("hypotheses", []), seed=int(seeds_spec["start"]) + 991)
    game_rows = [row for row in rows if np.isfinite(float(row.get("simplex_error", math.nan)))]
    exact_pd_rows = [row for row in rows if row["method"] in {"nash_pd_exact_guarded", "nash_pd_exact_unguarded"}]
    guarded_rows = [row for row in rows if _is_guarded_method(str(row["method"]))]
    audit = {
        "experiment_id": config["experiment_id"],
        "passed": bool(
            game_rows
            and max(float(row["simplex_error"]) for row in game_rows) <= 1e-10
            and exact_pd_rows
            and max(float(row["slot_violation"]) for row in exact_pd_rows) <= 0.05
            and max(float(row.get("qp_potential_gap", 0.0)) for row in exact_pd_rows) <= 0.01
            and all(bool(row["assignment_valid"]) for row in rows)
            and all(float(row["fp_given_assigned"]) <= 1e-12 for row in guarded_rows)
            and all(bool(item["qp_success"]) for item in qp_audit)
            and all(bool(row.get("qp_success", True)) for row in exact_pd_rows)
        ),
        "worlds": len(scenarios) * len(seeds),
        "runs": len(rows),
        "game_runs": len(game_rows),
        "max_simplex_error": max((float(row["simplex_error"]) for row in game_rows), default=math.nan),
        "max_slot_violation": max((float(row["slot_violation"]) for row in game_rows), default=math.nan),
        "max_exact_pd_slot_violation": max((float(row["slot_violation"]) for row in exact_pd_rows), default=math.nan),
        "max_exact_pd_qp_potential_gap": max((float(row.get("qp_potential_gap", 0.0)) for row in exact_pd_rows), default=math.nan),
        "max_kkt_residual": max((float(row["kkt_residual"]) for row in game_rows), default=math.nan),
        "guarded_false_positive_violations": sum(int(float(row["fp_given_assigned"]) > 1e-12) for row in guarded_rows),
        "raw_closed_distinct_runs": sum(int(bool(row.get("raw_closed_distinct", False))) for row in rows),
        "qp_audit": qp_audit,
        "contracts": {
            "kkt_equivalence": "Only the convex continuous relaxation under Slater/convexity; not the integer closure.",
            "population_protocols": "Simplex invariance is audited; convergence theorem is claimed only for projected primal-dual under stated assumptions.",
            "ring_graph": "Finite-consensus sensitivity, not a time-varying-graph theorem.",
            "guard": "Guarded CLOSED assignments abstain from mechanically infeasible loads; global optimality is not claimed.",
        },
    }
    _write_csv(tables / "runs.csv", rows)
    _write_csv(tables / "summary.csv", summary)
    _write_csv(tables / "hypothesis_results.csv", hypotheses)
    (output / "theory_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    figure_paths = _plots(rows, histories, figures)

    report_lines = [
        f"# {config['experiment_id']}",
        "",
        f"- Worlds: `{audit['worlds']}`",
        f"- Runs: `{audit['runs']}`",
        f"- Theory audit: `{'PASS' if audit['passed'] else 'FAIL'}`",
        "",
        "## Summary",
        "",
        "| Method | Coverage | Precision | FP assigned | Gap oracle | KKT | Runtime s |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        report_lines.append(
            f"| {row['method']} | {row['feasible_coverage_mean']:.4f} | {row['precision_given_assigned_mean']:.4f} | {row['fp_given_assigned_mean']:.4f} | {row['optimality_gap_vs_wrench_oracle_mean']:.4f} | {row['kkt_residual_mean']:.4g} | {row['runtime_s_mean']:.4f} |"
        )
    report_lines.extend(["", "## Hypotheses", "", "| ID | Effect A-B | CI95 | p Holm | Reject |", "|---|---:|---|---:|---|"])
    for row in hypotheses:
        report_lines.append(
            f"| {row['id']} | {row['effect_mean']:.5f} | [{row['ci95_low']:.5f}, {row['ci95_high']:.5f}] | {row['p_holm']:.5g} | {row['reject_holm_005']} |"
        )
    report_lines.extend(["", "## Scope", "", "- The KKT certificate applies to the convex force-utilisation relaxation.", "- Integer robot/slot selection remains NP-hard.", "- Population protocols are engine ablations on a shared wrench-price payoff.", "- Guarded closure is mechanically certified but not fully distributed or globally optimal."])
    (output / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    manifest = {
        "experiment_id": config["experiment_id"],
        "config": str(path),
        "output_dir": str(output),
        "worlds": audit["worlds"],
        "runs": len(rows),
        "theory_audit": str(output / "theory_audit.json"),
        "report": str(output / "report.md"),
        "figures": figure_paths,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


__all__ = [
    "ActionModel",
    "GameResult",
    "aggregate_wrench",
    "build_action_model",
    "decode_preferences",
    "kkt_residual",
    "potential_gradient",
    "potential_value",
    "project_simplex",
    "run_sp3_wrench_nash_config",
    "simulate_wrench_game",
    "solve_relaxed_qp",
]
