"""SP0 assignment methods, population dynamics, and integer closures."""

from __future__ import annotations

import math
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from viu_mrob_tfm.sp0.scenario import SP0World


DYNAMIC_IDS = {"REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB"}
FITNESS_IDS = {"DIST", "LIN", "QUAD", "ASYM", "SIG", "MC"}
ROUNDING_IDS = {"RAW", "ARG", "REPAIR", "QR1", "QR2", "QRA"}

SP0_METHOD_LABELS = {
    "HUN": "Hungarian min-cost maximum-cardinality",
    "GRD": "Greedy nearest available task",
    "DA": "Epsilon-auction one-to-one",
    "EPS-AUCTION": "Epsilon-auction one-to-one",
    "REP": "Replicator population dynamics",
    "SMI": "Smith population dynamics",
    "BNN": "Brown-von Neumann-Nash dynamics",
    "LOG": "Target logit dynamics",
    "PROJ": "Projection dynamics",
    "IBR": "Inertial best response",
    "GPC": "Generalized pairwise comparison",
    "HYB": "Hybrid logit-Smith/BNN-QR",
    "IPPO-GNN": "IPPO-GNN validation candidate",
    "MAPPO-GNN": "MAPPO-GNN validation candidate",
}


@dataclass(frozen=True, slots=True)
class SP0MethodResult:
    """Output of one SP0 method on one world."""

    method_id: str
    method_family: str
    architecture: str
    dynamic_id: str | None
    fitness_id: str | None
    rounding_id: str | None
    labels: np.ndarray
    continuous_x: np.ndarray | None
    runtime_ms: float
    convergence_time: float
    iterations: int
    timeout: bool
    messages: int
    bytes_sent: int
    fractionality: float
    entropy: float
    switches: int
    potential_violations: int
    occupancy_error: float
    training_steps: int | None = None
    training_converged: bool | None = None
    method_seed: int | None = None
    train_seed: int | None = None
    oracle_solve_time_ms: float = 0.0
    oracle_lookup_time_ms: float = 0.0
    method_online_time_ms: float = 0.0
    qra_exhaustive: bool | None = None
    continuous_converged: bool | None = None
    continuous_timeout: bool | None = None
    continuous_equilibrium_reached: bool | None = None
    state_change: float | None = None
    equilibrium_residual: float | None = None
    equilibrium_residual_id: str | None = None
    simulation_end_time_s: float | None = None
    closure_applied: bool | None = None
    closure_type: str | None = None
    closure_success: bool | None = None
    maximum_cardinality: bool | None = None
    final_success: bool | None = None
    closure_runtime_ms: float = 0.0
    closure_messages: int = 0
    global_strong_closure: bool = False
    largest_negative_delta: float = 0.0
    median_potential_delta: float = 0.0
    p01_potential_delta: float = 0.0
    trajectory: dict[str, np.ndarray] | None = None
    preclosure_labels: np.ndarray | None = None


def run_sp0_method(world: SP0World, method_spec: dict[str, Any]) -> SP0MethodResult:
    """Run one SP0 method specification."""

    method_id = str(method_spec.get("id", "GRD")).upper()
    params = dict(method_spec.get("params", {}))
    params.update({key: value for key, value in method_spec.items() if key not in {"id", "params"}})
    start = perf_counter()
    if method_id in {"HUN", "HUNGARIAN"}:
        labels, solve_ms = hungarian_assignment(world.cost)
        lookup_start = perf_counter()
        _ = getattr(world, "oracle_labels", None)
        lookup_ms = 1000.0 * (perf_counter() - lookup_start)
        return _finish_static(
            world,
            start,
            "HUN",
            "classic",
            "centralized",
            labels,
            messages=world.n_robots * world.n_loads,
            oracle_solve_time_ms=solve_ms,
            oracle_lookup_time_ms=lookup_ms,
        )
    if method_id in {"GRD", "GREEDY"}:
        architecture = str(params.get("architecture", "distributed_global"))
        if "local" in architecture.lower():
            labels = greedy_assignment_local(world)
            messages = int(np.sum(world.adjacency))
        else:
            labels = greedy_assignment(world)
            messages = world.n_robots
        return _finish_static(world, start, "GRD", "classic", architecture, labels, messages=messages)
    if method_id in {"DA", "EPS-AUCTION", "EPSILON-AUCTION"}:
        architecture = str(params.get("architecture", "distributed_global"))
        epsilon = float(params.get("auction_epsilon", 1.0e-3))
        max_rounds = int(params.get("max_rounds", 1000 * max(world.n_robots, world.n_loads)))
        if "local" in architecture.lower():
            labels, bids = auction_assignment_local(
                world,
                epsilon=epsilon,
                max_rounds=max_rounds,
            )
            messages = max(1, int(np.sum(world.adjacency))) * max(1, bids)
        else:
            labels, bids = auction_assignment(world, epsilon=epsilon, max_rounds=max_rounds)
            messages = 2 * bids
        return _finish_static(
            world,
            start,
            "EPS-AUCTION",
            "classic",
            architecture,
            labels,
            messages=messages,
        )
    if method_id.startswith("IPPO") or method_id.startswith("MAPPO"):
        if params.get("checkpoint_path"):
            from viu_mrob_tfm.sp0.data_driven import run_checkpoint_policy

            return run_checkpoint_policy(world, {**params, "id": method_id})
        if bool(params.get("allow_untrained_debug_policy", False)):
            from viu_mrob_tfm.sp0.data_driven import run_untrained_debug_policy

            return run_untrained_debug_policy(world, {**params, "id": method_id})
        raise RuntimeError("IPPO-GNN/MAPPO-GNN execution requires a real checkpoint; proxy execution is forbidden")
    dynamic = str(params.get("dynamic_id", params.get("dynamic", method_id))).upper()
    if dynamic not in DYNAMIC_IDS:
        raise ValueError(f"Unknown SP0 method or dynamic: {method_id}")
    return run_population_method(world, method_id=method_id, dynamic_id=dynamic, params=params, started_at=start)



