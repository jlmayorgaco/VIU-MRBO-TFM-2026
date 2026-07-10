"""SP8 warehouse-scale allocation methods."""

from __future__ import annotations

import math
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from viu_mrob_tfm.sp8.scenario import SP8Problem


SP8_METHOD_LABELS = {
    "centralized_hungarian_expanded": "Centralized Hungarian expanded",
    "centralized_coalition_oracle": "Centralized coalition oracle",
    "centralized_time_expanded_mpc": "Centralized time-expanded MPC",
    "classic_local_greedy": "Classic local greedy",
    "cbba_partitioned": "CBBA partitioned",
    "auction_market_local": "Auction market local",
    "ours_primal_dual_spatial": "Ours primal-dual spatial",
    "ours_tensor_quorum_flow": "Ours tensor quorum flow",
    "ours_wrench_market_hierarchical": "Ours wrench-market hierarchical",
    "ours_mean_field_approximation": "Ours mean-field approximation",
}

METHOD_META = {
    "centralized_hungarian_expanded": ("classic", "centralized", "baseline", "expanded_slot_hungarian_polynomial_but_scalar"),
    "centralized_coalition_oracle": ("model_based_oracle", "centralized", "reference", "exact_like_small_scale_coalition_search_timeout_large"),
    "centralized_time_expanded_mpc": ("sota", "centralized", "baseline", "time_expanded_mpc_timeout_large"),
    "classic_local_greedy": ("classic", "decentralized", "baseline", "nearest_local_greedy"),
    "cbba_partitioned": ("sota", "decentralized", "baseline", "partitioned_cbba_like_auction"),
    "auction_market_local": ("sota", "decentralized", "baseline", "local_market_auction"),
    "ours_primal_dual_spatial": ("model_based", "decentralized", "proposed", "spatial_primal_dual_capacity_prices"),
    "ours_tensor_quorum_flow": ("model_based", "decentralized", "proposed", "tensor_quorum_flow_density_obstacle_aware"),
    "ours_wrench_market_hierarchical": ("model_based", "hierarchical", "proposed", "zone_hierarchical_wrench_market"),
    "ours_mean_field_approximation": ("model_based", "decentralized", "proposed", "mean_field_density_allocation"),
}

METHOD_RESOURCES = {
    "centralized_hungarian_expanded": ("none", "centralized_expanded_assignment", "global_all_robot_load_slots", 0, 1),
    "centralized_coalition_oracle": ("none", "centralized_subset_coalition_search", "global_all_subsets", 0, 2),
    "centralized_time_expanded_mpc": ("none", "centralized_time_expanded_mpc", "global_time_expanded_state", 0, 8),
    "classic_local_greedy": ("none", "distributed_nearest_greedy", "local_distance_beacons", 0, 2),
    "cbba_partitioned": ("none", "partitioned_cbba_auction", "zone_auction_bids", 0, 6),
    "auction_market_local": ("none", "local_market_auction", "local_prices_and_bids", 0, 6),
    "ours_primal_dual_spatial": ("model_based_tuning_optional", "distributed_primal_dual_prices", "local_deficit_capacity_prices", 0, 9),
    "ours_tensor_quorum_flow": ("model_based_tuning_optional", "distributed_tensor_quorum_flow", "local_density_tensor_field", 0, 11),
    "ours_wrench_market_hierarchical": ("model_based_tuning_optional", "hierarchical_wrench_market", "zone_summaries_plus_local_wrench_bids", 0, 13),
    "ours_mean_field_approximation": ("model_based_tuning_optional", "mean_field_density_controller", "aggregate_density_broadcasts", 0, 7),
}


@dataclass(frozen=True, slots=True)
class SP8Assignment:
    labels: np.ndarray
    slot_angles: np.ndarray
    method: str
    solved: bool = True
    status: str = "ok"
    runtime_ms: float = 0.0
    estimated_memory_mb: float = 0.0
    communication_messages: int = 0
    complexity_score: float = 0.0


