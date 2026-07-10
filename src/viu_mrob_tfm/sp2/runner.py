"""Executable SP2 effective-capacity Monte Carlo pipeline."""

from __future__ import annotations

import csv
import json
import math
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
    wilcoxon_signed_rank_pvalue,
)
from viu_mrob_tfm.sp2.methods import (
    CentralizedCapacityMILPAllocator,
    CentralizedCapacityCoverageMILPAllocator,
    SP2_METHOD_LABELS,
    fit_imitation_model,
    fit_neural_imitation_model,
    make_sp2_allocator,
    sp2_potential_alignment,
    sp2_method_metadata,
)
from viu_mrob_tfm.sp2.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp2.scenario import iter_sp2_worlds
from viu_mrob_tfm.sp2.visualization import (
    plot_best_method_by_scenario,
    plot_capacity_coverage_vs_completion,
    plot_capacity_cost_tradeoff,
    plot_capacity_regime_interaction,
    plot_communication_degradation,
    plot_method_performance_matrix,
    plot_quality_resource_pareto,
    plot_summary_bars,
    save_capacity_snapshot,
    save_capacity_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


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
    "method_tuning_type",
    "method_tuning_seed_count",
    "method_tuning_validation_seed_count",
    "method_tuning_artifact",
    "method_uses_neural_policy",
    "method_uses_decoder",
    "method_checkpoint_version",
    "method_rollout_action_mode",
]


