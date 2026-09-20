"""Reproducible runner and audit artifacts for the Cargo campaign."""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import yaml

from .backends import CargoBackend, DeterministicCargoBackend
from .config import CampaignConfig, load_config
from .controller import CargoPoseController, Observation, wrap_angle
from .coppelia_backend import CoppeliaMuJoCoBackend
from .design import RunSpec, build_run_specs, build_worlds, design_hash
from .guards import GuardDecision, evaluate_guard
from .inference import write_inference
from .preflight import (
    CALIBRATION_GATE_FIELDS,
    OPERATIONAL_GATE_FIELDS,
    PHYSICAL_GATE_FIELDS,
    PreflightAttestation,
    PreflightEvidenceError,
    validate_preflight_evidence,
)


RUN_FIELDS = (
    "run_id", "phase", "cell_id", "cell_index", "seed_index", "seed", "world_hash",
    "coalition", "active_robot_count", "longitudinal_acceleration_m_s2",
    "guard", "guard_accepted", "guard_reason", "capacity_margin_kg",
    "guard_wrench_residual_normalized", "guard_wrench_utilization", "guard_support_margin",
    "guard_wheel_margin", "dt_s", "controller_id", "backend_kind", "evidence_class",
    "execution_status", "physical_success", "classification", "steps", "duration_s",
    "contact_duty", "max_relative_slip_m", "collision_count", "final_position_error_m",
    "final_yaw_error_rad", "final_linear_speed_m_s", "final_angular_speed_rad_s",
    "dwell_achieved", "nan_detected", "saturation_count", "wrench_model_residual_mean",
    "allocation_residual_mean", "allocation_residual_max", "allocation_utilization_max",
    "allocation_saturation_count", "wheel_saturation_count",
    "max_robot_drive_force_n", "wheel_drive_force_gate_pass",
    "calibration_status", "sensor_static_relative_error",
    "valid_force_sensor_count", "dynamically_enabled_force_sensor_count",
    "expected_static_force_n", "measured_static_force_raw_n",
    "measured_static_force_n", "sensor_vertical_tare_sum_n",
    "force_transmission_relative_error", "force_transmission_status",
    "wheel_twist_relative_error", "wheel_twist_status",
    "config_readback_max_abs_error", "support_overlap_max_abs_error_m",
    "ack_reset_sequence", "ack_contract_hash", "ack_run_start_simulation_time_s",
    "ack_engine", "ack_actuation_contract",
    "sensor_gate_pass", "force_transmission_gate_pass", "wheel_twist_gate_pass",
    "scene_actuation_audit_pass", "config_readback_gate_pass", "contact_gate_pass",
    "slip_gate_pass", "collision_gate_pass", "terminal_gate_pass", "error_type", "error_message",
)

SERIES_FIELDS = (
    "run_id", "phase", "world_hash", "guard", "guard_accepted", "dt_s", "step", "time_s",
    "payload_x_m", "payload_y_m", "payload_yaw_rad", "payload_vx_m_s", "payload_vy_m_s",
    "payload_omega_rad_s", "measured_fx_n", "measured_fy_n", "measured_tau_n_m",
    "reference_fx_n", "reference_fy_n", "reference_tau_n_m", "contact_duty_step",
    "allocated_fx_n", "allocated_fy_n", "allocated_tau_n_m",
    "allocation_residual_normalized", "allocation_utilization",
    "allocation_saturation_count", "wheel_saturation_count",
    "max_relative_slip_m", "collision_count", "wheel_speed_abs_max_rad_s", "saturation_count",
    "max_robot_drive_force_n",
    *(f"normal_force_r{index}_n" for index in range(1, 5)),
    *(f"contact_active_r{index}" for index in range(1, 5)),
    *(
        f"wheel_speed_r{index}_{side}_rad_s"
        for index in range(1, 5)
        for side in ("left", "right")
    ),
    *(
        f"wheel_drive_force_r{index}_{side}_n"
        for index in range(1, 5)
        for side in ("left", "right")
    ),
    "nan_detected",
)


@dataclass(frozen=True, slots=True)
class CampaignResult:
    output_dir: Path
    run_count: int
    completed_count: int
    failed_count: int
    manifest_path: Path


def _finite_observation(observation: Observation) -> bool:
    arrays = (
        observation.payload_pose_m_rad,
        observation.payload_twist_m_s_rad_s,
        observation.robot_pose_m_rad,
        observation.wheel_speed_rad_s,
        observation.wheel_drive_force_n,
        observation.measured_wrench_body,
        observation.normal_force_n,
        observation.relative_slip_m,
    )
    return all(np.isfinite(np.asarray(value, dtype=float)).all() for value in arrays)


def _active(values: np.ndarray, observation: Observation) -> np.ndarray:
    mask = np.asarray(observation.active_robot_mask, dtype=bool)
    array = np.asarray(values)
    if mask.shape != (array.shape[0],) or not np.any(mask):
        raise ValueError("observation has an invalid active-robot mask")
    return array[mask]


