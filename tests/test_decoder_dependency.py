from pathlib import Path

import numpy as np
import pytest

from viu_mrob_tfm.sp0.audit_v1 import load_checkpoint_model, rollout_with_scores, validation_worlds


def test_historical_final_policy_exposes_decoder_delta() -> None:
    path = Path("results/sp0/SP0_PROTOCOL_v1_2_CPU/training/final_seeds/DD_seed_1/checkpoint.pt")
    if not path.exists():
        pytest.skip("historical SP0 checkpoint is not available")
    model, _payload, _requested, _effective = load_checkpoint_model(path)
    deltas = []
    for world in validation_worlds()[:3]:
        raw, repaired, _scores, _iterations = rollout_with_scores(model, world)
        deltas.append(float(np.mean(raw != repaired)))
    assert max(deltas) > 0.0
