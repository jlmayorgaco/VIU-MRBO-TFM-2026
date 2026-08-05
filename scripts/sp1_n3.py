"""SP1 level N3: distributed baseline adaptations on paired GEO worlds."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sp1_levels_common import (
    COLORS,
    GEO_SOURCE_ROOT,
    LEVELS_OUTPUT_ROOT,
    METHOD_COLORS,
    add_sample_note,
    configure_publication_style,
    ensure_columns,
    label_panels,
    line_with_band,
    method_label,
    quantile_summary,
    save_figure,
    write_json,
    write_level_manifest,
)


N3_METHODS = (
    "capacity_cbba_scalar",
    "physical_cbba_marginal",
    "weighted_grape_scalar",
    "pair_role_grape_s_physical",
)


def _aggregate_runs(runs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & runs["method"].isin(N3_METHODS)
    ].copy()
    recovered["welfare_per_load"] = (
        recovered["physical_welfare"] / recovered["n_loads"]
    )
    summary = quantile_summary(
        recovered,
        groups=("method", "n_robots", "n_loads"),
        metrics=(
            "served_load_rate",
            "welfare_per_load",
            "runtime_total_ms",
            "messages",
            "bytes",
        ),
    )
    gaps = recovered.dropna(
        subset=("optimality_gap_vs_certified_milp",)
    ).copy()
    gap_summary = quantile_summary(
        gaps,
        groups=("method", "n_robots", "n_loads"),
        metrics=("optimality_gap_vs_certified_milp",),
    )
    return summary, gap_summary


def _plot_quality_runtime(
    summary: pd.DataFrame,
    figures_dir: Path,
) -> list[Path]:
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    markers = ("o", "s", "^", "D")
    for method, marker in zip(N3_METHODS, markers, strict=True):
        block = summary.loc[summary["method"] == method]
        color = METHOD_COLORS[method]
        ordered = block.sort_values("n_robots")
        axes[0].errorbar(
            ordered["n_robots"],
            ordered["served_load_rate_median"],
            yerr=np.vstack(
                (
                    ordered["served_load_rate_median"]
                    - ordered["served_load_rate_p05"],
                    ordered["served_load_rate_p95"]
                    - ordered["served_load_rate_median"],
                )
            ),
            color=color,
            marker=marker,
            capsize=2.4,
            label=method_label(method),
        )
        line_with_band(
            axes[1],
            block,
            x="n_robots",
            median="runtime_total_ms_median",
            low="runtime_total_ms_p05",
            high="runtime_total_ms_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Calidad tras recuperación común",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Tiempo total [ms]",
        yscale="log",
        title="Coste computacional observado",
    )
    axes[0].legend(
        loc="lower left",
        ncol=2,
        columnspacing=1.0,
        handlelength=1.6,
    )
    add_sample_note(
        axes[0],
        "P50 y [P05, P95] sobre mundos pareados de las seis familias.",
    )
    label_panels(axes)
    return save_figure(figure, figures_dir / "n3_quality_runtime")


def _plot_communication_gap(
    summary: pd.DataFrame,
    gap_summary: pd.DataFrame,
    figures_dir: Path,
) -> list[Path]:
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    markers = ("o", "s", "^", "D")
    for method, marker in zip(N3_METHODS, markers, strict=True):
        block = summary.loc[summary["method"] == method]
        color = METHOD_COLORS[method]
        line_with_band(
            axes[0],
            block,
            x="n_robots",
            median="bytes_median",
            low="bytes_p05",
            high="bytes_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
        gap_block = gap_summary.loc[gap_summary["method"] == method]
        if not gap_block.empty:
            line_with_band(
                axes[1],
                gap_block,
                x="n_robots",
                median="optimality_gap_vs_certified_milp_median",
                low="optimality_gap_vs_certified_milp_p05",
                high="optimality_gap_vs_certified_milp_p95",
                color=color,
                label=method_label(method),
                marker=marker,
            )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Bytes contabilizados",
        yscale="log",
        title="Escala de comunicación",
    )
    axes[1].axhline(
        0.0,
        color=COLORS["dark"],
        linestyle=":",
        linewidth=1.0,
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Gap frente a MILP certificado",
        title="Calidad condicionada a oráculo válido",
    )
    axes[0].legend(
        loc="upper left",
        ncol=2,
        columnspacing=1.0,
        handlelength=1.6,
    )
    add_sample_note(
        axes[1],
        "Los casos sin certificado MILP se excluyen; no se imputa gap.",
    )
    label_panels(axes)
    return save_figure(figure, figures_dir / "n3_communication_gap")


def _plot_pareto(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & runs["method"].isin(N3_METHODS)
    ].copy()
    recovered["welfare_per_load"] = (
        recovered["physical_welfare"] / recovered["n_loads"]
    )
    pareto = (
        recovered.groupby("method", as_index=False)
        .agg(
            served_load_rate=("served_load_rate", "median"),
            welfare_per_load=("welfare_per_load", "median"),
            runtime_total_ms=("runtime_total_ms", "median"),
            bytes=("bytes", "median"),
            n_worlds=("world_id", "nunique"),
        )
        .sort_values("runtime_total_ms")
    )

    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    sizes = 45 + 115 * (
        np.log10(pareto["bytes"].clip(lower=1))
        - np.log10(pareto["bytes"].clip(lower=1)).min()
    ) / max(
        np.log10(pareto["bytes"].clip(lower=1)).max()
        - np.log10(pareto["bytes"].clip(lower=1)).min(),
        1e-12,
    )
    for (_, row), size in zip(pareto.iterrows(), sizes, strict=True):
        method = str(row["method"])
        axis.scatter(
            row["runtime_total_ms"],
            row["welfare_per_load"],
            s=size,
            color=METHOD_COLORS[method],
            edgecolor="white",
            linewidth=0.9,
            zorder=3,
        )
        axis.annotate(
            method_label(method),
            (row["runtime_total_ms"], row["welfare_per_load"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7.6,
            color=COLORS["dark"],
        )
    axis.set(
        xscale="log",
        xlabel="Tiempo total mediano [ms]",
        ylabel="Bienestar físico mediano por carga",
        title="Frontera descriptiva calidad–cómputo–comunicación",
    )
    add_sample_note(
        axis,
        "El área del marcador crece con los bytes; no implica dominancia estadística.",
    )
    return save_figure(figure, figures_dir / "n3_pareto"), pareto


def build_level(source_dir: Path, output_dir: Path) -> dict[str, object]:
    """Build the N3 distributed-baseline publication package."""

    configure_publication_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = output_dir / "processed"
    figures_dir = output_dir / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)

    runs_path = source_dir / "runs.parquet"
    summary_path = source_dir / "summary.csv"
    metadata_path = source_dir / "method_metadata.csv"
    config_path = source_dir / "config_frozen.yaml"
    runs = pd.read_parquet(runs_path)
    ensure_columns(
        runs,
        (
            "world_id",
            "family",
            "seed",
            "n_robots",
            "n_loads",
            "method",
            "closure_stage",
            "served_load_rate",
            "physical_welfare",
            "runtime_total_ms",
            "messages",
            "bytes",
            "optimality_gap_vs_certified_milp",
        ),
    )

    level_runs = runs.loc[runs["method"].isin(N3_METHODS)].copy()
    summary, gap_summary = _aggregate_runs(level_runs)
    summary.to_csv(processed_dir / "n3_summary.csv", index=False)
    gap_summary.to_csv(processed_dir / "n3_gap_summary.csv", index=False)
    quality_paths = _plot_quality_runtime(summary, figures_dir)
    communication_paths = _plot_communication_gap(
        summary, gap_summary, figures_dir
    )
    pareto_paths, pareto = _plot_pareto(level_runs, figures_dir)
    pareto.to_csv(processed_dir / "n3_pareto.csv", index=False)

    recovered = level_runs.loc[
        level_runs["closure_stage"] == "RECOVERED"
    ]
    gap_count = int(
        recovered["optimality_gap_vs_certified_milp"].notna().sum()
    )
    key_metrics = {
        "raw_level_rows": int(len(level_runs)),
        "paired_worlds": int(level_runs["world_id"].nunique()),
        "methods": list(N3_METHODS),
        "max_n": int(level_runs["n_robots"].max()),
        "recovered_rows": int(len(recovered)),
        "certified_gap_rows": gap_count,
        "architecture": "distributed_adaptations",
        "common_certifier_and_recovery": True,
    }
    write_json(output_dir / "key_metrics.json", key_metrics)
    (output_dir / "REPORT.md").write_text(
        "\n".join(
            (
                "# SP1 · Nivel 3 — baselines distribuidos",
                "",
                f"- Mundos pareados: {level_runs['world_id'].nunique():,}.",
                f"- Filas método–mundo–cierre: {len(level_runs):,}.",
                f"- Filas RECOVERED con gap MILP válido: {gap_count:,}.",
                "- Métodos: Capacity-CBBA y variantes CBBA/GRAPE implementadas.",
                "- Todos atraviesan el mismo certificador y recuperación.",
                "- Son adaptaciones/proxies; no heredan garantías externas.",
                "",
            )
        ),
        encoding="utf-8",
    )
    manifest_path = write_level_manifest(
        output_dir=output_dir,
        level="N3",
        description=(
            "Distributed CBBA/GRAPE adaptations evaluated on the paired "
            "SP1-GEO confirmatory worlds."
        ),
        sources=(runs_path, summary_path, metadata_path, config_path),
        row_counts={
            "raw_level_rows": len(level_runs),
            "processed_summary": len(summary),
            "processed_gap_summary": len(gap_summary),
            "processed_pareto": len(pareto),
        },
        claims=(
            "All N3 methods share worlds, evaluator, certifier and recovery.",
            "MILP gaps are reported only where a certified reference exists.",
        ),
        limitations=(
            "The methods are implemented adaptations and do not automatically inherit source-method guarantees.",
            "The campaign evaluates static coalition formation, not physical transport.",
        ),
    )
    return {
        "manifest": manifest_path,
        "figures": quality_paths + communication_paths + pareto_paths,
        "key_metrics": key_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the SP1 N3 distributed-baseline package."
    )
    parser.add_argument("--source-dir", type=Path, default=GEO_SOURCE_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=LEVELS_OUTPUT_ROOT / "n3",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package = build_level(args.source_dir, args.output_dir)
    print(f"N3 package: {package['manifest'].resolve()}")


if __name__ == "__main__":
    main()
