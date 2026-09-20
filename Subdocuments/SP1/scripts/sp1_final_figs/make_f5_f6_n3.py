"""F5 y F6 — Coste de distribuir la decision (N3).

F5  Pareto calidad-comunicacion de las tres arquitecturas distribuidas.
    x = bytes/AMR (mediana)      y = brecha frente al MILP en SOPORTE COMUN
    tamano = factibilidad condicionada a que el oraculo declare factible.
    El soporte comun exige que los tres metodos entreguen coalicion factible
    y que el oraculo haya certificado el optimo en ese mundo.

F6  Robustez topologica y control negativo por particion permanente.
    Para las variantes GRAPE en particion, un perfil local medible a posteriori
    no cuenta como exito operacional si los perfiles no coinciden globalmente.

Todo procede de RAW congelado. No hay ningun valor medido escrito a mano.
"""
from __future__ import annotations

import collections
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
from thesis_style import (BASE_FS, apply_style, boot_ci, fbool, fnum, median, read_raw,  # noqa: E402
                          save, stamp, wilson_ci, C_BLUE, C_ORANGE, C_GREEN,
                          C_GRAY)

apply_style()

E2 = read_raw("n3_v2/raw/e2_runs.csv")
E3 = read_raw("n3_v2/raw/e3_runs.csv")

# Area del espacio de trabajo declarada por el generador de mundos
# (scripts/sp1_a1_hungarian.py: workspace_width = workspace_height = 100 m).
A_WORKSPACE = 100.0 * 100.0


def gamma_r(row):
    """Indice adimensional inspirado en la escala de conectividad RGG.

    Gamma_R = pi N R^2 / (A log N). Es un indice DIAGNOSTICO de densidad
    efectiva de comunicacion, no un umbral: la escala RGG supone puntos
    uniformes y cuatro de los cinco escenarios no lo son.
    """
    R = fnum(row.get("radius"))
    N = fnum(row.get("N"))
    if R is None or N is None or N <= 1:
        return None
    return math.pi * N * R * R / (A_WORKSPACE * math.log(N))


METHODS = ["capacity_cbba_rb", "weighted_grape", "weighted_pair_grape"]
MLABEL = {"capacity_cbba_rb": "CBBA-RB",
          "weighted_grape": "Weighted-GRAPE",
          "weighted_pair_grape": "Pair-GRAPE"}
MCOLOR = {"capacity_cbba_rb": C_BLUE,
          "weighted_grape": C_ORANGE,
          "weighted_pair_grape": C_GREEN}
REGIME_ORDER = ["complete", "dense", "medium", "threshold", "partitioned"]
RLABEL = {"complete": "Completo", "dense": "Denso", "medium": "Medio",
          "threshold": "Umbral", "partitioned": "Partición\n(control neg.)"}


def feasible(row) -> bool:
    return row.get("raw_certificate", "").upper() == "FEASIBLE"


# ============================================================ F5
by_world = collections.defaultdict(dict)
for r in E2:
    by_world[r["world_key"]][r["method"]] = r

oracle_ok = {w for w, d in by_world.items()
             if all(m in d for m in METHODS)
             and fbool(next(iter(d.values()))["oracle_feasible"])
             and fbool(next(iter(d.values()))["oracle_certified"])}
common = {w for w in oracle_ok if all(feasible(by_world[w][m]) for m in METHODS)}

f5_table = []
for m in METHODS:
    rows_all = [d[m] for d in by_world.values() if m in d]
    rows_or = [by_world[w][m] for w in oracle_ok]
    k = sum(1 for r in rows_or if feasible(r))
    p, plo, phi = wilson_ci(k, len(rows_or))
    gaps = [100 * fnum(by_world[w][m]["optimality_gap"]) for w in common]
    gaps = [g for g in gaps if g is not None]
    byts = [fnum(r["bytes_per_agent"]) for r in rows_all]
    glo, ghi = boot_ci(gaps)
    f5_table.append({
        "method": m, "label": MLABEL[m],
        "n_all": len(rows_all), "n_oracle_feasible": len(rows_or),
        "n_common_support": len(gaps),
        "feasibility_pct": round(100 * p, 2),
        "feasibility_ci_low": round(100 * plo, 2),
        "feasibility_ci_high": round(100 * phi, 2),
        "gap_median_pct": round(median(gaps), 3),
        "gap_ci_low": round(glo, 3), "gap_ci_high": round(ghi, 3),
        "bytes_per_amr_median": round(median(byts), 1),
    })

