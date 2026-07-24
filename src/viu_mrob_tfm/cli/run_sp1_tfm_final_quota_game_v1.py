"""CLI for the final SP1 quota-game benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.quota_game_benchmark import (
    execute_campaign,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preview", "full"), required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(
            "experiments/configs/sp1_tfm_final_quota_game_benchmark_v1.yaml"
        ),
    )
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute completed checkpoint shards.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Documentary alias: resume is the default behavior.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo = Path.cwd()
    output = execute_campaign(
        repo=repo,
        config_path=args.config.resolve(),
        mode=args.mode,
        workers=args.workers,
        force=args.force,
    )
    print(output)


if __name__ == "__main__":
    main()
