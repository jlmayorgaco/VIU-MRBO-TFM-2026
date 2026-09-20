"""Independently audit the Cargo scene's no-pose/no-body-force contract.

This static audit is intentionally separate from the Lua runtime that it
checks.  It binds the inspected source to both the generated scene manifest
and the current ``.ttt`` hash.  Passing it establishes only the declared
actuation surface; it is not a calibration or a physical-performance result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENE = REPO_ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.ttt"
DEFAULT_MANIFEST = DEFAULT_SCENE.with_suffix(".manifest.json")
DEFAULT_RUNTIME = Path(__file__).resolve().parent / "cargo_primary_scene_runtime.lua"
DEFAULT_OUTPUT = DEFAULT_SCENE.with_suffix(".audit.json")
POSE_SETTERS = (
    "sim.setObjectPose",
    "sim.setObjectPosition",
    "sim.setObjectOrientation",
    "sim.setObjectMatrix",
    "sim.setObjectQuaternion",
)
BODY_FORCE_SETTERS = ("sim.addForce", "sim.addForceAndTorque")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _portable(path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT):
        return resolved.relative_to(REPO_ROOT).as_posix()
    return f"external-artifact://{resolved.name}"


def _without_line_comments(source: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in source.splitlines())


def _section(source: str, start: str, end: str) -> str:
    try:
        return source.split(start, 1)[1].split(end, 1)[0]
    except IndexError as exc:
        raise ValueError(f"runtime section missing: {start!r} .. {end!r}") from exc


def _calls(source: str, name: str) -> int:
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", source))


def audit_scene(scene: Path, manifest: Path, runtime: Path) -> dict[str, object]:
    scene = scene.resolve()
    manifest = manifest.resolve()
    runtime = runtime.resolve()
    for path in (scene, manifest, runtime):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    source = _without_line_comments(runtime.read_text(encoding="utf-8"))
    apply_world = _section(
        source,
        "local function applyWorld(contract)",
        "local function forbiddenCollision()",
    )
    outside_apply_world = source.replace(apply_world, "", 1)
    init = _section(source, "function sysCall_init()", "function sysCall_actuation()")
    actuation = _section(
        source,
        "function sysCall_actuation()",
        "function sysCall_sensing()",
    )
    sensing = _section(source, "function sysCall_sensing()", "function sysCall_cleanup()")

    scene_hash = _sha256(scene)
    runtime_hash = _sha256(runtime)
    recorded_scene_hash = manifest_data.get("scene", {}).get("sha256")
    recorded_runtime_hash = manifest_data.get("inputs", {}).get("runtime", {}).get("sha256")
    embedded_runtime_hash = manifest_data.get("semantic_contract", {}).get(
        "embedded_runtime_sha256"
    )
    mutators = (*POSE_SETTERS, *BODY_FORCE_SETTERS)
    checks = {
        "manifest_structurally_valid": manifest_data.get("status")
        == "structurally_valid_not_physically_calibrated",
        "scene_sha256_matches_manifest": scene_hash == recorded_scene_hash,
        "runtime_sha256_matches_manifest_input": runtime_hash == recorded_runtime_hash,
        "runtime_sha256_matches_embedded_scene_contract": runtime_hash
        == embedded_runtime_hash,
        "pose_setters_exist_for_initialization": sum(
            _calls(apply_world, name) for name in POSE_SETTERS
        )
        > 0,
        "pose_setters_confined_to_apply_world": all(
            _calls(outside_apply_world, name) == 0 for name in POSE_SETTERS
        ),
        "apply_world_called_once_from_init": _calls(init, "applyWorld") == 1
        and _calls(source, "applyWorld") == 2,
        "no_direct_body_force_calls": all(
            _calls(source, name) == 0 for name in BODY_FORCE_SETTERS
        ),
        "actuation_callback_has_no_mutator": all(
            _calls(actuation, name) == 0
            for name in (*mutators, "sim.setJointTargetVelocity", "sim.setJointTargetForce")
        ),
        "sensing_callback_has_no_mutator": all(
            _calls(sensing, name) == 0 for name in mutators
        ),
        "external_wheel_velocity_surface_present": _calls(
            source, "sim.setJointTargetVelocity"
        )
        > 0,
    }
    return {
        "schema": "viu-cargo-runtime-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pass": all(checks.values()),
        "scope": (
            "Static independent audit of pose/body-force confinement and artifact "
            "hash binding only; not a physical calibration or performance gate."
        ),
        "checks": checks,
        "artifacts": {
            "scene": {"path": _portable(scene), "sha256": scene_hash},
            "manifest": {"path": _portable(manifest), "sha256": _sha256(manifest)},
            "runtime": {"path": _portable(runtime), "sha256": runtime_hash},
            "auditor": {
                "path": _portable(Path(__file__).resolve()),
                "sha256": _sha256(Path(__file__).resolve()),
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, default=DEFAULT_SCENE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = audit_scene(args.scene, args.manifest, args.runtime)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
