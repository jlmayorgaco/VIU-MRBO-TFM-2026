from pathlib import Path

import numpy as np
import pytest

from viu_mrob_tfm.sp0.audit_v1 import load_checkpoint_model, rollout_with_scores, validation_worlds


def test_distinct_final_seeds_change_logits_on_paired_world() -> None:
    root = Path("results/sp0/SP0_PROTOCOL_v1_2_CPU/training/final_seeds")
    paths = [root / "DD_seed_1/checkpoint.pt", root / "DD_seed_2/checkpoint.pt"]
    if not all(path.exists() for path in paths):
        pytest.skip("historical SP0 checkpoints are not available")
    world = validation_worlds()[0]
    logits = []
    for path in paths:
        model, _payload, _requested, _effective = load_checkpoint_model(path)
        _raw, _repair, scores, _iterations = rollout_with_scores(model, world)
        logits.append(scores)
    assert np.max(np.abs(logits[0] - logits[1])) > 1e-12
