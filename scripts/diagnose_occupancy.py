"""Audit raw vs effective occupancy signals for Smith variants."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_warehouse_methods import scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import POLICY_SMITH_FULL, WarehouseConfig, run_warehouse_simulation  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--scenario", choices=["nominal_flow", "scarcity_extreme"], default="nominal_flow")
    parser.add_argument("--out", type=Path, default=Path("results/benchmark-v2/diagnostics/occupancy_audit.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run = scenario_runs(args.scenario, quick=True)[0]
    overrides = dict(run.overrides)
    overrides["duration"] = max(300.0, float(overrides["duration"]))
    config = WarehouseConfig(
        **overrides,
        seed=args.seed,
        scenario_name=run.name,
        assignment_policy=POLICY_SMITH_FULL,
    )
    result = run_warehouse_simulation(config)
    rows = []
    previous_assignments = result.assignments[0]
    for step, now in enumerate(result.time):
        assignments = result.assignments[step]
        switched = assignments != previous_assignments
        for load_idx, load in enumerate(result.loads):
            load_number = load_idx + 1
            raw_commitment = int(np.sum(assignments == load_number))
            switch_into = int(np.sum(switched & (assignments == load_number)))
            switch_out = int(np.sum(switched & (previous_assignments == load_number)))
            rows.append(
                {
                    "time": float(now),
                    "load": load.identifier,
                    "status": int(result.load_status[step, load_idx]),
                    "z_effective": float(result.effective_occupancy[step, load_idx]),
                    "contact": float(result.contact_counts[step, load_idx]),
                    "raw_commitment": raw_commitment,
                    "price": float(result.prices[step, load_idx]),
                    "switch_into": switch_into,
                    "switch_out": switch_out,
                    "switch_cause": _switch_cause(switch_into, switch_out),
                }
            )
        previous_assignments = assignments
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    verdict = _verdict(rows)
    verdict_path = args.out.with_suffix(".md")
    verdict_path.write_text(verdict, encoding="utf-8")
    print(f"Saved occupancy audit to {args.out}")
    print(f"Saved verdict to {verdict_path}")
    return 0


def _switch_cause(switch_into: int, switch_out: int) -> str:
    if switch_into and switch_out:
        return "reshuffle"
    if switch_into:
        return "recruit"
    if switch_out:
        return "release"
    return ""


def _verdict(rows: list[dict[str, object]]) -> str:
    effective = np.array([float(row["z_effective"]) for row in rows])
    contact = np.array([float(row["contact"]) for row in rows])
    raw = np.array([float(row["raw_commitment"]) for row in rows])
    switch_count = sum(int(row["switch_into"]) + int(row["switch_out"]) for row in rows)
    lag = float(np.mean(np.maximum(raw - effective, 0.0)))
    mismatch = float(np.mean(np.abs(contact - effective)))
    if lag > mismatch:
        diagnosis = "Hypothesis (b): effective occupancy was under-counting committed but distant robots."
    else:
        diagnosis = "Hypothesis (a): decision, price and clearing signals are using inconsistent units."
    return (
        "# Occupancy Signal Audit\n\n"
        f"- mean max(raw_commitment - z_effective, 0): {lag:.4f}\n"
        f"- mean abs(contact - z_effective): {mismatch:.4f}\n"
        f"- switch events counted: {switch_count}\n\n"
        f"Verdict: {diagnosis}\n\n"
        "Decision applied in v2.1: Smith effective variants use `Psi_tilde=max(Psi, 0.3)` to reduce delayed closure of Phi; clearing remains based on integer contact because payload motion is physical.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
