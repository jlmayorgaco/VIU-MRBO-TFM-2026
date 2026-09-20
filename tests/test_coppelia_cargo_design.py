from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from viu_mrob_tfm.coppelia_cargo import build_run_specs, build_worlds, evaluate_guard, load_config
from viu_mrob_tfm.coppelia_cargo.campaign import run_campaign


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATORY = ROOT / "experiments" / "configs" / "coppelia_cargo_confirmatory.yaml"
SMOKE = ROOT / "experiments" / "configs" / "coppelia_cargo_smoke.yaml"


def test_confirmatory_design_is_exact_and_paired() -> None:
    config = load_config(CONFIRMATORY)
    worlds = build_worlds(config)
    runs = build_run_specs(config)
    primary = [run for run in runs if run.phase == "primary"]
    sensitivity = [run for run in runs if run.phase == "dt_sensitivity"]

    assert config.design.cell_count == 16
    assert config.design.payload_mass_kg == (14.0, 28.0)
    assert config.design.friction_regime == ("low", "nominal")
    assert config.design.coalition == ("minimal", "redundant")
    assert config.design.longitudinal_acceleration_m_s2 == (0.10, 0.25)
    assert {
        name: len(config.design.coalitions_m[name]) for name in config.design.coalition
    } == {"minimal": 3, "redundant": 4}
    assert len(worlds) == 16 * 30
    assert len(primary) == 16 * 30 * 3
    assert len(sensitivity) == 2 * 5 * 3 * 3

    primary_pairs: dict[tuple[int, int], set[str]] = defaultdict(set)
    for run in primary:
        primary_pairs[(run.world.cell.index, run.world.seed)].add(run.world.world_hash)
    assert all(len(hashes) == 1 for hashes in primary_pairs.values())

    sensitivity_pairs: dict[tuple[int, int], set[str]] = defaultdict(set)
    for run in sensitivity:
        sensitivity_pairs[(run.world.cell.index, run.world.seed)].add(run.world.world_hash)
    assert all(len(hashes) == 1 for hashes in sensitivity_pairs.values())
    assert all(
        world.active_robot_count == len(world.contact_offsets_body_m)
        for world in worlds
    )


def test_world_generation_is_order_independent_and_repeatable() -> None:
    config = load_config(CONFIRMATORY)
    first = build_worlds(config)
    second = build_worlds(config)
    assert [item.world_hash for item in first] == [item.world_hash for item in second]
    assert [item.as_record() for item in first] == [item.as_record() for item in second]


def test_guard_hierarchy_and_same_world_contract() -> None:
    config = load_config(CONFIRMATORY)
    observed_rejection = False
    for world in build_worlds(config):
        scalar = evaluate_guard(config, world, "scalar_capacity")
        planar = evaluate_guard(config, world, "planar_lsq")
        supported = evaluate_guard(config, world, "supported_wrench_wheels")
        assert not planar.accepted or scalar.accepted
        assert not supported.accepted or planar.accepted
        observed_rejection = observed_rejection or not supported.accepted
    assert observed_rejection, "the factorial must exercise a rejection regime"


def test_confirmatory_requires_explicit_authorization(tmp_path: Path) -> None:
    config = load_config(CONFIRMATORY)
    with pytest.raises(PermissionError, match="authorize-confirmatory"):
        run_campaign(config, output_dir=tmp_path / "must_not_exist")
    assert not (tmp_path / "must_not_exist").exists()


def test_synthetic_backend_cannot_be_configured_as_confirmatory(tmp_path: Path) -> None:
    text = SMOKE.read_text(encoding="utf-8").replace("mode: smoke", "mode: confirmatory")
    path = tmp_path / "invalid.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="Synthetic|synthetic"):
        load_config(path)
