"""Regenerate SP1-GEO tables, statistical tests, figures, and report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from viu_mrob_tfm.sp1_geo.runner import analyze_results, finalize_claim_audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument(
        "--finalize-claim-audit",
        action="store_true",
        help="Close claim traceability without recomputing statistics.",
    )
    args = parser.parse_args()
    operation = (
        finalize_claim_audit
        if args.finalize_claim_audit
        else analyze_results
    )
    print(operation(args.results.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
