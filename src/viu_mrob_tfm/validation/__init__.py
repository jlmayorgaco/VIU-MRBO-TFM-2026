"""Replicable validation suite for the TFM mathematical framework."""

from __future__ import annotations

from typing import Any

from viu_mrob_tfm.validation.hypotheses import HypothesisSuite


def run_validation_suite(*args: Any, **kwargs: Any) -> Any:
    """Run the validation suite without importing the CLI module eagerly."""

    from .suite import run_validation_suite as _run_validation_suite

    return _run_validation_suite(*args, **kwargs)


__all__ = ["HypothesisSuite", "run_validation_suite"]
