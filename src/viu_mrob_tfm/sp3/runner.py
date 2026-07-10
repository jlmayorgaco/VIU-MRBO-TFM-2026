"""Executable SP3 role/slot wrench-feasibility Monte Carlo pipeline."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from scipy import stats

from viu_mrob_tfm.experiment_stats import (
    apply_holm_correction,
    mean_difference_inference,
    wilcoxon_signed_rank_pvalue as robust_wilcoxon_signed_rank_pvalue,
)
from viu_mrob_tfm.sp3.methods import (
    SP3_METHOD_LABELS,
    SP3Assignment,
    assignment_valid,
    make_sp3_allocator,
    score_assignment,
    sp3_method_design,
    sp3_method_metadata,
)
from viu_mrob_tfm.sp3.metrics import evaluate_assignment, load_diagnostics
from viu_mrob_tfm.sp3.pose_dynamics import (
    PoseTransportConfig,
    pose_transport_rows,
    pose_transport_summary,
    save_pose_transport_snapshot,
    save_pose_transport_video,
    simulate_pose_transport,
)
from viu_mrob_tfm.sp3.scenario import SP3Problem, iter_sp3_problems
from viu_mrob_tfm.sp3.visualization import (
    plot_complementarity_gain,
    plot_false_positive_by_scenario,
    plot_precision_coverage,
    plot_quality_resource_pareto,
    plot_residual_wrench_by_method,
    plot_scalar_vs_wrench_success,
    plot_wrench_set_valid_vs_invalid,
    save_wrench_snapshot,
    save_wrench_video,
)
from viu_mrob_tfm.utils.io import ensure_directory, load_yaml, save_json


SUMMARY_METRICS = [
    "scalar_feasible_rate",
    "wrench_feasible_rate",
    "false_positive_rate",
    "false_positive_given_scalar_rate",
    "assigned_loads",
    "feasible_assigned_loads",
    "infeasible_assigned_loads",
    "feasible_available_loads",
    "relative_feasibility",
    "feasible_coverage",
    "precision_given_assigned",
    "fp_given_assigned",
    "wrench_residual_norm",
    "max_wrench_residual_norm",
    "wrench_residual_feasible_available",
    "max_wrench_residual_feasible_available",
    "wrench_margin",
    "torque_error_nm",
    "force_error_n",
    "slot_coverage_ratio",
    "complementarity_gain",
    "scalar_wrench_success_gap",
    "slot_conflict_count",
    "assignment_valid",
    "travel_distance_m",
    "estimated_arrival_time_s",
    "energy_proxy_wh",
    "communication_messages",
    "runtime_ms",
    "score_value",
    "oracle_score_value",
    "signed_score_delta_vs_oracle",
    "oracle_dominance_violation",
    "optimality_gap_vs_wrench_oracle",
    "captured_reward",
    "oracle_reward",
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


def run_sp3_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path)
    config = load_yaml(config_path)
    mode = str(config.get("mode", "monte_carlo")).lower()
    if mode in {"monte_carlo", "mc", "debug"}:
        return run_monte_carlo(config, config_path=config_path)
    if mode in {"pose_transport_suite", "euler_lagrange_pose_suite", "pose_suite"}:
        return run_pose_transport_suite(config, config_path=config_path)
    if mode in {"pose_transport", "euler_lagrange_pose", "pose"}:
        if "cases" in config or "methods" in config:
            return run_pose_transport_suite(config, config_path=config_path)
        return run_pose_transport(config, config_path=config_path)
    raise ValueError(f"Unknown SP3 config mode: {mode}")


def run_pose_transport(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp3") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    scenario = dict(config.get("scenario", {"param_generator": "pose_transport_rotate"}))
    generator = str(scenario.get("param_generator", scenario.get("generator", "pose_transport_rotate")))
    seed = int(config.get("seed", 5200))
    method_id = str(config.get("method", "wrench_oracle"))
    problem_rows = list(iter_sp3_problems([generator], [seed]))
    if not problem_rows:
        raise ValueError("SP3 pose transport did not create a problem.")
    scenario_generator, variant_id, _seed, params, problem = problem_rows[0]
    allocator = make_sp3_allocator(method_id, dict(config.get("method_params", {})))
    assignment, runtime_ms = timed_allocate(allocator, problem)
    pose_config = _pose_transport_config(config.get("pose_transport", {}))
    result = simulate_pose_transport(problem, assignment, pose_config)
    summary = {
        "experiment_id": experiment_id,
        "mode": "pose_transport",
        "scenario_generator": scenario_generator,
        "scenario_variant_id": variant_id,
        "seed": seed,
        "method": method_id,
        "allocation_runtime_ms": runtime_ms,
        "n_robots": params.n_robots,
        "n_loads": params.n_loads,
        **pose_transport_summary(result),
    }
    write_csv(tables_dir / "pose_trajectory.csv", pose_transport_rows(result), _ordered_columns([], pose_transport_rows(result)))
    write_csv(tables_dir / "pose_summary.csv", [summary], _ordered_columns([], [summary]))
    save_json(output_dir / "summary.json", summary)
    save_json(
        output_dir / "theory_audit.json",
        {
            "passed": bool(summary["final_position_error_m"] < 1.0 and summary["final_orientation_error_deg"] < 35.0 and summary["hamiltonian_drop"] > 0.0),
            "checks": 4,
            "failed_checks": int(not (summary["final_position_error_m"] < 1.0))
            + int(not (summary["final_orientation_error_deg"] < 35.0))
            + int(not (summary["hamiltonian_drop"] > 0.0))
            + int(not (summary["slot_coverage_ratio"] >= 0.99)),
            "euler_lagrange_model": "M qdd + D qd = G(q) lambda",
            "hamiltonian": "0.5 qd^T M qd + V(q)",
            "vector_game_signal": "bounded slot-force projection with residual-support payoffs",
            "slot_coverage_ratio": summary["slot_coverage_ratio"],
        },
    )
    stem = f"sp3_pose_transport_{scenario_generator}_{method_id}_seed{seed}".replace("_", "-")
    snapshot = figures_dir / f"{stem}.png"
    video = videos_dir / f"{stem}.mp4"
    title = f"SP3 Euler-Lagrange pose transport | {method_id} | seed {seed}"
    save_pose_transport_snapshot(problem, result, snapshot, title)
    artifact_options = dict(config.get("artifacts", {}))
    video_ok = save_pose_transport_video(
        problem,
        result,
        video,
        title,
        fps=int(artifact_options.get("fps", 12)),
        frame_stride=int(artifact_options.get("frame_stride", 1)),
        duration_s=float(artifact_options.get("duration_s", 14.0)),
        final_hold_s=float(artifact_options.get("final_hold_s", 3.0)),
    )
    report_path = output_dir / "report.md"
    _write_pose_transport_report(report_path, summary, snapshot, video, video_ok)
    manifest = {
        "experiment_id": experiment_id,
        "mode": "pose_transport",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "summary": str(output_dir / "summary.json"),
        "pose_trajectory": str(tables_dir / "pose_trajectory.csv"),
        "report": str(report_path),
        "snapshot": str(snapshot),
        "video": str(video),
        "video_ok": bool(video_ok),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def run_pose_transport_suite(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    """Run multiple SP3 rigid-payload transport demos across methods and scarcity regimes."""

    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp3") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    trajectory_dir = ensure_directory(tables_dir / "trajectories")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    cases = _pose_case_specs(config)
    method_specs = _pose_method_specs(config)
    thresholds = dict(config.get("success_thresholds", {}))
    artifacts = dict(config.get("artifacts", {}))
    save_video = bool(artifacts.get("save_video", True))
    fps = int(artifacts.get("fps", 10))
    frame_stride = int(artifacts.get("frame_stride", 1))
    duration_s = float(artifacts.get("duration_s", 14.0))
    final_hold_s = float(artifacts.get("final_hold_s", 3.0))
    rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    videos: list[dict[str, Any]] = []

    for case in cases:
        generator = str(case.get("param_generator", case.get("generator", "pose_transport_rotate")))
        seed = int(case.get("seed", config.get("seed", 5200)))
        problem_rows = list(iter_sp3_problems([generator], [seed]))
        if not problem_rows:
            raise ValueError(f"SP3 pose transport suite did not create problem for {generator!r}.")
        scenario_generator, variant_id, _seed, params, problem = problem_rows[0]
        pose_input = _pose_case_config(config, case)
        pose_config = _pose_transport_config(pose_input)
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            allocator = make_sp3_allocator(method_id, dict(method_spec.get("params", {})))
            assignment, runtime_ms = timed_allocate(allocator, problem)
            result = simulate_pose_transport(problem, assignment, pose_config)
            summary = pose_transport_summary(result)
            pose_success = _pose_success(summary, thresholds)
            stem = _pose_suite_stem(case, scenario_generator, method_id, seed)
            trajectory_path = trajectory_dir / f"{stem}.csv"
            write_csv(trajectory_path, pose_transport_rows(result), _ordered_columns([], pose_transport_rows(result)))
            snapshot_path = figures_dir / f"{stem}.png"
            video_path = videos_dir / f"{stem}.mp4"
            title = _pose_suite_title(case, method_id, params.n_robots, params.n_loads)
            save_pose_transport_snapshot(problem, result, snapshot_path, title)
            video_ok = False
            if save_video:
                video_ok = save_pose_transport_video(
                    problem,
                    result,
                    video_path,
                    title,
                    fps=fps,
                    frame_stride=frame_stride,
                    duration_s=duration_s,
                    final_hold_s=final_hold_s,
                )
            row = {
                "experiment_id": experiment_id,
                "case_id": str(case.get("id", scenario_generator)),
                "movement_type": str(case.get("movement_type", "pose_transport")),
                "robot_load_regime": str(case.get("robot_load_regime", _robot_load_regime(params.n_robots, params.n_loads))),
                "scenario_generator": scenario_generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP3_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "load_index": pose_config.load_index,
                "complete_uncovered_slots": pose_config.complete_uncovered_slots,
                "allocation_runtime_ms": runtime_ms,
                "pose_success": pose_success,
                "snapshot": str(snapshot_path),
                "video": str(video_path),
                "video_ok": video_ok,
                "trajectory_csv": str(trajectory_path),
                **summary,
            }
            rows.append(row)
            theory_rows.append(_pose_theory_check(row, result))
            if video_ok:
                videos.append(
                    {
                        "case_id": row["case_id"],
                        "scenario_generator": scenario_generator,
                        "method": method_id,
                        "seed": seed,
                        "snapshot": str(snapshot_path),
                        "video": str(video_path),
                    }
                )

    summary = _pose_suite_summary(experiment_id, rows, theory_rows, cases, method_specs)
    write_csv(tables_dir / "pose_runs.csv", rows, _pose_run_columns(rows))
    write_csv(tables_dir / "pose_theory_checks.csv", theory_rows, _ordered_columns(["case_id", "method", "passed", "message"], theory_rows))
    save_json(output_dir / "summary.json", summary)
    save_json(output_dir / "theory_audit.json", summary["theory_audit"])
    plot_pose_suite_performance(rows, figures_dir / "sp3_pose_transport_suite_performance.png")
    report_path = output_dir / "report.md"
    _write_pose_transport_suite_report(report_path, summary, rows, videos)
    manifest = {
        "experiment_id": experiment_id,
        "mode": "pose_transport_suite",
        "config_path": str(config_path),
        "output_dir": str(output_dir),
        "runs": len(rows),
        "cases": [str(case.get("id", case.get("param_generator", "case"))) for case in cases],
        "methods": [str(spec["id"]) for spec in method_specs],
        "report": str(report_path),
        "pose_runs": str(tables_dir / "pose_runs.csv"),
        "theory_audit": str(output_dir / "theory_audit.json"),
        "videos": videos,
        "video_count": len(videos),
    }
    save_json(output_dir / "manifest.json", manifest)
    return manifest


def _pose_transport_config(config: dict[str, Any]) -> PoseTransportConfig:
    target = dict(config.get("target_pose", {}))
    dynamics = dict(config.get("dynamics", {}))
    initial_theta = float(config.get("initial_theta_rad", math.radians(float(config.get("initial_theta_deg", -28.0)))))
    target_theta = float(target.get("theta_rad", math.radians(float(target.get("theta_deg", 58.0)))))
    return PoseTransportConfig(
        load_index=int(config.get("load_index", 0)),
        initial_theta_rad=initial_theta,
        target_xy=(float(target.get("x", 2.2)), float(target.get("y", 1.25))),
        target_theta_rad=target_theta,
        dt=float(dynamics.get("dt", 0.04)),
        steps=int(dynamics.get("steps", 320)),
        kp_pos=float(dynamics.get("kp_pos", 34.0)),
        kd_pos=float(dynamics.get("kd_pos", 22.0)),
        kp_theta=float(dynamics.get("kp_theta", 28.0)),
        kd_theta=float(dynamics.get("kd_theta", 60.0)),
        linear_damping=float(dynamics.get("linear_damping", 7.5)),
        angular_damping=float(dynamics.get("angular_damping", 60.0)),
        force_command_limit_n=float(dynamics.get("force_command_limit_n", 95.0)),
        torque_command_limit_nm=float(dynamics.get("torque_command_limit_nm", 45.0)),
        recruit_fraction=float(config.get("recruit_fraction", 0.24)),
        complete_uncovered_slots=bool(config.get("complete_uncovered_slots", True)),
    )


def _write_pose_transport_report(path: Path, summary: dict[str, Any], snapshot: Path, video: Path, video_ok: bool) -> None:
    lines = [
        f"# {summary['experiment_id']}",
        "",
        "SP3 pose transport adds a dynamic rigid-payload check after role/slot recruitment.",
        "",
        "## Model",
        "",
        "The payload state is `q=[x,y,theta]`. The planar Euler-Lagrange form used in the simulation is:",
        "",
        "```math",
        "M(q) \\ddot q + D \\dot q = G(q)\\lambda, \\quad 0 \\le \\lambda_i \\le f_i^{max}.",
        "```",
        "",
        "The Hamiltonian diagnostic is:",
        "",
        "```math",
        "H(q,\\dot q)=\\frac{1}{2}\\dot q^T M \\dot q + V(q).",
        "```",
        "",
        "The vector-game signal is the residual-support payoff induced by the current generalized wrench error. It is not a full contact/friction simulator; it is a controlled planar rigid-body feasibility demonstration.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in [
        "final_position_error_m",
        "final_orientation_error_deg",
        "hamiltonian_drop",
        "mean_residual_norm",
        "max_torque_nm",
        "slot_coverage_ratio",
        "assigned_robots",
    ]:
        value = summary.get(key)
        lines.append(f"| `{key}` | {float(value):.4f} |" if isinstance(value, (int, float)) else f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Snapshot: `{snapshot}`",
            f"- MP4: `{video}` ({'ok' if video_ok else 'failed'})",
            f"- Trajectory CSV: `tables/pose_trajectory.csv`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pose_case_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    cases = config.get("cases")
    if isinstance(cases, list) and cases:
        return [dict(case) for case in cases]
    scenario = dict(config.get("scenario", {"param_generator": "pose_transport_rotate"}))
    scenario.setdefault("id", str(scenario.get("param_generator", scenario.get("generator", "pose_transport_rotate"))))
    scenario.setdefault("seed", int(config.get("seed", 5200)))
    scenario.setdefault("pose_transport", dict(config.get("pose_transport", {})))
    return [scenario]


def _pose_method_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    methods = config.get("methods")
    if isinstance(methods, list) and methods:
        return _method_specs(methods)
    return [{"id": str(config.get("method", "wrench_oracle")), "params": dict(config.get("method_params", {}))}]


def _pose_case_config(config: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(dict(config.get("pose_transport", {})), dict(case.get("pose_transport", {})))
    if "load_index" in case:
        merged["load_index"] = int(case["load_index"])
    merged.setdefault("load_index", 0)
    merged.setdefault("complete_uncovered_slots", False)
    return merged


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    output = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = _deep_merge(dict(output[key]), dict(value))
        else:
            output[key] = value
    return output


def _pose_success(summary: dict[str, Any], thresholds: dict[str, Any]) -> bool:
    position_limit = float(thresholds.get("position_error_m", 1.0))
    orientation_limit = float(thresholds.get("orientation_error_deg", 20.0))
    coverage_limit = float(thresholds.get("slot_coverage_ratio", 0.5))
    return bool(
        float(summary.get("final_position_error_m", math.inf)) <= position_limit
        and float(summary.get("final_orientation_error_deg", math.inf)) <= orientation_limit
        and float(summary.get("slot_coverage_ratio", 0.0)) >= coverage_limit
    )


def _pose_theory_check(row: dict[str, Any], result: Any) -> dict[str, Any]:
    numeric_keys = [
        "final_position_error_m",
        "final_orientation_error_deg",
        "hamiltonian_drop",
        "mean_residual_norm",
        "max_torque_nm",
        "slot_coverage_ratio",
        "assigned_robots",
    ]
    finite = all(np.isfinite(_float(row.get(key))) for key in numeric_keys)
    frame_count_valid = len(result.frames) >= 2
    coverage_valid = 0.0 <= _float(row.get("slot_coverage_ratio")) <= 1.000001
    hamiltonian_valid = all(np.isfinite(frame.hamiltonian) for frame in result.frames)
    passed = bool(finite and frame_count_valid and coverage_valid and hamiltonian_valid)
    return {
        "experiment_id": row["experiment_id"],
        "case_id": row["case_id"],
        "movement_type": row["movement_type"],
        "robot_load_regime": row["robot_load_regime"],
        "scenario_generator": row["scenario_generator"],
        "seed": row["seed"],
        "method": row["method"],
        "passed": passed,
        "finite_metrics": finite,
        "frame_count_valid": frame_count_valid,
        "coverage_valid": coverage_valid,
        "hamiltonian_valid": hamiltonian_valid,
        "message": "" if passed else "pose transport numerical/theory check failed",
    }


def _pose_suite_summary(
    experiment_id: str,
    rows: list[dict[str, Any]],
    theory_rows: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    method_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    return {
        "experiment_id": experiment_id,
        "mode": "pose_transport_suite",
        "runs": len(rows),
        "case_count": len(cases),
        "method_count": len(method_specs),
        "video_ok_count": int(sum(1 for row in rows if bool(row.get("video_ok", False)))),
        "pose_success_rate": float(np.mean([bool(row.get("pose_success", False)) for row in rows])) if rows else 0.0,
        "mean_final_position_error_m": _mean(rows, "final_position_error_m") if rows else math.nan,
        "mean_final_orientation_error_deg": _mean(rows, "final_orientation_error_deg") if rows else math.nan,
        "mean_slot_coverage_ratio": _mean(rows, "slot_coverage_ratio") if rows else math.nan,
        "theory_audit": {
            "checks": len(theory_rows),
            "failed_checks": len(failed),
            "passed": len(failed) == 0,
            "euler_lagrange_model": "M(q) qdd + D qd = G(q) lambda",
            "hamiltonian": "0.5 qd^T M qd + V(q)",
            "wrench_projection": "bounded least-squares over planar slot force columns",
            "vector_game_signal": "residual-support payoff eta^T g_i with bounded force effort",
            "note": "A failed pose_success is a method outcome, not a theory-audit failure.",
        },
    }


def _pose_run_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(
        [
            "experiment_id",
            "case_id",
            "movement_type",
            "robot_load_regime",
            "scenario_generator",
            "scenario_variant_id",
            "seed",
            "method",
            "method_label",
            "method_family",
            "method_scope",
            "method_ownership",
            "method_variant",
            "method_engine",
            "method_payoff_signal",
            "method_role",
            "n_robots",
            "n_loads",
            "load_index",
            "complete_uncovered_slots",
            "allocation_runtime_ms",
            "pose_success",
            "frames",
            "assigned_robots",
            "slot_coverage_ratio",
            "final_position_error_m",
            "final_orientation_error_deg",
            "hamiltonian_drop",
            "mean_residual_norm",
            "max_torque_nm",
            "mass_kg",
            "inertia_kg_m2",
            "video_ok",
            "snapshot",
            "video",
            "trajectory_csv",
        ],
        rows,
    )


def _write_pose_transport_suite_report(path: Path, summary: dict[str, Any], rows: list[dict[str, Any]], videos: list[dict[str, Any]]) -> None:
    lines = [
        f"# {summary['experiment_id']}",
        "",
        "SP3 dynamic pose-transport suite compares centralized, decentralized, classic, SOTA-proxy and proposed role/slot methods after wrench-aware recruitment.",
        "",
        "## Model",
        "",
        "```math",
        "M(q) \\ddot q + D \\dot q = G(q)\\lambda, \\quad 0 \\le \\lambda_i \\le f_i^{max}",
        "```",
        "",
        "The payload state is `q=[x,y,theta]`. Each AMR contact contributes a planar wrench column `[d_x,d_y,r_x d_y-r_y d_x]^T`; the controller projects a desired generalized wrench onto bounded slot forces. The Hamiltonian diagnostic is `H=0.5 qd^T M qd + V(q)`.",
        "",
        "When `complete_uncovered_slots=True`, the dynamic demo fills uncovered target-load slots with nearest idle AMR after the selected allocator. That option is for visual/physical pose transport examples; the assignment benchmark remains the strict SP3 Monte Carlo v3.",
        "",
        "## Summary",
        "",
        f"- Runs: `{summary['runs']}`.",
        f"- Cases: `{summary['case_count']}`.",
        f"- Methods: `{summary['method_count']}`.",
        f"- Pose success rate: `{summary['pose_success_rate']:.3f}`.",
        f"- Theory failed checks: `{summary['theory_audit']['failed_checks']}`.",
        "",
        "## Runs",
        "",
        "| Case | Regime | Movement | Method | Family | Scope | Owner | Success | Slots | Pos err m | Ori err deg | H drop | Video |",
        "|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {case} | {regime} | {movement} | {method} | {family} | {scope} | {owner} | {success} | {slots:.2f} | {pos:.3f} | {ori:.2f} | {hdrop:.2f} | {video} |".format(
                case=row["case_id"],
                regime=row["robot_load_regime"],
                movement=row["movement_type"],
                method=row["method"],
                family=row["method_family"],
                scope=row["method_scope"],
                owner=row["method_ownership"],
                success=row["pose_success"],
                slots=float(row["slot_coverage_ratio"]),
                pos=float(row["final_position_error_m"]),
                ori=float(row["final_orientation_error_deg"]),
                hdrop=float(row["hamiltonian_drop"]),
                video=Path(str(row["video"])).name if row.get("video_ok") else "not generated",
            )
        )
    lines.extend(["", "## Videos", ""])
    for item in videos:
        lines.append(f"- `{item['case_id']}` `{item['method']}` seed `{item['seed']}`: `{Path(item['video']).name}`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `tables/pose_runs.csv`",
            "- `tables/pose_theory_checks.csv`",
            "- `tables/trajectories/*.csv`",
            "- `figures/sp3_pose_transport_suite_performance.png`",
            "- `videos/*.mp4`",
            "- `theory_audit.json`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_pose_suite_performance(rows: list[dict[str, Any]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8))
    if not rows:
        for ax in axes:
            ax.text(0.5, 0.5, "No pose runs", ha="center", va="center")
        fig.savefig(path, dpi=170, bbox_inches="tight")
        plt.close(fig)
        return
    methods = sorted({str(row["method"]) for row in rows})
    x = np.arange(len(methods))
    pos_means = [_mean([row for row in rows if row["method"] == method], "final_position_error_m") for method in methods]
    ori_means = [_mean([row for row in rows if row["method"] == method], "final_orientation_error_deg") for method in methods]
    success = [float(np.mean([bool(row["pose_success"]) for row in rows if row["method"] == method])) for method in methods]
    axes[0].bar(x - 0.18, pos_means, width=0.36, label="position error m", color="#2563eb")
    axes[0].bar(x + 0.18, np.asarray(ori_means) / 20.0, width=0.36, label="orientation error / 20", color="#dc2626")
    axes[0].set_title("Mean pose error by method")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(methods, rotation=35, ha="right", fontsize=7)
    axes[0].grid(True, axis="y", alpha=0.22)
    axes[0].legend(fontsize=7)
    axes[1].bar(x, success, color="#16a34a")
    axes[1].set_ylim(0.0, 1.05)
    axes[1].set_title("Pose success rate")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(methods, rotation=35, ha="right", fontsize=7)
    axes[1].grid(True, axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def _pose_suite_stem(case: dict[str, Any], scenario_generator: str, method_id: str, seed: int) -> str:
    case_id = str(case.get("id", scenario_generator))
    return f"sp3-pose-{case_id}-{scenario_generator}-{method_id}-seed{seed}".replace("_", "-").replace(" ", "-")


def _pose_suite_title(case: dict[str, Any], method_id: str, n_robots: int, n_loads: int) -> str:
    case_id = str(case.get("id", case.get("param_generator", "pose")))
    movement = str(case.get("movement_type", "pose_transport"))
    regime = str(case.get("robot_load_regime", _robot_load_regime(n_robots, n_loads)))
    meta = sp3_method_metadata(method_id)
    return f"SP3 pose | {case_id} | {movement} | {regime} | {meta['title']}"


def _robot_load_regime(n_robots: int, n_loads: int) -> str:
    if n_robots > n_loads:
        return "more_robots_than_loads"
    if n_robots == n_loads:
        return "equal_robots_loads"
    return "fewer_robots_than_loads"


def run_monte_carlo(config: dict[str, Any], *, config_path: Path) -> dict[str, Any]:
    experiment_id = str(config.get("experiment_id", config_path.stem))
    output_dir = ensure_directory(config.get("output_dir", Path("results/sp3") / experiment_id))
    tables_dir = ensure_directory(output_dir / "tables")
    figures_dir = ensure_directory(output_dir / "figures")
    videos_dir = ensure_directory(output_dir / "videos")
    seeds = _seed_range(config.get("seeds", {"start": 4100, "count": 5}))
    generators = [str(item.get("param_generator", item.get("generator", item.get("id", "setup")))) for item in config.get("scenarios", [{"param_generator": "setup"}])]
    method_specs = _method_specs(config.get("methods", []))
    rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    theory_rows: list[dict[str, Any]] = []
    video_candidates: list[dict[str, Any]] = []

    for generator, variant_id, seed, params, problem in iter_sp3_problems(generators, seeds):
        oracle_allocator = make_sp3_allocator("wrench_oracle")
        oracle_assignment, oracle_runtime_ms = timed_allocate(oracle_allocator, problem)
        for method_spec in method_specs:
            method_id = str(method_spec["id"])
            allocator = make_sp3_allocator(method_id, dict(method_spec.get("params", {})))
            assignment, runtime_ms = timed_allocate(allocator, problem)
            centralized = str(sp3_method_metadata(method_id)["scope"]) == "centralized"
            metrics = evaluate_assignment(
                problem,
                assignment,
                runtime_ms=runtime_ms,
                oracle_assignment=oracle_assignment,
                centralized=centralized,
            )
            row = {
                "experiment_id": experiment_id,
                "scenario_generator": generator,
                "scenario_variant_id": variant_id,
                "seed": seed,
                "method": method_id,
                "method_label": SP3_METHOD_LABELS.get(method_id, method_id),
                **method_taxonomy_fields(method_id),
                **method_resource_fields(method_id),
                "n_robots": params.n_robots,
                "n_loads": params.n_loads,
                "robot_force_n": params.robot_force_n,
                "robot_payload_kg": params.robot_payload_kg,
                "communication_radius": params.communication_radius,
                "wrench_tolerance": params.wrench_tolerance,
                "oracle_runtime_ms": oracle_runtime_ms,
                **metrics.to_dict(),
            }
            rows.append(row)
            theory_rows.append(_theory_check(row, problem, assignment))
            video_candidates.append({"problem": problem, "assignment": assignment, "row": row})
            for load_row in load_diagnostics(problem, assignment):
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

    summary_rows = summarize_rows(rows)
    ranking_rows = rank_method_performance(rows)
    hypothesis_rows = evaluate_hypotheses(rows, config.get("hypotheses", []))
    theory_audit = summarize_theory_checks(theory_rows, seeds, generators, method_specs, rows)

    write_csv(tables_dir / "runs.csv", rows, run_columns(rows))
    write_csv(tables_dir / "summary.csv", summary_rows, summary_columns(summary_rows))
    write_csv(tables_dir / "performance_ranking.csv", ranking_rows, ranking_columns(ranking_rows))
    write_csv(tables_dir / "load_status.csv", load_rows, load_status_columns(load_rows))
    write_csv(tables_dir / "theory_checks.csv", theory_rows, theory_check_columns(theory_rows))
    write_csv(tables_dir / "hypothesis_results.csv", hypothesis_rows, hypothesis_columns(hypothesis_rows))
    save_json(output_dir / "theory_audit.json", theory_audit)

    plot_scalar_vs_wrench_success(rows, figures_dir / "sp3_scalar_vs_wrench_success_by_method.png")
    plot_false_positive_by_scenario(rows, figures_dir / "sp3_false_positive_rate_by_scenario.png")
    plot_residual_wrench_by_method(rows, figures_dir / "sp3_residual_wrench_by_method.png")
    plot_wrench_set_valid_vs_invalid(rows, figures_dir / "sp3_wrench_set_valid_vs_invalid.png")
    plot_precision_coverage(rows, figures_dir / "sp3_precision_coverage.png")
    plot_complementarity_gain(rows, figures_dir / "sp3_complementarity_gain.png")
    plot_quality_resource_pareto(rows, figures_dir / "sp3_quality_resource_pareto.png")

    artifact_config = dict(config.get("artifacts", {}))
    scenario_videos: list[dict[str, Any]] = []
    if bool(artifact_config.get("save_video", True)):
        scenario_videos = save_scenario_videos(
            video_candidates,
            figures_dir=figures_dir,
            videos_dir=videos_dir,
            video_config=dict(artifact_config.get("video", {})),
        )

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


def timed_allocate(allocator: Any, problem: SP3Problem) -> tuple[SP3Assignment, float]:
    start = perf_counter()
    assignment = allocator.allocate(problem)
    return assignment, 1000.0 * (perf_counter() - start)


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
        ranked["ranking_rule"] = (
            "minimize strict wrench-oracle gap, maximize feasible coverage, minimize infeasible assigned loads, "
            "maximize assigned-load precision, then residual and resource costs"
        )
        output.append(ranked)
    return output


def evaluate_hypotheses(rows: list[dict[str, Any]], hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for spec in hypotheses:
        metric = str(spec.get("metric", "optimality_gap_vs_wrench_oracle"))
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
            p_value = float(p_value)
            if not np.isfinite(p_value):
                p_value = 1.0
            kendall_w = float(statistic / (len(blocks) * (len(methods) - 1)))
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
        method = str(spec.get("method", "oracle_scalar_assignment"))
        threshold = float(spec.get("threshold", 0.0))
        values = np.asarray([_float(row.get(metric)) for row in rows if str(row["method"]) == method], dtype=float)
        values = values[np.isfinite(values)]
        if values.size < 2:
            output.append(_hypothesis_error(spec, metric, "not enough samples"))
            continue
        alternative = str(spec.get("direction", "greater"))
        alternative = alternative if alternative in {"less", "greater", "two-sided"} else "two-sided"
        diffs = values - threshold
        p_value = robust_wilcoxon_signed_rank_pvalue(diffs, alternative=alternative)
        inference = mean_difference_inference(diffs, effect_name="mean_minus_threshold")
        output.append(
            {
                "id": spec.get("id", ""),
                "metric": metric,
                "test": "one_sample_wilcoxon_signed_rank",
                "n_pairs": int(values.size),
                "p_value": p_value,
                **inference,
                "alpha": alpha,
                "reject": bool(p_value < alpha),
                "status": "ok",
                "methods": method,
            }
        )
    return apply_holm_correction(output)


def save_scenario_videos(candidates: list[dict[str, Any]], *, figures_dir: Path, videos_dir: Path, video_config: dict[str, Any]) -> list[dict[str, Any]]:
    max_per_scenario = int(video_config.get("max_per_scenario", 8))
    selection_metric = str(video_config.get("selection_metric", "wrench_feasible_rate"))
    fps = int(video_config.get("fps", 10))
    duration_s = float(video_config.get("duration_s", 12.0))
    final_hold_s = float(video_config.get("final_hold_s", 3.0))
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
            save_wrench_snapshot(item["problem"], item["assignment"], snapshot, title)
            ok = save_wrench_video(
                item["problem"],
                item["assignment"],
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
                        "method": row["method"],
                        "seed": int(row["seed"]),
                        "snapshot": str(snapshot),
                        "video": str(video),
                    }
                )
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
        "SP3 evaluates role/slot wrench feasibility: scalar capacity is not sufficient when the load requires a planar force-torque vector.",
        f"- Seeds: `{seeds[0]}`-`{seeds[-1]}` (`n={len(seeds)}`)" if seeds else "- Seeds: none",
        f"- Scenario generators: `{', '.join(generators)}`",
        "",
        "## Method Taxonomy",
        "",
        "| Method | Label | Family | Scope | Ownership | Variant |",
        "|---|---|---|---|---|---|",
    ]
    for method in sorted({row["method"] for row in summary_rows}):
        meta = sp3_method_metadata(str(method))
        lines.append(f"| {method} | {meta['label']} | {meta['family']} | {meta['scope']} | {meta['ownership']} | {meta['variant']} |")
    lines.extend(["", "## Method Design", "", "SP3 separates the dynamic engine from the wrench signal. Replicator, Smith, BNN and CBBA are engines; the contribution is the strict wrench feasibility reference plus wrench-deficit, marginal-rho and residual-support signals.", "", "| Method | Engine | Payoff/signal | Role | Phase |", "|---|---|---|---|---|"])
    for method in sorted({row["method"] for row in summary_rows}):
        design = sp3_method_design(str(method))
        lines.append(f"| {method} | {design['engine']} | {design['payoff_signal']} | {design['method_role']} | {design['recommended_phase']} |")
    lines.extend(["", "## Performance Ranking", "", "| Rank | Method | Family | Owner | Coverage | Precision | FP assigned | Feasible residual | Gap | Runtime ms |", "|---:|---|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in ranking_rows:
        lines.append(
            "| {rank} | {method} | {family} | {owner} | {coverage:.3f} | {precision:.3f} | {fp:.3f} | {res:.3f} | {gap:.3f} | {runtime:.3f} |".format(
                rank=row["rank"],
                method=row["method"],
                family=row.get("method_family", ""),
                owner=row.get("method_ownership", ""),
                coverage=row.get("feasible_coverage_mean", math.nan),
                precision=row.get("precision_given_assigned_mean", math.nan),
                fp=row.get("fp_given_assigned_mean", math.nan),
                res=row.get("wrench_residual_feasible_available_mean", math.nan),
                gap=row.get("optimality_gap_vs_wrench_oracle_mean", math.nan),
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
    lines.extend(["", "## Artifacts", "", "- `tables/runs.csv`", "- `tables/summary.csv`", "- `tables/performance_ranking.csv`", "- `tables/load_status.csv`", "- `tables/theory_checks.csv`", "- `tables/hypothesis_results.csv`", "- `theory_audit.json`", "- `figures/sp3_scalar_vs_wrench_success_by_method.png`", "- `figures/sp3_false_positive_rate_by_scenario.png`", "- `figures/sp3_residual_wrench_by_method.png`", "- `figures/sp3_wrench_set_valid_vs_invalid.png`", "- `figures/sp3_precision_coverage.png`", "- `figures/sp3_complementarity_gain.png`", "- `figures/sp3_quality_resource_pareto.png`", "- `videos/sp3_<scenario>_<ownership>_<family>_<scope>_<variant>_<method>_seed<seed>.mp4`"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def method_taxonomy_fields(method_id: str) -> dict[str, str]:
    meta = sp3_method_metadata(method_id)
    return {
        "method_family": str(meta["family"]),
        "method_scope": str(meta["scope"]),
        "method_ownership": str(meta["ownership"]),
        "method_variant": str(meta["variant"]),
        "method_comparison_group": str(meta["comparison_group"]),
        "method_engine": str(meta["engine"]),
        "method_payoff_signal": str(meta["payoff_signal"]),
        "method_role": str(meta["method_role"]),
        "method_recommended_phase": str(meta["recommended_phase"]),
    }


def method_resource_fields(method_id: str) -> dict[str, Any]:
    meta = sp3_method_metadata(method_id)
    return {
        "method_training_type": meta["training_type"],
        "method_execution_model": meta["execution_model"],
        "method_communication_pattern": meta["communication_pattern"],
        "method_trainable_parameters": meta["trainable_parameters"],
        "method_tuned_parameters": meta["tuned_parameters"],
        "method_uses_neural_policy": meta["uses_neural_policy"],
        "method_uses_decoder": meta["uses_decoder"],
    }


def summarize_theory_checks(
    theory_rows: list[dict[str, Any]],
    seeds: list[int],
    generators: list[str],
    method_specs: list[dict[str, Any]],
    run_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    failed = [row for row in theory_rows if not bool(row.get("passed", False))]
    methods = [str(spec["id"]) for spec in method_specs]
    abstention_gate = _abstention_gaming_gate(run_rows or [])
    failed_count = len(failed) + int(abstention_gate["failed_checks"])
    check_count = len(theory_rows) + int(abstention_gate["checks"])
    return {
        "checks": check_count,
        "failed_checks": failed_count,
        "passed": failed_count == 0,
        "seed_count": len(seeds),
        "seed_start": min(seeds) if seeds else None,
        "seed_end": max(seeds) if seeds else None,
        "scenario_generators": generators,
        "method_count": len(method_specs),
        "method_design": {method: sp3_method_design(method) for method in methods},
        "engine_signal_principle": "Replicator/Smith/BNN/CBBA are dynamic engines; SP3 contribution is the strict wrench feasibility reference, wrench payoff, marginal rho signal, slot clearing, and residual-support wrench market.",
        "gates": {
            "G3_no_abstention_gaming": abstention_gate,
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", "method_engine", "method_payoff_signal", "method_role", "method_recommended_phase", *RESOURCE_COLUMNS, "n_robots", "n_loads", "robot_force_n", "robot_payload_kg", "communication_radius", "wrench_tolerance", "oracle_runtime_ms", *SUMMARY_METRICS, "assigned_robots", "idle_robots"], rows)


def summary_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", "method_engine", "method_payoff_signal", "method_role", "method_recommended_phase", *RESOURCE_COLUMNS, "n", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def ranking_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["scenario_generator", "rank", "method", "method_label", "method_family", "method_scope", "method_ownership", "method_variant", "method_comparison_group", "method_engine", "method_payoff_signal", "method_role", "method_recommended_phase", *RESOURCE_COLUMNS, "n", "ranking_rule", *[f"{m}_mean" for m in SUMMARY_METRICS]], rows)


def load_status_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "method_family", "method_scope", "method_ownership", "load_id", "load_index", "mass_kg", "required_capacity_kg", "required_robots", "wrench_fx_n", "wrench_fy_n", "wrench_tau_nm", "assigned_robots", "assigned_load", "feasible_assigned", "infeasible_assigned", "assigned_robot_ids", "assigned_slot_labels", "scalar_feasible", "wrench_feasible", "false_positive", "wrench_residual_norm", "wrench_margin", "force_error_n", "torque_error_nm", "achieved_fx_n", "achieved_fy_n", "achieved_tau_nm", "slot_coverage_ratio", "complementarity_gain", "reward", "status"], rows)


def theory_check_columns(rows: list[dict[str, Any]]) -> list[str]:
    return _ordered_columns(["experiment_id", "scenario_generator", "scenario_variant_id", "seed", "method", "passed", "assignment_valid", "rates_valid", "precision_coverage_valid", "oracle_dominance_valid", "message"], rows)


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


def _theory_check(row: dict[str, Any], problem: SP3Problem, assignment: SP3Assignment) -> dict[str, Any]:
    rates = [
        _float(row.get("scalar_feasible_rate")),
        _float(row.get("wrench_feasible_rate")),
        _float(row.get("false_positive_rate")),
        _float(row.get("false_positive_given_scalar_rate")),
    ]
    precision_coverage_rates = [
        _float(row.get("relative_feasibility")),
        _float(row.get("feasible_coverage")),
        _float(row.get("precision_given_assigned")),
        _float(row.get("fp_given_assigned")),
    ]
    rates_valid = all(0.0 <= value <= 1.000001 for value in rates if np.isfinite(value))
    precision_coverage_valid = all(0.0 <= value <= 1.000001 for value in precision_coverage_rates if np.isfinite(value))
    valid = assignment_valid(problem, assignment)
    dominance_valid = not bool(row.get("oracle_dominance_violation", False))
    passed = bool(valid and rates_valid and precision_coverage_valid and dominance_valid)
    return {
        "experiment_id": row["experiment_id"],
        "scenario_generator": row["scenario_generator"],
        "scenario_variant_id": row["scenario_variant_id"],
        "seed": row["seed"],
        "method": row["method"],
        "passed": passed,
        "assignment_valid": valid,
        "rates_valid": rates_valid,
        "precision_coverage_valid": precision_coverage_valid,
        "oracle_dominance_valid": dominance_valid,
        "message": "" if passed else "SP3 theory check failed",
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
        {"id": "wrench_oracle", "params": {}},
        {"id": "oracle_scalar_assignment", "params": {}},
        {"id": "hungarian_slots", "params": {}},
        {"id": "capacity_greedy_slots", "params": {}},
        {"id": "cbba_slots", "params": {}},
        {"id": "replicator_wrench_deficit", "params": {}},
        {"id": "bnn_wrench_deficit", "params": {}},
        {"id": "smith_wrench_deficit", "params": {}},
        {"id": "smith_wrench_marginal", "params": {}},
        {"id": "support_dual_wrench_market", "params": {}},
    ]


def _ranking_key(row: dict[str, Any]) -> tuple[float, ...]:
    return (
        _finite(row.get("optimality_gap_vs_wrench_oracle_mean", row.get("optimality_gap_vs_wrench_oracle"))),
        -_finite_or(row.get("relative_feasibility_mean", row.get("relative_feasibility")), 0.0),
        -_finite_or(row.get("feasible_coverage_mean", row.get("feasible_coverage")), 0.0),
        _finite(row.get("fp_given_assigned_mean", row.get("fp_given_assigned"))),
        -_finite_or(row.get("precision_given_assigned_mean", row.get("precision_given_assigned")), 0.0),
        _finite(row.get("wrench_residual_feasible_available_mean", row.get("wrench_residual_feasible_available"))),
        _finite(row.get("travel_distance_m_mean", row.get("travel_distance_m"))),
        _finite(row.get("energy_proxy_wh_mean", row.get("energy_proxy_wh"))),
        _finite(row.get("communication_messages_mean", row.get("communication_messages"))),
        _finite(row.get("runtime_ms_mean", row.get("runtime_ms"))),
    )


def _abstention_gaming_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_problem: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_problem[(str(row["scenario_generator"]), str(row["scenario_variant_id"]), int(row["seed"]))][str(row["method"])] = row
    checks = 0
    violations: list[dict[str, Any]] = []
    oracle_names = ("wrench_oracle", "oracle_wrench_assignment", "wrench_oracle_reference")
    for key, by_method in by_problem.items():
        oracle = next((by_method[name] for name in oracle_names if name in by_method), None)
        if oracle is None:
            continue
        oracle_fp = _float(oracle.get("fp_given_assigned"))
        oracle_coverage = _float(oracle.get("feasible_coverage"))
        if not (np.isfinite(oracle_fp) and np.isfinite(oracle_coverage)):
            continue
        for method, row in by_method.items():
            if method in oracle_names:
                continue
            fp_value = _float(row.get("fp_given_assigned"))
            coverage = _float(row.get("feasible_coverage"))
            if not (np.isfinite(fp_value) and np.isfinite(coverage)):
                continue
            checks += 1
            if fp_value < oracle_fp - 1e-9 and coverage >= oracle_coverage - 1e-9:
                violations.append(
                    {
                        "scenario_generator": key[0],
                        "scenario_variant_id": key[1],
                        "seed": key[2],
                        "method": method,
                        "fp_given_assigned": fp_value,
                        "oracle_fp_given_assigned": oracle_fp,
                        "feasible_coverage": coverage,
                        "oracle_feasible_coverage": oracle_coverage,
                    }
                )
    return {
        "description": "No non-oracle method may claim lower infeasible-assigned rate than the strict oracle while matching or exceeding oracle feasible coverage.",
        "checks": checks,
        "failed_checks": len(violations),
        "passed": len(violations) == 0,
        "violations": violations[:25],
        "truncated_violations": max(0, len(violations) - 25),
    }


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
    meta = sp3_method_metadata(str(row["method"]))
    return (
        "sp3_{scenario}_{owner}_{family}_{scope}_{variant}_{method}_seed{seed}".format(
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
    meta = sp3_method_metadata(str(row["method"]))
    return f"SP3 {row['scenario_generator']} | {meta['title']} | seed {row['seed']}"


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
