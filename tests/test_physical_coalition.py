from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from viu_mrob_tfm.physical_coalition.model import CertificateStage
from viu_mrob_tfm.physical_coalition.runner import prepare_protocol, run_official
from viu_mrob_tfm.physical_coalition.scenario import make_world
from viu_mrob_tfm.physical_coalition.simulation import run_variant


def test_world_and_evaluation_are_deterministic() -> None:
    first_world = make_world(family="nominal_rotation", seed=8123, ordinal=2)
    second_world = make_world(family="nominal_rotation", seed=8123, ordinal=2)
    assert first_world.world_hash == second_world.world_hash
    first, _ = run_variant(first_world, CertificateStage.ROBUST_LOCAL)
    second, _ = run_variant(second_world, CertificateStage.ROBUST_LOCAL)
    ignored = {"runtime_wall_s", "runtime_cpu_s", "runtime_s"}
    assert {key: value for key, value in first.items() if key not in ignored} == {
        key: value for key, value in second.items() if key not in ignored
    }


def test_obstacle_full_is_safe_and_recovers_selected_dropout() -> None:
    world = make_world(family="obstacle_network_dropout", seed=8103, ordinal=0)
    row, trajectory = run_variant(world, CertificateStage.ROBUST_LOCAL, retain_trajectory=True)
    assert row["collision"] is False
    assert row["minimum_clearance_m"] >= 0.0
    assert row["recovery_count"] == 1
    assert row["dropout_unrecovered"] is False
    assert row["final_physical_success"] is True
    assert trajectory


def test_certificate_false_positive_semantics_are_explicit() -> None:
    world = make_world(family="obstacle_network_dropout", seed=8103, ordinal=0)
    raw, _ = run_variant(world, CertificateStage.RAW_PREF)
    assert raw["accepted_by_stage"] is True
    assert raw["final_physical_success"] is False
    assert raw["physical_false_positive"] is True
    assert raw["failure_code"] == "collision"


def test_mechanics_stage_restores_dynamic_authority_after_wrench_reduction() -> None:
    world = make_world(family="scarcity_capacity", seed=8101, ordinal=0)
    wrench, _ = run_variant(world, CertificateStage.WRENCH_PAIR)
    mechanics, _ = run_variant(world, CertificateStage.MECHANICS_SAFE)
    assert wrench["wrench_ok"] is True
    assert wrench["final_physical_success"] is False
    assert mechanics["selected_robots"] >= wrench["selected_robots"]
    assert mechanics["final_physical_success"] is True


def _small_config() -> Path:
    config = {
        "protocol_id": "TEST_PHYSICAL_CERTIFICATE",
        "protocol_version": "test",
        "cpu_only": True,
        "simulator": "deterministic_reduced_order_python",
        "output_dir": "output/test_physical_coalition_protocol",
        "scenario_families": ["nominal_rotation", "scarcity_capacity", "torque_complementarity", "obstacle_network_dropout"],
        "certificate_stages": [stage.value for stage in CertificateStage],
        "worlds": {"base_per_family": 40, "precision_checkpoints": [40, 60, 100], "base_seed_start": 910000, "extension_seed_start": 920000, "dry_run_seeds": [930001, 930002, 930003, 930004]},
        "precision": {"metric": "paired_success_difference", "max_ci95_width": 0.2, "bootstrap_samples": 50, "extension_rule": "width_only"},
        "statistics": {"alpha": 0.05, "multiplicity": "Holm"},
        "runtime": {"workers": 1, "omp_threads": 1},
    }
    path = Path("output/test_physical_coalition_protocol_config.yaml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_seed_registry_is_disjoint_and_official_run_is_frozen_guarded() -> None:
    config_path = _small_config()
    prepared = prepare_protocol(config_path)
    assert prepared["status"] == "prepared_pre_freeze"
    registry = yaml.safe_load((Path("output/test_physical_coalition_protocol/protocol/seed_registry.yaml")).read_text(encoding="utf-8"))
    groups = [registry["dry_run_seeds"]]
    for key in ("test_seeds_1_40", "extension_seeds_41_60", "extension_seeds_61_100"):
        groups.extend(registry[key].values())
    flat = [seed for group in groups for seed in group]
    assert len(flat) == len(set(flat))
    with pytest.raises(RuntimeError, match="before a valid freeze"):
        run_official(config_path, workers=1)