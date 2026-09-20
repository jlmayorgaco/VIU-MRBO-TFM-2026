"""CLI for the SP1 dynamics benchmark V3 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.validation.dynamics_benchmark_v3 import STAGES, execute


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/configs/sp1_dynamics_benchmark_v3.yaml"))
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
    print(json.dumps({key: manifest[key] for key in ("experiment_id", "stage", "audit_status", "duration_s", "primary_runs", "all_rows")}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
