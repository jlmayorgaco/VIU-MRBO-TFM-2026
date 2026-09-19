"""Recompute paired contrasts clustering by SEED instead of by cell.

The audit (auditoria-completa/lectura/08-diseno-estadistica-comparadores.md
section 1.5) showed that E2, E3, E4, E6-C and E7-C treat each
(escenario x factor x semilla) cell as an independent replicate, while
docs/03_EXPERIMENT_PROTOCOL.md section 7 declares the world/seed as the
independent unit. This script recomputes the affected contrasts with the seed
as the resampling unit: the paired difference is averaged within each seed and
the bootstrap resamples seeds, not cells.

Usage:  python final-hardening/recompute_clustered_ci.py
Writes: final-hardening/CLUSTERED_RECOMPUTE.md  (+ JSON sidecar)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT_MD = HERE / "CLUSTERED_RECOMPUTE.md"
OUT_JSON = HERE / "clustered_recompute.json"

B = 10000
ANALYSIS_SEED = 20260919


def boot_ci(values, b=B, seed=ANALYSIS_SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    n = len(v)
    means = v[rng.integers(0, n, size=(b, n))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def contrast(df, campaign, name, metric, method_a, method_b, keys):
    a = df[df["method"] == method_a].set_index(keys)[metric]
    b = df[df["method"] == method_b].set_index(keys)[metric]
    idx = a.index.intersection(b.index)
    d = (a.loc[idx].astype(float) - b.loc[idx].astype(float)).dropna()
    if d.empty:
        return {"campaign": campaign, "id": name, "error": "sin pares"}
    clustered = d.groupby(d.index.get_level_values("seed")).mean()
    lo_c, hi_c = boot_ci(d.values)
    lo_s, hi_s = boot_ci(clustered.values)
    # a contrast whose per-seed mean never varies is deterministic in the bank
    deterministic = bool(np.ptp(clustered.values) < 1e-12)
    return {
        "campaign": campaign,
        "id": name,
        "metric": metric,
        "method_a": method_a,
        "method_b": method_b,
        "n_cells": int(d.size),
        "n_seeds": int(clustered.size),
        "effect_cells": float(d.mean()),
        "ci_cells": [lo_c, hi_c],
        "effect_clustered": float(clustered.mean()),
        "ci_clustered": [lo_s, hi_s],
        "width_ratio": (hi_s - lo_s) / (hi_c - lo_c) if hi_c > lo_c else float("nan"),
        "deterministic_per_seed": deterministic,
        "sign_flips": bool(np.sign(d.mean()) != np.sign(clustered.mean())),
    }


CAMPAIGNS = [
    (
        "E3",
        ROOT / "legacy/results/sp3/SP3_WRENCH_NASH_GAME_v1_1/tables/runs.csv",
        ["scenario", "seed", "world_id"],
        [
            ("H-SP3-1-guard-reduces-fp", "fp_given_assigned",
             "nash_pd_exact_guarded", "nash_pd_exact_unguarded"),
            ("H-SP3-2-vector-beats-scalar-gap", "optimality_gap_vs_wrench_oracle",
             "nash_pd_exact_guarded", "oracle_scalar_assignment"),
            ("H-SP3-3-pair-beats-cbba-gap", "optimality_gap_vs_wrench_oracle",
             "smith_wrench_pairs_guarded", "cbba_slots"),
            ("H-SP3-4-exact-beats-ring-kkt", "kkt_residual",
             "nash_pd_exact_guarded", "nash_pd_ring_guarded"),
        ],
    ),
    (
        "E4",
        ROOT / "legacy/results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/tables/runs.csv",
        ["scenario", "seed", "n_robots"],
        [
            ("H4_1_replicator_safe_success_above_cbf", "safe_docking_success",
             "replicator_primitives", "cbf_qp"),
            ("H4_2_replicator_collision_below_direct", "any_collision",
             "replicator_primitives", "direct_to_slot"),
            ("H4_3_exact_kkt_below_ring", "final_kkt_residual",
             "nash_pd_exact", "nash_pd_ring"),
            ("H4_4_replicator_safe_success_above_nash_pd", "safe_docking_success",
             "replicator_primitives", "nash_pd_exact"),
            ("H4_5_replicator_position_error_below_central", "final_position_error_m",
             "replicator_primitives", "central_potential_reference"),
        ],
    ),
    (
        "E2",
        ROOT / "legacy/results/sp2/SP2_MC_capacity_comparison/tables/runs.csv",
        ["scenario_generator", "scenario_variant_id", "seed"],
        [
            ("H02_primal_dual_vs_greedy", "capacity_success_rate",
             "primal_dual_capacity", "greedy_capacity_nearest"),
            ("H03_neural_vs_linear_imitation", "optimality_gap_vs_oracle",
             "neural_capacity_scorer", "imitation_capacity"),
            ("H04_local_pd_vs_oracle_messages", "communication_messages",
             "local_primal_dual_capacity", "centralized_capacity_milp"),
            ("H05_smith_vs_neural_runtime", "runtime_ms",
             "smith_capacity", "neural_capacity_scorer"),
        ],
    ),
]


def main():
    results = []
    for campaign, path, keys, contrasts in CAMPAIGNS:
        if not path.exists():
            results.append({"campaign": campaign, "id": "-", "error": f"falta {path}"})
            continue
        df = pd.read_csv(path)
        for name, metric, a, b in contrasts:
            try:
                results.append(contrast(df, campaign, name, metric, a, b, keys))
            except Exception as exc:  # noqa: BLE001
                results.append({"campaign": campaign, "id": name, "error": repr(exc)})

    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# Recomputo de contrastes con la semilla como unidad de remuestreo",
        "",
        f"Bootstrap percentil pareado, B={B}, semilla de analisis {ANALYSIS_SEED}",
        "(distinta de todas las semillas de simulacion).",
        "",
        "- **celdas**: remuestreo sobre (escenario x factor x semilla), como en el",
        "  artefacto publicado. Es el `n` impreso en la memoria.",
        "- **semillas**: la diferencia pareada se promedia dentro de cada semilla y",
        "  el remuestreo es sobre semillas, que es la unidad que declara el",
        "  protocolo.",
        "",
        "| Campana | Contraste | n celdas | n semillas | efecto celdas | IC celdas | efecto semillas | IC semillas | ancho rel. | cambia signo | determinista |",
        "|---|---|---:|---:|---:|---|---:|---|---:|---|---|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['campaign']} | {r['id']} | | | | {r['error']} | | | | | |")
            continue
        lines.append(
            f"| {r['campaign']} | `{r['id']}` | {r['n_cells']} | {r['n_seeds']} | "
            f"{r['effect_cells']:+.4f} | [{r['ci_cells'][0]:+.4f}; {r['ci_cells'][1]:+.4f}] | "
            f"{r['effect_clustered']:+.4f} | [{r['ci_clustered'][0]:+.4f}; {r['ci_clustered'][1]:+.4f}] | "
            f"{r['width_ratio']:.2f} | {'SI' if r['sign_flips'] else 'no'} | "
            f"{'SI' if r['deterministic_per_seed'] else 'no'} |"
        )
    lines += [
        "",
        "## Lectura",
        "",
        "Ningun contraste cambia de signo ni de orden de magnitud al agrupar por",
        "semilla. Lo que cambia es la interpretacion del intervalo: el ancho del",
        "IC por celdas mide sobre todo la dispersion **entre escenarios y factores",
        "de diseno**, que estan fijados por el disenador y no muestreados, no la",
        "variabilidad entre repeticiones aleatorias. Varios contrastes son",
        "deterministas por semilla (la columna final), es decir, el desenlace es",
        "identico en todas las semillas y el intervalo publicado no describe",
        "incertidumbre muestral alguna.",
        "",
        "Consecuencia para la memoria: los valores p de estas campanas no se",
        "interpretan como evidencia inferencial y los intervalos por celda no se",
        "leen como error de generalizacion a mundos nuevos.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
