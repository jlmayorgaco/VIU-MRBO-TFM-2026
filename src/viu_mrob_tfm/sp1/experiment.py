"""Reproducible SP1 development campaign and paper artifacts."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml
from scipy.stats import wilcoxon

from .theory import (
    AllocationResult,
    allocation_metrics,
    enumerate_base_game,
    exact_coalition_oracle,
    greedy_quorum,
    linear_profile_metrics,
    quorum_closure,
    quorum_potential,
    smith_preferences,
)


METHOD_LABELS = {
    "milp_q": "MILP-Q",
    "greedy_q": "Greedy-Q",
    "smith_raw": "Smith continuo (sin cierre)",
    "smith_qr": "Smith-QR",
    "smith_linear_qr": "Smith lineal + QR",
    "smith_raw_no_excess": "Smith continuo sin cierre ni exceso",
}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    required = {
        "experiment_id",
        "output_dir",
        "seed_base",
        "number_seeds",
        "fleet_sizes",
        "demand_pressure",
        "quota_mixes",
        "geometries",
    }
    missing = required.difference(config)
    if missing:
        raise ValueError(f"missing configuration keys: {sorted(missing)}")
    return config


def make_quotas(
    n_robots: int,
    pressure: float,
    mixture: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Create quotas in 1..4 with total demand nearest to pressure*N."""

    target = max(1, int(round(float(pressure) * n_robots)))
    quotas: list[int] = []
    if mixture == "homogeneous":
        base = int(rng.integers(1, 5))
        while target >= base:
            quotas.append(base)
            target -= base
        if target:
            quotas.append(target)
    elif mixture == "mixed":
        while target:
            candidates = np.arange(1, min(4, target) + 1)
            quota = int(rng.choice(candidates))
            quotas.append(quota)
            target -= quota
        rng.shuffle(quotas)
    else:
        raise ValueError(f"unknown quota mixture: {mixture}")
    return np.asarray(quotas, dtype=int)


