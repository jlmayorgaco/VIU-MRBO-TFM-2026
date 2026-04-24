"""Placeholder estimator for load inertial uncertainty."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from viu_mrob_tfm.domain.state import SystemState
from viu_mrob_tfm.estimators.base import BaseEstimator


@dataclass(slots=True)
class InertialUncertaintyEstimator(BaseEstimator):
    """Very small stateful placeholder for future adaptive estimation logic."""

    estimated_mass: float = 25.0
    estimated_inertia: float = 3.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__(name="inertial_uncertainty")

    def update(self, state: SystemState) -> dict[str, Any]:
        """Refresh placeholder estimates without changing the nominal values."""

        self.metadata["last_time"] = state.time
        # TODO: Inject adaptation dynamics based on tracking and load residuals.
        return self.estimate()

    def estimate(self) -> dict[str, Any]:
        """Return the current mass and inertia estimates."""

        return {
            "estimated_mass": self.estimated_mass,
            "estimated_inertia": self.estimated_inertia,
            "metadata": dict(self.metadata),
        }
