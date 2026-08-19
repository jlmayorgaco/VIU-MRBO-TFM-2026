"""Run the static F-I/F-II/F-III benchmark and the separate F-IV pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.ticker import FuncFormatter
from scipy import stats


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from viu_mrob_tfm.sp1_n3.graph import adjacency_for_regime  # noqa: E402
from viu_mrob_tfm.sp1_n3.worlds import World, make_world  # noqa: E402
from viu_mrob_tfm.sp1_n4 import (  # noqa: E402
    atomic_closure,
    canonical_event_schedule,
    run_distributed_population_game,
    run_distributed_vgne,
    run_event_triggered_policy,
    run_perfect_foresight_oracle,
    solve_central_vgne,
)


DEFAULT_CONFIG = (
    REPOSITORY_ROOT / "experiments" / "configs" / "sp1_n4_cross_family_v3.yaml"
)
DEFAULT_OUTPUT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n4_v3"

LABELS = {
    "capacity_cbba_rb": "CBBA-RB",
    "weighted_grape": "GRAPE",
    "weighted_pair_grape": "Pair-GRAPE",
    "geo_qpg_u": "Geo-QPG BR",
    "geo_qpg_p": "Geo-QPG 2BR",
    "geo_qpg_c3": "Geo-QPG C3",
    "geo_qpg_d": "Geo-QPG DMIS+TX",
    "fii_replicator_R": "Replicator + R",
    "fii_smith_R": "Smith + R",
    "fii_bnn_R": "BNN + R",
    "fii_logit_R": "Logit + R",
    "fiii_central_vgne_R": "vGNE central + R",
    "fiii_distributed_vgne_R": "PD-vGNE distribuido + R",
    "milp_highs": "MILP/HiGHS",
    "myopic_cold": "Geo-QPG reactivo",
    "event_triggered_warm": "Geo-QPG con memoria",
    "perfect_foresight_dp": "Óptimo escalar con futuro",
}

COLORS = {
    "F-I": "#D64B3C",
    "F-II": "#2F6FB0",
    "F-III": "#16825D",
    "F-IV": "#7A4FA3",
    "BASELINE": "#7A7F87",
    "ORACLE": "#202124",
}


def spanish_number(value: float, digits: int | None = None) -> str:
    """Format a plotted number with Spanish decimal and minus conventions."""
    if digits is None:
        text = f"{value:g}"
    else:
        text = f"{value:.{digits}f}"
    return text.replace("-", "−").replace(".", ",")


def spanish_tick(value: float, _position: float | None = None) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000 and float(value).is_integer():
        return f"{int(value):,}".replace(",", "\u202f")
    if abs(value) < 1e-3:
        exponent = int(math.floor(math.log10(abs(value))))
        mantissa = value / (10**exponent)
        return rf"${spanish_number(mantissa, 1)}\times10^{{{exponent}}}$"
    return spanish_number(value)


def latex_decimal(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", r"{,}")


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


def load_config(path: Path, smoke: bool) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if smoke:
        config["campaign_id"] += "_SMOKE"
        config["static"]["max_worlds"] = 8
        config["static"]["population"]["max_iterations"] = 300
        config["static"]["vgNE"]["central_max_iterations"] = 1_000
        config["static"]["vgNE"]["distributed_max_iterations"] = 500
        config["dynamic"]["scenarios"] = ["uniform", "corridor"]
        config["dynamic"]["seeds_per_scenario"] = 1
        config["analysis"]["bootstrap_resamples"] = 400
    return config


def world_from_row(row: Mapping[str, Any], section: Mapping[str, Any]) -> World:
    world = make_world(
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
    expected = row.get("world_digest")
    if expected is not None and str(expected) != "nan" and world.digest() != str(expected):
        raise RuntimeError(f"world digest mismatch: {row['world_key']}")
    return world


def _closure_fields(world: World, x: np.ndarray, section: Mapping[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    result = atomic_closure(
        world,
        x,
        max_chain_length=int(section["max_chain_length"]),
        max_nodes_per_augmentation=int(section["max_nodes_per_augmentation"]),
        candidates_per_load=int(section["candidates_per_load"]),
    )
    return {
        "feasible": result.feasible,
        "distance_cost": result.distance,
        "capacity_deficit": result.deficit,
        "excess_capacity": result.excess_capacity,
        "closure_robots_changed": result.robots_changed,
        "closure_operations": result.recovery_operations,
        "closure_augmentations": result.augmentations,
        "closure_max_chain": result.maximum_chain_length,
        "closure_nodes_explored": result.nodes_explored,
        "closure_failure_reason": result.failure_reason,
        "closure_runtime_ms": 1_000.0 * (time.perf_counter() - started),
        "assignment": ";".join(map(str, result.assignment.tolist())),
    }


def _gap(fields: Mapping[str, Any], oracle: Mapping[str, Any]) -> float:
    objective = float(oracle.get("oracle_objective", math.nan))
    if (
        bool(fields["feasible"])
        and bool(oracle.get("oracle_certified", False))
        and np.isfinite(objective)
        and objective > 0.0
    ):
        return (float(fields["distance_cost"]) - objective) / objective
    return math.nan


def _common_row(
    row: Mapping[str, Any], oracle: Mapping[str, Any], method: str, family: str
) -> dict[str, Any]:
    return {
        "campaign_id": row["campaign_id"],
        "experiment": "E7_CROSS_FAMILY_STATIC",
        "world_key": row["world_key"],
        "world_id": row["world_id"],
        "world_seed": int(row["world_seed"]),
        "scenario": row["scenario"],
        "N": int(row["N"]),
        "K": int(row["K"]),
        "capacity_cv": float(row["capacity_cv"]),
        "pressure": float(row["pressure"]),
        "graph_regime": row["graph_regime"],
        "method": method,
        "method_label": LABELS[method],
        "family": family,
        "atomic_endpoint": True,
        **oracle,
    }


def run_static_world(payload: tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]):
    row, section, oracle, capture_history = payload
    world = world_from_row(row, section)
    adjacency = adjacency_for_regime(world.robot_positions, str(section["graph_regime"]))
    population = section["population"]
    closure = section["closure"]
    vg = section["vgNE"]
    rows: list[dict[str, Any]] = []
    traces: list[pd.DataFrame] = []

    for method in section["population_methods"]:
        result = run_distributed_population_game(
            world,
            adjacency,
            str(method),
            deficit_penalty=float(population["deficit_penalty"]),
            distance_weight=float(population["distance_weight"]),
            step=float(population["step_by_method"][method]),
            temperature=float(population["temperature"]),
            max_iterations=int(population["max_iterations"]),
            tolerance=float(population["tolerance"]),
            consensus_tolerance=float(population["consensus_tolerance"]),
            history_stride=int(population["history_stride"]),
        )
        fields = _closure_fields(world, result.x, closure)
        method_id = f"fii_{method}_R"
        rows.append(
            {
                **_common_row(row, oracle, method_id, "F-II"),
                **fields,
                "optimality_gap": _gap(fields, oracle),
                "continuous_converged": result.converged,
                "continuous_stop_reason": result.stop_reason,
                "continuous_iterations": result.iterations,
                "continuous_potential": result.potential,
                "continuous_deficit": result.continuous_deficit,
                "continuous_distance": result.continuous_distance,
                "fixed_point_residual": result.fixed_point_residual,
                "consensus_residual": result.consensus_residual,
                "kkt_residual": math.nan,
                "potential_monotone": result.potential_monotone,
                "minimum_positive_correlation": result.minimum_positive_correlation,
                "messages": result.messages,
                "bytes": result.bytes_sent,
                "bytes_per_agent": result.bytes_sent / world.n_robots,
                "runtime_ms": result.runtime_ms + fields["closure_runtime_ms"],
                "information_mode": result.information_mode,
            }
        )
        if capture_history:
            trace = result.history.copy()
            trace.insert(0, "method", method_id)
            trace.insert(0, "world_key", row["world_key"])
            traces.append(trace)

    central = solve_central_vgne(
        world,
        regularization=float(vg["regularization"]),
        max_iterations=int(vg["central_max_iterations"]),
        kkt_tolerance=float(vg["central_kkt_tolerance"]),
    )
    distributed = run_distributed_vgne(
        world,
        adjacency,
        regularization=float(vg["regularization"]),
        primal_step=float(vg["primal_step"]),
        dual_step=float(vg["dual_step"]),
        max_iterations=int(vg["distributed_max_iterations"]),
        tolerance=float(vg["tolerance"]),
        history_stride=int(vg["history_stride"]),
    )
    for result, method_id, architecture in (
        (central, "fiii_central_vgne_R", "central_global"),
        (distributed, "fiii_distributed_vgne_R", "distributed_DAC_consensus"),
    ):
        fields = _closure_fields(world, result.x, closure)
        rows.append(
            {
                **_common_row(row, oracle, method_id, "F-III"),
                **fields,
                "optimality_gap": _gap(fields, oracle),
                "continuous_converged": result.converged,
                "continuous_stop_reason": result.stop_reason,
                "continuous_iterations": result.iterations,
                "continuous_potential": math.nan,
                "continuous_deficit": result.primal_residual,
                "continuous_distance": result.objective,
                "fixed_point_residual": result.stationarity_residual,
                "primal_residual": result.primal_residual,
                "dual_residual": result.dual_residual,
                "complementarity_residual": result.complementarity_residual,
                "stationarity_residual": result.stationarity_residual,
                "consensus_residual": result.consensus_residual,
                "kkt_residual": result.kkt_residual,
                "messages": result.messages,
                "bytes": result.bytes_sent,
                "bytes_per_agent": result.bytes_sent / world.n_robots,
                "runtime_ms": result.runtime_ms + fields["closure_runtime_ms"],
                "information_mode": architecture,
            }
        )
        if capture_history:
            trace = result.history.copy()
            trace.insert(0, "method", method_id)
            trace.insert(0, "world_key", row["world_key"])
            traces.append(trace)
    trace_frame = pd.concat(traces, ignore_index=True, sort=False) if traces else pd.DataFrame()
    return rows, trace_frame


def _prepare_static(config: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    section = config["static"]
    source_dir = REPOSITORY_ROOT / str(section["source_directory"])
    worlds = pd.read_csv(source_dir / str(section["source_worlds"])).copy()
    max_worlds = section.get("max_worlds")
    if max_worlds is not None:
        # Spread smoke worlds over the frozen order instead of taking one cell.
        indices = np.linspace(0, len(worlds) - 1, int(max_worlds), dtype=int)
        worlds = worlds.iloc[indices].copy()
    source_runs = pd.read_csv(REPOSITORY_ROOT / str(section["source_runs"]))
    source_runs = source_runs[
        source_runs["world_key"].isin(worlds["world_key"])
        & source_runs["method"].isin(section["existing_methods"])
    ].copy()
    oracles = (
        source_runs.sort_values("method")
        .drop_duplicates("world_key")
        .set_index("world_key")[[
            "oracle_status",
            "oracle_objective",
            "oracle_gap",
            "oracle_runtime_s",
            "oracle_feasible",
            "oracle_certified",
        ]]
    )
    return worlds, source_runs, oracles


def run_static_campaign(
    config: Mapping[str, Any], *, workers: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    worlds, source_runs, oracles = _prepare_static(config)
    section = dict(config["static"])
    trace_candidates = worlds[
        (worlds["pressure"] == worlds["pressure"].max())
        & (worlds["capacity_cv"] >= 0.65)
    ]
    trace_key = str((trace_candidates.iloc[0] if len(trace_candidates) else worlds.iloc[0])["world_key"])
    payloads = []
    for _, row in worlds.iterrows():
        oracle = oracles.loc[str(row["world_key"])].to_dict()
        payloads.append(
            (
                {**row.to_dict(), "campaign_id": config["campaign_id"], "graph_regime": section["graph_regime"]},
                section,
                oracle,
                str(row["world_key"]) == trace_key,
            )
        )

    new_rows: list[dict[str, Any]] = []
    traces: list[pd.DataFrame] = []
    with ProcessPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(run_static_world, payload) for payload in payloads]
        for index, future in enumerate(as_completed(futures), 1):
            rows, trace = future.result()
            new_rows.extend(rows)
            if not trace.empty:
                traces.append(trace)
            if index == len(futures) or index % max(1, len(futures) // 60) == 0:
                print(f"  E7 static: {index}/{len(futures)}", flush=True)

    existing = source_runs.copy()
    existing["campaign_id"] = config["campaign_id"]
    existing["experiment"] = "E7_CROSS_FAMILY_STATIC"
    existing["family"] = np.where(
        existing["method"].str.startswith("geo_qpg"), "F-I", "BASELINE"
    )
    existing["method_label"] = existing["method"].map(LABELS)
    existing["atomic_endpoint"] = True
    existing["assignment"] = "not_persisted_in_v2"
    existing["continuous_converged"] = np.nan
    existing["continuous_potential"] = np.nan
    existing["continuous_deficit"] = np.nan
    existing["closure_operations"] = 0
    existing["closure_robots_changed"] = 0
    existing["kkt_residual"] = np.nan
    oracle_rows = []
    for _, row in worlds.iterrows():
        oracle = oracles.loc[str(row["world_key"])].to_dict()
        oracle_rows.append(
            {
                **_common_row(
                    {**row.to_dict(), "campaign_id": config["campaign_id"], "graph_regime": section["graph_regime"]},
                    oracle,
                    "milp_highs",
                    "ORACLE",
                ),
                "feasible": bool(oracle["oracle_feasible"]),
                "distance_cost": float(oracle["oracle_objective"]),
                "capacity_deficit": 0.0 if bool(oracle["oracle_feasible"]) else math.nan,
                "optimality_gap": 0.0 if bool(oracle["oracle_certified"]) else math.nan,
                "runtime_ms": 1_000.0 * float(oracle["oracle_runtime_s"]),
                "messages": 0,
                "bytes": 0,
                "bytes_per_agent": 0.0,
                "continuous_converged": np.nan,
                "continuous_potential": np.nan,
                "continuous_deficit": np.nan,
                "closure_operations": 0,
                "closure_robots_changed": 0,
                "kkt_residual": np.nan,
                "assignment": "oracle_assignment_not_persisted_in_v2",
            }
        )
    combined = pd.concat(
        [existing, pd.DataFrame(new_rows), pd.DataFrame(oracle_rows)],
        ignore_index=True,
        sort=False,
    )
    combined = combined.sort_values(["world_key", "family", "method"]).reset_index(drop=True)
    trace_frame = pd.concat(traces, ignore_index=True, sort=False) if traces else pd.DataFrame()
    return combined, trace_frame


def run_dynamic_campaign(config: Mapping[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    section = config["dynamic"]
    rows: list[dict[str, Any]] = []
    histories: list[pd.DataFrame] = []
    cells = [
        (str(scenario), replicate)
        for scenario in section["scenarios"]
        for replicate in range(int(section["seeds_per_scenario"]))
    ]
    for index, (scenario, replicate) in enumerate(cells, 1):
        seed = stable_seed(int(section["base_seed"]), scenario, replicate)
        world_key = f"E8:{scenario}:r{replicate}:s{seed}"
        world = make_world(
            world_id=world_key,
            robot_count=int(section["robot_count"]),
            load_count=int(section["load_count"]),
            q_bar=float(section["q_bar_kg"]),
            cv=float(section["capacity_cv"]),
            pressure=float(section["pressure"]),
            scenario=scenario,
            workspace=tuple(float(value) for value in section["workspace_m"]),
            seed=seed,
            alpha=float(section["demand_split_alpha"]),
        )
        adjacency = adjacency_for_regime(world.robot_positions, str(section["graph_regime"]))
        events = canonical_event_schedule(world)
        results = [
            run_event_triggered_policy(
                world,
                adjacency,
                events,
                policy=policy,
                gamma=float(section["gamma"]),
                deficit_weight=float(section["deficit_weight"]),
                distance_weight=float(section["distance_weight"]),
                switch_weight=float(section["switch_weight"]),
                max_rounds=int(section["max_rounds"]),
            )
            for policy in ("myopic_cold", "event_triggered_warm")
        ]
        results.append(
            run_perfect_foresight_oracle(
                world,
                events,
                gamma=float(section["gamma"]),
                deficit_weight=float(section["deficit_weight"]),
                distance_weight=float(section["distance_weight"]),
                switch_weight=float(section["switch_weight"]),
                max_states=int(section["max_oracle_states"]),
            )
        )
        for result in results:
            rows.append(
                {
                    "campaign_id": config["campaign_id"],
                    "experiment": "E8_DYNAMIC_SEPARATE",
                    "world_key": world_key,
                    "world_seed": seed,
                    "scenario": scenario,
                    "replicate": replicate,
                    "method": result.policy,
                    "method_label": LABELS[result.policy],
                    "family": "F-IV",
                    "discounted_cost": result.discounted_cost,
                    "service_success_rate": result.service_success_rate,
                    "unmet_demand_steps": result.unmet_demand_steps,
                    "coalition_switches": result.coalition_switches,
                    "messages": result.messages,
                    "bytes": result.bytes_sent,
                    "atomic_feasible_rate": result.atomic_feasible_rate,
                }
            )
            history = result.history.copy()
            history.insert(0, "method", result.policy)
            history.insert(0, "scenario", scenario)
            history.insert(0, "world_seed", seed)
            history.insert(0, "world_key", world_key)
            histories.append(history)
        if index == len(cells) or index % max(1, len(cells) // 10) == 0:
            print(f"  E8 dynamic: {index}/{len(cells)}", flush=True)
    return pd.DataFrame(rows), pd.concat(histories, ignore_index=True, sort=False)


def bootstrap_interval(
    values: np.ndarray,
    *,
    config: Mapping[str, Any],
    seed_offset: int = 0,
    statistic: str = "median",
):
    data = np.asarray(values, dtype=float)
    data = data[np.isfinite(data)]
    if not len(data):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(int(config["analysis"]["bootstrap_seed"]) + seed_offset)
    sampled = rng.choice(
        data,
        size=(int(config["analysis"]["bootstrap_resamples"]), len(data)),
        replace=True,
    )
    estimator = np.mean if statistic == "mean" else np.median
    estimates = estimator(sampled, axis=1)
    return (
        float(estimator(data)),
        float(np.quantile(estimates, 0.025)),
        float(np.quantile(estimates, 0.975)),
    )


def summarize_static(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    rows = []
    eligible = frame[frame["oracle_feasible"].fillna(False).astype(bool)].copy()
    for index, (method, group) in enumerate(eligible.groupby("method", sort=False)):
        gaps = group.loc[group["feasible"].fillna(False).astype(bool), "optimality_gap"]
        gap, low, high = bootstrap_interval(gaps.to_numpy(float), config=config, seed_offset=index)
        rows.append(
            {
                "method": method,
                "label": LABELS.get(method, method),
                "family": str(group["family"].iloc[0]),
                "worlds": len(group),
                "feasibility": float(group["feasible"].fillna(False).astype(bool).mean()),
                "gap_median": gap,
                "gap_low": low,
                "gap_high": high,
                "runtime_ms_median": float(group["runtime_ms"].median()),
                "bytes_per_agent_median": float(group["bytes_per_agent"].fillna(0.0).median()),
                "closure_operations_median": float(group["closure_operations"].fillna(0.0).median()),
                "continuous_convergence": float(group["continuous_converged"].dropna().astype(bool).mean())
                if group["continuous_converged"].notna().any()
                else math.nan,
                "kkt_residual_median": float(group["kkt_residual"].median()),
            }
        )
    return pd.DataFrame(rows)


def population_ranking(frame: pd.DataFrame) -> pd.DataFrame:
    subset = frame[frame["family"] == "F-II"].copy()
    rows = []
    for world_key, group in subset.groupby("world_key"):
        continuous = group.loc[group["continuous_potential"].idxmax()]
        ordered = group.assign(
            feasible_order=~group["feasible"].fillna(False).astype(bool),
            gap_order=group["optimality_gap"].fillna(np.inf),
        ).sort_values(["feasible_order", "gap_order", "distance_cost", "method"])
        atomic = ordered.iloc[0]
        ranks_cont = group["continuous_potential"].rank(ascending=False, method="average")
        ranks_atomic = group["optimality_gap"].fillna(np.inf).rank(ascending=True, method="average")
        rho = (
            stats.spearmanr(ranks_cont, ranks_atomic).statistic
            if ranks_cont.nunique() > 1 and ranks_atomic.nunique() > 1
            else math.nan
        )
        rows.append(
            {
                "world_key": world_key,
                "scenario": group["scenario"].iloc[0],
                "pressure": group["pressure"].iloc[0],
                "capacity_cv": group["capacity_cv"].iloc[0],
                "continuous_winner": continuous["method"],
                "atomic_winner": atomic["method"],
                "winner_mismatch": continuous["method"] != atomic["method"],
                "spearman_rho": float(rho) if np.isfinite(rho) else math.nan,
            }
        )
    return pd.DataFrame(rows)


def paired_primary_contrasts(
    static: pd.DataFrame, dynamic: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    rows = []
    high = static[np.isclose(static["pressure"], 0.85)].copy()
    for metric in ("feasible", "optimality_gap", "closure_operations"):
        wide = high[high["method"].isin(["fiii_distributed_vgne_R", "fii_smith_R"])].pivot(
            index="world_key", columns="method", values=metric
        )
        required = ["fiii_distributed_vgne_R", "fii_smith_R"]
        if any(method not in wide.columns for method in required):
            continue
        if metric != "feasible":
            wide = wide.dropna()
        if wide.empty:
            continue
        left = wide["fiii_distributed_vgne_R"].astype(float)
        right = wide["fii_smith_R"].astype(float)
        difference = (left - right).to_numpy(float)
        estimate, low, high_ci = bootstrap_interval(
            difference,
            config=config,
            seed_offset=100 + len(rows),
            statistic="mean" if metric == "feasible" else "median",
        )
        if metric == "feasible":
            discordant_plus = int(((left == 1) & (right == 0)).sum())
            discordant_minus = int(((left == 0) & (right == 1)).sum())
            total = discordant_plus + discordant_minus
            p_value = (
                float(stats.binomtest(discordant_plus, total, 0.5).pvalue)
                if total
                else 1.0
            )
        else:
            p_value = float(stats.wilcoxon(difference).pvalue) if np.any(difference) else 1.0
        rows.append(
            {
                "question": "RQ-E",
                "metric": metric,
                "left": "fiii_distributed_vgne_R",
                "right": "fii_smith_R",
                "pairs": len(wide),
                "median_difference": estimate,
                "ci_low": low,
                "ci_high": high_ci,
                "p_value_uncorrected": p_value,
            }
        )
    for comparator in ("myopic_cold", "event_triggered_warm"):
        wide = dynamic[dynamic["method"].isin(["perfect_foresight_dp", comparator])].pivot(
            index="world_key", columns="method", values="discounted_cost"
        ).dropna()
        difference = (
            wide["perfect_foresight_dp"] - wide[comparator]
        ).to_numpy(float)
        estimate, low, high_ci = bootstrap_interval(
            difference, config=config, seed_offset=200 + len(rows)
        )
        rows.append(
            {
                "question": "RQ-G",
                "metric": "discounted_cost",
                "left": "perfect_foresight_dp",
                "right": comparator,
                "pairs": len(wide),
                "median_difference": estimate,
                "ci_low": low,
                "ci_high": high_ci,
                "p_value_uncorrected": float(stats.wilcoxon(difference).pvalue)
                if np.any(difference)
                else 1.0,
            }
        )
    p_values = np.asarray([row["p_value_uncorrected"] for row in rows], dtype=float)
    order = np.argsort(p_values)
    adjusted = np.empty_like(p_values)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (len(rows) - rank) * p_values[index])
        running = max(running, candidate)
        adjusted[index] = running
    for row, value in zip(rows, adjusted, strict=True):
        row["p_value_holm"] = float(value)
    return pd.DataFrame(rows)


def configure_plots() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.2,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "axes.linewidth": 0.8,
            "axes.edgecolor": "#4E5965",
            "axes.facecolor": "#FBFCFD",
            "figure.facecolor": "white",
            "grid.color": "#D9E0E7",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.65,
            "legend.frameon": False,
            "savefig.bbox": "tight",
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"))
    fig.savefig(path.with_suffix(".png"), dpi=450)
    plt.close(fig)


def plot_population(static: pd.DataFrame, ranking: pd.DataFrame, output: Path) -> None:
    subset = static[static["family"] == "F-II"].copy()
    methods = [f"fii_{name}_R" for name in ("replicator", "smith", "bnn", "logit")]
    labels = [LABELS[method].replace(" + R", "") for method in methods]
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 2.85), constrained_layout=True)
    deficit = [
        np.maximum(subset.loc[subset["method"] == method, "continuous_deficit"].to_numpy(float), 1e-8)
        for method in methods
    ]
    gap = [
        100.0 * subset.loc[
            (subset["method"] == method) & subset["feasible"].astype(bool),
            "optimality_gap",
        ].dropna().to_numpy(float)
        for method in methods
    ]
    boxes = axes[0].boxplot(deficit, tick_labels=labels, patch_artist=True, showfliers=False)
    for patch in boxes["boxes"]:
        patch.set(facecolor="#DDEAF7", edgecolor="#2F6FB0", linewidth=0.9)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Déficit continuo final [kg]")
    axes[0].set_title("A | Estado continuo final")
    boxes = axes[1].boxplot(gap, tick_labels=labels, patch_artist=True, showfliers=False)
    for patch in boxes["boxes"]:
        patch.set(facecolor="#E5F3EC", edgecolor="#16825D", linewidth=0.9)
    mismatch = 100.0 * float(ranking["winner_mismatch"].mean())
    eligible = subset[subset["oracle_feasible"].fillna(False).astype(bool)]
    feasibility = eligible.groupby("method")["feasible"].mean().reindex(methods)
    axes[1].set_ylabel("Gap MILP tras R [%]")
    axes[1].set_title(
        f"B | Resultado entero · ranking cambia en {spanish_number(mismatch, 1)} %"
    )
    axes[1].text(
        0.98,
        0.97,
        "factibilidad: "
        f"{spanish_number(100.0 * feasibility.min(), 1)}–"
        f"{spanish_number(100.0 * feasibility.max(), 1)} %",
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        fontsize=6.4,
        color="#4E5965",
        bbox={"boxstyle": "round,pad=0.24", "facecolor": "white", "edgecolor": "#D9E0E7"},
    )
    for ax in axes:
        ax.grid(True, axis="y")
        ax.tick_params(axis="x", rotation=18)
        ax.yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    save_figure(fig, output / "n4_fii_continuous_atomic")


def plot_vgne(traces: pd.DataFrame, static: pd.DataFrame, output: Path) -> None:
    trace = traces[traces["method"] == "fiii_distributed_vgne_R"].copy()
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.15, 2.95),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [1.58, 1.0]},
    )
    ax = axes[0]
    for column, label, color in (
        ("primal", "primal", "#D64B3C"),
        ("stationarity", "estacionariedad", "#2F6FB0"),
        ("complementarity", "complementariedad", "#7A4FA3"),
        ("consensus", "consenso", "#16825D"),
        ("kkt", "KKT conjunto", "#202124"),
    ):
        if column in trace:
            ax.plot(
                trace["iteration"],
                np.maximum(trace[column], 1e-10),
                label=label,
                color=color,
                linewidth=1.45 if column == "kkt" else 1.0,
            )
    ax.axhline(
        5e-4,
        color="#F04B23",
        linestyle="--",
        linewidth=0.9,
        label="umbral conjunto",
    )
    ax.set_yscale("log")
    ax.set_xlabel("Iteración digital")
    ax.set_ylabel("Residual")
    ax.set_title("A | Residuo durante una ejecución")
    ax.grid(True, which="both")
    ax.legend(ncol=2, loc="upper right", fontsize=6.2)

    distributed = static[static["method"] == "fiii_distributed_vgne_R"].copy()
    table = (
        distributed.groupby(["pressure", "capacity_cv"])["continuous_converged"]
        .mean()
        .mul(100.0)
        .unstack()
        .sort_index()
        .sort_index(axis=1)
    )
    cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "viu_green", ["#F8DED6", "#FFF7E8", "#DDEFE6", "#16825D"]
    )
    image_handle = axes[1].imshow(
        table.to_numpy(float), vmin=80.0, vmax=100.0, cmap=cmap, aspect="auto"
    )
    for row_index in range(table.shape[0]):
        for column_index in range(table.shape[1]):
            value = float(table.iloc[row_index, column_index])
            axes[1].text(
                column_index,
                row_index,
                spanish_number(value, 1),
                ha="center",
                va="center",
                fontsize=7.0,
                color="white" if value >= 96.0 else "#202124",
                fontweight="bold",
            )
    axes[1].set_xticks(
        range(table.shape[1]), [spanish_number(float(value)) for value in table.columns]
    )
    axes[1].set_yticks(
        range(table.shape[0]), [spanish_number(float(value)) for value in table.index]
    )
    axes[1].set_xlabel("CV de capacidad")
    axes[1].set_ylabel("Presión")
    axes[1].set_title("B | Convergencia conjunta [%]")
    colorbar = fig.colorbar(image_handle, ax=axes[1], fraction=0.046, pad=0.04)
    colorbar.ax.tick_params(labelsize=6.2)
    colorbar.ax.yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    save_figure(fig, output / "n4_fiii_residuals")


def plot_cross_pareto(summary: pd.DataFrame, output: Path) -> None:
    subset = summary[
        summary["method"].isin(
            [
                "geo_qpg_u",
                "geo_qpg_c3",
                "geo_qpg_d",
                "fii_replicator_R",
                "fii_smith_R",
                "fii_bnn_R",
                "fii_logit_R",
                "fiii_distributed_vgne_R",
                "capacity_cbba_rb",
                "weighted_grape",
                "weighted_pair_grape",
            ]
        )
    ].copy()
    fig, ax = plt.subplots(figsize=(7.1, 3.35), constrained_layout=True)
    label_offsets = {
        "fii_replicator_R": (4, 15),
        "fii_smith_R": (4, 3),
        "fii_bnn_R": (4, -10),
        "fii_logit_R": (-64, -19),
        "geo_qpg_u": (3, 3),
        "geo_qpg_c3": (3, 3),
        "geo_qpg_d": (3, 3),
    }
    for family, group in subset.groupby("family"):
        ax.scatter(
            group["bytes_per_agent_median"] + 1.0,
            100.0 * group["gap_median"],
            s=35.0 + 85.0 * group["feasibility"],
            color=COLORS.get(str(family), "#7A7F87"),
            edgecolor="white",
            linewidth=0.7,
            label=family,
            zorder=3,
        )
        for _, row in group.iterrows():
            offset = label_offsets.get(str(row["method"]), (3, 3))
            ax.annotate(
                row["label"],
                (row["bytes_per_agent_median"] + 1.0, 100.0 * row["gap_median"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=6.2,
            )
    ax.set_xscale("log")
    ax.set_xlabel("Bytes modelados por agente + 1 [log]")
    ax.set_ylabel("Brecha mediana frente al MILP [%]")
    ax.set_title(
        "Síntesis N3–N4: calidad, comunicación y factibilidad\n"
        "fase decisional; cierre central R excluido"
    )
    ax.grid(True, which="both")
    ax.xaxis.set_major_formatter(FuncFormatter(spanish_tick))
    ax.yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    ax.legend(title="Familia", ncol=2, loc="upper right", fontsize=7.2)
    save_figure(fig, output / "n4_cross_family_pareto")


def plot_dynamic(dynamic: pd.DataFrame, output: Path) -> None:
    methods = ["myopic_cold", "event_triggered_warm", "perfect_foresight_dp"]
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 2.9), constrained_layout=True)
    wide = dynamic.pivot(index="world_key", columns="method", values="discounted_cost")
    x = np.arange(len(methods))
    for _, row in wide.iterrows():
        axes[0].plot(x, [row[m] for m in methods], color="#B8C0C8", alpha=0.38, linewidth=0.65)
    medians = [float(wide[m].median()) for m in methods]
    axes[0].plot(x, medians, color="#202124", marker="o", linewidth=1.8, zorder=4)
    axes[0].set_xticks(x, ["Reactiva", "Con memoria", "Óptimo escalar"])
    axes[0].set_ylabel("Coste descontado")
    axes[0].set_title("A | Mismos eventos por mundo")
    summary = dynamic.groupby("method")[["coalition_switches", "messages"]].median().loc[methods]
    width = 0.36
    axes[1].bar(x - width / 2, summary["coalition_switches"], width, color="#7A4FA3", label="cambios")
    twin = axes[1].twinx()
    twin.bar(x + width / 2, summary["messages"], width, color="#F04B23", alpha=0.78, label="mensajes")
    axes[1].set_xticks(x, ["Reactiva", "Con memoria", "Óptimo escalar"])
    axes[1].set_ylabel("Cambios de coalición")
    twin.set_ylabel("Mensajes")
    axes[1].set_title("B | Recourse y coste informativo")
    axes[0].grid(True, axis="y")
    axes[1].grid(True, axis="y")
    handles = [
        mpl.patches.Patch(color="#7A4FA3", label="cambios"),
        mpl.patches.Patch(color="#F04B23", label="mensajes"),
    ]
    axes[1].legend(handles=handles, loc="upper right")
    axes[0].yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    axes[1].yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    twin.yaxis.set_major_formatter(FuncFormatter(spanish_tick))
    save_figure(fig, output / "n4_fiv_dynamic")


def write_macros(
    path: Path,
    static: pd.DataFrame,
    ranking: pd.DataFrame,
    dynamic: pd.DataFrame,
    contrasts: pd.DataFrame,
) -> None:
    def summary(method: str, column: str) -> float:
        return float(static.loc[static["method"] == method, column].median())

    mismatch = 100.0 * float(ranking["winner_mismatch"].mean())
    rho = float(ranking["spearman_rho"].median())
    pd_conv = 100.0 * float(
        static.loc[static["method"] == "fiii_distributed_vgne_R", "continuous_converged"]
        .astype(bool)
        .mean()
    )
    dynamic_wide = dynamic.pivot(index="world_key", columns="method", values="discounted_cost")
    lines = [
        f"\\newcommand{{\\NFourVThreeWorlds}}{{{static['world_key'].nunique():,}}}".replace(",", r"\,"),
        f"\\newcommand{{\\NFourFiiMismatchPct}}{{{latex_decimal(mismatch, 1)}}}",
        f"\\newcommand{{\\NFourFiiRankRho}}{{{latex_decimal(rho, 2)}}}",
        f"\\newcommand{{\\NFourPdConvergencePct}}{{{latex_decimal(pd_conv, 1)}}}",
        f"\\newcommand{{\\NFourPdKktMedian}}{{{latex_scientific(summary('fiii_distributed_vgne_R', 'kkt_residual'))}}}",
        f"\\newcommand{{\\NFourPdGapPct}}{{{latex_decimal(100.0 * summary('fiii_distributed_vgne_R', 'optimality_gap'), 2)}}}",
        f"\\newcommand{{\\NFourSmithGapPct}}{{{latex_decimal(100.0 * summary('fii_smith_R', 'optimality_gap'), 2)}}}",
        f"\\newcommand{{\\NFourDynamicWorlds}}{{{dynamic['world_key'].nunique()}}}",
        f"\\newcommand{{\\NFourWarmCost}}{{{latex_decimal(dynamic_wide['event_triggered_warm'].median(), 3)}}}",
        f"\\newcommand{{\\NFourMyopicCost}}{{{latex_decimal(dynamic_wide['myopic_cold'].median(), 3)}}}",
        f"\\newcommand{{\\NFourOracleCost}}{{{latex_decimal(dynamic_wide['perfect_foresight_dp'].median(), 3)}}}",
    ]
    for _, row in contrasts.iterrows():
        if row["question"] == "RQ-E" and row["metric"] == "feasible":
            lines.append(
                f"\\newcommand{{\\NFourPdRiskDiffPct}}{{{latex_decimal(100.0 * row['median_difference'], 2)}}}"
            )
        if row["question"] == "RQ-G" and row["right"] == "event_triggered_warm":
            lines.append(
                f"\\newcommand{{\\NFourOracleWarmDiff}}{{{latex_decimal(row['median_difference'], 3)}}}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Regenerate processed outputs, plots and manifest from existing RAW files.",
    )
    parser.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--max-worlds", type=int, default=None)
    args = parser.parse_args()
    config = load_config(args.config, args.smoke)
    if args.max_worlds is not None:
        config["static"]["max_worlds"] = int(args.max_worlds)
    output = args.output
    if args.smoke and args.output == DEFAULT_OUTPUT:
        output = DEFAULT_OUTPUT.with_name("n4_v3_smoke")
    for folder in ("raw", "processed", "figures"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    previous_elapsed = 0.0
    if args.analysis_only:
        required = [
            output / "raw" / "e7_cross_family_runs.csv",
            output / "raw" / "e7_representative_traces.csv",
            output / "raw" / "e8_dynamic_runs.csv",
            output / "raw" / "e8_dynamic_history.csv",
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(f"analysis-only requires RAW files: {missing}")
        static = pd.read_csv(required[0])
        traces = pd.read_csv(required[1])
        dynamic = pd.read_csv(required[2])
        dynamic_history = pd.read_csv(required[3])
        metrics_path = output / "key_metrics.json"
        if metrics_path.exists():
            previous_elapsed = float(json.loads(metrics_path.read_text(encoding="utf-8")).get("elapsed_s", 0.0))
    else:
        static, traces = run_static_campaign(config, workers=args.workers)
        dynamic, dynamic_history = run_dynamic_campaign(config)
    static_summary = summarize_static(static, config)
    ranking = population_ranking(static)
    contrasts = paired_primary_contrasts(static, dynamic, config)

    if not args.analysis_only:
        static.to_csv(output / "raw" / "e7_cross_family_runs.csv", index=False)
        traces.to_csv(output / "raw" / "e7_representative_traces.csv", index=False)
        dynamic.to_csv(output / "raw" / "e8_dynamic_runs.csv", index=False)
        dynamic_history.to_csv(output / "raw" / "e8_dynamic_history.csv", index=False)
    static_summary.to_csv(output / "processed" / "cross_family_summary.csv", index=False)
    ranking.to_csv(output / "processed" / "population_ranking_by_world.csv", index=False)
    contrasts.to_csv(output / "processed" / "primary_contrasts.csv", index=False)
    write_macros(output / "processed" / "n4_v3_results_macros.tex", static, ranking, dynamic, contrasts)

    configure_plots()
    plot_population(static, ranking, output / "figures")
    plot_vgne(traces, static, output / "figures")
    plot_cross_pareto(static_summary, output / "figures")
    plot_dynamic(dynamic, output / "figures")

    key_metrics = {
        "static_worlds": int(static["world_key"].nunique()),
        "static_rows": int(len(static)),
        "dynamic_worlds": int(dynamic["world_key"].nunique()),
        "population_winner_mismatch_rate": float(ranking["winner_mismatch"].mean()),
        "population_rank_spearman_median": float(ranking["spearman_rho"].median()),
        "distributed_vgne_convergence_rate": float(
            static.loc[
                static["method"] == "fiii_distributed_vgne_R", "continuous_converged"
            ].astype(bool).mean()
        ),
        "distributed_vgne_kkt_median": float(
            static.loc[static["method"] == "fiii_distributed_vgne_R", "kkt_residual"].median()
        ),
        "dynamic_cost_medians": dynamic.groupby("method")["discounted_cost"].median().to_dict(),
        "elapsed_s": previous_elapsed if args.analysis_only else time.perf_counter() - started,
    }
    write_json(output / "key_metrics.json", key_metrics)
    config_snapshot = output / "config_frozen.yaml"
    config_snapshot.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    artifact_files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "campaign_id": config["campaign_id"],
        "status": "smoke" if args.smoke else "executed",
        "git": git_state(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "workers": args.workers,
        },
        "artifacts": {
            path.relative_to(output).as_posix(): {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in artifact_files
        },
        "limitations": config["limitations"],
    }
    write_json(output / "manifest.json", manifest)
    report = (
        f"# SP1.N4 cross-family v3\n\n"
        f"- Static worlds: {key_metrics['static_worlds']}\n"
        f"- Static method-world rows: {key_metrics['static_rows']}\n"
        f"- Dynamic worlds: {key_metrics['dynamic_worlds']}\n"
        f"- F-II continuous/post-closure winner mismatch: "
        f"{100.0 * key_metrics['population_winner_mismatch_rate']:.1f}%\n"
        f"- Distributed vGNE joint-residual convergence: "
        f"{100.0 * key_metrics['distributed_vgne_convergence_rate']:.1f}%\n"
        f"- Scientific status: {'software smoke only' if args.smoke else 'executed paired campaign; claim audit required'}\n\n"
        "F-IV is a separate repeated-game pilot with exogenous events and is not "
        "pooled with the static ranking. The closure is a bounded deterministic "
        "heuristic and does not certify integer optimality.\n"
    )
    (output / "REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
