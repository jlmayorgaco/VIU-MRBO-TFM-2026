"""CLI for canonical SP1 distributed coalition formation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp1_canonical.experiment import execute


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the canonical SP1 coalition-formation experiment."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/configs/sp1_canonical_smoke.yaml"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Truncate any supplied configuration to a two-world software smoke test.",
    )
    args = parser.parse_args()
    print(json.dumps(execute(args.config, smoke=args.smoke), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
