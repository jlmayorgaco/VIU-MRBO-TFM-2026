"""SCALE-QPG: sparse atomic quota-game recruitment.

The simulator is centralized only as an experimental harness.  Persistent
robot state is deliberately sparse: a robot stores its current commitment and
dictionaries indexed by its active set, never a length-K market vector.
Physical assignments remain integer-valued throughout.  Logit probabilities
select proposals; only an exact positive potential change can be committed.
"""

from __future__ import annotations

import math
import time
import tracemalloc
from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Sequence

import numpy as np

from .quota_game_core import (
    FLOAT64_BYTES,
    INT64_BYTES,
    QuotaGraph,
    QuotaWorld,
    RecoveryResult,
    assignment_distance,
    capacities_by_load,
    evaluate_assignment,
    recover_assignment,
    social_potential,
    stable_hash,
)


SCALE_METHODS = (
    "SCALE-QPG-BR-LocalAR",
    "SCALE-QPG-LogitBR-LocalAR",
    "SCALE-QPG-LogitBR-GlobalAR",
)


@dataclass(slots=True)
class RobotLocalState:
    """Persistent sparse state held by one robot."""

    robot_id: int
    commitment: int
    previous_assignment: int
    active_set: tuple[int, ...] = field(default_factory=tuple)
    intention: dict[int, float] = field(default_factory=dict)
    local_versions: dict[int, int] = field(default_factory=dict)
    local_prices: dict[int, float] = field(default_factory=dict)
    phase: str = "current"
    reservation_id: str | None = None

    def validate_sparse(self, maximum_size: int, n_loads: int) -> bool:
        keys = set(self.active_set)
        return bool(
            len(self.active_set) <= int(maximum_size)
            and set(self.intention) <= keys
            and set(self.local_versions) <= (keys - {n_loads})
            and set(self.local_prices) <= (keys - {n_loads})
            and all(0 <= action <= n_loads for action in self.active_set)
        )


@dataclass(slots=True)
class LoadMarket:
    """State hosted by one load market."""

    load_id: int
    committed_capacity: float
    lower: float
    upper: float
    marginal_price: float
    deficit: float
    version: int = 0
    reserved_incoming: float = 0.0


@dataclass(frozen=True, slots=True)
class Proposal:
    proposal_id: str
    robot_id: int
    source_load: int
    target_load: int
    capacity: float
    delta_phi: float
    source_version: int
    target_version: int
    timestamp: int


@dataclass(slots=True)
class Reservation:
    proposal: Proposal
    expires_at: int
    status: str = "tentative"


@dataclass(frozen=True, slots=True)
class CommitDecision:
    accepted: bool
    reason: str
    proposal_id: str
    delta_phi: float


@dataclass(frozen=True, slots=True)
class ResidualUniverse:
    affected_loads: tuple[int, ...]
    loads: tuple[int, ...]
    robots: tuple[int, ...]
    radius: int
    is_global: bool


@dataclass(frozen=True, slots=True)
class LocalRecoveryResult:
    recovery: RecoveryResult
    universe: ResidualUniverse
    touched_loads: tuple[int, ...]
    touched_robots: tuple[int, ...]
    locality_respected: bool
    fallback_used: bool


@dataclass(frozen=True, slots=True)
class ScaleRunResult:
    method: str
    assignment_before_recovery: np.ndarray
    assignment: np.ndarray
    feasible_before_recovery: bool
    feasible: bool
    converged: bool
    censored: bool
    censoring_reason: str
    logical_epochs: int
    activations: int
    proposals: int
    rejected_proposals: int
    accepted_moves: int
    version_conflicts: int
    rollbacks: int
    potential_increments: tuple[float, ...]
    strict_potential_monotone: bool
    repeated_states: int
    cycles_detected: int
    packets_total: int
    scalar_transmissions_total: int
    payload_bytes_total: int
    indices_bytes_total: int
    versions_bytes_total: int
    reservation_bytes_total: int
    recovery_bytes_total: int
    first_atomic_assignment_time_s: float
    first_feasible_time_s: float | None
    first_persistent_feasible_time_s: float | None
    final_termination_time_s: float
    wall_time_s: float
    cpu_time_s: float
    peak_memory_mb: float
    maximum_active_set_size: int
    mean_active_set_size: float
    recovery: LocalRecoveryResult
    recourse_hamming: int
    traces: tuple[dict[str, Any], ...]
    message_rows: tuple[dict[str, Any], ...]


