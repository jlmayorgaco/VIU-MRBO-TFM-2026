"""Canonical SP1: distributed coalition formation with heterogeneous roles."""

from viu_mrob_tfm.sp1_canonical.experiment import execute, run_sp1_config
from viu_mrob_tfm.sp1_canonical.model import FormationWorld, generate_world

__all__ = ["FormationWorld", "execute", "generate_world", "run_sp1_config"]
