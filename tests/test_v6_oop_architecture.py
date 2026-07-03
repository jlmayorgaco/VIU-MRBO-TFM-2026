"""V6 OOP architecture smoke tests."""

from __future__ import annotations

import numpy as np

from viu_mrob_tfm.allocation import SmithQRAllocator
from viu_mrob_tfm.control import RigidFormation, SingleFieldController, VectorialWrenchGame
from viu_mrob_tfm.domain import LoadSpec, RobotRuntimeState, RobotSpec, WorldState, WrenchDemand
from viu_mrob_tfm.scenarios import WarehouseCoalitionScenario
from viu_mrob_tfm.simulation import PolicyStack, SimulationEngine


def test_v6_domain_models_construct_world_state() -> None:
    robot = RobotRuntimeState(spec=RobotSpec(identifier="AMR-1"), position=np.array([0.0, 0.0]))
    load = LoadSpec(identifier="load-1", pickup=np.array([1.0, 0.0]), destination=np.array([2.0, 0.0]))
    world = WorldState(robots=[robot], loads=[load])

    assert world.active_robot_count == 1
    assert world.robot_positions.shape == (1, 2)
    assert load.min_capacity_kg == load.mass_kg


def test_vectorial_wrench_game_solves_force_and_torque_for_rigid_load() -> None:
    load = LoadSpec(
        identifier="long-box",
        pickup=np.array([0.0, 0.0]),
        destination=np.array([2.0, 0.0]),
        length_m=2.0,
        width_m=1.0,
        wrench=WrenchDemand(force_xy=np.array([1.0, 0.0]), torque_z=0.5),
    )
    formation = RigidFormation.from_load(load)
    matrix = formation.contact_matrix()

    assert matrix.shape == (3, len(formation.slots))
    assert np.linalg.matrix_rank(matrix) == 3

    solution = VectorialWrenchGame(residual_tolerance=1e-8).solve(
        demand=load.wrench,
        formation=formation,
        force_limits=np.full(len(formation.slots), 10.0),
    )

    assert solution.feasible
    np.testing.assert_allclose(solution.provided_wrench, load.wrench.as_vector(), atol=1e-6)
    assert np.any(solution.contact_forces > 0.0)


def test_v6_policy_stack_runs_one_oop_step() -> None:
    scenario = WarehouseCoalitionScenario()
    engine = SimulationEngine(
        policy=PolicyStack(
            allocator=SmithQRAllocator(),
            controller=SingleFieldController(),
        )
    )

    result = engine.run(scenario, seed=2026)

    assert result.metadata["scenario"] == "warehouse-coalition-smoke"
    assert result.assignment.labels.shape == (scenario.robot_count,)
    assert result.command.velocity_xy.shape == (scenario.robot_count, 2)
    assert np.any(result.assignment.labels > 0)