"""Run SP1.N4: atomic Geo-QPG on the frozen N2/N3 recruitment problem.

E1 is the invariant battery in ``tests/test_sp1_n4.py``.  E2 replays the N3
worlds for descriptive continuity.  E3 opens a disjoint seed stream and runs
the three N3 references and three Geo-QPG variants on identical worlds.

The script never edits N1--N3 data.  A non-smoke output containing RAW files is
immutable: regenerating it requires a new campaign id and output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
from scipy import stats


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import sp1_a1_hungarian as homogeneous  # noqa: E402
import sp1_n2_oracle as n2_oracle  # noqa: E402
from sp1_n3_confirmatory import solve_oracle  # noqa: E402
from viu_mrob_tfm.sp1_n3.graph import (  # noqa: E402
    adjacency_for_regime,
    critical_radius,
    graph_metrics,
)
from viu_mrob_tfm.sp1_n3.runner import (  # noqa: E402
    METHODS as N3_METHODS,
    METHOD_LABELS as N3_LABELS,
    run_method as run_n3_method,
)
from viu_mrob_tfm.sp1_n3.worlds import World, make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import (  # noqa: E402
    LEGACY_METHODS as N4_LEGACY_METHODS,
    METHODS as N4_METHODS,
    METHOD_LABELS as N4_LABELS,
    run_geo_qpg,
)


DEFAULT_CONFIG = REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n4_confirmatory_v1.yaml"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n4_v1"
ALL_METHODS = tuple(N3_METHODS) + tuple(N4_LEGACY_METHODS)
METHOD_LABELS = {**N3_LABELS, **N4_LABELS}
METHOD_COLORS = {
    "capacity_cbba_rb": "#6F4AA8",
    "weighted_grape": "#2673B8",
    "weighted_pair_grape": "#45A2D8",
    "geo_qpg_u": "#D97820",
    "geo_qpg_p": "#D94A35",
    "geo_qpg_cf": "#18855B",
}
METHOD_MARKERS = {
    "capacity_cbba_rb": "s",
    "weighted_grape": "o",
    "weighted_pair_grape": "D",
    "geo_qpg_u": "^",
    "geo_qpg_p": "P",
    "geo_qpg_cf": "*",
}
SCENARIO_LABELS = {
    "uniform": "Aleatorio",
    "clustered": "Agrupado",
    "separated": "Separado",
    "ring": "Anillo",
    "corridor": "Pasillo",
}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=_json_default),
        encoding="utf-8",
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return value.as_posix()
    raise TypeError(f"cannot serialize {type(value)!r}")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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
        "tree_dirty": bool(run("git", "status", "--porcelain")),
        "branch": run("git", "branch", "--show-current") or "unknown",
    }


def load_config(path: Path, *, smoke: bool) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if smoke:
        config["campaign_id"] += "_SMOKE"
        config["replay"]["max_worlds"] = 8
        confirmatory = config["confirmatory"]
        confirmatory.update(
            base_seed=2026081391,
            capacity_cv=[0.00, 0.65],
            pressure=[0.85],
            scenarios=["uniform", "corridor"],
            seeds_per_cell=2,
            max_rounds_qpg=512,
        )
    return config


def progress(label: str, index: int, total: int) -> None:
    if index == total or index % max(1, total // 20) == 0:
        print(f"  {label}: {index}/{total}", flush=True)


def world_from_row(row: pd.Series, *, q_bar: float, workspace: tuple[float, float], alpha: float) -> World:
    return make_world(
        world_id=str(row["world_id"]),
        robot_count=int(row["N"]),
        load_count=int(row["K"]),
        q_bar=float(q_bar),
        cv=float(row["capacity_cv"]),
        pressure=float(row["pressure"]),
        scenario=str(row["scenario"]),
        workspace=workspace,
        seed=int(row["world_seed"]),
        alpha=float(alpha),
    )


def confirmatory_world(
    config: Mapping[str, Any], *, scenario: str, cv: float, pressure: float, replicate: int
) -> tuple[str, World]:
    section = config["confirmatory"]
    seed = homogeneous.stable_seed(
        int(section["base_seed"]), "n4-confirmatory", scenario, pressure, replicate
    )
    world = make_world(
        world_id=f"{scenario}-p{pressure}-r{replicate}",
        robot_count=int(section["robot_count"]),
        load_count=int(section["load_count"]),
        q_bar=float(section["q_bar_kg"]),
        cv=float(cv),
        pressure=float(pressure),
        scenario=scenario,
        workspace=tuple(float(x) for x in section["workspace_m"]),
        seed=seed,
        alpha=float(section["demand_split_alpha"]),
    )
    key = f"E3:{scenario}:p{pressure}:cv{cv}:r{replicate}"
    return key, world


def world_row(world_key: str, world: World) -> dict[str, Any]:
    return {
        "world_key": world_key,
        "world_id": world.world_id,
        "world_seed": world.seed,
        "world_digest": world.digest(),
        "scenario": world.scenario,
        "scenario_label": SCENARIO_LABELS.get(world.scenario, world.scenario),
        "capacity_cv": world.capacity_cv,
        "realized_cv": world.realized_cv,
        "pressure": world.pressure,
        "N": world.n_robots,
        "K": world.n_loads,
        "total_capacity": float(world.capacities.sum()),
        "total_demand": float(world.demands.sum()),
        "critical_radius_m": critical_radius(world.robot_positions),
    }


def graph_row(world_key: str, world: World, adjacency: np.ndarray, regime: str) -> dict[str, Any]:
    metrics = graph_metrics(adjacency).as_dict()
    return {
        "world_key": world_key,
        "graph_regime": regime,
        **{f"graph_{key}": value for key, value in metrics.items()},
    }


def method_row(
    *,
    campaign_id: str,
    experiment: str,
    world_key: str,
    world: World,
    regime: str,
    adjacency: np.ndarray,
    method: str,
    oracle_row: Mapping[str, Any],
    max_rounds_qpg: int,
) -> dict[str, Any]:
    if method in N3_METHODS:
        record = run_n3_method(world, adjacency, method, regime=regime)
        certificate = record.certificate
        observation = record.observation
        metrics: dict[str, Any] = {
            "algorithm_status": observation.algorithm_status,
            "terminal_phase": "N/A",
            "raw_certificate": certificate.status,
            "distance_cost": certificate.distance_cost,
            "capacity_deficit": certificate.total_deficit,
            "robot_conflict": certificate.conflicts,
            "excess_capacity": certificate.excess_capacity,
            "assigned_robots": certificate.assigned_robots,
            "max_coalition_size": max(certificate.coalition_sizes, default=0),
            "unserved_loads": certificate.unserved_loads,
            "rounds": observation.rounds,
            "messages": observation.messages,
            "bytes": observation.bytes_sent,
            "runtime_ms": record.runtime_ms,
            "commits": np.nan,
            "quota_commits": np.nan,
            "geometry_commits": np.nan,
            "rejected_stale": np.nan,
            "rejected_conflict": np.nan,
            "max_parallel_commits": np.nan,
            "potential_monotone": np.nan,
            "unilateral_local_minimum": np.nan,
            "pair_local_minimum": np.nan,
            "feasible": certificate.feasible,
        }
    else:
        result = run_geo_qpg(
            world, adjacency, method, max_rounds=int(max_rounds_qpg)
        )
        certificate = result.certificate
        payload = result.as_dict()
        metrics = {
            "algorithm_status": payload["algorithm_status"],
            "terminal_phase": payload["terminal_phase"],
            "raw_certificate": certificate.status,
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
            "runtime_ms": result.runtime_ms,
            "commits": result.commits,
            "quota_commits": result.quota_commits,
            "geometry_commits": result.geometry_commits,
            "rejected_stale": result.rejected_stale,
            "rejected_conflict": result.rejected_conflict,
            "max_parallel_commits": result.max_parallel_commits,
            "potential_monotone": result.potential_monotone,
            "unilateral_local_minimum": result.unilateral_local_minimum,
            "pair_local_minimum": result.pair_local_minimum,
            "feasible": certificate.feasible,
        }
    gap = float("nan")
    if (
        certificate.feasible
        and bool(oracle_row["oracle_certified"])
        and float(oracle_row["oracle_objective"]) > 0.0
    ):
        gap = (
            float(certificate.distance_cost) - float(oracle_row["oracle_objective"])
        ) / float(oracle_row["oracle_objective"])
    graph = graph_metrics(adjacency).as_dict()
    return {
        "campaign_id": campaign_id,
        "experiment": experiment,
        "world_key": world_key,
        "world_id": world.world_id,
        "world_seed": world.seed,
        "scenario": world.scenario,
        "N": world.n_robots,
        "K": world.n_loads,
        "capacity_cv": world.capacity_cv,
        "pressure": world.pressure,
        "graph_regime": regime,
        "method": method,
        "method_family": "N3_REFERENCE" if method in N3_METHODS else "N4_PROPOSED",
        **metrics,
        "messages_per_agent": float(metrics["messages"]) / world.n_robots,
        "bytes_per_agent": float(metrics["bytes"]) / world.n_robots,
        **oracle_row,
        "optimality_gap": gap,
        **{f"graph_{key}": value for key, value in graph.items()},
    }


def replay_n3(config: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    replay = config["replay"]
    source = REPOSITORY_ROOT / str(replay["source_dir"])
    source_runs = pd.read_csv(source / "raw" / "e2_runs.csv")
    source_worlds = pd.read_csv(source / "raw" / "worlds.csv")
    source_worlds = source_worlds[source_worlds["world_key"].str.startswith("E2:")]
    max_worlds = replay.get("max_worlds")
    if max_worlds is not None:
        source_worlds = source_worlds.head(int(max_worlds)).copy()
        source_runs = source_runs[source_runs["world_key"].isin(source_worlds["world_key"])]
    baseline = source_runs.copy()
    baseline["feasible"] = baseline["raw_certificate"].eq("FEASIBLE")
    baseline["method_family"] = "N3_REFERENCE"
    baseline["terminal_phase"] = "N/A"
    for column in (
        "commits",
        "quota_commits",
        "geometry_commits",
        "rejected_stale",
        "rejected_conflict",
        "max_parallel_commits",
        "potential_monotone",
        "unilateral_local_minimum",
        "pair_local_minimum",
    ):
        baseline[column] = np.nan

    q_bar = float(config["confirmatory"]["q_bar_kg"])
    workspace = tuple(float(x) for x in config["confirmatory"]["workspace_m"])
    alpha = float(config["confirmatory"]["demand_split_alpha"])
    regime = str(config["confirmatory"]["graph_regime"])
    max_rounds = int(config["confirmatory"]["max_rounds_qpg"])
    qpg_rows: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(source_worlds.iterrows(), 1):
        world = world_from_row(row, q_bar=q_bar, workspace=workspace, alpha=alpha)
        if world.digest() != str(row["world_digest"]):
            raise RuntimeError(f"N3 replay digest mismatch for {row['world_key']}")
        adjacency = adjacency_for_regime(world.robot_positions, regime)
        oracle_source = source_runs.loc[source_runs["world_key"] == row["world_key"]].iloc[0]
        oracle_row = {
            "oracle_status": oracle_source["oracle_status"],
            "oracle_objective": float(oracle_source["oracle_objective"]),
            "oracle_bound": float(oracle_source["oracle_bound"]),
            "oracle_gap": float(oracle_source["oracle_gap"]),
            "oracle_runtime_s": float(oracle_source["oracle_runtime_s"]),
            "oracle_feasible": bool(oracle_source["oracle_feasible"]),
            "oracle_certified": bool(oracle_source["oracle_certified"]),
        }
        for method in tuple(config["methods"]["proposed"]):
            qpg_rows.append(
                method_row(
                    campaign_id=str(config["campaign_id"]),
                    experiment="E2_REPLAY",
                    world_key=str(row["world_key"]),
                    world=world,
                    regime=regime,
                    adjacency=adjacency,
                    method=method,
                    oracle_row=oracle_row,
                    max_rounds_qpg=max_rounds,
                )
            )
        progress("E2 replay", index, len(source_worlds))
    baseline["experiment"] = "E2_REPLAY"
    # Align the historical deficit field with the N4 schema.
    if "capacity_deficit" not in baseline and "total_deficit" in baseline:
        baseline["capacity_deficit"] = baseline["total_deficit"]
    return pd.concat([baseline, pd.DataFrame(qpg_rows)], ignore_index=True), source_worlds


def run_confirmatory(
    config: Mapping[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    section = config["confirmatory"]
    cells = [
        (scenario, float(cv), float(pressure), replicate)
        for scenario in section["scenarios"]
        for cv in section["capacity_cv"]
        for pressure in section["pressure"]
        for replicate in range(int(section["seeds_per_cell"]))
    ]
    regime = str(section["graph_regime"])
    methods = tuple(config["methods"]["baselines"]) + tuple(config["methods"]["proposed"])
    runs: list[dict[str, Any]] = []
    worlds: list[dict[str, Any]] = []
    graphs: list[dict[str, Any]] = []
    oracles: list[dict[str, Any]] = []
    for index, (scenario, cv, pressure, replicate) in enumerate(cells, 1):
        key, world = confirmatory_world(
            config,
            scenario=scenario,
            cv=cv,
            pressure=pressure,
            replicate=replicate,
        )
        adjacency = adjacency_for_regime(world.robot_positions, regime)
        oracle_row = solve_oracle(world, float(section["oracle_time_limit_s"]))
        worlds.append(world_row(key, world))
        graphs.append(graph_row(key, world, adjacency, regime))
        oracles.append({"world_key": key, **oracle_row})
        for method in methods:
            runs.append(
                method_row(
                    campaign_id=str(config["campaign_id"]),
                    experiment="E3_CONFIRMATORY",
                    world_key=key,
                    world=world,
                    regime=regime,
                    adjacency=adjacency,
                    method=method,
                    oracle_row=oracle_row,
                    max_rounds_qpg=int(section["max_rounds_qpg"]),
                )
            )
        progress("E3 confirmatory", index, len(cells))
    return (
        pd.DataFrame(runs),
        pd.DataFrame(worlds),
        pd.DataFrame(graphs),
        pd.DataFrame(oracles),
    )


def check_integrity(
    replay: pd.DataFrame,
    confirmatory: pd.DataFrame,
    worlds: pd.DataFrame,
    methods: Iterable[str],
) -> list[str]:
    problems: list[str] = []
    methods = tuple(methods)
    for name, frame in (("replay", replay), ("confirmatory", confirmatory)):
        duplicate = frame.duplicated(["world_key", "method"]).sum()
        if duplicate:
            problems.append(f"{name}: {duplicate} duplicate world-method keys")
        counts = frame.groupby("world_key")["method"].nunique()
        if not (counts == len(methods)).all():
            problems.append(f"{name}: not every world has all {len(methods)} methods")
        if set(frame["method"].unique()) != set(methods):
            problems.append(f"{name}: method set differs from the frozen list")
        if frame[["distance_cost", "bytes", "rounds"]].isna().any().any():
            problems.append(f"{name}: missing primary metrics")
        if (frame["bytes"] < 0).any() or (frame["rounds"] < 0).any():
            problems.append(f"{name}: negative communication or rounds")
        qpg = frame[frame["method"].isin(N4_METHODS)]
        if not qpg["potential_monotone"].astype("boolean").fillna(False).all():
            problems.append(f"{name}: a QPG run violated potential monotonicity")
        if (qpg["robot_conflict"] != 0).any():
            problems.append(f"{name}: a QPG run violated atomic exclusivity")
    if worlds["world_key"].duplicated().any():
        problems.append("confirmatory worlds: duplicate world keys")
    # The spatial seed is intentionally reused across CV levels so geometry,
    # demand and graph stay paired while only the capacity stream changes.
    if worlds.duplicated(["world_seed", "capacity_cv"]).any():
        problems.append("confirmatory worlds: duplicate seed-CV pairs")
    return problems


def wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float, float]:
    if total <= 0:
        return float("nan"), float("nan"), float("nan")
    z = float(stats.norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    radius = z * np.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total**2)) / denominator
    return float(p), float(centre - radius), float(centre + radius)


def bootstrap_interval(
    values: np.ndarray,
    *,
    statistic: str,
    resamples: int,
    seed: int,
) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return float("nan"), float("nan"), float("nan")
    estimator = np.mean if statistic == "mean" else np.median
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(resamples, len(values)), replace=True)
    estimates = estimator(draws, axis=1)
    return (
        float(estimator(values)),
        float(np.quantile(estimates, 0.025)),
        float(np.quantile(estimates, 0.975)),
    )


def analyse_campaign(
    frame: pd.DataFrame,
    config: Mapping[str, Any],
    *,
    tag: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    analysis = config["analysis"]
    resamples = int(analysis["bootstrap_resamples"])
    seed = int(analysis["bootstrap_seed"])
    solvable = frame[frame["oracle_feasible"].astype(bool)].copy()
    feasibility = solvable.pivot(index="world_key", columns="method", values="feasible")
    certified = solvable[solvable["oracle_certified"].astype(bool)]
    gap_wide = certified.pivot(index="world_key", columns="method", values="optimality_gap")
    common_gap = gap_wide.dropna(subset=list(ALL_METHODS))

    rows: list[dict[str, Any]] = []
    for index, method in enumerate(ALL_METHODS):
        block = solvable[solvable["method"] == method]
        feasible_count = int(block["feasible"].astype(bool).sum())
        rate, low, high = wilson(feasible_count, len(block))
        gap = common_gap[method].to_numpy(dtype=float) if method in common_gap else np.array([])
        gap_median, gap_low, gap_high = bootstrap_interval(
            gap, statistic="median", resamples=resamples, seed=seed + index
        )
        rows.append(
            {
                "method": method,
                "label": METHOD_LABELS[method],
                "worlds": int(len(block)),
                "feasible": feasible_count,
                "feasibility_rate": rate,
                "feasibility_low": low,
                "feasibility_high": high,
                "common_gap_worlds": int(len(common_gap)),
                "common_gap_median": gap_median,
                "common_gap_low": gap_low,
                "common_gap_high": gap_high,
                "bytes_per_agent_median": float(block["bytes_per_agent"].median()),
                "bytes_per_agent_q25": float(block["bytes_per_agent"].quantile(0.25)),
                "bytes_per_agent_q75": float(block["bytes_per_agent"].quantile(0.75)),
                "messages_per_agent_median": float(block["messages_per_agent"].median()),
                "rounds_median": float(block["rounds"].median()),
                "runtime_ms_median": float(block["runtime_ms"].median()),
            }
        )
    summary = pd.DataFrame(rows)

    primary = str(config["methods"]["primary"])
    comparator = str(config["methods"]["comparator"])
    pair = solvable[solvable["method"].isin([primary, comparator])].pivot(
        index="world_key", columns="method"
    )
    risk_difference = (
        pair["feasible"][primary].astype(float)
        - pair["feasible"][comparator].astype(float)
    ).to_numpy()
    byte_difference = (
        pair["bytes_per_agent"][primary]
        - pair["bytes_per_agent"][comparator]
    ).to_numpy(dtype=float)
    rd, rd_low, rd_high = bootstrap_interval(
        risk_difference, statistic="mean", resamples=resamples, seed=seed + 101
    )
    bd, bd_low, bd_high = bootstrap_interval(
        byte_difference, statistic="median", resamples=resamples, seed=seed + 102
    )
    margin = float(config["hypotheses"]["primary_joint"]["feasibility_margin"])
    only_primary = int(np.sum(risk_difference == 1))
    only_comparator = int(np.sum(risk_difference == -1))
    discordant = only_primary + only_comparator
    mcnemar_p = (
        float(stats.binomtest(only_primary, discordant, 0.5).pvalue)
        if discordant
        else 1.0
    )
    metrics = {
        "tag": tag,
        "rows": int(len(frame)),
        "worlds": int(frame["world_key"].nunique()),
        "oracle_feasible_worlds": int(solvable["world_key"].nunique()),
        "oracle_infeasible_worlds": int(
            frame.loc[~frame["oracle_feasible"].astype(bool), "world_key"].nunique()
        ),
        "oracle_certified_worlds": int(certified["world_key"].nunique()),
        "false_feasible_on_oracle_infeasible": int(
            frame.loc[
                ~frame["oracle_feasible"].astype(bool) & frame["feasible"].astype(bool)
            ].shape[0]
        ),
        "common_gap_worlds": int(len(common_gap)),
        "primary": primary,
        "comparator": comparator,
        "paired_worlds": int(len(risk_difference)),
        "risk_difference": rd,
        "risk_difference_low": rd_low,
        "risk_difference_high": rd_high,
        "noninferiority_margin": margin,
        "feasibility_noninferior": bool(rd_low >= -margin),
        "only_primary_feasible": only_primary,
        "only_comparator_feasible": only_comparator,
        "mcnemar_p": mcnemar_p,
        "byte_difference_median": bd,
        "byte_difference_low": bd_low,
        "byte_difference_high": bd_high,
        "bytes_lower": bool(bd_high < 0.0),
        "joint_gate_passed": bool(rd_low >= -margin and bd_high < 0.0),
    }
    for _, row in summary.iterrows():
        method = str(row["method"])
        for column in (
            "feasibility_rate",
            "feasibility_low",
            "feasibility_high",
            "common_gap_median",
            "bytes_per_agent_median",
            "messages_per_agent_median",
            "rounds_median",
            "runtime_ms_median",
        ):
            metrics[f"{column}_{method}"] = float(row[column])
    primary_row = summary.set_index("method").loc[primary]
    comparator_row = summary.set_index("method").loc[comparator]
    metrics["bytes_relative_reduction"] = float(
        1.0
        - primary_row["bytes_per_agent_median"]
        / comparator_row["bytes_per_agent_median"]
    )
    metrics["rounds_relative_reduction"] = float(
        1.0 - primary_row["rounds_median"] / comparator_row["rounds_median"]
    )
    metrics["runtime_ratio"] = float(
        primary_row["runtime_ms_median"] / comparator_row["runtime_ms_median"]
    )
    for other, name in (
        ("weighted_grape", "grape"),
        ("weighted_pair_grape", "pair_grape"),
    ):
        differences = (
            common_gap[primary].to_numpy(dtype=float)
            - common_gap[other].to_numpy(dtype=float)
        )
        estimate, low, high = bootstrap_interval(
            differences,
            statistic="median",
            resamples=resamples,
            seed=seed + 201 + len(name),
        )
        nonzero = differences[~np.isclose(differences, 0.0, atol=1e-12)]
        wilcoxon_p = (
            float(stats.wilcoxon(nonzero, alternative="two-sided").pvalue)
            if len(nonzero)
            else 1.0
        )
        metrics[f"gap_difference_vs_{name}"] = estimate
        metrics[f"gap_difference_vs_{name}_low"] = low
        metrics[f"gap_difference_vs_{name}_high"] = high
        metrics[f"gap_difference_vs_{name}_wilcoxon_p"] = wilcoxon_p
    return summary, metrics


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 8.2,
            "axes.titlesize": 9.0,
            "axes.labelsize": 8.4,
            "axes.linewidth": 0.7,
            "axes.edgecolor": "#343840",
            "xtick.labelsize": 7.4,
            "ytick.labelsize": 7.4,
            "legend.fontsize": 7.0,
            "grid.color": "#D9DEE6",
            "grid.linewidth": 0.5,
            "grid.alpha": 0.8,
            "savefig.dpi": 450,
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def save_figure(figure: plt.Figure, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = [stem.with_suffix(".pdf"), stem.with_suffix(".png")]
    for path in paths:
        figure.savefig(path, facecolor="white", pad_inches=0.04)
    plt.close(figure)
    return paths


def plot_frontier(summary: pd.DataFrame, stem: Path, *, title_suffix: str) -> list[Path]:
    _style()
    figure, axes = plt.subplots(
        1, 2, figsize=(10.8, 4.25), gridspec_kw={"width_ratios": [1.18, 0.82]}
    )
    ax = axes[0]
    ax.axhspan(0.98, 1.005, color="#18855B", alpha=0.06, zorder=0)
    ax.grid(True, which="both", zorder=0)
    for _, row in summary.iterrows():
        method = str(row["method"])
        gap = max(float(row["common_gap_median"]), 0.0)
        size = 80.0 + 820.0 * min(gap, 0.55)
        ax.errorbar(
            float(row["bytes_per_agent_median"]),
            float(row["feasibility_rate"]),
            yerr=np.array(
                [[row["feasibility_rate"] - row["feasibility_low"]],
                 [row["feasibility_high"] - row["feasibility_rate"]]]
            ),
            fmt=METHOD_MARKERS[method],
            markersize=np.sqrt(size),
            color=METHOD_COLORS[method],
            markeredgecolor="white",
            markeredgewidth=0.8,
            capsize=2.8,
            linewidth=0.9,
            zorder=3,
        )
        xoff, yoff = (5, 5)
        if method in {"weighted_grape", "weighted_pair_grape"}:
            yoff = -13
        ax.annotate(
            METHOD_LABELS[method],
            (row["bytes_per_agent_median"], row["feasibility_rate"]),
            xytext=(xoff, yoff),
            textcoords="offset points",
            fontsize=6.8,
            color="#24272D",
        )
    ax.set_xscale("log")
    ax.set_ylim(0.68, 1.015)
    ax.set_xlabel("Bytes por agente, mediana (escala log)")
    ax.set_ylabel(r"$P(\mathrm{factible}\mid\mathrm{or\acute{a}culo\ factible})$")
    ax.set_title(f"Frontera comunicación--factibilidad · {title_suffix}", loc="left", fontweight="bold")
    ax.text(
        0.02,
        0.035,
        "Arriba e izquierda es preferible; el área del marcador crece con el gap MILP.",
        transform=ax.transAxes,
        fontsize=6.6,
        color="#626975",
    )

    ax = axes[1]
    x = np.arange(len(summary))
    values = 100.0 * summary["common_gap_median"].to_numpy(dtype=float)
    lower = values - 100.0 * summary["common_gap_low"].to_numpy(dtype=float)
    upper = 100.0 * summary["common_gap_high"].to_numpy(dtype=float) - values
    ax.bar(
        x,
        values,
        color=[METHOD_COLORS[str(method)] for method in summary["method"]],
        width=0.62,
        zorder=2,
    )
    ax.errorbar(x, values, yerr=[lower, upper], fmt="none", color="#24272D", capsize=2.5, linewidth=0.8, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [METHOD_LABELS[str(method)].replace("Weighted-", "W-").replace("Capacity-", "") for method in summary["method"]],
        rotation=28,
        ha="right",
    )
    ax.set_ylabel("Brecha mediana al MILP (%)")
    ax.set_title(
        f"Calidad · soporte común n={int(summary['common_gap_worlds'].iloc[0])}",
        loc="left",
        fontweight="bold",
    )
    ax.grid(True, axis="y", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    figure.subplots_adjust(wspace=0.30)
    return save_figure(figure, stem)


def plot_ablation(summary: pd.DataFrame, stem: Path) -> list[Path]:
    _style()
    block = summary[summary["method"].isin(N4_METHODS)].copy()
    figure, axes = plt.subplots(1, 3, figsize=(10.8, 3.65))
    labels = [METHOD_LABELS[str(method)].replace("Geo-", "") for method in block["method"]]
    colors = [METHOD_COLORS[str(method)] for method in block["method"]]
    panels = (
        (100.0 * block["feasibility_rate"], "Factibilidad (%)", (75, 101)),
        (block["bytes_per_agent_median"], "Bytes/agente (mediana)", None),
        (block["rounds_median"], "Rondas lógicas (mediana)", None),
    )
    for index, (ax, (values, ylabel, ylim)) in enumerate(zip(axes, panels, strict=True)):
        x = np.arange(len(block))
        bars = ax.bar(x, values, color=colors, width=0.58, zorder=2)
        ax.set_xticks(x, labels)
        ax.set_ylabel(ylabel)
        if ylim:
            ax.set_ylim(*ylim)
        ax.grid(True, axis="y", zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
        ax.text(-0.13, 1.04, f"({chr(97 + index)})", transform=ax.transAxes, fontweight="bold")
        for bar, value in zip(bars, values, strict=True):
            label = f"{value:.1f}" if value < 1000 else f"{value/1000:.1f}k"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=6.8)
    axes[0].set_title("Misma regla, distinta vecindad y agenda", loc="left", fontweight="bold")
    figure.subplots_adjust(wspace=0.38)
    return save_figure(figure, stem)


def plot_joint_gate(metrics: Mapping[str, Any], stem: Path) -> list[Path]:
    _style()
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 3.25))
    rd = 100.0 * float(metrics["risk_difference"])
    rd_low = 100.0 * float(metrics["risk_difference_low"])
    rd_high = 100.0 * float(metrics["risk_difference_high"])
    margin = -100.0 * float(metrics["noninferiority_margin"])
    axes[0].axvline(margin, color="#D94A35", linestyle="--", linewidth=1.0, label="margen −2 pp")
    axes[0].errorbar(rd, 0, xerr=[[rd - rd_low], [rd_high - rd]], fmt="o", color="#18855B", capsize=4, markersize=7)
    axes[0].set_yticks([])
    axes[0].set_xlabel("Diferencia de factibilidad QPG-CF − GRAPE (pp)")
    axes[0].set_title("No inferioridad preespecificada", loc="left", fontweight="bold")
    axes[0].grid(True, axis="x")
    axes[0].legend(frameon=False, loc="lower right")

    bd = float(metrics["byte_difference_median"])
    bd_low = float(metrics["byte_difference_low"])
    bd_high = float(metrics["byte_difference_high"])
    axes[1].axvline(0.0, color="#D94A35", linestyle="--", linewidth=1.0)
    axes[1].errorbar(bd, 0, xerr=[[bd - bd_low], [bd_high - bd]], fmt="o", color="#18855B", capsize=4, markersize=7)
    axes[1].set_yticks([])
    axes[1].set_xlabel("Diferencia mediana de bytes/agente")
    axes[1].set_title("Coste de comunicación pareado", loc="left", fontweight="bold")
    axes[1].grid(True, axis="x")
    for index, ax in enumerate(axes):
        ax.text(-0.08, 1.05, f"({chr(97 + index)})", transform=ax.transAxes, fontweight="bold")
        ax.spines[["top", "right", "left"]].set_visible(False)
    figure.subplots_adjust(wspace=0.28)
    return save_figure(figure, stem)


def analyse_and_plot(
    replay: pd.DataFrame,
    confirmatory: pd.DataFrame,
    config: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    processed = output / "processed"
    figures = output / "figures"
    processed.mkdir(parents=True, exist_ok=True)
    replay_summary, replay_metrics = analyse_campaign(replay, config, tag="E2_REPLAY")
    confirm_summary, confirm_metrics = analyse_campaign(
        confirmatory, config, tag="E3_CONFIRMATORY"
    )
    replay_summary.to_csv(processed / "e2_replay_summary.csv", index=False)
    confirm_summary.to_csv(processed / "e3_confirmatory_summary.csv", index=False)
    write_json(processed / "e2_replay_metrics.json", replay_metrics)
    write_json(processed / "e3_confirmatory_metrics.json", confirm_metrics)
    plot_frontier(replay_summary, figures / "n4_replay_frontier", title_suffix="replay N3")
    plot_frontier(confirm_summary, figures / "n4_confirmatory_frontier", title_suffix="semillas nuevas")
    plot_ablation(confirm_summary, figures / "n4_variants")
    plot_joint_gate(confirm_metrics, figures / "n4_joint_gate")
    metrics = {
        "campaign_id": config["campaign_id"],
        "replay": replay_metrics,
        "confirmatory": confirm_metrics,
    }
    write_json(output / "key_metrics.json", metrics)
    return metrics


def freeze_frames(output: Path, frames: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    frozen: dict[str, Any] = {}
    for name, frame in frames.items():
        path = raw / f"{name}.csv"
        frame.to_csv(path, index=False)
        frozen[name] = {
            "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
            "rows": int(len(frame)),
            "sha256": sha256_file(path),
        }
    return frozen


def build_manifest(
    *,
    output: Path,
    config_path: Path,
    config: Mapping[str, Any],
    frozen: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    source_paths = [
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "src" / "viu_mrob_tfm" / "sp1_n4" / "geo_qpg.py",
        REPOSITORY_ROOT / "src" / "viu_mrob_tfm" / "sp1_n3" / "runner.py",
        config_path.resolve(),
    ]
    artifacts = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifacts.append(
                {
                    "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    manifest = {
        "schema_version": "sp1-n4-package-v1",
        "level": "N4",
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
            {
                "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in source_paths
        ],
        "frozen_raw": frozen,
        "row_counts": {
            name: int(record["rows"])
            for name, record in frozen.items()
        },
        "primary_joint_gate": metrics["confirmatory"]["joint_gate_passed"],
        "artifacts": artifacts,
        "limitations": list(config["limitations"]),
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def write_report(output: Path, metrics: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    replay = metrics["replay"]
    confirm = metrics["confirmatory"]
    summary = pd.read_csv(output / "processed" / "e3_confirmatory_summary.csv")
    lines = [
        "# SP1.N4 — Geo-QPG atómico",
        "",
        "## Diseño",
        "",
        f"- Replay descriptivo: {replay['worlds']:,} mundos de N3.",
        f"- Confirmatorio: {confirm['worlds']:,} mundos nuevos pareados.",
        f"- Oráculo: {confirm['oracle_feasible_worlds']:,} mundos con solución y "
        f"{confirm['oracle_infeasible_worlds']:,} infactibles.",
        f"- Soporte común de calidad: {confirm['common_gap_worlds']:,} mundos.",
        "- El MILP conserva el papel de techo central; no interviene en las decisiones.",
        "",
        "## Hipótesis conjunta preespecificada",
        "",
        f"- Diferencia de factibilidad QPG-CF − GRAPE: {100*confirm['risk_difference']:.2f} pp "
        f"(IC95 % {100*confirm['risk_difference_low']:.2f}, {100*confirm['risk_difference_high']:.2f}).",
        f"- Diferencia mediana de bytes/agente: {confirm['byte_difference_median']:.1f} "
        f"(IC95 % {confirm['byte_difference_low']:.1f}, {confirm['byte_difference_high']:.1f}).",
        f"- Reducción relativa de bytes: {100*confirm['bytes_relative_reduction']:.1f} %; "
        f"ratio de tiempo CPU: {confirm['runtime_ratio']:.2f}.",
        f"- Diferencia mediana de gap QPG-CF − GRAPE: "
        f"{100*confirm['gap_difference_vs_grape']:.2f} pp "
        f"(IC95 % {100*confirm['gap_difference_vs_grape_low']:.2f}, "
        f"{100*confirm['gap_difference_vs_grape_high']:.2f}).",
        f"- Gate conjunto: {'PASS' if confirm['joint_gate_passed'] else 'FAIL'}.",
        "",
        "## Resumen por método",
        "",
        summary.to_markdown(index=False),
        "",
        "## Alcance",
        "",
    ]
    lines.extend(f"- {item}" for item in config["limitations"])
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    if args.analysis_only:
        replay = pd.read_csv(raw / "e2_replay_runs.csv")
        confirmatory = pd.read_csv(raw / "e3_confirmatory_runs.csv")
        metrics = analyse_and_plot(replay, confirmatory, config, output)
        write_report(output, metrics, config)
        previous = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        build_manifest(
            output=output,
            config_path=args.config,
            config=config,
            frozen=previous["frozen_raw"],
            metrics=metrics,
        )
        print(f"analysis: {output.resolve()}")
        print(f"joint gate: {metrics['confirmatory']['joint_gate_passed']}")
        return
    if raw.exists() and any(raw.glob("*.csv")):
        raise SystemExit(
            f"{raw} already contains RAW. Use --analysis-only or create a new campaign id."
        )

    print(f"campaign   {config['campaign_id']}")
    print(f"config     {sha256_file(args.config)}")
    print(f"commit     {git_state()['commit']}  dirty={git_state()['tree_dirty']}")
    replay, replay_worlds = replay_n3(config)
    confirmatory, worlds, graphs, oracles = run_confirmatory(config)
    methods = tuple(config["methods"]["baselines"]) + tuple(config["methods"]["proposed"])
    problems = check_integrity(replay, confirmatory, worlds, methods)
    if problems:
        for problem in problems:
            print(f"INTEGRITY: {problem}")
        raise SystemExit("integrity checks failed; no package was certified")
    frozen = freeze_frames(
        output,
        {
            "e2_replay_runs": replay,
            "e2_replay_worlds": replay_worlds,
            "e3_confirmatory_runs": confirmatory,
            "e3_confirmatory_worlds": worlds,
            "e3_graph_instances": graphs,
            "e3_oracle_runs": oracles,
        },
    )
    metrics = analyse_and_plot(replay, confirmatory, config, output)
    write_report(output, metrics, config)
    manifest = build_manifest(
        output=output,
        config_path=args.config,
        config=config,
        frozen=frozen,
        metrics=metrics,
    )
    print(f"package    {(output / 'manifest.json').resolve()}")
    print(f"artifacts  {len(manifest['artifacts'])}")
    print(f"joint gate {metrics['confirmatory']['joint_gate_passed']}")


if __name__ == "__main__":
    main()