fig = plt.figure(figsize=(7.1, 3.5))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.32)
ax = fig.add_subplot(gs[0, 0])
for t in f5_table:
    m = t["method"]
    ax.errorbar(t["bytes_per_amr_median"], t["gap_median_pct"],
                yerr=[[t["gap_median_pct"] - t["gap_ci_low"]],
                      [t["gap_ci_high"] - t["gap_median_pct"]]],
                fmt="none", ecolor=MCOLOR[m], elinewidth=1.1, capsize=3, zorder=2)
    ax.scatter(t["bytes_per_amr_median"], t["gap_median_pct"],
               s=28 + 3.4 * t["feasibility_pct"], color=MCOLOR[m],
               alpha=0.85, linewidths=0, zorder=3)
    ax.annotate("%s\n%.1f %% factible" % (t["label"], t["feasibility_pct"]),
                (t["bytes_per_amr_median"], t["gap_median_pct"]),
                textcoords="offset points", xytext=(9, 9), fontsize=7.4,
                color="#333333")
ax.set_xscale("log")
ax.set_xlabel("bytes/AMR (mediana, escala log)")
ax.set_ylabel("brecha frente al MILP\nen soporte común [%]")
ax.set_title("A · Calidad frente a comunicación", loc="left")
ax.grid(alpha=0.55)
ax.margins(x=0.28, y=0.30)
ax.text(0.02, 0.03, "soporte común n = %d de %d mundos con óptimo certificado"
        % (len(common), len(oracle_ok)), transform=ax.transAxes,
        fontsize=7.0, color=C_GRAY)

axb = fig.add_subplot(gs[0, 1])
xs = [MLABEL[t["method"]] for t in f5_table]
ys = [t["feasibility_pct"] for t in f5_table]
lo = [t["feasibility_pct"] - t["feasibility_ci_low"] for t in f5_table]
hi = [t["feasibility_ci_high"] - t["feasibility_pct"] for t in f5_table]
axb.bar(xs, ys, color=[MCOLOR[t["method"]] for t in f5_table], alpha=0.85,
        width=0.6, yerr=[lo, hi], capsize=3, error_kw={"elinewidth": 1.0})
axb.set_ylabel("factibilidad | oráculo\nfactible [%]")
axb.set_title("B · Factibilidad condicionada", loc="left")
axb.set_ylim(0, 108)
axb.grid(axis="y", alpha=0.55)
axb.tick_params(axis="x", labelrotation=12)

stamp(fig, "n3_v2/e2_runs.csv")
save(fig, "f5_n3a_quality_communication", f5_table)

# ============================================================ F6
f6_table = []
for reg in REGIME_ORDER:
    for m in METHODS:
        rows = [r for r in E3 if r["graph_regime"] == reg and r["method"] == m]
        if not rows:
            continue
        oro = [r for r in rows if fbool(r["oracle_feasible"])]
        k = sum(1 for r in oro if feasible(r))
        p, plo, phi = wilson_ci(k, len(oro))
        byts = [fnum(r["bytes_per_agent"]) for r in rows]
        rnds = [fnum(r["rounds"]) for r in rows]
        f6_table.append({
            "graph_regime": reg, "method": m, "label": MLABEL[m],
            "n_runs": len(rows), "n_oracle_feasible": len(oro),
            "feasibility_pct": round(100 * p, 2),
            "ci_low": round(100 * plo, 2), "ci_high": round(100 * phi, 2),
            "bytes_per_amr_median": round(median(byts), 1),
            "rounds_median": round(median(rnds), 1) if rnds else "",
            "graph_connected": rows[0]["graph_connected"],
        })

fig = plt.figure(figsize=(7.1, 5.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05],
                      width_ratios=[1.25, 1.0], hspace=0.52,
                      wspace=0.30)
axA = fig.add_subplot(gs[0, 0])
w = 0.26
for i, m in enumerate(METHODS):
    sub = [t for t in f6_table if t["method"] == m]
    order = {t["graph_regime"]: t for t in sub}
    xs = [j + (i - 1) * w for j in range(len(REGIME_ORDER))]
    ys = [order[r]["feasibility_pct"] if r in order else 0 for r in REGIME_ORDER]
    el = [order[r]["feasibility_pct"] - order[r]["ci_low"] if r in order else 0
          for r in REGIME_ORDER]
    eh = [order[r]["ci_high"] - order[r]["feasibility_pct"] if r in order else 0
          for r in REGIME_ORDER]
    axA.bar(xs, ys, width=w, color=MCOLOR[m], alpha=0.85, label=MLABEL[m],
            yerr=[el, eh], capsize=2, error_kw={"elinewidth": 0.8})
axA.axvspan(len(REGIME_ORDER) - 1.5, len(REGIME_ORDER) - 0.5,
            color=C_GRAY, alpha=0.08, zorder=0)
# En particion no hay perfil global acordado: lo que se mide es una cobertura
# verificable a posteriori, no un exito operacional comparable al resto.
axA.annotate("verificación\npost hoc:\nsin acuerdo\nglobal",
             xy=(len(REGIME_ORDER) - 1.0, 78), ha="center", va="center",
             fontsize=BASE_FS - 1.6, color=C_GRAY, linespacing=1.25)
