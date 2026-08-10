"""Weighted-GRAPE and Weighted-Pair-GRAPE over a distributed serial selection.

The naive distributed GRAPE -- every robot applies its own best deviation as
soon as it finds one -- does *not* inherit the potential argument. Two moves
that each improve the potential against a stale view can jointly worsen it:
two robots covering the same residual deficit both believe they remove it, and
only one of them does. The finite-improvement proof needs each applied
transition to strictly improve the *global* potential.

This module therefore takes option A of the review: an epoch structure in which
exactly one improvement is applied per epoch, selected by max-consensus over
neighbour links.

    round 0                 handshake: each robot sends its capacity and its
                            own distance row to its neighbours
    epoch e, local round 0  every robot computes its best improving deviation
                            against the current profile and floods it
    local rounds 1..H-2     merge arrivals, keep the lexicographic maximum,
                            forward it when it changed
    local round H-1         merge, then apply the single winning proposal

``H = max(N, 2)`` gives ``N-1`` forwarding rounds, and the diameter of any
connected graph on ``N`` nodes is at most ``N-1``, so every robot ends the
epoch holding the same winner. ``N`` is a public constant; the actual diameter
is never read, which is what the inherited implementation got wrong.

Because the profile is globally consistent at the start of every epoch and
exactly one strictly lexicographically improving move is applied, the pair
``(D, J)`` decreases strictly each epoch. The profile space is finite, so the
run terminates -- and when the flooded winner is "no move", every robot knows
it simultaneously, which is a genuine distributed termination certificate. That
is the only case in this package allowed to report CONVERGED.

Improvement is lexicographic, with no tuned weights:

    y' improves y  <=>  D(y') < D(y),  or  D(y') == D(y) and J(y') < J(y)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .certificate import TOLERANCE
from .contract import Outgoing, RobotView, StepResult
from .messages import (
    KIND_GRAPE_PROPOSAL,
    KIND_NEIGHBOUR_PROFILE,
    Proposal,
    canonical_proposal,
    decode_neighbour_profile,
    decode_proposal,
    encode_neighbour_profile,
    encode_proposal,
)


IDLE = -1

# Retries per distinct proposal, per neighbour, within an epoch.
REPEAT_LIMIT = 4


@dataclass
class GrapeState:
    """Private state. ``coverage`` and ``actions`` are reconstructed, not given.

    Both are built only from messages this robot received and paid for: the
    handshake, and the winning proposal of every epoch, which carries the
    movers' capacities precisely so the update can be applied locally.
    """

    coverage: np.ndarray
    actions: np.ndarray
    neighbour_capacity: dict[int, float] = field(default_factory=dict)
    neighbour_token: dict[int, int] = field(default_factory=dict)
    neighbour_distances: dict[int, np.ndarray] = field(default_factory=dict)
    best: Proposal | None = None
    last_sent: dict[int, tuple[tuple, int]] = field(default_factory=dict)
    epoch: int = 0
    done: bool = False
    # 0 = unilateral deviations only, 1 = joint deviations enabled.
    phase: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GrapeState):
            return NotImplemented
        return (
            np.array_equal(self.actions, other.actions)
            and self.epoch == other.epoch
            and self.done == other.done
            and self.phase == other.phase
        )


def initial_state(view: RobotView) -> GrapeState:
    return GrapeState(
        coverage=np.zeros(view.n_loads, dtype=float),
        actions=np.full(view.n_robots, IDLE, dtype=int),
    )


def epoch_length(n_robots: int) -> int:
    return max(int(n_robots), 2)


# ------------------------------------------------------------------ scoring
def _deficit(coverage: np.ndarray, demands: np.ndarray) -> float:
    return float(np.maximum(demands - coverage, 0.0).sum())


def _evaluate(
    coverage: np.ndarray,
    demands: np.ndarray,
    moves: tuple[tuple[int, int, float], ...],
    distance_terms: float,
) -> tuple[float, float]:
    """Return ``(deficit_gain, distance_gain)`` of a joint deviation.

    ``moves`` is ``(old_action, new_action, capacity)`` per mover, applied to a
    copy of the coverage vector. ``distance_terms`` is the already-computed
    ``J_old - J_new`` for the movers, which only needs each mover's own row.
    """

    candidate = coverage.copy()
    for old, new, capacity in moves:
        if old >= 0:
            candidate[old] -= capacity
        if new >= 0:
            candidate[new] += capacity
    return _deficit(coverage, demands) - _deficit(candidate, demands), distance_terms


def _improves(deficit_gain: float, distance_gain: float) -> bool:
    if deficit_gain > TOLERANCE:
        return True
    if deficit_gain < -TOLERANCE:
        return False
    return distance_gain > TOLERANCE


def _own_best(view: RobotView, state: GrapeState, *, pair_moves: bool) -> Proposal | None:
    """Best improving deviation this robot can propose.

    Unilateral moves cover idle -> load, load -> idle and load -> load. Pair
    moves are general joint deviations with a neighbour, so they also cover
    "recruit an idle robot while I leave", "both move to different loads" and
    a plain swap -- not only the slot exchange the inherited implementation
    allowed, which could never recruit an idle robot at all.
    """

    demands = view.catalog.demands
    coverage = state.coverage
    me = view.robot_id
    mine = int(state.actions[me])
    my_capacity = float(view.capacity)
    options = [IDLE, *range(view.n_loads)]

    best: Proposal | None = None
    best_local: tuple[float, float, int, int] | None = None

    def consider(
        moves: tuple[tuple[int, int, float], ...],
        distance_gain: float,
        robot_a: int,
        action_a: int,
        capacity_a: float,
        robot_b: int,
        action_b: int,
        capacity_b: float,
        partner_token: int,
    ) -> None:
        nonlocal best, best_local
        deficit_gain, distance_gain_ = _evaluate(
            coverage, demands, moves, distance_gain
        )
        if not _improves(deficit_gain, distance_gain_):
            return
        # Ranked locally on intrinsic attributes only. Two joint deviations
        # with identical gains are separated by the partner's token, never by
        # the neighbour's storage index.
        local_key = (deficit_gain, distance_gain_, -partner_token, action_a)
        if best_local is not None and local_key <= best_local:
            return
        best_local = local_key
        # Canonicalised now, so this robot ranks its own proposal on exactly
        # the bits its neighbours will see.
        best = canonical_proposal(
            Proposal(
                has_move=True,
                epoch=state.epoch,
                deficit_gain=deficit_gain,
                distance_gain=distance_gain_,
                token=int(view.priority_token),
                robot_a=robot_a,
                action_a=action_a,
                capacity_a=capacity_a,
                robot_b=robot_b,
                action_b=action_b,
                capacity_b=capacity_b,
            )
        )

    my_distance = view.distances
    for target in options:
        if target == mine:
            continue
        gain = _distance_term(my_distance, mine) - _distance_term(my_distance, target)
        consider(
            ((mine, target, my_capacity),),
            gain,
            me,
            target,
            my_capacity,
            me,
            target,
            my_capacity,
            int(view.priority_token),
        )

    if not pair_moves:
        return best

    for other in view.neighbours:
        capacity_other = state.neighbour_capacity.get(other)
        distance_other = state.neighbour_distances.get(other)
        token_other = state.neighbour_token.get(other)
        if capacity_other is None or distance_other is None or token_other is None:
            continue  # handshake not yet delivered; nothing is assumed
        theirs = int(state.actions[other])
        for mine_new in options:
            for other_new in options:
                if mine_new == mine and other_new == theirs:
                    continue
                gain = (
                    _distance_term(my_distance, mine)
                    - _distance_term(my_distance, mine_new)
                    + _distance_term(distance_other, theirs)
                    - _distance_term(distance_other, other_new)
                )
                consider(
                    (
                        (mine, mine_new, my_capacity),
                        (theirs, other_new, float(capacity_other)),
                    ),
                    gain,
                    me,
                    mine_new,
                    my_capacity,
                    other,
                    other_new,
                    float(capacity_other),
                    int(token_other),
                )
    return best


def _distance_term(distances: np.ndarray, action: int) -> float:
    return float(distances[action]) if action >= 0 else 0.0


def _apply(state: GrapeState, proposal: Proposal) -> None:
    """Apply the epoch's winner. Every robot runs this on the same input."""

    movers = [(proposal.robot_a, proposal.action_a, proposal.capacity_a)]
    if proposal.robot_b != proposal.robot_a:
        movers.append((proposal.robot_b, proposal.action_b, proposal.capacity_b))
    for robot, action, capacity in movers:
        old = int(state.actions[robot])
        if old >= 0:
            state.coverage[old] -= capacity
        if action >= 0:
            state.coverage[action] += capacity
        state.actions[robot] = action


