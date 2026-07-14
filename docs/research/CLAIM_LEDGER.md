# Claim ledger

The canonical ledger is `CLAIM_LEDGER.csv`. Status meanings:

- `demonstrated`: directly reproducible implementation/provenance/semantic evidence.
- `empirically_supported_reduced_order`: finite evidence within the declared simulation/model scope.
- `exploratory`: observed or implemented but not sealed confirmatory evidence.
- `unsupported`: evidence fails, is absent, or violates the claim contract.
- `future`: not yet implemented/evaluated.

## Immediate claim decisions

| Claim | Decision | Reason |
|---|---|---|
| Cardinality/capacity can yield wrench false positives | supported only in the implemented planar model | SP3 is reduced-order simulation, not physical validation |
| Wrench-Gated Pair-Aware Smith–QR is the contribution | candidate taxonomy only | component exists; integrated effect is not confirmatory |
| SP0 MAPPO learned assignment | unsupported | distinct logits collapse to identical RAW actions; repair supplies success |
| Historical reduced SP0 v1.2 has 15,436 base rows | demonstrated noncanonical provenance | row counts reproduce exactly, but the MARL budget is not v1.1-equivalent |
| SP0 v1.1 confirmatory closure | in progress | B0 and dry-run pass; 26M-step CPU training is running and test seeds remain sealed |
| Every SP0 promoted hypothesis is supported | unsupported | 15/19 hypothesis rows have non-finite effect/IC; 3 report p=0 |
| SP1 partial coalitions do not count | demonstrated | metric semantics and tests enforce it |
| SP1 has an exact coalition oracle | demonstrated when MILP returns optimal | previous subset/Hungarian implementation was replaced; timeouts must be reported |
| Existing SP1 results are confirmatory | unsupported | no new sealed holdout/freeze under common protocol |
| SP8 proves industrial deployment | unsupported | mesoscopic/scalability evidence only |

## Mathematical-claim rule

Every mathematical item must be labeled `known`, `adapted`, `derived`, or `original`. Algebraic agreement between a formula and its own implementation is a unit/consistency check, not independent validation. A theorem claim requires explicit assumptions, statement, proof status, and a traceable proposition identifier.

## Statistical-claim rule

No claim is supported when its effect or 95% interval is non-finite, its model is not estimable, or its inferential unit is invalid. Exact numerical p-values of zero are never printed. A rejection decision is necessary but not sufficient: effect scale, interval, assumptions, multiplicity family, and limitation must also be valid.

## Promotion rule

Only CSV rows with traceable code, configuration, raw data, processed data, statistic, artifact, thesis location, and limitation may enter abstract or conclusions. Missing fields force exploratory/unsupported status; wording cannot repair missing evidence.
