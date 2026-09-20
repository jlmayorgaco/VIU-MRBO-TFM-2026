"""World-paired confirmatory statistics for the SP1-GEO campaign."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any

import numpy as np
from scipy import stats


def holm_adjust(p_values: Iterable[float]) -> list[float]:
    values = np.asarray(list(p_values), dtype=float)
    adjusted = np.full(values.shape, math.nan)
    finite = np.flatnonzero(np.isfinite(values))
    if finite.size == 0:
        return adjusted.tolist()
    order = finite[np.argsort(values[finite])]
    running = 0.0
    total = len(order)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * float(values[index]))
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def exact_mcnemar(first: Iterable[bool], second: Iterable[bool]) -> dict[str, Any]:
    left = np.asarray(list(first), dtype=bool)
    right = np.asarray(list(second), dtype=bool)
    if left.shape != right.shape:
        raise ValueError("McNemar inputs must be paired and equal in length.")
    favorable = int(np.sum(left & ~right))
    adverse = int(np.sum(~left & right))
    discordant = favorable + adverse
    p_value = (
        float(stats.binomtest(min(favorable, adverse), discordant, 0.5).pvalue)
        if discordant
        else 1.0
    )
    return {
        "n_pairs": int(left.size),
        "favorable_discordances": favorable,
        "adverse_discordances": adverse,
        "ties": int(left.size - discordant),
        "effect": float(np.mean(left.astype(float) - right.astype(float)))
        if left.size
        else math.nan,
        "p_value": p_value,
    }


def paired_bootstrap_interval(
    first: Iterable[float],
    second: Iterable[float],
    *,
    statistic: Callable[[np.ndarray], float] = np.mean,
    resamples: int = 2_000,
    confidence: float = 0.95,
    seed: int = 990_001,
) -> dict[str, Any]:
    left = np.asarray(list(first), dtype=float)
    right = np.asarray(list(second), dtype=float)
    if left.shape != right.shape:
        raise ValueError("Bootstrap inputs must be paired.")
    mask = np.isfinite(left) & np.isfinite(right)
    differences = left[mask] - right[mask]
    if differences.size == 0:
        return {
            "n_pairs": 0,
            "effect": math.nan,
            "ci95_low": math.nan,
            "ci95_high": math.nan,
            "ties": 0,
        }
    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(resamples), dtype=float)
    for index in range(int(resamples)):
        sample = differences[
            rng.integers(0, differences.size, size=differences.size)
        ]
        estimates[index] = float(statistic(sample))
    alpha = 1.0 - float(confidence)
    low, high = np.quantile(estimates, [alpha / 2.0, 1.0 - alpha / 2.0])
    return {
        "n_pairs": int(differences.size),
        "effect": float(statistic(differences)),
        "ci95_low": float(low),
        "ci95_high": float(high),
        "ties": int(np.sum(np.isclose(differences, 0.0))),
    }


def paired_permutation_test(
    first: Iterable[float],
    second: Iterable[float],
    *,
    resamples: int = 10_000,
    seed: int = 990_002,
) -> dict[str, Any]:
    left = np.asarray(list(first), dtype=float)
    right = np.asarray(list(second), dtype=float)
    if left.shape != right.shape:
        raise ValueError("Permutation inputs must be paired.")
    mask = np.isfinite(left) & np.isfinite(right)
    differences = left[mask] - right[mask]
    if differences.size == 0:
        return {"n_pairs": 0, "effect": math.nan, "p_value": math.nan, "ties": 0}
    observed = abs(float(np.mean(differences)))
    if np.allclose(differences, 0.0):
        p_value = 1.0
    elif differences.size <= 18:
        signs = np.array(
            [
                [1.0 if (mask_value >> bit) & 1 else -1.0 for bit in range(differences.size)]
                for mask_value in range(2**differences.size)
            ],
            dtype=float,
        )
        values = np.abs(np.mean(signs * differences[None, :], axis=1))
        p_value = float(np.mean(values >= observed - 1e-15))
    else:
        rng = np.random.default_rng(int(seed))
        exceed = 0
        for _ in range(int(resamples)):
            signs = rng.choice([-1.0, 1.0], size=differences.size)
            exceed += int(abs(float(np.mean(signs * differences))) >= observed - 1e-15)
        p_value = (exceed + 1.0) / (int(resamples) + 1.0)
    return {
        "n_pairs": int(differences.size),
        "effect": float(np.mean(differences)),
        "p_value": float(p_value),
        "ties": int(np.sum(np.isclose(differences, 0.0))),
    }


def paired_wilcoxon(first: Iterable[float], second: Iterable[float]) -> dict[str, Any]:
    left = np.asarray(list(first), dtype=float)
    right = np.asarray(list(second), dtype=float)
    if left.shape != right.shape:
        raise ValueError("Wilcoxon inputs must be paired.")
    mask = np.isfinite(left) & np.isfinite(right)
    differences = left[mask] - right[mask]
    if differences.size == 0:
        return {
            "n_pairs": 0,
            "effect": math.nan,
            "p_value": math.nan,
            "rank_biserial": math.nan,
            "ties": 0,
        }
    nonzero = differences[~np.isclose(differences, 0.0)]
    if nonzero.size == 0:
        statistic, p_value, rank_biserial = 0.0, 1.0, 0.0
    else:
        test = stats.wilcoxon(nonzero, alternative="two-sided", zero_method="wilcox")
        statistic, p_value = float(test.statistic), float(test.pvalue)
        ranks = stats.rankdata(np.abs(nonzero))
        positive = float(np.sum(ranks[nonzero > 0.0]))
        negative = float(np.sum(ranks[nonzero < 0.0]))
        rank_biserial = (positive - negative) / max(positive + negative, 1e-15)
    return {
        "n_pairs": int(differences.size),
        "effect": float(np.median(differences)),
        "statistic": statistic,
        "p_value": p_value,
        "rank_biserial": float(rank_biserial),
        "ties": int(differences.size - nonzero.size),
    }


def friedman_kendall_w(matrix: np.ndarray) -> dict[str, Any]:
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2:
        raise ValueError("Friedman input must be a blocks × methods matrix.")
    values = values[np.all(np.isfinite(values), axis=1)]
    blocks, methods = values.shape
    if blocks < 2 or methods < 3:
        return {
            "n_blocks": blocks,
            "n_methods": methods,
            "statistic": math.nan,
            "p_value": math.nan,
            "kendall_w": math.nan,
        }
    test = stats.friedmanchisquare(
        *[values[:, method] for method in range(methods)]
    )
    denominator = blocks * (methods - 1)
    return {
        "n_blocks": blocks,
        "n_methods": methods,
        "statistic": float(test.statistic),
        "p_value": float(test.pvalue),
        "kendall_w": float(test.statistic / denominator),
    }


def paired_tost(
    first: Iterable[float],
    second: Iterable[float],
    *,
    margin: float,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Two one-sided paired t tests for equivalence within ``±margin``."""

    if margin <= 0.0:
        raise ValueError("TOST margin must be positive.")
    left = np.asarray(list(first), dtype=float)
    right = np.asarray(list(second), dtype=float)
    if left.shape != right.shape:
        raise ValueError("TOST inputs must be paired.")
    mask = np.isfinite(left) & np.isfinite(right)
    differences = left[mask] - right[mask]
    if differences.size < 2:
        return {
            "n_pairs": int(differences.size),
            "effect": float(np.mean(differences)) if differences.size else math.nan,
            "p_lower": math.nan,
            "p_upper": math.nan,
            "p_value": math.nan,
            "equivalent": False,
        }
    lower = stats.ttest_1samp(
        differences, popmean=-float(margin), alternative="greater"
    )
    upper = stats.ttest_1samp(
        differences, popmean=float(margin), alternative="less"
    )
    p_value = max(float(lower.pvalue), float(upper.pvalue))
    return {
        "n_pairs": int(differences.size),
        "effect": float(np.mean(differences)),
        "p_lower": float(lower.pvalue),
        "p_upper": float(upper.pvalue),
        "p_value": p_value,
        "equivalent": bool(p_value < alpha),
    }


def bernstein_margin(
    variance_sum: float,
    absolute_bound: float,
    alpha: float,
) -> float:
    """One-sided Bernstein margin for bounded independent zero-mean errors."""

    if variance_sum < 0.0 or absolute_bound <= 0.0 or not 0.0 < alpha < 1.0:
        raise ValueError("Invalid Bernstein parameters.")
    log_term = math.log(1.0 / alpha)
    return math.sqrt(2.0 * variance_sum * log_term) + (
        absolute_bound * log_term / 3.0
    )


__all__ = [
    "bernstein_margin",
    "exact_mcnemar",
    "friedman_kendall_w",
    "holm_adjust",
    "paired_bootstrap_interval",
    "paired_permutation_test",
    "paired_tost",
    "paired_wilcoxon",
]
