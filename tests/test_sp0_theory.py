from math import factorial

import numpy as np
import pandas as pd

from viu_mrob_tfm.sp0.experiment import sp0_hypothesis_test
from viu_mrob_tfm.sp0.theory import (
    action_fitness,
    auction_assignment,
    enumerate_pure_nash,
    greedy_assignment,
    hungarian_assignment,
    is_pure_nash,
    marginal_payoff,
    pairwise_exchange,
    potential_best_response,
    profile_metrics,
)


def test_action_fitness_has_the_closed_form_used_in_the_thesis() -> None:
    costs = np.array(
        [
            [0.1, 0.8, 0.4],
            [0.4, 0.2, 0.6],
            [0.7, 0.3, 0.5],
        ]
    )
    assignment = np.array([1, 0, 2])
    penalty = 1.1
    robot = 1
    assert np.isclose(action_fitness(costs, assignment, robot, 0, penalty), 0.0)
    assert np.isclose(
        action_fitness(costs, assignment, robot, 1, penalty),
        -penalty - costs[robot, 0],
    )
    assert np.isclose(
        action_fitness(costs, assignment, robot, 3, penalty),
        penalty - costs[robot, 2],
    )


def test_marginal_payoff_is_exact_potential_difference() -> None:
    costs = np.array([[0.1, 0.8], [0.7, 0.2], [0.4, 0.5]])
    penalty = 1.1
    before = np.array([1, 0, 2])
    after = np.array([2, 0, 2])
    delta_utility = marginal_payoff(costs, after, 0, penalty) - marginal_payoff(
        costs, before, 0, penalty
    )
    delta_potential = profile_metrics(costs, after, penalty)["potential"] - profile_metrics(
        costs, before, penalty
    )["potential"]
    assert np.isclose(delta_utility, delta_potential)


def test_nash_set_equals_feasible_set_above_cost_bound() -> None:
    costs = np.array([[0.1, 0.6], [0.4, 0.2], [0.3, 0.8]])
    audit = enumerate_pure_nash(costs, penalty=1.01)
    expected = factorial(3) // factorial(1)
    assert audit["nash_count"] == expected
    assert audit["feasible_profiles"] == expected
    assert all(profile_metrics(costs, a, 1.01)["feasible"] for a in audit["nash_profiles"])


def test_worst_nash_can_be_strictly_suboptimal() -> None:
    epsilon = 1e-3
    costs = np.array([[0.0, epsilon], [epsilon, 1.0]])
    bad_nash = np.array([1, 2])
    optimum = hungarian_assignment(costs)
    assert is_pure_nash(costs, bad_nash, penalty=1.01)
    assert profile_metrics(costs, bad_nash, 1.01)["social_cost"] > 100 * profile_metrics(
        costs, optimum.assignment, 1.01
    )["social_cost"]


def test_euclidean_occupancy_game_cannot_select_only_the_unique_optimum() -> None:
    delta = 0.1
    costs = np.array([[1.0, 0.0], [1.0 - delta, delta]])
    optimum = np.array([2, 1])
    alternative = np.array([1, 2])
    penalty = 1.01
    assert profile_metrics(costs, optimum, penalty)["social_cost"] < profile_metrics(
        costs, alternative, penalty
    )["social_cost"]
    assert is_pure_nash(costs, optimum, penalty)
    assert is_pure_nash(costs, alternative, penalty)


def test_better_response_reaches_feasibility_and_pairwise_refinement_is_monotone() -> None:
    rng = np.random.default_rng(7)
    costs = rng.uniform(0.0, 1.0, size=(6, 4))
    base = potential_best_response(costs, penalty=1.01, rng=np.random.default_rng(8))
    refined = pairwise_exchange(costs, base.assignment)
    base_metrics = profile_metrics(costs, base.assignment, 1.01)
    refined_metrics = profile_metrics(costs, refined.assignment, 1.01)
    assert base.converged and base_metrics["feasible"]
    assert refined.converged and refined_metrics["feasible"]
    assert refined_metrics["social_cost"] <= base_metrics["social_cost"] + 1e-12


def test_auction_certificate_and_additive_optimality_bound() -> None:
    rng = np.random.default_rng(11)
    costs = rng.uniform(0.0, 1.0, size=(7, 5))
    epsilon = 1e-3
    auction = auction_assignment(costs, epsilon=epsilon)
    optimum = hungarian_assignment(costs)
    auction_metrics = profile_metrics(costs, auction.assignment, 1.01)
    optimum_metrics = profile_metrics(costs, optimum.assignment, 1.01)
    assert auction.converged and auction_metrics["feasible"]
    assert auction.epsilon_cs_violation <= epsilon + 1e-10
    assert auction_metrics["social_cost"] <= optimum_metrics["social_cost"] + len(costs) * epsilon + 1e-10


def test_iterative_algorithms_record_valid_histories() -> None:
    costs = np.array([[0.1, 0.7], [0.6, 0.2], [0.3, 0.5]])
    potential = potential_best_response(costs, penalty=1.01, rng=np.random.default_rng(4))
    results = [
        greedy_assignment(costs),
        auction_assignment(costs, epsilon=1e-3),
        potential,
        pairwise_exchange(costs, potential.assignment),
    ]
    for result in results:
        assert result.history
        assert np.array_equal(result.history[-1], result.assignment)
        for state in result.history:
            assert state.shape == (3,)
            assert np.all((state >= 0) & (state <= 2))


def test_sp0_hypothesis_test_uses_paired_discordances() -> None:
    rows = []
    for instance in range(6):
        rows.extend(
            [
                {"instance_id": instance, "method": "potential_br", "feasible": True},
                {"instance_id": instance, "method": "no_exclusion", "feasible": False},
            ]
        )
    result = sp0_hypothesis_test(pd.DataFrame(rows)).iloc[0]
    assert result.n_pairs == 6
    assert result.complete_only == 6
    assert result.ablation_only == 0
    assert np.isclose(result.exact_mcnemar_p_two_sided, 0.03125)
    assert bool(result.reject_h0_alpha_0_05)
