"""Lightweight simulator placeholder for early experiment wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

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
        """Run a placeholder simulation and return zero-valued trajectories."""

        steps = max(1, int(self.scenario.duration / self.scenario.time_step) + 1)
        time = np.linspace(0.0, self.scenario.duration, steps)
        state = self.initial_state()
        control = self.controller.compute_control(state)
        if self.estimator is not None:
            self.estimator.update(state)

        # TODO: Propagate the dynamics once the system model and controllers are finalized.
        return {
            "time": time,
            "control": control,
            "trajectory": np.zeros((steps, len(self.scenario.agvs), 2), dtype=float),
            "load_trajectory": np.zeros((steps, 2), dtype=float),
        }
