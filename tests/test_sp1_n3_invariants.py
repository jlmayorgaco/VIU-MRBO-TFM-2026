"""N3.E1 white-box: invariants, determinism and the negative control.

No p-values here. E1 asks whether the implementations do what they claim on
instances small enough to check by hand, and whether the one experiment that
must fail actually fails.
"""

from __future__ import annotations

import numpy as np
import pytest

from viu_mrob_tfm.sp1_n3 import weighted_grape
from viu_mrob_tfm.sp1_n3.certificate import (
    CAPACITY_DEFICIT,
    DEFICIT_AND_CONFLICT,
    FEASIBLE,
    ROBOT_CONFLICT,
    certify,
    coverage,
    distance_cost,
    lexicographic_key,
    total_deficit,
)
from viu_mrob_tfm.sp1_n3.contract import priority_token
from viu_mrob_tfm.sp1_n3.graph import (
    adjacency_for_regime,
    complete_adjacency,
    critical_radius,
    graph_metrics,
    r_disk_adjacency,
)
from viu_mrob_tfm.sp1_n3.runner import METHODS, run_method
from viu_mrob_tfm.sp1_n3.worlds import load_count_for, make_world, n2_reference


def _world(n=8, k=3, cv=0.65, pressure=0.80, seed=2026080801, scenario="uniform"):
    return make_world(
        world_id=f"t-{n}-{k}-{cv}-{pressure}-{seed}-{scenario}",
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


# ------------------------------------------------------- N2 world regression
@pytest.mark.parametrize("cv", [0.00, 0.35, 0.65, 1.00])
@pytest.mark.parametrize("scenario", ["uniform", "clustered", "corridor"])
def test_worlds_are_bit_identical_to_the_frozen_n2_generator(
    cv: float, scenario: str
) -> None:
    """N3 must run on N2's worlds, not on worlds that merely resemble them.

    N2's ``make_world`` discards the robot positions that N3 needs for the
    R-disk graph, so this module replays the same RNG stream. If either side
    ever drifts, the campaign would silently compare against a different
    instance family; this fails instead.
    """

    kwargs = dict(
        robot_count=16,
        load_count=5,
        q_bar=5.0,
        cv=cv,
        pressure=0.85,
        scenario=scenario,
        workspace=(100.0, 100.0),
        seed=2026080801,
        alpha=3.0,
    )
    mine = make_world(world_id="regression", **kwargs)
    capacities, masses, distances = n2_reference(**kwargs)
    assert mine.capacities.tobytes() == capacities.tobytes()
    assert mine.demands.tobytes() == masses.tobytes()
    assert mine.distances.tobytes() == distances.tobytes()


def test_positions_reproduce_the_distance_matrix() -> None:
    world = _world(n=12, k=4)
    recomputed = np.linalg.norm(
        world.robot_positions[:, None, :] - world.load_positions[None, :, :], axis=2
    )
    assert recomputed == pytest.approx(world.distances)


def test_load_count_rule_is_explicit() -> None:
    """``3N/10`` is not an integer at the E4 sizes; the rounding is frozen."""

    assert [load_count_for(n) for n in (16, 24, 32, 48, 64)] == [5, 7, 10, 14, 19]


# -------------------------------------------------------------- certificates
def test_certificate_separates_deficit_from_conflict() -> None:
    capacities = np.array([3.0, 3.0, 4.0])
    demands = np.array([6.0, 4.0])
    distances = np.array([[1.0, 5.0], [2.0, 6.0], [9.0, 1.0]])

    feasible = np.array([0, 0, 1])
    verdict = certify(feasible, capacities, demands, distances)
    assert verdict.status == FEASIBLE
    assert verdict.total_deficit == pytest.approx(0.0)
    assert verdict.distance_cost == pytest.approx(1.0 + 2.0 + 1.0)

    short = np.array([0, -1, 1])
    assert certify(short, capacities, demands, distances).status == CAPACITY_DEFICIT
    assert certify(short, capacities, demands, distances).total_deficit == pytest.approx(3.0)

    # An out-of-range index both breaks exclusivity and starves load 1, and
    # the verdict must say so rather than report only the more visible half.
    broken = np.array([0, 0, 7])
    assert certify(broken, capacities, demands, distances).status == DEFICIT_AND_CONFLICT

    # A conflict with no shortfall stays a pure conflict.
    only_conflict = certify(
        np.array([0, 0, 5]),
        capacities,
        np.array([6.0]),
        distances[:, :1],
    )
    assert only_conflict.status == ROBOT_CONFLICT
    assert only_conflict.total_deficit == pytest.approx(0.0)


def test_coverage_and_objectives_match_the_frozen_definitions() -> None:
    capacities = np.array([2.0, 5.0, 1.0])
    demands = np.array([4.0, 3.0])
    distances = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    assignment = np.array([0, 1, 0])
    assert coverage(assignment, capacities, 2) == pytest.approx([3.0, 5.0])
    assert total_deficit(assignment, capacities, demands) == pytest.approx(1.0)
    assert distance_cost(assignment, distances) == pytest.approx(1.0 + 4.0 + 5.0)
    assert lexicographic_key(assignment, capacities, demands, distances) == pytest.approx(
        (1.0, 10.0)
    )


# --------------------------------------------------------------- exclusivity
@pytest.mark.parametrize("method", METHODS)
def test_every_robot_holds_at_most_one_commitment(method: str) -> None:
    for seed in (11, 12, 13):
        world = _world(n=10, k=3, seed=2026080801 + seed)
        adjacency = adjacency_for_regime(world.robot_positions, "medium")
        record = run_method(world, adjacency, method, regime="medium")
        assignment = record.assignment
        assert assignment.shape == (world.n_robots,)
        assert np.all(assignment >= -1)
        assert np.all(assignment < world.n_loads)
        assert record.certificate.status != ROBOT_CONFLICT


# --------------------------------------------------------------- determinism
@pytest.mark.parametrize("method", METHODS)
def test_runs_are_bit_reproducible(method: str) -> None:
    world = _world(n=10, k=3)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    first = run_method(world, adjacency, method, regime="medium")
    second = run_method(world, adjacency, method, regime="medium")
    assert np.array_equal(first.assignment, second.assignment)
    assert first.observation.messages == second.observation.messages
    assert first.observation.bytes_sent == second.observation.bytes_sent
    assert first.observation.rounds == second.observation.rounds
    assert first.certificate.status == second.certificate.status


@pytest.mark.parametrize("method", METHODS)
def test_storage_permutation_does_not_change_the_solution(method: str) -> None:
    """Relabelling the rows must not change who goes where.

    The tie-break token is derived from capacity and position, which travel
    with the robot, precisely so this holds. A token derived from the row index
    would pass every other test here and silently fail this one.
    """

    world = _world(n=9, k=3, seed=2026080877)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    baseline = run_method(world, adjacency, method, regime="medium")

    order = np.array([4, 0, 7, 2, 8, 1, 6, 3, 5])
    shuffled = type(world)(
        world_id=world.world_id,
        seed=world.seed,
        scenario=world.scenario,
        capacity_cv=world.capacity_cv,
        pressure=world.pressure,
        robot_positions=world.robot_positions[order],
        load_positions=world.load_positions,
        capacities=world.capacities[order],
        demands=world.demands,
        distances=world.distances[order],
    )
    permuted_adjacency = adjacency[np.ix_(order, order)]
    other = run_method(shuffled, permuted_adjacency, method, regime="medium")

    # Same decision per physical robot, read back through the permutation.
    assert np.array_equal(other.assignment, baseline.assignment[order])
    assert other.certificate.distance_cost == pytest.approx(
        baseline.certificate.distance_cost
    )


# ------------------------------------------------------- GRAPE potential
@pytest.mark.parametrize("pair_moves", [False, True])
def test_grape_applies_one_strictly_improving_move_per_epoch(pair_moves: bool) -> None:
    """The potential argument only holds if every applied transition improves.

    This replays the epochs and checks ``(D, J)`` strictly decreases
    lexicographically each time a proposal is applied, which is the hypothesis
    the termination claim rests on.
    """

    world = _world(n=8, k=3)
    adjacency = adjacency_for_regime(world.robot_positions, "medium")
    method = "weighted_pair_grape" if pair_moves else "weighted_grape"
    record = run_method(world, adjacency, method, regime="medium")

    # Rebuild the trajectory from the same deterministic run and score it.
    keys = _grape_trajectory(world, adjacency, pair_moves)
    assert len(keys) >= 2, "the run applied no move at all"
    for before, after in zip(keys, keys[1:], strict=False):
        assert after < before, f"potential did not improve: {before} -> {after}"
    assert keys[-1] == pytest.approx(
        lexicographic_key(
            record.assignment, world.capacities, world.demands, world.distances
        )
    )


def _grape_trajectory(world, adjacency, pair_moves: bool) -> list[tuple[float, float]]:
    """Replay a GRAPE run, recording ``(D, J)`` after each applied epoch."""

    from viu_mrob_tfm.sp1_n3.contract import LoadCatalog, priority_tokens, run_rounds
    from viu_mrob_tfm.sp1_n3.runner import default_max_rounds

    keys: list[tuple[float, float]] = []
    inner = weighted_grape.make_step(pair_moves=pair_moves)
    horizon = weighted_grape.epoch_length(world.n_robots)
    seen_epoch = 0

    def watched(view):
        nonlocal seen_epoch
        result = inner(view)
        # Record only epochs that actually applied a move: the terminal epoch
        # ends without one, and counting it would compare a profile with
        # itself rather than test the improvement.
        if view.robot_id == 0 and result.state.epoch > seen_epoch:
            seen_epoch = result.state.epoch
            keys.append(
                lexicographic_key(
                    result.state.actions,
                    world.capacities,
                    world.demands,
                    world.distances,
                )
            )
        return result

    run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=LoadCatalog(world.load_positions, world.demands),
        adjacency=adjacency,
        init=weighted_grape.initial_state,
        step=watched,
        max_rounds=default_max_rounds("weighted_grape", world.n_robots),
        priority_tokens=priority_tokens(
            world.seed, world.capacities, world.robot_positions
        ),
        quiescence_window=horizon + 2,
    )
    initial = lexicographic_key(
        np.full(world.n_robots, -1), world.capacities, world.demands, world.distances
    )
    return [initial, *keys]


