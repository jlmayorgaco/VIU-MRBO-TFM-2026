"""Post-commit validation closure for the immutable V1 quota campaign."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from .campaign_io import (
    git_metadata,
    git_path_matches_commit,
    load_resolved_config,
    parse_junit,
    sha256_file,
    verify_checksum_ledger,
    write_checksums,
    write_json,
    write_parquet_or_empty,
    write_shard,
    write_yaml,
)
from .quota_game_benchmark import (
    _dynamic_pair,
    _make_scalar_world,
    build_full_tasks,
)
from .quota_game_core import (
    AlgorithmResult,
    bernstein_rounding_bound,
    capacities_by_load,
    categorical_round,
    certificate_diagnostics,
    environment_record,
    evaluate_assignment,
    make_manual_quota_world,
    make_quota_graph,
    make_quota_world,
    quota_aware_seed,
    recover_assignment,
    run_primary_method,
    solve_quota_lp,
    stable_hash,
)
from .scale_qpg import (
    RobotLocalState,
    all_world_cost,
    greedy_deficit_seed,
    initialize_markets,
    nearest_compatible_seed,
    random_seed_assignment,
    refresh_robot_sparse_state,
    run_local_recovery,
)


CAMPAIGN = "SP1_TFM_VALIDATION_CLOSURE_v1_1"


def _wilson(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(norm.ppf(0.5 + confidence / 2.0))
    p = successes / total
    denominator = 1.0 + z**2 / total
    center = (p + z**2 / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(p * (1.0 - p) / total + z**2 / (4.0 * total**2))
        / denominator
    )
    return center - half, center + half


def _source_audit(
    repo: Path,
    config: Mapping[str, Any],
    output_dir: Path,
) -> tuple[dict[str, Any], pd.DataFrame]:
    source = repo / str(config["source_results"])
    source_commit = str(config["source_commit"])
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    primary = json.loads(
        (source / "primary_execution_manifest.json").read_text(encoding="utf-8")
    )
    audit = json.loads((source / "audit.json").read_text(encoding="utf-8"))
    checksum_validation = verify_checksum_ledger(
        source,
        source / str(config["postcommit_audit"]["source_checksums"]),
    )
    checksum_validation.to_csv(
        output_dir / "source_checksum_validation.csv",
        index=False,
    )
    config_hash = sha256_file(source / "config_snapshot.yaml")
    frozen_config_hash = sha256_file(
        repo / "experiments/configs/sp1_tfm_final_quota_game_benchmark_v1.yaml"
    )
    selected_hash = sha256_file(source / "selected_parameters.yaml")
    source_config = yaml.safe_load(
        (source / "config_snapshot.yaml").read_text(encoding="utf-8")
    )
    recomputed_task_hash = stable_hash(build_full_tasks(source_config))
    junit = parse_junit(source / "pytest-results.xml")
    expected_tasks = int(config["postcommit_audit"]["expected_tasks"])
    expected_tests = int(config["postcommit_audit"]["expected_tests"])
    source_path_matches = git_path_matches_commit(repo, source_commit, source)
    ancestor = (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
            cwd=repo,
            check=False,
        ).returncode
        == 0
    )
    invalid_legacy = checksum_validation.loc[~checksum_validation["valid"]]
    only_stale_config_hash = bool(
        len(invalid_legacy) == 1
        and invalid_legacy.iloc[0]["file"] == "config_snapshot.yaml"
    )
    source_final_lines = []
    for path in sorted(source.rglob("*")):
        if path.is_file():
            relative = path.relative_to(source).as_posix()
            source_final_lines.append(
                f"{sha256_file(path)}  {config['source_campaign']}/{relative}"
            )
    (output_dir / "checksums_final.sha256").write_text(
        "\n".join(source_final_lines) + "\n",
        encoding="utf-8",
    )
    gates = {
        "source_commit_is_ancestor": ancestor,
        "source_results_match_commit_tree": source_path_matches,
        "tasks_2200_of_2200": (
            int(manifest["runtime"]["tasks_completed"]) == expected_tasks
            and int(manifest["runtime"]["tasks_expected"]) == expected_tasks
            and int(primary["tasks"]) == expected_tasks
        ),
        "tests_203_of_203": (
            int(junit["tests"]) == expected_tests and bool(junit["passed"])
        ),
        "legacy_checksum_mismatch_isolated": only_stale_config_hash,
        "final_source_checksums_recomputed": len(source_final_lines) > 0,
        "committed_config_matches_frozen_config": (
            config_hash == frozen_config_hash
        ),
        "selected_parameters_hash_matches": (
            selected_hash == manifest["selected_parameters_sha256"]
            and selected_hash == primary["selected_parameters_sha256"]
        ),
        "task_manifest_hash_matches": (
            recomputed_task_hash == manifest["task_manifest_hash"]
            and recomputed_task_hash == primary["task_manifest_hash"]
        ),
        "source_precommit_audit_passed": bool(
            manifest["audit_passed_precommit"]
            and all(
                value
                for key, value in audit["gates"].items()
                if key != "git_clean_pending_final_commit"
            )
        ),
        "reconstructable_omitted_csv_hashes": bool(
            checksum_validation.loc[
                checksum_validation["file"].isin(
                    ["all_messages.csv", "all_traces.csv"]
                ),
                ["reconstructed_from_parquet", "valid"],
            ]
            .all(axis=None)
        ),
    }
    payload = {
        "campaign": CAMPAIGN,
        "source_campaign": config["source_campaign"],
        "source_commit": source_commit,
        "source_manifest_embedded_commit": manifest["git"]["commit"],
        "source_manifest_embedded_status": manifest["git"]["status_porcelain"],
        "interpretation": (
            "The embedded V1 manifest remains historical precommit evidence. "
            "The immutable source tree is independently verified at source_commit."
        ),
        "gates": gates,
        "passed": all(gates.values()),
        "historical_discrepancies": {
            "legacy_checksum_ledger_all_valid": bool(
                checksum_validation["valid"].all()
            ),
            "legacy_manifest_config_hash_matches_committed_config": (
                config_hash == manifest["config_sha256"]
            ),
            "legacy_manifest_config_sha256": manifest["config_sha256"],
            "committed_config_sha256": config_hash,
            "classification": (
                "stale precommit config hash; corrected by the V1.1 "
                "post-commit ledger without modifying V1"
            ),
        },
        "source_runtime": manifest["runtime"],
        "source_junit": junit,
        "source_checksums": {
            "entries": int(len(checksum_validation)),
            "valid": int(checksum_validation["valid"].sum()),
            "reconstructed": int(
                checksum_validation["reconstructed_from_parquet"].sum()
            ),
            "final_recomputed_entries": len(source_final_lines),
        },
        "cryptographic_boundary": (
            "A tracked manifest cannot contain the hash of the commit that "
            "contains itself. This audit binds the immutable V1 source commit; "
            "the closure implementation commit and clean final HEAD are checked "
            "after their respective commits."
        ),
    }
    write_json(output_dir / "audit_final.json", payload)
    write_json(output_dir / "audit.json", payload)
    return payload, checksum_validation


def _selected_v1_tasks(
    source_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    eligible = [
        task
        for task in build_full_tasks(source_config)
        if task["experiment"]
        in set(closure_config["seed_attribution"]["experiments"])
    ]
    rng = np.random.default_rng(
        int(closure_config["seed_attribution"]["selection_seed"])
    )
    selected: list[dict[str, Any]] = []
    count = int(closure_config["seed_attribution"]["worlds_per_experiment"])
    for experiment in closure_config["seed_attribution"]["experiments"]:
        candidates = [
            task for task in eligible if task["experiment"] == experiment
        ]
        indexes = np.sort(
            rng.choice(len(candidates), size=min(count, len(candidates)), replace=False)
        )
        selected.extend(candidates[int(index)] for index in indexes)
    return selected


def _seed_from_method(
    world: Any,
    graph: Any,
    label: str,
    config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    seed: int,
) -> tuple[np.ndarray, AlgorithmResult | None]:
    if label == "RandomSeed":
        return random_seed_assignment(world, seed), None
    if label == "NearestCompatibleSeed":
        return nearest_compatible_seed(world), None
    if label == "GreedyDeficitSeed":
        return greedy_deficit_seed(world), None
    if label == "LPSeed":
        lp = solve_quota_lp(world)
        return quota_aware_seed(world, lp.rho), None
    method_map = {
        "Capacity-CBBA": "Capacity-CBBA",
        "Weighted-GRAPE": "Weighted-GRAPE",
        "Weighted-Pair-GRAPE": "Weighted-Pair-GRAPE",
        "QPG-Replicator": "QPG-Replicator-AR",
        "QPG-Logit": "QPG-Logit-AR",
        "Atomic-Quota-Logit": "Atomic-Quota-Logit",
    }
    result = run_primary_method(
        world,
        graph,
        method_map[label],
        config,
        parameters,
        stage="full",
        seed=int(seed),
    )
    if result.rho is not None:
        assignment = quota_aware_seed(world, result.rho)
    elif result.assignment is not None:
        assignment = np.asarray(result.assignment, dtype=int).copy()
    else:
        raise RuntimeError(f"{label} produced no seed")
    return assignment, result


def _seed_task_worker(
    task: Mapping[str, Any],
    source_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    shard_path: str,
) -> str:
    if task["experiment"] == "E7":
        _, world, graph, _, _ = _dynamic_pair(task, source_config)
    else:
        world, graph = _make_scalar_world(task, source_config)
    rows: list[dict[str, Any]] = []
    for index, label in enumerate(closure_config["seed_attribution"]["methods"]):
        started = time.perf_counter()
        assignment, method_result = _seed_from_method(
            world,
            graph,
            str(label),
            source_config,
            parameters,
            seed=int(task["seed"]) + 1009 * (index + 1),
        )
        atomic_time = float(time.perf_counter() - started)
        before = evaluate_assignment(world, assignment)
        first_feasible = atomic_time if before["feasible"] else None
        recovery = recover_assignment(
            world,
            assignment,
            source_config["recovery"],
        )
        termination = float(time.perf_counter() - started)
        after = evaluate_assignment(world, recovery.assignment)
        if first_feasible is None and after["feasible"]:
            first_feasible = termination
        rows.append(
            {
                "experiment": task["experiment"],
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "seed": int(task["seed"]),
                "n": world.n_robots,
                "k": world.n_loads,
                "seed_method": str(label),
                "before_feasible": bool(before["feasible"]),
                "before_distance_m": float(before["distance_total_m"]),
                "before_excess": float(before["excess_upper_total"]),
                "before_deficit": float(before["deficit_total"]),
                "after_feasible": bool(after["feasible"]),
                "after_distance_m": float(after["distance_total_m"]),
                "after_excess": float(after["excess_upper_total"]),
                "after_deficit": float(after["deficit_total"]),
                "all_world_cost": all_world_cost(world, recovery.assignment),
                "robots_reassigned": recovery.robots_reassigned,
                "maximum_chain_length": recovery.maximum_chain_length,
                "mean_chain_length": recovery.mean_chain_length,
                "nodes_expanded": recovery.nodes_expanded,
                "recovery_runtime_s": recovery.runtime_s,
                "augmentations": recovery.loads_repaired,
                "required_chain_gt_2": recovery.maximum_chain_length > 2,
                "recovery_success": recovery.success,
                "recovery_failure_reason": recovery.failure_reason,
                "first_atomic_assignment_time_s": atomic_time,
                "first_feasible_time_s": first_feasible,
                "first_persistent_feasible_time_s": (
                    method_result.first_persistent_feasible_time_s
                    if method_result is not None
                    else None
                ),
                "final_termination_time_s": termination,
                "method_converged": (
                    bool(method_result.converged)
                    if method_result is not None
                    else None
                ),
                "method_censored": (
                    bool(method_result.censored)
                    if method_result is not None
                    else None
                ),
            }
        )
    write_shard(Path(shard_path), {"seed_rows": rows})
    return shard_path


def run_seed_attribution(
    repo: Path,
    source_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    output_dir: Path,
    *,
    workers: int,
    force: bool,
) -> pd.DataFrame:
    tasks = _selected_v1_tasks(source_config, closure_config)
    checkpoint = output_dir / "checkpoints" / "seed_attribution"
    pending = []
    shards = []
    for task in tasks:
        path = checkpoint / f"{stable_hash(task)}.json"
        shards.append(path)
        if force or not path.exists():
            pending.append((task, path))
    if pending:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            futures = [
                pool.submit(
                    _seed_task_worker,
                    task,
                    source_config,
                    closure_config,
                    parameters,
                    str(path),
                )
                for task, path in pending
            ]
            for future in as_completed(futures):
                future.result()
    rows = []
    for path in shards:
        rows.extend(json.loads(path.read_text(encoding="utf-8"))["seed_rows"])
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "seed_attribution.csv", index=False)
    return frame


def _convergence_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    spec = config["convergence"]
    tasks = []
    for n in spec["n_values"]:
        k = int(math.ceil(int(n) / 5))
        for topology in spec["topologies"]:
            for seed in range(
                int(spec["seeds"]["start"]),
                int(spec["seeds"]["start"]) + int(spec["seeds"]["count"]),
            ):
                for method in spec["methods"]:
                    tasks.append(
                        {
                            "n": int(n),
                            "k": k,
                            "topology": str(topology),
                            "seed": int(seed),
                            "method": str(method),
                        }
                    )
    return tasks


def _convergence_worker(
    task: Mapping[str, Any],
    base_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    shard_path: str,
    trace_path: str,
) -> str:
    spec = closure_config["convergence"]
    run_config = copy.deepcopy(base_config)
    stage = "closure_convergence"
    run_config["budgets"][stage] = {
        "max_rounds": int(spec["max_rounds"]),
        "max_wall_time_s": float(spec["max_wall_time_s"]),
        "max_payoff_evaluations": int(spec["max_payoff_evaluations"]),
    }
    run_config["budgets"]["evaluation_round_guard"][stage] = int(
        spec["max_rounds"]
    )
    run_config["budgets"]["evaluation_wall_guard_s"][stage] = float(
        spec["max_wall_time_s"]
    )
    run_config["budgets"]["dwell_rounds"] = int(spec["dwell_rounds"])
    run_config["budgets"]["trace_stride"] = int(spec["trace_stride"])
    world = make_quota_world(
        int(task["n"]),
        int(task["k"]),
        int(task["seed"]),
        run_config,
        capacity_regime=str(spec["capacity_regime"]),
        utilization=float(spec["utilization"]),
        quota_band=str(spec["quota_band"]),
        compatibility_regime=str(spec["compatibility"]),
        world_id=(
            f"a3_n{task['n']}_k{task['k']}_{task['topology']}_"
            f"s{task['seed']}"
        ),
    )
    graph = make_quota_graph(world, str(task["topology"]), run_config)
    result = run_primary_method(
        world,
        graph,
        str(task["method"]),
        run_config,
        parameters,
        stage=stage,
        seed=int(task["seed"]) + int(stable_hash(task["method"])[:8], 16),
    )
    traces = [
        {
            "world_id": world.world_id,
            "world_hash": world.world_hash,
            "method": str(task["method"]),
            "n": int(task["n"]),
            "k": int(task["k"]),
            "topology": str(task["topology"]),
            **row,
        }
        for row in result.traces
    ]
    dwell_values = [int(row.get("dwell", 0)) for row in result.traces]
    first_gate = next(
        (
            int(row["logical_round"])
            for row in result.traces
            if int(row.get("dwell", 0)) >= 1
        ),
        None,
    )
    persistent_gate = (
        int(result.convergence_round) if result.convergence_round is not None else None
    )
    residuals = np.asarray(
        [
            float(
                row.get(
                    "fixed_point_residual",
                    row.get("state_residual", math.nan),
                )
            )
            for row in result.traces
        ],
        dtype=float,
    )
    finite = np.flatnonzero(np.isfinite(residuals))
    terminal_slope = math.nan
    if finite.size >= 2:
        selected = finite[-min(100, finite.size) :]
        terminal_slope = float(
            np.polyfit(np.arange(selected.size), residuals[selected], 1)[0]
        )
    classification = (
        "persistent_convergence"
        if result.converged
        else "transient_gate_crossing"
        if first_gate is not None
        else "nonconvergence"
    )
    summary = {
        "world_id": world.world_id,
        "world_hash": world.world_hash,
        "method": str(task["method"]),
        "n": int(task["n"]),
        "k": int(task["k"]),
        "topology": str(task["topology"]),
        "seed": int(task["seed"]),
        "converged": bool(result.converged),
        "classification": classification,
        "budgeted_terminal_state": not bool(result.converged),
        "transient_gate_crossing": first_gate is not None
        and not bool(result.converged),
        "persistent_convergence": bool(result.converged),
        "first_gate_round": first_gate,
        "persistent_gate_round": persistent_gate,
        "maximum_dwell": max(dwell_values, default=0),
        "required_dwell": int(spec["dwell_rounds"]),
        "logical_rounds": result.logical_rounds,
        "wall_time_s": result.wall_time_s,
        "first_atomic_assignment_time_s": result.first_atomic_assignment_time_s,
        "first_feasible_time_s": result.first_feasible_time_s,
        "first_persistent_feasible_time_s": (
            result.first_persistent_feasible_time_s
        ),
        "final_termination_time_s": result.final_termination_time_s,
        "terminal_state_residual": result.terminal_state_residual,
        "terminal_capacity_residual": result.terminal_quota_residual,
        "terminal_tracking_residual": max(
            result.terminal_consensus_residual,
            result.terminal_price_residual,
        ),
        "terminal_fixed_point_residual": (
            float(residuals[finite[-1]]) if finite.size else math.nan
        ),
        "terminal_slope": terminal_slope,
        "censored": bool(result.censored),
        "censoring_reason": result.censoring_reason,
        "recovery_executed": False,
    }
    pd.DataFrame(traces).to_parquet(
        Path(trace_path),
        index=False,
        compression="zstd",
    )
    write_shard(Path(shard_path), {"summary": summary})
    return shard_path


def run_convergence_validation(
    base_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    parameters: Mapping[str, Any],
    output_dir: Path,
    *,
    workers: int,
    force: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    tasks = _convergence_tasks(closure_config)
    checkpoint = output_dir / "checkpoints" / "convergence"
    checkpoint.mkdir(parents=True, exist_ok=True)
    # Migrate early JSON trace shards produced by the first implementation.
    # The numerical payload is unchanged; only the checkpoint codec changes.
    for summary_path in checkpoint.glob("*.json"):
        trace_path = summary_path.with_suffix(".parquet")
        if trace_path.exists():
            continue
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if "traces" in payload:
            pd.DataFrame(payload["traces"]).to_parquet(
                trace_path,
                index=False,
                compression="zstd",
            )
            write_shard(summary_path, {"summary": payload["summary"]})
    pending = []
    shards: list[tuple[Path, Path]] = []
    for task in tasks:
        summary_path = checkpoint / f"{stable_hash(task)}.json"
        trace_path = summary_path.with_suffix(".parquet")
        shards.append((summary_path, trace_path))
        if force or not summary_path.exists() or not trace_path.exists():
            pending.append((task, summary_path, trace_path))
    if pending:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            futures = [
                pool.submit(
                    _convergence_worker,
                    task,
                    base_config,
                    closure_config,
                    parameters,
                    str(summary_path),
                    str(trace_path),
                )
                for task, summary_path, trace_path in pending
            ]
            for future in as_completed(futures):
                future.result()
    summaries, traces = [], []
    trace_frames = []
    for summary_path, trace_path in shards:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        summaries.append(payload["summary"])
        trace_frames.append(pd.read_parquet(trace_path))
    summary_frame = pd.DataFrame(summaries)
    trace_frame = (
        pd.concat(trace_frames, ignore_index=True)
        if trace_frames
        else pd.DataFrame()
    )
    summary_frame.to_csv(output_dir / "convergence_validation.csv", index=False)
    write_parquet_or_empty(output_dir / "all_traces.parquet", trace_frame)
    return summary_frame, trace_frame


def _controlled_bernstein_state(
    target: float,
    state_index: int,
    seed: int,
    *,
    n: int,
    state_count: int,
) -> tuple[Any, np.ndarray, float]:
    probability = 0.40 + 0.20 * (
        state_index / max(1.0, float(state_count - 1))
    )
    capacities = np.ones(n, dtype=float)
    positions = np.column_stack([np.arange(n, dtype=float), np.zeros(n)])
    load_position = np.asarray([[n / 2.0, 1.0]])
    compatibility = np.ones((n, 1), dtype=bool)
    witness = np.zeros(n, dtype=int)
    mean = n * probability
    variance = n * probability * (1.0 - probability)
    upper = float(n)
    upper_margin = upper - mean
    upper_tail = math.exp(
        -(upper_margin**2)
        / (2.0 * (variance + upper_margin / 3.0))
    )
    desired_lower = max(0.0, float(target) - upper_tail)
    if target >= 1.0 or desired_lower >= 1.0:
        margin = 0.0
    elif desired_lower <= 0.0:
        margin = mean
    else:
        low, high = 0.0, mean
        for _ in range(100):
            midpoint = (low + high) / 2.0
            bound = math.exp(
                -(midpoint**2)
                / (2.0 * (variance + midpoint / 3.0))
            )
            if bound > desired_lower:
                low = midpoint
            else:
                high = midpoint
        margin = (low + high) / 2.0
    lower = max(0.0, mean - margin)
    world = make_manual_quota_world(
        case_id=f"a4_b{target:.3f}_state{state_index}_seed{seed}",
        robot_positions=positions,
        load_positions=load_position,
        capacities=capacities,
        lower_quotas=np.asarray([lower]),
        upper_quotas=np.asarray([upper]),
        compatibility=compatibility,
        witness_assignment=witness,
    )
    rho = np.column_stack(
        [
            np.full(n, probability, dtype=float),
            np.full(n, 1.0 - probability, dtype=float),
        ]
    )
    return world, rho, mean - lower


def run_bernstein_validation(
    config: Mapping[str, Any],
    output_dir: Path,
) -> pd.DataFrame:
    spec = config["bernstein"]
    rows = []
    state_count = int(spec["states_per_band"])
    for band_index, target in enumerate(spec["target_bands"]):
        for state_index in range(state_count):
            seed = int(spec["seed_start"]) + 1000 * band_index + state_index
            world, rho, lower_slack = _controlled_bernstein_state(
                float(target),
                state_index,
                seed,
                n=int(spec["n"]),
                state_count=state_count,
            )
            bound = bernstein_rounding_bound(world, rho)
            rng = np.random.default_rng(seed)
            failures = 0
            for _ in range(int(spec["roundings_per_state"])):
                assignment = categorical_round(world, rho, rng)
                failures += int(not evaluate_assignment(world, assignment)["feasible"])
            rounds = int(spec["roundings_per_state"])
            frequency = failures / rounds
            lower_ci, upper_ci = _wilson(failures, rounds)
            observed_bound = float(bound["union_failure_bound"])
            rows.append(
                {
                    "target_band": float(target),
                    "state_index": state_index,
                    "world_id": world.world_id,
                    "seed": seed,
                    "roundings": rounds,
                    "failures": failures,
                    "failure_frequency": frequency,
                    "wilson_lower": lower_ci,
                    "wilson_upper": upper_ci,
                    "bernstein_bound": observed_bound,
                    "bound_minus_failure": observed_bound - frequency,
                    "bound_violated": frequency
                    > observed_bound + float(spec["tolerance"]),
                    "lower_slack": lower_slack,
                    "upper_slack": float(bound["upper_margin"][0]),
                    "capacity_mean": float(bound["capacity_mean"][0]),
                    "capacity_variance": float(bound["capacity_variance"][0]),
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "bernstein_validation.csv", index=False)
    return frame


def run_gap_decomposition(
    source_dir: Path,
    config: Mapping[str, Any],
    output_dir: Path,
) -> pd.DataFrame:
    theorem = pd.read_csv(source_dir / "theorem_diagnostics.csv")
    worlds = pd.read_csv(source_dir / "worlds.csv")[
        ["world_id", "normalization_scale_m"]
    ] if "normalization_scale_m" in pd.read_csv(
        source_dir / "worlds.csv", nrows=1
    ).columns else None
    # V1 worlds.csv stores the physical totals but not the normalization scale.
    # It is reconstructed from the theorem identity when finite, and marked
    # non-comparable otherwise.
    runs = pd.read_parquet(source_dir / "all_runs.parquet")
    lp = (
        runs.loc[
            (runs["method"] == "LP-raw")
            & (runs["closure"] == "oracle_reference"),
            ["world_id", "distance_total_m"],
        ]
        .drop_duplicates("world_id")
        .rename(columns={"distance_total_m": "lp_lower_bound_m"})
    )
    applicable = theorem.loc[
        theorem["method"].isin(["QPG-Logit-AR", "QPG-Replicator-AR"])
        & theorem["integer_upper_bound_m"].notna()
    ].copy()
    applicable = applicable.merge(lp, on="world_id", how="left")
    scale = (
        applicable["continuous_cost_m"]
        / np.maximum(
            applicable["regularized_primal_normalized"]
            + applicable["entropy"]
            * 0.01,
            1.0e-12,
        )
    )
    # The identity above can be distorted by load cost versus entropy.  Use
    # only positive finite estimates and expose this reconstruction flag.
    applicable["normalization_scale_reconstructed_m"] = scale
    epsilon = float(config["gap"]["denominator_epsilon_m"])
    applicable["J_ref_m"] = np.maximum(
        epsilon,
        np.abs(applicable["lp_lower_bound_m"]),
    )
    applicable["optimization_error_m"] = (
        applicable["optimization_error_normalized"] * scale
    )
    applicable["entropy_bias_bound_m"] = (
        applicable["entropy_bias_bound_normalized"] * scale
    )
    applicable["signed_atomic_delta_m"] = (
        applicable["integer_upper_bound_m"] - applicable["continuous_cost_m"]
    )
    applicable["positive_atomic_delta_m"] = np.maximum(
        0.0,
        applicable["signed_atomic_delta_m"],
    )
    applicable["integer_gap_m"] = (
        applicable["integer_upper_bound_m"] - applicable["lp_lower_bound_m"]
    )
    for numerator in (
        "optimization_error_m",
        "entropy_bias_bound_m",
        "positive_atomic_delta_m",
        "integer_gap_m",
    ):
        applicable[numerator.replace("_m", "_over_J_ref")] = (
            applicable[numerator] / applicable["J_ref_m"]
        )
    finite_columns = [
        "optimization_error_m",
        "entropy_bias_bound_m",
        "positive_atomic_delta_m",
        "integer_gap_m",
        "J_ref_m",
        "normalization_scale_reconstructed_m",
    ]
    applicable["comparable"] = (
        np.isfinite(applicable[finite_columns]).all(axis=1)
        & (applicable["normalization_scale_reconstructed_m"] > 0.0)
        & (applicable["optimization_error_m"] >= -1.0e-7)
        & (applicable["entropy_bias_bound_m"] >= -1.0e-7)
    )
    tolerance = float(config["gap"]["numerical_tolerance"])
    applicable["decomposition_rhs_m"] = (
        applicable["optimization_error_m"]
        + applicable["entropy_bias_bound_m"]
        + applicable["positive_atomic_delta_m"]
    )
    applicable["inequality_holds"] = np.where(
        applicable["comparable"],
        applicable["integer_gap_m"]
        <= applicable["decomposition_rhs_m"] + tolerance,
        pd.NA,
    )
    columns = [
        "experiment",
        "world_id",
        "method",
        "lp_lower_bound_m",
        "integer_upper_bound_m",
        "continuous_cost_m",
        "J_ref_m",
        "optimization_error_m",
        "entropy_bias_bound_m",
        "positive_atomic_delta_m",
        "signed_atomic_delta_m",
        "integer_gap_m",
        "optimization_error_over_J_ref",
        "entropy_bias_bound_over_J_ref",
        "positive_atomic_delta_over_J_ref",
        "integer_gap_over_J_ref",
        "comparable",
        "decomposition_rhs_m",
        "inequality_holds",
        "normalization_scale_reconstructed_m",
    ]
    result = applicable[columns]
    result.to_csv(output_dir / "gap_decomposition.csv", index=False)
    return result


def _dynamic_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    spec = config["dynamic_locality"]
    tasks = []
    event_map = {"robot_failure": "committed_robot_failure"}
    for event in spec["events"]:
        for seed in range(
            int(spec["seeds"]["start"]),
            int(spec["seeds"]["start"]) + int(spec["seeds"]["count"]),
        ):
            tasks.append(
                {
                    "kind": "dynamic",
                    "experiment": "A7",
                    "n": int(spec["n"]),
                    "k": int(spec["k"]),
                    "seed": int(seed),
                    "capacity_regime": str(spec["capacity_regime"]),
                    "utilization": float(spec["utilization"]),
                    "quota_band": str(spec["quota_band"]),
                    "compatibility": "arrival_radius",
                    "topology": str(spec["topology"]),
                    "event": event_map.get(str(event), str(event)),
                    "reported_event": str(event),
                    "methods": [],
                    "suffix": str(event),
                }
            )
    return tasks


def _dynamic_worker(
    task: Mapping[str, Any],
    base_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    shard_path: str,
) -> str:
    initial, world, graph, commitment, detail = _dynamic_pair(task, base_config)
    if (
        task["reported_event"] == "robot_failure"
        and detail.get("affected_robot") is not None
    ):
        commitment[int(detail["affected_robot"])] = world.idle_index
    if not evaluate_assignment(initial, np.asarray(initial.witness_assignment))[
        "feasible"
    ]:
        raise RuntimeError("event was injected without a valid pre-event state")
    markets = initialize_markets(
        world,
        commitment,
        rho_minus=30.0,
        rho_plus=40.0,
    )
    robot_states = [
        RobotLocalState(
            robot_id=robot,
            commitment=int(commitment[robot]),
            previous_assignment=int(commitment[robot]),
        )
        for robot in range(world.n_robots)
    ]
    for state in robot_states:
        refresh_robot_sparse_state(
            world,
            markets,
            state,
            maximum_size=6,
            gamma_switch=0.0,
        )
    active_sets = [state.active_set for state in robot_states]
    affected = []
    if detail.get("affected_load") is not None:
        affected.append(int(detail["affected_load"]))
    if detail.get("affected_robot") is not None:
        previous_load = int(
            np.asarray(initial.witness_assignment)[int(detail["affected_robot"])]
        )
        if previous_load < world.n_loads:
            affected.append(previous_load)
    rows = []
    for variant in closure_config["dynamic_locality"]["recovery_variants"]:
        options = dict(base_config["recovery"])
        if variant == "local_recourse":
            options["recourse_weight_m"] = float(
                closure_config["dynamic_locality"]["recourse_penalty"]
            ) * world.normalization_scale_m
        started = time.perf_counter()
        result = run_local_recovery(
            world,
            commitment,
            active_sets,
            options,
            affected_loads=affected,
            radius=int(closure_config["dynamic_locality"]["local_radius"]),
            maximum_chain_length=int(
                closure_config["dynamic_locality"]["max_chain_length"]
            ),
            previous_assignment=commitment,
            global_scope=variant == "global",
        )
        elapsed = float(time.perf_counter() - started)
        final = evaluate_assignment(
            world,
            result.recovery.assignment,
            previous_assignment=commitment,
        )
        old_loads = set(
            map(int, commitment[commitment < initial.n_loads])
        ) - set(affected)
        unchanged = 0
        for load in old_loads:
            before = set(map(int, np.flatnonzero(commitment == load)))
            after = set(
                map(int, np.flatnonzero(result.recovery.assignment == load))
            )
            unchanged += int(before == after)
        route_hops = int(
            sum(
                graph.market_route_hops[load, robot]
                for load in result.universe.loads
                for robot in result.universe.robots
                if world.compatibility[robot, load]
            )
        )
        bytes_total = route_hops * (2 * 8 + 5 * 8)
        rows.append(
            {
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "seed": int(task["seed"]),
                "event": str(task["reported_event"]),
                "recovery_variant": str(variant),
                "pre_event_integer_feasible": True,
                "post_event_feasible": bool(final["feasible"]),
                "time_to_feasibility_s": elapsed
                if final["feasible"]
                else None,
                "recourse": int(final["recourse_hamming"]),
                "loads_touched": len(result.touched_loads),
                "robots_touched": len(result.touched_robots),
                "unaffected_coalition_integrity": (
                    unchanged / len(old_loads) if old_loads else 1.0
                ),
                "distance_after_m": float(final["distance_total_m"]),
                "bytes": bytes_total,
                "fallback_global_used": False,
                "locality_respected": bool(result.locality_respected),
                "universe_loads": len(result.universe.loads),
                "universe_robots": len(result.universe.robots),
                "global_scope": bool(result.universe.is_global),
                "maximum_chain_length": result.recovery.maximum_chain_length,
                "nodes_expanded": result.recovery.nodes_expanded,
                "failure_reason": result.recovery.failure_reason,
            }
        )
    write_shard(Path(shard_path), {"dynamic_rows": rows})
    return shard_path


def run_dynamic_locality(
    base_config: Mapping[str, Any],
    closure_config: Mapping[str, Any],
    output_dir: Path,
    *,
    workers: int,
    force: bool,
) -> pd.DataFrame:
    tasks = _dynamic_tasks(closure_config)
    checkpoint = output_dir / "checkpoints" / "dynamic"
    pending, shards = [], []
    for task in tasks:
        path = checkpoint / f"{stable_hash(task)}.json"
        shards.append(path)
        if force or not path.exists():
            pending.append((task, path))
    if pending:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            futures = [
                pool.submit(
                    _dynamic_worker,
                    task,
                    base_config,
                    closure_config,
                    str(path),
                )
                for task, path in pending
            ]
            for future in as_completed(futures):
                future.result()
    rows = []
    for path in shards:
        rows.extend(json.loads(path.read_text(encoding="utf-8"))["dynamic_rows"])
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "dynamic_events.csv", index=False)
    return frame


def _paired_seed_summary(seed_frame: pd.DataFrame) -> pd.DataFrame:
    reference = "NearestCompatibleSeed"
    rows = []
    pivot = seed_frame.pivot_table(
        index="world_id",
        columns="seed_method",
        values=["after_feasible", "after_distance_m", "all_world_cost"],
        aggfunc="first",
    )
    for method in sorted(seed_frame["seed_method"].unique()):
        if method == reference:
            continue
        common = pivot.dropna(
            subset=[
                ("all_world_cost", method),
                ("all_world_cost", reference),
            ]
        )
        difference = (
            common[("all_world_cost", method)]
            - common[("all_world_cost", reference)]
        )
        rows.append(
            {
                "comparison": f"{method} vs {reference}",
                "worlds": len(common),
                "median_all_world_cost_difference": float(
                    np.median(difference)
                )
                if len(common)
                else math.nan,
                "method_feasibility": float(
                    seed_frame.loc[
                        seed_frame["seed_method"] == method,
                        "after_feasible",
                    ].mean()
                ),
                "reference_feasibility": float(
                    seed_frame.loc[
                        seed_frame["seed_method"] == reference,
                        "after_feasible",
                    ].mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def _save_figure(fig: Any, output_dir: Path, name: str) -> None:
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figure_dir / f"{name}.png", dpi=180)
    fig.savefig(figure_dir / f"{name}.pdf")
    plt.close(fig)


def generate_closure_figures(
    output_dir: Path,
    seed_frame: pd.DataFrame,
    convergence: pd.DataFrame,
    traces: pd.DataFrame,
    bernstein: pd.DataFrame,
    gap: pd.DataFrame,
    dynamic: pd.DataFrame,
) -> list[str]:
    names: list[str] = []

    def save(fig: Any, name: str) -> None:
        _save_figure(fig, output_dir, name)
        names.append(name)

    order = list(seed_frame["seed_method"].drop_duplicates())
    before = seed_frame.groupby("seed_method")["before_feasible"].mean().reindex(order)
    after = seed_frame.groupby("seed_method")["after_feasible"].mean().reindex(order)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(order))
    ax.bar(x - 0.2, before, width=0.4, label="antes")
    ax.bar(x + 0.2, after, width=0.4, label="después AR")
    ax.set_xticks(x, order, rotation=35, ha="right")
    ax.set_ylabel("Factibilidad")
    ax.legend()
    save(fig, "01_seed_quality_before_after_recovery")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    rates = convergence.groupby("method")["persistent_convergence"].mean()
    ax.bar(rates.index, rates.values)
    ax.tick_params(axis="x", rotation=30)
    ax.set_ylabel("Convergencia persistente")
    save(fig, "02_persistent_convergence")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(after.index, after.values)
    axes[0].tick_params(axis="x", rotation=70)
    axes[0].set_ylabel("Factibilidad recovered")
    costs = seed_frame.groupby("seed_method")["all_world_cost"].median().reindex(order)
    axes[1].bar(costs.index, costs.values)
    axes[1].tick_params(axis="x", rotation=70)
    axes[1].set_ylabel("Mediana all-world cost [m]")
    save(fig, "03_feasibility_all_world_cost")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    feasible = seed_frame[seed_frame["after_feasible"]]
    distances = feasible.groupby("seed_method")["after_distance_m"].median()
    ax.bar(distances.index, distances.values)
    ax.tick_params(axis="x", rotation=35)
    ax.set_ylabel("Distancia mediana [m]")
    save(fig, "04_common_feasible_distance")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    communication = convergence.groupby(["n", "method"])[
        "logical_rounds"
    ].median().unstack()
    communication.plot(ax=ax, marker="o")
    ax.set_ylabel("Rondas (proxy de comunicación V1)")
    save(fig, "05_bytes_vs_n_k")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for method, group in traces.groupby("method"):
        sample = group.groupby("k")["payload_bytes_total"].median()
        ax.plot(sample.index, sample.values, marker="o", label=method)
    ax.set_ylabel("Payload acumulado [bytes]")
    ax.set_xlabel("K")
    ax.legend(fontsize=7)
    save(fig, "06_active_set_size_vs_k")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    recourse = dynamic.groupby("recovery_variant")["recourse"].median()
    ax.bar(recourse.index, recourse.values)
    ax.set_ylabel("Recourse mediano")
    save(fig, "07_dynamic_recourse")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    integrity = dynamic.groupby("recovery_variant")[
        "unaffected_coalition_integrity"
    ].median()
    ax.bar(integrity.index, integrity.values)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Integridad de coaliciones no afectadas")
    save(fig, "08_unaffected_coalition_integrity")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    chains = seed_frame.groupby("maximum_chain_length")["nodes_expanded"].median()
    ax.plot(chains.index, chains.values, marker="o")
    ax.set_xlabel("Longitud máxima de cadena")
    ax.set_ylabel("Nodos expandidos")
    save(fig, "09_augmenting_chain_complexity")

    fig, ax = plt.subplots(figsize=(6, 5.5))
    calibration = bernstein.groupby("target_band").agg(
        bound=("bernstein_bound", "mean"),
        failure=("failure_frequency", "mean"),
    )
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey")
    ax.scatter(calibration["bound"], calibration["failure"])
    ax.set_xlabel("Cota Bernstein")
    ax.set_ylabel("Fallo empírico")
    save(fig, "10_bernstein_calibration")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    comparable = gap[gap["comparable"]]
    medians = comparable[
        [
            "optimization_error_over_J_ref",
            "entropy_bias_bound_over_J_ref",
            "positive_atomic_delta_over_J_ref",
        ]
    ].median()
    axes[0].bar(medians.index, medians.values)
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].set_ylabel("Componente / J_ref")
    axes[1].hist(gap["signed_atomic_delta_m"].dropna(), bins=30)
    axes[1].set_xlabel("Delta atómico firmado [m]")
    save(fig, "11_homogeneous_gap_decomposition")

    fig, ax = plt.subplots(figsize=(7, 5))
    pareto = seed_frame.groupby("seed_method").agg(
        distance=("after_distance_m", "median"),
        recourse=("robots_reassigned", "median"),
        runtime=("recovery_runtime_s", "median"),
    )
    scatter = ax.scatter(
        pareto["distance"],
        pareto["recourse"],
        c=pareto["runtime"],
        cmap="viridis",
    )
    for label, row in pareto.iterrows():
        ax.annotate(label, (row["distance"], row["recourse"]), fontsize=6)
    ax.set_xlabel("Distancia [m]")
    ax.set_ylabel("Recourse")
    fig.colorbar(scatter, ax=ax, label="Runtime AR [s]")
    save(fig, "12_pareto_quality_communication_recourse")
    return names


def _build_report(
    output_dir: Path,
    audit: Mapping[str, Any],
    seed_frame: pd.DataFrame,
    convergence: pd.DataFrame,
    bernstein: pd.DataFrame,
    gap: pd.DataFrame,
    dynamic: pd.DataFrame,
    runtime_s: float,
) -> None:
    seed_summary = (
        seed_frame.groupby("seed_method")
        .agg(
            before_feasibility=("before_feasible", "mean"),
            after_feasibility=("after_feasible", "mean"),
            distance_m=("after_distance_m", "median"),
            recourse=("robots_reassigned", "median"),
            chains_gt2=("required_chain_gt_2", "mean"),
        )
        .round(4)
    )
    convergence_summary = (
        convergence.groupby("method")
        .agg(
            persistent=("persistent_convergence", "mean"),
            transient=("transient_gate_crossing", "mean"),
            censored=("censored", "mean"),
        )
        .round(4)
    )
    lines = [
        f"# {CAMPAIGN}",
        "",
        "## Resultado",
        "",
        (
            "La auditoría independiente del commit V1 "
            f"{'aprobó' if audit['passed'] else 'no aprobó'} todos los gates "
            "post-commit. El manifiesto precommit se conserva sin editar."
        ),
        "",
        "## Atribución semilla–recovery",
        "",
        seed_summary.to_markdown(),
        "",
        (
            "La pregunta causal se responde separando la factibilidad de la "
            "semilla y la ganancia posterior del mismo recovery; no se atribuye "
            "al generador una factibilidad creada por AR."
        ),
        "",
        "## Convergencia real",
        "",
        convergence_summary.to_markdown(),
        "",
        (
            "Los tiempos censurados son tiempos terminales presupuestados, no "
            "tiempos de convergencia. Recovery no participa en A3."
        ),
        "",
        "## Bernstein",
        "",
        (
            f"Se evaluaron {len(bernstein)} estados y "
            f"{int(bernstein['roundings'].sum())} redondeos. La fracción de "
            f"violaciones empíricas fue {bernstein['bound_violated'].mean():.4f}; "
            "las bandas cubren deliberadamente cotas no vacuas y vacuas."
        ),
        "",
        "## Gap homogéneo",
        "",
        (
            f"Filas comparables: {int(gap['comparable'].sum())}/{len(gap)}. "
            "Los tres componentes se expresan en metros y se normalizan por "
            "`J_ref`; el delta firmado se mantiene separado."
        ),
        "",
        "## Dinámica y localidad",
        "",
        dynamic.groupby("recovery_variant")[
            [
                "post_event_feasible",
                "recourse",
                "unaffected_coalition_integrity",
                "locality_respected",
            ]
        ]
        .median(numeric_only=True)
        .round(4)
        .to_markdown(),
        "",
        "## Limitaciones",
        "",
        "- A3 prueba convergencia operacional bajo 12.000 rondas/240 s; no demuestra convergencia global.",
        "- La recuperación local es incompleta fuera de su universo residual.",
        "- La reconstrucción del factor de escala de A5 se marca explícitamente y puede invalidar comparabilidad.",
        "- La mensajería es payload lógico, no tráfico de middleware.",
        "",
        f"Runtime de cierre: {runtime_s:.3f} s.",
    ]
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute_closure(
    *,
    repo: Path,
    config_path: Path,
    workers: int | None = None,
    force: bool = False,
) -> Path:
    started = time.perf_counter()
    closure_config = load_resolved_config(repo, config_path)
    source_dir = repo / str(closure_config["source_results"])
    source_config = yaml.safe_load(
        (source_dir / "config_snapshot.yaml").read_text(encoding="utf-8")
    )
    output_dir = repo / str(closure_config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(output_dir / "config_snapshot.yaml", closure_config)
    parameters = yaml.safe_load(
        (source_dir / "selected_parameters.yaml").read_text(encoding="utf-8")
    )
    write_yaml(output_dir / "selected_parameters.yaml", parameters)
    audit, checksum_validation = _source_audit(
        repo,
        closure_config,
        output_dir,
    )
    worker_count = int(workers or closure_config["parallel_workers"])
    seed_frame = run_seed_attribution(
        repo,
        source_config,
        closure_config,
        parameters,
        output_dir,
        workers=worker_count,
        force=force,
    )
    convergence, traces = run_convergence_validation(
        source_config,
        closure_config,
        parameters,
        output_dir,
        workers=worker_count,
        force=force,
    )
    bernstein = run_bernstein_validation(closure_config, output_dir)
    gap = run_gap_decomposition(
        source_dir,
        closure_config,
        output_dir,
    )
    dynamic = run_dynamic_locality(
        source_config,
        closure_config,
        output_dir,
        workers=worker_count,
        force=force,
    )
    comparisons = _paired_seed_summary(seed_frame)
    comparisons.to_csv(output_dir / "paired_comparisons.csv", index=False)
    censoring = convergence.loc[
        convergence["censored"],
        [
            "world_id",
            "method",
            "logical_rounds",
            "wall_time_s",
            "censoring_reason",
        ],
    ]
    censoring.to_csv(output_dir / "censoring.csv", index=False)
    pd.DataFrame(
        columns=["world_id", "method", "fallback_kind", "reason"]
    ).to_csv(output_dir / "fallbacks.csv", index=False)
    regime = pd.DataFrame(
        [
            {
                "section": "A2",
                "domain": "scalar_quota_seed_attribution",
                "worlds": seed_frame["world_id"].nunique(),
            },
            {
                "section": "A3",
                "domain": "population_convergence_without_recovery",
                "worlds": convergence["world_id"].nunique(),
            },
            {
                "section": "A4",
                "domain": "controlled_bernstein_rounding",
                "worlds": bernstein["world_id"].nunique(),
            },
            {
                "section": "A7",
                "domain": "dynamic_recovery_locality",
                "worlds": dynamic["world_id"].nunique(),
            },
        ]
    )
    regime.to_csv(output_dir / "regime_map.csv", index=False)
    message_validation = pd.DataFrame(
        [
            {
                "section": "A7",
                "rows": len(dynamic),
                "bytes_nonnegative": bool((dynamic["bytes"] >= 0).all()),
                "local_runs_respected": bool(
                    dynamic.loc[
                        ~dynamic["global_scope"],
                        "locality_respected",
                    ].all()
                ),
            }
        ]
    )
    message_validation.to_csv(
        output_dir / "message_accounting_validation.csv",
        index=False,
    )
    all_runs = pd.concat(
        [
            seed_frame.assign(section="A2"),
            convergence.assign(section="A3"),
            bernstein.assign(section="A4"),
            dynamic.assign(section="A7"),
        ],
        ignore_index=True,
        sort=False,
    )
    write_parquet_or_empty(output_dir / "all_runs.parquet", all_runs)
    write_parquet_or_empty(
        output_dir / "all_messages.parquet",
        dynamic[
            ["world_id", "recovery_variant", "bytes", "global_scope"]
        ].rename(columns={"recovery_variant": "method"}),
    )
    figures = generate_closure_figures(
        output_dir,
        seed_frame,
        convergence,
        traces,
        bernstein,
        gap,
        dynamic,
    )
    statistics = {
        "seed_attribution": (
            seed_frame.groupby("seed_method")
            .agg(
                before_feasibility=("before_feasible", "mean"),
                after_feasibility=("after_feasible", "mean"),
                median_distance_m=("after_distance_m", "median"),
                median_recourse=("robots_reassigned", "median"),
                chains_gt2_rate=("required_chain_gt_2", "mean"),
            )
            .reset_index()
            .to_dict("records")
        ),
        "convergence": (
            convergence.groupby("method")
            .agg(
                persistent_rate=("persistent_convergence", "mean"),
                transient_rate=("transient_gate_crossing", "mean"),
                censoring_rate=("censored", "mean"),
            )
            .reset_index()
            .to_dict("records")
        ),
        "bernstein": {
            "states": len(bernstein),
            "roundings": int(bernstein["roundings"].sum()),
            "violation_rate": float(bernstein["bound_violated"].mean()),
        },
        "gap": {
            "rows": len(gap),
            "comparable": int(gap["comparable"].sum()),
            "inequality_holds_when_comparable": bool(
                gap.loc[gap["comparable"], "inequality_holds"].fillna(False).all()
            ),
        },
        "dynamic": (
            dynamic.groupby("recovery_variant")
            .agg(
                feasibility=("post_event_feasible", "mean"),
                median_recourse=("recourse", "median"),
                median_integrity=("unaffected_coalition_integrity", "median"),
            )
            .reset_index()
            .to_dict("records")
        ),
    }
    write_json(output_dir / "statistics.json", statistics)
    runtime = float(time.perf_counter() - started)
    _build_report(
        output_dir,
        audit,
        seed_frame,
        convergence,
        bernstein,
        gap,
        dynamic,
        runtime,
    )
    reproduce = f"""# Reproducción de {CAMPAIGN}

