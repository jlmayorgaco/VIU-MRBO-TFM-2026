"""Lightweight simulator placeholder for early experiment wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.controllers.base import BaseController
from viu_mrob_tfm.domain.state import SystemState
from viu_mrob_tfm.estimators.base import BaseEstimator
from viu_mrob_tfm.simulations.scenario import SimulationScenario


@dataclass(slots=True)
class Simulator:
    """Minimal simulator that exposes a stable run interface."""

    scenario: SimulationScenario
    controller: BaseController
    estimator: BaseEstimator | None = None

    def initial_state(self) -> SystemState:
        """Construct the initial system state from the scenario."""

        return SystemState(
            agv_states=[agv.state for agv in self.scenario.agvs],
            load_state=self.scenario.transported_load.state,
            time=0.0,
        )

    def run(self) -> dict[str, Any]:
        """Run a placeholder simulation and return trajectories.

        The AGV dynamics are not yet propagated (TODO below).  However,
        the kinematic load-coupling logic is exercised with synthetic
        positions so that load_trajectory reflects the coupling rule:
        the load stays at the pickup location until the coalition is
        formed for tau_s consecutive steps, then follows the centroid.
        """

        steps = max(1, int(self.scenario.duration / self.scenario.time_step) + 1)
        time = np.linspace(0.0, self.scenario.duration, steps)
        state = self.initial_state()
        control = self.controller.compute_control(state)
        if self.estimator is not None:
            self.estimator.update(state)

        n_agents = len(self.scenario.agvs)

        # TODO: Propagate the dynamics once the system model and controllers
        # are finalized.  For now, use synthetic positions to demonstrate
        # the kinematic load-coupling logic.
        agv_trajectories = np.zeros((steps, n_agents, 2), dtype=float)
        load_trajectory = np.zeros((steps, 2), dtype=float)
        coupled_flag = np.zeros(steps, dtype=bool)

        load = self.scenario.transported_load
        load.reset(pickup_position=load.state.position.copy())

        n_k: int = getattr(self.scenario, "min_coalition_size", 1)
        tau_s: int = getattr(self.scenario, "transport_threshold_steps", 3)

        for step_idx in range(steps):
            # Synthetic: full coalition assembles midway through the episode.
            coalition_assembled = step_idx >= steps // 2
            coalition_size = n_agents if coalition_assembled else 0
            coalition_positions: NDArray[np.float64] = (
                agv_trajectories[step_idx] if coalition_assembled else np.empty((0, 2))
            )

            load.step(
                coalition_positions=coalition_positions,
                coalition_size=coalition_size,
                n_k=n_k,
                tau_s=tau_s,
            )

            load_trajectory[step_idx] = load.state.position.copy()
            coupled_flag[step_idx] = load.coupled

        return {
            "time": time,
            "control": control,
            "trajectory": agv_trajectories,
            "load_trajectory": load_trajectory,
            "load_coupled": coupled_flag,
        }
