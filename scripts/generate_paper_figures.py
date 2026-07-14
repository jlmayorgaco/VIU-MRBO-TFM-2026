"""Generate publication-style figures for canonical SP1-SP8 results.

The experiment runners keep SP-specific plots. This script adds a consistent
cross-SP figure layer for thesis/paper use: vector PDF plus high-resolution PNG.
"""

from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExperimentSpec:
    sp: str
    title: str
    path: Path
    primary_metric: str
    primary_label: str
    primary_higher_is_better: bool
    pareto_metric: str | None = None


EXPERIMENTS = [
    ExperimentSpec("SP1", "SP1 homogeneous quorum recruitment", Path("results/sp1/SP1_HOMOGENEOUS_v1_1"), "normalized_regret", "Normalized regret", False, "messages"),
    ExperimentSpec("SP2", "SP2 heterogeneous capacity game", Path("results/sp2/SP2_HETEROGENEOUS_GAME_v1_2"), "final_served_rate", "Served-load rate", True, "normalized_regret"),
    ExperimentSpec("SP3", "SP3 wrench-feasible game", Path("results/sp3/SP3_WRENCH_NASH_GAME_v1_1"), "wrench_feasible_rate", "Wrench-feasible rate", True, "optimality_gap_vs_wrench_oracle"),
    ExperimentSpec("SP4", "SP4 safe docking game", Path("results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3"), "safe_docking_success", "Safe docking success", True, "any_collision"),
    ExperimentSpec("SP5", "SP5 executed payload transport", Path("results/sp5/SP5_PAYLOAD_TRANSPORT_CONFIRMATORY_v2"), "safe_transport_success", "Safe transport success", True, "any_collision"),
    ExperimentSpec("SP6", "SP6 operational robustness", Path("results/sp6/SP6_MC_robustness_comparison_high_power"), "recovery_success", "Recovery success rate", True, "lost_load_rate"),
    ExperimentSpec("SP7", "SP7 communication robustness", Path("results/sp7/SP7_MC_communication_robustness_high_power"), "transport_network_score", "Transport-network score", True, "delay_violation_rate"),
    ExperimentSpec("SP8", "SP8 warehouse-scale scalability", Path("results/sp8/SP8_MC_fleet_ladder_high_power"), "task_completion_rate", "Task completion rate", True, "timeout_rate"),
]

FAMILY_COLORS = {
    "classic": "#4C78A8",
    "sota": "#F58518",
    "model_based": "#54A24B",
    "model_based_oracle": "#7F7F7F",
    "data_driven": "#B279A2",
    "proposed": "#E45756",
    "reference": "#2F4B7C",
}

KEY_METRIC_CANDIDATES = [
    "safe_docking_success",
    "safe_transport_success",
    "final_served_rate",
    "normalized_regret",
    "any_collision",
    "coalition_success_rate",
    "capacity_success_rate",
    "wrench_feasible_rate",
    "arrival_success_rate",
    "transport_success",
    "recovery_success",
    "transport_network_score",
    "task_completion_rate",
    "collision_rate",
    "timeout_rate",
    "false_positive_rate",
    "runtime_ms",
    "runtime_s",
    "runtime_wall_s",
    "messages",
    "communication_messages",
    "energy_proxy_wh",
    "optimality_gap_vs_oracle",
    "optimality_gap_vs_reference",
    "optimality_gap_vs_wrench_oracle",
    "performance_gap_vs_reference",
]


def main() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 180,
            "savefig.dpi": 300,
            "font.size": 8.5,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    index_lines = ["# Paper Figures Index", ""]
    for spec in EXPERIMENTS:
        if not (spec.path / "tables" / "runs.csv").exists():
            continue
        out_dir = spec.path / "paper_figures"
        out_dir.mkdir(parents=True, exist_ok=True)
        runs = pd.read_csv(spec.path / "tables" / "runs.csv")
        ranking = _read_optional(spec.path / "tables" / "performance_ranking.csv")
        hypotheses = _read_optional(spec.path / "tables" / "hypothesis_results.csv")
        produced = []
        produced.append(_plot_primary_metric(spec, runs, out_dir))
        produced.append(_plot_pareto(spec, runs, out_dir))
        produced.append(_plot_metric_heatmap(spec, runs, out_dir))
        if hypotheses is not None and not hypotheses.empty:
            path = _plot_hypotheses(spec, hypotheses, out_dir)
            if path:
                produced.append(path)
        if spec.sp == "SP8":
            produced.append(_plot_sp8_scale_band(spec, runs, out_dir))
        if ranking is not None and not ranking.empty:
            _write_method_table(spec, ranking, out_dir)
        index_lines.extend([f"## {spec.sp}", ""])
        for path in produced:
            if path:
                index_lines.append(f"- `{path.as_posix()}`")
        index_lines.append("")
    Path("results/PAPER_FIGURES_INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")