def hungarian_assignment(cost: np.ndarray) -> tuple[np.ndarray, float]:
    """Solve SP0 with Hungarian and return labels plus solve time in milliseconds."""

    start = perf_counter()
    row_ind, col_ind = linear_sum_assignment(cost)
    labels = np.zeros(cost.shape[0], dtype=int)
    for row, col in zip(row_ind, col_ind):
        labels[int(row)] = int(col) + 1
    return labels, 1000.0 * (perf_counter() - start)


def qra_global_closure(world: SP0World, labels: np.ndarray, *, max_exact_bits: int = 20) -> tuple[np.ndarray, bool]:
    """Global strong closure without Hungarian: exact DP when feasible, declared QR2 fallback otherwise."""

    if min(world.n_robots, world.n_loads) == 0:
        return np.zeros(world.n_robots, dtype=int), True
    if world.n_loads <= world.n_robots:
        if world.n_robots > max_exact_bits:
            return qr_closure(world, labels, level="QR2", delta=0.0, max_swaps=world.n_robots), False
        return _dp_assign_loads_to_robots(world), True
    if world.n_loads > max_exact_bits:
        return qr_closure(world, labels, level="QR2", delta=0.0, max_swaps=world.n_robots), False
    return _dp_assign_robots_to_loads(world), True


def qra_exhaustive_for_world(world: SP0World, *, max_exact_bits: int = 20) -> bool:
    limiting_dimension = world.n_robots if world.n_loads <= world.n_robots else world.n_loads
    return limiting_dimension <= int(max_exact_bits)


def _dp_assign_robots_to_loads(world: SP0World) -> np.ndarray:
    n_robots, n_loads = world.n_robots, world.n_loads
    states: dict[int, tuple[float, list[int]]] = {0: (0.0, [])}
    for robot_idx in range(n_robots):
        nxt: dict[int, tuple[float, list[int]]] = {}
        for mask, (cost_so_far, chosen) in states.items():
            for load_idx in range(n_loads):
                bit = 1 << load_idx
                if mask & bit:
                    continue
                new_mask = mask | bit
                new_cost = cost_so_far + float(world.cost[robot_idx, load_idx])
                current = nxt.get(new_mask)
                if current is None or new_cost < current[0]:
                    nxt[new_mask] = (new_cost, chosen + [load_idx + 1])
        states = nxt
    best_mask, (_best_cost, best_labels) = min(states.items(), key=lambda item: (item[1][0], item[0]))
    _ = best_mask
    return np.asarray(best_labels, dtype=int)


def _dp_assign_loads_to_robots(world: SP0World) -> np.ndarray:
    n_robots, n_loads = world.n_robots, world.n_loads
    states: dict[int, tuple[float, list[int]]] = {0: (0.0, [])}
    for load_idx in range(n_loads):
        nxt: dict[int, tuple[float, list[int]]] = {}
        for mask, (cost_so_far, chosen_robots) in states.items():
            for robot_idx in range(n_robots):
                bit = 1 << robot_idx
                if mask & bit:
                    continue
                new_mask = mask | bit
                new_cost = cost_so_far + float(world.cost[robot_idx, load_idx])
                current = nxt.get(new_mask)
                if current is None or new_cost < current[0]:
                    nxt[new_mask] = (new_cost, chosen_robots + [robot_idx])
        states = nxt
    best_mask, (_best_cost, chosen_robots) = min(states.items(), key=lambda item: (item[1][0], item[0]))
    _ = best_mask
    labels = np.zeros(n_robots, dtype=int)
    for load_idx, robot_idx in enumerate(chosen_robots):
        labels[int(robot_idx)] = load_idx + 1
    return labels

def greedy_assignment(world: SP0World) -> np.ndarray:
    """Deterministic nearest-free-load greedy assignment."""

    labels = np.zeros(world.n_robots, dtype=int)
    remaining_loads = set(range(world.n_loads))
    nearest = np.min(world.cost, axis=1)
    order = np.lexsort((np.arange(world.n_robots), nearest))
    for robot_idx in order:
        if not remaining_loads:
            break
        load_candidates = np.asarray(sorted(remaining_loads), dtype=int)
        selected = int(load_candidates[np.argmin(world.cost[int(robot_idx), load_candidates])])
        labels[int(robot_idx)] = selected + 1
        remaining_loads.remove(selected)
    return labels


def greedy_assignment_local(world: SP0World) -> np.ndarray:
    """Run nearest-free greedy independently in each communication component."""

    labels = np.zeros(world.n_robots, dtype=int)
    for component in communication_components(world.adjacency):
        local_cost = np.asarray(world.cost)[component]
        local_labels = greedy_labels_from_cost(local_cost)
        labels[np.asarray(component, dtype=int)] = local_labels
    return labels


def greedy_labels_from_cost(cost: np.ndarray) -> np.ndarray:
    labels = np.zeros(cost.shape[0], dtype=int)
    remaining_loads = set(range(cost.shape[1]))
    nearest = np.min(cost, axis=1)
    order = np.lexsort((np.arange(cost.shape[0]), nearest))
    for robot_idx in order:
        if not remaining_loads:
            break
        candidates = np.asarray(sorted(remaining_loads), dtype=int)
        selected = int(candidates[np.argmin(cost[int(robot_idx), candidates])])
        labels[int(robot_idx)] = selected + 1
        remaining_loads.remove(selected)
    return labels


def communication_components(adjacency: np.ndarray) -> list[list[int]]:
    adjacency = np.asarray(adjacency, dtype=bool)
    unseen = set(range(adjacency.shape[0]))
    components: list[list[int]] = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        component = []
        while stack:
            node = stack.pop()
            component.append(node)
            neighbors = [int(index) for index in np.flatnonzero(adjacency[node]) if int(index) in unseen]
            for neighbor in neighbors:
                unseen.remove(neighbor)
                stack.append(neighbor)
        components.append(sorted(component))
    return components


