"""Communication graph utilities for local multi-AGV coordination."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class CommunicationGraph:
    """Undirected weighted graph represented by an adjacency matrix."""

    adjacency: NDArray[np.float64]

    def __post_init__(self) -> None:
        adjacency = np.asarray(self.adjacency, dtype=float)
        if adjacency.ndim != 2 or adjacency.shape[0] != adjacency.shape[1]:
            msg = "adjacency must be a square matrix."
            raise ValueError(msg)
        self.adjacency = adjacency

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""

        return int(self.adjacency.shape[0])

    def degree_matrix(self) -> NDArray[np.float64]:
        """Return the degree matrix."""

        degrees = np.sum(self.adjacency, axis=1)
        return np.diag(degrees)

    def laplacian_matrix(self) -> NDArray[np.float64]:
        """Return the combinatorial Laplacian."""

        return self.degree_matrix() - self.adjacency

    def neighbors(self, node_index: int) -> list[int]:
        """Return indices of adjacent nodes."""

        if not 0 <= node_index < self.node_count:
            msg = f"Node index {node_index} is out of range."
            raise IndexError(msg)
        return [idx for idx, value in enumerate(self.adjacency[node_index]) if value > 0]
