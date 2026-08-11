"""Analysis for SP1.N3. Reads frozen RAW, never runs an algorithm or a solver.

Feasibility comes before quality, and the two are estimated on different
denominators on purpose:

* feasibility is conditioned on the oracle having found a solution at all,
  because a world the oracle proved INFEASIBLE cannot count against a method;
* the gap exists only where the oracle *certified* the optimum and the method
  itself was feasible, so nothing is measured against an uncertified incumbent;
* methods are compared to each other only on the common support where all three
  are feasible, otherwise each would be scored on the worlds it happens to
  find easy.

No composite score is built. The point of N3 is a frontier, not a winner.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from sp1_n3_common import N3_OUTPUT_ROOT, REPOSITORY_ROOT, write_json

from viu_mrob_tfm.sp1_n3.graph import CONNECTED_REGIMES, NEGATIVE_CONTROL
from viu_mrob_tfm.sp1_n3.runner import METHOD_LABELS, METHODS


DEFAULT_INPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n3_v2"

COLORS = {
    "capacity_cbba_rb": "#C8102E",
    "weighted_grape": "#1F4E79",
    "weighted_pair_grape": "#2E8B57",
}
MARKERS = {"capacity_cbba_rb": "o", "weighted_grape": "s", "weighted_pair_grape": "^"}
# Truncated English ("comp", "thre") told the reader nothing.
REGIME_LABELS = {
    "complete": "Completo",
    "dense": "Denso",
    "medium": "Medio",
    "threshold": "Umbral",
    "partitioned": "Partido",
}


# ------------------------------------------------------------------ helpers
def wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float, float]:
    if total == 0:
        return float("nan"), float("nan"), float("nan")
    z = stats.norm.ppf(0.5 + confidence / 2.0)
    phat = successes / total
    denominator = 1.0 + z * z / total
    centre = (phat + z * z / (2 * total)) / denominator
    half = z * np.sqrt(phat * (1 - phat) / total + z * z / (4 * total * total)) / denominator
    return phat, max(0.0, centre - half), min(1.0, centre + half)


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni, returned in the same keying as the input."""

    ordered = sorted(pvalues.items(), key=lambda kv: kv[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (key, raw) in enumerate(ordered):
        value = (len(ordered) - rank) * raw
        running = max(running, min(1.0, value))
        adjusted[key] = running
    return adjusted


def mcnemar_exact(a_wins: int, b_wins: int) -> float:
    """Two-sided exact McNemar on the discordant pairs."""

    n = a_wins + b_wins
    if n == 0:
        return 1.0
    return float(min(1.0, 2.0 * stats.binom.cdf(min(a_wins, b_wins), n, 0.5)))


def cochran_q(matrix: np.ndarray) -> tuple[float, float]:
    """Cochran's Q for k paired binary treatments over the same blocks."""

    blocks, treatments = matrix.shape
    if blocks == 0:
        return float("nan"), float("nan")
    column = matrix.sum(axis=0)
    row = matrix.sum(axis=1)
    total = matrix.sum()
    numerator = (treatments - 1) * (treatments * np.sum(column**2) - total**2)
    denominator = treatments * total - np.sum(row**2)
    if denominator == 0:
        return float("nan"), 1.0
    q = numerator / denominator
    return float(q), float(stats.chi2.sf(q, treatments - 1))


def bootstrap_median(values: np.ndarray, resamples: int, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(resamples, values.size), replace=True)
    medians = np.median(draws, axis=1)
    return (
        float(np.median(values)),
        float(np.quantile(medians, 0.025)),
        float(np.quantile(medians, 0.975)),
    )


# ----------------------------------------------------------------------- E2
def analyse_e2(runs: pd.DataFrame, resamples: int) -> tuple[dict[str, Any], pd.DataFrame]:
    metrics: dict[str, Any] = {}
    # Feasibility is conditioned on the oracle having found any solution.
    solvable = runs.loc[runs["oracle_feasible"]]
    metrics["e2_rows"] = int(len(runs))
    metrics["e2_worlds"] = int(runs["world_key"].nunique())
    metrics["e2_oracle_feasible_worlds"] = int(solvable["world_key"].nunique())
    metrics["e2_oracle_infeasible_worlds"] = int(
        runs.loc[runs["oracle_status"] == "INFEASIBLE", "world_key"].nunique()
    )
    metrics["e2_oracle_certified_worlds"] = int(
        runs.loc[runs["oracle_certified"], "world_key"].nunique()
    )

    rows = []
    for method in METHODS:
        block = solvable.loc[solvable["method"] == method]
        feasible = int((block["raw_certificate"] == "FEASIBLE").sum())
        rate, low, high = wilson(feasible, len(block))
        gaps = block.loc[
            (block["raw_certificate"] == "FEASIBLE") & np.isfinite(block["optimality_gap"]),
            "optimality_gap",
        ].to_numpy()
        median, glow, ghigh = bootstrap_median(gaps, resamples, seed=17)
        rows.append(
            {
                "method": method,
                "n": len(block),
                "feasible": feasible,
                "rate": rate,
                "rate_low": low,
                "rate_high": high,
                "gap_n": int(gaps.size),
                "gap_median": median,
                "gap_low": glow,
                "gap_high": ghigh,
                "gap_p95": float(np.quantile(gaps, 0.95)) if gaps.size else float("nan"),
            }
        )
        metrics[f"e2_feasible_rate_{method}"] = rate
        metrics[f"e2_gap_median_{method}"] = median
    summary = pd.DataFrame(rows)

    # A method must never claim a world the oracle proved impossible.
    impossible = runs.loc[runs["oracle_status"] == "INFEASIBLE"]
    false_claims = int((impossible["raw_certificate"] == "FEASIBLE").sum())
    metrics["e2_false_feasible_on_infeasible"] = false_claims
    metrics["e2_infeasible_rows"] = int(len(impossible))

    # Paired feasibility across the three methods on the same worlds.
    pivot = (
        solvable.assign(ok=(solvable["raw_certificate"] == "FEASIBLE").astype(int))
        .pivot_table(index="world_key", columns="method", values="ok")
        .dropna()
    )
    if not pivot.empty:
        q, p = cochran_q(pivot[list(METHODS)].to_numpy())
        metrics["e2_cochran_q"] = q
        metrics["e2_cochran_p"] = p
        raw_p, effects = {}, {}
        for left, right in itertools.combinations(METHODS, 2):
            a = int(((pivot[left] == 1) & (pivot[right] == 0)).sum())
            b = int(((pivot[left] == 0) & (pivot[right] == 1)).sum())
            raw_p[f"{left}|{right}"] = mcnemar_exact(a, b)
            effects[f"{left}|{right}"] = {
                "only_left": a,
                "only_right": b,
                "paired_difference": (a - b) / len(pivot),
                "n_pairs": int(len(pivot)),
            }
        metrics["e2_mcnemar_holm"] = holm(raw_p)
        metrics["e2_mcnemar_effects"] = effects

    # Quality is compared only where every method is feasible.
    support = pivot.index[(pivot[list(METHODS)] == 1).all(axis=1)] if not pivot.empty else []
    certified = set(runs.loc[runs["oracle_certified"], "world_key"])
    common = [key for key in support if key in certified]
    metrics["e2_common_support_worlds"] = len(common)
    if len(common) >= 3:
        block = runs.loc[runs["world_key"].isin(common)]
        wide = block.pivot_table(
            index="world_key", columns="method", values="optimality_gap"
        ).dropna()
        for method in METHODS:
            median, low, high = bootstrap_median(
                wide[method].to_numpy(), resamples, seed=23
            )
            metrics[f"e2_common_gap_median_{method}"] = median
            metrics[f"e2_common_gap_low_{method}"] = low
            metrics[f"e2_common_gap_high_{method}"] = high
        if len(wide) >= 3:
            statistic, p = stats.friedmanchisquare(
                *[wide[method].to_numpy() for method in METHODS]
            )
            metrics["e2_friedman_stat"] = float(statistic)
            metrics["e2_friedman_p"] = float(p)
    return metrics, summary


# ----------------------------------------------------------------------- E3
def analyse_e3(runs: pd.DataFrame, resamples: int) -> tuple[dict[str, Any], pd.DataFrame]:
    metrics: dict[str, Any] = {}
    solvable = runs.loc[runs["oracle_feasible"]]
    rows = []
    for regime in list(CONNECTED_REGIMES) + [NEGATIVE_CONTROL]:
        for method in METHODS:
            block = solvable.loc[
                (solvable["graph_regime"] == regime) & (solvable["method"] == method)
            ]
            if block.empty:
                continue
            feasible = int((block["raw_certificate"] == "FEASIBLE").sum())
            rate, low, high = wilson(feasible, len(block))
            gaps = block.loc[
                (block["raw_certificate"] == "FEASIBLE")
                & np.isfinite(block["optimality_gap"]),
                "optimality_gap",
            ].to_numpy()
            rows.append(
                {
                    "graph_regime": regime,
                    "method": method,
                    "n": len(block),
                    "rate": rate,
                    "rate_low": low,
                    "rate_high": high,
                    "gap_median": float(np.median(gaps)) if gaps.size else float("nan"),
                    "bytes_per_agent": float(block["bytes_per_agent"].median()),
                    "messages_per_agent": float(block["messages_per_agent"].median()),
                    "rounds": float(block["rounds"].median()),
                    "lambda_2": float(block["graph_lambda_2"].median()),
                    "mean_degree": float(block["graph_mean_degree"].median()),
                    "diameter": float(block["graph_diameter"].median()),
                }
            )
    summary = pd.DataFrame(rows)
    for _, row in summary.iterrows():
        tag = f"{row['graph_regime']}_{row['method']}"
        metrics[f"e3_rate_{tag}"] = row["rate"]
        metrics[f"e3_bytes_{tag}"] = row["bytes_per_agent"]

    control = summary.loc[summary["graph_regime"] == NEGATIVE_CONTROL, "rate"]
    connected = summary.loc[summary["graph_regime"].isin(CONNECTED_REGIMES), "rate"]
    metrics["e3_control_rate_max"] = float(control.max()) if len(control) else float("nan")
    metrics["e3_connected_rate_min"] = float(connected.min()) if len(connected) else float("nan")
    metrics["e3_partition_components_median"] = float(
        runs.loc[runs["graph_regime"] == NEGATIVE_CONTROL, "graph_components"].median()
    )
    return metrics, summary


# -------------------------------------------------------------------- plots
def _style() -> None:
    plt.rcParams.update(
        {
            "font.size": 8.2,
            "axes.titlesize": 8.6,
            "axes.labelsize": 8.2,
            "legend.fontsize": 7.4,
            "figure.dpi": 160,
            "savefig.bbox": "tight",
        }
    )


def plot_e2(summary: pd.DataFrame, path: Path) -> list[Path]:
    _style()
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))
    x = np.arange(len(summary))
    axes[0].bar(
        x, summary["rate"],
        yerr=[summary["rate"] - summary["rate_low"], summary["rate_high"] - summary["rate"]],
        color=[COLORS[m] for m in summary["method"]], capsize=3.2, width=0.58,
    )
    axes[0].set(
        xticks=x, ylim=(0, 1.05),
        ylabel="P(RAW factible | oráculo factible)",
        title="Factibilidad condicionada al oráculo",
    )
    axes[0].set_xticklabels([METHOD_LABELS[m] for m in summary["method"]], rotation=12)
    axes[1].bar(
        x, summary["gap_median"],
        yerr=[
            summary["gap_median"] - summary["gap_low"],
            summary["gap_high"] - summary["gap_median"],
        ],
        color=[COLORS[m] for m in summary["method"]], capsize=3.2, width=0.58,
    )
    axes[1].set(
        xticks=x, ylabel="Brecha mediana frente al MILP",
        title="Calidad donde el oráculo certificó el óptimo",
    )
    axes[1].set_xticklabels([METHOD_LABELS[m] for m in summary["method"]], rotation=12)
    for axis, letter in zip(axes, "ab"):
        axis.text(-0.09, 1.06, f"({letter})", transform=axis.transAxes, fontweight="bold")
    return _save(figure, path)


