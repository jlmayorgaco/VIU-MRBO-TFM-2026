"""F4 — Mapa de atomicidad de N2.

Panel A  validacion del oraculo: HiGHS frente a enumeracion exhaustiva.
Panel B  rejilla CV x rho -> brecha de integralidad LP->MILP (mediana).
Panel C  rejilla CV x rho -> P(LP factible y MILP infactible).
Panel D  rejilla CV x rho -> tasa de certificacion del MILP bajo presupuesto.

Los paneles B y C usan la campana de atomicidad, con dos niveles de presion:
la rejilla es discreta 5x2 y no se interpola. El panel D usa la campana de
diagrama de fase, que barre seis niveles de presion.

Todo procede de RAW congelado. No hay ningun valor medido escrito a mano.
"""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from thesis_style import (apply_style, fbool, fnum, median, read_raw, save,  # noqa: E402
                          stamp, C_BLUE, C_GRAY)

apply_style()

ATOM = read_raw("n2_v1/raw/atomicity_runs.csv")
PHASE = read_raw("n2_v1/raw/phase_diagram_runs.csv")
ORACLE = read_raw("n2_v1/raw/oracle_validation_runs.csv")

# Escalas secuenciales sobrias, legibles tambien en gris de imprenta.
CMAP_WARM = LinearSegmentedColormap.from_list(
    "warm", ["#FBF3EC", "#F0C9A6", "#DE9058", "#C4622D", "#8A3D16"])
CMAP_COOL = LinearSegmentedColormap.from_list(
    "cool", ["#F1F5F9", "#C3D3E3", "#7E9FC2", "#2F5D8C", "#1B3A59"])


def grid(rows, xkey, ykey, fn):
    xs = sorted({fnum(r[xkey]) for r in rows})
    ys = sorted({fnum(r[ykey]) for r in rows})
    cells = collections.defaultdict(list)
    for r in rows:
        cells[(fnum(r[xkey]), fnum(r[ykey]))].append(r)
    mat = [[fn(cells.get((x, y), [])) for x in xs] for y in ys]
    return xs, ys, mat, cells


def draw_grid(ax, xs, ys, mat, cmap, fmt, title, vmax=None, cells=None,
              show_n=False):
    im = ax.imshow(mat, cmap=cmap, aspect="auto", origin="lower",
                   vmin=0, vmax=vmax)
    ax.set_xticks(range(len(xs)), ["%.2f" % x for x in xs])
    ax.set_yticks(range(len(ys)), ["%.2f" % y for y in ys])
    lim = (vmax if vmax is not None
           else max((v for row in mat for v in row if v is not None), default=1))
    for j, _y in enumerate(ys):
        for i, _x in enumerate(xs):
            v = mat[j][i]
            if v is None:
                ax.text(i, j, "–", ha="center", va="center", fontsize=7,
                        color=C_GRAY)
                continue
            txt = fmt % v
            if show_n and cells is not None:
                txt += "\n%d" % len(cells.get((xs[i], ys[j]), []))
            ax.text(i, j, txt, ha="center", va="center", fontsize=7.0,
                    color="white" if v > 0.55 * lim else "#222222")
    ax.set_title(title, loc="left")
    return im


fig = plt.figure(figsize=(7.1, 6.4))
gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.15],
                      hspace=0.55, wspace=0.30)

# ---------------------------------------------------------------- Panel A
axA = fig.add_subplot(gs[0, 0])
xs = [fnum(r["brute_objective"]) for r in ORACLE]
ys = [fnum(r["milp_objective"]) for r in ORACLE]
pairs = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
agree = sum(1 for r in ORACLE if fbool(r["status_agrees"]))
errs = [fnum(r["absolute_error"]) for r in ORACLE]
errs = [e for e in errs if e is not None]
lo = min(min(p) for p in pairs)
hi = max(max(p) for p in pairs)
axA.plot([lo, hi], [lo, hi], color=C_GRAY, linestyle="--", linewidth=0.9,
         zorder=1, label="identidad")
axA.scatter([p[0] for p in pairs], [p[1] for p in pairs], s=7,
            color=C_BLUE, alpha=0.55, linewidths=0, zorder=2)
axA.set_xlabel("óptimo por enumeración [m]")
axA.set_ylabel("óptimo HiGHS [m]")
axA.set_title("A · Validación del oráculo", loc="left")
axA.grid(alpha=0.5)
# En picometros y con coma decimal: la notacion cientifica sobre metros obliga
# al lector a contar ceros para descubrir que la cifra es redondeo.
_err_pm = ("%.1f" % ((max(errs) if errs else 0.0) * 1e12)).replace(".", ",")
axA.text(0.04, 0.94,
         "%d mundos\nacuerdo %d/%d\ndiscrepancia máx. %s pm"
         % (len(ORACLE), agree, len(ORACLE), _err_pm),
         transform=axA.transAxes, ha="left", va="top", fontsize=7.0,
         color=C_GRAY)

# ---------------------------------------------------------------- Panel B
axB = fig.add_subplot(gs[0, 1])


def med_gap(rows):
    vs = [fnum(r["gap_relative"]) for r in rows]
    m = median(vs)
    return 100 * m if m is not None else None


