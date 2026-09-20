"""SP1 · N3.B — factorial regla de revision x fitness, con el orden h fijo en 1.

POR QUE EXISTE
    N4 atribuye la caida grande de brecha a ampliar el ORDEN de la vecindad
    (h = 1 -> h = 2). Hasta ahora ASR y LLL se ejecutaron con un unico fitness,
    de modo que "regla de revision" y "fitness" nunca se separaron. Sin este
    contraste, N4 solo puede decir "las variantes evaluadas no reprodujeron la
    mejora". Con el puede decir "ninguna combinacion de regla y fitness a h = 1
    la reprodujo", si los datos lo sostienen.

QUE SE MANTIENE FIJO
    La aceptacion es lexicografica sobre (D4, J4) y es IDENTICA en las nueve
    celdas: `_admissible` no se toca. Lo unico que varia entre celdas es como se
    ORDENAN los candidatos ya admisibles. Asi el contraste aisla regla y fitness
    y no el criterio de aceptacion.

BANCO
    Flujo de semillas nuevo. La disyuncion frente a n1_v2, n2_v1, n3_v2, n4_v1,
    n4_v2, n4_v3 y n4_v4 se verifica por digest de contenido ANTES de cualquier
    analisis, y la campana aborta si la interseccion no es vacia.

    python scripts/sp1_n3b_revision_fitness.py --config experiments/configs/sp1_n3b_revision_fitness_v1.yaml
    python scripts/sp1_n3b_revision_fitness.py --smoke     # 20 mundos
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
from viu_mrob_tfm.sp1_n3.worlds import make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import run_geo_qpg  # noqa: E402

OUT = ROOT / "scripts" / "results" / "sp1_levels" / "n3b_v2"

# Tres reglas con h = 1 y un brazo de control con h = 2. El control es lo que
# permite atribuir la diferencia al orden: sin el, la comparacion seria contra
# una campana distinta y no habria contraste pareado posible.
RULES = (("BR", "geo_qpg_u"), ("ASR", "geo_qpg_smith"),
         ("LLL", "geo_qpg_lll"), ("2BR", "geo_qpg_p"))
ORDER_OF = {"BR": 1, "ASR": 1, "LLL": 1, "2BR": 2}
CONTROL = "2BR"
FITNESS = ("F0", "F1", "F2")

# Campanas cuyos mundos NO pueden reaparecer aqui.
PRIOR_WORLD_FILES = (
    "n3_v2/raw/worlds.csv",
    "n4_v1/raw/e2_replay_worlds.csv",
    "n4_v1/raw/e3_confirmatory_worlds.csv",
    "n4_v2/raw/e4_family_worlds.csv",
    "n3b_v1/raw/n3b_worlds.csv",
)


# --------------------------------------------------------------------------
# Banco
# --------------------------------------------------------------------------
def world_seed(base: int, scenario: str, cv: float, pressure: float,
               replicate: int) -> int:
    """Semilla derivada por hash: flujo propio, no un desplazamiento del previo.

    Un desplazamiento constante sobre las semillas de otra campana produciria
    solapamiento en cuanto dos campanas usaran el mismo paso. El hash del
    identificador completo hace que la coincidencia sea un accidente
    detectable, y por eso se verifica por digest de contenido.
    """

    key = "N3B|%d|%s|%.4f|%.4f|%d" % (base, scenario, cv, pressure, replicate)
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:6], "big")


def build_worlds(cfg: dict, limit: int | None) -> list[dict]:
    w = cfg["worlds"]
    base = int(cfg["base_seed"])
    rows = []
    grid = itertools.product(w["scenarios"], w["capacity_cv"], w["pressure"],
                             range(int(w["seeds_per_cell"])))
    for scenario, cv, pressure, rep in grid:
        seed = world_seed(base, scenario, float(cv), float(pressure), rep)
        wid = "n3b-%s-cv%.2f-p%.2f-r%02d" % (scenario, cv, pressure, rep)
        world = make_world(
            world_id=wid,
            robot_count=int(w["robot_count"]),
            load_count=int(w["load_count"]),
            q_bar=float(cfg["q_bar_kg"]),
            cv=float(cv),
            pressure=float(pressure),
            scenario=scenario,
            workspace=tuple(float(v) for v in cfg["workspace_m"]),
            seed=seed,
            alpha=float(cfg["generator"]["demand_split_alpha"]),
        )
        rows.append({"world_id": wid, "scenario": scenario,
                     "capacity_cv": float(cv), "pressure": float(pressure),
                     "replicate": rep, "world_seed": seed,
                     "world_digest": world.digest(), "world": world})
        if limit is not None and len(rows) >= limit:
            break
    return rows


def assert_holdout(rows: list[dict]) -> dict:
    """Aborta si algun mundo ya aparecio en una campana previa.

    v1 se excluye a proposito: v2 reutiliza sus MISMOS mundos para poder parear
    el brazo de control con las nueve celdas unilaterales. Reutilizarlos no es
    una fuga, porque ninguno participo en el diseno del metodo; lo que seria un
    defecto es compararlos sin parear, que es justo lo que v2 corrige.
    """

    mine = {r["world_digest"] for r in rows}
    seen: dict[str, str] = {}
    checked = []
    for rel in PRIOR_WORLD_FILES:
        if rel.startswith("n3b_v1/"):
            continue
        path = ROOT / "scripts" / "results" / "sp1_levels" / rel
        if not path.exists():
            continue
        col = pd.read_csv(path)
        name = next((c for c in col.columns if "digest" in c), None)
        if name is None:
            continue
        checked.append(rel)
        for d in col[name].astype(str):
            seen[d] = rel
    overlap = sorted(mine & set(seen))
    report = {"n_worlds": len(rows), "n_unique": len(mine),
              "prior_files_checked": checked,
              "prior_digests": len(seen), "overlap": len(overlap)}
    if len(mine) != len(rows):
        raise SystemExit("ABORTA: hay mundos duplicados dentro de la campana")
    if overlap:
        report["examples"] = overlap[:5]
        (OUT / "raw").mkdir(parents=True, exist_ok=True)
        (OUT / "raw" / "holdout_check.json").write_text(
            json.dumps(report, indent=1), encoding="utf-8")
        raise SystemExit(
            "ABORTA: %d mundos coinciden con campanas previas" % len(overlap))
    return report


# --------------------------------------------------------------------------
# Ejecucion
# --------------------------------------------------------------------------
def run(cfg: dict, rows: list[dict]) -> pd.DataFrame:
    fixed = cfg["fixed_across_cells"]
    max_rounds = int(fixed["max_rounds"])
    beta = float(fixed["beta_lll"])
    regime = cfg["worlds"]["graph_regime"]
    tl = float(cfg["worlds"]["oracle_time_limit_s"])
    out = []
    for i, row in enumerate(rows, 1):
        world = row["world"]
        adjacency = adjacency_for_regime(world.robot_positions, regime)
        oracle = solve_oracle(world, tl)
        for rule_tag, method in RULES:
            for fit in FITNESS:
                t0 = time.perf_counter()
                res = run_geo_qpg(world, adjacency, method,
                                  max_rounds=max_rounds, fitness=fit)
                cert = res.certificate
                out.append({
                    "campaign_id": cfg["campaign_id"],
                    "world_id": row["world_id"],
                    "world_seed": row["world_seed"],
                    "world_digest": row["world_digest"],
                    "scenario": row["scenario"],
                    "capacity_cv": row["capacity_cv"],
                    "pressure": row["pressure"],
                    "replicate": row["replicate"],
                    "strategic_order": ORDER_OF[rule_tag],
                    "revision_rule": rule_tag,
                    "fitness": fit,
                    "cell": "%s-%s" % (rule_tag, fit),
                    "method": method,
                    "beta_lll": beta,
                    "algorithm_status": res.algorithm_status,
                    "terminal_phase": res.terminal_phase,
                    "capacity_deficit": float(cert.total_deficit),
                    "distance_cost": float(cert.distance_cost),
                    "excess_capacity": float(cert.excess_capacity),
                    "assigned_robots": int(cert.assigned_robots),
                    "unserved_loads": int(cert.unserved_loads),
                    "feasible": bool(cert.total_deficit <= 1e-9
                                     and cert.conflicts == 0),
                    "rounds": int(res.rounds),
                    "messages": int(res.messages),
                    "bytes": int(res.bytes_sent),
                    "commits": int(res.commits),
                    "bytes_per_agent": float(res.bytes_sent) / world.n_robots,
                    "runtime_ms": (time.perf_counter() - t0) * 1000.0,
                    **oracle,
                })
        if i % 20 == 0 or i == len(rows):
            print("   mundos %d/%d" % (i, len(rows)), flush=True)
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# Analisis preespecificado
# --------------------------------------------------------------------------
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
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100.0 * p, 100.0 * max(0.0, c - h), 100.0 * min(1.0, c + h)


def holm(pvalues: dict) -> dict:
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def analyse(df: pd.DataFrame, cfg: dict) -> dict:
    rng = np.random.default_rng(int(cfg["base_seed"]) ^ 0xA17)
    n_boot = int(cfg["analysis"]["bootstrap_resamples"])
    cells = ["%s-%s" % (r, f) for r, _ in RULES for f in FITNESS]

    cert = df[df["oracle_certified"] & df["oracle_feasible"]]
    by_world = cert.pivot_table(index="world_id", columns="cell",
                                values="feasible", aggfunc="first")
    have_all = by_world.dropna(how="any")
    common = sorted(have_all[(have_all == 1).all(axis=1)].index)

    gaps = cert.copy()
    gaps["gap_pct"] = 100.0 * (gaps["distance_cost"] - gaps["oracle_objective"]) \
        / gaps["oracle_objective"].replace(0.0, np.nan)

    result = {"n_worlds": int(df["world_id"].nunique()),
              "n_oracle_feasible": int(cert["world_id"].nunique()),
              "n_common_support": len(common),
              "cells": {}}

    gcom = gaps[gaps["world_id"].isin(common)]
    per_world = {c: gcom[gcom["cell"] == c].set_index("world_id")["gap_pct"]
                 for c in cells}

    for c in cells:
        sub = cert[cert["cell"] == c]
        k = int(sub["feasible"].sum())
        n = int(len(sub))
        pct, lo, hi = wilson(k, n)
        g = per_world[c].reindex(common).dropna()
        gl, gh = boot_ci(g.values, n_boot, rng)
        result["cells"][c] = {
            "feasibility_pct": pct, "feas_ci_low": lo, "feas_ci_high": hi,
            "n_feasible": k, "n_certified": n,
            "gap_median_pct": float(np.median(g.values)) if len(g) else float("nan"),
            "gap_ci_low": gl, "gap_ci_high": gh,
            "bytes_per_amr_median": float(sub["bytes_per_agent"].median()),
            "rounds_median": float(sub["rounds"].median()),
        }
    return result


def paired_order_effect(df: pd.DataFrame, cfg: dict) -> dict:
    """Efecto de pasar de h=1 a h=2 sobre LOS MISMOS mundos, por fitness.

    Estimando: mediana de G(2BR,F) - G(BR,F) por mundo, sobre los mundos en que
    ambas salidas son factibles y el oraculo certifico el optimo. Es el
    contraste que faltaba en v1.
    """

    rng = np.random.default_rng(int(cfg["base_seed"]) ^ 0x2B2)
    n_boot = int(cfg["analysis"]["bootstrap_resamples"])
    cert = df[df["oracle_certified"].astype(bool)
              & df["oracle_feasible"].astype(bool)].copy()
    cert["gap_pct"] = 100.0 * (cert["distance_cost"] - cert["oracle_objective"]) \
        / cert["oracle_objective"].replace(0.0, np.nan)

    out = {"estimand": "mediana de G(2BR,F) menos G(BR,F), pareada por mundo",
           "by_fitness": {}, "pvalues": {}}
    for fit in FITNESS:
        sub = cert[cert["fitness"] == fit]
        piv = sub.pivot_table(index="world_id", columns="revision_rule",
                              values="gap_pct", aggfunc="first")
        feas = sub.pivot_table(index="world_id", columns="revision_rule",
                               values="feasible", aggfunc="first")
        ok = feas.index[(feas.get("BR", 0) == 1) & (feas.get(CONTROL, 0) == 1)]
        d = (piv.loc[ok, CONTROL] - piv.loc[ok, "BR"]).dropna()
        lo, hi = boot_ci(d.values, n_boot, rng)
        # Signo pareado: proporcion de mundos en que h=2 mejora.
        better = int((d.values < 0).sum())
        out["by_fitness"][fit] = {
            "n_paired": int(len(d)),
            "median_pp": float(np.median(d.values)) if len(d) else float("nan"),
            "ci_low": lo, "ci_high": hi,
            "excludes_zero": bool(hi < 0 or lo > 0),
            "worlds_h2_better": better,
            "worlds_h2_better_pct": 100.0 * better / max(len(d), 1),
        }
    return out


def compare_with_n4(result: dict, cells: list[str]) -> dict:
    """Contrasta cada celda con la brecha de 2BR (h = 2) de la campana N4.E4.

    2BR no se re-ejecuta aqui: su valor procede del RAW congelado de n4_v2, que
    esta campana no toca. La comparacion es por tanto entre bancos distintos y
    se declara como tal.
    """

    path = ROOT / "scripts" / "results" / "sp1_levels" / "n4_v2" / "raw" / \
        "e4_family_runs.csv"
    if not path.exists():
        return {"available": False}
    n4 = pd.read_csv(path)
    n4 = n4[(n4["method"] == "geo_qpg_p") & n4["oracle_certified"].astype(bool)
            & n4["oracle_feasible"].astype(bool)]
    n4 = n4[n4["feasible"].astype(bool)]
    gap = 100.0 * (n4["distance_cost"] - n4["oracle_objective"]) \
        / n4["oracle_objective"].replace(0.0, np.nan)
    ref = float(np.nanmedian(gap))
    out = {"available": True, "reference_cell": "2BR (h=2, campana n4_v2)",
           "reference_gap_median_pct": ref, "n_reference": int(gap.notna().sum()),
           "status": "DESCRIPTIVO, NO INFERENCIAL",
           "note": ("La referencia procede de OTRA poblacion de mundos. Un "
                    "intervalo calculado sobre este banco no puede excluirla en "
                    "sentido inferencial. El contraste valido del efecto del "
                    "orden es `paired_order_effect`, pareado mundo a mundo. "
                    "Este bloque se conserva solo como contexto historico y no "
                    "debe citarse como test."),
           "cells": {}}
    for c in cells:
        cell = result["cells"][c]
        out["cells"][c] = {
            "gap_median_pct": cell["gap_median_pct"],
            "excess_over_2br_pp": cell["gap_median_pct"] - ref,
            "ci_excludes_reference": not (
                cell["gap_ci_low"] <= ref <= cell["gap_ci_high"]),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path,
                    default=ROOT / "experiments" / "configs"
                    / "sp1_n3b_revision_fitness_v1.yaml")
    ap.add_argument("--smoke", action="store_true",
                    help="20 mundos, para verificar la tuberia")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    out = OUT if not args.smoke else OUT.with_name("n3b_v1_smoke")
    (out / "raw").mkdir(parents=True, exist_ok=True)

    print("N3.B · factorial regla x fitness, h = 1")
    print("configuracion:", args.config.name,
          "sha256", hashlib.sha256(args.config.read_bytes()).hexdigest()[:16])

    rows = build_worlds(cfg, 20 if args.smoke else None)
    print("mundos generados:", len(rows))

    report = assert_holdout(rows)
    print("hold-out disjunto: %d digests propios, %d previos, solape %d"
          % (report["n_unique"], report["prior_digests"], report["overlap"]))
    (out / "raw" / "holdout_check.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")

    df = run(cfg, rows)
    raw = out / "raw" / "n3b_factorial_runs.csv"
    df.to_csv(raw, index=False)
    print("RAW escrito:", raw, "(%d filas)" % len(df))

    pd.DataFrame([{k: r[k] for k in r if k != "world"} for r in rows]).to_csv(
        out / "raw" / "n3b_worlds.csv", index=False)

    result = analyse(df, cfg)
    cells = ["%s-%s" % (r, f) for r, _ in RULES for f in FITNESS]
    result["paired_order_effect"] = paired_order_effect(df, cfg)
    result["vs_n4_2br"] = compare_with_n4(result, cells)
    result["environment"] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
    }
    (out / "raw" / "n3b_analysis.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")

    print("\nmundos: %d   oraculo factible: %d   soporte comun: %d"
          % (result["n_worlds"], result["n_oracle_feasible"],
             result["n_common_support"]))
    print("\n%-8s %10s %20s %12s" % ("celda", "factib.%", "brecha mediana %",
                                     "bytes/AMR"))
    for c in cells:
        d = result["cells"][c]
        print("%-8s %9.1f  %8.2f [%5.2f,%5.2f] %10.0f"
              % (c, d["feasibility_pct"], d["gap_median_pct"],
                 d["gap_ci_low"], d["gap_ci_high"], d["bytes_per_amr_median"]))
    print("\nH-N3B.1v2 · efecto pareado de pasar de h=1 a h=2, por fitness")
    for fit, d in result["paired_order_effect"]["by_fitness"].items():
        print("  %-3s n=%3d  %7.2f pp  IC [%6.2f, %6.2f]  mejora en %5.1f %% "
              "de los mundos  IC excluye cero: %s"
              % (fit, d["n_paired"], d["median_pp"], d["ci_low"], d["ci_high"],
                 d["worlds_h2_better_pct"],
                 "SI" if d["excludes_zero"] else "NO"))
    v = result["vs_n4_2br"]
    if v.get("available"):
        print("\nreferencia 2BR (h=2, n4_v2): %.2f %%" % v["reference_gap_median_pct"])
        worse = [c for c in cells if v["cells"][c]["ci_excludes_reference"]
                 and v["cells"][c]["excess_over_2br_pp"] > 0]
        print("   (descriptivo: otra poblacion de mundos; el contraste valido "
              "es el pareado de arriba)")
        print("   celdas por encima de esa referencia: %d de %d"
              % (len(worse), len(cells)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
