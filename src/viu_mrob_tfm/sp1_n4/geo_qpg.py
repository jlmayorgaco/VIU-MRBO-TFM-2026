"""Geo-QPG: atomic quota-potential games and distributed commit variants.

The implementation deliberately separates the *decision view* from the
observer.  A robot evaluates a deviation with its own capacity and distance
row plus the replicated per-load registers ``(Q_k, v_k)``.  It never receives
the fleet assignment profile.  The simulator retains the profile only to apply
accepted atomic commits and to compute the post-hoc certificate.

Two phases avoid an arbitrary weight between feasibility and distance:

``Q``
    accept only moves that strictly decrease total capacity deficit;
``G``
    once the deficit is zero, accept only moves that preserve zero deficit and
    strictly decrease travelled distance.

Every proposal carries the versions it read.  Legacy 'geo_qpg_cf' resolves a
batch with a global proposal order and is retained as an architectural
ablation.  'geo_qpg_d' instead selects a maximal independent set by local
conflict-neighbour comparisons and applies PREPARE/COMMIT/ABORT transactions to
the affected load registers.  The nominal campaign assumes reliable delivery
and no coordinator crash during a transaction.  This is a logical coordination
contract, not a physical-safety guarantee or a claim for lossy channels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Iterable, Sequence

import numpy as np

from viu_mrob_tfm.sp1_n3.certificate import Certificate, certify, coverage
from viu_mrob_tfm.sp1_n3.contract import priority_tokens
from viu_mrob_tfm.sp1_n3.graph import graph_metrics
from viu_mrob_tfm.sp1_n3.worlds import World


LEGACY_METHODS = ("geo_qpg_u", "geo_qpg_p", "geo_qpg_cf")
METHODS = LEGACY_METHODS + (
    "geo_qpg_smith",
    "geo_qpg_lll",
    "geo_qpg_c3",
    "geo_qpg_d",
)
METHOD_LABELS = {
    "geo_qpg_u": "Geo-QPG-BR",
    "geo_qpg_p": "Geo-QPG-2BR",
    "geo_qpg_cf": "Geo-QPG-CF (global)",
    "geo_qpg_smith": "Geo-ASR (revisión Smith atómica)",
    "geo_qpg_lll": "Geo-LLL atómico",
    "geo_qpg_c3": "Geo-QPG-C3",
    "geo_qpg_d": "Geo-QPG-DMIS+TX",
}

# Fitness de seleccion del factorial N3.B. Solo cambia el orden en que se
# valoran los candidatos; la admisibilidad la fija `_admissible` y es comun.
FITNESS_DISTANCE = "F0"      # g depende solo de la distancia
FITNESS_DEFICIT = "F1"       # g depende solo de la cobertura
FITNESS_MARGINAL = "F2"      # utilidad marginal de Geo-QPG, dependiente de fase
FITNESS = (FITNESS_DISTANCE, FITNESS_DEFICIT, FITNESS_MARGINAL)

PHASE_QUOTA = "Q"
PHASE_GEOMETRY = "G"
TOLERANCE = 1e-9

# Wire-accounting constants.  They describe the compact protocol fields, not
# Python object sizes.  Every routed hop is one counted transmission.
PROPOSAL_BASE_BYTES = 28
PROPOSAL_ROBOT_BYTES = 28
PROPOSAL_LOAD_BYTES = 12
ACK_BYTES = 16
REGISTER_UPDATE_BYTES = 32
PAIR_STATE_BASE_BYTES = 24
PAIR_STATE_PER_LOAD_BYTES = 8
ARBITRATION_HEADER_BYTES = 24
TX_PREPARE_BYTES = 36
TX_REPLY_BYTES = 16
TX_DECISION_BYTES = 20


def deficit_from_coverage(q: np.ndarray, demands: np.ndarray) -> float:
    """Return ``D = sum_k [m_k-Q_k]_+``."""

    return float(np.maximum(np.asarray(demands) - np.asarray(q), 0.0).sum())


def assignment_distance(assignment: np.ndarray, distances: np.ndarray) -> float:
    """Return ``J`` for an atomic assignment vector (``-1`` means idle)."""

    return float(
        sum(
            distances[i, load]
            for i, load in enumerate(np.asarray(assignment, dtype=int))
            if load >= 0
        )
    )


def affected_loads(old_actions: Sequence[int], new_actions: Sequence[int]) -> tuple[int, ...]:
    """Loads whose aggregate changes; idle is excluded."""

    touched = {
        int(load)
        for load in tuple(old_actions) + tuple(new_actions)
        if int(load) >= 0
    }
    return tuple(sorted(touched))


def marginal_changes(
    q: np.ndarray,
    demands: np.ndarray,
    robot_ids: Sequence[int],
    old_actions: Sequence[int],
    new_actions: Sequence[int],
    capacities: np.ndarray,
    distances: np.ndarray,
) -> tuple[float, float]:
    """Exact ``(D(new)-D(old), J(new)-J(old))`` on affected loads only.

    No membership list is needed.  For a unilateral deviation ``r -> s`` the
    inputs reduce to ``Q_r, Q_s, c_i, d_ir, d_is``.  The pair version uses the
    same calculation on the union of the affected loads (at most four for a
    pair and six for a triple).
    """

    q = np.asarray(q, dtype=float)
    demands = np.asarray(demands, dtype=float)
    capacities = np.asarray(capacities, dtype=float)
    distances = np.asarray(distances, dtype=float)
    robot_ids = tuple(int(i) for i in robot_ids)
    old_actions = tuple(int(a) for a in old_actions)
    new_actions = tuple(int(a) for a in new_actions)
    if not (len(robot_ids) == len(old_actions) == len(new_actions)):
        raise ValueError("robot, old-action and new-action tuples must align")

    touched = affected_loads(old_actions, new_actions)
    q_after = {load: float(q[load]) for load in touched}
    for robot, old, new in zip(robot_ids, old_actions, new_actions, strict=True):
        if old >= 0:
            q_after[old] -= float(capacities[robot])
        if new >= 0:
            q_after[new] += float(capacities[robot])

    d_before = sum(max(float(demands[k] - q[k]), 0.0) for k in touched)
    d_after = sum(max(float(demands[k] - q_after[k]), 0.0) for k in touched)
    j_before = sum(
        float(distances[i, old])
        for i, old in zip(robot_ids, old_actions, strict=True)
        if old >= 0
    )
    j_after = sum(
        float(distances[i, new])
        for i, new in zip(robot_ids, new_actions, strict=True)
        if new >= 0
    )
    return float(d_after - d_before), float(j_after - j_before)


@dataclass(frozen=True, slots=True)
class MoveProposal:
    """A versioned unilateral or pair deviation."""

    robot_ids: tuple[int, ...]
    old_actions: tuple[int, ...]
    new_actions: tuple[int, ...]
    touched_loads: tuple[int, ...]
    expected_versions: tuple[int, ...]
    delta_deficit: float
    delta_distance: float
    phase: str
    priority: tuple[int, ...]
    exploratory: bool = False

    @property
    def coordinator(self) -> int:
        """Robot proposer responsible for this proposal's transaction only."""

        return min(self.robot_ids)


@dataclass(frozen=True, slots=True)
class CoordinationOrderResult:
    """Auditable result of the bounded minimum coordination-order search.

    ``order`` is the number of robots that must *all* change action in the
    first connected strict lexicographic improvement found. ``None`` means
    that the search exhausted ``searched_through``; it does not rule out a
    larger improving coalition.
    """

    order: int | None
    searched_through: int
    phase: str
    deficit_before: float
    distance_before: float
    robot_ids: tuple[int, ...] = ()
    old_actions: tuple[int, ...] = ()
    new_actions: tuple[int, ...] = ()
    delta_deficit: float = 0.0
    delta_distance: float = 0.0
    connected_only: bool = True

    @property
    def category(self) -> str:
        """Compact label used by the bounded experiment."""

        return str(self.order) if self.order is not None else f">{self.searched_through}"


