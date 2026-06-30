"""Common data structures and exporters for validation protocols."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class GateRecord:
    """Single acceptance check in the validation suite."""

    protocol: str
    claim: str
    evidence_class: str
    metric: str
    observed: float
    threshold: float
    direction: str
    passed: bool
    note: str


@dataclass(frozen=True)
class ComparisonRecord:
    """Comparison between a candidate treatment and a baseline."""

    protocol: str
    candidate: str
    baseline: str
    metric: str
    delta_mean: float
    ci95_low: float
    ci95_high: float
    passed: bool
    note: str


@dataclass(frozen=True)
class HypothesisDecision:
    """H0/H1 decision with mathematical, statistical, and robotic evidence."""

    protocol: str
    h0: str
    h1: str
    evidence_math: str
    statistical_test: str
    n: str
    alpha: str
    statistic: str
    p_value: str
    ci95: str
    coppelia_evidence: str
    decision: str
    scope: str


@dataclass(frozen=True)
class SuiteSummary:
    """Top-level result of a validation-suite execution."""

    protocol_version: str
    gate_count: int
    gate_pass_count: int
    comparison_count: int
    comparison_pass_count: int
    all_required_passed: bool


def write_dict_csv(path: Path, rows: Iterable[object]) -> None:
    """Write dataclass rows to CSV."""

    materialized = [asdict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not materialized:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0].keys()))
        writer.writeheader()
        writer.writerows(materialized)


def write_json(path: Path, payload: object) -> None:
    """Write a JSON payload with stable formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "__dataclass_fields__"):
        data = asdict(payload)
    else:
        data = payload
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
