"""Executable SP1 tuning, training, and Monte Carlo pipeline."""

from __future__ import annotations

import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy import stats

from viu_mrob_tfm.allocation import DecisionContext, timed_allocate
from viu_mrob_tfm.experiment_stats import (
    apply_holm_correction,
    mean_difference_inference,
    mean_value_inference,
    wilcoxon_signed_rank_pvalue,
)
from viu_mrob_tfm.sp1.methods import (
    CentralizedCoalitionOracleAllocator,
    SP1_METHOD_LABELS,
    fit_imitation_model,
    make_sp1_allocator,
    sp1_method_metadata,
)
from viu_mrob_tfm.sp1.mappo import train_mappo_recruitment
from viu_mrob_tfm.sp1.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp1.scenario import SP1RecruitmentScenario, iter_sp1_worlds
from viu_mrob_tfm.sp1.visualization import (
    plot_best_method_by_scenario,
    plot_communication_degradation,
    plot_demand_ratio_interaction,
    plot_method_performance_matrix,
    plot_ours_vs_others,
    plot_physical_cost_tradeoff,
    plot_quality_resource_pareto,
    plot_reference_gap,
    plot_summary_bars,
    plot_taxonomy_comparison,
    save_recruitment_snapshot,
    save_recruitment_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


def run_sp1_config(config_path: str | Path) -> dict[str, Any]:
    """Run an SP1 config file and return a manifest dictionary."""

    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"monte_carlo", "mc", "debug"}:
        return run_monte_carlo(config, config_path=config_path)
    if mode in {"tune", "tune_model_based", "tuning"}:
        return run_tuning(config, config_path=config_path)
    if mode in {"train_imitation", "imitation"}:
        return run_imitation_training(config, config_path=config_path)
    if mode in {"train_mappo", "mappo", "train_mappo_recruitment"}:
        return train_mappo_recruitment(config, config_path=config_path)
    if mode in {"train_mappo_stub", "mappo_stub"}:
        return write_mappo_stub(config, config_path=config_path)
    raise ValueError(f"Unknown SP1 config mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp1") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")

    seeds = _seed_range(config.get("seeds", {"start": 2000, "count": 5}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    method_specs = _method_specs(config.get("methods", []))
    tuned_params = _load_tuned_params(method_specs)
    rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []
    representative: tuple[Any, Any, dict[str, Any]] | None = None

    for generator, variant_id, seed, params, world in iter_sp1_worlds(generators, seeds):
        oracle = CentralizedCoalitionOracleAllocator()
        context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})
        oracle_assignment, oracle_runtime_ms = timed_allocate(oracle, context)
        oracle_metrics = evaluate_assignment(
            world,
            oracle_assignment,
            runtime_ms=oracle_runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=params.communication_radius,
            centralized=True,
        )

        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            if _should_skip_optional(method_spec):
                continue
            params_for_method = dict(method_spec.get("params", {}))
            params_for_method.update(tuned_params.get(method_id, {}))
            allocator = make_sp1_allocator(method_id, params_for_method)
            centralized = method_id in {"hungarian_expanded", "centralized_coalition_milp"}
            assignment, runtime_ms = timed_allocate(allocator, context)
            metrics = evaluate_assignment(
                world,
                assignment,
                runtime_ms=runtime_ms,
                oracle_assignment=oracle_assignment,
                communication_radius=params.communication_radius,
                centralized=centralized,
            )
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP1_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id, params_for_method),
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                "rho": float(len(world.robots) / max(sum(load.min_coalition_size for load in world.loads), 1)),
                "heterogeneous_robots": params.heterogeneous_robots,
                "communication_radius": params.communication_radius,
                "oracle_runtime_ms": oracle_runtime_ms,
                **metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_allocation_theory_check(row, world, assignment, metrics.to_dict()))
            video_candidates.append({"world": world, "assignment": assignment, "row": row})
            for load_row in load_diagnostics(world, assignment):
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
            if representative is None and method_id in {"primal_dual_wrench_market", "centralized_coalition_milp"}:
                representative = (world, assignment, row)

        oracle_row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": "oracle_reference",
                "method_label": "Oracle reference",
                **method_taxonomy_fields("oracle_reference"),
                **method_resource_fields("oracle_reference", {}),
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                "rho": float(len(world.robots) / max(sum(load.min_coalition_size for load in world.loads), 1)),
                "heterogeneous_robots": params.heterogeneous_robots,
                "communication_radius": params.communication_radius,
                "oracle_runtime_ms": oracle_runtime_ms,
                **oracle_metrics.to_dict(),
            }
        rows.append(oracle_row)
        theory_rows.append(_allocation_theory_check(oracle_row, world, oracle_assignment, oracle_metrics.to_dict()))

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, performance_ranking_columns(ranking_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, load_status_columns(load_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, theory_check_columns(theory_rows))
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", []))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, hypothesis_columns(hypothesis_rows))
    theory_audit = summarize_theory_checks(theory_rows, seeds, generators, method_specs)
    save_json(output_dir / "theory_audit.json", theory_audit)
    plot_summary_bars(rows, figures_dir / "sp1_demand_satisfaction_by_method.png")
    plot_demand_ratio_interaction(rows, figures_dir / "sp1_demand_ratio_interaction.png")
    plot_method_performance_matrix(rows, figures_dir / "sp1_performance_matrix_by_method.png")
    plot_taxonomy_comparison(rows, figures_dir / "sp1_taxonomy_scope_family_ownership.png")
    plot_ours_vs_others(rows, figures_dir / "sp1_ours_vs_baselines_vs_reference.png")
    plot_reference_gap(rows, figures_dir / "sp1_reference_gap_proposed_methods.png")
    plot_communication_degradation(rows, figures_dir / "sp1_communication_radius_degradation.png")
    plot_best_method_by_scenario(rows, figures_dir / "sp1_best_method_by_scenario.png")
    plot_quality_resource_pareto(rows, figures_dir / "sp1_quality_resource_pareto.png")
    plot_physical_cost_tradeoff(rows, figures_dir / "sp1_physical_cost_tradeoff.png")
    artifact_config = config.get("artifacts", {})
    scenario_videos: list[dict[str, Any]] = []
    if bool(artifact_config.get("save_video", True)):
        scenario_videos = save_scenario_videos(
            video_candidates,
            figures_dir=figures_dir,
            videos_dir=videos_dir,
            video_config=dict(artifact_config.get("video", {})),
        )
    if representative is not None and bool(artifact_config.get("save_video", True)):
        video_options = dict(artifact_config.get("video", {}))
        world, assignment, row = representative
        representative_stem = _video_stem(row, str(row["scenario_generator"]), "representative")
        representative_title = _video_title(row, str(row["scenario_generator"]), "representative")
        save_recruitment_snapshot(
            world,
            assignment,
            figures_dir / f"{representative_stem}.png",
            representative_title,
        )
        save_recruitment_video(
            world,
            assignment,
            videos_dir / f"{representative_stem}.mp4",
            representative_title,
            fps=int(video_options.get("fps", 12)),
            duration_s=float(video_options.get("duration_s", 10.0)),
            final_hold_s=float(video_options.get("final_hold_s", 2.0)),
        )
    report_path = output_dir / "report.md"
    write_report(
        report_path,
        experiment_id,
        seeds,
        generators,
        summary_rows,
        ranking_rows=ranking_rows,
        hypothesis_rows=hypothesis_rows,
        theory_audit=theory_audit,
        scenario_videos=scenario_videos,
    )
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
        "scenario_videos": scenario_videos,
        "hypotheses": len(hypothesis_rows),
        "theory_audit": str(output_dir / "theory_audit.json"),
        "performance_ranking": str(tables_dir / "performance_ranking.csv"),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def run_tuning(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_artifact = Path(config.get("tuning", {}).get("output_artifact", "outputs/tuning/SP1/model_based/best_params.yaml"))
    ensure_directory(output_artifact.parent)
    seeds = _seed_range(config.get("seeds", {"start": 0, "count": 5}))
    validation_seeds = _seed_range(config.get("validation_seeds", {"start": 1000, "count": 0}))
    generators = [str(item.get("param_generator", item.get("generator", "under_demand"))) for item in config.get("scenarios", [])]
    if not generators:
        generators = ["under_demand", "balanced_demand", "over_demand"]
    method_grids = config.get("tuning", {}).get("method_param_grid", {})
    methods = [str(item.get("id", item)) for item in config.get("methods", [])]
    if not methods:
        methods = ["replicator_cardinality", "smith_cardinality", "primal_dual_cardinality_capacity", "primal_dual_wrench_market"]

    best: dict[str, dict[str, Any]] = {}
    scores: list[dict[str, Any]] = []
    for method_id in methods:
        candidates = _expand_grid(method_grids.get(method_id, {"default": [{}]}))
        best_score = math.inf
        best_params: dict[str, Any] = {}
        best_train_score = math.inf
        best_validation_score = math.nan
        selection_split = "validation" if validation_seeds else "train"
        for candidate in candidates:
            train_score = _score_candidate(method_id, candidate, generators, seeds)
            validation_score = _score_candidate(method_id, candidate, generators, validation_seeds) if validation_seeds else math.nan
            selection_score = validation_score if validation_seeds else train_score
            scores.append(
                {
                    "method": method_id,
                    "selection_split": selection_split,
                    "selection_score": selection_score,
                    "train_score": train_score,
                    "validation_score": validation_score,
                    **candidate,
                }
            )
            if selection_score < best_score:
                best_score = selection_score
                best_train_score = train_score
                best_validation_score = validation_score
                best_params = dict(candidate)
        best[method_id] = {
            "params": best_params,
            "score": float(best_score),
            "selection_split": selection_split,
            "train_score": float(best_train_score),
            "validation_score": float(best_validation_score) if validation_seeds else None,
        }

    payload = {
        "experiment_id": experiment_id,
        "config_path": str(config_path),
        "seed_start": seeds[0] if seeds else None,
        "seed_count": len(seeds),
        "validation_seed_start": validation_seeds[0] if validation_seeds else None,
        "validation_seed_count": len(validation_seeds),
        "best_params": best,
    }
    output_artifact.write_text(yaml.safe_dump(payload, sort_keys=True, allow_unicode=False), encoding="utf-8")
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp1") / experiment_id))
    write_csv(output_dir / "tuning_scores.csv", scores, tuning_columns(scores))
    validation_scores = []
    if validation_seeds:
        for method_id, row in best.items():
            score = float(row["validation_score"])
            validation_scores.append({"method": method_id, "selection_split": row["selection_split"], "validation_score": score, **dict(row["params"])})
        write_csv(output_dir / "validation_scores.csv", validation_scores, tuning_validation_columns(validation_scores))
    manifest = {
        "experiment_id": experiment_id,
        "mode": "tuning",
        "output_artifact": str(output_artifact),
        "seed_count": len(seeds),
        "validation_seed_count": len(validation_seeds),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def run_imitation_training(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    training_id = str(config.get("training_id", config_path.stem))
    output = config.get("output", {})
    checkpoint_dir = ensure_directory(output.get("checkpoint_dir", Path("outputs/trained_models/SP1/imitation_oracle/v1")))
    seeds = _seed_range(config.get("train_seeds", {"start": 0, "count": 25}))
    validation_seeds = _seed_range(config.get("validation_seeds", {"start": 1000, "count": 0}))
    test_seeds = _seed_range(config.get("test_seeds", {"start": 1200, "count": 0}))
    generators = [str(item.get("param_generator", item.get("generator", "monte_carlo"))) for item in config.get("scenarios", [{"param_generator": "monte_carlo"}])]
    contexts = []
    for _generator, _variant_id, _seed, params, world in iter_sp1_worlds(generators, seeds):
        contexts.append(DecisionContext(world=world, metadata={"communication_radius": params.communication_radius}))
    model = fit_imitation_model(contexts, CentralizedCoalitionOracleAllocator())
    model.update(
        {
            "training_id": training_id,
            "config_path": str(config_path),
            "train_seed_count": len(seeds),
            "validation_seed_count": len(validation_seeds),
            "test_seed_count": len(test_seeds),
            "trainable_parameters": len(model.get("weights", [])) + 1,
            "training_type": "supervised_oracle_imitation",
        }
    )
    model_path = checkpoint_dir / "model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    split_metrics: dict[str, dict[str, Any]] = {}
    validation_rows = []
    if validation_seeds:
        allocator = make_sp1_allocator("imitation_oracle", {"checkpoint": model_path})
        validation_rows = validate_data_driven_allocator(
            allocator,
            training_id=training_id,
            generators=generators,
            seeds=validation_seeds,
        )
        write_csv(checkpoint_dir / "validation_runs.csv", validation_rows, run_columns(validation_rows))
        validation_summary = data_driven_metric_summary(training_id, "validation", validation_rows, len(validation_seeds))
        save_json(checkpoint_dir / "validation_metrics.json", validation_summary)
        model["validation"] = validation_summary
        split_metrics["validation"] = validation_summary
    test_rows: list[dict[str, Any]] = []
    if test_seeds:
        allocator = make_sp1_allocator("imitation_oracle", {"checkpoint": model_path})
        test_rows = validate_data_driven_allocator(
            allocator,
            training_id=training_id,
            generators=generators,
            seeds=test_seeds,
        )
        write_csv(checkpoint_dir / "test_runs.csv", test_rows, run_columns(test_rows))
        test_summary = data_driven_metric_summary(training_id, "test", test_rows, len(test_seeds))
        save_json(checkpoint_dir / "test_metrics.json", test_summary)
        model["test"] = test_summary
        split_metrics["test"] = test_summary
    quality_gates = evaluate_data_driven_quality_gates(split_metrics, dict(config.get("quality_gates", {})))
    if quality_gates:
        save_json(checkpoint_dir / "quality_gates.json", {"checks": quality_gates, "passed": all(row["passed"] for row in quality_gates)})
        model["quality_gates"] = quality_gates
        failed_gates = [row for row in quality_gates if not bool(row["passed"])]
        if failed_gates:
            names = ", ".join(f"{row['split']}.{row['metric']}" for row in failed_gates)
            raise ValueError(f"Imitation quality gates failed: {names}")
    if split_metrics:
        model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = checkpoint_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                f"# {training_id}",
                "",
                "Frozen linear SP1 data-driven policy trained by oracle imitation.",
                f"- Train seeds: {seeds[0]}-{seeds[-1]} (`n={len(seeds)}`)",
                f"- Validation seeds: {validation_seeds[0]}-{validation_seeds[-1]} (`n={len(validation_seeds)}`)" if validation_seeds else "- Validation seeds: not configured",
                f"- Test seeds: {test_seeds[0]}-{test_seeds[-1]} (`n={len(test_seeds)}`)" if test_seeds else "- Test seeds: not configured",
                f"- Model: `{model_path.name}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "training_id": training_id,
        "mode": "train_imitation",
        "checkpoint": str(model_path),
        "train_seed_count": len(seeds),
        "validation_seed_count": len(validation_seeds),
        "test_seed_count": len(test_seeds),
    }


def write_mappo_stub(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    training_id = str(config.get("training_id", config_path.stem))
    checkpoint_dir = ensure_directory(config.get("output", {}).get("checkpoint_dir", "outputs/trained_models/SP1/mappo_recruitment/v1"))
    stub = {
        "training_id": training_id,
        "config_path": str(config_path),
        "status": "stub",
        "reason": "MAPPO is declared as an optional future data-driven baseline; no heavy RL dependency is required for SP1 smoke runs.",
    }
    save_json(checkpoint_dir / "stub.json", stub)
    return {"training_id": training_id, "mode": "train_mappo_stub", "checkpoint": str(checkpoint_dir / "stub.json")}


def validate_data_driven_allocator(
    allocator: Any,
    *,
    training_id: str,
    generators: list[str],
    seeds: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator, variant_id, seed, params, world in iter_sp1_worlds(generators, seeds):
        context = DecisionContext(world=world, metadata={"communication_radius": params.communication_radius})
        oracle_assignment, _ = timed_allocate(CentralizedCoalitionOracleAllocator(), context)
        assignment, runtime_ms = timed_allocate(allocator, context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=params.communication_radius,
        )
        rows.append(
            {
                "training_id": training_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                **metrics.to_dict(),
            }
        )
    return rows


def data_driven_metric_summary(
    training_id: str,
    split: str,
    rows: list[dict[str, Any]],
    seed_count: int,
) -> dict[str, Any]:
    return {
        "training_id": training_id,
        "split": split,
        f"{split}_seed_count": seed_count,
        f"{split}_runs": len(rows),
        "demand_satisfaction_ratio_mean": _mean_metric(rows, "demand_satisfaction_ratio"),
        "coalition_success_rate_mean": _mean_metric(rows, "coalition_success_rate"),
        "robots_underassigned_mean": _mean_metric(rows, "robots_underassigned"),
        "robots_overassigned_mean": _mean_metric(rows, "robots_overassigned"),
        "captured_reward_mean": _mean_metric(rows, "captured_reward"),
        "optimality_gap_vs_oracle_mean": _mean_metric(rows, "optimality_gap_vs_oracle"),
        "travel_distance_m_mean": _mean_metric(rows, "travel_distance_m"),
        "estimated_arrival_time_s_mean": _mean_metric(rows, "estimated_arrival_time_s"),
        "energy_proxy_wh_mean": _mean_metric(rows, "energy_proxy_wh"),
        "runtime_ms_mean": _mean_metric(rows, "runtime_ms"),
    }


def evaluate_data_driven_quality_gates(
    split_metrics: dict[str, dict[str, Any]],
    gates: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split, split_gates in gates.items():
        metrics = split_metrics.get(str(split))
        if metrics is None:
            continue
        for name, threshold in dict(split_gates or {}).items():
            metric, direction = _parse_quality_gate(str(name))
            value = float(metrics.get(metric, math.nan))
            target = float(threshold)
            passed = value >= target if direction == "min" else value <= target
            rows.append(
                {
                    "split": str(split),
                    "metric": metric,
                    "direction": direction,
                    "value": value,
                    "threshold": target,
                    "passed": bool(passed),
                }
            )
    return rows


def _parse_quality_gate(name: str) -> tuple[str, str]:
    if name.endswith("_min"):
        return name[: -len("_min")], "min"
    if name.endswith("_max"):
        return name[: -len("_max")], "max"
    return name, "min"


METHOD_RESOURCE_COLUMNS = [
    "method_training_type",
    "method_execution_model",
    "method_communication_pattern",
    "method_trainable_parameters",
    "method_training_parameters",
    "method_tuned_parameters",
    "method_training_episodes",
    "method_train_seed_count",
    "method_validation_seed_count",
    "method_test_seed_count",
    "method_uses_neural_policy",
    "method_uses_decoder",
    "method_checkpoint_version",
    "method_rollout_action_mode",
]


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row["scenario_generator"]), str(row["method"]))].append(row)
    metrics = [
        "coalition_success_rate",
        "served_load_rate",
        "demand_satisfaction_ratio",
        "robots_underassigned",
        "robots_overassigned",
        "assignment_cost",
        "travel_distance_m",
        "mean_assigned_travel_distance_m",
        "max_assigned_travel_distance_m",
        "estimated_arrival_time_s",
        "energy_proxy_wh",
        "priority_regret",
        "optimality_gap_vs_oracle",
        "communication_messages",
        "runtime_ms",
    ]
    output = []
    for (scenario, method), group in sorted(groups.items()):
        first = group[0]
        row: dict[str, Any] = {
            "scenario_generator": scenario,
            "method": method,
            "method_label": first.get("method_label", method),
            "method_family": first.get("method_family", "unknown"),
            "method_scope": first.get("method_scope", "unknown"),
            "method_ownership": first.get("method_ownership", "unknown"),
            "method_variant": first.get("method_variant", method),
            "method_comparison_group": first.get("method_comparison_group", "unknown"),
            "n": len(group),
        }
        for column in METHOD_RESOURCE_COLUMNS:
            row[column] = first.get(column, "")
        for metric in metrics:
            values = np.asarray([float(item[metric]) for item in group], dtype=float)
            row[f"{metric}_mean"] = float(np.nanmean(values))
            row[f"{metric}_std"] = float(np.nanstd(values, ddof=1)) if values.size > 1 else 0.0
        output.append(row)
    return output


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank methods by a transparent lexicographic SP1 quality criterion."""

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        method = str(row["method"])
        groups[(str(row["scenario_generator"]), method)].append(row)
        groups[("ALL_SCENARIOS", method)].append(row)
    metrics = [
        "coalition_success_rate",
        "served_load_rate",
        "demand_satisfaction_ratio",
        "robots_underassigned",
        "robots_overassigned",
        "optimality_gap_vs_oracle",
        "travel_distance_m",
        "estimated_arrival_time_s",
        "energy_proxy_wh",
        "communication_messages",
        "runtime_ms",
    ]
    summaries: list[dict[str, Any]] = []
    for (scenario, method), group in sorted(groups.items()):
        first = group[0]
        row: dict[str, Any] = {
            "scenario_generator": scenario,
            "method": method,
            "method_label": first.get("method_label", method),
            "method_family": first.get("method_family", "unknown"),
            "method_scope": first.get("method_scope", "unknown"),
            "method_ownership": first.get("method_ownership", "unknown"),
            "method_variant": first.get("method_variant", method),
            "method_comparison_group": first.get("method_comparison_group", "unknown"),
            "n": len(group),
            "ranking_rule": "min oracle gap, max coalition success, max served loads, max demand, min under/over assignment, min travel/energy/communication/runtime",
        }
        for column in METHOD_RESOURCE_COLUMNS:
            row[column] = first.get(column, "")
        for metric in metrics:
            values = np.asarray([float(item[metric]) for item in group], dtype=float)
            row[f"{metric}_mean"] = float(np.nanmean(values))
        summaries.append(row)

    ranked: list[dict[str, Any]] = []
    scenarios = sorted({str(row["scenario_generator"]) for row in summaries}, key=lambda item: (item != "ALL_SCENARIOS", item))
    for scenario in scenarios:
        scenario_rows = [row for row in summaries if str(row["scenario_generator"]) == scenario]
        ordered = sorted(scenario_rows, key=_performance_rank_key)
        for rank, row in enumerate(ordered, start=1):
            ranked.append({"rank": rank, **row})
    return ranked


def _performance_rank_key(row: dict[str, Any]) -> tuple[float, float, float, float, float, float, float, float, float, float, str]:
    return (
        _finite_or_ceiling(row.get("optimality_gap_vs_oracle_mean")),
        -_finite_or_floor(row.get("coalition_success_rate_mean")),
        -_finite_or_floor(row.get("served_load_rate_mean")),
        -_finite_or_floor(row.get("demand_satisfaction_ratio_mean")),
        _finite_or_ceiling(row.get("robots_underassigned_mean")),
        _finite_or_ceiling(row.get("robots_overassigned_mean")),
        _finite_or_ceiling(row.get("travel_distance_m_mean")),
        _finite_or_ceiling(row.get("energy_proxy_wh_mean")),
        _finite_or_ceiling(row.get("communication_messages_mean")),
        _finite_or_ceiling(row.get("runtime_ms_mean")),
        str(row.get("method", "")),
    )


def _finite_or_floor(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return -math.inf
    return numeric if np.isfinite(numeric) else -math.inf


def _finite_or_ceiling(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return math.inf
    return numeric if np.isfinite(numeric) else math.inf


STRICT_COMPLETE_METHODS = {"centralized_coalition_milp", "mappo_recruitment", "oracle_reference"}


def method_taxonomy_fields(method_id: str) -> dict[str, Any]:
    metadata = sp1_method_metadata(method_id)
    scope = str(metadata["scope"])
    is_oracle = metadata["family"] == "model_based_oracle" or metadata["ownership"] == "reference"
    information_scope = "global" if scope == "centralized" else "local_radius_limited" if "local" in scope else "local"
    method = method_id.lower()
    return {
        "method_family": metadata["family"],
        "method_scope": metadata["scope"],
        "method_ownership": metadata["ownership"],
        "method_variant": metadata["variant"],
        "method_comparison_group": metadata["comparison_group"],
        "method_file_tag": metadata["file_tag"],
        "method_title": metadata["title"],
        "centralized_or_distributed": scope,
        "information_scope": information_scope,
        "oracle_access": bool(is_oracle),
        "decoder": "quorum_decoder" if method == "mappo_recruitment" else "none",
        "repair": "local_repair" if "repair" in method else "none",
        "closure": "quorum_decoder" if method == "mappo_recruitment" else "allocator_internal" if "repair" in method else "none",
    }


def method_resource_fields(method_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return comparable method-resource metadata for fair quality/cost analysis."""

    params = dict(params or {})
    metadata = sp1_method_metadata(method_id)
    checkpoint_metadata = _load_checkpoint_metadata(params.get("checkpoint") or params.get("model_path"))
    trainable_parameters = int(metadata.get("trainable_parameters", 0))
    training_parameters = trainable_parameters
    training_episodes = 0
    training_seed_count = 0
    validation_seed_count = 0
    test_seed_count = 0
    rollout_action_mode = "none"
    checkpoint_version = ""

    if checkpoint_metadata:
        checkpoint_version = str(checkpoint_metadata.get("model_version", ""))
        training_seed_count = int(checkpoint_metadata.get("train_seed_count", 0) or 0)
        validation_seed_count = int(checkpoint_metadata.get("validation_seed_count", 0) or 0)
        test_seed_count = int(checkpoint_metadata.get("test_seed_count", 0) or 0)
        training_episodes = int(checkpoint_metadata.get("total_episodes", 0) or 0)
        rollout_action_mode = str(checkpoint_metadata.get("rollout_action_mode", "supervised_or_static"))
        if method_id == "mappo_recruitment":
            hidden_dim = int(checkpoint_metadata.get("hidden_dim", 64))
            pair_dim = len(checkpoint_metadata.get("pair_feature_names", [])) or 6
            global_dim = len(checkpoint_metadata.get("global_feature_names", [])) or 7
            actor_parameters = _mlp_parameter_count([pair_dim, hidden_dim, hidden_dim, 1]) + 1
            critic_parameters = _mlp_parameter_count([global_dim, hidden_dim, hidden_dim, 1])
            trainable_parameters = actor_parameters
            training_parameters = actor_parameters + critic_parameters
        elif method_id == "imitation_oracle":
            trainable_parameters = len(checkpoint_metadata.get("weights", [])) + 1
            training_parameters = trainable_parameters

    return {
        "method_training_type": metadata.get("training_type", "unknown"),
        "method_execution_model": metadata.get("execution_model", "unknown"),
        "method_communication_pattern": metadata.get("communication_pattern", "unknown"),
        "method_trainable_parameters": trainable_parameters,
        "method_training_parameters": training_parameters,
        "method_tuned_parameters": int(metadata.get("tuned_parameters", 0)),
        "method_training_episodes": training_episodes,
        "method_train_seed_count": training_seed_count,
        "method_validation_seed_count": validation_seed_count,
        "method_test_seed_count": test_seed_count,
        "method_uses_neural_policy": bool(metadata.get("uses_neural_policy", False)),
        "method_uses_decoder": bool(metadata.get("uses_decoder", False)),
        "method_checkpoint_version": checkpoint_version,
        "method_rollout_action_mode": rollout_action_mode,
        "training_required": str(metadata.get("training_type", "none")) not in {"none", "model_based_tuning_optional"},
        "number_of_parameters": trainable_parameters,
        "communication_model": metadata.get("communication_pattern", "unknown"),
    }


def _load_checkpoint_metadata(path_value: Any) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if path.is_dir():
        path = path / "model.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _mlp_parameter_count(layer_sizes: list[int]) -> int:
    return int(sum((left + 1) * right for left, right in zip(layer_sizes[:-1], layer_sizes[1:])))


def save_scenario_videos(
    candidates: list[dict[str, Any]],
    *,
    figures_dir: Path,
    videos_dir: Path,
    video_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Save selected scenario-level SP1 videos."""

    if not candidates:
        return []
    metric = str(video_config.get("selection_metric", "demand_satisfaction_ratio"))
    method_priority = [
        str(method)
        for method in video_config.get(
            "method_priority",
            ["mappo_recruitment", "primal_dual_wrench_market", "centralized_coalition_milp"],
        )
    ]
    modes = _video_selection_modes(video_config)
    fps = int(video_config.get("fps", 12))
    duration_s = float(video_config.get("duration_s", 10.0))
    final_hold_s = float(video_config.get("final_hold_s", 2.0))
    outputs: list[dict[str, Any]] = []
    scenarios = sorted({str(item["row"]["scenario_generator"]) for item in candidates})
    for scenario in scenarios:
        scenario_candidates = [item for item in candidates if str(item["row"]["scenario_generator"]) == scenario]
        for method_candidates in _video_method_groups(scenario_candidates, method_priority, video_config):
            for mode in modes:
                item = _select_video_candidate(method_candidates, metric, mode)
                if item is None:
                    continue
                row = item["row"]
                stem = _video_stem(row, scenario, mode)
                snapshot_path = figures_dir / f"{stem}.png"
                video_path = videos_dir / f"{stem}.mp4"
                title = _video_title(row, scenario, mode)
                save_recruitment_snapshot(item["world"], item["assignment"], snapshot_path, title)
                ok = save_recruitment_video(
                    item["world"],
                    item["assignment"],
                    video_path,
                    title,
                    fps=fps,
                    duration_s=duration_s,
                    final_hold_s=final_hold_s,
                )
                outputs.append(
                    {
                        "scenario_generator": scenario,
                        "selection": mode,
                        "method": row["method"],
                        "method_family": row.get("method_family", "unknown"),
                        "method_scope": row.get("method_scope", "unknown"),
                        "method_ownership": row.get("method_ownership", "unknown"),
                        "method_variant": row.get("method_variant", row["method"]),
                        "method_comparison_group": row.get("method_comparison_group", "unknown"),
                        "seed": int(row["seed"]),
                        "scenario_variant_id": row["scenario_variant_id"],
                        "metric": metric,
                        "metric_value": float(row.get(metric, math.nan)),
                        "snapshot": str(snapshot_path),
                        "video": str(video_path),
                        "ok": bool(ok),
                    }
                )
    return outputs


def _video_method_groups(
    scenario_candidates: list[dict[str, Any]],
    method_priority: list[str],
    video_config: dict[str, Any],
) -> list[list[dict[str, Any]]]:
    if bool(video_config.get("save_per_method", False)):
        allowed = {str(method) for method in video_config.get("methods", [])}
        methods = []
        for item in scenario_candidates:
            method = str(item["row"]["method"])
            if allowed and method not in allowed:
                continue
            if method not in methods:
                methods.append(method)
        return [[item for item in scenario_candidates if str(item["row"]["method"]) == method] for method in methods]

    for method_id in method_priority:
        selected = [item for item in scenario_candidates if str(item["row"]["method"]) == method_id]
        if selected:
            return [selected]
    return [scenario_candidates]


def _video_stem(row: dict[str, Any], scenario: str, mode: str) -> str:
    return "_".join(
        [
            "sp1",
            _safe_slug(scenario),
            _safe_slug(mode),
            _safe_slug(str(row.get("method_ownership", "unknown"))),
            _safe_slug(str(row.get("method_family", "unknown"))),
            _safe_slug(str(row.get("method_scope", "unknown"))),
            _safe_slug(str(row.get("method_variant", row["method"]))),
            _safe_slug(str(row["method"])),
            f"seed{int(row['seed'])}",
        ]
    )


def _video_title(row: dict[str, Any], scenario: str, mode: str) -> str:
    return (
        f"SP1 {scenario} | {mode} | "
        f"{row.get('method_ownership', 'unknown')} / {row.get('method_family', 'unknown')} / "
        f"{row.get('method_scope', 'unknown')} | {row.get('method_label', row['method'])}"
    )


def _safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")


def _video_selection_modes(video_config: dict[str, Any]) -> list[str]:
    modes = []
    if bool(video_config.get("save_best_run", False)):
        modes.append("best")
    if bool(video_config.get("save_median_run", True)):
        modes.append("median")
    if bool(video_config.get("save_worst_run", False)):
        modes.append("worst")
    return modes or ["median"]


def _select_video_candidate(candidates: list[dict[str, Any]], metric: str, mode: str) -> dict[str, Any] | None:
    finite = [item for item in candidates if np.isfinite(float(item["row"].get(metric, math.nan)))]
    if not finite:
        return None
    ordered = sorted(finite, key=lambda item: float(item["row"][metric]))
    if mode == "best":
        return ordered[-1]
    if mode == "worst":
        return ordered[0]
    return ordered[len(ordered) // 2]


def _allocation_theory_check(
    row: dict[str, Any],
    world: Any,
    assignment: Any,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    labels = np.asarray(assignment.labels, dtype=int)
    invalid_label_count = int(np.sum((labels < 0) | (labels > len(world.loads)))) if labels.size else 0
    shape_ok = bool(labels.shape == (len(world.robots),))
    diagnostics = load_diagnostics(world, assignment)
    assigned_under_loads = [
        item for item in diagnostics if int(item["assigned_robots"]) > 0 and str(item["status"]) == "UNDER"
    ]
    strict_method = str(row["method"]) in STRICT_COMPLETE_METHODS
    passed = shape_ok and invalid_label_count == 0 and (not strict_method or not assigned_under_loads)
    return {
        "experiment_id": row["experiment_id"],
        "scenario_generator": row["scenario_generator"],
        "scenario_variant_id": row["scenario_variant_id"],
        "seed": row["seed"],
        "method": row["method"],
        "shape_ok": shape_ok,
        "invalid_label_count": invalid_label_count,
        "assigned_under_loads": len(assigned_under_loads),
        "robots_underassigned": int(metrics["robots_underassigned"]),
        "robots_overassigned": int(metrics["robots_overassigned"]),
        "strict_complete_coalition_method": strict_method,
        "passed": passed,
    }


def summarize_theory_checks(
    theory_rows: list[dict[str, Any]],
    seeds: list[int],
    generators: list[str],
    method_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row["passed"])]
    strict_failed = [
        row
        for row in failed
        if bool(row["strict_complete_coalition_method"])
    ]
    return {
        "seed_start": seeds[0] if seeds else None,
        "seed_end": seeds[-1] if seeds else None,
        "seed_count": len(seeds),
        "scenario_generators": generators,
        "method_count": len(method_specs),
        "checks": len(theory_rows),
        "failed_checks": len(failed),
        "strict_complete_coalition_failures": len(strict_failed),
        "passed": len(failed) == 0,
    }


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for spec in hypotheses or []:
        cls = str(spec.get("class", ""))
        try:
            if cls == "MultiMethodFriedmanHypothesis":
                output.append(_evaluate_friedman_hypothesis(rows, spec))
            elif cls == "PairedSuperiorityHypothesis":
                output.append(_evaluate_paired_superiority(rows, spec))
            elif cls == "NonInferiorityHypothesis":
                output.append(_evaluate_noninferiority(rows, spec))
            else:
                output.append(_hypothesis_error(spec, f"Unknown hypothesis class: {cls}"))
        except Exception as exc:  # pragma: no cover - defensive reporting path
            output.append(_hypothesis_error(spec, str(exc)))
    return apply_holm_correction(output)


def _evaluate_friedman_hypothesis(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    metric = str(spec["metric"])
    methods = [str(method) for method in spec["methods"]]
    alpha = float(spec.get("alpha", 0.05))
    matrix = _paired_metric_matrix(rows, methods, metric, spec.get("paired_by", []))
    if matrix.shape[0] < 2 or matrix.shape[1] < 3:
        return _hypothesis_error(spec, "Friedman test needs at least 2 paired blocks and 3 methods.")
    statistic, p_value = stats.friedmanchisquare(*[matrix[:, idx] for idx in range(matrix.shape[1])])
    p_value = float(p_value) if np.isfinite(float(p_value)) else 1.0
    kendall_w = float(statistic / (matrix.shape[0] * (matrix.shape[1] - 1)))
    return {
        "id": spec.get("id", ""),
        "class": spec.get("class", ""),
        "metric": metric,
        "n_pairs": int(matrix.shape[0]),
        "methods": " ".join(methods),
        "statistic": float(statistic),
        "test": "friedman_chi_square",
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
        "message": "",
    }


def _evaluate_paired_superiority(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    metric = str(spec["metric"])
    treatment = str(spec["treatment"])
    control = str(spec["control"])
    alpha = float(spec.get("alpha", 0.05))
    alternative = str(spec.get("alternative", "two-sided"))
    matrix = _paired_metric_matrix(rows, [treatment, control], metric, spec.get("paired_by", []))
    if matrix.shape[0] < 2:
        return _hypothesis_error(spec, "Paired superiority test needs at least 2 paired blocks.")
    diff = matrix[:, 0] - matrix[:, 1]
    try:
        statistic, p_value = stats.wilcoxon(matrix[:, 0], matrix[:, 1], alternative=alternative)
    except ValueError:
        statistic, p_value = 0.0, 1.0
    p_value = wilcoxon_signed_rank_pvalue(diff, alternative=alternative)
    inference = mean_difference_inference(diff)
    return {
        "id": spec.get("id", ""),
        "class": spec.get("class", ""),
        "metric": metric,
        "n_pairs": int(matrix.shape[0]),
        "methods": f"{treatment} {control}",
        "test": "wilcoxon_signed_rank",
        "statistic": float(statistic),
        "p_value": float(p_value),
        **inference,
        "alpha": alpha,
        "reject": bool(float(p_value) < alpha),
        "status": "ok",
        "message": "",
    }


def _evaluate_noninferiority(rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
    metric = str(spec["metric"])
    treatment = str(spec["treatment"])
    control = str(spec["control"])
    alpha = float(spec.get("alpha", 0.05))
    threshold = float(spec.get("ratio_threshold", 0.9))
    matrix = _paired_metric_matrix(rows, [treatment, control], metric, spec.get("paired_by", []))
    if matrix.shape[0] < 2:
        return _hypothesis_error(spec, "Non-inferiority test needs at least 2 paired blocks.")
    ratios = matrix[:, 0] / np.maximum(matrix[:, 1], 1.0e-9)
    margins = ratios - threshold
    statistic, p_value = stats.ttest_1samp(margins, 0.0, alternative="greater")
    p_value = float(p_value) if np.isfinite(float(p_value)) else 1.0
    inference = mean_value_inference(ratios, effect_name=f"mean_ratio_vs_threshold_{threshold:g}")
    inference["effect_size"] = float(mean_difference_inference(margins)["effect_size"])
    inference["effect_size_name"] = "cohens_dz_margin"
    return {
        "id": spec.get("id", ""),
        "class": spec.get("class", ""),
        "metric": metric,
        "n_pairs": int(matrix.shape[0]),
        "methods": f"{treatment} {control}",
        "statistic": float(statistic),
        "test": "one_sample_t_test_noninferiority",
        "p_value": p_value,
        **inference,
        "alpha": alpha,
        "reject": bool(float(p_value) < alpha),
        "status": "ok",
        "message": "",
    }


def _paired_metric_matrix(
    rows: list[dict[str, Any]],
    methods: list[str],
    metric: str,
    paired_by: list[str],
) -> np.ndarray:
    keys = [str(key) for key in paired_by] or ["scenario_generator", "scenario_variant_id", "seed"]
    groups: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in rows:
        method = str(row["method"])
        if method not in methods:
            continue
        key = tuple(row[item] for item in keys)
        groups[key][method] = float(row[metric])
    values = []
    for key in sorted(groups):
        group = groups[key]
        if all(method in group for method in methods):
            values.append([group[method] for method in methods])
    return np.asarray(values, dtype=float)


def _hypothesis_error(spec: dict[str, Any], message: str) -> dict[str, Any]:
    return {
        "id": spec.get("id", ""),
        "class": spec.get("class", ""),
        "metric": spec.get("metric", ""),
        "n_pairs": 0,
        "methods": " ".join(str(item) for item in spec.get("methods", [])),
        "statistic": math.nan,
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
        "status": "error",
        "message": message,
    }


def write_report(
    path: Path,
    experiment_id: str,
    seeds: list[int],
    generators: list[str],
    summary_rows: list[dict[str, Any]],
    *,
    ranking_rows: list[dict[str, Any]] | None = None,
    hypothesis_rows: list[dict[str, Any]] | None = None,
    theory_audit: dict[str, Any] | None = None,
    scenario_videos: list[dict[str, Any]] | None = None,
) -> None:
    best = max(summary_rows, key=lambda row: (row["demand_satisfaction_ratio_mean"], -row["optimality_gap_vs_oracle_mean"]))
    lines = [
        f"# {experiment_id}",
        "",
        "SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.",
        f"- Seeds: `{seeds[0]}`-`{seeds[-1]}` (`n={len(seeds)}`)",
        f"- Scenario generators: `{', '.join(generators)}`",
        "- Tuning/training must use disjoint seeds from this Monte Carlo config.",
        "",
        "## Method Taxonomy",
        "",
        "| Method | Label | Family | Scope | Ownership | Variant | Comparison group |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in unique_method_rows(summary_rows):
        lines.append(
            "| {method} | {label} | {family} | {scope} | {ownership} | {variant} | {group} |".format(
                method=row["method"],
                label=row.get("method_label", row["method"]),
                family=row.get("method_family", "unknown"),
                scope=row.get("method_scope", "unknown"),
                ownership=row.get("method_ownership", "unknown"),
                variant=row.get("method_variant", row["method"]),
                group=row.get("method_comparison_group", "unknown"),
            )
        )
    lines.extend(
        [
            "",
            "## Resource Fairness",
            "",
            "Interpret neural/data-driven methods as quality-resource tradeoffs, not as free replacements for compact distributed rules.",
            "",
            "| Method | Training type | Execution model | Trainable params | Tuned params | Train episodes | Train seeds | Decoder |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in unique_method_rows(summary_rows):
        lines.append(
            "| {method} | {training} | {execution} | {params} | {tuned} | {episodes} | {seeds} | {decoder} |".format(
                method=row["method"],
                training=row.get("method_training_type", "unknown"),
                execution=row.get("method_execution_model", "unknown"),
                params=int(float(row.get("method_trainable_parameters", 0) or 0)),
                tuned=int(float(row.get("method_tuned_parameters", 0) or 0)),
                episodes=int(float(row.get("method_training_episodes", 0) or 0)),
                seeds=int(float(row.get("method_train_seed_count", 0) or 0)),
                decoder=row.get("method_uses_decoder", False),
            )
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
        "| Scenario | Method | Family | Scope | Owner | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Travel m | Energy Wh | Runtime ms |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {scenario} | {method} | {family} | {scope} | {owner} | {n} | {success:.3f} | {demand:.3f} | {under:.3f} | {over:.3f} | {gap:.3f} | {travel:.2f} | {energy:.2f} | {runtime:.3f} |".format(
                scenario=row["scenario_generator"],
                method=row["method"],
                family=row.get("method_family", "unknown"),
                scope=row.get("method_scope", "unknown"),
                owner=row.get("method_ownership", "unknown"),
                n=row["n"],
                success=row["coalition_success_rate_mean"],
                demand=row["demand_satisfaction_ratio_mean"],
                under=row["robots_underassigned_mean"],
                over=row["robots_overassigned_mean"],
                gap=row["optimality_gap_vs_oracle_mean"],
                travel=row.get("travel_distance_m_mean", row.get("assignment_cost_mean", math.nan)),
                energy=row.get("energy_proxy_wh_mean", math.nan),
                runtime=row["runtime_ms_mean"],
            )
        )
    lines.extend(
        [
            "",
            f"Best raw mean demand satisfaction: **{best['method']}** on `{best['scenario_generator']}`.",
            "",
        ]
    )
    if ranking_rows:
        overall_best = next(
            (
                row
                for row in ranking_rows
                if str(row["scenario_generator"]) == "ALL_SCENARIOS" and int(row["rank"]) == 1
            ),
            None,
        )
        lines.extend(
            [
                "## Performance Ranking",
                "",
                "Ranking rule: minimize gap vs oracle; then maximize coalition success, served-load rate, and demand satisfaction; then minimize under/over assignment, travel, energy, communication, and runtime.",
                "",
            ]
        )
        if overall_best:
            lines.extend(
                [
                    f"Theory-aligned best overall: **{overall_best['method']}** (`{overall_best.get('method_ownership', 'unknown')}`).",
                    "",
                ]
            )
        lines.extend(
            [
                "| Scope | Rank | Method | Family | Ownership | Demand | Success | Gap vs oracle | Travel m | Params | Runtime ms |",
                "|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        top_rows = [
            row
            for row in ranking_rows
            if str(row["scenario_generator"]) == "ALL_SCENARIOS" and int(row["rank"]) <= 8
        ]
        if not top_rows:
            top_rows = [row for row in ranking_rows if int(row["rank"]) <= 3][:8]
        for row in top_rows:
            lines.append(
                "| {scope} | {rank} | {method} | {family} | {owner} | {demand:.3f} | {success:.3f} | {gap:.3f} | {travel:.2f} | {params} | {runtime:.3f} |".format(
                    scope=row["scenario_generator"],
                    rank=int(row["rank"]),
                    method=row["method"],
                    family=row.get("method_family", "unknown"),
                    owner=row.get("method_ownership", "unknown"),
                    demand=row["demand_satisfaction_ratio_mean"],
                    success=row["coalition_success_rate_mean"],
                    gap=row["optimality_gap_vs_oracle_mean"],
                    travel=row.get("travel_distance_m_mean", math.nan),
                    params=int(float(row.get("method_trainable_parameters", 0) or 0)),
                    runtime=row["runtime_ms_mean"],
                )
            )
        lines.append("")
    if theory_audit:
        lines.extend(
            [
                "## Theory Audit",
                "",
                f"- Checks: `{theory_audit['checks']}`.",
                f"- Failed checks: `{theory_audit['failed_checks']}`.",
                f"- Strict complete-coalition failures: `{theory_audit['strict_complete_coalition_failures']}`.",
                f"- Passed: `{theory_audit['passed']}`.",
                "",
            ]
        )
    if hypothesis_rows:
        lines.extend(
            [
                "## Hypotheses",
                "",
                "| ID | Metric | n | p raw | p Holm | Effect | CI95 | Reject Holm | Status |",
                "|---|---|---:|---:|---:|---:|---|---|---|",
            ]
        )
        for row in hypothesis_rows:
            ci_low = float(row.get("ci95_low", math.nan))
            ci_high = float(row.get("ci95_high", math.nan))
            ci = f"[{ci_low:.4g}, {ci_high:.4g}]" if np.isfinite(ci_low) and np.isfinite(ci_high) else ""
            lines.append(
                "| {id} | {metric} | {n} | {p:.4g} | {p_holm:.4g} | {effect:.4g} | {ci} | {reject} | {status} |".format(
                    id=row["id"],
                    metric=row["metric"],
                    n=row["n_pairs"],
                    p=float(row["p_value"]) if np.isfinite(float(row["p_value"])) else math.nan,
                    p_holm=float(row.get("p_value_holm", math.nan)) if np.isfinite(float(row.get("p_value_holm", math.nan))) else math.nan,
                    effect=float(row["effect"]) if np.isfinite(float(row["effect"])) else math.nan,
                    ci=ci,
                    reject=row.get("reject_holm", row["reject"]),
                    status=row["status"],
                )
            )
        lines.append("")
    if scenario_videos:
        lines.extend(["## Scenario Videos", ""])
        for item in scenario_videos:
            lines.append(
                "- `{scenario}` `{selection}` `{ownership}/{family}/{scope}` `{method}` seed `{seed}`: `{video}`".format(
                    scenario=item["scenario_generator"],
                    selection=item["selection"],
                    ownership=item.get("method_ownership", "unknown"),
                    family=item.get("method_family", "unknown"),
                    scope=item.get("method_scope", "unknown"),
                    method=item["method"],
                    seed=item["seed"],
                    video=Path(item["video"]).name,
                )
            )
        lines.append("")
    lines.extend(
        [
            "## Artifacts",
            "",
            "- `tables/runs.csv`",
            "- `tables/summary.csv`",
            "- `tables/performance_ranking.csv`",
            "- `tables/load_status.csv`",
            "- `tables/theory_checks.csv`",
            "- `tables/hypothesis_results.csv`",
            "- `theory_audit.json`",
            "- `figures/sp1_demand_satisfaction_by_method.png`",
            "- `figures/sp1_demand_ratio_interaction.png`",
            "- `figures/sp1_performance_matrix_by_method.png`",
            "- `figures/sp1_taxonomy_scope_family_ownership.png`",
            "- `figures/sp1_ours_vs_baselines_vs_reference.png`",
            "- `figures/sp1_reference_gap_proposed_methods.png`",
            "- `figures/sp1_communication_radius_degradation.png`",
            "- `figures/sp1_best_method_by_scenario.png`",
            "- `figures/sp1_quality_resource_pareto.png`",
            "- `figures/sp1_physical_cost_tradeoff.png`",
            "- `figures/sp1_<scenario>_<selection>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.png`",
            "- `videos/sp1_<scenario>_<selection>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def unique_method_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, dict[str, Any]] = {}
    for row in summary_rows:
        by_method.setdefault(str(row["method"]), row)
    return sorted(
        by_method.values(),
        key=lambda row: (
            str(row.get("method_ownership", "")),
            str(row.get("method_family", "")),
            str(row.get("method_scope", "")),
            str(row["method"]),
        ),
    )


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _score_candidate(method_id: str, params: dict[str, Any], generators: list[str], seeds: list[int]) -> float:
    penalties = []
    for _generator, _variant_id, _seed, scenario_params, world in iter_sp1_worlds(generators, seeds):
        context = DecisionContext(world=world, metadata={"communication_radius": scenario_params.communication_radius})
        oracle = CentralizedCoalitionOracleAllocator()
        oracle_assignment, _ = timed_allocate(oracle, context)
        allocator = make_sp1_allocator(method_id, params)
        assignment, runtime_ms = timed_allocate(allocator, context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            communication_radius=scenario_params.communication_radius,
        )
        penalties.append(
            (1.0 - metrics.coalition_success_rate)
            + 0.15 * metrics.robots_underassigned
            + 0.08 * metrics.robots_overassigned
            + metrics.optimality_gap_vs_oracle
            + 0.0002 * metrics.communication_messages
        )
    return float(np.mean(penalties)) if penalties else math.inf


def _seed_range(config: Any) -> list[int]:
    if isinstance(config, list):
        return [int(seed) for seed in config]
    start = int(config.get("start", 0))
    count = int(config.get("count", 1))
    return list(range(start, start + count))


def _method_specs(items: list[Any]) -> list[dict[str, Any]]:
    if not items:
        items = [
            {"id": "greedy_nearest"},
            {"id": "hungarian_expanded"},
            {"id": "centralized_coalition_milp"},
            {"id": "replicator_cardinality"},
            {"id": "smith_cardinality"},
            {"id": "primal_dual_cardinality_capacity"},
            {"id": "primal_dual_wrench_market"},
        ]
    specs = []
    for item in items:
        if isinstance(item, str):
            specs.append({"id": item})
        else:
            specs.append(dict(item))
    return specs


def _load_tuned_params(method_specs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for spec in method_specs:
        artifact = spec.get("tuning_artifact")
        if not artifact:
            continue
        path = Path(artifact)
        if not path.exists():
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        best = payload.get("best_params", {})
        method_id = str(spec["id"])
        if method_id in best:
            loaded[method_id] = dict(best[method_id].get("params", {}))
    return loaded


def _should_skip_optional(method_spec: dict[str, Any]) -> bool:
    if not bool(method_spec.get("optional", False)):
        return False
    checkpoint = method_spec.get("checkpoint") or method_spec.get("params", {}).get("checkpoint")
    return checkpoint is not None and not Path(checkpoint).exists()


def _expand_grid(config: Any) -> list[dict[str, Any]]:
    if isinstance(config, list):
        return [dict(item) for item in config]
    if isinstance(config, dict) and "default" in config:
        return [dict(item) for item in config["default"]]
    if not isinstance(config, dict):
        return [{}]
    keys = list(config)
    values = [value if isinstance(value, list) else [value] for value in config.values()]
    rows = [{}]
    for key, options in zip(keys, values):
        rows = [dict(row, **{key: option}) for row in rows for option in options]
    return rows


def run_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "experiment_id",
        "scenario_generator",
        "scenario_variant_id",
        "seed",
        "method",
        "method_label",
        "method_family",
        "method_scope",
        "method_ownership",
        "method_variant",
        "method_comparison_group",
        *METHOD_RESOURCE_COLUMNS,
        "n_robots",
        "n_loads",
        "demand_ratio",
        "rho",
        "heterogeneous_robots",
        "communication_radius",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "scenario_generator",
        "method",
        "method_label",
        "method_family",
        "method_scope",
        "method_ownership",
        "method_variant",
        "method_comparison_group",
        *METHOD_RESOURCE_COLUMNS,
        "n",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def performance_ranking_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "scenario_generator",
        "rank",
        "method",
        "method_label",
        "method_family",
        "method_scope",
        "method_ownership",
        "method_variant",
        "method_comparison_group",
        *METHOD_RESOURCE_COLUMNS,
        "n",
        "ranking_rule",
        "demand_satisfaction_ratio_mean",
        "coalition_success_rate_mean",
        "served_load_rate_mean",
        "optimality_gap_vs_oracle_mean",
        "robots_underassigned_mean",
        "robots_overassigned_mean",
        "travel_distance_m_mean",
        "estimated_arrival_time_s_mean",
        "energy_proxy_wh_mean",
        "communication_messages_mean",
        "runtime_ms_mean",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def load_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "experiment_id",
        "scenario_generator",
        "scenario_variant_id",
        "seed",
        "method",
        "method_family",
        "method_scope",
        "method_ownership",
        "method_variant",
        "load_id",
        "status",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def theory_check_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "experiment_id",
        "scenario_generator",
        "scenario_variant_id",
        "seed",
        "method",
        "passed",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def hypothesis_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "id",
        "class",
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
        "message",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def tuning_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["method", "selection_split", "selection_score", "train_score", "validation_score"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def tuning_validation_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["method", "selection_split", "validation_score"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([float(row[metric]) for row in rows], dtype=float)
    return float(np.nanmean(values)) if values.size else math.nan
