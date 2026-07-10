"""Executable SP4 post-allocation AMR motion Monte Carlo pipeline."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from viu_mrob_tfm.experiment_stats import (
    apply_holm_correction,
    mean_difference_inference,
    wilcoxon_signed_rank_pvalue as robust_wilcoxon_signed_rank_pvalue,
)
from viu_mrob_tfm.sp4.methods import (
    SP4_METHOD_LABELS,
    make_sp4_policy,
    simulate_motion,
    sp4_method_metadata,
)
from viu_mrob_tfm.sp4.metrics import (
    evaluate_motion,
    robot_status_rows,
    trajectory_sample_rows,
)
from viu_mrob_tfm.sp4.scenario import SP4Problem, iter_sp4_problems
from viu_mrob_tfm.sp4.visualization import (
    plot_arrival_success,
    plot_clearance_by_method,
    plot_collision_rate_by_scenario,
    plot_communication_degradation,
    plot_path_efficiency,
    plot_time_energy_pareto,
    save_motion_snapshot,
    save_motion_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


SUMMARY_METRICS = [
    "arrival_success_rate",
    "timeout_rate",
    "mean_arrival_time_s",
    "max_arrival_time_s",
    "travel_distance_m",
    "mean_path_length_m",
    "path_efficiency_ratio",
    "energy_proxy_wh",
    "collision_count",
    "collision_rate",
    "safety_violation_count",
    "min_robot_clearance_m",
    "min_obstacle_clearance_m",
    "mean_clearance_m",
    "mean_speed_mps",
    "max_speed_mps",
    "max_speed_violation_mps",
    "congestion_delay_s",
    "communication_messages",
    "runtime_ms",
    "score_value",
    "reference_score_value",
    "signed_score_delta_vs_reference",
    "performance_gap_vs_reference",
    "optimality_gap_vs_reference",
    "arrived_robots",
    "timed_out_robots",
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


def run_sp4_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"monte_carlo", "mc", "debug"}:
        return run_monte_carlo(config, config_path=config_path)
    raise ValueError(f"Unknown SP4 config mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp4") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    seeds = _seed_range(config.get("seeds", {"start": 5100, "count": 5}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    method_specs = _method_specs(config.get("methods", []))
    sample_limit = int(config.get("trajectory_sample_runs", 16))
    rows: list[dict[str, Any]] = []
    robot_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []

    for generator, variant_id, seed, params, problem in iter_sp4_problems(generators, seeds):
        reference_policy = make_sp4_policy("reference_time_expanded_cbf")
        reference_result = simulate_motion(reference_policy, problem)
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            policy = make_sp4_policy(method_id, dict(method_spec.get("params", {})))
            result = reference_result if method_id == "reference_time_expanded_cbf" else simulate_motion(policy, problem)
            meta = sp4_method_metadata(method_id)
            centralized = str(meta["scope"]) == "centralized"
            metrics = evaluate_motion(problem, result, runtime_ms=result.runtime_ms, reference_result=reference_result, centralized=centralized)
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP4_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "n_robots": params.n_robots,
                "world_size_m": problem.world.map.size_m,
                "obstacle_count": len(problem.world.map.obstacles),
                "robot_radius_m": params.robot_radius_m,
                "target_tolerance_m": params.target_tolerance_m,
                "safety_margin_m": params.safety_margin_m,
                "dt_s": params.dt_s,
                "horizon_s": params.horizon_s,
                "communication_radius": params.communication_radius,
                **metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_theory_check(row, problem, result))
            video_candidates.append({"problem": problem, "result": result, "row": row})
            for robot_row in robot_status_rows(problem, result):
                robot_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "scenario_generator": generator,
                        "scenario_variant_id": variant_id,
                        "seed": seed,
                        "method": method_id,
                        **method_taxonomy_fields(method_id),
                        **robot_row,
                    }
                )
            if len(sample_rows) < sample_limit * max(params.n_robots, 1) * 80:
                for sample in trajectory_sample_rows(problem, result):
                    sample_rows.append(
                        {
                            "experiment_id": experiment_id,
                            "scenario_generator": generator,
                            "scenario_variant_id": variant_id,
                            "seed": seed,
                            "method": method_id,
                            **sample,
                        }
                    )

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", []))
    theory_audit = summarize_theory_checks(theory_rows, rows, seeds, generators, method_specs)

    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, ranking_columns(ranking_rows))
    write_csv(tables_dir / "robot_status.csv", robot_rows, robot_status_columns(robot_rows))
    write_csv(tables_dir / "trajectory_samples.csv", sample_rows, trajectory_sample_columns(sample_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, theory_check_columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, hypothesis_columns(hypothesis_rows))
    save_json(output_dir / "theory_audit.json", theory_audit)

    plot_arrival_success(rows, figures_dir / "sp4_arrival_success_by_method.png")
    plot_collision_rate_by_scenario(rows, figures_dir / "sp4_collision_rate_by_scenario.png")
    plot_time_energy_pareto(rows, figures_dir / "sp4_time_energy_pareto.png")
    plot_clearance_by_method(rows, figures_dir / "sp4_clearance_by_method.png")
    plot_path_efficiency(rows, figures_dir / "sp4_path_efficiency_by_method.png")
    plot_communication_degradation(rows, figures_dir / "sp4_communication_radius_degradation.png")

    scenario_videos: list[dict[str, Any]] = []
    artifact_config = dict(config.get("artifacts", {}))
    if bool(artifact_config.get("save_video", True)):
        scenario_videos = save_scenario_videos(video_candidates, figures_dir=figures_dir, videos_dir=videos_dir, video_config=dict(artifact_config.get("video", {})))

    report_path = output_dir / "report.md"
    write_report(report_path, experiment_id, seeds, generators, summary_rows, ranking_rows, hypothesis_rows, theory_audit, scenario_videos)
    manifest = {
        "experiment_id": experiment_id,
        "mode": "monte_carlo",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "seeds": seeds,
        "scenario_generators": generators,
        "methods": [spec["id"] for spec in method_specs],
        "runs": len(rows),
        "report": str(report_path),
        "performance_ranking": str(tables_dir / "performance_ranking.csv"),
        "hypotheses": len(hypothesis_rows),
        "theory_audit": str(output_dir / "theory_audit.json"),
        "scenario_videos": scenario_videos,
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    all_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_generator"]), str(row["method"]))].append(row)
        all_groups[str(row["method"])].append(row)
    for (scenario, method), selected in sorted(groups.items()):
        output.append(_summary_row(scenario, method, selected))
    for method, selected in sorted(all_groups.items()):
        output.append(_summary_row("ALL_SCENARIOS", method, selected))
    return output


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = [row for row in summarize_rows(rows) if row["scenario_generator"] == "ALL_SCENARIOS"]
    summaries.sort(key=_ranking_key)
    output = []
    for rank, row in enumerate(summaries, start=1):
        ranked = dict(row)
        ranked["rank"] = rank
        ranked["ranking_rule"] = "maximize arrival success first, minimize timeouts, then collisions, gap vs safe reference, arrival time, energy, messages and runtime"
        output.append(ranked)
    return output


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for spec in hypotheses:
        metric = str(spec.get("metric", "performance_gap_vs_reference"))
        alpha = float(spec.get("alpha", 0.05))
        if "method_a" in spec and "method_b" in spec:
            pairs = _paired_values(rows, str(spec["method_a"]), str(spec["method_b"]), metric)
            diffs = np.asarray([a - b for a, b in pairs], dtype=float)
            if diffs.size < 2:
                output.append(_hypothesis_error(spec, metric, "not enough paired samples"))
                continue
            alternative = str(spec.get("direction", "less"))
            alternative = alternative if alternative in {"less", "greater", "two-sided"} else "two-sided"
            p_value = robust_wilcoxon_signed_rank_pvalue(diffs, alternative=alternative)
            inference = mean_difference_inference(diffs)
            output.append(
                {
                    "id": spec.get("id", ""),
                    "metric": metric,
                    "test": "wilcoxon_signed_rank",
                    "n_pairs": int(diffs.size),
                    "p_value": p_value,
                    **inference,
                    "alpha": alpha,
                    "reject": bool(p_value < alpha),
                    "status": "ok",
                    "methods": f"{spec['method_a']} vs {spec['method_b']}",
                }
            )
            continue
        if "methods" in spec:
            methods = [str(method) for method in spec["methods"]]
            blocks = _friedman_blocks(rows, methods, metric)
            if len(blocks) < 2:
                output.append(_hypothesis_error(spec, metric, "not enough complete blocks"))
                continue
            arrays = [[block[method] for block in blocks] for method in methods]
            statistic, p_value = stats.friedmanchisquare(*arrays)
            statistic = float(statistic)
            p_value = float(p_value) if np.isfinite(p_value) else 1.0
            kendall_w = float(statistic / (len(blocks) * max(len(methods) - 1, 1)))
            output.append(
                {
                    "id": spec.get("id", ""),
                    "metric": metric,
                    "test": "friedman_chi_square",
                    "n_pairs": len(blocks),
                    "p_value": p_value,
                    "effect": kendall_w,
                    "effect_name": "kendall_w",
                    "ci95_low": math.nan,
                    "ci95_high": math.nan,
                    "effect_size": kendall_w,
                    "effect_size_name": "kendall_w",
                    "rank_biserial": math.nan,
                    "alpha": alpha,
                    "reject": bool(p_value < alpha),
                    "status": "ok",
                    "methods": ",".join(methods),
                }
            )
            continue
        output.append(_hypothesis_error(spec, metric, "unsupported hypothesis spec"))
    return apply_holm_correction(output)


def save_scenario_videos(candidates: list[dict[str, Any]], *, figures_dir: Path, videos_dir: Path, video_config: dict[str, Any]) -> list[dict[str, Any]]:
    max_per_scenario = int(video_config.get("max_per_scenario", 4))
    selection_metric = str(video_config.get("selection_metric", "arrival_success_rate"))
    fps = int(video_config.get("fps", 12))
    duration_s = float(video_config.get("duration_s", 12.0))
    final_hold_s = float(video_config.get("final_hold_s", 2.0))
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        by_scenario[str(item["row"]["scenario_generator"])].append(item)
    output = []
    for scenario, items in sorted(by_scenario.items()):
        by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            by_method[str(item["row"]["method"])].append(item)
        selected = []
        for method_items in by_method.values():
            method_items.sort(key=lambda item: abs(_float(item["row"].get(selection_metric)) - _median(method_items, selection_metric)))
            selected.append(method_items[0])
        selected.sort(key=lambda item: _ranking_key(item["row"]))
        for item in selected[:max_per_scenario]:
            row = item["row"]
            stem = _artifact_stem(row)
            snapshot = figures_dir / f"{stem}.png"
            video = videos_dir / f"{stem}.mp4"
            title = _artifact_title(row)
            save_motion_snapshot(item["problem"], item["result"], snapshot, title)
            ok = save_motion_video(
                item["problem"],
                item["result"],
                video,
                title,
                fps=fps,
                duration_s=duration_s,
                final_hold_s=final_hold_s,
            )
            if ok:
                output.append({"scenario_generator": scenario, "method": row["method"], "seed": int(row["seed"]), "snapshot": str(snapshot), "video": str(video)})
    return output


def write_report(
    path: Path,
    experiment_id: str,
    seeds: list[int],
    generators: list[str],
    summary_rows: list[dict[str, Any]],
    ranking_rows: list[dict[str, Any]],
    hypothesis_rows: list[dict[str, Any]],
    theory_audit: dict[str, Any],
    scenario_videos: list[dict[str, Any]],
) -> None:
    lines = [
        f"# {experiment_id}",
        "",
        "SP4 evaluates post-allocation AMR motion: after robots have been assigned to load/slot targets, can they arrive safely and cheaply under finite horizon, obstacles and local communication?",
        f"- Seeds: `{seeds[0]}`-`{seeds[-1]}` (`n={len(seeds)}`)" if seeds else "- Seeds: none",
        f"- Scenario generators: `{', '.join(generators)}`",
        "",
        "## Method Taxonomy",
        "",
        "| Method | Label | Family | Scope | Ownership | Variant |",
        "|---|---|---|---|---|---|",
    ]
    for method in sorted({row["method"] for row in summary_rows}):
        meta = sp4_method_metadata(str(method))
        lines.append(f"| {method} | {meta['label']} | {meta['family']} | {meta['scope']} | {meta['ownership']} | {meta['variant']} |")
    lines.extend(
        [
            "",
            "## Performance Ranking",
            "",
            "| Rank | Method | Family | Owner | Arrival | Collision | Timeout | Time s | Energy Wh | Gap | Runtime ms |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in ranking_rows:
        lines.append(
            "| {rank} | {method} | {family} | {owner} | {arr:.3f} | {col:.4f} | {tout:.3f} | {time:.2f} | {energy:.2f} | {gap:.3f} | {runtime:.3f} |".format(
                rank=row["rank"],
                method=row["method"],
                family=row.get("method_family", ""),
                owner=row.get("method_ownership", ""),
                arr=row.get("arrival_success_rate_mean", math.nan),
                col=row.get("collision_rate_mean", math.nan),
                tout=row.get("timeout_rate_mean", math.nan),
                time=row.get("mean_arrival_time_s_mean", math.nan),
                energy=row.get("energy_proxy_wh_mean", math.nan),
                gap=row.get("performance_gap_vs_reference_mean", row.get("optimality_gap_vs_reference_mean", math.nan)),
                runtime=row.get("runtime_ms_mean", math.nan),
            )
        )
    lines.extend(["", "## Theory Audit", "", f"- Checks: `{theory_audit.get('checks', 0)}`.", f"- Failed checks: `{theory_audit.get('failed_checks', 0)}`.", f"- Passed: `{theory_audit.get('passed', False)}`.", "", "## Hypotheses", "", "| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |", "|---|---|---:|---:|---:|---:|---|---|---|"])
    for row in hypothesis_rows:
        ci_low = _float(row.get("ci95_low"))
        ci_high = _float(row.get("ci95_high"))
        ci = f"[{ci_low:.4g}, {ci_high:.4g}]" if np.isfinite(ci_low) and np.isfinite(ci_high) else ""
        lines.append(f"| {row.get('id')} | {row.get('metric')} | {row.get('n_pairs')} | {_format(row.get('p_value'))} | {_format(row.get('p_value_holm'))} | {_format(row.get('effect'))} | {ci} | {row.get('reject_holm', row.get('reject'))} | {row.get('status')} |")
    lines.extend(["", "## Scenario Videos", ""])
    for item in scenario_videos:
        lines.append(f"- `{item['scenario_generator']}` `{item['method']}` seed `{item['seed']}`: `{Path(item['video']).name}`")
    lines.extend(["", "## Artifacts", "", "- `tables/runs.csv`", "- `tables/summary.csv`", "- `tables/performance_ranking.csv`", "- `tables/robot_status.csv`", "- `tables/trajectory_samples.csv`", "- `tables/theory_checks.csv`", "- `tables/hypothesis_results.csv`", "- `theory_audit.json`", "- `figures/sp4_arrival_success_by_method.png`", "- `figures/sp4_collision_rate_by_scenario.png`", "- `figures/sp4_time_energy_pareto.png`", "- `figures/sp4_clearance_by_method.png`", "- `figures/sp4_path_efficiency_by_method.png`", "- `figures/sp4_communication_radius_degradation.png`", "- `videos/sp4_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp4_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
    }


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp4_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": meta["trainable_parameters"],
        "method_tuned_parameters": meta["tuned_parameters"],
        "method_uses_neural_policy": meta["uses_neural_policy"],
        "method_uses_decoder": meta["uses_decoder"],
    }


def summarize_theory_checks(theory_rows: list[dict[str, Any]], rows: list[dict[str, Any]], seeds: list[int], generators: list[str], method_specs: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    gate = _reference_collision_gate(rows)
    failed_count = len(failed) + int(gate["failed_checks"])
    checks = len(theory_rows) + int(gate["checks"])
    return {
        "checks": checks,
        "failed_checks": failed_count,
        "passed": failed_count == 0,
        "seed_count": len(seeds),
        "seed_start": min(seeds) if seeds else None,
        "seed_end": max(seeds) if seeds else None,
        "scenario_generators": generators,
        "method_count": len(method_specs),
        "model_scope": "single_integrator_planar_motion_with_obstacles_and_pairwise_robot_clearance",
        "not_claimed": "SP4 is not a full kinodynamic MAPF optimum and not a contact/manipulation controller.",
        "gates": {"G4_reference_no_worse_collision_than_direct": gate},
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "n_robots", "world_size_m", "obstacle_count", "robot_radius_m", "target_tolerance_m", "safety_margin_m", "dt_s", "horizon_s", "communication_radius", *SUMMARY_METRICS], rows)


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "n", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def ranking_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "rank", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "n", "ranking_rule", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def robot_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_family", "method_scope", "method_ownership", "robot_id", "robot_index", "target_label", "start_x", "start_y", "target_x", "target_y", "final_x", "final_y", "arrived", "arrival_time_s", "final_target_error_m", "path_length_m", "direct_distance_m", "path_efficiency_ratio", "battery_fraction", "max_speed_mps"], rows)


def trajectory_sample_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "time_s", "robot_id", "robot_index", "x", "y", "vx", "vy", "target_x", "target_y"], rows)


def theory_check_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "passed", "rates_valid", "finite_metrics", "speed_valid", "message"], rows)


def hypothesis_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(
        [
            "id",
            "metric",
            "test",
            "n_pairs",
            "p_value",
            "p_value_raw",
            "p_value_holm",
            "effect",
            "effect_name",
            "ci95_low",
            "ci95_high",
            "effect_size",
            "effect_size_name",
            "rank_biserial",
            "alpha",
            "reject_raw",
            "reject_holm",
            "reject",
            "status",
            "methods",
        ],
        rows,
    )


def _summary_row(scenario: str, method: str, selected: list[dict[str, Any]]) -> dict[str, Any]:
    first = selected[0]
    row = {
        "scenario_generator": scenario,
        "method": method,
        "method_label": first.get("method_label", method),
        **method_taxonomy_fields(method),
        **method_resource_fields(method),
        "n": len(selected),
    }
    for metric in SUMMARY_METRICS:
        row[f"{metric}_mean"] = _mean(selected, metric)
    return row


def _theory_check(row: dict[str, Any], problem: SP4Problem, result: Any) -> dict[str, Any]:
    rates = [
        _float(row.get("arrival_success_rate")),
        _float(row.get("timeout_rate")),
        _float(row.get("collision_rate")),
    ]
    rates_valid = all(0.0 <= value <= 1.000001 for value in rates if np.isfinite(value))
    gap = _float(row.get("performance_gap_vs_reference", row.get("optimality_gap_vs_reference")))
    gap_valid = bool(np.isfinite(gap) and gap >= 0.0)
    finite_metrics = bool(np.isfinite(result.positions).all() and np.isfinite(result.velocities).all())
    speed_valid = _float(row.get("max_speed_violation_mps")) <= 1e-6
    passed = bool(rates_valid and gap_valid and finite_metrics and speed_valid and result.positions.shape[1] == len(problem.world.robots))
    return {
        "experiment_id": row["experiment_id"],
        "scenario_generator": row["scenario_generator"],
        "scenario_variant_id": row["scenario_variant_id"],
        "seed": row["seed"],
        "method": row["method"],
        "passed": passed,
        "rates_valid": rates_valid,
        "gap_valid": gap_valid,
        "finite_metrics": finite_metrics,
        "speed_valid": speed_valid,
        "message": "" if passed else "SP4 theory check failed",
    }


def _seed_range(config: Any) -> list[int]:
    if isinstance(config, list):
        return [int(value) for value in config]
    start = int(config.get("start", 0))
    count = int(config.get("count", 1))
    return list(range(start, start + count))


def _method_specs(config: list[Any]) -> list[dict[str, Any]]:
    specs = []
    for item in config:
        if isinstance(item, str):
            specs.append({"id": item, "params": {}})
        else:
            specs.append({"id": str(item["id"]), "params": dict(item.get("params", {}))})
    if specs:
        return specs
    return [
        {"id": "direct_to_target", "params": {}},
        {"id": "priority_yield", "params": {}},
        {"id": "apf_obstacle_avoidance", "params": {}},
        {"id": "velocity_obstacle_proxy", "params": {}},
        {"id": "cbf_safety_filter", "params": {}},
        {"id": "smith_motion_field", "params": {}},
        {"id": "energy_aware_smith_motion", "params": {}},
        {"id": "reference_time_expanded_cbf", "params": {}},
    ]


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (
        -_finite_or(row.get("arrival_success_rate_mean", row.get("arrival_success_rate")), 0.0),
        _finite(row.get("timeout_rate_mean", row.get("timeout_rate"))),
        _finite(row.get("collision_rate_mean", row.get("collision_rate"))),
        _finite(row.get("performance_gap_vs_reference_mean", row.get("performance_gap_vs_reference", row.get("optimality_gap_vs_reference_mean", row.get("optimality_gap_vs_reference"))))),
        _finite(row.get("mean_arrival_time_s_mean", row.get("mean_arrival_time_s"))),
        _finite(row.get("energy_proxy_wh_mean", row.get("energy_proxy_wh"))),
        _finite(row.get("communication_messages_mean", row.get("communication_messages"))),
        _finite(row.get("runtime_ms_mean", row.get("runtime_ms"))),
    )


def _paired_values(rows: list[dict[str, Any]], method_a: str, method_b: str, metric: str) -> list[tuple[float, float]]:
    by_key: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))][str(row["method"])] = row
    pairs = []
    for methods in by_key.values():
        if method_a in methods and method_b in methods:
            a = _float(methods[method_a].get(metric))
            b = _float(methods[method_b].get(metric))
            if np.isfinite(a) and np.isfinite(b):
                pairs.append((a, b))
    return pairs


def _friedman_blocks(rows: list[dict[str, Any]], methods: list[str], metric: str) -> list[dict[str, float]]:
    by_key: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))][str(row["method"])] = row
    blocks = []
    for row_by_method in by_key.values():
        if all(method in row_by_method for method in methods):
            block = {method: _float(row_by_method[method].get(metric)) for method in methods}
            if all(np.isfinite(value) for value in block.values()):
                blocks.append(block)
    return blocks


def _reference_collision_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))][str(row["method"])] = row
    checks = 0
    deltas: list[float] = []
    outliers = []
    for key, by_method in by_key.items():
        if "reference_time_expanded_cbf" not in by_method or "direct_to_target" not in by_method:
            continue
        checks += 1
        ref = _float(by_method["reference_time_expanded_cbf"].get("collision_rate"))
        direct = _float(by_method["direct_to_target"].get("collision_rate"))
        if np.isfinite(ref) and np.isfinite(direct):
            delta = ref - direct
            deltas.append(delta)
            if delta > 1e-9:
                outliers.append({"scenario_generator": key[0], "scenario_variant_id": key[1], "seed": key[2], "reference_collision_rate": ref, "direct_collision_rate": direct, "delta": delta})
    mean_delta = float(np.mean(deltas)) if deltas else math.nan
    failed = int(bool(deltas) and mean_delta > 1e-9)
    return {
        "description": "The safe reference is a heuristic reference, not an exact MAPF oracle; it must reduce paired collision rate in aggregate versus direct target tracking.",
        "checks": checks,
        "failed_checks": failed,
        "passed": failed == 0,
        "mean_reference_minus_direct_collision_rate": mean_delta,
        "outlier_count": len(outliers),
        "outliers": outliers[:25],
        "truncated_outliers": max(0, len(outliers) - 25),
    }


def _hypothesis_error(spec: dict[str, Any], metric: str, message: str) -> dict[str, Any]:
    return {
        "id": spec.get("id", ""),
        "metric": metric,
        "test": "",
        "n_pairs": 0,
        "p_value": math.nan,
        "p_value_raw": math.nan,
        "p_value_holm": math.nan,
        "effect": math.nan,
        "effect_name": "",
        "ci95_low": math.nan,
        "ci95_high": math.nan,
        "effect_size": math.nan,
        "effect_size_name": "",
        "rank_biserial": math.nan,
        "alpha": float(spec.get("alpha", 0.05)),
        "reject_raw": False,
        "reject_holm": False,
        "reject": False,
        "status": message,
        "methods": "",
    }


def _wilcoxon_signed_rank_pvalue(diffs: np.ndarray, *, alternative: str) -> float:
    finite = np.asarray(diffs, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < 2:
        return 1.0
    try:
        result = stats.wilcoxon(finite, alternative=alternative, zero_method="zsplit")
        p_value = float(result.pvalue)
    except ValueError:
        p_value = 1.0
    return p_value if np.isfinite(p_value) else 1.0


def _artifact_stem(row: dict[str, Any]) -> str:
    meta = sp4_method_metadata(str(row["method"]))
    return (
        "sp4_{scenario}_{owner}_{family}_{scope}_{variant}_{method}_seed{seed}".format(
            scenario=str(row["scenario_generator"]).replace("_", "-"),
            owner=str(meta["ownership"]).replace("_", "-"),
            family=str(meta["family"]).replace("_", "-"),
            scope=str(meta["scope"]).replace("_", "-"),
            variant=str(meta["variant"]).replace("_", "-"),
            method=str(row["method"]).replace("_", "-"),
            seed=row["seed"],
        )
    )


def _artifact_title(row: dict[str, Any]) -> str:
    meta = sp4_method_metadata(str(row["method"]))
    return f"SP4 {row['scenario_generator']} | {meta['title']} | seed {row['seed']}"


def _median(items: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(item["row"].get(metric)) for item in items], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else 0.0


def _ordered_columns(preferred: list[str], rows: list[dict[str, Any]]) -> list[str]:
    seen = set()
    columns = []
    for column in preferred:
        if column not in seen:
            columns.append(column)
            seen.add(column)
    for row in rows:
        for column in row:
            if column not in seen:
                columns.append(column)
                seen.add(column)
    return columns


def _mean(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    return float(np.mean(values)) if values.size else math.nan


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _finite(value: Any) -> float:
    value = _float(value)
    return value if np.isfinite(value) else math.inf


def _finite_or(value: Any, default: float) -> float:
    value = _float(value)
    return value if np.isfinite(value) else default


def _format(value: Any) -> str:
    value = _float(value)
    if not np.isfinite(value):
        return "n/a"
    if abs(value) >= 100.0 or abs(value) < 1e-3 and value != 0:
        return f"{value:.3g}"
    return f"{value:.4f}"
