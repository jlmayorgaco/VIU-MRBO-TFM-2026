"""Load entity definition for cooperative transport scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.domain.state import LoadState


@dataclass(slots=True)
class TransportedLoad:
    """Nominal load properties and current state placeholder."""

    nominal_mass: float = 25.0
    nominal_inertia: float = 3.0
    center_of_mass_shift: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    state: LoadState = field(default_factory=LoadState)

    def __post_init__(self) -> None:
        self.center_of_mass_shift = np.asarray(self.center_of_mass_shift, dtype=float)
        if self.center_of_mass_shift.shape != (2,):
            msg = "center_of_mass_shift must be a 2D vector."
            raise ValueError(msg)
