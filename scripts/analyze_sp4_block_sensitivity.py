"""Reanalyse SP4 hypotheses at the independent seed-by-fleet block level.

The canonical SP4 table contains 108 paired scenario instances, but its independent
experimental blocks are the 18 combinations of seed and fleet size.  This script
aggregates each endpoint over the six scenarios inside a block and applies an exact
one-sided sign test, followed by Holm correction across the five frozen hypotheses.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/experiments/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3.yaml"
RUNS = ROOT / "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/tables/runs.csv"
OUT_DIR = ROOT / "results/sp4/SP4_DOCKING_GAME_CONFIRMATORY_v3/statistics"


def one_sided_sign_pvalue(positive: int, nonzero: int) -> float:
    """Return P[X >= positive] for X ~ Binomial(nonzero, 0.5)."""
    if nonzero == 0:
        return 1.0
    return sum(math.comb(nonzero, k) for k in range(positive, nonzero + 1)) / (2**nonzero)


def holm_adjust(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=pvalues.__getitem__)
    adjusted = [1.0] * len(pvalues)
    running = 0.0
    total = len(pvalues)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * pvalues[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    runs = pd.read_csv(RUNS)
    hypotheses = config["hypotheses"]
    records: list[dict[str, object]] = []

    for hypothesis in hypotheses:
        metric = hypothesis["metric"]
        subset = runs[runs["method"].isin([hypothesis["method_a"], hypothesis["method_b"]])]
        block = (
            subset.groupby(["seed", "n_robots", "method"], as_index=False)[metric]
            .mean()
            .pivot(index=["seed", "n_robots"], columns="method", values=metric)
        )
        original = block[hypothesis["method_a"]] - block[hypothesis["method_b"]]
        oriented = original if hypothesis["direction"] == "greater" else -original
        tolerance = 1.0e-12
        positive = int((oriented > tolerance).sum())
        negative = int((oriented < -tolerance).sum())
        nonzero = positive + negative
        records.append(
            {
                "hypothesis": hypothesis["id"],
                "metric": metric,
                "method_a": hypothesis["method_a"],
                "method_b": hypothesis["method_b"],
                "direction": hypothesis["direction"],
                "independent_blocks": int(len(block)),
                "scenarios_per_block": int(runs["scenario"].nunique()),
                "paired_instances": int(len(block) * runs["scenario"].nunique()),
                "mean_original_difference": float(original.mean()),
                "median_oriented_block_difference": float(oriented.median()),
                "positive_blocks": positive,
                "negative_blocks": negative,
                "tied_blocks": int(len(block) - nonzero),
                "p_raw": one_sided_sign_pvalue(positive, nonzero),
            }
        )

    adjusted = holm_adjust([float(record["p_raw"]) for record in records])
    for record, p_holm in zip(records, adjusted, strict=True):
        record["p_holm"] = p_holm
        record["supported_at_0_05"] = bool(p_holm < 0.05)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "block_sensitivity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    payload = {
        "analysis": "SP4 independent-block sensitivity",
        "independent_unit": ["seed", "n_robots"],
        "blocks": 18,
        "scenarios_per_block": 6,
        "paired_instances": 108,
        "test": "exact one-sided sign test over block-aggregated differences",
        "multiplicity": "Holm across five frozen hypotheses",
        "results": records,
    }
    (OUT_DIR / "block_sensitivity.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# SP4 independent-block sensitivity",
        "",
        "The independent unit is the `(seed, n_robots)` block. Each of the 18 blocks "
        "aggregates the same six scenarios; the 108 paired instances remain descriptive.",
        "",
        "| Hypothesis | Mean original difference | Positive / negative / tied blocks | Exact p | Holm p | Supported |",
        "|---|---:|---:|---:|---:|:---:|",
    ]
    for record in records:
        counts = f"{record['positive_blocks']} / {record['negative_blocks']} / {record['tied_blocks']}"
        lines.append(
            f"| {record['hypothesis']} | {record['mean_original_difference']:.6f} | {counts} | "
            f"{record['p_raw']:.6g} | {record['p_holm']:.6g} | "
            f"{'yes' if record['supported_at_0_05'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "Positive blocks are always oriented in the preregistered direction. No optional stopping or "
            "post-hoc change of endpoint was introduced.",
            "",
        ]
    )
    (OUT_DIR / "block_sensitivity.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
