# Protocol Deviations

No confirmatory deviations recorded.

| date_utc | commit_before | commit_after | reason | affected_blocks | affected_hypotheses | impact_on_confirmatory_validity | resolution |
|---|---|---|---|---|---|---|---|
| 2026-07-11T11:37:53.179670+00:00 | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | B0 audit instrumentation added before freezing; no confirmatory seeds opened. | B0 | none | none | pending validation |

## CPU-only revision before confirmatory seed opening

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: pending_worktree
- `reason`: The available host has no CUDA device and the corrected v1.1 budget of 26,000,000 joint environment transitions was measured at a minimum of 114.6 hours before optimization. Batched PPO reached 208.9 transitions/s with one PPO epoch and rollout batches of 512. To satisfy the user-imposed three-hour total wall-clock limit, v1.2 pre-registers 1,120,000 training transitions: DD-1 uses 10,000 per configuration, DD-2 uses 50,000 per seed/configuration, and each of the three final seeds uses exactly 200,000.
- `affected_blocks`: data-driven tuning, final IPPO/MAPPO training, freeze, B4-B7.
- `affected_hypotheses`: comparisons involving the data-driven champion in P, C and R.
- `impact_on_confirmatory_validity`: Confirmatory seeds remain unopened, so there is no post-hoc test selection. Statistical comparisons remain valid for the declared resource-constrained CPU protocol, but results are not evidence for equivalence to the original 26M-step learning budget.
- `resolution`: Freeze and report v1.2 as `resource_constrained_cpu_budget`; retain all three final seeds and exact final checkpoints; do not compare learning convergence claims across v1.1 and v1.2 as if budgets were equal.

## Pre-freeze environment-lock implementation correction

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: pending_worktree
- `reason`: The first v1.2 freeze attempt stopped before artifact serialization because `environment_lock()` referenced `importlib.metadata` without importing it.
- `affected_blocks`: freeze only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; no frozen manifest or confirmatory seed-opening event was created.
- `resolution`: add the missing standard-library import, rerun tests and regenerate B0/dry-run so the implementation hash is current before freezing.

## Post-freeze orchestration correction without semantic changes

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- `commit_after`: frozen implementation unchanged
- `reason`: B5's thread-pool orchestration was limited by the Python GIL; a 96-row N=64 chunk required about 20 minutes and threatened the declared wall-clock envelope. The run was stopped after a valid 1056-row checkpoint and resumed with 12 isolated Python processes.
- `affected_blocks`: B5 execution orchestration; B6/B7 use the same process orchestration proactively.
- `affected_hypotheses`: none; task definitions, seeds, methods, worlds, numerical code, closures and metrics are unchanged.
- `impact_on_confirmatory_validity`: none. Existing rows were reused only after matching frozen `task_token`; pending rows were produced by the frozen `_execute_run_task`; final Parquet validation enforces the original primary keys, hashes and counts.
- `resolution`: record process count and preserve the original resume Parquet; report wall-clock as measured rather than as the preflight estimate.

## Precision diagnostic dtype correction

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: The precision-only extension decision aborted before producing extension rows because pandas preserved `final_success` as NumPy boolean and NumPy forbids boolean subtraction. Its first external retry also exposed that NumPy integer cell labels require conversion to Python scalars for JSON serialization.
- `affected_blocks`: precision diagnostics for B4, B5 and B7; no base run is affected.
- `affected_hypotheses`: none unless an extension is triggered; the decision rule and thresholds are unchanged.
- `impact_on_confirmatory_validity`: none. The external correction casts paired success indicators to float before subtraction, which is the declared success-rate difference, and uses the frozen bootstrap implementation unchanged.
- `resolution`: cast paired success to float, serialize cell labels through scalar `.item()`, rerun diagnostics from base Parquet, and extend only if the original width thresholds are exceeded; retain both failed tracebacks and this deviation record.

## Postprocessing nullable-value compatibility correction

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: Postprocessing aborted before analysis because `unit_id()` used Python boolean fallback on `pandas.NA`, whose truth value is intentionally undefined.
- `affected_blocks`: statistics, tables, figures, videos and final reporting only; no experimental run or metric computation is affected.
- `affected_hypotheses`: none; the shim only maps missing method/train-seed fields to the existing identifier semantics.
- `impact_on_confirmatory_validity`: none. The frozen run rows, planned contrasts, models, Holm procedure and rendering functions remain unchanged.
- `resolution`: apply an external audited compatibility shim that tests nullable scalars with `pandas.isna`, then delegate analysis and rendering to the frozen implementation.

## Post-hoc video encoder availability

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation unchanged
- `commit_after`: frozen implementation unchanged
- `reason`: All ten video render attempts reached the encoding stage but failed because no `ffmpeg` executable was available on `PATH`.
- `affected_blocks`: qualitative post-hoc videos only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; videos are generated from stored trajectories and are not statistical evidence.
- `resolution`: install `imageio-ffmpeg==0.6.0`, record the local encoder path/version, and rerun video rendering without reexecuting experimental worlds.

## Final acceptance accumulator initialization

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation hash `8031084d625dbaa804bca06ad02273bddb49f480c8da0eca00688b34074f08e3`
- `commit_after`: frozen implementation unchanged
- `reason`: The frozen final acceptance function references `block_integrity_ok` and `parquet_types_ok` before assigning initial values.
- `affected_blocks`: final acceptance manifest and report only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; each original acceptance predicate is preserved.
- `resolution`: run an external finalizer that initializes both conjunction accumulators to `true`, evaluates the unchanged block/schema/hash/artifact checks, and delegates report generation to the frozen writer.

## Seconds-only runtime schema validation

- `date_utc`: 2026-07-11
- `commit_before`: frozen implementation unchanged
- `commit_after`: frozen implementation unchanged
- `reason`: The generic acceptance schema still required legacy ambiguous fields `oracle_lookup_time` and `oracle_solve_time`, while the v1.1/v1.2 protocol explicitly migrated them to seconds-only `oracle_lookup_time_s` and `oracle_solve_time_s`.
- `affected_blocks`: schema validation for B2-B7 only.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; all six Parquet files contain the seconds-only fields with numeric types and retain the measured values.
- `resolution`: validate the frozen v1.2 seconds-only schema by replacing the two legacy names with their `_s` counterparts; do not synthesize duplicate legacy columns.
