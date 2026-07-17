from __future__ import annotations

import numpy as np

from viu_mrob_tfm.sp6.experiment import audit_world_theory, generate_world, run_sp6_config, simulate_method
from viu_mrob_tfm.sp6.theory import (
    asynchronous_better_response,
    exact_feasible_oracle,
    is_feasible,
    is_inclusion_minimal,
    is_pure_nash,
    marginal_utility,
    potential,
    pure_nash_profiles,
    sufficient_penalty,
    unbounded_efficiency_example,
)


def test_wonderful_life_utility_is_an_exact_potential() -> None:
    capabilities = np.asarray([[0.7, 0.1], [0.2, 0.8], [0.5, 0.5]])
    requirement = np.asarray([0.8, 0.8])
    costs = np.asarray([0.3, 0.4, 0.5])
    penalty, _ = sufficient_penalty(capabilities, requirement, costs)
    for encoded in range(8):
        profile = np.asarray([(encoded >> idx) & 1 for idx in range(3)], dtype=int)
        for robot in range(3):
            deviated = profile.copy()
            deviated[robot] = 1 - deviated[robot]
            utility_delta = marginal_utility(robot, int(deviated[robot]), profile, capabilities, requirement, costs, penalty) - marginal_utility(
                robot, int(profile[robot]), profile, capabilities, requirement, costs, penalty
            )
            phi_delta = potential(deviated, capabilities, requirement, costs, penalty) - potential(
                profile, capabilities, requirement, costs, penalty
            )
            assert np.isclose(utility_delta, phi_delta)


def test_penalty_threshold_makes_every_equilibrium_feasible_and_minimal() -> None:
    world = generate_world("complementary_recoverable", 6, 8604)
    penalty, delta_min = sufficient_penalty(world.capabilities, world.requirement, world.costs)
    assert delta_min > 0.0
    equilibria = pure_nash_profiles(world.capabilities, world.requirement, world.costs, penalty)
    assert equilibria
    assert all(is_feasible(profile, world.capabilities, world.requirement) for profile in equilibria)
    assert all(is_inclusion_minimal(profile, world.capabilities, world.requirement) for profile in equilibria)


def test_equilibria_equal_all_inclusion_minimal_feasible_coalitions() -> None:
    world = generate_world("complementary_recoverable", 6, 8604)
    penalty, delta_min = sufficient_penalty(world.capabilities, world.requirement, world.costs)
    assert penalty > float(np.max(world.costs)) / delta_min
    equilibria = {
        tuple(profile)
        for profile in pure_nash_profiles(
            world.capabilities, world.requirement, world.costs, penalty
        )
    }
    minimal = set()
    for encoded in range(2**world.reserve_size):
        profile = np.asarray(
            [(encoded >> idx) & 1 for idx in range(world.reserve_size)], dtype=int
        )
        if is_inclusion_minimal(profile, world.capabilities, world.requirement):
            minimal.add(tuple(profile))
    assert equilibria == minimal


def test_asynchronous_better_response_terminates_at_nash() -> None:
    world = generate_world("balanced_recoverable", 8, 8611)
    penalty, _ = sufficient_penalty(world.capabilities, world.requirement, world.costs)
    result = asynchronous_better_response(world.capabilities, world.requirement, world.costs, penalty, seed=3)
    assert np.all(np.diff(result.potential_trace) > 0.0)
    assert result.strict_moves <= 2**world.reserve_size - 1
    assert is_pure_nash(result.profile, world.capabilities, world.requirement, world.costs, penalty)
    assert is_feasible(result.profile, world.capabilities, world.requirement)


def test_no_uniform_efficiency_bound_counterexample() -> None:
    capabilities, requirement, costs, penalty, expensive, cheap = unbounded_efficiency_example(100.0)
    assert is_pure_nash(expensive, capabilities, requirement, costs, penalty)
    assert is_pure_nash(cheap, capabilities, requirement, costs, penalty)
    oracle = exact_feasible_oracle(capabilities, requirement, costs)
    assert np.array_equal(oracle, cheap)
    assert float(expensive @ costs) / float(oracle @ costs) == 50.0


def test_world_audit_and_impossibility_guard() -> None:
    feasible = generate_world("balanced_recoverable", 4, 8600)
    theory = audit_world_theory(feasible)
    assert theory["exact_potential_verified"]
    result = simulate_method(feasible, "guarded_potential", float(exact_feasible_oracle(feasible.capabilities, feasible.requirement, feasible.costs) @ feasible.costs), theory)
    assert result["certificate_restored"]
    assert result["final_pure_nash"]

    impossible = generate_world("infeasible_reserve", 4, 8600)
    impossible_theory = audit_world_theory(impossible)
    impossible_result = simulate_method(impossible, "guarded_potential", float("nan"), impossible_theory)
    assert impossible_result["declares_impossible"]
    assert not impossible_result["certificate_restored"]


def test_smoke_campaign_writes_a_passed_audit(tmp_path) -> None:
    config = tmp_path / "sp6.yaml"
    config.write_text(
        "\n".join(
            [
                "experiment_id: test_sp6",
                "protocol_family: sp6_potential_recovery_v1",
                f"output_dir: {str(tmp_path / 'out').replace(chr(92), '/')}",
                "scenarios: [balanced_recoverable, infeasible_reserve]",
                "reserve_sizes: [4]",
                "seeds: [8600]",
                "methods: [guarded_potential, marginal_auction, distance_greedy, no_repair, central_exact]",
            ]
        ),
        encoding="utf-8",
    )
    manifest = run_sp6_config(config)
    assert manifest["runs"] == 10
    audit = (tmp_path / "out" / "audit.json").read_text(encoding="utf-8")
    assert '"status": "passed"' in audit
