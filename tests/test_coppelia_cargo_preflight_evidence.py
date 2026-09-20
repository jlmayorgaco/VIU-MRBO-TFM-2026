from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "results" / "coppelia_cargo_preflight_minimal_v5"
SOURCE_CONFIG = (
    ROOT / "experiments" / "configs" / "coppelia_cargo_preflight_minimal.yaml"
)
IMPLEMENTATION_SNAPSHOT = (
    ROOT
    / "pre-thesis"
    / "evidence"
    / "cargo-code-snapshot-preflight-minimal-v5"
)
SCENE = ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.ttt"
SCENE_MANIFEST = SCENE.with_suffix(".manifest.json")
SCENE_AUDIT = SCENE.with_suffix(".audit.json")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(payload: object) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _artifact_path(relative: str) -> Path:
    """Interpret the Windows separators frozen in the campaign manifest portably."""

    return ARTIFACT.joinpath(*PureWindowsPath(relative).parts)


def _assert_hash_map(
    entries: dict[str, str],
    resolve_path: Callable[[str], Path],
) -> None:
    errors: list[str] = []
    for name, expected in sorted(entries.items()):
        if SHA256_RE.fullmatch(expected) is None:
            errors.append(f"{name}: malformed expected SHA-256 {expected!r}")
            continue
        path = resolve_path(name)
        try:
            actual = _sha256(path)
        except OSError as exc:
            errors.append(f"{name}: cannot read {path}: {exc}")
            continue
        if actual != expected:
            errors.append(f"{name}: expected {expected}, observed {actual}")
    assert not errors, "SHA-256 audit failed:\n" + "\n".join(errors)


def _typed_design_record(row: dict[str, str]) -> dict[str, object]:
    integer_fields = {"index", "active_robot_count", "seed_index", "seed"}
    string_fields = {
        "cell_id",
        "friction_regime",
        "coalition",
        "contact_offsets_body_m",
        "profile_peak_acceleration",
        "profile_peak_twist",
        "world_hash",
    }
    return {
        name: (
            int(value)
            if name in integer_fields
            else value
            if name in string_fields
            else float(value)
        )
        for name, value in row.items()
    }


