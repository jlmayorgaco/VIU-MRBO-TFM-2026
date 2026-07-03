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

from viu_mrob_tfm.allocation import DecisionContext, timed_allocate
from viu_mrob_tfm.sp1.methods import (
    CentralizedCoalitionOracleAllocator,
    SP1_METHOD_LABELS,
    fit_imitation_model,
    make_sp1_allocator,
)
from viu_mrob_tfm.sp1.mappo import train_mappo_recruitment
from viu_mrob_tfm.sp1.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp1.scenario import SP1RecruitmentScenario, iter_sp1_worlds
from viu_mrob_tfm.sp1.visualization import (
    plot_demand_ratio_interaction,
    plot_summary_bars,
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
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                "heterogeneous_robots": params.heterogeneous_robots,
                "communication_radius": params.communication_radius,
                "oracle_runtime_ms": oracle_runtime_ms,
                **metrics.to_dict(),
            }
            rows.append(row)
            for load_row in load_diagnostics(world, assignment):
                load_rows.append(
                    {
                        "experiment_id": experiment_id,
                        "scenario_generator": generator,
                        "scenario_variant_id": variant_id,
                        "seed": seed,
                        "method": method_id,
                        **load_row,
                    }
                )
            if representative is None and method_id in {"primal_dual_wrench_market", "centralized_coalition_milp"}:
                representative = (world, assignment, row)

        rows.append(
            {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": "oracle_reference",
                "method_label": "Oracle reference",
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "demand_ratio": params.demand_ratio,
                "heterogeneous_robots": params.heterogeneous_robots,
                "communication_radius": params.communication_radius,
                "oracle_runtime_ms": oracle_runtime_ms,
                **oracle_metrics.to_dict(),
            }
        )

    summary_rows = summarize_rows(rows)
    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, load_status_columns(load_rows))
    plot_summary_bars(rows, figures_dir / "sp1_demand_satisfaction_by_method.png")
    plot_demand_ratio_interaction(rows, figures_dir / "sp1_demand_ratio_interaction.png")
    if representative is not None and bool(config.get("artifacts", {}).get("save_video", True)):
        world, assignment, row = representative
        save_recruitment_snapshot(
            world,
            assignment,
            figures_dir / "sp1_representative_snapshot.png",
            f"{row['method_label']} {row['scenario_variant_id']}",
        )
        save_recruitment_video(
            world,
            assignment,
            videos_dir / "sp1_representative_recruitment.mp4",
            f"SP1 {row['method_label']}",
        )
    report_path = output_dir / "report.md"
    write_report(report_path, experiment_id, seeds, generators, summary_rows)
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
        for candidate in candidates:
            score = _score_candidate(method_id, candidate, generators, seeds)
            scores.append({"method": method_id, "score": score, **candidate})
            if score < best_score:
                best_score = score
                best_params = dict(candidate)
        best[method_id] = {"params": best_params, "score": float(best_score)}

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
            score = _score_candidate(method_id, dict(row["params"]), generators, validation_seeds)
            validation_scores.append({"method": method_id, "validation_score": score, **dict(row["params"])})
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
    generators = [str(item.get("param_generator", item.get("generator", "monte_carlo"))) for item in config.get("scenarios", [{"param_generator": "monte_carlo"}])]
    contexts = []
    for _generator, _variant_id, _seed, params, world in iter_sp1_worlds(generators, seeds):
        contexts.append(DecisionContext(world=world, metadata={"communication_radius": params.communication_radius}))
    model = fit_imitation_model(contexts, CentralizedCoalitionOracleAllocator())
    model.update({"training_id": training_id, "config_path": str(config_path), "train_seed_count": len(seeds)})
    model_path = checkpoint_dir / "model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_rows = []
    if validation_seeds:
        allocator = make_sp1_allocator("imitation_oracle", {"checkpoint": model_path})
        for _generator, variant_id, seed, params, world in iter_sp1_worlds(generators, validation_seeds):
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
            validation_rows.append(
                {
                    "training_id": training_id,
                    "scenario_variant_id": variant_id,
                    "seed": seed,
                    "n_robots": params.n_robots,
                    "n_loads": params.n_loads,
                    "demand_ratio": params.demand_ratio,
                    **metrics.to_dict(),
                }
            )
        write_csv(checkpoint_dir / "validation_runs.csv", validation_rows, run_columns(validation_rows))
        validation_summary = {
            "training_id": training_id,
            "validation_seed_count": len(validation_seeds),
            "validation_runs": len(validation_rows),
            "demand_satisfaction_ratio_mean": _mean_metric(validation_rows, "demand_satisfaction_ratio"),
            "coalition_success_rate_mean": _mean_metric(validation_rows, "coalition_success_rate"),
            "robots_underassigned_mean": _mean_metric(validation_rows, "robots_underassigned"),
            "robots_overassigned_mean": _mean_metric(validation_rows, "robots_overassigned"),
        }
        save_json(checkpoint_dir / "validation_metrics.json", validation_summary)
        model["validation"] = validation_summary
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
        "priority_regret",
        "optimality_gap_vs_oracle",
        "communication_messages",
        "runtime_ms",
    ]
    output = []
    for (scenario, method), group in sorted(groups.items()):
        row: dict[str, Any] = {"scenario_generator": scenario, "method": method, "n": len(group)}
        for metric in metrics:
            values = np.asarray([float(item[metric]) for item in group], dtype=float)
            row[f"{metric}_mean"] = float(np.nanmean(values))
            row[f"{metric}_std"] = float(np.nanstd(values, ddof=1)) if values.size > 1 else 0.0
        output.append(row)
    return output


