"""Hash-bound authorization of physical Cargo preflight evidence.

The preflight directory is a scientific attestation, not a convenience flag.
A confirmatory campaign may consume it only when its immutable artifacts,
physical gates, scene, controller contract, and implementation snapshot match
the confirmatory runner that is about to execute.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from .config import CampaignConfig, SeedConfig
from .coppelia_backend import (
    build_world_contract,
    validate_independent_scene_audit,
)
from .design import RunSpec, build_run_specs, build_worlds, design_hash


CALIBRATION_GATE_FIELDS = (
    "sensor_gate_pass",
    "force_transmission_gate_pass",
    "wheel_twist_gate_pass",
    "scene_actuation_audit_pass",
    "config_readback_gate_pass",
    "wheel_drive_force_gate_pass",
)

OPERATIONAL_GATE_FIELDS = (
    "contact_gate_pass",
    "slip_gate_pass",
    "collision_gate_pass",
    "terminal_gate_pass",
)

PHYSICAL_GATE_FIELDS = CALIBRATION_GATE_FIELDS + OPERATIONAL_GATE_FIELDS

REQUIRED_PREFLIGHT_ARTIFACTS = frozenset(
    {
        "coppeliasim.log",
        "failures.csv",
        "gate_status.json",
        "inference/analysis_contract.json",
        "inference/cell_guard_rates.csv",
        "inference/paired_guard_contrasts.csv",
        "protocol/config_snapshot.yaml",
        "protocol/design.csv",
        "protocol/seed_registry.csv",
        "runs.csv",
        "series.csv.gz",
        "summary.csv",
    }
)


class PreflightEvidenceError(ValueError):
    """Raised before output creation when preflight evidence is not admissible."""


@dataclass(frozen=True, slots=True)
class PreflightAttestation:
    """Portable identifiers persisted in the later confirmatory manifest."""

    evidence_dir: Path
    experiment_id: str
    manifest_sha256: str
    gate_status_sha256: str
    configuration_sha256: str
    design_sha256: str
    scene_sha256: str
    scene_audit_sha256: str
    implementation_set_sha256: str

    def as_record(self) -> dict[str, str]:
        # Deliberately omit the host-specific absolute evidence directory.
        return {
            "experiment_id": self.experiment_id,
            "manifest_sha256": self.manifest_sha256,
            "gate_status_sha256": self.gate_status_sha256,
            "configuration_sha256": self.configuration_sha256,
            "design_sha256": self.design_sha256,
            "scene_sha256": self.scene_sha256,
            "scene_audit_sha256": self.scene_audit_sha256,
            "implementation_set_sha256": self.implementation_set_sha256,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def current_implementation_hashes() -> dict[str, str]:
    """Hash every live Python module that defines the Cargo campaign."""

    package = Path(__file__).resolve().parent
    return {
        path.name: _sha256_file(path)
        for path in sorted(package.glob("*.py"), key=lambda item: item.name)
    }


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PreflightEvidenceError(f"{label} must be a JSON/YAML object")
    return {str(key): item for key, item in value.items()}


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightEvidenceError(f"cannot read valid {label}: {path}: {exc}") from exc
    return _mapping(value, label)


def _normalized_artifact_path(root: Path, name: str) -> tuple[str, Path]:
    normalized = name.replace("\\", "/")
    relative = PurePosixPath(normalized)
    if (
        not normalized
        or relative.is_absolute()
        or ".." in relative.parts
        or any(":" in part for part in relative.parts)
    ):
        raise PreflightEvidenceError(f"unsafe artifact path in preflight manifest: {name!r}")
    candidate = root.joinpath(*relative.parts).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PreflightEvidenceError(
            f"preflight artifact escapes its evidence directory: {name!r}"
        ) from exc
    return relative.as_posix(), candidate


def _strict_bool(value: object, label: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise PreflightEvidenceError(f"{label} must be an explicit boolean")


def _require_true(value: object, label: str) -> None:
    if not _strict_bool(value, label):
        raise PreflightEvidenceError(f"preflight gate is not approved: {label}")


def _require_equal(observed: object, expected: object, label: str) -> None:
    if _canonical_sha256(observed) != _canonical_sha256(expected):
        raise PreflightEvidenceError(f"preflight {label} does not match confirmatory configuration")


def _snapshot_contract_is_compatible(
    snapshot: dict[str, Any], config: CampaignConfig
) -> None:
    if snapshot.get("mode") != "smoke":
        raise PreflightEvidenceError("preflight configuration snapshot must use mode=smoke")
    if snapshot.get("protocol_family") != config.protocol_family:
        raise PreflightEvidenceError("preflight protocol_family does not match confirmatory protocol")
    guards = snapshot.get("guards")
    if not isinstance(guards, list):
        raise PreflightEvidenceError("preflight configuration guards must be a list")
    _require_equal(guards, list(config.guards), "three-guard protocol")

    backend = _mapping(snapshot.get("backend"), "preflight configuration backend")
    current_backend = asdict(config.backend)
    backend_contract = {
        key: backend.get(key)
        for key in ("kind", "scene_path", "payload_alias", "robots")
    }
    current_backend_contract = {
        key: current_backend[key]
        for key in ("kind", "scene_path", "payload_alias", "robots")
    }
    _require_equal(backend_contract, current_backend_contract, "backend/alias contract")

    control = _mapping(snapshot.get("control"), "preflight configuration control")
    current_control = asdict(config.control)
    controller_fields = tuple(
        key for key in current_control if key not in {"horizon_s", "series_stride"}
    )
    _require_equal(
        {key: control.get(key) for key in controller_fields},
        {key: current_control[key] for key in controller_fields},
        "controller law",
    )

    gates = _mapping(snapshot.get("gates"), "preflight configuration gates")
    _require_equal(gates, asdict(config.gates), "physical gate thresholds")
    robot = _mapping(snapshot.get("robot"), "preflight configuration robot")
    _require_equal(robot, asdict(config.robot), "robot parameters")

    payload = _mapping(snapshot.get("payload"), "preflight configuration payload")
    current_payload = asdict(config.payload)
    physical_payload_fields = (
        "length_m",
        "width_m",
        "height_m",
        "linear_damping_n_s_m",
        "yaw_damping_n_m_s_rad",
    )
    _require_equal(
        {key: payload.get(key) for key in physical_payload_fields},
        {key: current_payload[key] for key in physical_payload_fields},
        "payload physical parameters",
    )

    design = _mapping(snapshot.get("design"), "preflight configuration design")
    current_design = asdict(config.design)
    design_contract_fields = (
        "payload_mass_kg",
        "friction_regime",
        "friction_coefficients",
        "coalition",
        "longitudinal_acceleration_m_s2",
        "coalitions_m",
        "motion_envelope",
        "perturbations",
        "primary_dt_s",
    )
    _require_equal(
        {key: design.get(key) for key in design_contract_fields},
        {key: current_design[key] for key in design_contract_fields},
        "factorial/mechanical design contract",
    )
    sensitivity = _mapping(
        design.get("sensitivity"), "preflight configuration sensitivity"
    )
    current_sensitivity = _mapping(
        current_design["sensitivity"], "confirmatory configuration sensitivity"
    )
    _require_equal(
        {
            key: sensitivity.get(key)
            for key in ("dt_values_s", "cell_indices")
        },
        {
            key: current_sensitivity[key]
            for key in ("dt_values_s", "cell_indices")
        },
        "dt sensitivity domain",
    )
    preflight_sensitivity_seeds = int(sensitivity.get("seeds_per_cell", 0))
    confirmatory_sensitivity_seeds = int(current_sensitivity["seeds_per_cell"])
    if not 0 < preflight_sensitivity_seeds <= confirmatory_sensitivity_seeds:
        raise PreflightEvidenceError(
            "preflight dt sensitivity seed count exceeds or misses the confirmatory domain"
        )


def _snapshot_campaign_config(
    snapshot: dict[str, Any], config: CampaignConfig
) -> CampaignConfig:
    """Reconstruct the admissible smoke design from a validated snapshot."""

    design = _mapping(snapshot.get("design"), "preflight configuration design")
    seeds = _mapping(design.get("seeds"), "preflight configuration seeds")
    sensitivity = _mapping(
        design.get("sensitivity"), "preflight configuration sensitivity"
    )
    control = _mapping(snapshot.get("control"), "preflight configuration control")
    payload = _mapping(snapshot.get("payload"), "preflight configuration payload")
    try:
        preflight_design = replace(
            config.design,
            seeds=SeedConfig(start=int(seeds["start"]), count=int(seeds["count"])),
            sensitivity=replace(
                config.design.sensitivity,
                seeds_per_cell=int(sensitivity["seeds_per_cell"]),
            ),
        )
        preflight_control = replace(
            config.control,
            horizon_s=float(control["horizon_s"]),
            series_stride=int(control["series_stride"]),
        )
        initial_pose = tuple(float(value) for value in payload["initial_pose_m_rad"])
        target_pose = tuple(float(value) for value in payload["target_pose_m_rad"])
        if len(initial_pose) != 3 or len(target_pose) != 3:
            raise ValueError("payload poses must have three entries")
        preflight_payload = replace(
            config.payload,
            initial_pose_m_rad=initial_pose,
            target_pose_m_rad=target_pose,
        )
        return replace(
            config,
            experiment_id=str(snapshot["experiment_id"]),
            mode="smoke",
            output_dir=str(snapshot["output_dir"]),
            design=preflight_design,
            control=preflight_control,
            payload=preflight_payload,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PreflightEvidenceError(
            f"cannot reconstruct the preflight design from its snapshot: {exc}"
        ) from exc


def _expected_counts(snapshot: dict[str, Any]) -> tuple[int, int, int, int]:
    design = _mapping(snapshot.get("design"), "preflight configuration design")
    seeds = _mapping(design.get("seeds"), "preflight configuration seeds")
    sensitivity = _mapping(
        design.get("sensitivity"), "preflight configuration sensitivity"
    )
    guards = snapshot.get("guards")
    if not isinstance(guards, list) or not guards:
        raise PreflightEvidenceError("preflight configuration guards must be a non-empty list")
    factor_names = (
        "payload_mass_kg",
        "friction_regime",
        "coalition",
        "longitudinal_acceleration_m_s2",
    )
    lengths: list[int] = []
    for name in factor_names:
        values = design.get(name)
        if not isinstance(values, list) or not values:
            raise PreflightEvidenceError(f"preflight design.{name} must be a non-empty list")
        lengths.append(len(values))
    cells = math.prod(lengths)
    seed_count = int(seeds.get("count", 0))
    if seed_count <= 0:
        raise PreflightEvidenceError("preflight seed count must be positive")
    primary = cells * seed_count * len(guards)
    dt_values = sensitivity.get("dt_values_s")
    cell_indices = sensitivity.get("cell_indices")
    seeds_per_cell = int(sensitivity.get("seeds_per_cell", 0))
    if not isinstance(dt_values, list) or not isinstance(cell_indices, list):
        raise PreflightEvidenceError("preflight sensitivity lists are missing")
    dt_runs = len(cell_indices) * seeds_per_cell * len(guards) * len(dt_values)
    return cells, seed_count, primary, dt_runs


def _validate_gate_status(
    gate_status: dict[str, Any],
    *,
    cells: int,
    seed_count: int,
    primary_expected: int,
    dt_values_s: object,
) -> None:
    preflight = _mapping(gate_status.get("preflight"), "gate_status.preflight")
    _require_true(preflight.get("approved"), "preflight.approved")
    _require_true(
        preflight.get("all_runs_physical_success"),
        "preflight.all_runs_physical_success",
    )
    _require_equal(
        preflight.get("required_gate_fields"),
        list(PHYSICAL_GATE_FIELDS),
        "declared physical gate fields",
    )

    design = _mapping(gate_status.get("design"), "gate_status.design")
    if int(design.get("factorial_cells", -1)) != cells:
        raise PreflightEvidenceError("preflight gate_status has the wrong factorial cell count")
    if int(design.get("perturbations_per_cell", -1)) != seed_count:
        raise PreflightEvidenceError("preflight gate_status has the wrong seed count")
    if int(design.get("primary_runs_expected", -1)) != primary_expected:
        raise PreflightEvidenceError("preflight gate_status has the wrong primary run count")
    if int(design.get("primary_runs_recorded", -1)) != primary_expected:
        raise PreflightEvidenceError("preflight did not record every primary run")
    _require_true(
        design.get("paired_world_hashes_across_guards"),
        "design.paired_world_hashes_across_guards",
    )
    _require_equal(
        design.get("dt_sensitivity_values_s"),
        dt_values_s,
        "reported dt sensitivity values",
    )

    execution = _mapping(gate_status.get("execution"), "gate_status.execution")
    _require_true(execution.get("all_primary_recorded"), "execution.all_primary_recorded")
    _require_true(
        execution.get("fresh_ack_reset_sequences"),
        "execution.fresh_ack_reset_sequences",
    )
    if int(execution.get("failed_runs", -1)) != 0:
        raise PreflightEvidenceError("preflight contains failed runs")
    if int(execution.get("nan_runs", -1)) != 0:
        raise PreflightEvidenceError("preflight contains NaN/Inf runs")

    scene = _mapping(gate_status.get("physical_scene"), "gate_status.physical_scene")
    for field in CALIBRATION_GATE_FIELDS:
        _require_true(scene.get(field), f"physical_scene.{field}")
    trials = _mapping(gate_status.get("physical_trials"), "gate_status.physical_trials")
    for field in OPERATIONAL_GATE_FIELDS:
        _require_true(trials.get(field), f"physical_trials.{field}")

    sensitivity = _mapping(
        gate_status.get("dt_sensitivity"), "gate_status.dt_sensitivity"
    )
    _require_true(sensitivity.get("complete"), "dt_sensitivity.complete")
    _require_true(sensitivity.get("pass"), "dt_sensitivity.pass")
    repeatability = _mapping(
        gate_status.get("paired_execution_repeatability"),
        "gate_status.paired_execution_repeatability",
    )
    _require_true(repeatability.get("complete"), "paired_execution_repeatability.complete")
    _require_true(repeatability.get("pass"), "paired_execution_repeatability.pass")


def _read_runs(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        raise PreflightEvidenceError(f"cannot read preflight runs.csv: {exc}") from exc


def _typed_csv_records(
    path: Path, expected: list[dict[str, object]], label: str
) -> list[dict[str, object]]:
    """Parse campaign CSV values according to the generator's expected schema."""

    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise PreflightEvidenceError(f"cannot read preflight {label}: {exc}") from exc
    if not expected:
        raise PreflightEvidenceError(f"internal expected schema for {label} is empty")
    expected_keys = list(expected[0])
    if not rows or list(rows[0]) != expected_keys:
        raise PreflightEvidenceError(f"preflight {label} has the wrong columns or is empty")
    typed: list[dict[str, object]] = []
    try:
        for row in rows:
            record: dict[str, object] = {}
            for name, exemplar in expected[0].items():
                raw = row[name]
                if isinstance(exemplar, bool):
                    record[name] = _strict_bool(raw, f"{label}.{name}")
                elif isinstance(exemplar, int):
                    record[name] = int(raw)
                elif isinstance(exemplar, float):
                    value = float(raw)
                    if not math.isfinite(value):
                        raise ValueError(f"non-finite {name}")
                    record[name] = value
                else:
                    record[name] = raw
            typed.append(record)
    except (KeyError, TypeError, ValueError) as exc:
        raise PreflightEvidenceError(f"preflight {label} contains invalid data: {exc}") from exc
    return typed


