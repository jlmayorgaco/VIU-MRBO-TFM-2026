"""Load entity definition for cooperative transport scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.domain.state import LoadState


@dataclass(slots=True)
class TransportedLoad:
    """Nominal load properties and kinematic coupling state.

    The load is modelled as a rigid body with no contact dynamics.
    When the coalition satisfies |C_k| >= n_k for tau_s consecutive steps
    the load is kinematically coupled to the coalition centroid; otherwise
    it remains stationary at its last position.  This represents the
    assignment-layer abstraction: a downstream manipulation controller
    (e.g. Ebel et al. 2024) would use the coalition geometry to compute
    the actual contact forces.
    """

    nominal_mass: float = 25.0
    nominal_inertia: float = 3.0
    center_of_mass_shift: NDArray[np.float64] = field(
        default_factory=lambda: np.zeros(2, dtype=float)
    )
    state: LoadState = field(default_factory=LoadState)

    # Kinematic coupling state (not exposed as slots to allow mutation)
    _coupled: bool = field(default=False, repr=False)
    _coupled_steps: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        self.center_of_mass_shift = np.asarray(self.center_of_mass_shift, dtype=float)
        if self.center_of_mass_shift.shape != (2,):
            msg = "center_of_mass_shift must be a 2D vector."
            raise ValueError(msg)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def coupled(self) -> bool:
        """True when the load is kinematically attached to the coalition."""
        return self._coupled

    def step(
        self,
        coalition_positions: NDArray[np.float64],
        coalition_size: int,
        n_k: int,
        tau_s: int,
    ) -> None:
        """Update load pose for one time step.

        Parameters
        ----------
        coalition_positions:
            Array of shape (m, 2) with the 2-D positions of the robots
            currently assigned to this task.  May be empty (m=0).
        coalition_size:
            Number of robots currently in the coalition (|C_k|).
        n_k:
            Minimum cardinality required for transport to begin.
        tau_s:
            Number of consecutive steps |C_k| >= n_k must hold before
            the load couples to the coalition centroid.
        """
        if coalition_size >= n_k:
            self._coupled_steps += 1
            if self._coupled_steps >= tau_s:
                self._coupled = True
        else:
            self._coupled_steps = 0
            self._coupled = False

        if self._coupled and coalition_size > 0:
            positions = np.asarray(coalition_positions, dtype=float)
            if positions.ndim == 2 and positions.shape[0] > 0:
                self.state.position = positions.mean(axis=0)

    def reset(self, pickup_position: NDArray[np.float64] | None = None) -> None:
        """Reset coupling state and optionally reposition the load."""
        self._coupled = False
        self._coupled_steps = 0
        if pickup_position is not None:
            self.state.position = np.asarray(pickup_position, dtype=float)