def _json_dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _git_dirty() -> bool | None:
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
    )
    return bool(result.stdout.strip()) if result.returncode == 0 else None


def _classification(predicted: bool, observed: bool) -> str:
    return {
        (True, True): "true_positive",
        (True, False): "false_positive",
        (False, True): "false_negative",
        (False, False): "true_negative",
    }[(predicted, observed)]


def _all_physical_runs_pass(rows: list[dict[str, object]]) -> bool:
    """Require every primary and sensitivity run to close every physical gate."""

    return bool(rows) and all(
        row.get("execution_status") == "completed"
        and bool(row.get("physical_success"))
        and all(bool(row.get(gate)) for gate in PHYSICAL_GATE_FIELDS)
        for row in rows
    )


def _is_physical_coppelia_backend(backend: CargoBackend) -> bool:
    metadata = backend.metadata
    return bool(
        metadata.backend_kind == "coppeliasim_mujoco"
        and metadata.evidence_class == "physical_coppeliasim_candidate"
        and metadata.engine == "mujoco"
        and metadata.synchronous_stepping is True
        and metadata.actuator_contract == "wheel_velocity_only"
    )


def _prepare_output(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty campaign directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _default_backend(config: CampaignConfig, output_dir: Path) -> CargoBackend:
    if config.backend.kind == "deterministic_contract":
        return DeterministicCargoBackend(config)
    return CoppeliaMuJoCoBackend(
        config,
        log_path=output_dir / "coppeliasim.log",
    )


def _series_record(
    spec: RunSpec,
    decision: GuardDecision,
    observation: Observation,
    command: object,
    step: int,
    nan_detected: bool,
) -> dict[str, object]:
    reference = np.asarray(command.reference_wrench_body)
    allocated = np.asarray(command.allocated_wrench_body)
    record = {
        "run_id": spec.run_id,
        "phase": spec.phase,
        "world_hash": spec.world.world_hash,
        "guard": spec.guard,
        "guard_accepted": decision.accepted,
        "dt_s": spec.dt_s,
        "step": step,
        "time_s": observation.time_s,
        "payload_x_m": observation.payload_pose_m_rad[0],
        "payload_y_m": observation.payload_pose_m_rad[1],
        "payload_yaw_rad": observation.payload_pose_m_rad[2],
        "payload_vx_m_s": observation.payload_twist_m_s_rad_s[0],
        "payload_vy_m_s": observation.payload_twist_m_s_rad_s[1],
        "payload_omega_rad_s": observation.payload_twist_m_s_rad_s[2],
        "measured_fx_n": observation.measured_wrench_body[0],
        "measured_fy_n": observation.measured_wrench_body[1],
        "measured_tau_n_m": observation.measured_wrench_body[2],
        "reference_fx_n": reference[0],
        "reference_fy_n": reference[1],
        "reference_tau_n_m": reference[2],
        "allocated_fx_n": allocated[0],
        "allocated_fy_n": allocated[1],
        "allocated_tau_n_m": allocated[2],
        "allocation_residual_normalized": command.allocation_residual_normalized,
        "allocation_utilization": command.allocation_utilization,
        "allocation_saturation_count": command.allocation_saturation_count,
        "wheel_saturation_count": command.wheel_saturation_count,
        "contact_duty_step": float(np.mean(_active(observation.contact_active, observation))),
        "max_relative_slip_m": float(np.max(_active(observation.relative_slip_m, observation))),
        "collision_count": observation.collision_count,
        "wheel_speed_abs_max_rad_s": float(np.max(np.abs(observation.wheel_speed_rad_s))),
        "max_robot_drive_force_n": float(
            np.max(np.sum(np.abs(observation.wheel_drive_force_n), axis=1))
        ),
        "saturation_count": command.saturation_count,
        "nan_detected": nan_detected,
    }
    for index in range(4):
        robot = index + 1
        record[f"normal_force_r{robot}_n"] = observation.normal_force_n[index]
        record[f"contact_active_r{robot}"] = bool(observation.contact_active[index])
        record[f"wheel_speed_r{robot}_left_rad_s"] = observation.wheel_speed_rad_s[
            index, 0
        ]
        record[f"wheel_speed_r{robot}_right_rad_s"] = observation.wheel_speed_rad_s[
            index, 1
        ]
        record[f"wheel_drive_force_r{robot}_left_n"] = (
            observation.wheel_drive_force_n[index, 0]
        )
        record[f"wheel_drive_force_r{robot}_right_n"] = (
            observation.wheel_drive_force_n[index, 1]
        )
    return record


def _run_one(
    config: CampaignConfig,
    backend: CargoBackend,
    controller: CargoPoseController,
    spec: RunSpec,
    series_writer: csv.DictWriter,
) -> tuple[dict[str, object], dict[str, object] | None]:
    decision = evaluate_guard(config, spec.world, spec.guard)
    base: dict[str, object] = {
        "run_id": spec.run_id,
        "phase": spec.phase,
        "cell_id": spec.world.cell.cell_id,
        "cell_index": spec.world.cell.index,
        "seed_index": spec.world.seed_index,
        "seed": spec.world.seed,
        "world_hash": spec.world.world_hash,
        "coalition": spec.world.cell.coalition,
        "active_robot_count": spec.world.active_robot_count,
        "longitudinal_acceleration_m_s2": spec.world.cell.longitudinal_acceleration_m_s2,
        "guard": spec.guard,
        **decision.as_record(),
        "dt_s": spec.dt_s,
        "controller_id": config.control.controller_id,
        "backend_kind": backend.metadata.backend_kind,
        "evidence_class": backend.metadata.evidence_class,
    }
    try:
        observation = backend.reset(spec.world, spec.dt_s)
        calibration = backend.calibration
        calibration_raw = calibration.raw.get("calibration", {})
        ack_raw = calibration.raw.get("ack", {})
        ack_readback = ack_raw.get("readback", {})
        sensor_gate = calibration.sensor_static_relative_error <= config.gates.sensor_static_relative_error_max
        transmission_gate = calibration.force_transmission_relative_error <= config.gates.force_transmission_relative_error_max
        wheel_gate = calibration.wheel_twist_relative_error <= config.gates.wheel_twist_relative_error_max
        audit_gate = calibration.scene_no_pose_actuation_audited
        readback_gate = bool(
            calibration.configuration_acknowledged
            and calibration.readback_max_abs_error <= config.gates.config_readback_abs_tolerance
        )
        max_steps = int(math.ceil(config.control.horizon_s / spec.dt_s))
        contact_samples = 0.0
        sample_count = 0
        max_slip = 0.0
        saturation_count = 0
        allocation_saturation_count = 0
        wheel_saturation_count = 0
        wrench_residuals: list[float] = []
        allocation_residuals: list[float] = []
        allocation_utilizations: list[float] = []
        max_robot_drive_force_n = float(
            np.max(np.sum(np.abs(observation.wheel_drive_force_n), axis=1))
        )
        dwell = 0.0
        nan_detected = not _finite_observation(observation)
        command = controller.command(spec.world, observation, spec.dt_s)
        for step in range(max_steps):
            command = controller.command(spec.world, observation, spec.dt_s)
            saturation_count += command.saturation_count
            allocation_saturation_count += command.allocation_saturation_count
            wheel_saturation_count += command.wheel_saturation_count
            allocation_residuals.append(command.allocation_residual_normalized)
            allocation_utilizations.append(command.allocation_utilization)
            backend.apply(command)
            observation = backend.step()
            finite = _finite_observation(observation)
            nan_detected = nan_detected or not finite
            sample_count += 1
            contact_samples += float(
                np.mean(_active(observation.contact_active, observation))
            )
            if finite:
                max_robot_drive_force_n = max(
                    max_robot_drive_force_n,
                    float(
                        np.max(
                            np.sum(
                                np.abs(observation.wheel_drive_force_n), axis=1
                            )
                        )
                    ),
                )
                max_slip = max(
                    max_slip,
                    float(np.max(_active(observation.relative_slip_m, observation))),
                )
                wrench_residuals.append(
                    float(
                        np.linalg.norm(
                            observation.measured_wrench_body
                            - command.reference_wrench_body
                        )
                    )
                    / max(float(np.linalg.norm(command.reference_wrench_body)), 1.0)
                )
            position_error = float(np.linalg.norm(observation.payload_pose_m_rad[:2] - np.asarray(spec.world.target_pose_m_rad[:2])))
            yaw_error = abs(wrap_angle(float(observation.payload_pose_m_rad[2] - spec.world.target_pose_m_rad[2])))
            terminal_now = bool(
                finite
                and position_error <= config.gates.final_position_error_m
                and yaw_error <= config.gates.final_yaw_error_rad
                and np.linalg.norm(observation.payload_twist_m_s_rad_s[:2]) <= config.gates.final_linear_speed_m_s
                and abs(observation.payload_twist_m_s_rad_s[2]) <= config.gates.final_angular_speed_rad_s
            )
            dwell = dwell + spec.dt_s if terminal_now else 0.0
            if step % config.control.series_stride == 0 or step == max_steps - 1:
                series_writer.writerow(_series_record(spec, decision, observation, command, step, nan_detected))
            if nan_detected or dwell >= config.gates.dwell_time_s:
                break

        contact_duty = contact_samples / max(sample_count, 1)
        final_position = float(np.linalg.norm(observation.payload_pose_m_rad[:2] - np.asarray(spec.world.target_pose_m_rad[:2])))
        final_yaw = abs(wrap_angle(float(observation.payload_pose_m_rad[2] - spec.world.target_pose_m_rad[2])))
        final_linear = float(np.linalg.norm(observation.payload_twist_m_s_rad_s[:2]))
        final_angular = abs(float(observation.payload_twist_m_s_rad_s[2]))
        dwell_achieved = dwell >= config.gates.dwell_time_s
        contact_gate = contact_duty >= config.gates.contact_duty_min
        slip_gate = max_slip <= config.gates.max_relative_slip_m
        collision_gate = observation.collision_count <= config.gates.collision_count_max
        wheel_drive_force_gate = bool(
            max_robot_drive_force_n
            <= config.robot.max_drive_force_n
            + config.gates.config_readback_abs_tolerance
        )
        terminal_gate = bool(
            dwell_achieved
            and final_position <= config.gates.final_position_error_m
            and final_yaw <= config.gates.final_yaw_error_rad
            and final_linear <= config.gates.final_linear_speed_m_s
            and final_angular <= config.gates.final_angular_speed_rad_s
        )
        physical_success = bool(
            not nan_detected
            and sensor_gate
            and transmission_gate
            and wheel_gate
            and audit_gate
            and readback_gate
            and wheel_drive_force_gate
            and contact_gate
            and slip_gate
            and collision_gate
            and terminal_gate
        )
        row = {
            **base,
            "execution_status": "completed",
            "physical_success": physical_success,
            "classification": _classification(decision.accepted, physical_success),
            "steps": sample_count,
            "duration_s": observation.time_s,
            "contact_duty": contact_duty,
            "max_relative_slip_m": max_slip,
            "collision_count": observation.collision_count,
            "final_position_error_m": final_position,
            "final_yaw_error_rad": final_yaw,
            "final_linear_speed_m_s": final_linear,
            "final_angular_speed_rad_s": final_angular,
            "dwell_achieved": dwell_achieved,
            "nan_detected": nan_detected,
            "saturation_count": saturation_count,
            "wrench_model_residual_mean": float(np.mean(wrench_residuals)) if wrench_residuals else float("nan"),
            "allocation_residual_mean": (
                float(np.mean(allocation_residuals)) if allocation_residuals else float("nan")
            ),
            "allocation_residual_max": (
                float(np.max(allocation_residuals)) if allocation_residuals else float("nan")
            ),
            "allocation_utilization_max": (
                float(np.max(allocation_utilizations))
                if allocation_utilizations
                else float("nan")
            ),
            "allocation_saturation_count": allocation_saturation_count,
            "wheel_saturation_count": wheel_saturation_count,
            "max_robot_drive_force_n": max_robot_drive_force_n,
            "wheel_drive_force_gate_pass": wheel_drive_force_gate,
            "calibration_status": calibration_raw.get("status", "not_reported"),
            "sensor_static_relative_error": calibration.sensor_static_relative_error,
            "valid_force_sensor_count": calibration_raw.get("valid_force_sensors", ""),
            "dynamically_enabled_force_sensor_count": calibration_raw.get(
                "dynamically_enabled_force_sensors", ""
            ),
            "expected_static_force_n": calibration_raw.get("expected_force_n", ""),
            "measured_static_force_raw_n": calibration_raw.get(
                "measured_force_raw_n", ""
            ),
            "measured_static_force_n": calibration_raw.get("measured_force_n", ""),
            "sensor_vertical_tare_sum_n": sum(
                calibration_raw.get("sensor_vertical_tare_n", [])
            ),
            "force_transmission_relative_error": (
                calibration.force_transmission_relative_error
            ),
            "force_transmission_status": calibration_raw.get(
                "force_transmission_status", "not_reported"
            ),
            "wheel_twist_relative_error": calibration.wheel_twist_relative_error,
            "wheel_twist_status": calibration_raw.get(
                "wheel_twist_status", "not_reported"
            ),
            "config_readback_max_abs_error": calibration.readback_max_abs_error,
            "support_overlap_max_abs_error_m": ack_readback.get(
                "support_overlap_max_abs_error_m", ""
            ),
            "ack_reset_sequence": ack_raw.get("reset_sequence", ""),
            "ack_contract_hash": ack_raw.get("contract_hash", ""),
            "ack_run_start_simulation_time_s": ack_raw.get(
                "run_start_simulation_time_s", ""
            ),
            "ack_engine": ack_raw.get("engine", ""),
            "ack_actuation_contract": ack_raw.get("actuation_contract", ""),
            "sensor_gate_pass": sensor_gate,
            "force_transmission_gate_pass": transmission_gate,
            "wheel_twist_gate_pass": wheel_gate,
            "scene_actuation_audit_pass": audit_gate,
            "config_readback_gate_pass": readback_gate,
            "contact_gate_pass": contact_gate,
            "slip_gate_pass": slip_gate,
            "collision_gate_pass": collision_gate,
            "terminal_gate_pass": terminal_gate,
            "error_type": "",
            "error_message": "",
        }
        return row, None
    except Exception as exc:  # each failed trial remains an auditable observation
        row = {
            **base,
            **{field: "" for field in RUN_FIELDS if field not in base},
            "execution_status": "failed",
            "physical_success": False,
            "classification": _classification(decision.accepted, False),
            "nan_detected": isinstance(exc, FloatingPointError),
            "saturation_count": 0,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        failure = {
            "run_id": spec.run_id,
            "phase": spec.phase,
            "world_hash": spec.world.world_hash,
            "guard": spec.guard,
            "guard_accepted": decision.accepted,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
        return row, failure


def _summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["phase"]), str(row["guard"]))].append(row)
    result = []
    for (phase, guard), items in sorted(groups.items()):
        completed = [item for item in items if item["execution_status"] == "completed"]
        result.append(
            {
                "phase": phase,
                "guard": guard,
                "runs": len(items),
                "completed": len(completed),
                "failed": len(items) - len(completed),
                "accepted": sum(bool(item["guard_accepted"]) for item in items),
                "rejected": sum(not bool(item["guard_accepted"]) for item in items),
                "physical_successes": sum(bool(item["physical_success"]) for item in completed),
                "true_positive": sum(item["classification"] == "true_positive" for item in completed),
                "false_positive": sum(item["classification"] == "false_positive" for item in completed),
                "false_negative": sum(item["classification"] == "false_negative" for item in completed),
                "true_negative": sum(item["classification"] == "true_negative" for item in completed),
                "nan_runs": sum(bool(item["nan_detected"]) for item in items),
                "saturation_events": sum(int(item["saturation_count"] or 0) for item in items),
            }
        )
    return result


