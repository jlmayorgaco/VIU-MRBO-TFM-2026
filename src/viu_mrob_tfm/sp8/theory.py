"""Network-visible route game used by the canonical SP8 study.

SP8 keeps the finite route catalogue from SP7 and changes only the information
layer.  An undirected communication graph determines which pairwise resource
conflicts enter each player's payoff.  The resulting game remains an exact
potential game, but its equilibria need not be equilibria of the global game.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import prod
from typing import Iterable

import numpy as np


RouteResources = tuple[tuple[frozenset[str], ...], ...]


@dataclass(frozen=True, slots=True)
class NetworkResponseResult:
    profile: np.ndarray
    potential_trace: np.ndarray
    strict_moves: int
    activations: int
    visible_nash: bool


@dataclass(frozen=True, slots=True)
class ExhaustiveOracleResult:
    profile: np.ndarray | None
    social_cost: float
    evaluated_profiles: int
    certified: bool
    profile_space: int


def validate_adjacency(adjacency: np.ndarray, n_agents: int) -> np.ndarray:
    graph = np.asarray(adjacency, dtype=bool)
    if graph.shape != (int(n_agents), int(n_agents)):
        raise ValueError("The communication adjacency has an invalid shape.")
    if np.any(np.diag(graph)):
        raise ValueError("The communication adjacency must have a zero diagonal.")
    if not np.array_equal(graph, graph.T):
        raise ValueError("The network-visible potential requires an undirected graph.")
    return graph


def all_profiles(route_resources: RouteResources) -> Iterable[np.ndarray]:
    for profile in product(*(range(len(routes)) for routes in route_resources)):
        yield np.asarray(profile, dtype=int)


def profile_space_size(route_resources: RouteResources) -> int:
    return int(prod(len(routes) for routes in route_resources))


def base_cost(profile: np.ndarray, base_costs: np.ndarray) -> float:
    routes = np.asarray(profile, dtype=int)
    return float(sum(float(base_costs[i, route]) for i, route in enumerate(routes)))


def shared_resource_count(
    agent_i: int,
    route_i: int,
    agent_j: int,
    route_j: int,
    route_resources: RouteResources,
) -> int:
    return len(
        route_resources[int(agent_i)][int(route_i)]
        & route_resources[int(agent_j)][int(route_j)]
    )


def global_conflict_pairs(profile: np.ndarray, route_resources: RouteResources) -> int:
    routes = np.asarray(profile, dtype=int)
    total = 0
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            total += shared_resource_count(i, int(routes[i]), j, int(routes[j]), route_resources)
    return int(total)


def visible_conflict_pairs(
    profile: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
) -> int:
    routes = np.asarray(profile, dtype=int)
    graph = validate_adjacency(adjacency, len(routes))
    total = 0
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            if graph[i, j]:
                total += shared_resource_count(i, int(routes[i]), j, int(routes[j]), route_resources)
    return int(total)


def missed_conflict_pairs(
    profile: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
) -> int:
    return global_conflict_pairs(profile, route_resources) - visible_conflict_pairs(
        profile, route_resources, adjacency
    )


def social_cost(
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
) -> float:
    return base_cost(profile, base_costs) + float(penalty) * global_conflict_pairs(
        profile, route_resources
    )


def network_potential(
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
    penalty: float,
) -> float:
    return -base_cost(profile, base_costs) - float(penalty) * visible_conflict_pairs(
        profile, route_resources, adjacency
    )


def visible_utility(
    agent: int,
    route: int,
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
    penalty: float,
) -> float:
    routes = np.asarray(profile, dtype=int).copy()
    graph = validate_adjacency(adjacency, len(routes))
    routes[int(agent)] = int(route)
    conflicts = 0
    for other in range(len(routes)):
        if other == int(agent) or not graph[int(agent), other]:
            continue
        conflicts += shared_resource_count(
            int(agent), int(route), other, int(routes[other]), route_resources
        )
    return -float(base_costs[int(agent), int(route)]) - float(penalty) * conflicts


def is_visible_nash(
    profile: np.ndarray,
    base_costs: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
    penalty: float,
    *,
    atol: float = 1e-10,
) -> bool:
    routes = np.asarray(profile, dtype=int)
    for agent, current_route in enumerate(routes):
        current = visible_utility(
            agent,
            int(current_route),
            routes,
            base_costs,
            route_resources,
            adjacency,
            penalty,
        )
        for route in range(len(route_resources[agent])):
            if route == int(current_route):
                continue
            if visible_utility(
                agent,
                route,
                routes,
                base_costs,
                route_resources,
                adjacency,
                penalty,
            ) > current + atol:
                return False
    return True


def verify_exact_network_potential(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
    penalty: float,
    *,
    atol: float = 1e-10,
) -> bool:
    for profile in all_profiles(route_resources):
        for agent, old_route in enumerate(profile):
            for new_route in range(len(route_resources[agent])):
                if new_route == int(old_route):
                    continue
                candidate = profile.copy()
                candidate[agent] = new_route
                utility_delta = visible_utility(
                    agent,
                    new_route,
                    profile,
                    base_costs,
                    route_resources,
                    adjacency,
                    penalty,
                ) - visible_utility(
                    agent,
                    int(old_route),
                    profile,
                    base_costs,
                    route_resources,
                    adjacency,
                    penalty,
                )
                potential_delta = network_potential(
                    candidate,
                    base_costs,
                    route_resources,
                    adjacency,
                    penalty,
                ) - network_potential(
                    profile,
                    base_costs,
                    route_resources,
                    adjacency,
                    penalty,
                )
                if not np.isclose(utility_delta, potential_delta, atol=atol):
                    return False
    return True


def asynchronous_visible_better_response(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    adjacency: np.ndarray,
    penalty: float,
    *,
    initial_profile: np.ndarray | None = None,
    seed: int = 0,
    atol: float = 1e-10,
) -> NetworkResponseResult:
    n_agents = len(route_resources)
    profile = (
        np.zeros(n_agents, dtype=int)
        if initial_profile is None
        else np.asarray(initial_profile, dtype=int).copy()
    )
    rng = np.random.default_rng(int(seed))
    trace = [network_potential(profile, base_costs, route_resources, adjacency, penalty)]
    strict_moves = 0
    activations = 0
    bound = profile_space_size(route_resources) - 1
    while True:
        moved = False
        for agent in rng.permutation(n_agents):
            agent = int(agent)
            activations += 1
            old_route = int(profile[agent])
            old_utility = visible_utility(
                agent,
                old_route,
                profile,
                base_costs,
                route_resources,
                adjacency,
                penalty,
            )
            alternatives = []
            for route in range(len(route_resources[agent])):
                value = visible_utility(
                    agent,
                    route,
                    profile,
                    base_costs,
                    route_resources,
                    adjacency,
                    penalty,
                )
                if value > old_utility + atol:
                    alternatives.append((value, -route))
            if not alternatives:
                continue
            profile[agent] = -max(alternatives)[1]
            current_potential = network_potential(
                profile, base_costs, route_resources, adjacency, penalty
            )
            if current_potential <= trace[-1] + atol:
                raise RuntimeError("Strict visible improvement failed to increase the potential.")
            trace.append(current_potential)
            strict_moves += 1
            moved = True
        if not moved:
            break
        if strict_moves > bound:
            raise RuntimeError("Finite-profile improvement bound exceeded.")
    return NetworkResponseResult(
        profile=profile,
        potential_trace=np.asarray(trace, dtype=float),
        strict_moves=strict_moves,
        activations=activations,
        visible_nash=is_visible_nash(
            profile, base_costs, route_resources, adjacency, penalty
        ),
    )


def exhaustive_global_oracle(
    base_costs: np.ndarray,
    route_resources: RouteResources,
    penalty: float,
    *,
    max_profiles: int,
) -> ExhaustiveOracleResult:
    space = profile_space_size(route_resources)
    if space > int(max_profiles):
        return ExhaustiveOracleResult(None, float("nan"), 0, False, space)
    best_profile: np.ndarray | None = None
    best_cost = float("inf")
    evaluated = 0
    for profile in all_profiles(route_resources):
        evaluated += 1
        value = social_cost(profile, base_costs, route_resources, penalty)
        key = tuple(int(item) for item in profile)
        best_key = tuple(int(item) for item in best_profile) if best_profile is not None else None
        if value < best_cost - 1e-12 or (
            np.isclose(value, best_cost, atol=1e-12) and (best_key is None or key < best_key)
        ):
            best_cost = value
            best_profile = profile.copy()
    return ExhaustiveOracleResult(best_profile, best_cost, evaluated, True, space)


def retransmission_failure_probability(packet_loss: float, transmissions: int) -> float:
    probability = float(packet_loss)
    attempts = int(transmissions)
    if not 0.0 <= probability <= 1.0:
        raise ValueError("packet_loss must lie in [0, 1].")
    if attempts < 0:
        raise ValueError("transmissions must be non-negative.")
    return probability**attempts


__all__ = [
    "ExhaustiveOracleResult",
    "NetworkResponseResult",
    "RouteResources",
    "all_profiles",
    "asynchronous_visible_better_response",
    "base_cost",
    "exhaustive_global_oracle",
    "global_conflict_pairs",
    "is_visible_nash",
    "missed_conflict_pairs",
    "network_potential",
    "profile_space_size",
    "retransmission_failure_probability",
    "shared_resource_count",
    "social_cost",
    "validate_adjacency",
    "verify_exact_network_potential",
    "visible_conflict_pairs",
    "visible_utility",
]
