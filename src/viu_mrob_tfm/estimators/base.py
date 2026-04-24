"""Base interfaces for parameter estimation blocks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from viu_mrob_tfm.domain.state import SystemState


class BaseEstimator(ABC):
    """Common contract for estimators used by adaptive controllers."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def update(self, state: SystemState) -> dict[str, Any]:
        """Update internal estimates using the latest system state."""

    @abstractmethod
    def estimate(self) -> dict[str, Any]:
        """Expose the current estimated parameters."""
