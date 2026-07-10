"""Executable SP8 warehouse-scale scalability pipeline."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from viu_mrob_tfm.experiment_stats import apply_holm_correction, mean_difference_inference, wilcoxon_signed_rank_pvalue
from viu_mrob_tfm.sp8.methods import SP8_METHOD_LABELS, make_sp8_allocator
from viu_mrob_tfm.sp8.metrics import evaluate_sp8_assignment, method_resource_fields, method_taxonomy_fields
from viu_mrob_tfm.sp8.scenario import iter_sp8_problems
from viu_mrob_tfm.sp8.visualization import (
    plot_quality_complexity_pareto,
    plot_runtime_scaling,
    plot_solved_rate_by_scale,
    plot_throughput_by_scale,
    plot_timeout_boundary,
    plot_wrench_success,
    save_scale_transport_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


SUMMARY_METRICS = [
    "solved_rate",
    "timeout_rate",
    "assigned_robot_rate",
    "scalar_feasible_rate",
    "wrench_feasible_rate",
    "false_positive_rate",
    "transport_success_rate",
    "task_completion_rate",
    "throughput_tasks_per_min",
    "collision_risk_rate",
    "obstacle_intersection_rate",
    "mobile_conflict_rate",
    "route_crossing_rate",
    "mean_travel_distance_m",
    "total_travel_distance_m",
    "energy_proxy_wh",
    "communication_messages",
    "messages_per_robot",
    "runtime_ms",
    "estimated_memory_mb",
    "complexity_score",
    "score_value",
    "performance_gap_vs_reference",
]

RESOURCE_COLUMNS = [
    "method_training_type",
    "method_execution_model",
    "method_communication_pattern",
    "method_trainable_parameters",
    "method_tuned_parameters",
    "method_uses_neural_policy",
    "method_uses_decoder",
]


def run_sp8_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"debug", "smoke", "monte_carlo", "mc"}:
        return run_monte_carlo(config, config_path=config_path)
    raise ValueError(f"Unknown SP8 mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp8") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    seeds = _seed_range(config.get("seeds", {"start": 9800, "count": 2}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "debug")))) for item in config.get("scenarios", [{"param_generator": "debug"}])]
    method_specs = _method_specs(config.get("methods", []))
    make_videos = bool(config.get("make_videos", False))
    video_methods = {str(item) for item in config.get("video_methods", ["classic_local_greedy", "ours_wrench_market_hierarchical"])}
    load_status_sample_limit = int(config.get("load_status_sample_limit", -1))
    video_rows: list[dict[str, Any]] = []
    video_done: set[str] = set()

    rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    for generator, variant_id, seed, params, problem in iter_sp8_problems(generators, seeds):
        run_cache = []
        reference_score = None
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            allocator = make_sp8_allocator(method_id, dict(method_spec.get("params", {})))
            assignment = allocator.allocate(problem)
            metrics, load_status = evaluate_sp8_assignment(problem, assignment, reference_score=None)
            run_cache.append((method_id, assignment, metrics, load_status))
            if method_id in {"centralized_coalition_oracle", "ours_wrench_market_hierarchical"} and assignment.solved:
                reference_score = metrics.score_value if reference_score is None else max(reference_score, metrics.score_value)
        if reference_score is None:
            reference_score = max((item[2].score_value for item in run_cache), default=1.0)
        for method_id, assignment, _metrics, load_status in run_cache:
            metrics, load_status = evaluate_sp8_assignment(problem, assignment, reference_score=reference_score)
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP8_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "warehouse_archetype": params.warehouse_archetype,
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "loads_per_robot": float(params.n_loads / max(params.n_robots, 1)),
                "world_size_m": params.world_size_m,
                "obstacle_count": params.obstacle_count,
                "mobile_obstacle_count": params.mobile_obstacle_count,
                "communication_radius_m": params.communication_radius_m,
                **metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_theory_check(row, assignment))
            if make_videos and method_id in video_methods and method_id not in video_done and assignment.solved:
                video_name = f"sp8_{generator}_{variant_id}_{method_id}_seed{seed}.mp4"
                ok = save_scale_transport_video(problem, assignment, videos_dir / video_name, _video_title(row))
                video_done.add(method_id)
                video_rows.append({"video": video_name, "scenario_generator": generator, "scenario_variant_id": variant_id, "seed": seed, "method": method_id, "status": "ok" if ok else "failed_writer", "objective": "Mesoscopic large-scale load transport with wrench/torque, static/mobile obstacles and assigned AMR coalitions."})
            for load in load_status:
                if load_status_sample_limit >= 0 and len(load_rows) >= load_status_sample_limit:
                    break
                load_rows.append({"experiment_id": experiment_id, "scenario_generator": generator, "scenario_variant_id": variant_id, "seed": seed, "method": method_id, **load})

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", _default_hypotheses()))
    theory_audit = summarize_theory_checks(theory_rows, rows, seeds, generators, method_specs)
    write_csv(tables_dir / "runs.csv", rows, columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, columns(ranking_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, columns(load_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, columns(hypothesis_rows))
    if video_rows:
        write_csv(tables_dir / "video_index.csv", video_rows, columns(video_rows))
        write_video_index(output_dir, video_rows)
    save_json(output_dir / "theory_audit.json", theory_audit)
    if bool(config.get("make_figures", True)):
        plot_runtime_scaling(rows, figures_dir / "sp8_runtime_scaling_loglog.png")
        plot_solved_rate_by_scale(rows, figures_dir / "sp8_solved_rate_by_scale.png")
        plot_throughput_by_scale(rows, figures_dir / "sp8_throughput_by_scale.png")
        plot_wrench_success(rows, figures_dir / "sp8_wrench_success_by_scale.png")
        plot_quality_complexity_pareto(rows, figures_dir / "sp8_quality_complexity_pareto.png")
        plot_timeout_boundary(rows, figures_dir / "sp8_timeout_boundary.png")
    write_report(output_dir, experiment_id, rows, ranking_rows, hypothesis_rows, theory_audit)
    return {"experiment_id": experiment_id, "output_dir": str(output_dir), "runs": len(rows), "summary_rows": len(summary_rows), "failed_theory_checks": theory_audit["failed_checks"]}


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_generator"]), str(row["method"]))].append(row)
        groups[("ALL_SCENARIOS", str(row["method"]))].append(row)
    output = []
    for (scenario, method), selected in sorted(groups.items()):
        first = selected[0]
        item = {"scenario_generator": scenario, "method": method, "method_label": first.get("method_label", method), **method_taxonomy_fields(method), **method_resource_fields(method), "n": len(selected)}
        for metric in SUMMARY_METRICS:
            item[f"{metric}_mean"] = _mean(selected, metric)
            item[f"{metric}_std"] = _std(selected, metric)
        output.append(item)
    return output


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = summarize_rows(rows)
    ranked = []
    for scenario in sorted({row["scenario_generator"] for row in summaries}, key=lambda value: (value != "ALL_SCENARIOS", value)):
        selected = sorted([row for row in summaries if row["scenario_generator"] == scenario], key=_ranking_key)
        for rank, row in enumerate(selected, start=1):
            ranked.append({"rank": rank, "ranking_rule": "max solved/completion/wrench/throughput, min timeout/collision/runtime/memory/messages/gap", **row})
    return ranked


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for spec in hypotheses or []:
        try:
            output.append(_evaluate_hypothesis(rows, spec))
        except Exception as exc:  # pragma: no cover
            output.append({"id": spec.get("id", "unknown"), "metric": spec.get("metric", ""), "error": str(exc), "p_value": 1.0, "alpha": 0.05})
    return apply_holm_correction(output)


def _evaluate_hypothesis(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    cls = str(spec.get("class", "PairedSuperiorityHypothesis"))
    metric = str(spec["metric"])
    if cls == "PairedSuperiorityHypothesis":
        a, b = str(spec["method_a"]), str(spec["method_b"])
        diffs = _paired_diffs(rows, a, b, metric)
        lower = bool(spec.get("lower_is_better", False))
        p_value = wilcoxon_signed_rank_pvalue(diffs, alternative="less" if lower else "greater")
        return {"id": spec["id"], "class": cls, "metric": metric, "methods": f"{a} vs {b}", "n_pairs": int(diffs.size), "p_value": p_value, "alpha": float(spec.get("alpha", 0.05)), "null_hypothesis": spec.get("null_hypothesis", ""), "alternative": f"{a} {'<' if lower else '>'} {b}", **mean_difference_inference(diffs, effect_name=f"{a}-{b} {metric}")}
    if cls == "SpearmanScalingHypothesis":
        method = str(spec.get("method", ""))
        selected = [row for row in rows if not method or str(row["method"]) == method]
        x = np.asarray([float(row["n_robots"]) for row in selected], dtype=float)
        y = np.asarray([float(row[metric]) for row in selected], dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        if np.sum(mask) >= 3 and np.unique(x[mask]).size >= 2 and np.unique(y[mask]).size >= 2:
            rho, p_value = stats.spearmanr(x[mask], y[mask])
        else:
            rho, p_value = 0.0, 1.0
        return {"id": spec["id"], "class": cls, "metric": metric, "methods": method or "ALL", "n_pairs": int(np.sum(mask)), "statistic": float(rho), "p_value": float(p_value), "alpha": float(spec.get("alpha", 0.05)), "effect": float(rho), "effect_name": "spearman_rho", "ci95_low": math.nan, "ci95_high": math.nan, "effect_size": float(rho), "effect_size_name": "spearman_rho", "rank_biserial": math.nan}
    raise ValueError(cls)


def write_report(output_dir: Path, experiment_id: str, rows: list[dict[str, Any]], ranking_rows: list[dict[str, Any]], hypothesis_rows: list[dict[str, Any]], theory_audit: dict[str, Any]) -> None:
    best = next((row for row in ranking_rows if row["scenario_generator"] == "ALL_SCENARIOS" and int(row["rank"]) == 1), None)
    lines = [
        f"# {experiment_id}",
        "",
        "SP8 studies warehouse-scale intractability: many AMRs, many simultaneous payload loads, wrench/torque requirements, static/mobile obstacles and approximate transport risk.",
        "",
        f"- Runs: `{len(rows)}`",
        f"- Theory failed checks: `{theory_audit['failed_checks']}`",
        f"- Best all-scenario method: `{best['method'] if best else 'n/a'}`",
        "",
        "## Hypotheses",
    ]
    for row in hypothesis_rows:
        lines.append(f"- `{row.get('id')}`: p={float(row.get('p_value_raw', row.get('p_value', math.nan))):.4g}, Holm reject={row.get('reject_holm', False)}.")
    lines.extend(["", "## Primary Ranking"])
    for row in ranking_rows[: min(12, len(ranking_rows))]:
        lines.append(f"- {row['scenario_generator']} rank {row['rank']}: `{row['method']}` completion={float(row.get('task_completion_rate_mean', math.nan)):.3f}, timeout={float(row.get('timeout_rate_mean', math.nan)):.3f}, runtime={float(row.get('runtime_ms_mean', math.nan)):.2f} ms.")
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_video_index(output_dir: Path, video_rows: list[dict[str, Any]]) -> None:
    lines = ["# SP8 Video Index", "", "SP8 videos are qualitative mesoscopic inspections. They show representative load pickup-to-target motion, assigned AMR coalitions, wrench/torque demand arrows, static obstacles and mobile obstacle fields.", ""]
    for row in video_rows:
        lines.append(f"- `videos/{row['video']}`: `{row['method']}` on `{row['scenario_variant_id']}` seed `{row['seed']}`; status `{row['status']}`.")
    (output_dir / "video_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_theory_checks(theory_rows: list[dict[str, Any]], rows: list[dict[str, Any]], seeds: list[int], generators: list[str], method_specs: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row["passed"])]
    return {"checks": len(theory_rows), "failed_checks": len(failed), "passed": len(failed) == 0, "seed_count": len(seeds), "scenario_generators": generators, "method_count": len(method_specs), "model_scope": "mesoscopic_vectorized_warehouse_scale_wrench_transport_obstacle_model", "not_claimed": "SP8 is not full robot dynamics, exact MPC, RF simulation, or hardware validation.", "failed_examples": failed[:20]}


def _theory_check(row: dict[str, Any], assignment: Any) -> dict[str, Any]:
    rates = ["solved_rate", "timeout_rate", "assigned_robot_rate", "scalar_feasible_rate", "wrench_feasible_rate", "transport_success_rate", "collision_risk_rate", "performance_gap_vs_reference"]
    rates_ok = all(0.0 <= _float(row.get(key)) <= 1.000001 for key in rates if np.isfinite(_float(row.get(key))))
    labels_ok = bool(assignment.labels.ndim == 1 and assignment.labels.size == int(row["n_robots"]))
    passed = bool(rates_ok and labels_ok and (bool(row["solved"]) or bool(row["timeout"])))
    return {"experiment_id": row["experiment_id"], "scenario_generator": row["scenario_generator"], "scenario_variant_id": row["scenario_variant_id"], "seed": row["seed"], "method": row["method"], "passed": passed, "rates_ok": rates_ok, "labels_ok": labels_ok}


def _default_hypotheses() -> list[dict[str, Any]]:
    return [
        {"id": "H8.1_centralized_oracle_timeout_increases_with_scale", "class": "SpearmanScalingHypothesis", "method": "centralized_coalition_oracle", "metric": "timeout_rate"},
        {"id": "H8.2_ours_hierarchical_higher_completion_than_classic_local", "class": "PairedSuperiorityHypothesis", "method_a": "ours_wrench_market_hierarchical", "method_b": "classic_local_greedy", "metric": "task_completion_rate", "lower_is_better": False},
        {"id": "H8.3_ours_hierarchical_higher_wrench_feasibility_than_hungarian", "class": "PairedSuperiorityHypothesis", "method_a": "ours_wrench_market_hierarchical", "method_b": "centralized_hungarian_expanded", "metric": "wrench_feasible_rate", "lower_is_better": False},
    ]


def _video_title(row: dict[str, Any]) -> str:
    return f"SP8 {row['method_label']} | {row['scenario_variant_id']} | {row['n_robots']} AMR/{row['n_loads']} loads"


def _paired_diffs(rows: list[dict[str, Any]], method_a: str, method_b: str, metric: str) -> np.ndarray:
    by_key: dict[tuple[str, str, int], dict[str, float]] = defaultdict(dict)
    for row in rows:
        if row["method"] not in {method_a, method_b}:
            continue
        by_key[(str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))][str(row["method"])] = _float(row[metric])
    return np.asarray([values[method_a] - values[method_b] for values in by_key.values() if method_a in values and method_b in values], dtype=float)


def _method_specs(config: list[Any]) -> list[dict[str, Any]]:
    specs = [{"id": str(item), "params": {}} if isinstance(item, str) else {"id": str(item["id"]), "params": dict(item.get("params", {}))} for item in config]
    return specs or [{"id": method, "params": {}} for method in SP8_METHOD_LABELS]


def _seed_range(config: Any) -> list[int]:
    if isinstance(config, list):
        return [int(value) for value in config]
    return list(range(int(config.get("start", 0)), int(config.get("start", 0)) + int(config.get("count", 1))))


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (-_float(row.get("solved_rate_mean")), _float(row.get("timeout_rate_mean")), -_float(row.get("task_completion_rate_mean")), -_float(row.get("wrench_feasible_rate_mean")), _float(row.get("collision_risk_rate_mean")), _float(row.get("runtime_ms_mean")), _float(row.get("estimated_memory_mb_mean")), _float(row.get("messages_per_robot_mean")))


def columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_label", "rank"]
    keys = sorted({key for row in rows for key in row})
    return [key for key in preferred if key in keys] + [key for key in keys if key not in preferred]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_directory(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else math.nan


def _std(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.std(values, ddof=1)) if values.size > 1 else 0.0


def _float(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
