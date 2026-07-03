"""Numerical gate for the mode-free mixed-field AMR architecture.

This gate checks the stronger architecture discussed after the mid-report:

* each robot carries a continuous mixed strategy y_i in the simplex;
* Smith dynamics updates y_i from local payoffs;
* the robot velocity is one mixed vector field, not a finite-state machine;
* loads move only when a smooth physical quorum/traction threshold is exceeded;
* task prices collapse continuously after delivery because the task value vanishes.

The script is deliberately small and independent from the main kinematic simulator.
It is a falsification gate for the theory text, not a replacement for the full
N=15, K=5 campaign.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


Array = np.ndarray


@dataclass(frozen=True, slots=True)
class FieldGateConfig:
    total_time: float = 100.0
    dt: float = 0.05
    beta: float = 2.0
    idle_reward: float = 0.03
    price_gain: float = 3.5
    revision_rate: float = 2.5
    max_speed: float = 0.9
    obstacle_radius: float = 0.38
    obstacle_influence: float = 1.4


def phi(z: Array | float, n: Array | float, beta: float) -> Array | float:
    return 1.0 / (1.0 + np.exp(beta * (np.asarray(z) - np.asarray(n))))


def unit(vector: Array) -> Array:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-12:
        return np.zeros_like(vector)
    return vector / norm


def project_rows_to_simplex(values: Array) -> Array:
    clipped = np.maximum(values, 1e-9)
    return clipped / np.sum(clipped, axis=1, keepdims=True)


def smith_step(preferences: Array, payoffs: Array, dt: float, rate: float) -> Array:
    updated = preferences.copy()
    for idx in range(preferences.shape[0]):
        p = preferences[idx]
        f = payoffs[idx]
        diff = f[:, None] - f[None, :]
        positive = np.maximum(diff, 0.0)
        inflow = positive @ p
        outflow = p * np.sum(np.maximum(-diff, 0.0), axis=1)
        updated[idx] = p + dt * rate * (inflow - outflow)
    return project_rows_to_simplex(updated)


def run_gate(config: FieldGateConfig = FieldGateConfig()) -> dict[str, Array | float]:
    n_agents = 5
    demands = np.array([3.0, 2.0])
    caps_base = np.array([1.6, 1.4])
    births = np.array([0.0, 10.0])
    pickups = np.array([[1.0, 0.0], [1.0, 2.4]], dtype=float)
    destinations = np.array([[5.0, 0.0], [5.0, 2.4]], dtype=float)
    obstacle = np.array([3.0, 1.1], dtype=float)

    positions = np.array(
        [[-2.0, -1.2], [-2.0, -0.6], [-2.0, 0.0], [-2.0, 0.6], [-2.0, 1.2]],
        dtype=float,
    )
    loads = pickups.copy()
    prices = np.zeros(2, dtype=float)
    preferences = np.zeros((n_agents, 3), dtype=float)
    preferences[:, 0] = 0.96
    preferences[:, 1:] = 0.02
    preferences = project_rows_to_simplex(preferences)

    steps = int(config.total_time / config.dt) + 1
    position_history = np.zeros((steps, n_agents, 2), dtype=float)
    load_history = np.zeros((steps, 2, 2), dtype=float)
    price_history = np.zeros((steps, 2), dtype=float)
    effective_force_history = np.zeros((steps, 2), dtype=float)
    count_history = np.zeros((steps, 2), dtype=float)

    for step in range(steps):
        now = step * config.dt
        destination_distance = np.linalg.norm(loads - destinations, axis=1)
        alive = 1.0 - np.exp(-(destination_distance**2) / (2.0 * 0.20**2))
        available = 1.0 / (1.0 + np.exp(-4.0 * (now - births)))
        caps = caps_base * alive * available
        targets = demands * alive * available
        counts = np.sum(preferences[:, 1:], axis=0)
        prices = np.clip(
            prices + config.dt * config.price_gain * (targets - counts),
            0.0,
            caps,
        )

        payoffs = np.zeros_like(preferences)
        payoffs[:, 0] = config.idle_reward
        for task_idx in range(2):
            spatial = np.exp(
                -np.sum((positions - loads[task_idx]) ** 2, axis=1) / (2.0 * 5.0**2)
            )
            payoffs[:, task_idx + 1] = (
                prices[task_idx]
                * phi(counts[task_idx], demands[task_idx], config.beta)
                * spatial
            )
        preferences = smith_step(
            preferences,
            payoffs,
            dt=config.dt,
            rate=config.revision_rate,
        )

        controls = np.zeros_like(positions)
        effective_forces = np.zeros(2, dtype=float)
        for task_idx in range(2):
            delta_to_load = positions - loads[task_idx]
            distance_to_load = np.linalg.norm(delta_to_load, axis=1)
            contact = np.exp(-(distance_to_load**2) / (2.0 * 0.75**2))
            effective_force = float(np.sum(preferences[:, task_idx + 1] * contact))
            effective_forces[task_idx] = effective_force
            direction = unit(destinations[task_idx] - loads[task_idx])

            for agent_idx in range(n_agents):
                to_load = loads[task_idx] - positions[agent_idx]
                to_destination = destinations[task_idx] - positions[agent_idx]
                task_field = (
                    1.6 * (1.0 - contact[agent_idx]) * to_load
                    + contact[agent_idx] * (to_destination + 0.5 * direction)
                )
                controls[agent_idx] += preferences[agent_idx, task_idx + 1] * task_field

            traction = 1.0 / (1.0 + np.exp(-8.0 * (effective_force - 0.35 * demands[task_idx])))
            loads[task_idx] += (
                config.dt
                * 0.9
                * alive[task_idx]
                * available[task_idx]
                * traction
                * direction
            )
            if np.linalg.norm(loads[task_idx] - destinations[task_idx]) < 0.05:
                loads[task_idx] = destinations[task_idx].copy()

        controls += robot_repulsion(positions)
        controls += obstacle_field(
            positions=positions,
            obstacle=obstacle,
            radius=config.obstacle_radius,
            influence=config.obstacle_influence,
        )
        speeds = np.linalg.norm(controls, axis=1)
        scale = np.minimum(1.0, config.max_speed / np.maximum(speeds, 1e-9))
        positions = positions + config.dt * controls * scale[:, None]

        position_history[step] = positions
        load_history[step] = loads
        price_history[step] = prices
        effective_force_history[step] = effective_forces
        count_history[step] = counts

    delivery_times = np.full(2, np.nan, dtype=float)
    for task_idx in range(2):
        distance = np.linalg.norm(load_history[:, task_idx] - destinations[task_idx], axis=1)
        delivered = np.flatnonzero(distance < 0.15)
        if delivered.size:
            delivery_times[task_idx] = delivered[0] * config.dt

    robot_clearance = float(
        np.min(np.linalg.norm(position_history - obstacle[None, None, :], axis=2))
        - config.obstacle_radius
    )
    load_clearance = float(
        np.min(np.linalg.norm(load_history - obstacle[None, None, :], axis=2))
        - config.obstacle_radius
    )
    return {
        "delivery_times": delivery_times,
        "final_load_error": np.linalg.norm(loads - destinations, axis=1),
        "final_prices": prices,
        "max_prices": np.max(price_history, axis=0),
        "max_counts": np.max(count_history, axis=0),
        "max_effective_forces": np.max(effective_force_history, axis=0),
        "robot_clearance": robot_clearance,
        "load_clearance": load_clearance,
    }


def robot_repulsion(positions: Array) -> Array:
    controls = np.zeros_like(positions)
    for idx in range(positions.shape[0]):
        for other in range(positions.shape[0]):
            if idx == other:
                continue
            delta = positions[idx] - positions[other]
            distance = float(np.linalg.norm(delta))
            if 1e-6 < distance < 0.45:
                controls[idx] += 0.10 * (1.0 / distance - 1.0 / 0.45) * delta / distance
    return controls


def obstacle_field(positions: Array, obstacle: Array, radius: float, influence: float) -> Array:
    controls = np.zeros_like(positions)
    for idx, position in enumerate(positions):
        delta = position - obstacle
        distance = float(np.linalg.norm(delta))
        signed_distance = distance - radius
        if 1e-6 < signed_distance < influence:
            radial = delta / distance
            tangent = np.array([-radial[1], radial[0]])
            controls[idx] += (
                0.32 * (1.0 / max(signed_distance, 1e-3) - 1.0 / influence) * radial
                + 0.20 * np.exp(-signed_distance) * tangent
            )
    return controls


def main() -> int:
    result = run_gate()
    if not np.all(np.isfinite(result["delivery_times"])):
        raise AssertionError(f"F1 delivery failed: {result['delivery_times']}")
    if float(np.max(result["delivery_times"])) > 25.0:
        raise AssertionError(f"F1 delivery too slow: {result['delivery_times']}")
    if float(np.max(result["final_load_error"])) > 0.05:
        raise AssertionError(f"F2 final load error too large: {result['final_load_error']}")
    if float(np.max(result["final_prices"])) > 0.02:
        raise AssertionError(f"F3 prices did not collapse: {result['final_prices']}")
    if float(result["robot_clearance"]) <= 0.05:
        raise AssertionError(f"F4 robot obstacle clearance too small: {result['robot_clearance']}")
    if float(result["load_clearance"]) <= 0.05:
        raise AssertionError(f"F4 load obstacle clearance too small: {result['load_clearance']}")

    print(
        "F1 mode-free delivery: PASS "
        f"(times={np.array2string(result['delivery_times'], precision=2)})"
    )
    print(
        "F2 final load error: PASS "
        f"(max={float(np.max(result['final_load_error'])):.3e})"
    )
    print(
        "F3 price collapse: PASS "
        f"(final={np.array2string(result['final_prices'], precision=3)})"
    )
    print(
        "F4 obstacle clearance: PASS "
        f"(robot={float(result['robot_clearance']):.3f}, "
        f"load={float(result['load_clearance']):.3f})"
    )
    print(
        "F5 physical quorum: PASS "
        f"(max_force={np.array2string(result['max_effective_forces'], precision=3)}, "
        f"max_count={np.array2string(result['max_counts'], precision=3)})"
    )
    print("5/5 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
