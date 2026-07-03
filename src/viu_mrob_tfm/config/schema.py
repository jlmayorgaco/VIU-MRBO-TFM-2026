"""Dataclass-based schemas for experiment and simulation settings."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ControllerConfig:
    """Minimal controller configuration container."""

    type: str = "nominal"
    parameters: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class LoadConfig:
    """Nominal load and uncertainty parameters."""

    nominal_mass: float = 25.0
    nominal_inertia: float = 3.0
    mass_uncertainty_ratio: float = 0.1
    center_of_mass_shift: list[float] = field(default_factory=lambda: [0.0, 0.0])


@dataclass(slots=True)
class GraphConfig:
    """Adjacency definition for local agent communication."""

    adjacency: list[list[float]]


@dataclass(slots=True, init=False)
class SimulationConfig:
    """Core simulation parameters shared across scenarios."""

    duration: float = 20.0
    time_step: float = 0.1
    amr_count: int = 3
    dimensions: int = 2
    random_seed: int = 2026
    initial_positions: list[list[float]] = field(default_factory=list)
    communication_range: float | None = None
    visibility_range: float = 8.0
    transport_threshold_steps: int = 3
    detection_radius: float = 0.75

    def __init__(
        self,
        duration: float = 20.0,
        time_step: float = 0.1,
        amr_count: int = 3,
        dimensions: int = 2,
        random_seed: int = 2026,
        initial_positions: list[list[float]] | None = None,
        communication_range: float | None = None,
        visibility_range: float = 8.0,
        transport_threshold_steps: int = 3,
        detection_radius: float = 0.75,
        agv_count: int | None = None,
    ) -> None:
        if agv_count is not None:
            amr_count = agv_count
        self.duration = duration
        self.time_step = time_step
        self.amr_count = amr_count
        self.dimensions = dimensions
        self.random_seed = random_seed
        self.initial_positions = list(initial_positions or [])
        self.communication_range = communication_range
        self.visibility_range = visibility_range
        self.transport_threshold_steps = transport_threshold_steps
        self.detection_radius = detection_radius

    @property
    def agv_count(self) -> int:
        """Legacy alias for configurations created before the AMR terminology pass."""

        return self.amr_count

    @agv_count.setter
    def agv_count(self, value: int) -> None:
        self.amr_count = value


@dataclass(slots=True)
class TaskConfig:
    """YAML-facing transport task specification."""

    identifier: str
    pickup: list[float]
    destination: list[float]
    min_coalition_size: int = 1
    reward: float = 1.0
    demand_capacity: float | None = None


@dataclass(slots=True)
class ObstacleConfig:
    """YAML-facing circular obstacle specification."""

    center: list[float]
    radius: float = 0.35
    influence_radius: float = 1.25


@dataclass(slots=True)
class FailureConfig:
    """YAML-facing abrupt robot failure event."""

    time: float
    agent_index: int


@dataclass(slots=True)
class ExperimentConfig:
    """Top-level configuration for a reproducible experiment run."""

    name: str
    description: str
    controller: ControllerConfig = field(default_factory=ControllerConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    load: LoadConfig = field(default_factory=LoadConfig)
    graph: GraphConfig = field(
        default_factory=lambda: GraphConfig(adjacency=[[0.0]])
    )
    tasks: list[TaskConfig] = field(default_factory=list)
    obstacles: list[ObstacleConfig] = field(default_factory=list)
    failures: list[FailureConfig] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration into plain Python structures."""

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        """Build a typed config object from a plain dictionary."""

        simulation_data = dict(data.get("simulation", {}))
        if "agv_count" in simulation_data:
            legacy_count = simulation_data.pop("agv_count")
            if "amr_count" in simulation_data and simulation_data["amr_count"] != legacy_count:
                msg = "simulation.amr_count and legacy simulation.agv_count disagree."
                raise ValueError(msg)
            simulation_data.setdefault("amr_count", legacy_count)
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            controller=ControllerConfig(**data.get("controller", {})),
            simulation=SimulationConfig(**simulation_data),
            load=LoadConfig(**data.get("load", {})),
            graph=GraphConfig(**data.get("graph", {})),
            tasks=[TaskConfig(**item) for item in data.get("tasks", [])],
            obstacles=[ObstacleConfig(**item) for item in data.get("obstacles", [])],
            failures=[FailureConfig(**item) for item in data.get("failures", [])],
            metrics=list(data.get("metrics", [])),
            notes=data.get("notes", ""),
        )
