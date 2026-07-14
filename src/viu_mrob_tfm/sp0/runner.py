"""Executable SP0 pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from viu_mrob_tfm.experiment_stats import apply_holm_correction, mean_difference_inference, wilcoxon_signed_rank_pvalue
from viu_mrob_tfm.sp0.methods import (
    DYNAMIC_IDS,
    FITNESS_IDS,
    ROUNDING_IDS,
    assignment_objective,
    assignment_valid,
    close_integer,
    project_rows_to_simplex,
    run_sp0_method,
)
from viu_mrob_tfm.sp0.metrics import evaluate_sp0_result, theory_check_row
from viu_mrob_tfm.sp0.scenario import SP0World, make_sp0_world
from viu_mrob_tfm.sp0.visualization import (
    plot_dynamic_fitness_heatmap,
    plot_method_quality,
    plot_quality_communication_pareto,
    plot_quality_runtime_pareto,
    plot_scalability,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


SUMMARY_METRICS = [
    "success",
    "matching_valid",
    "coverage",
    "social_cost",
    "social_regret",
    "normalized_regret",
    "cost_gap",
    "makespan_proxy",
    "p95_individual_cost",
    "convergence_time",
    "timeout",
    "messages",
    "bytes",
    "runtime_wall_s",
    "memory_peak",
    "epsilon_ne_1",
    "epsilon_ne_2",
    "fractionality",
    "switches",
    "potential_violations",
    "occupancy_error",
    "observed_poa_ratio",
    "price_of_integrality",
]


def run_sp0_config(config_path: str | Path) -> dict[str, Any]:
    """Run an SP0 config file and return a manifest dictionary."""

    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "debug")).lower()
    if mode in {"protocol", "freeze", "pre_register", "preregister"}:
        return write_protocol_manifest(config, config_path=config_path)
    if mode in {"b0", "unit", "benchmark"}:
        return run_b0(config, config_path=config_path)
    if mode in {"debug", "smoke", "monte_carlo", "mc", "screening"}:
        return run_monte_carlo(config, config_path=config_path)
    raise ValueError(f"Unknown SP0 mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp0") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    seeds = _seed_range(config.get("seeds", {"start": 1000, "count": 2}))
    world_specs = _world_specs(config)
    method_specs = _method_specs(config.get("methods", []))
    rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    git_hash = _git_hash()
    timestamp_utc = datetime.now(UTC).isoformat()

    for world_spec in world_specs:
        for seed in seeds:
            world = make_sp0_world(
                n_robots=int(world_spec["N"]),
                n_loads=int(world_spec["K"]),
                seed=int(seed),
                geometry_id=str(world_spec["geometry_id"]),
                mean_degree_target=world_spec.get("mean_degree_target"),
                sp_id=str(config.get("sp_id", "SP0-v1.0")),
            )
            for method_spec in method_specs:
                spec = _resolve_method_spec(method_spec)
                result = run_sp0_method(world, spec)
                metrics = evaluate_sp0_result(world, result)
                row = {
                    "sp_id": world.sp_id,
                    "experiment_id": experiment_id,
                    "block": world_spec.get("block", ""),
                    "block_id": world_spec.get("block", ""),
                    "method_family": result.method_family,
                    "method_variant": result.method_id,
                    "method": result.method_id,
                    "architecture": result.architecture,
                    "dynamic_id": result.dynamic_id,
                    "fitness_id": result.fitness_id,
                    "rounding_id": result.rounding_id,
                    "world_seed": world.world_seed,
                    "method_seed": result.method_seed,
                    "train_seed": result.train_seed,
                    "N": world.n_robots,
                    "K": world.n_loads,
                    "load_ratio": world.load_ratio,
                    "geometry_id": world.geometry_id,
                    "R": world.radius,
                    "mean_degree": world.mean_degree,
                    "min_degree": world.min_degree,
                    "lambda2": world.lambda2,
                    "num_components": world.num_components,
                    "diameter": world.diameter,
                    "oracle_j": world.oracle_j,
                    "oracle_social_cost": world.oracle_social_cost,
                    "oracle_solve_time_s": float(result.oracle_solve_time_ms) / 1000.0,
                    "oracle_lookup_time_s": float(result.oracle_lookup_time_ms) / 1000.0,
                    "method_online_time_s": float(result.method_online_time_ms) / 1000.0,
                    "config_hash": _config_hash(config),
                    "world_hash": world.world_hash,
                    "git_hash": git_hash,
                    "timestamp_utc": timestamp_utc,
                    "training_steps": result.training_steps,
                    "training_converged": result.training_converged,
                    **metrics.to_dict(),
                }
                rows.append(row)
                theory_rows.append(theory_check_row(world, result, metrics))

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", _default_hypotheses()))
    theory_audit = summarize_theory_checks(theory_rows, rows, config)
    write_csv(tables_dir / "runs.csv", rows, columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, columns(ranking_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, columns(hypothesis_rows))
    parquet_files = write_optional_parquet(tables_dir, {"runs": rows, "summary": summary_rows, "theory_checks": theory_rows})
    save_json(output_dir / "theory_audit.json", theory_audit)
    if bool(config.get("make_figures", True)):
        plot_method_quality(rows, figures_dir / "sp0_method_quality.png")
        plot_dynamic_fitness_heatmap(rows, figures_dir / "sp0_dynamic_fitness_regret.png")
        plot_dynamic_fitness_heatmap(rows, figures_dir / "sp0_dynamic_fitness_success.png", metric="success")
        plot_quality_communication_pareto(rows, figures_dir / "sp0_quality_communication_pareto.png")
        plot_quality_runtime_pareto(rows, figures_dir / "sp0_quality_runtime_pareto.png")
        plot_scalability(rows, figures_dir / "sp0_runtime_scaling.png")
    report_path = output_dir / "report.md"
    write_report(report_path, experiment_id, rows, ranking_rows, hypothesis_rows, theory_audit, parquet_files)
    manifest = {
        "experiment_id": experiment_id,
        "mode": str(config.get("mode", "debug")),
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "runs": len(rows),
        "worlds": len(world_specs) * len(seeds),
        "methods": [str(_resolve_method_spec(spec).get("id")) for spec in method_specs],
        "report": str(report_path),
        "theory_audit": str(output_dir / "theory_audit.json"),
        "parquet_files": parquet_files,
        "expected_full_campaign_evaluations": int(config.get("expected_full_campaign_evaluations", 15436)),
        "implementation_decisions": config.get("implementation_decisions", {}),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def run_b0(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp0") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    count = int(config.get("b0_runs", config.get("runs", 300)))
    checks: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    dynamic_cycle = sorted(DYNAMIC_IDS)
    fitness_cycle = sorted(FITNESS_IDS - {"DIST"})
    rounding_cycle = ["REPAIR", "QR1", "QR2", "QRA"]

    for idx in range(count):
        n_robots = [4, 8, 12][idx % 3]
        ratio = [0.67, 1.0, 1.5][(idx // 3) % 3]
        n_loads = max(1, int(math.ceil(n_robots * ratio)))
        geometry = ["G-UNI", "G-CLU", "G-TIE", "G-X", "G-BIAS", "G-ZERO"][idx % 6]
        world = make_sp0_world(
            n_robots=n_robots,
            n_loads=n_loads,
            seed=7000 + idx,
            geometry_id=geometry,
            mean_degree_target="all" if idx % 4 else min(n_robots - 1, 4),
            sp_id=str(config.get("sp_id", "SP0-v1.0")),
        )
        method_spec = {
            "id": dynamic_cycle[idx % len(dynamic_cycle)],
            "dynamic_id": dynamic_cycle[idx % len(dynamic_cycle)],
            "fitness_id": fitness_cycle[idx % len(fitness_cycle)],
            "rounding_id": rounding_cycle[idx % len(rounding_cycle)],
            "h": 0.05,
            "max_steps": 50,
            "stable_window_steps": 4,
        }
        result = run_sp0_method(world, method_spec)
        metrics = evaluate_sp0_result(world, result)
        qr_start = close_integer(world, world.initial_x, rounding_id="REPAIR", params={})
        qr_labels = close_integer(world, world.initial_x, rounding_id="QR1", params={"delta_qr": 1.0e-4})
        potential_ok = assignment_objective(world, qr_labels) <= assignment_objective(world, qr_start) + 1.0e-8
        det_world = make_sp0_world(
            n_robots=n_robots,
            n_loads=n_loads,
            seed=7000 + idx,
            geometry_id=geometry,
            mean_degree_target="all" if idx % 4 else min(n_robots - 1, 4),
            sp_id=str(config.get("sp_id", "SP0-v1.0")),
        )
        checks.append(
            {
                "b0_index": idx,
                "world_hash": world.world_hash,
                "method": result.method_id,
                "simplex_ok": bool(result.continuous_x is None or np.allclose(np.sum(result.continuous_x, axis=1), 1.0, atol=1.0e-6)),
                "nonnegative_ok": bool(result.continuous_x is None or np.min(result.continuous_x) >= -1.0e-9),
                "oracle_valid": assignment_valid(world.oracle_labels, world.n_loads),
                "qr_valid": assignment_valid(qr_labels, world.n_loads),
                "qr_potential_ok": bool(potential_ok),
                "deterministic_world": bool(det_world.world_hash == world.world_hash),
                "finite_metrics": bool(np.isfinite(metrics.normalized_regret) and np.isfinite(metrics.runtime_wall_s)),
                "passed": bool(
                    (result.continuous_x is None or np.allclose(np.sum(result.continuous_x, axis=1), 1.0, atol=1.0e-6))
                    and (result.continuous_x is None or np.min(result.continuous_x) >= -1.0e-9)
                    and assignment_valid(world.oracle_labels, world.n_loads)
                    and assignment_valid(qr_labels, world.n_loads)
                    and potential_ok
                    and det_world.world_hash == world.world_hash
                    and np.isfinite(metrics.normalized_regret)
                    and np.isfinite(metrics.runtime_wall_s)
                ),
            }
        )
        rows.append(
            {
                "b0_index": idx,
                "world_hash": world.world_hash,
                "method": result.method_id,
                "N": n_robots,
                "K": n_loads,
                "geometry_id": geometry,
                **metrics.to_dict(),
            }
        )

    failed = [row for row in checks if not bool(row["passed"])]
    write_csv(tables_dir / "b0_checks.csv", checks, columns(checks))
    write_csv(tables_dir / "runs.csv", rows, columns(rows))
    audit = {
        "experiment_id": experiment_id,
        "b0_runs": count,
        "passed": len(failed) == 0,
        "failed_checks": len(failed),
        "failed_examples": failed[:20],
        "gate": "B0 passes only when simplex, nonnegativity, oracle, QR validity, QR potential, determinism and finite metrics hold.",
    }
    save_json(output_dir / "theory_audit.json", audit)
    write_b0_report(output_dir / "report.md", audit)
    manifest = {
        "experiment_id": experiment_id,
        "mode": "b0",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "runs": count,
        "passed": len(failed) == 0,
        "failed_checks": len(failed),
        "theory_audit": str(output_dir / "theory_audit.json"),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def write_protocol_manifest(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp0") / experiment_id))
    decisions = dict(config.get("implementation_decisions", {}))
    counts = dict(config.get("campaign_counts", {}))
    expected = int(config.get("expected_full_campaign_evaluations", sum(int(value) for value in counts.values() if isinstance(value, int))))
    payload = {
        "experiment_id": experiment_id,
        "mode": "protocol",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "sp_id": config.get("sp_id", "SP0-v1.0"),
        "status": config.get("status", "prepared_for_pre_registration"),
        "expected_full_campaign_evaluations": expected,
        "campaign_counts": counts,
        "implementation_decisions": decisions,
        "frozen": bool(config.get("frozen", False)),
        "config_hash": _config_hash(config),
    }
    save_json(output_dir / "protocol_manifest.json", payload)
    lines = [
        f"# {experiment_id}",
        "",
        f"- SP id: `{payload['sp_id']}`",
        f"- Status: `{payload['status']}`",
        f"- Frozen: `{payload['frozen']}`",
        f"- Expected evaluations: `{expected}`",
        f"- Exp4 population finalists: `{decisions.get('exp4_population_finalists', 'UNSET')}`",
        f"- Data-driven champion rule: `{decisions.get('data_driven_champion_rule', 'UNSET')}`",
        "",
        "This manifest freezes the computational protocol metadata only; it does not execute B2-B7.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("block", "ALL")), str(row["method"]))].append(row)
        groups[("ALL_BLOCKS", str(row["method"]))].append(row)
    output: list[dict[str, Any]] = []
    for (block, method), selected in sorted(groups.items()):
        item: dict[str, Any] = {"block": block, "method": method, "n": len(selected)}
        first = selected[0]
        for key in ["method_family", "architecture", "dynamic_id", "fitness_id", "rounding_id"]:
            item[key] = first.get(key)
        for metric in SUMMARY_METRICS:
            item[f"{metric}_mean"] = _mean(selected, metric)
            item[f"{metric}_std"] = _std(selected, metric)
        output.append(item)
    return output


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = summarize_rows(rows)
    ranked: list[dict[str, Any]] = []
    for block in sorted({str(row["block"]) for row in summaries}, key=lambda value: (value != "ALL_BLOCKS", value)):
        selected = sorted([row for row in summaries if str(row["block"]) == block], key=_ranking_key)
        for rank, row in enumerate(selected, start=1):
            ranked.append({"rank": rank, "ranking_rule": "max success/coverage, min regret/runtime/messages/timeout", **row})
    return ranked


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for spec in hypotheses or []:
        try:
            output.append(_evaluate_hypothesis(rows, spec))
        except Exception as exc:  # pragma: no cover
            output.append({"id": spec.get("id", "unknown"), "metric": spec.get("metric", ""), "error": str(exc), "p_value": 1.0, "alpha": 0.05})
    return apply_holm_correction(output)


def summarize_theory_checks(theory_rows: list[dict[str, Any]], rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    return {
        "checks": len(theory_rows),
        "failed_checks": len(failed),
        "passed": len(failed) == 0,
        "runs": len(rows),
        "model_scope": "SP0 homogeneous one-to-one numerical assignment; no robot dynamics, contact, friction, perception or hardware validation.",
        "expected_full_campaign_evaluations": int(config.get("expected_full_campaign_evaluations", 15436)),
        "failed_examples": failed[:20],
    }


def write_report(
    path: Path,
    experiment_id: str,
    rows: list[dict[str, Any]],
    ranking_rows: list[dict[str, Any]],
    hypothesis_rows: list[dict[str, Any]],
    theory_audit: dict[str, Any],
    parquet_files: list[str],
) -> None:
    best = next((row for row in ranking_rows if row["block"] == "ALL_BLOCKS" and int(row["rank"]) == 1), None)
    lines = [
        f"# {experiment_id}",
        "",
        "SP0 homogeneous one-to-one assignment executed with cached worlds, Hungarian oracle, distributed baselines, population dynamics and integer closures.",
        "",
        f"- Runs: `{len(rows)}`",
        f"- Theory failed checks: `{theory_audit['failed_checks']}`",
        f"- Best all-block method: `{best['method'] if best else 'n/a'}`",
        f"- Parquet files: `{len(parquet_files)}`",
        "",
        "## Hypotheses",
    ]
    for row in hypothesis_rows:
        p_value = float(row.get("p_value_raw", row.get("p_value", math.nan)))
        lines.append(f"- `{row.get('id')}`: p={p_value:.4g}, Holm reject={row.get('reject_holm', False)}.")
    lines.extend(["", "## Primary Ranking"])
    for row in ranking_rows[: min(14, len(ranking_rows))]:
        lines.append(
            f"- {row['block']} rank {row['rank']}: `{row['method']}` "
            f"success={float(row.get('success_mean', math.nan)):.3f}, "
            f"NR={float(row.get('normalized_regret_mean', math.nan)):.4f}, "
            f"runtime={float(row.get('runtime_wall_s_mean', math.nan)):.3f} s."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_b0_report(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        f"# {audit['experiment_id']}",
        "",
        "B0 unit and benchmark gate for SP0.",
        "",
        f"- Runs: `{audit['b0_runs']}`",
        f"- Passed: `{audit['passed']}`",
        f"- Failed checks: `{audit['failed_checks']}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_directory(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_csv_row(row, fieldnames))


def write_optional_parquet(tables_dir: Path, tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return []
    written: list[str] = []
    for name, rows in tables.items():
        if not rows:
            continue
        path = tables_dir / f"{name}.parquet"
        try:
            pd.DataFrame(rows).to_parquet(path, index=False)
        except Exception:
            continue
        written.append(str(path))
    return written


def columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "sp_id",
        "experiment_id",
        "block",
        "block_id",
        "method_family",
        "method_variant",
        "method",
        "architecture",
        "dynamic_id",
        "fitness_id",
        "rounding_id",
        "world_seed",
        "method_seed",
        "train_seed",
        "N",
        "K",
        "load_ratio",
        "geometry_id",
        "R",
        "mean_degree",
        "min_degree",
        "lambda2",
        "num_components",
        "diameter",
        "success",
        "matching_valid",
        "coverage",
        "social_cost",
        "social_regret",
        "normalized_regret",
        "cost_gap",
        "makespan_proxy",
        "convergence_time",
        "timeout",
        "messages",
        "bytes",
        "runtime_cpu_s",
        "runtime_wall_s",
        "oracle_solve_time_s",
        "oracle_lookup_time_s",
        "method_online_time_s",
        "closure_runtime_s",
        "memory_peak",
        "epsilon_ne_1",
        "epsilon_ne_2",
        "fractionality",
        "switches",
        "potential_violations",
        "occupancy_error",
        "training_steps",
        "training_converged",
        "config_hash",
        "world_hash",
        "git_hash",
        "timestamp_utc",
    ]
    seen = set(preferred)
    extra = sorted({key for row in rows for key in row if key not in seen})
    return [key for key in preferred if any(key in row for row in rows)] + extra


def _world_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    specs = config.get("worlds")
    if specs:
        output: list[dict[str, Any]] = []
        for item in specs:
            block = str(item.get("block", "debug"))
            geometries = item.get("geometries", item.get("geometry_id", item.get("geometry", "G-UNI")))
            if isinstance(geometries, str):
                geometries = [geometries]
            sizes = item.get("N", item.get("sizes", [8]))
            if isinstance(sizes, int):
                sizes = [sizes]
            ratios = item.get("load_ratios", item.get("ratio", [1.0]))
            if isinstance(ratios, (int, float)):
                ratios = [ratios]
            degrees = item.get("mean_degrees", item.get("mean_degree_target", ["all"]))
            if isinstance(degrees, (int, float, str)):
                degrees = [degrees]
            for geometry in geometries:
                for n_robots in sizes:
                    for ratio in ratios:
                        for degree in degrees:
                            output.append(
                                {
                                    "block": block,
                                    "geometry_id": str(geometry),
                                    "N": int(n_robots),
                                    "K": max(1, int(math.ceil(float(n_robots) * float(ratio)))),
                                    "mean_degree_target": degree,
                                }
                            )
        return output
    return [{"block": "debug", "geometry_id": "G-UNI", "N": 8, "K": 8, "mean_degree_target": "all"}]


def _method_specs(methods: list[Any]) -> list[dict[str, Any]]:
    if not methods:
        return [{"id": "HUN"}, {"id": "GRD"}, {"id": "DA"}, {"id": "SMI", "fitness_id": "LIN", "rounding_id": "QR1"}]
    output = []
    for item in methods:
        if isinstance(item, str):
            output.append({"id": item})
        else:
            output.append(dict(item))
    return output


def _resolve_method_spec(spec: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(spec)
    method_id = str(resolved.get("id", "")).upper()
    if method_id in DYNAMIC_IDS:
        resolved.setdefault("dynamic_id", method_id)
    return resolved


def _seed_range(spec: Any) -> list[int]:
    if isinstance(spec, list):
        return [int(value) for value in spec]
    if isinstance(spec, dict):
        start = int(spec.get("start", 0))
        count = int(spec.get("count", 1))
        return list(range(start, start + count))
    return [int(spec)]


def _evaluate_hypothesis(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    metric = str(spec.get("metric", "normalized_regret"))
    treatment = str(spec.get("treatment", spec.get("method_a", ""))).upper()
    control = str(spec.get("control", spec.get("method_b", ""))).upper()
    alternative = str(spec.get("alternative", "two-sided")).lower()
    lower_is_better = bool(spec.get("lower_is_better", metric not in {"success", "coverage"}))
    diffs = _paired_diffs(rows, treatment, control, metric)
    if alternative in {"less", "greater", "two-sided"}:
        wilcox_alt = alternative
    elif lower_is_better:
        wilcox_alt = "less"
    else:
        wilcox_alt = "greater"
    p_value = wilcoxon_signed_rank_pvalue(diffs, alternative=wilcox_alt)
    return {
        "id": spec.get("id", f"{treatment}_vs_{control}_{metric}"),
        "class": spec.get("class", "PairedSignedRank"),
        "metric": metric,
        "methods": f"{treatment} vs {control}",
        "n_pairs": int(diffs.size),
        "p_value": p_value,
        "alpha": float(spec.get("alpha", 0.05)),
        "alternative": wilcox_alt,
        **mean_difference_inference(diffs, effect_name=f"{treatment}-{control} {metric}"),
    }


def _paired_diffs(rows: list[dict[str, Any]], treatment: str, control: str, metric: str) -> np.ndarray:
    grouped: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in rows:
        method = str(row.get("method", "")).upper()
        if method not in {treatment, control}:
            continue
        key = (
            row.get("block"),
            row.get("world_hash"),
            row.get("N"),
            row.get("K"),
            row.get("geometry_id"),
            row.get("mean_degree"),
        )
        value = row.get(metric)
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        try:
            grouped[key][method] = float(value)
        except (TypeError, ValueError):
            pass
    diffs = [item[treatment] - item[control] for item in grouped.values() if treatment in item and control in item]
    return np.asarray(diffs, dtype=float)


def _default_hypotheses() -> list[dict[str, Any]]:
    return [
        {
            "id": "H0-SP0-debug-GRD-vs-HUN-regret",
            "metric": "normalized_regret",
            "treatment": "GRD",
            "control": "HUN",
            "alternative": "greater",
        },
        {
            "id": "H0-SP0-debug-DA-vs-GRD-regret",
            "metric": "normalized_regret",
            "treatment": "DA",
            "control": "GRD",
            "alternative": "less",
        },
    ]


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    values = [_to_float(row.get(key)) for row in rows]
    values = [value for value in values if np.isfinite(value)]
    return float(np.mean(values)) if values else math.nan


def _std(rows: list[dict[str, Any]], key: str) -> float:
    values = [_to_float(row.get(key)) for row in rows]
    values = [value for value in values if np.isfinite(value)]
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def _ranking_key(row: dict[str, Any]) -> tuple[float, float, float, float, float]:
    return (
        -_to_float(row.get("success_mean")),
        -_to_float(row.get("coverage_mean")),
        _to_float(row.get("normalized_regret_mean")),
        _to_float(row.get("runtime_wall_s_mean")),
        _to_float(row.get("messages_mean")),
    )


def _to_float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _csv_row(row: dict[str, Any], fieldnames: list[str]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key in fieldnames:
        value = row.get(key)
        if value is None:
            output[key] = ""
        elif isinstance(value, (dict, list, tuple)):
            output[key] = json.dumps(value, sort_keys=True)
        elif isinstance(value, float) and not np.isfinite(value):
            output[key] = ""
        else:
            output[key] = value
    return output


def _config_hash(config: dict[str, Any]) -> str:
    encoded = yaml.safe_dump(config, sort_keys=True, allow_unicode=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _git_hash() -> str:
    head = Path(".git/HEAD")
    try:
        text = head.read_text(encoding="utf-8").strip()
        if text.startswith("ref:"):
            ref = text.split(" ", 1)[1]
            ref_path = Path(".git") / ref
            return ref_path.read_text(encoding="utf-8").strip()[:12]
        return text[:12]
    except OSError:
        return "unknown"
