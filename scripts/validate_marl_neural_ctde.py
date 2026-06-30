"""Evaluate a frozen neural CTDE MARL actor against warehouse comparators."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from benchmark_warehouse_methods import SUMMARY_COLUMNS, scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import (  # noqa: E402
    POLICY_MARL_CTDE,
    POLICY_MARL_NEURAL_CTDE,
    WarehouseConfig,
    run_warehouse_simulation,
)


@dataclass(frozen=True)
class EvalCase:
    scenario: str
    case: str


SMITH_QR_PARAMS: dict[str, Any] = {
    "clearing_mode": "tick",
    "commit_dwell_time": 2.0,
    "epsilon_switch": 0.1,
    "lateral_switch_rule": "potential",
    "price_feedback_signal": "effective_committed",
    "price_gain": 0.1,
    "reserve_robot_slack": 0,
    "smith_integer_clearing_enabled": True,
    "smith_occupancy_mode": "raw",
    "smith_prices_enabled": True,
    "switch_margin": 0.1,
    "descriptor_belief_tau": 24.0,
    "commitment_ttl": 12.0,
    "local_quorum_grace": 4.0,
    "clearing_connectivity_guard": 2.2,
    "qr_patrol_gain": 1.6,
}

METHODS: dict[str, tuple[str, dict[str, Any]]] = {
    "marl_neural_ctde": (POLICY_MARL_NEURAL_CTDE, {}),
    "marl_ctde": (POLICY_MARL_CTDE, {}),
    "marl_proxy": ("marl_proxy_policy", {}),
    "smith_qr_full": ("smith_qr_full", SMITH_QR_PARAMS),
    "smith": ("smith_full", SMITH_QR_PARAMS),
    "greedy": ("classic_greedy_nearest", {}),
}

DEFAULT_CASES = (
    EvalCase("comm_degradation", "R3_p0"),
    EvalCase("scarcity_priority", "adversarial"),
    EvalCase("robot_failures", "fail4"),
)

METRICS = (
    "reward_capture_ratio",
    "reward_capture_discovered",
    "loads_delivered",
    "throughput_steady",
    "mean_contact_deficit",
    "wasted_distance",
    "lateral_switches_per_delivery",
    "mean_communication_degree",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("results/marl_neural_ctde_training/model.json"))
    parser.add_argument("--linear-model", type=Path, default=Path("results/marl_ctde_training_v1/model.json"))
    parser.add_argument("--out", type=Path, default=Path("results/marl_neural_ctde_validation"))
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--start-seed", type=int, default=3026)
    parser.add_argument("--cases", default=",".join(f"{case.scenario}:{case.case}" for case in DEFAULT_CASES))
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--max-loads", type=int, default=12)
    parser.add_argument("--smoke", action="store_true", help="Use shortest scenario templates before overrides.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    model = json.loads(args.model.read_text(encoding="utf-8"))
    linear_model = json.loads(args.linear_model.read_text(encoding="utf-8")) if args.linear_model.exists() else {}
    selected_methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    unknown = sorted(set(selected_methods).difference(METHODS))
    if unknown:
        raise SystemExit(f"Unknown methods: {', '.join(unknown)}")
    selected_cases = _parse_cases(args.cases)
    scenario_lookup = _scenario_lookup(selected_cases, smoke=args.smoke)
    seeds = list(range(args.start_seed, args.start_seed + args.seeds))

    rows: list[dict[str, Any]] = []
    for eval_case in selected_cases:
        scenario = scenario_lookup[(eval_case.scenario, eval_case.case)]
        for method in selected_methods:
            policy, params = METHODS[method]
            for seed in seeds:
                row = _run_one(eval_case, scenario, method, policy, params, seed, model, linear_model, args)
                rows.append(row)
                print(
                    f"{eval_case.scenario}:{eval_case.case} {method} seed={seed} "
                    f"capture={row['reward_capture_ratio']:.4g}"
                )

    write_csv(args.out / "runs.csv", rows, result_columns())
    summary = summarize(rows)
    write_csv(args.out / "summary.csv", summary, summary_columns())
    deltas = paired_deltas(
        rows,
        "marl_neural_ctde",
        tuple(method for method in selected_methods if method != "marl_neural_ctde"),
    )
    write_csv(args.out / "paired_deltas.csv", deltas, delta_columns())
    tests = statistical_tests(rows)
    write_csv(args.out / "statistical_tests.csv", tests, test_columns())
    write_readme(args.out / "README.md", model, seeds, summary, tests)
    return 0


def _run_one(
    eval_case: EvalCase,
    scenario: Any,
    method: str,
    policy: str,
    params: dict[str, Any],
    seed: int,
    model: dict[str, Any],
    linear_model: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    overrides = dict(scenario.overrides)
    overrides.update(params)
    overrides.update(
        {
            "seed": seed,
            "scenario_name": eval_case.scenario,
            "assignment_policy": policy,
            "duration": args.duration,
            "max_loads": args.max_loads,
            "max_active_loads": min(int(overrides.get("max_active_loads", 3)), args.max_loads),
        }
    )
    if method == "marl_neural_ctde":
        overrides["marl_neural_params"] = tuple(float(value) for value in model["params"])
        overrides["marl_neural_hidden_dim"] = int(model.get("hidden_dim", 8))
    if method == "marl_ctde" and linear_model:
        overrides["marl_ctde_weights"] = tuple(float(value) for value in linear_model["weights"])
        overrides["marl_ctde_idle_score"] = float(linear_model["idle_score"])
    started = time.perf_counter()
    result = run_warehouse_simulation(WarehouseConfig(**overrides))
    runtime = time.perf_counter() - started
    row = {column: result.summary.get(column, np.nan) for column in SUMMARY_COLUMNS}
    row.update(
        {
            "scenario": eval_case.scenario,
            "scenario_case": eval_case.case,
            "method": method,
            "label": method,
            "family": "marl_neural_ctde_validation",
            "runtime_seconds": runtime,
            "runtime_per_decision_ms": 1000.0 * runtime / max(result.time.size, 1),
        }
    )
    return row


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario"]), str(row["scenario_case"]), str(row["method"]))].append(row)
    output: list[dict[str, Any]] = []
    for (scenario, case, method), group in sorted(groups.items()):
        item: dict[str, Any] = {"scenario": scenario, "scenario_case": case, "method": method, "n": len(group)}
        for metric in METRICS:
            mean, low, high = mean_ci([as_float(row.get(metric)) for row in group])
            item[f"{metric}_mean"] = mean
            item[f"{metric}_ci95_low"] = low
            item[f"{metric}_ci95_high"] = high
        output.append(item)
    return output


def paired_deltas(rows: list[dict[str, Any]], candidate: str, baselines: tuple[str, ...]) -> list[dict[str, Any]]:
    by_key = {
        (row["scenario"], row["scenario_case"], row["method"], int(float(row["seed"]))): row
        for row in rows
    }
    scenario_cases = sorted({(row["scenario"], row["scenario_case"]) for row in rows})
    output: list[dict[str, Any]] = []
    for scenario, case in scenario_cases:
        seeds = sorted({int(float(row["seed"])) for row in rows if row["scenario"] == scenario and row["scenario_case"] == case})
        for baseline in baselines:
            item: dict[str, Any] = {"scenario": scenario, "scenario_case": case, "candidate": candidate, "baseline": baseline, "n": 0}
            for metric in METRICS:
                values = []
                for seed in seeds:
                    cand = by_key.get((scenario, case, candidate, seed))
                    base = by_key.get((scenario, case, baseline, seed))
                    if cand is None or base is None:
                        continue
                    values.append(as_float(cand.get(metric)) - as_float(base.get(metric)))
                item["n"] = max(int(item["n"]), len(values))
                mean, low, high = mean_ci(values)
                item[f"delta_{metric}_mean"] = mean
                item[f"delta_{metric}_ci95_low"] = low
                item[f"delta_{metric}_ci95_high"] = high
            output.append(item)
    return output


def statistical_tests(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for baseline in ("marl_ctde", "marl_proxy", "smith_qr_full", "smith", "greedy"):
        diffs = paired_metric_values(rows, "marl_neural_ctde", baseline, "reward_capture_ratio")
        if diffs.size < 2:
            continue
        ttest = stats.ttest_1samp(diffs, popmean=0.0, alternative="greater")
        mean, low, high = mean_ci(diffs.tolist())
        output.append(
            {
                "hypothesis": f"marl_neural_ctde_capture_gt_{baseline}",
                "h0": f"Neural MARL-CTDE no mejora captura frente a {baseline}",
                "h1": f"Neural MARL-CTDE mejora captura frente a {baseline}",
                "n": int(diffs.size),
                "alpha": 0.05,
                "metric": "reward_capture_ratio paired delta",
                "mean_delta": mean,
                "ci95_low": low,
                "ci95_high": high,
                "statistic": float(ttest.statistic),
                "p_value": float(ttest.pvalue),
                "decision": "reject_h0" if float(ttest.pvalue) < 0.05 and low > 0.0 else "do_not_reject_h0",
            }
        )
    return output


def paired_metric_values(rows: list[dict[str, Any]], candidate: str, baseline: str, metric: str) -> np.ndarray:
    by_key = {
        (row["scenario"], row["scenario_case"], row["method"], int(float(row["seed"]))): row
        for row in rows
    }
    keys = sorted({(row["scenario"], row["scenario_case"], int(float(row["seed"]))) for row in rows})
    values = []
    for scenario, case, seed in keys:
        cand = by_key.get((scenario, case, candidate, seed))
        base = by_key.get((scenario, case, baseline, seed))
        if cand is not None and base is not None:
            values.append(as_float(cand.get(metric)) - as_float(base.get(metric)))
    return np.asarray([value for value in values if math.isfinite(value)], dtype=float)


def _parse_cases(value: str) -> tuple[EvalCase, ...]:
    cases = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        scenario, sep, case = token.partition(":")
        if not sep:
            raise SystemExit(f"Case must be scenario:case, got {token!r}")
        cases.append(EvalCase(scenario, case))
    return tuple(cases)


def _scenario_lookup(cases: tuple[EvalCase, ...], smoke: bool) -> dict[tuple[str, str], Any]:
    lookup: dict[tuple[str, str], Any] = {}
    for scenario_name in sorted({case.scenario for case in cases}):
        for run in scenario_runs(scenario_name, quick=True, smoke=smoke):
            lookup[(scenario_name, run.case)] = run
    missing = [(case.scenario, case.case) for case in cases if (case.scenario, case.case) not in lookup]
    if missing:
        raise SystemExit(f"Unavailable cases: {missing}")
    return lookup


def write_readme(
    path: Path,
    model: dict[str, Any],
    seeds: list[int],
    summary: list[dict[str, Any]],
    tests: list[dict[str, Any]],
) -> None:
    lines = [
        "# Neural MARL CTDE validation",
        "",
        f"- Model version: {model.get('model_version', 'unknown')}.",
        f"- Seeds: {seeds[0]}-{seeds[-1]} (`n={len(seeds)}`).",
        "- Evaluation uses frozen actor parameters and seeds not used by training.",
        "",
        "| Scenario | Case | Method | n | Capture | Delivered | Wasted distance |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {scenario} | {case} | {method} | {n} | {cap:.4g} | {delivered:.4g} | {waste:.4g} |".format(
                scenario=row["scenario"],
                case=row["scenario_case"],
                method=row["method"],
                n=row["n"],
                cap=as_float(row["reward_capture_ratio_mean"]),
                delivered=as_float(row["loads_delivered_mean"]),
                waste=as_float(row["wasted_distance_mean"]),
            )
        )
    lines.extend(["", "## H0/H1 tests", ""])
    for row in tests:
        lines.append(
            "- {hypothesis}: mean delta={delta:.4g}, p={p:.4g}, decision={decision}".format(
                hypothesis=row["hypothesis"],
                delta=as_float(row["mean_delta"]),
                p=as_float(row["p_value"]),
                decision=row["decision"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def result_columns() -> list[str]:
    return list(SUMMARY_COLUMNS)


def summary_columns() -> list[str]:
    cols = ["scenario", "scenario_case", "method", "n"]
    for metric in METRICS:
        cols.extend([f"{metric}_mean", f"{metric}_ci95_low", f"{metric}_ci95_high"])
    return cols


def delta_columns() -> list[str]:
    cols = ["scenario", "scenario_case", "candidate", "baseline", "n"]
    for metric in METRICS:
        cols.extend([f"delta_{metric}_mean", f"delta_{metric}_ci95_low", f"delta_{metric}_ci95_high"])
    return cols


def test_columns() -> list[str]:
    return [
        "hypothesis",
        "h0",
        "h1",
        "n",
        "alpha",
        "metric",
        "mean_delta",
        "ci95_low",
        "ci95_high",
        "statistic",
        "p_value",
        "decision",
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def mean_ci(values: list[float]) -> tuple[float, float, float]:
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if finite.size == 0:
        return math.nan, math.nan, math.nan
    mean = float(np.mean(finite))
    if finite.size == 1:
        return mean, mean, mean
    half_width = 1.96 * float(np.std(finite, ddof=1)) / math.sqrt(float(finite.size))
    return mean, mean - half_width, mean + half_width


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


if __name__ == "__main__":
    raise SystemExit(main())
