"""SP3 role/slot wrench-feasibility pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from viu_mrob_tfm.sp3 import runner as sp3_runner
from viu_mrob_tfm.sp3.methods import (
    SP3Assignment,
    SP3_METHOD_LABELS,
    assignment_valid,
    make_sp3_allocator,
    score_assignment,
    wrench_fit,
    wrench_matrix,
)
from viu_mrob_tfm.sp3.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp3.pose_dynamics import pose_transport_summary, simulate_pose_transport
from viu_mrob_tfm.sp3.runner import run_sp3_config, timed_allocate
from viu_mrob_tfm.sp3.scenario import SP3WrenchScenario, iter_sp3_problems, scenario_params_for_generator


SP3_GENERATORS = [
    "setup",
    "point_load_degenerate",
    "bar_torque_pure",
    "one_sided_push",
    "off_center_com",
    "long_payload_slots",
    "slot_saturation",
    "pose_transport_rotate",
    "pose_push_overactuated",
    "pose_push_drag_balanced",
    "pose_cargo_scarce",
    "monte_carlo",
]
SP3_METHODS = [method for method in SP3_METHOD_LABELS if method != "wrench_oracle_reference"]


def test_sp3_wrench_matrix_uses_planar_cross_product() -> None:
    params = scenario_params_for_generator("bar_torque_pure")[0]
    problem = SP3WrenchScenario(params).build(seed=123)

    matrix = wrench_matrix(problem, load_idx=0, robot_indices=[0, 1], slot_indices=[0, 1])

    assert matrix.shape == (3, 2)
    assert matrix[2, 0] == pytest.approx(-1.0)
    assert matrix[2, 1] == pytest.approx(-1.0)


@pytest.mark.parametrize("generator", SP3_GENERATORS)
def test_sp3_each_scenario_generator_produces_valid_problem(generator: str) -> None:
    problems = list(iter_sp3_problems([generator], seeds=[123]))

    assert problems
    for scenario_generator, _variant_id, _seed, params, problem in problems:
        assert scenario_generator == generator
        assert len(problem.world.robots) == params.n_robots
        assert len(problem.world.loads) == params.n_loads
        assert len(problem.load_slots) == len(problem.world.loads)
        assert all(1 <= len(slots) <= 4 for slots in problem.load_slots)
        assert all(robot.spec.capacity.force_limit_n > 0.0 for robot in problem.world.robots)
        assert all(np.isfinite(load.wrench.as_vector()).all() for load in problem.world.loads)


@pytest.mark.parametrize("method_id", SP3_METHODS)
def test_sp3_each_method_returns_valid_role_slot_assignment(method_id: str) -> None:
    params = scenario_params_for_generator("off_center_com")[0]
    problem = SP3WrenchScenario(params).build(seed=11)

    assignment = make_sp3_allocator(method_id).allocate(problem)

    assert assignment.labels.shape == (len(problem.world.robots),)
    assert assignment.slot_labels.shape == assignment.labels.shape
    assert assignment.labels.min() >= 0
    assert assignment.labels.max() <= len(problem.world.loads)
    assert assignment_valid(problem, assignment)


def test_sp3_point_load_degenerate_scalar_feasible_implies_wrench_feasible() -> None:
    params = scenario_params_for_generator("point_load_degenerate")[0]
    problem = SP3WrenchScenario(params).build(seed=7)
    assignment = make_sp3_allocator("oracle_scalar_assignment").allocate(problem)
    diagnostics = load_diagnostics(problem, assignment)

    assert diagnostics[0]["scalar_feasible"] is True
    assert diagnostics[0]["wrench_feasible"] is True
    assert diagnostics[0]["false_positive"] is False


def test_sp3_bar_torque_pure_requires_two_complementary_slots() -> None:
    params = scenario_params_for_generator("bar_torque_pure")[0]
    problem = SP3WrenchScenario(params).build(seed=5)
    one_robot = SP3Assignment(labels=np.array([1, 0, 0, 0]), slot_labels=np.array([1, 0, 0, 0]), method="one")
    two_robot = SP3Assignment(labels=np.array([1, 1, 0, 0]), slot_labels=np.array([1, 2, 0, 0]), method="two")

    assert wrench_fit(problem, one_robot, 0).residual_norm > problem.wrench_tolerance
    assert wrench_fit(problem, two_robot, 0).residual_norm <= problem.wrench_tolerance
    assert load_diagnostics(problem, two_robot)[0]["complementarity_gain"] > 0.0


def test_sp3_slot_saturation_has_scalar_false_positive() -> None:
    params = scenario_params_for_generator("slot_saturation")[0]
    problem = SP3WrenchScenario(params).build(seed=6)
    assignment = make_sp3_allocator("oracle_scalar_assignment").allocate(problem)
    diagnostics = load_diagnostics(problem, assignment)

    assert diagnostics[0]["scalar_feasible"] is True
    assert diagnostics[0]["wrench_feasible"] is False
    assert diagnostics[0]["false_positive"] is True


def test_sp3_wrench_oracle_does_not_accept_scalar_false_positives() -> None:
    params = scenario_params_for_generator("slot_saturation")[0]
    problem = SP3WrenchScenario(params).build(seed=6)
    assignment = make_sp3_allocator("wrench_oracle").allocate(problem)
    diagnostics = load_diagnostics(problem, assignment)

    assert all(not row["false_positive"] for row in diagnostics)


def test_sp3_oracle_dominates_methods_under_wrench_score() -> None:
    params = scenario_params_for_generator("off_center_com")[0]
    problem = SP3WrenchScenario(params).build(seed=22)
    oracle = make_sp3_allocator("wrench_oracle").allocate(problem)
    oracle_score = score_assignment(problem, oracle)

    for method_id in [
        "oracle_scalar_assignment",
        "hungarian_slots",
        "capacity_greedy_slots",
        "cbba_slots",
        "replicator_wrench_deficit",
        "bnn_wrench_deficit",
        "smith_wrench_deficit",
        "smith_wrench_marginal",
        "support_dual_wrench_market",
        "greedy_cardinality",
        "greedy_capacity",
        "wrench_greedy",
        "cbba_wrench_score",
        "smith_qr_capacity",
        "smith_qr_wrench",
    ]:
        assignment = make_sp3_allocator(method_id).allocate(problem)
        assert score_assignment(problem, assignment) <= oracle_score + max(1e-6, 1e-4 * abs(oracle_score))


def test_sp3_metrics_include_false_positive_residual_and_gap() -> None:
    params = scenario_params_for_generator("slot_saturation")[0]
    problem = SP3WrenchScenario(params).build(seed=8)
    oracle_assignment, _oracle_runtime = timed_allocate(make_sp3_allocator("wrench_oracle"), problem)
    assignment, runtime_ms = timed_allocate(make_sp3_allocator("oracle_scalar_assignment"), problem)

    metrics = evaluate_assignment(problem, assignment, runtime_ms=runtime_ms, oracle_assignment=oracle_assignment, centralized=True)

    assert 0.0 <= metrics.scalar_feasible_rate <= 1.0
    assert 0.0 <= metrics.wrench_feasible_rate <= 1.0
    assert metrics.false_positive_rate > 0.0
    assert metrics.assigned_loads >= metrics.feasible_assigned_loads
    assert metrics.infeasible_assigned_loads > 0
    assert 0.0 <= metrics.feasible_coverage <= 1.0
    assert 0.0 <= metrics.precision_given_assigned <= 1.0
    assert 0.0 <= metrics.fp_given_assigned <= 1.0
    assert metrics.wrench_residual_norm >= 0.0
    assert metrics.wrench_residual_feasible_available >= 0.0
    assert metrics.torque_error_nm >= 0.0
    assert metrics.optimality_gap_vs_wrench_oracle >= 0.0


def test_sp3_precision_coverage_is_relative_to_wrench_oracle() -> None:
    params = scenario_params_for_generator("bar_torque_pure")[0]
    problem = SP3WrenchScenario(params).build(seed=9)
    oracle_assignment = make_sp3_allocator("wrench_oracle").allocate(problem)
    scalar_assignment = make_sp3_allocator("oracle_scalar_assignment").allocate(problem)

    oracle_metrics = evaluate_assignment(problem, oracle_assignment, runtime_ms=0.0, oracle_assignment=oracle_assignment)
    scalar_metrics = evaluate_assignment(problem, scalar_assignment, runtime_ms=0.0, oracle_assignment=oracle_assignment)

    assert oracle_metrics.feasible_available_loads >= 1
    assert oracle_metrics.feasible_coverage == pytest.approx(1.0)
    assert oracle_metrics.precision_given_assigned == pytest.approx(1.0)
    assert scalar_metrics.feasible_coverage <= 1.0
    assert scalar_metrics.fp_given_assigned >= 0.0


def test_sp3_pose_transport_euler_lagrange_reaches_target_pose() -> None:
    params = scenario_params_for_generator("pose_transport_rotate")[0]
    problem = SP3WrenchScenario(params).build(seed=5200)
    assignment = make_sp3_allocator("wrench_oracle").allocate(problem)

    result = simulate_pose_transport(problem, assignment)
    summary = pose_transport_summary(result)

    assert summary["slot_coverage_ratio"] == pytest.approx(1.0)
    assert summary["hamiltonian_drop"] > 0.0
    assert summary["max_torque_nm"] > 20.0
    assert summary["final_position_error_m"] < 0.75
    assert summary["final_orientation_error_deg"] < 2.0


def test_sp3_monte_carlo_writes_plots_videos_and_theory_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _assignment, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _assignment, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp3_runner, "save_wrench_snapshot", fake_snapshot)
    monkeypatch.setattr(sp3_runner, "save_wrench_video", fake_video)
    config = {
        "experiment_id": "SP3_TEST_smoke",
        "mode": "monte_carlo",
        "output_dir": str(tmp_path / "sp3"),
        "scenarios": [
            {"param_generator": "bar_torque_pure"},
            {"param_generator": "slot_saturation"},
        ],
        "methods": [
            {"id": "wrench_oracle"},
            {"id": "oracle_scalar_assignment"},
            {"id": "capacity_greedy_slots"},
            {"id": "smith_wrench_deficit"},
            {"id": "support_dual_wrench_market"},
        ],
        "seeds": {"start": 4100, "count": 2},
        "hypotheses": [
            {
                "id": "H_TEST_smith_gap",
                "metric": "wrench_residual_norm",
                "method_a": "smith_wrench_deficit",
                "method_b": "capacity_greedy_slots",
                "direction": "less",
            }
        ],
        "artifacts": {"save_video": True, "video": {"max_per_scenario": 2, "selection_metric": "wrench_feasible_rate", "duration_s": 2, "final_hold_s": 0.5}},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp3_config(config_path)

    assert manifest["runs"] == 20
    assert {item["scenario_generator"] for item in manifest["scenario_videos"]} == {"bar_torque_pure", "slot_saturation"}
    assert (tmp_path / "sp3" / "tables" / "runs.csv").exists()
    assert (tmp_path / "sp3" / "tables" / "load_status.csv").exists()
    assert (tmp_path / "sp3" / "tables" / "performance_ranking.csv").exists()
    assert (tmp_path / "sp3" / "tables" / "theory_checks.csv").exists()
    assert (tmp_path / "sp3" / "tables" / "hypothesis_results.csv").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_scalar_vs_wrench_success_by_method.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_false_positive_rate_by_scenario.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_residual_wrench_by_method.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_wrench_set_valid_vs_invalid.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_precision_coverage.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_complementarity_gain.png").exists()
    assert (tmp_path / "sp3" / "figures" / "sp3_quality_resource_pareto.png").exists()
    runs_text = (tmp_path / "sp3" / "tables" / "runs.csv").read_text(encoding="utf-8")
    assert "false_positive_rate" in runs_text
    assert "feasible_coverage" in runs_text
    assert "fp_given_assigned" in runs_text
    assert "wrench_residual_feasible_available" in runs_text
    assert "wrench_residual_norm" in runs_text
    assert "optimality_gap_vs_wrench_oracle" in runs_text
    assert "method_engine" in runs_text
    assert "support_dual_wrench_market" in runs_text
    audit = json.loads((tmp_path / "sp3" / "theory_audit.json").read_text(encoding="utf-8"))
    assert audit["failed_checks"] == 0
    assert audit["gates"]["G3_no_abstention_gaming"]["passed"] is True
    assert audit["method_design"]["support_dual_wrench_market"]["payoff_signal"] == "current_residual_wrench_direction"


def test_sp3_pose_transport_runner_writes_dynamic_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _result, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _result, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp3_runner, "save_pose_transport_snapshot", fake_snapshot)
    monkeypatch.setattr(sp3_runner, "save_pose_transport_video", fake_video)
    config = {
        "experiment_id": "SP3_TEST_pose_transport",
        "mode": "pose_transport",
        "output_dir": str(tmp_path / "pose"),
        "scenario": {"param_generator": "pose_transport_rotate"},
        "seed": 5200,
        "method": "wrench_oracle",
        "pose_transport": {"dynamics": {"steps": 80}},
        "artifacts": {"fps": 8},
    }
    config_path = tmp_path / "pose.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp3_config(config_path)
    summary = json.loads((tmp_path / "pose" / "summary.json").read_text(encoding="utf-8"))

    assert manifest["mode"] == "pose_transport"
    assert manifest["video_ok"] is True
    assert (tmp_path / "pose" / "tables" / "pose_trajectory.csv").exists()
    assert (tmp_path / "pose" / "report.md").exists()
    assert "hamiltonian_drop" in summary
    assert summary["slot_coverage_ratio"] == pytest.approx(1.0)


def test_sp3_pose_transport_suite_writes_multi_method_dynamic_artifacts(tmp_path, monkeypatch) -> None:
    def fake_snapshot(_problem, _result, path, _title):
        Path(path).write_text("snapshot", encoding="utf-8")

    def fake_video(_problem, _result, path, _title, **_kwargs):
        Path(path).write_text("video", encoding="utf-8")
        return True

    monkeypatch.setattr(sp3_runner, "save_pose_transport_snapshot", fake_snapshot)
    monkeypatch.setattr(sp3_runner, "save_pose_transport_video", fake_video)
    config = {
        "experiment_id": "SP3_TEST_pose_suite",
        "mode": "pose_transport_suite",
        "output_dir": str(tmp_path / "pose_suite"),
        "methods": [{"id": "wrench_oracle"}, {"id": "capacity_greedy_slots"}, {"id": "smith_wrench_deficit"}],
        "pose_transport": {"complete_uncovered_slots": False, "dynamics": {"steps": 50}},
        "cases": [
            {
                "id": "over",
                "param_generator": "pose_push_overactuated",
                "seed": 5300,
                "movement_type": "push",
                "robot_load_regime": "more_robots_than_loads",
                "pose_transport": {"target_pose": {"x": 1.2, "y": 0.4, "theta_deg": 20.0}},
            },
            {
                "id": "scarce",
                "param_generator": "pose_cargo_scarce",
                "seed": 5302,
                "movement_type": "cargo_push_drag",
                "robot_load_regime": "fewer_robots_than_loads",
                "pose_transport": {"target_pose": {"x": 0.9, "y": -0.6, "theta_deg": 35.0}},
            },
        ],
        "artifacts": {"save_video": True, "fps": 8, "duration_s": 2, "final_hold_s": 0.5},
    }
    config_path = tmp_path / "pose_suite.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    manifest = run_sp3_config(config_path)
    summary = json.loads((tmp_path / "pose_suite" / "summary.json").read_text(encoding="utf-8"))

    assert manifest["mode"] == "pose_transport_suite"
    assert manifest["runs"] == 6
    assert manifest["video_count"] == 6
    assert summary["theory_audit"]["failed_checks"] == 0
    assert (tmp_path / "pose_suite" / "tables" / "pose_runs.csv").exists()
    assert (tmp_path / "pose_suite" / "tables" / "pose_theory_checks.csv").exists()
    assert (tmp_path / "pose_suite" / "figures" / "sp3_pose_transport_suite_performance.png").exists()
    runs_text = (tmp_path / "pose_suite" / "tables" / "pose_runs.csv").read_text(encoding="utf-8")
    assert "more_robots_than_loads" in runs_text
    assert "fewer_robots_than_loads" in runs_text
    assert "cargo_push_drag" in runs_text
