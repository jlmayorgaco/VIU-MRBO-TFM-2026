"""Numerical gate for the single-clock primal-dual Smith auction.

This script is independent from the kinematic simulator. It checks the fluid
population model where Smith revision and task prices run on the same clock:

    dx/dt = Smith(x, pi),    pi_k = r_k Phi(N x_k, n_k)
    dr_k/dt = gamma (q_k - N x_k), projected to [0, r_k_max].

The goal is not to replace the proof. The goal is to catch algebraic mistakes
before promoting the single-clock extension into the thesis/paper theory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


Array = np.ndarray


@dataclass(frozen=True)
class SingleClockGame:
    n: Array
    q: Array
    caps: Array
    beta: float
    total: float
    idle_reward: float = 0.05

    @property
    def k(self) -> int:
        return int(self.n.size)


@dataclass(frozen=True)
class IntegratedTrajectory:
    t: Array
    x: Array
    r: Array


def phi(z: Array | float, n: Array | float, beta: float) -> Array | float:
    """Coalition demand sigmoid."""

    return 1.0 / (1.0 + np.exp(beta * (np.asarray(z) - np.asarray(n))))


def smith_rhs_from_payoffs(x: Array, payoffs: Array) -> Array:
    """Continuous-time Smith dynamics on the simplex."""

    diff = payoffs[:, None] - payoffs[None, :]
    positive = np.maximum(diff, 0.0)
    inflow = positive @ x
    outflow = x * np.sum(np.maximum(-diff, 0.0), axis=1)
    return inflow - outflow


def payoffs(x: Array, r: Array, game: SingleClockGame) -> Array:
    """Multiplicative task payoffs under adaptive prices."""

    task_payoffs = r * phi(game.total * x[1:], game.n, game.beta)
    return np.concatenate(([game.idle_reward], task_payoffs))


def single_clock_rhs(
    _: float,
    y: Array,
    game: SingleClockGame,
    gamma: float,
    q_schedule: Callable[[float], Array] | None = None,
) -> Array:
    """Projected single-clock dynamics."""

    x, r = unpack_state(y, game.k)
    q = game.q if q_schedule is None else q_schedule(_)
    dx = smith_rhs_from_payoffs(x, payoffs(x, r, game))
    dr = gamma * (q - game.total * x[1:])
    dr = np.where((r <= 0.0) & (dr < 0.0), 0.0, dr)
    dr = np.where((r >= game.caps) & (dr > 0.0), 0.0, dr)
    return np.concatenate((dx, dr))


def unpack_state(y: Array, k: int) -> tuple[Array, Array]:
    """Return a normalized simplex state and the current price vector."""

    x = np.maximum(np.asarray(y[: k + 1], dtype=float), 0.0)
    total = float(np.sum(x))
    if total <= 0.0:
        x = np.full(k + 1, 1.0 / (k + 1))
    else:
        x = x / total
    r = np.clip(np.asarray(y[k + 1 :], dtype=float), 0.0, np.inf)
    return x, r


def integrate(
    game: SingleClockGame,
    x0: Array,
    r0: Array,
    gamma: float,
    t_end: float,
    q_schedule: Callable[[float], Array] | None = None,
    max_step: float | None = None,
) -> IntegratedTrajectory:
    """Integrate the fluid dynamics and return normalized x and clipped r."""

    y0 = np.concatenate((x0 / np.sum(x0), np.clip(r0, 0.0, game.caps)))
    kwargs = {}
    if max_step is not None:
        kwargs["max_step"] = max_step
    sol = solve_ivp(
        lambda t, y: single_clock_rhs(t, y, game, gamma, q_schedule),
        (0.0, t_end),
        y0,
        rtol=1e-8,
        atol=1e-10,
        method="DOP853",
        **kwargs,
    )
    if not sol.success:
        raise AssertionError(sol.message)
    xs = np.maximum(sol.y[: game.k + 1], 0.0)
    xs = xs / np.sum(xs, axis=0, keepdims=True)
    rs = np.clip(sol.y[game.k + 1 :], 0.0, game.caps[:, None])
    return IntegratedTrajectory(t=sol.t, x=xs, r=rs)


def static_z_of_lambda(lam: float, n: Array, r: Array, beta: float) -> Array:
    """Closed-form static water-filling occupancy for fixed rewards."""

    empty_payoff = r * phi(0.0, n, beta)
    z = np.zeros_like(n, dtype=float)
    active = lam < empty_payoff
    z[active] = n[active] + np.log(r[active] / lam - 1.0) / beta
    return np.maximum(z, 0.0)


def static_water_filling(
    n: Array,
    r: Array,
    beta: float,
    total: float,
    idle_reward: float,
) -> tuple[float, Array, float]:
    """Static water-filling solution used as the saturated limit."""

    z_at_idle = static_z_of_lambda(idle_reward, n, r, beta)
    if float(np.sum(z_at_idle)) <= total:
        return idle_reward, z_at_idle, total - float(np.sum(z_at_idle))

    lo = idle_reward
    hi = float(np.max(r * phi(0.0, n, beta)))
    for _ in range(160):
        mid = 0.5 * (lo + hi)
        demand = float(np.sum(static_z_of_lambda(mid, n, r, beta)))
        if demand > total:
            lo = mid
        else:
            hi = mid
    lam = 0.5 * (lo + hi)
    return lam, static_z_of_lambda(lam, n, r, beta), 0.0


def assert_close(name: str, observed: Array | float, expected: Array | float, tol: float) -> str:
    err = float(np.max(np.abs(np.asarray(observed) - np.asarray(expected))))
    if err > tol:
        raise AssertionError(f"{name}: err={err:.3e} > {tol:.3e}")
    return f"{name}: PASS (err={err:.3e})"


def test_u1_master_identity() -> str:
    """Check the exact cancellation behind the one-clock Lyapunov candidate."""

    game = SingleClockGame(
        n=np.array([1.0, 2.0, 3.0]),
        q=np.array([2.0, 3.0, 4.0]),
        caps=np.array([2.0, 2.0, 2.0]),
        beta=2.0,
        total=12.0,
        idle_reward=0.05,
    )
    gamma = 3.0
    x = np.array([0.31, 0.19, 0.23, 0.27])
    x = x / np.sum(x)
    r = np.array([0.30, 0.60, 0.90])
    ph = phi(game.total * x[1:], game.n, game.beta)
    pi = payoffs(x, r, game)
    dx = smith_rhs_from_payoffs(x, pi)
    dr = gamma * (game.q - game.total * x[1:])
    dphi_dx = -game.beta * game.total * ph * (1.0 - ph)
    dpi_task = dr * ph + r * dphi_dx * dx[1:]
    lhs = float(np.dot(dpi_task, dx[1:]))
    dh = float(np.dot((game.total * x[1:] - game.q) * ph, dx[1:]))
    dissipation = float(np.sum(game.beta * game.total * r * ph * (1.0 - ph) * dx[1:] ** 2))
    rhs = -gamma * dh - dissipation
    return assert_close("U1 master identity", lhs, rhs, 5e-15)


def test_u2_feasible_exact_staffing() -> str:
    game = SingleClockGame(
        n=np.array([1.0, 2.0, 3.0]),
        q=np.array([2.0, 3.0, 4.0]),
        caps=np.array([2.0, 2.0, 2.0]),
        beta=2.0,
        total=12.0,
        idle_reward=0.05,
    )
    result = integrate(
        game,
        x0=np.array([0.85, 0.05, 0.05, 0.05]),
        r0=np.zeros(game.k),
        gamma=1.0,
        t_end=120.0,
    )
    observed_staffing = game.total * result.x[1:, -1]
    expected_prices = game.idle_reward / phi(game.q, game.n, game.beta)
    assert_close("U2 staffing", observed_staffing, game.q, 2e-5)
    return assert_close("U2 closed-form prices", result.r[:, -1], expected_prices, 2e-5)


def test_u3_gain_sweep_no_residual_oscillation() -> str:
    game = SingleClockGame(
        n=np.array([1.0, 2.0, 3.0]),
        q=np.array([2.0, 3.0, 4.0]),
        caps=np.array([2.0, 2.0, 2.0]),
        beta=2.0,
        total=12.0,
        idle_reward=0.05,
    )
    final_errors: list[float] = []
    tail_amplitudes: list[float] = []
    overshoots: list[float] = []
    for gamma in (0.5, 1.0, 3.0, 10.0):
        result = integrate(
            game,
            x0=np.array([0.85, 0.05, 0.05, 0.05]),
            r0=np.zeros(game.k),
            gamma=gamma,
            t_end=120.0,
        )
        occupancy = game.total * result.x[1:]
        final_errors.append(float(np.max(np.abs(occupancy[:, -1] - game.q))))
        tail_amplitudes.append(float(np.max(np.ptp(occupancy[:, -20:], axis=1))))
        overshoots.append(float(np.max(np.maximum(occupancy - game.q[:, None], 0.0))))

    if max(final_errors) > 5e-5:
        raise AssertionError(f"U3 final errors too large: {final_errors}")
    if max(tail_amplitudes) > 2e-3:
        raise AssertionError(f"U3 residual oscillation too large: {tail_amplitudes}")
    if max(overshoots) > 0.6:
        raise AssertionError(f"U3 overshoot too large: {overshoots}")
    return (
        "U3 gain sweep: PASS "
        f"(max_err={max(final_errors):.3e}, "
        f"max_tail={max(tail_amplitudes):.3e}, "
        f"max_overshoot={max(overshoots):.3e})"
    )


def test_u4_infeasible_saturates_to_water_filling() -> str:
    game = SingleClockGame(
        n=np.array([3.0, 3.0, 3.0]),
        q=np.array([4.0, 4.0, 4.0]),
        caps=np.array([1.6, 1.0, 0.35]),
        beta=2.0,
        total=5.0,
        idle_reward=0.01,
    )
    _, expected_staffing, _ = static_water_filling(
        n=game.n,
        r=game.caps,
        beta=game.beta,
        total=game.total,
        idle_reward=game.idle_reward,
    )
    result = integrate(
        game,
        x0=np.array([0.50, 0.20, 0.20, 0.10]),
        r0=np.zeros(game.k),
        gamma=2.0,
        t_end=200.0,
    )
    observed_staffing = game.total * result.x[1:, -1]
    assert_close("U4 saturated prices", result.r[:, -1], game.caps, 1e-5)
    return assert_close("U4 saturated water-filling", observed_staffing, expected_staffing, 1e-5)


def test_u5_birth_event_recruits_without_replanning() -> str:
    birth_time = 40.0
    q_before = np.array([3.0, 0.0])
    q_after = np.array([3.0, 3.0])
    game = SingleClockGame(
        n=np.array([1.0, 2.0]),
        q=q_after,
        caps=np.array([4.0, 2.0]),
        beta=2.0,
        total=8.0,
        idle_reward=0.05,
    )

    def schedule(now: float) -> Array:
        return q_after if now >= birth_time else q_before

    first_price = game.idle_reward / phi(q_before[0], game.n[0], game.beta)
    result = integrate(
        game,
        x0=np.array([5.0 / 8.0, 3.0 / 8.0, 0.0]),
        r0=np.array([first_price, 0.0]),
        gamma=4.0,
        t_end=90.0,
        q_schedule=schedule,
        max_step=0.1,
    )
    occupancy = game.total * result.x[1:]
    post_birth = result.t >= birth_time
    response_indices = np.flatnonzero(post_birth & (occupancy[1] >= 0.95 * q_after[1]))
    response_time = result.t[response_indices[0]] - birth_time if response_indices.size else np.inf
    neighbor_perturbation = float(np.max(np.abs(occupancy[0, post_birth] - q_after[0])))
    final_error = float(np.max(np.abs(occupancy[:, -1] - q_after)))
    if response_time > 2.0:
        raise AssertionError(f"U5 response time too slow: {response_time:.3f}s")
    if neighbor_perturbation > 1.0:
        raise AssertionError(f"U5 perturbation too large: {neighbor_perturbation:.3f}")
    if final_error > 1e-4:
        raise AssertionError(f"U5 final error too large: {final_error:.3e}")
    return (
        "U5 birth event: PASS "
        f"(response={response_time:.3f}s, "
        f"perturb={neighbor_perturbation:.3f}, "
        f"final_err={final_error:.3e})"
    )


def main() -> int:
    tests = [
        test_u1_master_identity,
        test_u2_feasible_exact_staffing,
        test_u3_gain_sweep_no_residual_oscillation,
        test_u4_infeasible_saturates_to_water_filling,
        test_u5_birth_event_recruits_without_replanning,
    ]
    for test in tests:
        print(test())
    print(f"{len(tests)}/{len(tests)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
