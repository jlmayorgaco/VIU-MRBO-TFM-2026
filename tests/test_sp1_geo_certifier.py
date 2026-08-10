from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_geo.certifier import (
    bounded_wrench_residual,
    certify_assignment,
)
from viu_mrob_tfm.sp1_geo.contributions import build_action_catalog
from viu_mrob_tfm.sp1_geo.models import Assignment
from viu_mrob_tfm.sp1_geo.scenario import torque_complementarity_world


def _torque_profiles():
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    first = catalog.action_for(0, 0, 0)
    second = catalog.action_for(1, 0, 1)
    assert first is not None and second is not None
    return (
        world,
        catalog,
        Assignment(np.array([first, -1])),
        Assignment(np.array([first, second])),
    )


def test_bounded_wrench_residual_respects_effort_bounds() -> None:
    columns = np.array([[1.0, 0.0, -1.0], [-1.0, 0.0, -1.0]])
    residual_si, residual, effort = bounded_wrench_residual(
        columns,
        np.array([8.5, 8.5]),
        np.array([0.0, 0.0, -16.0]),
    )
    assert residual_si < 1e-8
    assert residual < 1e-8
    assert np.all((effort >= 0.0) & (effort <= 8.5))


def test_certifier_rejects_incomplete_and_accepts_complementary_pair() -> None:
    world, catalog, singleton, pair = _torque_profiles()
    single_certificate = certify_assignment(world, catalog, singleton)
    pair_certificate = certify_assignment(world, catalog, pair)
    assert single_certificate.served_loads == 0
    assert "coalition_below_minimum" in single_certificate.load_certificates[0].reasons
    assert pair_certificate.served_loads == 1
    assert pair_certificate.assignment_valid


def test_certifier_detects_duplicate_slot() -> None:
    world, catalog, _, _ = _torque_profiles()
    first = catalog.action_for(0, 0, 0)
    duplicate = catalog.action_for(1, 0, 0)
    assert first is not None and duplicate is not None
    certificate = certify_assignment(
        world, catalog, Assignment(np.array([first, duplicate]))
    )
    assert certificate.duplicate_slots == 1
    assert not certificate.assignment_valid
    assert "duplicate_slot" in certificate.load_certificates[0].reasons
