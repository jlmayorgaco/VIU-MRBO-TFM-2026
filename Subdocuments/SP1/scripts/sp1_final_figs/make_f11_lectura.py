"""F11 — lectura conceptual de SP1 en una sola figura.

Cuatro paneles que reunen cinco campanas distintas. La idea es que el lector vea
de una vez las cuatro magnitudes que el capitulo separa y que hasta ahora solo
aparecian como cifras dispersas en el texto:

A  la escalera de optimalidad, con las dos perdidas en el MISMO eje: lo que se
   pierde por exigir enteros y lo que se pierde por limitar el orden h
B  esa misma escalera frente a lo que cuesta en comunicacion
C  regla de revision y funcion de merito no son el mismo objeto
D  exigir que el grupo que se mueve pueda hablarse tiene un precio propio, que
   decae al densificar el grafo

Fuentes: n2 (integralidad), n4_v2 via f7 (orden), n3b_v2 (factorial),
n4_poc_v1 (conectividad), f5 (metodos de N3).
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from thesis_style import (apply_style, save, C_BLUE, C_ORANGE, C_GREEN,  # noqa: E402
                          C_GRAY, C_RED, C_PURPLE)

apply_style()

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN = os.path.join(SP1, "generated", "sp1-final")
REPO = os.path.abspath(os.path.join(SP1, "..", ".."))
LEV = os.path.join(REPO, "scripts", "results", "sp1_levels")


def jload(*p):
    with io.open(os.path.join(LEV, *p), encoding="utf-8") as fh:
        return json.load(fh)


def cload(name):
    with io.open(os.path.join(GEN, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


f7 = cload("f7_n4_strategic_order.csv")
f5 = cload("f5_n3a_quality_communication.csv")
n3b = jload("n3b_v2", "raw", "n3b_analysis.json")
poc = jload("n4_poc_v1", "raw", "poc_analysis.json")

ORDERS = [("BR", "$h=1$"), ("2BR", "$h=2$"), ("C3", "$h=3$")]
row = {r["label"].replace("\n", " ").split()[0]: r for r in f7
       if r["panel"] == "A/B"}
gap = {k: float(row[k]["gap_median_pct"]) for k, _ in ORDERS}
byt = {k: float(row[k]["bytes_per_amr_median"]) for k, _ in ORDERS}

# Brecha de integralidad de N2: el optimo continuo queda por DEBAJO del entero.
LP_BELOW = 18.0
for r in cload("f4_n2_atomicity_map.csv"):
    if r["campaign"] == "atomicity" and r["capacity_cv"] == "0.65" \
            and r["pressure"] == "0.85":
        break

fig, (axA, axB, axD) = plt.subplots(1, 3, figsize=(12.8, 4.0))

# ------------------------------------------------- A · escalera de optimalidad
labels = ["LP\nrelajado", "MILP\nentero", "BR\n$h=1$", "2BR\n$h=2$", "C3\n$h=3$"]
vals = [-LP_BELOW, 0.0, gap["BR"], gap["2BR"], gap["C3"]]
cols = [C_PURPLE, C_GRAY, C_BLUE, C_ORANGE, C_GREEN]
axA.axhline(0.0, color=C_GRAY, lw=1.2)
axA.bar(range(5), vals, color=cols, width=0.62)
for i, v in enumerate(vals):
    axA.text(i, v + (2.0 if v >= 0 else -4.0), ("%.1f" % v).replace(".", ","),
             ha="center", va="bottom" if v >= 0 else "top", fontsize=8)
axA.set_xticks(range(5), labels, fontsize=7.5)
axA.set_ylabel("distancia al óptimo entero (%)")
axA.set_ylim(-34, 72)
axA.set_title("A · Brecha de relajación y precio de la localidad",
              loc="left", fontsize=9)
# Las etiquetas van fuera de las barras para no pisar los valores.
axA.text(0.0, -26.0, "brecha de\nrelajación", fontsize=7.5,
         ha="center", va="top", color=C_PURPLE)
axA.annotate("precio de la localidad", xy=(2.0, 52.0), xytext=(3.4, 63.0),
             fontsize=7.5, ha="center", color=C_BLUE,
             arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=0.8))

# --------------------------------------------- B · lo que cuesta coordinarse
for k, lab in ORDERS:
    axB.scatter(byt[k], gap[k], s=90, zorder=3,
                color={"BR": C_BLUE, "2BR": C_ORANGE, "C3": C_GREEN}[k])
    axB.annotate("%s %s" % (k, lab), (byt[k], gap[k]), fontsize=7.5,
                 textcoords="offset points", xytext=(8, 4))
axB.plot([byt[k] for k, _ in ORDERS], [gap[k] for k, _ in ORDERS],
         color=C_GRAY, lw=1.0, ls="--", zorder=1)
for r in f5:
    axB.scatter(float(r["bytes_per_amr_median"]), float(r["gap_median_pct"]),
                s=42, color=C_GRAY, marker="^", zorder=2)
    axB.annotate(r["label"], (float(r["bytes_per_amr_median"]),
                              float(r["gap_median_pct"])), fontsize=6.5,
                 color="#555555", textcoords="offset points", xytext=(6, -8))
axB.set_xscale("log")
axB.set_xlabel("bytes por AMR (escala logarítmica)")
axB.set_ylabel("brecha mediana (%)")
axB.set_title("B · Cada peldaño se paga en comunicación\n(campañas distintas: lectura descriptiva)", loc="left",
              fontsize=9)

# ------------------------------------------ D · el precio de la conectividad
regs = [r for r in ("partitioned", "threshold", "medium", "dense", "complete")
        if r in poc["by_regime"]]
deg = [poc["by_regime"][r]["mean_degree"] for r in regs]
aff = [poc["by_regime"][r]["affected_pct"] for r in regs]
NAME = {"partitioned": "partido", "threshold": "umbral", "medium": "medio",
        "dense": "denso", "complete": "completo"}
axD.plot(deg, aff, marker="o", color=C_RED, lw=1.6, zorder=3)
for r, x, y in zip(regs, deg, aff):
    axD.annotate(NAME[r], (x, y), fontsize=7, textcoords="offset points",
                 xytext=(6, 5))
axD.set_xlabel("grado medio del grafo de comunicación")
axD.set_ylabel("terminales afectados (%)")
axD.set_ylim(-0.25, max(aff) * 1.5 + 0.4)
axD.set_title("C · Exigir que el grupo pueda hablarse tiene precio propio",
              loc="left", fontsize=9)

table = []
for lab, v in zip(["LP relajado", "MILP", "BR h=1", "2BR h=2", "C3 h=3"], vals):
    table.append({"panel": "A", "nivel": lab, "distancia_al_milp_pct": v})
for k, _ in ORDERS:
    table.append({"panel": "B", "metodo": k, "gap_pct": gap[k],
                  "bytes_per_amr": byt[k]})
# El factorial se dibuja en la Figura 9; aqui solo se conserva su dato.
RULES, FIT = ("BR", "ASR", "LLL"), ("F0", "F1", "F2")
for r in RULES:
    for f in FIT:
        table.append({"panel": "anexo", "regla": r, "fitness": f,
                      "gap_pct": n3b["cells"]["%s-%s" % (r, f)]
                      ["gap_median_pct"]})
for r in regs:
    e = poc["by_regime"][r]
    table.append({"panel": "D", "regimen": r, "mean_degree": e["mean_degree"],
                  "with_improvement": e["with_improvement"],
                  "blocked": e["blocked"], "delayed": e["delayed"],
                  "affected_pct": e["affected_pct"]})

fig.tight_layout()
save(fig, "f11_lectura_conceptual", table)
