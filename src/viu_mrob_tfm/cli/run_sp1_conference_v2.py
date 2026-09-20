"""CLI for the targeted SP1 conference-remediation V2 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.conference_v2 import EXPERIMENTS, execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp1_conference_v2.yaml"),
    )
    parser.add_argument("--experiment", choices=["all", *EXPERIMENTS], default="all")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional external output path; used to keep the execution worktree clean.",
    )
    arguments = parser.parse_args()
    manifest = execute(
        arguments.config,
        experiment=arguments.experiment,
        resume=arguments.resume,
        output_dir=arguments.output_dir,
    )
    print(
        json.dumps(
            {
                "experiment_id": manifest["experiment_id"],
                "audit_status": manifest["audit_status"],
                "scientific_status": manifest["scientific_status"],
                "duration_s": manifest["duration_s"],
                "output_dir": manifest["configuration"]["effective_output_dir"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
