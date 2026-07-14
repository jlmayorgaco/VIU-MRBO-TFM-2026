# SP0_PROTOCOL_v1_1 Final Report

Overall status: dry_run_complete

## 1. Gates B0

| Gate | Status | Failed checks |
|---|---:|---|
| G1 | PASS | - |
| G2 | PASS | - |
| G3 | PASS | - |
| G4 | PASS | - |
| G5 | PASS | - |
| G6 | PASS | - |
| G7 | PASS | - |
| SMOKE | PASS | - |

## 2. Changes from v1

The active SP0 revision separates continuous convergence, timeout, closure success and final assignment success; uses method-specific residuals, isolates public/oracle views, records seconds-only runtimes, implements checkpoint-backed PPO with local GNN actors, and preserves audit trajectories.

## 3. IPPO/MAPPO training state

{
  "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\status.json": {
    "artifact_scope": "dry_run_only",
    "champion_id": "MAPPO-GNN",
    "confirmatory_seeds_opened": false,
    "device": "cpu",
    "final_seeds": [
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "46d18437d403eefcaa86af0630201947a709254ee28c649f9025eea24bebc442",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_1\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 3.041935470369127,
              "policy_loss": -0.0012492558194531767,
              "total_loss": 0.1113608255982399,
              "value_loss": 0.11565203281740348
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0063940018557736445,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 4,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_1\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 128,
        "timestamp_utc": "2026-07-11T21:26:55.283390+00:00",
        "train_seed": 15001,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 0.882871099980548
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "813374a63a7c0f3c4778764e321fc5403dc6de5a0e896cc24f367d61e6d3957b",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_2\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 3.215091149012248,
              "policy_loss": -0.0017798158857557402,
              "total_loss": 0.06417062878608704,
              "value_loss": 0.06916553792026307
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.003486861123410226,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 4,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_2\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 128,
        "timestamp_utc": "2026-07-11T21:26:56.134146+00:00",
        "train_seed": 15002,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 0.8327901000156999
      },
      {
        "algorithm": "MAPPO-GNN",
        "checkpoint_hash": "b99a229924eaa603ebc8f5a41ec1d577aca9bfe477e317cc38bd44395719ed06",
        "checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_3\\checkpoint.pt",
        "device": "cpu",
        "discount_factor": 0.95,
        "entropy_coefficient": 0.001,
        "episode_horizon": 4,
        "gnn_layers": 3,
        "gpu_hours": 0.0,
        "hidden_dim": 64,
        "history": [
          {
            "loss": {
              "entropy": 3.046911983778983,
              "policy_loss": -0.002106271458394593,
              "total_loss": 0.08993516862392426,
              "value_loss": 0.09508834248690895
            },
            "optimizer_updates": 1,
            "training_steps": 64,
            "validation": {
              "CVaR95_NR": 0.0034952203386420856,
              "NR_minus_Greedy": -0.0007083554756718499,
              "algorithm": "MAPPO-GNN",
              "greedy_mean_NR": 0.0014670780605179064,
              "inference_time_s": 0.0033936166652926694,
              "mean_NR": 0.0007587225848460564,
              "mean_closure_NR_delta": -0.9202233437445989,
              "mean_closure_vs_raw_decode_NR_delta": -0.9202233437445989,
              "mean_raw_decode_NR": 0.9209820663294446,
              "n_validation_worlds": 54.0,
              "raw_success": 0.0,
              "success": 1.0
            }
          }
        ],
        "learning_rate": 0.001,
        "optimizer_updates": 1,
        "policy_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "ppo_clip": 0.2,
        "ppo_epochs": 4,
        "progress_checkpoint_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\dry_run\\final_seeds\\DD_seed_3\\progress.pt",
        "resume_reused": false,
        "resumed_from_step": 0,
        "rollout_environment_steps": 128,
        "timestamp_utc": "2026-07-11T21:26:56.877839+00:00",
        "train_seed": 15003,
        "trainer_version": "sp0_gnn_ppo_v1_2_cpu_batched",
        "training_converged": false,
        "training_step_unit": "joint_environment_transition",
        "training_steps": 64,
        "training_wall_s": 0.7254844999406487
      }
    ],
    "status": "dry_run_complete",
    "timestamp_utc": "2026-07-11T21:26:56.888715+00:00"
  },
  "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\status.json": {
    "artifact_scope": "confirmatory_training_not_started",
    "budget_reduced": false,
    "confirmatory_seeds_opened": false,
    "estimated_training_wall_hours_lower_bound": 45.33325073327998,
    "failed_seed_replaced": false,
    "hardware_benchmark_path": "results\\sp0\\SP0_PROTOCOL_v1_1\\training\\hardware_benchmark.json",
    "maximum_estimated_training_wall_hours": 24.0,
    "reason": "CPU preflight estimates at least 45.3 hours for the frozen 26000000 environment-step budget; the configured operational limit is 24.0 hours.",
    "required_action": "resume unchanged full budget on suitable CUDA hardware, a durable worker, or pass --allow-long-cpu-training explicitly",
    "status": "HARDWARE_BLOCKED",
    "timestamp_utc": "2026-07-11T21:25:48.819029+00:00",
    "training_step_unit": "joint_environment_transition"
  }
}

