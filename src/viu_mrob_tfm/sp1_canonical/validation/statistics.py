"""Predeclared statistical utilities for the SP1 conference campaign."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_interval(
    values: Iterable[float],
    *,
    statistic: Callable[[np.ndarray], float] = np.mean,
    confidence: float = 0.95,
    resamples: int = 2_000,
    seed: int = 970_001,
) -> tuple[float, float]:
    data = np.asarray(list(values), dtype=float)
    data = data[np.isfinite(data)]
    if data.size == 0:
        return math.nan, math.nan
    if data.size == 1:
        value = float(statistic(data))
        return value, value
    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(resamples), dtype=float)
    for index in range(int(resamples)):
        sample = data[rng.integers(0, data.size, size=data.size)]
        estimates[index] = float(statistic(sample))
    alpha = 1.0 - float(confidence)
    return tuple(float(value) for value in np.quantile(estimates, [alpha / 2.0, 1.0 - alpha / 2.0]))


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    z = float(stats.norm.ppf(0.5 + confidence / 2.0))
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def holm_adjust(p_values: Iterable[float]) -> list[float]:
    values = np.asarray(list(p_values), dtype=float)
    result = np.full_like(values, math.nan)
    finite_indices = np.flatnonzero(np.isfinite(values))
    if finite_indices.size == 0:
        return result.tolist()
    order = finite_indices[np.argsort(values[finite_indices])]
    running = 0.0
    count = len(order)
    for rank, index in enumerate(order):
        adjusted = min(1.0, (count - rank) * float(values[index]))
        running = max(running, adjusted)
        result[index] = running
    return result.tolist()


def paired_wilcoxon(first: Iterable[float], second: Iterable[float]) -> dict[str, float | int]:
    a = np.asarray(list(first), dtype=float)
    b = np.asarray(list(second), dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    differences = a[mask] - b[mask]
    if differences.size == 0:
        return {"n_pairs": 0, "statistic": math.nan, "p_value": math.nan, "rank_biserial": math.nan, "cohen_dz": math.nan}
    if np.allclose(differences, 0.0):
        statistic, p_value = 0.0, 1.0
    else:
        test = stats.wilcoxon(differences, alternative="two-sided", zero_method="wilcox")
        statistic, p_value = float(test.statistic), float(test.pvalue)
    nonzero = differences[~np.isclose(differences, 0.0)]
    if nonzero.size:
        ranks = stats.rankdata(np.abs(nonzero))
        positive = float(np.sum(ranks[nonzero > 0]))
        negative = float(np.sum(ranks[nonzero < 0]))
        rank_biserial = (positive - negative) / max(positive + negative, 1e-15)
    else:
        rank_biserial = 0.0
    deviation = float(np.std(differences, ddof=1)) if differences.size > 1 else 0.0
    cohen_dz = float(np.mean(differences) / deviation) if deviation > 0.0 else math.nan
    return {
        "n_pairs": int(differences.size),
        "statistic": statistic,
        "p_value": p_value,
        "rank_biserial": float(rank_biserial),
        "cohen_dz": cohen_dz,
    }


def friedman_kendall_w(matrix: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(matrix, dtype=float)
    values = values[np.all(np.isfinite(values), axis=1)]
    if values.shape[0] < 2 or values.shape[1] < 3:
        return {"n_blocks": int(values.shape[0]), "n_methods": int(values.shape[1] if values.ndim == 2 else 0), "statistic": math.nan, "p_value": math.nan, "kendall_w": math.nan}
    test = stats.friedmanchisquare(*[values[:, column] for column in range(values.shape[1])])
    denominator = values.shape[0] * (values.shape[1] - 1)
    return {
        "n_blocks": int(values.shape[0]),
        "n_methods": int(values.shape[1]),
        "statistic": float(test.statistic),
        "p_value": float(test.pvalue),
        "kendall_w": float(test.statistic / denominator) if denominator > 0 else math.nan,
    }


def spearman_bootstrap(
    x: Iterable[float],
    y: Iterable[float],
    *,
    resamples: int = 2_000,
    seed: int = 970_002,
) -> dict[str, float | int]:
    left = np.asarray(list(x), dtype=float)
    right = np.asarray(list(y), dtype=float)
    mask = np.isfinite(left) & np.isfinite(right)
    left, right = left[mask], right[mask]
    if left.size < 3 or np.unique(left).size < 2 or np.unique(right).size < 2:
        return {"n": int(left.size), "rho": math.nan, "p_value": math.nan, "ci95_low": math.nan, "ci95_high": math.nan}
    test = stats.spearmanr(left, right)
    rng = np.random.default_rng(int(seed))
    estimates: list[float] = []
    for _ in range(int(resamples)):
        indices = rng.integers(0, left.size, size=left.size)
        if np.unique(left[indices]).size < 2 or np.unique(right[indices]).size < 2:
            continue
        value = float(stats.spearmanr(left[indices], right[indices]).statistic)
        if np.isfinite(value):
            estimates.append(value)
    low, high = (math.nan, math.nan) if not estimates else tuple(float(v) for v in np.quantile(estimates, [0.025, 0.975]))
    return {"n": int(left.size), "rho": float(test.statistic), "p_value": float(test.pvalue), "ci95_low": low, "ci95_high": high}


def aggregate_numeric(
    runs: pd.DataFrame,
    *,
    group_columns: list[str],
    metrics: list[str],
    bootstrap_resamples: int,
    analysis_seed: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouped = runs.groupby(group_columns, dropna=False, sort=False)
    for group_index, (keys, group) in enumerate(grouped):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys, strict=True))
        row["n_runs"] = len(group)
        for metric in metrics:
            if metric not in group:
                continue
            values = pd.to_numeric(group[metric], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            row[f"{metric}_n"] = int(finite.size)
            row[f"{metric}_mean"] = float(np.mean(finite)) if finite.size else math.nan
            row[f"{metric}_median"] = float(np.median(finite)) if finite.size else math.nan
            row[f"{metric}_p90"] = float(np.quantile(finite, 0.90)) if finite.size else math.nan
            row[f"{metric}_p95"] = float(np.quantile(finite, 0.95)) if finite.size else math.nan
            low, high = bootstrap_interval(
                finite,
                statistic=np.mean,
                resamples=bootstrap_resamples,
                seed=analysis_seed + 101 * group_index + len(metric),
            )
            row[f"{metric}_mean_ci95_low"] = low
            row[f"{metric}_mean_ci95_high"] = high
        for binary in ("converged", "comparable_to_lp", "feasible", "arrival_success"):
            if binary not in group:
                continue
            valid = group[binary].dropna().astype(bool)
            successes = int(valid.sum())
            low, high = wilson_interval(successes, len(valid))
            row[f"{binary}_n"] = int(len(valid))
            row[f"{binary}_rate"] = float(valid.mean()) if len(valid) else math.nan
            row[f"{binary}_ci95_low"] = low
            row[f"{binary}_ci95_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


__all__ = [
    "aggregate_numeric",
    "bootstrap_interval",
    "friedman_kendall_w",
    "holm_adjust",
    "paired_wilcoxon",
    "spearman_bootstrap",
    "wilson_interval",
]
