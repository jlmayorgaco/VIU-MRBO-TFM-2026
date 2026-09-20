"""Invariant and mechanism tests for the atomic SP1.N4 Geo-QPG family."""

from __future__ import annotations

import inspect
from itertools import combinations, product

import numpy as np
import pytest

from viu_mrob_tfm.sp1_n3.certificate import coverage
from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime, complete_adjacency
from viu_mrob_tfm.sp1_n3.worlds import make_world
from viu_mrob_tfm.sp1_n3.worlds import World
from viu_mrob_tfm.sp1_n4.geo_qpg import (
    METHODS,
    MessageLedger,
    MoveProposal,
    PHASE_GEOMETRY,
    PHASE_QUOTA,
    QuotaRegister,
    TransactionCoordinator,
    assignment_distance,
    build_proposal,
    deficit_from_coverage,
    distributed_mis_indices,
    marginal_changes,
    proposals_conflict,
    run_geo_qpg,
)


def _world(seed: int = 1234, *, n: int = 8, k: int = 3):
    return make_world(
        world_id=f"n4-test-{seed}",
        robot_count=n,
        load_count=k,
        q_bar=5.0,
        cv=0.55,
        pressure=0.80,
        scenario="uniform",
        workspace=(100.0, 100.0),
        seed=seed,
        alpha=3.0,
    )


def _global_dj(assignment, capacities, demands, distances):
    q = coverage(assignment, capacities, len(demands))
    return deficit_from_coverage(q, demands), assignment_distance(assignment, distances)


def test_marginal_change_equals_global_recomputation() -> None:
    rng = np.random.default_rng(81)
    capacities = np.array([1.0, 2.0, 3.0, 1.5])
    demands = np.array([2.5, 2.0, 1.5])
    distances = rng.uniform(1.0, 20.0, size=(4, 3))
    for assignment_tuple in product(range(-1, 3), repeat=4):
        assignment = np.array(assignment_tuple, dtype=int)
        q = coverage(assignment, capacities, 3)
        before_d, before_j = _global_dj(assignment, capacities, demands, distances)
        for robot in range(4):
            for target in range(-1, 3):
                old = int(assignment[robot])
                changed = assignment.copy()
                changed[robot] = target
                after_d, after_j = _global_dj(changed, capacities, demands, distances)
                delta_d, delta_j = marginal_changes(
                    q,
                    demands,
                    (robot,),
                    (old,),
                    (target,),
                    capacities,
                    distances,
                )
                assert delta_d == pytest.approx(after_d - before_d, abs=1e-12)
                assert delta_j == pytest.approx(after_j - before_j, abs=1e-12)


@pytest.mark.parametrize("order", (2, 3))
def test_group_marginal_change_equals_global_recomputation(order: int) -> None:
    """Pairs and triples need only affected aggregates, not the full profile."""

    rng = np.random.default_rng(1400 + order)
    n, k = 7, 4
    capacities = rng.uniform(0.5, 3.0, size=n)
    demands = rng.uniform(1.0, 5.0, size=k)
    distances = rng.uniform(0.0, 30.0, size=(n, k))
    for _ in range(250):
        assignment = rng.integers(-1, k, size=n)
        robot_ids = tuple(sorted(rng.choice(n, size=order, replace=False).tolist()))
        old_actions = tuple(int(assignment[robot]) for robot in robot_ids)
        new_actions = tuple(int(value) for value in rng.integers(-1, k, size=order))
        q = coverage(assignment, capacities, k)
        before_d, before_j = _global_dj(assignment, capacities, demands, distances)
        changed = assignment.copy()
        changed[list(robot_ids)] = new_actions
        after_d, after_j = _global_dj(changed, capacities, demands, distances)
        delta_d, delta_j = marginal_changes(
            q,
            demands,
            robot_ids,
            old_actions,
            new_actions,
            capacities,
            distances,
        )
        assert delta_d == pytest.approx(after_d - before_d, abs=1e-12)
        assert delta_j == pytest.approx(after_j - before_j, abs=1e-12)


