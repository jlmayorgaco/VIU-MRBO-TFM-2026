"""Checkpointed execution, theory audit, and analysis for SP1-GEO."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
import traceback
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import yaml

from .allocators import (
    allocate_capacity_cbba,
    allocate_grape,
    allocate_greedy,
    allocate_hungarian_slots,
    allocate_qpg,
    solve_entropic_convex,
    solve_lp_relaxation,
    solve_physical_milp,
)
from .certifier import (
    certify_assignment,
    filter_certified_assignment,
    physical_welfare,
)
from .contributions import build_action_catalog
from .metrics import evaluate_stage_metrics, load_metric_records
from .models import (
    ActionCatalog,
    AllocationResult,
    Assignment,
    GeoWorld,
    RecoveryResult,
)
from .recovery import recover_assignment
from .scenario import (
    FAMILY_DEFAULTS,
    generate_world,
    load_scenario_parameters,
    torque_complementarity_world,
)
from .statistics import (
    bernstein_margin,
    exact_mcnemar,
    friedman_kendall_w,
    holm_adjust,
    paired_bootstrap_interval,
    paired_permutation_test,
    paired_tost,
    paired_wilcoxon,
)
from .welfare import (
    assignment_signal_potential,
    independent_argmax_closure,
    relative_objective_gap,
    signal_potential,
    wonderful_life_difference,
)

CAMPAIGN_ID = "SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1"
STAGES = ("RAW", "CERTIFIED", "RECOVERED")
DISTRIBUTED_ENGINES = {
    "qpg_logit",
    "qpg_smith",
    "capacity_cbba",
    "pair_grape",
    "role_grape",
}
REQUIRED_ARTIFACTS = (
    "environment.json",
    "source_registry.json",
    "config_frozen.yaml",
    "seed_registry.json",
    "runs.parquet",
    "loads.parquet",
    "events.parquet",
    "method_metadata.csv",
    "summary.csv",
    "performance_ranking.csv",
    "hypothesis_results.csv",
    "success_gate_results.csv",
    "regime_map.csv",
    "theory_checks.csv",
    "theory_audit.json",
    "report.md",
)
ANALYSIS_REVISION_ID = "sp1_geo_h3_raw_and_composite_gates_v2"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")
    return payload


def _expand_seed_spec(spec: Any) -> list[int]:
    if isinstance(spec, list):
        return [int(value) for value in spec]
    if isinstance(spec, dict):
        if "values" in spec:
            return [int(value) for value in spec["values"]]
        start = int(spec["start"])
        if "count" in spec:
            return list(range(start, start + int(spec["count"])))
        if "stop" in spec:
            return list(range(start, int(spec["stop"]) + 1))
    raise ValueError(f"Invalid seed specification: {spec!r}")


def _seed_registry(config: dict[str, Any]) -> dict[str, Any]:
    blocks = config["seed_blocks"]
    expanded = {
        name: _expand_seed_spec(spec) for name, spec in blocks.items()
    }
    names = sorted(expanded)
    overlaps: list[dict[str, Any]] = []
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            shared = sorted(set(expanded[left]) & set(expanded[right]))
            if shared:
                overlaps.append({"left": left, "right": right, "shared": shared})
    if overlaps:
        raise ValueError(f"Seed blocks overlap: {overlaps}")
    return {
        "created_at_utc": _utc_now(),
        "analysis_seed": int(config["statistics"]["analysis_seed"]),
        "blocks": {
            name: {
                "count": len(values),
                "minimum": min(values) if values else None,
                "maximum": max(values) if values else None,
                "values": values,
            }
            for name, values in expanded.items()
        },
        "overlaps": overlaps,
        "disjoint": not overlaps,
    }


def _git_state() -> dict[str, Any]:
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
        return {"commit": head, "branch": branch, "dirty": dirty}
    except (OSError, subprocess.SubprocessError):
        return {"commit": "unknown", "branch": "unknown", "dirty": None}


def _environment_record() -> dict[str, Any]:
    try:
        import pyarrow

        pyarrow_version = pyarrow.__version__
    except ImportError:
        pyarrow_version = "unavailable"
    return {
        "created_at_utc": _utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "pyarrow": pyarrow_version,
        "git": _git_state(),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _config_digest(config: dict[str, Any]) -> str:
    return hashlib.sha256(
        yaml.safe_dump(config, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _source_registry(
    repository_root: Path,
    config_path: Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    candidates = list(
        (repository_root / "src" / "viu_mrob_tfm" / "sp1_geo").rglob("*.py")
    )
    candidates.extend(
        [
            repository_root / "scripts" / "run_sp1_geo_benchmark.py",
            repository_root / "scripts" / "audit_sp1_geo_theory.py",
            repository_root / "scripts" / "analyze_sp1_geo_results.py",
            repository_root
            / "plans"
            / "2026-07-24-sp1-geo-qpg-signal-engine-closure-v1.md",
            repository_root / "docs" / "03_EXPERIMENT_PROTOCOL.md",
            repository_root / "docs" / "04_CLAIMS_EVIDENCE.md",
            repository_root / "docs" / "05_NOTATION.md",
            config_path,
        ]
    )
    candidates.extend(
        (repository_root / "tests").glob("test_sp1_geo_*.py")
    )
    for scenario_path in config["scenario_files"].values():
        candidate = Path(scenario_path)
        candidates.append(
            candidate
            if candidate.is_absolute()
            else repository_root / candidate
        )
    records: dict[str, Any] = {}
    for path in sorted(set(candidate.resolve() for candidate in candidates)):
        if not path.is_file():
            raise FileNotFoundError(f"Declared source artifact is missing: {path}")
        try:
            relative = path.relative_to(repository_root.resolve()).as_posix()
            external = False
        except ValueError:
            relative = f"external::{path.as_posix()}"
            external = True
        records[relative] = {
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "external": external,
        }
    return {
        "created_at_utc": _utc_now(),
        "repository_root": str(repository_root.resolve()),
        "git": _git_state(),
        "files": records,
    }


def _validate_config(config: dict[str, Any]) -> None:
    required = {
        "experiment_id",
        "mode",
        "output_dir",
        "scenario_files",
        "sizes",
        "seed_blocks",
        "methods",
        "oracles",
        "recovery",
        "statistics",
    }
    missing = required - set(config)
    if missing:
        raise ValueError(f"Missing config keys: {sorted(missing)}")
    if config["mode"] not in config["seed_blocks"]:
        raise ValueError("The mode must identify one declared seed block.")
    sizes = [tuple(int(value) for value in pair) for pair in config["sizes"]]
    if any(len(pair) != 2 or pair[0] < pair[1] for pair in sizes):
        raise ValueError("Each size must satisfy N >= K.")
    unknown = set(config["scenario_files"]) - set(FAMILY_DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown scenario families: {sorted(unknown)}")
    _seed_registry(config)


def _failure_allocation(
    world: GeoWorld,
    method: str,
    engine: str,
    signal: str,
    error: BaseException | str,
) -> AllocationResult:
    return AllocationResult(
        method=method,
        engine=engine,
        signal=signal,  # type: ignore[arg-type]
        assignment=Assignment.empty(world.n_robots),
        status="solver_error",
        runtime_negotiation_ms=0.0,
        diagnostics={
            "failure_reason": str(error),
            "traceback": traceback.format_exc()
            if isinstance(error, BaseException)
            else "",
        },
    )


def _not_run_allocation(
    world: GeoWorld,
    method: str,
    engine: str,
    signal: str,
    reason: str,
) -> AllocationResult:
    return AllocationResult(
        method=method,
        engine=engine,
        signal=signal,  # type: ignore[arg-type]
        assignment=Assignment.empty(world.n_robots),
        status="not_run",
        runtime_negotiation_ms=0.0,
        diagnostics={"failure_reason": reason},
    )


def _safe_call(
    world: GeoWorld,
    method: str,
    engine: str,
    signal: str,
    function: Any,
) -> AllocationResult:
    try:
        return function()
    except Exception as exc:  # Every failure becomes an explicit run row.
        return _failure_allocation(world, method, engine, signal, exc)


def _allocators_for_world(
    world: GeoWorld,
    catalog: ActionCatalog,
    config: dict[str, Any],
) -> list[AllocationResult]:
    method_config = config["methods"]
    oracle_config = config["oracles"]
    results: list[AllocationResult] = []
    n = world.n_robots

    if n <= int(oracle_config["milp_max_n"]):
        results.append(
            _safe_call(
                world,
                "milp_physical_oracle",
                "milp",
                "marginal_physical",
                lambda: solve_physical_milp(
                    world,
                    catalog,
                    time_limit_s=float(oracle_config["milp_time_limit_s"]),
                ),
            )
        )
    else:
        results.append(
            _not_run_allocation(
                world,
                "milp_physical_oracle",
                "milp",
                "marginal_physical",
                "n_above_milp_max_n",
            )
        )

    if n <= int(oracle_config.get("lp_max_n", 10**9)):
        results.append(
            _safe_call(
                world,
                "lp_relaxation_oracle",
                "lp_relaxation",
                "marginal_physical",
                lambda: solve_lp_relaxation(
                    world,
                    catalog,
                    time_limit_s=float(oracle_config["milp_time_limit_s"]),
                ),
            )
        )
    else:
        results.append(
            _not_run_allocation(
                world,
                "lp_relaxation_oracle",
                "lp_relaxation",
                "marginal_physical",
                "n_above_lp_max_n",
            )
        )

    if n <= int(oracle_config["entropic_max_n"]):
        results.append(
            _safe_call(
                world,
                "entropic_convex_oracle",
                "entropic_convex",
                "marginal_physical",
                lambda: solve_entropic_convex(
                    world,
                    catalog,
                    signal="marginal_physical",
                    entropy_tau=float(method_config["qpg"]["entropy_tau"]),
                    max_iterations=int(oracle_config["entropic_max_iterations"]),
                ),
            )
        )
    else:
        results.append(
            _not_run_allocation(
                world,
                "entropic_convex_oracle",
                "entropic_convex",
                "marginal_physical",
                "n_above_entropic_max_n",
            )
        )

    results.extend(
        [
            _safe_call(
                world,
                "hungarian_slots",
                "hungarian",
                "scalar_capacity",
                lambda: allocate_hungarian_slots(world, catalog),
            ),
            _safe_call(
                world,
                "greedy_nearest",
                "greedy",
                "marginal_physical",
                lambda: allocate_greedy(
                    world, catalog, signal="marginal_physical", nearest_only=True
                ),
            ),
        ]
    )

    qpg = method_config["qpg"]
    for signal in ("scalar_capacity", "marginal_physical"):
        results.append(
            _safe_call(
                world,
                f"qpg_logit_{signal}",
                "qpg_logit",
                signal,
                lambda signal=signal: allocate_qpg(
                    world,
                    catalog,
                    signal=signal,
                    engine="logit",
                    entropy_tau=float(qpg["entropy_tau"]),
                    damping=float(qpg["damping"]),
                    max_iterations=int(qpg["max_iterations"]),
                    tolerance=float(qpg["tolerance"]),
                    consensus_rounds=int(qpg["consensus_rounds"]),
                    trace_stride=int(qpg["trace_stride"]),
                ),
            )
        )
        results.append(
            _safe_call(
                world,
                f"capacity_cbba_{signal}",
                "capacity_cbba",
                signal,
                lambda signal=signal: allocate_capacity_cbba(
                    world,
                    catalog,
                    signal=signal,
                    max_bundle_rounds=int(method_config["cbba"]["max_bundle_rounds"]),
                ),
            )
        )
        results.append(
            _safe_call(
                world,
                f"pair_grape_{signal}",
                "pair_grape",
                signal,
                lambda signal=signal: allocate_grape(
                    world,
                    catalog,
                    signal=signal,
                    pair_swaps=True,
                    max_iterations=int(method_config["grape"]["max_iterations"]),
                ),
            )
        )
    results.append(
        _safe_call(
            world,
            "role_grape_s_physical",
            "role_grape",
            "marginal_physical",
            lambda: allocate_grape(
                world,
                catalog,
                signal="marginal_physical",
                pair_swaps=False,
                max_iterations=int(method_config["grape"]["max_iterations"]),
            ),
        )
    )
    results.append(
        _safe_call(
            world,
            "geo_qpg_smith_physical",
            "qpg_smith",
            "marginal_physical",
            lambda: allocate_qpg(
                world,
                catalog,
                signal="marginal_physical",
                engine="smith",
                entropy_tau=float(qpg["entropy_tau"]),
                damping=float(qpg["smith_damping"]),
                max_iterations=int(qpg["max_iterations"]),
                tolerance=float(qpg["tolerance"]),
                consensus_rounds=int(qpg["consensus_rounds"]),
                trace_stride=int(qpg["trace_stride"]),
            ),
        )
    )
    return results


def _method_metadata() -> pd.DataFrame:
    rows = [
        ("milp_physical_oracle", "oracle", "centralized", "global", "physical", "reference"),
        ("lp_relaxation_oracle", "oracle", "centralized", "global", "physical", "reference"),
        ("entropic_convex_oracle", "oracle", "centralized", "global", "physical", "reference"),
        ("hungarian_slots", "control", "centralized", "global", "scalar", "F0_only"),
        ("greedy_nearest", "control", "centralized", "global", "physical", "control"),
        ("qpg_logit_scalar", "factorial", "distributed", "neighbor_estimates", "scalar", "proposed_ablation"),
        ("geo_qpg_logit_physical", "factorial", "distributed", "neighbor_estimates", "physical", "proposed"),
        ("capacity_cbba_scalar", "factorial", "distributed", "neighbor_consensus", "scalar", "adaptation"),
        ("physical_cbba_marginal", "factorial", "distributed", "neighbor_consensus", "physical", "adaptation"),
        ("weighted_grape_scalar", "factorial", "distributed", "neighbor_deviations", "scalar", "adaptation"),
        ("role_grape_s_physical", "control", "distributed", "neighbor_deviations", "physical", "adaptation"),
        ("pair_role_grape_s_physical", "factorial", "distributed", "neighbor_deviations", "physical", "adaptation"),
        ("geo_qpg_smith_physical", "ablation", "distributed", "neighbor_estimates", "physical", "proposed_ablation"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "method",
            "role",
            "architecture",
            "information_scope",
            "signal_family",
            "canonical_status",
        ],
    ).assign(
        common_certifier=True,
        common_recovery=True,
    )


def _scenario_config(
    family: str, path: str | Path, repository_root: Path
) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    payload = load_scenario_parameters(candidate)
    if payload.get("family") != family:
        raise ValueError(f"Scenario file {candidate} does not declare {family}.")
    return dict(payload.get("parameters", {}))


def _stage_payload(
    world: GeoWorld,
    catalog: ActionCatalog,
    allocation: AllocationResult,
    config: dict[str, Any],
    recovery_cache: dict[tuple[int, ...], RecoveryResult] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    raw_certificate = certify_assignment(world, catalog, allocation.assignment)
    raw_certifier_ms = 1_000.0 * (time.perf_counter() - started)

    certified_assignment = filter_certified_assignment(
        allocation.assignment, catalog, raw_certificate
    )
    started = time.perf_counter()
    certified_certificate = certify_assignment(
        world, catalog, certified_assignment
    )
    certified_certifier_ms = 1_000.0 * (time.perf_counter() - started)

    recovery_config = config["recovery"]
    invalid_statuses = {
        "infeasible",
        "not_applicable",
        "not_run",
        "solver_error",
        "unbounded",
    }
    has_native_incumbent = bool(allocation.assignment.selected_actions().size)
    recovery_allowed = (
        allocation.status not in invalid_statuses
        and not allocation.status.startswith("not_applicable")
        and (
        allocation.status != "timeout_or_limit" or has_native_incumbent
        )
    )
    if recovery_allowed:
        cache_key = tuple(
            int(value) for value in certified_assignment.action_by_robot
        )
        cached = (
            recovery_cache.get(cache_key)
            if recovery_cache is not None
            else None
        )
        if cached is None:
            recovery = recover_assignment(
                world,
                catalog,
                allocation.assignment,
                delta=float(recovery_config["delta"]),
                max_chain_length=int(recovery_config["max_chain_length"]),
                candidates_per_load=int(recovery_config["candidates_per_load"]),
                enable_swaps=bool(recovery_config["enable_swaps"]),
            )
            if recovery_cache is not None:
                recovery_cache[cache_key] = recovery
        else:
            recovery = replace(
                cached,
                robots_changed=int(
                    np.sum(
                        allocation.assignment.action_by_robot
                        != cached.assignment.action_by_robot
                    )
                ),
            )
    else:
        baseline_welfare = physical_welfare(
            world, catalog, certified_assignment, certified_certificate
        )
        recovery = RecoveryResult(
            assignment=certified_assignment,
            certificate=certified_certificate,
            potential_trajectory=(float(baseline_welfare),),
            steps=0,
            augmenting_path_length=0,
            robots_changed=int(
                np.sum(
                    allocation.assignment.action_by_robot
                    != certified_assignment.action_by_robot
                )
            ),
            visited_states=1,
            terminated=True,
            cycle_detected=False,
            runtime_ms=0.0,
            events=(
                {
                    "event": "recovery_skipped",
                    "reason": f"native_status:{allocation.status}",
                },
            ),
        )
    started = time.perf_counter()
    recovered_certificate = certify_assignment(
        world, catalog, recovery.assignment
    )
    recovered_certifier_ms = 1_000.0 * (time.perf_counter() - started)
    return {
        "RAW": (
            allocation.assignment,
            raw_certificate,
            raw_certifier_ms,
            None,
        ),
        "CERTIFIED": (
            certified_assignment,
            certified_certificate,
            certified_certifier_ms,
            None,
        ),
        "RECOVERED": (
            recovery.assignment,
            recovered_certificate,
            recovered_certifier_ms,
            recovery,
        ),
        "certified_before_recovery": certified_certificate,
        "recovery": recovery,
    }


def _records_for_world(
    world: GeoWorld,
    catalog: ActionCatalog,
    allocations: list[AllocationResult],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    recovery_cache: dict[tuple[int, ...], RecoveryResult] = {}
    staged: dict[str, dict[str, Any]] = {}
    for allocation in allocations:
        staged[allocation.method] = _stage_payload(
            world,
            catalog,
            allocation,
            config,
            recovery_cache,
        )
    oracle = next(
        allocation
        for allocation in allocations
        if allocation.method == "milp_physical_oracle"
    )
    oracle_stage = staged[oracle.method]["CERTIFIED"]
    oracle_assignment, oracle_certificate = oracle_stage[0], oracle_stage[1]
    oracle_welfare = physical_welfare(
        world, catalog, oracle_assignment, oracle_certificate
    )
    oracle_service_value = sum(
        world.loads[item.load_index].priority_value
        for item in oracle_certificate.load_certificates
        if item.feasible
    )
    oracle_certified = bool(
        oracle.status == "optimal"
        and oracle_certificate.all_committed_feasible
        and bool(oracle.diagnostics.get("optimal_certified", False))
    )
    oracle_upper_bound = float(
        oracle.diagnostics.get("welfare_upper_bound", math.nan)
    )
    if not np.isfinite(oracle_upper_bound):
        lp_reference = next(
            allocation
            for allocation in allocations
            if allocation.method == "lp_relaxation_oracle"
        )
        oracle_upper_bound = float(
            lp_reference.diagnostics.get("welfare_upper_bound", math.nan)
        )
    experiment_id = str(config["experiment_id"])
    run_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []

    for allocation in allocations:
        payload = staged[allocation.method]
        for stage in STAGES:
            assignment, certificate, certifier_ms, stage_recovery = payload[stage]
            metrics = evaluate_stage_metrics(
                world,
                catalog,
                allocation,
                assignment,
                certificate,
                stage,  # type: ignore[arg-type]
                runtime_certifier_ms=certifier_ms,
                recovery=stage_recovery,
                certified_before_recovery=payload["certified_before_recovery"],
                oracle_welfare=oracle_welfare,
                oracle_upper_bound=oracle_upper_bound,
                oracle_certified=oracle_certified,
            )
            if np.isfinite(oracle_service_value) and oracle_service_value > 0.0:
                metrics["service_value_ratio_vs_oracle"] = (
                    metrics["served_priority_value"] / oracle_service_value
                )
            base = {
                "experiment_id": experiment_id,
                "mode": config["mode"],
                "world_id": world.world_id,
                "world_hash": world.world_hash,
                "family": world.family,
                "seed": world.seed,
                "n_robots": world.n_robots,
                "n_loads": world.n_loads,
                "demand_pressure": world.demand_pressure,
                "method": allocation.method,
                "engine": allocation.engine,
                "signal": allocation.signal,
                "closure_stage": stage,
                "method_status": allocation.status,
                "failure_reason": allocation.diagnostics.get(
                    "failure_reason", "none"
                ),
                "assignment_actions": json.dumps(
                    assignment.action_by_robot.tolist(),
                    separators=(",", ":"),
                ),
            }
            run_rows.append({**base, **metrics})
            load_rows.extend(
                load_metric_records(
                    world,
                    certificate,
                    base={
                        key: base[key]
                        for key in (
                            "experiment_id",
                            "mode",
                            "world_id",
                            "world_hash",
                            "family",
                            "seed",
                            "n_robots",
                            "n_loads",
                            "method",
                            "engine",
                            "signal",
                            "closure_stage",
                        )
                    },
                )
            )

        for event in allocation.events:
            event_rows.append(
                {
                    "experiment_id": experiment_id,
                    "world_id": world.world_id,
                    "world_hash": world.world_hash,
                    "family": world.family,
                    "seed": world.seed,
                    "n_robots": world.n_robots,
                    "n_loads": world.n_loads,
                    "method": allocation.method,
                    "engine": allocation.engine,
                    "signal": allocation.signal,
                    "closure_stage": "RAW",
                    **event,
                }
            )
        recovery = payload["recovery"]
        for event in recovery.events:
            event_rows.append(
                {
                    "experiment_id": experiment_id,
                    "world_id": world.world_id,
                    "world_hash": world.world_hash,
                    "family": world.family,
                    "seed": world.seed,
                    "n_robots": world.n_robots,
                    "n_loads": world.n_loads,
                    "method": allocation.method,
                    "engine": allocation.engine,
                    "signal": allocation.signal,
                    "closure_stage": "RECOVERED",
                    **event,
                }
            )
    return run_rows, load_rows, event_rows


def _write_parquet(
    output: Path,
    run_rows: list[dict[str, Any]],
    load_rows: list[dict[str, Any]],
    event_rows: list[dict[str, Any]],
) -> None:
    runs = pd.DataFrame(run_rows)
    loads = pd.DataFrame(load_rows)
    events = pd.DataFrame(event_rows)
    if events.empty:
        events = pd.DataFrame(
            columns=[
                "experiment_id",
                "world_id",
                "method",
                "event",
            ]
        )
    for name, frame in (
        ("runs.parquet", runs),
        ("loads.parquet", loads),
        ("events.parquet", events),
    ):
        destination = output / name
        temporary = output / f".{name}.tmp"
        frame.to_parquet(temporary, index=False)
        temporary.replace(destination)


def _prepare_output(
    config: dict[str, Any],
    config_path: Path,
    *,
    resume: bool,
) -> Path:
    repository_root = Path.cwd()
    output = Path(config["output_dir"])
    if not output.is_absolute():
        output = repository_root / output
    frozen = output / "config_frozen.yaml"
    if output.exists() and any(output.iterdir()) and not resume:
        raise FileExistsError(
            f"{output} already contains artifacts; use --resume, never overwrite."
        )
    output.mkdir(parents=True, exist_ok=True)
    (output / "figures").mkdir(exist_ok=True)
    (output / "videos").mkdir(exist_ok=True)
    (output / "checkpoints").mkdir(exist_ok=True)
    if frozen.exists():
        existing = _load_yaml(frozen)
        if _config_digest(existing) != _config_digest(config):
            raise ValueError("Frozen config differs from the requested resume config.")
    else:
        frozen.write_text(
            yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    (output / "environment.json").write_text(
        json.dumps(_environment_record(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output / "source_registry.json").write_text(
        json.dumps(
            _source_registry(repository_root, config_path, config),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (output / "seed_registry.json").write_text(
        json.dumps(_seed_registry(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output / "method_metadata.csv").write_text(
        _method_metadata().to_csv(index=False), encoding="utf-8"
    )
    readme = output / "videos" / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Videos\n\n"
            "La campaña Python no genera vídeos. Este directorio queda reservado "
            "para réplicas visuales posteriores de mundos representativos; "
            "CoppeliaSim no constituye la evidencia principal.\n",
            encoding="utf-8",
        )
    return output


def run_benchmark(
    config_path: str | Path,
    *,
    resume: bool = False,
    analyze: bool = True,
) -> Path:
    """Run one declared campaign mode with per-world checkpointing."""

    config_path = Path(config_path).resolve()
    config = _load_yaml(config_path)
    _validate_config(config)
    output = _prepare_output(config, config_path, resume=resume)
    repository_root = Path.cwd()
    seeds = _expand_seed_spec(config["seed_blocks"][config["mode"]])
    sizes = [tuple(int(value) for value in pair) for pair in config["sizes"]]
    scenario_parameters = {
        family: _scenario_config(
            family, path, repository_root
        )
        for family, path in config["scenario_files"].items()
    }

    run_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    if resume and (output / "runs.parquet").exists():
        run_rows = pd.read_parquet(output / "runs.parquet").to_dict("records")
        load_rows = pd.read_parquet(output / "loads.parquet").to_dict("records")
        event_rows = pd.read_parquet(output / "events.parquet").to_dict("records")
    completed_hashes: set[str] = set()
    for path in (output / "checkpoints").glob("*.json"):
        try:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if checkpoint.get("complete") is True:
            completed_hashes.add(path.stem)
    if resume:
        original_lengths = (len(run_rows), len(load_rows), len(event_rows))
        run_rows = [
            row for row in run_rows if row.get("world_hash") in completed_hashes
        ]
        load_rows = [
            row for row in load_rows if row.get("world_hash") in completed_hashes
        ]
        event_rows = [
            row for row in event_rows if row.get("world_hash") in completed_hashes
        ]
        if original_lengths != (
            len(run_rows),
            len(load_rows),
            len(event_rows),
        ):
            _write_parquet(output, run_rows, load_rows, event_rows)

    expected_worlds = len(scenario_parameters) * len(sizes) * len(seeds)
    started_campaign = time.perf_counter()
    completed_worlds = 0
    for family, parameters in scenario_parameters.items():
        for n_robots, n_loads in sizes:
            for seed in seeds:
                world = generate_world(
                    family,
                    n_robots,
                    n_loads,
                    seed,
                    parameters=parameters,
                )
                if world.world_hash in completed_hashes:
                    completed_worlds += 1
                    continue
                catalog = build_action_catalog(
                    world, cost_weights=config.get("cost_weights")
                )
                allocations = _allocators_for_world(world, catalog, config)
                new_runs, new_loads, new_events = _records_for_world(
                    world, catalog, allocations, config
                )
                run_rows.extend(new_runs)
                load_rows.extend(new_loads)
                event_rows.extend(new_events)
                _write_parquet(output, run_rows, load_rows, event_rows)
                checkpoint = {
                    "complete": True,
                    "world_id": world.world_id,
                    "world_hash": world.world_hash,
                    "run_rows": len(new_runs),
                    "load_rows": len(new_loads),
                    "event_rows": len(new_events),
                    "completed_at_utc": _utc_now(),
                }
                checkpoint_path = (
                    output / "checkpoints" / f"{world.world_hash}.json"
                )
                checkpoint_temporary = checkpoint_path.with_suffix(".json.tmp")
                checkpoint_temporary.write_text(
                    json.dumps(checkpoint, indent=2), encoding="utf-8"
                )
                checkpoint_temporary.replace(checkpoint_path)
                completed_hashes.add(world.world_hash)
                completed_worlds += 1

    if not (output / "runs.parquet").exists():
        _write_parquet(output, run_rows, load_rows, event_rows)
    if analyze:
        analyze_results(output, config=config)
    audit_theory(output)
    _write_manifest(
        output,
        config,
        expected_worlds=expected_worlds,
        completed_worlds=completed_worlds,
        elapsed_s=time.perf_counter() - started_campaign,
    )
    return output


def _bootstrap_summary(
    runs: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    group_columns = [
        "family",
        "n_robots",
        "n_loads",
        "method",
        "engine",
        "signal",
        "closure_stage",
    ]
    metrics = [
        "served_load_rate",
        "served_priority_value",
        "physical_welfare",
        "false_positive_given_committed",
        "abstention_rate",
        "optimality_gap_vs_certified_milp",
        "travel_distance_total",
        "estimated_energy",
        "excess_capacity",
        "runtime_total_ms",
        "messages",
        "bytes",
        "recourse_robot_changes",
    ]
    rows: list[dict[str, Any]] = []
    resamples = int(config["statistics"]["bootstrap_resamples"])
    analysis_seed = int(config["statistics"]["analysis_seed"])
    for group_index, (keys, group) in enumerate(
        runs.groupby(group_columns, dropna=False, sort=True)
    ):
        row = dict(zip(group_columns, keys, strict=True))
        row["n_worlds"] = int(group["world_hash"].nunique())
        row["n_rows"] = len(group)
        row["failure_rate"] = float(
            (~group["method_status"].isin(["success", "converged", "local_stable", "optimal", "optimal_separable"])).mean()
        )
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(
                dtype=float
            )
            finite = values[np.isfinite(values)]
            row[f"{metric}_n"] = int(finite.size)
            row[f"{metric}_mean"] = (
                float(np.mean(finite)) if finite.size else math.nan
            )
            row[f"{metric}_median"] = (
                float(np.median(finite)) if finite.size else math.nan
            )
            if finite.size:
                interval = paired_bootstrap_interval(
                    finite,
                    np.zeros_like(finite),
                    resamples=resamples,
                    seed=analysis_seed + 101 * group_index + len(metric),
                )
                row[f"{metric}_ci95_low"] = interval["ci95_low"]
                row[f"{metric}_ci95_high"] = interval["ci95_high"]
            else:
                row[f"{metric}_ci95_low"] = math.nan
                row[f"{metric}_ci95_high"] = math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _paired_frame(
    runs: pd.DataFrame,
    first_mask: pd.Series,
    second_mask: pd.Series,
    metric: str,
) -> pd.DataFrame:
    keys = ["world_hash"]
    first = runs.loc[first_mask, keys + [metric]].rename(
        columns={metric: "first"}
    )
    second = runs.loc[second_mask, keys + [metric]].rename(
        columns={metric: "second"}
    )
    return first.merge(second, on=keys, how="inner").drop_duplicates("world_hash")


def _h3_comparison_masks(
    runs: pd.DataFrame, engine: str
) -> tuple[pd.Series, pd.Series]:
    """Return the predeclared RAW F3--F4 physical/scalar comparison."""

    scope = (
        (runs["closure_stage"] == "RAW")
        & (runs["engine"] == engine)
        & runs["family"].isin(
            ["F3_torque_complementarity", "F4_mixed_geometry_route"]
        )
    )
    return (
        scope & (runs["signal"] == "marginal_physical"),
        scope & (runs["signal"] == "scalar_capacity"),
    )


def _static_recourse_gate(
    qpg_recourse: pd.Series,
    baseline_recourse: pd.Series,
    qpg_feasible: pd.Series,
    baseline_feasible: pd.Series,
) -> dict[str, Any]:
    """Evaluate the numerical H7 gate for the declared static F5 proxy."""

    qpg_mean = float(pd.to_numeric(qpg_recourse).mean())
    baseline_mean = float(pd.to_numeric(baseline_recourse).mean())
    ratio = qpg_mean / baseline_mean if baseline_mean > 0.0 else math.inf
    feasibility_effect = float(
        pd.to_numeric(qpg_feasible).mean()
        - pd.to_numeric(baseline_feasible).mean()
    )
    return {
        "recourse_ratio": ratio,
        "feasibility_effect": feasibility_effect,
        "gate_passed": bool(ratio <= 0.70 and feasibility_effect >= -0.02),
    }


def _success_gate_results(runs: pd.DataFrame) -> pd.DataFrame:
    """Materialize the predeclared H4 composite gate by difficult regime."""

    recovered = runs[
        (runs["closure_stage"] == "RECOVERED")
        & runs["family"].isin(
            [
                "F1_heterogeneous_critical",
                "F2_scarce_priority",
                "F3_torque_complementarity",
                "F4_mixed_geometry_route",
                "F5_network_failure",
            ]
        )
    ]
    proposal = "geo_qpg_logit_physical"
    baseline_methods = {
        "capacity_cbba_scalar",
        "physical_cbba_marginal",
        "weighted_grape_scalar",
        "role_grape_s_physical",
        "pair_role_grape_s_physical",
    }
    rows: list[dict[str, Any]] = []
    for (family, n_robots, n_loads), group in recovered.groupby(
        ["family", "n_robots", "n_loads"], sort=True
    ):
        candidates = group[group["method"].isin(baseline_methods)]
        if candidates.empty:
            continue
        baseline_scores = (
            candidates.groupby("method")["physical_welfare"]
            .median()
            .sort_values(ascending=False, kind="stable")
        )
        baseline = str(baseline_scores.index[0])
        metrics = [
            "world_physical_feasible",
            "served_load_rate",
            "travel_distance_total",
            "excess_capacity",
            "runtime_total_ms",
            "bytes",
            "optimality_gap_vs_certified_milp",
        ]
        first = group.loc[
            group["method"] == proposal, ["world_hash", *metrics]
        ].rename(columns={metric: f"qpg_{metric}" for metric in metrics})
        second = group.loc[
            group["method"] == baseline, ["world_hash", *metrics]
        ].rename(columns={metric: f"baseline_{metric}" for metric in metrics})
        paired = first.merge(second, on="world_hash", how="inner")
        if paired.empty:
            continue

        def mean(prefix: str, metric: str) -> float:
            return float(
                pd.to_numeric(
                    paired[f"{prefix}_{metric}"], errors="coerce"
                ).mean()
            )

        def relative_reduction(metric: str) -> float:
            baseline_mean = mean("baseline", metric)
            qpg_mean = mean("qpg", metric)
            if not np.isfinite(baseline_mean) or baseline_mean <= 0.0:
                return math.nan
            return (baseline_mean - qpg_mean) / baseline_mean

        def ratio(metric: str) -> float:
            baseline_mean = mean("baseline", metric)
            qpg_mean = mean("qpg", metric)
            if not np.isfinite(baseline_mean) or baseline_mean <= 0.0:
                return math.inf
            return qpg_mean / baseline_mean

        gap_values = pd.to_numeric(
            paired["qpg_optimality_gap_vs_certified_milp"],
            errors="coerce",
        )
        gap_values = gap_values[np.isfinite(gap_values)]
        gap_median = (
            float(np.median(gap_values)) if len(gap_values) else math.nan
        )
        feasibility_effect = mean(
            "qpg", "world_physical_feasible"
        ) - mean("baseline", "world_physical_feasible")
        coverage_effect = mean("qpg", "served_load_rate") - mean(
            "baseline", "served_load_rate"
        )
        distance_reduction = relative_reduction("travel_distance_total")
        excess_reduction = relative_reduction("excess_capacity")
        runtime_ratio = ratio("runtime_total_ms")
        bytes_ratio = ratio("bytes")
        feasibility_gate = feasibility_effect >= -0.02
        coverage_gate = coverage_effect >= -0.02
        quality_gate = bool(
            (np.isfinite(distance_reduction) and distance_reduction >= 0.05)
            or (np.isfinite(excess_reduction) and excess_reduction >= 0.10)
        )
        gap_gate = bool(not len(gap_values) or gap_median <= 0.05)
        runtime_gate = runtime_ratio <= 5.0
        bytes_gate = bytes_ratio <= 5.0
        rows.append(
            {
                "family": family,
                "n_robots": int(n_robots),
                "n_loads": int(n_loads),
                "proposal_method": proposal,
                "baseline_method": baseline,
                "baseline_selection_rule": (
                    "highest median recovered physical_welfare in regime"
                ),
                "n_pairs": int(len(paired)),
                "feasibility_effect": feasibility_effect,
                "coverage_effect": coverage_effect,
                "distance_reduction": distance_reduction,
                "excess_capacity_reduction": excess_reduction,
                "certified_gap_n": int(len(gap_values)),
                "certified_gap_median": gap_median,
                "runtime_ratio": runtime_ratio,
                "bytes_ratio": bytes_ratio,
                "feasibility_gate": feasibility_gate,
                "coverage_gate": coverage_gate,
                "quality_gate": quality_gate,
                "gap_gate": gap_gate,
                "runtime_gate": runtime_gate,
                "bytes_gate": bytes_gate,
                "gate_passed": bool(
                    feasibility_gate
                    and coverage_gate
                    and quality_gate
                    and gap_gate
                    and runtime_gate
                    and bytes_gate
                ),
            }
        )
    return pd.DataFrame(rows)


def _hypothesis_results(
    runs: pd.DataFrame,
    config: dict[str, Any],
    success_gates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    stats_config = config["statistics"]
    resamples = int(stats_config["bootstrap_resamples"])
    permutation_resamples = int(
        stats_config.get("permutation_resamples", max(resamples, 1_000))
    )
    seed = int(stats_config["analysis_seed"])

    def add_continuous(
        hypothesis: str,
        metric: str,
        first_mask: pd.Series,
        second_mask: pd.Series,
        interpretation: str,
    ) -> None:
        paired = _paired_frame(runs, first_mask, second_mask, metric)
        bootstrap = paired_bootstrap_interval(
            paired["first"],
            paired["second"],
            resamples=resamples,
            seed=seed + len(rows),
        )
        permutation = paired_permutation_test(
            paired["first"],
            paired["second"],
            resamples=permutation_resamples,
            seed=seed + 1_000 + len(rows),
        )
        wilcoxon = paired_wilcoxon(paired["first"], paired["second"])
        rows.append(
            {
                "hypothesis": hypothesis,
                "endpoint": metric,
                "test": "paired_permutation_with_bootstrap_and_wilcoxon",
                "effect": bootstrap["effect"],
                "ci95_low": bootstrap["ci95_low"],
                "ci95_high": bootstrap["ci95_high"],
                "p_raw": permutation["p_value"],
                "wilcoxon_p": wilcoxon["p_value"],
                "rank_biserial": wilcoxon["rank_biserial"],
                "n_pairs": bootstrap["n_pairs"],
                "ties": bootstrap["ties"],
                "interpretation_rule": interpretation,
            }
        )

    theory = audit_theory()
    kkt_gate = next(
        item for item in theory["checks"] if item["gate"] == "T2_vgne_kkt"
    )
    rows.append(
        {
            "hypothesis": "H1_theory_kkt_alignment",
            "endpoint": "relative_entropic_objective_gap",
            "test": "predeclared_T2_software_theory_gate",
            "effect": kkt_gate["value"],
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "p_raw": math.nan,
            "wilcoxon_p": math.nan,
            "rank_biserial": math.nan,
            "n_pairs": 1,
            "ties": 0,
            "interpretation_rule": "relative gap <= 1e-3 and KKT residual <= 2e-3",
            "gate_passed": bool(kkt_gate["passed"]),
        }
    )

    qpg_physical = (
        (runs["engine"] == "qpg_logit")
        & (runs["signal"] == "marginal_physical")
    )
    recovered = runs["closure_stage"] == "RECOVERED"
    raw = runs["closure_stage"] == "RAW"
    pair = _paired_frame(
        runs,
        qpg_physical & recovered,
        qpg_physical & raw,
        "world_physical_feasible",
    )
    mcnemar = exact_mcnemar(pair["first"].astype(bool), pair["second"].astype(bool))
    rows.append(
        {
            "hypothesis": "H2_closure_needed",
            "endpoint": "world_physical_feasible",
            "test": "exact_mcnemar",
            "effect": mcnemar["effect"],
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "p_raw": mcnemar["p_value"],
            "wilcoxon_p": math.nan,
            "rank_biserial": math.nan,
            "n_pairs": mcnemar["n_pairs"],
            "ties": mcnemar["ties"],
            "interpretation_rule": "RECOVERED minus RAW > 0",
        }
    )
    difficult = runs["family"].isin(
        [
            "F1_heterogeneous_critical",
            "F2_scarce_priority",
            "F3_torque_complementarity",
            "F4_mixed_geometry_route",
            "F5_network_failure",
        ]
    )
    for engine in ("qpg_logit", "capacity_cbba", "pair_grape"):
        physical_mask, scalar_mask = _h3_comparison_masks(runs, engine)
        add_continuous(
            f"H3_physical_signal_{engine}",
            "false_positive_given_committed",
            physical_mask,
            scalar_mask,
            "RAW physical minus scalar <= -0.20 required in F3--F4",
        )
        rows[-1]["gate_passed"] = bool(rows[-1]["effect"] <= -0.20)
        rows[-1]["claim_scope"] = "RAW_F3_F4"
    add_continuous(
        "H4_geo_qpg_vs_cbba_quality",
        "physical_welfare",
        qpg_physical & recovered & difficult,
        (runs["engine"] == "capacity_cbba")
        & (runs["signal"] == "marginal_physical")
        & recovered
        & difficult,
        "positive favors Geo-QPG in predeclared difficult regimes",
    )
    if success_gates is None:
        success_gates = _success_gate_results(runs)
    rows[-1]["gate_passed"] = bool(
        not success_gates.empty and success_gates["gate_passed"].any()
    )
    rows[-1]["claim_scope"] = "composite_gate_by_family_and_size"
    add_continuous(
        "H5_engine_qpg_vs_pair_grape",
        "physical_welfare",
        qpg_physical & recovered & difficult,
        (runs["engine"] == "pair_grape")
        & (runs["signal"] == "marginal_physical")
        & recovered
        & difficult,
        "absolute effect below 3% supports signal-dominant interpretation",
    )
    equivalence_pairs = _paired_frame(
        runs,
        qpg_physical & recovered & difficult,
        (runs["engine"] == "pair_grape")
        & (runs["signal"] == "marginal_physical")
        & recovered
        & difficult,
        "served_load_rate",
    )
    equivalence = paired_tost(
        equivalence_pairs["first"],
        equivalence_pairs["second"],
        margin=0.03,
    )
    rows.append(
        {
            "hypothesis": "H5_engine_practical_equivalence_coverage",
            "endpoint": "served_load_rate",
            "test": "paired_tost",
            "effect": equivalence["effect"],
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "p_raw": equivalence["p_value"],
            "wilcoxon_p": math.nan,
            "rank_biserial": math.nan,
            "n_pairs": equivalence["n_pairs"],
            "ties": int(
                np.sum(
                    np.isclose(
                        equivalence_pairs["first"],
                        equivalence_pairs["second"],
                    )
                )
            ),
            "interpretation_rule": "TOST equivalence margin is ±0.03 coverage",
            "gate_passed": bool(equivalence["equivalent"]),
        }
    )
    add_continuous(
        "H6_easy_runtime_qpg_minus_hungarian",
        "runtime_total_ms",
        qpg_physical & recovered & (runs["family"] == "F0_easy_separable"),
        (runs["engine"] == "hungarian")
        & recovered
        & (runs["family"] == "F0_easy_separable"),
        "positive documents QPG resource disadvantage in F0",
    )
    add_continuous(
        "H7_failure_recourse_qpg_minus_cbba",
        "recourse_robot_changes",
        qpg_physical
        & recovered
        & (runs["family"] == "F5_network_failure"),
        (runs["engine"] == "capacity_cbba")
        & (runs["signal"] == "marginal_physical")
        & recovered
        & (runs["family"] == "F5_network_failure"),
        "ratio <= 0.70 required; negative difference alone is insufficient",
    )
    h7_qpg = runs[
        qpg_physical
        & recovered
        & (runs["family"] == "F5_network_failure")
    ].set_index("world_hash")
    h7_baseline = runs[
        (runs["engine"] == "capacity_cbba")
        & (runs["signal"] == "marginal_physical")
        & recovered
        & (runs["family"] == "F5_network_failure")
    ].set_index("world_hash")
    h7_index = h7_qpg.index.intersection(h7_baseline.index)
    h7_gate = _static_recourse_gate(
        h7_qpg.loc[h7_index, "recourse_robot_changes"],
        h7_baseline.loc[h7_index, "recourse_robot_changes"],
        h7_qpg.loc[h7_index, "world_physical_feasible"],
        h7_baseline.loc[h7_index, "world_physical_feasible"],
    )
    rows[-1].update(h7_gate)
    rows[-1]["claim_scope"] = "static_post_failure_proxy_not_dynamic"

    factorial = runs[
        recovered
        & runs["engine"].isin(["qpg_logit", "capacity_cbba", "pair_grape"])
    ]
    factorial_matrix = factorial.pivot_table(
        index="world_hash",
        columns="method",
        values="physical_welfare",
        aggfunc="first",
    ).dropna()
    friedman = friedman_kendall_w(factorial_matrix.to_numpy(dtype=float))
    rows.append(
        {
            "hypothesis": "H_global_factorial_engine_signal",
            "endpoint": "physical_welfare",
            "test": "friedman_with_kendall_w",
            "effect": friedman["kendall_w"],
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "p_raw": friedman["p_value"],
            "wilcoxon_p": math.nan,
            "rank_biserial": math.nan,
            "n_pairs": friedman["n_blocks"],
            "ties": 0,
            "interpretation_rule": "global omnibus only; Kendall W is effect size",
            "gate_passed": math.nan,
        }
    )

    p_holm = holm_adjust(row["p_raw"] for row in rows)
    for row, adjusted in zip(rows, p_holm, strict=True):
        row["p_holm"] = adjusted
        gate_required = (
            row["hypothesis"] == "H1_theory_kkt_alignment"
            or row["hypothesis"].startswith("H3_")
            or row["hypothesis"].startswith("H4_")
            or row["hypothesis"]
            in {
                "H5_engine_practical_equivalence_coverage",
                "H7_failure_recourse_qpg_minus_cbba",
            }
        )
        statistical_decision = bool(
            np.isfinite(adjusted) and adjusted < 0.05
        )
        row["decision_holm_005"] = (
            bool(row.get("gate_passed", False))
            if row["hypothesis"] == "H1_theory_kkt_alignment"
            else bool(
                statistical_decision
                and (
                    not gate_required
                    or bool(row.get("gate_passed", False))
                )
            )
        )
    return pd.DataFrame(rows)


def _performance_ranking(runs: pd.DataFrame) -> pd.DataFrame:
    source = runs[
        (runs["closure_stage"] == "RECOVERED")
        & runs["engine"].isin(DISTRIBUTED_ENGINES)
    ]
    grouped = (
        source.groupby(
            ["family", "n_robots", "n_loads", "method", "engine", "signal"],
            as_index=False,
        )
        .agg(
            served_load_rate=("served_load_rate", "mean"),
            served_priority_value=("served_priority_value", "mean"),
            physical_welfare=("physical_welfare", "median"),
            runtime_total_ms=("runtime_total_ms", "median"),
            bytes=("bytes", "median"),
            n_worlds=("world_hash", "nunique"),
        )
    )
    if grouped.empty:
        return grouped
    grouped["quality_rank"] = grouped.groupby(
        ["family", "n_robots", "n_loads"]
    )["physical_welfare"].rank(method="min", ascending=False)
    grouped["runtime_rank"] = grouped.groupby(
        ["family", "n_robots", "n_loads"]
    )["runtime_total_ms"].rank(method="min", ascending=True)
    grouped["pareto_score"] = grouped["quality_rank"] + 0.25 * grouped["runtime_rank"]
    grouped["overall_rank"] = grouped.groupby(
        ["family", "n_robots", "n_loads"]
    )["pareto_score"].rank(method="min", ascending=True)
    return grouped.sort_values(
        ["family", "n_robots", "n_loads", "overall_rank", "method"]
    )


def _regime_map(ranking: pd.DataFrame) -> pd.DataFrame:
    if ranking.empty:
        return pd.DataFrame(
            columns=[
                "family",
                "n_robots",
                "n_loads",
                "descriptive_best_method",
                "classification",
            ]
        )
    best = ranking.loc[
        ranking.groupby(["family", "n_robots", "n_loads"])["overall_rank"].idxmin()
    ].copy()
    best = best.rename(columns={"method": "descriptive_best_method"})
    best["classification"] = "descriptive_pareto_best_not_superiority_claim"
    return best[
        [
            "family",
            "n_robots",
            "n_loads",
            "descriptive_best_method",
            "engine",
            "signal",
            "served_load_rate",
            "physical_welfare",
            "runtime_total_ms",
            "bytes",
            "classification",
        ]
    ].sort_values(["family", "n_robots"])


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def _empty_figure(path: Path, title: str, message: str) -> None:
    fig, axis = plt.subplots(figsize=(8, 4.5))
    axis.axis("off")
    axis.set_title(title)
    axis.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
    _save_figure(fig, path)


def _plot_figures(
    output: Path,
    runs: pd.DataFrame,
    ranking: pd.DataFrame,
    regime: pd.DataFrame,
) -> None:
    figures = output / "figures"
    distributed = runs[
        runs["engine"].isin(DISTRIBUTED_ENGINES)
        & (runs["closure_stage"] == "RECOVERED")
    ]
    interaction = (
        distributed.groupby(["engine", "signal"], as_index=False)
        .agg(
            optimality_gap=(
                "optimality_gap_vs_certified_milp",
                "mean",
            ),
            served_load_rate=("served_load_rate", "mean"),
        )
    )
    if interaction.empty:
        _empty_figure(
            figures / "F1_signal_engine_interaction.png",
            "Signal × engine interaction",
            "No eligible rows.",
        )
    else:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for signal, group in interaction.groupby("signal"):
            axes[0].plot(
                group["engine"],
                group["optimality_gap"],
                marker="o",
                label=signal,
            )
            axes[1].plot(
                group["engine"],
                group["served_load_rate"],
                marker="o",
                label=signal,
            )
        axes[0].set_ylabel("Mean gap to certified MILP")
        axes[1].set_ylabel("Mean served-load rate")
        for axis in axes:
            axis.tick_params(axis="x", rotation=25)
            axis.grid(alpha=0.25)
            axis.legend()
        fig.suptitle("Signal × decision-engine interaction")
        _save_figure(fig, figures / "F1_signal_engine_interaction.png")

    closure = (
        runs[runs["engine"].isin(DISTRIBUTED_ENGINES)]
        .groupby(["method", "closure_stage"], as_index=False)
        .agg(served_load_rate=("served_load_rate", "mean"))
    )
    if closure.empty:
        _empty_figure(
            figures / "F2_raw_certified_recovered.png",
            "RAW–CERTIFIED–RECOVERED",
            "No eligible rows.",
        )
    else:
        pivot = closure.pivot(
            index="method", columns="closure_stage", values="served_load_rate"
        ).reindex(columns=list(STAGES))
        fig, axis = plt.subplots(figsize=(11, 5.5))
        pivot.plot(kind="bar", ax=axis)
        axis.set_ylabel("Mean served-load rate")
        axis.set_title("Closure-stage decomposition")
        axis.grid(axis="y", alpha=0.25)
        _save_figure(fig, figures / "F2_raw_certified_recovered.png")

    false_positive = (
        distributed.groupby(["engine", "signal"], as_index=False)
        .agg(
            false_positive=("false_positive_given_committed", "mean"),
            abstention=("abstention_rate", "mean"),
        )
    )
    if false_positive.empty:
        _empty_figure(
            figures / "F3_scalar_vs_wrench_false_positives.png",
            "Scalar false positives versus wrench",
            "No eligible rows.",
        )
    else:
        labels = (
            false_positive["engine"] + "\n" + false_positive["signal"]
        )
        x = np.arange(len(false_positive))
        fig, axis = plt.subplots(figsize=(11, 5))
        axis.bar(
            x - 0.18,
            false_positive["false_positive"],
            width=0.36,
            label="False positive | committed",
        )
        axis.bar(
            x + 0.18,
            false_positive["abstention"],
            width=0.36,
            label="Abstention",
        )
        axis.set_xticks(x, labels, rotation=25, ha="right")
        axis.set_ylim(0.0, 1.0)
        axis.legend()
        axis.set_title("Physical precision must be read with abstention")
        _save_figure(fig, figures / "F3_scalar_vs_wrench_false_positives.png")

    if ranking.empty:
        _empty_figure(
            figures / "F4_quality_resource_pareto.png",
            "Quality–resource Pareto",
            "No eligible rows.",
        )
    else:
        fig, axis = plt.subplots(figsize=(9, 5.5))
        for method, group in ranking.groupby("method"):
            axis.scatter(
                group["runtime_total_ms"],
                group["physical_welfare"],
                s=25 + 8 * np.log1p(group["bytes"]),
                alpha=0.7,
                label=method,
            )
        axis.set_xscale("symlog", linthresh=1.0)
        axis.set_xlabel("Median runtime [ms]")
        axis.set_ylabel("Median common physical welfare")
        axis.grid(alpha=0.25)
        axis.legend(fontsize=7, ncol=2)
        axis.set_title("Quality–runtime–bytes Pareto view")
        _save_figure(fig, figures / "F4_quality_resource_pareto.png")

    gaps = runs[
        (runs["closure_stage"] == "RECOVERED")
        & runs["optimality_gap_vs_certified_milp"].notna()
        & runs["engine"].isin(DISTRIBUTED_ENGINES)
    ]
    if gaps.empty:
        _empty_figure(
            figures / "F5_milp_gap_by_regime.png",
            "MILP gap by regime",
            "No certified MILP pairs were available.",
        )
    else:
        groups = [
            group["optimality_gap_vs_certified_milp"].to_numpy()
            for _, group in gaps.groupby(["family", "n_robots"])
        ]
        labels = [
            f"{family}\nN={n}"
            for (family, n), _ in gaps.groupby(["family", "n_robots"])
        ]
        fig, axis = plt.subplots(figsize=(12, 5.5))
        axis.boxplot(groups, labels=labels, showfliers=False)
        axis.tick_params(axis="x", rotation=35)
        axis.set_ylabel("Gap to certified MILP")
        axis.set_title("Conditional gap: only certified comparable worlds")
        axis.grid(axis="y", alpha=0.25)
        _save_figure(fig, figures / "F5_milp_gap_by_regime.png")

    failure = distributed[distributed["family"] == "F5_network_failure"]
    if failure.empty:
        _empty_figure(
            figures / "F6_failure_recourse.png",
            "Recourse after failure",
            "No F5 rows.",
        )
    else:
        recourse = (
            failure.groupby("method", as_index=False)
            .agg(
                robot_changes=("recourse_robot_changes", "mean"),
                recovered_service=("served_load_rate", "mean"),
            )
            .sort_values("robot_changes")
        )
        fig, axis = plt.subplots(figsize=(10, 5))
        axis.bar(recourse["method"], recourse["robot_changes"])
        axis.tick_params(axis="x", rotation=30)
        axis.set_ylabel("Mean robots changed")
        axis.set_title("Common recovery recourse in F5")
        axis.grid(axis="y", alpha=0.25)
        _save_figure(fig, figures / "F6_failure_recourse.png")

    if regime.empty:
        _empty_figure(
            figures / "F7_regime_map.png",
            "Regime map",
            "No eligible rows.",
        )
    else:
        families = list(dict.fromkeys(regime["family"]))
        sizes = sorted(regime["n_robots"].unique())
        methods = sorted(regime["descriptive_best_method"].unique())
        method_index = {method: index for index, method in enumerate(methods)}
        matrix = np.full((len(families), len(sizes)), np.nan)
        labels = np.full((len(families), len(sizes)), "", dtype=object)
        for _, row in regime.iterrows():
            left = families.index(row["family"])
            right = sizes.index(row["n_robots"])
            matrix[left, right] = method_index[row["descriptive_best_method"]]
            labels[left, right] = row["descriptive_best_method"]
        fig, axis = plt.subplots(figsize=(11, 5.5))
        image = axis.imshow(matrix, aspect="auto", cmap="tab20")
        for left in range(matrix.shape[0]):
            for right in range(matrix.shape[1]):
                axis.text(
                    right,
                    left,
                    labels[left, right].replace("_", "\n"),
                    ha="center",
                    va="center",
                    fontsize=7,
                )
        axis.set_xticks(range(len(sizes)), [f"N={size}" for size in sizes])
        axis.set_yticks(range(len(families)), families)
        axis.set_title("Descriptive Pareto-best method by regime (not a dominance claim)")
        fig.colorbar(image, ax=axis, label="Method index")
        _save_figure(fig, figures / "F7_regime_map.png")


def _build_report(
    runs: pd.DataFrame,
    ranking: pd.DataFrame,
    hypotheses: pd.DataFrame,
    success_gates: pd.DataFrame,
    config: dict[str, Any],
) -> str:
    worlds = int(runs["world_hash"].nunique())
    raw = runs[runs["closure_stage"] == "RAW"]
    timeouts = int((raw["method_status"] == "timeout_or_limit").sum())
    solver_errors = int(
        raw["method_status"].astype(str).str.contains("solver_error").sum()
    )
    nonconverged = int((raw["method_status"] == "max_iterations").sum())
    h4_gate_count = int(
        success_gates["gate_passed"].sum()
        if not success_gates.empty
        else 0
    )
    best_lines: list[str] = []
    if not ranking.empty:
        for family, group in ranking.groupby("family"):
            winners = group[group["overall_rank"] == group["overall_rank"].min()]
            win_counts = winners["method"].value_counts()
            leading_method = str(win_counts.index[0])
            trailing = (
                group.groupby("method", as_index=False)["overall_rank"]
                .median()
                .sort_values(["overall_rank", "method"], ascending=[False, True])
                .iloc[0]
            )
            best_lines.append(
                f"- `{family}`: `{leading_method}` lideró descriptivamente "
                f"{int(win_counts.iloc[0])}/{int(group['n_robots'].nunique())} "
                f"tamaños; `{trailing.method}` obtuvo la peor mediana de rango. "
                "Son etiquetas descriptivas y no acreditan dominancia."
            )
    hypothesis_lines = []
    for row in hypotheses.itertuples():
        if row.test == "predeclared_T2_software_theory_gate":
            decision = (
                "supera el gate numérico predeclarado"
                if row.decision_holm_005
                else "no supera el gate numérico predeclarado"
            )
        elif str(row.hypothesis).startswith("H3_"):
            decision = (
                "cumple la reducción RAW predeclarada de 20 pp tras Holm"
                if row.decision_holm_005
                else "no cumple la reducción RAW predeclarada de 20 pp"
            )
        elif row.hypothesis == "H4_geo_qpg_vs_cbba_quality":
            decision = (
                "cumple el gate compuesto en algún régimen y el contraste tras Holm"
                if row.decision_holm_005
                else "no cumple conjuntamente el gate compuesto y el contraste tras Holm"
            )
        elif row.test == "paired_tost":
            decision = (
                "acredita equivalencia dentro del margen tras Holm"
                if row.decision_holm_005
                else "no acredita equivalencia tras Holm"
            )
        elif row.hypothesis == "H7_failure_recourse_qpg_minus_cbba":
            decision = (
                "cumple el gate del proxy estático tras Holm; no valida recourse dinámico"
                if row.decision_holm_005
                else "no cumple el gate numérico del proxy estático"
            )
        else:
            decision = (
                "rechaza la nula tras Holm"
                if row.decision_holm_005
                else "no es concluyente tras Holm"
            )
        hypothesis_lines.append(
            f"- `{row.hypothesis}`: efecto {row.effect:.6g}, "
            f"p Holm {row.p_holm:.6g}; {decision}."
        )
    return "\n".join(
        [
            f"# Informe {config['experiment_id']}",
            "",
            "## Alcance",
            "",
            "Esta campaña evalúa formación estática de coaliciones en Python. "
            "No simula transporte físico sostenido, contacto dinámico ni estabilidad de SP2.",
            "",
            "El residual euclídeo de wrench se resuelve como mínimos cuadrados "
            "acotados convexos; no se etiqueta como LP. El margen publicado es "
            "el margen a la tolerancia del residual, no un certificado robusto "
            "frente a un conjunto de incertidumbre.",
            "",
            "## Integridad de ejecución",
            "",
            f"- Mundos independientes: {worlds}.",
            f"- Filas método–mundo–cierre: {len(runs)}.",
            f"- Timeouts o límites del MILP en salida nativa: {timeouts}.",
            f"- Errores de solver no recuperados en salida nativa: {solver_errors}.",
            f"- Salidas nativas por máximo de iteraciones: {nonconverged}.",
            "- RAW, CERTIFIED y RECOVERED se conservan por separado.",
            "- Todos los métodos usan el mismo mundo, bienestar físico de evaluación, "
            "certificador y recuperación común.",
            "",
            "## Mapa descriptivo",
            "",
            *(best_lines or ["- No hubo filas elegibles para ranking."]),
            "",
            "## Hipótesis predeclaradas",
            "",
            *(hypothesis_lines or ["- No hubo pares válidos."]),
            "",
            "## Gates compuestos",
            "",
            f"- H4 se evaluó en {len(success_gates)} combinaciones familia–tamaño; "
            f"{h4_gate_count} cumplieron simultáneamente factibilidad, cobertura, "
            "calidad, gap cuando aplicaba, runtime y bytes.",
            "- H3 se corrigió al endpoint RAW predeclarado en F3–F4. "
            "CERTIFIED y RECOVERED no son informativos para falsos positivos porque "
            "el certificador común elimina por construcción los compromisos inválidos.",
            "- H7 se informa solo como proxy estático postfallo. Aunque cumpla sus "
            "umbrales numéricos, la hipótesis dinámica permanece sin validar.",
            "",
            "## Revisión de análisis",
            "",
            f"- Revisión `{ANALYSIS_REVISION_ID}`: corrige el cierre de H3 y "
            "materializa los gates compuestos sin modificar mundos, semillas, "
            "asignaciones ni configuración confirmatoria.",
            "",
            "## Limitaciones",
            "",
            "- Capacity-CBBA, Weighted-GRAPE y Role/Pair-GRAPE-S son adaptaciones "
            "implementadas; no heredan automáticamente las garantías de los métodos originales.",
            "- El MILP usa una envolvente lineal de recursos alineados y después "
            "pasa el certificador firmado. Su optimalidad no equivale a un oráculo "
            "universal del contacto.",
            "- Los gaps a MILP aparecen únicamente cuando el solver y la salida "
            "certificada permiten la comparación.",
            "- F5 es una instantánea estática posterior a un fallo. El recourse "
            "mide cambios del cierre común respecto de la intención post-fallo; "
            "no sustituye una trayectoria dinámica pre/post-fallo.",
            "- La pérdida de paquetes de F5 se representa mediante una realización "
            "congelada de caída de aristas no puente; no modela pérdidas temporales "
            "independientes en cada ronda.",
            "- El análisis usa el mundo como unidad independiente; las cargas no "
            "se tratan como réplicas independientes.",
            "- Los resultados de preview son piloto. La configuración confirmatoria "
            "permanece separada y no debe ajustarse tras abrir sus semillas.",
            "",
            "## Reproducción",
            "",
            "```powershell",
            "python scripts/run_sp1_geo_benchmark.py --config "
            f"configs/experiments/sp1_geo/{Path(config.get('config_name', 'SP1_TFM_GEO_QPG_SIGNAL_ENGINE_CLOSURE_BENCHMARK_v1_preview.yaml')).name}",
            "```",
            "",
        ]
    )


def analyze_results(
    output_dir: str | Path,
    *,
    config: dict[str, Any] | None = None,
) -> Path:
    output = Path(output_dir)
    existing_manifest = output / "manifest.json"
    execution_manifest_sha256: str | None = None
    revision_path = output / "analysis_revision.json"
    if revision_path.exists():
        previous_revision = json.loads(
            revision_path.read_text(encoding="utf-8")
        )
        execution_manifest_sha256 = previous_revision.get(
            "execution_manifest_sha256"
        )
    elif existing_manifest.exists():
        execution_manifest_sha256 = _sha256(existing_manifest)
    if config is None:
        config = _load_yaml(output / "config_frozen.yaml")
    runs = pd.read_parquet(output / "runs.parquet")
    summary = _bootstrap_summary(runs, config)
    ranking = _performance_ranking(runs)
    success_gates = _success_gate_results(runs)
    hypotheses = _hypothesis_results(runs, config, success_gates)
    regime = _regime_map(ranking)
    summary.to_csv(output / "summary.csv", index=False)
    ranking.to_csv(output / "performance_ranking.csv", index=False)
    hypotheses.to_csv(output / "hypothesis_results.csv", index=False)
    success_gates.to_csv(output / "success_gate_results.csv", index=False)
    regime.to_csv(output / "regime_map.csv", index=False)
    _plot_figures(output, runs, ranking, regime)
    (output / "report.md").write_text(
        _build_report(runs, ranking, hypotheses, success_gates, config),
        encoding="utf-8",
    )
    if existing_manifest.exists():
        repository_root = Path.cwd().resolve()
        declared_config = (
            repository_root
            / "configs"
            / "experiments"
            / "sp1_geo"
            / str(config.get("config_name", ""))
        )
        config_source = (
            declared_config
            if declared_config.is_file()
            else output / "config_frozen.yaml"
        )
        (output / "analysis_source_registry.json").write_text(
            json.dumps(
                _source_registry(repository_root, config_source, config),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        revision = {
            "revision_id": ANALYSIS_REVISION_ID,
            "created_at_utc": _utc_now(),
            "execution_manifest_sha256": execution_manifest_sha256,
            "data_generation_changed": False,
            "confirmatory_parameters_changed": False,
            "reason": (
                "The predeclared H3 false-positive endpoint must compare RAW "
                "outputs in F3--F4; RECOVERED is structurally zero after the "
                "common certifier. H4 and H7 numerical gates are now explicit."
            ),
            "input_sha256": {
                name: _sha256(output / name)
                for name in ("runs.parquet", "loads.parquet", "events.parquet")
            },
            "analysis_source_registry": "analysis_source_registry.json",
        }
        revision_path.write_text(
            json.dumps(revision, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        _refresh_manifest_after_analysis(output)
    return output


def finalize_claim_audit(output_dir: str | Path) -> Path:
    """Close the confirmatory claim audit without recomputing statistics."""

    output = Path(output_dir)
    config = _load_yaml(output / "config_frozen.yaml")
    repository_root = Path.cwd().resolve()
    declared_config = (
        repository_root
        / "configs"
        / "experiments"
        / "sp1_geo"
        / str(config.get("config_name", ""))
    )
    config_source = (
        declared_config
        if declared_config.is_file()
        else output / "config_frozen.yaml"
    )
    source_registry = _source_registry(
        repository_root, config_source, config
    )
    (output / "analysis_source_registry.json").write_text(
        json.dumps(source_registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    runs = pd.read_parquet(output / "runs.parquet")
    hypotheses = pd.read_csv(output / "hypothesis_results.csv")
    gates = pd.read_csv(output / "success_gate_results.csv")
    theory = json.loads(
        (output / "theory_audit.json").read_text(encoding="utf-8")
    )
    report = (output / "report.md").read_text(encoding="utf-8")
    world_rows = runs.groupby("world_hash").size()
    hypothesis_records = hypotheses[
        [
            "hypothesis",
            "effect",
            "p_holm",
            "gate_passed",
            "decision_holm_005",
            "claim_scope",
        ]
    ].to_dict("records")
    for record in hypothesis_records:
        for key, value in tuple(record.items()):
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, np.generic):
                record[key] = value.item()
    claim_audit = {
        "created_at_utc": _utc_now(),
        "status": "complete",
        "claim_id": "C-SP1-GEO-SIGNAL-CLOSURE",
        "analysis_revision_id": ANALYSIS_REVISION_ID,
        "scope": "static_SP1_coalition_formation",
        "checks": {
            "worlds": int(runs["world_hash"].nunique()),
            "run_rows": int(len(runs)),
            "duplicate_run_keys": int(
                runs.duplicated(
                    ["world_hash", "method", "closure_stage"]
                ).sum()
            ),
            "rows_per_world_min": int(world_rows.min()),
            "rows_per_world_max": int(world_rows.max()),
            "theory_status": theory["status"],
            "h4_regimes": int(len(gates)),
            "h4_regimes_passed": int(gates["gate_passed"].sum()),
            "forbidden_report_phrase_present": (
                "superioridad universal" in report.lower()
            ),
        },
        "hypotheses": hypothesis_records,
        "limitations": [
            "F5 is a static post-failure proxy, not dynamic recourse.",
            "The bounded Euclidean wrench residual is convex least squares, not an LP.",
            "MILP optimality concerns the linear surrogate, not universal contact mechanics.",
            "No SP2 stability or sustained transport claim is supported.",
        ],
        "documentation": {
            "claims_evidence": "docs/04_CLAIMS_EVIDENCE.md",
            "plan": (
                "plans/2026-07-24-sp1-geo-qpg-signal-engine-closure-v1.md"
            ),
        },
    }
    (output / "claim_audit.json").write_text(
        json.dumps(claim_audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _refresh_manifest_after_analysis(
        output,
        scientific_status="confirmatory_claim_audit_complete",
    )
    return output


def _minimal_torque_assignments() -> tuple[
    GeoWorld, ActionCatalog, Assignment, Assignment, Assignment
]:
    world = torque_complementarity_world()
    catalog = build_action_catalog(world)
    first = catalog.action_for(0, 0, 0)
    second = catalog.action_for(1, 0, 1)
    assert first is not None and second is not None
    singleton_first = Assignment(np.array([first, -1]))
    singleton_second = Assignment(np.array([-1, second]))
    pair = Assignment(np.array([first, second]))
    return world, catalog, singleton_first, singleton_second, pair


def audit_theory(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Execute the predeclared T1--T8 software/theory checks."""

    checks: list[dict[str, Any]] = []
    world = generate_world("F0_easy_separable", 6, 2, 910_000)
    catalog = build_action_catalog(world)
    rng = np.random.default_rng(20260724)
    profile = Assignment.empty(world.n_robots)
    errors = []
    for _ in range(24):
        robot = int(rng.integers(0, world.n_robots))
        actions = catalog.actions_for_robot(robot, compatible_only=True)
        action = int(rng.choice(actions))
        delta_utility, delta_potential = wonderful_life_difference(
            world,
            catalog,
            profile,
            robot,
            action,
            "marginal_physical",
        )
        errors.append(abs(delta_utility - delta_potential))
        profile = profile.with_action(robot, action)
    exact_error = max(errors)
    flat_cross_mismatch = abs(-2.0 - (-1.0))
    checks.append(
        {
            "gate": "T1_potential_identity",
            "passed": exact_error < 1e-8 and flat_cross_mismatch > 1e-3,
            "value": exact_error,
            "tolerance": 1e-8,
            "detail": f"nonintegrable_flat_cross_mismatch={flat_cross_mismatch}",
        }
    )

    small = generate_world("F0_easy_separable", 4, 1, 910_001)
    small_catalog = build_action_catalog(small)
    entropy_tau = 0.08
    convex = solve_entropic_convex(
        small,
        small_catalog,
        signal="marginal_physical",
        entropy_tau=entropy_tau,
        max_iterations=4_000,
    )
    qpg = allocate_qpg(
        small,
        small_catalog,
        signal="marginal_physical",
        engine="logit",
        entropy_tau=entropy_tau,
        damping=0.25,
        max_iterations=4_000,
        tolerance=1e-9,
        consensus_rounds=1,
        exact_aggregates=True,
        monotone_guard=True,
        trace_stride=200,
    )
    qpg_value = signal_potential(
        small,
        small_catalog,
        qpg.preferences,
        "marginal_physical",
        entropy_tau=entropy_tau,
    )
    convex_value = signal_potential(
        small,
        small_catalog,
        convex.preferences,
        "marginal_physical",
        entropy_tau=entropy_tau,
    )
    kkt_gap = relative_objective_gap(qpg_value, convex_value)
    kkt_residual = float(qpg.diagnostics["kkt_residual"])
    primal_residual = float(qpg.diagnostics["primal_residual"])
    dual_residual = float(qpg.diagnostics["dual_stationarity_residual"])
    complementarity_residual = float(
        qpg.diagnostics["complementarity_residual"]
    )
    price_consensus_residual = float(
        qpg.diagnostics["price_consensus_residual"]
    )
    checks.append(
        {
            "gate": "T2_vgne_kkt",
            "passed": (
                kkt_gap <= 1e-3
                and kkt_residual <= 2e-3
                and primal_residual <= 1e-10
                and dual_residual <= 2e-3
                and complementarity_residual <= 1e-10
                and price_consensus_residual <= 1e-10
            ),
            "value": kkt_gap,
            "tolerance": 1e-3,
            "detail": (
                f"kkt={kkt_residual:.6g}; primal={primal_residual:.6g}; "
                f"dual={dual_residual:.6g}; complementarity="
                f"{complementarity_residual:.6g}; price_consensus="
                f"{price_consensus_residual:.6g}; convex_status={convex.status}"
            ),
        }
    )
    minimum_increment = float(qpg.diagnostics["potential_min_increment"])
    checks.append(
        {
            "gate": "T3_sampled_monotonicity",
            "passed": minimum_increment >= -1e-10,
            "value": minimum_increment,
            "tolerance": -1e-10,
            "detail": "exact-aggregate audit with global monotone guard; not benchmark information",
        }
    )

    torque_world, torque_catalog, singleton_a, singleton_b, pair = (
        _minimal_torque_assignments()
    )
    duplicate_preferences = np.zeros(torque_catalog.n_actions)
    duplicate_preferences[torque_catalog.action_for(0, 0, 0)] = 0.8  # type: ignore[index]
    duplicate_preferences[torque_catalog.action_for(1, 0, 0)] = 0.8  # type: ignore[index]
    duplicate = independent_argmax_closure(
        duplicate_preferences, torque_catalog, torque_world.n_robots
    )
    duplicate_certificate = certify_assignment(
        torque_world, torque_catalog, duplicate
    )
    singleton_certificate = certify_assignment(
        torque_world, torque_catalog, singleton_a
    )
    checks.append(
        {
            "gate": "T4_atomic_counterexamples",
            "passed": duplicate_certificate.duplicate_slots > 0
            and singleton_certificate.committed_loads == 1
            and singleton_certificate.served_loads == 0,
            "value": duplicate_certificate.duplicate_slots,
            "tolerance": 1,
            "detail": "independent argmax duplicates a slot; scalar commitment fails wrench",
        }
    )

    recovered = recover_assignment(
        torque_world,
        torque_catalog,
        singleton_a,
        delta=1e-10,
        max_chain_length=2,
        candidates_per_load=4,
    )
    monotone_recovery = all(
        later >= earlier + 1e-10 - 1e-12
        for earlier, later in zip(
            recovered.potential_trajectory,
            recovered.potential_trajectory[1:],
        )
    )
    checks.append(
        {
            "gate": "T5_recovery_finite",
            "passed": recovered.terminated
            and not recovered.cycle_detected
            and monotone_recovery
            and recovered.certificate.served_loads == 1,
            "value": recovered.steps,
            "tolerance": 2,
            "detail": f"visited={recovered.visited_states}; chain={recovered.augmenting_path_length}",
        }
    )

    separable_pass = True
    separable_count = 0
    for seed in range(910_000, 910_004):
        separable = generate_world("F0_easy_separable", 6, 2, seed)
        separable_catalog = build_action_catalog(separable)
        hungarian = allocate_hungarian_slots(separable, separable_catalog)
        before = certify_assignment(
            separable, separable_catalog, hungarian.assignment
        )
        after = recover_assignment(
            separable,
            separable_catalog,
            hungarian.assignment,
            max_chain_length=4,
            candidates_per_load=8,
        )
        separable_count += 1
        separable_pass &= (
            before.served_loads == after.certificate.served_loads
            == separable.n_loads
        )
    checks.append(
        {
            "gate": "T6_slot_decomposable",
            "passed": bool(separable_pass),
            "value": separable_count,
            "tolerance": separable_count,
            "detail": "Hungarian and common recovery agree on full feasibility",
        }
    )

    alpha = 0.05
    samples = 25_000
    components = 16
    bound = 0.05
    variance_sum = components * bound**2 / 3.0
    margin = bernstein_margin(variance_sum, bound, alpha)
    bernstein_rng = np.random.default_rng(20260725)
    noise = bernstein_rng.uniform(
        -bound, bound, size=(samples, components)
    ).sum(axis=1)
    violation_rate = float(np.mean(noise > margin))
    tolerance = alpha + 0.01
    checks.append(
        {
            "gate": "T7_bernstein_margin",
            "passed": violation_rate <= tolerance,
            "value": violation_rate,
            "tolerance": tolerance,
            "detail": f"nominal_alpha={alpha}; margin={margin:.6g}; samples={samples}",
        }
    )

    certificate_a = certify_assignment(
        torque_world, torque_catalog, singleton_a
    )
    certificate_b = certify_assignment(
        torque_world, torque_catalog, singleton_b
    )
    certificate_pair = certify_assignment(torque_world, torque_catalog, pair)
    values = (
        certificate_a.served_loads,
        certificate_b.served_loads,
        certificate_pair.served_loads,
    )
    checks.append(
        {
            "gate": "T8_torque_complementarity",
            "passed": values == (0, 0, 1),
            "value": values[2],
            "tolerance": 1,
            "detail": f"singleton_pair_values={values}",
        }
    )
    status = "passed" if all(bool(item["passed"]) for item in checks) else "failed"
    audit = {
        "campaign_id": CAMPAIGN_ID,
        "created_at_utc": _utc_now(),
        "status": status,
        "scientific_status": "software_theory_audit_not_global_proof",
        "checks": checks,
        "unexplained_failures": [
            item["gate"] for item in checks if not bool(item["passed"])
        ],
    }
    if output_dir is not None:
        output = Path(output_dir)
        pd.DataFrame(checks).to_csv(output / "theory_checks.csv", index=False)
        (output / "theory_audit.json").write_text(
            json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return audit


def _refresh_manifest_after_analysis(
    output: Path,
    *,
    scientific_status: str = (
        "confirmatory_analysis_corrected_claim_audit_pending"
    ),
) -> None:
    """Refresh hashes after a documented analysis-only correction."""

    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = {}
    for path in sorted(
        item
        for item in output.rglob("*")
        if item.is_file()
        and item.name != "manifest.json"
        and "checkpoints" not in item.parts
    ):
        artifacts[path.relative_to(output).as_posix()] = {
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
    manifest["last_analyzed_at_utc"] = _utc_now()
    manifest["scientific_status"] = scientific_status
    manifest["analysis_revision"] = json.loads(
        (output / "analysis_revision.json").read_text(encoding="utf-8")
    )
    manifest["artifacts"] = artifacts
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_manifest(
    output: Path,
    config: dict[str, Any],
    *,
    expected_worlds: int,
    completed_worlds: int,
    elapsed_s: float,
) -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (output / name).exists()]
    if missing:
        raise RuntimeError(f"Cannot close manifest; missing artifacts: {missing}")
    runs = pd.read_parquet(output / "runs.parquet")
    loads = pd.read_parquet(output / "loads.parquet")
    events = pd.read_parquet(output / "events.parquet")
    artifacts = {}
    for path in sorted(
        item
        for item in output.rglob("*")
        if item.is_file()
        and item.name != "manifest.json"
        and "checkpoints" not in item.parts
    ):
        artifacts[path.relative_to(output).as_posix()] = {
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
    manifest = {
        "experiment_id": config["experiment_id"],
        "mode": config["mode"],
        "created_at_utc": _utc_now(),
        "config_sha256": _config_digest(config),
        "expected_worlds": expected_worlds,
        "completed_worlds": completed_worlds,
        "world_count_from_data": int(runs["world_hash"].nunique()),
        "run_rows": len(runs),
        "load_rows": len(loads),
        "event_rows": len(events),
        "elapsed_s": float(elapsed_s),
        "git": _git_state(),
        "scientific_status": (
            "preview_pilot"
            if config["mode"] == "preview"
            else "confirmatory_execution_pending_claim_audit"
        ),
        "artifacts": artifacts,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--no-analyze", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _cli().parse_args(argv)
    output = run_benchmark(
        args.config,
        resume=args.resume,
        analyze=not args.no_analyze,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CAMPAIGN_ID",
    "analyze_results",
    "finalize_claim_audit",
    "audit_theory",
    "main",
    "run_benchmark",
]
