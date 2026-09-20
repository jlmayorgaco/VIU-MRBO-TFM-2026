from __future__ import annotations

import csv
import gzip
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from viu_mrob_tfm.coppelia_cargo import load_config
from viu_mrob_tfm.coppelia_cargo.backends import DeterministicCargoBackend
from viu_mrob_tfm.coppelia_cargo.campaign import RUN_FIELDS, run_campaign
from viu_mrob_tfm.coppelia_cargo.coppelia_backend import (
    CoppeliaCargoError,
    CoppeliaMuJoCoBackend,
    _stop_owned_process_tree,
)
from viu_mrob_tfm.coppelia_cargo.controller import CargoPoseController
from viu_mrob_tfm.coppelia_cargo.design import build_worlds
from viu_mrob_tfm.coppelia_cargo.inference import holm_adjust, mcnemar_exact_two_sided
from viu_mrob_tfm.coppelia_cargo.preflight import PreflightEvidenceError
from viu_mrob_tfm.cli.run_coppelia_cargo import build_parser, main as cli_main


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATORY = ROOT / "experiments" / "configs" / "coppelia_cargo_confirmatory.yaml"
SMOKE = ROOT / "experiments" / "configs" / "coppelia_cargo_smoke.yaml"
PREFLIGHT = ROOT / "experiments" / "configs" / "coppelia_cargo_preflight.yaml"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_synthetic_smoke_writes_auditable_artifacts_without_physical_label(
    tmp_path: Path,
) -> None:
    config = load_config(SMOKE)
    result = run_campaign(config, output_dir=tmp_path / "smoke")

    assert result.run_count == 15
    assert result.failed_count == 0
    expected = {
        "protocol/config_snapshot.yaml",
        "protocol/design.csv",
        "protocol/seed_registry.csv",
        "runs.csv",
        "series.csv.gz",
        "failures.csv",
        "summary.csv",
        "gate_status.json",
        "manifest.json",
        "inference/analysis_contract.json",
        "inference/cell_guard_rates.csv",
        "inference/paired_guard_contrasts.csv",
    }
    assert expected <= {
        str(path.relative_to(result.output_dir)).replace("\\", "/")
        for path in result.output_dir.rglob("*")
        if path.is_file()
    }
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["backend"]["backend_kind"] == "deterministic_contract"
    assert manifest["backend"]["evidence_class"] == "synthetic_contract_test_only"
    assert "not CoppeliaSim evidence" in manifest["scientific_use"]
    assert manifest["run_counts"]["accepted"] > 0
    assert manifest["run_counts"]["rejected"] > 0

    rows = _rows(result.output_dir / "runs.csv")
    assert set(RUN_FIELDS) == set(rows[0])
    assert {row["execution_status"] for row in rows} == {"completed"}
    for row in rows:
        for field in (
            "allocation_residual_mean",
            "allocation_residual_max",
            "allocation_utilization_max",
            "max_robot_drive_force_n",
            "sensor_static_relative_error",
            "force_transmission_relative_error",
            "wheel_twist_relative_error",
            "config_readback_max_abs_error",
        ):
            assert np.isfinite(float(row[field]))
    comparable: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["phase"], row["world_hash"], row["dt_s"])
        comparable.setdefault(key, []).append(row)
    metrics = (
        "physical_success",
        "steps",
        "duration_s",
        "contact_duty",
        "max_relative_slip_m",
        "collision_count",
        "final_position_error_m",
        "final_yaw_error_rad",
        "final_linear_speed_m_s",
        "final_angular_speed_rad_s",
        "saturation_count",
    )
    for group in comparable.values():
        if len(group) == 3:
            assert all(len({row[metric] for row in group}) == 1 for metric in metrics)

    with gzip.open(
        result.output_dir / "series.csv.gz", "rt", encoding="utf-8"
    ) as handle:
        first_series = next(csv.DictReader(handle))
    assert first_series["run_id"]
    for field in (
        "allocated_fx_n",
        "allocated_fy_n",
        "allocated_tau_n_m",
        "allocation_residual_normalized",
        "allocation_utilization",
        "allocation_saturation_count",
        "wheel_saturation_count",
        "max_robot_drive_force_n",
        "normal_force_r1_n",
        "wheel_speed_r1_left_rad_s",
        "wheel_drive_force_r1_left_n",
    ):
        assert field in first_series
        assert np.isfinite(float(first_series[field]))
    assert first_series["contact_active_r1"] in {"True", "False"}

    rates = _rows(result.output_dir / "inference" / "cell_guard_rates.csv")
    contrasts = _rows(result.output_dir / "inference" / "paired_guard_contrasts.csv")
    assert len(rates) == 3
    assert len(contrasts) == 9
    assert {row["n_complete_pairs"] for row in contrasts} == {"2"}
    assert {row["evidence_class"] for row in contrasts} == {
        "synthetic_contract_test_only"
    }
    assert all(
        float(row["mcnemar_p_holm"]) >= float(row["mcnemar_p_raw"]) for row in contrasts
    )


