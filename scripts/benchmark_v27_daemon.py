"""Resumable background runner for the v2.7 thesis benchmark.

The runner is intentionally checkpoint-first: every completed simulation appends one
summary row and updates ``state.json``. If the process is interrupted, rerun ``start``
or ``run`` and completed keys are skipped.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark_warehouse_methods import (  # noqa: E402
    SUMMARY_COLUMNS,
    ScenarioRun,
    _rho_config,
    _summary_row,
    _write_csv,
    _write_run_csv,
    _write_switch_log_csv,
    _write_theory_csv,
    scenario_runs,
    validate_metric_consistency,
)
from plot_benchmark import generate_figures  # noqa: E402
from viu_mrob_tfm.simulations import (  # noqa: E402
    INFO_REQUIREMENT,
    POLICY_AUCTION_CBBA,
    POLICY_CENTRALIZED_LIMITED_COMM,
    POLICY_CENTRALIZED_MINCOST,
    POLICY_GREEDY_NEAREST,
    POLICY_ORACLE_CLAIRVOYANT,
    POLICY_PIBT,
    POLICY_RANDOM_FEASIBLE,
    POLICY_RESPONSE_THRESHOLD,
    POLICY_MARL_PROXY,
    POLICY_SMITH_FULL,
    POLICY_SMITH_QR_BELIEF,
    POLICY_SMITH_QR_CLEARING_GUARD,
    POLICY_SMITH_QR_FULL,
    POLICY_SMITH_QR_STICKY,
    POLICY_TOKEN_PASSING,
    WAREHOUSE_ASSIGNMENT_POLICIES,
    WarehouseConfig,
    run_warehouse_simulation,
)


BASE_SEED = 2026
FULL_SEEDS = list(range(2026, 2046))
RANDOM_SEEDS = list(range(2026, 2031))
DEFAULT_OUT = Path("results/benchmark-v27-full")


@dataclass(frozen=True)
class MethodSpec:
    key: str
    policy: str
    label: str
    family: str
    params: dict[str, Any]
    seeds: list[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "run", "status", "pause", "resume", "stop"])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--params", type=Path, default=Path("configs/tuned_params_v26.json"))
    parser.add_argument("--poll", type=float, default=20.0, help="Pause polling interval in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = args.out
    if args.command == "start":
        return start_background(out=out, params=args.params)
    if args.command == "run":
        return run(out=out, params=args.params, poll=args.poll)
    if args.command == "status":
        print_status(out)
        return 0
    if args.command == "pause":
        control_file(out, "pause.flag").write_text("pause requested\n", encoding="utf-8")
        print(f"Pause requested. Current run will stop after the active simulation finishes: {out}")
        return 0
    if args.command == "resume":
        control_file(out, "pause.flag").unlink(missing_ok=True)
        print(f"Resume requested: {out}")
        return 0
    if args.command == "stop":
        control_file(out, "stop.flag").write_text("stop requested\n", encoding="utf-8")
        print(f"Stop requested. Runner will exit after the active simulation finishes: {out}")
        return 0
    raise AssertionError(args.command)


def start_background(out: Path, params: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    stdout = (out / "runner.log").open("a", encoding="utf-8")
    stderr = (out / "runner.err.log").open("a", encoding="utf-8")
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--out",
        str(out),
        "--params",
        str(params),
    ]
    creationflags = 0
    kwargs: dict[str, Any] = {"cwd": str(ROOT), "stdout": stdout, "stderr": stderr}
    if os.name == "nt":
        creationflags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(cmd, **kwargs)
    write_state(
        out,
        {
            "status": "starting",
            "pid": process.pid,
            "started_at": timestamp(),
            "updated_at": timestamp(),
            "out": str(out),
            "params": str(params),
        },
    )
    print(f"Started v2.7 benchmark in background. PID={process.pid}")
    print(f"Status: python scripts\\benchmark_v27_daemon.py status --out {out}")
    print(f"Pause:  python scripts\\benchmark_v27_daemon.py pause --out {out}")
    print(f"Resume: python scripts\\benchmark_v27_daemon.py resume --out {out}")
    return 0


def run(out: Path, params: Path, poll: float) -> int:
    out.mkdir(parents=True, exist_ok=True)
    (out / "stop.flag").unlink(missing_ok=True)
    tuned_params = load_params(params)
    methods = build_methods(tuned_params)
    runs = build_runs()
    tasks = [
        (scenario_run, method, seed)
        for scenario_run in runs
        for method in methods
        for seed in method.seeds
    ]
    completed = load_completed(out)
    rows = load_summary_rows(out)
    write_state(
        out,
        {
            "status": "running",
            "pid": os.getpid(),
            "started_at": timestamp(),
            "updated_at": timestamp(),
            "completed": len(completed),
            "total": len(tasks),
            "out": str(out),
        },
    )
    append_log(out, f"RUN start total={len(tasks)} completed={len(completed)}")
    try:
        for scenario_run, method, seed in tasks:
            key = task_key(scenario_run, method, seed)
            if key in completed:
                continue
            wait_if_paused(out, poll=poll, total=len(tasks), completed=len(completed))
            if control_file(out, "stop.flag").exists():
                update_state(out, status="stopped", updated_at=timestamp(), completed=len(completed), total=len(tasks))
                append_log(out, "STOP requested; exiting cleanly.")
                return 0
            update_state(
                out,
                status="running",
                updated_at=timestamp(),
                completed=len(completed),
                total=len(tasks),
                current=key,
            )
            row = execute_task(out, scenario_run, method, seed)
            rows.append(row)
            append_summary_row(out, row)
            completed.add(key)
            save_completed(out, completed)
            update_state(
                out,
                status="running",
                updated_at=timestamp(),
                completed=len(completed),
                total=len(tasks),
                current="",
                last_completed=key,
            )
        finalize(out, rows, tuned_params, methods)
        update_state(out, status="completed", updated_at=timestamp(), completed=len(completed), total=len(tasks))
        append_log(out, "RUN completed.")
        return 0
    except Exception as exc:
        update_state(out, status="failed", updated_at=timestamp(), error=repr(exc))
        append_log(out, f"FAILED {exc!r}")
        raise


def execute_task(out: Path, scenario_run: ScenarioRun, method: MethodSpec, seed: int) -> dict[str, Any]:
    overrides = dict(scenario_run.overrides)
    overrides.update(method.params)
    if scenario_run.name == "nominal_flow_big" and method.key.startswith("smith"):
        overrides["spatial_scale"] = 12.0
    overrides["seed"] = seed
    overrides["scenario_name"] = scenario_run.name
    overrides["assignment_policy"] = method.policy
    config = WarehouseConfig(**overrides)
    started = time.perf_counter()
    result = run_warehouse_simulation(config)
    runtime = time.perf_counter() - started
    # Reuse the benchmark summary schema with the simulator policy key, then
    # expose the compact v2.7 method key in the persisted dataset. Some shared
    # lookup tables, e.g. INFO_REQUIREMENT, are keyed by simulator policy names
    # and do not know aliases such as "smith".
    row = _summary_row(
        result.summary,
        scenario_run,
        method.policy,
        method.label,
        method.family,
        runtime,
        result.time.size,
    )
    row["method"] = method.key
    row["label"] = method.label
    row["family"] = method.family
    row["run_mode"] = "FULL_V27"
    row["switch_event_log_path"] = _write_switch_log_csv(
        out,
        scenario_run,
        method.key,
        seed,
        result.summary.get("switch_events", []),
    )
    _write_run_csv(out, scenario_run, method.key, seed, result)
    if method.key.startswith("smith"):
        _write_theory_csv(out, scenario_run, method.key, seed, result)
    append_log(
        out,
        (
            f"{scenario_run.name}/{scenario_run.case} | {method.label} seed={seed} "
            f"capture={row.get('reward_capture_ratio')} thr={row.get('throughput_steady')} "
            f"runtime={runtime:.2f}s"
        ),
    )
    return row


def build_methods(tuned_params: dict[str, dict[str, Any]]) -> list[MethodSpec]:
    full = dict(tuned_params.get(POLICY_SMITH_FULL, {}))
    full.update(
        {
            "clearing_mode": "tick",
            "lateral_switch_rule": "potential",
            "price_feedback_signal": "effective_committed",
        }
    )
    smith_raw = dict(full, smith_occupancy_mode="raw", smith_prices_enabled=True, smith_integer_clearing_enabled=True)
    smith_effective = dict(
        full,
        smith_occupancy_mode="effective",
        smith_prices_enabled=True,
        smith_integer_clearing_enabled=True,
    )
    smith_no_prices = dict(smith_raw, smith_prices_enabled=False, price_gain=0.0)
    smith_no_integer = dict(smith_raw, smith_integer_clearing_enabled=False)
    smith_qr = dict(
        smith_raw,
        descriptor_belief_tau=24.0,
        commitment_ttl=12.0,
        local_quorum_grace=4.0,
        clearing_connectivity_guard=2.2,
        qr_patrol_gain=1.6,
    )
    return [
        MethodSpec("smith", POLICY_SMITH_FULL, "Smith main raw", "ours", smith_raw, FULL_SEEDS),
        MethodSpec("smith_no_prices", POLICY_SMITH_FULL, "Smith no prices", "ablation", smith_no_prices, FULL_SEEDS),
        MethodSpec("smith_no_integer", POLICY_SMITH_FULL, "Smith no integer", "ablation", smith_no_integer, FULL_SEEDS),
        MethodSpec("smith_qr_belief", POLICY_SMITH_QR_BELIEF, "Smith-QR belief", "ours", smith_qr, FULL_SEEDS),
        MethodSpec("smith_qr_sticky", POLICY_SMITH_QR_STICKY, "Smith-QR sticky", "ours", smith_qr, FULL_SEEDS),
        MethodSpec(
            "smith_qr_clearing_guard",
            POLICY_SMITH_QR_CLEARING_GUARD,
            "Smith-QR clearing guard",
            "ours",
            smith_qr,
            FULL_SEEDS,
        ),
        MethodSpec("smith_qr_full", POLICY_SMITH_QR_FULL, "Smith-QR full", "ours", smith_qr, FULL_SEEDS),
        MethodSpec(
            "smith_effective_occupancy",
            POLICY_SMITH_FULL,
            "Smith effective occupancy",
            "ablation",
            smith_effective,
            FULL_SEEDS,
        ),
        MethodSpec("classic_greedy_nearest", POLICY_GREEDY_NEAREST, "Classic greedy nearest", "classic", {}, FULL_SEEDS),
        MethodSpec(
            "classic_centralized_mincost",
            POLICY_CENTRALIZED_MINCOST,
            "Classic centralized min-cost",
            "classic",
            {},
            FULL_SEEDS,
        ),
        MethodSpec(
            "classic_centralized_limited_comm",
            POLICY_CENTRALIZED_LIMITED_COMM,
            "Classic centralized limited-comm",
            "classic",
            {},
            FULL_SEEDS,
        ),
        MethodSpec(
            "classic_auction_cbba",
            POLICY_AUCTION_CBBA,
            "Classic auction/CBBA-lite",
            "classic",
            tuned_params.get(POLICY_AUCTION_CBBA, {}),
            FULL_SEEDS,
        ),
        MethodSpec("proxy_token_passing", POLICY_TOKEN_PASSING, "Proxy token passing", "sota_proxy", {}, FULL_SEEDS),
        MethodSpec("proxy_pibt_priority", POLICY_PIBT, "Proxy PIBT priority", "sota_proxy", {}, FULL_SEEDS),
        MethodSpec("oracle_clairvoyant", POLICY_ORACLE_CLAIRVOYANT, "Oracle clairvoyant", "oracle", {}, FULL_SEEDS),
        MethodSpec(
            "response_threshold",
            POLICY_RESPONSE_THRESHOLD,
            "Response threshold",
            "classic",
            tuned_params.get(POLICY_RESPONSE_THRESHOLD, {}),
            FULL_SEEDS,
        ),
        MethodSpec("marl_proxy_policy", POLICY_MARL_PROXY, "MARL proxy shared policy", "marl_proxy", {}, FULL_SEEDS),
        MethodSpec("random_feasible", POLICY_RANDOM_FEASIBLE, "Random feasible", "floor", {}, RANDOM_SEEDS),
    ]


def build_runs() -> list[ScenarioRun]:
    runs: list[ScenarioRun] = []
    runs.extend(scenario_runs("nominal_flow", quick=False))
    runs.extend(scenario_runs("nominal_flow_big", quick=False))
    runs.extend(scenario_runs("load_sweep", quick=True))
    runs.extend(scenario_runs("scarcity_extreme", quick=False))
    runs.extend(build_triage_scarcity_priority())
    runs.extend(scenario_runs("robot_failures", quick=False))
    runs.extend(scenario_runs("task_churn", quick=False))
    for run in scenario_runs("comm_degradation", quick=True):
        if run.case in {"R12_p0", "R6_p0", "R4_p0", "R3_p0", "R1.5_p0", "R12_p0.9"}:
            runs.append(run)
    return runs


def build_triage_scarcity_priority() -> list[ScenarioRun]:
    duration = 600.0
    config = _rho_config(duration, 120, rho=2.5, min_weight=2, max_weight=10, spawn_process="poisson")
    config.update(
        {
            "scenario_name": "scarcity_priority",
            "max_active_loads": 10,
            "spawn_period": 3.0,
            "reward_base": 0.5,
            "reward_per_weight": 0.0,
        }
    )
    return [ScenarioRun("scarcity_priority", "triage_forced", config)]


def finalize(out: Path, rows: list[dict[str, Any]], tuned_params: dict[str, dict[str, Any]], methods: list[MethodSpec]) -> None:
    try:
        validate_metric_consistency(rows)
    except RuntimeError as exc:
        append_log(out, f"METRIC WARNING {exc!r}")
    summary_csv = out / "summary.csv"
    summary_json = out / "summary.json"
    _write_csv(summary_csv, rows, SUMMARY_COLUMNS)
    summary_json.write_text(json.dumps(rows, indent=2, sort_keys=True, allow_nan=True), encoding="utf-8")
    write_v27_summary_md(out / "summary.md", rows, methods, tuned_params)
    for path in generate_figures(summary_csv, out / "figures"):
        append_log(out, f"FIGURE {path}")


def write_v27_summary_md(
    path: Path,
    rows: list[dict[str, Any]],
    methods: list[MethodSpec],
    tuned_params: dict[str, dict[str, Any]],
) -> None:
    lines = [
        "# Warehouse coalition benchmark v2.7 full run",
        "",
        "## Run Configuration",
        "",
        "- Seeds: 2026-2045 for all primary methods; random_feasible uses 2026-2030.",
        "- Smith main uses raw occupancy, prices, integer clearing, potential lateral switching and tick clearing.",
        "- nominal_flow_big sets `spatial_scale=12.0` for Smith-family methods.",
        "",
        "## Methods",
        "",
        "| Method | Policy | Family | Seeds | Params |",
        "|---|---|---|---:|---|",
    ]
    for method in methods:
        lines.append(
            f"| {method.label} | `{method.policy}` | {method.family} | {len(method.seeds)} | "
            f"`{json.dumps(method.params, sort_keys=True)}` |"
        )
    lines.extend(["", "## Aggregate Results", ""])
    lines.append(
        "| Scenario | Case | Method | Capture | Discovered | Throughput | Lateral/delivery | Recovery | Post-discovery | RMSE theory |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for (scenario, case, label), group in sorted(group_rows(rows).items()):
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario,
                    case,
                    label,
                    fmt_metric(group, "reward_capture_ratio"),
                    fmt_metric(group, "reward_capture_discovered"),
                    fmt_metric(group, "throughput_steady"),
                    fmt_metric(group, "lateral_switches_per_delivery"),
                    fmt_metric(group, "recovery_time_s"),
                    fmt_metric(group, "mean_time_post_discovery"),
                    fmt_metric(group, "staffing_rmse_vs_theory"),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def group_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("scenario", "")), str(row.get("scenario_case", "")), str(row.get("label", "")))
        grouped.setdefault(key, []).append(row)
    return grouped


def fmt_metric(rows: list[dict[str, Any]], metric: str) -> str:
    values = [as_float(row.get(metric)) for row in rows]
    values = [value for value in values if math.isfinite(value)]
    if not values:
        return "n/a"
    return f"{sum(values) / len(values):.3g}"


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def append_summary_row(out: Path, row: dict[str, Any]) -> None:
    path = out / "summary_partial.csv"
    first = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS)
        if first:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in SUMMARY_COLUMNS})


def load_summary_rows(out: Path) -> list[dict[str, Any]]:
    path = out / "summary_partial.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def task_key(scenario_run: ScenarioRun, method: MethodSpec, seed: int) -> str:
    return f"{scenario_run.name}/{scenario_run.case}/{method.key}/{seed}"


def load_completed(out: Path) -> set[str]:
    path = out / "completed.json"
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def save_completed(out: Path, completed: set[str]) -> None:
    (out / "completed.json").write_text(json.dumps(sorted(completed), indent=2), encoding="utf-8")


def load_params(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def wait_if_paused(out: Path, poll: float, total: int, completed: int) -> None:
    pause = control_file(out, "pause.flag")
    while pause.exists():
        update_state(out, status="paused", updated_at=timestamp(), completed=completed, total=total)
        time.sleep(max(1.0, poll))
    update_state(out, status="running", updated_at=timestamp(), completed=completed, total=total)


def control_file(out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    return out / name


def write_state(out: Path, state: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def update_state(out: Path, **updates: Any) -> None:
    state_path = out / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state.update(updates)
    write_state(out, state)


def print_status(out: Path) -> None:
    state_path = out / "state.json"
    if not state_path.exists():
        print(f"No state file yet at {state_path}")
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    completed = int(state.get("completed", 0) or 0)
    total = int(state.get("total", 0) or 0)
    pct = 100.0 * completed / total if total else math.nan
    print(f"status: {state.get('status', 'unknown')}")
    print(f"pid: {state.get('pid', 'n/a')}")
    print(f"progress: {completed}/{total} ({pct:.2f}%)" if math.isfinite(pct) else f"progress: {completed}/{total}")
    print(f"current: {state.get('current', '')}")
    print(f"last_completed: {state.get('last_completed', '')}")
    print(f"updated_at: {state.get('updated_at', '')}")
    print(f"out: {out}")
    log = out / "runner.log"
    if log.exists():
        print("\nlast log lines:")
        lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()[-8:]
        for line in lines:
            print(line)


def append_log(out: Path, message: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with (out / "runner.log").open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp()}] {message}\n")


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    raise SystemExit(main())
