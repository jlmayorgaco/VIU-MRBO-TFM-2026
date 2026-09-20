"""SP1 · N4 — banco hold-out industrial.

POR QUE EXISTE
    Los cinco generadores de SP1 se usaron para DESARROLLAR el metodo. Todo lo
    que el capitulo afirma sobre h_c* y sobre la utilidad de las revisiones
    bilaterales se ha medido sobre ese mismo banco. Esta campana somete el
    metodo a cuatro plantas de tipo industrial que no participaron en su diseno.

    El objetivo no es ganar. Es responder si la utilidad de pasar de h = 1 a
    h = 2 se reproduce fuera del banco de desarrollo. Un resultado negativo se
    reporta igual: acota el dominio de validez en vez de dejarlo implicito.

QUE NO CAMBIA
    Ningun metodo nuevo, ningun parametro del metodo tocado, y el truncamiento
    de la busqueda sigue en h_max = 3. Lo unico nuevo es la geometria.

    python scripts/sp1_n4_industrial_holdout.py
    python scripts/sp1_n4_industrial_holdout.py --smoke
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sp1_n3_confirmatory import solve_oracle  # noqa: E402
from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.runner import run_method  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import World  # noqa: E402
from viu_mrob_tfm.sp1_n4 import run_geo_qpg  # noqa: E402
from viu_mrob_tfm.sp1_n4.geo_qpg import (  # noqa: E402
    minimum_improving_coalition_order,
)
from viu_mrob_tfm.sp1_n4.industrial_layouts import (  # noqa: E402
    INDUSTRIAL_LAYOUTS,
    generate_industrial_positions,
)

OUT = ROOT / "scripts" / "results" / "sp1_levels" / "n4_holdout_v1"

# Los seis metodos de la configuracion congelada. Ninguno es nuevo: todos se
# publicaron ya en N3 o en N4, y aqui solo cambia la geometria del banco.
QPG_METHODS = (
    ("BR", "geo_qpg_u"),
    ("2BR", "geo_qpg_p"),
    ("C3", "geo_qpg_c3"),
    ("CF", "geo_qpg_cf"),
    ("DMIS+TX", "geo_qpg_d"),
)
N3_METHODS = (
    ("CBBA-RB", "capacity_cbba_rb"),
    ("Pair-GRAPE", "weighted_pair_grape"),
)
METHODS = QPG_METHODS + N3_METHODS

PRIOR_WORLD_FILES = (
    "n3_v2/raw/worlds.csv",
    "n4_v1/raw/e2_replay_worlds.csv",
    "n4_v1/raw/e3_confirmatory_worlds.csv",
    "n4_v2/raw/e4_family_worlds.csv",
    "n3b_v1/raw/n3b_worlds.csv",
)


def capacity_vector(n, q_bar, cv, rng):
    """Capacidades lognormales renormalizadas a media q_bar, como en N2."""

    if cv <= 0.0:
        return np.full(n, float(q_bar), dtype=float)
    sigma = float(np.sqrt(np.log(1.0 + cv * cv)))
    mu = float(np.log(q_bar) - 0.5 * sigma * sigma)
    draw = rng.lognormal(mean=mu, sigma=sigma, size=n)
    return draw * (float(q_bar) * n / float(draw.sum()))


def make_industrial_world(*, world_id, layout, robot_count, load_count, q_bar,
                          cv, pressure, workspace, seed, alpha) -> World:
    """Mismo orden de extraccion que `sp1_n3.worlds.make_world`.

    AMR, cargas, reparto de Dirichlet desde el flujo espacial; capacidades desde
    su propio flujo. Solo cambia como se colocan los puntos.
    """

    width, height = workspace
    spatial = np.random.default_rng(seed)
    robot_positions = generate_industrial_positions(
        robot_count, role="robot", layout=layout,
        workspace_width=width, workspace_height=height, rng=spatial)
    load_positions = generate_industrial_positions(
        load_count, role="load", layout=layout,
        workspace_width=width, workspace_height=height, rng=spatial)
    supply = robot_count * q_bar
    demands = pressure * supply * spatial.dirichlet(np.full(load_count, alpha))
    cap_seed = int.from_bytes(
        hashlib.sha256(("n4h-capacity|%d|%.6f" % (seed, cv)).encode())
        .digest()[:8], "big")
    capacities = capacity_vector(robot_count, q_bar, cv,
                                 np.random.default_rng(cap_seed))
    distances = np.linalg.norm(
        robot_positions[:, None, :] - load_positions[None, :, :], axis=2)
    return World(
        world_id=world_id, scenario=layout, seed=seed,
        capacity_cv=float(cv), pressure=float(pressure),
        robot_positions=robot_positions, load_positions=load_positions,
        capacities=capacities, demands=demands, distances=distances,
    )


def world_seed(base, layout, regime, network, replicate):
    key = "N4H|%d|%s|%s|%s|%d" % (base, layout, regime, network, replicate)
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:6], "big")


def build_worlds(cfg, limit):
    base = int(cfg["base_seed"])
    rows = []
    grid = itertools.product(INDUSTRIAL_LAYOUTS, cfg["regimes"].items(),
                             cfg["networks"].items(),
                             range(int(cfg["seeds_per_cell"])))
    for layout, (rname, rspec), (nname, mult), rep in grid:
        seed = world_seed(base, layout, rname, nname, rep)
        wid = "n4h-%s-%s-%s-r%02d" % (layout, rname, nname, rep)
        world = make_industrial_world(
            world_id=wid, layout=layout,
            robot_count=int(rspec["robot_count"]),
            load_count=int(rspec["load_count"]),
            q_bar=float(cfg["q_bar_kg"]),
            cv=float(cfg["capacity_cv"]),
            pressure=float(rspec["pressure"]),
            workspace=tuple(float(v) for v in cfg["workspace_m"]),
            seed=seed, alpha=float(cfg["generator"]["demand_split_alpha"]),
        )
        rows.append({"world_id": wid, "layout": layout, "regime": rname,
                     "network": nname, "radius_multiplier": float(mult),
                     "robot_count": int(rspec["robot_count"]),
                     "load_count": int(rspec["load_count"]),
                     "pressure": float(rspec["pressure"]),
                     "replicate": rep, "world_seed": seed,
                     "world_digest": world.digest(), "world": world})
        if limit is not None and len(rows) >= limit:
            break
    return rows


def assert_holdout(rows, out):
    mine = {r["world_digest"] for r in rows}
    seen, checked = {}, []
    for rel in PRIOR_WORLD_FILES:
        path = ROOT / "scripts" / "results" / "sp1_levels" / rel
        if not path.exists():
            continue
        table = pd.read_csv(path)
        col = next((c for c in table.columns if "digest" in c), None)
        if col is None:
            continue
        checked.append(rel)
        for d in table[col].astype(str):
            seen[d] = rel
    overlap = sorted(mine & set(seen))
    report = {"n_worlds": len(rows), "n_unique": len(mine),
              "prior_files_checked": checked, "prior_digests": len(seen),
              "overlap": len(overlap)}
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "raw" / "holdout_check.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    if len(mine) != len(rows):
        raise SystemExit("ABORTA: mundos duplicados dentro de la campana")
    if overlap:
        raise SystemExit("ABORTA: %d mundos coinciden con campanas previas"
                         % len(overlap))
    return report


def run(cfg, rows):
    tl = float(cfg["oracle_time_limit_s"])
    out = []
    for i, row in enumerate(rows, 1):
        world = row["world"]
        adjacency = adjacency_for_regime(
            world.robot_positions, row["network"])
        oracle = solve_oracle(world, tl)
        hstar = None
        for tag, method in METHODS:
            t0 = time.perf_counter()
            if (tag, method) in N3_METHODS:
                rec = run_method(world, adjacency, method,
                                 regime=row["network"], max_rounds=400)
                cert = rec.certificate
                rounds = int(rec.observation.rounds)
                messages = int(rec.observation.messages)
                nbytes = int(rec.observation.bytes_sent)
                status = str(rec.observation.algorithm_status)
            else:
                res = run_geo_qpg(world, adjacency, method, max_rounds=400)
                cert = res.certificate
                rounds = int(res.rounds)
                messages = int(res.messages)
                nbytes = int(res.bytes_sent)
                status = str(res.algorithm_status)
                if tag == "BR":
                    # h_c* se mide desde el terminal de BR, igual que en N4.E9.
                    order = minimum_improving_coalition_order(
                        world, res.assignment, adjacency,
                        max_order=3, connected_only=True)
                    hstar = order.category
            out.append({
                "campaign_id": cfg["campaign_id"],
                "world_id": row["world_id"], "layout": row["layout"],
                "regime": row["regime"], "network": row["network"],
                "world_seed": row["world_seed"],
                "world_digest": row["world_digest"],
                "N": row["robot_count"], "K": row["load_count"],
                "pressure": row["pressure"],
                "method_tag": tag, "method": method,
                "algorithm_status": status,
                "capacity_deficit": float(cert.total_deficit),
                "distance_cost": float(cert.distance_cost),
                "excess_capacity": float(cert.excess_capacity),
                "assigned_robots": int(cert.assigned_robots),
                "unserved_loads": int(cert.unserved_loads),
                "feasible": bool(cert.total_deficit <= 1e-9
                                 and cert.conflicts == 0),
                "rounds": rounds, "messages": messages,
                "bytes": nbytes,
                "bytes_per_agent": float(nbytes) / world.n_robots,
                "hstar_category": hstar,
                "runtime_ms": (time.perf_counter() - t0) * 1000.0,
                **oracle,
            })
        if i % 20 == 0 or i == len(rows):
            print("   mundos %d/%d" % (i, len(rows)), flush=True)
    return pd.DataFrame(out)


def boot_ci(values, n_boot, rng, level=0.95):
    v = np.asarray(sorted(float(x) for x in values), dtype=float)
    if v.size == 0:
        return float("nan"), float("nan")
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    meds = np.median(v[idx], axis=1)
    a = (1.0 - level) / 2.0
    return float(np.quantile(meds, a)), float(np.quantile(meds, 1.0 - a))


def wilson(k, n, z=1.959963985):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100.0 * p, 100.0 * max(0.0, c - hw), 100.0 * min(1.0, c + hw)


def analyse(df, cfg):
    rng = np.random.default_rng(int(cfg["base_seed"]) ^ 0xB01)
    n_boot = int(cfg["analysis"]["bootstrap_resamples"])
    tags = [t for t, _ in METHODS]

    cert = df[df["oracle_certified"].astype(bool)
              & df["oracle_feasible"].astype(bool)].copy()
    cert["gap_pct"] = 100.0 * (cert["distance_cost"] - cert["oracle_objective"]) \
        / cert["oracle_objective"].replace(0.0, np.nan)

    piv = cert.pivot_table(index="world_id", columns="method_tag",
                           values="feasible", aggfunc="first").dropna(how="any")
    common = sorted(piv[(piv == 1).all(axis=1)].index)

    res = {"n_worlds": int(df["world_id"].nunique()),
           "n_oracle_certified": int(cert["world_id"].nunique()),
           "n_common_support": len(common), "methods": {}, "by_layout": {},
           "hstar": {}}

    gsub = cert[cert["world_id"].isin(common)]
    per = {t: gsub[gsub["method_tag"] == t].set_index("world_id")["gap_pct"]
           for t in tags}

    for t in tags:
        s = cert[cert["method_tag"] == t]
        pct, lo, hi = wilson(int(s["feasible"].sum()), len(s))
        g = per[t].reindex(common).dropna()
        gl, gh = boot_ci(g.values, n_boot, rng)
        res["methods"][t] = {
            "feasibility_pct": pct, "feas_ci_low": lo, "feas_ci_high": hi,
            "gap_median_pct": float(np.median(g.values)) if len(g) else float("nan"),
            "gap_ci_low": gl, "gap_ci_high": gh,
            "bytes_per_amr_median": float(s["bytes_per_agent"].median()),
        }

    # Cadena de filtros: de los mundos generados al soporte de cada contraste.
    feas_sets = {t: set(cert[(cert["method_tag"] == t)
                             & cert["feasible"].astype(bool)]["world_id"])
                 for t in tags}
    res["filter_chain"] = {
        "generated": int(df["world_id"].nunique()),
        "oracle_incumbent": int(df[df["oracle_feasible"].astype(bool)]
                                ["world_id"].nunique()),
        "oracle_certified": int(cert["world_id"].nunique()),
        "feasible_by_method": {t: len(v) for t, v in feas_sets.items()},
        "br_and_2br": len(feas_sets["BR"] & feas_sets["2BR"]),
        "all_methods": len(set.intersection(*feas_sets.values())),
    }

    # H-N4H.1: diferencia pareada 2BR menos BR. El estimando solo exige que
    # ambas salidas sean factibles; pedir ademas que lo sean los otros cinco
    # metodos recortaria la muestra y cambiaria la poblacion sin motivo.
    pair = sorted(feas_sets["BR"] & feas_sets["2BR"])
    gp = cert.pivot_table(index="world_id", columns="method_tag",
                          values="gap_pct", aggfunc="first")
    d = (gp.loc[pair, "2BR"] - gp.loc[pair, "BR"]).dropna()
    lo, hi = boot_ci(d.values, n_boot, rng)
    better = int((d.values < 0).sum())
    res["h1_vs_h2_paired"] = {
        "support": "mundos certificados con BR y 2BR factibles",
        "n": int(len(d)), "median_pp": float(np.median(d.values)),
        "ci_low": lo, "ci_high": hi, "excludes_zero": bool(hi < 0 or lo > 0),
        "worlds_h2_better": better,
        "worlds_h2_better_pct": 100.0 * better / max(len(d), 1),
    }
    # Se conserva el valor sobre el soporte de los siete metodos, que es el que
    # usan las comparaciones cruzadas de la tabla de metodos.
    d7 = (per["2BR"].reindex(common) - per["BR"].reindex(common)).dropna()
    lo7, hi7 = boot_ci(d7.values, n_boot, rng)
    res["h1_vs_h2_paired_seven_method_support"] = {
        "n": int(len(d7)), "median_pp": float(np.median(d7.values)),
        "ci_low": lo7, "ci_high": hi7,
    }

    # H-N4H.3: sobrecoste de DMIS+TX frente a 2BR, pareado.
    b = df.pivot_table(index="world_id", columns="method_tag",
                       values="bytes_per_agent", aggfunc="first").dropna(how="any")
    db = (b["DMIS+TX"] - b["CF"]).dropna()
    blo, bhi = boot_ci(db.values, n_boot, rng)
    res["dmis_byte_overhead"] = {
        "reference": "CF (confirmacion con orden global)",
        "n": int(len(db)), "median": float(np.median(db.values)),
        "ci_low": blo, "ci_high": bhi,
    }

    # H-N4H.2: distribucion de h_c*.
    h = df[df["method_tag"] == "BR"]["hstar_category"].value_counts()
    total = int(h.sum())
    res["hstar"] = {"n": total,
                    "counts": {str(k): int(v) for k, v in h.items()},
                    "pct": {str(k): 100.0 * int(v) / total for k, v in h.items()}}

    for layout in sorted(df["layout"].unique()):
        sub = cert[cert["layout"] == layout]
        loc = sorted(set(sub[sub["feasible"].astype(bool)]["world_id"])
                     & set(common))
        entry = {"n_common": len(loc)}
        for t in tags:
            g = sub[(sub["method_tag"] == t) & sub["world_id"].isin(loc)]["gap_pct"]
            entry[t] = float(np.median(g)) if len(g) else float("nan")
        hs = df[(df["layout"] == layout) & (df["method_tag"] == "BR")]
        vc = hs["hstar_category"].value_counts()
        n = int(vc.sum())
        entry["hstar_pct"] = {str(k): 100.0 * int(v) / n for k, v in vc.items()}
        res["by_layout"][layout] = entry
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path,
                    default=ROOT / "experiments" / "configs"
                    / "sp1_n4_industrial_holdout_v1.yaml")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    out = OUT if not args.smoke else OUT.with_name("n4_holdout_v1_smoke")
    (out / "raw").mkdir(parents=True, exist_ok=True)

    print("N4 · hold-out industrial")
    print("configuracion:", args.config.name,
          "sha256", hashlib.sha256(args.config.read_bytes()).hexdigest()[:16])

    rows = build_worlds(cfg, 24 if args.smoke else None)
    print("mundos generados:", len(rows))
    rep = assert_holdout(rows, out)
    print("hold-out disjunto: %d propios, %d previos, solape %d"
          % (rep["n_unique"], rep["prior_digests"], rep["overlap"]))

    df = run(cfg, rows)
    raw = out / "raw" / "n4_holdout_runs.csv"
    df.to_csv(raw, index=False)
    print("RAW escrito:", raw, "(%d filas)" % len(df))
    pd.DataFrame([{k: r[k] for k in r if k != "world"} for r in rows]).to_csv(
        out / "raw" / "n4_holdout_worlds.csv", index=False)

    res = analyse(df, cfg)
    res["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
    }
    (out / "raw" / "n4_holdout_analysis.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")

    print("\nmundos %d   certificados %d   soporte comun %d"
          % (res["n_worlds"], res["n_oracle_certified"], res["n_common_support"]))
    print("\n%-8s %9s %22s %11s" % ("metodo", "factib.%", "brecha mediana %",
                                    "bytes/AMR"))
    for t, _ in METHODS:
        m = res["methods"][t]
        print("%-8s %8.1f  %8.2f [%5.2f,%5.2f] %10.0f"
              % (t, m["feasibility_pct"], m["gap_median_pct"],
                 m["gap_ci_low"], m["gap_ci_high"], m["bytes_per_amr_median"]))
    fc = res["filter_chain"]
    print("\ncadena de filtros: %d generados -> %d con incumbente -> %d "
          "certificados" % (fc["generated"], fc["oracle_incumbent"],
                            fc["oracle_certified"]))
    print("  factibles por metodo: %s" % fc["feasible_by_method"])
    print("  BR y 2BR factibles: %d    los siete factibles: %d"
          % (fc["br_and_2br"], fc["all_methods"]))
    p = res["h1_vs_h2_paired"]
    print("\nH-N4H.1  2BR menos BR, pareado sobre %d mundos: %.2f pp "
          "(IC 95%%: %.2f a %.2f)  mejora en %.1f %%  IC excluye cero: %s"
          % (p["n"], p["median_pp"], p["ci_low"], p["ci_high"],
             p["worlds_h2_better_pct"],
             "SI" if p["excludes_zero"] else "NO"))
    p7 = res["h1_vs_h2_paired_seven_method_support"]
    print("         sobre el soporte de los siete metodos (n=%d): %.2f pp "
          "[%.2f, %.2f]" % (p7["n"], p7["median_pp"], p7["ci_low"],
                            p7["ci_high"]))
    print("h_c* (n=%d): %s" % (res["hstar"]["n"],
                               {k: round(v, 1) for k, v in res["hstar"]["pct"].items()}))
    print("\nbrecha mediana por planta:")
    for layout, e in res["by_layout"].items():
        print("  %-18s n=%-4d BR %6.2f  2BR %6.2f  C3 %6.2f   h*: %s"
              % (layout, e["n_common"], e["BR"], e["2BR"], e["C3"],
                 {k: round(v, 1) for k, v in e["hstar_pct"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
