"""Reproducible orchestration and analysis for SP1_DYNAMICS_BENCHMARK_v3."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml
from scipy.stats import binomtest, norm, wilcoxon

from viu_mrob_tfm.sp1_canonical.validation.benchmark_v3_core import (
    deterministic_case_catalog,
    run_dynamic_event_task,
    run_fractional_scenario,
    stable_hash,
)
from viu_mrob_tfm.sp1_canonical.validation.dynamics_v3 import (
    FRACTIONAL_METHODS,
    DynamicsBudgets,
    budgets_from_mapping,
)
from viu_mrob_tfm.sp1_canonical.validation.statistics import holm_adjust


PREFLIGHT_TESTS = (
    "tests/test_sp1_dynamics_v3.py",
    "tests/test_sp1_conference_v2.py",
    "tests/test_sp1_validation.py",
)

STAGES = ("calibrate", "preview", "full", "audit")


def _git(*arguments: str, allow_failure: bool = False) -> str:
    completed = subprocess.run(["git", *arguments], capture_output=True, text=True, check=False)
    if completed.returncode and not allow_failure:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def _seed_range(spec: Mapping[str, Any]) -> list[int]:
    if "count" in spec:
        return list(range(int(spec["start"]), int(spec["start"]) + int(spec["count"])))
    return list(range(int(spec["start"]), int(spec["stop"]) + 1))


def _load_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {"campaign_id", "preview_id", "calibration", "evaluation", "budgets", "methods"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"missing V3 configuration keys: {sorted(missing)}")
    return config


def _candidate_mapping(config: Mapping[str, Any], index: int) -> dict[str, dict[str, Any]]:
    return {
        method: dict(config["calibration"]["candidates"][method][index])
        for method in FRACTIONAL_METHODS
    }


def _read_selected(path: Path) -> dict[str, dict[str, Any]]:
    selected = yaml.safe_load(path.read_text(encoding="utf-8"))
    methods = selected.get("selected_parameters", selected)
    if set(methods) != set(FRACTIONAL_METHODS):
        raise ValueError("selected parameters must contain exactly the five primary methods")
    return {method: dict(methods[method]) for method in FRACTIONAL_METHODS}


def calibration_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seeds = _seed_range(config["calibration"]["seeds"])
    candidate_count = len(config["calibration"]["candidates"][FRACTIONAL_METHODS[0]])
    if any(len(config["calibration"]["candidates"][method]) != candidate_count for method in FRACTIONAL_METHODS):
        raise ValueError("all methods must receive the same number of calibration candidates")
    for n_value, k_value in config["calibration"]["configurations"]:
        for seed in seeds:
            for candidate_index in range(candidate_count):
                tasks.append(
                    {
                        "kind": "calibration",
                        "experiment": "calibration",
                        "n": int(n_value),
                        "k": int(k_value),
                        "seed": seed,
                        "topology": "rdisk_v2",
                        "candidate_index": candidate_index,
                        "scenario_id": f"cal-N{n_value}-K{k_value}-S{seed}-C{candidate_index}",
                        "history_stride": 100,
                        "attempt_refinement": False,
                    }
                )
    return tasks


def preview_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for n in map(int, config["preview"]["n_values"]):
        k = int(math.ceil(n / 5))
        for seed in map(int, config["preview"]["seeds"]):
            for topology in config["preview"]["topologies"]:
                tasks.append(
                    {
                        "kind": "preview",
                        "experiment": "preview",
                        "n": n,
                        "k": k,
                        "seed": seed,
                        "topology": str(topology),
                        "scenario_id": f"preview-N{n}-K{k}-S{seed}-{topology}",
                        "history_stride": 25,
                        "attempt_refinement": True,
                    }
                )
    return tasks


def full_tasks(config: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    standard: list[dict[str, Any]] = []
    e71 = config["evaluation"]["e71"]
    for n, k in e71["configurations"]:
        for seed in _seed_range(e71["seeds"]):
            standard.append(
                {
                    "kind": "full",
                    "experiment": "e71",
                    "n": int(n),
                    "k": int(k),
                    "seed": seed,
                    "topology": "shared_dual",
                    "scenario_id": f"e71-N{n}-K{k}-S{seed}-shared_dual",
                    "history_stride": 50,
                    "attempt_refinement": True,
                    "include_pure": True,
                }
            )
    e72 = config["evaluation"]["e72"]
    for n, k in e72["configurations"]:
        for seed in _seed_range(e72["seeds"]):
            for topology in e72["topologies"]:
                standard.append(
                    {
                        "kind": "full",
                        "experiment": "e72",
                        "n": int(n),
                        "k": int(k),
                        "seed": seed,
                        "topology": str(topology),
                        "scenario_id": f"e72-N{n}-K{k}-S{seed}-{topology}",
                        "history_stride": 50,
                        "attempt_refinement": True,
                    }
                )
    e73 = config["evaluation"]["e73"]
    for n in map(int, e73["n_values"]):
        k = int(math.ceil(n / 5))
        seed_counts = e73["seed_counts"]
        count = int(seed_counts[n] if n in seed_counts else seed_counts[str(n)])
        for offset in range(count):
            seed = int(e73["seed_start"]) + 1000 * n + offset
            standard.append(
                {
                    "kind": "full",
                    "experiment": "e73",
                    "n": n,
                    "k": k,
                    "seed": seed,
                    "topology": "rdisk_v2",
                    "scenario_id": f"e73-N{n}-K{k}-S{seed}-rdisk_v2",
                    "history_stride": 50,
                    "attempt_refinement": True,
                }
            )
    e74 = config["evaluation"]["e74"]
    for k in map(int, e74["k_values"]):
        for seed in _seed_range(e74["seeds"]):
            standard.append(
                {
                    "kind": "full",
                    "experiment": "e74",
                    "n": int(e74["n"]),
                    "k": k,
                    "seed": seed,
                    "topology": str(e74["topology"]),
                    "target_utilization": float(e74["target_utilization"]),
                    "scenario_id": f"e74-N{e74['n']}-K{k}-S{seed}-rdisk_v2",
                    "history_stride": 50,
                    "attempt_refinement": True,
                }
            )
    dynamic: list[dict[str, Any]] = []
    e75 = config["evaluation"]["e75"]
    for n, k in e75["configurations"]:
        for seed in _seed_range(e75["seeds"]):
            dynamic.append(
                {
                    "kind": "event",
                    "experiment": "e75",
                    "n": int(n),
                    "k": int(k),
                    "seed": seed,
                    "scenario_id": f"e75-N{n}-K{k}-S{seed}",
                }
            )
    return standard, dynamic


def expected_primary_count(config: Mapping[str, Any], stage: str) -> int:
    if stage == "calibrate":
        return len(calibration_tasks(config)) * len(FRACTIONAL_METHODS)
    if stage == "preview":
        return len(preview_tasks(config)) * len(FRACTIONAL_METHODS)
    standard, dynamic = full_tasks(config)
    event_count = len(config["evaluation"]["e75"]["events"])
    return len(standard) * len(FRACTIONAL_METHODS) + len(dynamic) * event_count * len(FRACTIONAL_METHODS)


def _run_task(payload: tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    config, task, selected, budget_values = payload
    budgets = budgets_from_mapping(budget_values)
    if task["kind"] == "event":
        return run_dynamic_event_task(config, selected, task, budgets)
    if task["kind"] == "calibration":
        overrides = _candidate_mapping(config, int(task["candidate_index"]))
        result = run_fractional_scenario(
            config,
            selected,
            task,
            budgets,
            include_references=False,
            include_pure=False,
            include_recovery=False,
            parameters_override=overrides,
        )
        for row in result["runs"]:
            candidate = overrides[str(row["method"])]
            row["candidate_id"] = candidate["candidate_id"]
            row["is_primary"] = True
        return result
    return run_fractional_scenario(
        config,
        selected,
        task,
        budgets,
        include_references=True,
        include_pure=bool(task.get("include_pure", task["kind"] == "preview")),
        include_recovery=True,
    )


def _write_shard(directory: Path, shard_id: str, result: Mapping[str, list[dict[str, Any]]]) -> None:
    shard = directory / shard_id
    shard.mkdir(parents=True, exist_ok=True)
    for key in ("runs", "traces", "message_validation"):
        temporary = shard / f"{key}.json.tmp"
        temporary.write_text(
            json.dumps(result.get(key, []), ensure_ascii=False, allow_nan=True),
            encoding="utf-8",
        )
        temporary.replace(shard / f"{key}.json")
    (shard / "SUCCESS.json").write_text(json.dumps({"shard_id": shard_id}), encoding="utf-8")


def _read_shard(directory: Path, shard_id: str) -> dict[str, list[dict[str, Any]]]:
    shard = directory / shard_id
    return {
        key: json.loads((shard / f"{key}.json").read_text(encoding="utf-8"))
        for key in ("runs", "traces", "message_validation")
    }


def execute_tasks(
    config: dict[str, Any],
    tasks: list[dict[str, Any]],
    selected: dict[str, dict[str, Any]],
    budget_values: dict[str, Any],
    checkpoint_dir: Path,
    *,
    resume: bool,
) -> dict[str, pd.DataFrame]:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, list[dict[str, Any]]]] = []
    pending: list[tuple[str, dict[str, Any]]] = []
    for task in tasks:
        shard_id = stable_hash(task)[:24]
        success = checkpoint_dir / shard_id / "SUCCESS.json"
        if resume and success.exists():
            results.append(_read_shard(checkpoint_dir, shard_id))
        else:
            pending.append((shard_id, task))
    completed_count = len(tasks) - len(pending)
    if pending:
        workers = max(1, int(config.get("parallel_workers", 1)))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_run_task, (config, task, selected, budget_values)): shard_id
                for shard_id, task in pending
            }
            for future in as_completed(futures):
                shard_id = futures[future]
                result = future.result()
                _write_shard(checkpoint_dir, shard_id, result)
                results.append(result)
                completed_count += 1
                print(f"[V3] checkpoint {completed_count}/{len(tasks)} ({shard_id})", flush=True)
    frames: dict[str, pd.DataFrame] = {}
    for key in ("runs", "traces", "message_validation"):
        rows = [row for result in results for row in result.get(key, [])]
        frames[key] = pd.DataFrame(rows)
    return frames


def _select_parameters(config: Mapping[str, Any], runs: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    primary = runs[runs["method"].isin(FRACTIONAL_METHODS)].copy()
    residual_columns = ["primal_residual", "consensus_residual", "fixed_point_residual"]
    primary["terminal_residual"] = primary[residual_columns].max(axis=1)
    summary = (
        primary.groupby(["method", "candidate_id"], as_index=False)
        .agg(
            worlds=("scenario_id", "count"),
            convergence_rate=("operational_converged", "mean"),
            median_terminal_residual=("terminal_residual", "median"),
            median_scalars=("scalar_transmissions_total", "median"),
            median_wall_time_s=("wall_time_s", "median"),
            simplex_violation_max=("simplex_violation", "max"),
            mask_violation_max=("mask_violation", "max"),
        )
        .sort_values(
            ["method", "convergence_rate", "median_terminal_residual", "median_scalars", "median_wall_time_s"],
            ascending=[True, False, True, True, True],
        )
    )
    selected: dict[str, dict[str, Any]] = {}
    for method in FRACTIONAL_METHODS:
        winner = summary[summary.method == method].iloc[0]
        candidate_id = str(winner.candidate_id)
        candidate = next(
            dict(value)
            for value in config["calibration"]["candidates"][method]
            if str(value["candidate_id"]) == candidate_id
        )
        candidate["selection_metrics"] = {
            "convergence_rate": float(winner.convergence_rate),
            "median_terminal_residual": float(winner.median_terminal_residual),
            "median_scalars": float(winner.median_scalars),
            "median_wall_time_s": float(winner.median_wall_time_s),
        }
        selected[method] = candidate
    return summary, selected


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _km_rmst(durations: np.ndarray, observed: np.ndarray, tau: float) -> float:
    if len(durations) == 0:
        return math.nan
    order = np.argsort(durations)
    durations = durations[order]
    observed = observed[order]
    survival = 1.0
    previous = 0.0
    area = 0.0
    for instant in np.unique(durations[durations <= tau]):
        area += survival * (float(instant) - previous)
        at_risk = int(np.sum(durations >= instant))
        events = int(np.sum((durations == instant) & observed))
        if at_risk:
            survival *= 1.0 - events / at_risk
        previous = float(instant)
    area += survival * max(float(tau) - previous, 0.0)
    return float(area)


def aggregate_results(runs: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    primary = runs[runs.is_primary.astype(bool)].copy()
    rows: list[dict[str, Any]] = []
    group_columns = ["experiment", "method", "n_robots", "n_loads", "topology"]
    for keys, group in primary.groupby(group_columns, dropna=False):
        successes = int(group.operational_converged.astype(bool).sum())
        low, high = _wilson(successes, len(group))
        limit = float(config["budgets"]["evaluation"]["max_logical_rounds"])
        durations = group.operational_round.fillna(limit).to_numpy(dtype=float)
        observed = group.operational_converged.astype(bool).to_numpy()
        rows.append(
            {
                **dict(zip(group_columns, keys)),
                "runs": len(group),
                "converged": successes,
                "convergence_rate": successes / len(group),
                "convergence_wilson_low": low,
                "convergence_wilson_high": high,
                "integer_feasibility_rate": float(group.integer_feasibility.fillna(False).astype(bool).mean()),
                "censored": int(group.censored.fillna(False).astype(bool).sum()),
                "rmst_rounds": _km_rmst(durations, observed, limit),
                "median_wall_time_s": float(group.wall_time_s.median()),
                "median_packets": float(group.packets_total.median()),
                "median_scalars": float(group.scalar_transmissions_total.median()),
                "median_bytes": float(group.payload_bytes_total.median()),
                "median_payoff_evaluations": float(group.payoff_evaluations.median()),
                "median_MILP_gap": float(group.MILP_gap.dropna().median()) if group.MILP_gap.notna().any() else math.nan,
                "simplex_violation_max": float(group.simplex_violation.max()),
                "mask_violation_max": float(group.mask_violation.max()),
            }
        )
    return pd.DataFrame(rows)


def _rank_biserial(differences: np.ndarray) -> float:
    differences = differences[np.isfinite(differences) & (differences != 0)]
    if len(differences) == 0:
        return 0.0
    ranks = pd.Series(np.abs(differences)).rank(method="average").to_numpy()
    positive = float(np.sum(ranks[differences > 0]))
    negative = float(np.sum(ranks[differences < 0]))
    return (positive - negative) / max(positive + negative, 1e-12)


def _paired_bootstrap_median(differences: np.ndarray, seed: int, repetitions: int) -> tuple[float, float]:
    differences = differences[np.isfinite(differences)]
    if len(differences) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    estimates = np.empty(repetitions)
    for index in range(repetitions):
        estimates[index] = np.median(rng.choice(differences, size=len(differences), replace=True))
    return tuple(map(float, np.quantile(estimates, [0.025, 0.975])))


def paired_comparisons(runs: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    primary = runs[runs.is_primary.astype(bool)].copy()
    replicate = primary[primary.method == "Replicator-D-preconditioned"]
    rows: list[dict[str, Any]] = []
    repetitions = int(config["repetitions"]["bootstrap"])
    seed = int(config["analysis_seed"])
    for experiment in sorted(primary.experiment.unique()):
        base = replicate[replicate.experiment == experiment]
        for method in FRACTIONAL_METHODS[1:]:
            other = primary[(primary.experiment == experiment) & (primary.method == method)]
            merged = base.merge(other, on="scenario_id", suffixes=("_rep", "_method"))
            if merged.empty:
                continue
            rep_success = merged.operational_converged_rep.astype(bool).to_numpy()
            method_success = merged.operational_converged_method.astype(bool).to_numpy()
            b = int(np.sum(~rep_success & method_success))
            c = int(np.sum(rep_success & ~method_success))
            mcnemar_p = float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0
            rows.append(
                {
                    "experiment": experiment,
                    "method": method,
                    "endpoint": "operational_convergence",
                    "pairs": len(merged),
                    "estimate": float(np.mean(method_success.astype(float) - rep_success.astype(float))),
                    "ci_low": math.nan,
                    "ci_high": math.nan,
                    "p_value": mcnemar_p,
                    "effect_size": float((b - c) / max(b + c, 1)),
                    "test": "McNemar exact",
                }
            )
            for metric in ("wall_time_s", "payload_bytes_total", "MILP_gap"):
                left = pd.to_numeric(merged[f"{metric}_rep"], errors="coerce").to_numpy(dtype=float)
                right = pd.to_numeric(merged[f"{metric}_method"], errors="coerce").to_numpy(dtype=float)
                valid = np.isfinite(left) & np.isfinite(right)
                differences = right[valid] - left[valid]
                if len(differences) == 0:
                    continue
                low, high = _paired_bootstrap_median(differences, seed + len(rows), repetitions)
                try:
                    p_value = float(wilcoxon(differences).pvalue) if np.any(differences != 0) else 1.0
                except ValueError:
                    p_value = 1.0
                rows.append(
                    {
                        "experiment": experiment,
                        "method": method,
                        "endpoint": metric,
                        "pairs": len(differences),
                        "estimate": float(np.median(differences)),
                        "ci_low": low,
                        "ci_high": high,
                        "p_value": p_value,
                        "effect_size": _rank_biserial(differences),
                        "test": "Wilcoxon signed-rank",
                    }
                )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["p_holm"] = np.nan
        for _, indices in frame.groupby(["experiment", "endpoint"]).groups.items():
            frame.loc[indices, "p_holm"] = holm_adjust(frame.loc[indices, "p_value"].tolist())
    return frame


def regime_map(
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    paired: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    primary = runs[runs.is_primary.astype(bool)]
    gate = config["improvement_gate"]
    rows: list[dict[str, Any]] = []
    for keys, group in primary.groupby(["experiment", "n_robots", "n_loads", "topology"], dropna=False):
        rep = group[group.method == "Replicator-D-preconditioned"]
        for method in FRACTIONAL_METHODS[1:]:
            other = group[group.method == method]
            merged = rep.merge(other, on="scenario_id", suffixes=("_rep", "_method"))
            if merged.empty:
                continue
            risk_difference = float(
                np.mean(merged.operational_converged_method.astype(float) - merged.operational_converged_rep.astype(float))
            )
            discordant_good = int(np.sum(~merged.operational_converged_rep.astype(bool) & merged.operational_converged_method.astype(bool)))
            discordant_bad = int(np.sum(merged.operational_converged_rep.astype(bool) & ~merged.operational_converged_method.astype(bool)))
            p_value = float(binomtest(min(discordant_good, discordant_bad), discordant_good + discordant_bad, 0.5).pvalue) if discordant_good + discordant_bad else 1.0
            rep_wall = float(merged.wall_time_s_rep.median())
            method_wall = float(merged.wall_time_s_method.median())
            rep_bytes = float(merged.payload_bytes_total_rep.median())
            method_bytes = float(merged.payload_bytes_total_method.median())
            wall_reduction = 1.0 - method_wall / max(rep_wall, 1e-12)
            byte_reduction = 1.0 - method_bytes / max(rep_bytes, 1e-12) if rep_bytes > 0 else 0.0
            feasibility = float(merged.integer_feasibility_method.fillna(False).astype(bool).mean())
            gap_difference = pd.to_numeric(merged.MILP_gap_method, errors="coerce") - pd.to_numeric(merged.MILP_gap_rep, errors="coerce")
            gap_noninferior = bool(gap_difference.dropna().median() <= float(gate["milp_gap_noninferiority_margin"])) if gap_difference.notna().any() else False
            no_violations = bool(
                (merged.simplex_violation_method <= 1e-8).all()
                and (merged.mask_violation_method <= 1e-10).all()
                and (merged.consensus_residual_method.fillna(math.inf) <= 1e-4).loc[merged.operational_converged_method.astype(bool)].all()
            )
            improvement = bool(
                risk_difference >= float(gate["convergence_risk_difference_min"])
                and p_value < 0.05
                and max(wall_reduction, byte_reduction) >= float(gate["resource_reduction_min"])
                and feasibility >= float(gate["integer_feasibility_min"])
                and gap_noninferior
                and no_violations
            )
            if improvement:
                label = "operationally_better_than_replicator"
            elif risk_difference >= 0.10 and max(wall_reduction, byte_reduction) >= 0.30:
                label = "speed_or_convergence_tradeoff"
            else:
                label = "no_joint_improvement"
            rows.append(
                {
                    "experiment": keys[0],
                    "n_robots": keys[1],
                    "n_loads": keys[2],
                    "topology": keys[3],
                    "method": method,
                    "pairs": len(merged),
                    "convergence_risk_difference": risk_difference,
                    "mcnemar_p": p_value,
                    "wall_time_reduction": wall_reduction,
                    "byte_reduction": byte_reduction,
                    "integer_feasibility_rate": feasibility,
                    "gap_noninferior": gap_noninferior,
                    "no_new_invariant_violations": no_violations,
                    "joint_improvement": improvement,
                    "regime_label": label,
                }
            )
    return pd.DataFrame(rows)


def method_complexity() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"method": "Replicator-D-preconditioned", "revision_cost": "O(K)", "payoff_comparisons": "0", "consensus_exchanges_per_round": 2, "fractional": True},
            {"method": "Smith-D-preconditioned", "revision_cost": "O(K^2)", "payoff_comparisons": "N*(K+1)*K", "consensus_exchanges_per_round": 1, "fractional": True},
            {"method": "BNN-D-preconditioned", "revision_cost": "O(K)", "payoff_comparisons": "0", "consensus_exchanges_per_round": 1, "fractional": True},
            {"method": "Logit-D-annealed", "revision_cost": "O(K)", "payoff_comparisons": "0", "consensus_exchanges_per_round": 1, "fractional": True},
            {"method": "BestResponse-D", "revision_cost": "O(K)", "payoff_comparisons": "N*K", "consensus_exchanges_per_round": 1, "fractional": True},
            {"method": "BestResponse-pure", "revision_cost": "O(K) per activation", "payoff_comparisons": "K per activation", "consensus_exchanges_per_round": "event-driven", "fractional": False},
        ]
    )


def _censoring_table(runs: pd.DataFrame) -> pd.DataFrame:
    primary = runs[runs.is_primary.astype(bool)].copy()
    columns = ["experiment", "scenario_id", "world_id", "method", "n_robots", "n_loads", "topology", "censoring_reason", "logical_rounds", "wall_time_s", "scalar_transmissions_total"]
    return primary[primary.censored.fillna(False).astype(bool)][columns]


def _exclusions_table(runs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in runs.to_dict(orient="records"):
        if record.get("experiment") == "e75" and not bool(record.get("valid_event_origin", True)):
            rows.append({"scenario_id": record["scenario_id"], "method": record["method"], "reason": "pre_event_nonconverged", "excluded_from": "dynamic_confirmatory_contrast"})
        if record.get("is_primary") and not bool(record.get("oracle_certified", False)):
            rows.append({"scenario_id": record["scenario_id"], "method": record["method"], "reason": "milp_not_certified_or_not_run", "excluded_from": "MILP_gap_only"})
    return pd.DataFrame(rows, columns=["scenario_id", "method", "reason", "excluded_from"])


def _preview_gates(runs: pd.DataFrame, validation: pd.DataFrame, tests_passed: bool, expected: int) -> dict[str, bool]:
    primary = runs[runs.is_primary.astype(bool)]
    censor_reasons = set(primary.censoring_reason.dropna().astype(str))
    allowed = {"none", "max_rounds", "wall_time", "communication_budget", "payoff_budget", "numerical_failure", "disconnected_graph", "invalid_state"}
    br = primary[primary.method.isin(["Logit-D-annealed", "BestResponse-D"])]
    trivial_oscillation = bool((br.censoring_reason == "numerical_failure").mean() > 0.5) if len(br) else True
    return {
        "tests_pass": tests_passed,
        "exact_primary_run_count": len(primary) == expected,
        "no_simplex_violation": bool((primary.simplex_violation <= 1e-8).all()),
        "no_mask_violation": bool((primary.mask_violation <= 1e-10).all()),
        "no_nan_or_inf": bool(primary.finite_state.astype(bool).all()),
        "message_accounting_consistent": bool(not validation.empty and validation.valid.astype(bool).all()),
        "all_methods_produce_rows": set(primary.method) == set(FRACTIONAL_METHODS),
        "all_methods_every_scenario": bool(primary.groupby("scenario_id").method.nunique().eq(len(FRACTIONAL_METHODS)).all()),
        "censoring_recorded": censor_reasons <= allowed and bool(primary.loc[primary.censored.astype(bool), "censoring_reason"].ne("none").all()),
        "no_recovery_after_nonconvergence": bool((~primary.recovery_executed.fillna(False).astype(bool) | primary.operational_converged.astype(bool)).all()),
        "no_generalized_trivial_logit_br_failure": not trivial_oscillation,
    }


def audit_checks(
    runs: pd.DataFrame,
    validation: pd.DataFrame,
    config: Mapping[str, Any],
    *,
    stage: str,
    tests_passed: bool,
    git_clean_start: bool,
    git_clean_end: bool,
    hashes_valid: bool,
) -> dict[str, bool]:
    primary = runs[runs.is_primary.astype(bool)]
    expected = expected_primary_count(config, stage)
    calibration_seeds = set(_seed_range(config["calibration"]["seeds"]))
    evaluation_seeds = set(primary.seed.astype(int)) if stage != "calibrate" else set()
    allowed = {"none", "max_rounds", "wall_time", "communication_budget", "payoff_budget", "numerical_failure", "disconnected_graph", "invalid_state"}
    return {
        "preflight_tests_passed": tests_passed,
        "exact_run_count": len(primary) == expected,
        "all_methods_every_world": bool(primary.groupby("scenario_id").method.nunique().eq(len(FRACTIONAL_METHODS)).all()),
        "paired_origin_identical": bool(primary.groupby("scenario_id").agg({"world_hash": "nunique", "cost_hash": "nunique", "initial_state_hash": "nunique"}).le(1).all().all()),
        "graph_identical_across_methods": bool(primary.groupby("scenario_id").graph_hash.nunique().eq(1).all()),
        "no_simplex_violation": bool((primary.simplex_violation <= 1e-8).all()),
        "no_mask_violation": bool((primary.mask_violation <= 1e-10).all()),
        "no_nan_or_inf": bool(primary.finite_state.astype(bool).all()),
        "no_recovery_after_nonconvergence": bool((~primary.recovery_executed.fillna(False).astype(bool) | primary.operational_converged.astype(bool)).all()),
        "message_counts_recomputable": bool(not validation.empty and validation.valid.astype(bool).all()),
        "all_censoring_reasons_recorded": set(primary.censoring_reason.dropna().astype(str)) <= allowed,
        "calibration_seeds_disjoint": calibration_seeds.isdisjoint(evaluation_seeds),
        "evaluation_seeds_disjoint": evaluation_seeds.isdisjoint(calibration_seeds),
        "git_clean_start": git_clean_start,
        "git_clean_end": git_clean_end,
        "all_artifact_hashes_valid": hashes_valid,
    }


def _save_figure(figure: plt.Figure, directory: Path, name: str) -> None:
    figure.savefig(directory / f"{name}.pdf", bbox_inches="tight")
    figure.savefig(directory / f"{name}.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def make_figures(runs: pd.DataFrame, aggregate: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    primary = runs[runs.is_primary.astype(bool)].copy()
    colors = dict(zip(FRACTIONAL_METHODS, ["#355C7D", "#C06C84", "#6C5B7B", "#F67280", "#2A9D8F"]))
    style = {"axes.grid": True, "grid.alpha": 0.25, "figure.facecolor": "white", "axes.facecolor": "#FBFCFE"}
    with plt.rc_context(style):
        # F1
        heat = aggregate[aggregate.experiment.isin(["e73", "e74"])].copy()
        labels = sorted({f"N={int(row.n_robots)},K={int(row.n_loads)}" for row in heat.itertuples()})
        matrix = np.full((len(FRACTIONAL_METHODS), len(labels)), np.nan)
        for i, method in enumerate(FRACTIONAL_METHODS):
            for j, label in enumerate(labels):
                n = int(label.split(",")[0].split("=")[1])
                k = int(label.split("=")[2])
                values = heat[(heat.method == method) & (heat.n_robots == n) & (heat.n_loads == k)].convergence_rate
                if len(values):
                    matrix[i, j] = float(values.mean())
        figure, axis = plt.subplots(figsize=(max(8, len(labels) * 0.75), 4.8), constrained_layout=True)
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap="viridis", aspect="auto")
        axis.set_yticks(range(len(FRACTIONAL_METHODS)), [m.replace("-D-preconditioned", "") for m in FRACTIONAL_METHODS])
        axis.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
        axis.set_title("Convergencia operacional por método y régimen")
        figure.colorbar(image, ax=axis, label="Tasa de convergencia")
        _save_figure(figure, directory, "F1_v3_convergence_heatmap_method_N_K")

        # F2: KM in E73
        figure, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True, sharey=True)
        e73 = primary[primary.experiment == "e73"]
        for axis, n in zip(axes, [20, 100, 500]):
            subset_n = e73[e73.n_robots == n]
            for method in FRACTIONAL_METHODS:
                group = subset_n[subset_n.method == method]
                if group.empty:
                    continue
                durations = group.operational_round.fillna(group.logical_rounds).to_numpy(dtype=float)
                events = group.operational_converged.astype(bool).to_numpy()
                order = np.argsort(durations)
                duration_values, event_values = durations[order], events[order]
                survival = 1.0
                xs, ys = [0.0], [1.0]
                for instant in np.unique(duration_values):
                    at_risk = int(np.sum(duration_values >= instant))
                    event_count = int(np.sum((duration_values == instant) & event_values))
                    xs.extend([float(instant), float(instant)])
                    ys.extend([survival, survival * (1 - event_count / max(at_risk, 1))])
                    survival = ys[-1]
                axis.step(xs, ys, where="post", color=colors[method], label=method.split("-")[0])
                censored = duration_values[~event_values]
                if len(censored):
                    axis.scatter(censored, np.interp(censored, xs, ys), marker="|", color=colors[method], s=40)
            axis.set_title(f"N={n}")
            axis.set_xlabel("Rondas (marcas = censura)")
        axes[0].set_ylabel("Probabilidad de no converger")
        axes[-1].legend(fontsize=7)
        _save_figure(figure, directory, "F2_v3_time_to_convergence_censored")

        # F3
        figure, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)
        e73a = aggregate[aggregate.experiment == "e73"]
        for method in FRACTIONAL_METHODS:
            group = e73a[e73a.method == method].sort_values("n_robots")
            for axis, metric, label in zip(axes, ["median_packets", "median_scalars", "median_bytes"], ["Paquetes", "Escalares", "Bytes"]):
                axis.plot(group.n_robots, group[metric], marker="o", color=colors[method], label=method.split("-")[0])
                axis.set_yscale("symlog", linthresh=1)
                axis.set_xscale("log")
                axis.set_xlabel("N")
                axis.set_ylabel(label)
        axes[-1].legend(fontsize=7)
        _save_figure(figure, directory, "F3_v3_messages_bytes_vs_N")

        # F4
        figure, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)
        e74a = aggregate[aggregate.experiment == "e74"]
        for method in FRACTIONAL_METHODS:
            group = e74a[e74a.method == method].sort_values("n_loads")
            for axis, metric, label in zip(axes, ["median_wall_time_s", "median_payoff_evaluations", "median_bytes"], ["Tiempo [s]", "Evaluaciones", "Bytes"]):
                axis.plot(group.n_loads, group[metric], marker="o", color=colors[method], label=method.split("-")[0])
                axis.set_yscale("symlog", linthresh=1e-6)
                axis.set_xlabel("K")
                axis.set_ylabel(label)
        axes[-1].legend(fontsize=7)
        _save_figure(figure, directory, "F4_v3_scalability_vs_K")

        # F5
        figure, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)
        e72 = primary[primary.experiment == "e72"]
        for method in FRACTIONAL_METHODS:
            group = e72[e72.method == method]
            axes[0].scatter(group.lambda_2, group.operational_converged.astype(float), alpha=0.35, s=12, color=colors[method], label=method.split("-")[0])
            axes[1].scatter(group.lambda_2, group.logical_rounds, alpha=0.35, s=12, color=colors[method])
            axes[2].scatter(group.lambda_2, group.payload_bytes_total, alpha=0.35, s=12, color=colors[method])
        for axis, ylabel in zip(axes, ["Convergió", "Rondas", "Bytes"]):
            axis.set_xscale("symlog", linthresh=1e-6)
            axis.set_yscale("symlog", linthresh=1e-6)
            axis.set_xlabel(r"$\lambda_2(L)$")
            axis.set_ylabel(ylabel)
        axes[0].legend(fontsize=7)
        _save_figure(figure, directory, "F5_v3_topology_lambda2_interaction")

        # F6
        figure, axis = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
        support = primary[primary.reactivation_round.notna()]
        for index, method in enumerate(FRACTIONAL_METHODS):
            values = support[support.method == method].reactivation_round.to_numpy(dtype=float)
            if len(values):
                axis.boxplot(values, positions=[index], widths=0.6, showfliers=True)
        axis.set_xticks(range(len(FRACTIONAL_METHODS)), [m.split("-")[0] for m in FRACTIONAL_METHODS], rotation=25, ha="right")
        axis.set_ylabel("Ronda de reactivación")
        axis.set_title("Reactivación de estrategias con masa nula o casi nula")
        _save_figure(figure, directory, "F6_v3_support_reactivation")

        # F7
        figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
        feasibility = primary.groupby("method").integer_feasibility.mean().reindex(FRACTIONAL_METHODS)
        axes[0].bar(range(len(feasibility)), feasibility.values, color=[colors[m] for m in feasibility.index])
        axes[0].set_xticks(range(len(feasibility)), [m.split("-")[0] for m in feasibility.index], rotation=25, ha="right")
        axes[0].set_ylim(0, 1)
        axes[0].set_ylabel("Factibilidad tras recovery")
        gap_data = [primary.loc[(primary.method == method) & primary.MILP_gap.notna(), "MILP_gap"].to_numpy() for method in FRACTIONAL_METHODS]
        axes[1].boxplot(gap_data, labels=[m.split("-")[0] for m in FRACTIONAL_METHODS], showfliers=False)
        axes[1].tick_params(axis="x", rotation=25)
        axes[1].set_ylabel("Gap MILP certificado")
        _save_figure(figure, directory, "F7_v3_integer_quality")

        # F8
        e75 = primary[primary.experiment == "e75"]
        valid_origins = e75[e75.valid_event_origin.eq(True)]
        if valid_origins.empty:
            figure, axis = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
            counts = e75.groupby("method").valid_event_origin.sum().reindex(FRACTIONAL_METHODS, fill_value=0).astype(int)
            totals = e75.groupby("method").size().reindex(FRACTIONAL_METHODS, fill_value=0).astype(int)
            positions = np.arange(len(FRACTIONAL_METHODS))
            axis.bar(positions, counts.to_numpy(), color=[colors[m] for m in FRACTIONAL_METHODS])
            axis.set_xticks(positions, [m.split("-")[0] for m in FRACTIONAL_METHODS], rotation=25, ha="right")
            axis.set_ylim(0, 1)
            axis.set_yticks([0, 1])
            axis.set_ylabel("Orígenes dinámicos válidos")
            for position, count, total in zip(positions, counts, totals):
                axis.text(position, 0.04, f"{count}/{total}", ha="center", va="bottom", fontsize=9)
            axis.text(
                0.5,
                0.72,
                "Recuperación no ejecutada:\nningún método convergió antes del evento",
                transform=axis.transAxes,
                ha="center",
                va="center",
                fontsize=13,
                bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "0.35"},
            )
            axis.set_title("E7.5 — evidencia de recuperación dinámica")
        else:
            figure, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)
            for method in FRACTIONAL_METHODS:
                group = valid_origins[valid_origins.method == method]
                med = group.groupby("event")[["recovery_rounds", "hamming_recourse", "recovery_bytes"]].median()
                x = np.arange(len(med))
                for axis, metric in zip(axes, ["recovery_rounds", "hamming_recourse", "recovery_bytes"]):
                    axis.plot(x, med[metric], marker="o", color=colors[method], label=method.split("-")[0])
                    axis.set_xticks(x, med.index, rotation=25, ha="right")
                    axis.set_yscale("symlog", linthresh=1e-6)
                    axis.set_ylabel(metric)
            axes[-1].legend(fontsize=7)
        _save_figure(figure, directory, "F8_v3_dynamic_recovery")

        # F9
        figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
        for method in FRACTIONAL_METHODS:
            group = primary[primary.method == method]
            axes[0].scatter(group.payload_bytes_total, group.MILP_gap, alpha=0.3, s=12, color=colors[method], label=method.split("-")[0])
            grouped = group.groupby(["experiment", "n_robots", "n_loads"]).agg(bytes=("payload_bytes_total", "median"), feasible=("integer_feasibility", "mean"))
            axes[1].scatter(grouped.bytes, grouped.feasible, s=28, color=colors[method])
        axes[0].set_xscale("symlog", linthresh=1)
        axes[0].set_xlabel("Bytes")
        axes[0].set_ylabel("Gap MILP")
        axes[1].set_xscale("symlog", linthresh=1)
        axes[1].set_xlabel("Bytes medianos")
        axes[1].set_ylabel("Factibilidad")
        axes[0].legend(fontsize=7)
        _save_figure(figure, directory, "F9_v3_pareto_quality_communication")


def _runtime_storage_estimate(runs: pd.DataFrame, output: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    primary = runs[runs.is_primary.astype(bool)]
    full_count = expected_primary_count(config, "full")
    seconds_per_run = float(primary.wall_time_s.mean()) if len(primary) else math.nan
    bytes_now = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    return {
        "preview_primary_runs": len(primary),
        "full_primary_runs": full_count,
        "mean_wall_time_per_preview_run_s": seconds_per_run,
        "serial_full_runtime_estimate_s": seconds_per_run * full_count,
        "parallel_workers": int(config.get("parallel_workers", 1)),
        "parallel_full_runtime_estimate_s": seconds_per_run * full_count / max(int(config.get("parallel_workers", 1)), 1),
        "preview_storage_bytes": bytes_now,
        "full_storage_estimate_bytes": int(bytes_now * full_count / max(len(primary), 1)),
    }


def _write_hashes(base: Path) -> tuple[list[dict[str, str]], bool]:
    excluded = {"checksums.sha256", "audit.json", "manifest.json"}
    paths = [path for path in base.rglob("*") if path.is_file() and path.name not in excluded and "checkpoints" not in path.parts]
    records = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append({"sha256": digest, "path": path.relative_to(base).as_posix()})
    text = "".join(f"{row['sha256']}  {row['path']}\n" for row in records)
    (base / "checksums.sha256").write_text(text, encoding="utf-8")
    valid = all(hashlib.sha256((base / row["path"]).read_bytes()).hexdigest() == row["sha256"] for row in records)
    return records, valid


def _preflight(base: Path) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", *PREFLIGHT_TESTS, "-q"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    result = {
        "command": command,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    (base / "preflight_tests.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _report(
    config: Mapping[str, Any],
    runs: pd.DataFrame,
    aggregate: pd.DataFrame,
    censoring: pd.DataFrame,
    regimes: pd.DataFrame,
    preview_gates: Mapping[str, bool] | None,
    duration_s: float,
) -> str:
    primary = runs[runs.is_primary.astype(bool)]
    rates = primary.groupby("method").operational_converged.mean().sort_values(ascending=False)
    feasibility = primary.groupby("method").integer_feasibility.mean().sort_values(ascending=False)
    joint = regimes[regimes.joint_improvement.astype(bool)] if not regimes.empty else pd.DataFrame()
    e75 = primary[primary.experiment == "e75"]
    valid_event_origins = int(e75.valid_event_origin.eq(True).sum())
    recovery_executions = int(e75.recovery_executed.eq(True).sum())
    topology_complete = primary[(primary.experiment == "e72") & (primary.topology == "complete")].operational_converged.mean()
    topology_rdisk = primary[(primary.experiment == "e72") & (primary.topology != "complete")].operational_converged.mean()
    if not joint.empty:
        conclusion = "E: existen mejoras conjuntas en regímenes delimitados, sin ganador universal."
    elif np.isfinite(topology_complete) and np.isfinite(topology_rdisk) and topology_complete - topology_rdisk >= 0.10:
        conclusion = "B/D: el deterioro dominante aparece al introducir topología local/consenso; cambiar solo la revisión no satisface el gate conjunto."
    else:
        conclusion = "D/E: ninguna dinámica satisface de forma universal el gate conjunto; los resultados exigen un mapa de regímenes y posible rediseño de comunicación."
    lines = [
        "# SP1_DYNAMICS_BENCHMARK_v3",
        "",
        "## 1. Pregunta científica",
        "",
        "La campaña separa geometría primal, consenso, topología, N y K. No presupone un ganador ni interpreta una ejecución censurada como solución.",
        "",
        "## 2. Protocolo",
        "",
        f"Se ejecutaron {len(primary)} runs primarios pareados en {primary.scenario_id.nunique()} escenarios; duración de generación y análisis: {duration_s:.1f} s. Las semillas 70000–70019 se reservaron a calibración.",
        "",
        "## 3. Fórmulas de las dinámicas",
        "",
        "Replicator conserva el mirror-prox V2. Smith usa flujos pareados positivos; BNN usa exceso positivo respecto al fitness medio; Logit sigue el punto fijo softmax con annealing; BestResponse-D combina convexamente el estado con un argmax de desempate determinista. BestResponse-pure es un comparador entero asíncrono separado.",
        "",
        "## 4. Criterios de parada",
        "",
        "El gate operacional combina residual primal normalizado 1e-3, consenso 1e-4 y residual de punto fijo específico 1e-3. El refinamiento usa 1e-6, 1e-4 y 1e-4. Los límites de rondas, pared, escalares y evaluaciones producen censura explícita.",
        "",
        "## 5. Definición de mensaje",
        "",
        "Un paquete es un vector transmitido en una dirección sobre una arista durante un intercambio. El payload concatena dual y tracker PI (2*K*M float64); los bytes excluyen headers y valen 8 por escalar.",
        "",
        "## 6. Resultados de preview",
        "",
        (json.dumps(preview_gates, ensure_ascii=False, indent=2) if preview_gates is not None else "El preview se conserva en su paquete independiente."),
        "",
        "## 7. Resultados completos",
        "",
        "Tasa operacional por método: " + "; ".join(f"{method}={value:.3f}" for method, value in rates.items()) + ".",
        "Factibilidad entera condicionada por el protocolo: " + "; ".join(f"{method}={value:.3f}" for method, value in feasibility.items()) + ".",
        "",
        "## 8. Censura",
        "",
        f"Se registraron {len(censoring)} censuras primarias. Distribución: {censoring.censoring_reason.value_counts().to_dict() if len(censoring) else {}}.",
        "",
        "## 9. E7.5 y recuperación",
        "",
        f"E7.5 produjo {valid_event_origins} orígenes dinámicos válidos y {recovery_executions} recuperaciones ejecutadas en {len(e75)} runs primarios. Sin convergencia operacional previa al evento, la campaña no aporta evidencia sobre tiempo, calidad ni coste de recuperación.",
        "",
        "## 10. Mapa de regímenes",
        "",
        f"El gate conjunto se satisfizo en {len(joint)} comparaciones de régimen. Conclusión predeclarada: {conclusion}",
        "",
        "## 11. Claims permitidos",
        "",
        "Se permiten observaciones empíricas restringidas a mundos sintéticos, presupuestos, topologías y tolerancias registrados; diferencias de coste, calidad y convergencia se presentan como dependientes del régimen.",
        "",
        "## 12. Claims prohibidos",
        "",
        "No se afirma convergencia global, escalabilidad por alcanzar N=500, novedad de Smith/BNN/Logit, optimalidad de recovery, ni que menos rondas implique menor coste. LP/MILP no son distribuidos.",
        "",
        "## 13. Limitaciones",
        "",
        "La evidencia es simulada y estratégica; E7.5 configuró eventos, pero no alcanzó orígenes operacionales válidos y no ejecutó recuperación. No incluye navegación ni transporte. El estimador de escala no es una constante de Lipschitz demostrada. La recuperación es heurística y el payload omite headers/protocolo físico.",
        "",
        "## Conclusión A–E",
        "",
        conclusion,
    ]
    return "\n".join(lines) + "\n"


def _readme(config_path: Path, selected_path: Path, output: Path) -> str:
    return f"""# Reproducción de SP1_DYNAMICS_BENCHMARK_v3

