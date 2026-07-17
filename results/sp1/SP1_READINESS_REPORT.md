# SP1 readiness report

## Decision

**BLOCKED**

No confirmatory seeds were created or opened. No holdout, final training, or multi-hour campaign was executed.

## Gate status

| Gate | Result | Evidence | Consequence/action |
|---|---|---|---|
| Common schema | PARTIAL/FAIL | v1 minimum schemas exist and tests pass; SP1 legacy runner does not emit the required directory/table contract | adopt schemas in runner |
| Primary keys | NOT EXECUTED/FAIL | dry-run CSV has no common `run_id`/stage-key contract | add deterministic IDs and Parquet |
| World pairing | PASS for dry-run only | 28 rows share four public worlds across six methods plus oracle replay | repeat after final method selection |
| Split isolation | FAIL | public dry-run seeds are explicit, but no sealed validation/confirmatory registries exist | create/freeze registries before opening test |
| Exact oracle on small instances | PASS | binary MILP reaches `optimal`; brute-force comparison and idle/quorum tests pass | add timeout/gap fields to run outputs |
| Oracle leakage | PASS in current direct calls | deployed allocators receive ordinary `DecisionContext`; oracle output is used after execution for regret | enforce information contract automatically |
| Checkpoint load | NOT APPLICABLE to permitted SP1 dry-run | MAPPO was excluded | audit SP1 checkpoint separately if retained |
| Checkpoint sensitivity | FAIL/BLOCKING | SP0 audit shows changed logits but identical RAW actions versus random/uniform; SP1 MAPPO has not passed its own equivalent | MAPPO excluded from confirmatory method set |
| Cache isolation | PASS at common-contract unit level; FAIL for SP1 adoption | common key tests pass; SP1 runner has no checkpoint/world/evaluator cache contract | integrate common key |
| RAW/REPAIR/QR separation | FAIL/BLOCKING | current SP1 runner writes one final assignment only | persist three immutable assignment tables |
| Failure taxonomy | FAIL | common enum exists; SP1 run rows do not emit event-time `failure_code` | integrate failure registry |
| Statistical finite results | NOT EXECUTED/FAIL | dry-run intentionally has no hypotheses | preregister valid effects/fallbacks before freeze |
| Rebuild from RAW | FAIL/BLOCKING | no simulator-free common rebuild command exists | implement and verify |
| Video rebuild | FAIL | dry-run disabled videos; no universal trajectory/render manifest | add after raw trajectory contract |
| Budget preflight | PARTIAL/FAIL | legacy dry-run timed; required small/medium/large, training, full postprocess and video stages not all benchmarked | repeat after pipeline is complete |
| Final acceptance | FAIL | blocking gates remain | do not open confirmatory seeds |

## Changes made

- Added the SP common lifecycle, cache, stage, failure, and schema contracts.
- Replaced SP1’s subset/Hungarian pseudo-oracle with a binary MILP using robot–load and load-activation variables.
- Added explicit complete-service, demand, unmet-quorum, incomplete-coalition, overallocated, idle, regret, closure-time/message, timeout, and failure metrics.
- Added tests for integer quorum, partial coalition failure, idle robots, small-instance oracle optimality, checkpoint/cache isolation, and SP0 learning/decoder behavior.
- Created this draft protocol and a public-seed dry-run config.

## Tests and dry-run executed

- `python -m pytest -q tests/test_experiment_common_contracts.py tests/test_checkpoint_distinctness.py tests/test_policy_output_variation.py tests/test_raw_vs_closed_metrics.py tests/test_decoder_dependency.py tests/test_seed_isolation.py tests/test_world_pairing.py` → **10 passed**.
- Initial focused SP1 selection → **20 passed, 9 deselected**.
- Full SP1 + common schemas/contracts + six checkpoint/stage/isolation test files → **50 passed in 10.90 s** on the final targeted run.
- Repository-wide `python -m pytest -q` → **timed out after 304 s without emitting a final summary**; it is not reported as PASS or FAIL.
- `python scripts/run_sp1_experiment.py configs/experiments/sp1/SP1_PROTOCOL_v1_DRY_RUN.yaml` → **exit 0**, 28 rows, 2 public seeds, 2 scenario generators, 6 methods, no videos, no MAPPO, no hypotheses. Wall time: **6.692540 s**.
- Dry-run theory audit: **28 checks, 0 failures**. This is a semantic smoke check, not confirmatory evidence.

## Checkpoint sensitivity evidence

SP0 audit controls loaded 10 actors/checkpoints. Requested and effective hashes match; state fingerprints and logits differ. However, random, uniform, all seed-15001 snapshots, all three final seeds, and a perturbed final actor have the same RAW assignment on all six paired audit worlds. RAW success is 0.0 and repair success is 1.0 for every actor. `G_CHECKPOINT_SENSITIVITY` therefore fails under the strict RAW-action rule.