def auction_assignment_local(
    world: SP0World,
    *,
    epsilon: float,
    max_rounds: int,
) -> tuple[np.ndarray, int]:
    labels = np.zeros(world.n_robots, dtype=int)
    total_bids = 0
    for component in communication_components(world.adjacency):
        local_labels, bids = epsilon_auction_labels(
            np.asarray(world.cost)[component],
            epsilon=epsilon,
            max_rounds=max_rounds,
        )
        labels[np.asarray(component, dtype=int)] = local_labels
        total_bids += bids
    return labels, total_bids


def auction_assignment(
    world: SP0World,
    *,
    epsilon: float = 1.0e-3,
    max_rounds: int = 100_000,
) -> tuple[np.ndarray, int]:
    labels, bids = epsilon_auction_labels(
        np.asarray(world.cost, dtype=float),
        epsilon=epsilon,
        max_rounds=max_rounds,
    )
    if not assignment_valid(labels, world.n_loads):
        raise RuntimeError("epsilon-auction produced an invalid one-to-one assignment")
    return labels, bids


def epsilon_auction_labels(
    cost: np.ndarray,
    *,
    epsilon: float,
    max_rounds: int,
) -> tuple[np.ndarray, int]:
    """Rectangular epsilon-auction over a cost matrix without an oracle."""

    if epsilon <= 0.0:
        raise ValueError("epsilon-auction requires epsilon > 0")
    cost = np.asarray(cost, dtype=float)
    n_robots, n_loads = cost.shape
    transposed = n_robots > n_loads
    bidder_cost = cost.T if transposed else cost
    n_bidders, n_items = bidder_cost.shape
    benefit = -bidder_cost
    prices = np.zeros(n_items, dtype=float)
    owner = np.full(n_items, -1, dtype=int)
    assignment = np.full(n_bidders, -1, dtype=int)
    unassigned = list(range(n_bidders))
    bids = 0
    while unassigned and bids < int(max_rounds):
        bidder = int(unassigned.pop(0))
        net = benefit[bidder] - prices
        order = np.lexsort((np.arange(n_items), -net))
        best_item = int(order[0])
        best_value = float(net[best_item])
        second_value = float(net[int(order[1])]) if n_items > 1 else best_value - epsilon
        prices[best_item] += best_value - second_value + epsilon
        previous_owner = int(owner[best_item])
        owner[best_item] = bidder
        assignment[bidder] = best_item
        if previous_owner >= 0:
            assignment[previous_owner] = -1
            unassigned.append(previous_owner)
        bids += 1
    if unassigned or np.any(assignment < 0):
        raise TimeoutError(f"epsilon-auction did not terminate in {max_rounds} bids for shape {cost.shape}")
    labels = np.zeros(n_robots, dtype=int)
    if transposed:
        for load_idx, robot_idx in enumerate(assignment):
            labels[int(robot_idx)] = int(load_idx) + 1
    else:
        labels[:] = assignment + 1
    return labels, bids

def data_driven_proxy_assignment(world: SP0World, *, method_id: str, params: dict[str, Any]) -> tuple[np.ndarray, int]:
    """Forbidden legacy compatibility hook.

    Confirmatory and smoke execution must use either a real checkpoint or the
    explicitly marked untrained debug policy used only for B0 leakage checks.
    """

    raise RuntimeError("Data-driven proxy assignment is forbidden; provide checkpoint_path or allow_untrained_debug_policy for B0 only")


