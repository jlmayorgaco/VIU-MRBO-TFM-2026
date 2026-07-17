"""Audit and regenerate the SP2 manuscript artifacts from processed campaigns."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


METHOD_LABELS = {
    "oracle_reference": "Oráculo de puntuación",
    "capacity_oracle_reference": "Referencia de cobertura",
    "neural_capacity_scorer": "Puntuación neuronal",
    "imitation_capacity": "Imitación lineal",
    "greedy_capacity_nearest": "Voraz de servicio",
    "replicator_capacity": "Puntuación inspirada en replicator",
    "smith_capacity": "Puntuación inspirada en Smith",
    "smith_capacity_plain": "Puntuación plana",
    "smith_capacity_marginal": "Puntuación marginal",
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


def _all_scenarios(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    result = frame[frame["scenario_generator"] == "ALL_SCENARIOS"].copy()
    if result.empty:
        raise AssertionError(f"missing ALL_SCENARIOS rows in {path}")
    return result.set_index("method", drop=False)


def _format_main_table(frame: pd.DataFrame) -> str:
    methods = [
        "oracle_reference",
        "capacity_oracle_reference",
        "neural_capacity_scorer",
        "imitation_capacity",
        "greedy_capacity_nearest",
        "replicator_capacity",
        "smith_capacity",
    ]
    rows = []
    for method in methods:
        row = frame.loc[method]
        rows.append(
            f"{METHOD_LABELS[method]} & {row.capacity_satisfaction_ratio_mean:.3f} & "
            f"{row.capacity_success_rate_mean:.3f} & {row.optimality_gap_vs_oracle_mean:.3f} & "
            f"{row.capacity_gap_vs_capacity_oracle_mean:.3f} & {row.runtime_ms_mean:.2f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrr}\n\\toprule\n"
        "Método & Cobertura & Completitud & Brecha & Dif. cobertura & CPU [ms] \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _format_ablation_table(frame: pd.DataFrame) -> str:
    rows = []
    for method in ["smith_capacity_plain", "smith_capacity_marginal"]:
        row = frame.loc[method]
        rows.append(
            f"{METHOD_LABELS[method]} & {row.capacity_success_rate_mean:.3f} & "
            f"{row.optimality_gap_vs_oracle_mean:.3f} & {row.incomplete_capacity_ratio_mean:.3f} & "
            f"{row.served_capacity_alignment_mean:.3f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrr}\n\\toprule\n"
        "Variante & Completitud & Brecha & Serv. incompleto & Alineación \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _latex_probability(value: float) -> str:
    if value == 0.0:
        return "<10^{-300}"
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0**exponent
    return f"{mantissa:.2f}\\times10^{{{exponent}}}"


def _format_numbers(
    comparison: pd.DataFrame,
    ablation: pd.DataFrame,
    hypotheses: pd.DataFrame,
    negative: pd.Series,
) -> str:
    score = comparison.loc["oracle_reference"]
    coverage = comparison.loc["capacity_oracle_reference"]
    neural = comparison.loc["neural_capacity_scorer"]
    smith = comparison.loc["smith_capacity"]
    plain = ablation.loc["smith_capacity_plain"]
    marginal = ablation.loc["smith_capacity_marginal"]
    gap = hypotheses.loc["H_SP2_Marginal_smith_lower_score_gap"]
    success = hypotheses.loc["H_SP2_Marginal_smith_higher_success"]
    incomplete = hypotheses.loc[
        "H_SP2_Potential_marginal_lower_incomplete_capacity_smith"
    ]
    alignment = hypotheses.loc[
        "H_SP2_Potential_marginal_higher_alignment_smith"
    ]
    macros = {
        "SPTwoWorlds": "1560",
        "SPTwoComparisonRows": "20280",
        "SPTwoAblationRows": "9360",
        "SPTwoScoreCoverage": f"{score.capacity_satisfaction_ratio_mean:.3f}",
        "SPTwoScoreSuccess": f"{score.capacity_success_rate_mean:.3f}",
        "SPTwoScoreRuntime": f"{score.runtime_ms_mean:.2f}",
        "SPTwoCoverageCoverage": f"{coverage.capacity_satisfaction_ratio_mean:.3f}",
        "SPTwoCoverageSuccess": f"{coverage.capacity_success_rate_mean:.3f}",
        "SPTwoCoverageRuntime": f"{coverage.runtime_ms_mean:.2f}",
        "SPTwoNeuralGap": f"{neural.optimality_gap_vs_oracle_mean:.3f}",
        "SPTwoNeuralSuccess": f"{neural.capacity_success_rate_mean:.3f}",
        "SPTwoNeuralRuntime": f"{neural.runtime_ms_mean:.2f}",
        "SPTwoNeuralParameters": str(int(neural.method_trainable_parameters)),
        "SPTwoSmithGap": f"{smith.optimality_gap_vs_oracle_mean:.3f}",
        "SPTwoSmithSuccess": f"{smith.capacity_success_rate_mean:.3f}",
        "SPTwoSmithRuntime": f"{smith.runtime_ms_mean:.2f}",
        "SPTwoPlainSuccess": f"{plain.capacity_success_rate_mean:.3f}",
        "SPTwoMarginalSuccess": f"{marginal.capacity_success_rate_mean:.3f}",
        "SPTwoPlainGap": f"{plain.optimality_gap_vs_oracle_mean:.3f}",
        "SPTwoMarginalGap": f"{marginal.optimality_gap_vs_oracle_mean:.3f}",
        "SPTwoPlainIncomplete": f"{plain.incomplete_capacity_ratio_mean:.3f}",
        "SPTwoMarginalIncomplete": f"{marginal.incomplete_capacity_ratio_mean:.3f}",
        "SPTwoPlainAlignment": f"{plain.served_capacity_alignment_mean:.3f}",
        "SPTwoMarginalAlignment": f"{marginal.served_capacity_alignment_mean:.3f}",
        "SPTwoGapEffect": f"{gap.effect:.4f}",
        "SPTwoGapCILow": f"{gap.ci95_low:.4f}",
        "SPTwoGapCIHigh": f"{gap.ci95_high:.4f}",
        "SPTwoGapPHolm": _latex_probability(float(gap.p_value_holm)),
        "SPTwoSuccessEffect": f"{success.effect:.4f}",
        "SPTwoSuccessCILow": f"{success.ci95_low:.4f}",
        "SPTwoSuccessCIHigh": f"{success.ci95_high:.4f}",
        "SPTwoIncompleteEffect": f"{incomplete.effect:.4f}",
        "SPTwoAlignmentEffect": f"{alignment.effect:.4f}",
        "SPTwoPDEffect": f"{negative.effect:.3f}",
        "SPTwoPDCILow": f"{negative.ci95_low:.3f}",
        "SPTwoPDCIHigh": f"{negative.ci95_high:.3f}",
        "SPTwoPDPHolm": f"{negative.p_value_holm:.0f}",
    }
    return "\n".join(
        f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items()
    ) + "\n"


def _make_figure(comparison: pd.DataFrame, ablation: pd.DataFrame, output: Path) -> None:
    selected = [
        "oracle_reference",
        "capacity_oracle_reference",
        "neural_capacity_scorer",
        "imitation_capacity",
        "greedy_capacity_nearest",
        "replicator_capacity",
        "smith_capacity",
    ]
    colors = {
        "oracle_reference": "#23395B",
        "capacity_oracle_reference": "#6C757D",
        "neural_capacity_scorer": "#8C6BB1",
        "imitation_capacity": "#4C78A8",
        "greedy_capacity_nearest": "#F28E2B",
        "replicator_capacity": "#59A14F",
        "smith_capacity": "#2A9D8F",
    }
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.15), constrained_layout=True)
    for method in selected:
        row = comparison.loc[method]
        axes[0].scatter(
            row.capacity_satisfaction_ratio_mean,
            row.capacity_success_rate_mean,
            s=58,
            color=colors[method],
            label=METHOD_LABELS[method],
            zorder=3,
        )
        axes[1].scatter(
            row.runtime_ms_mean,
            row.optimality_gap_vs_oracle_mean,
            s=58,
            color=colors[method],
            zorder=3,
        )
    axes[0].set_title("(a) Cobertura no implica completitud")
    axes[0].set_xlabel("Cobertura efectiva")
    axes[0].set_ylabel("Proporción de cargas completas")
    axes[1].set_title("(b) Calidad frente a coste")
    axes[1].set_xlabel("CPU media [ms, escala log]")
    axes[1].set_ylabel("Brecha respecto al oráculo")
    axes[1].set_xscale("log")
    metrics = [
        ("capacity_success_rate_mean", "Completitud"),
        ("optimality_gap_vs_oracle_mean", "Brecha"),
        ("incomplete_capacity_ratio_mean", "Servicio incompleto"),
    ]
    plain = ablation.loc["smith_capacity_plain"]
    marginal = ablation.loc["smith_capacity_marginal"]
    locations = np.arange(len(metrics))
    width = 0.36
    axes[2].bar(
        locations - width / 2,
        [plain[column] for column, _ in metrics],
        width,
        label="Plano",
        color="#BB5566",
    )
    axes[2].bar(
        locations + width / 2,
        [marginal[column] for column, _ in metrics],
        width,
        label="Marginal",
        color="#2A9D8F",
    )
    axes[2].set_xticks(locations, [label for _, label in metrics], rotation=15)
    axes[2].set_title("(c) Ablación de la puntuación")
    axes[2].set_ylabel("Razón o brecha")
    axes[2].legend(frameon=False)
    for axis in axes:
        axis.grid(alpha=0.22, zorder=0)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, frameon=False)
    output.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        fig.savefig(output / f"fig-sp2-effective-capacity.{extension}", dpi=240)
    plt.close(fig)


def execute(config_path: Path) -> Path:
    config = _load_yaml(config_path)
    comparison_dir = Path(config["comparison_dir"])
    ablation_dir = Path(config["ablation_dir"])
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    expected = config["expected"]
    comparison_manifest = _load_json(comparison_dir / "manifest.json")
    ablation_manifest = _load_json(ablation_dir / "manifest.json")
    comparison_audit = _load_json(comparison_dir / "theory_audit.json")
    ablation_audit = _load_json(ablation_dir / "theory_audit.json")
    checks = {
        "comparison_seeds": comparison_manifest["seeds"] == list(
            range(int(expected["seed_start"]), int(expected["seed_end"]) + 1)
        ),
        "ablation_seeds": ablation_manifest["seeds"] == comparison_manifest["seeds"],
        "comparison_generators": comparison_manifest["scenario_generators"]
        == expected["scenario_generators"],
        "ablation_generators": ablation_manifest["scenario_generators"]
        == expected["scenario_generators"],
        "comparison_rows": int(comparison_manifest["runs"])
        == int(expected["comparison_rows"]),
        "ablation_rows": int(ablation_manifest["runs"])
        == int(expected["ablation_rows"]),
        "comparison_audit": int(comparison_audit["checks"])
        == int(expected["comparison_rows"])
        and int(comparison_audit["failed_checks"]) == 0,
        "ablation_audit": int(ablation_audit["checks"])
        == int(expected["ablation_rows"])
        and int(ablation_audit["failed_checks"]) == 0,
        "comparison_videos": len(comparison_manifest["scenario_videos"])
        == int(expected["comparison_videos"]),
        "ablation_videos": len(ablation_manifest["scenario_videos"])
        == int(expected["ablation_videos"]),
    }
    if not all(checks.values()):
        raise AssertionError(f"SP2 evidence audit failed: {checks}")
    comparison = _all_scenarios(comparison_dir / "tables" / "performance_ranking.csv")
    ablation = _all_scenarios(ablation_dir / "tables" / "performance_ranking.csv")
    required_comparison = set(METHOD_LABELS) - {
        "smith_capacity_plain",
        "smith_capacity_marginal",
    }
    if not required_comparison.issubset(comparison.index):
        raise AssertionError("comparison ranking is missing manuscript methods")
    if not {"smith_capacity_plain", "smith_capacity_marginal"}.issubset(ablation.index):
        raise AssertionError("ablation ranking is missing plain/marginal variants")
    hypotheses = pd.read_csv(ablation_dir / "tables" / "hypothesis_results.csv").set_index("id")
    required_hypotheses = {
        "H_SP2_Marginal_smith_lower_score_gap",
        "H_SP2_Marginal_smith_higher_success",
        "H_SP2_Potential_marginal_lower_incomplete_capacity_smith",
        "H_SP2_Potential_marginal_higher_alignment_smith",
    }
    if not required_hypotheses.issubset(hypotheses.index):
        raise AssertionError("missing marginal-payoff hypotheses")
    if not bool(hypotheses.loc[list(required_hypotheses), "reject_holm"].all()):
        raise AssertionError("a declared marginal-payoff contrast did not pass Holm correction")
    negative = pd.read_csv(
        comparison_dir / "tables" / "hypothesis_results.csv"
    ).set_index("id").loc["H02_primal_dual_higher_capacity_success_than_greedy"]
    if bool(negative["reject_holm"]) or float(negative["effect"]) >= 0.0:
        raise AssertionError("the preregistered primal-dual negative result changed")
    (tables / "sp2_comparison.tex").write_text(
        _format_main_table(comparison), encoding="utf-8"
    )
    (tables / "sp2_ablation.tex").write_text(
        _format_ablation_table(ablation), encoding="utf-8"
    )
    (tables / "sp2_numbers.tex").write_text(
        _format_numbers(comparison, ablation, hypotheses, negative),
        encoding="utf-8",
    )
    _make_figure(comparison, ablation, figures)
    audit = {
        "status": "passed",
        "checks": checks,
        "comparison_rows": int(comparison_manifest["runs"]),
        "ablation_rows": int(ablation_manifest["runs"]),
        "seeds": comparison_manifest["seeds"],
        "scenario_generators": comparison_manifest["scenario_generators"],
        "comparison_method_outputs": int(len(comparison)),
        "comparison_manifest_methods": int(len(comparison_manifest["methods"])),
        "comparison_videos": len(comparison_manifest["scenario_videos"]),
        "ablation_videos": len(ablation_manifest["scenario_videos"]),
        "compatibility_used_in_campaign": False,
        "historical_generator_present_in_worktree": False,
        "smith_ode_integrated_in_campaign": False,
        "interpretation": "paired score-rule ablation; not a convergence test of Smith dynamics",
        "negative_primal_dual_effect": float(negative["effect"]),
        "negative_primal_dual_p_holm": float(negative["p_value_holm"]),
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    report = [
        "# SP2 evidence audit",
        "",
        f"Comparison: {audit['comparison_rows']} paired method rows; ablation: {audit['ablation_rows']} rows.",
        f"Seeds: {audit['seeds'][0]}--{audit['seeds'][-1]}; generators: {', '.join(audit['scenario_generators'])}.",
        f"Videos catalogued: {audit['comparison_videos']} comparison + {audit['ablation_videos']} ablation.",
        "",
        "All recorded run-level audits passed. The postprocessing is reproducible, but the historical campaign generator is absent from the current worktree.",
        "The methods labelled Smith in the inherited campaign use sequential scoring and do not integrate the Smith ODE; the ablation therefore supports the marginal score rule, not a convergence claim.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    artifacts = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "experiment_id": config["experiment_id"],
        "status": "postprocess_completed_with_historical_generator_limitation",
        "config": str(config_path).replace("\\", "/"),
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): _sha256(path)
            for path in artifacts
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output


__all__ = ["execute"]
