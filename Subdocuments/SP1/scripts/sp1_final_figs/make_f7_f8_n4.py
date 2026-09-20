"""F7 y F8 — Orden estrategico y ejecucion distribuida (N4).

F7  A  brecha frente al MILP para h = 1, 2, 3 sobre soporte comun.
    B  riesgo de infactibilidad por orden estrategico.
    C  distribucion del primer escape conectado detectado, h_c*.
    D  sensibilidad de P(h_c* > 3) a CV, presion y relacion N/K.

    h_c* es el primer orden en el que existe una mejora conectada DETECTADA con
    la busqueda truncada en h = 3. No mide la magnitud de esa mejora.

F8  CF frente a DMIS+TX con el mismo conjunto de candidatos y el mismo orden
    estrategico, para aislar la arquitectura de confirmacion.

Todo procede de RAW congelado. No hay ningun valor medido escrito a mano.
"""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
from thesis_style import (apply_style, boot_ci, fbool, fnum, median, read_raw,  # noqa: E402
                          save, stamp, wilson_ci, err_pair, C_BLUE, C_ORANGE, C_GREEN,
                          C_GRAY, C_PURPLE, C_RED)

apply_style()

E4 = read_raw("n4_v2/raw/e4_family_runs.csv")
E9 = read_raw("n4_v4/raw/e9_hstar_runs.csv")

ORDER = [("geo_qpg_u", "BR\n$h=1$", C_BLUE),
         ("geo_qpg_p", "2BR\n$h=2$", C_ORANGE),
         ("geo_qpg_c3", "C3\n$h=3$", C_GREEN)]
MAIN = [m for m, _, _ in ORDER]

by_world = collections.defaultdict(dict)
for r in E4:
    by_world[r["world_key"]][r["method"]] = r

cert = {w for w, d in by_world.items()
        if all(m in d for m in MAIN)
        and fbool(d[MAIN[0]]["oracle_feasible"])
        and fbool(d[MAIN[0]]["oracle_certified"])}
common = {w for w in cert if all(fbool(by_world[w][m]["feasible"]) for m in MAIN)}

# ============================================================ F7
f7_table = []
for m, lab, _c in ORDER:
    rows_c = [by_world[w][m] for w in cert]
    k_inf = sum(1 for r in rows_c if not fbool(r["feasible"]))
    pinf, ilo, ihi = wilson_ci(k_inf, len(rows_c))
    gaps = [100 * fnum(by_world[w][m]["optimality_gap"]) for w in common]
    gaps = [g for g in gaps if g is not None]
    glo, ghi = boot_ci(gaps)
    f7_table.append({
        "panel": "A/B", "method": m, "label": lab.replace("\n", " "),
        "n_certified": len(rows_c), "n_common_support": len(gaps),
        "gap_median_pct": round(median(gaps), 3),
        "gap_ci_low": round(glo, 3), "gap_ci_high": round(ghi, 3),
        "infeasible_pct": round(100 * pinf, 3),
        "infeasible_ci_low": round(100 * ilo, 3),
        "infeasible_ci_high": round(100 * ihi, 3),
        "bytes_per_amr_median": round(
            median([fnum(by_world[w][m]["bytes_per_agent"]) for w in cert]), 1),
    })

MAINBLOCK = [r for r in E9 if r["block"] == "frozen_main"]
RATIO = [r for r in E9 if r["block"] == "ratio_sensitivity"]
CATS = ["2", "3", ">3"]
CATLAB = {"2": r"$h_c^\star=2$", "3": r"$h_c^\star=3$",
          ">3": "sin escape\ndetectado"}
CATCOL = {"2": C_ORANGE, "3": C_PURPLE, ">3": C_GRAY}

fig = plt.figure(figsize=(7.1, 5.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.05], hspace=0.52, wspace=0.42)

axA = fig.add_subplot(gs[0, 0])
xs = list(range(3))
ys = [t["gap_median_pct"] for t in f7_table]
pairs = [err_pair(t["gap_median_pct"], t["gap_ci_low"], t["gap_ci_high"])
         for t in f7_table]
el = [a for a, _ in pairs]
eh = [b for _, b in pairs]
axA.errorbar(xs, ys, yerr=[el, eh], marker="o", color="#333333",
             ecolor=C_GRAY, capsize=3, markerfacecolor="white",
             markeredgewidth=1.3, linewidth=1.3)
for x, t, (_m, _l, c) in zip(xs, f7_table, ORDER):
    axA.scatter([x], [t["gap_median_pct"]], s=42, color=c, zorder=4)
axA.set_xticks(xs, [l for _m, l, _c in ORDER])
axA.set_ylabel("brecha frente al MILP\nen soporte común [%]")
axA.set_title("A · Orden estratégico", loc="left")
axA.grid(axis="y", alpha=0.55)
axA.set_ylim(bottom=0)

axB = fig.add_subplot(gs[0, 1])
ys = [t["infeasible_pct"] for t in f7_table]
pairs = [err_pair(t["infeasible_pct"], t["infeasible_ci_low"],
                  t["infeasible_ci_high"]) for t in f7_table]