def test_exact_mcnemar_and_holm_are_deterministic() -> None:
    a = np.asarray([True, True, True, False])
    b = np.asarray([False, False, True, False])
    a_only, b_only, p_value = mcnemar_exact_two_sided(a, b)
    assert (a_only, b_only, p_value) == (2, 0, 0.5)
    assert holm_adjust([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_minimal_coalition_executes_three_robots_and_parks_fourth() -> None:
    config = load_config(SMOKE)
    world = build_worlds(config)[0]
    backend = DeterministicCargoBackend(config)
    backend.start()
    try:
        observation = backend.reset(world, config.design.primary_dt_s)
        command = CargoPoseController(config).command(
            world, observation, config.design.primary_dt_s
        )
    finally:
        backend.close()
    assert world.active_robot_count == 3
    assert observation.active_robot_mask.tolist() == [True, True, True, False]
    assert np.array_equal(command.wheel_speed_rad_s[3], np.zeros(2))


def test_cli_contract_and_confirmatory_denial(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    parsed = build_parser().parse_args(
        ["--config", str(SMOKE), "--output-dir", str(tmp_path / "smoke"), "--dry-run"]
    )
    assert parsed.config == SMOKE
    assert parsed.output_dir == tmp_path / "smoke"
    assert cli_main(["--config", str(CONFIRMATORY), "--dry-run"]) == 0
    dry_run = json.loads(capsys.readouterr().out)
    assert dry_run["primary_runs"] == 1440
    assert dry_run["confirmatory_execution_requires"] == [
        "--authorize-confirmatory",
        "--preflight-evidence DIR",
    ]
    with pytest.raises(PermissionError, match="authorize-confirmatory"):
        cli_main(
            [
                "--config",
                str(CONFIRMATORY),
                "--output-dir",
                str(tmp_path / "denied"),
            ]
        )
    assert not (tmp_path / "denied").exists()

    with pytest.raises(PreflightEvidenceError, match="preflight-evidence"):
        cli_main(
            [
                "--config",
                str(CONFIRMATORY),
                "--output-dir",
                str(tmp_path / "denied-with-authorization-only"),
                "--authorize-confirmatory",
            ]
        )
    assert not (tmp_path / "denied-with-authorization-only").exists()


class FailingBackend(DeterministicCargoBackend):
    def reset(self, world, dt_s):  # type: ignore[no-untyped-def]
        raise RuntimeError("injected reset failure")


class NaNBackend(DeterministicCargoBackend):
    def step(self):  # type: ignore[no-untyped-def]
        observation = super().step()
        pose = observation.payload_pose_m_rad.copy()
        pose[0] = np.nan
        return replace(observation, payload_pose_m_rad=pose)


def test_failures_are_first_class_records(tmp_path: Path) -> None:
    config = load_config(SMOKE)
    result = run_campaign(
        config,
        output_dir=tmp_path / "failures",
        backend_factory=FailingBackend,
    )
    assert result.failed_count == result.run_count
    failures = _rows(result.output_dir / "failures.csv")
    assert len(failures) == result.run_count
    assert {row["error_type"] for row in failures} == {"RuntimeError"}
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "complete_with_failed_trials"


def test_nan_trials_are_recorded_and_fail_physical_gates(tmp_path: Path) -> None:
    config = load_config(SMOKE)
    result = run_campaign(
        config,
        output_dir=tmp_path / "nan",
        backend_factory=NaNBackend,
    )
    rows = _rows(result.output_dir / "runs.csv")
    assert {row["nan_detected"] for row in rows} == {"True"}
    assert {row["physical_success"] for row in rows} == {"False"}
    gate_status = json.loads(
        (result.output_dir / "gate_status.json").read_text(encoding="utf-8")
    )
    assert gate_status["execution"]["nan_runs"] == result.run_count


class FakeActuatorSim:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, float]] = []

    def setJointTargetVelocity(self, handle: object, value: float) -> None:
        self.calls.append(("setJointTargetVelocity", handle, value))


def test_real_adapter_actuator_surface_is_wheel_velocity_only() -> None:
    config = load_config(CONFIRMATORY)
    sim = FakeActuatorSim()
    backend = CoppeliaMuJoCoBackend(config, sim=sim)
    backend._handles["robots"] = tuple(  # an isolated adapter surface test
        {"left": f"L{index}", "right": f"R{index}"}
        for index in range(config.robot.count)
    )
    command = np.arange(config.robot.count * 2, dtype=float).reshape(
        config.robot.count, 2
    )
    backend._apply_wheel_speeds(command)
    assert len(sim.calls) == 2 * config.robot.count
    assert {call[0] for call in sim.calls} == {"setJointTargetVelocity"}
    assert [call[2] for call in sim.calls] == command.reshape(-1).tolist()


class FakeSignalSim:
    floatparam_simulation_time_step = 1
    simulation_stopped = 0

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | int]] = []
        self.dt = 0.0

    def setFloatParam(self, _param: int, value: float) -> None:
        self.dt = value

    def getSimulationState(self) -> int:
        return self.simulation_stopped

    def getFloatParam(self, _param: int) -> float:
        return self.dt

    def clearStringSignal(self, name: str) -> None:
        self.calls.append(("clearStringSignal", name))

    def clearInt32Signal(self, name: str) -> None:
        self.calls.append(("clearInt32Signal", name))

    def setStringSignal(self, name: str, _value: str) -> None:
        self.calls.append(("setStringSignal", name))

    def startSimulation(self) -> None:
        self.calls.append(("startSimulation", 0))

    def setStepping(self, enabled: bool) -> None:
        self.calls.append(("setStepping", int(enabled)))

    def step(self) -> None:
        self.calls.append(("step", 0))

    def getStringSignal(self, _name: str):  # type: ignore[no-untyped-def]
        return None


