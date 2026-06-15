"""Benchmark v2 for warehouse coalition methods.

The SOTA-labelled entries are SOTA-inspired proxies, not official RHCR, LaCAM,
PIBT, or LNS2 implementations. They share the same robot physics as every other
method so the benchmark isolates coalition and assignment mechanisms.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.simulations import (  # noqa: E402
    INFO_REQUIREMENT,
    LOAD_DELIVERED,
    LOAD_RECRUITING,
    LOAD_TRANSPORT,
    POLICY_AUCTION_CBBA,
    POLICY_CENTRALIZED_LIMITED_COMM,
    POLICY_CENTRALIZED_MINCOST,
    POLICY_GREEDY_NEAREST,
    POLICY_ORACLE_CLAIRVOYANT,
    POLICY_PROXY_PIBT,
    POLICY_PROXY_ROLLING_HORIZON,
    POLICY_PROXY_TOKEN_PASSING,
    POLICY_RANDOM_FEASIBLE,
    POLICY_RESPONSE_THRESHOLD,
    POLICY_MARL_PROXY,
    POLICY_SMITH_FULL,
    POLICY_SMITH_NO_INTEGER,
    POLICY_SMITH_NO_PRICES,
    POLICY_SMITH_QR_BELIEF,
    POLICY_SMITH_QR_CLEARING_GUARD,
    POLICY_SMITH_QR_FULL,
    POLICY_SMITH_QR_STICKY,
    POLICY_SMITH_RAW_OCCUPANCY,
    WarehouseConfig,
    run_warehouse_simulation,
)


EVAL_SEEDS = list(range(2026, 2056))
QUICK_SEEDS = [2026, 2027, 2028]
SMOKE_SEEDS = [2026]
TUNING_SEEDS = list(range(1000, 1005))

METHODS = [
    (POLICY_SMITH_FULL, "Smith full", "ours"),
    (POLICY_SMITH_NO_PRICES, "Smith no prices", "ablation"),
    (POLICY_SMITH_NO_INTEGER, "Smith no integer", "ablation"),
    (POLICY_SMITH_RAW_OCCUPANCY, "Smith raw occupancy", "ablation"),
    (POLICY_SMITH_QR_BELIEF, "Smith-QR belief", "ours"),
    (POLICY_SMITH_QR_STICKY, "Smith-QR sticky", "ours"),
    (POLICY_SMITH_QR_CLEARING_GUARD, "Smith-QR clearing guard", "ours"),
    (POLICY_SMITH_QR_FULL, "Smith-QR full", "ours"),
    (POLICY_GREEDY_NEAREST, "Classic greedy nearest", "classic"),
    (POLICY_CENTRALIZED_MINCOST, "Classic centralized min-cost", "classic"),
    (POLICY_CENTRALIZED_LIMITED_COMM, "Classic centralized limited-comm", "classic"),
    (POLICY_AUCTION_CBBA, "Classic auction/CBBA-lite", "classic"),
    (POLICY_PROXY_TOKEN_PASSING, "Proxy token passing", "sota_proxy"),
    (POLICY_PROXY_ROLLING_HORIZON, "Proxy rolling horizon", "sota_proxy"),
    (POLICY_PROXY_PIBT, "Proxy PIBT priority", "sota_proxy"),
    (POLICY_ORACLE_CLAIRVOYANT, "Oracle clairvoyant bound", "oracle"),
    (POLICY_RESPONSE_THRESHOLD, "Response threshold", "classic"),
    (POLICY_RANDOM_FEASIBLE, "Random feasible", "floor"),
    (POLICY_MARL_PROXY, "MARL proxy shared policy", "marl_proxy"),
]

LOCAL_METHODS = [method for method, _label, _family in METHODS if INFO_REQUIREMENT[method] == "local"]

SUMMARY_COLUMNS = [
    "scenario",
    "scenario_case",
    "method",
    "label",
    "family",
    "info_requirement",
    "seed",
    "runtime_seconds",
    "runtime_per_decision_ms",
    "rho",
    "offered_load",
    "robots",
    "loads_offered",
    "loads_spawned",
    "loads_delivered",
    "censored_loads",
    "delivery_rate",
    "delivered_weight_ratio",
    "delivered_reward",
    "oracle_reward",
    "reward_capture_ratio",
    "reward_capture_discovered",
    "priority_regret",
    "throughput_steady",
    "mean_completion_time",
    "mean_time_post_discovery",
    "max_completion_time",
    "total_robot_distance",
    "distance_per_delivered_weight",
    "wasted_distance",
    "mean_contact_deficit",
    "mean_contact_surplus",
    "max_contact_margin",
    "mean_formation_error",
    "max_formation_error",
    "coalition_breaks",
    "assignment_switches",
    "switches_per_delivery",
    "recruit_switches",
    "release_switches",
    "lateral_switches",
    "lateral_while_transporting",
    "lateral_switches_per_delivery",
    "switch_denominator_lt3",
    "price_std_late",
    "recovery_time_s",
    "peak_deficit_after_fault",
    "staffing_rmse_vs_theory",
    "price_level_vs_lambda_star",
    "min_pair_distance",
    "min_robot_obstacle_clearance",
    "min_load_obstacle_clearance",
    "mean_communication_degree",
    "network_coverage_mean",
    "station_mesh_connected",
    "comm_graph_lambda2_mean",
    "discovery_latency_first_mean",
    "discovery_latency_mean",
    "frac_loads_never_discovered",
    "recruit_latency_mean",
    "pre_failure_deliveries",
    "switch_event_log_path",
    "run_mode",
]


@dataclass(frozen=True)
class ScenarioRun:
    name: str
    case: str
    overrides: dict[str, Any]


def scenario_runs(name: str, quick: bool, smoke: bool = False) -> list[ScenarioRun]:
    duration = 30.0 if smoke else 300.0 if quick else 600.0
    base_loads = 4 if smoke else 45 if quick else 90
    if name == "nominal_flow":
        return [
            ScenarioRun(
                name,
                "rho0.7",
                _rho_config(duration, base_loads, rho=0.7, spawn_process="poisson"),
            )
        ]
    if name == "nominal_flow_big":
        scale = 30.0 / 12.0
        config = _rho_config(duration, base_loads, rho=0.7, spawn_process="poisson")
        config["spawn_period"] *= scale
        return [
            ScenarioRun(
                name,
                "rho0.7_L30",
                config | {"square_size": 30.0, "station_count_per_side": 8},
            )
        ]
    if name == "load_sweep":
        rhos = [0.7] if smoke else [0.5, 1.0, 1.7] if quick else [0.5, 0.8, 1.0, 1.3, 1.7, 2.2]
        return [
            ScenarioRun(
                name,
                f"rho{rho:.1f}",
                _rho_config(duration, base_loads, rho=rho, spawn_process="poisson"),
            )
            for rho in rhos
        ]
    if name == "scarcity_priority":
        return [
            ScenarioRun(
                name,
                "adversarial",
                _rho_config(duration, 4 if smoke else 8 if quick else 70, rho=1.8, min_weight=1, max_weight=10)
                | {"scenario_name": "scarcity_priority", "max_active_loads": 4 if smoke else 6 if quick else 8},
            )
        ]
    if name == "robot_failures":
        return [
            ScenarioRun(
                name,
                "fail4",
                _rho_config(duration, base_loads, rho=1.1, spawn_process="poisson")
                | {"failure_time": duration * 0.40, "failure_count": 4, "revive_time": duration * 0.70},
            )
        ]
    if name == "comm_degradation":
        r_com_values = [12.0, 1.5] if smoke else [12.0, 8.0, 6.0, 4.0, 3.0, 1.5]
        losses = [0.0, 0.9] if smoke else [0.0, 0.5, 0.9]
        runs = []
        for r_com in r_com_values:
            for packet_loss in losses:
                runs.append(
                    ScenarioRun(
                        name,
                        f"R{r_com:g}_p{packet_loss:g}",
                        _rho_config(duration, base_loads, rho=0.8, spawn_process="poisson")
                        | {"r_com": r_com, "packet_loss": packet_loss},
                    )
                )
        return runs
    if name == "task_churn":
        return [
            ScenarioRun(
                name,
                "cancel30",
                _rho_config(duration, base_loads, rho=0.9, spawn_process="poisson")
                | {"cancel_probability": 0.30, "cancel_after_fraction": 0.5},
            )
        ]
    if name == "scaling":
        robots = [15] if smoke else [15, 30] if quick else [15, 30, 60]
        return [
            ScenarioRun(
                name,
                f"N{robot_count}",
                _rho_config(duration, base_loads * max(1, robot_count // 15), rho=0.9, spawn_process="poisson")
                | {"robot_count": robot_count},
            )
            for robot_count in robots
        ]
    if name == "scarcity_extreme":
        return [
            ScenarioRun(
                name,
                "rho2.2_heavy",
                _rho_config(duration, 4 if smoke else 8 if quick else 80, rho=2.2, min_weight=6, max_weight=10)
                | {"max_active_loads": 4 if smoke else 6},
            )
        ]
    msg = f"Unknown scenario {name!r}. Known: {sorted(SCENARIOS)}"
    raise ValueError(msg)


SCENARIOS = {
    "nominal_flow": "Poisson flow at rho ~= 0.7.",
    "nominal_flow_big": "Poisson nominal flow in a 30 m arena with unchanged Psi scale.",
    "load_sweep": "Load factor sweep; central money plot.",
    "scarcity_priority": "Sustained overload with heterogeneous rewards and adversarial distance.",
    "robot_failures": "Nominal flow with four robot failures and optional recovery.",
    "comm_degradation": "Communication radius and packet-loss sweep.",
    "task_churn": "Poisson task churn with 30% mid-service cancellations.",
    "scaling": "N in {15, 30, 60} at fixed rho.",
    "scarcity_extreme": "Heavy sustained scarcity gate.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="all", help="Scenario name, comma list, or 'all'.")
    parser.add_argument("--methods", default="all", help="Method name, comma list, or 'all'.")
    parser.add_argument("--seeds", default=None, help="Comma-separated seeds. Defaults to quick/full defaults.")
    parser.add_argument("--quick", action="store_true", help="Short 3-seed benchmark.")
    parser.add_argument("--smoke", action="store_true", help="Very short smoke run; outputs are labelled non-interpretable.")
    parser.add_argument("--out", type=Path, default=Path("results/benchmark-v2"))
    parser.add_argument("--tuned-params", type=Path, default=Path("configs/tuned_params_v26.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.quick and args.smoke:
        raise ValueError("Use either --quick or --smoke, not both.")
    selected_scenarios = _select_scenarios(args.scenario)
    selected_methods = _select_methods(args.methods)
    seeds = _parse_seeds(args.seeds, quick=args.quick, smoke=args.smoke)
    tuned_params = _load_tuned_params(args.tuned_params)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "figures").mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for scenario in selected_scenarios:
        for scenario_run in scenario_runs(scenario, quick=args.quick, smoke=args.smoke):
            for seed in seeds:
                for method, label, family in selected_methods:
                    effective_overrides = dict(scenario_run.overrides)
                    if scenario_run.name == "comm_degradation" and INFO_REQUIREMENT[method] == "global":
                        effective_overrides["packet_loss"] = 0.0
                        effective_overrides["r_com"] = 12.0
                    config = _config_from_run(seed, method, scenario_run, effective_overrides, tuned_params)
                    started = time.perf_counter()
                    result = run_warehouse_simulation(config)
                    runtime = time.perf_counter() - started
                    row = _summary_row(result.summary, scenario_run, method, label, family, runtime, result.time.size)
                    if method == POLICY_ORACLE_CLAIRVOYANT:
                        _promote_oracle_row_to_bound(row)
                    row["switch_event_log_path"] = _write_switch_log_csv(
                        args.out,
                        scenario_run,
                        method,
                        seed,
                        result.summary.get("switch_events", []),
                    )
                    rows.append(row)
                    _write_run_csv(args.out, scenario_run, method, seed, result)
                    if method.startswith("smith"):
                        _write_theory_csv(args.out, scenario_run, method, seed, result)
                    print(_format_progress(row))

    validate_oracle_bounds(rows)
    validate_metric_consistency(rows)
    for row in rows:
        row["run_mode"] = "SMOKE" if args.smoke else "QUICK" if args.quick else "FULL"

    summary_csv = args.out / "summary.csv"
    summary_json = args.out / "summary.json"
    _write_csv(summary_csv, rows, SUMMARY_COLUMNS)
    summary_json.write_text(json.dumps(rows, indent=2, sort_keys=True, allow_nan=True), encoding="utf-8")
    old_params = _load_tuned_params(Path("configs/tuned_params_v25.json"))
    _write_summary_md(args.out / "summary.md", rows, tuned_params, selected_methods, selected_scenarios, old_params)

    from plot_benchmark import generate_figures  # local scripts/ module

    figure_paths = generate_figures(summary_csv, args.out / "figures")
    print("\nSaved benchmark outputs:")
    print(f"  {summary_csv}")
    print(f"  {summary_json}")
    print(f"  {args.out / 'summary.md'}")
    for path in figure_paths:
        print(f"  {path}")
    if args.quick:
        validate_quick_gates(rows)
    return 0


def _rho_config(
    duration: float,
    max_loads: int,
    rho: float,
    min_weight: int = 1,
    max_weight: int = 10,
    spawn_process: str = "periodic",
) -> dict[str, Any]:
    mean_weight = 0.5 * (min_weight + max_weight)
    service_time = 24.0
    spawn_period = max(2.0, service_time * mean_weight / max(15.0 * rho, 1e-9))
    return {
        "duration": duration,
        "dt": 0.25,
        "max_loads": max_loads,
        "max_active_loads": 3,
        "spawn_period": spawn_period,
        "spawn_process": spawn_process,
        "min_weight": min_weight,
        "max_weight": max_weight,
        "rho": rho,
        "offered_load": rho,
    }


def _select_scenarios(value: str) -> list[str]:
    if value.strip().lower() == "all":
        return list(SCENARIOS)
    requested = [item.strip() for item in value.split(",") if item.strip()]
    missing = set(requested) - set(SCENARIOS)
    if missing:
        msg = f"Unknown scenarios: {sorted(missing)}"
        raise ValueError(msg)
    return requested


def _select_methods(value: str) -> list[tuple[str, str, str]]:
    if value.strip().lower() == "all":
        return METHODS
    requested = {item.strip() for item in value.split(",") if item.strip()}
    known = {method for method, _label, _family in METHODS}
    missing = requested - known
    if missing:
        msg = f"Unknown methods: {sorted(missing)}. Known: {sorted(known)}"
        raise ValueError(msg)
    return [entry for entry in METHODS if entry[0] in requested]


def _parse_seeds(value: str | None, quick: bool, smoke: bool = False) -> list[int]:
    if value:
        return [int(item.strip()) for item in value.split(",") if item.strip()]
    if smoke:
        return SMOKE_SEEDS
    return QUICK_SEEDS if quick else EVAL_SEEDS


def _load_tuned_params(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


SMITH_ABLATIONS = {
    POLICY_SMITH_NO_PRICES,
    POLICY_SMITH_NO_INTEGER,
    POLICY_SMITH_RAW_OCCUPANCY,
    POLICY_SMITH_QR_BELIEF,
    POLICY_SMITH_QR_STICKY,
    POLICY_SMITH_QR_CLEARING_GUARD,
    POLICY_SMITH_QR_FULL,
}


def smith_params_for_method(method: str, tuned_params: dict[str, dict[str, Any]]) -> dict[str, Any]:
    full = dict(tuned_params.get(POLICY_SMITH_FULL, {}))
    if method == POLICY_SMITH_FULL:
        return full
    if method == POLICY_SMITH_NO_PRICES:
        params = dict(full)
        params["price_gain"] = 0.0
        return params
    if method == POLICY_SMITH_NO_INTEGER:
        return dict(full)
    if method == POLICY_SMITH_RAW_OCCUPANCY:
        return dict(full)
    if method in {POLICY_SMITH_QR_BELIEF, POLICY_SMITH_QR_STICKY, POLICY_SMITH_QR_CLEARING_GUARD, POLICY_SMITH_QR_FULL}:
        params = dict(full)
        params.update(
            {
                "clearing_mode": "tick",
                "lateral_switch_rule": "potential",
                "price_feedback_signal": "effective_committed",
                "descriptor_belief_tau": 24.0,
                "commitment_ttl": 12.0,
                "local_quorum_grace": 4.0,
                "clearing_connectivity_guard": 2.2,
                "qr_patrol_gain": 1.6,
            }
        )
        return params
    return dict(tuned_params.get(method, {}))


def _config_from_run(
    seed: int,
    method: str,
    scenario_run: ScenarioRun,
    overrides: dict[str, Any],
    tuned_params: dict[str, dict[str, Any]],
) -> WarehouseConfig:
    kwargs = dict(overrides)
    kwargs.update(smith_params_for_method(method, tuned_params))
    kwargs["seed"] = seed
    kwargs["scenario_name"] = scenario_run.name
    kwargs["assignment_policy"] = method
    return WarehouseConfig(**kwargs)


def _summary_row(
    summary: dict[str, Any],
    scenario_run: ScenarioRun,
    method: str,
    label: str,
    family: str,
    runtime: float,
    steps: int,
) -> dict[str, Any]:
    row = {column: summary.get(column, np.nan) for column in SUMMARY_COLUMNS}
    row.update(
        {
            "scenario": scenario_run.name,
            "scenario_case": scenario_run.case,
            "method": method,
            "label": label,
            "family": family,
            "info_requirement": INFO_REQUIREMENT[method],
            "runtime_seconds": runtime,
            "runtime_per_decision_ms": 1000.0 * runtime / max(steps, 1),
        }
    )
    return row


def _promote_oracle_row_to_bound(row: dict[str, Any]) -> None:
    """Report the oracle row as an offline upper bound, not as a deployed policy."""

    oracle_reward = _as_float(row.get("oracle_reward"))
    if not math.isfinite(oracle_reward):
        return
    row["delivered_reward"] = oracle_reward
    row["reward_capture_ratio"] = 1.0 if oracle_reward > 0.0 else math.nan
    row["reward_capture_discovered"] = 1.0 if oracle_reward > 0.0 else math.nan
    row["priority_regret"] = 0.0
    row["loads_delivered"] = row.get("loads_offered", row.get("loads_delivered", 0))
    row["delivery_rate"] = 1.0 if _as_float(row.get("loads_spawned")) > 0 else 0.0


def validate_oracle_bounds(rows: list[dict[str, Any]]) -> None:
    """Abort when the oracle row is not an upper bound in every paired cell."""

    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["scenario"]), str(row["scenario_case"]), int(row["seed"]))
        grouped.setdefault(key, []).append(row)
    failures: list[str] = []
    for key, group in grouped.items():
        oracle_rows = [row for row in group if row["method"] == POLICY_ORACLE_CLAIRVOYANT]
        if not oracle_rows:
            continue
        oracle_reward = max(_as_float(row["delivered_reward"]) for row in oracle_rows)
        best_method = max(_as_float(row["delivered_reward"]) for row in group if row["method"] != POLICY_ORACLE_CLAIRVOYANT)
        if oracle_reward + 1e-9 < best_method:
            failures.append(f"{key}: oracle={oracle_reward:.6g} best={best_method:.6g}")
    if failures:
        joined = "\n  ".join(failures[:20])
        msg = "Oracle upper-bound validation failed; refusing to write summary:\n  " + joined
        raise RuntimeError(msg)


def validate_metric_consistency(rows: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    for row in rows:
        throughput = _as_float(row.get("throughput_steady"))
        mean_time = _as_float(row.get("mean_completion_time"))
        if throughput > 0.0 and not math.isfinite(mean_time):
            failures.append(
                f"{row.get('scenario')}/{row.get('scenario_case')}/{row.get('method')}/seed={row.get('seed')}"
            )
    if failures:
        joined = "\n  ".join(failures[:20])
        msg = "Metric validation failed: throughput > 0 with mean_completion_time=n/a:\n  " + joined
        raise RuntimeError(msg)


def validate_quick_gates(rows: list[dict[str, Any]]) -> None:
    failures: list[str] = []
    failures.extend(_gate_nominal_local_gap(rows))
    failures.extend(_gate_comm_monotonic(rows))
    failures.extend(_gate_smith_switches(rows))
    failures.extend(_gate_nominal_discovery(rows))
    failures.extend(_gate_smith_discovered_capture_consistency(rows))
    if failures:
        joined = "\n  ".join(failures)
        raise RuntimeError("Quick benchmark gates failed:\n  " + joined)


def _gate_nominal_local_gap(rows: list[dict[str, Any]]) -> list[str]:
    nominal = [
        row for row in rows
        if row.get("scenario") == "nominal_flow"
        and row.get("scenario_case") == "rho0.7"
        and row.get("method") != POLICY_ORACLE_CLAIRVOYANT
    ]
    if not nominal:
        return []
    local_best = _best_method_mean(nominal, info_requirement="local", metric="delivered_reward")
    global_best = _best_method_mean(nominal, info_requirement="global", metric="delivered_reward")
    if math.isfinite(global_best) and global_best > 0.0 and (not math.isfinite(local_best) or local_best < 0.75 * global_best):
        return [f"nominal local/global reward gap too large: local={local_best:.3g}, global={global_best:.3g}"]
    return []


def _gate_comm_monotonic(rows: list[dict[str, Any]]) -> list[str]:
    required = {POLICY_GREEDY_NEAREST, POLICY_SMITH_FULL}
    comm = [
        row for row in rows
        if row.get("scenario") == "comm_degradation" and row.get("method") in required
    ]
    if not comm:
        return []
    failures: list[str] = []
    by_method: dict[str, list[dict[str, Any]]] = {}
    for row in comm:
        by_method.setdefault(str(row["method"]), []).append(row)
    for method, group in by_method.items():
        values = _case_means(group, "reward_capture_ratio")
        ordered_r = [values.get(case) for case in ["R12_p0", "R8_p0", "R6_p0", "R4_p0", "R3_p0"]]
        finite = [value for value in ordered_r if value is not None and math.isfinite(value)]
        if len(finite) < 5:
            failures.append(f"comm monotonic R missing cases for {method}: {finite}")
            continue
        increases = sum(b > a + 0.20 for a, b in zip(finite, finite[1:]))
        if increases:
            failures.append(f"comm monotonic R failed for {method}: {finite}")
    return failures[:10]


def _gate_smith_switches(rows: list[dict[str, Any]]) -> list[str]:
    smith = [
        row
        for row in rows
        if row.get("method") == POLICY_SMITH_FULL and _as_float(row.get("loads_delivered")) >= 3.0
    ]
    values = np.array([_as_float(row.get("lateral_switches_per_delivery")) for row in smith], dtype=float)
    values = values[np.isfinite(values)]
    if values.size and float(np.median(values)) >= 10.0:
        return [f"smith_full median lateral_switches/delivery={float(np.median(values)):.3g} >= 10"]
    return []


def _gate_nominal_discovery(rows: list[dict[str, Any]]) -> list[str]:
    nominal_local = [
        row for row in rows
        if row.get("scenario") == "nominal_flow"
        and row.get("scenario_case") == "rho0.7"
        and row.get("info_requirement") == "local"
    ]
    if not nominal_local:
        return []
    never = np.array([_as_float(row.get("frac_loads_never_discovered")) for row in nominal_local], dtype=float)
    never = never[np.isfinite(never)]
    if never.size and float(np.mean(never)) >= 0.05:
        return [f"nominal frac_loads_never_discovered={float(np.mean(never)):.3g} >= 0.05"]
    return []


def _gate_smith_discovered_capture_consistency(rows: list[dict[str, Any]]) -> list[str]:
    smith_nominal = [
        row for row in rows
        if row.get("scenario") == "nominal_flow"
        and row.get("scenario_case") == "rho0.7"
        and row.get("method") == POLICY_SMITH_FULL
    ]
    total = np.array([_as_float(row.get("reward_capture_ratio")) for row in smith_nominal], dtype=float)
    discovered = np.array([_as_float(row.get("reward_capture_discovered")) for row in smith_nominal], dtype=float)
    mask = np.isfinite(total) & np.isfinite(discovered)
    if np.any(mask) and float(np.mean(discovered[mask])) + 1e-12 < 0.9 * float(np.mean(total[mask])):
        return [
            "smith_full reward_capture_discovered below 0.9 * total in nominal: "
            f"discovered={float(np.mean(discovered[mask])):.3g}, total={float(np.mean(total[mask])):.3g}"
        ]
    return []


def _best_method_mean(rows: list[dict[str, Any]], info_requirement: str, metric: str) -> float:
    by_method: dict[str, list[float]] = {}
    for row in rows:
        if row.get("info_requirement") != info_requirement:
            continue
        value = _as_float(row.get(metric))
        if math.isfinite(value):
            by_method.setdefault(str(row.get("method")), []).append(value)
    if not by_method:
        return math.nan
    return max(float(np.mean(values)) for values in by_method.values() if values)


def _case_means(rows: list[dict[str, Any]], metric: str) -> dict[str, float]:
    by_case: dict[str, list[float]] = {}
    for row in rows:
        value = _as_float(row.get(metric))
        if math.isfinite(value):
            by_case.setdefault(str(row.get("scenario_case")), []).append(value)
    return {case: float(np.mean(values)) for case, values in by_case.items() if values}


def _write_run_csv(
    output: Path,
    scenario_run: ScenarioRun,
    method: str,
    seed: int,
    result: Any,
) -> None:
    directory = output / scenario_run.name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scenario_run.case}_{method}_{seed}.csv"
    delivered_counts = np.sum(result.load_status == LOAD_DELIVERED, axis=1)
    active_counts = np.sum((result.load_status == LOAD_RECRUITING) | (result.load_status == LOAD_TRANSPORT), axis=1)
    active_weight = []
    for step in range(result.load_status.shape[0]):
        active_weight.append(
            sum(
                load.weight
                for idx, load in enumerate(result.loads)
                if result.load_status[step, idx] in {LOAD_RECRUITING, LOAD_TRANSPORT}
            )
        )
    rows = [
        {
            "time": float(result.time[idx]),
            "delivered_count": int(delivered_counts[idx]),
            "active_count": int(active_counts[idx]),
            "active_weight": float(active_weight[idx]),
            "mean_contact_deficit": float(
                np.mean(
                    [
                        max(0.0, load.weight - result.contact_counts[idx, load_idx])
                        for load_idx, load in enumerate(result.loads)
                        if result.load_status[idx, load_idx] in {LOAD_RECRUITING, LOAD_TRANSPORT}
                    ]
                    or [0.0]
                )
            ),
        }
        for idx in range(result.time.size)
    ]
    _write_csv(path, rows, ["time", "delivered_count", "active_count", "active_weight", "mean_contact_deficit"])


def _write_theory_csv(
    output: Path,
    scenario_run: ScenarioRun,
    method: str,
    seed: int,
    result: Any,
) -> None:
    directory = output / scenario_run.name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scenario_run.case}_{method}_{seed}_theory.csv"
    rows = []
    for step, now in enumerate(result.time):
        for load_idx, load in enumerate(result.loads):
            if result.theory_staffing[step, load_idx] <= 0.0 and result.contact_counts[step, load_idx] <= 0.0:
                continue
            rows.append(
                {
                    "time": float(now),
                    "load": load.identifier,
                    "z_observed": float(result.contact_counts[step, load_idx]),
                    "z_theory": float(result.theory_staffing[step, load_idx]),
                    "lambda_star": float(result.theory_lambda[step]),
                    "price": float(result.prices[step, load_idx]),
                }
            )
    _write_csv(path, rows, ["time", "load", "z_observed", "z_theory", "lambda_star", "price"])


def _write_switch_log_csv(
    output: Path,
    scenario_run: ScenarioRun,
    method: str,
    seed: int,
    events: Any,
) -> str:
    if not events:
        return ""
    directory = output / scenario_run.name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scenario_run.case}_{method}_{seed}_switches.csv"
    rows = [
        {
            "time": event.get("time", ""),
            "robot": event.get("robot", ""),
            "from": event.get("from", ""),
            "to": event.get("to", ""),
            "kind": event.get("kind", ""),
            "cause": event.get("cause", ""),
            "from_status": event.get("from_status", ""),
            "to_status": event.get("to_status", ""),
        }
        for event in events
    ]
    _write_csv(path, rows, ["time", "robot", "from", "to", "kind", "cause", "from_status", "to_status"])
    return str(path)


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _write_summary_md(
    path: Path,
    rows: list[dict[str, Any]],
    tuned_params: dict[str, dict[str, Any]],
    methods: list[tuple[str, str, str]],
    scenarios: list[str],
    old_params: dict[str, dict[str, Any]] | None = None,
) -> None:
    lines = [
        "# Warehouse coalition benchmark v2.6",
        "",
        "## Scope",
        "",
        "All methods share the same 2D robot physics, contact model, formation layer and obstacle avoidance. Only assignment/recruitment policies, scenario events and reporting differ.",
        "",
        "## Fairness",
        "",
        f"Evaluation scenarios: {', '.join(scenarios)}.",
        "Evaluation uses paired seeds across methods. Tuning seeds are separate: 1000-1004.",
        "",
        "| Method | Info | previous params | current params |",
        "|---|---:|---|---|",
    ]
    old_params = old_params or {}
    for method, label, _family in methods:
        params = smith_params_for_method(method, tuned_params)
        previous = smith_params_for_method(method, old_params)
        lines.append(
            f"| {label} | {INFO_REQUIREMENT[method]} | "
            f"`{json.dumps(previous, sort_keys=True)}` | `{json.dumps(params, sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "Tuning v2.6 objective: mean over `nominal_flow` and `scarcity_extreme` of `delivered_reward - 0.02*lateral_switches - 0.001*total_robot_distance`.",
            "The v2.6 configuration keeps E2 and E3, removes E4 event-driven clearing from `smith_full`, and derives all Smith ablations from the full Smith configuration.",
            "",
            "## Information model",
            "",
            "- Local methods receive load descriptors through station announcements and robot-to-robot multi-hop relay/gossip. Stations announce active loads every tick; robots relay descriptors they know every tick; each link is independently dropped with `packet_loss`.",
            "- A local robot can bid for, assign to, or contribute DAC signal only for loads whose descriptor is currently known. Descriptors expire after 10 s without refresh.",
            "- Idle local robots that know no active load for more than 5 s patrol slowly through random warehouse waypoints at `0.3*v_max`. This is a common information policy, not a method-specific advantage.",
            "- Global methods (`classic_centralized_mincost`, `proxy_rolling_horizon`, `oracle_clairvoyant`) are marked as requiring global information and are not degraded by packet loss.",
            "- `discovery_latency_first_mean` measures spawn-to-first-robot discovery; `discovery_latency_mean` measures spawn-to-last-known/full-spread discovery when available; `frac_loads_never_discovered` reports undiscovered offered loads.",
            "- If `oracle_reward == 0`, reward capture is reported as `NaN` and the cell is treated as censored in aggregation.",
            "",
            "## Occupancy Signal Audit",
            "",
            "v2.1 uses a floor on effective occupancy weights for Smith effective variants: `Psi_tilde=max(Psi, 0.3)`. This targets the observed recruit-clip-release cycle where distant committed robots were nearly invisible to Phi while clearing still counted integer contacts.",
            "",
            "## Price Loop And Finite Switching",
            "",
            "- `smith_full` price loop feedback: committed effective occupancy (fast). Integer clearing and load mode transitions still use physical contact as ground truth.",
            "- Lateral switching uses a potential-improvement test `DeltaV > epsilon_switch` with the robot's own externality internalized. During transport/contact, `epsilon_switch` is multiplied by 5.",
            "- Finite switching: with `epsilon_switch > 0`, every accepted lateral switch increases a bounded global potential by at least `epsilon_switch`, so total lateral switches are finite and bounded by `(V_max - V_min)/epsilon_switch`.",
            "- v2.6 uses per-tick integer clearing for `smith_full`; the attempted event-driven clearing is retained as an experimental mode after bisection showed it caused the nominal regression.",
            "",
            "## Epsilon Sweep",
            "",
            *(_epsilon_sweep_lines(Path("configs/tuned_params_v26_scores.json"))),
            "",
            "## Single-Clock Lesson",
            "",
            "- F2/F3 bisection showed that clearing belongs to the fast loop: E2-only tick clearing reached reward capture 0.633 with 129.7 lateral switches and discovery latency 42.1 s, while event-driven clearing alone fell to 0.335 with 897.3 lateral switches and discovery latency 71.7 s.",
            "- The corrected event-driven trigger recovered reward capture to 0.530 but still produced 739 lateral switches on average; periodic 1 s clearing fell to 0.244 with about 1888 lateral switches.",
            "- Operational conclusion: decision, prices and integer clearing must share the same single-clock loop in this implementation. Introducing separation of scales in the clearing layer degraded both coverage and assignment stability.",
            "",
        ]
    )
    if rows and rows[0].get("run_mode") == "SMOKE":
        lines.extend(["", "**SMOKE -- no interpretar como resultado experimental.**", ""])
    lines.extend(["", "## Aggregate Results", ""])
    aggregate = _aggregate_for_md(rows)
    lines.append("| Scenario | Case | Method | Reward capture | Discovered capture | Throughput steady | Recovery | Mean time | Post-discovery time | Recruit latency | Switches/delivery | Censored loads | Coverage | Lambda2 | Mesh | Discovery latency | Never discovered |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for key, group in aggregate.items():
        scenario, case, label = key
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario,
                    case,
                    label,
                    _format_ci(group, "reward_capture_ratio"),
                    _format_ci(group, "reward_capture_discovered"),
                    _format_ci(group, "throughput_steady"),
                    _format_ci(group, "recovery_time_s"),
                    _format_ci(group, "mean_completion_time"),
                    _format_ci(group, "mean_time_post_discovery"),
                    _format_ci(group, "recruit_latency_mean"),
                    _format_ci(group, "switches_per_delivery"),
                    _format_ci(group, "censored_loads"),
                    _format_ci(group, "network_coverage_mean"),
                    _format_ci(group, "comm_graph_lambda2_mean"),
                    _format_bool_rate(group, "station_mesh_connected"),
                    _format_ci(group, "discovery_latency_mean"),
                    _format_ci(group, "frac_loads_never_discovered"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Switch Audit", ""])
    lines.append("| Scenario | Case | Method | Recruit | Release | Lateral | Lateral transporting | Lateral/delivery | Deliveries<3 |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for key, group in aggregate.items():
        scenario, case, label = key
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario,
                    case,
                    label,
                    _format_ci(group, "recruit_switches"),
                    _format_ci(group, "release_switches"),
                    _format_ci(group, "lateral_switches"),
                    _format_ci(group, "lateral_while_transporting"),
                    _format_ci(group, "lateral_switches_per_delivery"),
                    _format_bool_rate(group, "switch_denominator_lt3"),
                ]
            )
            + " |"
        )
    worst_switch_row = _worst_switch_row(rows)
    if worst_switch_row is not None:
        lines.extend(
            [
                "",
                "Worst lateral-switch cell:",
                "",
                (
                    f"- {worst_switch_row.get('scenario')}/{worst_switch_row.get('scenario_case')} "
                    f"{worst_switch_row.get('label')} seed={worst_switch_row.get('seed')}: "
                    f"lateral/delivery={_as_float(worst_switch_row.get('lateral_switches_per_delivery')):.3g}, "
                    f"deliveries={_as_float(worst_switch_row.get('loads_delivered')):.3g}, "
                    f"log=`{worst_switch_row.get('switch_event_log_path') or 'n/a'}`"
                ),
            ]
        )
    lines.extend(_coverage_coupling_lines(rows))
    censored_cells = [
        key for key, group in aggregate.items()
        if all(not math.isfinite(_as_float(row.get("reward_capture_ratio"))) for row in group)
    ]
    if censored_cells:
        lines.extend(
            [
                "",
                f"Celda censurada: {len(censored_cells)} aggregate cells had `oracle_reward == 0` and no finite reward capture.",
            ]
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- `proxy_token_passing`, `proxy_rolling_horizon`, and `proxy_pibt_priority` are SOTA-inspired proxies, not official implementations of RHCR, LaCAM, PIBT, LNS2 or related solvers.",
            "- `oracle_clairvoyant` is a bound/proxy with full calendar visibility and is not deployable.",
            "- The physical simulator is still kinematic; contact and payload dynamics are simplified.",
            "- Smith variants use a fluid decision layer; the full method adds integer quorum clearing to close the gap with discrete payload physics.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _aggregate_for_md(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row["scenario"]), str(row["scenario_case"]), str(row["label"])), []).append(row)
    return dict(sorted(grouped.items()))


def _worst_switch_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        row for row in rows
        if math.isfinite(_as_float(row.get("lateral_switches_per_delivery")))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda row: _as_float(row.get("lateral_switches_per_delivery")))


def _epsilon_sweep_lines(path: Path) -> list[str]:
    if not path.exists():
        return ["Epsilon sweep table unavailable; run `scripts/tune_methods.py` first."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["Epsilon sweep table unavailable; score file could not be parsed."]
    rows = data.get("grid", {}).get(POLICY_SMITH_FULL, [])
    if not rows:
        return ["Epsilon sweep table unavailable; no smith_full grid rows found."]
    lines = [
        "| epsilon | score | nominal capture | nominal lateral/delivery | scarcity capture | scarcity lateral/delivery |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{_as_float(row.get('epsilon_switch')):.3g}",
                    f"{_as_float(row.get('score')):.3g}",
                    f"{_as_float(row.get('nominal_flow_capture_mean')):.3g}",
                    f"{_as_float(row.get('nominal_flow_lateral_per_delivery_mean')):.3g}",
                    f"{_as_float(row.get('scarcity_extreme_capture_mean')):.3g}",
                    f"{_as_float(row.get('scarcity_extreme_lateral_per_delivery_mean')):.3g}",
                ]
            )
            + " |"
        )
    best = max(rows, key=lambda row: _as_float(row.get("score")))
    nominal_ok = any(
        _as_float(row.get("nominal_flow_capture_mean")) >= 0.60
        and _as_float(row.get("nominal_flow_lateral_per_delivery_mean")) < 10.0
        for row in rows
    )
    if nominal_ok:
        lines.append(f"Selected epsilon `{_as_float(best.get('epsilon_switch')):.3g}` by tuning score.")
    else:
        lines.append(
            f"No epsilon reached nominal capture >= 0.60 in the clean sweep; selected "
            f"`{_as_float(best.get('epsilon_switch')):.3g}` by score and lowest nominal lateral pressure."
        )
    return lines


def _format_ci(rows: list[dict[str, Any]], metric: str) -> str:
    values = np.array([_as_float(row.get(metric)) for row in rows], dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return "n/a"
    low, high = _bootstrap_ci(values)
    return f"{np.mean(values):.3g} +/- {(high - low) / 2.0:.2g}"


def _format_bool_rate(rows: list[dict[str, Any]], metric: str) -> str:
    values = []
    for row in rows:
        value = row.get(metric)
        if isinstance(value, str):
            values.append(value.strip().lower() in {"true", "1", "yes"})
        elif value is not None:
            values.append(bool(value))
    if not values:
        return "n/a"
    rate = float(np.mean(values))
    if rate == 1.0:
        return "yes"
    if rate == 0.0:
        return "no"
    return f"{rate:.2g}"


def _coverage_coupling_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = ["", "## Coverage-allocation coupling", ""]
    lines.append("| Method | corr(coverage, discovery latency) | n |")
    lines.append("|---|---:|---:|")
    by_label: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("info_requirement") != "local":
            continue
        by_label.setdefault(str(row.get("label")), []).append(row)
    for label, group in sorted(by_label.items()):
        coverage = np.array([_as_float(row.get("network_coverage_mean")) for row in group], dtype=float)
        latency = np.array([_as_float(row.get("discovery_latency_mean")) for row in group], dtype=float)
        mask = np.isfinite(coverage) & np.isfinite(latency)
        if int(np.sum(mask)) < 3 or np.std(coverage[mask]) <= 1e-12 or np.std(latency[mask]) <= 1e-12:
            corr = "n/a"
        else:
            corr = f"{float(np.corrcoef(coverage[mask], latency[mask])[0, 1]):.3g}"
        lines.append(f"| {label} | {corr} | {int(np.sum(mask))} |")
    lines.append("")
    lines.append("This table separates coverage from allocation quality: high discovery latency can depress reward capture before the task-allocation policy has a fair chance to act.")
    return lines


def _bootstrap_ci(values: np.ndarray, samples: int = 400) -> tuple[float, float]:
    if values.size <= 1:
        return float(values[0]), float(values[0])
    rng = np.random.default_rng(31415)
    means = np.zeros(samples, dtype=float)
    for idx in range(samples):
        means[idx] = float(np.mean(rng.choice(values, size=values.size, replace=True)))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _format_progress(row: dict[str, Any]) -> str:
    return (
        f"{row['scenario']}/{row['scenario_case']} | {row['label']:<29} "
        f"seed={int(row['seed'])} reward={_as_float(row['reward_capture_ratio']):.2f} "
        f"thr={_as_float(row['throughput_steady']):.2f}/min "
        f"time={_as_float(row['mean_completion_time']):.1f}s "
        f"rt={_as_float(row['runtime_seconds']):.2f}s"
    )


if __name__ == "__main__":
    raise SystemExit(main())
