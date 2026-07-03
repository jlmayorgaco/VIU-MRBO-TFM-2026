"""Run a configured experiment from the command line."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from viu_mrob_tfm.experiments.runner import ExperimentRunner
from viu_mrob_tfm.utils.logging import get_logger


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to an experiment YAML configuration file.",
    )
    parser.add_argument(
        "--config",
        dest="config_option",
        help="Path to an experiment YAML configuration file.",
    )
    args = parser.parse_args(argv)
    config = args.config_option or args.config_path
    if config is None:
        parser.error("provide a config path either positionally or with --config")
    args.config = Path(config)
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logger = get_logger("run_experiment")
    runner = ExperimentRunner()
    summary = runner.run(args.config)
    logger.info("Experiment completed: %s", summary["experiment"])
    logger.info("Summary saved under: %s", summary["output_dir"])
    return 0
