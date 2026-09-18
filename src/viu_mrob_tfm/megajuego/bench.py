"""Escenarios, oráculo central y banco factorial del megajuego."""
from __future__ import annotations
import numpy as np, itertools, json, time, os, sys
from dataclasses import asdict
from .plant import Plant, Walls, AMRParams, LoadParams
from .mechanism import Mechanism, Config, cargo_slots

PLANT_W, PLANT_H = 22.0, 14.0
WALL_X = 11.0
OPENING = (WALL_X, 7.0)
OPEN_W = 3.3


def make_walls():
    t = 0.3
    rects = [(-t, 0.0, -t, PLANT_H + t), (PLANT_W, PLANT_W + t, -t, PLANT_H + t), (-t, PLANT_W + t, -t, 0.0), (-t, PLANT_W + t, PLANT_H, PLANT_H + t),
             (WALL_X - t / 2, WALL_X + t / 2, 0.0, OPENING[1] - OPEN_W / 2), (WALL_X - t / 2, WALL_X + t / 2, OPENING[1] + OPEN_W / 2, PLANT_H)]
    return Walls(rects)


def side_of(p):
    return 0 if p[0] < WALL_X else 1


def make_scenario(seed, N=8, K=2, rng=None, load_specs=None):
    rng = rng or np.random.default_rng(seed)
    amr = []
    for i in range(N):
        m = rng.uniform(19, 36); r_w = rng.uniform(0.085, 0.11); tau_max = rng.uniform(4.2, 7.0)
        cap = 0.8 * min(2 * tau_max / r_w, 0.7 * m * 9.81)   # fuerza de contacto sostenible: par o fricción (N)
        amr.append(AMRParams(m=m, I=0.5 * m * 0.25 ** 2, r_w=r_w, b=rng.uniform(0.42, 0.55), J_w=0.02, tau_max=tau_max,
                             c_g=400.0, mu=0.7, b_v=3.0, b_w=0.01, R=rng.uniform(0.235, 0.295), cap=cap, E0=2.0e5))
    loads = []; starts = []; goals = []
    specs = load_specs or [dict(m=60.0, L=1.6, W=1.1, r=3, modes=("cargo",)), dict(m=95.0, L=1.9, W=1.3, r=3, modes=("cargo",)), dict(m=45.0, L=1.25, W=0.95, r=4, modes=("caging",))]
    for k in range(K):
        sp = specs[k % 3]; m = sp["m"] * rng.uniform(0.9, 1.1)
        # cargas en lados alternos, deben cruzar el paso
        side = k % 2
        for _ in range(500):   # separación mínima entre cargas, y entre destinos y cargas
            x0 = rng.uniform(2.5, 7.0) if side == 0 else rng.uniform(15.0, 19.5)
            y0 = rng.uniform(3.0, 11.0)
            gx = rng.uniform(15.0, 19.5) if side == 0 else rng.uniform(2.5, 7.0)
            gy = rng.uniform(3.0, 11.0)
            if all(np.hypot(x0 - a, y0 - b) > 4.5 for a, b in starts) and all(np.hypot(gx - a, gy - b) > 4.0 for a, b in goals)                and all(np.hypot(gx - a, gy - b) > 3.5 for a, b in starts) and all(np.hypot(x0 - a, y0 - b) > 3.5 for a, b in goals):
                break
        starts.append((x0, y0)); goals.append((gx, gy))
        loads.append(LoadParams(m=m, I=m * (sp["L"] ** 2 + sp["W"] ** 2) / 12, L=sp["L"], W=sp["W"], mu_top=0.6, k_pad=1500.0, d_pad=120.0,
                                k_b=4000.0, mu_b=0.15, r_req=sp["r"], B=60.0 + 20 * k, goal=np.array([gx, gy]), modes=sp["modes"], mu_f=(0.10 if sp["modes"][0] == "caging" else 0.15)))
    P = Plant(amr, loads, make_walls())
    for k, ld in enumerate(loads):
        P.ql[k] = [starts[k][0], starts[k][1], 0.0]
    # AMR repartidos por toda la planta, sin solapar cargas
    placed = []
    for i in range(N):
        for _ in range(200):
            p = np.array([rng.uniform(1.0, PLANT_W - 1.0), rng.uniform(1.0, PLANT_H - 1.0)])
            if abs(p[0] - WALL_X) < 1.2: continue
            if all(np.linalg.norm(p - q) > 0.9 for q in placed) and all(np.linalg.norm(p - P.ql[k, :2]) > 2.2 for k in range(K)):
                placed.append(p); break
        P.q[i] = [p[0], p[1], rng.uniform(-np.pi, np.pi)]
    return P