class MessageLedger:
    """Recomputable logical payload accounting over graph edges."""

    _INDEX_FIELDS = {
        "proposal": 3,
        "reservation": 3,
        "commit": 3,
        "rollback": 3,
        "market_update": 1,
        "active_set_update": 1,
        "recovery": 3,
    }
    _VERSION_FIELDS = {
        "proposal": 2,
        "reservation": 2,
        "commit": 2,
        "rollback": 2,
        "market_update": 1,
        "active_set_update": 0,
        "recovery": 1,
    }

    def __init__(self, schema: Mapping[str, Mapping[str, int]]) -> None:
        self.schema = schema
        self.rows: list[dict[str, Any]] = []

    def record(
        self,
        kind: str,
        *,
        route_hops: int,
        activation: int,
        robot: int | None = None,
        source: int | None = None,
        target: int | None = None,
        note: str = "",
    ) -> None:
        spec = self.schema[kind]
        hops = max(0, int(route_hops))
        floats = int(spec["float64"])
        integers = int(spec["int64"])
        scalar_transmissions = floats * hops
        payload = (floats * FLOAT64_BYTES + integers * INT64_BYTES) * hops
        index_fields = min(integers, int(self._INDEX_FIELDS[kind]))
        version_fields = min(
            max(0, integers - index_fields),
            int(self._VERSION_FIELDS[kind]),
        )
        indices_bytes = index_fields * INT64_BYTES * hops
        versions_bytes = version_fields * INT64_BYTES * hops
        self.rows.append(
            {
                "activation": int(activation),
                "message_kind": kind,
                "route_hops": hops,
                "packets": hops,
                "float64_fields": floats,
                "int64_fields": integers,
                "scalar_transmissions": scalar_transmissions,
                "payload_bytes": payload,
                "indices_bytes": indices_bytes,
                "versions_bytes": versions_bytes,
                "reservation_bytes": payload
                if kind in {"reservation", "rollback"}
                else 0,
                "recovery_bytes": payload if kind == "recovery" else 0,
                "robot": robot,
                "source": source,
                "target": target,
                "note": note,
            }
        )

    def totals(self) -> dict[str, int]:
        return {
            "packets": int(sum(row["packets"] for row in self.rows)),
            "scalars": int(
                sum(row["scalar_transmissions"] for row in self.rows)
            ),
            "payload": int(sum(row["payload_bytes"] for row in self.rows)),
            "indices": int(sum(row["indices_bytes"] for row in self.rows)),
            "versions": int(sum(row["versions_bytes"] for row in self.rows)),
            "reservation": int(
                sum(row["reservation_bytes"] for row in self.rows)
            ),
            "recovery": int(sum(row["recovery_bytes"] for row in self.rows)),
        }

    def is_recomputable(self) -> bool:
        for row in self.rows:
            expected = (
                int(row["float64_fields"]) * FLOAT64_BYTES
                + int(row["int64_fields"]) * INT64_BYTES
            ) * int(row["route_hops"])
            if expected != int(row["payload_bytes"]):
                return False
            if int(row["packets"]) != int(row["route_hops"]):
                return False
        return True


def load_value(
    capacity: float,
    lower: float,
    upper: float,
    *,
    rho_minus: float,
    rho_plus: float,
) -> float:
    """Return the load component V_k(Q) of the atomic potential."""

    deficit = max(0.0, float(lower) - float(capacity))
    excess = max(0.0, float(capacity) - float(upper))
    return float(
        -0.5 * float(rho_minus) * deficit**2
        - 0.5 * float(rho_plus) * excess**2
    )


def marginal_price(
    capacity: float,
    lower: float,
    upper: float,
    *,
    rho_minus: float,
    rho_plus: float,
) -> float:
    """Derivative of V_k where it is differentiable."""

    if capacity < lower:
        return float(rho_minus) * (float(lower) - float(capacity))
    if capacity > upper:
        return -float(rho_plus) * (float(capacity) - float(upper))
    return 0.0


def atomic_potential(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    rho_minus: float,
    rho_plus: float,
    gamma_switch: float,
    previous_assignment: np.ndarray | None,
) -> float:
    """Canonical finite potential in normalized-cost units."""

    return social_potential(
        world,
        np.asarray(assignment, dtype=int),
        rho_minus=float(rho_minus),
        rho_plus=float(rho_plus),
        gamma_switch=float(gamma_switch),
        previous_assignment=previous_assignment,
    )


def exact_move_delta(
    world: QuotaWorld,
    assignment: np.ndarray,
    robot: int,
    target: int,
    *,
    rho_minus: float,
    rho_plus: float,
    gamma_switch: float,
    previous_assignment: np.ndarray | None,
) -> float:
    """Exact finite difference, not a continuous-gradient approximation."""

    current = np.asarray(assignment, dtype=int)
    if int(target) == int(current[int(robot)]):
        return 0.0
    if target < 0 or target > world.idle_index:
        return -math.inf
    if target < world.n_loads and not world.compatibility[int(robot), int(target)]:
        return -math.inf
    candidate = current.copy()
    candidate[int(robot)] = int(target)
    return atomic_potential(
        world,
        candidate,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
        gamma_switch=gamma_switch,
        previous_assignment=previous_assignment,
    ) - atomic_potential(
        world,
        current,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
        gamma_switch=gamma_switch,
        previous_assignment=previous_assignment,
    )


def initialize_markets(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    rho_minus: float,
    rho_plus: float,
) -> list[LoadMarket]:
    capacities = capacities_by_load(
        np.asarray(assignment, dtype=int),
        world.capacities,
        world.n_loads,
    )
    return [
        LoadMarket(
            load_id=load,
            committed_capacity=float(capacities[load]),
            lower=float(world.lower_quotas[load]),
            upper=float(world.upper_quotas[load]),
            marginal_price=marginal_price(
                capacities[load],
                world.lower_quotas[load],
                world.upper_quotas[load],
                rho_minus=rho_minus,
                rho_plus=rho_plus,
            ),
            deficit=max(0.0, float(world.lower_quotas[load] - capacities[load])),
        )
        for load in range(world.n_loads)
    ]


def build_active_set(
    world: QuotaWorld,
    markets: Sequence[LoadMarket],
    robot: RobotLocalState,
    *,
    maximum_size: int,
    gamma_switch: float,
) -> tuple[int, ...]:
    """Build a deterministic active set with urgent invitations first."""

    maximum = int(maximum_size)
    if maximum < 2:
        raise ValueError("L must leave room for current and idle")
    mandatory = [int(robot.commitment), world.idle_index]
    selected: list[int] = []
    for action in mandatory:
        if action not in selected:
            selected.append(action)

    candidates: list[tuple[int, float, int]] = []
    for load, market in enumerate(markets):
        if not world.compatibility[robot.robot_id, load] or load in selected:
            continue
        switch = (
            float(gamma_switch)
            if load != int(robot.previous_assignment)
            else 0.0
        )
        reduced = (
            float(world.normalized_costs[robot.robot_id, load])
            - float(world.capacities[robot.robot_id]) * market.marginal_price
            + switch
        )
        urgent = int(market.deficit > 1.0e-12)
        candidates.append((-urgent, reduced, load))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    for _, _, load in candidates:
        if len(selected) >= maximum:
            break
        selected.append(int(load))
    return tuple(selected)


