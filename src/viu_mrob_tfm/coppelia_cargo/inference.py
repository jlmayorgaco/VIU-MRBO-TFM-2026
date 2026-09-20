"""Preregistered paired inference for Cargo guard classification errors."""

from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, norm

from .config import CampaignConfig
from .design import factorial_cells


ENDPOINTS = (
    "false_positive_incidence",
    "false_negative_incidence",
    "misclassification_rate",
)


def wilson_interval(successes: int, total: int, confidence_level: float) -> tuple[float, float]:
    """Two-sided Wilson score interval for a binomial proportion."""

    if successes < 0 or total < 0 or successes > total:
        raise ValueError("invalid binomial counts")
    if total == 0:
        return float("nan"), float("nan")
    alpha = 1.0 - confidence_level
    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def mcnemar_exact_two_sided(a_event: np.ndarray, b_event: np.ndarray) -> tuple[int, int, float]:
    """Return discordances and the exact two-sided McNemar/binomial p-value."""

    a = np.asarray(a_event, dtype=bool)
    b = np.asarray(b_event, dtype=bool)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("paired binary endpoints must be one-dimensional and equally sized")
    a_only = int(np.sum(a & ~b))
    b_only = int(np.sum(~a & b))
    discordant = a_only + b_only
    p_value = (
        1.0
        if discordant == 0
        else float(binomtest(a_only, discordant, p=0.5, alternative="two-sided").pvalue)
    )
    return a_only, b_only, p_value


