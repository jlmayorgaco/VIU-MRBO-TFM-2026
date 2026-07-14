from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.sp2.heterogeneous_game import run_heterogeneous_campaign


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    args = parser.parse_args()
    result = run_heterogeneous_campaign(args.config)
    print(result["manifest"])


if __name__ == "__main__":
    main()
