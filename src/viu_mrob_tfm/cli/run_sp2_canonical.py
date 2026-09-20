"""CLI for the reduced canonical SP2 campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp2_canonical.experiment import run_sp2_canonical_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp2_canonical_smoke.yaml"),
    )
    args = parser.parse_args()
    manifest = run_sp2_canonical_config(args.config)
    print(
        f"{manifest['experiment_id']}: {manifest['status']} "
        f"({len(manifest['artifacts'])} artifacts)"
    )


if __name__ == "__main__":
    main()
