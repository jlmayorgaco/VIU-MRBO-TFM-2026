"""Run the confirmatory SP3 wrench Nash/primal-dual campaign."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.sp3.wrench_nash_game import run_sp3_wrench_nash_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    manifest = run_sp3_wrench_nash_config(args.config)
    print(manifest)


if __name__ == "__main__":
    main()
