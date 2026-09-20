from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime
from viu_mrob_tfm.sp1_n3.worlds import make_world
from viu_mrob_tfm.sp1_n4.continuous import (
    atomic_closure,
    initial_simplex,
    population_direction,
    population_potential_and_fitness,
    run_distributed_population_game,
    run_distributed_vgne,
    run_population_game,
    solve_central_vgne,
)


def _world(seed: int = 711):
    return make_world(
        world_id=f"continuous-{seed}",
        robot_count=6,
        load_count=2,
        q_bar=5.0,
        cv=0.55,
        pressure=0.72,
        scenario="uniform",
        workspace=(40.0, 40.0),
        seed=seed,
        alpha=3.0,
    )


def test_population_fitness_is_gradient_of_the_declared_potential() -> None:
    world = _world()
    x = initial_simplex(world)
    potential, fitness, _ = population_potential_and_fitness(world, x)
    epsilon = 1e-7
    for robot, strategy in ((0, 0), (2, 1), (4, 0)):
        perturbed = x.copy()
        perturbed[robot, strategy] += epsilon
        shifted, _, _ = population_potential_and_fitness(world, perturbed)
        numerical = (shifted - potential) / epsilon
        assert np.isclose(numerical, fitness[robot, strategy], atol=2e-5)


def test_rep_smith_and_bnn_have_nonnegative_positive_correlation() -> None:
    world = _world(712)
    rng = np.random.default_rng(22)
    x = rng.dirichlet(np.ones(world.n_loads + 1), size=world.n_robots)
    _, fitness, _ = population_potential_and_fitness(world, x)
    for method in ("replicator", "smith", "bnn"):
        direction = population_direction(method, x, fitness, temperature=0.08)
        assert abs(float(np.max(np.abs(np.sum(direction, axis=1))))) < 1e-10
        assert float(np.sum(fitness * direction)) >= -1e-10


def test_population_integrators_preserve_simplex_and_common_closure_is_deterministic() -> None:
    world = _world(713)
    for method in ("replicator", "smith", "bnn", "logit"):
        result = run_population_game(
            world,
            method,
            max_iterations=250,
            history_stride=25,
        )
        assert result.simplex_violation <= 1e-10
        assert np.all(result.x >= -1e-12)
        first = atomic_closure(world, result.x)
        second = atomic_closure(world, result.x)
        assert np.array_equal(first.assignment, second.assignment)
        assert first.feasible == second.feasible
        assert np.isclose(first.distance, second.distance)


def test_replicator_does_not_reactivate_a_zero_support_component() -> None:
    world = _world(714)
    initial = initial_simplex(world)
    initial[:, 0] = 0.0
    initial /= initial.sum(axis=1, keepdims=True)
    result = run_population_game(
        world,
        "replicator",
        initial_x=initial,
        max_iterations=120,
        history_stride=20,
    )
    assert np.all(result.x[:, 0] == 0.0)
    assert not result.support_reactivated


def test_distributed_population_layer_tracks_the_common_aggregate() -> None:
    world = _world(717)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    result = run_distributed_population_game(
        world,
        adjacency,
        "bnn",
        max_iterations=1_500,
        tolerance=1e-3,
        consensus_tolerance=1e-3,
        history_stride=100,
    )
    assert result.information_mode == "dynamic_average_consensus"
    assert result.messages > 0
    assert result.bytes_sent == result.messages * world.n_loads * 8
    assert result.simplex_violation <= 1e-9
    assert result.consensus_residual < float(result.history.iloc[0]["consensus_residual"])


def test_central_vgne_satisfies_projected_kkt_residuals() -> None:
    world = _world(715)
    result = solve_central_vgne(world)
    assert result.converged, result.stop_reason
    assert result.kkt_residual <= 5e-5
    assert result.primal_residual <= 1e-6
    assert result.simplex_violation <= 1e-9


def test_distributed_vgne_reduces_kkt_residual_and_preserves_simplex() -> None:
    world = _world(716)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    result = run_distributed_vgne(
        world,
        adjacency,
        max_iterations=4_000,
        tolerance=5e-4,
        history_stride=100,
    )
    assert result.simplex_violation <= 1e-9
    assert np.isfinite(result.kkt_residual)
    assert result.kkt_residual < float(result.history.iloc[0]["kkt"])
    assert result.consensus_residual < 1e-3
