from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp4.evidence import execute
from viu_mrob_tfm.sp4.theory import (
    closed_loop_energy_derivative,
    dissipation_upper_bound,
    pairwise_game_gradient,
    pairwise_game_hessian,
    pairwise_game_potential,
    pairwise_player_cost,
)


def test_pairwise_potential_gradient_and_strong_convexity() -> None:
    rng = np.random.default_rng(404)
    preferences = rng.random((3, 3))
    preferences /= preferences.sum(axis=1, keepdims=True)
    costs = rng.normal(size=(3, 3))
    features = rng.random((3, 3, 4))
    direction = rng.normal(size=(3, 3))
    epsilon = 1e-6
    analytic = pairwise_game_gradient(
        preferences,
        costs,
        features,
        congestion_weight=0.52,
        regularization=0.08,
    )
    numeric = (
        pairwise_game_potential(
            preferences + epsilon * direction,
            costs,
            features,
            congestion_weight=0.52,
            regularization=0.08,
        )
        - pairwise_game_potential(
            preferences - epsilon * direction,
            costs,
            features,
            congestion_weight=0.52,
            regularization=0.08,
        )
    ) / (2.0 * epsilon)
    assert numeric == pytest.approx(float(np.sum(analytic * direction)), abs=2e-6)
    hessian = pairwise_game_hessian(
        features, congestion_weight=0.52, regularization=0.08
    )
    assert float(np.min(np.linalg.eigvalsh(hessian))) >= 0.08 - 1e-10


def test_pairwise_player_cost_has_exact_finite_unilateral_differences() -> None:
    rng = np.random.default_rng(405)
    preferences = rng.dirichlet(np.ones(3), size=4)
    deviated = preferences.copy()
    deviated[2] = rng.dirichlet(np.ones(3))
    costs = rng.normal(size=(4, 3))
    features = rng.random((4, 3, 5))
    kwargs = {"congestion_weight": 0.47, "regularization": 0.09}
    potential_difference = pairwise_game_potential(
        deviated, costs, features, **kwargs
    ) - pairwise_game_potential(preferences, costs, features, **kwargs)
    player_difference = pairwise_player_cost(
        deviated, costs, features, 2, **kwargs
    ) - pairwise_player_cost(preferences, costs, features, 2, **kwargs)
    assert player_difference == pytest.approx(potential_difference, abs=1e-12)


def test_pose_storage_dissipates_and_respects_residual_bound() -> None:
    velocity = np.asarray([0.4, -0.2, 0.1])
    damping = np.diag([2.0, 2.0, 1.0])
    derivative = np.diag([4.0, 4.0, 3.0])
    exact = closed_loop_energy_derivative(velocity, damping, derivative)
    assert exact < 0.0
    residual = np.asarray([0.3, -0.1, 0.2])
    disturbed = closed_loop_energy_derivative(
        velocity, damping, derivative, residual
    )
    bound = dissipation_upper_bound(velocity, damping, derivative, residual)
    assert disturbed <= bound + 1e-12


def test_sp4_evidence_regenerates_audited_artifacts(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("experiments/configs/sp4_transport_evidence.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["output_dir"] = str(tmp_path / "sp4")
    config["bootstrap"]["resamples"] = 500
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    output = execute(config_path)
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    macros = (output / "tables" / "sp4_numbers.tex").read_text(encoding="utf-8")
    assert audit["status"] == "passed"
    assert audit["transport_worlds_per_method"] == 18
    assert "\\newcommand{\\SPFourDockWorlds}{108}" in macros
    assert "\\newcommand{\\SPFourTransportWorlds}{18}" in macros
    assert (output / "figures" / "fig-sp4-transport-tradeoff.pdf").is_file()
