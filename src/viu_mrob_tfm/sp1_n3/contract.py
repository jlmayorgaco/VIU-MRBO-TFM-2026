"""The N3 information contract and its synchronous execution engine.

N3 keeps the frozen N2 problem and removes only the coordinator. What a robot
may look at is therefore not a convention to be checked by reading the code --
that is exactly the failure mode that let ``sp1_geo`` compute a global argmax
and bill it as consensus. Here the step function is a pure function of
:class:`RobotView`, and a view carries nothing global: the robot's own private
state, its own inbox, the announced load catalog, and the public constants.
Anything else is unreachable rather than merely discouraged.

Round semantics, fixed for the nominal campaign:

* rounds are synchronous, ``t = 0, 1, ..., max_rounds - 1``;
* at round ``t`` a robot sees only messages *delivered* by ``t``;
* a message emitted at ``t`` can never influence another robot before ``t+1``;
* the observer records the global system but never decides, stops or repairs.

Public constants (``n_robots``, ``n_loads``, ``max_rounds``) are exposed because
they carry no robot's private attribute. The graph diameter, its algebraic
connectivity and the number of remaining rounds are *not* exposed: they are
global properties of the fleet, and reading them is what invalidated the
inherited CBBA implementation.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np


ENVELOPE = struct.Struct("<BHHH")  # kind, sender, round, payload length
ENVELOPE_BYTES = ENVELOPE.size


# --------------------------------------------------------------------- status
CONVERGED = "CONVERGED"
QUIESCENT_OBSERVED = "QUIESCENT_OBSERVED"
MAX_ROUNDS = "MAX_ROUNDS"
TIME_LIMIT = "TIME_LIMIT"
CYCLE_OBSERVED = "CYCLE_OBSERVED"
DIVERGED = "DIVERGED"
ERROR = "ERROR"

ALGORITHM_STATUS = (
    CONVERGED,
    QUIESCENT_OBSERVED,
    MAX_ROUNDS,
    TIME_LIMIT,
    CYCLE_OBSERVED,
    DIVERGED,
    ERROR,
)


# ----------------------------------------------------------------- catalogue
@dataclass(frozen=True, slots=True)
class LoadCatalog:
    """The immutable catalogue announced to every robot at ``t = 0``.

    Loads are a common input in N3, so this is not "fully local perception".
    Propagating the catalogue over the graph as well is a later sensitivity,
    deliberately kept out of the primary contract.
    """

    positions: np.ndarray  # (K, 2)
    demands: np.ndarray  # (K,)

    def __post_init__(self) -> None:
        positions = np.asarray(self.positions, dtype=float)
        demands = np.asarray(self.demands, dtype=float)
        if positions.ndim != 2 or positions.shape[1] != 2:
            raise ValueError("catalog positions must have shape (K, 2)")
        if demands.shape != (len(positions),):
            raise ValueError("one demand per load is required")
        object.__setattr__(self, "positions", positions)
        object.__setattr__(self, "demands", demands)

    @property
    def n_loads(self) -> int:
        return len(self.demands)


# ------------------------------------------------------------------ messages
@dataclass(frozen=True, slots=True)
class Outgoing:
    """One unicast transmission a robot asks the engine to send."""

    recipient: int
    kind: int
    payload: bytes


@dataclass(frozen=True, slots=True)
class Message:
    """A delivered transmission, exactly as the recipient sees it."""

    sender: int
    kind: int
    round_sent: int
    payload: bytes

    @property
    def nbytes(self) -> int:
        return ENVELOPE_BYTES + len(self.payload)


def wire_size(payload: bytes) -> int:
    """Serialized size of one unicast transmission, envelope included."""

    return ENVELOPE_BYTES + len(payload)


# ---------------------------------------------------------------------- view
@dataclass(frozen=True, slots=True)
class RobotView:
    """Everything a robot is allowed to look at during one round.

    Deliberately minimal. ``distances`` is the robot's own row of the N2 cost
    matrix -- its distance to each announced load -- which it can compute from
    its own position and the catalogue, so exposing it adds nothing global.
    """

    robot_id: int
    capacity: float
    position: np.ndarray  # (2,)
    distances: np.ndarray  # (K,) own row only
    priority_token: int
    neighbours: tuple[int, ...]  # own edge list only, never anyone else's
    catalog: LoadCatalog
    inbox: tuple[Message, ...]
    round_index: int
    n_robots: int
    n_loads: int
    max_rounds: int
    state: Any


@dataclass(frozen=True, slots=True)
class StepResult:
    """What a robot returns: its next private state and its transmissions.

    ``terminated`` is the robot's *own* claim that it can locally certify that
    no further work exists. It is only meaningful for algorithms that run a
    distributed termination protocol; for the rest it must stay ``False`` and
    the observer will report ``QUIESCENT_OBSERVED`` instead.
    """

    state: Any
    outgoing: tuple[Outgoing, ...] = ()
    terminated: bool = False


StepFn = Callable[[RobotView], StepResult]
InitFn = Callable[[RobotView], Any]


# ------------------------------------------------------------------- channel
@dataclass(frozen=True, slots=True)
class Channel:
    """Packet loss and delay with a realization paired across methods.

    The draw is a deterministic function of ``(world_id, treatment, u, v, t)``
    and never of the method, so two algorithms meet the same link state on the
    same edge in the same round even when they emit different traffic. Without
    this, a chattier method would face a different network.
    """

    world_id: str = "world"
    treatment: str = "nominal"
    loss_probability: float = 0.0
    delay_rounds: int = 0
    delay_jitter: int = 0

    def _uniform(self, sender: int, recipient: int, round_index: int, salt: str) -> float:
        key = (
            f"{self.world_id}|{self.treatment}|{sender}|{recipient}"
            f"|{round_index}|{salt}"
        )
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "little") / float(1 << 64)

    def dropped(self, sender: int, recipient: int, round_index: int) -> bool:
        if self.loss_probability <= 0.0:
            return False
        return self._uniform(sender, recipient, round_index, "loss") < self.loss_probability

    def latency(self, sender: int, recipient: int, round_index: int) -> int:
        base = max(int(self.delay_rounds), 0)
        if self.delay_jitter <= 0:
            return 1 + base
        draw = self._uniform(sender, recipient, round_index, "delay")
        return 1 + base + int(draw * (self.delay_jitter + 1))


# ------------------------------------------------------------------ observer
@dataclass
class Observation:
    """Metrics only. Nothing here is ever fed back into a decision."""

    rounds: int = 0
    messages: int = 0
    bytes_sent: int = 0
    delivered: int = 0
    dropped: int = 0
    messages_by_round: list[int] = field(default_factory=list)
    bytes_by_round: list[int] = field(default_factory=list)
    algorithm_status: str = MAX_ROUNDS
    cycle_detected: bool = False
    cycle_length: int = 0
    consistent: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "rounds": self.rounds,
            "messages": self.messages,
            "bytes": self.bytes_sent,
            "delivered": self.delivered,
            "dropped": self.dropped,
            "algorithm_status": self.algorithm_status,
            "cycle_observed": self.cycle_detected,
            "cycle_length": self.cycle_length,
            "consistent": self.consistent,
        }


# -------------------------------------------------------------------- engine
def run_rounds(
    *,
    capacities: np.ndarray,
    positions: np.ndarray,
    distances: np.ndarray,
    catalog: LoadCatalog,
    adjacency: np.ndarray,
    init: InitFn,
    step: StepFn,
    max_rounds: int,
    priority_tokens: Sequence[int],
    channel: Channel | None = None,
    quiescence_window: int = 3,
    signature: Callable[[list[Any]], Any] | None = None,
    consistency: Callable[[list[Any]], bool] | None = None,
) -> tuple[list[Any], Observation]:
    """Drive the synchronous rounds and return the final private states.

    The engine never shows a robot anything but its own :class:`RobotView`, so
    a step function physically cannot read another robot's capacity, position
    or commitment except through a message it was sent.
    """

    capacities = np.asarray(capacities, dtype=float)
    positions = np.asarray(positions, dtype=float)
    distances = np.asarray(distances, dtype=float)
    adjacency = np.asarray(adjacency, dtype=bool)
    n_robots = len(capacities)
    n_loads = catalog.n_loads
    if distances.shape != (n_robots, n_loads):
        raise ValueError("distances must have shape (N, K)")
    if adjacency.shape != (n_robots, n_robots):
        raise ValueError("adjacency must have shape (N, N)")
    channel = channel or Channel()
    neighbours = {
        robot: tuple(int(other) for other in np.flatnonzero(adjacency[robot]))
        for robot in range(n_robots)
    }

    def view_for(robot: int, round_index: int, inbox: tuple[Message, ...], state: Any) -> RobotView:
        return RobotView(
            robot_id=robot,
            capacity=float(capacities[robot]),
            position=positions[robot],
            distances=distances[robot],
            priority_token=int(priority_tokens[robot]),
            neighbours=neighbours[robot],
            catalog=catalog,
            inbox=inbox,
            round_index=round_index,
            n_robots=n_robots,
            n_loads=n_loads,
            max_rounds=int(max_rounds),
            state=state,
        )

    states: list[Any] = [
        init(view_for(robot, 0, (), None)) for robot in range(n_robots)
    ]
    pending: dict[int, list[Message]] = {}
    observation = Observation()
    idle_rounds = 0
    status = MAX_ROUNDS
    # Cycle detection is pure observation: it names what happened, it never
    # stops or steers the algorithm. Without it a non-terminating method would
    # be reported at whatever point the round cap happened to fall, which is a
    # snapshot of a limit cycle rather than an approximation of anything.
    seen_signatures: dict[Any, int] = {}
    last_mark: Any = object()  # sentinel: never equal to a real signature

    for round_index in range(int(max_rounds)):
        inboxes: list[tuple[Message, ...]] = []
        for robot in range(n_robots):
            arrived = pending.pop(_slot(round_index, robot), [])
            inboxes.append(tuple(arrived))
            observation.delivered += len(arrived)

        round_messages = 0
        round_bytes = 0
        next_states: list[Any] = []
        claims: list[bool] = []
        emissions: list[tuple[int, Outgoing]] = []
        for robot in range(n_robots):
            view = view_for(robot, round_index, inboxes[robot], states[robot])
            result = step(view)
            next_states.append(result.state)
            claims.append(bool(result.terminated))
            for out in result.outgoing:
                if not adjacency[robot, out.recipient]:
                    raise ValueError(
                        f"robot {robot} tried to reach non-neighbour {out.recipient}; "
                        "the contract allows edges of G only"
                    )
                emissions.append((robot, out))

        # Emissions are queued only after every robot has stepped, so a message
        # sent at t can never influence another robot's decision within t.
        for sender, out in emissions:
            size = wire_size(out.payload)
            round_messages += 1
            round_bytes += size
            if channel.dropped(sender, out.recipient, round_index):
                observation.dropped += 1
                continue
            arrival = round_index + channel.latency(sender, out.recipient, round_index)
            if arrival >= int(max_rounds):
                continue
            pending.setdefault(_slot(arrival, out.recipient), []).append(
                Message(
                    sender=sender,
                    kind=out.kind,
                    round_sent=round_index,
                    payload=out.payload,
                )
            )

        changed = any(
            _state_changed(before, after)
            for before, after in zip(states, next_states, strict=True)
        )
        states = next_states
        observation.messages += round_messages
        observation.bytes_sent += round_bytes
        observation.messages_by_round.append(round_messages)
        observation.bytes_by_round.append(round_bytes)
        observation.rounds = round_index + 1

        if all(claims):
            status = CONVERGED
            break

        if signature is None:
            # Nothing to watch but the traffic itself.
            settled = round_messages == 0 and not pending and not changed
        else:
            # Quiescence is about decisions, not silence. A method that
            # retransmits periodically to repair dropped messages is never
            # silent, yet it can be perfectly settled; judging it by traffic
            # would keep it running to the round cap forever.
            mark = signature(states)
            settled = mark == last_mark and not changed
            if not settled:
                # A fixed point repeats its signature every round; that is
                # stability, not a cycle. Only a signature the run had left and
                # came back to counts as one.
                if mark in seen_signatures:
                    if not observation.cycle_detected:
                        observation.cycle_length = (
                            round_index - seen_signatures[mark]
                        )
                        observation.cycle_detected = True
                else:
                    seen_signatures[mark] = round_index
            last_mark = mark

        if settled:
            idle_rounds += 1
            if idle_rounds >= quiescence_window:
                status = QUIESCENT_OBSERVED
                break
        else:
            idle_rounds = 0

    # Relabelling only, and only after the loop has ended on its own terms.
    # The detector must never shorten a run: cutting the moment a cycle is
    # seen would hand the cycling method a smaller communication bill than
    # the one it actually incurs.
    if status == MAX_ROUNDS and observation.cycle_detected:
        status = CYCLE_OBSERVED
    # A self-declared termination is only as good as the agreement behind it.
    # Under lossy links robots can end an epoch holding different profiles and
    # each conclude, correctly for its own view, that no move is left. Without
    # this check the engine would see every robot claim success and report a
    # convergence that never happened.
    if consistency is not None and not consistency(states):
        observation.consistent = False
        status = DIVERGED
    observation.algorithm_status = status
    return states, observation


def _slot(round_index: int, robot: int) -> int:
    return round_index * 1_000_003 + robot


def _state_changed(before: Any, after: Any) -> bool:
    if before is after:
        return False
    try:
        return bool(before != after)
    except ValueError:  # numpy inside the state
        return True


def priority_token(world_seed: int, capacity: float, position: Sequence[float]) -> int:
    """A deterministic token derived from intrinsic robot attributes.

    Never the storage index: a permutation of the rows must not change which
    robot wins a tie, and an index-derived token would silently break that.
    """

    key = "|".join(
        (
            str(int(world_seed)),
            f"{float(capacity):.9f}",
            f"{float(position[0]):.9f}",
            f"{float(position[1]):.9f}",
        )
    )
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def priority_tokens(
    world_seed: int, capacities: Sequence[float], positions: np.ndarray
) -> list[int]:
    return [
        priority_token(world_seed, capacity, positions[index])
        for index, capacity in enumerate(capacities)
    ]


__all__ = [
    "ALGORITHM_STATUS",
    "CONVERGED",
    "Channel",
    "CYCLE_OBSERVED",
    "DIVERGED",
    "ENVELOPE",
    "ENVELOPE_BYTES",
    "ERROR",
    "InitFn",
    "LoadCatalog",
    "MAX_ROUNDS",
    "Message",
    "Observation",
    "Outgoing",
    "QUIESCENT_OBSERVED",
    "RobotView",
    "StepFn",
    "StepResult",
    "TIME_LIMIT",
    "priority_token",
    "priority_tokens",
    "run_rounds",
    "wire_size",
]
