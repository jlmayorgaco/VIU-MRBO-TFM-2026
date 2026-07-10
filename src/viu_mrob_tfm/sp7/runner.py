"""Executable SP7 communication/network robustness Monte Carlo pipeline."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

from viu_mrob_tfm.experiment_stats import apply_holm_correction, mean_difference_inference, wilcoxon_signed_rank_pvalue
from viu_mrob_tfm.sp5.metrics import robot_status_rows, trajectory_sample_rows
from viu_mrob_tfm.sp5.methods import simulate_transport
from viu_mrob_tfm.sp7.methods import SP7_METHOD_LABELS, make_sp7_policy, sp7_method_metadata
from viu_mrob_tfm.sp7.metrics import evaluate_sp7_run, frame_rows, method_resource_fields, method_taxonomy_fields
from viu_mrob_tfm.sp7.scenario import iter_sp7_problems
from viu_mrob_tfm.sp7.visualization import (
    plot_connectivity_vs_radius,
    plot_packet_loss_delay_heatmap,
    plot_quality_resource_pareto,
    plot_relay_temporal_connectivity,
    plot_sensing_vs_collision,
    plot_transport_success_under_stress,
    save_communication_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


TRANSPORT_METRICS = [
    "selected_task_load",
    "pickup_success",
    "target_reached",
    "transport_success",
    "final_position_error_m",
    "final_orientation_error_deg",
    "formation_integrity_rate",
    "formation_broken_rate",
    "collision_rate",
    "min_obstacle_clearance_m",
    "min_mobile_group_clearance_m",
    "min_load_clearance_m",
    "travel_distance_m",
    "energy_proxy_wh",
    "completion_time_s",
    "assigned_robots",
    "idle_robots",
    "runtime_ms",
    "score_value",
    "optimality_gap_vs_reference",
]

NETWORK_METRICS = [
    "network_severity",
    "attempted_messages",
    "delivered_messages",
    "active_control_messages",
    "packet_delivery_ratio",
    "control_packet_ratio",
    "mean_link_delay_s",
    "delay_violation_rate",
    "mean_active_link_count",
    "mean_largest_component_ratio",
    "mean_component_count",
    "mean_algebraic_connectivity",
    "disconnected_time_ratio",
    "coalition_connected_time_ratio",
    "temporal_coalition_connected_rate",
    "relay_success_rate",
    "direct_clique_time_ratio",
    "base_connected_time_ratio",
    "communication_outage_count",
    "longest_outage_s",
    "mean_outage_duration_s",
    "obstacle_detection_rate",
    "mobile_group_detection_rate",
    "sensor_coverage_rate",
    "network_quality_score",
    "transport_network_score",
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


def run_sp7_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"debug", "smoke", "monte_carlo", "mc"}:
        return run_monte_carlo(config, config_path=config_path)
    raise ValueError(f"Unknown SP7 config mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp7") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    seeds = _seed_range(config.get("seeds", {"start": 8700, "count": 3}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    profile_filter = {str(item) for item in config.get("profile_ids", [])}
    method_specs = _method_specs(config.get("methods", []))
    sample_limit = int(config.get("trajectory_sample_runs", 12))
    video_limit = int(config.get("video_sample_runs", 4))

    rows: list[dict[str, Any]] = []
    robot_rows: list[dict[str, Any]] = []
    trajectory_rows: list[dict[str, Any]] = []
    network_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []

    for generator, variant_id, seed, sp7_params, sp5_params, problem in iter_sp7_problems(generators, seeds):
        if profile_filter and sp7_params.profile.profile_id not in profile_filter and not sp7_params.profile.profile_id.startswith("mc_"):
            continue
        reference_policy = make_sp7_policy("reference_full_communication", sp7_params.profile, transport_mode=sp5_params.transport_mode)
        reference_result = simulate_transport(reference_policy, problem)
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            policy = make_sp7_policy(method_id, sp7_params.profile, transport_mode=sp5_params.transport_mode, params=dict(method_spec.get("params", {})))
            result = reference_result if method_id == "reference_full_communication" else simulate_transport(policy, problem)
            transport_metrics, network_metrics, frames = evaluate_sp7_run(
                problem,
                result,
                sp7_params.profile,
                method_id=method_id,
                seed=seed,
                reference_result=reference_result,
            )
            meta = sp7_method_metadata(method_id)
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP7_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "communication_profile": sp7_params.profile.profile_id,
                "scenario_description": sp7_params.description,
                "transport_mode": sp5_params.transport_mode,
                "n_robots": sp5_params.n_robots,
                "n_loads": sp5_params.n_loads,
                "robots_minus_loads": int(sp5_params.n_robots - sp5_params.n_loads),
                "world_size_m": problem.world.map.size_m,
                "obstacle_count": len(problem.world.map.obstacles),
                "mobile_group_count": len(problem.mobile_groups),
                "dt_s": problem.dt_s,
                "horizon_s": problem.horizon_s,
                "sp5_backing_policy": policy.method_id,
                "communication_dependency": meta["communication_dependency"],
                **transport_metrics.to_dict(),
                **network_metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_theory_check(row, problem, result))
            video_candidates.append({"problem": problem, "result": result, "profile": sp7_params.profile, "row": row})
            for robot_row in robot_status_rows(problem, result):
                robot_rows.append({"experiment_id": experiment_id, "scenario_generator": generator, "scenario_variant_id": variant_id, "seed": seed, "method": method_id, "communication_profile": sp7_params.profile.profile_id, **method_taxonomy_fields(method_id), **robot_row})
            if len(trajectory_rows) < sample_limit * max(sp5_params.n_robots + 1, 1) * 90:
                for sample in trajectory_sample_rows(problem, result):
                    trajectory_rows.append({"experiment_id": experiment_id, "scenario_generator": generator, "scenario_variant_id": variant_id, "seed": seed, "method": method_id, "communication_profile": sp7_params.profile.profile_id, **sample})
            if len(network_rows) < sample_limit * 120:
                network_rows.extend(frame_rows(experiment_id, generator, variant_id, seed, method_id, sp7_params.profile.profile_id, frames))

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", _default_hypotheses()))
    theory_audit = summarize_theory_checks(theory_rows, rows, seeds, generators, method_specs)

    write_csv(tables_dir / "runs.csv", rows, columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, columns(ranking_rows))
    write_csv(tables_dir / "robot_status.csv", robot_rows, columns(robot_rows))
    write_csv(tables_dir / "trajectory_samples.csv", trajectory_rows, columns(trajectory_rows))
    write_csv(tables_dir / "network_timeseries.csv", network_rows, columns(network_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, columns(hypothesis_rows))
    save_json(output_dir / "theory_audit.json", theory_audit)

    if bool(config.get("make_figures", True)):
        plot_connectivity_vs_radius(rows, figures_dir / "sp7_connectivity_vs_radius_by_method.png")
        plot_transport_success_under_stress(rows, figures_dir / "sp7_transport_success_under_network_stress.png")
        plot_packet_loss_delay_heatmap(rows, figures_dir / "sp7_packet_loss_delay_heatmap.png")
        plot_relay_temporal_connectivity(rows, figures_dir / "sp7_relay_temporal_connectivity.png")
        plot_sensing_vs_collision(rows, figures_dir / "sp7_sensing_vs_collision.png")
        plot_quality_resource_pareto(rows, figures_dir / "sp7_quality_resource_pareto.png")

    video_rows = save_videos(videos_dir, video_candidates, limit=video_limit) if bool(config.get("make_videos", True)) else []
    write_csv(tables_dir / "video_catalog.csv", video_rows, columns(video_rows))
    write_video_index(videos_dir, video_rows)
    write_report(output_dir, experiment_id, rows, ranking_rows, hypothesis_rows, theory_audit, video_rows)
    return {
        "experiment_id": experiment_id,
        "output_dir": str(output_dir),
        "runs": len(rows),
        "summary_rows": len(summary_rows),
        "failed_theory_checks": theory_audit["failed_checks"],
        "videos": len(video_rows),
    }


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_generator"]), str(row["communication_profile"]), str(row["method"]))].append(row)
        groups[("ALL_SCENARIOS", "ALL_PROFILES", str(row["method"]))].append(row)
    output = []
    for (scenario, profile, method), selected in sorted(groups.items()):
        first = selected[0]
        item = {
            "scenario_generator": scenario,
            "communication_profile": profile,
            "method": method,
            "method_label": first.get("method_label", method),
            **method_taxonomy_fields(method),
            **method_resource_fields(method),
            "n": len(selected),
        }
        for metric in [*TRANSPORT_METRICS, *NETWORK_METRICS]:
            item[f"{metric}_mean"] = _mean(selected, metric)
            item[f"{metric}_std"] = _std(selected, metric)
        output.append(item)
    return output


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_generator"]), str(row["method"]))].append(row)
        groups[("ALL_SCENARIOS", str(row["method"]))].append(row)
    summaries = []
    for (scenario, method), selected in sorted(groups.items()):
        first = selected[0]
        item = {
            "scenario_generator": scenario,
            "rank": 0,
            "method": method,
            "method_label": first.get("method_label", method),
            **method_taxonomy_fields(method),
            **method_resource_fields(method),
            "n": len(selected),
            "ranking_rule": "max transport-network score, max transport success/connectivity/sensor coverage, min collisions/outages/messages/runtime",
        }
        for metric in [*TRANSPORT_METRICS, *NETWORK_METRICS]:
            item[f"{metric}_mean"] = _mean(selected, metric)
        summaries.append(item)
    ranked = []
    for scenario in sorted({row["scenario_generator"] for row in summaries}, key=lambda item: (item != "ALL_SCENARIOS", item)):
        ordered = sorted([row for row in summaries if row["scenario_generator"] == scenario], key=_ranking_key)
        for rank, row in enumerate(ordered, start=1):
            row = dict(row)
            row["rank"] = rank
            ranked.append(row)
    return ranked


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for spec in hypotheses or []:
        try:
            output.append(_evaluate_hypothesis(rows, spec))
        except Exception as exc:  # pragma: no cover
            output.append(_hypothesis_error(spec, str(exc)))
    return apply_holm_correction(output)


def _evaluate_hypothesis(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    cls = str(spec.get("class", "PairedSuperiorityHypothesis"))
    metric = str(spec["metric"])
    alpha = float(spec.get("alpha", 0.05))
    if cls == "PairedSuperiorityHypothesis":
        method_a = str(spec["method_a"])
        method_b = str(spec["method_b"])
        filter_profile_contains = str(spec.get("profile_contains", ""))
        lower_is_better = bool(spec.get("lower_is_better", False))
        pairs = _paired_diffs(rows, method_a, method_b, metric, profile_contains=filter_profile_contains)
        alternative = "less" if lower_is_better else "greater"
        p_value = wilcoxon_signed_rank_pvalue(pairs, alternative=alternative)
        inference = mean_difference_inference(pairs, effect_name=f"{method_a}-{method_b} {metric}")
        return {
            "id": spec.get("id", f"{method_a}_vs_{method_b}_{metric}"),
            "class": cls,
            "null_hypothesis": spec.get("null_hypothesis", f"{method_a} does not improve {metric} vs {method_b}."),
            "alternative": f"{method_a} {'<' if lower_is_better else '>'} {method_b}",
            "metric": metric,
            "methods": f"{method_a} vs {method_b}",
            "profile_filter": filter_profile_contains or "ALL",
            "n_pairs": int(np.asarray(pairs).size),
            "p_value": p_value,
            "alpha": alpha,
            **inference,
        }
    if cls == "MultiMethodFriedmanHypothesis":
        methods = [str(item) for item in spec.get("methods", [])]
        profile_contains = str(spec.get("profile_contains", ""))
        blocks = _friedman_blocks(rows, methods, metric, profile_contains=profile_contains)
        p_value = 1.0
        statistic = 0.0
        if len(blocks) >= 2 and len(methods) >= 3:
            arrays = [np.asarray([block[method] for block in blocks], dtype=float) for method in methods]
            statistic, p_value = stats.friedmanchisquare(*arrays)
        return {
            "id": spec.get("id", f"friedman_{metric}"),
            "class": cls,
            "null_hypothesis": spec.get("null_hypothesis", "All compared methods have equal distributions."),
            "alternative": "At least one method differs.",
            "metric": metric,
            "methods": " ".join(methods),
            "profile_filter": profile_contains or "ALL",
            "n_blocks": len(blocks),
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "effect": float(statistic),
            "effect_name": "friedman_chi_square",
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "effect_size": math.nan,
            "effect_size_name": "not_applicable",
            "rank_biserial": math.nan,
        }
    if cls == "SpearmanCorrelationHypothesis":
        x = np.asarray([_finite_radius(row["communication_radius_m"]) for row in rows], dtype=float)
        y = np.asarray([_float(row[metric]) for row in rows], dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        if np.sum(mask) >= 3 and np.unique(x[mask]).size >= 2 and np.unique(y[mask]).size >= 2:
            rho, p_value = stats.spearmanr(x[mask], y[mask])
        else:
            rho, p_value = 0.0, 1.0
        return {
            "id": spec.get("id", f"spearman_radius_{metric}"),
            "class": cls,
            "null_hypothesis": spec.get("null_hypothesis", f"Communication radius is not correlated with {metric}."),
            "alternative": "Positive monotone association.",
            "metric": metric,
            "methods": "ALL",
            "n_pairs": int(np.sum(mask)),
            "statistic": float(rho),
            "p_value": float(p_value) / 2.0 if float(rho) > 0 else 1.0,
            "alpha": alpha,
            "effect": float(rho),
            "effect_name": "spearman_rho",
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "effect_size": float(rho),
            "effect_size_name": "spearman_rho",
            "rank_biserial": math.nan,
        }
    raise ValueError(f"Unknown SP7 hypothesis class: {cls}")


def save_videos(videos_dir: Path, candidates: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    selected = []
    harsh = [item for item in candidates if "harsh" in str(item["row"]["communication_profile"]) or "intermittent" in str(item["row"]["communication_profile"])]
    priority = harsh + candidates
    seen = set()
    for item in priority:
        key = (item["row"]["scenario_generator"], item["row"]["communication_profile"], item["row"]["method"])
        if key in seen:
            continue
        if item["row"]["method"] not in {"ours_connectivity_wrench_game", "ours_delay_robust_repair", "classic_centralized_global_mpc", "sota_decentralized_cbba_relay"}:
            continue
        selected.append(item)
        seen.add(key)
        if len(selected) >= limit:
            break
    rows = []
    for item in selected:
        row = item["row"]
        stem = _artifact_stem(row)
        path = videos_dir / f"{stem}.mp4"
        ok = save_communication_video(item["problem"], item["result"], item["profile"], path, _artifact_title(row), duration_s=52.0)
        if ok:
            rows.append({"scenario_generator": row["scenario_generator"], "communication_profile": row["communication_profile"], "seed": row["seed"], "method": row["method"], "video": str(path), "objective": "Show AMR relay/connectivity while transporting payload around obstacles and moving groups."})
    return rows


def write_video_index(videos_dir: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# SP7 Video Index", "", "SP7 videos overlay communication links while AMRs transport payloads around obstacles and moving robot groups.", ""]
    for row in rows:
        lines.append(f"- `{row['scenario_generator']}` `{row['communication_profile']}` `{row['method']}` seed `{row['seed']}`: `{Path(row['video']).name}`")
    (videos_dir / "VIDEO_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(output_dir: Path, experiment_id: str, rows: list[dict[str, Any]], ranking_rows: list[dict[str, Any]], hypothesis_rows: list[dict[str, Any]], theory_audit: dict[str, Any], video_rows: list[dict[str, Any]]) -> None:
    best = next((row for row in ranking_rows if row["scenario_generator"] == "ALL_SCENARIOS" and int(row["rank"]) == 1), None)
    lines = [
        f"# {experiment_id}",
        "",
        "SP7 evaluates cooperative transport under time-varying communication and sensing stress: radio radius, packet loss, burst drops, delay, jitter, intermittent outages and sensor degradation.",
        "",
        "## Scope",
        "",
        "- Uses SP5 payload transport worlds with static obstacles and moving robot groups.",
        "- Adds temporal robot-robot communication graphs and sensor-detection metrics.",
        "- Measures direct connectivity, multi-hop relay connectivity and temporal connectivity.",
        "- Does not claim RF propagation fidelity or hardware-network validation.",
        "",
        "## Summary",
        "",
        f"- Runs: `{len(rows)}`",
        f"- Theory failed checks: `{theory_audit['failed_checks']}`",
        f"- Best all-scenario method: `{best['method'] if best else 'n/a'}`",
        f"- Videos generated: `{len(video_rows)}`",
        "",
        "## Hypotheses",
    ]
    for row in hypothesis_rows:
        lines.append(f"- `{row.get('id')}`: p={float(row.get('p_value_raw', row.get('p_value', math.nan))):.4g}, Holm reject={row.get('reject_holm', False)}.")
    lines.extend(["", "## Primary Ranking"])
    for row in ranking_rows[: min(12, len(ranking_rows))]:
        lines.append(f"- {row['scenario_generator']} rank {row['rank']}: `{row['method']}` score={float(row.get('transport_network_score_mean', math.nan)):.3f}, connectivity={float(row.get('coalition_connected_time_ratio_mean', math.nan)):.3f}.")
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_theory_checks(theory_rows: list[dict[str, Any]], rows: list[dict[str, Any]], seeds: list[int], generators: list[str], method_specs: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row["passed"])]
    return {
        "checks": len(theory_rows),
        "failed_checks": len(failed),
        "passed": len(failed) == 0,
        "seed_count": len(seeds),
        "scenario_generators": generators,
        "method_count": len(method_specs),
        "model_scope": "temporal_unit_disk_packet_network_plus_sp5_planar_payload_transport",
        "not_claimed": "SP7 is a communication/sensing robustness benchmark, not RF channel propagation, hardware networking, or full multi-agent POMDP validation.",
        "failed_examples": failed[:20],
    }


def _theory_check(row: dict[str, Any], problem: Any, result: Any) -> dict[str, Any]:
    rate_fields = [
        "packet_delivery_ratio",
        "control_packet_ratio",
        "coalition_connected_time_ratio",
        "temporal_coalition_connected_rate",
        "sensor_coverage_rate",
        "network_quality_score",
        "transport_network_score",
        "transport_success",
        "collision_rate",
    ]
    rates_ok = all(0.0 <= _float(row[field]) <= 1.000001 for field in rate_fields if np.isfinite(_float(row[field])))
    finite_ok = bool(np.isfinite(result.robot_positions).all() and np.isfinite(result.load_pose).all())
    shape_ok = bool(result.robot_positions.shape[1] == len(problem.world.robots))
    messages_ok = int(row["attempted_messages"]) >= int(row["delivered_messages"]) >= 0 and int(row["delivered_messages"]) >= int(row["active_control_messages"]) >= 0
    load_clearance = _float(row.get("min_load_clearance_m"))
    load_clearance_ok = bool((load_clearance >= -1e-6) or np.isposinf(load_clearance))
    passed = bool(rates_ok and finite_ok and shape_ok and messages_ok and load_clearance_ok)
    return {"experiment_id": row["experiment_id"], "scenario_generator": row["scenario_generator"], "scenario_variant_id": row["scenario_variant_id"], "seed": row["seed"], "method": row["method"], "communication_profile": row["communication_profile"], "passed": passed, "rates_ok": rates_ok, "finite_ok": finite_ok, "shape_ok": shape_ok, "messages_ok": messages_ok, "load_clearance_ok": load_clearance_ok}


def _default_hypotheses() -> list[dict[str, Any]]:
    return [
        {
            "id": "H7.1_radius_improves_coalition_connectivity",
            "class": "SpearmanCorrelationHypothesis",
            "metric": "coalition_connected_time_ratio",
            "null_hypothesis": "Communication radius is not positively associated with coalition connectivity.",
        },
        {
            "id": "H7.2_ours_connectivity_beats_classic_under_harsh_profiles",
            "class": "PairedSuperiorityHypothesis",
            "metric": "transport_network_score",
            "method_a": "ours_connectivity_wrench_game",
            "method_b": "classic_centralized_global_mpc",
            "profile_contains": "harsh",
            "lower_is_better": False,
            "null_hypothesis": "Ours connectivity-aware wrench game does not improve harsh-profile transport-network score over classic centralized global control.",
        },
        {
            "id": "H7.3_methods_differ_under_intermittent_communication",
            "class": "MultiMethodFriedmanHypothesis",
            "metric": "transport_network_score",
            "profile_contains": "intermittent",
            "methods": ["classic_decentralized_sensor_apf", "sota_decentralized_cbba_relay", "ours_connectivity_wrench_game", "ours_delay_robust_repair"],
            "null_hypothesis": "All compared methods have equal transport-network score under intermittent communication.",
        },
    ]


def _paired_diffs(rows: list[dict[str, Any]], method_a: str, method_b: str, metric: str, *, profile_contains: str = "") -> np.ndarray:
    by_key: dict[tuple[str, str, int, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        if profile_contains and profile_contains not in str(row["communication_profile"]):
            continue
        if str(row["method"]) not in {method_a, method_b}:
            continue
        key = (str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]), str(row["communication_profile"]))
        by_key[key][str(row["method"])] = _float(row[metric])
    return np.asarray([values[method_a] - values[method_b] for values in by_key.values() if method_a in values and method_b in values], dtype=float)


def _friedman_blocks(rows: list[dict[str, Any]], methods: list[str], metric: str, *, profile_contains: str = "") -> list[dict[str, float]]:
    by_key: dict[tuple[str, str, int, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        if profile_contains and profile_contains not in str(row["communication_profile"]):
            continue
        if str(row["method"]) not in methods:
            continue
        key = (str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]), str(row["communication_profile"]))
        by_key[key][str(row["method"])] = _float(row[metric])
    return [values for values in by_key.values() if all(method in values for method in methods)]


def _hypothesis_error(spec: dict[str, Any], message: str) -> dict[str, Any]:
    return {"id": spec.get("id", "unknown"), "class": spec.get("class", "unknown"), "metric": spec.get("metric", ""), "error": message, "p_value": 1.0, "alpha": float(spec.get("alpha", 0.05)), "effect": math.nan, "effect_name": "error", "ci95_low": math.nan, "ci95_high": math.nan, "effect_size": math.nan, "effect_size_name": "error", "rank_biserial": math.nan}


def _method_specs(config: list[Any]) -> list[dict[str, Any]]:
    specs = [{"id": str(item), "params": {}} if isinstance(item, str) else {"id": str(item["id"]), "params": dict(item.get("params", {}))} for item in config]
    if specs:
        return specs
    return [{"id": method, "params": {}} for method in SP7_METHOD_LABELS]


def _seed_range(config: Any) -> list[int]:
    if isinstance(config, list):
        return [int(value) for value in config]
    return list(range(int(config.get("start", 0)), int(config.get("start", 0)) + int(config.get("count", 1))))


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (
        -_float(row.get("transport_network_score_mean")),
        -_float(row.get("transport_success_mean")),
        -_float(row.get("coalition_connected_time_ratio_mean")),
        -_float(row.get("sensor_coverage_rate_mean")),
        _float(row.get("collision_rate_mean")),
        _float(row.get("longest_outage_s_mean")),
        _float(row.get("attempted_messages_mean")),
        _float(row.get("runtime_ms_mean")),
    )


def _artifact_stem(row: dict[str, Any]) -> str:
    return f"sp7_{str(row['scenario_generator']).replace('_','-')}_{str(row['communication_profile']).replace('_','-')}_{str(row['method']).replace('_','-')}_seed{row['seed']}"


def _artifact_title(row: dict[str, Any]) -> str:
    return f"SP7 {row['scenario_generator']} | {row['communication_profile']} | {row['method']} | seed {row['seed']}"


def columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["experiment_id", "scenario_generator", "scenario_variant_id", "communication_profile", "seed", "method", "method_label", "rank"]
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
        numeric = float(value)
    except (TypeError, ValueError):
        return math.nan
    return numeric


def _finite_radius(value: Any) -> float:
    numeric = _float(value)
    return 14.0 if not np.isfinite(numeric) else numeric
