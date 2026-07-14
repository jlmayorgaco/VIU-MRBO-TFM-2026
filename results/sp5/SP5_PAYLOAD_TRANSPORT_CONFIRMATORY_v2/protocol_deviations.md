# SP5 v2 protocol deviations and semantic corrections

## Before confirmatory freeze

- The historical `SP5_MC_cooperative_transport_high_power` package was audited
  and retained as non-canonical context. Its simulator projected payload and
  robot poses after integration, so its near-perfect safety rates cannot be
  attributed to continuous closed-loop dynamics alone.
- The v2 pilot initially protected only the payload envelope. Pilot diagnostics
  showed that a docked robot could contact an obstacle while the payload stayed
  clear. Before freezing v2, the CBF geometry was expanded to a conservative
  compound payload--robot radius.
- Contact points were changed from angular spacing to equal perimeter spacing
  before freeze, eliminating overlapping initial robot disks for `N=12`.
- Controller gains were rescaled before freeze to match the 45 s horizon. The
  method list, five hypotheses, scenarios, test seeds and confirmatory sample
  size were not selected from confirmatory outcomes.

## After confirmatory execution

- The opening routine originally rewrote a status field in the frozen manifest.
  The immutable pre-opening bytes were reconstructed exactly from the recorded
  hash, and the code was corrected so future openings write only a separate
  event. `HASHES_v2.sha256` and the opening event both verify the restored
  frozen-manifest hash `a14413e4...`. This metadata repair did not alter the
  configuration, hypotheses, seeds, worlds, trajectories, tables or decisions.

No confirmatory method, parameter, margin or hypothesis was changed after the
seed-opening event.