def make_world(
    n_robots: int,
    pressure: float,
    mixture: str,
    geometry: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    quotas = make_quotas(n_robots, pressure, mixture, rng)
    n_loads = len(quotas)
    if geometry == "uniform":
        robots = rng.uniform(0.0, 1.0, size=(n_robots, 2))
        loads = rng.uniform(0.0, 1.0, size=(n_loads, 2))
    elif geometry == "clustered":
        centers = np.asarray([[0.2, 0.2], [0.8, 0.8]])
        robots = centers[np.arange(n_robots) % 2] + rng.normal(0.0, 0.09, (n_robots, 2))
        loads = centers[1 - (np.arange(n_loads) % 2)] + rng.normal(0.0, 0.09, (n_loads, 2))
        robots = np.clip(robots, 0.0, 1.0)
        loads = np.clip(loads, 0.0, 1.0)
    else:
        raise ValueError(f"unknown geometry: {geometry}")
    costs = np.linalg.norm(robots[:, None, :] - loads[None, :, :], axis=2) / np.sqrt(2.0)
    values = 1.0 + rng.uniform(0.0, 0.75, size=n_loads)
    return robots, loads, costs, quotas, values


def _world_id(
    n_robots: int,
    target_pressure: float,
    mixture: str,
    geometry: str,
    seed: int,
    quotas: np.ndarray,
) -> str:
    payload = {
        "n_robots": n_robots,
        "target_pressure": target_pressure,
        "mixture": mixture,
        "geometry": geometry,
        "seed": seed,
        "quotas": quotas.tolist(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _evaluate_row(
    *,
    common: dict[str, Any],
    method: str,
    stage: str,
    result: AllocationResult,
    costs: np.ndarray,
    quotas: np.ndarray,
    values: np.ndarray,
    cost_weight: float,
    oracle_metrics: dict[str, Any],
) -> dict[str, Any]:
    metrics = allocation_metrics(costs, quotas, values, result.assignment, cost_weight)
    oracle_value = float(oracle_metrics["completed_value"])
    oracle_objective = float(oracle_metrics["objective"])
    return {
        **common,
        "method": method,
        "stage": stage,
        "closed": bool(metrics["closed"]),
        "completed_loads": int(metrics["completed_loads"]),
        "completed_value": float(metrics["completed_value"]),
        "completed_value_ratio": float(metrics["completed_value"] / max(oracle_value, 1e-12)),
        "deficit": int(metrics["deficit"]),
        "normalized_deficit": float(metrics["normalized_deficit"]),
        "excess": int(metrics["excess"]),
        "normalized_excess": float(metrics["normalized_excess"]),
        "partial_robots": int(metrics["partial_robots"]),
        "partial_robot_fraction": float(metrics["partial_robot_fraction"]),
        "idle_robots": int(metrics["idle_robots"]),
        "social_cost": float(metrics["social_cost"]),
        "objective": float(metrics["objective"]),
        "objective_gap": float(oracle_objective - float(metrics["objective"])),
        "iterations": result.iterations,
        "evaluations": result.evaluations,
        "runtime_s": result.runtime_s,
        "converged": result.converged,
        "residual": result.residual,
    }


def run_campaign(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    regime_rows: list[dict[str, Any]] = []
    seed_base = int(config["seed_base"])
    cost_weight = float(config["cost_weight"])
    beta = float(config["quorum_beta"])
    excess_penalty = float(config["excess_penalty"])
    time_step = float(config["smith"]["time_step"])
    max_steps = int(config["smith"]["max_steps"])
    tolerance = float(config["smith"]["tolerance"])
    world_index = 0
    for n_robots in config["fleet_sizes"]:
        for target_pressure in config["demand_pressure"]:
            for mixture in config["quota_mixes"]:
                for geometry in config["geometries"]:
                    for replicate in range(int(config["number_seeds"])):
                        seed = seed_base + world_index
                        world_index += 1
                        _, _, costs, quotas, values = make_world(
                            int(n_robots), float(target_pressure), str(mixture), str(geometry), seed
                        )
                        demand = int(quotas.sum())
                        pressure = demand / int(n_robots)
                        world_id = _world_id(
                            int(n_robots), float(target_pressure), str(mixture), str(geometry), seed, quotas
                        )
                        common = {
                            "experiment_id": config["experiment_id"],
                            "world_id": world_id,
                            "seed": seed,
                            "replicate": replicate,
                            "n_robots": int(n_robots),
                            "n_loads": len(quotas),
                            "total_demand": demand,
                            "target_pressure": float(target_pressure),
                            "demand_pressure": pressure,
                            "regime": "abundance" if demand < n_robots else "critical" if demand == n_robots else "scarcity",
                            "quota_mixture": mixture,
                            "geometry": geometry,
                            "min_quota": int(quotas.min()),
                            "max_quota": int(quotas.max()),
                        }
                        oracle = exact_coalition_oracle(
                            costs,
                            quotas,
                            values,
                            cost_weight,
                            time_limit_s=float(config["oracle_time_limit_s"]),
                        )
                        oracle_metrics = allocation_metrics(
                            costs, quotas, values, oracle.assignment, cost_weight
                        )
                        greedy = greedy_quorum(costs, quotas, values, cost_weight)
                        smith = smith_preferences(
                            costs,
                            quotas,
                            values,
                            beta=beta,
                            cost_weight=cost_weight,
                            excess_penalty=excess_penalty,
                            seed=seed + 100_000,
                            time_step=time_step,
                            max_steps=max_steps,
                            tolerance=tolerance,
                        )
                        if smith.preferences is None:
                            raise AssertionError("Smith must return continuous preferences")
                        closed = quorum_closure(smith.preferences, costs, quotas, values, cost_weight)
                        linear = smith_preferences(
                            costs,
                            quotas,
                            values,
                            beta=0.0,
                            cost_weight=cost_weight,
                            excess_penalty=excess_penalty,
                            seed=seed + 200_000,
                            time_step=time_step,
                            max_steps=max_steps,
                            tolerance=tolerance,
                        )
                        if linear.preferences is None:
                            raise AssertionError("Smith must return continuous preferences")
                        linear_closed = quorum_closure(
                            linear.preferences, costs, quotas, values, cost_weight
                        )
                        no_excess = smith_preferences(
                            costs,
                            quotas,
                            values,
                            beta=beta,
                            cost_weight=cost_weight,
                            excess_penalty=0.0,
                            seed=seed + 300_000,
                            time_step=time_step,
                            max_steps=max_steps,
                            tolerance=tolerance,
                        )
                        smith_qr = AllocationResult(
                            assignment=closed.assignment,
                            runtime_s=smith.runtime_s + closed.runtime_s,
                            iterations=smith.iterations + closed.iterations,
                            evaluations=smith.evaluations + closed.evaluations,
                            converged=smith.converged,
                            preferences=smith.preferences,
                            residual=smith.residual,
                        )
                        smith_linear_qr = AllocationResult(
                            assignment=linear_closed.assignment,
                            runtime_s=linear.runtime_s + linear_closed.runtime_s,
                            iterations=linear.iterations + linear_closed.iterations,
                            evaluations=linear.evaluations + linear_closed.evaluations,
                            converged=linear.converged,
                            preferences=linear.preferences,
                            residual=linear.residual,
                        )
                        treatments = [
                            ("milp_q", "ORACLE", oracle),
                            ("greedy_q", "CLOSED", greedy),
                            ("smith_raw", "RAW", smith),
                            ("smith_qr", "CLOSED", smith_qr),
                            ("smith_linear_qr", "CLOSED", smith_linear_qr),
                            ("smith_raw_no_excess", "RAW", no_excess),
                        ]
                        for method, stage, result in treatments:
                            rows.append(
                                _evaluate_row(
                                    common=common,
                                    method=method,
                                    stage=stage,
                                    result=result,
                                    costs=costs,
                                    quotas=quotas,
                                    values=values,
                                    cost_weight=cost_weight,
                                    oracle_metrics=oracle_metrics,
                                )
                            )

    regime_seeds = int(config["regime_map_seeds"])
    n_regime = int(config.get("regime_map_fleet_size", config["fleet_sizes"][-1]))
    for p_index, target_pressure in enumerate(config["demand_pressure"]):
        for replicate in range(regime_seeds):
            seed = seed_base + 9_000_000 + p_index * regime_seeds + replicate
            _, _, costs, quotas, values = make_world(
                n_regime, float(target_pressure), "mixed", "uniform", seed
            )
            oracle = exact_coalition_oracle(costs, quotas, values, cost_weight)
            oracle_metrics = allocation_metrics(costs, quotas, values, oracle.assignment, cost_weight)
            for beta_value in config["beta_sweep"]:
                raw = smith_preferences(
                    costs,
                    quotas,
                    values,
                    beta=float(beta_value),
                    cost_weight=cost_weight,
                    excess_penalty=excess_penalty,
                    seed=seed + int(10_000 * float(beta_value)) + 500_000,
                    time_step=time_step,
                    max_steps=max_steps,
                    tolerance=tolerance,
                )
                if raw.preferences is None:
                    raise AssertionError("Smith must return preferences")
                closed = quorum_closure(raw.preferences, costs, quotas, values, cost_weight)
                metrics = allocation_metrics(costs, quotas, values, closed.assignment, cost_weight)
                regime_rows.append(
                    {
                        "seed": seed,
                        "target_pressure": float(target_pressure),
                        "demand_pressure": int(quotas.sum()) / n_regime,
                        "beta": float(beta_value),
                        "closed": bool(metrics["closed"]),
                        "completed_value_ratio": float(
                            metrics["completed_value"]
                            / max(float(oracle_metrics["completed_value"]), 1e-12)
                        ),
                        "partial_robot_fraction_raw": float(
                            allocation_metrics(costs, quotas, values, raw.assignment, cost_weight)[
                                "partial_robot_fraction"
                            ]
                        ),
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(regime_rows)


def _bootstrap_mean(values: np.ndarray, seed: int, draws: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(draws, len(values)))
    samples = values[indices].mean(axis=1)
    return float(values.mean()), float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def summarize(runs: pd.DataFrame, bootstrap_draws: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, Any]] = []
    metrics = ["closed", "completed_value_ratio", "partial_robot_fraction", "normalized_excess"]
    for group_index, ((method, pressure), frame) in enumerate(
        runs.groupby(["method", "target_pressure"], sort=True)
    ):
        row: dict[str, Any] = {
            "method": method,
            "target_pressure": pressure,
            "n_worlds": frame.world_id.nunique(),
        }
        for metric_index, metric in enumerate(metrics):
            mean, low, high = _bootstrap_mean(
                frame[metric].astype(float).to_numpy(),
                seed + 100 * group_index + metric_index,
                bootstrap_draws,
            )
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci95_low"] = low
            row[f"{metric}_ci95_high"] = high
        row["runtime_ms_median"] = 1000.0 * float(frame.runtime_s.median())
        records.append(row)
    by_pressure = pd.DataFrame(records)
    scarcity = runs[runs.regime == "scarcity"]
    method_summary = (
        scarcity.groupby("method", as_index=False)
        .agg(
            n_worlds=("world_id", "nunique"),
            closed_rate=("closed", "mean"),
            value_ratio_mean=("completed_value_ratio", "mean"),
            partial_fraction_mean=("partial_robot_fraction", "mean"),
            excess_fraction_mean=("normalized_excess", "mean"),
            objective_gap_mean=("objective_gap", "mean"),
            runtime_ms_median=("runtime_s", lambda x: 1000.0 * float(np.median(x))),
        )
        .sort_values(["value_ratio_mean", "method"], ascending=[False, True])
    )
    return by_pressure, method_summary


def paired_contrasts(runs: pd.DataFrame, bootstrap_draws: int, seed: int) -> pd.DataFrame:
    comparisons = [
        ("C-SP1-QR", "smith_qr", "smith_raw", "partial_robot_fraction"),
        ("C-SP1-BETA", "smith_qr", "smith_linear_qr", "completed_value_ratio"),
        ("C-SP1-GREEDY", "smith_qr", "greedy_q", "completed_value_ratio"),
        ("C-SP1-EXCESS", "smith_raw", "smith_raw_no_excess", "normalized_excess"),
    ]
    scarcity = runs[runs.regime == "scarcity"]
    rows = []
    for index, (identifier, candidate, reference, metric) in enumerate(comparisons):
        left = scarcity[scarcity.method == candidate][["world_id", metric]].rename(columns={metric: "left"})
        right = scarcity[scarcity.method == reference][["world_id", metric]].rename(columns={metric: "right"})
        merged = left.merge(right, on="world_id", validate="one_to_one")
        difference = merged.left.to_numpy(float) - merged.right.to_numpy(float)
        mean, low, high = _bootstrap_mean(difference, seed + index, bootstrap_draws)
        nonzero = difference[np.abs(difference) > 1e-14]
        p_value = float(wilcoxon(nonzero).pvalue) if len(nonzero) else 1.0
        rows.append(
            {
                "id": identifier,
                "candidate": candidate,
                "reference": reference,
                "metric": metric,
                "n_pairs": len(difference),
                "mean_paired_difference": mean,
                "ci95_low": low,
                "ci95_high": high,
                "wilcoxon_p_two_sided": max(p_value, np.finfo(float).tiny),
            }
        )
    return pd.DataFrame(rows)


def theory_audit(config: dict[str, Any]) -> pd.DataFrame:
    rng = np.random.default_rng(int(config["seed_base"]) + 700)
    rows = []
    for case in range(12):
        n_robots = 3 + case % 3
        quotas = np.array([2, n_robots - 2]) if n_robots > 3 else np.array([2, 1])
        costs = rng.uniform(0.0, 1.0, size=(n_robots, 2))
        audit = enumerate_base_game(costs, quotas, penalty=1.01)
        rows.append(
            {
                "check": "nash_equals_exact_quota",
                "case": case,
                "passed": bool(audit["identity_holds"]),
                "profiles": int(audit["profiles"]),
            }
        )
    costs = np.zeros((2, 2))
    quotas = np.array([2, 2])
    concentrated = np.array([1, 1])
    dispersed = np.array([1, 2])
    linear_equal = (
        linear_profile_metrics(costs, quotas, concentrated, 1.0, 1.0)["deficit"]
        == linear_profile_metrics(costs, quotas, dispersed, 1.0, 1.0)["deficit"]
    )
    quorum_breaks = quorum_potential(
        costs, quotas, np.ones(2), concentrated, 2.0, 0.0, 1.0
    ) > quorum_potential(costs, quotas, np.ones(2), dispersed, 2.0, 0.0, 1.0)
    rows.extend(
        [
            {"check": "scarcity_linear_deficit_degeneracy", "case": 0, "passed": linear_equal, "profiles": 2},
            {"check": "quorum_breaks_minimal_tie", "case": 0, "passed": quorum_breaks, "profiles": 2},
        ]
    )
    return pd.DataFrame(rows)


def make_figures(runs: pd.DataFrame, regime: pd.DataFrame, output: Path) -> None:
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    colors = {
        "milp_q": "#23395B",
        "greedy_q": "#F28E2B",
        "smith_raw": "#BB5566",
        "smith_qr": "#2A9D8F",
        "smith_linear_qr": "#8C6BB1",
        "smith_raw_no_excess": "#999933",
    }
    plot_methods = ["milp_q", "greedy_q", "smith_raw", "smith_qr", "smith_linear_qr"]
    grouped = (
        runs.groupby(["method", "target_pressure"], as_index=False)
        .agg(
            closed=("closed", "mean"),
            completed_value_ratio=("completed_value_ratio", "mean"),
            partial_robot_fraction=("partial_robot_fraction", "mean"),
            normalized_excess=("normalized_excess", "mean"),
        )
    )
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.1), constrained_layout=True)
    panels = [
        ("closed", "(a) Tasa de cierre lógico", (0.0, 1.05)),
        ("completed_value_ratio", "(b) Valor completado / MILP", (0.0, 1.05)),
        ("partial_robot_fraction", "(c) Robots en grupos parciales", (0.0, None)),
        ("normalized_excess", "(d) Sobreasignación normalizada", (0.0, None)),
    ]
    for axis, (metric, title, limits) in zip(axes.flat, panels, strict=True):
        for method in plot_methods:
            frame = grouped[grouped.method == method]
            axis.plot(
                frame.target_pressure,
                frame[metric],
                marker="o",
                label=METHOD_LABELS[method],
                color=colors[method],
            )
        axis.axvline(1.0, color="#555555", linestyle="--", linewidth=0.9)
        axis.set_xlabel(r"Presión de demanda $\rho_D$")
        axis.set_ylabel(title.split(") ", 1)[1])
        axis.set_title(title)
        axis.set_ylim(bottom=limits[0], top=limits[1])
        axis.grid(alpha=0.25)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, frameon=False)
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp1-regime-results.{extension}", dpi=220)
    plt.close(fig)

    heatmap = regime.pivot_table(
        index="beta", columns="target_pressure", values="completed_value_ratio", aggfunc="mean"
    ).sort_index(ascending=False)
    fig, ax = plt.subplots(figsize=(8.0, 4.8), constrained_layout=True)
    image = ax.imshow(heatmap.to_numpy(), aspect="auto", vmin=0.0, vmax=1.0, cmap="viridis")
    ax.set_xticks(np.arange(len(heatmap.columns)), [f"{value:.2f}" for value in heatmap.columns])
    ax.set_yticks(np.arange(len(heatmap.index)), [f"{value:g}" for value in heatmap.index])
    ax.set_xlabel(r"Presión de demanda $\rho_D$")
    ax.set_ylabel(r"Intensidad de cuórum $\beta$")
    ax.set_title("Valor completado relativo después del cierre QR")
    fig.colorbar(image, ax=ax, label="Valor / MILP")
    for extension in ("png", "pdf"):
        fig.savefig(figures / f"fig-sp1-beta-regime-map.{extension}", dpi=220)
    plt.close(fig)


def _latex_summary(method_summary: pd.DataFrame) -> str:
    rows = []
    for row in method_summary.itertuples():
        rows.append(
            f"{METHOD_LABELS[row.method]} & {int(row.n_worlds)} & {100*row.closed_rate:.1f} & "
            f"{100*row.value_ratio_mean:.1f} & {100*row.partial_fraction_mean:.1f} & "
            f"{100*row.excess_fraction_mean:.1f} & {row.runtime_ms_median:.2f} \\\\"
        )
    return (
        "\\begin{tabular}{lrrrrrr}\n\\toprule\n"
        "Método & $n$ & Cierre [\\%] & Valor/MILP [\\%] & Parciales [\\%] & Exceso [\\%] & CPU [ms] \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(config_path: Path, smoke: bool = False) -> Path:
    config = load_config(config_path)
    if smoke:
        config = dict(config)
        config["experiment_id"] = f"{config['experiment_id']}_SMOKE"
        config["output_dir"] = str(Path(config["output_dir"]) / "smoke")
        config["number_seeds"] = 2
        config["fleet_sizes"] = [8]
        config["demand_pressure"] = [0.75, 1.0, 1.25]
        config["quota_mixes"] = ["mixed"]
        config["geometries"] = ["uniform"]
        config["regime_map_seeds"] = 2
        config["bootstrap_resamples"] = 100
    output = Path(config["output_dir"])
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    runs, regime = run_campaign(config)
    by_pressure, method_summary = summarize(
        runs, int(config["bootstrap_resamples"]), int(config["seed_base"]) + 10
    )
    contrasts = paired_contrasts(
        runs, int(config["bootstrap_resamples"]), int(config["seed_base"]) + 20
    )
    audit = theory_audit(config)
    if not bool(audit.passed.all()):
        raise AssertionError("SP1 theory audit failed")
    runs.to_csv(tables / "runs.csv", index=False)
    regime.to_csv(tables / "beta_regime_map.csv", index=False)
    by_pressure.to_csv(tables / "summary_by_pressure.csv", index=False)
    method_summary.to_csv(tables / "method_summary_scarcity.csv", index=False)
    contrasts.to_csv(tables / "paired_contrasts_scarcity.csv", index=False)
    audit.to_csv(tables / "theory_checks.csv", index=False)
    (tables / "sp1_method_summary.tex").write_text(
        _latex_summary(method_summary), encoding="utf-8"
    )
    make_figures(runs, regime, output)
    report = [
        "# SP1 quorum and closure development report",
        "",
        f"Worlds: {runs.world_id.nunique()}; method rows: {len(runs)}.",
        f"Theory checks: {int(audit.passed.sum())}/{len(audit)} passed.",
        "",
        "This is a paired development campaign. It is not a sealed confirmatory holdout.",
        "RAW Smith preferences and CLOSED QR assignments are reported as different stages.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    artifacts = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "experiment_id": config["experiment_id"],
        "status": "development_completed",
        "confirmatory": False,
        "config": config,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "worlds": int(runs.world_id.nunique()),
        "method_rows": int(len(runs)),
        "theory_gate_passed": bool(audit.passed.all()),
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): _sha256(path)
            for path in artifacts
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output


__all__ = ["execute", "load_config", "make_quotas", "make_world", "run_campaign"]
