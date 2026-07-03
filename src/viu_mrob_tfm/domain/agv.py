"""Legacy mobile-robot aliases kept for backward compatibility."""

from viu_mrob_tfm.domain.amr import AMR
from viu_mrob_tfm.domain.state import AMRState

AGV = AMR
AGVState = AMRState

__all__ = ["AGV", "AGVState"]
