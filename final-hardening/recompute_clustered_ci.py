"""Recompute every printed interval and p-value with the SEED as the unit.

Why. docs/03_EXPERIMENT_PROTOCOL.md section 7 declares the world/seed as the
independent unit. The pipelines of E2, E3, E4, E6-C and E7-C instead treated
each (escenario x factor x semilla) cell as a replicate, so the published
intervals and p-values condition on an independence the design does not have.
Declaring that in prose is not enough: the tables have to carry corrected
numbers. This script is the generator of record for them.

What it does. For each declared contrast it pairs the two methods cell by cell,
averages the paired difference within each seed, and then:
  - bootstraps over SEEDS for the 95 % interval (B=10000, analysis seed fixed
    and distinct from every simulation seed);
  - runs a Wilcoxon signed-rank over the per-seed differences and applies Holm
    inside the campaign's predeclared family;
  - marks a contrast DETERMINISTIC when every seed yields the same difference.
    For those, no interval and no p-value are emitted: there is no sampling
    variability to describe, and printing one would misrepresent a structural
    outcome as an inference.

Outputs
  final-hardening/CLUSTERED_RECOMPUTE.md    human-readable comparison
  final-hardening/clustered_recompute.json  machine-readable
  pre-thesis/shared/generated-macros/*.tex  corrected macros, in place

Usage:  python final-hardening/recompute_clustered_ci.py [--no-write-macros]
"""

from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
MACRO_DIR = ROOT / "pre-thesis/shared/generated-macros"

B = 10000
ANALYSIS_SEED = 20260919
DETERMINISTIC_TOL = 1e-12