def plot_e3(summary: pd.DataFrame, path: Path) -> list[Path]:
    _style()
    figure, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))
    connected = summary.loc[summary["graph_regime"].isin(CONNECTED_REGIMES)]
    for method in METHODS:
        block = connected.loc[connected["method"] == method].sort_values("bytes_per_agent")
        axes[0].plot(
            block["bytes_per_agent"], block["rate"],
            marker=MARKERS[method], color=COLORS[method],
            label=METHOD_LABELS[method], linewidth=1.2, markersize=5,
        )
        for _, row in block.iterrows():
            axes[0].annotate(
                REGIME_LABELS[row["graph_regime"]],
                (row["bytes_per_agent"], row["rate"]),
                xytext=(3, 3), textcoords="offset points", fontsize=6.2, color="#444",
            )
    axes[0].set(
        xscale="log", xlabel="Bytes por agente (mediana)",
        ylabel="P(RAW factible | oráculo factible)",
        title="Frontera comunicación–factibilidad (solo conexos)",
    )
    axes[0].legend(loc="lower right")

    control = summary.loc[summary["graph_regime"] == NEGATIVE_CONTROL]
    width = 0.34
    x = np.arange(len(METHODS))
    best_connected = [
        connected.loc[connected["method"] == m, "rate"].max() for m in METHODS
    ]
    axes[1].bar(x - width / 2, best_connected, width, color="#7A8B99", label="mejor conexo")
    axes[1].bar(
        x + width / 2,
        [
            control.loc[control["method"] == m, "rate"].squeeze()
            if not control.loc[control["method"] == m].empty else 0.0
            for m in METHODS
        ],
        width, color="#C8102E", label="partición (control)",
    )
    axes[1].set(
        xticks=x, ylim=(0, 1.05), ylabel="P(RAW factible | oráculo factible)",
        title="Control negativo: partición permanente",
    )
    axes[1].set_xticklabels([METHOD_LABELS[m] for m in METHODS], rotation=12)
    axes[1].legend(loc="upper right")
    for axis, letter in zip(axes, "ab"):
        axis.text(-0.09, 1.06, f"({letter})", transform=axis.transAxes, fontweight="bold")
    return _save(figure, path)