def write_report(path: Path, experiment_id: str, seeds: list[int], generators: list[str], summary_rows: list[dict[str, Any]]) -> None:
    best = max(summary_rows, key=lambda row: (row["demand_satisfaction_ratio_mean"], -row["optimality_gap_vs_oracle_mean"]))
    lines = [
        f"# {experiment_id}",
        "",
        "SP1 evaluates recruitment only: which AMRs should be assigned to which heterogeneous load.",
        f"- Seeds: `{seeds[0]}`-`{seeds[-1]}` (`n={len(seeds)}`)",
        f"- Scenario generators: `{', '.join(generators)}`",
        "- Tuning/training must use disjoint seeds from this Monte Carlo config.",
        "",
        "## Summary",
        "",
        "| Scenario | Method | n | Success | Demand satisfaction | Under | Over | Gap vs oracle | Runtime ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            "| {scenario} | {method} | {n} | {success:.3f} | {demand:.3f} | {under:.3f} | {over:.3f} | {gap:.3f} | {runtime:.3f} |".format(
                scenario=row["scenario_generator"],
                method=row["method"],
                n=row["n"],
                success=row["coalition_success_rate_mean"],
                demand=row["demand_satisfaction_ratio_mean"],
                under=row["robots_underassigned_mean"],
                over=row["robots_overassigned_mean"],
                gap=row["optimality_gap_vs_oracle_mean"],
                runtime=row["runtime_ms_mean"],
            )
        )
    lines.extend(
        [
            "",
            f"Best mean demand satisfaction: **{best['method']}** on `{best['scenario_generator']}`.",
            "",
            "## Artifacts",
            "",
            "- `tables/runs.csv`",
            "- `tables/summary.csv`",
            "- `tables/load_status.csv`",
            "- `figures/sp1_demand_satisfaction_by_method.png`",
            "- `figures/sp1_demand_ratio_interaction.png`",
            "- `figures/sp1_representative_snapshot.png`",
            "- `videos/sp1_representative_recruitment.mp4`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "n_robots",
        "n_loads",
        "demand_ratio",
        "heterogeneous_robots",
        "communication_radius",
    ]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["scenario_generator", "method", "n"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def load_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "load_id", "status"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def tuning_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["method", "score"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def tuning_validation_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = ["method", "validation_score"]
    return preferred + sorted({key for row in rows for key in row if key not in preferred})


def _mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    values = np.asarray([float(row[metric]) for row in rows], dtype=float)
    return float(np.nanmean(values)) if values.size else math.nan
