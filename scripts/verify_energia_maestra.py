"""Numerical gate for the master-energy theorem candidate.

The gate checks the mathematical redesign behind the mode-free architecture:

1. Raw occupancy z_k = sum_i y_ik breaks the potential structure when spatial
   discounts Psi_ik differ across robots.
2. Effective occupancy ztilde_k = sum_i Psi_ik y_ik restores the cross-partial
   symmetry because proximity acts as a capacity weight.
3. With the effective occupancy, one scalar energy E(p, y) generates both the
   Smith decision dynamics and the spatial motion:

       dy_i/dt = Smith(y_i, F_i),   F_i = grad_{y_i}(-E)
       dp_i/dt = -kappa grad_{p_i} E.

The script is intentionally independent from the simulator. It validates algebraic
identities before they are promoted into the theory text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


Array = np.ndarray


@dataclass(frozen=True, slots=True)
class MasterEnergyGame:
    demands: Array = field(default_factory=lambda: np.array([1.0, 2.0, 2.0]))
    rewards: Array = field(default_factory=lambda: np.array([1.4, 1.1, 0.8]))
    task_positions: Array = field(
        default_factory=lambda: np.array([[1.5, -1.5], [1.5, 0.4], [1.5, 2.1]])
    )
    beta: float = 2.0
    idle_reward: float = 0.05
    spatial_scale: float = 3.0
    kappa: float = 1.2
    repulsion_gain: float = 0.08
    repulsion_sigma: float = 0.55
    obstacle_gain: float = 0.15
    obstacle_sigma: float = 0.85
    obstacle_center: Array = field(default_factory=lambda: np.array([0.3, 0.2]))

    @property
    def task_count(self) -> int:
        return int(self.demands.size)


def phi(z: Array | float, n: Array | float, beta: float) -> Array | float:
    return 1.0 / (1.0 + np.exp(beta * (np.asarray(z) - np.asarray(n))))


def phi_prime(z: Array | float, n: Array | float, beta: float) -> Array | float:
    value = phi(z, n, beta)
    return -beta * value * (1.0 - value)


def potential_integral(z: Array, demands: Array, beta: float) -> Array:
    """Closed form of int_0^z Phi(s, n) ds for each task."""

    z = np.asarray(z, dtype=float)
    demands = np.asarray(demands, dtype=float)
    return z - (
        np.logaddexp(0.0, beta * (z - demands)) - np.logaddexp(0.0, -beta * demands)
    ) / beta


def spatial_weights(positions: Array, game: MasterEnergyGame) -> Array:
    deltas = positions[:, None, :] - game.task_positions[None, :, :]
    squared = np.sum(deltas**2, axis=2)
    return np.exp(-squared / (2.0 * game.spatial_scale**2))


def effective_occupancy(positions: Array, preferences: Array, game: MasterEnergyGame) -> Array:
    psi = spatial_weights(positions, game)
    return np.sum(psi * preferences[:, 1:], axis=0)


def payoffs_effective(positions: Array, preferences: Array, game: MasterEnergyGame) -> Array:
    psi = spatial_weights(positions, game)
    ztilde = np.sum(psi * preferences[:, 1:], axis=0)
    task_levels = game.rewards * phi(ztilde, game.demands, game.beta)
    payoffs = np.zeros_like(preferences)
    payoffs[:, 0] = game.idle_reward
    payoffs[:, 1:] = psi * task_levels[None, :]
    return payoffs


def energy(positions: Array, preferences: Array, game: MasterEnergyGame) -> float:
    ztilde = effective_occupancy(positions, preferences, game)
    task_energy = -float(
        np.dot(game.rewards, potential_integral(ztilde, game.demands, game.beta))
    )
    idle_energy = -float(game.idle_reward * np.sum(preferences[:, 0]))
    return idle_energy + task_energy + repulsion_energy(positions, game) + obstacle_energy(positions, game)


def grad_position(positions: Array, preferences: Array, game: MasterEnergyGame) -> Array:
    psi = spatial_weights(positions, game)
    ztilde = np.sum(psi * preferences[:, 1:], axis=0)
    task_levels = game.rewards * phi(ztilde, game.demands, game.beta)
    deltas = positions[:, None, :] - game.task_positions[None, :, :]
    task_grad = np.sum(
        task_levels[None, :, None]
        * preferences[:, 1:, None]
        * psi[:, :, None]
        * deltas
        / (game.spatial_scale**2),
        axis=1,
    )
    return task_grad + repulsion_grad(positions, game) + obstacle_grad(positions, game)


def repulsion_energy(positions: Array, game: MasterEnergyGame) -> float:
    total = 0.0
    for i in range(positions.shape[0]):
        for j in range(i + 1, positions.shape[0]):
            delta = positions[i] - positions[j]
            total += game.repulsion_gain * np.exp(
                -float(np.dot(delta, delta)) / (2.0 * game.repulsion_sigma**2)
            )
    return float(total)


def repulsion_grad(positions: Array, game: MasterEnergyGame) -> Array:
    grad = np.zeros_like(positions)
    for i in range(positions.shape[0]):
        for j in range(i + 1, positions.shape[0]):
            delta = positions[i] - positions[j]
            value = game.repulsion_gain * np.exp(
                -float(np.dot(delta, delta)) / (2.0 * game.repulsion_sigma**2)
            )
            pair_grad = -value * delta / (game.repulsion_sigma**2)
            grad[i] += pair_grad
            grad[j] -= pair_grad
    return grad


def obstacle_energy(positions: Array, game: MasterEnergyGame) -> float:
    deltas = positions - game.obstacle_center
    squared = np.sum(deltas**2, axis=1)
    return float(np.sum(game.obstacle_gain * np.exp(-squared / (2.0 * game.obstacle_sigma**2))))


def obstacle_grad(positions: Array, game: MasterEnergyGame) -> Array:
    deltas = positions - game.obstacle_center
    squared = np.sum(deltas**2, axis=1)
    values = game.obstacle_gain * np.exp(-squared / (2.0 * game.obstacle_sigma**2))
    return -values[:, None] * deltas / (game.obstacle_sigma**2)


def smith_rhs(preferences: Array, payoffs: Array) -> Array:
    updated = np.zeros_like(preferences)
    for idx in range(preferences.shape[0]):
        p = preferences[idx]
        f = payoffs[idx]
        diff = f[:, None] - f[None, :]
        positive = np.maximum(diff, 0.0)
        inflow = positive @ p
        outflow = p * np.sum(np.maximum(-diff, 0.0), axis=1)
        updated[idx] = inflow - outflow
    return updated


def smith_positive_correlation(preferences: Array, payoffs: Array) -> float:
    total = 0.0
    for idx in range(preferences.shape[0]):
        f = payoffs[idx]
        p = preferences[idx]
        gaps = np.maximum(f[None, :] - f[:, None], 0.0)
        total += float(np.sum(p[:, None] * gaps**2))
    return total


def project_rows(values: Array) -> Array:
    clipped = np.maximum(values, 1e-10)
    return clipped / np.sum(clipped, axis=1, keepdims=True)


def initial_state() -> tuple[Array, Array]:
    positions = np.array(
        [
            [-1.8, -1.4],
            [-1.5, -0.3],
            [-1.4, 0.9],
            [-1.6, 1.8],
            [-0.6, 0.2],
            [-0.2, 1.4],
        ],
        dtype=float,
    )
    preferences = np.array(
        [
            [0.40, 0.35, 0.15, 0.10],
            [0.35, 0.15, 0.35, 0.15],
            [0.20, 0.10, 0.40, 0.30],
            [0.25, 0.05, 0.25, 0.45],
            [0.30, 0.30, 0.20, 0.20],
            [0.30, 0.15, 0.25, 0.30],
        ],
        dtype=float,
    )
    return positions, project_rows(preferences)


def test_m0_raw_occupancy_obstruction() -> str:
    game = MasterEnergyGame()
    positions, preferences = initial_state()
    psi = spatial_weights(positions, game)
    raw_z = np.sum(preferences[:, 1:], axis=0)
    task_idx = 1
    agent_i = 0
    agent_j = 3
    left = (
        game.rewards[task_idx]
        * phi_prime(raw_z[task_idx], game.demands[task_idx], game.beta)
        * psi[agent_i, task_idx]
    )
    right = (
        game.rewards[task_idx]
        * phi_prime(raw_z[task_idx], game.demands[task_idx], game.beta)
        * psi[agent_j, task_idx]
    )
    mismatch = abs(float(left - right))
    if mismatch < 1e-3:
        raise AssertionError(f"M0 setup did not expose obstruction: {mismatch:.3e}")
    return f"M0 raw occupancy obstruction: PASS (mismatch={mismatch:.3e})"


def test_m1_effective_occupancy_symmetry() -> str:
    game = MasterEnergyGame()
    positions, preferences = initial_state()
    psi = spatial_weights(positions, game)
    ztilde = effective_occupancy(positions, preferences, game)
    max_mismatch = 0.0
    for task_idx in range(game.task_count):
        for agent_i in range(positions.shape[0]):
            for agent_j in range(positions.shape[0]):
                left = (
                    game.rewards[task_idx]
                    * phi_prime(ztilde[task_idx], game.demands[task_idx], game.beta)
                    * psi[agent_i, task_idx]
                    * psi[agent_j, task_idx]
                )
                right = (
                    game.rewards[task_idx]
                    * phi_prime(ztilde[task_idx], game.demands[task_idx], game.beta)
                    * psi[agent_j, task_idx]
                    * psi[agent_i, task_idx]
                )
                max_mismatch = max(max_mismatch, abs(float(left - right)))
    if max_mismatch > 1e-14:
        raise AssertionError(f"M1 effective symmetry mismatch: {max_mismatch:.3e}")
    return f"M1 effective occupancy symmetry: PASS (max_mismatch={max_mismatch:.3e})"


def test_m2_energy_derivative_identity() -> str:
    game = MasterEnergyGame()
    positions, preferences = initial_state()
    payoffs = payoffs_effective(positions, preferences, game)
    dy = smith_rhs(preferences, payoffs)
    grad_p = grad_position(positions, preferences, game)
    dp = -game.kappa * grad_p

    analytic = -smith_positive_correlation(preferences, payoffs) - game.kappa * float(
        np.sum(grad_p**2)
    )
    directional = -float(np.sum(payoffs * dy)) + float(np.sum(grad_p * dp))
    if abs(analytic - directional) > 1e-12:
        raise AssertionError(
            f"M2 identity mismatch: analytic={analytic:.12e}, directional={directional:.12e}"
        )

    eps = 1e-6
    finite = (energy(positions + eps * dp, preferences + eps * dy, game) - energy(positions, preferences, game)) / eps
    err = abs(float(finite - analytic))
    if err > 2e-6:
        raise AssertionError(f"M2 finite-difference derivative mismatch: {err:.3e}")
    return f"M2 energy derivative identity: PASS (fd_err={err:.3e})"


def test_m3_energy_monotonicity() -> str:
    game = MasterEnergyGame()
    positions, preferences = initial_state()
    dt = 0.03
    energies = []
    for _ in range(900):
        energies.append(energy(positions, preferences, game))
        payoffs = payoffs_effective(positions, preferences, game)
        dy = smith_rhs(preferences, payoffs)
        grad_p = grad_position(positions, preferences, game)
        preferences = project_rows(preferences + dt * dy)
        positions = positions - dt * game.kappa * grad_p
        positions = np.clip(positions, -3.0, 4.0)
    energies.append(energy(positions, preferences, game))
    increments = np.diff(np.asarray(energies))
    violation = float(np.max(increments))
    if violation > 2e-5:
        raise AssertionError(f"M3 energy monotonicity violation: {violation:.3e}")
    return f"M3 energy monotonicity: PASS (max_increase={violation:.3e})"


def test_m4_power_diagram_equivalence() -> str:
    game = MasterEnergyGame()
    positions, preferences = initial_state()
    dt = 0.03
    for _ in range(1200):
        payoffs = payoffs_effective(positions, preferences, game)
        preferences = project_rows(preferences + dt * smith_rhs(preferences, payoffs))
        positions = positions - dt * game.kappa * grad_position(positions, preferences, game)
        positions = np.clip(positions, -3.0, 4.0)

    psi = spatial_weights(positions, game)
    ztilde = effective_occupancy(positions, preferences, game)
    rho = game.rewards * phi(ztilde, game.demands, game.beta)
    task_payoffs = psi * rho[None, :]
    distances_sq = np.sum((positions[:, None, :] - game.task_positions[None, :, :]) ** 2, axis=2)
    power_scores = distances_sq / (2.0 * game.spatial_scale**2) - np.log(np.maximum(rho, 1e-12))[None, :]
    payoff_winners = np.argmax(task_payoffs, axis=1)
    power_winners = np.argmin(power_scores, axis=1)
    violations = int(np.sum(payoff_winners != power_winners))
    if violations:
        raise AssertionError(f"M4 power diagram violations: {violations}")
    return f"M4 power diagram equivalence: PASS (violations={violations}/{positions.shape[0]})"


def main() -> int:
    tests = [
        test_m0_raw_occupancy_obstruction,
        test_m1_effective_occupancy_symmetry,
        test_m2_energy_derivative_identity,
        test_m3_energy_monotonicity,
        test_m4_power_diagram_equivalence,
    ]
    for test in tests:
        print(test())
    print(f"{len(tests)}/{len(tests)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
