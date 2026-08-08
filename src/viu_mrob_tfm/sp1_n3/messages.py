"""Canonical binary message schemas, so bytes are measured and not assumed.

The inherited implementations priced a message at a hardcoded 40, 48 or
``16 + 8*K*d`` bytes depending on the allocator, which meant any communication
comparison measured the constants rather than the algorithms. Here every
algorithm shares one envelope and one encoder family; the payload is whatever
that algorithm actually needs to say, serialized once, and the engine counts
the real length of each unicast transmission.

Payloads are not padded to a common size. A method that genuinely needs to say
more pays for it -- that is a real cost, and equalising it would hide it.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np


KIND_NEIGHBOUR_PROFILE = 1
KIND_CBBA_TABLE = 2
KIND_GRAPE_PROPOSAL = 3

KIND_NAMES = {
    KIND_NEIGHBOUR_PROFILE: "neighbour_profile",
    KIND_CBBA_TABLE: "cbba_table",
    KIND_GRAPE_PROPOSAL: "grape_proposal",
}


# --------------------------------------------------- neighbour handshake (1)
# capacity and intrinsic token, then one float32 per load for the sender's own
# distance row. The token travels so that a tie between two joint deviations is
# broken on an intrinsic attribute rather than on a storage index, which would
# make the result depend on the order rows happen to be stored in.
_PROFILE_HEAD = struct.Struct("<fQ")


def encode_neighbour_profile(
    capacity: float, token: int, distances: np.ndarray
) -> bytes:
    values = np.asarray(distances, dtype=np.float32)
    head = _PROFILE_HEAD.pack(float(capacity), int(token) & 0xFFFFFFFFFFFFFFFF)
    return head + values.tobytes()


def decode_neighbour_profile(payload: bytes) -> tuple[float, int, np.ndarray]:
    capacity, token = _PROFILE_HEAD.unpack_from(payload, 0)
    values = np.frombuffer(payload, dtype=np.float32, offset=_PROFILE_HEAD.size)
    return float(capacity), int(token), values.astype(float)


# --------------------------------------------------------- CBBA bid table (2)
# One record per robot the sender has an opinion about. Only records whose
# version advanced since the last transmission to that neighbour are sent.
# robot, target, capacity, dD, -d, token, version
_CBBA_RECORD = struct.Struct("<HhfffQH")
CBBA_RECORD_BYTES = _CBBA_RECORD.size


@dataclass(frozen=True, slots=True)
class BidRecord:
    """One robot's current single-load commitment, as believed by the sender.

    The capacity travels with the record because a robot cannot estimate a
    load's residual deficit without knowing what the robots already committed
    to it actually carry. It is learned from a counted message, not read from
    a global table.
    """

    robot: int
    target: int  # -1 means "no commitment"
    capacity: float
    delta_deficit: float
    neg_distance: float
    token: int
    version: int

    @property
    def key(self) -> tuple[float, float, int]:
        """Lexicographic bid: useful capacity, then proximity, then token."""

        return (self.delta_deficit, self.neg_distance, -self.token)


def encode_cbba_table(records: tuple[BidRecord, ...]) -> bytes:
    return b"".join(
        _CBBA_RECORD.pack(
            record.robot,
            record.target,
            float(record.capacity),
            float(record.delta_deficit),
            float(record.neg_distance),
            int(record.token) & 0xFFFFFFFFFFFFFFFF,
            record.version,
        )
        for record in records
    )


def decode_cbba_table(payload: bytes) -> tuple[BidRecord, ...]:
    count = len(payload) // CBBA_RECORD_BYTES
    return tuple(
        BidRecord(*_CBBA_RECORD.unpack_from(payload, index * CBBA_RECORD_BYTES))
        for index in range(count)
    )


# ------------------------------------------------------ GRAPE proposal (3)
# has_move, epoch, deficit gain, distance gain, token, and the joint move.
_GRAPE = struct.Struct("<BHffQHhfHhf")
GRAPE_BYTES = _GRAPE.size


@dataclass(frozen=True, slots=True)
class Proposal:
    """A joint deviation of one or two robots, flooded for a total-order pick.

    Carrying the movers' capacities is what lets every robot apply the winning
    proposal to its own copy of the coverage vector without asking anyone.
    """

    has_move: bool
    epoch: int
    deficit_gain: float  # D(y) - D(y'), positive is better
    distance_gain: float  # J(y) - J(y'), positive is better
    token: int
    robot_a: int
    action_a: int
    capacity_a: float
    robot_b: int
    action_b: int
    capacity_b: float

    @property
    def order_key(self) -> tuple[float, float, int, int, int]:
        """Total order every robot applies identically.

        Lexicographic improvement first: reduce the deficit, and only at equal
        deficit reduce distance. Ties break on the intrinsic token, never on a
        storage index.
        """

        return (
            self.deficit_gain,
            self.distance_gain,
            -self.token,
            -self.robot_a,
            -self.robot_b,
        )


NO_PROPOSAL = Proposal(
    has_move=False,
    epoch=0,
    deficit_gain=-np.inf,
    distance_gain=-np.inf,
    token=0,
    robot_a=0,
    action_a=-1,
    capacity_a=0.0,
    robot_b=0,
    action_b=-1,
    capacity_b=0.0,
)


def encode_proposal(proposal: Proposal) -> bytes:
    return _GRAPE.pack(
        1 if proposal.has_move else 0,
        proposal.epoch,
        _finite(proposal.deficit_gain),
        _finite(proposal.distance_gain),
        int(proposal.token) & 0xFFFFFFFFFFFFFFFF,
        proposal.robot_a,
        proposal.action_a,
        float(proposal.capacity_a),
        proposal.robot_b,
        proposal.action_b,
        float(proposal.capacity_b),
    )


def decode_proposal(payload: bytes) -> Proposal:
    (
        has_move,
        epoch,
        deficit_gain,
        distance_gain,
        token,
        robot_a,
        action_a,
        capacity_a,
        robot_b,
        action_b,
        capacity_b,
    ) = _GRAPE.unpack_from(payload, 0)
    if not has_move:
        return Proposal(
            has_move=False,
            epoch=epoch,
            deficit_gain=-np.inf,
            distance_gain=-np.inf,
            token=0,
            robot_a=0,
            action_a=-1,
            capacity_a=0.0,
            robot_b=0,
            action_b=-1,
            capacity_b=0.0,
        )
    return Proposal(
        has_move=True,
        epoch=epoch,
        deficit_gain=float(deficit_gain),
        distance_gain=float(distance_gain),
        token=int(token),
        robot_a=int(robot_a),
        action_a=int(action_a),
        capacity_a=float(capacity_a),
        robot_b=int(robot_b),
        action_b=int(action_b),
        capacity_b=float(capacity_b),
    )


def canonical_proposal(proposal: Proposal) -> Proposal:
    """Round-trip a proposal through the wire format before ranking it.

    The gains are carried as float32. Without this, a robot compares its own
    proposal at full float64 precision while every neighbour compares the
    float32 image of the same proposal, so two robots can order the same pair
    of candidates differently and the epoch's max-consensus stops being a
    consensus. Canonicalising at creation makes every robot rank identical bit
    patterns.
    """

    if not proposal.has_move:
        return proposal
    return decode_proposal(encode_proposal(proposal))


def _finite(value: float) -> float:
    if np.isneginf(value):
        return float(np.finfo(np.float32).min)
    return float(value)


__all__ = [
    "BidRecord",
    "CBBA_RECORD_BYTES",
    "GRAPE_BYTES",
    "KIND_CBBA_TABLE",
    "KIND_GRAPE_PROPOSAL",
    "KIND_NAMES",
    "KIND_NEIGHBOUR_PROFILE",
    "NO_PROPOSAL",
    "Proposal",
    "decode_cbba_table",
    "decode_neighbour_profile",
    "decode_proposal",
    "encode_cbba_table",
    "encode_neighbour_profile",
    "encode_proposal",
]
