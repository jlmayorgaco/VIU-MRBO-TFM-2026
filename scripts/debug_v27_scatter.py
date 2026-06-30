"""Audit the v2.7 theory scatter construction.

The first postprocess scatter averaged the full physical life of each load. This
diagnostic separates three effects: travel transient, physical-contact
measurement, and the integer clearing cap.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_v27_daemon import build_methods, build_runs, load_params  # noqa: E402
from viu_mrob_tfm.simulations.warehouse import WarehouseConfig, _default_obstacles, _generate_loads  # noqa: E402

matplotlib.use("Agg")

METHODS = ["smith", "smith_no_prices", "smith_no_integer", "smith_effective_occupancy"]
WINDOWS = ["all", "contact_only", "post_first_contact_20s", "post_first_contact_40s"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=Path("results/benchmark-v27-full"))
    parser.add_argument("--params", type=Path, default=Path("configs/tuned_params_v26.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    methods = {method.key: method for method in build_methods(load_params(args.params))}
    runs = {(run.name, run.case): run for run in build_runs()}
    weights_cache: dict[tuple[str, str, str, int], dict[str, int]] = {}

    metrics: list[dict[str, Any]] = []
    all_points: dict[tuple[str, str, str, str, bool], list[tuple[float, float]]] = {}
    cases = sorted({(path.parent.name, parse_theory_filename(path)[0]) for path in args.run_dir.glob("*/*smith*_theory.csv") if parse_theory_filename(path)})
    for scenario, case in cases:
        for method in METHODS:
            files = sorted((args.run_dir / scenario).glob(f"{case}_{method}_*_theory.csv"))
            if not files:
                continue
            for window in WINDOWS:
                for cap in [False, True]:
                    points = collect_points(files, scenario, case, method, window, cap, methods, runs, weights_cache)
                    all_points[(scenario, case, method, window, cap)] = points
                    x = np.array([point[0] for point in points], dtype=float)
                    y = np.array([point[1] for point in points], dtype=float)
                    row = regression_metrics(x, y)
                    row.update(
                        {
                            "scenario": scenario,
                            "scenario_case": case,
                            "method": method,
                            "window": window,
                            "theory_capped_to_weight": cap,
                            "n_points": len(points),
                        }
                    )
                    metrics.append(row)

    write_csv(ROOT / "results" / "v2_7_scatter_debug_metrics.csv", metrics)
    examples = raw_examples(args.run_dir / "load_sweep" / "rho0.5_smith_2026_theory.csv")
    write_csv(ROOT / "results" / "v2_7_scatter_raw_examples.csv", examples)
    plot_case(
        all_points,
        scenario="load_sweep",
        case="rho0.5",
        method="smith",
        path=args.run_dir / "figures" / "fig_v27_scatter_debug_load_rho05.png",
    )
    print("Scatter debug complete.")
    print("  results/v2_7_scatter_debug_metrics.csv")
    print("  results/v2_7_scatter_raw_examples.csv")
    print("  results/benchmark-v27-full/figures/fig_v27_scatter_debug_load_rho05.png")
    return 0


def parse_theory_filename(path: Path) -> tuple[str, str, int] | None:
    stem = path.stem.removesuffix("_theory")
    try:
        seed = int(stem.split("_")[-1])
    except ValueError:
        return None
    for method in sorted(METHODS, key=len, reverse=True):
        suffix = f"_{method}_{seed}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], method, seed
    return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({column for row in rows for column in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def f(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def collect_points(
    files: list[Path],
    scenario: str,
    case: str,
    method: str,
    window: str,
    cap: bool,
    methods: dict[str, Any],
    runs: dict[tuple[str, str], Any],
    weights_cache: dict[tuple[str, str, str, int], dict[str, int]],
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for path in files:
        parsed = parse_theory_filename(path)
        if parsed is None:
            continue
        _case, _method, seed = parsed
        if _method != method:
            continue
        cache_key = (scenario, case, method, seed)
        if cache_key not in weights_cache:
            weights_cache[cache_key] = load_weights(scenario, case, method, seed, methods, runs)
        weights = weights_cache[cache_key]
        by_load: dict[str, list[tuple[float, float, float]]] = {}
        for row in read_csv(path):
            time = f(row["time"])
            observed = f(row["z_observed"])
            theory = f(row["z_theory"])
            if observed <= 0.0 and theory <= 0.0:
                continue
            by_load.setdefault(row["load"], []).append((time, observed, theory))
        for load, series in by_load.items():
            selected = select_window(series, window)
            if not selected:
                continue
            observed = float(np.mean([item[1] for item in selected]))
            theory = float(np.mean([item[2] for item in selected]))
            if cap:
                theory = min(theory, float(weights[load]))
            points.append((theory, observed))
    return points


def select_window(series: list[tuple[float, float, float]], window: str) -> list[tuple[float, float, float]]:
    if window == "all":
        return series
    if window == "contact_only":
        return [item for item in series if item[1] > 0.0]
    contacts = [item[0] for item in series if item[1] > 0.0]
    if not contacts:
        return []
    if window == "post_first_contact_20s":
        threshold = min(contacts) + 20.0
    elif window == "post_first_contact_40s":
        threshold = min(contacts) + 40.0
    else:
        raise ValueError(window)
    return [item for item in series if item[0] >= threshold]


def load_weights(
    scenario: str,
    case: str,
    method_key: str,
    seed: int,
    methods: dict[str, Any],
    runs: dict[tuple[str, str], Any],
) -> dict[str, int]:
    run = runs[(scenario, case)]
    method = methods[method_key]
    overrides = dict(run.overrides)
    overrides.update(method.params)
    if run.name == "nominal_flow_big" and method.key.startswith("smith"):
        overrides["spatial_scale"] = 12.0
    overrides["seed"] = seed
    overrides["scenario_name"] = run.name
    overrides["assignment_policy"] = method.policy
    cfg = WarehouseConfig(**overrides)
    rng = np.random.default_rng(cfg.seed)
    obstacles = list(cfg.obstacles) or _default_obstacles(cfg)
    loads = _generate_loads(cfg, rng, obstacles)
    return {load.identifier: int(load.weight) for load in loads}


def regression_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if x.size == 0:
        return {"r2": math.nan, "slope": math.nan, "bias": math.nan, "mae": math.nan, "rmse": math.nan}
    mae = float(np.mean(np.abs(y - x)))
    rmse = float(np.sqrt(np.mean((y - x) ** 2)))
    if x.size >= 2 and float(np.var(x)) > 1e-12 and float(np.var(y)) > 1e-12:
        slope, intercept = np.polyfit(x, y, 1)
        pred = slope * x + intercept
        r2 = 1.0 - float(np.sum((y - pred) ** 2)) / float(np.sum((y - np.mean(y)) ** 2))
    else:
        slope = math.nan
        r2 = math.nan
    return {"r2": float(r2), "slope": float(slope), "bias": float(np.mean(y - x)), "mae": mae, "rmse": rmse}


def raw_examples(path: Path) -> list[dict[str, Any]]:
    rows = read_csv(path)
    output: list[dict[str, Any]] = []
    first = [row for row in rows if row["load"] == "load-1"][:5]
    first_contact = [row for row in rows if row["load"] == "load-1" and f(row["z_observed"]) > 0.0][:10]
    for tag, group in [("first_rows", first), ("first_contact_rows", first_contact)]:
        for row in group:
            out = dict(row)
            out["source_file"] = str(path)
            out["sample"] = tag
            out["row_hash"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode("utf-8")).hexdigest()[:12]
            output.append(out)
    return output


def plot_case(
    all_points: dict[tuple[str, str, str, str, bool], list[tuple[float, float]]],
    scenario: str,
    case: str,
    method: str,
    path: Path,
) -> None:
    specs = [
        ("all", False, "Original: all rows, uncapped z*"),
        ("contact_only", False, "Contact rows only"),
        ("post_first_contact_20s", True, "Post-contact 20s, capped z*"),
        ("post_first_contact_40s", True, "Post-contact 40s, capped z*"),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(11, 10))
    for axis, (window, cap, title) in zip(axes.ravel(), specs):
        points = all_points.get((scenario, case, method, window, cap), [])
        x = np.array([point[0] for point in points], dtype=float)
        y = np.array([point[1] for point in points], dtype=float)
        metrics = regression_metrics(x, y)
        axis.scatter(x, y, s=12, alpha=0.35)
        lim = max(1.0, float(np.nanmax([np.nanmax(x) if x.size else 0, np.nanmax(y) if y.size else 0])))
        axis.plot([0, lim], [0, lim], "k--", linewidth=1)
        axis.set_title(f"{title}\nR2={metrics['r2']:.2f}, slope={metrics['slope']:.2f}, MAE={metrics['mae']:.2f}")
        axis.set_xlabel("z* theory")
        axis.set_ylabel("z observed")
        axis.grid(True, alpha=0.3)
    figure.suptitle(f"{scenario}/{case}/{method}: scatter construction audit")
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=200)
    plt.close(figure)


if __name__ == "__main__":
    raise SystemExit(main())