def run_population_method(
    world: SP0World,
    *,
    method_id: str,
    dynamic_id: str,
    params: dict[str, Any],
    started_at: float | None = None,
) -> SP0MethodResult:
    """Run a population dynamic and close it into an integer assignment."""

    start = perf_counter() if started_at is None else started_at
    fitness_id = str(params.get("fitness_id", params.get("fitness", "LIN"))).upper()
    rounding_id = str(params.get("rounding_id", params.get("rounding", "QR1"))).upper()
    architecture = str(params.get("architecture", "distributed_global"))
    if fitness_id not in FITNESS_IDS:
        raise ValueError(f"Unknown SP0 fitness: {fitness_id}")
    if rounding_id not in ROUNDING_IDS:
        raise ValueError(f"Unknown SP0 rounding: {rounding_id}")

    h = float(params.get("h", params.get("step", 0.05)))
    max_steps = int(params.get("max_steps", 100))
    dt = float(params.get("dt", 0.1))
    tol = float(params.get("stability_tol", 1.0e-4))
    eps_eq = float(params.get("epsilon_ne_cont", params.get("epsilon_equilibrium", 1.0e-3)))
    stable_window = int(params.get("stable_window_steps", 10))
    x = np.asarray(world.initial_x, dtype=float).copy()
    previous_choice = np.argmax(x, axis=1)
    stable_count = 0
    continuous_converged = False
    continuous_equilibrium_reached = False
    switches = 0
    potential_violations = 0
    potential_deltas: list[float] = []
    occupancy_errors: list[float] = []
    state_change = math.inf
    equilibrium_residual = math.inf
    equilibrium_residual_id = "uninitialized"
    last_potential = continuous_potential(world, x, fitness_id=fitness_id, params=params)
    record_trajectory = bool(params.get("record_trajectory", False))
    trajectory_time: list[float] = []
    trajectory_potential: list[float] = []
    trajectory_residual: list[float] = []
    trajectory_fractionality: list[float] = []
    trajectory_switches: list[int] = []
    trajectory_state_change: list[float] = []
    trajectory_occupancy_error: list[float] = []
    trajectory_labels: list[np.ndarray] = []

    for step_idx in range(max_steps):
        fitness, occupancy_error = fitness_matrix(world, x, fitness_id=fitness_id, params=params, architecture=architecture)
        occupancy_errors.append(float(occupancy_error))
        x_next = _dynamic_step(x, fitness, dynamic_id=dynamic_id, h=h, params=params, step_idx=step_idx)
        x_next = project_rows_to_simplex(x_next)
        state_change = float(np.max(np.abs(x_next - x)))
        next_fitness, _next_occupancy_error = fitness_matrix(world, x_next, fitness_id=fitness_id, params=params, architecture=architecture)
        equilibrium_residual, equilibrium_residual_id = applicable_equilibrium_residual(
            x_next,
            next_fitness,
            dynamic_id=dynamic_id,
            params=params,
            step_idx=step_idx,
            h=h,
        )
        continuous_equilibrium_reached = bool(equilibrium_residual <= eps_eq)
        choice = np.argmax(x_next, axis=1)
        switches += int(np.sum(choice != previous_choice))
        previous_choice = choice
        potential = continuous_potential(world, x_next, fitness_id=fitness_id, params=params)
        potential_delta = float(potential - last_potential)
        potential_deltas.append(potential_delta)
        if potential_delta < -1.0e-8:
            potential_violations += 1
        last_potential = potential
        x = x_next
        if record_trajectory:
            trajectory_time.append(float((step_idx + 1) * dt))
            trajectory_potential.append(float(potential))
            trajectory_residual.append(float(equilibrium_residual))
            trajectory_fractionality.append(float(fractionality(x)))
            trajectory_switches.append(int(switches))
            trajectory_state_change.append(float(state_change))
            trajectory_occupancy_error.append(float(occupancy_error))
            trajectory_labels.append(np.argmax(x, axis=1).astype(np.int16))
        if state_change <= tol and continuous_equilibrium_reached:
            stable_count += 1
            if stable_count >= stable_window:
                continuous_converged = True
                break
        else:
            stable_count = 0
    else:
        step_idx = max_steps - 1

    preclosure_labels = np.argmax(x, axis=1).astype(int)
    closure_start = perf_counter()
    labels = close_integer(world, x, rounding_id=rounding_id, params=params)
    closure_runtime_ms = 1000.0 * (perf_counter() - closure_start)
    runtime_ms = 1000.0 * (perf_counter() - start)
    qra_exhaustive = qra_exhaustive_for_world(world) if str(rounding_id).upper() == "QRA" else None
    closure_type = (
        "QRA_EXHAUSTIVE_GLOBAL"
        if qra_exhaustive is True
        else "QRA_NONEXHAUSTIVE_QR2_FALLBACK"
        if str(rounding_id).upper() == "QRA"
        else rounding_id
    )
    iterations = int(step_idx + 1)
    messages = _message_count(world, architecture=architecture, iterations=iterations, rounding_id=rounding_id)
    closure_messages = _message_count(world, architecture=architecture, iterations=0, rounding_id=rounding_id)
    raw_only = rounding_id == "RAW"
    matching_valid = False if raw_only else assignment_valid(labels, world.n_loads)
    assigned = int(np.sum(np.asarray(labels) > 0)) if matching_valid else int(np.unique(np.asarray(labels)[np.asarray(labels) > 0]).size)
    maximum_cardinality = None if raw_only else bool(matching_valid and assigned == world.s_star)
    closure_success = None if raw_only else bool(matching_valid)
    deltas = np.asarray(potential_deltas, dtype=float)
    trajectory = None
    if record_trajectory:
        trajectory = {
            "time_s": np.asarray(trajectory_time, dtype=np.float32),
            "potential": np.asarray(trajectory_potential, dtype=np.float32),
            "equilibrium_residual": np.asarray(trajectory_residual, dtype=np.float32),
            "fractionality": np.asarray(trajectory_fractionality, dtype=np.float32),
            "switches": np.asarray(trajectory_switches, dtype=np.int32),
            "state_change": np.asarray(trajectory_state_change, dtype=np.float32),
            "occupancy_error": np.asarray(trajectory_occupancy_error, dtype=np.float32),
            "argmax_labels": (
                np.stack(trajectory_labels, axis=0)
                if trajectory_labels
                else np.empty((0, world.n_robots), dtype=np.int16)
            ),
            "final_labels": np.asarray(labels, dtype=np.int16),
        }
    return SP0MethodResult(
        method_id=method_id,
        method_family="population",
        architecture=architecture,
        dynamic_id=dynamic_id,
        fitness_id=fitness_id,
        rounding_id=rounding_id,
        labels=labels,
        continuous_x=x,
        runtime_ms=runtime_ms,
        convergence_time=float(iterations * dt),
        iterations=iterations,
        timeout=not continuous_converged,
        messages=int(messages),
        bytes_sent=int(messages * 32),
        fractionality=fractionality(x),
        entropy=mean_entropy(x),
        switches=int(switches),
        potential_violations=int(potential_violations),
        occupancy_error=float(np.mean(occupancy_errors)) if occupancy_errors else 0.0,
        training_steps=None,
        training_converged=None,
        method_seed=_optional_int(params.get("method_seed")),
        train_seed=_optional_int(params.get("train_seed")),
        method_online_time_ms=runtime_ms - closure_runtime_ms,
        qra_exhaustive=qra_exhaustive,
        continuous_converged=bool(continuous_converged),
        continuous_timeout=bool(not continuous_converged),
        continuous_equilibrium_reached=bool(continuous_equilibrium_reached),
        state_change=float(state_change),
        equilibrium_residual=float(equilibrium_residual),
        equilibrium_residual_id=equilibrium_residual_id,
        simulation_end_time_s=float(iterations * dt),
        closure_applied=bool(rounding_id != "RAW"),
        closure_type=closure_type,
        closure_success=closure_success,
        maximum_cardinality=maximum_cardinality,
        final_success=maximum_cardinality,
        closure_runtime_ms=float(closure_runtime_ms),
        closure_messages=int(closure_messages),
        global_strong_closure=bool(rounding_id == "QRA" and qra_exhaustive),
        largest_negative_delta=float(min(0.0, np.min(deltas))) if deltas.size else 0.0,
        median_potential_delta=float(np.median(deltas)) if deltas.size else 0.0,
        p01_potential_delta=float(np.quantile(deltas, 0.01)) if deltas.size else 0.0,
        trajectory=trajectory,
        preclosure_labels=preclosure_labels,
    )


