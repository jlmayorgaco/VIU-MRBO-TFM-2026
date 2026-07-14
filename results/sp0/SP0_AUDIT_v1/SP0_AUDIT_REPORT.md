# SP0 audit report v1

> Read-only audit of `results/sp0/SP0_PROTOCOL_v1_2_CPU`. The historical campaign was not rerun or modified.

## Decision

**BLOCKED**

SP0 remains a historical result package, but its learned-policy and several statistical claims are not promotable. SP1 confirmatory execution remains blocked.

## Gate matrix

| Gate | Result | Evidence | File | Consequence | Required action |
|---|---|---|---|---|---|
| G_CHECKPOINT_LOAD | PASS | 10 controls/checkpoints loaded; requested and effective hashes compared. | `checkpoint_fingerprints.csv` | Checkpoint provenance is readable. | Retain hash verification in every evaluator. |
| G_CHECKPOINT_SENSITIVITY | FAIL | Random/final and controlled-perturbation comparisons use fixed paired worlds. | `checkpoint_pairwise_sensitivity.csv` | MAPPO claims are blocked. | Require superiority to random/uniform before SP1 promotion. |
| G_CACHE_ISOLATION | PASS | Audit cache key includes protocol, trainer, policy, checkpoint, worlds, evaluation, decoder, repair, closure and stage mode. | `checkpoint_evaluations.csv` | Audit evaluations cannot alias across checkpoint hashes. | Adopt the common key in all SP runners. |
| G_RAW_REPAIR_QR_SEPARATION | FAIL | Historical policy executor exposes RAW plus one POLICY_REPAIR result, not immutable RAW/REPAIR/QR tables. | `raw_vs_closed_by_checkpoint.csv` | Decoder/closure contribution cannot be split into repair and QR retrospectively. | SP1 must persist three separate assignment tables before confirmatory execution. |
| G_SEED_STATE_CONSISTENCY | FAIL | training/status.json says confirmatory_seeds_opened=false while final manifest says confirmatory complete. | `audit_environment.json` | Historical lifecycle cannot be promoted as internally consistent. | Keep history immutable; use append-only SP_COMMON state events from now on. |
| G_STATISTICAL_FINITE_RESULTS | FAIL | 15 hypothesis rows have non-finite effect/CI; 3 use p=0. | `hypothesis_results_audited.csv` | Affected claims are downgraded to not supported. | Implement preregistered fallbacks and interpretable effect scales. |
| G_FAILURE_TAXONOMY | FAIL | Historical rows lack a versioned explicit failure_code; retrospective mapping is not causal proof. | `failure_breakdown.csv` | The aggregate 8,498 failure/timeout statement is not methodologically adequate. | Emit FailureCode at event time in SP1 and future SPs. |
| G_REBUILD_FROM_RAW | FAIL | No complete simulator-free rebuild entry point or deterministic source-data contract exists. | `audit_plan.md` | End-to-end reproducibility is unproven. | Implement and test experiment_common.rebuild before SP1 freeze. |

## Checkpoint sensitivity

The checkpoint files and state fingerprints are distinct. This alone does not establish learned behavioral improvement. The audit compares logits and RAW assignments on one fixed validation-world set and includes an untrained actor plus a controlled perturbation.

| Checkpoint | Seed | Steps | RAW success | REPAIR success | RAW regret | REPAIR regret |
|---|---:|---:|---:|---:|---:|---:|
| random_actor_seed15001 | 15001 | 0 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| uniform_logits_control | 0 | 0 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| seed15001_step050176 | 15001 | 50176 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| seed15001_step100352 | 15001 | 100352 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| seed15001_step150016 | 15001 | 150016 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| seed15001_step200000 | 15001 | 200000 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| final_seed15001 | 15001 | 200000 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| final_seed15002 | 15002 | 200000 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| final_seed15003 | 15003 | 200000 | 0.000 | 1.000 | 0.928724 | 0.000579834 |
| final_seed15001_perturbed | 15001 | 200000 | 0.000 | 1.000 | 0.928724 | 0.000579834 |

Interpretation: the historical validation aggregates (`raw_success=0`, closed `success=1`) are reproducible as a decoder-dominant pattern. Any MAPPO claim must be limited to a checkpoint-backed learned score generator whose executable success is attributable to deterministic repair; the current evidence does not show learned RAW coalition/allocation success.

## Statistical audit

- Hypotheses with non-finite effect or IC95: 15.
- Hypotheses reported with `p=0`: 3.
- Model rows with non-finite intervals: 35.
- Model rows reported with `p=0`: 31.
- The audited exports preserve original numbers but downgrade non-finite or non-estimable rows and render exact zero p-values as numerical bounds.

## Failure taxonomy

The audit read 15436 base evaluations. It reproduces the report's 8498 rows selected by `error_type OR timeout`, while the richer retrospective mapping classifies 9150 rows after also distinguishing continuous nonconvergence and invalid/failed closure. Because the historical source has no explicit versioned `failure_code`, this mapping is evidence for remediation, not a claim that the original causes are known.

## Lifecycle contradiction

`training/status.json` records `confirmatory_seeds_opened=false`, while `FINAL_RUN_MANIFEST.json` records complete confirmatory blocks and the protocol directory contains a seed-opening event. The historical state model therefore fails closed.

## Rebuild status

No repository entry point currently proves complete deterministic regeneration of tables, contrasts, all figure source data, videos, claims, and report from canonical RAW Parquet/trajectories without simulator or trainer calls. `G_REBUILD_FROM_RAW` is FAIL, not untested PASS.
