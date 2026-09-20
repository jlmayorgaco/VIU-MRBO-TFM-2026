"""Humo de la cadena de medición de wrench.

Construye una escena dinámica mínima por API —suelo, sensor de fuerza y carga
respondable de masa conocida— y comprueba que el sensor lee el peso.

Es la prueba que decide si la campaña física puede medir algo. Si un sensor no
devuelve m*g con una masa en reposo, ningún residuo medido frente al predicho
significa nada.

Criterio: |Fz_medida| debe coincidir con m*g dentro del 2 %.

Uso:
    python -u scripts/smoke_coppelia_wrench.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from viu_mrob_tfm.coppelia import CoppeliaSession, ErrorSesion  # noqa: E402

G = 9.81
MASAS_KG = (5.0, 14.0, 28.0)   # las mismas clases de carga del escenario AWS
DT = 0.005
ASENTAMIENTO = 400             # pasos antes de medir (2 s)
MUESTRAS = 200                 # pasos de medición (1 s)
TOLERANCIA = 0.02


def construir(sim, masa_kg: float, lado: float = 0.30):
    """Suelo estático -> sensor de fuerza -> caja respondable de masa dada."""
    suelo = sim.createPrimitiveShape(sim.primitiveshape_cuboid, [2.0, 2.0, 0.10])
    sim.setObjectPosition(suelo, -1, [0.0, 0.0, -0.05])
    sim.setObjectInt32Param(suelo, sim.shapeintparam_respondable, 1)
    sim.setObjectInt32Param(suelo, sim.shapeintparam_static, 1)

    # createForceSensor(options, int[5], float[5]): filtro, tamano y umbrales.
    sensor = sim.createForceSensor(0, [0, 1, 0, 0, 0],
                                   [0.01, 0.0, 0.0, 0.0, 0.0])
    sim.setObjectPosition(sensor, -1, [0.0, 0.0, 0.0])
    sim.setObjectParent(sensor, suelo, True)

    caja = sim.createPrimitiveShape(sim.primitiveshape_cuboid,
                                    [lado, lado, lado])
    sim.setObjectPosition(caja, -1, [0.0, 0.0, lado / 2.0 + 0.002])
    sim.setObjectInt32Param(caja, sim.shapeintparam_respondable, 1)
    sim.setObjectInt32Param(caja, sim.shapeintparam_static, 0)
    sim.setShapeMass(caja, masa_kg)
    # La caja cuelga del sensor: todo su peso pasa por él.
    sim.setObjectParent(caja, sensor, True)
    return suelo, sensor, caja


def medir(masa_kg: float) -> dict[str, float]:
    with CoppeliaSession(motor="mujoco", dt=DT, headless=True) as ses:
        sim = ses.sim
        _, sensor, caja = construir(sim, masa_kg)
        ses.start()
        ses.step(ASENTAMIENTO)
        fz = []
        for _ in range(MUESTRAS):
            ses.step()
            lectura = sim.readForceSensor(sensor)
            # (estado, fuerza[3], par[3]) segun version; se toma la componente z
            if isinstance(lectura, (list, tuple)) and len(lectura) >= 2:
                fuerza = lectura[1]
                if fuerza and len(fuerza) >= 3:
                    fz.append(float(fuerza[2]))
        ses.stop()
    if not fz:
        raise ErrorSesion("El sensor no devolvio lecturas de fuerza.")
    medida = abs(statistics.median(fz))
    esperada = masa_kg * G
    return {
        "masa": masa_kg,
        "esperada_N": esperada,
        "medida_N": medida,
        "error_rel": abs(medida - esperada) / esperada,
        "desv_N": statistics.pstdev(fz),
        "n": len(fz),
    }


def main() -> int:
    print("Cadena de medicion de wrench: peso de una masa en reposo")
    print("motor MuJoCo, dt=%.3f s, %d pasos de asentamiento, %d muestras\n"
          % (DT, ASENTAMIENTO, MUESTRAS))
    filas = []
    for m in MASAS_KG:
        try:
            filas.append(medir(m))
        except Exception as exc:
            print("  masa %.1f kg -> FALLO: %s: %s" % (m, type(exc).__name__, exc))
            return 1

    print("  %-9s %-13s %-13s %-10s %s" % ("masa kg", "esperada N", "medida N",
                                           "error rel", "desv N"))
    for r in filas:
        print("  %-9.1f %-13.3f %-13.3f %-10.4f %.4f"
              % (r["masa"], r["esperada_N"], r["medida_N"], r["error_rel"],
                 r["desv_N"]))

    peor = max(r["error_rel"] for r in filas)
    print()
    if peor <= TOLERANCIA:
        print("VEREDICTO: cadena de medicion FIABLE (peor error %.2f %% <= %.0f %%)"
              % (100 * peor, 100 * TOLERANCIA))
        return 0
    print("VEREDICTO: cadena de medicion NO fiable (peor error %.2f %%)"
          % (100 * peor))
    return 2


if __name__ == "__main__":
    sys.exit(main())
