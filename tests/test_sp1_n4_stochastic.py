from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime
from viu_mrob_tfm.sp1_n3.worlds import make_world
from viu_mrob_tfm.sp1_n4.stochastic import (
    canonical_event_schedule,
    run_event_triggered_policy,
    run_perfect_foresight_oracle,
)


def _world(seed: int = 901):
    return make_world(
        world_id=f"dynamic-{seed}",
        robot_count=5,
        load_count=3,
        q_bar=5.0,
        cv=0.50,
        pressure=0.65,
        scenario="uniform",
        workspace=(40.0, 40.0),
        seed=seed,
        alpha=3.0,
    )


def test_dynamic_schedule_is_exogenous_and_reproducible() -> None:
    world = _world()
    first = canonical_event_schedule(world)
    second = canonical_event_schedule(world)
    assert first == second
    assert [event.name for event in first] == [
        "initial_job",
        "job_1_arrival",
        "robot_failure",
        "job_0_completion",
        "job_2_arrival",
        "job_1_completion",
    ]


def test_warm_policy_is_reproducible_and_records_atomic_endpoints() -> None:
    world = _world(902)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    events = canonical_event_schedule(world)
    first = run_event_triggered_policy(
        world, adjacency, events, policy="event_triggered_warm", max_rounds=512
    )
    second = run_event_triggered_policy(
        world, adjacency, events, policy="event_triggered_warm", max_rounds=512
    )
    assert np.isclose(first.discounted_cost, second.discounted_cost)
    assert first.history["assignment"].tolist() == second.history["assignment"].tolist()
    assert len(first.history) == len(events)
    assert first.atomic_feasible_rate >= 0.0


def test_small_dynamic_oracle_is_a_lower_bound_for_executed_policies() -> None:
    world = _world(903)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    events = canonical_event_schedule(world)
    cold = run_event_triggered_policy(
        world, adjacency, events, policy="myopic_cold", max_rounds=512
    )
    warm = run_event_triggered_policy(
        world, adjacency, events, policy="event_triggered_warm", max_rounds=512
    )
    oracle = run_perfect_foresight_oracle(world, events)
    assert oracle.discounted_cost <= cold.discounted_cost + 1e-10
    assert oracle.discounted_cost <= warm.discounted_cost + 1e-10
    assert oracle.messages == 0