def test_pair_moves_can_recruit_an_idle_robot() -> None:
    """The inherited pair move could only swap two already-assigned robots.

    Built as a case where *no* unilateral deviation improves and the only
    improvement is "I leave, you take over": exactly the move a slot exchange
    between two assigned robots cannot express. Checking the generated proposal
    rather than the end-to-end outcome keeps the test about the capability.
    """

    from viu_mrob_tfm.sp1_n3.contract import LoadCatalog, RobotView

    capacities = np.array([5.0, 5.0, 5.0])
    demands = np.array([5.0, 5.0])
    distances = np.array([[1.0, 50.0], [50.0, 10.0], [50.0, 1.0]])
    # A covers load 0 cheaply, B covers load 1 expensively, C sits idle next
    # to load 1. Any single move either starves a load or raises the cost.
    state = weighted_grape.GrapeState(
        coverage=np.array([5.0, 5.0]),
        actions=np.array([0, 1, -1]),
        neighbour_capacity={2: 5.0},
        neighbour_token={2: 4242},
        neighbour_distances={2: distances[2]},
    )
    view = RobotView(
        robot_id=1,
        capacity=5.0,
        position=np.array([0.0, 0.0]),
        distances=distances[1],
        priority_token=99,
        neighbours=(2,),
        catalog=LoadCatalog(np.zeros((2, 2)), demands),
        inbox=(),
        round_index=1,
        n_robots=3,
        n_loads=2,
        max_rounds=100,
        state=state,
    )

    assert weighted_grape._own_best(view, state, pair_moves=False) is None

    joint = weighted_grape._own_best(view, state, pair_moves=True)
    assert joint is not None
    assert (joint.robot_a, joint.action_a) == (1, -1)  # B steps out
    assert (joint.robot_b, joint.action_b) == (2, 1)  # idle C takes the load
    assert joint.deficit_gain == pytest.approx(0.0)
    assert joint.distance_gain == pytest.approx(9.0)


