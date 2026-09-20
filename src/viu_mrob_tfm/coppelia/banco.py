"""Banco experimental: certificado de wrench frente a verdad física.

Corrige el error de diseño de la primera versión, que usaba gravedad cero
«para aislar el certificado». Sin suelo no hay fricción de apoyo, y sin
resistencia la pregunta «¿puede esta coalición transportar la carga?» no está
bien planteada: cualquier fuerza neta mueve la carga. La fricción de apoyo
(μ·m·g) no era un estorbo, era el problema.

Diseño:

* Carga apoyada en el suelo, con gravedad y fricción declaradas.
* El wrench demandado se **deriva de un objetivo**: la fuerza necesaria para
  vencer la fricción de apoyo más la que produce la aceleración pedida hacia la
  pose destino. No se fija a ojo.
* El certificador decide ACEPTA/RECHAZA sobre ese wrench.
* La física ejecuta las fuerzas del certificador y dice si la carga llega.
* **También se ejecutan las coaliciones rechazadas**: sin esa fila no hay tasa
  de falsos negativos y el certificado queda ilustrado, no medido.

Unidades SI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .escena import Carga, Contacto, EscenaTransporte

G = 9.81


@dataclass(frozen=True)
class Caso:
    masa_kg: float
    angulos: tuple[float, ...]
    fuerza_max_N: float = 40.0
    friccion_suelo: float = 0.6
    friccion_contacto: float = 0.6
    distancia_objetivo_m: float = 0.30
    margen_arranque: float = 0.60
    tolerancia_m: float = 0.10
    duracion_s: float = 4.0
    umbral_residuo: float = 0.05

    @property
    def etiqueta(self) -> str:
        return "m=%.0fkg n=%d" % (self.masa_kg, len(self.angulos))


def wrench_demandado(caso: Caso) -> np.ndarray:
    """Wrench de la tarea: vencer el apoyo con un margen de arranque declarado.

    F = (1 + margen) * mu * m * g

    El intento anterior usaba mu*m*g + m*a con a = 0,25 m/s2: para 5 kg eso son
    29,4 N de friccion y solo 1,25 N de margen, un 4 %. Con ese margen ninguna
    coalicion transportaba y la columna «fisica: transporta» quedaba vacia, de
    modo que la matriz no discriminaba nada. El margen se declara ahora de
    forma explicita y es un factor del diseno.
    """
    friccion_N = caso.friccion_suelo * caso.masa_kg * G
    return np.array([(1.0 + caso.margen_arranque) * friccion_N, 0.0, 0.0],
                    dtype=float)


def evaluar_certificado(esc: EscenaTransporte, w_dem: np.ndarray,
                        umbral: float) -> dict[str, Any]:
    """Decisión del certificador tal cual está implementado en sp1_geo."""
    from ..sp1_geo.certifier import bounded_wrench_residual

    A = np.array(esc.matriz_agarre(), dtype=float)
    cotas = np.array(esc.cotas_fuerza(), dtype=float)
    res_si, res_rel, fuerzas = bounded_wrench_residual(A.T, cotas, w_dem)
    return {
        "acepta": bool(res_rel <= umbral),
        "residuo_rel": float(res_rel),
        "residuo_si": float(res_si),
        "fuerzas": np.asarray(fuerzas, dtype=float),
        "wrench_predicho": A @ fuerzas,
    }


def ejecutar_fisica(sesion: Any, caso: Caso, fuerzas: np.ndarray) -> dict[str, Any]:
    """Aplica las fuerzas del certificador y mide qué ocurre de verdad."""
    sim = sesion.sim
    contactos = tuple(
        Contacto(angulo_rad=a, fuerza_max_N=caso.fuerza_max_N)
        for a in caso.angulos)
    esc = EscenaTransporte(
        carga=Carga(masa_kg=caso.masa_kg),
        contactos=contactos,
        friccion=caso.friccion_contacto,
        gravedad_cero=False,
    )
    esc.construir(sim)
    sesion.start()

    dt = sesion.paso_s
    pasos_asentar = int(round(0.5 / dt))
    pasos = int(round(caso.duracion_s / dt))

    for _ in range(pasos_asentar):
        sesion.step()

    p0 = esc.pose_carga(sim)
    con_contacto = 0
    wrench_muestras = []
    for _ in range(pasos):
        esc.aplicar_fuerzas(sim, list(fuerzas))
        sesion.step()
        n = esc.contacto_establecido(sim)
        if n > 0:
            con_contacto += 1
            wrench_muestras.append(esc.wrench_medido(sim))
    p1 = esc.pose_carga(sim)
    sesion.stop()

    avance_x = p1[0] - p0[0]
    desplazamiento = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    duty = con_contacto / max(pasos, 1)
    wm = (np.median(np.array(wrench_muestras, dtype=float), axis=0)
          if wrench_muestras else np.zeros(3))

    llega = avance_x >= (caso.distancia_objetivo_m - caso.tolerancia_m)
    return {
        "avance_x_m": float(avance_x),
        "desplazamiento_m": float(desplazamiento),
        "giro_rad": float(abs(p1[2] - p0[2])),
        "duty_contacto": float(duty),
        "wrench_medido": wm,
        "n_muestras_con_contacto": len(wrench_muestras),
        "transporta": bool(llega),
    }


def evaluar_caso(sesion: Any, caso: Caso) -> dict[str, Any]:
    """Una celda de la matriz de confusión: predicción y verdad física."""
    contactos = tuple(
        Contacto(angulo_rad=a, fuerza_max_N=caso.fuerza_max_N)
        for a in caso.angulos)
    esc_geom = EscenaTransporte(
        carga=Carga(masa_kg=caso.masa_kg), contactos=contactos)

    w_dem = wrench_demandado(caso)
    cert = evaluar_certificado(esc_geom, w_dem, caso.umbral_residuo)

    # Las coaliciones RECHAZADAS también se ejecutan: es lo que da la tasa de
    # falsos negativos. Se aplican las mejores fuerzas que el LSQ pudo hallar.
    fis = ejecutar_fisica(sesion, caso, cert["fuerzas"])

    if cert["acepta"] and fis["transporta"]:
        celda = "acierto+"
    elif cert["acepta"] and not fis["transporta"]:
        celda = "FALSO POSITIVO"
    elif (not cert["acepta"]) and fis["transporta"]:
        celda = "FALSO NEGATIVO"
    else:
        celda = "acierto-"

    salida = {"caso": caso, "wrench_demandado": w_dem, "celda": celda}
    salida.update(cert)
    salida.update(fis)
    return salida
