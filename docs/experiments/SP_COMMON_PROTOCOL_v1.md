# SP common experimental protocol v1

Status: **DRAFT — implemented contracts, not yet adopted by every SP runner**.

## Purpose

This protocol is the cross-experiment control plane for SP0–SP8. It standardizes provenance, lifecycle, split isolation, stage semantics, cache safety, failures, statistics, artifacts, and fail-closed acceptance. It does not define any SP-specific scientific question, oracle, method, or metric.

The executable core is in `src/viu_mrob_tfm/experiment_common/`; the machine-readable policy is `configs/experiments/common/SP_COMMON_PROTOCOL_v1.yaml`.

## Lifecycle

The only valid forward path is:

`DRAFT → DRY_RUN_PASSED → FROZEN → TRAINING_COMPLETE → TEST_SEEDS_OPENED → TEST_COMPLETE → POSTPROCESS_COMPLETE → ACCEPTED → PROMOTED`.

Training-free experiments may go from `FROZEN` to `TEST_SEEDS_OPENED`. Every transition is append-only and records UTC timestamp, protocol, commit, seed-registry hash, entry point, previous state, next state, and whether test seeds are open. `TEST_COMPLETE`, `ACCEPTED`, or `PROMOTED` with `test_seeds_opened=false` is invalid.

## Immutable evaluation stages

- **RAW** is the direct method/policy output. No feasibility repair, decoder, closure, or oracle substitution is allowed.
- **REPAIR** is the declared minimal representation/feasibility repair.
- **QR** is the declared final integer closure/reassignment.

Each stage has its own assignment table, success flag, metrics, and runtime. A generic `success` may exist only in a stage-keyed long table; a wide table must use `raw_success`, `repair_success`, and `qr_success`. Learning claims use RAW evidence. Decoder and closure gains use `repair_delta_*` and `qr_delta_*`.

## Cache and resume

The common cache key includes protocol, trainer, policy, checkpoint hash, paired-world-set hash, evaluation config, decoder, repair, closure, and RAW/closed mode. Missing fields are rejected. Resume records use deterministic task tokens and validate primary keys before reuse; an incompatible partial result is archived, never silently merged.

## Splits and oracle isolation

Tuning, training, validation, and confirmatory seeds/worlds are mutually disjoint. Methods share paired worlds within a split. Confirmatory seeds remain sealed until freeze plus dry-run and budget gates pass. Deployed methods receive public world views only; oracle outputs live in a separate namespace and may be used only for references, regret calculation after execution, or explicitly declared imitation-training data.

## Versioned schemas

`experiment_common.schemas.v1` defines minimum fields for:

- `world_registry`
- `run_results`
- `method_manifest`
- `checkpoint_manifest`
- `trajectory_manifest`
- `failure_registry`
- `hypothesis_results`
- `claims_evidence`
- `artifact_manifest`

Parquet is canonical. CSV is an inspection/thesis export and cannot be the sole source for rebuild.

## Statistics

An empirically supported claim requires a finite effect and finite 95% interval on an interpretable scale. Exact `p=0` is forbidden; numerical bounds must be displayed. A preregistered fallback is required for separation, singularity, nonconvergence, or no variation. If both primary and fallback fail, the result is `not_estimable`, which is never favorable evidence. Multiplicity correction applies only to valid contrasts in the declared family.

## Rebuild and artifact provenance

Every figure has source data, every video has a trajectory and render manifest, and every claim links objective → hypothesis → runs → statistic → table/figure → limitation. `G_REBUILD_FROM_RAW` must delete only derived files in an isolated rebuild directory, regenerate without simulator/trainer calls, and compare counts, keys, and deterministic hashes where applicable.

## Current adoption status

The lifecycle, failure enum, stage enum, cache key, and v1 schema minimums are implemented and tested. SP0 historical artifacts are immutable and are mapped through adapters only. SP1 is not ready to adopt the protocol fully because it does not yet persist three immutable assignment stages, sealed confirmatory seeds, a complete rebuild command, or a run-time failure registry.
