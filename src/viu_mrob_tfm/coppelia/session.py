"""Sesión determinista de CoppeliaSim sobre la API remota ZMQ.

El avance del tiempo lo dispara siempre el cliente: sin `step()` no hay paso.
Es lo que hace reproducible una corrida con semilla fija y lo que permite
comparar la campaña física con la predicción del certificador.

Contrato:

    with CoppeliaSession(scene=ruta, motor="mujoco", dt=0.005) as ses:
        ses.start()
        for _ in range(pasos):
            ses.step()
            ...
        # stop() y cierre del proceso ocurren solos, también ante excepción

Notas de integración, para no repetir el camino largo:

* CoppeliaSim expone la API ZMQ en el puerto **23000**. El 19997 es de la API
  heredada y no está activo en esta instalación. Comprobarlo con
  `Get-NetTCPConnection -State Listen`, no deducirlo de la documentación.
* `sim.getInt32Param(sim.intparam_program_version)` devuelve `41000`, que es
  **4.10.0**, no 4.1.0.
* El proceso termina de inmediato si su salida estándar va a `DEVNULL`;
  necesita un descriptor real. Se le pasa un fichero de log, que además deja
  traza de la sesión.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

from coppeliasim_zmqremoteapi_client import RemoteAPIClient

PUERTO_ZMQ = 23000

MOTORES = {"bullet": 0, "ode": 1, "vortex": 2, "newton": 3, "mujoco": 4}
MOTORES_INV = {v: k for k, v in MOTORES.items()}

class ErrorSesion(RuntimeError):
    """La sesión no pudo establecerse o quedó inutilizable."""


def ejecutable_por_defecto() -> Path:
    configured = os.environ.get("COPPELIASIM_EXE")
    on_path = shutil.which("coppeliaSim.exe") or shutil.which("coppeliaSim")
    program_files = os.environ.get("ProgramFiles")
    candidatos = (
        Path(configured) if configured else None,
        Path(on_path) if on_path else None,
        (
            Path(program_files) / "CoppeliaRobotics" / "CoppeliaSimEdu" / "coppeliaSim.exe"
            if program_files
            else None
        ),
    )
    for ruta in candidatos:
        if ruta is None:
            continue
        if ruta.exists():
            return ruta
    raise ErrorSesion(
        "No se encontró coppeliaSim.exe mediante COPPELIASIM_EXE, PATH o Program Files.")


def _puerto_escucha(puerto: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, puerto)) == 0


class CoppeliaSession:
    def __init__(
        self,
        scene: str | os.PathLike[str] | None = None,
        motor: str = "mujoco",
        dt: float | None = None,
        puerto: int = PUERTO_ZMQ,
        ejecutable: str | os.PathLike[str] | None = None,
        headless: bool = True,
        arranque_s: float = 120.0,
        reutilizar: bool = False,
        log_path: str | os.PathLike[str] | None = None,
    ) -> None:
        if motor not in MOTORES:
            raise ValueError("Motor desconocido: %r. Opciones: %s"
                             % (motor, ", ".join(MOTORES)))
        self.scene = Path(scene).resolve() if scene else None
        self.motor_pedido = motor
        self.dt = dt
        self.puerto = puerto
        self.ejecutable = Path(ejecutable) if ejecutable else ejecutable_por_defecto()
        self.headless = headless
        self.arranque_s = arranque_s
        self.reutilizar = reutilizar
        self.log_path = Path(log_path) if log_path else (
            Path(__file__).resolve().parents[3] / "coppelia_session.log")

        self.client: RemoteAPIClient | None = None
        self.sim: Any = None
        self._proc: subprocess.Popen[bytes] | None = None
        self._log: Any = None
        self._lanzado_por_mi = False

    # ---------------------------------------------------------------- ciclo
    def __enter__(self) -> "CoppeliaSession":
        puerto_ocupado = _puerto_escucha(self.puerto)
        escena_cargada_en_arranque = False
        if self.reutilizar and puerto_ocupado:
            pass
        elif puerto_ocupado:
            raise ErrorSesion(
                "El puerto %d ya está ocupado; se rechaza terminar o "
                "adjuntar una instancia no propiedad de esta sesión."
                % self.puerto)
        else:
            self._lanzar()
            self._lanzado_por_mi = True
            escena_cargada_en_arranque = self.scene is not None
        self._conectar()
        if self.scene is not None and not escena_cargada_en_arranque:
            self.cargar_escena(self.scene)
        self.fijar_motor(self.motor_pedido)
        if self.dt is not None:
            self.fijar_paso(self.dt)
        self.sim.setStepping(True)
        return self

    def __exit__(self, *exc: Any) -> None:
        self.cerrar()

    def _lanzar(self) -> None:
        if not self.ejecutable.exists():
            raise ErrorSesion("No existe el ejecutable: %s" % self.ejecutable)
        args = [str(self.ejecutable)]
        if self.headless:
            args.append("-h")
        # Loading a scene through the same ZMQ connection tears down the
        # scene-owned add-on that serves that connection in CoppeliaSim 4.10.
        # Command-line loading happens before the server accepts clients and
        # therefore preserves a usable, deterministic remote session.  The
        # same -f option accepts .ttm models, which is useful for builders.
        if self.scene is not None:
            args.append(f"-f{self.scene}")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = open(self.log_path, "ab", buffering=0)
        self._proc = subprocess.Popen(
            args,
            # CoppeliaSim 4.10 treats an immediate console EOF as a shutdown
            # request in headless mode.  Inherit the caller's handle instead
            # of wiring stdin to DEVNULL; stdout/stderr still go to the owned
            # log file.
            stdin=None,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            cwd=str(self.ejecutable.parent),
        )
        limite = time.time() + self.arranque_s
        while time.time() < limite:
            if _puerto_escucha(self.puerto):
                time.sleep(1.5)
                return
            if self._proc.poll() is not None:
                raise ErrorSesion(
                    "CoppeliaSim terminó durante el arranque (código %s). "
                    "Revisa %s" % (self._proc.returncode, self.log_path))
            time.sleep(0.5)
        raise ErrorSesion("El puerto %d no abrió en %.0f s."
                          % (self.puerto, self.arranque_s))

    def _conectar(self) -> None:
        self.client = RemoteAPIClient(host="127.0.0.1", port=self.puerto)
        self.sim = self.client.require("sim")
        _ = self.version  # falla pronto si el servidor no responde

    # --------------------------------------------------------------- ajustes
    @property
    def version(self) -> str:
        v = int(self.sim.getInt32Param(self.sim.intparam_program_version))
        return "%d.%d.%d" % (v // 10000, (v // 100) % 100, v % 100)

    def cargar_escena(self, ruta: str | os.PathLike[str]) -> None:
        ruta = Path(ruta).resolve()
        if not ruta.exists():
            raise ErrorSesion("No existe la escena: %s" % ruta)
        self.sim.loadScene(str(ruta))
        self.scene = ruta

    def fijar_motor(self, motor: str) -> str:
        objetivo = MOTORES[motor]
        self.sim.setInt32Param(self.sim.intparam_dynamic_engine, objetivo)
        leido = int(self.sim.getInt32Param(self.sim.intparam_dynamic_engine))
        if leido != objetivo:
            raise ErrorSesion(
                "El motor %s no quedó activo (quedó %s)."
                % (motor, MOTORES_INV.get(leido, leido)))
        return motor

    @property
    def motor(self) -> str:
        return MOTORES_INV.get(
            int(self.sim.getInt32Param(self.sim.intparam_dynamic_engine)), "?")

    def fijar_paso(self, dt: float) -> None:
        self.sim.setFloatParam(self.sim.floatparam_simulation_time_step, dt)
        self.dt = dt

    @property
    def paso_s(self) -> float:
        return float(self.sim.getFloatParam(
            self.sim.floatparam_simulation_time_step))

    # ----------------------------------------------------------- simulación
    @property
    def activa(self) -> bool:
        return self.sim.getSimulationState() != self.sim.simulation_stopped

    def start(self) -> None:
        self.sim.startSimulation()
        limite = time.time() + 15.0
        while time.time() < limite:
            if self.activa:
                return
            time.sleep(0.05)
        raise ErrorSesion("La simulación no arrancó.")

    def step(self, n: int = 1) -> None:
        """Avanza n pasos. El tiempo solo avanza aquí."""
        for _ in range(n):
            self.sim.step()

    @property
    def tiempo_s(self) -> float:
        return float(self.sim.getSimulationTime())

    def stop(self) -> None:
        if self.sim is None:
            return
        self.sim.stopSimulation()
        limite = time.time() + 15.0
        while time.time() < limite:
            if not self.activa:
                time.sleep(0.2)
                return
            time.sleep(0.05)

    # ---------------------------------------------------------------- cierre
    def cerrar(self) -> None:
        try:
            if self.sim is not None and self.activa:
                self.stop()
        except Exception:
            pass
        self.sim = None
        self.client = None
        if self._lanzado_por_mi and self._proc is not None:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            self._proc = None
        if self._log is not None:
            try:
                self._log.close()
            except Exception:
                pass
            self._log = None
