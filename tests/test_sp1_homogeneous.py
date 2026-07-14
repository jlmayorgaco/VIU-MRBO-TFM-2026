from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp1.homogeneous import (
    evaluate_assignment,
    fitness,
    hungarian_exact,
    make_homogeneous_world,
    potential,
    quorum_closure,
    run_homogeneous_campaign,
    vector_field,
)


def test_homogeneous_exact_assignment_satisfies_common_quorum() -> None:
    world = make_homogeneous_world(seed=7, n_robots=8, quorum=2, geometry="uniform", graph="complete")
    labels = hungarian_exact(world)
    metrics = evaluate_assignment(world, labels, optimal_distance=1.0)
    assert metrics.valid
    assert np.array_equal(np.bincount(labels, minlength=world.n_loads), np.full(world.n_loads, 2))


def test_homogeneous_fitness_matches_potential_gradient() -> None:
    world = make_homogeneous_world(seed=11, n_robots=8, quorum=1, geometry="uniform", graph="complete")
    x = np.full((world.n_robots, world.n_loads), 1.0 / world.n_loads)
    values, _ = fitness(world, x, alpha=5.0, beta=1.0, consensus_rounds=1)
    direction = np.zeros_like(x)
    direction[0, 0] = 1.0
    direction[0, 1] = -1.0
    eps = 1.0e-7
    numerical = (
        potential(world, x + eps * direction, alpha=5.0, beta=1.0)
        - potential(world, x - eps * direction, alpha=5.0, beta=1.0)
    ) / (2.0 * eps)
    analytical = values[0, 0] - values[0, 1]
    assert numerical == pytest.approx(analytical, abs=1.0e-6)


def test_smith_field_conserves_each_robot_mass() -> None:
    rng = np.random.default_rng(13)
    x = rng.dirichlet(np.ones(4), size=6)
    values = rng.normal(size=x.shape)
    field = vector_field(x, values, "SMITH")
    assert np.allclose(np.sum(field, axis=1), 0.0, atol=1.0e-12)


@pytest.mark.parametrize("protocol", ["SMITH", "REPLICATOR", "BNN"])
def test_exact_information_protocols_conserve_mass_and_ascend_potential(protocol: str) -> None:
    rng = np.random.default_rng(19)
    world = make_homogeneous_world(
        seed=19, n_robots=8, quorum=2, geometry="uniform", graph="complete"
    )
    x = rng.dirichlet(np.ones(world.n_loads), size=world.n_robots)
    values, _ = fitness(world, x, alpha=5.0, beta=1.0, consensus_rounds=1)
    field = vector_field(x, values, protocol)
    assert np.allclose(np.sum(field, axis=1), 0.0, atol=1.0e-12)
    assert float(np.sum(values * field)) >= -1.0e-12


def test_quorum_closure_is_valid_and_preference_sensitive() -> None:
    world = make_homogeneous_world(seed=17, n_robots=8, quorum=2, geometry="clustered", graph="ring")
    first = np.zeros((world.n_robots, world.n_loads))
    first[np.arange(world.n_robots), np.arange(world.n_robots) % world.n_loads] = 1.0
    second = np.fliplr(first)
    labels_first = quorum_closure(world, first)
    labels_second = quorum_closure(world, second)
    assert evaluate_assignment(world, labels_first, optimal_distance=1.0).valid
    assert evaluate_assignment(world, labels_second, optimal_distance=1.0).valid
    assert not np.array_equal(labels_first, labels_second)


def test_small_homogeneous_campaign_writes_stage_artifacts(tmp_path: Path) -> None:
    config = {
        "experiment_id": "SP1_HOMOGENEOUS_TEST",
        "output_dir": str(tmp_path / "result"),
        "confirmatory": False,
        "base_seed": 990000,
        "replicates_per_cell": 2,
        "factors": {"n_robots": [8], "quorum": [1, 2], "geometry": ["uniform"], "graph": ["complete"]},
        "population": {"alpha": 5.0, "beta": 1.0, "dt": 0.02, "max_steps": 20, "tolerance": 1.0e-4, "stable_steps": 3, "consensus_rounds": 2},
        "methods": ["smith_qr", "uniform_qr", "greedy", "hungarian_exact"],
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    result = run_homogeneous_campaign(config_path)
    output = tmp_path / "result"
    assert result["manifest"]["runs"] == 16
    assert (output / "tables" / "assignments_raw.parquet").exists()
    assert (output / "tables" / "assignments_closed.parquet").exists()
    assert (output / "report.md").exists()
