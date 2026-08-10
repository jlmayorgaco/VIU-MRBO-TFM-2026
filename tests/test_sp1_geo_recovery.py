from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_geo.contributions import build_action_catalog
from viu_mrob_tfm.sp1_geo.models import Assignment
from viu_mrob_tfm.sp1_geo.recovery import recover_assignment
from viu_mrob_tfm.sp1_geo.scenario import torque_complementarity_world


def test_common_recovery_is_finite_strict_and_cycle_free() -> None:
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    first = catalog.action_for(0, 0, 0)
    assert first is not None
    recovered = recover_assignment(
        world,
        catalog,
        Assignment(np.array([first, -1])),
        delta=1e-10,
        max_chain_length=2,
        candidates_per_load=4,
    )
    differences = np.diff(recovered.potential_trajectory)
    assert recovered.terminated
    assert not recovered.cycle_detected
    assert recovered.steps <= 2
    assert recovered.visited_states == recovered.steps + 1
    assert np.all(differences >= 1e-10 - 1e-12)
    assert recovered.certificate.served_loads == 1


def test_recovery_is_deterministic_for_a_frozen_world() -> None:
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    initial = Assignment.empty(world.n_robots)
    first = recover_assignment(world, catalog, initial, max_chain_length=2)
    second = recover_assignment(world, catalog, initial, max_chain_length=2)
    assert np.array_equal(
        first.assignment.action_by_robot, second.assignment.action_by_robot
    )
    assert first.potential_trajectory == second.potential_trajectory
