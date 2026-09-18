"""Banco factorial del megajuego distribuido (protocolos, aptitud, pasillo, seguridad, reclutamiento, hiperjuego)."""
from __future__ import annotations
import sys, os, json, csv, math, itertools, time
import numpy as np
from .bench import factorial, run_one

SEEDS = list(range(30))


def grids(quick=False):
    seeds = SEEDS[:6] if quick else SEEDS
    G = {}
    G["protocolos"] = dict(protocol=["best_response", "smith", "bnn", "logit", "replicator"])
    G["aptitud"] = dict(protocol=["smith"], fitness=["vector", "scalar"])
    G["pasillo"] = dict(protocol=["smith"], corridor=["lease", "price"])
    G["seguridad"] = dict(protocol=["smith"], safety=["nested", "coalition", "none"])
    G["reclutamiento"] = dict(protocol=["smith"], recruit=["atomic", "gne_pd"])
    G["hiperjuego"] = dict(protocol=["smith"], belief_err=[0.0, 0.35], recertify=[True, False])
    G["planificador"] = dict(protocol=["smith"], planner=["waypoint", "game"])
    G["hiperjuego2"] = dict(protocol=["smith"], a_ref=[1.0], cap_scale=[0.4], belief_err=[0.0, 0.35], recertify=[True, False])
    return G, seeds


def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c); p = 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(p, 1.0)


def summarize(out_dir="results/megajuego"):
    rows = []
    for f in os.listdir(out_dir):
        if f.endswith(".csv"):
            with open(os.path.join(out_dir, f), encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    r["_grid"] = f[:-4]; rows.append(r)
    def cfgkey(r): return tuple(sorted((k, v) for k, v in r.items() if k.startswith("cfg_")))
    groups = {}
    for r in rows: groups.setdefault((r["_grid"], cfgkey(r)), []).append(r)
    summ = []
    for (g, key), rs in sorted(groups.items()):
        n = len(rs); succ = sum(r["success"] == "True" for r in rs)
        med = lambda k: float(np.median([float(r[k]) for r in rs]))
        lo, hi = wilson(succ, n)
        summ.append(dict(grid=g, cfg=dict(key), n=n, success=succ, rate=succ / n, ci=(round(lo, 3), round(hi, 3)),
                         makespan_med=round(med("makespan"), 1), energy_med=round(med("energy_Wh"), 2), minsep_med=round(med("min_sep_amr"), 3),
                         pen_max=round(max(float(r["wall_pen_max"]) for r in rs), 3), msgs_med=round(med("msgs")), rev_med=round(med("revisions")),
                         false_cert=sum(int(r["false_cert"]) for r in rs), recert=sum(int(r["recert_reject"]) for r in rs),
                         corridor_double_med=round(med("corridor_double"), 1), cpu_med=round(med("cpu_s"), 1)))
    # McNemar pareado frente a la referencia (smith/vector/lease/nested/atomic/0.0/True) por semilla
    ref = {r["seed"]: r for r in rows if r["_grid"] == "protocolos" and r.get("cfg_protocol") == "smith"}
    for s in summ:
        rs = [r for r in rows if r["_grid"] == s["grid"] and cfgkey(r) == tuple(sorted(s["cfg"].items()))]
        b = c = 0
        for r in rs:
            rr = ref.get(r["seed"])
            if rr is None: continue
            a, bb = r["success"] == "True", rr["success"] == "True"
            if a and not bb: b += 1
            if bb and not a: c += 1
        s["vs_ref_better"] = b; s["vs_ref_worse"] = c; s["mcnemar_p"] = round(mcnemar_exact(b, c), 4)
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as f: json.dump(summ, f, indent=1, ensure_ascii=False)
    for s in summ:
        print(f"{s['grid']:14s} {json.dumps(s['cfg'], ensure_ascii=False):70s} n={s['n']:3d} éxito={s['success']:3d} ({s['rate']:.2f} CI {s['ci']}) T={s['makespan_med']:6.1f} E={s['energy_med']:5.2f} minsep={s['minsep_med']:+.3f} pen={s['pen_max']:.3f} msgs={s['msgs_med']:7.0f} rev={s['rev_med']:3.0f} fc={s['false_cert']:3d} dbl={s['corridor_double_med']:5.1f} McN(b/c/p)={s['vs_ref_better']}/{s['vs_ref_worse']}/{s['mcnemar_p']}")
    return summ


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "summary":
        summarize(); sys.exit(0)
    quick = mode == "quick"
    G, seeds = grids(quick)
    only = sys.argv[2:] if len(sys.argv) > 2 else list(G.keys())
    workers = int(os.environ.get("WORKERS", "8"))
    t0 = time.time()
    for name in only:
        sd = seeds if name in ("protocolos", "aptitud", "planificador") else seeds[:max(6, len(seeds) * 2 // 3)]
        factorial(name, G[name], sd, N=8, K=2, workers=workers)
        print(f"== {name} terminado a {time.time() - t0:.0f} s", flush=True)
    summarize()