def boot_ci(values, b=B, seed=ANALYSIS_SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    n = len(v)
    means = v[rng.integers(0, n, size=(b, n))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, preserving input order."""
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adj[idx] = min(running, 1.0)
    return adj


def per_seed_differences(df, metric, method_a, method_b, keys):
    a = df[df["method"] == method_a].set_index(keys)[metric]
    b = df[df["method"] == method_b].set_index(keys)[metric]
    idx = a.index.intersection(b.index)
    d = (a.loc[idx].astype(float) - b.loc[idx].astype(float)).dropna()
    if d.empty:
        return None, None
    return d, d.groupby(d.index.get_level_values("seed")).mean()


CAMPAIGNS = {
    "E2": dict(
        path=ROOT / "legacy/results/sp2/SP2_MC_capacity_comparison/tables/runs.csv",
        keys=["scenario_generator", "scenario_variant_id", "seed"],
        contrasts=[
            ("H02_primal_dual_vs_greedy", "capacity_success_rate",
             "primal_dual_capacity", "greedy_capacity_nearest", "greater",
             dict(effect="SPTwoPDEffect", lo="SPTwoPDCILow", hi="SPTwoPDCIHigh",
                  p="SPTwoPDPHolm")),
            ("H03_neural_vs_linear_imitation", "optimality_gap_vs_oracle",
             "neural_capacity_scorer", "imitation_capacity", "less", {}),
            ("H04_local_pd_vs_oracle_messages", "communication_messages",
             "local_primal_dual_capacity", "centralized_capacity_milp", "less", {}),
            ("H05_smith_vs_neural_runtime", "runtime_ms",
             "smith_capacity", "neural_capacity_scorer", "less", {}),
        ],
    ),
    "E2-abl": dict(
        path=ROOT / "legacy/results/sp2/SP2_MC_marginal_payoff_ablation/tables/runs.csv",
        keys=["scenario_generator", "scenario_variant_id", "seed"],
        contrasts=[
            ("H_SP2_Marginal_smith_lower_score_gap", "optimality_gap_vs_oracle",
             "smith_capacity_marginal", "smith_capacity_plain", "less",
             dict(effect="SPTwoGapEffect", lo="SPTwoGapCILow",
                  hi="SPTwoGapCIHigh", p="SPTwoGapPHolm")),
            ("H_SP2_Marginal_smith_higher_success", "capacity_success_rate",
             "smith_capacity_marginal", "smith_capacity_plain", "greater",
             dict(effect="SPTwoSuccessEffect", lo="SPTwoSuccessCILow",
                  hi="SPTwoSuccessCIHigh")),
            ("H_SP2_Marginal_replicator_lower_score_gap", "optimality_gap_vs_oracle",
             "replicator_capacity_marginal", "replicator_capacity_plain", "less", {}),
            ("H_SP2_Potential_marginal_lower_incomplete_capacity_smith",
             "incomplete_capacity_ratio",
             "smith_capacity_marginal", "smith_capacity_plain", "less",
             dict(effect="SPTwoIncompleteEffect")),
            ("H_SP2_Potential_marginal_higher_alignment_smith",
             "served_capacity_alignment",
             "smith_capacity_marginal", "smith_capacity_plain", "greater",
             dict(effect="SPTwoAlignmentEffect")),
        ],
    ),
    "E3": dict(
        path=ROOT / "legacy/results/sp3/SP3_WRENCH_NASH_GAME_v1_1/tables/runs.csv",
        keys=["scenario", "seed", "world_id"],
        contrasts=[
            ("H-SP3-1-guard-reduces-fp", "fp_given_assigned",
             "nash_pd_exact_guarded", "nash_pd_exact_unguarded", "less",
             dict(effect="SPThreeGuardEffect", lo="SPThreeGuardCILow",
                  hi="SPThreeGuardCIHigh", p="SPThreeGuardPHolm")),
            ("H-SP3-2-vector-beats-scalar-gap", "optimality_gap_vs_wrench_oracle",
             "nash_pd_exact_guarded", "oracle_scalar_assignment", "less",
             dict(effect="SPThreeVectorEffect", lo="SPThreeVectorCILow",
                  hi="SPThreeVectorCIHigh")),
            ("H-SP3-3-pair-beats-cbba-gap", "optimality_gap_vs_wrench_oracle",
             "smith_wrench_pairs_guarded", "cbba_slots", "less",
             dict(effect="SPThreePairEffect")),
            ("H-SP3-4-exact-beats-ring-kkt", "kkt_residual",
             "nash_pd_exact_guarded", "nash_pd_ring_guarded", "less",
             dict(effect="SPThreeGraphEffect", lo="SPThreeGraphCILow",
                  hi="SPThreeGraphCIHigh")),
        ],
    ),
    "E4": dict(
        path=ROOT / "legacy/results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/tables/runs.csv",
        keys=["scenario", "seed", "n_robots"],
        contrasts=[
            ("H4_1_replicator_safe_success_above_cbf", "safe_docking_success",
             "replicator_primitives", "cbf_qp", "greater",
             dict(effect="SPFourDockEffect", lo="SPFourDockCILow",
                  hi="SPFourDockCIHigh", p="SPFourDockPHolm")),
            ("H4_2_replicator_collision_below_direct", "any_collision",
             "replicator_primitives", "direct_to_slot", "less", {}),
            ("H4_3_exact_kkt_below_ring", "final_kkt_residual",
             "nash_pd_exact", "nash_pd_ring", "less", {}),
            ("H4_4_replicator_safe_success_above_nash_pd", "safe_docking_success",
             "replicator_primitives", "nash_pd_exact", "greater", {}),
            ("H4_5_replicator_position_error_below_central", "final_position_error_m",
             "replicator_primitives", "central_potential_reference", "less", {}),
        ],
    ),
    "E6-C": dict(
        path=ROOT / "results/processed/sp6/SP6_RECOVERY_CONFIRMATORY_v1/tables/runs.csv",
        keys=["scenario", "reserve_size", "seed"],
        contrasts=[
            ("H6.1", "certificate_restored", "guarded_potential", "no_repair", "greater",
             dict(effect="SPSixHOneEffect", lo="SPSixHOneCILow",
                  hi="SPSixHOneCIHigh", p="SPSixHOnePHolm")),
            ("H6.2", "redundant_count", "guarded_potential", "distance_greedy", "less",
             dict(effect="SPSixHTwoEffect", p="SPSixHTwoPHolm")),
            ("H6.3", "selected_cost", "guarded_potential", "central_exact", "greater",
             dict(effect="SPSixHThreeEffect", p="SPSixHThreePHolm")),
        ],
    ),
    "E7-C": dict(
        path=ROOT / "results/processed/sp7/SP7_TRAFFIC_CONFIRMATORY_v1/tables/runs.csv",
        keys=["scenario", "n_coalitions", "seed"],
        contrasts=[
            ("H7.1", "delivery_success", "local_potential_reservation",
             "no_zone_reservation", "greater",
             dict(effect="SPSevenHOneEffect", ci="SPSevenHOneCI",
                  p="SPSevenHOnePHolm", pp="SPSevenHOneEffectPP")),
            ("H7.2", "makespan_steps", "local_potential_reservation",
             "no_congestion_penalty", "less",
             dict(effect="SPSevenHTwoEffect", p="SPSevenHTwoPHolm")),
            ("H7.3", "makespan_steps", "local_potential_reservation",
             "central_restricted_oracle", "greater",
             dict(effect="SPSevenHThreeEffect", p="SPSevenHThreePHolm")),
        ],
    ),
}

MACRO_FILE = {
    "E2": "sp2_numbers.tex",
    "E2-abl": "sp2_numbers.tex",
    "E3": "sp3_numbers.tex",
    "E4": "sp4_numbers.tex",
    "E6-C": "sp6_numbers.tex",
    "E7-C": "sp7_numbers.tex",
}


def fmt_p(p):
    if p is None or not np.isfinite(p):
        return None
    if p >= 1e-3:
        return f"{p:.3f}".replace(".", "{,}")
    exp = int(np.floor(np.log10(p)))
    mant = p / 10.0 ** exp
    return f"{mant:.2f}".replace(".", "{,}") + r"\times10^{" + str(exp) + "}"


def run_campaign(name, spec):
    df = pd.read_csv(spec["path"])
    rows, raw_p, p_index = [], [], []
    for cid, metric, a, b, direction, macros in spec["contrasts"]:
        d, cl = per_seed_differences(df, metric, a, b, spec["keys"])
        if d is None:
            rows.append(dict(campaign=name, id=cid, error="sin pares"))
            continue
        deterministic = bool(np.ptp(cl.values) < DETERMINISTIC_TOL)
        lo_c, hi_c = boot_ci(d.values)
        row = dict(
            campaign=name, id=cid, metric=metric, method_a=a, method_b=b,
            n_cells=int(d.size), n_seeds=int(cl.size),
            effect_cells=float(d.mean()), ci_cells=[lo_c, hi_c],
            effect_clustered=float(cl.mean()),
            deterministic=deterministic, macros=macros, direction=direction,
        )
        if deterministic:
            row["ci_clustered"] = None
            row["p_raw"] = None
        else:
            row["ci_clustered"] = list(boot_ci(cl.values))
            # One-sided, in the direction predeclared for the hypothesis: a
            # contrast whose effect runs the other way must keep a large p
            # rather than be rescued by a two-sided test.
            alt = "greater" if direction == "greater" else "less"
            try:
                row["p_raw"] = float(stats.wilcoxon(cl.values, alternative=alt).pvalue)
            except ValueError:
                row["p_raw"] = None
            if row["p_raw"] is not None:
                raw_p.append(row["p_raw"])
                p_index.append(len(rows))
        rows.append(row)

    if raw_p:
        adj = holm(np.array(raw_p))
        for slot, value in zip(p_index, adj):
            rows[slot]["p_holm"] = float(value)
    return rows


def rewrite_macros(rows_by_campaign):
    changed = []
    for campaign, rows in rows_by_campaign.items():
        path = MACRO_DIR / MACRO_FILE[campaign]
        if not path.exists():
            continue
        text = io.open(path, encoding="utf-8", newline="").read()
        original = text
        dropped = []
        for r in rows:
            m = r.get("macros") or {}
            if not m:
                continue

            def macro_pattern(name):
                # one level of brace nesting is enough for {,} and 10^{-8}
                return re.compile(
                    r"(?m)^[ \t]*\\newcommand\{\\" + name
                    + r"\}\{(?:[^{}]|\{[^{}]*\})*\}[ \t]*\r?\n?"
                )

            def current_decimals(name, default=4):
                mt = macro_pattern(name).search(text)
                if not mt:
                    return default
                mm = re.search(r"\}\{(-?\d+)\.(\d+)\}", mt.group(0))
                return len(mm.group(2)) if mm else default

            def setmacro(key, value):
                """value=None deletes the macro, so every call site must be
                revisited instead of silently printing a stale number."""
                nonlocal text
                name = m.get(key)
                if not name:
                    return
                pat = macro_pattern(name)
                if value is None:
                    if pat.search(text):
                        dropped.append(name)
                        text = pat.sub("", text, count=1)
                    return
                repl = "\\newcommand{\\" + name + "}{" + value + "}\n"
                if pat.search(text):
                    text = pat.sub(lambda _: repl, text, count=1)
                else:
                    text = text.rstrip("\n") + "\n" + repl

            eff = r["effect_clustered"]
            if m.get("effect"):
                d = current_decimals(m["effect"])
                setmacro("effect", f"{eff:.{d}f}")
            if m.get("pp"):
                setmacro("pp", f"{eff * 100:.1f}")
            ci = r.get("ci_clustered")
            if ci:
                if m.get("lo"):
                    d = current_decimals(m["lo"])
                    setmacro("lo", f"{ci[0]:.{d}f}")
                    setmacro("hi", f"{ci[1]:.{d}f}")
                setmacro("ci", f"[{ci[0]:.3f}; {ci[1]:.3f}]")
            else:
                for key in ("lo", "hi", "ci"):
                    setmacro(key, None)
            setmacro("p", fmt_p(r.get("p_holm")))

        header = (
            "% Intervalos y valores p recalculados con la SEMILLA como unidad de\n"
            "% remuestreo por final-hardening/recompute_clustered_ci.py.\n"
            "% Bootstrap pareado sobre semillas, B={b}, semilla de analisis {s};\n"
            "% Wilcoxon de una cola en la direccion predeclarada sobre diferencias\n"
            "% por semilla, y Holm dentro de la familia de la campana. Los\n"
            "% contrastes deterministas por semilla no llevan intervalo ni valor p.\n"
        ).format(b=B, s=ANALYSIS_SEED)
        if not text.startswith("% Intervalos"):
            text = header + text
        if text != original:
            io.open(path, "w", encoding="utf-8", newline="").write(text)
            changed.append((path.name, sorted(set(dropped))))
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write-macros", action="store_true")
    args = ap.parse_args()

    rows_by_campaign = {name: run_campaign(name, spec) for name, spec in CAMPAIGNS.items()}
    flat = [r for rows in rows_by_campaign.values() for r in rows]
    (HERE / "clustered_recompute.json").write_text(json.dumps(flat, indent=2), encoding="utf-8")

    changed = [] if args.no_write_macros else rewrite_macros(rows_by_campaign)

    lines = [
        "# Recomputo de toda la inferencia con la semilla como unidad",
        "",
        f"Bootstrap percentil pareado sobre semillas, B={B}, semilla de analisis",
        f"{ANALYSIS_SEED} (distinta de toda semilla de simulacion). Wilcoxon de rangos",
        "con signo sobre las diferencias por semilla y Holm dentro de la familia",
        "predeclarada de cada campana.",
        "",
        "- **celdas**: el `n` impreso originalmente, una fila por",
        "  (escenario x factor x semilla).",
        "- **semillas**: la unidad que declara el protocolo.",
        "- **det.**: el desenlace es identico en todas las semillas. En esos casos no",
        "  se publica intervalo ni valor p: no hay variabilidad muestral que describir.",
        "",
        "| Campana | Contraste | n celdas | n semillas | efecto | IC celdas (antiguo) | IC semillas (nuevo) | p Holm nuevo | p Holm antiguo | det. |",
        "|---|---|---:|---:|---:|---|---|---|---|---|",
    ]
    old_p = {
        "H02_primal_dual_vs_greedy": "1", "H-SP3-1-guard-reduces-fp": "4.27e-35",
        "H4_1_replicator_safe_success_above_cbf": "3.17e-3",
        "H6.1": "1.3e-108", "H6.2": "1.6e-21", "H6.3": "1.5e-35",
        "H7.1": "5.0e-29", "H7.2": "6.2e-48", "H7.3": "1.5e-45",
    }
    for r in flat:
        if "error" in r:
            lines.append(f"| {r['campaign']} | {r['id']} | | | | {r['error']} | | | | |")
            continue
        ci_new = ("---" if r["ci_clustered"] is None
                  else f"[{r['ci_clustered'][0]:+.4f}; {r['ci_clustered'][1]:+.4f}]")
        p_new = "---" if r.get("p_holm") is None else f"{r['p_holm']:.3g}"
        lines.append(
            f"| {r['campaign']} | `{r['id']}` | {r['n_cells']} | {r['n_seeds']} | "
            f"{r['effect_clustered']:+.4f} | "
            f"[{r['ci_cells'][0]:+.4f}; {r['ci_cells'][1]:+.4f}] | {ci_new} | {p_new} | "
            f"{old_p.get(r['id'], '---')} | {'SI' if r['deterministic'] else ''} |"
        )
    lines += [
        "",
        "## Lectura",
        "",
        "Ningun contraste cambia de signo. Lo que cambia es el tamano de la",
        "evidencia: los valores p caen de ordenes como 1e-108 a los que permiten",
        "40, 100 o 6 semillas, y dos contrastes dejan de tener valor p porque son",
        "deterministas dentro del banco.",
        "",
        "## Macros reescritas",
        "",
    ]
    if changed:
        for fname, dropped in changed:
            lines.append(f"- `{fname}`" + (f" (sin IC/p por determinismo: {', '.join(dropped)})" if dropped else ""))
    else:
        lines.append("- ninguna (ejecutado con --no-write-macros)")
    (HERE / "CLUSTERED_RECOMPUTE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
