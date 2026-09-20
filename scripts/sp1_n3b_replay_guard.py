"""Guardia de replay para geo_qpg.

Antes y despues de tocar `geo_qpg.py` se ejecuta un conjunto fijo de mundos con
los metodos ya publicados y se compara el digest de los resultados. Si el digest
cambia, la campana N4 congelada dejaria de ser reproducible y el cambio debe
revertirse.

    python scripts/sp1_n3b_replay_guard.py --write   # fija la linea base
    python scripts/sp1_n3b_replay_guard.py           # comprueba

La comparacion incluye el VECTOR DE ASIGNACION completo, no solo agregados. Dos
asignaciones distintas pueden tener el mismo coste, de modo que comparar solo el
objetivo dejaria pasar un cambio de comportamiento.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import run_geo_qpg  # noqa: E402

BASELINE = ROOT / "scripts" / "results" / "sp1_levels" / "replay_guard.json"

METHODS = ("geo_qpg_u", "geo_qpg_p", "geo_qpg_cf", "geo_qpg_c3", "geo_qpg_d",
           "geo_qpg_smith", "geo_qpg_lll")
SCENARIOS = ("uniform", "clustered", "separated", "ring", "corridor")
SEEDS = tuple(range(9_100_001, 9_100_009))

RUN_FIELDS = ("algorithm_status", "terminal_phase", "rounds", "messages",
              "bytes_sent", "commits", "quota_commits", "geometry_commits",
              "rejected_stale", "rejected_conflict", "mis_iterations",
              "max_parallel_commits", "unilateral_local_minimum",
              "pair_local_minimum", "triple_local_minimum",
              "potential_monotone")
CERT_FIELDS = ("status", "total_deficit", "distance_cost", "conflicts",
               "unserved_loads", "excess_capacity", "assigned_robots")


def _plain(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return round(float(v), 9)
    if isinstance(v, np.ndarray):
        return [_plain(x) for x in v.tolist()]
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return None if v is None else str(v)


def _row(scenario, seed, method, result) -> dict:
    row = {"scenario": scenario, "seed": seed, "method": method}
    missing = [f for f in RUN_FIELDS if not hasattr(result, f)]
    if missing:
        raise AttributeError("RunResult sin los campos %s" % missing)
    row.update({f: _plain(getattr(result, f)) for f in RUN_FIELDS})
    cert = result.certificate
    missing = [f for f in CERT_FIELDS if not hasattr(cert, f)]
    if missing:
        raise AttributeError("Certificate sin los campos %s" % missing)
    row.update({"cert_" + f: _plain(getattr(cert, f)) for f in CERT_FIELDS})
    row["assignment"] = _plain(np.asarray(result.assignment, dtype=int))
    return row


def collect() -> dict:
    rows = []
    for scenario in SCENARIOS:
        for seed in SEEDS:
            world = make_world(
                world_id="guard-%s-%d" % (scenario, seed),
                robot_count=10, load_count=3, q_bar=5.0,
                cv=0.65, pressure=0.85, scenario=scenario,
                workspace=(100.0, 100.0), seed=seed, alpha=3.0,
            )
            adjacency = adjacency_for_regime(world.robot_positions, "medium")
            for method in METHODS:
                result = run_geo_qpg(world, adjacency, method, max_rounds=256)
                rows.append(_row(scenario, seed, method, result))
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return {"n_rows": len(rows),
            "n_fields": len(rows[0]) if rows else 0,
            "digest": hashlib.sha256(blob.encode()).hexdigest(),
            "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="fija la linea base en vez de comprobarla")
    args = ap.parse_args()

    current = collect()
    print("filas: %d   campos por fila: %d" % (current["n_rows"],
                                               current["n_fields"]))
    print("digest: %s" % current["digest"])

    if args.write:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(current, indent=1), encoding="utf-8")
        print("linea base escrita en", BASELINE)
        return 0

    if not BASELINE.exists():
        print("NO HAY LINEA BASE. Ejecuta con --write antes de tocar geo_qpg.")
        return 2

    saved = json.loads(BASELINE.read_text(encoding="utf-8"))
    if saved["digest"] == current["digest"]:
        print("REPLAY IDENTICO: los metodos publicados no han cambiado.")
        return 0

    print("REPLAY ROTO: el digest difiere de la linea base.")
    old = {(r["scenario"], r["seed"], r["method"]): r for r in saved["rows"]}
    shown = 0
    for r in current["rows"]:
        k = (r["scenario"], r["seed"], r["method"])
        if k in old and old[k] != r:
            print("  %s seed=%s %s" % k)
            for f in r:
                if f in old[k] and old[k][f] != r[f]:
                    print("      %-24s %s -> %s" % (f, old[k][f], r[f]))
            shown += 1
            if shown >= 5:
                print("  ...")
                break
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
