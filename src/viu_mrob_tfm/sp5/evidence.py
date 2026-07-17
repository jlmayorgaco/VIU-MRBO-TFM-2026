"""Audit and regenerate manuscript artifacts for canonical SP5-C evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


METHODS = {
    "pose_pd_raw": "PD de pose sin filtro",
    "apf_wrench_heuristic": "Campo potencial",
    "velocity_obstacle_proxy": "Aproximación VO",
    "cbf_wrench_local": "CBF local",
    "damped_hamiltonian_raw": "Hamiltoniano sin filtro",
    "damped_hamiltonian_cbf": "Hamiltoniano + CBF",
    "distributed_preview_cbf": "CBF anticipativo local",
    "centralized_preview_reference": "Previsión central",
}

SCENARIOS = (
    "open_nominal",
    "static_corridor",
    "mobile_crossing",
    "mixed_corridor",
    "actuator_limited",
    "multi_load_clutter",
)

SCENARIO_LABELS = {
    "open_nominal": "abierto nominal",
    "static_corridor": "corredor estático",
    "mobile_crossing": "cruce móvil",
    "mixed_corridor": "corredor mixto",
    "actuator_limited": "actuadores limitados",
    "multi_load_clutter": "múltiples cargas",
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
    if value == 0.0:
        return "0"
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0**exponent
    return f"{mantissa:.2f}\\times10^{{{exponent}}}"


def _results_table(summary: pd.DataFrame) -> str:
    indexed = summary.set_index("method")
    rows: list[str] = []
    for method, label in METHODS.items():
        row = indexed.loc[method]
        rows.append(
            f"{label} & {int(row['n'])} & {row['safe_transport_success']:.3f} & "
            f"{row['any_collision']:.3f} & {row['timeout']:.3f} & "
            f"{row['min_clearance_m']:.3f} & {row['exec_barrier_violation_rate']:.3f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
        "Método & $n$ & Éxito seguro & Colisión & Horizonte agotado & "
        "Holgura [m] & Violación aplicada \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _hypotheses_table(hypotheses: pd.DataFrame) -> str:
    labels = {
        "H5_1_hamiltonian_cbf_reduces_collision_vs_raw": "CBF reduce colisión vs. RAW",
        "H5_2_hamiltonian_cbf_improves_safe_success_vs_raw": "CBF mejora éxito vs. RAW",
        "H5_3_central_preview_improves_safe_success_vs_local_cbf": "Previsión central mejora CBF local",
        "H5_4_local_cbf_reduces_exec_barrier_violation_vs_apf": "CBF local reduce violación vs. APF",
        "H5_5_preview_cbf_reduces_collision_vs_vo_proxy": "CBF anticipativo reduce colisión vs. VO",
    }
    rows: list[str] = []
    for row in hypotheses.itertuples(index=False):
        decision = "sustentada" if row.decision == "supported" else "no sustentada"
        rows.append(
            f"{labels[row.hypothesis]} & {int(row.n_pairs)} & {row.effect_estimate:.3f} & "
            f"[{row.CI95_low:.3f}, {row.CI95_high:.3f}] & "
            f"$" + _latex_probability(float(row.Holm_adjusted_p)) + f"$ & {decision} \\\\"
        )
    return (
        "\\begin{tabular}{p{4.6cm}rrrrl}\n\\toprule\n"
        "Hipótesis direccional & Pares & Efecto & IC del 95\\,\\% & "
        "$p_{\\mathrm{Holm}}$ & Decisión \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _numbers(
    manifest: dict[str, Any],
    summary: pd.DataFrame,
    hypotheses: pd.DataFrame,
) -> str:
    values = summary.set_index("method")
    tests = hypotheses.set_index("hypothesis")
    h51 = tests.loc["H5_1_hamiltonian_cbf_reduces_collision_vs_raw"]
    h52 = tests.loc["H5_2_hamiltonian_cbf_improves_safe_success_vs_raw"]
    h53 = tests.loc["H5_3_central_preview_improves_safe_success_vs_local_cbf"]
    h54 = tests.loc["H5_4_local_cbf_reduces_exec_barrier_violation_vs_apf"]
    h55 = tests.loc["H5_5_preview_cbf_reduces_collision_vs_vo_proxy"]
    macros = {
        "SPFiveWorlds": str(int(manifest["worlds"])),
        "SPFiveRuns": str(int(manifest["runs"])),
        "SPFiveRunsPerMethod": str(int(values.loc["pose_pd_raw", "n"])),
        "SPFiveHamiltonianRawCollision": f"{values.loc['damped_hamiltonian_raw', 'any_collision']:.3f}",
        "SPFiveHamiltonianCBFCollision": f"{values.loc['damped_hamiltonian_cbf', 'any_collision']:.3f}",
        "SPFiveHamiltonianRawSafe": f"{values.loc['damped_hamiltonian_raw', 'safe_transport_success']:.3f}",
        "SPFiveHamiltonianCBFSafe": f"{values.loc['damped_hamiltonian_cbf', 'safe_transport_success']:.3f}",
        "SPFiveHamiltonianCollisionEffect": f"{h51.effect_estimate:.3f}",
        "SPFiveHamiltonianCollisionCILow": f"{h51.CI95_low:.3f}",
        "SPFiveHamiltonianCollisionCIHigh": f"{h51.CI95_high:.3f}",
        "SPFiveHamiltonianCollisionPHolm": _latex_probability(float(h51.Holm_adjusted_p)),
        "SPFiveHamiltonianSafeEffect": f"{h52.effect_estimate:.3f}",
        "SPFiveHamiltonianSafeCILow": f"{h52.CI95_low:.3f}",
        "SPFiveHamiltonianSafeCIHigh": f"{h52.CI95_high:.3f}",
        "SPFiveHamiltonianSafePHolm": _latex_probability(float(h52.Holm_adjusted_p)),
        "SPFiveLocalCBFSafe": f"{values.loc['cbf_wrench_local', 'safe_transport_success']:.3f}",
        "SPFiveLocalCBFTimeout": f"{values.loc['cbf_wrench_local', 'timeout']:.3f}",
        "SPFiveCentralSafe": f"{values.loc['centralized_preview_reference', 'safe_transport_success']:.3f}",
        "SPFiveCentralTimeout": f"{values.loc['centralized_preview_reference', 'timeout']:.3f}",
        "SPFiveCentralSafeEffect": f"{h53.effect_estimate:.3f}",
        "SPFiveBarrierEffect": f"{h54.effect_estimate:.4f}",
        "SPFiveVOCollision": f"{values.loc['velocity_obstacle_proxy', 'any_collision']:.3f}",
        "SPFivePreviewCollision": f"{values.loc['distributed_preview_cbf', 'any_collision']:.3f}",
        "SPFivePreviewCollisionEffect": f"{h55.effect_estimate:.3f}",
        "SPFivePreviewCollisionCILow": f"{h55.CI95_low:.3f}",
        "SPFivePreviewCollisionCIHigh": f"{h55.CI95_high:.3f}",
        "SPFivePreviewCollisionPHolm": _latex_probability(float(h55.Holm_adjusted_p)),
    }
    return "\n".join(
        f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items()
    ) + "\n"


def _plot_tradeoff(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    colors = plt.cm.tab10(np.linspace(0.0, 0.8, len(METHODS)))
    for color, method in zip(colors, METHODS, strict=True):
        row = summary.loc[summary["method"] == method].iloc[0]
        x = float(row["any_collision"])
        y = float(row["safe_transport_success"])
        xerr = np.asarray(
            [[x - float(row["any_collision_ci95_low"])],
             [float(row["any_collision_ci95_high"]) - x]]
        )
        yerr = np.asarray(
            [[y - float(row["safe_transport_success_ci95_low"])],
             [float(row["safe_transport_success_ci95_high"]) - y]]
        )
        ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="o", capsize=3, color=color)
        ax.annotate(METHODS[method], (x, y), xytext=(5, 4), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Proporción de mundos con colisión")
    ax.set_ylabel("Proporción de transporte seguro")
    ax.set_xlim(-0.04, 0.90)
    ax.set_ylim(-0.04, 0.76)
    ax.grid(alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _plot_scenario_matrix(runs: pd.DataFrame, path: Path) -> None:
    matrix = np.zeros((len(METHODS), len(SCENARIOS)), dtype=float)
    for i, method in enumerate(METHODS):
        for j, scenario in enumerate(SCENARIOS):
            selected = runs.loc[
                (runs["method"] == method) & (runs["scenario"] == scenario),
                "any_collision",
            ]
            matrix[i, j] = float(selected.mean())
    fig, ax = plt.subplots(figsize=(8.2, 3.7))
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(
        range(len(SCENARIOS)),
        [SCENARIO_LABELS[name] for name in SCENARIOS],
        rotation=25,
        ha="right",
    )
    ax.set_yticks(range(len(METHODS)), list(METHODS.values()))
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, label="Proporción con colisión")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def execute(config_path: Path) -> Path:
    config = _load_yaml(config_path)
    source = Path(config["source_dir"])
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(source / "manifest.json")
    theory = _load_json(source / "theory_audit.json")
    runs = pd.read_csv(source / "tables" / "runs.csv")
    summary = pd.read_csv(source / "tables" / "summary.csv")
    hypotheses = pd.read_csv(source / "tables" / "hypothesis_results.csv")
    stage = pd.read_csv(source / "tables" / "stage_ablation.csv")
    expected = config["expected"]

    world_keys = ["scenario", "seed", "n_robots", "world_hash"]
    per_world = runs.groupby(world_keys)["method"].nunique()
    terminal = {"target_reached", "collision", "timeout", "numerical_failure", "initial_collision"}
    checks = {
        "manifest_complete": manifest["status"] == "complete",
        "world_count": int(manifest["worlds"]) == int(expected["worlds"]),
        "run_count": len(runs) == int(expected["runs"]) == int(manifest["runs"]),
        "method_set": set(runs["method"]) == set(METHODS),
        "scenario_set": set(runs["scenario"]) == set(SCENARIOS),
        "paired_worlds": bool((per_world == len(METHODS)).all()),
        "theory_audit": theory["status"] == "PASS",
        "no_pose_repair": bool((runs["positions_repaired_after_integration"] == 0).all()),
        "terminal_outcomes_preserved": set(runs["termination_reason"]).issubset(terminal),
        "finite_primary_metrics": bool(
            np.isfinite(
                runs[["safe_transport_success", "any_collision", "timeout", "min_clearance_m"]].to_numpy(dtype=float)
            ).all()
        ),
        "stage_rows_complete": len(stage) == 3 * len(runs),
    }
    if not all(checks.values()):
        raise AssertionError(f"SP5 evidence audit failed: {checks}")

    summary.to_csv(tables / "sp5_summary.csv", index=False)
    hypotheses.to_csv(tables / "sp5_hypotheses.csv", index=False)
    stage.to_csv(tables / "sp5_stage_ablation.csv", index=False)
    (tables / "sp5_results.tex").write_text(_results_table(summary), encoding="utf-8")
    (tables / "sp5_hypotheses.tex").write_text(_hypotheses_table(hypotheses), encoding="utf-8")
    (tables / "sp5_numbers.tex").write_text(_numbers(manifest, summary, hypotheses), encoding="utf-8")
    _plot_tradeoff(summary, figures / "fig-sp5-safety-progress.pdf")
    _plot_scenario_matrix(runs, figures / "fig-sp5-collision-matrix.pdf")

    audit = {
        "status": "passed",
        "checks": checks,
        "evidence_level": "C",
        "primary_branch": "SP5-C rigid supported payload",
        "pipeline": "OBSERVED-ESTIMATED-RAW-CLOSED-GUARDED-EXECUTED",
        "model_scope": theory["model_scope"],
        "not_claimed": theory["not_claimed"],
        "push_caging_branch_validated": False,
        "general_discrete_time_invariance_proved": False,
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "report.md").write_text(
        "# SP5-C evidence audit\n\n"
        "The processed artifacts reproduce the frozen 108-world, 864-run campaign. "
        "They support scenario-bounded claims about collision incidence and safe "
        "delivery in a reduced-order planar rigid-payload model. They do not prove "
        "recursive feasibility, sampled-data invariance, frictional contact safety "
        "or hardware performance.\n",
        encoding="utf-8",
    )
    artifacts = sorted(path for path in output.rglob("*") if path.is_file())
    processed_manifest = {
        "experiment_id": config["experiment_id"],
        "status": "complete",
        "config": str(config_path).replace("\\", "/"),
        "source_manifest_sha256": _sha256(source / "manifest.json"),
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): _sha256(path)
            for path in artifacts
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(processed_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = ["execute"]
