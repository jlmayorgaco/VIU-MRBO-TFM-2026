"""Command-line entry point for the canonical SP7 traffic experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.sp7 import run_sp7_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="SP7 YAML configuration path")
    args = parser.parse_args(argv)
    result = run_sp7_config(args.config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
