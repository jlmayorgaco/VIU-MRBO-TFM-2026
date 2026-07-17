from __future__ import annotations

import json

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp8.experiment import (
    audit_world_theory,
    generate_world,
    run_sp8_config,
    simulate_local_protocol,
)
from viu_mrob_tfm.sp8.theory import (
    asynchronous_visible_better_response,
    exhaustive_global_oracle,
    global_conflict_pairs,
    is_visible_nash,
    missed_conflict_pairs,
    profile_space_size,
    retransmission_failure_probability,
    verify_exact_network_potential,
    visible_conflict_pairs,
)


def _small_game():
    costs = np.asarray([[0.1, 0.4], [0.1, 0.4], [0.2, 0.3]])
    resources = (
        (frozenset({"a"}), frozenset({"b"})),
        (frozenset({"a"}), frozenset({"c"})),
        (frozenset({"b"}), frozenset({"c"})),
    )
    graph = np.asarray(
        [
            [False, True, False],
            [True, False, True],
            [False, True, False],
        ],
        dtype=bool,
    )
    return costs, resources, graph


def test_network_visible_game_is_an_exact_potential() -> None:
    costs, resources, graph = _small_game()
    assert verify_exact_network_potential(costs, resources, graph, penalty=2.0)


def test_visible_better_response_terminates_at_visible_nash() -> None:
    costs, resources, graph = _small_game()
    result = asynchronous_visible_better_response(
        costs,
        resources,
        graph,
        penalty=2.0,
        initial_profile=np.asarray([0, 0, 0]),
        seed=17,
    )
    assert result.visible_nash
    assert np.all(np.diff(result.potential_trace) > 0.0)
    assert result.strict_moves <= 2**3 - 1
    assert is_visible_nash(result.profile, costs, resources, graph, penalty=2.0)


def test_partition_can_hide_a_global_conflict() -> None:
    resources = (
        (frozenset({"core"}), frozenset({"a"})),
        (frozenset({"core"}), frozenset({"b"})),
    )
    profile = np.asarray([0, 0])
    disconnected = np.zeros((2, 2), dtype=bool)
    assert global_conflict_pairs(profile, resources) == 1
    assert visible_conflict_pairs(profile, resources, disconnected) == 0
    assert missed_conflict_pairs(profile, resources, disconnected) == 1


def test_retransmission_bound_decays_geometrically() -> None:
    assert np.isclose(retransmission_failure_probability(0.2, 0), 1.0)
    assert np.isclose(retransmission_failure_probability(0.2, 5), 0.2**5)
    assert retransmission_failure_probability(0.2, 5) < retransmission_failure_probability(0.2, 1)


def test_exhaustive_oracle_certifies_only_below_profile_cap() -> None:
    costs, resources, _graph = _small_game()
    certified = exhaustive_global_oracle(costs, resources, 2.0, max_profiles=8)
    skipped = exhaustive_global_oracle(costs, resources, 2.0, max_profiles=7)
    assert certified.certified
    assert certified.evaluated_profiles == 8
    assert certified.profile is not None
    assert not skipped.certified
    assert skipped.evaluated_profiles == 0
    assert skipped.profile is None


def test_profile_space_uses_unbounded_integer_arithmetic() -> None:
    resources = tuple((frozenset({f"a{i}"}), frozenset({f"b{i}"})) for i in range(64))
    assert profile_space_size(resources) == 2**64


def test_network_regimes_share_the_same_strategic_instance() -> None:
    nominal = generate_world(
        "nominal",
        {"radius": 2.0, "max_delay_events": 0, "packet_loss": 0.0},
        8,
        8800,
    )
    harsh = generate_world(
        "harsh_combined",
        {"radius": 0.3, "max_delay_events": 3, "packet_loss": 0.35},
        8,
        8800,
    )
    assert nominal.instance_hash == harsh.instance_hash
    assert nominal.world_hash != harsh.world_hash
    assert np.array_equal(nominal.base_costs, harsh.base_costs)
    assert np.array_equal(nominal.initial_profile, harsh.initial_profile)


def test_periodic_protocol_accounts_for_every_attempted_message() -> None:
    world = generate_world(
        "loss",
        {"radius": 2.0, "max_delay_events": 2, "packet_loss": 0.3},
        8,
        8801,
        horizon_sweeps=4,
    )
    outcome = simulate_local_protocol(world, periodic=True)
    assert outcome.messages_attempted == outcome.messages_delivered + outcome.messages_dropped
    assert np.all((outcome.profile == 0) | (outcome.profile == 1))
    assert outcome.protocol_state_bytes > 0
    assert outcome.mean_version_lag >= 0.0
    assert outcome.max_version_lag >= 0
    assert 0.0 <= outcome.missing_view_fraction <= 1.0


def test_theory_audit_checks_catalogue_and_visible_equilibrium() -> None:
    world = generate_world(
        "nominal",
        {"radius": 2.0, "max_delay_events": 0, "packet_loss": 0.0},
        4,
        8802,
    )
    audit = audit_world_theory(world, oracle_cap=4096)
    assert audit["exact_network_potential_verified"]
    assert audit["strict_potential_monotonicity"]
    assert audit["better_response_visible_nash"]
    assert audit["catalogue_has_conflict_free_profile"]
    assert audit["oracle_certified"]


def test_smoke_campaign_writes_passed_audit(tmp_path) -> None:
    config = tmp_path / "sp8.yaml"
    output = tmp_path / "out"
    config.write_text(
        "\n".join(
            [
                "experiment_id: test_sp8",
                "protocol_family: sp8_visible_route_network_v1",
                f"output_dir: {str(output).replace(chr(92), '/')}",
                "coalition_counts: [4]",
                "seeds: [8800, 8801]",
                "penalty: 2.0",
                "horizon_sweeps: 4",
                "message_bytes: 32",
                "oracle_max_profiles: 16",
                "network_regimes:",
                "  nominal: {radius: 2.0, max_delay_events: 0, packet_loss: 0.0}",
                "  loss: {radius: 2.0, max_delay_events: 1, packet_loss: 0.25}",
                "  delay: {radius: 2.0, max_delay_events: 2, packet_loss: 0.0}",
                "methods:",
                "  - periodic_versioned_local",
                "  - event_driven_local",
                "  - perfect_information_response",
                "  - random_static",
                "  - central_exhaustive_oracle",
            ]
        ),
        encoding="utf-8",
    )
    manifest = run_sp8_config(config)
    assert manifest["worlds"] == 6
    assert manifest["runs"] == 30
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "passed"
    assert all(audit["checks"].values())
    hypotheses = pd.read_csv(output / "tables" / "hypotheses.csv").set_index("id")
    assert hypotheses.loc["H8.1", "n"] == 2
    assert hypotheses.loc["H8.1", "n_regime_pairs"] == 4
