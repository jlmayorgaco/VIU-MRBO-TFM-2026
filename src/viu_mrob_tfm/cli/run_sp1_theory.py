"""CLI for the SP1 quorum and integer-closure campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp1.experiment import execute


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp1_theory.yaml"),
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    print(execute(args.config, smoke=args.smoke))


if __name__ == "__main__":
    main()
