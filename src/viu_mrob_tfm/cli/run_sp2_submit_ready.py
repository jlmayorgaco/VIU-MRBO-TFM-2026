"""CLI for the SP2 closure campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp2_canonical.benchmark import run_sp2_submit_ready_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp2_submit_ready.yaml"),
    )
    parser.add_argument(
        "--resume-from-raw",
        action="store_true",
        help="Regenerate processed artifacts from a matching frozen config and existing raw CSV/NPZ files.",
    )
    arguments = parser.parse_args()
    manifest = run_sp2_submit_ready_config(
        arguments.config,
        resume_from_raw=arguments.resume_from_raw,
    )
    print(f"{manifest['experiment_id']}: {manifest['status']}")


if __name__ == "__main__":
    main()
