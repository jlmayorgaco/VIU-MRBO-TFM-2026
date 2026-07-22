"""White-box distributed deficit/cost auction used as an SP1 baseline.

The implementation is deliberately modest: each load repeatedly requests a
robot whose normalized marginal deficit reduction per unit cost is maximal.
The winning bid is obtained by max-consensus over the static communication
graph.  It is an implemented proxy baseline, not CBBA and not a claim of
optimality.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import numpy as np

from viu_mrob_tfm.sp1_canonical.validation.dynamics import GraphInfo
from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld, normalized_constraints
from viu_mrob_tfm.sp1_canonical.validation.rounding import IntegerResult, evaluate_integer


@dataclass(frozen=True, slots=True)
class AuctionResult:
    integer: IntegerResult
    rounds: int
    runtime_s: float
    messages: int
    scalars_sent: int
    connected: bool
    status: str


def distributed_deficit_auction(
    world: ResourceWorld,
    costs: np.ndarray,
    graph: GraphInfo,
    *,
    max_awards: int | None = None,
) -> AuctionResult:
    """Allocate robots using neighbor max-consensus bids.

    A round advertises one scalar score and two integer identifiers per robot
    across each directed edge.  Loads are visited cyclically; after an award,
    the accepted robot and updated load coverage are common protocol state.
    This sequentialization is deterministic and makes paired runs reproducible.
    """

    start = time.perf_counter()
    assignment = np.full(world.n_robots, -1, dtype=int)
    normalized = normalized_constraints(world)
    coverage = np.zeros_like(world.requirements, dtype=float)
    coverage = coverage / np.maximum(world.requirements, 1e-12)
    max_awards = world.n_robots if max_awards is None else int(max_awards)
    consensus_rounds = _graph_diameter(graph.adjacency) if graph.connected else 0
    protocol_rounds = 0
    awards = 0

    while awards < max_awards:
        deficits = np.maximum(1.0 - coverage, 0.0)
        if np.all(deficits <= 1e-9):
            break
        awarded_this_cycle = False
        for load in range(world.n_loads):
            if float(np.sum(deficits[load])) <= 1e-9:
                continue
            local_scores = np.full(world.n_robots, -math.inf)
            for robot in np.flatnonzero(assignment < 0):
                if not np.isfinite(costs[robot, load]):
                    continue
                gain = float(np.sum(np.minimum(deficits[load], normalized[robot, load])))
                if gain > 1e-12:
                    local_scores[robot] = gain / max(float(costs[robot, load]), 1e-12)
            if not np.isfinite(local_scores).any():
                continue
            winner = _max_consensus_winner(local_scores, graph.adjacency, consensus_rounds)
            if winner < 0 or assignment[winner] >= 0:
                continue
            assignment[winner] = load
            coverage[load] += normalized[winner, load]
            awards += 1
            protocol_rounds += max(consensus_rounds, 1)
            awarded_this_cycle = True
            if awards >= max_awards:
                break
        if not awarded_this_cycle:
            break

    integer = evaluate_integer(world, assignment, costs)
    directed_messages = 2 * graph.edges * protocol_rounds
    status = "feasible" if integer.feasible else ("graph_disconnected" if not graph.connected else "auction_infeasible")
    return AuctionResult(
        integer=integer,
        rounds=protocol_rounds,
        runtime_s=float(time.perf_counter() - start),
        messages=int(directed_messages),
        scalars_sent=int(3 * directed_messages),
        connected=graph.connected,
        status=status,
    )


def _max_consensus_winner(scores: np.ndarray, adjacency: np.ndarray, rounds: int) -> int:
    values = np.asarray(scores, dtype=float).copy()
    identifiers = np.arange(len(values), dtype=int)
    for _ in range(max(int(rounds), 0)):
        next_values = values.copy()
        next_ids = identifiers.copy()
        for robot in range(len(values)):
            candidates = np.r_[robot, np.flatnonzero(adjacency[robot])]
            ordered = sorted(
                ((float(values[index]), -int(identifiers[index]), int(identifiers[index])) for index in candidates),
                reverse=True,
            )
            next_values[robot], _, next_ids[robot] = ordered[0]
        values, identifiers = next_values, next_ids
    finite = np.flatnonzero(np.isfinite(values))
    if finite.size == 0:
        return -1
    # Connected graphs agree.  The deterministic minimum breaks any numerical
    # tie and also makes a disconnected diagnostic reproducible.
    best_value = float(np.max(values[finite]))
    return int(np.min(identifiers[np.isclose(values, best_value, rtol=0.0, atol=1e-15)]))


def _graph_diameter(adjacency: np.ndarray) -> int:
    n = adjacency.shape[0]
    if n <= 1:
        return 0
    diameter = 0
    for source in range(n):
        distances = np.full(n, -1, dtype=int)
        distances[source] = 0
        queue = [source]
        for node in queue:
            for neighbour in np.flatnonzero(adjacency[node]):
                if distances[neighbour] < 0:
                    distances[neighbour] = distances[node] + 1
                    queue.append(int(neighbour))
        if np.any(distances < 0):
            return 0
        diameter = max(diameter, int(np.max(distances)))
    return diameter


__all__ = ["AuctionResult", "distributed_deficit_auction"]
