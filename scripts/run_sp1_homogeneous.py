"""Run the versioned homogeneous recruitment experiment."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.sp1.homogeneous import run_homogeneous_campaign


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        nargs="?",
        default="configs/experiments/sp1/SP1_HOMOGENEOUS_v1.yaml",
    )
    args = parser.parse_args()
    result = run_homogeneous_campaign(args.config)
    print(result["manifest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