# --------------------------------------------------------------------- step
def make_step(*, pair_moves: bool):
    """Return the round function for Weighted-GRAPE or Weighted-Pair-GRAPE."""

    def step(view: RobotView) -> StepResult:
        state: GrapeState = view.state
        following = GrapeState(
            coverage=state.coverage.copy(),
            actions=state.actions.copy(),
            neighbour_capacity=dict(state.neighbour_capacity),
            neighbour_token=dict(state.neighbour_token),
            neighbour_distances=dict(state.neighbour_distances),
            best=state.best,
            last_sent=dict(state.last_sent),
            epoch=state.epoch,
            done=state.done,
            phase=state.phase,
        )
        if following.done:
            return StepResult(state=following, outgoing=(), terminated=True)

        for message in view.inbox:
            if message.kind == KIND_NEIGHBOUR_PROFILE:
                capacity, token, distances = decode_neighbour_profile(message.payload)
                following.neighbour_capacity[message.sender] = capacity
                following.neighbour_token[message.sender] = token
                following.neighbour_distances[message.sender] = distances
            elif message.kind == KIND_GRAPE_PROPOSAL:
                arrived = decode_proposal(message.payload)
                if not arrived.has_move:
                    continue
                if following.best is None or arrived.order_key > following.best.order_key:
                    following.best = arrived

        # Round 0 is the handshake: neighbours exchange what a joint deviation
        # needs, and nothing else.
        if view.round_index == 0:
            payload = encode_neighbour_profile(
                view.capacity, view.priority_token, view.distances
            )
            return StepResult(
                state=following,
                outgoing=tuple(
                    Outgoing(recipient=neighbour, kind=KIND_NEIGHBOUR_PROFILE, payload=payload)
                    for neighbour in view.neighbours
                ),
                terminated=False,
            )

        horizon = epoch_length(view.n_robots)
        local = (view.round_index - 1) % horizon

        if local == 0:
            # Pair moves only after the unilateral equilibrium is reached, so
            # Pair-GRAPE refines Weighted-GRAPE instead of running a different
            # search from the same start. That makes
            # (D,J)_pair <=_lex (D,J)_grape true by construction rather than a
            # hope, and it is why the pair variant is a sensitivity and not an
            # independent third baseline.
            following.best = _own_best(
                view, following, pair_moves=following.phase == 1
            )
            following.last_sent = {}

        if local == horizon - 1:
            winner = following.best
            if winner is None or not winner.has_move:
                if pair_moves and following.phase == 0:
                    # Unilateral equilibrium reached. Every robot learns it in
                    # the same round from the same flooded "no move", so they
                    # all switch together and the shared profile stays shared.
                    following.phase = 1
                    following.best = None
                    following.last_sent = {}
                    return StepResult(
                        state=following, outgoing=(), terminated=False
                    )
                following.done = True
                return StepResult(state=following, outgoing=(), terminated=True)
            _apply(following, winner)
            following.epoch += 1
            following.best = None
            following.last_sent = {}
            return StepResult(state=following, outgoing=(), terminated=False)

        # Each distinct proposal is repeated to a neighbour up to
        # ``REPEAT_LIMIT`` times, not sent once. Sending only on change is
        # enough under reliable delivery and silently wrong under loss: a
        # dropped proposal is never retransmitted, the flood stops short, and
        # robots end the epoch applying different moves. Repeating every round
        # instead would fix that too but costs ~34x the bytes for redundancy
        # the epoch does not need, since the flood only has to cross the
        # diameter and the epoch is N-1 rounds long. A few retries per hop cut
        # the failure probability geometrically; whatever still slips through
        # is caught by the divergence invariant rather than assumed away.
        outgoing: list[Outgoing] = []
        if following.best is not None and following.best.has_move:
            key = following.best.order_key
            payload = encode_proposal(following.best)
            for neighbour in view.neighbours:
                previous, attempts = following.last_sent.get(neighbour) or (None, 0)
                if previous == key and attempts >= REPEAT_LIMIT:
                    continue
                outgoing.append(
                    Outgoing(
                        recipient=neighbour,
                        kind=KIND_GRAPE_PROPOSAL,
                        payload=payload,
                    )
                )
                following.last_sent[neighbour] = (
                    key,
                    attempts + 1 if previous == key else 1,
                )
        return StepResult(state=following, outgoing=tuple(outgoing), terminated=False)

    return step


