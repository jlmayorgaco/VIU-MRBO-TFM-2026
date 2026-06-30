"""Benchmark v2 correctness tests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import minimize

from viu_mrob_tfm.simulations import (
    POLICY_AUCTION_CBBA,
    POLICY_GREEDY_NEAREST,
    POLICY_SMITH_FULL,
    POLICY_SMITH_QR_FULL,
    WarehouseConfig,
    compute_recovery_metrics,
    run_warehouse_simulation,
    solve_water_filling_staffing,
)
from viu_mrob_tfm.simulations.warehouse import _density_quorum_subset

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_warehouse_methods import (  # noqa: E402
    POLICY_ORACLE_CLAIRVOYANT,
    SCENARIOS,
    ScenarioRun,
    _config_from_run,
    _promote_oracle_row_to_bound,
    scenario_runs,
    smith_params_for_method,
    validate_metric_consistency,
    validate_oracle_bounds,
)


def test_oracle_reward_is_upper_bound_for_quick_methods() -> None:
    methods = [POLICY_SMITH_FULL, POLICY_GREEDY_NEAREST, POLICY_AUCTION_CBBA]
    for seed in [2026, 2027, 2028]:
        for method in methods:
            result = run_warehouse_simulation(
                WarehouseConfig(seed=seed, duration=25.0, max_loads=2, assignment_policy=method)
            )
            assert result.summary["oracle_reward"] + 1e-9 >= result.summary["delivered_reward"]


def test_oracle_bound_validator_catches_bad_summary_cell() -> None:
    rows = [
        {
            "scenario": "s",
            "scenario_case": "c",
            "seed": 1,
            "method": POLICY_ORACLE_CLAIRVOYANT,
            "delivered_reward": 1.0,
        },
        {"scenario": "s", "scenario_case": "c", "seed": 1, "method": "smith_full", "delivered_reward": 2.0},
    ]

    with pytest.raises(RuntimeError, match="Oracle upper-bound"):
        validate_oracle_bounds(rows)


def test_oracle_row_is_promoted_to_upper_bound() -> None:
    row = {
        "oracle_reward": 3.5,
        "delivered_reward": 1.0,
        "loads_offered": 4,
        "loads_spawned": 4,
        "reward_capture_ratio": 0.0,
    }
    _promote_oracle_row_to_bound(row)

    assert row["delivered_reward"] == pytest.approx(3.5)
    assert row["reward_capture_ratio"] == pytest.approx(1.0)


def test_zero_oracle_reward_is_reported_as_censored_nan() -> None:
    row = {
        "oracle_reward": 0.0,
        "delivered_reward": 0.0,
        "loads_offered": 0,
        "loads_spawned": 0,
        "reward_capture_ratio": 0.0,
    }
    _promote_oracle_row_to_bound(row)

    assert np.isnan(row["reward_capture_ratio"])


def test_metric_consistency_rejects_throughput_without_completion_time() -> None:
    rows = [
        {
            "scenario": "s",
            "scenario_case": "c",
            "method": "m",
            "seed": 1,
            "throughput_steady": 1.0,
            "mean_completion_time": np.nan,
        }
    ]

    with pytest.raises(RuntimeError, match="throughput > 0"):
        validate_metric_consistency(rows)


def test_water_filling_matches_numerical_optimization() -> None:
    values = np.array([1.8, 1.1, 0.7], dtype=float)
    demands = np.array([4.0, 2.0, 1.5], dtype=float)
    capacity = 5.5
    beta = 1.35
    closed, _lambda_star = solve_water_filling_staffing(values, demands, capacity, beta)

    def objective(z: np.ndarray) -> float:
        utility = values * (z - np.logaddexp(0.0, beta * (z - demands)) / beta)
        return -float(np.sum(utility))

    constraints = {"type": "eq", "fun": lambda z: np.sum(z) - capacity}
    bounds = [(0.0, capacity)] * len(values)
    result = minimize(
        objective,
        x0=np.full(3, capacity / 3.0),
        bounds=bounds,
        constraints=constraints,
        method="SLSQP",
        options={"ftol": 1e-13, "maxiter": 500},
    )

    assert result.success
    np.testing.assert_allclose(closed, result.x, atol=1e-6)


def test_density_knapsack_prefers_density_over_raw_value() -> None:
    items = [
        (0, 8, 12.0),  # raw value is largest, density 1.5
        (1, 3, 6.0),  # density 2.0
        (2, 3, 5.7),  # density 1.9
    ]

    assert _density_quorum_subset(items, capacity=6) == {1, 2}


def test_comm_degradation_reduces_local_performance_and_degree() -> None:
    for method in [POLICY_SMITH_FULL, POLICY_AUCTION_CBBA]:
        base_rewards = []
        degraded_rewards = []
        base_degrees = []
        degraded_degrees = []
        for seed in [2026, 2027, 2028]:
            base = run_warehouse_simulation(
                WarehouseConfig(
                    seed=seed,
                    duration=90.0,
                    max_loads=6,
                    spawn_process="poisson",
                    spawn_period=8.0,
                    assignment_policy=method,
                    r_com=12.0,
                    packet_loss=0.0,
                )
            )
            degraded = run_warehouse_simulation(
                WarehouseConfig(
                    seed=seed,
                    duration=90.0,
                    max_loads=6,
                    spawn_process="poisson",
                    spawn_period=8.0,
                    assignment_policy=method,
                    r_com=1.5,
                    packet_loss=0.9,
                )
            )
            base_rewards.append(base.summary["reward_capture_ratio"])
            degraded_rewards.append(degraded.summary["reward_capture_ratio"])
            base_degrees.append(base.summary["mean_communication_degree"])
            degraded_degrees.append(degraded.summary["mean_communication_degree"])

        assert sum(d < b for d, b in zip(degraded_rewards, base_rewards)) >= 2
        assert np.mean(degraded_degrees) < 0.5 * np.mean(base_degrees)


def test_relay_discovery_restores_medium_radius_local_performance() -> None:
    for method in [POLICY_SMITH_FULL, POLICY_GREEDY_NEAREST]:
        r6_rewards = []
        p50_rewards = []
        discovery_never = []
        for seed in [2026, 2027, 2028]:
            r6 = run_warehouse_simulation(
                WarehouseConfig(
                    seed=seed,
                    duration=140.0,
                    max_loads=5,
                    spawn_process="poisson",
                    spawn_period=10.0,
                    assignment_policy=method,
                    r_com=6.0,
                    packet_loss=0.0,
                )
            )
            p50 = run_warehouse_simulation(
                WarehouseConfig(
                    seed=seed,
                    duration=140.0,
                    max_loads=5,
                    spawn_process="poisson",
                    spawn_period=10.0,
                    assignment_policy=method,
                    r_com=12.0,
                    packet_loss=0.5,
                )
            )
            r6_rewards.append(r6.summary["reward_capture_ratio"])
            p50_rewards.append(p50.summary["reward_capture_ratio"])
            discovery_never.append(r6.summary["frac_loads_never_discovered"])

        assert np.nanmean(r6_rewards) > 0.0
        assert np.nanmean(p50_rewards) > 0.0
        assert np.nanmean(discovery_never) < 0.5


def test_robot_failure_events_are_fractional_in_quick_scenario() -> None:
    run = scenario_runs("robot_failures", quick=True)[0]

    assert run.overrides["duration"] >= 300.0
    assert run.overrides["failure_time"] == pytest.approx(0.4 * run.overrides["duration"])
    assert run.overrides["revive_time"] == pytest.approx(0.7 * run.overrides["duration"])


def test_smoke_mode_does_not_inherit_full_load_counts() -> None:
    for name in SCENARIOS:
        for run in scenario_runs(name, quick=False, smoke=True):
            assert run.overrides["duration"] == pytest.approx(30.0)
            assert run.overrides["max_loads"] <= 4


def test_simulation_is_deterministic_for_same_seed() -> None:
    config = WarehouseConfig(seed=2026, duration=35.0, max_loads=3, assignment_policy=POLICY_SMITH_FULL)
    first = run_warehouse_simulation(config).summary
    second = run_warehouse_simulation(config).summary
    first_hash = hashlib.sha256(json.dumps(first, sort_keys=True, allow_nan=True).encode()).hexdigest()
    second_hash = hashlib.sha256(json.dumps(second, sort_keys=True, allow_nan=True).encode()).hexdigest()

    assert first_hash == second_hash


def test_summary_reports_censored_loads() -> None:
    result = run_warehouse_simulation(WarehouseConfig(seed=2026, duration=5.0, max_loads=2))

    assert "censored_loads" in result.summary
    assert result.summary["censored_loads"] >= 0
    assert "discovery_latency_mean" in result.summary
    assert "frac_loads_never_discovered" in result.summary
    assert "mean_time_post_discovery" in result.summary
    assert "reward_capture_discovered" in result.summary
    assert "network_coverage_mean" in result.summary
    assert "comm_graph_lambda2_mean" in result.summary
    assert "recruit_latency_mean" in result.summary
    assert "recruit_switches" in result.summary
    assert "release_switches" in result.summary
    assert "lateral_switches" in result.summary


def test_effective_price_feedback_reduces_late_price_variation() -> None:
    base = dict(
        seed=1000,
        duration=120.0,
        dt=0.25,
        max_loads=10,
        max_active_loads=4,
        spawn_period=5.0,
        spawn_process="periodic",
        min_weight=5,
        max_weight=10,
        rho=2.2,
        assignment_policy=POLICY_SMITH_FULL,
        r_com=12.0,
        packet_loss=0.0,
        commit_dwell_time=2.0,
        price_gain=0.1,
        switch_margin=0.1,
        reserve_robot_slack=0,
        epsilon_switch=0.05,
        lateral_switch_rule="potential",
        clearing_mode="event",
        clearing_deficit_grace=2.0,
    )
    physical = run_warehouse_simulation(WarehouseConfig(**base, price_feedback_signal="physical_contact")).summary
    effective = run_warehouse_simulation(
        WarehouseConfig(**base, price_feedback_signal="effective_committed")
    ).summary

    assert effective["price_std_late"] <= 0.6 * physical["price_std_late"]


def test_potential_switching_saturates_in_static_scenario() -> None:
    result = run_warehouse_simulation(
        WarehouseConfig(
            seed=3030,
            duration=120.0,
            dt=0.25,
            max_loads=4,
            max_active_loads=4,
            spawn_period=0.0,
            spawn_process="periodic",
            min_weight=2,
            max_weight=5,
            assignment_policy=POLICY_SMITH_FULL,
            r_com=12.0,
            packet_loss=0.0,
            commit_dwell_time=2.0,
            price_gain=0.1,
            switch_margin=0.1,
            reserve_robot_slack=0,
            epsilon_switch=0.05,
        )
    )
    before = result.assignments[:-1]
    after = result.assignments[1:]
    lateral = (before > 0) & (after > 0) & (before != after)
    last_third = lateral[int(lateral.shape[0] * 2 / 3):]

    assert int(np.sum(lateral)) > 0
    assert int(np.sum(last_third)) == 0


def test_discovered_capture_and_post_discovery_time_are_consistent() -> None:
    result = run_warehouse_simulation(
        WarehouseConfig(
            seed=2026,
            duration=90.0,
            max_loads=3,
            max_weight=4,
            assignment_policy=POLICY_SMITH_FULL,
            r_com=12.0,
        )
    )

    assert result.summary["reward_capture_discovered"] + 1e-12 >= result.summary["reward_capture_ratio"]
    if result.summary["loads_delivered"] > 0:
        assert result.summary["mean_time_post_discovery"] <= result.summary["mean_completion_time"] + 1e-12


def test_comm_sweep_includes_r8_and_reports_mesh_metrics() -> None:
    cases = {run.case for run in scenario_runs("comm_degradation", quick=True)}

    assert "R8_p0" in cases
    connected = run_warehouse_simulation(
        WarehouseConfig(seed=2026, duration=10.0, max_loads=1, r_com=12.0, assignment_policy=POLICY_SMITH_FULL)
    ).summary
    disconnected = run_warehouse_simulation(
        WarehouseConfig(seed=2026, duration=10.0, max_loads=1, r_com=1.5, assignment_policy=POLICY_SMITH_FULL)
    ).summary
    assert connected["station_mesh_connected"] is True
    assert disconnected["station_mesh_connected"] is False
    assert connected["comm_graph_lambda2_mean"] >= disconnected["comm_graph_lambda2_mean"]


def test_smith_qr_rescues_degraded_r3_smoke() -> None:
    r3 = {run.case: run for run in scenario_runs("comm_degradation", quick=True)}["R3_p0"]
    base = dict(r3.overrides)
    base.update(
        duration=120.0,
        max_loads=12,
        seed=2026,
        clearing_mode="tick",
        commit_dwell_time=2.0,
        epsilon_switch=0.1,
        lateral_switch_rule="potential",
        price_feedback_signal="effective_committed",
        price_gain=0.1,
        reserve_robot_slack=0,
        smith_integer_clearing_enabled=True,
        smith_occupancy_mode="raw",
        smith_prices_enabled=True,
        switch_margin=0.1,
    )

    smith = run_warehouse_simulation(WarehouseConfig(**base, assignment_policy=POLICY_SMITH_FULL)).summary
    qr = run_warehouse_simulation(WarehouseConfig(**base, assignment_policy=POLICY_SMITH_QR_FULL)).summary

    assert qr["reward_capture_ratio"] > smith["reward_capture_ratio"]
    assert qr["loads_delivered"] >= smith["loads_delivered"]


def test_smith_ablations_inherit_full_configuration() -> None:
    tuned = {
        POLICY_SMITH_FULL: {
            "clearing_mode": "tick",
            "commit_dwell_time": 2.0,
            "epsilon_switch": 0.1,
            "lateral_switch_rule": "potential",
            "price_feedback_signal": "effective_committed",
            "price_gain": 0.1,
            "reserve_robot_slack": 0,
            "switch_margin": 0.1,
        }
    }
    full = smith_params_for_method(POLICY_SMITH_FULL, tuned)
    no_prices = smith_params_for_method("smith_no_prices", tuned)
    no_integer = smith_params_for_method("smith_no_integer", tuned)
    raw = smith_params_for_method("smith_raw_occupancy", tuned)

    assert {key for key in no_prices if no_prices.get(key) != full.get(key)} == {"price_gain"}
    assert no_prices["price_gain"] == 0.0
    assert no_integer == full
    assert raw == full


def test_smith_ablations_are_not_switch_degenerate_in_nominal() -> None:
    tuned = {
        POLICY_SMITH_FULL: {
            "clearing_mode": "tick",
            "commit_dwell_time": 2.0,
            "epsilon_switch": 0.1,
            "lateral_switch_rule": "potential",
            "price_feedback_signal": "effective_committed",
            "price_gain": 0.1,
            "reserve_robot_slack": 0,
            "switch_margin": 0.1,
        }
    }
    scenario_run = scenario_runs("nominal_flow", quick=True)[0]
    for method in ["smith_no_prices", "smith_no_integer", "smith_raw_occupancy"]:
        config = _config_from_run(2026, method, scenario_run, scenario_run.overrides, tuned)
        result = run_warehouse_simulation(config)

        assert result.summary["lateral_switches_per_delivery"] < 50.0


def test_recovery_time_synthetic_step() -> None:
    time = np.arange(0.0, 11.0)
    throughput = np.array([10, 10, 10, 10, 2, 3, 5, 8, 9, 10, 10], dtype=float)
    metrics = compute_recovery_metrics(time, throughput, fault_time=4.0)

    assert metrics["recovery_time_s"] == pytest.approx(4.0)
    assert metrics["peak_deficit_after_fault"] == pytest.approx(8.0)


def test_scarcity_priority_has_oracle_greedy_tradeoff_on_tuning_seeds() -> None:
    wins = 0
    for seed in [1000, 1001, 1002, 1003, 1004]:
        result = run_warehouse_simulation(
            WarehouseConfig(
                seed=seed,
                duration=70.0,
                max_loads=8,
                max_active_loads=6,
                scenario_name="scarcity_priority",
                min_weight=1,
                max_weight=10,
                spawn_period=4.0,
                assignment_policy=POLICY_GREEDY_NEAREST,
            )
        )
        if result.summary["oracle_reward"] > result.summary["delivered_reward"] + 1e-9:
            wins += 1
        assert any(load.reward == pytest.approx(3.0) for load in result.loads)

    assert wins >= 3
