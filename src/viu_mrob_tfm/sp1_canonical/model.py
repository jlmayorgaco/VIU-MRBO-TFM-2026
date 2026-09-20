"""Model and algorithms for the canonical SP1 coalition-formation experiment.

The local method floods immutable bid records through a robot communication
graph for a finite number of digital rounds. Each robot computes the same
deterministic greedy matching over its own view and executes only the action
assigned to itself. The global evaluator records inconsistent claims but never
repairs them, so limited observability remains visible in the evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


CAPABILITY_NAMES = ("payload", "force", "torque")
ROLE_NAMES = ("support_left", "support_right", "stabilizer")


@dataclass(frozen=True, slots=True)
class FormationWorld:
    regime: str
    seed: int
    robot_positions_m: np.ndarray
    capabilities: np.ndarray
    battery_fraction: np.ndarray
    active: np.ndarray
    load_positions_m: np.ndarray
    load_values: np.ndarray
    slot_load: np.ndarray
    slot_roles: tuple[str, ...]
    slot_requirements: np.ndarray
    previous_slot: np.ndarray
    event_type: str
    world_hash: str

    @property
    def n_robots(self) -> int:
        return int(self.robot_positions_m.shape[0])

    @property
    def n_loads(self) -> int:
        return int(self.load_positions_m.shape[0])

    @property
    def n_slots(self) -> int:
        return int(self.slot_load.size)


@dataclass(frozen=True, slots=True)
class DistributedResult:
    assignment: np.ndarray
    messages: int
    bytes_sent: int
    mean_view_coverage: float
    min_view_coverage: float
    network_components: int
    visibility: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class OracleResult:
    assignment: np.ndarray
    activated: np.ndarray
    objective_value: float
    solver_status: int
    solver_message: str
    mip_gap: float


def generate_world(regime: str, n_robots: int, n_loads: int, seed: int) -> FormationWorld:
    """Generate one paired world with a common pre-event coalition state."""

    if regime not in {"abundant", "tight", "scarce"}:
        raise ValueError(f"Unknown SP1 regime: {regime}")
    if n_robots < 3:
        raise ValueError("SP1 requires at least three robots")
    if n_loads < 1:
        raise ValueError("SP1 requires at least one load")

    offset = int.from_bytes(hashlib.sha256(regime.encode("utf-8")).digest()[:4], "little")
    rng = np.random.default_rng(int(seed) + 1009 * int(n_robots) + 9173 * int(n_loads) + offset)
    robot_positions = rng.uniform(0.0, 10.0, size=(n_robots, 2))
    load_positions = rng.uniform(1.0, 9.0, size=(n_loads, 2))

    capability_ranges = {
        "abundant": (0.55, 1.00),
        "tight": (0.38, 0.95),
        "scarce": (0.28, 0.82),
    }
    requirement_ranges = {
        "abundant": (0.34, 0.62),
        "tight": (0.52, 0.82),
        "scarce": (0.60, 0.90),
    }
    low, high = capability_ranges[regime]
    capabilities = rng.uniform(low, high, size=(n_robots, len(CAPABILITY_NAMES)))
    battery = rng.uniform(0.45 if regime != "scarce" else 0.25, 1.0, size=n_robots)

    slot_load: list[int] = []
    slot_roles: list[str] = []
    requirements: list[np.ndarray] = []
    req_low, req_high = requirement_ranges[regime]
    for load in range(n_loads):
        role_count = 3 if regime == "scarce" else 2 + int((seed + load) % 2)
        for role_index, role in enumerate(ROLE_NAMES[:role_count]):
            requirement = rng.uniform(req_low, req_high, size=len(CAPABILITY_NAMES))
            if role_index < 2:
                requirement *= np.asarray([1.05, 1.00, 0.78])
            else:
                requirement *= np.asarray([0.72, 0.88, 1.12])
            slot_load.append(load)
            slot_roles.append(role)
            requirements.append(np.clip(requirement, 0.05, 0.98))

    slot_load_array = np.asarray(slot_load, dtype=int)
    requirement_array = np.vstack(requirements)
    load_values = rng.uniform(2.2, 3.8, size=n_loads)

    # The first task is constructively feasible before the event. Other tasks
    # retain random compatibility and create the competition/shortage regime.
    first_slots = np.flatnonzero(slot_load_array == 0)
    for robot, slot in enumerate(first_slots):
        capabilities[robot] = np.maximum(capabilities[robot], requirement_array[slot] + 0.04)
        battery[robot] = max(float(battery[robot]), 0.62)
        robot_positions[robot] = load_positions[0] + rng.normal(0.0, 0.55, size=2)
    robot_positions = np.clip(robot_positions, 0.0, 10.0)

    active = np.ones(n_robots, dtype=bool)
    previous_slot = np.full(n_robots, -1, dtype=int)
    compatible_before = compatibility_matrix(capabilities, battery, active, requirement_array)
    used: set[int] = set()
    for slot in first_slots:
        candidates = [
            robot
            for robot in range(n_robots)
            if robot not in used and compatible_before[robot, slot]
        ]
        if not candidates:
            continue
        winner = min(
            candidates,
            key=lambda robot: (
                float(np.linalg.norm(robot_positions[robot] - load_positions[0])),
                robot,
            ),
        )
        previous_slot[winner] = int(slot)
        used.add(winner)

    if seed % 2 == 0 and used:
        failed = min(used)
        active[failed] = False
        event_type = "robot_failure"
    else:
        load_values[-1] *= 1.65
        event_type = "priority_change"

    payload = {
        "regime": regime,
        "seed": int(seed),
        "robot_positions_m": robot_positions.round(12).tolist(),
        "capabilities": capabilities.round(12).tolist(),
        "battery_fraction": battery.round(12).tolist(),
        "active": active.astype(int).tolist(),
        "load_positions_m": load_positions.round(12).tolist(),
        "load_values": load_values.round(12).tolist(),
        "slot_load": slot_load_array.tolist(),
        "slot_roles": slot_roles,
        "slot_requirements": requirement_array.round(12).tolist(),
        "previous_slot": previous_slot.tolist(),
        "event_type": event_type,
    }
    world_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return FormationWorld(
        regime=regime,
        seed=int(seed),
        robot_positions_m=robot_positions,
        capabilities=capabilities,
        battery_fraction=battery,
        active=active,
        load_positions_m=load_positions,
        load_values=load_values,
        slot_load=slot_load_array,
        slot_roles=tuple(slot_roles),
        slot_requirements=requirement_array,
        previous_slot=previous_slot,
        event_type=event_type,
        world_hash=world_hash,
    )


def compatibility_matrix(
    capabilities: np.ndarray,
    battery_fraction: np.ndarray,
    active: np.ndarray,
    requirements: np.ndarray,
    *,
    minimum_battery: float = 0.20,
) -> np.ndarray:
    """Return robot-slot compatibility under componentwise role thresholds."""

    capability_ok = np.all(capabilities[:, None, :] + 1e-12 >= requirements[None, :, :], axis=2)
    return capability_ok & (battery_fraction[:, None] >= minimum_battery) & active[:, None]


def pair_cost_matrix(
    world: FormationWorld,
    weights: Mapping[str, float],
    *,
    switch_penalty: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Build normalized pair costs and the associated compatibility mask."""

    compatibility = compatibility_matrix(
        world.capabilities,
        world.battery_fraction,
        world.active,
        world.slot_requirements,
        minimum_battery=float(weights.get("minimum_battery", 0.20)),
    )
    target_positions = world.load_positions_m[world.slot_load]
    distances = np.linalg.norm(world.robot_positions_m[:, None, :] - target_positions[None, :, :], axis=2)
    distance_normalized = distances / math.sqrt(200.0)
    penalty = float(weights.get("switch_penalty", 0.20) if switch_penalty is None else switch_penalty)
    changed = (world.previous_slot[:, None] >= 0) & (
        world.previous_slot[:, None] != np.arange(world.n_slots, dtype=int)[None, :]
    )
    joined = world.previous_slot[:, None] < 0
    costs = (
        float(weights.get("distance", 0.55)) * distance_normalized
        + float(weights.get("battery", 0.25)) * (1.0 - world.battery_fraction[:, None])
        + penalty * changed
        + float(weights.get("join", 0.04)) * joined
    )
    costs = np.where(compatibility, costs, np.inf)
    return costs, compatibility