def extract_assignment(states: list[GrapeState], n_robots: int) -> np.ndarray:
    """Each robot reports its own action from its own copy of the profile."""

    assignment = np.full(n_robots, IDLE, dtype=int)
    for robot in range(n_robots):
        assignment[robot] = int(states[robot].actions[robot])
    return assignment


__all__ = [
    "GrapeState",
    "IDLE",
    "epoch_length",
    "extract_assignment",
    "initial_state",
    "make_step",
]


def profile_signature(states: list[GrapeState]) -> tuple[int, ...]:
    """Each robot's own action, plus the protocol phase, for the cycle check.

    The phase belongs in the signature because Pair-GRAPE crosses from
    unilateral to joint deviations without moving anyone: the profile at the
    end of phase 0 is the profile at the start of phase 1. Without the phase
    the observer sees that unchanged profile as a revisit and flags a cycle
    that never happened -- which it did, on every Pair-GRAPE run, with a
    reported period of exactly one epoch.
    """

    phase = int(states[0].phase) if states else 0
    return (phase, *(int(state.actions[robot]) for robot, state in enumerate(states)))


def profiles_agree(states: list[GrapeState]) -> bool:
    """Do all robots hold the same profile?

    The epoch argument assumes every robot ends the epoch with the same
    winner, which holds only if the flood actually reached everyone. Retries
    make that overwhelmingly likely but cannot guarantee it: exact agreement
    over links that may drop messages is the coordinated-attack problem, and
    it has no solution. So the property is checked rather than assumed, and a
    run that violates it is reported as DIVERGED instead of CONVERGED.
    """

    if not states:
        return True
    reference = states[0].actions
    return all(np.array_equal(state.actions, reference) for state in states[1:])
