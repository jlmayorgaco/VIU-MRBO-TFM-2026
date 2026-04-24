"""Run a configured placeholder experiment from the command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.experiments.runner import ExperimentRunner
from viu_mrob_tfm.utils.logging import get_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        required=True,
        help="Path to an experiment YAML configuration file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = get_logger("run_experiment")
    runner = ExperimentRunner()
    summary = runner.run(args.config)
    logger.info("Experiment completed: %s", summary["experiment"])
    logger.info("Summary saved under: %s", summary["output_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
