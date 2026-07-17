"""Run the integrated Cargo SP2--SP6 campaign."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from viu_mrob_tfm.integrated import run_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Cargo E2E YAML configuration")
    args = parser.parse_args(argv)
    result = run_config(args.config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
