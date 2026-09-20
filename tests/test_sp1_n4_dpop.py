"""Exactness and scope checks for the small-instance DPOP diagnostic."""

from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from viu_mrob_tfm.sp1_n3.certificate import certify
from viu_mrob_tfm.sp1_n3.worlds import World
from viu_mrob_tfm.sp1_n4.dpop_exact import solve_dpop_exact_small


def _world(*, demands: np.ndarray) -> World:
    return World(
        world_id="dpop-test",
        seed=77,
        scenario="manual",
        capacity_cv=0.25,
        pressure=0.8,
        robot_positions=np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]),
        load_positions=np.array([[0.0, 1.0], [3.0, 1.0]]),
        capacities=np.array([1.0, 1.5, 0.75, 1.25]),
        demands=np.asarray(demands, dtype=float),
        distances=np.array(
            [[1.0, 5.0], [2.0, 3.0], [4.0, 2.0], [5.0, 1.0]],
            dtype=float,
        ),
    )


def _brute_force(world: World) -> tuple[bool, float]:
    feasible_costs = []
    for assignment in product(range(-1, world.n_loads), repeat=world.n_robots):
        certificate = certify(
            np.asarray(assignment), world.capacities, world.demands, world.distances
        )
        if certificate.feasible:
            feasible_costs.append(certificate.distance_cost)
    return bool(feasible_costs), min(feasible_costs, default=float("inf"))


def test_dpop_matches_exhaustive_optimum_and_reports_width() -> None:
    world = _world(demands=np.array([1.5, 1.5]))
    expected_feasible, expected_cost = _brute_force(world)
    result = solve_dpop_exact_small(world)
    assert result.feasible == expected_feasible
    assert result.objective == pytest.approx(expected_cost)
    assert result.induced_width == world.n_robots - 1
    assert result.utility_entries == sum(
        (world.n_loads + 1) ** exponent
        for exponent in range(1, world.n_robots)
    )
    assert result.profiles_evaluated == (world.n_loads + 1) ** world.n_robots


def test_dpop_keeps_infeasible_worlds_in_the_denominator() -> None:
    result = solve_dpop_exact_small(_world(demands=np.array([10.0, 10.0])))
    assert not result.feasible
    assert np.isinf(result.objective)


def test_dpop_refuses_an_unbounded_table() -> None:
    with pytest.raises(ValueError, match="limit"):
        solve_dpop_exact_small(_world(demands=np.array([1.0, 1.0])), max_profiles=10)
