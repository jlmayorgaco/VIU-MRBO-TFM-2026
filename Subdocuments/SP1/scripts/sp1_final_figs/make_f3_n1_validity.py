"""F3 — Frontera de validez de la reduccion por cardinalidad (N1).

Panel A  CV realizado x geometria -> P(falso positivo de factibilidad), IC Wilson.
Panel B  severidad: deficit relativo de la peor carga, condicionado a que el
         evento de falso positivo haya ocurrido.
Panel C  control estructural: acuerdo LSAP/MILP en el limite homogeneo.

Un falso positivo de factibilidad es una coalicion aceptada por el modelo de
cardinalidad de N1 que incumple la restriccion real de capacidad agregada.

Todo procede de RAW congelado. No hay ningun valor medido escrito a mano.
"""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
from thesis_style import (SCEN_COLORS, SCEN_LABEL, SCEN_MARKER, apply_style,  # noqa: E402
                          fbool, fnum, median, read_raw, save, stamp,
                          wilson_ci, C_GRAY, C_ORANGE, C_BLUE)

apply_style()

HET = read_raw("n1_v2/raw/heterogeneity_runs.csv")
HOM = read_raw("n2_v1/raw/homogeneous_limit_runs.csv")

# Orden nominal de heterogeneidad tal como lo fija la campana.
LABEL_ORDER = ["Homogénea", "Baja", "Moderada", "Alta", "Extrema"]
SCEN_ORDER = ["uniform", "clustered", "separated", "ring", "corridor"]

# ---------------------------------------------------------------- agregacion
cells = collections.defaultdict(list)
for r in HET:
    cells[(r["scenario"], r["capacity_label"])].append(r)

table = []
for scen in SCEN_ORDER:
    for lab in LABEL_ORDER:
        rows = cells.get((scen, lab), [])
        if not rows:
            continue
        n = len(rows)
        k = sum(1 for r in rows if fbool(r["hungarian_false_feasible"]))
        p, lo, hi = wilson_ci(k, n)
        cv_real = median([fnum(r["capacity_cv"]) for r in rows])
        # Severidad solo sobre los eventos de falso positivo.
        sev = [fnum(r["hungarian_relative_deficit"]) for r in rows
               if fbool(r["hungarian_false_feasible"])]
        table.append({
            "scenario": scen,
            "scenario_label": SCEN_LABEL[scen],
            "capacity_label": lab,
            "n_worlds": n,
            "cv_realised_median": round(cv_real, 4) if cv_real is not None else "",
            "false_positive_count": k,
            "false_positive_rate": round(p, 4),
            "ci95_low": round(lo, 4),
            "ci95_high": round(hi, 4),
            "severity_median_rel_deficit": (round(median(sev), 4)
                                            if sev else ""),
            "severity_n": len(sev),
        })

# ------------------------------------------------------------------- figura
fig = plt.figure(figsize=(7.1, 5.5))
gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1.0], hspace=0.42, wspace=0.28)

axA = fig.add_subplot(gs[0, :])
for scen in SCEN_ORDER:
    pts = [t for t in table if t["scenario"] == scen]
    xs = [t["cv_realised_median"] for t in pts]
    ys = [100 * t["false_positive_rate"] for t in pts]
    lo = [100 * t["ci95_low"] for t in pts]
    hi = [100 * t["ci95_high"] for t in pts]
    axA.fill_between(xs, lo, hi, color=SCEN_COLORS[scen], alpha=0.10, linewidth=0)
    axA.plot(xs, ys, marker=SCEN_MARKER[scen], color=SCEN_COLORS[scen],
             label=SCEN_LABEL[scen], markerfacecolor="white",
             markeredgewidth=1.2)
axA.set_xlabel(r"CV realizado de la capacidad, $\mathrm{CV}(c_i^{\mathrm{pay}})$")
axA.set_ylabel("Falsos positivos de\nfactibilidad [%]")
axA.set_title("A · Falsos positivos por geometría y nivel de dispersión",
              loc="left")
axA.set_ylim(-4, 104)
axA.grid(axis="y", alpha=0.6)
axA.legend(ncol=5, loc="lower right", columnspacing=1.1, handletextpad=0.4)

axB = fig.add_subplot(gs[1, 0])
xs, ys, cs = [], [], []
for lab in LABEL_ORDER:
    rows = [r for r in HET if r["capacity_label"] == lab
            and fbool(r["hungarian_false_feasible"])]
    if not rows:
        continue
    xs.append(lab)
    ys.append(100 * median([fnum(r["hungarian_relative_deficit"]) for r in rows]))
    cs.append(len(rows))
bars = axB.bar(xs, ys, color=C_ORANGE, alpha=0.85, width=0.62)
for b, c in zip(bars, cs):
    axB.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, "n=%d" % c,
             ha="center", va="bottom", fontsize=6.2, color=C_GRAY)
axB.set_ylabel("Déficit relativo\nde la peor carga [%]")
axB.set_title("B · Severidad cuando el modelo falla", loc="left")
axB.grid(axis="y", alpha=0.6)
axB.tick_params(axis="x", labelrotation=18)

axC = fig.add_subplot(gs[1, 1])
err = [fnum(r["distance_absolute_error"]) for r in HOM]
err = [e for e in err if e is not None]
agree = sum(1 for r in HOM if fbool(r["feasibility_agrees"]))
card = sum(1 for r in HOM if fbool(r["cardinality_matches"]))
axC.hist(err, bins=24, color=C_BLUE, alpha=0.85)
axC.set_xlabel(r"$|J_{\mathrm{LSAP}}-J_{\mathrm{MILP}}|$  [m]")
axC.set_ylabel("mundos")
axC.set_title("C · Límite homogéneo: comprobación estructural", loc="left")
axC.grid(axis="y", alpha=0.6)
axC.text(0.97, 0.92,
         "acuerdo %d/%d\ncardinalidad %d/%d" % (agree, len(HOM), card, len(HOM)),
         transform=axC.transAxes, ha="right", va="top", fontsize=7.0,
         color=C_GRAY)

stamp(fig, "n1_v2/heterogeneity_runs.csv + n2_v1/homogeneous_limit_runs.csv")
save(fig, "f3_n1_validity_boundary", table)

# resumen para el informe de checkpoint
print("   celdas: %d | mundos por celda: %s"
      % (len(table), sorted({t["n_worlds"] for t in table})))
for lab in LABEL_ORDER:
    sub = [t for t in table if t["capacity_label"] == lab]
    rates = [100 * t["false_positive_rate"] for t in sub]
    print("   %-10s CV~%.2f  falsos positivos por geometria: %s"
          % (lab, median([t["cv_realised_median"] for t in sub]),
             " ".join("%5.1f" % v for v in rates)))
