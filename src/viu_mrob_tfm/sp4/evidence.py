"""Audit and regenerate manuscript artifacts for SP4 docking and transport."""

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


DOCKING_METHODS = {
    "direct_to_slot": "Directo al contacto",
    "cbf_qp": "Proyecci\\'on CBF",
    "nash_pd_exact": "Nash--PD exacto",
    "nash_pd_ring": "Nash--PD anillo",
    "replicator_primitives": "Replicator + CBF",
}

TRANSPORT_METHODS = {
    "pose_pd_raw": "PD de pose",
    "damped_hamiltonian_raw": "Hamiltoniano amortiguado",
    "distributed_preview_cbf": "CBF anticipativo distribuido",
    "centralized_preview_reference": "Previsión central",
}

TRANSPORT_METRICS = (
    "target_reached",
    "time_to_target_s",
    "final_position_error_m",
    "final_orientation_error_rad",
    "mechanical_work_j",
    "force_effort_n2s",
    "runtime_wall_s",
)


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


def _bootstrap_mean_ci(
    values: np.ndarray,
    *,
    rng: np.random.Generator,
    resamples: int,
) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        return float("nan"), float("nan")
    indices = rng.integers(0, data.size, size=(resamples, data.size))
    means = np.mean(data[indices], axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return float(low), float(high)


def _transport_summary(
    runs: pd.DataFrame,
    methods: list[str],
    *,
    seed: int,
    resamples: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records: list[dict[str, Any]] = []
    for method in methods:
        subset = runs.loc[runs["method"] == method]
        record: dict[str, Any] = {
            "method": method,
            "label": TRANSPORT_METHODS[method],
            "n": len(subset),
        }
        for metric in TRANSPORT_METRICS:
            values = subset[metric].to_numpy(dtype=float)
            low, high = _bootstrap_mean_ci(
                values, rng=rng, resamples=resamples
            )
            record[f"{metric}_mean"] = float(np.mean(values))
            record[f"{metric}_ci_low"] = low
            record[f"{metric}_ci_high"] = high
        records.append(record)
    return pd.DataFrame.from_records(records)


def _paired_contrasts(
    runs: pd.DataFrame,
    *,
    seed: int,
    resamples: int,
) -> pd.DataFrame:
    keys = ["scenario", "seed", "n_robots", "world_hash"]
    first = runs.loc[runs["method"] == "damped_hamiltonian_raw"].set_index(keys)
    second = runs.loc[runs["method"] == "pose_pd_raw"].set_index(keys)
    if not first.index.equals(second.index):
        first = first.sort_index()
        second = second.sort_index()
    if not first.index.equals(second.index):
        raise AssertionError("SP4 transport methods are not paired by world")
    rng = np.random.default_rng(seed + 1)
    records: list[dict[str, Any]] = []
    for metric in (
        "time_to_target_s",
        "mechanical_work_j",
        "final_position_error_m",
        "final_orientation_error_rad",
    ):
        differences = (
            first[metric].to_numpy(dtype=float)
            - second[metric].to_numpy(dtype=float)
        )
        low, high = _bootstrap_mean_ci(
            differences, rng=rng, resamples=resamples
        )
        records.append(
            {
                "contrast": "hamiltonian_minus_pose_pd",
                "metric": metric,
                "n_pairs": differences.size,
                "mean_difference": float(np.mean(differences)),
                "ci95_low": low,
                "ci95_high": high,
            }
        )
    return pd.DataFrame.from_records(records)


def _docking_table(summary: pd.DataFrame) -> str:
    indexed = summary.set_index("method")
    rows: list[str] = []
    for method, label in DOCKING_METHODS.items():
        row = indexed.loc[method]
        kkt = float(row["final_kkt_residual"])
        kkt_text = f"{kkt:.3f}" if np.isfinite(kkt) else "--"
        rows.append(
            f"{label} & {int(row['n'])} & {row['safe_docking_success']:.3f} & "
            f"{row['any_collision']:.3f} & {row['timeout']:.3f} & "
            f"{kkt_text} & {1000.0 * row['runtime_s']:.1f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
        "M\\'etodo & $n$ & \\'Exito seguro & Colisi\\'on & Horizonte agotado & KKT & CPU [ms] \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _transport_table(summary: pd.DataFrame) -> str:
    indexed = summary.set_index("method")
    rows: list[str] = []
    for method, label in TRANSPORT_METHODS.items():
        row = indexed.loc[method]
        rows.append(
            f"{label} & {int(row['n'])} & {row['target_reached_mean']:.3f} & "
            f"{row['time_to_target_s_mean']:.2f} & "
            f"{row['final_position_error_m_mean']:.3f} & "
            f"{np.degrees(row['final_orientation_error_rad_mean']):.3f} & "
            f"{row['mechanical_work_j_mean']:.1f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
        "Control & $n$ & Entrega & Tiempo [s] & Error [m] & Error [$^\\circ$] & Trabajo [J] \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _latex_probability(value: float) -> str:
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / 10.0**exponent
    return f"{mantissa:.2f}\\times10^{{{exponent}}}"


def _numbers(
    v3_summary: pd.DataFrame,
    v3_hypotheses: pd.DataFrame,
    v4_summary: pd.DataFrame,
    transport: pd.DataFrame,
    contrasts: pd.DataFrame,
) -> str:
    v3 = v3_summary.set_index("method")
    hypotheses = v3_hypotheses.set_index("hypothesis")
    v4 = v4_summary.set_index("method")
    trans = transport.set_index("method")
    diff = contrasts.set_index("metric")
    effect = hypotheses.loc["H4_1_replicator_safe_success_above_cbf"]
    macros = {
        "SPFourDockWorlds": str(int(v3.loc["replicator_primitives", "n"])),
        "SPFourDockRuns": str(int(v3_summary["n"].sum())),
        "SPFourRepSafe": f"{v3.loc['replicator_primitives', 'safe_docking_success']:.3f}",
        "SPFourCBFSafe": f"{v3.loc['cbf_qp', 'safe_docking_success']:.3f}",
        "SPFourDockEffect": f"{effect.mean_difference:.3f}",
        "SPFourDockCILow": f"{effect.ci95_low:.3f}",
        "SPFourDockCIHigh": f"{effect.ci95_high:.3f}",
        "SPFourDockPHolm": _latex_probability(float(effect.p_holm)),
        "SPFourVFourWorlds": str(int(v4.loc["distributed_pd_hocbf", "n"])),
        "SPFourVFourGameSafe": f"{v4.loc['distributed_pd_hocbf', 'safe_docking_success']:.3f}",
        "SPFourVFourCentralSafe": f"{v4.loc['central_hocbf', 'safe_docking_success']:.3f}",
        "SPFourVFourDirectSafe": f"{v4.loc['direct_hocbf', 'safe_docking_success']:.3f}",
        "SPFourTransportWorlds": str(int(trans.loc["pose_pd_raw", "n"])),
        "SPFourPoseTime": f"{trans.loc['pose_pd_raw', 'time_to_target_s_mean']:.2f}",
        "SPFourHamiltonianTime": f"{trans.loc['damped_hamiltonian_raw', 'time_to_target_s_mean']:.2f}",
        "SPFourPoseWork": f"{trans.loc['pose_pd_raw', 'mechanical_work_j_mean']:.1f}",
        "SPFourHamiltonianWork": f"{trans.loc['damped_hamiltonian_raw', 'mechanical_work_j_mean']:.1f}",
        "SPFourCentralTime": f"{trans.loc['centralized_preview_reference', 'time_to_target_s_mean']:.2f}",
        "SPFourCentralWork": f"{trans.loc['centralized_preview_reference', 'mechanical_work_j_mean']:.1f}",
        "SPFourTimeDiff": f"{diff.loc['time_to_target_s', 'mean_difference']:.3f}",
        "SPFourTimeDiffLow": f"{diff.loc['time_to_target_s', 'ci95_low']:.3f}",
        "SPFourTimeDiffHigh": f"{diff.loc['time_to_target_s', 'ci95_high']:.3f}",
        "SPFourWorkDiff": f"{diff.loc['mechanical_work_j', 'mean_difference']:.2f}",
        "SPFourWorkDiffLow": f"{diff.loc['mechanical_work_j', 'ci95_low']:.2f}",
        "SPFourWorkDiffHigh": f"{diff.loc['mechanical_work_j', 'ci95_high']:.2f}",
    }
    return "\n".join(
        f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items()
    ) + "\n"


def _plot_transport(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    colors = ["#0072B2", "#D55E00", "#009E73", "#6F4E7C"]
    for color, row in zip(colors, summary.itertuples(index=False)):
        x = float(row.time_to_target_s_mean)
        y = float(row.mechanical_work_j_mean)
        xerr = np.asarray(
            [[x - row.time_to_target_s_ci_low], [row.time_to_target_s_ci_high - x]]
        )
        yerr = np.asarray(
            [[y - row.mechanical_work_j_ci_low], [row.mechanical_work_j_ci_high - y]]
        )
        ax.errorbar(
            x,
            y,
            xerr=xerr,
            yerr=yerr,
            marker="o",
            markersize=6,
            capsize=3,
            color=color,
            label=row.label,
        )
    ax.set_xlabel("Tiempo hasta la pose objetivo [s]")
    ax.set_ylabel("Trabajo mec\u00e1nico [J]")
    ax.grid(alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def execute(config_path: Path) -> Path:
    config = _load_yaml(config_path)
    v3_dir = Path(config["docking_v3_dir"])
    v4_dir = Path(config["docking_v4_dir"])
    transport_dir = Path(config["transport_dir"])
    output = Path(config["output_dir"])
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    expected = config["expected"]
    v3_manifest = _load_json(v3_dir / "manifest.json")
    v3_theory = _load_json(v3_dir / "theory_audit.json")
    v4_theory = _load_json(v4_dir / "theory_audit.json")
    transport_manifest = _load_json(transport_dir / "manifest.json")
    transport_theory = _load_json(transport_dir / "theory_audit.json")
    v3_summary = pd.read_csv(v3_dir / "tables" / "summary.csv")
    v3_hypotheses = pd.read_csv(v3_dir / "tables" / "hypothesis_results.csv")
    v4_summary = pd.read_csv(v4_dir / "tables" / "summary.csv")
    v4_runs = pd.read_csv(v4_dir / "tables" / "runs.csv")
    transport_runs = pd.read_csv(transport_dir / "tables" / "runs.csv")

    methods = list(config["transport_methods"])
    open_runs = transport_runs.loc[
        (transport_runs["scenario"] == config["transport_scenario"])
        & transport_runs["method"].isin(methods)
    ].copy()
    counts = open_runs.groupby("method").size()
    world_hashes = open_runs.groupby(["seed", "n_robots"])["world_hash"].nunique()
    checks = {
        "v3_worlds": int(v3_manifest["worlds"])
        == int(expected["docking_v3_worlds"]),
        "v3_runs": int(v3_manifest["runs"]) == int(expected["docking_v3_runs"]),
        "v3_theory": v3_theory["status"] == "PASS",
        "v3_initial_worlds": int(v3_theory["initial_collision_count"]) == 0,
        "v4_runs": len(v4_runs) == int(expected["docking_v4_runs"]),
        "v4_theory": bool(v4_theory["gates_pass"]),
        "v4_exec_barrier": int(v4_theory["total_exec_barrier_violations"]) == 0,
        "transport_manifest": transport_manifest["status"] == "complete",
        "transport_theory": transport_theory["status"] == "PASS",
        "transport_no_repair": bool(transport_theory["positions_repaired_after_integration"])
        == bool(expected["transport_positions_repaired"]),
        "transport_counts": bool(
            (counts == int(expected["transport_worlds_per_method"])).all()
            and set(counts.index) == set(methods)
        ),
        "transport_world_pairing": bool((world_hashes == 1).all()),
        "transport_all_reached": bool((open_runs["target_reached"] == 1).all()),
    }
    if not all(checks.values()):
        raise AssertionError(f"SP4 evidence audit failed: {checks}")

    bootstrap = config["bootstrap"]
    transport_summary = _transport_summary(
        open_runs,
        methods,
        seed=int(bootstrap["seed"]),
        resamples=int(bootstrap["resamples"]),
    )
    contrasts = _paired_contrasts(
        open_runs,
        seed=int(bootstrap["seed"]),
        resamples=int(bootstrap["resamples"]),
    )
    transport_summary.to_csv(tables / "sp4_transport_summary.csv", index=False)
    contrasts.to_csv(tables / "sp4_transport_contrasts.csv", index=False)
    (tables / "sp4_docking_results.tex").write_text(
        _docking_table(v3_summary), encoding="utf-8"
    )
    (tables / "sp4_transport_results.tex").write_text(
        _transport_table(transport_summary), encoding="utf-8"
    )
    (tables / "sp4_numbers.tex").write_text(
        _numbers(v3_summary, v3_hypotheses, v4_summary, transport_summary, contrasts),
        encoding="utf-8",
    )
    _plot_transport(
        transport_summary, figures / "fig-sp4-transport-tradeoff.pdf"
    )

    audit = {
        "status": "passed",
        "checks": checks,
        "docking_scope": "dynamic-unicycle recruitment to fixed contact poses",
        "transport_scope": transport_theory["model_scope"],
        "transport_worlds_per_method": int(expected["transport_worlds_per_method"]),
        "coppelia_replay_is_independent_physics_validation": False,
        "push_caging_validated": False,
        "full_historical_generators_present_in_worktree": False,
    }
    (output / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "report.md").write_text(
        "# SP4 evidence audit\n\n"
        "The manuscript artifacts combine two explicitly separated evidence layers: "
        "dynamic-unicycle docking to fixed load-contact poses and the open-nominal "
        "stratum of the frozen reduced-order rigid-payload campaign. The latter has "
        f"{expected['transport_worlds_per_method']} paired worlds per method and no "
        "post-integration pose repair. It supports planar pose transport only; it does "
        "not validate frictional contact, hardware, or the push/caging branch.\n",
        encoding="utf-8",
    )
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
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


__all__ = ["execute"]
