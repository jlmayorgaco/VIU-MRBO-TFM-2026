"""Finite potential game used by the canonical SP6-C recovery study.

The formal scope is one affected rigid payload and a finite reserve pool.  Each
reserve robot either joins the repair coalition or remains free.  Mechanical
coverage is represented by a conservative additive resource certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True, slots=True)
class BetterResponseResult:
    profile: np.ndarray
    potential_trace: np.ndarray
    profiles: tuple[tuple[int, ...], ...]
    activations: int
    strict_moves: int


def weighted_deficit(
    profile: np.ndarray,
    capabilities: np.ndarray,
    requirement: np.ndarray,
    weights: np.ndarray | None = None,
) -> float:
    """Return the dimensionless weighted residual certificate deficit."""

    x = np.asarray(profile, dtype=float)
    c = np.asarray(capabilities, dtype=float)
    r = np.asarray(requirement, dtype=float)
    w = np.ones_like(r) if weights is None else np.asarray(weights, dtype=float)
    coverage = x @ c
    return float(np.sum(w * np.maximum(r - coverage, 0.0)))


def is_feasible(profile: np.ndarray, capabilities: np.ndarray, requirement: np.ndarray, *, atol: float = 1e-10) -> bool:
    coverage = np.asarray(profile, dtype=float) @ np.asarray(capabilities, dtype=float)
    return bool(np.all(coverage + atol >= np.asarray(requirement, dtype=float)))


def potential(
    profile: np.ndarray,
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    penalty: float,
    weights: np.ndarray | None = None,
) -> float:
    x = np.asarray(profile, dtype=float)
    return -float(penalty) * weighted_deficit(x, capabilities, requirement, weights) - float(x @ np.asarray(costs, dtype=float))


def marginal_utility(
    robot: int,
    action: int,
    profile: np.ndarray,
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    penalty: float,
    weights: np.ndarray | None = None,
) -> float:
    """Wonderful-life utility relative to the counterfactual action zero."""

    actual = np.asarray(profile, dtype=int).copy()
    actual[robot] = int(action)
    absent = actual.copy()
    absent[robot] = 0
    return potential(actual, capabilities, requirement, costs, penalty, weights) - potential(
        absent, capabilities, requirement, costs, penalty, weights
    )


def all_profiles(n_robots: int):
    for values in product((0, 1), repeat=int(n_robots)):
        yield np.asarray(values, dtype=int)


def is_pure_nash(
    profile: np.ndarray,
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    penalty: float,
    weights: np.ndarray | None = None,
    *,
    atol: float = 1e-10,
) -> bool:
    x = np.asarray(profile, dtype=int)
    current = potential(x, capabilities, requirement, costs, penalty, weights)
    for robot in range(len(x)):
        deviated = x.copy()
        deviated[robot] = 1 - deviated[robot]
        if potential(deviated, capabilities, requirement, costs, penalty, weights) > current + atol:
            return False
    return True


def pure_nash_profiles(
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    penalty: float,
    weights: np.ndarray | None = None,
) -> list[np.ndarray]:
    return [
        profile
        for profile in all_profiles(len(costs))
        if is_pure_nash(profile, capabilities, requirement, costs, penalty, weights)
    ]


def is_inclusion_minimal(profile: np.ndarray, capabilities: np.ndarray, requirement: np.ndarray) -> bool:
    x = np.asarray(profile, dtype=int)
    if not is_feasible(x, capabilities, requirement):
        return False
    for robot in np.flatnonzero(x):
        reduced = x.copy()
        reduced[int(robot)] = 0
        if is_feasible(reduced, capabilities, requirement):
            return False
    return True


def accessibility_margin(
    capabilities: np.ndarray,
    requirement: np.ndarray,
    weights: np.ndarray | None = None,
) -> float:
    """Compute delta_min over infeasible profiles for the theorem threshold."""

    c = np.asarray(capabilities, dtype=float)
    r = np.asarray(requirement, dtype=float)
    if not is_feasible(np.ones(c.shape[0], dtype=int), c, r):
        return 0.0
    margins: list[float] = []
    for profile in all_profiles(c.shape[0]):
        if is_feasible(profile, c, r):
            continue
        before = weighted_deficit(profile, c, r, weights)
        improvements = []
        for robot in np.flatnonzero(profile == 0):
            joined = profile.copy()
            joined[int(robot)] = 1
            improvements.append(before - weighted_deficit(joined, c, r, weights))
        margins.append(max(improvements, default=0.0))
    return float(min(margins, default=0.0))


def sufficient_penalty(
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    weights: np.ndarray | None = None,
    *,
    safety_factor: float = 1.05,
) -> tuple[float, float]:
    delta_min = accessibility_margin(capabilities, requirement, weights)
    if delta_min <= 0.0:
        return float("inf"), delta_min
    threshold = float(np.max(np.asarray(costs, dtype=float)) / delta_min)
    return float(safety_factor * threshold + 1e-12), delta_min


def asynchronous_better_response(
    capabilities: np.ndarray,
    requirement: np.ndarray,
    costs: np.ndarray,
    penalty: float,
    weights: np.ndarray | None = None,
    *,
    initial_profile: np.ndarray | None = None,
    seed: int = 0,
    atol: float = 1e-10,
) -> BetterResponseResult:
    """Fair shuffled activations with strict unilateral improvements only."""

    n = len(costs)
    profile = np.zeros(n, dtype=int) if initial_profile is None else np.asarray(initial_profile, dtype=int).copy()
    rng = np.random.default_rng(seed)
    trace = [potential(profile, capabilities, requirement, costs, penalty, weights)]
    profiles = [tuple(int(value) for value in profile)]
    activations = 0
    strict_moves = 0
    while True:
        moved_in_sweep = False
        for robot in rng.permutation(n):
            activations += 1
            candidate = profile.copy()
            candidate[int(robot)] = 1 - candidate[int(robot)]
            candidate_phi = potential(candidate, capabilities, requirement, costs, penalty, weights)
            if candidate_phi > trace[-1] + atol:
                profile = candidate
                trace.append(candidate_phi)
                profiles.append(tuple(int(value) for value in profile))
                strict_moves += 1
                moved_in_sweep = True
        if not moved_in_sweep:
            break
        if strict_moves >= 2**n:
            raise RuntimeError("Strict potential ascent exceeded the finite-profile bound.")
    return BetterResponseResult(
        profile=profile,
        potential_trace=np.asarray(trace, dtype=float),
        profiles=tuple(profiles),
        activations=activations,
        strict_moves=strict_moves,
    )


def exact_feasible_oracle(capabilities: np.ndarray, requirement: np.ndarray, costs: np.ndarray) -> np.ndarray:
    """Minimum-cost feasible coalition; empty if the reserve is insufficient."""

    best: np.ndarray | None = None
    best_key = (float("inf"), float("inf"), ())
    for profile in all_profiles(len(costs)):
        if not is_feasible(profile, capabilities, requirement):
            continue
        key = (float(profile @ costs), int(np.sum(profile)), tuple(int(v) for v in profile))
        if key < best_key:
            best_key = key
            best = profile.copy()
    return np.zeros(len(costs), dtype=int) if best is None else best


def recovery_time_upper_bound(
    detection_delay_s: float,
    strict_move_bound: int,
    max_interactivation_s: float,
    max_travel_distance_m: float,
    min_speed_mps: float,
    settling_time_s: float,
) -> float:
    return float(
        detection_delay_s
        + strict_move_bound * max_interactivation_s
        + max_travel_distance_m / max(min_speed_mps, 1e-12)
        + settling_time_s
    )


def unbounded_efficiency_example(scale: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, np.ndarray, np.ndarray]:
    """Return the one-resource counterexample used in the SP6 appendix."""

    m = float(scale)
    capabilities = np.asarray([[1.0], [0.5], [0.5]], dtype=float)
    requirement = np.asarray([1.0], dtype=float)
    costs = np.asarray([m, 1.0, 1.0], dtype=float)
    penalty = 2.5 * m
    expensive = np.asarray([1, 0, 0], dtype=int)
    cheap = np.asarray([0, 1, 1], dtype=int)
    return capabilities, requirement, costs, penalty, expensive, cheap


__all__ = [
    "BetterResponseResult",
    "accessibility_margin",
    "all_profiles",
    "asynchronous_better_response",
    "exact_feasible_oracle",
    "is_feasible",
    "is_inclusion_minimal",
    "is_pure_nash",
    "marginal_utility",
    "potential",
    "pure_nash_profiles",
    "recovery_time_upper_bound",
    "sufficient_penalty",
    "unbounded_efficiency_example",
    "weighted_deficit",
]
