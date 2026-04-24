"""Formation references for cooperative transport geometries."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class FormationSpec:
    """Desired relative offsets between AGVs and the transported load."""

    relative_offsets: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros((0, 2), dtype=float)
    )

    def __post_init__(self) -> None:
        self.relative_offsets = np.asarray(self.relative_offsets, dtype=float)
        if self.relative_offsets.ndim != 2 or self.relative_offsets.shape[1] != 2:
            msg = "relative_offsets must have shape (n_agents, 2)."
            raise ValueError(msg)

    @property
    def agent_count(self) -> int:
        """Return the number of agents encoded in the formation."""

        return int(self.relative_offsets.shape[0])