el = [a for a, _ in pairs]
eh = [b for _, b in pairs]
axB.bar(xs, ys, color=[c for _m, _l, c in ORDER], alpha=0.85, width=0.6,
        yerr=[el, eh], capsize=3, error_kw={"elinewidth": 1.0})
axB.set_xticks(xs, [l for _m, l, _c in ORDER])
axB.set_ylabel("riesgo de\ninfactibilidad [%]")
axB.set_title("B · Riesgo residual", loc="left")
axB.grid(axis="y", alpha=0.55)

axC = fig.add_subplot(gs[0, 2])
counts = collections.Counter(r["hstar_category"] for r in MAINBLOCK)
tot = len(MAINBLOCK)
ys = [100 * counts.get(c, 0) / tot for c in CATS]
bars = axC.bar(range(3), ys, color=[CATCOL[c] for c in CATS], alpha=0.85,
               width=0.62)
for b, c in zip(bars, CATS):
    axC.text(b.get_x() + b.get_width() / 2, b.get_height() + 2,
             "%d/%d" % (counts.get(c, 0), tot), ha="center", va="bottom",
             fontsize=7.0, color=C_GRAY)
axC.set_xticks(range(3), [CATLAB[c] for c in CATS])
axC.set_ylabel("mundos [%]")
axC.set_title("C · Primer escape", loc="left")
axC.set_ylim(0, 112)
axC.grid(axis="y", alpha=0.55)

# Panel D: sensibilidad de P(h_c* > 3)
axD = fig.add_subplot(gs[1, :])
groups = []
for key, lab, src in (("capacity_cv", "CV", MAINBLOCK),
                      ("pressure", r"$\rho$", MAINBLOCK),
                      ("robots_per_load", "N/K", RATIO)):
    levels = sorted({fnum(r[key]) for r in src})
    for lv in levels:
        rows = [r for r in src if fnum(r[key]) == lv]
        k = sum(1 for r in rows if r["hstar_category"] == ">3")
        p, lo, hi = wilson_ci(k, len(rows))
        groups.append({"factor": lab, "level": lv, "n": len(rows),
                       "p": 100 * p, "lo": 100 * lo, "hi": 100 * hi,
                       "block": "frozen_main" if src is MAINBLOCK
                       else "ratio_sensitivity"})
xs = list(range(len(groups)))
cols = {"CV": C_BLUE, r"$\rho$": C_GREEN, "N/K": C_PURPLE}
axD.bar(xs, [g["p"] for g in groups],
        color=[cols[g["factor"]] for g in groups], alpha=0.85, width=0.62,
        yerr=[[err_pair(g["p"], g["lo"], g["hi"])[0] for g in groups],
              [err_pair(g["p"], g["lo"], g["hi"])[1] for g in groups]],
        capsize=2.5, error_kw={"elinewidth": 0.9})
axD.set_xticks(xs, ["%s\n%g" % (g["factor"], g["level"]) for g in groups])
axD.set_ylabel(r"$P(\mathrm{sin\ escape\ hasta\ }h=3)$ [%]")
axD.set_title("D · Sensibilidad del caso sin escape detectado "
              "(N/K: bloque de sensibilidad)", loc="left")
axD.grid(axis="y", alpha=0.55)
for i, g in enumerate(groups):
    axD.text(i, -3.2, "n=%d" % g["n"], ha="center", va="top", fontsize=6.0,
             color=C_GRAY)

for g in groups:
    f7_table.append({
        "panel": "D", "method": "", "label": "%s=%g" % (g["factor"], g["level"]),
        "n_certified": g["n"], "n_common_support": "",
        "gap_median_pct": "", "gap_ci_low": "", "gap_ci_high": "",
        "infeasible_pct": round(g["p"], 3),
        "infeasible_ci_low": round(g["lo"], 3),
        "infeasible_ci_high": round(g["hi"], 3),
        "bytes_per_amr_median": "",
    })
for c in CATS:
    f7_table.append({
        "panel": "C", "method": "", "label": "hstar_" + c,
        "n_certified": tot, "n_common_support": counts.get(c, 0),
        "gap_median_pct": round(100 * counts.get(c, 0) / tot, 3),
        "gap_ci_low": "", "gap_ci_high": "", "infeasible_pct": "",
        "infeasible_ci_low": "", "infeasible_ci_high": "",
        "bytes_per_amr_median": "",
    })

stamp(fig, "n4_v2/e4_family_runs.csv + n4_v4/e9_hstar_runs.csv")
save(fig, "f7_n4_strategic_order", f7_table)

# ============================================================ F8
ARCH = [("geo_qpg_cf", "CF", C_BLUE),
        ("geo_qpg_d", "DMIS+TX", C_ORANGE)]
pair = {w for w, d in by_world.items()
        if all(m in d for m, _l, _c in ARCH)
        and fbool(d["geo_qpg_cf"]["oracle_feasible"])
        and fbool(d["geo_qpg_cf"]["oracle_certified"])}
pair_ok = {w for w in pair
           if all(fbool(by_world[w][m]["feasible"]) for m, _l, _c in ARCH)}