def fitness_matrix(
    world: SP0World,
    x: np.ndarray,
    *,
    fitness_id: str,
    params: dict[str, Any],
    architecture: str,
) -> tuple[np.ndarray, float]:
    """Return per-robot fitness values for idle plus every load."""

    alpha = float(params.get("alpha", params.get("distance_weight", 1.0)))
    lam = float(params.get("lambda", params.get("lambda_congestion", 1.0)))
    reward = float(params.get("r", params.get("reward", 1.0)))
    beta = float(params.get("beta", 5.0))
    delta_x = float(params.get("delta_x", 0.05))
    n_global = np.sum(x[:, 1:], axis=0)
    if "local" in str(architecture).lower():
        estimates = _local_occupancy_estimates(world, x)
        occupancy_error = float(np.mean(np.abs(estimates - n_global[None, :])))
    else:
        estimates = np.repeat(n_global[None, :], world.n_robots, axis=0)
        occupancy_error = 0.0
    f = np.zeros((world.n_robots, world.n_loads + 1), dtype=float)
    for robot_idx in range(world.n_robots):
        n = estimates[robot_idx]
        if fitness_id == "DIST":
            load_fit = -alpha * world.cost[robot_idx]
        elif fitness_id == "LIN":
            load_fit = reward - alpha * world.cost[robot_idx] - lam * n
        elif fitness_id == "QUAD":
            load_fit = -alpha * world.cost[robot_idx] - lam * (n - 1.0)
        elif fitness_id == "ASYM":
            load_fit = -alpha * world.cost[robot_idx] + reward * np.maximum(1.0 - n, 0.0) - lam * np.maximum(n - 1.0, 0.0)
        elif fitness_id == "SIG":
            under = _sigmoid(beta * (1.0 - n))
            over = _sigmoid(beta * (n - 1.0))
            load_fit = -alpha * world.cost[robot_idx] + reward * under - lam * over
        elif fitness_id == "MC":
            load_fit = -alpha * world.cost[robot_idx] + _mc_utility(n + delta_x, reward, lam) - _mc_utility(n, reward, lam)
        else:
            raise ValueError(fitness_id)
        f[robot_idx, 1:] = load_fit
    return f, occupancy_error


def close_integer(world: SP0World, x: np.ndarray, *, rounding_id: str, params: dict[str, Any]) -> np.ndarray:
    rounding = rounding_id.upper()
    if rounding == "RAW":
        return np.full(world.n_robots, -1, dtype=int)
    if rounding == "ARG":
        return np.argmax(x, axis=1).astype(int)
    if rounding == "REPAIR":
        return repair_assignment(world, np.argmax(x, axis=1).astype(int), x)
    if rounding in {"QR1", "QR2"}:
        start = repair_assignment(world, np.argmax(x, axis=1).astype(int), x)
        return qr_closure(
            world,
            start,
            level=rounding,
            delta=float(params.get("delta_qr", params.get("delta_QR", 1.0e-4))),
            max_swaps=int(params.get("max_swaps", 10)),
        )
    if rounding == "QRA":
        start = qr_closure(
            world,
            repair_assignment(world, np.argmax(x, axis=1).astype(int), x),
            level="QR2",
            delta=float(params.get("delta_qr", params.get("delta_QR", 1.0e-4))),
            max_swaps=int(params.get("max_swaps", 10)),
        )
        labels, _is_exhaustive = qra_global_closure(world, start)
        return labels
    raise ValueError(rounding_id)


def repair_assignment(world: SP0World, labels: np.ndarray, x: np.ndarray | None = None) -> np.ndarray:
    """Repair duplicates while preserving at most one robot per load."""

    repaired = np.asarray(labels, dtype=int).copy()
    repaired[(repaired < 0) | (repaired > world.n_loads)] = 0
    for load_label in range(1, world.n_loads + 1):
        assigned = np.flatnonzero(repaired == load_label)
        if assigned.size <= 1:
            continue
        if x is None:
            keep = int(assigned[np.argmin(world.cost[assigned, load_label - 1])])
        else:
            keep = int(assigned[np.argmax(x[assigned, load_label])])
        for robot_idx in assigned:
            if int(robot_idx) != keep:
                repaired[int(robot_idx)] = 0
    free_loads = [idx for idx in range(world.n_loads) if not np.any(repaired == idx + 1)]
    idle = list(np.flatnonzero(repaired == 0))
    while free_loads and idle and int(np.sum(repaired > 0)) < world.s_star:
        best: tuple[float, int, int] | None = None
        for robot_idx in idle:
            for load_idx in free_loads:
                preference = float(x[int(robot_idx), load_idx + 1]) if x is not None else -float(world.cost[int(robot_idx), load_idx])
                candidate = (preference, -float(world.cost[int(robot_idx), load_idx]), -int(robot_idx), -int(load_idx))
                if best is None or candidate > best:
                    best = candidate
        if best is None:
            break
        _pref, _neg_cost, neg_robot, neg_load = best
        robot_idx = -int(neg_robot)
        load_idx = -int(neg_load)
        repaired[robot_idx] = load_idx + 1
        idle.remove(robot_idx)
        free_loads.remove(load_idx)
    return repaired


