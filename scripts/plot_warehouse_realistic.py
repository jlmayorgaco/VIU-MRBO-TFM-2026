"""Run and plot the realistic 2D warehouse simulation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.plotting import save_warehouse_animation, save_warehouse_plot_suite
from viu_mrob_tfm.simulations import WarehouseConfig, run_warehouse_simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--duration", type=float, default=90.0)
    parser.add_argument("--loads", type=int, default=3)
    parser.add_argument("--max-active-loads", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("results/figures/warehouse-realistic-2d"))
    parser.add_argument("--mp4", action="store_true", help="Also render an MP4 animation.")
    parser.add_argument("--fps", type=int, default=18)
    parser.add_argument("--stride", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = WarehouseConfig(
        seed=args.seed,
        duration=args.duration,
        max_loads=args.loads,
        max_active_loads=args.max_active_loads,
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
        preferences=result.preferences,
        prices=result.prices,
        effective_occupancy=result.effective_occupancy,
        contact_counts=result.contact_counts,
        wheel_speeds=result.wheel_speeds,
        linear_speeds=result.linear_speeds,
        angular_speeds=result.angular_speeds,
        communication_degrees=result.communication_degrees,
        formation_errors=result.formation_errors,
    )
    plot_paths = save_warehouse_plot_suite(result, args.output)
    video_path = None
    if args.mp4:
        video_path = save_warehouse_animation(
            result,
            args.output / "warehouse_realistic_simulation.mp4",
            fps=args.fps,
            stride=args.stride,
        )

    print(json.dumps(result.summary, indent=2, sort_keys=True, allow_nan=True))
    print("PNG outputs:")
    for path in plot_paths:
        print(f"  {path}")
    if video_path is not None:
        print(f"MP4 output:\n  {video_path}")
    print(f"Data outputs:\n  {summary_path}\n  {args.output / 'trajectories.npz'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
