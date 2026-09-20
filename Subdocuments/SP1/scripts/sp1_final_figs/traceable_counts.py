# -*- coding: utf-8 -*-
"""Emite como macro las cifras que el capitulo todavia escribia a mano.

Segunda revision de tribunal, hallazgo 12: once cifras de prosa existian como
dato generado y aun asi estaban tecleadas. Este script las saca de los CSV
congelados que ya alimentan las figuras, de modo que texto y figura no puedan
divergir.

Lee solo `generated/sp1-final/*.csv` y el RAW de N4. No re-ejecuta ninguna
campana. Salida: generated/sp1-final/traceable_counts.tex
"""
from __future__ import annotations

import csv
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN = os.path.join(SP1, "generated", "sp1-final")
REPO = os.path.abspath(os.path.join(SP1, "..", ".."))
RAW4 = os.path.join(REPO, "scripts", "results", "sp1_levels", "n4_v2", "raw",
                    "e4_family_runs.csv")
OUT = os.path.join(GEN, "traceable_counts.tex")

NC = "\\newcommand{\\%s}{%s}"


def dec(x, d=1):
    """Coma decimal espanola, y sin decimales que solo aportan un cero."""

    t = "%.*f" % (d, float(x))
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t.replace(".", "{,}")


def sep(n):
    return "{:,}".format(int(n)).replace(",", "\\,")


def load(name):
    with io.open(os.path.join(GEN, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


lines = ["% Generado por scripts/sp1_final_figs/traceable_counts.py — no editar."]

# ------------------------------------------------------------------ N1 (f3)
n1 = load("f3_n1_validity_boundary.csv")
per_cell = [r for r in n1 if r["n_worlds"]]
lines.append(NC % ("NOneWorldsPerCell", sep(per_cell[0]["n_worlds"])))


def severity_median(level):
    vals = sorted(float(r["severity_median_rel_deficit"]) for r in per_cell
                  if r["capacity_label"] == level
                  and r["severity_median_rel_deficit"])
    return 100.0 * vals[len(vals) // 2]


# Mediana ENTRE geometrias de la severidad mediana de cada una: una sola
# agregacion para los dos extremos del barrido, no una mezcla de mediana y
# maximo como estaba escrito a mano.
lines.append(NC % ("NOneSeverityLow", dec(severity_median("Baja"))))
lines.append(NC % ("NOneSeverityExtreme", dec(severity_median("Extrema"))))

# ------------------------------------------------------------------ N2 (f4)
n2 = load("f4_n2_atomicity_map.csv")
atom = [r for r in n2 if r["campaign"] == "atomicity"]
phase = [r for r in n2 if r["campaign"] == "phase_diagram"]

CV_TAG = {"0.0": "CvZeroRho", "0.15": "CvLowRho", "0.35": "CvMidRho",
          "0.65": "CvHighRho", "1.0": "CvOneRho"}
for r in atom:
    if r["pressure"] == "0.7" and r["capacity_cv"] in CV_TAG:
        lines.append(NC % ("NTwoGap" + CV_TAG[r["capacity_cv"]],
                           dec(r["gap_median_pct"])))

for r in phase:
    if r["capacity_cv"] == "0.0" and r["pressure"] == "0.85":
        lines.append(NC % ("NTwoCertHomogeneousHighRho",
                           dec(r["milp_certified_pct"])))

lp_only = [(r["capacity_cv"], int(r["lp_feasible_milp_infeasible"]))
           for r in atom if int(r["lp_feasible_milp_infeasible"]) > 0]
lp_only.sort(key=lambda t: -t[1])
lines.append(NC % ("NTwoLpOnlyTopN", sep(lp_only[0][1])))
lines.append(NC % ("NTwoLpOnlyRestN", sep(sum(n for _, n in lp_only[1:]))))

# ------------------------------------------------------------------ N3 (f6)
n3 = load("f6_n3c_topology_robustness.csv")
topo = [r for r in n3 if r["method"] == "capacity_cbba_rb" and r["n_runs"]]
REG = {"threshold": "Threshold", "medium": "Medium", "dense": "Dense",
       "complete": "Complete", "partitioned": "Partitioned"}
for r in topo:
    lines.append(NC % ("NThreeTopoCbba" + REG[r["graph_regime"]],
                       dec(r["feasibility_pct"])))
lines.append(NC % ("NThreeTopoWorldsPerRegime", sep(topo[0]["n_runs"])))

grape = [float(r["feasibility_pct"]) for r in n3
         if r["method"] in ("weighted_grape", "weighted_pair_grape")
         and r["n_runs"] and r["graph_regime"] != "partitioned"]
lines.append(NC % ("NThreeTopoGrapeMin", dec(min(grape))))
lines.append(NC % ("NThreeTopoGrapeMax", dec(max(grape))))

# ------------------------------------------------------- N4: CF frente a DMIS
INV = ["distance_cost", "capacity_deficit", "excess_capacity", "assigned_robots",
       "max_coalition_size", "unserved_loads", "feasible"]
with io.open(RAW4, encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
by = {}
for r in rows:
    by.setdefault(r["world_key"], {})[r["method"]] = r
pair = {w: d for w, d in by.items() if "geo_qpg_cf" in d and "geo_qpg_d" in d}

same, worst = 0, 0.0
for d in pair.values():
    ok = True
    for k in INV:
        a, b = d["geo_qpg_cf"][k], d["geo_qpg_d"][k]
        try:
            fa, fb = float(a), float(b)
            eq = abs(fa - fb) <= 1e-9
            if k == "distance_cost":
                worst = max(worst, abs(fa - fb))
        except ValueError:
            eq = str(a).strip().lower() == str(b).strip().lower()
        ok = ok and eq
    same += int(ok)

lines.append(NC % ("SPoneDmisInvariantsK", "siete"))
lines.append(NC % ("SPoneDmisAllInvariantsN", sep(same)))
lines.append(NC % ("SPoneDmisMaxDistDelta",
                   "%s\\times10^{-13}" % dec(worst * 1e13)))

os.makedirs(GEN, exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("escrito:", OUT)
for line in lines[1:]:
    print("  ", line)

# --------------------------------------------------- unidades naturales
# La discrepancia del oraculo se publicaba en notacion cientifica sobre metros.
# Son picometros: el prefijo SI lo dice sin que el lector tenga que contar
# ceros, y deja claro que la magnitud es redondeo en coma flotante.
import re as _re

_metrics = os.path.join(SP1, "generated", "metrics.tex")
if os.path.exists(_metrics):
    _t = io.open(_metrics, encoding="utf-8").read()
    _m = _re.search(r"NTwoOracleMaxError\}\{([0-9]+)\{,\}([0-9]+)\s*"
                    r"\\times\s*10\^\{-([0-9]+)\}", _t)
    if _m:
        _v = float("%s.%s" % (_m.group(1), _m.group(2))) * 10 ** -int(_m.group(3))
        with io.open(OUT, "a", encoding="utf-8") as _fh:
            _fh.write(NC % ("NTwoOracleMaxErrorPm", dec(_v * 1e12)) + "\n")
        print("   NTwoOracleMaxErrorPm =", dec(_v * 1e12), "pm")
