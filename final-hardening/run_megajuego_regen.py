"""Regenera la campana factorial del juego de integracion bajo manifiesto congelado.

Ejecuta EXACTAMENTE el diseno de final-hardening/megajuego_regeneration_manifest.json:
mismas 8 rejillas, mismos factores y niveles, misma regla de semillas (30 para
protocolos/aptitud/planificador, 20 para el resto), N=8 AMR, K=2 cargas.

Escribe en results/megajuego_regen_v1/ y NO toca results/megajuego/, que se
conserva como artefacto historico.

Uso:
    python final-hardening/run_megajuego_regen.py [--workers 16] [--grids protocolos seguridad]
"""
import argparse
import csv
import io
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

OUT_DIR = os.path.join(ROOT, "results", "megajuego_regen_v1")
MANIFEST = os.path.join(ROOT, "final-hardening", "megajuego_regeneration_manifest.json")

SEEDS_FULL = list(range(30))
SEEDS_REDUCED = list(range(20))

# Diseno congelado. No modificar sin versionar el manifiesto.
GRIDS = {
    "protocolos":    (dict(protocol=["best_response", "smith", "bnn", "logit", "replicator"]), SEEDS_FULL),
    "aptitud":       (dict(protocol=["smith"], fitness=["vector", "scalar"]), SEEDS_FULL),
    "planificador":  (dict(protocol=["smith"], planner=["waypoint", "game"]), SEEDS_FULL),
    "pasillo":       (dict(protocol=["smith"], corridor=["lease", "price"]), SEEDS_REDUCED),
    "seguridad":     (dict(protocol=["smith"], safety=["nested", "coalition", "none"]), SEEDS_REDUCED),
    "reclutamiento": (dict(protocol=["smith"], recruit=["atomic", "gne_pd"]), SEEDS_REDUCED),
    "hiperjuego":    (dict(protocol=["smith"], belief_err=[0.0, 0.35], recertify=[True, False]), SEEDS_REDUCED),
    "hiperjuego2":   (dict(protocol=["smith"], a_ref=[1.0], cap_scale=[0.4], belief_err=[0.0, 0.35], recertify=[True, False]), SEEDS_REDUCED),
}

N_AMR = 8
N_LOADS = 2


def _job_list(grid_name):
    import itertools
    grid, seeds = GRIDS[grid_name]
    return [
        (s, dict(zip(grid.keys(), vals)), N_AMR, N_LOADS)
        for vals in itertools.product(*grid.values())
        for s in seeds
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--grids", nargs="*", default=list(GRIDS.keys()))
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        print("ERROR: falta el manifiesto congelado %s" % MANIFEST)
        return 2

    os.makedirs(OUT_DIR, exist_ok=True)
    log_path = os.path.join(OUT_DIR, "RUN_LOG.txt")
    log = io.open(log_path, "a", encoding="utf8")

    def say(msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    from viu_mrob_tfm.megajuego.bench import run_one

    say("campana MEGAJUEGO_FACTORIAL_REGEN_v1, workers=%d" % args.workers)
    say("rejillas: %s" % ", ".join(args.grids))

    t_all = time.time()
    totals = {}

    for name in args.grids:
        jobs = _job_list(name)
        out_csv = os.path.join(OUT_DIR, name + ".csv")
        if os.path.exists(out_csv):
            say("%s ya existe, se omite (borrar para rehacer)" % name)
            continue
        say("%s: %d corridas" % (name, len(jobs)))
        t0 = time.time()
        rows, failed = [], 0
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            for r in ex.map(run_one, jobs):
                if r is None:
                    failed += 1
                    continue
                rows.append(r)
                if len(rows) % 20 == 0:
                    say("  %s %d/%d  %.0fs" % (name, len(rows), len(jobs), time.time() - t0))
        keys = sorted({k for r in rows for k in r})
        with io.open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        totals[name] = dict(rows=len(rows), failed=failed, seconds=round(time.time() - t0, 1))
        say("%s terminado: %d filas, %d fallos, %.0f s" % (name, len(rows), failed, time.time() - t0))

    say("TOTAL %.0f s" % (time.time() - t_all))
    io.open(os.path.join(OUT_DIR, "RUN_TOTALS.json"), "w", encoding="utf8").write(
        json.dumps(totals, indent=2)
    )
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
