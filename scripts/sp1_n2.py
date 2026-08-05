"""SP1 level N2: centralized heterogeneous-capacity MILP oracle."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sp1_levels_common import (
    COLORS,
    LEVELS_OUTPUT_ROOT,
    REPOSITORY_ROOT,
    add_sample_note,
    artifact_records,
    bool_to_float,
    configure_publication_style,
    ensure_columns,
    fit_power_law,
    label_panels,
    line_with_band,
    quantile_summary,
    save_figure,
    source_record,
    write_json,
    write_level_manifest,
)


DEFAULT_SOURCE = (
    REPOSITORY_ROOT
    / "scripts"
    / "results"
    / "sp1_a2_milp_revised"
    / "milp_results"
)
DEFAULT_COMPARISON_SOURCE = (
    REPOSITORY_ROOT
    / "scripts"
    / "results"
    / "sp1_a2_milp_revised"
    / "comparison"
)


def _build_capacity_figure(
    runs: pd.DataFrame,
    figures_dir: Path,
) -> list[Path]:
    capacity = runs.loc[
        (runs["treatment"] == "none")
        & runs["study"].isin(("capacity", "scaling", "balance"))
    ].copy()
    capacity["milp_feasible_float"] = bool_to_float(
        capacity["milp_feasible"]
    )
    capacity["milp_optimal_float"] = bool_to_float(capacity["milp_optimal"])
    capacity_summary = quantile_summary(
        capacity,
        groups=("capacity_mode",),
        metrics=(
            "milp_feasible_float",
            "milp_optimal_float",
            "milp_total_excess_kg",
            "milp_assigned_robot_count",
        ),
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    categories = list(capacity_summary["capacity_mode"])
    x_values = np.arange(len(categories))
    width = 0.34
    axes[0].bar(
        x_values - width / 2,
        capacity_summary["milp_feasible_float_mean"],
        width,
        color=COLORS["green"],
        label="Factible",
    )
    axes[0].bar(
        x_values + width / 2,
        capacity_summary["milp_optimal_float_mean"],
        width,
        color=COLORS["blue"],
        label="Óptimo certificado",
    )
    axes[0].set_xticks(
        x_values,
        [value.replace("_", " ") for value in categories],
        rotation=18,
    )
    axes[0].set(
        ylabel="Fracción de ejecuciones",
        ylim=(0.0, 1.04),
        title="Factibilidad y certificación por heterogeneidad",
    )
    axes[0].legend(loc="upper right")

    valid = capacity.dropna(
        subset=("capacity_cv", "milp_total_excess_kg")
    )
    axes[1].scatter(
        valid["capacity_cv"],
        valid["milp_total_excess_kg"],
        c=valid["milp_assigned_robot_count"],
        cmap="viridis",
        s=20,
        alpha=0.34,
        edgecolors="none",
    )
    if len(valid) >= 3:
        coefficients = np.polyfit(
            valid["capacity_cv"],
            valid["milp_total_excess_kg"],
            1,
        )
        x_fit = np.linspace(
            valid["capacity_cv"].min(),
            valid["capacity_cv"].max(),
            100,
        )
        axes[1].plot(
            x_fit,
            np.polyval(coefficients, x_fit),
            color=COLORS["orange"],
            linestyle="--",
            label="Tendencia lineal descriptiva",
        )
    axes[1].set(
        xlabel=r"Heterogeneidad de capacidad, CV$(c_i^{pay})$",
        ylabel="Exceso de capacidad reclutada [kg]",
        title="Efecto de capacidades indivisibles",
    )
    axes[1].legend(loc="upper left")
    add_sample_note(
        axes[1],
        "El color codifica robots reclutados; la recta no implica causalidad.",
    )
    label_panels(axes)
    paths = save_figure(figure, figures_dir / "n2_capacity")
    return paths, capacity_summary


def _build_saturation_figure(
    saturation: pd.DataFrame,
    figures_dir: Path,
) -> tuple[list[Path], pd.DataFrame, object]:
    saturation = saturation.copy()
    saturation["optimal_float"] = bool_to_float(
        saturation["optimal_certified"]
    )
    saturation["censored_float"] = bool_to_float(saturation["censored"])
    core = saturation.loc[
        saturation["arm"].isin(("fixed_demand", "joint_growth"))
    ].copy()
    summary = quantile_summary(
        core,
        groups=("arm", "N", "K"),
        metrics=(
            "observed_time_seconds",
            "optimal_float",
            "censored_float",
            "binary_variable_count",
            "explicit_model_bytes",
        ),
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    arms = (
        ("fixed_demand", "K fijo", COLORS["blue"]),
        ("joint_growth", "N y K crecen", COLORS["orange"]),
    )
    for arm, label, color in arms:
        block = summary.loc[summary["arm"] == arm]
        line_with_band(
            axes[0],
            block,
            x="N",
            median="observed_time_seconds_median",
            low="observed_time_seconds_p05",
            high="observed_time_seconds_p95",
            color=color,
            label=label,
        )
        axes[1].plot(
            block["N"],
            block["optimal_float_mean"],
            marker="o",
            color=color,
            label=label,
        )
    axes[0].axhline(
        5.0,
        color=COLORS["red"],
        linestyle=":",
        linewidth=1.2,
        label="Timeout nominal · 5 s",
    )
    axes[0].set(
        xscale="log",
        yscale="log",
        xlabel="Robots, $N$",
        ylabel="Tiempo observado [s]",
        title="Tiempo censurado por timeout",
    )
    axes[0].legend(loc="lower right")
    axes[1].set(
        xscale="log",
        xlabel="Robots, $N$",
        ylabel="Fracción con óptimo certificado",
        ylim=(-0.03, 1.03),
        title="La meseta temporal no es saturación algorítmica",
    )
    axes[1].legend(loc="upper right")
    add_sample_note(
        axes[1],
        "Cuando expira el límite, la duración se pega al timeout y cae la certificación.",
    )
    label_panels(axes)
    paths = save_figure(figure, figures_dir / "n2_saturation_audit")

    model_fit = fit_power_law(
        summary["N"],
        summary["binary_variable_count_median"],
    )
    return paths, summary, model_fit


def _build_controlled_comparison(
    comparison: pd.DataFrame,
    comparison_dir: Path,
    source_path: Path,
) -> dict[str, object]:
    figures_dir = comparison_dir / "figures"
    processed_dir = comparison_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    comparison = comparison.copy()
    ensure_columns(
        comparison,
        (
            "same_capacity_model",
            "both_feasible",
            "N",
            "milp_to_hungarian_distance_ratio",
            "milp_to_hungarian_solver_ratio",
            "milp_minus_hungarian_assigned_robots",
        ),
    )
    controlled = comparison.loc[
        comparison["same_capacity_model"].astype(bool)
        & comparison["both_feasible"].astype(bool)
    ].copy()
    summary = quantile_summary(
        controlled,
        groups=("N",),
        metrics=(
            "milp_to_hungarian_distance_ratio",
            "milp_to_hungarian_solver_ratio",
            "milp_minus_hungarian_assigned_robots",
        ),
    )
    summary.to_csv(
        processed_dir / "n1_n2_homogeneous_summary.csv",
        index=False,
    )

    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.15))
    line_with_band(
        axes[0],
        summary,
        x="N",
        median="milp_to_hungarian_distance_ratio_median",
        low="milp_to_hungarian_distance_ratio_p05",
        high="milp_to_hungarian_distance_ratio_p95",
        color=COLORS["green"],
        label="MILP / húngaro",
    )
    axes[0].axhline(1.0, color=COLORS["dark"], linestyle=":", linewidth=1)
    axes[0].set(
        xlabel="Robots, $N$",
        ylabel="Razón de distancia",
        title="Paridad de solución en el caso común",
    )
    axes[0].legend(loc="upper right")

    line_with_band(
        axes[1],
        summary,
        x="N",
        median="milp_to_hungarian_solver_ratio_median",
        low="milp_to_hungarian_solver_ratio_p05",
        high="milp_to_hungarian_solver_ratio_p95",
        color=COLORS["orange"],
        label="MILP / húngaro",
    )
    axes[1].axhline(1.0, color=COLORS["dark"], linestyle=":", linewidth=1)
    axes[1].set(
        xlabel="Robots, $N$",
        ylabel="Razón de tiempo del solver",
        yscale="log",
        title="Coste de usar el modelo general",
    )
    axes[1].legend(loc="upper left")
    add_sample_note(
        axes[0],
        f"Solo pares homogéneos y factibles; n={len(controlled)}.",
    )
    label_panels(axes)
    paths = save_figure(
        figure,
        figures_dir / "n1_n2_homogeneous_comparison",
    )
    metrics = {
        "controlled_rows": int(len(controlled)),
        "median_distance_ratio": float(
            controlled["milp_to_hungarian_distance_ratio"].median()
        ),
        "median_solver_ratio": float(
            controlled["milp_to_hungarian_solver_ratio"].median()
        ),
    }
    write_json(comparison_dir / "n1_n2_metrics.json", metrics)
    write_json(
        comparison_dir / "n1_n2_manifest.json",
        {
            "schema_version": "sp1-controlled-comparison-v1",
            "scope": "N1 versus N2 under the same homogeneous slot problem",
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
    comparison_source_dir: Path,
    output_dir: Path,
    comparison_output_dir: Path,
) -> dict[str, object]:
    """Build N2 and its strictly homogeneous N1 comparison."""

    configure_publication_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir = output_dir / "processed"
    figures_dir = output_dir / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)

    runs_path = source_dir / "mc_all_runs.csv"
    saturation_path = (
        source_dir / "saturation_audit" / "saturation_runs.csv"
    )
    config_path = source_dir / "config.json"
    comparison_path = comparison_source_dir / "mc_all_runs.csv"

    runs = pd.read_csv(runs_path)
    saturation = pd.read_csv(saturation_path)
    comparison = pd.read_csv(comparison_path)
    ensure_columns(
        runs,
        (
            "study",
            "N",
            "capacity_mode",
            "capacity_cv",
            "milp_feasible",
            "milp_optimal",
            "milp_total_excess_kg",
            "milp_assigned_robot_count",
            "treatment",
        ),
    )

    capacity_paths, capacity_summary = _build_capacity_figure(
        runs, figures_dir
    )
    capacity_summary.to_csv(
        processed_dir / "capacity_summary.csv", index=False
    )
    saturation_paths, saturation_summary, model_fit = (
        _build_saturation_figure(saturation, figures_dir)
    )
    saturation_summary.to_csv(
        processed_dir / "saturation_summary.csv", index=False
    )
    controlled = _build_controlled_comparison(
        comparison,
        comparison_output_dir,
        comparison_path,
    )

    key_metrics = {
        "raw_rows": int(len(runs)),
        "saturation_rows": int(len(saturation)),
        "saturation_censored": int(
            bool_to_float(saturation["censored"]).sum()
        ),
        "saturation_optimal_certified": int(
            bool_to_float(saturation["optimal_certified"]).sum()
        ),
        "saturation_max_n": int(saturation["N"].max()),
        "saturation_max_k": int(saturation["K"].max()),
        "binary_variable_growth_exponent": model_fit.exponent,
        "binary_variable_growth_r_squared": model_fit.r_squared,
        "solver": "SciPy milp / HiGHS",
        "architecture": "centralized_global_information",
    }
    write_json(output_dir / "key_metrics.json", key_metrics)
    (output_dir / "REPORT.md").write_text(
        "\n".join(
            (
                "# SP1 · Nivel 2 — MILP heterogéneo centralizado",
                "",
                f"- Filas de campaña MILP: {len(runs):,}.",
                f"- Casos de auditoría temporal: {len(saturation):,}.",
                (
                    "- Censurados por timeout: "
                    f"{key_metrics['saturation_censored']:,}; óptimos certificados: "
                    f"{key_metrics['saturation_optimal_certified']:,}."
                ),
                (
                    "- Escala auditada: hasta "
                    f"N={saturation['N'].max():,}, K={saturation['K'].max():,}."
                ),
                "- Solver: scipy.optimize.milp con HiGHS; arquitectura centralizada.",
                "- Una meseta cerca del timeout no prueba coste constante ni N infinito.",
                "- La comparación N1–N2 usa únicamente mundos homogéneos equivalentes.",
                "",
            )
        ),
        encoding="utf-8",
    )
    manifest_path = write_level_manifest(
        output_dir=output_dir,
        level="N2",
        description=(
            "Centralized heterogeneous payload-capacity MILP oracle with a "
            "censoring-aware scalability audit."
        ),
        sources=(runs_path, saturation_path, config_path),
        row_counts={
            "raw_runs": len(runs),
            "saturation_runs": len(saturation),
            "capacity_summary": len(capacity_summary),
            "saturation_summary": len(saturation_summary),
        },
        claims=(
            "A successful status-0 run is a global MILP optimum for the encoded model.",
            "Timeout incumbents are feasible candidates, not certified optima.",
            "N1 and N2 are compared only under the shared homogeneous problem.",
        ),
        limitations=(
            "The oracle uses global information and is not an architectural peer of distributed methods.",
            "The runtime plateau is induced by the time limit and cannot support fixed-cost or infinite-N claims.",
        ),
    )
    return {
        "manifest": manifest_path,
        "figures": capacity_paths + saturation_paths,
        "comparison": controlled,
        "key_metrics": key_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the SP1 N2 heterogeneous MILP package."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--comparison-source-dir",
        type=Path,
        default=DEFAULT_COMPARISON_SOURCE,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=LEVELS_OUTPUT_ROOT / "n2",
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
        args.comparison_source_dir,
        args.output_dir,
        args.comparison_output_dir,
    )
    print(f"N2 package: {package['manifest'].resolve()}")


if __name__ == "__main__":
    main()
