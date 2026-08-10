from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_geo.allocators.hungarian import allocate_hungarian_slots
from viu_mrob_tfm.sp1_geo.certifier import certify_assignment
from viu_mrob_tfm.sp1_geo.contributions import build_action_catalog
from viu_mrob_tfm.sp1_geo.scenario import (
    generate_world,
    torque_complementarity_world,
)
from viu_mrob_tfm.sp1_geo.welfare import independent_argmax_closure


def test_independent_closure_can_create_slot_collision() -> None:
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    preferences = np.zeros(catalog.n_actions)
    for robot in range(world.n_robots):
        action = catalog.action_for(robot, 0, 0)
        assert action is not None
        preferences[action] = 0.8
    assignment = independent_argmax_closure(
        preferences, catalog, world.n_robots
    )
    certificate = certify_assignment(world, catalog, assignment)
    assert certificate.duplicate_slots == 1


def test_scalar_commitment_is_not_a_wrench_certificate() -> None:
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    preferences = np.zeros(catalog.n_actions)
    action = catalog.action_for(0, 0, 0)
    assert action is not None
    preferences[action] = 0.8
    assignment = independent_argmax_closure(
        preferences, catalog, world.n_robots
    )
    certificate = certify_assignment(world, catalog, assignment)
    assert certificate.committed_loads == 1
    assert certificate.served_loads == 0
    assert "wrench_residual" in certificate.load_certificates[0].reasons


def test_hungarian_is_explicitly_restricted_to_separable_f0() -> None:
    world = generate_world("F3_torque_complementarity", 12, 3, 910000)
    catalog = build_action_catalog(world)
    result = allocate_hungarian_slots(world, catalog)
    assert result.status == "not_applicable_nonseparable"
    assert result.assignment.selected_actions().size == 0