SP1 MAPPO has not undergone the same per-world RAW/decoder audit and is excluded from the permitted dry-run and any future confirmatory set until it passes.

## RAW / REPAIR / QR evidence

The SP0 auditor can retain RAW and the historical combined `POLICY_REPAIR`, demonstrating decoder dependence, but cannot recover an independent QR stage. The SP1 runner still exposes one final assignment. Consequently no SP1 claim can currently attribute performance among policy/dynamic, repair, and QR. This is a blocking design gap.

## Oracle

The SP1 reference is now `sp1_binary_coalition_milp_v1`, solved by SciPy/HiGHS. It enforces:

- binary robot–load assignment;
- at most one load per robot;
- binary load activation;
- integer quorum;
- payload capacity;
- zero assignment to inactive loads;
- idle via label 0;
- deterministic tiny tie-break;
- time limit and solver status/gap fields on the allocator.

The new enumerable-instance test compares the MILP objective with all `3^4=81` assignments. Expanded Hungarian remains a baseline only. The runner must still persist solver status and optimality gap per world before freeze.

## Proposed confirmatory methods

1. Binary coalition MILP oracle/reference.
2. Expanded Hungarian imperfect baseline.
3. Greedy nearest.
4. CBBA-like auction, explicitly labeled an adaptation.
5. Smith cardinality ablation.
6. Primal-dual local repair finalist, conditional on validation.
7. Tensor quorum-flow repair finalist, conditional on validation.
8. MAPPO recruitment only if its own sensitivity, split, cache, and RAW-decoder gates pass.

## Planned evaluations

The draft preregisters 160 base worlds × 8 methods including oracle = **1,280 evaluations**. A precision-only extension may increase this to 240 worlds × 8 = **1,920 evaluations**. These numbers are design targets, not executed rows.

## Timing preflight

Observed p95 method runtimes in the four-world public dry-run were:

| Method | p95 runtime (ms) |
|---|---:|
| Hungarian expanded | 0.080 |
| Greedy nearest | 0.100 |
| Smith cardinality | 0.153 |
| CBBA-like | 0.542 |
| Coalition MILP method row | 2.176 |
| Oracle replay row | 5.731 |
| Primal-dual local repair | 14.533 |

The full legacy dry-run took 6.69 s. Linear scaling by paired worlds gives roughly 268 s for 160 worlds, but this is **not an accepted campaign projection** because the future pipeline adds three stages, final methods, manifests, Parquet, statistics, figure source data, trajectories/videos, and possibly training. The required 3 h–3 h 15 min plan, 3 h 45 min hard cap, and 30 min reserve remain in the draft, but `G_BUDGET_PREFLIGHT` stays FAIL until every stage is benchmarked at a high percentile.

## CPU and RAM

Host observed: Intel Core Ultra 9 185H, 16 cores/22 logical processors, 31.54 GB RAM. The dry-run used the ordinary single Python process; per-stage peak RAM and CPU utilization were **not measured**, so no unsupported resource claim is made. A future preflight must record peak RSS, CPU time, wall time, and solver threads by stage.

## Future artifact contract

The frozen run must create `00_manifest/`, `01_raw/`, `02_tables/`, `03_figures/`, `04_videos/`, and `05_thesis_packet/` exactly as listed in `SP1_PROTOCOL_v1_DRAFT.yaml` and the common protocol. Every main result must link objective, hypothesis, statistic, table, figure, source file, limitation, and allowed wording.

## Pending risks

1. Current SP1 runner has no immutable three-stage assignments.
2. No sealed holdout or confirmatory seed-opening event exists.
3. Existing SP1 results are already observed and cannot become the new holdout.
4. MAPPO is decoder-dependent and has no SP1 sensitivity audit.
5. MILP status/gap is not yet persisted in run rows.
6. SP1 method metadata still overuses `proposed` for ablations.
7. No event-time failure registry exists.
8. No complete rebuild-from-raw command exists.
9. Figure source data and video trajectory manifests are incomplete.
10. Full time/RAM preflight has not been executed.

## Unequivocal decision

`BLOCKED`

Do not open SP1 confirmatory seeds or start final training/campaign execution.

## Development addendum — 2026-07-16

The new `SP1_QUORUM_v1` pipeline replaces the deleted legacy SP1 implementation for the delimited logical-quorum study. It stores Smith-RAW and QR-CLOSED outcomes as different method/stage rows, uses an exact binary MILP-Q oracle, generates 1,440 paired development worlds and 8,640 method rows, and passes 14/14 formal checks. The campaign is explicitly marked `confirmatory: false`; its observed seeds cannot be promoted to a sealed holdout.

This addendum resolves the narrow absence of a reproducible SP1 theory/development path, but it does not reverse the `BLOCKED` decision. The current QR implementation aggregates the preference matrix to isolate the logical closure effect; a neighbor-only implementation, a frozen confirmatory registry, event-level failure artifacts, and the full promotion gates remain pending.
