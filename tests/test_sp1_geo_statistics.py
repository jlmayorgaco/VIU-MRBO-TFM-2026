from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from viu_mrob_tfm.sp1_geo.runner import (
    _h3_comparison_masks,
    _static_recourse_gate,
    run_benchmark,
)
from viu_mrob_tfm.sp1_geo.statistics import (
    bernstein_margin,
    exact_mcnemar,
    friedman_kendall_w,
    holm_adjust,
    paired_bootstrap_interval,
    paired_permutation_test,
    paired_tost,
    paired_wilcoxon,
)


def test_exact_pairing_and_ties_are_preserved() -> None:
    first = [True, True, False, True, False]
    second = [False, True, False, False, True]
    result = exact_mcnemar(first, second)
    assert result["n_pairs"] == 5
    assert result["favorable_discordances"] == 2
    assert result["adverse_discordances"] == 1
    assert result["ties"] == 2


def test_bootstrap_and_permutation_are_reproducible() -> None:
    first = [1.0, 2.0, 3.0, 4.0]
    second = [0.0, 1.0, 2.0, 3.0]
    one = paired_bootstrap_interval(first, second, resamples=200, seed=17)
    two = paired_bootstrap_interval(first, second, resamples=200, seed=17)
    assert one == two
    permutation = paired_permutation_test(first, second)
    assert permutation["effect"] == 1.0
    assert 0.0 <= permutation["p_value"] <= 1.0


def test_holm_wilcoxon_friedman_and_tost_return_bounded_statistics() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.03])
    assert adjusted == sorted(adjusted)
    assert all(0.0 <= value <= 1.0 for value in adjusted)
    wilcoxon = paired_wilcoxon([1, 2, 3, 4], [0, 1, 2, 3])
    assert -1.0 <= wilcoxon["rank_biserial"] <= 1.0
    friedman = friedman_kendall_w(
        np.array([[1, 2, 3], [1, 2, 3], [2, 3, 4]], dtype=float)
    )
    assert 0.0 <= friedman["kendall_w"] <= 1.0
    tost = paired_tost(
        [1.001, 0.999, 1.000, 1.002],
        [1.000, 1.000, 1.000, 1.000],
        margin=0.02,
    )
    assert tost["equivalent"]


def test_bernstein_margin_is_positive_and_monotone() -> None:
    narrow = bernstein_margin(0.01, 0.05, 0.05)
    wide = bernstein_margin(0.02, 0.05, 0.05)
    assert 0.0 < narrow < wide


def test_h3_uses_raw_f3_f4_outputs() -> None:
    runs = pd.DataFrame(
        {
            "closure_stage": ["RAW", "RECOVERED", "RAW", "RAW"],
            "engine": ["qpg_logit"] * 4,
            "family": [
                "F3_torque_complementarity",
                "F3_torque_complementarity",
                "F4_mixed_geometry_route",
                "F0_easy_separable",
            ],
            "signal": [
                "marginal_physical",
                "scalar_capacity",
                "scalar_capacity",
                "marginal_physical",
            ],
        }
    )
    physical, scalar = _h3_comparison_masks(runs, "qpg_logit")
    assert physical.tolist() == [True, False, False, False]
    assert scalar.tolist() == [False, False, True, False]


def test_static_recourse_gate_requires_ratio_and_noninferior_feasibility() -> None:
    passing = _static_recourse_gate(
        pd.Series([6.0, 7.0]),
        pd.Series([10.0, 10.0]),
        pd.Series([1.0, 0.0]),
        pd.Series([1.0, 0.0]),
    )
    failing = _static_recourse_gate(
        pd.Series([6.0, 7.0]),
        pd.Series([10.0, 10.0]),
        pd.Series([0.0, 0.0]),
        pd.Series([1.0, 0.0]),
    )
    assert passing["recourse_ratio"] == 0.65
    assert passing["gate_passed"]
    assert not failing["gate_passed"]


def test_checkpoint_resume_is_idempotent(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[1]
    output = tmp_path / "result"
    config = {
        "experiment_id": "SP1_GEO_TEST",
        "mode": "preview",
        "output_dir": str(output),
        "scenario_files": {
            "F0_easy_separable": str(
                repository
                / "configs"
                / "scenarios"
                / "sp1_geo"
                / "F0_easy_separable.yaml"
            )
        },
        "sizes": [[4, 1]],
        "seed_blocks": {
            "preview": {"values": [991001]},
            "tuning": {"values": [991101]},
            "confirmatory": {"values": [991201]},
        },
        "methods": {
            "qpg": {
                "entropy_tau": 0.08,
                "damping": 0.25,
                "smith_damping": 0.01,
                "max_iterations": 5,
                "tolerance": 1e-5,
                "consensus_rounds": 1,
                "trace_stride": 2,
            },
            "cbba": {"max_bundle_rounds": 4},
            "grape": {"max_iterations": 2},
        },
        "oracles": {
            "milp_max_n": 0,
            "lp_max_n": 0,
            "entropic_max_n": 0,
            "milp_time_limit_s": 1.0,
            "entropic_max_iterations": 20,
        },
        "recovery": {
            "delta": 1e-9,
            "max_chain_length": 4,
            "candidates_per_load": 4,
            "enable_swaps": True,
        },
        "statistics": {
            "analysis_seed": 991301,
            "bootstrap_resamples": 50,
            "permutation_resamples": 100,
        },
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    run_benchmark(config_path)
    first = pd.read_parquet(output / "runs.parquet")
    run_benchmark(config_path, resume=True)
    second = pd.read_parquet(output / "runs.parquet")
    manifest = json.loads(
        (output / "manifest.json").read_text(encoding="utf-8")
    )
    assert len(first) == len(second) == 39
    assert second["world_hash"].nunique() == 1
    assert manifest["expected_worlds"] == manifest["completed_worlds"] == 1
