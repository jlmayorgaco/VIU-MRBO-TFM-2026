from pathlib import Path

import yaml

from viu_mrob_tfm.sp9.metrics import (
    cbf_clearance_prediction,
    consensus_time_prediction,
    n_min_prediction,
    rho_loop_prediction,
)
from viu_mrob_tfm.sp9.runner import required_scene_files


def test_sp9_config_declares_minimum_gap_study_contract():
    config = yaml.safe_load(Path("configs/experiments/sp9/SP9_COPPELIA_gap_study.yaml").read_text())
    assert config["experiment"]["sp"] == "sp9"
    assert len(config["scenarios"]) >= 5
    assert len(config["methods"]) >= 3
    assert "predicted_vs_measured" in config["metrics"]
    assert "blocked_dir" in config["outputs"]


def test_sp9_closed_form_predictions_are_well_defined():
    assert rho_loop_prediction(4.0) == 2.0
    assert consensus_time_prediction(2.0, 0.5) == 1.0
    assert n_min_prediction(10.0, 0.8, 0.2, 4.0) == 3
    assert cbf_clearance_prediction(0.6) == 0.6


def test_sp9_scene_contract_points_to_yaml_and_lua_pairs():
    files = required_scene_files(Path("coppeliasim/scenes"), ["nominal", "robot_failure"])
    assert len(files) == 4
    assert files[0].name == "nominal_smith_qr.yaml"
    assert files[1].name == "nominal_smith_qr.lua"
