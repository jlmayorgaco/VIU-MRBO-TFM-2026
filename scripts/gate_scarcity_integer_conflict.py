"""Mechanism gate for scarcity_extreme: fluid water-filling vs integer quorum.

This gate reads existing v2.7 theory CSVs for smith main raw only. It does not
rerun simulations. The diagnostic includes loads with no physical contact by
using a post-active window rather than a post-contact window.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any

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

SCENARIO = "scarcity_extreme"
CASE = "rho2.2_heavy"
METHOD = "smith"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=Path("results/benchmark-v27-full"))
    parser.add_argument("--params", type=Path, default=Path("configs/tuned_params_v26.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    methods = {method.key: method for method in build_methods(load_params(args.params))}
    runs = {(run.name, run.case): run for run in build_runs()}
    rows = collect_rows(args.run_dir, methods, runs)
    summary = summarize(rows)
    write_csv(ROOT / "results" / "v2_7_scarcity_integer_conflict.csv", rows)
    write_csv(ROOT / "results" / "v2_7_scarcity_integer_conflict_summary.csv", summary)
    update_findings(ROOT / "docs" / "hallazgos_v2_7.md", summary)
    for row in summary:
        print(row)
    return 0


def collect_rows(run_dir: Path, methods: dict[str, Any], runs: dict[tuple[str, str], Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((run_dir / SCENARIO).glob(f"{CASE}_{METHOD}_*_theory.csv")):
        parsed = parse_theory_filename(path)
        if parsed is None:
            continue
        case, method, seed = parsed
        if case != CASE or method != METHOD:
            continue
        loads = loads_for(seed, methods, runs)
        by_load: dict[str, list[dict[str, str]]] = {}
        for row in read_csv(path):
            if as_float(row["z_theory"]) <= 0.0 and as_float(row["z_observed"]) <= 0.0:
                continue
            by_load.setdefault(row["load"], []).append(row)
        for load_id, series in by_load.items():
            if not series:
                continue
            first_time = min(as_float(row["time"]) for row in series)
            selected = [row for row in series if as_float(row["time"]) >= first_time + 40.0]
            if not selected:
                continue
            load = loads[load_id]
            observed = np.array([as_float(row["z_observed"]) for row in selected], dtype=float)
            theory = np.array([as_float(row["z_theory"]) for row in selected], dtype=float)
            lam = np.array([as_float(row["lambda_star"]) for row in selected], dtype=float)
            weight = int(load.weight)
            z_fluid = float(np.nanmean(theory))
            z_obs = float(np.nanmean(observed))
            max_obs = float(np.nanmax(observed))
            quorum_fraction = float(np.nanmean(observed >= weight))
            rows.append(
                {
                    "seed": seed,
                    "load": load_id,
                    "weight": weight,
                    "reward": float(load.reward),
                    "spawn_time": float(load.spawn_time),
                    "z_fluid_uncapped": z_fluid,
                    "z_fluid_capped_to_weight": min(z_fluid, float(weight)),
                    "z_observed": z_obs,
                    "max_observed": max_obs,
                    "quorum_fraction": quorum_fraction,
                    "lambda_mean": float(np.nanmean(lam)),
                    "n_raw_rows": len(selected),
                    "low_contact": z_obs < 1.0,
                    "never_reached_quorum": max_obs < weight,
                    "quorum_majority": quorum_fraction >= 0.5,
                    "fluid_high": z_fluid >= 0.8 * weight,
                    "fluid_integer_conflict": z_fluid >= 0.8 * weight and max_obs < weight,
                    "fluid_partial_below_quorum": 0.0 < z_fluid < weight,
                    "fluid_partial_never_quorum": 0.0 < z_fluid < weight and max_obs < weight,
                    "mean_quorum_gap_fluid": weight - z_fluid,
                }
            )
    return rows


def parse_theory_filename(path: Path) -> tuple[str, str, int] | None:
    stem = path.stem.removesuffix("_theory")
    try:
        seed = int(stem.split("_")[-1])
    except ValueError:
        return None
    for method in ["smith_effective_occupancy", "smith_no_integer", "smith_no_prices", "smith"]:
        suffix = f"_{method}_{seed}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], method, seed
    return None


def loads_for(seed: int, methods: dict[str, Any], runs: dict[tuple[str, str], Any]) -> dict[str, Any]:
    run = runs[(SCENARIO, CASE)]
    method = methods[METHOD]
    overrides = dict(run.overrides)
    overrides.update(method.params)
    overrides["seed"] = seed
    overrides["scenario_name"] = run.name
    overrides["assignment_policy"] = method.policy
    cfg = WarehouseConfig(**overrides)
    rng = np.random.default_rng(seed)
    obstacles = list(cfg.obstacles) or _default_obstacles(cfg)
    loads = _generate_loads(cfg, rng, obstacles)
    return {load.identifier: load for load in loads}


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


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    x = np.array([as_float(row["z_fluid_uncapped"]) for row in rows], dtype=float)
    y = np.array([as_float(row["z_observed"]) for row in rows], dtype=float)
    metrics = regression_metrics(x, y)
    output.append({"metric": "regression_uncapped_fluid_vs_observed", **metrics, "count": len(rows)})
    for name, predicate in [
        ("low_contact", lambda row: bool(row["low_contact"])),
        ("never_reached_quorum", lambda row: bool(row["never_reached_quorum"])),
        ("quorum_majority", lambda row: bool(row["quorum_majority"])),
        ("fluid_high_never_quorum", lambda row: bool(row["fluid_integer_conflict"])),
        ("fluid_partial_never_quorum", lambda row: bool(row["fluid_partial_never_quorum"])),
    ]:
        group = [row for row in rows if predicate(row)]
        output.append(
            {
                "metric": name,
                "count": len(group),
                "share": len(group) / max(len(rows), 1),
                "mean_weight": mean(group, "weight"),
                "mean_z_fluid_uncapped": mean(group, "z_fluid_uncapped"),
                "mean_z_observed": mean(group, "z_observed"),
                "mean_max_observed": mean(group, "max_observed"),
                "mean_quorum_fraction": mean(group, "quorum_fraction"),
                "mean_quorum_gap_fluid": mean(group, "mean_quorum_gap_fluid"),
            }
        )
    return output


def regression_metrics(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if x.size < 2:
        return {"r2": math.nan, "slope": math.nan, "bias": math.nan, "mae": math.nan}
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    denom = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - float(np.sum((y - pred) ** 2)) / denom if denom > 1e-12 else math.nan
    return {
        "r2": float(r2),
        "slope": float(slope),
        "bias": float(np.mean(y - x)),
        "mae": float(np.mean(np.abs(y - x))),
    }


def mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [as_float(row[key]) for row in rows]
    values = [value for value in values if math.isfinite(value)]
    return float(np.mean(values)) if values else math.nan


def update_findings(path: Path, summary: list[dict[str, Any]]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Hallazgos v2.7\n"
    marker = "## Gate mecanistico de escasez extrema"
    if marker in existing:
        existing = existing.split(marker, maxsplit=1)[0].rstrip() + "\n\n"
    by_metric = {row["metric"]: row for row in summary}
    reg = by_metric["regression_uncapped_fluid_vs_observed"]
    low = by_metric["low_contact"]
    never = by_metric["never_reached_quorum"]
    conflict = by_metric["fluid_high_never_quorum"]
    partial_conflict = by_metric["fluid_partial_never_quorum"]
    lines = [
        marker,
        "",
        "Este gate usa `scarcity_extreme/rho2.2_heavy`, `smith` main raw, ventana post-activa de 40 s, z* fluido sin cap y z_obs fisico.",
        "",
        f"- Regresion z_obs ~ z*_fluido: R2={fmt(reg.get('r2'))}, slope={fmt(reg.get('slope'))}, MAE={fmt(reg.get('mae'))}, n={reg.get('count')}.",
        f"- Cargas con z_obs<1: {low.get('count')} ({fmt(low.get('share'))}); peso medio={fmt(low.get('mean_weight'))}, z*_medio={fmt(low.get('mean_z_fluid_uncapped'))}, z_obs_medio={fmt(low.get('mean_z_observed'))}.",
        f"- Cargas que nunca alcanzan quorum: {never.get('count')} ({fmt(never.get('share'))}); peso medio={fmt(never.get('mean_weight'))}, z*_medio={fmt(never.get('mean_z_fluid_uncapped'))}, z_obs_medio={fmt(never.get('mean_z_observed'))}.",
        f"- Conflictos directos z*_fluido alto pero sin quorum: {conflict.get('count')} ({fmt(conflict.get('share'))}).",
        f"- Conflictos de capacidad parcial fluida sin quorum: {partial_conflict.get('count')} ({fmt(partial_conflict.get('share'))}); gap medio peso-z*={fmt(partial_conflict.get('mean_quorum_gap_fluid'))}.",
        "",
        "Interpretacion: `scarcity_extreme` no refuta la teoria fluida; marca una transicion de regimen. El predictor marginal fluido recomienda capacidad parcial positiva para cargas pesadas, pero el clearing entero exige quorum completo. Cuando z* queda por debajo del peso, esa capacidad parcial no mueve la carga y el sistema observado puede anti-correlacionarse con z*.",
        "",
        "Artefactos: `results/v2_7_scarcity_integer_conflict.csv` y `results/v2_7_scarcity_integer_conflict_summary.csv`.",
        "",
    ]
    path.write_text(existing + "\n".join(lines), encoding="utf-8")


def fmt(value: Any) -> str:
    value = as_float(value)
    return "nan" if not math.isfinite(value) else f"{value:.3f}"


if __name__ == "__main__":
    raise SystemExit(main())
