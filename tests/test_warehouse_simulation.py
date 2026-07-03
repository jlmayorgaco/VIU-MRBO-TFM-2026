"""Smoke tests for the realistic warehouse AMR simulation."""

from __future__ import annotations

import numpy as np
import pytest

from viu_mrob_tfm.simulations import LOAD_DELIVERED, WarehouseConfig, WarehouseResult
from viu_mrob_tfm.simulations.warehouse import (
    WAREHOUSE_ASSIGNMENT_POLICIES,
    _communication_graph,
    run_warehouse_simulation,
)


@pytest.fixture(scope="module")
def warehouse_result() -> WarehouseResult:
    config = WarehouseConfig(seed=2026, duration=90.0, max_loads=3, max_active_loads=3, max_weight=4)
    return run_warehouse_simulation(config)


def test_warehouse_recruits_and_delivers_dynamic_loads(warehouse_result: WarehouseResult) -> None:
    result = warehouse_result

    assert result.summary["robots"] == 15
    assert result.summary["loads_spawned"] == 3
    assert result.summary["loads_delivered"] == 3
    assert result.summary["delivery_rate"] == pytest.approx(1.0)
    assert all(1 <= load.weight <= 10 for load in result.loads)
    assert np.all(result.load_status[-1] == LOAD_DELIVERED)


def test_load_weight_is_physical_quorum(warehouse_result: WarehouseResult) -> None:
    result = warehouse_result
    max_contacts = np.max(result.contact_counts, axis=0)

    for idx, load in enumerate(result.loads):
        assert max_contacts[idx] >= load.weight
        assert max_contacts[idx] <= load.weight + result.config.reserve_robot_slack
        assert np.isfinite(load.coalition_time)
        assert np.isfinite(load.delivered_time)


def test_robot_limits_and_safety_layers_are_respected(warehouse_result: WarehouseResult) -> None:
    result = warehouse_result
    cfg = result.config

    assert float(np.max(np.abs(result.wheel_speeds))) <= cfg.max_wheel_angular_speed + 1e-9
    assert float(np.max(np.abs(result.linear_speeds))) <= min(cfg.max_speed, cfg.wheel_speed_limit) + 1e-9
    assert float(np.max(np.abs(result.angular_speeds))) <= cfg.max_angular_speed + 1e-9
    assert result.summary["min_robot_obstacle_clearance"] >= 0.075
    assert result.summary["min_load_obstacle_clearance"] > 0.45
    assert result.summary["min_pair_distance"] > 0.25


def test_communication_graph_is_range_limited(warehouse_result: WarehouseResult) -> None:
    result = warehouse_result

    assert float(np.max(result.communication_degrees)) <= result.config.robot_count - 1
    positions = np.array([[0.0, 0.0], [0.5, 0.0], [2.0, 0.0]])
    adjacency = _communication_graph(positions, r_com=0.75)
    np.testing.assert_array_equal(
        adjacency,
        np.array(
            [
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
            ]
        ),
    )


def test_all_warehouse_assignment_policies_run() -> None:
    for policy in WAREHOUSE_ASSIGNMENT_POLICIES:
        config = WarehouseConfig(
            seed=2026,
            duration=20.0,
            max_loads=1,
            max_active_loads=1,
            assignment_policy=policy,
        )
        result = run_warehouse_simulation(config)

        assert result.summary["assignment_policy"] == policy
        assert result.summary["loads_spawned"] == 1
        assert result.robot_positions.shape[1] == config.robot_count
