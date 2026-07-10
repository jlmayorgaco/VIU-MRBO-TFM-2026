"""SP4 post-allocation motion pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp4 import runner as sp4_runner
from viu_mrob_tfm.sp4.methods import SP4_METHOD_LABELS, make_sp4_policy, simulate_motion
from viu_mrob_tfm.sp4.metrics import evaluate_motion
from viu_mrob_tfm.sp4.runner import run_sp4_config
from viu_mrob_tfm.sp4.scenario import SP4MotionScenario, iter_sp4_problems, scenario_params_for_generator


SP4_GENERATORS = [
    "setup",
    "open_field_arrival",
    "crossing_traffic",
    "narrow_passage",
    "cluttered_warehouse",
    "communication_limited",
    "long_distance_energy",
    "monte_carlo",
]


def test_sp4_each_scenario_generator_produces_valid_problem() -> None:
    for generator in SP4_GENERATORS:
        problems = list(iter_sp4_problems([generator], seeds=[123]))
        assert problems
        for scenario_generator, _variant_id, _seed, params, problem in problems:
            assert scenario_generator == generator
            assert len(problem.world.robots) == params.n_robots
            assert problem.target_xy.shape == (params.n_robots, 2)
            assert problem.robot_radius_m > 0.0
            assert problem.target_tolerance_m > 0.0
            assert problem.dt_s > 0.0
            assert problem.horizon_s > 0.0
            assert all(robot.spec.max_speed > 0.0 for robot in problem.world.robots)
            assert np.isfinite(problem.target_xy).all()


@pytest.mark.parametrize("method_id", list(SP4_METHOD_LABELS))
def test_sp4_each_method_runs_and_returns_valid_metrics(method_id: str) -> None:
    params = scenario_params_for_generator("open_field_arrival")[0]
    problem = SP4MotionScenario(params).build(seed=11)
    reference = simulate_motion(make_sp4_policy("reference_time_expanded_cbf"), problem)
    result = reference if method_id == "reference_time_expanded_cbf" else simulate_motion(make_sp4_policy(method_id), problem)

    metrics = evaluate_motion(problem, result, reference_result=reference)

    assert result.positions.shape[1:] == (len(problem.world.robots), 2)
    assert result.velocities.shape == result.positions.shape
    assert 0.0 <= metrics.arrival_success_rate <= 1.0
    assert 0.0 <= metrics.timeout_rate <= 1.0
    assert metrics.travel_distance_m >= 0.0
    assert metrics.energy_proxy_wh >= 0.0
    assert metrics.max_speed_violation_mps <= 1e-6
    assert metrics.performance_gap_vs_reference >= 0.0
    assert metrics.optimality_gap_vs_reference >= 0.0
    assert metrics.performance_gap_vs_reference == pytest.approx(metrics.optimality_gap_vs_reference)


def test_sp4_direct_open_field_reaches_all_targets() -> None:
    params = scenario_params_for_generator("open_field_arrival")[0]
    problem = SP4MotionScenario(params).build(seed=5)
    result = simulate_motion(make_sp4_policy("direct_to_target"), problem)
    metrics = evaluate_motion(problem, result)

    assert metrics.arrival_success_rate == pytest.approx(1.0)
    assert metrics.timeout_rate == pytest.approx(0.0)
    assert metrics.collision_count == 0


def test_sp4_reference_collision_not_worse_than_direct_on_crossing() -> None:
    params = scenario_params_for_generator("crossing_traffic")[0]
    problem = SP4MotionScenario(params).build(seed=8)
    direct = simulate_motion(make_sp4_policy("direct_to_target"), problem)
    reference = simulate_motion(make_sp4_policy("reference_time_expanded_cbf"), problem)
    direct_metrics = evaluate_motion(problem, direct, reference_result=reference)
    reference_metrics = evaluate_motion(problem, reference, reference_result=reference)

    assert reference_metrics.collision_rate <= direct_metrics.collision_rate + 1e-9
    assert reference_metrics.arrival_success_rate >= 0.5


def test_sp4_runner_writes_plots_videos_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _result, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _result, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp4_runner, "save_motion_snapshot", fake_snapshot)
    monkeypatch.setattr(sp4_runner, "save_motion_video", fake_video)
    config = {
        "experiment_id": "SP4_TEST_smoke",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp4"),
        "seeds": {"start": 5100, "count": 2},
        "scenarios": [
            {"param_generator": "open_field_arrival"},
            {"param_generator": "crossing_traffic"},
        ],
        "methods": [
            {"id": "direct_to_target"},
            {"id": "cbf_safety_filter"},
            {"id": "smith_motion_field"},
            {"id": "reference_time_expanded_cbf"},
        ],
        "hypotheses": [
            {
                "id": "H_TEST_reference_collision",
                "metric": "collision_rate",
                "method_a": "reference_time_expanded_cbf",
                "method_b": "direct_to_target",
                "direction": "less",
            }
        ],
        "trajectory_sample_runs": 2,
        "artifacts": {"save_video": True, "video": {"max_per_scenario": 2, "selection_metric": "arrival_success_rate", "duration_s": 2, "final_hold_s": 0.5}},
    }
    config_path = tmp_path / "sp4.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp4_config(config_path)

    assert manifest["runs"] == 16
    assert (tmp_path / "sp4" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp4" / "tables" / "robot_status.csv").exists()
    assert (tmp_path / "sp4" / "tables" / "trajectory_samples.csv").exists()
    assert (tmp_path / "sp4" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp4" / "tables" / "hypothesis_results.csv").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_arrival_success_by_method.png").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_collision_rate_by_scenario.png").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_time_energy_pareto.png").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_clearance_by_method.png").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_path_efficiency_by_method.png").exists()
    assert (tmp_path / "sp4" / "figures" / "sp4_communication_radius_degradation.png").exists()
    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"open_field_arrival", "crossing_traffic"}
    runs_text = (tmp_path / "sp4" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "arrival_success_rate" in runs_text
    assert "collision_rate" in runs_text
    assert "performance_gap_vs_reference" in runs_text
    assert "optimality_gap_vs_reference" in runs_text
    hypothesis_text = (tmp_path / "sp4" / "tables" / "hypothesis_results.csv").read_text(encoding="utf-8")
    assert "p_value_holm" in hypothesis_text
    assert "reject_holm" in hypothesis_text
    audit = json.loads((tmp_path / "sp4" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0
    assert audit["gates"]["G4_reference_no_worse_collision_than_direct"]["passed"] is True
