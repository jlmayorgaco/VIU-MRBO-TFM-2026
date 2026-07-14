# Integrity addendum: freeze/seed-opening metadata

Date of independent audit: 2026-07-14.

## Finding

The frozen file `protocol/hypotheses.yaml` contains the stale field
`frozen_before_confirmatory_seed_opening: false`. This field conflicts with the
separate immutable freeze and seed-opening records. The historical YAML is not
rewritten because its SHA-256 is itself bound into the frozen manifest.

## Authoritative event chain

1. `protocol/frozen_manifest.json` records `frozen: true`, status
   `frozen_ready_for_execution`, and `confirmatory_seeds_opened: false` at
   `2026-07-12T19:04:06Z`.
2. Its SHA-256 is
   `9e335554de67ea982186bd2cebb92a2aabeabbe86f840f5198450356381c6583`.
3. `audit/seed_opening.json` records `after_freeze: true` at
   `2026-07-12T19:04:21Z` and binds exactly that frozen-manifest hash.
4. The seed-opening event therefore follows the freeze record by 15 seconds.
5. The frozen manifest also binds the unchanged hypotheses file with SHA-256
   `d6148914b021883d53a8cc085fd6b600dabe65dc7f392d30b570fd163e15907c`.

## Resolution

The freeze-before-opening claim is supported by the hash-bound event chain. The
boolean in `hypotheses.yaml` is classified as a protocol-metadata defect, not as
evidence that confirmatory seeds were exposed early. Future protocol generators
must derive this field from the seed-opening ledger or omit it from the
pre-freeze hypotheses file.

No frozen protocol, seed, run, statistic, or result file was modified as part of
this addendum.
