from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pytest


matplotlib.use("Agg")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "sp1_a1_hungarian.py"
MODULE_NAME = "sp1_a1_hungarian_under_test"

SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
HUNGARIAN = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = HUNGARIAN
SPEC.loader.exec_module(HUNGARIAN)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_partial_assignment_is_diagnostic_not_feasible() -> None:
    robots, loads, quotas = HUNGARIAN.generate_world(
        robot_count=5,
        total_slots=10,
        q_bar=5.0,
        mean_quota=3.0,
        quota_mode="symmetric",
        spatial_mode="uniform",
        workspace_width=100.0,
        workspace_height=100.0,
        seed=1234,
    )

    result = HUNGARIAN.solve_hungarian(
        robots=robots,
        loads=loads,
        q_bar=5.0,
        allow_partial=True,
    )

    assert int(np.sum(quotas)) == 10
    assert result.feasible is False
    assert result.coverage == pytest.approx(0.5)
    assert result.missing_slots == 5
    assert len(result.assignments) == 5
    assert result.cost_matrix.nbytes == 8 * 5 * 10

    with pytest.raises(RuntimeError, match="asignación parcial"):
        HUNGARIAN.validate_result(
            result=result,
            robots=robots,
            loads=loads,
            q_bar=5.0,
        )


def test_world_generation_is_reproducible_and_preserves_quotas() -> None:
    parameters = {
        "robot_count": 30,
        "total_slots": 20,
        "q_bar": 5.0,
        "mean_quota": 3.0,
        "quota_mode": "high",
        "spatial_mode": "clustered",
        "workspace_width": 100.0,
        "workspace_height": 100.0,
        "seed": 20260728,
    }

    robots_a, loads_a, quotas_a = HUNGARIAN.generate_world(**parameters)
    robots_b, loads_b, quotas_b = HUNGARIAN.generate_world(**parameters)

    assert np.array_equal(quotas_a, quotas_b)
    assert int(np.sum(quotas_a)) == 20
    assert np.all(quotas_a > 0)
    assert robots_a == robots_b
    assert loads_a == loads_b
    assert [
        HUNGARIAN.required_robot_count(load, 5.0) for load in loads_a
    ] == quotas_a.tolist()


def test_dense_profiles_have_at_least_twelve_x_values_and_full_has_60_seeds() -> None:
    quick = HUNGARIAN.config_for_profile("quick")
    full = HUNGARIAN.config_for_profile("full")

    for config in (quick, full):
        assert len(config.scaling_m_values) >= HUNGARIAN.DENSE_SWEEP_MIN_POINTS
        assert len(config.scaling_deltas) >= HUNGARIAN.DENSE_SWEEP_MIN_POINTS
        assert tuple(sorted(set(config.scaling_m_values))) == config.scaling_m_values
        assert tuple(sorted(set(config.scaling_deltas))) == config.scaling_deltas
        assert config.scaling_deltas[0] < 0 < config.scaling_deltas[-1]
        assert 0.0 in config.scaling_deltas
        assert len(config.balance_deltas) == 39
        assert config.balance_deltas[0] == -0.95
        assert config.balance_deltas[-1] == 0.95
        assert all(
            right - left == pytest.approx(0.05)
            for left, right in zip(
                config.balance_deltas,
                config.balance_deltas[1:],
            )
        )

    assert full.seeds_per_cell == 60


def test_delta_endpoints_are_mathematical_limits_not_finite_instances() -> None:
    with pytest.raises(ValueError, match="estrictamente"):
        HUNGARIAN.robot_count_from_delta(20, -1.0)
    with pytest.raises(ValueError, match="estrictamente"):
        HUNGARIAN.robot_count_from_delta(20, 1.0)


def test_smoke_profile_writes_complete_reproducible_package(
    tmp_path: Path,
) -> None:
    config = HUNGARIAN.config_for_profile("smoke")
    HUNGARIAN.run_monte_carlo(config=config, output_dir=tmp_path)

    scaling = csv_rows(tmp_path / "mc_scaling.csv")
    balance = csv_rows(tmp_path / "mc_balance.csv")
    asymmetry = csv_rows(tmp_path / "mc_asymmetry.csv")
    failures = csv_rows(tmp_path / "mc_failures.csv")
    all_runs = csv_rows(tmp_path / "mc_all_runs.csv")
    exponents = csv_rows(tmp_path / "scaling_exponents.csv")

    assert len(scaling) == 20
    assert len(balance) == 10
    assert len(asymmetry) == 50
    assert len(failures) == 46
    assert len(all_runs) == 126
    assert len(exponents) == len(config.scaling_deltas)
    assert {int(row["size_points"]) for row in exponents} == {2}

    assert len({(row["study"], row["seed"]) for row in all_runs}) == 126
    assert all(
        int(row["matrix_bytes"]) == 8 * int(row["N"]) * int(row["M"])
        for row in all_runs
    )
    assert all(
        row["mission_feasible"] == "False"
        for row in scaling
        if float(row["requested_delta"]) < 0
    )
    assert all(
        int(row["logical_messages"])
        == 2 * int(row["N"]) + config.max_retries * int(row["failure_count"])
        for row in all_runs
    )
    assert all(
        float(row["greedy_to_hungarian_ratio"]) >= 1.0 - 1e-12
        for row in all_runs
    )
    assert all(
        0.0 <= float(row["assignment_cost_gini"]) <= 1.0
        for row in all_runs
    )
    assert {row["quota_mode"] for row in asymmetry} == {
        "symmetric",
        "low",
        "moderate",
        "high",
        "extreme",
    }
    assert {row["spatial_mode"] for row in asymmetry} == {
        "uniform",
        "clustered",
        "separated",
        "ring",
        "corridor",
    }

    expected_csv = {
        "mc_all_runs.csv",
        "mc_scaling.csv",
        "mc_balance.csv",
        "mc_asymmetry.csv",
        "mc_failures.csv",
        "summary_scaling.csv",
        "summary_balance.csv",
        "summary_asymmetry.csv",
        "summary_failures.csv",
        "scaling_exponents.csv",
    }
    assert expected_csv <= {path.name for path in tmp_path.glob("*.csv")}
    assert (tmp_path / "config.json").is_file()
    assert len(list((tmp_path / "plots").glob("*.png"))) == 18

    reloaded_failures = HUNGARIAN.read_csv_records(tmp_path / "mc_failures.csv")
    assert all(
        isinstance(row["mission_feasible"], bool)
        for row in reloaded_failures
    )
    HUNGARIAN.regenerate_plots_from_csv(tmp_path)
    assert len(list((tmp_path / "plots").glob("*.png"))) == 18
