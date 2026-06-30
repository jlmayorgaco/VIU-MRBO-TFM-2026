"""Allocator contracts for the V6 OOP architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.domain.world import WorldState


Array = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class Assignment:
    """Robot-to-load assignment using 0 for idle and 1..M for loads."""

    labels: NDArray[np.int_]
    scores: Array | None = None
    method: str = "unknown"

    def __post_init__(self) -> None:
        labels = np.asarray(self.labels, dtype=int)
        if labels.ndim != 1:
            raise ValueError("Assignment labels must be a 1D array.")
        object.__setattr__(self, "labels", labels)

    def members_for_load(self, load_index: int) -> NDArray[np.int_]:
        return np.flatnonzero(self.labels == load_index + 1)


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Allocator input bundle."""

    world: WorldState
    occupancy_estimate: Array | None = None
    previous_assignment: Assignment | None = None
    prices: Array | None = None
    metadata: dict[str, float] = field(default_factory=dict)


class BaseAllocator(ABC):
    """Strategy interface for task allocation and coalition recruitment."""

    name: str = "base"

    @abstractmethod
    def allocate(self, context: DecisionContext) -> Assignment:
        """Return the executable robot-to-load assignment."""