def refresh_robot_sparse_state(
    world: QuotaWorld,
    markets: Sequence[LoadMarket],
    robot: RobotLocalState,
    *,
    maximum_size: int,
    gamma_switch: float,
) -> bool:
    """Refresh only sparse dictionaries and return whether A_i changed."""

    active = build_active_set(
        world,
        markets,
        robot,
        maximum_size=maximum_size,
        gamma_switch=gamma_switch,
    )
    changed = active != robot.active_set
    robot.active_set = active
    robot.local_versions = {
        action: int(markets[action].version)
        for action in active
        if action < world.n_loads
    }
    robot.local_prices = {
        action: float(markets[action].marginal_price)
        for action in active
        if action < world.n_loads
    }
    if not robot.intention or set(robot.intention) != set(active):
        probability = 1.0 / len(active)
        robot.intention = {action: probability for action in active}
    return changed


class AtomicCommitProtocol:
    """Serialized two-phase commit with explicit versions and rollback."""

    def __init__(
        self,
        *,
        world: QuotaWorld,
        graph: QuotaGraph,
        assignment: np.ndarray,
        robots: Sequence[RobotLocalState],
        markets: Sequence[LoadMarket],
        ledger: MessageLedger,
        rho_minus: float,
        rho_plus: float,
        gamma_switch: float,
        epsilon_improvement: float,
        epsilon_price: float,
        reservation_timeout: int,
        previous_assignment: np.ndarray | None,
    ) -> None:
        self.world = world
        self.graph = graph
        self.assignment = assignment
        self.robots = list(robots)
        self.markets = list(markets)
        self.ledger = ledger
        self.rho_minus = float(rho_minus)
        self.rho_plus = float(rho_plus)
        self.gamma_switch = float(gamma_switch)
        self.epsilon_improvement = float(epsilon_improvement)
        self.epsilon_price = float(epsilon_price)
        self.reservation_timeout = int(reservation_timeout)
        self.previous_assignment = previous_assignment
        self.reservations: dict[str, Reservation] = {}
        self.preserve_lower = bool(evaluate_assignment(world, assignment)["feasible"])
        self.version_conflicts = 0
        self.rollbacks = 0
        self.rejections: dict[str, int] = {}

    def _reject(self, proposal: Proposal, reason: str) -> CommitDecision:
        self.rejections[reason] = self.rejections.get(reason, 0) + 1
        if reason == "version_conflict":
            self.version_conflicts += 1
        return CommitDecision(False, reason, proposal.proposal_id, proposal.delta_phi)

    def prepare(
        self,
        proposal: Proposal,
        *,
        activation: int,
        chain_reserved: bool = False,
    ) -> CommitDecision:
        robot = self.robots[proposal.robot_id]
        source = int(self.assignment[proposal.robot_id])
        target = int(proposal.target_load)
        if robot.phase != "current" or source != int(proposal.source_load):
            return self._reject(proposal, "robot_not_current")
        if target == source:
            return self._reject(proposal, "no_change")
        source_version = (
            self.markets[source].version if source < self.world.n_loads else -1
        )
        target_version = (
            self.markets[target].version if target < self.world.n_loads else -1
        )
        if (
            source_version != int(proposal.source_version)
            or target_version != int(proposal.target_version)
        ):
            return self._reject(proposal, "version_conflict")
        exact = exact_move_delta(
            self.world,
            self.assignment,
            proposal.robot_id,
            target,
            rho_minus=self.rho_minus,
            rho_plus=self.rho_plus,
            gamma_switch=self.gamma_switch,
            previous_assignment=self.previous_assignment,
        )
        if not np.isfinite(exact) or abs(exact - proposal.delta_phi) > 1.0e-9:
            return self._reject(proposal, "stale_delta")
        if exact <= self.epsilon_improvement:
            return self._reject(proposal, "non_improving")
        if target < self.world.n_loads:
            market = self.markets[target]
            if (
                market.committed_capacity
                + market.reserved_incoming
                + proposal.capacity
                > market.upper + 1.0e-9
            ):
                return self._reject(proposal, "upper_quota")
        if (
            self.preserve_lower
            and source < self.world.n_loads
            and not chain_reserved
            and self.markets[source].committed_capacity - proposal.capacity
            < self.markets[source].lower - 1.0e-9
        ):
            return self._reject(proposal, "protected_lower_quota")
        if target < self.world.n_loads:
            self.markets[target].reserved_incoming += proposal.capacity
        robot.phase = "tentative"
        robot.reservation_id = proposal.proposal_id
        self.reservations[proposal.proposal_id] = Reservation(
            proposal=proposal,
            expires_at=int(activation) + self.reservation_timeout,
        )
        target_for_route = target if target < self.world.n_loads else source
        hops = (
            int(self.graph.market_route_hops[target_for_route, proposal.robot_id])
            if target_for_route < self.world.n_loads
            else 0
        )
        self.ledger.record(
            "reservation",
            route_hops=hops,
            activation=activation,
            robot=proposal.robot_id,
            source=source,
            target=target,
        )
        return CommitDecision(True, "tentative", proposal.proposal_id, exact)

    def commit(self, proposal_id: str, *, activation: int) -> CommitDecision:
        reservation = self.reservations.get(proposal_id)
        if reservation is None or reservation.status != "tentative":
            dummy = Proposal(proposal_id, 0, 0, 0, 0.0, 0.0, -1, -1, activation)
            return self._reject(dummy, "missing_reservation")
        proposal = reservation.proposal
        if int(activation) > reservation.expires_at:
            self.rollback(proposal_id, activation=activation, reason="timeout")
            return CommitDecision(
                False,
                "timeout",
                proposal.proposal_id,
                proposal.delta_phi,
            )
        robot = self.robots[proposal.robot_id]
        source = int(proposal.source_load)
        target = int(proposal.target_load)
        if int(self.assignment[proposal.robot_id]) != source:
            self.rollback(
                proposal_id,
                activation=activation,
                reason="assignment_changed",
            )
            return CommitDecision(
                False,
                "assignment_changed",
                proposal.proposal_id,
                proposal.delta_phi,
            )
        before_prices = {
            load: self.markets[load].marginal_price
            for load in (source, target)
            if load < self.world.n_loads
        }
        if target < self.world.n_loads:
            self.markets[target].reserved_incoming -= proposal.capacity
            self.markets[target].committed_capacity += proposal.capacity
        if source < self.world.n_loads:
            self.markets[source].committed_capacity -= proposal.capacity
        self.assignment[proposal.robot_id] = target
        robot.commitment = target
        robot.phase = "current"
        robot.reservation_id = None
        reservation.status = "committed"
        for load in sorted({source, target}):
            if load >= self.world.n_loads:
                continue
            market = self.markets[load]
            old_deficit_sign = market.deficit > 1.0e-12
            market.deficit = max(0.0, market.lower - market.committed_capacity)
            next_price = marginal_price(
                market.committed_capacity,
                market.lower,
                market.upper,
                rho_minus=self.rho_minus,
                rho_plus=self.rho_plus,
            )
            price_trigger = abs(next_price - before_prices[load]) > self.epsilon_price
            sign_trigger = old_deficit_sign != (market.deficit > 1.0e-12)
            market.marginal_price = next_price
            market.version += 1
            if price_trigger or sign_trigger:
                subscribers = [
                    state.robot_id
                    for state in self.robots
                    if load in state.active_set
                ]
                route_hops = int(
                    sum(
                        self.graph.market_route_hops[load, subscriber]
                        for subscriber in subscribers
                    )
                )
                self.ledger.record(
                    "market_update",
                    route_hops=route_hops,
                    activation=activation,
                    robot=proposal.robot_id,
                    source=source,
                    target=target,
                    note="price_or_deficit_trigger",
                )
        target_for_route = target if target < self.world.n_loads else source
        hops = (
            int(self.graph.market_route_hops[target_for_route, proposal.robot_id])
            if target_for_route < self.world.n_loads
            else 0
        )
        self.ledger.record(
            "commit",
            route_hops=hops,
            activation=activation,
            robot=proposal.robot_id,
            source=source,
            target=target,
        )
        self.preserve_lower = self.preserve_lower or bool(
            evaluate_assignment(self.world, self.assignment)["feasible"]
        )
        return CommitDecision(
            True,
            "committed",
            proposal.proposal_id,
            proposal.delta_phi,
        )

    def rollback(
        self,
        proposal_id: str,
        *,
        activation: int,
        reason: str,
    ) -> None:
        reservation = self.reservations.get(proposal_id)
        if reservation is None or reservation.status != "tentative":
            return
        proposal = reservation.proposal
        if proposal.target_load < self.world.n_loads:
            self.markets[proposal.target_load].reserved_incoming -= proposal.capacity
        robot = self.robots[proposal.robot_id]
        robot.phase = "current"
        robot.reservation_id = None
        reservation.status = "rolled_back"
        self.rollbacks += 1
        target_for_route = (
            proposal.target_load
            if proposal.target_load < self.world.n_loads
            else proposal.source_load
        )
        hops = (
            int(
                self.graph.market_route_hops[
                    target_for_route,
                    proposal.robot_id,
                ]
            )
            if target_for_route < self.world.n_loads
            else 0
        )
        self.ledger.record(
            "rollback",
            route_hops=hops,
            activation=activation,
            robot=proposal.robot_id,
            source=proposal.source_load,
            target=proposal.target_load,
            note=reason,
        )

    def expire(self, *, activation: int) -> None:
        for reservation_id, reservation in list(self.reservations.items()):
            if (
                reservation.status == "tentative"
                and int(activation) > reservation.expires_at
            ):
                self.rollback(
                    reservation_id,
                    activation=activation,
                    reason="timeout",
                )


