"""Reproducible experiment for canonical SP1 coalition formation."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml

from viu_mrob_tfm.sp1_canonical.model import (
    FormationWorld,
    assignment_records,
    bid_matrix,
    distributed_gossip_matching,
    evaluate_assignment,
    generate_world,
    greedy_matching,
    pair_cost_matrix,
    solve_central_milp,
)


METHODS = (
    "local_gossip",
    "local_no_gossip",
    "local_no_switch_penalty",
    "global_greedy",
    "central_milp",
)

METHOD_LABELS = {
    "local_gossip": "Gossip local",
    "local_no_gossip": "Sin gossip",
    "local_no_switch_penalty": "Sin coste de cambio",
    "global_greedy": "Greedy global",
    "central_milp": "Oráculo MILP",
}


def execute(config_path: str | Path, *, smoke: bool = False) -> dict[str, Any]:
    return run_sp1_config(config_path, smoke=smoke)


def run_sp1_config(config_path: str | Path, *, smoke: bool = False) -> dict[str, Any]:
    path = Path(config_path)
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    _validate_config(config)
    experiment_id = str(config["experiment_id"])
    output_dir = Path(config.get("output_dir", f"results/sp1_canonical/{experiment_id}"))
    for subdir in ("raw", "processed", "tables", "figures"):
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)

    regimes = [str(value) for value in config["regimes"]]
    fleet_sizes = [int(value) for value in config["fleet_sizes"]]
    load_counts = [int(value) for value in config["load_counts"]]
    seeds = _expand_seeds(config["seeds"])
    network_cases = [dict(value) for value in config["network_cases"]]
    if smoke:
        regimes = regimes[:1]
        fleet_sizes = fleet_sizes[:1]
        load_counts = load_counts[:1]
        seeds = seeds[:2]
        network_cases = network_cases[:1]

    weights = {str(key): float(value) for key, value in config["cost_weights"].items()}
    oracle_time_limit_s = float(config.get("oracle_time_limit_s", 10.0))
    bootstrap_resamples = int(config.get("bootstrap_resamples", 2000))

    run_rows: list[dict[str, Any]] = []
    robot_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    world_rows: list[dict[str, Any]] = []

    for regime in regimes:
        for n_robots in fleet_sizes:
            for n_loads in load_counts:
                for seed in seeds:
                    world = generate_world(regime, n_robots, n_loads, seed)
                    canonical_costs, _ = pair_cost_matrix(world, weights)
                    canonical_scores = bid_matrix(world, canonical_costs)
                    oracle_start = perf_counter()
                    oracle = solve_central_milp(world, canonical_costs, time_limit_s=oracle_time_limit_s)
                    oracle_runtime_ms = 1000.0 * (perf_counter() - oracle_start)
                    oracle_eval = evaluate_assignment(world, oracle.assignment, canonical_costs)
                    oracle_value = float(oracle_eval["social_value"])
                    world_rows.append(_world_record(world, oracle, oracle_eval))

                    for network_case in network_cases:
                        case_name = str(network_case["name"])
                        radius_m = float(network_case["radius_m"])
                        rounds = int(network_case["gossip_rounds"])
                        for method in METHODS[:3]:
                            method_costs = canonical_costs
                            method_scores = canonical_scores
                            applied_rounds = rounds
                            if method == "local_no_gossip":
                                applied_rounds = 0
                            elif method == "local_no_switch_penalty":
                                method_costs, _ = pair_cost_matrix(world, weights, switch_penalty=0.0)
                                method_scores = bid_matrix(world, method_costs)
                            start = perf_counter()
                            distributed = distributed_gossip_matching(
                                world,
                                method_scores,
                                radius_m=radius_m,
                                rounds=applied_rounds,
                            )
                            runtime_ms = 1000.0 * (perf_counter() - start)
                            method_name = f"{method}__{case_name}"
                            _record_run(
                                run_rows,
                                robot_rows,
                                load_rows,
                                world,
                                method_name=method_name,
                                method_family=method,
                                assignment=distributed.assignment,
                                canonical_costs=canonical_costs,
                                oracle_value=oracle_value,
                                runtime_ms=runtime_ms,
                                information_scope="neighbors",
                                network_case=case_name,
                                radius_m=radius_m,
                                gossip_rounds=applied_rounds,
                                messages=distributed.messages,
                                bytes_sent=distributed.bytes_sent,
                                mean_view_coverage=distributed.mean_view_coverage,
                                min_view_coverage=distributed.min_view_coverage,
                                network_components=distributed.network_components,
                                solver_status=-1,
                                solver_gap=0.0,
                            )

                    greedy_start = perf_counter()
                    greedy_assignment = greedy_matching(canonical_scores)
                    greedy_runtime_ms = 1000.0 * (perf_counter() - greedy_start)
                    _record_run(
                        run_rows,
                        robot_rows,
                        load_rows,
                        world,
                        method_name="global_greedy",
                        method_family="global_greedy",
                        assignment=greedy_assignment,
                        canonical_costs=canonical_costs,
                        oracle_value=oracle_value,
                        runtime_ms=greedy_runtime_ms,
                        information_scope="global",
                        network_case="global",
                        radius_m=0.0,
                        gossip_rounds=0,
                        messages=0,
                        bytes_sent=0,
                        mean_view_coverage=1.0,
                        min_view_coverage=1.0,
                        network_components=1,
                        solver_status=-1,
                        solver_gap=0.0,
                    )
                    _record_run(
                        run_rows,
                        robot_rows,
                        load_rows,
                        world,
                        method_name="central_milp",
                        method_family="central_milp",
                        assignment=oracle.assignment,
                        canonical_costs=canonical_costs,
                        oracle_value=oracle_value,
                        runtime_ms=oracle_runtime_ms,
                        information_scope="global_oracle",
                        network_case="global",
                        radius_m=0.0,
                        gossip_rounds=0,
                        messages=0,
                        bytes_sent=0,
                        mean_view_coverage=1.0,
                        min_view_coverage=1.0,
                        network_components=1,
                        solver_status=oracle.solver_status,
                        solver_gap=0.0 if not np.isfinite(oracle.mip_gap) else oracle.mip_gap,
                    )

    runs = pd.DataFrame(run_rows)
    robots = pd.DataFrame(robot_rows)
    loads = pd.DataFrame(load_rows)
    worlds = pd.DataFrame(world_rows)
    summary = summarize_runs(runs, bootstrap_resamples=bootstrap_resamples)
    contrasts = paired_contrasts(
        runs,
        network_cases=network_cases,
        bootstrap_resamples=bootstrap_resamples,
    )
    audit = build_audit(
        runs,
        robots,
        loads,
        worlds,
        regimes=regimes,
        fleet_sizes=fleet_sizes,
        load_counts=load_counts,
        seeds=seeds,
        network_cases=network_cases,
    )

    runs.to_csv(output_dir / "raw" / "runs.csv", index=False)
    robots.to_csv(output_dir / "raw" / "assignments.csv", index=False)
    loads.to_csv(output_dir / "raw" / "load_decisions.csv", index=False)
    worlds.to_csv(output_dir / "raw" / "worlds.csv", index=False)
    summary.to_csv(output_dir / "processed" / "summary.csv", index=False)
    contrasts.to_csv(output_dir / "processed" / "paired_contrasts.csv", index=False)
    summary.to_csv(output_dir / "tables" / "sp1_canonical_summary.csv", index=False)
    contrasts.to_csv(output_dir / "tables" / "sp1_canonical_contrasts.csv", index=False)
    (output_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _plot_results(output_dir, runs, summary)
    (output_dir / "audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(
        _build_report(experiment_id, runs, summary, contrasts, audit),
        encoding="utf-8",
    )

    git_commit, git_dirty = _git_state()
    manifest = {
        "experiment_id": experiment_id,
        "canonical_sp": "SP1",
        "protocol_family": str(config["protocol_family"]),
        "config_path": str(path),
        "config_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "output_dir": str(output_dir),
        "worlds": int(len(worlds)),
        "runs": int(len(runs)),
        "regimes": regimes,
        "fleet_sizes": fleet_sizes,
        "load_counts": load_counts,
        "seeds": seeds,
        "network_cases": network_cases,
        "methods": list(METHODS),
        "audit_status": audit["status"],
        "evidence_level": "C-pilot" if "SMOKE" in experiment_id.upper() or smoke else "B-target",
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "gpu_used": False,
        "artifact_sha256": _artifact_hashes(output_dir),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if audit["status"] != "passed" and bool(config.get("fail_on_audit", True)):
        raise RuntimeError(f"Canonical SP1 audit failed; inspect {output_dir / 'audit.json'}")
    return manifest


def _record_run(
    run_rows: list[dict[str, Any]],
    robot_rows: list[dict[str, Any]],
    load_rows: list[dict[str, Any]],
    world: FormationWorld,
    *,
    method_name: str,
    method_family: str,
    assignment: np.ndarray,
    canonical_costs: np.ndarray,
    oracle_value: float,
    runtime_ms: float,
    information_scope: str,
    network_case: str,
    radius_m: float,
    gossip_rounds: int,
    messages: int,
    bytes_sent: int,
    mean_view_coverage: float,
    min_view_coverage: float,
    network_components: int,
    solver_status: int,
    solver_gap: float,
) -> None:
    metrics = evaluate_assignment(world, assignment, canonical_costs)
    denominator = max(abs(float(oracle_value)), 1.0)
    gap = max(0.0, float(oracle_value - metrics["social_value"]) / denominator)
    common = {
        "world_hash": world.world_hash,
        "regime": world.regime,
        "seed": world.seed,
        "event_type": world.event_type,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "n_slots": world.n_slots,
        "method": method_name,
        "method_family": method_family,
        "method_label": METHOD_LABELS[method_family],
        "information_scope": information_scope,
        "network_case": network_case,
        "communication_radius_m": radius_m,
        "gossip_rounds": gossip_rounds,
    }
    run_rows.append(
        {
            **common,
            **{key: value for key, value in metrics.items() if key not in {"load_rows", "slot_counts"}},
            "oracle_social_value": float(oracle_value),
            "optimality_gap": gap,
            "messages": int(messages),
            "bytes_sent": int(bytes_sent),
            "mean_view_coverage": float(mean_view_coverage),
            "min_view_coverage": float(min_view_coverage),
            "network_components": int(network_components),
            "runtime_ms": float(runtime_ms),
            "solver_status": int(solver_status),
            "solver_gap": float(solver_gap),
            "assignment_signature": ";".join(str(int(value)) for value in assignment),
            "status": "completed",
        }
    )
    for record in assignment_records(world, assignment, canonical_costs):
        robot_rows.append({**common, **record})
    for record in metrics["load_rows"]:
        load_rows.append({**common, **record})


def summarize_runs(runs: pd.DataFrame, *, bootstrap_resamples: int) -> pd.DataFrame:
    metrics = (
        "started_loads",
        "waiting_loads",
        "unmet_roles",
        "duplicate_slots",
        "social_value",
        "optimality_gap",
        "switches",
        "abandonments",
        "messages",
        "bytes_sent",
        "mean_view_coverage",
        "runtime_ms",
    )
    rows: list[dict[str, Any]] = []
    for method, group in runs.groupby("method", sort=False):
        first = group.iloc[0]
        row: dict[str, Any] = {
            "method": method,
            "method_label": first["method_label"],
            "information_scope": first["information_scope"],
            "network_case": first["network_case"],
            "n": int(len(group)),
        }
        for index, metric in enumerate(metrics):
            values = group[metric].to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values))
            low, high = _bootstrap_mean_ci(
                values,
                seed=2026072100 + index,
                resamples=bootstrap_resamples,
            )
            row[f"{metric}_ci_low"] = low
            row[f"{metric}_ci_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def paired_contrasts(
    runs: pd.DataFrame,
    *,
    network_cases: list[dict[str, Any]],
    bootstrap_resamples: int,
) -> pd.DataFrame:
    specs: list[tuple[str, str, str, str]] = []
    for case in network_cases:
        name = str(case["name"])
        specs.extend(
            [
                (f"H1-info-start-{name}", "started_loads", f"local_gossip__{name}", f"local_no_gossip__{name}"),
                (f"H1-info-value-{name}", "social_value", f"local_gossip__{name}", f"local_no_gossip__{name}"),
                (f"H1-switch-{name}", "switches", f"local_gossip__{name}", f"local_no_switch_penalty__{name}"),
            ]
        )
    specs.append(("H1-gap-oracle", "social_value", str(runs[runs["method_family"] == "local_gossip"].iloc[0]["method"]), "central_milp"))
    rows: list[dict[str, Any]] = []
    for index, (identifier, metric, method_a, method_b) in enumerate(specs):
        selected = runs[runs["method"].isin([method_a, method_b])]
        paired = selected.pivot(index="world_hash", columns="method", values=metric)
        if method_a not in paired or method_b not in paired:
            continue
        paired = paired[[method_a, method_b]].dropna()
        differences = paired[method_a].to_numpy(dtype=float) - paired[method_b].to_numpy(dtype=float)
        low, high = _bootstrap_mean_ci(
            differences,
            seed=2026072200 + index,
            resamples=bootstrap_resamples,
        )
        rows.append(
            {
                "id": identifier,
                "metric": metric,
                "method_a": method_a,
                "method_b": method_b,
                "n_pairs": int(len(differences)),
                "effect_a_minus_b": float(np.mean(differences)) if differences.size else 0.0,
                "ci95_low": low,
                "ci95_high": high,
                "analysis_status": "descriptive_pilot",
            }
        )
    return pd.DataFrame(rows)


def build_audit(
    runs: pd.DataFrame,
    robots: pd.DataFrame,
    loads: pd.DataFrame,
    worlds: pd.DataFrame,
    *,
    regimes: list[str],
    fleet_sizes: list[int],
    load_counts: list[int],
    seeds: list[int],
    network_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_worlds = len(regimes) * len(fleet_sizes) * len(load_counts) * len(seeds)
    expected_methods = 3 * len(network_cases) + 2
    expected_runs = expected_worlds * expected_methods
    paired_counts = runs.groupby("world_hash")["method"].nunique()
    numeric_columns = [
        "started_loads",
        "waiting_loads",
        "unmet_roles",
        "duplicate_slots",
        "social_value",
        "optimality_gap",
        "messages",
        "bytes_sent",
        "runtime_ms",
    ]
    numeric = runs[numeric_columns].to_numpy(dtype=float)
    oracle_loads = loads[loads["method"] == "central_milp"]
    full_view_local = runs[
        (runs["method_family"] == "local_gossip")
        & np.isclose(runs["mean_view_coverage"], 1.0)
    ]
    greedy_signatures = runs[runs["method"] == "global_greedy"].set_index("world_hash")["assignment_signature"]
    full_view_consistent = all(
        greedy_signatures.get(row.world_hash, "") == row.assignment_signature
        for row in full_view_local.itertuples()
    )
    checks = {
        "expected_world_count": bool(len(worlds) == expected_worlds),
        "expected_run_count": bool(len(runs) == expected_runs),
        "paired_method_count": bool((paired_counts == expected_methods).all()),
        "finite_primary_metrics": bool(np.isfinite(numeric).all()),
        "no_invalid_role_assignments": bool((runs["invalid_assignments"] == 0).all()),
        "one_record_per_robot_and_run": bool(
            len(robots) == int(runs["n_robots"].sum())
        ),
        "oracle_all_or_none": bool((oracle_loads["decision"] != "wait").all()),
        "oracle_has_no_duplicate_slots": bool(
            (runs[runs["method"] == "central_milp"]["duplicate_slots"] == 0).all()
        ),
        "oracle_solver_completed": bool(
            (runs[runs["method"] == "central_milp"]["solver_status"] == 0).all()
        ),
        "full_gossip_matches_global_greedy": bool(full_view_consistent),
        "local_methods_use_neighbor_scope": bool(
            (runs[runs["method_family"].str.startswith("local_")]["information_scope"] == "neighbors").all()
        ),
        "world_hash_unique_per_factor_cell": bool(worlds["world_hash"].nunique() == expected_worlds),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "canonical_sp": "SP1",
        "evidence_level": "C-pilot",
        "worlds": expected_worlds,
        "runs": expected_runs,
        "model_scope": "static heterogeneous role assignment after one failure or priority event",
        "pipeline_state": "OBSERVED--ESTIMATED--RAW--CLOSED--GUARDED; no physical EXECUTED state",
        "not_claimed": (
            "El piloto no demuestra convergencia global ni optimalidad del método local, ejecución "
            "continua sin reloj, factibilidad de wrench planar, movimiento, seguridad ante colisiones, "
            "validez en hardware ni superioridad frente a una implementación CBBA multi-ganador verificada."
        ),
    }


def _world_record(world: FormationWorld, oracle: Any, oracle_eval: dict[str, Any]) -> dict[str, Any]:
    return {
        "world_hash": world.world_hash,
        "regime": world.regime,
        "seed": world.seed,
        "event_type": world.event_type,
        "n_robots": world.n_robots,
        "n_loads": world.n_loads,
        "n_slots": world.n_slots,
        "active_robots": int(np.sum(world.active)),
        "previously_assigned": int(np.sum(world.previous_slot >= 0)),
        "oracle_started_loads": int(oracle_eval["started_loads"]),
        "oracle_social_value": float(oracle_eval["social_value"]),
        "oracle_status": int(oracle.solver_status),
        "oracle_mip_gap": 0.0 if not np.isfinite(oracle.mip_gap) else float(oracle.mip_gap),
    }


def _plot_results(output_dir: Path, runs: pd.DataFrame, summary: pd.DataFrame) -> None:
    labels = [f"{row.method_label}\n{row.network_case}" for row in summary.itertuples()]
    starts = summary["started_loads_mean"].to_numpy(dtype=float)
    start_low = summary["started_loads_ci_low"].to_numpy(dtype=float)
    start_high = summary["started_loads_ci_high"].to_numpy(dtype=float)
    errors = np.vstack([starts - start_low, start_high - starts])
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    positions = np.arange(len(labels))
    ax.bar(positions, starts, color="#1f77b4", alpha=0.86)
    ax.errorbar(positions, starts, yerr=errors, fmt="none", ecolor="black", capsize=3, linewidth=0.9)
    ax.set_xticks(positions, labels, rotation=22, ha="right", fontsize=8)
    ax.set_ylabel("Cargas iniciadas, media")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / "fig-sp1-started-loads.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "figures" / "fig-sp1-started-loads.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for method, group in runs.groupby("method", sort=False):
        first = group.iloc[0]
        ax.scatter(
            float(group["messages"].mean()),
            float(group["optimality_gap"].mean()),
            s=58,
            label=f"{first['method_label']} / {first['network_case']}",
        )
    ax.set_xlabel("Mensajes medios por mundo")
    ax.set_ylabel("Brecha normalizada media respecto al MILP")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(output_dir / "figures" / "fig-sp1-quality-communication.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "figures" / "fig-sp1-quality-communication.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _build_report(
    experiment_id: str,
    runs: pd.DataFrame,
    summary: pd.DataFrame,
    contrasts: pd.DataFrame,
    audit: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {experiment_id}",
            "",
            f"- Canonical subproblem: `SP1`",
            f"- Worlds: `{runs['world_hash'].nunique()}`",
            f"- Runs: `{len(runs)}`",
            f"- Audit: `{audit['status']}`",
            f"- Evidence level: `{audit['evidence_level']}`",
            "",
            "## Resumen por método",
            "",
            "```text",
            summary.to_string(index=False),
            "```",
            "",
            "## Contrastes pareados del piloto",
            "",
            "```text",
            contrasts.to_string(index=False),
            "```",
            "",
            "## Limitación de alcance",
            "",
            str(audit["not_claimed"]),
            "",
        ]
    )


def _validate_config(config: dict[str, Any]) -> None:
    required = {
        "experiment_id",
        "protocol_family",
        "regimes",
        "fleet_sizes",
        "load_counts",
        "seeds",
        "network_cases",
        "methods",
        "cost_weights",
    }
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"Missing canonical SP1 config fields: {missing}")
    methods = tuple(str(value) for value in config["methods"])
    if methods != METHODS:
        raise ValueError(f"Canonical SP1 requires methods in this order: {METHODS}")
    names = [str(case["name"]) for case in config["network_cases"]]
    if len(names) != len(set(names)):
        raise ValueError("network case names must be unique")
    for case in config["network_cases"]:
        if float(case["radius_m"]) <= 0.0 or int(case["gossip_rounds"]) < 0:
            raise ValueError(f"Invalid network case: {case}")


def _expand_seeds(spec: Any) -> list[int]:
    if isinstance(spec, list):
        return [int(value) for value in spec]
    return list(range(int(spec["start"]), int(spec["start"]) + int(spec["count"])))


def _bootstrap_mean_ci(
    values: np.ndarray,
    *,
    seed: int,
    resamples: int,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0, 0.0
    if values.size == 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(values, size=(resamples, values.size), replace=True), axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _git_state() -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return "unknown", True


def _artifact_hashes(output_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            hashes[str(path.relative_to(output_dir)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


__all__ = [
    "METHODS",
    "build_audit",
    "execute",
    "paired_contrasts",
    "run_sp1_config",
    "summarize_runs",
]
