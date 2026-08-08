"""Paths, labels and seeds owned exclusively by N3.

``sp1_levels_common.py`` is a build dependency of the frozen N1 and N2 packages
and is deliberately not touched: N1 and N2 must stay unchanged not only in
their RAW but in everything their build reads.

The pilot seed base is distinct from any confirmatory base and is the only seed
family this phase is allowed to open. Confirmatory seeds stay closed until the
design is approved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
N3_OUTPUT_ROOT = REPOSITORY_ROOT / "scripts" / "results" / "sp1_levels" / "n3_v1_pilot"

# Technical pilots only: sizing, radii and runtime. Never a reported result.
PILOT_SEED_BASE = 4242000
CONFIRMATORY_SEED_BASE: int | None = None  # opened only on approval

Q_BAR_KG = 5.0
WORKSPACE_M = (100.0, 100.0)
DEMAND_ALPHA = 3.0

SCENARIOS = ("uniform", "clustered", "separated", "ring", "corridor")

METHOD_LABELS = {
    "capacity_cbba": "Capacity-CBBA",
    "weighted_grape": "Weighted-GRAPE",
    "weighted_pair_grape": "Weighted-Pair-GRAPE",
}


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "CONFIRMATORY_SEED_BASE",
    "DEMAND_ALPHA",
    "METHOD_LABELS",
    "N3_OUTPUT_ROOT",
    "PILOT_SEED_BASE",
    "Q_BAR_KG",
    "REPOSITORY_ROOT",
    "SCENARIOS",
    "WORKSPACE_M",
    "write_json",
]
