"""CLI for audited SP3 evidence postprocessing."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp3.evidence import execute


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp3_wrench_evidence.yaml"),
    )
    args = parser.parse_args()
    print(execute(args.config))


if __name__ == "__main__":
    main()