def _strict_geometry_improvements(
    assignment: np.ndarray,
    capacities: np.ndarray,
    demands: np.ndarray,
    distances: np.ndarray,
    order: int,
) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """Enumerate strict feasible improvements changing exactly ``order`` robots."""

    q = coverage(assignment, capacities, len(demands))
    improvements: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for robot_ids in combinations(range(len(assignment)), order):
        old_actions = tuple(int(assignment[robot]) for robot in robot_ids)
        for new_actions in product(range(-1, len(demands)), repeat=order):
            if any(old == new for old, new in zip(old_actions, new_actions, strict=True)):
                continue
            delta_d, delta_j = marginal_changes(
                q,
                demands,
                robot_ids,
                old_actions,
                new_actions,
                capacities,
                distances,
            )
            if abs(delta_d) <= 1e-12 and delta_j < -1e-12:
                improvements.append((robot_ids, tuple(int(value) for value in new_actions)))
    return improvements


def test_pair_swap_is_a_minimal_order_two_barrier() -> None:
    capacities = np.ones(2)
    demands = np.ones(2)
    assignment = np.array([0, 1], dtype=int)
    distances = np.array([[10.0, 0.0], [0.0, 10.0]])
    assert not _strict_geometry_improvements(
        assignment, capacities, demands, distances, order=1
    )
    assert _strict_geometry_improvements(
        assignment, capacities, demands, distances, order=2
    ) == [((0, 1), (1, 0))]


def test_three_cycle_is_a_minimal_order_three_barrier() -> None:
    capacities = np.ones(3)
    demands = np.ones(3)
    assignment = np.array([0, 1, 2], dtype=int)
    distances = np.array(
        [
            [10.0, 0.0, 30.0],
            [30.0, 10.0, 0.0],
            [0.0, 30.0, 10.0],
        ]
    )
    assert not _strict_geometry_improvements(
        assignment, capacities, demands, distances, order=1
    )
    assert not _strict_geometry_improvements(
        assignment, capacities, demands, distances, order=2
    )
    assert _strict_geometry_improvements(
        assignment, capacities, demands, distances, order=3
    ) == [((0, 1, 2), (1, 2, 0))]


def test_decision_proposal_has_no_profile_or_oracle_input() -> None:
    parameters = set(inspect.signature(build_proposal).parameters)
    forbidden = {"assignment", "global_profile", "oracle", "adjacency", "diameter", "lambda_2"}
    assert not parameters.intersection(forbidden)
    assert {"q", "versions", "robot_ids", "old_actions", "new_actions"} <= parameters


def test_stale_version_rejects_without_mutation() -> None:
    capacities = np.array([1.0, 1.0])
    demands = np.array([1.0, 1.0])
    distances = np.array([[1.0, 3.0], [2.0, 1.0]])
    register = QuotaRegister(demands, capacities, distances)
    first = build_proposal(
        q=register.q.copy(),
        versions=register.versions.copy(),
        demands=demands,
        robot_ids=(0,),
        old_actions=(-1,),
        new_actions=(0,),
        capacities=capacities,
        distances=distances,
        phase=PHASE_QUOTA,
        priority=(0,),
    )
    stale = build_proposal(
        q=register.q.copy(),
        versions=register.versions.copy(),
        demands=demands,
        robot_ids=(1,),
        old_actions=(-1,),
        new_actions=(0,),
        capacities=capacities,
        distances=distances,
        phase=PHASE_QUOTA,
        priority=(1,),
    )
    assert first is not None and stale is not None
    assert register.commit(first) == (True, "COMMITTED")
    assignment_after_first = register.assignment.copy()
    q_after_first = register.q.copy()
    assert register.commit(stale) == (False, "STALE_VERSION")
    np.testing.assert_array_equal(register.assignment, assignment_after_first)
    np.testing.assert_allclose(register.q, q_after_first)