def _save(figure, path: Path) -> list[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for suffix in (".pdf", ".png"):
        target = path.with_suffix(suffix)
        figure.savefig(target)
        written.append(target)
    plt.close(figure)
    return written


def _paired_difference_ci(
    wide: pd.DataFrame, left: str, right: str, resamples: int, seed: int
) -> tuple[float, float, float]:
    """Bootstrap the paired difference in feasibility, resampling worlds.

    The world is the independent unit: every method saw the same ones, so the
    interval has to be built by resampling worlds rather than rows.
    """

    difference = wide[left].to_numpy() - wide[right].to_numpy()
    rng = np.random.default_rng(seed)
    draws = rng.choice(difference, size=(resamples, difference.size), replace=True)
    means = draws.mean(axis=1)
    return (
        float(difference.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def _audit_quantities(
    e2: pd.DataFrame, e3: pd.DataFrame, resamples: int
) -> dict[str, Any]:
    """Effects, ratios and the invariance certificate, straight from RAW."""

    out: dict[str, Any] = {}

    # --- paired feasibility differences, with intervals rather than p-values
    solvable = e2.loc[e2["oracle_feasible"]]
    wide = (
        solvable.assign(ok=(solvable["raw_certificate"] == "FEASIBLE").astype(float))
        .pivot_table(index="world_key", columns="method", values="ok")
        .dropna()
    )
    for index, (left, right) in enumerate(itertools.combinations(METHODS, 2)):
        point, low, high = _paired_difference_ci(
            wide, right, left, resamples, seed=101 + index
        )
        tag = f"{right}_minus_{left}"
        out[f"e2_feas_diff_{tag}"] = point
        out[f"e2_feas_diff_low_{tag}"] = low
        out[f"e2_feas_diff_high_{tag}"] = high

    # --- communication: bytes and messages disagree about the magnitude
    base = "capacity_cbba_rb"
    for method in METHODS:
        if method == base:
            continue
        for what in ("bytes_per_agent", "messages_per_agent"):
            ratio = (
                e2.loc[e2["method"] == method, what].median()
                / e2.loc[e2["method"] == base, what].median()
            )
            out[f"e2_ratio_{what}_{method}"] = float(ratio)

    # --- what "identical across connected graphs" actually means
    connected = e3.loc[e3["graph_regime"].isin(CONNECTED_REGIMES)]
    for method in METHODS:
        block = connected.loc[connected["method"] == method]
        certificates = block.pivot_table(
            index="world_key", columns="graph_regime",
            values="raw_certificate", aggfunc="first",
        ).dropna()
        agree = int((certificates.nunique(axis=1) == 1).sum())
        costs = block.pivot_table(
            index="world_key", columns="graph_regime", values="distance_cost"
        ).dropna()
        spread = (costs.max(axis=1) - costs.min(axis=1)).abs()
        out[f"e3_cert_agree_{method}"] = agree
        out[f"e3_cert_worlds_{method}"] = int(len(certificates))
        out[f"e3_cost_identical_{method}"] = int((spread <= 1e-9).sum())
        out[f"e3_cost_maxspread_{method}"] = float(spread.max())

    # --- Pair-GRAPE quality against topology, the claim that needs numbers
    for regime in CONNECTED_REGIMES:
        for method in ("weighted_grape", "weighted_pair_grape"):
            block = e3.loc[
                (e3["graph_regime"] == regime)
                & (e3["method"] == method)
                & (e3["raw_certificate"] == "FEASIBLE")
                & np.isfinite(e3["optimality_gap"])
            ]
            if not block.empty:
                out[f"e3_gap_{regime}_{method}"] = float(block["optimality_gap"].median())
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    raw = args.input_dir / "raw"
    e2 = pd.read_csv(raw / "e2_runs.csv")
    e3 = pd.read_csv(raw / "e3_runs.csv")
    config = json.loads((args.input_dir / "manifest.json").read_text(encoding="utf-8"))
    resamples = 4000

    processed = args.input_dir / "processed"
    figures = args.input_dir / "figures"
    processed.mkdir(parents=True, exist_ok=True)

    metrics_e2, summary_e2 = analyse_e2(e2, resamples)
    metrics_e3, summary_e3 = analyse_e3(e3, resamples)
    summary_e2.to_csv(processed / "e2_summary.csv", index=False)
    summary_e3.to_csv(processed / "e3_summary.csv", index=False)
    plot_e2(summary_e2, figures / "n3_quality")
    plot_e3(summary_e3, figures / "n3_locality")

    metrics = {**metrics_e2, **metrics_e3, "campaign_id": config["campaign_id"]}
    # Communication, reported as estimation rather than as a contest.
    for method in METHODS:
        block = e2.loc[e2["method"] == method]
        metrics[f"e2_bytes_per_agent_{method}"] = float(block["bytes_per_agent"].median())
        metrics[f"e2_rounds_{method}"] = float(block["rounds"].median())
        metrics[f"e2_messages_per_agent_{method}"] = float(
            block["messages_per_agent"].median()
        )
    for frame, tag in ((e2, "e2"), (e3, "e3")):
        metrics[f"{tag}_cycle_observed"] = int(frame["cycle_observed"].sum())
        metrics[f"{tag}_max_rounds"] = int((frame["algorithm_status"] == "MAX_ROUNDS").sum())
        metrics[f"{tag}_inconsistent"] = int((~frame["consistent"]).sum())
    metrics.update(_audit_quantities(e2, e3, resamples))
    write_json(args.input_dir / "key_metrics.json", metrics)
    print(summary_e2.to_string(index=False))
    print()
    print(summary_e3.to_string(index=False))


if __name__ == "__main__":
    main()
