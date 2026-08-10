# SP1_N3_DISTRIBUTED_BASELINES_v1 — INVALIDATED

**Do not read any number in this directory.** It is kept only so the decision
to discard it can be audited.

## What was wrong

`cycle_observed` was `true` on every Weighted-Pair-GRAPE row, with a reported
period of exactly one epoch. It was not an oscillation.

Pair-GRAPE crosses from unilateral to joint deviations without moving anyone:
the profile at the end of phase 0 is the profile at the start of phase 1. The
observer's signature was the profile alone, so that unchanged profile looked
like a return to a state already visited, and the run was flagged as cyclic.

The defect is confined to an observational column. `algorithm_status` was
unaffected (Pair-GRAPE reported CONVERGED, correctly), as were feasibility, the
gap, rounds and bytes. It was still an implementation defect that reached a
reported column, so the campaign was invalidated rather than annotated.

## What changed

`weighted_grape.profile_signature` now includes the protocol phase, and
`test_pair_grape_phase_switch_is_not_a_cycle` pins it.

## Replacement

    config      experiments/configs/sp1_n3_confirmatory_v2.yaml
    campaign_id SP1_N3_DISTRIBUTED_BASELINES_v2
    output      scripts/results/sp1_levels/n3_v2

Rows from this run are never mixed with the replacement's.
