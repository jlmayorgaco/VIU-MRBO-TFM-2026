"""Run a configured experiment from the command line."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from viu_mrob_tfm.cli.run_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
