"""A2 - Analisis estadistico de la campana regenerada del juego de integracion.

Corrige los cuatro defectos del guion original (ver MEGAGAME_CAMPAIGN_AUDIT.md §4):

  1. Wilson se usa SOLO para la tasa de una celda, nunca como IC de una
     diferencia. Toda diferencia lleva IC bootstrap pareado sobre mundos.
  2. Holm se aplica DENTRO de cada familia declarada en el manifiesto, no una
     vez sobre todas las tablas.
  3. Los endpoints continuos llevan efecto pareado con IC, no mediana por celda.
  4. El contraste de cada rejilla es el que su pregunta pide (referencia interna
     de la rejilla), no siempre protocolos/smith.

Las familias y los parametros se leen del manifiesto congelado; no se eligen
despues de ver los datos.

Uso: python final-hardening/analyze_megajuego_regen.py [--dir results/megajuego_regen_v1]
"""
import argparse
import io
import json
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "final-hardening", "megajuego_regeneration_manifest.json")

# Referencia interna por rejilla: el nivel contra el que su pregunta contrasta.
REFERENCE = {
    "protocolos":    ("cfg_protocol", "smith"),
    "aptitud":       ("cfg_fitness", "vector"),
    "planificador":  ("cfg_planner", "game"),
    "pasillo":       ("cfg_corridor", "lease"),
    "seguridad":     ("cfg_safety", "nested"),
    "reclutamiento": ("cfg_recruit", "atomic"),
}

# Familias de Holm declaradas en el manifiesto antes de ejecutar.
FAMILIES = {
    "F1_protocolo": ["protocolos"],
    "F2_ablacion_seguridad": ["seguridad"],
    "F3_mecanismo": ["aptitud", "pasillo", "reclutamiento", "planificador"],
    "F4_creencia": ["hiperjuego", "hiperjuego2"],
}

CONTINUOUS = ["makespan", "energy_Wh", "msgs", "min_sep_amr", "revisions", "wall_pen_max"]


