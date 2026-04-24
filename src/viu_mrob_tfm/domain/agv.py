"""AGV domain entity used by scenarios and experiments."""

from __future__ import annotations

from dataclasses import dataclass, field

from viu_mrob_tfm.domain.state import AGVState


@dataclass(slots=True)
class AGV:
    """Minimal AGV description for early simulation scaffolding."""

    identifier: str
    state: AGVState = field(default_factory=AGVState)
    nominal_mass: float = 50.0
    max_control: float = 10.0

    def reset(self) -> None:
        """Reset the AGV state to a default value."""

        self.state = AGVState()
