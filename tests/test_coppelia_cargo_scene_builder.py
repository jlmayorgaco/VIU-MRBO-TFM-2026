from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "coppelia_cargo" / "build_cargo_primary_scene.py"
ADDON = ROOT / "scripts" / "coppelia_cargo" / "cargo_primary_scene_builder.lua"
RUNTIME = ROOT / "scripts" / "coppelia_cargo" / "cargo_primary_scene_runtime.lua"
AUDITOR = ROOT / "scripts" / "coppelia_cargo" / "audit_cargo_runtime_contract.py"
PREFLIGHT = ROOT / "experiments" / "configs" / "coppelia_cargo_preflight.yaml"
MINIMAL_PREFLIGHT = (
    ROOT / "experiments" / "configs" / "coppelia_cargo_preflight_minimal.yaml"
)
SCENE_MANIFEST = ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.manifest.json"


def _load_builder():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("cargo_scene_builder", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_auditor():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("cargo_runtime_auditor", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_builder_inputs_are_self_contained_and_locate_native_pioneer() -> None:
    module = _load_builder()
    executable = module.default_coppeliasim_executable()
    pioneer = module.default_pioneer_model(executable)
    assert executable.name.lower() == "coppeliasim.exe"
    assert pioneer.name.lower() == "pioneer p3dx.ttm"
    assert ADDON.is_file() and RUNTIME.is_file()


def test_runtime_has_no_pose_or_force_actuation_after_initialization() -> None:
    source = RUNTIME.read_text(encoding="utf-8")
    actuation = source.split("function sysCall_actuation()", 1)[1].split(
        "function sysCall_sensing()", 1
    )[0]
    sensing = source.split("function sysCall_sensing()", 1)[1].split(
        "function sysCall_cleanup()", 1
    )[0]
    forbidden = (
        "setObjectPose",
        "setObjectPosition",
        "setObjectOrientation",
        "addForce",
        "addForceAndTorque",
    )
    assert all(token not in actuation for token in forbidden)
    assert all(token not in sensing for token in forbidden)
    assert "setJointTargetVelocity" not in actuation


def test_scene_contract_contains_four_sensors_and_no_claimed_calibration() -> None:
    addon = ADDON.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    assert "for index = 1, 4" in addon
    assert "sim.createForceSensor" in addon
    assert "sim.dummytype_dynloopclosure" in addon
    assert "calibration_status = 'pending_preflight'" in addon
    assert "wheel_twist_status = 'not_executed'" in runtime
    assert "scene_no_pose_actuation_audited = false" in runtime
    assert "sim.getJointTargetForce" in runtime
    assert "0.5 * contract.max_drive_force_n * contract.wheel_radius_m" in runtime
    assert "sim.setObjectPosition(\n                robot.payloadLoop" in runtime
    assert "support_overlap_max_abs_error_m = maxAbs(overlapErrors)" in runtime
    assert "OBSERVATION_SIGNAL = 'viu_cargo_observation_json'" in runtime
    assert "wheel_drive_force_n = wheelForces" in runtime


def test_scene_manifest_uses_portable_paths_and_distinct_alias_handles() -> None:
    manifest = json.loads(SCENE_MANIFEST.read_text(encoding="utf-8"))
    def string_values(value):  # type: ignore[no-untyped-def]
        if isinstance(value, dict):
            for child in value.values():
                yield from string_values(child)
        elif isinstance(value, list):
            for child in value:
                yield from string_values(child)
        elif isinstance(value, str):
            yield value

    assert all(
        not re.match(r"^[A-Za-z]:[\\/]", value)
        for value in string_values(manifest)
    )
    status = manifest["reload_validation_status"]
    assert status["aliases_resolve_to_distinct_handles"] is True
    assert status["required_alias_count"] == status["distinct_alias_handle_count"] == 17


def test_independent_runtime_audit_is_hash_bound_and_detects_tampering(
    tmp_path: Path,
) -> None:
    module = _load_auditor()
    scene = ROOT / "coppeliasim" / "real_scenes" / "cargo_primary_mujoco_v1.ttt"
    result = module.audit_scene(scene, SCENE_MANIFEST, RUNTIME)
    assert result["pass"] is True
    tampered = tmp_path / "runtime.lua"
    tampered.write_text(
        RUNTIME.read_text(encoding="utf-8")
        + "\nfunction forbiddenMutation() sim.setObjectPosition(1,{0,0,0},-1) end\n",
        encoding="utf-8",
    )
    rejected = module.audit_scene(scene, SCENE_MANIFEST, tampered)
    assert rejected["pass"] is False
    assert rejected["checks"]["pose_setters_confined_to_apply_world"] is False


def test_physical_preflight_is_separate_from_confirmatory_registry() -> None:
    from viu_mrob_tfm.coppelia_cargo import build_run_specs, load_config

    config = load_config(PREFLIGHT)
    runs = build_run_specs(config)
    primary = [run for run in runs if run.phase == "primary"]
    sensitivity = [run for run in runs if run.phase == "dt_sensitivity"]
    assert config.mode == "smoke"
    assert config.backend.kind == "coppeliasim_mujoco"
    assert config.design.cell_count == 16
    assert config.design.seeds.count == 1
    assert len(primary) == 16 * 3
    assert len(sensitivity) == 2 * 1 * 3 * 3


def test_minimal_physical_preflight_is_bounded_and_keeps_all_gates() -> None:
    from viu_mrob_tfm.coppelia_cargo import build_run_specs, load_config

    config = load_config(MINIMAL_PREFLIGHT)
    runs = build_run_specs(config)
    assert config.mode == "smoke"
    assert config.backend.kind == "coppeliasim_mujoco"
    assert config.design.cell_count == 1
    assert config.design.coalition == ("redundant",)
    assert config.control.horizon_s == 0.25
    assert config.gates.dwell_time_s == 1.0
    assert len(runs) == 6
