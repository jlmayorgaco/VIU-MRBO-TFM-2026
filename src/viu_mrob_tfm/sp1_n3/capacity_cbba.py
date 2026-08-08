"""Capacity-CBBA adaptation: multi-winner, deficit-driven, neighbour consensus.

This is an *adaptation*, never canonical CBBA. Loads in N2 need several robots
and a quantitative capacity, so the bundle is unitary, a load admits several
winners, and the bid is the marginal reduction of the load's residual deficit.
None of CBBA's published guarantees survive those changes: no ``N*D`` round
bound, no diminishing-marginal-gain argument, no conflict-resolution
optimality. Termination is therefore reported as an observed property under a
declared round budget, never as a theorem.

What the algorithm does each round:

1. merge the bid records that arrived, accepting a record about robot ``j``
   only when its version strictly advances what was already known;
2. estimate, for every load, who is committed to it and what deficit is left;
3. release its own commitment if it has fallen out of the load's greedy
   capacity prefix, otherwise keep it;
4. bid on the load where its own capacity removes the most deficit;
5. send to each neighbour only the records whose version advanced since the
   last transmission to that neighbour.

Bid, frozen here:

    r_ik  = [ m_k - sum_{j in Chat_ik, j != i} c_j ]_+        local estimate
    dD_ik = min(c_i, r_ik)
    b_ik  = ( dD_ik, -d_ik, -token_i )                        lexicographic

Larger useful capacity first; at equal usefulness the closer robot; ties broken
by an intrinsic token that travels with the robot, so permuting the storage
order cannot change who wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from .certificate import TOLERANCE
from .contract import Outgoing, RobotView, StepResult
from .messages import (
    KIND_CBBA_TABLE,
    BidRecord,
    decode_cbba_table,
    encode_cbba_table,
)


@dataclass
class CbbaState:
    """Private state of one robot. Nothing here is shared implicitly."""

    table: dict[int, BidRecord] = field(default_factory=dict)
    # Named for what it is: the last version *transmitted* to each neighbour.
    # Nothing acknowledges it, so it is refreshed periodically -- see step().
    sent: dict[int, dict[int, int]] = field(default_factory=dict)
    # Highest bid at which this robot was displaced from each load. It may
    # only return with a strictly better bid, which is what makes the process
    # finite: the barrier never decreases and the bid space is finite.
    barrier: dict[int, tuple[float, float, int]] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CbbaState):
            return NotImplemented
        return self.table == other.table and self.barrier == other.barrier


def _initial(view: RobotView) -> CbbaState:
    record = BidRecord(
        robot=view.robot_id,
        target=-1,
        capacity=float(view.capacity),
        delta_deficit=0.0,
        neg_distance=0.0,
        token=int(view.priority_token),
        version=0,
    )
    return CbbaState(table={view.robot_id: record}, sent={}, barrier={})


def heartbeat_period(n_robots: int) -> int:
    """How often the full table is retransmitted to every neighbour."""

    return max(int(n_robots), 4)


def _members(table: dict[int, BidRecord], load: int) -> list[BidRecord]:
    return [record for record in table.values() if record.target == load]


def _greedy_prefix(members: list[BidRecord], demand: float) -> set[int]:
    """Who a load actually needs, in bid order, until its demand is covered.

    Everyone past that point is redundant: with ``d_ik > 0`` a redundant robot
    always lowers the objective by leaving, and it is the mechanism that keeps
    over-coverage from freezing.
    """

    accumulated = 0.0
    keep: set[int] = set()
    for record in sorted(members, key=lambda item: item.key, reverse=True):
        if accumulated >= demand - TOLERANCE:
            break
        keep.add(record.robot)
        accumulated += record.capacity
    return keep


def _best_bid(
    view: RobotView,
    table: dict[int, BidRecord],
    barrier: dict[int, tuple[float, float, int]],
) -> tuple[int, float, float]:
    """Pick the load where this robot's capacity removes the most deficit.

    A load this robot was displaced from is only reconsidered at a strictly
    better bid than the one it lost with. Without that barrier the release and
    re-bid loop has nothing monotone in it and the process cycles forever --
    the pilot measured exactly that.
    """

    demands = view.catalog.demands
    best_target = -1
    best_key: tuple[float, float, int] | None = None
    best_delta = 0.0
    for load in range(view.n_loads):
        committed = sum(
            record.capacity
            for record in _members(table, load)
            if record.robot != view.robot_id
        )
        residual = max(float(demands[load]) - committed, 0.0)
        if residual <= TOLERANCE:
            continue
        delta = min(float(view.capacity), residual)
        key = (delta, -float(view.distances[load]), -int(view.priority_token))
        lost_at = barrier.get(load)
        if lost_at is not None and key <= lost_at:
            continue
        if best_key is None or key > best_key:
            best_key = key
            best_target = load
            best_delta = delta
    return best_target, best_delta, (
        -float(view.distances[best_target]) if best_target >= 0 else 0.0
    )


def step(view: RobotView) -> StepResult:
    state: CbbaState = view.state
    table = dict(state.table)
    sent = {key: dict(value) for key, value in state.sent.items()}
    barrier = dict(state.barrier)

    # Periodic full refresh. Diffs alone assume every transmission arrives: a
    # dropped record is marked as sent and never retransmitted, so a neighbour
    # can stay permanently stale. Clearing the ledger every N rounds bounds how
    # long a lost record can go unrepaired.
    if view.n_robots and view.round_index % heartbeat_period(view.n_robots) == 0:
        sent = {}

    # 1. Merge arrivals. A record about j is accepted only when its version
    #    strictly advances; stale relays are dropped rather than reapplied.
    for message in view.inbox:
        if message.kind != KIND_CBBA_TABLE:
            continue
        for record in decode_cbba_table(message.payload):
            if record.robot == view.robot_id:
                continue  # a robot is the sole authority on its own commitment
            known = table.get(record.robot)
            if known is None or record.version > known.version:
                table[record.robot] = record

    # 2-4. Recompute this robot's own commitment.
    mine = table[view.robot_id]
    target = mine.target
    delta = mine.delta_deficit
    neg_distance = mine.neg_distance
    if target >= 0:
        demand = float(view.catalog.demands[target])
        if view.robot_id not in _greedy_prefix(_members(table, target), demand):
            # Displaced. Remember the bid that lost, so returning requires a
            # strictly better one.
            previous = barrier.get(target)
            lost_with = mine.key
            barrier[target] = lost_with if previous is None else max(previous, lost_with)
            target = -1

    if target < 0:
        target, delta, neg_distance = _best_bid(view, table, barrier)
    # A committed bid is *not* recomputed while the commitment holds. Letting
    # it float with the estimated residual is what let the prefix reorder
    # without anyone new bidding, which is the other half of the cycle.

    changed = (
        target != mine.target
        or abs(delta - mine.delta_deficit) > TOLERANCE
        or abs(neg_distance - mine.neg_distance) > TOLERANCE
    )
    if changed:
        mine = replace(
            mine,
            target=int(target),
            delta_deficit=float(delta),
            neg_distance=float(neg_distance),
            version=mine.version + 1,
        )
        table[view.robot_id] = mine

    # 5. Send each neighbour only what it has not already been told.
    outgoing: list[Outgoing] = []
    for neighbour in view.neighbours:
        seen = sent.setdefault(neighbour, {})
        fresh = tuple(
            record
            for robot, record in sorted(table.items())
            if seen.get(robot, -1) < record.version
        )
        if not fresh:
            continue
        outgoing.append(
            Outgoing(
                recipient=neighbour,
                kind=KIND_CBBA_TABLE,
                payload=encode_cbba_table(fresh),
            )
        )
        for record in fresh:
            seen[record.robot] = record.version

    return StepResult(
        state=CbbaState(table=table, sent=sent, barrier=barrier),
        outgoing=tuple(outgoing),
        # No distributed termination protocol exists for this adaptation, so
        # the robot never claims convergence. The observer reports quiescence.
        terminated=False,
    )


def initial_state(view: RobotView) -> CbbaState:
    return _initial(view)


def extract_assignment(states: list[CbbaState], n_robots: int) -> np.ndarray:
    """Each robot's own final commitment. No robot speaks for another."""

    assignment = np.full(n_robots, -1, dtype=int)
    for robot in range(n_robots):
        record = states[robot].table.get(robot)
        if record is not None:
            assignment[robot] = int(record.target)
    return assignment


__all__ = [
    "CbbaState",
    "extract_assignment",
    "initial_state",
    "make_step",
    "step",
]


def commitment_signature(states: list[CbbaState]) -> tuple[int, ...]:
    """The vector of self-declared commitments, for the observer's cycle check."""

    return tuple(
        int(state.table[robot].target) if robot in state.table else -1
        for robot, state in enumerate(states)
    )
