"""Placeholder adaptive or robust consensus controller."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.controllers.base import BaseController
from viu_mrob_tfm.domain.graph import CommunicationGraph
from viu_mrob_tfm.domain.state import SystemState
from viu_mrob_tfm.estimators.base import BaseEstimator


class AdaptiveConsensusController(BaseController):
    """Distributed controller reserved for adaptive/robust extensions."""

    def __init__(
        self,
        graph: CommunicationGraph,
        estimator: BaseEstimator | None = None,
        adaptation_gain: float = 0.2,
    ) -> None:
        super().__init__(name="adaptive_consensus", dimensions=2)
        self.graph = graph
        self.estimator = estimator
        self.adaptation_gain = adaptation_gain

    def compute_control(self, state: SystemState) -> NDArray[np.float64]:
        """Return a placeholder control action using the estimator hook."""

        if self.estimator is not None:
            self.estimator.update(state)
        # TODO: Couple the consensus baseline with the uncertainty adaptation law.
        return self.zero_control(agent_count=state.agent_count)
