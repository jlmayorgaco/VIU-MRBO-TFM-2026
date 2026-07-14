"""Fail-closed experiment lifecycle, stage, failure, and cache contracts.

This module is deliberately small.  It defines cross-experiment semantics but
does not import any SP-specific simulator, policy, decoder, or oracle.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Mapping


SCHEMA_VERSION = "sp-common-v1"


class LifecycleState(StrEnum):
    DRAFT = "DRAFT"
    DRY_RUN_PASSED = "DRY_RUN_PASSED"
    FROZEN = "FROZEN"
    TRAINING_COMPLETE = "TRAINING_COMPLETE"
    TEST_SEEDS_OPENED = "TEST_SEEDS_OPENED"
    TEST_COMPLETE = "TEST_COMPLETE"
    POSTPROCESS_COMPLETE = "POSTPROCESS_COMPLETE"
    ACCEPTED = "ACCEPTED"
    PROMOTED = "PROMOTED"


class Stage(StrEnum):
    RAW = "RAW"
    REPAIR = "REPAIR"
    QR = "QR"


class FailureCode(StrEnum):
    ORACLE_INFEASIBLE_WORLD = "oracle_infeasible_world"
    METHOD_NONCONVERGENCE = "method_nonconvergence"
    METHOD_TIMEOUT = "method_timeout"
    NUMERICAL_ERROR = "numerical_error"
    INVALID_ASSIGNMENT = "invalid_assignment"
    REPAIR_FAILURE = "repair_failure"
    CLOSURE_FAILURE = "closure_failure"
    SAFETY_VIOLATION = "safety_violation"
    EXTERNAL_PROCESS_ERROR = "external_process_error"
    POSTPROCESSING_ERROR = "postprocessing_error"
    UNKNOWN_FAILURE = "unknown_failure"


CACHE_KEY_FIELDS = (
    "protocol_version",
    "trainer_version",
    "policy_version",
    "checkpoint_sha256",
    "world_set_sha256",
    "evaluation_config_sha256",
    "decoder_version",
    "repair_version",
    "closure_version",
    "raw_or_closed_mode",
)


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    timestamp_utc: str
    protocol: str
    commit: str
    seed_registry_sha256: str
    entry_point: str
    previous_state: LifecycleState
    next_state: LifecycleState
    test_seeds_opened: bool


_ALLOWED_TRANSITIONS = {
    LifecycleState.DRAFT: {LifecycleState.DRY_RUN_PASSED},
    LifecycleState.DRY_RUN_PASSED: {LifecycleState.FROZEN},
    LifecycleState.FROZEN: {LifecycleState.TRAINING_COMPLETE, LifecycleState.TEST_SEEDS_OPENED},
    LifecycleState.TRAINING_COMPLETE: {LifecycleState.TEST_SEEDS_OPENED},
    LifecycleState.TEST_SEEDS_OPENED: {LifecycleState.TEST_COMPLETE},
    LifecycleState.TEST_COMPLETE: {LifecycleState.POSTPROCESS_COMPLETE},
    LifecycleState.POSTPROCESS_COMPLETE: {LifecycleState.ACCEPTED},
    LifecycleState.ACCEPTED: {LifecycleState.PROMOTED},
    LifecycleState.PROMOTED: set(),
}


def transition(
    previous: LifecycleState | str,
    following: LifecycleState | str,
    *,
    protocol: str,
    commit: str,
    seed_registry_sha256: str,
    entry_point: str,
    test_seeds_opened: bool,
    timestamp_utc: str | None = None,
) -> LifecycleEvent:
    """Validate and materialize one append-only lifecycle transition."""

    previous_state = LifecycleState(previous)
    next_state = LifecycleState(following)
    if next_state not in _ALLOWED_TRANSITIONS[previous_state]:
        raise ValueError(f"invalid lifecycle transition: {previous_state} -> {next_state}")
    if next_state in {
        LifecycleState.TEST_SEEDS_OPENED,
        LifecycleState.TEST_COMPLETE,
        LifecycleState.POSTPROCESS_COMPLETE,
        LifecycleState.ACCEPTED,
        LifecycleState.PROMOTED,
    } and not test_seeds_opened:
        raise ValueError(f"{next_state} requires test_seeds_opened=true")
    required = {
        "protocol": protocol,
        "commit": commit,
        "seed_registry_sha256": seed_registry_sha256,
        "entry_point": entry_point,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise ValueError(f"missing lifecycle evidence: {', '.join(missing)}")
    return LifecycleEvent(
        timestamp_utc=timestamp_utc or datetime.now(UTC).isoformat(),
        protocol=protocol,
        commit=commit,
        seed_registry_sha256=seed_registry_sha256,
        entry_point=entry_point,
        previous_state=previous_state,
        next_state=next_state,
        test_seeds_opened=bool(test_seeds_opened),
    )


def build_cache_key(values: Mapping[str, Any]) -> str:
    """Return a stable cache key only when every provenance field is present."""

    missing = [field for field in CACHE_KEY_FIELDS if field not in values or values[field] in {None, ""}]
    if missing:
        raise ValueError(f"unsafe cache key; missing: {', '.join(missing)}")
    payload = {field: values[field] for field in CACHE_KEY_FIELDS}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def lifecycle_event_dict(event: LifecycleEvent) -> dict[str, Any]:
    """Serialize an event without losing enum values."""

    result = asdict(event)
    result["previous_state"] = event.previous_state.value
    result["next_state"] = event.next_state.value
    return result