def _read_optional(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _plot_primary_metric(spec: ExperimentSpec, runs: pd.DataFrame, out_dir: Path) -> Path:
    metric = _metric_or_fallback(runs, spec.primary_metric)
    grouped = _method_summary(runs, metric)
    grouped = grouped.sort_values("mean", ascending=not spec.primary_higher_is_better).head(18)
    y = np.arange(len(grouped))
    colors = [_family_color(row) for _, row in grouped.iterrows()]
    fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.28 * len(grouped) + 1.0)))
    ax.barh(y, grouped["mean"], xerr=grouped["ci95"], color=colors, alpha=0.92, edgecolor="#222222", linewidth=0.35)
    ax.set_yticks(y)
    ax.set_yticklabels([_wrap_label(label, 28) for label in grouped["method_label"]])
    ax.invert_yaxis()
    ax.set_xlabel(spec.primary_label if metric == spec.primary_metric else metric)
    ax.set_title(f"{spec.title}: method ranking")
    ax.axvline(0.0, color="#333333", linewidth=0.7)
    _add_family_legend(ax, grouped)
    fig.tight_layout()
    return _save(fig, out_dir / "paper_primary_metric_by_method")


def _plot_pareto(spec: ExperimentSpec, runs: pd.DataFrame, out_dir: Path) -> Path:
    quality = _metric_or_fallback(runs, spec.primary_metric)
    cost = "runtime_ms" if "runtime_ms" in runs.columns else None
    if cost is None:
        cost = "communication_messages" if "communication_messages" in runs.columns else quality
    grouped = _method_summary(runs, quality, extra=[cost, "communication_messages", "energy_proxy_wh"])
    fig, ax = plt.subplots(figsize=(6.0, 4.1))
    for _, row in grouped.iterrows():
        x = max(float(row.get(f"{cost}_mean", np.nan)), 1e-6)
        y = float(row["mean"])
        messages = max(float(row.get("communication_messages_mean", 1.0)), 1.0)
        size = 42.0 + 38.0 * math.log10(messages + 1.0)
        ax.scatter(x, y, s=size, color=_family_color(row), alpha=0.86, edgecolor="#222222", linewidth=0.35)
        ax.annotate(_short(row["method"]), (x, y), xytext=(3, 2), textcoords="offset points", fontsize=6.6)
    ax.set_xscale("log")
    ax.set_xlabel(f"{cost} (log)")
    ax.set_ylabel(spec.primary_label if quality == spec.primary_metric else quality)
    ax.set_title(f"{spec.title}: quality-resource Pareto")
    fig.tight_layout()
    return _save(fig, out_dir / "paper_quality_resource_pareto")


