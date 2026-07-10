"""Postprocess SP9 only when real campaign outputs exist."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "sp9" / "SP9_COPPELIA_gap_study"


def main() -> int:
    required = RUN_DIR / "tables" / "runs.csv"
    if not required.exists():
        print("SP9 postprocess skipped: real runs.csv not found.")
        return 0
    print("SP9 postprocess placeholder: real runs.csv found; extend before promotion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