def test_quota_and_geometry_guards_are_monotone() -> None:
    capacities = np.array([1.0, 1.0, 1.0])
    demands = np.array([1.0, 1.0])
    distances = np.array([[1.0, 9.0], [9.0, 1.0], [5.0, 5.0]])
    register = QuotaRegister(demands, capacities, distances)
    for robot, target in ((0, 0), (1, 1)):
        proposal = build_proposal(
            q=register.q,
            versions=register.versions,
            demands=demands,
            robot_ids=(robot,),
            old_actions=(-1,),
            new_actions=(target,),
            capacities=capacities,
            distances=distances,
            phase=PHASE_QUOTA,
            priority=(robot,),
        )
        assert proposal is not None
        before = register.deficit
        assert register.commit(proposal)[0]
        assert register.deficit < before
    assert register.phase == PHASE_GEOMETRY

    # Moving the redundant idle robot cannot improve J, while breaking either
    # covered load is rejected by the G-phase guard at proposal construction.
    breaking = build_proposal(
        q=register.q,
        versions=register.versions,
        demands=demands,
        robot_ids=(0,),
        old_actions=(0,),
        new_actions=(-1,),
        capacities=capacities,
        distances=distances,
        phase=PHASE_GEOMETRY,
        priority=(0,),
    )
    assert breaking is None


def test_disjoint_proposal_deltas_add_exactly() -> None:
    capacities = np.ones(4)
    demands = np.ones(4)
    distances = np.arange(16, dtype=float).reshape(4, 4) + 1.0
    assignment = np.full(4, -1, dtype=int)
    q = coverage(assignment, capacities, 4)
    left = marginal_changes(q, demands, (0,), (-1,), (0,), capacities, distances)
    right = marginal_changes(q, demands, (1,), (-1,), (1,), capacities, distances)
    joint = marginal_changes(
        q,
        demands,
        (0, 1),
        (-1, -1),
        (0, 1),
        capacities,
        distances,
    )
    assert joint[0] == pytest.approx(left[0] + right[0])
    assert joint[1] == pytest.approx(left[1] + right[1])


def test_disjoint_pair_improvements_compose_without_changing_feasibility() -> None:
    """Two pair swaps on disjoint loads have additive lexicographic gains."""

    capacities = np.ones(4)
    demands = np.ones(4)
    assignment = np.array([0, 1, 2, 3], dtype=int)
    distances = np.full((4, 4), 50.0)
    distances[0, 0], distances[1, 1] = 10.0, 10.0
    distances[0, 1], distances[1, 0] = 0.0, 0.0
    distances[2, 2], distances[3, 3] = 12.0, 12.0
    distances[2, 3], distances[3, 2] = 1.0, 1.0
    q = coverage(assignment, capacities, 4)
    left = marginal_changes(
        q, demands, (0, 1), (0, 1), (1, 0), capacities, distances
    )
    right = marginal_changes(
        q, demands, (2, 3), (2, 3), (3, 2), capacities, distances
    )
    joint = marginal_changes(
        q,
        demands,
        (0, 1, 2, 3),
        (0, 1, 2, 3),
        (1, 0, 3, 2),
        capacities,
        distances,
    )
    assert left[0] == pytest.approx(0.0)
    assert right[0] == pytest.approx(0.0)
    assert left[1] < 0.0 and right[1] < 0.0
    assert joint[0] == pytest.approx(left[0] + right[0])
    assert joint[1] == pytest.approx(left[1] + right[1])


@pytest.mark.parametrize("method", METHODS)
def test_all_variants_are_atomic_monotone_and_deterministic(method: str) -> None:
    world = _world(seed=9001)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    first = run_geo_qpg(world, adjacency, method, max_rounds=1024)
    second = run_geo_qpg(world, adjacency, method, max_rounds=1024)
    np.testing.assert_array_equal(first.assignment, second.assignment)
    assert first.bytes_sent == second.bytes_sent
    assert first.messages == second.messages
    if method == "geo_qpg_lll":
        assert not first.potential_monotone
    else:
        assert first.potential_monotone
    assert first.certificate.conflicts == 0
    assert first.unilateral_local_minimum
    if method in {"geo_qpg_p", "geo_qpg_cf", "geo_qpg_c3", "geo_qpg_d"}:
        assert first.pair_local_minimum
    if method == "geo_qpg_c3":
        assert first.triple_local_minimum
    assert first.algorithm_status == "LOCAL_MINIMUM"
    assert first.rounds < 1024


