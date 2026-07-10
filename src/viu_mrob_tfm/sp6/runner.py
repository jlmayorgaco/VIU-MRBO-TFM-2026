"""Executable SP6 operational robustness Monte Carlo pipeline."""

from __future__ import annotations

import csv
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
from viu_mrob_tfm.sp6.methods import SP6_METHOD_LABELS, make_sp6_policy, simulate_recovery, sp6_method_metadata
from viu_mrob_tfm.sp6.metrics import (
    evaluate_recovery,
    load_status_rows,
    method_resource_fields,
    robot_status_rows,
    trajectory_sample_rows,
)
from viu_mrob_tfm.sp6.scenario import SP6Problem, iter_sp6_problems
from viu_mrob_tfm.sp6.visualization import (
    plot_communication_resource_pareto,
    plot_completion_vs_reassignment,
    plot_degradation_by_scenario,
    plot_recovery_success_by_method,
    plot_recovery_time_by_method,
    plot_safety_by_method,
    save_recovery_snapshot,
    save_recovery_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


SUMMARY_METRICS = [
    "feasible_load_count",
    "completed_load_count",
    "task_completion_rate",
    "recovery_success",
    "recovery_time_s",
    "load_target_reached_rate",
    "mean_final_pose_error_m",
    "max_final_pose_error_m",
    "mean_final_orientation_error_deg",
    "max_final_orientation_error_deg",
    "lost_load_rate",
    "infeasible_load_count",
    "infeasible_load_detection_rate",
    "post_event_wrench_feasible_rate",
    "mean_wrench_residual_norm",
    "min_wrench_margin",
    "unsupported_time_s",
    "load_pause_time_s",
    "degraded_speed_time_s",
    "replacement_arrival_time_s",
    "final_assigned_loads",
    "final_idle_robots",
    "reassignment_count",
    "final_active_robot_rate",
    "failed_robot_count",
    "battery_margin_final",
    "min_battery_fraction",
    "communication_coverage_ratio",
    "communication_messages",
    "collision_count",
    "collision_rate",
    "safety_violation_count",
    "min_robot_clearance_m",
    "min_obstacle_clearance_m",
    "min_load_clearance_m",
    "travel_distance_m",
    "mean_path_length_m",
    "path_efficiency_ratio",
    "energy_proxy_wh",
    "mean_speed_mps",
    "max_speed_mps",
    "max_speed_violation_mps",
    "runtime_ms",
    "score_value",
    "reference_score_value",
    "signed_score_delta_vs_reference",
    "performance_gap_vs_reference",
    "optimality_gap_vs_reference",
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


def run_sp6_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"monte_carlo", "mc", "debug"}:
        return run_monte_carlo(config, config_path=config_path)
    raise ValueError(f"Unknown SP6 config mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp6") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    seeds = _seed_range(config.get("seeds", {"start": 7100, "count": 5}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    method_specs = _method_specs(config.get("methods", []))
    sample_limit = int(config.get("trajectory_sample_runs", 12))

    rows: list[dict[str, Any]] = []
    robot_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []

    for generator, variant_id, seed, params, problem in iter_sp6_problems(generators, seeds):
        reference_policy = make_sp6_policy("reference_resilient_oracle")
        reference_result = simulate_recovery(reference_policy, problem)
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            policy = make_sp6_policy(method_id, dict(method_spec.get("params", {})))
            result = reference_result if method_id == "reference_resilient_oracle" else simulate_recovery(policy, problem)
            meta = sp6_method_metadata(method_id)
            centralized = str(meta["scope"]) == "centralized"
            metrics = evaluate_recovery(problem, result, reference_result=reference_result, centralized=centralized)
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP6_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "event_kind": problem.event.kind,
                "event_time_s": problem.event.time_s,
                "event_observation_delay_s": problem.event.observation_delay_s,
                "event_observed_time_s": result.event_observed_time_s,
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "world_size_m": problem.world.map.size_m,
                "obstacle_count_initial": len(problem.world.map.obstacles),
                "obstacle_count_post_event": len(problem.active_obstacles_at(problem.event.time_s + problem.dt_s)),
                "robot_radius_m": problem.robot_radius_m,
                "target_tolerance_m": problem.target_tolerance_m,
                "safety_margin_m": problem.safety_margin_m,
                "dt_s": problem.dt_s,
                "horizon_s": problem.horizon_s,
                "communication_radius_initial": problem.communication_radius,
                "communication_radius_post_event": problem.communication_radius_at(problem.event.time_s + problem.dt_s, observed=False),
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
            for load_row in load_status_rows(problem, result):
                load_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "scenario_generator": generator,
                        "scenario_variant_id": variant_id,
                        "seed": seed,
                        "method": method_id,
                        **method_taxonomy_fields(method_id),
                        **load_row,
                    }
                )
            if len(sample_rows) < sample_limit * max(params.n_robots + params.n_loads, 1) * 100:
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
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", _default_hypotheses()))
    theory_audit = summarize_theory_checks(theory_rows, rows, seeds, generators, method_specs)

    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, ranking_columns(ranking_rows))
    write_csv(tables_dir / "robot_status.csv", robot_rows, robot_status_columns(robot_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, load_status_columns(load_rows))
    write_csv(tables_dir / "trajectory_samples.csv", sample_rows, trajectory_sample_columns(sample_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, theory_check_columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, hypothesis_columns(hypothesis_rows))
    save_json(output_dir / "theory_audit.json", theory_audit)

    plot_recovery_success_by_method(rows, figures_dir / "sp6_recovery_success_by_method.png")
    plot_degradation_by_scenario(rows, figures_dir / "sp6_lost_load_degradation_by_scenario.png")
    plot_recovery_time_by_method(rows, figures_dir / "sp6_recovery_time_by_method.png")
    plot_safety_by_method(rows, figures_dir / "sp6_safety_by_method.png")
    plot_communication_resource_pareto(rows, figures_dir / "sp6_communication_resource_pareto.png")
    plot_completion_vs_reassignment(rows, figures_dir / "sp6_completion_vs_reassignment.png")

    scenario_videos: list[dict[str, Any]] = []
    artifact_config = dict(config.get("artifacts", {}))
    if bool(artifact_config.get("save_video", True)):
        scenario_videos = save_scenario_videos(video_candidates, figures_dir=figures_dir, videos_dir=videos_dir, video_config=dict(artifact_config.get("video", {})))
    write_video_catalog(videos_dir / "VIDEO_INDEX.md", tables_dir / "video_catalog.csv", scenario_videos)

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
        ranked["ranking_rule"] = "maximize recovery success and feasible-load completion, minimize lost loads and reference gap, then minimize collisions, recovery time, energy, messages and runtime"
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
    max_per_scenario = int(video_config.get("max_per_scenario", 2))
    selection_metric = str(video_config.get("selection_metric", "score_value"))
    fps = int(video_config.get("fps", 10))
    duration_s = float(video_config.get("duration_s", 42.0))
    final_hold_s = float(video_config.get("final_hold_s", 8.0))
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
            save_recovery_snapshot(item["problem"], item["result"], snapshot, title)
            ok = save_recovery_video(
                item["problem"],
                item["result"],
                video,
                title,
                fps=fps,
                duration_s=duration_s,
                final_hold_s=final_hold_s,
            )
            if ok:
                output.append(
                    {
                        "scenario_generator": scenario,
                        "scenario_variant_id": row.get("scenario_variant_id", ""),
                        "method": row["method"],
                        "method_label": row.get("method_label", row["method"]),
                        "seed": int(row["seed"]),
                        "event_kind": row.get("event_kind", ""),
                        "event_time_s": row.get("event_time_s", ""),
                        "n_robots": row.get("n_robots", ""),
                        "n_loads": row.get("n_loads", ""),
                        "objective": "Recover payload transport after the disruption while preserving slot formation, wrench feasibility and final load pose.",
                        "key_metrics": "recovery_success={}; completion={}; target_rate={}; min_wrench_margin={}; pause_s={}; degraded_s={}; replacement_s={}; pose_error_m={}; collision_rate={}".format(
                            _format(row.get("recovery_success")),
                            _format(row.get("task_completion_rate")),
                            _format(row.get("load_target_reached_rate")),
                            _format(row.get("min_wrench_margin")),
                            _format(row.get("load_pause_time_s")),
                            _format(row.get("degraded_speed_time_s")),
                            _format(row.get("replacement_arrival_time_s")),
                            _format(row.get("mean_final_pose_error_m")),
                            _format(row.get("collision_rate")),
                        ),
                        "snapshot": str(snapshot),
                        "video": str(video),
                    }
                )
    return output


def write_video_catalog(markdown_path: Path, csv_path: Path, scenario_videos: list[dict[str, Any]]) -> None:
    columns = [
        "scenario_generator",
        "scenario_variant_id",
        "method",
        "method_label",
        "seed",
        "event_kind",
        "event_time_s",
        "n_robots",
        "n_loads",
        "objective",
        "key_metrics",
        "snapshot",
        "video",
    ]
    write_csv(csv_path, scenario_videos, columns)
    lines = [
        "# SP6 Video Index",
        "",
        "Cada MP4 muestra transporte cooperativo de carga con evento de resiliencia: reclutamiento a slots, movimiento de payload, fallo/degradacion, reemplazo/reasignacion y estado final.",
        "",
    ]
    if not scenario_videos:
        lines.append("No videos were generated.")
    for item in scenario_videos:
        lines.extend(
            [
                f"## {Path(str(item['video'])).name}",
                "",
                f"- Scenario: `{item.get('scenario_generator')}` / `{item.get('scenario_variant_id')}`.",
                f"- Method: `{item.get('method')}` ({item.get('method_label')}).",
                f"- Seed: `{item.get('seed')}`.",
                f"- Event: `{item.get('event_kind')}` at `{item.get('event_time_s')}` s.",
                f"- Size: `{item.get('n_robots')}` AMR, `{item.get('n_loads')}` loads.",
                f"- Objective: {item.get('objective')}",
                f"- Metrics: {item.get('key_metrics')}",
                f"- Snapshot: `{Path(str(item.get('snapshot'))).name}`.",
                "",
            ]
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "SP6 evaluates resilient cooperative payload transport: AMR coalitions must keep or recover slot contact, wrench feasibility and final payload pose after communication degradation, robot failure, battery depletion, blocked corridors, delayed consensus or infeasible demand.",
        f"- Seeds: `{seeds[0]}`-`{seeds[-1]}` (`n={len(seeds)}`)" if seeds else "- Seeds: none",
        f"- Scenario generators: `{', '.join(generators)}`",
        "",
        "## Method Taxonomy",
        "",
        "| Method | Label | Family | Scope | Owner | Variant |",
        "|---|---|---|---|---|---|",
    ]
    for method in sorted({row["method"] for row in summary_rows}):
        meta = sp6_method_metadata(str(method))
        lines.append(f"| {method} | {meta['label']} | {meta['family']} | {meta['scope']} | {meta['ownership']} | {meta['variant']} |")
    lines.extend(
        [
            "",
            "## Performance Ranking",
            "",
            "| Rank | Method | Success | Completion | Lost | Collision | Infeasible detection | Wrench feasible | Time s | Energy Wh | Gap | Runtime ms |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in ranking_rows:
        lines.append(
            "| {rank} | {method} | {success:.3f} | {completion:.3f} | {lost:.3f} | {collision:.4f} | {detect:.3f} | {wrench:.3f} | {time:.2f} | {energy:.2f} | {gap:.3f} | {runtime:.3f} |".format(
                rank=row["rank"],
                method=row["method"],
                success=row.get("recovery_success_mean", math.nan),
                completion=row.get("task_completion_rate_mean", math.nan),
                lost=row.get("lost_load_rate_mean", math.nan),
                collision=row.get("collision_rate_mean", math.nan),
                detect=row.get("infeasible_load_detection_rate_mean", math.nan),
                wrench=row.get("post_event_wrench_feasible_rate_mean", math.nan),
                time=row.get("recovery_time_s_mean", math.nan),
                energy=row.get("energy_proxy_wh_mean", math.nan),
                gap=row.get("performance_gap_vs_reference_mean", math.nan),
                runtime=row.get("runtime_ms_mean", math.nan),
            )
        )
    lines.extend(
        [
            "",
            "## Theory Audit",
            "",
            f"- Checks: `{theory_audit.get('checks', 0)}`.",
            f"- Failed checks: `{theory_audit.get('failed_checks', 0)}`.",
            f"- Passed: `{theory_audit.get('passed', False)}`.",
            "",
            "## Hypotheses",
            "",
            "| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |",
            "|---|---|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in hypothesis_rows:
        ci_low = _float(row.get("ci95_low"))
        ci_high = _float(row.get("ci95_high"))
        ci = f"[{ci_low:.4g}, {ci_high:.4g}]" if np.isfinite(ci_low) and np.isfinite(ci_high) else ""
        lines.append(f"| {row.get('id')} | {row.get('metric')} | {row.get('n_pairs')} | {_format(row.get('p_value'))} | {_format(row.get('p_value_holm'))} | {_format(row.get('effect'))} | {ci} | {row.get('reject_holm', row.get('reject'))} | {row.get('status')} |")
    lines.extend(["", "## Scenario Videos", ""])
    for item in scenario_videos:
        lines.append(f"- `{item['scenario_generator']}` `{item['method']}` seed `{item['seed']}`: `{Path(item['video']).name}`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `tables/runs.csv`",
            "- `tables/summary.csv`",
            "- `tables/performance_ranking.csv`",
            "- `tables/robot_status.csv`",
            "- `tables/load_status.csv`",
            "- `tables/trajectory_samples.csv`",
            "- `tables/theory_checks.csv`",
            "- `tables/hypothesis_results.csv`",
            "- `tables/video_catalog.csv`",
            "- `theory_audit.json`",
            "- `figures/sp6_recovery_success_by_method.png`",
            "- `figures/sp6_lost_load_degradation_by_scenario.png`",
            "- `figures/sp6_recovery_time_by_method.png`",
            "- `figures/sp6_safety_by_method.png`",
            "- `figures/sp6_communication_resource_pareto.png`",
            "- `figures/sp6_completion_vs_reassignment.png`",
            "- `videos/VIDEO_INDEX.md`",
            "- `videos/sp6_<scenario>_<owner>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp6_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
    }


def summarize_theory_checks(theory_rows: list[dict[str, Any]], rows: list[dict[str, Any]], seeds: list[int], generators: list[str], method_specs: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    return {
        "checks": len(theory_rows),
        "failed_checks": len(failed),
        "passed": len(failed) == 0,
        "seed_count": len(seeds),
        "seed_start": min(seeds) if seeds else None,
        "seed_end": max(seeds) if seeds else None,
        "scenario_generators": generators,
        "method_count": len(method_specs),
        "model_scope": "planar_payload_transport_robustness_with_slots_wrench_margin_handover_battery_dropout_and_replacement_reallocation",
        "not_claimed": "SP6 is a reduced-order cooperative payload transport robustness benchmark; it is not hardware validation, full frictional contact simulation, full stochastic POMDP optimal control, or a certified kinodynamic multi-agent planner.",
        "failed_examples": failed[:25],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "event_kind", "event_time_s", "event_observation_delay_s", "event_observed_time_s", "n_robots", "n_loads", "world_size_m", "obstacle_count_initial", "obstacle_count_post_event", "robot_radius_m", "target_tolerance_m", "safety_margin_m", "dt_s", "horizon_s", "communication_radius_initial", "communication_radius_post_event", *SUMMARY_METRICS], rows)


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "n", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def ranking_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "rank", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *RESOURCE_COLUMNS, "n", "ranking_rule", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def robot_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_family", "method_scope", "method_ownership", "robot_id", "robot_index", "final_active", "assigned_load_label", "start_x", "start_y", "final_x", "final_y", "path_length_m", "initial_battery_fraction", "final_battery_fraction", "battery_reserve_fraction", "max_speed_mps", "force_limit_n", "torque_limit_nm", "payload_kg"], rows)


def load_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_family", "method_scope", "method_ownership", "load_id", "load_index", "mass_kg", "post_event_demand_kg", "min_coalition_size", "assigned_robots", "assigned_capacity_kg", "assigned_force_n", "assigned_torque_nm", "wrench_force_demand_n", "wrench_torque_demand_nm", "feasible_after_event", "completed", "physically_feasible_final", "final_unassigned_infeasible", "final_pose_x", "final_pose_y", "final_pose_theta_rad", "target_pose_x", "target_pose_y", "target_pose_theta_rad", "final_pose_error_m", "final_orientation_error_deg", "final_wrench_margin", "unsupported_time_s", "load_pause_time_s", "degraded_speed_time_s", "completion_time_s", "destination_x", "destination_y"], rows)


def trajectory_sample_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "time_s", "entity", "entity_id", "robot_index", "assigned_load_label", "active", "battery_fraction", "x", "y", "theta_rad", "vx", "vy", "target_x", "target_y", "target_theta_rad", "wrench_margin", "wrench_residual_norm", "support_level", "paused", "degraded_speed", "event_phase"], rows)


def theory_check_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "passed", "rates_valid", "finite_metrics", "shape_valid", "speed_valid", "event_valid", "clearance_evaluated", "battery_valid", "message"], rows)


def hypothesis_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["id", "metric", "test", "n_pairs", "p_value", "p_value_raw", "p_value_holm", "effect", "effect_name", "ci95_low", "ci95_high", "effect_size", "effect_size_name", "rank_biserial", "alpha", "reject_raw", "reject_holm", "reject", "status", "methods"], rows)


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


def _theory_check(row: dict[str, Any], problem: SP6Problem, result: Any) -> dict[str, Any]:
    rates = [
        _float(row.get("task_completion_rate")),
        _float(row.get("recovery_success")),
        _float(row.get("lost_load_rate")),
        _float(row.get("infeasible_load_detection_rate")),
        _float(row.get("post_event_wrench_feasible_rate")),
        _float(row.get("final_active_robot_rate")),
        _float(row.get("communication_coverage_ratio")),
        _float(row.get("collision_rate")),
        _float(row.get("performance_gap_vs_reference")),
    ]
    rates_valid = all(0.0 <= value <= 1.000001 for value in rates if np.isfinite(value))
    finite_metrics = bool(np.isfinite(result.robot_positions).all() and np.isfinite(result.robot_velocities).all() and np.isfinite(result.battery_fraction).all() and np.isfinite(result.load_pose).all())
    shape_valid = bool(result.robot_positions.shape[1] == len(problem.world.robots) and result.labels.shape[1] == len(problem.world.robots) and result.completed_loads.shape[1] == len(problem.world.loads) and result.load_pose.shape[1] == len(problem.world.loads))
    speed_valid = _float(row.get("max_speed_violation_mps")) <= 1e-6
    event_valid = bool(result.event_observed_time_s >= problem.event.time_s)
    robot_clearance = _float(row.get("min_robot_clearance_m"))
    obstacle_clearance = _float(row.get("min_obstacle_clearance_m"))
    load_clearance = _float(row.get("min_load_clearance_m"))
    clearance_evaluated = bool(
        np.isfinite(robot_clearance)
        and (np.isfinite(obstacle_clearance) or np.isposinf(obstacle_clearance))
        and (np.isfinite(load_clearance) or np.isposinf(load_clearance))
    )
    hard_clearance_valid = bool(
        int(_float(row.get("collision_count"))) == 0
        and all(
            (value >= -1e-6) or np.isposinf(value)
            for value in [robot_clearance, obstacle_clearance, load_clearance]
        )
    )
    battery = np.asarray(result.battery_fraction, dtype=float)
    battery_valid = bool(np.all(battery >= -1e-9) and np.all(battery <= 1.0 + 1e-9))
    passed = bool(rates_valid and finite_metrics and shape_valid and speed_valid and event_valid and clearance_evaluated and hard_clearance_valid and battery_valid)
    return {
        "experiment_id": row["experiment_id"],
        "scenario_generator": row["scenario_generator"],
        "scenario_variant_id": row["scenario_variant_id"],
        "seed": row["seed"],
        "method": row["method"],
        "passed": passed,
        "rates_valid": rates_valid,
        "finite_metrics": finite_metrics,
        "shape_valid": shape_valid,
        "speed_valid": speed_valid,
        "event_valid": event_valid,
        "clearance_evaluated": clearance_evaluated,
        "hard_clearance_valid": hard_clearance_valid,
        "battery_valid": battery_valid,
        "message": "" if passed else "SP6 theory check failed",
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
    return [{"id": method, "params": {}} for method in SP6_METHOD_LABELS]


def _default_hypotheses() -> list[dict[str, Any]]:
    return [
        {
            "id": "H6.1_ours_reduces_lost_load_rate_vs_classic_greedy",
            "method_a": "ours_guarded_wrench_market_recovery",
            "method_b": "classic_decentralized_greedy_recovery",
            "metric": "lost_load_rate",
            "direction": "less",
        },
        {
            "id": "H6.2_ours_improves_completion_vs_smith_qr",
            "method_a": "ours_guarded_wrench_market_recovery",
            "method_b": "smith_qr_recovery",
            "metric": "task_completion_rate",
            "direction": "greater",
        },
        {
            "id": "H6.3_recovery_family_differs_on_reference_gap",
            "methods": ["classic_decentralized_greedy_recovery", "cbba_recovery", "smith_qr_recovery", "ours_guarded_wrench_market_recovery"],
            "metric": "performance_gap_vs_reference",
        },
    ]


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (
        -_finite_or(row.get("recovery_success_mean", row.get("recovery_success")), 0.0),
        -_finite_or(row.get("task_completion_rate_mean", row.get("task_completion_rate")), 0.0),
        -_finite_or(row.get("load_target_reached_rate_mean", row.get("load_target_reached_rate")), 0.0),
        _finite(row.get("lost_load_rate_mean", row.get("lost_load_rate"))),
        _finite(row.get("performance_gap_vs_reference_mean", row.get("performance_gap_vs_reference", row.get("optimality_gap_vs_reference_mean", row.get("optimality_gap_vs_reference"))))),
        _finite(row.get("collision_rate_mean", row.get("collision_rate"))),
        -_finite_or(row.get("infeasible_load_detection_rate_mean", row.get("infeasible_load_detection_rate")), 0.0),
        -_finite_or(row.get("post_event_wrench_feasible_rate_mean", row.get("post_event_wrench_feasible_rate")), 0.0),
        _finite(row.get("recovery_time_s_mean", row.get("recovery_time_s"))),
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


def _artifact_stem(row: dict[str, Any]) -> str:
    meta = sp6_method_metadata(str(row["method"]))
    return (
        "sp6_{scenario}_{owner}_{family}_{scope}_{variant}_{method}_seed{seed}".format(
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
    meta = sp6_method_metadata(str(row["method"]))
    return f"SP6 {row['scenario_generator']} | {meta['title']} | seed {row['seed']}"


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
