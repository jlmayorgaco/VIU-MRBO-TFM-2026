"""Genera paper/sec_ensayo_cierre_resultados.tex a partir de results/megajuego/SUMMARY.json."""
import json, os, sys, csv, math
import numpy as np

LAB = {"protocolos": "Protocolo de revisión", "aptitud": "Aptitud", "pasillo": "Pasillo", "seguridad": "Seguridad",
       "reclutamiento": "Reclutamiento", "hiperjuego": "Hiperjuego (margen holgado)", "hiperjuego2": "Hiperjuego (margen vinculante)", "planificador": "Planificador de trayectoria"}
NAME = {"best_response": "mejor respuesta", "smith": "Smith", "bnn": "BNN", "logit": "logit", "replicator": "imitación (replicador)",
        "vector": "vector (margen de \\emph{wrench})", "scalar": "escalar (suma de capacidades)", "lease": "arrendamiento exclusivo",
        "price": "precio de congestión", "nested": "anidada", "coalition": "solo coalición", "none": "ninguna", "atomic": "atómico",
        "gne_pd": "GNE primal--dual", "True": "sí", "False": "no", "waypoint": "seguidor de puntos de espera", "game": "juego continuo de trayectorias"}


def fmt(x, d=1):
    s = f"{x:.{d}f}".replace(".", "{,}"); return f"${s}$"


def cfg_label(grid, cfg):
    if grid == "protocolos": return NAME[cfg["cfg_protocol"]]
    if grid == "aptitud": return NAME[cfg["cfg_fitness"]]
    if grid == "pasillo": return NAME[cfg["cfg_corridor"]]
    if grid == "seguridad": return NAME[cfg["cfg_safety"]]
    if grid == "reclutamiento": return NAME[cfg["cfg_recruit"]]
    if grid == "planificador": return NAME[cfg["cfg_planner"]]
    if grid in ("hiperjuego", "hiperjuego2"): return f"error $\\pm{int(float(cfg['cfg_belief_err']) * 100)}\\%$, recertifica: {NAME[cfg['cfg_recertify']]}"
    return str(cfg)


def main(summary="results/megajuego/SUMMARY.json", out="paper/sec_ensayo_cierre_resultados.tex"):
    S = json.load(open(summary, encoding="utf-8"))
    L = []
    L.append("\\subsection{Resultados}\n")
    L.append("Cada fila es una configuración sobre semillas comunes; el McNemar es pareado frente a la referencia (Smith, vector, arrendamiento, anidada, atómico, creencias exactas).\n")
    for grid in ["protocolos", "aptitud", "planificador", "pasillo", "seguridad", "reclutamiento", "hiperjuego", "hiperjuego2"]:
        rows = [s for s in S if s["grid"] == grid]
        if not rows: continue
        L.append("\\begin{center}\\small\n\\begin{tabular}{@{}lrrrrrrrr@{}}\n\\toprule")
        L.append(f"{LAB[grid]} & Éxito & IC$_{{95}}$ & $T$ [s] & $E$ [Wh] & sep.\\ mín.\\ [m] & mensajes & revisiones & McNemar \\\\\n\\midrule")
        for s in rows:
            lo, hi = s["ci"]
            mc = f"{s['vs_ref_better']}/{s['vs_ref_worse']}, $p={s['mcnemar_p']:.3f}$".replace(".", "{,}") if s['vs_ref_better'] + s['vs_ref_worse'] > 0 else "—"
            L.append(f"{cfg_label(grid, s['cfg'])} & ${s['success']}/{s['n']}$ & {fmt(lo, 2)}--{fmt(hi, 2)} & {fmt(s['makespan_med'], 0)} & {fmt(s['energy_med'], 1)} & {fmt(s['minsep_med'], 2)} & {fmt(s['msgs_med'] / 1000, 0)}k & {fmt(s['rev_med'], 0)} & {mc} \\\\")
        L.append("\\bottomrule\n\\end{tabular}\n\\end{center}\n")
        if grid in ("hiperjuego", "hiperjuego2"):
            L.append("Certificados falsos (coalición certificada con creencias que no lo estaba con capacidades reales) y rechazos por recertificación, sumados sobre semillas: " +
                     "; ".join(f"{cfg_label(grid, s['cfg'])}: ${s['false_cert']}$ falsos, ${s['recert']}$ rechazos" for s in rows) + ".\n")
        if grid == "pasillo":
            L.append("Tiempo mediano con dos cargas dentro del hueco: " + "; ".join(f"{cfg_label(grid, s['cfg'])} {fmt(s['corridor_double_med'], 1)}~s" for s in rows) + ".\n")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print("escrito", out, len(L), "líneas")


if __name__ == "__main__":
    main(*sys.argv[1:])