f8_table = []
for m, lab, _c in ARCH:
    rows = [by_world[w][m] for w in pair]
    gaps = [100 * fnum(by_world[w][m]["optimality_gap"]) for w in pair_ok]
    gaps = [g for g in gaps if g is not None]
    glo, ghi = boot_ci(gaps)
    k = sum(1 for r in rows if fbool(r["feasible"]))
    p, plo, phi = wilson_ci(k, len(rows))
    byts = [fnum(r["bytes_per_agent"]) for r in rows]
    f8_table.append({
        "method": m, "label": lab.replace("\n", " "), "n": len(rows),
        "n_common": len(gaps),
        "gap_median_pct": round(median(gaps), 3),
        "gap_ci_low": round(glo, 3), "gap_ci_high": round(ghi, 3),
        "feasibility_pct": round(100 * p, 3),
        "feasibility_ci_low": round(100 * plo, 3),
        "feasibility_ci_high": round(100 * phi, 3),
        "bytes_per_amr_median": round(median(byts), 1),
    })

# diferencia pareada de bytes por mundo
delta = []
for w in pair:
    a = fnum(by_world[w]["geo_qpg_d"]["bytes_per_agent"])
    b = fnum(by_world[w]["geo_qpg_cf"]["bytes_per_agent"])
    if a is not None and b is not None:
        delta.append(a - b)
dlo, dhi = boot_ci(delta)

fig = plt.figure(figsize=(7.1, 3.2))
gs = fig.add_gridspec(1, 3, wspace=0.46)

ax1 = fig.add_subplot(gs[0, 0])
ax1.bar([0, 1], [t["gap_median_pct"] for t in f8_table],
        color=[c for _m, _l, c in ARCH], alpha=0.85, width=0.55,
        yerr=[[err_pair(t["gap_median_pct"], t["gap_ci_low"],
                        t["gap_ci_high"])[0] for t in f8_table],
              [err_pair(t["gap_median_pct"], t["gap_ci_low"],
                        t["gap_ci_high"])[1] for t in f8_table]],
        capsize=3, error_kw={"elinewidth": 1.0})
ax1.set_xticks([0, 1], [l for _m, l, _c in ARCH])
ax1.set_ylabel("brecha frente\nal MILP [%]")
ax1.set_title("A · Brecha", loc="left")
ax1.grid(axis="y", alpha=0.55)

ax2 = fig.add_subplot(gs[0, 1])
ax2.bar([0, 1], [t["feasibility_pct"] for t in f8_table],
        color=[c for _m, _l, c in ARCH], alpha=0.85, width=0.55,
        yerr=[[err_pair(t["feasibility_pct"], t["feasibility_ci_low"],
                        t["feasibility_ci_high"])[0] for t in f8_table],
              [err_pair(t["feasibility_pct"], t["feasibility_ci_low"],
                        t["feasibility_ci_high"])[1] for t in f8_table]],
        capsize=3, error_kw={"elinewidth": 1.0})
ax2.set_xticks([0, 1], [l for _m, l, _c in ARCH])
ax2.set_ylabel("factibilidad [%]")
ax2.set_ylim(0, 108)
ax2.set_title("B · Factibilidad", loc="left")
ax2.grid(axis="y", alpha=0.55)

ax3 = fig.add_subplot(gs[0, 2])
ax3.hist(delta, bins=26, color=C_ORANGE, alpha=0.85)
ax3.axvline(median(delta), color="#222222", linestyle="--", linewidth=1.1)
ax3.set_xlabel("bytes/AMR adicionales\n(DMIS+TX − CF)")
ax3.set_ylabel("mundos")
ax3.set_title("C · Sobrecoste", loc="left")
ax3.grid(axis="y", alpha=0.55)
ax3.text(0.96, 0.93, "mediana %.0f\nIC95 %.0f–%.0f"
         % (median(delta), dlo, dhi), transform=ax3.transAxes,
         ha="right", va="top", fontsize=7.0, color=C_GRAY)

f8_table.append({
    "method": "paired_delta", "label": "DMIS+TX menos CF", "n": len(delta),
    "n_common": len(delta), "gap_median_pct": "", "gap_ci_low": "",
    "gap_ci_high": "", "feasibility_pct": "", "feasibility_ci_low": "",
    "feasibility_ci_high": "",
    "bytes_per_amr_median": round(median(delta), 1),
})

stamp(fig, "n4_v2/e4_family_runs.csv")
save(fig, "f8_n4_distributed_execution", f8_table)

print("   F7 soporte comun: %d de %d certificados" % (len(common), len(cert)))
for t in f7_table[:3]:
    print("      %-8s brecha %5.1f %% [%.1f, %.1f] | infactible %4.1f %%"
          % (t["label"], t["gap_median_pct"], t["gap_ci_low"],
             t["gap_ci_high"], t["infeasible_pct"]))
print("   F7 h_c*: %s" % dict(counts))
print("   F8 pareado n=%d | delta bytes/AMR mediana %.0f [%.0f, %.0f]"
      % (len(delta), median(delta), dlo, dhi))
