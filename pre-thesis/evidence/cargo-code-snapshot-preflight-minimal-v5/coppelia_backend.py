"""Synchronous CoppeliaSim/MuJoCo adapter for the Cargo scene contract.

The adapter writes only differential-drive joint target velocities while a
simulation is active. World parameters are sent to a scene-side initialization
script before each run and must be acknowledged by readback.
"""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import numpy as np

from .backends import BackendMetadata, CalibrationReport
from .config import CampaignConfig
from .controller import Observation, WheelCommand
from .design import WorldSpec


class CoppeliaCargoError(RuntimeError):
    pass


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def _default_executable() -> Path:
    configured = os.environ.get("COPPELIASIM_EXE")
    on_path = shutil.which("coppeliaSim.exe") or shutil.which("coppeliaSim")
    program_files = os.environ.get("ProgramFiles")
    candidates = [
        Path(configured) if configured else None,
        Path(on_path) if on_path else None,
        (
            Path(program_files)
            / "CoppeliaRobotics"
            / "CoppeliaSimEdu"
            / "coppeliaSim.exe"
            if program_files
            else None
        ),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return candidate
    raise CoppeliaCargoError(
        "CoppeliaSim executable not found via COPPELIASIM_EXE, PATH or Program Files"
    )


def _stop_owned_process_tree(proc: subprocess.Popen[bytes]) -> None:
    """Stop only the CoppeliaSim process tree launched by this backend."""

    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=25.0,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode == 0:
                try:
                    proc.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    pass
                if proc.poll() is not None:
                    return
        except (OSError, subprocess.SubprocessError):
            pass
    proc.terminate()
    try:
        proc.wait(timeout=20.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5.0)


class CoppeliaMuJoCoBackend:
    WORLD_SIGNAL = "viu_cargo_world_json"
    ACK_SIGNAL = "viu_cargo_world_ack_json"
    CALIBRATION_SIGNAL = "viu_cargo_calibration_json"
    SLIP_SIGNAL = "viu_cargo_relative_slip_json"
    COLLISION_SIGNAL = "viu_cargo_collision_count"
    OBSERVATION_SIGNAL = "viu_cargo_observation_json"

    def __init__(
        self,
        config: CampaignConfig,
        *,
        executable: str | Path | None = None,
        log_path: str | Path | None = None,
        sim: Any | None = None,
        client: Any | None = None,
    ) -> None:
        if config.backend.kind != "coppeliasim_mujoco":
            raise ValueError(
                "CoppeliaMuJoCoBackend requires a coppeliasim_mujoco config"
            )
        self.config = config
        self.executable = Path(executable) if executable else None
        self.log_path = Path(log_path) if log_path else None
        self.sim = sim
        self.client = client
        self._proc: subprocess.Popen[bytes] | None = None
        self._log: Any | None = None
        self._owns_process = False
        self._started = False
        self._handles: dict[str, Any] = {}
        self._dt = 0.0
        self._calibration: CalibrationReport | None = None
        self._version = "unknown"
        self._world: WorldSpec | None = None
        self._reset_sequence = 0
        self._run_time_origin_s = 0.0
        self._scene_audit: dict[str, Any] = {
            "pass": False,
            "status": "not_checked",
        }

    @property
    def metadata(self) -> BackendMetadata:
        return BackendMetadata(
            backend_kind="coppeliasim_mujoco",
            evidence_class="physical_coppeliasim_candidate",
            engine="mujoco",
            simulator_version=self._version,
            synchronous_stepping=True,
            actuator_contract="wheel_velocity_only",
            wrench_realization="bounded_contact_setpoints_indirectly_realized_by_wheel_velocity",
        )

    @property
    def calibration(self) -> CalibrationReport:
        if self._calibration is None:
            raise CoppeliaCargoError("scene calibration has not been read")
        return self._calibration

    def start(self) -> None:
        if self.sim is None:
            self._launch_and_connect()
        sim = self.sim
        version = int(sim.getInt32Param(sim.intparam_program_version))
        self._version = f"{version // 10000}.{(version // 100) % 100}.{version % 100}"
        expected_scene = Path(str(self.config.backend.scene_path)).resolve()
        loaded_scene = Path(
            str(sim.getStringParam(sim.stringparam_scene_path_and_name))
        ).resolve()
        try:
            same_scene = expected_scene.samefile(loaded_scene)
        except (FileNotFoundError, OSError):
            same_scene = expected_scene == loaded_scene
        if not same_scene:
            raise CoppeliaCargoError(
                f"scene readback mismatch: loaded {loaded_scene}, expected {expected_scene}"
            )
        self._scene_audit = self._load_independent_scene_audit(expected_scene)
        sim.setInt32Param(sim.intparam_dynamic_engine, 4)
        if int(sim.getInt32Param(sim.intparam_dynamic_engine)) != 4:
            raise CoppeliaCargoError("MuJoCo engine readback failed")
        if self.client is not None:
            self.client.setStepping(True)
        else:
            # Isolated test doubles expose the convenience call on ``sim``.
            sim.setStepping(True)
        self._resolve_handles()
        self._started = True

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _load_independent_scene_audit(self, scene: Path) -> dict[str, Any]:
        audit_path = scene.with_suffix(".audit.json")
        if not audit_path.is_file():
            return {"pass": False, "status": "missing", "path": audit_path.name}
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "pass": False,
                "status": "invalid_json",
                "path": audit_path.name,
                "error": str(exc),
            }
        repo_root = Path(__file__).resolve().parents[3]
        checks = audit.get("checks", {})
        artifacts = audit.get("artifacts", {})
        verified_hashes: dict[str, bool] = {}
        for name in ("scene", "manifest", "runtime", "auditor"):
            record = artifacts.get(name, {})
            portable = record.get("path")
            if not isinstance(portable, str) or "://" in portable:
                verified_hashes[name] = False
                continue
            path = (repo_root / portable).resolve()
            verified_hashes[name] = bool(
                path.is_file() and record.get("sha256") == self._sha256_file(path)
            )
        passed = bool(
            audit.get("schema") == "viu-cargo-runtime-audit-v1"
            and audit.get("pass") is True
            and isinstance(checks, dict)
            and checks
            and all(value is True for value in checks.values())
            and all(verified_hashes.values())
            and artifacts.get("scene", {}).get("sha256") == self._sha256_file(scene)
        )
        return {
            "pass": passed,
            "status": "verified" if passed else "verification_failed",
            "path": audit_path.name,
            "sha256": self._sha256_file(audit_path),
            "artifact_hashes_verified": verified_hashes,
            "checks": checks,
        }

    def _launch_and_connect(self) -> None:
        backend = self.config.backend
        scene = Path(str(backend.scene_path)).resolve()
        if not scene.is_file():
            raise CoppeliaCargoError(f"Cargo scene does not exist: {scene}")
        if _port_open(backend.host, backend.port):
            raise CoppeliaCargoError(
                f"port {backend.port} is already occupied; refusing to kill or attach to an unowned process"
            )
        executable = self.executable or _default_executable()
        log_path = self.log_path or Path(self.config.output_dir) / "coppeliasim.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = log_path.open("ab", buffering=0)
        arguments = [str(executable)]
        if backend.headless:
            arguments.append("-h")
        # Scene replacement unloads the scene-side ZMQ service in 4.10 and
        # invalidates the connection that requested it.  Load the immutable
        # scene before connecting instead.
        arguments.extend(
            [
                f"-GzmqRemoteApi.rpcPort={backend.port}",
                f"-f{scene}",
            ]
        )
        self._proc = subprocess.Popen(
            arguments,
            # CoppeliaSim 4.10 exits on an immediate console EOF in headless
            # mode.  Inherit the caller's stdin; all textual output remains in
            # the owned log file.
            stdin=subprocess.PIPE,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            cwd=str(executable.parent),
        )
        self._owns_process = True
        deadline = time.monotonic() + backend.startup_timeout_s
        while time.monotonic() < deadline:
            if self._proc.poll() is not None:
                raise CoppeliaCargoError(
                    f"CoppeliaSim exited during startup with {self._proc.returncode}"
                )
            if _port_open(backend.host, backend.port):
                break
            time.sleep(0.25)
        else:
            raise CoppeliaCargoError("CoppeliaSim ZMQ port did not open before timeout")
        try:
            from coppeliasim_zmqremoteapi_client import RemoteAPIClient
            import zmq
        except ImportError as exc:
            raise CoppeliaCargoError(
                "coppeliasim-zmqremoteapi-client is not installed"
            ) from exc
        self.client = RemoteAPIClient(host=backend.host, port=backend.port)
        # The upstream client defaults to an effectively unbounded receive.
        # Bound every handshake/request and avoid lingering sockets so an
        # invalid scene cannot hang a campaign worker indefinitely.
        timeout_ms = max(1, int(backend.startup_timeout_s * 1000.0))
        self.client.socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
        self.client.socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
        self.client.socket.setsockopt(zmq.LINGER, 0)
        try:
            self.sim = self.client.require("sim")
        except zmq.error.Again as exc:
            raise CoppeliaCargoError(
                f"CoppeliaSim ZMQ handshake timed out after {backend.startup_timeout_s:.1f} s"
            ) from exc

    def _resolve_handles(self) -> None:
        aliases = self.config.backend
        self._handles["payload"] = self.sim.getObject(aliases.payload_alias)
        self._handles["robots"] = tuple(
            {
                "base": self.sim.getObject(item.base),
                "left": self.sim.getObject(item.left_wheel_joint),
                "right": self.sim.getObject(item.right_wheel_joint),
                "sensor": self.sim.getObject(item.force_sensor),
            }
            for item in aliases.robots
        )

    def _world_contract(self, world: WorldSpec, dt_s: float) -> dict[str, object]:
        self._reset_sequence += 1
        contract: dict[str, object] = {
            "protocol_family": self.config.protocol_family,
            "world_hash": world.world_hash,
            "seed": world.seed,
            "dt_s": dt_s,
            "payload_mass_kg": world.actual_payload_mass_kg,
            "yaw_inertia_kg_m2": world.yaw_inertia_kg_m2,
            "friction_coefficient": world.actual_friction_coefficient,
            "com_offset_body_m": world.com_offset_body_m,
            "initial_pose_m_rad": world.initial_pose_m_rad,
            "target_pose_m_rad": world.target_pose_m_rad,
            "contact_offsets_body_m": world.contact_offsets_body_m,
            "active_robot_count": world.active_robot_count,
            # This sequence is deliberately excluded from WorldSpec.  It
            # proves that an acknowledgement belongs to this reset while the
            # physical world remains identical across paired guard runs.
            "reset_sequence": self._reset_sequence,
            "active_robot_ids": [
                item.robot_id
                for item in self.config.backend.robots[: world.active_robot_count]
            ],
            "wheel_radius_m": self.config.robot.wheel_radius_m,
            "track_width_m": self.config.robot.track_width_m,
            "max_wheel_speed_rad_s": self.config.robot.max_wheel_speed_rad_s,
            "max_drive_force_n": self.config.robot.max_drive_force_n,
            "actuation_contract": "wheel_velocity_only",
        }
        serialized = json.dumps(contract, sort_keys=True, separators=(",", ":"))
        contract["contract_hash"] = hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()
        return contract

    def reset(self, world: WorldSpec, dt_s: float) -> Observation:
        if not self._started:
            raise CoppeliaCargoError("backend must be started before reset")
        if self.sim.getSimulationState() != self.sim.simulation_stopped:
            self.sim.stopSimulation()
            self._wait_stopped()
        self._dt = float(dt_s)
        self._world = world
        self.sim.setFloatParam(self.sim.floatparam_simulation_time_step, self._dt)
        read_dt = float(
            self.sim.getFloatParam(self.sim.floatparam_simulation_time_step)
        )
        if abs(read_dt - self._dt) > 1e-12:
            raise CoppeliaCargoError(
                f"simulation timestep readback mismatch: {read_dt} != {self._dt}"
            )
        # A repeated world is intentionally executed once per guard.  Clear
        # scene outputs before publishing the next contract so a stale ACK
        # with the same world hash can never be accepted as fresh evidence.
        for name in (
            self.ACK_SIGNAL,
            self.CALIBRATION_SIGNAL,
            self.SLIP_SIGNAL,
            self.OBSERVATION_SIGNAL,
        ):
            self.sim.clearStringSignal(name)
        self.sim.clearInt32Signal(self.COLLISION_SIGNAL)
        contract = self._world_contract(world, self._dt)
        self.sim.setStringSignal(
            self.WORLD_SIGNAL, json.dumps(contract, sort_keys=True)
        )
        # CoppeliaSim resets the remote stepping mode when a simulation is
        # stopped.  Re-arm it before every start, not only on connection.
        if self.client is not None:
            self.client.setStepping(True)
        else:
            self.sim.setStepping(True)
        self.sim.startSimulation()
        ack: dict[str, Any] = {}
        calibration: dict[str, Any] = {}
        for _ in range(max(2, int(np.ceil(1.0 / self._dt)))):
            self._synchronous_step()
            ack = self._json_signal(self.ACK_SIGNAL, required=False)
            calibration = self._json_signal(self.CALIBRATION_SIGNAL, required=False)
            if (
                ack
                and calibration
                and ack.get("contract_hash") == contract["contract_hash"]
                and ack.get("reset_sequence") == contract["reset_sequence"]
            ):
                break
        else:
            raise CoppeliaCargoError(
                "scene did not provide a fresh acknowledgement and calibration report"
            )
        self._calibration = CalibrationReport(
            sensor_static_relative_error=float(
                calibration["sensor_static_relative_error"]
            ),
            force_transmission_relative_error=float(
                calibration["force_transmission_relative_error"]
            ),
            wheel_twist_relative_error=float(calibration["wheel_twist_relative_error"]),
            # Never trust the scene's self-attestation for this gate.  Only a
            # separately generated, hash-bound audit artifact can open it.
            scene_no_pose_actuation_audited=bool(self._scene_audit.get("pass")),
            configuration_acknowledged=bool(
                ack.get("contract_hash") == contract["contract_hash"]
                and ack.get("actuation_contract") == "wheel_velocity_only"
                and ack.get("engine") == "mujoco"
                and int(ack.get("active_robot_count", -1)) == world.active_robot_count
            ),
            readback_max_abs_error=float(
                ack.get("readback_max_abs_error", float("inf"))
            ),
            raw={
                "ack": ack,
                "calibration": calibration,
                "independent_scene_audit": self._scene_audit,
            },
        )
        # Report trial time after the fixed calibration/settling prefix.  The
        # observation signal is emitted from ``sysCall_sensing`` and therefore
        # can trail ``getSimulationTime()`` by one integration step.  Anchor
        # the run to that exact sample, otherwise the first observation becomes
        # negative and every horizon is shifted by one dt.  The ACK retains the
        # simulator's init time as separate provenance.
        initial_sample = self._json_signal(self.OBSERVATION_SIGNAL, required=True)
        self._run_time_origin_s = float(initial_sample["simulation_time_s"])
        return self._observe()

    def _json_signal(self, name: str, *, required: bool) -> dict[str, Any]:
        raw = self.sim.getStringSignal(name)
        if not raw:
            if required:
                raise CoppeliaCargoError(f"required scene signal is missing: {name}")
            return {}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            parsed = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise CoppeliaCargoError(f"scene signal is not valid JSON: {name}") from exc
        if not isinstance(parsed, dict):
            raise CoppeliaCargoError(f"scene signal must be a JSON object: {name}")
        return parsed

    def apply(self, command: WheelCommand) -> None:
        if self._world is not None and np.any(
            command.wheel_speed_rad_s[self._world.active_robot_count :] != 0.0
        ):
            raise CoppeliaCargoError(
                "inactive coalition members must receive zero wheel velocity"
            )
        self._apply_wheel_speeds(command.wheel_speed_rad_s)

    def _apply_wheel_speeds(self, values: np.ndarray) -> None:
        wheels = np.asarray(values, dtype=float)
        if (
            wheels.shape != (self.config.robot.count, 2)
            or not np.isfinite(wheels).all()
        ):
            raise ValueError("invalid wheel command")
        for handles, speeds in zip(self._handles["robots"], wheels, strict=True):
            # These are the only actuator writes in the adapter.
            self.sim.setJointTargetVelocity(handles["left"], float(speeds[0]))
            self.sim.setJointTargetVelocity(handles["right"], float(speeds[1]))

    def step(self) -> Observation:
        self._synchronous_step()
        return self._observe()

    def _synchronous_step(self) -> None:
        if self.client is not None:
            self.client.step()
        else:
            self.sim.step()

    def _observe(self) -> Observation:
        if self._world is None:
            raise CoppeliaCargoError("world is not initialized")
        sample = self._json_signal(self.OBSERVATION_SIGNAL, required=True)
        if (
            sample.get("reset_sequence") != self._reset_sequence
            or sample.get("world_hash") != self._world.world_hash
        ):
            raise CoppeliaCargoError(
                "observation signal is stale or belongs to another world"
            )
        return Observation(
            time_s=float(sample["simulation_time_s"]) - self._run_time_origin_s,
            payload_pose_m_rad=np.asarray(sample["payload_pose_m_rad"], dtype=float),
            payload_twist_m_s_rad_s=np.asarray(
                sample["payload_twist_m_s_rad_s"], dtype=float
            ),
            robot_pose_m_rad=np.asarray(sample["robot_pose_m_rad"], dtype=float),
            wheel_speed_rad_s=np.asarray(sample["wheel_speed_rad_s"], dtype=float),
            wheel_drive_force_n=np.asarray(sample["wheel_drive_force_n"], dtype=float),
            measured_wrench_body=np.asarray(
                sample["measured_wrench_body"], dtype=float
            ),
            normal_force_n=np.asarray(sample["normal_force_n"], dtype=float),
            contact_active=np.asarray(sample["contact_active"], dtype=bool),
            active_robot_mask=np.asarray(sample["active_robot_mask"], dtype=bool),
            relative_slip_m=np.asarray(sample["relative_slip_m"], dtype=float),
            collision_count=int(sample["collision_count"]),
        )

    def _wait_stopped(self) -> None:
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            if self.sim.getSimulationState() == self.sim.simulation_stopped:
                return
            time.sleep(0.05)
        raise CoppeliaCargoError("simulation did not stop before timeout")

    def close(self) -> None:
        try:
            if (
                self.sim is not None
                and self.sim.getSimulationState() != self.sim.simulation_stopped
            ):
                self.sim.stopSimulation()
                self._wait_stopped()
        finally:
            client = self.client
            self.sim = None
            self.client = None
            self._world = None
            if client is not None:
                try:
                    client.socket.close(linger=0)
                    client.context.term()
                except Exception:
                    pass
            proc = self._proc
            if self._owns_process and proc is not None and proc.poll() is None:
                _stop_owned_process_tree(proc)
            if proc is not None and proc.stdin is not None:
                proc.stdin.close()
            self._proc = None
            if self._log is not None:
                self._log.close()
                self._log = None


__all__ = ["CoppeliaCargoError", "CoppeliaMuJoCoBackend"]
