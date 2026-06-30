"""Scenario builders for cooperative transport experiments."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from viu_mrob_tfm.config.schema import ExperimentConfig
from viu_mrob_tfm.domain.agv import AGV
from viu_mrob_tfm.domain.graph import CommunicationGraph
from viu_mrob_tfm.domain.load import TransportedLoad
from viu_mrob_tfm.domain.state import AGVState, LoadState


@dataclass(slots=True)
class TaskSpec:
    """Transport task with pickup, destination, priority, and coalition demand."""

    identifier: str
    pickup: NDArray[np.float64]
    destination: NDArray[np.float64]
    min_coalition_size: int = 1
    reward: float = 1.0
    demand_capacity: float | None = None

    def __post_init__(self) -> None:
        self.pickup = np.asarray(self.pickup, dtype=float)
        self.destination = np.asarray(self.destination, dtype=float)
        if self.pickup.shape != (2,) or self.destination.shape != (2,):
            msg = "pickup and destination must be 2D vectors."
            raise ValueError(msg)
        if self.min_coalition_size < 1:
            msg = "min_coalition_size must be at least 1."
            raise ValueError(msg)


@dataclass(slots=True)
class ObstacleSpec:
    """Circular static obstacle used by the reactive navigation layer."""

    center: NDArray[np.float64]
    radius: float = 0.35
    influence_radius: float = 1.25

    def __post_init__(self) -> None:
        self.center = np.asarray(self.center, dtype=float)
        if self.center.shape != (2,):
            msg = "Obstacle center must be a 2D vector."
            raise ValueError(msg)
        if self.radius <= 0 or self.influence_radius <= self.radius:
            msg = "Obstacle radii must satisfy 0 < radius < influence_radius."
            raise ValueError(msg)


@dataclass(slots=True)
class FailureEvent:
    """Abrupt robot removal event for reorganization tests."""

    time: float
    agent_index: int


@dataclass(slots=True)
class SimulationScenario:
    """Scenario definition consumed by the simulator."""

    name: str
    agvs: list[AGV]
    transported_load: TransportedLoad
    graph: CommunicationGraph
    duration: float
    time_step: float
    tasks: list[TaskSpec] = field(default_factory=list)
    obstacles: list[ObstacleSpec] = field(default_factory=list)
    failure_events: list[FailureEvent] = field(default_factory=list)
    communication_range: float | None = None
    visibility_range: float = 8.0
    transport_threshold_steps: int = 3
    detection_radius: float = 0.75

    @classmethod
    def from_config(cls, config: ExperimentConfig) -> "SimulationScenario":
        """Create a default scenario from an experiment configuration."""

        agvs = []
        for index in range(config.simulation.agv_count):
            if index < len(config.simulation.initial_positions):
                position = np.asarray(config.simulation.initial_positions[index], dtype=float)
            else:
                position = np.array(
                    [-2.0, 0.8 * (index - (config.simulation.agv_count - 1) / 2.0)]
                )
            agvs.append(
                AGV(
                    identifier=f"agv-{index + 1}",
                    state=AGVState(position=position, heading=0.0),
                )
            )
        load = TransportedLoad(
            nominal_mass=config.load.nominal_mass,
            nominal_inertia=config.load.nominal_inertia,
            center_of_mass_shift=np.asarray(config.load.center_of_mass_shift, dtype=float),
            state=LoadState(position=np.array([1.5, 0.0])),
        )
        graph = CommunicationGraph(np.asarray(config.graph.adjacency, dtype=float))
        if config.tasks:
            tasks = [
                TaskSpec(
                    identifier=task.identifier,
                    pickup=np.asarray(task.pickup, dtype=float),
                    destination=np.asarray(task.destination, dtype=float),
                    min_coalition_size=task.min_coalition_size,
                    reward=task.reward,
                    demand_capacity=task.demand_capacity,
                )
                for task in config.tasks
            ]
            load.state.position = tasks[0].pickup.copy()
        else:
            tasks = [
                TaskSpec(
                    identifier="load-1",
                    pickup=load.state.position.copy(),
                    destination=np.array([4.5, 0.0]),
                    min_coalition_size=min(2, config.simulation.agv_count),
                    reward=1.0,
                )
            ]
        obstacles = [
            ObstacleSpec(
                center=np.asarray(obstacle.center, dtype=float),
                radius=obstacle.radius,
                influence_radius=obstacle.influence_radius,
            )
            for obstacle in config.obstacles
        ]
        failures = [
            FailureEvent(time=failure.time, agent_index=failure.agent_index)
            for failure in config.failures
        ]
        return cls(
            name=config.name,
            agvs=agvs,
            transported_load=load,
            graph=graph,
            duration=config.simulation.duration,
            time_step=config.simulation.time_step,
            tasks=tasks,
            obstacles=obstacles,
            failure_events=failures,
            communication_range=config.simulation.communication_range,
            visibility_range=config.simulation.visibility_range,
            transport_threshold_steps=config.simulation.transport_threshold_steps,
            detection_radius=config.simulation.detection_radius,
        )
