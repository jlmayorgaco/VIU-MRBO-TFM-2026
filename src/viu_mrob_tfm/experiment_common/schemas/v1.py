"""Minimum v1 column contracts; SP-specific schemas may add fields."""

from __future__ import annotations

from collections.abc import Iterable


SCHEMAS_V1: dict[str, tuple[str, ...]] = {
    "world_registry": ("world_id", "world_sha256", "split", "seed", "protocol_version"),
    "run_results": (
        "run_id",
        "world_id",
        "method_id",
        "stage",
        "success",
        "runtime_s",
        "failure_code",
        "task_token",
    ),
    "method_manifest": (
        "method_id",
        "method_family",
        "centralized_or_distributed",
        "information_scope",
        "oracle_access",
        "training_required",
        "decoder_version",
        "repair_version",
        "closure_version",
    ),
    "checkpoint_manifest": (
        "checkpoint_id",
        "requested_path",
        "requested_sha256",
        "effective_sha256",
        "model_state_fingerprint",
        "train_seed",
        "training_steps",
    ),
    "trajectory_manifest": ("trajectory_id", "run_id", "relative_path", "sha256", "renderer_version"),
    "failure_registry": ("run_id", "failure_code", "stage", "message"),
    "hypothesis_results": (
        "hypothesis_id",
        "effect_scale",
        "effect_estimate",
        "ci95_low",
        "ci95_high",
        "p_value_reported",
        "decision",
    ),
    "claims_evidence": ("claim_id", "objective_id", "hypothesis_id", "artifact_id", "status", "limitation"),
    "artifact_manifest": ("artifact_id", "relative_path", "artifact_type", "sha256", "source_run_ids"),
}


def validate_columns(schema_name: str, columns: Iterable[str]) -> list[str]:
    """Return missing required columns; unknown schema names fail explicitly."""

    if schema_name not in SCHEMAS_V1:
        raise KeyError(f"unknown common schema: {schema_name}")
    available = set(columns)
    return [column for column in SCHEMAS_V1[schema_name] if column not in available]
