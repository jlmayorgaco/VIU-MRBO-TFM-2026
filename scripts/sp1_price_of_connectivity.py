"""SP1 · cuanto cuesta exigir que una mejora sea negociable sobre el grafo.

POR QUE EXISTE
    El capitulo mide una perdida y la nombra «brecha»: la que se paga por
    limitar el ORDEN de la revision, porque con h = 1 las mejoras que exigen
    mover dos AMR quedan fuera del alcance. Hay una segunda perdida que hasta
    ahora no se medía: exigir que los AMR implicados esten CONECTADOS entre si.
    Una mejora puede existir en el espacio de estrategias y no ser acordable,
    porque quienes deben moverse no pueden hablarse.

    Son perdidas distintas. Este guion mide la segunda sobre el terminal de la
    mejor respuesta: para cada mundo busca la primera mejora estricta de orden
    menor o igual que tres sin restriccion, y despues la busca exigiendo que el
    grupo sea conexo en el grafo de comunicacion.

    El barrido cubre los cinco regimenes de conectividad de N3, porque la
    respuesta depende de cuan raleado este el grafo: con vecindad densa casi
    cualquier pareja esta conectada y la restriccion no ata; cerca del umbral
    de conectividad si.

QUE NO ES
    No es una campana nueva. Reutiliza los mundos congelados de n4_v2, que se
    reconstruyen y se verifican byte a byte por su resumen de contenido antes
    de usarlos. No hay parametros nuevos ni decisiones nuevas.

    python scripts/sp1_price_of_connectivity.py
    python scripts/sp1_price_of_connectivity.py --limit 40   # prueba rapida
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import run_geo_qpg  # noqa: E402
from viu_mrob_tfm.sp1_n4.geo_qpg import (  # noqa: E402
    minimum_improving_coalition_order,
)

LEV = ROOT / "scripts" / "results" / "sp1_levels"
SRC = LEV / "n4_v2" / "raw" / "e4_family_worlds.csv"
OUT = LEV / "n4_poc_v1"
MAX_ORDER = 3
# De mas raleado a mas denso. La particion permanente es el control negativo
# de N3 y aqui marca el extremo: un grafo con dos componentes.
REGIMES = ("partitioned", "threshold", "medium", "dense", "complete")
DEFAULT_WORLDS = 240


def rebuild(row):
    return make_world(
        world_id=str(row["world_key"]),
        robot_count=int(row["N"]), load_count=int(row["K"]),
        q_bar=5.0, cv=float(row["capacity_cv"]),
        pressure=float(row["pressure"]), scenario=str(row["scenario"]),
        workspace=(100.0, 100.0), seed=int(row["world_seed"]), alpha=3.0,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=DEFAULT_WORLDS)
    args = ap.parse_args()

    worlds = pd.read_csv(SRC).head(args.limit)
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    print("mundos: %d   regimenes: %d" % (len(worlds), len(REGIMES)))

    rows = []
    for i, (_, w) in enumerate(worlds.iterrows(), 1):
        world = rebuild(w)
        if world.digest() != str(w["world_digest"]):
            raise SystemExit("ABORTA: el mundo %s no se reproduce byte a byte"
                             % w["world_key"])
        for regime in REGIMES:
            adjacency = adjacency_for_regime(world.robot_positions, regime)
            terminal = run_geo_qpg(world, adjacency, "geo_qpg_u",
                                   max_rounds=400)
            free = minimum_improving_coalition_order(
                world, terminal.assignment, adjacency,
                max_order=MAX_ORDER, connected_only=False)
            conn = minimum_improving_coalition_order(
                world, terminal.assignment, adjacency,
                max_order=MAX_ORDER, connected_only=True)
            rows.append({
                "world_key": w["world_key"], "scenario": w["scenario"],
                "capacity_cv": w["capacity_cv"], "pressure": w["pressure"],
                "graph_regime": regime,
                "mean_degree": float(adjacency.sum(axis=1).mean()),
                "order_free": free.order, "order_connected": conn.order,
                "free_found": free.order is not None,
                "connected_found": conn.order is not None,
                "blocked": bool(free.order is not None and conn.order is None),
                "delayed": bool(free.order is not None
                                and conn.order is not None
                                and conn.order > free.order),
            })
        if i % 40 == 0 or i == len(worlds):
            print("   mundos %d/%d" % (i, len(worlds)), flush=True)

    df = pd.DataFrame(rows)
    raw = OUT / "raw" / "poc_runs.csv"
    df.to_csv(raw, index=False)

    res = {"n_worlds": int(df["world_key"].nunique()),
           "max_order": MAX_ORDER, "by_regime": {},
           "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}
    for regime in REGIMES:
        sub = df[df["graph_regime"] == regime]
        wf = int(sub["free_found"].sum())
        blocked = int(sub["blocked"].sum())
        delayed = int(sub["delayed"].sum())
        res["by_regime"][regime] = {
            "n": int(len(sub)),
            "mean_degree": float(sub["mean_degree"].median()),
            "with_improvement": wf,
            "blocked": blocked, "delayed": delayed,
            "blocked_pct": 100.0 * blocked / max(wf, 1),
            "affected_pct": 100.0 * (blocked + delayed) / max(wf, 1),
        }

    (OUT / "raw" / "poc_analysis.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")

    print("\n%-12s %6s %8s %9s %9s %9s"
          % ("regimen", "grado", "c/mejora", "bloquea", "retrasa", "afecta %"))
    for regime in REGIMES:
        e = res["by_regime"][regime]
        print("%-12s %6.2f %8d %9d %9d %8.1f"
              % (regime, e["mean_degree"], e["with_improvement"],
                 e["blocked"], e["delayed"], e["affected_pct"]))
    print("\nescrito:", OUT / "raw" / "poc_analysis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
