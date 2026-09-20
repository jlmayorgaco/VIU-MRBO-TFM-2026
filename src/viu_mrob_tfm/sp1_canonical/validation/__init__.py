"""Integral E0--E6 validation campaign for canonical SP1."""

from viu_mrob_tfm.sp1_canonical.validation.experiment import execute, run_validation_config
from viu_mrob_tfm.sp1_canonical.validation.conference import run_conference_config

__all__ = ["execute", "run_conference_config", "run_validation_config"]
