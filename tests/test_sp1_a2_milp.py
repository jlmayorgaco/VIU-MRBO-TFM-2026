from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import matplotlib
import numpy as np
import pytest


matplotlib.use("Agg")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "sp1_a2_milp.py"
MODULE_NAME = "sp1_a2_milp_under_test"

SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MILP = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = MILP
SPEC.loader.exec_module(MILP)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_solver_covers_loads_and_assigns_each_robot_at_most_once() -> None:
    robots = [
        MILP.Robot(id="R1", x=0.0, y=0.0, capacity=3.0),
        MILP.Robot(id="R2", x=1.0, y=0.0, capacity=5.0),
        MILP.Robot(id="R3", x=9.0, y=0.0, capacity=4.0),
        MILP.Robot(id="R4", x=10.0, y=0.0, capacity=6.0),
    ]
    loads = [
        MILP.Load(id="L1", x=0.0, y=1.0, mass=7.0),
        MILP.Load(id="L2", x=10.0, y=1.0, mass=8.0),
    ]
    result = MILP.solve_heterogeneous_milp(robots, loads)
    MILP.validate_result(result, robots, loads)

    assigned = [assignment.robot_id for assignment in result.assignments]
    assert result.feasible
    assert result.optimal
    assert len(assigned) == len(set(assigned))
    assert all(
        result.recruited_capacity[load.id] >= load.mass
        for load in loads
    )


def test_total_capacity_deficit_is_rejected() -> None:
    robots = [
        MILP.Robot(id="R1", x=0.0, y=0.0, capacity=2.0),
        MILP.Robot(id="R2", x=1.0, y=0.0, capacity=2.0),
    ]
    loads = [MILP.Load(id="L1", x=0.5, y=1.0, mass=5.0)]
    with pytest.raises(MILP.InfeasibleCoalitionError, match="insuficiente"):
        MILP.solve_heterogeneous_milp(robots, loads)


def test_homogeneous_reduction_matches_hungarian_distance() -> None:
    config = MILP.config_for_profile("smoke")
    for seed in (20260728, 12345, 98765):
        robots, loads, quotas = MILP.generate_paired_world(
            robot_count=15,
            total_slots=10,
            q_bar=config.q_bar,
            mean_quota=config.mean_quota,
            quota_mode="moderate",
            spatial_mode="clustered",
            capacity_mode="homogeneous",
            workspace_width=config.workspace_width,
            workspace_height=config.workspace_height,
            seed=seed,
        )
        result = MILP.solve_heterogeneous_milp(
            robots,
            loads,
            distance_weight=config.distance_weight,
            excess_weight=config.excess_weight,
            robot_use_weight=config.robot_use_weight,
        )
        homogeneous_robots, homogeneous_loads = MILP._hungarian_entities(
            robots,
            loads,
            config.q_bar,
        )
        hungarian = MILP.HUNGARIAN.solve_hungarian(
            homogeneous_robots,
            homogeneous_loads,
            config.q_bar,
        )

        assert int(np.sum(quotas)) == 10
        assert result.total_distance == pytest.approx(
            hungarian.total_cost,
            abs=1e-8,
        )
        assert len(result.assignments) == len(hungarian.assignments) == 10


def test_capacity_vectors_are_reproducible_heterogeneous_and_balanced() -> None:
    for mode in ("low", "moderate", "high", "extreme"):
        first = MILP.generate_capacity_vector(
            robot_count=30,
            q_bar=5.0,
            mode=mode,
            rng=np.random.default_rng(1234),
        )
        second = MILP.generate_capacity_vector(
            robot_count=30,
            q_bar=5.0,
            mode=mode,
            rng=np.random.default_rng(1234),
        )
        assert np.array_equal(first, second)
        assert float(np.sum(first)) == pytest.approx(150.0, abs=1e-10)
        assert float(np.mean(first)) == pytest.approx(5.0, abs=1e-12)
        assert np.std(first) > 0.0
        assert np.all(first > 0.0)


def test_paired_world_preserves_hungarian_positions_loads_and_quotas() -> None:
    parameters = {
        "robot_count": 30,
        "total_slots": 20,
        "q_bar": 5.0,
        "mean_quota": 3.0,
        "quota_mode": "high",
        "spatial_mode": "ring",
        "workspace_width": 100.0,
        "workspace_height": 100.0,
        "seed": 20260728,
    }
    robots, loads, quotas = MILP.generate_paired_world(
        **parameters,
        capacity_mode="moderate",
    )
    h_robots, h_loads, h_quotas = MILP.HUNGARIAN.generate_world(**parameters)

    assert [(robot.id, robot.x, robot.y) for robot in robots] == [
        (robot.id, robot.x, robot.y) for robot in h_robots
    ]
    assert [(load.id, load.x, load.y, load.mass) for load in loads] == [
        (load.id, load.x, load.y, load.mass) for load in h_loads
    ]
    assert np.array_equal(quotas, h_quotas)
    assert all(
        not np.isclose(robot.capacity, 5.0)
        for robot in robots
    )


