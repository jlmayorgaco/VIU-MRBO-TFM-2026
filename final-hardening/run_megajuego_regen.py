"""Regenera la campana factorial del juego de integracion bajo manifiesto congelado.

Ejecuta EXACTAMENTE el diseno de final-hardening/megajuego_regeneration_manifest.json:
mismas 8 rejillas, mismos factores y niveles, misma regla de semillas (30 para
protocolos/aptitud/planificador, 20 para el resto), N=8 AMR, K=2 cargas.

Escribe en results/megajuego_regen_v1/ y NO toca results/megajuego/, que se
conserva como artefacto historico.

PARALELISMO POR FRAGMENTOS, NO POR POOL.
ProcessPoolExecutor esta roto en este interprete (Python de WindowsApps):
levanta BrokenProcessPool incluso con una funcion trivial. Por eso cada
fragmento es un proceso independiente que se lanza por separado y escribe su
propio CSV; despues `--merge` los une en el orden canonico.

Uso:
    python final-hardening/run_megajuego_regen.py --shard 0 --nshards 8
    ...
    python final-hardening/run_megajuego_regen.py --merge
"""
import argparse
import csv
import io
import itertools
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

OUT_DIR = os.path.join(ROOT, "results", "megajuego_regen_v1")
SHARD_DIR = os.path.join(OUT_DIR, "shards")
MANIFEST = os.path.join(ROOT, "final-hardening", "megajuego_regeneration_manifest.json")

SEEDS_FULL = list(range(30))
SEEDS_REDUCED = list(range(20))

# Diseno congelado. El orden de este diccionario y el de itertools.product fijan
# el orden canonico de los trabajos; no reordenar sin versionar el manifiesto.
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


def all_jobs():
    """Lista global y determinista de (grid, cfg, seed)."""
    jobs = []
    for name, (grid, seeds) in GRIDS.items():
        for vals in itertools.product(*grid.values()):
            cfg = dict(zip(grid.keys(), vals))
            for s in seeds:
                jobs.append((name, cfg, s))
    return jobs


def run_shard(shard, nshards):
    from viu_mrob_tfm.megajuego.bench import run_one

    os.makedirs(SHARD_DIR, exist_ok=True)
    jobs = [j for i, j in enumerate(all_jobs()) if i % nshards == shard]
    log_path = os.path.join(SHARD_DIR, "shard_%02d.log" % shard)
    log = io.open(log_path, "w", encoding="utf8")

    def say(m):
        line = "[%s] shard %d: %s" % (time.strftime("%H:%M:%S"), shard, m)
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    say("%d corridas asignadas de %d totales" % (len(jobs), len(all_jobs())))
    rows, failed = [], []
    t0 = time.time()
    for n, (grid, cfg, seed) in enumerate(jobs, 1):
        try:
            r = run_one((seed, cfg, N_AMR, N_LOADS))
            r["_grid"] = grid
            rows.append(r)
        except Exception as exc:  # se registra, no se reintenta con otra semilla
            failed.append(dict(grid=grid, cfg=cfg, seed=seed, error=repr(exc)))
            say("FALLO %s %s seed=%d: %r" % (grid, cfg, seed, exc))
        if n % 5 == 0 or n == len(jobs):
            el = time.time() - t0
            say("%d/%d  %.0f s  (%.1f s/corrida, quedan ~%.0f min)"
                % (n, len(jobs), el, el / n, (len(jobs) - n) * el / n / 60))

    keys = sorted({k for r in rows for k in r})
    out = os.path.join(SHARD_DIR, "shard_%02d.csv" % shard)
    with io.open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    io.open(os.path.join(SHARD_DIR, "shard_%02d_failed.json" % shard), "w", encoding="utf8").write(
        json.dumps(failed, indent=2)
    )
    say("terminado: %d filas, %d fallos, %.0f s" % (len(rows), len(failed), time.time() - t0))
    log.close()
    return 0


def merge():
    import pandas as pd

    parts = sorted(f for f in os.listdir(SHARD_DIR) if f.endswith(".csv"))
    if not parts:
        print("no hay fragmentos que unir")
        return 1
    d = pd.concat([pd.read_csv(os.path.join(SHARD_DIR, p)) for p in parts], ignore_index=True)
    print("filas unidas: %d desde %d fragmentos" % (len(d), len(parts)))

    failed_total = []
    for f in sorted(os.listdir(SHARD_DIR)):
        if f.endswith("_failed.json"):
            failed_total.extend(json.load(io.open(os.path.join(SHARD_DIR, f), encoding="utf8")))

    expected = {}
    for name, (grid, seeds) in GRIDS.items():
        expected[name] = len(list(itertools.product(*grid.values()))) * len(seeds)

    ok = True
    for name in GRIDS:
        sub = d[d["_grid"] == name].drop(columns=["_grid"])
        got, exp = len(sub), expected[name]
        flag = "OK" if got == exp else "INCOMPLETO"
        if got != exp:
            ok = False
        print("  %-14s %4d / %4d  %s" % (name, got, exp, flag))
        sub.to_csv(os.path.join(OUT_DIR, name + ".csv"), index=False)

    io.open(os.path.join(OUT_DIR, "RUN_TOTALS.json"), "w", encoding="utf8").write(
        json.dumps(
            dict(rows=len(d), expected=expected, failed=failed_total, complete=ok),
            indent=2,
        )
    )
    print("fallos registrados: %d" % len(failed_total))
    print("campana completa" if ok else "CAMPANA INCOMPLETA")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int)
    ap.add_argument("--nshards", type=int, default=8)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--plan", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        print("ERROR: falta el manifiesto congelado")
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)

    if args.plan:
        jobs = all_jobs()
        print("trabajos totales: %d" % len(jobs))
        for name, (grid, seeds) in GRIDS.items():
            c = len(list(itertools.product(*grid.values())))
            print("  %-14s %d celdas x %d semillas = %d" % (name, c, len(seeds), c * len(seeds)))
        return 0
    if args.merge:
        return merge()
    if args.shard is None:
        print("indica --shard i --nshards k, o --merge")
        return 2
    return run_shard(args.shard, args.nshards)


if __name__ == "__main__":
    sys.exit(main())
