"""CLI for the frozen SP1 conference validation campaign."""

from __future__ import annotations

import argparse
import json

from viu_mrob_tfm.sp1_canonical.validation.conference import EXPERIMENTS, execute


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SP1 conference validation campaign")
    parser.add_argument(
        "--config",
        default="experiments/configs/sp1_conference_v1.yaml",
        help="Frozen YAML campaign configuration",
    )
    parser.add_argument("--experiment", choices=["all", *EXPERIMENTS], default="all")
    parser.add_argument("--resume", action="store_true", help="Reuse completed per-experiment CSV artifacts after verifying the config snapshot")
    arguments = parser.parse_args()
    manifest = execute(arguments.config, experiment=arguments.experiment, resume=arguments.resume)
    print(json.dumps({
        "experiment_id": manifest["experiment_id"],
        "audit_status": manifest["audit_status"],
        "scientific_status": manifest["scientific_status"],
        "duration_s": manifest["duration_s"],
        "output_dir": manifest["configuration"]["output_dir"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