def _route_for_proposal(
    graph: QuotaGraph,
    world: QuotaWorld,
    robot: int,
    source: int,
    target: int,
) -> int:
    host_load = target if target < world.n_loads else source
    return (
        int(graph.market_route_hops[host_load, robot])
        if host_load < world.n_loads
        else 0
    )


def _proposal(
    *,
    world: QuotaWorld,
    protocol: AtomicCommitProtocol,
    robot: int,
    target: int,
    activation: int,
) -> Proposal:
    source = int(protocol.assignment[robot])
    delta = exact_move_delta(
        world,
        protocol.assignment,
        robot,
        target,
        rho_minus=protocol.rho_minus,
        rho_plus=protocol.rho_plus,
        gamma_switch=protocol.gamma_switch,
        previous_assignment=protocol.previous_assignment,
    )
    source_version = (
        protocol.markets[source].version if source < world.n_loads else -1
    )
    target_version = (
        protocol.markets[target].version if target < world.n_loads else -1
    )
    identifier = stable_hash(
        {
            "robot": robot,
            "source": source,
            "target": target,
            "activation": activation,
            "source_version": source_version,
            "target_version": target_version,
        }
    )[:20]
    return Proposal(
        proposal_id=identifier,
        robot_id=int(robot),
        source_load=source,
        target_load=int(target),
        capacity=float(world.capacities[robot]),
        delta_phi=float(delta),
        source_version=int(source_version),
        target_version=int(target_version),
        timestamp=int(activation),
    )