class FakeClockSim(FakeSignalSim):
    """Mimic sensing-time stamps that trail the simulator clock by one dt."""

    simulation_advancing = 1

    def __init__(self) -> None:
        super().__init__()
        self.state = self.simulation_stopped
        self.time_s = 0.0
        self.signals: dict[str, str] = {}
        self.contract: dict[str, object] = {}

    def getSimulationState(self) -> int:
        return self.state

    def clearStringSignal(self, name: str) -> None:
        super().clearStringSignal(name)
        self.signals.pop(name, None)

    def setStringSignal(self, name: str, value: str) -> None:
        super().setStringSignal(name, value)
        self.signals[name] = value
        if name == CoppeliaMuJoCoBackend.WORLD_SIGNAL:
            self.contract = json.loads(value)

    def getStringSignal(self, name: str):  # type: ignore[no-untyped-def]
        return self.signals.get(name)

    def startSimulation(self) -> None:
        super().startSimulation()
        self.state = self.simulation_advancing
        self.time_s = 0.0

    def stopSimulation(self) -> None:
        self.state = self.simulation_stopped

    def getSimulationTime(self) -> float:
        return self.time_s

    def step(self) -> None:
        super().step()
        sensing_time = self.time_s
        self.time_s += self.dt
        count = int(self.contract["active_robot_count"])
        reset_sequence = int(self.contract["reset_sequence"])
        world_hash = str(self.contract["world_hash"])
        contract_hash = str(self.contract["contract_hash"])
        self.signals[CoppeliaMuJoCoBackend.ACK_SIGNAL] = json.dumps(
            {
                "contract_hash": contract_hash,
                "reset_sequence": reset_sequence,
                "actuation_contract": "wheel_velocity_only",
                "engine": "mujoco",
                "active_robot_count": count,
                "readback_max_abs_error": 0.0,
            }
        )
        self.signals[CoppeliaMuJoCoBackend.CALIBRATION_SIGNAL] = json.dumps(
            {
                "sensor_static_relative_error": 0.0,
                "force_transmission_relative_error": 1.0,
                "wheel_twist_relative_error": 1.0,
            }
        )
        self.signals[CoppeliaMuJoCoBackend.OBSERVATION_SIGNAL] = json.dumps(
            {
                "reset_sequence": reset_sequence,
                "world_hash": world_hash,
                "simulation_time_s": sensing_time,
                "payload_pose_m_rad": [0.0, 0.0, 0.0],
                "payload_twist_m_s_rad_s": [0.0, 0.0, 0.0],
                "robot_pose_m_rad": [[0.0, 0.0, 0.0]] * 4,
                "wheel_speed_rad_s": [[0.0, 0.0]] * 4,
                "wheel_drive_force_n": [[0.0, 0.0]] * 4,
                "measured_wrench_body": [0.0, 0.0, 0.0],
                "normal_force_n": [1.0] * count + [0.0] * (4 - count),
                "contact_active": [True] * count + [False] * (4 - count),
                "active_robot_mask": [True] * count + [False] * (4 - count),
                "relative_slip_m": [0.0] * 4,
                "collision_count": 0,
            }
        )


