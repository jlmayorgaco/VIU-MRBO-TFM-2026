import numpy as np

from viu_mrob_tfm.sp0.audit_v1 import rollout_with_scores, validation_worlds
from viu_mrob_tfm.sp0.data_driven import SP0GNNActorCritic
from viu_mrob_tfm.sp0.methods import assignment_valid


def test_raw_and_repair_are_retained_as_distinct_stages() -> None:
    world = validation_worlds()[0]
    model = SP0GNNActorCritic(hidden_dim=16, critic_global=True, gnn_layers=1)
    raw, repaired, _scores, _iterations = rollout_with_scores(model, world)
    assert raw.shape == repaired.shape
    assert assignment_valid(repaired, world.n_loads)
    assert np.shares_memory(raw, repaired) is False
