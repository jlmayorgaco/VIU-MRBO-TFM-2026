from itertools import product

import numpy as np

from viu_mrob_tfm.sp1.theory import (
    allocation_metrics,
    enumerate_base_game,
    exact_coalition_oracle,
    linear_profile_metrics,
    marginal_payoff,
    quorum_benefit,
    quorum_closure,
    quorum_potential,
    smith_preferences,
)


def test_quorum_benefit_has_endpoints_saturation_and_increasing_increments() -> None:
    values = np.array([quorum_benefit(q, quota=4, beta=2.0) for q in range(6)])
    assert np.isclose(values[0], 0.0)
    assert np.isclose(values[4], 1.0)
    assert np.isclose(values[5], 1.0)
    assert np.all(np.diff(values[:5], n=2) > 0.0)
    assert np.isclose(quorum_benefit(2, quota=4, beta=0.0), 0.5)


def test_marginal_payoffs_reproduce_exact_potential_differences() -> None:
    costs = np.array([[0.1, 0.8], [0.2, 0.7], [0.9, 0.1]])
    quotas = np.array([2, 1])
    penalty = 1.01
    before = np.array([1, 1, 2])
    after = np.array([2, 1, 2])
    delta_u = marginal_payoff(costs, quotas, after, 0, penalty, penalty) - marginal_payoff(
        costs, quotas, before, 0, penalty, penalty
    )
    delta_phi = linear_profile_metrics(costs, quotas, after, penalty, penalty)[
        "potential"
    ] - linear_profile_metrics(costs, quotas, before, penalty, penalty)["potential"]
    assert np.isclose(delta_u, delta_phi)


def test_nash_profiles_are_exact_when_total_quota_is_feasible() -> None:
    costs = np.array([[0.1, 0.8], [0.2, 0.7], [0.9, 0.1]])
    quotas = np.array([2, 1])
    audit = enumerate_base_game(costs, quotas, penalty=1.01)
    assert audit["identity_holds"]
    assert audit["nash_count"] == audit["exact_profiles"] == 3


def test_linear_deficit_is_degenerate_under_scarcity() -> None:
    costs = np.zeros((2, 2))
    quotas = np.array([2, 2])
    concentrated = linear_profile_metrics(costs, quotas, np.array([1, 1]), 1.0, 1.0)
    dispersed = linear_profile_metrics(costs, quotas, np.array([1, 2]), 1.0, 1.0)
    assert concentrated["deficit"] == dispersed["deficit"] == 2
    assert concentrated["excess"] == dispersed["excess"] == 0


def test_quorum_incentive_breaks_the_minimal_scarcity_tie() -> None:
    costs = np.zeros((2, 2))
    quotas = np.array([2, 2])
    values = np.ones(2)
    concentrated = quorum_potential(costs, quotas, values, np.array([1, 1]), 2.0, 0.0, 1.0)
    dispersed = quorum_potential(costs, quotas, values, np.array([1, 2]), 2.0, 0.0, 1.0)
    assert concentrated > dispersed


def test_milp_matches_brute_force_small_optional_instance() -> None:
    costs = np.array(
        [
            [0.1, 0.7, 0.4],
            [0.2, 0.6, 0.5],
            [0.8, 0.1, 0.3],
            [0.7, 0.2, 0.4],
        ]
    )
    quotas = np.array([2, 2, 1])
    values = np.array([1.0, 1.1, 0.45])
    weight = 0.2
    oracle = exact_coalition_oracle(costs, quotas, values, weight)
    oracle_metrics = allocation_metrics(costs, quotas, values, oracle.assignment, weight)
    objectives = []
    for actions in product(range(4), repeat=4):
        metrics = allocation_metrics(costs, quotas, values, np.asarray(actions), weight)
        if metrics["closed"]:
            objectives.append(float(metrics["objective"]))
    assert oracle_metrics["closed"]
    assert np.isclose(oracle_metrics["objective"], max(objectives))


def test_qr_closure_enforces_exclusivity_and_all_or_nothing_quotas() -> None:
    preferences = np.array(
        [
            [0.9, 0.1, 0.2],
            [0.8, 0.2, 0.4],
            [0.1, 0.9, 0.3],
            [0.2, 0.8, 0.6],
            [0.3, 0.4, 0.9],
        ]
    )
    costs = 0.1 * np.ones_like(preferences)
    quotas = np.array([2, 2, 3])
    values = np.ones(3)
    closed = quorum_closure(preferences, costs, quotas, values, cost_weight=0.1)
    metrics = allocation_metrics(costs, quotas, values, closed.assignment, cost_weight=0.1)
    assert metrics["closed"]
    assert np.all((closed.assignment >= 0) & (closed.assignment <= 3))
    counts = np.asarray(metrics["counts"])
    assert np.all((counts == 0) | (counts == quotas))


def test_smith_relaxation_preserves_rows_of_the_simplex_and_separates_raw_output() -> None:
    costs = np.array([[0.1, 0.7], [0.2, 0.6], [0.8, 0.1]])
    quotas = np.array([2, 2])
    values = np.ones(2)
    result = smith_preferences(
        costs,
        quotas,
        values,
        beta=2.0,
        cost_weight=0.1,
        excess_penalty=1.0,
        seed=7,
        time_step=0.1,
        max_steps=100,
        tolerance=1e-7,
    )
    assert result.preferences is not None
    assert np.all(np.isfinite(result.preferences))
    assert np.all(result.preferences >= -1e-12)
    assert np.allclose(result.preferences.sum(axis=1), 1.0)
    assert np.array_equal(result.assignment, np.argmax(result.preferences, axis=1))
