"""Guarded SP0 campaign execution after B0 freeze.

This module executes the blocks that can be produced by the current numerical
simulator without fabricating unavailable data-driven training results. It stops
before confirmatory test seeds when the real IPPO/MAPPO trainer is absent.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import yaml

from viu_mrob_tfm.sp0.methods import assignment_valid, run_sp0_method
from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result
from viu_mrob_tfm.sp0.runner import _config_hash, _git_hash
from viu_mrob_tfm.sp0.scenario import SP0World, make_sp0_world, public_world_view
from viu_mrob_tfm.utils.io import coerce_nullable_dataframe_types, ensure_directory, load_yaml, save_json

DYNAMICS = ["REP", "SMI", "BNN", "LOG", "PROJ", "IBR", "GPC", "HYB"]
FITNESS = ["LIN", "QUAD", "ASYM", "SIG", "MC"]
B2_CLOSURES = ["RAW", "QR1"]
REGIMES = [1.5, 1.0, 0.67]
B2_SIZES = [8, 32]
B4_SIZES = [8, 16, 32, 64]


def run_available_campaign(
    config_path: str | Path,
    *,
    resume: bool = True,
    dry_run: bool = False,
    block: str | None = None,
) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1"))
    _require_frozen(root)
    os.environ["SP0_AUDIT_TRAJECTORY_ROOT"] = str(ensure_directory(root / "audit" / "trajectories"))
    target_block = str(block).upper() if block else None
    if target_block and target_block not in {"B1", "B2", "B3", "B4", "B5", "B6", "B7"}:
        raise ValueError(f"Unknown SP0 block: {block}")
    manifest: dict[str, Any] = {
        "started_at_utc": datetime.now(UTC).isoformat(),
        "requested_block": target_block,
        "resume": bool(resume),
        "dry_run": bool(dry_run),
        "confirmatory_seeds_opened": False,
        "completed_blocks": [],
    }
    if dry_run:
        plan = planned_counts()
        manifest.update({"status": "dry_run", "planned_counts": plan})
        save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
        return manifest

    b1 = run_b1_world_cache(config, root, resume=resume)
    manifest["B1"] = b1
    manifest["completed_blocks"].append("B1")
    if target_block == "B1":
        return finish_requested_block(root, manifest)

    b2 = run_b2_screening(config, root, resume=resume)
    manifest["B2"] = b2
    manifest["completed_blocks"].append("B2")
    if target_block == "B2":
        return finish_requested_block(root, manifest)

    b3 = run_b3_tuning(config, root, resume=resume)
    manifest["B3"] = b3
    manifest["completed_blocks"].append("B3")
    if target_block == "B3":
        return finish_requested_block(root, manifest)

    selection_validation = run_model_selection_validation(config, root, resume=resume)
    manifest["selection_validation"] = selection_validation
    manifest["completed_blocks"].append("MODEL_SELECTION_VALIDATION")

    training_block = data_driven_training_status(root)
    manifest["training"] = training_block
    if training_block["status"] != "complete":
        manifest["status"] = "blocked_before_confirmatory_seed_opening"
        manifest["blocked_at"] = "training_before_B4"
        manifest["reason"] = training_block["reason"]
        save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
        write_campaign_report(root, manifest)
        return manifest

    executor_block = data_driven_execution_status(root, training_block)
    manifest["data_driven_execution"] = executor_block
    if executor_block["status"] != "complete":
        manifest["status"] = "blocked_before_confirmatory_seed_opening"
        manifest["blocked_at"] = "data_driven_executor_before_B4"
        manifest["reason"] = executor_block["reason"]
        save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
        write_campaign_report(root, manifest)
        return manifest

    opening_event = record_confirmatory_seed_opening(root, training_block, selection_validation)
    manifest["confirmatory_seeds_opened"] = True
    manifest["confirmatory_seeds_opened_at_utc"] = opening_event["opened_at_utc"]
    manifest["confirmatory_seed_opening_event"] = opening_event
    manifest["champions_sha256_at_seed_opening"] = opening_event["b3_champions_sha256"]
    manifest["data_driven_champion_sha256_at_seed_opening"] = opening_event["data_driven_champion_sha256"]
    manifest["model_selection_sha256_at_seed_opening"] = opening_event["model_selection_sha256"]
    save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
    confirmatory_worlds, confirmatory_cache = materialize_confirmatory_worlds(config, root)
    manifest["confirmatory_world_cache"] = confirmatory_cache
    save_json(root / "FINAL_RUN_MANIFEST.json", manifest)

    b4 = run_b4_confirmatory(config, root, training_block, worlds=confirmatory_worlds["B4"], resume=resume)
    manifest["B4"] = b4
    manifest["completed_blocks"].append("B4")
    if target_block == "B4":
        return finish_requested_block(root, manifest)
    b5 = run_b5_communication(config, root, training_block, worlds=confirmatory_worlds["B5"], resume=resume)
    manifest["B5"] = b5
    manifest["completed_blocks"].append("B5")
    if target_block == "B5":
        return finish_requested_block(root, manifest)
    b6 = run_b6_stress(config, root, training_block, worlds=confirmatory_worlds["B6"], resume=resume)
    manifest["B6"] = b6
    manifest["completed_blocks"].append("B6")
    if target_block == "B6":
        return finish_requested_block(root, manifest)
    b7 = run_b7_generalization(config, root, training_block, worlds=confirmatory_worlds["B7"], resume=resume)
    manifest["B7"] = b7
    manifest["completed_blocks"].append("B7")
    manifest["confirmatory_seeds_opened"] = True
    manifest["status"] = "confirmatory_blocks_complete"
    save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
    write_campaign_report(root, manifest)
    return manifest


def run_integral_dry_run(config_path: str | Path, training_status: dict[str, Any]) -> dict[str, Any]:
    config = load_yaml(config_path)
    root = ensure_directory(config.get("output_dir", "results/sp0/SP0_PROTOCOL_v1_1"))
    smoke_dir = ensure_directory(root / "smoke")
    os.environ["SP0_AUDIT_TRAJECTORY_ROOT"] = str(ensure_directory(root / "audit" / "trajectories"))
    training_dir = root / "training" / "dry_run"
    implementation_hash = sha256_python_sources(Path(__file__).parent)
    report_path = smoke_dir / "integral_dry_run_report.json"
    runs_path = smoke_dir / "integral_dry_run_runs.parquet"
    if report_path.exists() and runs_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous.get("status") == "PASS" and previous.get("implementation_sha256") == implementation_hash:
            return {**previous, "resume_reused": True}

    checkpoint_by_algorithm: dict[str, Path] = {}
    for algorithm in ["IPPO-GNN", "MAPPO-GNN"]:
        candidates = sorted((training_dir / algorithm.replace("-", "_")).rglob("checkpoint.pt"))
        if not candidates:
            raise RuntimeError(f"Integral dry-run requires a real reduced-budget checkpoint for {algorithm}")
        checkpoint_by_algorithm[algorithm] = candidates[-1]

    cases = [
        ("nominal", 8, 8, "G-UNI", "all"),
        ("crossed", 8, 8, "G-X", "all"),
        ("zero_support", 8, 8, "G-ZERO", "all"),
        ("connected_local", 8, 8, "G-UNI", 4),
        ("disconnected", 8, 8, "G-UNI", 0),
        ("robot_scarcity", 8, 12, "G-UNI", 4),
        ("robot_surplus", 12, 8, "G-UNI", 4),
        ("balanced_N16", 16, 16, "G-UNI", 6),
        ("unseen_N24", 24, 24, "G-UNI", 4),
        ("unseen_N48", 48, 48, "G-UNI", 4),
        ("inference_N64", 64, 64, "G-UNI", 6),
    ]
    specs: list[dict[str, Any]] = [{"id": "HUN"}, {"id": "GRD"}, {"id": "DA"}]
    for dynamic in DYNAMICS:
        for closure in ["RAW", "ARG", "REPAIR", "QR1", "QR2", "QRA"]:
            specs.append(
                {
                    "id": dynamic,
                    "fitness_id": "ASYM",
                    "rounding_id": closure,
                    "h": 0.05,
                    "dt": 0.1,
                    "max_steps": 6,
                    "stable_window_steps": 2,
                    "architecture": "distributed_local",
                }
            )
    for algorithm, checkpoint in checkpoint_by_algorithm.items():
        payload = __import__("torch").load(checkpoint, map_location="cpu", weights_only=False)
        specs.append(
            {
                "id": algorithm,
                "checkpoint_path": str(checkpoint),
                "checkpoint_hash": sha256_file(checkpoint),
                "training_steps": int(payload.get("training_steps", 0)),
                "train_seed": int(payload.get("train_seed", 0)),
                "training_converged": bool(payload.get("training_converged", False)),
            }
        )

    rows: list[dict[str, Any]] = []
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    for case_index, (case_id, n, k, geometry, degree) in enumerate(cases):
        world = make_sp0_world(
            n_robots=n,
            n_loads=k,
            seed=8000 + case_index,
            geometry_id=geometry,
            mean_degree_target=degree,
            sp_id=str(config.get("sp_id", "SP0-v1.1")),
        )
        case_specs = (
            [spec for spec in specs if str(spec.get("id", "")).startswith(("IPPO", "MAPPO"))]
            if n in {24, 48, 64}
            else specs
        )
        for spec in case_specs:
            rows.append(
                run_row(
                    world,
                    spec,
                    "SP0_v1_1_integral_dry_run",
                    "DRY",
                    config_hash,
                    git_hash,
                    timestamp,
                    extra={"dry_case": case_id, "exploratory_debug_only": True},
                )
            )

    duplicate_keys = [
        (
            row.get("dry_case"), row.get("method_variant"), row.get("dynamic_id"),
            row.get("fitness_id"), row.get("rounding_id"), row.get("train_seed"),
        )
        for row in rows
    ]
    method_errors = [row for row in rows if row.get("error_type")]
    world_mismatch = any(
        len({str(row.get("world_hash")) for row in rows if row.get("dry_case") == case[0]}) != 1
        for case in cases
    )
    schema_missing = sorted(CORE_RUN_FIELDS.difference(rows[0])) if rows else sorted(CORE_RUN_FIELDS)
    b1_root = ensure_directory(smoke_dir / "b1_dry_run")
    b1_first = run_b1_world_cache(config, b1_root, resume=False)
    b1_resumed = run_b1_world_cache(config, b1_root, resume=True)
    registry = default_seed_registry()
    seed_values = [set(values) for values in registry.values()]
    seed_sets_disjoint = all(not left.intersection(right) for index, left in enumerate(seed_values) for right in seed_values[index + 1 :])
    checks = {
        "all_methods_executed_without_error": not method_errors,
        "no_duplicate_rows": len(set(duplicate_keys)) == len(duplicate_keys),
        "all_methods_share_world_per_case": not world_mismatch,
        "schema_valid": not schema_missing,
        "seed_sets_disjoint": seed_sets_disjoint,
        "b1_cache_valid": bool(b1_first.get("cache_validated")),
        "b1_resume_validated": bool(b1_resumed.get("resume_validated", b1_resumed.get("cache_validated"))),
        "ippo_checkpoint_inference": any(row.get("method_variant") == "IPPO-GNN" for row in rows),
        "mappo_checkpoint_inference": any(row.get("method_variant") == "MAPPO-GNN" for row in rows),
        "variable_sizes_24_48_64": all(any(row.get("N") == n for row in rows) for n in [24, 48, 64]),
        "confirmatory_seeds_untouched": all(int(row.get("world_seed")) < 13000 for row in rows),
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "method_errors": [
            {"case": row.get("dry_case"), "method": row.get("method_variant"), "error": row.get("error_message")}
            for row in method_errors
        ],
        "runs": len(rows),
        "methods": len(specs),
        "cases": len(cases),
        "exploratory_debug_only": True,
        "implementation_sha256": implementation_hash,
        "data_driven_training_status": training_status,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "resume_reused": False,
    }
    write_parquet(runs_path, rows)
    save_json(report_path, report)
    if report["status"] != "PASS":
        raise RuntimeError("Integral dry-run failed: " + json.dumps(report["failed_checks"]))
    return report


def finish_requested_block(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    manifest["status"] = "requested_block_complete"
    manifest["finished_at_utc"] = datetime.now(UTC).isoformat()
    save_json(root / "FINAL_RUN_MANIFEST.json", manifest)
    write_campaign_report(root, manifest)
    return manifest


def planned_counts() -> dict[str, int]:
    return {"B0": 300, "B2": 2400, "B3": 1536, "B4": 5760, "B5": 4000, "B6": 960, "B7": 480, "TOTAL": 15436}


BLOCK_PRIMARY_KEYS = {
    "B2": ["dynamic_id", "fitness_id", "rounding_id", "world_hash"],
    "B3": ["family", "config_id", "round", "world_hash"],
    "B4": ["method_variant", "train_seed", "world_hash"],
    "B5": ["method_variant", "train_seed", "world_hash", "target_mean_degree"],
    "B6": ["method_variant", "train_seed", "world_hash", "stress_type"],
    "B7": ["method_variant", "train_seed", "world_hash"],
}
CORE_RUN_FIELDS = {
    "sp_id", "experiment_id", "block_id", "method_family", "method_variant", "world_seed", "N", "K",
    "world_hash", "config_hash", "git_hash", "timestamp_utc", "matching_valid", "maximum_cardinality",
    "final_success", "continuous_converged", "continuous_timeout", "closure_applied", "closure_success",
    "runtime_wall_s", "time_to_epsilon_solution", "time_to_epsilon_duration_s", "time_to_epsilon_observed", "messages_to_epsilon_solution", "bytes_to_epsilon_solution", "trajectory_path", "trajectory_sha256", "error_type", "error_message",
}


def validate_completed_block(
    rows: list[dict[str, Any]],
    *,
    block_id: str,
    expected_runs: int,
    config_hash: str,
) -> list[str]:
    errors: list[str] = []
    if len(rows) != expected_runs:
        errors.append(f"{block_id} rows={len(rows)} expected={expected_runs}")
    if rows:
        missing = CORE_RUN_FIELDS.difference(rows[0])
        if missing:
            errors.append(f"{block_id} missing schema fields: {sorted(missing)}")
    if any(str(row.get("block_id")) != block_id for row in rows):
        errors.append(f"{block_id} contains rows from another block")
    if any(str(row.get("config_hash")) != str(config_hash) for row in rows):
        errors.append(f"{block_id} config_hash mismatch")
    keys = BLOCK_PRIMARY_KEYS[block_id]
    identities = [tuple(normalize_identity(row.get(key)) for key in keys) for row in rows]
    if len(set(identities)) != len(identities):
        errors.append(f"{block_id} contains duplicate primary keys")
    world_groups: dict[tuple[Any, ...], set[str]] = {}
    for row in rows:
        group = (
            row.get("world_seed"), row.get("N"), row.get("K"), row.get("geometry_id"),
            normalize_identity(row.get("R")), row.get("target_mean_degree"), row.get("stress_type"),
        )
        world_groups.setdefault(group, set()).add(str(row.get("world_hash")))
    inconsistent = [group for group, hashes in world_groups.items() if len(hashes) != 1]
    if inconsistent:
        errors.append(f"{block_id} has {len(inconsistent)} world specifications with inconsistent world_hash")
    return errors


def normalize_identity(value: Any) -> Any:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "<null>"
    if isinstance(value, float):
        return round(value, 12)
    return value


def preserve_invalid_resume(root: Path, block_id: str, runs_path: Path, errors: list[str]) -> None:
    audit_dir = ensure_directory(root / "audit" / "rejected_resume")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    preserved = audit_dir / f"{block_id.lower()}_{stamp}.parquet"
    shutil.copy2(runs_path, preserved)
    save_json(
        audit_dir / f"{block_id.lower()}_{stamp}.json",
        {"block_id": block_id, "source": str(runs_path), "preserved": str(preserved), "errors": errors},
    )


def write_validated_runs(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    block_id: str,
    expected_runs: int,
    config_hash: str,
) -> None:
    errors = validate_completed_block(rows, block_id=block_id, expected_runs=expected_runs, config_hash=config_hash)
    if errors:
        raise RuntimeError("Refusing to write invalid campaign block: " + "; ".join(errors))
    write_parquet(path, rows)


def default_seed_registry() -> dict[str, list[int]]:
    return {
        "unit_seeds": list(range(8000, 8010)),
        "screening_seeds": list(range(10000, 10005)),
        "tuning_seeds": list(range(11000, 11030)),
        "validation_seeds": list(range(12000, 12040)),
        "test_seeds_1_40": list(range(13000, 13040)),
        "extension_seeds_41_60": list(range(13040, 13060)),
        "extension_seeds_61_100": list(range(13060, 13100)),
        "generalization_seeds": list(range(14000, 14040)),
        "training_seeds": [14101, 14201, 14202, 15001, 15002, 15003],
    }


def frozen_manifest_path(root: Path, *, required: bool = True) -> Path | None:
    candidates = sorted((root / "protocol").glob("frozen_manifest*.json"))
    if len(candidates) > 1:
        raise RuntimeError(f"Multiple frozen manifests found: {[path.name for path in candidates]}")
    if candidates:
        return candidates[0]
    if required:
        raise RuntimeError("Versioned frozen protocol manifest is missing.")
    return None


def load_frozen_seed_registry(
    root: Path,
    *,
    required: bool = True,
    allow_confirmatory: bool = False,
) -> dict[str, list[int]]:
    manifest_path = frozen_manifest_path(root, required=False)
    if manifest_path is None:
        if required:
            raise RuntimeError("Frozen seed registry cannot be read before protocol freeze.")
        registry = default_seed_registry()
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        names = manifest.get("artifact_names", {})
        seed_path = root / "protocol" / str(names.get("seeds", "seed_registry.yaml"))
        if not seed_path.exists() or sha256_file(seed_path) != manifest.get("seed_registry_sha256"):
            raise RuntimeError("Frozen seed registry is missing or its SHA-256 does not match the manifest.")
        raw = yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
        registry = {str(name): [int(value) for value in values] for name, values in raw.items()}
        expected = set(default_seed_registry())
        if set(registry) != expected:
            raise RuntimeError(f"Frozen seed registry groups differ: expected={sorted(expected)}, got={sorted(registry)}")
        seen: set[int] = set()
        for name, values in registry.items():
            overlap = seen.intersection(values)
            if overlap:
                raise RuntimeError(f"Frozen seed registry overlap in {name}: {sorted(overlap)}")
            seen.update(values)

    confirmatory_groups = {
        "test_seeds_1_40",
        "extension_seeds_41_60",
        "extension_seeds_61_100",
        "generalization_seeds",
    }
    if allow_confirmatory:
        event_path = root / "protocol" / "confirmatory_seed_opening.json"
        if not event_path.exists():
            raise RuntimeError("Confirmatory seed registry is sealed until the opening event is recorded.")
        event = json.loads(event_path.read_text(encoding="utf-8"))
        if event.get("status") != "OPENED" or not event.get("confirmatory_seeds_opened"):
            raise RuntimeError("Confirmatory seed opening event is invalid.")
        if manifest_path is not None:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if event.get("seed_registry_sha256") != manifest.get("seed_registry_sha256"):
                raise RuntimeError("Confirmatory seed opening event does not match the frozen seed registry.")
        return registry
    return {name: values for name, values in registry.items() if name not in confirmatory_groups}
def record_confirmatory_seed_opening(
    root: Path,
    training_block: dict[str, Any],
    selection_validation: dict[str, Any],
) -> dict[str, Any]:
    """Write one immutable event before any confirmatory seed value is exposed."""

    protocol_dir = ensure_directory(root / "protocol")
    frozen_path = frozen_manifest_path(root)
    assert frozen_path is not None
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    immutable = {
        "status": "OPENED",
        "confirmatory_seeds_opened": True,
        "frozen_manifest_sha256": sha256_file(frozen_path),
        "seed_registry_sha256": frozen.get("seed_registry_sha256"),
        "b3_champions_sha256": sha256_file(root / "b3" / "champions.yaml"),
        "data_driven_champion_sha256": training_block.get("champion_sha256"),
        "model_selection_sha256": selection_validation.get("selection_sha256"),
        "confirmatory_seed_groups": [
            "test_seeds_1_40",
            "extension_seeds_41_60",
            "extension_seeds_61_100",
            "generalization_seeds",
        ],
        "test_results_not_used_for_selection": True,
    }
    event_path = protocol_dir / "confirmatory_seed_opening.json"
    if event_path.exists():
        existing = json.loads(event_path.read_text(encoding="utf-8"))
        mismatches = [key for key, value in immutable.items() if existing.get(key) != value]
        if mismatches:
            raise RuntimeError(f"Confirmatory seed opening event mismatch: {mismatches}")
        event = existing
    else:
        event = {
            **immutable,
            "opened_at_utc": datetime.now(UTC).isoformat(),
            "event_version": "SP0_CONFIRMATORY_SEED_OPENING_VERSIONED",
        }
        save_json(event_path, event)
    digest = sha256_file(event_path)
    digest_path = event_path.with_suffix(".sha256")
    digest_path.write_text(f"{digest}  {event_path.name}\n", encoding="utf-8")
    return {**event, "event_path": str(event_path), "event_sha256": digest}

def _require_frozen(root: Path) -> None:
    gate_path = root / "GATE_STATUS.json"
    if not gate_path.exists():
        raise RuntimeError("B0 gate status is missing; refusing to continue.")
    gates = json.loads(gate_path.read_text(encoding="utf-8"))["gates"]
    failed = {name: row for name, row in gates.items() if row.get("status") != "PASS"}
    if failed:
        raise RuntimeError(f"B0 gates are not all PASS: {failed}")
    manifest_path = frozen_manifest_path(root)
    assert manifest_path is not None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not bool(manifest.get("frozen")) or manifest.get("status") != "frozen_ready_for_execution":
        raise RuntimeError("Protocol is not frozen_ready_for_execution.")
    names = manifest.get("artifact_names", {})
    checks = {
        "config_sha256": root / "protocol" / str(names.get("protocol", "frozen_protocol.yaml")),
        "hypotheses_sha256": root / "protocol" / str(names.get("hypotheses", "hypotheses.yaml")),
        "seed_registry_sha256": root / "protocol" / str(names.get("seeds", "seed_registry.yaml")),
        "environment_lock_sha256": root / "protocol" / str(names.get("environment", "environment.lock")),
    }
    for field, path in checks.items():
        if not path.exists() or sha256_file(path) != manifest.get(field):
            raise RuntimeError(f"Frozen protocol integrity failure for {field}: {path}")
    implementation_path = Path(__file__).with_name("data_driven.py")
    expected_implementation = manifest.get("data_driven_implementation_sha256")
    if expected_implementation and sha256_file(implementation_path) != expected_implementation:
        raise RuntimeError("Data-driven implementation changed after protocol freeze.")
    expected_tree = manifest.get("sp0_implementation_sha256")
    if expected_tree and sha256_python_sources(Path(__file__).parent) != expected_tree:
        raise RuntimeError("SP0 implementation sources changed after protocol freeze.")


def run_b1_world_cache(config: dict[str, Any], root: Path, *, resume: bool) -> dict[str, Any]:
    worlds_dir = ensure_directory(root / "worlds")
    public_dir = ensure_directory(worlds_dir / "public")
    oracle_dir = ensure_directory(worlds_dir / "oracle")
    catalog_path = worlds_dir / "world_catalog.parquet"
    manifest_path = worlds_dir / "cache_manifest.json"
    expected_worlds = 60
    if resume:
        errors = validate_b1_cache(catalog_path, manifest_path, expected_worlds=expected_worlds, allow_additional=True)
        if not errors:
            cached_worlds = len(read_parquet(catalog_path))
            return {
                "status": "reused",
                "worlds": cached_worlds,
                "preconfirmatory_worlds": expected_worlds,
                "catalog": str(catalog_path),
                "cache_manifest": str(manifest_path),
                "cache_validated": True,
            }

    rows: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for world_spec in b1_preconfirmatory_world_specs(load_frozen_seed_registry(root, required=False)):
        world = make_sp0_world(**world_spec, sp_id=str(config.get("sp_id", "SP0-v1.1")))
        if world.world_hash in seen:
            continue
        seen.add(world.world_hash)
        public_path = public_dir / f"{world.world_hash}.npz"
        oracle_path = oracle_dir / f"{world.world_hash}.npz"
        laplacian = np.diag(np.sum(world.adjacency, axis=1).astype(float)) - world.adjacency.astype(float)
        np.savez_compressed(
            public_path,
            robot_xy=world.robot_xy,
            load_xy=world.load_xy,
            cost_matrix=world.cost,
            adjacency=world.adjacency.astype(np.int8),
            laplacian=laplacian,
            initial_population_state=world.initial_x,
        )
        np.savez_compressed(
            oracle_path,
            oracle_assignment=world.oracle_labels,
            oracle_cost=np.asarray(world.oracle_social_cost),
            oracle_j=np.asarray(world.oracle_j),
        )
        public_sha = sha256_file(public_path)
        oracle_sha = sha256_file(oracle_path)
        row = world_catalog_row(world, public_path, oracle_path)
        row.update({"public_sha256": public_sha, "oracle_sha256": oracle_sha})
        rows.append(row)
        entries.append(
            {
                "world_hash": world.world_hash,
                "public_path": str(public_path),
                "public_sha256": public_sha,
                "oracle_path": str(oracle_path),
                "oracle_sha256": oracle_sha,
            }
        )

    if len(rows) != expected_worlds:
        raise RuntimeError(f"B1 generated {len(rows)} unique worlds; expected {expected_worlds}")
    write_parquet(catalog_path, rows)
    cache_manifest = {
        "schema_version": "SP0_WORLD_CACHE_v1_1",
        "immutable_after_freeze": True,
        "oracle_namespace_separate": True,
        "world_count": len(rows),
        "entries": entries,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    save_json(manifest_path, cache_manifest)
    errors = validate_b1_cache(catalog_path, manifest_path, expected_worlds=expected_worlds)
    if errors:
        raise RuntimeError("B1 cache validation failed: " + "; ".join(errors))
    return {
        "status": "complete",
        "worlds": len(rows),
        "catalog": str(catalog_path),
        "cache_manifest": str(manifest_path),
        "cache_validated": True,
    }


def validate_b1_cache(
    catalog_path: Path,
    manifest_path: Path,
    *,
    expected_worlds: int,
    allow_additional: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not catalog_path.exists():
        return [f"missing catalog: {catalog_path}"]
    if not manifest_path.exists():
        return [f"missing cache manifest: {manifest_path}"]
    rows = read_parquet(catalog_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    count_invalid = len(rows) < expected_worlds if allow_additional else len(rows) != expected_worlds
    if count_invalid:
        relation = "at least" if allow_additional else "exactly"
        errors.append(f"catalog rows={len(rows)} expected {relation} {expected_worlds}")
    manifest_count = int(manifest.get("world_count", -1))
    if manifest_count != len(entries) or manifest_count != len(rows):
        errors.append("cache manifest/catalog world count mismatch")
    row_hashes = [str(row.get("world_hash")) for row in rows]
    entry_hashes = [str(entry.get("world_hash")) for entry in entries]
    if len(set(row_hashes)) != len(row_hashes):
        errors.append("duplicate world_hash in catalog")
    if set(row_hashes) != set(entry_hashes):
        errors.append("catalog and cache manifest world_hash sets differ")

    oracle_names = {"oracle_assignment", "oracle_cost", "oracle_j", "oracle_labels", "oracle_social_cost"}
    for entry in entries:
        public_path = Path(str(entry.get("public_path", "")))
        oracle_path = Path(str(entry.get("oracle_path", "")))
        if not public_path.exists() or not oracle_path.exists():
            errors.append(f"missing cache file for {entry.get('world_hash')}")
            continue
        if sha256_file(public_path) != entry.get("public_sha256"):
            errors.append(f"public hash mismatch for {entry.get('world_hash')}")
        if sha256_file(oracle_path) != entry.get("oracle_sha256"):
            errors.append(f"oracle hash mismatch for {entry.get('world_hash')}")
        with np.load(public_path, allow_pickle=False) as public_data:
            leaked = oracle_names.intersection(public_data.files)
            if leaked:
                errors.append(f"oracle fields in public cache for {entry.get('world_hash')}: {sorted(leaked)}")
        with np.load(oracle_path, allow_pickle=False) as oracle_data:
            missing = {"oracle_assignment", "oracle_cost", "oracle_j"}.difference(oracle_data.files)
            if missing:
                errors.append(f"oracle cache fields missing for {entry.get('world_hash')}: {sorted(missing)}")
    return errors

def append_worlds_to_cache(
    root: Path,
    worlds: list[SP0World],
    *,
    phase: str,
) -> dict[str, Any]:
    worlds_dir = ensure_directory(root / "worlds")
    public_dir = ensure_directory(worlds_dir / "public")
    oracle_dir = ensure_directory(worlds_dir / "oracle")
    catalog_path = worlds_dir / "world_catalog.parquet"
    manifest_path = worlds_dir / "cache_manifest.json"
    rows = read_parquet(catalog_path) if catalog_path.exists() else []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "schema_version": "SP0_WORLD_CACHE_v1_1",
        "immutable_after_freeze": True,
        "oracle_namespace_separate": True,
        "entries": [],
        "phases": [],
    }
    entries = list(manifest.get("entries", []))
    known = {str(entry.get("world_hash")) for entry in entries}
    added = 0
    for world in worlds:
        if world.world_hash in known:
            continue
        public_path = public_dir / f"{world.world_hash}.npz"
        oracle_path = oracle_dir / f"{world.world_hash}.npz"
        laplacian = np.diag(np.sum(world.adjacency, axis=1).astype(float)) - world.adjacency.astype(float)
        np.savez_compressed(
            public_path,
            robot_xy=world.robot_xy,
            load_xy=world.load_xy,
            cost_matrix=world.cost,
            adjacency=world.adjacency.astype(np.int8),
            laplacian=laplacian,
            initial_population_state=world.initial_x,
        )
        np.savez_compressed(
            oracle_path,
            oracle_assignment=world.oracle_labels,
            oracle_cost=np.asarray(world.oracle_social_cost),
            oracle_j=np.asarray(world.oracle_j),
        )
        public_sha = sha256_file(public_path)
        oracle_sha = sha256_file(oracle_path)
        row = world_catalog_row(world, public_path, oracle_path)
        row.update({"public_sha256": public_sha, "oracle_sha256": oracle_sha, "cache_phase": phase})
        rows.append(row)
        entries.append(
            {
                "world_hash": world.world_hash,
                "public_path": str(public_path),
                "public_sha256": public_sha,
                "oracle_path": str(oracle_path),
                "oracle_sha256": oracle_sha,
                "cache_phase": phase,
            }
        )
        known.add(world.world_hash)
        added += 1
    manifest.update(
        {
            "world_count": len(entries),
            "entries": entries,
            "phases": sorted(set(manifest.get("phases", [])) | {phase}),
            "updated_at_utc": datetime.now(UTC).isoformat(),
        }
    )
    write_parquet(catalog_path, rows)
    save_json(manifest_path, manifest)
    errors = validate_b1_cache(catalog_path, manifest_path, expected_worlds=len(entries))
    if errors:
        raise RuntimeError("Extended world cache validation failed: " + "; ".join(errors))
    return {
        "phase": phase,
        "added_worlds": added,
        "total_cached_worlds": len(entries),
        "catalog": str(catalog_path),
        "cache_manifest": str(manifest_path),
        "cache_validated": True,
    }


def materialize_confirmatory_worlds(
    config: dict[str, Any],
    root: Path,
) -> tuple[dict[str, list[tuple[SP0World, dict[str, Any]]]], dict[str, Any]]:
    registry = load_frozen_seed_registry(root, allow_confirmatory=True)
    by_key: dict[tuple[Any, ...], SP0World] = {}

    def get_world(n: int, k: int, seed: int, geometry: str, degree: int | str) -> SP0World:
        canonical_degree: int | str = "all" if degree == "all" or degree == n - 1 else int(degree)
        key = (n, k, seed, geometry, canonical_degree)
        if key not in by_key:
            by_key[key] = make_sp0_world(
                n_robots=n,
                n_loads=k,
                seed=seed,
                geometry_id=geometry,
                mean_degree_target=canonical_degree,
                sp_id=str(config.get("sp_id", "SP0-v1.1")),
            )
        return by_key[key]

    blocks: dict[str, list[tuple[SP0World, dict[str, Any]]]] = {"B4": [], "B5": [], "B6": [], "B7": []}
    for n in B4_SIZES:
        for ratio in REGIMES:
            for seed in registry["test_seeds_1_40"]:
                k = int(math.ceil(n * ratio))
                blocks["B4"].append((get_world(n, k, seed, "G-UNI", "all"), {"confirmatory_seed": seed}))
    for n in [32, 64]:
        for degree in [2, 4, 6, 10, n - 1]:
            for seed in registry["test_seeds_1_40"]:
                blocks["B5"].append(
                    (
                        get_world(n, n, seed, "G-UNI", degree),
                        {"confirmatory_seed": seed, "target_mean_degree": degree},
                    )
                )
    stress_types = ["G-TIE", "G-X", "G-CLU", "G-BIAS_G-ZERO"]
    for stress_id in stress_types:
        for offset, seed in enumerate(registry["test_seeds_1_40"][:20]):
            geometry = (
                "G-BIAS"
                if stress_id == "G-BIAS_G-ZERO" and offset % 2 == 0
                else "G-ZERO"
                if stress_id == "G-BIAS_G-ZERO"
                else stress_id
            )
            blocks["B6"].append(
                (
                    get_world(32, 32, seed, geometry, "all"),
                    {"confirmatory_seed": seed, "stress_type": stress_id},
                )
            )
    for n in [24, 48]:
        for seed in registry["generalization_seeds"]:
            blocks["B7"].append((get_world(n, n, seed, "G-UNI", "all"), {"generalization_seed": seed}))

    cache_status = append_worlds_to_cache(root, list(by_key.values()), phase="confirmatory_after_seed_opening")
    cache_status["block_world_counts"] = {block: len(values) for block, values in blocks.items()}
    cache_status["unique_worlds_in_memory"] = len(by_key)
    return blocks, cache_status


def b1_preconfirmatory_world_specs(seed_registry: dict[str, list[int]] | None = None) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    registry = seed_registry or default_seed_registry()
    for seed in registry["screening_seeds"]:
        for n in B2_SIZES:
            for ratio in REGIMES:
                specs.append({"n_robots": n, "n_loads": int(math.ceil(n * ratio)), "seed": seed, "geometry_id": "G-UNI", "mean_degree_target": "all"})
    for idx, world in enumerate(tuning_world_specs(30, seeds=registry["tuning_seeds"])):
        specs.append(world)
    return specs


def world_catalog_row(world: SP0World, public_path: Path, oracle_path: Path) -> dict[str, Any]:
    return {
        "sp_id": world.sp_id,
        "world_seed": world.world_seed,
        "N": world.n_robots,
        "K": world.n_loads,
        "load_ratio": world.load_ratio,
        "geometry_id": world.geometry_id,
        "R": world.radius,
        "mean_degree": world.mean_degree,
        "min_degree": world.min_degree,
        "lambda2": world.lambda2,
        "num_components": world.num_components,
        "diameter": world.diameter,
        "world_hash": world.world_hash,
        "public_cache_path": str(public_path),
        "oracle_namespace_path": str(oracle_path),
        "oracle_inaccessible_to_methods": True,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }


def run_b2_screening(config: dict[str, Any], root: Path, *, resume: bool) -> dict[str, Any]:
    b2_dir = ensure_directory(root / "b2")
    runs_path = b2_dir / "runs.parquet"
    if resume and runs_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B2", expected_runs=2400, config_hash=_config_hash(config))
        if not errors:
            return {"status": "reused", "runs": len(rows), "runs_path": str(runs_path), "resume_validated": True}
        preserve_invalid_resume(root, "B2", runs_path, errors)
    experiment_id = "SP0_B2_screening"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = []
    for seed in load_frozen_seed_registry(root)["screening_seeds"]:
        for n in B2_SIZES:
            for ratio in REGIMES:
                world = make_sp0_world(n_robots=n, n_loads=int(math.ceil(n * ratio)), seed=seed, geometry_id="G-UNI", mean_degree_target="all", sp_id=str(config.get("sp_id", "SP0-v1.0")))
                for dynamic in DYNAMICS:
                    for fitness in FITNESS:
                        for closure in B2_CLOSURES:
                            spec = {"id": dynamic, "fitness_id": fitness, "rounding_id": closure, "h": 0.1, "dt": 0.1, "max_steps": 100, "stable_window_steps": 10}
                            tasks.append((world, spec, experiment_id, "B2", config_hash, git_hash, timestamp, {"screening_seed": seed}))
    rows = execute_run_tasks_resumable(
        tasks, b2_dir / "resume" / "runs.parquet", resume=resume
    )
    write_validated_runs(runs_path, rows, block_id="B2", expected_runs=2400, config_hash=config_hash)
    summary = summarize_by(rows, ["dynamic_id", "fitness_id", "rounding_id"])
    write_parquet(b2_dir / "screening_summary.parquet", summary)
    elimination_log = build_screening_elimination_log(rows, timestamp=timestamp)
    write_parquet(b2_dir / "elimination_log.parquet", elimination_log)
    write_markdown_report(
        b2_dir / "report.md",
        "SP0 B2 Screening",
        len(rows),
        2400,
        {
            "summary_rows": len(summary),
            "kept": sum(row["decision"] == "KEEP" for row in elimination_log),
            "eliminated": sum(row["decision"] == "ELIMINATE" for row in elimination_log),
            "nonconvergent_closure_only": sum(row["decision"] == "NONCONVERGENT_CLOSURE_ONLY" for row in elimination_log),
        },
    )
    return {"status": "complete", "runs": len(rows), "expected_runs": 2400, "runs_path": str(runs_path)}


def run_b3_tuning(config: dict[str, Any], root: Path, *, resume: bool) -> dict[str, Any]:
    b3_dir = ensure_directory(root / "b3")
    runs_path = b3_dir / "runs.parquet"
    champions_path = b3_dir / "champions.yaml"
    if resume and runs_path.exists() and champions_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B3", expected_runs=1536, config_hash=_config_hash(config))
        digest_path = champions_path.with_suffix(".sha256")
        if not digest_path.exists() or sha256_file(champions_path) != digest_path.read_text(encoding="utf-8").split()[0]:
            errors.append("B3 champion hash missing or invalid")
        if not errors:
            return {"status": "reused", "runs": len(rows), "expected_runs": 1536, "champions": str(champions_path), "resume_validated": True}
        preserve_invalid_resume(root, "B3", runs_path, errors)
    all_rows: list[dict[str, Any]] = []
    history_rows: list[dict[str, Any]] = []
    champions: dict[str, dict[str, Any]] = {}
    experiment_id = "SP0_B3_tuning"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tuning_seeds = load_frozen_seed_registry(root)["tuning_seeds"]
    for family in DYNAMICS:
        configs = candidate_configs(family)[:12]
        round_specs = [(1, 6, 4), (2, 15, 2), (3, 30, 1)]
        active = configs
        for round_id, world_count, keep_count in round_specs:
            worlds = [make_sp0_world(**spec, sp_id=str(config.get("sp_id", "SP0-v1.1"))) for spec in tuning_world_specs(world_count, seeds=tuning_seeds)]
            tasks: list[RunTask] = []
            for cfg in active:
                for world in worlds:
                    tasks.append((
                        world,
                        cfg,
                        experiment_id,
                        "B3",
                        config_hash,
                        git_hash,
                        timestamp,
                        {"round": round_id, "config_id": cfg["config_id"], "family": family},
                    ))
            round_rows = execute_run_tasks_resumable(
                tasks,
                b3_dir / "resume" / f"{family}_round_{round_id}.parquet",
                resume=resume,
            )
            all_rows.extend(round_rows)
            scored = score_configs(round_rows)
            for rank, item in enumerate(scored, start=1):
                history_rows.append({"family": family, "round": round_id, "rank": rank, **item})
            if round_id < 3:
                keep_ids = {item["config_id"] for item in scored[:keep_count]}
                active = [cfg for cfg in active if cfg["config_id"] in keep_ids]
            else:
                best = scored[0]
                champion = next(cfg for cfg in active if cfg["config_id"] == best["config_id"])
                champions[family] = {**champion, "score": best["S_val"], "mean_normalized_regret": best["mean_normalized_regret"], "p_fail": best["p_fail"], "continuous_timeout_rate": best["continuous_timeout_rate"], "cvar95_normalized_regret": best["cvar95_normalized_regret"]}
    write_validated_runs(runs_path, all_rows, block_id="B3", expected_runs=1536, config_hash=config_hash)
    write_parquet(b3_dir / "tuning_history.parquet", history_rows)
    write_yaml(champions_path, champions)
    sha = sha256_file(champions_path)
    (b3_dir / "champions.sha256").write_text(f"{sha}  champions.yaml\n", encoding="utf-8")
    write_markdown_report(b3_dir / "report.md", "SP0 B3 Successive Halving", len(all_rows), 1536, {"champions": sorted(champions)})
    return {"status": "complete", "runs": len(all_rows), "expected_runs": 1536, "champions": str(champions_path), "champions_sha256": sha}


def candidate_configs(family: str) -> list[dict[str, Any]]:
    """Twelve deterministic, preregistered configurations per population family."""

    h_values = [0.01, 0.03, 0.05, 0.1]
    alpha_values = [0.25, 0.5, 1.0, 2.0]
    lambda_values = [0.5, 1.0, 2.0, 4.0]
    reward_values = [0.5, 1.0, 2.0]
    eta_values = [0.05, 0.1, 0.2, 0.5]
    beta_values = [1.0, 2.0, 5.0, 10.0]
    delta_x_values = [0.01, 0.05, 0.1]
    closures = ["REPAIR", "QR1", "QR2"]
    configs: list[dict[str, Any]] = []
    for index in range(12):
        configs.append(
            {
                "id": family,
                "dynamic_id": family,
                "fitness_id": FITNESS[index % len(FITNESS)],
                "rounding_id": closures[index % len(closures)],
                "h": h_values[index % len(h_values)],
                "dt": 0.1,
                "max_steps": 100,
                "stable_window_steps": 10,
                "alpha": alpha_values[index % len(alpha_values)],
                "lambda": lambda_values[(index * 3) % len(lambda_values)],
                "r": reward_values[index % len(reward_values)],
                "eta": eta_values[(index * 3) % len(eta_values)],
                "beta": beta_values[(index * 3) % len(beta_values)],
                "delta_x": delta_x_values[(index * 2) % len(delta_x_values)],
                "q": [1.0, 1.5, 2.0][index % 3],
                "kappa": [0.5, 1.0, 2.0][(index * 2) % 3],
                "alpha_BR": [0.1, 0.3, 0.5][index % 3],
                "dwell_time_s": [0.0, 0.2, 0.5, 1.0][index % 4],
                "delta_QR": [1.0e-4, 1.0e-3, 1.0e-2][index % 3],
                "max_swaps": [1, 5, 10][index % 3],
                "config_id": f"{family}_{index:02d}",
            }
        )
    return configs

def tuning_world_specs(count: int, *, seeds: list[int] | None = None) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    sizes = [8, 16, 32]
    geometries = ["G-UNI", "G-CLU", "G-X", "G-TIE", "G-BIAS"]
    for idx in range(count):
        n = sizes[idx % len(sizes)]
        ratio = REGIMES[(idx // len(sizes)) % len(REGIMES)]
        seed_values = seeds or default_seed_registry()["tuning_seeds"]
        specs.append({"n_robots": n, "n_loads": int(math.ceil(n * ratio)), "seed": int(seed_values[idx]), "geometry_id": geometries[idx % len(geometries)], "mean_degree_target": "all"})
    return specs


RunTask = tuple[
    SP0World,
    dict[str, Any],
    str,
    str,
    str,
    str,
    str,
    dict[str, Any] | None,
]


def execute_run_tasks(tasks: list[RunTask]) -> list[dict[str, Any]]:
    """Execute independent method/world rows with deterministic output order."""

    if not tasks:
        return []
    workers = max(1, int(os.environ.get("SP0_WORKERS", "1")))
    if workers == 1:
        return [_execute_run_task(task) for task in tasks]
    with ThreadPoolExecutor(max_workers=min(workers, len(tasks)), thread_name_prefix="sp0") as executor:
        return list(executor.map(_execute_run_task, tasks))


def _execute_run_task(task: RunTask) -> dict[str, Any]:
    world, spec, experiment_id, block_id, config_hash, git_hash, timestamp, extra = task
    return run_row(
        world,
        spec,
        experiment_id,
        block_id,
        config_hash,
        git_hash,
        timestamp,
        extra=extra,
    )

def execute_run_tasks_resumable(
    tasks: list[RunTask],
    checkpoint_path: Path,
    *,
    resume: bool,
) -> list[dict[str, Any]]:
    """Checkpoint task rows in stable chunks and resume without duplicate runs."""

    prepared: list[RunTask] = []
    tokens: list[str] = []
    for task in tasks:
        token = run_task_token(task)
        world, spec, experiment_id, block_id, config_hash, git_hash, timestamp, extra = task
        prepared.append((
            world,
            spec,
            experiment_id,
            block_id,
            config_hash,
            git_hash,
            timestamp,
            {**(extra or {}), "task_token": token},
        ))
        tokens.append(token)
    if len(tokens) != len(set(tokens)):
        raise RuntimeError("SP0 task plan contains duplicate task tokens")

    completed: dict[str, dict[str, Any]] = {}
    if checkpoint_path.exists():
        checkpoint_rows = read_parquet(checkpoint_path)
        valid = (
            resume
            and all(row.get("task_token") for row in checkpoint_rows)
            and len({row.get("task_token") for row in checkpoint_rows}) == len(checkpoint_rows)
            and all(str(row.get("task_token")) in set(tokens) for row in checkpoint_rows)
        )
        if valid:
            completed = {str(row["task_token"]): row for row in checkpoint_rows}
        else:
            archive = ensure_directory(checkpoint_path.parent / "archive")
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            checkpoint_path.replace(archive / f"{checkpoint_path.stem}_{stamp}{checkpoint_path.suffix}")

    pending = [task for task, token in zip(prepared, tokens) if token not in completed]
    workers = max(1, int(os.environ.get("SP0_WORKERS", "1")))
    chunk_size = max(1, int(os.environ.get("SP0_RESUME_CHUNK_SIZE", str(workers * 4))))
    for start in range(0, len(pending), chunk_size):
        for row in execute_run_tasks(pending[start : start + chunk_size]):
            completed[str(row["task_token"])] = row
        ordered_partial = [completed[token] for token in tokens if token in completed]
        write_parquet(checkpoint_path, ordered_partial)

    missing = [token for token in tokens if token not in completed]
    if missing:
        raise RuntimeError(f"SP0 resumable execution is missing {len(missing)} task rows")
    return [completed[token] for token in tokens]


def run_task_token(task: RunTask) -> str:
    world, spec, experiment_id, block_id, config_hash, git_hash, _timestamp, extra = task
    payload = {
        "world_hash": world.world_hash,
        "spec": spec,
        "experiment_id": experiment_id,
        "block_id": block_id,
        "config_hash": config_hash,
        "git_hash": git_hash,
        "extra": extra or {},
    }
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
def run_row(
    world: SP0World,
    spec: dict[str, Any],
    experiment_id: str,
    block_id: str,
    config_hash: str,
    git_hash: str,
    timestamp: str,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = base_row(world, spec, experiment_id, block_id, config_hash, git_hash, timestamp)
    started = perf_counter()
    try:
        effective_spec = dict(spec)
        if os.environ.get("SP0_AUDIT_TRAJECTORY_ROOT") and block_id in {"DRY", "B2", "B3", "B4", "B5", "B6", "B7"}:
            effective_spec["record_trajectory"] = True
        method_id = str(effective_spec.get("id", "")).upper()
        method_world = world if method_id in {"HUN", "HUNGARIAN"} else public_world_view(world)
        result = run_sp0_method(method_world, effective_spec)
        metrics = evaluate_sp0_result(world, result)
        simplex_error = (
            float(np.max(np.abs(np.sum(result.continuous_x, axis=1) - 1.0)))
            if result.continuous_x is not None
            else 0.0
        )
        min_probability = (
            float(np.min(result.continuous_x))
            if result.continuous_x is not None
            else 0.0
        )
        trajectory_path, trajectory_sha256 = persist_result_trajectory(
            world,
            result,
            block_id=block_id,
            experiment_id=experiment_id,
            spec=effective_spec,
        )
        row = {
            **base,
            "method_family": result.method_family,
            "method_variant": result.method_id,
            "method": result.method_id,
            "architecture": result.architecture,
            "dynamic_id": result.dynamic_id,
            "fitness_id": result.fitness_id,
            "rounding_id": result.rounding_id,
            "method_seed": result.method_seed,
            "train_seed": result.train_seed,
            "training_steps": result.training_steps,
            "training_converged": result.training_converged,
            "trajectory_path": trajectory_path,
            "trajectory_sha256": trajectory_sha256,
            "simplex_max_error": simplex_error,
            "min_probability": min_probability,
            "simplex_violation": bool(simplex_error > 1.0e-6 or min_probability < -1.0e-9),
            "nan_or_inf": bool(
                not np.isfinite(metrics.runtime_wall_s)
                or not np.isfinite(metrics.normalized_regret)
            ),
            "error_type": None,
            "error_message": None,
            **metrics.to_dict(),
        }
    except Exception as exc:
        timed_out = isinstance(exc, TimeoutError)
        row = {
            **base,
            "method_family": "error",
            "method_variant": str(spec.get("id")),
            "method": str(spec.get("id")),
            "architecture": spec.get("architecture"),
            "dynamic_id": spec.get("dynamic_id", spec.get("id")),
            "fitness_id": spec.get("fitness_id"),
            "rounding_id": spec.get("rounding_id"),
            "method_seed": spec.get("method_seed"),
            "train_seed": spec.get("train_seed"),
            "training_steps": spec.get("training_steps"),
            "training_converged": spec.get("training_converged"),
            "trajectory_path": None,
            "trajectory_sha256": None,
            "continuous_converged": False if timed_out else None,
            "continuous_timeout": True if timed_out else None,
            "continuous_equilibrium_reached": False if timed_out else None,
            "closure_applied": None,
            "closure_type": spec.get("rounding_id"),
            "closure_success": None,
            "matching_valid": False,
            "maximum_cardinality": False,
            "final_success": False,
            "success": False,
            "coverage": None,
            "assigned_count": None,
            "social_cost": None,
            "social_regret": None,
            "normalized_regret": None,
            "continuous_objective": None,
            "continuous_normalized_regret": None,
            "preclosure_matching_valid": None,
            "preclosure_coverage": None,
            "preclosure_objective": None,
            "preclosure_normalized_regret": None,
            "closure_regret_delta": None,
            "closure_vs_preclosure_regret_delta": None,
            "final_vs_continuous_regret_delta": None,
            "cost_gap": None,
            "makespan_proxy": None,
            "p95_individual_cost": None,
            "convergence_time": None,
            "time_to_epsilon_solution": None,
            "time_to_epsilon_duration_s": None,
            "time_to_epsilon_observed": False,
            "messages_to_epsilon_solution": None,
            "bytes_to_epsilon_solution": None,
            "timeout": timed_out,
            "messages": None,
            "bytes": None,
            "runtime_cpu_s": None,
            "runtime_wall_s": perf_counter() - started,
            "oracle_solve_time_s": None,
            "oracle_lookup_time_s": None,
            "method_online_time_s": None,
            "closure_runtime_s": None,
            "memory_peak": None,
            "epsilon_ne_1": None,
            "epsilon_ne_2": None,
            "fractionality": None,
            "switches": None,
            "potential_violations": None,
            "occupancy_error": None,
            "state_change": None,
            "equilibrium_residual": None,
            "equilibrium_residual_id": None,
            "simulation_end_time_s": None,
            "closure_messages": None,
            "global_strong_closure": None,
            "largest_negative_delta": None,
            "median_potential_delta": None,
            "p01_potential_delta": None,
            "observed_poa_ratio": None,
            "price_of_integrality": None,
            "simplex_max_error": None,
            "min_probability": None,
            "simplex_violation": None,
            "nan_or_inf": None,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }
    if extra:
        row.update(extra)
    return row

def persist_result_trajectory(
    world: SP0World,
    result: Any,
    *,
    block_id: str,
    experiment_id: str,
    spec: dict[str, Any],
) -> tuple[str | None, str | None]:
    root_value = os.environ.get("SP0_AUDIT_TRAJECTORY_ROOT")
    if not root_value or block_id not in {"DRY", "B2", "B3", "B4", "B5", "B6", "B7"}:
        return None, None
    root = ensure_directory(Path(root_value) / block_id.lower())
    identity = {
        "experiment_id": experiment_id,
        "block_id": block_id,
        "method": result.method_id,
        "dynamic_id": result.dynamic_id,
        "fitness_id": result.fitness_id,
        "rounding_id": result.rounding_id,
        "config_id": spec.get("config_id"),
        "world_hash": world.world_hash,
        "train_seed": result.train_seed,
        "method_seed": result.method_seed,
    }
    token = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()[:24]
    path = root / f"{token}.npz"
    trajectory = result.trajectory or {
        "time_s": np.asarray([0.0], dtype=np.float32),
        "potential": np.asarray([math.nan], dtype=np.float32),
        "equilibrium_residual": np.asarray([math.nan], dtype=np.float32),
        "fractionality": np.asarray([float(result.fractionality)], dtype=np.float32),
        "switches": np.asarray([int(result.switches)], dtype=np.int32),
        "state_change": np.asarray([math.nan], dtype=np.float32),
        "occupancy_error": np.asarray([float(result.occupancy_error)], dtype=np.float32),
        "argmax_labels": np.asarray(result.labels, dtype=np.int16)[None, :],
        "final_labels": np.asarray(result.labels, dtype=np.int16),
    }
    payload = {
        **trajectory,
        "robot_xy": np.asarray(world.robot_xy, dtype=np.float32),
        "load_xy": np.asarray(world.load_xy, dtype=np.float32),
        "adjacency": np.asarray(world.adjacency, dtype=np.int8),
        "cost_matrix": np.asarray(world.cost, dtype=np.float32),
        "oracle_j_posthoc": np.asarray(world.oracle_j, dtype=np.float64),
        "s_star": np.asarray(world.s_star, dtype=np.int32),
        "world_seed": np.asarray(world.world_seed, dtype=np.int64),
        "lambda2": np.asarray(world.lambda2, dtype=np.float64),
        "num_components": np.asarray(world.num_components, dtype=np.int32),
        "messages_total": np.asarray(result.messages, dtype=np.int64),
        "closure_messages": np.asarray(result.closure_messages, dtype=np.int64),
        "iterations": np.asarray(result.iterations, dtype=np.int32),
        "simulation_end_time_s": np.asarray(
            0.0 if result.simulation_end_time_s is None else result.simulation_end_time_s,
            dtype=np.float64,
        ),
        "closure_type": np.asarray(result.closure_type or result.rounding_id or "none"),
        "world_hash": np.asarray(world.world_hash),
        "method_variant": np.asarray(result.method_id),
        "train_seed": np.asarray(-1 if result.train_seed is None else result.train_seed, dtype=np.int64),
        "continuous_converged": np.asarray(
            -1 if result.continuous_converged is None else int(result.continuous_converged),
            dtype=np.int8,
        ),
        "continuous_timeout": np.asarray(
            -1 if result.continuous_timeout is None else int(result.continuous_timeout),
            dtype=np.int8,
        ),
    }
    np.savez_compressed(path, **payload)
    return str(path), sha256_file(path)


def is_data_driven_spec(spec: dict[str, Any]) -> bool:
    method_id = str(spec.get("id", "")).upper()
    return method_id.startswith("IPPO") or method_id.startswith("MAPPO")


def run_data_driven_checkpoint(world: SP0World, spec: dict[str, Any]):
    if not spec.get("requires_real_checkpoint"):
        raise RuntimeError("Data-driven confirmatory run requires a real checkpoint; proxy execution is forbidden")
    module_name = spec.get("executor_module")
    function_name = spec.get("executor_function")
    if not module_name or not function_name:
        raise RuntimeError("Data-driven executor module/function missing")
    module = __import__(str(module_name), fromlist=[str(function_name)])
    fn = getattr(module, str(function_name))
    try:
        result = fn(world=world, spec=spec)
    except TypeError:
        result = fn(world, spec)
    if hasattr(result, "labels") and hasattr(result, "method_id"):
        return result
    from viu_mrob_tfm.sp0.methods import SP0MethodResult

    labels = np.asarray(result.get("labels") if isinstance(result, dict) else result, dtype=int)
    if not assignment_valid(labels, world.n_loads):
        raise RuntimeError("Data-driven executor returned an invalid assignment")
    messages = int(result.get("messages", 0)) if isinstance(result, dict) else 0
    runtime_ms = float(result.get("runtime_ms", 0.0)) if isinstance(result, dict) else 0.0
    return SP0MethodResult(
        method_id=str(spec.get("id")),
        method_family="data_driven",
        architecture="distributed_local",
        dynamic_id=None,
        fitness_id=None,
        rounding_id="POLICY",
        labels=labels,
        continuous_x=None,
        runtime_ms=runtime_ms,
        convergence_time=0.0,
        iterations=1,
        timeout=False,
        messages=messages,
        bytes_sent=int(result.get("bytes", messages * 32)) if isinstance(result, dict) else messages * 32,
        fractionality=0.0,
        entropy=0.0,
        switches=0,
        potential_violations=0,
        occupancy_error=math.nan,
        training_steps=int(spec.get("training_steps", 0) or 0),
        training_converged=bool(spec.get("training_converged", False)),
        train_seed=int(spec.get("train_seed")),
        method_online_time_ms=runtime_ms,
    )
def base_row(world: SP0World, spec: dict[str, Any], experiment_id: str, block_id: str, config_hash: str, git_hash: str, timestamp: str) -> dict[str, Any]:
    return {
        "sp_id": world.sp_id,
        "experiment_id": experiment_id,
        "block_id": block_id,
        "world_seed": world.world_seed,
        "N": world.n_robots,
        "K": world.n_loads,
        "load_ratio": world.load_ratio,
        "geometry_id": world.geometry_id,
        "R": world.radius,
        "mean_degree": world.mean_degree,
        "min_degree": world.min_degree,
        "lambda2": world.lambda2,
        "num_components": world.num_components,
        "world_hash": world.world_hash,
        "oracle_j": world.oracle_j,
        "oracle_social_cost": world.oracle_social_cost,
        "config_hash": config_hash,
        "git_hash": git_hash,
        "timestamp_utc": timestamp,
        "config_id": spec.get("config_id"),
    }


def score_configs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("config_id")), []).append(row)
    scored: list[dict[str, Any]] = []
    for config_id, selected in grouped.items():
        regrets = np.asarray([float(row.get("normalized_regret") if row.get("normalized_regret") is not None else 1.0) for row in selected], dtype=float)
        fail = np.asarray(
            [
                row.get("error_type") is not None
                or not bool(row.get("final_success"))
                or not bool(row.get("matching_valid"))
                for row in selected
            ],
            dtype=bool,
        )
        continuous_timeout_rate = float(np.mean([bool(row.get("continuous_timeout")) for row in selected]))
        cvar = cvar95(regrets)
        mean_nr = float(np.mean(regrets))
        p_fail = float(np.mean(fail))
        runtime = float(np.nanmean([float(row.get("runtime_wall_s") or math.nan) for row in selected]))
        s_val = mean_nr + p_fail + 0.25 * cvar
        scored.append({"config_id": config_id, "S_val": s_val, "mean_normalized_regret": mean_nr, "p_fail": p_fail, "continuous_timeout_rate": continuous_timeout_rate, "cvar95_normalized_regret": cvar, "runtime_wall_mean": runtime, "n_worlds": len(selected)})
    return sorted(scored, key=lambda item: (item["S_val"], item["cvar95_normalized_regret"], item["continuous_timeout_rate"], item["runtime_wall_mean"], item["config_id"]))


def cvar95(values: np.ndarray) -> float:
    if values.size == 0:
        return math.nan
    threshold = float(np.quantile(values, 0.95))
    tail = values[values >= threshold]
    return float(np.mean(tail if tail.size else values))


def summarize_by(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row.get(key) for key in keys), []).append(row)
    output: list[dict[str, Any]] = []
    for key_values, selected in grouped.items():
        item = {key: value for key, value in zip(keys, key_values)}
        success_values = [bool(row["final_success"]) for row in selected if row.get("final_success") is not None]
        validity_values = [bool(row["matching_valid"]) for row in selected if row.get("matching_valid") is not None]
        regret_values = [float(row["normalized_regret"]) for row in selected if row.get("normalized_regret") is not None]
        runtime_values = [float(row["runtime_wall_s"]) for row in selected if row.get("runtime_wall_s") is not None]
        item.update({
            "n": len(selected),
            "n_discrete_applicable": len(success_values),
            "success_rate": float(np.mean(success_values)) if success_values else math.nan,
            "invalid_rate": float(np.mean([not value for value in validity_values])) if validity_values else math.nan,
            "timeout_rate": float(np.mean([bool(row.get("continuous_timeout")) for row in selected])),
            "mean_normalized_regret": float(np.mean(regret_values)) if regret_values else math.nan,
            "mean_runtime_wall_s": float(np.mean(runtime_values)) if runtime_values else math.nan,
        })
        output.append(item)
    return output


def build_screening_elimination_log(rows: list[dict[str, Any]], *, timestamp: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("dynamic_id")), str(row.get("fitness_id")), str(row.get("rounding_id")))
        grouped.setdefault(key, []).append(row)

    diagnostics: dict[tuple[str, str, str], dict[str, Any]] = {}
    for key, selected in grouped.items():
        closure = key[2]
        regrets = np.asarray(
            [float(row["normalized_regret"]) for row in selected if row.get("normalized_regret") is not None],
            dtype=float,
        )
        runtimes = np.asarray(
            [float(row["runtime_wall_s"]) for row in selected if row.get("runtime_wall_s") is not None],
            dtype=float,
        )
        applicable_success = [bool(row["final_success"]) for row in selected if row.get("final_success") is not None]
        diagnostics[key] = {
            "timeout_rate": float(np.mean([bool(row.get("continuous_timeout")) for row in selected])),
            "invalid_rate": (
                float(np.mean([not bool(row.get("matching_valid")) for row in selected]))
                if closure != "RAW"
                else math.nan
            ),
            "failure_rate": (
                float(np.mean([not value for value in applicable_success]))
                if applicable_success
                else math.nan
            ),
            "error_rate": float(np.mean([row.get("error_type") is not None for row in selected])),
            "simplex_violation_rate": float(np.mean([bool(row.get("simplex_violation")) for row in selected])),
            "nan_or_inf_rate": float(np.mean([bool(row.get("nan_or_inf")) for row in selected])),
            "mean_normalized_regret": float(np.mean(regrets)) if regrets.size else math.inf,
            "p95_runtime_wall_s": float(np.quantile(runtimes, 0.95)) if runtimes.size else math.inf,
            "n": len(selected),
        }

    dominated_by: dict[tuple[str, str, str], str] = {}
    for key, item in diagnostics.items():
        for other_key, other in diagnostics.items():
            if key == other_key or key[2] != other_key[2]:
                continue
            item_vector = (
                item["mean_normalized_regret"],
                item["timeout_rate"],
                item["p95_runtime_wall_s"],
            )
            other_vector = (
                other["mean_normalized_regret"],
                other["timeout_rate"],
                other["p95_runtime_wall_s"],
            )
            weakly_better = all(a <= b + 1.0e-12 for a, b in zip(other_vector, item_vector))
            strictly_better = any(a < b - 1.0e-6 for a, b in zip(other_vector, item_vector))
            if weakly_better and strictly_better:
                dominated_by[key] = "/".join(other_key)
                break

    output: list[dict[str, Any]] = []
    for key, item in sorted(diagnostics.items()):
        fatal_reasons: list[str] = []
        diagnostic_reasons: list[str] = []
        if item["timeout_rate"] > 0.20:
            diagnostic_reasons.append("continuous_timeout_rate_gt_0.20")
        if item["error_rate"] > 0.0:
            fatal_reasons.append("execution_error")
        if item["simplex_violation_rate"] > 0.0:
            fatal_reasons.append("simplex_violation")
        if item["nan_or_inf_rate"] > 0.0:
            fatal_reasons.append("nan_or_inf")
        if key[2] != "RAW" and item["invalid_rate"] > 0.0:
            fatal_reasons.append("invalid_matching_after_QR1")
        if item["p95_runtime_wall_s"] > 10.0:
            fatal_reasons.append("runtime_incompatible_with_budget")
        if key in dominated_by:
            fatal_reasons.append("clear_pareto_domination")
        decision = (
            "ELIMINATE"
            if fatal_reasons
            else "NONCONVERGENT_CLOSURE_ONLY"
            if diagnostic_reasons
            else "KEEP"
        )
        output.append(
            {
                "dynamic_id": key[0],
                "fitness_id": key[1],
                "rounding_id": key[2],
                "config_id": "/".join(key),
                "decision": decision,
                "fatal_reasons": fatal_reasons,
                "diagnostic_reasons": diagnostic_reasons,
                "reasons": fatal_reasons + diagnostic_reasons,
                "dominated_by": dominated_by.get(key),
                "negative_control_rule_applicable": False,
                "negative_control_note": "DIST is outside the fixed 2400-run B2 factorial; no hidden extra runs are used.",
                **item,
                "timestamp_utc": timestamp,
            }
        )
    return output


def run_model_selection_validation(config: dict[str, Any], root: Path, *, resume: bool) -> dict[str, Any]:
    """Select B5/B7 units using validation seeds before confirmatory seed opening."""

    b3_dir = ensure_directory(root / "b3")
    runs_path = b3_dir / "model_selection_validation.parquet"
    selection_path = b3_dir / "model_selection_champions.yaml"
    digest_path = b3_dir / "model_selection_champions.sha256"
    expected_runs = 96
    if resume and runs_path.exists() and selection_path.exists() and digest_path.exists():
        rows = read_parquet(runs_path)
        expected_digest = digest_path.read_text(encoding="utf-8").split()[0]
        if (
            len(rows) == expected_runs
            and sha256_file(selection_path) == expected_digest
            and len({(row.get("selection_id"), row.get("world_hash")) for row in rows}) == expected_runs
        ):
            return {
                "status": "reused",
                "runs": expected_runs,
                "included_in_base_15436": False,
                "selection_path": str(selection_path),
                "selection_sha256": expected_digest,
                "resume_validated": True,
            }

    champions = load_b3_champions(root)
    candidates: list[dict[str, Any]] = [
        {"id": "GRD", "architecture": "distributed_local", "selection_id": "GRD"},
        {"id": "DA", "architecture": "distributed_local", "selection_id": "EPS-AUCTION"},
    ]
    for family in ["REP", "SMI", "BNN", "LOG", "PROJ", "HYB"]:
        candidate = {**champions[family], "architecture": "distributed_local", "selection_id": family}
        candidates.append(candidate)
    registry = load_frozen_seed_registry(root)
    validation_seeds = registry["validation_seeds"][:2]
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = []
    for seed in validation_seeds:
        for n in [16, 32]:
            for degree in [2, 6, n - 1]:
                world = make_sp0_world(
                    n_robots=n,
                    n_loads=n,
                    seed=seed,
                    geometry_id="G-UNI",
                    mean_degree_target=degree,
                    sp_id=str(config.get("sp_id", "SP0-v1.1")),
                )
                for candidate in candidates:
                    tasks.append((
                        world,
                        candidate,
                        "SP0_model_selection_validation",
                        "SEL",
                        config_hash,
                        git_hash,
                        timestamp,
                        {
                            "selection_id": candidate["selection_id"],
                            "selection_only": True,
                            "included_in_base_15436": False,
                        },
                    ))
    rows = execute_run_tasks_resumable(
        tasks, b3_dir / "resume" / "model_selection.parquet", resume=resume
    )
    if len(rows) != expected_runs:
        raise RuntimeError(f"model selection validation rows={len(rows)} expected={expected_runs}")
    if len({(row.get("selection_id"), row.get("world_hash")) for row in rows}) != expected_runs:
        raise RuntimeError("model selection validation contains duplicate candidate/world rows")

    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        selected = [row for row in rows if row.get("selection_id") == candidate["selection_id"]]
        regrets = np.asarray(
            [float(row["normalized_regret"]) if row.get("normalized_regret") is not None else 1.0 for row in selected],
            dtype=float,
        )
        failures = np.asarray(
            [row.get("error_type") is not None or not bool(row.get("final_success")) for row in selected],
            dtype=bool,
        )
        runtimes = np.asarray(
            [float(row["runtime_wall_s"]) if row.get("runtime_wall_s") is not None else math.inf for row in selected],
            dtype=float,
        )
        score = float(np.mean(regrets) + np.mean(failures) + 0.25 * cvar95(regrets))
        scored.append(
            {
                "selection_id": candidate["selection_id"],
                "spec": {key: value for key, value in candidate.items() if key != "selection_id"},
                "S_val": score,
                "mean_NR": float(np.mean(regrets)),
                "p_fail": float(np.mean(failures)),
                "CVaR95_NR": cvar95(regrets),
                "mean_runtime_wall_s": float(np.mean(runtimes)),
            }
        )
    ranked = sorted(
        scored,
        key=lambda row: (row["S_val"], row["CVaR95_NR"], row["mean_runtime_wall_s"], row["selection_id"]),
    )
    population_ids = {"REP", "SMI", "BNN", "LOG", "PROJ", "HYB"}
    top5_population = [row for row in ranked if row["selection_id"] in population_ids][:5]
    top3_model_based = ranked[:3]
    selection = {
        "selection_rule": "validation_only_S_val_then_CVaR_then_runtime",
        "validation_seed_count": len(validation_seeds),
        "validation_worlds": 12,
        "evaluations": expected_runs,
        "included_in_base_15436": False,
        "ranked_candidates": ranked,
        "B5_top5_local_population": top5_population,
        "B7_top3_distributed_model_based": top3_model_based,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    write_parquet(runs_path, rows)
    write_yaml(selection_path, selection)
    digest = sha256_file(selection_path)
    digest_path.write_text(f"{digest}  {selection_path.name}\n", encoding="utf-8")
    return {
        "status": "complete",
        "runs": expected_runs,
        "included_in_base_15436": False,
        "selection_path": str(selection_path),
        "selection_sha256": digest,
    }


def load_model_selection(root: Path) -> dict[str, Any]:
    path = root / "b3" / "model_selection_champions.yaml"
    digest_path = root / "b3" / "model_selection_champions.sha256"
    if not path.exists() or not digest_path.exists():
        raise RuntimeError("Preconfirmatory model selection artifacts are missing")
    expected = digest_path.read_text(encoding="utf-8").split()[0]
    if sha256_file(path) != expected:
        raise RuntimeError("Model selection champions changed after validation")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_b4_confirmatory(
    config: dict[str, Any],
    root: Path,
    training_status: dict[str, Any],
    *,
    worlds: list[tuple[SP0World, dict[str, Any]]],
    resume: bool,
) -> dict[str, Any]:
    out_dir = ensure_directory(root / "b4")
    runs_path = out_dir / "runs.parquet"
    if resume and runs_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B4", expected_runs=5760, config_hash=_config_hash(config))
        if not errors:
            return {"status": "reused", "runs": len(rows), "expected_runs": 5760, "runs_path": str(runs_path), "resume_validated": True}
        preserve_invalid_resume(root, "B4", runs_path, errors)
    units = b4_units(root, training_status)
    experiment_id = "SP0_B4_confirmatory"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = [
        (world, unit, experiment_id, "B4", config_hash, git_hash, timestamp, extra)
        for unit in units
        for world, extra in worlds
    ]
    rows = execute_run_tasks_resumable(
        tasks, out_dir / "resume" / "runs.parquet", resume=resume
    )
    write_validated_runs(runs_path, rows, block_id="B4", expected_runs=5760, config_hash=config_hash)
    write_parquet(out_dir / "primary_metrics.parquet", summarize_by(rows, ["method_variant", "N", "K"]))
    write_empty_parquet(out_dir / "pairwise_differences.parquet", ["contrast", "metric", "effect", "ci_low", "ci_high", "p_value", "holm_p"])
    write_markdown_report(out_dir / "report.md", "SP0 B4 Confirmatory", len(rows), 5760, {"units": [unit.get("id") for unit in units]})
    return {"status": "complete", "runs": len(rows), "expected_runs": 5760, "runs_path": str(runs_path)}


def run_b5_communication(
    config: dict[str, Any],
    root: Path,
    training_status: dict[str, Any],
    *,
    worlds: list[tuple[SP0World, dict[str, Any]]],
    resume: bool,
) -> dict[str, Any]:
    out_dir = ensure_directory(root / "b5")
    runs_path = out_dir / "runs.parquet"
    if resume and runs_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B5", expected_runs=4000, config_hash=_config_hash(config))
        if not errors:
            return {"status": "reused", "runs": len(rows), "expected_runs": 4000, "runs_path": str(runs_path), "resume_validated": True}
        preserve_invalid_resume(root, "B5", runs_path, errors)
    units = b5_units(root, training_status)
    experiment_id = "SP0_B5_communication"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = [
        (world, unit, experiment_id, "B5", config_hash, git_hash, timestamp, extra)
        for unit in units
        for world, extra in worlds
    ]
    rows = execute_run_tasks_resumable(
        tasks, out_dir / "resume" / "runs.parquet", resume=resume
    )
    write_validated_runs(runs_path, rows, block_id="B5", expected_runs=4000, config_hash=config_hash)
    write_markdown_report(out_dir / "report.md", "SP0 B5 Communication Sweep", len(rows), 4000, {"units": [unit.get("id") for unit in units]})
    return {"status": "complete", "runs": len(rows), "expected_runs": 4000, "runs_path": str(runs_path)}


def run_b6_stress(
    config: dict[str, Any],
    root: Path,
    training_status: dict[str, Any],
    *,
    worlds: list[tuple[SP0World, dict[str, Any]]],
    resume: bool,
) -> dict[str, Any]:
    out_dir = ensure_directory(root / "b6")
    runs_path = out_dir / "runs.parquet"
    if resume and runs_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B6", expected_runs=960, config_hash=_config_hash(config))
        if not errors:
            return {"status": "reused", "runs": len(rows), "expected_runs": 960, "runs_path": str(runs_path), "resume_validated": True}
        preserve_invalid_resume(root, "B6", runs_path, errors)
    units = b4_units(root, training_status)
    stress = ["G-TIE", "G-X", "G-CLU", "G-BIAS_G-ZERO"]
    experiment_id = "SP0_B6_stress"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = [
        (world, unit, experiment_id, "B6", config_hash, git_hash, timestamp, extra)
        for unit in units
        for world, extra in worlds
    ]
    rows = execute_run_tasks_resumable(
        tasks, out_dir / "resume" / "runs.parquet", resume=resume
    )
    write_validated_runs(runs_path, rows, block_id="B6", expected_runs=960, config_hash=config_hash)
    write_markdown_report(out_dir / "report.md", "SP0 B6 Stress Tests", len(rows), 960, {"stress_types": stress})
    return {"status": "complete", "runs": len(rows), "expected_runs": 960, "runs_path": str(runs_path)}


def run_b7_generalization(
    config: dict[str, Any],
    root: Path,
    training_status: dict[str, Any],
    *,
    worlds: list[tuple[SP0World, dict[str, Any]]],
    resume: bool,
) -> dict[str, Any]:
    out_dir = ensure_directory(root / "b7")
    runs_path = out_dir / "runs.parquet"
    if resume and runs_path.exists():
        rows = read_parquet(runs_path)
        errors = validate_completed_block(rows, block_id="B7", expected_runs=480, config_hash=_config_hash(config))
        if not errors:
            return {"status": "reused", "runs": len(rows), "expected_runs": 480, "runs_path": str(runs_path), "resume_validated": True}
        preserve_invalid_resume(root, "B7", runs_path, errors)
    units = b7_units(root, training_status)
    experiment_id = "SP0_B7_generalization"
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = [
        (world, unit, experiment_id, "B7", config_hash, git_hash, timestamp, extra)
        for unit in units
        for world, extra in worlds
    ]
    rows = execute_run_tasks_resumable(
        tasks, out_dir / "resume" / "runs.parquet", resume=resume
    )
    write_validated_runs(runs_path, rows, block_id="B7", expected_runs=480, config_hash=config_hash)
    write_markdown_report(out_dir / "report.md", "SP0 B7 Generalization", len(rows), 480, {"units": [unit.get("id") for unit in units]})
    return {"status": "complete", "runs": len(rows), "expected_runs": 480, "runs_path": str(runs_path)}


def b4_units(root: Path, training_status: dict[str, Any]) -> list[dict[str, Any]]:
    champions = load_b3_champions(root)
    units = [{"id": "HUN"}, {"id": "GRD"}, {"id": "DA"}]
    for family in ["REP", "SMI", "BNN", "LOG", "PROJ", "HYB"]:
        units.append(champions[family])
    units.extend(data_driven_seed_specs(training_status))
    if len(units) != 12:
        raise RuntimeError(f"B4 requires 12 units, got {len(units)}")
    return units


def b5_units(root: Path, training_status: dict[str, Any]) -> list[dict[str, Any]]:
    selection = load_model_selection(root)
    population = [
        dict(row["spec"])
        for row in selection.get("B5_top5_local_population", [])
    ]
    units = [
        {"id": "GRD", "architecture": "distributed_local"},
        {"id": "DA", "architecture": "distributed_local"},
    ] + population + data_driven_seed_specs(training_status)
    if len(units) != 10:
        raise RuntimeError(f"B5 requires 10 validation-selected units, got {len(units)}")
    return units


def b7_units(root: Path, training_status: dict[str, Any]) -> list[dict[str, Any]]:
    selection = load_model_selection(root)
    model_based = [
        dict(row["spec"])
        for row in selection.get("B7_top3_distributed_model_based", [])
    ]
    units = model_based + data_driven_seed_specs(training_status)
    if len(units) != 6:
        raise RuntimeError(f"B7 requires 6 validation-selected units, got {len(units)}")
    return units

def load_b3_champions(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "b3" / "champions.yaml"
    if not path.exists():
        raise RuntimeError("B3 champions.yaml is required before confirmatory blocks")
    digest_path = path.with_suffix(".sha256")
    if not digest_path.exists():
        raise RuntimeError("B3 champions.sha256 is required before confirmatory blocks")
    expected = digest_path.read_text(encoding="utf-8").split()[0]
    if sha256_file(path) != expected:
        raise RuntimeError("B3 champions.yaml changed after successive-halving selection")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(key): dict(value) for key, value in data.items()}


def data_driven_seed_specs(training_status: dict[str, Any]) -> list[dict[str, Any]]:
    champion_id = str(training_status.get("champion_id"))
    champion_path = Path(str(training_status.get("champion_path", "")))
    executor_path = champion_path.parent / "dd_executor.json" if champion_path else Path("training/dd_executor.json")
    executor = json.loads(executor_path.read_text(encoding="utf-8")) if executor_path.exists() else {}
    specs: list[dict[str, Any]] = []
    for seed in training_status.get("final_seeds", []):
        spec = {
            "id": champion_id,
            "train_seed": seed.get("train_seed"),
            "training_steps": seed.get("training_steps"),
            "training_converged": seed.get("training_converged", False),
            "checkpoint_path": seed.get("checkpoint_path"),
            "checkpoint_hash": seed.get("checkpoint_hash"),
            "requires_real_checkpoint": True,
            "executor_module": executor.get("executor_module"),
            "executor_function": executor.get("executor_function"),
            "executor_backend": executor.get("backend"),
        }
        specs.append(spec)
    return specs
def data_driven_training_status(root: Path) -> dict[str, Any]:
    training_dir = ensure_directory(root / "training")
    champion_path = training_dir / "champion.yaml"
    if not champion_path.exists():
        status = {
            "status": "blocked_missing_real_trainer",
            "reason": "No preregistered training/champion.yaml exists for IPPO-GNN/MAPPO-GNN with three final seeds.",
            "confirmatory_seeds_opened": False,
            "did_not_converge_under_preregistered_budget": None,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "status.json", status)
        return status
    champion = yaml.safe_load(champion_path.read_text(encoding="utf-8")) or {}
    errors = validate_data_driven_champion(champion)
    if errors:
        status = {
            "status": "blocked_invalid_data_driven_champion",
            "reason": "; ".join(errors),
            "confirmatory_seeds_opened": False,
            "champion_path": str(champion_path),
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "status.json", status)
        return status
    status = {
        "status": "complete",
        "champion_path": str(champion_path),
        "champion_sha256": sha256_file(champion_path),
        "champion_id": champion.get("champion_id"),
        "final_seeds": champion.get("final_seeds", []),
        "confirmatory_seeds_opened": False,
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    save_json(training_dir / "status.json", status)
    return status


def validate_data_driven_champion(champion: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if champion.get("champion_id") not in {"IPPO-GNN", "MAPPO-GNN"}:
        errors.append("champion_id must be IPPO-GNN or MAPPO-GNN")
    seeds = champion.get("final_seeds")
    if not isinstance(seeds, list) or len(seeds) != 3:
        errors.append("final_seeds must contain exactly 3 seeds")
        return errors
    budget = champion.get("training_budget_contract", {})
    expected_final_steps = 5_000_000
    expected_contract = {
        "DD_1_steps": 250_000,
        "DD_2_steps": 1_000_000,
        "final_steps_per_seed": 5_000_000,
        "expected_total_environment_steps": 26_000_000,
    }
    for field, expected in expected_contract.items():
        observed = int(budget.get(field, 0) or 0)
        if observed != expected:
            errors.append(f"training_budget_contract.{field}={observed}; expected exactly {expected}")
    train_seeds = []
    for idx, seed in enumerate(seeds, start=1):
        if not isinstance(seed, dict):
            errors.append(f"final_seeds[{idx}] must be a mapping")
            continue
        train_seed = seed.get("train_seed")
        train_seeds.append(train_seed)
        observed_steps = int(seed.get("training_steps", 0) or 0)
        if observed_steps != expected_final_steps:
            errors.append(
                f"train_seed {train_seed} has {observed_steps} training_steps; expected exactly {expected_final_steps}"
            )
        checkpoint_hash = seed.get("checkpoint_hash")
        if not checkpoint_hash:
            errors.append(f"train_seed {train_seed} missing checkpoint_hash")
        checkpoint_path = seed.get("checkpoint_path")
        if not checkpoint_path or not Path(str(checkpoint_path)).exists():
            errors.append(f"train_seed {train_seed} missing checkpoint_path on disk")
        elif checkpoint_hash and sha256_file(Path(str(checkpoint_path))) != str(checkpoint_hash):
            errors.append(f"train_seed {train_seed} checkpoint SHA-256 mismatch")
    if len(set(train_seeds)) != len(train_seeds):
        errors.append("train_seed values must be distinct; no best-seed selection is allowed")
    return errors


def data_driven_execution_status(root: Path, training_status: dict[str, Any]) -> dict[str, Any]:
    training_dir = ensure_directory(root / "training")
    executor_path = training_dir / "dd_executor.json"
    if not executor_path.exists():
        status = {
            "status": "blocked_missing_real_executor",
            "reason": "training/dd_executor.json is missing; refusing to use the IPPO/MAPPO proxy in methods.py for confirmatory B4-B7.",
            "confirmatory_seeds_opened": False,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "execution_status.json", status)
        return status
    executor = json.loads(executor_path.read_text(encoding="utf-8"))
    required = ["executor_module", "executor_function", "backend", "backend_sha256"]
    missing = [key for key in required if not executor.get(key)]
    backend_module = Path(__file__).with_name("data_driven.py")
    backend_hash_invalid = bool(
        executor.get("backend_sha256")
        and sha256_file(backend_module) != str(executor.get("backend_sha256"))
    )
    if missing or backend_hash_invalid or str(executor.get("backend", "")).lower() in {"proxy", "placeholder", "heuristic"}:
        status = {
            "status": "blocked_invalid_real_executor",
            "reason": "Invalid data-driven executor metadata; missing=" + json.dumps(missing) + ", backend_hash_invalid=" + str(backend_hash_invalid) + ", backend=" + str(executor.get("backend")),
            "confirmatory_seeds_opened": False,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }
        save_json(training_dir / "execution_status.json", status)
        return status
    status = {"status": "complete", **executor, "training_champion_sha256": training_status.get("champion_sha256"), "timestamp_utc": datetime.now(UTC).isoformat()}
    save_json(training_dir / "execution_status.json", status)
    return status


def run_precision_extensions(
    config: dict[str, Any],
    root: Path,
    training_status: dict[str, Any],
    *,
    resume: bool = True,
) -> dict[str, Any]:
    """Extend B4/B5/B7 only when paired CI width exceeds the frozen precision threshold."""

    extension_dir = ensure_directory(root / "extensions")
    registry = load_frozen_seed_registry(root, allow_confirmatory=True)
    units_by_block = {
        "B4": b4_units(root, training_status),
        "B5": b5_units(root, training_status),
        "B7": b7_units(root, training_status),
    }
    base_frames = {
        block: read_parquet(root / block.lower() / "runs.parquet")
        for block in ["B4", "B5", "B7"]
    }
    decisions: dict[str, Any] = {}
    all_diagnostics: list[dict[str, Any]] = []
    for block in ["B4", "B5", "B7"]:
        combined = list(base_frames[block])
        diagnostics = precision_diagnostics(combined, block_id=block, checkpoint=40)
        all_diagnostics.extend(diagnostics)
        extend_to_60 = any(row["extend"] for row in diagnostics)
        stages = []
        if extend_to_60:
            stage_path = extension_dir / f"{block.lower()}_41_60.parquet"
            if resume and stage_path.exists():
                stage_rows = read_parquet(stage_path)
            else:
                stage_rows = run_extension_stage(
                    config,
                    root,
                    block_id=block,
                    units=units_by_block[block],
                    seeds=registry["extension_seeds_41_60"],
                    stage="41_60",
                )
                write_parquet(stage_path, stage_rows)
            combined.extend(stage_rows)
            stages.append({"stage": "41_60", "runs": len(stage_rows), "extension_reason": "precision_only"})
            diagnostics_60 = precision_diagnostics(combined, block_id=block, checkpoint=60)
            all_diagnostics.extend(diagnostics_60)
            if any(row["extend"] for row in diagnostics_60):
                stage_path = extension_dir / f"{block.lower()}_61_100.parquet"
                if resume and stage_path.exists():
                    stage_rows = read_parquet(stage_path)
                else:
                    stage_rows = run_extension_stage(
                        config,
                        root,
                        block_id=block,
                        units=units_by_block[block],
                        seeds=registry["extension_seeds_61_100"],
                        stage="61_100",
                    )
                    write_parquet(stage_path, stage_rows)
                combined.extend(stage_rows)
                stages.append({"stage": "61_100", "runs": len(stage_rows), "extension_reason": "precision_only"})
        decisions[block] = {
            "base_worlds": 40,
            "extended": bool(stages),
            "stages": stages,
            "final_checkpoint": 100 if any(item["stage"] == "61_100" for item in stages) else 60 if stages else 40,
        }
    write_parquet(extension_dir / "precision_diagnostics.parquet", all_diagnostics)
    report = {
        "status": "complete",
        "extension_reason": "precision_only",
        "thresholds": {"normalized_regret_CI_width": 0.05, "success_difference_CI_width": 0.03},
        "blocks": decisions,
        "generated_at_utc": datetime.now(UTC).isoformat(),
    }
    save_json(extension_dir / "precision_decision.json", report)
    return report


def precision_diagnostics(rows: list[dict[str, Any]], *, block_id: str, checkpoint: int) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.DataFrame(rows)
    if frame.empty:
        return [{"block_id": block_id, "checkpoint": checkpoint, "extend": True, "reason": "missing_data"}]
    frame["unit_id"] = frame.apply(
        lambda row: str(row.get("method_variant")) + (
            f"::train_seed={int(row['train_seed'])}"
            if pd.notna(row.get("train_seed"))
            else ""
        ),
        axis=1,
    )
    cell_columns = {"B4": ["N", "K"], "B5": ["N", "target_mean_degree"], "B7": ["N"]}[block_id]
    output: list[dict[str, Any]] = []
    for cell, group in frame.groupby(cell_columns, dropna=False):
        units = sorted(group["unit_id"].unique())
        preferred = "HUN" if block_id == "B4" else "GRD"
        reference = preferred if preferred in units else units[0]
        left = group[group["unit_id"] == reference]
        for unit in units:
            if unit == reference:
                continue
            right = group[group["unit_id"] == unit]
            merged = left[["world_hash", "normalized_regret", "final_success"]].merge(
                right[["world_hash", "normalized_regret", "final_success"]],
                on="world_hash",
                suffixes=("_reference", "_candidate"),
            )
            nr_reference = pd.to_numeric(merged["normalized_regret_reference"], errors="coerce").fillna(1.0).to_numpy()
            nr_candidate = pd.to_numeric(merged["normalized_regret_candidate"], errors="coerce").fillna(1.0).to_numpy()
            success_reference = pd.to_numeric(merged["final_success_reference"], errors="coerce").fillna(0.0).to_numpy()
            success_candidate = pd.to_numeric(merged["final_success_candidate"], errors="coerce").fillna(0.0).to_numpy()
            nr_width = paired_bootstrap_width(nr_candidate - nr_reference)
            success_width = paired_bootstrap_width(success_candidate - success_reference)
            extend = nr_width > 0.05 or success_width > 0.03
            output.append(
                {
                    "block_id": block_id,
                    "checkpoint": checkpoint,
                    "cell": json.dumps(cell if isinstance(cell, tuple) else [cell]),
                    "reference": reference,
                    "candidate": unit,
                    "n_worlds": len(merged),
                    "NR_CI95_width": nr_width,
                    "success_difference_CI95_width": success_width,
                    "extend": extend,
                    "extension_reason": "precision_only" if extend else "precision_sufficient",
                }
            )
    return output


def paired_bootstrap_width(values: np.ndarray, *, samples: int = 2000) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not values.size or np.allclose(values, values[0]):
        return 0.0
    rng = np.random.default_rng(20260710)
    means = np.mean(values[rng.integers(0, len(values), size=(samples, len(values)))], axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(high - low)


def run_extension_stage(
    config: dict[str, Any],
    root: Path,
    *,
    block_id: str,
    units: list[dict[str, Any]],
    seeds: list[int],
    stage: str,
) -> list[dict[str, Any]]:
    worlds: list[tuple[SP0World, dict[str, Any]]] = []
    if block_id == "B4":
        for n in B4_SIZES:
            for ratio in REGIMES:
                for seed in seeds:
                    worlds.append(
                        (
                            make_sp0_world(
                                n_robots=n, n_loads=int(math.ceil(n * ratio)), seed=seed,
                                geometry_id="G-UNI", mean_degree_target="all",
                                sp_id=str(config.get("sp_id", "SP0-v1.1")),
                            ),
                            {"confirmatory_seed": seed},
                        )
                    )
    elif block_id == "B5":
        for n in [32, 64]:
            for degree in [2, 4, 6, 10, n - 1]:
                for seed in seeds:
                    worlds.append(
                        (
                            make_sp0_world(
                                n_robots=n, n_loads=n, seed=seed, geometry_id="G-UNI",
                                mean_degree_target="all" if degree == n - 1 else degree,
                                sp_id=str(config.get("sp_id", "SP0-v1.1")),
                            ),
                            {"confirmatory_seed": seed, "target_mean_degree": degree},
                        )
                    )
    else:
        for n in [24, 48]:
            for seed in seeds:
                worlds.append(
                    (
                        make_sp0_world(
                            n_robots=n, n_loads=n, seed=seed, geometry_id="G-UNI",
                            mean_degree_target="all", sp_id=str(config.get("sp_id", "SP0-v1.1")),
                        ),
                        {"generalization_seed": seed},
                    )
                )
    unique = {world.world_hash: world for world, _extra in worlds}
    append_worlds_to_cache(root, list(unique.values()), phase=f"{block_id}_extension_{stage}")
    config_hash = _config_hash(config)
    git_hash = _git_hash()
    timestamp = datetime.now(UTC).isoformat()
    tasks: list[RunTask] = [
        (
            world,
            unit,
            f"SP0_{block_id}_precision_extension_{stage}",
            block_id,
            config_hash,
            git_hash,
            timestamp,
            {**extra, "extension_stage": stage, "extension_reason": "precision_only"},
        )
        for unit in units
        for world, extra in worlds
    ]
    return execute_run_tasks_resumable(
        tasks,
        root / "extensions" / "resume" / f"{block_id}_{stage}.parquet",
        resume=True,
    )


def write_campaign_report(root: Path, manifest: dict[str, Any]) -> None:
    lines = ["# SP0 Campaign Execution Status", "", f"Status: `{manifest.get('status')}`", "", "| Block | Status | Runs |", "|---|---:|---:|"]
    for block in ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]:
        row = manifest.get(block, {})
        lines.append(f"| {block} | {row.get('status')} | {row.get('runs', row.get('worlds', ''))} |")
    training = manifest.get("training", {})
    lines.extend(["", "## Training/Data-driven", "", json.dumps(training, indent=2, sort_keys=True), "", "Confirmatory seeds opened: `false`"])
    (root / "CAMPAIGN_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown_report(path: Path, title: str, runs: int, expected: int, extra: dict[str, Any]) -> None:
    lines = [f"# {title}", "", f"Runs: `{runs}`", f"Expected: `{expected}`", f"Count valid: `{runs == expected}`", "", "```json", json.dumps(extra, indent=2, sort_keys=True), "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=True, allow_unicode=False), encoding="utf-8")


def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row}) if rows else []
    df = pd.DataFrame([{key: normalize_cell(row.get(key)) for key in columns} for row in rows], columns=columns)
    coerce_nullable_dataframe_types(df).to_parquet(path, index=False)



def write_empty_parquet(path: Path, columns: list[str]) -> None:
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=columns).to_parquet(path, index=False)
def read_parquet(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    return pd.read_parquet(path).to_dict(orient="records")


def normalize_cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def sha256_python_sources(path: Path) -> str:
    h = hashlib.sha256()
    for item in sorted(path.rglob("*.py")):
        h.update(str(item.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(item.read_bytes())
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()
