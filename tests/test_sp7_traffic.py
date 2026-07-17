from __future__ import annotations

import math

import numpy as np

from viu_mrob_tfm.sp7.experiment import (
    audit_world_theory,
    generate_world,
    restricted_schedule_oracle,
    run_sp7_config,
    simulate_schedule,
)
from viu_mrob_tfm.sp7.theory import (
    asynchronous_better_response,
    conflict_free_penalty_threshold,
    conflict_pairs,
    is_pure_nash,
    pure_nash_profiles,
    verify_exact_potential_identity,
)


def _two_coalition_game():
    costs = np.asarray([[1.0, 2.2], [1.0, 2.2]])
    resources = (
        (frozenset({"core"}), frozenset()),
        (frozenset({"core"}), frozenset()),
    )
    return costs, resources


def test_route_utility_is_an_exact_potential() -> None:
    costs, resources = _two_coalition_game()
    assert verify_exact_potential_identity(costs, resources, penalty=1.5)


def test_strict_better_response_terminates_at_nash() -> None:
    costs, resources = _two_coalition_game()
    result = asynchronous_better_response(costs, resources, penalty=1.5, seed=7)
    assert np.all(np.diff(result.potential_trace) > 0.0)
    assert result.strict_moves <= 3
    assert is_pure_nash(result.profile, costs, resources, penalty=1.5)


def test_conflict_free_threshold_is_sufficient_but_not_necessary_claim() -> None:
    costs, resources = _two_coalition_game()
    threshold = conflict_free_penalty_threshold(costs, resources)
    assert np.isclose(threshold, 1.2)
    equilibria = pure_nash_profiles(costs, resources, penalty=threshold + 0.1)
    assert equilibria
    assert all(conflict_pairs(profile, resources) == 0 for profile in equilibria)


def test_below_threshold_a_conflicted_nash_can_remain() -> None:
    costs, resources = _two_coalition_game()
    equilibria = pure_nash_profiles(costs, resources, penalty=1.0)
    assert any(conflict_pairs(profile, resources) > 0 for profile in equilibria)


def test_zone_reservation_resolves_opposing_corridor_entry() -> None:
    world = generate_world("bidirectional_corridor", 2, 8700)
    profile = np.zeros(2, dtype=int)
    guarded = simulate_schedule(world, profile, use_zone_reservation=True, priority_mode="aging")
    unguarded = simulate_schedule(world, profile, use_zone_reservation=False, priority_mode="aging")
    assert guarded.delivery_success
    assert guarded.collision_violations == 0
    assert not unguarded.delivery_success
    assert unguarded.deadlock


def test_restricted_oracle_is_auditable_and_delivers() -> None:
    world = generate_world("dynamic_bottleneck", 3, 8701)
    outcome, profile, order, evaluated = restricted_schedule_oracle(world)
    assert outcome.delivery_success
    assert outcome.collision_violations == 0
    assert len(profile) == 3
    assert sorted(order) == [0, 1, 2]
    assert evaluated == 2**3 * math.factorial(3)


def test_world_theory_audit_passes() -> None:
    world = generate_world("crossing", 4, 8702)
    audit = audit_world_theory(world)
    assert audit["exact_potential_verified"]
    assert audit["potential_monotone"]
    assert audit["better_response_ends_at_nash"]
    assert audit["conditional_all_nash_conflict_free"]


def test_smoke_campaign_writes_a_passed_audit(tmp_path) -> None:
    config = tmp_path / "sp7.yaml"
    config.write_text(
        "\n".join(
            [
                "experiment_id: test_sp7",
                "protocol_family: sp7_route_reservation_v1",
                f"output_dir: {str(tmp_path / 'out').replace(chr(92), '/')}",
                "scenarios: [crossing, bidirectional_corridor]",
                "coalition_counts: [2]",
                "seeds: [8700]",
                "methods: [local_potential_reservation, no_congestion_penalty, no_zone_reservation, prioritized_planning, central_restricted_oracle]",
            ]
        ),
        encoding="utf-8",
    )
    manifest = run_sp7_config(config)
    assert manifest["runs"] == 10
    audit = (tmp_path / "out" / "audit.json").read_text(encoding="utf-8")
    assert '"status": "passed"' in audit
