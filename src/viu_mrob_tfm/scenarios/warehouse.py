"""Warehouse scenarios for V6 OOP tests and smoke runs."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from viu_mrob_tfm.domain.load import LoadSpec, WrenchDemand
from viu_mrob_tfm.domain.robot import CapacityModel, RobotRuntimeState, RobotSpec
from viu_mrob_tfm.domain.world import Obstacle, WarehouseMap, WorldState
from viu_mrob_tfm.scenarios.base import BaseScenario, ScenarioMetadata


@dataclass(slots=True)
class WarehouseCoalitionScenario(BaseScenario):
    """Small deterministic coalition scenario used as the OOP canonical smoke."""

    metadata: ScenarioMetadata = field(
        default_factory=lambda: ScenarioMetadata(
            name="warehouse-coalition-smoke",
            description="Three heterogeneous robots recruiting for one load.",
            hypothesis="Smith-QR closes a minimal quorum with a continuous field controller.",
        )
    )
    robot_count: int = 3

    def build(self, seed: int = 2026) -> WorldState:
        rng = np.random.default_rng(seed)
        robots: list[RobotRuntimeState] = []
        for idx in range(self.robot_count):
            spec = RobotSpec(
                identifier=f"amr-{idx + 1}",
                capacity=CapacityModel(payload_kg=1.0 + 0.5 * (idx == self.robot_count - 1)),
            )
            position = np.array([-2.0, 0.8 * (idx - (self.robot_count - 1) / 2.0)], dtype=float)
            robots.append(
                RobotRuntimeState(
                    spec=spec,
                    position=position,
                    heading=float(rng.uniform(-0.05, 0.05)),
                    battery_fraction=1.0,
                )
            )
        loads = [
            LoadSpec(
                identifier="load-1",
                pickup=np.array([1.5, 0.0], dtype=float),
                destination=np.array([4.5, 0.0], dtype=float),
                mass_kg=2.0,
                min_coalition_size=2,
                reward=1.0,
                wrench=WrenchDemand(force_xy=np.array([1.0, 0.0]), torque_z=0.2),
            )
        ]
        world_map = WarehouseMap(
            size_m=8.0,
            obstacles=(Obstacle(center=np.array([0.0, 1.8]), radius=0.35, influence_radius=1.2),),
        )
        return WorldState(robots=robots, loads=loads, map=world_map)