# ------------------------------------------------------------ graph regimes
def test_critical_radius_is_the_connectivity_threshold() -> None:
    world = _world(n=12, k=4)
    radius = critical_radius(world.robot_positions)
    assert graph_metrics(r_disk_adjacency(world.robot_positions, radius)).connected
    below = r_disk_adjacency(world.robot_positions, radius * 0.999)
    assert not graph_metrics(below).connected


def test_regimes_are_ordered_by_connectivity() -> None:
    world = _world(n=16, k=5)
    metrics = {
        regime: graph_metrics(adjacency_for_regime(world.robot_positions, regime))
        for regime in ("complete", "dense", "medium", "threshold", "partitioned")
    }
    assert metrics["partitioned"].components > 1
    for regime in ("complete", "dense", "medium", "threshold"):
        assert metrics[regime].connected
    degrees = [metrics[r].mean_degree for r in ("complete", "dense", "medium", "threshold")]
    assert degrees == sorted(degrees, reverse=True)


def test_minimal_connected_graph_runs() -> None:
    world = _world(n=8, k=3)
    radius = critical_radius(world.robot_positions)
    adjacency = r_disk_adjacency(world.robot_positions, radius)
    assert graph_metrics(adjacency).connected
    for method in METHODS:
        record = run_method(world, adjacency, method, regime="threshold")
        assert record.assignment.shape == (world.n_robots,)