def _dt_sensitivity_status(
    config: CampaignConfig, rows: list[dict[str, object]]
) -> dict[str, object]:
    sensitivity = [row for row in rows if row["phase"] == "dt_sensitivity"]
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in sensitivity:
        groups[(str(row["world_hash"]), str(row["guard"]))].append(row)
    expected_groups = (
        len(config.design.sensitivity.cell_indices)
        * config.design.sensitivity.seeds_per_cell
        * len(config.guards)
    )
    expected_per_group = len(config.design.sensitivity.dt_values_s)
    complete = bool(
        len(groups) == expected_groups
        and all(
            len(items) == expected_per_group
            and all(item["execution_status"] == "completed" for item in items)
            for items in groups.values()
        )
    )
    position_spreads: list[float] = []
    yaw_spreads: list[float] = []
    disagreements = 0
    for items in groups.values():
        if not all(item["execution_status"] == "completed" for item in items):
            continue
        positions = np.asarray([float(item["final_position_error_m"]) for item in items])
        yaws = np.asarray([float(item["final_yaw_error_rad"]) for item in items])
        if not np.isfinite(positions).all() or not np.isfinite(yaws).all():
            position_spreads.append(float("inf"))
            yaw_spreads.append(float("inf"))
        else:
            position_spreads.append(float(np.ptp(positions)))
            yaw_spreads.append(float(np.ptp(yaws)))
        disagreements += int(len({bool(item["physical_success"]) for item in items}) > 1)
    max_position = max(position_spreads, default=float("inf"))
    max_yaw = max(yaw_spreads, default=float("inf"))
    has_multiple_dt = len(config.design.sensitivity.dt_values_s) >= 2
    passed = bool(
        complete
        and has_multiple_dt
        and math.isfinite(max_position)
        and math.isfinite(max_yaw)
        and max_position <= config.gates.dt_final_position_spread_max_m
        and max_yaw <= config.gates.dt_final_yaw_spread_max_rad
        and disagreements <= config.gates.dt_success_disagreement_max
    )
    return {
        "complete": complete,
        "groups_expected": expected_groups,
        "groups_recorded": len(groups),
        "dt_values_s": list(config.design.sensitivity.dt_values_s),
        "interpretation": (
            "declared_multi_dt_sensitivity"
            if has_multiple_dt
            else "single_dt_repeat_only_not_a_sensitivity_study"
        ),
        "max_final_position_spread_m": max_position if math.isfinite(max_position) else None,
        "max_final_yaw_spread_rad": max_yaw if math.isfinite(max_yaw) else None,
        "success_disagreement_groups": disagreements,
        "position_spread_limit_m": config.gates.dt_final_position_spread_max_m,
        "yaw_spread_limit_rad": config.gates.dt_final_yaw_spread_max_rad,
        "success_disagreement_limit": config.gates.dt_success_disagreement_max,
        "pass": passed,
    }


