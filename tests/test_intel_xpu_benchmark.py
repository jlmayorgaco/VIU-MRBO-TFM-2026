from __future__ import annotations

import pytest

from viu_mrob_tfm.benchmarks.intel_xpu import PRESETS, summarize_timings, validate_preset


def test_timing_summary_uses_cpu_over_xpu_speedup() -> None:
    summary = summarize_timings(
        cpu_s=[4.0, 2.0, 3.0],
        xpu_s=[1.5, 1.0, 2.0],
        xpu_e2e_s=[2.5, 2.0, 3.0],
    )
    assert summary["cpu_median_s"] == pytest.approx(3.0)
    assert summary["speedup_resident_cpu_over_xpu"] == pytest.approx(2.0)
    assert summary["speedup_end_to_end_cpu_over_xpu"] == pytest.approx(1.2)


def test_empty_timing_collection_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        summarize_timings([], [1.0], [1.0])


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_benchmark_presets_are_well_formed(preset: str) -> None:
    validate_preset(preset)

