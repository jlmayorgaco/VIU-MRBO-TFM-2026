"""SP1 level N4: proposed Geo-QPG method, variants and closure analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sp1_levels_common import (
    COLORS,
    FAMILY_LABELS,
    GEO_SOURCE_ROOT,
    LEVELS_OUTPUT_ROOT,
    METHOD_COLORS,
    add_sample_note,
    artifact_records,
    bool_to_float,
    configure_publication_style,
    ensure_columns,
    family_label,
    label_panels,
    line_with_band,
    method_label,
    quantile_summary,
    save_figure,
    source_record,
    write_json,
    write_level_manifest,
)


MAIN_METHOD = "geo_qpg_logit_physical"
QPG_METHODS = (
    "qpg_logit_scalar",
    MAIN_METHOD,
    "geo_qpg_smith_physical",
)
COMPARISON_METHODS = (
    MAIN_METHOD,
    "capacity_cbba_scalar",
    "pair_role_grape_s_physical",
)


def _closure_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    main = runs.loc[runs["method"] == MAIN_METHOD].copy()
    main["physical_feasible_float"] = bool_to_float(
        main["world_physical_feasible"]
    )
    summary = quantile_summary(
        main,
        groups=("closure_stage", "n_robots", "n_loads"),
        metrics=(
            "physical_feasible_float",
            "served_load_rate",
            "robots_changed_by_recovery",
        ),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    styles = (
        ("RAW", COLORS["red"], "o"),
        ("CERTIFIED", COLORS["blue"], "s"),
        ("RECOVERED", COLORS["green"], "^"),
    )
    for stage, color, marker in styles:
        block = summary.loc[summary["closure_stage"] == stage]
        axes[0].plot(
            block["n_robots"],
            block["physical_feasible_float_mean"],
            color=color,
            marker=marker,
            label=stage,
        )
        axes[1].plot(
            block["n_robots"],
            block["served_load_rate_median"],
            color=color,
            marker=marker,
            label=stage,
        )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Fracción físicamente factible",
        ylim=(-0.03, 1.03),
        title="La decisión continua requiere cierre",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Recuperación frente a abstención",
    )
    axes[0].legend(loc="lower right")
    add_sample_note(
        axes[0],
        "Mismos mundos y método; cambia únicamente la etapa de cierre.",
    )
    label_panels(axes)
    return (
        save_figure(figure, figures_dir / "n4_closure_ladder"),
        summary,
    )


def _scenario_quality_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & runs["method"].isin(COMPARISON_METHODS)
    ].copy()
    recovered["welfare_per_load"] = (
        recovered["physical_welfare"] / recovered["n_loads"]
    )
    summary = quantile_summary(
        recovered,
        groups=("family", "method"),
        metrics=("served_load_rate", "welfare_per_load"),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.25))
    family_order = list(FAMILY_LABELS)
    x_values = np.arange(len(family_order))
    offsets = (-0.22, 0.0, 0.22)
    markers = ("o", "s", "^")
    for method, offset, marker in zip(
        COMPARISON_METHODS, offsets, markers, strict=True
    ):
        block = (
            summary.loc[summary["method"] == method]
            .set_index("family")
            .reindex(family_order)
        )
        axes[0].errorbar(
            x_values + offset,
            block["served_load_rate_median"],
            yerr=np.vstack(
                (
                    block["served_load_rate_median"]
                    - block["served_load_rate_p05"],
                    block["served_load_rate_p95"]
                    - block["served_load_rate_median"],
                )
            ),
            fmt=marker,
            color=METHOD_COLORS[method],
            capsize=2.2,
            label=method_label(method),
        )
        axes[1].errorbar(
            x_values + offset,
            block["welfare_per_load_median"],
            yerr=np.vstack(
                (
                    block["welfare_per_load_median"]
                    - block["welfare_per_load_p05"],
                    block["welfare_per_load_p95"]
                    - block["welfare_per_load_median"],
                )
            ),
            fmt=marker,
            color=METHOD_COLORS[method],
            capsize=2.2,
            label=method_label(method),
        )
    tick_labels = [
        family_label(family).replace(" · ", "\n") for family in family_order
    ]
    for axis in axes:
        axis.set_xticks(x_values, tick_labels)
    axes[0].set(
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Cobertura por régimen",
    )
    axes[1].set(
        ylabel="Bienestar físico por carga",
        title="Calidad después del cierre común",
    )
    axes[0].legend(
        loc="lower left",
        ncol=3,
        columnspacing=0.8,
        handletextpad=0.4,
    )
    add_sample_note(
        axes[1],
        "P50 y [P05, P95]; la comparación descriptiva no acredita superioridad.",
    )
    label_panels(axes)
    return (
        save_figure(figure, figures_dir / "n4_scenario_quality"),
        summary,
    )


def _oracle_gap_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    gaps = runs.loc[
        (runs["method"] == MAIN_METHOD)
        & (runs["closure_stage"] == "RECOVERED")
    ].dropna(subset=("optimality_gap_vs_certified_milp",))
    summary = quantile_summary(
        gaps,
        groups=("family", "n_robots", "n_loads"),
        metrics=("optimality_gap_vs_certified_milp",),
    )
    figure, axis = plt.subplots(figsize=(8.0, 4.45))
    family_order = list(FAMILY_LABELS)
    data = [
        gaps.loc[
            gaps["family"] == family,
            "optimality_gap_vs_certified_milp",
        ].dropna()
        for family in family_order
    ]
    boxes = axis.boxplot(
        data,
        tick_labels=[
            family_label(family).replace(" · ", "\n")
            for family in family_order
        ],
        patch_artist=True,
        showfliers=False,
        widths=0.62,
        medianprops={"color": "white", "linewidth": 1.5},
    )
    for patch in boxes["boxes"]:
        patch.set_facecolor(COLORS["blue"])
        patch.set_edgecolor(COLORS["blue"])
        patch.set_alpha(0.88)
    axis.axhline(0.0, color=COLORS["dark"], linestyle=":", linewidth=1)
    axis.set(
        ylabel="Gap frente a MILP certificado",
        title="Geo-QPG físico: gap condicionado a referencia válida",
    )
    add_sample_note(
        axis,
        f"n={len(gaps)} pares con certificado; ausencias conservadas como ausencias.",
    )
    return save_figure(figure, figures_dir / "n4_oracle_gap"), summary


def _resource_scaling_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    methods = (
        MAIN_METHOD,
        "qpg_logit_scalar",
        "geo_qpg_smith_physical",
        "capacity_cbba_scalar",
        "pair_role_grape_s_physical",
    )
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & runs["method"].isin(methods)
    ]
    summary = quantile_summary(
        recovered,
        groups=("method", "n_robots", "n_loads"),
        metrics=("runtime_total_ms", "bytes"),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    markers = ("o", "s", "^", "D", "P")
    for method, marker in zip(methods, markers, strict=True):
        block = summary.loc[summary["method"] == method]
        color = METHOD_COLORS[method]
        line_with_band(
            axes[0],
            block,
            x="n_robots",
            median="runtime_total_ms_median",
            low="runtime_total_ms_p05",
            high="runtime_total_ms_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
        line_with_band(
            axes[1],
            block,
            x="n_robots",
            median="bytes_median",
            low="bytes_p05",
            high="bytes_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Tiempo total [ms]",
        yscale="log",
        title="Escalabilidad temporal observada",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Bytes contabilizados",
        yscale="log",
        title="Escalabilidad comunicativa observada",
    )
    axes[0].legend(
        loc="upper left",
        ncol=2,
        columnspacing=0.8,
        handlelength=1.5,
    )
    add_sample_note(
        axes[1],
        "La campaña llega a N=64; no identifica el orden asintótico.",
    )
    label_panels(axes)
    return (
        save_figure(figure, figures_dir / "n4_resource_scaling"),
        summary,
    )


def _signal_ablation_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    signal = runs.loc[
        (runs["closure_stage"] == "RAW")
        & runs["method"].isin(("qpg_logit_scalar", MAIN_METHOD))
        & runs["family"].isin(
            ("F3_torque_complementarity", "F4_mixed_geometry_route")
        )
    ].copy()
    summary = quantile_summary(
        signal,
        groups=("family", "method", "n_robots"),
        metrics=(
            "false_positive_given_committed",
            "served_load_rate",
            "physical_welfare",
        ),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    for method, marker in (
        ("qpg_logit_scalar", "o"),
        (MAIN_METHOD, "s"),
    ):
        color = METHOD_COLORS[method]
        for family, linestyle in (
            ("F3_torque_complementarity", "-"),
            ("F4_mixed_geometry_route", "--"),
        ):
            block = summary.loc[
                (summary["method"] == method)
                & (summary["family"] == family)
            ]
            label = (
                f"{method_label(method)} · "
                f"{family_label(family).split(' · ')[0]}"
            )
            axes[0].plot(
                block["n_robots"],
                block["false_positive_given_committed_mean"],
                color=color,
                marker=marker,
                linestyle=linestyle,
                label=label,
            )
            axes[1].plot(
                block["n_robots"],
                block["served_load_rate_median"],
                color=color,
                marker=marker,
                linestyle=linestyle,
                label=label,
            )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Falso positivo dado compromiso",
        ylim=(-0.03, 1.03),
        title="Ablación de señal antes del certificador",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Cobertura RAW asociada",
    )
    axes[0].legend(
        loc="upper left",
        ncol=2,
        columnspacing=0.8,
        handlelength=1.8,
    )
    add_sample_note(
        axes[0],
        "Endpoint H3 predeclarado: RAW en F3–F4; el gate de −20 pp no se alcanzó.",
    )
    label_panels(axes)
    return (
        save_figure(figure, figures_dir / "n4_signal_ablation"),
        summary,
    )


def _engine_ablation_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    methods = (
        MAIN_METHOD,
        "geo_qpg_smith_physical",
        "pair_role_grape_s_physical",
    )
    recovered = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & runs["method"].isin(methods)
    ].copy()
    recovered["welfare_per_load"] = (
        recovered["physical_welfare"] / recovered["n_loads"]
    )
    summary = quantile_summary(
        recovered,
        groups=("method", "n_robots", "n_loads"),
        metrics=("welfare_per_load", "served_load_rate"),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    for method, marker in zip(methods, ("o", "s", "^"), strict=True):
        block = summary.loc[summary["method"] == method].sort_values(
            "n_robots"
        )
        color = METHOD_COLORS[method]
        axes[0].errorbar(
            block["n_robots"],
            block["welfare_per_load_median"],
            yerr=np.vstack(
                (
                    block["welfare_per_load_median"]
                    - block["welfare_per_load_p05"],
                    block["welfare_per_load_p95"]
                    - block["welfare_per_load_median"],
                )
            ),
            color=color,
            marker=marker,
            capsize=2.4,
            label=method_label(method),
        )
        axes[1].errorbar(
            block["n_robots"],
            block["served_load_rate_median"],
            yerr=np.vstack(
                (
                    block["served_load_rate_median"]
                    - block["served_load_rate_p05"],
                    block["served_load_rate_p95"]
                    - block["served_load_rate_median"],
                )
            ),
            color=color,
            marker=marker,
            capsize=2.4,
            label=method_label(method),
        )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Bienestar físico por carga",
        title="Motor de revisión: calidad",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Equivalencia práctica de cobertura",
    )
    axes[0].legend(loc="lower left")
    add_sample_note(
        axes[1],
        "H5 acredita equivalencia de cobertura ±0.03; no superioridad de bienestar.",
    )
    label_panels(axes)
    return (
        save_figure(figure, figures_dir / "n4_engine_ablation"),
        summary,
    )


def _failure_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    methods = (MAIN_METHOD, "capacity_cbba_scalar")
    failure = runs.loc[
        (runs["closure_stage"] == "RECOVERED")
        & (runs["family"] == "F5_network_failure")
        & runs["method"].isin(methods)
    ].copy()
    summary = quantile_summary(
        failure,
        groups=("method", "n_robots", "n_loads"),
        metrics=(
            "recourse_robot_changes",
            "served_load_rate",
            "lost_served_value",
        ),
    )
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    for method, marker in zip(methods, ("o", "s"), strict=True):
        block = summary.loc[summary["method"] == method]
        color = METHOD_COLORS[method]
        line_with_band(
            axes[0],
            block,
            x="n_robots",
            median="recourse_robot_changes_median",
            low="recourse_robot_changes_p05",
            high="recourse_robot_changes_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
        line_with_band(
            axes[1],
            block,
            x="n_robots",
            median="served_load_rate_median",
            low="served_load_rate_p05",
            high="served_load_rate_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Robots cambiados por recourse",
        title="Proxy estático posterior al fallo",
    )
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Fracción de cargas servidas",
        ylim=(-0.03, 1.03),
        title="Cobertura después de recuperación",
    )
    axes[0].legend(loc="upper left")
    add_sample_note(
        axes[0],
        "F5 es una instantánea postfallo; no mide una trayectoria dinámica.",
    )
    label_panels(axes)
    return save_figure(figure, figures_dir / "n4_failure_proxy"), summary


def _anytime_figure(
    events: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame]:
    traces = events.loc[
        (events["event"] == "qpg_trace")
        & events["method"].isin(QPG_METHODS)
        & events["potential"].notna()
    ].copy()
    traces = traces.sort_values(["method", "world_id", "iteration"])
    groups = traces.groupby(["method", "world_id"], sort=False)
    traces["potential_first"] = groups["potential"].transform("first")
    traces["potential_last"] = groups["potential"].transform("last")
    denominator = traces["potential_last"] - traces["potential_first"]
    traces["normalized_progress"] = (
        traces["potential"] - traces["potential_first"]
    ) / denominator.replace(0.0, np.nan)
    summary = quantile_summary(
        traces,
        groups=("method", "iteration"),
        metrics=("normalized_progress", "max_change"),
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    for method, marker in zip(QPG_METHODS, ("o", "s", "^"), strict=True):
        block = summary.loc[summary["method"] == method]
        color = METHOD_COLORS[method]
        line_with_band(
            axes[0],
            block,
            x="iteration",
            median="normalized_progress_median",
            low="normalized_progress_p05",
            high="normalized_progress_p95",
            color=color,
            label=method_label(method),
            marker=marker,
        )
        valid = block.loc[block["max_change_median"] > 0.0]
        axes[1].plot(
            valid["iteration"],
            valid["max_change_median"],
            color=color,
            marker=marker,
            label=method_label(method),
        )
    axes[0].set(
        xlabel="Iteración digital",
        ylabel="Progreso potencial normalizado",
        ylim=(-0.08, 1.08),
        title="Comportamiento anytime del potencial",
    )
    axes[1].set(
        xlabel="Iteración digital",
        ylabel="Cambio máximo de preferencia",
        yscale="log",
        title="Residual de actualización",
    )
    axes[0].legend(loc="lower right")
    add_sample_note(
        axes[0],
        "Normalización por mundo; no es una prueba de convergencia global.",
    )
    label_panels(axes)
    return save_figure(figure, figures_dir / "n4_anytime"), summary


def _gate_figure(
    gates: pd.DataFrame,
    figures_dir: Path,
) -> list[Path]:
    columns = (
        "feasibility_gate",
        "coverage_gate",
        "quality_gate",
        "gap_gate",
        "runtime_gate",
        "bytes_gate",
    )
    matrix = gates.loc[:, columns].astype(float).to_numpy()
    labels = [
        f"{str(row.family).split('_')[0]} · N={int(row.n_robots)}"
        for row in gates.itertuples()
    ]
    figure, axis = plt.subplots(figsize=(8.2, 5.7))
    axis.imshow(
        matrix,
        cmap=mpl_gate_cmap(),
        vmin=0.0,
        vmax=1.0,
        aspect="auto",
        interpolation="nearest",
    )
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(
                column,
                row,
                "P" if matrix[row, column] > 0.5 else "F",
                ha="center",
                va="center",
                color="white",
                fontsize=9.0,
                fontweight="bold",
            )
    axis.set_xticks(
        np.arange(len(columns)),
        ("Fact.", "Cob.", "Cal.", "Gap", "CPU", "Bytes"),
    )
    axis.set_yticks(np.arange(len(labels)), labels)
    axis.set(
        title="Gate compuesto N4 frente al baseline distribuido",
        xlabel="Criterios predeclarados",
    )
    axis.tick_params(axis="y", labelsize=7.2)
    add_sample_note(
        axis,
        "Verde: criterio individual; rojo: fallo. Ninguna de 15 celdas pasa el conjunto.",
    )
    return save_figure(figure, figures_dir / "n4_composite_gates")


def mpl_gate_cmap():
    """Two-color map kept local to avoid another plotting dependency."""

    from matplotlib.colors import ListedColormap

    return ListedColormap((COLORS["red"], COLORS["green"]))


def _build_n3_n4_comparison(
    gates: pd.DataFrame,
    comparison_dir: Path,
    source_path: Path,
) -> dict[str, object]:
    figures_dir = comparison_dir / "figures"
    processed_dir = comparison_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    gates.to_csv(
        processed_dir / "n3_n4_composite_gates.csv",
        index=False,
    )
    figure, axis = plt.subplots(figsize=(7.4, 4.7))
    for row in gates.itertuples():
        family = str(row.family)
        color = COLORS["green"] if bool(row.quality_gate) else COLORS["red"]
        axis.scatter(
            row.runtime_ratio,
            row.bytes_ratio,
            s=28 + 0.8 * row.n_robots,
            color=color,
            alpha=0.78,
            edgecolor="white",
            linewidth=0.7,
        )
        axis.annotate(
            f"{family.split('_')[0]}-{int(row.n_robots)}",
            (row.runtime_ratio, row.bytes_ratio),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=6.6,
        )
    axis.axvline(1.0, color=COLORS["gray"], linestyle=":", linewidth=1)
    axis.axhline(1.0, color=COLORS["gray"], linestyle=":", linewidth=1)
    axis.set(
        xscale="log",
        yscale="log",
        xlabel="Razón de runtime · N4 / baseline N3",
        ylabel="Razón de bytes · N4 / baseline N3",
        title="N3–N4: coste de recursos por régimen y tamaño",
    )
    add_sample_note(
        axis,
        "El área aumenta con N; verde indica gate individual de calidad, no gate compuesto.",
    )
    paths = save_figure(
        figure,
        figures_dir / "n3_n4_resource_tradeoff",
    )
    metrics = {
        "cells": int(len(gates)),
        "composite_passed": int(gates["gate_passed"].astype(bool).sum()),
        "bytes_gate_failed": int(
            (~gates["bytes_gate"].astype(bool)).sum()
        ),
        "median_runtime_ratio": float(gates["runtime_ratio"].median()),
        "median_bytes_ratio": float(gates["bytes_ratio"].median()),
    }
    write_json(comparison_dir / "n3_n4_metrics.json", metrics)
    write_json(
        comparison_dir / "n3_n4_manifest.json",
        {
            "schema_version": "sp1-controlled-comparison-v1",
            "scope": "N4 Geo-QPG versus the selected N3 distributed baseline",
            "source": source_record(source_path),
            "metrics": metrics,
            "artifacts": artifact_records(
                comparison_dir,
                exclude_names=(
                    "n1_n2_manifest.json",
                    "n3_n4_manifest.json",
                ),
            ),
        },
    )
    return {"figures": paths, "metrics": metrics}


def build_level(
    source_dir: Path,
    output_dir: Path,
    comparison_output_dir: Path,
) -> dict[str, object]:
    """Build N4, its ablations and the N3–N4 comparison package."""

    configure_publication_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = output_dir / "processed"
    figures_dir = output_dir / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)

    runs_path = source_dir / "runs.parquet"
    events_path = source_dir / "events.parquet"
    summary_path = source_dir / "summary.csv"
    hypotheses_path = source_dir / "hypothesis_results.csv"
    gates_path = source_dir / "success_gate_results.csv"
    metadata_path = source_dir / "method_metadata.csv"
    config_path = source_dir / "config_frozen.yaml"
    report_path = source_dir / "report.md"

    runs = pd.read_parquet(runs_path)
    events = pd.read_parquet(events_path)
    hypotheses = pd.read_csv(hypotheses_path)
    gates = pd.read_csv(gates_path)
    ensure_columns(
        runs,
        (
            "world_id",
            "family",
            "n_robots",
            "n_loads",
            "method",
            "closure_stage",
            "world_physical_feasible",
            "served_load_rate",
            "physical_welfare",
            "runtime_total_ms",
            "bytes",
            "optimality_gap_vs_certified_milp",
            "false_positive_given_committed",
            "recourse_robot_changes",
        ),
    )

    level_methods = set(QPG_METHODS) | set(COMPARISON_METHODS)
    level_runs = runs.loc[runs["method"].isin(level_methods)].copy()

    closure_paths, closure_summary = _closure_figure(
        level_runs, figures_dir
    )
    quality_paths, quality_summary = _scenario_quality_figure(
        level_runs, figures_dir
    )
    gap_paths, gap_summary = _oracle_gap_figure(level_runs, figures_dir)
    scaling_paths, scaling_summary = _resource_scaling_figure(
        level_runs, figures_dir
    )
    signal_paths, signal_summary = _signal_ablation_figure(
        level_runs, figures_dir
    )
    engine_paths, engine_summary = _engine_ablation_figure(
        level_runs, figures_dir
    )
    failure_paths, failure_summary = _failure_figure(
        level_runs, figures_dir
    )
    anytime_paths, anytime_summary = _anytime_figure(events, figures_dir)
    gate_paths = _gate_figure(gates, figures_dir)
    n3_n4 = _build_n3_n4_comparison(
        gates,
        comparison_output_dir,
        gates_path,
    )

    processed_frames = {
        "closure_summary.csv": closure_summary,
        "scenario_quality_summary.csv": quality_summary,
        "oracle_gap_summary.csv": gap_summary,
        "resource_scaling_summary.csv": scaling_summary,
        "signal_ablation_summary.csv": signal_summary,
        "engine_ablation_summary.csv": engine_summary,
        "failure_summary.csv": failure_summary,
        "anytime_summary.csv": anytime_summary,
        "hypothesis_results.csv": hypotheses,
        "composite_gates.csv": gates,
    }
    for name, frame in processed_frames.items():
        frame.to_csv(processed_dir / name, index=False)

    h2 = hypotheses.loc[hypotheses["hypothesis"] == "H2_closure_needed"].iloc[
        0
    ]
    h4 = hypotheses.loc[
        hypotheses["hypothesis"] == "H4_geo_qpg_vs_cbba_quality"
    ].iloc[0]
    h5_equivalence = hypotheses.loc[
        hypotheses["hypothesis"]
        == "H5_engine_practical_equivalence_coverage"
    ].iloc[0]
    h7 = hypotheses.loc[
        hypotheses["hypothesis"]
        == "H7_failure_recourse_qpg_minus_cbba"
    ].iloc[0]
    key_metrics = {
        "confirmatory_worlds": int(runs["world_id"].nunique()),
        "campaign_rows_all_methods": int(len(runs)),
        "n4_level_rows": int(len(level_runs)),
        "max_n": int(runs["n_robots"].max()),
        "h2_closure_effect": float(h2["effect"]),
        "h2_p_holm": float(h2["p_holm"]),
        "h4_quality_effect": float(h4["effect"]),
        "h4_gate_passed": bool(h4["gate_passed"]),
        "h5_coverage_equivalence_effect": float(h5_equivalence["effect"]),
        "h5_coverage_equivalence_passed": bool(
            h5_equivalence["gate_passed"]
        ),
        "h7_static_recourse_ratio": float(h7["recourse_ratio"]),
        "h7_static_gate_passed": bool(h7["gate_passed"]),
        "composite_cells": int(len(gates)),
        "composite_cells_passed": int(
            gates["gate_passed"].astype(bool).sum()
        ),
        "bytes_gates_failed": int(
            (~gates["bytes_gate"].astype(bool)).sum()
        ),
        "closure_states": ["RAW", "CERTIFIED", "RECOVERED"],
    }
    write_json(output_dir / "key_metrics.json", key_metrics)
    (output_dir / "REPORT.md").write_text(
        "\n".join(
            (
                "# SP1 · Nivel 4 — Geo-QPG físico y variantes",
                "",
                f"- Mundos confirmatorios: {key_metrics['confirmatory_worlds']:,}.",
                (
                    "- Filas método–mundo–cierre de la campaña completa: "
                    f"{key_metrics['campaign_rows_all_methods']:,}."
                ),
                (
                    "- H2, efecto del cierre sobre factibilidad: "
                    f"{key_metrics['h2_closure_effect']:.4f}."
                ),
                (
                    "- H4, celdas que superan el gate compuesto: "
                    f"{key_metrics['composite_cells_passed']}/"
                    f"{key_metrics['composite_cells']}."
                ),
                (
                    "- H5: equivalencia práctica de cobertura dentro de ±0.03 "
                    f"({key_metrics['h5_coverage_equivalence_passed']})."
                ),
                (
                    "- H7: ratio de recourse estático Geo-QPG/CBBA = "
                    f"{key_metrics['h7_static_recourse_ratio']:.3f}; "
                    "no valida recuperación dinámica."
                ),
                "- La propuesta no acredita superioridad global ni escalabilidad asintótica.",
                "",
            )
        ),
        encoding="utf-8",
    )
    all_paths = (
        closure_paths
        + quality_paths
        + gap_paths
        + scaling_paths
        + signal_paths
        + engine_paths
        + failure_paths
        + anytime_paths
        + gate_paths
    )
    manifest_path = write_level_manifest(
        output_dir=output_dir,
        level="N4",
        description=(
            "Proposed neighbor-estimate Geo-QPG with signal, engine and "
            "integer-closure ablations."
        ),
        sources=(
            runs_path,
            events_path,
            summary_path,
            hypotheses_path,
            gates_path,
            metadata_path,
            config_path,
            report_path,
        ),
        row_counts={
            "campaign_rows": len(runs),
            "level_rows": len(level_runs),
            "events": len(events),
            "closure_summary": len(closure_summary),
            "scenario_quality_summary": len(quality_summary),
            "oracle_gap_summary": len(gap_summary),
            "resource_scaling_summary": len(scaling_summary),
            "signal_ablation_summary": len(signal_summary),
            "engine_ablation_summary": len(engine_summary),
            "failure_summary": len(failure_summary),
            "anytime_summary": len(anytime_summary),
            "composite_gate_cells": len(gates),
        },
        claims=(
            "The common closure materially improves physical feasibility (H2).",
            "Coverage is practically equivalent across the tested QPG/Pair-GRAPE engines (H5 endpoint).",
            "No family-size cell passes the complete H4 success gate.",
        ),
        limitations=(
            "No global superiority, asymptotic scalability or physical transport claim is supported.",
            "F5 is a static post-failure proxy, not dynamic recourse.",
            "Communication bytes fail the predeclared resource gate in all 15 H4 cells.",
        ),
    )
    return {
        "manifest": manifest_path,
        "figures": all_paths,
        "comparison": n3_n4,
        "key_metrics": key_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the SP1 N4 Geo-QPG package."
    )
    parser.add_argument("--source-dir", type=Path, default=GEO_SOURCE_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=LEVELS_OUTPUT_ROOT / "n4",
    )
    parser.add_argument(
        "--comparison-output-dir",
        type=Path,
        default=LEVELS_OUTPUT_ROOT / "comparison",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    package = build_level(
        args.source_dir,
        args.output_dir,
        args.comparison_output_dir,
    )
    print(f"N4 package: {package['manifest'].resolve()}")


if __name__ == "__main__":
    main()
