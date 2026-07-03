"""Run the realistic warehouse AMR simulation and save reproducible outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.simulations import WarehouseConfig, run_warehouse_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--duration", type=float, default=160.0)
    parser.add_argument("--loads", type=int, default=6)
    parser.add_argument("--output", type=Path, default=Path("results/raw/warehouse-realistic-smoke"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = WarehouseConfig(
        seed=args.seed,
        duration=args.duration,
        max_loads=args.loads,
    )
    result = run_warehouse_simulation(config)
    args.output.mkdir(parents=True, exist_ok=True)

    summary_path = args.output / "summary.json"
    summary_path.write_text(
        json.dumps(result.summary, indent=2, sort_keys=True, allow_nan=True),
        encoding="utf-8",
    )
    np.savez_compressed(
        args.output / "trajectories.npz",
        time=result.time,
        robot_positions=result.robot_positions,
        headings=result.headings,
        load_positions=result.load_positions,
        load_status=result.load_status,
        assignments=result.assignments,
        prices=result.prices,
        contact_counts=result.contact_counts,
        wheel_speeds=result.wheel_speeds,
        linear_speeds=result.linear_speeds,
        angular_speeds=result.angular_speeds,
        communication_degrees=result.communication_degrees,
        formation_errors=result.formation_errors,
    )
    loads_path = args.output / "loads.csv"
    lines = ["id,spawn_time,weight,source_x,source_y,target_x,target_y,status,coalition_time,delivered_time"]
    for load in result.loads:
        lines.append(
            ",".join(
                [
                    load.identifier,
                    f"{load.spawn_time:.3f}",
                    str(load.weight),
                    f"{load.source[0]:.6f}",
                    f"{load.source[1]:.6f}",
                    f"{load.target[0]:.6f}",
                    f"{load.target[1]:.6f}",
                    str(load.status),
                    f"{load.coalition_time:.6f}",
                    f"{load.delivered_time:.6f}",
                ]
            )
        )
    loads_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(result.summary, indent=2, sort_keys=True, allow_nan=True))
    print(f"Saved summary to {summary_path}")
    print(f"Saved trajectories to {args.output / 'trajectories.npz'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
