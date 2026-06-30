"""Validate Smith-QR and communication-aware baselines.

Default settings are intentionally full-run oriented (20 seeds). Use
``--seeds 3`` for a quick smoke pass while developing.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import defaultdict
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


BASE_SMITH_PARAMS: dict[str, Any] = {
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
}

QR_PARAMS: dict[str, Any] = {
    "descriptor_belief_tau": 24.0,
    "commitment_ttl": 12.0,
    "local_quorum_grace": 4.0,
    "clearing_connectivity_guard": 2.2,
    "qr_patrol_gain": 1.6,
}

METHODS: dict[str, tuple[str, dict[str, Any]]] = {
    "smith": ("smith_full", BASE_SMITH_PARAMS),
    "smith_qr_belief": ("smith_qr_belief", BASE_SMITH_PARAMS | QR_PARAMS),
    "smith_qr_sticky": ("smith_qr_sticky", BASE_SMITH_PARAMS | QR_PARAMS),
    "smith_qr_clearing_guard": ("smith_qr_clearing_guard", BASE_SMITH_PARAMS | QR_PARAMS),
    "smith_qr_full": ("smith_qr_full", BASE_SMITH_PARAMS | QR_PARAMS),
    "greedy": ("classic_greedy_nearest", {}),
    "centralized_limited_comm": ("classic_centralized_limited_comm", {}),
    "marl_proxy": ("marl_proxy_policy", {}),
}

CASES = ("R12_p0", "R4_p0", "R3_p0", "R1.5_p0")
METRICS = (
    "reward_capture_ratio",
    "reward_capture_discovered",
    "throughput_steady",
    "loads_delivered",
    "mean_contact_deficit",
    "wasted_distance",
    "lateral_switches_per_delivery",
    "mean_communication_degree",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/smith_qr_validation"))
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--start-seed", type=int, default=2026)
    parser.add_argument("--cases", default=",".join(CASES), help="Comma-separated case list.")
    parser.add_argument("--methods", default=",".join(METHODS), help="Comma-separated method list.")
    parser.add_argument("--smoke", action="store_true", help="Use the 30 s benchmark smoke scenarios.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(args.start_seed, args.start_seed + args.seeds))
    cases = tuple(item.strip() for item in args.cases.split(",") if item.strip())
    methods = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    unknown_methods = sorted(set(methods).difference(METHODS))
    if unknown_methods:
        msg = f"Unknown methods: {', '.join(unknown_methods)}"
        raise SystemExit(msg)
    scenarios = {
        run.case: run
        for run in scenario_runs("comm_degradation", quick=True, smoke=args.smoke)
        if run.case in cases
    }
    missing_cases = sorted(set(cases).difference(scenarios))
    if missing_cases:
        msg = f"Unknown or unavailable cases: {', '.join(missing_cases)}"
        raise SystemExit(msg)

    rows: list[dict[str, Any]] = []
    for case in cases:
        for method_key in methods:
            policy, params = METHODS[method_key]
            for seed in seeds:
                row = run_one(scenarios[case], method_key, policy, params, seed)
                rows.append(row)
                print(f"{case} {method_key} seed={seed} capture={row['reward_capture_ratio']:.4g}")

    write_csv(args.out / "runs.csv", rows, result_columns())
    summary_rows = summarize(rows)
    write_csv(args.out / "summary.csv", summary_rows, summary_columns())
    delta_rows = paired_deltas(
        rows,
        "smith_qr_full",
        tuple(method for method in ("smith", "greedy", "centralized_limited_comm", "marl_proxy") if method in methods),
        cases,
    )
    write_csv(args.out / "paired_deltas.csv", delta_rows, delta_columns())
    write_readme(args.out / "README.md", seeds, summary_rows, delta_rows)
    return 0


def run_one(scenario: Any, method_key: str, policy: str, params: dict[str, Any], seed: int) -> dict[str, Any]:
    overrides = dict(scenario.overrides)
    overrides.update(params)
    overrides["seed"] = seed
    overrides["scenario_name"] = scenario.name
    overrides["assignment_policy"] = policy
    started = time.perf_counter()
    result = run_warehouse_simulation(WarehouseConfig(**overrides))
    runtime = time.perf_counter() - started
    row = {column: result.summary.get(column, np.nan) for column in SUMMARY_COLUMNS}
    row.update(
        {
            "scenario": scenario.name,
            "scenario_case": scenario.case,
            "method": method_key,
            "label": method_key,
            "family": "smith_qr_validation",
            "runtime_seconds": runtime,
            "runtime_per_decision_ms": 1000.0 * runtime / max(result.time.size, 1),
        }
    )
    return row


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_case"]), str(row["method"]))].append(row)
    output: list[dict[str, Any]] = []
    for (case, method), group in sorted(groups.items()):
        item: dict[str, Any] = {"scenario_case": case, "method": method, "n": len(group)}
        for metric in METRICS:
            mean, low, high = mean_ci([as_float(row.get(metric)) for row in group])
            item[f"{metric}_mean"] = mean
            item[f"{metric}_ci95_low"] = low
            item[f"{metric}_ci95_high"] = high
        output.append(item)
    return output


def paired_deltas(
    rows: list[dict[str, Any]],
    candidate: str,
    baselines: tuple[str, ...],
    cases: tuple[str, ...],
) -> list[dict[str, Any]]:
    by_key = {(row["scenario_case"], row["method"], int(float(row["seed"]))): row for row in rows}
    output: list[dict[str, Any]] = []
    for case in cases:
        seeds = sorted({int(float(row["seed"])) for row in rows if row["scenario_case"] == case})
        for baseline in baselines:
            item: dict[str, Any] = {"scenario_case": case, "candidate": candidate, "baseline": baseline, "n": 0}
            for metric in METRICS:
                values = []
                for seed in seeds:
                    cand = by_key.get((case, candidate, seed))
                    base = by_key.get((case, baseline, seed))
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
    r3 = next((row for row in deltas if row["scenario_case"] == "R3_p0" and row["baseline"] == "smith"), None)
    if r3 is None:
        delta = math.nan
        low = math.nan
        verdict = "NOT_EVALUATED"
    else:
        delta = as_float(r3["delta_reward_capture_ratio_mean"])
        low = as_float(r3["delta_reward_capture_ratio_ci95_low"])
        verdict = "PASS" if delta > 0.0 and low > 0.0 else "INCONCLUSIVE"
    lines = [
        "# Smith-QR validation",
        "",
        f"- Seeds: {seeds[0]}-{seeds[-1]} (`n={len(seeds)}`).",
        f"- Cases: {', '.join(sorted({str(row['scenario_case']) for row in summary}))}.",
        f"- R3_p0 Smith-QR full delta vs Smith capture: {delta:.4g} (CI95 low {low:.4g}).",
        f"- Pre-registered verdict: `{verdict}`.",
        "",
        "| Case | Method | n | Capture | Throughput | Wasted distance |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {case} | {method} | {n} | {cap:.4g} | {thr:.4g} | {waste:.4g} |".format(
                case=row["scenario_case"],
                method=row["method"],
                n=row["n"],
                cap=as_float(row["reward_capture_ratio_mean"]),
                thr=as_float(row["throughput_steady_mean"]),
                waste=as_float(row["wasted_distance_mean"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def result_columns() -> list[str]:
    return list(SUMMARY_COLUMNS)


def summary_columns() -> list[str]:
    cols = ["scenario_case", "method", "n"]
    for metric in METRICS:
        cols.extend([f"{metric}_mean", f"{metric}_ci95_low", f"{metric}_ci95_high"])
    return cols


def delta_columns() -> list[str]:
    cols = ["scenario_case", "candidate", "baseline", "n"]
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
