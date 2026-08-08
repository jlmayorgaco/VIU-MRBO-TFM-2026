"""Run one method on one world and one graph, and record what happened.

The record keeps the review's status fields separate. ``algorithm_status``
describes the execution, ``raw_certificate`` the allocation the method actually
produced, and ``oracle_status`` the N2 MILP -- three different things that the
first draft collapsed into one enum. ``recovery_applied`` is present and always
false: N3 confirmatory v1 reports RAW as the primary endpoint, and a shared
local repair is a separate extension that N4 would have to inherit unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from . import capacity_cbba, weighted_grape
from .certificate import Certificate, certify
from .contract import Channel, LoadCatalog, Observation, priority_tokens, run_rounds
from .graph import graph_metrics
from .worlds import World


METHODS = ("capacity_cbba", "weighted_grape", "weighted_pair_grape")

METHOD_LABELS = {
    "capacity_cbba": "Capacity-CBBA",
    "weighted_grape": "Weighted-GRAPE",
    "weighted_pair_grape": "Weighted-Pair-GRAPE",
}


@dataclass(frozen=True, slots=True)
class RunRecord:
    world_id: str
    method: str
    regime: str
    assignment: np.ndarray
    certificate: Certificate
    observation: Observation
    graph: dict[str, Any]
    runtime_ms: float

    def as_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "world_id": self.world_id,
            "method": self.method,
            "graph_regime": self.regime,
            "recovery_applied": False,
            "recovered_certificate": None,
            "runtime_ms": self.runtime_ms,
        }
        row.update(self.observation.as_dict())
        row.update(self.certificate.as_dict())
        row.update({f"graph_{key}": value for key, value in self.graph.items()})
        return row


def default_max_rounds(method: str, n_robots: int, *, epochs: int = 0) -> int:
    """Round budget, stated rather than discovered.

    GRAPE needs one handshake round plus ``N`` rounds per epoch; the number of
    epochs is bounded by how many strict improvements the profile admits, which
    is not known in advance, so the budget is an explicit cap and hitting it is
    reported as MAX_ROUNDS rather than treated as convergence.
    """

    if method == "capacity_cbba":
        return max(8 * n_robots, 64)
    budget = epochs or max(4 * n_robots, 40)
    return 1 + budget * weighted_grape.epoch_length(n_robots)


def run_method(
    world: World,
    adjacency: np.ndarray,
    method: str,
    *,
    regime: str = "unspecified",
    channel: Channel | None = None,
    max_rounds: int | None = None,
) -> RunRecord:
    import time

    if method not in METHODS:
        raise KeyError(f"unknown method: {method}")
    catalog = LoadCatalog(positions=world.load_positions, demands=world.demands)
    tokens = priority_tokens(world.seed, world.capacities, world.robot_positions)
    budget = max_rounds or default_max_rounds(method, world.n_robots)

    if method == "capacity_cbba":
        init = capacity_cbba.initial_state
        step = capacity_cbba.step
        extract = capacity_cbba.extract_assignment
        # Silence is only meaningful once a full retransmission cycle has gone
        # by without changing anything. A shorter window can declare quiescence
        # in the gap between heartbeats, while a record dropped earlier is still
        # waiting to be repaired.
        window = capacity_cbba.heartbeat_period(world.n_robots) + 1
        # The adaptation has no termination proof and the pilot shows it can
        # cycle, so the observer watches the commitment vector for repeats.
        signature = capacity_cbba.commitment_signature
        # Each CBBA robot owns only its own commitment, so there is no shared
        # profile that could diverge; nothing to check.
        consistency = None
    else:
        init = weighted_grape.initial_state
        step = weighted_grape.make_step(pair_moves=method == "weighted_pair_grape")
        extract = weighted_grape.extract_assignment
        # Mid-epoch silence is not quiescence: a robot with nothing new to
        # forward correctly sends nothing while the flood completes, and the
        # profile only changes on the epoch's last round. The observer must
        # therefore wait longer than a full epoch before calling it done.
        window = weighted_grape.epoch_length(world.n_robots) + 2
        # A strictly improving potential cannot revisit a profile, so a repeat
        # would be a bug rather than a limit cycle; watched anyway.
        signature = weighted_grape.profile_signature
        # The epoch argument needs every robot to hold the same profile. Checked,
        # never assumed: see weighted_grape.profiles_agree.
        consistency = weighted_grape.profiles_agree

    started = time.perf_counter()
    states, observation = run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=catalog,
        adjacency=adjacency,
        init=init,
        step=step,
        max_rounds=budget,
        priority_tokens=tokens,
        channel=channel,
        quiescence_window=window,
        signature=signature,
        consistency=consistency,
    )
    elapsed = 1_000.0 * (time.perf_counter() - started)
    assignment = extract(states, world.n_robots)
    certificate = certify(
        assignment, world.capacities, world.demands, world.distances
    )
    return RunRecord(
        world_id=world.world_id,
        method=method,
        regime=regime,
        assignment=assignment,
        certificate=certificate,
        observation=observation,
        graph=graph_metrics(adjacency).as_dict(),
        runtime_ms=elapsed,
    )


__all__ = ["METHODS", "METHOD_LABELS", "RunRecord", "default_max_rounds", "run_method"]
