"""Smoke tests for initial domain entities."""

import numpy as np

from viu_mrob_tfm.domain import AMR, AMRState, FormationSpec, LoadState, TransportedLoad


def test_domain_objects_can_be_instantiated() -> None:
    amr = AMR(identifier="amr-1", state=AMRState(position=np.array([1.0, 0.0])))
    load = TransportedLoad()
    formation = FormationSpec(relative_offsets=np.array([[0.5, 0.0], [-0.5, 0.0]]))

    assert amr.identifier == "amr-1"
    assert isinstance(load.state, LoadState)
    assert formation.agent_count == 2
