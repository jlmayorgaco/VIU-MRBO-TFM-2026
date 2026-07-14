from viu_mrob_tfm.experiment_common import build_cache_key


def _values(checkpoint: str, evaluation: str) -> dict[str, str]:
    return {
        "protocol_version": "SP0-v1.2",
        "trainer_version": "trainer-v1",
        "policy_version": "policy-v1",
        "checkpoint_sha256": checkpoint,
        "world_set_sha256": "paired-validation-worlds",
        "evaluation_config_sha256": evaluation,
        "decoder_version": "decoder-v1",
        "repair_version": "repair-v1",
        "closure_version": "closure-v1",
        "raw_or_closed_mode": "RAW",
    }


def test_training_seed_checkpoint_and_evaluation_split_cannot_alias() -> None:
    assert build_cache_key(_values("seed-15001", "validation")) != build_cache_key(
        _values("seed-15002", "validation")
    )
    assert build_cache_key(_values("seed-15001", "validation")) != build_cache_key(
        _values("seed-15001", "test")
    )
