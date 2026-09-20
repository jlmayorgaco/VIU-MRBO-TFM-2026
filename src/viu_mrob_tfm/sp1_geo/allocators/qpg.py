"""Sampled QPG Logit/Smith engines with neighbor aggregate estimates."""

from __future__ import annotations

import math
import time
import tracemalloc
from typing import Literal

import numpy as np

from ..models import ActionCatalog, AllocationResult, GeoWorld, SignalName
from ..welfare import (
    independent_argmax_closure,
    load_signal_gradient,
    projected_kkt_residual,
    signal_potential,
)

QPGEngine = Literal["logit", "smith"]


def _metropolis_matrix(adjacency: np.ndarray) -> np.ndarray:
    graph = np.asarray(adjacency, dtype=bool)
    n = len(graph)
    degrees = np.sum(graph, axis=1)
    matrix = np.zeros((n, n), dtype=float)
    for left in range(n):
        for right in np.flatnonzero(graph[left]):
            matrix[left, right] = 1.0 / (1.0 + max(degrees[left], degrees[right]))
        matrix[left, left] = 1.0 - float(np.sum(matrix[left]))
    return matrix


def _local_aggregate_estimates(
    world: GeoWorld,
    catalog: ActionCatalog,
    x: np.ndarray,
    signal: SignalName,
    rounds: int,
    *,
    exact: bool,
) -> tuple[np.ndarray, float]:
    contributions = catalog.contributions(signal)
    dimensions = contributions.shape[1]
    own = np.zeros((world.n_robots, world.n_loads, dimensions), dtype=float)
    np.add.at(
        own,
        (catalog.robot_index, catalog.load_index),
        x[:, None] * contributions,
    )
    exact_aggregate = np.sum(own, axis=0)
    if exact:
        estimates = np.broadcast_to(
            exact_aggregate[None, :, :],
            (world.n_robots, world.n_loads, dimensions),
        ).copy()
    else:
        estimates = world.n_robots * own
        mixing = _metropolis_matrix(world.communication_adjacency)
        flat = estimates.reshape(world.n_robots, -1)
        for _ in range(max(int(rounds), 0)):
            flat = mixing @ flat
        estimates = flat.reshape(estimates.shape)
    error = float(
        np.linalg.norm(estimates - exact_aggregate[None, :, :])
        / max(np.linalg.norm(exact_aggregate), 1e-12)
        / math.sqrt(world.n_robots)
    )
    return estimates, error


def _estimated_payoffs(
    world: GeoWorld,
    catalog: ActionCatalog,
    estimates: np.ndarray,
    signal: SignalName,
) -> np.ndarray:
    demands = catalog.demands(signal)
    contributions = catalog.contributions(signal)
    gradients = np.zeros_like(estimates)
    for robot in range(world.n_robots):
        for load in range(world.n_loads):
            gradients[robot, load] = load_signal_gradient(
                estimates[robot, load],
                demands[load],
                world.loads[load].priority_value,
            )
    payoff = np.einsum(
        "ad,ad->a",
        contributions,
        gradients[catalog.robot_index, catalog.load_index],
    ) - catalog.costs
    return np.where(catalog.compatible, payoff, -1e9)


def _full_robot_state(
    x: np.ndarray, actions: np.ndarray
) -> np.ndarray:
    values = np.maximum(x[actions], 0.0)
    idle = max(1.0 - float(np.sum(values)), 0.0)
    full = np.concatenate([values, np.array([idle])])
    total = float(np.sum(full))
    if total <= 1e-15:
        full[-1] = 1.0
        total = 1.0
    return full / total


def _logit_target(payoff: np.ndarray, temperature: float) -> np.ndarray:
    shifted = payoff - float(np.max(payoff))
    values = np.exp(np.clip(shifted / temperature, -700.0, 50.0))
    return values / float(np.sum(values))


def _smith_direction(state: np.ndarray, payoff: np.ndarray) -> np.ndarray:
    difference = payoff[:, None] - payoff[None, :]
    positive = np.maximum(difference, 0.0)
    inflow = positive @ state
    outflow = state * np.sum(positive.T, axis=1)
    return inflow - outflow


