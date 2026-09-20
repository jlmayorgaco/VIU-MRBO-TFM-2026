"""CLI for the canonical SP1 E0--E6 validation battery."""

from __future__ import annotations

import argparse
import json

from viu_mrob_tfm.sp1_canonical.validation.experiment import EXPERIMENTS, execute


def main() -> None:
    parser = argparse.ArgumentParser(description="Run canonical SP1 validation experiments E0--E6")
    parser.add_argument(
        "--config",
        default="experiments/configs/sp1_validation_smoke.yaml",
        help="YAML campaign configuration",
    )
    parser.add_argument(
        "--experiment",
        choices=["all", *EXPERIMENTS],
        default="all",
        help="Run the complete battery or one experiment",
    )
    arguments = parser.parse_args()
    manifest = execute(arguments.config, experiment=arguments.experiment)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
