"""CLI for the blocking preview and full SCALE-QPG V2 benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.scale_qpg_benchmark import (
    execute_campaign,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preview", "full"), required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "experiments/configs/sp1_scale_qpg_benchmark_v2.yaml"
        ),
    )
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Documentary alias; checkpoint resume is the default.",
    )
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    output = execute_campaign(
        repo=Path.cwd(),
        config_path=arguments.config.resolve(),
        mode=arguments.mode,
        workers=arguments.workers,
        force=arguments.force,
    )
    print(output)


if __name__ == "__main__":
    main()
