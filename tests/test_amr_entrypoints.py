"""AMR terminology and CLI entry-point contracts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from viu_mrob_tfm.cli.run_experiment import parse_args
from viu_mrob_tfm.config.schema import ExperimentConfig, SimulationConfig
from viu_mrob_tfm.domain import AGV, AGVState, AMR, AMRState, LoadState, SystemState


def test_amr_is_canonical_domain_entity_with_legacy_aliases() -> None:
    assert AGV is AMR
    assert AGVState is AMRState

    state = AMRState(position=np.array([1.0, 2.0]))
    robot = AMR(identifier="amr-1", state=state)
    system = SystemState(amr_states=[state], load_state=LoadState())

    assert robot.identifier == "amr-1"
    assert system.agent_count == 1
    assert system.agv_states is system.amr_states


def test_simulation_config_accepts_amr_and_legacy_count() -> None:
    config = SimulationConfig(amr_count=4)
    assert config.amr_count == 4
    assert config.agv_count == 4
    assert SimulationConfig(agv_count=5).amr_count == 5

    loaded = ExperimentConfig.from_dict(
        {
            "name": "legacy-count",
            "description": "legacy count compatibility",
            "simulation": {"agv_count": 2},
            "graph": {"adjacency": [[0.0, 1.0], [1.0, 0.0]]},
        }
    )
    assert loaded.simulation.amr_count == 2

    with pytest.raises(ValueError, match="disagree"):
        ExperimentConfig.from_dict(
            {
                "name": "bad-count",
                "description": "conflicting count compatibility",
                "simulation": {"amr_count": 2, "agv_count": 3},
                "graph": {"adjacency": [[0.0, 1.0], [1.0, 0.0]]},
            }
        )


def test_run_experiment_cli_accepts_positional_and_option_config() -> None:
    config = Path("experiments/exp-001-baseline-nominal/config.yaml")

    positional = parse_args([str(config)])
    option = parse_args(["--config", str(config)])

    assert positional.config == config
    assert option.config == config