def _entropy(world: GeoWorld, catalog: ActionCatalog, x: np.ndarray) -> float:
    result = 0.0
    for robot in range(world.n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        full = _full_robot_state(x, actions)
        result -= float(np.sum(full * np.log(np.maximum(full, 1e-15))))
    return result


def _simplex_diagnostics(
    world: GeoWorld,
    catalog: ActionCatalog,
    x: np.ndarray,
) -> tuple[float, bool]:
    residual = float(
        max(
            np.max(np.maximum(-x, 0.0), initial=0.0),
            np.max(np.abs(x[~catalog.compatible]), initial=0.0),
        )
    )
    interior = True
    for robot in range(world.n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        mass = float(np.sum(x[actions]))
        residual = max(residual, max(mass - 1.0, 0.0))
        full = np.concatenate([x[actions], np.array([1.0 - mass])])
        interior &= bool(np.all(full > 1e-14))
    return residual, interior


def allocate_qpg(
    world: GeoWorld,
    catalog: ActionCatalog,
    *,
    signal: SignalName,
    engine: QPGEngine = "logit",
    entropy_tau: float = 0.08,
    damping: float = 0.22,
    max_iterations: int = 300,
    tolerance: float = 1e-6,
    consensus_rounds: int = 3,
    exact_aggregates: bool = False,
    monotone_guard: bool = False,
    trace_stride: int = 10,
) -> AllocationResult:
    """Execute a sampled local-estimate QPG dynamic.

    ``monotone_guard`` evaluates the global potential and is reserved for the
    numerical theory audit. Benchmark runs keep it disabled so it cannot leak
    a global acceptance oracle into the distributed decision rule.
    """

    if entropy_tau <= 0.0 or not 0.0 < damping <= 1.0:
        raise ValueError("entropy_tau and damping must be positive.")
    started = time.perf_counter()
    tracemalloc.start()
    x = np.zeros(catalog.n_actions, dtype=float)
    for robot in range(world.n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        if actions.size:
            x[actions] = 0.50 / actions.size
    initial_potential = signal_potential(
        world, catalog, x, signal, entropy_tau=entropy_tau
    )
    history = [initial_potential]
    events: list[dict[str, float | int | str]] = []
    aggregate_error = math.inf
    status = "max_iterations"
    edges = int(np.sum(world.communication_adjacency) // 2)
    completed_iterations = 0

    for iteration in range(1, int(max_iterations) + 1):
        estimates, aggregate_error = _local_aggregate_estimates(
            world,
            catalog,
            x,
            signal,
            consensus_rounds,
            exact=exact_aggregates,
        )
        payoff = _estimated_payoffs(world, catalog, estimates, signal)
        proposal = x.copy()
        max_change = 0.0
        for robot in range(world.n_robots):
            actions = catalog.actions_for_robot(robot, compatible_only=True)
            if actions.size == 0:
                continue
            current = _full_robot_state(x, actions)
            scores = np.concatenate([payoff[actions], np.array([0.0])])
            if engine == "logit":
                target = _logit_target(scores, entropy_tau)
                updated = (1.0 - damping) * current + damping * target
            elif engine == "smith":
                direction = _smith_direction(current, scores)
                updated = np.maximum(current + damping * direction, 0.0)
                updated /= max(float(np.sum(updated)), 1e-15)
            else:
                raise ValueError(f"Unknown QPG engine: {engine}")
            proposal[actions] = updated[:-1]
            max_change = max(
                max_change, float(np.max(np.abs(updated - current)))
            )

        if monotone_guard:
            previous_value = signal_potential(
                world, catalog, x, signal, entropy_tau=entropy_tau
            )
            candidate = proposal
            fraction = 1.0
            while fraction >= 2.0**-20:
                value = signal_potential(
                    world, catalog, candidate, signal, entropy_tau=entropy_tau
                )
                if value >= previous_value - 1e-12:
                    break
                fraction *= 0.5
                candidate = x + fraction * (proposal - x)
            proposal = candidate
        x = proposal
        value = signal_potential(
            world, catalog, x, signal, entropy_tau=entropy_tau
        )
        history.append(value)
        completed_iterations = iteration
        if iteration == 1 or iteration % max(int(trace_stride), 1) == 0:
            events.append(
                {
                    "event": "qpg_trace",
                    "iteration": iteration,
                    "potential": value,
                    "max_change": max_change,
                    "aggregate_estimation_error": aggregate_error,
                }
            )
        if max_change <= tolerance:
            status = "converged"
            break

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assignment = independent_argmax_closure(x, catalog, world.n_robots)
    try:
        kkt = projected_kkt_residual(
            world,
            catalog,
            x,
            signal,
            entropy_tau=entropy_tau,
        )
    except ValueError:
        kkt = math.nan
    primal_residual, entropy_interior = _simplex_diagnostics(
        world, catalog, x
    )
    message_rounds = (
        0 if exact_aggregates else completed_iterations * max(consensus_rounds, 0)
    )
    messages = 2 * edges * message_rounds
    resource_dimension = catalog.contributions(signal).shape[1]
    bytes_sent = messages * (16 + 8 * world.n_loads * resource_dimension)
    method_prefix = "geo_qpg" if signal == "marginal_physical" else "qpg"
    method = f"{method_prefix}_{engine}_{'physical' if signal == 'marginal_physical' else 'scalar'}"
    runtime_ms = 1_000.0 * (time.perf_counter() - started)
    return AllocationResult(
        method=method,
        engine=f"qpg_{engine}",
        signal=signal,
        assignment=assignment,
        status=status,
        runtime_negotiation_ms=runtime_ms,
        preferences=x,
        iterations=completed_iterations,
        rounds=message_rounds,
        messages=messages,
        bytes_sent=bytes_sent,
        diagnostics={
            "information_scope": (
                "exact_aggregate_theory_control"
                if exact_aggregates
                else "neighbor_consensus_estimates"
            ),
            "kkt_residual": kkt,
            "primal_residual": primal_residual,
            "dual_stationarity_residual": kkt,
            "complementarity_residual": (
                0.0 if entropy_interior and engine == "logit" else math.nan
            ),
            "price_consensus_residual": aggregate_error,
            "aggregate_estimation_error": aggregate_error,
            "potential_increment": history[-1] - history[0],
            "potential_min_increment": float(np.min(np.diff(history)))
            if len(history) > 1
            else 0.0,
            "final_entropy": _entropy(world, catalog, x),
            "potential_history": history,
            "peak_memory_mb": peak / (1024.0**2),
            "current_memory_mb": current / (1024.0**2),
            "monotone_guard": monotone_guard,
        },
        events=[dict(item) for item in events],
    )


__all__ = ["allocate_qpg"]
