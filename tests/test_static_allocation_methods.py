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
from scripts.run_allocation_exp0 import build_world, load_diagnostics, summarize_assignment


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


def test_exp0_reports_payload_and_load_capacity_status() -> None:
    world = build_world(robot_count=3, load_count=2, seed=7, size=8.0, robot_payload_kg=25.0)
    assignment = CentralizedClassicAllocator().allocate(DecisionContext(world=world))
    summary = summarize_assignment(world, assignment, runtime_ms=0.0)
    load_rows = load_diagnostics(world, assignment)

    assert all(robot.spec.capacity.payload_kg == 25.0 for robot in world.robots)
    assert [load.min_coalition_size for load in world.loads] == [1, 2]
    assert [load.mass_kg for load in world.loads] == [20.0, 48.0]
    assert "total_capacity_deficit_kg" in summary
    assert "load_statuses" in summary
    assert {row["status"] for row in load_rows} <= {"UNDER", "OK", "OVER"}