def _admissible(phase: str, delta_deficit: float, delta_distance: float) -> bool:
    if phase == PHASE_QUOTA:
        return delta_deficit < -TOLERANCE
    if phase == PHASE_GEOMETRY:
        return abs(delta_deficit) <= TOLERANCE and delta_distance < -TOLERANCE
    raise ValueError(f"unknown phase {phase!r}")


def build_proposal(
    *,
    q: np.ndarray,
    versions: np.ndarray,
    demands: np.ndarray,
    robot_ids: Sequence[int],
    old_actions: Sequence[int],
    new_actions: Sequence[int],
    capacities: np.ndarray,
    distances: np.ndarray,
    phase: str,
    priority: Sequence[int],
) -> MoveProposal | None:
    """Build an admissible proposal from the aggregate register snapshot."""

    old = tuple(int(a) for a in old_actions)
    new = tuple(int(a) for a in new_actions)
    if old == new:
        return None
    robots = tuple(int(i) for i in robot_ids)
    touched = affected_loads(old, new)
    delta_d, delta_j = marginal_changes(
        q, demands, robots, old, new, capacities, distances
    )
    if not _admissible(phase, delta_d, delta_j):
        return None
    return MoveProposal(
        robot_ids=robots,
        old_actions=old,
        new_actions=new,
        touched_loads=touched,
        expected_versions=tuple(int(versions[k]) for k in touched),
        delta_deficit=delta_d,
        delta_distance=delta_j,
        phase=phase,
        priority=tuple(int(value) for value in priority),
    )


def build_transition_proposal(
    *,
    q: np.ndarray,
    versions: np.ndarray,
    demands: np.ndarray,
    robot_ids: Sequence[int],
    old_actions: Sequence[int],
    new_actions: Sequence[int],
    capacities: np.ndarray,
    distances: np.ndarray,
    phase: str,
    priority: Sequence[int],
) -> MoveProposal | None:
    """Build one versioned exploratory transition for atomic log-linear learning.

    During phase Q the transition may temporarily increase the quota deficit.
    Once phase G has been reached, only transitions that preserve feasibility
    are emitted.  This distinction is what separates LLL from the strict
    improvement rules used by BR, ASR and the coalition neighbourhoods.
    """

    old = tuple(int(a) for a in old_actions)
    new = tuple(int(a) for a in new_actions)
    if old == new:
        return None
    robots = tuple(int(i) for i in robot_ids)
    touched = affected_loads(old, new)
    delta_d, delta_j = marginal_changes(
        q, demands, robots, old, new, capacities, distances
    )
    if phase == PHASE_GEOMETRY and abs(delta_d) > TOLERANCE:
        return None
    return MoveProposal(
        robot_ids=robots,
        old_actions=old,
        new_actions=new,
        touched_loads=touched,
        expected_versions=tuple(int(versions[k]) for k in touched),
        delta_deficit=delta_d,
        delta_distance=delta_j,
        phase=phase,
        priority=tuple(int(value) for value in priority),
        exploratory=True,
    )


@dataclass(slots=True)
class CommitEvent:
    phase: str
    robot_ids: tuple[int, ...]
    old_actions: tuple[int, ...]
    new_actions: tuple[int, ...]
    touched_loads: tuple[int, ...]
    deficit_before: float
    deficit_after: float
    distance_before: float
    distance_after: float
    accepted: bool
    reason: str


@dataclass(slots=True)
class QuotaRegister:
    """Atomic per-load aggregates and their monotonically increasing versions."""

    demands: np.ndarray
    capacities: np.ndarray
    distances: np.ndarray
    assignment: np.ndarray | None = None
    q: np.ndarray = field(init=False)
    versions: np.ndarray = field(init=False)
    events: list[CommitEvent] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.demands = np.asarray(self.demands, dtype=float)
        self.capacities = np.asarray(self.capacities, dtype=float)
        self.distances = np.asarray(self.distances, dtype=float)
        if self.assignment is None:
            self.assignment = np.full(len(self.capacities), -1, dtype=int)
        else:
            self.assignment = np.asarray(self.assignment, dtype=int).copy()
        self.q = coverage(self.assignment, self.capacities, len(self.demands))
        self.versions = np.zeros(len(self.demands), dtype=np.int64)

    @property
    def deficit(self) -> float:
        return deficit_from_coverage(self.q, self.demands)

    @property
    def distance(self) -> float:
        return assignment_distance(self.assignment, self.distances)

    @property
    def phase(self) -> str:
        return PHASE_GEOMETRY if self.deficit <= TOLERANCE else PHASE_QUOTA

    def commit(self, proposal: MoveProposal) -> tuple[bool, str]:
        """Compare versions and atomically apply one guarded proposal."""

        d_before = self.deficit
        j_before = self.distance
        if any(
            int(self.versions[k]) != expected
            for k, expected in zip(
                proposal.touched_loads, proposal.expected_versions, strict=True
            )
        ):
            self._record_rejection(proposal, d_before, j_before, "STALE_VERSION")
            return False, "STALE_VERSION"
        if any(
            int(self.assignment[i]) != old
            for i, old in zip(
                proposal.robot_ids, proposal.old_actions, strict=True
            )
        ):
            self._record_rejection(proposal, d_before, j_before, "STALE_ACTION")
            return False, "STALE_ACTION"

        delta_d, delta_j = marginal_changes(
            self.q,
            self.demands,
            proposal.robot_ids,
            proposal.old_actions,
            proposal.new_actions,
            self.capacities,
            self.distances,
        )
        if not (
            np.isclose(delta_d, proposal.delta_deficit, atol=1e-10)
            and np.isclose(delta_j, proposal.delta_distance, atol=1e-10)
        ):
            self._record_rejection(proposal, d_before, j_before, "DELTA_MISMATCH")
            return False, "DELTA_MISMATCH"
        if proposal.phase != self.phase:
            self._record_rejection(proposal, d_before, j_before, "PHASE_CHANGED")
            return False, "PHASE_CHANGED"
        if proposal.exploratory:
            exploratory_guard = (
                proposal.phase == PHASE_QUOTA
                or (
                    proposal.phase == PHASE_GEOMETRY
                    and abs(delta_d) <= TOLERANCE
                )
            )
            if not exploratory_guard:
                self._record_rejection(
                    proposal, d_before, j_before, "EXPLORATION_GUARD_REJECTED"
                )
                return False, "EXPLORATION_GUARD_REJECTED"
        elif not _admissible(proposal.phase, delta_d, delta_j):
            self._record_rejection(proposal, d_before, j_before, "GUARD_REJECTED")
            return False, "GUARD_REJECTED"

        for robot, old, new in zip(
            proposal.robot_ids,
            proposal.old_actions,
            proposal.new_actions,
            strict=True,
        ):
            capability = float(self.capacities[robot])
            if old >= 0:
                self.q[old] -= capability
            if new >= 0:
                self.q[new] += capability
            self.assignment[robot] = new
        for load in proposal.touched_loads:
            self.versions[load] += 1

        # This equality is an implementation invariant, not an input to a
        # robot's decision.
        expected_q = coverage(self.assignment, self.capacities, len(self.demands))
        if not np.allclose(self.q, expected_q, atol=1e-9):
            raise AssertionError("atomic register drifted from the committed profile")
        d_after = self.deficit
        j_after = self.distance
        self.events.append(
            CommitEvent(
                phase=proposal.phase,
                robot_ids=proposal.robot_ids,
                old_actions=proposal.old_actions,
                new_actions=proposal.new_actions,
                touched_loads=proposal.touched_loads,
                deficit_before=d_before,
                deficit_after=d_after,
                distance_before=j_before,
                distance_after=j_after,
                accepted=True,
                reason=("EXPLORATORY_COMMIT" if proposal.exploratory else "COMMITTED"),
            )
        )
        return True, "EXPLORATORY_COMMIT" if proposal.exploratory else "COMMITTED"

    def _record_rejection(
        self, proposal: MoveProposal, d_before: float, j_before: float, reason: str
    ) -> None:
        self.events.append(
            CommitEvent(
                phase=proposal.phase,
                robot_ids=proposal.robot_ids,
                old_actions=proposal.old_actions,
                new_actions=proposal.new_actions,
                touched_loads=proposal.touched_loads,
                deficit_before=d_before,
                deficit_after=d_before,
                distance_before=j_before,
                distance_after=j_before,
                accepted=False,
                reason=reason,
            )
        )


