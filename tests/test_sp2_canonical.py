from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from viu_mrob_tfm.sp2_canonical.caging import verify_grid_caging
from viu_mrob_tfm.sp2_canonical.communication import canonical_message_bytes
from viu_mrob_tfm.sp2_canonical.experiment import run_sp2_canonical_config
from viu_mrob_tfm.sp2_canonical.kinematics import (
    DifferentialDrive,
    anchor_kinematics,
    certify_formation_twist,
    independent_speed_only_feasible,
)
from viu_mrob_tfm.sp2_canonical.mechanics import (
    aggregate_force_only_feasible,
    certify_planar_wrench,
    grasp_matrix_2d,
)


def test_anchor_velocity_is_rigid_body_velocity() -> None:
    velocity, acceleration = anchor_kinematics(
        np.asarray([0.4, -0.2, 0.5]),
        np.zeros(3),
        np.asarray([2.0, 0.0]),
    )
    assert np.allclose(velocity, np.asarray([0.4, 0.8]))
    assert np.allclose(acceleration, np.asarray([-0.5, 0.0]))


def test_joint_certificate_detects_a_naive_false_feasible() -> None:
    drives = [
        DifferentialDrive(f"r{index}", 0.06, 0.32, limit)
        for index, limit in enumerate([12.0, 10.0, 8.0, 6.0], start=1)
    ]
    offsets = np.asarray([[0.0, -0.5], [0.5, 0.0], [0.0, 0.5], [-0.5, 0.0]])
    candidates = [np.asarray([0.18, 0.0, omega]) for omega in np.linspace(0.1, 1.2, 100)]
    false_feasible = [
        twist
        for twist in candidates
        if independent_speed_only_feasible(drives, offsets, twist)
        and not certify_formation_twist(drives, offsets, twist).feasible
    ]
    assert false_feasible


def test_grasp_matrix_and_wrench_identity() -> None:
    offsets = np.asarray([[0.5, 0.0], [-0.5, 0.0]])
    grasp = grasp_matrix_2d(offsets)
    forces = np.asarray([[0.0, 2.0], [0.0, -2.0]])
    assert np.allclose(grasp @ forces.reshape(-1), np.asarray([0.0, 0.0, 2.0]))
    certificate = certify_planar_wrench(offsets, np.asarray([4.0, 4.0]), np.asarray([0.0, 0.0, 2.0]))
    assert certificate.feasible
    assert certificate.residual_norm <= 1e-9


def test_aggregate_capacity_is_not_sufficient_for_moment() -> None:
    offsets = np.zeros((4, 2))
    limits = np.full(4, 8.0)
    wrench = np.asarray([0.0, 0.0, 2.0])
    assert aggregate_force_only_feasible(limits, wrench)
    assert not certify_planar_wrench(offsets, limits, wrench).feasible


def test_caging_grid_separates_closed_ring_and_gap() -> None:
    grid = np.zeros((11, 11), dtype=bool)
    grid[1:-1, 1:-1] = True
    closed = verify_grid_caging(grid, (5, 5), resolution_label="test")
    assert closed.status == "no_escape_at_resolution"
    grid[0, 5] = True
    opened = verify_grid_caging(grid, (5, 5), resolution_label="test")
    assert opened.status == "escape_found"
    assert opened.path[0] == (5, 5)


def test_message_size_is_deterministic() -> None:
    first = {"b": 2, "a": [1.0, 2.0]}
    second = {"a": [1.0, 2.0], "b": 2}
    assert canonical_message_bytes(first) == canonical_message_bytes(second)


def test_smoke_campaign_writes_audited_artifacts(tmp_path: Path) -> None:
    config = yaml.safe_load(
        Path("experiments/configs/sp2_canonical_smoke.yaml").read_text(
            encoding="utf-8"
        )
    )
    config["output_dir"] = str(tmp_path / "sp2")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run_sp2_canonical_config(config_path)
    audit = json.loads(
        (tmp_path / "sp2" / "audit.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "complete"
    assert audit["status"] == "passed"
    assert (tmp_path / "sp2" / "generated" / "metrics.tex").is_file()
    assert (tmp_path / "sp2" / "figures" / "n2_pressure_dispersion.pdf").is_file()
