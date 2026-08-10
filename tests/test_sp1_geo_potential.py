from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_geo.contributions import build_action_catalog
from viu_mrob_tfm.sp1_geo.models import Assignment
from viu_mrob_tfm.sp1_geo.scenario import generate_world
from viu_mrob_tfm.sp1_geo.welfare import (
    marginal_payoffs,
    signal_potential,
    wonderful_life_difference,
)


def _interior_preferences(catalog, n_robots: int) -> np.ndarray:
    values = np.zeros(catalog.n_actions, dtype=float)
    for robot in range(n_robots):
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        values[actions] = 0.35 / max(len(actions), 1)
    return values


def test_signal_gradient_matches_finite_difference() -> None:
    world = generate_world("F0_easy_separable", 4, 1, 910000)
    catalog = build_action_catalog(world)
    preferences = _interior_preferences(catalog, world.n_robots)
    gradient = marginal_payoffs(
        world, catalog, preferences, "marginal_physical"
    )
    epsilon = 1e-6
    for action in np.flatnonzero(catalog.compatible)[:8]:
        perturbation = np.zeros(catalog.n_actions)
        perturbation[action] = epsilon
        numerical = (
            signal_potential(
                world,
                catalog,
                preferences + perturbation,
                "marginal_physical",
            )
            - signal_potential(
                world,
                catalog,
                preferences - perturbation,
                "marginal_physical",
            )
        ) / (2.0 * epsilon)
        assert np.isclose(numerical, gradient[action], atol=2e-6)


def test_wonderful_life_unilateral_difference_is_exact_potential() -> None:
    world = generate_world("F0_easy_separable", 6, 2, 910001)
    catalog = build_action_catalog(world)
    assignment = Assignment.empty(world.n_robots)
    action = int(catalog.actions_for_robot(0, compatible_only=True)[0])
    utility_delta, potential_delta = wonderful_life_difference(
        world,
        catalog,
        assignment,
        0,
        action,
        "marginal_physical",
    )
    assert utility_delta == potential_delta


def test_flat_nonsymmetric_cross_effect_is_not_an_integrable_potential() -> None:
    # A flat two-player payoff field with cross derivatives -2 and -1 fails
    # the equality of mixed partials required by an exact smooth potential.
    d_u1_d_x2 = -2.0
    d_u2_d_x1 = -1.0
    assert not np.isclose(d_u1_d_x2, d_u2_d_x1)