def bid_matrix(world: FormationWorld, costs: np.ndarray) -> np.ndarray:
    """Return the local value share minus pair cost for every robot-slot pair."""

    role_counts = np.bincount(world.slot_load, minlength=world.n_loads)
    shares = world.load_values[world.slot_load] / role_counts[world.slot_load]
    return np.where(np.isfinite(costs), shares[None, :] - costs, -np.inf)


def communication_graph(world: FormationWorld, radius_m: float) -> np.ndarray:
    if radius_m <= 0.0:
        raise ValueError("communication radius must be positive")
    delta = world.robot_positions_m[:, None, :] - world.robot_positions_m[None, :, :]
    distances = np.linalg.norm(delta, axis=2)
    adjacency = (distances <= float(radius_m)) & (~np.eye(world.n_robots, dtype=bool))
    adjacency &= world.active[:, None] & world.active[None, :]
    return adjacency


def greedy_matching(scores: np.ndarray, visible_robots: set[int] | None = None) -> np.ndarray:
    """Deterministic maximum-bid greedy matching over the visible bid records."""

    n_robots, n_slots = scores.shape
    visible = set(range(n_robots)) if visible_robots is None else set(visible_robots)
    pairs: list[tuple[float, int, int]] = []
    for robot in sorted(visible):
        for slot in range(n_slots):
            score = float(scores[robot, slot])
            if np.isfinite(score) and score > 0.0:
                pairs.append((-score, robot, slot))
    pairs.sort()
    assignment = np.full(n_robots, -1, dtype=int)
    occupied: set[int] = set()
    for _, robot, slot in pairs:
        if assignment[robot] < 0 and slot not in occupied:
            assignment[robot] = slot
            occupied.add(slot)
    return assignment


