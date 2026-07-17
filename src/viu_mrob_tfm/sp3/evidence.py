"""Audit and regenerate manuscript artifacts for the SP3 wrench campaign."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt


METHOD_LABELS = {
    "wrench_oracle": "Oráculo de wrench",
    "nash_pd_exact_guarded": "PD exacto + guardia",
    "nash_pd_ring_guarded": "PD anillo + guardia",
    "smith_wrench_pairs_guarded": "Smith pareado + guardia",
    "nash_pd_exact_unguarded": "PD exacto sin guardia",
    "cbba_slots": "CBBA por puestos",
    "oracle_scalar_assignment": "Referencia escalar",
}

FIGURE_METHODS = [
    "wrench_oracle",
    "replicator_price_guarded",
    "erv_bnn_price_guarded",
    "smith_price_guarded",
    "smith_wrench_pairs_guarded",
    "nash_pd_ring_guarded",
    "nash_pd_exact_guarded",
    "uniform_guarded",
    "nash_pd_exact_unguarded",
    "cbba_slots",
    "wrench_greedy",
    "oracle_scalar_assignment",
]

FIGURE_LABELS = {
    "wrench_oracle": "Oráculo de wrench",
    "replicator_price_guarded": "Replicator + precio + guardia",
    "erv_bnn_price_guarded": "ERV--BNN + precio + guardia",
    "smith_price_guarded": "Smith + precio + guardia",
    "smith_wrench_pairs_guarded": "Smith pareado + guardia",
    "nash_pd_ring_guarded": "PD anillo + guardia",
    "nash_pd_exact_guarded": "PD exacto + guardia",
    "uniform_guarded": "Uniforme + guardia",
    "nash_pd_exact_unguarded": "PD exacto sin guardia",
    "cbba_slots": "CBBA por puestos",
    "wrench_greedy": "Voraz de wrench",
    "oracle_scalar_assignment": "Referencia escalar",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _latex_probability(value: float) -> str:
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0**exponent
    return f"{mantissa:.2f}\\times10^{{{exponent}}}"


def _finite_or_dash(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}" if np.isfinite(value) else "--"


def _format_table(summary: pd.DataFrame, abstention: pd.Series) -> str:
    rows: list[str] = []
    for method, label in METHOD_LABELS.items():
        row = summary.loc[method]
        rows.append(
            f"{label} & {row.precision_given_assigned_mean:.3f} & "
            f"{row.feasible_coverage_mean:.3f} & "
            f"{abstention.loc[method]:.3f} & "
            f"{row.fp_given_assigned_mean:.3f} & "
            f"{row.optimality_gap_vs_wrench_oracle_mean:.4f} & "
            f"{_finite_or_dash(float(row.kkt_residual_mean))} & "
            f"{1000.0 * row.runtime_s_mean:.1f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrrrr}\n\\toprule\n"
        "Método & Precisión & Cobertura & Abstención & Falsos positivos & Brecha wrench & Residual KKT & CPU [ms] \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _format_macros(
    summary: pd.DataFrame,
    hypotheses: pd.DataFrame,
    abstention: pd.Series,
    worlds: int,
    runs: int,
) -> str:
    guarded = summary.loc["nash_pd_exact_guarded"]
    unguarded = summary.loc["nash_pd_exact_unguarded"]
    scalar = summary.loc["oracle_scalar_assignment"]
    pair = summary.loc["smith_wrench_pairs_guarded"]
    cbba = summary.loc["cbba_slots"]
    ring = summary.loc["nash_pd_ring_guarded"]
    contrast_guard = hypotheses.loc["H-SP3-1-guard-reduces-fp"]
    contrast_vector = hypotheses.loc["H-SP3-2-vector-beats-scalar-gap"]
    contrast_pair = hypotheses.loc["H-SP3-3-pair-beats-cbba-gap"]
    contrast_graph = hypotheses.loc["H-SP3-4-exact-beats-ring-kkt"]
    macros = {
        "SPThreeWorlds": str(worlds),
        "SPThreeRuns": str(runs),
        "SPThreeGuardedPrecision": f"{guarded.precision_given_assigned_mean:.3f}",
        "SPThreeGuardedCoverage": f"{guarded.feasible_coverage_mean:.3f}",
        "SPThreeGuardedAbstention": f"{abstention.loc['nash_pd_exact_guarded']:.3f}",
        "SPThreeGuardedFP": f"{guarded.fp_given_assigned_mean:.3f}",
        "SPThreeUnguardedFP": f"{unguarded.fp_given_assigned_mean:.3f}",
        "SPThreeGuardEffect": f"{contrast_guard.effect_mean:.3f}",
        "SPThreeGuardCILow": f"{contrast_guard.ci95_low:.3f}",
        "SPThreeGuardCIHigh": f"{contrast_guard.ci95_high:.3f}",
        "SPThreeGuardPHolm": _latex_probability(float(contrast_guard.p_holm)),
        "SPThreeGuardedGap": f"{guarded.optimality_gap_vs_wrench_oracle_mean:.5f}",
        "SPThreeScalarGap": f"{scalar.optimality_gap_vs_wrench_oracle_mean:.5f}",
        "SPThreeVectorEffect": f"{contrast_vector.effect_mean:.5f}",
        "SPThreeVectorCILow": f"{contrast_vector.ci95_low:.5f}",
        "SPThreeVectorCIHigh": f"{contrast_vector.ci95_high:.5f}",
        "SPThreePairGap": f"{pair.optimality_gap_vs_wrench_oracle_mean:.5f}",
        "SPThreeCBBAGap": f"{cbba.optimality_gap_vs_wrench_oracle_mean:.5f}",
        "SPThreePairEffect": f"{contrast_pair.effect_mean:.5f}",
        "SPThreeExactKKT": f"{guarded.kkt_residual_mean:.5f}",
        "SPThreeRingKKT": f"{ring.kkt_residual_mean:.5f}",
        "SPThreeGraphEffect": f"{contrast_graph.effect_mean:.5f}",
        "SPThreeGraphCILow": f"{contrast_graph.ci95_low:.5f}",
        "SPThreeGraphCIHigh": f"{contrast_graph.ci95_high:.5f}",
    }
    return "\n".join(
        f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items()
    ) + "\n"


def _plot_performance(summary: pd.DataFrame, path: Path) -> None:
    """Render the manuscript SP3 comparison as a legible vector figure."""
    frame = summary.loc[FIGURE_METHODS]
    labels = [FIGURE_LABELS[method] for method in FIGURE_METHODS]
    positions = np.arange(len(frame))
    figure, axes = plt.subplots(1, 2, figsize=(7.2, 5.5), sharey=True)
    axes[0].barh(
        positions,
        frame["optimality_gap_vs_wrench_oracle_mean"],
        color="#0B78B5",
    )
    axes[1].barh(
        positions,
        frame["fp_given_assigned_mean"],
        color="#E56A00",
    )
    axes[0].set_yticks(positions, labels=labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Brecha frente al oráculo (↓)")
    axes[1].set_xlabel("Falsos positivos condicionados (↓)")
    axes[1].tick_params(axis="y", labelleft=False)
    for axis in axes:
        axis.grid(axis="x", alpha=0.25)
        axis.tick_params(labelsize=9)
    figure.tight_layout(w_pad=0.8)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)


def execute(config_path: Path) -> Path:
    config = _load_yaml(config_path)
    source = Path(config["source_dir"])
    output = Path(config["output_dir"])
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(source / "manifest.json")
    theory = _load_json(source / "theory_audit.json")
    expected = config["expected"]
    checks = {
        "experiment_id": manifest["experiment_id"] == expected["experiment_id"],
        "worlds": int(manifest["worlds"]) == int(expected["worlds"]),
        "runs": int(manifest["runs"]) == int(expected["runs"]),
        "theory_passed": bool(theory["passed"]),
        "simplex": float(theory["max_simplex_error"]) <= float(expected["max_simplex_error"]),
        "guard": int(theory["guarded_false_positive_violations"]) == 0,
        "raw_closed_distinct": int(theory["raw_closed_distinct_runs"]) > 0,
    }
    if not all(checks.values()):
        raise AssertionError(f"SP3 evidence audit failed: {checks}")

    summary = pd.read_csv(source / "tables" / "summary.csv").set_index("method")
    runs_table = pd.read_csv(source / "tables" / "runs.csv")
    abstention = (
        runs_table.assign(abstained=runs_table["assigned_loads"].eq(0).astype(float))
        .groupby("method")["abstained"]
        .mean()
    )
    hypotheses = pd.read_csv(source / "tables" / "hypothesis_results.csv").set_index("id")
    if not set(METHOD_LABELS).issubset(summary.index):
        raise AssertionError("SP3 summary is missing manuscript methods")
    required_hypotheses = {
        "H-SP3-1-guard-reduces-fp",
        "H-SP3-2-vector-beats-scalar-gap",
        "H-SP3-3-pair-beats-cbba-gap",
        "H-SP3-4-exact-beats-ring-kkt",
    }
    if not required_hypotheses.issubset(hypotheses.index):
        raise AssertionError("SP3 hypothesis table is incomplete")
    if not bool(hypotheses.loc[list(required_hypotheses), "reject_holm_005"].all()):
        raise AssertionError("a pre-specified SP3 contrast failed Holm correction")

    (tables / "sp3_results.tex").write_text(
        _format_table(summary, abstention), encoding="utf-8"
    )
    (tables / "sp3_numbers.tex").write_text(
        _format_macros(
            summary,
            hypotheses,
            abstention,
            int(manifest["worlds"]),
            int(manifest["runs"]),
        ),
        encoding="utf-8",
    )
    figure_path = output / "figures" / "fig-sp3-wrench-performance.pdf"
    _plot_performance(summary, figure_path)
    audit = {
        "status": "passed",
        "checks": checks,
        "source_experiment": manifest["experiment_id"],
        "worlds": int(manifest["worlds"]),
        "runs": int(manifest["runs"]),
        "integer_closure_globally_optimal": False,
        "guard_fully_distributed": False,
        "cargo_rigidity_measured": False,
        "caging_measured": False,
        "vector_figure_regenerated": figure_path.is_file(),
        "historical_generator_present_in_worktree": False,
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "report.md").write_text(
        "# SP3 evidence audit\n\n"
        f"Audited {audit['worlds']} worlds and {audit['runs']} method runs from "
        f"`{audit['source_experiment']}`.\n\n"
        "The manuscript table, macros, and vector performance figure are regenerated "
        "from the campaign CSV files. "
        "The result covers the planar convex wrench relaxation and guarded closure; it "
        "does not establish Cargo rigidity, caging, integer global optimality, or a fully "
        "distributed mechanical guard.\n",
        encoding="utf-8",
    )
    artifacts = sorted(path for path in output.rglob("*") if path.is_file())
    output_manifest = {
        "experiment_id": config["experiment_id"],
        "status": "postprocess_completed_with_historical_generator_limitation",
        "config": str(config_path).replace("\\", "/"),
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): _sha256(path)
            for path in artifacts
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(output_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = ["execute"]