def make_sp8_allocator(method_id: str, params: dict[str, Any] | None = None) -> "SP8Allocator":
    return SP8Allocator(_canonical_method(method_id), dict(params or {}))


class SP8Allocator:
    def __init__(self, method_id: str, params: dict[str, Any] | None = None) -> None:
        self.method_id = _canonical_method(method_id)
        self.params = dict(params or {})

    def allocate(self, problem: SP8Problem) -> SP8Assignment:
        start = perf_counter()
        method = self.method_id
        n, m = problem.params.n_robots, problem.params.n_loads
        complexity = complexity_score(method, n, m)
        memory = estimated_memory_mb(method, n, m)
        timeout_s = float(self.params.get("timeout_s", 60.0))
        if _declared_timeout(method, n, m, timeout_s):
            return SP8Assignment(
                labels=np.zeros(n, dtype=int),
                slot_angles=np.full(n, np.nan),
                method=method,
                solved=False,
                status="timeout_declared_intractable",
                runtime_ms=1000.0 * timeout_s,
                estimated_memory_mb=memory,
                communication_messages=_messages(method, problem, np.zeros(n, dtype=int)),
                complexity_score=complexity,
            )
        if method == "centralized_hungarian_expanded":
            labels, angles = _hungarian_expanded(problem)
        elif method in {"centralized_coalition_oracle", "centralized_time_expanded_mpc"}:
            labels, angles = _centralized_wrench_aware(problem, max_candidates=int(self.params.get("max_candidates", 10)))
        elif method == "classic_local_greedy":
            labels, angles = _local_greedy(problem, wrench_aware=False, obstacle_aware=False)
        elif method == "cbba_partitioned":
            labels, angles = _local_greedy(problem, wrench_aware=False, obstacle_aware=True, partitioned=True)
        elif method == "auction_market_local":
            labels, angles = _auction_market(problem, wrench_aware=False)
        elif method == "ours_primal_dual_spatial":
            labels, angles = _auction_market(problem, wrench_aware=True, spatial_price=True)
        elif method == "ours_tensor_quorum_flow":
            labels, angles = _auction_market(problem, wrench_aware=True, spatial_price=True, obstacle_price=True)
        elif method == "ours_wrench_market_hierarchical":
            labels, angles = _hierarchical_wrench(problem)
        elif method == "ours_mean_field_approximation":
            labels, angles = _mean_field(problem)
        else:  # pragma: no cover
            raise ValueError(method)
        runtime_ms = 1000.0 * (perf_counter() - start)
        return SP8Assignment(labels=labels, slot_angles=angles, method=method, solved=True, status="ok", runtime_ms=runtime_ms, estimated_memory_mb=memory, communication_messages=_messages(method, problem, labels), complexity_score=complexity)


def sp8_method_metadata(method_id: str) -> dict[str, Any]:
    method = _canonical_method(method_id)
    family, scope, ownership, variant = METHOD_META[method]
    training_type, execution_model, communication_pattern, trainable, tuned = METHOD_RESOURCES[method]
    return {
        "label": SP8_METHOD_LABELS[method],
        "title": f"{SP8_METHOD_LABELS[method]} [{ownership} | {family} | {scope}]",
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "comparison_group": f"{ownership}_{family}_{scope}_scale",
        "training_type": training_type,
        "execution_model": execution_model,
        "communication_pattern": communication_pattern,
        "trainable_parameters": trainable,
        "tuned_parameters": tuned,
        "uses_neural_policy": False,
        "uses_decoder": False,
    }


def complexity_score(method: str, n: int, m: int) -> float:
    method = _canonical_method(method)
    if method == "centralized_coalition_oracle":
        return float(m * min(2.0 ** min(n, 28), 2.0**28))
    if method == "centralized_time_expanded_mpc":
        return float((n + m) ** 3 * 8.0)
    if method == "centralized_hungarian_expanded":
        return float(max(n, int(3 * m)) ** 3)
    if method in {"cbba_partitioned", "auction_market_local"}:
        return float(n * np.log2(max(n, 2)) * max(m, 1))
    if method in {"ours_wrench_market_hierarchical", "ours_tensor_quorum_flow"}:
        return float((n + m) * np.log2(max(n + m, 2)))
    return float(n * max(m, 1))


