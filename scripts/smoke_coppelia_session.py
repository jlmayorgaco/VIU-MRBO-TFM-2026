"""Humo del runner de sesión de CoppeliaSim.

Comprueba lo que hace falta para que una campaña física sea posible:

  1. la sesión arranca, conecta y acepta modo síncrono;
  2. el motor dinámico está activo;
  3. el tiempo avanza EXACTAMENTE un paso por disparo del cliente;
  4. la sesión cierra dejando el servidor utilizable;
  5. una SEGUNDA sesión abre sin bloquearse.

El punto 5 es el que importa: una simulación síncrona sin parar deja el
servidor esperando disparos y la conexión siguiente muere. Sin esto no hay
campaña, solo ejecuciones sueltas.

Uso:
    python -u scripts/smoke_coppelia_session.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from viu_mrob_tfm.coppelia import CoppeliaSession, ErrorSesion  # noqa: E402

PASOS = 20


def una_sesion(etiqueta: str) -> dict[str, object]:
    with CoppeliaSession(headless=True, motor="mujoco", dt=0.005) as ses:
        motor = ses.motor
        dt = ses.paso_s
        version = ses.version
        ses.start()
        t0 = ses.tiempo_s
        tiempos = []
        for _ in range(PASOS):
            ses.step()
            tiempos.append(ses.tiempo_s)
        saltos = [round(tiempos[i + 1] - tiempos[i], 5) for i in range(len(tiempos) - 1)]
        ses.stop()
        activa_tras_stop = ses.activa

    unicos = sorted(set(saltos))
    return {
        "etiqueta": etiqueta,
        "motor": motor,
        "version": version,
        "dt": dt,
        "t0": t0,
        "t_final": tiempos[-1],
        "saltos_unicos": unicos,
        "avance_total": round(tiempos[-1] - t0, 5),
        "activa_tras_stop": activa_tras_stop,
    }


def main() -> int:
    resultados = []
    for etiqueta in ("primera", "segunda"):
        print("--- sesion %s ---" % etiqueta)
        try:
            r = una_sesion(etiqueta)
        except ErrorSesion as exc:
            print("  FALLO: %s" % exc)
            return 1
        resultados.append(r)
        print("  version CoppeliaSim: %s" % r["version"])
        print("  motor dinamico     : %s" % r["motor"])
        print("  paso declarado     : %.4f s" % r["dt"])
        print("  t inicial / final  : %.3f -> %.3f s" % (r["t0"], r["t_final"]))
        print("  saltos por disparo : %s" % r["saltos_unicos"])
        print("  avance en %d pasos : %.3f s" % (PASOS, r["avance_total"]))
        print("  activa tras stop   : %s" % r["activa_tras_stop"])

    print()
    fallos = []
    for r in resultados:
        if r["activa_tras_stop"]:
            fallos.append("%s: la simulacion sigue activa tras stop()" % r["etiqueta"])
        if r["avance_total"] <= 0:
            fallos.append("%s: el tiempo no avanzo" % r["etiqueta"])
        # t0 se lee antes del primer disparo: N pasos avanzan N*dt.
        esperado = round(r["dt"] * PASOS, 5)
        if abs(r["avance_total"] - esperado) > 1e-6:
            fallos.append(
                "%s: avance %.3f s, esperado %.3f s (un paso por disparo)"
                % (r["etiqueta"], r["avance_total"], esperado))

    if fallos:
        print("VEREDICTO: NO operativo")
        for f in fallos:
            print("  - %s" % f)
        return 2

    print("VEREDICTO: runner OPERATIVO")
    print("  Dos sesiones consecutivas, avance determinista de un paso por")
    print("  disparo y cierre limpio. La campana fisica es viable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