def qr_closure(world: SP0World, labels: np.ndarray, *, level: str, delta: float, max_swaps: int) -> np.ndarray:
    """Finite improvement closure over unilateral moves and optional swaps."""

    current = np.asarray(labels, dtype=int).copy()
    max_passes = max(1, world.n_robots * max(world.n_loads, 1) + max_swaps)
    for _ in range(max_passes):
        improved, current = _best_unilateral_improvement(world, current, delta=delta)
        if improved:
            continue
        if level == "QR2":
            improved, current = _best_swap_improvement(world, current, delta=delta)
            if improved:
                continue
        break
    return current


def assignment_valid(labels: np.ndarray, n_loads: int) -> bool:
    labels = np.asarray(labels, dtype=int)
    if labels.ndim != 1:
        return False
    if np.any(labels < 0) or np.any(labels > n_loads):
        return False
    positive = labels[labels > 0]
    return np.unique(positive).size == positive.size


def assignment_objective(world: SP0World, labels: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    positive = labels > 0
    assigned_loads = np.unique(labels[positive])
    valid_covered = int(assigned_loads.size)
    cost_sum = 0.0
    for robot_idx, label in enumerate(labels):
        if 1 <= int(label) <= world.n_loads:
            cost_sum += float(world.cost[robot_idx, int(label) - 1])
    b_penalty = world.s_star + 1.0
    duplicate_penalty = max(0, int(np.sum(positive)) - valid_covered) * b_penalty
    return float(b_penalty * (world.s_star - valid_covered) + duplicate_penalty + cost_sum)


def assignment_social_cost(world: SP0World, labels: np.ndarray) -> float:
    total = 0.0
    for robot_idx, label in enumerate(labels):
        if 1 <= int(label) <= world.n_loads:
            total += float(world.cost[robot_idx, int(label) - 1])
    return float(total)


def unilateral_epsilon(world: SP0World, labels: np.ndarray) -> float:
    current_j = assignment_objective(world, labels)
    best = 0.0
    occupied = {int(label) for label in labels if int(label) > 0}
    free_loads = [idx + 1 for idx in range(world.n_loads) if idx + 1 not in occupied]
    for robot_idx in range(world.n_robots):
        candidates = [0] + free_loads
        for candidate in candidates:
            if int(candidate) == int(labels[robot_idx]):
                continue
            trial = labels.copy()
            trial[robot_idx] = int(candidate)
            if assignment_valid(trial, world.n_loads):
                best = max(best, current_j - assignment_objective(world, trial))
    return float(max(best, 0.0))


def swap_epsilon(world: SP0World, labels: np.ndarray) -> float:
    current_j = assignment_objective(world, labels)
    best = 0.0
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            trial = labels.copy()
            trial[i], trial[j] = trial[j], trial[i]
            if assignment_valid(trial, world.n_loads):
                best = max(best, current_j - assignment_objective(world, trial))
    return float(max(best, 0.0))


def fractionality(x: np.ndarray | None) -> float:
    if x is None:
        return 0.0
    return float(np.mean(1.0 - np.max(x, axis=1)))


def mean_entropy(x: np.ndarray | None) -> float:
    if x is None:
        return 0.0
    safe = np.clip(x, 1.0e-12, 1.0)
    return float(np.mean(-np.sum(safe * np.log(safe), axis=1)))


def applicable_equilibrium_residual(
    x: np.ndarray,
    fitness: np.ndarray,
    *,
    dynamic_id: str,
    params: dict[str, Any],
    step_idx: int,
    h: float,
) -> tuple[float, str]:
    """Return the stationarity residual appropriate to the active revision protocol."""

    dynamic = dynamic_id.upper()
    if dynamic == "REP":
        mean = np.sum(x * fitness, axis=1, keepdims=True)
        field = x * (fitness - mean)
        residual_id = "replicator_support_conditioned_vector_field"
    elif dynamic == "SMI":
        field = _smith_vector_field(x, fitness)
        residual_id = "smith_vector_field"
    elif dynamic == "BNN":
        mean = np.sum(x * fitness, axis=1, keepdims=True)
        excess = np.maximum(fitness - mean, 0.0)
        field = excess - x * np.sum(excess, axis=1, keepdims=True)
        residual_id = "bnn_excess_payoff_vector_field"
    elif dynamic == "LOG":
        eta = float(params.get("eta", params.get("temperature", 0.2)))
        field = _softmax(fitness / max(eta, 1.0e-9)) - x
        residual_id = "target_logit_fixed_point"
    elif dynamic == "PROJ":
        projected = project_rows_to_simplex(x + h * fitness)
        field = (projected - x) / max(abs(h), 1.0e-12)
        residual_id = "projection_gradient_mapping"
    elif dynamic == "IBR":
        best = np.argmax(fitness, axis=1)
        target = np.zeros_like(x)
        target[np.arange(x.shape[0]), best] = 1.0
        field = target - x
        residual_id = "inertial_best_response_fixed_point"
    elif dynamic == "GPC":
        field = _gpc_vector_field(x, fitness, params=params)
        residual_id = "generalized_pairwise_vector_field"
    elif dynamic == "HYB":
        entropy = mean_entropy(x)
        threshold = float(params.get("entropy_switch", 0.45 * math.log(max(x.shape[1], 2))))
        if entropy > threshold and step_idx < int(params.get("exploration_steps", 25)):
            eta = float(params.get("eta", 0.2))
            field = _softmax(fitness / max(eta, 1.0e-9)) - x
            residual_id = "hybrid_logit_phase_fixed_point"
        else:
            field = _smith_vector_field(x, fitness)
            residual_id = "hybrid_smith_phase_vector_field"
    else:
        return continuous_equilibrium_residual(x, fitness), "generic_payoff_advantage"
    return float(np.max(np.abs(field))), residual_id


def continuous_equilibrium_residual(x: np.ndarray, fitness: np.ndarray) -> float:
    """Max payoff advantage over currently mixed strategies.

    This is an operational residual for B0/B2 stopping, not a universal proof of
    Nash convergence for every dynamic.
    """

    x = np.asarray(x, dtype=float)
    fitness = np.asarray(fitness, dtype=float)
    expected = np.sum(x * fitness, axis=1)
    best = np.max(fitness, axis=1)
    return float(np.max(np.maximum(best - expected, 0.0)))
def continuous_potential(world: SP0World, x: np.ndarray, *, fitness_id: str, params: dict[str, Any]) -> float:
    alpha = float(params.get("alpha", params.get("distance_weight", 1.0)))
    lam = float(params.get("lambda", params.get("lambda_congestion", 1.0)))
    reward = float(params.get("r", params.get("reward", 1.0)))
    n = np.sum(x[:, 1:], axis=0)
    if fitness_id == "LIN":
        load_term = reward * n - 0.5 * lam * n * n
    elif fitness_id == "QUAD":
        load_term = -0.5 * lam * (n - 1.0) ** 2
    elif fitness_id == "ASYM":
        load_term = reward * np.minimum(n, 1.0) - 0.5 * lam * np.maximum(n - 1.0, 0.0) ** 2
    elif fitness_id == "MC":
        load_term = _mc_utility(n, reward, lam)
    elif fitness_id == "SIG":
        load_term = reward * n - lam * np.maximum(n - 1.0, 0.0)
    else:
        load_term = np.zeros_like(n)
    distance_term = alpha * float(np.sum(world.cost * x[:, 1:]))
    return float(np.sum(load_term) - distance_term)


def project_rows_to_simplex(x: np.ndarray) -> np.ndarray:
    return np.vstack([project_simplex(row) for row in np.asarray(x, dtype=float)])


def project_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection onto the probability simplex."""

    values = np.asarray(v, dtype=float)
    if values.size == 0:
        return values
    u = np.sort(values)[::-1]
    cssv = np.cumsum(u)
    rho_candidates = u * np.arange(1, values.size + 1) > (cssv - 1.0)
    if not np.any(rho_candidates):
        return np.full_like(values, 1.0 / values.size)
    rho = int(np.flatnonzero(rho_candidates)[-1])
    theta = (cssv[rho] - 1.0) / float(rho + 1)
    return np.maximum(values - theta, 0.0)


def sp0_method_metadata(method_id: str) -> dict[str, Any]:
    method = str(method_id).upper()
    if method == "HUN":
        return _metadata(method, "classic", "centralized", "reference", "hungarian_mincost_maxcardinality")
    if method in {"GRD", "GREEDY"}:
        return _metadata("GRD", "classic", "distributed_global", "baseline", "nearest_available_task")
    if method in {"DA", "CBAA", "CBBA"}:
        return _metadata("DA", "classic", "distributed_global", "baseline", "distributed_auction_one_to_one")
    if method.startswith("IPPO") or method.startswith("MAPPO"):
        base = "IPPO-GNN" if method.startswith("IPPO") else "MAPPO-GNN"
        return _metadata(base, "data_driven", "distributed_local", "candidate", base.lower().replace("-", "_"))
    if method in DYNAMIC_IDS:
        return _metadata(method, "population", "distributed_global", "candidate", f"{method.lower()}_fitness_rounding")
    return _metadata(method, "unknown", "unknown", "unknown", method.lower())


def _dynamic_step(x: np.ndarray, fitness: np.ndarray, *, dynamic_id: str, h: float, params: dict[str, Any], step_idx: int) -> np.ndarray:
    dynamic = dynamic_id.upper()
    if dynamic == "REP":
        mean = np.sum(x * fitness, axis=1, keepdims=True)
        return x + h * x * (fitness - mean)
    if dynamic == "SMI":
        return x + h * _smith_vector_field(x, fitness)
    if dynamic == "BNN":
        mean = np.sum(x * fitness, axis=1, keepdims=True)
        excess = np.maximum(fitness - mean, 0.0)
        return x + h * (excess - x * np.sum(excess, axis=1, keepdims=True))
    if dynamic == "LOG":
        eta = float(params.get("eta", params.get("temperature", 0.2)))
        target = _softmax(fitness / max(eta, 1.0e-9))
        return x + h * (target - x)
    if dynamic == "PROJ":
        return project_rows_to_simplex(x + h * fitness)
    if dynamic == "IBR":
        alpha_br = float(params.get("alpha_br", params.get("alpha_BR", 0.3)))
        best = np.argmax(fitness, axis=1)
        target = np.zeros_like(x)
        target[np.arange(x.shape[0]), best] = 1.0
        return (1.0 - alpha_br) * x + alpha_br * target
    if dynamic == "GPC":
        return x + h * _gpc_vector_field(x, fitness, params=params)
    if dynamic == "HYB":
        entropy = mean_entropy(x)
        threshold = float(params.get("entropy_switch", 0.45 * math.log(max(x.shape[1], 2))))
        if entropy > threshold and step_idx < int(params.get("exploration_steps", 25)):
            eta = float(params.get("eta", 0.2))
            return x + h * (_softmax(fitness / max(eta, 1.0e-9)) - x)
        return x + h * _smith_vector_field(x, fitness)
    raise ValueError(dynamic_id)


def _smith_vector_field(x: np.ndarray, fitness: np.ndarray) -> np.ndarray:
    diff = fitness[:, :, None] - fitness[:, None, :]
    positive = np.maximum(diff, 0.0)
    inflow = np.sum(x[:, None, :] * positive, axis=2)
    outflow = x * np.sum(np.maximum(-diff, 0.0), axis=2)
    return inflow - outflow


def _gpc_vector_field(x: np.ndarray, fitness: np.ndarray, *, params: dict[str, Any]) -> np.ndarray:
    q = float(params.get("q", 1.0))
    kappa = float(params.get("kappa", 1.0))
    phi_id = str(params.get("phi", "linear")).lower()
    diff = np.maximum(fitness[:, :, None] - fitness[:, None, :], 0.0)
    if phi_id == "power":
        phi = diff**q
    elif phi_id == "tanh":
        phi = np.tanh(kappa * diff)
    elif phi_id == "saturated":
        phi = diff / (1.0 + kappa * diff)
    else:
        phi = diff
    inflow = np.sum(x[:, None, :] * phi, axis=2)
    outflow = x * np.sum(np.swapaxes(phi, 1, 2), axis=2)
    return inflow - outflow


def _best_unilateral_improvement(world: SP0World, labels: np.ndarray, *, delta: float) -> tuple[bool, np.ndarray]:
    current_j = assignment_objective(world, labels)
    best_improvement = float(delta)
    best_labels = labels
    occupied = {int(label) for label in labels if int(label) > 0}
    free_loads = [idx + 1 for idx in range(world.n_loads) if idx + 1 not in occupied]
    for robot_idx in range(world.n_robots):
        candidates = [0] + free_loads
        for candidate in candidates:
            if int(candidate) == int(labels[robot_idx]):
                continue
            trial = labels.copy()
            trial[robot_idx] = int(candidate)
            if not assignment_valid(trial, world.n_loads):
                continue
            improvement = current_j - assignment_objective(world, trial)
            if improvement > best_improvement:
                best_improvement = improvement
                best_labels = trial
    return best_labels is not labels, best_labels


def _best_swap_improvement(world: SP0World, labels: np.ndarray, *, delta: float) -> tuple[bool, np.ndarray]:
    current_j = assignment_objective(world, labels)
    best_improvement = float(delta)
    best_labels = labels
    for i in range(world.n_robots):
        for j in range(i + 1, world.n_robots):
            if labels[i] == labels[j]:
                continue
            trial = labels.copy()
            trial[i], trial[j] = trial[j], trial[i]
            if not assignment_valid(trial, world.n_loads):
                continue
            improvement = current_j - assignment_objective(world, trial)
            if improvement > best_improvement:
                best_improvement = improvement
                best_labels = trial
    return best_labels is not labels, best_labels


def _local_occupancy_estimates(world: SP0World, x: np.ndarray) -> np.ndarray:
    load_mass = x[:, 1:]
    mask = world.adjacency.astype(float) + np.eye(world.n_robots)
    counts = np.sum(mask, axis=1, keepdims=True)
    local_mean = (mask @ load_mass) / np.maximum(counts, 1.0)
    return local_mean * world.n_robots


def _message_count(world: SP0World, *, architecture: str, iterations: int, rounding_id: str) -> int:
    if "central" in architecture:
        base = world.n_robots * world.n_loads
    elif "local" in architecture:
        base = int(np.sum(world.adjacency))
    else:
        base = world.n_robots * max(world.n_robots - 1, 1)
    closure_factor = {"RAW": 0, "ARG": 0, "REPAIR": world.n_robots, "QR1": world.n_robots, "QR2": 2 * world.n_robots, "QRA": world.n_robots * world.n_loads}.get(rounding_id.upper(), 0)
    return int(iterations * base + closure_factor)


def _finish_static(
    world: SP0World,
    started_at: float,
    method_id: str,
    family: str,
    architecture: str,
    labels: np.ndarray,
    *,
    messages: int,
    oracle_solve_time_ms: float = 0.0,
    oracle_lookup_time_ms: float = 0.0,
) -> SP0MethodResult:
    runtime_ms = 1000.0 * (perf_counter() - started_at)
    method_online_time_ms = oracle_solve_time_ms if method_id == "HUN" else runtime_ms
    clean_labels = np.asarray(labels, dtype=int)
    matching_valid = assignment_valid(clean_labels, world.n_loads)
    assigned = int(np.sum(clean_labels > 0)) if matching_valid else int(np.unique(clean_labels[clean_labels > 0]).size)
    maximum_cardinality = bool(matching_valid and assigned == world.s_star)
    return SP0MethodResult(
        method_id=method_id,
        method_family=family,
        architecture=architecture,
        dynamic_id=None,
        fitness_id=None,
        rounding_id="EXACT" if method_id == "HUN" else "POLICY",
        labels=np.asarray(labels, dtype=int),
        continuous_x=None,
        runtime_ms=runtime_ms,
        convergence_time=0.0,
        iterations=1,
        timeout=False,
        messages=int(messages),
        bytes_sent=int(messages * 32),
        fractionality=0.0,
        entropy=0.0,
        switches=0,
        potential_violations=0,
        occupancy_error=0.0,
        oracle_solve_time_ms=float(oracle_solve_time_ms),
        oracle_lookup_time_ms=float(oracle_lookup_time_ms),
        method_online_time_ms=float(method_online_time_ms),
        continuous_converged=None,
        continuous_timeout=None,
        continuous_equilibrium_reached=None,
        closure_applied=False,
        closure_type="EXACT" if method_id == "HUN" else "POLICY",
        closure_success=bool(matching_valid),
        maximum_cardinality=maximum_cardinality,
        final_success=maximum_cardinality,
    )


def _metadata(method: str, family: str, scope: str, ownership: str, variant: str) -> dict[str, Any]:
    return {
        "method_id": method,
        "label": SP0_METHOD_LABELS.get(method, method),
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "comparison_group": f"{ownership}_{family}_{scope}",
    }


def _mc_utility(n: np.ndarray, reward: float, lam: float) -> np.ndarray:
    return reward * np.minimum(n, 1.0) - lam * np.maximum(n - 1.0, 0.0) ** 2


def _sigmoid(z: np.ndarray) -> np.ndarray:
    clipped = np.clip(z, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _softmax(z: np.ndarray) -> np.ndarray:
    shifted = z - np.max(z, axis=1, keepdims=True)
    exp = np.exp(np.clip(shifted, -60.0, 60.0))
    return exp / np.sum(exp, axis=1, keepdims=True)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
