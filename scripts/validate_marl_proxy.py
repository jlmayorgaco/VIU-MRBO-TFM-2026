"""Validate the deterministic MARL proxy baseline.

This script keeps MARL as an empirical comparator, not as the thesis mechanism.
It avoids heavy RL dependencies and records the exact observation/reward contract
declared in ``configs/marl/marl_proxy.yaml``.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from benchmark_warehouse_methods import SUMMARY_COLUMNS, scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import WarehouseConfig, run_warehouse_simulation  # noqa: E402


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
    "marl_proxy": ("marl_proxy_policy", {}),
    "smith_qr_full": ("smith_qr_full", SMITH_QR_PARAMS),
    "smith": ("smith_full", SMITH_QR_PARAMS),
    "greedy": ("classic_greedy_nearest", {}),
    "centralized_limited_comm": ("classic_centralized_limited_comm", {}),
}

DEFAULT_CASES = (
    EvalCase("comm_degradation", "R12_p0"),
    EvalCase("comm_degradation", "R4_p0"),
    EvalCase("comm_degradation", "R3_p0"),
    EvalCase("scarcity_priority", "default"),
    EvalCase("robot_failures", "default"),
)

METRICS = (
    "reward_capture_ratio",
    "reward_capture_discovered",
    "loads_delivered",
    "throughput_steady",
    "mean_contact_deficit",
    "wasted_distance",
    "mean_communication_degree",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/marl_validation"))
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--start-seed", type=int, default=2026)
    parser.add_argument("--methods", default=",".join(METHODS), help="Comma-separated method list.")
    parser.add_argument("--cases", default="", help="Comma-separated scenario:case filters.")
    parser.add_argument("--smoke", action="store_true", help="Use 30 s benchmark smoke scenarios.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(args.start_seed, args.start_seed + args.seeds))
    selected_methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    unknown = sorted(set(selected_methods).difference(METHODS))
    if unknown:
        raise SystemExit(f"Unknown methods: {', '.join(unknown)}")
    selected_cases = _parse_cases(args.cases) if args.cases else DEFAULT_CASES
    scenario_lookup = _scenario_lookup(args.smoke)

    rows: list[dict[str, Any]] = []
    for eval_case in selected_cases:
        scenario = scenario_lookup.get((eval_case.scenario, eval_case.case))
        if scenario is None:
            raise SystemExit(f"Unavailable case: {eval_case.scenario}:{eval_case.case}")
        for method in selected_methods:
            policy, params = METHODS[method]
            for seed in seeds:
                row = _run_one(eval_case, scenario, method, policy, params, seed)
                rows.append(row)
                print(f"{eval_case.scenario}:{eval_case.case} {method} seed={seed} capture={row['reward_capture_ratio']:.4g}")

    write_csv(args.out / "runs.csv", rows, result_columns())
    summary = summarize(rows)
    write_csv(args.out / "summary.csv", summary, summary_columns())
    deltas = paired_deltas(rows, "marl_proxy", tuple(method for method in selected_methods if method != "marl_proxy"))
    write_csv(args.out / "paired_deltas.csv", deltas, delta_columns())
    write_readme(args.out / "README.md", seeds, summary, deltas)
    return 0


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


def _scenario_lookup(smoke: bool) -> dict[tuple[str, str], Any]:
    lookup: dict[tuple[str, str], Any] = {}
    for scenario_name in {case.scenario for case in DEFAULT_CASES}:
        for run in scenario_runs(scenario_name, quick=True, smoke=smoke):
            lookup[(scenario_name, run.case)] = run
    return lookup


def _run_one(
    eval_case: EvalCase,
    scenario: Any,
    method: str,
    policy: str,
    params: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    overrides = dict(scenario.overrides)
    overrides.update(params)
    overrides["seed"] = seed
    overrides["scenario_name"] = eval_case.scenario
    overrides["assignment_policy"] = policy
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
            "family": "marl_validation",
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
            item: dict[str, Any] = {
                "scenario": scenario,
                "scenario_case": case,
                "candidate": candidate,
                "baseline": baseline,
                "n": 0,
            }
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


def write_readme(path: Path, seeds: list[int], summary: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> None:
    lines = [
        "# MARL proxy validation",
        "",
        f"- Seeds: {seeds[0]}-{seeds[-1]} (`n={len(seeds)}`).",
        "- Baseline: deterministic parameter-sharing proxy, local observation, decentralized execution.",
        "- This is an empirical comparator, not a trained PPO/MAPPO contribution.",
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
    lines.extend(
        [
            "",
            "Full command:",
            "",
            "```powershell",
            "python scripts\\validate_marl_proxy.py --seeds 20 --out results\\marl_validation",
            "```",
        ]
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
