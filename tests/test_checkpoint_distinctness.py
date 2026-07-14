from pathlib import Path

import pytest

from viu_mrob_tfm.sp0.audit_v1 import load_checkpoint_model, state_fingerprint


ROOT = Path("results/sp0/SP0_PROTOCOL_v1_2_CPU/training/final_seeds")


def test_final_checkpoint_files_and_model_states_are_distinct() -> None:
    paths = [ROOT / f"DD_seed_{index}" / "checkpoint.pt" for index in (1, 2, 3)]
    if not all(path.exists() for path in paths):
        pytest.skip("historical SP0 checkpoints are not available")
    file_hashes = []
    state_hashes = []
    for path in paths:
        model, _payload, requested, effective = load_checkpoint_model(path)
        assert requested == effective
        file_hashes.append(requested)
        state_hashes.append(state_fingerprint(model.state_dict()))
    assert len(set(file_hashes)) == 3
    assert len(set(state_hashes)) == 3
