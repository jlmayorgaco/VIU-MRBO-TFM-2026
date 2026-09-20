"""Humo del banco: matriz de confusión del certificado contra la física.

Rejilla pequeña de casos donde masa y número de contactos hacen que el
certificado acepte unos y rechace otros. Se ejecutan TODOS, aceptados y
rechazados, que es lo que permite medir falsos positivos y falsos negativos.

Uso:
    python -u scripts/smoke_coppelia_banco.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from viu_mrob_tfm.coppelia import CoppeliaSession  # noqa: E402
from viu_mrob_tfm.coppelia.banco import Caso, evaluar_caso, wrench_demandado  # noqa: E402

# Contactos repartidos en el semicírculo trasero: todos pueden empujar en +x.
def angulos(n: int) -> tuple[float, ...]:
    if n == 1:
        return (math.pi,)
    span = 1.4
    return tuple(math.pi - span / 2 + span * i / (n - 1) for i in range(n))


CASOS = [
    Caso(masa_kg=5.0, angulos=angulos(1)),
    Caso(masa_kg=5.0, angulos=angulos(2)),
    Caso(masa_kg=14.0, angulos=angulos(2)),
    Caso(masa_kg=14.0, angulos=angulos(4)),
    Caso(masa_kg=28.0, angulos=angulos(3)),
    Caso(masa_kg=28.0, angulos=angulos(6)),
]


def main() -> int:
    print("Banco: certificado de wrench frente a verdad fisica")
    print("suelo con friccion 0.6, gravedad activa, MuJoCo, dt=0.005 s")
    print("objetivo: avanzar 1.00 m en +x en 4 s (tolerancia 0.15 m)\n")

    filas = []
    for caso in CASOS:
        w = wrench_demandado(caso)
        with CoppeliaSession(motor="mujoco", dt=0.005, headless=True) as ses:
            r = evaluar_caso(ses, caso)
        filas.append(r)
        print("  %-12s  wdem=%6.1f N  residuo=%.3f  %s"
              % (caso.etiqueta, w[0], r["residuo_rel"],
                 "ACEPTA" if r["acepta"] else "RECHAZA"))
        print("      avance %.3f m  giro %.2f rad  duty %.2f  transporta=%s"
              % (r["avance_x_m"], r["giro_rad"], r["duty_contacto"],
                 r["transporta"]))
        print("      wrench medido %s"
              % np.array2string(r["wrench_medido"], precision=1))
        print("      -> %s\n" % r["celda"])

    print("=" * 62)
    print("MATRIZ DE CONFUSION")
    print("=" * 62)
    cuenta = {"acierto+": 0, "FALSO POSITIVO": 0, "FALSO NEGATIVO": 0,
              "acierto-": 0}
    for r in filas:
        cuenta[r["celda"]] += 1
    print("                    fisica: transporta   fisica: falla")
    print("  cert. ACEPTA      %-19d %d"
          % (cuenta["acierto+"], cuenta["FALSO POSITIVO"]))
    print("  cert. RECHAZA     %-19d %d"
          % (cuenta["FALSO NEGATIVO"], cuenta["acierto-"]))
    n = len(filas)
    print()
    print("  casos: %d   falsos positivos: %d   falsos negativos: %d"
          % (n, cuenta["FALSO POSITIVO"], cuenta["FALSO NEGATIVO"]))

    duty_bajo = [r for r in filas if r["duty_contacto"] < 0.5]
    if duty_bajo:
        print()
        print("  AVISO: %d caso(s) con contacto por debajo del 50 %% del tiempo."
              % len(duty_bajo))
        print("  Su wrench medido no es comparable con el de contacto pleno.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