def test_conflict_free_variant_can_commit_disjoint_moves_in_parallel() -> None:
    world = World(
        world_id="n4-parallel",
        seed=744,
        scenario="manual",
        capacity_cv=0.0,
        pressure=0.5,
        robot_positions=np.array(
            [[0.0, 0.0], [10.0, 0.0], [20.0, 0.0], [1.0, 0.0], [11.0, 0.0], [21.0, 0.0]]
        ),
        load_positions=np.array([[0.0, 1.0], [10.0, 1.0], [20.0, 1.0]]),
        capacities=np.ones(6),
        demands=np.ones(3),
        distances=np.array(
            [
                [1.0, 12.0, 22.0],
                [12.0, 1.0, 12.0],
                [22.0, 12.0, 1.0],
                [2.0, 11.0, 21.0],
                [11.0, 2.0, 11.0],
                [21.0, 11.0, 2.0],
            ]
        ),
    )
    result = run_geo_qpg(world, complete_adjacency(6), "geo_qpg_cf", max_rounds=512)
    assert result.max_parallel_commits >= 2
    assert result.potential_monotone


def _proposal(
    robot: int, load: int, *, priority: int, delta: float = -1.0
) -> MoveProposal:
    return MoveProposal(
        robot_ids=(robot,),
        old_actions=(-1,),
        new_actions=(load,),
        touched_loads=(load,),
        expected_versions=(0,),
        delta_deficit=delta,
        delta_distance=1.0,
        phase=PHASE_QUOTA,
        priority=(priority, robot),
    )


def test_distributed_mis_is_conflict_free_and_maximal_without_global_sort() -> None:
    proposals = (
        _proposal(0, 0, priority=10),
        _proposal(1, 0, priority=20),
        _proposal(2, 1, priority=30),
    )
    selected, iterations = distributed_mis_indices(proposals)
    chosen = [proposals[index] for index in selected]
    assert iterations >= 1
    assert len(chosen) == 2
    assert all(
        not proposals_conflict(left, right)
        for left, right in combinations(chosen, 2)
    )
    rejected = set(range(len(proposals))).difference(selected)
    assert all(
        any(proposals_conflict(proposals[index], winner) for winner in chosen)
        for index in rejected
    )


def test_transaction_aborts_a_stale_prepare_without_mutation() -> None:
    capacities = np.array([1.0, 1.0])
    demands = np.array([1.0])
    distances = np.array([[1.0], [2.0]])
    register = QuotaRegister(demands, capacities, distances)
    ledger = MessageLedger(complete_adjacency(2), n_loads=1)
    tx = TransactionCoordinator(register, ledger)
    first = build_proposal(
        q=register.q.copy(),
        versions=register.versions.copy(),
        demands=demands,
        robot_ids=(0,),
        old_actions=(-1,),
        new_actions=(0,),
        capacities=capacities,
        distances=distances,
        phase=PHASE_QUOTA,
        priority=(0,),
    )
    stale = build_proposal(
        q=register.q.copy(),
        versions=register.versions.copy(),
        demands=demands,
        robot_ids=(1,),
        old_actions=(-1,),
        new_actions=(0,),
        capacities=capacities,
        distances=distances,
        phase=PHASE_QUOTA,
        priority=(1,),
    )
    assert first is not None and stale is not None
    assert tx.prepare_commit(first)[0]
    assignment = register.assignment.copy()
    aggregate = register.q.copy()
    assert tx.prepare_commit(stale) == (False, "STALE_VERSION")
    np.testing.assert_array_equal(register.assignment, assignment)
    np.testing.assert_allclose(register.q, aggregate)
    assert tx.aborted == 1