def run_sp2_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"monte_carlo", "mc", "debug"}:
        return run_monte_carlo(config, config_path=config_path)
    if mode in {"train_imitation", "imitation"}:
        return run_imitation_training(config, config_path=config_path)
    if mode in {"tune_model_based", "model_based_tuning", "tuning"}:
        return run_model_based_tuning(config, config_path=config_path)
    raise ValueError(f"Unknown SP2 config mode: {mode}")


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp2") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")

    seeds = _seed_range(config.get("seeds", {"start": 3100, "count": 5}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    method_specs = _apply_tuned_params(_method_specs(config.get("methods", [])), config)
    rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []

    for generator, variant_id, seed, params, world in iter_sp2_worlds(generators, seeds):
        context = DecisionContext(
            world=world,
            metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m},
        )
        oracle = CentralizedCapacityMILPAllocator()
        oracle_assignment, oracle_runtime_ms = timed_allocate(oracle, context)
        capacity_oracle = CentralizedCapacityCoverageMILPAllocator()
        capacity_oracle_assignment, capacity_oracle_runtime_ms = timed_allocate(capacity_oracle, context)
        oracle_metrics = evaluate_assignment(
            world,
            oracle_assignment,
            runtime_ms=oracle_runtime_ms,
            oracle_assignment=oracle_assignment,
            capacity_oracle_assignment=capacity_oracle_assignment,
            communication_radius=params.communication_radius,
            distance_decay_m=params.distance_decay_m,
            centralized=True,
        )
        capacity_oracle_metrics = evaluate_assignment(
            world,
            capacity_oracle_assignment,
            runtime_ms=capacity_oracle_runtime_ms,
            oracle_assignment=oracle_assignment,
            capacity_oracle_assignment=capacity_oracle_assignment,
            communication_radius=params.communication_radius,
            distance_decay_m=params.distance_decay_m,
            centralized=True,
        )

        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            allocator = make_sp2_allocator(method_id, dict(method_spec.get("params", {})))
            centralized = method_id in {"hungarian_capacity", "centralized_capacity_milp"}
            assignment, runtime_ms = timed_allocate(allocator, context)
            metrics = evaluate_assignment(
                world,
                assignment,
                runtime_ms=runtime_ms,
                oracle_assignment=oracle_assignment,
                capacity_oracle_assignment=capacity_oracle_assignment,
                communication_radius=params.communication_radius,
                distance_decay_m=params.distance_decay_m,
                centralized=centralized,
            )
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP2_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id, dict(method_spec.get("params", {}))),
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "capacity_ratio": params.capacity_ratio,
                "robot_payload_mean_kg": params.robot_payload_mean_kg,
                "robot_payload_cv": params.robot_payload_cv,
                "load_mass_cv": params.load_mass_cv,
                "battery_variation": params.battery_variation,
                "communication_radius": params.communication_radius,
                "distance_decay_m": params.distance_decay_m,
                "oracle_runtime_ms": oracle_runtime_ms,
                "capacity_oracle_runtime_ms": capacity_oracle_runtime_ms,
                **metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_theory_check(row, world, assignment, params.communication_radius, params.distance_decay_m))
            video_candidates.append({"world": world, "assignment": assignment, "row": row})
            for load_row in load_diagnostics(world, assignment, communication_radius=params.communication_radius, distance_decay_m=params.distance_decay_m):
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
            "capacity_ratio": params.capacity_ratio,
            "robot_payload_mean_kg": params.robot_payload_mean_kg,
            "robot_payload_cv": params.robot_payload_cv,
            "load_mass_cv": params.load_mass_cv,
            "battery_variation": params.battery_variation,
            "communication_radius": params.communication_radius,
            "distance_decay_m": params.distance_decay_m,
            "oracle_runtime_ms": oracle_runtime_ms,
            "capacity_oracle_runtime_ms": capacity_oracle_runtime_ms,
            **oracle_metrics.to_dict(),
        }
        rows.append(oracle_row)
        theory_rows.append(_theory_check(oracle_row, world, oracle_assignment, params.communication_radius, params.distance_decay_m))
        capacity_oracle_row = {
            "experiment_id": experiment_id,
            "scenario_generator": generator,
            "scenario_variant_id": variant_id,
            "seed": seed,
            "method": "capacity_oracle_reference",
            "method_label": "Pure capacity oracle reference",
            **method_taxonomy_fields("capacity_oracle_reference"),
            **method_resource_fields("capacity_oracle_reference", {}),
            "n_robots": params.n_robots,
            "n_loads": params.n_loads,
            "capacity_ratio": params.capacity_ratio,
            "robot_payload_mean_kg": params.robot_payload_mean_kg,
            "robot_payload_cv": params.robot_payload_cv,
            "load_mass_cv": params.load_mass_cv,
            "battery_variation": params.battery_variation,
            "communication_radius": params.communication_radius,
            "distance_decay_m": params.distance_decay_m,
            "oracle_runtime_ms": oracle_runtime_ms,
            "capacity_oracle_runtime_ms": capacity_oracle_runtime_ms,
            **capacity_oracle_metrics.to_dict(),
        }
        rows.append(capacity_oracle_row)
        theory_rows.append(_theory_check(capacity_oracle_row, world, capacity_oracle_assignment, params.communication_radius, params.distance_decay_m))

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", []))
    theory_audit = summarize_theory_checks(theory_rows, seeds, generators, method_specs)

    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, ranking_columns(ranking_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, load_status_columns(load_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, theory_check_columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, hypothesis_columns(hypothesis_rows))
    save_json(output_dir / "theory_audit.json", theory_audit)

    plot_summary_bars(rows, figures_dir / "sp2_capacity_satisfaction_by_method.png")
    plot_capacity_regime_interaction(rows, figures_dir / "sp2_capacity_ratio_interaction.png")
    plot_method_performance_matrix(rows, figures_dir / "sp2_performance_matrix_by_method.png")
    plot_quality_resource_pareto(rows, figures_dir / "sp2_quality_resource_pareto.png")
    plot_capacity_cost_tradeoff(rows, figures_dir / "sp2_capacity_cost_tradeoff.png")
    plot_capacity_coverage_vs_completion(rows, figures_dir / "sp2_capacity_coverage_vs_completion.png")
    plot_communication_degradation(rows, figures_dir / "sp2_communication_radius_degradation.png")
    plot_best_method_by_scenario(rows, figures_dir / "sp2_best_method_by_scenario.png")

    scenario_videos: list[dict[str, Any]] = []
    artifact_config = dict(config.get("artifacts", {}))
    if bool(artifact_config.get("save_video", True)):
        scenario_videos = save_scenario_videos(video_candidates, figures_dir=figures_dir, videos_dir=videos_dir, video_config=dict(artifact_config.get("video", {})))

    report_path = output_dir / "report.md"
    write_report(
        report_path,
        experiment_id,
        seeds,
        generators,
        summary_rows,
        ranking_rows,
        hypothesis_rows,
        theory_audit,
        scenario_videos,
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
        "performance_ranking": str(tables_dir / "performance_ranking.csv"),
        "hypotheses": len(hypothesis_rows),
        "theory_audit": str(output_dir / "theory_audit.json"),
        "scenario_videos": scenario_videos,
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def run_imitation_training(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    training_id = str(config.get("training_id", config_path.stem))
    training_config = dict(config.get("training", {}))
    model_type = str(training_config.get("model_type", "linear")).lower()
    output_artifact = Path(training_config.get("output_artifact", "outputs/trained_models/SP2/imitation_capacity/v1/model.json"))
    checkpoint_dir = ensure_directory(training_config.get("output_dir", output_artifact.parent))
    linear_artifact = Path(training_config.get("linear_artifact", output_artifact if model_type in {"linear", "imitation"} else checkpoint_dir / "model.json"))
    neural_artifact = Path(training_config.get("neural_artifact", checkpoint_dir / "neural_model.json"))
    ensure_directory(linear_artifact.parent)
    ensure_directory(neural_artifact.parent)
    seeds = _seed_range(config.get("train_seeds", config.get("seeds", {"start": 1200, "count": 20})))
    validation_seeds = _seed_range(config.get("validation_seeds", {"start": 2200, "count": 0}))
    test_seeds = _seed_range(config.get("test_seeds", {"start": 3200, "count": 0}))
    generators = [str(item.get("param_generator", item.get("generator", "balanced_capacity"))) for item in config.get("scenarios", [{"param_generator": "balanced_capacity"}])]
    contexts = []
    for _generator, _variant, _seed, params, world in iter_sp2_worlds(generators, seeds):
        contexts.append(DecisionContext(world=world, metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m}))
    requested_models = ["imitation_capacity", "neural_capacity_scorer"] if model_type in {"both", "all", "data_driven"} else ["neural_capacity_scorer"] if model_type in {"neural", "mlp"} else ["imitation_capacity"]
    checkpoints: dict[str, str] = {}
    split_summaries: dict[str, dict[str, dict[str, Any]]] = {}
    oracle = CentralizedCapacityMILPAllocator()

    for method_id in requested_models:
        if method_id == "neural_capacity_scorer":
            model = fit_neural_imitation_model(
                contexts,
                oracle,
                hidden_dim=int(training_config.get("neural_hidden_dim", 8)),
                epochs=int(training_config.get("neural_epochs", training_config.get("training_episodes", 180))),
                learning_rate=float(training_config.get("neural_learning_rate", 0.015)),
                random_seed=int(training_config.get("random_seed", 2026)),
            )
            model_path = neural_artifact
            training_parameters = int(np.asarray(model["w1"]).size + np.asarray(model["b1"]).size + np.asarray(model["w2"]).size + 1)
        else:
            model = fit_imitation_model(contexts, oracle)
            model_path = linear_artifact
            training_parameters = len(model.get("weights", []))
        model.update(
            {
                "training_id": training_id,
                "config_path": str(config_path),
                "method": method_id,
                "train_seed_count": len(seeds),
                "validation_seed_count": len(validation_seeds),
                "test_seed_count": len(test_seeds),
                "train_context_count": len(contexts),
                "trainable_parameters": int(training_parameters),
                "training_parameters": int(training_parameters),
                "training_type": "supervised_oracle_imitation",
                "rollout_action_mode": "greedy_capacity_score_decode",
            }
        )
        model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checkpoints[method_id] = str(model_path)
        split_summaries[method_id] = {}
        if validation_seeds:
            allocator = make_sp2_allocator(method_id, {"checkpoint": model_path})
            validation_rows = validate_data_driven_allocator(
                allocator,
                training_id=training_id,
                method_id=method_id,
                generators=generators,
                seeds=validation_seeds,
            )
            validation_prefix = "validation" if method_id == "imitation_capacity" else f"{method_id}_validation"
            write_csv(checkpoint_dir / f"{validation_prefix}_runs.csv", validation_rows, run_columns(validation_rows))
            validation_summary = data_driven_metric_summary(training_id, "validation", validation_rows, len(validation_seeds), method_id=method_id)
            save_json(checkpoint_dir / f"{validation_prefix}_metrics.json", validation_summary)
            model["validation"] = validation_summary
            split_summaries[method_id]["validation"] = validation_summary
        if test_seeds:
            allocator = make_sp2_allocator(method_id, {"checkpoint": model_path})
            test_rows = validate_data_driven_allocator(
                allocator,
                training_id=training_id,
                method_id=method_id,
                generators=generators,
                seeds=test_seeds,
            )
            test_prefix = "test" if method_id == "imitation_capacity" else f"{method_id}_test"
            write_csv(checkpoint_dir / f"{test_prefix}_runs.csv", test_rows, run_columns(test_rows))
            test_summary = data_driven_metric_summary(training_id, "test", test_rows, len(test_seeds), method_id=method_id)
            save_json(checkpoint_dir / f"{test_prefix}_metrics.json", test_summary)
            model["test"] = test_summary
            split_summaries[method_id]["test"] = test_summary
        if split_summaries[method_id]:
            model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    quality_gates = evaluate_data_driven_quality_gates(split_summaries, dict(config.get("quality_gates", {})))
    if quality_gates:
        save_json(checkpoint_dir / "quality_gates.json", {"checks": quality_gates, "passed": all(row["passed"] for row in quality_gates)})
        failed_gates = [row for row in quality_gates if not bool(row["passed"])]
        if failed_gates:
            names = ", ".join(f"{row['method']}.{row['split']}.{row['metric']}" for row in failed_gates)
            raise ValueError(f"SP2 data-driven quality gates failed: {names}")
    (checkpoint_dir / "README.md").write_text(
        "\n".join(
            [
                f"# {training_id}",
                "",
                "SP2 capacity-aware data-driven policies trained by centralized capacity-oracle imitation.",
                f"- Train seeds: {seeds[0]}-{seeds[-1]} (`n={len(seeds)}`)",
                f"- Validation seeds: {validation_seeds[0]}-{validation_seeds[-1]} (`n={len(validation_seeds)}`)" if validation_seeds else "- Validation seeds: not configured",
                f"- Test seeds: {test_seeds[0]}-{test_seeds[-1]} (`n={len(test_seeds)}`)" if test_seeds else "- Test seeds: not configured",
                f"- Methods: `{', '.join(requested_models)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "training_id": training_id,
        "mode": "train_imitation",
        "config_path": str(config_path),
        "checkpoint_dir": str(checkpoint_dir),
        "checkpoints": checkpoints,
        "train_contexts": len(contexts),
        "train_seed_count": len(seeds),
        "validation_seed_count": len(validation_seeds),
        "test_seed_count": len(test_seeds),
        "models": requested_models,
    }
    save_json(checkpoint_dir / "manifest.json", manifest)
    return manifest


def run_model_based_tuning(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp2") / experiment_id))
    tuning_config = dict(config.get("tuning", {}))
    output_artifact = Path(tuning_config.get("output_artifact", "outputs/tuning/SP2/model_based/best_params.yaml"))
    ensure_directory(output_artifact.parent)
    seeds = _seed_range(config.get("seeds", {"start": 1300, "count": 8}))
    validation_seeds = _seed_range(config.get("validation_seeds", {"start": 2300, "count": 0}))
    generators = [str(item.get("param_generator", item.get("generator", "balanced_capacity"))) for item in config.get("scenarios", [{"param_generator": "balanced_capacity"}])]
    method_grids = dict(tuning_config.get("method_param_grid", {}))
    methods = [str(item.get("id", item)) if not isinstance(item, str) else item for item in config.get("methods", [])]
    if not methods:
        methods = ["replicator_capacity", "bnn_capacity", "smith_capacity", "primal_dual_capacity", "local_primal_dual_capacity"]

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
            train_score, metrics = _score_model_based_candidate(method_id, candidate, generators, seeds)
            validation_score = math.nan
            validation_metrics: dict[str, float] = {}
            if validation_seeds:
                validation_score, validation_metrics = _score_model_based_candidate(method_id, candidate, generators, validation_seeds)
            selection_score = validation_score if validation_seeds else train_score
            row = {
                "method": method_id,
                "split": "train",
                "selection_split": selection_split,
                "selection_score": selection_score,
                "candidate_score": train_score,
                "train_score": train_score,
                "validation_score": validation_score,
                "seed_count": len(seeds),
                **candidate,
                **metrics,
            }
            for key, value in validation_metrics.items():
                row[f"validation_{key}"] = value
            scores.append(row)
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

    validation_scores: list[dict[str, Any]] = []
    if validation_seeds:
        for method_id, item in best.items():
            score = float(item["validation_score"])
            _train_score = float(item["train_score"])
            _fresh_score, metrics = _score_model_based_candidate(method_id, dict(item["params"]), generators, validation_seeds)
            validation_scores.append(
                {
                    "method": method_id,
                    "split": "validation",
                    "selection_split": item["selection_split"],
                    "validation_score": score,
                    "train_score": _train_score,
                    "seed_count": len(validation_seeds),
                    **dict(item["params"]),
                    **metrics,
                }
            )

    artifact_payload = {
        "experiment_id": experiment_id,
        "config_path": str(config_path),
        "mode": "tune_model_based",
        "seed_start": seeds[0] if seeds else None,
        "seed_count": len(seeds),
        "validation_seed_start": validation_seeds[0] if validation_seeds else None,
        "validation_seed_count": len(validation_seeds),
        "scenario_generators": generators,
        "best_params": best,
    }
    output_artifact.write_text(yaml.safe_dump(artifact_payload, sort_keys=True, allow_unicode=False), encoding="utf-8")
    write_csv(output_dir / "tuning_scores.csv", scores, _ordered_columns(["method", "split", "candidate_score", "seed_count"], scores))
    if validation_scores:
        write_csv(output_dir / "validation_scores.csv", validation_scores, _ordered_columns(["method", "split", "validation_score", "seed_count"], validation_scores))
    manifest = {
        "experiment_id": experiment_id,
        "mode": "tune_model_based",
        "output_artifact": str(output_artifact),
        "seed_count": len(seeds),
        "validation_seed_count": len(validation_seeds),
        "methods": methods,
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def validate_data_driven_allocator(
    allocator: Any,
    *,
    training_id: str,
    method_id: str,
    generators: list[str],
    seeds: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator, variant_id, seed, params, world in iter_sp2_worlds(generators, seeds):
        context = DecisionContext(
            world=world,
            metadata={"communication_radius": params.communication_radius, "distance_decay_m": params.distance_decay_m},
        )
        oracle_assignment, oracle_runtime_ms = timed_allocate(CentralizedCapacityMILPAllocator(), context)
        capacity_oracle_assignment, capacity_oracle_runtime_ms = timed_allocate(CentralizedCapacityCoverageMILPAllocator(), context)
        assignment, runtime_ms = timed_allocate(allocator, context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=oracle_assignment,
            capacity_oracle_assignment=capacity_oracle_assignment,
            communication_radius=params.communication_radius,
            distance_decay_m=params.distance_decay_m,
        )
        rows.append(
            {
                "training_id": training_id,
                "method": method_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "capacity_ratio": params.capacity_ratio,
                "robot_payload_cv": params.robot_payload_cv,
                "load_mass_cv": params.load_mass_cv,
                "battery_variation": params.battery_variation,
                "communication_radius": params.communication_radius,
                "distance_decay_m": params.distance_decay_m,
                "oracle_runtime_ms": oracle_runtime_ms,
                "capacity_oracle_runtime_ms": capacity_oracle_runtime_ms,
                **metrics.to_dict(),
            }
        )
    return rows


def data_driven_metric_summary(
    training_id: str,
    split: str,
    rows: list[dict[str, Any]],
    seed_count: int,
    *,
    method_id: str,
) -> dict[str, Any]:
    return {
        "training_id": training_id,
        "method": method_id,
        "split": split,
        f"{split}_seed_count": seed_count,
        f"{split}_runs": len(rows),
        "capacity_success_rate_mean": _mean(rows, "capacity_success_rate"),
        "capacity_satisfaction_ratio_mean": _mean(rows, "capacity_satisfaction_ratio"),
        "under_capacity_kg_mean": _mean(rows, "under_capacity_kg"),
        "over_capacity_kg_mean": _mean(rows, "over_capacity_kg"),
        "capacity_waste_ratio_mean": _mean(rows, "capacity_waste_ratio"),
        "incomplete_capacity_ratio_mean": _mean(rows, "incomplete_capacity_ratio"),
        "served_capacity_alignment_mean": _mean(rows, "served_capacity_alignment"),
        "captured_reward_mean": _mean(rows, "captured_reward"),
        "optimality_gap_vs_oracle_mean": _mean(rows, "optimality_gap_vs_oracle"),
        "capacity_gap_vs_capacity_oracle_mean": _mean(rows, "capacity_gap_vs_capacity_oracle"),
        "effective_feasibility_ratio_mean": _mean(rows, "effective_feasibility_ratio"),
        "signed_score_delta_vs_oracle_mean": _mean(rows, "signed_score_delta_vs_oracle"),
        "travel_distance_m_mean": _mean(rows, "travel_distance_m"),
        "estimated_arrival_time_s_mean": _mean(rows, "estimated_arrival_time_s"),
        "energy_proxy_wh_mean": _mean(rows, "energy_proxy_wh"),
        "communication_coverage_ratio_mean": _mean(rows, "communication_coverage_ratio"),
        "runtime_ms_mean": _mean(rows, "runtime_ms"),
    }


def evaluate_data_driven_quality_gates(
    split_metrics: dict[str, dict[str, dict[str, Any]]],
    gates: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method_id, method_splits in split_metrics.items():
        method_gates = dict(gates.get(method_id, gates.get("default", {})) or {})
        for split, split_gates in method_gates.items():
            metrics = method_splits.get(str(split))
            if metrics is None:
                continue
            for name, threshold in dict(split_gates or {}).items():
                metric, direction = _parse_quality_gate(str(name))
                value = float(metrics.get(metric, math.nan))
                target = float(threshold)
                passed = value >= target if direction == "min" else value <= target
                rows.append(
                    {
                        "method": method_id,
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


def _score_model_based_candidate(
    method_id: str,
    params: dict[str, Any],
    generators: list[str],
    seeds: list[int],
) -> tuple[float, dict[str, float]]:
    rows: list[dict[str, Any]] = []
    for _generator, _variant_id, _seed, scenario_params, world in iter_sp2_worlds(generators, seeds):
        context = DecisionContext(
            world=world,
            metadata={"communication_radius": scenario_params.communication_radius, "distance_decay_m": scenario_params.distance_decay_m},
        )
        score_oracle, _score_runtime = timed_allocate(CentralizedCapacityMILPAllocator(), context)
        capacity_oracle, _capacity_runtime = timed_allocate(CentralizedCapacityCoverageMILPAllocator(), context)
        assignment, runtime_ms = timed_allocate(make_sp2_allocator(method_id, params), context)
        metrics = evaluate_assignment(
            world,
            assignment,
            runtime_ms=runtime_ms,
            oracle_assignment=score_oracle,
            capacity_oracle_assignment=capacity_oracle,
            communication_radius=scenario_params.communication_radius,
            distance_decay_m=scenario_params.distance_decay_m,
            centralized=method_id in {"hungarian_capacity", "centralized_capacity_milp"},
        )
        rows.append(metrics.to_dict())
    summary = {
        "capacity_satisfaction_ratio_mean": _mean(rows, "capacity_satisfaction_ratio"),
        "capacity_success_rate_mean": _mean(rows, "capacity_success_rate"),
        "optimality_gap_vs_oracle_mean": _mean(rows, "optimality_gap_vs_oracle"),
        "capacity_gap_vs_capacity_oracle_mean": _mean(rows, "capacity_gap_vs_capacity_oracle"),
        "under_capacity_kg_mean": _mean(rows, "under_capacity_kg"),
        "over_capacity_kg_mean": _mean(rows, "over_capacity_kg"),
        "capacity_waste_ratio_mean": _mean(rows, "capacity_waste_ratio"),
        "incomplete_capacity_ratio_mean": _mean(rows, "incomplete_capacity_ratio"),
        "served_capacity_alignment_mean": _mean(rows, "served_capacity_alignment"),
        "travel_distance_m_mean": _mean(rows, "travel_distance_m"),
        "energy_proxy_wh_mean": _mean(rows, "energy_proxy_wh"),
        "communication_messages_mean": _mean(rows, "communication_messages"),
        "runtime_ms_mean": _mean(rows, "runtime_ms"),
    }
    score = (
        1.25 * summary["optimality_gap_vs_oracle_mean"]
        + 0.95 * summary["capacity_gap_vs_capacity_oracle_mean"]
        + 0.85 * (1.0 - summary["capacity_success_rate_mean"])
        + 0.35 * (1.0 - summary["capacity_satisfaction_ratio_mean"])
        + 0.0006 * summary["under_capacity_kg_mean"]
        + 0.0004 * summary["over_capacity_kg_mean"]
        + 0.08 * summary["capacity_waste_ratio_mean"]
        + 0.0002 * summary["travel_distance_m_mean"]
        + 0.00003 * summary["energy_proxy_wh_mean"]
        + 0.00005 * summary["communication_messages_mean"]
        + 0.0002 * summary["runtime_ms_mean"]
    )
    return float(score), summary


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


def summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["scenario_generator"]), str(row["method"]))].append(row)
    summaries = []
    for (scenario, method), selected in sorted(grouped.items()):
        first = selected[0]
        summary = {
            "scenario_generator": scenario,
            "method": method,
            "method_label": first.get("method_label", method),
            **{f"method_{k}": v for k, v in sp2_method_metadata(method).items() if k in {"family", "scope", "ownership", "variant", "comparison_group"}},
            "n": len(selected),
        }
        for column in METHOD_RESOURCE_COLUMNS:
            summary[column] = first.get(column, "")
        for metric in SUMMARY_METRICS:
            summary[f"{metric}_mean"] = _mean(selected, metric)
        summaries.append(summary)
    return summaries


def rank_method_performance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranking = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["method"])].append(row)
    for method, selected in grouped.items():
        first = selected[0]
        item = {
            "scenario_generator": "ALL_SCENARIOS",
            "method": method,
            "method_label": first.get("method_label", method),
            **{f"method_{k}": v for k, v in sp2_method_metadata(method).items() if k in {"family", "scope", "ownership", "variant", "comparison_group"}},
            "n": len(selected),
            "ranking_rule": "min score-oracle gap, max capacity success, min capacity-ceiling gap, then min incomplete capacity and physical/resource cost",
        }
        for column in METHOD_RESOURCE_COLUMNS:
            item[column] = first.get(column, "")
        for metric in SUMMARY_METRICS:
            item[f"{metric}_mean"] = _mean(selected, metric)
        ranking.append(item)
    ranking.sort(key=_ranking_key)
    for idx, item in enumerate(ranking, start=1):
        item["rank"] = idx
    return ranking


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for spec in hypotheses:
        hid = str(spec.get("id", "H"))
        metric = str(spec.get("metric", "capacity_satisfaction_ratio"))
        method_a = str(spec.get("method_a", ""))
        method_b = str(spec.get("method_b", ""))
        direction = str(spec.get("direction", "greater"))
        alpha = float(spec.get("alpha", 0.05))
        if method_a and method_b:
            paired = _paired_values(rows, method_a, method_b, metric)
            if not paired:
                out.append(_hypothesis_error(hid, metric, alpha, "insufficient_pairs", f"{method_a} {method_b}"))
                continue
            a = np.asarray([x for x, _y in paired], dtype=float)
            b = np.asarray([y for _x, y in paired], dtype=float)
            delta = a - b
            alternative = "greater" if direction == "greater" else "less" if direction == "less" else "two-sided"
            p_value = wilcoxon_signed_rank_pvalue(delta, alternative=alternative)
            inference = mean_difference_inference(delta)
            out.append(
                {
                    "id": hid,
                    "metric": metric,
                    "test": "wilcoxon_signed_rank",
                    "n_pairs": len(paired),
                    "p_value": p_value,
                    **inference,
                    "alpha": alpha,
                    "reject": p_value < alpha,
                    "status": "ok",
                    "methods": f"{method_a} {method_b}",
                }
            )
        else:
            methods = [str(m) for m in spec.get("methods", [])]
            blocks = _friedman_blocks(rows, methods, metric)
            if len(blocks) < 2 or len(methods) < 3:
                out.append(_hypothesis_error(hid, metric, alpha, "insufficient_blocks", " ".join(methods), n_pairs=len(blocks)))
                continue
            arrays = [np.asarray([block[m] for block in blocks], dtype=float) for m in methods]
            test = stats.friedmanchisquare(*arrays)
            kendall_w = float(test.statistic / (len(blocks) * (len(methods) - 1)))
            p_value = float(test.pvalue) if np.isfinite(float(test.pvalue)) else 1.0
            out.append(
                {
                    "id": hid,
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
                    "reject": p_value < alpha,
                    "status": "ok",
                    "methods": " ".join(methods),
                }
            )
    return apply_holm_correction(out)


def _hypothesis_error(
    hid: str,
    metric: str,
    alpha: float,
    status: str,
    methods: str,
    *,
    n_pairs: int = 0,
) -> dict[str, Any]:
    return {
        "id": hid,
        "metric": metric,
        "test": "",
        "n_pairs": n_pairs,
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
        "alpha": alpha,
        "reject_raw": False,
        "reject_holm": False,
        "reject": False,
        "status": status,
        "methods": methods,
    }


def save_scenario_videos(candidates: list[dict[str, Any]], *, figures_dir: Path, videos_dir: Path, video_config: dict[str, Any]) -> list[dict[str, Any]]:
    metric = str(video_config.get("selection_metric", "capacity_satisfaction_ratio"))
    max_per_scenario = int(video_config.get("max_per_scenario", 16))
    fps = int(video_config.get("fps", 12))
    duration_s = float(video_config.get("duration_s", 10.0))
    final_hold_s = float(video_config.get("final_hold_s", 2.0))
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        row = candidate["row"]
        by_key[(str(row["scenario_generator"]), str(row["method"]))].append(candidate)
    selected = []
    by_scenario_count: dict[str, int] = defaultdict(int)
    for (scenario, method), items in sorted(by_key.items()):
        if by_scenario_count[scenario] >= max_per_scenario:
            continue
        metric_values = [float(x["row"].get(metric, 0.0)) for x in items if np.isfinite(float(x["row"].get(metric, 0.0)))]
        median_value = float(np.median(metric_values)) if metric_values else 0.0
        items.sort(key=lambda item: abs(float(item["row"].get(metric, 0.0)) - median_value))
        selected.append(items[0])
        by_scenario_count[scenario] += 1
    artifacts = []
    for item in selected:
        row = item["row"]
        stem = _artifact_stem(row)
        title = _artifact_title(row)
        snapshot = figures_dir / f"{stem}.png"
        video = videos_dir / f"{stem}.mp4"
        ok_snapshot = True
        save_capacity_snapshot(
            item["world"],
            item["assignment"],
            snapshot,
            title,
            communication_radius=float(row.get("communication_radius", np.inf)),
            distance_decay_m=float(row.get("distance_decay_m", 22.0)),
        )
        ok_video = save_capacity_video(
            item["world"],
            item["assignment"],
            video,
            title,
            communication_radius=float(row.get("communication_radius", np.inf)),
            distance_decay_m=float(row.get("distance_decay_m", 22.0)),
            fps=fps,
            duration_s=duration_s,
            final_hold_s=final_hold_s,
        )
        artifacts.append({"scenario_generator": row["scenario_generator"], "method": row["method"], "seed": row["seed"], "selection": "median", "metric": metric, "metric_value": row.get(metric), "snapshot": str(snapshot), "video": str(video), "ok": bool(ok_snapshot and ok_video)})
    return artifacts


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
        "SP2 evaluates physical effective capacity: which heterogeneous AMRs cover heterogeneous load demand after distance and battery discounts, while communication is tracked separately as observability.",
        "Theory note: because effective capacity is pair-dependent, the plain payoff V_k sigma(D_k-S_k)-g_ik is not generally potential-aligned. The Teorema 2 marginal payoff e_ik V_k sigma(D_k-S_k)-g_ik recovers exact potential structure for fixed E during the decision instant.",
        f"- Seeds: `{min(seeds)}`-`{max(seeds)}` (`n={len(seeds)}`)",
        f"- Scenario generators: `{', '.join(generators)}`",
        "- Training/tuning seeds must remain disjoint from this Monte Carlo evaluation.",
        "- `oracle_reference` is the score oracle: capacity coverage plus completed-load reward and small physical-cost penalties.",
        "- `capacity_oracle_reference` is the pure physical capacity ceiling used for `effective_feasibility_ratio` and capacity-gap analysis.",
        "",
        "## Method Taxonomy",
        "",
        "| Method | Label | Family | Scope | Ownership | Variant | Comparison group |",
        "|---|---|---|---|---|---|---|",
    ]
    for method in sorted({row["method"] for row in summary_rows} | {row["method"] for row in ranking_rows}):
        meta = sp2_method_metadata(str(method))
        lines.append(f"| {method} | {meta['label']} | {meta['family']} | {meta['scope']} | {meta['ownership']} | {meta['variant']} | {meta['comparison_group']} |")
    lines.extend(["", "## Resource Fairness", "", "| Method | Training type | Execution model | Trainable params | Tuned params | Decoder |", "|---|---|---|---:|---:|---|"])
    for method in sorted({row["method"] for row in ranking_rows}):
        first = next(row for row in ranking_rows if row["method"] == method)
        lines.append(f"| {method} | {first.get('method_training_type','')} | {first.get('method_execution_model','')} | {first.get('method_trainable_parameters',0)} | {first.get('method_tuned_parameters',0)} | {first.get('method_uses_decoder',False)} |")
    lines.extend(["", "## Summary", "", "| Scenario | Method | Family | Scope | Owner | n | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Alignment | Under kg | Over kg | Travel m | Energy Wh | Runtime ms |", "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for row in sorted(summary_rows, key=lambda item: (str(item["scenario_generator"]), str(item["method"]))):
        lines.append(
            "| {scenario} | {method} | {family} | {scope} | {owner} | {n} | {success:.3f} | {gap:.3f} | {cap_gap:.3f} | {cap:.3f} | {incomplete:.3f} | {alignment:.3f} | {under:.2f} | {over:.2f} | {travel:.2f} | {energy:.2f} | {runtime:.3f} |".format(
                scenario=row["scenario_generator"],
                method=row["method"],
                family=row.get("method_family", ""),
                scope=row.get("method_scope", ""),
                owner=row.get("method_ownership", ""),
                n=row["n"],
                cap=row.get("capacity_satisfaction_ratio_mean", math.nan),
                success=row.get("capacity_success_rate_mean", math.nan),
                incomplete=row.get("incomplete_capacity_ratio_mean", math.nan),
                alignment=row.get("served_capacity_alignment_mean", math.nan),
                under=row.get("under_capacity_kg_mean", math.nan),
                over=row.get("over_capacity_kg_mean", math.nan),
                gap=row.get("optimality_gap_vs_oracle_mean", math.nan),
                cap_gap=row.get("capacity_gap_vs_capacity_oracle_mean", math.nan),
                travel=row.get("travel_distance_m_mean", math.nan),
                energy=row.get("energy_proxy_wh_mean", math.nan),
                runtime=row.get("runtime_ms_mean", math.nan),
            )
        )
    best = ranking_rows[0] if ranking_rows else None
    lines.extend(["", "## Performance Ranking", "", "Ranking rule: minimize score-oracle gap; then maximize completed-load capacity success; then minimize capacity-ceiling gap, incomplete capacity, under/over capacity, travel, energy, communication, and runtime. Capacity satisfaction is reported as secondary coverage.", ""])
    if best:
        lines.append(f"Theory-aligned best overall: **{best['method']}** (`{best.get('method_ownership','')}`).")
    lines.extend(["", "| Rank | Method | Family | Owner | Success | Score gap | Capacity gap | Capacity | Incomplete cap. | Under kg | Over kg | Travel m | Params | Runtime ms |", "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for row in ranking_rows:
        lines.append(
            "| {rank} | {method} | {family} | {owner} | {success:.3f} | {gap:.3f} | {cap_gap:.3f} | {cap:.3f} | {incomplete:.3f} | {under:.2f} | {over:.2f} | {travel:.2f} | {params} | {runtime:.3f} |".format(
                rank=row["rank"],
                method=row["method"],
                family=row.get("method_family", ""),
                owner=row.get("method_ownership", ""),
                cap=row.get("capacity_satisfaction_ratio_mean", math.nan),
                success=row.get("capacity_success_rate_mean", math.nan),
                gap=row.get("optimality_gap_vs_oracle_mean", math.nan),
                cap_gap=row.get("capacity_gap_vs_capacity_oracle_mean", math.nan),
                incomplete=row.get("incomplete_capacity_ratio_mean", math.nan),
                under=row.get("under_capacity_kg_mean", math.nan),
                over=row.get("over_capacity_kg_mean", math.nan),
                travel=row.get("travel_distance_m_mean", math.nan),
                params=row.get("method_trainable_parameters", 0),
                runtime=row.get("runtime_ms_mean", math.nan),
            )
        )
    potential = dict(theory_audit.get("potential_alignment", {}))
    lines.extend(
        [
            "",
            "## Theory Audit",
            "",
            f"- Checks: `{theory_audit.get('checks', 0)}`.",
            f"- Failed checks: `{theory_audit.get('failed_checks', 0)}`.",
            f"- Passed: `{theory_audit.get('passed', False)}`.",
            f"- Potential theorem: `{potential.get('theorem', 'n/a')}`.",
            f"- Potential structure in this experiment: `{potential.get('potential_structure', 'n/a')}`.",
            f"- Marginal payoff methods: `{', '.join(potential.get('marginal_methods', [])) or 'none'}`.",
            f"- Distance interpretation: `{potential.get('distance_interpretation', 'n/a')}`.",
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
        lines.append(
            f"| {row.get('id')} | {row.get('metric')} | {row.get('n_pairs')} | {_format(row.get('p_value'))} | {_format(row.get('p_value_holm'))} | {_format(row.get('effect'))} | {ci} | {row.get('reject_holm', row.get('reject'))} | {row.get('status')} |"
        )
    lines.extend(["", "## Scenario Videos", ""])
    for item in scenario_videos:
        lines.append(f"- `{item['scenario_generator']}` `{item['method']}` seed `{item['seed']}`: `{Path(item['video']).name}`")
    lines.extend(["", "## Artifacts", "", "- `tables/runs.csv`", "- `tables/summary.csv`", "- `tables/performance_ranking.csv`", "- `tables/load_status.csv`", "- `tables/theory_checks.csv`", "- `tables/hypothesis_results.csv`", "- `theory_audit.json`", "- `figures/sp2_capacity_satisfaction_by_method.png`", "- `figures/sp2_capacity_ratio_interaction.png`", "- `figures/sp2_performance_matrix_by_method.png`", "- `figures/sp2_quality_resource_pareto.png`", "- `figures/sp2_capacity_cost_tradeoff.png`", "- `figures/sp2_capacity_coverage_vs_completion.png`", "- `figures/sp2_communication_radius_degradation.png`", "- `figures/sp2_best_method_by_scenario.png`", "- `videos/sp2_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


SUMMARY_METRICS = [
    "capacity_success_rate",
    "served_load_rate",
    "capacity_satisfaction_ratio",
    "demand_satisfaction_ratio",
    "coalition_success_rate",
    "under_capacity_kg",
    "over_capacity_kg",
    "capacity_waste_ratio",
    "mean_capacity_margin_kg",
    "nominal_payload_assigned_kg",
    "effective_capacity_assigned_kg",
    "incomplete_capacity_kg",
    "incomplete_capacity_ratio",
    "served_capacity_alignment",
    "robots_underassigned",
    "robots_overassigned",
    "travel_distance_m",
    "estimated_arrival_time_s",
    "energy_proxy_wh",
    "score_value",
    "oracle_score_value",
    "signed_score_delta_vs_oracle",
    "oracle_dominance_violation",
    "optimality_gap_vs_oracle",
    "capacity_oracle_satisfaction_ratio",
    "capacity_oracle_success_rate",
    "effective_feasibility_ratio",
    "capacity_gap_vs_capacity_oracle",
    "signed_capacity_delta_vs_capacity_oracle",
    "priority_regret",
    "communication_messages",
    "communication_coverage_ratio",
    "runtime_ms",
    "captured_reward",
    "oracle_reward",
]


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp2_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
    }


def method_resource_fields(method_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = sp2_method_metadata(method_id)
    params = params or {}
    checkpoint = params.get("checkpoint")
    checkpoint_meta = _checkpoint_metadata(checkpoint)
    tuning_meta = dict(params.get("_tuning_metadata", {})) if isinstance(params.get("_tuning_metadata", {}), dict) else {}
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": checkpoint_meta.get("trainable_parameters", meta["trainable_parameters"]),
        "method_training_parameters": checkpoint_meta.get("training_parameters", meta["trainable_parameters"]),
        "method_tuned_parameters": meta["tuned_parameters"],
        "method_training_episodes": checkpoint_meta.get("training_episodes", 0),
        "method_train_seed_count": checkpoint_meta.get("train_seed_count", 0),
        "method_validation_seed_count": checkpoint_meta.get("validation_seed_count", 0),
        "method_test_seed_count": checkpoint_meta.get("test_seed_count", 0),
        "method_tuning_type": tuning_meta.get("mode", ""),
        "method_tuning_seed_count": tuning_meta.get("seed_count", 0),
        "method_tuning_validation_seed_count": tuning_meta.get("validation_seed_count", 0),
        "method_tuning_artifact": tuning_meta.get("artifact", ""),
        "method_uses_neural_policy": meta["uses_neural_policy"],
        "method_uses_decoder": meta["uses_decoder"],
        "method_checkpoint_version": checkpoint_meta.get("model_version", ""),
        "method_rollout_action_mode": checkpoint_meta.get("rollout_action_mode", "supervised_or_static"),
    }


def summarize_theory_checks(theory_rows: list[dict[str, Any]], seeds: list[int], generators: list[str], method_specs: list[dict[str, Any]]) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    audited_methods = [str(spec["id"]) for spec in method_specs] + ["oracle_reference", "capacity_oracle_reference"]
    method_alignment = {method: sp2_potential_alignment(method) for method in audited_methods}
    marginal_methods = [method for method, row in method_alignment.items() if bool(row.get("payoff_uses_marginal_capacity", False))]
    exact_methods = [method for method, row in method_alignment.items() if row.get("potential_structure") == "exact"]
    return {
        "checks": len(theory_rows),
        "failed_checks": len(failed),
        "passed": len(failed) == 0,
        "seed_count": len(seeds),
        "seed_start": min(seeds) if seeds else None,
        "seed_end": max(seeds) if seeds else None,
        "scenario_generators": generators,
        "method_count": len(method_specs) + 2,
        "potential_alignment": {
            "effective_capacity_pair_dependent": True,
            "payoff_uses_marginal_capacity": bool(marginal_methods),
            "potential_structure": "mixed" if len(exact_methods) != len(method_alignment) else "exact",
            "theorem": "Teorema 2",
            "marginal_methods": marginal_methods,
            "exact_potential_methods": exact_methods,
            "method_alignment": method_alignment,
            "distance_interpretation": "deliverable_capacity_within_finite_operational_horizon",
            "static_capacity_limit": "ell_d_to_infinity_or_move_distance_to_separable_cost_gik",
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_columns(rows: list[dict[str, Any]]) -> list[str]:
    base = [
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
        "capacity_ratio",
        "robot_payload_mean_kg",
        "robot_payload_cv",
        "load_mass_cv",
        "battery_variation",
        "communication_radius",
        "distance_decay_m",
        "oracle_runtime_ms",
        "capacity_oracle_runtime_ms",
        *SUMMARY_METRICS,
        "assigned_robots",
        "idle_robots",
    ]
    return _ordered_columns(base, rows)


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *METHOD_RESOURCE_COLUMNS, "n", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def ranking_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "rank", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", *METHOD_RESOURCE_COLUMNS, "n", "ranking_rule", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def load_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_family", "method_scope", "method_ownership", "load_id", "load_index", "mass_kg", "length_m", "width_m", "required_robots", "assigned_robots", "robot_deficit", "robot_surplus", "required_capacity_kg", "assigned_nominal_capacity_kg", "assigned_effective_capacity_kg", "capacity_deficit_kg", "capacity_surplus_kg", "capacity_margin_kg", "capacity_satisfaction_ratio", "status", "reward", "assigned_robot_ids"], rows)


def theory_check_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "passed", "capacity_success_rate_valid", "capacity_ratio_valid", "labels_valid", "message"], rows)


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
        {"id": "greedy_capacity_nearest", "params": {}},
        {"id": "hungarian_capacity", "params": {}},
        {"id": "centralized_capacity_milp", "params": {}},
        {"id": "cbba_capacity", "params": {}},
        {"id": "replicator_capacity", "params": {}},
        {"id": "bnn_capacity", "params": {}},
        {"id": "smith_capacity", "params": {}},
        {"id": "primal_dual_capacity", "params": {}},
        {"id": "local_primal_dual_capacity", "params": {}},
        {"id": "imitation_capacity", "params": {}},
        {"id": "neural_capacity_scorer", "params": {}},
    ]


def _apply_tuned_params(method_specs: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    tuned = _load_tuned_params(config.get("tuning_artifacts", []))
    if not tuned:
        return method_specs
    output = []
    for spec in method_specs:
        method_id = str(spec["id"])
        params = dict(tuned.get(method_id, {}).get("params", {}))
        params.update(dict(spec.get("params", {})))
        if method_id in tuned:
            params["_tuning_metadata"] = dict(tuned[method_id].get("metadata", {}))
        output.append({"id": method_id, "params": params})
    return output


def _load_tuned_params(artifacts: Any) -> dict[str, dict[str, Any]]:
    if not artifacts:
        return {}
    paths = artifacts if isinstance(artifacts, list) else [artifacts]
    loaded: dict[str, dict[str, Any]] = {}
    for item in paths:
        path = Path(str(item))
        if not path.exists():
            continue
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        metadata = {
            "artifact": str(path),
            "seed_count": int(payload.get("seed_count", 0) or 0),
            "validation_seed_count": int(payload.get("validation_seed_count", 0) or 0),
            "mode": str(payload.get("mode", "tune_model_based")),
        }
        for method_id, row in dict(payload.get("best_params", {})).items():
            loaded[str(method_id)] = {"params": dict(row.get("params", {})), "metadata": metadata}
    return loaded


def _theory_check(row: dict[str, Any], world: Any, assignment: Any, communication_radius: float, distance_decay_m: float) -> dict[str, Any]:
    labels = np.asarray(assignment.labels, dtype=int)
    labels_valid = bool(labels.size == len(world.robots) and np.all(labels >= 0) and np.all(labels <= len(world.loads)))
    cap_valid = 0.0 <= float(row.get("capacity_satisfaction_ratio", 0.0)) <= 1.000001
    success_valid = 0.0 <= float(row.get("capacity_success_rate", 0.0)) <= 1.000001
    diagnostics = load_diagnostics(world, assignment, communication_radius=communication_radius, distance_decay_m=distance_decay_m)
    served_valid = all(row_diag["assigned_effective_capacity_kg"] + 1e-6 >= row_diag["required_capacity_kg"] for row_diag in diagnostics if row_diag["status"] in {"OK", "OVER"})
    passed = labels_valid and cap_valid and success_valid and served_valid
    return {
        "experiment_id": row["experiment_id"],
        "scenario_generator": row["scenario_generator"],
        "scenario_variant_id": row["scenario_variant_id"],
        "seed": row["seed"],
        "method": row["method"],
        "passed": passed,
        "capacity_success_rate_valid": success_valid,
        "capacity_ratio_valid": cap_valid,
        "labels_valid": labels_valid,
        "message": "" if passed else "SP2 capacity theory check failed",
    }


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (
        _finite(row.get("optimality_gap_vs_oracle_mean")),
        -_finite(row.get("capacity_success_rate_mean")),
        _finite(row.get("capacity_gap_vs_capacity_oracle_mean")),
        -_finite(row.get("served_capacity_alignment_mean")),
        _finite(row.get("incomplete_capacity_ratio_mean")),
        -_finite(row.get("capacity_satisfaction_ratio_mean")),
        _finite(row.get("under_capacity_kg_mean")),
        _finite(row.get("over_capacity_kg_mean")),
        _finite(row.get("travel_distance_m_mean")),
        _finite(row.get("energy_proxy_wh_mean")),
        _finite(row.get("communication_messages_mean")),
        _finite(row.get("runtime_ms_mean")),
    )


def _paired_values(rows: list[dict[str, Any]], method_a: str, method_b: str, metric: str) -> list[tuple[float, float]]:
    by_key: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))
        by_key[key][str(row["method"])] = row
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


def _artifact_stem(row: dict[str, Any]) -> str:
    meta = sp2_method_metadata(str(row["method"]))
    return (
        "sp2_{scenario}_{owner}_{family}_{scope}_{variant}_{method}_seed{seed}".format(
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
    meta = sp2_method_metadata(str(row["method"]))
    return f"SP2 {row['scenario_generator']} | {meta['title']} | seed {row['seed']}"


def _checkpoint_metadata(checkpoint: Any) -> dict[str, Any]:
    if checkpoint is None:
        return {}
    path = Path(str(checkpoint))
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    param_count = 0
    if "weights" in data:
        param_count = len(data["weights"])
    elif "w1" in data:
        param_count = int(np.asarray(data["w1"]).size + np.asarray(data.get("b1", [])).size + np.asarray(data.get("w2", [])).size + 1)
    return {
        "model_version": data.get("model_version", ""),
        "trainable_parameters": int(data.get("trainable_parameters", param_count)),
        "training_parameters": int(data.get("training_parameters", param_count)),
        "training_episodes": int(data.get("training_episodes", 0)),
        "train_seed_count": int(data.get("train_seed_count", 0)),
        "validation_seed_count": int(data.get("validation_seed_count", 0)),
        "test_seed_count": int(data.get("test_seed_count", 0)),
    }


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


def _format(value: Any) -> str:
    value = _float(value)
    if not np.isfinite(value):
        return "n/a"
    if abs(value) >= 100.0 or abs(value) < 1e-3 and value != 0:
        return f"{value:.3g}"
    return f"{value:.4f}"
