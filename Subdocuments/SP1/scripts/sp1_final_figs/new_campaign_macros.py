# -*- coding: utf-8 -*-
"""Macros de las campanas de validacion.

  n3b_v2          factorial 4 x 3 con brazo de control 2BR pareado
  n4_holdout_v1   banco industrial, cadena de filtros y mecanismo
  n4_v2/e5        DPOP, que si se ejecuto

Lee RAW y analisis congelados. Ninguna cifra se escribe a mano en el capitulo.
Salida: generated/sp1-final/new_campaigns.tex
"""
from __future__ import annotations

import csv
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SP1 = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN = os.path.join(SP1, "generated", "sp1-final")
REPO = os.path.abspath(os.path.join(SP1, "..", ".."))
LEV = os.path.join(REPO, "scripts", "results", "sp1_levels")
OUT = os.path.join(GEN, "new_campaigns.tex")

NC = "\\newcommand{\\%s}{%s}"


def dec(x, d=1):
    """Coma decimal espanola, y sin decimales que solo aportan un cero."""

    t = "%.*f" % (d, float(x))
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t.replace(".", "{,}")


_LETRAS = {1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
           6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez",
           11: "once", 12: "doce"}


def _letra(n):
    """En prosa castellana los numeros pequenos van con letra."""

    return _LETRAS.get(int(n), sep(n))


def sep(n):
    return "{:,}".format(int(n)).replace(",", "\\,")


def load(*parts):
    with io.open(os.path.join(LEV, *parts), encoding="utf-8") as fh:
        return json.load(fh)


lines = ["% Generado por scripts/sp1_final_figs/new_campaign_macros.py"]

# ------------------------------------------------------------- N3.B v2
b = load("n3b_v2", "raw", "n3b_analysis.json")
H1 = ("BR", "ASR", "LLL")
FIT = ("F0", "F1", "F2")
# LaTeX no admite digitos en un nombre de macro.
FITNAME = {"F0": "FZero", "F1": "FOne", "F2": "FTwo"}
unil = {k: v for k, v in b["cells"].items()
        if k.split("-")[0] in H1}

lines += [
    NC % ("NThreeBWorlds", sep(b["n_worlds"])),
    NC % ("NThreeBOracleFeasible", sep(b["n_oracle_feasible"])),
    NC % ("NThreeBCommon", sep(b["n_common_support"])),
    NC % ("NThreeBCells", sep(len(b["cells"]))),
    NC % ("NThreeBUnilateralCells", _letra(len(unil))),
    NC % ("NThreeBRuns", sep(b["n_worlds"] * len(b["cells"]))),
]

best = min(unil.items(), key=lambda kv: kv[1]["gap_median_pct"])
lines += [
    NC % ("NThreeBBestCell", best[0].replace("-", "--")),
    NC % ("NThreeBBestGap", dec(best[1]["gap_median_pct"])),
    NC % ("NThreeBBestGapLo", dec(best[1]["gap_ci_low"])),
    NC % ("NThreeBBestGapHi", dec(best[1]["gap_ci_high"])),
    NC % ("NThreeBBestFeas", dec(best[1]["feasibility_pct"])),
    NC % ("NThreeBWorstGap",
          dec(max(unil.values(), key=lambda v: v["gap_median_pct"])
              ["gap_median_pct"])),
]

# Control: la peor celda 2BR sigue siendo mejor que la mejor unilateral?
ctrl = {k: v for k, v in b["cells"].items() if k.startswith("2BR-")}
worst_ctrl = max(ctrl.items(), key=lambda kv: kv[1]["gap_median_pct"])
lines += [
    NC % ("NThreeBCtrlWorstCell", worst_ctrl[0].replace("-", "--")),
    NC % ("NThreeBCtrlWorstGap", dec(worst_ctrl[1]["gap_median_pct"])),
    NC % ("NThreeBCtrlBestGap",
          dec(min(ctrl.values(), key=lambda v: v["gap_median_pct"])
              ["gap_median_pct"])),
    NC % ("NThreeBSeparation",
          dec(best[1]["gap_median_pct"]
              - worst_ctrl[1]["gap_median_pct"])),
]

pe = b["paired_order_effect"]["by_fitness"]
for fit in FIT:
    d = pe[fit]
    lines += [
        NC % ("NThreeBPaired%sN" % FITNAME[fit], sep(d["n_paired"])),
        # En valor absoluto: la prosa dice «reduce», y repetir el signo
        # convierte la frase en un volcado de tabla. El orden del intervalo se
        # invierte en consecuencia.
        NC % ("NThreeBPaired%sDrop" % FITNAME[fit], dec(abs(d["median_pp"]))),
        NC % ("NThreeBPaired%sDropLo" % FITNAME[fit], dec(abs(d["ci_high"]))),
        NC % ("NThreeBPaired%sDropHi" % FITNAME[fit], dec(abs(d["ci_low"]))),
        NC % ("NThreeBPaired%sBetterPct" % FITNAME[fit], dec(d["worlds_h2_better_pct"])),
    ]