def _plot_metric_heatmap(spec: ExperimentSpec, runs: pd.DataFrame, out_dir: Path) -> Path:
    metrics = [metric for metric in KEY_METRIC_CANDIDATES if metric in runs.columns]
    metrics = metrics[:10]
    if len(metrics) < 2:
        return out_dir / "paper_metric_heatmap"
    grouped = []
    for method, selected in runs.groupby("method"):
        row = {"method": method, "method_label": _first(selected, "method_label", method)}
        for metric in metrics:
            row[metric] = pd.to_numeric(selected[metric], errors="coerce").mean()
        grouped.append(row)
    df = pd.DataFrame(grouped)
    score_metric = spec.primary_metric if spec.primary_metric in df.columns else metrics[0]
    df = df.sort_values(score_metric, ascending=not spec.primary_higher_is_better).head(16)
    matrix = []
    for metric in metrics:
        values = pd.to_numeric(df[metric], errors="coerce").to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0 or np.nanmax(finite) - np.nanmin(finite) <= 1e-12:
            norm = np.zeros_like(values)
        else:
            norm = (values - np.nanmin(finite)) / (np.nanmax(finite) - np.nanmin(finite))
        if _lower_is_better(metric):
            norm = 1.0 - norm
        matrix.append(norm)
    mat = np.vstack(matrix).T
    fig, ax = plt.subplots(figsize=(max(6.6, 0.58 * len(metrics)), max(3.5, 0.25 * len(df) + 1.1)))
    im = ax.imshow(mat, aspect="auto", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xticks(np.arange(len(metrics)))
    ax.set_xticklabels([_metric_label(metric) for metric in metrics], rotation=35, ha="right")
    ax.set_yticks(np.arange(len(df)))
    ax.set_yticklabels([_wrap_label(label, 28) for label in df["method_label"]])
    ax.set_title(f"{spec.title}: normalized metric matrix")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Normalized utility")
    fig.tight_layout()
    return _save(fig, out_dir / "paper_metric_heatmap")


def _plot_hypotheses(spec: ExperimentSpec, hypotheses: pd.DataFrame, out_dir: Path) -> Path | None:
    if "effect" not in hypotheses.columns:
        return None
    df = hypotheses.copy()
    df["effect"] = pd.to_numeric(df["effect"], errors="coerce")
    df = df[np.isfinite(df["effect"])].copy()
    if df.empty:
        return None
    df = df.head(14)
    labels = [str(row.get("id", row.get("methods", f"H{i+1}"))) for i, row in df.iterrows()]
    y = np.arange(len(df))
    x = df["effect"].to_numpy(dtype=float)
    xerr = None
    if {"ci95_low", "ci95_high"}.issubset(df.columns):
        lo = pd.to_numeric(df["ci95_low"], errors="coerce").to_numpy(dtype=float)
        hi = pd.to_numeric(df["ci95_high"], errors="coerce").to_numpy(dtype=float)
        if np.isfinite(lo).any() and np.isfinite(hi).any():
            xerr = np.vstack([np.maximum(x - lo, 0.0), np.maximum(hi - x, 0.0)])
    colors = ["#2ca02c" if bool(row.get("reject_holm", False)) else "#7f7f7f" for _, row in df.iterrows()]
    fig, ax = plt.subplots(figsize=(7.2, max(2.8, 0.30 * len(df) + 1.0)))
    ax.barh(y, x, xerr=xerr, color=colors, alpha=0.88, edgecolor="#222222", linewidth=0.35)
    ax.axvline(0.0, color="#222222", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([_wrap_label(label, 38) for label in labels])
    ax.invert_yaxis()
    ax.set_xlabel("Estimated paired effect")
    ax.set_title(f"{spec.title}: hypothesis effects")
    fig.tight_layout()
    return _save(fig, out_dir / "paper_hypothesis_effects")


def _plot_sp8_scale_band(spec: ExperimentSpec, runs: pd.DataFrame, out_dir: Path) -> Path:
    if "n_robots" not in runs.columns:
        return out_dir / "paper_sp8_scale_completion"
    metric = "task_completion_rate"
    methods = (
        runs.groupby("method")[metric]
        .mean()
        .sort_values(ascending=False)
        .head(7)
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for method in methods:
        selected = runs[runs["method"] == method]
        grouped = selected.groupby("n_robots")[metric].agg(["mean", "std", "count"]).reset_index().sort_values("n_robots")
        x = grouped["n_robots"].to_numpy(dtype=float)
        y = grouped["mean"].to_numpy(dtype=float)
        sem = grouped["std"].fillna(0.0).to_numpy(dtype=float) / np.sqrt(np.maximum(grouped["count"].to_numpy(dtype=float), 1.0))
        ax.plot(x, y, marker="o", linewidth=1.55, label=_short(method))
        lo = np.clip(y - 1.96 * sem, 0.0, 1.0)
        hi = np.clip(y + 1.96 * sem, 0.0, 1.0)
        ax.fill_between(x, lo, hi, alpha=0.12)
    ax.set_xscale("log")
    ax.set_xlabel("AMR count (log)")
    ax.set_ylabel("Task completion rate")
    ax.set_title("SP8 scale curve with 95% CI")
    ax.set_ylim(-0.02, 1.02)
    ax.legend(ncol=2)
    fig.tight_layout()
    return _save(fig, out_dir / "paper_sp8_scale_completion_ci")


def _method_summary(runs: pd.DataFrame, metric: str, extra: Iterable[str] = ()) -> pd.DataFrame:
    rows = []
    for method, selected in runs.groupby("method"):
        values = pd.to_numeric(selected[metric], errors="coerce").dropna().to_numpy(dtype=float)
        if values.size == 0:
            continue
        row = {
            "method": method,
            "method_label": _first(selected, "method_label", method),
            "method_family": _first(selected, "method_family", ""),
            "method_ownership": _first(selected, "method_ownership", ""),
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
            "n": int(values.size),
            "ci95": float(1.96 * (np.std(values, ddof=1) if values.size > 1 else 0.0) / math.sqrt(max(values.size, 1))),
        }
        for item in extra:
            if item in selected.columns:
                row[f"{item}_mean"] = float(pd.to_numeric(selected[item], errors="coerce").mean())
        rows.append(row)
    return pd.DataFrame(rows)


def _write_method_table(spec: ExperimentSpec, ranking: pd.DataFrame, out_dir: Path) -> None:
    subset = ranking[ranking.get("scenario_generator", "ALL_SCENARIOS").astype(str) == "ALL_SCENARIOS"] if "scenario_generator" in ranking.columns else ranking
    if subset.empty:
        subset = ranking
    cols = [col for col in ["rank", "method", "method_label", "method_family", "method_scope", "method_ownership"] if col in subset.columns]
    metric_cols = [col for col in subset.columns if col.endswith("_mean") and any(key in col for key in ["success", "feasible", "completion", "collision", "timeout", "gap", "runtime"])]
    subset[cols + metric_cols[:8]].head(20).to_csv(out_dir / "paper_method_table.csv", index=False)


def _metric_or_fallback(runs: pd.DataFrame, metric: str) -> str:
    if metric in runs.columns:
        return metric
    for candidate in KEY_METRIC_CANDIDATES:
        if candidate in runs.columns:
            return candidate
    raise ValueError(f"No usable metric in {runs.columns.tolist()}")


def _lower_is_better(metric: str) -> bool:
    keys = ["gap", "collision", "timeout", "false_positive", "runtime", "messages", "energy", "residual", "error", "lost"]
    return any(key in metric for key in keys)


def _family_color(row: pd.Series) -> str:
    family = str(row.get("method_family", "")).lower()
    ownership = str(row.get("method_ownership", "")).lower()
    if "proposed" in ownership:
        return "#D62728"
    return FAMILY_COLORS.get(family, "#6B7280")


def _add_family_legend(ax: plt.Axes, grouped: pd.DataFrame) -> None:
    seen = {}
    for _, row in grouped.iterrows():
        label = "proposed" if "proposed" in str(row.get("method_ownership", "")).lower() else str(row.get("method_family", "other"))
        seen[label] = _family_color(row)
    handles = [plt.Line2D([0], [0], marker="s", linestyle="", color=color, label=label, markersize=6) for label, color in seen.items()]
    if handles:
        ax.legend(handles=handles, loc="lower right", frameon=True)


def _first(df: pd.DataFrame, column: str, default: str) -> str:
    if column not in df.columns:
        return default
    values = df[column].dropna().astype(str)
    return str(values.iloc[0]) if not values.empty else default


def _wrap_label(value: str, width: int) -> str:
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False)) or str(value)


def _short(value: str) -> str:
    text = str(value)
    replacements = {
        "centralized_": "cent_",
        "decentralized_": "dec_",
        "ours_": "ours_",
        "classic_": "classic_",
        "wrench_market": "wm",
        "hierarchical": "hier",
        "communication": "comm",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text[:22]


def _metric_label(metric: str) -> str:
    return metric.replace("_", " ")


def _save(fig: plt.Figure, stem: Path) -> Path:
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return png


if __name__ == "__main__":
    main()
