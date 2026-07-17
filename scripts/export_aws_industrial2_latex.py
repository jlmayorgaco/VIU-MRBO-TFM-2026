"""Export audited simulator evidence as LaTeX commands."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
RESULTS = WORKSPACE / "results" / "coppeliasim_validation"
DEFAULT_OUTPUT = WORKSPACE / "thesis" / "generated" / "aws-industrial2-results.tex"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def by_policy(path: Path) -> dict[str, dict[str, str]]:
    return {row["policy"]: row for row in csv_rows(path)}


def fmt(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def scientific_tex(value: float) -> str:
    mantissa, exponent = f"{float(value):.3e}".split("e")
    return rf"{mantissa}\times10^{{{int(exponent)}}}"


def value_range(
    rows: list[dict[str, str]], policy: str, field: str
) -> tuple[float, float]:
    values = [float(row[field]) for row in rows if row["policy"] == policy]
    if not values:
        raise ValueError(f"Missing {field!r} values for policy {policy!r}.")
    return min(values), max(values)


def main() -> int:
    sp0 = by_policy(RESULTS / "aws_dynamic_assignment_sp0" / "aws_assignment_summary.csv")
    c16 = by_policy(
        RESULTS / "aws_heterogeneous_coalitions" / "coalition_summary.csv"
    )
    c17 = by_policy(
        RESULTS
        / "aws_heterogeneous_coalitions_open_center"
        / "coalition_summary.csv"
    )
    c18 = by_policy(
        RESULTS
        / "aws_heterogeneous_coalitions_continuous_tfm"
        / "coalition_summary.csv"
    )

    comparison = RESULTS / "aws_industrial2_method_comparison_pilot"
    comparison_summary = csv_rows(comparison / "multiscenario_summary.csv")
    comparison_runs = csv_rows(comparison / "multiscenario_runs.csv")
    comparison_manifest = json.loads(
        (comparison / "manifest.json").read_text(encoding="utf-8")
    )

    scene = RESULTS / "aws_industrial_adversarial_industrial2"
    layout = json.loads((scene / "layout_validation.json").read_text(encoding="utf-8"))
    scene_manifest = csv_rows(scene / "manifest.csv")[0]
    video = json.loads((scene / "aws_industrial2_demo.json").read_text(encoding="utf-8"))

    assert len(comparison_runs) == 32
    assert int(comparison_manifest["seeds_per_scenario"]) == 2
    assert bool(comparison_manifest["sampled_collision_free"])
    assert all(int(row["quota_violations"]) == 0 for row in comparison_runs)
    assert all(
        int(row["sampled_guard_interventions"]) == 0 for row in comparison_runs
    )
    assert layout["status"] == "ok"
    assert int(layout["collision_count"]) == 0
    assert int(layout["support_violation_count"]) == 0
    assert video["status"] == "ok"

    open_rows = [row for row in comparison_summary if row["scenario"] == "open_center"]
    congested_rows = [
        row for row in comparison_summary if row["scenario"] != "open_center"
    ]
    assert all(float(row["delivered_mean"]) == 0.0 for row in congested_rows)
    open_lookup = {row["policy"]: row for row in open_rows}

    predictive_deadlock = value_range(
        comparison_summary,
        "distributed_predictive_cbf_proxy",
        "deadlock_fraction_mean",
    )
    replicator_deadlock = value_range(
        comparison_summary, "replicator_cbf_tfm", "deadlock_fraction_mean"
    )
    central_cpu = value_range(
        comparison_summary, "central_milp_global_preview", "cpu_time_s_mean"
    )
    predictive_cpu = value_range(
        comparison_summary, "distributed_predictive_cbf_proxy", "cpu_time_s_mean"
    )

    max_safe = max(float(row["max_safe_barrier_residual"]) for row in comparison_runs)
    max_exec = max(float(row["max_exec_barrier_residual"]) for row in comparison_runs)
    safe_violations = sum(
        int(row["safe_barrier_violations"]) for row in comparison_runs
    )

    commands: dict[str, Any] = {
        "AwsPilotRuns": len(comparison_runs),
        "AwsPilotSeeds": comparison_manifest["seeds_per_scenario"],
        "AwsPilotScenarios": len(comparison_manifest["scenarios"]),
        "AwsPilotMethods": len(comparison_manifest["policies"]),
        "AwsPilotHorizon": fmt(comparison_manifest["horizon_s"], 0),
        "AwsOpenCentralDeliveries": fmt(
            open_lookup["central_milp_global_preview"]["delivered_mean"], 2
        ),
        "AwsOpenAuctionDeliveries": fmt(
            open_lookup["cbba_reciprocal_proxy"]["delivered_mean"], 2
        ),
        "AwsOpenPredictiveDeliveries": fmt(
            open_lookup["distributed_predictive_cbf_proxy"]["delivered_mean"], 2
        ),
        "AwsOpenTfmDeliveries": fmt(
            open_lookup["replicator_cbf_tfm"]["delivered_mean"], 2
        ),
        "AwsPredictiveDeadlockMin": fmt(predictive_deadlock[0]),
        "AwsPredictiveDeadlockMax": fmt(predictive_deadlock[1]),
        "AwsTfmDeadlockMin": fmt(replicator_deadlock[0]),
        "AwsTfmDeadlockMax": fmt(replicator_deadlock[1]),
        "AwsCentralCpuMin": fmt(central_cpu[0], 2),
        "AwsCentralCpuMax": fmt(central_cpu[1], 2),
        "AwsPredictiveCpuMin": fmt(predictive_cpu[0], 2),
        "AwsPredictiveCpuMax": fmt(predictive_cpu[1], 2),
        "AwsSampledStaticCollisions": sum(
            int(row["static_collision_violations"]) for row in comparison_runs
        ),
        "AwsSampledDynamicCollisions": sum(
            int(row["dynamic_collision_violations"]) for row in comparison_runs
        ),
        "AwsSampledGuardInterventions": sum(
            int(row["sampled_guard_interventions"]) for row in comparison_runs
        ),
        "AwsSafeBarrierViolations": safe_violations,
        "AwsMaxSafeBarrierResidual": scientific_tex(max_safe),
        "AwsMaxExecBarrierResidual": scientific_tex(max_exec),
        "AwsSceneObjects": scene_manifest["object_count"],
        "AwsSceneRobots": scene_manifest["robots"],
        "AwsSceneActiveLoads": scene_manifest["active_loads"],
        "AwsSceneQueuedLoads": scene_manifest["queued_loads"],
        "AwsSceneLayoutCollisions": layout["collision_count"],
        "AwsSceneSupportViolations": layout["support_violation_count"],
        "AwsSceneSensingRadius": fmt(layout["sensing_radius_m"], 1),
        "AwsSceneCommunicationRadius": fmt(layout["communication_radius_m"], 1),
        "AwsDemoSimulationSeconds": fmt(video["simulation_duration_s"], 0),
        "AwsDemoDeliveries": video["max_deliveries"],
        "AwsDemoFailureSeen": r"s{\'i}" if video["failure_seen"] else "no",
    }

    policies = {
        "CFifteen": (sp0, ["hungarian_centralized", "distributed_greedy", "replicator_distributed", "random_feasible"]),
        "CSixteen": (c16, ["milp_coalition_oracle", "greedy_coalition", "replicator_coalition_distributed", "random_coalition"]),
        "CSeventeen": (c17, ["milp_coalition_oracle", "greedy_coalition", "replicator_coalition_distributed", "random_coalition"]),
        "CEighteen": (c18, ["milp_coalition_oracle", "greedy_coalition", "replicator_coalition_distributed", "random_coalition"]),
    }
    suffixes = ["Central", "Greedy", "Replicator", "Random"]
    for campaign, (table, policy_ids) in policies.items():
        for suffix, policy in zip(suffixes, policy_ids, strict=True):
            commands[f"Aws{campaign}{suffix}"] = fmt(table[policy]["delivered_mean"])

    lines = [
        "% Generated from versioned simulator summaries.",
        "% Do not edit numerical values manually.",
        *[rf"\newcommand{{\{name}}}{{{value}}}" for name, value in commands.items()],
        "",
    ]
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(DEFAULT_OUTPUT), "macros": len(commands)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