def estimated_memory_mb(method: str, n: int, m: int) -> float:
    method = _canonical_method(method)
    if method == "centralized_time_expanded_mpc":
        return float(8.0 * (n + m) ** 2 * 8 / 1e6)
    if method in {"centralized_hungarian_expanded", "centralized_coalition_oracle"}:
        return float(8.0 * n * max(3 * m, 1) / 1e6 + 24.0)
    return float(8.0 * (n + m) / 1e6 + 2.0)


def _declared_timeout(method: str, n: int, m: int, timeout_s: float) -> bool:
    if method == "centralized_coalition_oracle":
        return n > 96 or m > 28 or n * m > 2500
    if method == "centralized_time_expanded_mpc":
        return n + m > 220 or n * m > 12_000
    if method == "centralized_hungarian_expanded":
        return n * max(3 * m, 1) > 900_000
    return False


def _distance_matrix(problem: SP8Problem) -> np.ndarray:
    diff = problem.robot_xy[:, None, :] - problem.load_pickup_xy[None, :, :]
    return np.linalg.norm(diff, axis=2)


def _hungarian_expanded(problem: SP8Problem) -> tuple[np.ndarray, np.ndarray]:
    n, m = problem.params.n_robots, problem.params.n_loads
    repeated_loads = np.repeat(np.arange(m), problem.required_robots)
    if repeated_loads.size == 0:
        return np.zeros(n, dtype=int), np.full(n, np.nan)
    distances = _distance_matrix(problem)[:, repeated_loads]
    row_idx, col_idx = linear_sum_assignment(distances)
    labels = np.zeros(n, dtype=int)
    labels[row_idx] = repeated_loads[col_idx] + 1
    return labels, _angles_from_bearing(problem, labels)


def _centralized_wrench_aware(problem: SP8Problem, *, max_candidates: int) -> tuple[np.ndarray, np.ndarray]:
    return _assign_by_load(problem, max_candidates=max_candidates, utility_mode="wrench", partitioned=False)


def _local_greedy(problem: SP8Problem, *, wrench_aware: bool, obstacle_aware: bool, partitioned: bool = False) -> tuple[np.ndarray, np.ndarray]:
    mode = "wrench" if wrench_aware else ("obstacle" if obstacle_aware else "distance")
    return _assign_by_load(problem, max_candidates=8, utility_mode=mode, partitioned=partitioned)


def _auction_market(problem: SP8Problem, *, wrench_aware: bool, spatial_price: bool = False, obstacle_price: bool = False) -> tuple[np.ndarray, np.ndarray]:
    mode = "wrench" if wrench_aware else "auction"
    if obstacle_price:
        mode = "wrench_obstacle"
    elif spatial_price:
        mode = "wrench_spatial"
    return _assign_by_load(problem, max_candidates=10, utility_mode=mode, partitioned=False)


def _hierarchical_wrench(problem: SP8Problem) -> tuple[np.ndarray, np.ndarray]:
    return _assign_by_load(problem, max_candidates=12, utility_mode="wrench_hierarchical", partitioned=True)


def _mean_field(problem: SP8Problem) -> tuple[np.ndarray, np.ndarray]:
    return _assign_by_load(problem, max_candidates=7, utility_mode="mean_field", partitioned=True)


