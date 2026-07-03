"""Static allocation baselines used by EXP0."""

from __future__ import annotations

import numpy as np

from viu_mrob_tfm.allocation import (
    CentralizedClassicAllocator,
    CentralizedUtilityAllocator,
    DecisionContext,
    DecentralizedAuctionAllocator,
    DecentralizedClassicGreedyAllocator,
    SmithQRAllocator,
)
from viu_mrob_tfm.domain import CapacityModel, LoadSpec, RobotRuntimeState, RobotSpec, WorldState


def _world() -> WorldState:
    robots = [
        RobotRuntimeState(
            spec=RobotSpec(identifier=f"amr-{idx}", capacity=CapacityModel(payload_kg=1.0)),
            position=np.array([float(idx), 0.0]),
        )
        for idx in range(5)
    ]
    loads = [
        LoadSpec(
            identifier="load-1",
            pickup=np.array([0.0, 1.0]),
            destination=np.array([1.0, 1.0]),
            mass_kg=2.0,
            min_coalition_size=2,
            reward=1.2,
        ),
        LoadSpec(
            identifier="load-2",
            pickup=np.array([4.0, 1.0]),
            destination=np.array([5.0, 1.0]),
            mass_kg=3.0,
            min_coalition_size=3,
            reward=2.0,
        ),
    ]
    return WorldState(robots=robots, loads=loads)


def test_static_allocators_return_valid_labels() -> None:
    context = DecisionContext(world=_world())
    allocators = [
        CentralizedClassicAllocator(),
        DecentralizedClassicGreedyAllocator(),
        CentralizedUtilityAllocator(),
        DecentralizedAuctionAllocator(),
        SmithQRAllocator(),
    ]

    for allocator in allocators:
        assignment = allocator.allocate(context)
        assert assignment.labels.shape == (5,)
        assert np.all(assignment.labels >= 0)
        assert np.all(assignment.labels <= 2)
        assert assignment.method == allocator.name
