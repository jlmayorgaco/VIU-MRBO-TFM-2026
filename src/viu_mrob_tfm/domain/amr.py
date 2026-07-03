"""AMR domain entity used by scenarios and experiments."""

from __future__ import annotations

from dataclasses import dataclass, field

from viu_mrob_tfm.domain.state import AMRState


@dataclass(slots=True)
class AMR:
    """Minimal autonomous mobile robot description for simulation scaffolding."""

    identifier: str
    state: AMRState = field(default_factory=AMRState)
    nominal_mass: float = 50.0
    max_control: float = 10.0

    def reset(self) -> None:
        """Reset the robot state to a default value."""

        self.state = AMRState()
