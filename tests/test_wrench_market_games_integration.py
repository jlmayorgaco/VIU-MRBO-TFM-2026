"""Integration checks for the Wrench-Market Games extension layer."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml

from viu_mrob_tfm.allocation import BaseAllocator
from viu_mrob_tfm.sp1.methods import make_sp1_allocator
from viu_mrob_tfm.sp2.methods import make_sp2_allocator
from viu_mrob_tfm.sp3.methods import BaseSP3Allocator, make_sp3_allocator
from viu_mrob_tfm.sp4.methods import BaseMotionPolicy, make_sp4_policy


ROOT = Path(__file__).resolve().parents[1]


def _assert_config_methods_exist(
    path: Path,
    factory: Callable[[str], BaseAllocator | BaseSP3Allocator | BaseMotionPolicy],
) -> list[str]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    methods = [str(item["id"]) for item in config["methods"]]
    assert methods
    for method_id in methods:
        assert factory(method_id) is not None
    return methods


def test_wrench_market_games_configs_are_factory_valid() -> None:
    specs: list[tuple[Path, Callable[[str], BaseAllocator | BaseSP3Allocator | BaseMotionPolicy]]] = [
        (ROOT / "configs/experiments/sp1/SP1_MC_wrench_market_protocol_repair.yaml", make_sp1_allocator),
        (ROOT / "configs/experiments/sp1/SP1_DIAG_wrench_market_protocol_repair.yaml", make_sp1_allocator),
        (ROOT / "configs/experiments/sp2/SP2_MC_wrench_market_vector_potential_repair.yaml", make_sp2_allocator),
        (ROOT / "configs/experiments/sp2/SP2_DIAG_wrench_market_vector_potential_repair.yaml", make_sp2_allocator),
        (ROOT / "configs/experiments/sp3/SP3_MC_wrench_market_protocol_invariance.yaml", make_sp3_allocator),
        (ROOT / "configs/experiments/sp3/SP3_DIAG_wrench_market_protocol_invariance.yaml", make_sp3_allocator),
        (ROOT / "configs/experiments/sp4/SP4_MC_wrench_market_motion_safety.yaml", make_sp4_policy),
        (ROOT / "configs/experiments/sp4/SP4_DIAG_wrench_market_motion_safety.yaml", make_sp4_policy),
    ]
    all_methods = []
    for path, factory in specs:
        assert path.exists()
        all_methods.extend(_assert_config_methods_exist(path, factory))

    for required in [
        "replicator_cardinality_repair",
        "smith_capacity_marginal_repair",
        "support_dual_wrench_market_guarded",
        "tensor_flow_motion_field",
    ]:
        assert required in all_methods


def test_wrench_market_games_documentation_is_linked_from_tfm() -> None:
    mapping = ROOT / "docs/WRENCH_MARKET_GAMES_INTEGRATION.md"
    tfm = ROOT / "TFM.md"
    assert mapping.exists()
    mapping_text = mapping.read_text(encoding="utf-8")
    tfm_text = tfm.read_text(encoding="utf-8")

    assert "Vector-aggregative potential game" in mapping_text
    assert "WRENCH_MARKET_GAMES_INTEGRATION.md" in tfm_text
    assert "Smith-QR no es la contribucion completa" in tfm_text
