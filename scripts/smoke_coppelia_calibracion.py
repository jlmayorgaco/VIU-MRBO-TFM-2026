"""Calibración del transmisor de fuerza: ¿llega al contacto lo que se manda?

Carga **estática**: no puede moverse, así que toda la fuerza del empujador
aparece como fuerza de contacto. Es la prueba que aísla la transmisión de la
dinámica de la carga.

Sin este cierre, ningún número del banco vale: la primera matriz de confusión
dio 4 falsos positivos de 6 que eran puro rozamiento de los empujadores.

Criterio: |F_medida - F_mandada| / F_mandada <= 5 % para cada fuerza ensayada.

Uso:
    python -u scripts/smoke_coppelia_calibracion.py
"""
from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from viu_mrob_tfm.coppelia import CoppeliaSession  # noqa: E402
from viu_mrob_tfm.coppelia.escena import Carga, Contacto, EscenaTransporte  # noqa: E402

DT = 0.005
ASENTAR = 200
MUESTRAS = 300
FUERZAS_N = (10.0, 20.0, 30.0, 40.0)
TOLERANCIA = 0.05


def medir(f_mandada: float, compensar: bool) -> dict[str, float]:
    esc = EscenaTransporte(
        carga=Carga(masa_kg=14.0),
        contactos=(Contacto(angulo_rad=math.pi),),
        gravedad_cero=False,
        carga_estatica=True,        # la carga no se mueve: aisla la transmision
        compensar_apoyo=compensar,
    )
    with CoppeliaSession(motor="mujoco", dt=DT, headless=True) as ses:
        sim = ses.sim
        esc.construir(sim)
        ses.start()
        for _ in range(ASENTAR):
            esc.aplicar_fuerzas(sim, [f_mandada])
            ses.step()
        fx = []
        for _ in range(MUESTRAS):
            esc.aplicar_fuerzas(sim, [f_mandada])
            ses.step()
            w = esc.wrench_medido(sim)
            fx.append(abs(w[0]))
        ses.stop()
    medida = statistics.median(fx) if fx else 0.0
    return {
        "mandada": f_mandada,
        "medida": medida,
        "error_rel": abs(medida - f_mandada) / f_mandada,
    }


def main() -> int:
    print("Calibracion del transmisor: carga estatica, un contacto")
    print("MuJoCo, dt=%.3f s, friccion 0.6, empujador 2 kg\n" % DT)

    for compensar in (False, True):
        etiqueta = "CON compensacion" if compensar else "SIN compensacion"
        print("  --- %s ---" % etiqueta)
        print("  %-11s %-11s %s" % ("mandada N", "medida N", "error rel"))
        filas = []
        for f in FUERZAS_N:
            try:
                r = medir(f, compensar)
            except Exception as exc:
                print("    %.1f -> FALLO %s: %s" % (f, type(exc).__name__, exc))
                return 1
            filas.append(r)
            print("  %-11.1f %-11.2f %.4f"
                  % (r["mandada"], r["medida"], r["error_rel"]))
        peor = max(r["error_rel"] for r in filas)
        print("  peor error: %.2f %%\n" % (100 * peor))
        if compensar:
            if peor <= TOLERANCIA:
                print("VEREDICTO: transmisor CALIBRADO (%.2f %% <= %.0f %%)."
                      % (100 * peor, 100 * TOLERANCIA))
                print("El banco ya puede medir el certificado y no su montaje.")
                return 0
            print("VEREDICTO: NO calibrado (peor error %.2f %%)." % (100 * peor))
            print("La compensacion mu*m_pad*g no basta: queda fisica sin modelar.")
            return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
