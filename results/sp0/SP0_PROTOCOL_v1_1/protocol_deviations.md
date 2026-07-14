# Protocol Deviations SP0 v1.1

| date_utc | commit_before | commit_after | reason | affected_blocks | affected_hypotheses | impact_on_confirmatory_validity | resolution |
|---|---|---|---|---|---|---|---|
| 2026-07-11T00:00:00Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | v1 was frozen before complete B1-B7/DD executor and before corrected timeout/potential semantics; v1.1 created before confirmatory seeds are opened. | B0,B1-B7,training | all SP0 v1.1 hypotheses | none; confirmatory seeds remain unopened | archive v1, repair B0 semantics, refreeze v1.1 only after gates and dry-run |
| 2026-07-11T02:19:03Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | Implemented checkpoint-backed IPPO/MAPPO-GNN executor/training skeleton; full DD tuning/final training blocked because this session has torch CPU only and no CUDA GPU. | training,freeze,B4-B7 | DD champion selection and confirmatory DD units | Keeps confirmatory seeds closed; no post-hoc selection. | Status HARDWARE_BLOCKED recorded; rerun --train-data-driven on suitable GPU hardware before freeze. |
| 2026-07-11T03:10:00Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | Replaced the one-step policy-gradient draft with clipped PPO, learned graph message passing, local IPPO critic, MAPPO centralized training critic, and actor-only decentralized inference. CPU execution now preserves the full budget instead of being rejected solely for lacking CUDA. | training,freeze,B4-B7 | DD champion and comparisons | none; only reduced dry-run training has run and test seeds remain closed | require real DD-1/DD-2 and three exact 5M final checkpoints before freeze |
| 2026-07-11T03:10:00Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | Corrected RAW semantics, method-specific equilibrium residuals, epsilon-auction identity, QRA exhaustive/fallback labels, public/oracle world views, immutable hashed cache, and one-oracle-generation-per-world execution. | B0,B1-B7 | P,C,R and exploratory G | strengthens validity before test; no confirmatory data inspected | rerun B0 and integral dry-run, then include implementation tree hash in freeze |
| 2026-07-11T03:10:00Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | The fixed 15436-run design contains no confirmatory dynamic-fitness or QR-neighborhood factorial outside exploratory B2. Family G hypotheses were therefore explicitly downgraded to preregistered exploratory status before freeze. | B2,B3,statistics | G1-G6 | prevents invalid confirmatory claims; P,C,R remain confirmatory | label B2 and G-family outputs exploratory in all tables and figures |
| 2026-07-11T03:10:00Z | 72418e13f1bed1a6d37698e59bf0d07400dc8b10 | pending | Added 96 validation-only model-selection evaluations to choose B5 top-5 local population units and B7 top-3 distributed model-based units without using B5/B7 outcomes. They are explicitly excluded from the base 15436 count. | B3,B5,B7 | C,R2 | prevents test-driven finalist selection; base count unchanged | hash selected units before opening test seeds and report auxiliary count separately |

## 2026-07-11 - Correct environment-step accounting before freeze

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: The PPO trainer had counted one joint MARL transition as `N` agent-steps while the preregistered budget is stated in environment steps. v1.1 now defines one joint action/state transition as one environment step, records `training_step_unit=joint_environment_transition`, and archives incompatible pre-freeze debug checkpoints.
- `affected_blocks`: B0 dry-run and data-driven training only; no confirmatory block or test seed was opened.
- `affected_hypotheses`: none; correction precedes freeze.
- `impact_on_confirmatory_validity`: positive; prevents an understated MARL training budget and preserves equal IPPO/MAPPO accounting.
- `resolution`: regenerate B0/dry-run, benchmark the corrected unit, and freeze only after hardware readiness or an explicit HARDWARE_BLOCKED status.
## 2026-07-11 - Automated CPU hardware preflight before official MARL training

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: A measured 10,000-step benchmark of the corrected joint-environment-step trainer achieved 63.05 steps/s on the available CPU-only host, implying a lower bound of 114.6 hours for the preregistered 26M training steps. The runner now reuses a versioned benchmark, blocks before DD-1 when the estimate exceeds the pre-freeze operational limit of 24 hours, and exposes `--allow-long-cpu-training` for an explicitly provisioned durable CPU worker.
- `affected_blocks`: data-driven preflight only; B2-B7 and confirmatory seeds remain untouched.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; scientific budgets and seed identities remain unchanged, and no reduced run can satisfy readiness.
- `resolution`: run the unchanged command on CUDA or explicitly authorize a durable CPU job; freeze remains impossible until all official checkpoints pass readiness.
## 2026-07-11 - Parallel and row-resumable campaign execution before freeze

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: `--workers` previously only appeared in hardware metadata and completed blocks were reusable only after their final Parquet existed. B2, each B3 round, validation selection, B4-B7 and precision extensions now execute independent rows with deterministic thread-pool ordering and persist typed resume checkpoints by cryptographic `task_token`.
- `affected_blocks`: B2-B7 and precision extensions.
- `affected_hypotheses`: none.
- `impact_on_confirmatory_validity`: none; task identity includes frozen config, git hash, world hash, method specification and factors. Failed/timeout rows are checkpointed and never omitted.
- `resolution`: retain canonical run counts and validate final primary keys; resume checkpoints live outside files consumed by confirmatory analysis.