axA.set_xticks(range(len(REGIME_ORDER)), [RLABEL[r] for r in REGIME_ORDER])
axA.set_ylabel("factibilidad | oráculo\nfactible [%]")
axA.set_title("A · Factibilidad por régimen de conectividad", loc="left")
axA.set_ylim(0, 106)
axA.grid(axis="y", alpha=0.55)
axA.legend(ncol=3, loc="lower left", bbox_to_anchor=(0.0, -0.42),
           columnspacing=1.0, handletextpad=0.4)

axB = fig.add_subplot(gs[0, 1])
for m in METHODS:
    sub = {t["graph_regime"]: t for t in f6_table if t["method"] == m}
    xs = [i for i, r in enumerate(REGIME_ORDER) if r in sub]
    ys = [sub[REGIME_ORDER[i]]["bytes_per_amr_median"] for i in xs]
    axB.plot(xs, ys, marker="o", color=MCOLOR[m], label=MLABEL[m],
             markerfacecolor="white", markeredgewidth=1.2)
axB.set_xticks(range(len(REGIME_ORDER)),
               [RLABEL[r].split("\n")[0] for r in REGIME_ORDER])
axB.set_yscale("log")
axB.set_ylabel("bytes/AMR (mediana, log)")
axB.set_title("B · Coste de comunicación", loc="left")
axB.grid(alpha=0.55)
axB.tick_params(axis="x", labelrotation=18)


# ---- Panel C: densidad efectiva de comunicacion frente a lambda_2 ----------
GREG = {"threshold": "Umbral", "medium": "Medio", "dense": "Denso",
        "partitioned": "Particion"}
GCOL = {"threshold": C_BLUE, "medium": C_ORANGE, "dense": C_GREEN,
        "partitioned": C_GRAY}

axC = fig.add_subplot(gs[1, :])
seen_world = {}
for r in E3:
    key = (r["world_key"], r["graph_regime"])
    if key in seen_world:
        continue
    g = gamma_r(r)
    lam = fnum(r["graph_lambda_2"])
    if g is None or lam is None:
        continue
    seen_world[key] = (r["graph_regime"], r["scenario"], g, lam)

# Solo grafos conexos: con el grafo partido lambda_2 vale cero exactamente y
# no tiene lugar en un eje logaritmico.
n_part = 0
for reg in ("threshold", "medium", "dense"):
    pts = [(g, lam) for rg, _s, g, lam in seen_world.values() if rg == reg]
    if not pts:
        continue
    axC.scatter([q[0] for q in pts], [q[1] for q in pts],
                s=9, alpha=0.45, linewidths=0, color=GCOL[reg],
                label=GREG[reg])
n_part = sum(1 for rg, _s, _g, _l in seen_world.values() if rg == "partitioned")
axC.annotate(r"partición: $\lambda_2=0$ (n=%d), fuera del eje" % n_part,
             xy=(0.015, 0.06), xycoords="axes fraction", fontsize=BASE_FS - 1.0,
             color=C_GRAY)
axC.set_xscale("log")
axC.set_yscale("log")
axC.set_xlabel(r"$\Gamma_R=\pi N R^{2}/(A\log N)$  ·  densidad efectiva "
               r"de comunicación")
axC.set_ylabel(r"$\lambda_2$ del grafo")
axC.set_title(r"C · $\lambda_2$ frente a $\Gamma_R$, por régimen", loc="left")
axC.grid(alpha=0.55, which="both")
axC.legend(ncol=3, loc="lower right", columnspacing=1.0, handletextpad=0.3,
           markerscale=2.2)

for reg, scen, g, lam in seen_world.values():
    f6_table.append({
        "graph_regime": reg, "method": "gamma_r", "label": scen,
        "n_runs": "", "n_oracle_feasible": "", "feasibility_pct": "",
        "ci_low": "", "ci_high": "", "bytes_per_amr_median": round(g, 4),
        "rounds_median": round(lam, 6), "graph_connected": "",
    })

stamp(fig, "n3_v2/e3_runs.csv")
save(fig, "f6_n3c_topology_robustness", f6_table)

print("   F5 soporte comun: %d de %d mundos con oraculo certificado"
      % (len(common), len(oracle_ok)))
for t in f5_table:
    print("      %-16s brecha %5.1f %% | bytes/AMR %8.0f | factible %5.1f %%"
          % (t["label"], t["gap_median_pct"], t["bytes_per_amr_median"],
             t["feasibility_pct"]))
print("   F6 regimenes: %s" % ", ".join(REGIME_ORDER))
for reg in REGIME_ORDER:
    vals = [(t["label"], t["feasibility_pct"]) for t in f6_table
            if t["graph_regime"] == reg]
    # f6_table mezcla filas por metodo y filas por mundo; solo las primeras
    # traen una tasa numerica, el resto llega como cadena vacia.
    shown = ["%s %.1f%%" % (lab, float(pct))
             for lab, pct in vals if str(pct).strip() != ""]
    print("      %-12s %s" % (reg, "  ".join(shown)))
