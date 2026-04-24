"""Abstract controller contract for the simulation pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.domain.state import SystemState


class BaseController(ABC):
    """Base interface for distributed cooperative transport controllers."""

    def __init__(self, name: str, dimensions: int = 2) -> None:
        self.name = name
        self.dimensions = dimensions

    def zero_control(self, agent_count: int) -> NDArray[np.float64]:
        """Return a zero-valued control array."""

        return np.zeros((agent_count, self.dimensions), dtype=float)

    @abstractmethod
    def compute_control(self, state: SystemState) -> NDArray[np.float64]:
        """Compute the control action for each agent."""

    def reset(self) -> None:
        """Reset controller internals when a new simulation starts."""

        # TODO: Add controller-specific state reset when the control law is implemented.