def residual_universe(
    world: QuotaWorld,
    assignment: np.ndarray,
    active_sets: Sequence[Sequence[int]],
    affected_loads: Sequence[int],
    *,
    radius: int,
    global_scope: bool = False,
) -> ResidualUniverse:
    """Build the local bipartite residual universe by bounded BFS."""

    affected = {
        int(load)
        for load in affected_loads
        if 0 <= int(load) < world.n_loads
    }
    if global_scope:
        return ResidualUniverse(
            affected_loads=tuple(sorted(affected)),
            loads=tuple(range(world.n_loads)),
            robots=tuple(range(world.n_robots)),
            radius=int(radius),
            is_global=True,
        )
    loads = set(affected)
    robots: set[int] = set()
    frontier = set(affected)
    for _ in range(max(0, int(radius)) + 1):
        if not frontier:
            break
        next_robots = {
            robot
            for robot in range(world.n_robots)
            if any(
                world.compatibility[robot, load]
                and (
                    load in set(map(int, active_sets[robot]))
                    or int(assignment[robot]) == load
                )
                for load in frontier
            )
        }
        next_robots -= robots
        robots.update(next_robots)
        next_loads: set[int] = set()
        for robot in next_robots:
            current = int(assignment[robot])
            if current < world.n_loads:
                next_loads.add(current)
            next_loads.update(
                action
                for action in map(int, active_sets[robot])
                if action < world.n_loads
            )
        next_loads -= loads
        loads.update(next_loads)
        frontier = next_loads
    return ResidualUniverse(
        affected_loads=tuple(sorted(affected)),
        loads=tuple(sorted(loads)),
        robots=tuple(sorted(robots)),
        radius=int(radius),
        is_global=False,
    )


def run_local_recovery(
    world: QuotaWorld,
    assignment: np.ndarray,
    active_sets: Sequence[Sequence[int]],
    options: Mapping[str, Any],
    *,
    affected_loads: Sequence[int] | None,
    radius: int,
    maximum_chain_length: int,
    previous_assignment: np.ndarray | None,
    global_scope: bool,
) -> LocalRecoveryResult:
    """Run common AR under an auditable compatibility restriction."""

    initial = np.asarray(assignment, dtype=int).copy()
    capacities = capacities_by_load(initial, world.capacities, world.n_loads)
    violations = set(
        map(
            int,
            np.flatnonzero(
                (capacities < world.lower_quotas - 1.0e-9)
                | (capacities > world.upper_quotas + 1.0e-9)
            ),
        )
    )
    if affected_loads is not None:
        violations.update(
            int(load)
            for load in affected_loads
            if 0 <= int(load) < world.n_loads
        )
    universe = residual_universe(
        world,
        initial,
        active_sets,
        sorted(violations),
        radius=radius,
        global_scope=global_scope,
    )
    if global_scope:
        restricted_world = world
    else:
        mask = np.zeros_like(world.compatibility, dtype=bool)
        local_loads = set(universe.loads)
        local_robots = set(universe.robots)
        for robot in range(world.n_robots):
            current = int(initial[robot])
            if robot in local_robots:
                allowed = local_loads & set(
                    map(int, np.flatnonzero(world.compatibility[robot]))
                )
                if current < world.n_loads:
                    allowed.add(current)
                if allowed:
                    mask[robot, sorted(allowed)] = True
            elif current < world.n_loads:
                mask[robot, current] = True
        restricted_world = replace(world, compatibility=mask)
    recovery_options = dict(options)
    recovery_options["compress"] = False
    recovery_options["local_exchange"] = False
    result = recover_assignment(
        restricted_world,
        initial,
        recovery_options,
        previous_assignment=previous_assignment,
        max_chain_length_override=int(maximum_chain_length),
    )
    changed = np.flatnonzero(result.assignment != initial)
    touched_robots = tuple(map(int, changed))
    touched_loads = set()
    for robot in changed:
        before, after = int(initial[robot]), int(result.assignment[robot])
        if before < world.n_loads:
            touched_loads.add(before)
        if after < world.n_loads:
            touched_loads.add(after)
    locality = bool(
        global_scope
        or (
            set(touched_robots) <= set(universe.robots)
            and touched_loads <= set(universe.loads)
        )
    )
    return LocalRecoveryResult(
        recovery=result,
        universe=universe,
        touched_loads=tuple(sorted(touched_loads)),
        touched_robots=touched_robots,
        locality_respected=locality,
        fallback_used=False,
    )


def _empty_recovery(
    world: QuotaWorld,
    assignment: np.ndarray,
    *,
    global_scope: bool,
) -> LocalRecoveryResult:
    metrics = evaluate_assignment(world, assignment)
    recovery = RecoveryResult(
        assignment=np.asarray(assignment, dtype=int).copy(),
        success=bool(metrics["feasible"]),
        failure_reason="none" if metrics["feasible"] else "not_run",
        runtime_s=0.0,
        chain_lengths=tuple(),
        nodes_expanded=0,
        robots_reassigned=0,
        cost_before_m=float(metrics["distance_total_m"]),
        cost_after_m=float(metrics["distance_total_m"]),
        loads_repaired=0,
        residual_deficit_loads=int(metrics["deficit_total"] > 1.0e-9),
        residual_excess_loads=int(metrics["excess_upper_total"] > 1.0e-9),
        residual_no_path=False,
    )
    universe = ResidualUniverse(
        affected_loads=tuple(),
        loads=tuple(),
        robots=tuple(),
        radius=0,
        is_global=global_scope,
    )
    return LocalRecoveryResult(
        recovery=recovery,
        universe=universe,
        touched_loads=tuple(),
        touched_robots=tuple(),
        locality_respected=True,
        fallback_used=False,
    )


