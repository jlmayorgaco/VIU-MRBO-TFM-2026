"""Finite route-congestion game for the canonical SP7 traffic study.

Coalitions are the players and candidate routes are their actions.  A resource
is a named conflict zone in configuration space.  The model is intentionally
unweighted: footprint differences belong to route feasibility and clearance
times, not to the strategic congestion count.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import numpy as np


RouteResources = tuple[tuple[frozenset[str], ...], ...]


@dataclass(frozen=True, slots=True)
class RouteResponseResult:
    profile: np.ndarray
    potential_trace: np.ndarray
    profiles: tuple[tuple[int, ...], ...]
    activations: int
    strict_moves: int


def all_profiles(route_resources: RouteResources) -> Iterable[np.ndarray]:
    """Enumerate every route profile for a finite, possibly asymmetric game."""

    ranges = [range(len(routes)) for routes in route_resources]
    for values in product(*ranges):
        yield np.asarray(values, dtype=int)


def resource_counts(profile: np.ndarray, route_resources: RouteResources) -> dict[str, int]:
    counts: dict[str, int] = {}
    for agent, route in enumerate(np.asarray(profile, dtype=int)):
        for resource in route_resources[agent][int(route)]:
            counts[resource] = counts.get(resource, 0) + 1
    return counts


def conflict_pairs(profile: np.ndarray, route_resources: RouteResources) -> int:
    """Return the number of unordered coalition pairs sharing resources."""

    return int(sum(count * (count - 1) // 2 for count in resource_counts(profile, route_resources).values()))


def base_cost(profile: np.ndarray, base_costs: np.ndarray) -> float:
    routes = np.asarray(profile, dtype=int)
    return float(sum(float(base_costs[agent, route]) for agent, route in enumerate(routes)))


def potential(
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
) -> float:
    """Exact potential: negative route cost and pairwise resource congestion."""

    return -base_cost(profile, base_costs) - float(penalty) * conflict_pairs(profile, route_resources)


def utility(
    agent: int,
    route: int,
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
) -> float:
    """Player utility for one route against the other players' fixed routes."""

    candidate = np.asarray(profile, dtype=int).copy()
    candidate[int(agent)] = int(route)
    counts = resource_counts(candidate, route_resources)
    own_resources = route_resources[int(agent)][int(route)]
    congestion_with_others = sum(counts[resource] - 1 for resource in own_resources)
    return -float(base_costs[int(agent), int(route)]) - float(penalty) * float(congestion_with_others)


def is_pure_nash(
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
    *,
    atol: float = 1e-10,
) -> bool:
    current = np.asarray(profile, dtype=int)
    for agent, current_route in enumerate(current):
        current_utility = utility(agent, int(current_route), current, base_costs, route_resources, penalty)
        for route in range(len(route_resources[agent])):
            if route == int(current_route):
                continue
            if utility(agent, route, current, base_costs, route_resources, penalty) > current_utility + atol:
                return False
    return True


def pure_nash_profiles(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
) -> list[np.ndarray]:
    return [
        profile
        for profile in all_profiles(route_resources)
        if is_pure_nash(profile, base_costs, route_resources, penalty)
    ]


def verify_exact_potential_identity(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
    *,
    atol: float = 1e-10,
) -> bool:
    """Exhaustively check unilateral utility and potential differences."""

    for profile in all_profiles(route_resources):
        for agent, old_route in enumerate(profile):
            for new_route in range(len(route_resources[agent])):
                if new_route == int(old_route):
                    continue
                deviated = profile.copy()
                deviated[agent] = new_route
                utility_delta = utility(agent, new_route, profile, base_costs, route_resources, penalty) - utility(
                    agent, int(old_route), profile, base_costs, route_resources, penalty
                )
                potential_delta = potential(deviated, base_costs, route_resources, penalty) - potential(
                    profile, base_costs, route_resources, penalty
                )
                if not np.isclose(utility_delta, potential_delta, atol=atol):
                    return False
    return True


def conflict_free_penalty_threshold(
    base_costs: np.ndarray,
    route_resources: RouteResources,
) -> float:
    """Return the sufficient accessibility threshold for conflict-free Nash.

    For every conflicted profile, at least one unilateral route change must
    reduce the number of conflict pairs.  The returned value is the largest,
    over profiles, of the smallest penalty needed to make such a change a
    strict potential improvement.  Infinity means that the accessibility
    assumption fails.
    """

    profile_thresholds: list[float] = []
    for profile in all_profiles(route_resources):
        before_pairs = conflict_pairs(profile, route_resources)
        if before_pairs == 0:
            continue
        before_base = base_cost(profile, base_costs)
        deviations: list[float] = []
        for agent, old_route in enumerate(profile):
            for new_route in range(len(route_resources[agent])):
                if new_route == int(old_route):
                    continue
                candidate = profile.copy()
                candidate[agent] = new_route
                pair_reduction = before_pairs - conflict_pairs(candidate, route_resources)
                if pair_reduction <= 0:
                    continue
                base_increase = base_cost(candidate, base_costs) - before_base
                deviations.append(max(0.0, base_increase / float(pair_reduction)))
        if not deviations:
            return float("inf")
        profile_thresholds.append(min(deviations))
    return float(max(profile_thresholds, default=0.0))


def asynchronous_better_response(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
    *,
    initial_profile: np.ndarray | None = None,
    seed: int = 0,
    atol: float = 1e-10,
) -> RouteResponseResult:
    """Run fair shuffled strict better responses until a pure Nash profile."""

    n_agents = len(route_resources)
    profile = np.zeros(n_agents, dtype=int) if initial_profile is None else np.asarray(initial_profile, dtype=int).copy()
    rng = np.random.default_rng(int(seed))
    trace = [potential(profile, base_costs, route_resources, penalty)]
    profiles = [tuple(int(value) for value in profile)]
    activations = 0
    strict_moves = 0
    profile_bound = int(np.prod([len(routes) for routes in route_resources]))
    while True:
        moved_in_sweep = False
        for agent in rng.permutation(n_agents):
            agent = int(agent)
            activations += 1
            current_route = int(profile[agent])
            current_utility = utility(agent, current_route, profile, base_costs, route_resources, penalty)
            candidates: list[tuple[float, int]] = []
            for route in range(len(route_resources[agent])):
                if route == current_route:
                    continue
                value = utility(agent, route, profile, base_costs, route_resources, penalty)
                if value > current_utility + atol:
                    candidates.append((value, -route))
            if not candidates:
                continue
            new_route = -max(candidates)[1]
            profile[agent] = new_route
            new_potential = potential(profile, base_costs, route_resources, penalty)
            if new_potential <= trace[-1] + atol:
                raise RuntimeError("A strict utility improvement did not increase the exact potential.")
            trace.append(new_potential)
            profiles.append(tuple(int(value) for value in profile))
            strict_moves += 1
            moved_in_sweep = True
        if not moved_in_sweep:
            break
        if strict_moves >= profile_bound:
            raise RuntimeError("Strict potential ascent exceeded the finite-profile bound.")
    return RouteResponseResult(
        profile=profile,
        potential_trace=np.asarray(trace, dtype=float),
        profiles=tuple(profiles),
        activations=activations,
        strict_moves=strict_moves,
    )


__all__ = [
    "RouteResources",
    "RouteResponseResult",
    "all_profiles",
    "asynchronous_better_response",
    "base_cost",
    "conflict_free_penalty_threshold",
    "conflict_pairs",
    "is_pure_nash",
    "potential",
    "pure_nash_profiles",
    "resource_counts",
    "utility",
    "verify_exact_potential_identity",
]
