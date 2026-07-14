from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp1.homogeneous import vector_field
from viu_mrob_tfm.sp2.heterogeneous_game import (
    evaluate_assignment, fitness, make_heterogeneous_world, milp_exact, potential,
    preference_closure, run_heterogeneous_campaign,
)


@pytest.mark.parametrize("mode", ["marginal_deficit", "marginal_log"])
def test_aligned_fitness_matches_potential_directional_derivative(mode: str) -> None:
    world = make_heterogeneous_world(seed=5, n_robots=8, n_loads=3, heterogeneity="high", demand_ratio=1.0, geometry="uniform", graph="complete")
    x = np.full((world.n_robots, world.n_loads + 1), 1.0 / (world.n_loads + 1))
    values, _ = fitness(world, x, fitness_mode=mode, alpha=4.0, beta=0.35, epsilon=0.2, consensus_rounds=1)
    direction = np.zeros_like(x); direction[0, 1] = 1.0; direction[0, 2] = -1.0
    eps = 1.0e-7
    numerical = (potential(world, x + eps * direction, fitness_mode=mode, alpha=4.0, beta=0.35, epsilon=0.2) - potential(world, x - eps * direction, fitness_mode=mode, alpha=4.0, beta=0.35, epsilon=0.2)) / (2 * eps)
    assert numerical == pytest.approx(values[0, 1] - values[0, 2], abs=1.0e-6)


@pytest.mark.parametrize("protocol", ["SMITH", "REPLICATOR", "BNN"])
def test_revision_fields_conserve_mass_and_ascend_aligned_potential(protocol: str) -> None:
    world = make_heterogeneous_world(seed=7, n_robots=8, n_loads=3, heterogeneity="high", demand_ratio=0.9, geometry="clustered", graph="complete")
    x = np.random.default_rng(7).dirichlet(np.ones(world.n_loads + 1), world.n_robots)
    values, _ = fitness(world, x, fitness_mode="marginal_deficit", alpha=4.0, beta=0.35, epsilon=0.2, consensus_rounds=1)
    field = vector_field(x, values, protocol)
    assert np.allclose(field.sum(axis=1), 0.0, atol=1.0e-12)
    assert float(np.sum(values * field)) >= -1.0e-12


def test_milp_dominates_preference_closure() -> None:
    world = make_heterogeneous_world(seed=9, n_robots=8, n_loads=3, heterogeneity="high", demand_ratio=1.0, geometry="uniform", graph="complete")
    preferences = np.random.default_rng(9).dirichlet(np.ones(world.n_loads + 1), world.n_robots)
    heuristic = preference_closure(world, preferences)
    exact = milp_exact(world, partial_weight=0.3, distance_weight=0.08)
    exact_metrics = evaluate_assignment(world, exact, optimal_value=None, partial_weight=0.3, distance_weight=0.08)
    heuristic_metrics = evaluate_assignment(world, heuristic, optimal_value=exact_metrics.objective_value, partial_weight=0.3, distance_weight=0.08)
    assert heuristic_metrics.normalized_regret >= 0.0
    assert exact_metrics.objective_value + 1.0e-8 >= heuristic_metrics.objective_value


def test_small_campaign_writes_factorial_artifacts(tmp_path: Path) -> None:
    config = {
        "experiment_id": "SP2_HET_TEST", "output_dir": str(tmp_path / "result"), "confirmatory": False,
        "base_seed": 990100, "replicates_per_cell": 1,
        "factors": {"n_robots": [8], "n_loads": [3], "heterogeneity": ["high"], "demand_ratio": [1.0], "geometry": ["uniform"], "graph": ["complete"]},
        "population": {"alpha": 4.0, "beta": 0.35, "epsilon": 0.2, "dt": 0.01, "max_steps": 30, "tolerance": 0.02, "stable_steps": 3, "consensus_rounds": 2},
        "objective": {"partial_weight": 0.3, "distance_weight": 0.08},
        "methods": ["smith__marginal_deficit", "erv_bnn__plain_deficit", "uniform_closure", "greedy_capacity", "milp_exact"],
    }
    path = tmp_path / "config.yaml"; path.write_text(yaml.safe_dump(config), encoding="utf-8")
    result = run_heterogeneous_campaign(path)
    output = tmp_path / "result"
    assert result["manifest"]["runs"] == 5
    assert (output / "tables" / "assignments_raw.parquet").exists()
    assert (output / "tables" / "assignments_closed.parquet").exists()
    assert (output / "figures" / "sp2_heterogeneous_regret.png").exists()