def wilson(k, n, z=1.96):
    """IC de UNA tasa. No es el IC de una diferencia."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def mcnemar_exact(b, c):
    """p exacto bilateral: 2*P(X <= min(b,c)), X ~ Bin(b+c, 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(p, 1.0)


def paired_boot_diff(a, b, rng, resamples=10000, level=0.95):
    """IC percentil bootstrap de la diferencia pareada media a-b, remuestreando MUNDOS."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = a - b
    n = len(d)
    if n == 0:
        return float("nan"), (float("nan"), float("nan"))
    idx = rng.integers(0, n, size=(resamples, n))
    boots = d[idx].mean(axis=1)
    lo = float(np.percentile(boots, 100 * (1 - level) / 2))
    hi = float(np.percentile(boots, 100 * (1 + level) / 2))
    return float(d.mean()), (lo, hi)


def holm(pvals):
    """Devuelve p ajustados por Holm, en el orden de entrada."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def cell_label(row, factors):
    return ", ".join("%s=%s" % (f.replace("cfg_", ""), row[f]) for f in factors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(ROOT, "results", "megajuego_regen_v1"))
    args = ap.parse_args()

    man = json.load(io.open(MANIFEST, encoding="utf8"))
    stats_cfg = man["statistics_planned_before_execution"]
    resamples = int(stats_cfg["bootstrap_resamples"])
    level = float(stats_cfg["confidence_level"])
    seed = int(stats_cfg["analysis_seed"])
    rng = np.random.default_rng(seed)

    print("Analisis con parametros CONGELADOS antes de ejecutar:")
    print("  bootstrap=%d  nivel=%.2f  semilla_analisis=%d" % (resamples, level, seed))
    print()

    results = []

    for grid in sorted(REFERENCE.keys()) + ["hiperjuego", "hiperjuego2"]:
        path = os.path.join(args.dir, grid + ".csv")
        if not os.path.exists(path):
            print("(falta %s)" % grid)
            continue
        d = pd.read_csv(path)
        d["success"] = d["success"].astype(str).str.lower().isin(["true", "1"])
        factors = [c for c in d.columns if c.startswith("cfg_") and d[c].nunique() > 1]
        if not factors:
            factors = [c for c in d.columns if c.startswith("cfg_")][:1]

        print("=== %s ===  factores variables: %s" % (grid, [f.replace("cfg_", "") for f in factors]))

        cells = {}
        for key, sub in d.groupby(factors, dropna=False):
            k = key if isinstance(key, tuple) else (key,)
            cells[k] = sub.set_index("seed").sort_index()

        # tasa por celda con Wilson (solo descriptivo)
        for k, sub in sorted(cells.items(), key=lambda kv: str(kv[0])):
            n = len(sub)
            s = int(sub["success"].sum())
            lo, hi = wilson(s, n)
            print("  %-42s n=%2d  exito=%2d  tasa=%.3f  Wilson=[%.3f, %.3f]"
                  % (str(k), n, s, s / n, lo, hi))

        # contraste pareado contra la referencia interna
        if grid in REFERENCE:
            rf, rv = REFERENCE[grid]
            ref_key = None
            for k in cells:
                if str(k[factors.index(rf)] if len(factors) > 1 else k[0]) == rv:
                    ref_key = k
                    break
            if ref_key is None:
                print("  (sin celda de referencia %s=%s)" % (rf, rv))
                continue
            ref = cells[ref_key]
            for k, sub in sorted(cells.items(), key=lambda kv: str(kv[0])):
                if k == ref_key:
                    continue
                common = ref.index.intersection(sub.index)
                a = sub.loc[common, "success"].astype(int).to_numpy()
                b = ref.loc[common, "success"].astype(int).to_numpy()
                bb = int(((a == 1) & (b == 0)).sum())
                cc = int(((a == 0) & (b == 1)).sum())
                p = mcnemar_exact(bb, cc)
                eff, (lo, hi) = paired_boot_diff(a, b, rng, resamples, level)
                results.append(dict(grid=grid, cell=str(k), ref=str(ref_key),
                                    endpoint="success", n=len(common),
                                    effect=eff, ci_low=lo, ci_high=hi,
                                    disc_b=bb, disc_c=cc, p_raw=p))
                print("    %-38s vs ref  n=%2d  dif=%+.3f IC[%+.3f,%+.3f]  McNemar b/c=%d/%d p=%.4f"
                      % (str(k), len(common), eff, lo, hi, bb, cc, p))
                for ep in CONTINUOUS:
                    if ep not in sub.columns:
                        continue
                    e2, (l2, h2) = paired_boot_diff(
                        sub.loc[common, ep].to_numpy(), ref.loc[common, ep].to_numpy(),
                        rng, resamples, level)
                    results.append(dict(grid=grid, cell=str(k), ref=str(ref_key),
                                        endpoint=ep, n=len(common),
                                        effect=e2, ci_low=l2, ci_high=h2,
                                        disc_b=None, disc_c=None, p_raw=None))
        else:
            # hiperjuego / hiperjuego2: efecto de belief_err y de recertify
            for fac in [f for f in factors if f in ("cfg_belief_err", "cfg_recertify")]:
                lv = sorted(d[fac].unique(), key=str)
                if len(lv) != 2:
                    continue
                hi_lv, lo_lv = lv[1], lv[0]
                A = d[d[fac] == hi_lv].groupby("seed")["success"].mean()
                B = d[d[fac] == lo_lv].groupby("seed")["success"].mean()
                common = A.index.intersection(B.index)
                a, b = A.loc[common].to_numpy(), B.loc[common].to_numpy()
                eff, (l, h) = paired_boot_diff(a, b, rng, resamples, level)
                ab = int(((a > b)).sum()); ba = int(((b > a)).sum())
                p = mcnemar_exact(ab, ba)
                results.append(dict(grid=grid, cell="%s=%s" % (fac.replace("cfg_", ""), hi_lv),
                                    ref="%s=%s" % (fac.replace("cfg_", ""), lo_lv),
                                    endpoint="success", n=len(common),
                                    effect=eff, ci_low=l, ci_high=h,
                                    disc_b=ab, disc_c=ba, p_raw=p))
                print("    %-20s %s vs %s  n=%2d  dif=%+.3f IC[%+.3f,%+.3f]  p=%.4f"
                      % (fac.replace("cfg_", ""), hi_lv, lo_lv, len(common), eff, l, h, p))
        print()

    # Holm dentro de cada familia, solo sobre contrastes con p
    print("=== CORRECCION DE HOLM, POR FAMILIA DECLARADA ===")
    for fam, grids in FAMILIES.items():
        rows = [r for r in results if r["grid"] in grids and r["p_raw"] is not None
                and r["endpoint"] == "success"]
        if not rows:
            continue
        adj = holm([r["p_raw"] for r in rows])
        for r, a in zip(rows, adj):
            r["p_holm"] = a
            r["family"] = fam
        print("  %s  (k=%d)" % (fam, len(rows)))
        for r in rows:
            print("    %-14s %-38s dif=%+.3f IC[%+.3f,%+.3f]  p=%.4f  p_Holm=%.4f"
                  % (r["grid"], r["cell"], r["effect"], r["ci_low"], r["ci_high"],
                     r["p_raw"], r["p_holm"]))
    print()

    out = os.path.join(args.dir, "STATISTICS.json")
    io.open(out, "w", encoding="utf8").write(json.dumps(results, indent=1, ensure_ascii=False, default=str))
    pd.DataFrame(results).to_csv(os.path.join(args.dir, "STATISTICS.csv"), index=False)
    print("-> %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
