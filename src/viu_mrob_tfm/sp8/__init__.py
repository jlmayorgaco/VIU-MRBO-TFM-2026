"""Canonical SP8 scale and imperfect-network study."""

from viu_mrob_tfm.sp8.experiment import run_sp8_config
from viu_mrob_tfm.sp8.theory import (
    asynchronous_visible_better_response,
    exhaustive_global_oracle,
    global_conflict_pairs,
    network_potential,
    retransmission_failure_probability,
    verify_exact_network_potential,
    visible_conflict_pairs,
)

__all__ = [
    "asynchronous_visible_better_response",
    "exhaustive_global_oracle",
    "global_conflict_pairs",
    "network_potential",
    "retransmission_failure_probability",
    "run_sp8_config",
    "verify_exact_network_potential",
    "visible_conflict_pairs",
]