def oracle_assignment(P, cfg):
    """Oráculo central: enumera asignaciones (con información verdadera) y maximiza Phi."""
    M = Mechanism(P, cfg, side_of, OPENING)
    N, K = len(P.amr), len(P.loads)
    best = (-1e9, None)
    idx = list(range(N))
    loads = list(range(K))
    def rec(k, avail, assign, val):
        nonlocal best
        if k == K:
            if val > best[0]: best = (val, dict(assign))
            return
        ld = P.loads[k]; r = ld.r_req
        # opción: no servir la carga k
        rec(k + 1, avail, assign, val)
        for combo in itertools.combinations(avail, r):
            caps = [P.amr[i].cap for i in combo]
            v = M.coalition_value(k, ld.modes[0], caps, None)
            if v <= 0: continue
            # mejor asignación de puestos por coste de viaje (greedy)
            cost = 0.0; free = list(range(r)); a2 = dict(assign)
            for i in combo:
                s = min(free, key=lambda s: M.travel_cost(i, k, ld.modes[0], s)); free.remove(s)
                cost += M.travel_cost(i, k, ld.modes[0], s); a2[i] = (k, ld.modes[0], s)
            rec(k + 1, [i for i in avail if i not in combo], a2, val + v - cost)
    rec(0, idx, {}, 0.0)
    return best


def run_one(args):
    seed, cfg_kw, N, K = args
    cfg = Config(seed=seed, **cfg_kw)
    P = make_scenario(seed, N=N, K=K)
    for a in P.amr: a.cap *= cfg.cap_scale
    M = Mechanism(P, cfg, side_of, OPENING)
    t0 = time.perf_counter()
    m = M.run()
    m["cpu_s"] = time.perf_counter() - t0; m["seed"] = seed; m.update({f"cfg_{k}": v for k, v in cfg_kw.items()})
    # brecha del potencial frente al oráculo (información verdadera) en el instante inicial
    try:
        P2 = make_scenario(seed, N=N, K=K)
        for a in P2.amr: a.cap *= cfg.cap_scale
        val, assign = oracle_assignment(P2, Config(seed=seed, **cfg_kw))
        m["phi_oracle"] = val
    except Exception as e:
        m["phi_oracle"] = float("nan")
    return m


def factorial(name, grid, seeds, N=8, K=2, workers=None, out_dir="results/megajuego"):
    os.makedirs(out_dir, exist_ok=True)
    jobs = [(s, dict(zip(grid.keys(), vals)), N, K) for vals in itertools.product(*grid.values()) for s in seeds]
    from concurrent.futures import ProcessPoolExecutor
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(run_one, jobs):
            rows.append(r); print(f"[{name}] {len(rows)}/{len(jobs)} seed={r['seed']} {dict((k, r[k]) for k in r if k.startswith('cfg_'))} success={r['success']} n_done={r['n_done']} T={r['makespan']:.1f}", flush=True)
    import csv
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(out_dir, f"{name}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in rows]
    return rows


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    kw = dict(protocol=sys.argv[2] if len(sys.argv) > 2 else "smith")
    print(run_one((seed, kw, 8, 2)))