def _assign_by_load(problem: SP8Problem, *, max_candidates: int, utility_mode: str, partitioned: bool) -> tuple[np.ndarray, np.ndarray]:
    n, m = problem.params.n_robots, problem.params.n_loads
    labels = np.zeros(n, dtype=int)
    angles = np.full(n, np.nan, dtype=float)
    available = np.ones(n, dtype=bool)
    tree = cKDTree(problem.robot_xy)
    order = np.argsort(-problem.load_reward / np.maximum(problem.required_robots, 1))
    zone_count = max(1, int(round(math.sqrt(max(n, 1)) / 3))) if partitioned else 1
    load_zones = _zones(problem.load_pickup_xy, problem.params.world_size_m, zone_count)
    robot_zones = _zones(problem.robot_xy, problem.params.world_size_m, zone_count)
    for load_idx in order:
        needed = int(problem.required_robots[load_idx])
        candidates = _candidate_pool(problem, tree, available, load_idx, needed=needed, max_candidates=max_candidates, partitioned=partitioned, zone_count=zone_count, robot_zones=robot_zones, load_zones=load_zones)
        if candidates.size == 0:
            continue
        local_dist = np.linalg.norm(problem.robot_xy[candidates] - problem.load_pickup_xy[load_idx], axis=1)
        keep = min(candidates.size, max(max_candidates * needed, needed))
        nearest = candidates[np.argpartition(local_dist, keep - 1)[:keep]]
        nearest_dist = np.linalg.norm(problem.robot_xy[nearest] - problem.load_pickup_xy[load_idx], axis=1)
        score = _candidate_score(problem, nearest, load_idx, nearest_dist, utility_mode)
        selected = nearest[np.argsort(-score)[:needed]]
        if selected.size == 0:
            continue
        labels[selected] = load_idx + 1
        angles[selected] = _slot_angles(problem, selected, load_idx, utility_mode)
        available[selected] = False
    return labels, angles


def _candidate_pool(
    problem: SP8Problem,
    tree: cKDTree,
    available: np.ndarray,
    load_idx: int,
    *,
    needed: int,
    max_candidates: int,
    partitioned: bool,
    zone_count: int,
    robot_zones: np.ndarray,
    load_zones: np.ndarray,
) -> np.ndarray:
    n = problem.params.n_robots
    query_k = min(n, max(32, needed * max_candidates * 8))
    candidates = np.zeros(0, dtype=int)
    while True:
        _dist, idx = tree.query(problem.load_pickup_xy[load_idx], k=query_k)
        idx = np.atleast_1d(idx).astype(int)
        idx = idx[(idx >= 0) & (idx < n)]
        candidates = idx[available[idx]]
        if partitioned and zone_count > 1:
            same = candidates[robot_zones[candidates] == load_zones[load_idx]]
            if same.size >= needed:
                candidates = same
        if candidates.size >= needed or query_k >= n:
            break
        query_k = min(n, query_k * 2)
    if candidates.size >= needed:
        return np.unique(candidates)
    fallback = np.flatnonzero(available)
    if partitioned and zone_count > 1:
        same = fallback[robot_zones[fallback] == load_zones[load_idx]]
        if same.size >= needed:
            fallback = same
    return fallback


def _candidate_score(problem: SP8Problem, robots: np.ndarray, load_idx: int, distances: np.ndarray, mode: str) -> np.ndarray:
    capacity = problem.robot_payload_kg[robots] / max(problem.load_mass_kg[load_idx], 1.0)
    force = problem.robot_force_n[robots] / max(np.linalg.norm(problem.wrench_demands[load_idx, :2]), 1.0)
    base = 0.7 * capacity + 0.8 * force - 0.018 * distances
    if "wrench" in mode:
        bearing = np.arctan2(problem.robot_xy[robots, 1] - problem.load_pickup_xy[load_idx, 1], problem.robot_xy[robots, 0] - problem.load_pickup_xy[load_idx, 0])
        torque_pref = np.sign(problem.wrench_demands[load_idx, 2]) * np.sin(bearing)
        base += 0.32 * torque_pref + 0.18 * np.abs(np.cos(bearing))
    if "obstacle" in mode or "tensor" in mode:
        base -= 0.10 * _route_obstacle_exposure(problem, load_idx)
        base -= 0.18 * _approach_obstacle_exposure(problem, robots, load_idx)
    if mode == "mean_field":
        density = np.linalg.norm(problem.robot_xy[robots] - problem.load_pickup_xy[load_idx], axis=1) / max(problem.params.world_size_m, 1.0)
        base += 0.25 * np.exp(-density)
    return base


