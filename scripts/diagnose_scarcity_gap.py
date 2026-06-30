"""Diagnose the scarcity gap between Smith full and greedy nearest."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark_warehouse_methods import scenario_runs  # noqa: E402
from viu_mrob_tfm.simulations import (  # noqa: E402
    LOAD_DELIVERED,
    LOAD_RECRUITING,
    LOAD_TRANSPORT,
    POLICY_GREEDY_NEAREST,
    POLICY_SMITH_FULL,
    WarehouseConfig,
    run_warehouse_simulation,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=Path("results/benchmark-v2/diagnostics/scarcity_gap.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenario = scenario_runs("scarcity_extreme", quick=True)[0]
    rows = []
    for method in [POLICY_SMITH_FULL, POLICY_GREEDY_NEAREST]:
        config = WarehouseConfig(
            **scenario.overrides,
            seed=args.seed,
            scenario_name=scenario.name,
            assignment_policy=method,
        )
        result = run_warehouse_simulation(config)
        for load_idx, load in enumerate(result.loads):
            status = result.load_status[:, load_idx]
            recruiting = _first_time(result.time, status == LOAD_RECRUITING)
            transport = _first_time(result.time, status == LOAD_TRANSPORT)
            delivered = _first_time(result.time, status == LOAD_DELIVERED)
            max_contact = float(result.contact_counts[:, load_idx].max())
            rows.append(
                {
                    "method": method,
                    "load": load.identifier,
                    "weight": load.weight,
                    "reward": load.reward,
                    "spawn_time": load.spawn_time,
                    "first_recruiting_time": recruiting,
                    "first_transport_time": transport,
                    "delivered_time": delivered,
                    "quorum_wait": transport - recruiting if transport == transport and recruiting == recruiting else "",
                    "max_contact": max_contact,
                    "final_status": int(load.status),
                }
            )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved scarcity diagnosis to {args.out}")
    return 0


def _first_time(time, mask) -> float:
    indices = mask.nonzero()[0]
    return float(time[int(indices[0])]) if indices.size else float("nan")


if __name__ == "__main__":
    raise SystemExit(main())