lines.append(NC % ("NThreeBPairedAllExcludeZero",
                   "sí" if all(pe[f]["excludes_zero"] for f in FIT) else "no"))
lines.append(NC % ("NThreeBPairedMinBetterPct",
                   dec(min(pe[f]["worlds_h2_better_pct"] for f in FIT))))

try:
    e = load("n3b_v2", "raw", "n3b_effects.json")
    lines += [
        NC % ("NThreeBRuleRange", dec(e["rule_range_pp"])),
        NC % ("NThreeBFitRange", dec(e["fitness_range_pp"])),
        NC % ("NThreeBInteraction", dec(e["interaction_max_range_pp"])),
    ]
except OSError:
    pass

# ------------------------------------------------- hold-out industrial
h = load("n4_holdout_v1", "raw", "n4_holdout_analysis.json")
fc = h["filter_chain"]
lines += [
    NC % ("NFourHWorlds", sep(h["n_worlds"])),
    NC % ("NFourHCertified", sep(fc["oracle_certified"])),
    NC % ("NFourHBrFeasN", sep(fc["feasible_by_method"]["BR"])),
    NC % ("NFourHTwoBrFeasN", sep(fc["feasible_by_method"]["2BR"])),
    NC % ("NFourHPairN", sep(fc["br_and_2br"])),
    NC % ("NFourHCommon", sep(fc["all_methods"])),
    NC % ("NFourHLayouts", sep(len(h["by_layout"]))),
]

for tag, key in (("BR", "Br"), ("2BR", "TwoBr"), ("C3", "CThree"),
                 ("CF", "Cf"), ("DMIS+TX", "Dmis"),
                 ("CBBA-RB", "Cbba"), ("Pair-GRAPE", "Pair")):
    m = h["methods"][tag]
    lines += [
        NC % ("NFourH%sGap" % key, dec(m["gap_median_pct"])),
        NC % ("NFourH%sGapLo" % key, dec(m["gap_ci_low"])),
        NC % ("NFourH%sGapHi" % key, dec(m["gap_ci_high"])),
        NC % ("NFourH%sFeas" % key, dec(m["feasibility_pct"])),
        NC % ("NFourH%sBytes" % key, sep(round(m["bytes_per_amr_median"]))),
    ]

p = h["h1_vs_h2_paired"]
lines += [
    NC % ("NFourHPairedN", sep(p["n"])),
    NC % ("NFourHPairedDrop", dec(abs(p["median_pp"]))),
    NC % ("NFourHPairedDropLo", dec(abs(p["ci_high"]))),
    NC % ("NFourHPairedDropHi", dec(abs(p["ci_low"]))),
    NC % ("NFourHPairedBetterPct", dec(p["worlds_h2_better_pct"])),
]

o = h["dmis_byte_overhead"]
lines += [
    NC % ("NFourHDmisOverhead", sep(round(o["median"]))),
    NC % ("NFourHDmisOverheadLo", sep(round(o["ci_low"]))),
    NC % ("NFourHDmisOverheadHi", sep(round(o["ci_high"]))),
]

hs = h["hstar"]
for cat, key in (("2", "Two"), ("3", "Three"), (">3", "GtThree")):
    lines += [
        NC % ("NFourHHstar%sPct" % key, dec(hs["pct"].get(cat, 0.0))),
        NC % ("NFourHHstar%sN" % key, sep(hs["counts"].get(cat, 0))),
    ]
lines.append(NC % ("NFourHHstarN", sep(hs["n"])))

LABEL = {"cross_aisle": "pasillos cruzados",
         "parallel_aisles": "pasillos paralelos",
         "docks_staging": "muelles y preparación",
         "open_bottleneck": "áreas con paso estrecho"}
by = h["by_layout"]
hard = max(by.items(), key=lambda kv: kv[1]["2BR"])
easy = min(by.items(), key=lambda kv: kv[1]["2BR"])
lines += [
    NC % ("NFourHHardLayout", LABEL[hard[0]]),
    NC % ("NFourHHardGap", dec(hard[1]["2BR"])),
    NC % ("NFourHEasyLayout", LABEL[easy[0]]),
    NC % ("NFourHEasyGap", dec(easy[1]["2BR"])),
]

