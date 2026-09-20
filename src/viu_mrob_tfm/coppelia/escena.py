"""Escena dinámica de transporte cooperativo planar.

Construye por API la escena mínima que permite refutar el certificado de wrench:
una carga respondable y N empujadores que le transmiten fuerza **por contacto**,
no aplicándola a su centro de masas. Esa diferencia es el objeto del
experimento: el certificador (`sp1_geo/certifier.py`) resuelve un mínimos
cuadrados acotado con fuerzas unilaterales y no modela conos de fricción ni
pérdida de contacto. Aquí ambas cosas existen.

Diseño del banco aislado (`gravedad_cero=True`, por defecto):

* Sin suelo y sin gravedad. La única física que actúa sobre la carga son los
  contactos de los empujadores, que es exactamente lo que el certificado
  pretende describir. Con suelo, la fricción de apoyo (μ·m·g ≈ 82 N para 14 kg)
  domina sobre el wrench pedido y enmascara lo que se quiere medir.
* Movimiento planar: la carga y los empujadores solo tienen sentido en XY.

Correcciones respecto a la primera versión, que no medía nada:

1. Los empujadores abarcan la altura de la cara de la carga. Antes eran cubos
   de 0,10 m flotando a media altura de una carga de 0,32 m: caían al suelo y
   empujaban al aire.
2. Los contactos se leen filtrados por pareja empujador↔carga. Antes se sumaban
   también los contactos carga↔suelo, que no forman parte del agarre.
3. `contacto_establecido()` permite abortar un caso sin contacto en vez de
   producir ceros que parecen datos.

Unidades SI: m, kg, N, N·m, s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

G = 9.81


@dataclass(frozen=True)
class Carga:
    masa_kg: float
    largo_m: float = 0.62
    ancho_m: float = 0.46
    alto_m: float = 0.32

    @property
    def dims(self) -> list[float]:
        return [self.largo_m, self.ancho_m, self.alto_m]


@dataclass(frozen=True)
class Contacto:
    """Punto de empuje sobre el borde de la carga, en el marco de la carga.

    La dirección de empuje es hacia el centro: es la única que un contacto
    unilateral puede ejercer sin adherencia.
    """
    angulo_rad: float
    fuerza_max_N: float = 40.0
    ancho_m: float = 0.10


@dataclass
class EscenaTransporte:
    carga: Carga
    contactos: tuple[Contacto, ...]
    friccion: float = 0.6
    holgura_m: float = 0.001
    masa_empujador_kg: float = 2.0
    gravedad_cero: bool = True
    compensar_apoyo: bool = True
    carga_estatica: bool = False
    handles: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------- geometría
    def punto_contacto(self, c: Contacto) -> tuple[float, float]:
        a, b = self.carga.largo_m / 2.0, self.carga.ancho_m / 2.0
        cx, cy = math.cos(c.angulo_rad), math.sin(c.angulo_rad)
        t = min(a / abs(cx) if abs(cx) > 1e-9 else math.inf,
                b / abs(cy) if abs(cy) > 1e-9 else math.inf)
        return t * cx, t * cy

    def columna_wrench(self, c: Contacto) -> tuple[float, float, float]:
        """Columna (fx, fy, tau) de una fuerza unitaria empujando hacia dentro.

        Es la misma columna que usa el certificador, para que predicción y
        medición hablen del mismo objeto.
        """
        px, py = self.punto_contacto(c)
        nx, ny = -math.cos(c.angulo_rad), -math.sin(c.angulo_rad)
        return nx, ny, px * ny - py * nx

    def matriz_agarre(self) -> list[list[float]]:
        cols = [self.columna_wrench(c) for c in self.contactos]
        return [[c[i] for c in cols] for i in range(3)]

    def cotas_fuerza(self) -> list[float]:
        return [c.fuerza_max_N for c in self.contactos]

    # -------------------------------------------------------------- montaje
    def construir(self, sim: Any) -> dict[str, Any]:
        h: dict[str, Any] = {}
        z = self.carga.alto_m / 2.0

        if self.gravedad_cero:
            sim.setArrayParam(sim.arrayparam_gravity, [0.0, 0.0, 0.0])
        else:
            sim.setArrayParam(sim.arrayparam_gravity, [0.0, 0.0, -G])
            suelo = sim.createPrimitiveShape(
                sim.primitiveshape_cuboid, [8.0, 8.0, 0.10])
            sim.setObjectPosition(suelo, -1, [0.0, 0.0, -0.05])
            sim.setObjectInt32Param(suelo, sim.shapeintparam_respondable, 1)
            sim.setObjectInt32Param(suelo, sim.shapeintparam_static, 1)
            sim.setObjectAlias(suelo, "suelo")
            # Mascaras: bit global 0x0100. El empujador (0x0200) no lo
            # comparte, asi que no colisiona con el suelo.
            sim.setObjectInt32Param(
                suelo, sim.shapeintparam_respondable_mask, 0xFF01)
            self._fijar_friccion(sim, suelo)
            h["suelo"] = suelo

        carga = sim.createPrimitiveShape(sim.primitiveshape_cuboid, self.carga.dims)
        sim.setObjectPosition(carga, -1, [0.0, 0.0, z])
        sim.setObjectInt32Param(carga, sim.shapeintparam_respondable, 1)
        sim.setObjectInt32Param(carga, sim.shapeintparam_static,
                                1 if self.carga_estatica else 0)
        sim.setShapeMass(carga, self.carga.masa_kg)
        sim.setObjectAlias(carga, "carga")
        # La carga comparte bit con el suelo (0x01) y con el empujador (0x02).
        sim.setObjectInt32Param(
            carga, sim.shapeintparam_respondable_mask, 0xFF03)
        self._fijar_friccion(sim, carga)
        h["carga"] = carga

        empujadores = []
        for i, c in enumerate(self.contactos):
            px, py = self.punto_contacto(c)
            grosor = c.ancho_m
            # El empujador abarca la altura de la carga: contacto de cara plena.
            dims = [grosor, c.ancho_m, self.carga.alto_m]
            ex = px + math.cos(c.angulo_rad) * (grosor / 2.0 + self.holgura_m)
            ey = py + math.sin(c.angulo_rad) * (grosor / 2.0 + self.holgura_m)
            pad = sim.createPrimitiveShape(sim.primitiveshape_cuboid, dims)
            sim.setObjectPosition(pad, -1, [ex, ey, z])
            sim.setObjectOrientation(pad, -1, [0.0, 0.0, c.angulo_rad])
            sim.setObjectInt32Param(pad, sim.shapeintparam_respondable, 1)
            sim.setObjectInt32Param(pad, sim.shapeintparam_static, 0)
            sim.setShapeMass(pad, self.masa_empujador_kg)
            sim.setObjectAlias(pad, "empujador_%d" % i)
            # Solo el bit 0x02: colisiona con la carga, nunca con el suelo.
            sim.setObjectInt32Param(
                pad, sim.shapeintparam_respondable_mask, 0xFF02)
            self._fijar_friccion(sim, pad)
            empujadores.append(pad)
        h["empujadores"] = empujadores

        self.handles = h
        return h

    def _fijar_friccion(self, sim: Any, handle: int) -> None:
        for nombre in ("mujoco_body_friction1", "mujoco_body_friction2",
                       "mujoco_body_friction3"):
            param = getattr(sim, nombre, None)
            if param is not None:
                try:
                    sim.setEngineFloatParam(param, handle, self.friccion)
                except Exception:
                    pass

    # ------------------------------------------------------------- dinámica
    def aplicar_fuerzas(self, sim: Any, fuerzas_N: list[float]) -> None:
        """Aplica a cada empujador su fuerza, dirigida hacia el centro.

        La fuerza llega a la carga a través del contacto: si el cono de fricción
        no la admite, o el contacto se pierde, la carga no la recibe. Eso es lo
        que el certificador no puede ver.
        """
        if len(fuerzas_N) != len(self.contactos):
            raise ValueError("Se esperaban %d fuerzas, llegaron %d"
                             % (len(self.contactos), len(fuerzas_N)))
        # El certificador prescribe fuerzas EN EL CONTACTO, y el empujador
        # representa el punto de contacto, no el vehiculo con sus perdidas.
        # Por eso el empujador no colisiona con el suelo (mascaras) y se le
        # sostiene contra la gravedad: asi, en regimen, la fuerza mandada llega
        # integra al contacto.
        #
        # El intento anterior --restar mu*m_pad*g-- era erroneo: con el
        # empujador quieto contra la carga el rozamiento del suelo es estatico
        # e indeterminado, no mu*N. Compensarlo con una constante empeoro el
        # error del 65 % al 80 %.
        sustentacion = (self.masa_empujador_kg * G
                        if not self.gravedad_cero else 0.0)
        for pad, c, f in zip(self.handles["empujadores"], self.contactos, fuerzas_N):
            fx = -math.cos(c.angulo_rad) * float(f)
            fy = -math.sin(c.angulo_rad) * float(f)
            sim.addForceAndTorque(pad, [fx, fy, sustentacion], [0.0, 0.0, 0.0])

    def pose_carga(self, sim: Any) -> tuple[float, float, float]:
        x, y, _ = sim.getObjectPosition(self.handles["carga"], -1)
        _, _, yaw = sim.getObjectOrientation(self.handles["carga"], -1)
        return float(x), float(y), float(yaw)

    # ---------------------------------------------------------- instrumentos
    def _contactos_agarre(self, sim: Any) -> list[tuple[list[float], list[float]]]:
        """Contactos empujador↔carga, filtrados por pareja de handles.

        `getContactInfo` devuelve (pareja, posicion, fuerza, normal) e incluye
        cualquier contacto de la carga. Sin filtrar, el apoyo en el suelo
        contaminaría el wrench de agarre.
        """
        carga = self.handles["carga"]
        pads = set(self.handles["empujadores"])
        fuera = []
        for idx in range(64):
            info = sim.getContactInfo(sim.handle_all, carga, idx)
            if not info or len(info) < 3 or not info[0]:
                break
            pareja = list(info[0])
            if any(p in pads for p in pareja):
                fuera.append((list(info[1]), list(info[2])))
        return fuera

    def contacto_establecido(self, sim: Any) -> int:
        """Número de contactos empujador↔carga activos."""
        return len(self._contactos_agarre(sim))

    def wrench_medido(self, sim: Any) -> tuple[float, float, float]:
        """Wrench planar que la carga recibe realmente de los empujadores."""
        cx, cy, _ = self.pose_carga(sim)
        fx = fy = tau = 0.0
        for punto, fuerza in self._contactos_agarre(sim):
            if len(punto) < 2 or len(fuerza) < 2:
                continue
            rx, ry = float(punto[0]) - cx, float(punto[1]) - cy
            fx += float(fuerza[0])
            fy += float(fuerza[1])
            tau += rx * float(fuerza[1]) - ry * float(fuerza[0])
        return fx, fy, tau