# --------------------------------------------------------- negative control
def test_partition_blocks_guaranteed_feasibility() -> None:
    """The control the inherited implementation could not even express.

    ``sp1_geo`` forced connectivity when building the graph and, worse, still
    computed a globally consistent winner when handed a disconnected one, so a
    partitioned run reported success. Here a partition must actually cost
    feasibility on at least some worlds a connected graph solves.
    """

    broken = 0
    checked = 0
    for offset in range(12):
        world = _world(n=10, k=3, pressure=0.85, seed=2026080801 + 100 * offset)
        connected = adjacency_for_regime(world.robot_positions, "complete")
        partitioned = adjacency_for_regime(world.robot_positions, "partitioned")
        if graph_metrics(partitioned).components < 2:
            continue
        for method in METHODS:
            good = run_method(world, connected, method, regime="complete")
            bad = run_method(world, partitioned, method, regime="partitioned")
            if good.certificate.feasible:
                checked += 1
                if not bad.certificate.feasible:
                    broken += 1
    assert checked > 0, "no world was solved on the connected graph"
    assert broken > 0, (
        "a permanent partition never cost feasibility; the negative control "
        "is not discriminating and would validate a non-distributed method"
    )


def test_priority_token_depends_on_attributes_not_index() -> None:
    first = priority_token(7, 5.0, (1.0, 2.0))
    same = priority_token(7, 5.0, (1.0, 2.0))
    other = priority_token(7, 5.0, (1.0, 2.5))
    assert first == same
    assert first != other


# ------------------------------------------------ regressions: lossy delivery
def test_grape_never_certifies_convergence_on_divergent_profiles() -> None:
    """A self-declared termination must be backed by actual agreement.

    Flooding only on change is enough under reliable delivery and silently
    wrong under loss: a dropped proposal is never retransmitted, the flood
    stops short, robots end the epoch applying different moves, and each then
    concludes -- correctly for its own view -- that nothing is left to do. The
    engine used to see every robot claim success and report CONVERGED. At 15%
    and 30% loss that happened in 25 of 40 runs.
    """

    from viu_mrob_tfm.sp1_n3.contract import CONVERGED, Channel

    divergent = 0
    for rep in range(6):
        world = _world(n=16, k=5, pressure=0.85, seed=4242000 + 31 * rep)
        for regime in ("threshold", "medium"):
            adjacency = adjacency_for_regime(world.robot_positions, regime)
            for loss in (0.3, 0.7):
                channel = Channel(
                    world_id=f"r{rep}", treatment=f"l{loss}", loss_probability=loss
                )
                record = run_method(
                    world,
                    adjacency,
                    "weighted_grape",
                    regime=regime,
                    channel=channel,
                )
                observed = record.observation
                if not observed.consistent:
                    divergent += 1
                    assert observed.algorithm_status != CONVERGED
                if observed.algorithm_status == CONVERGED:
                    assert observed.consistent
    assert divergent > 0, (
        "no run diverged even at 70% loss, so this test is not exercising the "
        "safety net it exists to protect"
    )


def test_capacity_cbba_terminates_on_every_pilot_world() -> None:
    """The frozen bid cycled; the barrier and the frozen commitment stop it.

    Before the fix the process never settled: 0 of 27 pilot runs terminated, 10
    were caught in a limit cycle, and raising the budget from 192 to 4000
    rounds made the result *worse* because the cut fell elsewhere in the cycle.
    """

    from viu_mrob_tfm.sp1_n3.contract import CYCLE_OBSERVED

    for size in (10, 16):
        for scenario in ("uniform", "clustered", "corridor"):
            for rep in range(2):
                world = _world(
                    n=size,
                    k=load_count_for(size),
                    pressure=0.85,
                    seed=4242000 + 101 * rep + size,
                    scenario=scenario,
                )
                for regime in ("complete", "medium", "threshold"):
                    adjacency = adjacency_for_regime(world.robot_positions, regime)
                    record = run_method(
                        world, adjacency, "capacity_cbba_rb", regime=regime
                    )
                    assert record.observation.algorithm_status != CYCLE_OBSERVED


