"""SP5 cooperative payload transport pipeline tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp5 import runner as sp5_runner
from viu_mrob_tfm.sp5.methods import SP5_METHOD_LABELS, make_sp5_policy, simulate_transport
from viu_mrob_tfm.sp5.metrics import evaluate_transport
from viu_mrob_tfm.sp5.runner import run_sp5_config
from viu_mrob_tfm.sp5.scenario import SP5TransportScenario, iter_sp5_problems, scenario_params_for_generator


SP5_GENERATORS = [
    "setup",
    "formation_corridor_push",
    "cargo_overhead_delivery",
    "multi_group_crossing_push",
    "overactuated_push_drag",
    "scarce_cargo_multi_load",
    "monte_carlo",
]


def test_sp5_each_scenario_generator_produces_valid_problem() -> None:
    for generator in SP5_GENERATORS:
        problems = list(iter_sp5_problems([generator], seeds=[123]))
        assert problems
        for scenario_generator, _variant_id, _seed, params, problem in problems:
            assert scenario_generator == generator
            assert len(problem.world.robots) == params.n_robots
            assert len(problem.world.loads) == params.n_loads
            assert len(problem.load_slots) == params.n_loads
            assert problem.task.initial_pose.shape == (3,)
            assert problem.task.target_pose.shape == (3,)
            assert problem.dt_s > 0.0
            assert problem.horizon_s > 0.0
            assert problem.pickup_horizon_s > 0.0
            assert all(robot.spec.max_speed > 0.0 for robot in problem.world.robots)
            assert np.isfinite(problem.task.initial_pose).all()
            assert np.isfinite(problem.task.target_pose).all()


def test_sp5_each_method_runs_and_returns_valid_metrics() -> None:
    params = scenario_params_for_generator("formation_corridor_push")[0]
    problem = SP5TransportScenario(params).build(seed=11)
    reference = simulate_transport(make_sp5_policy("reference_centralized_mpc_cbf_cargo"), problem)

    for method_id in SP5_METHOD_LABELS:
        result = reference if method_id == "reference_centralized_mpc_cbf_cargo" else simulate_transport(make_sp5_policy(method_id), problem)
        metrics = evaluate_transport(problem, result, reference_result=reference)

        assert result.load_pose.shape[1] == 3
        assert result.robot_positions.shape[1:] == (len(problem.world.robots), 2)
        assert result.robot_velocities.shape == result.robot_positions.shape
        assert np.isfinite(result.load_pose).all()
        assert np.isfinite(result.robot_positions).all()
        assert 0.0 <= metrics.formation_integrity_rate <= 1.0
        assert 0.0 <= metrics.formation_broken_rate <= 1.0
        assert 0.0 <= metrics.collision_rate
        assert metrics.final_position_error_m >= 0.0
        assert metrics.energy_proxy_wh >= 0.0
        assert metrics.max_speed_violation_mps <= 1e-6
        assert metrics.min_load_clearance_m >= -1e-6
        assert metrics.performance_gap_vs_reference >= 0.0
        assert metrics.optimality_gap_vs_reference == metrics.performance_gap_vs_reference


def test_sp5_cargo_mode_uses_cargo_transport_and_assigns_robots() -> None:
    params = scenario_params_for_generator("cargo_overhead_delivery")[0]
    problem = SP5TransportScenario(params).build(seed=7)
    result = simulate_transport(make_sp5_policy("ours_hamiltonian_cargo"), problem)
    metrics = evaluate_transport(problem, result)

    assert result.transport_mode == "cargo"
    assert metrics.assigned_robots >= 1
    assert np.any(result.phase == 1)
    assert metrics.mean_wrench_residual_norm >= 0.0


def test_sp5_mobile_traffic_is_a_hard_barrier_for_all_methods() -> None:
    params = scenario_params_for_generator("multi_group_crossing_push")[0]
    problem = SP5TransportScenario(params).build(seed=6101)

    for method_id in SP5_METHOD_LABELS:
        result = simulate_transport(make_sp5_policy(method_id), problem)
        metrics = evaluate_transport(problem, result)

        assert metrics.min_mobile_group_clearance_m >= problem.safety_margin_m - 1e-6, method_id
        assert metrics.collision_count == 0, method_id


def test_sp5_detects_solid_load_overlap() -> None:
    params = scenario_params_for_generator("formation_corridor_push")[0]
    problem = SP5TransportScenario(params).build(seed=42)
    result = simulate_transport(make_sp5_policy("ours_tensor_game_push"), problem)
    other_load = problem.world.loads[1]
    overlapped_pose = result.load_pose.copy()
    overlapped_pose[:, :2] = other_load.pickup
    overlapped_pose[:, 2] = 0.0
    collided = replace(result, load_pose=overlapped_pose)

    metrics = evaluate_transport(problem, collided)

    assert metrics.min_load_clearance_m < 0.0
    assert metrics.collision_count > 0


def test_sp5_runner_writes_plots_videos_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _result, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _result, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp5_runner, "save_transport_snapshot", fake_snapshot)
    monkeypatch.setattr(sp5_runner, "save_transport_video", fake_video)
    config = {
        "experiment_id": "SP5_TEST_smoke",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp5"),
        "seeds": {"start": 6100, "count": 2},
        "scenarios": [
            {"param_generator": "formation_corridor_push"},
            {"param_generator": "cargo_overhead_delivery"},
        ],
        "methods": [
            {"id": "classic_decentralized_apf_push"},
            {"id": "sota_centralized_cbf_push"},
            {"id": "ours_hamiltonian_cargo"},
            {"id": "reference_centralized_mpc_cbf_cargo"},
        ],
        "hypotheses": [
            {
                "id": "H_TEST_reference_gap",
                "metric": "performance_gap_vs_reference",
                "method_a": "reference_centralized_mpc_cbf_cargo",
                "method_b": "classic_decentralized_apf_push",
                "direction": "less",
            }
        ],
        "trajectory_sample_runs": 2,
        "artifacts": {"save_video": True, "video": {"max_per_scenario": 2, "selection_metric": "score_value", "duration_s": 2, "final_hold_s": 0.5}},
    }
    config_path = tmp_path / "sp5.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp5_config(config_path)

    assert manifest["runs"] == 16
    assert (tmp_path / "sp5" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp5" / "tables" / "robot_status.csv").exists()
    assert (tmp_path / "sp5" / "tables" / "trajectory_samples.csv").exists()
    assert (tmp_path / "sp5" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp5" / "tables" / "hypothesis_results.csv").exists()
    assert (tmp_path / "sp5" / "tables" / "video_catalog.csv").exists()
    assert (tmp_path / "sp5" / "videos" / "VIDEO_INDEX.md").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_transport_success_by_method.png").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_final_pose_error_by_method.png").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_formation_error_by_method.png").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_collision_rate_by_scenario.png").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_quality_resource_pareto.png").exists()
    assert (tmp_path / "sp5" / "figures" / "sp5_push_drag_vs_cargo.png").exists()
    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"formation_corridor_push", "cargo_overhead_delivery"}
    runs_text = (tmp_path / "sp5" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "transport_success" in runs_text
    assert "formation_integrity_rate" in runs_text
    assert "selected_task_load" in runs_text
    audit = json.loads((tmp_path / "sp5" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0
    assert audit["passed"] is True
