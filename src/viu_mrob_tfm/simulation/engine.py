"""OOP simulation engine facade for V6."""

from __future__ import annotations

from dataclasses import dataclass, field

from viu_mrob_tfm.allocation import BaseAllocator, DecisionContext, SmithQRAllocator
from viu_mrob_tfm.control import BaseContinuousController, SingleFieldController
from viu_mrob_tfm.scenarios import BaseScenario
from viu_mrob_tfm.simulation.result import SimulationResult


@dataclass(slots=True)
class PolicyStack:
    """Composable policy bundle for a simulation run."""

    allocator: BaseAllocator = field(default_factory=SmithQRAllocator)
    controller: BaseContinuousController = field(default_factory=SingleFieldController)


@dataclass(slots=True)
class SimulationEngine:
    """Minimal engine that wires scenario, allocator, and controller."""

    policy: PolicyStack = field(default_factory=PolicyStack)

    def run(self, scenario: BaseScenario, seed: int = 2026, steps: int = 1) -> SimulationResult:
        world = scenario.build(seed=seed)
        assignment = None
        command = None
        for _ in range(max(1, steps)):
            context = DecisionContext(world=world, previous_assignment=assignment)
            assignment = self.policy.allocator.allocate(context)
            command = self.policy.controller.compute(world, assignment)
            world.time_s += 1.0
        assert assignment is not None and command is not None
        return SimulationResult(
            world=world,
            assignment=assignment,
            command=command,
            steps=max(1, steps),
            metadata={
                "scenario": scenario.metadata.name,
                "allocator": self.policy.allocator.name,
                "controller": self.policy.controller.name,
            },
        )