def run_scale_qpg(
    world: QuotaWorld,
    graph: QuotaGraph,
    method: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    stage: str,
    seed: int,
    initial_assignment: np.ndarray | None = None,
    previous_assignment: np.ndarray | None = None,
    affected_loads: Sequence[int] | None = None,
) -> ScaleRunResult:
    """Run SCALE-QPG and its declared local/global recovery closure."""

    if method not in SCALE_METHODS:
        raise ValueError(f"unsupported SCALE-QPG method: {method}")
    scale_config = config["scale"]
    maximum_epochs = int(scale_config["max_epochs"][stage])
    maximum_wall = float(scale_config["max_wall_time_s"][stage])
    maximum_proposals = int(scale_config["max_proposals"][stage])
    reservation_timeout = int(scale_config["reservation_timeout_activations"])
    stable_required = int(scale_config["stable_epochs_required"])
    L = int(parameters["L"])
    rho_minus = float(parameters["rho_minus"])
    rho_plus = float(parameters["rho_plus"])
    gamma_switch = float(parameters["gamma_switch"])
    epsilon = float(parameters["epsilon_improvement"])
    epsilon_price = float(parameters["epsilon_price"])
    temperature_initial = float(parameters["T0"])
    temperature_minimum = float(parameters["T_min"])
    anneal = float(parameters["anneal"])
    explore_activations = (
        0 if method == "SCALE-QPG-BR-LocalAR" else int(parameters["R_explore"])
    )
    global_recovery = method == "SCALE-QPG-LogitBR-GlobalAR"
    rng = np.random.default_rng(int(seed))
    assignment = (
        np.full(world.n_robots, world.idle_index, dtype=int)
        if initial_assignment is None
        else np.asarray(initial_assignment, dtype=int).copy()
    )
    if assignment.shape != (world.n_robots,):
        raise ValueError("initial_assignment has invalid shape")
    prior = (
        assignment.copy()
        if previous_assignment is None
        else np.asarray(previous_assignment, dtype=int).copy()
    )
    if prior.shape != assignment.shape:
        raise ValueError("previous_assignment has invalid shape")
    markets = initialize_markets(
        world,
        assignment,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
    )
    robots = [
        RobotLocalState(
            robot_id=robot,
            commitment=int(assignment[robot]),
            previous_assignment=int(prior[robot]),
        )
        for robot in range(world.n_robots)
    ]
    ledger = MessageLedger(scale_config["payload_schema"])
    for robot in robots:
        refresh_robot_sparse_state(
            world,
            markets,
            robot,
            maximum_size=L,
            gamma_switch=gamma_switch,
        )
    protocol = AtomicCommitProtocol(
        world=world,
        graph=graph,
        assignment=assignment,
        robots=robots,
        markets=markets,
        ledger=ledger,
        rho_minus=rho_minus,
        rho_plus=rho_plus,
        gamma_switch=gamma_switch,
        epsilon_improvement=epsilon,
        epsilon_price=epsilon_price,
        reservation_timeout=reservation_timeout,
        previous_assignment=prior,
    )
    traces: list[dict[str, Any]] = []
    potential_increments: list[float] = []
    strict_monotone = True
    repeated_states = 0
    cycles = 0
    seen_strict: set[str] = set()
    proposals = rejected = accepted = activations = 0
    logical_epochs = 0
    stable_epochs = 0
    converged = False
    censoring_reason = "max_epochs"
    first_atomic = 0.0
    first_feasible: float | None = (
        0.0 if evaluate_assignment(world, assignment)["feasible"] else None
    )
    first_persistent: float | None = None
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    owned_trace = not tracemalloc.is_tracing()
    if owned_trace:
        tracemalloc.start()
    baseline_peak = (
        tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    )

    def refresh(robot_id: int) -> None:
        state = robots[robot_id]
        changed = refresh_robot_sparse_state(
            world,
            markets,
            state,
            maximum_size=L,
            gamma_switch=gamma_switch,
        )
        if changed:
            route_hops = int(
                sum(
                    graph.market_route_hops[action, robot_id]
                    for action in state.active_set
                    if action < world.n_loads
                )
            )
            ledger.record(
                "active_set_update",
                route_hops=route_hops,
                activation=activations,
                robot=robot_id,
            )

    def attempt(robot_id: int, target: int, phase: str) -> bool:
        nonlocal proposals, rejected, accepted, first_feasible
        proposal = _proposal(
            world=world,
            protocol=protocol,
            robot=robot_id,
            target=target,
            activation=activations,
        )
        proposals += 1
        route_hops = _route_for_proposal(
            graph,
            world,
            robot_id,
            proposal.source_load,
            proposal.target_load,
        )
        ledger.record(
            "proposal",
            route_hops=route_hops,
            activation=activations,
            robot=robot_id,
            source=proposal.source_load,
            target=proposal.target_load,
            note=phase,
        )
        prepared = protocol.prepare(proposal, activation=activations)
        if not prepared.accepted:
            rejected += 1
            return False
        committed = protocol.commit(proposal.proposal_id, activation=activations)
        if not committed.accepted:
            rejected += 1
            return False
        accepted += 1
        potential_increments.append(float(committed.delta_phi))
        if phase == "strict" and committed.delta_phi <= epsilon:
            strict_monotone = False
        if (
            first_feasible is None
            and evaluate_assignment(world, assignment)["feasible"]
        ):
            first_feasible = float(time.perf_counter() - started_wall)
        return True

    # Logit warm-up is counted in activations, not synchronous rounds.
    for explore_index in range(explore_activations):
        if time.perf_counter() - started_wall >= maximum_wall:
            censoring_reason = "wall_time"
            break
        if proposals >= maximum_proposals:
            censoring_reason = "proposal_budget"
            break
        robot_id = int(rng.integers(0, world.n_robots))
        activations += 1
        protocol.expire(activation=activations)
        refresh(robot_id)
        actions = robots[robot_id].active_set
        deltas = np.asarray(
            [
                exact_move_delta(
                    world,
                    assignment,
                    robot_id,
                    action,
                    rho_minus=rho_minus,
                    rho_plus=rho_plus,
                    gamma_switch=gamma_switch,
                    previous_assignment=prior,
                )
                for action in actions
            ],
            dtype=float,
        )
        temperature = max(
            temperature_minimum,
            temperature_initial * anneal**explore_index,
        )
        finite = np.isfinite(deltas)
        shifted = np.full(deltas.shape, -np.inf, dtype=float)
        shifted[finite] = deltas[finite] - float(np.max(deltas[finite]))
        weights = np.zeros_like(deltas)
        weights[finite] = np.exp(
            np.clip(shifted[finite] / max(temperature, 1.0e-12), -745.0, 0.0)
        )
        weights /= max(float(np.sum(weights)), 1.0e-300)
        robots[robot_id].intention = {
            action: float(probability)
            for action, probability in zip(actions, weights, strict=True)
        }
        target = int(rng.choice(np.asarray(actions, dtype=int), p=weights))
        if target != int(assignment[robot_id]):
            attempt(robot_id, target, "logit")
    else:
        censoring_reason = "max_epochs"

    # Strict asynchronous best response.
    if censoring_reason not in {"wall_time", "proposal_budget"}:
        for epoch in range(maximum_epochs):
            if time.perf_counter() - started_wall >= maximum_wall:
                censoring_reason = "wall_time"
                break
            moves_this_epoch = 0
            version_before = tuple(market.version for market in markets)
            for robot_id in map(int, rng.permutation(world.n_robots)):
                if time.perf_counter() - started_wall >= maximum_wall:
                    censoring_reason = "wall_time"
                    break
                if proposals >= maximum_proposals:
                    censoring_reason = "proposal_budget"
                    break
                activations += 1
                protocol.expire(activation=activations)
                refresh(robot_id)
                source = int(assignment[robot_id])
                candidates: list[tuple[float, int]] = []
                for target in robots[robot_id].active_set:
                    if target == source:
                        continue
                    delta = exact_move_delta(
                        world,
                        assignment,
                        robot_id,
                        int(target),
                        rho_minus=rho_minus,
                        rho_plus=rho_plus,
                        gamma_switch=gamma_switch,
                        previous_assignment=prior,
                    )
                    if np.isfinite(delta):
                        candidates.append((float(delta), int(target)))
                candidates.sort(key=lambda item: (-item[0], item[1]))
                if candidates and candidates[0][0] > epsilon:
                    if attempt(robot_id, candidates[0][1], "strict"):
                        moves_this_epoch += 1
                        state_hash = stable_hash(assignment)
                        if state_hash in seen_strict:
                            repeated_states += 1
                            cycles += 1
                        seen_strict.add(state_hash)
            logical_epochs = epoch + 1
            metrics = evaluate_assignment(world, assignment)
            potential = atomic_potential(
                world,
                assignment,
                rho_minus=rho_minus,
                rho_plus=rho_plus,
                gamma_switch=gamma_switch,
                previous_assignment=prior,
            )
            traces.append(
                {
                    "phase": "strict",
                    "logical_epoch": logical_epochs,
                    "activations": activations,
                    "accepted_moves": moves_this_epoch,
                    "potential": potential,
                    "feasible": bool(metrics["feasible"]),
                    "deficit_total": float(metrics["deficit_total"]),
                    "excess_upper_total": float(metrics["excess_upper_total"]),
                    "packets_total": ledger.totals()["packets"],
                    "payload_bytes_total": ledger.totals()["payload"],
                    "versions_stable": bool(
                        version_before == tuple(market.version for market in markets)
                    ),
                }
            )
            versions_stable = version_before == tuple(
                market.version for market in markets
            )
            if moves_this_epoch == 0 and versions_stable:
                stable_epochs += 1
            else:
                stable_epochs = 0
            if stable_epochs >= stable_required:
                converged = True
                censoring_reason = "none"
                if metrics["feasible"] and first_persistent is None:
                    first_persistent = float(time.perf_counter() - started_wall)
                break
            if censoring_reason in {"wall_time", "proposal_budget"}:
                break

    assignment_before = assignment.copy()
    before_metrics = evaluate_assignment(
        world,
        assignment_before,
        previous_assignment=prior,
    )
    capacities = capacities_by_load(
        assignment_before,
        world.capacities,
        world.n_loads,
    )
    residual_loads = set(
        map(
            int,
            np.flatnonzero(
                (capacities < world.lower_quotas - 1.0e-9)
                | (capacities > world.upper_quotas + 1.0e-9)
            ),
        )
    )
    if affected_loads is not None:
        residual_loads.update(map(int, affected_loads))
    if before_metrics["feasible"]:
        recovery = _empty_recovery(
            world,
            assignment_before,
            global_scope=global_recovery,
        )
    else:
        recovery = run_local_recovery(
            world,
            assignment_before,
            [robot.active_set for robot in robots],
            scale_config["local_recovery"],
            affected_loads=sorted(residual_loads),
            radius=int(parameters["h"]),
            maximum_chain_length=int(parameters["H"]),
            previous_assignment=prior,
            global_scope=global_recovery,
        )
        route_hops = max(
            1,
            int(
                sum(
                    graph.market_route_hops[load, robot]
                    for load in recovery.universe.loads
                    for robot in recovery.universe.robots
                    if world.compatibility[robot, load]
                )
            ),
        )
        ledger.record(
            "recovery",
            route_hops=route_hops,
            activation=activations,
            note="global" if global_recovery else "local",
        )
    final_assignment = recovery.recovery.assignment.copy()
    final_metrics = evaluate_assignment(
        world,
        final_assignment,
        previous_assignment=prior,
    )
    if first_feasible is None and final_metrics["feasible"]:
        first_feasible = float(time.perf_counter() - started_wall)
    if first_persistent is None and final_metrics["feasible"]:
        first_persistent = float(time.perf_counter() - started_wall)
    termination = float(time.perf_counter() - started_wall)
    cpu = float(time.process_time() - started_cpu)
    peak = (
        tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
    )
    if owned_trace:
        tracemalloc.stop()
    totals = ledger.totals()
    active_sizes = [len(robot.active_set) for robot in robots]
    if not all(robot.validate_sparse(L, world.n_loads) for robot in robots):
        raise RuntimeError("robot state violated sparse-state invariant")
    return ScaleRunResult(
        method=method,
        assignment_before_recovery=assignment_before,
        assignment=final_assignment,
        feasible_before_recovery=bool(before_metrics["feasible"]),
        feasible=bool(final_metrics["feasible"]),
        converged=converged,
        censored=not converged,
        censoring_reason=censoring_reason,
        logical_epochs=logical_epochs,
        activations=activations,
        proposals=proposals,
        rejected_proposals=rejected,
        accepted_moves=accepted,
        version_conflicts=protocol.version_conflicts,
        rollbacks=protocol.rollbacks,
        potential_increments=tuple(potential_increments),
        strict_potential_monotone=bool(strict_monotone),
        repeated_states=repeated_states,
        cycles_detected=cycles,
        packets_total=totals["packets"],
        scalar_transmissions_total=totals["scalars"],
        payload_bytes_total=totals["payload"],
        indices_bytes_total=totals["indices"],
        versions_bytes_total=totals["versions"],
        reservation_bytes_total=totals["reservation"],
        recovery_bytes_total=totals["recovery"],
        first_atomic_assignment_time_s=first_atomic,
        first_feasible_time_s=first_feasible,
        first_persistent_feasible_time_s=first_persistent,
        final_termination_time_s=termination,
        wall_time_s=termination,
        cpu_time_s=cpu,
        peak_memory_mb=float(max(0, peak - baseline_peak) / (1024.0**2)),
        maximum_active_set_size=max(active_sizes, default=0),
        mean_active_set_size=float(np.mean(active_sizes)) if active_sizes else 0.0,
        recovery=recovery,
        recourse_hamming=int(np.sum(final_assignment != prior)),
        traces=tuple(traces),
        message_rows=tuple(ledger.rows),
    )


