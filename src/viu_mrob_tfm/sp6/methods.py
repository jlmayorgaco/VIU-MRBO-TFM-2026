"""Methods and simulation loop for SP6 operational robustness."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, fields, replace
from time import perf_counter
from typing import Any

import numpy as np

from viu_mrob_tfm.control.explicit_law import ExplicitControlGains, required_wrench_pd
from viu_mrob_tfm.sp6.scenario import SP6Problem


SP6_METHOD_LABELS = {
    "classic_centralized_replan": "Classic centralized replanning",
    "classic_decentralized_greedy_recovery": "Classic decentralized greedy recovery",
    "cbba_recovery": "CBBA recovery",
    "cbf_recovery": "CBF recovery",
    "replicator_repair_recovery": "Replicator repair recovery",
    "smith_qr_recovery": "Smith-QR recovery",
    "primal_dual_recovery": "Primal-dual recovery",
    "tensor_flow_recovery": "Tensor-flow recovery",
    "ours_guarded_wrench_market_recovery": "Ours guarded wrench-market recovery",
    "reference_resilient_oracle": "Reference centralized resilient recovery",
}


METHOD_META = {
    "classic_centralized_replan": ("classic", "centralized", "baseline", "periodic_global_replan"),
    "classic_decentralized_greedy_recovery": ("classic", "decentralized", "baseline", "local_greedy_recovery"),
    "cbba_recovery": ("sota", "decentralized", "baseline", "cbba_recovery_auction"),
    "cbf_recovery": ("sota", "centralized", "baseline", "centralized_cbf_recovery"),
    "replicator_repair_recovery": ("model_based", "decentralized", "proposed", "replicator_integer_repair"),
    "smith_qr_recovery": ("model_based", "decentralized", "proposed", "smith_qr_recovery"),
    "primal_dual_recovery": ("model_based", "decentralized", "proposed", "primal_dual_recovery"),
    "tensor_flow_recovery": ("model_based", "decentralized", "proposed", "tensor_flow_recovery"),
    "ours_guarded_wrench_market_recovery": ("model_based", "decentralized", "proposed", "guarded_wrench_market_recovery"),
    "reference_resilient_oracle": ("model_based_reference", "centralized", "reference", "centralized_resilient_recovery"),
}


METHOD_RESOURCES = {
    "classic_centralized_replan": ("none", "centralized_periodic_replan", "global_state", 0, 2, False, False),
    "classic_decentralized_greedy_recovery": ("none", "local_greedy_recovery", "local_load_robot_state", 0, 2, False, False),
    "cbba_recovery": ("none", "distributed_auction_recovery", "local_bids_plus_neighbors", 0, 4, False, False),
    "cbf_recovery": ("none", "centralized_cbf_recovery", "global_state_and_obstacles", 0, 5, False, False),
    "replicator_repair_recovery": ("model_based_tuning_optional", "distributed_replicator_repair", "local_payoff_and_repair", 0, 5, False, False),
    "smith_qr_recovery": ("model_based_tuning_optional", "distributed_smith_qr_recovery", "local_deficit_prices", 0, 5, False, False),
    "primal_dual_recovery": ("model_based_tuning_optional", "distributed_primal_dual_recovery", "local_dual_prices", 0, 6, False, False),
    "tensor_flow_recovery": ("model_based_tuning_optional", "distributed_tensor_flow_recovery", "local_tensor_field", 0, 7, False, False),
    "ours_guarded_wrench_market_recovery": ("model_based_tuning_optional", "guarded_wrench_market_recovery", "local_wrench_prices_and_repair", 0, 8, False, False),
    "reference_resilient_oracle": ("none", "centralized_resilient_recovery", "global_state_and_event_observation", 0, 10, False, False),
}


@dataclass(frozen=True, slots=True)
class SP6PolicyConfig:
    global_state: bool = False
    guarded: bool = False
    oracle: bool = False
    replan_interval_s: float = 2.0
    target_gain: float = 1.25
    safety_gain: float = 0.42
    robot_repulsion_gain: float = 0.12
    battery_guard: bool = True
    communication_penalty: float = 0.22
    distance_weight: float = 0.10
    capacity_weight: float = 0.015
    wrench_weight: float = 0.010
    priority_weight: float = 1.0
    repair_strength: float = 0.0
    speed_scale: float = 0.90
    observation_delay_s: float = 0.0
    explicit_control_law: bool = False
    explicit_pose_bandwidth: float = 1.05
    explicit_theta_bandwidth: float = 1.05
    explicit_accel_fraction: float = 0.80


@dataclass(frozen=True, slots=True)
class SP6TrajectoryResult:
    method: str
    method_label: str
    time_s: np.ndarray
    robot_positions: np.ndarray
    robot_velocities: np.ndarray
    load_pose: np.ndarray
    load_velocity: np.ndarray
    formation_errors: np.ndarray
    wrench_residuals: np.ndarray
    wrench_margins: np.ndarray
    support_level: np.ndarray
    load_paused_mask: np.ndarray
    degraded_speed_mask: np.ndarray
    labels: np.ndarray
    active_mask: np.ndarray
    battery_fraction: np.ndarray
    completed_loads: np.ndarray
    completion_times_s: np.ndarray
    feasible_after_event: np.ndarray
    event_observed_time_s: float
    reassignment_count: int
    runtime_ms: float


class SP6RecoveryPolicy:
    """Assignment repair plus motion policy for SP6."""

    def __init__(self, method_id: str, config: SP6PolicyConfig | None = None) -> None:
        self.method_id = _canonical_method(method_id)
        self.config = config or _default_config(self.method_id)

    def assign(
        self,
        problem: SP6Problem,
        positions: np.ndarray,
        active: np.ndarray,
        battery: np.ndarray,
        completed: np.ndarray,
        t_s: float,
        previous_labels: np.ndarray | None = None,
    ) -> np.ndarray:
        return _assign_labels(problem, self.config, positions, active, battery, completed, t_s, previous_labels=previous_labels)


def make_sp6_policy(method_id: str, params: dict[str, Any] | None = None) -> SP6RecoveryPolicy:
    params = dict(params or {})
    method = _canonical_method(method_id)
    cfg = _default_config(method)
    policy_params = dict(params.get("policy", params))
    if policy_params:
        allowed = {field.name for field in fields(SP6PolicyConfig)}
        cfg = replace(cfg, **{key: value for key, value in policy_params.items() if key in allowed})
    return SP6RecoveryPolicy(method, cfg)


def simulate_recovery(policy: SP6RecoveryPolicy, problem: SP6Problem) -> SP6TrajectoryResult:
    """Roll out one SP6 recovery policy."""

    start = perf_counter()
    steps = int(np.ceil(problem.horizon_s / problem.dt_s))
    n = len(problem.world.robots)
    m = len(problem.world.loads)
    time_s = np.arange(steps + 1, dtype=float) * problem.dt_s
    positions = np.zeros((steps + 1, n, 2), dtype=float)
    velocities = np.zeros((steps + 1, n, 2), dtype=float)
    load_pose = np.zeros((steps + 1, m, 3), dtype=float)
    load_velocity = np.zeros((steps + 1, m, 3), dtype=float)
    formation_errors = np.full((steps + 1, m), 99.0, dtype=float)
    wrench_residuals = np.ones((steps + 1, m), dtype=float)
    wrench_margins = np.full((steps + 1, m), -1.0, dtype=float)
    support_level = np.zeros((steps + 1, m), dtype=float)
    load_paused = np.zeros((steps + 1, m), dtype=bool)
    degraded_speed = np.zeros((steps + 1, m), dtype=bool)
    labels = np.zeros((steps + 1, n), dtype=int)
    active = np.ones((steps + 1, n), dtype=bool)
    battery = np.zeros((steps + 1, n), dtype=float)
    completed = np.zeros((steps + 1, m), dtype=bool)
    completion_times = np.full(m, np.nan, dtype=float)
    positions[0] = _project_clearance(problem, np.vstack([robot.position for robot in problem.world.robots]), 0.0)
    battery[0] = np.asarray([robot.battery_fraction for robot in problem.world.robots], dtype=float)
    initial_load_pose = problem.initial_load_poses.copy()
    for load_idx in range(m):
        initial_load_pose[load_idx] = _project_load_clearance(problem, load_idx, initial_load_pose[load_idx], 0.0, initial_load_pose)
    load_pose[0] = initial_load_pose
    current_labels = np.zeros(n, dtype=int)
    event_observed_time = float(problem.event.time_s + (0.0 if policy.config.global_state else problem.event.observation_delay_s + policy.config.observation_delay_s))
    reassignment_count = 0
    next_replan_time = 0.0
    event_applied = False

    for step in range(steps):
        t_s = float(time_s[step])
        if (not event_applied) and t_s >= problem.event.time_s:
            _apply_event(problem, active[step], battery[step])
            event_applied = True
        elif event_applied:
            _apply_event(problem, active[step], battery[step])

        needs_replan = step == 0 or t_s >= next_replan_time or abs(t_s - problem.event.time_s) <= 0.5 * problem.dt_s or abs(t_s - event_observed_time) <= 0.5 * problem.dt_s
        if needs_replan:
            new_labels = policy.assign(problem, positions[step], active[step], battery[step], completed[step], t_s, previous_labels=current_labels)
            if step > 0:
                reassignment_count += int(np.sum(new_labels != current_labels))
            current_labels = new_labels
            next_replan_time = t_s + max(float(policy.config.replan_interval_s), problem.dt_s)
        labels[step] = current_labels

        commanded = _robot_velocities(problem, policy.config, positions[step], load_pose[step], current_labels, active[step], battery[step], t_s)
        velocities[step] = commanded
        next_positions = positions[step] + problem.dt_s * commanded
        next_positions = _project_clearance(problem, next_positions, t_s + problem.dt_s)
        positions[step + 1] = next_positions

        next_load_pose, next_load_velocity, step_formation, step_residuals, step_margins, step_support, step_paused, step_degraded = _load_transport_step(
            problem,
            policy.config,
            load_pose[step],
            load_velocity[step],
            positions[step + 1],
            current_labels,
            active[step],
            battery[step],
            completed[step],
            t_s,
        )
        load_pose[step + 1] = next_load_pose
        load_velocity[step + 1] = next_load_velocity
        formation_errors[step] = step_formation
        wrench_residuals[step] = step_residuals
        wrench_margins[step] = step_margins
        support_level[step] = step_support
        load_paused[step] = step_paused
        degraded_speed[step] = step_degraded

        distance = np.linalg.norm(next_positions - positions[step], axis=1)
        battery_next = np.clip(battery[step] - distance * np.asarray([robot.spec.battery.discharge_per_meter for robot in problem.world.robots], dtype=float), 0.0, 1.0)
        battery[step + 1] = battery_next
        active[step + 1] = active[step]
        completed_next = completed[step].copy()
        _update_completion(problem, load_pose[step + 1], completed_next, completion_times, t_s + problem.dt_s)
        completed[step + 1] = completed_next
        labels[step + 1] = current_labels

    final_formation, final_residuals, final_margins, final_support = _load_support_state(problem, load_pose[-1], positions[-1], labels[-1], active[-1], battery[-1], float(time_s[-1]))
    for load_idx, done in enumerate(completed[-1]):
        if bool(done):
            final_formation[load_idx] = 0.0
            final_residuals[load_idx] = 0.0
            final_margins[load_idx] = 0.0
            final_support[load_idx] = 1.0
    formation_errors[-1] = final_formation
    wrench_residuals[-1] = final_residuals
    wrench_margins[-1] = final_margins
    support_level[-1] = final_support
    load_paused[-1] = load_paused[-2] if len(load_paused) > 1 else False
    degraded_speed[-1] = degraded_speed[-2] if len(degraded_speed) > 1 else False
    event_idx = min(len(time_s) - 1, int(np.searchsorted(time_s, problem.event.time_s, side="left")))
    feasible_after_event = _feasible_after_event(problem, active[event_idx], battery[event_idx])
    runtime_ms = 1000.0 * (perf_counter() - start)
    return SP6TrajectoryResult(
        method=policy.method_id,
        method_label=SP6_METHOD_LABELS[policy.method_id],
        time_s=time_s,
        robot_positions=positions,
        robot_velocities=velocities,
        load_pose=load_pose,
        load_velocity=load_velocity,
        formation_errors=formation_errors,
        wrench_residuals=wrench_residuals,
        wrench_margins=wrench_margins,
        support_level=support_level,
        load_paused_mask=load_paused,
        degraded_speed_mask=degraded_speed,
        labels=labels,
        active_mask=active,
        battery_fraction=battery,
        completed_loads=completed,
        completion_times_s=completion_times,
        feasible_after_event=feasible_after_event,
        event_observed_time_s=event_observed_time,
        reassignment_count=int(reassignment_count),
        runtime_ms=runtime_ms,
    )


def sp6_method_metadata(method_id: str) -> dict[str, Any]:
    method = _canonical_method(method_id)
    family, scope, ownership, variant = METHOD_META[method]
    training_type, execution_model, communication_pattern, trainable, tuned, uses_neural, uses_decoder = METHOD_RESOURCES[method]
    return {
        "label": SP6_METHOD_LABELS[method],
        "title": f"{SP6_METHOD_LABELS[method]} [{ownership} | {family} | {scope} | {variant}]",
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "comparison_group": f"{ownership}_{family}_{scope}",
        "training_type": training_type,
        "execution_model": execution_model,
        "communication_pattern": communication_pattern,
        "trainable_parameters": trainable,
        "tuned_parameters": tuned,
        "uses_neural_policy": uses_neural,
        "uses_decoder": uses_decoder,
    }


def communication_messages(problem: SP6Problem, result: SP6TrajectoryResult, *, centralized: bool) -> int:
    n = len(problem.world.robots)
    frames = max(len(result.time_s) - 1, 1)
    if centralized:
        return int(frames * n * max(n - 1, 0))
    total = 0
    for idx, frame in enumerate(result.robot_positions[:-1]):
        radius = problem.communication_radius_at(float(result.time_s[idx]))
        if not np.isfinite(radius):
            total += int(n * max(n - 1, 0))
            continue
        distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
        total += int(np.sum((distances <= radius) & (distances > 0.0)))
    return total


def communication_coverage(problem: SP6Problem, result: SP6TrajectoryResult, *, centralized: bool) -> float:
    n = len(problem.world.robots)
    if n <= 1:
        return 1.0
    if centralized:
        return 1.0
    ratios = []
    denom = n * max(n - 1, 0)
    for idx, frame in enumerate(result.robot_positions[:-1]):
        radius = problem.communication_radius_at(float(result.time_s[idx]))
        if not np.isfinite(radius):
            ratios.append(1.0)
            continue
        distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
        ratios.append(float(np.sum((distances <= radius) & (distances > 0.0)) / max(denom, 1)))
    return float(np.mean(ratios)) if ratios else 1.0


def _canonical_method(method_id: str) -> str:
    method = method_id.lower()
    aliases = {
        "centralized_replan": "classic_centralized_replan",
        "decentralized_greedy": "classic_decentralized_greedy_recovery",
        "cbba": "cbba_recovery",
        "cbf": "cbf_recovery",
        "replicator": "replicator_repair_recovery",
        "smith": "smith_qr_recovery",
        "primal_dual": "primal_dual_recovery",
        "tensor": "tensor_flow_recovery",
        "ours": "ours_guarded_wrench_market_recovery",
        "reference": "reference_resilient_oracle",
    }
    method = aliases.get(method, method)
    if method not in METHOD_META:
        raise ValueError(f"Unknown SP6 method: {method_id}")
    return method


def _default_config(method: str) -> SP6PolicyConfig:
    if method == "classic_centralized_replan":
        return SP6PolicyConfig(global_state=True, replan_interval_s=4.0, target_gain=1.18, safety_gain=0.18, robot_repulsion_gain=0.05, battery_guard=False, speed_scale=0.90)
    if method == "classic_decentralized_greedy_recovery":
        return SP6PolicyConfig(replan_interval_s=5.0, target_gain=1.12, safety_gain=0.22, robot_repulsion_gain=0.08, battery_guard=False, communication_penalty=0.45, speed_scale=0.86)
    if method == "cbba_recovery":
        return SP6PolicyConfig(replan_interval_s=3.0, target_gain=1.18, safety_gain=0.34, robot_repulsion_gain=0.10, communication_penalty=0.35, priority_weight=1.12, repair_strength=0.20, speed_scale=0.88)
    if method == "cbf_recovery":
        return SP6PolicyConfig(global_state=True, replan_interval_s=2.5, target_gain=1.20, safety_gain=0.58, robot_repulsion_gain=0.16, guarded=True, repair_strength=0.25, speed_scale=0.88)
    if method == "replicator_repair_recovery":
        return SP6PolicyConfig(replan_interval_s=2.4, target_gain=1.22, safety_gain=0.40, robot_repulsion_gain=0.13, guarded=True, repair_strength=0.42, speed_scale=0.90)
    if method == "smith_qr_recovery":
        return SP6PolicyConfig(replan_interval_s=2.2, target_gain=1.24, safety_gain=0.42, robot_repulsion_gain=0.13, guarded=True, repair_strength=0.46, capacity_weight=0.018, speed_scale=0.90)
    if method == "primal_dual_recovery":
        return SP6PolicyConfig(replan_interval_s=1.8, target_gain=1.26, safety_gain=0.44, robot_repulsion_gain=0.14, guarded=True, repair_strength=0.54, capacity_weight=0.019, speed_scale=0.90)
    if method == "tensor_flow_recovery":
        return SP6PolicyConfig(replan_interval_s=1.6, target_gain=1.28, safety_gain=0.50, robot_repulsion_gain=0.16, guarded=True, repair_strength=0.60, wrench_weight=0.014, speed_scale=0.90, explicit_control_law=True, explicit_pose_bandwidth=1.08, explicit_theta_bandwidth=1.04)
    if method == "ours_guarded_wrench_market_recovery":
        return SP6PolicyConfig(replan_interval_s=1.4, target_gain=1.30, safety_gain=0.55, robot_repulsion_gain=0.16, guarded=True, repair_strength=0.72, capacity_weight=0.020, wrench_weight=0.018, speed_scale=0.92, explicit_control_law=True, explicit_pose_bandwidth=1.14, explicit_theta_bandwidth=1.10)
    if method == "reference_resilient_oracle":
        return SP6PolicyConfig(global_state=True, guarded=True, oracle=False, replan_interval_s=2.0, target_gain=1.32, safety_gain=0.62, robot_repulsion_gain=0.18, repair_strength=0.85, capacity_weight=0.020, wrench_weight=0.018, speed_scale=0.92, explicit_control_law=True, explicit_pose_bandwidth=1.16, explicit_theta_bandwidth=1.12)
    raise ValueError(f"Unknown SP6 method: {method}")


def _apply_event(problem: SP6Problem, active: np.ndarray, battery: np.ndarray) -> None:
    event = problem.event
    if event.kind in {"robot_dropout_mid_task", "delayed_information_consensus"}:
        for idx in event.robot_indices:
            if 0 <= idx < len(active):
                active[idx] = False
    if event.kind == "battery_depletion_reallocation" and event.battery_fraction_after is not None:
        for idx in event.robot_indices:
            if 0 <= idx < len(battery):
                battery[idx] = min(float(battery[idx]), float(event.battery_fraction_after))
                if battery[idx] <= problem.world.robots[idx].spec.battery.reserve_fraction:
                    active[idx] = False


def _assign_labels(
    problem: SP6Problem,
    cfg: SP6PolicyConfig,
    positions: np.ndarray,
    active: np.ndarray,
    battery: np.ndarray,
    completed: np.ndarray,
    t_s: float,
    *,
    previous_labels: np.ndarray | None = None,
) -> np.ndarray:
    observed_t = t_s if cfg.global_state else max(0.0, t_s - cfg.observation_delay_s)
    observed_active = active.copy()
    observed_battery = battery.copy()
    event_visible = cfg.global_state or observed_t >= problem.event.time_s + problem.event.observation_delay_s
    if not cfg.global_state and not event_visible:
        observed_active[:] = True
        observed_battery = np.maximum(observed_battery, 0.45)
    if cfg.oracle:
        return _oracle_labels(problem, cfg, positions, observed_active, observed_battery, completed, t_s)
    labels = np.zeros(len(problem.world.robots), dtype=int)
    available = set(_available_indices(problem, cfg, observed_active, observed_battery))
    load_order = sorted(range(len(problem.world.loads)), key=lambda idx: _load_priority(problem, idx, t_s), reverse=True)

    if previous_labels is not None:
        previous = np.asarray(previous_labels, dtype=int)
        for load_idx in load_order:
            if completed[load_idx]:
                continue
            demand = problem.load_demand_at(load_idx, observed_t, observed=True)
            min_size = int(problem.world.loads[load_idx].min_coalition_size)
            existing = [int(idx) for idx in np.flatnonzero(previous == load_idx + 1) if int(idx) in available]
            if not existing:
                continue
            feasible_with_all = _pool_can_serve(problem, list(set(existing) | available), demand, min_size, t_s)
            if cfg.guarded and not feasible_with_all:
                continue
            max_keep = max(min_size + 2, min_size)
            existing = sorted(existing, key=lambda ridx: _utility(problem, cfg, positions, observed_battery, ridx, load_idx, t_s), reverse=True)[:max_keep]
            for ridx in existing:
                labels[ridx] = load_idx + 1
                available.discard(ridx)

    for load_idx in load_order:
        if completed[load_idx]:
            continue
        already = [int(idx) for idx in np.flatnonzero(labels == load_idx + 1)]
        demand = problem.load_demand_at(load_idx, observed_t, observed=True)
        min_size = int(problem.world.loads[load_idx].min_coalition_size)
        current_capacity = sum(_effective_payload(problem, observed_battery, ridx, t_s) for ridx in already)
        if len(already) >= min_size and current_capacity >= demand:
            continue
        feasible_pool = list(available)
        if cfg.guarded and not _pool_can_serve(problem, feasible_pool, demand, min_size, t_s):
            if not already or not _pool_can_serve(problem, already + feasible_pool, demand, min_size, t_s):
                continue
        ranked = sorted(feasible_pool, key=lambda ridx: _utility(problem, cfg, positions, observed_battery, ridx, load_idx, t_s), reverse=True)
        chosen: list[int] = list(already)
        capacity = current_capacity
        for ridx in ranked:
            if len(chosen) >= min_size and capacity >= demand:
                break
            chosen.append(ridx)
            capacity += _effective_payload(problem, observed_battery, ridx, t_s)
        if not chosen:
            continue
        if cfg.guarded and (len(chosen) < min_size or capacity < demand):
            continue
        if len(chosen) < min_size and cfg.repair_strength < 0.35:
            continue
        for ridx in chosen:
            labels[ridx] = load_idx + 1
            available.discard(ridx)
    return labels


def _oracle_labels(problem: SP6Problem, cfg: SP6PolicyConfig, positions: np.ndarray, active: np.ndarray, battery: np.ndarray, completed: np.ndarray, t_s: float) -> np.ndarray:
    labels = np.zeros(len(problem.world.robots), dtype=int)
    remaining = set(_available_indices(problem, cfg, active, battery))
    load_order = sorted(range(len(problem.world.loads)), key=lambda idx: _load_priority(problem, idx, t_s), reverse=True)
    for load_idx in load_order:
        if completed[load_idx]:
            continue
        demand = problem.load_demand_at(load_idx, t_s, observed=True)
        min_size = int(problem.world.loads[load_idx].min_coalition_size)
        best_subset: tuple[int, ...] | None = None
        best_cost = float("inf")
        candidates = list(remaining)
        max_size = min(len(candidates), max(min_size + 2, min_size))
        for size in range(min_size, max_size + 1):
            for subset in itertools.combinations(candidates, size):
                if not _pool_can_serve(problem, subset, demand, min_size, t_s):
                    continue
                distance_cost = sum(np.linalg.norm(positions[idx] - problem.world.loads[load_idx].destination) for idx in subset)
                capacity_surplus = sum(_effective_payload(problem, battery, idx, t_s) for idx in subset) - demand
                cost = distance_cost + 0.85 * len(subset) - 0.01 * capacity_surplus
                if cost < best_cost:
                    best_cost = cost
                    best_subset = tuple(subset)
        if best_subset is None:
            continue
        for ridx in best_subset:
            labels[ridx] = load_idx + 1
            remaining.discard(ridx)
    return labels


def _available_indices(problem: SP6Problem, cfg: SP6PolicyConfig, active: np.ndarray, battery: np.ndarray) -> list[int]:
    output = []
    for idx, robot in enumerate(problem.world.robots):
        if not bool(active[idx]):
            continue
        if cfg.battery_guard and battery[idx] <= robot.spec.battery.reserve_fraction + 0.03:
            continue
        output.append(idx)
    return output


def _utility(problem: SP6Problem, cfg: SP6PolicyConfig, positions: np.ndarray, battery: np.ndarray, robot_idx: int, load_idx: int, t_s: float) -> float:
    load = problem.world.loads[load_idx]
    distance = float(np.linalg.norm(positions[robot_idx] - load.destination))
    payload = _effective_payload(problem, battery, robot_idx, t_s)
    force = float(problem.world.robots[robot_idx].spec.capacity.force_limit_n)
    radius = problem.communication_radius_at(t_s)
    communication_penalty = 0.0
    if not cfg.global_state and np.isfinite(radius) and distance > max(radius * 1.8, radius + 1.0):
        communication_penalty = cfg.communication_penalty * (distance - radius)
    return (
        cfg.priority_weight * _load_priority(problem, load_idx, t_s)
        + cfg.capacity_weight * payload
        + cfg.wrench_weight * force
        - cfg.distance_weight * distance
        - communication_penalty
        + cfg.repair_strength * float(payload >= 0.45 * (load.min_capacity_kg or load.mass_kg))
    )


def _load_priority(problem: SP6Problem, load_idx: int, t_s: float) -> float:
    reward = float(problem.world.loads[load_idx].reward)
    if problem.event.kind == "multi_load_priority_shift" and t_s >= problem.event.time_s and load_idx == len(problem.world.loads) - 1:
        reward *= 1.65
    return reward


def _pool_can_serve(problem: SP6Problem, pool: list[int] | tuple[int, ...], demand: float, min_size: int, t_s: float | None = None) -> bool:
    if len(pool) < min_size:
        return False
    capacity = sum(_effective_payload(problem, np.ones(len(problem.world.robots), dtype=float), idx, t_s) for idx in pool)
    return capacity >= demand


def _effective_payload(problem: SP6Problem, battery: np.ndarray, robot_idx: int, t_s: float | None = None) -> float:
    robot = problem.world.robots[robot_idx]
    if battery[robot_idx] <= robot.spec.battery.reserve_fraction:
        return 0.0
    scale = np.clip((battery[robot_idx] - robot.spec.battery.reserve_fraction) / max(1.0 - robot.spec.battery.reserve_fraction, 1e-9), 0.0, 1.0)
    return float(robot.spec.capacity.payload_kg * scale * _event_force_scale(problem, robot_idx, t_s))


def _robot_velocities(problem: SP6Problem, cfg: SP6PolicyConfig, positions: np.ndarray, load_pose: np.ndarray, labels: np.ndarray, active: np.ndarray, battery: np.ndarray, t_s: float) -> np.ndarray:
    velocities = np.zeros_like(positions)
    for idx, robot in enumerate(problem.world.robots):
        if not active[idx] or battery[idx] <= robot.spec.battery.reserve_fraction:
            continue
        label = int(labels[idx])
        if label <= 0:
            target = positions[idx]
        else:
            target = _target_for_robot(problem, labels, idx, load_pose)
        desired = cfg.target_gain * (target - positions[idx])
        desired += _safety_velocity(problem, cfg, positions, idx, t_s)
        limit = max(float(robot.spec.max_speed) * cfg.speed_scale * _event_speed_scale(problem, idx, t_s), 1e-9)
        norm = float(np.linalg.norm(desired))
        if norm > limit:
            desired = desired / norm * limit
        velocities[idx] = desired
    return velocities


def _safety_velocity(problem: SP6Problem, cfg: SP6PolicyConfig, positions: np.ndarray, idx: int, t_s: float) -> np.ndarray:
    term = np.zeros(2, dtype=float)
    for obstacle in problem.active_obstacles_at(t_s):
        vec = positions[idx] - obstacle.center
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        clearance = dist - obstacle.radius - problem.robot_radius_m
        if clearance < obstacle.influence_radius:
            normal = vec / dist
            tangent = np.array([-normal[1], normal[0]], dtype=float)
            pressure = max(0.0, 1.0 / max(clearance + 0.20, 0.20) - 1.0 / (obstacle.influence_radius + 0.20))
            term += cfg.safety_gain * pressure * normal + 0.32 * cfg.safety_gain * pressure * tangent
    safe = 2.0 * problem.robot_radius_m + problem.safety_margin_m
    for j in range(positions.shape[0]):
        if j == idx:
            continue
        vec = positions[idx] - positions[j]
        dist = float(np.linalg.norm(vec))
        if dist <= 1e-9:
            vec = np.array([1.0, 0.0], dtype=float)
            dist = 1.0
        if dist < 2.5 * safe:
            term += cfg.robot_repulsion_gain * (2.5 * safe - dist) * vec / dist
    return _clip_vector(term, 1.2)


def _load_transport_step(
    problem: SP6Problem,
    cfg: SP6PolicyConfig,
    q: np.ndarray,
    qd: np.ndarray,
    positions: np.ndarray,
    labels: np.ndarray,
    active: np.ndarray,
    battery: np.ndarray,
    completed: np.ndarray,
    t_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    next_q = q.copy()
    next_qd = qd.copy()
    formation, residuals, margins, support = _load_support_state(problem, q, positions, labels, active, battery, t_s)
    paused = np.zeros(len(problem.world.loads), dtype=bool)
    degraded = np.zeros(len(problem.world.loads), dtype=bool)
    for load_idx, load in enumerate(problem.world.loads):
        if completed[load_idx]:
            next_q[load_idx] = _project_load_clearance(problem, load_idx, q[load_idx], t_s + problem.dt_s, next_q)
            next_qd[load_idx] = 0.0
            residuals[load_idx] = 0.0
            margins[load_idx] = max(margins[load_idx], 0.0)
            support[load_idx] = max(support[load_idx], 1.0)
            continue
        formation_factor = float(np.clip(1.0 - max(0.0, formation[load_idx] - problem.formation_tolerance_m) / max(1.8 * problem.formation_tolerance_m, 1e-9), 0.0, 1.0))
        support_factor = float(np.clip(support[load_idx], 0.0, 1.0))
        transport_factor = min(formation_factor, support_factor)
        paused[load_idx] = bool(transport_factor < 0.18)
        degraded[load_idx] = bool(0.18 <= transport_factor < 0.98)
        if paused[load_idx]:
            next_qd[load_idx] *= 0.35
            next_q[load_idx] = _project_load_clearance(problem, load_idx, q[load_idx] + problem.dt_s * next_qd[load_idx], t_s + problem.dt_s, next_q)
            continue

        target = problem.target_load_poses[load_idx]
        pos_error = target[:2] - q[load_idx, :2]
        theta_error = _wrap_angle(float(target[2] - q[load_idx, 2]))
        mass = max(float(load.mass_kg), 1e-6)
        inertia = max(float(mass * (load.length_m**2 + load.width_m**2) / 12.0), 1e-6)
        if cfg.explicit_control_law:
            gains = ExplicitControlGains(
                load_position_bandwidth=float(cfg.explicit_pose_bandwidth),
                load_orientation_bandwidth=float(cfg.explicit_theta_bandwidth),
                acceleration_limit_fraction=float(cfg.explicit_accel_fraction),
            )
            desired_wrench, _desired_accel = required_wrench_pd(
                mass_total_kg=mass,
                inertia_total_kgm2=inertia,
                pose=q[load_idx],
                twist=qd[load_idx],
                target_pose=target,
                target_twist=np.zeros(3, dtype=float),
                target_acceleration=np.zeros(3, dtype=float),
                gains=gains,
                force_limit_sum_n=_active_force_limit_sum(problem, labels, active, load_idx, t_s),
            )
        else:
            desired_wrench = np.array(
                [
                    18.0 * pos_error[0] - 9.5 * qd[load_idx, 0],
                    18.0 * pos_error[1] - 9.5 * qd[load_idx, 1],
                    24.0 * theta_error - 19.0 * qd[load_idx, 2],
                ],
                dtype=float,
            )
        achieved = transport_factor * desired_wrench
        qdd = np.array([achieved[0] / mass, achieved[1] / mass, achieved[2] / inertia], dtype=float)
        next_qd[load_idx] = qd[load_idx] + problem.dt_s * qdd
        base_speed = 0.62 if support_factor >= 0.98 else 0.36
        next_qd[load_idx, :2] = _clip_vector(next_qd[load_idx, :2], base_speed * max(transport_factor, 0.10))
        next_qd[load_idx, 2] = float(np.clip(next_qd[load_idx, 2], -0.78 * max(transport_factor, 0.10), 0.78 * max(transport_factor, 0.10)))
        candidate = next_q[load_idx] + problem.dt_s * next_qd[load_idx]
        candidate[2] = _wrap_angle(float(candidate[2]))
        projected = _project_load_clearance(problem, load_idx, candidate, t_s + problem.dt_s, next_q)
        next_q[load_idx] = projected
        next_qd[load_idx, :2] = (projected[:2] - q[load_idx, :2]) / problem.dt_s
        next_qd[load_idx, 2] = _wrap_angle(float(projected[2] - q[load_idx, 2])) / problem.dt_s
    return next_q, next_qd, formation, residuals, margins, support, paused, degraded


def _load_support_state(
    problem: SP6Problem,
    q: np.ndarray,
    positions: np.ndarray,
    labels: np.ndarray,
    active: np.ndarray,
    battery: np.ndarray,
    t_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    m = len(problem.world.loads)
    formation = np.full(m, 99.0, dtype=float)
    residuals = np.ones(m, dtype=float)
    margins = np.full(m, -1.0, dtype=float)
    support = np.zeros(m, dtype=float)
    for load_idx, load in enumerate(problem.world.loads):
        members = np.flatnonzero((labels == load_idx + 1) & active)
        slot_positions = _slot_positions(problem, load_idx, q[load_idx], len(members))
        formation[load_idx] = _formation_error(positions, members, slot_positions)
        min_size = max(int(load.min_coalition_size), 1)
        demand = problem.load_demand_at(load_idx, t_s, observed=False)
        capacity = sum(_effective_payload(problem, battery, int(idx), t_s) for idx in members)
        force = sum(float(problem.world.robots[int(idx)].spec.capacity.force_limit_n) * _event_force_scale(problem, int(idx), t_s) for idx in members)
        torque = sum(float(problem.world.robots[int(idx)].spec.capacity.torque_limit_nm) * _event_force_scale(problem, int(idx), t_s) for idx in members)
        force_demand = max(float(np.linalg.norm(load.wrench.force_xy)), 1e-9)
        torque_demand = max(abs(float(load.wrench.torque_z)), 1e-9)
        ratios = [
            len(members) / min_size,
            capacity / max(demand, 1e-9),
            force / force_demand,
            torque / torque_demand,
        ]
        support[load_idx] = float(min(ratios))
        margins[load_idx] = float(support[load_idx] - 1.0)
        residuals[load_idx] = float(max(0.0, 1.0 - support[load_idx]) + max(0.0, formation[load_idx] - problem.formation_tolerance_m) / max(problem.formation_tolerance_m, 1e-9))
    return formation, residuals, margins, support


def _active_force_limit_sum(problem: SP6Problem, labels: np.ndarray, active: np.ndarray, load_idx: int, t_s: float) -> float:
    members = np.flatnonzero((labels == int(load_idx) + 1) & active)
    if members.size == 0:
        return float(max(problem.world.loads[load_idx].mass_kg, 1.0))
    return float(sum(problem.world.robots[int(idx)].spec.capacity.force_limit_n * _event_force_scale(problem, int(idx), t_s) for idx in members))


def _slot_positions(problem: SP6Problem, load_idx: int, q: np.ndarray, count: int) -> np.ndarray:
    slots = problem.load_slots[load_idx]
    if count <= 0 or not slots:
        return np.zeros((0, 2), dtype=float)
    rotation = _rotation(float(q[2]))
    return np.vstack([q[:2] + rotation @ slots[idx % len(slots)].offset_xy for idx in range(count)])


def _formation_error(positions: np.ndarray, members: np.ndarray, slot_positions: np.ndarray) -> float:
    if len(members) == 0 or slot_positions.size == 0:
        return 99.0
    count = min(len(members), len(slot_positions))
    errors = [float(np.linalg.norm(positions[int(members[idx])] - slot_positions[idx])) for idx in range(count)]
    return float(max(errors)) if errors else 99.0


def _target_for_robot(problem: SP6Problem, labels: np.ndarray, robot_idx: int, load_pose: np.ndarray | None = None) -> np.ndarray:
    label = int(labels[robot_idx])
    if label <= 0:
        return np.zeros(2, dtype=float)
    load = problem.world.loads[label - 1]
    members = np.flatnonzero(labels == label)
    rank_matches = np.flatnonzero(members == robot_idx)
    rank = int(rank_matches[0]) if rank_matches.size else 0
    slots = problem.load_slots[label - 1]
    if slots:
        slot_idx = rank % len(slots)
        pose = problem.target_load_poses[label - 1] if load_pose is None else load_pose[label - 1]
        return pose[:2] + _rotation(float(pose[2])) @ slots[slot_idx].offset_xy
    count = max(int(len(members)), int(load.min_coalition_size), 1)
    angle = 2.0 * math.pi * rank / count
    radius = max(0.55 * max(float(load.length_m), float(load.width_m)), 2.0 * problem.robot_radius_m + 2.0 * problem.safety_margin_m)
    center = problem.target_load_poses[label - 1, :2] if load_pose is None else load_pose[label - 1, :2]
    return center + radius * np.array([math.cos(angle), math.sin(angle)], dtype=float)


def _project_load_clearance(problem: SP6Problem, load_idx: int, q: np.ndarray, t_s: float, all_load_poses: np.ndarray | None = None) -> np.ndarray:
    desired = _clip_load_pose(problem, q)
    out = desired.copy()
    load = problem.world.loads[load_idx]
    margin = float(problem.safety_margin_m)
    best = out.copy()
    best_clearance = _minimum_load_clearance(problem, load_idx, out, t_s, all_load_poses)
    for _pass in range(80):
        previous = out.copy()
        for obstacle in problem.active_obstacles_at(t_s):
            out = _project_payload_rectangle_outside_circle(out, load, obstacle.center, obstacle.radius, margin)
        if all_load_poses is not None:
            for other_idx, other_load in enumerate(problem.world.loads):
                if other_idx == load_idx:
                    continue
                out = _project_payload_rectangle_outside_payload(out, load, all_load_poses[other_idx], other_load, margin)
        out = _clip_load_pose(problem, out)
        clearance = _minimum_load_clearance(problem, load_idx, out, t_s, all_load_poses)
        if clearance > best_clearance + 1e-9:
            best_clearance = clearance
            best = out.copy()
        if clearance >= margin - 1e-6:
            break
        if float(np.linalg.norm(out[:2] - previous[:2])) <= 1e-9:
            if clearance >= -1e-6:
                break
            recovered = _search_payload_clear_pose(problem, load_idx, desired, out, t_s, margin, all_load_poses)
            recovered_clearance = _minimum_load_clearance(problem, load_idx, recovered, t_s, all_load_poses)
            if recovered_clearance > best_clearance + 1e-9:
                best_clearance = recovered_clearance
                best = recovered.copy()
            out = recovered
            if recovered_clearance >= -1e-6:
                break
    if _minimum_load_clearance(problem, load_idx, out, t_s, all_load_poses) + 1e-9 < best_clearance:
        out = best
    return out


def _project_payload_rectangle_outside_circle(q: np.ndarray, load: Any, center: np.ndarray, radius: float, margin: float) -> np.ndarray:
    out = np.asarray(q, dtype=float).copy()
    center = np.asarray(center, dtype=float)
    rotation = _rotation(float(out[2]))
    local = rotation.T @ (center - out[:2])
    half_extents = np.array([0.5 * float(load.length_m), 0.5 * float(load.width_m)], dtype=float)
    closest = np.clip(local, -half_extents, half_extents)
    delta_local = local - closest
    distance = float(np.linalg.norm(delta_local))
    if distance > 1e-9:
        clearance = distance - float(radius)
        if clearance < margin:
            normal_world = rotation @ (delta_local / distance)
            out[:2] -= normal_world * (float(margin) - clearance + 1e-6)
        return out

    inflated = half_extents + float(radius + margin)
    penetration = inflated - np.abs(local)
    axis = int(np.argmin(penetration))
    sign = math.copysign(1.0, float(local[axis]))
    if abs(float(local[axis])) <= 1e-9:
        sign = 1.0
    correction_local = np.zeros(2, dtype=float)
    correction_local[axis] = -sign * (float(penetration[axis]) + 1e-6)
    out[:2] += rotation @ correction_local
    return out


def _clip_load_pose(problem: SP6Problem, q: np.ndarray) -> np.ndarray:
    half = 0.5 * problem.world.map.size_m
    out = np.asarray(q, dtype=float).copy()
    out[:2] = np.clip(out[:2], -0.82 * half, 0.82 * half)
    out[2] = _wrap_angle(float(out[2]))
    return out


def _search_payload_clear_pose(
    problem: SP6Problem,
    load_idx: int,
    desired_q: np.ndarray,
    current_q: np.ndarray,
    t_s: float,
    margin: float,
    all_load_poses: np.ndarray | None,
) -> np.ndarray:
    desired = _clip_load_pose(problem, desired_q)
    current = _clip_load_pose(problem, current_q)
    candidates = [desired, current]
    load = problem.world.loads[load_idx]
    for obstacle in problem.active_obstacles_at(t_s):
        candidates.append(_project_payload_rectangle_outside_circle(desired, load, obstacle.center, obstacle.radius, margin))
        candidates.append(_project_payload_rectangle_outside_circle(current, load, obstacle.center, obstacle.radius, margin))
    if all_load_poses is not None:
        for other_idx, other_load in enumerate(problem.world.loads):
            if other_idx == load_idx:
                continue
            candidates.append(_project_payload_rectangle_outside_payload(desired, load, all_load_poses[other_idx], other_load, margin))
            candidates.append(_project_payload_rectangle_outside_payload(current, load, all_load_poses[other_idx], other_load, margin))

    angles = np.linspace(0.0, 2.0 * math.pi, 72, endpoint=False)
    radii = np.array([0.15, 0.30, 0.50, 0.75, 1.05, 1.40, 1.80, 2.30, 2.90, 3.60, 4.50, 5.60], dtype=float)
    anchors = (desired[:2].copy(), current[:2].copy())
    for anchor in anchors:
        for radius in radii:
            offsets = np.column_stack((np.cos(angles), np.sin(angles))) * float(radius)
            for offset in offsets:
                candidate = desired.copy()
                candidate[:2] = anchor + offset
                candidates.append(_clip_load_pose(problem, candidate))

    best = current.copy()
    best_clearance = _minimum_load_clearance(problem, load_idx, best, t_s, all_load_poses)
    best_cost = float(np.linalg.norm(best[:2] - desired[:2]))
    for candidate in candidates:
        candidate = _clip_load_pose(problem, candidate)
        clearance = _minimum_load_clearance(problem, load_idx, candidate, t_s, all_load_poses)
        cost = float(np.linalg.norm(candidate[:2] - desired[:2]))
        if clearance >= margin:
            if best_clearance < margin or cost < best_cost - 1e-9:
                best = candidate.copy()
                best_clearance = clearance
                best_cost = cost
            continue
        if clearance > best_clearance + 1e-9 or (abs(clearance - best_clearance) <= 1e-9 and cost < best_cost):
            best = candidate.copy()
            best_clearance = clearance
            best_cost = cost
    return best


def _minimum_load_clearance(problem: SP6Problem, load_idx: int, q: np.ndarray, t_s: float, all_load_poses: np.ndarray | None) -> float:
    load = problem.world.loads[load_idx]
    values: list[float] = []
    for obstacle in problem.active_obstacles_at(t_s):
        values.append(_payload_rectangle_circle_clearance_local(q, load, obstacle.center, float(obstacle.radius)))
    if all_load_poses is not None:
        for other_idx, other_load in enumerate(problem.world.loads):
            if other_idx == load_idx:
                continue
            values.append(_payload_rectangle_rectangle_clearance_local(q, load, all_load_poses[other_idx], other_load))
    return float(min(values)) if values else float("inf")


def _payload_rectangle_circle_clearance_local(q: np.ndarray, load: Any, center: np.ndarray, radius_m: float) -> float:
    rotation_t = _rotation(float(q[2])).T
    local = rotation_t @ (np.asarray(center, dtype=float) - np.asarray(q[:2], dtype=float))
    half_extents = np.array([0.5 * float(load.length_m), 0.5 * float(load.width_m)], dtype=float)
    outside = np.maximum(np.abs(local) - half_extents, 0.0)
    return float(np.linalg.norm(outside) - float(radius_m))


def _payload_rectangle_rectangle_clearance_local(q_a: np.ndarray, load_a: Any, q_b: np.ndarray, load_b: Any) -> float:
    vec = np.asarray(q_a[:2], dtype=float) - np.asarray(q_b[:2], dtype=float)
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        normal = np.array([1.0, 0.0], dtype=float)
        dist = 0.0
    else:
        normal = vec / dist
    return float(dist - _payload_support_radius(q_a, load_a, normal) - _payload_support_radius(q_b, load_b, -normal))


def _project_payload_rectangle_outside_payload(q: np.ndarray, load: Any, other_q: np.ndarray, other_load: Any, margin: float) -> np.ndarray:
    out = np.asarray(q, dtype=float).copy()
    other_q = np.asarray(other_q, dtype=float)
    vec = out[:2] - other_q[:2]
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        vec = np.array([1.0, 0.0], dtype=float)
        dist = 1.0
    normal = vec / dist
    support_radius = _payload_support_radius(out, load, normal)
    other_support_radius = _payload_support_radius(other_q, other_load, -normal)
    min_distance = float(support_radius + other_support_radius + margin)
    if dist < min_distance:
        out[:2] = other_q[:2] + normal * min_distance
    return out


def _payload_support_radius(q: np.ndarray, load: Any, normal: np.ndarray) -> float:
    rotation = _rotation(float(q[2]))
    return float(
        0.5 * float(load.length_m) * abs(float(np.dot(normal, rotation[:, 0])))
        + 0.5 * float(load.width_m) * abs(float(np.dot(normal, rotation[:, 1])))
    )


def _project_clearance(problem: SP6Problem, positions: np.ndarray, t_s: float) -> np.ndarray:
    out = positions.copy()
    margin = float(problem.safety_margin_m + 0.035)
    for _pass in range(48):
        previous = out.copy()
        for idx in range(out.shape[0]):
            for obstacle in problem.active_obstacles_at(t_s):
                out[idx] = _project_point(out[idx], obstacle.center, obstacle.radius + problem.robot_radius_m + margin)
        for i in range(out.shape[0]):
            for j in range(i + 1, out.shape[0]):
                vec = out[i] - out[j]
                dist = float(np.linalg.norm(vec))
                min_distance = float(2.0 * problem.robot_radius_m + margin)
                if dist >= min_distance:
                    continue
                if dist <= 1e-9:
                    vec = np.array([1.0, 0.0], dtype=float)
                    dist = 1.0
                correction = 0.5 * (min_distance - dist) * vec / dist
                out[i] += correction
                out[j] -= correction
        half = 0.5 * problem.world.map.size_m
        out = np.clip(out, -0.92 * half, 0.92 * half)
        if float(np.linalg.norm(out - previous)) <= 1e-9:
            break
    return out


def _project_point(point: np.ndarray, center: np.ndarray, min_distance: float) -> np.ndarray:
    vec = point - center
    dist = float(np.linalg.norm(vec))
    if dist <= 1e-9:
        vec = np.array([1.0, 0.0], dtype=float)
        dist = 1.0
    if dist < min_distance:
        return center + vec / dist * min_distance
    return point


def _update_completion(problem: SP6Problem, load_pose: np.ndarray, completed: np.ndarray, completion_times: np.ndarray, t_s: float) -> None:
    for load_idx, load in enumerate(problem.world.loads):
        if completed[load_idx]:
            continue
        del load
        pos_error = float(np.linalg.norm(problem.target_load_poses[load_idx, :2] - load_pose[load_idx, :2]))
        theta_error = abs(_wrap_angle(float(problem.target_load_poses[load_idx, 2] - load_pose[load_idx, 2])))
        if pos_error <= problem.pose_tolerance_m and theta_error <= problem.orientation_tolerance_rad:
            completed[load_idx] = True
            completion_times[load_idx] = t_s


def _feasible_after_event(problem: SP6Problem, active: np.ndarray, battery: np.ndarray) -> np.ndarray:
    available = set(idx for idx, flag in enumerate(active) if bool(flag) and battery[idx] > problem.world.robots[idx].spec.battery.reserve_fraction)
    output = np.zeros(len(problem.world.loads), dtype=bool)
    load_order = sorted(range(len(problem.world.loads)), key=lambda idx: _load_priority(problem, idx, problem.event.time_s), reverse=True)
    for load_idx in load_order:
        load = problem.world.loads[load_idx]
        demand = problem.load_demand_at(load_idx, problem.event.time_s, observed=False)
        candidates = sorted(available, key=lambda idx: np.linalg.norm(problem.world.robots[idx].position - load.pickup))
        chosen: list[int] = []
        capacity = 0.0
        for ridx in candidates:
            if len(chosen) >= int(load.min_coalition_size) and capacity >= demand:
                break
            chosen.append(int(ridx))
            capacity += _effective_payload(problem, battery, int(ridx), problem.event.time_s)
        if len(chosen) >= int(load.min_coalition_size) and capacity >= demand:
            output[load_idx] = True
            for ridx in chosen:
                available.discard(ridx)
    return output


def _clip_vector(vector: np.ndarray, limit: float) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm > max(limit, 1e-9):
        return vector / norm * limit
    return np.asarray(vector, dtype=float)


def _event_speed_scale(problem: SP6Problem, robot_idx: int, t_s: float | None) -> float:
    if t_s is None or t_s < problem.event.time_s or robot_idx not in problem.event.robot_indices:
        return 1.0
    return float(problem.event.speed_scale_after)


def _event_force_scale(problem: SP6Problem, robot_idx: int, t_s: float | None) -> float:
    if t_s is None or t_s < problem.event.time_s or robot_idx not in problem.event.robot_indices:
        return 1.0
    return float(problem.event.force_scale_after)


def _rotation(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)


def _wrap_angle(value: float) -> float:
    return (float(value) + math.pi) % (2.0 * math.pi) - math.pi
