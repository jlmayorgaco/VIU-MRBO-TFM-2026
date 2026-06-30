"""Validate a logit-mutated Smith dynamic under communication degradation.

The experiment is intentionally narrow: it tests whether adding a small logit
innovation term to Smith preferences prevents the R3 communication collapse
observed in v2.7, without changing the legacy `smith_full` default.
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
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_warehouse_methods import SUMMARY_COLUMNS, scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import POLICY_SMITH_FULL, WarehouseConfig, run_warehouse_simulation  # noqa: E402


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

GRID_CANDIDATES: dict[str, dict[str, Any]] = {
    "smith_logit_mu0.15_tau0.20": {"smith_logit_mutation_rate": 0.15, "smith_logit_temperature": 0.20},
    "smith_logit_mu0.30_tau0.20": {"smith_logit_mutation_rate": 0.30, "smith_logit_temperature": 0.20},
    "smith_logit_mu0.60_tau0.20": {"smith_logit_mutation_rate": 0.60, "smith_logit_temperature": 0.20},
    "smith_logit_mu1.00_tau0.20": {"smith_logit_mutation_rate": 1.00, "smith_logit_temperature": 0.20},
    "smith_logit_mu0.60_tau0.10": {"smith_logit_mutation_rate": 0.60, "smith_logit_temperature": 0.10},
    "smith_logit_mu1.00_tau0.10": {"smith_logit_mutation_rate": 1.00, "smith_logit_temperature": 0.10},
    "smith_logit_no_integer_mu0.30_tau0.20": {
        "smith_integer_clearing_enabled": False,
        "smith_logit_mutation_rate": 0.30,
        "smith_logit_temperature": 0.20,
    },
    "smith_logit_no_integer_mu0.60_tau0.20": {
        "smith_integer_clearing_enabled": False,
        "smith_logit_mutation_rate": 0.60,
        "smith_logit_temperature": 0.20,
    },
    "smith_logit_no_integer_mu1.00_tau0.20": {
        "smith_integer_clearing_enabled": False,
        "smith_logit_mutation_rate": 1.00,
        "smith_logit_temperature": 0.20,
    },
    "smith_logit_no_integer_mu0.60_tau0.10": {
        "smith_integer_clearing_enabled": False,
        "smith_logit_mutation_rate": 0.60,
        "smith_logit_temperature": 0.10,
    },
}

VALIDATION_CASES = ("R12_p0", "R4_p0", "R3_p0", "R1.5_p0")
BASELINE_METHODS = ("smith", "smith_no_integer", "classic_greedy_nearest")
METRICS = (
    "reward_capture_ratio",
    "reward_capture_discovered",
    "throughput_steady",
    "loads_delivered",
    "delivered_weight_ratio",
    "wasted_distance",
    "mean_contact_deficit",
    "lateral_switches_per_delivery",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/smith_logit_validation"))
    parser.add_argument("--baseline", type=Path, default=Path("results/benchmark-v27-full/summary.csv"))
    parser.add_argument("--grid-seeds", type=int, default=10)
    parser.add_argument("--validation-seeds", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    grid_seeds = list(range(2026, 2026 + int(args.grid_seeds)))
    validation_seeds = list(range(2026, 2026 + int(args.validation_seeds)))
    scenarios = {run.case: run for run in scenario_runs("comm_degradation", quick=True) if run.case in VALIDATION_CASES}
    r3 = scenarios["R3_p0"]

    baseline_rows = load_baselines(args.baseline, set(validation_seeds) | set(grid_seeds))
    write_csv(args.out / "baseline_rows.csv", baseline_rows, baseline_columns())

    grid_rows: list[dict[str, Any]] = []
    for method, params in GRID_CANDIDATES.items():
        for seed in grid_seeds:
            grid_rows.append(run_candidate(r3, method, params, seed))
            print(f"grid {method} seed={seed} capture={grid_rows[-1]['reward_capture_ratio']:.4g}")
    write_csv(args.out / "grid_runs.csv", grid_rows, result_columns())

    best_method = select_best_grid_candidate(grid_rows)
    best_params = GRID_CANDIDATES[best_method]

    validation_rows: list[dict[str, Any]] = []
    for case in VALIDATION_CASES:
        scenario = scenarios[case]
        for seed in validation_seeds:
            validation_rows.append(run_candidate(scenario, best_method, best_params, seed))
            print(f"validate {case} {best_method} seed={seed} capture={validation_rows[-1]['reward_capture_ratio']:.4g}")
    write_csv(args.out / "validation_runs.csv", validation_rows, result_columns())

    summary_rows = summarize_methods(dedupe_rows(baseline_rows + grid_rows + validation_rows))
    write_csv(args.out / "summary.csv", summary_rows, summary_columns())

    delta_rows = paired_deltas(validation_rows, baseline_rows, best_method)
    write_csv(args.out / "paired_deltas.csv", delta_rows, delta_columns())

    write_readme(args.out / "README.md", best_method, best_params, summary_rows, delta_rows, grid_seeds, validation_seeds)
    return 0


def run_candidate(scenario: Any, method_id: str, params: dict[str, Any], seed: int) -> dict[str, Any]:
    overrides = dict(scenario.overrides)
    overrides.update(BASE_SMITH_PARAMS)
    overrides.update(params)
    overrides["seed"] = int(seed)
    overrides["scenario_name"] = scenario.name
    overrides["assignment_policy"] = POLICY_SMITH_FULL
    config = WarehouseConfig(**overrides)
    started = time.perf_counter()
    result = run_warehouse_simulation(config)
    runtime = time.perf_counter() - started
    row = {column: result.summary.get(column, np.nan) for column in SUMMARY_COLUMNS}
    row.update(
        {
            "scenario": scenario.name,
            "scenario_case": scenario.case,
            "method": method_id,
            "label": method_id,
            "family": "experimental",
            "info_requirement": "local",
            "seed": int(seed),
            "runtime_seconds": runtime,
            "runtime_per_decision_ms": 1000.0 * runtime / max(result.time.size, 1),
            "smith_logit_mutation_rate": float(params["smith_logit_mutation_rate"]),
            "smith_logit_temperature": float(params["smith_logit_temperature"]),
            "smith_integer_clearing_enabled": bool(overrides["smith_integer_clearing_enabled"]),
        }
    )
    return row


def load_baselines(path: Path, seeds: set[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("scenario") != "comm_degradation":
                continue
            if row.get("scenario_case") not in VALIDATION_CASES:
                continue
            if row.get("method") not in BASELINE_METHODS:
                continue
            if int(float(row.get("seed", "nan"))) not in seeds:
                continue
            row["smith_logit_mutation_rate"] = 0.0
            row["smith_logit_temperature"] = 0.0
            row["smith_integer_clearing_enabled"] = row.get("method") != "smith_no_integer"
            rows.append(row)
    return rows


def select_best_grid_candidate(rows: list[dict[str, Any]]) -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["method"])].append(row)

    def score(item: tuple[str, list[dict[str, Any]]]) -> tuple[float, float, float]:
        _method, group = item
        return (
            mean_metric(group, "reward_capture_ratio"),
            mean_metric(group, "throughput_steady"),
            -mean_metric(group, "wasted_distance"),
        )

    return max(groups.items(), key=score)[0]


def summarize_methods(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_case"]), str(row["method"]))].append(row)
    out: list[dict[str, Any]] = []
    for (case, method), group in sorted(groups.items()):
        summary: dict[str, Any] = {"scenario_case": case, "method": method, "n": len(group)}
        for metric in METRICS:
            values = finite_values(group, metric)
            mean, low, high = mean_ci(values)
            summary[f"{metric}_mean"] = mean
            summary[f"{metric}_ci95_low"] = low
            summary[f"{metric}_ci95_high"] = high
        out.append(summary)
    return out


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["scenario_case"]), str(row["method"]), int(float(row["seed"])))
        deduped[key] = row
    return list(deduped.values())


def paired_deltas(candidate_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]], candidate_method: str) -> list[dict[str, Any]]:
    baseline_index = {
        (str(row["scenario_case"]), str(row["method"]), int(float(row["seed"]))): row for row in baseline_rows
    }
    candidate_index = {
        (str(row["scenario_case"]), int(row["seed"])): row for row in candidate_rows if row["method"] == candidate_method
    }
    rows: list[dict[str, Any]] = []
    for case in VALIDATION_CASES:
        for baseline_method in BASELINE_METHODS:
            deltas_by_metric: dict[str, list[float]] = {metric: [] for metric in METRICS}
            seeds: list[int] = []
            for (candidate_case, seed), candidate in candidate_index.items():
                if candidate_case != case:
                    continue
                baseline = baseline_index.get((case, baseline_method, seed))
                if baseline is None:
                    continue
                seeds.append(seed)
                for metric in METRICS:
                    deltas_by_metric[metric].append(as_float(candidate.get(metric)) - as_float(baseline.get(metric)))
            row: dict[str, Any] = {
                "scenario_case": case,
                "candidate_method": candidate_method,
                "baseline_method": baseline_method,
                "n": len(seeds),
                "seeds": " ".join(str(seed) for seed in sorted(seeds)),
            }
            for metric, values in deltas_by_metric.items():
                mean, low, high = mean_ci(values)
                row[f"delta_{metric}_mean"] = mean
                row[f"delta_{metric}_ci95_low"] = low
                row[f"delta_{metric}_ci95_high"] = high
            rows.append(row)
    return rows


def write_readme(
    path: Path,
    best_method: str,
    best_params: dict[str, Any],
    summary_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    grid_seeds: list[int],
    validation_seeds: list[int],
) -> None:
    r3_vs_smith = next(
        row
        for row in delta_rows
        if row["scenario_case"] == "R3_p0" and row["baseline_method"] == "smith"
    )
    r3_delta = as_float(r3_vs_smith["delta_reward_capture_ratio_mean"])
    r3_low = as_float(r3_vs_smith["delta_reward_capture_ratio_ci95_low"])
    r3_high = as_float(r3_vs_smith["delta_reward_capture_ratio_ci95_high"])
    verdict = "works" if r3_delta > 0.0 and r3_low > 0.0 else "not confirmed"
    lines = [
        "# Smith logit mutation validation",
        "",
        f"- Best R3 candidate: `{best_method}` with `{best_params}`.",
        f"- Grid seeds: {grid_seeds[0]}-{grid_seeds[-1]}. Validation seeds: {validation_seeds[0]}-{validation_seeds[-1]}.",
        "- Baselines are paired against `results/benchmark-v27-full/summary.csv`.",
        f"- R3_p0 paired delta vs Smith in reward capture: {r3_delta:.4g} "
        f"(CI95 {r3_low:.4g}, {r3_high:.4g}).",
        f"- Verdict: `{verdict}` for the isolated logit-mutation patch.",
        "",
        "## Mean reward capture",
        "",
        "| Case | Method | n | Capture mean | Throughput mean | Wasted distance mean |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {case} | {method} | {n} | {capture:.4g} | {throughput:.4g} | {wasted:.4g} |".format(
                case=row["scenario_case"],
                method=row["method"],
                n=row["n"],
                capture=as_float(row["reward_capture_ratio_mean"]),
                throughput=as_float(row["throughput_steady_mean"]),
                wasted=as_float(row["wasted_distance_mean"]),
            )
        )
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `grid_runs.csv`: candidate sweep on R3_p0.",
            "- `validation_runs.csv`: best candidate on R12_p0, R4_p0, R3_p0 and R1.5_p0.",
            "- `summary.csv`: mean and CI95 by case/method.",
            "- `paired_deltas.csv`: paired candidate-minus-baseline deltas.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def result_columns() -> list[str]:
    extra = ["smith_logit_mutation_rate", "smith_logit_temperature", "smith_integer_clearing_enabled"]
    return list(SUMMARY_COLUMNS) + extra


def baseline_columns() -> list[str]:
    return list(SUMMARY_COLUMNS) + [
        "smith_logit_mutation_rate",
        "smith_logit_temperature",
        "smith_integer_clearing_enabled",
    ]


def summary_columns() -> list[str]:
    cols = ["scenario_case", "method", "n"]
    for metric in METRICS:
        cols.extend([f"{metric}_mean", f"{metric}_ci95_low", f"{metric}_ci95_high"])
    return cols


def delta_columns() -> list[str]:
    cols = ["scenario_case", "candidate_method", "baseline_method", "n", "seeds"]
    for metric in METRICS:
        cols.extend([f"delta_{metric}_mean", f"delta_{metric}_ci95_low", f"delta_{metric}_ci95_high"])
    return cols


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def finite_values(rows: list[dict[str, Any]], metric: str) -> list[float]:
    values = [as_float(row.get(metric)) for row in rows]
    return [value for value in values if math.isfinite(value)]


def mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = finite_values(rows, metric)
    return float(np.mean(values)) if values else -math.inf


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