def all_world_cost(world: QuotaWorld, assignment: np.ndarray) -> float:
    """Selection-unbiased penalized cost declared by the protocol."""

    metrics = evaluate_assignment(world, assignment)
    if metrics["feasible"]:
        return float(metrics["distance_total_m"])
    capacity_cap = world.n_robots * float(np.max(world.distances_m))
    lower_denominator = max(float(np.sum(world.lower_quotas)), 1.0e-12)
    upper_denominator = max(float(np.sum(world.upper_quotas)), 1.0e-12)
    violation = (
        float(metrics["deficit_total"]) / lower_denominator
        + float(metrics["excess_upper_total"]) / upper_denominator
    )
    return float(capacity_cap * (1.0 + violation))


def random_seed_assignment(world: QuotaWorld, seed: int) -> np.ndarray:
    rng = np.random.default_rng(int(seed))
    assignment = np.empty(world.n_robots, dtype=int)
    for robot in range(world.n_robots):
        actions = np.r_[
            np.flatnonzero(world.compatibility[robot]),
            world.idle_index,
        ].astype(int)
        assignment[robot] = int(rng.choice(actions))
    return assignment


def nearest_compatible_seed(world: QuotaWorld) -> np.ndarray:
    """Distance-ordered atomic seed that never exceeds upper quotas."""

    assignment = np.full(world.n_robots, world.idle_index, dtype=int)
    capacity = np.zeros(world.n_loads, dtype=float)
    candidates = [
        (
            float(world.distances_m[robot, load]),
            robot,
            load,
        )
        for robot in range(world.n_robots)
        for load in np.flatnonzero(world.compatibility[robot])
    ]
    candidates.sort()
    used: set[int] = set()
    for _, robot, load in candidates:
        if robot in used:
            continue
        if (
            capacity[load] + world.capacities[robot]
            > world.upper_quotas[load] + 1.0e-9
        ):
            continue
        assignment[robot] = load
        capacity[load] += world.capacities[robot]
        used.add(robot)
    return assignment