## 4. Three final seeds

No contract-valid confirmatory champion exists; reduced dry-run checkpoints are not substitutes.

## 5. Planned vs executed counts

| Block | Planned | Executed |
|---|---:|---:|
| B0 | 300 | 300 |
| B2 | 2400 | 0 |
| B3 | 1536 | 0 |
| B4 | 5760 | 0 |
| B5 | 4000 | 0 |
| B6 | 960 | 0 |
| B7 | 480 | 0 |
| TOTAL | 15436 | 300 |

## 6. Duration and hardware

- commit: 72418e13f1bed1a6d37698e59bf0d07400dc8b10
- generated_at_utc: 2026-07-11T21:27:09.363252+00:00
- hardware_id: 6922fcded7e90bd6

{
  "MKL_NUM_THREADS": "1",
  "OMP_NUM_THREADS": "1",
  "OPENBLAS_NUM_THREADS": "1",
  "batch_size": 1,
  "cpu_model": "Intel64 Family 6 Model 170 Stepping 4, GenuineIntel",
  "gpu_memory_bytes": null,
  "gpu_model": "not_detected",
  "jax_version": "not_installed",
  "num_workers": 1,
  "python_version": "3.13.9",
  "ram_bytes": 33863831552,
  "torch_version": "2.11.0+cpu"
}

## 7. Results by regime

Confirmatory result tables do not exist yet.

## 8. Continuous dynamics vs closures

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 9. Dynamic-fitness interaction

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 10. Method-connectivity interaction

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 11. Robustness

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 12. Generalization

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 13. Pareto fronts

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 14. Observed PoA/PoS

See the versioned Parquet tables and figures; no claim is emitted when its artifact is absent.

## 15. Hypotheses with Holm

Holm-adjusted confirmatory analysis has not been generated.

## 16. Claims

- Theoretically guaranteed: oracle optimality, declared simplex contracts, finite QR termination and declared QRA scope.
- Empirically supported: only frozen confirmatory hypotheses at final sample size with Holm correction.
- Exploratory only: B0, smoke, B2 dynamic-fitness screening and nonconfirmatory closure ablations.
- Not supported: universal stability, universal graph convergence, theoretical PoA from Monte Carlo, or physical transfer.

## 17. Failure cases

Preserved failure/timeout rows found: 0.

## 18. Deviations

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

## 19. Reproducibility

Frozen hashes, seed registry, environment lock, world/checkpoint/trajectory hashes are authoritative. Dry-run artifacts are exploratory and cannot open test seeds.

## 20. Final verdict

SP0 is not closed. Winners cannot be declared until contract-valid training, freeze, B1-B7, precision checks and postprocessing complete.
