"""The N3 information contract, enforced rather than documented.

The inherited ``sp1_geo`` allocators passed a code review by being named after
distributed algorithms. These tests exist so that N3 cannot: they check the
shape of what a robot can see, not the intentions of the module that reads it.
"""

from __future__ import annotations

import dataclasses
import inspect

import numpy as np
import pytest

from viu_mrob_tfm.sp1_n3 import capacity_cbba, weighted_grape
from viu_mrob_tfm.sp1_n3.contract import (
    CONVERGED,
    Channel,
    LoadCatalog,
    Message,
    Outgoing,
    QUIESCENT_OBSERVED,
    RobotView,
    StepResult,
    priority_token,
    priority_tokens,
    run_rounds,
    wire_size,
)
from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime, complete_adjacency
from viu_mrob_tfm.sp1_n3.messages import (
    KIND_GRAPE_PROPOSAL,
    BidRecord,
    Proposal,
    decode_cbba_table,
    decode_neighbour_profile,
    decode_proposal,
    encode_cbba_table,
    encode_neighbour_profile,
    encode_proposal,
)
from viu_mrob_tfm.sp1_n3.runner import METHODS, run_method
from viu_mrob_tfm.sp1_n3.worlds import make_world


def _world(n=8, k=3, cv=0.65, pressure=0.80, seed=2026080801, scenario="uniform"):
    return make_world(
        world_id=f"t-{n}-{k}-{cv}-{pressure}-{seed}",
        robot_count=n,
        load_count=k,
        q_bar=5.0,
        cv=cv,
        pressure=pressure,
        scenario=scenario,
        workspace=(100.0, 100.0),
        seed=seed,
        alpha=3.0,
    )


# ------------------------------------------------------------------ the view
def test_robot_view_exposes_nothing_global() -> None:
    """A view carries local state, the announced catalogue and public sizes.

    Anything else -- another robot's capacity or position, the adjacency
    matrix, the diameter, the full assignment -- must be absent, so a step
    function cannot read it even by accident.
    """

    fields = {field.name for field in dataclasses.fields(RobotView)}
    assert fields == {
        "robot_id",
        "capacity",
        "position",
        "distances",
        "priority_token",
        "neighbours",
        "catalog",
        "inbox",
        "round_index",
        "n_robots",
        "n_loads",
        "max_rounds",
        "state",
    }
    forbidden = {
        "adjacency",
        "diameter",
        "lambda_2",
        "capacities",
        "positions",
        "assignment",
        "coverage_truth",
        "rounds_remaining",
        "world",
    }
    assert not (fields & forbidden)


def test_catalog_is_the_only_shared_input() -> None:
    fields = {field.name for field in dataclasses.fields(LoadCatalog)}
    assert fields == {"positions", "demands"}


@pytest.mark.parametrize("method", METHODS)
def test_step_functions_take_only_a_view(method: str) -> None:
    if method == "capacity_cbba_rb":
        step = capacity_cbba.step
    else:
        step = weighted_grape.make_step(pair_moves=method == "weighted_pair_grape")
    signature = inspect.signature(step)
    assert list(signature.parameters) == ["view"]


# -------------------------------------------------------------- round timing
def test_a_message_sent_at_t_cannot_be_seen_at_t() -> None:
    """No robot may react within the same round to what another just said."""

    seen: list[tuple[int, int, int]] = []

    def init(view: RobotView) -> int:
        return 0

    def step(view: RobotView) -> StepResult:
        for message in view.inbox:
            seen.append((view.round_index, message.sender, message.round_sent))
            assert message.round_sent < view.round_index
        payload = encode_proposal(
            Proposal(True, 0, 1.0, 1.0, 7, view.robot_id, 0, 1.0, view.robot_id, 0, 1.0)
        )
        return StepResult(
            state=view.state + 1,
            outgoing=tuple(
                Outgoing(recipient=other, kind=KIND_GRAPE_PROPOSAL, payload=payload)
                for other in view.neighbours
            ),
        )

    world = _world(n=5, k=2)
    catalog = LoadCatalog(world.load_positions, world.demands)
    run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=catalog,
        adjacency=complete_adjacency(world.n_robots),
        init=init,
        step=step,
        max_rounds=6,
        priority_tokens=priority_tokens(
            world.seed, world.capacities, world.robot_positions
        ),
    )
    assert seen, "the probe never received anything"


