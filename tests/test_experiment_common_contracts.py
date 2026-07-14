from __future__ import annotations

import pytest

from viu_mrob_tfm.experiment_common import LifecycleState, build_cache_key, transition


def _cache_values(checkpoint: str = "checkpoint-a") -> dict[str, str]:
    return {
        "protocol_version": "SP0-v1.2",
        "trainer_version": "trainer-v1",
        "policy_version": "policy-v1",
        "checkpoint_sha256": checkpoint,
        "world_set_sha256": "worlds-a",
        "evaluation_config_sha256": "eval-a",
        "decoder_version": "decoder-v1",
        "repair_version": "repair-v1",
        "closure_version": "closure-v1",
        "raw_or_closed_mode": "RAW",
    }


def test_cache_isolated_by_checkpoint() -> None:
    assert build_cache_key(_cache_values("a")) != build_cache_key(_cache_values("b"))


def test_cache_key_rejects_missing_provenance() -> None:
    values = _cache_values()
    del values["checkpoint_sha256"]
    with pytest.raises(ValueError, match="checkpoint_sha256"):
        build_cache_key(values)


def test_lifecycle_cannot_complete_test_before_opening_seeds() -> None:
    with pytest.raises(ValueError, match="test_seeds_opened"):
        transition(
            LifecycleState.TEST_SEEDS_OPENED,
            LifecycleState.TEST_COMPLETE,
            protocol="SPX-v1",
            commit="abc",
            seed_registry_sha256="def",
            entry_point="pytest",
            test_seeds_opened=False,
        )


def test_lifecycle_rejects_skipped_states() -> None:
    with pytest.raises(ValueError, match="invalid lifecycle transition"):
        transition(
            LifecycleState.DRAFT,
            LifecycleState.ACCEPTED,
            protocol="SPX-v1",
            commit="abc",
            seed_registry_sha256="def",
            entry_point="pytest",
            test_seeds_opened=True,
        )