def _all_pairs_hops(adjacency: np.ndarray) -> np.ndarray:
    adjacency = np.asarray(adjacency, dtype=bool)
    n = len(adjacency)
    hops = np.full((n, n), np.inf)
    for source in range(n):
        hops[source, source] = 0
        queue = [source]
        head = 0
        while head < len(queue):
            node = queue[head]
            head += 1
            for neighbor in np.flatnonzero(adjacency[node]):
                if not np.isfinite(hops[source, neighbor]):
                    hops[source, neighbor] = hops[source, node] + 1
                    queue.append(int(neighbor))
    return hops


@dataclass(slots=True)
class MessageLedger:
    """Transparent hop-by-hop communication accounting."""

    adjacency: np.ndarray
    n_loads: int
    messages: int = 0
    bytes_sent: int = 0
    proposal_messages: int = 0
    update_messages: int = 0
    pair_messages: int = 0
    arbitration_messages: int = 0
    transaction_messages: int = 0
    unreachable: int = 0
    hops: np.ndarray = field(init=False)
    keepers: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.adjacency = np.asarray(self.adjacency, dtype=bool)
        self.hops = _all_pairs_hops(self.adjacency)
        self.keepers = np.arange(self.n_loads, dtype=int) % len(self.adjacency)

    def _route(self, sender: int, recipient: int, nbytes: int, *, kind: str) -> bool:
        distance = self.hops[int(sender), int(recipient)]
        if not np.isfinite(distance):
            self.unreachable += 1
            return False
        count = int(distance)
        self.messages += count
        self.bytes_sent += count * int(nbytes)
        if kind == "proposal":
            self.proposal_messages += count
        elif kind == "update":
            self.update_messages += count
        elif kind == "pair":
            self.pair_messages += count
        elif kind == "arbitration":
            self.arbitration_messages += count
        elif kind == "transaction":
            self.transaction_messages += count
        return True

    def record_proposal(self, proposal: MoveProposal) -> bool:
        size = (
            PROPOSAL_BASE_BYTES
            + PROPOSAL_ROBOT_BYTES * len(proposal.robot_ids)
            + PROPOSAL_LOAD_BYTES * len(proposal.touched_loads)
        )
        ok = True
        for load in proposal.touched_loads:
            keeper = int(self.keepers[load])
            ok &= self._route(proposal.coordinator, keeper, size, kind="proposal")
            ok &= self._route(keeper, proposal.coordinator, ACK_BYTES, kind="proposal")
        return bool(ok)

    def record_updates(self, proposal: MoveProposal) -> None:
        # Reliable register updates are flooded once over a spanning tree of
        # the keeper's connected component.  The observer counts N_c-1 actual
        # edge transmissions, not a fictional one-hop broadcast.
        for load in proposal.touched_loads:
            keeper = int(self.keepers[load])
            reachable = np.flatnonzero(np.isfinite(self.hops[keeper]))
            count = max(int(len(reachable)) - 1, 0)
            self.messages += count
            self.update_messages += count
            self.bytes_sent += count * REGISTER_UPDATE_BYTES

    def record_pair_exchange(self, left: int, right: int) -> bool:
        size = PAIR_STATE_BASE_BYTES + PAIR_STATE_PER_LOAD_BYTES * self.n_loads
        ok = self._route(left, right, size, kind="pair")
        ok &= self._route(right, left, size, kind="pair")
        return bool(ok)

    def record_pair_broadcast(self) -> None:
        size = PAIR_STATE_BASE_BYTES + PAIR_STATE_PER_LOAD_BYTES * self.n_loads
        count = int(np.asarray(self.adjacency, dtype=bool).sum())
        self.messages += count
        self.pair_messages += count
        self.bytes_sent += count * size

    def record_group_exchange(self, robots: Sequence[int]) -> bool:
        """Count a local state exchange along a coordinator-centred tree."""

        group = tuple(int(robot) for robot in robots)
        coordinator = min(group)
        size = PAIR_STATE_BASE_BYTES + PAIR_STATE_PER_LOAD_BYTES * self.n_loads
        ok = True
        for robot in group:
            if robot == coordinator:
                continue
            ok &= self._route(robot, coordinator, size, kind="pair")
            ok &= self._route(coordinator, robot, size, kind="pair")
        return bool(ok)

    def record_arbitration(self, left: MoveProposal, right: MoveProposal) -> bool:
        """Count the exchange of priorities between two conflicting proposals."""

        size = ARBITRATION_HEADER_BYTES + 4 * (
            len(left.touched_loads) + len(right.touched_loads)
        )
        ok = self._route(left.coordinator, right.coordinator, size, kind="arbitration")
        ok &= self._route(right.coordinator, left.coordinator, size, kind="arbitration")
        return bool(ok)

    def record_transaction_leg(
        self, sender: int, recipient: int, nbytes: int
    ) -> bool:
        return self._route(sender, recipient, nbytes, kind="transaction")


def _candidate_key(
    proposal: MoveProposal,
    fitness: str = FITNESS_MARGINAL,
) -> tuple[float, ...]:
    if fitness == FITNESS_DISTANCE:
        return (
            proposal.delta_distance,
            *proposal.priority,
            *proposal.new_actions,
        )
    if fitness == FITNESS_DEFICIT:
        return (
            proposal.delta_deficit,
            *proposal.priority,
            *proposal.new_actions,
        )
    if proposal.phase == PHASE_QUOTA:
        return (
            proposal.delta_deficit,
            proposal.delta_distance,
            *proposal.priority,
            *proposal.new_actions,
        )
    return (
        proposal.delta_distance,
        *proposal.priority,
        *proposal.new_actions,
    )


def _best_unilateral(
    robot: int,
    register: QuotaRegister,
    tokens: np.ndarray,
    fitness: str = FITNESS_MARGINAL,
) -> MoveProposal | None:
    old = int(register.assignment[robot])
    phase = register.phase
    proposals: list[MoveProposal] = []
    for target in range(-1, len(register.demands)):
        proposal = build_proposal(
            q=register.q,
            versions=register.versions,
            demands=register.demands,
            robot_ids=(robot,),
            old_actions=(old,),
            new_actions=(target,),
            capacities=register.capacities,
            distances=register.distances,
            phase=phase,
            priority=(int(tokens[robot]), robot),
        )
        if proposal is not None:
            proposals.append(proposal)
    if not proposals:
        return None
    return min(proposals, key=lambda p: _candidate_key(p, fitness))


