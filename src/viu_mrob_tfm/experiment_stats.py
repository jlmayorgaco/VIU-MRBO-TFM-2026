"""Shared statistical inference helpers for SP experiment reports."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import stats


DEFAULT_BOOTSTRAP_SEED = 20260707


def finite_array(values: Any) -> np.ndarray:
    """Return a one-dimensional finite float array."""

    array = np.asarray(values, dtype=float).reshape(-1)
    return array[np.isfinite(array)]


def bootstrap_mean_ci(
    values: Any,
    *,
    confidence: float = 0.95,
    n_boot: int = 2_000,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval for the sample mean."""

    finite = finite_array(values)
    if finite.size == 0:
        return math.nan, math.nan
    if finite.size == 1 or n_boot <= 0:
        mean = float(np.mean(finite))
        return mean, mean
    alpha = max(0.0, min(1.0, 1.0 - confidence))
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, finite.size, size=(int(n_boot), finite.size))
    means = np.mean(finite[indices], axis=1)
    low, high = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(low), float(high)


def cohens_dz(diffs: Any) -> float:
    """Paired-sample standardized mean difference."""

    finite = finite_array(diffs)
    if finite.size < 2:
        return 0.0
    std = float(np.std(finite, ddof=1))
    if std <= 1.0e-12:
        return 0.0
    return float(np.mean(finite) / std)


def rank_biserial_from_diffs(diffs: Any) -> float:
    """Rank-biserial effect size for signed paired differences."""

    finite = finite_array(diffs)
    finite = finite[np.abs(finite) > 1.0e-12]
    if finite.size == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(finite))
    positive = float(np.sum(ranks[finite > 0.0]))
    negative = float(np.sum(ranks[finite < 0.0]))
    denom = float(finite.size * (finite.size + 1) / 2.0)
    return float((positive - negative) / denom) if denom > 0.0 else 0.0


def mean_difference_inference(
    diffs: Any,
    *,
    effect_name: str = "mean_paired_difference",
    ci_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, float | str]:
    """Summary fields for a paired or one-sample difference vector."""

    finite = finite_array(diffs)
    effect = float(np.mean(finite)) if finite.size else math.nan
    ci_low, ci_high = bootstrap_mean_ci(finite, seed=ci_seed)
    return {
        "effect": effect,
        "effect_name": effect_name,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "effect_size": cohens_dz(finite),
        "effect_size_name": "cohens_dz",
        "rank_biserial": rank_biserial_from_diffs(finite),
    }


def mean_value_inference(
    values: Any,
    *,
    effect_name: str = "mean",
    ci_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, float | str]:
    """Summary fields for a scalar sample mean."""

    finite = finite_array(values)
    effect = float(np.mean(finite)) if finite.size else math.nan
    ci_low, ci_high = bootstrap_mean_ci(finite, seed=ci_seed)
    return {
        "effect": effect,
        "effect_name": effect_name,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "effect_size": cohens_dz(finite),
        "effect_size_name": "standardized_mean",
        "rank_biserial": math.nan,
    }


def wilcoxon_signed_rank_pvalue(diffs: Any, *, alternative: str = "two-sided") -> float:
    """Robust Wilcoxon signed-rank p-value for paired differences."""

    finite = finite_array(diffs)
    if finite.size < 2:
        return 1.0
    if alternative not in {"less", "greater", "two-sided"}:
        alternative = "two-sided"
    try:
        result = stats.wilcoxon(finite, alternative=alternative, zero_method="zsplit")
        p_value = float(result.pvalue)
    except ValueError:
        p_value = 1.0
    return p_value if np.isfinite(p_value) else 1.0


def apply_holm_correction(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add Holm-Bonferroni adjusted p-values and corrected decisions."""

    for row in rows:
        raw_p = _safe_float(row.get("p_value", math.nan))
        row["p_value_raw"] = raw_p
        row.setdefault("p_value_holm", math.nan)
        row.setdefault("reject_raw", bool(np.isfinite(raw_p) and raw_p < _safe_float(row.get("alpha", 0.05))))
        row.setdefault("reject_holm", False)
    indexed = [(idx, _safe_float(row.get("p_value_raw"))) for idx, row in enumerate(rows)]
    indexed = [(idx, p_value) for idx, p_value in indexed if np.isfinite(p_value)]
    indexed.sort(key=lambda item: item[1])
    m = len(indexed)
    running = 0.0
    for rank, (idx, p_value) in enumerate(indexed, start=1):
        adjusted = min(1.0, float((m - rank + 1) * p_value))
        running = max(running, adjusted)
        row = rows[idx]
        row["p_value_holm"] = running
        alpha = _safe_float(row.get("alpha", 0.05))
        row["reject_holm"] = bool(running < alpha)
        row["reject"] = bool(row["reject_holm"])
    return rows


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