def test_real_adapter_clears_outputs_before_repeated_world_contract() -> None:
    config = load_config(CONFIRMATORY)
    sim = FakeSignalSim()
    backend = CoppeliaMuJoCoBackend(config, sim=sim)
    backend._started = True
    world = build_worlds(config)[0]
    with pytest.raises(CoppeliaCargoError, match="fresh acknowledgement"):
        backend.reset(world, config.design.primary_dt_s)
    publish_index = sim.calls.index(("setStringSignal", backend.WORLD_SIGNAL))
    clears = sim.calls[:publish_index]
    assert clears == [
        ("clearStringSignal", backend.ACK_SIGNAL),
        ("clearStringSignal", backend.CALIBRATION_SIGNAL),
        ("clearStringSignal", backend.SLIP_SIGNAL),
        ("clearStringSignal", backend.OBSERVATION_SIGNAL),
        ("clearInt32Signal", backend.COLLISION_SIGNAL),
    ]


def test_real_adapter_time_origin_excludes_settling_and_tracks_exact_horizon() -> None:
    config = load_config(PREFLIGHT)
    sim = FakeClockSim()
    backend = CoppeliaMuJoCoBackend(config, sim=sim)
    backend._started = True
    world = build_worlds(config)[0]
    dt_s = config.design.primary_dt_s

    initial = backend.reset(world, dt_s)
    assert initial.time_s == pytest.approx(0.0, abs=1.0e-15)
    step_count = round(config.control.horizon_s / dt_s)
    observation = initial
    for _ in range(step_count):
        observation = backend.step()
    assert observation.time_s == pytest.approx(config.control.horizon_s, abs=1.0e-12)

    repeated = backend.reset(world, dt_s)
    assert repeated.time_s == pytest.approx(0.0, abs=1.0e-15)
    assert backend._reset_sequence == 2


def test_owned_windows_process_cleanup_targets_only_the_spawned_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name != "nt":
        pytest.skip("Windows-specific CoppeliaSim process-tree contract")

    class FakeProcess:
        pid = 4242

        def __init__(self) -> None:
            self.running = True
            self.terminate_called = False
            self.kill_called = False

        def poll(self) -> int | None:
            return None if self.running else 1

        def wait(self, timeout: float) -> int:
            if self.running:
                raise subprocess.TimeoutExpired("fake", timeout)
            return 1

        def terminate(self) -> None:
            self.terminate_called = True

        def kill(self) -> None:
            self.kill_called = True
            self.running = False

    process = FakeProcess()
    calls: list[list[str]] = []

    def fake_run(
        arguments: list[str], **_: object
    ) -> subprocess.CompletedProcess[bytes]:
        calls.append(arguments)
        process.running = False
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(
        "viu_mrob_tfm.coppelia_cargo.coppelia_backend.subprocess.run",
        fake_run,
    )
    _stop_owned_process_tree(process)  # type: ignore[arg-type]

    assert calls == [["taskkill", "/PID", "4242", "/T", "/F"]]
    assert process.terminate_called is False
    assert process.kill_called is False