def _best_pair(
    left: int,
    right: int,
    register: QuotaRegister,
    tokens: np.ndarray,
    fitness: str = FITNESS_MARGINAL,
) -> MoveProposal | None:
    old = (int(register.assignment[left]), int(register.assignment[right]))
    phase = register.phase
    proposals: list[MoveProposal] = []
    actions = range(-1, len(register.demands))
    for targets in product(actions, repeat=2):
        proposal = build_proposal(
            q=register.q,
            versions=register.versions,
            demands=register.demands,
            robot_ids=(left, right),
            old_actions=old,
            new_actions=targets,
            capacities=register.capacities,
            distances=register.distances,
            phase=phase,
            priority=(
                min(int(tokens[left]), int(tokens[right])),
                max(int(tokens[left]), int(tokens[right])),
                left,
                right,
            ),
        )
        if proposal is not None:
            proposals.append(proposal)
    if not proposals:
        return None
    return min(proposals, key=lambda p: _candidate_key(p, fitness))


def _best_group(
    robots: Sequence[int],
    register: QuotaRegister,
    tokens: np.ndarray,
    *,
    require_all_change: bool = False,
) -> MoveProposal | None:
    """Return the best strict deviation for a bounded coalition."""

    group = tuple(int(robot) for robot in robots)
    old = tuple(int(register.assignment[robot]) for robot in group)
    phase = register.phase
    targets = np.asarray(
        list(product(range(-1, len(register.demands)), repeat=len(group))),
        dtype=int,
    )
    q_after = np.repeat(register.q[None, :], len(targets), axis=0)
    for position, robot in enumerate(group):
        old_load = old[position]
        if old_load >= 0:
            q_after[:, old_load] -= float(register.capacities[robot])
        active = np.flatnonzero(targets[:, position] >= 0)
        q_after[active, targets[active, position]] += float(register.capacities[robot])
    delta_d = (
        np.maximum(register.demands[None, :] - q_after, 0.0).sum(axis=1)
        - register.deficit
    )
    old_j = sum(
        float(register.distances[robot, load])
        for robot, load in zip(group, old, strict=True)
        if load >= 0
    )
    new_j = np.zeros(len(targets), dtype=float)
    for position, robot in enumerate(group):
        active = np.flatnonzero(targets[:, position] >= 0)
        new_j[active] += register.distances[robot, targets[active, position]]
    delta_j = new_j - old_j
    changed_positions = targets != np.asarray(old)[None, :]
    changed = (
        np.all(changed_positions, axis=1)
        if require_all_change
        else np.any(changed_positions, axis=1)
    )
    if phase == PHASE_QUOTA:
        admissible = changed & (delta_d < -TOLERANCE)
    else:
        admissible = changed & (np.abs(delta_d) <= TOLERANCE) & (delta_j < -TOLERANCE)
    indices = np.flatnonzero(admissible)
    if not len(indices):
        return None
    best = min(
        (int(index) for index in indices),
        key=lambda index: (
            float(delta_d[index]) if phase == PHASE_QUOTA else float(delta_j[index]),
            float(delta_j[index]),
            tuple(int(value) for value in targets[index]),
        ),
    )
    return build_proposal(
        q=register.q,
        versions=register.versions,
        demands=register.demands,
        robot_ids=group,
        old_actions=old,
        new_actions=tuple(int(value) for value in targets[best]),
        capacities=register.capacities,
        distances=register.distances,
        phase=phase,
        priority=tuple(sorted(int(tokens[robot]) for robot in group)) + group,
    )


def _connected_group(group: Sequence[int], adjacency: np.ndarray) -> bool:
    """Return whether the subgraph induced by ``group`` is connected."""

    nodes = tuple(int(node) for node in group)
    if len(nodes) <= 1:
        return True
    allowed = set(nodes)
    reached = {nodes[0]}
    frontier = [nodes[0]]
    while frontier:
        node = frontier.pop()
        for neighbor in np.flatnonzero(adjacency[node]):
            neighbor = int(neighbor)
            if neighbor in allowed and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    return len(reached) == len(nodes)


def minimum_improving_coalition_order(
    world: World,
    assignment: np.ndarray,
    adjacency: np.ndarray,
    *,
    max_order: int = 3,
    connected_only: bool = True,
) -> CoordinationOrderResult:
    """Find the minimum bounded coalition order with a strict improvement.

    The objective and the phase guard are exactly those used by Geo-QPG:
    decrease total capacity deficit in phase Q; once feasible, preserve zero
    deficit and decrease travelled distance in phase G. Every member of a
    witness coalition changes action, so the returned order is not inflated by
    inactive members. With ``connected_only=True`` (the N4 experiment), only
    coalitions connected in the frozen N3 graph are admissible.

    Exhausting ``max_order`` is a truncated result, not a certificate of a
    global or unrestricted local optimum.
    """

    assignment = np.asarray(assignment, dtype=int)
    adjacency = np.asarray(adjacency, dtype=bool)
    if assignment.shape != (world.n_robots,):
        raise ValueError(f"assignment must have shape {(world.n_robots,)}")
    if adjacency.shape != (world.n_robots, world.n_robots):
        raise ValueError(
            "adjacency must have shape "
            f"{(world.n_robots, world.n_robots)}"
        )
    if np.any((assignment < -1) | (assignment >= world.n_loads)):
        raise ValueError("assignment contains an invalid load index")
    if max_order < 1:
        raise ValueError("max_order must be positive")

    searched_through = min(int(max_order), world.n_robots)
    register = QuotaRegister(
        world.demands,
        world.capacities,
        world.distances,
        assignment=assignment,
    )
    tokens = np.asarray(
        priority_tokens(world.seed, world.capacities, world.robot_positions),
        dtype=np.uint64,
    )
    for order in range(1, searched_through + 1):
        proposals: list[MoveProposal] = []
        for group in combinations(range(world.n_robots), order):
            if connected_only and not _connected_group(group, adjacency):
                continue
            proposal = _best_group(
                group,
                register,
                tokens,
                require_all_change=True,
            )
            if proposal is not None:
                proposals.append(proposal)
        if proposals:
            witness = min(proposals, key=_candidate_key)
            return CoordinationOrderResult(
                order=order,
                searched_through=searched_through,
                phase=register.phase,
                deficit_before=register.deficit,
                distance_before=register.distance,
                robot_ids=witness.robot_ids,
                old_actions=witness.old_actions,
                new_actions=witness.new_actions,
                delta_deficit=witness.delta_deficit,
                delta_distance=witness.delta_distance,
                connected_only=connected_only,
            )
    return CoordinationOrderResult(
        order=None,
        searched_through=searched_through,
        phase=register.phase,
        deficit_before=register.deficit,
        distance_before=register.distance,
        connected_only=connected_only,
    )


def _unilateral_proposals(
    robot: int,
    register: QuotaRegister,
    tokens: np.ndarray,
) -> list[MoveProposal]:
    old = int(register.assignment[robot])
    phase = register.phase
    proposals: list[MoveProposal] = []
    for target in range(-1, len(register.demands)):
        proposal = build_proposal(
            q=register.q,
            versions=register.versions,
            demands=register.demands,
            robot_ids=(robot,),
            old_actions=(old,),
            new_actions=(target,),
            capacities=register.capacities,
            distances=register.distances,
            phase=phase,
            priority=(int(tokens[robot]), robot),
        )
        if proposal is not None:
            proposals.append(proposal)
    return proposals


