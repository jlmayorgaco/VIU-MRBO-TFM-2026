"""SP7 communication-aware method registry."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from viu_mrob_tfm.sp5.methods import SP5TransportPolicy, make_sp5_policy, sp5_method_metadata
from viu_mrob_tfm.sp7.scenario import CommunicationProfile


SP7_METHOD_LABELS = {
    "classic_centralized_global_mpc": "Classic centralized global comms",
    "classic_decentralized_sensor_apf": "Classic decentralized sensor APF",
    "sota_centralized_cbf_networked": "SOTA centralized CBF networked",
    "sota_decentralized_cbba_relay": "SOTA decentralized relay/CBBA",
    "sota_delay_tolerant_consensus": "SOTA delay-tolerant consensus",
    "ours_connectivity_wrench_game": "Ours connectivity-aware wrench game",
    "ours_delay_robust_repair": "Ours delay-robust local repair",
    "reference_full_communication": "Reference full-communication controller",
}

METHOD_META = {
    "classic_centralized_global_mpc": ("classic", "centralized", "baseline", "global_state_controller_sensitive_to_network", "high"),
    "classic_decentralized_sensor_apf": ("classic", "decentralized", "baseline", "local_sensor_apf_low_comm", "low"),
    "sota_centralized_cbf_networked": ("sota", "centralized", "baseline", "networked_cbf_with_global_traffic", "high"),
    "sota_decentralized_cbba_relay": ("sota", "decentralized", "baseline", "event_triggered_cbba_relay", "medium"),
    "sota_delay_tolerant_consensus": ("sota", "decentralized", "baseline", "delay_tolerant_consensus_transport", "medium"),
    "ours_connectivity_wrench_game": ("model_based", "decentralized", "proposed", "connectivity_aware_wrench_market_game", "low"),
    "ours_delay_robust_repair": ("model_based", "decentralized_local", "proposed", "delay_robust_wrench_repair_guard", "low"),
    "reference_full_communication": ("model_based_reference", "centralized", "reference", "full_information_upper_reference", "high"),
}

METHOD_RESOURCES = {
    "classic_centralized_global_mpc": ("none", "centralized_controller_with_global_state_stream", "all_to_base_low_latency_required", 0, 4, False, False),
    "classic_decentralized_sensor_apf": ("none", "distributed_local_sensor_apf", "local_sensing_only_optional_neighbor_beacons", 0, 3, False, False),
    "sota_centralized_cbf_networked": ("none", "centralized_cbf_with_networked_state_estimation", "all_robot_payload_traffic_streams", 0, 7, False, False),
    "sota_decentralized_cbba_relay": ("none", "distributed_cbba_relay_with_velocity_obstacle_transport", "auction_bids_plus_neighbor_relay", 0, 8, False, False),
    "sota_delay_tolerant_consensus": ("none", "distributed_consensus_with_delay_margin", "neighbor_consensus_packets", 0, 8, False, False),
    "ours_connectivity_wrench_game": ("model_based_tuning_optional", "distributed_wrench_game_with_connectivity_pressure", "local_wrench_residual_plus_link_quality_prices", 0, 11, False, False),
    "ours_delay_robust_repair": ("model_based_tuning_optional", "distributed_local_repair_with_delay_guard", "event_triggered_local_repair_and_relay_selection", 0, 12, False, False),
    "reference_full_communication": ("none", "centralized_reference_full_information", "global_lossless_network", 0, 10, False, False),
}


def make_sp7_policy(
    method_id: str,
    profile: CommunicationProfile,
    *,
    transport_mode: str,
    params: dict[str, Any] | None = None,
) -> SP5TransportPolicy:
    """Instantiate a communication-aware SP5 transport policy."""

    method = _canonical_method(method_id)
    params = dict(params or {})
    sp5_method = _sp5_method_for(method, transport_mode)
    base = make_sp5_policy(sp5_method, params)
    cfg = base.config
    severity = profile.severity()
    dependence = _dependence(method)
    sensor_quality = max(0.35, 1.0 - profile.sensor_false_negative_probability - 0.75 * profile.sensor_noise_std_m)
    comm_quality = max(0.25, 1.0 - dependence * severity)

    if method == "reference_full_communication":
        comm_quality = 1.0 if profile.profile_id == "nominal_full_mesh" else max(0.68, comm_quality)
    if method in {"ours_connectivity_wrench_game", "ours_delay_robust_repair"}:
        cfg = replace(
            cfg,
            formation_gain=cfg.formation_gain * (0.96 + 0.18 * (1.0 - severity)),
            obstacle_gain=max(cfg.obstacle_gain, 0.54) * max(0.76, sensor_quality),
            mobile_gain=max(cfg.mobile_gain, 0.68) * max(0.76, sensor_quality),
            robot_gain=max(cfg.robot_gain, 0.22),
            speed_scale=cfg.speed_scale * max(0.74, 1.0 - 0.18 * severity),
        )
    elif method == "classic_decentralized_sensor_apf":
        cfg = replace(
            cfg,
            formation_gain=cfg.formation_gain * max(0.62, 1.0 - 0.22 * severity),
            obstacle_gain=cfg.obstacle_gain * sensor_quality,
            mobile_gain=cfg.mobile_gain * sensor_quality,
            speed_scale=cfg.speed_scale * max(0.72, 1.0 - 0.16 * severity),
        )
    else:
        cfg = replace(
            cfg,
            pose_gain=cfg.pose_gain * comm_quality,
            theta_gain=cfg.theta_gain * comm_quality,
            formation_gain=cfg.formation_gain * max(0.52, comm_quality),
            obstacle_gain=cfg.obstacle_gain * max(0.55, sensor_quality),
            mobile_gain=cfg.mobile_gain * max(0.55, sensor_quality),
            speed_scale=cfg.speed_scale * max(0.55, comm_quality),
        )
    return SP5TransportPolicy(sp5_method, cfg, base.allocator_params)


def sp7_method_metadata(method_id: str) -> dict[str, Any]:
    method = _canonical_method(method_id)
    family, scope, ownership, variant, comm_dependency = METHOD_META[method]
    training_type, execution_model, communication_pattern, trainable, tuned, uses_neural, uses_decoder = METHOD_RESOURCES[method]
    return {
        "label": SP7_METHOD_LABELS[method],
        "title": f"{SP7_METHOD_LABELS[method]} [{ownership} | {family} | {scope} | comm={comm_dependency}]",
        "family": family,
        "scope": scope,
        "ownership": ownership,
        "variant": variant,
        "communication_dependency": comm_dependency,
        "comparison_group": f"{ownership}_{family}_{scope}_{comm_dependency}_communication",
        "training_type": training_type,
        "execution_model": execution_model,
        "communication_pattern": communication_pattern,
        "trainable_parameters": trainable,
        "tuned_parameters": tuned,
        "uses_neural_policy": uses_neural,
        "uses_decoder": uses_decoder,
    }


def _canonical_method(method_id: str) -> str:
    method = method_id.lower()
    aliases = {
        "centralized": "classic_centralized_global_mpc",
        "sensor_apf": "classic_decentralized_sensor_apf",
        "cbba_relay": "sota_decentralized_cbba_relay",
        "ours": "ours_connectivity_wrench_game",
        "reference": "reference_full_communication",
    }
    method = aliases.get(method, method)
    if method not in METHOD_META:
        raise ValueError(f"Unknown SP7 communication method: {method_id}")
    return method


def _sp5_method_for(method: str, transport_mode: str) -> str:
    cargo = str(transport_mode).lower() == "cargo"
    if method == "classic_centralized_global_mpc":
        return "sota_centralized_cbf_cargo" if cargo else "classic_centralized_shortest_push"
    if method == "classic_decentralized_sensor_apf":
        return "sota_decentralized_vo_cargo" if cargo else "classic_decentralized_apf_push"
    if method == "sota_centralized_cbf_networked":
        return "sota_centralized_cbf_cargo" if cargo else "sota_centralized_cbf_push"
    if method == "sota_decentralized_cbba_relay":
        return "sota_decentralized_vo_cargo" if cargo else "sota_decentralized_vo_push"
    if method == "sota_delay_tolerant_consensus":
        return "sota_decentralized_vo_cargo" if cargo else "sota_decentralized_vo_push"
    if method == "ours_connectivity_wrench_game":
        return "ours_hamiltonian_cargo" if cargo else "ours_tensor_game_push"
    if method == "ours_delay_robust_repair":
        return "ours_hamiltonian_cargo" if cargo else "ours_primal_dual_wrench_push"
    if method == "reference_full_communication":
        return "reference_centralized_mpc_cbf_cargo" if cargo else "sota_centralized_cbf_push"
    raise ValueError(f"Unknown SP7 method: {method}")


def _dependence(method: str) -> float:
    return {
        "classic_centralized_global_mpc": 0.92,
        "classic_decentralized_sensor_apf": 0.24,
        "sota_centralized_cbf_networked": 0.72,
        "sota_decentralized_cbba_relay": 0.52,
        "sota_delay_tolerant_consensus": 0.40,
        "ours_connectivity_wrench_game": 0.22,
        "ours_delay_robust_repair": 0.18,
        "reference_full_communication": 0.65,
    }[method]


def sp5_backing_method(method_id: str, transport_mode: str) -> str:
    return _sp5_method_for(_canonical_method(method_id), transport_mode)


def backing_method_metadata(method_id: str, transport_mode: str) -> dict[str, Any]:
    return sp5_method_metadata(sp5_backing_method(method_id, transport_mode))