def test_sparse_model_diagnostics_match_structure() -> None:
    robots, loads, _ = MILP.generate_paired_world(
        robot_count=15,
        total_slots=10,
        q_bar=5.0,
        mean_quota=3.0,
        quota_mode="symmetric",
        spatial_mode="uniform",
        capacity_mode="moderate",
        workspace_width=100.0,
        workspace_height=100.0,
        seed=77,
    )
    result = MILP.solve_heterogeneous_milp(robots, loads)
    n = len(robots)
    k = len(loads)
    assert result.diagnostics["constraint_count"] == n + 2 * k
    assert result.diagnostics["constraint_nonzero_count"] == 3 * n * k + k
    dense_bytes = (n + 2 * k) * (n * k + k) * 8
    assert result.diagnostics["constraint_matrix_bytes"] < dense_bytes


def test_profiles_mirror_hungarian_monte_carlo_grids() -> None:
    fields = (
        "seeds_per_cell",
        "scaling_m_values",
        "scaling_deltas",
        "balance_m_values",
        "balance_deltas",
        "asymmetry_m_values",
        "asymmetry_delta",
        "quota_modes",
        "spatial_modes",
        "failure_m_values",
        "failure_deltas",
        "failure_treatments",
    )
    for profile in ("smoke", "quick", "full"):
        milp = MILP.config_for_profile(profile)
        hungarian = MILP.HUNGARIAN.config_for_profile(profile)
        assert all(
            getattr(milp, field) == getattr(hungarian, field)
            for field in fields
        )


def test_saturation_audit_grid_extends_n_and_has_unique_resume_keys() -> None:
    config = MILP.SaturationAuditConfig()
    cases = MILP.saturation_audit_cases(config)
    keys = [MILP.saturation_case_key(case) for case in cases]

    assert len(cases) == 105
    assert len(keys) == len(set(keys))
    assert max(
        case["N"] for case in cases if case["arm"] == "fixed_demand"
    ) == 4800
    assert max(
        case["N"] for case in cases if case["arm"] == "joint_growth"
    ) == 1800
    assert {
        case["time_limit_seconds"]
        for case in cases
        if case["arm"] == "timeout_probe"
    } == {2.0, 5.0, 20.0}


def test_saturation_outcome_distinguishes_timeout_from_optimality() -> None:
    optimal = SimpleNamespace(optimal=True, status=0, feasible=True)
    outcome, censored = MILP.classify_saturation_outcome(
        result=optimal,
        error_message="",
        call_wall_seconds=5.1,
        time_limit_seconds=5.0,
    )
    assert outcome == "optimal_certified"
    assert censored is False

    incumbent = SimpleNamespace(optimal=False, status=1, feasible=True)
    outcome, censored = MILP.classify_saturation_outcome(
        result=incumbent,
        error_message="",
        call_wall_seconds=5.1,
        time_limit_seconds=5.0,
    )
    assert outcome == "timeout_with_incumbent"
    assert censored is True

    outcome, censored = MILP.classify_saturation_outcome(
        result=None,
        error_message="status=1; Time limit reached",
        call_wall_seconds=5.1,
        time_limit_seconds=5.0,
    )
    assert outcome == "timeout_without_incumbent"
    assert censored is True


def test_saturation_summary_has_uniform_csv_schema(tmp_path: Path) -> None:
    records = []
    for arm, robot_count, time_limit in (
        ("fixed_demand", 120, 5.0),
        ("joint_growth", 60, 5.0),
        ("timeout_probe", 400, 5.0),
    ):
        records.append(
            {
                "arm": arm,
                "N": robot_count,
                "M": 120,
                "K": 40,
                "time_limit_seconds": time_limit,
                "observed_time_seconds": 5.0,
                "optimal_certified": False,
                "censored": True,
                "solver_returned_incumbent": True,
                "binary_variable_count": robot_count * 40,
                "explicit_model_bytes": robot_count * 160,
            }
        )

    summary = MILP.build_saturation_summary_records(
        records=records,
        config=MILP.SaturationAuditConfig(),
    )
    assert len(summary) == 3
    assert len({tuple(record.keys()) for record in summary}) == 1
    assert all("time_limit_seconds" in record for record in summary)

    path = tmp_path / "saturation_summary.csv"
    MILP.write_csv(path, summary)
    assert len(csv_rows(path)) == 3


