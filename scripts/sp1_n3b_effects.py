"""N3.B · H-N3B.2 — efectos principales de regla y de fitness, e interaccion.

La hipotesis secundaria preguntaba si la eleccion de fitness mueve la brecha mas
que la eleccion de regla. La configuracion congelada anade una condicion: no se
formula ningun claim causal si hay interaccion. Este guion mide las dos cosas.

El contraste es pareado por mundo: cada mundo del soporte comun aporta las nueve
celdas, de modo que la geometria y las capacidades se cancelan.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "scripts" / "results" / "sp1_levels" / "n3b_v2" / "raw"

RULES = ("BR", "ASR", "LLL")  # el control 2BR se analiza aparte
FITNESS = ("F0", "F1", "F2")


def boot_ci(v, rng, n_boot=4000, level=0.95):
    v = np.asarray(sorted(float(x) for x in v), dtype=float)
    if v.size == 0:
        return float("nan"), float("nan")
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    meds = np.median(v[idx], axis=1)
    a = (1.0 - level) / 2.0
    return float(np.quantile(meds, a)), float(np.quantile(meds, 1.0 - a))


def main() -> int:
    df = pd.read_csv(RAW / "n3b_factorial_runs.csv")
    cert = df[df["oracle_certified"].astype(bool)
              & df["oracle_feasible"].astype(bool)].copy()
    cert["gap_pct"] = 100.0 * (cert["distance_cost"] - cert["oracle_objective"]) \
        / cert["oracle_objective"].replace(0.0, np.nan)

    piv = cert.pivot_table(index="world_id", columns="cell",
                           values="feasible", aggfunc="first").dropna(how="any")
    common = sorted(piv[(piv == 1).all(axis=1)].index)
    sub = cert[cert["world_id"].isin(common)]
    grid = sub.pivot_table(index="world_id",
                           columns=["revision_rule", "fitness"],
                           values="gap_pct", aggfunc="first").dropna()

    rng = np.random.default_rng(0xE77EC7)
    out = {"n_common_support": int(len(grid)), "cell_medians": {},
           "main_effect_rule": {}, "main_effect_fitness": {}}

    print("soporte comun pareado: %d mundos\n" % len(grid))
    print("brecha mediana por celda (%)")
    print("%-6s %8s %8s %8s" % ("", *FITNESS))
    for r in RULES:
        row = []
        for f in FITNESS:
            m = float(np.median(grid[(r, f)].values))
            out["cell_medians"]["%s-%s" % (r, f)] = m
            row.append(m)
        print("%-6s %8.2f %8.2f %8.2f" % (r, *row))

    print("\nefecto principal de la REGLA (mediana sobre los tres fitness)")
    for r in RULES:
        vals = np.concatenate([grid[(r, f)].values for f in FITNESS])
        lo, hi = boot_ci(vals, rng)
        out["main_effect_rule"][r] = {"median": float(np.median(vals)),
                                      "ci_low": lo, "ci_high": hi}
        print("  %-4s %7.2f  [%6.2f, %6.2f]" % (r, np.median(vals), lo, hi))

    print("\nefecto principal del FITNESS (mediana sobre las tres reglas)")
    for f in FITNESS:
        vals = np.concatenate([grid[(r, f)].values for r in RULES])
        lo, hi = boot_ci(vals, rng)
        out["main_effect_fitness"][f] = {"median": float(np.median(vals)),
                                         "ci_low": lo, "ci_high": hi}
        print("  %-4s %7.2f  [%6.2f, %6.2f]" % (f, np.median(vals), lo, hi))

    rule_range = (max(out["main_effect_rule"][r]["median"] for r in RULES)
                  - min(out["main_effect_rule"][r]["median"] for r in RULES))
    fit_range = (max(out["main_effect_fitness"][f]["median"] for f in FITNESS)
                 - min(out["main_effect_fitness"][f]["median"] for f in FITNESS))
    out["rule_range_pp"] = rule_range
    out["fitness_range_pp"] = fit_range

    # Interaccion: si el efecto del fitness fuera aditivo, la diferencia entre
    # dos fitness seria la misma dentro de cada regla. Se mide cuanto varia.
    spreads = {}
    for f in FITNESS:
        if f == "F2":
            continue
        diffs = {r: float(np.median(grid[(r, f)].values
                                    - grid[(r, "F2")].values)) for r in RULES}
        spreads[f] = {"per_rule_vs_F2": diffs,
                      "range_pp": max(diffs.values()) - min(diffs.values())}
    out["interaction"] = spreads

    print("\nrecorrido del efecto principal: regla %.2f pp, fitness %.2f pp"
          % (rule_range, fit_range))
    print("\ninteraccion: efecto de cada fitness frente a F2, por regla")
    for f, d in spreads.items():
        print("  %s: %s   recorrido %.2f pp"
              % (f, {k: round(v, 2) for k, v in d["per_rule_vs_F2"].items()},
                 d["range_pp"]))
    biggest = max(d["range_pp"] for d in spreads.values())
    out["interaction_max_range_pp"] = biggest
    out["verdict"] = (
        "hay interaccion: el efecto del fitness depende de la regla, de modo "
        "que no se formula ningun claim causal separado, como fijaba la "
        "configuracion congelada"
        if biggest > min(rule_range, fit_range) / 2.0 else
        "los efectos se comportan de forma aproximadamente aditiva")
    print("\nveredicto: " + out["verdict"])

    (RAW / "n3b_effects.json").write_text(json.dumps(out, indent=1),
                                          encoding="utf-8")
    print("\nescrito:", RAW / "n3b_effects.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
