"""Build and structurally validate the primary Cargo CoppeliaSim scene.

The builder deliberately uses a CoppeliaSim add-on instead of the remote API:
scene construction must also work when no ZMQ service is available.  Every
process is owned by this command and no unrelated simulator process is ever
terminated.  Structural validation is not a physical calibration and cannot
open the confirmatory gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TARGET = REPO_ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.ttt"
DEFAULT_MANIFEST = DEFAULT_TARGET.with_suffix(".manifest.json")
ADDON_PATH = SCRIPT_DIR / "cargo_primary_scene_builder.lua"
RUNTIME_PATH = SCRIPT_DIR / "cargo_primary_scene_runtime.lua"
GENERATOR_VERSION = "cargo-primary-scene-v1"


class SceneBuildError(RuntimeError):
    """The owned CoppeliaSim builder process did not produce a valid scene."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def portable_repo_path(path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(REPO_ROOT):
        return resolved.relative_to(REPO_ROOT).as_posix()
    return f"external-artifact://{resolved.name}"


def portable_coppelia_path(path: Path, installation_root: Path) -> str:
    resolved = path.resolve()
    root = installation_root.resolve()
    if not resolved.is_relative_to(root):
        return f"coppeliasim-installation://{resolved.name}"
    return "coppeliasim-installation://" + resolved.relative_to(root).as_posix()


def default_coppeliasim_executable() -> Path:
    configured = os.environ.get("COPPELIASIM_EXE")
    on_path = shutil.which("coppeliaSim.exe") or shutil.which("coppeliaSim")
    candidates = [
        Path(configured) if configured else None,
        Path(on_path) if on_path else None,
        Path.home() / "Documents" / "CoppeliaSim" / "V4_10_0" / "coppeliaSim.exe",
    ]
    program_files = os.environ.get("ProgramFiles")
    if program_files:
        candidates.append(
            Path(program_files) / "CoppeliaRobotics" / "CoppeliaSimEdu" / "coppeliaSim.exe"
        )
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate.resolve()
    raise SceneBuildError(
        "CoppeliaSim executable not found; set COPPELIASIM_EXE or pass --executable"
    )


def default_pioneer_model(executable: Path) -> Path:
    candidate = executable.parent / "models" / "robots" / "mobile" / "pioneer p3dx.ttm"
    if not candidate.is_file():
        raise SceneBuildError(f"native Pioneer P3DX model not found: {candidate}")
    return candidate.resolve()


