"""Analysis and figures for the frozen SP1.N2 campaign.

Reads only ``n2_v1/raw``; never solves anything. Every number the document
quotes is produced here and sealed in ``manifest.json``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as smapi
import yaml
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Binomial

import sp1_n2_oracle as oracle
from sp1_levels_common import (
    COLORS,
    LEVELS_OUTPUT_ROOT,
    REPOSITORY_ROOT,
    configure_publication_style,
    label_panels,
    save_figure,
    write_json,
    write_level_manifest,
)

DEFAULT_CONFIG = (
    REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n2_confirmatory_v1.yaml"
)
DEFAULT_OUTPUT = LEVELS_OUTPUT_ROOT / "n2_v1"
LAYERS = (
    "oracle_validation",
    "homogeneous_limit",
    "atomicity",
    "phase_diagram",
    "certification",
)
# Matches the N1 figures so both blocks print at the same scale.
WIDTH_IN = 5.75
HEIGHT_IN = 2.02


def _decimal_comma(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def bootstrap_median(
    values: Sequence[float], *, resamples: int, seed: int, confidence: float
) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(seed)
    estimates = np.array(
        [
            np.median(array[rng.integers(0, array.size, array.size)])
            for _ in range(resamples)
        ]
    )
    alpha = 1.0 - confidence
    return (
        float(np.median(array)),
        float(np.quantile(estimates, alpha / 2.0)),
        float(np.quantile(estimates, 1.0 - alpha / 2.0)),
    )


def wilson(successes: int, total: int, *, confidence: float) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(stats.norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = (
        z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total**2)) / denominator
    )
    return max(0.0, center - radius), min(1.0, center + radius)


# ----------------------------------------------------------------- E1
def analyse_oracle(
    validation: pd.DataFrame, limit: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    comparable = validation.loc[
        (validation["milp_status"] == oracle.OPTIMAL)
        & (validation["brute_status"] == oracle.OPTIMAL)
    ]
    summary = (
        validation.groupby(["N", "K"], as_index=False)
        .agg(
            worlds=("world_id", "size"),
            status_agreement=("status_agrees", "mean"),
            max_absolute_error=("absolute_error", "max"),
            milp_runtime_median=("milp_runtime_s", "median"),
        )
    )
    metrics = {
        "oracle_rows": int(len(validation)),
        "oracle_status_agreement": float(validation["status_agrees"].mean()),
        "oracle_status_disagreements": int((~validation["status_agrees"]).sum()),
        "oracle_comparable_rows": int(len(comparable)),
        "oracle_max_absolute_error": float(comparable["absolute_error"].max()),
        "oracle_infeasible_rows": int(
            (validation["brute_status"] == oracle.INFEASIBLE).sum()
        ),
        "oracle_max_states": int(validation["enumeration_states"].max()),
        "homogeneous_rows": int(len(limit)),
        "homogeneous_feasibility_agreement": float(
            limit["feasibility_agrees"].mean()
        ),
        "homogeneous_max_distance_error": float(
            limit["distance_absolute_error"].max()
        ),
        "homogeneous_cardinality_matches": int(limit["cardinality_matches"].sum()),
    }
    return summary, metrics


# ----------------------------------------------------------------- E2
def analyse_atomicity(
    runs: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    confidence = float(config["analysis"]["confidence_level"])
    resamples = int(config["analysis"]["bootstrap_resamples"])
    usable = runs.loc[
        (runs["lp_status"] == oracle.OPTIMAL)
        & (runs["milp_status"] == oracle.OPTIMAL)
    ]
    rows: list[dict[str, Any]] = []
    for cv, block in usable.groupby("capacity_cv", sort=True):
        median, low, high = bootstrap_median(
            block["gap_relative"].to_numpy(float),
            resamples=resamples,
            seed=int(abs(hash(("n2-gap", float(cv)))) % 2**31),
            confidence=confidence,
        )
        fractional = int(block["fractional_world"].sum())
        f_low, f_high = wilson(fractional, len(block), confidence=confidence)
        rows.append(
            {
                "capacity_cv": float(cv),
                "worlds": len(block),
                "gap_median": median,
                "gap_ci_low": low,
                "gap_ci_high": high,
                "gap_p95": float(np.quantile(block["gap_relative"], 0.95)),
                "gap_max": float(block["gap_relative"].max()),
                "fractional_rate": fractional / len(block),
                "fractional_ci_low": f_low,
                "fractional_ci_high": f_high,
                "fractionality_rate_median": float(
                    block["fractionality_rate"].median()
                ),
            }
        )
    summary = pd.DataFrame(rows)
    overall = bootstrap_median(
        usable["gap_relative"].to_numpy(float),
        resamples=resamples,
        seed=7,
        confidence=confidence,
    )
    fractional_total = int(usable["fractional_world"].sum())
    low, high = wilson(fractional_total, len(usable), confidence=confidence)
    # Does the gap actually track heterogeneity? Answer, do not assume.
    finite = usable.loc[np.isfinite(usable["gap_relative"])]
    correlation = stats.spearmanr(
        finite["capacity_cv"], finite["gap_relative"]
    )
    # The sharpest form of the atomicity argument: the relaxation is feasible
    # while no atomic coalition exists at all.
    lp_only = runs.loc[
        (runs["lp_status"] == oracle.OPTIMAL)
        & (runs["milp_status"] == oracle.INFEASIBLE)
    ]
    metrics = {
        "atomicity_rows": int(len(runs)),
        "atomicity_comparable_rows": int(len(usable)),
        "atomicity_lp_feasible_milp_infeasible": int(len(lp_only)),
        "atomicity_lp_only_share": len(lp_only) / max(1, len(runs)),
        "atomicity_gap_median": overall[0],
        "atomicity_gap_ci_low": overall[1],
        "atomicity_gap_ci_high": overall[2],
        "atomicity_gap_p95": float(np.quantile(usable["gap_relative"], 0.95)),
        "atomicity_gap_max": float(usable["gap_relative"].max()),
        "atomicity_gap_min": float(usable["gap_relative"].min()),
        "atomicity_fractional_rate": fractional_total / len(usable),
        "atomicity_fractional_ci_low": low,
        "atomicity_fractional_ci_high": high,
        "atomicity_negative_gaps": int((usable["gap_relative"] < -1e-9).sum()),
        "atomicity_cv_spearman": float(correlation.statistic),
        "atomicity_cv_spearman_p": float(correlation.pvalue),
    }
    for row in summary.itertuples(index=False):
        tag = f"{row.capacity_cv:.2f}".replace(".", "")
        metrics[f"atomicity_gap_median_cv{tag}"] = float(row.gap_median)
        metrics[f"atomicity_fractional_rate_cv{tag}"] = float(row.fractional_rate)
    return summary, metrics


# ----------------------------------------------------------------- E3
def analyse_phase(
    runs: pd.DataFrame, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    confidence = float(config["analysis"]["confidence_level"])
    # An incumbent proves feasibility even when optimality is not certified,
    # so a time limit must never be read as infeasibility. Feasibility is
    # therefore estimated over the runs the solver actually resolved.
    runs = runs.copy()
    runs["feasible_known"] = runs["milp_status"].isin(
        [oracle.OPTIMAL, oracle.FEASIBLE_TIME_LIMIT]
    )
    runs["resolved"] = runs["feasible_known"] | runs["proven_infeasible"]
    rows: list[dict[str, Any]] = []
    for (pressure, cv), block in runs.groupby(
        ["pressure", "capacity_cv"], sort=True
    ):
        resolved = block.loc[block["resolved"]]
        feasible = int(block["feasible_known"].sum())
        low, high = wilson(feasible, max(1, len(resolved)), confidence=confidence)
        solved = block.loc[block["certified_feasible"]]
        rows.append(
            {
                "pressure": float(pressure),
                "capacity_cv": float(cv),
                "worlds": len(block),
                "resolved": len(resolved),
                "feasible_count": feasible,
                "feasible_rate": feasible / max(1, len(resolved)),
                "feasible_ci_low": low,
                "feasible_ci_high": high,
                "infeasible_count": int(block["proven_infeasible"].sum()),
                "censored_count": int(block["censored"].sum()),
                "certified_count": int(block["certified_feasible"].sum()),
                "excess_median": (
                    float(solved["excess_capacity"].median())
                    if not solved.empty
                    else math.nan
                ),
                "coalition_median": (
                    float(solved["coalition_size"].median())
                    if not solved.empty
                    else math.nan
                ),
                "objective_median": (
                    float(solved["milp_objective"].median())
                    if not solved.empty
                    else math.nan
                ),
            }
        )
    summary = pd.DataFrame(rows)

    # Infeasibility below rho = 1 is the empirical face of T2.
    slack = runs.loc[runs["pressure"] < 1.0]
    slack_infeasible = int(slack["proven_infeasible"].sum())

    resolved_runs = runs.loc[runs["resolved"]]
    frame = pd.DataFrame(
        {
            "feasible": resolved_runs["feasible_known"].astype(float),
            "capacity_cv": resolved_runs["capacity_cv"].astype(float),
            "pressure": resolved_runs["pressure"].astype(float),
            "world_id": resolved_runs["world_id"].astype(str),
        }
    )
    trend = smapi.GEE.from_formula(
        "feasible ~ capacity_cv + pressure",
        groups="world_id",
        data=frame,
        family=Binomial(),
        cov_struct=Exchangeable(),
    ).fit()
    metrics = {
        "phase_rows": int(len(runs)),
        "phase_worlds": int(runs["world_id"].nunique()),
        "phase_censored": int(runs["censored"].sum()),
        "phase_resolved": int(runs["resolved"].sum()),
        "phase_slack_rows": int(len(slack)),
        "phase_slack_infeasible": slack_infeasible,
        "phase_slack_infeasible_rate": slack_infeasible / max(1, len(slack)),
        "phase_trend_cv": float(trend.params["capacity_cv"]),
        "phase_trend_cv_low": float(
            trend.params["capacity_cv"] - 1.959963985 * trend.bse["capacity_cv"]
        ),
        "phase_trend_cv_high": float(
            trend.params["capacity_cv"] + 1.959963985 * trend.bse["capacity_cv"]
        ),
        "phase_trend_pressure": float(trend.params["pressure"]),
        "phase_trend_pressure_low": float(
            trend.params["pressure"] - 1.959963985 * trend.bse["pressure"]
        ),
        "phase_trend_pressure_high": float(
            trend.params["pressure"] + 1.959963985 * trend.bse["pressure"]
        ),
    }
    homogeneous = summary.loc[summary["capacity_cv"] == 0.0]
    extreme = summary.loc[summary["capacity_cv"] == summary["capacity_cv"].max()]
    for label, block in (("homogeneous", homogeneous), ("extreme", extreme)):
        metrics[f"phase_{label}_feasible_rate"] = float(
            block["feasible_count"].sum() / max(1, block["resolved"].sum())
        )
    return summary, metrics


# ----------------------------------------------------------------- E4
def analyse_certification(runs: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (size, limit), block in runs.groupby(["N", "time_limit_s"], sort=True):
        certified = int(block["optimal_certified"].sum())
        low, high = wilson(certified, len(block), confidence=0.95)
        censored = block.loc[~block["optimal_certified"]]
        rows.append(
            {
                "N": int(size),
                "K": int(block["K"].iloc[0]),
                "binary_variables": int(block["binary_variables"].iloc[0]),
                "time_limit_s": float(limit),
                "runs": len(block),
                "certified_count": certified,
                "certified_rate": certified / len(block),
                "certified_ci_low": low,
                "certified_ci_high": high,
                "incumbent_rate": float(block["incumbent_exists"].mean()),
                "runtime_p50": float(block["runtime_s"].median()),
                "runtime_p95": float(block["runtime_s"].quantile(0.95)),
                "censored_gap_median": (
                    float(censored["mip_gap"].median()) if not censored.empty else math.nan
                ),
                "censored_gap_max": (
                    float(censored["mip_gap"].max()) if not censored.empty else math.nan
                ),
            }
        )
    summary = pd.DataFrame(rows)
    metrics = {
        "certification_rows": int(len(runs)),
        "certification_min_n": int(runs["N"].min()),
        "certification_max_n": int(runs["N"].max()),
        "certification_incumbent_rate": float(runs["incumbent_exists"].mean()),
        "certification_overall_rate": float(runs["optimal_certified"].mean()),
    }
    for row in summary.itertuples(index=False):
        if math.isclose(row.time_limit_s, 5.0):
            metrics[f"certification_rate_n{int(row.N)}"] = float(row.certified_rate)
            metrics[f"certification_runtime_p95_n{int(row.N)}"] = float(row.runtime_p95)
    return summary, metrics


# ----------------------------------------------------------------- figures
def plot_oracle(
    validation: pd.DataFrame, limit: pd.DataFrame, output_dir: Path
) -> list[Path]:
    figure, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, HEIGHT_IN))
    comparable = validation.loc[
        (validation["milp_status"] == oracle.OPTIMAL)
        & (validation["brute_status"] == oracle.OPTIMAL)
    ]
    axes[0].plot(
        [comparable["brute_objective"].min(), comparable["brute_objective"].max()],
        [comparable["brute_objective"].min(), comparable["brute_objective"].max()],
        color=COLORS["gray"],
        linestyle="--",
        linewidth=0.9,
        label="identidad",
    )
    axes[0].scatter(
        comparable["brute_objective"],
        comparable["milp_objective"],
        s=9,
        color=COLORS["blue"],
        alpha=0.55,
        linewidths=0,
        label=f"{len(comparable)} mundos",
    )
    axes[0].set(
        xlabel="Óptimo por enumeración [m]",
        ylabel="Óptimo HiGHS [m]",
        title="E1.A · oráculo frente a fuerza bruta",
    )
    axes[0].legend(loc="upper left", fontsize=6.2)

    order = sorted(limit["scenario_label"].unique())
    errors = [
        limit.loc[limit["scenario_label"] == name, "distance_absolute_error"]
        .abs()
        .max()
        for name in order
    ]
    axes[1].barh(
        np.arange(len(order)),
        np.maximum(errors, 1e-16),
        color=COLORS["green"],
        height=0.6,
    )
    axes[1].set_xscale("log")
    axes[1].set_yticks(np.arange(len(order)), order)
    axes[1].invert_yaxis()
    axes[1].set(
        xlabel="máx. |J$_{N2}$ − J$_{LSAP}$| [m]",
        title="E1.B · límite homogéneo frente a N1",
        xlim=(1e-16, 1e-6),
    )
    axes[1].axvline(1e-9, color=COLORS["red"], linestyle=":", linewidth=1.0)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.1)
    return save_figure(figure, output_dir / "n2_oracle_validation", tight=False)


def plot_atomicity(
    runs: pd.DataFrame, summary: pd.DataFrame, output_dir: Path
) -> list[Path]:
    figure, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, HEIGHT_IN))
    usable = runs.loc[
        (runs["lp_status"] == oracle.OPTIMAL)
        & (runs["milp_status"] == oracle.OPTIMAL)
    ]
    levels = sorted(usable["capacity_cv"].unique())
    data = [
        100.0 * usable.loc[usable["capacity_cv"] == cv, "gap_relative"].to_numpy()
        for cv in levels
    ]
    parts = axes[0].violinplot(data, positions=np.arange(len(levels)), widths=0.75)
    for body in parts["bodies"]:
        body.set_facecolor(COLORS["blue"])
        body.set_alpha(0.35)
    for key in ("cbars", "cmins", "cmaxes"):
        parts[key].set_color(COLORS["dark"])
        parts[key].set_linewidth(0.8)
    medians = 100.0 * summary.set_index("capacity_cv").loc[levels, "gap_median"]
    axes[0].plot(
        np.arange(len(levels)),
        medians.to_numpy(),
        color=COLORS["orange"],
        marker="o",
        markersize=3.6,
        linewidth=1.4,
        label="mediana",
    )
    axes[0].set_xticks(
        np.arange(len(levels)), [_decimal_comma(cv, 2) for cv in levels]
    )
    axes[0].set(
        xlabel=r"Heterogeneidad nominal, CV$(c_i)$",
        ylabel="Brecha de integralidad [%]",
        title="E2 · precio de la atomicidad",
    )
    axes[0].legend(loc="upper right", fontsize=6.2)

    rates = summary.set_index("capacity_cv").loc[levels]
    axes[1].errorbar(
        np.arange(len(levels)),
        100.0 * rates["fractional_rate"],
        yerr=np.maximum(
            0.0,
            np.vstack(
                (
                    100.0 * (rates["fractional_rate"] - rates["fractional_ci_low"]),
                    100.0 * (rates["fractional_ci_high"] - rates["fractional_rate"]),
                )
            ),
        ),
        color=COLORS["purple"],
        marker="s",
        markersize=3.6,
        capsize=2.4,
        linewidth=1.3,
        label="mundos con LP fraccionario",
    )
    axes[1].plot(
        np.arange(len(levels)),
        100.0 * rates["fractionality_rate_median"],
        color=COLORS["gray"],
        marker="|",
        linestyle="none",
        markersize=8,
        label="variables fraccionales (mediana)",
    )
    axes[1].set_xticks(
        np.arange(len(levels)), [_decimal_comma(cv, 2) for cv in levels]
    )
    axes[1].set(
        xlabel=r"Heterogeneidad nominal, CV$(c_i)$",
        ylabel="[%]",
        title="E2 · dónde aparece la fracción",
        ylim=(-4, 108),
    )
    axes[1].legend(loc="center right", fontsize=5.9)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.1)
    return save_figure(figure, output_dir / "n2_atomicity", tight=False)


def plot_phase(summary: pd.DataFrame, output_dir: Path) -> list[Path]:
    figure, axes = plt.subplots(
        1, 2, figsize=(WIDTH_IN, HEIGHT_IN), gridspec_kw={"width_ratios": [1.15, 0.85]}
    )
    pressures = sorted(summary["pressure"].unique())
    cvs = sorted(summary["capacity_cv"].unique())
    grid = (
        summary.pivot(index="pressure", columns="capacity_cv", values="feasible_rate")
        .loc[pressures, cvs]
        .to_numpy(float)
    )
    cmap = LinearSegmentedColormap.from_list(
        "n2_phase", ["#B3202A", "#F2E7E3", "#DCEAF5", COLORS["blue"]]
    )
    image = axes[0].pcolormesh(
        np.arange(len(cvs) + 1) - 0.5,
        np.arange(len(pressures) + 1) - 0.5,
        grid,
        cmap=cmap,
        vmin=0.0,
        vmax=1.0,
    )
    for row, _ in enumerate(pressures):
        for column, _ in enumerate(cvs):
            value = grid[row, column]
            axes[0].text(
                column,
                row,
                f"{100 * value:.0f}",
                ha="center",
                va="center",
                fontsize=5.8,
                fontweight="bold",
                color="white" if value < 0.28 or value > 0.85 else COLORS["dark"],
            )
    axes[0].set_xticks(np.arange(len(cvs)), [_decimal_comma(v, 2) for v in cvs])
    axes[0].set_yticks(
        np.arange(len(pressures)), [_decimal_comma(v, 2) for v in pressures]
    )
    axes[0].set(
        xlabel=r"Heterogeneidad, CV$(c_i)$",
        ylabel=r"Presión, $\rho$",
        title="E3 · asignación atómica factible [%]",
    )
    axes[0].grid(False)
    bar = figure.colorbar(image, ax=axes[0], fraction=0.045, pad=0.03)
    bar.set_label("P(factible)", fontsize=7.0)

    for cv in cvs:
        block = summary.loc[summary["capacity_cv"] == cv].sort_values("pressure")
        axes[1].plot(
            block["pressure"],
            block["excess_median"],
            marker="o",
            markersize=3.0,
            linewidth=1.2,
            label=f"CV={_decimal_comma(cv, 2)}",
        )
    axes[1].set(
        xlabel=r"Presión, $\rho$",
        ylabel="Exceso de capacidad [kg]",
        title="E3 · capacidad desperdiciada",
    )
    axes[1].legend(loc="upper right", fontsize=5.6, ncol=2, columnspacing=0.8)
    label_panels(axes)
    figure.tight_layout(pad=0.45, w_pad=1.05)
    return save_figure(figure, output_dir / "n2_phase_diagram", tight=False)


def plot_certification(summary: pd.DataFrame, output_dir: Path) -> list[Path]:
    figure, axes = plt.subplots(1, 3, figsize=(WIDTH_IN, HEIGHT_IN))
    limits = sorted(summary["time_limit_s"].unique())
    palette = [COLORS["blue"], COLORS["orange"], COLORS["green"]]
    for index, limit in enumerate(limits):
        block = summary.loc[summary["time_limit_s"] == limit].sort_values("N")
        colour = palette[index % len(palette)]
        axes[0].plot(
            block["N"], block["runtime_p50"], marker="o", markersize=3.0,
            color=colour, linewidth=1.3, label=f"{_decimal_comma(limit, 0)} s",
        )
        axes[0].plot(
            block["N"], block["runtime_p95"], marker="^", markersize=3.0,
            color=colour, linewidth=0.9, linestyle="--",
        )
        axes[1].errorbar(
            block["N"],
            100.0 * block["certified_rate"],
            yerr=np.maximum(
                0.0,
                np.vstack(
                    (
                        100.0 * (block["certified_rate"] - block["certified_ci_low"]),
                        100.0 * (block["certified_ci_high"] - block["certified_rate"]),
                    )
                ),
            ),
            marker="o", markersize=3.0, color=colour, linewidth=1.3, capsize=2.0,
            label=f"{_decimal_comma(limit, 0)} s",
        )
        axes[2].plot(
            block["N"], 100.0 * block["censored_gap_median"], marker="o",
            markersize=3.0, color=colour, linewidth=1.3,
        )
    axes[0].set(
        xlabel="Robots, $N$", ylabel="Tiempo [s]", yscale="log",
        title="Tiempo P50 y P95",
    )
    axes[0].legend(loc="upper left", fontsize=5.8, title="límite", title_fontsize=5.8)
    axes[1].set(
        xlabel="Robots, $N$", ylabel="Óptimo certificado [%]",
        title="Certificación", ylim=(-5, 105),
    )
    axes[2].set(
        xlabel="Robots, $N$", ylabel="Brecha MIP [%]",
        title="Brecha si no certifica",
    )
    label_panels(axes)
    figure.tight_layout(pad=0.4, w_pad=0.85)
    return save_figure(figure, output_dir / "n2_certification", tight=False)


# ----------------------------------------------------------------- driver
def build(config_path: Path, output_dir: Path) -> dict[str, Any]:
    configure_publication_style()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw_dir = output_dir / "raw"
    frames = {}
    for layer in LAYERS:
        path = raw_dir / f"{layer}_runs.csv"
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {path}; run sp1_n2_confirmatory.py first."
            )
        frames[layer] = pd.read_csv(path)

    processed_dir = output_dir / "processed"
    figures_dir = output_dir / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    oracle_summary, oracle_metrics = analyse_oracle(
        frames["oracle_validation"], frames["homogeneous_limit"]
    )
    atomicity_summary, atomicity_metrics = analyse_atomicity(
        frames["atomicity"], config
    )
    phase_summary, phase_metrics = analyse_phase(frames["phase_diagram"], config)
    certification_summary, certification_metrics = analyse_certification(
        frames["certification"]
    )

    oracle_summary.to_csv(processed_dir / "oracle_summary.csv", index=False)
    atomicity_summary.to_csv(processed_dir / "atomicity_summary.csv", index=False)
    phase_summary.to_csv(processed_dir / "phase_summary.csv", index=False)
    certification_summary.to_csv(
        processed_dir / "certification_summary.csv", index=False
    )

    figures = []
    figures += plot_oracle(
        frames["oracle_validation"], frames["homogeneous_limit"], figures_dir
    )
    figures += plot_atomicity(frames["atomicity"], atomicity_summary, figures_dir)
    figures += plot_phase(phase_summary, figures_dir)
    figures += plot_certification(certification_summary, figures_dir)

    metrics: dict[str, Any] = {
        "campaign_id": config["campaign_id"],
        "raw_rows": int(sum(len(frame) for frame in frames.values())),
        **oracle_metrics,
        **atomicity_metrics,
        **phase_metrics,
        **certification_metrics,
    }
    write_json(output_dir / "key_metrics.json", metrics)

    raw_paths = {layer: raw_dir / f"{layer}_runs.csv" for layer in LAYERS}
    manifest_path = write_level_manifest(
        output_dir=output_dir,
        level="N2",
        description=(
            "Confirmatory heterogeneous-capacity campaign: oracle validation, "
            "the price of atomicity, a pressure-by-heterogeneity phase diagram "
            "and the certification frontier of the central solver."
        ),
        sources=(
            config_path,
            REPOSITORY_ROOT / "scripts" / "sp1_n2_confirmatory.py",
            REPOSITORY_ROOT / "scripts" / "sp1_n2_oracle.py",
            REPOSITORY_ROOT / "scripts" / "sp1_n2_analysis.py",
            *raw_paths.values(),
        ),
        row_counts={f"{layer}_runs": len(frames[layer]) for layer in LAYERS},
        claims=(
            "HiGHS reproduces exhaustive enumeration on the enumerable sizes.",
            "With equal capacities the N2 optimum equals the frozen N1 LSAP.",
            "The LP relaxation is strictly cheaper than any atomic coalition.",
            "Feasibility depends on pressure and on capacity dispersion.",
            "Certified optimality degrades with instance size under a budget.",
        ),
        limitations=tuple(config["limitations"]),
        raw_paths=raw_paths,
    )
    return {"manifest": manifest_path, "metrics": metrics, "figures": figures}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyse the SP1.N2 campaign.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package = build(args.config.resolve(), args.output_dir.resolve())
    print(f"N2 package: {package['manifest']}")


if __name__ == "__main__":
    main()
