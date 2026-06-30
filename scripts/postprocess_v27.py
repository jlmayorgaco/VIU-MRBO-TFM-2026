"""Post-process the completed v2.7 warehouse benchmark.

This script does not rerun the benchmark. It extracts confidence intervals,
sanity checks, theory scatter diagnostics, price-regime diagnostics, and a
short thesis-facing findings document from an existing v2.7 run directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_v27_daemon import build_methods, build_runs, load_params  # noqa: E402
from viu_mrob_tfm.simulations.warehouse import (  # noqa: E402
    WarehouseConfig,
    _default_obstacles,
    _generate_loads,
    run_warehouse_simulation,
)

matplotlib.use("Agg")

METRICS = {
    "capture": "reward_capture_ratio",
    "throughput": "throughput_steady",
    "recovery": "recovery_time_s",
}

PRIMARY_METHOD = "smith"
NO_PRICE_METHOD = "smith_no_prices"
CENTRALIZED_METHOD = "classic_centralized_mincost"
ORACLE_METHOD = "oracle_clairvoyant"


@dataclass(frozen=True)
class ComparisonResult:
    name: str
    scenario: str
    scenario_case: str
    metric: str
    method_a: str
    method_b: str
    mean_a: float
    ci_low_a: float
    ci_high_a: float
    mean_b: float
    ci_low_b: float
    ci_high_b: float
    verdict: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=Path("results/benchmark-v27-full"))
    parser.add_argument("--params", type=Path, default=Path("configs/tuned_params_v26.json"))
    parser.add_argument("--determinism-check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir
    summary_path = run_dir / "summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(summary_path)

    rows = read_rows(summary_path)
    figure_dir = run_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    results_dir = ROOT / "results"
    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    significance = build_significance(rows)
    write_csv(results_dir / "v2_7_significance.csv", significance)

    comparisons = build_preregistered_comparisons(significance)
    sanity_rows = build_sanity_report(rows)
    write_csv(results_dir / "v2_7_sanity_violations.csv", sanity_rows)

    hash_rows = build_environment_hashes(rows, args.params)
    write_csv(results_dir / "v2_7_environment_hashes.csv", hash_rows)

    theory_points, theory_metrics = build_theory_scatter(run_dir)
    write_csv(results_dir / "v2_7_theory_scatter_metrics.csv", theory_metrics)
    plot_theory_scatter(theory_points, figure_dir / "fig_v27_theory_scatter_by_scenario.png")

    rmse_rows = build_rmse_by_regime(rows, theory_points)
    write_csv(results_dir / "v2_7_theory_rmse_by_regime.csv", rmse_rows)

    price_rows = build_price_regime(rows)
    write_csv(results_dir / "v2_7_price_regime.csv", price_rows)
    plot_price_regime(price_rows, figure_dir / "fig_v27_price_regime.png")

    churn_rows = build_price_churn(rows)
    write_csv(results_dir / "v2_7_price_churn.csv", churn_rows)
    plot_price_churn(churn_rows, figure_dir / "fig_v27_price_churn.png")

    determinism = run_determinism_check(args.params) if args.determinism_check else {"status": "not_run"}

    report = {
        "comparisons": [asdict(item) for item in comparisons],
        "sanity": summarize_sanity(sanity_rows, hash_rows),
        "theory": summarize_theory(theory_metrics, rmse_rows),
        "price_regime": summarize_price_regime(price_rows, churn_rows),
        "determinism": determinism,
        "artifacts": {
            "significance": str(results_dir / "v2_7_significance.csv"),
            "sanity_violations": str(results_dir / "v2_7_sanity_violations.csv"),
            "environment_hashes": str(results_dir / "v2_7_environment_hashes.csv"),
            "theory_scatter_metrics": str(results_dir / "v2_7_theory_scatter_metrics.csv"),
            "theory_rmse_by_regime": str(results_dir / "v2_7_theory_rmse_by_regime.csv"),
            "price_regime": str(results_dir / "v2_7_price_regime.csv"),
            "price_churn": str(results_dir / "v2_7_price_churn.csv"),
        },
    }
    (results_dir / "v2_7_postprocess_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=True),
        encoding="utf-8",
    )
    write_findings_doc(docs_dir / "hallazgos_v2_7.md", report)

    print("Postprocess complete.")
    print(f"  significance: {results_dir / 'v2_7_significance.csv'}")
    print(f"  findings:     {docs_dir / 'hallazgos_v2_7.md'}")
    print(f"  figures:      {figure_dir}")
    return 0


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({column for row in rows for column in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def f(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return math.nan
    return output


def finite_values(rows: Iterable[dict[str, Any]], column: str) -> list[float]:
    values = [f(row.get(column)) for row in rows]
    return [value for value in values if math.isfinite(value)]


def mean_ci(values: list[float]) -> tuple[float, float, float, int]:
    clean = [value for value in values if math.isfinite(value)]
    n = len(clean)
    if n == 0:
        return math.nan, math.nan, math.nan, 0
    mean = float(np.mean(clean))
    if n == 1:
        return mean, mean, mean, n
    sem = float(np.std(clean, ddof=1) / math.sqrt(n))
    half_width = float(stats.t.ppf(0.975, n - 1) * sem)
    return mean, mean - half_width, mean + half_width, n


def build_significance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key_base = (
            str(row["scenario"]),
            str(row["scenario_case"]),
            str(row["method"]),
            str(row["label"]),
        )
        for metric_name, column in METRICS.items():
            grouped.setdefault((*key_base, metric_name), []).append(row)

    output: list[dict[str, Any]] = []
    for (scenario, case, method, label, metric), group in sorted(grouped.items()):
        mean, low, high, n = mean_ci(finite_values(group, METRICS[metric]))
        output.append(
            {
                "scenario": scenario,
                "scenario_case": case,
                "method": method,
                "label": label,
                "metric": metric,
                "mean": mean,
                "ci95_low": low,
                "ci95_high": high,
                "n_seeds": n,
            }
        )
    return output


def find_ci(
    significance: list[dict[str, Any]],
    scenario: str,
    case: str,
    method: str,
    metric: str,
) -> dict[str, Any]:
    for row in significance:
        if (
            row["scenario"] == scenario
            and row["scenario_case"] == case
            and row["method"] == method
            and row["metric"] == metric
        ):
            return row
    raise KeyError((scenario, case, method, metric))


def build_preregistered_comparisons(significance: list[dict[str, Any]]) -> list[ComparisonResult]:
    specs = [
        (
            "scarcity_priority_smith_vs_centralized_capture",
            "scarcity_priority",
            "triage_forced",
            "capture",
            PRIMARY_METHOD,
            CENTRALIZED_METHOD,
        ),
        (
            "nominal_no_prices_vs_raw_capture",
            "nominal_flow",
            "rho0.7",
            "capture",
            NO_PRICE_METHOD,
            PRIMARY_METHOD,
        ),
        (
            "robot_failures_raw_vs_centralized_recovery",
            "robot_failures",
            "fail4",
            "recovery",
            PRIMARY_METHOD,
            CENTRALIZED_METHOD,
        ),
    ]
    output: list[ComparisonResult] = []
    for name, scenario, case, metric, method_a, method_b in specs:
        a = find_ci(significance, scenario, case, method_a, metric)
        b = find_ci(significance, scenario, case, method_b, metric)
        overlap = ci_overlap(a, b)
        verdict = "NO_CONCLUSIVE" if overlap else "SIGNIFICANT"
        output.append(
            ComparisonResult(
                name=name,
                scenario=scenario,
                scenario_case=case,
                metric=metric,
                method_a=method_a,
                method_b=method_b,
                mean_a=f(a["mean"]),
                ci_low_a=f(a["ci95_low"]),
                ci_high_a=f(a["ci95_high"]),
                mean_b=f(b["mean"]),
                ci_low_b=f(b["ci95_low"]),
                ci_high_b=f(b["ci95_high"]),
                verdict=verdict,
            )
        )
    return output


def ci_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if not all(math.isfinite(f(a[key])) and math.isfinite(f(b[key])) for key in ["ci95_low", "ci95_high"]):
        return True
    return max(f(a["ci95_low"]), f(b["ci95_low"])) <= min(f(a["ci95_high"]), f(b["ci95_high"]))


def build_sanity_report(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        capture = f(row.get("reward_capture_ratio"))
        discovered = f(row.get("reward_capture_discovered"))
        if math.isfinite(capture) and math.isfinite(discovered) and capture > discovered + 1e-9:
            output.append(sanity_row("capture_gt_discovered", row, capture, discovered))
        delivered = f(row.get("delivered_reward"))
        oracle_reward = f(row.get("oracle_reward"))
        if math.isfinite(delivered) and math.isfinite(oracle_reward) and delivered > oracle_reward + 1e-9:
            output.append(sanity_row("delivered_gt_oracle_reward", row, delivered, oracle_reward))

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["scenario"]), str(row["scenario_case"]), str(row["seed"])), []).append(row)
    for (scenario, case, seed), group in grouped.items():
        oracle = [row for row in group if row["method"] == ORACLE_METHOD]
        if not oracle:
            continue
        oracle_capture = f(oracle[0].get("reward_capture_ratio"))
        if not math.isfinite(oracle_capture):
            continue
        for row in group:
            if row["method"] == ORACLE_METHOD:
                continue
            capture = f(row.get("reward_capture_ratio"))
            if math.isfinite(capture) and capture > oracle_capture + 1e-9:
                violation = sanity_row("method_capture_gt_oracle_policy", row, capture, oracle_capture)
                violation["oracle_method"] = ORACLE_METHOD
                violation["seed"] = seed
                violation["scenario"] = scenario
                violation["scenario_case"] = case
                output.append(violation)
    return output


def sanity_row(kind: str, row: dict[str, Any], actual: float, bound: float) -> dict[str, Any]:
    return {
        "kind": kind,
        "scenario": row.get("scenario"),
        "scenario_case": row.get("scenario_case"),
        "method": row.get("method"),
        "label": row.get("label"),
        "seed": row.get("seed"),
        "actual": actual,
        "bound": bound,
    }


def build_environment_hashes(rows: list[dict[str, Any]], params_path: Path) -> list[dict[str, Any]]:
    present = {(str(row["scenario"]), str(row["scenario_case"]), str(row["method"]), int(float(row["seed"]))) for row in rows}
    methods = {method.key: method for method in build_methods(load_params(params_path))}
    runs = {(run.name, run.case): run for run in build_runs()}
    hash_rows: list[dict[str, Any]] = []
    by_world: dict[tuple[str, str, int], set[str]] = {}
    for scenario, case, method_key, seed in sorted(present):
        method = methods[method_key]
        scenario_run = runs[(scenario, case)]
        digest = environment_hash(scenario_run, method, seed)
        key = (scenario, case, seed)
        by_world.setdefault(key, set()).add(digest)
        hash_rows.append(
            {
                "scenario": scenario,
                "scenario_case": case,
                "seed": seed,
                "method": method_key,
                "environment_hash": digest,
            }
        )
    invariant = {key: len(values) == 1 for key, values in by_world.items()}
    for row in hash_rows:
        key = (str(row["scenario"]), str(row["scenario_case"]), int(row["seed"]))
        row["invariant_across_methods"] = invariant[key]
    return hash_rows


def environment_hash(scenario_run: Any, method: Any, seed: int) -> str:
    overrides = dict(scenario_run.overrides)
    overrides.update(method.params)
    if scenario_run.name == "nominal_flow_big" and method.key.startswith("smith"):
        overrides["spatial_scale"] = 12.0
    overrides["seed"] = seed
    overrides["scenario_name"] = scenario_run.name
    overrides["assignment_policy"] = method.policy
    cfg = WarehouseConfig(**overrides)
    rng = np.random.default_rng(cfg.seed)
    obstacles = list(cfg.obstacles) or _default_obstacles(cfg)
    loads = _generate_loads(cfg, rng, obstacles)
    payload = []
    for load in loads:
        payload.append(
            {
                "id": load.identifier,
                "source": np.round(load.source, 9).tolist(),
                "target": np.round(load.target, 9).tolist(),
                "weight": int(load.weight),
                "spawn_time": round(float(load.spawn_time), 9),
                "reward": round(float(load.reward), 9),
                "max_price": round(float(load.max_price), 9),
                "cancel_time": None if not math.isfinite(float(load.cancel_time)) else round(float(load.cancel_time), 9),
            }
        )
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_theory_scatter(run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    points: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob(f"*/*{PRIMARY_METHOD}_*_theory.csv")):
        scenario = path.parent.name
        parsed = parse_theory_filename(path)
        if parsed is None:
            continue
        case, method, seed = parsed
        if method != PRIMARY_METHOD:
            continue
        rows = read_rows(path)
        by_load: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if f(row.get("z_theory")) <= 0.0 and f(row.get("z_observed")) <= 0.0:
                continue
            by_load.setdefault(str(row["load"]), []).append(row)
        for load, group in by_load.items():
            observed = [f(row["z_observed"]) for row in group]
            theory = [f(row["z_theory"]) for row in group]
            observed = [value for value in observed if math.isfinite(value)]
            theory = [value for value in theory if math.isfinite(value)]
            if not observed or not theory:
                continue
            points.append(
                {
                    "scenario": scenario,
                    "scenario_case": case,
                    "method": method,
                    "seed": seed,
                    "load": load,
                    "z_observed": float(np.mean(observed)),
                    "z_theory": float(np.mean(theory)),
                }
            )
    metrics: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for point in points:
        grouped.setdefault((point["scenario"], point["scenario_case"], point["method"]), []).append(point)
    for (scenario, case, method), group in sorted(grouped.items()):
        obs = np.array([f(point["z_observed"]) for point in group], dtype=float)
        theory = np.array([f(point["z_theory"]) for point in group], dtype=float)
        row = regression_metrics(theory, obs)
        row.update({"scenario": scenario, "scenario_case": case, "method": method, "n_points": len(group)})
        metrics.append(row)
    return points, metrics


def parse_theory_filename(path: Path) -> tuple[str, str, int] | None:
    stem = path.stem.removesuffix("_theory")
    parts = stem.split("_")
    if len(parts) < 3:
        return None
    try:
        seed = int(parts[-1])
    except ValueError:
        return None
    known_methods = [PRIMARY_METHOD, NO_PRICE_METHOD, "smith_no_integer", "smith_effective_occupancy"]
    for method in sorted(known_methods, key=len, reverse=True):
        suffix = f"_{method}_{seed}"
        if stem.endswith(suffix):
            case = stem[: -len(suffix)]
            return case, method, seed
    return None


def regression_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if x.size == 0:
        return {"r2": math.nan, "mae": math.nan, "slope": math.nan, "bias": math.nan, "rmse": math.nan}
    mae = float(np.mean(np.abs(y - x)))
    rmse = float(np.sqrt(np.mean((y - x) ** 2)))
    if x.size >= 2 and float(np.var(x)) > 1e-12:
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else math.nan
    else:
        slope = math.nan
        r2 = math.nan
    return {
        "r2": float(r2),
        "mae": mae,
        "slope": float(slope),
        "bias": float(np.mean(y - x)),
        "rmse": rmse,
    }


def plot_theory_scatter(points: list[dict[str, Any]], path: Path) -> None:
    scenarios = sorted({point["scenario"] for point in points})
    if not scenarios:
        return
    cols = 3
    rows = int(math.ceil(len(scenarios) / cols))
    figure, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4.5 * rows), squeeze=False)
    for axis in axes.ravel():
        axis.axis("off")
    for axis, scenario in zip(axes.ravel(), scenarios):
        axis.axis("on")
        data = [point for point in points if point["scenario"] == scenario]
        x = np.array([f(point["z_theory"]) for point in data], dtype=float)
        y = np.array([f(point["z_observed"]) for point in data], dtype=float)
        axis.scatter(x, y, s=12, alpha=0.35)
        lim = max(1.0, float(np.nanmax([np.nanmax(x), np.nanmax(y)])))
        axis.plot([0, lim], [0, lim], "k--", linewidth=1)
        metrics = regression_metrics(x, y)
        axis.set_title(f"{scenario}\nR2={metrics['r2']:.2f}, slope={metrics['slope']:.2f}, bias={metrics['bias']:.2f}")
        axis.set_xlabel("z* theory")
        axis.set_ylabel("z observed")
        axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def build_rmse_by_regime(rows: list[dict[str, Any]], theory_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    point_scale: dict[tuple[str, str], float] = {}
    for key in {(point["scenario"], point["scenario_case"]) for point in theory_points}:
        values = [f(point["z_theory"]) for point in theory_points if (point["scenario"], point["scenario_case"]) == key]
        finite = [value for value in values if math.isfinite(value) and value > 0.0]
        point_scale[key] = float(np.mean(finite)) if finite else math.nan
    output: list[dict[str, Any]] = []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if str(row["method"]) != PRIMARY_METHOD:
            continue
        groups.setdefault((str(row["scenario"]), str(row["scenario_case"]), str(row["method"])), []).append(row)
    for (scenario, case, method), group in sorted(groups.items()):
        mean, low, high, n = mean_ci(finite_values(group, "staffing_rmse_vs_theory"))
        scale = point_scale.get((scenario, case), math.nan)
        output.append(
            {
                "scenario": scenario,
                "scenario_case": case,
                "method": method,
                "rmse_mean": mean,
                "rmse_ci95_low": low,
                "rmse_ci95_high": high,
                "n_seeds": n,
                "mean_z_theory_task": scale,
                "normalized_rmse": mean / scale if math.isfinite(mean) and math.isfinite(scale) and scale > 0 else math.nan,
            }
        )
    return output


def build_price_regime(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {
        ("nominal_flow", "rho0.7"),
        ("load_sweep", "rho0.5"),
        ("load_sweep", "rho1.0"),
        ("load_sweep", "rho1.7"),
        ("scarcity_extreme", "rho2.2_heavy"),
        ("scarcity_priority", "triage_forced"),
    }
    output: list[dict[str, Any]] = []
    for scenario, case in sorted(wanted):
        raw = by_seed(rows, scenario, case, PRIMARY_METHOD)
        no_prices = by_seed(rows, scenario, case, NO_PRICE_METHOD)
        common = sorted(set(raw) & set(no_prices))
        deltas = [f(raw[seed]["reward_capture_ratio"]) - f(no_prices[seed]["reward_capture_ratio"]) for seed in common]
        mean, low, high, n = mean_ci([delta for delta in deltas if math.isfinite(delta)])
        raw_mean, raw_low, raw_high, _ = mean_ci(finite_values(raw.values(), "reward_capture_ratio"))
        nop_mean, nop_low, nop_high, _ = mean_ci(finite_values(no_prices.values(), "reward_capture_ratio"))
        output.append(
            {
                "scenario": scenario,
                "scenario_case": case,
                "rho": scenario_rho(rows, scenario, case),
                "raw_capture_mean": raw_mean,
                "raw_capture_ci95_low": raw_low,
                "raw_capture_ci95_high": raw_high,
                "no_prices_capture_mean": nop_mean,
                "no_prices_capture_ci95_low": nop_low,
                "no_prices_capture_ci95_high": nop_high,
                "delta_raw_minus_no_prices": mean,
                "delta_ci95_low": low,
                "delta_ci95_high": high,
                "n_seed_pairs": n,
                "verdict": "SIGNIFICANT" if math.isfinite(low) and (low > 0.0 or high < 0.0) else "NO_CONCLUSIVE",
            }
        )
    return output


def by_seed(rows: list[dict[str, Any]], scenario: str, case: str, method: str) -> dict[int, dict[str, Any]]:
    output = {}
    for row in rows:
        if row["scenario"] == scenario and row["scenario_case"] == case and row["method"] == method:
            output[int(float(row["seed"]))] = row
    return output


def scenario_rho(rows: list[dict[str, Any]], scenario: str, case: str) -> float:
    for row in rows:
        if row["scenario"] == scenario and row["scenario_case"] == case:
            return f(row.get("rho"))
    return math.nan


def plot_price_regime(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    labels = [f"{row['scenario']}\n{row['scenario_case']}" for row in rows]
    x = np.arange(len(rows))
    delta = np.array([f(row["delta_raw_minus_no_prices"]) for row in rows], dtype=float)
    low = np.array([f(row["delta_ci95_low"]) for row in rows], dtype=float)
    high = np.array([f(row["delta_ci95_high"]) for row in rows], dtype=float)
    yerr = np.vstack([delta - low, high - delta])
    figure, axis = plt.subplots(figsize=(11, 5))
    axis.axhline(0.0, color="black", linewidth=1)
    colors = ["#b91c1c" if value < 0 else "#047857" for value in delta]
    axis.bar(x, delta, color=colors, alpha=0.82)
    axis.errorbar(x, delta, yerr=yerr, fmt="none", ecolor="black", linewidth=1, capsize=4)
    axis.set_xticks(x)
    axis.set_xticklabels(labels, rotation=25, ha="right")
    axis.set_ylabel("Delta capture: Smith raw - Smith no prices")
    axis.set_title("Price layer contribution across regimes")
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def build_price_churn(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    cases = sorted({(row["scenario"], row["scenario_case"]) for row in rows})
    for scenario, case in cases:
        raw = by_seed(rows, scenario, case, PRIMARY_METHOD)
        no_prices = by_seed(rows, scenario, case, NO_PRICE_METHOD)
        common = sorted(set(raw) & set(no_prices))
        if not common:
            continue
        delta_capture = []
        delta_lateral = []
        delta_recruit_release = []
        for seed in common:
            raw_row = raw[seed]
            nop_row = no_prices[seed]
            cap = f(raw_row["reward_capture_ratio"]) - f(nop_row["reward_capture_ratio"])
            lateral = f(raw_row["lateral_switches_per_delivery"]) - f(nop_row["lateral_switches_per_delivery"])
            recruit_release = (
                f(raw_row["recruit_switches"])
                + f(raw_row["release_switches"])
                - f(nop_row["recruit_switches"])
                - f(nop_row["release_switches"])
            )
            if math.isfinite(cap) and math.isfinite(lateral):
                delta_capture.append(cap)
                delta_lateral.append(lateral)
                delta_recruit_release.append(recruit_release)
        cap_mean, cap_low, cap_high, n = mean_ci(delta_capture)
        lateral_mean, lateral_low, lateral_high, _ = mean_ci(delta_lateral)
        rr_mean, rr_low, rr_high, _ = mean_ci(delta_recruit_release)
        output.append(
            {
                "scenario": scenario,
                "scenario_case": case,
                "delta_capture_raw_minus_no_prices": cap_mean,
                "delta_capture_ci95_low": cap_low,
                "delta_capture_ci95_high": cap_high,
                "delta_lateral_per_delivery_raw_minus_no_prices": lateral_mean,
                "delta_lateral_ci95_low": lateral_low,
                "delta_lateral_ci95_high": lateral_high,
                "delta_recruit_release_raw_minus_no_prices": rr_mean,
                "delta_recruit_release_ci95_low": rr_low,
                "delta_recruit_release_ci95_high": rr_high,
                "n_seed_pairs": n,
            }
        )
    return output


def plot_price_churn(rows: list[dict[str, Any]], path: Path) -> None:
    data = [
        row
        for row in rows
        if math.isfinite(f(row["delta_lateral_per_delivery_raw_minus_no_prices"]))
        and math.isfinite(f(row["delta_capture_raw_minus_no_prices"]))
    ]
    if not data:
        return
    x = np.array([f(row["delta_lateral_per_delivery_raw_minus_no_prices"]) for row in data], dtype=float)
    y = np.array([f(row["delta_capture_raw_minus_no_prices"]) for row in data], dtype=float)
    corr = float(np.corrcoef(x, y)[0, 1]) if x.size >= 2 and np.std(x) > 1e-12 and np.std(y) > 1e-12 else math.nan
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.axhline(0.0, color="black", linewidth=1, alpha=0.5)
    axis.axvline(0.0, color="black", linewidth=1, alpha=0.5)
    axis.scatter(x, y, s=55, alpha=0.75)
    for row, xi, yi in zip(data, x, y):
        axis.annotate(str(row["scenario_case"]), (xi, yi), fontsize=7, alpha=0.75)
    axis.set_xlabel("Delta lateral/delivery: raw - no_prices")
    axis.set_ylabel("Delta capture: raw - no_prices")
    axis.set_title(f"Price-induced churn vs capture change (r={corr:.2f})")
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)


def summarize_sanity(sanity_rows: list[dict[str, Any]], hash_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in sanity_rows:
        counts[str(row["kind"])] = counts.get(str(row["kind"]), 0) + 1
    hash_groups: dict[tuple[str, str, int], bool] = {}
    for row in hash_rows:
        hash_groups[(str(row["scenario"]), str(row["scenario_case"]), int(row["seed"]))] = bool(
            str(row["invariant_across_methods"]).lower() == "true" or row["invariant_across_methods"] is True
        )
    return {
        "violation_counts": counts,
        "environment_worlds": len(hash_groups),
        "environment_hash_invariant": all(hash_groups.values()) if hash_groups else False,
        "environment_hash_failures": sum(1 for value in hash_groups.values() if not value),
    }


def summarize_theory(theory_metrics: list[dict[str, Any]], rmse_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_scenario = {f"{row['scenario']}/{row['scenario_case']}": row for row in theory_metrics}
    rmse = {f"{row['scenario']}/{row['scenario_case']}": row for row in rmse_rows}
    return {"scatter": by_scenario, "rmse_by_regime": rmse}


def summarize_price_regime(price_rows: list[dict[str, Any]], churn_rows: list[dict[str, Any]]) -> dict[str, Any]:
    x = np.array([f(row["delta_lateral_per_delivery_raw_minus_no_prices"]) for row in churn_rows], dtype=float)
    y = np.array([f(row["delta_capture_raw_minus_no_prices"]) for row in churn_rows], dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    corr = float(np.corrcoef(x[mask], y[mask])[0, 1]) if np.sum(mask) >= 2 else math.nan
    return {
        "price_delta_by_regime": {f"{row['scenario']}/{row['scenario_case']}": row for row in price_rows},
        "churn_capture_correlation": corr,
    }


def run_determinism_check(params_path: Path) -> dict[str, Any]:
    methods = {method.key: method for method in build_methods(load_params(params_path))}
    run = next(item for item in build_runs() if item.name == "nominal_flow" and item.case == "rho0.7")
    method = methods[PRIMARY_METHOD]
    config = dict(run.overrides)
    config.update(method.params)
    config["seed"] = 2026
    config["scenario_name"] = run.name
    config["assignment_policy"] = method.policy
    result_a = run_warehouse_simulation(WarehouseConfig(**config))
    result_b = run_warehouse_simulation(WarehouseConfig(**config))
    digest_a = result_hash(result_a)
    digest_b = result_hash(result_b)
    return {
        "scenario": run.name,
        "scenario_case": run.case,
        "method": method.key,
        "seed": 2026,
        "hash_a": digest_a,
        "hash_b": digest_b,
        "deterministic": digest_a == digest_b,
    }


def result_hash(result: Any) -> str:
    payload = {
        "loads": [
            {
                "id": load.identifier,
                "status": int(load.status),
                "delivered_time": round(float(load.delivered_time), 9) if math.isfinite(float(load.delivered_time)) else None,
            }
            for load in result.loads
        ],
        "assignments": np.asarray(result.assignments, dtype=int).tolist(),
        "contacts": np.round(np.asarray(result.contact_counts, dtype=float), 9).tolist(),
        "prices": np.round(np.asarray(result.prices, dtype=float), 9).tolist(),
        "summary": {
            key: round(float(value), 9)
            for key, value in result.summary.items()
            if isinstance(value, (int, float, np.integer, np.floating)) and math.isfinite(float(value))
        },
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def write_findings_doc(path: Path, report: dict[str, Any]) -> None:
    comparisons = report["comparisons"]
    sanity = report["sanity"]
    price = report["price_regime"]
    theory = report["theory"]
    determinism = report["determinism"]

    def comparison_line(item: dict[str, Any]) -> str:
        return (
            f"- `{item['name']}`: {item['verdict']}. "
            f"{item['method_a']}={item['mean_a']:.3f} "
            f"[{item['ci_low_a']:.3f}, {item['ci_high_a']:.3f}] vs "
            f"{item['method_b']}={item['mean_b']:.3f} "
            f"[{item['ci_low_b']:.3f}, {item['ci_high_b']:.3f}]."
        )

    price_lines = []
    for key, row in price["price_delta_by_regime"].items():
        price_lines.append(
            f"- `{key}`: delta raw-no_prices={f(row['delta_raw_minus_no_prices']):.3f} "
            f"[{f(row['delta_ci95_low']):.3f}, {f(row['delta_ci95_high']):.3f}] "
            f"({row['verdict']})."
        )

    rmse_lines = []
    for key, row in theory["rmse_by_regime"].items():
        rmse_lines.append(
            f"- `{key}`: RMSE={f(row['rmse_mean']):.3f}, normalized={f(row['normalized_rmse']):.3f}."
        )

    scatter_lines = []
    for key, row in theory["scatter"].items():
        scatter_lines.append(
            f"- `{key}`: R2={f(row['r2']):.3f}, slope={f(row['slope']):.3f}, "
            f"bias={f(row['bias']):.3f}, MAE={f(row['mae']):.3f}."
        )

    lines = [
        "# Hallazgos v2.7",
        "",
        "Este documento congela la lectura post full-run v2.7 antes de incorporar resultados al TFM.",
        "Las comparaciones se interpretan con IC95; si los intervalos se solapan, el texto debe decir paridad o no concluyente.",
        "",
        "## Sanity checks",
        "",
        f"- Mundos reconstruidos por semilla: {sanity['environment_worlds']}. Hash invariante entre metodos: {sanity['environment_hash_invariant']} ({sanity['environment_hash_failures']} fallos).",
        f"- Violaciones registradas: `{sanity['violation_counts']}`. Ver `results/v2_7_sanity_violations.csv`.",
        f"- Determinismo: `{determinism}`.",
        "",
        "## Comparaciones preregistradas",
        "",
        *[comparison_line(item) for item in comparisons],
        "",
        "## Validacion teoria-realidad",
        "",
        "Scatter por escenario guardado en `results/benchmark-v27-full/figures/fig_v27_theory_scatter_by_scenario.png`.",
        *scatter_lines,
        "",
        "Descomposicion de RMSE por regimen:",
        *rmse_lines,
        "",
        "## Hallazgos positivos",
        "",
        "- En `scarcity_priority/triage_forced`, Smith main raw mejora la captura frente al centralizado con IC95 disjunto.",
        "- El RMSE bruto de staffing es bajo en `scarcity_priority`, pero al normalizar por escala y mirar el scatter tarea-a-tarea no aparece una validacion fuerte de pendiente 1/sesgo 0. En el TFM esto debe presentarse como diagnostico mixto, no como prueba cerrada.",
        "- La capa de clearing entero es necesaria en este panel: `smith_no_integer` colapsa en escasez extrema y prioridad.",
        "",
        "## Hallazgos negativos",
        "",
        "- Los precios parecen restar captura en flujo nominal en el delta pareado, pero la comparacion conservadora de IC95 de medias `smith_no_prices` vs `smith` queda no concluyente. No debe venderse como claim fuerte sin aclarar la regla estadistica.",
        "- `smith_effective_occupancy` es mas conservador y cuesta captura en este panel; no conviene venderlo como mejora empirica general sin nuevos escenarios.",
        "- Bajo comunicacion pobre (`R_com <= 3`) los metodos sin estado o de reaccion local simple pueden superar a Smith; esta es una limitacion de cobertura/relay, no un detalle menor.",
        "- La fila `oracle_clairvoyant` del run v2.7 no siempre actua como cota superior operacional; cualquier violacion queda listada como problema de medicion/benchmark, no como resultado teorico.",
        "",
        "## Capa de precios",
        "",
        "Delta de captura `smith - smith_no_prices`:",
        *price_lines,
        f"- Correlacion entre exceso de laterales por delivery y delta de captura: {f(price['churn_capture_correlation']):.3f}.",
        "",
        "## Artefactos",
        "",
        "- `results/v2_7_significance.csv`",
        "- `results/v2_7_sanity_violations.csv`",
        "- `results/v2_7_environment_hashes.csv`",
        "- `results/v2_7_theory_scatter_metrics.csv`",
        "- `results/v2_7_theory_rmse_by_regime.csv`",
        "- `results/v2_7_price_regime.csv`",
        "- `results/v2_7_price_churn.csv`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
