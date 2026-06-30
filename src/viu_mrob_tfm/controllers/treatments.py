"""Treatment policy descriptors for the experimental ladder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DynamicsKind = Literal["none", "replicator", "smith"]
AssignmentKind = Literal["greedy_local", "greedy_dac", "preference", "centralized"]


@dataclass(frozen=True, slots=True)
class TreatmentPolicy:
    """Behavioral switches used by the kinematic simulator."""

    code: str
    label: str
    dynamics: DynamicsKind
    assignment: AssignmentKind
    uses_dac: bool
    uses_spatial_payoff: bool
    uses_modulated_rate: bool
    uses_adaptive_prices: bool = False


T1_GREEDY_LOCAL = TreatmentPolicy(
    code="t1_greedy",
    label="T1 greedy local",
    dynamics="none",
    assignment="greedy_local",
    uses_dac=False,
    uses_spatial_payoff=False,
    uses_modulated_rate=False,
)

T2_DAC_GREEDY = TreatmentPolicy(
    code="t2_dac_greedy",
    label="T2 DAC + greedy",
    dynamics="none",
    assignment="greedy_dac",
    uses_dac=True,
    uses_spatial_payoff=True,
    uses_modulated_rate=False,
)

T3_REPLICATOR = TreatmentPolicy(
    code="t3_replicator",
    label="T3 distributed replicator",
    dynamics="replicator",
    assignment="preference",
    uses_dac=True,
    uses_spatial_payoff=True,
    uses_modulated_rate=True,
)

T4_SMITH = TreatmentPolicy(
    code="t4_smith",
    label="T4 Smith proposed",
    dynamics="smith",
    assignment="preference",
    uses_dac=True,
    uses_spatial_payoff=True,
    uses_modulated_rate=True,
)

T5_CENTRALIZED = TreatmentPolicy(
    code="t5_centralized",
    label="T5 centralized replanning",
    dynamics="none",
    assignment="centralized",
    uses_dac=False,
    uses_spatial_payoff=False,
    uses_modulated_rate=False,
)

T6_SINGLE_CLOCK = TreatmentPolicy(
    code="t6_single_clock",
    label="T6 single-clock adaptive Smith auction",
    dynamics="smith",
    assignment="preference",
    uses_dac=True,
    uses_spatial_payoff=True,
    uses_modulated_rate=True,
    uses_adaptive_prices=True,
)


_ALIASES = {
    "nominal": T4_SMITH,
    "nominal_consensus": T4_SMITH,
    "adaptive": T4_SMITH,
    "adaptive_consensus": T4_SMITH,
    "smith": T4_SMITH,
    "t4": T4_SMITH,
    "t4_smith": T4_SMITH,
    "greedy": T1_GREEDY_LOCAL,
    "t1": T1_GREEDY_LOCAL,
    "t1_greedy": T1_GREEDY_LOCAL,
    "dac_greedy": T2_DAC_GREEDY,
    "t2": T2_DAC_GREEDY,
    "t2_dac_greedy": T2_DAC_GREEDY,
    "replicator": T3_REPLICATOR,
    "t3": T3_REPLICATOR,
    "t3_replicator": T3_REPLICATOR,
    "centralized": T5_CENTRALIZED,
    "centralised": T5_CENTRALIZED,
    "t5": T5_CENTRALIZED,
    "t5_centralized": T5_CENTRALIZED,
    "adaptive_prices": T6_SINGLE_CLOCK,
    "single_clock": T6_SINGLE_CLOCK,
    "single_clock_smith": T6_SINGLE_CLOCK,
    "t6": T6_SINGLE_CLOCK,
    "t6_single_clock": T6_SINGLE_CLOCK,
}


def resolve_treatment(name: str) -> TreatmentPolicy:
    """Resolve a controller/treatment name into a policy descriptor."""

    key = name.strip().lower().replace("-", "_")
    if key not in _ALIASES:
        known = ", ".join(sorted(_ALIASES))
        msg = f"Unknown treatment {name!r}. Known treatments: {known}"
        raise ValueError(msg)
    return _ALIASES[key]
