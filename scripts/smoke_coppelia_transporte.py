"""Humo de la escena de transporte: ¿llega a la carga el wrench pedido?

Monta la escena dinámica, pide al certificador las fuerzas por contacto para un
wrench demandado y mide lo que la carga recibe de verdad a través de los
contactos.

La diferencia entre lo pedido y lo recibido es el objeto del experimento: el
certificador resuelve un LSQ acotado sin conos de fricción ni pérdida de
contacto, y aquí ambas cosas existen.

Uso:
    python -u scripts/smoke_coppelia_transporte.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from viu_mrob_tfm.coppelia import CoppeliaSession  # noqa: E402
from viu_mrob_tfm.coppelia.escena import Carga, Contacto, EscenaTransporte  # noqa: E402
from viu_mrob_tfm.sp1_geo.certifier import bounded_wrench_residual  # noqa: E402

DT = 0.005
ASENTAMIENTO = 300
EMPUJE = 400


def caso(masa_kg: float, angulos: tuple[float, ...], wrench_dem: tuple[float, float, float]):
    contactos = tuple(Contacto(angulo_rad=a) for a in angulos)
    esc = EscenaTransporte(carga=Carga(masa_kg=masa_kg), contactos=contactos)

    A = np.array(esc.matriz_agarre(), dtype=float)
    cotas = np.array(esc.cotas_fuerza(), dtype=float)
    dem = np.array(wrench_dem, dtype=float)

    # El certificador trabaja con columnas por contacto (m x 3).
    res_si, res_rel, fuerzas = bounded_wrench_residual(A.T, cotas, dem)

    with CoppeliaSession(motor="mujoco", dt=DT, headless=True) as ses:
        sim = ses.sim
        esc.construir(sim)
        ses.start()
        # Con gravedad cero no hay asentamiento: se empuja unos pasos para
        # establecer contacto y se comprueba antes de medir nada.
        for _ in range(60):
            esc.aplicar_fuerzas(sim, [1.0] * len(contactos))
            ses.step()
        n_contactos_activos = esc.contacto_establecido(sim)
        if n_contactos_activos == 0:
            ses.stop()
            raise RuntimeError('sin contacto empujador-carga: el caso no mide nada')
        p0 = esc.pose_carga(sim)
        medidos = []
        for _ in range(EMPUJE):
            esc.aplicar_fuerzas(sim, list(fuerzas))
            ses.step()
            medidos.append(esc.wrench_medido(sim))
        p1 = esc.pose_carga(sim)
        ses.stop()

    med = np.median(np.array(medidos, dtype=float), axis=0) if medidos else np.zeros(3)
    predicho = A @ fuerzas
    desplazamiento = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    giro = abs(p1[2] - p0[2])
    return {
        "masa": masa_kg,
        "n_contactos": len(contactos),
        "demandado": dem,
        "predicho": predicho,
        "medido": med,
        "fuerzas": fuerzas,
        "residuo_rel_certificado": res_rel,
        "desplazamiento_m": desplazamiento,
        "giro_rad": giro,
        "contactos_activos": n_contactos_activos,
    }


def main() -> int:
    print("Escena de transporte: wrench pedido frente a wrench recibido")
    print("motor MuJoCo, dt=%.3f s, %d pasos de empuje\n" % (DT, EMPUJE))

    casos = [
        ("2 contactos opuestos, empuje +x", 14.0,
         (math.pi, 0.0), (60.0, 0.0, 0.0)),
        ("3 contactos, empuje +x", 14.0,
         (math.pi, 2.0, -2.0), (60.0, 0.0, 0.0)),
        ("3 contactos, empuje diagonal", 14.0,
         (math.pi, 2.0, -2.0), (45.0, 45.0, 0.0)),
    ]

    for etiqueta, masa, angs, w in casos:
        try:
            r = caso(masa, angs, w)
        except Exception as exc:
            print("  %-34s FALLO %s: %s" % (etiqueta, type(exc).__name__, exc))
            return 1
        print("  %s" % etiqueta)
        print("    fuerzas del certificado (N) : %s"
              % np.array2string(r["fuerzas"], precision=2))
        print("    residuo relativo certificado: %.4f" % r["residuo_rel_certificado"])
        print("    wrench demandado            : %s"
              % np.array2string(r["demandado"], precision=2))
        print("    wrench predicho (A f)       : %s"
              % np.array2string(r["predicho"], precision=2))
        print("    wrench MEDIDO por contacto  : %s"
              % np.array2string(r["medido"], precision=2))
        print("    contactos activos           : %d" % r["contactos_activos"])
        print("    desplazamiento / giro       : %.4f m / %.4f rad"
              % (r["desplazamiento_m"], r["giro_rad"]))
        print()

    print("Lectura: si el medido se aparta del predicho, el certificado esta")
    print("prometiendo un wrench que el contacto real no entrega. Esa brecha es")
    print("exactamente lo que la campana tiene que cuantificar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