def _read_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SceneBuildError(f"CoppeliaSim did not write builder status: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SceneBuildError(f"invalid builder status JSON: {path}") from exc
    if not isinstance(value, dict):
        raise SceneBuildError("builder status must be a JSON object")
    return value


def _run_addon(
    *,
    executable: Path,
    mode: str,
    scene: Path | None,
    output: Path,
    pioneer_model: Path,
    runtime_script: Path,
    status_path: Path,
    log_path: Path,
    timeout_s: float,
) -> dict[str, Any]:
    arguments = [str(executable), "-h", "-vscriptinfos"]
    # CoppeliaSim processes startup actions in command-line order.  A scene
    # must therefore be loaded before the validation add-on starts.
    if scene is not None:
        arguments.append(f"-f{scene.resolve()}")
    arguments.extend([
        f"-a{ADDON_PATH.resolve()}",
        f"-GviuCargoBuilderMode={mode}",
        f"-GviuCargoOutput={output.resolve()}",
        f"-GviuCargoPioneerModel={pioneer_model.resolve()}",
        f"-GviuCargoRuntimeScript={runtime_script.resolve()}",
        f"-GviuCargoRuntimeSha256={sha256_file(runtime_script)}",
        f"-GviuCargoStatus={status_path.resolve()}",
    ])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("wb") as log_handle:
        process = subprocess.Popen(
            arguments,
            stdin=subprocess.PIPE,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=str(executable.parent),
        )
        try:
            return_code = process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            process.terminate()
            try:
                process.wait(timeout=20.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5.0)
            raise SceneBuildError(
                f"owned CoppeliaSim builder timed out after {timeout_s:.1f} s; see {log_path}"
            ) from exc
        finally:
            if process.stdin is not None:
                process.stdin.close()
    status = _read_status(status_path)
    if return_code != 0 or status.get("status") != "ok":
        detail = status.get("error", f"exit code {return_code}")
        raise SceneBuildError(f"CoppeliaSim builder failed: {detail}; see {log_path}")
    return status


def _semantic_contract(status: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "generator_version",
        "simulator_version",
        "engine",
        "payload_alias",
        "robot_count",
        "force_sensor_count",
        "passive_yaw_joint_count",
        "loop_closure_count",
        "wheel_joint_count",
        "runtime_script_count",
        "actuation_contract",
        "calibration_status",
        "embedded_runtime_sha256",
        "aliases",
    )
    return {key: status.get(key) for key in keys}


def build_scene(
    *,
    target: Path = DEFAULT_TARGET,
    executable: Path | None = None,
    pioneer_model: Path | None = None,
    manifest_path: Path = DEFAULT_MANIFEST,
    force: bool = False,
    timeout_s: float = 180.0,
) -> dict[str, Any]:
    target = target.resolve()
    manifest_path = manifest_path.resolve()
    executable = (executable or default_coppeliasim_executable()).resolve()
    pioneer_model = (pioneer_model or default_pioneer_model(executable)).resolve()
    for required in (executable, pioneer_model, ADDON_PATH, RUNTIME_PATH):
        if not required.is_file():
            raise SceneBuildError(f"required build input is missing: {required}")
    if target.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing scene without --force: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="viu-cargo-scene-", dir=target.parent) as raw_tmp:
        tmp = Path(raw_tmp)
        staged_scene = tmp / target.name
        build_status_path = tmp / "build-status.json"
        validate_status_path = tmp / "validate-status.json"
        build_log = tmp / "build.log"
        validate_log = tmp / "validate.log"
        build_status = _run_addon(
            executable=executable,
            mode="build",
            scene=None,
            output=staged_scene,
            pioneer_model=pioneer_model,
            runtime_script=RUNTIME_PATH,
            status_path=build_status_path,
            log_path=build_log,
            timeout_s=timeout_s,
        )
        if not staged_scene.is_file() or staged_scene.stat().st_size < 1024:
            raise SceneBuildError(f"builder produced no usable scene: {staged_scene}")
        validate_status = _run_addon(
            executable=executable,
            mode="validate",
            scene=staged_scene,
            output=staged_scene,
            pioneer_model=pioneer_model,
            runtime_script=RUNTIME_PATH,
            status_path=validate_status_path,
            log_path=validate_log,
            timeout_s=timeout_s,
        )
        build_contract = _semantic_contract(build_status)
        validate_contract = _semantic_contract(validate_status)
        if build_contract != validate_contract:
            raise SceneBuildError(
                "saved scene semantic contract differs from the in-memory build contract"
            )
        if validate_contract.get("embedded_runtime_sha256") != sha256_file(RUNTIME_PATH):
            raise SceneBuildError("saved scene is not linked to the selected runtime SHA-256")

        os.replace(staged_scene, target)
        persistent_log = target.with_suffix(".builder.log")
        persistent_log.write_bytes(build_log.read_bytes() + b"\n--- reload validation ---\n" + validate_log.read_bytes())
        portable_scene = portable_repo_path(target)
        portable_build_status = {**build_status, "output": portable_scene}
        portable_validate_status = {**validate_status, "output": portable_scene}
        manifest: dict[str, Any] = {
            "schema": "viu-cargo-scene-manifest-v1",
            "generator_version": GENERATOR_VERSION,
            "status": "structurally_valid_not_physically_calibrated",
            "scientific_use": (
                "Scene construction evidence only. This manifest does not establish any "
                "physical, calibration, stability, safety, or confirmatory gate."
            ),
            "scene": {
                "path": portable_scene,
                "sha256": sha256_file(target),
                "bytes": target.stat().st_size,
            },
            "inputs": {
                "addon": {
                    "path": portable_repo_path(ADDON_PATH),
                    "sha256": sha256_file(ADDON_PATH),
                },
                "runtime": {
                    "path": portable_repo_path(RUNTIME_PATH),
                    "sha256": sha256_file(RUNTIME_PATH),
                },
                "pioneer_model": {
                    "path": portable_coppelia_path(pioneer_model, executable.parent),
                    "sha256": sha256_file(pioneer_model),
                },
                "coppeliasim_executable": {
                    "path": portable_coppelia_path(executable, executable.parent),
                    "sha256": sha256_file(executable),
                },
            },
            "semantic_contract": validate_contract,
            "builder_status": portable_build_status,
            "reload_validation_status": portable_validate_status,
            "log": portable_repo_path(persistent_log),
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return manifest


def validate_scene(
    scene: Path,
    *,
    executable: Path | None = None,
    pioneer_model: Path | None = None,
    timeout_s: float = 180.0,
) -> dict[str, Any]:
    scene = scene.resolve()
    if not scene.is_file():
        raise FileNotFoundError(scene)
    executable = (executable or default_coppeliasim_executable()).resolve()
    pioneer_model = (pioneer_model or default_pioneer_model(executable)).resolve()
    with tempfile.TemporaryDirectory(prefix="viu-cargo-validate-") as raw_tmp:
        tmp = Path(raw_tmp)
        return _run_addon(
            executable=executable,
            mode="validate",
            scene=scene,
            output=scene,
            pioneer_model=pioneer_model,
            runtime_script=RUNTIME_PATH,
            status_path=tmp / "status.json",
            log_path=tmp / "validate.log",
            timeout_s=timeout_s,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--pioneer-model", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--timeout-s", type=float, default=180.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout_s <= 0:
        raise ValueError("--timeout-s must be positive")
    if args.validate_only is not None:
        result = validate_scene(
            args.validate_only,
            executable=args.executable,
            pioneer_model=args.pioneer_model,
            timeout_s=args.timeout_s,
        )
    else:
        result = build_scene(
            target=args.target,
            executable=args.executable,
            pioneer_model=args.pioneer_model,
            manifest_path=args.manifest,
            force=args.force,
            timeout_s=args.timeout_s,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SceneBuildError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
