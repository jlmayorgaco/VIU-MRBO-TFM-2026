"""Focused tests for the confirmatory SP3 wrench Nash game."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp3.scenario import SP3WrenchScenario, scenario_params_for_generator
from viu_mrob_tfm.sp3.wrench_nash_game import (
    build_action_model,
    decode_preferences,
    potential_gradient,
    potential_value,
    project_simplex,
    run_sp3_wrench_nash_config,
    simulate_wrench_game,
    solve_relaxed_qp,
)


def _problem(generator: str = "bar_torque_pure", seed: int = 7):
    return SP3WrenchScenario(scenario_params_for_generator(generator)[0]).build(seed)


def test_simplex_projection_is_nonnegative_and_mass_preserving() -> None:
    projected = project_simplex(np.array([-1.0, 0.2, 2.5, 0.3]))
    assert np.all(projected >= 0.0)
    assert float(np.sum(projected)) == pytest.approx(1.0)


def test_potential_gradient_matches_finite_difference() -> None:
    problem = _problem("off_center_com")
    model = build_action_model(problem)
    rng = np.random.default_rng(13)
    preferences = np.vstack([project_simplex(rng.random(model.n_actions + 1)) for _ in problem.world.robots])
    analytic = potential_gradient(preferences, model)
    eps = 1e-6
    for robot_idx, action_idx in [(0, 1), (1, min(2, model.n_actions))]:
        plus = preferences.copy()
        minus = preferences.copy()
        plus[robot_idx, action_idx] += eps
        minus[robot_idx, action_idx] -= eps
        numeric = (potential_value(plus, model) - potential_value(minus, model)) / (2.0 * eps)
        assert numeric == pytest.approx(analytic[robot_idx, action_idx], abs=2e-6)


@pytest.mark.parametrize("protocol", ["projected_pd", "smith", "replicator", "erv_bnn"])
def test_game_protocols_preserve_simplex(protocol: str) -> None:
    result = simulate_wrench_game(_problem(), protocol=protocol, steps=80)
    assert result.simplex_error <= 1e-12
    assert np.all(np.isfinite(result.preferences))
    assert np.all(result.preferences >= -1e-12)


def test_relaxed_qp_dominates_random_feasible_preferences() -> None:
    problem = _problem("off_center_com")
    model = build_action_model(problem)
    optimum, value, success = solve_relaxed_qp(problem)
    assert success
    assert np.max(np.sum(optimum[:, 1:], axis=0)) <= 1.0 + 1e-7
    rng = np.random.default_rng(44)
    for _ in range(20):
        candidate = np.vstack([project_simplex(rng.random(model.n_actions + 1)) for _ in problem.world.robots])
        occupancy = np.sum(candidate[:, 1:], axis=0)
        candidate[:, 1:] /= max(float(np.max(occupancy)), 1.0)
        candidate[:, 0] = 1.0 - np.sum(candidate[:, 1:], axis=1)
        assert potential_value(candidate, model) <= value + 1e-6


def test_guarded_closure_removes_wrench_false_positives() -> None:
    problem = _problem("slot_saturation")
    result = simulate_wrench_game(problem, protocol="projected_pd", steps=120)
    _raw, closed = decode_preferences(problem, result.preferences, guarded=True, method="test_guarded")
    for load_idx in range(len(problem.world.loads)):
        if np.any(closed.labels == load_idx + 1):
            from viu_mrob_tfm.sp3.methods import wrench_fit

            assert wrench_fit(problem, closed, load_idx).residual_norm <= problem.wrench_tolerance


def test_smoke_campaign_writes_audited_artifacts(tmp_path: Path) -> None:
    config = {
        "experiment_id": "SP3_TEST_WRENCH_NASH",
        "output_dir": str(tmp_path / "out"),
        "audit_worlds": 2,
        "seeds": {"start": 9000, "count": 1},
        "scenarios": [{"param_generator": "bar_torque_pure"}, {"param_generator": "slot_saturation"}],
        "game": {"steps": 60, "dt": 0.06, "dual_dt": 0.08, "regularization": 0.025, "tolerance": 0.001, "consensus_rounds": 3},
        "methods": [
            {"id": "wrench_oracle", "kind": "allocator"},
            {"id": "oracle_scalar_assignment", "kind": "allocator"},
            {"id": "nash_pd_exact_guarded", "kind": "game", "protocol": "projected_pd", "graph": "complete", "guarded": True},
            {"id": "nash_pd_ring_guarded", "kind": "game", "protocol": "projected_pd", "graph": "ring", "guarded": True},
        ],
        "hypotheses": [
            {"id": "H-test", "metric": "optimality_gap_vs_wrench_oracle", "method_a": "nash_pd_exact_guarded", "method_b": "oracle_scalar_assignment", "direction": "less"}
        ],
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run_sp3_wrench_nash_config(path)
    output = Path(manifest["output_dir"])
    assert manifest["runs"] == 8
    assert (output / "tables" / "runs.csv").exists()
    assert (output / "tables" / "summary.csv").exists()
    assert (output / "tables" / "hypothesis_results.csv").exists()
    assert (output / "figures" / "fig-sp3-wrench-game-performance.png").exists()
    audit = json.loads((output / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["guarded_false_positive_violations"] == 0
    assert audit["max_simplex_error"] <= 1e-10