def _transition_options(
    robot: int,
    register: QuotaRegister,
    tokens: np.ndarray,
    fitness: str = FITNESS_MARGINAL,
) -> list[tuple[int, MoveProposal | None, float]]:
    """Enumerate the current action and all locally admissible LLL transitions."""

    old = int(register.assignment[robot])
    phase = register.phase
    options: list[tuple[int, MoveProposal | None, float]] = [(old, None, 0.0)]
    for target in range(-1, len(register.demands)):
        if target == old:
            continue
        proposal = build_transition_proposal(
            q=register.q,
            versions=register.versions,
            demands=register.demands,
            robot_ids=(robot,),
            old_actions=(old,),
            new_actions=(target,),
            capacities=register.capacities,
            distances=register.distances,
            phase=phase,
            priority=(int(tokens[robot]), robot),
        )
        if proposal is None:
            continue
        deficit_scale = max(float(register.demands.sum()), 1.0)
        distance_scale = max(
            float(np.max(register.distances)) * len(register.assignment), 1.0
        )
        if fitness == FITNESS_DISTANCE:
            loss = proposal.delta_distance / distance_scale
        elif fitness == FITNESS_DEFICIT:
            loss = proposal.delta_deficit / deficit_scale
        else:
            loss = (
                proposal.delta_deficit / deficit_scale
                if phase == PHASE_QUOTA
                else proposal.delta_distance / distance_scale
            )
        options.append((target, proposal, float(loss)))
    return options


def _submit(
    proposal: MoveProposal,
    register: QuotaRegister,
    ledger: MessageLedger,
) -> tuple[bool, str]:
    if not ledger.record_proposal(proposal):
        register._record_rejection(
            proposal, register.deficit, register.distance, "UNREACHABLE_REGISTER"
        )
        return False, "UNREACHABLE_REGISTER"
    accepted, reason = register.commit(proposal)
    if accepted:
        ledger.record_updates(proposal)
    return accepted, reason


def _state_signature(register: QuotaRegister) -> tuple[int, ...]:
    return tuple(int(value) for value in register.assignment)


def _sequential_unilateral(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    max_rounds: int,
    fitness: str = FITNESS_MARGINAL,
) -> tuple[int, bool]:
    order = list(np.argsort(tokens, kind="stable"))
    quiet = 0
    rounds = 0
    changed = False
    while rounds < max_rounds and quiet < len(order):
        robot = int(order[rounds % len(order)])
        proposal = _best_unilateral(robot, register, tokens, fitness)
        rounds += 1
        if proposal is None:
            quiet += 1
            continue
        accepted, _ = _submit(proposal, register, ledger)
        if accepted:
            quiet = 0
            changed = True
        else:
            quiet += 1
    return rounds, changed


def _sequential_pairs(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    adjacency: np.ndarray,
    max_rounds: int,
    fitness: str = FITNESS_MARGINAL,
) -> tuple[int, bool]:
    edges = [
        (int(i), int(j))
        for i, j in combinations(range(len(adjacency)), 2)
        if adjacency[i, j]
    ]
    edges.sort(key=lambda edge: (min(tokens[list(edge)]), max(tokens[list(edge)]), edge))
    if not edges:
        return 0, False
    quiet = 0
    rounds = 0
    changed = False
    while rounds < max_rounds and quiet < len(edges):
        left, right = edges[rounds % len(edges)]
        rounds += 1
        if not ledger.record_pair_exchange(left, right):
            quiet += 1
            continue
        proposal = _best_pair(left, right, register, tokens, fitness)
        if proposal is None:
            quiet += 1
            continue
        accepted, _ = _submit(proposal, register, ledger)
        if accepted:
            quiet = 0
            changed = True
        else:
            quiet += 1
    return rounds, changed


def _selection_gain(proposal: MoveProposal, fitness: str) -> float:
    """Ganancia con la que ASR sortea entre candidatos ya admisibles."""

    if fitness == FITNESS_DISTANCE:
        return -proposal.delta_distance
    if fitness == FITNESS_DEFICIT:
        return -proposal.delta_deficit
    return (
        -proposal.delta_deficit
        if proposal.phase == PHASE_QUOTA
        else -proposal.delta_distance
    )


def _smith_atomic_unilateral(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    rng: np.random.Generator,
    max_rounds: int,
    fitness: str = FITNESS_MARGINAL,
) -> tuple[int, bool]:
    """Asynchronous Atomic Smith Revision (ASR) over strict positive gains.

    A complete quiet sweep is the stopping certificate.  Unlike the
    deterministic best response, ASR samples one admissible action with
    probability proportional to its positive potential gain.  It borrows the
    Smith revision-rate idea but is not the continuous Smith population ODE.
    """

    n = len(register.assignment)
    rounds = 0
    changed_any = False
    while rounds < max_rounds:
        changed_sweep = False
        for robot in rng.permutation(n):
            if rounds >= max_rounds:
                break
            proposals = _unilateral_proposals(int(robot), register, tokens)
            rounds += 1
            if not proposals:
                continue
            gains = np.asarray(
                [_selection_gain(proposal, fitness) for proposal in proposals],
                dtype=float,
            )
            # Con F2 toda propuesta admisible tiene ganancia estrictamente
            # positiva, de modo que la parte positiva es la identidad y esta
            # rama reproduce el comportamiento publicado. Con F0 o F1 la
            # ganancia puede ser negativa ---un movimiento que reduce el
            # deficit puede alejar al AMR--- y entonces se sortea uniformemente
            # entre los admisibles en lugar de normalizar un vector con signos
            # mezclados.
            positive = np.maximum(gains, 0.0)
            total = float(positive.sum())
            if total <= 0.0:
                probabilities = np.full(len(proposals), 1.0 / len(proposals))
            else:
                probabilities = positive / total
            proposal = proposals[int(rng.choice(len(proposals), p=probabilities))]
            accepted, _ = _submit(proposal, register, ledger)
            changed_sweep |= accepted
            changed_any |= accepted
        if not changed_sweep:
            break
    return rounds, changed_any


def _log_linear_exploration(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    rng: np.random.Generator,
    max_rounds: int,
    *,
    beta_start: float = 1.0,
    beta_end: float = 24.0,
    fitness: str = FITNESS_MARGINAL,
) -> int:
    """Run a finite annealed atomic LLL horizon before strict BR polishing."""

    if max_rounds <= 0:
        return 0
    n = len(register.assignment)
    rounds = 0
    while rounds < max_rounds:
        for robot in rng.permutation(n):
            if rounds >= max_rounds:
                break
            fraction = rounds / max(max_rounds - 1, 1)
            beta = beta_start + fraction * (beta_end - beta_start)
            options = _transition_options(int(robot), register, tokens, fitness)
            losses = np.asarray([option[2] for option in options], dtype=float)
            logits = -beta * losses
            logits -= float(np.max(logits))
            weights = np.exp(np.clip(logits, -700.0, 0.0))
            probabilities = weights / weights.sum()
            selected = options[int(rng.choice(len(options), p=probabilities))]
            proposal = selected[1]
            rounds += 1
            if proposal is not None:
                _submit(proposal, register, ledger)
    return rounds


