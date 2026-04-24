"""Scenario builders for cooperative transport experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from viu_mrob_tfm.config.schema import ExperimentConfig
from viu_mrob_tfm.domain.agv import AGV
from viu_mrob_tfm.domain.graph import CommunicationGraph
from viu_mrob_tfm.domain.load import TransportedLoad


@dataclass(slots=True)
class SimulationScenario:
    """Scenario definition consumed by the simulator."""

    name: str
    agvs: list[AGV]
    transported_load: TransportedLoad
    graph: CommunicationGraph
    duration: float
    time_step: float

    @classmethod
    def from_config(cls, config: ExperimentConfig) -> "SimulationScenario":
        """Create a default scenario from an experiment configuration."""

        agvs = [AGV(identifier=f"agv-{index + 1}") for index in range(config.simulation.agv_count)]
        load = TransportedLoad(
            nominal_mass=config.load.nominal_mass,
            nominal_inertia=config.load.nominal_inertia,
            center_of_mass_shift=np.asarray(config.load.center_of_mass_shift, dtype=float),
        )
        graph = CommunicationGraph(np.asarray(config.graph.adjacency, dtype=float))
        return cls(
            name=config.name,
            agvs=agvs,
            transported_load=load,
            graph=graph,
            duration=config.simulation.duration,
            time_step=config.simulation.time_step,
        )
