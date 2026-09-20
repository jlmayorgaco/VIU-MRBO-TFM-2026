"""Tests for the bounded minimum coordination-order audit in SP1.N4."""

from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime
from viu_mrob_tfm.sp1_n3.worlds import World, make_world
from viu_mrob_tfm.sp1_n4.geo_qpg import (
    minimum_improving_coalition_order,
    run_geo_qpg,
)


def _manual_world(distances: np.ndarray) -> World:
    distances = np.asarray(distances, dtype=float)
    n, k = distances.shape
    return World(
        world_id="hstar-manual",
        seed=77,
        scenario="manual",
        capacity_cv=0.0,
        pressure=1.0,
        robot_positions=np.column_stack((np.arange(n, dtype=float), np.zeros(n))),
        load_positions=np.column_stack((np.arange(k, dtype=float), np.ones(k))),
        capacities=np.ones(n),
        demands=np.ones(k),
        distances=distances,
    )


def _complete(n: int) -> np.ndarray:
    adjacency = np.ones((n, n), dtype=bool)
    np.fill_diagonal(adjacency, False)
    return adjacency


def test_hstar_finds_exact_pair_swap_witness() -> None:
    world = _manual_world(np.array([[10.0, 0.0], [0.0, 10.0]]))
    result = minimum_improving_coalition_order(
        world,
        np.array([0, 1]),
        _complete(2),
        max_order=2,
    )
    assert result.order == 2
    assert result.category == "2"
    assert result.robot_ids == (0, 1)
    assert result.old_actions == (0, 1)
    assert result.new_actions == (1, 0)
    assert result.delta_deficit == 0.0
    assert result.delta_distance == -20.0


def test_hstar_finds_three_cycle_only_at_order_three() -> None:
    world = _manual_world(
        np.array(
            [
                [10.0, 0.0, 30.0],
                [30.0, 10.0, 0.0],
                [0.0, 30.0, 10.0],
            ]
        )
    )
    result = minimum_improving_coalition_order(
        world,
        np.array([0, 1, 2]),
        _complete(3),
        max_order=3,
    )
    assert result.order == 3
    assert result.robot_ids == (0, 1, 2)
    assert result.new_actions == (1, 2, 0)
    assert result.delta_deficit == 0.0
    assert result.delta_distance == -30.0


def test_hstar_respects_graph_connectivity() -> None:
    world = _manual_world(np.array([[10.0, 0.0], [0.0, 10.0]]))
    disconnected = np.zeros((2, 2), dtype=bool)
    connected = minimum_improving_coalition_order(
        world,
        np.array([0, 1]),
        disconnected,
        max_order=2,
        connected_only=False,
    )
    local = minimum_improving_coalition_order(
        world,
        np.array([0, 1]),
        disconnected,
        max_order=2,
        connected_only=True,
    )
    assert connected.order == 2
    assert local.order is None
    assert local.category == ">2"


def test_hstar_truncation_is_not_reported_as_an_optimum() -> None:
    world = _manual_world(np.array([[10.0, 0.0], [0.0, 10.0]]))
    result = minimum_improving_coalition_order(
        world,
        np.array([0, 1]),
        _complete(2),
        max_order=1,
    )
    assert result.order is None
    assert result.category == ">1"
    assert result.searched_through == 1


def test_br_terminal_is_audited_as_unilateral_local_minimum() -> None:
    world = make_world(
        world_id="hstar-generated",
        robot_count=8,
        load_count=3,
        q_bar=5.0,
        cv=0.65,
        pressure=0.8,
        scenario="clustered",
        workspace=(100.0, 100.0),
        seed=901,
        alpha=3.0,
    )
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    terminal = run_geo_qpg(world, adjacency, "geo_qpg_u")
    result = minimum_improving_coalition_order(
        world,
        terminal.assignment,
        adjacency,
        max_order=3,
    )
    assert terminal.unilateral_local_minimum
    assert result.order != 1
    assert result.category in {"2", "3", ">3"}
