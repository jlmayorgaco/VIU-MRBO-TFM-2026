"""Communication, sensing and transport metrics for SP7."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from viu_mrob_tfm.sp5.metrics import SP5Metrics, evaluate_transport
from viu_mrob_tfm.sp5.methods import SP5TrajectoryResult
from viu_mrob_tfm.sp5.scenario import SP5Problem
from viu_mrob_tfm.sp7.methods import sp7_method_metadata
from viu_mrob_tfm.sp7.scenario import CommunicationProfile


@dataclass(frozen=True, slots=True)
class NetworkFrameMetrics:
    time_s: float
    active_link_count: int
    attempted_link_count: int
    delivered_link_count: int
    largest_component_ratio: float
    component_count: int
    algebraic_connectivity: float
    coalition_connected: bool
    coalition_direct_clique: bool
    coalition_relay_connected: bool
    temporal_coalition_connected: bool
    base_connected_ratio: float
    packet_delivery_ratio: float
    mean_delay_s: float
    delay_violation_rate: float
    obstacle_detection_rate: float
    mobile_group_detection_rate: float


@dataclass(frozen=True, slots=True)
class SP7NetworkMetrics:
    communication_radius_m: float
    packet_loss_probability: float
    burst_loss_probability: float
    delay_mean_s: float
    delay_jitter_s: float
    latency_tolerance_s: float
    sensor_range_m: float
    sensor_false_negative_probability: float
    sensor_noise_std_m: float
    network_severity: float
    attempted_messages: int
    delivered_messages: int
    active_control_messages: int
    packet_delivery_ratio: float
    control_packet_ratio: float
    mean_link_delay_s: float
    delay_violation_rate: float
    mean_active_link_count: float
    mean_largest_component_ratio: float
    mean_component_count: float
    mean_algebraic_connectivity: float
    disconnected_time_ratio: float
    coalition_connected_time_ratio: float
    temporal_coalition_connected_rate: float
    relay_success_rate: float
    direct_clique_time_ratio: float
    base_connected_time_ratio: float
    communication_outage_count: int
    longest_outage_s: float
    mean_outage_duration_s: float
    obstacle_detection_rate: float
    mobile_group_detection_rate: float
    sensor_coverage_rate: float
    network_quality_score: float
    transport_network_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_sp7_run(
    problem: SP5Problem,
    result: SP5TrajectoryResult,
    profile: CommunicationProfile,
    *,
    method_id: str,
    seed: int,
    reference_result: SP5TrajectoryResult | None = None,
) -> tuple[SP5Metrics, SP7NetworkMetrics, list[NetworkFrameMetrics]]:
    """Evaluate transport plus temporal network/sensor behavior."""

    meta = sp7_method_metadata(method_id)
    transport = evaluate_transport(problem, result, reference_result=reference_result, centralized=str(meta["scope"]) == "centralized")
    frames = network_frame_metrics(problem, result, profile, seed=seed, method_id=method_id)
    network = summarize_network_metrics(frames, profile, transport)
    return transport, network, frames


def network_frame_metrics(
    problem: SP5Problem,
    result: SP5TrajectoryResult,
    profile: CommunicationProfile,
    *,
    seed: int,
    method_id: str,
) -> list[NetworkFrameMetrics]:
    rng = np.random.default_rng(_stable_seed(seed, method_id, profile.profile_id))
    positions = result.robot_positions
    n = positions.shape[1]
    assigned = np.flatnonzero(np.asarray(result.assignment.labels, dtype=int) == result.selected_load_index + 1)
    base_xy = np.zeros(2, dtype=float)
    frame_rows: list[NetworkFrameMetrics] = []
    active_graphs: list[np.ndarray] = []

    for frame_idx, frame in enumerate(positions):
        t_s = float(result.time_s[frame_idx])
        attempted = _geometric_links(frame, profile.communication_radius_m)
        attempted_count = int(np.sum(attempted))
        if _dropout_active(profile, t_s):
            delivered = np.zeros_like(attempted, dtype=bool)
            delays = np.full_like(attempted, np.nan, dtype=float)
        else:
            delivered, delays = _sample_delivery(attempted, profile, rng)
        active = delivered & (delays <= profile.latency_tolerance_s)
        active_count = int(np.sum(active))
        active_graphs.append(active)
        component_count, largest_ratio, lambda2 = _component_metrics(active)
        coalition_connected = _subset_connected(active, assigned)
        direct_clique = _subset_clique(active, assigned)
        relay_connected = bool(coalition_connected and not direct_clique and assigned.size >= 3)
        base_connected = _base_connected_ratio(frame, base_xy, active, profile.communication_radius_m)
        packet_ratio = float(np.sum(delivered) / max(attempted_count, 1))
        finite_delays = delays[np.isfinite(delays)]
        delay_violation = float(np.mean(finite_delays > profile.latency_tolerance_s)) if finite_delays.size else 0.0
        obs_rate, mobile_rate = _sensor_detection_rates(problem, result, frame_idx, profile, rng)
        frame_rows.append(
            NetworkFrameMetrics(
                time_s=t_s,
                active_link_count=active_count,
                attempted_link_count=attempted_count,
                delivered_link_count=int(np.sum(delivered)),
                largest_component_ratio=largest_ratio,
                component_count=component_count,
                algebraic_connectivity=lambda2,
                coalition_connected=coalition_connected,
                coalition_direct_clique=direct_clique,
                coalition_relay_connected=relay_connected,
                temporal_coalition_connected=False,
                base_connected_ratio=base_connected,
                packet_delivery_ratio=packet_ratio,
                mean_delay_s=float(np.mean(finite_delays)) if finite_delays.size else 0.0,
                delay_violation_rate=delay_violation,
                obstacle_detection_rate=obs_rate,
                mobile_group_detection_rate=mobile_rate,
            )
        )
    _annotate_temporal_connectivity(frame_rows, active_graphs, assigned, window=max(3, int(round(1.4 / max(problem.dt_s, 1e-9)))))
    return frame_rows


def summarize_network_metrics(frames: list[NetworkFrameMetrics], profile: CommunicationProfile, transport: SP5Metrics) -> SP7NetworkMetrics:
    attempted = int(sum(frame.attempted_link_count for frame in frames))
    delivered = int(sum(frame.delivered_link_count for frame in frames))
    active = int(sum(frame.active_link_count for frame in frames))
    delays = np.asarray([frame.mean_delay_s for frame in frames if frame.delivered_link_count > 0], dtype=float)
    connected = np.asarray([float(frame.coalition_connected) for frame in frames], dtype=float)
    temporal = np.asarray([float(frame.temporal_coalition_connected) for frame in frames], dtype=float)
    outages = _outage_durations(connected, dt_s=_dt_from_frames(frames))
    packet_ratio = float(delivered / max(attempted, 1))
    control_ratio = float(active / max(attempted, 1))
    coalition_connected = float(np.mean(connected)) if connected.size else 0.0
    temporal_rate = float(np.mean(temporal)) if temporal.size else 0.0
    relay_rate = _mean(frames, "coalition_relay_connected")
    direct_rate = _mean(frames, "coalition_direct_clique")
    obstacle_rate = _mean(frames, "obstacle_detection_rate")
    mobile_rate = _mean(frames, "mobile_group_detection_rate")
    network_quality = float(
        np.clip(
            0.25 * packet_ratio
            + 0.25 * control_ratio
            + 0.22 * coalition_connected
            + 0.14 * temporal_rate
            + 0.08 * obstacle_rate
            + 0.06 * mobile_rate,
            0.0,
            1.0,
        )
    )
    transport_score = float(
        np.clip(
            0.38 * float(transport.transport_success)
            + 0.22 * float(transport.target_reached)
            + 0.16 * transport.formation_integrity_rate
            + 0.14 * network_quality
            + 0.10 * max(0.0, 1.0 - transport.collision_rate),
            0.0,
            1.0,
        )
    )
    return SP7NetworkMetrics(
        communication_radius_m=float(profile.communication_radius_m),
        packet_loss_probability=float(profile.packet_loss_probability),
        burst_loss_probability=float(profile.burst_loss_probability),
        delay_mean_s=float(profile.delay_mean_s),
        delay_jitter_s=float(profile.delay_jitter_s),
        latency_tolerance_s=float(profile.latency_tolerance_s),
        sensor_range_m=float(profile.sensor_range_m),
        sensor_false_negative_probability=float(profile.sensor_false_negative_probability),
        sensor_noise_std_m=float(profile.sensor_noise_std_m),
        network_severity=profile.severity(),
        attempted_messages=attempted,
        delivered_messages=delivered,
        active_control_messages=active,
        packet_delivery_ratio=packet_ratio,
        control_packet_ratio=control_ratio,
        mean_link_delay_s=float(np.mean(delays)) if delays.size else 0.0,
        delay_violation_rate=_mean(frames, "delay_violation_rate"),
        mean_active_link_count=_mean(frames, "active_link_count"),
        mean_largest_component_ratio=_mean(frames, "largest_component_ratio"),
        mean_component_count=_mean(frames, "component_count"),
        mean_algebraic_connectivity=_mean(frames, "algebraic_connectivity"),
        disconnected_time_ratio=1.0 - coalition_connected,
        coalition_connected_time_ratio=coalition_connected,
        temporal_coalition_connected_rate=temporal_rate,
        relay_success_rate=relay_rate,
        direct_clique_time_ratio=direct_rate,
        base_connected_time_ratio=_mean(frames, "base_connected_ratio"),
        communication_outage_count=len(outages),
        longest_outage_s=float(max(outages)) if outages else 0.0,
        mean_outage_duration_s=float(np.mean(outages)) if outages else 0.0,
        obstacle_detection_rate=obstacle_rate,
        mobile_group_detection_rate=mobile_rate,
        sensor_coverage_rate=0.5 * (obstacle_rate + mobile_rate),
        network_quality_score=network_quality,
        transport_network_score=transport_score,
    )


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp7_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
        "method_communication_dependency": str(meta["communication_dependency"]),
    }


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp7_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": int(meta["trainable_parameters"]),
        "method_tuned_parameters": int(meta["tuned_parameters"]),
        "method_uses_neural_policy": bool(meta["uses_neural_policy"]),
        "method_uses_decoder": bool(meta["uses_decoder"]),
    }


def frame_rows(
    experiment_id: str,
    scenario_generator: str,
    scenario_variant_id: str,
    seed: int,
    method: str,
    profile_id: str,
    frames: list[NetworkFrameMetrics],
    *,
    max_frames: int = 90,
) -> list[dict[str, Any]]:
    if not frames:
        return []
    stride = max(1, int(np.ceil(len(frames) / max(max_frames, 1))))
    rows = []
    for frame in frames[::stride]:
        row = asdict(frame)
        row["temporal_coalition_connected"] = bool(frame.temporal_coalition_connected)
        rows.append(
            {
                "experiment_id": experiment_id,
                "scenario_generator": scenario_generator,
                "scenario_variant_id": scenario_variant_id,
                "seed": seed,
                "method": method,
                "communication_profile": profile_id,
                **row,
            }
        )
    return rows


def _geometric_links(frame: np.ndarray, radius: float) -> np.ndarray:
    n = frame.shape[0]
    if n <= 1:
        return np.zeros((n, n), dtype=bool)
    distances = np.linalg.norm(frame[:, None, :] - frame[None, :, :], axis=2)
    links = distances <= float(radius) if np.isfinite(radius) else np.ones((n, n), dtype=bool)
    np.fill_diagonal(links, False)
    return links


def _sample_delivery(attempted: np.ndarray, profile: CommunicationProfile, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    loss_probability = np.clip(profile.packet_loss_probability + profile.burst_loss_probability * rng.random(), 0.0, 1.0)
    delivered = attempted & (rng.random(attempted.shape) >= loss_probability)
    delays = np.full(attempted.shape, np.nan, dtype=float)
    raw = rng.normal(profile.delay_mean_s, max(profile.delay_jitter_s, 1e-9), size=attempted.shape)
    delays[delivered] = np.maximum(0.0, raw[delivered])
    return delivered, delays


def _dropout_active(profile: CommunicationProfile, t_s: float) -> bool:
    if profile.dropout_period_s <= 0.0 or profile.dropout_duration_s <= 0.0:
        return False
    return float(t_s % profile.dropout_period_s) <= profile.dropout_duration_s


def _component_metrics(adj: np.ndarray) -> tuple[int, float, float]:
    n = adj.shape[0]
    if n == 0:
        return 0, 0.0, 0.0
    visited = np.zeros(n, dtype=bool)
    sizes = []
    for start in range(n):
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        size = 0
        while stack:
            node = stack.pop()
            size += 1
            for nxt in np.flatnonzero(adj[node]):
                if not visited[int(nxt)]:
                    visited[int(nxt)] = True
                    stack.append(int(nxt))
        sizes.append(size)
    degree = np.diag(np.sum(adj.astype(float), axis=1))
    laplacian = degree - adj.astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian) if n > 1 else np.array([0.0])
    lambda2 = float(eigenvalues[1]) if eigenvalues.size > 1 else 0.0
    return len(sizes), float(max(sizes) / max(n, 1)), lambda2


def _subset_connected(adj: np.ndarray, subset: np.ndarray) -> bool:
    if subset.size <= 1:
        return bool(subset.size == 1)
    subset = subset.astype(int)
    allowed = set(int(i) for i in subset)
    start = int(subset[0])
    visited = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for nxt in np.flatnonzero(adj[node]):
            nxt = int(nxt)
            if nxt in allowed and nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return len(visited) == len(allowed)


def _subset_clique(adj: np.ndarray, subset: np.ndarray) -> bool:
    if subset.size <= 1:
        return bool(subset.size == 1)
    sub = adj[np.ix_(subset, subset)]
    return bool(np.all(sub | np.eye(sub.shape[0], dtype=bool)))


def _base_connected_ratio(frame: np.ndarray, base_xy: np.ndarray, adj: np.ndarray, radius: float) -> float:
    n = frame.shape[0]
    if n == 0:
        return 0.0
    base_links = np.linalg.norm(frame - base_xy[None, :], axis=1) <= (radius if np.isfinite(radius) else np.inf)
    if np.any(base_links):
        connected = set(int(i) for i in np.flatnonzero(base_links))
        stack = list(connected)
        while stack:
            node = stack.pop()
            for nxt in np.flatnonzero(adj[node]):
                nxt = int(nxt)
                if nxt not in connected:
                    connected.add(nxt)
                    stack.append(nxt)
        return float(len(connected) / n)
    return 0.0


def _sensor_detection_rates(problem: SP5Problem, result: SP5TrajectoryResult, frame_idx: int, profile: CommunicationProfile, rng: np.random.Generator) -> tuple[float, float]:
    robots = result.robot_positions[frame_idx]
    t_s = float(result.time_s[frame_idx])
    obstacle_required = 0
    obstacle_detected = 0
    for obstacle in problem.world.map.obstacles:
        distances = np.linalg.norm(robots - obstacle.center[None, :], axis=1) + rng.normal(0.0, profile.sensor_noise_std_m, size=robots.shape[0])
        near = distances <= profile.sensor_range_m + obstacle.influence_radius
        obstacle_required += int(np.sum(near))
        obstacle_detected += int(np.sum(near & (rng.random(robots.shape[0]) >= profile.sensor_false_negative_probability)))
    mobile_required = 0
    mobile_detected = 0
    for group in problem.mobile_groups:
        center = group.center_at(t_s, problem.horizon_s)
        distances = np.linalg.norm(robots - center[None, :], axis=1) + rng.normal(0.0, profile.sensor_noise_std_m, size=robots.shape[0])
        near = distances <= profile.sensor_range_m + group.influence_radius_m
        mobile_required += int(np.sum(near))
        mobile_detected += int(np.sum(near & (rng.random(robots.shape[0]) >= profile.sensor_false_negative_probability)))
    return (
        float(obstacle_detected / max(obstacle_required, 1)),
        float(mobile_detected / max(mobile_required, 1)),
    )


def _annotate_temporal_connectivity(frames: list[NetworkFrameMetrics], graphs: list[np.ndarray], subset: np.ndarray, *, window: int) -> None:
    for idx, frame in enumerate(frames):
        start = max(0, idx - window + 1)
        if graphs:
            union = np.zeros_like(graphs[idx], dtype=bool)
            for graph in graphs[start : idx + 1]:
                union |= graph
            temporal = _subset_connected(union, subset)
        else:
            temporal = False
        object.__setattr__(frame, "temporal_coalition_connected", temporal)


def _outage_durations(connected: np.ndarray, *, dt_s: float) -> list[float]:
    durations = []
    current = 0
    for value in connected:
        if value < 0.5:
            current += 1
        elif current > 0:
            durations.append(current * dt_s)
            current = 0
    if current > 0:
        durations.append(current * dt_s)
    return durations


def _dt_from_frames(frames: list[NetworkFrameMetrics]) -> float:
    if len(frames) < 2:
        return 0.0
    return float(max(frames[1].time_s - frames[0].time_s, 0.0))


def _mean(frames: list[NetworkFrameMetrics], field: str) -> float:
    values = np.asarray([float(getattr(frame, field)) for frame in frames], dtype=float)
    return float(np.mean(values)) if values.size else math.nan


def _stable_seed(seed: int, method: str, profile: str) -> int:
    text = f"{seed}:{method}:{profile}"
    value = 0
    for char in text:
        value = (value * 131 + ord(char)) % (2**32 - 1)
    return int(value)
