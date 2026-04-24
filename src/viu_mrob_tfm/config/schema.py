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


@dataclass(slots=True)
class SimulationConfig:
    """Core simulation parameters shared across scenarios."""

    duration: float = 20.0
    time_step: float = 0.1
    agv_count: int = 3
    dimensions: int = 2
    random_seed: int = 2026


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
    metrics: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration into plain Python structures."""

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentConfig":
        """Build a typed config object from a plain dictionary."""

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            controller=ControllerConfig(**data.get("controller", {})),
            simulation=SimulationConfig(**data.get("simulation", {})),
            load=LoadConfig(**data.get("load", {})),
            graph=GraphConfig(**data.get("graph", {})),
            metrics=list(data.get("metrics", [])),
            notes=data.get("notes", ""),
        )
