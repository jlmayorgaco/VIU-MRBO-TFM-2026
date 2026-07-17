from itertools import product

import numpy as np

from viu_mrob_tfm.sp2.effective_capacity import (
    coverage_reference,
    effective_capacity,
    marginal_payoff,
    marginal_potential,
    operational_availability,
    plain_payoff,
    score_reference,
    service_contribution,
)


def test_service_contribution_preserves_legacy_values_without_mass_semantics() -> None:
    contribution = service_contribution(
        nominal_payload_kg=np.array([10.0, 20.0]),
        battery_fraction=np.array([1.0, 0.5]),
        reserve_fraction=np.array([0.2, 0.2]),
        distance_m=np.array([[0.0, 10.0], [0.0, 10.0]]),
        distance_scale_m=10.0,
        compatibility=np.array([[1, 0], [1, 1]]),
    )
    assert np.isclose(contribution[0, 0], 10.0)
    assert np.isclose(contribution[1, 0], 7.5)
    assert np.isclose(contribution[1, 1], 7.5 / np.e)
    assert contribution[0, 1] == 0.0
    rescaled = service_contribution(
        nominal_payload_kg=np.array([10.0, 20.0]),
        battery_fraction=np.array([1.0, 0.5]),
        reserve_fraction=np.array([0.2, 0.2]),
        distance_m=np.array([[0.0, 10.0], [0.0, 10.0]]),
        distance_scale_m=10.0,
        compatibility=np.array([[1, 0], [1, 1]]),
        service_reference_kg=10.0,
    )
    assert np.allclose(rescaled, contribution / 10.0)
    assert np.allclose(
        effective_capacity(
            np.array([10.0, 20.0]),
            np.array([1.0, 0.5]),
            np.array([0.2, 0.2]),
            np.array([[0.0, 10.0], [0.0, 10.0]]),
            10.0,
            np.array([[1, 0], [1, 1]]),
        ),
        contribution,
    )


def test_operational_availability_does_not_mutate_physical_payload() -> None:
    payload = np.array([10.0, 20.0])
    availability = operational_availability(
        battery_fraction=np.array([1.0, 0.5]),
        reserve_fraction=np.array([0.2, 0.2]),
        distance_m=np.array([[0.0], [10.0]]),
        distance_scale_m=10.0,
    )
    assert np.all((availability >= 0.0) & (availability <= 1.0))
    assert np.array_equal(payload, np.array([10.0, 20.0]))


def test_marginal_payoff_is_the_potential_gradient() -> None:
    preferences = np.array([[0.20, 0.25], [0.35, 0.10]])
    capacity = np.array([[4.0, 7.0], [8.0, 3.0]])
    demand = np.array([10.0, 12.0])
    values = np.array([1.0, 1.3])
    costs = np.array([[0.02, 0.05], [0.04, 0.03]])
    payoff = marginal_payoff(preferences, capacity, demand, values, costs)
    epsilon = 1e-7
    for robot, load in product(range(2), range(2)):
        perturbed = preferences.copy()
        perturbed[robot, load] += epsilon
        finite_difference = (
            marginal_potential(perturbed, capacity, demand, values, costs)
            - marginal_potential(preferences, capacity, demand, values, costs)
        ) / epsilon
        assert np.isclose(finite_difference, payoff[robot, load], atol=1e-6)


def test_marginal_potential_gradient_across_the_saturation_boundary() -> None:
    capacity = np.array([[6.0], [4.0]])
    demand = np.array([10.0])
    values = np.array([1.7])
    costs = np.array([[0.03], [0.05]])
    epsilon = 1e-7
    for preferences in (
        np.array([[0.30], [0.20]]),
        np.array([[0.60], [0.40]]),
        np.array([[0.80], [0.70]]),
    ):
        payoff = marginal_payoff(preferences, capacity, demand, values, costs)
        for robot in range(2):
            plus = preferences.copy()
            minus = preferences.copy()
            plus[robot, 0] += epsilon
            minus[robot, 0] -= epsilon
            numeric = (
                marginal_potential(plus, capacity, demand, values, costs)
                - marginal_potential(minus, capacity, demand, values, costs)
            ) / (2.0 * epsilon)
            assert np.isclose(numeric, payoff[robot, 0], atol=2e-6)


def test_plain_payoff_cross_partials_are_not_symmetric_under_heterogeneity() -> None:
    preferences = np.array([[0.2], [0.3]])
    capacity = np.array([[4.0], [8.0]])
    demand = np.array([20.0])
    values = np.array([1.0])
    costs = np.zeros((2, 1))
    epsilon = 1e-6
    baseline = plain_payoff(preferences, capacity, demand, values, costs)
    change_j = preferences.copy()
    change_j[1, 0] += epsilon
    d_f_i_d_rho_j = (
        plain_payoff(change_j, capacity, demand, values, costs)[0, 0]
        - baseline[0, 0]
    ) / epsilon
    change_i = preferences.copy()
    change_i[0, 0] += epsilon
    d_f_j_d_rho_i = (
        plain_payoff(change_i, capacity, demand, values, costs)[1, 0]
        - baseline[1, 0]
    ) / epsilon
    assert not np.isclose(d_f_i_d_rho_j, d_f_j_d_rho_i)
    marginal = marginal_payoff(preferences, capacity, demand, values, costs)
    marginal_j = marginal_payoff(change_j, capacity, demand, values, costs)
    marginal_i = marginal_payoff(change_i, capacity, demand, values, costs)
    assert np.isclose(
        (marginal_j[0, 0] - marginal[0, 0]) / epsilon,
        (marginal_i[1, 0] - marginal[1, 0]) / epsilon,
    )


def test_coverage_reference_matches_brute_force() -> None:
    capacity = np.array([[8.0, 3.0], [7.0, 6.0], [2.0, 9.0]])
    demand = np.array([10.0, 10.0])
    result = coverage_reference(capacity, demand, distance_weight=0.0)
    candidates = []
    for labels in product(range(3), repeat=3):
        assignment = np.zeros((3, 2))
        for robot, label in enumerate(labels):
            if label:
                assignment[robot, label - 1] = 1.0
        supplied = np.minimum((capacity * assignment).sum(axis=0), demand)
        candidates.append(float(np.sum(supplied / demand)))
    assert result.optimal
    assert np.isclose(result.objective, max(candidates))


def test_score_reference_prefers_completion_over_slightly_more_coverage() -> None:
    capacity = np.array([[6.0, 0.0], [4.0, 11.0]])
    demand = np.array([10.0, 25.0])
    values = np.ones(2)
    result = score_reference(
        capacity,
        demand,
        values,
        min_cardinality=np.array([2, 2]),
        distance_m=np.zeros_like(capacity),
        travel_energy_wh=np.zeros_like(capacity),
    )
    assert result.optimal
    assert result.completed.tolist() == [True, False]
