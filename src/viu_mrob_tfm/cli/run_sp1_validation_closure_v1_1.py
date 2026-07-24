"""CLI for SP1_TFM_VALIDATION_CLOSURE_v1_1."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.validation_closure_v1_1 import (
    execute_closure,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("full",), default="full")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "experiments/configs/sp1_tfm_validation_closure_v1_1.yaml"
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
    output = execute_closure(
        repo=Path.cwd(),
        config_path=arguments.config.resolve(),
        workers=arguments.workers,
        force=arguments.force,
    )
    print(output)


if __name__ == "__main__":
    main()