def distributed_gossip_matching(
    world: FormationWorld,
    scores: np.ndarray,
    *,
    radius_m: float,
    rounds: int,
) -> DistributedResult:
    """Run finite-hop bid flooding and aggregate robots' self-accepted actions."""

    if rounds < 0:
        raise ValueError("gossip rounds must be non-negative")
    adjacency = communication_graph(world, radius_m)
    views: list[set[int]] = [{robot} if world.active[robot] else set() for robot in range(world.n_robots)]
    messages = 0
    bytes_sent = 0
    finite_bids = np.isfinite(scores) & (scores > 0.0)
    directed_edges = np.argwhere(adjacency)
    for _ in range(int(rounds)):
        previous = [set(view) for view in views]
        updated = [set(view) for view in views]
        for sender, receiver in directed_edges:
            sender_id = int(sender)
            receiver_id = int(receiver)
            updated[receiver_id].update(previous[sender_id])
            records = previous[sender_id]
            bid_values = sum(int(np.sum(finite_bids[robot])) for robot in records)
            messages += 1
            bytes_sent += 24 + 16 * len(records) + 16 * bid_values
        views = updated

    assignment = np.full(world.n_robots, -1, dtype=int)
    active_count = max(int(np.sum(world.active)), 1)
    coverage: list[float] = []
    for robot in range(world.n_robots):
        if not world.active[robot]:
            continue
        local = greedy_matching(scores, views[robot])
        if local[robot] >= 0:
            assignment[robot] = int(local[robot])
        coverage.append(len(views[robot]) / active_count)
    return DistributedResult(
        assignment=assignment,
        messages=messages,
        bytes_sent=bytes_sent,
        mean_view_coverage=float(np.mean(coverage)) if coverage else 0.0,
        min_view_coverage=float(np.min(coverage)) if coverage else 0.0,
        network_components=_component_count(adjacency, world.active),
        visibility=tuple(tuple(sorted(view)) for view in views),
    )


def solve_central_milp(world: FormationWorld, costs: np.ndarray, *, time_limit_s: float) -> OracleResult:
    """Solve the all-or-none role assignment using global information."""

    n_x = world.n_robots * world.n_slots
    n_variables = n_x + world.n_loads
    objective = np.zeros(n_variables, dtype=float)
    finite_costs = np.where(np.isfinite(costs), costs, 0.0)
    objective[:n_x] = finite_costs.reshape(-1)
    objective[n_x:] = -world.load_values

    upper = np.ones(n_variables, dtype=float)
    upper[:n_x] = np.isfinite(costs).astype(float).reshape(-1)
    bounds = Bounds(np.zeros(n_variables, dtype=float), upper)

    n_constraints = world.n_robots + world.n_slots
    matrix = lil_matrix((n_constraints, n_variables), dtype=float)
    lower = np.full(n_constraints, -np.inf, dtype=float)
    upper_constraint = np.ones(n_constraints, dtype=float)
    for robot in range(world.n_robots):
        start = robot * world.n_slots
        matrix[robot, start : start + world.n_slots] = 1.0
    for slot in range(world.n_slots):
        row = world.n_robots + slot
        for robot in range(world.n_robots):
            matrix[row, robot * world.n_slots + slot] = 1.0
        matrix[row, n_x + int(world.slot_load[slot])] = -1.0
        lower[row] = 0.0
        upper_constraint[row] = 0.0

    result = milp(
        objective,
        integrality=np.ones(n_variables, dtype=int),
        bounds=bounds,
        constraints=LinearConstraint(matrix.tocsr(), lower, upper_constraint),
        options={"time_limit": float(time_limit_s)},
    )
    if result.x is None:
        assignment = np.full(world.n_robots, -1, dtype=int)
        activated = np.zeros(world.n_loads, dtype=int)
        objective_value = 0.0
    else:
        x = np.asarray(result.x[:n_x]).reshape(world.n_robots, world.n_slots)
        assignment = np.full(world.n_robots, -1, dtype=int)
        for robot in range(world.n_robots):
            selected = np.flatnonzero(x[robot] > 0.5)
            if selected.size:
                assignment[robot] = int(selected[0])
        activated = (np.asarray(result.x[n_x:]) > 0.5).astype(int)
        objective_value = float(-result.fun) if result.fun is not None else 0.0
    gap = float(getattr(result, "mip_gap", math.nan))
    return OracleResult(
        assignment=assignment,
        activated=activated,
        objective_value=objective_value,
        solver_status=int(result.status),
        solver_message=str(result.message),
        mip_gap=gap,
    )