Ejecutar desde un checkout limpio de la rama registrada en `manifest.json`:

```powershell
python -m pytest {' '.join(PREFLIGHT_TESTS)} -q
python -m viu_mrob_tfm.cli.run_sp1_dynamics_v3 --config {config_path.as_posix()} --stage calibrate --output-dir {output.as_posix()} --resume
python -m viu_mrob_tfm.cli.run_sp1_dynamics_v3 --config {config_path.as_posix()} --stage preview --selected-parameters {selected_path.as_posix()} --output-dir {output.as_posix()} --resume
python -m viu_mrob_tfm.cli.run_sp1_dynamics_v3 --config {config_path.as_posix()} --stage full --selected-parameters {selected_path.as_posix()} --output-dir results/sp1_validation/SP1_DYNAMICS_BENCHMARK_v3 --resume
python -m viu_mrob_tfm.cli.run_sp1_dynamics_v3 --config {config_path.as_posix()} --stage audit --output-dir results/sp1_validation/SP1_DYNAMICS_BENCHMARK_v3
```

Los checkpoints son por tarea mundo–topología o mundo–evento. `--resume` reutiliza únicamente shards con `SUCCESS.json`.
"""


def _finalize_package(
    base: Path,
    config_path: Path,
    selected_path: Path,
    config: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    *,
    stage: str,
    started: float,
    preflight: Mapping[str, Any],
    git_info: Mapping[str, Any],
    calibration_runs: pd.DataFrame | None = None,
    calibration_summary: pd.DataFrame | None = None,
) -> dict[str, Any]:
    runs = frames["runs"]
    traces = frames["traces"]
    validation = frames["message_validation"]
    runs.to_csv(base / "all_runs.csv", index=False)
    traces.to_csv(base / "all_traces.csv", index=False)
    validation.to_csv(base / "message_accounting_validation.csv", index=False)
    aggregate = aggregate_results(runs, config)
    aggregate.to_csv(base / "aggregated_results.csv", index=False)
    censoring = _censoring_table(runs)
    censoring.to_csv(base / "censoring.csv", index=False)
    exclusions = _exclusions_table(runs)
    exclusions.to_csv(base / "exclusions.csv", index=False)
    paired = paired_comparisons(runs, config) if stage != "calibrate" else pd.DataFrame()
    paired.to_csv(base / "paired_comparisons.csv", index=False)
    regimes = regime_map(runs, aggregate, paired, config) if stage != "calibrate" else pd.DataFrame()
    regimes.to_csv(base / "regime_map.csv", index=False)
    method_complexity().to_csv(base / "method_complexity.csv", index=False)
    deterministic_case_catalog().to_csv(base / "e70_deterministic_cases.csv", index=False)
    if calibration_runs is not None:
        calibration_runs.to_csv(base / "calibration_runs.csv", index=False)
    elif not (base / "calibration_runs.csv").exists():
        pd.DataFrame().to_csv(base / "calibration_runs.csv", index=False)
    if calibration_summary is not None:
        calibration_summary.to_csv(base / "calibration_summary.csv", index=False)
    elif not (base / "calibration_summary.csv").exists():
        pd.DataFrame().to_csv(base / "calibration_summary.csv", index=False)
    if selected_path.exists():
        (base / "selected_parameters.yaml").write_text(selected_path.read_text(encoding="utf-8"), encoding="utf-8")
    snapshot = base / "config_snapshot.yaml"
    snapshot.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    preview_gates = None
    if stage == "preview":
        preview_gates = _preview_gates(runs, validation, bool(preflight["passed"]), expected_primary_count(config, "preview"))
        estimate = _runtime_storage_estimate(runs, base, config)
        (base / "runtime_storage_estimate.json").write_text(json.dumps(estimate, indent=2), encoding="utf-8")
    if stage == "full":
        make_figures(runs, aggregate, base / "figures")
    duration = time.perf_counter() - started
    statistics = {
        "stage": stage,
        "primary_runs": int(runs.is_primary.astype(bool).sum()),
        "all_rows": len(runs),
        "scenarios": int(runs[runs.is_primary.astype(bool)].scenario_id.nunique()),
        "censoring": censoring.censoring_reason.value_counts().to_dict() if len(censoring) else {},
        "preview_gates": preview_gates,
    }
    (base / "statistics.json").write_text(json.dumps(statistics, indent=2, ensure_ascii=False), encoding="utf-8")
    (base / "report.md").write_text(_report(config, runs, aggregate, censoring, regimes, preview_gates, duration), encoding="utf-8")
    (base / "README_REPRODUCE.md").write_text(_readme(config_path, selected_path, base), encoding="utf-8")
    hash_records, hashes_valid = _write_hashes(base)
    git_clean_end = _git("status", "--porcelain", allow_failure=True) == ""
    checks = audit_checks(
        runs,
        validation,
        config,
        stage=stage,
        tests_passed=bool(preflight["passed"]),
        git_clean_start=bool(git_info["clean_start"]),
        git_clean_end=git_clean_end,
        hashes_valid=hashes_valid,
    )
    audit = {
        "status": "passed" if all(checks.values()) and (preview_gates is None or all(preview_gates.values())) else "failed",
        **checks,
        "preview_gates": preview_gates,
        "artifact_hash_count": len(hash_records),
    }
    (base / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "experiment_id": config["preview_id"] if stage in {"calibrate", "preview"} else config["campaign_id"],
        "stage": stage,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "duration_s": duration,
        "run_compute_wall_time_sum_s": float(runs.wall_time_s.sum()),
        "artifact_generation_and_orchestration_s": duration,
        "primary_runs": int(runs.is_primary.astype(bool).sum()),
        "all_rows": len(runs),
        "git": {**git_info, "clean_end": git_clean_end},
        "environment": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
        "commands": {
            "stage": f"python -m viu_mrob_tfm.cli.run_sp1_dynamics_v3 --config {config_path} --stage {stage} --selected-parameters {selected_path} --output-dir {base} --resume",
            "tests": f"python -m pytest {' '.join(PREFLIGHT_TESTS)} -q",
        },
        "audit_status": audit["status"],
        "scope": "SP1 strategic allocation only; no A*, unicycle, obstacles, contact, transport or videos",
    }
    (base / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def execute(
    config_path: str | Path,
    *,
    stage: str,
    selected_parameters_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    if stage not in STAGES:
        raise ValueError(f"unknown stage: {stage}")
    started = time.perf_counter()
    config_path = Path(config_path).resolve()
    config = _load_config(config_path)
    default_key = "preview" if stage in {"calibrate", "preview"} else "full"
    base = Path(output_dir).resolve() if output_dir else Path(config["output_dirs"][default_key]).resolve()
    if stage != "audit" and base.exists() and not resume:
        raise FileExistsError(f"V3 output already exists; pass --resume: {base}")
    base.mkdir(parents=True, exist_ok=True)
    git_status = _git("status", "--porcelain", allow_failure=True)
    git_info = {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("branch", "--show-current"),
        "clean_start": git_status == "",
        "status_start": git_status,
    }
    preflight = _preflight(base)
    if not preflight["passed"]:
        raise RuntimeError("V3 preflight failed; inspect preflight_tests.json")
    if stage == "audit":
        runs = pd.read_csv(base / "all_runs.csv")
        traces = pd.read_csv(base / "all_traces.csv")
        validation = pd.read_csv(base / "message_accounting_validation.csv")
        selected_path = Path(selected_parameters_path).resolve() if selected_parameters_path else base / "selected_parameters.yaml"
        return _finalize_package(base, config_path, selected_path, config, {"runs": runs, "traces": traces, "message_validation": validation}, stage="full", started=started, preflight=preflight, git_info=git_info)

    if stage == "calibrate":
        initial = _candidate_mapping(config, 0)
        tasks = calibration_tasks(config)
        frames = execute_tasks(config, tasks, initial, config["budgets"]["calibration"], base / "checkpoints" / "calibration", resume=resume)
        summary, selected = _select_parameters(config, frames["runs"])
        selected_payload = {
            "campaign_id": config["campaign_id"],
            "calibration_seed_range": [70000, 70019],
            "selection_rule": "lexicographic: convergence desc, residual/scalars/wall asc",
            "selected_parameters": selected,
        }
        selected_path = base / "selected_parameters.yaml"
        selected_path.write_text(yaml.safe_dump(selected_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return _finalize_package(base, config_path, selected_path, config, frames, stage="calibrate", started=started, preflight=preflight, git_info=git_info, calibration_runs=frames["runs"], calibration_summary=summary)

    selected_path = Path(selected_parameters_path).resolve() if selected_parameters_path else base / "selected_parameters.yaml"
    selected = _read_selected(selected_path)
    if stage == "preview":
        frames = execute_tasks(config, preview_tasks(config), selected, config["budgets"]["preview"], base / "checkpoints" / "preview", resume=resume)
        calibration_runs = pd.read_csv(base / "calibration_runs.csv") if (base / "calibration_runs.csv").exists() else None
        calibration_summary = pd.read_csv(base / "calibration_summary.csv") if (base / "calibration_summary.csv").exists() else None
        return _finalize_package(base, config_path, selected_path, config, frames, stage="preview", started=started, preflight=preflight, git_info=git_info, calibration_runs=calibration_runs, calibration_summary=calibration_summary)

    standard, events = full_tasks(config)
    standard_frames = execute_tasks(config, standard, selected, config["budgets"]["evaluation"], base / "checkpoints" / "standard", resume=resume)
    event_frames = execute_tasks(config, events, selected, config["budgets"]["evaluation"], base / "checkpoints" / "events", resume=resume)
    frames = {
        key: pd.concat([standard_frames[key], event_frames[key]], ignore_index=True, sort=False)
        for key in ("runs", "traces", "message_validation")
    }
    preview_base = Path(config["output_dirs"]["preview"]).resolve()
    calibration_runs = pd.read_csv(preview_base / "calibration_runs.csv") if (preview_base / "calibration_runs.csv").exists() else None
    calibration_summary = pd.read_csv(preview_base / "calibration_summary.csv") if (preview_base / "calibration_summary.csv").exists() else None
    return _finalize_package(base, config_path, selected_path, config, frames, stage="full", started=started, preflight=preflight, git_info=git_info, calibration_runs=calibration_runs, calibration_summary=calibration_summary)


__all__ = [
    "STAGES",
    "aggregate_results",
    "audit_checks",
    "calibration_tasks",
    "execute",
    "expected_primary_count",
    "full_tasks",
    "method_complexity",
    "paired_comparisons",
    "preview_tasks",
    "regime_map",
]