## 2026-07-11 - Sealed confirmatory seed API and immutable opening event

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: The frozen registry contains all disjoint seed groups, but preconfirmatory code should not receive test, extension or generalization values. The loader now exposes a restricted view until an immutable opening event records the frozen registry, B3 champion, DD champion and model-selection hashes.
- `affected_blocks`: B1-B7 and precision extensions.
- `affected_hypotheses`: all confirmatory P/C/R families.
- `impact_on_confirmatory_validity`: strengthens the pre-test selection barrier; no confirmatory seed has been opened in the current campaign.
- `resolution`: final acceptance requires a valid event SHA and opening timestamp after freeze.
## 2026-07-11 - Primary useful-solution metrics and confirmatory model completion

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: `time_to_epsilon_solution`, messages-to-epsilon and bytes-to-epsilon had been declared but not computed. They are now derived from the first trajectory state satisfying valid maximum cardinality and NR<=0.05, with explicit censor duration/event fields. Statistical postprocessing now records mixed logistic, robust/mixed regret, Cox, negative-binomial communication, connectivity, stress, support and generalization models, plus H0-level Holm decisions.
- `affected_blocks`: B0 schema, B2-B7 metrics, statistics, figures and final report.
- `affected_hypotheses`: P1-P6, C1-C3, R1-R4; G remains exploratory.
- `impact_on_confirmatory_validity`: positive and pre-freeze; prevents substituting convergence time or total communication for the registered primary outcomes.
- `resolution`: regenerate B0/dry-run and require these fields/models in final acceptance.
## 2026-07-11 - Explicit closure-effect baselines and complete rankings

- `date_utc`: 2026-07-11
- `commit_before`: 72418e13f1be
- `commit_after`: pending_worktree
- `reason`: The legacy `closure_regret_delta` was normalized but ambiguously referenced the independently decoded pre-closure assignment rather than the continuous state. v1.1 now records `closure_vs_preclosure_regret_delta` and `final_vs_continuous_regret_delta` separately, retains the old field only as a documented alias, and adds the preregistered after-ARG and Pareto-by-regime rankings.
- `affected_blocks`: B0 schema, B2-B7 metrics, statistics, tables and figures.
- `affected_hypotheses`: P2 and exploratory G4-G6.
- `impact_on_confirmatory_validity`: positive and pre-freeze; prevents attributing QR2/QRA improvements to HYB continuous convergence.
- `resolution`: regenerate B0 and the integral dry-run with the updated schema before any freeze. MARL validation metadata additionally records raw-decoding NR and closure-vs-raw NR; legacy debug metadata is migrated algebraically without changing checkpoints.
## 2026-07-11 - Seconds-only runtime schema and acceptance hardening before freeze

- date_utc: 2026-07-11
- commit_before: 72418e13f1be
- commit_after: pending_worktree
- reason: Canonical SP0 rows still exported ambiguous runtime aliases, and the final acceptance function referenced two uninitialized integrity accumulators.
- affected_blocks: B0-B7, statistics, figures, final acceptance.
- affected_hypotheses: P2-P4, C1-C3, R1-R2.
- impact_on_confirmatory_validity: positive and pre-freeze; no confirmatory seed was exposed.
- resolution: export only seconds-suffixed runtime fields, label figures in seconds, initialize and evaluate block/parquet integrity gates, rerun B0 and the integral dry-run.

## 2026-07-11 - Canonical 26M MARL budget made non-bypassable

- date_utc: 2026-07-11
- commit_before: 72418e13f1be
- commit_after: pending_worktree
- reason: The preserved SP0_PROTOCOL_v1_2_CPU evidence used 10k/50k/200k training budgets and therefore cannot satisfy the requested SP0 v1.1 250k/1M/5M contract.
- affected_blocks: data-driven tuning, final training, freeze, B4-B7.
- affected_hypotheses: every comparison containing DD units.
- impact_on_confirmatory_validity: prevents a reduced resource experiment from being labeled as SP0 v1.1 closure.
- resolution: code now rejects any official budget other than 26,000,000 joint environment transitions; v1.2 artifacts are retained with a noncanonical notice.

## 2026-07-11 - CPU-only full-budget execution authorized

- date_utc: 2026-07-11
- commit_before: 72418e13f1be
- commit_after: pending_worktree
- reason: The investigator confirmed that no GPU is available and instructed that no remaining work be deferred to GPU hardware.
- affected_blocks: DD-1, DD-2, three final 5M seeds, freeze, B1-B7 and postprocessing.
- affected_hypotheses: all SP0 v1.1 hypotheses.
- impact_on_confirmatory_validity: none; step budgets, seeds and checkpoint rule are unchanged.
- resolution: official CPU run started with --device cpu --allow-long-cpu-training --resume; watchdog preserves logs and restarts the same resumable command up to five times. Confirmatory seeds remain sealed until training, dry-run and freeze gates pass.
## 2026-07-12 - Full-budget CPU execution stopped before freeze

- date_utc: 2026-07-12
- commit_before: 72418e13f1be
- commit_after: pending_worktree
- reason: The 10,000-transition hardware benchmark estimated a 45.33-hour lower bound for the 26M training budget, excluding validation and B1-B7. After six IPPO DD-1 configurations completed, the investigator authorized a resource-proportional protocol that prioritizes B0-B7 design, pairing, closure attribution, failure preservation and confirmatory statistics over additional PPO compute.
- affected_blocks: data-driven DD-2/final training, freeze and downstream execution.
- affected_hypotheses: comparisons containing data-driven units; no hypothesis result or confirmatory world was inspected.
- impact_on_confirmatory_validity: none for future test inference because the protocol was not frozen and confirmatory seeds remained sealed. Completed v1.1 training artifacts remain immutable preconfirmatory engineering evidence and cannot be represented as a completed v1.1 campaign.
- resolution: stop the watchdog and runner, preserve every checkpoint and timeout, supersede v1.1 for CPU execution with an explicitly resource-constrained protocol, and freeze any future evaluation protocol before opening fresh disjoint confirmatory seeds.
