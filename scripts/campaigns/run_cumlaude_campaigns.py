"""Regenerate the cum laude validation campaigns H10-H12."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    commands = [
        [sys.executable, "scripts/campaigns/run_h10_predictive_density.py"],
        [sys.executable, "scripts/campaigns/run_h11_integrated_engine.py"],
        [sys.executable, "scripts/coppelia/run_h12_coppelia_campaign.py"],
    ]
    for command in commands:
        print("running", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