def _paired_execution_status(
    config: CampaignConfig, rows: list[dict[str, object]], expected_worlds: int
) -> dict[str, object]:
    primary = [row for row in rows if row["phase"] == "primary"]
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in primary:
        groups[str(row["world_hash"])].append(row)
    complete = bool(
        len(groups) == expected_worlds
        and all(
            len(items) == len(config.guards)
            and {str(item["guard"]) for item in items} == set(config.guards)
            and all(item["execution_status"] == "completed" for item in items)
            for items in groups.values()
        )
    )
    position_spreads: list[float] = []
    yaw_spreads: list[float] = []
    disagreements = 0
    for items in groups.values():
        if len(items) != len(config.guards) or not all(
            item["execution_status"] == "completed" for item in items
        ):
            continue
        positions = np.asarray([float(item["final_position_error_m"]) for item in items])
        yaws = np.asarray([float(item["final_yaw_error_rad"]) for item in items])
        if not np.isfinite(positions).all() or not np.isfinite(yaws).all():
            position_spreads.append(float("inf"))
            yaw_spreads.append(float("inf"))
        else:
            position_spreads.append(float(np.ptp(positions)))
            yaw_spreads.append(float(np.ptp(yaws)))
        disagreements += int(len({bool(item["physical_success"]) for item in items}) > 1)
    max_position = max(position_spreads, default=float("inf"))
    max_yaw = max(yaw_spreads, default=float("inf"))
    passed = bool(
        complete
        and math.isfinite(max_position)
        and math.isfinite(max_yaw)
        and max_position <= config.gates.paired_repeat_position_spread_max_m
        and max_yaw <= config.gates.paired_repeat_yaw_spread_max_rad
        and disagreements <= config.gates.paired_success_disagreement_max
    )
    return {
        "complete": complete,
        "worlds_expected": expected_worlds,
        "worlds_recorded": len(groups),
        "max_final_position_spread_m": max_position if math.isfinite(max_position) else None,
        "max_final_yaw_spread_rad": max_yaw if math.isfinite(max_yaw) else None,
        "success_disagreement_worlds": disagreements,
        "position_spread_limit_m": config.gates.paired_repeat_position_spread_max_m,
        "yaw_spread_limit_rad": config.gates.paired_repeat_yaw_spread_max_rad,
        "success_disagreement_limit": config.gates.paired_success_disagreement_max,
        "interpretation": "repeatability of the same controller and world across guard labels",
        "pass": passed,
    }


