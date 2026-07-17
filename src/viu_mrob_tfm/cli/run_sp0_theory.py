"""CLI for the submit-ready SP0 theory campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp0.experiment import execute


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp0_theory.yaml"),
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    output = execute(args.config, smoke=args.smoke)
    print(output)


if __name__ == "__main__":
    main()