def test_manifest_is_complete_and_covers_the_frozen_artifact() -> None:
    manifest = _json(ARTIFACT / "manifest.json")
    runs = _csv_rows(ARTIFACT / "runs.csv")
    failures = _csv_rows(ARTIFACT / "failures.csv")

    assert manifest["experiment_id"] == "COPPELIA_CARGO_PREFLIGHT_MINIMAL_v4"
    assert manifest["status"] == "complete"
    assert manifest["mode"] == "smoke"
    assert len(runs) == 6
    assert failures == []
    assert manifest["run_counts"] == {
        "accepted": 6,
        "completed": 6,
        "failed": 0,
        "rejected": 0,
        "total": 6,
    }

    artifact_hashes = manifest["artifact_sha256"]
    assert isinstance(artifact_hashes, dict)
    recorded_files = {
        PureWindowsPath(relative).as_posix() for relative in artifact_hashes
    }
    actual_files = {
        path.relative_to(ARTIFACT).as_posix()
        for path in ARTIFACT.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    assert recorded_files == actual_files
    _assert_hash_map(artifact_hashes, _artifact_path)


def test_config_design_implementation_scene_and_audit_hashes_are_valid() -> None:
    manifest = _json(ARTIFACT / "manifest.json")
    runs = _csv_rows(ARTIFACT / "runs.csv")
    design_rows = _csv_rows(ARTIFACT / "protocol" / "design.csv")

    snapshot = yaml.safe_load(
        (ARTIFACT / "protocol" / "config_snapshot.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(snapshot, dict)
    assert manifest["configuration_sha256"] == _canonical_sha256(snapshot)
    assert manifest["source_config_sha256"] == _sha256(SOURCE_CONFIG)

    assert len(design_rows) == 1
    world = _typed_design_record(design_rows[0])
    frozen_run_specs = [
        {
            "run_id": row["run_id"],
            "phase": row["phase"],
            "guard": row["guard"],
            "dt_s": float(row["dt_s"]),
            **world,
        }
        for row in runs
    ]
    assert manifest["design_sha256"] == _canonical_sha256(frozen_run_specs)

    snapshot_manifest = _json(IMPLEMENTATION_SNAPSHOT / "manifest.json")
    assert snapshot_manifest["source_artifact"] == (
        "results/coppelia_cargo_preflight_minimal_v5"
    )
    assert snapshot_manifest["source_artifact_manifest_sha256"] == _sha256(
        ARTIFACT / "manifest.json"
    )
    assert snapshot_manifest["source_gate_status_sha256"] == _sha256(
        ARTIFACT / "gate_status.json"
    )

    implementation_hashes = manifest["implementation_sha256"]
    assert isinstance(implementation_hashes, dict)
    assert snapshot_manifest["implementation_sha256"] == implementation_hashes
    assert set(implementation_hashes) == {
        path.name for path in IMPLEMENTATION_SNAPSHOT.glob("*.py")
    }
    _assert_hash_map(
        implementation_hashes,
        lambda name: IMPLEMENTATION_SNAPSHOT / name,
    )

    assert manifest["scene_sha256"] == _sha256(SCENE)
    assert manifest["scene_audit_sha256"] == _sha256(SCENE_AUDIT)

    scene_manifest = _json(SCENE_MANIFEST)
    assert scene_manifest["scene"]["sha256"] == _sha256(SCENE)
    assert scene_manifest["status"] == "structurally_valid_not_physically_calibrated"
    for entry in scene_manifest["inputs"].values():
        path = str(entry["path"])
        if "://" not in path:
            assert entry["sha256"] == _sha256(ROOT / path)

    audit = _json(SCENE_AUDIT)
    assert audit["schema"] == "viu-cargo-runtime-audit-v1"
    assert audit["pass"] is True
    assert all(audit["checks"].values())
    for entry in audit["artifacts"].values():
        audited_path = (ROOT / entry["path"]).resolve()
        assert audited_path.is_relative_to(ROOT.resolve())
        assert entry["sha256"] == _sha256(audited_path)


def test_ack_backend_actuation_and_world_identity_are_bound() -> None:
    manifest = _json(ARTIFACT / "manifest.json")
    gates = _json(ARTIFACT / "gate_status.json")
    runs = _csv_rows(ARTIFACT / "runs.csv")
    design_rows = _csv_rows(ARTIFACT / "protocol" / "design.csv")

    backend = manifest["backend"]
    assert backend["backend_kind"] == "coppeliasim_mujoco"
    assert backend["engine"] == "mujoco"
    assert backend["actuator_contract"] == "wheel_velocity_only"
    assert backend["synchronous_stepping"] is True
    assert {row["backend_kind"] for row in runs} == {"coppeliasim_mujoco"}
    assert {row["ack_engine"] for row in runs} == {"mujoco"}
    assert {row["ack_actuation_contract"] for row in runs} == {"wheel_velocity_only"}

    sequences = [int(row["ack_reset_sequence"]) for row in runs]
    ack_hashes = [row["ack_contract_hash"] for row in runs]
    assert sequences == list(range(1, 7))
    assert len(set(ack_hashes)) == 6
    assert all(SHA256_RE.fullmatch(value) for value in ack_hashes)
    measurements = gates["physical_scene_measurements"]
    assert measurements["all_ack_reset_sequences"] == list(range(1, 7))
    assert measurements["primary_ack_reset_sequences"] == [1, 2, 3]
    assert measurements["unique_ack_contract_hashes"] == 6

    world_hashes = {row["world_hash"] for row in runs}
    assert len(world_hashes) == 1
    assert world_hashes == {design_rows[0]["world_hash"]}
    assert all(SHA256_RE.fullmatch(value) for value in world_hashes)
    assert gates["design"]["factorial_cells"] == 1
    assert gates["design"]["paired_world_hashes_across_guards"] is True


def test_negative_and_not_executed_gates_cannot_support_a_physical_claim() -> None:
    manifest = _json(ARTIFACT / "manifest.json")
    gates = _json(ARTIFACT / "gate_status.json")
    runs = _csv_rows(ARTIFACT / "runs.csv")

    assert manifest["scientific_use"] == "physical_candidate_subject_to_gate_status"
    assert {row["physical_success"] for row in runs} == {"False"}
    assert gates["evidence"]["confirmatory_claim_eligible"] is False

    assert {row["force_transmission_status"] for row in runs} == {"not_executed"}
    assert {row["wheel_twist_status"] for row in runs} == {"not_executed"}
    assert {row["force_transmission_gate_pass"] for row in runs} == {"False"}
    assert {row["wheel_twist_gate_pass"] for row in runs} == {"False"}
    assert gates["physical_scene"]["force_transmission_gate_pass"] is False
    assert gates["physical_scene"]["wheel_twist_gate_pass"] is False
    assert gates["physical_scene_measurements"]["force_transmission_status"] == [
        "not_executed"
    ]
    assert gates["physical_scene_measurements"]["wheel_twist_status"] == [
        "not_executed"
    ]

    assert {row["dwell_achieved"] for row in runs} == {"False"}
    assert {row["terminal_gate_pass"] for row in runs} == {"False"}

    sensitivity = gates["dt_sensitivity"]
    sensitivity_rows = [row for row in runs if row["phase"] == "dt_sensitivity"]
    assert len(sensitivity_rows) == 3
    assert sensitivity["complete"] is True
    assert sensitivity["dt_values_s"] == [0.005]
    assert sensitivity["interpretation"] == (
        "single_dt_repeat_only_not_a_sensitivity_study"
    )
    assert sensitivity["pass"] is False
    assert {float(row["dt_s"]) for row in sensitivity_rows} == {0.005}