```powershell
$env:PYTHONPATH = "src"
python -m viu_mrob_tfm.cli.run_sp1_validation_closure_v1_1 --mode full --workers {worker_count} --resume
```

Los checkpoints son idempotentes. `--force` recalcula los shards. V1 se lee
en modo inmutable; los dos CSV omitidos se reconstruyen en memoria desde sus
Parquet únicamente para verificar sus hashes.
"""
    (output_dir / "README_REPRODUCE.md").write_text(
        reproduce,
        encoding="utf-8",
    )
    final_manifest = {
        "campaign": CAMPAIGN,
        "schema_version": int(closure_config["schema_version"]),
        "source_campaign": closure_config["source_campaign"],
        "source_commit": closure_config["source_commit"],
        "source_audit_passed": bool(audit["passed"]),
        "config_sha256": sha256_file(output_dir / "config_snapshot.yaml"),
        "selected_parameters_sha256": sha256_file(
            output_dir / "selected_parameters.yaml"
        ),
        "environment": environment_record(),
        "git_at_execution": git_metadata(repo),
        "runtime_s": runtime,
        "workers": worker_count,
        "row_counts": {
            "seed_attribution": len(seed_frame),
            "convergence": len(convergence),
            "convergence_traces": len(traces),
            "bernstein": len(bernstein),
            "gap": len(gap),
            "dynamic": len(dynamic),
        },
        "censoring_count": int(convergence["censored"].sum()),
        "fallback_count": 0,
        "figures": figures,
        "source_checksum_entries": len(checksum_validation),
    }
    write_json(output_dir / "manifest_final.json", final_manifest)
    write_json(output_dir / "manifest.json", final_manifest)
    write_checksums(
        output_dir,
        filename="checksums.sha256",
    )
    return output_dir