def connected_triples(adjacency: np.ndarray) -> tuple[tuple[int, int, int], ...]:
    """Return all three-robot subsets whose induced graph is connected."""

    adjacency = np.asarray(adjacency, dtype=bool)
    triples: list[tuple[int, int, int]] = []
    for triple in combinations(range(len(adjacency)), 3):
        subgraph = adjacency[np.ix_(triple, triple)]
        # A simple undirected graph on three vertices is connected iff it has
        # at least two edges and no isolated vertex.
        degrees = subgraph.sum(axis=1)
        if int(subgraph.sum() // 2) >= 2 and bool(np.all(degrees > 0)):
            triples.append(tuple(int(robot) for robot in triple))
    return tuple(triples)


def _sequential_triples(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    adjacency: np.ndarray,
    max_rounds: int,
) -> tuple[int, bool]:
    triples = list(connected_triples(adjacency))
    triples.sort(
        key=lambda group: (
            tuple(sorted(int(tokens[robot]) for robot in group)),
            group,
        )
    )
    if not triples:
        return 0, False
    quiet = 0
    rounds = 0
    changed = False
    while rounds < max_rounds and quiet < len(triples):
        group = triples[rounds % len(triples)]
        rounds += 1
        if not ledger.record_group_exchange(group):
            quiet += 1
            continue
        proposal = _best_group(group, register, tokens)
        if proposal is None:
            quiet += 1
            continue
        accepted, _ = _submit(proposal, register, ledger)
        if accepted:
            quiet = 0
            changed = True
        else:
            quiet += 1
    return rounds, changed


def _conflict_free_batch(
    proposals: Iterable[MoveProposal],
    register: QuotaRegister,
    ledger: MessageLedger,
) -> tuple[int, int]:
    """Commit a deterministic maximal subset with disjoint load sets."""

    candidates = sorted(proposals, key=_candidate_key)
    selected: list[MoveProposal] = []
    used_loads: set[int] = set()
    used_robots: set[int] = set()
    for proposal in candidates:
        if used_loads.intersection(proposal.touched_loads):
            continue
        if used_robots.intersection(proposal.robot_ids):
            continue
        selected.append(proposal)
        used_loads.update(proposal.touched_loads)
        used_robots.update(proposal.robot_ids)

    accepted = 0
    # Every candidate reaches the arbiters; only the selected disjoint set is
    # allowed to commit.  Rejected conflicts do not mutate a register.
    selected_ids = {id(item) for item in selected}
    for proposal in candidates:
        reachable = ledger.record_proposal(proposal)
        if id(proposal) not in selected_ids:
            register._record_rejection(
                proposal, register.deficit, register.distance, "CONFLICTING_PROPOSAL"
            )
            continue
        if not reachable:
            register._record_rejection(
                proposal, register.deficit, register.distance, "UNREACHABLE_REGISTER"
            )
            continue
        ok, _ = register.commit(proposal)
        if ok:
            ledger.record_updates(proposal)
            accepted += 1
    return accepted, len(selected)


def proposals_conflict(left: MoveProposal, right: MoveProposal) -> bool:
    """Whether two proposals compete for a robot or a quota register."""

    return bool(
        set(left.robot_ids).intersection(right.robot_ids)
        or set(left.touched_loads).intersection(right.touched_loads)
    )


def _local_priority(proposal: MoveProposal) -> tuple[object, ...]:
    return (
        *_candidate_key(proposal),
        proposal.robot_ids,
        proposal.new_actions,
        proposal.touched_loads,
    )


def distributed_mis_indices(
    proposals: Sequence[MoveProposal],
) -> tuple[tuple[int, ...], int]:
    """Select a maximal conflict-free set by repeated local minima.

    Each candidate compares its immutable priority only with conflicting
    candidates.  The routine is a deterministic event-simulator of that local
    rule; it never constructs a global proposal ordering.
    """

    candidates = tuple(proposals)
    neighbours: list[set[int]] = [set() for _ in candidates]
    for left, right in combinations(range(len(candidates)), 2):
        if proposals_conflict(candidates[left], candidates[right]):
            neighbours[left].add(right)
            neighbours[right].add(left)
    keys = [_local_priority(proposal) for proposal in candidates]
    if len(set(keys)) != len(keys):
        raise ValueError("proposal priorities must be unique within one epoch")

    pending = set(range(len(candidates)))
    selected: list[int] = []
    iterations = 0
    while pending:
        iterations += 1
        winners = [
            index
            for index in pending
            if all(
                keys[index] < keys[other]
                for other in neighbours[index].intersection(pending)
            )
        ]
        if not winners:
            raise AssertionError("unique local priorities must produce a winner")
        selected.extend(winners)
        blocked = set(winners)
        for winner in winners:
            blocked.update(neighbours[winner])
        pending.difference_update(blocked)
    return tuple(selected), iterations


@dataclass(slots=True)
class TransactionCoordinator:
    """Prepare/commit/abort state machine driven by the proposal's robot.

    The simulator stores the ground-truth registers in one object solely to
    verify invariants.  A transaction decision is made from versioned READY
    replies of the touched keepers; it does not inspect unrelated loads or the
    fleet assignment profile.  ``proposal.coordinator`` is the lowest-ID robot
    in that proposal and coordinates only that transaction.  It is not a fleet
    coordinator, leader, or persistent service.
    """

    register: QuotaRegister
    ledger: MessageLedger
    locks: np.ndarray = field(init=False)
    next_tx_id: int = 1
    prepared: int = 0
    committed: int = 0
    aborted: int = 0

    def __post_init__(self) -> None:
        self.locks = np.full(len(self.register.demands), -1, dtype=np.int64)

    def _decision(self, proposal: MoveProposal, nbytes: int) -> None:
        for load in proposal.touched_loads:
            keeper = int(self.ledger.keepers[load])
            self.ledger.record_transaction_leg(
                proposal.coordinator, keeper, nbytes
            )

    def prepare_commit(self, proposal: MoveProposal) -> tuple[bool, str]:
        tx_id = self.next_tx_id
        self.next_tx_id += 1
        acquired: list[int] = []
        for load, expected in zip(
            proposal.touched_loads, proposal.expected_versions, strict=True
        ):
            keeper = int(self.ledger.keepers[load])
            if not self.ledger.record_transaction_leg(
                proposal.coordinator, keeper, TX_PREPARE_BYTES
            ):
                self._abort(proposal, acquired, "UNREACHABLE_PREPARE")
                return False, "UNREACHABLE_PREPARE"
            current_lock = int(self.locks[load])
            version_ok = int(self.register.versions[load]) == int(expected)
            lock_ok = current_lock in {-1, tx_id}
            self.ledger.record_transaction_leg(
                keeper, proposal.coordinator, TX_REPLY_BYTES
            )
            if not (version_ok and lock_ok):
                reason = "STALE_VERSION" if not version_ok else "LOCKED_REGISTER"
                self._abort(proposal, acquired, reason)
                return False, reason
            self.locks[load] = tx_id
            acquired.append(load)

        self.prepared += 1
        accepted, reason = self.register.commit(proposal)
        if not accepted:
            self._abort(proposal, acquired, reason, record=False)
            return False, reason
        self._decision(proposal, TX_DECISION_BYTES)
        for load in acquired:
            self.locks[load] = -1
        self.ledger.record_updates(proposal)
        self.committed += 1
        return True, "COMMITTED"

    def _abort(
        self,
        proposal: MoveProposal,
        acquired: Sequence[int],
        reason: str,
        *,
        record: bool = True,
    ) -> None:
        self._decision(proposal, TX_DECISION_BYTES)
        for load in acquired:
            self.locks[load] = -1
        if record:
            self.register._record_rejection(
                proposal, self.register.deficit, self.register.distance, reason
            )
        self.aborted += 1


def _distributed_mis_batch(
    proposals: Iterable[MoveProposal],
    register: QuotaRegister,
    ledger: MessageLedger,
    transactions: TransactionCoordinator,
) -> tuple[int, int, int]:
    """Arbitrate locally and commit a maximal non-conflicting proposal set."""

    candidates: list[MoveProposal] = []
    for proposal in proposals:
        if ledger.record_proposal(proposal):
            candidates.append(proposal)
        else:
            register._record_rejection(
                proposal, register.deficit, register.distance, "UNREACHABLE_REGISTER"
            )
    for left, right in combinations(candidates, 2):
        if proposals_conflict(left, right):
            ledger.record_arbitration(left, right)
    selected_indices, iterations = distributed_mis_indices(candidates)
    selected = set(selected_indices)
    accepted = 0
    for index, proposal in enumerate(candidates):
        if index not in selected:
            register._record_rejection(
                proposal, register.deficit, register.distance, "CONFLICTING_PROPOSAL"
            )
            continue
        ok, _ = transactions.prepare_commit(proposal)
        accepted += int(ok)
    return accepted, len(selected), iterations


def _parallel_unilateral(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    max_batches: int,
) -> tuple[int, int]:
    batches = 0
    max_parallel = 0
    while batches < max_batches:
        proposals = [
            proposal
            for robot in range(len(register.assignment))
            if (proposal := _best_unilateral(robot, register, tokens)) is not None
        ]
        batches += 1
        if not proposals:
            break
        accepted, selected = _conflict_free_batch(proposals, register, ledger)
        max_parallel = max(max_parallel, accepted)
        if accepted == 0:
            break
    return batches, max_parallel


def _parallel_pairs(
    register: QuotaRegister,
    ledger: MessageLedger,
    tokens: np.ndarray,
    adjacency: np.ndarray,
    max_batches: int,
) -> tuple[int, int]:
    edges = [
        (int(i), int(j))
        for i, j in combinations(range(len(adjacency)), 2)
        if adjacency[i, j]
    ]
    if not edges:
        return 0, 0
    batches = 0
    max_parallel = 0
    while batches < max_batches:
        ledger.record_pair_broadcast()
        proposals = [
            proposal
            for left, right in edges
            if (proposal := _best_pair(left, right, register, tokens)) is not None
        ]
        batches += 1
        if not proposals:
            break
        accepted, _ = _conflict_free_batch(proposals, register, ledger)
        max_parallel = max(max_parallel, accepted)
        if accepted == 0:
            break
    return batches, max_parallel


def _distributed_parallel_unilateral(
    register: QuotaRegister,
    ledger: MessageLedger,
    transactions: TransactionCoordinator,
    tokens: np.ndarray,
    max_batches: int,
) -> tuple[int, int, int]:
    batches = 0
    max_parallel = 0
    mis_iterations = 0
    while batches < max_batches:
        proposals = [
            proposal
            for robot in range(len(register.assignment))
            if (proposal := _best_unilateral(robot, register, tokens)) is not None
        ]
        batches += 1
        if not proposals:
            break
        accepted, _, iterations = _distributed_mis_batch(
            proposals, register, ledger, transactions
        )
        mis_iterations += iterations
        max_parallel = max(max_parallel, accepted)
        if accepted == 0:
            break
    return batches, max_parallel, mis_iterations


def _distributed_parallel_pairs(
    register: QuotaRegister,
    ledger: MessageLedger,
    transactions: TransactionCoordinator,
    tokens: np.ndarray,
    adjacency: np.ndarray,
    max_batches: int,
) -> tuple[int, int, int]:
    edges = [
        (int(i), int(j))
        for i, j in combinations(range(len(adjacency)), 2)
        if adjacency[i, j]
    ]
    if not edges:
        return 0, 0, 0
    batches = 0
    max_parallel = 0
    mis_iterations = 0
    while batches < max_batches:
        ledger.record_pair_broadcast()
        proposals = [
            proposal
            for left, right in edges
            if (proposal := _best_pair(left, right, register, tokens)) is not None
        ]
        batches += 1
        if not proposals:
            break
        accepted, _, iterations = _distributed_mis_batch(
            proposals, register, ledger, transactions
        )
        mis_iterations += iterations
        max_parallel = max(max_parallel, accepted)
        if accepted == 0:
            break
    return batches, max_parallel, mis_iterations


def _improving_unilateral_exists(register: QuotaRegister, tokens: np.ndarray) -> bool:
    return any(
        _best_unilateral(robot, register, tokens) is not None
        for robot in range(len(register.assignment))
    )


def _improving_pair_exists(
    register: QuotaRegister, tokens: np.ndarray, adjacency: np.ndarray
) -> bool:
    return any(
        _best_pair(int(i), int(j), register, tokens) is not None
        for i, j in combinations(range(len(adjacency)), 2)
        if adjacency[i, j]
    )


def _improving_triple_exists(
    register: QuotaRegister, tokens: np.ndarray, adjacency: np.ndarray
) -> bool:
    return any(
        _best_group(group, register, tokens) is not None
        for group in connected_triples(adjacency)
    )


@dataclass(frozen=True, slots=True)
class RunResult:
    method: str
    assignment: np.ndarray
    certificate: Certificate
    algorithm_status: str
    terminal_phase: str
    runtime_ms: float
    rounds: int
    messages: int
    bytes_sent: int
    commits: int
    quota_commits: int
    geometry_commits: int
    rejected_stale: int
    rejected_conflict: int
    unreachable_messages: int
    arbitration_messages: int
    transaction_messages: int
    transaction_aborts: int
    mis_iterations: int
    max_parallel_commits: int
    unilateral_local_minimum: bool
    pair_local_minimum: bool
    triple_local_minimum: bool
    potential_monotone: bool
    graph: dict[str, float | int | bool]
    event_history: tuple[CommitEvent, ...]

    def as_dict(self) -> dict[str, object]:
        row: dict[str, object] = {
            "method": self.method,
            "algorithm_status": self.algorithm_status,
            "terminal_phase": self.terminal_phase,
            "runtime_ms": self.runtime_ms,
            "rounds": self.rounds,
            "messages": self.messages,
            "bytes": self.bytes_sent,
            "commits": self.commits,
            "quota_commits": self.quota_commits,
            "geometry_commits": self.geometry_commits,
            "rejected_stale": self.rejected_stale,
            "rejected_conflict": self.rejected_conflict,
            "unreachable_messages": self.unreachable_messages,
            "arbitration_messages": self.arbitration_messages,
            "transaction_messages": self.transaction_messages,
            "transaction_aborts": self.transaction_aborts,
            "mis_iterations": self.mis_iterations,
            "max_parallel_commits": self.max_parallel_commits,
            "unilateral_local_minimum": self.unilateral_local_minimum,
            "pair_local_minimum": self.pair_local_minimum,
            "triple_local_minimum": self.triple_local_minimum,
            "potential_monotone": self.potential_monotone,
        }
        row.update(self.certificate.as_dict())
        row.update({f"graph_{key}": value for key, value in self.graph.items()})
        return row


def run_geo_qpg(
    world: World,
    adjacency: np.ndarray,
    method: str,
    *,
    max_rounds: int | None = None,
    initial_assignment: np.ndarray | None = None,
    fitness: str = FITNESS_MARGINAL,
) -> RunResult:
    """Run one Geo-QPG variant on one frozen N2/N3 world.

    ``fitness`` selecciona con que escalar se ordenan los candidatos dentro de
    la vecindad. El valor por defecto reproduce las campanas publicadas. Solo
    tiene efecto en las variantes de orden h = 1, que son las del factorial
    N3.B; las de orden superior lo ignoran.
    """

    if fitness not in FITNESS:
        raise KeyError(f"unknown fitness: {fitness}")

    import time

    if method not in METHODS:
        raise KeyError(f"unknown Geo-QPG method: {method}")
    started = time.perf_counter()
    adjacency = np.asarray(adjacency, dtype=bool)
    if initial_assignment is not None:
        initial_assignment = np.asarray(initial_assignment, dtype=int)
        if initial_assignment.shape != (world.n_robots,):
            raise ValueError(
                f"initial_assignment must have shape {(world.n_robots,)}"
            )
        if np.any((initial_assignment < -1) | (initial_assignment >= world.n_loads)):
            raise ValueError("initial_assignment contains an invalid load index")
    register = QuotaRegister(
        world.demands,
        world.capacities,
        world.distances,
        assignment=initial_assignment,
    )
    ledger = MessageLedger(adjacency, world.n_loads)
    transactions = TransactionCoordinator(register, ledger)
    tokens = np.asarray(
        priority_tokens(world.seed, world.capacities, world.robot_positions),
        dtype=np.uint64,
    )
    budget = int(max_rounds or max(32 * world.n_robots, 512))
    rounds = 0
    max_parallel = 1
    mis_iterations = 0
    seen = {_state_signature(register)}
    status = "LOCAL_MINIMUM"

    if method == "geo_qpg_u":
        used, _ = _sequential_unilateral(
            register, ledger, tokens, max(budget - rounds, 0), fitness
        )
        rounds += used
    elif method == "geo_qpg_smith":
        rng = np.random.default_rng(world.seed ^ 0x534D495448)
        used, _ = _smith_atomic_unilateral(
            register, ledger, tokens, rng, max(budget - rounds, 0), fitness
        )
        rounds += used
    elif method == "geo_qpg_lll":
        rng = np.random.default_rng(world.seed ^ 0x4C4C4C)
        exploration_budget = min(
            max(8 * world.n_robots, 1), max(budget // 2, 1)
        )
        rounds += _log_linear_exploration(
            register,
            ledger,
            tokens,
            rng,
            min(exploration_budget, max(budget - rounds, 0)),
            fitness=fitness,
        )
        used, _ = _sequential_unilateral(
            register, ledger, tokens, max(budget - rounds, 0), fitness
        )
        rounds += used
    elif method == "geo_qpg_p":
        while rounds < budget:
            u_rounds, u_changed = _sequential_unilateral(
                register, ledger, tokens, max(budget - rounds, 0), fitness
            )
            rounds += u_rounds
            if rounds >= budget:
                break
            p_rounds, p_changed = _sequential_pairs(
                register,
                ledger,
                tokens,
                adjacency,
                max(budget - rounds, 0),
                fitness,
            )
            rounds += p_rounds
            if not u_changed and not p_changed:
                break
            signature = _state_signature(register)
            if signature in seen:
                raise AssertionError("strict-potential run revisited an assignment")
            seen.add(signature)
    elif method == "geo_qpg_c3":
        while rounds < budget:
            u_rounds, u_changed = _sequential_unilateral(
                register, ledger, tokens, max(budget - rounds, 0)
            )
            rounds += u_rounds
            if rounds >= budget:
                break
            p_rounds, p_changed = _sequential_pairs(
                register,
                ledger,
                tokens,
                adjacency,
                max(budget - rounds, 0),
            )
            rounds += p_rounds
            if rounds >= budget:
                break
            c_rounds, c_changed = _sequential_triples(
                register,
                ledger,
                tokens,
                adjacency,
                max(budget - rounds, 0),
            )
            rounds += c_rounds
            if not u_changed and not p_changed and not c_changed:
                break
            signature = _state_signature(register)
            if signature in seen:
                raise AssertionError("strict-potential run revisited an assignment")
            seen.add(signature)
    elif method == "geo_qpg_cf":
        while rounds < budget:
            u_batches, u_parallel = _parallel_unilateral(
                register, ledger, tokens, max(budget - rounds, 0)
            )
            rounds += u_batches
            max_parallel = max(max_parallel, u_parallel)
            if rounds >= budget:
                break
            p_batches, p_parallel = _parallel_pairs(
                register,
                ledger,
                tokens,
                adjacency,
                max(budget - rounds, 0),
            )
            rounds += p_batches
            max_parallel = max(max_parallel, p_parallel)
            if u_parallel == 0 and p_parallel == 0:
                break
            signature = _state_signature(register)
            if signature in seen:
                raise AssertionError("strict-potential run revisited an assignment")
            seen.add(signature)
    else:  # Geo-QPG-DMIS+TX
        while rounds < budget:
            u_batches, u_parallel, u_mis = _distributed_parallel_unilateral(
                register,
                ledger,
                transactions,
                tokens,
                max(budget - rounds, 0),
            )
            rounds += u_batches
            mis_iterations += u_mis
            max_parallel = max(max_parallel, u_parallel)
            if rounds >= budget:
                break
            p_batches, p_parallel, p_mis = _distributed_parallel_pairs(
                register,
                ledger,
                transactions,
                tokens,
                adjacency,
                max(budget - rounds, 0),
            )
            rounds += p_batches
            mis_iterations += p_mis
            max_parallel = max(max_parallel, p_parallel)
            if u_parallel == 0 and p_parallel == 0:
                break
            signature = _state_signature(register)
            if signature in seen:
                raise AssertionError("strict-potential run revisited an assignment")
            seen.add(signature)

    if rounds >= budget:
        status = "MAX_ROUNDS"
    certificate = certify(
        register.assignment, world.capacities, world.demands, world.distances
    )
    accepted = [event for event in register.events if event.accepted]
    quota_events = [event for event in accepted if event.phase == PHASE_QUOTA]
    geometry_events = [event for event in accepted if event.phase == PHASE_GEOMETRY]
    monotone = all(
        (
            event.deficit_after < event.deficit_before - TOLERANCE
            if event.phase == PHASE_QUOTA
            else abs(event.deficit_after) <= TOLERANCE
            and event.distance_after < event.distance_before - TOLERANCE
        )
        for event in accepted
    )
    unilateral_min = not _improving_unilateral_exists(register, tokens)
    pair_min = (
        not _improving_pair_exists(register, tokens, adjacency)
        if method in {"geo_qpg_p", "geo_qpg_cf", "geo_qpg_c3", "geo_qpg_d"}
        else False
    )
    triple_min = (
        not _improving_triple_exists(register, tokens, adjacency)
        if method == "geo_qpg_c3"
        else False
    )
    return RunResult(
        method=method,
        assignment=register.assignment.copy(),
        certificate=certificate,
        algorithm_status=status,
        terminal_phase=register.phase,
        runtime_ms=1_000.0 * (time.perf_counter() - started),
        rounds=rounds,
        messages=ledger.messages,
        bytes_sent=ledger.bytes_sent,
        commits=len(accepted),
        quota_commits=len(quota_events),
        geometry_commits=len(geometry_events),
        rejected_stale=sum(event.reason == "STALE_VERSION" for event in register.events),
        rejected_conflict=sum(
            event.reason == "CONFLICTING_PROPOSAL" for event in register.events
        ),
        unreachable_messages=ledger.unreachable,
        arbitration_messages=ledger.arbitration_messages,
        transaction_messages=ledger.transaction_messages,
        transaction_aborts=transactions.aborted,
        mis_iterations=mis_iterations,
        max_parallel_commits=max_parallel,
        unilateral_local_minimum=unilateral_min,
        pair_local_minimum=pair_min,
        triple_local_minimum=triple_min,
        potential_monotone=monotone,
        graph=graph_metrics(adjacency).as_dict(),
        event_history=tuple(register.events),
    )


__all__ = [
    "METHODS",
    "LEGACY_METHODS",
    "METHOD_LABELS",
    "CoordinationOrderResult",
    "MoveProposal",
    "PHASE_GEOMETRY",
    "PHASE_QUOTA",
    "QuotaRegister",
    "RunResult",
    "TransactionCoordinator",
    "affected_loads",
    "assignment_distance",
    "build_proposal",
    "build_transition_proposal",
    "connected_triples",
    "deficit_from_coverage",
    "marginal_changes",
    "minimum_improving_coalition_order",
    "distributed_mis_indices",
    "proposals_conflict",
    "run_geo_qpg",
]
