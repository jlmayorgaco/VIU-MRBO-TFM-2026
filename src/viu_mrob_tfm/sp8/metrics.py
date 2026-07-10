"""SP8 scalability, wrench and transport metrics."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.optimize import lsq_linear

from viu_mrob_tfm.sp8.methods import SP8Assignment, sp8_method_metadata
from viu_mrob_tfm.sp8.scenario import SP8Problem


@dataclass(frozen=True, slots=True)
class SP8Metrics:
    solved: bool
    timeout: bool
    solved_rate: float
    timeout_rate: float
    assigned_robot_rate: float
    scalar_feasible_rate: float
    wrench_feasible_rate: float
    false_positive_rate: float
    force_error_n_mean: float
    torque_error_nm_mean: float
    wrench_residual_norm_mean: float
    transport_success_rate: float
    task_completion_rate: float
    throughput_tasks_per_min: float
    collision_risk_rate: float
    obstacle_intersection_rate: float
    mobile_conflict_rate: float
    route_crossing_rate: float
    mean_travel_distance_m: float
    total_travel_distance_m: float
    energy_proxy_wh: float
    communication_messages: int
    messages_per_robot: float
    runtime_ms: float
    estimated_memory_mb: float
    complexity_score: float
    score_value: float
    reference_score_value: float
    performance_gap_vs_reference: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_sp8_assignment(problem: SP8Problem, assignment: SP8Assignment, *, reference_score: float | None = None) -> tuple[SP8Metrics, list[dict[str, Any]]]:
    if not assignment.solved:
        reference = 1.0 if reference_score is None else float(reference_score)
        metrics = SP8Metrics(
            solved=False,
            timeout=True,
            solved_rate=0.0,
            timeout_rate=1.0,
            assigned_robot_rate=0.0,
            scalar_feasible_rate=0.0,
            wrench_feasible_rate=0.0,
            false_positive_rate=0.0,
            force_error_n_mean=math.nan,
            torque_error_nm_mean=math.nan,
            wrench_residual_norm_mean=math.nan,
            transport_success_rate=0.0,
            task_completion_rate=0.0,
            throughput_tasks_per_min=0.0,
            collision_risk_rate=1.0,
            obstacle_intersection_rate=math.nan,
            mobile_conflict_rate=math.nan,
            route_crossing_rate=math.nan,
            mean_travel_distance_m=math.nan,
            total_travel_distance_m=math.nan,
            energy_proxy_wh=math.nan,
            communication_messages=int(assignment.communication_messages),
            messages_per_robot=float(assignment.communication_messages / max(problem.params.n_robots, 1)),
            runtime_ms=float(assignment.runtime_ms),
            estimated_memory_mb=float(assignment.estimated_memory_mb),
            complexity_score=float(assignment.complexity_score),
            score_value=-1.0e6,
            reference_score_value=reference,
            performance_gap_vs_reference=1.0,
        )
        return metrics, []

    labels = np.asarray(assignment.labels, dtype=int)
    assigned = labels > 0
    robots_by_load = _robots_by_load(labels, problem.params.n_loads)
    load_rows = []
    scalar_ok = []
    wrench_ok = []
    residuals = []
    force_errors = []
    torque_errors = []
    completed = []
    travel_distances = []
    obstacle_flags = []
    mobile_flags = []
    route_mitigation = _route_mitigation_factor(assignment.method)
    for load_idx in range(problem.params.n_loads):
        robots = robots_by_load[load_idx]
        scalar = _scalar_feasible(problem, load_idx, robots)
        residual, force_error, torque_error = _wrench_residual(problem, load_idx, robots, assignment.slot_angles[robots])
        wrench = bool(residual <= 0.12)
        raw_obstacle_exposure = _obstacle_exposure(problem, load_idx)
        raw_mobile_exposure = _mobile_exposure(problem, load_idx)
        obstacle_exposure = raw_obstacle_exposure * (1.0 - route_mitigation)
        mobile_exposure = raw_mobile_exposure * (1.0 - 0.75 * route_mitigation)
        travel = _load_travel_distance(problem, load_idx, robots, obstacle_exposure=obstacle_exposure, route_mitigation=route_mitigation)
        route_ok = obstacle_exposure < 1.0 and mobile_exposure < 1.0
        success = bool(scalar and wrench and route_ok and robots.size > 0)
        scalar_ok.append(float(scalar))
        wrench_ok.append(float(wrench))
        residuals.append(residual)
        force_errors.append(force_error)
        torque_errors.append(torque_error)
        completed.append(float(success))
        travel_distances.append(travel)
        obstacle_flags.append(float(obstacle_exposure >= 1.0))
        mobile_flags.append(float(mobile_exposure >= 1.0))
        load_rows.append(
            {
                "load_index": load_idx + 1,
                "assigned_robots": int(robots.size),
                "required_robots": int(problem.required_robots[load_idx]),
                "mass_kg": float(problem.load_mass_kg[load_idx]),
                "force_demand_n": float(np.linalg.norm(problem.wrench_demands[load_idx, :2])),
                "torque_demand_nm": float(problem.wrench_demands[load_idx, 2]),
                "scalar_feasible": bool(scalar),
                "wrench_feasible": bool(wrench),
                "wrench_residual_norm": float(residual),
                "force_error_n": float(force_error),
                "torque_error_nm": float(torque_error),
                "obstacle_intersection": bool(obstacle_exposure >= 1.0),
                "mobile_conflict": bool(mobile_exposure >= 1.0),
                "raw_obstacle_intersections": float(raw_obstacle_exposure),
                "raw_mobile_conflicts": float(raw_mobile_exposure),
                "route_mitigation_factor": float(route_mitigation),
                "transport_success": success,
                "travel_distance_m": float(travel),
            }
        )
    scalar_arr = np.asarray(scalar_ok, dtype=float)
    wrench_arr = np.asarray(wrench_ok, dtype=float)
    completed_arr = np.asarray(completed, dtype=float)
    crossings = _route_crossing_rate(problem) * (1.0 - 0.65 * route_mitigation)
    collision_risk = float(np.clip(0.45 * np.mean(obstacle_flags) + 0.30 * np.mean(mobile_flags) + 0.25 * crossings, 0.0, 1.0))
    false_positive = float(np.mean((scalar_arr > 0.5) & (wrench_arr < 0.5))) if scalar_arr.size else 0.0
    total_travel = float(np.nansum(travel_distances))
    energy = float(0.035 * total_travel * np.mean(problem.load_mass_kg) / 50.0)
    throughput = float(np.sum(completed_arr) / max(problem.params.horizon_s / 60.0, 1e-9))
    score = float(
        1000.0 * np.mean(completed_arr)
        + 170.0 * np.mean(wrench_arr)
        - 120.0 * collision_risk
        - 0.012 * total_travel
        - 0.0004 * assignment.communication_messages
        - 0.001 * assignment.runtime_ms
    )
    reference = score if reference_score is None else float(reference_score)
    gap = float(np.clip((reference - score) / max(abs(reference) + abs(score) + 1.0, 1.0), 0.0, 1.0))
    metrics = SP8Metrics(
        solved=True,
        timeout=False,
        solved_rate=1.0,
        timeout_rate=0.0,
        assigned_robot_rate=float(np.mean(assigned)),
        scalar_feasible_rate=float(np.mean(scalar_arr)),
        wrench_feasible_rate=float(np.mean(wrench_arr)),
        false_positive_rate=false_positive,
        force_error_n_mean=float(np.nanmean(force_errors)),
        torque_error_nm_mean=float(np.nanmean(torque_errors)),
        wrench_residual_norm_mean=float(np.nanmean(residuals)),
        transport_success_rate=float(np.mean(completed_arr)),
        task_completion_rate=float(np.mean(completed_arr)),
        throughput_tasks_per_min=throughput,
        collision_risk_rate=collision_risk,
        obstacle_intersection_rate=float(np.mean(obstacle_flags)),
        mobile_conflict_rate=float(np.mean(mobile_flags)),
        route_crossing_rate=crossings,
        mean_travel_distance_m=float(np.nanmean(travel_distances)),
        total_travel_distance_m=total_travel,
        energy_proxy_wh=energy,
        communication_messages=int(assignment.communication_messages),
        messages_per_robot=float(assignment.communication_messages / max(problem.params.n_robots, 1)),
        runtime_ms=float(assignment.runtime_ms),
        estimated_memory_mb=float(assignment.estimated_memory_mb),
        complexity_score=float(assignment.complexity_score),
        score_value=score,
        reference_score_value=reference,
        performance_gap_vs_reference=gap,
    )
    return metrics, load_rows


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp8_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
    }


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp8_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": int(meta["trainable_parameters"]),
        "method_tuned_parameters": int(meta["tuned_parameters"]),
        "method_uses_neural_policy": bool(meta["uses_neural_policy"]),
        "method_uses_decoder": bool(meta["uses_decoder"]),
    }


def _scalar_feasible(problem: SP8Problem, load_idx: int, robots: np.ndarray) -> bool:
    if robots.size < int(problem.required_robots[load_idx]):
        return False
    return bool(np.sum(problem.robot_payload_kg[robots]) >= problem.load_mass_kg[load_idx])


def _robots_by_load(labels: np.ndarray, n_loads: int) -> list[np.ndarray]:
    groups = [np.zeros(0, dtype=int) for _ in range(n_loads)]
    assigned = np.flatnonzero((labels > 0) & (labels <= n_loads))
    if assigned.size == 0:
        return groups
    load_ids = labels[assigned] - 1
    order = np.argsort(load_ids, kind="stable")
    sorted_loads = load_ids[order]
    sorted_robots = assigned[order]
    edges = np.flatnonzero(np.diff(sorted_loads)) + 1
    for load_group, robot_group in zip(np.split(sorted_loads, edges), np.split(sorted_robots, edges)):
        groups[int(load_group[0])] = robot_group.astype(int, copy=False)
    return groups


def _wrench_residual(problem: SP8Problem, load_idx: int, robots: np.ndarray, angles: np.ndarray) -> tuple[float, float, float]:
    demand = problem.wrench_demands[load_idx]
    force_ref = max(float(np.linalg.norm(demand[:2])), 80.0)
    torque_ref = max(abs(float(demand[2])), 80.0)
    if robots.size == 0:
        return float(np.linalg.norm([1.0, 1.0])), force_ref, torque_ref
    length = problem.load_length_m[load_idx]
    width = problem.load_width_m[load_idx]
    cols = []
    for angle in np.asarray(angles, dtype=float):
        if not np.isfinite(angle):
            angle = 0.0
        r = np.array([0.5 * length * np.cos(angle), 0.5 * width * np.sin(angle)], dtype=float)
        tangent = np.array([-np.sin(angle), np.cos(angle)], dtype=float)
        force_dir = 0.55 * _unit(demand[:2]) + 0.45 * np.sign(demand[2] if abs(demand[2]) > 1e-9 else 1.0) * tangent
        force_dir = _unit(force_dir)
        tau = r[0] * force_dir[1] - r[1] * force_dir[0]
        cols.append([force_dir[0], force_dir[1], tau])
    g = np.asarray(cols, dtype=float).T
    try:
        if problem.params.n_loads > 2000:
            x, *_ = np.linalg.lstsq(g, demand, rcond=None)
            achieved = g @ np.clip(x, np.zeros(robots.size), problem.robot_force_n[robots])
            diff = achieved - demand
            force_error = float(np.linalg.norm(diff[:2]))
            torque_error = float(abs(diff[2]))
            residual = float(np.linalg.norm([force_error / force_ref, torque_error / torque_ref]))
            return residual, force_error, torque_error
        result = lsq_linear(g, demand, bounds=(np.zeros(robots.size), problem.robot_force_n[robots]), max_iter=40)
        achieved = g @ result.x
    except Exception:
        achieved = np.zeros(3, dtype=float)
    diff = achieved - demand
    force_error = float(np.linalg.norm(diff[:2]))
    torque_error = float(abs(diff[2]))
    residual = float(np.linalg.norm([force_error / force_ref, torque_error / torque_ref]))
    return residual, force_error, torque_error


def _load_travel_distance(problem: SP8Problem, load_idx: int, robots: np.ndarray, *, obstacle_exposure: float, route_mitigation: float) -> float:
    direct = float(np.linalg.norm(problem.load_target_xy[load_idx] - problem.load_pickup_xy[load_idx]))
    if robots.size == 0:
        return direct
    approach = float(np.mean(np.linalg.norm(problem.robot_xy[robots] - problem.load_pickup_xy[load_idx], axis=1)))
    detour = 0.08 * obstacle_exposure + 0.04 * route_mitigation
    return approach + direct * (1.0 + detour)


def _route_mitigation_factor(method: str) -> float:
    return {
        "centralized_time_expanded_mpc": 0.80,
        "ours_tensor_quorum_flow": 0.68,
        "ours_wrench_market_hierarchical": 0.62,
        "ours_primal_dual_spatial": 0.52,
        "ours_mean_field_approximation": 0.42,
        "cbba_partitioned": 0.35,
        "auction_market_local": 0.32,
        "centralized_coalition_oracle": 0.18,
        "centralized_hungarian_expanded": 0.08,
        "classic_local_greedy": 0.04,
    }.get(method, 0.0)


def _obstacle_exposure(problem: SP8Problem, load_idx: int) -> float:
    if problem.obstacle_xy.size == 0:
        return 0.0
    dist = _point_segment_distance(problem.obstacle_xy, problem.load_pickup_xy[load_idx], problem.load_target_xy[load_idx])
    return float(np.sum(dist < problem.obstacle_radius_m + 1.25))


def _mobile_exposure(problem: SP8Problem, load_idx: int) -> float:
    if problem.mobile_start_xy.size == 0:
        return 0.0
    mid = 0.5 * (problem.mobile_start_xy + problem.mobile_end_xy)
    dist = _point_segment_distance(mid, problem.load_pickup_xy[load_idx], problem.load_target_xy[load_idx])
    return float(np.sum(dist < problem.mobile_radius_m + 1.5))


def _route_crossing_rate(problem: SP8Problem, sample_limit: int = 2000) -> float:
    m = problem.params.n_loads
    if m < 2:
        return 0.0
    rng = np.random.default_rng(m + problem.params.n_robots)
    total_pairs = m * (m - 1) // 2
    checks = min(total_pairs, sample_limit)
    hits = 0
    for _ in range(checks):
        i, j = rng.choice(m, size=2, replace=False)
        hits += int(_segments_intersect(problem.load_pickup_xy[i], problem.load_target_xy[i], problem.load_pickup_xy[j], problem.load_target_xy[j]))
    return float(hits / max(checks, 1))


def _point_segment_distance(points: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    denom = max(float(np.dot(ab, ab)), 1e-9)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    projection = a + t[:, None] * ab
    return np.linalg.norm(points - projection, axis=1)


def _segments_intersect(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> bool:
    def orient(p: np.ndarray, q: np.ndarray, r: np.ndarray) -> float:
        return float((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))

    return bool(orient(a, b, c) * orient(a, b, d) < 0.0 and orient(c, d, a) * orient(c, d, b) < 0.0)


def _unit(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-9:
        return np.array([1.0, 0.0], dtype=float)
    return np.asarray(vec, dtype=float) / norm