# ------------------------------------------------------------ mecanismo
try:
    mech = load("n4_holdout_v1", "raw", "mechanism.json")
    c = mech["correlations"]
    lines += [
        NC % ("NFourHRhoSpread", dec(c["dist_spread"], 2)),
        NC % ("NFourHRhoDegree", dec(c["mean_degree"], 2)),
        NC % ("NFourHRhoLambda", dec(c["lambda2"], 2)),
        NC % ("NFourHSpreadEasy", dec(mech["by_layout"][easy[0]]["dist_spread"], 2)),
        NC % ("NFourHSpreadHard", dec(mech["by_layout"][hard[0]]["dist_spread"], 2)),
    ]
except OSError:
    pass

# ------------------------------------------------------------------ DPOP
dp = os.path.join(LEV, "n4_v2", "raw", "e5_dpop_runs.csv")
if os.path.exists(dp):
    with io.open(dp, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if "dpop" in r["method"].lower()]
    cert = [r for r in rows
            if str(r["oracle_certified"]).strip().lower() in ("true", "1")]
    agree = sum(1 for r in cert
                if abs(float(r["distance_cost"])
                       - float(r["oracle_objective"])) <= 1e-6)
    worst = max(abs(float(r["distance_cost"]) - float(r["oracle_objective"]))
                for r in cert)
    tab = max(int(float(r["utility_entries"])) for r in rows
              if r.get("utility_entries"))
    lines += [
        NC % ("NFourDpopRuns", sep(len(cert))),
        NC % ("NFourDpopAgree", sep(agree)),
        # En picometros: 1e-12 m. La notacion cientifica sobre metros no se
        # lee, y lo que la cifra dice es "redondeo", no "distancia".
        NC % ("NFourDpopMaxDeltaPm", dec(worst * 1e12)),
        NC % ("NFourDpopMaxTable", sep(tab)),
    ]

os.makedirs(GEN, exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("escrito:", OUT, "(%d macros)" % (len(lines) - 1))

# ------------------------------------------------ veredicto por familia
# La pregunta del TFM incluye explicitamente las dinamicas poblacionales. En
# SP1 entran por dos vias: como relajacion continua (F-II) y como regla de
# revision atomica (Geo-ASR, protocolo de Smith). Estas macros permiten dar el
# veredicto de cada via con la cifra medida, sea favorable o no.
_extra = []
for _rule, _key in (("BR", "Br"), ("ASR", "Asr"), ("LLL", "Lll"),
                    ("2BR", "TwoBr")):
    _cells = {f: b["cells"]["%s-%s" % (_rule, f)] for f in FIT}
    _best = min(_cells.items(), key=lambda kv: kv[1]["gap_median_pct"])
    _extra += [
        NC % ("NThreeB%sBestFit" % _key, _best[0]),
        NC % ("NThreeB%sBestGap" % _key, dec(_best[1]["gap_median_pct"])),
        NC % ("NThreeB%sBestFeas" % _key, dec(_best[1]["feasibility_pct"])),
    ]
with io.open(OUT, "a", encoding="utf-8") as _fh:
    _fh.write("\n".join(_extra) + "\n")
print("veredicto por familia:")
for _l in _extra:
    print("  ", _l)

# ------------------------------------------- precio de la conectividad
# Cuantas veces exigir que el grupo que se mueve pueda hablarse impide o
# retrasa una mejora que existe en el espacio de estrategias.
try:
    _poc = load("n4_poc_v1", "raw", "poc_analysis.json")
    _reg = _poc["by_regime"]
    _worst = max(_reg.items(), key=lambda kv: kv[1]["affected_pct"])
    _zero = [k for k, v in _reg.items() if v["affected_pct"] == 0.0]
    _extra2 = [
        NC % ("PoCWorlds", sep(_poc["n_worlds"])),
        NC % ("PoCWorstRegime", {"partitioned": "el grafo partido",
                                 "threshold": "el umbral de conectividad",
                                 "medium": "conectividad media",
                                 "dense": "grafo denso",
                                 "complete": "grafo completo"}[_worst[0]]),
        NC % ("PoCWorstPct", dec(_worst[1]["affected_pct"])),
        NC % ("PoCWorstBlocked", sep(_worst[1]["blocked"])),
        NC % ("PoCWorstDelayed", sep(_worst[1]["delayed"])),
        NC % ("PoCWorstN", sep(_worst[1]["with_improvement"])),
        NC % ("PoCZeroRegimes", _letra(len(_zero))),
    ]
    with io.open(OUT, "a", encoding="utf-8") as _fh:
        _fh.write("\n".join(_extra2) + "\n")
    print("\nprecio de la conectividad:")
    for _l in _extra2:
        print("  ", _l)
except OSError:
    pass
