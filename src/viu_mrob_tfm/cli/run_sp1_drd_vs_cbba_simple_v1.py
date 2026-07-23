"""CLI for the SP1 DRD-simple versus CBBA-1-Capacity campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.drd_cbba_benchmark import STAGES, execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp1_drd_vs_cbba_simple_v1.yaml"),
    )
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--selected-parameters", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    arguments = parser.parse_args()
    manifest = execute(
        arguments.config,
        stage=arguments.stage,
        selected_parameters_path=arguments.selected_parameters,
        output_dir=arguments.output_dir,
        resume=arguments.resume,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