def greedy_deficit_seed(world: QuotaWorld) -> np.ndarray:
    """Greedy marginal deficit reduction with deterministic tie-breaking."""

    assignment = np.full(world.n_robots, world.idle_index, dtype=int)
    capacity = np.zeros(world.n_loads, dtype=float)
    unused = set(range(world.n_robots))
    while unused:
        candidates: list[tuple[float, float, int, int]] = []
        for robot in unused:
            for load in np.flatnonzero(world.compatibility[robot]):
                if (
                    capacity[load] + world.capacities[robot]
                    > world.upper_quotas[load] + 1.0e-9
                ):
                    continue
                before = max(0.0, world.lower_quotas[load] - capacity[load])
                after = max(
                    0.0,
                    world.lower_quotas[load]
                    - capacity[load]
                    - world.capacities[robot],
                )
                reduction = before - after
                candidates.append(
                    (
                        -float(reduction),
                        float(world.normalized_costs[robot, load]),
                        robot,
                        int(load),
                    )
                )
        if not candidates:
            break
        candidates.sort()
        negative_reduction, _, robot, load = candidates[0]
        if negative_reduction >= -1.0e-12:
            break
        assignment[robot] = load
        capacity[load] += world.capacities[robot]
        unused.remove(robot)
        if np.all(capacity >= world.lower_quotas - 1.0e-9):
            break
    return assignment
