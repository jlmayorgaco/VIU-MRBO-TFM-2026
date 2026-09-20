"""Versioned SP2 closure campaign built from the common N1--N4 interfaces."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.lines import Line2D
from scipy.stats import binomtest, wilcoxon

from .communication import (
    ChannelConfig,
    SeededLocalChannel,
    leader_follower_update,
    virtual_structure_update,
)
from .controllers import cbf_acceleration_filter, make_controller, pose_error, wrap_angle
from .dynamics import PlanarPayload, required_wrench_body
from .governor import govern_acceleration
from .kinematics import DifferentialDrive, certify_formation_twist, independent_speed_only_feasible
from .mechanics import (
    aggregate_force_only_feasible,
    certify_planar_wrench,
    certify_supported_wrench,
)
from .support import SupportContact


METHOD_LABELS = {
    "pd": "PD",
    "pid": "PID",
    "lqr": "LQR",
    "lqi": "LQI",
    "port_hamiltonian": "Amortiguamiento energético",
    "mpc_central": "MPC central",
}

SHORT_METHOD_LABELS = {
    "pd": "PD",
    "pid": "PID",
    "lqr": "LQR",
    "lqi": "LQI",
    "port_hamiltonian": "Amortiguamiento",
    "mpc_central": "MPC central",
}

SCENARIO_LABELS = {
    "S0": "Nominal",
    "S1": "Carga y perturbación",
    "S2": "Actuadores heterogéneos",
    "S3": "Canal degradado",
    "S4": "Pérdida y restauración exógena",
    "S5": "Obstáculo y filtro de seguridad",
    "S6": "Fallo combinado",
}


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    payload: PlanarPayload
    target: np.ndarray
    wheel_limits: tuple[float, ...]
    friction: tuple[float, ...]
    drive_limits: tuple[float, ...]
    normal_limits: tuple[float, ...]
    channel: ChannelConfig
    obstacles: tuple[tuple[tuple[float, float], float], ...] = ()


def _hash_payload(payload: Any) -> str:
    serial = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    """Hash a file without loading large raw artifacts into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hardware() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": __import__("os").cpu_count(),
        "execution_device": "CPU",
        "gpu_used": False,
    }


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unavailable"


def _offsets() -> np.ndarray:
    return np.asarray([[-0.45, -0.30], [0.45, -0.30], [0.45, 0.30], [-0.45, 0.30]])


def _coalition_radius_m(geometry: dict[str, Any]) -> float:
    """Return the conservative circumscribed radius of the reduced coalition."""

    half_extents = np.asarray(geometry["payload_half_extents_m"], dtype=float)
    if half_extents.shape != (2,) or np.any(half_extents <= 0.0):
        raise ValueError("payload_half_extents_m must contain two positive values")
    robot_radius = float(geometry["robot_radius_m"])
    if robot_radius <= 0.0:
        raise ValueError("robot_radius_m must be strictly positive")
    payload_radius = float(np.linalg.norm(half_extents))
    robot_envelope = float(np.max(np.linalg.norm(_offsets(), axis=1)) + robot_radius)
    return max(payload_radius, robot_envelope)


def _governor_grid(step: float) -> np.ndarray:
    """Return a descending grid from one to zero with an exact declared step."""

    if not 0.0 < step <= 1.0:
        raise ValueError("governor grid step must lie in (0, 1]")
    intervals = int(round(1.0 / step))
    if not np.isclose(intervals * step, 1.0, atol=1e-12):
        raise ValueError("governor grid step must divide one exactly")
    return np.linspace(1.0, 0.0, intervals + 1)


def _drives(scenario: Scenario) -> list[DifferentialDrive]:
    return [
        DifferentialDrive(f"r{index + 1}", 0.06, 0.32, float(limit))
        for index, limit in enumerate(scenario.wheel_limits)
    ]


def _contacts(scenario: Scenario) -> list[SupportContact]:
    return [
        SupportContact(
            f"r{index + 1}",
            tuple(offset),
            float(scenario.friction[index]),
            float(scenario.normal_limits[index]),
            float(scenario.drive_limits[index]),
        )
        for index, offset in enumerate(_offsets())
    ]


def _scenario(scenario_id: str) -> Scenario:
    nominal_channel = ChannelConfig(2.0, bandwidth_bytes_s=20_000.0)
    common = {
        "payload": PlanarPayload(18.0, 2.2, 1.2, 0.18),
        "target": np.asarray([1.6, 0.4, 0.25]),
        "wheel_limits": (11.0, 11.0, 11.0, 11.0),
        "friction": (0.65, 0.65, 0.65, 0.65),
        "drive_limits": (28.0, 28.0, 28.0, 28.0),
        "normal_limits": (70.0, 70.0, 70.0, 70.0),
        "channel": nominal_channel,
    }
    if scenario_id == "S0":
        return Scenario(scenario_id, **common)
    if scenario_id == "S1":
        common.update(payload=PlanarPayload(28.0, 3.4, 1.6, 0.25), normal_limits=(90.0,) * 4)
    elif scenario_id == "S2":
        common.update(
            wheel_limits=(7.0, 9.0, 11.0, 13.0),
            friction=(0.25, 0.42, 0.65, 0.80),
            drive_limits=(15.0, 20.0, 25.0, 30.0),
        )
    elif scenario_id == "S3":
        common.update(
            channel=ChannelConfig(
                2.0,
                delay_mean_s=0.16,
                delay_jitter_s=0.08,
                loss_probability=0.25,
                bandwidth_bytes_s=3_500.0,
                retransmissions=1,
            )
        )
    elif scenario_id == "S4":
        pass
    elif scenario_id == "S5":
        common.update(obstacles=(((0.80, -0.65), 0.18),))
    elif scenario_id == "S6":
        common.update(
            payload=PlanarPayload(24.0, 3.0, 1.5, 0.22),
            channel=ChannelConfig(
                1.2,
                delay_mean_s=0.24,
                delay_jitter_s=0.12,
                loss_probability=0.45,
                bandwidth_bytes_s=2_000.0,
                retransmissions=0,
            ),
            obstacles=(((0.80, -0.65), 0.18),),
        )
    else:
        raise ValueError(f"unknown scenario: {scenario_id}")
    return Scenario(scenario_id, **common)