def test_milp_only_record_removes_hungarian_and_comparison_fields() -> None:
    source = {
        "study": "scaling",
        "milp_feasible": True,
        "milp_total_distance": 10.0,
        "hungarian_feasible": True,
        "hungarian_total_distance": 10.0,
        "both_feasible": True,
        "same_capacity_model": False,
        "milp_to_hungarian_distance_ratio": 1.0,
    }
    filtered = MILP.milp_only_record(source)
    assert filtered == {
        "study": "scaling",
        "milp_feasible": True,
        "milp_total_distance": 10.0,
    }


def test_smoke_campaign_writes_two_scientific_packages(
    tmp_path: Path,
) -> None:
    config = MILP.config_for_profile("smoke")
    package = MILP.run_separated_monte_carlo(
        config=config,
        output_dir=tmp_path,
        profile="smoke",
        comparison_profile="smoke",
    )

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "comparison",
        "milp_results",
    ]
    milp_dir = tmp_path / "milp_results"
    comparison_dir = tmp_path / "comparison"
    scaling = csv_rows(milp_dir / "mc_scaling.csv")
    balance = csv_rows(milp_dir / "mc_balance.csv")
    asymmetry = csv_rows(milp_dir / "mc_asymmetry.csv")
    failures = csv_rows(milp_dir / "mc_failures.csv")
    capacity = csv_rows(milp_dir / "mc_capacity.csv")
    all_runs = csv_rows(milp_dir / "mc_all_runs.csv")

    assert len(scaling) == 20
    assert len(balance) == 10
    assert len(asymmetry) == 50
    assert 36 <= len(failures) <= 48
    assert len(capacity) == 10
    assert len(all_runs) == sum(
        map(len, (scaling, balance, asymmetry, failures, capacity))
    )
    assert package["milp_results"]["row_counts"]["all"] == len(all_runs)
    assert (
        package["milp_results"]["audit"]["contains_hungarian_columns"]
        is False
    )
    assert all(
        not any(key.startswith("hungarian_") for key in row)
        for row in all_runs
    )
    assert all(
        float(row["capacity_mean_kg"]) == pytest.approx(5.0, abs=1e-10)
        for row in all_runs
        if row["failure_count"] == "0"
    )
    milp_pngs = sorted((milp_dir / "figures").glob("*.png"))
    assert len(milp_pngs) == 9
    assert all(path.with_suffix(".pdf").is_file() for path in milp_pngs)
    assert (milp_dir / "MILP_RESULTS_REPORT.md").is_file()
    assert (milp_dir / "FIGURE_GUIDE.md").is_file()
    assert (milp_dir / "milp_results_manifest.json").is_file()

    comparison = csv_rows(comparison_dir / "mc_all_runs.csv")
    assert 116 <= len(comparison) <= 128
    assert package["comparison"]["row_counts"]["all"] == len(comparison)
    assert all(row["capacity_mode"] == "homogeneous" for row in comparison)
    assert all(row["same_capacity_model"] == "True" for row in comparison)
    jointly_feasible = [
        row for row in comparison if row["both_feasible"] == "True"
    ]
    assert jointly_feasible
    assert all(
        float(row["milp_total_distance"])
        == pytest.approx(float(row["hungarian_total_distance"]), abs=1e-8)
        for row in jointly_feasible
    )
    comparison_pngs = sorted((comparison_dir / "figures").glob("*.png"))
    assert len(comparison_pngs) == 4
    assert all(path.with_suffix(".pdf").is_file() for path in comparison_pngs)
    assert (comparison_dir / "CONTROLLED_COMPARISON_REPORT.md").is_file()
    assert (comparison_dir / "FIGURE_GUIDE.md").is_file()
    assert (comparison_dir / "comparison_manifest.json").is_file()

    for directory, manifest_name in (
        (milp_dir, "milp_results_manifest.json"),
        (comparison_dir, "comparison_manifest.json"),
    ):
        stored = json.loads(
            (directory / manifest_name).read_text(encoding="utf-8")
        )
        for relative_path, metadata in stored["artifacts"].items():
            path = directory / relative_path
            assert path.is_file()
            assert path.stat().st_size == metadata["bytes"]
            assert MILP.sha256_file(path) == metadata["sha256"]