def run_campaign(
    config: CampaignConfig,
    *,
    output_dir: str | Path | None = None,
    authorize_confirmatory: bool = False,
    preflight_evidence: str | Path | None = None,
    backend_factory: Callable[[CampaignConfig], CargoBackend] | None = None,
    source_config: str | Path | None = None,
) -> CampaignResult:
    """Execute a campaign after any confirmatory preflight is fully attested."""

    preflight_attestation: PreflightAttestation | None = None
    if config.backend.kind == "coppeliasim_mujoco" and backend_factory is not None:
        raise PermissionError(
            "physical CoppeliaSim execution forbids backend_factory overrides"
        )
    if config.mode == "confirmatory":
        if authorize_confirmatory is not True:
            raise PermissionError("confirmatory execution requires --authorize-confirmatory")
        if preflight_evidence is None:
            raise PreflightEvidenceError(
                "confirmatory execution requires --preflight-evidence DIR"
            )
        # This read-only validation must remain before _prepare_output: rejected
        # authorization must not leave an apparently started campaign directory.
        preflight_attestation = validate_preflight_evidence(
            config, preflight_evidence
        )
    elif preflight_evidence is not None:
        raise PreflightEvidenceError(
            "preflight evidence can only authorize a confirmatory campaign"
        )
    target = Path(output_dir or config.output_dir).resolve()
    _prepare_output(target)
    protocol = target / "protocol"
    protocol.mkdir()
    snapshot = protocol / "config_snapshot.yaml"
    snapshot_payload = json.loads(json.dumps(asdict(config)))
    snapshot.write_text(yaml.safe_dump(snapshot_payload, sort_keys=False), encoding="utf-8")
    worlds = build_worlds(config)
    runs = build_run_specs(config)
    design_path = protocol / "design.csv"
    with design_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(worlds[0].as_record()))
        writer.writeheader()
        writer.writerows(world.as_record() for world in worlds)
    seed_path = protocol / "seed_registry.csv"
    with seed_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["seed_index", "seed"])
        writer.writeheader()
        writer.writerows(
            {"seed_index": index, "seed": seed}
            for index, seed in enumerate(config.design.seeds.values)
        )

    backend = backend_factory(config) if backend_factory else _default_backend(config, target)
    controller = CargoPoseController(config)
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    series_path = target / "series.csv.gz"
    try:
        backend.start()
        if config.backend.kind == "coppeliasim_mujoco":
            metadata = backend.metadata
            expected_backend_contract = {
                "backend_kind": "coppeliasim_mujoco",
                "evidence_class": "physical_coppeliasim_candidate",
                "engine": "mujoco",
                "synchronous_stepping": True,
                "actuator_contract": "wheel_velocity_only",
            }
            observed_backend_contract = {
                field: getattr(metadata, field) for field in expected_backend_contract
            }
            if observed_backend_contract != expected_backend_contract:
                raise RuntimeError(
                    "confirmatory execution requires synchronous MuJoCo with "
                    "wheel-velocity-only actuation"
                )
        with gzip.open(series_path, "wt", newline="", encoding="utf-8") as handle:
            series_writer = csv.DictWriter(handle, fieldnames=SERIES_FIELDS)
            series_writer.writeheader()
            for spec in runs:
                row, failure = _run_one(config, backend, controller, spec, series_writer)
                rows.append(row)
                if failure is not None:
                    failures.append(failure)
    finally:
        backend.close()

    runs_path = target / "runs.csv"
    with runs_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    failure_path = target / "failures.csv"
    with failure_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["run_id", "phase", "world_hash", "guard", "guard_accepted", "error_type", "error_message"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(failures)
    summaries = _summaries(rows)
    summary_path = target / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    primary = [row for row in rows if row["phase"] == "primary"]
    expected_primary = len(worlds) * len(config.guards)
    physical_backend = _is_physical_coppelia_backend(backend)

    def primary_numeric(field: str) -> list[float]:
        values: list[float] = []
        for row in primary:
            try:
                value = float(row[field])
            except (KeyError, TypeError, ValueError):
                continue
            if math.isfinite(value):
                values.append(value)
        return values

    def measured_max(field: str) -> float | None:
        values = primary_numeric(field)
        return max(values) if values else None

    def measured_min(field: str) -> float | None:
        values = primary_numeric(field)
        return min(values) if values else None

    dt_status = _dt_sensitivity_status(config, rows)
    paired_status = _paired_execution_status(config, rows, len(worlds))
    inference_contract = write_inference(
        config,
        rows,
        target,
        backend_kind=backend.metadata.backend_kind,
        evidence_class=backend.metadata.evidence_class,
    )
    ack_sequences = [
        int(value) for value in primary_numeric("ack_reset_sequence")
    ]
    all_ack_sequences = []
    for row in rows:
        try:
            all_ack_sequences.append(int(row["ack_reset_sequence"]))
        except (KeyError, TypeError, ValueError):
            continue
    fresh_ack_reset_sequences = (
        bool(all_ack_sequences)
        and len(all_ack_sequences) == len(rows)
        and len(set(all_ack_sequences)) == len(all_ack_sequences)
        and all_ack_sequences == sorted(all_ack_sequences)
    )
    physical_scene_gates = {
        gate: bool(primary)
        and all(
            row["execution_status"] == "completed" and bool(row[gate])
            for row in primary
        )
        for gate in CALIBRATION_GATE_FIELDS
    }
    physical_trial_gates = {
        gate: bool(primary)
        and all(
            row["execution_status"] == "completed" and bool(row[gate])
            for row in primary
        )
        for gate in OPERATIONAL_GATE_FIELDS
    }
    all_runs_physical_success = _all_physical_runs_pass(rows)
    preflight_approved = bool(
        config.mode == "smoke"
        and physical_backend
        and len(primary) == expected_primary
        and not failures
        and fresh_ack_reset_sequences
        and dt_status["pass"]
        and paired_status["pass"]
        and inference_contract["complete"]
        and all(physical_scene_gates.values())
        and all(physical_trial_gates.values())
        and all_runs_physical_success
    )
    gate_status = {
        "design": {
            "factorial_cells": config.design.cell_count,
            "perturbations_per_cell": config.design.seeds.count,
            "primary_runs_expected": expected_primary,
            "primary_runs_recorded": len(primary),
            "paired_world_hashes_across_guards": all(
                len({item["world_hash"] for item in primary if item["cell_id"] == world.cell.cell_id and item["seed"] == world.seed}) == 1
                for world in worlds
            ),
            "dt_sensitivity_values_s": list(config.design.sensitivity.dt_values_s),
        },
        "execution": {
            "all_primary_recorded": len(primary) == expected_primary,
            "failed_runs": len(failures),
            "nan_runs": sum(bool(row["nan_detected"]) for row in rows),
            "saturation_events": sum(int(row["saturation_count"] or 0) for row in rows),
            "fresh_ack_reset_sequences": fresh_ack_reset_sequences,
        },
        "physical_scene": physical_scene_gates,
        "physical_trials": physical_trial_gates,
        "physical_scene_measurements": {
            "sensor_static_relative_error_max": measured_max(
                "sensor_static_relative_error"
            ),
            "valid_force_sensor_count_min": measured_min(
                "valid_force_sensor_count"
            ),
            "dynamically_enabled_force_sensor_count_min": measured_min(
                "dynamically_enabled_force_sensor_count"
            ),
            "expected_static_force_n_range": [
                measured_min("expected_static_force_n"),
                measured_max("expected_static_force_n"),
            ],
            "measured_static_force_n_range": [
                measured_min("measured_static_force_n"),
                measured_max("measured_static_force_n"),
            ],
            "config_readback_max_abs_error": measured_max(
                "config_readback_max_abs_error"
            ),
            "support_overlap_max_abs_error_m": measured_max(
                "support_overlap_max_abs_error_m"
            ),
            "max_robot_drive_force_n": measured_max("max_robot_drive_force_n"),
            "primary_ack_reset_sequences": ack_sequences,
            "all_ack_reset_sequences": all_ack_sequences,
            "unique_ack_contract_hashes": len(
                {
                    str(row["ack_contract_hash"])
                    for row in rows
                    if row.get("ack_contract_hash")
                }
            ),
            "force_transmission_status": sorted(
                {
                    str(row["force_transmission_status"])
                    for row in primary
                    if row.get("force_transmission_status")
                }
            ),
            "wheel_twist_status": sorted(
                {
                    str(row["wheel_twist_status"])
                    for row in primary
                    if row.get("wheel_twist_status")
                }
            ),
            "pending_calibration_sentinels_are_not_measurements": True,
        },
        "dt_sensitivity": dt_status,
        "paired_execution_repeatability": paired_status,
        "inference": inference_contract,
        "preflight": {
            "applicable": bool(config.mode == "smoke" and physical_backend),
            "approved": preflight_approved,
            "all_runs_physical_success": all_runs_physical_success,
            "required_gate_fields": list(PHYSICAL_GATE_FIELDS),
        },
        "evidence": {
            "backend_kind": backend.metadata.backend_kind,
            "evidence_class": backend.metadata.evidence_class,
            "synthetic_outputs_must_not_be_cited_as_coppeliasim": not physical_backend,
            "confirmatory_claim_eligible": bool(
                config.mode == "confirmatory"
                and preflight_attestation is not None
                and physical_backend
                and len(primary) == expected_primary
                and not failures
                and dt_status["pass"]
                and paired_status["pass"]
                and inference_contract["complete"]
                and _all_physical_runs_pass(rows)
            ),
        },
    }
    gate_path = target / "gate_status.json"
    _json_dump(gate_path, gate_status)

    source_hash = _file_hash(Path(source_config)) if source_config else None
    artifacts = sorted(path for path in target.rglob("*") if path.is_file())
    implementation_files = sorted(Path(__file__).resolve().parent.glob("*.py"))
    scene_path = Path(str(config.backend.scene_path)).resolve() if config.backend.scene_path else None
    scene_audit_path = scene_path.with_suffix(".audit.json") if scene_path else None
    manifest = {
        "experiment_id": config.experiment_id,
        "protocol_family": config.protocol_family,
        "mode": config.mode,
        "status": "complete" if not failures else "complete_with_failed_trials",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_sha256": config.canonical_hash,
        "source_config_sha256": source_hash,
        "design_sha256": design_hash(runs),
        "seed_registry": list(config.design.seeds.values),
        "controller_id": config.control.controller_id,
        "controller_scope": (
            "pose PD -> bounded contact-force setpoints -> wrench-error admittance -> "
            "wheel velocities; setpoints are indirectly realized and exact wrench "
            "realization is not assumed"
        ),
        "backend": asdict(backend.metadata),
        "run_counts": {
            "total": len(rows),
            "completed": sum(row["execution_status"] == "completed" for row in rows),
            "failed": len(failures),
            "accepted": sum(bool(row["guard_accepted"]) for row in rows),
            "rejected": sum(not bool(row["guard_accepted"]) for row in rows),
        },
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "git_commit": _git_sha(),
            "git_dirty": _git_dirty(),
        },
        "implementation_sha256": {
            path.name: _file_hash(path) for path in implementation_files
        },
        "scene_sha256": _file_hash(scene_path) if scene_path and scene_path.is_file() else None,
        "scene_audit_sha256": (
            _file_hash(scene_audit_path)
            if scene_audit_path and scene_audit_path.is_file()
            else None
        ),
        "confirmatory_preflight": (
            preflight_attestation.as_record()
            if preflight_attestation is not None
            else None
        ),
        "artifact_sha256": {str(path.relative_to(target)): _file_hash(path) for path in artifacts},
        "scientific_use": (
            "physical_candidate_subject_to_gate_status"
            if physical_backend
            else "synthetic_contract_test_only; not CoppeliaSim evidence"
        ),
    }
    manifest_path = target / "manifest.json"
    _json_dump(manifest_path, manifest)
    return CampaignResult(
        output_dir=target,
        run_count=len(rows),
        completed_count=sum(row["execution_status"] == "completed" for row in rows),
        failed_count=len(failures),
        manifest_path=manifest_path,
    )


def run_campaign_file(
    path: str | Path,
    *,
    output_dir: str | Path | None = None,
    authorize_confirmatory: bool = False,
    preflight_evidence: str | Path | None = None,
) -> CampaignResult:
    config = load_config(path)
    return run_campaign(
        config,
        output_dir=output_dir,
        authorize_confirmatory=authorize_confirmatory,
        preflight_evidence=preflight_evidence,
        source_config=path,
    )


__all__ = ["CampaignResult", "run_campaign", "run_campaign_file"]