xs, ys, mat, cells = grid(ATOM, "capacity_cv", "pressure", med_gap)
imB = draw_grid(axB, xs, ys, mat, CMAP_WARM, "%.1f",
                "B · Brecha de integralidad [%]")
axB.set_xlabel(r"CV nominal de capacidad")
axB.set_ylabel(r"presión $\rho$")

# ---------------------------------------------------------------- Panel C
axC = fig.add_subplot(gs[1, 0])


def p_lp_only(rows):
    if not rows:
        return None
    k = sum(1 for r in rows
            if r["lp_status"].upper().startswith("OPT")
            and not r["milp_status"].upper().startswith("OPT"))
    return 100.0 * k / len(rows)


xs, ys, mat, cells = grid(ATOM, "capacity_cv", "pressure", p_lp_only)
imC = draw_grid(axC, xs, ys, mat, CMAP_COOL, "%.1f",
                "C · LP factible y MILP infactible [%]")
axC.set_xlabel(r"CV nominal de capacidad")
axC.set_ylabel(r"presión $\rho$")

# ---------------------------------------------------------------- Panel D
axD = fig.add_subplot(gs[1:, 1])


def p_cert(rows):
    if not rows:
        return None
    return 100.0 * sum(1 for r in rows if fbool(r["certified_feasible"])) / len(rows)


xs, ys, mat, cellsD = grid(PHASE, "capacity_cv", "pressure", p_cert)
draw_grid(axD, xs, ys, mat, CMAP_COOL, "%.0f", "D · MILP certificado factible [%]",
          vmax=100)
axD.set_xlabel(r"CV nominal de capacidad")
axD.set_ylabel(r"presión $\rho$")

# ---------------------------------------------------------------- Panel E
axE = fig.add_subplot(gs[2, 0])
frac = sum(1 for r in ATOM if fbool(r["fractional_world"]))
lp_only = sum(1 for r in ATOM
              if r["lp_status"].upper().startswith("OPT")
              and not r["milp_status"].upper().startswith("OPT"))
gaps = [100 * fnum(r["gap_relative"]) for r in ATOM if fnum(r["gap_relative"]) is not None]
axE.hist(gaps, bins=30, color="#C4622D", alpha=0.85)
axE.axvline(median(gaps), color="#222222", linewidth=1.1, linestyle="--")
axE.set_xlabel("brecha de integralidad [%]")
axE.set_ylabel("mundos")
axE.set_title("E · Distribución agregada de la brecha", loc="left")
axE.grid(axis="y", alpha=0.5)
axE.text(0.97, 0.94,
         "LP fraccionario %d/%d\nLP✓ MILP✗ %d\nmediana %.1f %%"
         % (frac, len(ATOM), lp_only, median(gaps)),
         transform=axE.transAxes, ha="right", va="top", fontsize=7.0,
         color=C_GRAY)

# ---------------------------------------------------------------- tabla CSV
table = []
cellsA = collections.defaultdict(list)
for r in ATOM:
    cellsA[(fnum(r["capacity_cv"]), fnum(r["pressure"]))].append(r)
for (cv, rho), rows in sorted(cellsA.items()):
    gv = [fnum(r["gap_relative"]) for r in rows]
    gv = [v for v in gv if v is not None]
    table.append({
        "campaign": "atomicity",
        "capacity_cv": cv,
        "pressure": rho,
        "n_worlds": len(rows),
        "n_comparable": len(gv),
        "gap_median_pct": round(100 * median(gv), 3) if gv else "",
        "lp_feasible_milp_infeasible": sum(
            1 for r in rows if r["lp_status"].upper().startswith("OPT")
            and not r["milp_status"].upper().startswith("OPT")),
        "fractional_worlds": sum(1 for r in rows if fbool(r["fractional_world"])),
        "milp_certified_pct": "",
    })
cellsP = collections.defaultdict(list)
for r in PHASE:
    cellsP[(fnum(r["capacity_cv"]), fnum(r["pressure"]))].append(r)
for (cv, rho), rows in sorted(cellsP.items()):
    table.append({
        "campaign": "phase_diagram",
        "capacity_cv": cv,
        "pressure": rho,
        "n_worlds": len(rows),
        "n_comparable": "",
        "gap_median_pct": "",
        "lp_feasible_milp_infeasible": "",
        "fractional_worlds": "",
        "milp_certified_pct": round(
            100.0 * sum(1 for r in rows if fbool(r["certified_feasible"]))
            / len(rows), 2),
    })

stamp(fig, "n2_v1/{atomicity,phase_diagram,oracle_validation}_runs.csv")
save(fig, "f4_n2_atomicity_map", table)

print("   atomicity : %d mundos | rejilla CV(%d) x rho(%d)"
      % (len(ATOM), len({r['capacity_cv'] for r in ATOM}),
         len({r['pressure'] for r in ATOM})))
print("   phase     : %d mundos | rejilla CV(%d) x rho(%d)"
      % (len(PHASE), len({r['capacity_cv'] for r in PHASE}),
         len({r['pressure'] for r in PHASE})))
print("   LP fraccionario %d/%d | LP factible y MILP infactible %d"
      % (frac, len(ATOM), lp_only))
