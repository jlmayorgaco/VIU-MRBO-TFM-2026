"""Smoke tests for initial domain entities."""

import numpy as np

from viu_mrob_tfm.domain import AGV, AGVState, FormationSpec, LoadState, TransportedLoad


def test_domain_objects_can_be_instantiated() -> None:
    agv = AGV(identifier="agv-1", state=AGVState(position=np.array([1.0, 0.0])))
    load = TransportedLoad()
    formation = FormationSpec(relative_offsets=np.array([[0.5, 0.0], [-0.5, 0.0]]))

    assert agv.identifier == "agv-1"
    assert isinstance(load.state, LoadState)
    assert formation.agent_count == 2