def holm_adjust(p_values: list[float]) -> list[float]:
    """Step-down Holm adjustment, monotone in sorted p-value order."""

    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in p_values):
        raise ValueError("p-values must be finite and lie in [0, 1]")
    count = len(p_values)
    adjusted = [1.0] * count
    running = 0.0
    for rank, index in enumerate(sorted(range(count), key=p_values.__getitem__)):
        running = max(running, (count - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def _paired_bootstrap_interval(
    differences: np.ndarray,
    *,
    confidence_level: float,
    resamples: int,
    seed_sequence: np.random.SeedSequence,
) -> tuple[float, float]:
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or values.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed_sequence)
    indices = rng.integers(0, values.size, size=(resamples, values.size))
    estimates = np.mean(values[indices], axis=1)
    alpha = 1.0 - confidence_level
    low, high = np.quantile(estimates, [alpha / 2.0, 1.0 - alpha / 2.0])
    return float(low), float(high)


def _event(row: dict[str, object], endpoint: str) -> bool:
    accepted = bool(row["guard_accepted"])
    success = bool(row["physical_success"])
    if endpoint == "false_positive_incidence":
        return accepted and not success
    if endpoint == "false_negative_incidence":
        return not accepted and success
    if endpoint == "misclassification_rate":
        return accepted != success
    raise ValueError(f"unknown endpoint: {endpoint}")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty inferential table: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_inference(
    config: CampaignConfig,
    run_rows: list[dict[str, object]],
    *,
    backend_kind: str,
    evidence_class: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Build cell rates and paired guard contrasts from primary runs only."""

    primary = [row for row in run_rows if row["phase"] == "primary"]
    lookup = {
        (str(row["cell_id"]), int(row["seed"]), str(row["guard"])): row
        for row in primary
    }
    cells = factorial_cells(config)
    inferential_status = (
        "smoke_only_no_inferential_claim"
        if config.mode != "confirmatory"
        else (
            "physical_candidate_subject_to_campaign_gates"
            if backend_kind == "coppeliasim_mujoco"
            else "synthetic_software_check_only"
        )
    )

    rate_rows: list[dict[str, object]] = []
    for cell in cells:
        for guard in config.guards:
            items = [
                lookup[(cell.cell_id, seed, guard)]
                for seed in config.design.seeds.values
                if (cell.cell_id, seed, guard) in lookup
                and lookup[(cell.cell_id, seed, guard)]["execution_status"] == "completed"
            ]
            total = len(items)
            accepted = sum(bool(row["guard_accepted"]) for row in items)
            success = sum(bool(row["physical_success"]) for row in items)
            false_positive = sum(_event(row, "false_positive_incidence") for row in items)
            false_negative = sum(_event(row, "false_negative_incidence") for row in items)
            misclassified = sum(_event(row, "misclassification_rate") for row in items)
            record: dict[str, object] = {
                "cell_id": cell.cell_id,
                "payload_mass_kg": cell.payload_mass_kg,
                "friction_regime": cell.friction_regime,
                "friction_coefficient": cell.friction_coefficient,
                "coalition": cell.coalition,
                "active_robot_count": cell.active_robot_count,
                "longitudinal_acceleration_m_s2": cell.longitudinal_acceleration_m_s2,
                "guard": guard,
                "n_expected": config.design.seeds.count,
                "n_completed": total,
                "backend_kind": backend_kind,
                "evidence_class": evidence_class,
                "inferential_status": inferential_status,
                "confidence_level": config.inference.confidence_level,
                "rate_ci_method": "Wilson score, two-sided",
            }
            metrics = {
                "acceptance_rate": accepted,
                "physical_success_rate": success,
                "false_positive_incidence": false_positive,
                "false_negative_incidence": false_negative,
                "misclassification_rate": misclassified,
            }
            for name, numerator in metrics.items():
                low, high = wilson_interval(numerator, total, config.inference.confidence_level)
                record[name] = numerator / total if total else float("nan")
                record[f"{name}_ci_low"] = low
                record[f"{name}_ci_high"] = high
            rate_rows.append(record)

    contrast_rows: list[dict[str, object]] = []
    guard_pairs = tuple(itertools.combinations(config.guards, 2))
    for cell in cells:
        for endpoint_index, endpoint in enumerate(ENDPOINTS):
            family: list[dict[str, object]] = []
            for pair_index, (guard_a, guard_b) in enumerate(guard_pairs):
                paired = []
                for seed in config.design.seeds.values:
                    key_a = (cell.cell_id, seed, guard_a)
                    key_b = (cell.cell_id, seed, guard_b)
                    if key_a not in lookup or key_b not in lookup:
                        continue
                    row_a, row_b = lookup[key_a], lookup[key_b]
                    if row_a["execution_status"] != "completed" or row_b["execution_status"] != "completed":
                        continue
                    paired.append((_event(row_a, endpoint), _event(row_b, endpoint)))
                a = np.asarray([item[0] for item in paired], dtype=bool)
                b = np.asarray([item[1] for item in paired], dtype=bool)
                a_only, b_only, p_raw = mcnemar_exact_two_sided(a, b)
                differences = a.astype(float) - b.astype(float)
                low, high = _paired_bootstrap_interval(
                    differences,
                    confidence_level=config.inference.confidence_level,
                    resamples=config.inference.bootstrap_resamples,
                    seed_sequence=np.random.SeedSequence(
                        [config.inference.analysis_seed, cell.index, endpoint_index, pair_index]
                    ),
                )
                family.append(
                    {
                        "contrast_id": f"{cell.cell_id}:{endpoint}:{guard_a}-vs-{guard_b}",
                        "cell_id": cell.cell_id,
                        "payload_mass_kg": cell.payload_mass_kg,
                        "friction_regime": cell.friction_regime,
                        "friction_coefficient": cell.friction_coefficient,
                        "coalition": cell.coalition,
                        "active_robot_count": cell.active_robot_count,
                        "longitudinal_acceleration_m_s2": cell.longitudinal_acceleration_m_s2,
                        "endpoint": endpoint,
                        "guard_a": guard_a,
                        "guard_b": guard_b,
                        "n_expected_pairs": config.design.seeds.count,
                        "n_complete_pairs": len(paired),
                        "rate_a": float(np.mean(a)) if a.size else float("nan"),
                        "rate_b": float(np.mean(b)) if b.size else float("nan"),
                        "effect_a_minus_b": float(np.mean(differences)) if differences.size else float("nan"),
                        "effect_ci_low": low,
                        "effect_ci_high": high,
                        "effect_ci_method": "paired percentile bootstrap over seeds",
                        "confidence_level": config.inference.confidence_level,
                        "discordant_a1_b0": a_only,
                        "discordant_a0_b1": b_only,
                        "mcnemar_method": "exact two-sided binomial",
                        "mcnemar_p_raw": p_raw,
                        "holm_family_id": f"{cell.cell_id}:{endpoint}",
                        "holm_family_definition": config.inference.holm_family,
                        "holm_family_size": len(guard_pairs),
                        "analysis_seed": config.inference.analysis_seed,
                        "bootstrap_resamples": config.inference.bootstrap_resamples,
                        "backend_kind": backend_kind,
                        "evidence_class": evidence_class,
                        "inferential_status": inferential_status,
                    }
                )
            adjusted = holm_adjust([float(row["mcnemar_p_raw"]) for row in family])
            alpha = 1.0 - config.inference.confidence_level
            for row, p_holm in zip(family, adjusted, strict=True):
                row["mcnemar_p_holm"] = p_holm
                row["reject_equal_marginals_holm"] = p_holm < alpha
                contrast_rows.append(row)

    expected_primary = config.design.cell_count * config.design.seeds.count * len(config.guards)
    contract = {
        "protocol_family": config.protocol_family,
        "analysis_population": "completed primary runs; one paired perturbation per cell and seed",
        "primary_endpoint": "false_positive_incidence = guard_accepts AND physical_transport_fails",
        "secondary_endpoints": [
            "false_negative_incidence = guard_rejects AND physical_transport_succeeds",
            "misclassification_rate = guard prediction differs from physical outcome",
        ],
        "rates": "per cell and guard with two-sided Wilson score intervals",
        "contrasts": "all three guard pairs within each cell and endpoint",
        "test": "exact two-sided McNemar test (conditional binomial on discordances)",
        "effect": "paired mean difference in binary endpoint, guard_a minus guard_b",
        "effect_interval": (
            "paired percentile bootstrap over the "
            f"{config.design.seeds.count} declared seed pair(s)"
        ),
        "multiplicity": "Holm correction across the three guard pairs within each cell and endpoint",
        "confidence_level": config.inference.confidence_level,
        "analysis_seed": config.inference.analysis_seed,
        "bootstrap_resamples": config.inference.bootstrap_resamples,
        "backend_kind": backend_kind,
        "evidence_class": evidence_class,
        "inferential_status": inferential_status,
        "expected_primary_runs": expected_primary,
        "recorded_primary_runs": len(primary),
        "complete": bool(
            len(primary) == expected_primary
            and all(row["execution_status"] == "completed" for row in primary)
            and all(int(row["n_complete_pairs"]) == config.design.seeds.count for row in contrast_rows)
        ),
        "limitation": (
            "The common controller maps bounded contact-force setpoints through "
            "wrench-error admittance to wheel velocities; exact wrench realization "
            "is not assumed. Contrasts estimate predictive classification error, "
            "not wrench-allocation tracking."
        ),
    }
    return rate_rows, contrast_rows, contract


def write_inference(
    config: CampaignConfig,
    run_rows: list[dict[str, object]],
    output_dir: Path,
    *,
    backend_kind: str,
    evidence_class: str,
) -> dict[str, object]:
    directory = output_dir / "inference"
    directory.mkdir()
    rates, contrasts, contract = build_inference(
        config,
        run_rows,
        backend_kind=backend_kind,
        evidence_class=evidence_class,
    )
    _write_csv(directory / "cell_guard_rates.csv", rates)
    _write_csv(directory / "paired_guard_contrasts.csv", contrasts)
    (directory / "analysis_contract.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return contract


__all__ = [
    "ENDPOINTS",
    "build_inference",
    "holm_adjust",
    "mcnemar_exact_two_sided",
    "wilson_interval",
    "write_inference",
]
