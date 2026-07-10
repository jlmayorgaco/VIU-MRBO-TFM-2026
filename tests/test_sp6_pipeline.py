"""SP6 operational robustness pipeline tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp6 import runner as sp6_runner
from viu_mrob_tfm.sp6.methods import SP6_METHOD_LABELS, make_sp6_policy, simulate_recovery
from viu_mrob_tfm.sp6.metrics import evaluate_recovery
from viu_mrob_tfm.sp6.runner import run_sp6_config
from viu_mrob_tfm.sp6.scenario import SP6RobustnessScenario, iter_sp6_problems, scenario_params_for_generator


SP6_GENERATORS = [
    "setup",
    "communication_radius_decay",
    "robot_dropout_mid_task",
    "battery_depletion_reallocation",
    "blocked_corridor_recovery",
    "infeasible_load_detection",
    "delayed_information_consensus",
    "multi_load_priority_shift",
    "monte_carlo",
]


def test_sp6_each_scenario_generator_produces_valid_problem() -> None:
    for generator in SP6_GENERATORS:
        problems = list(iter_sp6_problems([generator], seeds=[123]))
        assert problems
        for scenario_generator, _variant_id, _seed, params, problem in problems:
            assert scenario_generator == generator
            assert len(problem.world.robots) == params.n_robots
            assert len(problem.world.loads) == params.n_loads
            assert problem.robot_radius_m > 0.0
            assert problem.target_tolerance_m > 0.0
            assert problem.dt_s > 0.0
            assert problem.horizon_s > 0.0
            assert problem.event.time_s > 0.0
            assert all(robot.spec.max_speed > 0.0 for robot in problem.world.robots)
            assert all(np.isfinite(load.destination).all() for load in problem.world.loads)
            assert _min_payload_obstacle_clearance(problem, problem.initial_load_poses, 0.0) >= -1e-6
            assert _min_payload_obstacle_clearance(problem, problem.target_load_poses, problem.event.time_s + problem.dt_s) >= -1e-6
            assert _min_payload_pair_clearance(problem, problem.initial_load_poses) >= -1e-6
            assert _min_payload_pair_clearance(problem, problem.target_load_poses) >= -1e-6


@pytest.mark.parametrize("method_id", list(SP6_METHOD_LABELS))
def test_sp6_each_method_runs_and_returns_valid_metrics(method_id: str) -> None:
    params = scenario_params_for_generator("robot_dropout_mid_task")[0]
    problem = SP6RobustnessScenario(params).build(seed=11)
    reference = simulate_recovery(make_sp6_policy("reference_resilient_oracle"), problem)
    result = reference if method_id == "reference_resilient_oracle" else simulate_recovery(make_sp6_policy(method_id), problem)

    metrics = evaluate_recovery(problem, result, reference_result=reference)

    assert result.robot_positions.shape[1:] == (len(problem.world.robots), 2)
    assert result.robot_velocities.shape == result.robot_positions.shape
    assert result.load_pose.shape[1:] == (len(problem.world.loads), 3)
    assert result.load_velocity.shape == result.load_pose.shape
    assert result.labels.shape[1] == len(problem.world.robots)
    assert result.completed_loads.shape[1] == len(problem.world.loads)
    assert np.isfinite(result.robot_positions).all()
    assert np.isfinite(result.robot_velocities).all()
    assert np.isfinite(result.load_pose).all()
    assert np.max(np.linalg.norm(result.load_pose[-1, :, :2] - result.load_pose[0, :, :2], axis=1)) > 0.05
    assert 0.0 <= metrics.task_completion_rate <= 1.0
    assert 0.0 <= metrics.lost_load_rate <= 1.0
    assert 0.0 <= metrics.infeasible_load_detection_rate <= 1.0
    assert 0.0 <= metrics.post_event_wrench_feasible_rate <= 1.0
    assert metrics.travel_distance_m >= 0.0
    assert metrics.energy_proxy_wh >= 0.0
    assert metrics.max_speed_violation_mps <= 1e-6
    assert metrics.collision_count == 0
    assert metrics.min_load_clearance_m >= -1e-6
    assert metrics.performance_gap_vs_reference >= 0.0
    assert metrics.optimality_gap_vs_reference == pytest.approx(metrics.performance_gap_vs_reference)


def test_sp6_robot_dropout_reduces_active_count() -> None:
    params = scenario_params_for_generator("robot_dropout_mid_task")[0]
    problem = SP6RobustnessScenario(params).build(seed=17)
    result = simulate_recovery(make_sp6_policy("ours_guarded_wrench_market_recovery"), problem)

    assert int(np.sum(result.active_mask[-1])) < len(problem.world.robots)
    assert result.reassignment_count > 0


def test_sp6_infeasible_load_detection_contains_true_infeasible_load() -> None:
    params = scenario_params_for_generator("infeasible_load_detection")[0]
    problem = SP6RobustnessScenario(params).build(seed=19)
    result = simulate_recovery(make_sp6_policy("ours_guarded_wrench_market_recovery"), problem)
    metrics = evaluate_recovery(problem, result)

    assert not bool(result.feasible_after_event[0])
    assert metrics.infeasible_load_count >= 1
    assert 0.0 <= metrics.infeasible_load_detection_rate <= 1.0


def test_sp6_detects_solid_load_overlap() -> None:
    params = scenario_params_for_generator("robot_dropout_mid_task")[0]
    problem = SP6RobustnessScenario(params).build(seed=23)
    result = simulate_recovery(make_sp6_policy("ours_guarded_wrench_market_recovery"), problem)
    overlapped_pose = result.load_pose.copy()
    overlapped_pose[:, 1, :] = overlapped_pose[:, 0, :]
    collided = replace(result, load_pose=overlapped_pose)

    metrics = evaluate_recovery(problem, collided)

    assert metrics.min_load_clearance_m < 0.0
    assert metrics.collision_count > 0


def test_sp6_communication_radius_decay_is_observable_after_delay() -> None:
    params = scenario_params_for_generator("communication_radius_decay")[0]
    problem = SP6RobustnessScenario(params).build(seed=21)

    before = problem.communication_radius_at(problem.event.time_s - problem.dt_s)
    after = problem.communication_radius_at(problem.event.time_s + problem.dt_s)

    assert np.isinf(before)
    assert after == pytest.approx(problem.event.communication_radius_after_m)


def test_sp6_runner_writes_plots_videos_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _result, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _result, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp6_runner, "save_recovery_snapshot", fake_snapshot)
    monkeypatch.setattr(sp6_runner, "save_recovery_video", fake_video)
    config = {
        "experiment_id": "SP6_TEST_smoke",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp6"),
        "seeds": {"start": 7100, "count": 2},
        "scenarios": [
            {"param_generator": "robot_dropout_mid_task"},
            {"param_generator": "infeasible_load_detection"},
        ],
        "methods": [
            {"id": "classic_decentralized_greedy_recovery"},
            {"id": "cbba_recovery"},
            {"id": "smith_qr_recovery"},
            {"id": "ours_guarded_wrench_market_recovery"},
            {"id": "reference_resilient_oracle"},
        ],
        "hypotheses": [
            {
                "id": "H_TEST_lost_load",
                "metric": "lost_load_rate",
                "method_a": "ours_guarded_wrench_market_recovery",
                "method_b": "classic_decentralized_greedy_recovery",
                "direction": "less",
            }
        ],
        "trajectory_sample_runs": 2,
        "artifacts": {"save_video": True, "video": {"max_per_scenario": 2, "selection_metric": "score_value", "duration_s": 2, "final_hold_s": 0.5}},
    }
    config_path = tmp_path / "sp6.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp6_config(config_path)

    assert manifest["runs"] == 20
    assert (tmp_path / "sp6" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "robot_status.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "load_status.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "trajectory_samples.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "hypothesis_results.csv").exists()
    assert (tmp_path / "sp6" / "tables" / "video_catalog.csv").exists()
    assert (tmp_path / "sp6" / "videos" / "VIDEO_INDEX.md").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_recovery_success_by_method.png").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_lost_load_degradation_by_scenario.png").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_recovery_time_by_method.png").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_safety_by_method.png").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_communication_resource_pareto.png").exists()
    assert (tmp_path / "sp6" / "figures" / "sp6_completion_vs_reassignment.png").exists()
    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"robot_dropout_mid_task", "infeasible_load_detection"}
    runs_text = (tmp_path / "sp6" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "recovery_success" in runs_text
    assert "lost_load_rate" in runs_text
    assert "infeasible_load_detection_rate" in runs_text
    assert "post_event_wrench_feasible_rate" in runs_text
    assert "load_target_reached_rate" in runs_text
    assert "replacement_arrival_time_s" in runs_text
    audit = json.loads((tmp_path / "sp6" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0
    assert audit["passed"] is True


def _min_payload_obstacle_clearance(problem, poses: np.ndarray, t_s: float) -> float:
    values: list[float] = []
    for load_idx, load in enumerate(problem.world.loads):
        for obstacle in problem.active_obstacles_at(t_s):
            values.append(_payload_rectangle_circle_clearance(poses[load_idx], float(load.length_m), float(load.width_m), obstacle.center, float(obstacle.radius)))
    return min(values) if values else float("inf")


def _min_payload_pair_clearance(problem, poses: np.ndarray) -> float:
    values: list[float] = []
    for i, load_i in enumerate(problem.world.loads):
        for j in range(i + 1, len(problem.world.loads)):
            load_j = problem.world.loads[j]
            values.append(_payload_rectangle_rectangle_clearance(poses[i], float(load_i.length_m), float(load_i.width_m), poses[j], float(load_j.length_m), float(load_j.width_m)))
    return min(values) if values else float("inf")


def _payload_rectangle_circle_clearance(q: np.ndarray, length_m: float, width_m: float, center: np.ndarray, radius_m: float) -> float:
    theta = float(q[2])
    c = np.cos(theta)
    s = np.sin(theta)
    rotation_t = np.array([[c, s], [-s, c]], dtype=float)
    local = rotation_t @ (np.asarray(center, dtype=float) - np.asarray(q[:2], dtype=float))
    half_extents = np.array([0.5 * float(length_m), 0.5 * float(width_m)], dtype=float)
    outside = np.maximum(np.abs(local) - half_extents, 0.0)
    return float(np.linalg.norm(outside) - float(radius_m))


def _payload_rectangle_rectangle_clearance(q_a: np.ndarray, length_a_m: float, width_a_m: float, q_b: np.ndarray, length_b_m: float, width_b_m: float) -> float:
    vec = np.asarray(q_a[:2], dtype=float) - np.asarray(q_b[:2], dtype=float)
    dist = float(np.linalg.norm(vec))
    normal = np.array([1.0, 0.0], dtype=float) if dist <= 1e-9 else vec / dist
    return float(dist - _payload_support_radius(q_a, length_a_m, width_a_m, normal) - _payload_support_radius(q_b, length_b_m, width_b_m, -normal))


def _payload_support_radius(q: np.ndarray, length_m: float, width_m: float, normal: np.ndarray) -> float:
    theta = float(q[2])
    c = np.cos(theta)
    s = np.sin(theta)
    rotation = np.array([[c, -s], [s, c]], dtype=float)
    return float(
        0.5 * float(length_m) * abs(float(np.dot(normal, rotation[:, 0])))
        + 0.5 * float(width_m) * abs(float(np.dot(normal, rotation[:, 1])))
    )
