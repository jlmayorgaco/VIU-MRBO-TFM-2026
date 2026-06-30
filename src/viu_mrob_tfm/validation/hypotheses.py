"""Hypothesis-suite facade for the organized V6 repository."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class HypothesisSuite:
    """Small object wrapper around the current validation suite."""

    output_dir: Path = Path("results/validation_suite_v1")
    figure_path: Path = Path("docs/report/figures/fig-validation-suite-summary.png")

    def run(self) -> Any:
        from viu_mrob_tfm.validation.suite import run_validation_suite

        return run_validation_suite(output_dir=self.output_dir, figure_path=self.figure_path)
