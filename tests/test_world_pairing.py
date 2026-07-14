from viu_mrob_tfm.sp0.audit_v1 import validation_worlds, world_set_hash


def test_checkpoint_audit_world_pairing_is_stable_and_order_sensitive() -> None:
    worlds = validation_worlds()
    assert world_set_hash(worlds) == world_set_hash(validation_worlds())
    assert world_set_hash(worlds) != world_set_hash(list(reversed(worlds)))