def test_cbba_repairs_stale_records_under_loss() -> None:
    """Diffs alone assume delivery; the heartbeat is what repairs a drop.

    ``sent`` records what was transmitted, not what arrived. Without periodic
    retransmission a dropped record is marked as sent and never repeated, so a
    neighbour can hold a stale commitment for the rest of the run.
    """

    from viu_mrob_tfm.sp1_n3.contract import Channel, LoadCatalog, priority_tokens, run_rounds
    from viu_mrob_tfm.sp1_n3 import capacity_cbba
    from viu_mrob_tfm.sp1_n3.runner import default_max_rounds

    stale = 0
    total = 0
    for rep in range(4):
        world = _world(n=16, k=5, pressure=0.85, seed=4242000 + 31 * rep)
        adjacency = adjacency_for_regime(world.robot_positions, "medium")
        channel = Channel(
            world_id=f"h{rep}", treatment="loss-30", loss_probability=0.30
        )
        states, _ = run_rounds(
            capacities=world.capacities,
            positions=world.robot_positions,
            distances=world.distances,
            catalog=LoadCatalog(world.load_positions, world.demands),
            adjacency=adjacency,
            channel=channel,
            init=capacity_cbba.initial_state,
            step=capacity_cbba.step,
            max_rounds=default_max_rounds("capacity_cbba_rb", world.n_robots),
            priority_tokens=priority_tokens(
                world.seed, world.capacities, world.robot_positions
            ),
            quiescence_window=capacity_cbba.heartbeat_period(world.n_robots) + 1,
            signature=capacity_cbba.commitment_signature,
        )
        truth = capacity_cbba.commitment_signature(states)
        for holder, state in enumerate(states):
            for other in range(world.n_robots):
                if other == holder:
                    continue
                total += 1
                record = state.table.get(other)
                if record is None or record.target != truth[other]:
                    stale += 1
    assert total > 0
    assert stale == 0, f"{stale}/{total} table entries never repaired after a drop"


def test_a_fixed_point_is_not_reported_as_a_cycle() -> None:
    """Stability repeats its signature every round; that is not oscillation."""

    from viu_mrob_tfm.sp1_n3.contract import (
        LoadCatalog,
        QUIESCENT_OBSERVED,
        StepResult,
        run_rounds,
    )

    world = _world(n=5, k=2)
    _, observed = run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=LoadCatalog(world.load_positions, world.demands),
        adjacency=complete_adjacency(world.n_robots),
        init=lambda view: 0,
        step=lambda view: StepResult(state=view.state),
        max_rounds=30,
        priority_tokens=list(range(world.n_robots)),
        signature=lambda states: tuple(states),
        quiescence_window=3,
    )
    assert observed.algorithm_status == QUIESCENT_OBSERVED
    assert not observed.cycle_detected


# ----------------------------------------------- gates before the confirmatory
def test_cycle_detector_never_shortens_a_run() -> None:
    """Observation must not become a decision, nor a discount on the bill.

    If the engine stopped the moment a repeat appeared, the method that cycles
    would be charged fewer rounds and fewer bytes than it actually spends, and
    the communication comparison would reward cycling.
    """

    from viu_mrob_tfm.sp1_n3.contract import LoadCatalog, StepResult, run_rounds

    world = _world(n=6, k=2)
    seen_rounds: list[int] = []

    def step(view):
        seen_rounds.append(view.round_index)
        # Deliberately oscillates between two configurations forever.
        return StepResult(state=(view.round_index % 2, view.robot_id))

    _, watched = run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=LoadCatalog(world.load_positions, world.demands),
        adjacency=complete_adjacency(world.n_robots),
        init=lambda view: (0, view.robot_id),
        step=step,
        max_rounds=25,
        priority_tokens=list(range(world.n_robots)),
        signature=lambda states: tuple(states),
        quiescence_window=3,
    )
    assert watched.cycle_detected, "the probe was supposed to cycle"
    # The run went the full distance despite the cycle being visible early.
    assert watched.rounds == 25
    assert max(seen_rounds) == 24


