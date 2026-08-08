"""R-disk communication graphs and the metrics that select their regimes.

Regimes are chosen by graph metrics alone -- never by how well a method scores
on them -- and by a multiplier of the *critical radius* rather than a fixed
radius in metres, because a fixed radius changes the mean degree drastically
as N grows.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree


@dataclass(frozen=True, slots=True)
class GraphMetrics:
    n_edges: int
    mean_degree: float
    min_degree: int
    diameter: int  # -1 when disconnected
    components: int
    algebraic_connectivity: float
    connected: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "n_edges": self.n_edges,
            "mean_degree": self.mean_degree,
            "min_degree": self.min_degree,
            "diameter": self.diameter,
            "components": self.components,
            "lambda_2": self.algebraic_connectivity,
            "connected": self.connected,
        }


def pairwise_distances(positions: np.ndarray) -> np.ndarray:
    positions = np.asarray(positions, dtype=float)
    return np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)


def critical_radius(positions: np.ndarray) -> float:
    """Smallest radius whose R-disk graph is connected.

    That is exactly the largest edge of the Euclidean minimum spanning tree:
    below it some MST edge is missing and the graph splits; at it the tree is
    contained in the R-disk graph.
    """

    positions = np.asarray(positions, dtype=float)
    if len(positions) <= 1:
        return 0.0
    tree = minimum_spanning_tree(pairwise_distances(positions)).toarray()
    return float(tree.max())


def r_disk_adjacency(positions: np.ndarray, radius: float) -> np.ndarray:
    distances = pairwise_distances(positions)
    adjacency = distances <= float(radius)
    np.fill_diagonal(adjacency, False)
    return adjacency


def complete_adjacency(n_robots: int) -> np.ndarray:
    adjacency = np.ones((n_robots, n_robots), dtype=bool)
    np.fill_diagonal(adjacency, False)
    return adjacency


def components(adjacency: np.ndarray) -> list[list[int]]:
    adjacency = np.asarray(adjacency, dtype=bool)
    n = len(adjacency)
    seen = np.zeros(n, dtype=bool)
    found: list[list[int]] = []
    for start in range(n):
        if seen[start]:
            continue
        stack = [start]
        seen[start] = True
        block = []
        while stack:
            node = stack.pop()
            block.append(node)
            for neighbor in np.flatnonzero(adjacency[node]):
                if not seen[neighbor]:
                    seen[neighbor] = True
                    stack.append(int(neighbor))
        found.append(sorted(block))
    return found


def diameter(adjacency: np.ndarray) -> int:
    """Graph diameter, or ``-1`` when the graph is disconnected.

    Recorded by the observer only. No algorithm in this package may read it:
    that is precisely what invalidated the inherited CBBA implementation.
    """

    adjacency = np.asarray(adjacency, dtype=bool)
    n = len(adjacency)
    if n <= 1:
        return 0
    longest = 0
    for source in range(n):
        distances = np.full(n, -1, dtype=int)
        distances[source] = 0
        queue = [source]
        head = 0
        while head < len(queue):
            node = queue[head]
            head += 1
            for neighbor in np.flatnonzero(adjacency[node]):
                if distances[neighbor] < 0:
                    distances[neighbor] = distances[node] + 1
                    queue.append(int(neighbor))
        if np.any(distances < 0):
            return -1
        longest = max(longest, int(distances.max()))
    return longest


def algebraic_connectivity(adjacency: np.ndarray) -> float:
    adjacency = np.asarray(adjacency, dtype=float)
    n = len(adjacency)
    if n <= 1:
        return 0.0
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    eigenvalues = np.linalg.eigvalsh(laplacian)
    return float(np.sort(eigenvalues)[1])


def graph_metrics(adjacency: np.ndarray) -> GraphMetrics:
    adjacency = np.asarray(adjacency, dtype=bool)
    degrees = adjacency.sum(axis=1)
    blocks = components(adjacency)
    return GraphMetrics(
        n_edges=int(adjacency.sum() // 2),
        mean_degree=float(degrees.mean()) if len(degrees) else 0.0,
        min_degree=int(degrees.min()) if len(degrees) else 0,
        diameter=diameter(adjacency),
        components=len(blocks),
        algebraic_connectivity=algebraic_connectivity(adjacency),
        connected=len(blocks) == 1,
    )


# Regime names are fixed here so E3 cannot silently redefine them later.
REGIME_MULTIPLIERS: dict[str, float | None] = {
    "complete": None,  # not an R-disk graph
    "dense": 2.00,
    "medium": 1.50,
    "threshold": 1.05,
    "partitioned": 0.95,  # negative control, never in the connected Pareto front
}

CONNECTED_REGIMES = ("complete", "dense", "medium", "threshold")
NEGATIVE_CONTROL = "partitioned"


def adjacency_for_regime(positions: np.ndarray, regime: str) -> np.ndarray:
    if regime not in REGIME_MULTIPLIERS:
        raise KeyError(f"unknown graph regime: {regime}")
    if regime == "complete":
        return complete_adjacency(len(positions))
    multiplier = REGIME_MULTIPLIERS[regime]
    assert multiplier is not None
    return r_disk_adjacency(positions, multiplier * critical_radius(positions))


__all__ = [
    "CONNECTED_REGIMES",
    "GraphMetrics",
    "NEGATIVE_CONTROL",
    "REGIME_MULTIPLIERS",
    "adjacency_for_regime",
    "algebraic_connectivity",
    "complete_adjacency",
    "components",
    "critical_radius",
    "diameter",
    "graph_metrics",
    "pairwise_distances",
    "r_disk_adjacency",
]
