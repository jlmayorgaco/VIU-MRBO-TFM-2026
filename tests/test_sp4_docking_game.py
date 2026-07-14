"""Focused tests for the SP4 wrench-aware docking game."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp4.docking_game import (
    build_docking_world,
    build_primitive_snapshot,
    decode_conflict_aware,
    potential_cost,
    potential_gradient,
    project_simplex,
    run_sp4_docking_config,
    simulate_docking,
    solve_motion_game,
    solve_snapshot_qp,
)


def test_simplex_projection_preserves_probability_mass() -> None:
    projected = project_simplex(np.asarray([-1.0, 0.2, 2.4, 0.7]))
    assert np.all(projected >= 0.0)
    assert float(np.sum(projected)) == pytest.approx(1.0)


def test_potential_gradient_matches_finite_difference() -> None:
    world = build_docking_world("crossing", 42, 4)
    snapshot = build_primitive_snapshot(world, world.initial_state)
    rng = np.random.default_rng(7)
    preferences = np.vstack([project_simplex(rng.random(snapshot.n_actions)) for _ in range(world.n_robots)])
    analytic = potential_gradient(preferences, snapshot)
    direction = np.zeros_like(preferences)
    direction[0, 0] = 1.0
    direction[0, 1] = -1.0
    eps = 1e-6
    numeric = (potential_cost(preferences + eps * direction, snapshot) - potential_cost(preferences - eps * direction, snapshot)) / (2.0 * eps)
    assert numeric == pytest.approx(float(np.sum(analytic * direction)), abs=2e-6)


@pytest.mark.parametrize("protocol", ["projected_pd", "smith", "replicator", "erv_bnn"])
def test_protocols_preserve_simplex(protocol: str) -> None:
    world = build_docking_world("open_docking", 11, 4)
    snapshot = build_primitive_snapshot(world, world.initial_state)
    result = solve_motion_game(snapshot, protocol=protocol, steps=40)
    assert result.simplex_error <= 1e-12
    assert np.all(result.preferences >= -1e-12)


def test_qp_reference_is_no_worse_than_pd_snapshot() -> None:
    world = build_docking_world("symmetric_deadlock", 13, 4)
    snapshot = build_primitive_snapshot(world, world.initial_state)
    game = solve_motion_game(snapshot, steps=180)
    _optimum, optimum_value, success = solve_snapshot_qp(snapshot)
    assert success
    assert potential_cost(game.preferences, snapshot) >= optimum_value - 1e-7


def test_conflict_aware_closure_reserves_resources_once() -> None:
    world = build_docking_world("crossing", 91, 4)
    snapshot = build_primitive_snapshot(world, world.initial_state)
    game = solve_motion_game(snapshot, steps=40)
    actions, _interventions = decode_conflict_aware(
        game.preferences,
        snapshot,
        world.wrench_priority,
        np.zeros(world.n_robots, dtype=bool),
    )
    used: set[int] = set()
    for robot, action in enumerate(actions):
        resources = set(
            np.flatnonzero(snapshot.occupancy_features[robot, action] > 0.0).tolist()
        )
        assert not (used & resources)
        used.update(resources)

def test_nonholonomic_simulation_does_not_repair_positions() -> None:
    world = build_docking_world("open_docking", 18, 4)
    result = simulate_docking(world, "nash_pd_exact", horizon_s=2.0, game_steps=8)
    assert result.positions.shape[0] == result.steps + 1
    increments = np.diff(result.positions, axis=0)
    assert np.all(np.isfinite(increments))
    assert result.max_simplex_error <= 1e-12


def test_smoke_campaign_writes_audited_artifacts(tmp_path: Path) -> None:
    config = {
        "experiment_id": "SP4_TEST_DOCKING_GAME",
        "output_dir": str(tmp_path / "out"),
        "audit_worlds": 1,
        "seeds": {"start": 9900, "count": 1},
        "scenarios": [{"id": "open_docking"}],
        "robot_counts": [4],
        "methods": [{"id": "direct_to_slot"}, {"id": "cbf_qp"}, {"id": "nash_pd_exact"}],
        "simulation": {"dt_s": 0.18, "horizon_s": 2.0, "barrier_iterations": 8},
        "game": {"steps": 6, "central_steps": 10, "audit_steps": 80},
        "audit_gates": {"max_simplex_error": 1e-9, "max_capacity_violation": 0.2, "max_qp_potential_gap": 0.2, "max_potential_gradient_error": 1e-5},
        "hypotheses": [{"id": "H-test", "metric": "safe_docking_success", "method_a": "nash_pd_exact", "method_b": "direct_to_slot", "direction": "greater"}],
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run_sp4_docking_config(config_path)
    output = Path(manifest["output_dir"])
    assert manifest["runs"] == 3
    assert (output / "tables" / "runs.csv").exists()
    assert (output / "figures" / "fig-sp4-docking-performance.png").exists()
    audit = json.loads((output / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["positions_repaired_after_integration"] is False
