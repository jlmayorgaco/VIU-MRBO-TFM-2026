"""Theory and integration gates for the SP4 v4 docking game."""

from __future__ import annotations

import numpy as np
import pytest

from viu_mrob_tfm.sp4.docking_game import build_docking_world
from viu_mrob_tfm.sp4.docking_game_v4 import (
    build_docking_world_v4,
    build_pairwise_game_features,
    execute_acceleration,
    hocbf_residual,
    initialise_pairwise_game,
    minimum_goal_clearance,
    pairwise_game_gradient,
    pairwise_game_potential,
    project_hocbf_acceleration,
    simulate_docking_v4,
    solve_pairwise_game,
)


def test_v4_repairs_infeasible_goal_geometries() -> None:
    invalid_v3 = build_docking_world("actuator_limited", 7001, 4)
    assert minimum_goal_clearance(invalid_v3) < 0.0
    for scenario in ("actuator_limited", "narrow_passage"):
        for n_robots in (4, 8, 12):
            world = build_docking_world_v4(scenario, 7001 + n_robots, n_robots)
            assert minimum_goal_clearance(world) >= -1e-12


def test_pairwise_potential_gradient_matches_finite_difference() -> None:
    conflict = np.asarray(
        [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
        dtype=bool,
    )
    features = build_pairwise_game_features(conflict)
    preferences = np.asarray(
        [[0.55, 0.30, 0.15], [0.25, 0.50, 0.25], [0.40, 0.35, 0.25]],
        dtype=float,
    )
    costs = np.asarray(
        [[-1.0, -0.4, 0.1], [-0.9, -0.3, 0.2], [-1.1, -0.5, 0.1]],
        dtype=float,
    )
    direction = np.zeros_like(preferences)
    direction[1] = (0.35, -0.20, -0.15)
    analytic = pairwise_game_gradient(preferences, costs, features)
    eps = 1e-6
    numeric = (
        pairwise_game_potential(preferences + eps * direction, costs, features)
        - pairwise_game_potential(preferences - eps * direction, costs, features)
    ) / (2.0 * eps)
    assert numeric == pytest.approx(float(np.sum(analytic * direction)), abs=2e-6)


@pytest.mark.parametrize("protocol", ["projected_pd", "replicator"])
def test_pairwise_protocol_preserves_simplex_and_closes_capacity(protocol: str) -> None:
    game = initialise_pairwise_game(3)
    conflict = np.ones((3, 3), dtype=bool)
    np.fill_diagonal(conflict, False)
    docked = np.zeros(3, dtype=bool)
    for _ in range(12):
        solve_pairwise_game(
            game,
            conflict,
            np.ones(3),
            docked,
            protocol=protocol,
            iterations=64,
        )
    assert np.max(np.abs(np.sum(game.preferences, axis=1) - 1.0)) <= 1e-12
    assert np.min(game.preferences) >= -1e-12
    assert game.capacity_trace[-1] <= 1e-2


def test_hocbf_projection_is_executable_without_torque_clipping() -> None:
    world = build_docking_world_v4("open_docking", 7019, 4)
    state = world.initial_state.copy()
    state[:, 3:] = 0.0
    state[0, :3] = (-0.65, 3.0, 0.0)
    state[1, :3] = (0.65, 3.0, np.pi)
    state[2, :3] = (-3.0, -3.0, 0.0)
    state[3, :3] = (3.0, -3.0, np.pi)
    state[0:2, 3] = 0.55
    nominal = np.zeros((4, 2), dtype=float)
    nominal[0:2, 0] = 0.8
    docked = np.zeros(4, dtype=bool)
    safe = project_hocbf_acceleration(
        world,
        state,
        nominal,
        docked,
        iterations=180,
        margin_m=0.005,
    )
    assert safe.residual <= 1e-6
    _next, actual, _energy, saturated = execute_acceleration(
        world,
        state,
        safe.acceleration,
        docked,
        dt_s=0.12,
    )
    assert saturated == 0
    assert hocbf_residual(world, state, actual, margin_m=0.005) <= 1e-6


def test_v4_open_docking_micro_run_is_certified() -> None:
    world = build_docking_world_v4("open_docking", 7023, 4)
    result = simulate_docking_v4(
        world,
        "distributed_pd_hocbf",
        horizon_s=15.0,
        game_iterations=24,
        hocbf_iterations=80,
    )
    assert result.safe_docking_success
    assert not result.any_collision
    assert result.exec_barrier_violations == 0
    assert result.torque_saturation_events == 0
    assert result.max_simplex_error <= 1e-12