def _validate_design_artifacts(
    artifacts: dict[str, tuple[Path, str]],
    manifest: dict[str, Any],
    preflight_config: CampaignConfig,
    expected_runs: tuple[RunSpec, ...],
) -> None:
    expected_design = [world.as_record() for world in build_worlds(preflight_config)]
    observed_design = _typed_csv_records(
        artifacts["protocol/design.csv"][0],
        expected_design,
        "protocol/design.csv",
    )
    _require_equal(observed_design, expected_design, "protocol design.csv")

    expected_seeds = [
        {"seed_index": index, "seed": seed}
        for index, seed in enumerate(preflight_config.design.seeds.values)
    ]
    observed_seeds = _typed_csv_records(
        artifacts["protocol/seed_registry.csv"][0],
        expected_seeds,
        "protocol/seed_registry.csv",
    )
    _require_equal(observed_seeds, expected_seeds, "seed registry")

    expected_design_hash = design_hash(expected_runs)
    if manifest.get("design_sha256") != expected_design_hash:
        raise PreflightEvidenceError(
            "preflight design_sha256 does not match the reconstructed run design"
        )


def _validate_runs(
    rows: list[dict[str, str]],
    manifest: dict[str, Any],
    *,
    expected_runs: tuple[RunSpec, ...],
    preflight_config: CampaignConfig,
    controller_id: str,
) -> None:
    primary_expected = sum(run.phase == "primary" for run in expected_runs)
    dt_expected = sum(run.phase == "dt_sensitivity" for run in expected_runs)
    expected_total = primary_expected + dt_expected
    if len(rows) != expected_total:
        raise PreflightEvidenceError(
            f"preflight runs.csv has {len(rows)} rows; expected {expected_total}"
        )
    if len({row.get("run_id") for row in rows}) != len(rows):
        raise PreflightEvidenceError("preflight run_id values are not unique")
    primary = [row for row in rows if row.get("phase") == "primary"]
    sensitivity = [row for row in rows if row.get("phase") == "dt_sensitivity"]
    if len(primary) != primary_expected or len(sensitivity) != dt_expected:
        raise PreflightEvidenceError("preflight primary/dt phase counts do not match its snapshot")
    ack_sequences: list[int] = []
    for index, (row, expected) in enumerate(zip(rows, expected_runs, strict=True)):
        prefix = f"runs.csv row {index + 2}"
        expected_identity = {
            "run_id": expected.run_id,
            "phase": expected.phase,
            "guard": expected.guard,
            "world_hash": expected.world.world_hash,
            "cell_id": expected.world.cell.cell_id,
            "cell_index": str(expected.world.cell.index),
            "seed_index": str(expected.world.seed_index),
            "seed": str(expected.world.seed),
            "coalition": expected.world.cell.coalition,
            "active_robot_count": str(expected.world.active_robot_count),
        }
        for field, expected_value in expected_identity.items():
            if row.get(field) != expected_value:
                raise PreflightEvidenceError(
                    f"{prefix} does not match the reconstructed design field {field}"
                )
        try:
            observed_dt = float(row["dt_s"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PreflightEvidenceError(f"{prefix} has an invalid dt_s") from exc
        if observed_dt != expected.dt_s:
            raise PreflightEvidenceError(
                f"{prefix} does not match the reconstructed design field dt_s"
            )
        if row.get("execution_status") != "completed":
            raise PreflightEvidenceError(f"{prefix} did not complete")
        if row.get("backend_kind") != "coppeliasim_mujoco":
            raise PreflightEvidenceError(f"{prefix} is not CoppeliaSim/MuJoCo evidence")
        if row.get("controller_id") != controller_id:
            raise PreflightEvidenceError(f"{prefix} uses a different controller")
        if row.get("ack_engine") != "mujoco":
            raise PreflightEvidenceError(f"{prefix} did not acknowledge MuJoCo")
        if row.get("ack_actuation_contract") != "wheel_velocity_only":
            raise PreflightEvidenceError(
                f"{prefix} did not acknowledge wheel-only actuation"
            )
        expected_contract = build_world_contract(
            preflight_config,
            expected.world,
            expected.dt_s,
            index + 1,
        )
        if row.get("ack_contract_hash") != expected_contract["contract_hash"]:
            raise PreflightEvidenceError(
                f"{prefix} acknowledgement hash does not match its SI world contract"
            )
        try:
            ack_sequences.append(int(row["ack_reset_sequence"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise PreflightEvidenceError(
                f"{prefix} has an invalid acknowledgement reset sequence"
            ) from exc
        _require_true(row.get("physical_success"), f"{prefix}.physical_success")
        if _strict_bool(row.get("nan_detected"), f"{prefix}.nan_detected"):
            raise PreflightEvidenceError(f"{prefix} contains NaN/Inf")
        for field in PHYSICAL_GATE_FIELDS:
            _require_true(row.get(field), f"{prefix}.{field}")

    if ack_sequences != list(range(1, expected_total + 1)):
        raise PreflightEvidenceError(
            "preflight acknowledgement reset sequences are not fresh and contiguous"
        )

    counts = _mapping(manifest.get("run_counts"), "preflight manifest.run_counts")
    if (
        int(counts.get("total", -1)) != expected_total
        or int(counts.get("completed", -1)) != expected_total
        or int(counts.get("failed", -1)) != 0
    ):
        raise PreflightEvidenceError("preflight manifest run counts do not match runs.csv")


def validate_preflight_evidence(
    config: CampaignConfig, evidence_dir: str | Path
) -> PreflightAttestation:
    """Validate an approved physical preflight for a confirmatory campaign.

    This function is read-only. It raises before the caller creates a campaign
    output directory whenever any artifact, gate, or compatibility check fails.
    """

    if config.mode != "confirmatory":
        raise PreflightEvidenceError(
            "preflight authorization is only defined for mode=confirmatory"
        )
    root = Path(evidence_dir).resolve()
    if not root.is_dir():
        raise PreflightEvidenceError(f"preflight evidence directory does not exist: {root}")
    manifest_path = root / "manifest.json"
    gate_path = root / "gate_status.json"
    manifest = _read_json(manifest_path, "preflight manifest.json")
    gate_status = _read_json(gate_path, "preflight gate_status.json")

    artifacts_raw = _mapping(
        manifest.get("artifact_sha256"), "preflight manifest.artifact_sha256"
    )
    artifacts: dict[str, tuple[Path, str]] = {}
    for raw_name, raw_hash in artifacts_raw.items():
        normalized, path = _normalized_artifact_path(root, raw_name)
        expected_hash = str(raw_hash).lower()
        if normalized in artifacts:
            raise PreflightEvidenceError(
                f"duplicate normalized artifact path in preflight manifest: {normalized}"
            )
        if not _is_sha256(expected_hash):
            raise PreflightEvidenceError(
                f"invalid SHA-256 for preflight artifact: {raw_name}"
            )
        artifacts[normalized] = (path, expected_hash)

    missing = sorted(REQUIRED_PREFLIGHT_ARTIFACTS - set(artifacts))
    if missing:
        raise PreflightEvidenceError(
            "preflight manifest omits required artifacts: " + ", ".join(missing)
        )
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_files != set(artifacts):
        missing_from_manifest = sorted(actual_files - set(artifacts))
        missing_on_disk = sorted(set(artifacts) - actual_files)
        raise PreflightEvidenceError(
            "preflight artifact inventory mismatch; "
            f"unmanifested={missing_from_manifest}, missing={missing_on_disk}"
        )
    for name, (path, expected_hash) in artifacts.items():
        if _sha256_file(path) != expected_hash:
            raise PreflightEvidenceError(f"preflight artifact SHA-256 mismatch: {name}")

    gate_hash = _sha256_file(gate_path)
    if gate_hash != artifacts["gate_status.json"][1]:
        raise PreflightEvidenceError("preflight gate_status.json is not hash-bound")

    if manifest.get("mode") != "smoke" or manifest.get("status") != "complete":
        raise PreflightEvidenceError("preflight manifest must be a complete smoke campaign")
    if manifest.get("protocol_family") != config.protocol_family:
        raise PreflightEvidenceError("preflight manifest protocol does not match confirmatory protocol")
    if manifest.get("controller_id") != config.control.controller_id:
        raise PreflightEvidenceError("preflight manifest controller does not match confirmatory controller")
    if manifest.get("scientific_use") != "physical_candidate_subject_to_gate_status":
        raise PreflightEvidenceError("preflight manifest is not physical candidate evidence")
    backend = _mapping(manifest.get("backend"), "preflight manifest.backend")
    expected_backend = {
        "backend_kind": "coppeliasim_mujoco",
        "engine": "mujoco",
        "synchronous_stepping": True,
        "actuator_contract": "wheel_velocity_only",
    }
    for key, expected in expected_backend.items():
        if backend.get(key) != expected:
            raise PreflightEvidenceError(
                f"preflight backend contract mismatch: {key}={backend.get(key)!r}"
            )

    snapshot_path = artifacts["protocol/config_snapshot.yaml"][0]
    try:
        snapshot = _mapping(
            yaml.safe_load(snapshot_path.read_text(encoding="utf-8")),
            "preflight configuration snapshot",
        )
    except (OSError, yaml.YAMLError) as exc:
        raise PreflightEvidenceError(f"cannot read preflight configuration snapshot: {exc}") from exc
    configuration_hash = _canonical_sha256(snapshot)
    if manifest.get("configuration_sha256") != configuration_hash:
        raise PreflightEvidenceError("preflight configuration snapshot hash is inconsistent")
    _snapshot_contract_is_compatible(snapshot, config)
    preflight_config = _snapshot_campaign_config(snapshot, config)
    expected_runs = build_run_specs(preflight_config)
    _validate_design_artifacts(artifacts, manifest, preflight_config, expected_runs)

    cells, seed_count, primary_expected, _ = _expected_counts(snapshot)
    sensitivity = _mapping(snapshot["design"], "preflight configuration design")[
        "sensitivity"
    ]
    dt_values_s = _mapping(
        sensitivity, "preflight configuration sensitivity"
    ).get("dt_values_s")
    _validate_gate_status(
        gate_status,
        cells=cells,
        seed_count=seed_count,
        primary_expected=primary_expected,
        dt_values_s=dt_values_s,
    )

    scene_path = Path(str(config.backend.scene_path)).resolve()
    scene_audit_path = scene_path.with_suffix(".audit.json")
    if not scene_path.is_file() or not scene_audit_path.is_file():
        raise PreflightEvidenceError("confirmatory scene or independent scene audit is missing")
    scene_hash = _sha256_file(scene_path)
    scene_audit_hash = _sha256_file(scene_audit_path)
    if manifest.get("scene_sha256") != scene_hash:
        raise PreflightEvidenceError("preflight scene hash does not match confirmatory scene")
    if manifest.get("scene_audit_sha256") != scene_audit_hash:
        raise PreflightEvidenceError(
            "preflight scene-audit hash does not match confirmatory scene audit"
        )
    scene_audit_verification = validate_independent_scene_audit(scene_path)
    _require_true(
        scene_audit_verification.get("pass"),
        "confirmatory_scene_audit.full_hash_verification",
    )

    recorded_implementation = _mapping(
        manifest.get("implementation_sha256"),
        "preflight manifest.implementation_sha256",
    )
    live_implementation = current_implementation_hashes()
    if recorded_implementation != live_implementation:
        raise PreflightEvidenceError(
            "preflight implementation snapshot does not match the live Cargo package"
        )

    rows = _read_runs(artifacts["runs.csv"][0])
    _validate_runs(
        rows,
        manifest,
        expected_runs=expected_runs,
        preflight_config=preflight_config,
        controller_id=config.control.controller_id,
    )

    implementation_set_hash = _canonical_sha256(live_implementation)
    return PreflightAttestation(
        evidence_dir=root,
        experiment_id=str(manifest.get("experiment_id")),
        manifest_sha256=_sha256_file(manifest_path),
        gate_status_sha256=gate_hash,
        configuration_sha256=configuration_hash,
        design_sha256=str(manifest.get("design_sha256")),
        scene_sha256=scene_hash,
        scene_audit_sha256=scene_audit_hash,
        implementation_set_sha256=implementation_set_hash,
    )


__all__ = [
    "CALIBRATION_GATE_FIELDS",
    "OPERATIONAL_GATE_FIELDS",
    "PHYSICAL_GATE_FIELDS",
    "PreflightAttestation",
    "PreflightEvidenceError",
    "current_implementation_hashes",
    "validate_preflight_evidence",
]
