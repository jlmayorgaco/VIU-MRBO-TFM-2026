"""Smoke tests for communication graph helpers."""

import numpy as np

from viu_mrob_tfm.domain import CommunicationGraph


def test_graph_adjacency_and_laplacian_shape() -> None:
    graph = CommunicationGraph(
        np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 1.0],
                [0.0, 1.0, 0.0],
            ]
        )
    )

    adjacency = graph.adjacency
    laplacian = graph.laplacian_matrix()

    assert adjacency.shape == (3, 3)
    assert laplacian.shape == (3, 3)
    assert graph.neighbors(1) == [0, 2]
