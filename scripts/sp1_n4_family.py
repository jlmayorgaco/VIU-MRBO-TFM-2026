"""Extend SP1.N4 into an auditable distributed algorithm family.

The campaign has three evidence strata:

1. four new atomic methods are run on the 1,200 frozen N4-v1 worlds and
   joined to the six existing paired methods;
2. exact DPOP and MILP are compared on deliberately small worlds;
3. a separate scaling campaign measures BR and DMIS+TX while N and K grow.

The historical population-dynamics benchmark is reduced only for context.  It
is never pooled with the atomic campaign because the model and worlds differ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.ticker import FuncFormatter, MaxNLocator
from scipy import stats


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from sp1_n3_confirmatory import solve_oracle  # noqa: E402
from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import World, make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import (  # noqa: E402
    METHOD_LABELS,
    run_geo_qpg,
    solve_dpop_exact_small,
)


DEFAULT_CONFIG = REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n4_family_v2.yaml"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n4_v2"

METHOD_ORDER = (
    "capacity_cbba_rb",
    "weighted_grape",
    "weighted_pair_grape",
    "geo_qpg_u",
    "geo_qpg_smith",
    "geo_qpg_lll",
    "geo_qpg_p",
    "geo_qpg_c3",
    "geo_qpg_cf",
    "geo_qpg_d",
)
HIERARCHY_ORDER = ("geo_qpg_u", "geo_qpg_p", "geo_qpg_c3")
LABELS = {
    "capacity_cbba_rb": "CBBA-RB",
    "weighted_grape": "GRAPE",
    "weighted_pair_grape": "Pair-GRAPE",
    **METHOD_LABELS,
    "milp_highs": "MILP/HIGHS",
    "dpop_exact_small": "DPOP exacto",
}
COLORS = {
    "capacity_cbba_rb": "#6F4AA8",
    "weighted_grape": "#3274A1",
    "weighted_pair_grape": "#63A8D3",
    "geo_qpg_u": "#B77816",
    "geo_qpg_smith": "#E2A93B",
    "geo_qpg_lll": "#CE6D39",
    "geo_qpg_p": "#D64B3C",
    "geo_qpg_c3": "#9E2F3D",
    "geo_qpg_cf": "#7A7F87",
    "geo_qpg_d": "#16825D",
    "milp_highs": "#202124",
    "dpop_exact_small": "#008B8B",
}
SCENARIO_LABELS = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}


def spanish_number(value: float, digits: int | None = None) -> str:
    text = f"{value:g}" if digits is None else f"{value:.{digits}f}"
    return text.replace("-", "−").replace(".", ",")


def spanish_tick(value: float, _position: float | None = None) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000 and float(value).is_integer():
        return f"{int(value):,}".replace(",", "\u202f")
    return spanish_number(value)


def latex_decimal(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", r"{,}")


def latex_integer(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", r"\,")


def latex_scientific(value: float, digits: int = 2) -> str:
    if value == 0:
        return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10**exponent)
    return rf"{latex_decimal(mantissa, digits)} \times 10^{{{exponent}}}"


def stable_seed(base: int, *parts: object) -> int:
    payload = "|".join([str(base), *(str(part) for part in parts)])
    return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:4], "big")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return value.as_posix()
    raise TypeError(type(value).__name__)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=json_default),
        encoding="utf-8",
    )


def git_state() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(
            args,
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

    return {
        "commit": run("git", "rev-parse", "HEAD") or "unknown",
        "branch": run("git", "branch", "--show-current") or "unknown",
        "tree_dirty": bool(run("git", "status", "--porcelain")),
    }


def load_config(path: Path, *, smoke: bool) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if smoke:
        config["campaign_id"] += "_SMOKE"
        config["family_extension"]["max_worlds"] = 12
        config["dpop_small"]["robot_load_pairs"] = [[6, 2]]
        config["dpop_small"]["scenarios"] = ["uniform", "corridor"]
        config["dpop_small"]["capacity_cv"] = [0.65]
        config["dpop_small"]["pressure"] = [0.85]
        config["dpop_small"]["seeds_per_cell"] = 1
        config["scaling"]["robot_load_pairs"] = [[16, 4], [32, 8]]
        config["scaling"]["scenarios"] = ["uniform"]
        config["scaling"]["seeds_per_cell"] = 1
        config["analysis"]["bootstrap_resamples"] = 500
    return config


def progress(label: str, index: int, total: int) -> None:
    if index == total or index % max(1, total // 20) == 0:
        print(f"  {label}: {index}/{total}", flush=True)


def world_from_frozen(row: pd.Series, section: Mapping[str, Any]) -> World:
    return make_world(
        world_id=str(row["world_id"]),
        robot_count=int(row["N"]),
        load_count=int(row["K"]),
        q_bar=float(section["q_bar_kg"]),
        cv=float(row["capacity_cv"]),
        pressure=float(row["pressure"]),
        scenario=str(row["scenario"]),
        workspace=tuple(float(value) for value in section["workspace_m"]),
        seed=int(row["world_seed"]),
        alpha=float(section["demand_split_alpha"]),
    )


def extension_row(
    world_key: str,
    world: World,
    adjacency: np.ndarray,
    method: str,
    oracle: Mapping[str, Any],
    max_rounds: int,
    campaign_id: str,
    experiment: str,
) -> dict[str, Any]:
    result = run_geo_qpg(world, adjacency, method, max_rounds=max_rounds)
    certificate = result.certificate
    gap = float("nan")
    objective = float(oracle.get("oracle_objective", float("nan")))
    if certificate.feasible and bool(oracle.get("oracle_certified", False)) and objective > 0:
        gap = (certificate.distance_cost - objective) / objective
    return {
        "campaign_id": campaign_id,
        "experiment": experiment,
        "evidence_origin": "v2_execution",
        "world_key": world_key,
        "world_id": world.world_id,
        "world_seed": world.seed,
        "scenario": world.scenario,
        "N": world.n_robots,
        "K": world.n_loads,
        "capacity_cv": world.capacity_cv,
        "pressure": world.pressure,
        "graph_regime": "medium",
        "method": method,
        "method_family": "N4_ATOMIC",
        "algorithm_status": result.algorithm_status,
        "terminal_phase": result.terminal_phase,
        "raw_certificate": certificate.status,
        "feasible": certificate.feasible,
        "distance_cost": certificate.distance_cost,
        "capacity_deficit": certificate.total_deficit,
        "robot_conflict": certificate.conflicts,
        "excess_capacity": certificate.excess_capacity,
        "assigned_robots": certificate.assigned_robots,
        "max_coalition_size": max(certificate.coalition_sizes, default=0),
        "unserved_loads": certificate.unserved_loads,
        "rounds": result.rounds,
        "messages": result.messages,
        "bytes": result.bytes_sent,
        "messages_per_agent": result.messages / world.n_robots,
        "bytes_per_agent": result.bytes_sent / world.n_robots,
        "runtime_ms": result.runtime_ms,
        "commits": result.commits,
        "quota_commits": result.quota_commits,
        "geometry_commits": result.geometry_commits,
        "rejected_stale": result.rejected_stale,
        "rejected_conflict": result.rejected_conflict,
        "arbitration_messages": result.arbitration_messages,
        "transaction_messages": result.transaction_messages,
        "transaction_aborts": result.transaction_aborts,
        "mis_iterations": result.mis_iterations,
        "max_parallel_commits": result.max_parallel_commits,
        "potential_monotone": result.potential_monotone,
        "unilateral_local_minimum": result.unilateral_local_minimum,
        "pair_local_minimum": result.pair_local_minimum,
        "triple_local_minimum": result.triple_local_minimum,
        **dict(oracle),
        "optimality_gap": gap,
    }


def run_family_extension(config: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = REPOSITORY_ROOT / str(config["source"]["directory"])
    worlds = pd.read_csv(source / "raw" / "e3_confirmatory_worlds.csv")
    source_runs = pd.read_csv(source / "raw" / "e3_confirmatory_runs.csv")
    oracles = pd.read_csv(source / "raw" / "e3_oracle_runs.csv").set_index("world_key")
    max_worlds = config["family_extension"].get("max_worlds")
    if max_worlds is not None:
        worlds = worlds.head(int(max_worlds)).copy()
        source_runs = source_runs[source_runs["world_key"].isin(worlds["world_key"])].copy()
    source_runs["source_campaign_id"] = source_runs["campaign_id"]
    source_runs["campaign_id"] = str(config["campaign_id"])
    source_runs["evidence_origin"] = "frozen_v1"
    for column in (
        "arbitration_messages",
        "transaction_messages",
        "transaction_aborts",
        "mis_iterations",
        "triple_local_minimum",
    ):
        source_runs[column] = np.nan

    section = config["family_extension"]
    rows: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(worlds.iterrows(), 1):
        world = world_from_frozen(row, section)
        if world.digest() != str(row["world_digest"]):
            raise RuntimeError(f"frozen world digest mismatch: {row['world_key']}")
        adjacency = adjacency_for_regime(world.robot_positions, str(section["graph_regime"]))
        oracle = oracles.loc[str(row["world_key"])].to_dict()
        for method in section["methods"]:
            rows.append(
                extension_row(
                    str(row["world_key"]),
                    world,
                    adjacency,
                    str(method),
                    oracle,
                    int(section["max_rounds"]),
                    str(config["campaign_id"]),
                    "E4_FAMILY_PAIRED",
                )
            )
        progress("E4 family", index, len(worlds))
    extension = pd.DataFrame(rows)
    combined = pd.concat([source_runs, extension], ignore_index=True, sort=False)
    combined["feasible"] = combined["feasible"].astype(bool)
    return combined, worlds


def generated_world(
    section: Mapping[str, Any],
    *,
    experiment: str,
    n: int,
    k: int,
    scenario: str,
    cv: float,
    pressure: float,
    replicate: int,
) -> tuple[str, World]:
    seed = stable_seed(
        int(section["base_seed"]), experiment, n, k, scenario, cv, pressure, replicate
    )
    key = f"{experiment}:N{n}:K{k}:{scenario}:cv{cv}:p{pressure}:r{replicate}"
    return key, make_world(
        world_id=key,
        robot_count=n,
        load_count=k,
        q_bar=float(section["q_bar_kg"]),
        cv=float(cv),
        pressure=float(pressure),
        scenario=scenario,
        workspace=tuple(float(value) for value in section["workspace_m"]),
        seed=seed,
        alpha=float(section["demand_split_alpha"]),
    )


def run_dpop_small(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["dpop_small"]
    cells = [
        (int(n), int(k), scenario, float(cv), float(pressure), replicate)
        for n, k in section["robot_load_pairs"]
        for scenario in section["scenarios"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    rows: list[dict[str, Any]] = []
    for index, (n, k, scenario, cv, pressure, replicate) in enumerate(cells, 1):
        key, world = generated_world(
            section,
            experiment="E5_DPOP",
            n=n,
            k=k,
            scenario=scenario,
            cv=cv,
            pressure=pressure,
            replicate=replicate,
        )
        oracle = solve_oracle(world, float(section["oracle_time_limit_s"]))
        dpop = solve_dpop_exact_small(world, max_profiles=int(section["max_profiles"]))
        common = {
            "campaign_id": config["campaign_id"],
            "experiment": "E5_DPOP_SMALL",
            "world_key": key,
            "world_seed": world.seed,
            "scenario": scenario,
            "N": n,
            "K": k,
            "capacity_cv": cv,
            "pressure": pressure,
            **oracle,
        }
        rows.append({**common, **dpop.as_dict(), "method_family": "EXACT_DISTRIBUTED"})
        oracle_objective = float(oracle["oracle_objective"])
        rows.append(
            {
                **common,
                "method": "milp_highs",
                "method_family": "CENTRAL_ORACLE",
                "feasible": bool(oracle["oracle_feasible"]),
                "distance_cost": oracle_objective,
                "runtime_ms": 1_000.0 * float(oracle["oracle_runtime_s"]),
                "messages": np.nan,
                "bytes": np.nan,
                "utility_entries": np.nan,
                "induced_width": np.nan,
                "profiles_evaluated": np.nan,
            }
        )
        adjacency = adjacency_for_regime(world.robot_positions, "medium")
        for method in section["qpg_methods"]:
            result = run_geo_qpg(
                world, adjacency, str(method), max_rounds=int(section["max_rounds"])
            )
            rows.append(
                {
                    **common,
                    "method": method,
                    "method_family": "N4_ATOMIC",
                    "feasible": result.certificate.feasible,
                    "distance_cost": result.certificate.distance_cost,
                    "runtime_ms": result.runtime_ms,
                    "messages": result.messages,
                    "bytes": result.bytes_sent,
                    "utility_entries": np.nan,
                    "induced_width": np.nan,
                    "profiles_evaluated": np.nan,
                }
            )
        progress("E5 DPOP", index, len(cells))
    frame = pd.DataFrame(rows)
    frame["optimality_gap"] = np.where(
        frame["feasible"].astype(bool)
        & frame["oracle_certified"].astype(bool)
        & (frame["oracle_objective"] > 0),
        (frame["distance_cost"] - frame["oracle_objective"]) / frame["oracle_objective"],
        np.nan,
    )
    return frame


def run_scaling(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["scaling"]
    cells = [
        (int(n), int(k), scenario, replicate)
        for n, k in section["robot_load_pairs"]
        for scenario in section["scenarios"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    rows: list[dict[str, Any]] = []
    for index, (n, k, scenario, replicate) in enumerate(cells, 1):
        key, world = generated_world(
            section,
            experiment="E6_SCALE",
            n=n,
            k=k,
            scenario=scenario,
            cv=float(section["capacity_cv"]),
            pressure=float(section["pressure"]),
            replicate=replicate,
        )
        adjacency = adjacency_for_regime(world.robot_positions, str(section["graph_regime"]))
        for method in section["methods"]:
            result = run_geo_qpg(
                world, adjacency, str(method), max_rounds=int(section["max_rounds"])
            )
            rows.append(
                {
                    "campaign_id": config["campaign_id"],
                    "experiment": "E6_SCALING",
                    "world_key": key,
                    "world_seed": world.seed,
                    "scenario": scenario,
                    "N": n,
                    "K": k,
                    "method": method,
                    "feasible": result.certificate.feasible,
                    "capacity_deficit": result.certificate.total_deficit,
                    "runtime_ms": result.runtime_ms,
                    "rounds": result.rounds,
                    "messages": result.messages,
                    "bytes": result.bytes_sent,
                    "bytes_per_agent": result.bytes_sent / n,
                    "max_parallel_commits": result.max_parallel_commits,
                    "algorithm_status": result.algorithm_status,
                    "arbitration_messages": result.arbitration_messages,
                    "transaction_messages": result.transaction_messages,
                }
            )
        progress("E6 scaling", index, len(cells))
    return pd.DataFrame(rows)


def wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float, float]:
    if total == 0:
        return float("nan"), float("nan"), float("nan")
    z = float(stats.norm.ppf(0.5 + confidence / 2))
    p = successes / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total**2)) / den
    return float(p), float(centre - radius), float(centre + radius)


def bootstrap_ci(
    values: Iterable[float], *, resamples: int, seed: int, statistic: str = "median"
) -> tuple[float, float, float]:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if not len(array):
        return float("nan"), float("nan"), float("nan")
    estimator = np.mean if statistic == "mean" else np.median
    rng = np.random.default_rng(seed)
    samples = rng.choice(array, size=(resamples, len(array)), replace=True)
    estimates = estimator(samples, axis=1)
    return (
        float(estimator(array)),
        float(np.quantile(estimates, 0.025)),
        float(np.quantile(estimates, 0.975)),
    )


def family_summary(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["analysis"]
    oracle_feasible = frame[frame["oracle_feasible"].astype(bool)].copy()
    rows: list[dict[str, Any]] = []
    for index, method in enumerate(METHOD_ORDER):
        group = oracle_feasible[oracle_feasible["method"] == method]
        rate, low, high = wilson(int(group["feasible"].sum()), len(group))
        gap = bootstrap_ci(
            group.loc[group["feasible"], "optimality_gap"],
            resamples=int(section["bootstrap_resamples"]),
            seed=int(section["bootstrap_seed"]) + index,
        )
        rows.append(
            {
                "method": method,
                "label": LABELS[method],
                "worlds": len(group),
                "feasibility": rate,
                "feasibility_low": low,
                "feasibility_high": high,
                "gap_median": gap[0],
                "gap_low": gap[1],
                "gap_high": gap[2],
                "runtime_ms_median": float(group["runtime_ms"].median()),
                "bytes_per_agent_median": float(group["bytes_per_agent"].median()),
                "rounds_median": float(group["rounds"].median()),
            }
        )
    return pd.DataFrame(rows)


def paired_contrast(
    frame: pd.DataFrame,
    left: str,
    right: str,
    metric: str,
    config: Mapping[str, Any],
    *,
    feasible_common: bool = False,
) -> dict[str, Any]:
    subset = frame[frame["method"].isin([left, right])].copy()
    if feasible_common:
        feasible = subset.pivot(index="world_key", columns="method", values="feasible")
        keys = feasible.index[feasible[left].astype(bool) & feasible[right].astype(bool)]
        subset = subset[subset["world_key"].isin(keys)]
    wide = subset.pivot(index="world_key", columns="method", values=metric).dropna()
    differences = (wide[left] - wide[right]).to_numpy(float)
    estimate, low, high = bootstrap_ci(
        differences,
        resamples=int(config["analysis"]["bootstrap_resamples"]),
        seed=stable_seed(int(config["analysis"]["bootstrap_seed"]), left, right, metric),
    )
    nonzero = differences[np.abs(differences) > 1e-12]
    p_value = (
        float(stats.wilcoxon(nonzero, alternative="two-sided").pvalue)
        if len(nonzero)
        else 1.0
    )
    return {
        "left": left,
        "right": right,
        "metric": metric,
        "worlds": len(differences),
        "median_difference": estimate,
        "ci_low": low,
        "ci_high": high,
        "wilcoxon_p": p_value,
    }


def risk_difference(
    frame: pd.DataFrame, left: str, right: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    subset = frame[
        frame["oracle_feasible"].astype(bool) & frame["method"].isin([left, right])
    ]
    wide = subset.pivot(index="world_key", columns="method", values="feasible").dropna()
    differences = wide[left].astype(int).to_numpy() - wide[right].astype(int).to_numpy()
    estimate, low, high = bootstrap_ci(
        differences,
        resamples=int(config["analysis"]["bootstrap_resamples"]),
        seed=stable_seed(int(config["analysis"]["bootstrap_seed"]), left, right, "risk"),
        statistic="mean",
    )
    left_only = int(((wide[left] == 1) & (wide[right] == 0)).sum())
    right_only = int(((wide[left] == 0) & (wide[right] == 1)).sum())
    mcnemar = float(stats.binomtest(left_only, left_only + right_only, 0.5).pvalue) if left_only + right_only else 1.0
    return {
        "left": left,
        "right": right,
        "worlds": len(wide),
        "risk_difference": estimate,
        "ci_low": low,
        "ci_high": high,
        "left_only": left_only,
        "right_only": right_only,
        "mcnemar_p": mcnemar,
    }


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (total - rank) * float(value)))
        adjusted[name] = running
    return adjusted


def scaling_summary(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    summary = (
        frame.groupby(["method", "N", "K"], as_index=False)
        .agg(
            runs=("world_key", "size"),
            feasibility=("feasible", "mean"),
            runtime_ms_median=("runtime_ms", "median"),
            bytes_per_agent_median=("bytes_per_agent", "median"),
            rounds_median=("rounds", "median"),
        )
    )
    fits: dict[str, Any] = {}
    for method, group in summary.groupby("method"):
        fits[method] = {}
        for metric in ("runtime_ms_median", "bytes_per_agent_median"):
            fit = stats.linregress(np.log(group["N"]), np.log(group[metric]))
            tcrit = float(stats.t.ppf(0.975, max(len(group) - 2, 1)))
            fits[method][metric] = {
                "slope": float(fit.slope),
                "ci_low": float(fit.slope - tcrit * fit.stderr),
                "ci_high": float(fit.slope + tcrit * fit.stderr),
                "r_squared": float(fit.rvalue**2),
            }
    return summary, fits


def configure_plot_style() -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 450,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 9.5,
            "axes.titlesize": 10.0,
            "axes.labelsize": 9.3,
            "axes.linewidth": 0.7,
            "axes.edgecolor": "#50555C",
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 8.0,
            "grid.color": "#DDE2E8",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def finish_axes(axis: plt.Axes) -> None:
    axis.grid(True, axis="both", zorder=0)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)


def plot_family(summary: pd.DataFrame, path: Path) -> None:
    configure_plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 5.0), constrained_layout=True)
    indexed = summary.set_index("method")
    hierarchy = indexed.loc[list(HIERARCHY_ORDER)].reset_index()
    orders = np.arange(1, 4)
    colors = [COLORS[method] for method in hierarchy["method"]]

    gap = 100 * hierarchy["gap_median"].to_numpy(float)
    gap_low = 100 * hierarchy["gap_low"].to_numpy(float)
    gap_high = 100 * hierarchy["gap_high"].to_numpy(float)
    axes[0].plot(orders, gap, color="#60666E", linewidth=1.1, zorder=1)
    axes[0].errorbar(
        orders,
        gap,
        yerr=np.vstack([gap - gap_low, gap_high - gap]),
        fmt="none",
        ecolor="#89929D",
        elinewidth=1.3,
        capsize=3,
        zorder=2,
    )
    axes[0].scatter(orders, gap, c=colors, s=58, edgecolor="white", linewidth=0.8, zorder=3)
    for order, value, label in zip(orders, gap, ("BR", "2BR", "C3"), strict=True):
        axes[0].annotate(label, (order, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)
    axes[0].set_xticks(orders, ["1", "2", "3"])
    axes[0].set_xlabel("Orden máximo de desviación h")
    axes[0].set_ylabel("Brecha mediana frente al MILP (%)")
    axes[0].set_title("a  Brecha frente al oráculo")
    finish_axes(axes[0])
    axes[0].yaxis.set_major_formatter(FuncFormatter(spanish_tick))

    risk = 100 * (1.0 - hierarchy["feasibility"].to_numpy(float))
    risk_low = 100 * (1.0 - hierarchy["feasibility_high"].to_numpy(float))
    risk_high = 100 * (1.0 - hierarchy["feasibility_low"].to_numpy(float))
    axes[1].plot(orders, risk, color="#60666E", linewidth=1.1, zorder=1)
    axes[1].errorbar(
        orders,
        risk,
        yerr=np.vstack([risk - risk_low, risk_high - risk]),
        fmt="none",
        ecolor="#89929D",
        elinewidth=1.3,
        capsize=3,
        zorder=2,
    )
    axes[1].scatter(orders, risk, c=colors, s=58, edgecolor="white", linewidth=0.8, zorder=3)
    axes[1].set_xticks(orders, ["1", "2", "3"])
    axes[1].set_xlabel("Orden máximo de desviación h")
    axes[1].set_ylabel("Riesgo de infactibilidad (%)")
    axes[1].set_title("b  Tasa de infactibilidad")
    finish_axes(axes[1])
    axes[1].yaxis.set_major_formatter(FuncFormatter(spanish_tick))

    comparison = indexed.loc[[*HIERARCHY_ORDER, "geo_qpg_d"]].reset_index()
    hierarchy_points = comparison.iloc[:3]
    axes[2].plot(
        hierarchy_points["bytes_per_agent_median"],
        100 * hierarchy_points["gap_median"],
        color="#60666E",
        linewidth=1.0,
        zorder=1,
    )
    labels = ("BR · h=1", "2BR · h=2", "C3 · h=3", "DMIS+TX · h≤2")
    offsets = ((6, 5), (6, 5), (6, -11), (6, 6))
    for (_, row), label, (dx, dy) in zip(comparison.iterrows(), labels, offsets, strict=True):
        marker = "D" if row["method"] == "geo_qpg_d" else "o"
        axes[2].scatter(
            row["bytes_per_agent_median"],
            100 * row["gap_median"],
            s=62,
            marker=marker,
            color=COLORS[row["method"]],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        axes[2].annotate(
            label,
            (row["bytes_per_agent_median"], 100 * row["gap_median"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=7.5,
        )
    axes[2].set_xscale("log")
    axes[2].set_xlabel("Bytes/AMR, mediana (log)")
    axes[2].set_ylabel("Brecha mediana (%)")
    axes[2].set_title("c  Coste de comunicación")
    finish_axes(axes[2])
    axes[2].xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[2].yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    fig.suptitle("")
    save_figure(fig, path)


def plot_architecture(frame: pd.DataFrame, path: Path) -> None:
    configure_plot_style()
    subset = frame[
        frame["method"].isin(["geo_qpg_cf", "geo_qpg_d"])
        & frame["oracle_feasible"].astype(bool)
    ]
    metrics = ["bytes_per_agent", "runtime_ms"]
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 4.4), constrained_layout=True)
    for axis, metric, label in zip(
        axes[:2], metrics, ["Diferencia de bytes/AMR", "Diferencia de tiempo (ms)"], strict=True
    ):
        wide = subset.pivot(index="world_key", columns="method", values=metric).dropna()
        differences = wide["geo_qpg_d"] - wide["geo_qpg_cf"]
        scenario = subset.drop_duplicates("world_key").set_index("world_key")["scenario"]
        rows = []
        for name in SCENARIO_LABELS:
            values = differences[scenario.loc[differences.index].eq(name)]
            estimate, low, high = bootstrap_ci(values, resamples=2500, seed=stable_seed(71, metric, name))
            rows.append((SCENARIO_LABELS[name], estimate, low, high))
        y = np.arange(len(rows))
        estimates = np.array([row[1] for row in rows])
        axis.errorbar(
            estimates,
            y,
            xerr=np.vstack([[row[1] - row[2] for row in rows], [row[3] - row[1] for row in rows]]),
            fmt="o",
            color=COLORS["geo_qpg_d"],
            ecolor=COLORS["geo_qpg_d"],
            capsize=2.5,
        )
        axis.axvline(0, color="#202124", linewidth=0.8)
        axis.set_yticks(y, [row[0] for row in rows] if axis is axes[0] else [])
        axis.invert_yaxis()
        axis.set_xlabel(label + "\nDMIS+TX − CF global")
        finish_axes(axis)
        axis.xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    dmis = subset[subset["method"] == "geo_qpg_d"]
    components = pd.Series(
        {
            "Propuesta/estado/updates": float((dmis["messages"] - dmis["arbitration_messages"] - dmis["transaction_messages"]).median()),
            "Arbitraje DMIS": float(dmis["arbitration_messages"].median()),
            "Prepare/commit": float(dmis["transaction_messages"].median()),
        }
    )
    axes[2].barh(np.arange(len(components)), components.values, color=["#AAB2BC", "#E2A93B", COLORS["geo_qpg_d"]])
    axes[2].set_yticks(np.arange(len(components)), components.index)
    axes[2].invert_yaxis()
    axes[2].set_xlabel("Mensajes medianos por mundo")
    axes[2].set_title("c  Reparto de los mensajes")
    finish_axes(axes[2])
    axes[2].xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[0].set_title("a  Sobrecoste de comunicación")
    axes[1].set_title("b  Diferencia de cómputo observado")
    fig.suptitle("Ablación arquitectónica · efecto de retirar el orden global", fontsize=11, fontweight="bold")
    save_figure(fig, path)


def plot_dpop(frame: pd.DataFrame, path: Path) -> None:
    configure_plot_style()
    dpop = frame[frame["method"] == "dpop_exact_small"].copy()
    qpg = frame[frame["method"].isin(["geo_qpg_u", "geo_qpg_p", "geo_qpg_c3", "geo_qpg_d"])]
    summary = qpg.groupby(["method", "N"], as_index=False).agg(gap=("optimality_gap", "median"))
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.15), constrained_layout=True)
    entries = dpop.groupby("N", as_index=False)["utility_entries"].median()
    axes[0].plot(entries["N"], entries["utility_entries"], "o-", color=COLORS["dpop_exact_small"], linewidth=1.6)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Robots N")
    axes[0].set_ylabel("Entradas medianas en mensajes UTIL (log)")
    axes[0].set_title("a  La exactitud distribuye la tabla, no la elimina")
    finish_axes(axes[0])
    for method, group in summary.groupby("method"):
        axes[1].plot(group["N"], 100 * group["gap"], marker="o", linewidth=1.4, color=COLORS[method], label=LABELS[method])
    axes[1].axhline(0, color=COLORS["milp_highs"], linewidth=1.0, label="MILP = DPOP")
    axes[1].set_xlabel("Robots N")
    axes[1].set_ylabel("Brecha mediana frente al óptimo (%)")
    axes[1].set_title("b  Qué se pierde al limitar el vecindario")
    axes[1].legend(frameon=False, ncol=2)
    finish_axes(axes[1])
    axes[0].xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[0].yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[1].xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[1].yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    fig.suptitle("Referencia exacta para instancias pequeñas", fontsize=11, fontweight="bold")
    save_figure(fig, path)


def plot_scaling(summary: pd.DataFrame, fits: Mapping[str, Any], path: Path) -> None:
    configure_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.15), constrained_layout=True)
    for method, group in summary.groupby("method"):
        label = (
            f"{LABELS[method]}  b="
            f"{spanish_number(fits[method]['runtime_ms_median']['slope'], 2)}"
        )
        axes[0].plot(group["N"], group["runtime_ms_median"], "o-", color=COLORS[method], linewidth=1.5, label=label)
        label_bytes = (
            f"{LABELS[method]}  b="
            f"{spanish_number(fits[method]['bytes_per_agent_median']['slope'], 2)}"
        )
        axes[1].plot(group["N"], group["bytes_per_agent_median"], "o-", color=COLORS[method], linewidth=1.5, label=label_bytes)
    axes[0].set_ylabel("Tiempo mediano (ms, log)")
    axes[1].set_ylabel("Bytes/AMR, mediana (log)")
    for axis, title in zip(axes, ["a  Cómputo observado", "b  Comunicación observada"], strict=True):
        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xlabel("Robots N (K=N/4)")
        axis.set_title(title)
        axis.legend(frameon=False)
        finish_axes(axis)
        axis.xaxis.set_major_formatter(FuncFormatter(spanish_tick))
        axis.yaxis.set_major_formatter(FuncFormatter(spanish_tick))
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.suptitle("Escala ejecutada · la pendiente log–log describe este rango, no prueba complejidad", fontsize=10.5, fontweight="bold")
    save_figure(fig, path)


def population_context(config: Mapping[str, Any]) -> pd.DataFrame:
    section = config["population_context"]
    source = pd.read_csv(REPOSITORY_ROOT / str(section["source"]))
    return source[
        source["experiment"].eq(section["experiment"])
        & source["topology"].eq(section["topology"])
    ].copy()


def plot_population(frame: pd.DataFrame, path: Path) -> None:
    configure_plot_style()
    palette = {
        "Replicator-D-preconditioned": "#7D5BBE",
        "Smith-D-preconditioned": "#D18B20",
        "BNN-D-preconditioned": "#2B8CBE",
        "Logit-D-annealed": "#16825D",
        "BestResponse-D": "#6B7178",
    }
    short = {
        "Replicator-D-preconditioned": "Replicator-D",
        "Smith-D-preconditioned": "Smith-D",
        "BNN-D-preconditioned": "BNN-D",
        "Logit-D-annealed": "Logit-D",
        "BestResponse-D": "BR-D",
    }
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.2), constrained_layout=True)
    for method, group in frame.groupby("method"):
        group = group.sort_values("n_robots")
        axes[0].plot(group["n_robots"], 100 * group["convergence_rate"], "o-", color=palette[method], label=short[method], linewidth=1.4)
        axes[1].plot(group["n_robots"], group["rmst_rounds"], "o-", color=palette[method], label=short[method], linewidth=1.4)
    axes[0].set_ylabel("Convergencia operacional (%)")
    axes[1].set_ylabel("RMST de rondas")
    for axis, title in zip(axes, ["a  Cierre continuo", "b  Tiempo con censura"], strict=True):
        axis.set_xlabel("Robots N")
        axis.set_title(title)
        axis.legend(frameon=False, ncol=2)
        finish_axes(axis)
    fig.suptitle("Dinámicas poblacionales · evidencia histórica en otro modelo", fontsize=11, fontweight="bold")
    save_figure(fig, path)


def analyse(
    family: pd.DataFrame,
    dpop: pd.DataFrame,
    scaling: pd.DataFrame,
    population: pd.DataFrame,
    config: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    processed = output / "processed"
    figures = output / "figures"
    processed.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    summary = family_summary(family, config)
    summary.to_csv(processed / "family_summary.csv", index=False)

    contrasts = [
        paired_contrast(family, "geo_qpg_c3", "geo_qpg_u", "optimality_gap", config, feasible_common=True),
        paired_contrast(family, "geo_qpg_smith", "geo_qpg_u", "optimality_gap", config, feasible_common=True),
        paired_contrast(family, "geo_qpg_lll", "geo_qpg_u", "optimality_gap", config, feasible_common=True),
        paired_contrast(family, "geo_qpg_d", "geo_qpg_cf", "optimality_gap", config, feasible_common=True),
        paired_contrast(family, "geo_qpg_d", "geo_qpg_cf", "bytes_per_agent", config),
        paired_contrast(family, "geo_qpg_d", "geo_qpg_cf", "runtime_ms", config),
    ]
    contrast_frame = pd.DataFrame(contrasts)
    adjusted = holm_adjust(
        {
            f"{row.left}:{row.right}:{row.metric}": row.wilcoxon_p
            for row in contrast_frame.itertuples()
            if row.metric == "optimality_gap"
        }
    )
    contrast_frame["holm_p"] = [
        adjusted.get(f"{row.left}:{row.right}:{row.metric}", np.nan)
        for row in contrast_frame.itertuples()
    ]
    contrast_frame.to_csv(processed / "paired_contrasts.csv", index=False)
    risk = pd.DataFrame(
        [
            risk_difference(family, "geo_qpg_c3", "geo_qpg_u", config),
            risk_difference(family, "geo_qpg_smith", "geo_qpg_u", config),
            risk_difference(family, "geo_qpg_lll", "geo_qpg_u", config),
            risk_difference(family, "geo_qpg_d", "geo_qpg_cf", config),
        ]
    )
    risk.to_csv(processed / "paired_risk_differences.csv", index=False)

    dpop_exact = dpop[dpop["method"] == "dpop_exact_small"].set_index("world_key")
    milp = dpop[dpop["method"] == "milp_highs"].set_index("world_key")
    dpop_keys = dpop_exact.index.intersection(milp.index)
    feasibility_matches = int(
        (dpop_exact.loc[dpop_keys, "feasible"].astype(bool) == milp.loc[dpop_keys, "feasible"].astype(bool)).sum()
    )
    certified = dpop_exact.loc[dpop_keys, "oracle_certified"].astype(bool) & dpop_exact.loc[dpop_keys, "feasible"].astype(bool)
    objective_errors = np.abs(
        dpop_exact.loc[dpop_keys[certified], "distance_cost"].to_numpy(float)
        - milp.loc[dpop_keys[certified], "distance_cost"].to_numpy(float)
    )
    dpop_metrics = {
        "worlds": len(dpop_keys),
        "feasibility_matches": feasibility_matches,
        "certified_objective_worlds": int(certified.sum()),
        "max_absolute_objective_error": float(np.max(objective_errors, initial=0.0)),
        "max_utility_entries": int(dpop_exact["utility_entries"].max()),
        "max_payload_bytes": int(dpop_exact["bytes"].max()),
    }
    dpop.groupby(["method", "N"], as_index=False).agg(
        runs=("world_key", "size"),
        feasibility=("feasible", "mean"),
        gap_median=("optimality_gap", "median"),
        runtime_ms_median=("runtime_ms", "median"),
        bytes_median=("bytes", "median"),
    ).to_csv(processed / "dpop_summary.csv", index=False)

    scale_summary, fits = scaling_summary(scaling)
    scale_summary.to_csv(processed / "scaling_summary.csv", index=False)
    population.to_csv(processed / "population_context.csv", index=False)

    plot_family(summary, figures / "n4_family_comparison")
    plot_architecture(family, figures / "n4_architecture_ablation")
    plot_dpop(dpop, figures / "n4_dpop_exactness")
    plot_scaling(scale_summary, fits, figures / "n4_scaling")
    plot_population(population, figures / "n4_population_context")

    metrics = {
        "campaign_id": config["campaign_id"],
        "family_worlds": int(family["world_key"].nunique()),
        "family_rows": len(family),
        "family_summary": summary.set_index("method").to_dict(orient="index"),
        "paired_contrasts": contrasts,
        "risk_differences": risk.to_dict(orient="records"),
        "dpop": dpop_metrics,
        "dpop_summary": dpop.groupby(["method", "N"], as_index=False).agg(
            runs=("world_key", "size"),
            feasibility=("feasible", "mean"),
            gap_median=("optimality_gap", "median"),
            runtime_ms_median=("runtime_ms", "median"),
            bytes_median=("bytes", "median"),
        ).to_dict(orient="records"),
        "scaling_summary": scale_summary.to_dict(orient="records"),
        "scaling_fits": fits,
        "population_context_rows": len(population),
        "population_context": population[
            [
                "method",
                "n_robots",
                "runs",
                "convergence_rate",
                "convergence_wilson_low",
                "convergence_wilson_high",
                "rmst_rounds",
                "median_MILP_gap",
            ]
        ].to_dict(orient="records"),
    }
    write_json(output / "key_metrics.json", metrics)
    write_latex_artifacts(output, summary, contrast_frame, risk, dpop_metrics, fits)
    return metrics


def latex_number(value: float, digits: int = 2) -> str:
    if not np.isfinite(value):
        return "--"
    return latex_decimal(value, digits)


def write_latex_artifacts(
    output: Path,
    summary: pd.DataFrame,
    contrasts: pd.DataFrame,
    risk: pd.DataFrame,
    dpop: Mapping[str, Any],
    fits: Mapping[str, Any],
) -> None:
    processed = output / "processed"
    rows = [
        "\\begin{tabular}{@{}lrrrr@{}}",
        "\\toprule",
        "Método & Fact. (\\%) & Brecha med. (\\%) & bytes/robot & tiempo (ms) \\\\",
        "\\midrule",
    ]
    for method in METHOD_ORDER:
        row = summary.loc[summary["method"] == method].iloc[0]
        rows.append(
            f"{LABELS[method]} & {latex_decimal(100*row['feasibility'], 1)} & "
            f"{latex_decimal(100*row['gap_median'], 1)} & "
            f"{latex_integer(row['bytes_per_agent_median'])} & "
            f"{latex_decimal(row['runtime_ms_median'], 1)} \\\\"
        )
    rows.extend(["\\bottomrule", "\\end{tabular}"])
    (processed / "n4_method_comparison.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")

    look = summary.set_index("method")
    contrast_lookup = {
        (row.left, row.right, row.metric): row for row in contrasts.itertuples()
    }
    risk_lookup = {(row.left, row.right): row for row in risk.itertuples()}
    d_c3 = contrast_lookup[("geo_qpg_c3", "geo_qpg_u", "optimality_gap")]
    d_arch = contrast_lookup[("geo_qpg_d", "geo_qpg_cf", "bytes_per_agent")]
    r_arch = risk_lookup[("geo_qpg_d", "geo_qpg_cf")]
    macros = [
        f"\\newcommand{{\\NFourFamilyWorlds}}{{{int(look.iloc[0]['worlds'])}}}",
        f"\\newcommand{{\\NFourDFeasPct}}{{{latex_decimal(100*look.loc['geo_qpg_d','feasibility'], 2)}}}",
        f"\\newcommand{{\\NFourDGapPct}}{{{latex_decimal(100*look.loc['geo_qpg_d','gap_median'], 2)}}}",
        f"\\newcommand{{\\NFourCThreeGapDeltaPct}}{{{latex_decimal(100*d_c3.median_difference, 2)}}}",
        f"\\newcommand{{\\NFourDBytesDelta}}{{{latex_integer(d_arch.median_difference)}}}",
        f"\\newcommand{{\\NFourDRiskDeltaPct}}{{{latex_decimal(100*r_arch.risk_difference, 2)}}}",
        f"\\newcommand{{\\NFourDpopWorlds}}{{{int(dpop['worlds'])}}}",
        f"\\newcommand{{\\NFourDpopMaxError}}{{{latex_scientific(dpop['max_absolute_objective_error'])}}}",
        f"\\newcommand{{\\NFourDpopMaxEntries}}{{{latex_integer(dpop['max_utility_entries'])}}}",
        f"\\newcommand{{\\NFourScaleSlopeD}}{{{latex_decimal(fits['geo_qpg_d']['runtime_ms_median']['slope'], 2)}}}",
        f"\\newcommand{{\\NFourScaleSlopeBR}}{{{latex_decimal(fits['geo_qpg_u']['runtime_ms_median']['slope'], 2)}}}",
    ]
    (processed / "n4_results_macros.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")


def freeze_raw(output: Path, frames: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    for name, frame in frames.items():
        path = raw / f"{name}.csv"
        frame.to_csv(path, index=False)
        records[name] = {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "rows": len(frame),
            "sha256": sha256_file(path),
        }
    return records


def build_manifest(
    output: Path,
    config_path: Path,
    config: Mapping[str, Any],
    frozen: Mapping[str, Any],
) -> None:
    sources = [
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "src" / "viu_mrob_tfm" / "sp1_n4" / "geo_qpg.py",
        REPOSITORY_ROOT / "src" / "viu_mrob_tfm" / "sp1_n4" / "dpop_exact.py",
        config_path.resolve(),
    ]
    artifacts = [
        {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    ]
    write_json(
        output / "manifest.json",
        {
            "schema_version": "sp1-n4-family-package-v2",
            "campaign_id": config["campaign_id"],
            "config": {
                "path": config_path.relative_to(REPOSITORY_ROOT).as_posix(),
                "sha256": sha256_file(config_path),
            },
            "git": git_state(),
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": __import__("scipy").__version__,
                "matplotlib": mpl.__version__,
            },
            "sources": [
                {"path": path.relative_to(REPOSITORY_ROOT).as_posix(), "sha256": sha256_file(path)}
                for path in sources
            ],
            "frozen_raw": frozen,
            "limitations": list(config["limitations"]),
            "artifacts": artifacts,
        },
    )


def write_report(output: Path, metrics: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    summary = pd.read_csv(output / "processed" / "family_summary.csv")
    lines = [
        "# SP1.N4 — familia Geo-QPG distribuida",
        "",
        f"La comparación atómica contiene {metrics['family_worlds']} mundos pareados y {metrics['family_rows']} filas.",
        "QPG-CF se conserva como ablación con orden global; Geo-QPG-DMIS+TX es la variante distribuida principal.",
        "",
        "## Resultados por método",
        "",
        summary.to_markdown(index=False),
        "",
        "## Exactitud pequeña",
        "",
        f"DPOP y MILP coincidieron en factibilidad en {metrics['dpop']['feasibility_matches']}/{metrics['dpop']['worlds']} mundos. ",
        f"El error objetivo máximo fue {metrics['dpop']['max_absolute_objective_error']:.3e}.",
        "",
        "## Límites",
        "",
    ]
    lines.extend(f"- {item}" for item in config["limitations"])
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_integrity(
    family: pd.DataFrame, worlds: pd.DataFrame, dpop: pd.DataFrame, scaling: pd.DataFrame
) -> list[str]:
    problems: list[str] = []
    counts = family.groupby("world_key")["method"].nunique()
    if not (counts == len(METHOD_ORDER)).all():
        problems.append("family: not every world contains all ten methods")
    if family.duplicated(["world_key", "method"]).any():
        problems.append("family: duplicate world-method rows")
    if worlds["world_key"].duplicated().any():
        problems.append("family: duplicate worlds")
    proposed = family[family["method"].str.startswith("geo_qpg")]
    if (proposed["robot_conflict"] != 0).any():
        problems.append("family: atomic exclusivity violation")
    strict = proposed[~proposed["method"].eq("geo_qpg_lll")]
    if not strict["potential_monotone"].astype("boolean").fillna(False).all():
        problems.append("family: strict method violated monotonicity")
    dpop_counts = dpop.groupby("world_key")["method"].nunique()
    expected_dpop = dpop["method"].nunique()
    if not (dpop_counts == expected_dpop).all():
        problems.append("DPOP: incomplete method blocks")
    scaling_counts = scaling.groupby("world_key")["method"].nunique()
    if not (scaling_counts == scaling["method"].nunique()).all():
        problems.append("scaling: incomplete method blocks")
    numeric = scaling[["runtime_ms", "rounds", "messages", "bytes"]].to_numpy(float)
    if not np.isfinite(numeric).all() or (numeric < 0).any():
        problems.append("scaling: invalid numeric metrics")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--analysis-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config, smoke=args.smoke)
    output = args.output_dir.with_name(args.output_dir.name + "_smoke") if args.smoke else args.output_dir
    raw = output / "raw"
    population = population_context(config)
    if args.analysis_only:
        family = pd.read_csv(raw / "e4_family_runs.csv")
        dpop = pd.read_csv(raw / "e5_dpop_runs.csv")
        scaling = pd.read_csv(raw / "e6_scaling_runs.csv")
        metrics = analyse(family, dpop, scaling, population, config, output)
        write_report(output, metrics, config)
        manifest_path = output / "manifest.json"
        if manifest_path.exists():
            frozen = json.loads(manifest_path.read_text(encoding="utf-8"))["frozen_raw"]
        else:
            frozen = {
                path.stem: {
                    "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                    "rows": int(len(pd.read_csv(path))),
                    "sha256": sha256_file(path),
                }
                for path in sorted(raw.glob("*.csv"))
            }
        build_manifest(output, args.config, config, frozen)
        print(f"analysis: {output.resolve()}")
        return
    if raw.exists() and any(raw.glob("*.csv")):
        raise SystemExit(f"{raw} already contains RAW; use --analysis-only or a new output")

    print(f"campaign {config['campaign_id']}")
    print(f"commit   {git_state()['commit']} dirty={git_state()['tree_dirty']}")
    family, worlds = run_family_extension(config)
    dpop = run_dpop_small(config)
    scaling = run_scaling(config)
    problems = check_integrity(family, worlds, dpop, scaling)
    if problems:
        raise SystemExit("integrity failed:\n- " + "\n- ".join(problems))
    frozen = freeze_raw(
        output,
        {
            "e4_family_runs": family,
            "e4_family_worlds": worlds,
            "e5_dpop_runs": dpop,
            "e6_scaling_runs": scaling,
        },
    )
    metrics = analyse(family, dpop, scaling, population, config, output)
    write_report(output, metrics, config)
    build_manifest(output, args.config, config, frozen)
    print(f"package  {(output / 'manifest.json').resolve()}")


if __name__ == "__main__":
    main()
