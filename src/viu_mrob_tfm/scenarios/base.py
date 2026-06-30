"""Scenario contracts for organized V6 experiments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from viu_mrob_tfm.domain.world import WorldState


@dataclass(frozen=True, slots=True)
class ScenarioMetadata:
    """Human-readable scenario metadata."""

    name: str
    description: str = ""
    hypothesis: str = ""


class BaseScenario(ABC):
    """Factory interface for deterministic world states."""

    metadata: ScenarioMetadata

    @abstractmethod
    def build(self, seed: int = 2026) -> WorldState:
        """Build a fresh world state."""
