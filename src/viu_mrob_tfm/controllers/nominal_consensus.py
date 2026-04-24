"""Placeholder nominal consensus controller."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.controllers.base import BaseController
from viu_mrob_tfm.domain.graph import CommunicationGraph
from viu_mrob_tfm.domain.state import SystemState


class NominalConsensusController(BaseController):
    """Baseline distributed controller using local consensus information."""

    def __init__(
        self,
        graph: CommunicationGraph,
        consensus_gain: float = 1.0,
        tracking_gain: float = 0.5,
    ) -> None:
        super().__init__(name="nominal_consensus", dimensions=2)
        self.graph = graph
        self.consensus_gain = consensus_gain
        self.tracking_gain = tracking_gain

    def compute_control(self, state: SystemState) -> NDArray[np.float64]:
        """Return a placeholder control action with the expected shape."""

        _ = self.graph.laplacian_matrix()
        # TODO: Replace the zero action with the nominal distributed consensus law.
        return np.zeros((state.agent_count, self.dimensions), dtype=float)
