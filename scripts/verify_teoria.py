"""Numerical checks for the scarcity/water-filling theory draft.

This script is intentionally independent from the simulator. It validates the
fluid population-game claims before they are promoted into the thesis text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize


Array = np.ndarray


@dataclass(frozen=True)
class Game:
    n: Array
    r: Array
    beta: float
    total: float
    r0: float = 0.01

    @property
    def k(self) -> int:
        return int(self.n.size)


def phi(z: Array | float, n: Array | float, beta: float) -> Array | float:
    arg = beta * (np.asarray(z) - np.asarray(n))
    return 1.0 / (1.0 + np.exp(arg))


def z_of_lambda(lam: float, game: Game) -> Array:
    empty_payoff = game.r * phi(0.0, game.n, game.beta)
    z = np.zeros(game.k)
    active = lam < empty_payoff
    z[active] = game.n[active] + np.log(game.r[active] / lam - 1.0) / game.beta
    return np.maximum(z, 0.0)


def water_filling(game: Game) -> tuple[float, Array, float]:
    z_at_idle = z_of_lambda(game.r0, game)
    if float(np.sum(z_at_idle)) <= game.total:
        idle = game.total - float(np.sum(z_at_idle))
        return game.r0, z_at_idle, idle

    lo = game.r0
    hi = float(np.max(game.r * phi(0.0, game.n, game.beta)))
    for _ in range(160):
        mid = 0.5 * (lo + hi)
        demand = float(np.sum(z_of_lambda(mid, game)))
        if demand > game.total:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    return lam, z_of_lambda(lam, game), 0.0


def potential_integral(x_task: Array, game: Game) -> Array:
    arg = game.beta * (game.total * x_task - game.n)
    base = -game.beta * game.n
    return x_task - (np.logaddexp(0.0, arg) - np.logaddexp(0.0, base)) / (
        game.beta * game.total
    )


def potential(x: Array, game: Game) -> float:
    return float(game.r0 * x[0] + np.dot(game.r, potential_integral(x[1:], game)))


def payoffs(x: Array, game: Game) -> Array:
    f = np.empty(game.k + 1)
    f[0] = game.r0
    f[1:] = game.r * phi(game.total * x[1:], game.n, game.beta)
    return f


def smith_rhs_from_payoffs(x: Array, f: Array, rate: float = 1.0) -> Array:
    diff = f[:, None] - f[None, :]
    positive = np.maximum(diff, 0.0)
    inflow = positive @ x
    outflow = x * np.sum(np.maximum(-diff, 0.0), axis=1)
    return rate * (inflow - outflow)


def smith_rhs(_: float, x: Array, game: Game) -> Array:
    return smith_rhs_from_payoffs(x, payoffs(x, game))


def integrate_simplex(rhs: Callable[[float, Array], Array], x0: Array, t_end: float = 120.0) -> Array:
    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        x0,
        rtol=1e-9,
        atol=1e-11,
        method="DOP853",
    )
    if not sol.success:
        raise AssertionError(sol.message)
    x = np.maximum(sol.y[:, -1], 0.0)
    return x / np.sum(x)


def integrate_state(rhs: Callable[[float, Array], Array], y0: Array, t_end: float = 120.0) -> Array:
    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        y0,
        rtol=1e-9,
        atol=1e-11,
        method="DOP853",
    )
    if not sol.success:
        raise AssertionError(sol.message)
    return np.maximum(sol.y[:, -1], 0.0)


def x_star(game: Game) -> Array:
    _, z, idle = water_filling(game)
    x = np.zeros(game.k + 1)
    x[0] = idle / game.total
    x[1:] = z / game.total
    return x


def assert_close(name: str, observed: Array | float, expected: Array | float, tol: float) -> str:
    err = float(np.max(np.abs(np.asarray(observed) - np.asarray(expected))))
    if err > tol:
        raise AssertionError(f"{name}: err={err:.3e} > {tol:.3e}")
    return f"{name}: PASS (err={err:.3e})"


def test_t1_closed_form_matches_slsqp() -> str:
    game = Game(n=np.array([2.0, 3.0, 4.0, 5.0]), r=np.array([1.4, 1.2, 1.0, 0.8]), beta=1.7, total=9.0)
    expected = x_star(game)

    cons = {"type": "eq", "fun": lambda x: np.sum(x) - 1.0}
    res = minimize(
        lambda x: -potential(x, game),
        x0=np.full(game.k + 1, 1.0 / (game.k + 1)),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * (game.k + 1),
        constraints=[cons],
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    if not res.success:
        raise AssertionError(res.message)
    return assert_close("T1 closed form vs SLSQP", res.x, expected, 2e-7)


def test_t2_uniform_deficit() -> str:
    game = Game(n=np.array([3.0, 5.0, 8.0]), r=np.ones(3), beta=2.0, total=10.0)
    lam, z, idle = water_filling(game)
    d = z - game.n
    expected_d = np.full(3, (game.total - np.sum(game.n)) / game.k)
    expected_lam = 1.0 / (1.0 + np.exp(game.beta * expected_d[0]))
    assert_close("T2 uniform deficit", d, expected_d, 1e-12)
    assert_close("T2 lambda", lam, expected_lam, 1e-12)
    return assert_close("T2 idle", idle, 0.0, 1e-12)


def test_t3_rigid_limit_moves_toward_greedy() -> str:
    target = np.array([3.0, 2.0, 0.0])
    errors: list[float] = []
    for beta in (10.0, 20.0):
        game = Game(n=np.array([3.0, 3.0, 3.0]), r=np.array([3.0, 2.0, 1.0]), beta=beta, total=5.0)
        _, z, _ = water_filling(game)
        errors.append(float(np.linalg.norm(z - target, ord=np.inf)))
    if not errors[1] < errors[0] < 0.12:
        raise AssertionError(f"T3 errors did not shrink as expected: {errors}")
    return f"T3 rigid limit: PASS (err beta10={errors[0]:.3e}, beta20={errors[1]:.3e})"


def test_t4_static_comparative_derivative() -> str:
    game = Game(n=np.array([2.0, 3.0, 5.0]), r=np.array([1.8, 1.2, 0.9]), beta=1.3, total=8.0)
    lam, _, _ = water_filling(game)
    weights_den = np.sum(game.r / (game.r - lam))
    analytic = -game.beta * lam / weights_den

    eps = 1e-5
    lam_plus = water_filling(Game(game.n, game.r, game.beta, game.total + eps, game.r0))[0]
    lam_minus = water_filling(Game(game.n, game.r, game.beta, game.total - eps, game.r0))[0]
    finite = (lam_plus - lam_minus) / (2 * eps)
    return assert_close("T4 d lambda / dN", finite, analytic, 1e-6)


def test_t5_smith_global_with_abandoned_task() -> str:
    game = Game(n=np.array([2.0, 3.0, 4.0]), r=np.array([1.6, 1.2, 0.15]), beta=2.0, total=6.0)
    expected = x_star(game)
    if expected[-1] > 1e-10:
        raise AssertionError(f"T5 setup error: last task is active in {expected}")

    starts = [
        np.array([0.05, 0.30, 0.45, 0.20]),
        np.array([0.00, 0.70, 0.10, 0.20]),
        np.array([0.20, 0.10, 0.10, 0.60]),
    ]
    errors = []
    for x0 in starts:
        x = integrate_simplex(lambda t, y: smith_rhs(t, y, game), x0 / np.sum(x0), t_end=220.0)
        errors.append(float(np.linalg.norm(x - expected, ord=np.inf)))
    if max(errors) > 2e-6:
        raise AssertionError(f"T5 convergence errors too large: {errors}")
    return f"T5 Smith global/frontier: PASS (max_err={max(errors):.3e})"


def test_t6_heterogeneous_revision_rates() -> str:
    game = Game(n=np.array([2.0, 3.0]), r=np.array([1.4, 1.0]), beta=1.8, total=5.0)
    expected = x_star(game)
    alpha = np.array([0.55, 0.45])
    rates = np.array([1.0, 0.15])
    y0 = np.array(
        [
            [0.05, 0.75, 0.20],
            [0.10, 0.10, 0.80],
        ]
    ).reshape(-1)

    def rhs(_: float, y: Array) -> Array:
        groups = y.reshape(2, game.k + 1)
        agg = alpha @ groups
        f = payoffs(agg, game)
        dy = np.vstack([smith_rhs_from_payoffs(groups[i], f, rates[i]) for i in range(2)])
        return dy.reshape(-1)

    y = integrate_state(rhs, y0, t_end=220.0).reshape(2, game.k + 1)
    y = np.vstack([row / np.sum(row) for row in y])
    observed = alpha @ y
    return assert_close("T6 heterogeneous rates", observed, expected, 2e-5)


def test_t7_capacity_heterogeneous_aggregate() -> str:
    capacities = np.array([1.0, 3.0])
    class_masses = np.array([6.0, 3.0])
    total_capacity = float(np.dot(capacities, class_masses))
    game = Game(n=np.array([5.0, 7.0]), r=np.array([1.5, 1.2]), beta=1.4, total=total_capacity)
    _, expected_c, _ = water_filling(game)
    y0 = np.array(
        [
            [0.10, 0.80, 0.10],
            [0.20, 0.10, 0.70],
        ]
    ).reshape(-1)

    def rhs(_: float, y: Array) -> Array:
        groups = y.reshape(2, game.k + 1)
        task_capacity = capacities @ (class_masses[:, None] * groups[:, 1:])
        f_tasks = game.r * phi(task_capacity, game.n, game.beta)
        dy_rows = []
        for row in groups:
            f = np.concatenate(([game.r0], f_tasks))
            dy_rows.append(smith_rhs_from_payoffs(row, f))
        return np.vstack(dy_rows).reshape(-1)

    y = integrate_state(rhs, y0, t_end=400.0).reshape(2, game.k + 1)
    y = np.vstack([row / np.sum(row) for row in y])
    observed_c = capacities @ (class_masses[:, None] * y[:, 1:])
    return assert_close("T7 heterogeneous capacity aggregate", observed_c, expected_c, 2e-5)


def test_t8_idle_reward_integer_slack_rule() -> str:
    n = np.array([1.0, 2.0, 4.0])
    r = np.array([1.5, 1.2, 1.0])
    beta = 2.0
    r0 = float(np.min(r) / (1.0 + np.exp(beta)))
    game = Game(n=n, r=r, beta=beta, total=20.0, r0=r0)
    _, z, idle = water_filling(game)
    if idle <= 0:
        raise AssertionError("T8 setup error: abundance expected")
    return assert_close("T8 integer slack rule", np.min(z - n), 1.0, 1e-12)


def test_t9_scenario_b_prediction() -> str:
    game = Game(n=np.array([1.0, 3.0]), r=np.ones(2), beta=2.0, total=6.0)
    lam, z, idle = water_filling(game)
    assert_close("T9 z", z, np.array([2.0, 4.0]), 1e-12)
    assert_close("T9 lambda", lam, 1.0 / (1.0 + np.exp(2.0)), 1e-12)
    return assert_close("T9 idle", idle, 0.0, 1e-12)


def main() -> int:
    tests = [
        test_t1_closed_form_matches_slsqp,
        test_t2_uniform_deficit,
        test_t3_rigid_limit_moves_toward_greedy,
        test_t4_static_comparative_derivative,
        test_t5_smith_global_with_abandoned_task,
        test_t6_heterogeneous_revision_rates,
        test_t7_capacity_heterogeneous_aggregate,
        test_t8_idle_reward_integer_slack_rule,
        test_t9_scenario_b_prediction,
    ]
    for test in tests:
        print(test())
    print(f"{len(tests)}/{len(tests)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
