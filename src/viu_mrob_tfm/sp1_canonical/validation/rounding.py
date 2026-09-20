"""Integer recovery operators for relaxed SP1 allocations."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld
from viu_mrob_tfm.sp1_canonical.validation.solvers import matrix_from_assignment


@dataclass(frozen=True, slots=True)
class IntegerResult:
    assignment: np.ndarray
    feasible: bool
    objective: float
    deficit_l1: float
    overassignment_l1: float
    repairs: int
    pruned: int = 0
    exchanges: int = 0


@dataclass(frozen=True, slots=True)
class AugmentingRepairResult:
    integer: IntegerResult
    augmentations: int
    maximum_chain_length: int
    nodes_explored: int
    search_failures: int
    failure_reason: str
    chain_lengths: tuple[int, ...]


def evaluate_integer(
    world: ResourceWorld,
    assignment: np.ndarray,
    costs: np.ndarray,
    *,
    repairs: int = 0,
    pruned: int = 0,
    exchanges: int = 0,
) -> IntegerResult:
    x = matrix_from_assignment(assignment, world.n_loads)
    coverage = np.einsum("ik,im->km", x, world.resources)
    deficit = np.maximum(world.requirements - coverage, 0.0)
    excess = np.maximum(coverage - world.requirements, 0.0)
    invalid = any(load >= 0 and not np.isfinite(costs[robot, load]) for robot, load in enumerate(assignment))
    safe_cost = np.where(np.isfinite(costs), costs, 0.0)
    objective = float(np.sum(safe_cost * x))
    return IntegerResult(
        assignment=np.asarray(assignment, dtype=int).copy(),
        feasible=bool(not invalid and np.all(deficit <= 1e-8)),
        objective=objective,
        deficit_l1=float(np.sum(deficit)),
        overassignment_l1=float(np.sum(excess)),
        repairs=int(repairs),
        pruned=int(pruned),
        exchanges=int(exchanges),
    )


def argmax_round(x: np.ndarray, *, margin: float = 0.0) -> np.ndarray:
    """Close a relaxed profile with an optional load-over-idle margin.

    ``margin`` is fixed by the experimental configuration.  A robot is kept
    idle unless its best load mass exceeds the idle mass by at least that
    amount.  The historical behaviour is preserved by the default ``0.0``.
    """

    if margin < 0.0:
        raise ValueError("margin must be nonnegative")
    x = np.clip(np.asarray(x, dtype=float), 0.0, None)
    idle = np.maximum(1.0 - x.sum(axis=1), 0.0)
    best_load = np.argmax(x, axis=1)
    best_mass = x[np.arange(x.shape[0]), best_load]
    return np.where(best_mass >= idle + float(margin), best_load, -1).astype(int)


def categorical_round(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=float), 0.0, None)
    assignments = np.full(x.shape[0], -1, dtype=int)
    for robot in range(x.shape[0]):
        idle = max(1.0 - float(np.sum(x[robot])), 0.0)
        probabilities = np.r_[x[robot], idle]
        total = float(np.sum(probabilities))
        if total <= 1e-15:
            continue
        probabilities /= total
        choice = int(rng.choice(len(probabilities), p=probabilities))
        assignments[robot] = -1 if choice == x.shape[1] else choice
    return assignments


def repair_assignment(
    world: ResourceWorld,
    assignment: np.ndarray,
    costs: np.ndarray,
    *,
    prune: bool = True,
    local_exchange: bool = True,
    compress: bool = True,
) -> IntegerResult:
    """Greedily reduce deficit and optionally improve a feasible coalition.

    The phase switches exist for predeclared ablations.  Defaults reproduce the
    historical complete operator: repair, pruning, one-for-one exchanges and
    two-for-one compression.
    """

    current = np.asarray(assignment, dtype=int).copy()
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)

    def deficit_score(candidate: np.ndarray) -> float:
        x = matrix_from_assignment(candidate, world.n_loads)
        coverage = np.einsum("ik,ikm->km", x, normalized)
        return float(np.sum(np.maximum(1.0 - coverage, 0.0)))

    repairs = 0
    for _ in range(world.n_robots * max(world.n_loads, 1)):
        base_score = deficit_score(current)
        if base_score <= 1e-9:
            break
        candidates: list[tuple[float, float, int, int]] = []
        for robot in range(world.n_robots):
            old_load = int(current[robot])
            old_cost = float(costs[robot, old_load]) if old_load >= 0 and np.isfinite(costs[robot, old_load]) else 0.0
            for load in range(world.n_loads):
                if load == old_load or not np.isfinite(costs[robot, load]):
                    continue
                trial = current.copy()
                trial[robot] = load
                improvement = base_score - deficit_score(trial)
                if improvement > 1e-12:
                    incremental_cost = float(costs[robot, load]) - old_cost
                    candidates.append((-improvement, incremental_cost, robot, load))
        if not candidates:
            break
        _, _, robot, load = min(candidates)
        current[robot] = load
        repairs += 1
    pruned = 0
    exchanges = 0
    if deficit_score(current) <= 1e-9 and prune:
        # Cost-first deletion: remove a member whenever every aggregate
        # requirement remains covered.
        while True:
            deletion_candidates: list[tuple[float, int]] = []
            for robot in np.flatnonzero(current >= 0):
                trial = current.copy()
                trial[int(robot)] = -1
                if evaluate_integer(world, trial, costs).feasible:
                    load = int(current[int(robot)])
                    deletion_candidates.append((-float(costs[int(robot), load]), int(robot)))
            if not deletion_candidates:
                break
            _, robot = min(deletion_candidates)
            current[robot] = -1
            pruned += 1

        # Replace one expensive member by one cheaper idle robot.
        improved = bool(local_exchange)
        while improved:
            improved = False
            replacement_candidates: list[tuple[float, int, int, int]] = []
            for old_robot in np.flatnonzero(current >= 0):
                load = int(current[int(old_robot)])
                old_cost = float(costs[int(old_robot), load])
                for new_robot in np.flatnonzero(current < 0):
                    if not np.isfinite(costs[int(new_robot), load]):
                        continue
                    saving = old_cost - float(costs[int(new_robot), load])
                    if saving <= 1e-12:
                        continue
                    trial = current.copy()
                    trial[int(old_robot)] = -1
                    trial[int(new_robot)] = load
                    if evaluate_integer(world, trial, costs).feasible:
                        replacement_candidates.append((-saving, int(old_robot), int(new_robot), load))
            if replacement_candidates:
                _, old_robot, new_robot, load = min(replacement_candidates)
                current[old_robot] = -1
                current[new_robot] = load
                exchanges += 1
                improved = True

        # Two-for-one compression within a coalition.
        compression_candidates: list[tuple[float, int, int, int, int]] = []
        idle_robots = np.flatnonzero(current < 0)
        if local_exchange and compress:
            for load in range(world.n_loads):
                members = np.flatnonzero(current == load)
                for left_index, left in enumerate(members):
                    for right in members[left_index + 1 :]:
                        removed_cost = float(costs[int(left), load] + costs[int(right), load])
                        for replacement in idle_robots:
                            if not np.isfinite(costs[int(replacement), load]):
                                continue
                            saving = removed_cost - float(costs[int(replacement), load])
                            if saving <= 1e-12:
                                continue
                            trial = current.copy()
                            trial[int(left)] = -1
                            trial[int(right)] = -1
                            trial[int(replacement)] = load
                            if evaluate_integer(world, trial, costs).feasible:
                                compression_candidates.append((-saving, int(left), int(right), int(replacement), load))
        if compression_candidates:
            _, left, right, replacement, load = min(compression_candidates)
            current[left] = -1
            current[right] = -1
            current[replacement] = load
            exchanges += 1
            pruned += 1

    return evaluate_integer(world, current, costs, repairs=repairs, pruned=pruned, exchanges=exchanges)


def repair_assignment_augmenting(
    world: ResourceWorld,
    assignment: np.ndarray,
    costs: np.ndarray,
    *,
    max_chain_length: int = 8,
    max_nodes_per_augmentation: int = 5_000,
    candidates_per_load: int = 16,
    prune: bool = True,
    local_exchange: bool = True,
    compress: bool = True,
) -> AugmentingRepairResult:
    """Repair a closure through bounded augmenting reassignment chains.

    Unlike :func:`repair_assignment`, an intermediate move may increase the
    total deficit by taking a useful robot from another coalition.  The search
    then follows the newly deficient coalition until it finds a state whose
    total normalized deficit is strictly smaller than at the chain origin.
    This is a bounded deterministic heuristic, not an exact integer solver.
    """

    if max_chain_length < 1 or max_nodes_per_augmentation < 1 or candidates_per_load < 1:
        raise ValueError("augmenting-search bounds must be positive")
    current = np.asarray(assignment, dtype=int).copy()
    if current.shape != (world.n_robots,):
        raise ValueError(f"assignment must have shape {(world.n_robots,)}")
    normalized = world.resources[:, None, :] / np.maximum(world.requirements[None, :, :], 1e-12)

    def deficit(candidate: np.ndarray) -> tuple[float, np.ndarray]:
        x = matrix_from_assignment(candidate, world.n_loads)
        coverage = np.einsum("ik,ikm->km", x, normalized)
        missing = np.maximum(1.0 - coverage, 0.0)
        return float(np.sum(missing)), missing

    def incremental_cost(candidate: np.ndarray, origin: np.ndarray) -> float:
        total = 0.0
        for robot, load in enumerate(candidate):
            old_load = int(origin[robot])
            old_cost = float(costs[robot, old_load]) if old_load >= 0 and np.isfinite(costs[robot, old_load]) else 0.0
            new_cost = float(costs[robot, load]) if load >= 0 and np.isfinite(costs[robot, load]) else 0.0
            total += new_cost - old_cost
        return total

    def find_chain(origin: np.ndarray, origin_score: float) -> tuple[np.ndarray | None, int, int]:
        # Entries are ordered by deficit first, then depth and cost.  A state
        # below the origin score is retained, but the bounded search continues
        # to prefer a larger reduction within the same deterministic budget.
        queue: list[tuple[float, int, float, int, tuple[int, ...], tuple[int, ...]]] = []
        serial = 0
        origin_tuple = tuple(int(value) for value in origin)
        heapq.heappush(queue, (origin_score, 0, 0.0, serial, origin_tuple, ()))
        visited = {origin_tuple: 0}
        best: tuple[float, float, int, np.ndarray] | None = None
        explored = 0
        while queue and explored < max_nodes_per_augmentation:
            score, depth, _, _, state_tuple, moved_robots = heapq.heappop(queue)
            state = np.asarray(state_tuple, dtype=int)
            explored += 1
            if depth > 0 and score < origin_score - 1e-12:
                candidate_key = (score, incremental_cost(state, origin), depth, state)
                if best is None or candidate_key[:3] < best[:3]:
                    best = candidate_key
                # A one-step improvement is exactly the old greedy move.  For
                # longer paths we still explore peers at this depth so a chain
                # with a materially larger reduction can win.
                if score <= 1e-9:
                    break
            if depth >= max_chain_length:
                continue
            _, missing = deficit(state)
            deficient_loads = np.flatnonzero(np.any(missing > 1e-10, axis=1))
            if not deficient_loads.size:
                continue
            moved = set(moved_robots)
            for load in deficient_loads:
                ranked: list[tuple[float, float, int]] = []
                for robot in range(world.n_robots):
                    if robot in moved or int(state[robot]) == int(load) or not np.isfinite(costs[robot, load]):
                        continue
                    useful = float(np.sum(np.minimum(missing[load], normalized[robot, load])))
                    if useful <= 1e-12:
                        continue
                    old_load = int(state[robot])
                    old_cost = float(costs[robot, old_load]) if old_load >= 0 and np.isfinite(costs[robot, old_load]) else 0.0
                    ranked.append((-useful, float(costs[robot, load]) - old_cost, robot))
                for _, _, robot in sorted(ranked)[:candidates_per_load]:
                    trial = state.copy()
                    trial[robot] = int(load)
                    trial_tuple = tuple(int(value) for value in trial)
                    next_depth = depth + 1
                    if visited.get(trial_tuple, max_chain_length + 1) <= next_depth:
                        continue
                    visited[trial_tuple] = next_depth
                    trial_score, _ = deficit(trial)
                    serial += 1
                    heapq.heappush(
                        queue,
                        (
                            trial_score,
                            next_depth,
                            incremental_cost(trial, origin),
                            serial,
                            trial_tuple,
                            tuple((*moved_robots, robot)),
                        ),
                    )
        if best is None:
            return None, 0, explored
        return best[3], int(best[2]), explored

    augmentations = 0
    nodes_explored = 0
    search_failures = 0
    chain_lengths: list[int] = []
    for _ in range(world.n_robots * max(world.n_loads, 1)):
        score, _ = deficit(current)
        if score <= 1e-9:
            break
        improved, length, explored = find_chain(current, score)
        nodes_explored += explored
        if improved is None:
            search_failures += 1
            break
        current = improved
        augmentations += 1
        chain_lengths.append(length)

    base = evaluate_integer(world, current, costs, repairs=augmentations)
    if base.feasible and (prune or local_exchange):
        polished = repair_assignment(
            world,
            current,
            costs,
            prune=prune,
            local_exchange=local_exchange,
            compress=compress,
        )
        integer = evaluate_integer(
            world,
            polished.assignment,
            costs,
            repairs=augmentations,
            pruned=polished.pruned,
            exchanges=polished.exchanges,
        )
    else:
        integer = base
    failure_reason = "none" if integer.feasible else "no_augmenting_chain_within_limits"
    return AugmentingRepairResult(
        integer=integer,
        augmentations=augmentations,
        maximum_chain_length=max(chain_lengths, default=0),
        nodes_explored=nodes_explored,
        search_failures=search_failures,
        failure_reason=failure_reason,
        chain_lengths=tuple(chain_lengths),
    )


def best_of_samples(
    world: ResourceWorld,
    x: np.ndarray,
    costs: np.ndarray,
    *,
    samples: int,
    rng: np.random.Generator,
    repair: bool,
) -> IntegerResult:
    if samples < 1:
        raise ValueError("samples must be positive")
    candidates: list[IntegerResult] = []
    for _ in range(samples):
        assignment = categorical_round(x, rng)
        result = repair_assignment(world, assignment, costs) if repair else evaluate_integer(world, assignment, costs)
        candidates.append(result)
    return min(candidates, key=lambda result: (not result.feasible, result.deficit_l1, result.objective, result.repairs))


__all__ = [
    "AugmentingRepairResult",
    "IntegerResult",
    "argmax_round",
    "best_of_samples",
    "categorical_round",
    "evaluate_integer",
    "repair_assignment",
    "repair_assignment_augmenting",
]