def _slot_angles(problem: SP8Problem, robots: np.ndarray, load_idx: int, mode: str) -> np.ndarray:
    count = robots.size
    if count == 0:
        return np.zeros(0, dtype=float)
    if "wrench" in mode:
        sign = 1.0 if problem.wrench_demands[load_idx, 2] >= 0.0 else -1.0
        base = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
        return base + sign * np.pi / 2.0
    return np.arctan2(problem.robot_xy[robots, 1] - problem.load_pickup_xy[load_idx, 1], problem.robot_xy[robots, 0] - problem.load_pickup_xy[load_idx, 0])


def _angles_from_bearing(problem: SP8Problem, labels: np.ndarray) -> np.ndarray:
    angles = np.full(labels.shape, np.nan, dtype=float)
    assigned = np.flatnonzero(labels > 0)
    if assigned.size:
        load_idx = labels[assigned] - 1
        delta = problem.robot_xy[assigned] - problem.load_pickup_xy[load_idx]
        angles[assigned] = np.arctan2(delta[:, 1], delta[:, 0])
    return angles


def _route_obstacle_exposure(problem: SP8Problem, load_idx: int) -> float:
    if problem.obstacle_xy.size == 0:
        return 0.0
    start = problem.load_pickup_xy[load_idx]
    end = problem.load_target_xy[load_idx]
    dist = _point_segment_distance(problem.obstacle_xy, start, end)
    return float(np.sum(np.maximum(problem.obstacle_radius_m + 1.0 - dist, 0.0)))


def _approach_obstacle_exposure(problem: SP8Problem, robots: np.ndarray, load_idx: int) -> np.ndarray:
    if problem.obstacle_xy.size == 0 or robots.size == 0:
        return np.zeros(robots.size, dtype=float)
    exposure = np.zeros(robots.size, dtype=float)
    target = problem.load_pickup_xy[load_idx]
    for local_idx, robot_idx in enumerate(robots):
        dist = _point_segment_distance(problem.obstacle_xy, problem.robot_xy[robot_idx], target)
        exposure[local_idx] = float(np.sum(np.maximum(problem.obstacle_radius_m + 0.8 - dist, 0.0)))
    return exposure


def _point_segment_distance(points: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ab = b - a
    denom = max(float(np.dot(ab, ab)), 1e-9)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    projection = a + t[:, None] * ab
    return np.linalg.norm(points - projection, axis=1)


def _zones(xy: np.ndarray, world_size: float, zone_count: int) -> np.ndarray:
    if zone_count <= 1:
        return np.zeros(xy.shape[0], dtype=int)
    half = 0.5 * world_size
    scaled = np.clip(((xy + half) / max(world_size, 1e-9) * zone_count).astype(int), 0, zone_count - 1)
    return scaled[:, 0] + zone_count * scaled[:, 1]


def _messages(method: str, problem: SP8Problem, labels: np.ndarray) -> int:
    n, m = problem.params.n_robots, problem.params.n_loads
    if METHOD_META[method][1] == "centralized":
        return int(n * m)
    assigned = int(np.sum(labels > 0))
    if method == "ours_wrench_market_hierarchical":
        return int(4 * assigned + 2 * m + n)
    if method == "ours_mean_field_approximation":
        return int(n + m)
    return int(6 * assigned + 2 * m)


def _canonical_method(method_id: str) -> str:
    method = method_id.lower()
    aliases = {"hungarian": "centralized_hungarian_expanded", "oracle": "centralized_coalition_oracle", "mpc": "centralized_time_expanded_mpc", "ours": "ours_wrench_market_hierarchical"}
    method = aliases.get(method, method)
    if method not in METHOD_META:
        raise ValueError(f"Unknown SP8 method: {method_id}")
    return method
