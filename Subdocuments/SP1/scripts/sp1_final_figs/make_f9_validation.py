"""F9 y F10 — las dos campanas de validacion, una figura cada una.

La version anterior metia cuatro paneles en una figura y en A4 los tres ultimos
quedaban al limite de lo legible. Se separan.

F9  N3.B, factorial con brazo de control
    A  brecha mediana de las doce celdas; la fila 2BR es el control con h = 2
    B  factibilidad condicionada de las mismas doce celdas
    C  efecto pareado de pasar de h = 1 a h = 2, por fitness, sobre los mismos
       mundos

F10 hold-out industrial
    A  brecha mediana por planta
    B  factibilidad condicionada con IC de Wilson
    C  primer escape conectado en los dos bancos
    D  brecha frente a dispersion relativa de las distancias, que es la variable
       que ordena las cuatro plantas
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from thesis_style import (apply_style, save, C_BLUE, C_ORANGE, C_GREEN,  # noqa: E402
                          C_GRAY, C_RED)

apply_style()

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(SP1, "..", ".."))
LEV = os.path.join(REPO, "scripts", "results", "sp1_levels")


def load(*p):
    with io.open(os.path.join(LEV, *p), encoding="utf-8") as fh:
        return json.load(fh)


b = load("n3b_v2", "raw", "n3b_analysis.json")
h = load("n4_holdout_v1", "raw", "n4_holdout_analysis.json")
try:
    mech = load("n4_holdout_v1", "raw", "mechanism.json")
except OSError:
    mech = None

ROWS = ("BR", "ASR", "LLL", "2BR")
FIT = ("F0", "F1", "F2")
LAYOUT = {"cross_aisle": "Pasillos\ncruzados",
          "parallel_aisles": "Pasillos\nparalelos",
          "docks_staging": "Muelles y\npreparación",
          "open_bottleneck": "Áreas con\npaso estrecho"}

# =========================================================== F9 · N3.B
fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(12.4, 3.9))

gap = np.array([[b["cells"]["%s-%s" % (r, f)]["gap_median_pct"] for f in FIT]
                for r in ROWS])
im = axA.imshow(gap, cmap="YlOrRd", aspect="auto", vmin=0.0,
                vmax=float(gap.max()) * 1.05)
for i in range(len(ROWS)):
    for j in range(len(FIT)):
        v = gap[i, j]
        axA.text(j, i, "%.1f" % v, ha="center", va="center", fontsize=9,
                 color="white" if v > gap.max() * 0.6 else "black")
axA.set_xticks(range(3), FIT)
axA.set_yticks(range(4), ["BR\n$h=1$", "ASR\n$h=1$", "LLL\n$h=1$",
                          "2BR\n$h=2$"], fontsize=8)
axA.axhline(2.5, color="black", lw=1.4)
axA.set_title("A · Brecha mediana (%%)\nsobre %s mundos de soporte común"
              % b["n_common_support"], loc="left", fontsize=9)
axA.set_xlabel("función de mérito")
fig.colorbar(im, ax=axA, fraction=0.046, pad=0.03)

feas = np.array([[b["cells"]["%s-%s" % (r, f)]["feasibility_pct"] for f in FIT]
                 for r in ROWS])
im2 = axB.imshow(feas, cmap="YlGn", aspect="auto", vmin=80.0, vmax=100.0)
for i in range(len(ROWS)):
    for j in range(len(FIT)):
        axB.text(j, i, "%.1f" % feas[i, j], ha="center", va="center",
                 fontsize=9, color="black")
axB.set_xticks(range(3), FIT)
axB.set_yticks(range(4), ["BR", "ASR", "LLL", "2BR"], fontsize=8)
axB.axhline(2.5, color="black", lw=1.4)
axB.set_title("B · Factibilidad condicionada (%)", loc="left", fontsize=9)
axB.set_xlabel("función de mérito")
fig.colorbar(im2, ax=axB, fraction=0.046, pad=0.03)

pe = b["paired_order_effect"]["by_fitness"]
xs = np.arange(len(FIT))
med = [pe[f]["median_pp"] for f in FIT]
err = [[med[i] - pe[f]["ci_low"] for i, f in enumerate(FIT)],
       [pe[f]["ci_high"] - med[i] for i, f in enumerate(FIT)]]
axC.axhline(0.0, color=C_GRAY, lw=1.0, ls="--")
axC.errorbar(xs, med, yerr=err, fmt="o", color=C_BLUE, capsize=4, ms=7)
for i, f in enumerate(FIT):
    axC.annotate("n=%d\n%.0f %% mejor" % (pe[f]["n_paired"],
                                          pe[f]["worlds_h2_better_pct"]),
                 (xs[i], med[i]), textcoords="offset points",
                 xytext=(12, -4), fontsize=7)
axC.set_xticks(xs, FIT)
axC.set_xlim(-0.5, 2.9)
axC.set_ylabel("2BR menos BR (puntos)")
axC.set_xlabel("función de mérito")
axC.set_title("C · Efecto pareado de $h=1\\rightarrow h=2$", loc="left",
              fontsize=9)

t9 = []
for r in ROWS:
    for f in FIT:
        c = b["cells"]["%s-%s" % (r, f)]
        t9.append({"panel": "A/B", "rule": r, "fitness": f,
                   "gap_median_pct": c["gap_median_pct"],
                   "feasibility_pct": c["feasibility_pct"]})
for f in FIT:
    d = pe[f]
    t9.append({"panel": "C", "fitness": f, "n_paired": d["n_paired"],
               "median_pp": d["median_pp"], "ci_low": d["ci_low"],
               "ci_high": d["ci_high"],
               "worlds_h2_better_pct": d["worlds_h2_better_pct"]})
fig.tight_layout()
save(fig, "f9_n3b_factorial", t9)

# ================================================= F10 · hold-out industrial
fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.0))
axA, axB, axD = axes

layouts = list(h["by_layout"].keys())
x = np.arange(len(layouts))
w = 0.26
for k, (tag, colour) in enumerate((("BR", C_BLUE), ("2BR", C_ORANGE),
                                   ("C3", C_GREEN))):
    axA.bar(x + (k - 1) * w, [h["by_layout"][ly][tag] for ly in layouts], w,
            color=colour, label=tag)
axA.set_xticks(x, [LAYOUT[ly] for ly in layouts], fontsize=7)
axA.set_ylabel("brecha mediana (%)")
axA.set_title("A · Brecha por planta", loc="left", fontsize=9)
axA.legend(fontsize=7, frameon=False)

tags = ["BR", "2BR", "C3", "DMIS+TX", "CBBA-RB", "Pair-GRAPE"]
pcts = [h["methods"][t]["feasibility_pct"] for t in tags]
lo = [p - h["methods"][t]["feas_ci_low"] for t, p in zip(tags, pcts)]
hi = [h["methods"][t]["feas_ci_high"] - p for t, p in zip(tags, pcts)]
axB.barh(range(len(tags)), pcts, color=C_GRAY, height=0.6)
axB.errorbar(pcts, range(len(tags)), xerr=[lo, hi], fmt="none",
             ecolor="black", elinewidth=0.9, capsize=2)
axB.set_yticks(range(len(tags)), tags, fontsize=7)
axB.invert_yaxis()
axB.set_xlim(0, 105)
axB.set_xlabel("factibilidad condicionada (%)")
axB.set_title("B · Factibilidad", loc="left", fontsize=9)

if mech:
    sp = [mech["by_layout"][ly]["dist_spread"] for ly in layouts]
    gp = [mech["by_layout"][ly]["gap_2br_median"] for ly in layouts]
    axD.scatter(sp, gp, s=60, color=C_ORANGE, zorder=3)
    for ly, a, c in zip(layouts, sp, gp):
        axD.annotate(LAYOUT[ly].replace("\n", " "), (a, c), fontsize=6.5,
                     textcoords="offset points", xytext=(6, -3))
    axD.set_xlabel("dispersión relativa de $d_{ik}$")
    axD.set_ylabel("brecha mediana de 2BR (%)")
    axD.set_xlim(0.0, 1.45)
    _rho = ("%.2f" % mech["correlations"]["dist_spread"]).replace(".", ",")
    axD.set_title("C · Qué hace dura una planta\n($\\rho$ de Spearman = %s)"
                  % _rho, loc="left", fontsize=9)

t10 = []
for ly in layouts:
    e = h["by_layout"][ly]
    row = {"panel": "A", "layout": ly, "n_common": e["n_common"],
           "BR": e["BR"], "2BR": e["2BR"], "C3": e["C3"]}
    if mech:
        row["dist_spread"] = mech["by_layout"][ly]["dist_spread"]
    t10.append(row)
for t in tags:
    m = h["methods"][t]
    t10.append({"panel": "B", "method": t,
                "feasibility_pct": m["feasibility_pct"],
                "ci_low": m["feas_ci_low"], "ci_high": m["feas_ci_high"]})
# El primer escape conectado se dibuja en la Figura 7; aqui solo se
# conserva en la tabla fuente para que el dato siga siendo trazable.
cats = ["2", "3", ">3"]
dev_counts = {"2": 1156, "3": 4, ">3": 40}
dev_total = sum(dev_counts.values())
for c in cats:
    t10.append({"panel": "anexo", "category": c,
                "development_pct": 100.0 * dev_counts[c] / dev_total,
                "industrial_pct": h["hstar"]["pct"].get(c, 0.0)})
fig.tight_layout()
save(fig, "f10_holdout_industrial", t10)
