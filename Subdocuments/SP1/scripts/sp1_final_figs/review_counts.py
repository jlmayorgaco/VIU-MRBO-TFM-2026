# -*- coding: utf-8 -*-
"""Emite como macro los recuentos que el capitulo citaba a mano.

Lee solo RAW congelado; no re-ejecuta ninguna campana. Salida:
    generated/sp1-final/review_counts.tex
"""
from __future__ import annotations

import io
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LEV = os.path.join(REPO, "scripts", "results", "sp1_levels")
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "generated", "sp1-final",
                                   "review_counts.tex"))


def sep(n):
    """Separador de millar en formato LaTeX del capitulo."""
    return "{:,}".format(int(n)).replace(",", "\\,")


def dec(x, d=1):
    """Coma decimal espanola, y sin decimales que solo aportan un cero."""

    t = "%.*f" % (d, float(x))
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t.replace(".", "{,}")


lines = ["% Generado por scripts/sp1_final_figs/review_counts.py — no editar a mano."]

# ---------------------------------------------------------------- N4.E9
h = pd.read_csv(os.path.join(LEV, "n4_v4", "raw", "e9_hstar_runs.csv"))
main = h[h["block"] == "frozen_main"]
cat = main["hstar_category"].value_counts()
n_two, n_three, n_gt = int(cat.get("2", 0)), int(cat.get("3", 0)), int(cat.get(">3", 0))
lines += [
    "\\newcommand{\\NFourHStarWorldsN}{%s}" % sep(len(main)),
    "\\newcommand{\\NFourHStarTwoN}{%s}" % sep(n_two),
    "\\newcommand{\\NFourHStarThreeN}{%s}" % sep(n_three),
    "\\newcommand{\\NFourHStarGtThreeN}{%s}" % sep(n_gt),
]

# soporte con las tres brechas definidas
link = main.dropna(subset=["gap_br", "gap_2br", "gap_c3"])
lk = link["hstar_category"].value_counts()
lines += [
    "\\newcommand{\\NFourHStarLinkN}{%s}" % sep(len(link)),
    "\\newcommand{\\NFourHStarLinkTwoN}{%s}" % sep(int(lk.get("2", 0))),
    "\\newcommand{\\NFourHStarLinkThreeN}{%s}" % sep(int(lk.get("3", 0))),
    "\\newcommand{\\NFourHStarLinkGtThreeN}{%s}" % sep(int(lk.get(">3", 0))),
]

# ---------------------------------------------------------------- N4.E7
c = pd.read_csv(os.path.join(LEV, "n4_v3", "raw", "e7_cross_family_runs.csv"))
cert = c[(c["oracle_feasible"]) & (c["oracle_certified"])]

# soporte certificado: es el denominador de todas las cifras de este bloque
fii = cert[cert["method"].str.startswith("fii_")]
n_sup = fii["world_key"].nunique()
rate = fii.groupby("method")["feasible"].mean() * 100.0
NC = "\\newcommand{\\%s}{%s}"
lines += [
    NC % ("NFourContSupportN", sep(n_sup)),
    NC % ("NFourFiiRateMin", dec(rate.min(), 1)),
    NC % ("NFourFiiRateMax", dec(rate.max(), 1)),
]

pdv = cert[cert["method"] == "fiii_distributed_vgne_R"]
ok = int(pdv["feasible"].sum())
lines += [
    NC % ("NFourPdFeasibleN", sep(ok)),
    NC % ("NFourPdSupportN", sep(len(pdv))),
    NC % ("NFourPdFeasiblePct", dec(100.0 * ok / len(pdv))),
    NC % ("NFourPdClosedGapPct",
          dec(100.0 * pdv.loc[pdv["feasible"], "optimality_gap"].median())),
]

# mundos del experimento continuo completo (denominador del desajuste de orden)
lines.append(NC % ("NFourContWorldsN", sep(c["world_key"].nunique())))

# ------------------------------------------------------- sensibilidad de E9
#
# El RAW tiene DOS bloques de 1200 mundos con disenos distintos y no deben
# mezclarse en una misma frase:
#   frozen_main       N/K fijo en 3,2; barre CV y presion
#   ratio_sensitivity barre N/K en {2,3,4}
# Cada macro declara su bloque en el nombre.
NOESC = ">3"


def rate(frame, col, value):
    sub = frame[frame[col] == value]
    return 100.0 * (sub["hstar_category"] == NOESC).mean(), len(sub)


main_b = h[h["block"] == "frozen_main"]
ratio_b = h[h["block"] == "ratio_sensitivity"]

for cv, tag in ((0.0, "Zero"), (0.35, "Low"), (0.65, "Mid"), (1.0, "High")):
    p, n = rate(main_b, "capacity_cv", cv)
    lines.append(NC % ("NFourNoEscCv" + tag, dec(p)))
    lines.append(NC % ("NFourNoEscCv" + tag + "N", sep(n)))

for rho, tag in ((0.7, "Low"), (0.85, "High")):
    p, n = rate(main_b, "pressure", rho)
    lines.append(NC % ("NFourNoEscRho" + tag, dec(p)))
    lines.append(NC % ("NFourNoEscRho" + tag + "N", sep(n)))

for nk, tag in ((2.0, "Two"), (3.0, "Three"), (4.0, "Four")):
    p, n = rate(ratio_b, "robots_per_load", nk)
    lines.append(NC % ("NFourNoEscNk" + tag, dec(p)))
    lines.append(NC % ("NFourNoEscNk" + tag + "N", sep(n)))

lines.append(NC % ("NFourRatioBlockN", sep(len(ratio_b))))
lines.append(NC % ("NFourMainBlockNk", dec(float(main_b["robots_per_load"].iloc[0]), 1)))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("escrito:", OUT)
for line in lines[1:]:
    print("  ", line)
