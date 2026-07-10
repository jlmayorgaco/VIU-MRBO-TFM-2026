import numpy as np
import pytest

from viu_mrob_tfm.experiment_stats import (
    apply_holm_correction,
    bootstrap_mean_ci,
    mean_difference_inference,
    wilcoxon_signed_rank_pvalue,
)


def test_bootstrap_ci_and_effect_summary_are_deterministic() -> None:
    diffs = np.asarray([0.1, 0.2, 0.3, 0.4], dtype=float)

    ci_a = bootstrap_mean_ci(diffs, seed=7)
    ci_b = bootstrap_mean_ci(diffs, seed=7)
    summary = mean_difference_inference(diffs, ci_seed=7)

    assert ci_a == pytest.approx(ci_b)
    assert ci_a[0] <= float(np.mean(diffs)) <= ci_a[1]
    assert summary["effect"] == pytest.approx(0.25)
    assert summary["effect_size_name"] == "cohens_dz"
    assert summary["rank_biserial"] == pytest.approx(1.0)


def test_wilcoxon_and_holm_correction_report_raw_and_corrected_decisions() -> None:
    p_value = wilcoxon_signed_rank_pvalue([1.0, 2.0, 3.0, 4.0], alternative="greater")
    rows = [
        {"id": "H1", "p_value": p_value, "alpha": 0.05, "reject": p_value < 0.05},
        {"id": "H2", "p_value": 0.04, "alpha": 0.05, "reject": True},
        {"id": "H3", "p_value": np.nan, "alpha": 0.05, "reject": False},
    ]

    corrected = apply_holm_correction(rows)

    assert corrected[0]["p_value_raw"] == pytest.approx(p_value)
    assert corrected[0]["p_value_holm"] <= 1.0
    assert corrected[1]["reject_raw"] is True
    assert corrected[1]["reject"] is corrected[1]["reject_holm"]
    assert np.isnan(corrected[2]["p_value_holm"])
    assert corrected[2]["reject_holm"] is False