def _run_n1(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    omegas = np.linspace(0.0, float(config["max_omega_rad_s"]), int(config["omega_samples"]))
    for seed in config["seeds"]:
        rng = np.random.default_rng(int(seed))
        wheel_limits = np.asarray(config["base_wheel_limits_rad_s"], dtype=float) * rng.uniform(0.82, 1.18, 4)
        drives = [DifferentialDrive(f"r{i + 1}", 0.06, 0.32, float(limit)) for i, limit in enumerate(wheel_limits)]
        for radius in config["formation_radii_m"]:
            offsets = float(radius) * np.asarray([[0.0, -1.0], [1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])
            for speed in config["forward_speeds_mps"]:
                for omega in omegas:
                    twist = np.asarray([float(speed), 0.0, float(omega)])
                    certificate = certify_formation_twist(drives, offsets, twist)
                    naive = independent_speed_only_feasible(drives, offsets, twist)
                    rows.append(
                        {
                            "seed": int(seed),
                            "radius_m": float(radius),
                            "speed_mps": float(speed),
                            "omega_rad_s": float(omega),
                            "feasible": int(certificate.feasible),
                            "naive_feasible": int(naive),
                            "false_feasible": int(naive and not certificate.feasible),
                            "margin": certificate.margin,
                            "utilization": certificate.max_utilization,
                            "limiting_robot": certificate.limiting_robot_id,
                            "limiting_wheel": certificate.limiting_wheel,
                        }
                    )
    return pd.DataFrame(rows)


def _geometry(dispersion: float, rng: np.random.Generator) -> np.ndarray:
    base = dispersion * np.asarray([[-1.0, -0.65], [1.0, -0.65], [1.0, 0.65], [-1.0, 0.65]])
    return base + rng.normal(0.0, 0.025, base.shape)


def _run_n2(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for seed in config["seeds"]:
        rng = np.random.default_rng(int(seed))
        for dispersion in config["dispersion_m"]:
            offsets = _geometry(float(dispersion), rng)
            for pressure in config["pressure_levels"]:
                force = 40.0 * float(pressure)
                torque = 12.0 * float(pressure)
                wrench = np.asarray([force, 0.25 * force, torque])
                planar_limits = np.asarray([28.0, 24.0, 20.0, 16.0])
                contacts = [
                    SupportContact(
                        f"r{i + 1}", tuple(offset), mu, 75.0, float(planar_limits[i])
                    )
                    for i, (offset, mu) in enumerate(zip(offsets, [0.28, 0.42, 0.62, 0.78], strict=True))
                ]
                scalar = aggregate_force_only_feasible(planar_limits, wrench)
                bilateral = certify_planar_wrench(offsets, planar_limits, wrench)
                full = certify_supported_wrench(contacts, float(config["payload_mass_kg"]), wrench)
                rows.append(
                    {
                        "seed": int(seed),
                        "dispersion_m": float(dispersion),
                        "pressure": float(pressure),
                        "scalar_feasible": int(scalar),
                        "bilateral_feasible": int(bilateral.feasible),
                        "supported_feasible": int(full.feasible),
                        "scalar_false_feasible": int(scalar and not full.feasible),
                        "bilateral_false_feasible": int(bilateral.feasible and not full.feasible),
                        "supported_utilization": full.utilization,
                        "wrench_residual": full.residual_norm,
                        "internal_force_ratio": full.internal_force_ratio,
                        "limiting_robot": full.limiting_robot_id,
                    }
                )
    return pd.DataFrame(rows)


def _run_n3(config: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dt = float(config["dt_s"])
    updates = int(config["updates"])
    positions = np.asarray([[0.0, 0.0], [0.55, 0.0], [0.55, 0.55], [0.0, 0.55]])
    measurement_std = np.asarray([0.020, 0.020, 0.010])
    covariance_diagonal = np.square(measurement_std).tolist()
    for seed in config["seeds"]:
        for network_name, network in config["networks"].items():
            channel_config = ChannelConfig(**network)
            for architecture in ("leader_follower", "virtual_structure"):
                channel = SeededLocalChannel(channel_config, int(seed))
                rng = np.random.default_rng(int(seed))
                estimates = {f"r{i + 1}": np.zeros(3) for i in range(4)}
                position_squared_errors_m2: list[float] = []
                yaw_squared_errors_rad2: list[float] = []
                ages: list[float] = []
                for sequence in range(updates):
                    now = sequence * dt
                    truth = np.asarray([0.4 * np.sin(0.5 * now), 0.3 * np.cos(0.4 * now), 0.2 * np.sin(0.3 * now)])
                    if architecture == "leader_follower":
                        message = leader_follower_update(
                            coalition_id="c17",
                            membership_version=3,
                            sequence=sequence,
                            pose=(truth + rng.normal(0.0, measurement_std)).tolist(),
                            twist=[0.0, 0.0, 0.0],
                            sender_id="r1",
                            timestamp_s=now,
                        )
                        for receiver in ("r2", "r3", "r4"):
                            channel.send(message, receiver, positions[0], positions[int(receiver[1:]) - 1], now)
                    else:
                        for robot in range(4):
                            local = truth + rng.normal(0.0, measurement_std)
                            estimates[f"r{robot + 1}"] = local
                            message = virtual_structure_update(
                                coalition_id="c17",
                                membership_version=3,
                                sequence=sequence,
                                robot_id=f"r{robot + 1}",
                                pose_estimate=local.tolist(),
                                twist_estimate=[0.0, 0.0, 0.0],
                                confidence=0.85,
                                timestamp_s=now,
                                covariance_diagonal=covariance_diagonal,
                            )
                            for neighbor in ((robot - 1) % 4, (robot + 1) % 4):
                                channel.send(message, f"r{neighbor + 1}", positions[robot], positions[neighbor], now)
                    for delivery in channel.receive_until(now):
                        if architecture == "leader_follower":
                            estimates[delivery.receiver] = np.asarray(delivery.payload["pose"])
                        else:
                            receiver_estimate = estimates[delivery.receiver]
                            incoming = np.asarray(delivery.payload["pose_estimate"])
                            estimates[delivery.receiver] = 0.5 * receiver_estimate + 0.5 * incoming
                        ages.append(now - float(delivery.payload["timestamp_s"]))
                    evaluated = [estimates[robot] for robot in ("r2", "r3", "r4")]
                    for estimate in evaluated:
                        position_squared_errors_m2.append(float(np.sum((estimate[:2] - truth[:2]) ** 2)))
                        yaw_error = wrap_angle(float(estimate[2] - truth[2]))
                        yaw_squared_errors_rad2.append(yaw_error * yaw_error)
                channel.receive_until(float("inf"))
                rows.append(
                    {
                        "seed": int(seed),
                        "network": network_name,
                        "architecture": architecture,
                        "rmse_position_m": float(np.sqrt(np.mean(position_squared_errors_m2))),
                        "rmse_yaw_rad": float(np.sqrt(np.mean(yaw_squared_errors_rad2))),
                        "measurement_std_xy_m": float(measurement_std[0]),
                        "measurement_std_yaw_rad": float(measurement_std[2]),
                        "mean_age_s": float(np.mean(ages)) if ages else float("nan"),
                        "attempted_messages": channel.stats.attempted_messages,
                        "queued_messages": channel.stats.queued_messages,
                        "delivered_messages": channel.stats.delivered_messages,
                        "bytes": channel.stats.attempted_bytes,
                        "generated_bytes": channel.stats.attempted_bytes,
                        "queued_bytes": channel.stats.queued_bytes,
                        "delivered_bytes": channel.stats.delivered_bytes,
                        "dropped_bytes": channel.stats.dropped_bytes,
                        "delivery_ratio": channel.stats.delivery_ratio,
                        "mean_latency_s": channel.stats.mean_latency_s,
                    }
                )
    return pd.DataFrame(rows)


def _external_acceleration(scenario_id: str, time_s: float) -> np.ndarray:
    if scenario_id == "S1" and 3.0 <= time_s < 4.0:
        return np.asarray([0.0, -0.65, 0.0])
    if scenario_id == "S6" and 4.0 <= time_s < 5.2:
        return np.asarray([-0.25, -0.55, 0.12])
    return np.zeros(3)


def _active_indices(scenario_id: str, time_s: float) -> tuple[int, ...]:
    if scenario_id == "S4" and 3.0 <= time_s < 4.5:
        return (0, 1, 2)
    if scenario_id == "S6" and time_s >= 3.0:
        return (0, 1, 2)
    return (0, 1, 2, 3)


def _simulate(
    scenario: Scenario,
    method: str,
    mode: str,
    seed: int,
    dynamic_config: dict[str, Any],
    *,
    governor_grid: np.ndarray | None = None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    simulation = dynamic_config["simulation"]
    geometry = dynamic_config["geometry"]
    terminal = dynamic_config["terminal"]
    dt = float(simulation["dt_s"])
    horizon = float(simulation["horizon_s"])
    steps = int(round(horizon / dt))
    coalition_radius = _coalition_radius_m(geometry)
    safety_margin = float(geometry["safety_margin_m"])
    position_tolerance = float(terminal["position_tolerance_m"])
    yaw_tolerance = float(terminal["yaw_tolerance_rad"])
    linear_speed_tolerance = float(terminal["linear_speed_tolerance_mps"])
    angular_speed_tolerance = float(terminal["angular_speed_tolerance_rad_s"])
    stable_steps_required = max(1, int(math.ceil(float(terminal["dwell_time_s"]) / dt)))
    information_max_age_s = float(simulation.get("information_max_age_s", 0.60))
    brake_gain = float(simulation.get("brake_gain", 1.8))
    controller = make_controller(method)
    rng = np.random.default_rng(seed)
    drives_all = _drives(scenario)
    contacts_all = _contacts(scenario)
    offsets_all = _offsets()
    channel = SeededLocalChannel(scenario.channel, seed + 77_000)
    q = np.zeros(3)
    twist = np.zeros(3)
    observed_q = q.copy()
    observed_twist = twist.copy()
    last_observation_timestamp_s = 0.0
    last_scale = 1.0
    stable_steps = 0
    collision = False
    success = False
    recovery_started: float | None = None
    recovery_time = float("nan")
    scale_values: list[float] = []
    kinematic_margins: list[float] = []
    mechanical_margins: list[float] = []
    internal_ratios: list[float] = []
    estimate_position_errors_m: list[float] = []
    estimate_yaw_errors_rad: list[float] = []
    cbf_interventions: list[float] = []
    information_ages_s: list[float] = []
    governor_statuses: list[str] = []
    command_infeasible_events: list[bool] = []
    realized_violation_events: list[bool] = []
    realized_kinematic_events: list[bool] = []
    realized_wrench_events: list[bool] = []
    realized_kinematic_margins: list[float] = []
    realized_mechanical_margins: list[float] = []
    longest_realized_violation_steps = 0
    current_realized_violation_steps = 0
    kinematic_violation_seen = False
    wrench_violation_seen = False
    support_failure_seen = False
    requested_linear_effort = 0.0
    requested_yaw_effort = 0.0
    executed_linear_effort = 0.0
    executed_yaw_effort = 0.0
    traces = {
        "time": [],
        "pose": [],
        "twist": [],
        "scale": [],
        "brake_scale": [],
        "kin_margin": [],
        "mech_margin": [],
    }
    termination = "timeout"

    for step in range(steps + 1):
        now = step * dt
        noise = rng.normal(0.0, [0.006, 0.006, 0.003])
        message = leader_follower_update(
            coalition_id="c17",
            membership_version=4 if scenario.scenario_id in {"S4", "S6"} and now >= 3.0 else 3,
            sequence=step,
            pose=(q + noise).tolist(),
            twist=(twist + rng.normal(0.0, [0.008, 0.008, 0.004])).tolist(),
            sender_id="r1",
            timestamp_s=now,
        )
        channel.send(message, "controller", np.asarray([0.0, 0.0]), np.asarray([0.4, 0.0]), now)
        for delivery in channel.receive_until(now):
            observed_q = np.asarray(delivery.payload["pose"], dtype=float)
            observed_twist = np.asarray(delivery.payload["twist"], dtype=float)
            last_observation_timestamp_s = float(delivery.payload["timestamp_s"])
        if method == "mpc_central":
            controller_q, controller_twist = q, twist
            information_age_s = 0.0
        else:
            controller_q, controller_twist = observed_q, observed_twist
            information_age_s = max(0.0, now - last_observation_timestamp_s)
        information_fresh = bool(information_age_s <= information_max_age_s + 1e-12)
        information_ages_s.append(information_age_s)
        estimate_position_errors_m.append(float(np.linalg.norm(controller_q[:2] - q[:2])))
        estimate_yaw_errors_rad.append(abs(wrap_angle(float(controller_q[2] - q[2]))))
        requested = controller.command(
            controller_q,
            controller_twist,
            scenario.target,
            dt,
            governor_scale=last_scale,
        )
        obstacles = [(np.asarray(center), radius) for center, radius in scenario.obstacles]
        if obstacles:
            requested, intervention = cbf_acceleration_filter(
                controller_q,
                controller_twist,
                requested,
                obstacles,
                body_radius_m=coalition_radius,
                safety_margin_m=safety_margin,
            )
        else:
            intervention = 0.0
        if obstacles:
            def barrier_guard(candidate: np.ndarray) -> bool:
                filtered, _ = cbf_acceleration_filter(
                    controller_q,
                    controller_twist,
                    candidate,
                    obstacles,
                    body_radius_m=coalition_radius,
                    safety_margin_m=safety_margin,
                )
                return bool(np.allclose(filtered, candidate, rtol=0.0, atol=1e-9))

            brake_request, _ = cbf_acceleration_filter(
                controller_q,
                controller_twist,
                -brake_gain * twist,
                obstacles,
                body_radius_m=coalition_radius,
                safety_margin_m=safety_margin,
            )
        else:
            barrier_guard = None
            brake_request = -brake_gain * twist
        cbf_interventions.append(intervention)
        active = _active_indices(scenario.scenario_id, now)
        drives = [drives_all[index] for index in active]
        contacts = [contacts_all[index] for index in active]
        offsets = offsets_all[list(active)]
        requested_linear_effort += dt * float(np.dot(requested[:2], requested[:2]))
        requested_yaw_effort += dt * float(requested[2] ** 2)

        if mode == "governed":
            governed = govern_acceleration(
                requested,
                twist,
                float(q[2]),
                scenario.payload,
                drives,
                offsets,
                contacts,
                scale_grid=(
                    _governor_grid(0.2)
                    if governor_grid is None
                    else np.asarray(governor_grid, dtype=float)
                ),
                lookahead_s=dt,
                candidate_guard=barrier_guard,
                information_fresh=information_fresh,
                brake_acceleration=brake_request,
                brake_gain=brake_gain,
            )
            executed = governed.executed_acceleration
            scale = governed.scale
            brake_scale = governed.brake_scale
            kinematic = governed.kinematic
            mechanical = governed.mechanical
            governor_status = governed.status
            auxiliary_guard_feasible = governed.auxiliary_guard_feasible
        else:
            kinematic = certify_formation_twist(
                drives,
                offsets,
                twist + dt * requested,
                requested,
                payload_yaw_rad=float(q[2]),
            )
            desired_wrench = required_wrench_body(scenario.payload, requested, twist, float(q[2]))
            mechanical = certify_supported_wrench(contacts, scenario.payload.mass_kg, desired_wrench)
            wheel_scale = min(1.0, 1.0 / max(kinematic.max_utilization, 1.0))
            realized_wrench = mechanical.achieved_wrench
            if (
                not mechanical.feasible
                and mechanical.diagnostic_achieved_wrench is not None
                and np.all(np.isfinite(mechanical.diagnostic_achieved_wrench))
            ):
                realized_wrench = mechanical.diagnostic_achieved_wrench
            if np.all(np.isfinite(realized_wrench)):
                c, s = math.cos(float(q[2])), math.sin(float(q[2]))
                rotation = np.asarray([[c, -s], [s, c]])
                achieved_world = realized_wrench.copy()
                achieved_world[:2] = rotation @ achieved_world[:2]
                executed = np.linalg.solve(
                    scenario.payload.mass_matrix,
                    achieved_world - scenario.payload.damping_matrix @ twist,
                )
            else:
                executed = np.zeros(3)
            executed *= wheel_scale
            scale = float(min(wheel_scale, 1.0 if mechanical.feasible else max(0.0, 1.0 / max(mechanical.utilization, 1.0))))
            brake_scale = 0.0
            governor_status = "raw"
            auxiliary_guard_feasible = bool(barrier_guard(requested)) if barrier_guard is not None else True

        command_feasible = bool(
            kinematic.feasible and mechanical.feasible and auxiliary_guard_feasible
        )
        command_infeasible_events.append(not command_feasible)
        governor_statuses.append(governor_status)
        if mechanical.support is not None and not mechanical.support.feasible:
            support_failure_seen = True

        if scenario.scenario_id in {"S2", "S6"}:
            executed *= 0.92 if scenario.scenario_id == "S2" else 0.84
        external_acceleration = _external_acceleration(scenario.scenario_id, now)
        actual_acceleration = executed + external_acceleration
        actual_acceleration += rng.normal(0.0, [0.006, 0.006, 0.003])
        predicted_realized_twist = twist + dt * actual_acceleration
        realized_kinematic = certify_formation_twist(
            drives,
            offsets,
            predicted_realized_twist,
            actual_acceleration,
            payload_yaw_rad=float(q[2]),
        )
        external_wrench_world = scenario.payload.mass_matrix @ external_acceleration
        realized_wrench = required_wrench_body(
            scenario.payload,
            actual_acceleration,
            twist,
            float(q[2]),
            external_wrench_world,
        )
        realized_mechanical = certify_supported_wrench(
            contacts,
            scenario.payload.mass_kg,
            realized_wrench,
            diagnose_infeasible=False,
        )
        realized_kinematic_violation = not realized_kinematic.feasible
        realized_wrench_violation = not realized_mechanical.feasible
        realized_violation = bool(realized_kinematic_violation or realized_wrench_violation)
        realized_kinematic_events.append(realized_kinematic_violation)
        realized_wrench_events.append(realized_wrench_violation)
        realized_violation_events.append(realized_violation)
        realized_kinematic_margins.append(realized_kinematic.margin)
        realized_mechanical_margins.append(realized_mechanical.friction_margin)
        if realized_violation:
            current_realized_violation_steps += 1
            longest_realized_violation_steps = max(
                longest_realized_violation_steps,
                current_realized_violation_steps,
            )
        else:
            current_realized_violation_steps = 0
        kinematic_violation_seen = bool(
            kinematic_violation_seen or realized_kinematic_violation
        )
        if realized_mechanical.support is not None and not realized_mechanical.support.feasible:
            support_failure_seen = True
        elif realized_wrench_violation:
            wrench_violation_seen = True
        executed_linear_effort += dt * float(np.dot(executed[:2], executed[:2]))
        executed_yaw_effort += dt * float(executed[2] ** 2)
        scale_values.append(scale)
        last_scale = scale
        kinematic_margins.append(kinematic.margin)
        mechanical_margins.append(mechanical.friction_margin)
        if np.isfinite(mechanical.internal_force_ratio):
            internal_ratios.append(mechanical.internal_force_ratio)

        traces["time"].append(now)
        traces["pose"].append(q.copy())
        traces["twist"].append(twist.copy())
        traces["scale"].append(scale)
        traces["brake_scale"].append(brake_scale)
        traces["kin_margin"].append(kinematic.margin)
        traces["mech_margin"].append(mechanical.friction_margin)

        if scenario.scenario_id in {"S4", "S6"} and now >= 3.0 and recovery_started is None:
            recovery_started = now
        if scenario.scenario_id == "S4" and recovery_started is not None and now >= 4.5 and math.isnan(recovery_time):
            recovery_time = now - recovery_started

        for center, radius in obstacles:
            if float(np.linalg.norm(q[:2] - center)) < coalition_radius + radius:
                collision = True
                termination = "collision"
                break
        if collision:
            break
        error = pose_error(scenario.target, q)
        if (
            float(np.linalg.norm(error[:2])) <= position_tolerance
            and abs(float(error[2])) <= yaw_tolerance
            and float(np.linalg.norm(twist[:2])) <= linear_speed_tolerance
            and abs(float(twist[2])) <= angular_speed_tolerance
        ):
            stable_steps += 1
            if stable_steps >= stable_steps_required:
                success = True
                termination = "target_reached"
                break
        else:
            stable_steps = 0
        if step == steps:
            break
        twist = twist + dt * actual_acceleration
        q = q + dt * twist
        q[2] = wrap_angle(float(q[2]))
        if not np.all(np.isfinite(q)) or not np.all(np.isfinite(twist)):
            termination = "numerical_failure"
            break

    channel.receive_until(float("inf"))
    time_to_target = traces["time"][-1] if success else float("nan")
    final_error = pose_error(scenario.target, q)
    finite_mechanical = [value for value in mechanical_margins if np.isfinite(value)]
    finite_realized_mechanical = [
        value for value in realized_mechanical_margins if np.isfinite(value)
    ]
    scale_array = np.asarray(scale_values, dtype=float)
    status_array = np.asarray(governor_statuses, dtype=str)
    command_infeasible = bool(any(command_infeasible_events))
    physical_violation = bool(any(realized_violation_events))
    physically_admissible_success = bool(success and not collision and not physical_violation)
    if success and not collision:
        failure_mode = "none"
    elif collision:
        failure_mode = "collision"
    elif termination == "numerical_failure":
        failure_mode = "numerical_failure"
    elif support_failure_seen:
        failure_mode = "support_unavailable"
    elif "uncontrolled_stop_required" in governor_statuses:
        failure_mode = "uncontrolled_stop_required"
    elif any(age > information_max_age_s + 1e-12 for age in information_ages_s):
        failure_mode = "stale_information_braking"
    elif scenario.scenario_id == "S3":
        failure_mode = "communication_timeout"
    elif scenario.scenario_id == "S5" and float(np.mean(cbf_interventions)) > 1e-9:
        failure_mode = "barrier_limited_timeout"
    elif mode == "governed" and float(np.mean(scale_array < 1.0 - 1e-12)) > 0.5:
        failure_mode = "governor_limited_timeout"
    elif kinematic_violation_seen:
        failure_mode = "kinematic_limit"
    elif wrench_violation_seen:
        failure_mode = "wrench_limit"
    else:
        failure_mode = "timeout"
    result = {
        "scenario": scenario.scenario_id,
        "scenario_label": SCENARIO_LABELS[scenario.scenario_id],
        "method": method,
        "method_label": METHOD_LABELS[method],
        "centralized": int(method == "mpc_central"),
        "mode": mode,
        "seed": int(seed),
        "world_hash": _hash_payload({"scenario": scenario.scenario_id, "seed": seed}),
        "success": int(success and not collision),
        "physically_admissible_success": int(physically_admissible_success),
        "command_infeasible": int(command_infeasible),
        "command_infeasible_fraction": float(np.mean(command_infeasible_events)),
        "physical_violation": int(physical_violation),
        "realized_violation_fraction": float(np.mean(realized_violation_events)),
        "realized_violation_duration_s": float(dt * np.sum(realized_violation_events)),
        "realized_violation_max_duration_s": float(
            dt * longest_realized_violation_steps
        ),
        "kinematic_violation": int(kinematic_violation_seen),
        "wrench_violation": int(wrench_violation_seen),
        "support_failure": int(support_failure_seen),
        "collision": int(collision),
        "timeout": int(termination == "timeout"),
        "numerical_failure": int(termination == "numerical_failure"),
        "termination": termination,
        "failure_mode": failure_mode,
        "time_to_target_s": time_to_target,
        "final_position_error_m": float(np.linalg.norm(final_error[:2])),
        "final_yaw_error_rad": abs(float(final_error[2])),
        "final_linear_speed_mps": float(np.linalg.norm(twist[:2])),
        "final_angular_speed_rad_s": abs(float(twist[2])),
        "minimum_kinematic_margin": float(np.min(kinematic_margins)),
        "minimum_mechanical_margin": float(np.min(finite_mechanical)) if finite_mechanical else float("-inf"),
        "minimum_realized_kinematic_margin": float(
            np.min(realized_kinematic_margins)
        ),
        "minimum_realized_mechanical_margin": float(
            np.min(finite_realized_mechanical)
        )
        if finite_realized_mechanical
        else float("-inf"),
        "governor_intervention_rate": float(np.mean(np.asarray(scale_values) < 1.0 - 1e-12)),
        "governor_hold_rate": float(np.mean(status_array == "hold")),
        "governor_brake_rate": float(np.mean(status_array == "brake")),
        "governor_uncontrolled_rate": float(
            np.mean(status_array == "uncontrolled_stop_required")
        ),
        "mean_governor_scale": float(np.mean(scale_values)),
        "governor_total_variation": float(np.sum(np.abs(np.diff(scale_array)))),
        "governor_switch_rate": float(np.mean(np.abs(np.diff(scale_array)) > 1e-12))
        if scale_array.size > 1
        else 0.0,
        "mean_internal_force_ratio": float(np.mean(internal_ratios)) if internal_ratios else float("nan"),
        "state_estimate_rmse_position_m": float(np.sqrt(np.mean(np.square(estimate_position_errors_m)))),
        "state_estimate_rmse_yaw_rad": float(np.sqrt(np.mean(np.square(estimate_yaw_errors_rad)))),
        "mean_information_age_s": float(np.mean(information_ages_s)),
        "information_stale_rate": float(
            np.mean(np.asarray(information_ages_s) > information_max_age_s + 1e-12)
        ),
        "cbf_intervention_mean": float(np.mean(cbf_interventions)),
        "requested_linear_effort_m2_s3": requested_linear_effort,
        "requested_yaw_effort_rad2_s3": requested_yaw_effort,
        "executed_linear_effort_m2_s3": executed_linear_effort,
        "executed_yaw_effort_rad2_s3": executed_yaw_effort,
        "attempted_messages": channel.stats.attempted_messages,
        "queued_messages": channel.stats.queued_messages,
        "delivered_messages": channel.stats.delivered_messages,
        "bytes": channel.stats.attempted_bytes,
        "generated_bytes": channel.stats.attempted_bytes,
        "queued_bytes": channel.stats.queued_bytes,
        "delivered_bytes": channel.stats.delivered_bytes,
        "dropped_bytes": channel.stats.dropped_bytes,
        "delivery_ratio": channel.stats.delivery_ratio,
        "recovery_time_s": recovery_time,
    }
    trace = {key: np.asarray(value) for key, value in traces.items()}
    return result, trace


def _wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""

    if trials <= 0:
        return float("nan"), float("nan")
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _summary(rows: pd.DataFrame) -> pd.DataFrame:
    grouped = rows.groupby(["method", "method_label", "mode", "centralized"], sort=False)
    records: list[dict[str, Any]] = []
    for keys, frame in grouped:
        success = frame["success"].to_numpy(dtype=float)
        physical_success = frame["physically_admissible_success"].to_numpy(dtype=float)
        mean = float(np.mean(success))
        success_low, success_high = _wilson_interval(int(np.sum(success)), len(success))
        collision_values = frame["collision"].to_numpy(dtype=float)
        collision_low, collision_high = _wilson_interval(
            int(np.sum(collision_values)), len(collision_values)
        )
        records.append(
            {
                "method": keys[0],
                "method_label": keys[1],
                "mode": keys[2],
                "centralized": keys[3],
                "runs": len(frame),
                "success_rate": mean,
                "success_ci95_low": success_low,
                "success_ci95_high": success_high,
                "physically_admissible_success_rate": float(np.mean(physical_success)),
                "command_infeasible_run_rate": float(frame["command_infeasible"].mean()),
                "mean_command_infeasible_fraction": float(
                    frame["command_infeasible_fraction"].mean()
                ),
                "physical_violation_rate": float(frame["physical_violation"].mean()),
                "mean_realized_violation_fraction": float(
                    frame["realized_violation_fraction"].mean()
                ),
                "mean_realized_violation_max_duration_s": float(
                    frame["realized_violation_max_duration_s"].mean()
                ),
                "collision_rate": float(frame["collision"].mean()),
                "collision_ci95_low": collision_low,
                "collision_ci95_high": collision_high,
                "timeout_rate": float(frame["timeout"].mean()),
                "median_final_position_error_m": float(frame["final_position_error_m"].median()),
                "mean_governor_intervention_rate": float(frame["governor_intervention_rate"].mean()),
                "mean_minimum_kinematic_margin": float(frame["minimum_kinematic_margin"].replace([np.inf, -np.inf], np.nan).mean()),
                "mean_minimum_mechanical_margin": float(frame["minimum_mechanical_margin"].replace([np.inf, -np.inf], np.nan).mean()),
                "mean_bytes": float(frame["bytes"].mean()),
                "mean_state_estimate_rmse_position_m": float(
                    frame["state_estimate_rmse_position_m"].mean()
                ),
                "mean_state_estimate_rmse_yaw_rad": float(
                    frame["state_estimate_rmse_yaw_rad"].mean()
                ),
            }
        )
    return pd.DataFrame(records)


def _governor_sensitivity_summary(rows: pd.DataFrame) -> pd.DataFrame:
    """Summarize the predeclared scale-grid sensitivity on paired worlds."""

    return (
        rows.groupby(["method", "method_label", "governor_step"], sort=False)
        .agg(
            runs=("success", "size"),
            geometric_success_rate=("success", "mean"),
            physically_admissible_success_rate=("physically_admissible_success", "mean"),
            command_infeasible_run_rate=("command_infeasible", "mean"),
            mean_command_infeasible_fraction=("command_infeasible_fraction", "mean"),
            physical_violation_rate=("physical_violation", "mean"),
            mean_realized_violation_fraction=("realized_violation_fraction", "mean"),
            mean_realized_violation_max_duration_s=(
                "realized_violation_max_duration_s",
                "mean",
            ),
            collision_rate=("collision", "mean"),
            mean_governor_total_variation=("governor_total_variation", "mean"),
            mean_governor_switch_rate=("governor_switch_rate", "mean"),
        )
        .reset_index()
    )


def _seed_block_bootstrap(
    differences: pd.Series,
    *,
    rng: np.random.Generator,
    resamples: int = 5_000,
) -> tuple[float, float, float, np.ndarray]:
    """Estimate a paired mean and CI while resampling complete seed blocks.

    Each confirmatory seed is reused across the seven scenarios. Treating the
    resulting 210 rows as independent understates that design dependence. The
    input series must therefore expose a ``seed`` index level; all scenarios
    belonging to the sampled seed travel together in every bootstrap draw.
    """

    if "seed" not in differences.index.names:
        raise ValueError("paired differences must expose a seed index level")
    per_seed = differences.groupby(level="seed").mean().sort_index()
    values = per_seed.to_numpy(dtype=float)
    if values.size == 0:
        raise ValueError("cannot bootstrap an empty paired endpoint")
    bootstrap = np.asarray(
        [
            np.mean(rng.choice(values, size=len(values), replace=True))
            for _ in range(resamples)
        ],
        dtype=float,
    )
    return (
        float(np.mean(values)),
        float(np.quantile(bootstrap, 0.025)),
        float(np.quantile(bootstrap, 0.975)),
        values,
    )


def _holm_adjust(values: pd.Series) -> np.ndarray:
    """Return Holm-adjusted p values in the original row order."""

    raw = values.to_numpy(dtype=float)
    order = np.argsort(raw)
    adjusted = np.ones(len(raw), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (len(raw) - rank) * float(raw[index]))
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def _paired_statistics(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    rng = np.random.default_rng(64001)
    for method in sorted(set(rows["method"]) & set(rows.loc[rows["mode"] == "raw", "method"])):
        subset = rows[rows["method"] == method]
        pivot = subset.pivot_table(
            index=["scenario", "seed"],
            columns="mode",
            values=[
                "success",
                "physically_admissible_success",
                "physical_violation",
                "collision",
                "final_position_error_m",
                "realized_violation_fraction",
                "realized_violation_max_duration_s",
                "minimum_realized_kinematic_margin",
                "minimum_realized_mechanical_margin",
            ],
        )
        if ("success", "raw") not in pivot or ("success", "governed") not in pivot:
            continue
        success_difference = pivot[("success", "governed")] - pivot[("success", "raw")]
        physical_success_difference = (
            pivot[("physically_admissible_success", "governed")]
            - pivot[("physically_admissible_success", "raw")]
        )
        physical_violation_difference = (
            pivot[("physical_violation", "governed")]
            - pivot[("physical_violation", "raw")]
        )
        collision_difference = pivot[("collision", "governed")] - pivot[("collision", "raw")]
        error_difference = pivot[("final_position_error_m", "governed")] - pivot[("final_position_error_m", "raw")]
        success_mean, success_ci_low, success_ci_high, success_seed_values = (
            _seed_block_bootstrap(success_difference, rng=rng)
        )
        collision_mean, collision_ci_low, collision_ci_high, collision_seed_values = (
            _seed_block_bootstrap(collision_difference, rng=rng)
        )
        wins = int(np.sum(success_difference > 0))
        losses = int(np.sum(success_difference < 0))
        discordant = wins + losses
        mcnemar_p = float(binomtest(wins, discordant, 0.5).pvalue) if discordant else 1.0
        physical_wins = int(np.sum(physical_success_difference > 0))
        physical_losses = int(np.sum(physical_success_difference < 0))
        physical_discordant = physical_wins + physical_losses
        physical_mcnemar_p = (
            float(binomtest(physical_wins, physical_discordant, 0.5).pvalue)
            if physical_discordant
            else 1.0
        )
        try:
            error_p = float(wilcoxon(error_difference, zero_method="pratt").pvalue)
        except ValueError:
            error_p = 1.0
        try:
            success_seed_p = (
                1.0
                if np.allclose(success_seed_values, 0.0)
                else float(wilcoxon(success_seed_values, zero_method="pratt").pvalue)
            )
        except ValueError:
            success_seed_p = 1.0
        if not np.isfinite(success_seed_p):
            success_seed_p = 1.0
        try:
            collision_seed_p = (
                1.0
                if np.allclose(collision_seed_values, 0.0)
                else float(wilcoxon(collision_seed_values, zero_method="pratt").pvalue)
            )
        except ValueError:
            collision_seed_p = 1.0
        if not np.isfinite(collision_seed_p):
            collision_seed_p = 1.0
        records.append(
            {
                "comparison": f"{method}:governed-minus-raw",
                "paired_worlds": len(pivot),
                "independent_seed_blocks": int(pivot.index.get_level_values("seed").nunique()),
                "scenarios_per_seed": int(pivot.index.get_level_values("scenario").nunique()),
                "success_risk_difference": success_mean,
                "success_difference_ci95_low": success_ci_low,
                "success_difference_ci95_high": success_ci_high,
                "mcnemar_exact_p": mcnemar_p,
                "success_seed_wilcoxon_p": success_seed_p,
                "physical_success_risk_difference": float(physical_success_difference.mean()),
                "physical_success_mcnemar_exact_p": physical_mcnemar_p,
                "physical_violation_risk_difference": float(physical_violation_difference.mean()),
                "collision_risk_difference": collision_mean,
                "collision_difference_ci95_low": collision_ci_low,
                "collision_difference_ci95_high": collision_ci_high,
                "collision_seed_wilcoxon_p": collision_seed_p,
                "median_error_difference_m": float(error_difference.median()),
                "wilcoxon_error_p": error_p,
                "wins_success": wins,
                "losses_success": losses,
                "ties_success": int(np.sum(success_difference == 0)),
            }
        )
    frame = pd.DataFrame(records)
    if not frame.empty:
        for source, target in (
            ("mcnemar_exact_p", "mcnemar_holm_p"),
            ("physical_success_mcnemar_exact_p", "physical_success_mcnemar_holm_p"),
            ("success_seed_wilcoxon_p", "success_seed_wilcoxon_holm_p"),
            ("collision_seed_wilcoxon_p", "collision_seed_wilcoxon_holm_p"),
        ):
            frame[target] = _holm_adjust(frame[source])
    return frame


def _paired_endpoint_statistics(rows: pd.DataFrame) -> pd.DataFrame:
    """Summarize governor endpoints with seed-block bootstrap intervals."""

    raw_methods = sorted(set(rows.loc[rows["mode"] == "raw", "method"]))
    subset = rows[rows["method"].isin(raw_methods)]
    endpoints = (
        "success",
        "physically_admissible_success",
        "physical_violation",
        "collision",
        "realized_violation_fraction",
        "realized_violation_max_duration_s",
        "minimum_realized_kinematic_margin",
        "minimum_realized_mechanical_margin",
    )
    pivot = subset.pivot_table(
        index=["method", "scenario", "seed"],
        columns="mode",
        values=list(endpoints),
    )
    rng = np.random.default_rng(64003)
    records: list[dict[str, Any]] = []
    for endpoint in endpoints:
        raw_values = pivot[(endpoint, "raw")]
        governed_values = pivot[(endpoint, "governed")]
        difference = governed_values - raw_values
        mean, ci_low, ci_high, seed_values = _seed_block_bootstrap(
            difference,
            rng=rng,
        )
        records.append(
            {
                "endpoint": endpoint,
                "paired_world_method_rows": int(len(difference)),
                "independent_seed_blocks": int(
                    difference.index.get_level_values("seed").nunique()
                ),
                "raw_mean": float(raw_values.mean()),
                "governed_mean": float(governed_values.mean()),
                "difference_governed_minus_raw": mean,
                "difference_ci95_low": ci_low,
                "difference_ci95_high": ci_high,
                "seed_block_difference_median": float(np.median(seed_values)),
                "seed_block_difference_q25": float(np.quantile(seed_values, 0.25)),
                "seed_block_difference_q75": float(np.quantile(seed_values, 0.75)),
            }
        )
    return pd.DataFrame(records)


def _n3_statistics(rows: pd.DataFrame) -> pd.DataFrame:
    """Return paired architecture contrasts for every channel and overall."""

    records: list[dict[str, Any]] = []
    rng = np.random.default_rng(64002)
    groups = [(str(network), rows[rows["network"] == network]) for network in sorted(rows["network"].unique())]
    groups.append(("all_channels", rows))
    for network, subset in groups:
        index = ["seed"] if network != "all_channels" else ["network", "seed"]
        pivot = subset.pivot_table(
            index=index,
            columns="architecture",
            values=[
                "rmse_position_m",
                "rmse_yaw_rad",
                "bytes",
                "delivered_bytes",
                "delivery_ratio",
                "mean_age_s",
            ],
        )
        if any((metric, architecture) not in pivot for metric in ("rmse_position_m", "rmse_yaw_rad", "bytes") for architecture in ("leader_follower", "virtual_structure")):
            raise RuntimeError(f"incomplete paired N3 data for {network}")
        record: dict[str, Any] = {
            "network": network,
            "paired_runs": len(pivot),
            "independent_seed_blocks": int(
                pivot.index.get_level_values("seed").nunique()
            ),
        }
        for metric in (
            "rmse_position_m",
            "rmse_yaw_rad",
            "bytes",
            "delivered_bytes",
            "delivery_ratio",
            "mean_age_s",
        ):
            leader = pivot[(metric, "leader_follower")].to_numpy(dtype=float)
            virtual = pivot[(metric, "virtual_structure")].to_numpy(dtype=float)
            difference = virtual - leader
            difference_series = pd.Series(difference, index=pivot.index)
            difference_mean, ci_low, ci_high, _ = _seed_block_bootstrap(
                difference_series,
                rng=rng,
            )
            record[f"leader_{metric}"] = float(np.mean(leader))
            record[f"virtual_{metric}"] = float(np.mean(virtual))
            record[f"difference_virtual_minus_leader_{metric}"] = difference_mean
            record[f"difference_ci95_low_{metric}"] = ci_low
            record[f"difference_ci95_high_{metric}"] = ci_high
        records.append(record)
    return pd.DataFrame(records)


def _hypotheses(
    n1: pd.DataFrame,
    n2: pd.DataFrame,
    n3: pd.DataFrame,
    n3_statistics: pd.DataFrame,
    dynamic: pd.DataFrame,
) -> pd.DataFrame:
    leader = n3[n3["architecture"] == "leader_follower"]
    virtual = n3[n3["architecture"] == "virtual_structure"]
    raw = dynamic[dynamic["mode"] == "raw"]
    governed = dynamic[dynamic["mode"] == "governed"]
    paired_methods = sorted(set(raw["method"]))
    paired_governed = governed[governed["method"].isin(paired_methods)]
    raw_kinematic_margin = raw["minimum_kinematic_margin"].replace([np.inf, -np.inf], np.nan).mean()
    governed_kinematic_margin = paired_governed["minimum_kinematic_margin"].replace([np.inf, -np.inf], np.nan).mean()
    per_channel_n3 = n3_statistics[n3_statistics["network"] != "all_channels"]
    n3_position_differences = per_channel_n3[
        "difference_virtual_minus_leader_rmse_position_m"
    ]
    records = [
        ("H1", "La prueba de rueda detecta falsos factibles del baseline de rapidez.", int(n1["false_feasible"].sum()), int(n1["false_feasible"].sum()) > 0),
        ("H2", "El modelo 2.5D rechaza casos aceptados por el LP bilateral.", int(n2["bilateral_false_feasible"].sum()), int(n2["bilateral_false_feasible"].sum()) > 0),
        ("H3", "Líder--seguidor usa menos bytes que la estructura virtual.", float(virtual["bytes"].mean() - leader["bytes"].mean()), float(leader["bytes"].mean()) < float(virtual["bytes"].mean())),
        (
            "H4",
            "La estructura virtual reduce el RMSE de posición en todos los canales.",
            float(n3_position_differences.max()),
            bool((n3_position_differences < 0.0).all()),
        ),
        ("H5", "El gobernador aumenta el margen cinemático medio.", float(governed_kinematic_margin - raw_kinematic_margin), float(governed_kinematic_margin) > float(raw_kinematic_margin)),
        ("H6", "El gobernador reduce colisiones en mundos pareados.", float(raw["collision"].mean() - paired_governed["collision"].mean()), float(paired_governed["collision"].mean()) < float(raw["collision"].mean())),
        ("H7", "El fallo combinado conserva los casos sin éxito en el denominador.", int(len(dynamic[dynamic["scenario"] == "S6"])), bool((dynamic[dynamic["scenario"] == "S6"]["success"] == 0).any())),
    ]
    return pd.DataFrame(
        [
            {"hypothesis": identifier, "statement": statement, "effect": effect, "supported_in_sample": int(decision), "evidence_level": "observacion_empirica"}
            for identifier, statement, effect, decision in records
        ]
    )


def _plot_n1(frame: pd.DataFrame, path: Path) -> None:
    per_seed = (
        frame.assign(feasible_omega=frame["omega_rad_s"].where(frame["feasible"] == 1))
        .groupby(["seed", "radius_m", "speed_mps"], as_index=False)["feasible_omega"]
        .max()
        .fillna({"feasible_omega": 0.0})
    )
    fig, ax = plt.subplots(figsize=(7.8, 4.05), layout="constrained")
    radii = sorted(per_seed["radius_m"].unique())
    colors = plt.cm.viridis(np.linspace(0.08, 0.92, len(radii)))
    for radius, color in zip(radii, colors, strict=True):
        subset = per_seed[per_seed["radius_m"] == radius]
        summary = (
            subset.groupby("speed_mps")["feasible_omega"]
            .agg(
                median="median",
                q05=lambda values: float(np.quantile(values, 0.05)),
                q95=lambda values: float(np.quantile(values, 0.95)),
            )
            .reset_index()
        )
        speed = summary["speed_mps"].to_numpy(dtype=float)
        ax.plot(
            speed,
            summary["median"],
            marker="o",
            linewidth=1.8,
            color=color,
            label=f"R={radius:.2f} m",
        )
        ax.fill_between(speed, summary["q05"], summary["q95"], color=color, alpha=0.14)
    ax.set(
        xlabel="velocidad longitudinal [m/s]",
        ylabel="máxima velocidad angular factible [rad/s]",
    )
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=10.2)
    ax.xaxis.label.set_size(11.2)
    ax.yaxis.label.set_size(11.2)
    ax.legend(
        frameon=False,
        ncol=2,
        fontsize=10.0,
        title="radio de formación",
        title_fontsize=10.0,
    )
    ax.text(
        0.99,
        0.02,
        "línea: mediana · banda: P5--P95 (30 semillas)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10.0,
        color="#4b5563",
    )
    fig.savefig(path, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def _plot_n2(frame: pd.DataFrame, path: Path) -> None:
    grouped = frame.groupby(["dispersion_m", "pressure"])[["scalar_feasible", "bilateral_feasible", "supported_feasible"]].mean().reset_index()
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(8.0, 2.45),
        sharey=True,
        layout="constrained",
    )
    for axis, column, title in zip(axes, ["scalar_feasible", "bilateral_feasible", "supported_feasible"], ["Capacidad escalar", "LP bilateral", "Soporte + fricción"], strict=True):
        pivot = grouped.pivot(index="pressure", columns="dispersion_m", values=column)
        image = axis.imshow(pivot.to_numpy(), origin="lower", aspect="auto", vmin=0, vmax=1, cmap="viridis")
        accepted = int(frame[column].sum())
        axis.set_title(f"{title}\n{accepted}/{len(frame)} aceptados", fontsize=11.0)
        axis.set_xticks(range(len(pivot.columns)), [f"{v:.2f}" for v in pivot.columns])
        axis.set_xlabel("dispersión [m]", fontsize=10.6)
        axis.tick_params(labelsize=10.2)
    axes[0].set_yticks(range(len(pivot.index)), [f"{v:.1f}" for v in pivot.index])
    axes[0].set_ylabel(r"escala de demanda $\pi^{N2}$", fontsize=10.6)
    colorbar = fig.colorbar(image, ax=axes, label="fracción factible", shrink=0.80, pad=0.02)
    colorbar.ax.tick_params(labelsize=10.2)
    colorbar.set_label("fracción factible", fontsize=10.6)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def _plot_n3(frame: pd.DataFrame, statistics: pd.DataFrame, path: Path) -> None:
    grouped = (
        frame.groupby(["network", "architecture"])[
            [
                "generated_bytes",
                "delivered_bytes",
                "dropped_bytes",
                "delivery_ratio",
                "mean_age_s",
                "rmse_position_m",
            ]
        ]
        .mean()
        .reset_index()
    )
    fig = plt.figure(figsize=(8.0, 3.35), layout="constrained")
    grid = fig.add_gridspec(2, 2, width_ratios=(1.05, 1.15), height_ratios=(1, 1))
    ax_tradeoff = fig.add_subplot(grid[:, 0])
    ax_difference = fig.add_subplot(grid[0, 1])
    ax_age = fig.add_subplot(grid[1, 1])
    labels = {"leader_follower": "líder--seguidor", "virtual_structure": "estructura virtual"}
    network_labels = {
        "ideal": "ideal",
        "delayed": "retardo",
        "limited": "limitado",
        "degraded": "degradado",
    }
    annotation_offsets = {
        "ideal": (-28, 7),
        "delayed": (5, -12),
        "limited": (-34, -12),
        "degraded": (5, 6),
    }
    for architecture, subset in grouped.groupby("architecture"):
        dropped_kb = subset["dropped_bytes"].to_numpy(dtype=float) / 1000.0
        ax_tradeoff.scatter(
            subset["delivered_bytes"] / 1000.0,
            subset["rmse_position_m"],
            s=52 + 5 * dropped_kb,
            label=labels[str(architecture)],
            alpha=0.82,
        )
        for _, row in subset.iterrows():
            if architecture != "virtual_structure":
                continue
            network = str(row["network"])
            ax_tradeoff.annotate(
                network_labels.get(network, network),
                (row["delivered_bytes"] / 1000.0, row["rmse_position_m"]),
                fontsize=10.0,
                xytext=annotation_offsets.get(network, (4, 4)),
                textcoords="offset points",
            )
    ax_tradeoff.set(
        xlabel="bytes entregados [kB/ejecución]",
        ylabel="RMSE de posición [m]",
        title="Coste entregado frente a error",
    )
    ax_tradeoff.grid(alpha=0.25)
    ax_tradeoff.legend(frameon=False, fontsize=9.8, loc="best")

    per_channel = statistics[statistics["network"] != "all_channels"].reset_index(drop=True)
    difference = per_channel["difference_virtual_minus_leader_rmse_position_m"].to_numpy()
    lower = difference - per_channel["difference_ci95_low_rmse_position_m"].to_numpy()
    upper = per_channel["difference_ci95_high_rmse_position_m"].to_numpy() - difference
    y = np.arange(len(per_channel))
    ax_difference.errorbar(
        difference,
        y,
        xerr=np.vstack([lower, upper]),
        fmt="o",
        color="#0f766e",
        capsize=3,
    )
    ax_difference.axvline(0.0, color="#111827", linewidth=0.9)
    ax_difference.set_yticks(
        y,
        [network_labels.get(str(value), str(value)) for value in per_channel["network"]],
    )
    ax_difference.set(
        xlabel=r"$\Delta$RMSE [m] (virtual $-$ líder)",
        title="Contraste pareado (IC 95 %)",
    )
    ax_difference.grid(axis="x", alpha=0.25)

    networks = list(dict.fromkeys(grouped["network"].tolist()))
    x = np.arange(len(networks))
    for offset, architecture in ((-0.18, "leader_follower"), (0.18, "virtual_structure")):
        selected = grouped[grouped["architecture"] == architecture].set_index("network").reindex(networks)
        bars = ax_age.bar(
            x + offset,
            selected["mean_age_s"],
            0.34,
            label=labels[architecture],
        )
        for bar, ratio in zip(bars, selected["delivery_ratio"], strict=True):
            ax_age.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.04,
                f"{100 * ratio:.0f}%",
                ha="center",
                va="bottom",
                fontsize=10.0,
            )
    ax_age.set_xticks(
        x,
        [network_labels.get(str(value), str(value)) for value in networks],
        rotation=16,
        ha="right",
    )
    ax_age.set(ylabel="edad media [s]", title="Edad; etiqueta = entrega")
    ax_age.grid(axis="y", alpha=0.25)
    for axis in (ax_tradeoff, ax_difference, ax_age):
        axis.tick_params(labelsize=10.0)
        axis.xaxis.label.set_size(10.4)
        axis.yaxis.label.set_size(10.4)
        axis.title.set_size(10.8)
        axis.spines[["top", "right"]].set_visible(False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def _plot_dynamic_matrix(frame: pd.DataFrame, path: Path) -> None:
    governed = frame[frame["mode"] == "governed"]
    pivot = governed.pivot_table(index="method", columns="scenario", values="success", aggfunc="mean").reindex(index=METHOD_LABELS, columns=SCENARIO_LABELS)
    fig, (ax, ax_failure) = plt.subplots(
        1,
        2,
        figsize=(8.1, 3.15),
        gridspec_kw={"width_ratios": (1.0, 1.0)},
        layout="constrained",
    )
    image = ax.imshow(pivot.to_numpy(), vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), [SHORT_METHOD_LABELS[item] for item in pivot.index])
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(
                j,
                i,
                f"{pivot.iloc[i, j]:.2f}",
                ha="center",
                va="center",
                color="white" if pivot.iloc[i, j] < 0.55 else "black",
                fontsize=9.5,
                fontweight="semibold",
            )
    ax.set_title("Éxito geométrico (tasa)", fontsize=10.8)

    failure_labels = {
        "timeout": "TO",
        "communication_timeout": "COM",
        "governor_limited_timeout": "GOV",
        "barrier_limited_timeout": "BAR",
        "stale_information_braking": "AGE",
        "uncontrolled_stop_required": "AUT",
        "support_unavailable": "SUP",
        "collision": "COL",
        "kinematic_limit": "KIN",
        "wrench_limit": "W",
        "numerical_failure": "NUM",
    }
    modes = list(failure_labels)
    dominant = np.zeros_like(pivot.to_numpy(), dtype=float)
    annotations: list[list[str]] = []
    for method in pivot.index:
        annotation_row: list[str] = []
        for scenario in pivot.columns:
            cell = governed[(governed["method"] == method) & (governed["scenario"] == scenario)]
            failures = cell[cell["failure_mode"] != "none"]["failure_mode"]
            if failures.empty:
                dominant[pivot.index.get_loc(method), pivot.columns.get_loc(scenario)] = 0
                annotation_row.append("—")
            else:
                counts = failures.value_counts()
                mode = str(counts.index[0])
                dominant[pivot.index.get_loc(method), pivot.columns.get_loc(scenario)] = modes.index(mode) + 1
                annotation_row.append(f"{failure_labels[mode]}\n{counts.iloc[0] / len(cell):.0%}")
        annotations.append(annotation_row)
    failure_colors = [
        "#f8fafc",
        "#9ca3af",
        "#60a5fa",
        "#f59e0b",
        "#a78bfa",
        "#22c55e",
        "#e11d48",
        "#dc2626",
        "#111827",
        "#0f766e",
        "#b45309",
        "#be185d",
    ]
    ax_failure.imshow(
        dominant,
        vmin=0,
        vmax=len(failure_colors) - 1,
        cmap=matplotlib.colors.ListedColormap(failure_colors),
        aspect="auto",
    )
    ax_failure.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax_failure.set_yticks(range(len(pivot.index)), [SHORT_METHOD_LABELS[item] for item in pivot.index])
    for i, row in enumerate(annotations):
        for j, value in enumerate(row):
            ax_failure.text(
                j,
                i,
                value,
                ha="center",
                va="center",
                fontsize=9.4,
                fontweight="semibold",
                color="white" if value.startswith(("AUT", "COL", "SUP")) else "#111827",
            )
    ax_failure.set_title("Terminal dominante (% de 30)", fontsize=10.8)
    for axis in (ax, ax_failure):
        axis.tick_params(axis="both", labelsize=9.5)
        axis.set_xticks(np.arange(-0.5, len(pivot.columns), 1), minor=True)
        axis.set_yticks(np.arange(-0.5, len(pivot.index), 1), minor=True)
        axis.grid(which="minor", color="white", linewidth=1.1)
        axis.tick_params(which="minor", bottom=False, left=False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def _plot_governor(frame: pd.DataFrame, sensitivity: pd.DataFrame, path: Path) -> None:
    paired_methods = sorted(set(frame.loc[frame["mode"] == "raw", "method"]))
    grouped = (
        frame[frame["method"].isin(paired_methods)]
        .groupby(["method", "mode"])[
            ["success", "physically_admissible_success", "physical_violation"]
        ]
        .mean()
        .reset_index()
    )
    x = np.arange(len(paired_methods))
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3))
    mode_labels = {"raw": "sin gobernador", "governed": "con gobernador"}
    for offset, mode in [(-0.18, "raw"), (0.18, "governed")]:
        selected = grouped[grouped["mode"] == mode].set_index("method").reindex(paired_methods)
        axes[0].bar(
            x + offset,
            selected["physically_admissible_success"],
            0.36,
            label=mode_labels[mode],
        )
        axes[0].scatter(
            x + offset,
            selected["success"],
            marker="D",
            s=22,
            color="#111827",
            zorder=4,
        )
    axes[0].set_title("Éxito físicamente admisible")
    axes[0].set_ylim(0, 1.0)
    axes[0].set_xticks(x, [METHOD_LABELS[item] for item in paired_methods], rotation=20, ha="right")
    axes[0].grid(axis="y", alpha=0.22)
    axes[0].text(0.02, 0.98, "rombo: éxito geométrico", transform=axes[0].transAxes, va="top", fontsize=7.5)

    method_colors = {
        "pd": "#2563eb",
        "lqi": "#7c3aed",
        "port_hamiltonian": "#0f766e",
        "mpc_central": "#c2410c",
    }
    for method in paired_methods:
        selected = sensitivity[sensitivity["method"] == method].sort_values("governor_step")
        color = method_colors[method]
        axes[1].plot(
            selected["governor_step"],
            selected["geometric_success_rate"],
            marker="o",
            linewidth=1.6,
            color=color,
        )
        axes[1].plot(
            selected["governor_step"],
            selected["physically_admissible_success_rate"],
            marker="s",
            linestyle="--",
            linewidth=1.35,
            color=color,
        )
        axes[1].plot(
            selected["governor_step"],
            selected["physical_violation_rate"],
            marker="x",
            linestyle=":",
            linewidth=1.35,
            color=color,
        )
    axes[1].set(
        xlim=(0.21, 0.04),
        ylim=(0, 1.0),
        xticks=[0.20, 0.10, 0.05],
        xlabel=r"paso de la cuadrícula $\Delta\alpha$",
        ylabel="tasa por ejecución",
        title="Sensibilidad: progreso, admisibilidad y violación",
    )
    axes[1].grid(alpha=0.22)
    method_handles = [
        Line2D([0], [0], color=method_colors[item], linewidth=1.7, label=METHOD_LABELS[item])
        for item in paired_methods
    ]
    metric_handles = [
        Line2D([0], [0], color="#374151", marker="o", label="éxito geom."),
        Line2D([0], [0], color="#374151", marker="s", linestyle="--", label="éxito físico"),
        Line2D([0], [0], color="#374151", marker="x", linestyle=":", label="violación realizada"),
    ]
    method_legend = axes[1].legend(
        handles=method_handles,
        frameon=False,
        fontsize=7.0,
        ncol=2,
        loc="lower left",
    )
    axes[1].add_artist(method_legend)
    axes[1].legend(
        handles=metric_handles,
        frameon=False,
        fontsize=6.9,
        loc="upper left",
    )
    axes[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_paired_effects(
    paired: pd.DataFrame,
    paired_endpoints: pd.DataFrame,
    path: Path,
) -> None:
    """Render seed-block effects without diagonal labels or dense legends."""

    order = ["pd", "lqi", "port_hamiltonian", "mpc_central"]
    indexed = paired.assign(
        method=paired["comparison"].str.split(":").str[0]
    ).set_index("method").reindex(order)
    labels = [SHORT_METHOD_LABELS[method] for method in order]
    y = np.arange(len(order))
    fig, (ax_success, ax_collision) = plt.subplots(
        2,
        1,
        figsize=(7.8, 3.45),
        sharey=False,
        constrained_layout=True,
    )

    success = indexed["success_risk_difference"].to_numpy(dtype=float)
    success_low = indexed["success_difference_ci95_low"].to_numpy(dtype=float)
    success_high = indexed["success_difference_ci95_high"].to_numpy(dtype=float)
    ax_success.errorbar(
        success,
        y,
        xerr=np.vstack([success - success_low, success_high - success]),
        fmt="o",
        color="#2563eb",
        ecolor="#2563eb",
        capsize=3,
        linewidth=1.1,
    )
    ax_success.axvline(0.0, color="#111827", linewidth=0.9)
    ax_success.set_yticks(y, labels)
    ax_success.invert_yaxis()
    ax_success.set_xlabel(r"$\Delta$ éxito geométrico (guarda $-$ crudo)")
    ax_success.set_title("Éxito geométrico · positivo favorece", loc="left")
    ax_success.grid(axis="x", alpha=0.25)

    collision = indexed["collision_risk_difference"].to_numpy(dtype=float)
    collision_low = indexed["collision_difference_ci95_low"].to_numpy(dtype=float)
    collision_high = indexed["collision_difference_ci95_high"].to_numpy(dtype=float)
    ax_collision.errorbar(
        collision,
        y,
        xerr=np.vstack(
            [collision - collision_low, collision_high - collision]
        ),
        fmt="o",
        color="#d97706",
        ecolor="#d97706",
        capsize=3,
        linewidth=1.1,
    )
    aggregate = paired_endpoints.set_index("endpoint").loc["collision"]
    ax_collision.errorbar(
        float(aggregate["difference_governed_minus_raw"]),
        len(order),
        xerr=np.asarray(
            [[
                float(aggregate["difference_governed_minus_raw"])
                - float(aggregate["difference_ci95_low"])
            ], [
                float(aggregate["difference_ci95_high"])
                - float(aggregate["difference_governed_minus_raw"])
            ]]
        ),
        fmt="D",
        color="#111827",
        ecolor="#111827",
        capsize=3,
        linewidth=1.1,
    )
    ax_collision.axvline(0.0, color="#111827", linewidth=0.9)
    ax_collision.set_yticks(
        np.arange(len(order) + 1),
        labels + ["Agregado H6"],
    )
    ax_collision.invert_yaxis()
    ax_collision.set_xlabel(r"$\Delta$ riesgo de colisión (guarda $-$ crudo)")
    ax_collision.set_title("Colisión · positivo perjudica", loc="left")
    ax_collision.grid(axis="x", alpha=0.25)
    for axis in (ax_success, ax_collision):
        axis.tick_params(labelsize=10.0)
        axis.xaxis.label.set_size(10.6)
        axis.yaxis.label.set_size(10.6)
        axis.title.set_size(11.1)
        axis.spines[["top", "right"]].set_visible(False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def _plot_trajectory(
    traces: dict[tuple[str, str, str], dict[str, np.ndarray]],
    scenario: Scenario,
    geometry: dict[str, Any],
    path: Path,
) -> None:
    methods = ("pd", "lqi", "port_hamiltonian", "mpc_central")
    colors = {
        "pd": "#2563eb",
        "lqi": "#ea580c",
        "port_hamiltonian": "#15803d",
        "mpc_central": "#7c3aed",
    }
    linestyles = {"pd": "-", "lqi": "--", "port_hamiltonian": "-.", "mpc_central": ":"}
    fig, (ax_map, ax_error) = plt.subplots(
        1,
        2,
        figsize=(10.0, 3.15),
        gridspec_kw={"width_ratios": (1.05, 1.65)},
    )
    for method in methods:
        key = (scenario.scenario_id, method, "governed")
        if key in traces:
            trace = traces[key]
            pose = trace["pose"]
            style = {
                "color": colors[method],
                "linestyle": linestyles[method],
                "linewidth": 2.4,
            }
            ax_map.plot(pose[:, 0], pose[:, 1], **style)
            distance = np.linalg.norm(pose[:, :2] - scenario.target[:2], axis=1)
            ax_error.plot(trace["time"], distance, label=METHOD_LABELS[method], **style)
    coalition_radius = _coalition_radius_m(geometry)
    safety_margin = float(geometry["safety_margin_m"])
    for center, radius in scenario.obstacles:
        ax_map.add_patch(
            plt.Circle(
                center,
                radius + coalition_radius + safety_margin,
                color="#b91c1c",
                alpha=0.14,
            )
        )
        ax_map.text(
            center[0],
            center[1] - 0.03,
            "zona excluida\npara la coalición",
            ha="center",
            va="center",
            fontsize=11.5,
            color="#991b1b",
        )
    ax_map.scatter(0.0, 0.0, marker="s", s=28, color="#111827", zorder=4)
    ax_map.scatter(scenario.target[0], scenario.target[1], marker="*", s=105, color="#f59e0b", zorder=4)
    lqi_key = (scenario.scenario_id, "lqi", "governed")
    if lqi_key in traces:
        lqi_pose = traces[lqi_key]["pose"]
        outside = np.flatnonzero(lqi_pose[:, 1] > 1.08)
        if outside.size:
            crossing = lqi_pose[outside[0]]
            ax_map.scatter(crossing[0], 1.07, marker="^", s=45, color=colors["lqi"], zorder=5)
            ax_map.annotate(
                "LQI sale del marco",
                xy=(crossing[0], 1.07),
                xytext=(0.50, 0.86),
                textcoords="axes fraction",
                fontsize=11.5,
                color=colors["lqi"],
                arrowprops={"arrowstyle": "->", "color": colors["lqi"], "linewidth": 0.8},
            )
    ax_map.set(
        xlim=(-0.25, 1.95),
        ylim=(-1.05, 1.15),
        xlabel="x [m]",
        ylabel="y [m]",
        aspect="equal",
        title="Geometría local de S5",
    )
    ax_error.set(
        xlabel="tiempo [s]",
        ylabel="distancia al destino [m]",
        title="Progreso y divergencia",
    )
    for axis in (ax_map, ax_error):
        axis.grid(alpha=0.20)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(labelsize=11)
        axis.xaxis.label.set_size(12)
        axis.yaxis.label.set_size(12)
        axis.title.set_size(13)
    ax_error.legend(frameon=False, fontsize=10.5, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_failure_trace(traces: dict[tuple[str, str, str], dict[str, np.ndarray]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.0), sharex=True)
    styles = {
        "S4": {"color": "#2563eb", "linestyle": "-"},
        "S6": {"color": "#ea580c", "linestyle": "--"},
    }
    for scenario_id in ("S4", "S6"):
        key = (scenario_id, "lqi", "governed")
        if key not in traces:
            continue
        trace = traces[key]
        style = styles[scenario_id]
        axes[0].plot(
            trace["time"],
            trace["scale"],
            label=f"{scenario_id} · nominal",
            linewidth=2.4,
            **style,
        )
        axes[0].plot(
            trace["time"],
            trace["brake_scale"],
            label=f"{scenario_id} · freno",
            linewidth=1.5,
            color=style["color"],
            linestyle=":" if scenario_id == "S4" else "-.",
        )
        axes[1].plot(trace["time"], trace["mech_margin"], label=scenario_id, linewidth=2.4, **style)
        missing_support = ~np.isfinite(trace["mech_margin"])
        if np.any(missing_support):
            axes[1].scatter(
                trace["time"][missing_support],
                np.full(int(np.sum(missing_support)), -0.05),
                marker="x",
                s=20,
                color=style["color"],
                linewidth=1.0,
            )
    axes[0].set(title="Acción certificada", ylabel="escala nominal / freno", xlabel="tiempo [s]")
    axes[1].set(title="Soporte y wrench", ylabel="margen mecánico", xlabel="tiempo [s]")
    axes[1].axhline(0.0, color="#6b7280", linewidth=0.8, alpha=0.55)
    axes[1].text(
        0.98,
        0.05,
        r"$\times$ soporte inviable",
        transform=axes[1].transAxes,
        ha="right",
        va="bottom",
        fontsize=9.5,
        color="#4b5563",
    )
    for axis in axes:
        axis.axvline(3.0, color="black", alpha=0.45, linewidth=0.9)
        axis.grid(alpha=0.20)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(labelsize=11)
        axis.xaxis.label.set_size(12)
        axis.yaxis.label.set_size(12)
        axis.title.set_size(13)
    axes[0].annotate(
        "pérdida",
        xy=(3.0, 0.04),
        xytext=(3.35, 0.27),
        fontsize=11.5,
        arrowprops={"arrowstyle": "->", "color": "#374151", "linewidth": 0.8},
    )
    axes[0].axvline(4.5, color="#2563eb", alpha=0.45, linewidth=0.9)
    axes[0].annotate(
        "restauración exógena",
        xy=(4.5, 0.04),
        xytext=(5.0, 0.45),
        fontsize=11.5,
        color="#1d4ed8",
        arrowprops={"arrowstyle": "->", "color": "#2563eb", "linewidth": 0.8},
    )
    axes[0].legend(frameon=False, fontsize=9.5, ncol=2, loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _plot_pareto(summary: pd.DataFrame, path: Path) -> None:
    governed = summary[summary["mode"] == "governed"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for _, row in governed.iterrows():
        ax.scatter(row["mean_bytes"], row["success_rate"], s=70)
        ax.annotate(row["method_label"], (row["mean_bytes"], row["success_rate"]), fontsize=8, xytext=(4, 4), textcoords="offset points")
    ax.set(xlabel="bytes medios por ejecución", ylabel="tasa de éxito")
    ax.grid(alpha=0.24)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _render_video(trace: dict[str, np.ndarray], scenario: Scenario, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.set(xlim=(-0.15, 1.85), ylim=(-0.35, 0.85), aspect="equal", xlabel="x [m]", ylabel="y [m]")
    for center, radius in scenario.obstacles:
        ax.add_patch(plt.Circle(center, radius, color="#991b1b", alpha=0.45))
    ax.scatter(scenario.target[0], scenario.target[1], marker="*", s=100, color="#f59e0b")
    path_line, = ax.plot([], [], color="#1d4ed8")
    payload_point, = ax.plot([], [], "o", color="#0f766e")
    title = ax.set_title("")

    def update(frame: int) -> tuple[Any, ...]:
        pose = trace["pose"][: frame + 1]
        path_line.set_data(pose[:, 0], pose[:, 1])
        payload_point.set_data([pose[-1, 0]], [pose[-1, 1]])
        title.set_text(f"{scenario.scenario_id} · t={trace['time'][frame]:.1f} s")
        return path_line, payload_point, title

    animation = FuncAnimation(fig, update, frames=len(trace["time"]), interval=100, blit=False)
    animation.save(path, writer=FFMpegWriter(fps=10, bitrate=850))
    plt.close(fig)


def _write_metrics(path: Path, metrics: dict[str, Any]) -> None:
    names = {
        "dynamic_runs": "SPTwoReadyDynamicRuns",
        "worlds": "SPTwoReadyWorlds",
        "n1_rows": "SPTwoReadyNOneRows",
        "n1_false": "SPTwoReadyNOneFalse",
        "n1_false_rate": "SPTwoReadyNOneFalseRate",
        "n2_rows": "SPTwoReadyNTwoRows",
        "n2_false": "SPTwoReadyNTwoFalse",
        "n2_reject_rate_percent": "SPTwoReadyNTwoRejectRate",
        "n2_supported_feasible": "SPTwoReadyNTwoFeasible",
        "n3_rows": "SPTwoReadyNThreeRows",
        "n3_leader_bytes": "SPTwoReadyNThreeLeaderBytes",
        "n3_virtual_bytes": "SPTwoReadyNThreeVirtualBytes",
        "n3_leader_rmse_position_m": "SPTwoReadyNThreeLeaderPositionRMSE",
        "n3_virtual_rmse_position_m": "SPTwoReadyNThreeVirtualPositionRMSE",
        "n3_leader_rmse_yaw_rad": "SPTwoReadyNThreeLeaderYawRMSE",
        "n3_virtual_rmse_yaw_rad": "SPTwoReadyNThreeVirtualYawRMSE",
        "n3_lossy_position_difference_m": "SPTwoReadyNThreeLossyPositionDifference",
        "n3_lossy_position_ci_low_m": "SPTwoReadyNThreeLossyPositionCILow",
        "n3_lossy_position_ci_high_m": "SPTwoReadyNThreeLossyPositionCIHigh",
        "n3_lossy_leader_age_s": "SPTwoReadyNThreeLossyLeaderAge",
        "n3_lossy_virtual_age_s": "SPTwoReadyNThreeLossyVirtualAge",
        "n3_lossy_leader_delivery": "SPTwoReadyNThreeLossyLeaderDelivery",
        "n3_lossy_virtual_delivery": "SPTwoReadyNThreeLossyVirtualDelivery",
        "n3_leader_delivered_bytes": "SPTwoReadyNThreeLeaderDeliveredBytes",
        "n3_virtual_delivered_bytes": "SPTwoReadyNThreeVirtualDeliveredBytes",
        "governed_success": "SPTwoReadyGovernedSuccess",
        "raw_success": "SPTwoReadyRawSuccess",
        "governed_collision": "SPTwoReadyGovernedCollision",
        "raw_collision": "SPTwoReadyRawCollision",
        "s6_success": "SPTwoReadySSixSuccess",
        "s3_success": "SPTwoReadySThreeSuccess",
        "s5_success": "SPTwoReadySFiveSuccess",
        "s6_collision": "SPTwoReadySSixCollision",
        "pd_governed_success": "SPTwoReadyPDGovernedSuccess",
        "pd_raw_success": "SPTwoReadyPDRawSuccess",
        "lqi_governed_success": "SPTwoReadyLQIGovernedSuccess",
        "lqi_raw_success": "SPTwoReadyLQIRawSuccess",
        "ph_governed_success": "SPTwoReadyPHGovernedSuccess",
        "ph_raw_success": "SPTwoReadyPHRawSuccess",
        "mpc_governed_success": "SPTwoReadyMPCGovernedSuccess",
        "mpc_raw_success": "SPTwoReadyMPCRawSuccess",
        "pd_difference": "SPTwoReadyPDDifference",
        "pd_ci_low": "SPTwoReadyPDCILow",
        "pd_ci_high": "SPTwoReadyPDCIHigh",
        "pd_holm_p": "SPTwoReadyPDHolmP",
        "pd_block_holm_p": "SPTwoReadyPDBlockHolmP",
        "lqi_difference": "SPTwoReadyLQIDifference",
        "lqi_ci_low": "SPTwoReadyLQICILow",
        "lqi_ci_high": "SPTwoReadyLQICIHigh",
        "lqi_holm_p": "SPTwoReadyLQIHolmP",
        "lqi_block_holm_p": "SPTwoReadyLQIBlockHolmP",
        "ph_difference": "SPTwoReadyPHDifference",
        "ph_ci_low": "SPTwoReadyPHCILow",
        "ph_ci_high": "SPTwoReadyPHCIHigh",
        "ph_holm_p": "SPTwoReadyPHHolmP",
        "ph_block_holm_p": "SPTwoReadyPHBlockHolmP",
        "lqi_collision_difference": "SPTwoReadyLQICollisionDifference",
        "mpc_difference": "SPTwoReadyMPCDifference",
        "mpc_ci_low": "SPTwoReadyMPCCILow",
        "mpc_ci_high": "SPTwoReadyMPCCIHigh",
        "mpc_holm_p": "SPTwoReadyMPCHolmP",
        "mpc_block_holm_p": "SPTwoReadyMPCBlockHolmP",
        "pd_collision_difference": "SPTwoReadyPDCollisionDifference",
        "pd_collision_ci_low": "SPTwoReadyPDCollisionCILow",
        "pd_collision_ci_high": "SPTwoReadyPDCollisionCIHigh",
        "lqi_collision_ci_low": "SPTwoReadyLQICollisionCILow",
        "lqi_collision_ci_high": "SPTwoReadyLQICollisionCIHigh",
        "ph_collision_difference": "SPTwoReadyPHCollisionDifference",
        "ph_collision_ci_low": "SPTwoReadyPHCollisionCILow",
        "ph_collision_ci_high": "SPTwoReadyPHCollisionCIHigh",
        "mpc_collision_difference": "SPTwoReadyMPCCollisionDifference",
        "mpc_collision_ci_low": "SPTwoReadyMPCCollisionCILow",
        "mpc_collision_ci_high": "SPTwoReadyMPCCollisionCIHigh",
        "paired_collision_difference": "SPTwoReadyPairedCollisionDifference",
        "paired_collision_ci_low": "SPTwoReadyPairedCollisionCILow",
        "paired_collision_ci_high": "SPTwoReadyPairedCollisionCIHigh",
        "paired_success_difference": "SPTwoReadyPairedSuccessDifference",
        "paired_success_ci_low": "SPTwoReadyPairedSuccessCILow",
        "paired_success_ci_high": "SPTwoReadyPairedSuccessCIHigh",
        "paired_admissible_success_difference": "SPTwoReadyPairedAdmissibleSuccessDifference",
        "paired_admissible_success_ci_low": "SPTwoReadyPairedAdmissibleSuccessCILow",
        "paired_admissible_success_ci_high": "SPTwoReadyPairedAdmissibleSuccessCIHigh",
        "pd_raw_physical_success": "SPTwoReadyPDRawPhysicalSuccess",
        "pd_governed_physical_success": "SPTwoReadyPDGovernedPhysicalSuccess",
        "pd_raw_violation": "SPTwoReadyPDRawViolation",
        "pd_governed_violation": "SPTwoReadyPDGovernedViolation",
        "pd_raw_command_infeasible": "SPTwoReadyPDRawCommandInfeasible",
        "pd_governed_command_infeasible": "SPTwoReadyPDGovernedCommandInfeasible",
        "lqi_raw_physical_success": "SPTwoReadyLQIRawPhysicalSuccess",
        "lqi_governed_physical_success": "SPTwoReadyLQIGovernedPhysicalSuccess",
        "lqi_raw_violation": "SPTwoReadyLQIRawViolation",
        "lqi_governed_violation": "SPTwoReadyLQIGovernedViolation",
        "lqi_raw_command_infeasible": "SPTwoReadyLQIRawCommandInfeasible",
        "lqi_governed_command_infeasible": "SPTwoReadyLQIGovernedCommandInfeasible",
        "ph_raw_physical_success": "SPTwoReadyPHRawPhysicalSuccess",
        "ph_governed_physical_success": "SPTwoReadyPHGovernedPhysicalSuccess",
        "ph_raw_violation": "SPTwoReadyPHRawViolation",
        "ph_governed_violation": "SPTwoReadyPHGovernedViolation",
        "ph_raw_command_infeasible": "SPTwoReadyPHRawCommandInfeasible",
        "ph_governed_command_infeasible": "SPTwoReadyPHGovernedCommandInfeasible",
        "mpc_raw_physical_success": "SPTwoReadyMPCRawPhysicalSuccess",
        "mpc_governed_physical_success": "SPTwoReadyMPCGovernedPhysicalSuccess",
        "mpc_raw_violation": "SPTwoReadyMPCRawViolation",
        "mpc_governed_violation": "SPTwoReadyMPCGovernedViolation",
        "mpc_raw_command_infeasible": "SPTwoReadyMPCRawCommandInfeasible",
        "mpc_governed_command_infeasible": "SPTwoReadyMPCGovernedCommandInfeasible",
        "paired_raw_realized_fraction": "SPTwoReadyPairedRawRealizedFraction",
        "paired_governed_realized_fraction": "SPTwoReadyPairedGovernedRealizedFraction",
        "paired_realized_fraction_difference_ci_low": "SPTwoReadyPairedRealizedFractionDifferenceCILow",
        "paired_realized_fraction_difference_ci_high": "SPTwoReadyPairedRealizedFractionDifferenceCIHigh",
        "paired_raw_max_violation_duration_s": "SPTwoReadyPairedRawMaxViolationDuration",
        "paired_governed_max_violation_duration_s": "SPTwoReadyPairedGovernedMaxViolationDuration",
        "paired_duration_difference_ci_low": "SPTwoReadyPairedDurationDifferenceCILow",
        "paired_duration_difference_ci_high": "SPTwoReadyPairedDurationDifferenceCIHigh",
        "paired_raw_min_kinematic_margin": "SPTwoReadyPairedRawMinKinematicMargin",
        "paired_governed_min_kinematic_margin": "SPTwoReadyPairedGovernedMinKinematicMargin",
        "paired_min_kinematic_difference_ci_low": "SPTwoReadyPairedMinKinematicDifferenceCILow",
        "paired_min_kinematic_difference_ci_high": "SPTwoReadyPairedMinKinematicDifferenceCIHigh",
        "paired_raw_min_mechanical_margin": "SPTwoReadyPairedRawMinMechanicalMargin",
        "paired_governed_min_mechanical_margin": "SPTwoReadyPairedGovernedMinMechanicalMargin",
        "pd_step_010_success": "SPTwoReadyPDStepTenSuccess",
        "pd_step_005_success": "SPTwoReadyPDStepFiveSuccess",
        "lqi_step_010_success": "SPTwoReadyLQIStepTenSuccess",
        "lqi_step_005_success": "SPTwoReadyLQIStepFiveSuccess",
        "ph_step_010_success": "SPTwoReadyPHStepTenSuccess",
        "ph_step_005_success": "SPTwoReadyPHStepFiveSuccess",
        "mpc_step_010_success": "SPTwoReadyMPCStepTenSuccess",
        "mpc_step_005_success": "SPTwoReadyMPCStepFiveSuccess",
        "pd_step_005_physical_success": "SPTwoReadyPDStepFivePhysicalSuccess",
        "pd_step_005_violation": "SPTwoReadyPDStepFiveViolation",
        "lqi_step_005_physical_success": "SPTwoReadyLQIStepFivePhysicalSuccess",
        "lqi_step_005_violation": "SPTwoReadyLQIStepFiveViolation",
        "ph_step_005_physical_success": "SPTwoReadyPHStepFivePhysicalSuccess",
        "ph_step_005_violation": "SPTwoReadyPHStepFiveViolation",
        "mpc_step_005_physical_success": "SPTwoReadyMPCStepFivePhysicalSuccess",
        "mpc_step_005_violation": "SPTwoReadyMPCStepFiveViolation",
    }
    lines = []
    for key, command in names.items():
        value = metrics[key]
        if key.endswith("_bytes"):
            rendered = str(int(round(float(value))))
        elif key.endswith("_holm_p"):
            rendered = (
                r"\ensuremath{<0{,}001}"
                if float(value) < 0.001
                else f"{float(value):.3f}".replace(".", "{,}")
            )
        elif isinstance(value, float):
            # Coma decimal, y sin decimales que solo aportan ceros: el
            # documento esta en castellano y «0,124» se lee, «0.124» no.
            text = f"{value:.3f}".rstrip("0").rstrip(".")
            rendered = (text or "0").replace(".", "{,}")
        else:
            rendered = str(value)
        lines.append(f"\\newcommand{{\\{command}}}{{{rendered}}}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_sp2_submit_ready_config(
    config_path: Path | str,
    *,
    resume_from_raw: bool = False,
) -> dict[str, Any]:
    """Execute the fixed CPU campaign and write auditable artifacts."""

    started = time.perf_counter()
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    output = Path(str(config["output_dir"]))
    for folder in ("raw", "processed", "figures", "traces", "videos", "generated", "audit", "protocol"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    frozen = output / "protocol" / "frozen_config.yaml"
    frozen_text = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    if resume_from_raw and frozen.exists() and frozen.read_text(encoding="utf-8") != frozen_text:
        raise ValueError("cannot resume SP2 postprocessing with a different frozen config")
    frozen.write_text(frozen_text, encoding="utf-8")

    seeds = [int(item) for item in config["dynamic"]["seeds"]]
    methods = [str(item) for item in config["dynamic"]["methods"]]
    raw_ablation = set(str(item) for item in config["dynamic"]["raw_ablation_methods"])
    scenario_ids = [str(item) for item in config["dynamic"]["scenarios"]]
    primary_governor_step = float(config["dynamic"].get("governor_grid_step", 0.2))
    sensitivity_steps = [
        float(item)
        for item in config["dynamic"].get(
            "governor_sensitivity_steps", [primary_governor_step]
        )
    ]
    representative: dict[tuple[str, str, str], dict[str, np.ndarray]] = {}

    if resume_from_raw:
        required_raw = {
            "n1": output / "raw" / "n1_kinematic_grid.csv",
            "n2": output / "raw" / "n2_mechanical_grid.csv",
            "n3": output / "raw" / "n3_network_runs.csv",
            "dynamic": output / "raw" / "n4_runs.csv",
            "sensitivity": output / "raw" / "n4_governor_sensitivity.csv",
        }
        missing = [str(item) for item in required_raw.values() if not item.exists()]
        if missing:
            raise FileNotFoundError(f"cannot resume; missing raw SP2 artifacts: {missing}")
        n1 = pd.read_csv(required_raw["n1"])
        n2 = pd.read_csv(required_raw["n2"])
        n3 = pd.read_csv(required_raw["n3"])
        dynamic = pd.read_csv(required_raw["dynamic"])
        sensitivity = pd.read_csv(required_raw["sensitivity"])
        for scenario_id in scenario_ids:
            for method in methods:
                for mode in (["raw", "governed"] if method in raw_ablation else ["governed"]):
                    trace_path = output / "traces" / f"{scenario_id}_{method}_{mode}.npz"
                    if not trace_path.exists():
                        raise FileNotFoundError(f"cannot resume; missing trace: {trace_path}")
                    with np.load(trace_path) as loaded:
                        representative[(scenario_id, method, mode)] = {
                            key: loaded[key] for key in loaded.files
                        }
    else:
        n1 = _run_n1(config["n1"])
        n2 = _run_n2(config["n2"])
        n3 = _run_n3(config["n3"])
        n1.to_csv(output / "raw" / "n1_kinematic_grid.csv", index=False)
        n2.to_csv(output / "raw" / "n2_mechanical_grid.csv", index=False)
        n3.to_csv(output / "raw" / "n3_network_runs.csv", index=False)

        dynamic_rows: list[dict[str, Any]] = []
        primary_governor_grid = _governor_grid(primary_governor_step)
        for scenario_id in scenario_ids:
            scenario = _scenario(scenario_id)
            for seed in seeds:
                for method in methods:
                    for mode in (["raw", "governed"] if method in raw_ablation else ["governed"]):
                        row, trace = _simulate(
                            scenario,
                            method,
                            mode,
                            seed,
                            config["dynamic"],
                            governor_grid=primary_governor_grid,
                        )
                        dynamic_rows.append(row)
                        if seed == seeds[0]:
                            representative[(scenario_id, method, mode)] = trace
        dynamic = pd.DataFrame(dynamic_rows)
        dynamic.to_csv(output / "raw" / "n4_runs.csv", index=False)

        sensitivity_rows: list[dict[str, Any]] = []
        for step_size in sensitivity_steps:
            if np.isclose(step_size, primary_governor_step):
                reused = dynamic[
                    (dynamic["mode"] == "governed")
                    & (dynamic["method"].isin(raw_ablation))
                ]
                for row in reused.to_dict(orient="records"):
                    sensitivity_rows.append({**row, "governor_step": step_size})
                continue
            sensitivity_grid = _governor_grid(step_size)
            for scenario_id in scenario_ids:
                scenario = _scenario(scenario_id)
                for seed in seeds:
                    for method in sorted(raw_ablation):
                        row, _ = _simulate(
                            scenario,
                            method,
                            "governed",
                            seed,
                            config["dynamic"],
                            governor_grid=sensitivity_grid,
                        )
                        sensitivity_rows.append({**row, "governor_step": step_size})
        sensitivity = pd.DataFrame(sensitivity_rows)
        sensitivity.to_csv(output / "raw" / "n4_governor_sensitivity.csv", index=False)

    n3_statistics = _n3_statistics(n3)
    summary = _summary(dynamic)
    sensitivity_summary = _governor_sensitivity_summary(sensitivity)
    paired = _paired_statistics(dynamic)
    paired_endpoints = _paired_endpoint_statistics(dynamic)
    hypotheses = _hypotheses(n1, n2, n3, n3_statistics, dynamic)
    summary.to_csv(output / "processed" / "controller_summary.csv", index=False)
    sensitivity_summary.to_csv(
        output / "processed" / "governor_sensitivity_summary.csv", index=False
    )
    paired.to_csv(output / "processed" / "paired_governor_statistics.csv", index=False)
    paired_endpoints.to_csv(
        output / "processed" / "paired_endpoint_statistics.csv", index=False
    )
    n3_statistics.to_csv(output / "processed" / "n3_architecture_statistics.csv", index=False)
    hypotheses.to_csv(output / "processed" / "hypotheses.csv", index=False)

    for (scenario_id, method, mode), trace in representative.items():
        np.savez_compressed(output / "traces" / f"{scenario_id}_{method}_{mode}.npz", **trace)

    _plot_n1(n1, output / "figures" / "fig-sp2-n1-envelope.pdf")
    _plot_n2(n2, output / "figures" / "fig-sp2-n2-model-comparison.pdf")
    _plot_n3(n3, n3_statistics, output / "figures" / "fig-sp2-n3-quality-communication.pdf")
    _plot_dynamic_matrix(dynamic, output / "figures" / "fig-sp2-n4-scenario-matrix.pdf")
    _plot_governor(
        dynamic,
        sensitivity_summary,
        output / "figures" / "fig-sp2-n4-governor-ablation.pdf",
    )
    _plot_paired_effects(
        paired,
        paired_endpoints,
        output / "figures" / "fig-sp2-n4-paired-effects.pdf",
    )
    _plot_trajectory(
        representative,
        _scenario("S0"),
        config["dynamic"]["geometry"],
        output / "figures" / "fig-sp2-n4-trajectory-s0.pdf",
    )
    _plot_trajectory(
        representative,
        _scenario("S5"),
        config["dynamic"]["geometry"],
        output / "figures" / "fig-sp2-n4-trajectory-s5.pdf",
    )
    _plot_failure_trace(representative, output / "figures" / "fig-sp2-n4-failure-trace.pdf")
    _plot_pareto(summary, output / "figures" / "fig-sp2-n4-quality-communication.pdf")

    if bool(config["dynamic"].get("render_videos", False)):
        for scenario_id in ("S0", "S5", "S6"):
            for method in ("pd", "lqi", "port_hamiltonian", "mpc_central"):
                key = (scenario_id, method, "governed")
                if key in representative:
                    _render_video(representative[key], _scenario(scenario_id), output / "videos" / f"{scenario_id}_{method}.mp4")

    governed = dynamic[dynamic["mode"] == "governed"]
    raw = dynamic[dynamic["mode"] == "raw"]
    n3_architecture = n3.groupby("architecture")[["bytes", "delivered_bytes", "rmse_position_m", "rmse_yaw_rad"]].mean()
    n3_network_architecture = n3.groupby(["network", "architecture"])[
        ["mean_age_s", "delivery_ratio"]
    ].mean()
    n3_statistics_index = n3_statistics.set_index("network")
    governed_scenario = governed.groupby("scenario")[["success", "collision"]].mean()
    controller_mode = dynamic.groupby(["method", "mode"])[
        [
            "success",
            "physically_admissible_success",
            "command_infeasible",
            "command_infeasible_fraction",
            "physical_violation",
            "realized_violation_fraction",
            "realized_violation_max_duration_s",
            "minimum_realized_kinematic_margin",
            "minimum_realized_mechanical_margin",
        ]
    ].mean()
    paired_index = paired.set_index("comparison")
    paired_endpoint_index = paired_endpoints.set_index("endpoint")
    sensitivity_index = sensitivity_summary.set_index(["method", "governor_step"])

    def controller_mean(method: str, mode: str, column: str) -> float:
        return float(controller_mode.loc[(method, mode), column])

    def sensitivity_mean(
        method: str,
        step: float,
        column: str = "geometric_success_rate",
    ) -> float:
        return float(sensitivity_index.loc[(method, step), column])

    def scenario_mean(scenario_id: str, column: str) -> float:
        if scenario_id not in governed_scenario.index:
            return float("nan")
        return float(governed_scenario.loc[scenario_id, column])

    metrics = {
        "dynamic_runs": len(dynamic),
        "worlds": len(scenario_ids) * len(seeds),
        "n1_rows": len(n1),
        "n1_false": int(n1["false_feasible"].sum()),
        "n1_false_rate": float(n1["false_feasible"].mean()),
        "n2_rows": len(n2),
        "n2_false": int(n2["bilateral_false_feasible"].sum()),
        "n2_reject_rate_percent": float(100.0 * n2["bilateral_false_feasible"].mean()),
        "n2_supported_feasible": int(n2["supported_feasible"].sum()),
        "n3_rows": len(n3),
        "n3_leader_bytes": float(n3_architecture.loc["leader_follower", "bytes"]),
        "n3_virtual_bytes": float(n3_architecture.loc["virtual_structure", "bytes"]),
        "n3_leader_delivered_bytes": float(
            n3_architecture.loc["leader_follower", "delivered_bytes"]
        ),
        "n3_virtual_delivered_bytes": float(
            n3_architecture.loc["virtual_structure", "delivered_bytes"]
        ),
        "n3_leader_rmse_position_m": float(
            n3_architecture.loc["leader_follower", "rmse_position_m"]
        ),
        "n3_virtual_rmse_position_m": float(
            n3_architecture.loc["virtual_structure", "rmse_position_m"]
        ),
        "n3_leader_rmse_yaw_rad": float(
            n3_architecture.loc["leader_follower", "rmse_yaw_rad"]
        ),
        "n3_virtual_rmse_yaw_rad": float(
            n3_architecture.loc["virtual_structure", "rmse_yaw_rad"]
        ),
        "n3_lossy_position_difference_m": float(
            n3_statistics_index.loc[
                "degraded", "difference_virtual_minus_leader_rmse_position_m"
            ]
        ),
        "n3_lossy_position_ci_low_m": float(
            n3_statistics_index.loc["degraded", "difference_ci95_low_rmse_position_m"]
        ),
        "n3_lossy_position_ci_high_m": float(
            n3_statistics_index.loc["degraded", "difference_ci95_high_rmse_position_m"]
        ),
        "n3_lossy_leader_age_s": float(
            n3_network_architecture.loc[("degraded", "leader_follower"), "mean_age_s"]
        ),
        "n3_lossy_virtual_age_s": float(
            n3_network_architecture.loc[("degraded", "virtual_structure"), "mean_age_s"]
        ),
        "n3_lossy_leader_delivery": float(
            n3_network_architecture.loc[("degraded", "leader_follower"), "delivery_ratio"]
        ),
        "n3_lossy_virtual_delivery": float(
            n3_network_architecture.loc[("degraded", "virtual_structure"), "delivery_ratio"]
        ),
        "governed_success": float(governed["success"].mean()),
        "raw_success": float(raw["success"].mean()),
        "governed_collision": float(governed["collision"].mean()),
        "raw_collision": float(raw["collision"].mean()),
        "s6_success": float(governed[governed["scenario"] == "S6"]["success"].mean()),
        "s3_success": scenario_mean("S3", "success"),
        "s5_success": scenario_mean("S5", "success"),
        "s6_collision": scenario_mean("S6", "collision"),
        "pd_governed_success": controller_mean("pd", "governed", "success"),
        "pd_raw_success": controller_mean("pd", "raw", "success"),
        "lqi_governed_success": controller_mean("lqi", "governed", "success"),
        "lqi_raw_success": controller_mean("lqi", "raw", "success"),
        "ph_governed_success": controller_mean("port_hamiltonian", "governed", "success"),
        "ph_raw_success": controller_mean("port_hamiltonian", "raw", "success"),
        "mpc_governed_success": controller_mean("mpc_central", "governed", "success"),
        "mpc_raw_success": controller_mean("mpc_central", "raw", "success"),
        "pd_difference": float(paired_index.loc["pd:governed-minus-raw", "success_risk_difference"]),
        "pd_ci_low": float(paired_index.loc["pd:governed-minus-raw", "success_difference_ci95_low"]),
        "pd_ci_high": float(paired_index.loc["pd:governed-minus-raw", "success_difference_ci95_high"]),
        "pd_holm_p": float(paired_index.loc["pd:governed-minus-raw", "mcnemar_holm_p"]),
        "pd_block_holm_p": float(
            paired_index.loc[
                "pd:governed-minus-raw", "success_seed_wilcoxon_holm_p"
            ]
        ),
        "lqi_difference": float(paired_index.loc["lqi:governed-minus-raw", "success_risk_difference"]),
        "lqi_ci_low": float(
            paired_index.loc["lqi:governed-minus-raw", "success_difference_ci95_low"]
        ),
        "lqi_ci_high": float(
            paired_index.loc["lqi:governed-minus-raw", "success_difference_ci95_high"]
        ),
        "lqi_holm_p": float(
            paired_index.loc["lqi:governed-minus-raw", "mcnemar_holm_p"]
        ),
        "lqi_block_holm_p": float(
            paired_index.loc[
                "lqi:governed-minus-raw", "success_seed_wilcoxon_holm_p"
            ]
        ),
        "ph_difference": float(paired_index.loc["port_hamiltonian:governed-minus-raw", "success_risk_difference"]),
        "ph_ci_low": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw", "success_difference_ci95_low"
            ]
        ),
        "ph_ci_high": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw", "success_difference_ci95_high"
            ]
        ),
        "ph_holm_p": float(
            paired_index.loc["port_hamiltonian:governed-minus-raw", "mcnemar_holm_p"]
        ),
        "ph_block_holm_p": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw",
                "success_seed_wilcoxon_holm_p",
            ]
        ),
        "lqi_collision_difference": float(paired_index.loc["lqi:governed-minus-raw", "collision_risk_difference"]),
        "mpc_difference": float(paired_index.loc["mpc_central:governed-minus-raw", "success_risk_difference"]),
        "mpc_ci_low": float(paired_index.loc["mpc_central:governed-minus-raw", "success_difference_ci95_low"]),
        "mpc_ci_high": float(paired_index.loc["mpc_central:governed-minus-raw", "success_difference_ci95_high"]),
        "mpc_holm_p": float(
            paired_index.loc["mpc_central:governed-minus-raw", "mcnemar_holm_p"]
        ),
        "mpc_block_holm_p": float(
            paired_index.loc[
                "mpc_central:governed-minus-raw", "success_seed_wilcoxon_holm_p"
            ]
        ),
        "pd_collision_difference": float(
            paired_index.loc["pd:governed-minus-raw", "collision_risk_difference"]
        ),
        "pd_collision_ci_low": float(
            paired_index.loc[
                "pd:governed-minus-raw", "collision_difference_ci95_low"
            ]
        ),
        "pd_collision_ci_high": float(
            paired_index.loc[
                "pd:governed-minus-raw", "collision_difference_ci95_high"
            ]
        ),
        "lqi_collision_ci_low": float(
            paired_index.loc[
                "lqi:governed-minus-raw", "collision_difference_ci95_low"
            ]
        ),
        "lqi_collision_ci_high": float(
            paired_index.loc[
                "lqi:governed-minus-raw", "collision_difference_ci95_high"
            ]
        ),
        "ph_collision_difference": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw", "collision_risk_difference"
            ]
        ),
        "ph_collision_ci_low": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw",
                "collision_difference_ci95_low",
            ]
        ),
        "ph_collision_ci_high": float(
            paired_index.loc[
                "port_hamiltonian:governed-minus-raw",
                "collision_difference_ci95_high",
            ]
        ),
        "mpc_collision_difference": float(
            paired_index.loc[
                "mpc_central:governed-minus-raw", "collision_risk_difference"
            ]
        ),
        "mpc_collision_ci_low": float(
            paired_index.loc[
                "mpc_central:governed-minus-raw", "collision_difference_ci95_low"
            ]
        ),
        "mpc_collision_ci_high": float(
            paired_index.loc[
                "mpc_central:governed-minus-raw", "collision_difference_ci95_high"
            ]
        ),
        "paired_collision_difference": float(
            paired_endpoint_index.loc[
                "collision", "difference_governed_minus_raw"
            ]
        ),
        "paired_collision_ci_low": float(
            paired_endpoint_index.loc["collision", "difference_ci95_low"]
        ),
        "paired_collision_ci_high": float(
            paired_endpoint_index.loc["collision", "difference_ci95_high"]
        ),
        "paired_success_difference": float(
            paired_endpoint_index.loc["success", "difference_governed_minus_raw"]
        ),
        "paired_success_ci_low": float(
            paired_endpoint_index.loc["success", "difference_ci95_low"]
        ),
        "paired_success_ci_high": float(
            paired_endpoint_index.loc["success", "difference_ci95_high"]
        ),
        "paired_admissible_success_difference": float(
            paired_endpoint_index.loc[
                "physically_admissible_success", "difference_governed_minus_raw"
            ]
        ),
        "paired_admissible_success_ci_low": float(
            paired_endpoint_index.loc[
                "physically_admissible_success", "difference_ci95_low"
            ]
        ),
        "paired_admissible_success_ci_high": float(
            paired_endpoint_index.loc[
                "physically_admissible_success", "difference_ci95_high"
            ]
        ),
        "pd_raw_physical_success": controller_mean("pd", "raw", "physically_admissible_success"),
        "pd_governed_physical_success": controller_mean("pd", "governed", "physically_admissible_success"),
        "pd_raw_violation": controller_mean("pd", "raw", "physical_violation"),
        "pd_governed_violation": controller_mean("pd", "governed", "physical_violation"),
        "pd_raw_command_infeasible": controller_mean("pd", "raw", "command_infeasible"),
        "pd_governed_command_infeasible": controller_mean("pd", "governed", "command_infeasible"),
        "lqi_raw_physical_success": controller_mean("lqi", "raw", "physically_admissible_success"),
        "lqi_governed_physical_success": controller_mean("lqi", "governed", "physically_admissible_success"),
        "lqi_raw_violation": controller_mean("lqi", "raw", "physical_violation"),
        "lqi_governed_violation": controller_mean("lqi", "governed", "physical_violation"),
        "lqi_raw_command_infeasible": controller_mean("lqi", "raw", "command_infeasible"),
        "lqi_governed_command_infeasible": controller_mean("lqi", "governed", "command_infeasible"),
        "ph_raw_physical_success": controller_mean("port_hamiltonian", "raw", "physically_admissible_success"),
        "ph_governed_physical_success": controller_mean("port_hamiltonian", "governed", "physically_admissible_success"),
        "ph_raw_violation": controller_mean("port_hamiltonian", "raw", "physical_violation"),
        "ph_governed_violation": controller_mean("port_hamiltonian", "governed", "physical_violation"),
        "ph_raw_command_infeasible": controller_mean("port_hamiltonian", "raw", "command_infeasible"),
        "ph_governed_command_infeasible": controller_mean("port_hamiltonian", "governed", "command_infeasible"),
        "mpc_raw_physical_success": controller_mean("mpc_central", "raw", "physically_admissible_success"),
        "mpc_governed_physical_success": controller_mean("mpc_central", "governed", "physically_admissible_success"),
        "mpc_raw_violation": controller_mean("mpc_central", "raw", "physical_violation"),
        "mpc_governed_violation": controller_mean("mpc_central", "governed", "physical_violation"),
        "mpc_raw_command_infeasible": controller_mean("mpc_central", "raw", "command_infeasible"),
        "mpc_governed_command_infeasible": controller_mean("mpc_central", "governed", "command_infeasible"),
        "paired_raw_realized_fraction": float(
            dynamic[(dynamic["mode"] == "raw") & dynamic["method"].isin(raw_ablation)][
                "realized_violation_fraction"
            ].mean()
        ),
        "paired_governed_realized_fraction": float(
            dynamic[
                (dynamic["mode"] == "governed")
                & dynamic["method"].isin(raw_ablation)
            ]["realized_violation_fraction"].mean()
        ),
        "paired_realized_fraction_difference_ci_low": float(
            paired_endpoint_index.loc[
                "realized_violation_fraction", "difference_ci95_low"
            ]
        ),
        "paired_realized_fraction_difference_ci_high": float(
            paired_endpoint_index.loc[
                "realized_violation_fraction", "difference_ci95_high"
            ]
        ),
        "paired_raw_max_violation_duration_s": float(
            dynamic[(dynamic["mode"] == "raw") & dynamic["method"].isin(raw_ablation)][
                "realized_violation_max_duration_s"
            ].mean()
        ),
        "paired_governed_max_violation_duration_s": float(
            dynamic[
                (dynamic["mode"] == "governed")
                & dynamic["method"].isin(raw_ablation)
            ]["realized_violation_max_duration_s"].mean()
        ),
        "paired_duration_difference_ci_low": float(
            paired_endpoint_index.loc[
                "realized_violation_max_duration_s", "difference_ci95_low"
            ]
        ),
        "paired_duration_difference_ci_high": float(
            paired_endpoint_index.loc[
                "realized_violation_max_duration_s", "difference_ci95_high"
            ]
        ),
        "paired_raw_min_kinematic_margin": float(
            dynamic[(dynamic["mode"] == "raw") & dynamic["method"].isin(raw_ablation)][
                "minimum_realized_kinematic_margin"
            ].mean()
        ),
        "paired_governed_min_kinematic_margin": float(
            dynamic[
                (dynamic["mode"] == "governed")
                & dynamic["method"].isin(raw_ablation)
            ]["minimum_realized_kinematic_margin"].mean()
        ),
        "paired_min_kinematic_difference_ci_low": float(
            paired_endpoint_index.loc[
                "minimum_realized_kinematic_margin", "difference_ci95_low"
            ]
        ),
        "paired_min_kinematic_difference_ci_high": float(
            paired_endpoint_index.loc[
                "minimum_realized_kinematic_margin", "difference_ci95_high"
            ]
        ),
        "paired_raw_min_mechanical_margin": float(
            dynamic[(dynamic["mode"] == "raw") & dynamic["method"].isin(raw_ablation)][
                "minimum_realized_mechanical_margin"
            ].mean()
        ),
        "paired_governed_min_mechanical_margin": float(
            dynamic[
                (dynamic["mode"] == "governed")
                & dynamic["method"].isin(raw_ablation)
            ]["minimum_realized_mechanical_margin"].mean()
        ),
        "pd_step_010_success": sensitivity_mean("pd", 0.10),
        "pd_step_005_success": sensitivity_mean("pd", 0.05),
        "lqi_step_010_success": sensitivity_mean("lqi", 0.10),
        "lqi_step_005_success": sensitivity_mean("lqi", 0.05),
        "ph_step_010_success": sensitivity_mean("port_hamiltonian", 0.10),
        "ph_step_005_success": sensitivity_mean("port_hamiltonian", 0.05),
        "mpc_step_010_success": sensitivity_mean("mpc_central", 0.10),
        "mpc_step_005_success": sensitivity_mean("mpc_central", 0.05),
        "pd_step_005_physical_success": sensitivity_mean(
            "pd", 0.05, "physically_admissible_success_rate"
        ),
        "pd_step_005_violation": sensitivity_mean(
            "pd", 0.05, "physical_violation_rate"
        ),
        "lqi_step_005_physical_success": sensitivity_mean(
            "lqi", 0.05, "physically_admissible_success_rate"
        ),
        "lqi_step_005_violation": sensitivity_mean(
            "lqi", 0.05, "physical_violation_rate"
        ),
        "ph_step_005_physical_success": sensitivity_mean(
            "port_hamiltonian", 0.05, "physically_admissible_success_rate"
        ),
        "ph_step_005_violation": sensitivity_mean(
            "port_hamiltonian", 0.05, "physical_violation_rate"
        ),
        "mpc_step_005_physical_success": sensitivity_mean(
            "mpc_central", 0.05, "physically_admissible_success_rate"
        ),
        "mpc_step_005_violation": sensitivity_mean(
            "mpc_central", 0.05, "physical_violation_rate"
        ),
    }
    _write_metrics(output / "generated" / "metrics.tex", metrics)
    feasible_n1 = n1[n1["feasible"] == 1]
    per_seed_sections = (
        feasible_n1.groupby(["seed", "radius_m", "speed_mps"])["omega_rad_s"]
        .max()
        .reset_index()
    )
    sampled_sections = []
    for (radius, speed), section in per_seed_sections.groupby(["radius_m", "speed_mps"]):
        sampled_sections.append(
            {
                "radius_m": float(radius),
                "v_x_mps": float(speed),
                "v_y_mps": 0.0,
                "omega_max_q05_rad_s": float(np.quantile(section["omega_rad_s"], 0.05)),
                "seeds_with_feasible_sample": int(section["seed"].nunique()),
            }
        )
    geometry = config["dynamic"]["geometry"]
    coalition_radius = _coalition_radius_m(geometry)
    envelope = {
        "interface": "SP2_to_SP3_virtual_vehicle_v3",
        "model_scope": "reduced_planar_supported_load",
        "hardware_validated": False,
        "units": {
            "linear_velocity": "m/s",
            "yaw_rate": "rad/s",
            "linear_acceleration": "m/s^2",
            "yaw_acceleration": "rad/s^2",
        },
        "formation_offsets_body_m": _offsets().tolist(),
        "footprint": {
            "model": "conservative_circumscribed_disc",
            "radius_m": coalition_radius,
            "payload_half_extents_m": geometry["payload_half_extents_m"],
            "robot_radius_m": float(geometry["robot_radius_m"]),
            "safety_margin_m": float(geometry["safety_margin_m"]),
        },
        "sampled_kinematic_twist_sections": sampled_sections,
        "sampled_kinematic_margin_min": float(feasible_n1["margin"].min()),
        "sampled_mechanical_margin_min": float(
            n2.loc[n2["supported_feasible"] == 1, "supported_utilization"].rsub(1.0).min()
        ),
        "governor": {
            "implementation": "govern_acceleration",
            "nominal_scale_grid": [1.0, 0.8, 0.6, 0.4, 0.2],
            "brake_scale_grid": [1.0, 0.8, 0.6, 0.4, 0.2],
            "modes": ["execute", "brake", "hold", "uncontrolled_stop_required"],
            "brake_gain": float(config["dynamic"]["simulation"]["brake_gain"]),
            "information_max_age_s": float(
                config["dynamic"]["simulation"]["information_max_age_s"]
            ),
            "wrench_set": "sequential_hat_W_C",
            "barrier_revalidated_for_each_candidate": True,
            "terminal_criterion": config["dynamic"]["terminal"],
        },
        "failure_policy": {
            "support_infeasible": "uncontrolled_stop_required_and_request_replacement",
            "communication_stale": "brake_or_hold_if_jointly_feasible",
        },
        "limitations": [
            "twist sections sample only non-negative yaw rate and zero lateral body speed",
            "mechanical margin is observed on the N2 demand grid",
            "footprint parameters belong to the reduced model, not calibrated hardware",
            "traction is an isotropic configured surrogate, not an identified Pioneer 3-DX envelope",
            "autonomous replacement travel and docking are not executed",
        ],
    }
    (output / "operational_envelope.json").write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    analysis_contract = {
        "analysis_version": "SP2_HONORS_v3_review_revision_1",
        "confirmatory_unit": "seed block",
        "independent_seed_blocks": len(seeds),
        "scenarios_preserved_per_block": len(scenario_ids),
        "bootstrap_resamples": 5_000,
        "analysis_seeds": {
            "controller_pairs": 64001,
            "network_architectures": 64002,
            "aggregate_endpoints": 64003,
        },
        "multiplicity": "Holm over the four controller-wise paired contrasts",
        "controller_tuning_provenance": (
            "non-optimized engineering selection fixed before opening the "
            "experimental seeds; no archived disjoint tuning set, search log, "
            "or independent optimization campaign exists"
        ),
        "seed_count_rationale": (
            "30 seed blocks were fixed as a computational budget before analysis; "
            "no prospective power calculation is claimed, and achieved precision "
            "is reported through block-bootstrap intervals"
        ),
        "controller_comparison_scope": (
            "descriptive across controller families; confirmatory inference is limited "
            "to each controller compared with itself with and without the governor"
        ),
        "terminal_threshold_scope": (
            "study-defined simulation acceptance tolerances, not calibrated industrial "
            "accuracy requirements"
        ),
        "dt_sensitivity": (
            "not executed in this campaign; changing dt also changes sampled noise and "
            "communication timing, so a separate continuous-time disturbance contract "
            "is required"
        ),
        "post_hoc_diagnostics": [
            "controller-wise collision effects used to interpret aggregate H6",
        ],
    }
    (output / "protocol" / "analysis_contract.json").write_text(
        json.dumps(analysis_contract, indent=2), encoding="utf-8"
    )
    audit = {
        "status": "PASS",
        "checks": {
            "all_dynamic_runs_accounted": bool(len(dynamic) == len(scenario_ids) * len(seeds) * (len(methods) + len(raw_ablation))),
            "all_sensitivity_runs_accounted": bool(
                len(sensitivity)
                == len(scenario_ids)
                * len(seeds)
                * len(raw_ablation)
                * len(sensitivity_steps)
            ),
            "paired_world_hashes": bool(dynamic.groupby(["scenario", "seed"])["world_hash"].nunique().max() == 1),
            "no_nan_pose_metrics": bool(np.isfinite(dynamic["final_position_error_m"]).all()),
            "pose_errors_have_separate_units": bool(
                {"rmse_position_m", "rmse_yaw_rad"}.issubset(n3.columns)
                and {
                    "state_estimate_rmse_position_m",
                    "state_estimate_rmse_yaw_rad",
                }.issubset(dynamic.columns)
            ),
            "terminal_speeds_have_separate_units": bool(
                {
                    "final_linear_speed_mps",
                    "final_angular_speed_rad_s",
                }.issubset(dynamic.columns)
            ),
            "failures_preserved": set(dynamic["termination"]).issubset({"target_reached", "collision", "timeout", "numerical_failure"}),
            "failure_modes_recorded": bool(dynamic["failure_mode"].notna().all()),
            "physical_endpoints_recorded": bool(
                {
                    "physically_admissible_success",
                    "physical_violation",
                    "kinematic_violation",
                    "wrench_violation",
                    "support_failure",
                    "command_infeasible",
                    "command_infeasible_fraction",
                    "realized_violation_fraction",
                    "realized_violation_max_duration_s",
                }.issubset(dynamic.columns)
            ),
            "joint_barrier_revalidation": True,
            "n3_byte_accounting_conserved": bool(
                n3["generated_bytes"].eq(n3["queued_bytes"] + n3["dropped_bytes"]).all()
                and n3["queued_bytes"].eq(n3["delivered_bytes"]).all()
            ),
            "central_method_labelled": bool(dynamic.loc[dynamic["method"] == "mpc_central", "centralized"].eq(1).all()),
            "paired_statistics_use_seed_blocks": bool(
                paired["independent_seed_blocks"].eq(len(seeds)).all()
                and paired["scenarios_per_seed"].eq(len(scenario_ids)).all()
            ),
            "paired_endpoint_intervals_finite": bool(
                np.isfinite(
                    paired_endpoints[
                        ["difference_ci95_low", "difference_ci95_high"]
                    ].to_numpy(dtype=float)
                ).all()
                and (
                    paired_endpoints["difference_ci95_low"]
                    <= paired_endpoints["difference_ci95_high"]
                ).all()
            ),
            "h6_negative_result_preserved": bool(
                hypotheses.loc[
                    hypotheses["hypothesis"] == "H6", "supported_in_sample"
                ].eq(0).all()
                and float(
                    paired_endpoint_index.loc[
                        "collision", "difference_governed_minus_raw"
                    ]
                )
                > 0.0
            ),
            "caging_kept_separate": True,
            "coppeliasim_rerun": False,
        },
        "external_simulator_validation": "not_part_of_this_protocol",
        "model_scope": "CPU reduced-order planar supported-load simulation with 2.5-D static contact checks",
        "not_claimed": [
            "hardware validation",
            "global stability",
            "continuous-time collision invariance",
            "optimal distributed control",
            "autonomous physical replacement",
        ],
    }
    audit["status"] = "PASS" if all(value for key, value in audit["checks"].items() if key != "coppeliasim_rerun") else "FAIL"
    (output / "audit" / "campaign_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    postprocessing_elapsed_s = time.perf_counter() - started
    raw_generation_span_s = 0.0
    if resume_from_raw:
        raw_timestamps = [item.stat().st_mtime for item in (output / "raw").glob("*.csv")]
        if raw_timestamps:
            raw_generation_span_s = max(raw_timestamps) - min(raw_timestamps)
    manifest = {
        "experiment_id": config["experiment_id"],
        "status": "complete" if audit["status"] == "PASS" else "failed_audit",
        "config": str(path),
        "config_sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(),
        "git_sha_at_execution": _git_sha(),
        "postprocessing_resumed_from_raw": bool(resume_from_raw),
        "timing_scope": (
            "raw_file_span_plus_resumed_postprocessing"
            if resume_from_raw
            else "single_complete_process"
        ),
        "hardware": _hardware(),
        "elapsed_wall_s": raw_generation_span_s + postprocessing_elapsed_s,
        "metrics": metrics,
        "artifacts": sorted(str(item.relative_to(output)) for item in output.rglob("*") if item.is_file()),
        "postprocessing_source_sha256": {
            str(item): _file_sha256(item)
            for item in sorted(Path("src/viu_mrob_tfm/sp2_canonical").glob("*.py"))
        },
        "raw_sha256": {
            str(item.relative_to(output)): _file_sha256(item)
            for item in sorted((output / "raw").glob("*.csv"))
        },
        "artifact_sha256": {
            str(item.relative_to(output)): _file_sha256(item)
            for item in sorted(output.rglob("*"))
            if item.is_file() and item.name != "manifest.json"
        },
        "raw_provenance_note": (
            "SHA256 values were recorded during postprocessing resumed from raw; "
            "they verify the current archive but do not prove that the current "
            "untracked source tree generated the historical raw files."
            if resume_from_raw
            else "Raw and processed artifacts were generated in this single process."
        ),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


__all__ = ["METHOD_LABELS", "SCENARIO_LABELS", "run_sp2_submit_ready_config"]
