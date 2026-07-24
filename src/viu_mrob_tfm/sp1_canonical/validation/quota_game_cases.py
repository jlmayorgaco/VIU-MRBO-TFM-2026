"""Deterministic scalar-quota cases and the separate GRAPE-S service domain.

The service benchmark deliberately does not reuse the scalar-capacity labels:
the version-of-record GRAPE-S formulation uses integer service requirements
and service-providing robots.  Weighted-GRAPE remains an adaptation in the
primary scalar benchmark.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .quota_game_core import (
    QuotaGraph,
    QuotaWorld,
    ServiceWorld,
    make_manual_quota_world,
    make_quota_graph,
    stable_hash,
)


def _line_positions(n: int, *, offset: float = 0.0) -> np.ndarray:
    return np.column_stack(
        [np.arange(n, dtype=float) + float(offset), np.zeros(n, dtype=float)]
    )


def make_chain_world(
    length: int,
    *,
    adversarial: bool = False,
    seed: int = 0,
) -> tuple[QuotaWorld, np.ndarray]:
    """Return a world whose supplied initial state needs a chain of ``length``.

    Loads and robots have unit capacity and exact unit quotas.  Robot ``i`` can
    serve loads ``i-1`` and ``i`` (when those indexes exist).  The initial
    assignment shifts the first ``length`` robots one load to the right and
    leaves the last robot idle.  Repairing load zero therefore requires the
    complete alternating chain.
    """

    if length < 1:
        raise ValueError("length must be positive")
    n = length
    k = length
    compatibility = np.zeros((n, k), dtype=bool)
    for robot in range(n):
        compatibility[robot, robot] = True
        if robot > 0:
            compatibility[robot, robot - 1] = True
    if adversarial and n > 3:
        # Distractor edges enlarge the search tree without shortening the
        # unique quota-feasible alternating chain.
        for robot in range(2, n):
            compatibility[robot, min(k - 1, robot + 1)] = True
    witness = np.arange(k, dtype=int)
    initial = np.full(n, k, dtype=int)
    if n > 1:
        initial[1:] = np.arange(0, k - 1, dtype=int)
    rng = np.random.default_rng(seed)
    robot_positions = _line_positions(n)
    load_positions = _line_positions(k, offset=0.1)
    if seed:
        robot_positions[:, 1] = rng.uniform(-0.05, 0.05, size=n)
        load_positions[:, 1] = rng.uniform(-0.05, 0.05, size=k)
    world = make_manual_quota_world(
        case_id=f"e9_chain_{length}{'_adversarial' if adversarial else ''}",
        robot_positions=robot_positions,
        load_positions=load_positions,
        capacities=np.ones(n),
        lower_quotas=np.ones(k),
        upper_quotas=np.ones(k),
        compatibility=compatibility,
        witness_assignment=witness,
    )
    return world, initial


def deterministic_case_catalog() -> list[dict[str, Any]]:
    """Construct the ten predeclared E0 analytical controls."""

    cases: list[dict[str, Any]] = []

    def add(
        name: str,
        capacities: list[float],
        lower: list[float],
        upper: list[float],
        compatibility: list[list[int]],
        witness: list[int],
        initial: list[int] | None = None,
        note: str = "",
    ) -> None:
        n, k = len(capacities), len(lower)
        cases.append(
            {
                "case": name,
                "world": make_manual_quota_world(
                    case_id=f"e0_{name}",
                    robot_positions=_line_positions(n),
                    load_positions=_line_positions(k, offset=0.25),
                    capacities=np.asarray(capacities),
                    lower_quotas=np.asarray(lower),
                    upper_quotas=np.asarray(upper),
                    compatibility=np.asarray(compatibility, dtype=bool),
                    witness_assignment=np.asarray(witness, dtype=int),
                ),
                "initial_assignment": (
                    np.asarray(initial, dtype=int) if initial is not None else None
                ),
                "analytical_note": note,
            }
        )

    add(
        "hungarian_slots",
        [1, 1, 1, 1],
        [2, 2],
        [4, 4],
        [[1, 1]] * 4,
        [0, 0, 1, 1],
        note="Unit capacities and integer slots admit a Hungarian reduction.",
    )
    add(
        "argmax_breaks_quotas",
        [1, 1, 1, 1],
        [2, 2],
        [2, 2],
        [[1, 1]] * 4,
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        "A valid fractional state can have an invalid common argmax.",
    )
    add(
        "symmetric_random_rounding",
        [1, 1, 1, 1],
        [2, 2],
        [2, 2],
        [[1, 1]] * 4,
        [0, 0, 1, 1],
        note="Independent categorical rounding has nonzero quota-failure probability.",
    )
    add(
        "three_partition_small",
        [4, 4, 4, 3, 3, 3],
        [7, 7, 7],
        [7, 7, 7],
        [[1, 1, 1]] * 6,
        [0, 1, 2, 0, 1, 2],
        note="Exact weighted quotas expose the combinatorial structure.",
    )
    chain1, initial1 = make_chain_world(1)
    cases.append(
        {
            "case": "chain_length_1",
            "world": chain1,
            "initial_assignment": initial1,
            "analytical_note": "One alternating displacement repairs the deficit.",
        }
    )
    add(
        "swap_length_2",
        [1, 1],
        [1, 1],
        [1, 1],
        [[1, 1], [1, 1]],
        [0, 1],
        [1, 0],
        "A two-robot exchange improves distance while preserving exact quotas.",
    )
    chain3, initial3 = make_chain_world(3)
    cases.append(
        {
            "case": "chain_length_3",
            "world": chain3,
            "initial_assignment": initial3,
            "analytical_note": "A repair requires an alternating chain of at least three.",
        }
    )
    add(
        "critical_robot",
        [4, 1, 1],
        [4, 2],
        [4, 2],
        [[1, 0], [0, 1], [0, 1]],
        [0, 1, 1],
        note="The high-capacity robot is critical and has one compatible load.",
    )
    add(
        "narrow_upper_quota",
        [2, 2, 1],
        [3, 2],
        [3, 2],
        [[1, 1], [1, 1], [1, 1]],
        [0, 1, 0],
        [0, 0, 1],
        "A lower-feasible greedy state violates a narrow upper quota.",
    )
    chain5, initial5 = make_chain_world(5, adversarial=True)
    cases.append(
        {
            "case": "no_short_path_global_solution",
            "world": chain5,
            "initial_assignment": initial5,
            "analytical_note": "No repair of length below five exists, but a global solution does.",
        }
    )
    return cases


def make_service_world(
    *,
    n: int,
    service_types: int,
    services_per_robot: int,
    task_fraction: float,
    seed: int,
    config: Mapping[str, Any],
) -> ServiceWorld:
    """Generate an integer-service world with a hidden feasible partition."""

    if not 1 <= services_per_robot <= service_types:
        raise ValueError("services_per_robot must be in [1, service_types]")
    rng = np.random.default_rng(seed)
    k = max(2, int(math.ceil(task_fraction * n)))
    robot_services = np.zeros((n, service_types), dtype=np.int8)
    for robot in range(n):
        selected = rng.choice(service_types, size=services_per_robot, replace=False)
        robot_services[robot, selected] = 1
    witness = np.arange(n, dtype=int) % k
    rng.shuffle(witness)
    requirements = np.zeros((k, service_types), dtype=int)
    utilities = rng.uniform(0.8, 1.2, size=(k, service_types))
    for robot, task in enumerate(witness):
        available = np.flatnonzero(robot_services[robot])
        service = int(available[(robot + task) % available.size])
        requirements[task, service] += 1
    # Build a scalar geometry shell only to reuse the audited graph constructor.
    shell = make_manual_quota_world(
        case_id=f"service_shell_n{n}_s{service_types}_r{services_per_robot}_{seed}",
        robot_positions=rng.uniform(0.0, 100.0, size=(n, 2)),
        load_positions=rng.uniform(0.0, 100.0, size=(k, 2)),
        capacities=np.ones(n),
        lower_quotas=np.bincount(witness, minlength=k).astype(float),
        upper_quotas=np.bincount(witness, minlength=k).astype(float),
        compatibility=np.ones((n, k), dtype=bool),
        witness_assignment=witness,
    )
    graph = make_quota_graph(shell, "rdisk_degree_8", config)
    return ServiceWorld(
        seed=seed,
        world_id=(
            f"e10_n{n}_s{service_types}_r{services_per_robot}_seed{seed}"
        ),
        robot_services=robot_services,
        task_requirements=requirements,
        task_service_utilities=utilities,
        graph=graph,
    )


def evaluate_service_assignment(
    world: ServiceWorld,
    tasks: np.ndarray,
    provided_services: np.ndarray,
) -> dict[str, Any]:
    """Audit exact integer service coverage and exclusive robot assignment."""

    tasks = np.asarray(tasks, dtype=int)
    provided_services = np.asarray(provided_services, dtype=int)
    k, s = world.task_requirements.shape
    delivered = np.zeros((k, s), dtype=int)
    compatible = True
    for robot in range(world.n_robots):
        task, service = int(tasks[robot]), int(provided_services[robot])
        if task == k:
            continue
        if not (0 <= task < k and 0 <= service < s):
            compatible = False
            continue
        if world.robot_services[robot, service] != 1:
            compatible = False
            continue
        delivered[task, service] += 1
    deficit = np.maximum(world.task_requirements - delivered, 0)
    excess = np.maximum(delivered - world.task_requirements, 0)
    return {
        "feasible": bool(compatible and np.sum(deficit) == 0),
        "compatible": compatible,
        "deficit": int(np.sum(deficit)),
        "excess": int(np.sum(excess)),
        "robots_used": int(np.sum(tasks < k)),
        "delivered": delivered,
    }


@dataclass(frozen=True)
class ServiceAlgorithmResult:
    method: str
    tasks: np.ndarray
    services: np.ndarray
    logical_rounds: int
    unilateral_moves: int
    swaps: int
    packets: int
    bytes_total: int
    converged: bool
    deviation: str


def _grape_utility(
    world: ServiceWorld,
    robot: int,
    task: int,
    service: int,
    delivered: np.ndarray,
) -> float:
    if task >= world.n_tasks or world.robot_services[robot, service] == 0:
        return 0.0
    requirement = int(world.task_requirements[task, service])
    if requirement <= 0:
        return 0.0
    coalition = int(delivered[task, service])
    # Version-of-record service-vector utility: requirement-normalized reward
    # with coalition-size exponential attenuation.
    return float(
        world.task_service_utilities[task, service]
        / requirement
        * math.exp(1.0 - coalition / requirement)
    )


def run_grape_s(
    world: ServiceWorld,
    *,
    pairwise: bool,
    seed: int,
    max_rounds: int = 1000,
) -> ServiceAlgorithmResult:
    """Serialized faithful discrete-service GRAPE-S/Pair-GRAPE-S simulation."""

    rng = np.random.default_rng(seed)
    tasks = np.full(world.n_robots, world.n_tasks, dtype=int)
    services = np.full(world.n_robots, -1, dtype=int)
    packets = moves = swaps = 0
    converged = False
    rounds = 0
    for round_index in range(max_rounds):
        changed = False
        delivered = evaluate_service_assignment(world, tasks, services)["delivered"]
        for robot in rng.permutation(world.n_robots):
            old_task, old_service = int(tasks[robot]), int(services[robot])
            old_value = (
                _grape_utility(world, robot, old_task, old_service, delivered)
                if old_task < world.n_tasks
                else 0.0
            )
            best = (old_value, old_task, old_service)
            for task in range(world.n_tasks):
                for service in np.flatnonzero(world.robot_services[robot]):
                    value = _grape_utility(world, robot, task, int(service), delivered)
                    candidate = (value, -task, -int(service))
                    incumbent = (best[0], -best[1], -best[2])
                    if candidate > incumbent:
                        best = (value, task, int(service))
            if best[0] > old_value + 1.0e-12:
                if old_task < world.n_tasks:
                    delivered[old_task, old_service] -= 1
                tasks[robot], services[robot] = best[1], best[2]
                delivered[best[1], best[2]] += 1
                changed = True
                moves += 1
                packets += max(1, 2 * world.graph.diameter)
        if pairwise:
            metrics = evaluate_service_assignment(world, tasks, services)
            deficits = np.argwhere(
                metrics["delivered"] < world.task_requirements
            )
            for task, service in deficits:
                idle = [
                    int(r)
                    for r in np.flatnonzero(tasks == world.n_tasks)
                    if world.robot_services[r, service]
                ]
                if not idle:
                    continue
                replacement = idle[0]
                for displaced in np.flatnonzero(tasks < world.n_tasks):
                    old_task, old_service = int(tasks[displaced]), int(services[displaced])
                    if world.robot_services[replacement, old_service] == 0:
                        continue
                    if world.robot_services[displaced, service] == 0:
                        continue
                    tasks[replacement], services[replacement] = old_task, old_service
                    tasks[displaced], services[displaced] = int(task), int(service)
                    swaps += 1
                    changed = True
                    packets += max(1, 4 * world.graph.diameter)
                    break
        rounds = round_index + 1
        if not changed:
            converged = True
            break
    return ServiceAlgorithmResult(
        method="Pair-GRAPE-S" if pairwise else "GRAPE-S",
        tasks=tasks,
        services=services,
        logical_rounds=rounds,
        unilateral_moves=moves,
        swaps=swaps,
        packets=packets,
        bytes_total=packets * 40,
        converged=converged,
        deviation=(
            "Faithful discrete-service domain; serialized mutex emulates "
            "collision-free asynchronous partition updates."
        ),
    )


def run_service_greedy(
    world: ServiceWorld,
    *,
    method: str,
    seed: int,
) -> ServiceAlgorithmResult:
    """Service-domain Capacity-CBBA/QPG-extension comparators."""

    rng = np.random.default_rng(seed)
    tasks = np.full(world.n_robots, world.n_tasks, dtype=int)
    services = np.full(world.n_robots, -1, dtype=int)
    remaining = world.task_requirements.copy()
    packets = moves = 0
    candidates: list[tuple[float, int, int, int]] = []
    for robot in range(world.n_robots):
        for task in range(world.n_tasks):
            for service in np.flatnonzero(world.robot_services[robot]):
                if remaining[task, service] > 0:
                    score = float(world.task_service_utilities[task, service])
                    if method == "QPG-Multiservice-Extension":
                        score += float(remaining[task, service])
                    candidates.append((-score, robot, task, int(service)))
    rng.shuffle(candidates)
    candidates.sort()
    used: set[int] = set()
    for _, robot, task, service in candidates:
        if robot in used or remaining[task, service] <= 0:
            continue
        tasks[robot], services[robot] = task, service
        remaining[task, service] -= 1
        used.add(robot)
        moves += 1
        packets += max(1, 2 * int(world.graph.market_route_hops[task, robot]))
    return ServiceAlgorithmResult(
        method=method,
        tasks=tasks,
        services=services,
        logical_rounds=max(1, moves),
        unilateral_moves=moves,
        swaps=0,
        packets=packets,
        bytes_total=packets * 48,
        converged=True,
        deviation=(
            "Discrete-service adaptation of Capacity-CBBA."
            if method == "Capacity-CBBA-Services"
            else "Exploratory multiservice extension; not the scalar QPG theorem domain."
        ),
    )


def service_world_hash(world: ServiceWorld) -> str:
    return stable_hash(
        {
            "robots": world.robot_services.tolist(),
            "requirements": world.task_requirements.tolist(),
            "utilities": np.asarray(world.task_service_utilities).round(12).tolist(),
            "graph": world.graph.graph_hash,
        }
    )