def test_sending_to_a_non_neighbour_is_refused() -> None:
    world = _world(n=4, k=2)
    adjacency = np.zeros((4, 4), dtype=bool)
    adjacency[0, 1] = adjacency[1, 0] = True

    def step(view: RobotView) -> StepResult:
        if view.robot_id != 0:
            return StepResult(state=None)
        return StepResult(
            state=None,
            outgoing=(Outgoing(recipient=3, kind=KIND_GRAPE_PROPOSAL, payload=b""),),
        )

    with pytest.raises(ValueError, match="non-neighbour"):
        run_rounds(
            capacities=world.capacities,
            positions=world.robot_positions,
            distances=world.distances,
            catalog=LoadCatalog(world.load_positions, world.demands),
            adjacency=adjacency,
            init=lambda view: None,
            step=step,
            max_rounds=2,
            priority_tokens=[0, 1, 2, 3],
        )


# ------------------------------------------------------------------- bytes
def test_message_sizes_are_serialized_not_assumed() -> None:
    """Every payload's cost is the length of its own encoding.

    ``sp1_geo`` priced a message at 40, 48 or ``16+8Kd`` bytes depending on the
    allocator, which made any communication comparison a comparison of those
    constants.
    """

    distances = np.array([1.0, 2.0, 3.0])
    profile = encode_neighbour_profile(4.5, 12345, distances)
    capacity, token, decoded = decode_neighbour_profile(profile)
    assert capacity == pytest.approx(4.5)
    assert token == 12345
    assert decoded == pytest.approx(distances)
    assert wire_size(profile) == 7 + len(profile)

    records = (
        BidRecord(0, 1, 5.0, 2.5, -3.0, 99, 4),
        BidRecord(1, -1, 6.0, 0.0, 0.0, 17, 2),
    )
    table = encode_cbba_table(records)
    assert decode_cbba_table(table) == records
    assert len(table) == 2 * (len(encode_cbba_table(records[:1])))

    proposal = Proposal(True, 3, 1.5, 0.25, 42, 1, 2, 5.0, 3, -1, 6.0)
    assert decode_proposal(encode_proposal(proposal)) == proposal


def test_reported_bytes_match_the_transmissions() -> None:
    world = _world(n=6, k=2)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    record = run_method(world, adjacency, "capacity_cbba_rb", regime="medium")
    observed = record.observation
    assert observed.bytes_sent == sum(observed.bytes_by_round)
    assert observed.messages == sum(observed.messages_by_round)
    # Every transmission carries at least the envelope.
    assert observed.bytes_sent >= 7 * observed.messages


# ------------------------------------------------------------------ channel
def test_channel_realization_is_paired_across_methods() -> None:
    """Two methods must meet the same link state on the same edge and round.

    Otherwise a chattier algorithm faces a different network, and the
    comparison measures the draw rather than the method.
    """

    channel = Channel(
        world_id="w1", treatment="loss-15", loss_probability=0.15, delay_rounds=0
    )
    twin = Channel(
        world_id="w1", treatment="loss-15", loss_probability=0.15, delay_rounds=0
    )
    drops = [
        (u, v, t)
        for u in range(6)
        for v in range(6)
        for t in range(20)
        if channel.dropped(u, v, t)
    ]
    twin_drops = [
        (u, v, t)
        for u in range(6)
        for v in range(6)
        for t in range(20)
        if twin.dropped(u, v, t)
    ]
    assert drops == twin_drops
    assert drops, "a 15% loss over 720 draws should drop something"


def test_channel_treatment_changes_the_realization() -> None:
    nominal = Channel(world_id="w1", treatment="nominal", loss_probability=0.15)
    other = Channel(world_id="w1", treatment="loss-15", loss_probability=0.15)
    assert [nominal.dropped(0, 1, t) for t in range(40)] != [
        other.dropped(0, 1, t) for t in range(40)
    ]


# ------------------------------------------------------------------- status
def test_cbba_never_claims_convergence() -> None:
    """The adaptation runs no distributed termination protocol, so it may not.

    Absence of change is detected by the observer, which is a weaker statement
    and gets a weaker name.
    """

    world = _world(n=8, k=3)
    for regime in ("complete", "medium", "threshold"):
        adjacency = adjacency_for_regime(world.robot_positions, regime)
        record = run_method(world, adjacency, "capacity_cbba_rb", regime=regime)
        assert record.observation.algorithm_status != CONVERGED


def test_grape_convergence_is_a_distributed_certificate() -> None:
    """GRAPE may claim CONVERGED: every robot learns "no move" simultaneously."""

    world = _world(n=8, k=3)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    record = run_method(world, adjacency, "weighted_pair_grape", regime="medium")
    assert record.observation.algorithm_status in {CONVERGED, QUIESCENT_OBSERVED}
