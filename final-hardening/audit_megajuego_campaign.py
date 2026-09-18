"""A0 - Auditoria forense de results/megajuego/.

Determina, sin suponer nada:
  - cuantas rejillas hay y como se llaman
  - factores y niveles por rejilla
  - N REAL de semillas independientes (no robots, no pasos temporales)
  - si las celdas de una rejilla comparten el mismo conjunto de semillas (pareado)
  - corridas totales por rejilla y en conjunto
  - hashes de auditoria de datos crudos y scripts

Uso: python final-hardening/audit_megajuego_campaign.py
"""
import hashlib
import io
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMP = os.path.join(ROOT, "results", "megajuego")
SRC = os.path.join(ROOT, "src", "viu_mrob_tfm", "megajuego")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    grids = sorted(f[:-4] for f in os.listdir(CAMP) if f.endswith(".csv"))
    print("REJILLAS ENCONTRADAS: %d" % len(grids))
    print("  " + ", ".join(grids))
    print()

    total_runs = 0
    all_seeds = set()
    report = []

    for g in grids:
        path = os.path.join(CAMP, g + ".csv")
        d = pd.read_csv(path)
        cfg_cols = [c for c in d.columns if c.startswith("cfg_")]
        # una celda = combinacion de niveles de los factores
        if cfg_cols:
            cells = d.groupby(cfg_cols, dropna=False)
        else:
            cells = [((), d)]
        cell_list = list(cells) if cfg_cols else cells

        seeds_per_cell = {}
        for key, sub in cell_list:
            k = key if isinstance(key, tuple) else (key,)
            seeds_per_cell[k] = sorted(sub["seed"].unique().tolist())

        seed_sets = [tuple(v) for v in seeds_per_cell.values()]
        paired = len(set(seed_sets)) == 1
        n_seeds = len(seed_sets[0]) if seed_sets else 0
        uniq_seeds = sorted({s for v in seeds_per_cell.values() for s in v})

        total_runs += len(d)
        all_seeds.update(uniq_seeds)

        levels = {c: sorted(map(str, d[c].dropna().unique().tolist())) for c in cfg_cols}

        report.append(
            dict(
                grid_id=g,
                factors=cfg_cols,
                levels=levels,
                n_cells=len(seeds_per_cell),
                seeds_per_cell=n_seeds,
                paired_seed_set=bool(paired),
                seed_min=min(uniq_seeds) if uniq_seeds else None,
                seed_max=max(uniq_seeds) if uniq_seeds else None,
                n_distinct_seeds=len(uniq_seeds),
                total_rows=len(d),
                sha256=sha256(path),
                columns=list(d.columns),
            )
        )

        print("=== %s ===" % g)
        print("  factores      : %s" % (cfg_cols or "(ninguno)"))
        for c, lv in levels.items():
            print("    %-22s %s" % (c, lv))
        print("  celdas        : %d" % len(seeds_per_cell))
        print("  semillas/celda: %d   %s" % (n_seeds, "PAREADO (mismo conjunto)" if paired else "NO PAREADO"))
        print("  semillas      : %d distintas, rango [%s, %s]"
              % (len(uniq_seeds), min(uniq_seeds) if uniq_seeds else "-", max(uniq_seeds) if uniq_seeds else "-"))
        print("  filas totales : %d   (= celdas x semillas = %d)" % (len(d), len(seeds_per_cell) * n_seeds))
        if len(d) != len(seeds_per_cell) * n_seeds:
            print("  AVISO: filas != celdas x semillas")
        print("  sha256        : %s" % sha256(path)[:32])
        print()

    print("TOTAL corridas crudas en la campana: %d" % total_runs)
    print("Union de semillas usadas          : %d  %s"
          % (len(all_seeds), sorted(all_seeds)[:8]))
    print()

    print("=== HASHES DE AUDITORIA DEL CODIGO (no son los hashes de generacion) ===")
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".py"):
            p = os.path.join(SRC, f)
            print("  %-22s %s" % (f, sha256(p)[:32]))

    out = os.path.join(ROOT, "final-hardening", "megajuego_campaign_inventory.json")
    io.open(out, "w", encoding="utf8").write(
        json.dumps(
            dict(
                campaign_dir=os.path.relpath(CAMP, ROOT).replace("\\", "/"),
                grids=report,
                total_raw_runs=total_runs,
                union_of_seeds=sorted(all_seeds),
                code_audit_sha256={
                    f: sha256(os.path.join(SRC, f))
                    for f in sorted(os.listdir(SRC))
                    if f.endswith(".py")
                },
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
    print("\nJSON -> %s" % os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