def evaluate_assignment(world: FormationWorld, assignment: np.ndarray, costs: np.ndarray) -> dict[str, Any]:
    """Evaluate CLOSED/GUARDED status without repairing the submitted profile."""

    assignment = np.asarray(assignment, dtype=int)
    if assignment.shape != (world.n_robots,):
        raise ValueError("assignment has incompatible shape")
    compatibility = np.isfinite(costs)
    slot_counts = np.zeros(world.n_slots, dtype=int)
    invalid_assignments = 0
    assigned_cost = 0.0
    for robot, slot in enumerate(assignment):
        if slot < 0:
            continue
        if slot >= world.n_slots:
            invalid_assignments += 1
            continue
        slot_counts[slot] += 1
        if not compatibility[robot, slot]:
            invalid_assignments += 1
            assigned_cost += 1_000.0
        else:
            assigned_cost += float(costs[robot, slot])

    started = np.zeros(world.n_loads, dtype=bool)
    waiting = np.zeros(world.n_loads, dtype=bool)
    load_rows: list[dict[str, Any]] = []
    for load in range(world.n_loads):
        slots = np.flatnonzero(world.slot_load == load)
        counts = slot_counts[slots]
        complete = bool(np.all(counts == 1))
        has_claim = bool(np.any(counts > 0))
        started[load] = complete
        waiting[load] = has_claim and not complete
        load_rows.append(
            {
                "load_id": load,
                "decision": "start" if complete else ("wait" if has_claim else "idle"),
                "required_roles": int(len(slots)),
                "assigned_claims": int(np.sum(counts)),
                "unmet_roles": int(np.sum(counts == 0)),
                "duplicate_slots": int(np.sum(counts > 1)),
                "load_value": float(world.load_values[load]),
            }
        )

    previous = world.previous_slot
    active = world.active
    switches = int(np.sum(active & (previous >= 0) & (assignment >= 0) & (assignment != previous)))
    abandonments = int(np.sum(active & (previous >= 0) & (assignment < 0)))
    joins = int(np.sum(active & (previous < 0) & (assignment >= 0)))
    failed_departures = int(np.sum((~active) & (previous >= 0)))
    social_value = float(np.sum(world.load_values[started]) - assigned_cost)
    return {
        "started_loads": int(np.sum(started)),
        "waiting_loads": int(np.sum(waiting)),
        "idle_loads": int(world.n_loads - np.sum(started) - np.sum(waiting)),
        "assigned_robots": int(np.sum(assignment >= 0)),
        "unmet_roles": int(np.sum(slot_counts == 0)),
        "duplicate_slots": int(np.sum(slot_counts > 1)),
        "overrecruitment": int(np.sum(np.maximum(slot_counts - 1, 0))),
        "invalid_assignments": int(invalid_assignments),
        "switches": switches,
        "abandonments": abandonments,
        "joins": joins,
        "failed_departures": failed_departures,
        "assignment_cost": float(assigned_cost),
        "social_value": social_value,
        "load_rows": load_rows,
        "slot_counts": slot_counts,
    }


def assignment_records(world: FormationWorld, assignment: np.ndarray, costs: np.ndarray) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for robot, slot in enumerate(np.asarray(assignment, dtype=int)):
        load = int(world.slot_load[slot]) if 0 <= slot < world.n_slots else -1
        role = world.slot_roles[slot] if 0 <= slot < world.n_slots else "idle"
        records.append(
            {
                "robot_id": robot,
                "active": bool(world.active[robot]),
                "previous_slot": int(world.previous_slot[robot]),
                "selected_slot": int(slot),
                "load_id": load,
                "role": role,
                "compatible": bool(slot < 0 or (slot < world.n_slots and np.isfinite(costs[robot, slot]))),
                "changed": bool(world.previous_slot[robot] != slot),
            }
        )
    return records


def _component_count(adjacency: np.ndarray, active: np.ndarray) -> int:
    unseen = set(np.flatnonzero(active).tolist())
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            node = stack.pop()
            neighbours = set(np.flatnonzero(adjacency[node]).tolist()) & unseen
            unseen.difference_update(neighbours)
            stack.extend(neighbours)
    return components


__all__ = [
    "CAPABILITY_NAMES",
    "DistributedResult",
    "FormationWorld",
    "OracleResult",
    "assignment_records",
    "bid_matrix",
    "communication_graph",
    "compatibility_matrix",
    "distributed_gossip_matching",
    "evaluate_assignment",
    "generate_world",
    "greedy_matching",
    "pair_cost_matrix",
    "solve_central_milp",
]
