from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_canonical.validation.dynamics import make_graph, run_population_dynamics
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v2 import (
    estimate_instance_preconditioner,
    run_two_phase_dynamics,
)
from viu_mrob_tfm.sp1_canonical.validation.model import ResourceWorld, build_costs, generate_resource_world
from viu_mrob_tfm.sp1_canonical.validation.rounding import (
    evaluate_integer,
    repair_assignment,
    repair_assignment_augmenting,
)
from viu_mrob_tfm.sp1_canonical.validation.simulation import (
    astar_waypoints,
    conditioned_warehouse_obstacles,
    segment_intersects_rectangle,
)


WEIGHTS = {"distance": 0.45, "time": 0.25, "energy": 0.30}


def test_v2_preconditioner_is_per_instance_bounded_and_honestly_named() -> None:
    small = generate_resource_world(6, 2, 12000)
    large = generate_resource_world(40, 8, 12000)
    small_preconditioner = estimate_instance_preconditioner(
        small, make_graph(small, "complete"), distributed=True
    )
    large_preconditioner = estimate_instance_preconditioner(
        large, make_graph(large, "complete"), distributed=True
    )
    assert 0.01 <= small_preconditioner.step <= 0.10
    assert 0.01 <= large_preconditioner.step <= 0.10
    assert small_preconditioner.operator_scale_estimate != large_preconditioner.operator_scale_estimate
    assert small_preconditioner.step != large_preconditioner.step


def test_v2_dynamics_does_not_refine_a_nonconverged_operational_state() -> None:
    world = generate_resource_world(8, 2, 12123)
    costs, _, _ = build_costs(world, WEIGHTS)
    result = run_two_phase_dynamics(
        world,
        costs,
        make_graph(world, "complete"),
        distributed=True,
        operational_max_iterations=1,
        refinement_max_iterations=1,
    )
    assert not result.operational_converged
    assert not result.refinement_attempted
    assert result.refinement is None
    assert result.stop_reason == "operational_iteration_limit_or_nonfinite"
    assert set(result.history["phase"]) == {"operational"}


def test_population_dynamics_accepts_a_valid_warm_start() -> None:
    world = generate_resource_world(8, 2, 12124)
    costs, _, _ = build_costs(world, WEIGHTS)
    graph = make_graph(world, "complete")
    initial = np.zeros((world.n_robots, world.n_loads))
    result = run_population_dynamics(
        world,
        costs,
        graph,
        distributed=False,
        initial_x=initial,
        initial_dual=np.zeros_like(world.requirements),
        max_iterations=1,
        step=0.05,
    )
    assert result.x.shape == initial.shape
    assert np.all(np.isfinite(result.x))
    assert np.all(result.x.sum(axis=1) <= 1.0 + 1e-10)


def _augmenting_chain_world() -> tuple[ResourceWorld, np.ndarray]:
    resources = np.asarray(
        [
            [1.0, 10.0, 0.0],
            [1.0, 0.0, 10.0],
            [1.0, 6.0, 10.0],
            [1.0, 10.0, 0.0],
        ]
    )
    requirements = np.asarray([[1.0, 10.0, 10.0], [1.0, 10.0, 10.0]])
    world = ResourceWorld(
        seed=1,
        robot_positions_m=np.asarray([[1.0, 1.0], [2.0, 1.0], [18.0, 18.0], [3.0, 1.0]]),
        load_positions_m=np.asarray([[2.0, 2.0], [17.0, 17.0]]),
        resources=resources,
        requirements=requirements,
        battery_energy=np.full(4, 100.0),
        max_speed_mps=np.ones(4),
        energy_per_m=np.ones(4),
        robot_classes=("test",) * 4,
        feasibility_witness=np.asarray([1, 0, 1, 0]),
        world_hash="augmenting-chain-test",
    )
    costs = np.ones((4, 2))
    costs[3, 1] = np.inf
    return world, costs


def test_augmenting_chain_succeeds_where_single_improvement_greedy_stalls() -> None:
    world, costs = _augmenting_chain_world()
    initial = np.asarray([0, 0, 1, -1])
    greedy = repair_assignment(
        world, initial, costs, prune=False, local_exchange=False, compress=False
    )
    augmenting = repair_assignment_augmenting(
        world,
        initial,
        costs,
        max_chain_length=4,
        max_nodes_per_augmentation=100,
        candidates_per_load=4,
        prune=False,
        local_exchange=False,
        compress=False,
    )
    assert not greedy.feasible
    assert augmenting.integer.feasible
    assert augmenting.maximum_chain_length >= 2
    assert augmenting.failure_reason == "none"
    assert evaluate_integer(world, augmenting.integer.assignment, costs).feasible


def test_conditioned_obstacle_blocks_direct_path_and_forces_astar_detour() -> None:
    starts = np.asarray([[2.0, 10.0], [2.0, 3.0]])
    targets = np.asarray([[18.0, 10.0], [18.0, 3.0]])
    plan = conditioned_warehouse_obstacles(starts, targets, desired_obstacles=1)
    assert len(plan.obstacles) == 1
    assert plan.blocked_route_indices
    assert plan.detoured_route_indices
    route = plan.detoured_route_indices[0]
    assert segment_intersects_rectangle(starts[route], targets[route], plan.obstacles[0])
    assert astar_waypoints(starts[route], targets[route], plan.obstacles)
    assert plan.astar_lengths_m[route] > plan.direct_lengths_m[route] + 0.20
