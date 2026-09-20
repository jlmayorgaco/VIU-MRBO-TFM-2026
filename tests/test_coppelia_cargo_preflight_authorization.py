from __future__ import annotations

import csv
import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from viu_mrob_tfm.coppelia_cargo import load_config
from viu_mrob_tfm.coppelia_cargo.campaign import (
    _all_physical_runs_pass,
    run_campaign,
)
from viu_mrob_tfm.coppelia_cargo.coppelia_backend import build_world_contract
from viu_mrob_tfm.coppelia_cargo.design import build_run_specs, build_worlds, design_hash
from viu_mrob_tfm.coppelia_cargo.preflight import (
    CALIBRATION_GATE_FIELDS,
    OPERATIONAL_GATE_FIELDS,
    PHYSICAL_GATE_FIELDS,
    PreflightEvidenceError,
    current_implementation_hashes,
    validate_preflight_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATORY = ROOT / "experiments" / "configs" / "coppelia_cargo_confirmatory.yaml"
PREFLIGHT = ROOT / "experiments" / "configs" / "coppelia_cargo_preflight.yaml"
HISTORICAL_PREFLIGHT = ROOT / "results" / "coppelia_cargo_preflight_minimal_v5"
SCENE = ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.ttt"
SCENE_AUDIT = SCENE.with_suffix(".audit.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _refresh_artifact_hash(evidence: Path, relative: str) -> None:
    manifest_path = evidence / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact_sha256"][relative] = _sha256(evidence / relative)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


def _approved_preflight_fixture(
    tmp_path: Path,
    *,
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    mutate_gates: Callable[[dict[str, Any]], None] | None = None,
    mutate_snapshot: Callable[[dict[str, Any]], None] | None = None,
) -> Path:
    """Create a hash-consistent unit fixture; it is never physical evidence."""

    evidence = tmp_path / "approved-preflight-unit-fixture"
    (evidence / "protocol").mkdir(parents=True)
    (evidence / "inference").mkdir()
    preflight = load_config(PREFLIGHT)
    snapshot = json.loads(json.dumps(asdict(preflight)))
    if mutate_snapshot is not None:
        mutate_snapshot(snapshot)
    (evidence / "protocol" / "config_snapshot.yaml").write_text(
        yaml.safe_dump(snapshot, sort_keys=False), encoding="utf-8"
    )

    specs = build_run_specs(preflight)
    worlds = build_worlds(preflight)
    rows: list[dict[str, object]] = []
    for reset_sequence, spec in enumerate(specs, start=1):
        contract = build_world_contract(
            preflight, spec.world, spec.dt_s, reset_sequence
        )
        row: dict[str, object] = {
            "run_id": spec.run_id,
            "phase": spec.phase,
            "guard": spec.guard,
            "dt_s": spec.dt_s,
            "guard_accepted": True,
            "world_hash": spec.world.world_hash,
            "cell_id": spec.world.cell.cell_id,
            "cell_index": spec.world.cell.index,
            "seed_index": spec.world.seed_index,
            "seed": spec.world.seed,
            "coalition": spec.world.cell.coalition,
            "active_robot_count": spec.world.active_robot_count,
            "controller_id": preflight.control.controller_id,
            "backend_kind": "coppeliasim_mujoco",
            "ack_engine": "mujoco",
            "ack_actuation_contract": "wheel_velocity_only",
            "ack_reset_sequence": reset_sequence,
            "ack_contract_hash": contract["contract_hash"],
            "execution_status": "completed",
            "physical_success": True,
            "nan_detected": False,
        }
        row.update({field: True for field in PHYSICAL_GATE_FIELDS})
        rows.append(row)
    run_fields = list(rows[0])
    _write_csv(evidence / "runs.csv", run_fields, rows)
    _write_csv(
        evidence / "failures.csv",
        [
            "run_id",
            "phase",
            "world_hash",
            "guard",
            "guard_accepted",
            "error_type",
            "error_message",
        ],
        [],
    )
    _write_csv(evidence / "summary.csv", ["phase", "guard", "runs"], [])
    design_records = [world.as_record() for world in worlds]
    _write_csv(
        evidence / "protocol" / "design.csv",
        list(design_records[0]),
        design_records,
    )
    _write_csv(
        evidence / "protocol" / "seed_registry.csv",
        ["seed_index", "seed"],
        [
            {"seed_index": index, "seed": seed}
            for index, seed in enumerate(preflight.design.seeds.values)
        ],
    )
    _write_csv(evidence / "inference" / "cell_guard_rates.csv", ["cell_id"], [])
    _write_csv(
        evidence / "inference" / "paired_guard_contrasts.csv",
        ["contrast_id"],
        [],
    )
    (evidence / "inference" / "analysis_contract.json").write_text(
        json.dumps({"complete": True}), encoding="utf-8"
    )
    (evidence / "coppeliasim.log").write_text(
        "unit fixture only; CoppeliaSim was not executed\n", encoding="utf-8"
    )
    with gzip.open(evidence / "series.csv.gz", "wt", encoding="utf-8") as handle:
        handle.write("run_id,time_s\n")

    primary = [spec for spec in specs if spec.phase == "primary"]
    dt_runs = [spec for spec in specs if spec.phase == "dt_sensitivity"]
    gate_status: dict[str, Any] = {
        "design": {
            "factorial_cells": preflight.design.cell_count,
            "perturbations_per_cell": preflight.design.seeds.count,
            "primary_runs_expected": len(primary),
            "primary_runs_recorded": len(primary),
            "paired_world_hashes_across_guards": True,
            "dt_sensitivity_values_s": list(preflight.design.sensitivity.dt_values_s),
        },
        "execution": {
            "all_primary_recorded": True,
            "failed_runs": 0,
            "nan_runs": 0,
            "fresh_ack_reset_sequences": True,
        },
        "physical_scene": {field: True for field in CALIBRATION_GATE_FIELDS},
        "physical_trials": {field: True for field in OPERATIONAL_GATE_FIELDS},
        "dt_sensitivity": {"complete": True, "pass": True},
        "paired_execution_repeatability": {"complete": True, "pass": True},
        "preflight": {
            "applicable": True,
            "approved": True,
            "all_runs_physical_success": True,
            "required_gate_fields": list(PHYSICAL_GATE_FIELDS),
        },
        "evidence": {
            "backend_kind": "coppeliasim_mujoco",
            "evidence_class": "physical_coppeliasim_candidate",
        },
    }
    if mutate_gates is not None:
        mutate_gates(gate_status)
    (evidence / "gate_status.json").write_text(
        json.dumps(gate_status, indent=2, sort_keys=True), encoding="utf-8"
    )

    artifact_hashes = {
        path.relative_to(evidence).as_posix(): _sha256(path)
        for path in sorted(evidence.rglob("*"))
        if path.is_file()
    }
    manifest: dict[str, Any] = {
        "artifact_sha256": artifact_hashes,
        "backend": {
            "actuator_contract": "wheel_velocity_only",
            "backend_kind": "coppeliasim_mujoco",
            "engine": "mujoco",
            "evidence_class": "physical_coppeliasim_candidate",
            "simulator_version": "unit-fixture",
            "synchronous_stepping": True,
        },
        "configuration_sha256": _canonical_sha256(snapshot),
        "controller_id": preflight.control.controller_id,
        "design_sha256": design_hash(specs),
        "experiment_id": "COPPELIA_CARGO_PREFLIGHT_UNIT_FIXTURE",
        "implementation_sha256": current_implementation_hashes(),
        "mode": "smoke",
        "protocol_family": preflight.protocol_family,
        "run_counts": {
            "accepted": len(rows),
            "completed": len(rows),
            "failed": 0,
            "rejected": 0,
            "total": len(rows),
        },
        "scene_audit_sha256": _sha256(SCENE_AUDIT),
        "scene_sha256": _sha256(SCENE),
        "scientific_use": "physical_candidate_subject_to_gate_status",
        "status": "complete",
    }
    if mutate_manifest is not None:
        mutate_manifest(manifest)
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    assert len(primary) == 48
    assert len(dt_runs) == 18
    return evidence


def test_confirmatory_requires_preflight_before_creating_output(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    output = tmp_path / "must-not-exist"
    with pytest.raises(PreflightEvidenceError, match="preflight-evidence"):
        run_campaign(
            config,
            output_dir=output,
            authorize_confirmatory=True,
        )
    assert not output.exists()


@pytest.mark.parametrize("authorization", [False, "false", 1, object()])
def test_confirmatory_api_requires_literal_true_authorization(
    tmp_path: Path, authorization: object
) -> None:
    config = load_config(CONFIRMATORY)
    output = tmp_path / "must-not-exist"
    with pytest.raises(PermissionError, match="authorize-confirmatory"):
        run_campaign(
            config,
            output_dir=output,
            authorize_confirmatory=authorization,  # type: ignore[arg-type]
        )
    assert not output.exists()


def test_historical_minimal_v5_cannot_authorize_confirmatory(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    output = tmp_path / "must-not-exist"
    with pytest.raises(PreflightEvidenceError):
        run_campaign(
            config,
            output_dir=output,
            authorize_confirmatory=True,
            preflight_evidence=HISTORICAL_PREFLIGHT,
        )
    assert not output.exists()


def test_confirmatory_forbids_backend_injection_before_creating_output(
    tmp_path: Path,
) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    output = tmp_path / "must-not-exist"
    with pytest.raises(PermissionError, match="backend_factory"):
        run_campaign(
            config,
            output_dir=output,
            authorize_confirmatory=True,
            preflight_evidence=evidence,
            backend_factory=lambda _: None,  # type: ignore[arg-type,return-value]
        )
    assert not output.exists()


def test_physical_preflight_forbids_backend_injection_before_creating_output(
    tmp_path: Path,
) -> None:
    config = load_config(PREFLIGHT)
    output = tmp_path / "must-not-exist"
    with pytest.raises(PermissionError, match="backend_factory"):
        run_campaign(
            config,
            output_dir=output,
            backend_factory=lambda _: None,  # type: ignore[arg-type,return-value]
        )
    assert not output.exists()


def test_approved_hash_bound_preflight_is_accepted(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    attestation = validate_preflight_evidence(config, evidence)
    assert attestation.experiment_id == "COPPELIA_CARGO_PREFLIGHT_UNIT_FIXTURE"
    assert attestation.gate_status_sha256 == _sha256(evidence / "gate_status.json")
    assert attestation.scene_sha256 == _sha256(SCENE)
    assert Path(attestation.evidence_dir) == evidence.resolve()
    assert "evidence_dir" not in attestation.as_record()


def test_tampered_gate_status_is_rejected(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    gate_path = evidence / "gate_status.json"
    gate_path.write_text(gate_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(PreflightEvidenceError, match="SHA-256 mismatch"):
        validate_preflight_evidence(config, evidence)


def test_hash_consistent_but_failed_gate_is_rejected(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)

    def fail_terminal(gates: dict[str, Any]) -> None:
        gates["physical_trials"]["terminal_gate_pass"] = False
        gates["preflight"]["approved"] = False
        gates["preflight"]["all_runs_physical_success"] = False

    evidence = _approved_preflight_fixture(tmp_path, mutate_gates=fail_terminal)
    with pytest.raises(PreflightEvidenceError, match="preflight.approved"):
        validate_preflight_evidence(config, evidence)


def test_preflight_snapshot_must_use_the_same_three_guards(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)

    def remove_guard(snapshot: dict[str, Any]) -> None:
        snapshot["guards"] = snapshot["guards"][:-1]

    evidence = _approved_preflight_fixture(tmp_path, mutate_snapshot=remove_guard)
    with pytest.raises(PreflightEvidenceError, match="three-guard protocol"):
        validate_preflight_evidence(config, evidence)


def test_hash_consistent_but_wrong_design_csv_is_rejected(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    design_path = evidence / "protocol" / "design.csv"
    with design_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    rows[0]["actual_payload_mass_kg"] = str(
        float(rows[0]["actual_payload_mass_kg"]) + 1.0
    )
    _write_csv(design_path, fieldnames, rows)
    _refresh_artifact_hash(evidence, "protocol/design.csv")
    with pytest.raises(PreflightEvidenceError, match="protocol design.csv"):
        validate_preflight_evidence(config, evidence)


def test_hash_consistent_but_invalid_run_ack_is_rejected(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    runs_path = evidence / "runs.csv"
    with runs_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    rows[0]["ack_engine"] = "not-mujoco"
    _write_csv(runs_path, fieldnames, rows)
    _refresh_artifact_hash(evidence, "runs.csv")
    with pytest.raises(PreflightEvidenceError, match="acknowledge MuJoCo"):
        validate_preflight_evidence(config, evidence)


def test_hash_consistent_but_wrong_contract_hash_is_rejected(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path)
    runs_path = evidence / "runs.csv"
    with runs_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    rows[0]["ack_contract_hash"] = "0" * 64
    _write_csv(runs_path, fieldnames, rows)
    _refresh_artifact_hash(evidence, "runs.csv")
    with pytest.raises(PreflightEvidenceError, match="SI world contract"):
        validate_preflight_evidence(config, evidence)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda manifest: manifest["backend"].update(
                synchronous_stepping=False
            ),
            "backend contract mismatch",
        ),
        (
            lambda manifest: manifest.update(controller_id="other-controller"),
            "controller does not match",
        ),
        (
            lambda manifest: manifest.update(scene_sha256="0" * 64),
            "scene hash does not match",
        ),
        (
            lambda manifest: manifest["implementation_sha256"].update(
                {"campaign.py": "0" * 64}
            ),
            "implementation snapshot does not match",
        ),
    ],
)
def test_preflight_must_match_backend_controller_scene_and_code(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    config = load_config(CONFIRMATORY)
    evidence = _approved_preflight_fixture(tmp_path, mutate_manifest=mutation)
    with pytest.raises(PreflightEvidenceError, match=message):
        validate_preflight_evidence(config, evidence)


def test_every_operational_gate_and_physical_success_is_required() -> None:
    passing: dict[str, object] = {
        "execution_status": "completed",
        "physical_success": True,
        **{field: True for field in PHYSICAL_GATE_FIELDS},
    }
    assert _all_physical_runs_pass([passing])
    for field in (*OPERATIONAL_GATE_FIELDS, "physical_success"):
        failing = dict(passing)
        failing[field] = False
        assert not _all_physical_runs_pass([passing, failing]), field