def test_cbba_barrier_reads_only_local_state() -> None:
    """The barrier is what makes CBBA-RB terminate, so it must stay local.

    It may only remember bids this robot itself lost with, which it knows from
    its own table. A barrier fed by the true global deficit, by the oracle or
    by the observer would make the method quietly centralised.
    """

    import inspect

    from viu_mrob_tfm.sp1_n3 import capacity_cbba

    source = inspect.getsource(capacity_cbba)
    for forbidden in (
        "oracle",
        "observation",
        "adjacency",
        "diameter",
        "lambda_2",
        "global",
    ):
        assert forbidden not in source.lower().replace("globally", ""), (
            f"capacity_cbba refers to {forbidden!r}; the barrier must be built "
            "from RobotView and delivered messages only"
        )
    # The barrier is written only from this robot's own losing bid.
    assert "barrier[target] = lost_with if previous is None else max(" in source


@pytest.mark.parametrize("scenario", ["uniform", "clustered", "corridor"])
def test_pair_grape_refines_and_never_worsens_grape(scenario: str) -> None:
    """Pair-GRAPE starts from the unilateral equilibrium, so it cannot lose.

    Running it as a separate search from the same start would let it land
    worse on some worlds, and then it could not be reported as a sensitivity
    of Weighted-GRAPE at all.
    """

    for offset in range(4):
        world = _world(
            n=12, k=4, pressure=0.85, seed=2026080801 + 31 * offset, scenario=scenario
        )
        adjacency = adjacency_for_regime(world.robot_positions, "medium")
        unilateral = run_method(world, adjacency, "weighted_grape", regime="medium")
        paired = run_method(world, adjacency, "weighted_pair_grape", regime="medium")
        key_uni = lexicographic_key(
            unilateral.assignment, world.capacities, world.demands, world.distances
        )
        key_pair = lexicographic_key(
            paired.assignment, world.capacities, world.demands, world.distances
        )
        assert key_pair <= key_uni, (
            f"pair refinement worsened the profile: {key_uni} -> {key_pair}"
        )


def test_disconnected_components_exchange_nothing() -> None:
    """The negative control must be a real information barrier.

    Not merely "coordination is harder": no message may cross between
    components, so no component can acquire another's state at any price.
    """

    from viu_mrob_tfm.sp1_n3.contract import LoadCatalog, priority_tokens, run_rounds
    from viu_mrob_tfm.sp1_n3 import capacity_cbba
    from viu_mrob_tfm.sp1_n3.graph import components
    from viu_mrob_tfm.sp1_n3.runner import default_max_rounds

    world = _world(n=16, k=5, pressure=0.85, seed=4242000)
    adjacency = adjacency_for_regime(world.robot_positions, "partitioned")
    blocks = components(adjacency)
    assert len(blocks) >= 2, "this world did not partition; pick another"
    membership = {robot: index for index, b in enumerate(blocks) for robot in b}

    crossings = 0

    def watched(view):
        for message in view.inbox:
            nonlocal crossings
            if membership[message.sender] != membership[view.robot_id]:
                crossings += 1
        return capacity_cbba.step(view)

    run_rounds(
        capacities=world.capacities,
        positions=world.robot_positions,
        distances=world.distances,
        catalog=LoadCatalog(world.load_positions, world.demands),
        adjacency=adjacency,
        init=capacity_cbba.initial_state,
        step=watched,
        max_rounds=default_max_rounds("capacity_cbba_rb", world.n_robots),
        priority_tokens=priority_tokens(
            world.seed, world.capacities, world.robot_positions
        ),
        quiescence_window=capacity_cbba.heartbeat_period(world.n_robots) + 1,
    )
    assert crossings == 0, f"{crossings} messages crossed a permanent partition"


def test_pair_grape_phase_switch_is_not_a_cycle() -> None:
    """Crossing from unilateral to joint deviations moves nobody.

    The profile at the end of phase 0 is the profile at the start of phase 1,
    so a signature that ignores the phase sees a revisit and reports a cycle on
    every single Pair-GRAPE run. It is an observational false positive, not an
    oscillation, and it invalidated a whole confirmatory campaign once.
    """

    for offset in range(3):
        world = _world(n=16, k=5, pressure=0.85, seed=2026080901 + 17 * offset)
        adjacency = adjacency_for_regime(world.robot_positions, "medium")
        paired = run_method(world, adjacency, "weighted_pair_grape", regime="medium")
        unilateral = run_method(world, adjacency, "weighted_grape", regime="medium")
        assert not unilateral.observation.cycle_detected
        assert not paired.observation.cycle_detected, (
            "the phase boundary was reported as a cycle of length "
            f"{paired.observation.cycle_length}"
        )
