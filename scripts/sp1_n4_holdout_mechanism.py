"""Por que los pasillos paralelos son la planta mas dura del banco industrial.

La brecha mediana de 2BR va del 15 % en muelles al 51 % en pasillos paralelos.
Un tribunal preguntara si eso es geometria, densidad, presion o topologia del
grafo. Este guion mide los candidatos sobre el RAW ya congelado, sin ejecutar
ninguna campana nueva.

Candidatos, todos calculables desde el RAW y desde los mundos:
  - dispersion de las distancias AMR-carga (la geometria del coste)
  - grado medio y diametro del grafo de comunicacion
  - lambda_2, conectividad algebraica
  - cuantos AMR quedan sin asignar en el terminal
  - cuanto mejora el optimo respecto de la asignacion trivial mas cercana

Salida: n4_holdout_v1/raw/mechanism.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from sp1_n4_industrial_holdout import make_industrial_world  # noqa: E402

RAW = ROOT / "scripts" / "results" / "sp1_levels" / "n4_holdout_v1" / "raw"


def main() -> int:
    runs = pd.read_csv(RAW / "n4_holdout_runs.csv")
    worlds = pd.read_csv(RAW / "n4_holdout_worlds.csv")

    cert = runs[runs["oracle_certified"].astype(bool)
                & runs["oracle_feasible"].astype(bool)].copy()
    cert["gap_pct"] = 100.0 * (cert["distance_cost"] - cert["oracle_objective"]) \
        / cert["oracle_objective"].replace(0.0, np.nan)

    rows = []
    for _, w in worlds.iterrows():
        world = make_industrial_world(
            world_id=str(w["world_id"]), layout=str(w["layout"]),
            robot_count=int(w["robot_count"]), load_count=int(w["load_count"]),
            q_bar=5.0, cv=0.65, pressure=float(w["pressure"]),
            workspace=(100.0, 100.0), seed=int(w["world_seed"]), alpha=3.0)
        adj = adjacency_for_regime(world.robot_positions, str(w["network"]))
        deg = adj.sum(axis=1).astype(float)
        lap = np.diag(deg) - adj.astype(float)
        ev = np.sort(np.linalg.eigvalsh(lap))
        d = world.distances
        # Cuanto discrimina la geometria: si todas las cargas estan casi a la
        # misma distancia de cada AMR, elegir bien importa poco y el coste es
        # plano; si discrimina mucho, una eleccion mala se paga cara.
        spread = float(np.mean(np.ptp(d, axis=1) / np.maximum(d.mean(axis=1), 1e-9)))
        rows.append({
            "world_id": w["world_id"], "layout": w["layout"],
            "regime": w["regime"], "network": w["network"],
            "mean_degree": float(deg.mean()),
            "lambda2": float(ev[1]),
            "dist_mean": float(d.mean()),
            "dist_spread": spread,
            "demand_ratio": float(world.demands.sum()
                                  / world.capacities.sum()),
        })
    geo = pd.DataFrame(rows)

    gaps = cert[cert["method_tag"] == "2BR"][["world_id", "gap_pct"]]
    br = cert[cert["method_tag"] == "BR"][["world_id", "gap_pct"]].rename(
        columns={"gap_pct": "gap_br"})
    merged = geo.merge(gaps, on="world_id").merge(br, on="world_id")

    out = {"by_layout": {}, "correlations": {}}
    print("%-18s %7s %8s %9s %9s %9s %9s"
          % ("planta", "2BR %", "grado", "lambda2", "d media", "disp. d",
             "dem/cap"))
    for layout, sub in merged.groupby("layout"):
        e = {
            "n": int(len(sub)),
            "gap_2br_median": float(sub["gap_pct"].median()),
            "gap_br_median": float(sub["gap_br"].median()),
            "mean_degree": float(sub["mean_degree"].median()),
            "lambda2": float(sub["lambda2"].median()),
            "dist_mean": float(sub["dist_mean"].median()),
            "dist_spread": float(sub["dist_spread"].median()),
            "demand_ratio": float(sub["demand_ratio"].median()),
        }
        out["by_layout"][layout] = e
        print("%-18s %7.1f %8.2f %9.3f %9.1f %9.3f %9.3f"
              % (layout, e["gap_2br_median"], e["mean_degree"], e["lambda2"],
                 e["dist_mean"], e["dist_spread"], e["demand_ratio"]))

    print("\ncorrelacion de Spearman con la brecha de 2BR, mundo a mundo:")
    for col in ("mean_degree", "lambda2", "dist_mean", "dist_spread",
                "demand_ratio"):
        r = merged[col].corr(merged["gap_pct"], method="spearman")
        out["correlations"][col] = float(r)
        print("  %-14s rho = %+.3f" % (col, r))

    # Cual explica mejor la diferencia ENTRE plantas: se ordena por brecha y se
    # mira que variable sigue el mismo orden.
    order = sorted(out["by_layout"].items(),
                   key=lambda kv: kv[1]["gap_2br_median"])
    out["layout_order_by_gap"] = [k for k, _ in order]
    for col in ("mean_degree", "lambda2", "dist_mean", "dist_spread"):
        vals = [v[col] for _, v in order]
        mono = all(a <= b for a, b in zip(vals, vals[1:])) or \
            all(a >= b for a, b in zip(vals, vals[1:]))
        out["correlations"][col + "_monotone_across_layouts"] = bool(mono)

    (RAW / "mechanism.json").write_text(json.dumps(out, indent=1),
                                        encoding="utf-8")
    print("\nescrito:", RAW / "mechanism.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
