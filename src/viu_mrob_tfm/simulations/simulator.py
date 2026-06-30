"""Incremental kinematic simulator for distributed coalition transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linear_sum_assignment

from viu_mrob_tfm.controllers.base import BaseController
from viu_mrob_tfm.controllers.treatments import TreatmentPolicy, resolve_treatment
from viu_mrob_tfm.domain.state import SystemState
from viu_mrob_tfm.estimators.base import BaseEstimator
from viu_mrob_tfm.simulations.scenario import SimulationScenario


Array = NDArray[np.float64]


MODE_RECRUITING = 0
MODE_TRANSPORT = 1
MODE_DELIVERED = 2


@dataclass(slots=True)
class Simulator:
    """Run a minimal closed-loop decision-motion-transport simulation.

    The simulator intentionally stays kinematic: it validates the assignment,
    recruitment, formation, obstacle-reaction, and task-mode logic without claiming
    contact-force realism for the transported load.
    """

    scenario: SimulationScenario
    controller: BaseController
    estimator: BaseEstimator | None = None

    def initial_state(self) -> SystemState:
        """Construct the initial system state from the scenario."""

        return SystemState(
            agv_states=[agv.state for agv in self.scenario.agvs],
            load_state=self.scenario.transported_load.state,
            time=0.0,
        )

    def run(self) -> dict[str, Any]:
        """Run the kinematic closed loop and return trajectories and diagnostics."""

        steps = max(1, int(self.scenario.duration / self.scenario.time_step) + 1)
        time = np.linspace(0.0, self.scenario.duration, steps)
        state = self.initial_state()
        initial_control = self.controller.compute_control(state)
        if self.estimator is not None:
            self.estimator.update(state)

        n_agents = len(self.scenario.agvs)
        tasks = self.scenario.tasks
        n_tasks = len(tasks)
        if n_tasks == 0:
            raise ValueError("SimulationScenario requires at least one task.")

        params = _SimulationParams.from_controller(self.controller)
        policy = _resolve_controller_policy(self.controller)
        positions = np.vstack([agv.state.position for agv in self.scenario.agvs]).astype(float)
        headings = np.array([agv.state.heading for agv in self.scenario.agvs], dtype=float)
        load_positions = np.vstack([task.pickup for task in tasks]).astype(float)
        destinations = np.vstack([task.destination for task in tasks]).astype(float)
        demands = np.array([task.min_coalition_size for task in tasks], dtype=int)
        reward_caps = np.array([task.reward for task in tasks], dtype=float)
        rewards = reward_caps.copy()
        if policy.uses_adaptive_prices:
            rewards = np.full_like(reward_caps, params.initial_price)

        preferences = _initial_preferences(positions, load_positions)
        assignments = np.argmax(preferences, axis=1).astype(int)
        previous_y = _assignment_indicators(assignments, n_tasks)
        xhat = np.full_like(previous_y, 1.0 / (n_tasks + 1))
        active = np.ones(n_agents, dtype=bool)

        task_modes = np.zeros(n_tasks, dtype=int)
        enough_counts = np.zeros(n_tasks, dtype=int)
        deficit_counts = np.zeros(n_tasks, dtype=int)
        coalition_times = np.full(n_tasks, np.nan, dtype=float)
        completion_times = np.full(n_tasks, np.nan, dtype=float)
        applied_failures: set[tuple[float, int]] = set()

        trajectory = np.zeros((steps, n_agents, 2), dtype=float)
        heading_history = np.zeros((steps, n_agents), dtype=float)
        control_history = np.zeros((steps, n_agents, 2), dtype=float)
        assignment_history = np.zeros((steps, n_agents), dtype=int)
        preference_history = np.zeros((steps, n_agents, n_tasks + 1), dtype=float)
        xhat_history = np.zeros((steps, n_agents, n_tasks + 1), dtype=float)
        load_history = np.zeros((steps, n_tasks, 2), dtype=float)
        mode_history = np.zeros((steps, n_tasks), dtype=int)
        feasible_history = np.zeros((steps, n_tasks), dtype=bool)
        active_history = np.zeros((steps, n_agents), dtype=bool)
        reward_history = np.zeros((steps, n_tasks), dtype=float)

        for step_idx, now in enumerate(time):
            _apply_failure_events(
                now=now,
                active=active,
                assignments=assignments,
                preferences=preferences,
                xhat=xhat,
                previous_y=previous_y,
                events=self.scenario.failure_events,
                applied=applied_failures,
            )

            graph = _adjacency_from_positions(
                positions=positions,
                active=active,
                fallback=self.scenario.graph.adjacency,
                communication_range=self.scenario.communication_range,
            )
            payoffs = _compute_payoffs(
                positions=positions,
                xhat=xhat,
                load_positions=load_positions,
                task_modes=task_modes,
                rewards=rewards,
                demands=demands,
                active=active,
                params=params,
                use_spatial=policy.uses_spatial_payoff,
            )

            if policy.assignment == "centralized":
                assignments = _centralized_assignments(
                    positions=positions,
                    active=active,
                    load_positions=load_positions,
                    destinations=destinations,
                    task_modes=task_modes,
                    demands=demands,
                )
                preferences = _preferences_from_assignments(assignments, n_tasks)
            elif policy.assignment in {"greedy_local", "greedy_dac"}:
                assignments = _greedy_assignments(
                    positions=positions,
                    assignments=assignments,
                    xhat=xhat,
                    active=active,
                    load_positions=load_positions,
                    task_modes=task_modes,
                    demands=demands,
                    rewards=rewards,
                    use_dac=policy.assignment == "greedy_dac",
                )
                preferences = _preferences_from_assignments(assignments, n_tasks)
            else:
                rates = _revision_rates(
                    positions=positions,
                    assignments=assignments,
                    load_positions=load_positions,
                    active=active,
                    params=params,
                    modulated=policy.uses_modulated_rate,
                )
                preferences = _preference_dynamics_step(
                    preferences=preferences,
                    payoffs=payoffs,
                    rates=rates,
                    dt=self.scenario.time_step,
                    active=active,
                    policy=policy,
                )
                assignments = _update_assignments(
                    assignments=assignments,
                    preferences=preferences,
                    active=active,
                    hysteresis=params.hysteresis,
                )
            assignments = _release_delivered_assignments(assignments, task_modes)
            preferences = _release_delivered_preferences(preferences, task_modes)

            y = _assignment_indicators(assignments, n_tasks)
            if policy.uses_dac:
                xhat = _dac_step(
                    xhat=xhat,
                    y=y,
                    previous_y=previous_y,
                    adjacency=graph,
                    gain=params.consensus_gain,
                    active=active,
                )
            else:
                xhat = y.copy()
            previous_y = y

            if policy.uses_adaptive_prices:
                rewards = _adaptive_price_step(
                    prices=rewards,
                    caps=reward_caps,
                    xhat=xhat,
                    active=active,
                    task_modes=task_modes,
                    demands=demands,
                    params=params,
                    dt=self.scenario.time_step,
                )

            coalition_present = _coalition_presence(
                positions=positions,
                load_positions=load_positions,
                assignments=assignments,
                active=active,
                detection_radius=self.scenario.detection_radius,
                n_tasks=n_tasks,
            )
            newly_feasible = (coalition_present >= demands) & np.isnan(coalition_times)
            coalition_times[newly_feasible] = now
            _update_task_modes(
                task_modes=task_modes,
                enough_counts=enough_counts,
                deficit_counts=deficit_counts,
                coalition_present=coalition_present,
                demands=demands,
                threshold=self.scenario.transport_threshold_steps,
            )

            controls = _navigation_controls(
                positions=positions,
                assignments=assignments,
                active=active,
                load_positions=load_positions,
                destinations=destinations,
                task_modes=task_modes,
                demands=demands,
                obstacles=self.scenario.obstacles,
                params=params,
            )
            positions, headings, applied_controls = _integrate_unicycle(
                positions=positions,
                headings=headings,
                desired_velocity=controls,
                active=active,
                dt=self.scenario.time_step,
                vmax=params.max_speed,
                omega_max=params.max_angular_speed,
            )
            _update_load_positions(
                load_positions=load_positions,
                positions=positions,
                assignments=assignments,
                active=active,
                task_modes=task_modes,
                destinations=destinations,
                completion_times=completion_times,
                now=now,
                detection_radius=self.scenario.detection_radius,
            )

            trajectory[step_idx] = positions
            heading_history[step_idx] = headings
            control_history[step_idx] = applied_controls
            assignment_history[step_idx] = assignments
            preference_history[step_idx] = preferences
            xhat_history[step_idx] = xhat
            load_history[step_idx] = load_positions
            mode_history[step_idx] = task_modes
            feasible_history[step_idx] = coalition_present >= demands
            active_history[step_idx] = active
            reward_history[step_idx] = rewards

        if n_tasks == 1:
            self.scenario.transported_load.state.position = load_positions[0].copy()

        return {
            "time": time,
            "control": initial_control,
            "controls": control_history,
            "trajectory": trajectory,
            "headings": heading_history,
            "assignments": assignment_history,
            "preferences": preference_history,
            "xhat": xhat_history,
            "task_modes": mode_history,
            "task_feasible": feasible_history,
            "task_coalition_times": coalition_times,
            "task_completion_times": completion_times,
            "active": active_history,
            "prices": reward_history,
            "load_trajectory": load_history[:, 0],
            "load_trajectories": load_history,
            "load_coupled": mode_history[:, 0] >= MODE_TRANSPORT,
            "treatment": policy.code,
        }


@dataclass(frozen=True, slots=True)
class _SimulationParams:
    beta: float = 2.0
    spatial_scale: float = 5.0
    idle_reward: float = 0.05
    revision_rate: float = 0.8
    min_revision_rate: float = 0.02
    revision_sigma: float = 2.0
    hysteresis: float = 0.03
    consensus_gain: float = 0.05
    attraction_gain: float = 1.1
    robot_repulsion_gain: float = 0.06
    obstacle_repulsion_gain: float = 0.35
    formation_radius: float = 0.65
    formation_activation_radius: float = 1.6
    robot_safety_radius: float = 0.45
    max_speed: float = 0.65
    max_angular_speed: float = 2.5
    local_minimum_kick: float = 0.0
    price_gain: float = 1.0
    staffing_slack: float = 0.0
    initial_price: float = 0.0

    @classmethod
    def from_controller(cls, controller: BaseController) -> "_SimulationParams":
        raw = getattr(controller, "parameters", None)
        if raw is None:
            raw = {}
        values = {field: getattr(cls(), field) for field in cls.__dataclass_fields__}
        values.update({key: float(value) for key, value in raw.items() if key in values})
        return cls(**values)


def _resolve_controller_policy(controller: BaseController) -> TreatmentPolicy:
    name = getattr(controller, "treatment", None) or controller.name
    return resolve_treatment(str(name))


def _initial_preferences(positions: Array, pickups: Array) -> Array:
    n_agents = positions.shape[0]
    n_tasks = pickups.shape[0]
    preferences = np.zeros((n_agents, n_tasks + 1), dtype=float)
    distances = np.linalg.norm(positions[:, None, :] - pickups[None, :, :], axis=2)
    scores = 1.0 / (distances + 1.0)
    preferences[:, 1:] = scores
    preferences[:, 0] = 0.05
    return _project_rows_to_simplex(preferences)


def _assignment_indicators(assignments: NDArray[np.int_], n_tasks: int) -> Array:
    y = np.zeros((assignments.size, n_tasks + 1), dtype=float)
    y[np.arange(assignments.size), assignments] = 1.0
    return y


def _compute_payoffs(
    positions: Array,
    xhat: Array,
    load_positions: Array,
    task_modes: NDArray[np.int_],
    rewards: Array,
    demands: NDArray[np.int_],
    active: NDArray[np.bool_],
    params: _SimulationParams,
    use_spatial: bool,
) -> Array:
    n_agents, strategy_count = xhat.shape
    n_tasks = strategy_count - 1
    payoffs = np.zeros_like(xhat)
    payoffs[:, 0] = params.idle_reward
    estimated_counts = n_agents * np.clip(xhat[:, 1:], 0.0, 1.0)
    demand = 1.0 / (1.0 + np.exp(params.beta * (estimated_counts - demands[None, :])))
    distances = np.linalg.norm(positions[:, None, :] - load_positions[None, :, :], axis=2)
    if use_spatial:
        spatial = np.exp(-(distances**2) / (2.0 * params.spatial_scale**2))
    else:
        spatial = np.ones_like(distances)
    spatial[:, task_modes >= MODE_TRANSPORT] = 1.0
    payoffs[:, 1:] = rewards[None, :] * demand * spatial
    payoffs[~active, :] = 0.0
    delivered = task_modes == MODE_DELIVERED
    if np.any(delivered):
        payoffs[:, 1 + np.flatnonzero(delivered)] = 0.0
    return payoffs


def _revision_rates(
    positions: Array,
    assignments: NDArray[np.int_],
    load_positions: Array,
    active: NDArray[np.bool_],
    params: _SimulationParams,
    modulated: bool,
) -> Array:
    rates = np.full(assignments.size, params.revision_rate, dtype=float)
    for idx, assignment in enumerate(assignments):
        if not active[idx]:
            rates[idx] = 0.0
        elif modulated and assignment > 0:
            distance = np.linalg.norm(positions[idx] - load_positions[assignment - 1])
            rates[idx] = params.min_revision_rate + (
                params.revision_rate - params.min_revision_rate
            ) * (1.0 - np.exp(-(distance**2) / (2.0 * params.revision_sigma**2)))
    return rates


def _preference_dynamics_step(
    preferences: Array,
    payoffs: Array,
    rates: Array,
    dt: float,
    active: NDArray[np.bool_],
    policy: TreatmentPolicy,
) -> Array:
    if policy.dynamics == "smith":
        return _smith_step(preferences, payoffs, rates, dt, active)
    if policy.dynamics == "replicator":
        return _replicator_step(preferences, payoffs, rates, dt, active)
    return preferences


def _smith_step(
    preferences: Array,
    payoffs: Array,
    rates: Array,
    dt: float,
    active: NDArray[np.bool_],
) -> Array:
    next_preferences = preferences.copy()
    for idx in range(preferences.shape[0]):
        if not active[idx]:
            next_preferences[idx] = 0.0
            next_preferences[idx, 0] = 1.0
            continue
        f = payoffs[idx]
        p = preferences[idx]
        diff = f[:, None] - f[None, :]
        positive = np.maximum(diff, 0.0)
        inflow = positive @ p
        outflow = p * np.sum(np.maximum(-diff, 0.0), axis=1)
        next_preferences[idx] = p + dt * rates[idx] * (inflow - outflow)
    return _project_rows_to_simplex(next_preferences)


def _replicator_step(
    preferences: Array,
    payoffs: Array,
    rates: Array,
    dt: float,
    active: NDArray[np.bool_],
) -> Array:
    next_preferences = preferences.copy()
    for idx in range(preferences.shape[0]):
        if not active[idx]:
            next_preferences[idx] = 0.0
            next_preferences[idx, 0] = 1.0
            continue
        p = preferences[idx]
        f = payoffs[idx]
        average = float(np.dot(p, f))
        next_preferences[idx] = p + dt * rates[idx] * p * (f - average)
    return _project_rows_to_simplex(next_preferences)


def _preferences_from_assignments(assignments: NDArray[np.int_], n_tasks: int) -> Array:
    return _assignment_indicators(assignments, n_tasks)


def _update_assignments(
    assignments: NDArray[np.int_],
    preferences: Array,
    active: NDArray[np.bool_],
    hysteresis: float,
) -> NDArray[np.int_]:
    updated = assignments.copy()
    winners = np.argmax(preferences, axis=1)
    for idx, winner in enumerate(winners):
        if not active[idx]:
            updated[idx] = 0
            continue
        current = updated[idx]
        if winner != current and preferences[idx, winner] >= preferences[idx, current] + hysteresis:
            updated[idx] = int(winner)
    return updated


def _greedy_assignments(
    positions: Array,
    assignments: NDArray[np.int_],
    xhat: Array,
    active: NDArray[np.bool_],
    load_positions: Array,
    task_modes: NDArray[np.int_],
    demands: NDArray[np.int_],
    rewards: Array,
    use_dac: bool,
) -> NDArray[np.int_]:
    updated = np.zeros_like(assignments)
    assigned_counts = np.zeros(demands.size, dtype=float)
    estimated_counts = assignments.size * np.clip(np.mean(xhat[:, 1:], axis=0), 0.0, 1.0)
    for idx, position in enumerate(positions):
        if not active[idx]:
            continue
        counts = estimated_counts if use_dac else assigned_counts
        available = (task_modes != MODE_DELIVERED) & (counts < demands) & (assigned_counts < demands)
        if not np.any(available):
            updated[idx] = 0
            continue
        distances = np.linalg.norm(load_positions - position, axis=1)
        scores = rewards / (distances + 1.0)
        scores[~available] = -np.inf
        selected = int(np.argmax(scores))
        updated[idx] = selected + 1
        assigned_counts[selected] += 1.0
    return updated


def _centralized_assignments(
    positions: Array,
    active: NDArray[np.bool_],
    load_positions: Array,
    destinations: Array,
    task_modes: NDArray[np.int_],
    demands: NDArray[np.int_],
) -> NDArray[np.int_]:
    updated = np.zeros(active.size, dtype=int)
    active_indices = np.flatnonzero(active)
    if active_indices.size == 0:
        return updated

    slot_targets: list[Array] = []
    slot_tasks: list[int] = []
    for task_idx, demand in enumerate(demands):
        if task_modes[task_idx] == MODE_DELIVERED:
            continue
        target = destinations[task_idx] if task_modes[task_idx] == MODE_TRANSPORT else load_positions[task_idx]
        for _ in range(int(demand)):
            slot_targets.append(target)
            slot_tasks.append(task_idx + 1)

    if not slot_targets:
        return updated

    if active_indices.size > len(slot_targets):
        idle_count = active_indices.size - len(slot_targets)
        far_point = np.mean(np.vstack(slot_targets), axis=0)
        for _ in range(idle_count):
            slot_targets.append(far_point)
            slot_tasks.append(0)

    targets = np.vstack(slot_targets)
    cost = np.linalg.norm(positions[active_indices, None, :] - targets[None, :, :], axis=2)
    idle_cols = np.array(slot_tasks) == 0
    if np.any(idle_cols):
        cost[:, idle_cols] = np.max(cost[:, ~idle_cols]) + 1.0 if np.any(~idle_cols) else 0.0
    row_ind, col_ind = linear_sum_assignment(cost)
    for row, col in zip(row_ind, col_ind):
        updated[active_indices[row]] = slot_tasks[col]
    return updated


def _release_delivered_assignments(
    assignments: NDArray[np.int_],
    task_modes: NDArray[np.int_],
) -> NDArray[np.int_]:
    updated = assignments.copy()
    for task_idx, mode in enumerate(task_modes, start=1):
        if mode == MODE_DELIVERED:
            updated[updated == task_idx] = 0
    return updated


def _release_delivered_preferences(preferences: Array, task_modes: NDArray[np.int_]) -> Array:
    updated = preferences.copy()
    delivered = np.flatnonzero(task_modes == MODE_DELIVERED)
    if delivered.size:
        updated[:, 1 + delivered] = 0.0
        updated = _project_rows_to_simplex(updated)
    return updated


def _dac_step(
    xhat: Array,
    y: Array,
    previous_y: Array,
    adjacency: Array,
    gain: float,
    active: NDArray[np.bool_],
) -> Array:
    updated = xhat.copy()
    for idx in range(xhat.shape[0]):
        if not active[idx]:
            updated[idx] = y[idx]
            continue
        neighbors = np.flatnonzero(adjacency[idx] > 0)
        consensus = np.sum(xhat[neighbors] - xhat[idx], axis=0) if neighbors.size else 0.0
        updated[idx] = xhat[idx] + gain * consensus + (y[idx] - previous_y[idx])
    return updated


def _adaptive_price_step(
    prices: Array,
    caps: Array,
    xhat: Array,
    active: NDArray[np.bool_],
    task_modes: NDArray[np.int_],
    demands: NDArray[np.int_],
    params: _SimulationParams,
    dt: float,
) -> Array:
    """Integral price update for the single-clock treatment."""

    active_count = max(float(np.sum(active)), 1.0)
    active_estimates = xhat[active, 1:] if np.any(active) else xhat[:, 1:]
    estimated_counts = active_count * np.clip(np.mean(active_estimates, axis=0), 0.0, 1.0)
    targets = demands.astype(float) + params.staffing_slack
    updated = prices + dt * params.price_gain * (targets - estimated_counts)
    updated = np.clip(updated, 0.0, caps)
    updated[task_modes == MODE_DELIVERED] = 0.0
    return updated


def _coalition_presence(
    positions: Array,
    load_positions: Array,
    assignments: NDArray[np.int_],
    active: NDArray[np.bool_],
    detection_radius: float,
    n_tasks: int,
) -> NDArray[np.int_]:
    counts = np.zeros(n_tasks, dtype=int)
    for task_idx in range(n_tasks):
        assigned = (assignments == task_idx + 1) & active
        if np.any(assigned):
            distances = np.linalg.norm(positions[assigned] - load_positions[task_idx], axis=1)
            counts[task_idx] = int(np.sum(distances <= detection_radius))
    return counts


def _update_task_modes(
    task_modes: NDArray[np.int_],
    enough_counts: NDArray[np.int_],
    deficit_counts: NDArray[np.int_],
    coalition_present: NDArray[np.int_],
    demands: NDArray[np.int_],
    threshold: int,
) -> None:
    for task_idx in range(task_modes.size):
        if task_modes[task_idx] == MODE_DELIVERED:
            continue
        if coalition_present[task_idx] >= demands[task_idx]:
            enough_counts[task_idx] += 1
            deficit_counts[task_idx] = 0
            if enough_counts[task_idx] >= threshold:
                task_modes[task_idx] = MODE_TRANSPORT
        else:
            enough_counts[task_idx] = 0
            if task_modes[task_idx] == MODE_TRANSPORT:
                deficit_counts[task_idx] += 1
                if deficit_counts[task_idx] >= threshold:
                    task_modes[task_idx] = MODE_RECRUITING


def _navigation_controls(
    positions: Array,
    assignments: NDArray[np.int_],
    active: NDArray[np.bool_],
    load_positions: Array,
    destinations: Array,
    task_modes: NDArray[np.int_],
    demands: NDArray[np.int_],
    obstacles: list[Any],
    params: _SimulationParams,
) -> Array:
    controls = np.zeros_like(positions)
    for idx, assignment in enumerate(assignments):
        if not active[idx] or assignment == 0:
            continue
        task_idx = assignment - 1
        center = destinations[task_idx] if task_modes[task_idx] == MODE_TRANSPORT else load_positions[task_idx]
        target = center + _formation_offset(idx, assignments, active, task_idx, demands[task_idx], params)
        controls[idx] = params.attraction_gain * (target - positions[idx])

    controls += _robot_repulsion(positions, active, params)
    controls += _obstacle_repulsion(positions, active, obstacles, params)
    return controls


def _formation_offset(
    agent_index: int,
    assignments: NDArray[np.int_],
    active: NDArray[np.bool_],
    task_idx: int,
    demand: int,
    params: _SimulationParams,
) -> Array:
    if demand <= 1:
        return np.zeros(2, dtype=float)
    members = np.flatnonzero((assignments == task_idx + 1) & active)
    if members.size == 0:
        return np.zeros(2, dtype=float)
    rank = int(np.where(members == agent_index)[0][0]) if agent_index in members else 0
    count = max(demand, members.size)
    angle = 2.0 * np.pi * rank / count
    return params.formation_radius * np.array([np.cos(angle), np.sin(angle)])


def _robot_repulsion(positions: Array, active: NDArray[np.bool_], params: _SimulationParams) -> Array:
    repulsion = np.zeros_like(positions)
    for i in range(positions.shape[0]):
        if not active[i]:
            continue
        for j in range(positions.shape[0]):
            if i == j or not active[j]:
                continue
            delta = positions[i] - positions[j]
            distance = np.linalg.norm(delta)
            if 1e-9 < distance < params.robot_safety_radius:
                strength = params.robot_repulsion_gain * (1.0 / distance - 1.0 / params.robot_safety_radius)
                repulsion[i] += strength * delta / distance
    return repulsion


def _obstacle_repulsion(
    positions: Array,
    active: NDArray[np.bool_],
    obstacles: list[Any],
    params: _SimulationParams,
) -> Array:
    repulsion = np.zeros_like(positions)
    for idx, position in enumerate(positions):
        if not active[idx]:
            continue
        for obstacle in obstacles:
            delta = position - obstacle.center
            center_distance = np.linalg.norm(delta)
            signed_distance = center_distance - obstacle.radius
            if 1e-9 < signed_distance < obstacle.influence_radius:
                direction = delta / center_distance
                strength = params.obstacle_repulsion_gain * (
                    1.0 / max(signed_distance, 1e-3) - 1.0 / obstacle.influence_radius
                )
                repulsion[idx] += strength * direction
    return repulsion


def _integrate_unicycle(
    positions: Array,
    headings: Array,
    desired_velocity: Array,
    active: NDArray[np.bool_],
    dt: float,
    vmax: float,
    omega_max: float,
) -> tuple[Array, Array, Array]:
    next_positions = positions.copy()
    next_headings = headings.copy()
    applied = np.zeros_like(desired_velocity)
    for idx, vector in enumerate(desired_velocity):
        if not active[idx]:
            continue
        speed_command = min(float(np.linalg.norm(vector)), vmax)
        if speed_command < 1e-9:
            continue
        desired_heading = float(np.arctan2(vector[1], vector[0]))
        heading_error = _wrap_to_pi(desired_heading - headings[idx])
        omega = float(np.clip(heading_error / dt, -omega_max, omega_max))
        next_headings[idx] = _wrap_to_pi(headings[idx] + dt * omega)
        forward_scale = max(0.0, np.cos(heading_error))
        speed = speed_command * forward_scale
        applied[idx] = speed * np.array([np.cos(next_headings[idx]), np.sin(next_headings[idx])])
        next_positions[idx] = positions[idx] + dt * applied[idx]
    return next_positions, next_headings, applied


def _update_load_positions(
    load_positions: Array,
    positions: Array,
    assignments: NDArray[np.int_],
    active: NDArray[np.bool_],
    task_modes: NDArray[np.int_],
    destinations: Array,
    completion_times: Array,
    now: float,
    detection_radius: float,
) -> None:
    for task_idx in range(task_modes.size):
        if task_modes[task_idx] != MODE_TRANSPORT:
            continue
        members = (assignments == task_idx + 1) & active
        if np.any(members):
            load_positions[task_idx] = positions[members].mean(axis=0)
        if np.linalg.norm(load_positions[task_idx] - destinations[task_idx]) <= detection_radius:
            task_modes[task_idx] = MODE_DELIVERED
            completion_times[task_idx] = now
            load_positions[task_idx] = destinations[task_idx].copy()


def _apply_failure_events(
    now: float,
    active: NDArray[np.bool_],
    assignments: NDArray[np.int_],
    preferences: Array,
    xhat: Array,
    previous_y: Array,
    events: list[Any],
    applied: set[tuple[float, int]],
) -> None:
    for event in events:
        key = (event.time, event.agent_index)
        if key in applied or now + 1e-12 < event.time:
            continue
        if 0 <= event.agent_index < active.size:
            active[event.agent_index] = False
            assignments[event.agent_index] = 0
            preferences[event.agent_index] = 0.0
            preferences[event.agent_index, 0] = 1.0
            xhat[event.agent_index] = 0.0
            xhat[event.agent_index, 0] = 1.0
            previous_y[event.agent_index] = xhat[event.agent_index]
        applied.add(key)


def _adjacency_from_positions(
    positions: Array,
    active: NDArray[np.bool_],
    fallback: Array,
    communication_range: float | None,
) -> Array:
    if communication_range is None or np.isinf(communication_range):
        adjacency = np.asarray(fallback, dtype=float).copy()
    else:
        distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
        adjacency = ((distances <= communication_range) & (distances > 0.0)).astype(float)
    adjacency[~active, :] = 0.0
    adjacency[:, ~active] = 0.0
    return adjacency


def _project_rows_to_simplex(values: Array) -> Array:
    projected = np.vstack([_project_to_simplex(row) for row in values])
    return projected


def _project_to_simplex(values: Array) -> Array:
    vector = np.asarray(values, dtype=float)
    if vector.size == 1:
        return np.ones_like(vector)
    sorted_values = np.sort(vector)[::-1]
    cssv = np.cumsum(sorted_values) - 1.0
    index = np.arange(1, vector.size + 1)
    condition = sorted_values - cssv / index > 0
    if not np.any(condition):
        return np.full_like(vector, 1.0 / vector.size)
    rho = index[condition][-1]
    theta = cssv[condition][-1] / rho
    return np.maximum(vector - theta, 0.0)


def _wrap_to_pi(angle: float) -> float:
    return float((angle + np.pi) % (2.0 * np.pi) - np.pi)
